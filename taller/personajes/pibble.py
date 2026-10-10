"""
Pibble, el semidios errante, hermano de Moles (de la misma estrella). Se rehace paso a paso con los mismos terminos
que ella: el mismo cuerpo chibi y la misma escala, todo low-poly de caras planas, segun referencias/personajes/pibble.png.

Por ahora solo la cabeza, esculpida como un gato de papel: redonda y mas ancha que alta, de caras triangulares, con
los cachetes en pico a los lados, el hocico con la nariz que sale, las cuencas de los ojos hundidas, la ceja y la
frente redonda; de vacio negro, con los ojos de almendra crema inclinados hacia arriba afuera y el rombo dorado en la
frente.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..textura import hex_a_rgba as hex_
from .moles import faceta

D = 4
NEGRO = ((0.34, "#1C1A1F"), (0.5, "#28252B"), (0.66, "#353138"), (9.0, "#433E47"))   # grises de papel
OJO, OJO_ORILLA = "#EADCBF", "#C8A058"

# la cabeza, redonda como gato de papel (mas ancha que alta), de abajo hacia arriba: (y, medio ancho, medio hondo
# adelante, medio hondo atras, {punto: cuanto sale (+) o se mete (-)}). 16 puntos por anillo: 0 a su derecha (+X),
# 4 el frente, 8 a su izquierda, 12 atras; solo se dan los de la derecha y el medio (los de la izquierda en espejo)
CABEZA = ((11.2, 2.6, 2.6, 2.6, {4: 0.3}),
          (12.2, 4.0, 3.9, 3.6, {4: 0.5, 3: 0.2}),                           # la barbilla
          (13.4, 5.0, 4.5, 4.1, {4: 1.3, 3: 0.6, 0: 0.5, 1: 0.2}),           # el hocico y los cachetes en pico
          (14.6, 5.4, 4.6, 4.3, {4: 1.65, 3: 0.45, 0: 0.6}),                 # la punta de la nariz
          (15.6, 5.3, 4.6, 4.4, {4: 0.75, 3: -0.15, 2: -0.45}),              # el puente y las cuencas de los ojos
          (16.6, 5.15, 4.6, 4.4, {4: 0.3, 3: -0.2, 2: -0.45}),
          (17.6, 4.9, 4.6, 4.3, {4: 0.1, 3: 0.1, 2: 0.1}),                   # la ceja
          (19.0, 4.2, 3.9, 3.8, {}),
          (20.0, 2.9, 2.7, 2.7, {}),
          (20.6, 1.3, 1.2, 1.2, {}))
CORONILLA = (0.0, 20.8, 0.0)
LADOS = 16


def _anillo(y, mx, mzf, mzb, sale):
    sale = {**sale, **{(8 - k) % LADOS: v for k, v in sale.items()}}         # el espejo de cada punto
    pts = []
    for k in range(LADOS):
        a = 2 * math.pi * k / LADOS
        c, s = math.cos(a), math.sin(a)
        mz = mzf if s > 0 else mzb
        e = sale.get(k, 0.0)
        pts.append((mx * c + e * c, y, -mz * s - e * s))
    return pts


def cabeza_malla():
    anillos = [_anillo(*nivel) for nivel in CABEZA]
    return geo.unir(geo.loft_puntos(anillos, tapa_arriba=False), geo.piramide(anillos[-1], CORONILLA, tapa=False))


def cara_pintor():
    """Vacio negro de caras planas; adelante los ojos de almendra crema con orilla dorada, inclinados hacia arriba
    afuera, y el rombo dorado en la frente (por la posicion en el frente, asi pasan de una cara a otra)."""
    negro = faceta(paleta=NEGRO, grano=0)

    def pintor(t):
        if t.n[2] > -0.25:
            return negro(t)
        u, v = t.x, t.y - 11.0                             # u desde el medio, v desde la barbilla
        for s in (1, -1):
            du = s * u - 2.4
            dv = v - 5.1 - 0.14 * du
            if abs(du) < 1.45:
                alto = 0.62 * (1 - (du / 1.45) ** 2) ** 0.8
                if abs(dv) < alto:
                    return hex_(OJO)
                if abs(dv) < alto + 0.14:
                    return hex_(OJO_ORILLA)
        d = abs(u + 1.2) + abs(v - 7.3) * 0.7
        return hex_(OJO_ORILLA) if 0.22 < d < 0.4 else negro(t)
    return pintor


def construir():
    p = Personaje("pibble", altura=21, cabeza=10, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    p.malla("Head/cabeza", "cabeza", cabeza_malla(), cara_pintor(), dens=8, luz=False)   # el vacio no se sombrea
    return p
