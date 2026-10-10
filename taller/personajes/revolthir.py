"""
Revolthir, rehecho a tamano de jugador (32 de alto, cuerpo de Steve) como el druida del bosque de la referencia que
paso el usuario: estilo de bloques con detalles.
  CABEZA: mascara blanca con dos ojos cuadrados negros (abajo, una barba de musgo) y la capucha cubierta de musgo
  ASTAS de rama en escalera (bloques) que salen de arriba de la cabeza hacia los lados y suben, con musgo, flores
    blancas y un FAROL encendido colgando de la punta de cada una
  CAPA verde oliva oscura: la esclavina de musgo sobre los hombros, los lados que caen junto a los brazos y la
    espalda hasta las pantorrillas, con el ARBOL dorado bordado atras y abajo un galon dorado con rombo; el borde de
    abajo con jirones de tela blanca; ENREDADERAS de musgo colgando de todas las orillas
  TUNICA: la camisa crema de un lado y la tunica cafe del otro, la pechera de cuero con su emblema dorado y el
    CINTURON de cuero con frasquitos colgando; abajo la falda partida: blanca de un lado y verde oscuro del otro
  BRAZOS con mangas (una cafe y una crema) con musgo arriba y guantes de cuero; PIERNAS verde oscuro; BOTAS cafes
    con puno de pelaje blanco
Textura de bloques (voxel). Las flores, el fuego de los faroles y los frascos van sin luz horneada (brillan).
"""

import math

from ..kit import Personaje
from ..textura import hex_a_rgba as hex_
from .bloques import color, voxel

D = 4                                   # texeles por px

MADERA = {"s": "#4A2E1C", "b": "#6B4428", "l": "#8A5A36"}
MUSGO = {"s": "#3E6B22", "b": "#5A8C2E", "l": "#7CB042"}
MUSGO_OSC = {"s": "#2C4C18", "b": "#3F6A22", "l": "#578A30"}   # la capucha
CAPA = {"s": "#2B2B1C", "b": "#3A3A26", "l": "#4B4A31"}
MASCARA = {"s": "#CFC8B4", "b": "#E6E0CE", "l": "#F4F0E2"}
TELA = {"s": "#D6D0C0", "b": "#E9E4D6", "l": "#F7F4EC"}
TUNICA = {"s": "#55391F", "b": "#74502F", "l": "#906843"}
CUERO = {"s": "#3F2817", "b": "#583A22", "l": "#72502F"}
VERDE = {"s": "#1F2B17", "b": "#2B3A1F", "l": "#3A4B2A"}
ORO, OJO, FUEGO, VIDRIO, CORCHO = "#D2A644", "#140E0A", "#FFD37A", "#A9D8B8", "#8A6A44"
PETALO, POLEN = "#F4F1E8", "#E8B830"


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _a_segmento(p, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    f = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / (ex * ex + ey * ey)))
    return math.hypot(p[0] - a[0] - ex * f, p[1] - a[1] - ey * f)


# ---------------------------------------------------------------- la cabeza

def cabeza_pintor():
    """Adelante la mascara blanca con los ojos cuadrados negros, manchas de musgo en sus orillas y la barba de musgo
    abajo; los otros lados, musgo."""
    mascara, musgo = voxel(MASCARA, 0.1), manchas_de_musgo(MUSGO_OSC, umbral=0.7)

    def p(t):
        if t.cara != "north":
            return musgo(t)
        u, v = t.x, t.y - 24.0
        if 1.0 <= abs(u) <= 3.0 and 3.4 <= v <= 5.6:
            return hex_(OJO)
        if v < 2.2:
            return musgo(t)
        cu, cv = math.floor(u * 2), math.floor(v * 2)
        if (abs(u) > 3.0 or v > 6.6) and _azar(cu * 7.1 + cv * 3.3) > 0.45:
            return musgo(t)
        return mascara(t)
    return p


# ---------------------------------------------------------------- las astas, las flores y los faroles

# las ramas de la derecha (la izquierda en espejo): (de, a, grueso); se arman con bloques en escalera
RAMAS = (((2.6, 32.4, 0.0), (6.5, 35.0, 0.0), 1.7), ((6.5, 35.0, 0.0), (10.5, 37.2, 0.0), 1.5),
         ((10.5, 37.2, 0.0), (13.2, 40.6, 0.0), 1.3), ((8.4, 36.1, 0.0), (8.9, 39.6, 0.0), 1.1),
         ((12.0, 39.0, 0.0), (14.6, 39.8, 0.0), 0.9))
FLORES = ((5.0, 35.9, -0.95), (9.7, 38.3, -0.85), (13.6, 41.3, -0.75), (2.0, 32.9, -4.75), (4.8, 29.0, -4.75),
          (6.8, 23.6, -2.95))
FAROL = (13.6, 40.0)                                     # de donde cuelga (la punta de la rama)
FAROL_ALTO = (31.6, 35.2)                                # de donde a donde va el farol


def _bloques_rama(a, b, g):
    """Bloques en escalera a lo largo de una rama."""
    n = max(1, math.ceil(math.dist(a, b) / (g * 0.7)))
    return [tuple(a[c] + (b[c] - a[c]) * i / n for c in range(3)) for i in range(n + 1)]


def flor(p, grupo, nombre, c):
    """Florecita blanca de cuatro petalos con el centro amarillo, mirando al frente."""
    x, y, z = c
    p.caja(grupo, f"{nombre}_centro", (x - 0.25, y - 0.25, z - 0.3), (x + 0.25, y + 0.25, z + 0.05), color(POLEN),
           dens=D, luz=False)
    for i, (dx, dy) in enumerate(((0.5, 0.0), (-0.5, 0.0), (0.0, 0.5), (0.0, -0.5))):
        p.caja(grupo, f"{nombre}_petalo{i}", (x + dx - 0.28, y + dy - 0.28, z - 0.2), (x + dx + 0.28, y + dy + 0.28, z),
               color(PETALO), dens=D, luz=False)


def farol_pintor(t):
    """El vidrio encendido con el marco oscuro en las orillas de cada cara."""
    a = (t.x - t.f[0]) / max(1e-6, t.t[0] - t.f[0]) if t.cara in ("north", "south") else \
        (t.z - t.f[2]) / max(1e-6, t.t[2] - t.f[2])
    b = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    if t.cara in ("up", "down") or min(a, 1 - a) < 0.18 or min(b, 1 - b) < 0.12:
        return hex_(MADERA["s"])
    return hex_(FUEGO)


def astas(p):
    madera, musgo = voxel(MADERA, 0.05), voxel(MUSGO, 0.1)
    k = 0
    for s in (1, -1):
        g = "Head/astas"
        for a, b, grueso in RAMAS:
            for c in _bloques_rama(a, b, grueso):
                x, y, z = s * c[0], c[1], c[2]
                h = grueso / 2
                pintor = musgo if _azar(k * 1.7) > 0.62 else madera
                p.caja(g, f"rama{k}", (x - h, y - h, z - h), (x + h, y + h, z + h), pintor, dens=D)
                if _azar(k * 2.3) > 0.7:                       # musgo encima
                    p.caja(g, f"musgo{k}", (x - h * 0.8, y + h, z - h * 0.8), (x + h * 0.6, y + h + 0.5, z + h * 0.6),
                           musgo, dens=D)
                k += 1
        for i, (x, y, z) in enumerate(FLORES):
            flor(p, "Head/flores", f"flor{s}_{i}", (s * x, y, z))
        # el farol colgando de la punta de la rama
        fx, fy = FAROL
        x0, x1 = FAROL_ALTO
        p.caja(g, f"cadena{s}", (s * fx - 0.15, x1, -0.15), (s * fx + 0.15, fy, 0.15), color(MADERA["s"]), dens=D)
        p.caja(g, f"techo_farol{s}", (s * fx - 1.0, x1, -1.0), (s * fx + 1.0, x1 + 0.6, 1.0), madera, dens=D)
        p.caja(g, f"farol{s}", (s * fx - 0.8, x0, -0.8), (s * fx + 0.8, x1, 0.8), farol_pintor, dens=D, luz=False)
        p.caja(g, f"base_farol{s}", (s * fx - 0.9, x0 - 0.4, -0.9), (s * fx + 0.9, x0, 0.9), madera, dens=D)


# ---------------------------------------------------------------- el cuerpo y la ropa

def torso_pintor():
    """Adelante: la camisa crema de un lado y la tunica cafe del otro, la pechera de cuero con su emblema dorado; el
    cinturon de cuero con la hebilla dorada; los otros lados, tunica."""
    crema, cafe, cuero = voxel(TELA, 0.05), voxel(TUNICA, 0.05), voxel(CUERO, 0.05)

    def p(t):
        if 14.8 <= t.y <= 16.0:                                 # el cinturon
            if t.cara == "north" and abs(t.x) < 0.6:
                return hex_(ORO)
            return cuero(t)
        if t.cara != "north":
            return cafe(t)
        if abs(t.x) < 1.6 and 18.8 <= t.y <= 23.2:              # la pechera con el emblema
            u, v = t.x, t.y - 21.0
            if (abs(u) < 0.2 and -1.6 < v < 1.6) or abs(abs(u) - 0.25 * (v + 1.6)) < 0.18 and v < 0.8:
                return hex_(ORO)
            return cuero(t)
        return crema(t) if t.x > 0 else cafe(t)
    return p


def manchas_de_musgo(base, rampa=MUSGO, umbral=0.68):
    """Una textura con manchas de musgo (en bloques de medio px)."""
    tela, musgo = voxel(base, 0.05), voxel(rampa, 0.1)

    def p(t):
        u = t.x if t.cara in ("north", "south", "up", "down") else t.z
        w = t.z if t.cara in ("up", "down") else t.y
        if _azar(math.floor(u * 2) * 5.3 + math.floor(w * 2) * 2.9) > umbral:
            return musgo(t)
        return tela(t)
    return p


def arbol_dorado(x, y):
    """El arbol dorado de la espalda de la capa: tronco, ramas en V, hojitas, y abajo el galon con su rombo."""
    if abs(x) < 0.25 and 12.5 < y < 21.5:
        return True
    for i, yb in enumerate((15.2, 16.6, 18.0, 19.4, 20.6)):
        largo = 2.6 - 0.45 * i
        for s in (1, -1):
            if _a_segmento((x, y), (0.0, yb), (s * largo, yb + 1.0)) < 0.22:
                return True
            if abs(x - s * (largo + 0.25)) < 0.25 and abs(y - (yb + 1.25)) < 0.25:
                return True
    if abs(x) < 3.8 and abs(y - (9.2 + 0.45 * abs(x))) < 0.22:
        return True
    return 0.3 < abs(x) + abs(y - 10.4) * 0.8 < 0.55


def capa_espalda():
    tela, oro = manchas_de_musgo(CAPA, umbral=0.88), hex_(ORO)
    return lambda t: oro if t.cara == "south" and arbol_dorado(t.x, t.y) else tela(t)


def enredaderas(p, orillas, semilla):
    """Tiras de musgo que cuelgan de cada orilla: ((x0, z0), (x1, z1), y, cuantas)."""
    musgo = voxel(MUSGO, 0.08)
    k = 0
    for (x0, z0), (x1, z1), y, n in orillas:
        for i in range(n):
            f = (i + 0.5) / n
            x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            largo = 1.2 + 3.6 * _azar(semilla + k * 3.1)
            w = 0.55 + 0.35 * _azar(semilla + k * 7.7)
            p.caja("Body/enredaderas", f"enredadera{semilla}_{k}", (x - w / 2, y - largo, z - w / 2),
                   (x + w / 2, y + 0.3, z + w / 2), musgo, dens=D)
            k += 1


def construir():
    p = Personaje("revolthir", altura=32, cabeza=8, torso=(8, 12, 4), brazo=(4, 4), pierna=(4, 4))
    musgo, capa = manchas_de_musgo(MUSGO_OSC, umbral=0.7), manchas_de_musgo(CAPA, umbral=0.8)
    # la cabeza con la mascara y la capucha de musgo (sin cara adelante)
    p.caja("Head/cabeza", "cabeza", (-4, 24, -4), (4, 32, 4), cabeza_pintor(), dens=D)
    p.caja("Head/capucha", "capucha", (-4.6, 22.6, -4.6), (4.6, 32.7, 4.6), musgo, dens=D,
           caras=("south", "east", "west", "up"))
    astas(p)
    # el torso, los brazos y las piernas (cuerpo de Steve)
    p.caja("Body/cuerpo", "torso", (-4, 12, -2), (4, 24, 2), torso_pintor(), dens=D)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 4, s * 8))
        manga = manchas_de_musgo(TUNICA if s > 0 else TELA, umbral=0.86)
        p.caja(f"{hueso}/brazo", "manga", (x1, 13.2, -2), (x2, 24, 2), manga, dens=D)
        p.caja(f"{hueso}/brazo", "guante", (x1 + s * 0.05, 12, -1.95), (x2 - s * 0.05, 13.2, 1.95), voxel(CUERO), dens=D)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((0, s * 4))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 3.4, -2), (x2, 12, 2), voxel(VERDE, 0.05), dens=D)
        a, b = sorted((s * -0.2, s * 4.2))
        p.caja(f"{hueso}/bota", "bota", (a, 0.0, -2.4), (b, 3.4, 2.3), voxel(MADERA), dens=D)
        a, b = sorted((s * -0.3, s * 4.3))
        p.caja(f"{hueso}/bota", "pelaje", (a, 3.0, -2.5), (b, 4.2, 2.4), voxel(TELA, 0.15), dens=D)
        # la falda partida: blanca de un lado y verde oscuro del otro
        a, b = sorted((s * 0.05, s * 4.35))
        falda = manchas_de_musgo(TELA if s > 0 else VERDE, umbral=0.9)
        p.caja("Body/ropa", f"falda{s}", (a, 5.6, -2.4), (b, 14.9, 2.4), falda, dens=D)
    # los frasquitos colgando del cinturon
    for i, (x, abajo) in enumerate(((-1.3, 11.0), (0.9, 12.2), (2.3, 10.2))):
        p.caja("Body/ropa", f"cordon{i}", (x - 0.08, abajo, -2.56), (x + 0.08, 14.9, -2.44), color(CUERO["b"]), dens=D)
        p.caja("Body/ropa", f"frasco{i}", (x - 0.4, abajo - 1.2, -2.95), (x + 0.4, abajo, -2.4), color(VIDRIO), dens=D,
               luz=False)
        p.caja("Body/ropa", f"corcho{i}", (x - 0.22, abajo, -2.82), (x + 0.22, abajo + 0.3, -2.52), color(CORCHO), dens=D)
    # la capa: la esclavina de musgo, los lados junto a los brazos y la espalda con el arbol dorado
    p.caja("Body/capa", "esclavina", (-8.7, 20.8, -2.7), (8.7, 24.9, 3.2), capa, dens=D)
    p.caja("Body/capa", "espalda", (-5.0, 5.0, 2.2), (5.0, 24.6, 3.1), capa_espalda(), dens=D)
    for s in (1, -1):
        a, b = sorted((s * 8.1, s * 8.8))
        p.caja("Body/capa", f"lado{s}", (a, 5.6, -1.6), (b, 21.0, 3.0), capa, dens=D)
    # los jirones de tela blanca abajo de la capa
    for i in range(10):
        x = -4.6 + i * 0.95
        largo = 0.9 + 1.8 * _azar(i * 4.1)
        p.caja("Body/capa", f"jiron{i}", (x, 5.0 - largo, 2.35), (x + 0.8, 5.2, 2.95), voxel(TELA, 0.1), dens=D)
    # las enredaderas: de la capucha a los lados de la cara, de la esclavina y de los lados de la capa
    enredaderas(p, (((-4.6, -4.4), (-4.6, 2.0), 25.0, 4), ((4.6, -4.4), (4.6, 2.0), 25.0, 4),
                    ((-8.7, -2.8), (8.7, -2.8), 20.9, 14), ((-8.7, 3.3), (8.7, 3.3), 20.9, 10),
                    ((-8.9, -1.6), (-8.9, 3.0), 12.0, 3), ((8.9, -1.6), (8.9, 3.0), 12.0, 3),
                    ((-5.0, 3.2), (5.0, 3.2), 16.0, 4)), 11)
    return p
