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
from .bloques import ojo_kemira, voxel
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
VISERA = "#1A1820"
OJOS = {"blanco": "#E8E2D8", "blanco_s": "#C2B8AC", "iris": "#6E9AD0", "iris_s": "#4F78AE", "iris_c": "#9CC0EC",
        "pupila": "#1E2E52", "tapado": "#38527E", "pestana": "#1C1A22"}


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _a_segmento(p, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    f = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / (ex * ex + ey * ey)))
    return math.hypot(p[0] - a[0] - ex * f, p[1] - a[1] - ey * f)


# ---------------------------------------------------------------- la cabeza, la corona y los cristales

def cabeza_pintor():
    """La cabeza: tela blanca; adelante, en la rendija en T de la mascara, lo oscuro y debajo los ojos como los de
    Kemira (el blanco afuera y el iris celeste con la pupila hacia adentro: bizcos)."""
    tela, visera = voxel(BLANCO, 0.05), hex_(VISERA)
    cols = {k: hex_(c) for k, c in OJOS.items()}

    def p(t):
        if t.cara != "north":
            return tela(t)
        u, v = abs(t.x), t.y - 24.0
        if (3.8 <= v <= 5.8 and u < 3.55) or (u < 0.6 and 2.2 <= v < 3.8):
            parte = ojo_kemira(t.x, math.floor((t.y - 27.95) * 8))
            return cols[parte] if parte else visera
        return tela(t)
    return p


# la mascara de enfrente (lo demas de la cabeza es plano): las placas que dejan la rendija en T (ojos y nariz) con
# su ceja y sus bordes salidos: (nombre, desde, hasta)
CASCO = (("frente", (-4.0, 29.8, -4.75), (4.0, 30.6, -4.0)),
         ("ceja", (-3.95, 29.6, -5.05), (3.95, 30.15, -4.7)),
         ("lado_d", (3.55, 27.8, -4.75), (4.0, 29.8, -4.0)),
         ("lado_i", (-4.0, 27.8, -4.75), (-3.55, 29.8, -4.0)),
         ("borde_d", (3.55, 27.45, -5.05), (3.95, 30.15, -4.7)),
         ("borde_i", (-3.95, 27.45, -5.05), (-3.55, 30.15, -4.7)),
         ("repisa_d", (0.6, 27.45, -5.05), (3.95, 27.9, -4.7)),
         ("repisa_i", (-3.95, 27.45, -5.05), (-0.6, 27.9, -4.7)),
         ("mejilla_d", (0.6, 24.0, -4.75), (4.0, 27.8, -4.0)),
         ("mejilla_i", (-4.0, 24.0, -4.75), (-0.6, 27.8, -4.0)),
         ("barbilla", (-0.6, 24.0, -4.75), (0.6, 26.2, -4.0)))


def casco(p):
    blanco, borde = voxel(BLANCO, 0.1), voxel(BLANCO, 0.25)
    for nombre, d, h in CASCO:
        p.caja("Head/casco", nombre, d, h, borde if d[2] < -5 else blanco, dens=D)


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

    p.caja("Head/corona", "corona", (-4.75, 30.4, -4.9), (4.75, 32.6, 4.75), banda, dens=D)
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
    """La camisa crema (se ve en la V de la capucha y en la abertura de la bata)."""
    return voxel(CREMA, 0.05)


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
CAPUCHA = ((24.5, 4.0, 3.0), (23.0, 3.9, 2.6), (21.0, 3.4, 2.2), (19.4, 2.6, 1.6), (18.0, 1.6, 1.0), (17.0, 0.7, 0.45),
           (16.4, 0.15, 0.15))


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


def _rollo(camino, ancho, grueso, lados=14):
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
    # el cinturon de cuero que cine la bata, con la hebilla cuadrada de oro salida
    p.caja(g, "cinturon", (-4.85, 14.3, -2.85), (4.85, 15.9, 2.9), voxel(CUERO, 0.05), dens=D)
    oro_h = voxel(ORO, 0.15)
    for nombre, d, h in (("arriba", (-1.05, 15.7, -3.2), (1.05, 16.1, -2.8)), ("abajo", (-1.05, 14.1, -3.2), (1.05, 14.5, -2.8)),
                         ("izq", (-1.05, 14.1, -3.2), (-0.65, 16.1, -2.8)), ("der", (0.65, 14.1, -3.2), (1.05, 16.1, -2.8)),
                         ("pua", (-0.12, 14.5, -3.05), (0.12, 15.7, -2.8))):
        p.caja(g, f"hebilla_{nombre}", d, h, oro_h, dens=D)
    # la capucha: la tela en V que va del pecho a la espalda por los hombros, y atras la capucha doblada
    tela, oro = capucha_pintor()
    camino = _suave([(-x, y, z) for x, y, z in CAMINO_V][::-1] + list(CAMINO_V), 6)   # de la punta izq. a la der.
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


def detalles(p):
    """Los detalles: la gema de la corona en su placa de oro, los cristales en las hombreras, los aros de oro de los
    punos, el colgante de cristal del broche de la V, el libro con esquinas de oro colgando del cinturon, el emblema
    de la faldilla, la borla de oro en la punta de la capucha y las botas con puntera y aro de oro."""
    oro = voxel(ORO, 0.15)
    cristal = faceta(paleta=CRISTAL, grano=0, simetrico=True)
    g = "Body/ropa"
    # la gema de enfrente de la corona
    p.caja("Head/corona", "placa_gema", (-0.8, 30.7, -5.0), (0.8, 32.3, -4.88), oro, dens=D)
    p.malla("Head/corona", "gema", geo.bipiramide((0.0, 31.5, -5.1), 0.48, 0.7, 0.7, 4, 45.0), cristal, dens=D,
            luz=False)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        # los cristales que salen de las hombreras
        for i, (x, y, z, r, h) in enumerate(((7.2, 25.35, 0.2, 0.5, 0.9), (8.1, 25.0, -1.1, 0.32, 0.6),
                                             (7.9, 25.0, 1.4, 0.3, 0.55))):
            p.malla(f"{hueso}/brazo", f"cristal_hombro{i}", geo.bipiramide((s * x, y, z), r, h, 0.3, 4, 45.0),
                    cristal, dens=D, luz=False)
        # los aros de oro de los punos
        a, b = sorted((s * 3.6, s * 8.7))
        for k, y in enumerate((13.0, 15.2)):
            p.caja(f"{hueso}/brazo", f"aro_puno{k}", (a, y, -2.6), (b, y + 0.3, 2.6), oro, dens=D)
        # las botas: puntera blanca y el aro de oro arriba
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        a, b = sorted((s * 0.2, s * 3.8))
        p.caja(f"{hueso}/bota", "puntera", (a, 0.0, -2.75), (b, 1.4, -2.35), voxel(BLANCO, 0.2), dens=D)
        a, b = sorted((s * -0.35, s * 4.35))
        p.caja(f"{hueso}/bota", "aro_bota", (a, 2.95, -2.55), (b, 3.25, 2.45), oro, dens=D)
    # el colgante de cristal del broche de la V
    p.caja(g, "cadenita", (-0.06, 17.2, -3.42), (0.06, 17.75, -3.3), oro, dens=D)
    p.malla(g, "colgante", geo.bipiramide((0.0, 16.75, -3.4), 0.32, 0.45, 0.55, 4, 45.0), cristal, dens=D, luz=False)
    # el libro con esquinas de oro que cuelga del cinturon (a su derecha)
    p.caja(g, "correa_libro", (2.6, 13.3, -3.45), (2.85, 14.4, -3.25), voxel(CUERO, -0.2), dens=D)
    p.caja(g, "libro", (2.0, 11.2, -3.95), (3.5, 13.4, -3.45), voxel(CUERO, 0.1), dens=D)
    p.caja(g, "hojas_libro", (2.08, 11.3, -3.47), (3.42, 13.3, -3.4), voxel(CREMA), dens=D)
    for k, (x, y) in enumerate(((2.0, 11.2), (3.1, 11.2), (2.0, 13.0), (3.1, 13.0))):
        p.caja(g, f"esquina_libro{k}", (x - 0.05, y - 0.05, -4.02), (x + 0.45, y + 0.45, -3.9), oro, dens=D)
    p.caja(g, "runa_libro", (2.6, 11.85, -4.02), (2.9, 12.75, -3.92), oro, dens=D)
    # el emblema de la faldilla (un rombo de oro)
    p.caja(g, "emblema_faldilla", (-0.45, 9.05, -3.12), (0.45, 9.95, -2.92), oro, rot=(0, 0, 45),
           piv=(0.0, 9.5, -3.0), dens=D)
    # la borla de oro en la punta de la capucha
    p.caja(g, "borla_nudo", (-0.3, 15.9, 2.95), (0.3, 16.5, 3.45), oro, dens=D)
    p.caja(g, "borla", (-0.22, 14.6, 3.0), (0.22, 15.95, 3.35), voxel(ORO, -0.1), dens=D)


def construir():
    p = Personaje("correctar", altura=32, cabeza=8, torso=(8, 12, 4), brazo=(4, 4), pierna=(4, 4))
    blanco = voxel(BLANCO, 0.05)
    # la cabeza envuelta, la vuelta de la bufanda (tapa la boca), la corona y los cristales
    p.caja("Head/cabeza", "cabeza", (-4, 24, -4), (4, 32, 4), cabeza_pintor(), dens=8, luz=False)
    casco(p)
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
    detalles(p)
    return p
