"""Etapa 1: historia geológica completa a resolución gruesa (por defecto 1024², 8 bloques/celda).

Fases:
  P1  orogenia (2,0 Ma): levantamiento por zona, clima pluvial ("desierto verde").
  P2  meseta (1,0 Ma): se levanta la meseta de los cañones mientras el río antecedente
      se encaja; el clima se vuelve árido.
  P3  glaciaciones (30 ka): ELA baja y mar a -40 m. Glaciares (SIA) + ríos al nivel bajo.
  P4  Holoceno (10 ka): el mar sube a 0 (valles y circos inundados = rías y fiordos),
      quedan glaciares pequeños en las cumbres más altas.
"""
import os
import time

import numpy as np

from . import lem
from .estructuras import cargar_sitios, canal_vieja_velkia
from .geology import Geology
from .glacier import glaciate
from .layout import Layout, poi_blocks, SEA
from .noise import blur
from . import jardines
from . import rios
from .rios import disenar_rio, rasterize_chain
from .volcan import build_volcano
from .sim import LEMState, run
from .tectonica import Forcing, smoothstep


def diffusivity(lay):
    z = lay.zonas
    D = (0.030 * z['cordillera'] + 0.020 * z['jardines'] + 0.050 * z['corrompidas'] +
         0.030 * z['oeste'] + 0.030 * z['este'] + 0.020 * z['volcanica'] + 0.025 * z['canones'] +
         0.010 * (z['desierto'] + z['dunas'] + z['salar']))
    return D.astype(np.float64)


def alluvial_factor(lay):
    """Peso de la difusión aluvial (migración y avulsión de cauces sobre el sedimento)."""
    z = lay.zonas
    return (1.0 * (z['desierto'] + z['dunas'] + z['salar']) + 0.5 * z['canones'] +
            0.3 * (z['este'] + z['oeste'] + z['volcanica'])).astype(np.float64)


def make_D_func(lay, D_alluvial=3.0):
    """Difusividad: reptación de laderas + difusión aluvial donde hay sedimento y poca pendiente
    (Paola et al. 1992: los abanicos y llanuras aluviales evolucionan como un medio difusivo)."""
    D0 = diffusivity(lay)
    af = alluvial_factor(lay)

    def D_func(s):
        sed = s.h - s.b
        S = lem.slope_d8(s.h, s.dx)
        w = np.clip(sed / 4.0, 0, 1) * np.clip(1.0 - S / 0.4, 0, 1) * (s.h > 0)
        return D0 + D_alluvial * af * w
    return D_func


def ela_field(lay, base, north_drop=60.0):
    """Línea de equilibrio glaciar: más baja en la vertiente norte (umbría) y al oeste."""
    zz, xx = lay.coords()
    dcres, _ = lay.cresta
    return base - north_drop * np.clip((3000 - zz) / 2000.0, -1, 1) + 25.0 * (xx - 3500) / 3500.0


def etapa1(n=1024, out_dir='salida', seed=7, log_every=25, solo_tectonica=False):
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)
    lay = Layout(n, seed=seed)
    geo = Geology(lay)
    fo = Forcing(lay, geo)
    dx = lay.dx
    zz, xx = lay.coords()

    # ------------------------------------------------ río antecedente y afluentes
    sitios = cargar_sitios(['vieja_velkia'])
    canal, canal_y = canal_vieja_velkia(sitios['vieja_velkia'])
    try:
        res = disenar_rio(canal, land=lay.land, dx=dx)
    except TypeError:
        res = disenar_rio(canal)
    rio_xy, rio_fijo, oxbows = res[0], res[1], res[2]
    boca = res[3] if len(res) > 3 else None
    chain = rasterize_chain(rio_xy, n, dx)
    # la fuente debe estar en tierra firme y alta: descartar celdas iniciales cerca del mar
    ini = np.nonzero(fo.h0.ravel()[chain] > 15.0)[0]
    if ini.size:
        chain = chain[ini[0]:]
    fixed_rec = np.full(n * n, -1, np.int64)
    fixed_rec[chain[:-1]] = chain[1:]
    cadenas = [chain]
    afl_xy = {}
    for nombre, pts in getattr(rios, 'AFLUENTES', {}).items():
        xy = rios.disenar_afluente(pts) if hasattr(rios, 'disenar_afluente') else np.asarray(pts, float)
        c = rasterize_chain(np.asarray(xy, float), n, dx)
        # unir al río principal en la celda más cercana (o terminar en el salar: sumidero)
        if nombre != 'rio_salado':
            cxy = np.c_[chain % n, chain // n]
            last = np.array([c[-1] % n, c[-1] // n])
            k = int(np.argmin(np.hypot(*(cxy - last).T)))
            c = c[~np.isin(c, chain)]
            if c.size == 0:
                continue
            fixed_rec[c[:-1]] = c[1:]
            fixed_rec[c[-1]] = chain[k]
        else:
            fixed_rec[c[:-1]] = c[1:]
        cadenas.append(c)
        afl_xy[nombre] = np.asarray(xy, float)
    fixed_rec = fixed_rec.reshape(n, n)
    rio_mask = np.zeros(n * n, bool)
    for c in cadenas:
        rio_mask[c] = True
    rio_mask = rio_mask.reshape(n, n)
    h0 = fo.h0.copy()
    trough = blur(rio_mask.astype(np.float64), 1.0)
    h0 -= 8.0 * trough / trough.max() * (h0 > 0)

    # ------------------------------------------------ sumidero del salar
    sx, sz = poi_blocks('bioma_de_sales')
    sink = None   # el salar se forma como cuenca cerrada por hundimiento (ver tectonica.py)

    st = LEMState(h0, h0, dx)
    # el río Velkia se alimenta del deshielo de la cordillera y de los lagos de los Jardines
    # (cuenca glaciar mayor que la resuelta aquí): ~1,5 m3/s de caudal de base
    # se inyecta a la salida de los Jardines (confluencia de la cuenca glaciar), no en la fuente
    cxy = np.c_[chain % n, chain // n] * dx
    k_out = int(np.argmin(np.hypot(cxy[:, 0] - 3040, cxy[:, 1] - 2900)))
    bflow = (int(chain[k_out]), 4.5e7)
    # el cauce principal es un río aluvial eficiente: transporta casi todo lo que recibe
    rio_cells = np.zeros(n * n, bool)
    rio_cells[chain[k_out:]] = True      # tramo aluvial: desde la salida de los Jardines al mar
    # forzado "siempre cuesta abajo" (antecedencia) solo en el tramo aluvial y en los afluentes;
    # en la montaña la pendiente natural ya baja y no debe arrastrar la fuente al nivel del mar
    cadenas[0] = chain[k_out:]
    # piso del lecho: 0,5 m sobre el mar en la boca + 0,07 % hacia aguas arriba (solo en tierra)
    alu = chain[k_out:]
    en_mar = fo.h0.ravel()[alu] < 0
    k_boca = int(np.argmax(en_mar)) if en_mar.any() else alu.size
    seg = np.r_[0, np.hypot(np.diff(alu % n), np.diff(alu // n))] * dx
    dist_boca = np.cumsum(seg[::-1])[::-1] - np.cumsum(seg[::-1])[::-1][min(k_boca, alu.size - 1)]
    piso = 0.5 + 7e-4 * np.maximum(dist_boca, 0)
    rfloor = (alu[:k_boca], piso[:k_boca])
    Garr = np.where(rio_cells, 0.08, 0.6)
    Kmul = np.where(rio_cells, 4.0, 1.0)
    D = make_D_func(lay)

    # fin del Río Salado = sumidero del salar (cuenca cerrada); su fondo no baja de Y≈70
    sal = [c for nm, c in zip(['principal'] + list(afl_xy.keys()), cadenas) if nm == 'rio_salado']
    salar_cell = int(sal[0][-1]) if sal else None

    def sink_cb(step, s):
        if salar_cell is not None:
            hf = s.h.ravel()
            if hf[salar_cell] < 8.0:
                hf[salar_cell] = 8.0
                s.b.ravel()[salar_cell] = min(s.b.ravel()[salar_cell], 8.0)

    # ------------------------------------------------ P1
    fo.P_base = fo.P_pluvial
    st._dt = 1e4
    print('== P1 orogenia', flush=True)
    run(st, geo, fo, 2.0e6, 1e4, lambda t: fo.U_orogeny, D_func=D, sinks=sink,
        fixed_rec=fixed_rec, baseflow=bflow, G_arr=Garr, Kmult_arr=Kmul, breach=cadenas, river_floor=rfloor, log_every=log_every, label='P1', callback=sink_cb)
    np.savez_compressed(os.path.join(out_dir, 'etapa1_p1.npz'), h=st.h, b=st.b)

    # ------------------------------------------------ P2
    print('== P2 meseta + aridificación', flush=True)
    T2 = 1.0e6

    def cb2(step, s):
        frac = min(1.0, (step + 1) * 1e4 / T2)
        fo.P_base = fo.P_pluvial * (1 - frac) + fo.P_arid * frac
        sink_cb(step, s)

    run(st, geo, fo, T2, 1e4, lambda t: 0.85 * fo.U_orogeny + fo.U_plateau, D_func=D,
        sinks=sink, fixed_rec=fixed_rec, baseflow=bflow, G_arr=Garr, Kmult_arr=Kmul, breach=cadenas, river_floor=rfloor, log_every=log_every, label='P2', callback=cb2)
    np.savez_compressed(os.path.join(out_dir, 'etapa1_p2.npz'), h=st.h, b=st.b, chain=chain)
    if solo_tectonica:
        return st, lay, geo, fo

    # ------------------------------------------------ volcán (coladas + piroclastos)
    print('== Volcán', flush=True)
    vx, vz = poi_blocks('region_volcanica')
    hv, lava = build_volcano(st.h.copy(), dx, (vx - 70, vz - 20), height=230.0, radius=1100.0,
                             n_flows=2600, log=False)
    st.h = hv
    st.b = np.maximum(st.b, hv - 0.5)      # roca volcánica nueva
    print(f'  cumbre del volcán: Y={hv.max() + SEA:.0f}', flush=True)

    # ------------------------------------------------ P3 glaciaciones
    print('== P3 glaciaciones (mar a -40 m)', flush=True)
    fo.P_base = fo.P_arid
    ela_lgm = ela_field(lay, 255.0, north_drop=50.0)
    ice_mask = lay.zonas['cordillera'] + lay.zonas['jardines'] + lay.zonas['corrompidas'] > 0.05
    H = None
    gl_ero = np.zeros((n, n))
    st._dt = 1e3
    for k in range(6):
        hg, H, ero = glaciate(st.h, dx, ela_lgm, -40.0, 5000.0, H=H, mask=ice_mask, log=(k % 2 == 0))
        st.h = hg
        st.b = np.minimum(st.b, st.h)
        gl_ero += ero
        run(st, geo, fo, 5000.0, 1000.0, lambda t: 0.85 * fo.U_orogeny + fo.U_plateau,
            sea_level=-40.0, D_func=D, sinks=sink, fixed_rec=fixed_rec, baseflow=bflow, G_arr=Garr, Kmult_arr=Kmul, breach=cadenas, river_floor=rfloor, log_every=0,
            label='P3', callback=sink_cb)
        print(f'  ciclo glaciar {k + 1}/6 listo, erosión glaciar máx {gl_ero.max():.0f} m', flush=True)
    H_lgm = H.copy()

    # ------------------------------------------------ Jardines: excavación glaciar del valle
    print('== Jardines (valle glaciar en U)', flush=True)
    st.h, st.b, lagos_jardines = jardines.excavar(st.h, st.b, lay, chain)

    # ------------------------------------------------ P4 Holoceno
    print('== P4 Holoceno (mar a 0)', flush=True)
    st._dt = 500.0
    ela_hol = ela_field(lay, 405.0, north_drop=35.0)
    hg, H, ero = glaciate(st.h, dx, ela_hol, 0.0, 4000.0, H=H * 0.0, mask=ice_mask, Kg=0.8e-5)
    st.h = hg
    st.b = np.minimum(st.b, st.h)
    gl_ero += ero
    run(st, geo, fo, 10000.0, 500.0, lambda t: 0.85 * fo.U_orogeny + fo.U_plateau, sea_level=0.0,
        D_func=D, sinks=sink, fixed_rec=fixed_rec, baseflow=bflow, G_arr=Garr, Kmult_arr=Kmul, breach=cadenas, river_floor=rfloor, log_every=log_every, label='P4',
        callback=sink_cb)

    # ------------------------------------------------ guardar
    rec, stack, filled = lem.route_flow(st.h, st.h < 0, 1e-4, fixed_rec)
    stack = lem.fix_stack(rec, n * n)
    P = fo.precip(st.h)
    Q = lem.accumulate(stack, rec, (P * dx * dx).ravel()).reshape(n, n)
    np.savez_compressed(os.path.join(out_dir, 'etapa1.npz'), h=st.h, b=st.b, Q=Q, filled=filled,
                        gl_ero=gl_ero, H_ice=H, H_lgm=H_lgm, rio_xy=rio_xy, rio_fijo=rio_fijo,
                        chain=chain, zone_id=lay.zone_id, prov=geo.prov,
                        oxbows=np.array(len(oxbows)), lava=lava, lagos_jardines=lagos_jardines,
                        afluentes=np.array(list(afl_xy.keys())),
                        **{'afl_' + k: v for k, v in afl_xy.items()},
                        **{'cad_' + str(i): c for i, c in enumerate(cadenas)},
                        boca=np.array([boca['x'], boca['z']]) if isinstance(boca, dict) and 'x' in boca else np.zeros(2))
    print(f'Etapa 1 lista en {time.time() - t0:.0f} s', flush=True)
    return st, lay, geo, fo
