"""Validación de cierre de etapa: vistas en perspectiva a altura de jugador y vistas lejanas.

Cada vista se comprueba antes de renderizar (perspectiva.encuadrar): si la cámara queda metida en
el terreno, mira contra una ladera o no ve su objetivo, se mueve a la mejor posición cercana.
La etiqueta de cada imagen indica la posición final y si la cámara se movió.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .layout import N, SEA, poi_blocks
from .perspectiva import OJO, VISION, distancias, encuadrar, orientar, render, suelo, vision
from .render import relief_image

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_N = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# desde: (poi, dx, dz) desplazamiento en bloques desde un punto de interés, (x, z) absoluto o
#        ('mirador', poi, radio): punto más alto a menos de `radio` bloques del poi que ve el objetivo
# rumbo en grados (0 = norte, 90 = este) u objetivo (poi) hacia el que mirar
# inclinacion en grados (None = hacia el objetivo); y = Y absoluta de las vistas lejanas
VISTAS = [
    dict(titulo='Desierto central hacia la Cordillera (jugador)', desde=('gran_piramide', 0, 900),
         rumbo=0.0, inclinacion=1.0),
    dict(titulo='Borde del cañón mirando Vieja Velkia (jugador)',
         desde=('mirador', 'gran_canon_vieja_velkia', 700), objetivo='gran_canon_vieja_velkia', inclinacion=None),
    dict(titulo='Dentro de los Jardines (jugador)', desde=('jardines_de_velkia', 250, 250),
         rumbo=315.0, inclinacion=2.0),
    dict(titulo='Cumbre de la Cordillera hacia el sur (jugador)', desde=('mirador', 'cordillera_nevada', 900),
         objetivo='gran_piramide', inclinacion=None),
    dict(titulo='Lejana: desde el mar al sureste', desde=(7900, 7900), rumbo=315.0, inclinacion=-6.0, y=220.0),
    dict(titulo='Lejana: sobre la región volcánica hacia el noreste', desde=('region_volcanica', -600, 600),
         rumbo=45.0, inclinacion=-10.0, y=330.0),
]


def _mirador(Y, poi, radio, objetivo, W=960, H=540):
    """Mirador a menos de `radio` bloques del poi: entre los puntos más altos con línea de visión libre
    al objetivo, el de vista más abierta (perder altura penaliza)."""
    n = Y.shape[0]
    dx = N / n
    bx, bz = poi_blocks(poi)
    i0, j0 = int(bz / dx), int(bx / dx)
    r = int(radio / dx)
    ii, jj = np.mgrid[-r:r + 1:2, -r:r + 1:2]
    ii, jj = (ii + i0).ravel(), (jj + j0).ravel()
    m = ((ii - i0) ** 2 + (jj - j0) ** 2 <= r * r) & (ii >= 2) & (jj >= 2) & (ii < n - 2) & (jj < n - 2)
    ii, jj = ii[m], jj[m]
    orden = np.argsort(-Y[ii, jj])[:400]
    ii, jj = ii[orden], jj[orden]
    cams = np.stack([(jj + 0.5) * dx, np.maximum(Y[ii, jj], SEA) + OJO, (ii + 0.5) * dx], 1)
    if objetivo is not None:
        libre = vision(Y, cams, objetivo) >= VISION
        if libre.any():
            cams = cams[libre]
            ori = np.array([orientar(*c, objetivo) for c in cams])
            apertura = np.minimum(distancias(Y, cams, ori[:, 0], ori[:, 1], W=W, H=H), 1500.0).mean(axis=(1, 2))
            k = int(np.argmax(apertura / 1500.0 - (cams[:, 1].max() - cams[:, 1]) / 200.0))
            return float(cams[k, 0]), float(cams[k, 2])
    return float(cams[0, 0]), float(cams[0, 2])


def camaras(Y, W=960, H=540):
    """Cámaras comprobadas de cada vista: lista de (vista, Camara)."""
    out = []
    for v in VISTAS:
        objetivo = None
        if v.get('objetivo'):
            tx, tz = poi_blocks(v['objetivo'])
            objetivo = (tx, suelo(Y, tx, tz) + OJO, tz)
        desde = v['desde']
        if desde[0] == 'mirador':
            x, z = _mirador(Y, desde[1], desde[2], objetivo, W, H)
        elif isinstance(desde[0], str):
            bx, bz = poi_blocks(desde[0])
            x, z = bx + desde[1], bz + desde[2]
        else:
            x, z = desde
        cam = encuadrar(Y, x, z, rumbo=v.get('rumbo'), inclinacion=v.get('inclinacion'), objetivo=objetivo,
                        y_abs=v.get('y'), W=W, H=H)
        out.append((v, cam))
    return out


def _etiqueta(cam):
    med = 'sin impacto' if cam.mediana >= 8999 else f'{cam.mediana:.0f} bl'
    txt = (f'x={cam.x:.0f} z={cam.z:.0f} Y={cam.y:.0f} · rumbo {cam.rumbo:.0f}° · incl. {cam.inclinacion:.0f}° · '
           f'mediana central {med}')
    if cam.movida:
        x0, z0, y0 = cam.origen
        txt += f' · cámara movida {cam.desplazamiento:.0f} bl desde x={x0:.0f} z={z0:.0f} Y={y0:.0f} ({cam.motivo})'
    else:
        txt += ' · cámara en su posición' + (f' ({cam.motivo})' if cam.motivo else '')
    if cam.tapada:
        txt += ' · AVISO: sigue tapada'
    return txt


def _envolver(d, txt, f, ancho):
    lineas, actual = [], ''
    for pal in txt.split(' '):
        prueba = f'{actual} {pal}'.strip()
        if actual and d.textlength(prueba, font=f) > ancho:
            lineas.append(actual)
            actual = pal
        else:
            actual = prueba
    return lineas + [actual]


def generar(Y, ocean, out_dir, prefijo='v1', W=960, H=540):
    os.makedirs(out_dir, exist_ok=True)
    n = Y.shape[0]
    dx = N / n
    tex = np.asarray(relief_image(Y, dx, water=ocean)).astype(np.float32)
    f1 = ImageFont.truetype(FONT, 18)
    f2 = ImageFont.truetype(FONT_N, 14)
    paths = []
    for k, (v, cam) in enumerate(camaras(Y, W, H)):
        im = render(Y, tex, cam, W, H, niebla=4000.0 if v.get('y') is not None else 2500.0)
        d = ImageDraw.Draw(im)
        lineas = _envolver(d, _etiqueta(cam), f2, W - 16)
        d.rectangle([0, 0, W, 30 + 18 * len(lineas)], fill=(0, 0, 0))
        d.text((8, 4), v['titulo'], fill=(255, 255, 255), font=f1)
        for i, ln in enumerate(lineas):
            d.text((8, 28 + 18 * i), ln, fill=(255, 210, 120) if cam.movida else (210, 210, 210), font=f2)
        p = os.path.join(out_dir, f'{prefijo}_vista_{k + 1}.png')
        im.save(p)
        paths.append(p)
    # mosaico
    mos = Image.new('RGB', (2 * W, (len(paths) + 1) // 2 * H))
    for k, p in enumerate(paths):
        mos.paste(Image.open(p), ((k % 2) * W, (k // 2) * H))
    pm = os.path.join(out_dir, f'{prefijo}_vistas_perspectiva.png')
    mos.save(pm)
    return pm, paths
