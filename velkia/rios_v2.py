"""Ríos de la v2 (trazado del lienzo aprobado) tallados a 1 bloque.

Trazado (malla gruesa, bloques):
  * principal: nace en el flanco de la cumbre de la cordillera (Y~320), baja al valle colgado, cae a
    los Jardines, los rodea, cruza las dunas y baja por los domos, donde adelgaza; tras Vieja Velkia
    se parte: un brazo sigue al estuario del este y otro baja a la costa sur;
  * afluentes: dos bajan del macizo central hacia el sur hasta el principal; uno baja de la meseta
    del noroeste al fondo de los Jardines;
  * mura: nacimiento en su cumbre -> lago morado -> manantial que baja al principal.
Tallado (1 bloque): el nivel del agua sigue el terreno (1 bloque bajo la orilla) y nunca sube aguas
abajo; donde el terreno se eleva por encima del nivel la montaña se abre en valle (laderas
~40°, no un tajo); donde el nivel cae más de 3 bloques hay cascada (columna de agua); cada río
nace en una poza con una caída de agua contra la ladera.
"""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from .etapa4 import _densificar, _por_teselas, cauce
from .layout import N, SEA
from .volcan import _trazar
from .zonas_v1 import Z

ESCALA_ANCHO = 2.4          # ancho del lienzo -> bloques


def _sinuoso(pts, amp=60.0, paso=40.0, seed=0):
    """Polilínea suave (Chaikin) con meandros suaves."""
    pts = np.asarray(pts, float)
    for _ in range(4):
        q = 0.75 * pts[:-1] + 0.25 * pts[1:]
        r = 0.25 * pts[:-1] + 0.75 * pts[1:]
        pts = np.r_[pts[:1], np.c_[q, r].reshape(-1, 2), pts[-1:]]
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    t = np.arange(0, s[-1], paso)
    p = np.c_[np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])]
    if amp <= 0 or len(p) < 8:
        return np.r_[p, pts[-1:]]
    tg = np.gradient(p, axis=0)
    nr = np.c_[-tg[:, 1], tg[:, 0]] / (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-9)
    off = np.convolve(np.random.default_rng(seed).standard_normal(len(p)), np.hanning(9) / np.hanning(9).sum(),
                      'same') * amp * 2.5
    off[:3] = 0
    off[-3:] = 0
    return p + nr * off[:, None]


def trazados(d, z, mar=None):
    """Polilíneas (bloques) de los ríos: lista de dicts {nombre, xy, ancho, une_a}.
    z: zonas v1 nítidas (1024²).  mar: máscara del mar real en la malla gruesa (si no, el del dibujo).
    une_a: nombre del río al que desemboca (o None = mar/lago)."""
    h = d['h']
    n = h.shape[0]
    dx = N / n
    yy, xx = np.mgrid[0:n, 0:n]
    Xc, Zc = (xx + 0.5) * dx, (yy + 0.5) * dx
    mar = (z == 0) if mar is None else mar

    def hasta_mar(p):
        for k, (x, y) in enumerate(p):
            if mar[int(np.clip(y / dx, 0, n - 1)), int(np.clip(x / dx, 0, n - 1))]:
                return p[:k + 2]
        return p

    def nacimiento(cerca, hacia, zonas=(Z['montanas'],), r_pico=350.0, banda=(0.80, 0.90)):
        """Punto del flanco de la cumbre cercana (80-90 % de su altura) que mira hacia 'hacia'."""
        m = np.isin(z, zonas) & (np.hypot(Xc - cerca[0], Zc - cerca[1]) < r_pico)
        k = int(np.argmax(np.where(m, h, -1e9)))
        pz, px = divmod(k, n)
        cima = h[pz, px]
        cand = np.isin(z, zonas) & (np.hypot(Xc - Xc[pz, px], Zc - Zc[pz, px]) < 450) & \
            (h > banda[0] * cima) & (h < banda[1] * cima)
        k = int(np.argmin(np.where(cand, np.hypot(Xc - hacia[0], Zc - hacia[1]), 1e18)))
        return float(Xc.flat[k]), float(Zc.flat[k])

    def bajada(ini, obj, seed=0):
        pi, pj = _trazar(h, dx, ini, objetivo=obj, sesgo=1.2, remonta=40.0, ruido=0.05,
                         rng=np.random.default_rng(seed), max_pasos=600)
        p = np.c_[(np.array(pj) + 0.5) * dx, (np.array(pi) + 0.5) * dx][::3]
        return [tuple(ini)] + [tuple(q) for q in p[1:]] + [tuple(obj)]

    # principal: desde la celda fuente del modelado, con el nacimiento subido a la cumbre
    rio = d['rio_xy']
    c = d['chain'][int(d['k_fuente'])]
    i0 = int(np.argmin(np.hypot(rio[:, 0] - (c % n + 0.5) * dx, rio[:, 1] - (c // n + 0.5) * dx)))
    principal = rio[i0:]
    n0 = nacimiento((3044, 1476), tuple(principal[8]))
    principal = np.r_[np.array(bajada(n0, tuple(principal[12]), 1)), principal[13:]]
    principal = _sinuoso(principal, amp=0, paso=16.0)
    principal = hasta_mar(principal)

    def en_rio(x, y):
        return tuple(principal[int(np.argmin(np.hypot(principal[:, 0] - x, principal[:, 1] - y)))])

    # en los domos adelgaza; tras Vieja Velkia se parte en dos brazos
    zr = z[np.clip((principal[:, 1] / dx).astype(int), 0, n - 1), np.clip((principal[:, 0] / dx).astype(int), 0, n - 1)]
    k_domos = int(np.argmax(zr == Z['domos'])) if (zr == Z['domos']).any() else len(principal)
    ancho = np.where(np.arange(len(principal)) < k_domos, 30.0, 14.0)
    ancho = np.convolve(np.r_[np.full(20, ancho[0]), ancho, np.full(20, ancho[-1])], np.ones(41) / 41, 'valid')
    k_vv = int(np.argmin(np.hypot(principal[:, 0] - 6655, principal[:, 1] - 5808)))
    s_split = principal[min(k_vv + 22, len(principal) - 2)]       # ~350 bloques tras Vieja Velkia
    brazo = hasta_mar(_sinuoso([tuple(s_split), (7000, 6280), (6870, 6450), (6815, 6620), (6700, 6770), (6620, 7100), (6600, 7450),
                                (6520, 7800), (6480, 8100)], amp=30, seed=21))   # por lo bajo, a la costa sur
    rios = [dict(nombre='principal', xy=principal, ancho=ancho, une_a=None),
            dict(nombre='brazo_sur', xy=brazo, ancho=np.full(len(brazo), 11.0), une_a=None, nace_de='principal')]
    n1 = nacimiento((3850, 1450), (3600, 2400))
    n3 = nacimiento((4300, 1400), (4400, 2400), r_pico=220)
    nj = nacimiento((2092, 1324), (2220, 1750))
    nm = nacimiento((6550, 2050), (6650, 2250), zonas=(Z['mura'],), r_pico=300, banda=(0.97, 1.0))
    afl = [('trib_montana_1', bajada(n1, en_rio(3600, 3000), 2), 10.0, 'principal'),
           ('trib_montana_3', bajada(n3, en_rio(4400, 3000), 3), 12.0, 'principal'),
           ('trib_jardines', bajada(nj, (2220, 1750), 4) + [(2160, 1990), en_rio(2124, 2143)], 12.0, 'principal'),
           ('mura_nacimiento', [nm, (6650, 2090), (6650, 2200)], 9.0, 'lago_morado'),
           ('mura_manantial', [(6650, 2250), (6650, 2300), (6560, 2700), (6150, 3150), (5600, 3420),
                               en_rio(5136, 3596)], 16.0, 'principal')]
    for k, (nmb, pts, w, une) in enumerate(afl):
        p = _sinuoso(pts, amp=30 if w < 15 else 50, seed=k + 3)
        rios.append(dict(nombre=nmb, xy=p, ancho=np.full(len(p), w), une_a=une))
    return rios


def _perfil(Y, xy, hw):
    """Cota del suelo a lo largo del eje (mediana en el ancho, suavizada a lo largo)."""
    tg = np.gradient(xy, axis=0)
    nr = np.c_[-tg[:, 1], tg[:, 0]] / (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-9)
    muestras = []
    for f in (-0.6, -0.3, 0.0, 0.3, 0.6):
        p = xy + nr * (f * hw)[:, None]
        iz = np.clip(p[:, 1].astype(int), 0, N - 1)
        ix = np.clip(p[:, 0].astype(int), 0, N - 1)
        muestras.append(np.asarray(Y[iz, ix], np.float32))
    g = np.median(np.stack(muestras), 0)
    return ndi.median_filter(g, 9, mode='nearest')


def abrir_valle(Y, xy, nivel, hw, protegido, pend=0.8, seed=0):
    """Baja el terreno que queda sobre el nivel del río: laderas de pendiente ~'pend' desde la
    orilla (valle, no tajo).  protegido: máscara que no se toca (construcciones, mar)."""
    corte = np.nan_to_num(_perfil(Y, xy, hw) - nivel, nan=0.0)
    alc = float(hw.max() + 3.0 + np.clip(corte.max(), 0, 220) / pend)
    rng = np.random.default_rng(seed)
    ruido_v = np.convolve(rng.standard_normal(len(xy)), np.hanning(31) / np.hanning(31).sum(), 'same') * 2.0

    def fn(z0, z1, x0, x1, idx):
        t = cKDTree(xy[idx])
        zz, xx = np.mgrid[z0:z1, x0:x1]
        dd, k = t.query(np.c_[xx.ravel() + 0.5, zz.ravel() + 0.5], distance_upper_bound=alc)
        ok = np.isfinite(dd)
        if not ok.any():
            return
        kk = idx[np.where(ok, k, 0)]
        lv = nivel[kk]
        ok &= np.isfinite(lv)
        p = pend * (1.0 + 0.25 * ruido_v[kk])
        tope = lv + 1.0 + np.maximum(0.0, dd - hw[kk] - 2.0) * p
        sub = Y[z0:z1, x0:x1].ravel()
        pr = protegido[z0:z1, x0:x1].ravel()
        baja = ok & ~pr & (sub > tope)
        sub = np.where(baja, tope, sub)
        Y[z0:z1, x0:x1] = sub.reshape(zz.shape)

    _por_teselas(xy, alc, Y.shape[0], fn)


def tallar(Y, WL, FL, mar, huella, rios, nivel_lagos=None, log=print):
    """Talla todos los ríos (en orden: principal, brazos, afluentes).  Devuelve la máscara de
    celdas donde el agua puede caer (cascadas y nacimientos) e información por río."""
    permitir = np.zeros((N, N), bool)
    protegido = mar | ndi.binary_dilation(huella, iterations=6)
    hechos = {}
    info = {}
    nivel_lagos = nivel_lagos or {}
    for r in rios:
        xy, = _densificar(r['xy'], 2.0)
        ancho = np.interp(np.linspace(0, 1, len(xy)), np.linspace(0, 1, len(r['ancho'])), r['ancho'])
        s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
        nace = r.get('nace_de') is None and not r['nombre'].startswith('mura_manantial')
        crece = np.clip(0.35 + s / 800.0, 0, 1) if nace else 1.0          # los nacimientos empiezan finos
        hw = 0.5 * ancho * ESCALA_ANCHO * crece
        iz = np.clip(xy[:, 1].astype(int), 0, N - 1)
        ix = np.clip(xy[:, 0].astype(int), 0, N - 1)
        # recorte: termina al llegar al mar o (los afluentes) a otro río ya tallado
        en_mar = mar[iz, ix]
        fin = int(np.argmax(en_mar)) + 6 if en_mar.any() else len(xy)
        if r['une_a'] in hechos:
            dd, _ = cKDTree(hechos[r['une_a']]['xy']).query(xy)
            junto = dd < hechos[r['une_a']]['hw_med']
            if junto[10:].any():
                fin = min(fin, int(np.argmax(junto[10:])) + 10 + 2)
        xy, hw, s = xy[:fin], hw[:fin], s[:fin]
        g = _perfil(Y, xy, hw)
        inicio = None
        if r.get('nace_de') in hechos:                    # brazo: sale al nivel del río madre
            m = hechos[r['nace_de']]
            dd, k = cKDTree(m['xy']).query(xy[0])
            inicio = float(m['nivel'][k])
        if r['nombre'] == 'mura_manantial' and 'lago_morado' in nivel_lagos:
            inicio = float(nivel_lagos['lago_morado'])
        gg = np.floor(g) - 1.0
        if inicio is not None:
            gg[0] = min(gg[0], inicio)
        nivel = np.minimum.accumulate(gg)
        nivel = np.maximum(nivel, SEA)
        # afluente: no queda por debajo del nivel del río (o lago) al que llega
        destino = None
        if r['une_a'] in hechos:
            m = hechos[r['une_a']]
            dd, k = cKDTree(m['xy']).query(xy[-1])
            destino = float(m['nivel'][k])
        elif r['une_a'] in nivel_lagos:
            destino = float(nivel_lagos[r['une_a']])
        if destino is not None:
            nivel = np.maximum(nivel, destino)
        abrir_valle(Y, xy, nivel, hw, protegido, seed=len(info))
        # cascadas: donde el nivel cae más de 3 bloques, columna de agua del nivel de arriba
        lvc = nivel.copy()
        caidas = np.nonzero(np.diff(nivel) < -3)[0]
        cerca_casc = np.zeros(len(xy), bool)
        for k in caidas:
            lvc[k + 1:k + 4] = nivel[k]
            cerca_casc[max(0, k - 3):k + 8] = True
        seco = huella
        if r['une_a'] is not None:
            # el tramo final sí moja dentro del río destino (sin cambiar su nivel)
            seco = huella | ((FL > 0) & ~mar & (WL != np.int16(destino if destino is not None else -1)))
        prof = np.clip(hw / 3.0, 2.0, 6.0)
        cauce(Y, WL, FL, xy, 2 * hw, lvc, prof, seco=seco, sin_orilla=cerca_casc, mar=mar)
        for k in np.nonzero(cerca_casc)[0]:
            x, z = xy[k]
            rr = int(hw[k] + 6)
            permitir[max(0, int(z) - rr):int(z) + rr, max(0, int(x) - rr):int(x) + rr] = True
        if nace:
            _nacimiento(Y, WL, FL, xy, nivel, hw, permitir)
        hechos[r['nombre']] = dict(xy=xy, nivel=nivel, hw_med=float(np.median(hw)) + 4.0)
        info[r['nombre']] = dict(largo=float(s[-1]) if len(s) else 0.0, nace=float(nivel[0]),
                                 llega=float(nivel[-1]), cascadas=int(len(caidas)),
                                 corte_max=float(np.nanmax(g - nivel)) if len(g) else 0.0)
        log(f"  río {r['nombre']}: {info[r['nombre']]['largo']:.0f} bloques, nace Y {nivel[0]:.0f} -> "
            f"Y {nivel[-1]:.0f}, {len(caidas)} cascadas, valle abierto hasta {info[r['nombre']]['corte_max']:.0f}")
    return permitir, info


def _nacimiento(Y, WL, FL, xy, nivel, hw, permitir):
    """Poza al pie de una caída de agua que sale de la ladera (como un manantial de montaña)."""
    x0, z0 = xy[0]
    L = int(nivel[0])
    t = xy[min(6, len(xy) - 1)] - xy[0]
    t = t / (np.hypot(*t) + 1e-9)
    R = int(max(7, hw[0] + 4))
    a, b = int(z0) - R - 12, int(x0) - R - 12
    zz, xx = np.mgrid[a:a + 2 * R + 24, b:b + 2 * R + 24]
    zz, xx = np.clip(zz, 0, N - 1), np.clip(xx, 0, N - 1)
    r = np.hypot(xx + 0.5 - x0, zz + 0.5 - z0)
    poza = r < R
    Y[zz[poza], xx[poza]] = np.minimum(Y[zz[poza], xx[poza]], L - 1 - 2.5 * np.clip(1 - r[poza] / R, 0, 1))
    WL[zz[poza], xx[poza]] = L
    FL[zz[poza], xx[poza]] = 1
    # caída: columna de agua de 3x2 contra la ladera, del alto del terreno detrás de la poza
    cx, cz = x0 - t[0] * (R - 1.5), z0 - t[1] * (R - 1.5)
    detras = Y[int(np.clip(cz - t[1] * 4, 0, N - 1)), int(np.clip(cx - t[0] * 4, 0, N - 1))]
    top = int(min(max(detras, L + 4), L + 16))
    col = np.hypot(xx + 0.5 - cx, zz + 0.5 - cz) < 1.8
    WL[zz[col], xx[col]] = top
    FL[zz[col], xx[col]] = 1
    # la ladera detrás de la caída queda al menos a la altura del chorro
    pared = (np.hypot(xx + 0.5 - (cx - t[0] * 2.5), zz + 0.5 - (cz - t[1] * 2.5)) < 3.0) & ~col & ~poza
    Y[zz[pared], xx[pared]] = np.maximum(Y[zz[pared], xx[pared]], top)
    permitir[a:a + 2 * R + 24, b:b + 2 * R + 24] = True
