"""
Revolthir, NSWY de la negacion: chibi de caos y colores calidos. Hecho a mano con el kit segun la imagen que paso el
usuario (referencias/personajes/revolthir_bufon.jpg) y las formas que marco encima con rayas blancas
(revolthir_bufon_rayas.jpg). Reglas: no es humano (cabeza-cubo naranja, sin piel), chibi de la misma altura que
Pibble (nada mas que la altura), estilo propio: carnaval caotico, ni desertico, ni japones, ni de bosque.

Formas (en bloques, como la referencia; cristales, cascabeles y estrella en low-poly):
  CABEZA-CUBO naranja con orejitas de bloque; una placa en la cara con dos huecos deja los ojos HUNDIDOS (blancos,
    grandes, con las pupilas hacia adentro: se miran entre si); bigotito en "w" en 3D con las puntas para arriba
  CORONA DE BUFON magenta bien abajo (tapa la cabeza hasta arriba de los ojos) y encima un racimo de CRISTALES de
    colores; de las esquinas de adelante salen dos puntas con cascabeles de cristal (uno grande celeste, uno rosa
    con gotita dorada)
  TORSO rojo y delgado con el cuello amarillo en punta; FALDA de solapas sueltas de distintos largos y tonos
  MANGAS amarillas con PUNOS grandes; PIERNAS verdes; BOTAS en bloque
  VARITA en la mano izquierda: baston con bandas y una estrella morada
Textura de bloques: cada px es un bloquecito de su rampa, mas claro arriba y mas oscuro abajo, con un patron fijo
(ondas suaves + una matriz de Bayer), nada al azar. El volumen lo termina la luz horneada.
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_

D = 4                                   # texeles por px

NARANJA = tonos("#E8762C")              # la cabeza
OREJA = tonos("#F0A07C")                # orejitas
MAGENTA = tonos("#C42A86")              # corona
ROSA = tonos("#E85AA8")                 # falda, cristales, cascabel chico
ROJO = tonos("#D23A30")                 # torso
AMARILLO = tonos("#F2C232")             # mangas, cuello, gotita
VERDE = tonos("#6CC23C")                # piernas, cristales, punta
GUANTE = tonos("#7A6470")               # punos
BOTA = tonos("#4A2E2C")                 # botas
MORADO = tonos("#8A4AE0")               # la estrella, cristales
CELESTE = tonos("#6AC8F0")              # cascabel grande, cristales
FUEGO = tonos("#F06A2A")                # cristales
GRIS = tonos("#6E6A78")                 # baston
OJO, PUPILA = "#FFF8EE", "#1A1218"

TOPE = 27.0                             # la cabeza va de 17 a 27: la altura de Pibble
CABEZA_Y = 17.0
PIERNAS = 9.0                           # la cadera

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def voxel(rampa, claro=0.0):
    """Textura de bloques de 1 px: cada bloque toma un tono de la rampa (sombra, base, medio, luz) segun la altura
    dentro de la pieza (mas claro arriba), unas ondas suaves y una matriz de Bayer. Siempre el mismo patron."""
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
            alto = max(1e-6, t.t[1] - t.f[1])
            r = (t.y - t.f[1]) / alto
        cu, cv = math.floor(u + 100), math.floor(v + 100)
        f = 0.5 + 0.2 * math.sin(cu * 0.9 + cv * 0.5) * math.cos(cv * 0.8 - cu * 0.35) + 0.28 * (r - 0.5) + claro
        f += ((BAYER[cv % 4][cu % 4] + 0.5) / 16 - 0.5) * 0.4
        return tonos4[0 if f < 0.22 else 1 if f < 0.6 else 2 if f < 0.8 else 3]
    return p


def _trazo(u, v, a, b, grosor):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    k = max(0.0, min(1.0, ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(u - ax - k * dx, v - ay - k * dy) <= grosor / 2


BIGOTE = [(-1.85, 2.8), (-1.45, 2.2), (-0.75, 2.2), (0.0, 2.8), (0.75, 2.2), (1.45, 2.2), (1.85, 2.8)]
OJOS_V = (3.6, 6.4)                     # alto de los ojos (desde el menton)
OJOS_U = (0.7, 3.3)                     # de donde a donde va cada ojo, desde el centro de la cara
HUNDIDO = 0.3                           # cuanto se meten los ojos: lo que mide de grueso la placa de la cara


def en_ojo(u, v):
    """Si (u, v) cae en un ojo. u: hacia la derecha de quien mira, v: desde el menton."""
    return OJOS_U[0] <= abs(u) <= OJOS_U[1] and OJOS_V[0] <= v <= OJOS_V[1]


def cara(t):
    """El frente de la cabeza, que solo se ve por los huecos de la placa: los ojos blancos con la pupila abajo y
    hacia adentro (se miran entre si)."""
    u, v = -t.x, t.y - CABEZA_Y
    if en_ojo(u, v):
        if abs(u) <= OJOS_U[0] + 1.25 and v <= OJOS_V[0] + 1.65:
            return hex_(PUPILA)
        return hex_(OJO)
    return CABEZA_TEX(t)


CABEZA_TEX = voxel(NARANJA, claro=0.14)                 # la cabeza mas clara y calida, sin manchas oscuras


def cabeza(t):
    return cara(t) if t.cara == "north" else CABEZA_TEX(t)


def placa(t):
    """La placa de la cara (0.3 de grueso) con dos huecos: por ahi se ven los ojos, hundidos."""
    if t.cara in ("north", "south") and en_ojo(-t.x, t.y - CABEZA_Y):
        return TRANSPARENTE
    return CABEZA_TEX(t)


def bigote_malla(z):
    """El bigotito en w con las puntas para arriba, en 3D: el trazo engrosado y extruido 0.35 hacia adelante."""
    w = 0.21
    pts = [(-u, CABEZA_Y + v) for u, v in BIGOTE]              # a coordenadas del mundo (x = -u)
    arriba, abajo = [], []
    for k, (x, y) in enumerate(pts):
        (xa, ya), (xb, yb) = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
        dx, dy = xb - xa, yb - ya
        largo = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / largo, dx / largo
        if ny < 0:
            nx, ny = -nx, -ny
        arriba.append((x + nx * w, y + ny * w))
        abajo.append((x - nx * w, y - ny * w))
    return geo.extruir(arriba + abajo[::-1], z - 0.35, z)


def bigote(t):
    if t.n[1] > 0.4 or t.n[2] < -0.7 and t.y > CABEZA_Y + 2.6:
        return hex_("#3A2A30")
    return hex_(PUPILA)


CORONA_Y = (TOPE - 3.1, TOPE + 0.8)     # la corona tapa la cabeza hasta arriba de los ojos


def corona(t):
    """Banda magenta de bloques con una fila de rombos claros y el borde de abajo oscuro."""
    if t.cara not in ("up", "down"):
        u = t.x if t.cara in ("north", "south") else t.z
        y0, y1 = CORONA_Y
        v = t.y - (y0 + y1) / 2 - 0.2
        if abs((u % 1.8) - 0.9) + abs(v) * 1.1 < 0.6:
            return hex_(ROSA["l"])
        if t.y < y0 + 0.5:
            return hex_(MAGENTA["s"])
    return voxel(MAGENTA)(t)


def cristal(rampa):
    """Cristal facetado: las caras que miran a la izquierda de quien mira y arriba con luz, las de atras oscuras,
    y una veta clara a lo largo de cada cara."""
    def p(t):
        n = t.n
        if n[1] > 0.55:
            return hex_(rampa["h"])
        if n[2] > 0.5:
            return hex_(rampa["s"])
        if n[0] > 0.3:
            return hex_(rampa["l"])
        return hex_(rampa["b"])
    return p


def pieza_cristal(x, y, z, r, alto, giro, lados=6):
    """Cristal: prisma de 'lados' con punta, de radio r y alto 'alto', inclinado 'giro' desde su base."""
    cuerpo = geo.loft([(y, x, z, r, r), (y + alto * 0.68, x, z, r * 0.92, r * 0.92)], lados, 30, tapa_arriba=False)
    tope = geo.piramide(geo.anillo(x, y + alto * 0.68, z, r * 0.92, r * 0.92, lados, 30), (x, y + alto, z), tapa=False)
    return geo.girar(geo.unir(cuerpo, tope), giro, (x, y, z))


def falda_solapa(t):
    """Solapa de la falda: rosa de bloques, mas oscura abajo."""
    return voxel(ROSA)(t)


def babero(t):
    """Cuello amarillo: una barra arriba y una lengueta que baja en punta al centro."""
    u, v = t.x, t.y - (CABEZA_Y - 0.8)
    if v > 0:
        return voxel(AMARILLO)(t)
    if abs(u) < 0.75 and v > -1.6 + abs(u) * 0.8:
        return voxel(AMARILLO)(t)
    return TRANSPARENTE


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


def punta(base, largo, caida, ry):
    """Punta de bufon: cono de 6 lados que sale de 'base' hacia afuera y caido ('caida' grados, como rz) y despues
    girado 'ry' grados para que salga en diagonal desde la esquina. Devuelve (malla, punta)."""
    m = geo.loft([(0.0, 0, 0, 1.2, 1.2), (largo * 0.55, 0, 0, 0.85, 0.85), (largo, 0, 0, 0.25, 0.25)], 6, 30)
    m = geo.girar(geo.girar(m, (0, 0, caida)), (0, ry, 0))
    vs, cs = geo.mover(m, base)
    tip = max(vs, key=lambda q: (q[0] - base[0]) ** 2 + (q[1] - base[1]) ** 2 + (q[2] - base[2]) ** 2)
    return (vs, cs), tip


def construir():
    p = Personaje("revolthir", altura=27, cabeza=10, torso=(7.5, 8, 4.5), brazo=(2.6, 2.6), pierna=(3.4, 3.4))
    C, T, L = p.cuello, p.tope, p.lh                           # 17, 27, 9
    assert (C, T, L) == (CABEZA_Y, TOPE, PIERNAS)

    # ================================================================ CABEZA-CUBO con OREJITAS
    p.caja("Head/cabeza", "cabeza", (-5, C, -5), (5, T, 5), cabeza, dens=D)
    p.caja("Head/cabeza", "placa", (-5, C, -5.02 - HUNDIDO), (5, CORONA_Y[0] + 0.1, -5.02), placa, dens=D)
    p.malla("Head/cabeza", "bigote", bigote_malla(-5.02 - HUNDIDO), bigote, dens=D)
    for s in (1, -1):
        x1, x2 = sorted((s * 5.0, s * 5.7))
        p.caja("Head/cabeza", f"oreja{s}", (x1, C + 3.6, -0.4), (x2, C + 5.6, 1.2), voxel(OREJA), dens=D)

    # ================================================================ CORONA baja y CRISTALES encima
    g = "Head/corona"
    y0, y1 = CORONA_Y
    p.caja(g, "corona", (-5.45, y0, -5.45), (5.45, y1, 5.45), corona, dens=D)
    cristales = [((-3.6, -2.4), 1.15, 4.6, (-8, 0, 16), VERDE), ((-1.2, -3.1), 1.0, 3.4, (-14, 0, 6), ROSA),
                 ((1.3, -2.6), 1.25, 5.0, (-10, 0, -8), FUEGO), ((3.7, -1.6), 1.0, 3.6, (-6, 0, -20), CELESTE),
                 ((-2.6, 1.0), 1.3, 5.6, (6, 0, 10), MORADO), ((0.4, 0.2), 1.1, 6.2, (2, 0, -2), VERDE),
                 ((2.8, 1.8), 1.2, 4.4, (10, 0, -14), ROSA), ((-4.0, 3.4), 0.95, 3.2, (14, 0, 20), AMARILLO),
                 ((-0.6, 3.6), 1.0, 3.8, (16, 0, 0), CELESTE), ((4.1, 3.6), 0.9, 3.0, (16, 0, -18), FUEGO)]
    for k, ((x, z), r, alto, giro, col) in enumerate(cristales):
        p.malla(g, f"cristal{k}", pieza_cristal(x, y1 - 0.3, z, r, alto, giro), cristal(col), dens=D)
    # puntas que salen de las esquinas de adelante, en diagonal, con cascabeles de cristal
    malla, tip = punta((5.2, y0 + 1.6, -5.2), 3.6, -116, 45)
    p.malla(g, "punta_der", malla, voxel(VERDE), dens=D)
    p.malla(g, "cascabel_der", geo.bipiramide((tip[0] + 0.3, tip[1] - 1.2, tip[2]), 1.25, 1.2, 1.4, lados=6, giro=30),
            cristal(CELESTE), dens=D)
    malla, tip = punta((-5.2, y0 + 1.4, -5.2), 2.6, 120, -45)
    p.malla(g, "punta_izq", malla, voxel(ROSA), dens=D)
    cas = (tip[0] - 0.2, tip[1] - 0.9, tip[2])
    p.malla(g, "cascabel_izq", geo.bipiramide(cas, 0.95, 0.9, 1.0, lados=6, giro=30), cristal(ROSA), dens=D)
    p.malla(g, "gotita", geo.bipiramide((cas[0], cas[1] - 1.5, cas[2]), 0.35, 0.35, 0.6, lados=4, giro=45),
            cristal(AMARILLO), dens=D)

    # ================================================================ TORSO delgado, CUELLO en punta y FALDA de solapas
    p.caja("Body/torso", "torso", (-3.75, L, -2.25), (3.75, C, 2.25), voxel(ROJO), dens=D)
    p.caja("Body/torso", "cuello", (-1.5, C - 2.5, -2.45), (1.5, C - 0.05, -2.25), babero, dens=D)
    # solapas: (centro en el borde de la cintura, largo, hacia donde se abren); se abren un poco hacia afuera
    solapas = []
    for k, x in enumerate((-3.0, -1.0, 1.0, 3.0)):
        # rx > 0 lleva la punta de abajo hacia adelante; rz > 0, hacia +X
        solapas.append(((x, -2.45), (1.9, 0.25), 3.9 + 0.7 * (k % 2), (20, 0, 5 * x)))       # adelante
        solapas.append(((x, 2.45), (1.9, 0.25), 4.4 - 0.6 * (k % 2), (-20, 0, 5 * x)))       # atras
    for s in (1, -1):
        solapas.append(((s * 3.95, -0.9), (0.25, 1.9), 4.2, (0, 0, 22 * s)))                 # costados
        solapas.append(((s * 3.95, 0.9), (0.25, 1.9), 3.6, (0, 0, 22 * s)))
    for k, ((x, z), (w, d), largo, giro) in enumerate(solapas):
        arriba = L + 1.2
        p.caja("Body/falda", f"solapa{k}", (x - w / 2, arriba - largo, z - d / 2), (x + w / 2, arriba, z + d / 2),
               voxel(ROSA if k % 3 else MAGENTA), rot=giro, piv=(x, arriba, z), dens=D)

    # ================================================================ BRAZOS: mangas amarillas y punos grandes
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.75, s * 6.35))
        g1, g2 = sorted((s * 3.5, s * 6.6))
        p.caja(f"{hueso}/brazo", "manga", (x1, L + 2.9, -1.3), (x2, C, 1.3), voxel(AMARILLO), dens=D)
        p.caja(f"{hueso}/brazo", "puno", (g1, L - 0.3, -1.55), (g2, L + 3.0, 1.55), voxel(GUANTE), dens=D)

    # ================================================================ VARITA de estrella en la mano izquierda
    g = "LeftArm/varita"
    piv = (-5.05, L + 1.4, -2.05)
    giro = dict(rot=(0, 0, 12), piv=piv)
    p.caja(g, "baston", (-5.3, L - 1.4, -2.3), (-4.8, L + 10.5, -1.8), baston, dens=D, **giro)
    cx, cy = -5.05, L + 12.3
    malla = geo.extruir(estrella(cx, cy, 2.1, 0.95), -2.45, -1.65)
    p.malla(g, "estrella", geo.girar(malla, (0, 0, 12), piv), pintor_estrella(cx, cy), dens=D)

    # ================================================================ PIERNAS verdes y BOTAS en bloque
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.15, s * 3.55))
        b1, b2 = sorted((s * 0.0, s * 3.75))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 2.6, -1.7), (x2, L, 1.7), voxel(VERDE), dens=D)
        p.caja(f"{hueso}/bota", "bota", (b1, 0.0, -2.5), (b2, 2.8, 2.0), bota, dens=D)
    return p
