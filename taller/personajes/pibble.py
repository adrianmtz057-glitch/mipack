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
from ..textura import TRANSPARENTE, azar, hex_a_rgba

NEGRO = tonos("#1E181A")
MARRON = tonos("#3E2C22")
CREMA = tonos("#E6DAC2")
ORO = tonos("#C29A48")
AZUL = tonos("#3E5C72")
VACIO = "#0E0A0C"

# ---------------------------------------------------------------- dibujos

CARA = dibujo("""
    KKKKKKKKKKKKKKKK
    KKKKKKKgKKKKKKKK
    KKKKKKgGgKKKKKKK
    KKKKKgKoKgKKKKKK
    KKKKKKgGgKKKKKKK
    KKKKKKKgKKKKKKKK
    KoooKKKKKKKKoooK
    oEEEEoKKKKoEEEEo
    KoEFEEoKKoEEFEoK
    KKooooKKKKooooKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
""")
PAL_CARA = {"K": VACIO, "g": ORO["s"], "G": ORO["h"], "E": "#F6C850", "F": "#FFF4C8", "o": "#9A6A20"}

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

    # esqueleto base (casi todo queda tapado por las piezas redondas)
    cabeza = sprite({"north": CARA}, PAL_CARA, base=lambda t: hex_(VACIO))
    p.cuerpo(cabeza=cabeza, torso=textil(1), brazo=textil(2), pierna=marron(1, bandas=True), mano=negro_liso, dens=2)

    # ---- cuerpo redondo: el abrigo abulta en la panza y se cierra arriba y abajo
    perfil = [  # (y1, y2, ancho, fondo, escalon)
        (C - 1.0, C + 0.3, 8.4, 5.2, 1.2),
        (C - 2.5, C - 1.0, 10.0, 6.6, 1.6),
        (C - 4.0, C - 2.5, 11.2, 7.6, 2.0),
        (C - 6.0, C - 4.0, 12.2, 8.4, 2.4),
        (L - 0.5, C - 6.0, 12.6, 8.8, 2.6),
    ]
    for k, (y1, y2, w, d, r) in enumerate(perfil):
        losa(p, "Body/abrigo", f"abrigo{k}", 0, 0, y1, y2, w, d, r, textil(k))
    # faldon: se abre adelante (se ven los bombachos), atras y a los costados baja hasta los tobillos
    faldon = [(L - 2.5, L - 0.5, 12.2, 8.6, 2.4), (L - 4.5, L - 2.5, 11.6, 8.2, 2.2), (L - 6.3, L - 4.5, 11.0, 7.8, 2.0)]
    for k, (y1, y2, w, d, r) in enumerate(faldon):
        ultimo = k == len(faldon) - 1
        pint = textil(k + 5, forro_abajo=5 if ultimo else 0)
        p.caja("Body/faldon", f"faldon_atras{k}", (-w / 2 + r, y1, d / 2 - 1.2), (w / 2 - r, y2, d / 2), pint, dens=2)
        for s in (1, -1):
            x1, x2 = sorted((s * (w / 2 - 1.2), s * w / 2))
            p.caja("Body/faldon", f"faldon_lado{k}_{s}", (x1, y1, -d / 2 + r), (x2, y2, d / 2 - r), pint, dens=2)
            x1, x2 = sorted((s * 2.4, s * (w / 2 - r)))
            p.caja("Body/faldon", f"faldon_frente{k}_{s}", (x1, y1, -d / 2), (x2, y2, -d / 2 + 1.2), pint, dens=2)
            x1, x2 = sorted((s * (w / 2 - r), s * (w / 2 - 1.2)))
            p.caja("Body/faldon", f"faldon_esquina{k}_{s}", (x1, y1, -d / 2 + 0.2), (x2, y2, d / 2 - 0.2), pint,
                   dens=2)
    for s in (1, -1):                                                   # forro azul en la abertura
        x1, x2 = sorted((s * 2.2, s * 3.0))
        p.caja("Body/faldon", f"forro_{s}", (x1, L - 6.0, -4.45), (x2, L - 0.5, -4.15), textil(9, forro_abajo=40),
               dens=2)

    # ---- cinturon redondo de cuero con cadena dorada y colgantes
    losa(p, "Body/cinturon", "cinturon", 0, 0, L - 0.6, L + 0.9, 13.0, 9.2, 2.6, marron(2))
    p.caja("Body/cinturon", "hebilla", (-1.1, L - 0.8, -4.85), (1.1, L + 1.1, -4.55), metal(ORO["b"], 4, gema=AZUL["l"]))
    for k in range(9):
        xx = -4.8 + k * 1.2
        yy = L - 1.2 - (xx * xx) * 0.04
        zz = -4.6 + (abs(xx) > 3.5) * 0.7
        p.caja("Body/cinturon", f"eslabon{k}", (xx - 0.4, yy - 0.4, zz - 0.15), (xx + 0.4, yy + 0.4, zz + 0.15), oro,
               rot=(0, 0, 45), piv=(xx, yy, zz))
    for k, (xx, largo) in enumerate(((-4.0, 1.4), (-2.2, 2.6), (2.6, 2.0), (4.2, 1.2))):
        rombo(p, "Body/cinturon", f"colgante{k}", xx, L - 1.8 - largo, -4.75 + (abs(xx) > 3.5) * 0.7, 1.2, ORO["b"],
              cadena=largo)

    # ---- manto crema sobre los hombros (redondo) y tiras largas al frente
    losa(p, "Body/manto", "manto_cuello", 0, 0, C - 2.6, C + 0.9, 12.6, 8.6, 2.0, crema(picos(20, prof=4), 3))
    p.caja("Body/manto", "manto_espalda", (-5.6, L + 1.0, 3.9), (5.6, C - 2.0, 4.5),
           crema(picos(21, prof=6), 4), rot=(-6, 0, 0), piv=(0, C - 2, 4.2), dens=2)
    for s in (1, -1):                                   # dos tiras crema que caen adelante, separadas del abrigo
        x1, x2 = sorted((s * 0.9, s * 3.0))
        p.caja("Body/manto", f"tira_{s}", (x1, L - 5.5, -5.6), (x2, C - 1.5, -5.1),
               crema([0, 1, 2, 3, 2, 1] if s > 0 else [3, 2, 1, 0, 1, 2], 6 + s), rot=(6, 0, -2 * s),
               piv=((x1 + x2) / 2, C - 1.5, -5.3), dens=2)

    # ---- bufanda gruesa en dos vueltas que tapa la boca, con nudo y punta
    losa(p, "Body/bufanda", "bufanda_baja", 0, 0, C - 0.6, C + 1.4, 9.6, 6.6, 1.4, bufanda(0))
    losa(p, "Head/bufanda", "bufanda_alta", 0, -0.2, C + 1.0, C + 2.5, 9.0, 9.4, 1.4, bufanda(1),
         rot=(0, 0, -3), piv=(0, C + 1.8, 0))
    p.caja("Body/bufanda", "nudo", (4.0, C - 2.4, -4.6), (6.0, C + 0.4, -2.6), bufanda(2), rot=(0, 0, 15),
           piv=(5.0, C - 1, -3.6))
    p.caja("Body/bufanda", "punta", (4.4, L + 0.5, -4.2), (6.0, C - 2.2, -3.4), bufanda(3, picos(30, prof=2)),
           rot=(0, 0, 10), piv=(5.2, C - 2.2, -3.8), dens=2)

    # ---- mangas gordas con puño azul y manos redondas
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        cx = s * 6.8
        losa(p, f"{hueso}/manga", "manga", cx, 0, C - 6.2, C + 0.4, 4.8, 5.2, 1.0, textil(11))
        losa(p, f"{hueso}/manga", "puno", cx, 0, C - 7.4, C - 6.0, 5.4, 5.8, 1.2, textil(12, forro_abajo=40))
        losa(p, f"{hueso}/manga", "mano", cx, -0.2, C - 9.4, C - 7.4, 3.4, 3.6, 0.8, negro_liso)

    # ---- bombachos y botas redondas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        cx = s * 2.4
        losa(p, f"{hueso}/pantalon", "bombacho", cx, 0, 2.6, L - 2.0, 5.2, 5.4, 1.2, marron(2 + s))
        losa(p, f"{hueso}/pantalon", "vendas", cx, 0, 1.2, 2.8, 4.4, 4.6, 0.8, marron(3, bandas=True))
        losa(p, f"{hueso}/bota", "bota", cx, -0.4, 0, 1.4, 4.8, 5.8, 1.0, negro_liso)
        p.caja(f"{hueso}/bota", "puntera", (cx - 1.8, 0, -3.6), (cx + 1.8, 1.1, -2.9), metal(ORO["b"], 5))

    # ---- capucha crema bajo el sombrero
    p.caja("Head/capucha", "capucha_arriba", (-5.0, T - 0.3, -4.8), (5.0, T + 0.6, 5.0), crema(semilla=1), dens=2)
    p.par("Head/capucha", "capucha_lado", (4.3, C + 1.5, -4.5), (5.0, T - 0.3, 5.0),
          crema(picos(3, prof=3), 2), rot=(0, 0, 8), piv=(4.6, T, 0), dens=2)
    p.caja("Head/capucha", "capucha_atras", (-5.0, C + 0.5, 4.3), (5.0, T - 0.3, 5.0), crema(picos(4, prof=4), 3),
           dens=2)

    # ---- ala del sombrero: 4 paneles inclinados hacia abajo (no un plato plano)
    ala = crema(picos(40, prof=2, ancho=(3, 5)), 9)
    p.caja("Head/sombrero", "ala_frente", (-5.6, T + 0.1, -6.4), (5.6, T + 0.6, -4.2), ala, rot=(-18, 0, 0),
           piv=(0, T + 0.4, -4.4), dens=2)
    p.caja("Head/sombrero", "ala_atras", (-5.8, T + 0.1, 4.2), (5.8, T + 0.6, 6.8), ala, rot=(16, 0, 0),
           piv=(0, T + 0.4, 4.4), dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 4.4, s * 7.0))
        p.caja("Head/sombrero", f"ala_lado{s}", (x1, T + 0.1, -5.0), (x2, T + 0.6, 5.4), ala, rot=(0, 0, s * -20),
               piv=(s * 4.6, T + 0.4, 0), dens=2)

    # ---- sombrero puntiagudo: niveles irregulares (cada uno con su giro y desplazamiento)
    x, y, z = 0.0, T + 0.4, 0.4
    az = ax = 0.0
    pasos = [(0, 0, 9.0, 1.6), (2, -3, 8.0, 1.4), (4, -1, 7.0, 1.8), (5, -3, 5.8, 1.6), (9, -2, 4.8, 2.0),
             (12, 0, 3.8, 2.2), (15, 1, 2.9, 2.4), (18, 0, 2.0, 2.4), (21, 2, 1.3, 2.4), (24, 0, 0.7, 2.2)]
    centros = []
    for k, (dz, dx, ancho, alto) in enumerate(pasos):
        az += dz
        ax += dx
        giro = (azar(17, k) - 0.5) * 16
        w = ancho / 2
        p.caja("Head/sombrero", f"sombrero{k}", (x - w, y, z - w), (x + w, y + alto, z + w), sombrero,
               rot=(ax, giro, az), piv=(x, y, z), dens=2)
        centros.append((x, y, z, w, az))
        rz, rx = math.radians(az), math.radians(ax)
        x += -math.sin(rz) * alto * 0.92 + (azar(18, k) - 0.5) * 0.3
        y += math.cos(rz) * math.cos(rx) * alto * 0.92
        z += math.sin(rx) * alto * 0.92
    rombo(p, "Head/sombrero", "colgante_punta", x - 0.6, y - 1.6, z, 1.2, ORO["b"], cadena=1.2)
    for k, (i, lado) in enumerate(((1, 1), (3, -1), (5, 1))):         # pliegues de papel que salen del cono
        cx, cy, cz, w, _ = centros[i]
        p.plano("Head/sombrero", f"pliegue{k}", (cx + lado * w - 1.6, cy, cz - 1.0),
                (cx + lado * w + 1.6, cy + 3.0, cz - 1.0), sprite({"todas": PLIEGUE}, PAL_PLIEGUE),
                rot=(0, 20 * lado, -30 * lado), piv=(cx + lado * w, cy, cz - 1.0), dens=2)
    for s in (1, -1):                                                   # dos puntas tipo orejas
        p.plano("Head/sombrero", f"oreja_{'d' if s > 0 else 'i'}", (s * 4.0 - 2.5, T + 1.0, -0.5),
                (s * 4.0 + 2.5, T + 7.0, -0.5), sprite({"todas": OREJA}, PAL_OREJA), rot=(0, 0, -s * 30),
                piv=(s * 4.0, T + 1.0, -0.5), dens=2)
    # aro dorado con rombo azul y colgantes, del lado izquierdo (-X)
    p.plano("Head/sombrero", "aro", (-7.6, T - 2.4, -2.4), (-3.6, T + 1.6, -2.4),
            sprite({"todas": ARO}, PAL_ARO), rot=(0, 20, 0), piv=(-5.6, T, -2.4), dens=2)
    for k, (xx, largo) in enumerate(((-5.6, 3.0), (-6.8, 1.6), (-4.4, 1.8))):
        rombo(p, "Head/sombrero", f"colgante{k}", xx, T - 3.0 - largo, -2.7, 1.1 + 0.3 * (k == 0), ORO["b"],
              cadena=largo)
    for k, (xx, zz, largo) in enumerate(((6.0, -1.8, 1.4), (6.6, 1.2, 2.6), (4.8, -4.8, 2.0))):
        rombo(p, "Head/sombrero", f"colgante_der{k}", xx, T - 1.4 - largo, zz, 1.1, ORO["b"], cadena=largo)
    rombo(p, "Body/collar", "colgante_pecho", 0, C - 4.4, -4.85, 1.4, ORO["b"], cadena=1.5)

    # ---- cola en media luna: hoja ancha azul y negra con bordes dorados
    x, y, z = 1.6, L - 1.0, 4.2
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

    # ---- mochila: pergaminos enrollados atras con tapas de bronce
    for k, (yy, zz) in enumerate(((L + 3.6, 5.4), (L + 1.6, 5.2))):
        rollo = crema(semilla=7 + k, borde=CREMA["s"])
        for giro in (0, 45):
            p.caja("Body/mochila", f"rollo{k}_{giro}", (-3.8, yy - 0.85, zz - 0.85), (3.8, yy + 0.85, zz + 0.85), rollo,
                   rot=(giro, 0, 0), piv=(0, yy, zz))
        for s in (1, -1):
            p.caja("Body/mochila", f"tapa{k}_{s}", (s * 3.8 - 0.5, yy - 1.0, zz - 1.0), (s * 3.8 + 0.5, yy + 1.0, zz + 1.0),
                   metal(ORO["s"], 8))
    return p
