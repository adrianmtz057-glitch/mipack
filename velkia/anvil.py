"""Escritura de mundos Java Edition 1.20.1 (formato Anvil, DataVersion 3465).

* Regiones .mca con chunks en estado "minecraft:full" y luz sin calcular (isLightOn=0):
  el servidor calcula la iluminación al cargar cada chunk por primera vez.
* Altura -64..511 mediante datapack (dimension_type minecraft:overworld, height 576).
* Fuera del mapa: generador plano de océano (el borde del mundo limita el área jugable).
"""
import json
import os
import struct
import time
import zlib

import numpy as np

from . import nbt

DATA_VERSION = 3465
MIN_Y = -64
HEIGHT = 576
MIN_SECTION = MIN_Y // 16
N_SECTIONS = HEIGHT // 16


class Palette:
    """Paleta global de estados de bloque (string -> índice uint16)."""

    def __init__(self):
        self.states = []
        self.index = {}
        self._nbt = []
        self.get('minecraft:air')

    def get(self, state):
        i = self.index.get(state)
        if i is None:
            i = len(self.states)
            self.states.append(state)
            self.index[state] = i
            self._nbt.append(_state_nbt(state))
        return i

    def nbt_of(self, i):
        return self._nbt[i]

    def __len__(self):
        return len(self.states)


def _state_nbt(state):
    if '[' in state:
        name, props = state[:-1].split('[', 1)
        d = {}
        for kv in props.split(','):
            k, v = kv.split('=')
            d[k] = v
        return {'Name': name, 'Properties': d}
    return {'Name': state}


def _pack(indices, bits):
    """Empaqueta índices (sin cruzar longs, formato 1.16+)."""
    per = 64 // bits
    n = indices.size
    nl = (n + per - 1) // per
    pad = nl * per - n
    a = indices.astype(np.uint64)
    if pad:
        a = np.concatenate([a, np.zeros(pad, np.uint64)])
    a = a.reshape(nl, per)
    shifts = (np.arange(per, dtype=np.uint64) * np.uint64(bits))
    packed = np.bitwise_or.reduce(a << shifts[None, :], axis=1)
    return packed.view(np.int64)


def encode_section(blocks16, pal, biome_ids, biome_names):
    """blocks16: (16,16,16) uint16 [y,z,x] índices de la paleta global.
    biome_ids: (4,4,4) [y,z,x] índices en biome_names."""
    flat = blocks16.ravel()
    uniq, inv = np.unique(flat, return_inverse=True)
    bs = {'palette': nbt.NBTList(nbt.TAG_COMPOUND, [pal.nbt_of(int(u)) for u in uniq])}
    if uniq.size > 1:
        bits = max(4, int(np.ceil(np.log2(uniq.size))))
        bs['data'] = _pack(inv, bits)
    bflat = biome_ids.ravel()
    bu, binv = np.unique(bflat, return_inverse=True)
    bio = {'palette': nbt.NBTList(nbt.TAG_STRING, [biome_names[int(u)] for u in bu])}
    if bu.size > 1:
        bits = int(np.ceil(np.log2(bu.size)))
        bio['data'] = _pack(binv, bits)
    return bs, bio


def build_chunk(cx, cz, blocks, pal, biomes, biome_names, block_entities=(), fluid_ticks=()):
    """blocks: (HEIGHT,16,16) uint16 [y,z,x];  biomes: (HEIGHT//4,4,4) uint8 [y,z,x]."""
    sections = []
    for s in range(N_SECTIONS):
        b16 = blocks[s * 16:(s + 1) * 16]
        bi = biomes[s * 4:(s + 1) * 4]
        bs, bio = encode_section(b16, pal, bi, biome_names)
        sections.append({'Y': nbt.TByte(MIN_SECTION + s), 'block_states': bs, 'biomes': bio})
    root = {
        'DataVersion': nbt.TInt(DATA_VERSION),
        'xPos': nbt.TInt(cx), 'zPos': nbt.TInt(cz), 'yPos': nbt.TInt(MIN_SECTION),
        'Status': 'minecraft:full',
        'LastUpdate': nbt.TLong(0), 'InhabitedTime': nbt.TLong(0),
        'sections': nbt.NBTList(nbt.TAG_COMPOUND, sections),
        'block_entities': nbt.NBTList(nbt.TAG_COMPOUND, list(block_entities)),
        'Heightmaps': {},
        'fluid_ticks': nbt.NBTList(nbt.TAG_COMPOUND, list(fluid_ticks)),
        'block_ticks': nbt.NBTList(nbt.TAG_COMPOUND, []),
        'PostProcessing': nbt.NBTList(nbt.TAG_LIST, [nbt.NBTList(nbt.TAG_SHORT, []) for _ in range(N_SECTIONS)]),
        'structures': {'References': {}, 'starts': {}},
        'isLightOn': nbt.TByte(0),
    }
    return zlib.compress(nbt.dumps(root), 6)


def write_region(path, chunks):
    """chunks: dict {(lx, lz): bytes_zlib} con lx, lz en 0..31."""
    header = bytearray(8192)
    body = bytearray()
    sector = 2
    now = int(time.time())
    for (lx, lz), data in sorted(chunks.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        payload = struct.pack('>IB', len(data) + 1, 2) + data
        nsec = (len(payload) + 4095) // 4096
        if nsec > 255:
            raise ValueError(f'chunk demasiado grande ({len(payload)} bytes)')
        payload += b'\x00' * (nsec * 4096 - len(payload))
        idx = lx + lz * 32
        struct.pack_into('>I', header, idx * 4, (sector << 8) | nsec)
        struct.pack_into('>I', header, 4096 + idx * 4, now)
        body += payload
        sector += nsec
    with open(path, 'wb') as f:
        f.write(header)
        f.write(body)


# ------------------------------------------------------------------ level.dat y datapack
def write_level_dat(world_dir, name, spawn, size_blocks, center, seed=20261011):
    flat_layers = [
        {'block': 'minecraft:bedrock', 'height': nbt.TInt(1)},
        {'block': 'minecraft:stone', 'height': nbt.TInt(70)},
        {'block': 'minecraft:sand', 'height': nbt.TInt(3)},
        {'block': 'minecraft:water', 'height': nbt.TInt(53)},
    ]
    data = {
        'DataVersion': nbt.TInt(DATA_VERSION),
        'version': nbt.TInt(19133),
        'Version': {'Id': nbt.TInt(DATA_VERSION), 'Name': '1.20.1', 'Series': 'main',
                    'Snapshot': nbt.TByte(0)},
        'LevelName': name,
        'GameType': nbt.TInt(0),
        'Difficulty': nbt.TByte(2),
        'DifficultyLocked': nbt.TByte(0),
        'hardcore': nbt.TByte(0),
        'allowCommands': nbt.TByte(1),
        'initialized': nbt.TByte(1),
        'SpawnX': nbt.TInt(spawn[0]), 'SpawnY': nbt.TInt(spawn[1]), 'SpawnZ': nbt.TInt(spawn[2]),
        'SpawnAngle': nbt.TFloat(0.0),
        'Time': nbt.TLong(0), 'DayTime': nbt.TLong(6000), 'LastPlayed': nbt.TLong(int(time.time() * 1000)),
        'raining': nbt.TByte(0), 'rainTime': nbt.TInt(120000),
        'thundering': nbt.TByte(0), 'thunderTime': nbt.TInt(180000), 'clearWeatherTime': nbt.TInt(0),
        'WanderingTraderSpawnChance': nbt.TInt(25), 'WanderingTraderSpawnDelay': nbt.TInt(24000),
        'BorderCenterX': nbt.TDouble(center[0]), 'BorderCenterZ': nbt.TDouble(center[1]),
        'BorderSize': nbt.TDouble(size_blocks), 'BorderSizeLerpTarget': nbt.TDouble(size_blocks),
        'BorderSizeLerpTime': nbt.TLong(0), 'BorderSafeZone': nbt.TDouble(5.0),
        'BorderDamagePerBlock': nbt.TDouble(0.2), 'BorderWarningBlocks': nbt.TDouble(5.0),
        'BorderWarningTime': nbt.TDouble(15.0),
        'DataPacks': {'Enabled': nbt.NBTList(nbt.TAG_STRING, ['vanilla', 'file/velkia']),
                      'Disabled': nbt.NBTList(nbt.TAG_STRING, [])},
        'enabled_features': nbt.NBTList(nbt.TAG_STRING, ['minecraft:vanilla']),
        'GameRules': {'doFireTick': 'false', 'doMobSpawning': 'true', 'spawnRadius': '4'},
        'WorldGenSettings': {
            'bonus_chest': nbt.TByte(0), 'generate_features': nbt.TByte(0), 'seed': nbt.TLong(seed),
            'dimensions': {
                'minecraft:overworld': {
                    'type': 'minecraft:overworld',
                    'generator': {'type': 'minecraft:flat', 'settings': {
                        'biome': 'minecraft:deep_ocean', 'features': nbt.TByte(0), 'lakes': nbt.TByte(0),
                        'layers': nbt.NBTList(nbt.TAG_COMPOUND, flat_layers),
                        'structure_overrides': nbt.NBTList(nbt.TAG_STRING, [])}}},
                'minecraft:the_nether': {
                    'type': 'minecraft:the_nether',
                    'generator': {'type': 'minecraft:noise', 'settings': 'minecraft:nether',
                                  'biome_source': {'type': 'minecraft:multi_noise',
                                                   'preset': 'minecraft:nether'}}},
                'minecraft:the_end': {
                    'type': 'minecraft:the_end',
                    'generator': {'type': 'minecraft:noise', 'settings': 'minecraft:end',
                                  'biome_source': {'type': 'minecraft:the_end'}}},
            }},
        'ScheduledEvents': nbt.NBTList(nbt.TAG_COMPOUND, []),
        'ServerBrands': nbt.NBTList(nbt.TAG_STRING, ['vanilla']),
        'WasModded': nbt.TByte(0),
        'CustomBossEvents': {},
    }
    nbt.save(os.path.join(world_dir, 'level.dat'), {'Data': data})


CUSTOM_BIOMES = {
    # nombre: (temperatura, lluvia, cielo, niebla, agua, niebla_agua, pasto, follaje, partícula, prob)
    'salar': (2.0, 0.0, 0xA9C6E8, 0xE8EEF2, 0x9FD8E0, 0x6FB6C4, 0xD8D4B0, 0xC8C4A0, None, 0.0),
    'volcanica': (2.0, 0.0, 0x8E8A88, 0x6E625C, 0x3E5A66, 0x2A3238, 0x6E6A50, 0x5E5A40,
                  'minecraft:white_ash', 0.025),
    'tierras_corrompidas': (0.9, 0.3, 0x6E5A86, 0x4A3A5E, 0x5A3A7A, 0x2A1A3A, 0x5E4A6A, 0x4E3A5A,
                            'minecraft:ash', 0.012),
    'jardines': (0.8, 0.8, 0x78A7FF, 0xC0D8FF, 0x3F76E4, 0x050533, 0x6FBF4A, 0x5FAF3A, None, 0.0),
}


def write_datapack(world_dir):
    root = os.path.join(world_dir, 'datapacks', 'velkia')
    os.makedirs(os.path.join(root, 'data', 'minecraft', 'dimension_type'), exist_ok=True)
    os.makedirs(os.path.join(root, 'data', 'velkia', 'worldgen', 'biome'), exist_ok=True)
    json.dump({'pack': {'pack_format': 15,
                        'description': 'Velkia: altura -64..511 y biomas propios'}},
              open(os.path.join(root, 'pack.mcmeta'), 'w'), indent=2)
    dim = {
        'ultrawarm': False, 'natural': True, 'coordinate_scale': 1.0, 'has_skylight': True,
        'has_ceiling': False, 'ambient_light': 0.0,
        'monster_spawn_light_level': {'type': 'minecraft:uniform',
                                      'value': {'min_inclusive': 0, 'max_inclusive': 7}},
        'monster_spawn_block_light_limit': 0, 'piglin_safe': False, 'bed_works': True,
        'respawn_anchor_works': False, 'has_raids': True,
        'logical_height': HEIGHT, 'min_y': MIN_Y, 'height': HEIGHT,
        'infiniburn': '#minecraft:infiniburn_overworld', 'effects': 'minecraft:overworld',
    }
    json.dump(dim, open(os.path.join(root, 'data', 'minecraft', 'dimension_type', 'overworld.json'), 'w'),
              indent=2)
    for name, (t, d, sky, fog, wat, wfog, grass, fol, part, prob) in CUSTOM_BIOMES.items():
        eff = {'sky_color': sky, 'fog_color': fog, 'water_color': wat, 'water_fog_color': wfog,
               'grass_color': grass, 'foliage_color': fol,
               'mood_sound': {'sound': 'minecraft:ambient.cave', 'tick_delay': 6000,
                              'block_search_extent': 8, 'offset': 2.0}}
        if part:
            eff['particle'] = {'options': {'type': part}, 'probability': prob}
        bio = {'has_precipitation': d > 0, 'temperature': t, 'downfall': d, 'effects': eff,
               'spawners': {}, 'spawn_costs': {}, 'carvers': {}, 'features': []}
        json.dump(bio, open(os.path.join(root, 'data', 'velkia', 'worldgen', 'biome', name + '.json'), 'w'),
                  indent=2)
