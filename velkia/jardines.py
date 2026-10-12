"""Jardines de Velkia: valle glaciar en U (modelo Yosemite).

El glaciar que bajaba de la cordillera excavó un valle en U en una meseta de granito.  El valle
sigue el eje del hielo (el mismo que hoy sigue el río): estrecho donde entra desde el norte,
ensanchado en una cubeta en el centro y estrecho otra vez en la garganta de salida al sureste.
Fondo plano, paredes casi verticales que se tienden hacia arriba, valles laterales colgados
(cascadas en la pared), una roca aborregada alargada en el sentido del hielo y cubetas
sobreexcavadas en el fondo que hoy son una cadena de lagos a lo largo del río.  El umbral
rocoso de la garganta (riegel) retiene los lagos.

Se aplica al final de la fase glaciar como plantilla de la erosión del glaciar de los Jardines
y de la meseta granítica que lo encierra (el modelo SIA a 8 bloques/celda no resuelve bien un
valle de este tamaño); la erosión fluvial y de laderas posterior actúa sobre él.
"""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from .layout import jardines_r, poi_blocks
from .noise import spectral_noise


def _suave1d(v, k):
    if k < 2:
        return v
    w = np.hanning(k + 2)[1:-1]
    w /= w.sum()
    vp = np.r_[np.full(k, v[0]), v, np.full(k, v[-1])]
    return np.convolve(vp, w, 'same')[k:-k]


def excavar(h, b, lay, chain, wall_h=105.0, lip_h=55.0, lake_depth=7.0, seed=17):
    """Devuelve (h, b, lagos).  h, b relativos al mar; chain = celdas del río (fuente -> mar)."""
    n = lay.n
    dx = lay.dx
    zz, xx = lay.coords()
    jx, jz = poi_blocks('jardines_de_velkia')
    rng = np.random.default_rng(seed)
    h = h.copy()
    b = b.copy()
    # ---------------------------------------------- eje del valle (río) cerca de los Jardines
    cx = (chain % n + 0.5) * dx
    cz = (chain // n + 0.5) * dx
    rch = jardines_r(cx, cz)
    idx = np.nonzero(rch < 1.45)[0]
    if idx.size < 4:
        return h, b, np.zeros((n, n), bool)
    k0, k1 = idx[0], idx[-1]
    ax = np.c_[cx[k0:k1 + 1], cz[k0:k1 + 1]]
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(ax, axis=0).T))]
    s /= s[-1]
    # semiancho del valle a lo largo del eje: estrecho, cubeta ancha, garganta
    base = 130.0 + 520.0 * np.sin(np.pi * np.clip((s - 0.08) / 0.80, 0, 1)) ** 0.8
    base *= 1.0 + 0.18 * _suave1d(rng.standard_normal(s.size), 25) / 0.4
    semi = np.clip(base, 110.0, 700.0)
    # entrada colgada: la cascada está donde el eje cruza la pared norte
    s_casc = float(s[np.argmax(jardines_r(ax[:, 0], ax[:, 1]) < 0.95)]) if np.any(jardines_r(ax[:, 0], ax[:, 1]) < 0.95) else 0.1
    # ---------------------------------------------- distancia (deformada) al eje
    wu = spectral_noise((n, n), 2.8, seed + 1, kmin=6.0) * 70.0
    wv = spectral_noise((n, n), 2.8, seed + 2, kmin=6.0) * 70.0
    pts = np.c_[(xx + wu).ravel(), (zz + wv).ravel()]
    tree = cKDTree(ax)
    d, k = tree.query(pts, distance_upper_bound=2500.0)
    d = np.where(np.isfinite(d), d, 1e9).reshape(n, n)
    k = np.minimum(k, ax.shape[0] - 1).reshape(n, n)
    w = semi[k]
    u = d / w
    sk = s[k]
    interior = (u < 0.72) & (sk > s_casc)
    floor = float(np.median(h[interior])) if interior.any() else float(np.median(h[u < 0.72]))
    # ---------------------------------------------- meseta granítica y paredes
    ruido = spectral_noise((n, n), 3.2, seed + 3)
    alto = floor + wall_h * (1.0 + 0.10 * ruido)
    # valles laterales colgados: muescas en la meseta que llegan al borde de la pared
    lateral = np.zeros((n, n))
    for a in rng.uniform(0, 2 * np.pi, 5):
        kk = int(rng.integers(int(0.25 * ax.shape[0]), int(0.85 * ax.shape[0])))
        px, pz = ax[kk]
        lado = np.array([np.cos(a), np.sin(a)])
        q = np.c_[xx.ravel() - px, zz.ravel() - pz] @ lado
        perp = np.abs(np.c_[xx.ravel() - px, zz.ravel() - pz] @ np.array([-lado[1], lado[0]]))
        mask = (q > semi[kk] * 0.85) & (q < semi[kk] + 700.0)
        lateral = np.maximum(lateral, (mask * np.exp(-(perp / 55.0) ** 2)).reshape(n, n))
    alto = alto - 38.0 * lateral
    pared = np.clip((u - 0.72) / 0.28, 0, 1) ** 0.55
    fondo_eje = np.where(sk <= s_casc, floor + lip_h, floor)      # valle colgado aguas arriba
    perfil = fondo_eje + (alto - fondo_eje) * pared
    enlace = np.clip((2.4 - u) / 0.8, 0, 1)                         # hacia el terreno exterior
    nuevo = np.where(u <= 1.0, perfil, np.maximum(h, h + (alto - h) * enlace))
    # aguas abajo de la garganta la meseta no debe tapar la salida al desierto
    nuevo = np.where((sk > 0.97) & (u > 1.0), h, nuevo)
    # roca aborregada alargada en el sentido del hielo, centrada en el punto de los Jardines
    kc = int(tree.query([jx, jz])[1])
    tdir = ax[min(kc + 5, ax.shape[0] - 1)] - ax[max(kc - 5, 0)]
    tdir /= np.linalg.norm(tdir) + 1e-9
    rx = (xx - jx) * tdir[0] + (zz - jz) * tdir[1]
    rz = -(xx - jx) * tdir[1] + (zz - jz) * tdir[0]
    domo = 15.0 * np.clip(1 - (rx / 260.0) ** 2 - (rz / 150.0) ** 2 + 0.25 * ruido, 0, 1) ** 0.7
    nuevo = np.where(u < 0.9, nuevo + domo, nuevo)
    zona = u < 2.4
    h = np.where(zona, nuevo, h)
    # ---------------------------------------------- cadena de lagos a lo largo del río
    lagos = np.zeros((n, n), bool)
    j = int(np.searchsorted(s, s_casc + 0.04))
    while j < ax.shape[0] - 10:
        largo = int(rng.integers(12, 30))
        seg = ax[j:min(ax.shape[0] - 8, j + largo)]
        if seg.shape[0] < 3:
            break
        t2 = cKDTree(seg)
        dl, _ = t2.query(np.c_[xx.ravel(), zz.ravel()], distance_upper_bound=200.0)
        dl = np.where(np.isfinite(dl), dl, 1e9).reshape(n, n)
        ancho = rng.uniform(45, 115) * (1.0 + 0.3 * ruido)
        lagos |= (dl < ancho) & (u < 0.70)
        j += largo + int(rng.integers(8, 18))
    prof = lake_depth * np.clip(ndi.distance_transform_edt(lagos) * dx / 40.0, 0, 1)
    h = np.where(lagos, floor - 1.0 - prof, h)
    # garganta: umbral 1 m bajo el fondo
    garg = (sk > 0.90) & (u < 0.75)
    h = np.where(garg, np.minimum(h, floor - 1.0), h)
    # roca: meseta y paredes son granito; el fondo tiene 3 m de aluvión
    b = np.where(zona & (u > 0.72), h, np.minimum(b, h - 3.0 * (u <= 0.72)))
    return h, b, lagos
