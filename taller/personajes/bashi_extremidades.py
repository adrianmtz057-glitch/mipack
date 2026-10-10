"""
Bashi: las extremidades (ver bashi.py), con colores lisos por ahora.

  MANOS de verdad con cinco dedos GORDITOS de bloque, como la hoja: cada dedo en dos tramos (el de la punta se dobla
    hacia la palma), separados entre si, de largos distintos, y el pulgar grueso adelante, tambien en dos tramos. La
    mano cuelga del brazal: la palma mira hacia el cuerpo y los dedos hacia abajo.
  PIERNAS: la derecha flaca con el pantalon en tres ESCALONES de bloque (cada uno un poco mas ancho, como las
    mangas), el tobillo flaco y un zapato de cuero; la izquierda es una PATA DE PALO: el pantalon se rompe en la
    rodilla (tiras disparejas) y de ahi para abajo el palo cafe de 8 lados que se angosta, con su encaje arriba y
    una correa que lo amarra.
"""

import math

from .. import malla as geo
from .bashi import CUERO_OSC, D, MADERA, PIEL, VINO, azar, giro_brazo, girar_brazo
from .bashi_abrigo import anillo, bloque, caja, oscuro, plano, tira

PALMA = ((4.85, 17.0, -1.1), (6.15, 18.8, 1.1))         # la palma (sin girar, mano derecha)
GRUESO_DEDO = 0.82                                       # de canto (hacia los lados)
DEDOS = ((-1.1, -0.57, 1.05, 0.8), (-0.53, 0.0, 1.2, 0.9), (0.04, 0.57, 1.1, 0.85), (0.61, 1.1, 0.85, 0.65))
# cada dedo, del indice (adelante) al menique (atras): de z a z, largo del primer tramo y de la punta
DOBLA = 28.0                                             # grados que la punta se dobla hacia la palma
PULGAR = ((4.95, 18.3, -1.0), (1.1, 0.85), (20.0, 35.0), (15.0, 22.0))
# base (sin girar), largos de los dos tramos, cuanto se va adelante y cuanto hacia la palma cada tramo


def colgando(p, g, nombre, punta, largo, ancho_x, ancho_z, rot):
    """Un tramo de dedo que cuelga desde 'punta' (ya girada, en el mundo), girado 'rot' desde ahi."""
    x, y, z = punta
    caja(p, g, nombre, (x - ancho_x / 2, y - largo, z - ancho_z / 2), (x + ancho_x / 2, y + 0.08, z + ancho_z / 2),
         PIEL, rot=rot, piv=punta)


def manos(p):
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        g = f"{hueso}/mano"
        giro = giro_brazo(s)
        rz = giro["rot"][2]
        (x0, y0, z0), (x1, y1, z1) = PALMA
        xa, xb = sorted((s * x0, s * x1))
        caja(p, g, "palma", (xa, y0, z0), (xb, y1, z1), PIEL, **giro)
        xc = s * (x0 + x1) / 2
        for k, (za, zb, l1, l2) in enumerate(DEDOS):
            zc = (za + zb) / 2
            nudillo = girar_brazo((xc, y0 + 0.05, zc), s)
            colgando(p, g, f"dedo{k}", nudillo, l1, GRUESO_DEDO, zb - za, (0, 0, rz))
            junta = girar_brazo((xc, y0 + 0.05 - l1, zc), s)
            colgando(p, g, f"dedo{k}_punta", junta, l2, GRUESO_DEDO * 0.92, (zb - za) * 0.92, (0, 0, rz - s * DOBLA))
        (bx, by, bz), (l1, l2), (adelante1, adelante2), (adentro1, adentro2) = PULGAR
        base = (s * bx, by, bz)
        colgando(p, g, "pulgar", girar_brazo(base, s), l1, 0.85, 0.75, (adelante1, 0, rz - s * adentro1))
        fin = geo.girar(([(base[0], by - l1, bz)], []), (adelante1, 0, -s * adentro1), base)[0][0]
        colgando(p, g, "pulgar_punta", girar_brazo(fin, s), l2, 0.78, 0.7, (adelante2, 0, rz - s * adentro2))


CENTRO_PIERNA = 2.0                     # x del medio de cada pierna
PANTALON = ((12.5, 18.5, 1.55, 1.6, 0.4), (8.6, 12.7, 1.7, 1.75, 0.45), (4.6, 8.8, 1.85, 1.9, 0.5))
# los escalones del pantalon, de arriba abajo: (y de abajo, y de arriba, medio ancho, medio hondo, esquina)
RODILLA_ROTA = 9.6                      # en la pata de palo el pantalon se rompe aqui
TOBILLO = ((1.6, 0.75, 0.8, 0.2), (4.9, 0.75, 0.8, 0.2))
ZAPATO = ((0.0, 1.8), 1.25, (-2.6, 1.4), 0.4)            # alto, medio ancho, de z a z (la punta adelante), esquina
PALO = ((0.0, 0.55), (0.4, 0.6), (8.4, 0.8))             # el palo de 8 lados: (y, radio) de abajo hacia arriba
ENCAJE = ((8.2, 1.0), (10.0, 1.05))                      # donde entra el muslo, arriba del palo
CORREA_PALO = (9.15, 9.6, 1.12)


def escalon(cx, y0, y1, mx, mz, ch):
    return bloque([(y0, mx, mz, ch), (y1, mx, mz, ch)], cx)


def piernas(p):
    """La pierna derecha con su pantalon escalonado y el zapato; la izquierda de palo, con el pantalon roto en la
    rodilla."""
    # derecha
    g, cx = "RightLeg/pantalon", CENTRO_PIERNA
    for k, (y0, y1, mx, mz, ch) in enumerate(PANTALON):
        p.malla(g, f"escalon{k}", escalon(cx, y0, y1, mx, mz, ch), plano(VINO), dens=D)
    p.malla("RightLeg/pierna", "tobillo", bloque(TOBILLO, cx), plano(PIEL), dens=D)
    (ya, yb), mx, (za, zb), ch = ZAPATO
    zc, mz = (za + zb) / 2, (zb - za) / 2
    zapato = geo.loft_puntos([anillo(cx, ya, mx, mz, ch, zc), anillo(cx, yb, mx, mz, ch, zc)])
    p.malla("RightLeg/zapato", "zapato", zapato, plano(CUERO_OSC), dens=D)
    # izquierda: el pantalon hasta la rodilla, roto en tiras, y la pata de palo
    g, cx = "LeftLeg/pantalon", -CENTRO_PIERNA
    (y0, y1, mx, mz, ch) = PANTALON[0]
    p.malla(g, "escalon0", escalon(cx, y0, y1, mx, mz, ch), plano(VINO), dens=D)
    (_, y1, mx, mz, ch) = PANTALON[1]
    p.malla(g, "escalon1", escalon(cx, RODILLA_ROTA, y1, mx, mz, ch), plano(VINO), dens=D)
    for k in range(9):                                           # las tiras rotas alrededor de la rodilla
        ang = 360.0 * (k + 0.3 * azar(k, 70)) / 9
        a = math.radians(ang)
        x, z = cx + (mx - 0.1) * math.sin(a), (mz - 0.1) * math.cos(a)
        largo = 0.5 + 0.7 * azar(k, 71)
        m = geo.girar(tira(0.85, largo, 400 + k, grueso=0.3), (10 + 6 * azar(k, 72), ang - 180, 0))
        p.malla(g, f"roto{k}", geo.mover(m, (x, RODILLA_ROTA + 0.25, z)), oscuro(VINO), dens=D)
    g = "LeftLeg/palo"
    palo = geo.loft_puntos([geo.anillo(cx, y, 0.0, r, r, 8, 22.5) for y, r in PALO])
    p.malla(g, "palo", palo, plano(MADERA), dens=D)
    encaje = geo.loft_puntos([geo.anillo(cx, y, 0.0, r, r, 8, 22.5) for y, r in ENCAJE])
    p.malla(g, "encaje", encaje, oscuro(MADERA), dens=D)
    ya, yb, r = CORREA_PALO
    p.malla(g, "correa", geo.loft_puntos([geo.anillo(cx, y, 0.0, r, r, 8, 22.5) for y in (ya, yb)]),
            plano(CUERO_OSC), dens=D)


def extremidades(p):
    manos(p)
    piernas(p)
