"""Diseño del mapa: zonas digitalizadas del mapa de referencia y campos físicos de entrada.

Todo se define en píxeles del mapa de referencia (referencia/mapa_referencia_biomas.webp,
1254x1254) y se convierte a bloques con una escala casi isótropa (~6,7 bloques/píxel).
El mapa final mide 8192 x 8192 bloques, x hacia el este y z hacia el sur.
"""
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from .noise import spectral_noise, resize, blur

N = 8192                    # lado del mapa en bloques
SEA = 62                    # cota de la superficie del mar (bloques de agua hasta Y=62)
Y_MIN, Y_MAX = -64, 511     # rango vertical (datapack: min_y=-64, height=576)
REF = os.path.join(os.path.dirname(__file__), '..', 'referencia', 'mapa_referencia_biomas.webp')

# --------------------------------------------------------------------- escala
SX, SZ = 6.75, 6.60         # bloques por píxel de referencia
OX, OZ = 520.0, 330.0       # bloque correspondiente al píxel (11, 35)


def px2b(px, py):
    return OX + (px - 11.0) * SX, OZ + (py - 35.0) * SZ


def b2px(x, z):
    return (x - OX) / SX + 11.0, (z - OZ) / SZ + 35.0


# --------------------------------------------------------------------- zonas (píxeles de referencia)
ZONAS = {
    'cordillera': [(150, 300), (165, 235), (225, 185), (300, 125), (380, 72), (470, 42), (560, 32),
                   (640, 50), (720, 80), (775, 105), (790, 200), (785, 300), (730, 330), (650, 340),
                   (560, 350), (470, 352), (400, 335), (360, 300), (300, 268), (240, 262), (190, 285)],
    'corrompidas': [(762, 118), (840, 98), (930, 108), (1000, 165), (1042, 240), (1032, 330), (985, 392),
                    (900, 412), (820, 402), (772, 352), (752, 262), (752, 182)],
    'oeste': [(18, 430), (55, 305), (145, 232), (168, 282), (158, 400), (175, 505), (265, 515), (385, 485),
              (425, 560), (412, 700), (425, 790), (330, 805), (90, 805), (28, 705), (14, 560)],
    'volcanica': [(55, 800), (150, 782), (300, 782), (402, 805), (425, 905), (405, 1000), (425, 1100),
                  (385, 1152), (250, 1165), (160, 1125), (98, 1045), (58, 945)],
    'salar': [(352, 812), (430, 795), (520, 805), (585, 850), (602, 930), (590, 1010), (545, 1072),
              (460, 1085), (390, 1060), (350, 990), (338, 900)],
    'canones': [(702, 625), (780, 592), (880, 602), (960, 645), (1050, 655), (1072, 800), (1082, 950),
                (1062, 1100), (982, 1172), (850, 1185), (722, 1165), (662, 1062), (682, 900), (698, 780)],
    'este': [(925, 382), (1000, 392), (1052, 432), (1065, 560), (1055, 655), (962, 645), (905, 602),
             (912, 480)],
    'dunas': [(620, 392), (760, 372), (905, 382), (930, 452), (920, 600), (820, 602), (705, 600),
              (642, 522)],
}
JARDINES_ELIPSE = (275, 385, 112, 118)      # cx, cy, rx, ry (px)

# cresta principal de la cordillera (px) y altura relativa
CRESTA = [(170, 255, 0.45), (240, 205, 0.6), (330, 160, 0.8), (450, 115, 0.95), (565, 85, 1.0),
          (650, 110, 0.95), (720, 140, 0.85), (775, 165, 0.7)]

# --------------------------------------------------------------------- puntos de interés (px de referencia)
POIS = {
    'gran_piramide': (597, 490), 'esfinge': (521, 575), 'thza': (640, 600),
    'cuarto_de_bashi': (632, 720), 'torre_llama_eterna': (1020, 580),
    'gran_canon_vieja_velkia': (920, 865), 'fuertes_en_ruinas': (785, 1045),
    'aldea_fantasma_oeste': (140, 535), 'aldea_fantasma_sur': (595, 945),
    'jardines_de_velkia': (275, 385), 'crakatos': (897, 325), 'tierras_corrompidas': (878, 258),
    'region_volcanica': (248, 920), 'playa_arena_negra': (200, 1080), 'bioma_de_sales': (470, 940),
    'mar_de_dunas': (840, 500), 'cordillera_nevada': (565, 120),
}


def poi_blocks(name):
    return px2b(*POIS[name])


# --------------------------------------------------------------------- rasterización
def _poly_mask(points, n):
    s = n / N
    img = Image.new('L', (n, n), 0)
    pts = [(px2b(x, y)[0] * s, px2b(x, y)[1] * s) for x, y in points]
    ImageDraw.Draw(img).polygon(pts, fill=255)
    return np.asarray(img, np.float32) / 255.0


def _ellipse_mask(cx, cy, rx, ry, n):
    s = n / N
    x0, z0 = px2b(cx - rx, cy - ry)
    x1, z1 = px2b(cx + rx, cy + ry)
    img = Image.new('L', (n, n), 0)
    ImageDraw.Draw(img).ellipse([x0 * s, z0 * s, x1 * s, z1 * s], fill=255)
    return np.asarray(img, np.float32) / 255.0


def island_mask(n):
    """Máscara de tierra a partir del mapa de referencia (generalizada)."""
    im = np.asarray(Image.open(REF).convert('RGB')).astype(np.float32)
    imb = np.stack([ndi.gaussian_filter(im[..., c], 2.0) for c in range(3)], -1)
    r, g, b = imb[..., 0], imb[..., 1], imb[..., 2]
    water = (b > r + 25) & (b > g - 5)
    land = ~water
    land[:, 1075:] = False
    land = ndi.binary_opening(land, iterations=2)
    lab, nl = ndi.label(land)
    sizes = ndi.sum(land, lab, range(1, nl + 1))
    land = lab == (np.argmax(sizes) + 1)
    land = ndi.binary_fill_holes(land)
    # a bloques
    H, W = land.shape
    zz, xx = np.meshgrid((np.arange(n) + 0.5) * N / n, (np.arange(n) + 0.5) * N / n, indexing='ij')
    px, py = b2px(xx, zz)
    m = ndi.map_coordinates(land.astype(np.float32), [py, px], order=1, mode='constant', cval=0.0)
    return m


class Layout:
    """Campos de diseño a resolución n x n (celda = N/n bloques)."""

    def __init__(self, n=1024, seed=7):
        self.n = n
        self.dx = N / n
        self.seed = seed
        cells_per_px = SX / self.dx
        land = island_mask(n)
        # generalizar la costa (~45 bloques) y deformar con ruido para romper la forma del dibujo
        land = blur(land, 45.0 / self.dx)
        wu = spectral_noise((n, n), 3.0, seed + 1) * (60.0 / self.dx)
        wv = spectral_noise((n, n), 3.0, seed + 2) * (60.0 / self.dx)
        from .noise import warp
        land = warp(land, wu, wv)
        self.land_soft = np.clip(land, 0, 1)
        self.land = self.land_soft > 0.5
        # distancia a la costa (bloques), positiva en tierra, negativa en mar
        din = ndi.distance_transform_edt(self.land) * self.dx
        dout = ndi.distance_transform_edt(~self.land) * self.dx
        self.dist_coast = np.where(self.land, din, -dout).astype(np.float32)

        sig = 120.0 / self.dx   # transición entre zonas ~ 120 bloques
        z = {}
        for k, pts in ZONAS.items():
            m = _poly_mask(pts, n)
            z[k] = m
        z['jardines'] = _ellipse_mask(*JARDINES_ELIPSE, n)
        # deformar fronteras
        wu2 = spectral_noise((n, n), 2.6, seed + 3) * (90.0 / self.dx)
        wv2 = spectral_noise((n, n), 2.6, seed + 4) * (90.0 / self.dx)
        for k in z:
            z[k] = np.clip(blur(warp(z[k], wu2, wv2), sig), 0, 1)
        # prioridades: jardines dentro de cordillera/oeste; resto
        z['oeste'] = z['oeste'] * (1 - z['jardines'])
        z['cordillera'] = z['cordillera'] * (1 - z['jardines']) * (1 - z['corrompidas'])
        z['dunas'] = z['dunas'] * (1 - z['este']) * (1 - z['canones'])
        z['salar'] = z['salar'] * (1 - z['volcanica'])
        tot = sum(z.values())
        z['desierto'] = np.clip(1.0 - tot, 0, 1)
        tot = sum(z.values()) + 1e-6
        for k in z:
            z[k] = (z[k] / tot).astype(np.float32)
        self.zonas = z
        self.zone_names = list(z.keys())
        self.zone_id = np.argmax(np.stack([z[k] for k in self.zone_names]), 0).astype(np.uint8)

        # cresta de la cordillera: distancia a la polilínea de la cresta
        self.cresta = self._crest_field()

    # ------------------------------------------------------------------
    def coords(self):
        c = (np.arange(self.n) + 0.5) * self.dx
        return np.meshgrid(c, c, indexing='ij')  # zz, xx

    def _crest_field(self):
        zz, xx = self.coords()
        best = np.full(zz.shape, 1e9, np.float32)
        hval = np.zeros(zz.shape, np.float32)
        pts = [(px2b(x, y), h) for x, y, h in CRESTA]
        for (a, ha), (b, hb) in zip(pts[:-1], pts[1:]):
            ax, az = a
            bx, bz = b
            vx, vz = bx - ax, bz - az
            L2 = vx * vx + vz * vz
            t = np.clip(((xx - ax) * vx + (zz - az) * vz) / L2, 0, 1)
            px_ = ax + t * vx
            pz_ = az + t * vz
            d = np.hypot(xx - px_, zz - pz_)
            h = ha + t * (hb - ha)
            upd = d < best
            best = np.where(upd, d, best)
            hval = np.where(upd, h, hval)
        return best, hval
