"""Schematics Sponge v2 (.schem de WorldEdit): lectura, rotación, traslado y escritura."""
import os
import re

import numpy as np
from numba import njit

from . import nbt


@njit(cache=True)
def _decode_varints(buf, n_out):
    out = np.empty(n_out, np.int32)
    j = 0
    v = 0
    s = 0
    for i in range(buf.size):
        b = buf[i]
        v |= (b & 0x7F) << s
        if b & 0x80:
            s += 7
        else:
            out[j] = v
            j += 1
            v = 0
            s = 0
            if j == n_out:
                break
    return out


def _encode_varints(arr):
    arr = np.asarray(arr, dtype=np.int64).ravel()
    out = bytearray()
    if arr.max(initial=0) < 128:
        return arr.astype(np.uint8).tobytes()
    for v in arr.tolist():
        while True:
            b = v & 0x7F
            v >>= 7
            if v:
                out.append(b | 0x80)
            else:
                out.append(b)
                break
    return bytes(out)


class Schematic:
    """blocks[y, z, x] -> índice en palette (lista de strings de estado de bloque)."""

    def __init__(self, blocks, palette, offset, block_entities=None, entities=None,
                 data_version=3465, name='', biomes=None):
        self.blocks = blocks
        self.palette = list(palette)
        self.offset = np.array(offset, dtype=np.int64)  # esquina mínima absoluta (x, y, z)
        self.block_entities = block_entities or []       # dicts con 'Pos' relativo [x,y,z]
        self.entities = entities or []
        self.data_version = data_version
        self.name = name

    @property
    def size(self):  # (W, H, L) = (x, y, z)
        h, l, w = self.blocks.shape
        return w, h, l

    def index_of(self, name):
        try:
            return self.palette.index(name)
        except ValueError:
            return -1

    def mask_of(self, names):
        ids = [i for i, p in enumerate(self.palette) if p in names or p.split('[')[0] in names]
        return np.isin(self.blocks, ids)

    # ------------------------------------------------------------ E/S
    @classmethod
    def load(cls, path):
        _, root = nbt.load(path)
        if 'Schematic' in root and 'Width' not in root:
            root = root['Schematic']
        ver = int(root.get('Version', 2))
        if ver != 2:
            raise ValueError(f'{path}: solo se soporta Sponge v2 (encontrado v{ver})')
        w, h, l = int(root['Width']), int(root['Height']), int(root['Length'])
        pal = root['Palette']
        palette = [None] * (max(int(v) for v in pal.values()) + 1)
        for k, v in pal.items():
            palette[int(v)] = k
        palette = [p if p is not None else 'minecraft:air' for p in palette]
        raw = np.asarray(root['BlockData']).view(np.uint8)
        blocks = _decode_varints(raw, w * h * l).reshape(h, l, w).astype(np.uint16)
        bes = []
        for be in root.get('BlockEntities', []):
            be = dict(be)
            be['Pos'] = [int(v) for v in be['Pos']]
            bes.append(be)
        ents = [dict(e) for e in root.get('Entities', [])]
        off = [int(v) for v in root.get('Offset', [0, 0, 0])]
        meta = root.get('Metadata', {})
        if 'WEOffsetX' in meta and any(int(meta[k]) for k in ('WEOffsetX', 'WEOffsetY', 'WEOffsetZ')):
            raise ValueError(f'{path}: WEOffset distinto de cero no soportado')
        return cls(blocks, palette, off, bes, ents, int(root.get('DataVersion', 3465)),
                   os.path.splitext(os.path.basename(path))[0])

    def save(self, path):
        w, h, l = self.size
        # compactar paleta
        used = np.unique(self.blocks)
        remap = np.zeros(len(self.palette), np.int64)
        remap[used] = np.arange(used.size)
        blocks = remap[self.blocks]
        pal = {self.palette[u]: nbt.TInt(i) for i, u in enumerate(used.tolist())}
        root = {
            'Version': nbt.TInt(2),
            'DataVersion': nbt.TInt(self.data_version),
            'Width': nbt.TShort(w), 'Height': nbt.TShort(h), 'Length': nbt.TShort(l),
            'Offset': np.array(self.offset, dtype=np.int32),
            'Metadata': {'WEOffsetX': nbt.TInt(0), 'WEOffsetY': nbt.TInt(0), 'WEOffsetZ': nbt.TInt(0),
                         'Name': self.name, 'Author': 'Velkia'},
            'PaletteMax': nbt.TInt(len(pal)),
            'Palette': pal,
            'BlockData': np.frombuffer(_encode_varints(blocks), dtype=np.int8),
            'BlockEntities': nbt.NBTList(nbt.TAG_COMPOUND, [
                {**be, 'Pos': np.array(be['Pos'], dtype=np.int32)} for be in self.block_entities]),
        }
        if self.entities:
            root['Entities'] = nbt.NBTList(nbt.TAG_COMPOUND, self.entities)
        nbt.save(path, root, name='Schematic')

    # ------------------------------------------------------------ transformaciones
    def rotated_ccw(self, turns=1):
        """Rota 90° antihorario visto desde arriba (norte arriba): este -> norte."""
        s = self
        for _ in range(turns % 4):
            s = s._rot_ccw_once()
        return s

    def _rot_ccw_once(self):
        w, h, l = self.size
        # nuevo[y, z', x'] con x' = z, z' = (w-1) - x
        nb = np.transpose(self.blocks, (0, 2, 1))[:, ::-1, :].copy()
        pal = [rotate_state_ccw(p) for p in self.palette]
        bes = []
        for be in self.block_entities:
            x, y, z = be['Pos']
            be = dict(be)
            be['Pos'] = [z, y, (w - 1) - x]
            bes.append(be)
        if self.entities:
            raise NotImplementedError('rotación de entidades no implementada')
        return Schematic(nb, pal, self.offset.copy(), bes, [], self.data_version, self.name)


# ---------------------------------------------------------------- estados de bloque
_DIR_CCW = {'north': 'west', 'west': 'south', 'south': 'east', 'east': 'north',
            'up': 'up', 'down': 'down'}
_RAIL_CANON = {frozenset(('north', 'south')): 'north_south', frozenset(('east', 'west')): 'east_west',
               frozenset(('north', 'east')): 'north_east', frozenset(('north', 'west')): 'north_west',
               frozenset(('south', 'east')): 'south_east', frozenset(('south', 'west')): 'south_west'}


def parse_state(s):
    m = re.match(r'^([^\[]+)(?:\[(.*)\])?$', s)
    name, props = m.group(1), m.group(2)
    d = {}
    if props:
        for kv in props.split(','):
            k, v = kv.split('=')
            d[k] = v
    return name, d


def format_state(name, d):
    if not d:
        return name
    return name + '[' + ','.join(f'{k}={v}' for k, v in d.items()) + ']'


def rotate_state_ccw(s):
    name, p = parse_state(s)
    if not p:
        return s
    q = dict(p)
    if 'facing' in p and p['facing'] in _DIR_CCW:
        q['facing'] = _DIR_CCW[p['facing']]
    if 'axis' in p:
        q['axis'] = {'x': 'z', 'z': 'x', 'y': 'y'}[p['axis']]
    if 'rotation' in p:
        q['rotation'] = str((int(p['rotation']) - 4) % 16)
    sides = [d for d in ('north', 'east', 'south', 'west') if d in p]
    if sides:
        for d in ('north', 'east', 'south', 'west'):
            q.pop(d, None)
        rot = {}
        for d in sides:
            rot[_DIR_CCW[d]] = p[d]
        q.update(rot)
    if 'shape' in p and ('rail' in name):
        sh = p['shape']
        if sh.startswith('ascending_'):
            q['shape'] = 'ascending_' + _DIR_CCW[sh[len('ascending_'):]]
        else:
            a, b = sh.split('_')
            q['shape'] = _RAIL_CANON[frozenset((_DIR_CCW[a], _DIR_CCW[b]))]
    if 'orientation' in p:
        a, b = p['orientation'].split('_')
        q['orientation'] = _DIR_CCW[a] + '_' + _DIR_CCW[b]
    return format_state(name, dict(sorted(q.items())))
