"""
Kemira, diosa de Thza (avatar). Se arma paso a paso siguiendo la hoja referencias/personajes/kemira_hoja.png.

Paso 1: la cabeza, un cubo liso del color de piel de la hoja (#A67556), y la diadema: cuadrada adelante y a los
costados, y atras se cierra en triangulo cortado al medio (termina recta), de punta a punta de la cabeza.
"""

import math

from ..kit import Personaje
from ..textura import hex_a_rgba as hex_
from .revolthir import color

D = 4

PIEL = "#A67556"                        # tomado de la paleta de la hoja
CAFE, CAFE_OSCURO, CREMA = "#54443A", "#3E3128", "#E4D8C4"


def tejido(t):
    """Banda cafe con una fila de triangulos crema."""
    u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
    v = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    if v < 0.18 or v > 0.82:
        return hex_(CAFE_OSCURO)
    tri = abs(((u * 0.9) % 1.0) - 0.5) * 2
    return hex_(CREMA if abs(v - (0.3 + 0.4 * tri)) < 0.09 else CAFE)


def diadema(p, y0, y1, lado=4.0, grosor=0.4, cola=2.6):
    """Diadema alrededor de la cabeza (de lado 2*lado): frente y costados rectos; atras, dos tramos a 45 grados que
    se cierran hacia el medio y una punta recta (el triangulo cortado al medio). cola: cuanto sale por detras."""
    g = "Head/diadema"
    a = lado + grosor
    p.caja(g, "frente", (-a, y0, -a), (a, y1, -lado), tejido, dens=D)
    for s in (1, -1):
        x1, x2 = sorted((s * lado, s * a))
        p.caja(g, f"costado{s}", (x1, y0, -a), (x2, y1, lado), tejido, dens=D)
        # tramo que se cierra: de la esquina de atras (s*a, lado) hacia (s*(a - cola), lado + cola)
        largo = cola * math.sqrt(2)
        cx, cz = s * (a - cola / 2), lado + cola / 2
        p.caja(g, f"cierre{s}", (cx - largo / 2, y0, cz - grosor / 2), (cx + largo / 2, y1, cz + grosor / 2), tejido,
               rot=(0, 45 * s, 0), piv=(cx, y0, cz), dens=D)
    ancho = a - cola                                             # la punta recta de atras
    p.caja(g, "punta", (-ancho - 0.1, y0, lado + cola - grosor / 2), (ancho + 0.1, y1, lado + cola + grosor / 2),
           tejido, dens=D)


def construir():
    p = Personaje("kemira", altura=36, cabeza=8, torso=(7.4, 12, 4.0), brazo=(2.6, 2.6), pierna=(3.4, 3.4))
    C, T = p.cuello, p.tope                                # 28, 36
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), color(PIEL), dens=D, luz=False)
    diadema(p, T - 2.6, T - 1.4)
    return p
