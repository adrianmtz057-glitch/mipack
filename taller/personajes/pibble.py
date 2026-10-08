"""
Pibble, el semidios errante. Hecho a mano con el kit (boceto 9).

Low-poly con paneles usados con moderacion, a la escala de la capucha y pachoncito:
  - capucha (taller/personajes/pibble_capucha.py): ovalo acostado, forro negro, agujero de la cara, cubo de la
    cabeza adentro y orejas en cono con paneles
  - tunica: UNA sola pieza de 8 lados, del cuello a las puntas de abajo: hombros, panza gordita hacia adelante,
    abrigo abierto en A con su borde (escalon hacia adentro) y la falda azul con puntas doradas a los costados.
    Pintada: cuello negro bajo la capucha, abrigo crema, franjas negras, panel azul con runa atras, filetes
  - estola azul en 3D sobre la panza, con filetes dorados y runa de rombos, que termina en punta
  - mangas crema con puno negro que nacen de adentro del hombro (no pegadas por fuera)
  - botas facetadas negras con banda y puntera doradas
  - cola en gancho, gruesa, azul con runas doradas
  - joyas en 3D bien agarradas: aro con gema prendido a la capucha con un broche, y rombos apilados
"""

import math

from . import pibble_capucha as cap
from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import hex_a_rgba as hex_

NEGRO = tonos("#221D22")
AZUL = tonos("#2E4458")
CREMA = tonos("#DCD3C3")
TOSTADO = tonos("#B08A60")
ORO = tonos("#C8A058")
VACIO = "#0E0B0E"

# tunica: (altura, centro z, semieje x, semieje z) de cada anillo, de ARRIBA hacia abajo (la parte del abrigo)
TUNICA = ((17.6, 0.1, 4.6, 3.6),       # cuello (adentro de la capucha)
          (15.2, 0.0, 6.0, 4.6),       # hombros
          (9.8, -0.5, 7.3, 5.8),       # panza, corrida hacia adelante
          (4.6, 0.1, 8.2, 6.1))        # borde del abrigo, abierto en A
LADOS_TUNICA = 8
GIRO_TUNICA = 22.5                     # con este giro la cara de adelante queda plana (ahi va la estola)
Y_BORDE = 4.6                          # borde del abrigo; debajo, la falda


# ---------------------------------------------------------------- piezas

def loft(anillos, lados, giro=0.0, tapa_abajo=True, tapa_arriba=True):
    """Cuerpo facetado por anillos (y, cx, cz, rx, rz) de ABAJO hacia ARRIBA."""
    rs = [geo.anillo(cx, y, cz, rx, rz, lados, giro) for y, cx, cz, rx, rz in anillos]
    return geo.unir(*[geo.tronco(rs[k], rs[k + 1], tapa_abajo=tapa_abajo and k == 0,
                                 tapa_arriba=tapa_arriba and k == len(rs) - 2) for k in range(len(rs) - 1)])


def loft_puntos(anillos, tapa_abajo=True, tapa_arriba=True):
    """Como loft, pero con los anillos ya armados (listas de puntos), de abajo hacia arriba."""
    return geo.unir(*[geo.tronco(anillos[k], anillos[k + 1], tapa_abajo=tapa_abajo and k == 0,
                                 tapa_arriba=tapa_arriba and k == len(anillos) - 2) for k in range(len(anillos) - 1)])


def extruir_x(perfil_zy, x1, x2):
    """Extruye un perfil (z, y) a lo ancho, de x1 a x2 (para tiras que siguen la panza)."""
    vs, cs = geo.extruir(perfil_zy, x1, x2)
    return [(p[2], p[1], p[0]) for p in vs], [tuple(reversed(c)) for c in cs]     # cambiar ejes da vuelta las caras


def bipiramide(c, r, alto_arriba, alto_abajo, lados=4, giro=45.0):
    """Rombo / gota facetada: dos piramides pegadas por la base (colgantes, gemas)."""
    base = geo.anillo(c[0], c[1], c[2], r, r, lados, giro)
    arriba = geo.piramide(base, (c[0], c[1] + alto_arriba, c[2]), tapa=False)
    abajo = geo.piramide(base, (c[0], c[1] - alto_abajo, c[2]), tapa=False)
    vs, cs = abajo
    return geo.unir(arriba, (vs, [tuple(reversed(f)) for f in cs]))        # la de abajo mira hacia abajo


def aro3d(r_ext, r_int, grosor, lados=8):
    """Aro facetado en el plano XY (mira hacia -Z), centrado en el origen."""
    m = cap.Armador()
    o = [[m.v((r_ext * math.cos(2 * math.pi * k / lados + math.pi / lados),
               r_ext * math.sin(2 * math.pi * k / lados + math.pi / lados), z)) for k in range(lados)]
         for z in (-grosor / 2, grosor / 2)]
    i = [[m.v((r_int * math.cos(2 * math.pi * k / lados + math.pi / lados),
               r_int * math.sin(2 * math.pi * k / lados + math.pi / lados), z)) for k in range(lados)]
         for z in (-grosor / 2, grosor / 2)]
    for k in range(lados):
        k2 = (k + 1) % lados
        m.cara((o[0][k], o[0][k2], i[0][k2], i[0][k]), (0, 0, -1), "aro")
        m.cara((o[1][k], o[1][k2], i[1][k2], i[1][k]), (0, 0, 1), "aro")
        m.cara((o[0][k], o[0][k2], o[1][k2], o[1][k]), lambda c: (c[0], c[1], 0), "aro")
        m.cara((i[0][k], i[0][k2], i[1][k2], i[1][k]), lambda c: (-c[0], -c[1], 0), "aro")
    return m.vs, m.caras


def frente_tunica(y):
    """z de la cara de adelante de la tunica a la altura y (la cara plana del medio)."""
    pts = [(a[0], a[1] - a[3] * math.sin(math.radians(90 - 180 / LADOS_TUNICA))) for a in TUNICA]
    for (y1, z1), (y2, z2) in zip(pts, pts[1:]):
        if y2 <= y <= y1:
            return z1 + (z2 - z1) * (y1 - y) / (y1 - y2)
    return pts[-1][1]


GIRO_COLA = (0, -32, 0)
BASE_COLA = (2.4, 3.6, 3.4)
PERFIL_COLA = ((0, -0.5), (4.5, -2.2), (9, -1.0), (12.6, 2.6), (14, 7.5), (13.2, 13.2),      # borde de afuera
               (11.0, 8.0), (9.6, 4.6), (7.2, 2.7), (3.8, 2.6), (0, 4.0))                    # borde de adentro


def cola():
    """Gancho grueso: perfil en media luna extruido, sale de atras a la derecha y sube hacia afuera."""
    m = geo.extruir(list(PERFIL_COLA), -0.9, 0.9)
    m = geo.girar(m, GIRO_COLA)
    return geo.mover(m, BASE_COLA)


def desgirar(p, rot, piv):
    """Lleva un punto del modelo a las coordenadas propias de una pieza girada con geo.girar."""
    x, y, z = p[0] - piv[0], p[1] - piv[1], p[2] - piv[2]
    a, b, c = (math.radians(v) for v in rot)
    x, y = x * math.cos(c) + y * math.sin(c), -x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) - z * math.sin(b), x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) + z * math.sin(a), -y * math.sin(a) + z * math.cos(a)
    return x, y, z


# ---------------------------------------------------------------- pintores (por posicion: siguen a traves de las caras)

def tunica(t):
    if t.cara == "down":
        return hex_(AZUL["s"])                                             # debajo del borde del abrigo
    ax = abs(t.x)
    if t.y < Y_BORDE - 0.1:                                                # falda de abajo
        if t.y < 2.5:
            return hex_(ORO["s"])                                          # puntas doradas
        if t.n[2] < -0.35 and ax < 2.4:
            return hex_(NEGRO["b"])
        return hex_(AZUL["b"])
    if t.y < Y_BORDE + 0.55:
        return hex_(ORO["b"] if t.y > Y_BORDE + 0.25 else ORO["s"])        # filete dorado del borde del abrigo
    if t.y > 15.0:
        return hex_(NEGRO["b"])                                            # cuello negro debajo de la capucha
    if t.n[2] < -0.35:                                                     # adelante
        if ax < 2.9:
            return hex_(NEGRO["b"])
        return hex_(CREMA["l"] if t.cara == "up" else CREMA["b"])
    if t.n[2] > 0.35:                                                      # atras
        if ax < 1.8:
            return hex_(ORO["b"] if _runa(t.x, t.y - 10.0) else AZUL["b"])
        if ax < 2.6:
            return hex_(NEGRO["b"])
    return hex_(CREMA["l"] if t.cara == "up" else (CREMA["b"] if t.y > 8 else CREMA["s"]))


def _runa(x, y):
    """Runa de dos rombos encadenados (x, y relativos al centro de la runa)."""
    for cy in (1.5, -1.5):
        d = abs(x) + abs(y - cy) * 0.75
        if 0.95 < d < 1.35 or d < 0.3:
            return True
    return False


def estola(t):
    if t.cara in ("east", "west", "up", "down"):
        return hex_(AZUL["s"])
    if abs(t.x) > 1.4:
        return hex_(ORO["b"])                                              # filetes de los costados
    if _runa(t.x, t.y - 10.0):
        return hex_(ORO["l"])
    return hex_(AZUL["b"])


def negro_tela(t):
    if t.cara == "up":
        return hex_(NEGRO["b"])
    return hex_(NEGRO["b"] if t.cara != "down" else NEGRO["s"])


def manga(t):
    if t.y < 9.65:
        return hex_(NEGRO["s"] if t.cara == "down" else NEGRO["b"])        # puno negro
    if t.y < 10.2:
        return hex_(ORO["b"])                                              # filete dorado arriba del puno
    return hex_(CREMA["l"] if t.cara == "up" else CREMA["b"])


def bota(t):
    if t.cara == "down":
        return hex_(TOSTADO["s"])
    if 2.3 < t.y < 2.95:
        return hex_(ORO["b"])                                              # banda
    if t.z < -1.5 and t.y < 1.5:
        return hex_(ORO["l"] if t.cara == "up" else ORO["b"])              # puntera
    if t.y < 0.35:
        return hex_(TOSTADO["s"])
    return hex_(NEGRO["l"] if t.cara == "up" else NEGRO["b"])


def cola_pintor(t):
    u, v, w = desgirar((t.x, t.y, t.z), GIRO_COLA, BASE_COLA)
    if abs(w) < 0.85:                                                      # cantos
        return hex_(NEGRO["b"])
    trazos = (((2.0, -0.4), (3.2, 2.0)), ((5.8, -0.9), (7.0, 1.8)), ((2.6, 0.9), (6.4, 0.3)),
              ((10.0, 1.6), (12.0, 3.0)), ((11.4, 4.2), (12.2, 9.6)), ((10.6, 6.8), (12.8, 6.4)))
    for (ax, ay), (bx, by) in trazos:
        dx, dy = bx - ax, by - ay
        k = max(0.0, min(1.0, ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy)))
        if math.hypot(u - ax - k * dx, v - ay - k * dy) < 0.42:
            return hex_(ORO["b"])
    return hex_(AZUL["b"] if v < 6 else AZUL["s"])


def oro_pintor(t):
    return hex_(ORO["l"] if t.n[1] > 0.3 else (ORO["b"] if t.n[1] > -0.3 else ORO["s"]))


def gema(t):
    return hex_(AZUL["l"] if t.n[1] > 0 else "#4A7090")


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("pibble", altura=27, cabeza=10, torso=(12, 11, 9), brazo=(4, 5))

    # ================================================================ CAPUCHA (cabeza y orejas incluidas)
    cap.poner(p)

    # ================================================================ TUNICA pachoncita, una sola pieza
    abrigo = [geo.anillo(0, y, cz, rx, rz, LADOS_TUNICA, GIRO_TUNICA) for y, cz, rx, rz in reversed(TUNICA)]
    # falda: puntas largas a los costados, mas corta adelante y atras
    largas = {0, 3, 4, 7}
    falda = [(x, 1.9 if k in largas else 3.1, z) for k, (x, _, z) in
             enumerate(geo.anillo(0, 0, 0.1, 8.3, 6.2, LADOS_TUNICA, GIRO_TUNICA))]
    escalon = geo.anillo(0, Y_BORDE - 0.15, 0.1, 7.4, 5.5, LADOS_TUNICA, GIRO_TUNICA)   # el abrigo pisa la falda
    p.malla("Body/tunica", "tunica", loft_puntos([falda, escalon] + abrigo, tapa_abajo=False), tunica)

    # ================================================================ ESTOLA en 3D sobre la panza, con punta
    ys = (15.0, 13.0, 11.0, 9.8, 8.0, 6.2, 4.6)
    frente = [(frente_tunica(y) - 0.12, y) for y in ys]
    perfil = frente + [(z + 0.45, y) for z, y in reversed(frente)]
    p.malla("Body/estola", "estola", extruir_x(perfil, -1.8, 1.8), estola)
    zf = frente_tunica(4.6) - 0.12
    p.malla("Body/estola", "estola_punta", geo.extruir([(-1.8, 4.6), (0, 2.4), (1.8, 4.6)], zf, zf + 0.45), estola)

    # ================================================================ MANGAS crema acampanadas con puno negro
    anillos = [(7.6, 8.4, -0.4, 2.8, 2.8),        # abajo del puno
               (9.65, 8.1, -0.3, 3.0, 3.0),       # arriba del puno
               (17.2, 4.2, 0.0, 1.6, 1.6)]        # arriba: nace adentro del hombro, debajo del borde de la capucha
    p.malla_par("RightArm/manga", "manga", loft(anillos, 8, 22.5), manga)

    # ================================================================ PIERNAS cortas y botas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        cx = s * 2.4
        p.malla(f"{hueso}/pierna", "pantalon", loft([(3.2, cx, 0.2, 1.8, 1.8), (6.8, cx, 0.0, 2.3, 2.2)], 8, 22.5),
                negro_tela)
        p.malla(f"{hueso}/bota", "bota", loft([(0.0, cx, -0.6, 2.1, 2.8), (1.6, cx, 0.0, 1.95, 2.1),
                                                (3.6, cx, 0.2, 1.85, 1.85)], 8, 22.5), bota)

    # ================================================================ COLA en gancho
    p.malla("Body/cola", "cola", cola(), cola_pintor)

    # ================================================================ JOYAS en 3D
    # aro con gema al costado izquierdo de la capucha (mira hacia afuera), y debajo rombos apilados
    # aro con gema al costado izquierdo de la capucha, mirando afuera y adelante, prendido con un broche
    centro = (-8.45, 23.0, -2.2)
    p.malla("Head/joyas", "aro", geo.mover(geo.girar(aro3d(2.3, 1.5, 0.6), (0, 55, 0)), centro), oro_pintor)
    p.malla("Head/joyas", "gema", bipiramide(centro, 0.75, 1.1, 1.1), gema)
    p.caja("Head/joyas", "broche", (-8.6, 24.9, -2.45), (-7.1, 25.5, -1.95), oro_pintor, dens=2)
    # colgantes de rombos apilados: el izquierdo cuelga del aro, el derecho sale de la capucha
    for tag, x, y0 in (("izq", -8.45, 20.9), ("der", 8.2, 22.2)):
        p.caja("Head/joyas", f"eslabon_{tag}", (x - 0.15, y0 - 0.7, -2.35), (x + 0.15, y0, -2.05), oro_pintor, dens=2)
        p.malla("Head/joyas", f"cuenta_{tag}", bipiramide((x, y0 - 1.2, -2.2), 0.45, 0.5, 0.5), oro_pintor)
        p.caja("Head/joyas", f"eslabon2_{tag}", (x - 0.15, y0 - 2.4, -2.35), (x + 0.15, y0 - 1.7, -2.05), oro_pintor,
               dens=2)
        p.malla("Head/joyas", f"gota_{tag}", bipiramide((x, y0 - 3.3, -2.2), 0.85, 0.9, 2.1), oro_pintor)
    return p
