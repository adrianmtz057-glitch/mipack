"""Validación de cierre de etapa: vistas en perspectiva a altura de jugador y vistas lejanas."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .layout import N, SEA, poi_blocks
from .perspectiva import vista
from .render import relief_image

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# (título, x, z, rumbo, inclinación, sobre_suelo, altura): altura = ojo sobre el suelo o Y absoluta
# rumbo None = mirar hacia el punto 'objetivo'; 'mirador' = punto más alto en un radio dado
VISTAS = [
    ('Desierto central hacia la Cordillera (jugador)', 'gran_piramide', (0, 900), 0, 1.0, True, 1.62),
    ('Borde del cañón mirando Vieja Velkia (jugador)', ('mirador', 'gran_canon_vieja_velkia', 700),
     'gran_canon_vieja_velkia', None, -6.0, True, 1.62),
    ('Dentro de los Jardines (jugador)', 'jardines_de_velkia', (250, 250), 315, 3.0, True, 1.62),
    ('Cumbre de la Cordillera hacia el sur (jugador)', ('mirador', 'cordillera_nevada', 900),
     'gran_piramide', None, -4.0, True, 1.62),
    ('Lejana: desde el mar al sureste', None, (7900, 7900), 315, -6.0, False, 220.0),
    ('Lejana: sobre la región volcánica hacia el noreste', 'region_volcanica', (-600, 600), 45, -10.0, False, 330.0),
]


def generar(Y, ocean, out_dir, prefijo='v1', W=960, H=540):
    os.makedirs(out_dir, exist_ok=True)
    n = Y.shape[0]
    dx = N / n
    tex = np.asarray(relief_image(Y, dx, water=ocean)).astype(np.float32)
    paths = []
    for k, (titulo, poi, off, rumbo, incl, suelo, alt) in enumerate(VISTAS):
        if isinstance(poi, tuple) and poi[0] == 'mirador':
            _, anchor, rad = poi
            bx, bz = poi_blocks(anchor)
            i0, j0 = int(bz / dx), int(bx / dx)
            r = int(rad / dx)
            win = Y[max(0, i0 - r):i0 + r, max(0, j0 - r):j0 + r]
            ii, jj = np.unravel_index(np.argmax(win), win.shape)
            x = (max(0, j0 - r) + jj + 0.5) * dx
            z = (max(0, i0 - r) + ii + 0.5) * dx
            tx, tz = poi_blocks(off)
            rumbo = float(np.degrees(np.arctan2(tx - x, -(tz - z))) % 360)
        elif poi is None:
            x, z = off
        else:
            bx, bz = poi_blocks(poi)
            x, z = bx + off[0], bz + off[1]
        if suelo:
            im, y = vista(Y, tex, x, z, rumbo, inclinacion=incl, altura_ojo=alt, W=W, H=H)
        else:
            im, y = vista(Y, tex, x, z, rumbo, inclinacion=incl, y_abs=alt, W=W, H=H, niebla=4000.0)
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(FONT, 18)
        txt = f'{titulo}  ·  x={x:.0f} z={z:.0f} Y={y:.0f} rumbo {rumbo:.0f}°'
        d.rectangle([0, 0, W, 28], fill=(0, 0, 0))
        d.text((8, 4), txt, fill=(255, 255, 255), font=f)
        p = os.path.join(out_dir, f'{prefijo}_vista_{k + 1}.png')
        im.save(p)
        paths.append(p)
    # mosaico
    mos = Image.new('RGB', (2 * W, 3 * H))
    for k, p in enumerate(paths):
        mos.paste(Image.open(p), ((k % 2) * W, (k // 2) * H))
    pm = os.path.join(out_dir, f'{prefijo}_vistas_perspectiva.png')
    mos.save(pm)
    return pm, paths
