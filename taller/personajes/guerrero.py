"""
El GUERRERO CALAVERA de la ultima fase de Khaset: el modelo del esqueleto del juego (brazos y piernas de 2 px) con un
penacho de siete plumas de quetzal y una diadema de oro con mosaico de turquesa. La calavera lleva la pintura de
Mictlantecuhtli: banda negra en los ojos y la quijada roja; en el cuerpo, las costillas y el maxtlatl rojo con orilla
blanca; munequeras y tobilleras de oro. Textura de 64x64 con el acomodo del modelo (ver cliente/RenderGuerrero).
Tambien su arma, el MACUAHUITL (objeto de 16x16): el mazo plano de madera con navajas de obsidiana en los dos cantos.
"""

import math

from PIL import Image

from ..kit import tonos
from ..textura import hex_a_rgba as hex_

HUESO = tonos("#D6CDB4")
NEGRO = "#1A1416"
ROJO = tonos("#A8352A")
ORO = tonos("#D9A43A")
TURQUESA = tonos("#2FA39A")
QUETZAL = tonos("#2E9B5E")
BLANCO = "#E8E2D2"


def _ruido(x, y):
    h = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return h - math.floor(h)


def _hueso(img, x0, y0, w, h, oscuro_abajo=True):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            r = _ruido(x, y)
            k = "s" if (oscuro_abajo and y == y0 + h - 1) or r < 0.18 else "l" if r > 0.85 else "b"
            img.putpixel((x, y), hex_(HUESO[k]))


def _caja(img, u, v, w, h, d, pintor):
    """Pinta las 6 caras de una caja con el acomodo de Minecraft. pintor(cara, i, j, ancho, alto) -> color o None."""
    caras = {"arriba": (u + d, v, w, d), "abajo": (u + d + w, v, w, d), "der": (u, v + d, d, h),
             "frente": (u + d, v + d, w, h), "izq": (u + d + w, v + d, d, h), "atras": (u + 2 * d + w, v + d, w, h)}
    for cara, (x0, y0, cw, ch) in caras.items():
        for j in range(ch):
            for i in range(cw):
                c = pintor(cara, i, j, cw, ch)
                if c is not None:
                    img.putpixel((x0 + i, y0 + j), c)


def textura():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

    def cabeza(cara, i, j, w, h):
        base = hex_(HUESO["l" if cara == "arriba" else "s" if cara == "abajo" else "b"])
        if _ruido(i + 3 * len(cara), j) < 0.15:
            base = hex_(HUESO["s"])
        if cara != "frente":
            if cara in ("der", "izq") and 2 <= j <= 4:
                return hex_(NEGRO) if j == 3 else base           # la banda negra sigue por los lados
            return base
        if 2 <= j <= 4:                                          # la banda negra de los ojos
            if j in (3, 4) and i in (1, 2, 5, 6):
                return hex_("#3A0F0F") if j == 4 else hex_("#000000")      # las cuencas
            return hex_(NEGRO)
        if j == 5 and i in (3, 4):
            return hex_("#000000")                                # la nariz
        if j >= 6:                                               # la quijada roja con los dientes
            if j == 6 and 1 <= i <= 6:
                return hex_(BLANCO) if i % 2 else hex_("#5A1A14")
            return hex_(ROJO["b" if (i + j) % 3 else "s"])
        return base

    _caja(img, 0, 0, 8, 8, 8, cabeza)

    def gorro(cara, i, j, w, h):                                 # la capa de encima: la cinta y las orejeras
        if cara in ("arriba", "abajo"):
            return None
        if j == 1:
            return hex_(ORO["l"])
        if j == 2:
            return hex_(TURQUESA["b"] if i % 3 else ORO["b"])
        if cara in ("der", "izq") and 3 <= j <= 5 and 2 <= i <= 5:
            d = math.hypot(i - 3.5, j - 4)
            return hex_(ORO["l"] if d < 1.0 else ORO["s"]) if d < 1.9 else None      # orejera
        return None

    _caja(img, 32, 0, 8, 8, 8, gorro)

    def cuerpo(cara, i, j, w, h):
        if cara in ("arriba", "abajo"):
            return hex_(HUESO["s"])
        if j >= 8:                                               # el maxtlatl
            if j == 8 or (cara in ("frente", "atras") and 2 <= i <= 5 and j == 11):
                return hex_(BLANCO)
            if cara in ("frente", "atras") and 2 <= i <= 5:
                return hex_(ROJO["l" if j < 10 else "b"])
            return hex_(ROJO["s"])
        if cara in ("frente", "atras") and i in (3, 4):
            return hex_(HUESO["b"])                               # el espinazo / el esternon
        if j % 2 == 0 and j < 7:
            return hex_(HUESO["l" if cara == "frente" else "b"])  # costillas
        return hex_("#2A2224")

    _caja(img, 16, 16, 8, 12, 4, cuerpo)

    def hueso_largo(cara, i, j, w, h):
        if cara == "arriba":
            return hex_(HUESO["l"])
        if cara == "abajo":
            return hex_(HUESO["s"])
        if j in (9, 10):
            return hex_(ORO["l"] if j == 9 else TURQUESA["b"])    # munequera / tobillera
        if j in (5, 6) and cara in ("der", "izq"):
            return hex_(HUESO["s"])                               # la coyuntura
        return hex_(HUESO["b" if _ruido(i + j * 7, w) > 0.2 else "s"])

    _caja(img, 40, 16, 2, 12, 2, hueso_largo)                     # brazo
    _caja(img, 0, 16, 2, 12, 2, hueso_largo)                      # pierna

    # las plumas: 2 x 11 por cara (frente y atras)
    for k in range(7):
        for lado in (0, 2):
            for j in range(11):
                for i in range(2):
                    if j == 0:
                        c = hex_("#123A24")
                    elif j >= 9:
                        c = hex_(ROJO["b"] if j == 9 else ORO["b"])
                    else:
                        c = hex_(QUETZAL["l" if j < 4 else "b" if j < 7 else "s"])
                    if i == 1 and 1 <= j < 9:
                        c = hex_(QUETZAL["s"])                    # el canon de la pluma
                    img.putpixel((k * 4 + lado + i, 32 + j), c)

    def diadema(cara, i, j, w, h):
        if cara in ("arriba", "abajo"):
            return None
        return hex_(TURQUESA["l"] if (i + j) % 3 == 0 else ORO["b" if j else "l"])

    _caja(img, 0, 48, 9, 2, 9, diadema)
    return img


MACUAHUITL = (
    "............nn.",
    "...........nbbn",
    "..........nbwbn",
    ".........nbwbn.",
    "........nbwbn..",
    ".......nbwbn...",
    "......nbwbn....",
    ".....nbwbn.....",
    "....nbwbn......",
    "...nbwbn.......",
    "..ndwbn........",
    ".gdwn..........",
    "gdgn...........",
    "dgd............",
    "gd.............",
    "...............",
)


def macuahuitl():
    """16x16: madera (w), la orilla de navajas de obsidiana (n, b brillo morado), el mango (d, g cuero)."""
    colores = {"w": "#8A5A32", "n": "#1B1220", "b": "#6E4E8E", "d": "#5A3A20", "g": "#B8862E"}
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, fila in enumerate(MACUAHUITL):
        for x, ch in enumerate(fila):
            if ch in colores:
                img.putpixel((x, y), hex_(colores[ch]))
    return img
