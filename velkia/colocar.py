"""Colocación de las construcciones sobre un terreno dado y asiento (corte y relleno).

Devuelve, por construcción, la traslación final (dx, dz, dy) respecto de la ubicación del
mapa 2 y el terreno modificado.  Reglas:
  * Complejo Pirámide-Esfinge-Thza: un solo dy (las piezas encajan entre sí).
  * Jardines colgantes: en el domo central de los Jardines.
  * Vieja Velkia: el canal (agua a Y=87) a la cota del río; el fondo del cañón se ensancha
    en una vega (solo corte) para que la roca no entierre la ciudad.
  * Aldea oeste (terrazas): en su punto del mapa 2; el terreno ya trae preparada una ladera de
    ~3° con la orientación del diseño (modelado.ladera_aldea_oeste).
  * Aldea sur: en su punto, junto al Río Salado.
  * Torre: cima/promontorio cercano a la costa.
"""
import numpy as np
from scipy import ndimage as ndi

from .estructuras import SITIOS, Sitio, recortar
from .layout import N, SEA, poi_blocks
from .ubicacion import buscar_cima

TALUD = 0.5            # pendiente máxima del corte y del relleno alrededor de la huella (1:2)

CONSTRUCCIONES = [
    # etiqueta, sitio, carpetas, grupo (comparte dy), modo de asiento
    ('Gran Pirámide', 'complejo_piramide', ['piramide'], 'complejo', 'base'),
    ('Esfinge (explanada)', 'complejo_piramide', ['explanada_esfinge'], 'complejo', 'suelo'),
    ('Thza', 'complejo_piramide', ['thza'], 'complejo', 'suelo'),
    ('Jardines colgantes', 'jardines_colgantes', ['jardines_colgantes'], None, 'suelo'),
    ('Vieja Velkia', 'vieja_velkia', ['vieja_velkia'], None, 'suelo'),
    ('Aldea fantasma oeste', 'aldea_fantasma_oeste', ['aldea_fantasma_norte'], None, 'suelo'),
    ('Aldea fantasma sur', 'aldea_fantasma_sur', ['aldea_fantasma_sur'], None, 'suelo'),
    ('Torre de la llama eterna', 'torre_llama_eterna', ['torre_llama_eterna'], None, 'suelo'),
]


def _sitio(sitio, carpetas, shift=(0, 0)):
    cfg = dict(SITIOS[sitio])
    cfg['carpetas'] = carpetas
    s = Sitio(sitio, cfg)
    for modo in cfg.get('recortar', []):
        recortar(s, modo)
    if shift != (0, 0):
        for p in s.parts:
            p.offset = p.offset + np.array([shift[0], 0, shift[1]])
    return s


def _muestrear(Y, dx, m, mask=None):
    """Valores del terreno (malla dx) bajo las columnas de la huella."""
    n = Y.shape[0]
    f = m['foot'] if mask is None else mask
    zz, xx = np.nonzero(f)
    ci = np.clip(((zz + m['z0']) / dx).astype(int), 0, n - 1)
    cj = np.clip(((xx + m['x0']) / dx).astype(int), 0, n - 1)
    return Y[ci, cj]


def _objetivo(m, borde=8):
    """(suelo, asiento) por columna de la huella.
    suelo: techo del terreno del schematic; donde no hay terreno (columnas de edificios), una
    membrana armónica sin pasar de la base de la columna.  Sirve para el dy y para la costura
    del borde.
    asiento: igual que suelo en una franja de 'borde' bloques junto al contorno (la costura con
    el terreno natural); hacia dentro el terreno queda bajo la base de cada columna, porque el
    schematic trae su propio suelo (losas, terrazas, rellenos) y lo pone al pegarse."""
    from .asiento import _rellenar_huecos
    foot = m['foot']
    g = m['ground'].astype(np.float64)
    ok = foot & (g > -900)
    if not ok.any():
        t = np.where(foot, m['bottom'] - 1.0, np.nan)
        return t, t
    t = np.where(ok, g, np.nan)
    hueco = foot & ~ok
    if hueco.any():
        arm = _rellenar_huecos(t, ok, hueco)
        bajo = (m['bottom'][hueco] - 1.0).astype(np.float64)
        t[hueco] = np.minimum(arm, bajo)
    a = t.copy()
    dentro = ndi.binary_erosion(foot, iterations=borde)
    a[dentro] = np.minimum(t[dentro], m['bottom'][dentro] - 1.0)
    return t, a


def _dif_borde(Y, dx, m, ref, ancho=8):
    """Terreno menos suelo del schematic en la franja del borde de la huella (la costura): el
    dy se elige para que la costura case, aunque dentro haya terrazas o plataformas."""
    f = m['foot']
    borde = f & ~ndi.binary_erosion(f, iterations=ancho) & np.isfinite(ref)
    if not borde.any():
        borde = f & np.isfinite(ref)
    terr = _muestrear(Y, dx, m, borde)
    return terr - ref[borde]


def colocar(Y, dx, rio_y=None, dist_costa=None, analisis=None, log=True, busqueda=None):
    """Y: cotas absolutas (malla dx; para el asiento final, dx = 1).  rio_y: función (x, z) ->
    cota del agua del río cercano.  busqueda: (Yc, dxc, dist_costa_c) malla gruesa para buscar
    la cima de la torre (por defecto la misma Y).
    Devuelve (lista de dicts con la colocación de cada construcción, terreno asentado)."""
    from . import asiento
    out = []
    Ymod = Y.copy()
    Yb, dxb, dcb = busqueda if busqueda is not None else (Y, dx, dist_costa)
    # ---------------------------------------------- traslaciones XZ (solo la torre busca su cima)
    shifts = {}
    tx, tz = poi_blocks('torre_llama_eterna')
    cx, cz, cy = buscar_cima(Yb, dxb, tx, tz, radio=700.0, dist_costa=dcb, max_costa=650.0)
    t0 = _sitio('torre_llama_eterna', ['torre_llama_eterna']).maps()
    torre_c = np.unravel_index(np.argmax(np.where(t0['foot'], t0['top'], -999)), t0['top'].shape)
    shifts['Torre de la llama eterna'] = (int(round(cx - (t0['x0'] + torre_c[1]))),
                                         int(round(cz - (t0['z0'] + torre_c[0]))))
    # ---------------------------------------------- dy y asiento
    grupos = {}
    for nombre, sitio, carpetas, grupo, modo in CONSTRUCCIONES:
        s = _sitio(sitio, carpetas, shifts.get(nombre, (0, 0)))
        m = s.maps()
        out.append({'nombre': nombre, 'sitio': s, 'maps': m, 'grupo': grupo, 'modo': modo,
                    'shift': shifts.get(nombre, (0, 0))})
    for o in out:
        m = o['maps']
        terr = _muestrear(Ymod, dx, m)
        if o['modo'] == 'base':
            suelo = int(m['bottom'][m['foot']].min()) - 1
            ref = np.where(m['foot'], float(suelo), np.nan)
            o['ref_asiento'] = ref
        else:
            ref, o['ref_asiento'] = _objetivo(m)
        o['ref'] = ref
        o['terreno'] = terr
        if o['nombre'] == 'Vieja Velkia' and rio_y is not None:
            zz, xx = np.nonzero(m['water'])
            wy = rio_y(m['x0'] + xx.mean(), m['z0'] + zz.mean())
            o['dy'] = int(round(wy - int(m['water_y'][m['water']].max())))
        else:
            o['dy'] = int(round(np.median(_dif_borde(Ymod, dx, m, ref))))
    # grupo complejo: un solo dy (el de la costura de todas sus piezas)
    comp = [o for o in out if o['grupo'] == 'complejo']
    if comp:
        allv = np.concatenate([_dif_borde(Ymod, dx, o['maps'], o['ref']) for o in comp])
        dyc = int(round(np.median(allv)))
        for o in comp:
            o['dy'] = dyc
    # asiento por unidades: el complejo (piezas que encajan entre sí) va como UNA huella, para
    # que el talud de una pieza no rehaga el suelo de otra ya asentada
    unidades = []
    for o in out:
        if o['grupo'] and any(u['grupo'] == o['grupo'] for u in unidades):
            next(u for u in unidades if u['grupo'] == o['grupo'])['piezas'].append(o)
        else:
            unidades.append({'grupo': o['grupo'], 'piezas': [o]})
    for u in unidades:
        foot, x0, z0, target, target_a = _union(u['piezas'])
        nombre = u['piezas'][0]['nombre'] if len(u['piezas']) == 1 else 'complejo'
        if nombre == 'Vieja Velkia':
            # vega: huella ensanchada 80 bloques a la cota del suelo de la ciudad (solo corte)
            pad = 80
            fp = np.pad(foot, pad)
            vega = ndi.distance_transform_edt(~fp) <= pad
            tv = np.where(vega, np.nanmedian(target[foot]), np.nan)
            tv = np.where(fp, np.pad(target, pad, constant_values=np.nan), tv)
            Ycut, _ = asiento.asentar(Ymod, dx, vega, x0 - pad, z0 - pad, tv, slope_cut=1.8, slope_fill=0.0)
            Ymod = np.minimum(Ymod, Ycut)
        for o in u['piezas']:
            m = o['maps']
            o['antes'] = asiento.evaluar_asiento(Ymod, dx, m['foot'], m['x0'], m['z0'], o['ref'] + o['dy'])
        Ymod, inf = asiento.asentar(Ymod, dx, foot, x0, z0, target_a, slope_fill=TALUD,
                                    slope_cut=TALUD, border_min=max(6.0, 2.0 * dx), target_borde=target)
        for o in u['piezas']:
            o['informe'] = inf
        if log:
            print(f"  {nombre}: dy {u['piezas'][0]['dy']:+d}  corte máx {inf.get('corte_max', 0):.0f}  "
                  f"relleno máx {inf.get('relleno_max', 0):.0f}", flush=True)
    # evaluación final, con todo ya asentado: flotación/enterramiento en el borde y talud del anillo
    todas = np.zeros(Ymod.shape, bool) if dx == 1 else None
    if todas is not None:
        for o in out:
            m = o['maps']
            zz, xx = np.nonzero(m['foot'])
            todas[zz + m['z0'], xx + m['x0']] = True
    for o in out:
        m = o['maps']
        o['despues'] = asiento.evaluar_asiento(Ymod, dx, m['foot'], m['x0'], m['z0'], o['ref'] + o['dy'])
        if todas is not None:
            o['talud'] = talud_anillo(Ymod, m['foot'], m['x0'], m['z0'], todas)
    return out, Ymod


def _union(piezas):
    """Huella, esquina y objetivos (suelo, asiento) de una o varias piezas en una sola caja."""
    if len(piezas) == 1:
        o = piezas[0]
        m = o['maps']
        return m['foot'].copy(), m['x0'], m['z0'], o['ref'] + o['dy'], o['ref_asiento'] + o['dy']
    x0 = min(o['maps']['x0'] for o in piezas)
    z0 = min(o['maps']['z0'] for o in piezas)
    x1 = max(o['maps']['x0'] + o['maps']['foot'].shape[1] for o in piezas)
    z1 = max(o['maps']['z0'] + o['maps']['foot'].shape[0] for o in piezas)
    foot = np.zeros((z1 - z0, x1 - x0), bool)
    t = np.full(foot.shape, np.nan)
    ta = np.full(foot.shape, np.nan)
    for o in piezas:
        m = o['maps']
        sl = (slice(m['z0'] - z0, m['z0'] - z0 + m['foot'].shape[0]), slice(m['x0'] - x0, m['x0'] - x0 + m['foot'].shape[1]))
        f = m['foot']
        foot[sl] |= f
        v = np.where(f, o['ref'] + o['dy'], np.nan)
        va = np.where(f, o['ref_asiento'] + o['dy'], np.nan)
        t[sl] = np.where(np.isnan(t[sl]), v, np.where(np.isnan(v), t[sl], np.maximum(t[sl], v)))
        ta[sl] = np.where(np.isnan(ta[sl]), va, np.where(np.isnan(va), ta[sl], np.minimum(ta[sl], va)))
    return foot, x0, z0, t, ta


def talud_anillo(Y, foot, x0, z0, excluir, ancho=60):
    """Pendiente del terreno (bloques/bloque) en un anillo de 'ancho' bloques alrededor de la
    huella, sin contar otras huellas.  Devuelve (p95, p99, máx)."""
    pad = ancho + 2
    L, W = foot.shape
    a0, b0 = z0 - pad, x0 - pad
    a1, b1 = a0 + L + 2 * pad, b0 + W + 2 * pad
    if a0 < 1 or b0 < 1 or a1 >= Y.shape[0] - 1 or b1 >= Y.shape[1] - 1:
        return (0.0, 0.0, 0.0)
    fp = np.zeros((L + 2 * pad, W + 2 * pad), bool)
    fp[pad:pad + L, pad:pad + W] = foot
    dist = ndi.distance_transform_edt(~fp)
    win = np.asarray(Y[a0 - 1:a1 + 1, b0 - 1:b1 + 1], np.float64)
    gz, gx = np.gradient(win)
    G = np.hypot(gz, gx)[1:-1, 1:-1]
    otras = ndi.binary_dilation(excluir[a0:a1, b0:b1] & ~fp, iterations=2)
    anillo = (dist >= 1) & (dist <= ancho) & ~otras
    g = G[anillo]
    if g.size == 0:
        return (0.0, 0.0, 0.0)
    return (float(np.percentile(g, 95)), float(np.percentile(g, 99)), float(g.max()))
