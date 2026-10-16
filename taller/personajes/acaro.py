"""
El ACARO DE AMATISTA de la fase 2 de Crackatos: los cuatro segmentos del endermite (para que el juego los menee
igual), de la piedra oscura de Crackatos, con una geoda de cristales que le sale del lomo, un cuernito, dos colmillos
y seis patas. Los cristales, sus puntas y los ojos brillan. Textura de 64x32 con el acomodo del modelo (ver
cliente/AcaroRenderer.capa(), las cajas van en el mismo orden y con los mismos texOffs).
"""

from PIL import Image

from .guerrero import _caja, _ruido
from .jefe_piedra import AMATISTA, PIEDRA, PIEDRA_C
from ..textura import hex_a_rgba as hex_

CLARO = "#B48CF0"
PUNTA = "#EBDDFF"
OJO = "#FF8CF0"

# (u, v, ancho, alto, hondo, tipo): los segmentos 0..3, los cristales, el cuerno, el colmillo y la pata
SEGMENTOS = [(0, 0, 4, 3, 2), (0, 6, 6, 4, 5), (0, 16, 3, 3, 1), (0, 21, 1, 2, 1)]
CRISTALES = [(24, 0, 2, 7, 2), (34, 0, 2, 5, 2), (44, 0, 1, 4, 1), (50, 0, 1, 3, 1), (54, 0, 1, 3, 1), (58, 0, 1, 2, 1)]
COLMILLO = (24, 12, 1, 1, 2)
PATA = (32, 12, 3, 1, 1)


def _mezcla(a, b, t):
    a, b = hex_(a), hex_(b)
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)) + (255,)


def textura():
    """(textura, brillo). El brillo va con RenderType.eyes (se suma): negro o transparente = no brilla."""
    tex = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    brillo = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    luz = []                                                     # (x, y, color, fuerza) para el brillo

    def piedra(n):
        def pintor(cara, i, j, w, h):
            r = _ruido(i + 11 * n + 5 * len(cara), j + 3 * n)
            if cara == "abajo":
                return hex_(PIEDRA["s"])
            if cara == "arriba":
                if r > 0.9:
                    return hex_(AMATISTA["b"])                   # granitos de amatista
                return hex_(PIEDRA_C["b" if r > 0.35 else "s"] if (i + j) % 4 else PIEDRA_C["l"])
            if j == 0:
                return hex_(PIEDRA_C["s"])                       # el canto de arriba
            if j == h - 1:
                return hex_(PIEDRA["s"])
            if n == 0 and cara == "frente":                      # la cara: dos ojos y la boca
                if j == 1 and i in (0, w - 1):
                    return ("ojo", i, j)
                if j == 2 and 0 < i < w - 1:
                    return hex_("#0B0710")
            if r > 0.93:
                return hex_(AMATISTA["s"])
            return hex_(PIEDRA["b" if r > 0.3 else "l" if r > 0.15 else "s"])
        return pintor

    def cristal(cara, i, j, w, h):
        if cara == "abajo":
            return hex_(AMATISTA["s"])
        if cara == "arriba":
            return ("punta",)
        t = 1.0 - j / max(1, h - 1)                              # 1 arriba, 0 abajo
        lado = {"frente": 0.15, "izq": 0.0, "der": -0.25, "atras": -0.35}[cara]
        if w == 2:
            lado += 0.12 if i == 0 else -0.12                    # cada cara con su arista clara
        k = max(0.0, min(1.0, 0.25 + 0.6 * t + lado))
        if j == 0:
            return ("punta",)
        if k > 0.7:
            return _mezcla(AMATISTA["l"], CLARO, (k - 0.7) / 0.3)
        if k > 0.35:
            return _mezcla(AMATISTA["b"], AMATISTA["l"], (k - 0.35) / 0.35)
        return _mezcla(AMATISTA["s"], AMATISTA["b"], k / 0.35)

    def colmillo(cara, i, j, w, h):
        if cara == "frente":
            return ("punta",)
        return hex_(AMATISTA["l"] if cara in ("arriba", "izq") else AMATISTA["b"])

    def pata(cara, i, j, w, h):
        if cara in ("der", "izq"):
            return hex_(AMATISTA["b"])                           # las puntas de las patas
        return hex_(PIEDRA_C["s"] if cara == "arriba" else PIEDRA["s"])

    def con_luz(pintor):
        """Pinta en la textura y anota lo que brilla."""
        def envuelto(cara, i, j, w, h):
            c = pintor(cara, i, j, w, h)
            if isinstance(c, tuple) and isinstance(c[0], str):
                if c[0] == "ojo":
                    luz.append((cara, i, j, OJO, 1.0))
                    return hex_("#FFC8FA")
                luz.append((cara, i, j, PUNTA, 0.85))
                return hex_(PUNTA)
            return c
        return envuelto

    def caja(u, v, w, h, d, pintor, fuerza_cristal=0.0):
        """Pinta la caja y su brillo (los cristales brillan un poco todos; las puntas y los ojos, fuerte)."""
        marcas = {}

        def pintor2(cara, i, j, cw, ch):
            antes = len(luz)
            c = con_luz(pintor)(cara, i, j, cw, ch)
            if len(luz) > antes:
                marcas[(cara, i, j)] = luz[-1]
            elif fuerza_cristal and c is not None:
                marcas[(cara, i, j)] = (cara, i, j, c, fuerza_cristal)
            return c

        _caja(tex, u, v, w, h, d, pintor2)
        caras = {"arriba": (u + d, v), "abajo": (u + d + w, v), "der": (u, v + d), "frente": (u + d, v + d),
                 "izq": (u + d + w, v + d), "atras": (u + 2 * d + w, v + d)}
        for (cara, i, j), (_c, _i, _j, col, f) in marcas.items():
            x0, y0 = caras[cara]
            rgb = hex_(col)
            brillo.putpixel((x0 + i, y0 + j), tuple(int(rgb[k] * f) for k in range(3)) + (255,))

    for n, (u, v, w, h, d) in enumerate(SEGMENTOS):
        caja(u, v, w, h, d, piedra(n))
    for (u, v, w, h, d) in CRISTALES:
        caja(u, v, w, h, d, cristal, fuerza_cristal=0.4)
    caja(*COLMILLO, colmillo, fuerza_cristal=0.3)
    caja(*PATA, pata)
    return tex, brillo
