"""
Bashi: las extremidades (ver bashi.py). Por ahora las MANOS, con colores lisos: manos de verdad con cinco dedos que
cuelgan de la manga (la palma mira hacia el cuerpo, los dedos hacia abajo y el pulgar adelante), cada dedo de un
largo distinto. Las piernas van despues.
"""

from .bashi import D, PIEL, giro_brazo
from .bashi_abrigo import caja

PALMA = ((4.95, 17.5, -1.0), (6.15, 19.3, 1.0))         # la palma (sin girar, mano derecha): delgada hacia los lados
DEDOS = ((-0.95, -0.55, 1.35), (-0.45, -0.05, 1.6), (0.05, 0.45, 1.5), (0.55, 0.92, 1.1))
# cada dedo: de z a z y largo, del indice (adelante) al menique (atras)
PULGAR = ((4.55, 17.1, -1.35), (5.25, 18.5, -0.85))


def manos(p):
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        g = f"{hueso}/mano"
        giro = giro_brazo(s)
        lado = lambda a, b: sorted((s * a, s * b))
        (x0, y0, z0), (x1, y1, z1) = PALMA
        xa, xb = lado(x0, x1)
        caja(p, g, "palma", (xa, y0, z0), (xb, y1, z1), PIEL, **giro)
        xa, xb = lado(x0 + 0.08, x1 - 0.12)
        for k, (za, zb, largo) in enumerate(DEDOS):
            caja(p, g, f"dedo{k}", (xa, y0 - largo, za), (xb, y0 + 0.1, zb), PIEL, **giro)
        (x0, y0, z0), (x1, y1, z1) = PULGAR
        xa, xb = lado(x0, x1)
        caja(p, g, "pulgar", (xa, y0, z0), (xb, y1, z1), PIEL, rot=(0, 0, giro["rot"][2]), piv=giro["piv"])


def extremidades(p):
    manos(p)
