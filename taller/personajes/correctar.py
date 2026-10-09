"""
Correctar, el opuesto de Revolthir: chibi del orden y de los colores frios. Armado sobre el mismo mundo de bloques que
Revolthir (misma escala, misma cabeza-cubo con placa y ojos hundidos, mismos cristales en low-poly), pero al reves en
todo: donde Revolthir es caos, asimetria y arcoiris calido, Correctar es simetria, angulos rectos y una paleta
corta (azul, marino, blanco, plata y un solo toque de oro). Reglas: no es humano (cabeza-cubo azul, sin piel), chibi
de la misma altura que Pibble (nada mas que la altura), estilo propio: ni desertico, ni japones, ni de bosque.

Formas:
  CABEZA-CUBO azul cielo sin orejas y sin boca; la placa de la cara deja los ojos HUNDIDOS, iguales a los de
    Revolthir (grandes, separados, la pupila hacia adentro), pero con la pupila un poco mas arriba
  CORONA de plata ALTA y prolija con una fila de cuadraditos; encima cinco CRISTALES de hielo derechos, de seccion
    cuadrada: uno alto al centro y cuatro iguales en las esquinas. Atras, un HALO CUADRADO de plata que flota
  TORSO marino con cuello blanco; CINTURON de plata con hebilla cuadrada de oro; FALDA recta de tablas parejas,
    todas del mismo largo, sin abrirse
  MANGAS blancas con hombreras y punos de plata; GUANTES marino del ancho de la manga (nada de punos gigantes)
  PIERNAS marino y BOTAS blancas con suela de plata
  VARITA igual a la de Revolthir (baston con bandas y estrella morada), en espejo: en la mano derecha
Textura de bloques ordenada: cada px es un bloquecito de su rampa en bandas de altura (claro arriba, oscuro abajo) y
un damero fijo de 2 x 2: una grilla, sin ondas. El volumen lo termina la luz horneada.
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .revolthir import (CABEZA_Y, HUNDIDO, PIERNAS, TOPE, baston, color, en_ojo, estrella, pintor_estrella,
                        OJOS_U, OJOS_V)

D = 4                                   # texeles por px

CIELO = tonos("#5F9BE8")                # la cabeza
MARINO = tonos("#22336E")               # torso, guantes, piernas
AZUL = tonos("#3D62BE")                 # falda
BLANCO = tonos("#E6ECF5")               # mangas, cuello, botas
PLATA = tonos("#A9B4C8")                # corona, halo, cinturon, punos, cetro
HIELO = tonos("#9FDCFF")                # cristales
ORO = tonos("#E8BE48")                  # hebilla y esquinas del halo
OJO, PUPILA = "#F4F9FF", "#0E1630"
PUPILA_ARRIBA = 0.6                     # cuanto sube la pupila respecto de la de Revolthir


def orden(rampa, claro=0.0, alto=None):
    """Textura de bloques de 1 px ordenada: tono de la rampa (sombra, base, medio, luz) segun la altura dentro de la
    pieza (mas claro arriba) y un damero fijo de 2 x 2 px. Lo contrario de las ondas de Revolthir: una grilla.
    alto=(y0, y1): la altura se mide en ese tramo y no en la pieza, para que dos piezas pegadas se vean como una."""
    s, b, l = hex_(rampa["s"]), hex_(rampa["b"]), hex_(rampa["l"])
    medio = tuple((x + y) // 2 for x, y in zip(b, l))
    tonos4 = (s, b, medio, l)

    def p(t):
        if t.cara in ("up", "down"):
            u, v = t.x, t.z
            r = 1.0 if t.cara == "up" else 0.0
        else:
            u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
            v = t.y
            y0, y1 = alto or (t.f[1], t.t[1])
            r = (t.y - y0) / max(1e-6, y1 - y0)
        cu, cv = math.floor(u + 100), math.floor(v + 100)
        f = 0.48 + 0.34 * (r - 0.5) + claro + (0.06 if (cu // 2 + cv // 2) % 2 else -0.06)
        return tonos4[0 if f < 0.2 else 1 if f < 0.6 else 2 if f < 0.82 else 3]
    return p


def cara(t):
    """El frente de la cabeza, que solo se ve por los huecos de la placa: los ojos de Revolthir (blancos, la pupila
    hacia adentro), pero con la pupila un poco mas arriba: deja una franja blanca abajo."""
    u, v = -t.x, t.y - CABEZA_Y
    if en_ojo(u, v):
        if abs(u) <= OJOS_U[0] + 1.25 and OJOS_V[0] + PUPILA_ARRIBA <= v <= OJOS_V[0] + PUPILA_ARRIBA + 1.65:
            return hex_(PUPILA)
        return hex_(OJO)
    return CABEZA_TEX(t)


CABEZA_TEX = orden(CIELO, claro=0.1, alto=(CABEZA_Y, TOPE))   # la placa y el cubo, como una sola pieza


def cabeza(t):
    return cara(t) if t.cara == "north" else CABEZA_TEX(t)


def placa(t):
    """La placa de la cara con dos huecos: por ahi se ven los ojos, hundidos."""
    if t.cara in ("north", "south") and en_ojo(-t.x, t.y - CABEZA_Y):
        return TRANSPARENTE
    return CABEZA_TEX(t)


CORONA_Y = (TOPE - 1.6, TOPE + 1.3)     # corona alta: arriba de la frente, no tapa la cara


def corona(t):
    """Banda de plata con una fila pareja de cuadraditos marino y los bordes de arriba y abajo marcados."""
    y0, y1 = CORONA_Y
    if t.cara not in ("up", "down"):
        u = t.x if t.cara in ("north", "south") else t.z
        v = t.y - (y0 + y1) / 2
        if abs((u + 0.9) % 1.8 - 0.9) < 0.38 and abs(v) < 0.38:
            return hex_(MARINO["b"])
        if t.y < y0 + 0.35:
            return hex_(PLATA["s"])
        if t.y > y1 - 0.3:
            return hex_(PLATA["l"])
        return hex_(PLATA["b"])
    return orden(PLATA)(t)


def cristal_cuadrado(x, y, z, r, alto):
    """Cristal derecho de seccion cuadrada (caras alineadas con los ejes) y punta de piramide."""
    cuerpo = geo.loft([(y, x, z, r, r), (y + alto * 0.72, x, z, r, r)], 4, 45, tapa_arriba=False)
    tope = geo.piramide(geo.anillo(x, y + alto * 0.72, z, r, r, 4, 45), (x, y + alto, z), tapa=False)
    return geo.unir(cuerpo, tope)


def hielo(t):
    """Cristal de hielo: arriba y la cara que mira a la luz claras, atras oscuro, y una veta clara al medio de cada
    cara."""
    n = t.n
    if n[1] > 0.4:
        return hex_(HIELO["h"])
    if n[2] > 0.5:
        return hex_(HIELO["s"])
    if n[0] > 0.5:
        return hex_(HIELO["l"])
    return hex_(HIELO["b"])


def falda(t):
    """Falda recta de tablas parejas de 1 px: cada tabla con su mitad clara y su mitad en sombra (el pliegue), todas
    iguales, y un ruedo blanco abajo."""
    if t.cara in ("up", "down"):
        return hex_(AZUL["s"])
    if t.y < t.f[1] + 0.5:
        return hex_(BLANCO["b"] if t.y > t.f[1] + 0.12 else BLANCO["s"])
    u = t.x if t.cara in ("north", "south") else t.z
    fr = (u + 100) % 1.0
    r = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    if fr < 0.25:
        return hex_(AZUL["s"])
    if fr < 0.62:
        return hex_(AZUL["l"] if r > 0.82 else AZUL["b"])
    return hex_(AZUL["b"] if r > 0.82 else AZUL["s2"] if r < 0.2 else AZUL["s"])


def bota(t):
    if t.y < 0.5:
        return hex_(PLATA["l"] if t.cara != "down" else PLATA["s"])
    if 1.9 < t.y < 2.25 and t.cara != "up":
        return hex_(MARINO["b"])
    return orden(BLANCO)(t)


def construir():
    p = Personaje("correctar", altura=27, cabeza=10, torso=(7.5, 8, 4.5), brazo=(2.6, 2.6), pierna=(3.4, 3.4))
    C, T, L = p.cuello, p.tope, p.lh                           # 17, 27, 9
    assert (C, T, L) == (CABEZA_Y, TOPE, PIERNAS)

    # ================================================================ CABEZA-CUBO con los ojos hundidos, sin boca
    # el cubo empieza HUNDIDO mas atras y la placa queda al ras del frente: la cabeza mide 10 justos y no se ve una
    # lamina aparte desde abajo ni de costado
    p.caja("Head/cabeza", "cabeza", (-5, C, -5 + HUNDIDO), (5, T, 5), cabeza, dens=D)
    p.caja("Head/cabeza", "placa", (-5, C, -5), (5, CORONA_Y[0] + 0.1, -5 + HUNDIDO - 0.02), placa, dens=D)

    # ================================================================ CORONA alta, CRISTALES derechos y HALO cuadrado
    g = "Head/corona"
    y0, y1 = CORONA_Y
    p.caja(g, "corona", (-5.4, y0, -5.4), (5.4, y1, 5.4), corona, dens=D)
    p.malla(g, "cristal_centro", cristal_cuadrado(0.0, y1 - 0.3, 0.0, 1.25, 6.0), hielo, dens=D)
    for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        p.malla(g, f"cristal{k}", cristal_cuadrado(sx * 3.8, y1 - 0.3, sz * 3.8, 0.8, 3.2), hielo, dens=D)
    # halo: un marco cuadrado de plata que flota atras, a la altura de la corona (enmarca los cristales, no la cara),
    # con un cubito de oro en cada esquina
    hx, hy0, hy1, hg, hz = 6.3, T - 1.0, T + 8.4, 0.6, (5.9, 6.5)
    for nombre, (a, b) in {"arriba": ((-hx, hy1 - hg), (hx, hy1)),
                           "abajo": ((-hx, hy0), (hx, hy0 + hg)),
                           "der": ((hx - hg, hy0 + hg), (hx, hy1 - hg)),
                           "izq": ((-hx, hy0 + hg), (-hx + hg, hy1 - hg))}.items():
        p.caja(g, f"halo_{nombre}", (a[0], a[1], hz[0]), (b[0], b[1], hz[1]), orden(PLATA, claro=0.1), dens=D)
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        cx, cy = sx * (hx - hg / 2), (hy1 if sy > 0 else hy0) - sy * hg / 2
        p.caja(g, f"halo_oro{k}", (cx - 0.55, cy - 0.55, hz[0] - 0.15), (cx + 0.55, cy + 0.55, hz[1] + 0.15),
               color(ORO["b"]), dens=D)

    # ================================================================ TORSO marino, cuello blanco y cinturon
    p.caja("Body/torso", "torso", (-3.75, L, -2.25), (3.75, C, 2.25), orden(MARINO), dens=D)
    p.caja("Body/torso", "cuello", (-3.95, C - 1.0, -2.45), (3.95, C, 2.45), orden(BLANCO, claro=0.1), dens=D)
    p.caja("Body/torso", "cinturon", (-3.95, L + 0.5, -2.45), (3.95, L + 1.4, 2.45), orden(PLATA), dens=D)
    p.caja("Body/torso", "hebilla", (-0.7, L + 0.35, -2.65), (0.7, L + 1.55, -2.4), color(ORO["b"]), dens=D)
    # falda recta: una sola pieza que baja derecho, sin abrirse
    p.caja("Body/falda", "falda", (-4.0, L - 3.2, -2.5), (4.0, L + 0.6, 2.5), falda, dens=D)

    # ================================================================ BRAZOS: mangas blancas, hombreras y guantes
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.75, s * 6.35))
        p.caja(f"{hueso}/brazo", "manga", (x1, L + 2.6, -1.3), (x2, C, 1.3), orden(BLANCO), dens=D)
        h1, h2 = sorted((s * 3.6, s * 6.55))
        p.caja(f"{hueso}/brazo", "hombrera", (h1, C - 0.5, -1.5), (h2, C + 0.35, 1.5), orden(PLATA, claro=0.1),
               dens=D)
        p1, p2 = sorted((s * 3.65, s * 6.45))
        p.caja(f"{hueso}/brazo", "puno", (p1, L + 2.2, -1.4), (p2, L + 2.9, 1.4), orden(PLATA), dens=D)
        g1, g2 = sorted((s * 3.85, s * 6.25))
        p.caja(f"{hueso}/brazo", "guante", (g1, L - 0.2, -1.2), (g2, L + 2.3, 1.2), orden(MARINO, claro=0.08),
               dens=D)

    # ================================================================ VARITA de estrella, la de Revolthir en espejo
    g = "RightArm/varita"
    piv = (5.05, L + 1.4, -2.05)
    giro = dict(rot=(0, 0, -12), piv=piv)                      # rz < 0: la punta va hacia +X, afuera de la cabeza
    p.caja(g, "baston", (4.8, L - 1.4, -2.3), (5.3, L + 10.5, -1.8), baston, dens=D, **giro)
    cx, cy = 5.05, L + 12.3
    malla = geo.girar(geo.extruir(estrella(cx, cy, 2.1, 0.95), -2.45, -1.65), (0, 0, -12), piv)
    a = math.radians(-12)                                      # el centro de la estrella ya girada, para su brillo
    cx, cy = piv[0] - (cy - piv[1]) * math.sin(a), piv[1] + (cy - piv[1]) * math.cos(a)
    p.malla(g, "estrella", malla, pintor_estrella(cx, cy), dens=D)

    # ================================================================ PIERNAS marino y BOTAS blancas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.15, s * 3.55))
        b1, b2 = sorted((s * 0.05, s * 3.65))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 2.6, -1.7), (x2, L, 1.7), orden(MARINO), dens=D)
        p.caja(f"{hueso}/bota", "bota", (b1, 0.0, -2.3), (b2, 2.6, 1.9), bota, dens=D)
    return p
