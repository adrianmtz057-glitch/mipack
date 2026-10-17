"""Modelado final de la v2: igual que velkia.modelado.modelar pero
  * Jardines con fondo en relieve, sin cadena de lagos y domo más bajo (jardines_v2);
  * sin el promontorio de los Fuertes (el sitio se elimina: queda el terreno natural);
  * volcán sin cono interior ni coladas: la caldera se llena de lava y las bocas con sus caídas
    las pone relieve_v2 (a 1 bloque).
"""
import time

import numpy as np

from . import jardines_v2
from . import modelado as M
from .layout import RESERVADOS, SEA, px2b
from .volcan import rejuvenecer


def sitios_reservados_v2(h, b, dx):
    """Solo Crakatos (repisa para la ciudad); los Fuertes se eliminan."""
    L, W = h.shape
    info = {}
    for nombre, (pxy, rad, tipo) in RESERVADOS.items():
        if tipo != 'meseta':
            continue
        bx, bz = px2b(*pxy)
        Z, X = np.meshgrid((np.arange(L) + 0.5) * dx - bz, (np.arange(W) + 0.5) * dx - bx, indexing='ij')
        r = np.hypot(X, Z) / rad
        disco = r < 1.0
        nivel = float(np.percentile(h[disco], 55))
        w = 1.0 - M._sstep((r - 0.8) / 0.7)
        h2 = h + (nivel - h) * w
        b = np.where(h2 < h, np.minimum(b, h2), np.maximum(b, h2 - 1.0))
        h = h2
        info[nombre] = {'cima': nivel + SEA}
    return h, b, info


def modelar_v2(h, b, prov, lay, chain, rio_xy, volcan_c, seed=31, log=True):
    dx = lay.dx
    info = {}
    t0 = time.time()
    h, b, k_src = M.fuente_natural(h, b, chain)
    info['k_fuente'] = k_src
    h, b, lagos, ij = jardines_v2.excavar(h, b, lay, chain)
    info['jardines'] = ij
    if log:
        print(f"  Jardines v2: fondo {ij['piso'] + SEA:.0f}, domo en {ij['domo'][:2]}", flush=True)
    h, b, iv = rejuvenecer(h, b, dx, volcan_c, coladas=[], n_coladas=0, cono_interior=False, log=log)
    info['volcan'] = iv
    grupos = M.elegir_relieves(lay, rio_xy)
    h, b, prov = M.aplicar_relieves(h, b, prov, dx, grupos)
    info['relieves'] = grupos
    h, b = M.depresion_bashi(h, b, dx)
    h, b, info['reservados'] = sitios_reservados_v2(h, b, dx)
    h, b, ia = M.ladera_aldea_oeste(h, b, dx)
    info['aldea_oeste'] = ia
    info['lagos_jardines'] = lagos
    if log:
        print(f'  modelado v2 en {time.time() - t0:.0f} s', flush=True)
    return h, b, prov, info


def modelar_desde_v2(p4, salida, log=True):
    """Como velkia.modelado.modelar_desde pero con modelar_v2."""
    import json
    from . import lem
    from .geology import Geology
    from .layout import Layout
    from .tectonica import Forcing
    d = dict(np.load(p4, allow_pickle=False))
    n = d['h'].shape[0]
    lay = Layout(n)
    geo = Geology(lay)
    fo = Forcing(lay, geo)
    h, b, prov, info = modelar_v2(d['h'], d['b'], d['prov'], lay, d['chain'], d['rio_xy'], d['volcan'], log=log)
    kf = {}
    for k in sorted([k for k in d if k.startswith('cad_')], key=lambda s: int(s[4:]))[2:]:
        h, b, kf[k] = M.fuente_natural(h, b, d[k])
    h = np.ascontiguousarray(h, np.float64)
    b = np.ascontiguousarray(b, np.float64)
    for k in sorted([k for k in d if k.startswith('cad_')], key=lambda s: int(s[4:])):
        lem.breach_chain(h, b, np.ascontiguousarray(d[k]), 2e-4, lay.dx)
    rec, stack, filled = lem.route_flow(h, h < 0, 1e-4, d['fixed_rec'])
    stack = lem.fix_stack(rec, n * n)
    Q = lem.accumulate(stack, rec, (fo.precip(h) * lay.dx * lay.dx).ravel()).reshape(n, n)
    ij, iv = info['jardines'], info['volcan']
    casc = np.array([[c['x'], c['z'], c['y_borde'], c['y_pie'], c['dir'][0], c['dir'][1]]
                     for c in ij['cascadas']]).reshape(-1, 6)
    lava_xy = np.concatenate([np.r_[c, [[np.nan, np.nan]]] for c in iv['caminos']]) if iv['caminos'] else np.zeros((0, 2))
    d.update(h=h, b=b, prov=prov, Q=Q, filled=filled, lagos_jardines=info['lagos_jardines'],
             cascadas=casc, jardines_domo=np.array(ij['domo']), jardines_piso=np.array(ij['piso']),
             jardines_pared=ij['pared'], lava_canal=iv['lava_canal'], lago_lava=iv['lago_lava'],
             lava_xy=lava_xy, caldera=np.array(iv['caldera']),
             relieves_json=np.array(json.dumps(info['relieves'])), k_fuente=np.array(info['k_fuente']),
             **{'kf_' + k: np.array(v) for k, v in kf.items()},
             aldea_oeste_json=np.array(json.dumps(info['aldea_oeste'])))
    np.savez_compressed(salida, **d)
    if log:
        print(f'  guardado {salida}', flush=True)
    return d


if __name__ == '__main__':
    modelar_desde_v2('salida/etapa1_p4.npz', 'salida/etapa1_v2.npz')
