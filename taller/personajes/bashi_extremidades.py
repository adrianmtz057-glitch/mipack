"""
Bashi: las extremidades (ver bashi.py). Por ahora las MANOS, con colores lisos: manos de verdad con cinco dedos
GORDITOS de bloque, como la hoja: cada dedo en dos tramos (el de la punta se dobla hacia la palma), separados entre
si, de largos distintos, y el pulgar grueso adelante, tambien en dos tramos. La mano cuelga del brazal: la palma
mira hacia el cuerpo y los dedos hacia abajo. Las piernas van despues.
"""

from .. import malla as geo
from .bashi import D, PIEL, giro_brazo, girar_brazo
from .bashi_abrigo import caja

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


def extremidades(p):
    manos(p)
