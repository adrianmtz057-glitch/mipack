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

from .. import malla as geo
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
ORO, FUEGO, VIDRIO, CORCHO = "#D2A644", "#FFD37A", "#A9D8B8", "#8A6A44"
OJO_CAFE, OJO_NEGRO, MASCARA_GRIETA = "#4A2E1C", "#1F1612", "#9A8A70"
HOJAS = (("#22461A", "#336428", "#488432", "#64A43E"),     # las hojas del manto (de la sombra a la luz)
         ("#2F5017", "#467428", "#609436", "#82B44A"),
         ("#1E3F1F", "#2D5C2D", "#417A38", "#5C9A48"))
PETALO, POLEN = "#F4F1E8", "#E8B830"


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _a_segmento(p, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    f = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / (ex * ex + ey * ey)))
    return math.hypot(p[0] - a[0] - ex * f, p[1] - a[1] - ey * f)


# ---------------------------------------------------------------- la cabeza

def cabeza_pintor():
    """La cabeza casi no se ve (la tapan la mascara y el manto): adelante, en el hueco de cada ojo, el ojo cafe
    oscuro con el centro negro; lo demas musgo oscuro (la sombra adentro de la capucha)."""
    musgo, cafe, negro = voxel(MUSGO_OSC, -0.2), hex_(OJO_CAFE), hex_(OJO_NEGRO)

    def p(t):
        if t.cara != "north":
            return musgo(t)
        u, v = abs(t.x), t.y - 24.0
        if 1.0 <= u <= 3.0 and 3.4 <= v <= 5.6:
            return negro if 1.5 <= u <= 2.5 and 3.9 <= v <= 5.1 else cafe
        return hex_(MASCARA["s"])
    return p


# la mascara con volumen: piezas (desde, hasta) que dejan los huecos de los ojos (|x| 1-3, y 27.4-29.6)
MASCARA_PIEZAS = (("frente", (-3.7, 29.6, -4.75), (3.7, 31.5, -3.95)),
                  ("ceja", (-3.5, 29.4, -5.05), (3.5, 30.2, -4.7)),
                  ("puente", (-1.0, 26.6, -4.9), (1.0, 29.6, -3.95)),
                  ("nariz", (-0.65, 26.3, -5.3), (0.65, 28.4, -4.85)),
                  ("sien_d", (3.0, 27.0, -4.65), (3.75, 29.6, -3.95)),
                  ("sien_i", (-3.75, 27.0, -4.65), (-3.0, 29.6, -3.95)),
                  ("mejillas", (-3.6, 25.5, -4.75), (3.6, 27.4, -3.95)),
                  ("barbilla", (-2.6, 24.8, -4.6), (2.6, 25.6, -3.95)),
                  ("frente_alta", (-1.8, 30.8, -5.0), (1.8, 31.9, -4.7)))


def mascara(p):
    """La mascara blanca con volumen: la frente con su ceja que sobresale y hace sombra en los ojos, el puente con la
    nariz que sale, las sienes, las mejillas y la barbilla mas angosta. Unas grietas cafes chiquitas."""
    blanco = voxel(MASCARA, 0.12)
    grieta = hex_(MASCARA_GRIETA)

    def pintor(t):
        if t.cara == "north" and _a_segmento((t.x, t.y), (2.2, 31.4), (2.9, 30.0)) < 0.1:
            return grieta
        if t.cara == "north" and _a_segmento((t.x, t.y), (-2.4, 26.9), (-3.1, 25.9)) < 0.1:
            return grieta
        return blanco(t)
    for nombre, d, h in MASCARA_PIEZAS:
        p.caja("Head/mascara", nombre, d, h, pintor, dens=D)


# ---------------------------------------------------------------- el manto de hojas

def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _mas(a, b, k=1.0):
    return tuple(x + y * k for x, y in zip(a, b))


def _punto(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _a_tramo(p, a, b):
    e = _sub(b, a)
    f = max(0.0, min(1.0, _punto(_sub(p, a), e) / max(1e-9, _punto(e, e))))
    return math.dist(p, _mas(a, e, f))


def hoja_pintor(a, b, tonos, k):
    """Una hoja: cada mitad (esta doblada por la vena) de un tono segun hacia donde mira, la vena mas clara y las de
    abajo de cada capa mas oscuras (k). Sin luz horneada (entre tantas hojas encimadas la oclusion las ensucia)."""
    from ..luz import LUZ
    largo = math.sqrt(sum(c * c for c in LUZ))
    luz = tuple(c / largo for c in LUZ)
    cols = [hex_(c) for c in tonos]

    def p(t):
        d = _punto(t.n, luz)
        i = 1 + k + (1 if d > 0.5 else 0) - (1 if d < 0.0 else 0)
        if _a_tramo((t.x, t.y, t.z), a, b) < 0.13:
            i += 1
        return cols[max(0, min(3, i))]
    return p


class Manto:
    """Las hojas del manto, juntas en una malla por hueso. Cada hoja es un rombo doblado por la vena (las orillas
    hacia adentro), de dos caras."""

    def __init__(self):
        self.huesos = {}
        self.hojas = []                     # (centro, normal) para poner flores encima

    def hoja(self, grupo, a, d, n, ancho, largo, tonos, k=0, doblez=0.24):
        vs, cs, ps = self.huesos.setdefault(grupo, ([], [], []))
        s = _cruz(d, n)
        b = _mas(a, d, largo)
        m = _mas(a, d, largo * 0.42)
        r = _mas(_mas(m, s, ancho / 2), n, -doblez)
        l = _mas(_mas(m, s, -ancho / 2), n, -doblez)
        i0 = len(vs)
        vs.extend((a, r, b, l))
        pin = hoja_pintor(a, b, tonos, k)
        for tri in ((0, 1, 2), (0, 2, 3)):
            idx = [i0 + i for i in tri]
            if _punto(geo.normal([vs[i] for i in idx]), n) < 0:
                idx.reverse()
            cs += [tuple(idx), tuple(reversed(idx))]
            ps += [pin, pin]
        self.hojas.append((_mas(a, d, largo * 0.45), n, d))

    def colgar(self, grupo, a, nh, inclina, largo, ancho, k, semilla):
        """Una hoja que cuelga desde a, con la punta hacia afuera (nh, horizontal) 'inclina' grados."""
        g = math.radians(inclina + 10 * (_azar(semilla * 1.7) - 0.5))
        d = (nh[0] * math.sin(g), -math.cos(g), nh[2] * math.sin(g))
        n = (nh[0] * math.cos(g), math.sin(g), nh[2] * math.cos(g))
        tonos = HOJAS[int(_azar(semilla * 3.1) * len(HOJAS))]
        self.hoja(grupo, a, d, n, ancho, largo * (0.9 + 0.2 * _azar(semilla * 5.3)), tonos, k)

    def poner(self, p):
        for g, (vs, cs, ps) in self.huesos.items():
            p.malla(g, "manto_" + g.split("/")[0], (vs, cs), ps, dens=D, luz=False)


def _anillo(a, b, e, n, desfase=0.0):
    """n puntos repartidos por igual a lo largo de una superelipse (|x/a|^e + |z/b|^e = 1), con su normal."""
    finos = []
    for i in range(720):
        th = 2 * math.pi * i / 720
        c, s = math.cos(th), math.sin(th)
        x, z = a * math.copysign(abs(c) ** (2 / e), c), b * math.copysign(abs(s) ** (2 / e), s)
        nx = math.copysign(abs(x / a) ** (e - 1), x) / a
        nz = math.copysign(abs(z / b) ** (e - 1), z) / b
        h = math.hypot(nx, nz) or 1.0
        finos.append((x, z, nx / h, nz / h))
    acum = [0.0]
    for i in range(1, 721):
        p0, p1 = finos[i - 1], finos[i % 720]
        acum.append(acum[-1] + math.hypot(p1[0] - p0[0], p1[1] - p0[1]))
    out, j = [], 0
    for i in range(n):
        objetivo = acum[-1] * ((i + desfase) % n) / n
        while acum[j + 1] < objetivo:
            j += 1
        out.append(finos[j % 720])
    return out


def fila(manto, hueso, y, centro, a, b, e, n, inclina, largo, ancho, k=0, desfase=0.0, salta=None, semilla=0):
    """Una fila de hojas alrededor de una superelipse a la altura y."""
    for i, (x, z, nx, nz) in enumerate(_anillo(a, b, e, n, desfase)):
        x, z = x + centro[0], z + centro[1]
        if salta and salta(x, z):
            continue
        sem = semilla + i * 7.3
        sal = 0.06 + 0.08 * (i % 2)
        pt = (x + nx * sal, y + 0.2 * (_azar(sem) - 0.5), z + nz * sal)
        manto.colgar(hueso(pt), pt, (nx, 0.0, nz), inclina, largo, ancho, k, sem)


def manto_de_hojas(p):
    """El manto de hojas que lo cubre: la capucha (un monton de hojas arriba, filas que caen a los lados y atras
    dejando la cara), la barba de hojas bajo la mascara y la esclavina sobre los hombros que cae por la espalda y
    deja una V adelante. Las hojas de arriba de los brazos van en el hueso del brazo."""
    manto = Manto()
    cabeza = lambda pt: "Head/manto"                                 # noqa: E731

    def cuerpo(pt):
        return "RightArm/manto" if pt[0] > 4.5 else "LeftArm/manto" if pt[0] < -4.5 else "Body/manto"

    # la capucha: de arriba hacia abajo (cada fila de mas adentro queda encima de la de afuera)
    fila(manto, cabeza, 33.7, (0, 0.3), 1.0, 1.0, 2, 5, 74, 2.3, 1.7, 0, semilla=1)
    fila(manto, cabeza, 33.1, (0, 0.2), 2.8, 2.8, 2.4, 11, 70, 2.4, 1.8, 0, 0.5, semilla=2)
    fila(manto, cabeza, 32.4, (0, 0.0), 4.7, 4.7, 4, 20, 35, 2.4, 1.8, 0, semilla=3)
    cara = lambda x, z: z < -1.0 and abs(x) < 3.75                    # noqa: E731
    for i, y in enumerate((30.7, 28.9, 27.1, 25.3, 23.6)):
        fila(manto, cabeza, y, (0, 0.0), 4.75, 4.75, 4, 20, 18, 2.4, 1.8, 0 if i < 4 else -1, 0.5 * (i % 2 == 0),
             cara, semilla=10 + i)
    # la barba de hojas bajo la mascara
    for i, x in enumerate((-2.4, -1.2, 0.0, 1.2, 2.4)):
        manto.colgar("Head/manto", (x, 25.4 - 0.3 * (i % 2), -4.5), (0.0, 0.0, -1.0), 8, 2.3, 1.5, 0, 40 + i)
    for i, x in enumerate((-1.8, -0.6, 0.6, 1.8)):
        manto.colgar("Head/manto", (x, 24.2, -4.3), (0.0, 0.0, -1.0), 10, 2.2, 1.5, -1, 50 + i)
    # la esclavina: sobre los hombros y cayendo; adelante una V que deja ver la pechera
    v = lambda ancho: (lambda x, z: z < -1.0 and abs(x) < ancho)     # noqa: E731
    fila(manto, cuerpo, 25.1, (0, 0.2), 6.2, 3.0, 3, 18, 66, 2.4, 1.8, 0, salta=v(3.2), semilla=60)
    fila(manto, cuerpo, 23.9, (0, 0.2), 8.6, 3.3, 3.5, 26, 32, 2.5, 1.9, 0, 0.5, v(1.4), semilla=61)
    fila(manto, cuerpo, 22.2, (0, 0.2), 9.1, 3.5, 4, 28, 18, 2.5, 1.9, 0, 0.0, v(2.4), semilla=62)
    fila(manto, cuerpo, 20.5, (0, 0.2), 9.2, 3.6, 4, 28, 14, 2.5, 1.9, -1, 0.5, v(4.0), semilla=63)
    manto.poner(p)
    # flores blancas sobre algunas hojas que miran al frente
    n = 0
    for i, (c, nrm, d) in enumerate(manto.hojas):
        en_cara = abs(c[0]) < 4.2 and c[1] > 22.0                    # no sobre la mascara ni la barba
        if nrm[2] < -0.5 and not en_cara and _azar(i * 4.7) > 0.7 and n < 7:
            grupo = "Head/flores" if c[1] > 24.6 else "Body/flores"
            flor(p, grupo, f"flor_manto{n}", _mas(c, nrm, 0.15))
            n += 1
    return manto


# ---------------------------------------------------------------- las astas, las flores y los faroles

# las ramas de la derecha (la izquierda en espejo): (de, a, grueso); se arman con bloques en escalera
RAMAS = (((2.6, 32.4, 0.0), (6.5, 35.0, 0.0), 1.7), ((6.5, 35.0, 0.0), (10.5, 37.2, 0.0), 1.5),
         ((10.5, 37.2, 0.0), (13.2, 40.6, 0.0), 1.3), ((8.4, 36.1, 0.0), (8.9, 39.6, 0.0), 1.1),
         ((12.0, 39.0, 0.0), (14.6, 39.8, 0.0), 0.9))
FLORES = ((5.0, 35.9, -0.95), (9.7, 38.3, -0.85), (13.6, 41.3, -0.75))
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
    tela, oro = voxel(CAPA, 0.05), hex_(ORO)
    return lambda t: oro if t.cara == "south" and arbol_dorado(t.x, t.y + 2.4) else tela(t)


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
    base = voxel(MUSGO_OSC, -0.15)                  # lo de abajo del manto (se asoma entre las hojas)
    # la cabeza, la mascara con volumen, la base de la capucha y las astas
    p.caja("Head/cabeza", "cabeza", (-4, 24, -4), (4, 32, 4), cabeza_pintor(), dens=D, luz=False)
    mascara(p)
    p.caja("Head/capucha", "capucha", (-4.6, 23.0, -4.6), (4.6, 32.7, 4.6), base, dens=D,
           caras=("south", "east", "west", "up"))
    astas(p)
    # el torso, los brazos y las piernas (cuerpo de Steve)
    p.caja("Body/cuerpo", "torso", (-4, 12, -2), (4, 24, 2), torso_pintor(), dens=D)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 4, s * 8))
        p.caja(f"{hueso}/brazo", "manga", (x1, 13.2, -2), (x2, 24, 2), voxel(TUNICA if s > 0 else TELA, 0.05), dens=D)
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
        p.caja("Body/ropa", f"falda{s}", (a, 5.6, -2.4), (b, 14.9, 2.4), voxel(TELA if s > 0 else VERDE, 0.05), dens=D)
    # los frasquitos colgando del cinturon
    for i, (x, abajo) in enumerate(((-1.3, 11.0), (0.9, 12.2), (2.3, 10.2))):
        p.caja("Body/ropa", f"cordon{i}", (x - 0.08, abajo, -2.56), (x + 0.08, 14.9, -2.44), color(CUERO["b"]), dens=D)
        p.caja("Body/ropa", f"frasco{i}", (x - 0.4, abajo - 1.2, -2.95), (x + 0.4, abajo, -2.4), color(VIDRIO), dens=D,
               luz=False)
        p.caja("Body/ropa", f"corcho{i}", (x - 0.22, abajo, -2.82), (x + 0.22, abajo + 0.3, -2.52), color(CORCHO), dens=D)
    # la capa: la base del manto sobre los hombros, los lados junto a los brazos y la espalda con el arbol dorado
    p.caja("Body/capa", "base_manto", (-8.1, 20.6, -2.2), (8.1, 24.2, 2.5), base, dens=D)
    p.caja("Body/capa", "espalda", (-5.0, 5.0, 2.2), (5.0, 24.6, 3.1), capa_espalda(), dens=D)
    for s in (1, -1):
        a, b = sorted((s * 8.1, s * 8.8))
        p.caja("Body/capa", f"lado{s}", (a, 5.6, -1.6), (b, 21.0, 3.0), voxel(CAPA, 0.05), dens=D)
    # los jirones de tela blanca abajo de la capa
    for i in range(10):
        x = -4.6 + i * 0.95
        largo = 0.9 + 1.8 * _azar(i * 4.1)
        p.caja("Body/capa", f"jiron{i}", (x, 5.0 - largo, 2.35), (x + 0.8, 5.2, 2.95), voxel(TELA, 0.1), dens=D)
    # el manto de hojas y las enredaderas que cuelgan de sus orillas
    manto_de_hojas(p)
    enredaderas(p, (((-4.9, -4.3), (-4.9, -2.8), 22.4, 2), ((4.9, -4.3), (4.9, -2.8), 22.4, 2),
                    ((-9.2, -3.6), (-4.6, -3.6), 18.8, 4), ((4.6, -3.6), (9.2, -3.6), 18.8, 4),
                    ((-9.0, 4.1), (9.0, 4.1), 18.6, 10), ((-9.1, -1.6), (-9.1, 3.0), 12.0, 3),
                    ((9.1, -1.6), (9.1, 3.0), 12.0, 3)), 11)
    return p
