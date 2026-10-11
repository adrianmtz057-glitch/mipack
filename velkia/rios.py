"""Río Velkia: trazado antecedente (meandros por migración) y rasterización a la malla.

El río nace en la Cordillera, atraviesa los Jardines, cruza el desierto y corta la meseta
de los cañones (pasa por el canal de Vieja Velkia) hasta el mar.  Su planta se genera con
un modelo de migración de meandros (Howard & Knutson 1984): la tasa de migración lateral
depende de la curvatura local y de la curvatura aguas arriba ponderada exponencialmente.
Los meandros se forman sobre la llanura baja ANTES del levantamiento de la meseta; al
levantarse, el río se encaja y quedan meandros encajados (como los Goosenecks del San Juan).
"""
import numpy as np
from numba import njit

from .layout import poi_blocks

# puntos de paso (bloques). 'fijo' = tramo que no migra.
def waypoints(canal_pts):
    jx, jz = poi_blocks('jardines_de_velkia')
    pts = [
        ((2620, 1330), 'fijo'),       # circo glaciar bajo la cresta de la cordillera
        ((2430, 1620), 'fijo'),
        ((2260, 1950), 'fijo'),       # entra en los Jardines por el norte
        ((jx - 330, jz - 60), 'fijo'),  # rodea el domo central por el oeste (anillo de lagos)
        ((jx - 180, jz + 300), 'fijo'),
        ((jx + 250, jz + 260), 'fijo'),
        ((3040, 2900), 'fijo'),       # garganta y cascada de salida (sureste de los Jardines)
        ((3500, 2990), 'libre'),
        ((4300, 2950), 'libre'),      # pasa al norte de la Gran Pirámide
        ((4950, 3350), 'libre'),
        ((5250, 4200), 'libre'),      # borde oeste del Mar de Dunas
        ((5550, 4900), 'libre'),
        ((6000, 5500), 'libre'),
    ]
    cp = np.asarray(canal_pts, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(cp, axis=0).T))]
    for s in np.linspace(0, d[-1], max(2, int(d[-1] / 70) + 1)):   # canal fijo de Vieja Velkia
        pts.append(((float(np.interp(s, d, cp[:, 0])), float(np.interp(s, d, cp[:, 1]))), 'fijo'))
    pts += [
        ((7150, 6250), 'libre'),
        ((7300, 6700), 'libre'),
        ((7440, 7150), 'fijo'),
        ((7560, 7650), 'fijo'),       # desembocadura (estuario al sureste)
        ((7650, 8000), 'fijo'),
    ]
    return pts


def _resample(xy, fixed, ds):
    """Remuestrea una polilínea a paso ds manteniendo la marca 'fijo' por interpolación."""
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    nseg = max(1, int(round(d[-1] / ds)))
    s = np.linspace(0, d[-1], nseg + 1)
    x = np.interp(s, d, xy[:, 0])
    z = np.interp(s, d, xy[:, 1])
    f = np.interp(s, d, fixed.astype(float)) > 0.5
    return np.c_[x, z], f


def _smooth_path(pts, ds=10.0):
    """Curva suave (Catmull-Rom) por los puntos de paso."""
    P = np.array([p for p, _ in pts], float)
    F = np.array([k == 'fijo' for _, k in pts])
    out = []
    fl = []
    P2 = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    for i in range(1, len(P2) - 2):
        p0, p1, p2, p3 = P2[i - 1], P2[i], P2[i + 1], P2[i + 2]
        seg = np.linalg.norm(p2 - p1)
        nt = max(2, int(seg / ds))
        t = np.linspace(0, 1, nt, endpoint=False)[:, None]
        c = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 +
                   (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
        out.append(c)
        fl.append(np.full(nt, F[i - 1] and F[i]))
    out.append(P[-1:])
    fl.append(np.array([F[-1]]))
    return np.vstack(out), np.concatenate(fl)


@njit(cache=True)
def _upstream_weighted(curv, seg, alpha):
    acc = np.empty_like(curv)
    a = 0.0
    wv = 0.0
    for i in range(curv.size):
        e = np.exp(-alpha * seg[i])
        a = a * e + curv[i] * seg[i]
        wv = wv * e + seg[i]
        acc[i] = a / wv
    return acc


def _smooth1d(v, k):
    if k <= 1:
        return v
    w = np.hanning(k + 2)[1:-1]
    w /= w.sum()
    pad = k // 2
    vp = np.r_[np.full(pad, v[0]), v, np.full(pad, v[-1])]
    return np.convolve(vp, w, 'valid')[:v.size]


def meander(xy, fixed, width=22.0, steps=4000, seed=3, target_sinuosity=1.6, log=False):
    """Migración de meandros (Howard & Knutson 1984) con cortes (lagos en herradura).

    R1(s) = Omega*C(s) + Gamma * int C(s - xi) exp(-alpha xi) dxi / int exp(-alpha xi) dxi
    Devuelve la polilínea final, la marca de tramos fijos y los meandros abandonados.
    """
    rng = np.random.default_rng(seed)
    ds = width * 0.5
    xy, fixed = _resample(xy, fixed, ds)
    alpha = 0.75 / width         # escala de influencia aguas arriba (1/m)
    omega, gamma = -1.0, 2.5
    free0 = _free_length(xy, fixed)
    # perturbación inicial de longitud de onda ~10-20 anchos
    t_ = np.gradient(xy, axis=0)
    t_ /= np.linalg.norm(t_, axis=1)[:, None] + 1e-9
    nrm = np.c_[-t_[:, 1], t_[:, 0]]
    pert = _smooth1d(rng.standard_normal(len(xy)), int(4 * width / ds)) * 25.0
    taper = _smooth1d((~fixed).astype(float), int(10 * width / ds))
    xy = xy + (pert * taper)[:, None] * nrm
    oxbows = []
    for it in range(steps):
        t_ = np.gradient(xy, axis=0)
        t_ /= np.linalg.norm(t_, axis=1)[:, None] + 1e-9
        nrm = np.c_[-t_[:, 1], t_[:, 0]]
        ang = np.unwrap(np.arctan2(t_[:, 1], t_[:, 0]))
        seg = np.r_[ds, np.hypot(*np.diff(xy, axis=0).T)]
        curv = np.gradient(ang) / np.maximum(seg, 1e-3)
        curv = _smooth1d(curv, 5)
        R = omega * curv + gamma * _upstream_weighted(curv, seg, alpha)
        R *= 3.0 * width
        taper = _smooth1d((~fixed).astype(float), int(10 * width / ds))
        step = np.clip(R, -1, 1) * 0.03 * width * taper
        xy = xy - step[:, None] * nrm   # hacia la orilla exterior
        # suavizado débil anti-ruido de malla
        xs = xy.copy()
        xs[1:-1] = 0.25 * xy[:-2] + 0.5 * xy[1:-1] + 0.25 * xy[2:]
        k = 0.03 * (~fixed)[:, None]
        xy = xy * (1 - k) + xs * k
        xy, fixed = _resample(xy, fixed, ds)
        if it % 4 == 0:
            xy, fixed, cut = _cutoffs(xy, fixed, width * 1.4, ds)
            oxbows += cut
        sinu = _free_length(xy, fixed) / free0
        if log and it % 200 == 0:
            print('  meandros', it, 'sinuosidad', round(sinu, 3), 'oxbows', len(oxbows), flush=True)
        if sinu >= target_sinuosity:
            break
    return xy, fixed, oxbows


def _free_length(xy, fixed):
    d = np.hypot(*np.diff(xy, axis=0).T)
    f = ~(fixed[:-1] & fixed[1:])
    return d[f].sum()


def _cutoffs(xy, fixed, dmin, ds):
    from scipy.spatial import cKDTree
    cut = []
    tree = cKDTree(xy)
    pairs = tree.query_pairs(dmin)
    if not pairs:
        return xy, fixed, cut
    skip = int(4 * dmin / ds) + 2
    maxloop = int(2500.0 / ds)
    best = None
    for i, j in pairs:
        if i > j:
            i, j = j, i
        if skip < j - i < maxloop and not fixed[i:j + 1].any():
            if best is None or (j - i) < (best[1] - best[0]):
                best = (i, j)
    if best is None:
        return xy, fixed, cut
    i, j = best
    cut.append(xy[i:j + 1].copy())
    xy = np.vstack([xy[:i + 1], xy[j:]])
    fixed = np.r_[fixed[:i + 1], fixed[j:]]
    return xy, fixed, cut


def disenar_rio(canal_pts, seed=3, log=False):
    pts = waypoints(canal_pts)
    xy, fixed = _smooth_path(pts, 10.0)
    xy2, fixed2, oxbows = meander(xy, fixed, seed=seed, log=log)
    return xy2, fixed2, oxbows


def rasterize_chain(xy, n, dx):
    """Convierte la polilínea en una cadena 8-conexa de celdas (índices planos) sin repetidos."""
    cells = []
    for i in range(len(xy) - 1):
        a, b = xy[i] / dx, xy[i + 1] / dx
        steps = int(np.ceil(np.max(np.abs(b - a)) * 2)) + 1
        for t in np.linspace(0, 1, steps, endpoint=False):
            p = a + (b - a) * t
            c = (int(np.clip(p[1], 0, n - 1)), int(np.clip(p[0], 0, n - 1)))
            if not cells or cells[-1] != c:
                cells.append(c)
    # eliminar bucles (si una celda reaparece, cortar el lazo)
    seen = {}
    out = []
    for c in cells:
        if c in seen:
            k = seen[c]
            for cc in out[k + 1:]:
                seen.pop(cc, None)
            out = out[:k + 1]
        else:
            seen[c] = len(out)
            out.append(c)
    # asegurar 8-conectividad
    chain = [out[0]]
    for c in out[1:]:
        p = chain[-1]
        while max(abs(c[0] - p[0]), abs(c[1] - p[1])) > 1:
            p = (p[0] + int(np.sign(c[0] - p[0])), p[1] + int(np.sign(c[1] - p[1])))
            chain.append(p)
        if c != chain[-1]:
            chain.append(c)
    return np.array([r * n + c for r, c in chain], np.int64)
