"""v2: mundo con el relieve, los ríos y los biomas del lienzo aprobado.

  python3 -m velkia.modelado_v2                       # -> salida/etapa1_v2.npz (sin Fuertes, Jardines con relieve,
                                                      #    volcán sin cono interior ni coladas)
  python3 -c "from velkia.etapa4 import preparar; preparar('salida/etapa1_v2.npz', 'salida/v2_base', fluidos=False)"
  python3 -m velkia.etapa_v2                          # -> salida/v2_datos (Y, WL, FL, SURF, SDEP, BIO, decor...)
  python3 -c "from velkia import mundo; mundo.construir('salida/v2_datos', 'salida/mundo_v2/Velkia')"

Orden: canal del volcán -> domos, dunas y agujas de la mura -> mar -> lagos y charcas -> ríos (con
valles) -> lava -> sellado -> biomas y materiales (biomas_v1) -> palmeras.
"""
import json
import os
import shutil
import sys
import time

import numpy as np
from scipy import ndimage as ndi

from . import biomas_v1, relieve_v2 as RV, rios_v2
from .etapa4 import sellar, fugas
from .layout import N, SEA
from .materials import SUP
from .zonas_v1 import Z, zonas_v1


def huellas(estructuras):
    """Columnas ocupadas por las construcciones (algún bloque que no sea vacío)."""
    from .schem import Schematic
    m = np.zeros((N, N), bool)
    for e in estructuras:
        s = Schematic.load(e['archivo'])
        vacio = np.array([p.split('[')[0] in ('minecraft:structure_void',) for p in s.palette])
        lleno = (~vacio[s.blocks]).any(axis=0)
        ox, _, oz = e['offset']
        zz, xx = np.nonzero(lleno)
        zz, xx = zz + oz, xx + ox
        ok = (zz >= 0) & (zz < N) & (xx >= 0) & (xx < N)
        m[zz[ok], xx[ok]] = True
    return m


def preparar_v2(base='salida/v2_base', out='salida/v2_datos', etapa='salida/etapa1_v2.npz'):
    t0 = time.time()
    log = lambda t: print(f'[{time.time() - t0:5.0f} s] {t}', flush=True)
    os.makedirs(out, exist_ok=True)
    d = np.load(etapa)
    h = d['h']
    z, z_mix, z_tierra = zonas_v1(d)
    zb = biomas_v1.zonas_bloque(z_tierra)
    log('zonas')
    Y = np.load(os.path.join(base, 'Y.npy')).astype(np.float32)
    est = json.load(open(os.path.join(base, 'estructuras.json')))
    huella = huellas(est)
    protegido = ndi.binary_dilation(huella, iterations=4)
    FLb = np.load(os.path.join(base, 'FL.npy'), mmap_mode='r')
    rios = rios_v2.trazados(d, z, mar=np.asarray(FLb[4::8, 4::8]) == 1)
    drios = RV.distancia_rios(rios)
    log(f'trazado de {len(rios)} ríos')
    info = {}
    # ------------------------------------------------ relieve
    RV.canal_volcan(Y, d['caldera'], protegido)
    log('canal del volcán')
    nd, alto_dom = RV.domos(Y, zb, z, drios, protegido)
    log(f'domos: {nd}')
    info['domos'] = nd
    info['dunas_amp_max'] = RV.dunas(Y, zb, z, drios, protegido)
    log('dunas')
    info['agujas_mura'] = RV.agujas_mura(Y, zb, z, h, drios, protegido)
    log(f"agujas de la mura: {info['agujas_mura']}")
    np.clip(Y, -60, 505, out=Y)
    # ------------------------------------------------ mar (el canal del volcán ya es mar)
    WL = np.full((N, N), -32768, np.int16)
    FL = np.zeros((N, N), np.uint8)
    bajo = Y < SEA - 0.5
    semilla = bajo & (np.asarray(FLb) == 1)
    mar = ndi.binary_propagation(semilla, mask=bajo)
    Y = np.where(bajo & ~mar & ~huella, np.float32(SEA), Y)
    WL[mar] = SEA
    FL[mar] = 1
    log(f'mar {mar.mean() * 100:.1f} %')
    # ------------------------------------------------ lagos y charcas
    niveles, pozas, il = RV.lagos_v2(Y, WL, FL, d, z, zb, drios, protegido)
    info['lagos'] = il
    log(f'lagos: {il}')
    # ------------------------------------------------ ríos
    permitir, ir = rios_v2.tallar(Y, WL, FL, mar, huella, rios, nivel_lagos=niveles, log=log)
    info['rios'] = ir
    # ------------------------------------------------ lava
    pl, nb, nc = RV.lava_volcan(Y, WL, FL, d, z, mar, protegido)
    permitir |= pl
    info['lava'] = {'bocas': nb, 'caidas': nc}
    log(f'lava: {nb} bocas, {nc} caídas')
    # ------------------------------------------------ sellado
    permitir |= huella
    nsub = sellar(Y, WL, FL, permitir)
    log(f'sellado ({nsub} en la última pasada)')
    Yi = np.round(Y).astype(np.int16)
    del Y
    WL = np.where(FL > 0, np.maximum(WL, Yi + 1), WL).astype(np.int16)
    # ------------------------------------------------ biomas y materiales
    SURF, SDEP, BIO = biomas_v1.superficies_v1(Yi, WL, FL, zb, log=log)
    SURF[alto_dom & (FL == 0)] = SUP['roca']                          # los domos son de roca
    SURFb = np.load(os.path.join(base, 'SURF.npy'), mmap_mode='r')
    SURF = np.where(np.asarray(SURFb) == SUP['sendero'], SUP['sendero'], SURF)
    # ------------------------------------------------ palmeras
    agua = (FL == 1) & ~mar
    bloques, npal = RV.palmeras(Yi, FL, zb == Z['salar'], agua)
    info['palmeras'] = npal
    log(f'palmeras: {npal}')
    # ------------------------------------------------ guardar
    for nm, a in (('Y', Yi), ('WL', WL), ('FL', FL), ('SURF', SURF), ('SDEP', SDEP), ('BIO', BIO), ('ZONA', zb)):
        np.save(os.path.join(out, nm + '.npy'), a)
    g = np.load(os.path.join(base, 'geologia.npz'))
    prov, zref, thick = biomas_v1.provincia_v1(g['prov'], g['zref'], g['thick'], z_tierra)
    np.savez_compressed(os.path.join(out, 'geologia.npz'), prov=prov, zref=zref, thick=thick)
    json.dump(biomas_v1.BIOMAS, open(os.path.join(out, 'biomas.json'), 'w'))
    json.dump(biomas_v1.torre_v1(est, os.path.join(out, 'estructuras')),
              open(os.path.join(out, 'estructuras.json'), 'w'), indent=1, ensure_ascii=False)
    if bloques:
        nombres = sorted({b[3] for b in bloques})
        idx = {k: i for i, k in enumerate(nombres)}
        arr = np.array([(x, y, z_, idx[b]) for x, y, z_, b in bloques], np.int32)
        np.savez_compressed(os.path.join(out, 'decor.npz'), xyzb=arr, nombres=np.array(nombres))
    info['fugas'] = int(fugas(Yi, WL, FL, permitir).sum())
    info['mar_pct'] = float(mar.mean() * 100)
    json.dump(info, open(os.path.join(out, 'info.json'), 'w'), indent=1, ensure_ascii=False, default=float)
    log(f"guardado en {out}; fugas {info['fugas']}")
    return info


if __name__ == '__main__':
    preparar_v2(*sys.argv[1:])
