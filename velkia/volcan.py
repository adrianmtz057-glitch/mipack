"""Construcción volcánica: coladas de lava apiladas + caída de piroclastos.

Cada colada parte del cráter (o de un respiradero lateral), avanza por máxima pendiente
con desvíos aleatorios y se ensancha lateralmente; deja un depósito de espesor decreciente
hacia los bordes (con albardones).  Miles de coladas construyen un estratovolcán irregular,
con lóbulos y lenguas de lava que luego la erosión fluvial disecciona.
"""
import math

import numpy as np
from numba import njit

DI8 = np.array([-1, -1, -1, 0, 0, 1, 1, 1])
DJ8 = np.array([-1, 0, 1, -1, 1, -1, 0, 1])
DD8 = np.array([1.414, 1.0, 1.414, 1.0, 1.0, 1.414, 1.0, 1.414])


@njit(cache=True)
def _flow(h, dep, i0, j0, length_cells, width_cells, thick, seed, sea_cells):
    np.random.seed(seed)
    ny, nx = h.shape
    i, j = i0, j0
    di_prev, dj_prev = 0, 0
    path_i = np.empty(length_cells, np.int64)
    path_j = np.empty(length_cells, np.int64)
    n = 0
    for step in range(length_cells):
        path_i[n] = i
        path_j[n] = j
        n += 1
        # elegir vecino con máxima pendiente + ruido + inercia
        best = -1e9
        bi, bj = i, j
        for d in range(8):
            ii = i + DI8[d]
            jj = j + DJ8[d]
            if ii < 1 or ii >= ny - 1 or jj < 1 or jj >= nx - 1:
                continue
            s = (h[i, j] + dep[i, j] - h[ii, jj] - dep[ii, jj]) / DD8[d]
            s += 0.15 * np.random.randn() + 0.25 * (DI8[d] * di_prev + DJ8[d] * dj_prev)
            if s > best:
                best = s
                bi, bj = ii, jj
        if bi == i and bj == j:
            break
        di_prev, dj_prev = bi - i, bj - j
        i, j = bi, bj
        if h[i, j] < 0.0 and sea_cells:   # la lava se detiene al entrar al mar (deja un delta de lava)
            break
    # depósito: perfil transversal con albardones, espesor que crece hacia el frente
    for k in range(n):
        frac = k / max(n - 1, 1)
        w = width_cells * (0.6 + 0.8 * frac)
        t = thick * (0.6 + 0.9 * frac)
        ci, cj = path_i[k], path_j[k]
        r = int(w) + 1
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                ii = ci + a
                jj = cj + b
                if ii < 0 or ii >= ny or jj < 0 or jj >= nx:
                    continue
                d = math.sqrt(a * a + b * b) / w
                if d > 1.0:
                    continue
                prof = (1.0 - d ** 4) * (0.85 + 0.35 * math.exp(-((d - 0.8) / 0.12) ** 2))
                v = t * prof
                if v > dep[ii, jj] * 0.0 + 0.0:
                    dep[ii, jj] += v / (1.0 + 0.15 * (2 * r + 1) / max(w, 1.0))
    return n


def build_volcano(h, dx, center, height=250.0, radius=1100.0, n_flows=2600, seed=5, crater_r=110.0,
                  vents_lat=6, log=True):
    """Construye un volcán sobre h (m sobre el mar). Devuelve h nuevo y el espesor de lava."""
    rng = np.random.default_rng(seed)
    ny, nx = h.shape
    cy, cx = center[1] / dx, center[0] / dx
    zz, xx = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
    r = np.hypot((zz - cy) * dx, (xx - cx) * dx)
    dep = np.zeros_like(h)      # espesor acumulado de coladas
    # piroclastos: perfil cóncavo típico de estratovolcán (h ~ exp)
    tephra = height * 0.5 * np.exp(-r / (radius * 0.28))
    lat = [(cy + rng.uniform(-1, 1) * radius * 0.35 / dx, cx + rng.uniform(-1, 1) * radius * 0.35 / dx)
           for _ in range(vents_lat)]
    for k in range(n_flows):
        if rng.random() < 0.8:
            a = rng.uniform(0, 2 * np.pi)
            i0 = int(cy + np.sin(a) * crater_r / dx)
            j0 = int(cx + np.cos(a) * crater_r / dx)
        else:
            vi, vj = lat[rng.integers(len(lat))]
            i0, j0 = int(vi), int(vj)
        L = int(rng.uniform(0.3, 1.25) * radius / dx)
        W = rng.uniform(25, 70) / dx
        T = rng.uniform(0.8, 2.2) * (height / 250.0) * 0.35
        _flow(h + tephra, dep, i0, j0, L, W, T, int(seed * 100000 + k), True)
        if log and k % 500 == 0:
            print(f'  [volcán] colada {k}/{n_flows}  cumbre={float((h + dep).max()):.0f} m', flush=True)
    # escalar las coladas para que el edificio total tenga la altura pedida en la cumbre
    cumbre = r < 2.5 * crater_r
    dep *= (height * 0.5) / max(float(np.median(dep[cumbre])), 1e-6)
    dep += tephra
    # cráter: depresión de paredes empinadas en la cima
    crater = np.clip(1.0 - (r / crater_r) ** 2, 0, None)
    dep -= crater * height * 0.22
    return h + dep, dep


# ------------------------------------------------------------------ edificio joven (post-glaciar)
def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _trazar(h, dx, ini, objetivo=None, max_pasos=4000, inercia=0.35, ruido=0.12, sesgo=0.6, rng=None,
            remonta=9.0):
    """Camino de una colada por máxima pendiente (con inercia, ruido y, opcionalmente, atraída
    hacia un punto).  ini/objetivo en bloques.  Puede rellenar hondonadas de hasta 'remonta'
    metros (la lava se encharca y desborda); se detiene en el mar o en un hoyo más hondo."""
    rng = rng or np.random.default_rng(0)
    n = h.shape[0]
    i, j = int(ini[1] / dx), int(ini[0] / dx)
    pi, pj = [i], [j]
    di0, dj0 = 0.0, 0.0
    visit = {(i, j)}
    hmin = h[i, j]
    for _ in range(max_pasos):
        best, bi, bj = -1e18, -1, -1
        if objetivo is not None:
            ti, tj = objetivo[1] / dx - i, objetivo[0] / dx - j
            nt = np.hypot(ti, tj) + 1e-9
            ti, tj = ti / nt, tj / nt
            if nt * dx < 2 * dx:
                break
        for d in range(8):
            ii, jj = i + DI8[d], j + DJ8[d]
            if ii < 1 or ii >= n - 1 or jj < 1 or jj >= n - 1 or (ii, jj) in visit:
                continue
            s = (h[i, j] - h[ii, jj]) / (DD8[d] * dx)
            sc = s + inercia * (DI8[d] * di0 + DJ8[d] * dj0) / DD8[d] * 0.1 + ruido * 0.1 * rng.standard_normal()
            if objetivo is not None:
                sc += sesgo * 0.1 * (DI8[d] * ti + DJ8[d] * tj) / DD8[d]
            if h[ii, jj] > hmin + remonta:   # no remonta más de lo que puede rellenar
                sc -= 10.0
            elif s < 0.0:
                sc -= 0.05
            if sc > best:
                best, bi, bj = sc, ii, jj
        if bi < 0 or best < -5.0:
            break
        di0, dj0 = 0.6 * di0 + 0.4 * (bi - i), 0.6 * dj0 + 0.4 * (bj - j)
        i, j = bi, bj
        hmin = min(hmin, h[i, j])
        visit.add((i, j))
        pi.append(i)
        pj.append(j)
        if h[i, j] < 0.0:
            break
    return np.array(pi), np.array(pj)


def _colada(h, dx, pi, pj, espesor, ancho, rng, canal=False):
    """Deposita una colada a lo largo del camino: lóbulo de frente y bordes empinados (lava aa),
    albardones y, si canal, un canal central.  Devuelve (h nuevo, máscara del canal)."""
    n = h.shape[0]
    L = len(pi)
    if L < 3:
        return h, np.zeros_like(h, bool)
    # cota de la superficie de la colada: siempre baja a lo largo del camino
    sup = h[pi, pj] + espesor
    k_s = max(3, int(120.0 / dx))
    ker = np.hanning(2 * k_s + 1)
    ker /= ker.sum()
    sup = np.convolve(np.r_[np.full(k_s, sup[0]), sup, np.full(k_s, sup[-1])], ker, 'same')[k_s:-k_s]
    sup = np.minimum.accumulate(sup)
    sup = np.maximum(sup, h[pi, pj] + 0.4 * espesor)
    # ancho creciente aguas abajo, con lóbulos
    s = np.arange(L) / (L - 1)
    fase = rng.uniform(0, 6.3, 2)
    w = ancho * (0.55 + 0.7 * s) * (1.0 + 0.22 * np.sin(np.arange(L) * dx / 170.0 + fase[0])
                                   + 0.15 * np.sin(np.arange(L) * dx / 63.0 + fase[1]))
    w *= 1.0 + 0.8 * np.exp(-((1.0 - s) / 0.06) ** 2)          # lóbulo terminal
    from scipy.spatial import cKDTree
    pts = np.c_[(pj + 0.5) * dx, (pi + 0.5) * dx]
    r = int(np.ceil(w.max() / dx)) + 2
    i0, i1 = max(pi.min() - r, 0), min(pi.max() + r + 1, n)
    j0, j1 = max(pj.min() - r, 0), min(pj.max() + r + 1, n)
    zz, xx = np.mgrid[i0:i1, j0:j1]
    q = np.c_[(xx.ravel() + 0.5) * dx, (zz.ravel() + 0.5) * dx]
    dd, kk = cKDTree(pts).query(q, distance_upper_bound=w.max() + 2 * dx)
    ok = np.isfinite(dd)
    kk = np.where(ok, kk, 0)
    u = np.where(ok, dd / w[kk], 9.0)
    # perfil transversal: meseta con borde empinado (1 - u^6) y albardón cerca del borde
    perf = np.clip(1.0 - u ** 6, 0, None) * (0.85 + 0.25 * np.exp(-((u - 0.78) / 0.12) ** 2))
    tope = sup[kk] - espesor * (1.0 - perf)          # superficie de la colada en cada celda
    sub = h[i0:i1, j0:j1].ravel()
    cubre = ok & (u < 1.0)
    # el frente del lóbulo también es empinado
    frente = np.clip((L - 1 - kk) / max(3, 0.04 * L), 0, 1)
    tope = sub + (tope - sub) * np.where(cubre, frente, 0.0)
    nuevo = np.where(cubre, np.maximum(sub, tope), sub)
    can = np.zeros(h.shape, bool)
    if canal:
        c = cubre & (u < 0.12)
        nuevo = np.where(c, nuevo - 0.35 * espesor, nuevo)
        cm = np.zeros(sub.size, bool)
        cm[c] = True
        can[i0:i1, j0:j1] = cm.reshape(zz.shape)
    out = h.copy()
    out[i0:i1, j0:j1] = nuevo.reshape(zz.shape)
    return out, can


def _incision(e, dx, peso, prof_max=30.0, iters=50, K=0.012, m=0.5):
    """Incisión por ley de potencia (limitada por arranque) sobre la ventana del volcán: abre
    barrancos que se ramifican y se hacen más hondos ladera abajo."""
    from . import lem
    nz = np.nonzero(peso > 0)
    if nz[0].size == 0:
        return e
    i0, i1 = max(nz[0].min() - 2, 0), min(nz[0].max() + 3, e.shape[0])
    j0, j1 = max(nz[1].min() - 2, 0), min(nz[1].max() + 3, e.shape[1])
    z = np.ascontiguousarray(e[i0:i1, j0:j1], np.float64).copy()
    wv = peso[i0:i1, j0:j1].ravel()
    z0 = z.copy()
    ny, nx = z.shape
    out = np.zeros((ny, nx), bool)
    out[0, :] = out[-1, :] = out[:, 0] = out[:, -1] = True
    fr = np.full((ny, nx), -1, np.int64)
    area = np.full(ny * nx, dx * dx)
    for _ in range(iters):
        rec, stack, _f = lem.route_flow(z, out, 1e-4, fr)
        stack = lem.fix_stack(rec, ny * nx)
        A = lem.accumulate(stack, rec, area)
        L = lem.rec_dist(rec, nx, dx)
        zf = z.ravel()
        dz = np.maximum(zf - zf[rec], 0.0)
        E = np.minimum(K * A ** m * dz / L, 0.6 * dz) * wv
        zf -= E
        np.maximum(zf, z0.ravel() - prof_max, out=zf)
    e = e.copy()
    e[i0:i1, j0:j1] = z
    return e


def rejuvenecer(h, b, dx, center, R=1100.0, borde_h=270.0, p=2.2, caldera_r=230.0, caldera_d=85.0,
                barranco_max=30.0, n_parasitos=3, coladas=None, n_coladas=6, cono_interior=True, seed=8, log=True):
    """Edificio joven sobre el volcán erosionado: cono de flancos superiores empinados (perfil
    cóncavo), caldera de paredes casi verticales con un cono interior y su cráter de lava,
    barrancos radiales en V y coladas post-glaciares de bordes y frentes empinados.
    coladas: lista de (inicio, objetivo|None, espesor, ancho, canal) en bloques; las del mapa 2
    (río de lava con ramales) se pasan desde modelado.py.
    Devuelve (h, b, info) con info: lava_canal (máscara), lago_lava (máscara), caminos."""
    rng = np.random.default_rng(seed)
    altura = borde_h / (1.0 - caldera_r / R) ** p      # cono teórico (truncado por la caldera)
    n = h.shape[0]
    zz, xx = np.meshgrid((np.arange(n) + 0.5) * dx, (np.arange(n) + 0.5) * dx, indexing='ij')
    X, Z = xx - center[0], zz - center[1]
    r = np.hypot(X, Z)
    th = np.arctan2(Z, X)
    anillo = (r > 1.25 * R) & (r < 1.6 * R) & (h > 0)
    base = float(np.median(h[anillo])) if anillo.any() else 0.0
    e = h - base
    # contorno y flancos asimétricos (coladas preferentes, colapsos laterales antiguos)
    arm = [(k, rng.uniform(0.04, 0.10) / k ** 0.3, rng.uniform(0, 2 * np.pi)) for k in (1, 2, 3, 5)]
    fR = 1.0 + sum(a * np.cos(k * th + f) for k, a, f in arm)
    rn = r / fR
    # cono: el perfil suave sustituye la envolvente; se conserva el detalle de las coladas viejas
    from scipy import ndimage as ndi
    from .noise import spectral_noise
    det = e - ndi.gaussian_filter(e, 80.0 / dx)
    cono = altura * np.clip(1.0 - rn / R, 0, 1) ** p
    w = 1.0 - _sstep((rn - 0.85 * R) / (0.35 * R))
    e_new = (cono + 0.6 * det) * w + e * (1 - w)
    e_new = np.where(w > 0, np.maximum(e_new, e * (1 - w)), e_new)
    # conos parásitos (de escoria) en los flancos, con su cráter
    for _ in range(n_parasitos):
        a = rng.uniform(0, 2 * np.pi)
        rr = rng.uniform(0.35, 0.7) * R
        px_, pz_ = rr * np.cos(a), rr * np.sin(a)
        rp = np.hypot(X - px_, Z - pz_)
        hp = rng.uniform(30.0, 55.0)
        rad = hp * 2.6
        cp = hp * np.clip(1.0 - rp / rad, 0, 1) ** 1.1 - 0.45 * hp * np.clip(1.0 - (rp / (0.28 * rad)) ** 2, 0, 1)
        e_new = e_new + np.maximum(cp, 0) * w
    # barrancos: incisión fluvial sobre el cono (red radial y dendrítica de verdad)
    e_new = e_new + (2.5 * spectral_noise(e_new.shape, 2.6, seed + 3)) * w
    antes_inc = e_new
    e_new = _incision(e_new, dx, w * (rn > caldera_r + 30.0), prof_max=barranco_max, iters=50)
    # la red D8 deja cauces en zigzag: se suaviza la incisión (barrancos en V, sin dientes)
    e_new = antes_inc + ndi.gaussian_filter(e_new - antes_inc, 1.1)
    # caldera: borde irregular (festones de colapso), pared casi vertical, fondo plano
    borde = altura * (1.0 - caldera_r / R) ** p
    piso = borde - caldera_d
    fc = 1.0 + sum(a * np.cos(k * th + f) for k, a, f in
                   [(k, rng.uniform(0.03, 0.08), rng.uniform(0, 2 * np.pi)) for k in (2, 3, 5, 8)])
    rc = r / fc
    pared = _sstep((rc - (caldera_r - 45.0)) / 45.0)
    e_new = np.where(rc < caldera_r + 5, np.minimum(e_new, piso + (e_new - piso) * pared), e_new)
    # cono interior con cráter (lago de lava)
    ca = rng.uniform(0, 2 * np.pi)
    icx, icz = 0.35 * caldera_r * np.cos(ca), 0.35 * caldera_r * np.sin(ca)
    ri = np.hypot(X - icx, Z - icz)
    cono_i = 45.0 * np.clip(1.0 - ri / 95.0, 0, 1) ** 1.2
    crater_i = 16.0 * np.clip(1.0 - (ri / 26.0) ** 2, 0, 1)
    if cono_interior:
        e_new = np.where(rc < caldera_r, np.maximum(e_new, piso + cono_i - crater_i), e_new)
        lago_lava = (ri < 22.0) & (rc < caldera_r)
    else:                                   # caldera llena de lava (sin cono interior)
        lago_lava = rc < caldera_r - 20.0
    hn = e_new + base
    if log:
        print(f'  [volcán] base {base:.0f} m, borde de la caldera {borde + base:.0f} m, '
              f'fondo {piso + base:.0f} m, cumbre {hn[r < 1.2 * R].max():.0f} m', flush=True)
    # coladas jóvenes: las que pide el mapa + otras por los flancos
    canal = np.zeros((n, n), bool)
    caminos = []
    lista = list(coladas or [])
    for _ in range(n_coladas):
        a = rng.uniform(0, 2 * np.pi)
        rr = rng.uniform(caldera_r + 40, 0.45 * R)
        lista.append(((center[0] + rr * np.cos(a), center[1] + rr * np.sin(a)), None,
                      rng.uniform(7.0, 13.0), rng.uniform(40.0, 85.0), False))
    for ini, obj, esp, anc, con_canal in lista:
        pi, pj = _trazar(hn, dx, ini, objetivo=obj, rng=rng)
        hn, cm = _colada(hn, dx, pi, pj, esp, anc, rng, canal=con_canal)
        canal |= cm
        caminos.append(np.c_[(pj + 0.5) * dx, (pi + 0.5) * dx])
    b = np.where(hn > h + 0.5, hn - 0.2, np.minimum(b, hn))       # basalto fresco
    return hn, b, {'lava_canal': canal, 'lago_lava': lago_lava, 'caminos': caminos,
                   'caldera': (float(center[0]), float(center[1]), caldera_r), 'base': base}
