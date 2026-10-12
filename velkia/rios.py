"""Río Velkia: trazado antecedente (meandros por migración), desembocadura, afluentes y
rasterización a la malla.

El río nace en un circo con lago de alta montaña dentro de la Cordillera, baja por un valle
glaciar a los Jardines, cruza el desierto y corta la meseta de los cañones (pasa por el canal
de Vieja Velkia) hasta un estuario en la costa sureste.  Su planta se genera con un modelo de
migración de meandros (Howard & Knutson 1984): la tasa de migración lateral depende de la
curvatura local y de la curvatura aguas arriba ponderada exponencialmente.  El ancho del cauce
varía a lo largo del río (campo aleatorio suave) y con él la escala de influencia aguas arriba
y la velocidad de migración; cada tramo tiene su sinuosidad objetivo y su erodibilidad (unos
casi rectos, otros muy sinuosos, con cortes y lagos en herradura) y la llanura es heterogénea.
Los meandros se forman sobre la llanura baja ANTES del levantamiento de la meseta; al
levantarse, el río se encaja y quedan meandros encajados (como los Goosenecks del San Juan).
"""
import numpy as np
from numba import njit
from scipy import ndimage as ndi

from .layout import N, RESERVADOS, poi_blocks, px2b
from .noise import spectral_noise

ANCHO_MIN, ANCHO_MAX = 14.0, 34.0     # ancho del cauce principal (bloques)
FUENTE = (3050, 1480)                 # circo glaciar con lago, vertiente sur de la Cordillera

# tipos de tramo: (rango de sinuosidad objetivo, erodibilidad relativa de las orillas)
TIPOS_TRAMO = {
    'recto': ((1.03, 1.15), 0.45),
    'medio': ((1.30, 1.75), 1.00),
    'muy': ((2.60, 3.40), 1.40),      # limitado por cortes: migra hasta el final y deja lagos en herradura
}

# construcciones que los meandros no invaden: cajas (x0, z0, x1, z1) en bloques
EVITAR = {
    'gran_piramide': (4061, 3207, 4551, 3697),
    'explanada_esfinge': (4016, 3698, 4460, 4072),
    'thza': (4464, 3698, 4851, 4197),
    'jardines_colgantes': (2163, 2473, 2442, 2807),
    'vieja_velkia': (6327, 5553, 6986, 6064),
    'aldea_fantasma_sur': (4335, 6212, 4590, 6461),
    'aldea_fantasma_oeste': (1267, 3506, 1516, 3755),
    'torre_llama_eterna': (7204, 3800, 7459, 4055),
}
for _k, ((_px, _py), _r, _) in RESERVADOS.items():
    _x, _z = px2b(_px, _py)
    EVITAR[_k] = (_x - _r, _z - _r, _x + _r, _z + _r)

# afluentes (bloques, de la fuente a la confluencia o al sumidero)
AFLUENTES = {
    # nace en el borde oeste de la meseta de los cañones, rodea por el sur la Aldea fantasma
    # sur (a ~80 bloques de su caja, como el río del plano original) y muere en el salar
    'rio_salado': [(5450, 6150), (5050, 6260), (4720, 6420), (4520, 6545), (4300, 6530),
                   (4080, 6420), (3850, 6330), (3650, 6300)],
    # cañón lateral de la meseta que baja hacia el NNE y se une al río a la salida del canal
    # de Vieja Velkia (con la costa actual el trazado original desde el SSE caía en el mar)
    'canon_lateral': [(6640, 6560), (6740, 6380), (6860, 6190), (6975, 6030)],
}


# puntos de paso (bloques). 'fijo' = tramo que no migra.
def waypoints(canal_pts):
    jx, jz = poi_blocks('jardines_de_velkia')
    pts = [
        (FUENTE, 'fijo'),             # circo glaciar con lago de alta montaña
        ((2850, 1650), 'fijo'),       # valle glaciar que baja al suroeste
        ((2560, 1830), 'fijo'),
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
        ((7560, 7650), 'fijo'),       # sin máscara de tierra: sigue hasta el borde del mapa
        ((7650, 8000), 'fijo'),
    ]
    return pts


def _arclen(xy):
    return np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]


def _resample(xy, fixed, ds, *attrs):
    """Remuestrea una polilínea a paso ds; 'fijo' y los atributos se interpolan."""
    d = _arclen(xy)
    nseg = max(1, int(round(d[-1] / ds)))
    s = np.linspace(0, d[-1], nseg + 1)
    out = np.c_[np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1])]
    f = np.interp(s, d, fixed.astype(float)) > 0.5
    return (out, f) + tuple(np.interp(s, d, a) for a in attrs)


def _smooth_path(pts, ds=10.0):
    """Curva suave (Catmull-Rom centrípeta: sin bucles con puntos muy desiguales)."""
    P = np.array([p for p, _ in pts], float)
    F = np.array([k == 'fijo' for _, k in pts])
    P2 = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    fl = []
    for i in range(1, len(P2) - 2):
        p0, p1, p2, p3 = P2[i - 1], P2[i], P2[i + 1], P2[i + 2]
        t1 = np.linalg.norm(p1 - p0) ** 0.5 + 1e-6
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5 + 1e-6
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5 + 1e-6
        nt = max(2, int(np.linalg.norm(p2 - p1) / ds))
        t = np.linspace(t1, t2, nt, endpoint=False)[:, None]
        a1 = ((t1 - t) * p0 + t * p1) / t1
        a2 = ((t2 - t) * p1 + (t - t1) * p2) / (t2 - t1)
        a3 = ((t3 - t) * p2 + (t - t2) * p3) / (t3 - t2)
        b1 = ((t2 - t) * a1 + t * a2) / t2
        b2 = ((t3 - t) * a2 + (t - t1) * a3) / (t3 - t1)
        out.append(((t2 - t) * b1 + (t - t1) * b2) / (t2 - t1))
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
        e = np.exp(-alpha[i] * seg[i])
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


def _ruido_1d(n, ds, lmin, lmax, rng, beta=1.5):
    """Ruido de espectro ancho (potencia ~ k^-beta entre longitudes de onda lmin y lmax), std 1."""
    k = np.fft.rfftfreq(n, ds)
    amp = np.zeros_like(k)
    banda = (k >= 1.0 / lmax) & (k <= 1.0 / lmin)
    amp[banda] = k[banda] ** (-beta / 2.0)
    f = np.fft.irfft(amp * (rng.standard_normal(k.size) + 1j * rng.standard_normal(k.size)), n)
    return f / (f.std() + 1e-12)


def campos_rio(xy, fixed, seed=3, movilidad=None):
    """Campos sobre la coordenada de valle s (longitud de arco de la curva inicial, bloques).

    'ancho': ancho del cauce (campo suave aleatorio, ANCHO_MIN-ANCHO_MAX, algo mayor aguas abajo).
    Tramos: límites 'lim', tipo, sinuosidad objetivo 'meta' (-1 en tramos fijos), erodibilidad
    'erod' y 'alfa' (alpha = alfa / ancho: rozamiento y calado distintos por tramo).  Los tramos
    sin movilidad (función 'movilidad' casi nula: costa, construcciones) quedan 'inmovil'.
    """
    rng = np.random.default_rng(seed + 101)
    d = _arclen(xy)
    L = d[-1]
    s = np.arange(0.0, L + 25.0, 25.0)
    u = ndi.gaussian_filter1d(rng.standard_normal(s.size), 600.0 / 25.0, mode='nearest')
    u = 0.8 * (u - u.min()) / (np.ptp(u) + 1e-9) + 0.2 * s / L
    u = (u - u.min()) / (np.ptp(u) + 1e-9)
    ancho = ANCHO_MIN + (ANCHO_MAX - ANCHO_MIN) * u
    libre = np.interp(s, d, (~fixed).astype(float)) > 0.5
    # tramos: fijos tal cual; los libres se parten en trozos de 0,5-1,3 km
    lim, tipo = [0.0], []
    k = 0
    while k < s.size:
        j = k
        while j + 1 < s.size and libre[j + 1] == libre[k]:
            j += 1
        a, b = s[k], (s[j + 1] if j + 1 < s.size else L)
        if libre[k]:
            cortes = [a]
            while b - cortes[-1] > 1.3e3:
                cortes.append(cortes[-1] + rng.uniform(500.0, 1300.0))
            if b - cortes[-1] < 400.0 and len(cortes) > 1:
                cortes.pop()
            lim += cortes[1:] + [b]
            tipo += ['libre'] * len(cortes)
        else:
            lim.append(b)
            tipo.append('fijo')
        k = j + 1
    lim[-1] = L + 1.0
    if movilidad is not None:
        tid = np.clip(np.searchsorted(lim, d, 'right') - 1, 0, len(tipo) - 1)
        m = np.bincount(tid, movilidad(xy), len(tipo)) / np.maximum(np.bincount(tid, minlength=len(tipo)), 1)
        tipo = ['inmovil' if t == 'libre' and mi < 0.05 else t for t, mi in zip(tipo, m)]
    ilib = [i for i, t in enumerate(tipo) if t == 'libre']
    cats = []
    for _ in ilib:
        op = [c for c in TIPOS_TRAMO if not cats or c != cats[-1]]
        cats.append(op[rng.integers(len(op))])
    if len(ilib) >= 3:   # al menos un tramo de cada tipo
        largos = np.diff(lim)[ilib]
        for c in ('muy', 'recto', 'medio'):
            if c not in cats:
                cand = [i for i in np.argsort(-largos) if cats.count(cats[i]) > 1]
                cats[cand[0]] = c
    meta = np.full(len(tipo), -1.0)
    erod = np.zeros(len(tipo))
    alfa = np.full(len(tipo), 0.75)
    for i, c in zip(ilib, cats):
        (lo, hi), e = TIPOS_TRAMO[c]
        meta[i] = rng.uniform(lo, hi)
        erod[i] = e * rng.uniform(0.8, 1.2)
        alfa[i] = rng.uniform(0.5, 1.05)
        tipo[i] = c
    return {'s': s, 'ancho': ancho, 'lim': np.array(lim), 'tipo': tipo, 'meta': meta, 'erod': erod,
            'alfa': alfa}


def _dist_cajas(xy, cajas):
    d = np.full(len(xy), np.inf)
    for x0, z0, x1, z1 in cajas:
        ex = np.maximum(np.maximum(x0 - xy[:, 0], xy[:, 0] - x1), 0)
        ez = np.maximum(np.maximum(z0 - xy[:, 1], xy[:, 1] - z1), 0)
        d = np.minimum(d, np.hypot(ex, ez))
    return d


def _distancia_costa(land, dx):
    """Distancia con signo a la costa (bloques): positiva en tierra."""
    din = ndi.distance_transform_edt(land)
    dout = ndi.distance_transform_edt(~land)
    return ((din - dout) * dx).astype(np.float32)


def _muestrear(campo, xy, dx):
    return ndi.map_coordinates(campo, [xy[:, 1] / dx - 0.5, xy[:, 0] / dx - 0.5], order=1, mode='nearest')


def _movilidad(evitar=None, dist=None, dx=None, margen=50.0, rampa=200.0, costa=(120.0, 300.0)):
    """Factor [0, 1] de migración por vértice: se anula junto a construcciones y a la costa."""
    cajas = list((EVITAR if evitar is None else evitar).values())

    def f(xy):
        m = np.clip((_dist_cajas(xy, cajas) - margen) / rampa, 0, 1) if cajas else np.ones(len(xy))
        if dist is not None:
            m *= np.clip((_muestrear(dist, xy, dx) - costa[0]) / costa[1], 0, 1)
        return m
    return f


def _heterogeneidad(seed):
    """Erodibilidad de la llanura (tapones de arcilla, terrazas): campo 2D en [0,35, 1,65]."""
    g = spectral_noise((256, 256), 2.2, seed + 7, kmin=4.0, kmax=60.0).astype(np.float64)
    c = N / 256.0
    return lambda xy: np.clip(1.0 + 0.4 * _muestrear(g, xy, c), 0.35, 1.65)


def _migrar(xy, fixed, campos, movilidad, seed, steps, log=False, perturbacion=0.8, rate=0.03):
    """Núcleo de la migración HK.  Devuelve xy, fixed, oxbows y la coordenada de valle de cada vértice."""
    rng = np.random.default_rng(seed)
    s_c, w_c = campos['s'], campos['ancho']
    lim, meta, erod = campos['lim'], campos['meta'].copy(), campos['erod']
    alfa = campos.get('alfa', np.full(len(meta), 0.75))
    vlen = np.diff(lim)
    ds = 0.5 * w_c.min()
    xy, fixed, sv = _resample(xy, fixed, ds, _arclen(xy))
    w = np.interp(sv, s_c, w_c)
    ntaper = int(10 * w.mean() / ds)
    nsm = int(6 * w.mean() / ds)
    het = _heterogeneidad(seed)
    mov = movilidad if movilidad is not None else (lambda p: np.ones(len(p)))
    omega, gamma = -1.0, 2.5

    def geometria(xy):
        t_ = np.gradient(xy, axis=0)
        t_ /= np.linalg.norm(t_, axis=1)[:, None] + 1e-9
        nrm = np.c_[-t_[:, 1], t_[:, 0]]
        ang = np.unwrap(np.arctan2(t_[:, 1], t_[:, 0]))
        seg = np.r_[ds, np.hypot(*np.diff(xy, axis=0).T)]
        curv = _smooth1d(np.gradient(ang) / np.maximum(seg, 1e-3), 5)
        return nrm, seg, curv

    # perturbación inicial de espectro ancho (5 a 80 anchos), proporcional al ancho local
    nrm, _, _ = geometria(xy)
    taper = _smooth1d((~fixed).astype(float), ntaper)
    pert = _ruido_1d(len(xy), ds, 5 * w.mean(), 80 * w.mean(), rng)
    m0 = taper * mov(xy)
    xy = xy + (perturbacion * pert * w * m0)[:, None] * nrm
    # tramos sin movilidad (junto a la costa o a construcciones) no cuentan para terminar
    tid = np.clip(np.searchsorted(lim, sv, 'right') - 1, 0, len(meta) - 1)
    mtr = np.bincount(tid, m0, minlength=len(meta)) / np.maximum(np.bincount(tid, minlength=len(meta)), 1)
    meta[mtr < 0.05] = -1.0
    oxbows = []
    for it in range(steps):
        w = np.interp(sv, s_c, w_c)
        nrm, seg, curv = geometria(xy)
        tid = np.clip(np.searchsorted(lim, sv, 'right') - 1, 0, len(meta) - 1)
        R = (omega * curv + gamma * _upstream_weighted(curv, seg, alfa[tid] / w)) * 3.0 * w
        largo = np.bincount(tid, np.r_[seg[1:], 0.0], minlength=len(meta))
        sinu = largo / vlen
        act = np.clip((meta - sinu) / 0.08, 0, 1)
        if not act.any():
            break
        fac = _smooth1d(erod[tid] * act[tid], nsm)
        taper = _smooth1d((~fixed).astype(float), ntaper)
        step = np.clip(R, -1, 1) * rate * w * fac * taper * mov(xy) * het(xy)
        xy = xy - step[:, None] * nrm   # hacia la orilla exterior
        # suavizado débil anti-ruido de malla
        xs = xy.copy()
        xs[1:-1] = 0.25 * xy[:-2] + 0.5 * xy[1:-1] + 0.25 * xy[2:]
        k = 0.03 * (~fixed)[:, None]
        xy = xy * (1 - k) + xs * k
        xy, fixed, sv = _resample(xy, fixed, ds, sv)
        if it % 5 == 0:
            xy, fixed, sv, cut = _cutoffs(xy, fixed, sv, np.interp(sv, s_c, w_c), ds)
            oxbows += cut
        if log and it % 500 == 0:
            txt = ' '.join('%.2f/%.2f' % (a, b) for a, b in zip(sinu, meta) if b > 0)
            print('  meandros', it, 'sinuosidad/objetivo', txt, 'oxbows', len(oxbows), flush=True)
    return xy, fixed, oxbows, sv


def meander(xy, fixed, width=22.0, steps=4000, seed=3, target_sinuosity=1.6, log=False,
            campos=None, movilidad=None):
    """Migración de meandros (Howard & Knutson 1984) con cortes (lagos en herradura).

    R1(s) = Omega*C(s) + Gamma * int C(s - xi) exp(-alpha xi) dxi / int exp(-alpha xi) dxi
    con alpha = 0,75/ancho local y tasa de migración proporcional al ancho local.
    Sin 'campos' el ancho y la sinuosidad objetivo son uniformes (width, target_sinuosity).
    Devuelve la polilínea final, la marca de tramos fijos y los meandros abandonados.
    """
    if campos is None:
        L = _arclen(xy)[-1]
        campos = {'s': np.array([0.0, L]), 'ancho': np.array([width, width]),
                  'lim': np.array([0.0, L + 1.0]), 'meta': np.array([target_sinuosity]),
                  'erod': np.array([1.0]), 'tipo': ['libre']}
    xy, fixed, oxbows, _ = _migrar(xy, fixed, campos, movilidad, seed, steps, log)
    return xy, fixed, oxbows


def _cutoffs(xy, fixed, sv, w, ds, maxloop=4000.0):
    """Cortes de cuello: dos puntos del cauce a menos de 1,2 anchos con un lazo largo entre ellos."""
    from scipy.spatial import cKDTree
    pares = cKDTree(xy).query_pairs(1.2 * w.max(), output_type='ndarray')
    if len(pares) == 0:
        return xy, fixed, sv, []
    i, j = pares.min(1), pares.max(1)
    wm = 0.5 * (w[i] + w[j])
    lazo = (j - i) * ds
    cf = np.r_[0, np.cumsum(fixed)]
    ok = ((np.hypot(*(xy[i] - xy[j]).T) < 1.2 * wm) & (lazo > 6.0 * wm) & (lazo < maxloop) &
          (cf[j + 1] - cf[i] == 0))
    if not ok.any():
        return xy, fixed, sv, []
    i, j = i[ok], j[ok]
    usado = np.zeros(len(xy), bool)
    cortes = []
    for a, b in sorted(zip(i, j), key=lambda p: p[1] - p[0]):
        if not usado[a:b + 1].any():
            usado[a:b + 1] = True
            cortes.append((a, b))
    cortes.sort()
    cut = [xy[a:b + 1].copy() for a, b in cortes]
    keep = np.ones(len(xy), bool)
    for a, b in cortes:
        keep[a + 1:b] = False
    nuevo = np.cumsum(keep) - 1
    xy, fixed, sv = xy[keep], fixed[keep], sv[keep]
    for a, _ in cortes:   # alisar la unión del corte
        c = nuevo[a]
        lo, hi = max(c - 6, 1), min(c + 7, len(xy) - 1)
        libre = ~fixed[lo:hi, None]
        for _ in range(3):
            xs = 0.25 * xy[lo - 1:hi - 1] + 0.5 * xy[lo:hi] + 0.25 * xy[lo + 1:hi + 1]
            xy[lo:hi] = np.where(libre, xs, xy[lo:hi])
    return xy, fixed, sv, cut


def _desembocadura(xy, fixed, anchos, land, dx, dist, desde):
    """Recorta el cauce donde entra al mar (aguas abajo de 'desde') y deja 2-3 celdas mar adentro."""
    nz, nx = land.shape
    assert nz == nx, 'máscara de tierra cuadrada'

    def tierra(p):
        p = np.atleast_2d(p)
        return land[np.clip((p[:, 1] // dx).astype(int), 0, nz - 1),
                    np.clip((p[:, 0] // dx).astype(int), 0, nx - 1)]

    k0 = int(np.argmin(np.hypot(*(xy - np.asarray(desde, float)).T)))
    mar = np.nonzero(~tierra(xy[k0:]))[0]
    d = _arclen(xy)
    if mar.size == 0:
        boca = {'x': float(xy[-1, 0]), 'z': float(xy[-1, 1]), 'i': len(xy) - 1, 'en_costa': False,
                'ancho_cauce': float(anchos[-1]), 'ancho': float(anchos[-1]), 'anchos': anchos}
        return xy, fixed, boca
    i = k0 + int(mar[0])
    a, b = xy[i - 1].copy(), xy[i].copy()
    for _ in range(20):
        m = 0.5 * (a + b)
        if tierra(m)[0]:
            a = m
        else:
            b = m
    pc = b
    # dirección del cauce en los últimos ~250 bloques y normal de la costa hacia el mar
    j = int(np.searchsorted(d, d[i - 1] - 250.0))
    t = pc - xy[min(j, i - 1)]
    t /= np.linalg.norm(t) + 1e-9
    ds_ = ndi.gaussian_filter(dist, 100.0 / dx)
    gz, gx = np.gradient(ds_)
    g = -np.array([_muestrear(gx, pc[None], dx)[0], _muestrear(gz, pc[None], dx)[0]])
    ncos = g / (np.linalg.norm(g) + 1e-9)
    u = t if t @ ncos > 0.5 else (t + ncos) / (np.linalg.norm(t + ncos) + 1e-9)
    # extensión recta mar adentro: la más corta que deja 2-3 celdas de mar al final de la cadena
    base = np.vstack([xy[max(i - 40, 0):i], pc])
    mejor = None
    for lext in (2.5, 3.0, 2.0, 3.5, 1.5, 4.0):
        ext = pc + np.outer(np.linspace(0, lext * dx, 6)[1:], u)
        en_mar = ~land.ravel()[rasterize_chain(np.vstack([base, ext]), nx, dx)]
        nmar = int(np.argmin(en_mar[::-1])) if not en_mar.all() else en_mar.size
        if mejor is None or abs(nmar - 2.5) < abs(mejor[1] - 2.5):
            mejor = (ext, nmar)
        if 2 <= nmar <= 3:
            break
    ext, nmar = mejor
    out = np.vstack([xy[:i], pc, ext])
    fout = np.r_[fixed[:i], np.ones(1 + len(ext), bool)]
    # ancho sugerido: embudo de ~6 anchos, limitado por la bahía; estuario si la boca está
    # en el fondo de una bahía, delta si sale a costa abierta
    w0 = float(anchos[i - 1])
    perp = np.array([-u[1], u[0]])
    q = pc + 3 * dx * u
    lados = []
    for sg in (1, -1):
        r = np.arange(dx / 2, 1500.0, dx / 2)
        en_t = tierra(q + sg * np.outer(r, perp))
        lados.append(r[np.argmax(en_t)] if en_t.any() else 1500.0)
    bahia = float(sum(lados))
    zz, xx = np.mgrid[-500:501:dx, -500:501:dx]
    disco = np.hypot(zz, xx) <= 500
    frac_mar = float((~tierra(np.c_[pc[0] + xx[disco], pc[1] + zz[disco]])).mean())
    ancho = float(np.clip(6.0 * w0, 60.0, 200.0))
    ancho = float(max(min(ancho, 0.6 * bahia), 2.0 * w0))
    largo = float(min(5.0 * ancho, 0.8 * (d[i - 1] - d[k0])))
    tipo = 'estuario' if frac_mar < 0.55 else 'delta'
    # anchos por vértice con el embudo del estuario
    dsal = np.r_[d[i - 1] - d[:i], np.zeros(1 + len(ext))]
    fun = np.exp(np.log(ancho / w0) * np.clip(1.0 - dsal / max(largo, 1.0), 0, 1))
    an = np.r_[anchos[:i], np.full(1 + len(ext), w0)] * fun
    boca = {'x': float(pc[0]), 'z': float(pc[1]), 'i': i, 'en_costa': True,
            'dir': (float(u[0]), float(u[1])), 'normal_costa': (float(ncos[0]), float(ncos[1])),
            'ancho_cauce': w0, 'ancho': ancho, 'largo': largo, 'tipo': tipo,
            'bahia': bahia, 'frac_mar': frac_mar, 'celdas_mar': nmar, 'anchos': an}
    return out, fout, boca


def disenar_rio(canal_pts, seed=3, log=False, land=None, dx=None, evitar=None, steps=6000):
    """Trazado del río Velkia de la fuente (circo de la Cordillera) a la costa.

    canal_pts: polilínea (k, 2) del canal de Vieja Velkia (x, z en bloques).
    land: máscara bool 2D [z, x] de tierra (p. ej. Layout(n).land) y dx bloques/celda
    (por defecto N / n).  evitar: cajas {nombre: (x0, z0, x1, z1)} que los meandros no
    invaden (por defecto EVITAR).
    Sin land devuelve (xy, fixed, oxbows) como antes: xy (m, 2) float, fixed (m,) bool y una
    lista de polilíneas (k, 2) de meandros abandonados; la línea sigue hasta el borde del mapa.
    Con land los meandros no se acercan a la costa, la polilínea se recorta donde entra al mar
    (aguas abajo del canal) dejando 2-3 celdas mar adentro, y devuelve además el dict 'boca':
    x, z (cruce de la costa), i (índice en xy), dir (unitario hacia el mar), normal_costa,
    ancho_cauce, ancho (sugerido del estuario en la costa), largo (del embudo aguas arriba),
    tipo ('estuario' | 'delta'), bahia, frac_mar, celdas_mar, en_costa y anchos (ancho del
    cauce en cada vértice de xy, con el embudo del estuario).
    """
    pts = waypoints(canal_pts)
    xy, fixed = _smooth_path(pts, 10.0)
    dist = None
    if land is not None:
        land = np.asarray(land, bool)
        dx = float(dx) if dx is not None else N / land.shape[1]
        dist = _distancia_costa(land, dx)
    mov = _movilidad(evitar, dist, dx)
    campos = campos_rio(xy, fixed, seed, mov)
    xy2, fixed2, oxbows, sv = _migrar(xy, fixed, campos, mov, seed, steps, log)
    if land is None:
        return xy2, fixed2, oxbows
    anchos = np.interp(sv, campos['s'], campos['ancho'])
    xy3, fixed3, boca = _desembocadura(xy2, fixed2, anchos, land, dx, dist, np.asarray(canal_pts)[-1])
    return xy3, fixed3, oxbows, boca


def disenar_afluente(puntos, seed=None, sinuosidad=1.15, ancho=10.0, evitar=None):
    """Afluente: curva suave por los puntos (bloques, de la fuente a la confluencia o al sumidero)
    con ondulaciones de espectro ancho (8-40 anchos) hasta la sinuosidad pedida (longitud del
    cauce / longitud de la curva suave).  Los extremos quedan fijos y no se acerca a las
    construcciones de 'evitar' (por defecto EVITAR).  Devuelve xy (m, 2) float."""
    P = np.asarray(puntos, float)
    rng = np.random.default_rng(int(np.abs(P).sum()) % (2 ** 31) if seed is None else seed)
    ds = ancho / 2
    xy, fixed = _smooth_path([(tuple(p), 'libre') for p in P], ds)
    xy, _ = _resample(xy, fixed, ds)
    t_ = np.gradient(xy, axis=0)
    t_ /= np.linalg.norm(t_, axis=1)[:, None] + 1e-9
    nrm = np.c_[-t_[:, 1], t_[:, 0]]
    s = _arclen(xy)
    L = s[-1]
    rampa = np.clip(np.minimum(s, L - s) / (10 * ancho), 0, 1)
    m = 0.5 - 0.5 * np.cos(np.pi * rampa)
    m *= _movilidad(evitar, margen=40.0, rampa=150.0)(xy)
    ruido = _ruido_1d(len(xy), ds, 8 * ancho, 40 * ancho, rng, beta=2.0) * m
    lo, hi = 0.0, 20.0 * ancho
    for _ in range(40):
        a = 0.5 * (lo + hi)
        if _arclen(xy + (a * ruido)[:, None] * nrm)[-1] / L < sinuosidad:
            lo = a
        else:
            hi = a
    return xy + (lo * ruido)[:, None] * nrm


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
