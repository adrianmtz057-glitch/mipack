"""
Pibble, el semidios errante. Hecho a mano con el kit (boceto 5, segun la hoja de referencia final).

Todo 3D: capucha crema grande y angulosa con dos orejas de gato negras, cara de vacio hundida con ojos
crema en almendra y un rombo dorado, aros y colgantes dorados, bufanda negra gruesa, capa crema en
forma de A con puntas diagonales y ribete dorado, estola azul marino con lineas doradas, mangas negras
grandes que esconden las manos, bombachos negros, botas puntiagudas con dorado y cola en media luna.
Texturas limpias y planas (estilo low-poly), sin dibujo repetido.
"""

import math

from ..kit import Personaje, dibujo, sprite, tonos
from ..pintura import metal
from ..textura import TRANSPARENTE, hex_a_rgba

NEGRO = tonos("#221D22")
AZUL = tonos("#2E4458")
CREMA = tonos("#DCD3C3")
TOSTADO = tonos("#B08A60")
ORO = tonos("#C8A058")
VACIO = "#0E0B0E"

# ---------------------------------------------------------------- dibujos

CARA = dibujo("""
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKgKKKKKK
    KKKKKKKKgKgKKKKK
    KKKKKKKKKgKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKWWWKKWWWKKKK
    KKWWWWWKKWWWWWKK
    KKKKwwKKKKwwKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
    KKKKKKKKKKKKKKKK
""")
PAL_CARA = {"K": VACIO, "g": ORO["b"], "W": "#F2E6CC", "w": "#C8B898"}

ARO = dibujo("""
    ...GGGG...
    ..Gg..gG..
    .Gg....gG.
    G...bb...G
    G..bBBb..G
    G..bBBb..G
    G...bb...G
    .Gg....gG.
    ..Gg..gG..
    ...GGGG...
""")
PAL_ARO = {"G": ORO["l"], "g": ORO["s"], "b": AZUL["s"], "B": AZUL["l"]}

ESTOLA = dibujo("""
    GaaaaaG
    GaGGGaG
    GaGaaaG
    GaGGGaG
    GaaaGaG
    GaGGGaG
    GaaaaaG
    GaaGaaG
    GaGaGaG
    GaaGaaG
    GaaaaaG
    GaGGGaG
    GaGaaaG
    GaGGGaG
    GaaaGaG
    GaGGGaG
    GaaaaaG
    GaaaaaG
    .GaaaG.
    ..GaG..
    ...G...
""")
PAL_ESTOLA = {"G": ORO["b"], "a": AZUL["b"]}

EMBLEMA = dibujo("""
    ...G...
    ..GaG..
    .GaGaG.
    GaGaGaG
    .GaGaG.
    ..GaG..
    ...G...
""")

PUNTA_COLA = dibujo("""
    ....G
    ...GD
    ..GDB
    .GDBB
    GDBBB
    GDBoB
    GDBBB
    .GDBB
""")
PAL_COLA = {"G": ORO["b"], "D": NEGRO["b"], "B": AZUL["b"], "o": ORO["l"]}


# ---------------------------------------------------------------- pintores (limpios, planos)

def hex_(c):
    return hex_a_rgba(c)


def _uv(t):
    u = math.floor((t.x if t.cara in ("north", "south", "up", "down") else t.z) * 2 + 0.01)
    v = math.floor(t.y * 2 + 0.01)
    return u, v


def crema(diag=None, prof=0, picos_=None, semilla=0, oro=True, parches=True):
    """Tela crema lisa: luz arriba, sombra abajo, linea dorada sobre el borde.
    diag='izq'/'der': borde inferior en diagonal (la punta mas larga queda de ese lado)."""
    def p(t):
        if t.cara == "up":
            return hex_(CREMA["l"])
        if t.cara == "down":
            return hex_(AZUL["s"])                               # forro oscuro por debajo
        corte = 0
        if diag:
            f = t.i / max(1, t.tw - 1)
            corte = round((f if diag == "izq" else 1 - f) * prof)
        elif picos_:
            corte = picos_[(t.i + semilla) % len(picos_)]
        if t.fila_abajo < corte:
            return TRANSPARENTE
        if oro and t.fila_abajo == corte:
            return hex_(ORO["s"])
        if oro and t.fila_abajo == corte + 1:
            return hex_(ORO["b"])
        if oro and t.fila_abajo == corte + 2:
            return hex_(AZUL["b"])
        if parches and corte + 3 <= t.fila_abajo <= corte + 6:
            return hex_(NEGRO["b"] if (t.i + semilla) % 9 < 6 else AZUL["b"])   # banda oscura que sigue el borde
        k = t.j / max(1, t.th - 1)
        return hex_(CREMA["l"] if k < 0.15 else (CREMA["b"] if k < 0.7 else CREMA["s"]))
    return p


def negro(diag=None, prof=0, picos_=None, forro=False, semilla=0):
    def p(t):
        if t.cara == "up":
            return hex_(NEGRO["l"])
        if t.cara == "down":
            return hex_(NEGRO["s"])
        corte = 0
        if diag:
            f = t.i / max(1, t.tw - 1)
            corte = round((f if diag == "izq" else 1 - f) * prof)
        elif picos_:
            corte = picos_[(t.i + semilla) % len(picos_)]
        if t.fila_abajo < corte:
            return TRANSPARENTE
        if forro and t.fila_abajo < corte + 2:
            return hex_(AZUL["b"])
        k = t.j / max(1, t.th - 1)
        return hex_(NEGRO["l"] if k < 0.12 else (NEGRO["b"] if k < 0.75 else NEGRO["s"]))
    return p


def oreja_pintor(t):
    """Oreja de gato negra con el interior crema en la cara de adelante."""
    if t.cara == "down":
        return hex_(NEGRO["s"])
    if t.cara == "north" and 0 < t.i < t.tw - 1:
        return hex_(CREMA["b"] if t.j else CREMA["l"])
    if t.cara == "up":
        return hex_(NEGRO["l"])
    return hex_(NEGRO["b"] if t.cara != "south" else NEGRO["s"])


def bota(t):
    if t.cara == "up":
        return hex_(NEGRO["l"])
    if t.fila_abajo == 0:
        return hex_(TOSTADO["s"])
    return hex_(NEGRO["b"])


# ---------------------------------------------------------------- piezas reutilizables

def losa(p, grupo, nombre, cx, cz, y1, y2, w, d, r, pintor, rot=None, piv=None, dens=2):
    """Rebanada de esquinas escalonadas (cruz de dos cajas)."""
    p.caja(grupo, nombre + "_a", (cx - w / 2, y1, cz - d / 2 + r), (cx + w / 2, y2, cz + d / 2 - r), pintor, rot, piv,
           dens=dens)
    p.caja(grupo, nombre + "_b", (cx - w / 2 + r, y1, cz - d / 2), (cx + w / 2 - r, y2, cz + d / 2), pintor, rot, piv,
           dens=dens)


def rombo(p, grupo, nombre, x, y, z, tam, cadena=0.0):
    """Colgante: rombo dorado alargado (dos cubos a 45 grados) con cadena."""
    oro = metal(ORO["b"], 7)
    p.caja(grupo, nombre, (x - tam / 2, y - tam / 2, z - 0.3), (x + tam / 2, y + tam / 2, z + 0.3), oro,
           rot=(0, 0, 45), piv=(x, y, z))
    p.caja(grupo, nombre + "_punta", (x - 0.25, y - tam * 1.3, z - 0.25), (x + 0.25, y - tam * 0.4, z + 0.25), oro)
    if cadena:
        p.caja(grupo, nombre + "_cadena", (x - 0.15, y + tam * 0.6, z - 0.15), (x + 0.15, y + tam * 0.6 + cadena, z + 0.15),
               oro)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("pibble", altura=26, torso=(8, 9, 4), brazo=(3.5, 4))
    C, L, T = p.cuello, p.lh, p.tope                     # cuello 18, cintura 9, arriba de la cabeza 26

    cabeza = sprite({"north": CARA}, PAL_CARA, base=lambda t: hex_(VACIO))
    p.cuerpo(cabeza=cabeza, torso=negro(), brazo=negro(), pierna=negro(), mano=negro(), dens=2)

    # ================================================================ CAPUCHA (carpa crema angulosa)
    g = "Head/capucha"
    p.caja(g, "capucha_techo", (-5.6, T - 0.4, -5.0), (5.6, T + 1.2, 5.6), crema(semilla=1, oro=False, parches=False),
           dens=2)
    p.caja(g, "capucha_pico", (-4.0, T + 1.2, -3.4), (4.0, T + 2.2, 4.2), crema(semilla=2, oro=False, parches=False),
           rot=(-6, 0, 0), piv=(0, T + 1.2, 0.4), dens=2)
    p.caja(g, "capucha_atras", (-5.6, C - 1.5, 4.6), (5.6, T - 0.4, 5.6), crema(semilla=4), dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 4.6, s * 5.6))
        p.caja(g, f"capucha_lado{s}", (x1, C - 2.5, -5.0), (x2, T - 0.4, 5.6),
               crema(diag="der" if s > 0 else "izq", prof=5, semilla=5 + s), rot=(0, 0, 8 * s),
               piv=(s * 5.1, T, 0), dens=2)
    # visera profunda: la cara queda en sombra
    p.caja(g, "visera", (-5.6, T - 0.6, -6.8), (5.6, T + 0.6, -4.6), crema(semilla=7, oro=False, parches=False),
           rot=(-24, 0, 0), piv=(0, T + 0.4, -4.8), dens=2)
    # solapas delanteras que bajan en punta hasta el pecho
    for s in (1, -1):
        x1, x2 = sorted((s * 1.4, s * 5.6))
        p.caja(g, f"solapa{s}", (x1, C - 4.0, -5.4), (x2, C + 1.5, -4.8),
               crema(diag="der" if s > 0 else "izq", prof=7, semilla=8 + s), rot=(10, 0, 6 * s),
               piv=(s * 3.5, C + 1.5, -5.1), dens=2)

    # orejas de gato negras en las esquinas de arriba
    for s in (1, -1):
        x, y, z = s * 3.3, T + 0.8, 0.6
        az = ax = 0.0
        for k, (dz, dx, w, h) in enumerate(((8, -4, 4.6, 1.8), (4, -2, 3.4, 1.8), (4, 0, 2.2, 1.8), (4, 0, 1.0, 1.6))):
            az += dz * s
            ax += dx
            p.caja("Head/orejas", f"oreja{s}_{k}", (x - w / 2, y, z - w / 2), (x + w / 2, y + h, z + w / 2), oreja_pintor,
                   rot=(ax, 0, -az), piv=(x, y, z), dens=2)
            rz, rx = math.radians(-az), math.radians(ax)
            x += -math.sin(rz) * h * 0.9
            y += math.cos(rz) * math.cos(rx) * h * 0.9
            z += math.sin(rx) * h * 0.9

    # aro grande al costado izquierdo (mira hacia afuera) y aro chico del otro lado, con colgantes
    p.plano("Head/joyas", "aro_grande", (-6.0, T - 4.0, -2.6), (-6.0, T + 1.0, 2.4), sprite({"todas": ARO}, PAL_ARO),
            rot=(0, 0, -8), piv=(-6.0, T, 0), dens=2)
    rombo(p, "Head/joyas", "colgante_aro", -6.2, T - 7.6, 0, 1.3, cadena=2.6)
    p.plano("Head/joyas", "aro_chico", (6.1, T - 3.0, -1.4), (6.1, T - 0.2, 1.4), sprite({"todas": ARO}, PAL_ARO),
            rot=(0, 0, 8), piv=(6.1, T, 0), dens=2)
    rombo(p, "Head/joyas", "colgante_aro_chico", 6.3, T - 5.6, 0, 1.0, cadena=1.8)
    for k, (x, largo) in enumerate(((-5.0, 1.2), (5.0, 1.6))):
        rombo(p, "Head/joyas", f"colgante_solapa{k}", x, C - 6.0 - largo * 0.5, -5.3, 1.1, cadena=largo)

    # ================================================================ BUFANDA negra gruesa
    losa(p, "Body/bufanda", "bufanda", 0, 0, C - 1.0, C + 1.2, 9.8, 7.0, 1.6, negro(semilla=1))
    losa(p, "Head/bufanda", "bufanda_boca", 0, -0.6, C + 0.8, C + 2.6, 9.0, 9.6, 1.6, negro(semilla=2))
    p.caja("Body/bufanda", "lazo", (-2.6, C - 2.6, -4.4), (2.6, C - 0.4, -3.6), negro(semilla=3))

    # ================================================================ CUERPO: capa larga en A
    # nucleo negro (abrigo) y bajo negro largo
    losa(p, "Body/abrigo", "abrigo", 0, 0, L - 0.5, C + 0.3, 9.0, 6.0, 1.4, negro())
    losa(p, "Body/abrigo", "bajo", 0, 0, 3.0, L - 0.5, 9.6, 6.6, 1.6, negro(picos_=[0, 1, 2, 1], forro=True))
    # estola azul con lineas doradas (adelante) y panel azul con emblema (atras)
    for s in (1, -1):
        x1, x2 = sorted((s * 0.2, s * 2.0))
        p.caja("Body/estola", f"estola{s}", (x1, 2.6, -4.3), (x2, C - 1.0, -3.9),
               sprite({"north": ESTOLA, "south": ESTOLA}, PAL_ESTOLA), rot=(5, 0, -2 * s),
               piv=((x1 + x2) / 2, C - 1, -4.1), dens=2)
    p.caja("Body/estola", "panel_atras", (-1.8, 2.0, 5.0), (1.8, C - 1.0, 5.4),
           sprite({"south": EMBLEMA + ["aaaaaaa"] * 10}, {"G": ORO["b"], "a": AZUL["b"]}, base=negro()),
           rot=(-12, 0, 0), piv=(0, C - 1, 5.2), dens=2)
    # capa crema: paneles grandes que se abren desde los hombros y terminan en puntas diagonales
    for s in (1, -1):
        x1, x2 = sorted((s * 2.0, s * 6.8))
        p.caja("Body/capa", f"capa_frente{s}", (x1, 4.0, -4.6), (x2, C + 0.6, -4.1),
               crema(diag="der" if s > 0 else "izq", prof=12, semilla=10 + s), rot=(10, 0, 8 * s),
               piv=(s * 4.0, C + 0.6, -4.3), dens=2)
        x1, x2 = sorted((s * 6.4, s * 6.9))
        p.caja("Body/capa", f"capa_lado{s}", (x1, 3.0, -4.4), (x2, C + 0.6, 4.6),
               crema(diag="izq" if s > 0 else "der", prof=8, semilla=12 + s), rot=(0, 0, 8 * s),
               piv=(s * 4.0, C + 0.6, 0), dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 1.8, s * 6.8))
        p.caja("Body/capa", f"capa_atras{s}", (x1, 3.0, 4.3), (x2, C + 0.6, 4.8),
               crema(diag="izq" if s > 0 else "der", prof=6, semilla=14 + s), rot=(-10, 0, 8 * s),
               piv=(s * 4.0, C + 0.6, 4.5), dens=2)

    # mangas negras grandes que esconden las manos (asoman debajo de la capa)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        cx = s * 6.0
        losa(p, f"{hueso}/manga", "manga", cx, 0, C - 9.6, C - 2.0, 4.6, 5.0, 1.0, negro(forro=True))

    # bombachos negros y botas puntiagudas con dorado
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        cx = s * 2.3
        losa(p, f"{hueso}/pantalon", "bombacho", cx, 0, 1.4, 4.6, 5.0, 5.2, 1.2, negro(semilla=4))
        losa(p, f"{hueso}/bota", "bota", cx, -0.3, 0, 1.6, 4.2, 5.2, 0.8, bota)
        p.caja(f"{hueso}/bota", "punta", (cx - 1.0, 0, -4.4), (cx + 1.0, 1.2, -2.6), bota, rot=(0, 45, 0),
               piv=(cx, 0.6, -3.4))
        p.caja(f"{hueso}/bota", "rombo", (cx - 0.7, 1.0, -3.2), (cx + 0.7, 2.4, -2.9), metal(ORO["b"], 5),
               rot=(0, 0, 45), piv=(cx, 1.7, -3.0))

    # ================================================================ COLA en media luna
    x, y, z = 1.4, 4.0, 4.6
    angulos = (-140, -120, -100, -80, -60, -42, -26)
    anchos = (2.0, 2.8, 3.4, 3.6, 3.2, 2.6, 1.9)

    def hoja(t):
        if t.cara not in ("north", "south"):
            return hex_(ORO["s"])
        if t.i == 0 or t.i == t.tw - 1:
            return hex_(ORO["b"])
        if t.i <= 2:
            return hex_(NEGRO["b"])
        return hex_(AZUL["l"] if t.j < 2 else AZUL["b"])
    for k, (ang, w) in enumerate(zip(angulos, anchos)):
        largo = 2.4
        p.caja("Body/cola", f"cola{k}", (x - w / 2, y, z - 0.45), (x + w / 2, y + largo + 0.3, z + 0.45), hoja,
               rot=(0, -30, ang), piv=(x, y, z), dens=2)
        r = math.radians(ang)
        x += -math.sin(r) * largo * 0.95
        y += math.cos(r) * largo * 0.95
    p.plano("Body/cola", "cola_punta", (x - 1.3, y - 0.3, z), (x + 1.3, y + 4.0, z), sprite({"todas": PUNTA_COLA}, PAL_COLA),
            rot=(0, -30, -14), piv=(x, y, z), dens=2)
    return p
