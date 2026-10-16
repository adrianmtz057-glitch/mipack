"""Jardines de Velkia: valle glaciar en U (modelo Yosemite).

El glaciar que bajaba de la cordillera excavó un valle en U en una meseta de granito.  El valle
sigue el eje del hielo (el mismo que hoy sigue el río): estrecho donde entra desde el norte,
ensanchado en una cubeta en el centro y estrecho otra vez en la garganta de salida.

Forma (Yosemite): fondo plano y ancho; paredes de granito casi verticales de ~230 m con un
pequeño talud al pie y el borde superior apenas redondeado; la meseta arriba.  Los glaciares
laterales, más pequeños, excavaron menos: sus valles quedan colgados en el borde de la pared y
sus arroyos caen al valle en cascada.  El río principal entra igual, por un valle colgado.
Un domo de exfoliación junto a la pared quedó cortado a pico por el glaciar (tipo Half Dome).
En el fondo, una roca aborregada alargada en el sentido del hielo y cubetas sobreexcavadas que
hoy son una cadena de lagos; el umbral rocoso de la garganta (riegel) los retiene.

Se aplica tras la historia erosiva (modelado.py) como plantilla de la erosión del glaciar de los
Jardines: el modelo de hielo a 8 bloques/celda no resuelve paredes de este tamaño.  Todas las
medidas de la pared van en bloques, así que la forma no depende de la resolución.
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


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def excavar(h, b, lay, chain, wall_h=230.0, wall_w=75.0, meseta_w=200.0, enlace_w=420.0,
            lip_h=60.0, lake_depth=7.0, domo_h=95.0, domo_r=330.0, n_colgados=5, seed=17):
    """Devuelve (h, b, lagos, info).  h, b relativos al mar; chain = celdas del río (fuente -> mar).
    info: 'cascadas' (lista de dicts x, z, y_borde, y_pie, dir), 'domo' (x, z, r), 'piso',
    'pared' (máscara de pared + meseta de granito)."""
    n = lay.n
    dx = lay.dx
    zz, xx = lay.coords()
    jx, jz = poi_blocks('jardines_de_velkia')
    rng = np.random.default_rng(seed)
    h = h.copy()
    b = b.copy()
    vacio = (h, b, np.zeros((n, n), bool), {'cascadas': [], 'domo': None, 'piso': None,
                                           'pared': np.zeros((n, n), bool)})
    # ---------------------------------------------- eje del valle (río) cerca de los Jardines
    cx = (chain % n + 0.5) * dx
    cz = (chain // n + 0.5) * dx
    rch = jardines_r(cx, cz)
    idx = np.nonzero(rch < 1.45)[0]
    if idx.size < 4:
        return vacio
    k0, k1 = idx[0], idx[-1]
    ax = np.c_[cx[k0:k1 + 1], cz[k0:k1 + 1]]
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(ax, axis=0).T))]
    largo = s[-1]
    s /= largo
    # tangente y normal del eje (suavizadas)
    tg = np.gradient(ax, axis=0)
    tg = np.c_[_suave1d(tg[:, 0], 9), _suave1d(tg[:, 1], 9)]
    tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-9
    nrm = np.c_[-tg[:, 1], tg[:, 0]]
    # semiancho del FONDO a lo largo del eje: estrecho, cubeta ancha, garganta
    base = 110.0 + 470.0 * np.sin(np.pi * np.clip((s - 0.08) / 0.80, 0, 1)) ** 0.8
    base *= 1.0 + 0.18 * _suave1d(rng.standard_normal(s.size), 25) / 0.4
    semi = np.clip(base, 95.0, 620.0)
    # entrada colgada: la cascada está donde el eje cruza la pared norte
    dentro = jardines_r(ax[:, 0], ax[:, 1]) < 0.95
    s_casc = float(s[np.argmax(dentro)]) if dentro.any() else 0.1
    # ---------------------------------------------- distancia (deformada) al eje
    # contorno en planta: entrantes y contrafuertes de cientos de bloques (no dientes de sierra)
    wu = spectral_noise((n, n), 3.0, seed + 1, kmin=4.0, kmax=35.0) * 85.0
    wv = spectral_noise((n, n), 3.0, seed + 2, kmin=4.0, kmax=35.0) * 85.0
    pts = np.c_[(xx + wu).ravel(), (zz + wv).ravel()]
    tree = cKDTree(ax)
    alcance = semi.max() + wall_w + meseta_w + enlace_w + 200.0
    d, k = tree.query(pts, distance_upper_bound=alcance)
    d = np.where(np.isfinite(d), d, 1e9).reshape(n, n)
    k = np.minimum(k, ax.shape[0] - 1).reshape(n, n)
    sk = s[k]
    dr = d - semi[k]                       # distancia al pie de la pared (<0: fondo del valle)
    # más allá de los extremos del eje: coordenada a lo largo de la tangente final/inicial
    a_fin = (xx - ax[-1, 0]) * tg[-1, 0] + (zz - ax[-1, 1]) * tg[-1, 1]
    a_ini = -((xx - ax[0, 0]) * tg[0, 0] + (zz - ax[0, 1]) * tg[0, 1])
    interior = (dr < -0.15 * semi[k]) & (sk > s_casc) & (sk < 0.9)
    floor = float(np.median(h[interior])) if interior.any() else float(np.median(h[dr < 0]))
    e_in = float(h.ravel()[chain[k0]])     # cota del río donde empieza el eje
    # ---------------------------------------------- meseta granítica
    ruido = spectral_noise((n, n), 3.2, seed + 3)
    ruido2 = spectral_noise((n, n), 3.0, seed + 4, kmax=40.0)
    alto = floor + wall_h * (1.0 + 0.08 * ruido)
    # domo cortado a pico (Half Dome): junto a la pared, hacia la salida, del lado sin colgados
    kd = int(np.searchsorted(s, 0.78))
    lado_d = 1.0 if rng.random() < 0.5 else -1.0
    dcx, dcz = ax[kd] + lado_d * nrm[kd] * (semi[kd] + 0.30 * domo_r)
    rd = np.hypot(xx - dcx, zz - dcz) / domo_r
    alto = alto + domo_h * np.sqrt(np.clip(1.0 - rd ** 2, 0, 1)) + 0.10 * domo_h * _sstep((1.25 - rd) / 0.25)
    # valles colgados: tributarios perpendiculares a la pared; su fondo queda muy por encima del
    # valle y su arroyo cae en cascada desde el borde
    cascadas = []
    usados = []
    for _ in range(n_colgados * 6):
        if len(cascadas) >= n_colgados:
            break
        kk = int(rng.integers(int(0.22 * ax.shape[0]), int(0.88 * ax.shape[0])))
        lado = 1.0 if rng.random() < 0.5 else -1.0
        if lado == lado_d and abs(s[kk] - 0.78) < 0.12:
            continue                                   # no tapar el domo
        if any(abs(s[kk] - su) < 0.10 and lado == ls for su, ls in usados):
            continue
        usados.append((s[kk], lado))
        dirn = lado * nrm[kk]
        lip = ax[kk] + dirn * (semi[kk] + wall_w)
        prof_lab = rng.uniform(70.0, 120.0)          # cuánto más bajo que la meseta queda su fondo
        ancho = rng.uniform(55.0, 90.0)
        q = (xx - lip[0]) * dirn[0] + (zz - lip[1]) * dirn[1]            # hacia fuera del valle
        p = -(xx - lip[0]) * dirn[1] + (zz - lip[1]) * dirn[0]
        p = p - 0.12 * q * np.sin(q / 260.0 + rng.uniform(0, 6.3))         # algo sinuoso
        largo_v = rng.uniform(650.0, 1000.0)
        largo_v = min(largo_v, meseta_w + 0.6 * enlace_w)       # no baja por la ladera exterior
        perfil_l = np.clip(1.0 - q / largo_v, 0, 1) ** 0.6 * (q > -wall_w)
        seccion = np.clip(1.0 - (np.abs(p) / ancho) ** 2, 0, 1) ** 0.5
        alto = alto - prof_lab * perfil_l * seccion
        cascadas.append({'x': float(lip[0]), 'z': float(lip[1]), 'dir': (float(dirn[0]), float(dirn[1])),
                         'y_borde': float(floor + wall_h - prof_lab), 'y_pie': floor, 'k': kk})
    # ---------------------------------------------- perfil transversal
    fondo_eje = np.where(sk <= s_casc,
                         floor + lip_h + max(e_in - floor - lip_h, 0.0) * np.clip(1 - sk / max(s_casc, 1e-3), 0, 1),
                         floor)
    ww = wall_w * (1.0 + 0.3 * ruido2)
    t = dr / ww
    pared = _sstep(t)
    perfil = fondo_eje + (alto - fondo_eje) * pared
    enlace = _sstep(1.0 - (dr - ww - meseta_w) / enlace_w)
    # la ladera exterior del macizo no llega a la aldea oeste (es otra zona: colinas del oeste)
    ox, oz = poi_blocks('aldea_fantasma_oeste')
    enlace = enlace * _sstep((np.hypot(xx - ox, zz - oz) - 350.0) / 350.0)
    nuevo = np.where(dr <= ww + meseta_w, perfil, np.maximum(h, h + (alto - h) * enlace))
    # roca aborregada alargada en el sentido del hielo (sobre ella van los Jardines colgantes)
    kc = int(tree.query([jx, jz])[1])
    tdir = tg[kc]
    rx = (xx - jx) * tdir[0] + (zz - jz) * tdir[1]
    rz = -(xx - jx) * tdir[1] + (zz - jz) * tdir[0]
    domo = 15.0 * np.clip(1 - (rx / 260.0) ** 2 - (rz / 150.0) ** 2 + 0.25 * ruido, 0, 1) ** 0.7
    nuevo = np.where(dr < -0.1 * semi[k], nuevo + domo, nuevo)
    # extremos del eje: la plantilla se desvanece (la salida al desierto y la entrada desde la
    # montaña quedan libres, sin un muro transversal)
    f_ext = np.clip(1.0 - np.maximum(a_fin, 0) / 450.0, 0, 1) * np.clip(1.0 - np.maximum(a_ini, 0) / 300.0, 0, 1)
    f_ext = np.where((sk > 0.97) | (sk < 0.03), f_ext, 1.0)
    f_ext = np.clip(ndi.gaussian_filter(f_ext, 90.0 / dx), 0, 1)      # sin escalones
    nuevo = h + (nuevo - h) * f_ext
    zona = (dr < ww + meseta_w + enlace_w) & (f_ext > 0)
    h = np.where(zona, nuevo, h)
    # ---------------------------------------------- cadena de lagos a lo largo del río
    lagos = np.zeros((n, n), bool)
    j = int(np.searchsorted(s, s_casc + 0.04))
    while j < ax.shape[0] - 10:
        lg = int(rng.integers(12, 30))
        seg = ax[j:min(ax.shape[0] - 8, j + lg)]
        if seg.shape[0] < 3:
            break
        t2 = cKDTree(seg)
        dl, _ = t2.query(np.c_[xx.ravel(), zz.ravel()], distance_upper_bound=200.0)
        dl = np.where(np.isfinite(dl), dl, 1e9).reshape(n, n)
        ancho_l = rng.uniform(45, 115) * (1.0 + 0.3 * ruido)
        lagos |= (dl < ancho_l) & (dr < -40.0)
        j += lg + int(rng.integers(8, 18))
    lagos &= sk < 0.9
    prof = lake_depth * np.clip(ndi.distance_transform_edt(lagos) * dx / 40.0, 0, 1)
    h = np.where(lagos, floor - 1.0 - prof, h)
    # garganta: umbral 1 m bajo el fondo
    garg = (sk > 0.90) & (dr < 0) & (f_ext > 0.5)
    h = np.where(garg, np.minimum(h, floor - 1.0), h)
    # roca: meseta y paredes son granito; el fondo tiene 3 m de aluvión
    granito = zona & (dr > 0)
    b = np.where(granito, h, np.where(zona, np.minimum(b, h - 3.0), b))
    info = {'cascadas': cascadas, 'domo': (float(dcx), float(dcz), domo_r), 'piso': floor,
            'pared': granito & (dr < ww + meseta_w)}
    return h, b, lagos, info
