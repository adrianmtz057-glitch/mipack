"""
Pibble, el semidios errante. Hecho a mano con el kit (boceto 2: todo 3D).

No es un player con cosas encima: el cuerpo es un volumen redondo (abrigo abultado hecho con rebanadas
de esquinas escalonadas), piernas cortas con bombachos, mangas gordas, bufanda en dos vueltas que tapa
la boca, sombrero puntiagudo con niveles irregulares, pliegues de papel y ala en paneles inclinados.
Rostro de vacio negro con ojos que brillan, manto crema geometrico, forro azul con rombos, cadena y
colgantes dorados, cola en media luna y pergaminos atras. Bajito (~1.6 bloques sin el sombrero).
"""

import math

from ..kit import Personaje, dibujo, sprite, tonos
from ..pintura import metal
from ..textura import TRANSPARENTE, hex_a_rgba

NEGRO = tonos("#1E181A")
MARRON = tonos("#3E2C22")
CREMA = tonos("#E6DAC2")
ORO = tonos("#C29A48")
AZUL = tonos("#3E5C72")
VACIO = "#0E0A0C"

# ---------------------------------------------------------------- dibujos

CARA = dibujo("""
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKggKKKKKKK
    KKKKKKgGGgKKKKKK
    KKKKKKKggKKKKKKK
    KKKKKKKKKKKKKKKK
    KoooooKKKKoooooK
    oWWWWWoKKoWWWWWo
    KoWWWoKKKKoWWWoK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
""")
PAL_CARA = {"K": VACIO, "g": ORO["s"], "G": ORO["h"], "W": "#FFF2D0", "o": "#B08840"}

ARO = dibujo("""
    ..GGGG..
    .Gg..gG.
    Gg.bb.gG
    G.bBBb.G
    G.bBBb.G
    Gg.bb.gG
    .Gg..gG.
    ..GGGG..
""")
PAL_ARO = {"G": ORO["l"], "g": ORO["s"], "b": AZUL["s"], "B": AZUL["l"]}

OREJA = dibujo("""
    ...KK...
    ...KK...
    ..KKKK..
    ..KkkK..
    .KKkkKK.
    .KkkkkK.
    KKkkkkKK
    KkkkkkkK
""")
PAL_OREJA = {"K": NEGRO["b"], "k": MARRON["b"]}

PUNTA_COLA = dibujo("""
    ...G...
    ..GDG..
    ..DBD..
    .GDBDG.
    .DBoBD.
    GDBooBG
    DBBoBBD
    DBBBBBD
""")
PAL_COLA = {"G": ORO["b"], "D": NEGRO["b"], "B": AZUL["b"], "o": ORO["h"]}

SOLAPA = dibujo("""
    CCCCCCCC
    CccccccC
    CccMMccC
    CccccccC
    .CcccccC
    .CccMcC.
    ..CcccC.
    ..CcccC.
    ...CcC..
    ....C...
""")
PAL_SOLAPA = {"C": MARRON["b"], "c": CREMA["b"], "M": AZUL["b"]}

PLIEGUE = dibujo("""
    ......C
    .....CC
    ....CCc
    ...CCcc
    ..CCccc
    .CCcccc
    CCccccM
""")
PAL_PLIEGUE = {"C": CREMA["l"], "c": CREMA["b"], "M": MARRON["b"]}


# ---------------------------------------------------------------- pintores a mano

def hex_(c):
    return hex_a_rgba(c)


def _uv(t):
    """Coordenadas de mundo en texeles (dens 2) para que los dibujos sigan de una pieza a otra."""
    u = math.floor((t.x if t.cara in ("north", "south", "up", "down") else t.z) * 2 + 0.01)
    v = math.floor(t.y * 2 + 0.01)
    return u, v


def textil(semilla=0, forro_abajo=0):
    """Tela oscura del abrigo con bandas en zigzag doradas, filas de rombos y forro azul abajo."""
    def p(t):
        if t.cara == "up":
            return hex_(NEGRO["b"])
        if t.cara == "down":
            return hex_(NEGRO["s"])
        u, v = _uv(t)
        if forro_abajo and t.fila_abajo < forro_abajo:
            if t.fila_abajo == 0:
                return hex_(ORO["s"])
            if (u + v) % 4 == 0 and (u - v) % 4 == 0:
                return hex_(ORO["b"])
            return hex_(AZUL["b"] if (u + v) % 2 else AZUL["s"])
        fase = (v + semilla) % 14
        if fase == 0:
            return hex_(ORO["s"])                                   # linea de la banda
        if fase in (1, 2) and (u + (0 if fase == 1 else 2)) % 4 == 0:
            return hex_(ORO["b"])                                   # zigzag
        if fase == 7 and u % 6 == 0:
            return hex_(ORO["b"])                                   # fila de rombos
        if fase in (6, 8) and u % 6 in (5, 1):
            return hex_(ORO["s"])
        if fase == 7 and u % 6 in (5, 1):
            return hex_(AZUL["b"])
        # sombreado por altura de mundo (no por pieza): sin "anillos" entre rebanadas
        if t.cara in ("east", "west"):
            return hex_(NEGRO["b"] if (u + semilla) % 5 else NEGRO["s"])
        c = MARRON["s"] if v > 30 else NEGRO["b"]
        if (u + semilla) % 5 == 0:
            c = NEGRO["b"] if c != NEGRO["b"] else NEGRO["s"]
        return hex_(c)
    return p


def crema(cortes=None, semilla=0, borde=MARRON["b"]):
    """Manto crema con triangulos marrones, puntos dorados y borde en picos."""
    def p(t):
        if t.cara in ("up", "down"):
            return hex_(CREMA["l"] if t.cara == "up" else CREMA["s"])
        corte = 0
        if cortes:
            corte = cortes[(t.i + semilla) % len(cortes)]
            if t.fila_abajo < corte:
                return TRANSPARENTE
        if t.fila_abajo == corte:
            return hex_(borde)
        u, v = _uv(t)
        fu, fv = (u + semilla) % 8, (v + semilla) % 10
        if fv in (2, 3) and abs(fu - 3.5) <= (fv - 1.5):
            return hex_(MARRON["b"])                                # triangulos
        if fv == 7 and fu in (3, 4):
            return hex_(ORO["b"])
        if t.fila_abajo == corte + 2 and t.i % 3 == 1:
            return hex_(ORO["s"])
        k = t.j / max(1, t.th - 1)
        return hex_(CREMA["l"] if k < 0.12 else (CREMA["b"] if k < 0.8 else CREMA["s"]))
    return p


def bufanda(semilla=0, cortes=None):
    """Tela gruesa marron oscuro con pliegues horizontales (se distingue del vacio negro de la cara)."""
    def p(t):
        if t.cara in ("up", "down"):
            return hex_(MARRON["b"] if t.cara == "up" else NEGRO["s"])
        if cortes and t.fila_abajo < cortes[(t.i + semilla) % len(cortes)]:
            return TRANSPARENTE
        fila = (t.j + semilla) % 4
        if fila == 0:
            return hex_(MARRON["l"])
        if fila == 3:
            return hex_(NEGRO["b"])
        return hex_(MARRON["b"])
    return p


def marron(semilla=0, bandas=False):
    def p(t):
        if t.cara in ("up", "down"):
            return hex_(MARRON["s"])
        k = t.j / max(1, t.th - 1)
        if bandas and t.fila_abajo < 4:
            return hex_(AZUL["b"] if (t.i + t.fila_abajo) % 3 else CREMA["s"])   # vendas en el tobillo
        if (t.i + semilla) % 4 == 0:
            return hex_(MARRON["s"])
        return hex_(MARRON["l"] if k < 0.15 else (MARRON["b"] if k < 0.75 else MARRON["s"]))
    return p


def sombrero(t):
    """Frente crema, costados negros, franja negra atras; bordes marrones."""
    if t.cara == "down":
        return hex_(NEGRO["s"])
    if t.cara == "up":
        return hex_(CREMA["l"])
    if t.cara in ("east", "west"):
        return hex_(NEGRO["l"] if t.j == 0 else NEGRO["b"])
    if t.cara == "south" and abs(t.i - (t.tw - 1) / 2) < 0.6 + t.tw * 0.1:
        return hex_(NEGRO["b"])
    if t.i == 0 or t.i == t.tw - 1:
        return hex_(MARRON["b"])
    return hex_(CREMA["l"] if t.j == 0 else CREMA["b"])


def oreja_pintor(oscura=False):
    """Oreja de gato: crema por fuera, triangulo oscuro por dentro (cara de adelante)."""
    def p(t):
        if t.cara == "down":
            return hex_(NEGRO["s"])
        if t.cara == "up":
            return hex_(MARRON["b"] if oscura else CREMA["l"])
        if t.cara == "north":
            # interior oscuro con borde crema de 1 texel: los niveles apilados forman un solo triangulo
            if 0 < t.i < t.tw - 1:
                return hex_(NEGRO["b"] if oscura else (MARRON["s"] if t.j else MARRON["b"]))
            return hex_(MARRON["b"] if oscura else CREMA["l"])
        if oscura:
            return hex_(NEGRO["b"] if t.i % 3 else MARRON["s"])
        if t.cara in ("east", "west"):
            return hex_(CREMA["s"] if t.i % 4 else MARRON["b"])
        return hex_(CREMA["l"] if t.j == 0 else CREMA["b"])
    return p


def negro_liso(t):
    return hex_(NEGRO["s"] if t.fila_abajo == 0 and t.cara not in ("up", "down") else NEGRO["b"])


def picos(semilla, prof=5, ancho=(2, 4), largo=96):
    out, k = [], 0
    while len(out) < largo:
        a = ancho[0] + (k * 7 + semilla) % (ancho[1] - ancho[0] + 1)
        h = 1 + (k * 5 + semilla * 3) % prof
        m = (a - 1) / 2
        out += [round(abs(c - m) / max(0.5, m) * h) for c in range(a)]
        k += 1
    return out


# ---------------------------------------------------------------- piezas reutilizables

def losa(p, grupo, nombre, cx, cz, y1, y2, w, d, r, pintor, rot=None, piv=None, dens=2):
    """Rebanada de esquinas escalonadas (cruz de dos cajas): el ladrillo basico de las formas redondas."""
    p.caja(grupo, nombre + "_a", (cx - w / 2, y1, cz - d / 2 + r), (cx + w / 2, y2, cz + d / 2 - r), pintor, rot, piv,
           dens=dens)
    p.caja(grupo, nombre + "_b", (cx - w / 2 + r, y1, cz - d / 2), (cx + w / 2 - r, y2, cz + d / 2), pintor, rot, piv,
           dens=dens)


def rombo(p, grupo, nombre, x, y, z, tam, color, cadena=0.0):
    """Colgante en forma de rombo (cubo girado 45 grados) con su cadenita."""
    oro = metal(color, 7)
    p.caja(grupo, nombre, (x - tam / 2, y - tam / 2, z - 0.25), (x + tam / 2, y + tam / 2, z + 0.25), oro,
           rot=(0, 0, 45), piv=(x, y, z))
    if cadena:
        p.caja(grupo, nombre + "_cadena", (x - 0.12, y + tam * 0.6, z - 0.12),
               (x + 0.12, y + tam * 0.6 + cadena, z + 0.12), oro)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("pibble", altura=26, torso=(8, 9, 4), brazo=(3.5, 4))
    C, L, T = p.cuello, p.lh, p.tope                     # cuello 18, cintura 9, arriba de la cabeza 26
    oro = metal(ORO["b"], 3)

    # esqueleto base (casi todo queda tapado por las piezas 3D)
    cabeza = sprite({"north": CARA}, PAL_CARA, base=lambda t: hex_(VACIO))
    p.cuerpo(cabeza=cabeza, torso=textil(1), brazo=textil(2), pierna=marron(1, bandas=True), mano=negro_liso, dens=2)

    # ================================================================ CABEZA
    # capucha redonda: la cara queda hundida adentro, enmarcada
    losa(p, "Head/capucha", "capucha_arriba", 0, 0.3, T - 0.2, T + 1.0, 10.2, 10.2, 1.6, crema(semilla=1))
    p.caja("Head/capucha", "capucha_atras", (-5.1, C + 0.5, 4.3), (5.1, T, 5.1), crema(picos(4, prof=4), 3), dens=2)
    p.par("Head/capucha", "capucha_lado", (4.3, C + 0.2, -3.8), (5.1, T, 5.1), crema(picos(3, prof=3), 2),
          rot=(0, 0, 6), piv=(4.7, T, 0), dens=2)
    # visera en angulo sobre la frente
    p.caja("Head/capucha", "visera", (-5.4, T - 0.5, -6.3), (5.4, T + 0.3, -3.9), crema(picos(41, prof=2), 5),
           rot=(-22, 0, 0), piv=(0, T, -4.1), dens=2)
    # solapas que caen a los costados de la cara, con colgantes
    p.plano_par("Head/capucha", "solapa", (4.6, C - 2.5, -4.6), (4.6, T - 0.5, -1.0),
                sprite({"todas": SOLAPA}, PAL_SOLAPA), rot=(0, 0, 8), piv=(4.6, T - 0.5, -2.8), dens=2)
    for s in (1, -1):
        rombo(p, "Head/capucha", f"colgante_solapa{s}", s * 5.0, C - 4.2, -2.8, 1.2, ORO["b"], cadena=1.4)

    # orejas de gato: la derecha corta, la izquierda alta y doblada hacia afuera (con colgante en la punta)
    def oreja(nombre, s, pasos, oscura_desde):
        x, y, z = s * 2.9, T + 0.8, 0.6
        az = ax = 0.0
        for k, (dz, dx, w, h) in enumerate(pasos):
            az += dz * s
            ax += dx
            p.caja("Head/orejas", f"{nombre}{k}", (x - w / 2, y, z - w / 2), (x + w / 2, y + h, z + w / 2),
                   oreja_pintor(k >= oscura_desde), rot=(ax, 0, -az), piv=(x, y, z), dens=2)
            rz, rx = math.radians(-az), math.radians(ax)
            x += -math.sin(rz) * h * 0.9
            y += math.cos(rz) * math.cos(rx) * h * 0.9
            z += math.sin(rx) * h * 0.9
        return x, y, z
    oreja("oreja_d", 1, [(8, -4, 4.0, 1.8), (6, -2, 3.0, 1.8), (6, 0, 2.0, 1.6), (4, 0, 1.0, 1.4)], 9)
    xt, yt, zt = oreja("oreja_i", -1, [(8, -4, 4.2, 2.0), (6, -3, 3.2, 2.0), (10, -2, 2.3, 2.0), (18, 0, 1.6, 2.0),
                                       (26, 2, 1.0, 2.0)], 2)
    rombo(p, "Head/orejas", "colgante_punta", xt - 0.6, yt - 2.0, zt, 1.2, ORO["b"], cadena=1.4)
    # aro dorado con rombo azul colgando del lado de la oreja alta
    p.plano("Head/capucha", "aro", (-8.0, T - 2.6, -1.6), (-4.0, T + 1.4, -1.6), sprite({"todas": ARO}, PAL_ARO),
            rot=(0, 20, 0), piv=(-6.0, T, -1.6), dens=2)
    for k, (xx, largo) in enumerate(((-6.0, 2.6), (-7.2, 1.4))):
        rombo(p, "Head/capucha", f"colgante_aro{k}", xx, T - 3.2 - largo, -1.9, 1.1 + 0.3 * (k == 0), ORO["b"],
              cadena=largo)

    # bufanda gruesa en dos vueltas: tapa la boca y queda por delante de la cara
    losa(p, "Body/bufanda", "bufanda_baja", 0, 0, C - 0.6, C + 1.4, 9.6, 6.8, 1.4, bufanda(0))
    losa(p, "Head/bufanda", "bufanda_alta", 0, -0.4, C + 1.0, C + 2.6, 9.2, 9.8, 1.6, bufanda(1),
         rot=(0, 0, -3), piv=(0, C + 1.8, 0))
    p.caja("Body/bufanda", "nudo", (4.0, C - 2.4, -4.6), (6.0, C + 0.4, -2.6), bufanda(2), rot=(0, 0, 15),
           piv=(5.0, C - 1, -3.6))

    # ================================================================ CUERPO (forma de A)
    # abrigo oscuro debajo, mas angosto: el ancho lo da el manto
    perfil = [(C - 1.0, C + 0.3, 8.4, 5.2, 1.2), (C - 3.0, C - 1.0, 9.4, 6.2, 1.4), (C - 5.0, C - 3.0, 10.0, 6.8, 1.6),
              (L - 0.5, C - 5.0, 10.4, 7.2, 1.8)]
    for k, (y1, y2, w, d, r) in enumerate(perfil):
        losa(p, "Body/abrigo", f"abrigo{k}", 0, 0, y1, y2, w, d, r, textil(k))
    # faldon: atras y costados hasta los tobillos; adelante solo arriba (se ven los bombachos)
    faldon = [(L - 2.5, L - 0.5, 10.2, 7.2, 1.8), (L - 4.5, L - 2.5, 9.8, 7.0, 1.6), (L - 6.3, L - 4.5, 9.4, 6.8, 1.4)]
    for k, (y1, y2, w, d, r) in enumerate(faldon):
        pint = textil(k + 5, forro_abajo=5 if k == len(faldon) - 1 else 0)
        p.caja("Body/faldon", f"faldon_atras{k}", (-w / 2 + r, y1, d / 2 - 1.2), (w / 2 - r, y2, d / 2), pint, dens=2)
        for s in (1, -1):
            x1, x2 = sorted((s * (w / 2 - 1.2), s * w / 2))
            p.caja("Body/faldon", f"faldon_lado{k}_{s}", (x1, y1, -d / 2 + r), (x2, y2, d / 2 - r), pint, dens=2)
            if k == 0:
                x1, x2 = sorted((s * 2.0, s * (w / 2 - r)))
                p.caja("Body/faldon", f"faldon_frente_{s}", (x1, y1, -d / 2), (x2, y2, -d / 2 + 1.2),
                       textil(5, forro_abajo=4), dens=2)

    # cinturon de cuero con cadena dorada y colgantes
    losa(p, "Body/cinturon", "cinturon", 0, 0, L - 0.6, L + 0.9, 11.0, 7.8, 2.2, marron(2))
    p.caja("Body/cinturon", "hebilla", (-1.1, L - 0.8, -4.15), (1.1, L + 1.1, -3.85), metal(ORO["b"], 4, gema=AZUL["l"]))
    for k in range(7):
        xx = -3.6 + k * 1.2
        yy = L - 1.1 - (xx * xx) * 0.05
        p.caja("Body/cinturon", f"eslabon{k}", (xx - 0.4, yy - 0.4, -4.2), (xx + 0.4, yy + 0.4, -3.9), oro,
               rot=(0, 0, 45), piv=(xx, yy, -4.05))
    for k, (xx, largo) in enumerate(((-3.0, 1.6), (-1.0, 2.6), (1.6, 2.0), (3.2, 1.2))):
        rombo(p, "Body/cinturon", f"colgante{k}", xx, L - 1.8 - largo, -4.2, 1.2, ORO["b"], cadena=largo)

    # manto crema en campana: cuello redondo + paneles que se abren hacia afuera y terminan en picos
    losa(p, "Body/manto", "manto_cuello", 0, 0, C - 1.2, C + 0.9, 11.2, 8.0, 2.0, crema(picos(20, prof=2), 3))
    for s in (1, -1):
        x1, x2 = sorted((s * 1.0, s * 6.0))
        p.caja("Body/manto", f"manto_frente{s}", (x1, L - 2.0, -4.5), (x2, C - 0.8, -4.0),
               crema(picos(22 + s, prof=7, ancho=(3, 6)), 4 + s), rot=(14, 0, 10 * s), piv=(s * 3.5, C - 0.8, -4.2),
               dens=2)
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.4, s * 9.6))
        p.caja(f"{hueso}/manto", "manto_brazo", (x1, C - 5.8, -3.6), (x2, C + 0.9, 3.6),
               crema(picos(25 + s, prof=5), 6), rot=(0, 0, 12 * s), piv=(s * 3.8, C + 0.9, 0), dens=2)
    p.caja("Body/manto", "manto_espalda", (-5.8, L - 1.0, 4.0), (5.8, C - 0.8, 4.5), crema(picos(27, prof=7), 7),
           rot=(-14, 0, 0), piv=(0, C - 0.8, 4.2), dens=2)
    for s in (1, -1):                                   # dos tiras crema al frente, separadas
        x1, x2 = sorted((s * 0.5, s * 2.1))
        p.caja("Body/manto", f"tira_{s}", (x1, L - 5.5, -5.5), (x2, C - 1.2, -5.1),
               crema([0, 1, 2, 3, 2, 1] if s > 0 else [3, 2, 1, 0, 1, 2], 6 + s), rot=(8, 0, 0),
               piv=((x1 + x2) / 2, C - 1.2, -5.3), dens=2)
    rombo(p, "Body/collar", "colgante_pecho", 0, C - 3.8, -5.75, 1.4, ORO["b"], cadena=1.4)

    # mangas gordas con puño azul y manos chicas
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        cx = s * 6.6
        losa(p, f"{hueso}/manga", "manga", cx, 0, C - 6.6, C + 0.2, 4.6, 5.0, 1.0, textil(11))
        losa(p, f"{hueso}/manga", "puno", cx, 0, C - 7.6, C - 6.4, 5.2, 5.6, 1.2, textil(12, forro_abajo=40))
        losa(p, f"{hueso}/manga", "mano", cx, -0.2, C - 9.4, C - 7.6, 3.2, 3.4, 0.8, negro_liso)

    # bombachos grandes y botas redondas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        cx = s * 2.4
        losa(p, f"{hueso}/pantalon", "bombacho", cx, 0, 2.4, L - 1.5, 5.6, 5.8, 1.4, marron(2 + s))
        losa(p, f"{hueso}/pantalon", "vendas", cx, 0, 1.2, 2.6, 4.4, 4.6, 0.8, marron(3, bandas=True))
        losa(p, f"{hueso}/bota", "bota", cx, -0.4, 0, 1.4, 4.8, 5.8, 1.0, negro_liso)
        p.caja(f"{hueso}/bota", "puntera", (cx - 1.8, 0, -3.6), (cx + 1.8, 1.1, -2.9), metal(ORO["b"], 5))

    # ================================================================ COLA Y MOCHILA
    x, y, z = 1.6, L - 1.0, 5.0
    angulos = (-135, -115, -95, -75, -55, -37, -22)
    anchos = (2.2, 3.0, 3.6, 3.8, 3.4, 2.8, 2.0)

    def hoja(t):
        if t.cara not in ("north", "south"):
            return hex_(ORO["s"])
        if t.i == 0 or t.i == t.tw - 1:
            return hex_(ORO["b"])
        if t.i <= 2:
            return hex_(NEGRO["b"])
        if (t.i + t.j) % 9 == 0:
            return hex_(ORO["s"])
        return hex_(AZUL["l"] if t.j < 2 else AZUL["b"])
    for k, (ang, w) in enumerate(zip(angulos, anchos)):
        largo = 2.4
        p.caja("Body/cola", f"cola{k}", (x - w / 2, y, z - 0.45), (x + w / 2, y + largo + 0.3, z + 0.45), hoja,
               rot=(0, -25, ang), piv=(x, y, z), dens=2)
        r = math.radians(ang)
        x += -math.sin(r) * largo * 0.95
        y += math.cos(r) * largo * 0.95
    p.plano("Body/cola", "cola_punta", (x - 2.0, y - 0.3, z), (x + 2.0, y + 4.6, z),
            sprite({"todas": PUNTA_COLA}, PAL_COLA), rot=(0, -25, -12), piv=(x, y, z), dens=2)

    for k, (yy, zz) in enumerate(((L + 3.6, 5.6), (L + 1.6, 5.4))):
        rollo = crema(semilla=7 + k, borde=CREMA["s"])
        for giro in (0, 45):
            p.caja("Body/mochila", f"rollo{k}_{giro}", (-3.8, yy - 0.85, zz - 0.85), (3.8, yy + 0.85, zz + 0.85), rollo,
                   rot=(giro, 0, 0), piv=(0, yy, zz))
        for s in (1, -1):
            p.caja("Body/mochila", f"tapa{k}_{s}", (s * 3.8 - 0.5, yy - 1.0, zz - 1.0), (s * 3.8 + 0.5, yy + 1.0, zz + 1.0),
                   metal(ORO["s"], 8))
    return p
