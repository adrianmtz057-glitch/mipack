"""
Correctar (Correcthar), el opuesto de Revolthir, rehecho a tamano de jugador (32 de alto, cuerpo de Steve) como el
sacerdote de cristal de la referencia que paso el usuario: estilo de bloques con detalles, blanco con oro.
  CABEZA envuelta en tela blanca con la franja negra de los ojos (dos ojos celestes) y la raya que baja a la nariz;
    la BUFANDA en vueltas le tapa la boca
  CORONA blanca con filete dorado y ASTAS de bloques (dos altas adelante y dos que salen de lado y suben), con bandas
    de oro; arriba un CRISTAL grande que flota y otros chicos alrededor
  BATA blanca: los arneses de cuero cruzados en el pecho con el broche de oro, el collar de cuentas doradas, el
    CINTURON con la hebilla cuadrada de oro; la falda larga con rayas de cuero a los lados, la faldilla de enfrente
    con su orilla dorada y el borde de abajo deshilachado con manchas de oro; atras el ESTANDARTE con la runa dorada
  HOMBROS y PUNOS abultados blancos con filete dorado y guantes grises; PIERNAS gris lila y BOTAS blancas
  BACULO en la mano izquierda: mango de cuero y oro y arriba una JAULA dorada con un cristal adentro
Textura de bloques (voxel). Los cristales van sin luz horneada (brillan).
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..textura import hex_a_rgba as hex_
from .bloques import tubo, voxel
from .moles import faceta

D = 4                                   # texeles por px

BLANCO = {"s": "#C9C6CF", "b": "#E2E0E8", "l": "#F5F4F8"}
GRIS = {"s": "#A9A6B2", "b": "#C2BFCA", "l": "#D8D6DE"}
ORO = {"s": "#9C7A3C", "b": "#C29A50", "l": "#DDB86C"}
CUERO = {"s": "#6E5236", "b": "#8A6A46", "l": "#A6845A"}
GUANTE = {"s": "#3E3C44", "b": "#4E4C55", "l": "#62606A"}
CRISTAL = ((0.42, "#B9C9EC"), (0.6, "#D9E3F8"), (0.75, "#EEF3FD"), (9.0, "#FFFFFF"))
VISERA, OJO = "#1A1820", "#B9D2FF"


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _a_segmento(p, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    f = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / (ex * ex + ey * ey)))
    return math.hypot(p[0] - a[0] - ex * f, p[1] - a[1] - ey * f)


# ---------------------------------------------------------------- la cabeza, la corona y los cristales

def cabeza_pintor():
    """Tela blanca; adelante la franja negra de los ojos con los dos ojos celestes y la raya que baja a la nariz."""
    tela = voxel(BLANCO, 0.05)

    def p(t):
        if t.cara != "north":
            return tela(t)
        u, v = t.x, t.y - 24.0
        if 1.2 <= abs(u) <= 2.8 and 4.2 <= v <= 5.4:
            return hex_(OJO)
        if (3.8 <= v <= 5.8 and abs(u) < 3.4) or (abs(u) < 0.6 and 2.2 <= v < 3.8):
            return hex_(VISERA)
        return tela(t)
    return p


# las astas de la corona (las de la derecha; las de la izquierda en espejo): bloques (desde, hasta) con banda de oro
ASTAS = (((3.0, 32.2, -3.6), (4.0, 37.6, -2.6)), ((3.1, 37.6, -3.5), (3.9, 38.4, -2.7)),
         ((4.6, 32.4, -0.6), (6.2, 33.4, 0.6)), ((5.6, 33.4, -0.5), (6.6, 36.2, 0.5)),
         ((6.6, 34.4, -0.4), (7.6, 35.2, 0.4)), ((1.4, 32.4, -4.7), (2.4, 34.4, -3.9)))
CRISTALES = (((0.0, 41.0, 0.0), 1.9, 3.2), ((-7.6, 29.2, -1.0), 0.55, 0.9), ((7.4, 27.6, -0.8), 0.6, 1.0),
             ((-9.0, 22.4, 0.4), 0.45, 0.8), ((-8.0, 21.2, 1.0), 0.32, 0.55), ((9.2, 16.0, -1.4), 0.45, 0.8),
             ((-4.8, 29.6, -4.6), 0.3, 0.5), ((4.8, 29.6, -4.6), 0.3, 0.5))     # (centro, radio, medio alto)


def corona(p):
    blanco, oro = voxel(BLANCO, 0.15), voxel(ORO, 0.1)

    def banda(t):                                             # la corona blanca con su filete dorado abajo y arriba
        if t.cara == "up":                                    # arriba: solo un filete de oro en la orilla
            return oro(t) if max(abs(t.x), abs(t.z)) > 3.9 else blanco(t)
        b = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
        return oro(t) if b < 0.22 or b > 0.82 else blanco(t)

    p.caja("Head/corona", "corona", (-4.6, 30.4, -4.6), (4.6, 32.6, 4.6), banda, dens=D)
    k = 0
    for s in (1, -1):
        for (x0, y0, z0), (x1, y1, z1) in ASTAS:
            a, b = sorted((s * x0, s * x1))
            pint = oro if _azar(k * 2.1) > 0.7 else banda if y1 - y0 > 2 else blanco
            p.caja("Head/corona", f"asta{k}", (a, y0, z0), (b, y1, z1), pint, dens=D)
            k += 1
    cristal = faceta(paleta=CRISTAL, grano=0, simetrico=True)
    for i, (c, r, h) in enumerate(CRISTALES):
        p.malla("Head/cristales" if i == 0 else "Body/cristales", f"cristal{i}", geo.bipiramide(c, r, h, h, 6, 0.0),
                cristal, dens=D, luz=False)


# ---------------------------------------------------------------- el cuerpo y la ropa

def torso_pintor():
    """Bata blanca; adelante los arneses de cuero cruzados con el broche de oro y el collar de cuentas doradas; el
    cinturon de cuero con la hebilla cuadrada de oro (todo alrededor)."""
    blanco, cuero, oro = voxel(BLANCO, 0.05), voxel(CUERO, 0.05), voxel(ORO, 0.1)

    def p(t):
        if 14.4 <= t.y <= 15.8:                                 # el cinturon y su hebilla
            if t.cara == "north" and abs(t.x) < 0.9:
                return oro(t) if abs(t.x) > 0.45 or t.y < 14.75 or t.y > 15.45 else cuero(t)
            return cuero(t)
        if t.cara == "north":
            if abs(t.x) + abs(t.y - 19.6) * 0.9 < 0.8:          # el broche
                return oro(t)
            for s in (1, -1):                                   # los arneses cruzados
                if _a_segmento((t.x, t.y), (s * 3.6, 23.6), (-s * 3.0, 15.8)) < 0.45:
                    return cuero(t)
            if t.y > 22.6 and abs(abs(t.x) - (4.0 - (t.y - 22.6) * 1.2)) < 0.4:   # el collar de cuentas
                return oro(t) if math.floor(t.y * 2.5) % 2 else cuero(t)
        return blanco(t)
    return p


def falda_pintor():
    """La falda larga blanca con rayas de cuero a los lados y manchas de oro abajo."""
    blanco, cuero, oro = voxel(BLANCO, 0.05), voxel(CUERO, 0.05), voxel(ORO, 0.1)

    def p(t):
        u = t.x if t.cara in ("north", "south") else t.z
        if t.cara in ("north", "south") and abs(abs(u) - 3.0) < 0.22:
            return cuero(t)
        if t.y < 4.8 and _azar(math.floor(u * 2) * 3.7 + math.floor(t.y * 2) * 1.3) > 0.72:
            return oro(t)
        return blanco(t)
    return p


def estandarte_pintor():
    """El estandarte de la espalda: blanco con rayas de oro a los lados y la runa dorada (la cruz con su punta y el
    rombo abajo)."""
    blanco, oro, cuero = voxel(BLANCO, 0.1), voxel(ORO, 0.1), voxel(CUERO, 0.05)

    def p(t):
        if t.cara != "south":
            return blanco(t)
        x, y = t.x, t.y
        if abs(abs(x) - 2.9) < 0.3:
            return cuero(t)
        runa = ((abs(x) < 0.3 and 15.5 < y < 22.4) or (abs(x) < 1.6 and abs(y - 20.6) < 0.3)
                or (abs(abs(x) - 1.3) < 0.3 and 19.6 < y < 21.0) or 0.9 < abs(x) + abs(y - 13.0) * 0.8 < 1.5
                or (abs(x) + abs(y - 13.0) * 0.8 < 0.45))
        if runa:
            return oro(t)
        if y < 4.8 and _azar(math.floor(x * 2) * 5.1 + math.floor(y * 2) * 2.3) > 0.7:
            return oro(t)
        return blanco(t)
    return p


def baculo(p):
    """En la mano izquierda: el mango de cuero y oro que sube en diagonal y la jaula dorada con el cristal."""
    cuero, oro = voxel(CUERO, 0.05), voxel(ORO, 0.1)
    mano, arriba = (-6.0, 12.4, -2.6), (-8.6, 18.2, -3.4)
    p.malla("LeftArm/baculo", "mango", tubo(mano, arriba, 0.35, 0.35), cuero, dens=D)
    p.malla("LeftArm/baculo", "regaton", tubo((-5.4, 11.0, -2.4), mano, 0.4, 0.4), oro, dens=D)
    cx, cy, cz = -9.3, 20.1, -3.6
    h, g = 1.6, 0.22                                          # medio lado de la jaula y lo grueso de sus barras
    barras = []
    for a in (-1, 1):
        for b in (-1, 1):
            barras += [((cx - h, cy + a * h - g, cz + b * h - g), (cx + h, cy + a * h + g, cz + b * h + g)),
                       ((cx + a * h - g, cy - h, cz + b * h - g), (cx + a * h + g, cy + h, cz + b * h + g)),
                       ((cx + a * h - g, cy + b * h - g, cz - h), (cx + a * h + g, cy + b * h + g, cz + h))]
    for i, (d, e) in enumerate(barras):
        p.caja("LeftArm/baculo", f"jaula{i}", d, e, oro, rot=(0, 45, 20), piv=(cx, cy, cz), dens=D)
    p.malla("LeftArm/baculo", "cristal", geo.bipiramide((cx, cy, cz), 0.85, 1.2, 1.2, 6, 0.0),
            faceta(paleta=CRISTAL, grano=0, simetrico=True), dens=D, luz=False)


def construir():
    p = Personaje("correctar", altura=32, cabeza=8, torso=(8, 12, 4), brazo=(4, 4), pierna=(4, 4))
    blanco = voxel(BLANCO, 0.05)
    # la cabeza envuelta, la bufanda en vueltas, la corona y los cristales
    p.caja("Head/cabeza", "cabeza", (-4, 24, -4), (4, 32, 4), cabeza_pintor(), dens=D)
    p.caja("Head/bufanda", "vuelta_arriba", (-4.5, 24.6, -4.5), (4.5, 26.6, 4.5), voxel(BLANCO, 0.12), dens=D)
    p.caja("Head/bufanda", "vuelta_abajo", (-4.8, 22.4, -4.8), (4.8, 24.8, 4.6), voxel(BLANCO, -0.02), dens=D)
    corona(p)
    # el cuerpo de Steve con la bata
    p.caja("Body/cuerpo", "torso", (-4, 12, -2), (4, 24, 2), torso_pintor(), dens=D)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 4, s * 8))
        p.caja(f"{hueso}/brazo", "manga", (x1, 13.0, -2), (x2, 24, 2), blanco, dens=D)
        a, b = sorted((s * 3.8, s * 8.8))
        p.caja(f"{hueso}/brazo", "hombro", (a, 21.2, -2.6), (b, 24.8, 2.6), voxel(BLANCO, 0.15), dens=D)
        p.caja(f"{hueso}/brazo", "filete_hombro", (a, 20.9, -2.65), (b, 21.3, 2.65), voxel(ORO, 0.1), dens=D)
        a, b = sorted((s * 3.7, s * 8.6))
        p.caja(f"{hueso}/brazo", "puno", (a, 13.0, -2.5), (b, 15.4, 2.5), voxel(BLANCO, 0.1), dens=D)
        p.caja(f"{hueso}/brazo", "guante", (x1 + s * 0.1, 12.0, -1.9), (x2 - s * 0.1, 13.0, 1.9), voxel(GUANTE), dens=D)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((0, s * 4))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 2.6, -2), (x2, 12, 2), voxel(GRIS, 0.05), dens=D)
        a, b = sorted((s * -0.2, s * 4.2))
        p.caja(f"{hueso}/bota", "bota", (a, 0.0, -2.4), (b, 2.6, 2.3), voxel(BLANCO, 0.1), dens=D)
        a, b = sorted((s * -0.3, s * 4.3))
        p.caja(f"{hueso}/bota", "puno_bota", (a, 2.2, -2.5), (b, 3.1, 2.4), voxel(BLANCO, 0.2), dens=D)
    # la falda larga, la faldilla de enfrente, el borde deshilachado y el estandarte de atras
    p.caja("Body/ropa", "falda", (-4.6, 3.4, -2.6), (4.6, 15.2, 2.6), falda_pintor(), dens=D)
    oro = voxel(ORO, 0.1)

    def faldilla(t):
        b = min(t.x - t.f[0], t.t[0] - t.x)
        return oro(t) if b < 0.3 or (t.y < 4.4 and t.cara == "north") else blanco(t)
    p.caja("Body/ropa", "faldilla", (-1.7, 2.6, -2.95), (1.7, 15.2, -2.55), faldilla, dens=D)
    p.caja("Body/ropa", "estandarte", (-3.5, 2.8, 2.55), (3.5, 24.2, 3.1), estandarte_pintor(), dens=D)
    for i in range(12):                                       # el borde de abajo deshilachado (enfrente y atras)
        x = -4.6 + i * 0.78
        for lado, z0, z1 in (("f", -2.75, -2.45), ("a", 2.45, 2.75)):
            largo = 0.5 + 1.4 * _azar(i * 3.3 + (0 if lado == "f" else 50))
            pint = oro if _azar(i * 7.1 + len(lado)) > 0.7 else blanco
            p.caja("Body/ropa", f"hilacha_{lado}{i}", (x, 3.4 - largo, z0), (x + 0.7, 3.6, z1), pint, dens=D)
    baculo(p)
    return p
