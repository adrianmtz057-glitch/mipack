"""
Revolthir, NSWY de la negacion: chibi de caos y colores calidos. Hecho a mano con el kit segun la imagen que paso el
usuario (referencias/personajes/revolthir_bufon.jpg, un bufon voxel). Reglas: no es humano (cabeza-cubo naranja, sin piel), chibi de la misma altura que Pibble
(nada mas que la altura), estilo propio: carnaval caotico, ni desertico, ni japones, ni de bosque.

Piezas (todo cubos, como un voxel; picos y estrella en low-poly):
  CABEZA-CUBO naranja con ojos grandes blancos que miran de reojo y una boquita en zigzag
  CORONA DE BUFON magenta con rombos, picos de colores para todos lados y una punta caida con cascabel
  TORSO rojo con cuello de volados amarillo; FALDON magenta con el borde en picos
  MANGAS amarillas, GUANTES cafe, PIERNAS verdes, BOTAS cafe
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
AMARILLO = tonos("#F2C232")             # mangas y cuello
VERDE = tonos("#6CC23C")                # piernas y picos
CAFE = tonos("#4A2E24")                 # guantes y botas
MORADO = tonos("#8A4AE0")               # la estrella
ROSA = tonos("#E85AA8")                 # picos
AZUL = tonos("#4A9AE8")                 # picos
CIAN = tonos("#4AD8E0")                 # cascabel
GRIS = tonos("#6E6A78")                 # baston
OJO, PUPILA = "#FFF8EE", "#1A1218"

TOPE = 27.0
CABEZA_Y = 17.0                         # la cabeza va de 17 a 27: la altura de Pibble


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
        return hex_(CAFE["s"])
    return voxel(NARANJA)(t)


def cabeza(t):
    return cara(t) if t.cara == "north" else voxel(NARANJA)(t)


def corona(t):
    """Banda magenta con una fila de rombos claros."""
    if t.cara in ("up", "down"):
        return hex_(MAGENTA["s"])
    u = t.x if t.cara in ("north", "south") else t.z
    v = t.y - (TOPE - 0.5)
    if abs((u % 1.6) - 0.8) + abs(v) * 1.1 < 0.5:
        return hex_(ROSA["l"])
    if abs(v) > 0.72:
        return hex_(MAGENTA["s"])
    return hex_(MAGENTA["b"])


def con_picos(base, y_abajo, alto=0.9, ancho=1.0):
    """Recorta el borde de abajo de una caja en picos (volados de bufon)."""
    def p(t):
        if t.cara == "down":
            return TRANSPARENTE
        if t.cara != "up":
            u = t.x if t.cara in ("north", "south") else t.z
            f = abs(((u / ancho) % 1.0) - 0.5) * 2              # 0 en la punta, 1 entre puntas
            if t.y - y_abajo < alto * f:
                return TRANSPARENTE
        return base(t)
    return p


def bota(t):
    if t.y < 0.5:
        return hex_(CAFE["l"] if t.cara != "down" else CAFE["s"])
    return voxel(CAFE)(t)


def baston(t):
    """Baston gris con dos bandas doradas."""
    if 16.2 < t.y < 16.7 or 10.6 < t.y < 11.1:
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


def construir():
    p = Personaje("revolthir", altura=27, cabeza=10, torso=(7.5, 8, 4.5), brazo=(2.6, 2.6), pierna=(3.2, 3.2))
    C, T, L = p.cuello, p.tope, p.lh                           # 17, 27, 9
    assert (C, T) == (CABEZA_Y, TOPE)

    # ================================================================ CABEZA-CUBO y CORONA DE BUFON
    p.caja("Head/cabeza", "cabeza", (-5, C, -5), (5, T, 5), cabeza, dens=D)
    p.caja("Head/corona", "banda", (-5.4, T - 1.5, -5.4), (5.4, T + 0.4, 5.4), corona, dens=D)
    picos = [((-3.5, -2.9), VERDE, 3.4, (12, 0, 22)), ((-0.9, -3.3), ROSA, 4.0, (14, 0, 4)),
             ((2.1, -2.9), VERDE, 3.2, (10, 0, -16)), ((4.0, -0.3), ROSA, 2.8, (0, 0, -32)),
             ((0.7, 1.8), AZUL, 3.6, (-16, 0, -6)), ((-3.6, 2.2), VERDE, 3.0, (-14, 0, 24)),
             ((3.1, 3.2), AZUL, 2.6, (-20, 0, -18))]
    for k, ((x, z), col, alto, giro) in enumerate(picos):
        base = geo.anillo(x, T + 0.3, z, 1.1, 1.1, 4, 45)
        pico = geo.girar(geo.piramide(base, (x, T + 0.3 + alto, z)), giro, (x, T + 0.3, z))
        p.malla("Head/corona", f"pico{k}", pico, voxel(col), dens=D)
    # punta caida de bufon hacia la izquierda, con el cascabel colgando de la punta
    largo, giro_punta = 3.8, 105.0
    punta = geo.loft([(0.0, 0, 0, 1.3, 1.3), (2.2, 0, 0, 0.9, 0.9), (largo, 0, 0, 0.25, 0.25)], 6, 30)
    punta = geo.girar(punta, (0, 0, giro_punta))               # acostada hacia -X y caida
    base = (-5.1, T - 0.2, 0.4)
    p.malla("Head/corona", "punta", geo.mover(punta, base), voxel(MAGENTA), dens=D)
    a = math.radians(giro_punta)
    tx, ty = base[0] - largo * math.sin(a), base[1] + largo * math.cos(a)
    p.caja("Head/corona", "cascabel", (tx - 0.55, ty - 1.25, base[2] - 0.55), (tx + 0.55, ty - 0.15, base[2] + 0.55),
           voxel(CIAN), dens=D)

    # ================================================================ TORSO, CUELLO de volados y FALDON
    p.caja("Body/torso", "torso", (-3.75, L, -2.25), (3.75, C, 2.25), voxel(ROJO), dens=D)
    p.caja("Body/torso", "cuello", (-4.4, C - 1.6, -2.9), (4.4, C + 0.2, 2.9),
           con_picos(voxel(AMARILLO), C - 1.6, 0.8, 1.05), dens=D)
    p.caja("Body/faldon", "faldon", (-4.4, L - 2.6, -2.8), (4.4, L + 1.4, 2.8),
           con_picos(voxel(MAGENTA), L - 2.6, 1.3, 1.4), dens=D)

    # ================================================================ BRAZOS amarillos con guantes
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.75, s * 6.35))
        g1, g2 = sorted((s * 3.65, s * 6.45))
        p.caja(f"{hueso}/brazo", "manga", (x1, L + 2.2, -1.25), (x2, C, 1.25), voxel(AMARILLO), dens=D)
        p.caja(f"{hueso}/brazo", "guante", (g1, L + 0.2, -1.4), (g2, L + 2.4, 1.4), voxel(CAFE), dens=D)

    # ================================================================ VARITA de estrella en la mano izquierda
    g = "LeftArm/varita"
    giro = dict(rot=(0, 0, 12), piv=(-5.05, L + 1.3, -1.9))
    p.caja(g, "baston", (-5.3, L - 1.0, -2.15), (-4.8, L + 9.5, -1.65), baston, dens=D, **giro)
    cx, cy = -5.05, L + 11.3
    malla = geo.extruir(estrella(cx, cy, 2.0, 0.9), -2.3, -1.5)
    p.malla(g, "estrella", geo.girar(malla, (0, 0, 12), (-5.05, L + 1.3, -1.9)), pintor_estrella(cx, cy), dens=D)

    # ================================================================ PIERNAS verdes y BOTAS cafe
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.2, s * 3.4))
        b1, b2 = sorted((s * 0.0, s * 3.6))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 2.6, -1.5), (x2, L, 1.5), voxel(VERDE), dens=D)
        p.caja(f"{hueso}/bota", "bota", (b1, 0.0, -2.0), (b2, 2.8, 1.7), bota, dens=D)
    return p
