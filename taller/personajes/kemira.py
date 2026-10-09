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


def diadema(p, T, alto=3.8, grosor=0.4):
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


def pelo(p, C, T):
    """Pelo en capas parejas pegadas a la cabeza: la primera llega mas abajo y cada capa de encima es un poco mas
    gruesa hacia afuera y mas corta, con sus propias puntas; todas del mismo crema, unidas y sin sombras."""
    h = 4.0
    for capa, (o, sube) in enumerate(((0.4, 0.0), (0.8, 1.4), (1.2, 2.8))):
        g = "Head/pelo"
        n = f"{capa}"
        p.caja(g, "arriba" + n, (-h - o, T, -h - o), (h + o, T + 0.4, h + o), capa_pelo(0), dens=8, luz=False) if capa == 0 else None
        p.caja(g, "atras" + n, (-h - o, C, h), (h + o, T, h + o), capa_pelo(1.0 + sube), dens=8, luz=False)
        for s in (1, -1):
            a, b = sorted((s * h, s * (h + o)))
            p.caja(g, f"costado{s}_{n}", (a, C, -h - 0.4), (b, T, h), capa_pelo(1.6 + sube), dens=8, luz=False)
            if capa == 0:
                a, b = sorted((s * 2.9, s * h))
                p.caja(g, f"cortina{s}", (a, C, -h - 0.4), (b, T, -h), capa_pelo(2.6), dens=8, luz=False)
                a, b = sorted((s * 1.9, s * 2.9))
                p.caja(g, f"suelto{s}", (a, C, -h - 0.4), (b, T, -h), capa_pelo(6.3), dens=8, luz=False)
    p.caja("Head/pelo", "flequillo", (-1.9, C, -h - 0.4), (1.9, T, -h), capa_pelo(7.4), dens=8, luz=False)


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


def poner_figura(p, nombre, base, largo, ancho, rot, tono, punta=None, grosor=1.2, dobla=22):
    """Una figura del penacho en bloques cuadrados: un cuerpo ancho y una punta que se dobla 'dobla' grados mas
    (asi no queda recta). rot = (rx, 0, rz) desde la base."""
    x, y, z = base
    pint = figura(tono, punta)
    g = "Head/penacho"
    l1, l2 = largo * 0.62, largo * 0.38
    rx, _, rz = rot
    p.caja(g, nombre, (x - ancho / 2, y, z - grosor / 2), (x + ancho / 2, y + l1, z + grosor / 2), pint,
           rot=rot, piv=base, dens=D)
    a, c = math.radians(rx), math.radians(rz)                     # la junta, ya girada (orden Z * X)
    jy, jz = l1 * math.cos(a), l1 * math.sin(a)
    j = (x - jy * math.sin(c), y + jy * math.cos(c), z + jz)
    w2 = ancho * 0.7
    p.caja(g, nombre + "_p", (j[0] - w2 / 2, j[1], j[2] - grosor / 2 + 0.05), (j[0] + w2 / 2, j[1] + l2, j[2] + grosor / 2 - 0.05),
           pint, rot=(rx + dobla, 0, rz), piv=j, dens=D)


FX, FZ, BX, BZ = 4.1, -3.9, 2.2, 4.4                          # el trapecio de la diadema


def _azar(k):
    """Numero fijo entre 0 y 1 para la figura k (siempre el mismo: el penacho no cambia de un armado a otro)."""
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def penacho(p, T, C):
    """El pelo de arriba como un penacho de figuras 3D cuadradas que se doblan, desparejas y de tamanos distintos:
    llenan toda la diadema (sin pisarla), casi paradas; las de atras se abren hacia los costados. Donde no hay
    diadema (las esquinas de atras de la cabeza) salen figuras que caen hacia atras y abajo, abiertas a los lados.
    Desde el borde de atras de la diadema bajan otras hasta la nuca."""
    n = 70
    for k in range(n):
        f = (k + 0.5) / n
        z = FZ + 0.5 + (BZ - FZ - 1.0) * (0.6 * f + 0.4 * _azar(k))
        t = (z - FZ) / (BZ - FZ)
        mitad = FX + (BX - FX) * t - 0.4
        ancho = 1.3 + 1.9 * _azar(k + 50)
        q = 2 * ((k * 0.618 + 0.3 * _azar(k + 100)) % 1.0) - 1
        x = q * max(0.0, mitad - ancho / 2)
        largo = 2.6 + 5.0 * _azar(k + 150) ** 1.5 + 1.0 * t
        inclina = 2 + 12 * t + 10 * (_azar(k + 200) - 0.5)
        abre = -q * (6 + 34 * t) + 14 * (_azar(k + 250) - 0.5)        # atras se abren hacia los costados
        crema = _azar(k + 300) < 0.2
        tono = CREMA_PLUMA if crema else NEGRO
        punta = None if crema or _azar(k + 350) < 0.6 else CREMA_PLUMA["s"]
        poner_figura(p, f"figura{k}", (x, T + 0.4, z), largo, ancho, (inclina, 0, abre), tono, punta,
                     dobla=10 + 18 * _azar(k + 400))
    # las esquinas de atras, fuera de la diadema: caen hacia atras y abajo, abiertas a los costados
    k = 0
    for s in (1, -1):
        for i in range(9):
            z = -0.5 + 4.6 * i / 8
            t = (z - FZ) / (BZ - FZ)
            borde = FX + (BX - FX) * t + 0.5                         # justo afuera de la pared de la diadema
            x = s * (borde + (3.9 - borde) * _azar(k + 600))
            largo = 4.0 + 3.0 * _azar(k + 650)
            tono = CREMA_PLUMA if _azar(k + 700) < 0.2 else NEGRO
            poner_figura(p, f"cae{k}", (x, T + 0.4, z), largo, 1.4 + 1.2 * _azar(k + 750),
                         (110 + 30 * _azar(k + 800), 0, -s * (20 + 25 * _azar(k + 850))), tono, dobla=15)
            k += 1
    # del borde de atras de la diadema bajan figuras hacia la nuca, pegadas a la cabeza
    for k, x in enumerate((-2.6, -1.3, 0.0, 1.3, 2.6)):
        largo = 6.5 + 1.5 * _azar(k + 500)
        poner_figura(p, f"nuca{k}", (x, T + 1.2, BZ + 0.2), largo, 1.9, (176, 0, -x * 3), NEGRO if k % 2 == 0 else CREMA_PLUMA,
                     dobla=6)


def construir():
    p = Personaje("kemira", altura=36, cabeza=8, torso=(7.4, 12, 4.0), brazo=(2.6, 2.6), pierna=(3.4, 3.4))
    C, T = p.cuello, p.tope                                # 28, 36
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), cabeza, dens=8, luz=False)
    pelo(p, C, T)
    penacho(p, T, C)
    diadema(p, T)
    return p
