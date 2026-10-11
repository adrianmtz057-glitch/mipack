"""Glaciares: aproximación de capa delgada (SIA) con deslizamiento y erosión glaciar.

    dH/dt = div( D grad(s) ) + M(s),   s = b + H
    D = [ 2A/(n+2) (rho g)^n H^(n+2) + As (rho g)^n H^(n+1) ] |grad s|^(n-1),  n = 3
    u_b = As (rho g H |grad s|)^n            (velocidad de deslizamiento)
    erosión = Kg * u_b                         (Humphrey & Raymond 1994)
    M(s) = min(beta (s - ELA), Mmax)           (balance de masa)

Integración semi-implícita por direcciones alternadas (ADI) con D retrasado (Picard).
Acoplamiento asíncrono: el hielo se equilibra unos siglos, luego se aplica la erosión de
un intervalo largo y se repite.  Eso produce valles en U, sobreexcavaciones (lagos),
valles colgados, circos y, donde el hielo llega al mar con el nivel bajo, fiordos.
"""
import numpy as np
from numba import njit, prange

RHO_G = 910.0 * 9.81
A_GLEN = 7.6e-17           # Pa^-3 a^-1  (hielo templado)
A_SLIDE = 6.0e-14          # m a^-1 Pa^-3 (deslizamiento: ~50 m/a con tau_b = 90 kPa)


@njit(parallel=True, cache=True)
def _diffusivity(H, s, dx, Ad, As):
    ny, nx = H.shape
    D = np.zeros_like(H)
    ub = np.zeros_like(H)
    for i in prange(1, ny - 1):
        for j in range(1, nx - 1):
            h = H[i, j]
            if h <= 0.0:
                continue
            gx = (s[i, j + 1] - s[i, j - 1]) / (2 * dx)
            gy = (s[i + 1, j] - s[i - 1, j]) / (2 * dx)
            g2 = gx * gx + gy * gy
            tau = RHO_G * h
            D[i, j] = (2.0 * Ad / 5.0 * tau ** 3 * h * h + As * tau ** 3 * h) * g2
            ub[i, j] = As * (tau * np.sqrt(g2)) ** 3
    return D, ub


@njit(cache=True)
def _thomas(a, b, c, d):
    n = d.size
    cp = np.empty(n)
    dp = np.empty(n)
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        den = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / den
        dp[i] = (d[i] - a[i] * dp[i - 1]) / den
    x = np.empty(n)
    x[n - 1] = dp[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


@njit(parallel=True, cache=True)
def _sweep(H, bed, D, M, dt, dx, mask):
    """Medio paso implícito en la dirección de las columnas (eje 1)."""
    ny, nx = H.shape
    out = np.empty_like(H)
    r = dt / (dx * dx)
    for i in prange(ny):
        a = np.zeros(nx)
        b = np.ones(nx)
        c = np.zeros(nx)
        d = np.empty(nx)
        for j in range(nx):
            d[j] = H[i, j] + dt * M[i, j]
            if j == 0 or j == nx - 1 or not mask[i, j]:
                d[j] = 0.0 if not mask[i, j] else d[j]
                continue
            dl = 0.5 * (D[i, j] + D[i, j - 1]) * r
            dr = 0.5 * (D[i, j] + D[i, j + 1]) * r
            a[j] = -dl
            c[j] = -dr
            b[j] = 1.0 + dl + dr
            # término del lecho (explícito)
            d[j] += dr * (bed[i, j + 1] - bed[i, j]) - dl * (bed[i, j] - bed[i, j - 1])
        x = _thomas(a, b, c, d)
        for j in range(nx):
            out[i, j] = x[j] if x[j] > 0.0 else 0.0
    return out


def step(H, bed, dt, dx, ela, beta, mmax, mask, Ad=A_GLEN, As=A_SLIDE):
    s = bed + H
    M = np.minimum(beta * (s - ela), mmax)
    D, ub = _diffusivity(H, s, dx, Ad, As)
    H1 = _sweep(H, bed, D, M, dt * 0.5, dx, mask)
    s1 = bed + H1
    D1, _ = _diffusivity(H1, s1, dx, Ad, As)
    H2 = _sweep(np.ascontiguousarray(H1.T), np.ascontiguousarray(bed.T), np.ascontiguousarray(D1.T),
                np.ascontiguousarray(M.T), dt * 0.5, dx, np.ascontiguousarray(mask.T))
    return np.ascontiguousarray(H2.T), ub


def _depression_depth(h, sea_level):
    from .lem import route_flow
    n0, n1 = h.shape
    fr = np.full((n0, n1), -1, np.int64)
    _, _, filled = route_flow(h, h < sea_level, 0.0, fr)
    return filled - h


def glaciate(h, dx, ela, sea_level, t_total, beta=0.006, mmax=1.4, Kg=2.5e-5, ub_cap=150.0,
             max_overdeep=25.0,
             eq_years=400.0, dt_ice=2.0, dt_erosion=1000.0, H=None, log=True, mask=None):
    """Erosiona h (superficie, m sobre el nivel del mar actual) con glaciares.

    ela: cota de la línea de equilibrio (escalar o array).  Devuelve (h_nuevo, H, erosión)
    """
    h = h.astype(np.float64).copy()
    if H is None:
        H = np.zeros_like(h)
    if mask is None:
        mask = np.ones(h.shape, bool)
    ero_tot = np.zeros_like(h)
    ncyc = int(round(t_total / dt_erosion))
    nst = int(round(eq_years / dt_ice))
    for cyc in range(ncyc):
        # el hielo que entra al mar se pierde por desprendimiento (calving) a partir de -40 m
        ub_acc = np.zeros_like(h)
        for k in range(nst):
            H, ub = step(H, h, dt_ice, dx, ela, beta, mmax, mask)
            calv = (h < sea_level) & (H < (sea_level - h) * 1.1)
            H[calv] *= 0.5
            if k >= nst // 2:
                ub_acc += ub
        ub_mean = np.minimum(ub_acc / (nst - nst // 2), ub_cap)
        ero = Kg * ub_mean * dt_erosion
        # las sobreexcavaciones se autolimitan (pendiente adversa, sedimento): lagos de decenas de m
        depth = _depression_depth(h - ero, sea_level - 200.0)
        ero *= np.exp(-np.maximum(depth, 0.0) / max_overdeep)
        h -= ero
        ero_tot += ero
        if log:
            gl = H > 1
            print(f'  [glaciar] ciclo {cyc + 1}/{ncyc}  área hielo={gl.mean():.3f}  Hmax={H.max():.0f} m  '
                  f'ub_max={ub_mean.max():.0f} m/a  erosión_max={ero_tot.max():.0f} m', flush=True)
    return h, H, ero_tot
