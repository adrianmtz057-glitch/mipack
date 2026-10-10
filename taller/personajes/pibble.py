"""
Pibble, el semidios errante, hermano de Moles (de la misma estrella). Se rehace paso a paso con los mismos terminos
que ella: el mismo cuerpo chibi y la misma escala, todo low-poly de caras planas, segun referencias/personajes/pibble.png.

Por ahora solo la cabeza, esculpida como un gato de papel: redonda y mas ancha que alta, de caras triangulares, con
los cachetes en pico a los lados, el hocico con la nariz que sale, las cuencas de los ojos hundidas, la ceja y la
frente redonda; toda de vacio negro, con los ojos de almendra crema (piezas con las puntas afiladas, pegadas en las
cuencas, con orilla dorada) inclinados hacia arriba afuera y el rombo dorado al centro de la frente.
La capucha, paso a paso: por ahora los dos triangulos equilateros de enfrente, unidos por la punta en la frente,
con un triangulo de la mitad hundido en cada uno (de su punta hasta el final del grande), semi escalonado.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..textura import hex_a_rgba as hex_
from .moles import faceta

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


# la capucha, paso a paso: por ahora los dos triangulos de enfrente, unidos por la punta justo en la frente.
# Equilateros: cada uno (el derecho; el izquierdo en espejo) con la punta en la frente y el lado de afuera derecho
# (vertical), un poco hacia atras; los tres lados miden LADO_TRIANGULO. En cada uno, otro triangulo de la mitad, con
# la base sobre el lado de afuera, marca lo que se HUNDE (de su punta hasta el final del grande), semi escalonado: una
# pared inclinada, un escalon plano, otra pared inclinada y el fondo. HUNDIDO: (escala del triangulo chico, hasta
# donde baja la 1a pared, donde acaba el escalon, hasta donde baja la 2a pared), las escalas respecto al grande y
# hacia el medio de su lado de afuera; y las dos profundidades
LADO_TRIANGULO = 10.5
PUNTA_FRENTE = (0.0, 19.8, -5.0)
Z_AFUERA = -3.0
GROSOR = 0.8
HUNDIDO = ((0.5, 0.44, 0.35, 0.29), (0.25, 0.5))
CREMA = ((0.34, "#B8AD9A"), (0.5, "#CBC1AE"), (0.66, "#DCD3C3"), (9.0, "#E9E2D5"))


GIRO_TRIANGULO = 20.0                                    # grados que se gira sobre su punta: lo de afuera baja


def _triangulo():
    x0, y0, z0 = PUNTA_FRENTE
    l = LADO_TRIANGULO
    x = math.sqrt(l * l - (l / 2) ** 2 - (Z_AFUERA - z0) ** 2)
    g = math.radians(-GIRO_TRIANGULO)
    gira = lambda dx, dy: (x0 + dx * math.cos(g) - dy * math.sin(g), y0 + dx * math.sin(g) + dy * math.cos(g), Z_AFUERA)
    return (PUNTA_FRENTE, gira(x, l / 2), gira(x, -l / 2))


def _resta(p, q):
    return tuple(x - y for x, y in zip(p, q))


def _punto(p, q):
    return sum(x * y for x, y in zip(p, q))


def _cruz(p, q):
    return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])


def _unit(p):
    return tuple(x / math.sqrt(_punto(p, p)) for x in p)


def _placa_hundida(a, b, c):
    """Placa triangular (a la punta en la frente; b, c el lado de afuera; el grueso hacia atras) con el triangulo de la
    mitad hundido: su base sobre el lado de afuera y su punta a medio camino hacia la frente, asi se hunde todo de su
    punta hasta el final del grande, en dos escalones de paredes inclinadas (que se ven de canto en la orilla de
    afuera). Se arma en el plano de la placa (x, y; z hacia adentro) y luego se lleva al mundo; cada cara se voltea si
    hace falta para que mire hacia afuera."""
    u = _unit(_resta(b, a))
    n = _unit(_cruz(_resta(b, a), _resta(c, a)))
    if n[2] < 0:
        n = tuple(-x for x in n)                          # z de la placa = hacia atras
    v = _cruz(n, u)
    t0, b1, b2 = [(_punto(_resta(q, a), u), _punto(_resta(q, a), v)) for q in (a, b, c)]
    mx, my = (b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2   # medio del lado de afuera
    gx, gy = (t0[0] + b1[0] + b2[0]) / 3, (t0[1] + b1[1] + b2[1]) / 3
    (k1, k1b, k2, k2b), (d1, d2) = HUNDIDO

    def tri(k, z):                                        # el grande achicado hacia el medio del lado de afuera
        return [(mx + (x - mx) * k, my + (y - my) * k, z) for x, y in (t0, b1, b2)]

    (T0, B1, B2), atras = tri(1.0, 0.0), tri(1.0, GROSOR)
    (P, Q1, Q2), (Pb, Q1b, Q2b) = tri(k1, 0.0), tri(k1b, d1)
    (R, S1, S2), (Rb, S1b, S2b) = tri(k2, d1), tri(k2b, d2)
    frente, hacia_adentro = (0, 0, -1), lambda p, q: (mx - (p[0] + q[0]) / 2, my - (p[1] + q[1]) / 2, -0.6)
    caras = [([T0, B1, Q1, P], frente), ([T0, P, Q2, B2], frente),               # lo que no se hunde
             ([Q1, P, Pb, Q1b], hacia_adentro(Q1, P)), ([P, Q2, Q2b, Pb], hacia_adentro(P, Q2)),     # 1a pared
             ([Q1b, Pb, R, S1], frente), ([Pb, Q2b, S2, R], frente),             # el escalon
             ([S1, R, Rb, S1b], hacia_adentro(S1, R)), ([R, S2, S2b, Rb], hacia_adentro(R, S2)),     # 2a pared
             ([S1b, Rb, S2b], frente),                                            # el fondo
             (atras, (0, 0, 1)),
             ([T0, B1, atras[1], atras[0]], (b1[0] - b2[0] + t0[0] - mx, b1[1] - b2[1] + t0[1] - my, 0)),
             ([T0, B2, atras[2], atras[0]], (b2[0] - b1[0] + t0[0] - mx, b2[1] - b1[1] + t0[1] - my, 0)),
             # el lado de afuera, con el perfil de los escalones
             ([B1, Q1, Q1b, S1, S1b, S2b, S2, Q2b, Q2, B2, atras[2], atras[1]], (mx - gx, my - gy, 0))]
    vs, cs = [], []
    for pts, hacia in caras:
        nrm = [0.0, 0.0, 0.0]                             # normal de Newell (sirve para poligonos concavos)
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            nrm[0] += (p[1] - q[1]) * (p[2] + q[2])
            nrm[1] += (p[2] - q[2]) * (p[0] + q[0])
            nrm[2] += (p[0] - q[0]) * (p[1] + q[1])
        if _punto(nrm, hacia) < 0:
            pts = pts[::-1]
        cs.append(tuple(range(len(vs), len(vs) + len(pts))))
        vs += [tuple(a[i] + x * u[i] + y * v[i] + z * n[i] for i in range(3)) for x, y, z in pts]
    return vs, cs


def capucha(p):
    p.malla_par("Head/capucha", "triangulo", _placa_hundida(*_triangulo()), faceta(paleta=CREMA, grano=0), dens=4,
                luz=False)


def liso(col):
    c = hex_(col)
    return lambda t: c


def construir():
    p = Personaje("pibble", altura=21, cabeza=10, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    p.malla("Head/cabeza", "cabeza", cabeza_malla(), liso(VACIO), dens=4, luz=False)   # el vacio no se sombrea
    ojos(p)
    capucha(p)
    return p
