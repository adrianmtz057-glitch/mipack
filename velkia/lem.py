"""Modelo de evolución del paisaje (LEM) en numba.

Procesos:
  * enrutamiento de flujo D8 sobre la superficie rellenada (priority-flood, Barnes 2014),
    de modo que toda celda drena a un desagüe (mar o borde) y las depresiones son lagos;
  * ley de potencia fluvial con depósito (erosión-depósito tipo Yuan et al. 2019):
        dh/dt = U - K Q^m S^n + (G/Q) Qs        (n = 1, implícito, iteraciones de Gauss-Seidel)
    con dos capas: roca (K_roca depende de la litología a la cota de la roca) y sedimento (K_sed);
  * difusión de laderas implícita (ADI) con difusividad variable.

Convenciones: arrays [fila=z, columna=x], celdas cuadradas de lado dx (bloques = metros).
"""
import math

import numpy as np
from numba import njit, prange

SQRT2 = math.sqrt(2.0)
DI = np.array([-1, -1, -1, 0, 0, 1, 1, 1], np.int64)
DJ = np.array([-1, 0, 1, -1, 1, -1, 0, 1], np.int64)
DD = np.array([SQRT2, 1.0, SQRT2, 1.0, 1.0, SQRT2, 1.0, SQRT2])


# ------------------------------------------------------------------ montículo binario
@njit(cache=True, inline='always')
def _heap_push(hk, hv, n, key, val):
    i = n
    hk[i] = key
    hv[i] = val
    while i > 0:
        p = (i - 1) >> 1
        if hk[p] > hk[i] or (hk[p] == hk[i] and hv[p] > hv[i]):
            hk[p], hk[i] = hk[i], hk[p]
            hv[p], hv[i] = hv[i], hv[p]
            i = p
        else:
            break
    return n + 1


@njit(cache=True, inline='always')
def _heap_pop(hk, hv, n):
    k = hk[0]
    v = hv[0]
    n -= 1
    hk[0] = hk[n]
    hv[0] = hv[n]
    i = 0
    while True:
        l = 2 * i + 1
        r = l + 1
        s = i
        if l < n and (hk[l] < hk[s] or (hk[l] == hk[s] and hv[l] < hv[s])):
            s = l
        if r < n and (hk[r] < hk[s] or (hk[r] == hk[s] and hv[r] < hv[s])):
            s = r
        if s == i:
            break
        hk[s], hk[i] = hk[i], hk[s]
        hv[s], hv[i] = hv[i], hv[s]
        i = s
    return k, v, n


# ------------------------------------------------------------------ enrutamiento
@njit(cache=True)
def route_flow(z, outlet, eps, fixed_rec):
    """Priority-flood + D8 de máxima pendiente sobre la superficie rellenada.

    z        : elevación (float64 2D)
    outlet   : bool 2D, celdas desagüe (mar, borde). Reciben rec = sí mismas.
    eps      : pendiente mínima impuesta en zonas planas/lagos (m por m)
    fixed_rec: int64 2D, receptor forzado (índice plano) o -1. Se usa para fijar el
               trazado de un río antecedente. Debe ser coherente (sin ciclos).
    Devuelve rec (índice plano), stack (orden de abajo hacia arriba), filled.
    """
    ny, nx = z.shape
    n = ny * nx
    zf = z.ravel()
    filled = np.empty(n)
    rec = np.full(n, -1, np.int64)
    closed = np.zeros(n, np.bool_)
    queued = np.zeros(n, np.bool_)
    stack = np.empty(n, np.int64)
    hk = np.empty(n)
    hv = np.empty(n, np.int64)
    hn = 0
    out = outlet.ravel()
    fr = fixed_rec.ravel()
    for i in range(n):
        if out[i]:
            filled[i] = zf[i]
            rec[i] = i
            hn = _heap_push(hk, hv, hn, zf[i], i)
            queued[i] = True
    # si no hay desagües, usar el borde
    if hn == 0:
        for i in range(n):
            r = i // nx
            c = i % nx
            if r == 0 or c == 0 or r == ny - 1 or c == nx - 1:
                filled[i] = zf[i]
                rec[i] = i
                hn = _heap_push(hk, hv, hn, zf[i], i)
                queued[i] = True
    ns = 0
    while hn > 0:
        k, c, hn = _heap_pop(hk, hv, hn)
        if closed[c]:
            continue
        closed[c] = True
        stack[ns] = c
        ns += 1
        r0 = c // nx
        c0 = c % nx
        for d in range(8):
            r1 = r0 + DI[d]
            c1 = c0 + DJ[d]
            if r1 < 0 or r1 >= ny or c1 < 0 or c1 >= nx:
                continue
            j = r1 * nx + c1
            if closed[j] or queued[j]:
                continue
            f = zf[j]
            m = filled[c] + eps * DD[d]
            if f < m:
                f = m
            filled[j] = f
            rec[j] = c
            queued[j] = True
            hn = _heap_push(hk, hv, hn, f, j)
    # máxima pendiente sobre la superficie rellenada (receptor siempre más bajo => orden válido)
    for i in range(n):
        if fr[i] >= 0:
            rec[i] = fr[i]
            continue
        if out[i]:
            rec[i] = i
            continue
        r0 = i // nx
        c0 = i % nx
        best = 0.0
        bj = rec[i]
        for d in range(8):
            r1 = r0 + DI[d]
            c1 = c0 + DJ[d]
            if r1 < 0 or r1 >= ny or c1 < 0 or c1 >= nx:
                continue
            j = r1 * nx + c1
            if filled[j] < filled[i]:
                s = (filled[i] - filled[j]) / DD[d]
                if s > best:
                    best = s
                    bj = j
        rec[i] = bj
    return rec, stack[:ns], filled.reshape(ny, nx)


@njit(cache=True)
def fix_stack(rec, n):
    """Reconstruye un orden topológico (receptores antes que donantes) para rec arbitrario."""
    ndon = np.zeros(n, np.int64)
    for i in range(n):
        if rec[i] != i:
            ndon[rec[i]] += 1
    start = np.zeros(n + 1, np.int64)
    for i in range(n):
        start[i + 1] = start[i] + ndon[i]
    fill = start[:-1].copy()
    don = np.empty(max(start[n], 1), np.int64)
    for i in range(n):
        if rec[i] != i:
            r = rec[i]
            don[fill[r]] = i
            fill[r] += 1
    stack = np.empty(n, np.int64)
    ns = 0
    pile = np.empty(n, np.int64)
    for i in range(n):
        if rec[i] == i:
            pile[0] = i
            top = 1
            while top > 0:
                top -= 1
                c = pile[top]
                stack[ns] = c
                ns += 1
                for k in range(start[c], start[c + 1]):
                    pile[top] = don[k]
                    top += 1
    return stack[:ns]


@njit(cache=True)
def accumulate(stack, rec, w):
    """Suma w aguas abajo (área de drenaje o caudal)."""
    a = w.ravel().copy()
    for k in range(stack.size - 1, -1, -1):
        i = stack[k]
        r = rec[i]
        if r != i:
            a[r] += a[i]
    return a


@njit(cache=True)
def rec_dist(rec, nx, dx):
    n = rec.size
    L = np.empty(n)
    for i in range(n):
        r = rec[i]
        if r == i:
            L[i] = dx
        else:
            di = abs(r // nx - i // nx)
            dj = abs(r % nx - i % nx)
            L[i] = dx * (SQRT2 if (di + dj) == 2 else 1.0)
    return L


# ------------------------------------------------------------------ ley de potencia fluvial
@njit(cache=True)
def spl_ed(h, b, stack, rec, L, Q, Kb, Ks, m, G, U, dt, lake, outlet, cell_area,
           iters, sea, Gsea, filled, Qd):
    """Un paso implícito de erosión-depósito (n = 1), Yuan et al. (2019).

        h_i (1 + F + g) = h0_i (1 + g) + U dt (1 + g) + F h_r + dt G Qs_in / Q
        F = K dt Q^m / L ,  g = G a / Q   (G: velocidad efectiva de depósito, m/a)

    h, b   : superficie y techo de roca (1D, se actualizan in situ)
    Q      : caudal (m3/a);  Kb: erodabilidad de la roca;  Ks: multiplicador para sedimento
    Qd     : caudal efectivo para el transporte de sedimento (incluye crecidas en zonas áridas,
             evita concentraciones de sedimento irreales)
    lake   : celdas en depresión: solo se rellenan hasta 'filled' y pasan el resto
    Devuelve qs_in (m3/a) que llega a cada celda; en los desagües es lo que sale al mar.
    """
    n = h.size
    h0 = h.copy()
    hn = h.copy()
    qs_in = np.zeros(n)
    for it in range(iters):
        for k in range(stack.size):
            i = stack[k]
            r = rec[i]
            if outlet[i] or r == i:
                hn[i] = h0[i] if outlet[i] else h0[i] + U[i] * dt
                continue
            hr = hn[r]
            q = Q[i]
            if lake[i]:
                base = h0[i] + U[i] * dt
                cap = filled[i] - base
                if cap < 0.0:
                    cap = 0.0
                dep = qs_in[i] * dt / cell_area
                if dep > cap:
                    dep = cap
                hn[i] = base + dep
                continue
            K = Kb[i] * Ks if (h0[i] - b[i]) > 0.5 else Kb[i]
            F = K * dt * q ** m / L[i]
            qd = Qd[i]
            gg = G[i] * cell_area / qd
            num = (h0[i] + U[i] * dt) * (1.0 + gg) + F * hr + dt * G[i] * qs_in[i] / qd
            v = num / (1.0 + F + gg)
            if v < hr and h0[i] >= hr:
                v = hr + 1e-6
            hn[i] = v
        for k in range(n):
            qs_in[k] = 0.0
        for k in range(stack.size - 1, -1, -1):
            i = stack[k]
            r = rec[i]
            if r == i:
                continue
            e = (U[i] * dt - (hn[i] - h0[i])) * cell_area / dt
            if lake[i]:
                e = -(hn[i] - h0[i] - U[i] * dt) * cell_area / dt
            qo = qs_in[i] + e
            if qo < 0.0:
                qo = 0.0
            qs_in[r] += qo
    for i in range(n):
        h[i] = hn[i]
        # el levantamiento mueve la columna entera (roca y sedimento), no solo la superficie
        if not outlet[i]:
            b[i] += U[i] * dt
        if h[i] < b[i]:
            b[i] = h[i]
    return qs_in


# ------------------------------------------------------------------ difusión de laderas
@njit(cache=True)
def _tridiag(a, bdiag, c, d, out):
    n = d.size
    cp = np.empty(n)
    dp = np.empty(n)
    cp[0] = c[0] / bdiag[0]
    dp[0] = d[0] / bdiag[0]
    for i in range(1, n):
        den = bdiag[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / den if i < n - 1 else 0.0
        dp[i] = (d[i] - a[i] * dp[i - 1]) / den
    out[n - 1] = dp[n - 1]
    for i in range(n - 2, -1, -1):
        out[i] = dp[i] - cp[i] * out[i + 1]


@njit(parallel=True, cache=True)
def _adi_rows(h, D, fixed, r):
    ny, nx = h.shape
    out = np.empty_like(h)
    for i in prange(ny):
        a = np.zeros(nx)
        bd = np.ones(nx)
        c = np.zeros(nx)
        d = h[i].copy()
        for j in range(nx):
            if fixed[i, j] or j == 0 or j == nx - 1:
                continue
            dl = 0.5 * (D[i, j] + D[i, j - 1]) * r
            dr = 0.5 * (D[i, j] + D[i, j + 1]) * r
            a[j] = -dl
            c[j] = -dr
            bd[j] = 1.0 + dl + dr
        row = np.empty(nx)
        _tridiag(a, bd, c, d, row)
        out[i] = row
    return out


def diffuse(h, D, dt, dx, fixed):
    """Difusión lineal implícita por direcciones alternadas (dos medios pasos)."""
    r = 0.5 * dt / (dx * dx)
    h1 = _adi_rows(h, D, fixed, r)
    h2 = _adi_rows(np.ascontiguousarray(h1.T), np.ascontiguousarray(D.T),
                   np.ascontiguousarray(fixed.T), r)
    return np.ascontiguousarray(h2.T)


# ------------------------------------------------------------------ utilidades
@njit(parallel=True, cache=True)
def slope_d8(z, dx):
    ny, nx = z.shape
    s = np.zeros_like(z)
    for i in prange(ny):
        for j in range(nx):
            best = 0.0
            for d in range(8):
                i1 = i + DI[d]
                j1 = j + DJ[d]
                if i1 < 0 or i1 >= ny or j1 < 0 or j1 >= nx:
                    continue
                v = (z[i, j] - z[i1, j1]) / (DD[d] * dx)
                if v > best:
                    best = v
            s[i, j] = best
    return s


@njit(cache=True)
def breach_chain(h, b, chain, grad, dx):
    """Río antecedente: desde la fuente hacia la desembocadura, ninguna celda del cauce puede
    quedar más alta que la anterior (el río corta los obstáculos que se levantan en su camino).
    Devuelve el volumen removido (m3)."""
    vol = 0.0
    hf = h.ravel()
    bf = b.ravel()
    for k in range(1, chain.size):
        i = chain[k]
        p = chain[k - 1]
        lim = hf[p] - grad * dx
        if hf[i] > lim:
            vol += (hf[i] - lim) * dx * dx
            hf[i] = lim
            if bf[i] > lim:
                bf[i] = lim
    return vol
