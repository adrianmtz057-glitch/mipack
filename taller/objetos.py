"""
Accesorios como modelos APARTE (para la mano, la espalda o el cinturon): cetro, libro, mochila,
brujula, medallon, espada, baston y farol. Cada uno es un .bbmodel con un hueso "Item".
El punto (0, 0, 0) es donde se agarra.
"""

from .modelo import Modelo
from .pintura import Paleta, cuero, metal, tela
from .textura import TRANSPARENTE

ORO = "#E3B04B"


def _m(nombre):
    m = Modelo(nombre)
    m.pivotes = {"Item": (0, 0, 0)}
    return m


def _rayos(m, g, cx, cy, z1, z2, largo, grosor, pintor, n=8):
    for k in range(n):
        ang = k * 360 / n
        m.cubo(g, f"rayo{k}", (cx - grosor / 2, cy, z1), (cx + grosor / 2, cy + largo, z2), pintor,
               rot=(0, 0, ang), origen=(cx, cy, (z1 + z2) / 2))


def cetro(acc, nombre):
    m = _m(nombre)
    oro = metal(acc["color"] or ORO, 1, gema=acc["color2"] or "#2E8A6E")
    oro_liso = metal(acc["color"] or ORO, 2)
    madera = cuero("#5A3520", 3, costura=False)
    g = "Item/cetro"
    m.cubo(g, "vara", (-0.75, -6, -0.75), (0.75, 16, 0.75), madera)
    for k, y in enumerate((-6.5, 2, 9, 15)):
        m.cubo(g, f"anillo{k}", (-1.1, y, -1.1), (1.1, y + 1.2, 1.1), oro_liso)
    m.cubo(g, "base_sol", (-1.6, 16, -1.6), (1.6, 18, 1.6), oro_liso)
    m.cubo(g, "sol", (-2.5, 18, -0.75), (2.5, 23, 0.75), oro)
    _rayos(m, g, 0, 20.5, -0.5, 0.5, 4.5, 1.0, oro_liso, 8)
    m.cubo(g, "punta", (-0.6, 23, -0.6), (0.6, 26, 0.6), oro_liso)
    return m


def libro(acc, nombre):
    m = _m(nombre)
    tapa = acc["color"] or "#232B52"
    det = acc["color2"] or ORO
    T, D = Paleta(tapa), Paleta(det)
    forma = acc.get("forma", "diamante")

    def tapa_p(t):
        if t.cara in ("north", "south"):
            cx, cy = t.i - (t.tw - 1) / 2, t.j - (t.th - 1) / 2
            if t.i in (0, t.tw - 1) or t.j in (0, t.th - 1):
                return D.b if (t.i in (0, t.tw - 1)) == (t.j in (0, t.th - 1)) else T.o
            if forma == "diamante" and abs(cx) + abs(cy) in (2.0, 2.5, 3.0):
                return D.l
            if abs(cx) < 0.6 and abs(cy) < 0.6:
                return D.h
            return T.b if (t.i + t.j) % 5 else T.s
        if t.cara in ("east",):
            return T.s                                   # lomo
        return (236, 226, 204, 255) if t.j % 2 else (220, 208, 184, 255)   # hojas
    g = "Item/libro"
    m.cubo(g, "libro", (-3.5, 0, -1.25), (3.5, 9, 1.25), tapa_p)
    m.cubo(g, "lomo", (3.3, -0.2, -1.5), (4.1, 9.2, 1.5), cuero(tapa, 1, costura=False))
    for k, (x, y) in enumerate(((-3.6, -0.1), (2.4, -0.1), (-3.6, 7.9), (2.4, 7.9))):
        m.cubo(g, f"esquina{k}", (x, y, -1.4), (x + 1.2, y + 1.2, 1.4), metal(det, k))
    m.cubo(g, "cierre", (-4.1, 3.5, -0.6), (-3.4, 5.5, 0.6), metal(det, 9))
    return m


def mochila(acc, nombre):
    m = _m(nombre)
    c1 = acc["color"] or "#C2402E"
    c2 = acc["color2"] or "#3FA7A6"
    extra = acc.get("colores") or [ORO, "#F1E2C6"]
    g = "Item/mochila"
    cuerpo = tela(c1, [c1, extra[1] if len(extra) > 1 else c1], "manchas", c2, ("abajo", "lados"), sem=4)
    m.cubo(g, "bolso", (-3.5, 0, 0), (3.5, 8, 4), cuerpo)
    m.cubo(g, "tapa", (-3.7, 5, -0.3), (3.7, 8.4, 4.3), tela(c2, ribete=extra[0], bordes=("abajo",), sem=5))
    m.cubo(g, "bolsillo", (-2.2, 1, -0.9), (2.2, 4.2, 0), tela(c2, ribete=extra[0], bordes=("lados", "arriba"), sem=6))
    for x in (-2.3, 1.5):
        m.cubo(g, f"hebilla{x}", (x, 4.5, -0.6), (x + 0.8, 5.7, -0.2), metal(extra[0], 7))
        m.cubo(g, f"correa{x}", (x, -0.5, 4), (x + 0.8, 8.5, 4.6), cuero("#5A3520", 8))
    m.cubo(g, "manta", (-4.2, 8.4, 0.6), (4.2, 10.6, 3.4), tela(extra[1] if len(extra) > 1 else "#F1E2C6",
                                                              [extra[1] if len(extra) > 1 else "#F1E2C6", c1], "rayas", sem=9))
    for k, (x, col) in enumerate(((-3.0, extra[0]), (0.0, c2), (2.6, c1))):
        m.cubo(g, f"hilo{k}", (x, -2.5, -0.3), (x + 0.3, 0, 0), cuero("#3B2A1E", k, costura=False))
        m.cubo(g, f"totem{k}", (x - 0.6, -4.5, -0.7), (x + 0.9, -2.5, 0.4), metal(col, k, gema=c1 if k != 2 else c2))
    return m


def brujula(acc, nombre):
    m = _m(nombre)
    oro = metal(acc["color"] or ORO, 1)
    fondo = acc["color2"] or "#232B5E"
    F = Paleta(fondo)

    def esfera(t):
        if t.cara != "north":
            return F.s
        cx, cy = t.i - (t.tw - 1) / 2, t.j - (t.th - 1) / 2
        if abs(cx) < 0.6 and cy < 0:
            return (214, 64, 54, 255)                    # aguja norte
        if abs(cx) < 0.6 and cy >= 0:
            return (236, 232, 222, 255)
        if abs(abs(cx) - abs(cy)) < 0.6 and max(abs(cx), abs(cy)) > 1.4:
            return Paleta(acc["color"] or ORO).l         # rosa de los vientos
        return F.b if (t.i + t.j) % 6 else F.l
    g = "Item/brujula"
    m.cubo(g, "caja", (-3, 0, -0.75), (3, 6, 0.75), oro)
    m.cubo(g, "caja45", (-2.5, 0.5, -0.7), (2.5, 5.5, 0.7), oro, rot=(0, 0, 45), origen=(0, 3, 0))
    m.cubo(g, "esfera", (-2.3, 0.7, -0.95), (2.3, 5.3, -0.75), esfera)
    m.cubo(g, "aro", (-0.8, 6, -0.4), (0.8, 7.6, 0.4), oro)
    m.cubo(g, "aguja", (-0.25, 1.4, -1.1), (0.25, 4.6, -0.95), metal("#D64036", 3), rot=(0, 0, 22.5), origen=(0, 3, -1))
    return m


def medallon(acc, nombre):
    m = _m(nombre)
    oro = metal(acc["color"] or ORO, 1, gema=acc["color2"] or "#E8832A")
    cinta = tela(acc["color2"] or "#E8832A", sem=2, bordes=(), deshilachado=0.3)
    g = "Item/medallon"
    m.cubo(g, "disco", (-2.5, 0, -0.5), (2.5, 5, 0.5), oro)
    m.cubo(g, "disco45", (-2.1, 0.4, -0.45), (2.1, 4.6, 0.45), oro, rot=(0, 0, 45), origen=(0, 2.5, 0))
    _rayos(m, g, 0, 2.5, -0.3, 0.3, 3.6, 0.8, metal(acc["color"] or ORO, 3), 8)
    m.cubo(g, "cinta_izq", (-2.2, -6, -0.2), (-0.4, 0.5, 0.2), cinta, rot=(0, 0, -15), origen=(-1.3, 0.5, 0))
    m.cubo(g, "cinta_der", (0.4, -6, -0.2), (2.2, 0.5, 0.2), cinta, rot=(0, 0, 15), origen=(1.3, 0.5, 0))
    m.cubo(g, "lazo", (-1.5, 5, -0.4), (1.5, 6.5, 0.4), tela(acc["color2"] or "#E8832A", sem=4, bordes=()))
    return m


def espada(acc, nombre):
    m = _m(nombre)
    g = "Item/espada"
    m.cubo(g, "pomo", (-0.9, -4.5, -0.9), (0.9, -3, 0.9), metal(acc["color"] or ORO, 1))
    m.cubo(g, "mango", (-0.6, -3, -0.6), (0.6, 1, 0.6), cuero(acc["color2"] or "#5A3520", 2))
    m.cubo(g, "guarda", (-3, 1, -0.8), (3, 2.2, 0.8), metal(acc["color"] or ORO, 3))
    m.cubo(g, "hoja", (-1, 2.2, -0.35), (1, 17, 0.35), metal("#C9CED8", 4))
    m.cubo(g, "punta", (-0.7, 16, -0.3), (0.7, 18.5, 0.3), metal("#C9CED8", 5), rot=(0, 0, 45), origen=(0, 17, 0))
    return m


def baston(acc, nombre):
    m = _m(nombre)
    g = "Item/baston"
    m.cubo(g, "vara", (-0.75, -10, -0.75), (0.75, 18, 0.75), cuero(acc["color2"] or "#6B4A2A", 1, costura=False))
    m.cubo(g, "cabeza", (-1.6, 18, -1.6), (1.6, 21, 1.6), metal(acc["color"] or ORO, 2))
    m.cubo(g, "cristal", (-1.2, 21, -1.2), (1.2, 24.5, 1.2), metal("#7FD0E8", 3), rot=(0, 45, 0), origen=(0, 22.5, 0))
    return m


def farol(acc, nombre):
    m = _m(nombre)
    g = "Item/farol"
    marco = metal(acc["color"] or "#3A3A3A", 1)
    luz = metal("#FFE6A0", 2)
    m.cubo(g, "base", (-2.5, 0, -2.5), (2.5, 1, 2.5), marco)
    m.cubo(g, "luz", (-1.8, 1, -1.8), (1.8, 5, 1.8), luz)
    for k, (x, z) in enumerate(((-2.4, -2.4), (1.8, -2.4), (-2.4, 1.8), (1.8, 1.8))):
        m.cubo(g, f"poste{k}", (x, 1, z), (x + 0.6, 5, z + 0.6), marco)
    m.cubo(g, "techo", (-2.7, 5, -2.7), (2.7, 6, 2.7), marco)
    m.cubo(g, "asa", (-0.4, 6, -0.4), (0.4, 8, 0.4), marco)
    return m


FABRICAS = {"cetro": cetro, "libro": libro, "mochila": mochila, "brujula": brujula, "medallon": medallon,
            "espada": espada, "baston": baston, "farol": farol}


def construir(acc, nombre):
    f = FABRICAS.get(acc["tipo"])
    return f(acc, nombre) if f else None


__all__ = ["construir", "FABRICAS", "TRANSPARENTE"]
