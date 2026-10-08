"""
Pintores de materiales en pixel art (sin ruido al azar):

  - paleta de 5 tonos por color: contorno, sombra, base, luz, brillo
    (las sombras se enfrian y las luces se calientan, como en el pixel art a mano)
  - cada cara lateral va de clara arriba a oscura abajo, con borde de luz y contorno oscuro
  - pliegues verticales en la tela, ribetes de color en los bordes, estampados limpios

Un "pintor" es una funcion t -> (r, g, b, a) que recibe el texel (ver modelo.Texel):
t.cara, t.i, t.j (columna/fila dentro de la cara), t.tw, t.th, t.x/y/z (posicion 3D), t.nombre.
"""

import colorsys
import math

from .textura import TRANSPARENTE, azar, hex_a_rgba, ruido

LATERALES = ("north", "south", "east", "west")


def _hsv(c):
    c = hex_a_rgba(c)
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    return h, s, v, c[3]


def _rgb(h, s, v, a=255):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (round(r * 255), round(g * 255), round(b * 255), a)


def _hacia(h, objetivo, t):
    d = ((objetivo - h + 0.5) % 1.0) - 0.5
    return h + d * t


def tono_pa(c, paso):
    """paso < 0 = sombra (mas fria y saturada), paso > 0 = luz (mas calida). paso en -3..2."""
    h, s, v, a = _hsv(c)
    if paso < 0:
        k = -paso
        h = _hacia(h, 0.68, 0.06 * k)                 # hacia azul/violeta
        s = s + (1 - s) * 0.12 * k if s > 0.08 else s
        v = v * (1 - 0.16 * k)
    elif paso > 0:
        h = _hacia(h, 0.13, 0.05 * paso)              # hacia amarillo
        s = s * (1 - 0.12 * paso)
        v = v + (1 - v) * 0.3 * paso + 0.04 * paso
    return _rgb(h, s, v, a)


class Paleta:
    def __init__(self, base):
        self.base = hex_a_rgba(base)
        self.o = tono_pa(base, -3)      # contorno
        self.s2 = tono_pa(base, -2)
        self.s = tono_pa(base, -1)      # sombra
        self.b = self.base
        self.l = tono_pa(base, 1)       # luz
        self.h = tono_pa(base, 2)       # brillo

    def grad(self, k):
        """k de 0 (arriba) a 1 (abajo)."""
        if k < 0.15:
            return self.l
        if k < 0.62:
            return self.b
        if k < 0.9:
            return self.s
        return self.s2


def _pal(c):
    return c if isinstance(c, Paleta) else Paleta(c)


# ============================================================================ estampados


def color_estampado(patron, cols, t, sem):
    """Color base (antes de la luz) segun el estampado. cols = lista de hex."""
    c0 = cols[0]
    c1 = cols[1] if len(cols) > 1 else None
    c2 = cols[2] if len(cols) > 2 else c1
    c3 = cols[3] if len(cols) > 3 else c2
    X, Y, Z = math.floor(t.x - 1e-3), math.floor(t.y - 1e-3), math.floor(t.z - 1e-3)
    if patron == "manchas" and c1:
        n = ruido(t.x, t.y * 0.7, t.z, 3.0, sem)
        if n > 0.78:
            return c3
        if n > 0.66:
            return c2
        if n > 0.55:
            return c1
        return c0
    if patron == "camuflaje" and c1:
        n = ruido(t.x, t.y, t.z, 2.6, sem)
        m = ruido(t.x, t.y, t.z, 1.6, sem + 9)
        if m > 0.74:
            return c3
        return c0 if n < 0.5 else (c1 if n < 0.72 else c2)
    if patron == "tiras" and c1:
        col = X if t.cara in ("north", "south", "up", "down") else Z
        r = azar(sem, col, 3)
        return c0 if r < 0.55 else (c1 if r < 0.85 else c2)
    if patron == "paneles" and c1:
        banda = math.floor((t.x + 40) / 3) if t.cara in ("north", "south") else math.floor((t.z + 40) / 3)
        return (c0, c1, c0, c2)[banda % 4]
    if patron == "rayas" and c1:
        return c1 if Y % 3 == 0 else c0
    if patron == "cuadros" and c1:
        u = X if t.cara in ("north", "south", "up", "down") else Z
        a, b = u % 4 == 0, Y % 4 == 0
        return c2 if (a and b) else (c1 if (a or b) else c0)
    if patron == "estrellas" and c1:
        if t.lateral if hasattr(t, "lateral") else True:
            r = azar(sem, X, Y, Z)
            if r < 0.045:
                return ("estrella", c1)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if t.cara in ("north", "south"):
                    q = (X + dx, Y + dy, Z)
                else:
                    q = (X, Y + dy, Z + dx)
                if azar(sem, *q) < 0.045 and azar(sem + 1, *q) < 0.5:
                    return ("punta", c1)
        return c0
    if patron == "hojas" and c1:
        n = ruido(t.x, t.y, t.z, 2.3, sem)
        if n > 0.68:
            return c1
        if (X + 2 * Y + Z) % 5 == 0 and azar(sem, X // 3, Y // 3, Z // 3) < 0.35:
            return c2
        return c0
    return c0


# ============================================================================ pintores


def tela(color, cols=None, patron="liso", ribete=None, bordes=("abajo",), ancho_ribete=1,
         pliegues=True, sem=0, deshilachado=0.0, contorno=True):
    """Tela con luz arriba, sombra abajo, pliegues verticales y ribete en los bordes elegidos.
    bordes: 'abajo', 'arriba', 'lados' (bordes verticales de cada cara), 'todo'."""
    cols = list(cols or [color])
    paletas = {}

    def pal(c):
        k = c if isinstance(c, str) else str(c)
        if k not in paletas:
            paletas[k] = Paleta(c)
        return paletas[k]
    pr = pal(ribete) if ribete else None
    bset = set(bordes or ())
    if "todo" in bset:
        bset |= {"abajo", "arriba", "lados"}

    def p(t):
        lat = t.cara in LATERALES
        w = ancho_ribete
        # borde deshilachado (texeles transparentes en la ultima fila)
        if deshilachado and lat and t.fila_abajo == 0 and azar(sem, t.x * 7, t.z * 3, t.i) < deshilachado:
            return TRANSPARENTE
        en_ribete = False
        if pr and lat:
            if "abajo" in bset and t.fila_abajo < w:
                en_ribete = True
            if "arriba" in bset and t.j < w:
                en_ribete = True
            if "lados" in bset and (t.i < w or t.i >= t.tw - w):
                en_ribete = True
        elif pr and not lat and "lados" in bset and t.tw > 2 * w and t.th > 2 * w:
            if t.i < w or t.i >= t.tw - w or t.j < w or t.j >= t.th - w:
                en_ribete = True
        if en_ribete:
            P = pr
            if lat:
                k = 0.0 if t.j == 0 else (1.0 if t.fila_abajo == 0 else 0.4)
                return P.l if k == 0 else (P.s if k == 1 else P.b)
            return P.b
        base = color_estampado(patron, cols, t, sem)
        especial = None
        if isinstance(base, tuple) and len(base) == 2 and base[0] in ("estrella", "punta"):
            especial, base = base
        P = pal(base)
        if especial == "estrella":
            return P.h
        if especial == "punta":
            return P.l
        if not lat:
            if t.cara == "up":
                return P.l if (contorno and (t.i == 0 or t.j == 0)) else P.b
            return P.s
        k = t.j / max(1, t.th - 1)
        c = P.grad(k) if t.th > 2 else P.b
        if contorno and t.th >= 3 and t.fila_abajo == 0:
            c = P.o
        if pliegues and t.th >= 4:
            col = t.i + (0 if t.cara in ("north", "south") else 50)
            r = azar(sem, round(t.x * 2), round(t.z * 2), col, 5)
            alto = 0.35 + azar(sem, round(t.x * 2), round(t.z * 2), 6) * 0.55
            if r < 0.3 and k > 1 - alto and t.fila_abajo > 0:
                c = P.s if c in (P.b, P.l) else P.s2
        return c
    return p


def metal(color, sem=0, gema=None):
    P = Paleta(color)
    G = Paleta(gema) if gema else None

    def p(t):
        if G and t.cara == "north" and t.tw >= 3 and t.th >= 3:
            ci, cj = t.tw // 2, t.th // 2
            if abs(t.i - ci + 0.5 * (t.tw % 2 == 0)) <= 0.6 and abs(t.j - cj + 0.5 * (t.th % 2 == 0)) <= 0.6:
                return G.h if (t.i <= ci and t.j <= cj) else G.b
        if t.cara == "up":
            return P.h if (t.i + t.j) % 5 == 0 else P.l
        if t.cara == "down":
            return P.s
        if t.th >= 2 and t.j == 0:
            return P.h
        if t.th >= 3 and t.fila_abajo == 0:
            return P.s2
        if t.tw >= 3 and t.i == t.tw - 1:
            return P.s
        if azar(sem, t.x * 3, t.y * 3, t.z * 3) < 0.05:
            return P.h
        return P.l if t.j < t.th * 0.4 else P.b
    return p


def cuero(color, sem=0, costura=True):
    P = Paleta(color)

    def p(t):
        if t.cara not in LATERALES:
            return P.b if t.cara == "up" else P.s
        if t.th >= 3 and t.j == 0:
            return P.l
        if t.th >= 3 and t.fila_abajo == 0:
            return P.o
        if costura and t.th >= 4 and t.j == 1 and t.i % 2 == 0:
            return P.l
        if azar(sem, round(t.x * 2), round(t.y * 2), round(t.z * 2)) < 0.12:
            return P.s
        return P.b
    return p


def piel(color, sem=0):
    P = Paleta(color)

    def p(t):
        if t.cara == "down":
            return P.s
        if t.cara in LATERALES and t.th >= 3 and t.fila_abajo == 0:
            return P.s
        return P.b
    return p


def pelo(color, brillo=None, mechas=None, sem=0):
    """Mechones verticales + brillo de anime + puntas oscuras."""
    P = Paleta(color)
    B = Paleta(brillo) if brillo else None
    M = Paleta(mechas) if mechas else None

    def p(t):
        if t.cara == "down":
            return P.s2
        col = t.i if t.cara in ("north", "south", "up") else t.i + 31
        r = azar(sem, round(t.x * 2), round(t.z * 2), col)
        if t.cara == "up":
            if B and r < 0.25:
                return B.b
            return P.l if r < 0.5 else P.b
        k = t.j / max(1, t.th - 1)
        c = P.s if r < 0.33 else (P.l if r > 0.8 else P.b)
        if k > 0.75:
            c = P.s2 if r < 0.5 else P.s
        if t.fila_abajo == 0 and t.th >= 2:
            c = M.l if M else P.o
        if t.th >= 4 and t.j == max(1, round(t.th * 0.2)) and r > 0.45:
            c = B.l if B else P.h                       # brillo de anime
        return c
    return p


def plano(color, cols=None, sem=0, forma="pluma"):
    """Planos finos con recorte: plumas, pelaje, flecos. La punta se aclara."""
    cols = list(cols or [color])

    def p(t):
        if t.cara not in ("north", "south"):
            return Paleta(cols[0]).s
        k = t.j / max(1, t.th - 1)                    # 0 arriba (punta)
        mitad = (t.tw - 1) / 2
        if forma == "pluma":
            ancho = mitad * (0.35 + 0.65 * min(1, k * 1.6))
            if abs(t.i - mitad) > ancho + 0.01:
                return TRANSPARENTE
        elif forma == "fleco":
            if azar(sem, t.i, round(t.x), round(t.z)) < k * 0.0 + (0.5 if t.j < 2 else 0):
                return TRANSPARENTE
        c = cols[min(len(cols) - 1, int((1 - k) * len(cols)))]
        P = Paleta(c)
        if abs(t.i - mitad) < 0.6:
            return P.l                                # nervio central
        return P.b if t.i < mitad else P.s
    return p


def liso(color):
    c = hex_a_rgba(color)
    return lambda t: c
