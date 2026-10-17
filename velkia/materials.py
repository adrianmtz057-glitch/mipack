"""Materiales: bloque de roca por provincia y estrato, y códigos de superficie.

La roca de cada columna se elige con la MISMA columna estratigráfica que usó la erosión
(geology.py), de modo que las capas duras que forman cornisas son también las que se ven
como bandas de color en las paredes del cañón.
"""
import numpy as np

from .geology import (GRANITO, METAMORFICO, ESTRATOS, BASALTO, SEDIMENTOS, EVAPORITAS, CORROMPIDO,
                      COLUMNA_MESETA, NT, ZMIN, ZRES, PERIODICA, build_tables)

# --------------------------------------------------------------- roca por estrato
# Para cada provincia: lista de "materiales" (índice de material de la tabla M) -> lista de
# bloques con pesos (variación de 1-2 bloques dentro de la capa).
MESETA_BLOQUES = {
    'basamento': [('minecraft:stone', 6), ('minecraft:granite', 2), ('minecraft:andesite', 2),
                  ('minecraft:diorite', 1)],
    'lutita_roja': [('minecraft:red_terracotta', 5), ('minecraft:terracotta', 2), ('minecraft:brown_terracotta', 1)],
    'arenisca_roja': [('minecraft:red_sandstone', 4), ('minecraft:smooth_red_sandstone', 2),
                      ('minecraft:orange_terracotta', 1)],
    'limolita': [('minecraft:orange_terracotta', 4), ('minecraft:terracotta', 2), ('minecraft:red_terracotta', 1)],
    'caliza': [('minecraft:white_terracotta', 3), ('minecraft:calcite', 2), ('minecraft:light_gray_terracotta', 1)],
    'lutita_gris': [('minecraft:light_gray_terracotta', 4), ('minecraft:gray_terracotta', 1), ('minecraft:terracotta', 1)],
    'arenisca_blanca': [('minecraft:smooth_sandstone', 3), ('minecraft:white_terracotta', 2), ('minecraft:sandstone', 2)],
    'arenisca_amarilla': [('minecraft:yellow_terracotta', 4), ('minecraft:sandstone', 2)],
    'arenisca_crema': [('minecraft:sandstone', 4), ('minecraft:smooth_sandstone', 2), ('minecraft:cut_sandstone', 1)],
    'lutita_parda': [('minecraft:brown_terracotta', 4), ('minecraft:terracotta', 2), ('minecraft:orange_terracotta', 1)],
}

PROV_BLOQUES = {
    GRANITO: {0: [('minecraft:granite', 5), ('minecraft:stone', 3), ('minecraft:diorite', 1)],
              1: [('minecraft:granite', 5), ('minecraft:stone', 3), ('minecraft:diorite', 1)]},
    METAMORFICO: {0: [('minecraft:stone', 4), ('minecraft:tuff', 2), ('minecraft:andesite', 2)],
                  1: [('minecraft:stone', 3), ('minecraft:andesite', 3), ('minecraft:deepslate', 2),
                      ('minecraft:cobbled_deepslate', 1)]},
    BASALTO: {0: [('minecraft:tuff', 4), ('minecraft:blackstone', 2), ('minecraft:magma_block', 0)],
              1: [('minecraft:basalt[axis=y]', 4), ('minecraft:blackstone', 2), ('minecraft:smooth_basalt', 2),
                  ('minecraft:polished_basalt[axis=y]', 1)]},
    SEDIMENTOS: {0: [('minecraft:sandstone', 4), ('minecraft:sand', 1), ('minecraft:smooth_sandstone', 1)],
                 1: [('minecraft:smooth_sandstone', 3), ('minecraft:cut_sandstone', 1), ('minecraft:calcite', 1)]},
    EVAPORITAS: {0: [('minecraft:calcite', 3), ('minecraft:white_terracotta', 2), ('minecraft:diorite', 1)]},
    CORROMPIDO: {0: [('minecraft:deepslate', 4), ('minecraft:blackstone', 3), ('minecraft:tuff', 2),
                     ('minecraft:purple_terracotta', 1), ('minecraft:crying_obsidian', 0)]},
}

# --------------------------------------------------------------- códigos de superficie
SUP = {
    'roca': 0, 'pasto': 1, 'arena': 2, 'arena_roja': 3, 'grava': 4, 'nieve': 5, 'hielo': 6,
    'tierra_gruesa': 7, 'podzol': 8, 'barro': 9, 'sal': 10, 'arena_negra': 11, 'ceniza': 12,
    'musgo': 13, 'arcilla': 14, 'corrompido': 15, 'terracota': 16, 'pradera': 17, 'sendero': 18,
}
SUP_BLOQUES = {
    1: (['minecraft:grass_block[snowy=false]'], ['minecraft:dirt'], 3),
    17: (['minecraft:grass_block[snowy=false]'], ['minecraft:dirt'], 4),
    2: (['minecraft:sand'], ['minecraft:sand', 'minecraft:sandstone'], 4),
    3: (['minecraft:red_sand'], ['minecraft:red_sand', 'minecraft:red_sandstone'], 3),
    4: (['minecraft:gravel'], ['minecraft:gravel'], 3),
    5: (['minecraft:snow_block'], ['minecraft:snow_block', 'minecraft:packed_ice'], 3),
    6: (['minecraft:packed_ice'], ['minecraft:packed_ice', 'minecraft:blue_ice'], 6),
    7: (['minecraft:coarse_dirt'], ['minecraft:dirt'], 2),
    8: (['minecraft:podzol[snowy=false]'], ['minecraft:dirt'], 3),
    9: (['minecraft:mud'], ['minecraft:mud', 'minecraft:clay'], 3),
    10: (['minecraft:white_concrete_powder'], ['minecraft:calcite', 'minecraft:white_terracotta'], 2),
    11: (['minecraft:black_concrete_powder'], ['minecraft:black_concrete_powder', 'minecraft:tuff'], 3),
    12: (['minecraft:gray_concrete_powder'], ['minecraft:tuff'], 2),
    13: (['minecraft:moss_block'], ['minecraft:dirt'], 2),
    14: (['minecraft:clay'], ['minecraft:clay'], 2),
    15: (['minecraft:blackstone'], ['minecraft:deepslate'], 2),
    16: (['minecraft:terracotta'], ['minecraft:terracotta'], 2),
    18: (['minecraft:smooth_sandstone'], ['minecraft:sandstone'], 2),     # sendero de la torre (bioma de arena)
}

# provincias solo del mundo (la erosión no las usa): bandas horizontales por cota (zref=0, thick=1)
DOMOS, BADLANDS = 7, 8
N_PROV = 9
PERIODICA_MUNDO = np.r_[PERIODICA, True, True]
# (bloque, peso, espesor mínimo, espesor máximo en bloques)
BANDAS = {
    # domos tipo Kata Tjuta: conglomerado de arenisca roja con capas de terracota clara
    DOMOS: [('minecraft:red_sandstone', 5, 3, 8), ('minecraft:smooth_red_sandstone', 2, 2, 5),
            ('minecraft:orange_terracotta', 2, 1, 3), ('minecraft:terracotta', 1, 1, 3),
            ('minecraft:white_terracotta', 1, 1, 2)],
    # montañas de terracota como el bioma vanilla de badlands
    BADLANDS: [('minecraft:terracotta', 4, 2, 6), ('minecraft:orange_terracotta', 4, 2, 6),
               ('minecraft:yellow_terracotta', 2, 1, 3), ('minecraft:white_terracotta', 2, 1, 2),
               ('minecraft:light_gray_terracotta', 2, 1, 3), ('minecraft:red_terracotta', 3, 1, 4),
               ('minecraft:brown_terracotta', 2, 1, 3)],
}


def _bandas(pal, opciones, rng):
    """Fila de la tabla de roca con bandas horizontales de bloques al azar (periódica en NT)."""
    fila = np.zeros(NT, np.uint16)
    w = np.array([o[1] for o in opciones], float)
    w /= w.sum()
    k, prev = 0, -1
    while k < NT:
        c = int(rng.choice(len(opciones), p=w))
        if c == prev:
            continue
        nombre, _, e0, e1 = opciones[c]
        largo = int(rng.integers(e0, e1 + 1) / ZRES)
        fila[k:k + largo] = pal.get(nombre)
        k += largo
        prev = c
    return fila


class MaterialTables:
    """Tablas para el constructor de chunks: material de roca en función de (prov, índice estrato)."""

    def __init__(self, pal, seed=11):
        self.F, self.M = build_tables(seed)
        rng = np.random.default_rng(seed + 100)
        # tabla bloque[prov, k] (k = índice de estrato a 0,25 m) con variación por banda de ~1-2 m
        self.rock = np.zeros((N_PROV, NT), np.uint16)
        band = np.repeat(rng.random(NT // 6 + 1), 6)[:NT]
        for prov in range(7):
            for k0 in range(0, NT, 6):
                k1 = min(NT, k0 + 6)
                m = int(self.M[prov, k0])
                if prov == ESTRATOS:
                    key = COLUMNA_MESETA[min(m, len(COLUMNA_MESETA) - 1)][2]
                    opts = MESETA_BLOQUES[key]
                else:
                    opts = PROV_BLOQUES[prov].get(m, PROV_BLOQUES[prov][0])
                names = [o[0] for o in opts]
                w = np.array([o[1] for o in opts], float)
                w = w / w.sum()
                c = np.searchsorted(np.cumsum(w), band[k0])
                self.rock[prov, k0:k1] = pal.get(names[min(c, len(names) - 1)])
        for prov, opciones in BANDAS.items():
            self.rock[prov] = _bandas(pal, opciones, np.random.default_rng(seed + prov))
        self.sup_top = {}
        self.sup_sub = {}
        self.sup_depth = np.zeros(32, np.int16)
        self.sup_top_arr = np.zeros(32, np.uint16)
        self.sup_sub_arr = np.zeros(32, np.uint16)
        for code, (top, sub, depth) in SUP_BLOQUES.items():
            self.sup_top_arr[code] = pal.get(top[0])
            self.sup_sub_arr[code] = pal.get(sub[0])
            self.sup_depth[code] = depth
