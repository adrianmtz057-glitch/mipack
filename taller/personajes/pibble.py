"""
Pibble, el semidios errante. Hecho a mano con el kit (boceto 7).

  - capucha nueva low-poly (taller/personajes/pibble_capucha.py): ovalo acostado armado panel a panel, forro
    negro, agujero ovalado de la cara con filete dorado, cubo de la cabeza adentro y orejas de gato en cono con
    paneles; abajo abierta, conectada al cuerpo por el cuello
  - aro dorado con gema azul al costado izquierdo de la capucha y colgantes en rombo
  - CUERPO PROVISORIO (el del boceto 6, se rehace de cero): bufanda negra, estola azul con runa dorada,
    paneles crema largos en A, mangas negras con hombreras crema, botas con bandas doradas, cola en hoja
"""

from . import pibble_capucha
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

# estola: azul con filete dorado y una runa en S, termina en punta
ESTOLA = dibujo("""
    kaaaaak
    kaaaaak
    kGaaaGk
    kGaaaGk
    kGaaaGk
    kGaaaGk
    kGaaaGk
    kGaGGGk
    kGaGaGk
    kGGGaGk
    kGaaaGk
    kGaGGGk
    kGaGaak
    kGaGGGk
    kGaaaGk
    kGGGaGk
    kGaGaGk
    kGaGGGk
    kGaaaGk
    kGaaaGk
    kGaaaGk
    kGaaaGk
    kGaaaGk
    .kGaGk.
    .kGaGk.
    ..kak..
    ..kak..
    ...k...
""")
PAL_ESTOLA = {"G": ORO["b"], "a": AZUL["b"], "k": NEGRO["b"]}

EMBLEMA = dibujo("""
    ...G...
    ..GaG..
    .GaGaG.
    GaGaGaG
    .GaGaG.
    ..GaG..
    ...G...
""")

RUNA2 = dibujo("""
    ..a..
    .aGa.
    aG.Ga
    .aGa.
    ..a..
""")
PAL_RUNA = {"G": ORO["b"], "a": AZUL["b"]}


# ---------------------------------------------------------------- pintores

def hex_(c):
    return hex_a_rgba(c)


def _moteado(t, claro, oscuro, semilla=0):
    """Manchas suaves de 2x2 texeles: el voxel no es plano, cada bloquecito tiene su tono."""
    h = ((t.i // 2) * 73856093 ^ (t.j // 2) * 19349663 ^ (semilla + 7) * 83492791) & 0xFFFF
    return claro if h % 7 else oscuro


def con_runas(base, runas):
    """Pinta dibujos chicos encima de otro pintor. runas = [(cara, i0, j0, filas, paleta), ...]."""
    runas = [(c, i0, j0, f, {k: hex_(v) for k, v in pal.items()}) for c, i0, j0, f, pal in runas]

    def p(t):
        for cara, i0, j0, filas, pal in runas:
            if t.cara == cara:
                r, c = t.j - j0, t.i - i0
                if 0 <= r < len(filas) and 0 <= c < len(filas[0]) and filas[r][c] != ".":
                    return pal[filas[r][c]]
        return base(t)
    return p


def crema(diag=None, prof=0, picos_=None, semilla=0, oro=True):
    """Panel crema con borde inferior dorado + azul. diag='izq'/'der': ese lado queda mas corto."""
    def p(t):
        if t.cara == "up":
            return hex_(CREMA["l"])
        if t.cara == "down":
            return hex_(AZUL["s"])
        corte = 0
        if diag:
            f = t.i / max(1, t.tw - 1)
            corte = round((f if diag == "izq" else 1 - f) * prof)
        elif picos_:
            corte = picos_[(t.i + semilla) % len(picos_)]
        if t.fila_abajo < corte:
            return TRANSPARENTE
        if oro and t.fila_abajo <= corte + 1:
            return hex_(AZUL["b"])
        if oro and t.fila_abajo == corte + 2:
            return hex_(ORO["b"])
        k = t.j / max(1, t.th - 1)
        return hex_(_moteado(t, CREMA["l"] if k < 0.08 else (CREMA["b"] if k < 0.8 else CREMA["s"]), "#CFC5B3",
                             semilla))
    return p


def negro(picos_=None, pliegues=False, semilla=0):
    def p(t):
        if t.cara == "up":
            return hex_(NEGRO["l"])
        if t.cara == "down":
            return hex_(NEGRO["s"])
        if picos_ and t.fila_abajo < picos_[(t.i + semilla) % len(picos_)]:
            return TRANSPARENTE
        if pliegues:
            return hex_(NEGRO["s"] if t.fila_abajo % 4 == 0 else NEGRO["b"])
        k = t.j / max(1, t.th - 1)
        return hex_(_moteado(t, NEGRO["l"] if k < 0.08 else (NEGRO["b"] if k < 0.85 else NEGRO["s"]), "#2A2430",
                             semilla))
    return p


def cana(t):
    """Bota: negra con banda dorada arriba y suela tostada."""
    if t.cara == "up":
        return hex_(NEGRO["l"])
    if t.cara == "down" or t.fila_abajo == 0:
        return hex_(TOSTADO["s"])
    if t.j <= 1:
        return hex_(ORO["l"] if t.j == 0 else ORO["b"])
    return hex_(NEGRO["b"] if t.j > 2 else NEGRO["s"])


def puntera(t):
    """Puntera dorada (como un casquillo) sobre la suela."""
    if t.cara == "down" or (t.cara != "up" and t.fila_abajo == 0):
        return hex_(TOSTADO["s"])
    if t.cara == "up":
        return hex_(ORO["l"])
    return hex_(ORO["b"] if t.cara == "north" else ORO["s"])


def rombo(p, grupo, nombre, x, y, z, tam, cadena=0.0):
    """Colgante: rombo dorado (cubo a 45 grados) con punta y cadena."""
    oro = metal(ORO["b"], 7)
    p.caja(grupo, nombre, (x - tam / 2, y - tam / 2, z - 0.3), (x + tam / 2, y + tam / 2, z + 0.3), oro,
           rot=(0, 0, 45), piv=(x, y, z))
    p.caja(grupo, nombre + "_punta", (x - 0.25, y - tam * 1.3, z - 0.25), (x + 0.25, y - tam * 0.4, z + 0.25), oro)
    if cadena:
        p.caja(grupo, nombre + "_cadena", (x - 0.15, y + tam * 0.6, z - 0.15), (x + 0.15, y + tam * 0.6 + cadena, z + 0.15),
               oro)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("pibble", altura=27, cabeza=10, torso=(8, 11, 5), brazo=(4, 5))
    C = p.cuello                                         # cuello 17

    # ================================================================ CAPUCHA nueva (cabeza y orejas incluidas)
    pibble_capucha.poner(p)

    # aro dorado con gema azul al costado izquierdo de la capucha, con dos rombos colgando; colgante chico a la derecha
    p.plano("Head/joyas", "aro", (-8.45, 20.0, -4.6), (-8.45, 25.0, 0.4), sprite({"todas": ARO}, PAL_ARO), dens=2)
    rombo(p, "Head/joyas", "colgante_aro", -8.55, 18.4, -3.0, 1.0, cadena=0.6)
    rombo(p, "Head/joyas", "colgante_aro2", -8.55, 15.9, -3.0, 1.4, cadena=0.8)
    rombo(p, "Head/joyas", "colgante_der", 8.45, 19.4, -3.0, 1.2, cadena=1.0)

    # ================================================================ BUFANDA negra gruesa (tapa la boca)
    p.caja("Body/bufanda", "bufanda_cuello", (-5.0, C - 2.4, -4.6), (5.0, C + 0.2, 3.6), negro(pliegues=True, semilla=2),
           dens=2)
    p.caja("Body/bufanda", "bufanda_caida", (-2.4, C - 4.6, -4.2), (2.4, C - 2.4, -3.2), negro(semilla=3), dens=2)
    p.caja("Body/bufanda", "bufanda_punta", (-1.6, C - 6.2, -4.1), (1.6, C - 3.0, -3.3), negro(semilla=4),
           rot=(0, 0, 45), piv=(0, C - 4.6, -3.7), dens=2)

    # ================================================================ TUNICA
    p.caja("Body/tunica", "nucleo", (-4.2, 3.0, -2.6), (4.2, C, 2.6), negro(picos_=[0, 1, 2, 1]), dens=2)
    for z, nombre in ((-2.8, "estola"), (2.8, "estola_atras")):
        p.plano("Body/tunica", nombre, (-1.8, 2.2, z), (1.8, C - 0.8, z), sprite({"todas": ESTOLA}, PAL_ESTOLA), dens=2)
    # paneles crema largos que se abren en A, la punta larga hacia afuera
    for s in (1, -1):
        x1, x2 = sorted((s * 1.8, s * 4.9))
        diag = "izq" if s > 0 else "der"
        p.caja("Body/capa", f"panel{s}", (x1, 2.0, -3.3), (x2, C - 0.2, -2.7),
               con_runas(crema(diag=diag, prof=5, semilla=10 + s), [("north", 1, 20, RUNA2, PAL_RUNA)]),
               rot=(0, 0, 5 * s), piv=(s * 3.3, C - 0.2, -3.0), dens=2)
        p.caja("Body/capa", f"panel_atras{s}", (x1, 2.0, 2.7), (x2, C - 0.2, 3.3),
               crema(diag="der" if s > 0 else "izq", prof=5, semilla=12 + s),
               rot=(0, 0, 5 * s), piv=(s * 3.3, C - 0.2, 3.0), dens=2)
        x1, x2 = sorted((s * 4.25, s * 4.9))
        p.caja("Body/capa", f"panel_lado{s}", (x1, 2.6, -2.6), (x2, C - 3.0, 2.6),
               crema(picos_=[0, 1, 2, 3, 2, 1], semilla=14 + s), rot=(0, 0, 5 * s), piv=(s * 4.6, C - 0.2, 0), dens=2)

    # ================================================================ MANGAS cubicas con hombrera crema
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        rot, piv = (0, 0, 4 * s), (s * 6.8, C, 0)
        x1, x2 = sorted((s * 4.9, s * 8.7))
        p.caja(f"{hueso}/manga", "manga", (x1, 8.0, -2.3), (x2, C - 0.4, 2.3), negro(semilla=5 + s), rot, piv, dens=2)
        x1, x2 = sorted((s * 4.6, s * 9.0))
        p.caja(f"{hueso}/manga", "puno", (x1, 6.4, -2.6), (x2, 8.0, 2.6), negro(pliegues=True, semilla=6 + s), rot, piv,
               dens=2)
        cara_fuera = "east" if s > 0 else "west"
        p.caja(f"{hueso}/manga", "hombrera", (x1, C - 3.6, -2.6), (x2, C + 0.2, 2.6),
               con_runas(crema(picos_=[0, 1, 2, 1], semilla=7 + s), [(cara_fuera, 2, 0, EMBLEMA, PAL_RUNA)]),
               rot, piv, dens=2)

    # ================================================================ PIERNAS y botas con bandas doradas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.3, s * 3.9))
        p.caja(f"{hueso}/pantalon", "pantalon", (x1, 3.2, -2.2), (x2, 7.0, 2.2), negro(semilla=8 + s), dens=2)
        x1, x2 = sorted((s * 0.2, s * 4.0))
        p.caja(f"{hueso}/bota", "bota", (x1, 0, -2.4), (x2, 3.6, 2.4), cana, dens=2)
        x1, x2 = sorted((s * 0.4, s * 3.8))
        p.caja(f"{hueso}/bota", "puntera", (x1, 0, -3.8), (x2, 1.8, -2.4), puntera, dens=2)

    # ================================================================ COLA: hoja de rombo escalonada
    bx, by, bz = -6.0, 1.6, 3.4                       # sale baja por detras y sube hacia afuera
    tramos = ((-3.0, 2.5, 0.9), (2.5, 4.5, 2.0), (4.5, 9.0, 3.0), (9.0, 11.5, 2.0), (11.5, 13.5, 1.1), (13.5, 15.0, 0.4))

    def medio_ancho(ly):
        return next((w for a, b, w in tramos if a <= ly < b), 0.4)

    def hoja(t):
        lx, ly = t.x - bx, t.y - by
        if t.cara == "up":
            return hex_(CREMA["l"])
        if t.cara == "down":
            return hex_(CREMA["s"])
        if t.cara in ("east", "west"):
            return hex_(CREMA["b"])
        if ly < 2.5:
            return hex_(NEGRO["b"])
        dx = medio_ancho(ly) - abs(lx)
        if dx < 0.5:
            return hex_(CREMA["b"])
        if dx < 1.0:
            return hex_(ORO["b"])
        if abs(lx) < 0.5 or (ly - abs(lx)) % 2.5 < 0.5:
            return hex_(ORO["s"])                                   # nervio y espinas doradas
        return hex_(AZUL["b"] if ly < 9 else AZUL["l"])

    for k, (a, b, w) in enumerate(tramos):
        p.caja("Body/cola", f"cola{k}", (bx - w, by + a, bz - 0.7), (bx + w, by + b, bz + 0.7), hoja,
               rot=(10, -20, 50), piv=(bx, by, bz), dens=2)
    return p
