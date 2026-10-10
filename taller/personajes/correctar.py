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
FALDA_GRIS = {"s": "#7F7B90", "b": "#9894A9", "l": "#B0ADC0"}
ORO = {"s": "#9C7A3C", "b": "#C29A50", "l": "#DDB86C"}
CUERO = {"s": "#6E5236", "b": "#8A6A46", "l": "#A6845A"}
GUANTE = {"s": "#3E3C44", "b": "#4E4C55", "l": "#62606A"}
CREMA = {"s": "#BDB4A2", "b": "#D6CEBE", "l": "#E8E2D6"}
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
    """La camisa crema; adelante los arneses de cuero cruzados (se asoman en la V de la capucha)."""
    crema, cuero = voxel(CREMA, 0.05), voxel(CUERO, 0.05)

    def p(t):
        if t.cara == "north":
            for s in (1, -1):
                if _a_segmento((t.x, t.y), (s * 3.0, 23.8), (-s * 2.6, 15.6)) < 0.3:
                    return cuero(t)
        return crema(t)
    return p


def cinturon_pintor(t):
    """El cinturon de cuero con la hebilla cuadrada de oro adelante."""
    if t.cara == "north" and abs(t.x) < 0.9:
        if abs(t.x) > 0.45 or t.y < 14.75 or t.y > 15.45:
            return voxel(ORO, 0.1)(t)
    return voxel(CUERO, 0.05)(t)


def runa(x, y):
    """La runa dorada de la espalda de la bata: la cruz con sus brazos que suben y el rombo de abajo."""
    return ((abs(x) < 0.3 and 8.0 < y < 14.6) or (abs(x) < 1.6 and abs(y - 12.8) < 0.3)
            or (abs(abs(x) - 1.3) < 0.3 and 11.8 < y < 13.2) or 0.9 < abs(x) + abs(y - 6.2) * 0.8 < 1.5
            or abs(x) + abs(y - 6.2) * 0.8 < 0.45)


# ---------------------------------------------------------------- la bata larga, la falda y la capucha en V

# la bata larga abierta adelante, en A: (y, medio ancho, medio hondo adelante, medio hondo atras, medio ancho de la
# abertura); arriba la tapa la capucha en V, abajo se abre y deja ver la falda
BATA = ((24.4, 4.55, 2.55, 2.55, 2.4), (20.0, 4.5, 2.5, 2.55, 2.0), (15.6, 4.6, 2.6, 2.65, 1.9),
        (10.0, 5.1, 3.05, 3.1, 2.4), (6.0, 5.6, 3.45, 3.5, 3.0), (3.4, 5.9, 3.7, 3.8, 3.4))
GROSOR_BATA = 0.35
PLIEGUE_BATA = 0.7
# la falda gris (cerrada) de la cintura a los tobillos: (y, medio ancho, medio hondo)
FALDA = ((15.4, 4.3, 2.3), (11.0, 4.55, 2.55), (6.0, 4.85, 2.85), (2.5, 5.0, 3.0))
# la capucha: la tela en V (de la punta en el pecho, por los hombros, a la espalda) como un rollo de tela, y atras
# la capucha doblada que cuelga: anillos (y, medio ancho, cuanto sale de la espalda)
CAMINO_V = ((0.25, 17.8, -2.75), (1.7, 20.6, -2.75), (3.1, 23.0, -2.65), (4.6, 24.9, -1.9), (5.2, 25.4, 0.0),
            (4.7, 25.0, 2.1), (3.4, 24.2, 3.1), (0.0, 23.9, 3.4))
CAPUCHA = ((24.5, 4.0, 3.0), (23.0, 3.9, 2.6), (21.0, 3.4, 2.2), (19.0, 2.6, 1.6), (17.2, 1.6, 1.0), (15.6, 0.7, 0.45),
           (14.8, 0.15, 0.15))


def _abertura(y):
    for (y0, *_, x0), (y1, *_, x1) in zip(BATA, BATA[1:]):
        if y >= y1:
            return x0 + (x1 - x0) * (y0 - min(y, y0)) / (y0 - y1)
    return BATA[-1][-1]


def bata_pintor():
    """Blanca con el forro gris; el filete de oro en las orillas de la abertura y el borde de abajo con su greca, y
    atras la runa dorada."""
    blanco, forro, oro = voxel(BLANCO, 0.05), voxel(GRIS, -0.15), voxel(ORO, 0.1)

    def p(t):
        afuera = t.n[0] * t.x + t.n[2] * t.z
        if afuera < -0.35 * math.hypot(t.x, t.z):              # el forro
            return forro(t)
        if abs(afuera) < 0.2 * math.hypot(t.x, t.z) and t.z < -1.0:   # el canto de la abertura
            return oro(t)
        abajo = t.y - BATA[-1][0]
        if abajo < 0.9 and not (0.35 < abajo < 0.6 and math.floor(t.x * 1.5 + t.z * 1.5) % 3 == 0):
            return oro(t)
        if t.z < -1.0 and abs(abs(t.x) - _abertura(t.y)) < 0.5:
            return oro(t)
        if t.n[2] > 0.5 and runa(t.x, t.y):
            return oro(t)
        return blanco(t)
    return p


def falda_pintor():
    """La falda gris con un galon dorado abajo."""
    gris, oro = voxel(FALDA_GRIS, 0.05), voxel(ORO, 0.1)
    return lambda t: oro(t) if FALDA[-1][0] + 0.25 < t.y < FALDA[-1][0] + 0.75 else gris(t)


def capucha_pintor():
    """La tela de la capucha blanca con el filete dorado en la orilla de la V y el hueco de la capucha (arriba)
    en sombra."""
    blanco, oro, hueco = voxel(BLANCO, 0.1), voxel(ORO, 0.1), voxel(FALDA_GRIS, -0.3)

    def p(t):
        if t.cara == "up" and t.z > 2.4 and t.y > CAPUCHA[0][0] - 0.05:   # la boca de la capucha doblada
            w = CAPUCHA[0][1] * (1 - 0.25 * max(0.0, (t.z - 2.62) / CAPUCHA[0][2]))
            return oro(t) if abs(t.x) > w - 0.35 or t.z > 2.62 + CAPUCHA[0][2] * 0.85 else hueco(t)
        return blanco(t)
    return p, oro


def _rollo(camino, ancho, grueso, lados=8):
    """Un rollo de tela que sigue un camino pegado al cuerpo: cada corte es un ovalo (ancho sobre el cuerpo, grueso
    hacia afuera) apoyado en el cuerpo. ancho y grueso: funciones del punto. Con tapas en las puntas."""
    n = len(camino)
    vs, anillos = [], []
    for i, c in enumerate(camino):
        a, b = camino[max(0, i - 1)], camino[min(n - 1, i + 1)]
        t = _norm(tuple(b[k] - a[k] for k in range(3)))
        fuera = _norm((c[0] / 4.5, (c[1] - 22.0) / 3.0, c[2] / 2.6))
        k = sum(fuera[j] * t[j] for j in range(3))
        nn = _norm(tuple(fuera[j] - t[j] * k for j in range(3)))
        bb = (t[1] * nn[2] - t[2] * nn[1], t[2] * nn[0] - t[0] * nn[2], t[0] * nn[1] - t[1] * nn[0])
        w, h = ancho(c), grueso(c)
        centro = tuple(c[j] + nn[j] * h * 0.7 for j in range(3))
        anillo = []
        for q in range(lados):
            f = 2 * math.pi * q / lados
            hh = h * math.cos(f) * (1.0 if math.cos(f) > 0 else 0.45)          # pegado al cuerpo por dentro
            anillo.append(len(vs))
            vs.append(tuple(centro[j] + nn[j] * hh + bb[j] * w * math.sin(f) for j in range(3)))
        anillos.append((anillo, centro))
    cs = []
    for (a, _), (b, _) in zip(anillos, anillos[1:]):
        for q in range(lados):
            cs.append((a[q], a[(q + 1) % lados], b[(q + 1) % lados], b[q]))
    # que las caras miren hacia afuera del rollo
    c0, c1 = anillos[0][1], anillos[1][1]
    cara = [vs[i] for i in cs[0]]
    medio = tuple((c0[j] + c1[j]) / 2 for j in range(3))
    pc = tuple(sum(p[j] for p in cara) / 4 for j in range(3))
    if sum(geo.normal(cara)[j] * (pc[j] - medio[j]) for j in range(3)) < 0:
        cs = [tuple(reversed(c)) for c in cs]
    # las tapas de las puntas
    primero, ultimo = anillos[0][0], anillos[-1][0]
    for anillo, otro in ((primero, anillos[1][1]), (ultimo, anillos[-2][1])):
        tapa = list(anillo)
        cen = tuple(sum(vs[i][j] for i in tapa) / lados for j in range(3))
        if sum(geo.normal([vs[i] for i in tapa])[j] * (cen[j] - otro[j]) for j in range(3)) < 0:
            tapa.reverse()
        cs.append(tuple(tapa))
    return vs, cs


def _norm(v):
    largo = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / largo for c in v)


def _losa(x0, x1, arriba, abajo, g):
    """Una tira de tela (x0..x1) de arriba=(y, z) a abajo=(y, z), de grueso g hacia atras (+Z)."""
    (ya, za), (yb, zb) = arriba, abajo
    vs = [(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb),
          (x0, ya, za + g), (x1, ya, za + g), (x1, yb, zb + g), (x0, yb, zb + g)]
    cs = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 5, 1, 0), (3, 2, 6, 7), (4, 0, 3, 7), (1, 5, 6, 2)]
    return vs, cs


def bata_y_falda(p):
    from .moles import _suave
    from .pibble import _plegar, _subdividir, _u_bata, _pisos
    g = "Body/ropa"
    # la falda gris (con pliegues suaves) y el cinturon encima
    aros = []
    for i, (y, mx, mz) in enumerate(_pisos(FALDA, 2)):
        c = 0.3 * min(mx, mz)
        aro = [(mx, y, -mz + c), (mx - c, y, -mz), (-mx + c, y, -mz), (-mx, y, -mz + c), (-mx, y, mz - c),
               (-mx + c, y, mz), (mx - c, y, mz), (mx, y, mz - c)]
        f = (FALDA[0][0] - y) / (FALDA[0][0] - FALDA[-1][0])
        aros.append(_plegar(_subdividir(aro, 2, cerrado=True), 0.35 * f, piso=i, cerrado=True)[0])
    p.malla(g, "falda", geo.loft_puntos(aros), falda_pintor(), dens=D)
    p.caja(g, "cinturon", (-4.4, 14.4, -2.42), (4.4, 15.8, 2.42), cinturon_pintor, dens=D)
    # la faldilla blanca de enfrente con su orilla dorada (cuelga del cinturon sobre la falda)
    blanco, oro = voxel(BLANCO, 0.1), voxel(ORO, 0.1)

    def faldilla(t):
        b = min(t.x + 1.7, 1.7 - t.x)
        return oro(t) if b < 0.3 or (t.y < 4.4 and t.cara == "north") else blanco(t)
    p.malla(g, "faldilla", _losa(-1.7, 1.7, (14.6, -2.68), (3.0, -3.25), 0.22), faldilla, dens=D)
    # la bata larga: la U abierta adelante, con grueso y pliegues abajo
    anillos = []
    for i, (y, mx, mzf, mzb, xo) in enumerate(_pisos(BATA, 2)):
        f = max(0.0, (16.0 - y) / (16.0 - BATA[-1][0]))         # sin pliegues arriba de la cintura
        fuera, ns = _plegar(_subdividir(_u_bata(y, mx, mzf, mzb, xo), 2), PLIEGUE_BATA * f, piso=i)
        dentro = [(x - nx * GROSOR_BATA, yy, z - nz * GROSOR_BATA) for (x, yy, z), (nx, nz) in zip(fuera, ns)]
        anillos.append(fuera + dentro[::-1])
    p.malla(g, "bata", geo.loft_puntos(anillos[::-1]), bata_pintor(), dens=D)
    # la capucha: la tela en V que va del pecho a la espalda por los hombros, y atras la capucha doblada
    tela, oro = capucha_pintor()
    camino = _suave([(-x, y, z) for x, y, z in CAMINO_V][::-1] + list(CAMINO_V), 3)   # de la punta izq. a la der.
    ancho = lambda c: 0.95 + 0.45 * max(0.0, min(1.0, (c[2] + 1.0) / 4.4))      # noqa: E731
    grueso = lambda c: 0.42 + 0.5 * max(0.0, min(1.0, (c[2] + 1.0) / 4.4))     # noqa: E731
    p.malla(g, "capucha_v", _rollo(camino, ancho, grueso), tela, dens=D)
    aros = []
    for y, w, sale in CAPUCHA:
        z0 = 2.62
        aros.append([(w, y, z0 + sale * 0.45), (w * 0.85, y, z0), (-w * 0.85, y, z0), (-w, y, z0 + sale * 0.45),
                     (-w * 0.75, y, z0 + sale * 0.92), (0.0, y, z0 + sale), (w * 0.75, y, z0 + sale * 0.92)])
    p.malla(g, "capucha", geo.loft_puntos(aros[::-1]), tela, dens=D)
    # el broche de oro donde se juntan las dos puntas de la V
    p.malla(g, "broche", geo.bipiramide((0.0, 18.3, -3.35), 0.55, 0.7, 0.7, 4, 45.0), oro, dens=D)


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
    # la cabeza envuelta, la vuelta de la bufanda (tapa la boca), la corona y los cristales
    p.caja("Head/cabeza", "cabeza", (-4, 24, -4), (4, 32, 4), cabeza_pintor(), dens=D)
    p.caja("Head/bufanda", "vuelta", (-4.5, 24.2, -4.5), (4.5, 26.6, 4.5), voxel(BLANCO, 0.12), dens=D)
    corona(p)
    # el cuerpo de Steve con la camisa, las mangas abultadas y las botas
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
    # la falda, el cinturon, la faldilla, la bata larga y la capucha en V
    bata_y_falda(p)
    baculo(p)
    return p
