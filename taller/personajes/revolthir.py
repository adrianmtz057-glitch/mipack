"""
Revolthir, NSWY de la negacion: chibi de caos y colores calidos. Hecho a mano con el kit segun la imagen que paso el
usuario (referencias/personajes/revolthir_bufon.jpg) y las formas que marco encima con rayas blancas
(revolthir_bufon_rayas.jpg). Reglas: no es humano (cabeza-cubo naranja, sin piel), chibi de la misma altura que
Pibble (nada mas que la altura), estilo propio: carnaval caotico, ni desertico, ni japones, ni de bosque.

Formas (todo en bloques, como la referencia; picos, cascabeles y estrella en low-poly):
  CABEZA-CUBO naranja con ojos grandes blancos que miran de reojo y una boquita en zigzag
  CORONA DE BUFON: una caja grande magenta, mas ancha que la cabeza, con rombos y picos de colores en el borde de
    arriba; a los costados, dos puntas con cascabeles facetados (uno grande azul, uno chico rosa)
  TORSO rojo y ancho con un cuello amarillo en punta debajo de la cara; FALDON magenta que se abre hacia abajo y
    termina en picos
  MANGAS amarillas con PUNOS grandes; PIERNAS verdes gruesas; BOTAS en bloque
  VARITA en la mano izquierda: baston con bandas y una estrella morada
Paleta calida y saltona, cada color con su rampa (hue shifting) y sin ruido; el volumen lo pone la luz horneada.
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_

D = 4                                   # texeles por px

NARANJA = tonos("#E8762C")              # la cabeza
MAGENTA = tonos("#C42A86")              # corona y faldon
ROJO = tonos("#D23A30")                 # torso
AMARILLO = tonos("#F2C232")             # mangas, cuello y picos
VERDE = tonos("#6CC23C")                # piernas y picos
GUANTE = tonos("#7A6470")               # punos
BOTA = tonos("#4A2E2C")                 # botas
MORADO = tonos("#8A4AE0")               # la estrella
ROSA = tonos("#E85AA8")                 # picos y cascabel chico
AZUL = tonos("#4A9AE8")                 # picos y cascabel grande
GRIS = tonos("#6E6A78")                 # baston
OJO, PUPILA = "#FFF8EE", "#1A1218"

TOPE = 27.0                             # la cabeza va de 17 a 27: la altura de Pibble
CABEZA_Y = 17.0
PIERNAS = 9.0                           # la cadera


def voxel(rampa):
    """Color plano con algun bloquecito apenas mas claro en un patron fijo (aire de voxel, sin ruido)."""
    b, l = hex_(rampa["b"]), hex_(rampa["l"])
    medio = tuple((x + y) // 2 for x, y in zip(b, l))

    def p(t):
        if t.cara == "up":
            return l
        cx, cy = math.floor(t.x + t.z), math.floor(t.y)
        return medio if (3 * cx + 5 * cy) % 7 == 0 else b
    return p


def _trazo(u, v, a, b, grosor):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    k = max(0.0, min(1.0, ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(u - ax - k * dx, v - ay - k * dy) <= grosor / 2


def cara(t):
    """Ojos grandes blancos con la pupila corrida a la derecha de quien mira (de reojo, travieso), un parpado oscuro
    arriba y una boquita en zigzag."""
    u, v = -t.x, t.y - CABEZA_Y                              # u: hacia la derecha de quien mira; v: desde el menton
    for lado in (-1, 1):
        u0, u1 = (0.8, 3.2) if lado > 0 else (-3.2, -0.8)
        if u0 <= u <= u1 and 4.0 <= v <= 6.4:
            if v > 6.15:
                return hex_(PUPILA)                          # parpado
            if u1 - 1.15 <= u <= u1 - 0.05 and 4.15 <= v <= 5.45:
                return hex_(PUPILA)                          # pupila de reojo
            return hex_(OJO)
    puntos = [(-1.3, 2.1), (-0.65, 1.7), (0.0, 2.1), (0.65, 1.7), (1.3, 2.1)]
    if any(_trazo(u, v, puntos[k], puntos[k + 1], 0.3) for k in range(len(puntos) - 1)):
        return hex_(BOTA["s"])
    return voxel(NARANJA)(t)


def cabeza(t):
    return cara(t) if t.cara == "north" else voxel(NARANJA)(t)


CORONA_Y = (TOPE - 0.8, TOPE + 3.4)     # la caja de la corona


def corona(t):
    """Caja magenta: banda oscura abajo, una fila de rombos claros al medio y el canto de arriba con luz."""
    if t.cara == "up":
        return hex_(MAGENTA["l"])
    if t.cara == "down":
        return hex_(MAGENTA["s"])
    u = t.x if t.cara in ("north", "south") else t.z
    y0, y1 = CORONA_Y
    v = t.y - (y0 + y1) / 2
    if abs((u % 1.8) - 0.9) + abs(v) * 1.1 < 0.62:
        return hex_(ROSA["l"])
    if t.y < y0 + 0.6:
        return hex_(MAGENTA["s"])
    return voxel(MAGENTA)(t)


def con_picos(base, y_abajo, alto=0.9, ancho=1.0):
    """Recorta el borde de abajo de una pieza en picos (volados de bufon)."""
    def p(t):
        if t.cara == "down":
            return TRANSPARENTE
        if t.cara != "up":
            u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
            f = abs(((u / ancho) % 1.0) - 0.5) * 2              # 0 en la punta, 1 entre puntas
            if t.y - y_abajo < alto * f:
                return TRANSPARENTE
        return base(t)
    return p


def babero(t):
    """Cuello amarillo en punta: el borde de abajo baja en V hasta el centro."""
    if t.y < CABEZA_Y - 2.9 + abs(t.x) * 0.9:
        return TRANSPARENTE
    return voxel(AMARILLO)(t)


def bota(t):
    if t.y < 0.55:
        return hex_(BOTA["l"] if t.cara != "down" else BOTA["s"])
    return voxel(BOTA)(t)


def baston(t):
    """Baston gris con dos bandas doradas."""
    if PIERNAS + 2.5 < t.y < PIERNAS + 3.0 or PIERNAS + 8.3 < t.y < PIERNAS + 8.8:
        return hex_(AMARILLO["b"])
    return hex_(GRIS["l"] if t.cara == "up" else GRIS["b"])


def estrella(cx, cy, r_ext, r_int):
    """Estrella de 5 puntas en el plano XY (antihoraria)."""
    pts = []
    for k in range(10):
        a = math.radians(90 + 36 * k)
        r = r_ext if k % 2 == 0 else r_int
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def pintor_estrella(cx, cy):
    def p(t):
        if abs(t.n[2]) > 0.7:
            return hex_(MORADO["l"] if math.hypot(t.x - cx, t.y - cy) < 0.75 else MORADO["b"])
        return hex_(MORADO["s"])
    return p


def cascabel(c, lado):
    """Cascabel facetado: un octaedro (dos piramides) de lado 'lado', como una gema."""
    return geo.bipiramide(c, lado * 0.62, lado * 0.62, lado * 0.62, lados=4, giro=45)


def punta(base, largo, giro):
    """Punta de bufon: cono de 6 lados que sale de 'base' girado 'giro' grados (rz)."""
    m = geo.loft([(0.0, 0, 0, 1.2, 1.2), (largo * 0.55, 0, 0, 0.85, 0.85), (largo, 0, 0, 0.25, 0.25)], 6, 30)
    m = geo.girar(m, (0, 0, giro))
    a = math.radians(giro)
    tip = (base[0] - largo * math.sin(a), base[1] + largo * math.cos(a), base[2])
    return geo.mover(m, base), tip


def construir():
    p = Personaje("revolthir", altura=27, cabeza=10, torso=(9.5, 8, 5.5), brazo=(3, 3), pierna=(4.5, 4.5))
    C, T, L = p.cuello, p.tope, p.lh                           # 17, 27, 9
    assert (C, T, L) == (CABEZA_Y, TOPE, PIERNAS)

    # ================================================================ CABEZA-CUBO y CORONA DE BUFON
    p.caja("Head/cabeza", "cabeza", (-5, C, -5), (5, T, 5), cabeza, dens=D)
    y0, y1 = CORONA_Y
    p.caja("Head/corona", "corona", (-6.2, y0, -6.2), (6.2, y1, 6.2), corona, dens=D)
    colores = (VERDE, ROSA, AMARILLO, AZUL, VERDE, ROSA, AMARILLO, AZUL, ROSA, VERDE)
    picos = [((-4.6, -5.3), 3.2, (-14, 0, 6)), ((-1.6, -5.3), 3.8, (-16, 0, 0)), ((1.5, -5.3), 3.0, (-14, 0, 0)),
             ((4.5, -5.3), 3.5, (-14, 0, -6)), ((5.3, -1.6), 2.8, (0, 0, -16)), ((5.3, 2.0), 3.2, (6, 0, -16)),
             ((3.0, 5.3), 3.0, (14, 0, -4)), ((0.0, 5.3), 3.6, (16, 0, 0)), ((-3.0, 5.3), 2.8, (14, 0, 4)),
             ((-5.3, 0.2), 3.3, (0, 0, 16))]
    for k, ((x, z), alto, giro) in enumerate(picos):
        base = geo.anillo(x, y1, z, 1.05, 1.05, 4, 45)
        pico = geo.girar(geo.piramide(base, (x, y1 + alto, z)), giro, (x, y1, z))
        p.malla("Head/corona", f"pico{k}", pico, voxel(colores[k]), dens=D)
    # puntas de bufon a los costados con sus cascabeles: el grande cae a la derecha del personaje, el chico a la otra
    malla, tip = punta((6.0, y0 + 1.2, -0.5), 3.6, -112)
    p.malla("Head/corona", "punta_der", malla, voxel(VERDE), dens=D)
    p.malla("Head/corona", "cascabel_der", cascabel((tip[0] + 0.3, tip[1] - 1.1, tip[2]), 2.3), voxel(AZUL), dens=D)
    malla, tip = punta((-6.0, y0 + 0.9, 0.6), 2.4, 118)
    p.malla("Head/corona", "punta_izq", malla, voxel(ROSA), dens=D)
    p.malla("Head/corona", "cascabel_izq", cascabel((tip[0] - 0.2, tip[1] - 0.8, tip[2]), 1.7), voxel(ROSA), dens=D)

    # ================================================================ TORSO ancho, CUELLO en punta y FALDON abierto
    p.caja("Body/torso", "torso", (-4.75, L, -2.75), (4.75, C, 2.75), voxel(ROJO), dens=D)
    p.caja("Body/torso", "cuello", (-4.95, C - 0.6, -2.95), (4.95, C + 0.05, 2.95), voxel(AMARILLO), dens=D)
    p.caja("Body/torso", "babero", (-2.3, C - 2.9, -3.0), (2.3, C - 0.55, -2.8), babero, dens=D)
    falda = geo.loft([(L - 2.4, 0, 0, 6.3 / 0.7071, 4.0 / 0.7071), (L + 1.4, 0, 0, 5.05 / 0.7071, 3.05 / 0.7071)],
                     4, 45, tapa_abajo=False, tapa_arriba=False)
    p.malla("Body/faldon", "faldon", falda, con_picos(voxel(MAGENTA), L - 2.4, 1.3, 1.5), dens=D)

    # ================================================================ BRAZOS: mangas amarillas y punos grandes
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 4.75, s * 7.75))
        g1, g2 = sorted((s * 4.45, s * 8.05))
        p.caja(f"{hueso}/brazo", "manga", (x1, L + 2.9, -1.5), (x2, C, 1.5), voxel(AMARILLO), dens=D)
        p.caja(f"{hueso}/brazo", "puno", (g1, L - 0.5, -1.8), (g2, L + 3.1, 1.8), voxel(GUANTE), dens=D)

    # ================================================================ VARITA de estrella en la mano izquierda
    g = "LeftArm/varita"
    piv = (-6.25, L + 1.4, -2.3)
    giro = dict(rot=(0, 0, 12), piv=piv)
    p.caja(g, "baston", (-6.5, L - 1.4, -2.55), (-6.0, L + 10.5, -2.05), baston, dens=D, **giro)
    cx, cy = -6.25, L + 12.3
    malla = geo.extruir(estrella(cx, cy, 2.1, 0.95), -2.7, -1.9)
    p.malla(g, "estrella", geo.girar(malla, (0, 0, 12), piv), pintor_estrella(cx, cy), dens=D)

    # ================================================================ PIERNAS verdes gruesas y BOTAS en bloque
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.15, s * 4.5))
        b1, b2 = sorted((s * 0.0, s * 4.75))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 2.6, -2.2), (x2, L, 2.2), voxel(VERDE), dens=D)
        p.caja(f"{hueso}/bota", "bota", (b1, 0.0, -2.9), (b2, 2.8, 2.4), bota, dens=D)
    return p
