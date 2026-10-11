"""Colocación de las construcciones sobre un terreno dado y asiento (corte y relleno).

Devuelve, por construcción, la traslación final (dx, dz, dy) respecto de la ubicación del
mapa 2 y el terreno modificado.  Reglas:
  * Complejo Pirámide-Esfinge-Thza: un solo dy (las piezas encajan entre sí).
  * Jardines colgantes: en el domo central de los Jardines.
  * Vieja Velkia: el canal (agua a Y=87) a la cota del río; el fondo del cañón se ensancha
    en una vega (solo corte) para que la roca no entierre la ciudad.
  * Aldea oeste (terrazas): ladera con pendiente y orientación de diseño cerca de su punto.
  * Aldea sur: en su punto, junto al Río Salado.
  * Torre: cima/promontorio cercano a la costa.
"""
import numpy as np
from scipy import ndimage as ndi

from .estructuras import SITIOS, Sitio
from .layout import N, SEA, poi_blocks
from .ubicacion import buscar_cima, buscar_ladera

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


def colocar(Y, dx, rio_y=None, dist_costa=None, analisis=None, log=True):
    """Y: cotas absolutas (malla dx).  rio_y: función (x, z) -> cota del agua del río cercano.
    analisis: dict opcional con pendiente/aspecto de diseño de la aldea oeste, etc.
    Devuelve lista de dicts con la colocación de cada construcción."""
    from . import asiento
    analisis = analisis or {}
    out = []
    Ymod = Y.copy()
    # ---------------------------------------------- traslaciones XZ
    shifts = {}
    tx, tz = poi_blocks('torre_llama_eterna')
    cx, cz, cy = buscar_cima(Y, dx, tx, tz, radio=700.0, dist_costa=dist_costa, max_costa=650.0)
    t0 = _sitio('torre_llama_eterna', ['torre_llama_eterna']).maps()
    torre_c = np.unravel_index(np.argmax(np.where(t0['foot'], t0['top'], -999)), t0['top'].shape)
    shifts['Torre de la llama eterna'] = (int(round(cx - (t0['x0'] + torre_c[1]))),
                                         int(round(cz - (t0['z0'] + torre_c[0]))))
    ax, az = poi_blocks('aldea_fantasma_oeste')
    a0 = _sitio('aldea_fantasma_oeste', ['aldea_fantasma_norte']).maps()
    # diseño original: terrazas suaves, 0,051 bloques/bloque (2,9°) bajando hacia 25,7° (ESE)
    pend = analisis.get('aldea_oeste_pendiente', 0.051)
    asp = analisis.get('aldea_oeste_aspecto', 25.7)
    lx, lz, info = buscar_ladera(Y, dx, ax, az, 800.0, pend, asp, 250.0)
    zz, xx = np.nonzero(a0['foot'])
    shifts['Aldea fantasma oeste'] = (int(round(lx - (a0['x0'] + xx.mean()))), int(round(lz - (a0['z0'] + zz.mean()))))
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
            ref = np.full(m['foot'].shape, float(suelo))
        else:
            g = m['ground'].astype(float)
            g[(g < -900) | ~m['foot']] = np.nan
            if np.isnan(g).all():
                g = np.where(m['foot'], m['bottom'] - 1.0, np.nan)
            ref = g
        o['ref'] = ref
        o['terreno'] = terr
        if o['nombre'] == 'Vieja Velkia' and rio_y is not None:
            zz, xx = np.nonzero(m['water'])
            wy = rio_y(m['x0'] + xx.mean(), m['z0'] + zz.mean())
            o['dy'] = int(round(wy - int(m['water_y'][m['water']].max())))
        else:
            o['dy'] = int(round(np.median(terr) - np.nanmedian(ref[m['foot']])))
    # grupo complejo: un solo dy (mediana ponderada por área)
    comp = [o for o in out if o['grupo'] == 'complejo']
    if comp:
        allv = np.concatenate([o['terreno'] - np.nanmedian(o['ref'][o['maps']['foot']]) for o in comp])
        dyc = int(round(np.median(allv)))
        for o in comp:
            o['dy'] = dyc
    # asiento: Vieja Velkia primero con vega (solo corte), luego el resto
    for o in out:
        m = o['maps']
        target = o['ref'] + o['dy']
        x0, z0 = m['x0'], m['z0']
        foot = m['foot'].copy()
        if o['nombre'] == 'Vieja Velkia':
            # vega: huella ensanchada 80 bloques a la cota del suelo de la ciudad (solo corte)
            vega = ndi.binary_dilation(foot, iterations=80)
            tv = np.where(vega, np.nanmedian(target[foot]), np.nan)
            tv = np.where(foot, target, tv)
            Ycut, _ = asiento.asentar(Ymod, dx, vega, x0, z0, tv, slope_cut=1.8, slope_fill=0.0)
            Ymod = np.minimum(Ymod, Ycut)
            foot_use, target_use = foot, target
        else:
            foot_use, target_use = foot, target
        antes = asiento.evaluar_asiento(Ymod, dx, foot_use, x0, z0, target_use)
        Ymod, inf = asiento.asentar(Ymod, dx, foot_use, x0, z0, target_use)
        o['informe'] = inf
        o['antes'] = antes
        o['despues'] = asiento.evaluar_asiento(Ymod, dx, foot_use, x0, z0, target_use)
        if log:
            print(f"  {o['nombre']}: desplazamiento {o['shift']}  dy {o['dy']:+d}  "
                  f"corte máx {inf.get('corte_max', 0):.0f}  relleno máx {inf.get('relleno_max', 0):.0f}", flush=True)
    return out, Ymod
