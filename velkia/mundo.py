"""Construcción del mundo Minecraft a partir de los mapas finales.

Entradas (memmaps de N x N en un directorio):
  Y.npy     int16  cota del bloque sólido superior de cada columna
  WL.npy    int16  cota de la superficie del agua/lava (-32768 = sin fluido)
  FL.npy    uint8  0 nada, 1 agua, 2 lava
  SURF.npy  uint8  código de superficie (materials.SUP)
  SDEP.npy  uint8  espesor de suelo/sedimento bajo la superficie (bloques)
  BIO.npy   uint8  índice de bioma (lista en biomas.json)
y la geología a baja resolución (prov, zref, thick) para elegir la roca por estrato.
Las construcciones se pegan encima (structure_void = no se pega; el aire sí, como
//paste -o -m !structure_void), con sus cofres y barriles (block entities).
"""
import json
import os
import time
from multiprocessing import Pool

import numpy as np

from . import anvil, nbt
from .geology import ZMIN, ZRES
from .layout import N, SEA
from .materials import MaterialTables, PERIODICA_MUNDO as PERIODICA

MIN_Y = anvil.MIN_Y
H = anvil.HEIGHT


class Fuente:
    """Acceso perezoso a los mapas (memmap) y a las construcciones colocadas."""

    def __init__(self, d):
        self.d = d
        self.Y = np.load(os.path.join(d, 'Y.npy'), mmap_mode='r')
        self.WL = np.load(os.path.join(d, 'WL.npy'), mmap_mode='r')
        self.FL = np.load(os.path.join(d, 'FL.npy'), mmap_mode='r')
        self.SURF = np.load(os.path.join(d, 'SURF.npy'), mmap_mode='r')
        self.SDEP = np.load(os.path.join(d, 'SDEP.npy'), mmap_mode='r')
        self.BIO = np.load(os.path.join(d, 'BIO.npy'), mmap_mode='r')
        g = np.load(os.path.join(d, 'geologia.npz'))
        self.prov = g['prov']
        self.zref = g['zref']
        self.thick = g['thick']
        self.biomas = json.load(open(os.path.join(d, 'biomas.json')))
        self.gn = self.prov.shape[0]
        est = os.path.join(d, 'estructuras.json')
        self.estructuras = json.load(open(est)) if os.path.exists(est) else []
        dec = os.path.join(d, 'decor.npz')       # bloques sueltos (palmeras): x, y, z, índice de nombre
        if os.path.exists(dec):
            dc = np.load(dec)
            self.decor, self.decor_nombres = dc['xyzb'], [str(k) for k in dc['nombres']]
        else:
            self.decor, self.decor_nombres = np.zeros((0, 4), np.int32), []


_CACHE = {}
# ids de entidad de bloque que en 1.20.1 se llaman distinto que el bloque
BE_ID = {'minecraft:suspicious_sand': 'minecraft:brushable_block',
         'minecraft:suspicious_gravel': 'minecraft:brushable_block'}


def _schem(path):
    s = _CACHE.get(path)
    if s is None:
        from .schem import Schematic
        s = Schematic.load(path)
        _CACHE[path] = s
    return s


def _geo_region(f, x0, z0, w):
    """Geología interpolada (vecino más cercano) para una ventana de w x w bloques."""
    sc = f.gn / N
    zi = np.clip(((np.arange(z0, z0 + w) + 0.5) * sc).astype(int), 0, f.gn - 1)
    xi = np.clip(((np.arange(x0, x0 + w) + 0.5) * sc).astype(int), 0, f.gn - 1)
    return f.prov[zi][:, xi], f.zref[zi][:, xi], f.thick[zi][:, xi]


def _columnas(f, mt, pal, cx, cz, geo):
    """Bloques del terreno de un chunk: array (H, 16, 16) [y, z, x]."""
    x0, z0 = cx * 16, cz * 16
    Y = np.asarray(f.Y[z0:z0 + 16, x0:x0 + 16], np.int32)
    WL = np.asarray(f.WL[z0:z0 + 16, x0:x0 + 16], np.int32)
    FL = np.asarray(f.FL[z0:z0 + 16, x0:x0 + 16])
    SU = np.asarray(f.SURF[z0:z0 + 16, x0:x0 + 16])
    SD = np.asarray(f.SDEP[z0:z0 + 16, x0:x0 + 16], np.int32)
    prov, zref, thick = geo
    ys = (np.arange(H) + MIN_Y)[:, None, None]
    # roca por estrato
    zeta = (ys - SEA - zref[None]) / thick[None]          # la geología usa cotas sobre el mar
    k = ((zeta - ZMIN) / ZRES).astype(np.int64)
    nt = mt.rock.shape[1]
    per = PERIODICA[prov][None].repeat(H, 0)
    k = np.where(per, k % nt, np.clip(k, 0, nt - 1))
    pv = np.broadcast_to(prov[None], k.shape)
    blocks = mt.rock[pv, k].astype(np.uint16)
    # pizarra profunda bajo Y=0 (con transición irregular) y lecho de roca abajo
    deep = pal.get('minecraft:deepslate[axis=y]')
    blocks = np.where(ys < -2 + ((x0 * 7 + z0 * 13) % 5), deep, blocks)
    # suelo / sedimento y superficie
    top = mt.sup_top_arr[SU]
    sub = mt.sup_sub_arr[SU]
    roca_sup = SU == 0
    sdep = np.where(roca_sup, 0, np.maximum(SD, 1))
    in_sub = (ys > (Y - sdep)[None]) & (ys < Y[None])
    blocks = np.where(in_sub & ~roca_sup[None], sub[None], blocks)
    is_top = (ys == Y[None]) & ~roca_sup[None]
    blocks = np.where(is_top, top[None], blocks)
    air = 0
    blocks = np.where(ys > Y[None], air, blocks)
    # fluidos
    water = pal.get('minecraft:water[level=0]')
    lava = pal.get('minecraft:lava[level=0]')
    fl = (ys > Y[None]) & (ys <= WL[None]) & (FL[None] > 0)
    blocks = np.where(fl & (FL[None] == 1), water, blocks)
    blocks = np.where(fl & (FL[None] == 2), lava, blocks)
    # lecho de roca
    bed = pal.get('minecraft:bedrock')
    blocks[0] = bed
    rnd = ((np.arange(16)[:, None] * 31 + np.arange(16)[None] * 17 + x0 + z0) % 3)
    blocks[1] = np.where(rnd == 0, bed, blocks[1])
    return blocks


def _pegar(blocks, pal, cx, cz, est, bes):
    """Pega las partes de construcciones que caen en el chunk."""
    x0, z0 = cx * 16, cz * 16
    for e in est:
        ox, oy, oz = e['offset']
        w, h, l = e['size']
        if ox >= x0 + 16 or ox + w <= x0 or oz >= z0 + 16 or oz + l <= z0:
            continue
        s = _schem(e['archivo'])
        if 'rot' in e and e['rot']:
            s = s.rotated_ccw(e['rot'])
        # índices de la paleta del schematic -> paleta global
        key = id(s)
        lut = e.get('_lut')
        if lut is None:
            lut = np.array([pal.get(p) for p in s.palette], np.int64)
            void = np.array([p == 'minecraft:structure_void' for p in s.palette])
            e['_lut'] = lut
            e['_void'] = void
        void = e['_void']
        sx0, sx1 = max(x0, ox), min(x0 + 16, ox + w)
        sz0, sz1 = max(z0, oz), min(z0 + 16, oz + l)
        sub = s.blocks[:, sz0 - oz:sz1 - oz, sx0 - ox:sx1 - ox]
        ylo = oy - MIN_Y
        yhi = ylo + h
        if yhi <= 0 or ylo >= H:
            continue
        a0, a1 = max(0, -ylo), min(h, H - ylo)
        sub = sub[a0:a1]
        tgt = blocks[ylo + a0:ylo + a1, sz0 - z0:sz1 - z0, sx0 - x0:sx1 - x0]
        m = ~void[sub]
        tgt[m] = lut[sub[m]]
        for be in s.block_entities:
            bx, by, bz = be['Pos']
            X, Yb, Z = ox + bx, oy + by, oz + bz
            if x0 <= X < x0 + 16 and z0 <= Z < z0 + 16 and MIN_Y <= Yb < MIN_Y + H:
                t = {k: v for k, v in be.items() if k not in ('Pos', 'Id')}
                t['id'] = BE_ID.get(str(be.get('Id', 'minecraft:chest')), str(be.get('Id', 'minecraft:chest')))
                t['x'] = nbt.TInt(X)
                t['y'] = nbt.TInt(Yb)
                t['z'] = nbt.TInt(Z)
                t['keepPacked'] = nbt.TByte(0)
                bes.append(t)


def _region(args):
    d, out, rx, rz = args
    f = Fuente(d)
    pal = anvil.Palette()
    mt = MaterialTables(pal)
    bnames = f.biomas
    chunks = {}
    t0 = time.time()
    geo_all = _geo_region(f, rx * 512, rz * 512, 512)
    dec = f.decor[(f.decor[:, 0] // 512 == rx) & (f.decor[:, 2] // 512 == rz)]
    dec_ids = np.array([pal.get(k) for k in f.decor_nombres], np.int64)
    for lz in range(32):
        for lx in range(32):
            cx, cz = rx * 32 + lx, rz * 32 + lz
            if cx * 16 >= N or cz * 16 >= N:
                continue
            g = tuple(a[lz * 16:lz * 16 + 16, lx * 16:lx * 16 + 16] for a in geo_all)
            blocks = _columnas(f, mt, pal, cx, cz, g)
            bes = []
            if f.estructuras:
                _pegar(blocks, pal, cx, cz, f.estructuras, bes)
            dch = dec[(dec[:, 0] // 16 == cx) & (dec[:, 2] // 16 == cz)]
            if len(dch):
                yy = dch[:, 1] - MIN_Y
                ok = (yy >= 0) & (yy < H)
                dch, yy = dch[ok], yy[ok]
                bz, bx = dch[:, 2] - cz * 16, dch[:, 0] - cx * 16
                libre = blocks[yy, bz, bx] == 0                      # solo en aire
                blocks[yy[libre], bz[libre], bx[libre]] = dec_ids[dch[libre, 3]]
            bio2 = np.asarray(f.BIO[cz * 16 + 2:cz * 16 + 16:4, cx * 16 + 2:cx * 16 + 16:4])
            bio = np.broadcast_to(bio2[None], (H // 4, 4, 4)).astype(np.uint8)
            chunks[(lx, lz)] = anvil.build_chunk(cx, cz, blocks, pal, bio, bnames, bes)
    anvil.write_region(os.path.join(out, 'region', f'r.{rx}.{rz}.mca'), chunks)
    return rx, rz, time.time() - t0


def construir(d, out, nombre='Velkia', spawn=(4096, 120, 4096), procesos=4, regiones=None):
    os.makedirs(os.path.join(out, 'region'), exist_ok=True)
    nr = N // 512
    todas = [(d, out, rx, rz) for rz in range(nr) for rx in range(nr)]
    if regiones is not None:
        todas = [a for a in todas if (a[2], a[3]) in regiones]
    t0 = time.time()
    with Pool(procesos) as p:
        for i, (rx, rz, dt) in enumerate(p.imap_unordered(_region, todas)):
            if i % 16 == 0:
                print(f'  región {i + 1}/{len(todas)} ({rx},{rz}) {dt:.0f} s  total {time.time() - t0:.0f} s', flush=True)
    anvil.write_level_dat(out, nombre, spawn, N, (N / 2, N / 2))
    anvil.write_datapack(out)
    print(f'Mundo escrito en {out} ({time.time() - t0:.0f} s)', flush=True)
