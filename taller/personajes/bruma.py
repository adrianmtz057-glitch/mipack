"""
La Bruma: un espectro que flota (como un dementor). Diseno simple (las formas grandes), sin textura todavia.
  CAPUCHA honda que cae hacia adelante y acaba en punta; adentro solo el vacio negro (no tiene cara)
  TUNICA larga y oscura con pliegues hondos, que se abre hacia abajo y acaba en JIRONES desgarrados de distintos
    largos; no tiene piernas: flota
  MANGAS anchas y caidas, tambien desgarradas, y MANOS de hueso con dedos largos; la izquierda se estira hacia
    adelante (como en la referencia) y la derecha cuelga
  BRUMA: hilos de humo que se enroscan saliendo de abajo de la tunica
Medidas en px (16 por bloque); el frente es -Z, su derecha es +X. Mide unos 3 bloques de alto.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..luz import LUZ_SIMETRICA
from ..textura import hex_a_rgba as hex_
from .bloques import tubo, voxel
from .pibble import _anillo_oval, _doble, _plegar, _subdividir, _u_bata

D = 4

TELA = {"s": "#0E1114", "b": "#171C21", "l": "#232A31"}           # la tunica (negro verdoso)
TELA_C = {"s": "#151B1F", "b": "#1F272C", "l": "#2C363C"}         # los jirones, un poco mas claros
HUESO = {"s": "#4E5549", "b": "#6A7262", "l": "#8A927E"}          # las manos
HUMO = {"s": "#26313C", "b": "#34424F", "l": "#475766"}           # la bruma
VACIO = "#030405"

# la tunica: (y, medio ancho, medio hondo adelante, medio hondo atras); cerrada, en A
TUNICA = ((34.5, 5.0, 3.6, 3.6), (32.5, 7.6, 4.2, 4.4), (28.0, 7.4, 4.4, 4.8), (22.0, 7.9, 5.0, 5.6),
          (16.0, 8.7, 5.8, 6.4), (11.0, 9.5, 6.5, 7.2))
# la capucha: (y, medio ancho, medio hondo adelante, medio hondo atras, medio ancho de la abertura, z del centro)
CAPUCHA = ((34.0, 5.8, 4.8, 5.2, 0.4, 0.0), (36.5, 6.2, 5.4, 5.6, 2.8, -0.4), (39.5, 6.0, 5.6, 5.6, 3.5, -1.0),
           (42.5, 5.2, 5.2, 5.0, 3.0, -1.6), (44.8, 3.6, 3.8, 3.6, 1.6, -2.2), (46.4, 1.6, 2.0, 2.0, 0.3, -2.8))


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _norm(v):
    largo = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / largo for c in v)


def jiron(arriba_izq, arriba_der, largo, fuera, curva, filas=4):
    """Un jiron de tela (dos caras) que cuelga de una orilla (de arriba_izq a arriba_der), se angosta hasta la punta
    y se abre un poco hacia afuera (fuera: direccion, curva: cuanto)."""
    vs, cs = [], []
    medio = tuple((a + b) / 2 for a, b in zip(arriba_izq, arriba_der))
    lado = tuple((b - a) / 2 for a, b in zip(arriba_izq, arriba_der))
    for f in range(filas + 1):
        t = f / filas
        c = (medio[0] + fuera[0] * curva * t * t, medio[1] - largo * t, medio[2] + fuera[2] * curva * t * t)
        if f == filas:
            vs.append(c)
            break
        w = (1 - t) ** 0.8
        vs += [tuple(c[i] - lado[i] * w for i in range(3)), tuple(c[i] + lado[i] * w for i in range(3))]
    for f in range(filas - 1):
        a = 2 * f
        cs.append((a, a + 1, a + 3, a + 2))
    a = 2 * (filas - 1)
    cs.append((a, a + 1, len(vs) - 1))
    return _doble((vs, cs))


def tunica(p):
    tela, tela_c = voxel(TELA, 0.05), voxel(TELA_C, 0.05)
    g = "Body/tunica"
    anillos = []
    for i, (y, mx, mzf, mzb) in enumerate(TUNICA):
        f = (TUNICA[0][0] - y) / (TUNICA[0][0] - TUNICA[-1][0])
        aro = _subdividir(_anillo_oval(0.0, y, 0.0, mx, mzf, mzb), 2, cerrado=True)
        anillos.append(_plegar(aro, 0.2 + 1.1 * f, piso=i, cerrado=True)[0])
    p.malla(g, "tunica", geo.loft_puntos(anillos[::-1], tapa_abajo=False), tela, dens=D)
    # los jirones desgarrados que cuelgan de la orilla de abajo, de distintos largos
    orilla = anillos[-1]
    n = len(orilla)
    for k in range(n):
        a, b = orilla[k], orilla[(k + 1) % n]
        fuera = _norm(((a[0] + b[0]) / 2, 0.0, (a[2] + b[2]) / 2))
        largo = 4.0 + 7.0 * _azar(k * 3.3)
        p.malla(g, f"jiron{k}", jiron(a, b, largo, fuera, 1.5 + 2.0 * _azar(k * 5.1)), tela_c if k % 2 else tela,
                dens=D)
    # jirones mas largos encima (la tela rota en capas)
    for k in range(0, n, 2):
        a, b = orilla[k], orilla[(k + 1) % n]
        fuera = _norm(((a[0] + b[0]) / 2, 0.0, (a[2] + b[2]) / 2))
        a2 = tuple(a[i] + fuera[i] * 0.3 for i in range(3))
        b2 = tuple(b[i] + fuera[i] * 0.3 for i in range(3))
        a2, b2 = (a2[0], a2[1] + 4.0, a2[2]), (b2[0], b2[1] + 4.0, b2[2])
        p.malla(g, f"jiron_largo{k}", jiron(a2, b2, 9.0 + 5.0 * _azar(k * 7.7), fuera, 2.5), tela_c, dens=D)


def capucha(p):
    tela_ = voxel(TELA, 0.1)
    vacio = hex_(VACIO)

    def tela(t):                                              # por dentro, la capucha es el vacio
        return vacio if t.n[0] * t.x + t.n[2] * (t.z + 1.0) < 0 else tela_(t)
    g = "Head/capucha"
    anillos = []
    for y, mx, mzf, mzb, xo, cz in CAPUCHA:
        fuera = [(x, yy, z + cz) for x, yy, z in _u_bata(y, mx, mzf, mzb, xo)]
        dentro = [(x, yy, z + cz) for x, yy, z in _u_bata(y, mx, mzf, mzb, xo, 0.5)]
        anillos.append(fuera + dentro[::-1])
    p.malla(g, "capucha", geo.loft_puntos(anillos), tela, dens=D)
    # adentro, el vacio: no tiene cara
    p.caja("Head/vacio", "vacio", (-3.8, 34.5, -3.6), (3.8, 41.5, 2.0), lambda t: hex_(VACIO), dens=1, luz=False)


def manga(p, hueso, camino, radios, nombre):
    """Una manga ancha y caida a lo largo del camino del brazo (cortes de 8 lados), con jirones abajo de la boca."""
    tela, tela_c = voxel(TELA, 0.05), voxel(TELA_C, 0.05)
    anillos = []
    for i, (c, r) in enumerate(zip(camino, radios)):
        a, b = camino[max(0, i - 1)], camino[min(len(camino) - 1, i + 1)]
        t = _norm(tuple(b[k] - a[k] for k in range(3)))
        ref = (0.0, 1.0, 0.0) if abs(t[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm((t[1] * ref[2] - t[2] * ref[1], t[2] * ref[0] - t[0] * ref[2], t[0] * ref[1] - t[1] * ref[0]))
        w = (t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0])
        anillos.append([tuple(c[k] + r * (math.cos(2 * math.pi * j / 8) * u[k] + math.sin(2 * math.pi * j / 8) * w[k])
                              for k in range(3)) for j in range(8)])
    vs, cs = [], []
    for a in anillos:
        vs.extend(a)
    for j in range(len(anillos) - 1):
        for k in range(8):
            cs.append((j * 8 + k, j * 8 + (k + 1) % 8, (j + 1) * 8 + (k + 1) % 8, (j + 1) * 8 + k))
    p.malla(f"{hueso}/manga", nombre, _doble((vs, cs)), tela, dens=D)
    # los jirones que cuelgan de la boca de la manga (los de abajo, mas largos)
    boca = anillos[-1]
    for k in range(8):
        a, b = boca[k], boca[(k + 1) % 8]
        bajo = 1.0 - ((a[1] + b[1]) / 2 - min(q[1] for q in boca)) / max(1e-6, max(q[1] for q in boca) - min(q[1] for q in boca))
        fuera = _norm(tuple((a[i] + b[i]) / 2 - camino[-1][i] for i in range(3)))
        p.malla(f"{hueso}/manga", f"{nombre}_jiron{k}", jiron(a, b, 2.0 + 6.0 * bajo * (0.7 + 0.6 * _azar(k + len(nombre))),
                                                              fuera, 1.0), tela_c, dens=D)


def mano(p, hueso, muneca, adelante, abajo, nombre):
    """Mano de hueso: la palma y cuatro dedos largos de dos falanges que se curvan, y el pulgar."""
    hueso_ = voxel(HUESO, 0.1)
    lado = _norm((adelante[1] * abajo[2] - adelante[2] * abajo[1], adelante[2] * abajo[0] - adelante[0] * abajo[2],
                  adelante[0] * abajo[1] - adelante[1] * abajo[0]))
    palma = tuple(muneca[i] + adelante[i] * 1.6 for i in range(3))
    p.malla(f"{hueso}/mano", f"{nombre}_palma", tubo(muneca, palma, 0.9, 1.1, 4), hueso_, dens=D)
    for k, dx in enumerate((-0.9, -0.3, 0.3, 0.9)):
        base = tuple(palma[i] + lado[i] * dx for i in range(3))
        largo = 2.4 - 0.25 * abs(k - 1.5)
        medio = tuple(base[i] + adelante[i] * largo + abajo[i] * 0.4 for i in range(3))
        punta = tuple(medio[i] + adelante[i] * largo * 0.6 + abajo[i] * 1.3 for i in range(3))
        p.malla(f"{hueso}/mano", f"{nombre}_dedo{k}a", tubo(base, medio, 0.28, 0.24, 4), hueso_, dens=D)
        p.malla(f"{hueso}/mano", f"{nombre}_dedo{k}b", tubo(medio, punta, 0.24, 0.12, 4), hueso_, dens=D)
    pulgar = tuple(muneca[i] + adelante[i] * 0.8 - lado[i] * 1.0 for i in range(3))
    punta = tuple(pulgar[i] + adelante[i] * 1.4 - lado[i] * 0.9 + abajo[i] * 0.8 for i in range(3))
    p.malla(f"{hueso}/mano", f"{nombre}_pulgar", tubo(pulgar, punta, 0.28, 0.14, 4), hueso_, dens=D)


def brazos(p):
    # la derecha cuelga, un poco adelante
    manga(p, "RightArm", ((6.8, 32.5, 0.0), (8.6, 27.0, -1.0), (9.6, 21.5, -2.2)), (2.3, 2.8, 3.6), "manga")
    mano(p, "RightArm", (9.6, 20.2, -2.6), (0.05, -0.85, -0.5), (0.0, -0.4, 0.9), "mano")
    # la izquierda se estira hacia adelante
    manga(p, "LeftArm", ((-6.8, 32.5, 0.0), (-9.6, 28.0, -4.5), (-10.6, 25.0, -9.5)), (2.3, 2.8, 3.6), "manga")
    mano(p, "LeftArm", (-10.8, 24.4, -10.6), (-0.1, -0.25, -0.95), (0.0, -0.95, 0.25), "mano")


def bruma(p):
    """Hilos de humo que salen de abajo de la tunica y se enroscan hacia atras y abajo."""
    humo = voxel(HUMO, 0.1)
    for k in range(7):
        a0 = 2 * math.pi * k / 7 + 0.4
        pts = []
        for j in range(7):
            t = j / 6
            a = a0 + 1.6 * t
            r = 8.5 + 4.0 * t
            pts.append((math.cos(a) * r, 9.0 - 6.5 * t + 1.5 * math.sin(t * 6 + k), math.sin(a) * r + 4.0 * t))
        for j, (a, b) in enumerate(zip(pts, pts[1:])):
            r0, r1 = 1.4 * (1 - j / 6) + 0.2, 1.4 * (1 - (j + 1) / 6) + 0.2
            p.malla("Body/bruma", f"humo{k}_{j}", tubo(a, b, r0, r1, 6), humo, dens=2)


def construir():
    p = Personaje("bruma", altura=32)
    p.m.luz_desde = LUZ_SIMETRICA
    tunica(p)
    capucha(p)
    brazos(p)
    bruma(p)
    p.m.pivotes.update({"Head": (0.0, 34.0, 0.0), "Body": (0.0, 34.0, 0.0),
                        "RightArm": (6.8, 32.5, 0.0), "LeftArm": (-6.8, 32.5, 0.0)})
    return p
