"""
Pibble, el semidios errante, hermano de Moles (de la misma estrella). Se rehace paso a paso con los mismos terminos
que ella: el mismo cuerpo chibi y la misma escala, todo low-poly de caras planas, segun referencias/personajes/pibble.png.

Por ahora solo la cabeza, esculpida como un gato de papel: redonda y mas ancha que alta, de caras triangulares, con
los cachetes en pico a los lados, el hocico con la nariz que sale, las cuencas de los ojos hundidas, la ceja y la
frente redonda; toda de vacio negro, con los ojos de almendra crema (piezas con las puntas afiladas, pegadas en las
cuencas, con orilla dorada) inclinados hacia arriba afuera y el rombo dorado al centro de la frente.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..textura import hex_a_rgba as hex_

VACIO, OJO, OJO_ORILLA = "#0E0C10", "#EADCBF", "#C8A058"

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


# los ojos: almendras con las puntas afiladas, pegadas en las cuencas (siguen la curva de la cara) y un poco
# inclinadas hacia arriba afuera, con la orilla dorada atras; el rombo dorado al centro de la frente con el centro negro
OJO_CENTRO = (2.4, 16.1, -3.95)                          # el derecho; el izquierdo en espejo
OJO_TAMANO = (1.25, 0.55)                                # medio largo, medio alto
OJO_GIRO = (0, -35, 9)                                   # sigue la curva de la cara y sube hacia afuera
ROMBO = ((0.0, 18.3, -4.35), (0.3, 0.55), 30)            # centro, medio ancho y medio alto, inclinado como la frente


def _almendra(largo, alto, n=6):
    """Contorno de almendra con las dos puntas afiladas."""
    arriba = [(-largo + 2 * largo * i / n, alto * math.sin(math.pi * i / n) ** 0.8) for i in range(n + 1)]
    abajo = [(x, -y) for x, y in arriba[-2:0:-1]]
    return arriba + abajo


def _placa(perfil, grueso, giro, centro, adelante=0.0):
    m = geo.extruir(perfil, -grueso / 2 - adelante, grueso / 2 - adelante)
    return geo.mover(geo.girar(m, giro), centro)


def ojos(p):
    largo, alto = OJO_TAMANO
    crema = _placa(_almendra(largo, alto), 0.14, OJO_GIRO, OJO_CENTRO, adelante=0.08)
    orilla = _placa(_almendra(largo + 0.16, alto + 0.12), 0.1, OJO_GIRO, OJO_CENTRO)
    p.malla_par("Head/ojos", "ojo", crema, liso(OJO), dens=8, luz=False)
    p.malla_par("Head/ojos", "orilla", orilla, liso(OJO_ORILLA), dens=8, luz=False)
    centro, (w, h), rx = ROMBO
    rombo = lambda a, b: [(0.0, -b), (a, 0.0), (0.0, b), (-a, 0.0)]
    p.malla("Head/ojos", "rombo", _placa(rombo(w, h), 0.1, (rx, 0, 0), centro), liso(OJO_ORILLA), dens=8, luz=False)
    p.malla("Head/ojos", "rombo_centro", _placa(rombo(w * 0.45, h * 0.5), 0.1, (rx, 0, 0), centro, adelante=0.06),
            liso(VACIO), dens=8, luz=False)


def liso(col):
    c = hex_(col)
    return lambda t: c


def construir():
    p = Personaje("pibble", altura=21, cabeza=10, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    p.malla("Head/cabeza", "cabeza", cabeza_malla(), liso(VACIO), dens=4, luz=False)   # el vacio no se sombrea
    ojos(p)
    return p
