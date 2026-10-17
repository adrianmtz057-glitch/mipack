"""
Kemira, diosa de Thza (avatar). Se arma paso a paso siguiendo la hoja referencias/personajes/kemira_hoja.png.

Hasta ahora: la cabeza (cubo liso del color de piel de la hoja, #A67556, con el pelo crema pintado y en capas), la
diadema alta en trapecio sobre la cabeza con flecos de cuentas, el penacho y la melena de figuras 3D, el cuerpo
(cintura marcada que se abre a una cadera ancha y honda donde se sienta la falda, muslos gruesos, brazos un poco
abiertos), el top negro con escote en V pintado sobre el busto y la falda tribal de plumas.
"""

import math

from ..kit import Personaje
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import color

D = 4
PX = 1.0 / D                                                      # un pixel del cuerpo

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
    costados y atras baja en mechones; adelante, mechones en las esquinas de la frente que llegan justo arriba de
    los ojos. El resto, la cara."""
    v = t.y - CUELLO
    if t.cara == "up":
        return mechones(t.x, t.z, -99)
    if t.cara == "down":
        return hex_(PIEL)
    if t.cara == "north":
        u, au = -t.x, abs(-t.x)
        if v > 7.4 or (au > 2.9 and v > _puntas(u, 5.4)) or (1.9 < au <= 2.9 and v > _puntas(u, 6.3)):
            return mechones(u, v, -99)
        return cara(u, v)
    u = t.z if t.cara in ("east", "west") else t.x
    base = 1.6 if t.cara in ("east", "west") else 1.0
    return mechones(u, v, _puntas(u, base)) if v > _puntas(u, base) else hex_(PIEL)


OJO_BLANCO, OJO_BLANCO_S = "#E8E2D8", "#C2B8AC"
IRIS, IRIS_S, IRIS_C, PUPILA, IRIS_TAPADO = "#5F87AD", "#456C93", "#7FA6C8", "#2A4460", "#34506E"
PESTANA, CEJA, NARIZ, BOCA = "#1C1515", "#86573E", "#93644A", "#6E4632"


def cara(u, v):
    """La cara de la hoja, pixel a pixel (8 por bloque; u de izquierda a derecha de quien la ve, v desde la barbilla):
    ojos grandes con el blanco hacia afuera y el iris azul hacia adentro con una pupila chica, mas claro abajo y
    tapado arriba por la pestana; pestanas negras gruesas que salen en ala hacia las orillas, una rayita de
    pestana abajo en la orilla, ceja fina apenas mas oscura, nariz de un punto y boca de una linea. Sin sombras."""
    i, j = math.floor(u * 8), math.floor(v * 8)
    a = i if i < 0 else -1 - i                               # el ojo derecho es el espejo del izquierdo
    if -28 <= a <= -11 and 20 <= j <= 29:                    # el ojo
        if a <= -22:
            return hex_(OJO_BLANCO_S if j == 29 or (a == -28 and j == 20) else OJO_BLANCO)
        if j == 29:
            return hex_(IRIS_TAPADO)
        if a in (-17, -16) and 23 <= j <= 25:
            return hex_(PUPILA)
        return hex_(IRIS_S if j >= 27 else IRIS_C if j == 20 else IRIS)
    pestana = ((30 <= j <= 33 and -30 <= a <= -11) or (j == 34 and -30 <= a <= -14) or
               (a == -31 and 32 <= j <= 35) or (a == -32 and 34 <= j <= 36) or (a == -10 and 29 <= j <= 31) or
               (j == 19 and -28 <= a <= -24) or (a == -29 and 19 <= j <= 20))
    if pestana:
        return hex_(PESTANA)
    if (j == 38 and -27 <= a <= -12) or (a == -11 and j == 37):
        return hex_(CEJA)
    if j == 18 and a == -1:
        return hex_(NARIZ)
    if j == 10 and -4 <= a <= -1:
        return hex_(BOCA)
    return hex_(PIEL)


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
                p.caja(g, f"cortina{s}", (a, C, -h - 0.4), (b, T, -h), capa_pelo(5.4), dens=8, luz=False)
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


PIEL_OSC2, PIEL_OSC, PIEL_MEDIO, PIEL_CLARA = "#7C4F3A", "#8E5E46", "#9B6B50", "#B5846A"
PINTURA = "#D9CBB4"                                                # las marcas claras de la hoja (muslos y brazos)
ESCALONES = {(0, 0), (1, 0), (2, 0), (2, -1), (3, -1), (4, -1), (4, -2), (5, -2)}     # marca del brazo, en pixeles


def piel(t):
    """La piel del cuerpo, pixel a pixel (la luz horneada pone encima el volumen, las sombras y los cantos con brillo):
    claviculas y el hueco del cuello, el canal del busto con brillo arriba de cada capa, ombligo y una linea suave al
    medio de la panza, columna, omoplatos y hoyuelos atras, un brillo largo al frente de muslos y espinillas, rodillas,
    codos y dedos; y las marcas claras de la hoja: en cada muslo una raya con un arco y una barrita abajo, atras una
    raya que sube en diagonal, y escalones en el hombro."""
    x, y, z, n, c = t.x, t.y, t.z, t.nombre, t.cara
    s = 1 if (t.f[0] + t.t[0]) > 0 else -1
    q = lambda v: math.floor(v * D)                               # pixel
    tono = PIEL
    if n == "torax":
        if c == "north":
            alto = 27.0 if abs(x) < 1.75 else 27.25                 # claviculas: suben hacia los hombros
            if 0.5 <= abs(x) < 3.0 and alto <= y < alto + PX:
                tono = PIEL_MEDIO
            elif abs(x) < PX and (y >= 27.5 or y < 26.4):           # hueco del cuello y canal del busto
                tono = PIEL_OSC
            elif abs(x) < 3.2 and BUSTO[0][2] <= y < BUSTO[0][2] + 2 * PX:
                tono = PIEL_CLARA                                    # brillo arriba del busto
        elif c == "south":
            if abs(x) < PX:
                tono = PIEL_OSC                                      # columna
            elif (1.0 <= abs(x) < 2.75 and 26.25 <= y < 26.5) or (1.0 <= abs(x) < 1.25 and 26.5 <= y < 27.5):
                tono = PIEL_MEDIO                                    # omoplatos
    elif n.startswith("busto") and c == "north":
        tono = PIEL_OSC if abs(x) < PX else PIEL_CLARA if t.j == 0 else PIEL
    elif n.startswith("cintura"):
        if c in ("east", "west"):
            tono = PIEL_MEDIO                                        # los costados, un tono abajo
        elif c in ("north", "south") and y >= 22.1:
            tono = PIEL_OSC if y >= 22.35 else PIEL_MEDIO            # la sombra bajo el top
        elif c == "north":
            if abs(x) < PX and 19.5 <= y < 20.0:
                tono = PIEL_OSC2 if y >= 19.75 else PIEL_OSC         # ombligo
            elif abs(x) < PX and 20.5 <= y < 22.0:
                tono = PIEL_MEDIO
        elif c == "south":
            if abs(x) < PX:
                tono = PIEL_OSC
            elif 0.75 <= abs(x) < 1.0 and 18.4 <= y < 18.65:
                tono = PIEL_OSC                                      # hoyuelos
    elif n == "gluteos" and c == "south":
        tono = PIEL_OSC if abs(x) < PX or t.fila_abajo == 0 else PIEL
    elif n in ("muslo", "muslo_alto", "rodilla", "pantorrilla"):
        lx = (x - s * 2.3) * s                                       # 0 al medio del muslo, + hacia afuera
        if c == "north":
            marca = ((11.5 <= y < 11.75 and 0.5 <= abs(lx) < 1.75) or (0.5 <= abs(lx) < 0.75 and 11.5 <= y < 12.5) or
                     (12.25 <= y < 12.5 and abs(lx) < 0.75) or (abs(lx) < 0.25 and 10.5 <= y < 11.25))
            if marca:
                tono = PINTURA
            elif n == "rodilla" and abs(lx) < 0.5:
                tono = PIEL_CLARA if 9.25 <= y < 9.75 else PIEL_OSC if 9.0 <= y < 9.25 else PIEL
            elif n != "rodilla" and -0.25 <= lx < (0.75 if n != "pantorrilla" else 0.25) and y > 1.5:
                tono = PIEL_CLARA                                    # brillo largo al frente
        elif c == ("east" if s > 0 else "west") and n == "muslo":
            if ((11.5 <= y < 11.75 and 0.5 <= abs(z) < 1.75) or (0.5 <= abs(z) < 0.75 and 11.5 <= y < 12.5) or
                    (12.25 <= y < 12.5 and abs(z) < 0.75) or (abs(z) < 0.25 and 10.5 <= y < 11.25)):
                tono = PINTURA                                       # la misma marca por el costado del muslo
        elif c == "south" and n == "muslo":
            dx = q(lx) - q(0.25)
            if (11.5 <= y < 11.75 and -1.25 <= lx < 0.25) or (0 <= dx <= 2 and q(y) == q(11.75) + dx):
                tono = PINTURA                                       # raya que sube en diagonal
    elif n == "gemelo" and c == "south" and t.j == 0:
        tono = PIEL_CLARA
    elif n == "pie" and c == "down":
        tono = PIEL_OSC2
    elif n in ("hombro", "brazo") and c == ("east" if s > 0 else "west"):
        if (q(z) - q(-0.75), q(y) - q(25.25)) in ESCALONES:
            tono = PINTURA                                           # escalones en el hombro, por afuera
    elif n == "brazo" and c == "south" and t.fila_abajo == 0:
        tono = PIEL_OSC                                              # codo
    elif n == "mano":
        if c == ("east" if s > 0 else "west") and y < 14.35 and q(z) in (-2, 0, 2):
            tono = PIEL_OSC                                          # dedos
        elif c == ("east" if s > 0 else "west") and 15.0 <= y < 15.25:
            tono = PIEL_CLARA                                        # nudillos
        elif c == "north" and abs(x - s * 4.15) < 0.5 and 14.5 <= y < 15.75:
            tono = PIEL_OSC if abs(x - s * 4.15) >= 0.25 else PIEL_CLARA     # pulgar
    return hex_(tono)


BUSTO = ((3.7, 22.8, 25.9, -2.1), (3.35, 23.1, 25.4, -2.7), (2.75, 23.5, 24.9, -3.3))   # (medio ancho, abajo, arriba, z de atras)
CADERA_X, CADERA_ZF, CADERA_ZB, GLUTEO_ZB = 4.7, -2.6, 2.7, 3.4     # la cadera donde se sienta la falda
CINTURA = ((21.4, 22.6, 3.3, -1.95, 1.95), (20.0, 21.4, 3.15, -1.9, 1.9), (19.4, 20.0, 3.35, -2.0, 2.0),
           (18.9, 19.4, 3.65, -2.15, 2.2), (18.4, 18.9, 3.95, -2.3, 2.35), (17.6, 18.4, 4.3, -2.45, 2.55))
BRAZO_ABRE = 8.5                                                   # grados: los brazos cuelgan por fuera de la falda


def cuerpo(p, C, L):
    """La base del cuerpo: hombros y torax anchos, busto en capas, cintura marcada que se abre en escalones a una
    cadera ancha y honda (llena la falda), gluteos, muslos gruesos que se afinan a la rodilla y pantorrillas con
    volumen. Los brazos cuelgan un poco abiertos para pasar por fuera de la falda. La piel lleva su textura (ver
    piel) y luz horneada; el top va pintado encima del torax y el busto (pegado, como el pelo en la cabeza)."""
    g = "Body/cuerpo"
    caja = lambda grupo, n, a, b, pintor=piel, **kw: p.caja(grupo, n, a, b, pintor, dens=D, **kw)
    caja(g, "torax", (-4.0, 22.6, -2.1), (4.0, C, 2.1), top)
    for k, (x, y0, y1, z) in enumerate(BUSTO):                     # busto en capas: redondo de perfil
        caja(g, f"busto{k}", (-x, y0, z - 0.6), (x, y1, z), top)
    for k, (y0, y1, x, zf, zb) in enumerate(CINTURA):              # la cintura se abre a la cadera en escalones finos
        caja(g, f"cintura{k}", (-x, y0, zf), (x, y1, zb), luz=False)       # sombreada a mano: sin rayas por escalon
    caja(g, "cadera", (-CADERA_X, L - 1.2, CADERA_ZF), (CADERA_X, 17.6, CADERA_ZB))
    caja(g, "gluteos", (-4.3, L - 1.8, CADERA_ZB - 0.1), (4.3, 17.6, GLUTEO_ZB))
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        gb = f"{hueso}/brazo"
        giro = dict(rot=(0, 0, s * BRAZO_ABRE), piv=(s * 4.0, C - 0.4, 0))
        x1, x2 = sorted((s * 3.6, s * 6.75))
        caja(gb, "hombro", (x1, C - 2.6, -1.45), (x2, C + 0.2, 1.45), **giro)
        x1, x2 = sorted((s * 4.0, s * 6.6))
        caja(gb, "brazo", (x1, 20.4, -1.3), (x2, C - 2.6, 1.3), **giro)
        f1, f2 = sorted((s * 4.15, s * 6.45))
        caja(gb, "antebrazo", (f1, L, -1.15), (f2, 20.4, 1.15), **giro)
        caja(gb, "mano", (f1, L - 2.4, -1.05), (f2, L, 1.05), **giro)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        gl = f"{hueso}/pierna"
        lado = lambda a, b: sorted((s * a, s * b))
        m1, m2 = lado(0.0, CADERA_X + 0.05)
        caja(gl, "muslo_alto", (m1, 12.8, CADERA_ZF), (m2, L + 0.2, CADERA_ZB))
        m1, m2 = lado(0.1, 4.45)
        caja(gl, "muslo", (m1, 10.2, -2.4), (m2, 12.8, 2.5))
        r1, r2 = lado(0.3, 4.0)
        caja(gl, "rodilla", (r1, 7.8, -2.0), (r2, 10.2, 2.1))
        c1, c2 = lado(0.4, 3.8)
        caja(gl, "pantorrilla", (c1, 1.2, -1.8), (c2, 7.8, 1.9))
        g1, g2 = lado(0.65, 3.55)
        caja(gl, "gemelo", (g1, 3.6, 1.9), (g2, 6.8, 2.5))
        caja(gl, "pie", (c1, 0.0, -2.8), (c2, 1.2, 1.9))


NEGRO_ROPA, BEIGE_ROPA, TOSTADO = "#262325", "#D8C9AE", "#A8977C"
TOP_ABAJO, TOP_LADO, TOP_ATRAS = 22.6, 25.9, 25.6                 # alturas del top: abajo, borde de arriba adelante y atras
V_ANCHO, V_HONDO = 1.75, 1.5                                       # la V del escote al centro del pecho


def _corte(x):
    """Altura del borde de arriba del top adelante: parejo a los lados y en V al medio del pecho."""
    return TOP_LADO - V_HONDO * max(0.0, 1.0 - abs(x) / V_ANCHO)


def top(t):
    """Pintor del torax y el busto con el top encima, como la hoja: adelante una banda negra que tapa el busto, con el
    borde de arriba en V (un pixel negro y debajo una linea beige que sigue la V); atras rodea la espalda derecho, con una banda beige abajo; en los costados la linea beige baja en diagonal
    de adelante-arriba a atras-abajo. Arriba del top, piel."""
    x, y, z = t.x, t.y, t.z
    if t.cara == "down":
        return hex_(NEGRO_ROPA)
    if t.cara == "up" and y >= 27.9:                               # los hombros
        return piel(t)
    # que tan atras esta el punto: 0 adelante (pecho), 1 en la espalda
    atras = 1.0 if t.cara == "south" else 0.0 if t.cara in ("north", "up") else min(1.0, max(0.0, (z + 2.1) / 4.2))
    borde = _corte(x) if atras == 0.0 else TOP_LADO + (TOP_ATRAS - TOP_LADO) * atras
    if y > borde:
        return piel(t)
    if t.cara == "up":                                             # los escalones del busto: piel o negro, sin linea
        return hex_(NEGRO_ROPA)
    linea = borde - PX if atras == 0.0 else TOP_ABAJO + 3 * PX + (borde - PX - TOP_ABAJO - 3 * PX) * (1 - atras)
    if atras == 1.0:                                               # la espalda: banda beige abajo con marcas
        if y < TOP_ABAJO + 3 * PX:
            i = int((x + 50) / PX)
            return hex_(TOSTADO if (i % 4 == 1 and TOP_ABAJO + PX <= y < TOP_ABAJO + 2 * PX) else BEIGE_ROPA)
        return hex_(NEGRO_ROPA)
    if y > borde - PX and atras == 0.0:                            # el canto de arriba, negro
        return hex_(NEGRO_ROPA)
    grueso = PX if atras > 0.0 or abs(x) >= V_ANCHO else PX * (1 + V_HONDO / V_ANCHO)   # en diagonal, linea seguida
    if linea - grueso <= y < linea:
        return hex_(BEIGE_ROPA)
    return hex_(NEGRO_ROPA)


def ropa(p, L):
    """El top va pintado sobre el cuerpo (ver top); aqui va su dobladillo (un canto apenas salido abajo) y la falda
    de plumas como taparrabo."""
    p.caja("Body/ropa", "top_dobladillo", (-4.05, TOP_ABAJO - 0.1, -2.15), (4.05, TOP_ABAJO + 0.3, 2.15),
           lambda t: hex_(NEGRO_ROPA), dens=D)
    falda(p, L)


OSCUROS = ("#1C1D26", "#272935")                               # negro azulado de la hoja, en dos tonos
BEIGES = ("#E0D0B4", "#D2C1A3")
CARBON = OSCUROS[0]

# silueta de una pluma: (desde que fraccion del largo, medio ancho / ancho), de arriba hacia la punta.
# Cada tramo es recto y entre tramos hay un escalon: bordes de pixel, con muescas a los costados.
NIVELES = ((0.00, 0.30), (0.06, 0.50), (0.28, 0.38), (0.34, 0.50), (0.52, 0.36), (0.60, 0.44), (0.74, 0.30),
           (0.85, 0.18), (0.94, 0.08))


def perfil_pluma(ancho, largo, k):
    """Contorno 2D (x, y) de una pluma colgando desde (0, 0) hasta la punta en (0, -largo), con escalones. Los
    dos lados tienen las muescas un poco corridas (k), asi ninguna pluma es igual a otra."""
    lados = []
    for s in (1, -1):
        corre = 0.05 * (_azar(k * 2 + (s > 0) + 2000) - 0.5)
        pts = []
        niveles = [(f if i in (0, 1) else min(0.97, f + corre), hw) for i, (f, hw) in enumerate(NIVELES)]
        for i, (f, hw) in enumerate(niveles):
            f2 = niveles[i + 1][0] if i + 1 < len(niveles) else 1.0
            pts += [(s * hw * ancho, -f * largo), (s * hw * ancho, -f2 * largo)]
        lados.append(pts)
    derecha, izquierda = lados
    return derecha + [(0.0, -largo)] + izquierda[::-1]


def pluma_3d(base, ancho, largo, k, angulo, abre, abanico=0.0, grosor=0.45):
    """Malla de una pluma: el contorno extruido (grosor), colgando desde 'base'. angulo: donde esta alrededor de la
    cadera (180 adelante, 0 atras, 90 a su derecha); abre: cuanto se separa la punta del cuerpo; abanico: giro en
    su propio plano (las de arriba en las caderas se abren en abanico)."""
    from .. import malla as geo
    m = geo.extruir(perfil_pluma(ancho, largo, k), -grosor / 2, grosor / 2)
    if abanico:
        m = geo.girar(m, (0, 0, abanico))
    m = geo.girar(m, (abre, angulo - 180, 0))
    return geo.mover(m, base)


ARO_X, ARO_ZF, ARO_ZB = CADERA_X + 0.15, -CADERA_ZF + 0.15, GLUTEO_ZB + 0.15    # el cinturon, justo sobre la cadera


def borde_cadera(t):
    """Punto del borde del cinturon y su angulo para t de 0 a 1 (vuelta entera: empieza adelante al medio)."""
    ang = 180 + 360 * t
    a = math.radians(ang)
    sx, sz = math.sin(a), math.cos(a)
    r = 1.0 / max(abs(sx) / ARO_X, abs(sz) / (ARO_ZB if sz > 0 else ARO_ZF))      # rectangulo de la cadera
    return (r * sx, r * sz), ang


def falda(p, L):
    """Falda tribal de plumas como la hoja y la guia: cinturon de cuero con triangulos y una base oscura; debajo,
    tres hileras de plumas con silueta escalonada (anchas, con muescas, en punta) que se enciman: atras las negras
    largas, que bajan en punta al centro de adelante y de atras; al medio, medianas negras y beige; arriba, cortas
    que en las caderas se abren en abanico. Las beige van por delante, sobre todo al frente. A los costados son mas
    cortas y dejan ver el muslo."""
    g = "Body/falda"
    color_ = lambda col: (lambda t: hex_(col))
    p.caja(g, "cinturon", (-ARO_X, L + 0.8, -ARO_ZF), (ARO_X, L + 1.8, ARO_ZB), tejido, dens=D, luz=False)
    p.caja(g, "base", (-ARO_X + 0.1, L - 1.4, -ARO_ZF + 0.1), (ARO_X - 0.1, L + 0.8, ARO_ZB - 0.1), color_(CARBON),
           dens=D, luz=False)
    y0 = L + 1.0
    hileras = (                                                    # (cuantas, fuera, largo centro, largo costado, abre, beige)
        (22, 0.05, 11.0, 4.4, 2, 0.0),
        (18, 0.40, 7.4, 3.8, 6, 0.45),
        (16, 0.75, 4.4, 3.0, 12, 0.5),
    )
    k = 0
    for h, (n, fuera, l_centro, l_lado, abre, beige) in enumerate(hileras):
        for i in range(n):
            t = (i + 0.5 * h + 0.3 * _azar(k + 2100)) / n
            (x, z), ang = borde_cadera(t)
            a = math.radians(ang)
            centro = abs(math.cos(a)) ** 1.6                      # 1 al centro de adelante/atras, 0 a los costados
            if h == 0 and centro < 0.08 and i % 2:                # aberturas a los costados
                continue
            largo = l_lado + (l_centro - l_lado) * centro + (2.6 if h == 0 else 1.2) * (_azar(k + 2200) - 0.5)
            adelante = math.cos(a) < 0
            es_beige = _azar(k + 2300) < beige * ((1.5 if centro > 0.3 else 0.9) if adelante else 0.45)
            col = BEIGES[k % 2] if es_beige else OSCUROS[k % 2]
            # las de la hilera de arriba en las caderas se abren en abanico hacia el costado
            abanico = -math.sin(a) * (12 + 10 * _azar(k + 2400)) * (1 - centro) if h == 2 else 0.0
            fuera_ = fuera * (0.3 + 0.7 * centro)                # a los costados las capas van mas pegadas
            base = (x + math.sin(a) * fuera_, y0 - 0.15 * h, z + math.cos(a) * fuera_)
            ancho = 2.0 + 0.6 * _azar(k + 2500) - 0.2 * h
            malla = pluma_3d(base, ancho, largo, k, ang, (abre + 4 * _azar(k + 2600)) * (0.35 + 0.65 * centro), abanico)
            p.malla(g, f"pluma{h}_{k}", malla, color_(col), dens=D)
            k += 1


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
