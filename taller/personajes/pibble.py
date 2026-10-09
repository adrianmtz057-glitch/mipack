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
  - cola gordita y redonda en gancho: tubo de 8 lados con la punta redondeada, azul con anillos dorados y la
    punta negra
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

def frente_tunica(y):
    """z de la cara de adelante de la tunica a la altura y (la cara plana del medio)."""
    pts = [(a[0], a[1] - a[3] * math.sin(math.radians(90 - 180 / LADOS_TUNICA))) for a in TUNICA]
    for (y1, z1), (y2, z2) in zip(pts, pts[1:]):
        if y2 <= y <= y1:
            return z1 + (z2 - z1) * (y1 - y) / (y1 - y2)
    return pts[-1][1]


GIRO_COLA = (0, -32, 0)
BASE_COLA = (2.4, 3.6, 3.4)
# linea del medio de la cola en su plano (u hacia afuera, v hacia arriba) y su radio en cada punto: gorda en la base
CENTRO_COLA = ((0.0, 1.8), (4.0, 0.2), (8.0, 0.9), (11.0, 3.6), (12.3, 7.4), (12.5, 10.6))
RADIO_COLA = (2.1, 2.05, 1.95, 1.8, 1.6, 1.35)
LADOS_COLA = 8
ANILLOS_COLA = ((3.2, 3.9), (7.4, 8.1), (11.4, 12.1))     # anillos dorados (tramos del largo de la cola)
PUNTA_COLA = 15.2                   # desde este largo, la punta va negra


def _catmull(p0, p1, p2, p3, s):
    return tuple(0.5 * (2 * b + (c - a) * s + (2 * a - 5 * b + 4 * c - d) * s * s + (3 * b - a - 3 * c + d) * s ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def camino_cola(pasos=3):
    """Puntos (u, v, radio) de la linea del medio de la cola: una curva suave (Catmull-Rom) por CENTRO_COLA."""
    pts = [(u, v, r) for (u, v), r in zip(CENTRO_COLA, RADIO_COLA)]
    ext = [tuple(2 * a - b for a, b in zip(pts[0], pts[1]))] + pts
    ext.append(tuple(2 * a - b for a, b in zip(pts[-1], pts[-2])))
    camino = [_catmull(ext[k], ext[k + 1], ext[k + 2], ext[k + 3], i / pasos)
              for k in range(len(pts) - 1) for i in range(pasos)]
    return camino + [pts[-1]]


def _largos(camino):
    out, total = [0.0], 0.0
    for a, b in zip(camino, camino[1:]):
        total += math.hypot(b[0] - a[0], b[1] - a[1])
        out.append(total)
    return out


FINO_COLA = camino_cola(12)
LARGO_COLA = _largos(FINO_COLA)


def cola():
    """Cola gordita y redonda: un tubo de 8 lados que sigue una curva suave en gancho (sale de atras a la derecha y
    sube hacia afuera), gruesa en la base, apenas mas fina arriba y con la punta redondeada."""
    camino = camino_cola()
    anillos = []

    def anillo(c, t, r):
        n = (t[1], -t[0])                                      # normal en el plano; la otra es +Z (n x t = +Z)
        return [(c[0] + r * n[0] * math.cos(a), c[1] + r * n[1] * math.cos(a), -r * math.sin(a))
                for a in (2 * math.pi * k / LADOS_COLA + math.pi / LADOS_COLA for k in range(LADOS_COLA))]
    for k, (u, v, r) in enumerate(camino):
        a, b = camino[max(0, k - 1)], camino[min(len(camino) - 1, k + 1)]
        tu, tv = b[0] - a[0], b[1] - a[1]
        largo = math.hypot(tu, tv)
        anillos.append(anillo((u, v), (tu / largo, tv / largo), r))
    # punta redondeada: dos anillos que se cierran y el remate, siguiendo la direccion del final
    (u0, v0, r0), (u1, v1, _) = camino[-2], camino[-1]
    tu, tv = u1 - u0, v1 - v0
    largo = math.hypot(tu, tv)
    tu, tv = tu / largo, tv / largo
    for d, k in ((0.55, 0.8), (1.0, 0.45)):
        anillos.append(anillo((u1 + tu * d * r0, v1 + tv * d * r0), (tu, tv), r0 * k))
    tubo = geo.loft_puntos(anillos, tapa_abajo=True, tapa_arriba=False)
    remate = geo.piramide(anillos[-1], (u1 + tu * 1.2 * r0, v1 + tv * 1.2 * r0, 0.0), tapa=False)
    m = geo.girar(geo.unir(tubo, remate), GIRO_COLA)
    return geo.mover(m, BASE_COLA)


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
    """Azul con anillos dorados parejos a lo largo de la cola y la punta negra. El largo se mide sobre la linea del
    medio (el punto mas cercano), asi los anillos dan la vuelta derechos al tubo."""
    u, v, _ = geo.desgirar((t.x, t.y, t.z), GIRO_COLA, BASE_COLA)
    k = min(range(len(FINO_COLA)), key=lambda i: (FINO_COLA[i][0] - u) ** 2 + (FINO_COLA[i][1] - v) ** 2)
    largo = LARGO_COLA[k]
    if k == len(FINO_COLA) - 1:                                            # pasando el final: la punta redonda
        largo += math.hypot(u - FINO_COLA[k][0], v - FINO_COLA[k][1])
    if largo > PUNTA_COLA:
        return hex_(NEGRO["b"])
    if any(a <= largo <= b for a, b in ANILLOS_COLA):
        return hex_(ORO["b"])
    return hex_(AZUL["b"] if largo < 9 else AZUL["s"])


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
    p.malla("Body/tunica", "tunica", geo.loft_puntos([falda, escalon] + abrigo, tapa_abajo=False), tunica)

    # ================================================================ ESTOLA en 3D sobre la panza, con punta
    ys = (15.0, 13.0, 11.0, 9.8, 8.0, 6.2, 4.6)
    frente = [(frente_tunica(y) - 0.12, y) for y in ys]
    perfil = frente + [(z + 0.45, y) for z, y in reversed(frente)]
    p.malla("Body/estola", "estola", geo.extruir_x(perfil, -1.8, 1.8), estola)
    zf = frente_tunica(4.6) - 0.12
    p.malla("Body/estola", "estola_punta", geo.extruir([(-1.8, 4.6), (0, 2.4), (1.8, 4.6)], zf, zf + 0.45), estola)

    # ================================================================ MANGAS crema acampanadas con puno negro
    anillos = [(7.6, 8.4, -0.4, 2.8, 2.8),        # abajo del puno
               (9.65, 8.1, -0.3, 3.0, 3.0),       # arriba del puno
               (17.2, 4.2, 0.0, 1.6, 1.6)]        # arriba: nace adentro del hombro, debajo del borde de la capucha
    p.malla_par("RightArm/manga", "manga", geo.loft(anillos, 8, 22.5), manga)

    # ================================================================ PIERNAS cortas y botas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        cx = s * 2.4
        p.malla(f"{hueso}/pierna", "pantalon", geo.loft([(3.2, cx, 0.2, 1.8, 1.8), (6.8, cx, 0.0, 2.3, 2.2)], 8, 22.5),
                negro_tela)
        p.malla(f"{hueso}/bota", "bota", geo.loft([(0.0, cx, -0.6, 2.1, 2.8), (1.6, cx, 0.0, 1.95, 2.1),
                                                (3.6, cx, 0.2, 1.85, 1.85)], 8, 22.5), bota)

    # ================================================================ COLA en gancho
    p.malla("Body/cola", "cola", cola(), cola_pintor)

    # ================================================================ JOYAS en 3D
    # aro con gema al costado izquierdo de la capucha (mira hacia afuera), y debajo rombos apilados
    # aro con gema al costado izquierdo de la capucha, mirando afuera y adelante, prendido con un broche
    centro = (-8.45, 23.0, -2.2)
    p.malla("Head/joyas", "aro", geo.mover(geo.girar(geo.aro(2.3, 1.5, 0.6), (0, 55, 0)), centro), oro_pintor)
    p.malla("Head/joyas", "gema", geo.bipiramide(centro, 0.75, 1.1, 1.1), gema)
    p.caja("Head/joyas", "broche", (-8.6, 24.9, -2.45), (-7.1, 25.5, -1.95), oro_pintor, dens=2)
    # colgantes de rombos apilados: el izquierdo cuelga del aro, el derecho sale de la capucha
    for tag, x, y0 in (("izq", -8.45, 20.9), ("der", 8.2, 22.2)):
        p.caja("Head/joyas", f"eslabon_{tag}", (x - 0.15, y0 - 0.7, -2.35), (x + 0.15, y0, -2.05), oro_pintor, dens=2)
        p.malla("Head/joyas", f"cuenta_{tag}", geo.bipiramide((x, y0 - 1.2, -2.2), 0.45, 0.5, 0.5), oro_pintor)
        p.caja("Head/joyas", f"eslabon2_{tag}", (x - 0.15, y0 - 2.4, -2.35), (x + 0.15, y0 - 1.7, -2.05), oro_pintor,
               dens=2)
        p.malla("Head/joyas", f"gota_{tag}", geo.bipiramide((x, y0 - 3.3, -2.2), 0.85, 0.9, 2.1), oro_pintor)
    return p
