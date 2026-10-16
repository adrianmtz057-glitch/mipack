"""Validación de la etapa 4 (mundo jugable): vistas en perspectiva y comprobación de las regiones.

  python3 -m velkia.validar4 vistas   -> revision/v4_*.png desde los mapas de bloque (2 bloques/celda),
                                         con los materiales de superficie, agua, lava y construcciones
  python3 -m velkia.validar4 regiones -> relee chunks de los .mca escritos y compara el bloque
                                         superior de cada columna con lo que se quiso escribir
"""
import json
import os
import sys

import numpy as np

from .layout import N, SEA
from .materials import SUP

DATOS = 'salida/mundo_datos'
MUNDO = 'salida/mundo/Velkia'

COLOR_SUP = {
    SUP['roca']: (128, 124, 120), SUP['pasto']: (96, 150, 64), SUP['arena']: (219, 205, 160),
    SUP['arena_roja']: (190, 110, 60), SUP['grava']: (140, 135, 130), SUP['nieve']: (245, 248, 252),
    SUP['hielo']: (170, 200, 240), SUP['tierra_gruesa']: (125, 90, 62), SUP['podzol']: (95, 70, 40),
    SUP['barro']: (70, 62, 60), SUP['sal']: (236, 236, 232), SUP['arena_negra']: (40, 40, 44),
    SUP['ceniza']: (110, 108, 108), SUP['musgo']: (90, 120, 50), SUP['arcilla']: (160, 165, 180),
    SUP['corrompido']: (52, 40, 60), SUP['terracota']: (160, 90, 60), SUP['pradera']: (110, 170, 70),
}


def _color_bloque(nombre):
    n = nombre.split('[')[0].replace('minecraft:', '')
    tabla = [('gold', (230, 190, 60)), ('sandstone', (220, 205, 150)), ('sand', (219, 205, 160)),
             ('terracotta', (165, 100, 70)), ('brick', (150, 80, 60)), ('stone', (130, 130, 130)),
             ('deepslate', (80, 80, 85)), ('blackstone', (45, 40, 45)), ('basalt', (70, 70, 75)),
             ('log', (100, 75, 45)), ('planks', (160, 125, 80)), ('wood', (110, 85, 55)),
             ('leaves', (60, 120, 45)), ('grass', (96, 150, 64)), ('water', (50, 110, 215)),
             ('glass', (190, 220, 230)), ('wool', (210, 210, 210)), ('mud', (120, 90, 70)),
             ('copper', (190, 120, 90)), ('quartz', (235, 230, 225)), ('obsidian', (30, 20, 40)),
             ('lava', (235, 85, 20)), ('dirt', (120, 85, 60)), ('moss', (90, 120, 50))]
    for k, c in tabla:
        if k in n:
            return c
    return (175, 165, 150)


def superficie_con_construcciones(paso=2):
    """Cota y color de la superficie (terreno, fluidos y construcciones) a 'paso' bloques/celda."""
    Y = np.load(os.path.join(DATOS, 'Y.npy'), mmap_mode='r')
    WL = np.load(os.path.join(DATOS, 'WL.npy'), mmap_mode='r')
    FL = np.load(os.path.join(DATOS, 'FL.npy'), mmap_mode='r')
    SU = np.load(os.path.join(DATOS, 'SURF.npy'), mmap_mode='r')
    sl = (slice(paso // 2, None, paso), slice(paso // 2, None, paso))
    y = np.asarray(Y[sl], np.float32)
    fl = np.asarray(FL[sl])
    wl = np.asarray(WL[sl], np.float32)
    su = np.asarray(SU[sl])
    lut = np.zeros((256, 3), np.float32)
    for k, c in COLOR_SUP.items():
        lut[k] = c
    col = lut[su]
    agua = fl == 1
    lava = fl == 2
    ys = np.where(fl > 0, np.maximum(y, wl), y)
    prof = np.clip((wl - y) / 10.0, 0, 1)
    col[agua] = (np.array([60, 125, 215]) * (1 - 0.4 * prof[agua, None]))
    col[lava] = (235, 85, 20)
    tipo = np.where(agua, 1, np.where(lava, 4, 0)).astype(np.uint8)
    # construcciones: bloque superior no vacío de cada columna
    from .schem import Schematic
    for e in json.load(open(os.path.join(DATOS, 'estructuras.json'))):
        s = Schematic.load(e['archivo'])
        ox, oy, oz = e['offset']
        vacio = np.array([p.split('[')[0] in ('minecraft:air', 'minecraft:structure_void', 'minecraft:cave_air')
                          for p in s.palette])
        lleno = ~vacio[s.blocks]                                   # [y, z, x]
        hay = lleno.any(axis=0)
        top = lleno.shape[0] - 1 - np.argmax(lleno[::-1], axis=0)
        z0 = (paso // 2 - oz) % paso
        x0 = (paso // 2 - ox) % paso
        hz, hx = hay[z0::paso, x0::paso], top[z0::paso, x0::paso]
        zz, xx = np.nonzero(hz)
        gz, gx = (oz + z0 + zz * paso) // paso, (ox + x0 + xx * paso) // paso
        ok = (gz >= 0) & (gz < y.shape[0]) & (gx >= 0) & (gx < y.shape[1])
        zz, xx, gz, gx = zz[ok], xx[ok], gz[ok], gx[ok]
        tyv = hx[zz, xx]
        bid = s.blocks[tyv, z0 + zz * paso, x0 + xx * paso]
        pc = np.array([_color_bloque(p) for p in s.palette], np.float32)
        yy = (oy + tyv).astype(np.float32)
        mas = yy >= ys[gz, gx] - 0.5
        ys[gz[mas], gx[mas]] = yy[mas]
        col[gz[mas], gx[mas]] = pc[bid[mas]]
        tipo[gz[mas], gx[mas]] = 6
    return ys, col, tipo


def vistas(prefijo='v4', W=800, H=450):
    from .render import hillshade
    from .validacion import generar
    from .hacer_revision import vistas_extra
    ys, col, tipo = superficie_con_construcciones(2)
    dx = N / ys.shape[0]
    hs = hillshade(ys, dx)
    tex = np.clip(col * (0.45 + 0.75 * hs[..., None]), 0, 255)
    mar = (tipo == 1) & (ys <= SEA + 0.5)
    d = np.load('salida/etapa1.npz')
    return generar(ys, mar, 'revision', prefijo=prefijo, W=W, H=H, tex=tex, extra=vistas_extra(d, ys, dx))


# --------------------------------------------------------------------- relectura de regiones
def _unpack(data, bits, n):
    per = 64 // bits
    a = data.view(np.uint64)
    idx = np.arange(n)
    w = a[idx // per]
    return ((w >> ((idx % per) * bits).astype(np.uint64)) & np.uint64((1 << bits) - 1)).astype(np.int64)


def comprobar_regiones(muestras=40, seed=3):
    """Compara el bloque superior no-aire de columnas al azar del mundo escrito con lo esperado
    (terreno, fluidos y construcciones)."""
    from . import nbt
    rng = np.random.default_rng(seed)
    Y = np.load(os.path.join(DATOS, 'Y.npy'), mmap_mode='r')
    WL = np.load(os.path.join(DATOS, 'WL.npy'), mmap_mode='r')
    FL = np.load(os.path.join(DATOS, 'FL.npy'), mmap_mode='r')
    est = json.load(open(os.path.join(DATOS, 'estructuras.json')))
    malos, total = 0, 0
    for _ in range(muestras):
        x, z = int(rng.integers(600, N - 600)), int(rng.integers(600, N - 600))
        if any(e['offset'][0] <= x < e['offset'][0] + e['size'][0] and e['offset'][2] <= z < e['offset'][2] + e['size'][2]
               for e in est):
            continue
        cx, cz = x // 16, z // 16
        ruta = os.path.join(MUNDO, 'region', f'r.{cx >> 5}.{cz >> 5}.mca')
        col = columna(ruta, cx, cz, x & 15, z & 15)
        if col is None:
            continue
        top = max(k for k, b in col.items() if b != 'minecraft:air')
        esperado = int(WL[z, x]) if FL[z, x] > 0 else int(Y[z, x])
        total += 1
        if top != esperado:
            malos += 1
            print(f'  ({x},{z}): escrito Y={top} {col[top]}, esperado {esperado}')
    print(f'columnas comprobadas: {total}, distintas: {malos}')
    return total, malos


def columna(ruta, cx, cz, lx, lz):
    """{Y: bloque} de una columna del chunk escrito."""
    import zlib
    from . import nbt
    with open(ruta, 'rb') as fh:
        cab = fh.read(4096)
        i = 4 * ((cx & 31) + (cz & 31) * 32)
        off = int.from_bytes(cab[i:i + 3], 'big')
        if off == 0:
            return None
        fh.seek(off * 4096)
        ln = int.from_bytes(fh.read(4), 'big')
        fh.read(1)
        raw = fh.read(ln - 1)
    _, t = nbt.loads(zlib.decompress(raw))
    out = {}
    for sec in t['sections']:
        sy = int(sec['Y'])
        bs = sec['block_states']
        pal = [p['Name'] for p in bs['palette']]
        if 'data' in bs and len(pal) > 1:
            bits = max(4, int(np.ceil(np.log2(len(pal)))))
            idx = _unpack(np.asarray(bs['data']), bits, 4096).reshape(16, 16, 16)
        else:
            idx = np.zeros((16, 16, 16), np.int64)
        for yy in range(16):
            out[sy * 16 + yy] = pal[int(idx[yy, lz, lx])]
    return out


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'vistas'
    if cmd == 'vistas':
        print(vistas())
    else:
        comprobar_regiones()
