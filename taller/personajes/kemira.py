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
        return mechones(t.x, t.z, -99)
    if t.cara == "down":
        return hex_(PIEL)
    if t.cara == "north":
        u, au = -t.x, abs(-t.x)
        if v > 7.4 or (au > 2.9 and v > _puntas(u, 2.6)) or (1.9 < au <= 2.9 and v > _puntas(u, 6.3)):
            return mechones(u, v, -99)
        return hex_(PIEL)
    u = t.z if t.cara in ("east", "west") else t.x
    base = 1.6 if t.cara in ("east", "west") else 1.0
    return mechones(u, v, _puntas(u, base)) if v > _puntas(u, base) else hex_(PIEL)


PELO_TONOS = ("#D3C6B0", "#E2D6C2", "#E9DFCD", "#F2EADB")     # sombra, base, medio, luz


def mechones(u, v, borde):
    """Textura de mechones del pelo blanco: tiras verticales de 0.5 px con su tono (un patron fijo), una linea mas
    oscura entre mechon y mechon, y las puntas un poco mas oscuras cerca del borde de abajo."""
    k = int((u + 50) // 0.5)
    tono = (1, 2, 1, 3, 2, 1, 2, 0)[k % 8]
    if ((u + 50) % 0.5) < 0.07:
        tono = 0
    if v - borde < 0.5:
        tono = max(0, tono - 1)
    elif (v * 1.3 + k * 0.37) % 2.2 < 0.12:                       # un brillo cortito suelto en algunos mechones
        tono = 3
    return hex_(PELO_TONOS[tono])


def capa_pelo(base):
    """Pintor de una capa de pelo: mechones crema; por debajo de 'base' (con puntas) queda transparente."""
    def p(t):
        if t.cara in ("up", "down"):
            return mechones(t.x, t.z, -99)
        u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
        v = t.y - CUELLO
        borde = _puntas(u, base)
        if v < borde:
            return TRANSPARENTE
        return mechones(u, v, borde)
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


def poner_figura(p, nombre, base, largo, ancho, rot, tono, punta=None, grosor=1.2, dobla=22, grupo="Head/penacho",
                 luz=True, pintor=None):
    """Una figura del penacho en bloques cuadrados: un cuerpo ancho y una punta que se dobla 'dobla' grados mas
    (asi no queda recta). rot = (rx, 0, rz) desde la base."""
    x, y, z = base
    pint = pintor or figura(tono, punta)
    g = grupo
    l1, l2 = largo * 0.62, largo * 0.38
    rx, ry, rz = rot
    p.caja(g, nombre, (x - ancho / 2, y, z - grosor / 2), (x + ancho / 2, y + l1, z + grosor / 2), pint,
           rot=rot, piv=base, dens=D, luz=luz)
    from .. import malla as geo
    j = geo.girar(([(x, y + l1, z)], []), rot, base)[0][0]      # la junta, ya girada
    w2 = ancho * 0.7
    p.caja(g, nombre + "_p", (j[0] - w2 / 2, j[1], j[2] - grosor / 2 + 0.05), (j[0] + w2 / 2, j[1] + l2, j[2] + grosor / 2 - 0.05),
           pint, rot=(rx + dobla, ry, rz), piv=j, dens=D, luz=luz)


FX, FZ, BX, BZ = 4.1, -3.9, 2.2, 4.4                          # el trapecio de la diadema


def _azar(k):
    """Numero fijo entre 0 y 1 para la figura k (siempre el mismo: el penacho no cambia de un armado a otro)."""
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def penacho(p, T, C):
    """El pelo de arriba como un penacho de figuras 3D cuadradas que se doblan, desparejas y de tamanos distintos:
    llenan toda la diadema (sin pisarla), casi paradas; las de atras se abren hacia los costados. Donde no hay
    diadema (las esquinas de atras de la cabeza) salen figuras que caen hacia atras y abajo, abiertas a los lados.
    Desde el borde de atras de la diadema bajan otras hasta la nuca, abiertas hacia los costados."""
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
    # la melena de atras: muchas figuras que salen de la parte de atras y los costados de la cabeza (y de las
    # esquinas de atras de arriba, donde no hay diadema) y se abren hacia afuera, a los lados y hacia abajo
    n = 90
    for k in range(n):
        phi = -115 + 230 * ((k * 0.618) % 1.0)                    # 0 = derecho hacia atras
        alto = _azar(k + 600)
        y = C + 2.0 + (T + 0.6 - C - 2.0) * alto
        rad = math.radians(phi)
        r = 4.3 / max(abs(math.sin(rad)), abs(math.cos(rad)))     # sobre el borde de la cabeza cuadrada
        x, z = r * math.sin(rad), r * math.cos(rad)
        if z < 0.0:                                               # nada adelante de las orejas
            continue
        elev = -60 + 55 * alto + 16 * (_azar(k + 650) - 0.5)     # salen hacia afuera y caen; las de arriba algo mas paradas
        largo = 4.0 + 4.5 * _azar(k + 700)
        tono = CREMA_PLUMA if _azar(k + 750) < 0.2 else NEGRO
        punta = None if tono is CREMA_PLUMA or _azar(k + 760) < 0.6 else CREMA_PLUMA["s"]
        poner_figura(p, f"melena{k}", (x, y, z), largo, 1.4 + 1.6 * _azar(k + 800),
                     (90 - elev, phi, 0), tono, punta, dobla=12 + 16 * _azar(k + 850))      # la punta cae


def piel(t):
    return hex_(PIEL)


BUSTO = ((3.5, 22.8, 25.9, -2.0), (3.2, 23.1, 25.4, -2.6), (2.6, 23.5, 24.9, -3.2))   # (medio ancho, abajo, arriba, z de atras)


def cuerpo(p, C, L):
    """La base del cuerpo, sin ropa: hombros y torax anchos, busto, cintura marcada, cadera ancha con gluteos,
    muslos gruesos que se afinan a la rodilla, pantorrillas con volumen y brazos de hombro redondo. Piel lisa."""
    g = "Body/cuerpo"
    caja = lambda grupo, n, a, b: p.caja(grupo, n, a, b, piel, dens=D, luz=False)
    caja(g, "torax", (-3.8, 22.6, -2.0), (3.8, C, 2.0))
    for k, (x, y0, y1, z) in enumerate(BUSTO):                     # busto en capas: redondo de perfil
        caja(g, f"busto{k}", (-x, y0, z - 0.6), (x, y1, z))
    caja(g, "cintura", (-2.9, 19.4, -1.7), (2.9, 22.6, 1.7))
    caja(g, "cadera_alta", (-3.6, 18.2, -2.0), (3.6, 19.4, 2.0))
    caja(g, "cadera", (-4.2, L - 0.6, -2.2), (4.2, 18.2, 2.2))
    caja(g, "gluteos", (-3.9, L - 1.2, 2.0), (3.9, 17.6, 2.85))
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        gb = f"{hueso}/brazo"
        x1, x2 = sorted((s * 3.8, s * 6.4))
        caja(gb, "hombro", (x1, C - 2.6, -1.45), (x2 + s * 0.15, C + 0.2, 1.45))
        caja(gb, "brazo", (x1, 20.4, -1.3), (x2, C - 2.6, 1.3))
        f1, f2 = sorted((s * 3.95, s * 6.25))
        caja(gb, "antebrazo", (f1, L, -1.15), (f2, 20.4, 1.15))
        caja(gb, "mano", (f1, L - 2.4, -1.05), (f2, L, 1.05))
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        gl = f"{hueso}/pierna"
        m1, m2 = sorted((s * 0.0, s * 4.2))
        caja(gl, "muslo", (m1, 9.6, -2.2), (m2, L, 2.2))
        r1, r2 = sorted((s * 0.3, s * 3.7))
        caja(gl, "rodilla", (r1, 7.4, -1.85), (r2, 9.6, 1.85))
        c1, c2 = sorted((s * 0.4, s * 3.6))
        caja(gl, "pantorrilla", (c1, 1.2, -1.6), (c2, 7.4, 1.7))
        caja(gl, "gemelo", (c1 + s * 0.2 if s > 0 else c1 + 0.2, 3.6, 1.7), (c2 - 0.2 if s > 0 else c2 - 0.2, 6.6, 2.3))
        caja(gl, "pie", (c1, 0.0, -2.6), (c2, 1.2, 1.7))


NEGRO_ROPA = "#262325"


def top_v(t):
    """Top negro con el escote en V: el borde de arriba baja al medio del pecho; atras rodea la espalda derecho."""
    if t.cara in ("up", "down"):
        return hex_(NEGRO_ROPA)
    if t.n[2] < -0.5:                                              # adelante: la V
        corte = 24.5 + 1.5 * min(1.0, abs(t.x) / 3.4)
        return TRANSPARENTE if t.y > corte else hex_(NEGRO_ROPA)
    return hex_(NEGRO_ROPA) if t.y < 25.4 else TRANSPARENTE


def ropa(p, L):
    """Un top negro con escote en V que rodea el pecho y la espalda, y una falda de plumas como taparrabo: plumas 2D
    chicas de blanco y negro puros, en capas adelante y atras, en V; los costados sin plumas."""
    g = "Body/ropa"
    p.caja(g, "top", (-3.9, 22.3, -2.1), (3.9, 26.0, 2.1), top_v, dens=D, luz=False)
    for k, (x, y0, y1, z) in enumerate(BUSTO):
        p.caja(g, f"top_busto{k}", (-x - 0.1, y0 - 0.1, z - 0.7), (x + 0.1, y1 + 0.1, z - 0.05), top_v, dens=D, luz=False)
    falda(p, L)


def falda(p, L):
    """Falda tribal armada en orden, como se arma en Blockbench: cinturon de cuero con triangulos, una base oscura
    con el borde roto, tiras negras de distintos tamanos en tres profundidades (largas al medio, cortas a los
    costados con alguna punta hacia afuera, mas tiras atras) y plumas blancas concentradas en el frente, con la
    punta escalonada y algunas tiras negras por delante."""
    g = "Body/falda"
    oscuro = lambda col: (lambda t: hex_(col))
    # 1. cinturon: banda de cuero con triangulos y una banda mas angosta encima
    p.caja(g, "cinturon", (-4.4, L + 0.8, -2.55), (4.4, L + 1.8, 3.15), tejido, dens=D, luz=False)
    p.caja(g, "cinturon_alto", (-4.3, L + 1.8, -2.45), (4.3, L + 2.2, 3.05), oscuro(CAFE_OSCURO), dens=D, luz=False)
    # 2. base oscura alrededor de la cadera, con el borde de abajo roto en bloquecitos
    p.caja(g, "base", (-4.3, L - 2.2, -2.45), (4.3, L + 0.8, 3.05), oscuro(NEGRO_PURO), dens=D, luz=False)
    for k in range(10):
        x = -4.0 + 8.0 * k / 9
        for lado, z0, z1 in ((-1, -2.5, -2.0), (1, 2.6, 3.1)):
            baja = 0.4 + 1.0 * _azar(k * 2 + (lado > 0) + 1000)
            p.caja(g, f"borde{k}_{lado}", (x - 0.4, L - 2.2 - baja, z0), (x + 0.4, L - 2.2, z1), oscuro(NEGRO_PURO),
                   dens=D, luz=False)

    def tira(nombre, x, z, ancho, grueso, largo, col, giro=0.0, escalon=True):
        """Una tira colgante (prisma) con la punta escalonada: un bloquecito mas angosto debajo, corrido adentro."""
        y1 = L + 0.8
        p.caja(g, nombre, (x - ancho / 2, y1 - largo, z - grueso / 2), (x + ancho / 2, y1, z + grueso / 2), oscuro(col),
               rot=(0, 0, giro), piv=(x, y1, z), dens=D, luz=False)
        if escalon:
            corre = (0.15 if x < 0 else -0.15) * ancho
            p.caja(g, nombre + "_punta", (x + corre - ancho * 0.25, y1 - largo - 0.8, z - grueso / 2 + 0.1),
                   (x + corre + ancho * 0.25, y1 - largo, z + grueso / 2 - 0.1), oscuro(col),
                   rot=(0, 0, giro), piv=(x, y1, z), dens=D, luz=False)

    negros = (NEGRO_PURO, "#222022")
    k = 0
    # 3. tiras negras del frente y de atras, en tres profundidades (adentro, al medio y afuera)
    for lado, zs in ((-1, -2.45), (1, 3.05)):
        for capa in range(3):
            for i in range(7 - capa):
                x = -3.8 + 7.6 * (i + 0.5 * capa + 0.4 * _azar(k + 1100)) / (6.4 - capa)
                x = max(-3.9, min(3.9, x))
                if lado < 0 and capa == 2 and abs(x) < 2.3:            # el centro de adelante queda para las blancas
                    continue
                centro = 1 - min(1.0, abs(x) / 4.0)
                largo = 3.0 + 3.0 * _azar(k + 1150) + 3.2 * centro ** 1.4 + (0.8 if lado > 0 else 0.0)
                tira(f"tira{k}", x, zs + lado * (0.3 + 0.35 * capa), 1.0 + 1.0 * _azar(k + 1200),
                     0.8 + 0.4 * _azar(k + 1250), largo, negros[k % 2])
                k += 1
    # 4. tiras cortas a los costados, alguna con la punta hacia afuera
    for s in (1, -1):
        for i in range(4):
            z = -1.6 + 3.8 * i / 3
            tira(f"lado{k}", s * 4.5, z, 1.0, 1.0 + 0.6 * _azar(k + 1300), 2.4 + 1.8 * _azar(k + 1350), negros[k % 2],
                 giro=s * 14 * _azar(k + 1400))
            k += 1
    # 5. plumas blancas concentradas en el frente: una larga al medio, dos medianas, varias cortas entre las negras
    claras = ((0.0, 9.0, 1.4), (-1.5, 6.6, 1.2), (1.5, 6.6, 1.2), (-2.8, 4.2, 1.0), (2.8, 4.2, 1.0),
              (-0.8, 3.4, 0.9), (0.8, 3.6, 0.9), (-3.6, 3.0, 0.9), (3.5, 3.2, 0.9))
    for i, (x, largo, ancho) in enumerate(claras):
        tira(f"clara{i}", x, -2.45 - 1.15 - 0.2 * (i % 2), ancho, 0.6, largo, BLANCO_PURO)
    for i, x in enumerate((-2.1, 2.1, -0.4)):                     # tiras negras por delante de las puntas claras
        tira(f"delante{i}", x, -2.45 - 1.65, 0.7, 0.5, 4.6 + 1.2 * _azar(i + 1500), NEGRO_PURO)
    for i, x in enumerate((-2.0, 0.0, 2.0)):                      # alguna clara atras, entre las negras
        tira(f"clara_atras{i}", x, 3.05 + 1.15, 1.0, 0.6, 4.0 + 2.0 * (x == 0.0), BLANCO_PURO)


BLANCO_PURO, NEGRO_PURO = "#FFFFFF", "#141414"


def pluma_plana(col):
    """Pluma 2D de color puro: un plano recortado con la punta hacia abajo (se angosta en el ultimo tramo)."""
    def p(t):
        f = (t.j + 0.5) / t.th                                       # 0 arriba, 1 en la punta de abajo
        u = abs((t.i + 0.5) / t.tw * 2 - 1)
        if u > 1.0 - max(0.0, f - 0.55) / 0.45:
            return TRANSPARENTE
        return hex_(col)
    return p


def construir():
    p = Personaje("kemira", altura=36, cabeza=8, torso=(7.4, 12, 4.0), brazo=(2.6, 2.6), pierna=(3.4, 3.4))
    C, T = p.cuello, p.tope                                # 28, 36
    cuerpo(p, C, p.lh)
    ropa(p, p.lh)
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), cabeza, dens=8, luz=False)
    pelo(p, C, T)
    penacho(p, T, C)
    diadema(p, T)
    return p
