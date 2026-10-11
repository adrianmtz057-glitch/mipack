"""Construcciones: reubicación según el mapa de referencia, recorte de losas y asiento.

Cada sitio agrupa uno o más .schem (Sponge v2).  Las transformaciones son rígidas:
rotación de 90° (opcional, alrededor de un pivote) + traslación entera en XZ, y un
desplazamiento vertical dy que se decide al final según el terreno generado.

Decisiones (ver README):
  * El complejo Pirámide + Esfinge + Thza se mueve como un bloque y se rota 90° antihorario:
    así la Esfinge queda al suroeste/sur de la pirámide y Thza al sureste, como en el mapa 2,
    sin romper las piezas que encajan entre sí (Thza contiene una esquina de la explanada).
  * La aldea fantasma "norte" (casas colmena) pasa a ser la aldea fantasma del oeste del
    mapa 2; la aldea "sur" (casas de barro junto al río) queda al noreste del salar.
"""
import glob
import json
import os

import numpy as np
from scipy import ndimage as ndi

from .layout import poi_blocks
from .schem import Schematic, parse_state

ORIG = os.path.join(os.path.dirname(__file__), '..', 'referencia', 'construcciones_originales')

NATURAL = {
    'minecraft:stone', 'minecraft:dirt', 'minecraft:grass_block', 'minecraft:sand', 'minecraft:red_sand',
    'minecraft:gravel', 'minecraft:coarse_dirt', 'minecraft:terracotta', 'minecraft:orange_terracotta',
    'minecraft:brown_terracotta', 'minecraft:yellow_terracotta', 'minecraft:light_gray_terracotta',
    'minecraft:red_terracotta', 'minecraft:white_terracotta', 'minecraft:sandstone', 'minecraft:clay',
    'minecraft:granite', 'minecraft:snow', 'minecraft:packed_mud', 'minecraft:calcite',
    'minecraft:blackstone', 'minecraft:gray_terracotta', 'minecraft:cyan_terracotta',
    'minecraft:black_terracotta', 'minecraft:light_blue_terracotta', 'minecraft:red_sandstone',
    'minecraft:water', 'minecraft:netherrack', 'minecraft:magma_block', 'minecraft:dead_bush',
    'minecraft:fern', 'minecraft:moss_carpet', 'minecraft:moss_block', 'minecraft:mud',
}


def _center_of(parts):
    x0 = min(p.offset[0] for p in parts)
    z0 = min(p.offset[2] for p in parts)
    x1 = max(p.offset[0] + p.size[0] for p in parts) - 1
    z1 = max(p.offset[2] + p.size[2] for p in parts) - 1
    return (x0 + x1) // 2, (z0 + z1) // 2


# --------------------------------------------------------------------- sitios
# 'ancla': punto del mapa 2 (POI) al que se lleva el 'centro' del sitio, o coordenadas.
SITIOS = {
    'complejo_piramide': {
        'carpetas': ['piramide', 'explanada_esfinge', 'thza'],
        'rotar_ccw': 1,
        'pivote': (4000, 3900),          # centro original de la pirámide
        'destino_pivote': (4306, 3452),  # ajuste por mínimos cuadrados a pirámide/esfinge/Thza del mapa 2
        'recortar': [],                  # explanadas y ciudad son arquitectura: se conservan
    },
    'jardines_colgantes': {
        'carpetas': ['jardines_colgantes'], 'rotar_ccw': 0,
        'destino_centro': 'jardines_de_velkia', 'recortar': ['losa'],
    },
    'vieja_velkia': {
        'carpetas': ['vieja_velkia'], 'rotar_ccw': 0,
        'destino_centro': 'gran_canon_vieja_velkia', 'recortar': ['entorno'],
    },
    'aldea_fantasma_oeste': {
        'carpetas': ['aldea_fantasma_norte'], 'rotar_ccw': 0,
        'destino_centro': 'aldea_fantasma_oeste', 'recortar': ['entorno'],
    },
    'aldea_fantasma_sur': {
        'carpetas': ['aldea_fantasma_sur'], 'rotar_ccw': 0,
        'destino_centro': 'aldea_fantasma_sur', 'recortar': ['entorno'],
    },
    'torre_llama_eterna': {
        'carpetas': ['torre_llama_eterna'], 'rotar_ccw': 0,
        'destino_centro': 'torre_llama_eterna', 'recortar': ['sendero'],
    },
}


class Sitio:
    def __init__(self, nombre, cfg):
        self.nombre = nombre
        self.cfg = cfg
        parts = []
        for carpeta in cfg['carpetas']:
            idx = json.load(open(os.path.join(ORIG, carpeta, 'indice.json')))
            for a in idx['archivos']:
                parts.append(Schematic.load(os.path.join(ORIG, carpeta, a['archivo'] + '.schem')))
        self.parts_orig = parts
        self.transform()

    # ------------------------------------------------------------ transformación XZ
    def transform(self):
        cfg = self.cfg
        rot = cfg.get('rotar_ccw', 0) % 4
        if 'pivote' in cfg:
            px, pz = cfg['pivote']
            tx, tz = cfg['destino_pivote']
        else:
            px, pz = _center_of(self.parts_orig)
            tx, tz = poi_blocks(cfg['destino_centro'])
            tx, tz = int(round(tx)), int(round(tz))
        out = []
        for p in self.parts_orig:
            w, h, l = p.size
            x0, y0, z0 = p.offset
            q = p.rotated_ccw(rot) if rot else p
            # esquina mínima tras rotar (antihorario: x' = px + (z - pz), z' = pz - (x - px))
            if rot == 1:
                nx0 = px + (z0 - pz)
                nz0 = pz - (x0 + w - 1 - px)
            elif rot == 0:
                nx0, nz0 = x0, z0
            else:
                raise NotImplementedError
            q.offset = np.array([nx0 + (tx - px), y0, nz0 + (tz - pz)], np.int64)
            out.append(q)
        self.parts = out
        self.dy = 0

    def bbox(self):
        x0 = min(p.offset[0] for p in self.parts)
        z0 = min(p.offset[2] for p in self.parts)
        x1 = max(p.offset[0] + p.size[0] for p in self.parts)
        z1 = max(p.offset[2] + p.size[2] for p in self.parts)
        y0 = min(p.offset[1] for p in self.parts)
        y1 = max(p.offset[1] + p.size[1] for p in self.parts)
        return x0, y0, z0, x1, y1, z1

    # ------------------------------------------------------------ mapas 2D del sitio
    def maps(self):
        """Devuelve dict con arrays 2D (z, x) sobre la caja del sitio:
        foot (no vacío), built (bloque no natural), water, top (Y del bloque sólido más alto),
        ground (Y del techo de lo natural), bottom (Y más bajo no vacío)."""
        x0, y0, z0, x1, y1, z1 = self.bbox()
        W, L = x1 - x0, z1 - z0
        m = {k: np.zeros((L, W), bool) for k in ('foot', 'built', 'water')}
        m['top'] = np.full((L, W), -999, np.int32)
        m['ground'] = np.full((L, W), -999, np.int32)
        m['bottom'] = np.full((L, W), 9999, np.int32)
        m['water_y'] = np.full((L, W), -999, np.int32)
        for p in self.parts:
            base = np.array([s.split('[')[0] for s in p.palette], dtype=object)
            void = (base == 'minecraft:structure_void')[p.blocks]
            air = (base == 'minecraft:air')[p.blocks]
            nat = np.isin(base, list(NATURAL))[p.blocks]
            wat = (base == 'minecraft:water')[p.blocks] | np.array(
                ['waterlogged=true' in s for s in p.palette])[p.blocks] & False
            solid = ~void & ~air
            h = p.size[1]
            ys = (np.arange(h) + p.offset[1] + self.dy)[:, None, None]
            ox, oz = p.offset[0] - x0, p.offset[2] - z0
            sl = (slice(oz, oz + p.size[2]), slice(ox, ox + p.size[0]))
            m['foot'][sl] |= (~void).any(0)
            m['built'][sl] |= (solid & ~nat).any(0)
            m['water'][sl] |= wat.any(0)
            m['top'][sl] = np.maximum(m['top'][sl], np.where(solid, ys, -999).max(0))
            m['ground'][sl] = np.maximum(m['ground'][sl], np.where(nat & ~wat, ys, -999).max(0))
            m['bottom'][sl] = np.minimum(m['bottom'][sl], np.where(~void, ys, 9999).min(0))
            m['water_y'][sl] = np.maximum(m['water_y'][sl], np.where(wat, ys, -999).max(0))
        m['x0'], m['z0'] = x0, z0
        return m


def cargar_sitios(nombres=None):
    return {k: Sitio(k, v) for k, v in SITIOS.items() if nombres is None or k in nombres}


def canal_vieja_velkia(sitio):
    """Polilínea (x, z) del río que atraviesa Vieja Velkia, de oeste a sureste."""
    m = sitio.maps()
    w = m['water']
    lab, n = ndi.label(w, structure=np.ones((3, 3)))
    sizes = ndi.sum(w, lab, range(1, n + 1))
    main = lab == (np.argmax(sizes) + 1)
    zz, xx = np.nonzero(main)
    order = np.argsort(xx)
    xs = xx[order]
    # centro por columnas de x (el canal va de oeste a este)
    pts = []
    for x in range(xs.min(), xs.max() + 1, 8):
        sel = (xx >= x) & (xx < x + 8)
        if sel.any():
            pts.append((m['x0'] + x + 4, m['z0'] + zz[sel].mean()))
    return np.array(pts), int(m['water_y'][main].max())


# --------------------------------------------------------------------- recorte
def recortar(sitio, modo, margen=4):
    """Convierte en structure_void el terreno viejo que trae el schematic, para que el relieve
    nuevo rodee la construcción (no una losa plana ni el terreno del mapa anterior).

    modo 'losa'    : columnas solo con bloques naturales fuera del casco de lo construido.
    modo 'entorno' : igual (anillo de terreno natural alrededor de ciudades y aldeas).
    modo 'sendero' : la torre: se conserva solo el núcleo (radio 22) y el sendero viejo se quita.
    Devuelve el número de columnas recortadas.
    """
    if modo not in ('losa', 'entorno', 'sendero'):
        return 0
    m = sitio.maps()
    foot, built = m['foot'], m['built']
    if modo == 'sendero':
        top = m['top']
        ci = np.unravel_index(np.argmax(np.where(foot, top, -999)), top.shape)
        zz, xx = np.meshgrid(np.arange(foot.shape[0]), np.arange(foot.shape[1]), indexing='ij')
        conservar = np.hypot(zz - ci[0], xx - ci[1]) <= 22
    else:
        # casco de lo construido: cierre morfológico + relleno de huecos (calles incluidas)
        casco = ndi.binary_closing(built, structure=np.ones((3, 3)), iterations=12)
        casco = ndi.binary_fill_holes(casco)
        conservar = ndi.binary_dilation(casco, iterations=margen)
    quitar = foot & ~conservar
    total = 0
    for p in sitio.parts:
        x0, z0 = m['x0'], m['z0']
        ox, oz = p.offset[0] - x0, p.offset[2] - z0
        w, h, l = p.size
        q = quitar[oz:oz + l, ox:ox + w]
        if not q.any():
            continue
        vi = p.index_of('minecraft:structure_void')
        if vi < 0:
            p.palette.append('minecraft:structure_void')
            vi = len(p.palette) - 1
        p.blocks[:, q] = vi
        p.block_entities = [be for be in p.block_entities if not q[be['Pos'][2], be['Pos'][0]]]
        total += int(q.sum())
    return total
