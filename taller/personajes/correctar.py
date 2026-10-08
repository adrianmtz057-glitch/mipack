"""
Correcthar, el dios libre ("自由な神"). Hecho a mano con el kit (boceto 1, segun referencias/personajes/correctar_nuevo.png).

Analisis de la referencia (capas, de adentro hacia afuera):
  BASE (player de 32 px, brazos finos de 3 px)
    - cabeza de piel con cara pintada: ojos amarillos cansados (parpado oscuro, ojeras), boca chiquita
    - torso de piel con abdominales, tatuajes negros (simbolo de engranaje en el pecho izquierdo, ramas de tinta)
      y el cordon negro del collar pintados; hombros desnudos con el mismo tatuaje en los brazos
  PELO (cubos sueltos): casco negro con reflejos cafes, flequillo de mechones finos que tapan los ojos a medias,
    picos desordenados girados por arriba, los costados y la nuca; mechones blancos y una cinta roja del lado
    izquierdo, mechones rojos atras, un broche blanco arriba
  ACCESORIOS 3D: aretes (argollas doradas y un talisman blanco colgando del lado izquierdo), moneda dorada del collar,
    anillos negros en las manos
  HAORI (capa de ropa): chaqueta negra con manchones blancos, abierta adelante y caida de los hombros; espalda con
    un kanji blanco grande; mangas anchas que cuelgan (con bolsa atras), bandas blancas abajo; tira amarilla en el
    borde izquierdo
  FAJA negra con nudo adelante; CINTAS como paneles finos: roja adelante y atras, amarilla en la cadera derecha,
    amarillas con talismanes blancos a los costados
  PANTALON hakama ancho en tres alturas (cadera, pierna abierta, puno doblado), con pliegues y manchas blancas
  ZAPATILLAS gruesas: suela blanca, capellada negra con paneles blancos, puntera blanca, correas amarillas con hebilla
"""

import math
import random

from ..kit import Objeto, Personaje, dibujo, sprite, tonos
from ..textura import hex_a_rgba as hex_

PIEL = tonos("#C8966E")
PELO, PELO2, PELO3 = "#171213", "#2C211E", "#0E0B0C"
NEGRO, NEGRO2 = "#151314", "#221E20"
BLANCO, GRIS = "#E9E5DF", "#B8B2AC"
AMARILLO = tonos("#E2B42A")
ROJO = tonos("#C0262A")
ORO = tonos("#C9A14A")

# ---------------------------------------------------------------- dibujos

CARA = dibujo("""
    pppppppppppppppp
    pppppppppppppppp
    pppppppppppppppp
    pppppppppppppppp
    pppppppppppppppp
    pppppppppppppppp
    pppppppppppppppp
    pkkkkkkppkkkkkkp
    ppWYYoWppWoYYWpp
    ppbYYobppboYYbpp
    pppbbbppppbbbppp
    pppppppssppppppp
    pppppppppppppppp
    ppppppmmmmpppppp
    pppppppppppppppp
    ssssssssssssssss
""")
PAL_CARA = {"p": PIEL["b"], "s": PIEL["s"], "k": "#24181A", "W": "#EDE6DC", "Y": "#E8C21E", "o": "#4A3410",
            "b": PIEL["s2"], "m": "#8A5A44"}

def _torso_dibujo():
    """Frente del torso a densidad 3 (24 x 36 texeles): cordon del collar, claviculas, pecho, abdominales,
    tatuaje de engranaje en el pecho izquierdo (lado derecho de la imagen), ramas de tinta y marcas."""
    W, H = 24, 36
    g = [["p"] * W for _ in range(H)]

    def pon(c, r, ch):
        if 0 <= r < H and 0 <= c < W:
            g[r][c] = ch
    for r in range(10):                                         # cordon en V hasta la moneda
        pon(5 + round(r * 0.7), r, "k")
        pon(18 - round(r * 0.7), r, "k")
    for c in list(range(2, 9)) + list(range(15, 22)):           # claviculas
        pon(c, 3 + (1 if c in (2, 21) else 0), "s")
    for c in list(range(2, 11)) + list(range(13, 22)):          # borde de abajo del pecho
        pon(c, 12, "s")
    for r in range(13, 31):                                     # linea del medio
        pon(11, r, "s")
        pon(12, r, "s")
    for r in (17, 22, 27):                                      # abdominales
        for c in list(range(5, 11)) + list(range(13, 19)):
            pon(c, r, "s")
    for r in range(18, 34):                                     # oblicuos
        pon(3 + (r - 18) // 6, r, "s")
        pon(20 - (r - 18) // 6, r, "s")
    pon(11, 31, "s"), pon(12, 31, "s")                           # ombligo
    engranaje = ("..kkkk..", ".k.kk.k.", "k.k..k.k", "kk.kk.kk", "kk.kk.kk", "k.k..k.k", ".k.kk.k.", "..kkkk..")
    for r, fila in enumerate(engranaje):
        for c, ch in enumerate(fila):
            if ch == "k":
                pon(14 + c, 7 + r, "k")
    for r in range(15, 19):                                     # tinta que chorrea
        if r % 2:
            pon(16, r, "k")
        pon(19, r - 1, "k")
    for c, r in ((1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (9, 4), (8, 5), (7, 6), (6, 7), (5, 9), (6, 10),
                 (4, 10), (3, 11), (8, 9)):                     # ramas de tinta en el pecho derecho
        pon(c, r, "k")
    for c, r in ((14, 20), (8, 24), (9, 25), (16, 29)):         # marcas sueltas
        pon(c, r, "k")
    for c in (6, 7, 8):                                         # cicatriz
        pon(c, 19, "c")
    return ["".join(f) for f in g]


TORSO = _torso_dibujo()
PAL_TORSO = {"p": PIEL["b"], "s": PIEL["s"], "k": "#181214", "c": "#E2B392"}

TATUAJE = dibujo("""
    .kkkk.
    k.kk.k
    kk..kk
    kk..kk
    k.kk.k
    .kkkk.
""")

KANJI = dibujo("""
    .......WW.......
    ..WWWWWWWWWWWW..
    ....W..WW..W....
    ...W.W.WW.W.W...
    ..W...WWWW...W..
    .....W....W.....
    ....WWWWWWWW....
    ......W..W......
    .....W....W.....
    ....WW....WW....
    ...W..W..W..W...
    ..W....WW....W..
    ......W..W......
    ....WW....WW....
""")

TALISMAN = dibujo("""
    wwwwww
    wwkkww
    wkkkkw
    wwkkww
    wkwwkw
    wkkkkw
    wwkkww
    wkwkww
    wkkkkw
    wwwkww
    wkwwkw
    wwwwww
""")

CARA_MASCARA = dibujo("""
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yykykyyyyykykyyy
    yyykyyyyyyykyyyy
    yykykyyyyykykyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yykyyyyyyyyykyyy
    yyykyyyyyyykyyyy
    yyyykkkkkkkyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
""")


# ---------------------------------------------------------------- pintores

def _h(*v):
    """Ruido fijo por celda (0..1)."""
    n = 0
    for x in v:
        n = (n * 73856093) ^ (int(x) * 19349663 + 83492791)
    return ((n ^ (n >> 13)) * 1274126177 & 0xFFFF) / 65535.0


def pelo(t):
    k = _h(t.i // 2, t.j // 2, len(t.nombre))
    if t.cara == "up":
        return hex_(PELO2 if k < 0.35 else PELO)
    if t.j % 5 == 0 and k < 0.5:
        return hex_(PELO3)                                     # hebras
    return hex_(PELO2 if k < 0.22 else (PELO3 if k > 0.85 else PELO))


def color(hexa):
    c = hex_(hexa)
    return lambda t: c


def manchas(blanco_abajo=None, base=NEGRO):
    """Tela negra con manchones blancos (pintura salpicada). blanco_abajo: altura bajo la cual hay banda blanca."""
    def p(t):
        x, y, z = t.x, t.y, t.z
        f = (0.5 + 0.5 * math.sin(x * 0.9 + y * 0.45 + z * 0.3)) * (0.5 + 0.5 * math.cos(z * 0.8 - y * 0.55 + x * 0.2))
        f += 0.35 * _h(x // 1, y // 1, z // 1) - 0.1
        if blanco_abajo is not None and y < blanco_abajo:
            f += 0.35
        if f > 0.62:
            return hex_(BLANCO)
        if f > 0.52:
            return hex_(GRIS)
        return hex_(NEGRO2 if _h(x * 2 // 1, y * 2 // 1, z * 2 // 1) < 0.2 else base)
    return p


_manchas_espalda = None


def espalda_haori(t):
    """Espalda del haori: arriba negro liso (ahi va el kanji), manchones blancos de la cintura para abajo."""
    global _manchas_espalda
    if _manchas_espalda is None:
        _manchas_espalda = manchas(blanco_abajo=12.0)
    if t.cara == "south" and t.y > 14.5:
        return hex_(NEGRO2 if _h(t.i // 3, t.j // 3) < 0.15 else NEGRO)
    return _manchas_espalda(t)


def pantalon(t):
    x, y, z = t.x, t.y, t.z
    if t.cara == "down":
        return hex_(NEGRO2)
    if t.cara in ("north", "south") and (abs(x) * 2) % 3 < 0.5:
        return hex_(NEGRO2)                                    # pliegues
    if y < 7.2:
        f = _h(x // 1, y // 1, z // 1)
        lado = x > 0                                           # mas manchas en la pierna derecha
        if (lado and f > 0.8) or (not lado and f > 0.92):
            return hex_(BLANCO if f > 0.88 else GRIS)
    return hex_(NEGRO if _h(x * 2 // 1, y * 2 // 1, z * 2 // 1) > 0.15 else NEGRO2)


def encima(base, capas):
    """Dibujos encima de otro pintor: capas = [(cara, i0, j0, filas, paleta)]."""
    capas = [(c, i0, j0, f, {k: hex_(v) for k, v in pal.items()}) for c, i0, j0, f, pal in capas]

    def p(t):
        for cara, i0, j0, filas, pal in capas:
            if t.cara == cara:
                r, c = t.j - j0, t.i - i0
                if 0 <= r < len(filas) and 0 <= c < len(filas[0]) and filas[r][c] != ".":
                    return pal[filas[r][c]]
        return base(t)
    return p


def piel(t):
    return hex_(PIEL["l"] if t.cara == "up" else PIEL["b"])


def cinta(c, marcas="#5A1010"):
    """Cinta de tela con marcas de escritura vertical."""
    def p(t):
        if t.cara in ("north", "south", "east", "west") and t.i % 3 == 1 and t.j % 4 in (1, 2) and \
                _h(t.j // 4, len(t.nombre)) < 0.6:
            return hex_(marcas)
        return hex_(c["b"] if t.cara != "down" else c["s"])
    return p


def oro(t):
    return hex_(ORO["l"] if t.cara == "up" else ORO["b"])


def suela(t):
    if t.cara in ("north", "south", "east", "west") and t.fila_abajo == 1:
        return hex_(NEGRO)                                     # raya negra de la suela
    return hex_(BLANCO if t.cara != "down" else GRIS)


def capellada(t):
    if t.cara == "up":
        return hex_(NEGRO2)
    if t.cara in ("east", "west") and (2 <= t.i <= 6 or t.i >= t.tw - 3) and t.j >= 1:
        return hex_(BLANCO)                                    # paneles blancos de los costados
    if t.cara == "north" and t.j >= t.th - 2:
        return hex_(BLANCO)
    return hex_(NEGRO)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("correctar", altura=32, cabeza=8, torso=(8, 12, 4), brazo=(3, 4))
    C, T = p.cuello, p.tope                                     # 24, 32
    rnd = random.Random(7)

    # ================================================================ CABEZA y cara
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), sprite({"north": CARA}, PAL_CARA, base=piel), dens=2)

    # ================================================================ PELO (mucho volumen, desordenado)
    g = "Head/pelo"
    p.caja(g, "techo", (-5.0, T - 0.8, -4.6), (5.0, T + 1.4, 5.2), pelo, dens=2)
    p.caja(g, "techo2", (-4.2, T + 1.4, -3.8), (4.4, T + 2.2, 4.4), pelo, dens=2)
    p.caja(g, "nuca", (-5.0, C + 0.8, 3.8), (5.0, T - 0.8, 5.4), pelo, dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 3.8, s * 5.2))
        p.caja(g, f"costado{s}", (x1, C + 1.4, -3.4), (x2, T - 0.8, 3.8), pelo, dens=2)
    p.caja(g, "frente", (-5.0, T - 2.0, -4.9), (5.0, T - 0.6, -3.9), pelo, dens=2)
    # flequillo en dos capas: mechones largos y desparejos que tapan los ojos a medias
    mechones = ((4.4, 1.2, 26.8, 10, -5.0), (3.4, 1.4, 28.6, 5, -5.3), (2.3, 1.1, 28.3, -3, -5.0),
                (1.2, 1.3, 28.9, 6, -5.35), (0.2, 1.1, 26.2, -5, -5.05), (-1.0, 1.4, 28.7, 4, -5.3),
                (-2.1, 1.1, 28.2, -6, -5.0), (-3.2, 1.4, 28.9, 3, -5.3), (-4.3, 1.2, 27.0, -10, -5.05))
    for k, (x, w, y0, giro, z) in enumerate(mechones):
        p.caja(g, f"mechon{k}", (x - w / 2, y0, z), (x + w / 2, T - 0.3, z + 0.6), pelo,
               rot=(-6, 0, giro), piv=(x, T - 0.3, z + 0.3), dens=2)
    # picos de arriba: salen hacia afuera segun donde nacen
    for k in range(18):
        x, z = rnd.uniform(-4.2, 4.2), rnd.uniform(-3.6, 4.6)
        h = rnd.uniform(1.8, 3.2)
        p.caja(g, f"pico_arriba{k}", (x - 0.5, T + 1.2, z - 0.5), (x + 0.5, T + 1.2 + h, z + 0.5), pelo,
               rot=(z * 8 - 12 + rnd.uniform(-8, 8), 0, -x * 10 + rnd.uniform(-8, 8)), piv=(x, T + 1.2, z), dens=2)
    # picos de los costados: hacia afuera y abajo (tapan las orejas)
    for s in (1, -1):
        for k in range(12):
            y, z = rnd.uniform(C + 1.2, T + 1.0), rnd.uniform(-3.4, 4.8)
            largo = rnd.uniform(2.6, 4.0)
            x = s * 5.0
            p.caja(g, f"pico_lado{s}_{k}", (x - 0.5, y - largo, z - 0.5), (x + 0.5, y, z + 0.5), pelo,
                   rot=(rnd.uniform(-8, 8), 0, s * rnd.uniform(30, 55)), piv=(x, y, z), dens=2)
    # picos de la nuca: hacia atras y abajo; algunos rojos a los costados
    for k in range(16):
        x, y = rnd.uniform(-4.6, 4.6), rnd.uniform(C + 0.6, T + 1.2)
        largo = rnd.uniform(2.6, 3.8)
        rojo = abs(x) > 2.6 and rnd.random() < 0.4
        p.caja(g, f"pico_nuca{k}", (x - 0.5, y - largo, 5.0), (x + 0.5, y, 6.0),
               color(ROJO["b"]) if rojo else pelo,
               rot=(-rnd.uniform(25, 40), 0, rnd.uniform(-12, 12)), piv=(x, y, 5.5), dens=2)
    # mechones blancos del lado izquierdo (-X) arriba, uno en el flequillo, cinta roja y broche blanco
    for k, (x, y, z, rx, rz) in enumerate(((-4.6, T + 1.6, -1.8, 0, 40), (-3.6, T + 2.2, -0.6, -10, 25),
                                            (-5.2, T + 0.2, 0.6, 0, 55), (-4.0, T + 0.8, 1.8, 15, 35))):
        p.caja(g, f"mechon_blanco{k}", (x - 0.6, y - 2.8, z - 0.6), (x + 0.6, y, z + 0.6),
               color(BLANCO if k % 2 == 0 else GRIS), rot=(rx, 0, rz), piv=(x, y, z), dens=2)
    p.caja(g, "flequillo_blanco", (-3.9, 27.6, -5.45), (-3.0, T - 0.3, -4.9), color(GRIS), rot=(-6, 0, -4),
           piv=(-3.45, T - 0.3, -5.2), dens=2)
    p.caja(g, "cinta_roja", (-5.9, T - 2.8, -2.0), (-5.0, T + 0.6, -0.6), color(ROJO["b"]), rot=(0, 0, 20),
           piv=(-5.45, T + 0.6, -1.3), dens=2)
    p.caja(g, "cinta_roja2", (-6.2, T - 0.6, -1.9), (-5.2, T + 0.6, -0.5), color(ROJO["l"]), dens=2)
    for k, giro in enumerate((32, -32)):
        p.caja(g, f"broche{k}", (-0.2, T + 2.2, -2.6), (1.8, T + 2.6, -2.2), color(BLANCO), rot=(0, 0, giro),
               piv=(0.8, T + 2.4, -2.4), dens=2)

    # ================================================================ ARETES
    g = "Head/aretes"
    p.caja(g, "argolla_izq", (-4.75, C + 2.2, -0.4), (-4.45, C + 3.0, 0.4), oro, dens=2)
    p.caja(g, "cadena_izq", (-4.95, C + 1.2, -0.1), (-4.75, C + 2.4, 0.1), oro, dens=2)
    p.caja(g, "talisman_izq", (-5.5, C - 1.2, -0.3), (-4.4, C + 1.3, -0.1),
           sprite({"todas": TALISMAN}, {"w": BLANCO, "k": "#141214"}), dens=3)
    p.caja(g, "arete_izq2", (-4.75, C + 3.4, -0.9), (-4.45, C + 3.8, -0.5), oro, dens=2)
    p.caja(g, "argolla_der", (4.45, C + 2.4, -0.4), (4.75, C + 3.2, 0.4), oro, dens=2)
    p.caja(g, "talisman_der", (4.5, C + 0.4, 0.1), (5.3, C + 2.2, 0.3), sprite({"todas": TALISMAN}, {"w": BLANCO, "k": "#141214"}),
           dens=3)

    # ================================================================ TORSO (piel con tatuajes y abdominales)
    p.caja("Body/torso", "torso", (-4, p.lh, -2), (4, C, 2), sprite({"north": TORSO}, PAL_TORSO, base=piel), dens=3)
    p.caja("Body/collar", "moneda", (-0.8, C - 4.0, -2.4), (0.8, C - 2.4, -2.05), oro, rot=(0, 0, 45),
           piv=(0, C - 3.2, -2.2), dens=3)
    p.caja("Body/collar", "moneda_centro", (-0.35, C - 3.55, -2.55), (0.35, C - 2.85, -2.35), color("#5A4416"), dens=3)

    # ================================================================ FAJA con nudo
    p.caja("Body/faja", "faja", (-4.35, p.lh - 0.6, -2.35), (4.35, p.lh + 1.4, 2.35), color(NEGRO2), dens=2)
    p.caja("Body/faja", "nudo", (0.0, p.lh - 0.8, -2.95), (1.8, p.lh + 1.2, -2.35), color(NEGRO), dens=2)

    # ================================================================ HAORI (chaqueta abierta, caida de los hombros)
    g = "Body/haori"
    kanji = encima(espalda_haori, [("south", 1, 4, KANJI, {"W": BLANCO})])
    p.caja(g, "espalda", (-4.5, 9.0, 2.05), (4.5, C + 0.2, 2.75), kanji, dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 2.5, s * 4.5))
        p.caja(g, f"frente{s}", (x1, 9.0, -2.75), (x2, 20.6, -2.05), manchas(blanco_abajo=12.0), dens=2)
        x1, x2 = sorted((s * 2.4, s * 3.2))
        p.caja(g, f"solapa{s}", (x1, 9.0, -2.95), (x2, 20.8, -2.05), color(NEGRO), dens=2)
        x1, x2 = sorted((s * 4.0, s * 4.6))
        p.caja(g, f"costado{s}", (x1, 9.0, -2.75), (x2, 20.0, 2.75), manchas(blanco_abajo=12.0), dens=2)
    p.caja(g, "tira_amarilla", (-3.6, 13.5, -3.15), (-2.8, C - 1.2, -2.9), cinta(AMARILLO, "#6A4A08"), dens=2)

    # ================================================================ BRAZOS (hombros desnudos con tatuaje) y MANGAS anchas
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 4.0, s * 7.0))
        cara_fuera = "east" if s > 0 else "west"
        p.caja(f"{hueso}/brazo", "brazo", (x1, p.lh, -2), (x2, C, 2),
               encima(piel, [(cara_fuera, 1, 1, TATUAJE, {"k": "#181214"})]), dens=2)
        for k, y in enumerate((12.7, 13.5)):                     # anillos
            p.caja(f"{hueso}/anillos", f"anillo{k}", (x1 - 0.12, y, -2.12), (x2 + 0.12, y + 0.4, 2.12),
                   lambda t: hex_(ORO["b"] if t.i % 4 == 1 else NEGRO), dens=2)
        x1, x2 = sorted((s * 3.7, s * 7.6))
        p.caja(f"{hueso}/manga", "manga", (x1, 14.4, -2.9), (x2, 20.6, 2.9), manchas(blanco_abajo=16.2), dens=2)
        x1, x2 = sorted((s * 3.8, s * 7.4))
        p.caja(f"{hueso}/manga", "manga_hombro", (x1, 20.6, 0.2), (x2, 23.4, 2.9), manchas(), dens=2)
        p.caja(f"{hueso}/manga", "manga_bolsa", (x1, 11.8, 0.4), (x2, 14.4, 2.9), manchas(blanco_abajo=14.0), dens=2)

    # ================================================================ CINTAS (paneles finos)
    g = "Body/cintas"
    p.caja(g, "roja_frente", (0.1, 4.8, -3.15), (1.7, 12.4, -2.95), cinta(ROJO), rot=(0, 0, -3), piv=(0.9, 12.4, -3.05),
           dens=2)
    p.caja(g, "amarilla_frente", (2.7, 5.8, -3.15), (3.9, 12.0, -2.95), cinta(AMARILLO, "#6A4A08"), rot=(0, 0, 6),
           piv=(3.3, 12.0, -3.05), dens=2)
    p.caja(g, "roja_espalda", (0.7, 6.4, 2.75), (2.1, 17.6, 2.95), cinta(ROJO), dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 4.8, s * 5.0))
        p.caja(g, f"amarilla_lado{s}", (x1, 5.4, -1.4), (x2, 12.0, 0.0), cinta(AMARILLO, "#6A4A08"), dens=2)
        p.caja(g, f"talisman_lado{s}", (x1, 3.0, -1.3), (x2, 5.6, -0.1),
               sprite({"todas": TALISMAN}, {"w": BLANCO, "k": "#141214"}), dens=3)

    # ================================================================ PANTALON hakama y ZAPATILLAS
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        def x(a, b):
            return sorted((s * a, s * b))
        a, b = x(0, 4)
        p.caja(f"{hueso}/pierna", "pierna", (a, 0, -2), (b, p.lh, 2), color(NEGRO))
        a, b = x(0.0, 4.5)
        p.caja(f"{hueso}/pantalon", "cadera", (a, 8.0, -2.6), (b, p.lh + 0.2, 2.6), pantalon, dens=2)
        a, b = x(0.0, 4.8)
        p.caja(f"{hueso}/pantalon", "pierna_ancha", (a, 5.2, -2.9), (b, 8.0, 2.9), pantalon, dens=2)
        a, b = x(0.1, 4.6)
        p.caja(f"{hueso}/pantalon", "puno", (a, 4.6, -2.7), (b, 5.4, 2.7), pantalon, dens=2)
        a, b = x(-0.6, 4.6)
        p.caja(f"{hueso}/zapatilla", "suela", (a, 0, -4.1), (b, 1.6, 2.8), suela, dens=2)
        a, b = x(-0.15, 4.15)
        p.caja(f"{hueso}/zapatilla", "capellada", (a, 1.6, -3.7), (b, 3.9, 2.5), capellada, dens=2)
        a, b = x(0.1, 3.9)
        p.caja(f"{hueso}/zapatilla", "puntera", (a, 1.6, -4.0), (b, 2.9, -2.8), color(BLANCO), dens=2)
        a, b = x(0.0, 4.0)
        p.caja(f"{hueso}/zapatilla", "cana", (a, 3.9, -1.9), (b, 5.3, 2.5), capellada, dens=2)
        a, b = x(1.2, 2.8)
        p.caja(f"{hueso}/zapatilla", "lengua", (a, 3.4, -2.6), (b, 5.6, -1.8), color(BLANCO), dens=2)
        a, b = x(-0.3, 4.3)
        p.caja(f"{hueso}/zapatilla", "correa", (a, 2.7, -3.85), (b, 3.25, -1.5), color(AMARILLO["b"]), dens=2)
        p.caja(f"{hueso}/zapatilla", "correa_tobillo", (a, 4.2, -2.05), (b, 4.75, 2.65), color(AMARILLO["b"]), dens=2)
        a, b = x(1.4, 2.6)
        p.caja(f"{hueso}/zapatilla", "hebilla", (a, 2.6, -4.05), (b, 3.35, -3.8), oro, dens=2)
        a, b = x(1.6, 2.4)
        p.caja(f"{hueso}/zapatilla", "tira_talon", (a, 1.8, 2.5), (b, 5.4, 2.8), color(AMARILLO["b"]), dens=2)
    return p


def accesorios():
    """La mascara amarilla de cubo (ojos en cruz y sonrisa), como modelo aparte."""
    o = Objeto("correctar_mascara")
    o.caja("cubo", (-4, 0, -4), (4, 8, 4), sprite({"north": CARA_MASCARA}, {"y": AMARILLO["b"], "k": "#161214"},
                                                   base=color(AMARILLO["b"])), dens=2)
    return [o]

