"""
Pibble, el semidios errante. Hecho a mano con el kit (boceto 1).

Bajito (~1.6 bloques). Rostro de vacio negro con ojos almendrados que brillan y marca de ojo dorada,
bufanda negra sobre la boca, sombrero puntiagudo crema y negro que se dobla con dos puntas tipo orejas,
aro dorado con rombo azul y colgantes de rombos, manto crema con dibujo geometrico y tiras largas,
abrigo oscuro con forro azul acero y rombos dorados, cadena dorada con colgantes, pantalon bombacho,
vendas y botas con puntera dorada, cola en media luna, pergaminos enrollados atras.
"""

import math

from ..kit import Personaje, dibujo, sprite, tonos
from ..pintura import metal
from ..textura import TRANSPARENTE, hex_a_rgba

NEGRO = tonos("#1C1618")
MARRON = tonos("#3A2A22")
CREMA = tonos("#E6DAC2")
ORO = tonos("#C29A48")
AZUL = tonos("#3E5C72")
VACIO = "#100C0E"

# ---------------------------------------------------------------- dibujos

CARA = dibujo("""
    KKKKKKKKKKKKKKKK
    KKKKKKKgKKKKKKKK
    KKKKKKgGgKKKKKKK
    KKKKKgKoKgKKKKKK
    KKKKKKgGgKKKKKKK
    KKKKKKKgKKKKKKKK
    KKooKKKKKKKKooKK
    KKEEEoKKKKoEEEKK
    KKoEEEoKKoEEEoKK
    KKKooooKKooooKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
""")
PAL_CARA = {"K": VACIO, "g": ORO["s"], "G": ORO["h"], "E": "#FFF0C0", "o": "#B08A40"}

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


# ---------------------------------------------------------------- pintores a mano

def hex_(c):
    return hex_a_rgba(c)


def tela_crema(cortes=None, semilla=0, dibujo_geo=True, borde=MARRON["b"]):
    """Tela crema con dibujo geometrico (triangulos y rombos marrones, puntos dorados) y borde en picos."""
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
        if dibujo_geo:
            u, v = (t.i + semilla) % 8, (t.j + semilla * 3) % 10
            if v in (6, 7) and abs(u - 3.5) < (7 - v) + 1.5 and abs(u - 3.5) > (6 - v):
                return hex_(MARRON["b"])                   # triangulos
            if v == 2 and u in (3, 4):
                return hex_(ORO["b"])                      # puntos dorados
            if t.fila_abajo in (corte + 2,) and (t.i % 3 == 1):
                return hex_(ORO["s"])
        k = t.j / max(1, t.th - 1)
        c = CREMA["l"] if k < 0.12 else (CREMA["b"] if k < 0.75 else CREMA["s"])
        if (t.i + semilla) % 5 == 0 and t.fila_abajo > corte + 2:
            c = CREMA["s"]
        return hex_(c)
    return p


def tela_negra(cortes=None, semilla=0, forro=None, rombos=True, oro_abajo=True):
    """Tela oscura del abrigo. 'forro': columnas (por el lado) donde asoma el forro azul con rombos dorados."""
    def p(t):
        if t.cara in ("up", "down"):
            return hex_(NEGRO["s"])
        corte = 0
        if cortes:
            corte = cortes[(t.i + semilla) % len(cortes)]
            if t.fila_abajo < corte:
                return TRANSPARENTE
        if oro_abajo and t.fila_abajo == corte:
            return hex_(ORO["s"])
        en_forro = forro and ((forro == "izq" and t.i < 3) or (forro == "der" and t.i >= t.tw - 3)
                              or (forro == "abajo" and t.fila_abajo < corte + 5))
        if en_forro:
            if rombos and (t.i + t.j) % 4 == 0 and (t.i - t.j) % 4 == 0:
                return hex_(ORO["b"])
            return hex_(AZUL["b"] if (t.i + t.j) % 2 else AZUL["s"])
        k = t.j / max(1, t.th - 1)
        c = NEGRO["l"] if k < 0.1 else NEGRO["b"]
        if (t.i + semilla) % 4 == 0 and t.fila_abajo > corte + 2:
            c = NEGRO["s"]
        if rombos and (t.i + 2 * t.j + semilla) % 13 == 0:
            c = MARRON["l"]
        return hex_(c)
    return p


def tela_marron(semilla=0):
    def p(t):
        if t.cara in ("up", "down"):
            return hex_(MARRON["s"])
        k = t.j / max(1, t.th - 1)
        if (t.i + semilla) % 3 == 0:
            return hex_(MARRON["s"])
        return hex_(MARRON["l"] if k < 0.1 else (MARRON["b"] if k < 0.8 else MARRON["s"]))
    return p


def sombrero(t):
    """Frente y espalda crema con una franja negra en V, costados negros: triangulos grandes y limpios."""
    if t.cara == "down":
        return hex_(NEGRO["s"])
    if t.cara == "up":
        return hex_(CREMA["l"])
    if t.cara in ("east", "west"):
        return hex_(NEGRO["l"] if t.j == 0 else NEGRO["b"])
    centro = (t.tw - 1) / 2
    franja = abs(t.i - centro) < 0.6 + t.tw * 0.08 if t.cara == "south" else False
    if franja:
        return hex_(NEGRO["b"])
    borde = t.i == 0 or t.i == t.tw - 1
    if borde:
        return hex_(MARRON["b"])
    return hex_(CREMA["l"] if t.j == 0 else CREMA["b"])


def vendas(t):
    """Piernas: vendas con rombos sobre fondo oscuro."""
    if t.cara in ("up", "down"):
        return hex_(MARRON["s"])
    h = t.fila_abajo
    if h < 3:
        return hex_(NEGRO["b"])
    if (t.i + h) % 4 == 0 or (t.i - h) % 4 == 0:
        return hex_(CREMA["s"])
    return hex_(AZUL["s"] if h % 2 else NEGRO["b"])


def guante(t):
    return hex_(NEGRO["s"] if t.fila_abajo == 0 else NEGRO["b"])


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

def rombo(p, grupo, nombre, x, y, z, tam, color, cadena=0.0):
    """Colgante en forma de rombo (cubo girado 45 grados) con su cadenita."""
    oro = metal(color, 7)
    p.caja(grupo, nombre, (x - tam / 2, y - tam / 2, z - 0.25), (x + tam / 2, y + tam / 2, z + 0.25), oro,
           rot=(0, 0, 45), piv=(x, y, z))
    if cadena:
        p.caja(grupo, nombre + "_cadena", (x - 0.12, y + tam * 0.6, z - 0.12), (x + 0.12, y + tam * 0.6 + cadena, z + 0.12),
               oro)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("pibble", altura=26, torso=(8, 9, 4), brazo=(3.5, 4))
    C, L, T = p.cuello, p.lh, p.tope                     # cuello 18, cintura 9, arriba de la cabeza 26
    oro = metal(ORO["b"], 3)

    cabeza = sprite({"north": CARA}, PAL_CARA, base=lambda t: hex_(VACIO))
    p.cuerpo(cabeza=cabeza, torso=tela_negra(semilla=1), brazo=tela_negra(semilla=2), pierna=vendas,
             mano=guante, dens=2)

    # ---- capucha crema bajo el sombrero, enmarca la cara
    p.caja("Head/capucha", "capucha_arriba", (-5.0, T - 0.3, -4.8), (5.0, T + 0.6, 5.0), tela_crema(semilla=1))
    p.par("Head/capucha", "capucha_lado", (4.3, C - 0.5, -4.5), (5.0, T - 0.3, 5.0),
          tela_crema(cortes=picos(3, prof=3), semilla=2), rot=(0, 0, 8), piv=(4.6, T, 0), dens=2)
    p.caja("Head/capucha", "capucha_atras", (-5.0, C - 1.5, 4.3), (5.0, T - 0.3, 5.0),
           tela_crema(cortes=picos(4, prof=4), semilla=3), dens=2)

    # ---- sombrero puntiagudo: niveles que se achican y se doblan hacia un costado
    x, y, z = 0.0, T + 0.5, 0.3
    az = ax = 0.0
    # muchos niveles bajos que se achican de a poco: se lee como cono, no como torta de pisos
    pasos = [(0, 0, 9.4, 1.4), (2, -2, 8.4, 1.4), (3, -2, 7.4, 1.4), (4, -2, 6.4, 1.4), (6, -2, 5.4, 1.4),
             (8, -1, 4.4, 1.4), (10, 0, 3.4, 1.4), (12, 0, 2.5, 1.4), (14, 0, 1.7, 1.4), (16, 0, 1.0, 1.6)]
    for k, (dz, dx, ancho, alto) in enumerate(pasos):
        az += dz
        ax += dx
        w = ancho / 2
        p.caja("Head/sombrero", f"sombrero{k}", (x - w, y, z - w), (x + w, y + alto, z + w), sombrero,
               rot=(ax, 0, az), piv=(x, y, z), dens=2)
        rz, rx = math.radians(az), math.radians(ax)
        x += -math.sin(rz) * alto * 0.9
        y += math.cos(rz) * math.cos(rx) * alto * 0.9
        z += math.sin(rx) * alto * 0.9
    rombo(p, "Head/sombrero", "colgante_punta", x - 0.6, y - 1.6, z, 1.2, ORO["b"], cadena=1.2)
    # ala: borde ancho y angular alrededor de la base
    p.caja("Head/sombrero", "ala", (-5.8, T + 0.1, -5.6), (5.8, T + 0.6, 5.6),
           tela_crema(semilla=9, dibujo_geo=False, borde=MARRON["b"]), dens=2)
    # dos puntas tipo orejas
    for s in (1, -1):
        p.plano("Head/sombrero", f"oreja_{'d' if s > 0 else 'i'}", (s * 4.0 - 2.5, T + 1.0, -0.5),
                (s * 4.0 + 2.5, T + 7.0, -0.5), sprite({"todas": OREJA}, PAL_OREJA), rot=(0, 0, -s * 30),
                piv=(s * 4.0, T + 1.0, -0.5), dens=2)
    # aro dorado con rombo azul y colgantes, del lado izquierdo (-X)
    p.plano("Head/sombrero", "aro", (-7.2, T - 2.2, -2.0), (-3.2, T + 1.8, -2.0),
            sprite({"todas": ARO}, PAL_ARO), rot=(0, 20, 0), piv=(-5.2, T, -2.0), dens=2)
    for k, (xx, largo) in enumerate(((-5.2, 3.0), (-6.4, 1.6), (-4.0, 1.8))):
        rombo(p, "Head/sombrero", f"colgante{k}", xx, T - 2.8 - largo, -2.3, 1.1 + 0.3 * (k == 0), ORO["b"], cadena=largo)
    rombo(p, "Head/sombrero", "colgante_der", 5.6, T - 1.8, -1.6, 1.1, ORO["b"], cadena=1.4)

    # ---- bufanda negra sobre la boca
    bufanda = tela_negra(semilla=4, rombos=False, oro_abajo=False)
    bufanda = (lambda base: (lambda t: hex_(NEGRO["b"]) if t.cara in ("north", "south", "east", "west") and t.j == 0
                             else base(t)))(bufanda)
    p.caja("Head/bufanda", "bufanda_cara", (-4.6, C - 0.2, -4.7), (4.6, C + 2.6, -3.9), bufanda)
    p.caja("Body/bufanda", "bufanda_cuello", (-4.9, C - 2.5, -3.2), (4.9, C + 0.5, 3.2), bufanda)
    p.caja("Body/bufanda", "bufanda_cola", (1.0, L - 1, -3.6), (3.2, C - 2.0, -3.1),
           tela_negra(cortes=picos(5, prof=2), semilla=5, rombos=False), rot=(0, 0, -6), piv=(2.1, C - 2, -3.3), dens=2)

    # ---- abrigo oscuro abierto con forro azul
    p.caja("Body/abrigo", "abrigo_espalda", (-4.6, L - 0.5, 2.0), (4.6, C, 2.6), tela_negra(semilla=6))
    p.par("Body/abrigo", "abrigo_frente", (0.9, L - 0.5, -2.6), (4.6, C, -2.0), tela_negra(semilla=7, forro="izq"),
          dens=2)
    p.par("Body/abrigo", "abrigo_costado", (4.0, L - 0.5, -2.6), (4.6, C, 2.6), tela_negra(semilla=8))
    # faldones del abrigo (en las piernas), cola de atras mas larga
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = sorted((lado * 0.8, lado * 4.9))
        p.caja(f"{hueso}/faldon", "faldon_frente", (x1, 1.5, -2.9), (x2, L + 0.2, -2.4),
               tela_negra(cortes=picos(10 + lado, prof=3), semilla=9, forro="izq" if lado > 0 else "der"),
               rot=(6, 0, -4 * lado), piv=((x1 + x2) / 2, L, -2.6), dens=2)
        x1, x2 = sorted((lado * 4.4, lado * 4.9))
        p.caja(f"{hueso}/faldon", "faldon_lado", (x1, 1.0, -2.6), (x2, L + 0.2, 2.6),
               tela_negra(cortes=picos(12 + lado, prof=3), semilla=10, forro="abajo"), rot=(0, 0, 6 * lado),
               piv=(lado * 4.6, L, 0), dens=2)
        x1, x2 = sorted((0, lado * 4.9))
        p.caja(f"{hueso}/faldon", "faldon_atras", (x1, -0.2, 2.4), (x2, L + 0.2, 2.9),
               tela_negra(cortes=picos(14 + lado, prof=5), semilla=11, forro="abajo"), rot=(-6, 0, 0),
               piv=(lado * 2.4, L, 2.6), dens=2)

    # ---- manto crema sobre los hombros y tiras largas al frente
    p.caja("Body/manto", "manto_espalda", (-5.2, L + 1.5, 2.7), (5.2, C + 0.6, 3.3),
           tela_crema(cortes=picos(20, prof=6), semilla=4), rot=(-6, 0, 0), piv=(0, C + 0.6, 2.9), dens=2)
    for lado in (1, -1):
        hueso = "RightArm" if lado > 0 else "LeftArm"
        x1, x2 = sorted((lado * 3.4, lado * 8.3))
        p.caja(f"{hueso}/manto", "manto_hombro", (x1, C - 4.5, -2.8), (x2, C + 0.8, 2.8),
               tela_crema(cortes=picos(22 + lado, prof=4), semilla=5), rot=(0, 0, 10 * lado),
               piv=(lado * 3.6, C + 0.8, 0), dens=2)
        x1, x2 = sorted((lado * 1.2, lado * 2.8))
        p.caja("Body/manto", f"tira_{'d' if lado > 0 else 'i'}", (x1, 2.5, -3.3), (x2, C + 0.4, -2.9),
               tela_crema(cortes=[0, 1, 2, 1] if lado > 0 else [2, 1, 0, 1], semilla=6 + lado), rot=(5, 0, 0),
               piv=((x1 + x2) / 2, C, -3.1), dens=2)

    # ---- mangas con puño azul y guantes
    for lado in (1, -1):
        hueso = "RightArm" if lado > 0 else "LeftArm"
        x1, x2 = sorted((lado * 3.8, lado * 7.8))
        p.caja(f"{hueso}/manga", "puno", (x1, C - 7.0, -2.4), (x2, C - 5.6, 2.4),
               tela_negra(semilla=12, forro="abajo"), dens=2)

    # ---- cinturon de cuero, cadena dorada y colgantes
    p.caja("Body/cinturon", "cinturon", (-4.9, L - 0.2, -2.9), (4.9, L + 1.4, 2.9), tela_marron(1))
    p.caja("Body/cinturon", "hebilla", (-1.0, L - 0.4, -3.15), (1.0, L + 1.6, -2.9), metal(ORO["b"], 4, gema=AZUL["l"]))
    for k in range(7):
        xx = -4.2 + k * 1.4
        yy = L - 1.0 - abs(xx) * 0.15
        p.caja("Body/cinturon", f"eslabon{k}", (xx - 0.45, yy - 0.45, -3.2), (xx + 0.45, yy + 0.45, -2.95), oro,
               rot=(0, 0, 45), piv=(xx, yy, -3.1))
    for k, (xx, largo) in enumerate(((-3.6, 1.5), (-1.6, 2.6), (2.2, 2.0), (3.8, 1.2))):
        rombo(p, "Body/cinturon", f"colgante{k}", xx, L - 1.6 - largo, -3.25, 1.2, ORO["b"], cadena=largo)
    rombo(p, "Body/collar", "colgante_pecho", 0, C - 3.5, -3.45, 1.4, ORO["b"], cadena=1.5)

    # ---- pantalon bombacho y botas con puntera dorada
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = sorted((lado * -0.1, lado * 4.5))
        p.caja(f"{hueso}/pantalon", "bombacho", (x1, 3.0, -2.5), (x2, L, 2.5), tela_marron(2 + lado))
        x1, x2 = sorted((lado * -0.1, lado * 4.3))
        p.caja(f"{hueso}/bota", "bota", (x1, 0, -2.5), (x2, 1.4, 2.3), tela_negra(semilla=13, rombos=False))
        x1, x2 = sorted((lado * 0.4, lado * 3.8))
        p.caja(f"{hueso}/bota", "puntera", (x1, 0, -2.9), (x2, 1.0, -2.2), metal(ORO["b"], 5))

    # ---- cola en media luna: hoja ancha azul y negra con bordes dorados
    x, y, z = 1.6, L - 0.5, 3.0
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
        p.caja("Body/cola", f"cola{k}", (x - w / 2, y, z - 0.35), (x + w / 2, y + largo + 0.3, z + 0.35), hoja,
               rot=(0, -15, ang), piv=(x, y, z), dens=2)
        r = math.radians(ang)
        x += -math.sin(r) * largo * 0.95
        y += math.cos(r) * largo * 0.95
    p.plano("Body/cola", "cola_punta", (x - 2.0, y - 0.3, z), (x + 2.0, y + 4.6, z), sprite({"todas": PUNTA_COLA}, PAL_COLA),
            rot=(0, -15, -12), piv=(x, y, z), dens=2)

    # ---- mochila: pergaminos enrollados atras con tapas de bronce
    for k, (yy, zz) in enumerate(((L + 3.5, 4.2), (L + 1.6, 4.0))):
        rollo = tela_crema(semilla=7 + k, dibujo_geo=False, borde=CREMA["s"])
        for giro in (0, 45):
            p.caja("Body/mochila", f"rollo{k}_{giro}", (-3.6, yy - 0.8, zz - 0.8), (3.6, yy + 0.8, zz + 0.8), rollo,
                   rot=(giro, 0, 0), piv=(0, yy, zz))
        for s in (1, -1):
            p.caja("Body/mochila", f"tapa{k}_{s}", (s * 3.6 - 0.5, yy - 0.95, zz - 0.95), (s * 3.6 + 0.5, yy + 0.95,
                                                                                          zz + 0.95), metal(ORO["s"], 8))
    p.caja("Body/mochila", "correa", (-0.6, L + 0.5, 2.9), (0.6, C - 0.5, 3.4), tela_marron(5), rot=(0, 0, 30),
           piv=(0, L + 4, 3.1))
    return p
