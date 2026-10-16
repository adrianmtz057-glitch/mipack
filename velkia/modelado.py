"""Modelado final de la etapa 1: formas que la erosión a 8 bloques/celda no resuelve.

Se aplica sobre el estado tras el Holoceno (salida/etapa1_p4.npz) y escribe salida/etapa1.npz.
Así se puede iterar sin repetir la historia erosiva (python3 -m velkia.modelado).

  * Jardines: valle en U tipo Yosemite (jardines.py).
  * Volcán joven: cono de flancos empinados, caldera, barrancos radiales, coladas post-glaciares
    y el río de lava del mapa 2 con sus ramales (volcan.rejuvenecer).
  * Mesas y buttes (cornisa dura horizontal: cima plana, escarpe y talud) y domos graníticos,
    pocos y agrupados.  Todos los de un grupo tienen la cima a la misma cota: son restos de la
    misma capa dura.
  * Cuarto de Bashi: dolina de colapso romboidal (disolución de evaporitas bajo la cornisa),
    posterior al relleno sedimentario, para que no quede tapada.
  * Aldea oeste: ladera de ~3° con la orientación del diseño (bajando hacia 25,7° del E al S)
    en su punto del mapa 2; se prepara el terreno para la aldea, la aldea no se mueve.

Las formas son funciones analíticas de las coordenadas en bloques, con sus parámetros guardados
(relieves_json): en la etapa 4 se vuelven a evaluar a resolución de bloque.
"""
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage as ndi

from . import jardines, lem
from .layout import Layout, RESERVADOS, px2b, poi_blocks, SEA
from .volcan import rejuvenecer, _trazar, _colada

# puntos de la referencia (mapa 2) del río de lava
LAVA_NO = px2b(140, 838)          # extremo noroeste del río de lava
LAVA_SE = px2b(372, 1135)         # llega a la costa sureste de la región volcánica

ALDEA_OESTE_PEND = 0.051          # 2,9°
ALDEA_OESTE_ASPECTO = 25.7        # bajada hacia 25,7° desde el este hacia el sur (ESE)


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ===================================================================== mesas, buttes y domos
EVITAR = [('gran_piramide', 600.0), ('esfinge', 550.0), ('thza', 600.0), ('aldea_fantasma_sur', 500.0),
          ('aldea_fantasma_oeste', 450.0), ('jardines_de_velkia', 1300.0), ('torre_llama_eterna', 500.0),
          ('gran_canon_vieja_velkia', 800.0), ('bioma_de_sales', 500.0)]


def elegir_relieves(lay, rio_xy, seed=23, n_mesas=3, n_domos=1):
    """Grupos de mesas/buttes y de domos en el desierto, lejos de construcciones, sitios
    reservados, el río y la costa."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    n, dx = lay.n, lay.dx
    z = lay.zonas
    evitar = [(np.array(poi_blocks(k)), r) for k, r in EVITAR]
    evitar += [(np.array(px2b(*v[0])), v[1] + 200.0) for v in RESERVADOS.values()]
    rio = cKDTree(np.asarray(rio_xy, float))

    def valor(campo, x, y):
        i, j = int(np.clip(y / dx, 0, n - 1)), int(np.clip(x / dx, 0, n - 1))
        return campo[i, j]

    def libre(x, y, r, zona_min=0.7, zonas=('desierto',), costa=450.0):
        if not (0 < x < n * dx and 0 < y < n * dx):
            return False
        if sum(valor(z[k], x, y) for k in zonas) < zona_min:
            return False
        if valor(lay.dist_coast, x, y) < costa + r:
            return False
        if rio.query([x, y])[0] < 260.0 + 1.3 * r:
            return False
        return all(np.hypot(x - p[0], y - p[1]) > rr + 1.3 * r for p, rr in evitar)

    def armonicos(f=1.0):
        return [(k, f * rng.uniform(0.03, 0.10) * (5.0 / max(k, 5)), rng.uniform(0, 2 * np.pi))
                for k in (3, 4, 5, 7, 9, 12)]

    grupos = []
    centros = []
    for tipo, cuantos in (('domo', n_domos), ('mesa', n_mesas)):
        zonas = ('desierto', 'oeste')
        intentos = 0
        hechos = 0
        while hechos < cuantos and intentos < 4000:
            intentos += 1
            x, y = rng.uniform(0, n * dx, 2)
            if not libre(x, y, 150.0, zona_min=0.65, zonas=zonas, costa=350.0):
                continue
            if any(np.hypot(x - c[0], y - c[1]) < 1100.0 for c in centros):
                continue
            centros.append((x, y))
            hechos += 1
            miembros = []
            fi = rng.uniform(0, np.pi)
            if tipo == 'mesa':
                R = rng.uniform(110.0, 180.0)
                miembros.append({'tipo': 'mesa', 'x': x, 'z': y, 'R': R, 'elong': rng.uniform(1.2, 1.8),
                                 'phi': fi, 'arm': armonicos()})
                dir_retro = rng.uniform(0, 2 * np.pi)          # hacia donde retrocedió la cornisa
                for _ in range(int(rng.integers(3, 6)) * 4):
                    if len(miembros) >= 1 + 5:
                        break
                    a = dir_retro + rng.uniform(-1.0, 1.0)
                    dd = rng.uniform(R + 140.0, R + 600.0)
                    bx, bz = x + dd * np.cos(a), y + dd * np.sin(a)
                    r = rng.uniform(25.0, 60.0)
                    if not libre(bx, bz, r, zona_min=0.5, zonas=zonas, costa=350.0):
                        continue
                    if any(np.hypot(bx - m['x'], bz - m['z']) < m['R'] * m['elong'] + r + 70.0 for m in miembros):
                        continue
                    miembros.append({'tipo': 'butte', 'x': bx, 'z': bz, 'R': r, 'elong': rng.uniform(1.0, 1.4),
                                     'phi': rng.uniform(0, np.pi), 'arm': armonicos()})
                if len(miembros) < 3:                       # un grupo necesita varios restos
                    centros.pop()
                    hechos -= 1
                    continue
                grupos.append({'tipo': 'mesa', 'x': x, 'z': y, 'cima_rel': rng.uniform(42.0, 66.0),
                               'miembros': miembros})
            else:
                for _ in range(24):
                    if len(miembros) >= int(rng.integers(3, 5)):
                        break
                    a = rng.uniform(0, 2 * np.pi)
                    dd = 0.0 if not miembros else rng.uniform(170.0, 520.0)
                    bx, bz = x + dd * np.cos(a), y + dd * np.sin(a)
                    r = rng.uniform(70.0, 150.0)
                    if not libre(bx, bz, r, zona_min=0.5, zonas=zonas, costa=350.0):
                        continue
                    if any(np.hypot(bx - m['x'], bz - m['z']) < m['R'] + r + 20.0 for m in miembros):
                        continue
                    miembros.append({'tipo': 'domo', 'x': bx, 'z': bz, 'R': r, 'elong': rng.uniform(1.0, 1.35),
                                     'phi': rng.uniform(0, np.pi), 'arm': armonicos(0.35),
                                     'H': r * rng.uniform(0.45, 0.65)})
                grupos.append({'tipo': 'domo', 'x': x, 'z': y, 'miembros': miembros})
    return grupos


def _rho(X, Z, m):
    """Distancia normalizada al contorno irregular del relieve (1 = contorno)."""
    c, s = np.cos(m['phi']), np.sin(m['phi'])
    u = (X * c + Z * s) / m['elong']
    v = -X * s + Z * c
    th = np.arctan2(Z, X)
    f = 1.0 + sum(a * np.cos(k * th + fa) for k, a, fa in m['arm'])
    return np.hypot(u, v) / (m['R'] * f), m['R'] * f


def perfil_relieve(X, Z, m, base, cima=None):
    """Cota del relieve m (cotas relativas al mar) en coordenadas locales X, Z (bloques)."""
    rho, Rf = _rho(X, Z, m)
    if m['tipo'] == 'domo':
        H = m['H']
        p = base + H * np.clip(1.0 - rho ** 2, 0, 1) ** 0.6
        falda = base + 0.06 * H * np.clip(1.0 - (rho - 1.0) / 0.35, 0, 1) ** 2
        return np.where(rho < 1.0, p, np.where(rho < 1.35, falda, -1e9))
    # mesa / butte: cima plana a la cota de la capa dura, escarpe casi vertical, talud
    alto = cima - base
    c = float(np.clip(0.55 * alto, 8.0, 38.0))       # escarpe de la cornisa (más de la mitad)
    wc = max(c / 3.5, 2.0)
    ht = max(alto - c, 0.0)
    Lt = max(2.4 * ht, 1.0)                          # talud: pendiente inicial 0,75 (37°)
    dout = (rho - 1.0) * Rf
    u = np.clip((dout - wc) / Lt, 0, 1)
    p = np.where(dout <= 0, cima,
                 np.where(dout <= wc, cima - c * _sstep(dout / wc), base + ht * (1.0 - u) ** 1.8))
    return np.where(dout <= wc + Lt, p, -1e9)


def aplicar_relieves(h, b, prov, dx, grupos, x0=0.0, z0=0.0, calcular_base=True):
    """Aplica los grupos sobre h (malla de dx bloques con esquina en x0, z0).  Guarda en cada
    miembro su 'base' (cota del llano alrededor) y en cada grupo de mesas su 'cima'."""
    from .geology import GRANITO, ESTRATOS
    h = h.copy()
    b = b.copy()
    prov = prov.copy() if prov is not None else None
    L, W = h.shape
    for g in grupos:
        if g['tipo'] == 'mesa' and calcular_base:
            ci, cj = int((g['z'] - z0) / dx), int((g['x'] - x0) / dx)
            r = int(900.0 / dx)
            win = h[max(ci - r, 0):ci + r, max(cj - r, 0):cj + r]
            g['cima'] = float(np.median(win[win > 0])) + g['cima_rel'] if (win > 0).any() else g['cima_rel']
        for m in g['miembros']:
            alcance = m['R'] * m['elong'] * 1.25 + (300.0 if g['tipo'] == 'mesa' else 60.0)
            i0, i1 = int(max((m['z'] - alcance - z0) / dx, 0)), int(min((m['z'] + alcance - z0) / dx + 1, L))
            j0, j1 = int(max((m['x'] - alcance - x0) / dx, 0)), int(min((m['x'] + alcance - x0) / dx + 1, W))
            if i1 <= i0 or j1 <= j0:
                continue
            Zc = (np.arange(i0, i1) + 0.5) * dx + z0 - m['z']
            Xc = (np.arange(j0, j1) + 0.5) * dx + x0 - m['x']
            Zg, Xg = np.meshgrid(Zc, Xc, indexing='ij')
            sub = h[i0:i1, j0:j1]
            if calcular_base:
                rr = np.hypot(Xg, Zg)
                an = (rr > 1.3 * m['R'] * m['elong']) & (rr < 2.5 * m['R'] * m['elong'])
                m['base'] = float(np.median(sub[an])) if an.any() else float(np.median(sub))
            if g['tipo'] == 'mesa':
                cima = max(g['cima'], m['base'] + 18.0)
                m['cima'] = cima
                p = perfil_relieve(Xg, Zg, m, m['base'], cima)
            else:
                p = perfil_relieve(Xg, Zg, m, m['base'])
            nuevo = np.maximum(sub, p)
            sube = nuevo > sub + 0.25
            h[i0:i1, j0:j1] = nuevo
            b[i0:i1, j0:j1] = np.where(sube, nuevo - 0.3, b[i0:i1, j0:j1])
            if prov is not None:
                prov[i0:i1, j0:j1][sube] = GRANITO if g['tipo'] == 'domo' else ESTRATOS
    return h, b, prov


# ===================================================================== Cuarto de Bashi
def depresion_bashi(h, b, dx, prof=32.0, x0=0.0, z0=0.0):
    """Dolina de colapso romboidal (~340×360 bloques), fondo plano y paredes de ~33°."""
    (bpx, rad, _) = RESERVADOS['cuarto_de_bashi']
    bx, bz = px2b(*bpx)
    L, W = h.shape
    Z, X = np.meshgrid((np.arange(L) + 0.5) * dx + z0 - bz, (np.arange(W) + 0.5) * dx + x0 - bx, indexing='ij')
    rombo = (np.abs(X) ** 1.3 + np.abs(Z) ** 1.3) ** (1 / 1.3) / rad
    anillo = (rombo > 1.05) & (rombo < 1.5)
    if not anillo.any():
        return h, b
    base = float(np.median(h[anillo]))
    prof = min(prof, base - 4.0)              # fondo seco, por encima del mar
    fondo = base - prof
    p = fondo + prof * _sstep((rombo - 0.60) / 0.40)
    h2 = np.where(rombo < 1.0, np.minimum(h, p), h)
    return h2, np.minimum(b, h2)


# ===================================================================== sitios reservados
def sitios_reservados(h, b, dx, x0=0.0, z0=0.0):
    """Fuertes en ruinas: promontorio costero de cima amplia y suave (para las ruinas).
    Crakatos: repisa amplia en lo alto de las Tierras Corrompidas (para la ciudad)."""
    L, W = h.shape
    info = {}
    for nombre, (pxy, rad, tipo) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        Z, X = np.meshgrid((np.arange(L) + 0.5) * dx + z0 - bz, (np.arange(W) + 0.5) * dx + x0 - bx, indexing='ij')
        r = np.hypot(X, Z) / rad
        if tipo == 'promontorio':
            anillo = (r > 1.6) & (r < 2.4) & (h > 0)
            base = float(np.median(h[anillo])) if anillo.any() else float(np.median(h[r < 1]))
            alto = 48.0
            cima = base + alto
            # cima casi plana (r < 0,55), laderas de ~25-30° hasta r = 1,6
            p = base + alto * _sstep((1.6 - r) / 1.05)
            h2 = np.where(r < 1.6, np.maximum(h, p), h)
            b = np.where(h2 > h, np.maximum(b, h2 - 1.0), b)
            h = h2
            info[nombre] = {'cima': cima + SEA}
        elif tipo == 'meseta':
            disco = r < 1.0
            nivel = float(np.percentile(h[disco], 55))
            w = 1.0 - _sstep((r - 0.8) / 0.7)
            h2 = h + (nivel - h) * w
            b = np.where(h2 < h, np.minimum(b, h2), np.maximum(b, h2 - 1.0))
            h = h2
            info[nombre] = {'cima': nivel + SEA}
    return h, b, info


# ===================================================================== aldea oeste
def ladera_aldea_oeste(h, b, dx, pend=ALDEA_OESTE_PEND, aspecto=ALDEA_OESTE_ASPECTO, x0=0.0, z0=0.0,
                       transicion=240.0):
    """Ladera plana inclinada (~3°, bajando hacia 'aspecto' grados del E al S) bajo la huella de
    la aldea oeste en su punto del mapa 2, enlazada con suavidad con el terreno."""
    from .colocar import _sitio
    m = _sitio('aldea_fantasma_oeste', ['aldea_fantasma_norte']).maps()
    zz, xx = np.nonzero(m['foot'])
    cx, cz = m['x0'] + xx.mean(), m['z0'] + zz.mean()
    rf = float(np.percentile(np.hypot(m['x0'] + xx - cx, m['z0'] + zz - cz), 99)) + 20.0
    L, W = h.shape
    Z, X = np.meshgrid((np.arange(L) + 0.5) * dx + z0 - cz, (np.arange(W) + 0.5) * dx + x0 - cx, indexing='ij')
    r = np.hypot(X, Z)
    a = np.deg2rad(aspecto)
    disco = r < rf
    y0 = float(np.median(h[disco]))
    plano = y0 - pend * (X * np.cos(a) + Z * np.sin(a))
    w = 1.0 - _sstep((r - rf) / transicion)
    h2 = h + (plano - h) * w
    b2 = np.where(w > 0, np.minimum(b, h2 - 1.0 * (h2 < h)), b)
    b2 = np.where(h2 > h, np.maximum(b2, h2 - 2.0), b2)
    return h2, b2, {'x': cx, 'z': cz, 'r': rf, 'y0': y0, 'pend': pend, 'aspecto': aspecto}


# ===================================================================== fuente del río
def fuente_natural(h, b, chain, n_ok=10, tol=5.0):
    """La cabecera del cauce forzado recibe muy poco caudal y queda como una cresta (el río
    correría por encima de sus laderas).  La fuente se pone en la primera celda desde la que
    el cauce va por un valle (no más alto que sus vecinas fuera del cauce) y las celdas de
    antes vuelven al relieve natural (mediana de sus vecinas).  Devuelve (h, b, k_fuente)."""
    n = h.shape[0]
    en = np.zeros(n * n, bool)
    en[chain] = True
    exceso = np.zeros(chain.size)
    vec = []
    for k, c in enumerate(chain[:400]):
        i, j = divmod(int(c), n)
        v = [h[i + a, j + bb] for a in (-1, 0, 1) for bb in (-1, 0, 1)
             if (a or bb) and 0 <= i + a < n and 0 <= j + bb < n and not en[(i + a) * n + j + bb]]
        vec.append(v)
        exceso[k] = h[i, j] - min(v) if v else 0.0
    k_src = 0
    for k in range(min(400, chain.size) - n_ok):
        if np.all(exceso[k:k + n_ok] < tol):
            k_src = k
            break
    h = h.copy()
    b = b.copy()
    for k in range(k_src):
        i, j = divmod(int(chain[k]), n)
        if vec[k]:
            h[i, j] = min(h[i, j], float(np.median(vec[k])))
            b[i, j] = min(b[i, j], h[i, j])
    return h, b, k_src


# ===================================================================== todo junto
def modelar(h, b, prov, lay, chain, rio_xy, volcan_c, seed=31, log=True):
    dx = lay.dx
    info = {}
    t0 = time.time()
    h, b, k_src = fuente_natural(h, b, chain)
    info['k_fuente'] = k_src
    if log:
        print(f'  fuente del río en la celda {k_src} del cauce (Y={h.ravel()[chain[k_src]] + SEA:.0f})', flush=True)
    # Jardines
    h, b, lagos, ij = jardines.excavar(h, b, lay, chain)
    info['jardines'] = ij
    if log:
        print(f"  Jardines: fondo {ij['piso'] + SEA:.0f}, {len(ij['cascadas'])} valles colgados, "
              f"domo en {ij['domo'][:2]}", flush=True)
    # volcán joven y río de lava del mapa 2
    vx, vz = volcan_c
    def salida_hacia(obj):
        a = np.arctan2(obj[1] - vz, obj[0] - vx)
        return (vx + 290.0 * np.cos(a), vz + 290.0 * np.sin(a))
    coladas = [(salida_hacia(LAVA_SE), LAVA_SE, 11.0, 75.0, True),
               (salida_hacia(LAVA_NO), LAVA_NO, 9.0, 60.0, True)]
    h, b, iv = rejuvenecer(h, b, dx, (vx, vz), coladas=coladas, log=log)
    # ramales del río de lava hacia la costa (4 con el principal)
    rng = np.random.default_rng(seed)
    camino = iv['caminos'][0]
    for f in (0.45, 0.62, 0.78):
        k = int(f * (len(camino) - 1))
        ini = camino[k]
        dirv = camino[min(k + 8, len(camino) - 1)] - camino[max(k - 8, 0)]
        a = np.arctan2(dirv[1], dirv[0]) + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
        obj = (ini[0] + 1500.0 * np.cos(a), ini[1] + 1500.0 * np.sin(a))
        pi, pj = _trazar(h, dx, ini, objetivo=obj, sesgo=0.4, rng=rng)
        h, cm = _colada(h, dx, pi, pj, 7.0, 45.0, rng, canal=True)
        iv['lava_canal'] |= cm
        iv['caminos'].append(np.c_[(pj + 0.5) * dx, (pi + 0.5) * dx])
    info['volcan'] = iv
    # mesas, buttes y domos
    grupos = elegir_relieves(lay, rio_xy)
    h, b, prov = aplicar_relieves(h, b, prov, dx, grupos)
    info['relieves'] = grupos
    if log:
        print(f"  relieves: {sum(len(g['miembros']) for g in grupos)} en {len(grupos)} grupos", flush=True)
    # Bashi, sitios reservados y aldea oeste
    h, b = depresion_bashi(h, b, dx)
    h, b, info['reservados'] = sitios_reservados(h, b, dx)
    if log:
        print(f"  reservados: {info['reservados']}", flush=True)
    h, b, ia = ladera_aldea_oeste(h, b, dx)
    info['aldea_oeste'] = ia
    info['lagos_jardines'] = lagos
    if log:
        print(f'  modelado en {time.time() - t0:.0f} s', flush=True)
    return h, b, prov, info


def modelar_desde(p4, salida, lay=None, geo=None, fo=None, log=True):
    d = dict(np.load(p4, allow_pickle=False))
    n = d['h'].shape[0]
    lay = lay or Layout(n)
    if fo is None:
        from .geology import Geology
        from .tectonica import Forcing
        geo = geo or Geology(lay)
        fo = Forcing(lay, geo)
    print('== Modelado final', flush=True)
    h, b, prov, info = modelar(d['h'], d['b'], d['prov'], lay, d['chain'], d['rio_xy'], d['volcan'], log=log)
    # el cauce vuelve a bajar siempre (por si alguna forma lo tapó), fuera de los Jardines
    # afluentes: misma corrección de la cabecera que el río principal
    kf = {}
    for k in sorted([k for k in d if k.startswith('cad_')], key=lambda s: int(s[4:]))[2:]:
        h, b, kf[k] = fuente_natural(h, b, d[k])
        if log:
            print(f'  {k}: fuente en la celda {kf[k]} (Y={h.ravel()[d[k][kf[k]]] + SEA:.0f})', flush=True)
    h = np.ascontiguousarray(h, np.float64)
    b = np.ascontiguousarray(b, np.float64)
    for k in sorted([k for k in d if k.startswith('cad_')], key=lambda s: int(s[4:])):
        lem.breach_chain(h, b, np.ascontiguousarray(d[k]), 2e-4, lay.dx)
    fixed_rec = d['fixed_rec']
    rec, stack, filled = lem.route_flow(h, h < 0, 1e-4, fixed_rec)
    stack = lem.fix_stack(rec, n * n)
    P = fo.precip(h)
    Q = lem.accumulate(stack, rec, (P * lay.dx * lay.dx).ravel()).reshape(n, n)
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
    print(f'  guardado {salida}', flush=True)
    return d


if __name__ == '__main__':
    args = sys.argv[1:]
    modelar_desde(args[0] if args else 'salida/etapa1_p4.npz', args[1] if len(args) > 1 else 'salida/etapa1.npz')
