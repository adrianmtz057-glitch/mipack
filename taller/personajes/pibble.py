"""
Pibble, el semidios errante, hermano de Moles (de la misma estrella). Se rehace paso a paso con los mismos terminos
que ella: el mismo cuerpo chibi y la misma escala, todo low-poly de caras planas, segun referencias/personajes/pibble.png.

Por ahora solo la cabeza, esculpida como un gato de papel: redonda y mas ancha que alta, de caras triangulares, con
los cachetes en pico a los lados, el hocico con la nariz que sale, las cuencas de los ojos hundidas, la ceja y la
frente redonda; toda de vacio negro, con los ojos de almendra crema (piezas con las puntas afiladas, pegadas en las
cuencas, con orilla dorada) inclinados hacia arriba afuera y el rombo dorado al centro de la frente.
La capucha, paso a paso: por ahora los dos paneles de enfrente, unidos por la punta en la frente: doblados hacia la
cabeza, la parte de abajo inclinada hacia enfrente, la esquina de arriba alargada hacia arriba, y el hundido hecho con
paneles 2D en capas.
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


# la capucha, paso a paso: por ahora los dos paneles de enfrente, unidos por la punta justo en la frente. Cada uno (el
# derecho; el izquierdo en espejo) nace de un triangulo equilatero de lado LADO_TRIANGULO con la punta en la frente:
# las esquinas de afuera alargadas (en punta), girado sobre su punta (lo de afuera baja), doblado hacia la cabeza e
# inclinado (la parte de abajo hacia enfrente); y la esquina de arriba alargada hacia arriba desde la mitad de la
# orilla de arriba. El hundido (un triangulo de la mitad con la base sobre el lado de afuera, de su punta hasta el
# final) va con PANELES 2D en capas, cada una un poco mas atras y mas oscura: (escala del hueco, que tan atras, sesgo)
LADO_TRIANGULO = 10.5
PUNTA_FRENTE = (0.0, 19.8, -5.0)
Z_AFUERA = -3.0
GIRO_TRIANGULO = 20.0                                    # grados que se gira sobre su punta: lo de afuera baja
HACIA_ADENTRO = 25.0                                     # grados que lo de afuera se dobla hacia la cabeza
INCLINA = 20.0                                           # grados que la parte de abajo se inclina hacia enfrente
ALARGA = 2.5                                             # cuanto se alargan las dos esquinas de afuera (en punta)
PUNTA_ARRIBA = 4.0                                       # cuanto se alarga hacia arriba la esquina de arriba
CAPAS = ((0.5, 0.0, 0.0), (0.32, 0.15, -0.1), (None, 0.3, -0.2))
CREMA = ((0.34, "#B8AD9A"), (0.5, "#CBC1AE"), (0.66, "#DCD3C3"), (9.0, "#E9E2D5"))


def _triangulo():
    """La punta en la frente y las dos esquinas de afuera (la de arriba y la de abajo)."""
    x0, y0, z0 = PUNTA_FRENTE
    l = LADO_TRIANGULO
    x = math.sqrt(l * l - (l / 2) ** 2 - (Z_AFUERA - z0) ** 2)
    cx = x * 2 / 3                                       # el centro del triangulo (respecto a la punta)
    g, h, k = math.radians(-GIRO_TRIANGULO), math.radians(HACIA_ADENTRO), math.radians(INCLINA)

    def esquina(dy):
        ex, ey = x - cx, dy
        d = math.hypot(ex, ey)
        dx, dy = cx + ex * (1 + ALARGA / d), ey * (1 + ALARGA / d)     # alargada desde el centro
        dx, dy = dx * math.cos(g) - dy * math.sin(g), dx * math.sin(g) + dy * math.cos(g)
        dz = Z_AFUERA - z0
        dx, dz = dx * math.cos(h) - dz * math.sin(h), dx * math.sin(h) + dz * math.cos(h)
        dy, dz = dy * math.cos(k) - dz * math.sin(k), dz * math.cos(k) + dy * math.sin(k)
        return (x0 + dx, y0 + dy, z0 + dz)
    return (PUNTA_FRENTE, esquina(l / 2), esquina(-l / 2))


def _resta(p, q):
    return tuple(x - y for x, y in zip(p, q))


def _punto(p, q):
    return sum(x * y for x, y in zip(p, q))


def _cruz(p, q):
    return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])


def _unit(p):
    return tuple(x / math.sqrt(_punto(p, p)) for x in p)


def _paneles(a, b, c):
    """Los paneles 2D de un lado: (malla, sesgo de tono). Cada panel es un poligono plano con sus dos caras."""
    u = _unit(_resta(b, a))
    n = _unit(_cruz(_resta(b, a), _resta(c, a)))
    if n[2] < 0:
        n = tuple(-x for x in n)                          # atras = hacia la cabeza
    v = _cruz(n, u)
    t0, b1, b2 = [(_punto(_resta(q, a), u), _punto(_resta(q, a), v)) for q in (a, b, c)]
    mx, my = (b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2   # medio del lado de afuera
    lx, ly = b1[0] - b2[0], b1[1] - b2[1]
    largo = math.hypot(lx, ly)
    punta = (b1[0] + lx / largo * PUNTA_ARRIBA, b1[1] + ly / largo * PUNTA_ARRIBA)
    mitad = ((t0[0] + b1[0]) / 2, (t0[1] + b1[1]) / 2)

    def hueco(k):                                         # el triangulo achicado hacia el medio del lado de afuera
        return [(mx + (x - mx) * k, my + (y - my) * k) for x, y in (t0, b1, b2)]

    (k0, z0, s0), (k1, z1, s1), (_, z2, s2) = CAPAS
    p, q1, q2 = hueco(k0)
    r, w1, w2 = hueco(k1)
    capas = (([t0, mitad, punta, q1, p, q2, b2], z0, s0), ([q1, p, q2, w2, r, w1], z1, s1), ([r, w1, w2], z2, s2))
    out = []
    for pts, z, sesgo in capas:
        area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
        if area > 0:                                      # que la cara de enfrente mire hacia enfrente
            pts = pts[::-1]
        vs = [tuple(a[i] + x * u[i] + y * v[i] + z * n[i] for i in range(3)) for x, y in pts]
        m = len(vs)
        out.append(((vs, [tuple(range(m)), tuple(range(m))[::-1]]), sesgo))
    return out


def capucha(p):
    for k, (malla, sesgo) in enumerate(_paneles(*_triangulo())):
        p.malla_par("Head/capucha", f"panel{k}", malla, faceta(sesgo, CREMA, grano=0), dens=4, luz=False)


def liso(col):
    c = hex_(col)
    return lambda t: c


def construir():
    p = Personaje("pibble", altura=21, cabeza=10, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    p.malla("Head/cabeza", "cabeza", cabeza_malla(), liso(VACIO), dens=4, luz=False)   # el vacio no se sombrea
    ojos(p)
    capucha(p)
    return p
