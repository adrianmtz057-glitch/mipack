"""Etapa 4: mundo jugable de baja resolución (terreno de la etapa 1 ampliado a 1 bloque).

  python3 -m velkia.etapa4 preparar   -> salida/mundo_datos/ (Y, WL, FL, SURF, SDEP, BIO, ...)
  python3 -m velkia.etapa4 construir  -> salida/mundo/Velkia (regiones .mca, level.dat, datapack)

Agua (Minecraft la tiene plana por nivel):
  * mar a Y=62 (todo lo que queda bajo 62 y conecta con el mar);
  * río y afluentes: nivel entero por vértice, que nunca sube aguas abajo, sacado del nivel de
    la malla gruesa (agua.superficie); cauce parabólico bajo el nivel y orillas al nivel;
  * lagos de los Jardines a un nivel; canal y lago de lava del volcán;
  * sellado final: ninguna celda de agua tiene al lado tierra más baja que su nivel (salvo en
    los bordes de las cascadas, donde el agua cae).
Las construcciones se pegan tal cual (structure_void no se pega) con su dy.
"""
import json
import os
import sys
import time

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from . import agua, lem
from .colocar import colocar
from .layout import Layout, N, SEA
from .materials import SUP
from .preparar_mundo import ampliar
from .sim import ocean_mask

BIOMAS = ['minecraft:ocean', 'minecraft:deep_ocean', 'minecraft:beach', 'minecraft:river', 'minecraft:desert',
          'minecraft:badlands', 'minecraft:eroded_badlands', 'minecraft:savanna_plateau', 'minecraft:snowy_slopes',
          'minecraft:jagged_peaks', 'minecraft:stony_peaks', 'minecraft:windswept_gravelly_hills',
          'velkia:salar', 'velkia:volcanica', 'velkia:tierras_corrompidas', 'velkia:jardines',
          'minecraft:stony_shore', 'minecraft:warm_ocean', 'minecraft:frozen_peaks', 'minecraft:wooded_badlands']
B = {k.split(':')[1]: i for i, k in enumerate(BIOMAS)}
TILE = 512


# ===================================================================== utilidades
def _densificar(xy, paso=2.0, *attrs):
    """Remuestrea una polilínea cada 'paso' bloques; interpola los atributos por vértice."""
    xy = np.asarray(xy, float)
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    t = np.arange(0, s[-1], paso)
    out = np.c_[np.interp(t, s, xy[:, 0]), np.interp(t, s, xy[:, 1])]
    return (out,) + tuple(np.interp(t, s, a) for a in attrs)


def _por_teselas(xy, alcance, M, fn):
    """Llama fn(z0, z1, x0, x1, idx) para cada tesela de TILE bloques que toca la polilínea
    (idx: vértices a menos de 'alcance' de la tesela)."""
    tx = (xy[:, 0] // TILE).astype(int)
    tz = (xy[:, 1] // TILE).astype(int)
    tes = set()
    r = int(np.ceil(alcance / TILE))
    for a, b in zip(tz, tx):
        for da in range(-r, r + 1):
            for db in range(-r, r + 1):
                tes.add((a + da, b + db))
    for a, b in sorted(tes):
        z0, x0 = a * TILE, b * TILE
        if z0 < 0 or x0 < 0 or z0 >= M or x0 >= M:
            continue
        z1, x1 = min(z0 + TILE, M), min(x0 + TILE, M)
        sel = ((xy[:, 0] > x0 - alcance) & (xy[:, 0] < x1 + alcance) &
               (xy[:, 1] > z0 - alcance) & (xy[:, 1] < z1 + alcance))
        if sel.any():
            fn(z0, z1, x0, x1, np.nonzero(sel)[0])


def cauce(Y, WL, FL, xy, ancho, nivel, prof, fluido=1, seco=None, sin_orilla=None, mar=None):
    """Talla un cauce a lo largo de xy (vértices densos): agua 'fluido' al nivel entero de
    cada vértice, lecho parabólico 'prof' bloques bajo el nivel en el centro, orillas de 2
    bloques al nivel.  seco: máscara (bloque) donde no se pone agua (construcciones).
    sin_orilla: vértices sin orilla (bordes de cascada).  nivel: NaN = sin agua."""
    M = Y.shape[0]
    half = 0.5 * np.asarray(ancho, float)
    alc = half.max() + 3.0

    def fn(z0, z1, x0, x1, idx):
        t = cKDTree(xy[idx])
        zz, xx = np.mgrid[z0:z1, x0:x1]
        d, k = t.query(np.c_[xx.ravel() + 0.5, zz.ravel() + 0.5], distance_upper_bound=alc)
        ok = np.isfinite(d)
        if not ok.any():
            return
        kk = idx[np.where(ok, k, 0)]
        lv = nivel[kk]
        hw = half[kk]
        con = ok & np.isfinite(lv)
        dentro = con & (d <= hw)
        orilla = con & (d > hw) & (d <= hw + 2.0)
        if sin_orilla is not None:
            orilla &= ~sin_orilla[kk]
        sub = Y[z0:z1, x0:x1].ravel().astype(np.float32)
        wl = WL[z0:z1, x0:x1].ravel()
        fl = FL[z0:z1, x0:x1].ravel()
        sec = seco[z0:z1, x0:x1].ravel() if seco is not None else np.zeros(sub.size, bool)
        mr = mar[z0:z1, x0:x1].ravel() if mar is not None else np.zeros(sub.size, bool)
        lvs = np.where(con, lv, 0.0)
        pf = np.asarray(prof)[kk] if np.ndim(prof) else prof
        lecho = np.floor(lvs - 1.0 - (pf - 1.0) * np.clip(1.0 - (d / np.maximum(hw, 1.0)) ** 2, 0, 1))
        dentro &= ~sec & ~mr
        orilla &= ~sec & ~mr & (fl == 0)
        sub = np.where(dentro, np.minimum(sub, lecho), sub)
        wl = np.where(dentro, np.maximum(wl, lvs.astype(np.int16)) if fluido == 2 else lvs.astype(np.int16), wl)
        fl = np.where(dentro, fluido, fl)
        sub = np.where(orilla, np.maximum(sub, lvs), sub)
        Y[z0:z1, x0:x1] = sub.reshape(zz.shape)
        WL[z0:z1, x0:x1] = wl.reshape(zz.shape).astype(np.int16)
        FL[z0:z1, x0:x1] = fl.reshape(zz.shape).astype(np.uint8)

    _por_teselas(xy, alc, M, fn)


def niveles_desde_cadena(xy, chain, wl_chain, n, dx):
    """Nivel entero por vértice: el de la celda gruesa del cauce más cercana, sin subir nunca."""
    cxy = np.c_[(chain % n + 0.5) * dx, (chain // n + 0.5) * dx]
    d, k = cKDTree(cxy).query(xy)
    lv = np.where(d < 3 * dx, wl_chain[k], np.nan)
    # antes de la fuente (vértices sin celda con agua) no hay agua
    ok = np.isfinite(lv)
    if ok.any():
        i0 = int(np.argmax(ok))
        lv[:i0] = np.nan
        seg = lv[i0:]
        seg = np.where(np.isfinite(seg), seg, np.inf)
        seg = np.minimum.accumulate(np.floor(seg))
        lv[i0:] = np.where(np.isfinite(seg), seg, np.nan)
    return lv


def sellar(Y, WL, FL, permitir=None, iters=4):
    """Sin agua colgada: la tierra vecina (4 direcciones) de una celda con fluido sube al nivel
    del fluido.  permitir: máscara donde el fluido puede caer (cascadas)."""
    hay = FL > 0
    for _ in range(iters):
        req = np.full(Y.shape, -32768, np.int32)
        for dz, dxx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            w = np.where(hay & ~(permitir if permitir is not None else False), WL, -32768)
            req = np.maximum(req, np.roll(w, (dz, dxx), (0, 1)))
        sube = ~hay & (Y < req)
        if not sube.any():
            break
        Y[sube] = req[sube]
    return int(sube.sum())


# ===================================================================== preparar
def preparar(etapa='salida/etapa1.npz', out='salida/mundo_datos', log=True, fluidos=True):
    """fluidos=False: solo terreno, construcciones y mar (los ríos, lagos y lava los pone la v2)."""
    t0 = time.time()
    os.makedirs(out, exist_ok=True)
    d = np.load(etapa)
    h = d['h']
    n = h.shape[0]
    dx = N / n
    f = int(dx)
    lay = Layout(n)
    Y0 = h + SEA
    ch = d['chain']
    cy = Y0.ravel()[ch]
    cx, cz = (ch % n + 0.5) * dx, (ch // n + 0.5) * dx

    def rio_y(x, z):
        k = int(np.argmin(np.hypot(cx - x, cz - z)))
        return float(cy[k]) + 1.5

    def paso(txt):
        if log:
            print(f'  [{time.time() - t0:5.0f} s] {txt}', flush=True)

    # ---------------------------------------------- terreno a 1 bloque y construcciones asentadas
    Y = ampliar(Y0.astype(np.float32), f)
    out_c, Y = colocar(Y, 1.0, rio_y=rio_y, busqueda=(Y0, dx, lay.dist_coast), log=False)
    paso('terreno ampliado y construcciones asentadas')
    # huellas (sin agua del terreno dentro: el schematic trae la suya) y suelo propio
    huella = np.zeros((N, N), bool)
    Ys1 = Y.copy()
    for o in out_c:
        m = o['maps']
        zz, xx = np.nonzero(m['foot'])
        huella[zz + m['z0'], xx + m['x0']] = True
        zz, xx = np.nonzero(m['foot'] & (m['ground'] > -900))
        Ys1[zz + m['z0'], xx + m['x0']] = np.maximum(Ys1[zz + m['z0'], xx + m['x0']], m['ground'][zz, xx] + o['dy'])
    # ---------------------------------------------- niveles de agua en la malla gruesa
    Ym = Ys1.reshape(n, f, n, f).mean(axis=(1, 3)).astype(np.float64)
    del Ys1
    hm = np.ascontiguousarray(Ym - SEA)
    bm = hm.copy()
    for k in sorted([k for k in d.files if k.startswith('cad_')], key=lambda s: int(s[4:])):
        lem.breach_chain(hm, bm, np.ascontiguousarray(d[k]), 2e-4, dx)
    oc = ocean_mask(hm, 0.0)
    Ymc, WLc, tipo, inf = agua.superficie(d, hm + SEA, oc)
    paso(f"niveles en malla gruesa: río {inf['rio']}")
    # ---------------------------------------------- fluidos a 1 bloque
    WL = np.full((N, N), -32768, np.int16)
    FL = np.zeros((N, N), np.uint8)
    # mar: bajo 62 y conectado con el mar de la malla gruesa
    ocb = np.repeat(np.repeat(ndi.binary_dilation(oc, iterations=2), f, 0), f, 1)
    bajo = Y < SEA - 0.5
    mar = ndi.binary_propagation(bajo & ocb, mask=bajo)
    Y = np.where(bajo & ~mar & ~huella, np.float32(SEA), Y)        # hoyos sueltos bajo el mar: a tierra
    WL[mar] = SEA
    FL[mar] = 1
    paso(f'mar: {mar.mean() * 100:.1f} % del mapa')
    if fluidos:
        # río principal
        k0 = int(d['k_fuente']) if 'k_fuente' in d.files else 0
        chm = ch[k0:]
        wl_ch = WLc.ravel()[chm]
        fin = int(np.argmax(~np.isfinite(wl_ch))) if (~np.isfinite(wl_ch)).any() else chm.size
        chm, wl_ch = chm[:fin], wl_ch[:fin]
        from .rios import ANCHO_MIN
        rxy = d['rio_xy']
        anch = np.interp(np.arange(len(rxy)), [0, len(rxy) - 1], [ANCHO_MIN, 30.0])
        rxy, anch = _densificar(rxy, 2.0, anch)
        lv = niveles_desde_cadena(rxy, chm, wl_ch, n, dx)
        casc = np.zeros(len(rxy), bool)
        salto = np.nonzero(np.diff(np.nan_to_num(lv, nan=-1e9)) < -3)[0]
        for k in salto:
            casc[max(0, k - 20):k + 20] = True
        cauce(Y, WL, FL, rxy, anch, lv, 3.0, seco=huella, sin_orilla=casc, mar=mar)
        paso(f'río: {np.isfinite(lv).sum()} vértices con agua, {len(salto)} cascadas')
        # afluentes
        for k in sorted([k for k in d.files if k.startswith('cad_')], key=lambda s: int(s[4:]))[2:]:
            nm = [a for a in d['afluentes']][int(k[4:]) - 2] if 'afluentes' in d.files else None
            if nm is None or 'afl_' + str(nm) not in d.files:
                continue
            c = d[k][int(d['kf_' + k]) if 'kf_' + k in d.files else 0:]
            w = WLc.ravel()[c]
            fin = int(np.argmax(~np.isfinite(w))) if (~np.isfinite(w)).any() else c.size
            axy, = _densificar(d['afl_' + str(nm)], 2.0)
            lva = niveles_desde_cadena(axy, c[:fin], w[:fin], n, dx)
            cauce(Y, WL, FL, axy, np.full(len(axy), 9.0), lva, 2.0, seco=huella, mar=mar)
            paso(f'afluente {nm}: {np.isfinite(lva).sum()} vértices con agua')
        # lagos de los Jardines
        if 'lagos_jardines' in d.files:
            lg = ndi.zoom(d['lagos_jardines'].astype(np.float32), f, order=1) > 0.5
            lg &= ~huella
            nivel = int(np.floor(float(d['jardines_piso']) + SEA - 0.5))
            prof = np.clip(ndi.distance_transform_edt(lg) / 6.0, 1, 6)
            Y = np.where(lg, np.minimum(Y, nivel - prof), Y)
            WL[lg] = nivel
            FL[lg] = 1
            paso(f'lagos de los Jardines a Y={nivel}')
        # lava: canales (polilíneas del volcán) y lago del cráter
        if 'lava_xy' in d.files:
            L = d['lava_xy']
            cortes = np.nonzero(np.isnan(L[:, 0]))[0]
            ini = 0
            for c in list(cortes) + [len(L)]:
                seg = L[ini:c]
                ini = c + 1
                if len(seg) < 3:
                    continue
                sxy, = _densificar(seg, 2.0)
                iz = np.clip(sxy[:, 1].astype(int), 0, N - 1)
                ix = np.clip(sxy[:, 0].astype(int), 0, N - 1)
                lvl = np.minimum.accumulate(np.floor(Y[iz, ix]))
                lvl = np.where(mar[iz, ix], np.nan, lvl)
                cauce(Y, WL, FL, sxy, np.full(len(sxy), 5.0), lvl, 2.0, fluido=2, seco=huella, mar=mar)
            if 'lago_lava' in d.files and d['lago_lava'].any():
                ll = ndi.zoom(d['lago_lava'].astype(np.float32), f, order=1) > 0.5
                if ll.any():
                    nv = int(np.floor(np.percentile(Y[ll], 30)))
                    Y = np.where(ll, np.minimum(Y, nv - 2), Y)
                    WL[ll] = nv
                    FL[ll] = 2
            paso('lava')
    # sellado (sin agua colgada), dejando caer el agua en las cascadas
    permitir = np.zeros((N, N), bool)
    for x, z, dz in (inf.get('cascadas_rio', []) if fluidos else []):
        if dz > 3:
            permitir[max(0, int(z) - 48):int(z) + 48, max(0, int(x) - 48):int(x) + 48] = True
    nsub = sellar(Y, WL, FL, permitir)
    paso(f'sellado: {nsub} celdas en la última pasada')
    Yi = np.round(Y).astype(np.int16)
    WL = np.where(FL > 0, np.maximum(WL, Yi + 1), WL).astype(np.int16)   # al menos 1 de agua
    # ---------------------------------------------- superficie, suelo y biomas
    SURF, SDEP, BIO = superficies(Yi, WL, FL, mar, lay, d, f)
    paso('superficies y biomas')
    sendero_torre(Yi, SURF, out_c, mar, lay)
    paso('sendero de la torre')
    # ---------------------------------------------- construcciones
    est_dir = os.path.join(out, 'estructuras')
    os.makedirs(est_dir, exist_ok=True)
    est = []
    for o in out_c:
        import unicodedata
        slug = unicodedata.normalize('NFKD', o['nombre']).encode('ascii', 'ignore').decode().lower()
        slug = ''.join(ch if ch.isalnum() else '_' for ch in slug).strip('_')
        for i, p in enumerate(o['sitio'].parts):
            nombre = f"{slug}_{i}"
            ruta = os.path.abspath(os.path.join(est_dir, nombre + '.schem'))
            p.save(ruta)
            off = [int(p.offset[0]), int(p.offset[1] + o['dy']), int(p.offset[2])]
            est.append({'nombre': o['nombre'], 'archivo': ruta, 'offset': off, 'size': [int(v) for v in p.size]})
    json.dump(est, open(os.path.join(out, 'estructuras.json'), 'w'), indent=1, ensure_ascii=False)
    # ---------------------------------------------- guardar
    for nm, a in (('Y', Yi), ('WL', WL), ('FL', FL), ('SURF', SURF), ('SDEP', SDEP), ('BIO', BIO)):
        np.save(os.path.join(out, nm + '.npy'), a)
    from .geology import Geology
    geo = Geology(lay)
    # provincia de la etapa 1 (incluye mesas y domos del modelado)
    np.savez_compressed(os.path.join(out, 'geologia.npz'), prov=d['prov'], zref=geo.zref, thick=geo.thick)
    json.dump(BIOMAS, open(os.path.join(out, 'biomas.json'), 'w'))
    info = {'colocacion': [{'nombre': o['nombre'], 'dy': int(o['dy']), 'shift': list(o['shift']),
                            'flota': o['despues']['flotacion_max'], 'enterrado': o['despues']['enterramiento_max']}
                           for o in out_c], 'agua_gruesa': {k: v for k, v in inf.items() if k != 'rio'},
            'rio': inf['rio'], 'fugas': int(fugas(Yi, WL, FL, permitir | huella).sum())}
    json.dump(info, open(os.path.join(out, 'info.json'), 'w'), indent=1, ensure_ascii=False, default=float)
    paso(f"guardado en {out}; fugas: {info['fugas']}")
    return info


def fugas(Y, WL, FL, permitir=None):
    """Celdas con fluido que tienen al lado tierra más baja que su nivel."""
    hay = FL > 0
    f = np.zeros(Y.shape, bool)
    for dz, dxx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        Yn = np.roll(Y, (dz, dxx), (0, 1))
        Hn = np.roll(hay, (dz, dxx), (0, 1))
        f |= hay & ~Hn & (Yn < WL)
    if permitir is not None:
        f &= ~permitir
    return f


def superficies(Y, WL, FL, mar, lay, d, f):
    """Códigos de superficie (materials.SUP), espesor de suelo y bioma por columna."""
    n = lay.n
    zid = np.repeat(np.repeat(lay.zone_id, f, 0), f, 1)
    # bordes de zona menos rectos: desplazamiento con ruido
    from .noise import spectral_noise
    wz = (spectral_noise((n, n), 3.0, 77) * 40.0).astype(np.float32)
    wx = (spectral_noise((n, n), 3.0, 78) * 40.0).astype(np.float32)
    zid_w = np.empty((N, N), np.uint8)
    cols = (np.arange(N) + 0.5) / f - 0.5
    for r0 in range(0, N, 1024):
        r1 = r0 + 1024
        filas = (np.arange(r0, r1) + 0.5) / f - 0.5
        FZ, FX = np.meshgrid(filas, cols, indexing='ij')
        # desplazamiento interpolado (continuo): sin escalones de celda en los bordes de zona
        dz = ndi.map_coordinates(wz, [FZ, FX], order=1, mode='nearest')
        dxw = ndi.map_coordinates(wx, [FZ, FX], order=1, mode='nearest')
        zz = (np.arange(r0, r1)[:, None] + dz).astype(np.int64)
        xx = (np.arange(N)[None, :] + dxw).astype(np.int64)
        zid_w[r0:r1] = zid[np.clip(zz, 0, N - 1), np.clip(xx, 0, N - 1)]
    del zid
    names = lay.zone_names
    Z = {k: i for i, k in enumerate(names)}
    gz, gx = np.gradient(Y.astype(np.float32))
    S = np.hypot(gz, gx)
    del gz, gx
    sed = np.repeat(np.repeat(np.clip(d['h'] - d['b'], 0, 8).astype(np.float32), f, 0), f, 1)
    SURF = np.full((N, N), SUP['arena'], np.uint8)
    BIO = np.full((N, N), B['desert'], np.uint8)
    agua_ = FL == 1
    tierra = ~mar
    zona = lambda k: zid_w == Z[k]
    # por zona
    for k, sup, bio in (('desierto', 'arena', 'desert'), ('dunas', 'arena', 'desert'),
                        ('salar', 'sal', 'salar'), ('canones', 'terracota', 'badlands'),
                        ('este', 'tierra_gruesa', 'savanna_plateau'), ('oeste', 'arena_roja', 'wooded_badlands'),
                        ('volcanica', 'ceniza', 'volcanica'), ('corrompidas', 'corrompido', 'tierras_corrompidas'),
                        ('jardines', 'pradera', 'jardines'), ('cordillera', 'grava', 'windswept_gravelly_hills')):
        if k in Z:
            m = zona(k)
            SURF[m] = SUP[sup]
            BIO[m] = B[bio]
    # cordillera: nieve en lo alto, roca en las laderas, picos
    alto = Y > 330
    SURF[zona('cordillera') & alto] = SUP['nieve']
    BIO[zona('cordillera') & (Y > 300)] = B['snowy_slopes']
    BIO[zona('cordillera') & (Y > 380)] = B['jagged_peaks']
    SURF[(zona('corrompidas') | zona('cordillera')) & (Y > 400)] = SUP['nieve']
    # cañones: terracota en llanos, roca en paredes (se ven los estratos)
    BIO[zona('canones') & (S > 0.8)] = B['eroded_badlands']
    # Jardines: pradera en el fondo, granito y pasto en la meseta
    if 'jardines_piso' in d.files:
        piso = float(d['jardines_piso']) + SEA
        SURF[zona('jardines') & (Y > piso + 25)] = SUP['pasto']
    # mesas, buttes y domos: roca desnuda (cornisa y estratos a la vista; granito en los domos);
    # arena solo en el pie de los taludes
    rel = _mascara_relieves(d, lay)
    if rel is not None:
        relb = np.repeat(np.repeat(rel, f, 0), f, 1)
        SURF[relb & ((S > 0.25) | (Y > np.repeat(np.repeat(d['h'], f, 0), f, 1) + SEA - 2))] = SUP['roca']
    # roca en pendientes fuertes (paredes, escarpes de mesas, caldera)
    SURF[S > 1.1] = SUP['roca']
    SURF[(S > 0.75) & zona('cordillera')] = SUP['roca']
    # lava: basalto alrededor
    lava = FL == 2
    if lava.any():
        cerca = ndi.binary_dilation(lava, iterations=4)
        SURF[cerca & ~lava] = SUP['roca']
    # costa: playas (arena negra en la región volcánica), fondo marino
    costa = ndi.binary_dilation(mar, iterations=6) & tierra & (Y <= SEA + 3)
    SURF[costa] = SUP['arena']
    SURF[costa & zona('volcanica')] = SUP['arena_negra']
    BIO[costa] = B['beach']
    BIO[costa & (S > 0.6)] = B['stony_shore']
    prof = SEA - Y
    SURF[mar] = np.where(prof[mar] < 8, SUP['arena'], SUP['grava'])
    BIO[mar] = np.where(prof[mar] > 30, B['deep_ocean'], B['warm_ocean'])
    # ríos y lagos: grava en el lecho, río como bioma
    SURF[agua_ & ~mar] = SUP['grava']
    BIO[ndi.binary_dilation(agua_ & ~mar, iterations=3) & ~mar] = B['river']
    BIO[agua_ & ~mar & zona('jardines')] = B['jardines']
    SURF[(FL == 1) & ~mar & zona('salar')] = SUP['barro']
    # espesor de suelo
    SDEP = np.clip(np.round(1 + sed), 1, 8).astype(np.uint8)
    SDEP[SURF == SUP['arena']] = np.maximum(SDEP[SURF == SUP['arena']], 4)
    return SURF, SDEP, BIO


def _mascara_relieves(d, lay):
    """Celdas gruesas cuya superficie la dan las mesas, buttes y domos del modelado."""
    if 'relieves_json' not in d.files:
        return None
    from .modelado import perfil_relieve
    h = d['h']
    n, dx = lay.n, lay.dx
    rel = np.zeros((n, n), bool)
    for g in json.loads(str(d['relieves_json'])):
        for m in g['miembros']:
            if 'base' not in m:
                continue
            alc = m['R'] * m['elong'] * 1.25 + (300.0 if g['tipo'] == 'mesa' else 60.0)
            i0, i1 = int(max((m['z'] - alc) / dx, 0)), int(min((m['z'] + alc) / dx + 1, n))
            j0, j1 = int(max((m['x'] - alc) / dx, 0)), int(min((m['x'] + alc) / dx + 1, n))
            Zg, Xg = np.meshgrid((np.arange(i0, i1) + 0.5) * dx - m['z'], (np.arange(j0, j1) + 0.5) * dx - m['x'],
                                 indexing='ij')
            p = perfil_relieve(Xg, Zg, m, m['base'], m.get('cima'))
            rel[i0:i1, j0:j1] |= p >= h[i0:i1, j0:j1] - 0.5
    return rel


# ===================================================================== sendero de la torre
def sendero_torre(Y, SURF, out_c, mar, lay, pend_max=0.14, radio=420.0, paso=4, log=True):
    """Sendero nuevo de la Torre: desde el borde de la plaza hasta el pie del cerro por el lado
    de tierra, con pendiente <= pend_max (zigzag donde la ladera es más empinada).
    Camino de costo mínimo en una malla de 'paso' bloques; luego perfil suavizado y tallado
    (corte y relleno) de 3 bloques de ancho con dirt_path."""
    import heapq
    o = next(o for o in out_c if o['nombre'].startswith('Torre'))
    m = o['maps']
    top = np.where(m['foot'], m['top'], -999)
    ci = np.unravel_index(np.argmax(top), top.shape)
    tx, tz = m['x0'] + ci[1], m['z0'] + ci[0]
    x0, z0 = int(tx - radio), int(tz - radio)
    L = int(2 * radio) // paso
    sl = (slice(z0, z0 + L * paso), slice(x0, x0 + L * paso))
    Yw = np.asarray(Y[sl], np.float32)
    G = Yw.reshape(L, paso, L, paso).mean(axis=(1, 3))
    agua = np.asarray(mar[sl]).reshape(L, paso, L, paso).any(axis=(1, 3))
    huella = np.zeros((L * paso, L * paso), bool)
    zz, xx = np.nonzero(m['foot'])
    gz, gx = zz + m['z0'] - z0, xx + m['x0'] - x0
    ok = (gz >= 0) & (gz < L * paso) & (gx >= 0) & (gx < L * paso)
    huella[gz[ok], gx[ok]] = True
    plaza = huella.reshape(L, paso, L, paso).any(axis=(1, 3))
    # destino: punto bajo del anillo de 260-360 bloques, lo más tierra adentro posible
    cz_, cx_ = np.mgrid[0:L, 0:L]
    r = np.hypot((cx_ + 0.5) * paso + x0 - tx, (cz_ + 0.5) * paso + z0 - tz)
    dc = lay.dist_coast[np.clip(((cz_ + 0.5) * paso + z0) / lay.dx, 0, lay.n - 1).astype(int),
                        np.clip(((cx_ + 0.5) * paso + x0) / lay.dx, 0, lay.n - 1).astype(int)]
    anillo = (r > 260) & (r < 360) & ~agua & (G > SEA + 2)
    if not anillo.any():
        return 0
    score = np.where(anillo, G - 0.25 * dc, np.inf)
    dz_, dx_ = np.unravel_index(np.argmin(score), score.shape)
    # inicio: celdas del borde de la plaza
    borde = plaza & ~ndi.binary_erosion(plaza)
    # Dijkstra con penalización por pendiente (prohibida > 3·pend_max)
    INF = np.inf
    dist = np.full((L, L), INF)
    prev = np.full((L, L, 2), -1, np.int64)
    pq = []
    for a, b in zip(*np.nonzero(borde)):
        dist[a, b] = 0.0
        heapq.heappush(pq, (0.0, a, b))
    vec = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while pq:
        dd, a, b = heapq.heappop(pq)
        if dd > dist[a, b]:
            continue
        if (a, b) == (dz_, dx_):
            break
        for da, db in vec:
            na, nb = a + da, b + db
            if not (0 <= na < L and 0 <= nb < L) or agua[na, nb] or plaza[na, nb]:
                continue
            ln = paso * (1.4142 if da and db else 1.0)
            g = abs(G[na, nb] - G[a, b]) / ln
            if g > 3 * pend_max:
                continue
            c = ln * (1.0 + 60.0 * max(0.0, g - pend_max) ** 1.0 + 2.0 * g)
            if dd + c < dist[na, nb]:
                dist[na, nb] = dd + c
                prev[na, nb] = (a, b)
                heapq.heappush(pq, (dd + c, na, nb))
    if not np.isfinite(dist[dz_, dx_]):
        if log:
            print('  sendero de la torre: sin camino', flush=True)
        return 0
    camino = []
    a, b = dz_, dx_
    while a >= 0:
        camino.append(((b + 0.5) * paso + x0, (a + 0.5) * paso + z0))
        a, b = prev[a, b]
    camino = np.array(camino[::-1])
    # suavizado (Chaikin) y remuestreo cada bloque
    for _ in range(3):
        q = 0.75 * camino[:-1] + 0.25 * camino[1:]
        r_ = 0.25 * camino[:-1] + 0.75 * camino[1:]
        camino = np.r_[camino[:1], np.c_[q, r_].reshape(-1, 2), camino[-1:]]
    camino, = _densificar(camino, 1.0)
    # perfil: terreno suavizado con pendiente limitada, empezando a la cota de la plaza
    iz = np.clip(camino[:, 1].astype(int), 0, N - 1)
    ix = np.clip(camino[:, 0].astype(int), 0, N - 1)
    t = np.asarray(Y[iz, ix], np.float64)
    k = 9
    t = np.convolve(np.r_[np.full(k, t[0]), t, np.full(k, t[-1])], np.ones(2 * k + 1) / (2 * k + 1), 'same')[k:-k]
    zc, xc = np.nonzero(m['foot'])
    j = int(np.argmin(np.hypot(m['x0'] + xc - camino[0, 0], m['z0'] + zc - camino[0, 1])))
    t[0] = float(o['ref'][zc[j], xc[j]] + o['dy'])
    for _ in range(4):
        for i in range(1, len(t)):
            t[i] = np.clip(t[i], t[i - 1] - pend_max, t[i - 1] + pend_max)
        for i in range(len(t) - 2, 0, -1):
            t[i] = np.clip(t[i], t[i + 1] - pend_max, t[i + 1] + pend_max)
    # tallar: núcleo de 3 bloques a la cota del perfil, transición de 4 bloques a cada lado
    tree = cKDTree(camino)
    a0, a1 = int(camino[:, 1].min()) - 8, int(camino[:, 1].max()) + 9
    b0, b1 = int(camino[:, 0].min()) - 8, int(camino[:, 0].max()) + 9
    zz, xx = np.mgrid[a0:a1, b0:b1]
    dd, kk = tree.query(np.c_[xx.ravel() + 0.5, zz.ravel() + 0.5], distance_upper_bound=7.0)
    okc = np.isfinite(dd)
    kk = np.where(okc, kk, 0)
    sub = Y[a0:a1, b0:b1].ravel().astype(np.float64)
    perf = t[kk]
    w = np.clip((7.0 - dd) / 4.0, 0, 1)
    w = w * w * (3 - 2 * w)
    H = np.zeros((a1 - a0, b1 - b0), bool)               # la plaza de la torre no se toca
    zf, xf = np.nonzero(m['foot'])
    g1, g2 = zf + m['z0'] - a0, xf + m['x0'] - b0
    okh = (g1 >= 0) & (g1 < H.shape[0]) & (g2 >= 0) & (g2 < H.shape[1])
    H[g1[okh], g2[okh]] = True
    hu = H.ravel()
    nuevo = np.where(okc & ~hu, sub + (perf - sub) * w, sub)
    Y[a0:a1, b0:b1] = np.round(nuevo).reshape(zz.shape).astype(Y.dtype)
    nucleo = (okc & (dd <= 1.6) & ~hu).reshape(zz.shape)
    SURF[a0:a1, b0:b1][nucleo] = SUP['sendero']
    if log:
        print(f'  sendero de la torre: {len(camino)} bloques, de Y={t[0]:.0f} a Y={t[-1]:.0f} '
              f'(pendiente máx. {np.abs(np.diff(t)).max():.2f})', flush=True)
    return len(camino)


# ===================================================================== construir
def construir(datos='salida/mundo_datos', out='salida/mundo/Velkia', regiones=None, procesos=4):
    from . import mundo
    est = json.load(open(os.path.join(datos, 'estructuras.json')))
    Y = np.load(os.path.join(datos, 'Y.npy'), mmap_mode='r')
    # aparición: llano al sur de la Gran Pirámide
    sx, sz = 4300, 4700
    spawn = (sx, int(Y[sz, sx]) + 1, sz)
    mundo.construir(datos, out, nombre='Velkia', spawn=spawn, procesos=procesos, regiones=regiones)
    return out


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'preparar'
    if cmd == 'preparar':
        print(json.dumps(preparar(), indent=1, ensure_ascii=False, default=float))
    elif cmd == 'construir':
        reg = None
        if len(sys.argv) > 2:
            reg = [tuple(int(v) for v in r.split(',')) for r in sys.argv[2:]]
        construir(regiones=reg)
