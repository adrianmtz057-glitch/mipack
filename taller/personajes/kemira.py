"""
Kemira, diosa de Thza (avatar). Se arma paso a paso siguiendo la hoja referencias/personajes/kemira_hoja.png.

Paso 1: la cabeza, un cubo liso del color de piel de la hoja (#A67556), y la diadema alta sobre la cabeza: vista
desde arriba es un trapecio (adelante de punta a punta de la frente, se cierra hacia atras y termina recta), con
flecos de cuentas colgando adelante.
"""

import math

from ..kit import Personaje
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .revolthir import color

D = 4

PIEL = "#A67556"                        # tomado de la paleta de la hoja
CUELLO = 28.0
CAFE, CAFE_OSCURO, CREMA = "#54443A", "#3E3128", "#E4D8C4"


def tejido(t):
    """Banda cafe con una fila de triangulos crema."""
    u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
    v = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    if v < 0.18 or v > 0.82:
        return hex_(CAFE_OSCURO)
    tri = abs(((u * 0.9) % 1.0) - 0.5) * 2
    return hex_(CREMA if abs(v - (0.3 + 0.4 * tri)) < 0.09 else CAFE)


def diadema(p, T, alto=3.0, grosor=0.4):
    """Diadema alta encima de la cabeza (sujeta del pelo, no en la frente), vista desde arriba es un trapecio: adelante, de punta a punta de la frente;
    los costados se cierran hacia atras y termina recta en la nuca. Adelante cuelgan flecos de cuentas."""
    g = "Head/diadema"
    y0, y1 = T - 0.4, T - 0.4 + alto                            # arriba de la cabeza, sujeta del pelo
    fx, fz = 4.1, -3.9                                           # esquinas de adelante: sobresale apenas
    bx, bz = 2.2, 4.4                                            # esquinas de atras: llega hasta la nuca
    p.caja(g, "frente", (-fx - 0.15, y0, fz - grosor), (fx + 0.15, y1, fz), tejido, dens=D)
    for s in (1, -1):
        dx, dz = bx - fx, bz - fz
        largo = math.hypot(dx, dz)
        ang = math.degrees(math.atan2(dz, abs(dx)))              # giro en Y para que el largo siga el costado
        cx, cz = s * (fx + bx) / 2, (fz + bz) / 2
        p.caja(g, f"costado{s}", (cx - largo / 2, y0, cz - grosor / 2), (cx + largo / 2, y1, cz + grosor / 2),
               tejido, rot=(0, ang * s, 0), piv=(cx, y0, cz), dens=D)
    p.caja(g, "atras", (-bx - 0.2, y0, bz - grosor / 2), (bx + 0.2, y1, bz + grosor / 2), tejido, dens=D)
    # flecos de cuentas que cuelgan del frente
    for k, x in enumerate((-2.4, -1.6, -0.8, 0.0, 0.8, 1.6, 2.4)):
        largo = (1.4, 2.0, 1.6, 2.4, 1.6, 2.0, 1.4)[k]
        for i in range(int(largo / 0.4)):
            y = y0 - 0.4 * (i + 1)
            p.caja(g, f"cuenta{k}_{i}", (x - 0.15, y, fz - grosor - 0.1), (x + 0.15, y + 0.4, fz - grosor + 0.2),
                   color(CREMA if (i + k) % 2 else CAFE), dens=D)


PELO, PELO_SOMBRA = "#E2D6C2", "#D3C6B0"


def _puntas(u, base, paso=0.5):
    """Borde de abajo del pelo en mechones: cada columna de 'paso' baja un poco distinto."""
    k = int((u + 50) // paso)
    return base - (0.0, 0.6, 0.25, 0.9, 0.4)[k % 5]


def cabeza(t):
    """La cabeza con el pelo pintado encima, pegado al cubo (nada sobresale y sin sombras): arriba todo crema; a los
    costados y atras baja en mechones; adelante, cortinas a los lados de la cara y un mechon suelto en cada borde
    de la frente. El resto, piel."""
    v = t.y - CUELLO
    if t.cara == "up":
        return hex_(PELO)
    if t.cara == "down":
        return hex_(PIEL)
    if t.cara == "north":
        u, au = -t.x, abs(-t.x)
        if v > 7.4 or (au > 2.9 and v > _puntas(u, 2.6)) or (1.9 < au <= 2.9 and v > _puntas(u, 6.3)):
            return hex_(PELO_SOMBRA if 2.85 < au < 3.0 or 1.85 < au < 1.95 else PELO)
        return hex_(PIEL)
    u = t.z if t.cara in ("east", "west") else t.x
    base = 1.6 if t.cara in ("east", "west") else 1.0
    return hex_(PELO) if v > _puntas(u, base) else hex_(PIEL)


def capa_pelo(base):
    """Pintor de la capa de pelo: crema liso; por debajo de 'base' (con puntas en mechones) queda transparente."""
    def p(t):
        if t.cara not in ("up", "down"):
            u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
            if t.y - CUELLO < _puntas(u, base):
                return TRANSPARENTE
        return hex_(PELO)
    return p


def pelo(p, C, T, o=0.4):
    """Pelo en 3D como una sola capa de grosor parejo (o) pegada a la cabeza: arriba, atras, a los costados y las
    cortinas de adelante, todas unidas, del mismo crema y sin sombras; nada mas gordo ni que sobresalga."""
    g = "Head/pelo"
    h = 4.0
    p.caja(g, "arriba", (-h - o, T, -h - o), (h + o, T + o, h + o), capa_pelo(0), dens=8, luz=False)
    p.caja(g, "atras", (-h - o, C, h), (h + o, T, h + o), capa_pelo(1.0), dens=8, luz=False)
    for s in (1, -1):
        a, b = sorted((s * h, s * (h + o)))
        p.caja(g, f"costado{s}", (a, C, -h - o), (b, T, h), capa_pelo(1.6), dens=8, luz=False)
        a, b = sorted((s * 2.9, s * h))
        p.caja(g, f"cortina{s}", (a, C, -h - o), (b, T, -h), capa_pelo(2.6), dens=8, luz=False)
        a, b = sorted((s * 1.9, s * 2.9))
        p.caja(g, f"suelto{s}", (a, C, -h - o), (b, T, -h), capa_pelo(6.3), dens=8, luz=False)
    p.caja(g, "flequillo", (-1.9, C, -h - o), (1.9, T, -h), capa_pelo(7.4), dens=8, luz=False)


NEGRO = {"s": "#1E1C1E", "b": "#2B2829", "l": "#3B3637"}
CREMA_PLUMA = {"s": "#CDBFA8", "b": "#E4D8C4", "l": "#F2EADB"}


def figura(tono, punta=None):
    """Pintor de una figura del penacho: el tono con el canto un poco mas claro; con punta, el ultimo tramo crema."""
    def p(t):
        v = (t.fila_abajo + 0.5) / t.th
        if punta and v > 0.78 and t.cara not in ("up", "down"):
            return hex_(punta)
        u = abs((t.i + 0.5) / t.tw * 2 - 1)
        return hex_(tono["l"] if u > 0.78 else tono["b"])
    return p


def poner_figura(p, nombre, base, largo, ancho, rot, tono, punta=None, grosor=0.8):
    """Una figura en bloques (como una pluma): el cuerpo y una punta mas angosta, giradas juntas desde la base."""
    x, y, z = base
    pint = figura(tono, punta)
    g = "Head/penacho"
    p.caja(g, nombre, (x - ancho / 2, y, z - grosor / 2), (x + ancho / 2, y + largo * 0.75, z + grosor / 2), pint,
           rot=rot, piv=base, dens=D)
    p.caja(g, nombre + "_p", (x - ancho * 0.3, y + largo * 0.75, z - grosor / 2 + 0.05),
           (x + ancho * 0.3, y + largo, z + grosor / 2 - 0.05), pint, rot=rot, piv=base, dens=D)


def penacho(p, T):
    """El pelo de arriba como un penacho de figuras 3D: nace en la mitad de la frente (adentro de la diadema) y va
    hacia atras en filas; adelante figuras cortas y paradas, atras mas largas, mas abiertas hacia los costados y
    vencidas hacia atras hasta caer por la espalda. Casi todas negras, algunas crema."""
    filas = 6
    for r in range(filas):
        f = r / (filas - 1)                                        # 0 adelante, 1 atras
        z = -2.6 + 6.4 * f
        mitad = 1.6 + 0.9 * f * 0 + (4.1 - 1.9 * f) * 0.55         # medio ancho del trapecio a esa altura, adentro
        n = 3 + r
        abre = 18 + 70 * f
        for k in range(n):
            a = -abre + 2 * abre * k / max(1, n - 1) if n > 1 else 0.0
            x = mitad * (a / abre if abre else 0) * 0.8
            largo = (7.5 + 6.5 * f) * (1.0 - 0.12 * abs(a) / 90)
            crema = (r >= 2 and (k + r) % 5 == 0) or (r == filas - 1 and k == n // 2)
            tono = CREMA_PLUMA if crema else NEGRO
            punta = None if crema or (k + r) % 3 else CREMA_PLUMA["s"]
            poner_figura(p, f"figura{r}_{k}", (x, T + 0.5, z), largo, 2.4 + 0.8 * f, (-8 - 45 * f, 0, -a),
                         tono, punta)


def construir():
    p = Personaje("kemira", altura=36, cabeza=8, torso=(7.4, 12, 4.0), brazo=(2.6, 2.6), pierna=(3.4, 3.4))
    C, T = p.cuello, p.tope                                # 28, 36
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), cabeza, dens=8, luz=False)
    pelo(p, C, T)
    penacho(p, T)
    diadema(p, T)
    return p
