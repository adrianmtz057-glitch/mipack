"""
Correcthar, el dios libre ("自由な神"). Hecho a mano con el kit (boceto 3, segun referencias/personajes/correctar_nuevo.png).

Bases del pedido original: semidios cuyo poder es hacer cualquier cosa random; estilo unico, alocado, rebelde, sin
control y arriesgado; estilo japones; SIN MUCHOS DETALLES; pose neutra. Por eso: pocas piezas, bien marcadas.

Medidas: 2.5 bloques (40 px, 1.25 veces Steve). Alto y delgado por proporcion, no por tamano: cabeza de 8 px, torso
de 12 (7 de ancho), piernas de 20 (mas largas que el torso), brazos finos de 16.5 (las manos a media pierna).

Capas, de adentro hacia afuera:
  BASE: cara a densidad 3 (ojos amarillos cansados de anime); torso de piel con abdominales, el engranaje tatuado,
    unas ramas de tinta y el cordon del collar; hombros desnudos con el engranaje tatuado
  PELO en cascos con mechones recortados (adentro largo, afuera mas grande y desparejo) y mechones parados arriba;
    mechones blancos y cinta roja del lado izquierdo, mechones rojos atras
  ACCESORIOS 3D: arete con talisman (izquierda), moneda del collar, un anillo por mano
  HAORI de paneles 2D: abierto, caido de los hombros, dobladillo deshilachado, manchones blancos, kanji atras;
    mangas anchas de paneles con la bolsa del kimono
  FAJA con nudo; tres cintas (roja adelante y atras, amarilla con talisman al costado izquierdo); HAKAMA ancho;
  ZAPATILLAS gruesas con correa amarilla
"""

import math
import random

from ..kit import Objeto, Personaje, dibujo, sprite, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_

PIEL = tonos("#C8966E")
PELO = {"k": "#171213", "h": "#33251F", "d": "#0D0A0B", "w": "#E9E5DF", "g": "#A9A39D", "r": "#B8242A"}
NEGRO, NEGRO2 = "#151314", "#221E20"
BLANCO, GRIS = "#E9E5DF", "#B8B2AC"
AMARILLO = tonos("#E2B42A")
ROJO = tonos("#C0262A")
ORO = tonos("#C9A14A")

# ---------------------------------------------------------------- cara (24 x 24, densidad 3)

CARA = dibujo("""
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    ppkkkkkkkkppppkkkkkkkkpp
    pppkWYLoYWppppWYoLYWkppp
    ppppWYYoGWppppWGoYYWpppp
    pppppGGGbppppppbGGGppppp
    ppppbbbbbppppppbbbbbpppp
    pppppppppppssppppppppppp
    pppppppppppppppppppppppp
    ppppppppppmmmmpppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    ssssssssssssssssssssssss
""")
PAL_CARA = {"p": PIEL["b"], "s": PIEL["s"], "k": "#1E1416", "W": "#EDE6DC", "Y": "#F0C81E", "G": "#B88A12",
            "L": "#FFF0A0", "o": "#3A2808", "b": PIEL["s2"], "m": "#8A5A44"}

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
PAL_TALISMAN = {"w": BLANCO, "k": "#141214"}

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


def torso_dibujo(W, H):
    """Frente del torso: cordon del collar en V, claviculas, pecho, abdominales, oblicuos, el engranaje tatuado en
    el pecho izquierdo (derecha de la imagen) y unas ramas de tinta en el derecho."""
    g = [["p"] * W for _ in range(H)]
    m = W // 2

    def pon(c, r, ch):
        if 0 <= r < H and 0 <= c < W:
            g[r][c] = ch

    def fila(f):
        return round(f * H)
    for r in range(11):                                         # cordon en V hasta la moneda
        pon(round(m - 6 + r * 0.55), r, "k")
        pon(round(m + 5 - r * 0.55), r, "k")
    for c in list(range(1, m - 2)) + list(range(m + 2, W - 1)):  # claviculas
        pon(c, 3, "s")
    for c in list(range(1, m - 1)) + list(range(m + 1, W - 1)):  # borde de abajo del pecho
        pon(c, fila(0.36), "s")
    for r in range(fila(0.38), fila(0.86)):                     # linea del medio
        pon(m, r, "s")
    for f in (0.5, 0.63, 0.76):                                 # abdominales
        for c in list(range(m - 6, m - 1)) + list(range(m + 2, m + 7)):
            pon(c, fila(f), "s")
    for r in range(fila(0.5), fila(0.92)):                      # oblicuos
        pon(2 + (r - fila(0.5)) // 6, r, "s")
        pon(W - 3 - (r - fila(0.5)) // 6, r, "s")
    pon(m, fila(0.84), "d")                                     # ombligo
    engranaje = ("..kkkk..", ".k.kk.k.", "k.k..k.k", "kk.kk.kk", "kk.kk.kk", "k.k..k.k", ".k.kk.k.", "..kkkk..")
    for r, fil in enumerate(engranaje):
        for c, ch in enumerate(fil):
            if ch == "k":
                pon(m + 2 + c, 6 + r, "k")
    for r in range(14, 18):                                     # tinta que chorrea
        if r % 2:
            pon(m + 4, r, "k")
    for c, r in ((1, 5), (2, 6), (3, 7), (4, 8), (7, 5), (6, 6), (5, 9), (6, 10)):    # ramas de tinta
        pon(c, r, "k")
    return ["".join(f) for f in g]


def mechones(w, h, hebras, rnd, acentos=None):
    """Panel de pelo dibujado: hebras = [(columna, ancho, largo en filas)], con punta finita, reflejo cafe y
    huecos transparentes entre hebras. acentos: {indice de hebra: letra de color} (w blanco, g gris, r rojo)."""
    g = [["."] * w for _ in range(h)]
    for k, (c0, ancho, largo) in enumerate(hebras):
        letra = (acentos or {}).get(k, "k")
        for r in range(min(h, largo)):
            angosta = 1 if r >= largo - 2 else 0
            angosta += 1 if r == largo - 1 and ancho > 2 else 0
            for c in range(c0 + angosta, c0 + ancho - angosta):
                if 0 <= c < w:
                    ch = letra
                    if letra == "k":
                        if c == c0 + 1 and 1 <= r < largo - 3:
                            ch = "h"                           # reflejo cafe
                        elif rnd.random() < 0.08:
                            ch = "d"
                    g[r][c] = ch
    for r in range(min(2, h)):                                 # la raiz siempre tapada
        for c in range(w):
            if g[r][c] == ".":
                g[r][c] = "k"
    return ["".join(f) for f in g]


def hebras_parejas(w, largos, rnd, ancho_min=2, ancho_max=4, huecos=0.0):
    """Reparte hebras de lado a lado del panel con los largos dados (se repiten si faltan).
    largos se estira a lo ancho del panel: el primero queda en la columna 0 y el ultimo en la ultima."""
    out, c = [], 0
    while c < w:
        ancho = rnd.randint(ancho_min, ancho_max)
        k = min(len(largos) - 1, int(c / max(1, w) * len(largos)))
        largo = largos[k] + rnd.randint(-1, 1)
        if rnd.random() >= huecos:
            out.append((c, ancho, max(2, largo)))
        c += ancho - rnd.randint(0, 1)
    return out


def casco_pelo(caras, arriba=True):
    """Caja de pelo (casco) con un dibujo de mechones en cada costado: da volumen y se ve de todos lados.
    caras = {"north": filas, ...}; arriba: tapa de pelo arriba; abajo siempre abierto (ahi esta la cara)."""
    pal = {k: hex_(v) for k, v in PELO.items()}

    def p(t):
        if t.cara == "down" or (t.cara == "up" and not arriba):
            return TRANSPARENTE
        if t.cara == "up":
            return pelo(t)
        filas = caras[t.cara]
        r = min(len(filas) - 1, t.j * len(filas) // max(1, t.th))
        c = min(len(filas[0]) - 1, t.i * len(filas[0]) // max(1, t.tw))
        ch = filas[r][c]
        return TRANSPARENTE if ch == "." else pal[ch]
    return p


# ---------------------------------------------------------------- pintores

def _h(*v):
    """Ruido fijo por celda (0..1)."""
    n = 0
    for x in v:
        n = (n * 73856093) ^ (int(x) * 19349663 + 83492791)
    return ((n ^ (n >> 13)) * 1274126177 & 0xFFFF) / 65535.0


def color(hexa):
    c = hex_(hexa)
    return lambda t: c


def pelo(t):
    k = _h(t.i // 2, t.j // 2, len(t.nombre))
    if t.cara == "up":
        return hex_(PELO["h"] if k < 0.3 else PELO["k"])
    return hex_(PELO["h"] if k < 0.2 else (PELO["d"] if k > 0.85 else PELO["k"]))


def panel_pelo(filas_a, filas_b=None):
    """Pintor de un panel de pelo (plano): filas_a en una cara (north/east/up), filas_b en la otra."""
    pal = {k: hex_(v) for k, v in PELO.items()}
    filas_b = filas_b or filas_a

    def p(t):
        filas = filas_a if t.cara in ("north", "east", "up") else filas_b
        r = min(len(filas) - 1, t.j * len(filas) // max(1, t.th))
        c = min(len(filas[0]) - 1, t.i * len(filas[0]) // max(1, t.tw))
        ch = filas[r][c]
        return TRANSPARENTE if ch == "." else pal[ch]
    return p


def manchas(blanco_abajo=None, base=NEGRO, deshilachado=None, kanji=None, sesgo=0.0):
    """Tela negra con manchones blancos. deshilachado: (alto del dobladillo en px, semilla) recorta el borde de abajo.
    kanji: altura desde la que la tela queda negra lisa (ahi va el kanji de la espalda)."""
    def p(t):
        x, y, z = t.x, t.y, t.z
        if deshilachado and t.cara in ("north", "south", "east", "west"):
            alto, sem = deshilachado
            if t.fila_abajo < int(alto * 3 * _h(t.i // 2, sem)):
                return TRANSPARENTE
        if kanji is not None and t.cara in ("north", "south") and y > kanji:
            return hex_(NEGRO2 if _h(t.i // 3, t.j // 3) < 0.15 else NEGRO)
        f = (0.5 + 0.5 * math.sin(x * 0.9 + y * 0.35 + z * 0.3)) * (0.5 + 0.5 * math.cos(z * 0.8 - y * 0.45 + x * 0.2))
        f += 0.35 * _h(x // 1, y // 1, z // 1) - 0.1 + sesgo
        if blanco_abajo is not None and y < blanco_abajo:
            f += 0.35
        if f > 0.62:
            return hex_(BLANCO)
        if f > 0.52:
            return hex_(GRIS)
        return hex_(NEGRO2 if _h(x * 2 // 1, y * 2 // 1, z * 2 // 1) < 0.2 else base)
    return p


Y_MANCHAS_PANTALON = 10.0


def pantalon(t):
    x, y, z = t.x, t.y, t.z
    if t.cara == "down":
        return hex_(NEGRO2)
    if t.cara in ("north", "south") and (abs(x) * 2) % 3 < 0.45:
        return hex_(NEGRO2)                                    # pliegues
    if t.cara in ("east", "west") and (abs(z) * 2) % 3 < 0.45:
        return hex_(NEGRO2)
    if y < Y_MANCHAS_PANTALON:
        f = _h(x // 1, y // 1, z // 1)
        if (x > 0 and f > 0.8) or (x < 0 and f > 0.9):
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
    def p(t):
        if t.i % 3 == 1 and t.j % 4 in (1, 2) and _h(t.j // 4, len(t.nombre)) < 0.6:
            return hex_(marcas)
        return hex_(c["b"])
    return p


def oro(t):
    return hex_(ORO["l"] if t.cara == "up" else ORO["b"])


# ---------------------------------------------------------------- zapatillas, cubo por cubo

def zapatilla(p, g, x, s):
    """Zapatilla gruesa de calle armada con cubos sueltos (derecha; x() la refleja para la izquierda):
    suela blanca por tramos con acentos negros, puntera y talon blancos, capellada negra con paneles blancos,
    lengueta, cordones amarillos cruzados, correa amarilla con hebilla dorada, cuello negro con borde blanco,
    correa del tobillo y tirador amarillo atras."""
    def cubo(nombre, xa, xb, y1, y2, z1, z2, pintor, rot=None, piv=None):
        a, b = x(xa, xb)
        piv2 = None if piv is None else (s * piv[0], piv[1], piv[2])
        rot2 = None if rot is None else (rot[0], rot[1] * s, rot[2] * s)
        p.caja(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=3)

    blanco, gris, negro = color(BLANCO), color(GRIS), color(NEGRO)
    amarillo, negro2 = color(AMARILLO["b"]), color(NEGRO2)
    # suela: base gris, relleno blanco y tramos alrededor que sobresalen un poco
    cubo("suela_base", -0.5, 4.1, 0.0, 0.45, -4.1, 2.7, gris)
    cubo("suela", -0.35, 3.95, 0.45, 1.5, -3.95, 2.55, blanco)
    for k, (z1, z2) in enumerate(((-3.9, -2.8), (-2.7, -1.6), (-1.5, -0.4), (-0.3, 0.8), (0.9, 2.0), (2.1, 2.6))):
        pint = negro if k in (2, 4) else blanco
        cubo(f"suela_fuera{k}", 3.95, 4.15, 0.45, 1.55, z1, z2, pint)
        cubo(f"suela_dentro{k}", -0.55, -0.35, 0.45, 1.55, z1, z2, negro if k == 3 else blanco)
    for k, (x1, x2) in enumerate(((-0.4, 0.8), (0.9, 2.5), (2.6, 4.0))):
        cubo(f"suela_punta{k}", x1, x2, 0.45, 1.6, -4.15, -3.95, blanco)
        cubo(f"suela_talon{k}", x1, x2, 0.45, 1.5, 2.55, 2.75, negro if k == 1 else blanco)
    # capellada negra con paneles blancos a los costados, puntera y talon
    cubo("capellada", -0.2, 3.8, 1.5, 3.6, -3.4, 2.4, negro)
    for k, (z1, z2, y2) in enumerate(((-2.6, -1.5, 3.0), (-0.4, 0.9, 2.7))):
        cubo(f"panel_fuera{k}", 3.8, 3.95, 1.6, y2, z1, z2, blanco)
        cubo(f"panel_dentro{k}", -0.35, -0.2, 1.6, y2, z1, z2, blanco)
    cubo("puntera", 0.1, 3.5, 1.5, 2.6, -3.75, -3.0, blanco)
    cubo("puntera_raya", 0.4, 3.2, 2.6, 2.85, -3.6, -3.0, negro2)
    cubo("talon", 0.2, 3.4, 1.5, 3.4, 2.4, 2.8, blanco)
    # lengueta, cordones cruzados y correa con hebilla
    cubo("lengueta", 1.0, 2.6, 3.3, 5.8, -2.6, -1.6, blanco)
    for k, z in enumerate((-3.0, -2.3, -1.6, -0.9)):
        cubo(f"cordon{k}", 0.4, 3.2, 3.55, 3.85, z - 0.2, z + 0.2, amarillo, rot=(0, 14 if k % 2 else -14, 0),
             piv=(1.8, 3.7, z))
    cubo("correa", -0.35, 3.95, 2.4, 2.95, -2.2, -1.4, amarillo)
    cubo("hebilla", 3.9, 4.25, 2.3, 3.05, -2.15, -1.45, oro)
    cubo("hebilla_centro", 4.2, 4.3, 2.5, 2.85, -1.95, -1.65, negro)
    # cuello del tobillo con borde blanco, correa del tobillo y tirador de atras
    cubo("cuello", 0.0, 3.6, 3.6, 5.4, -1.6, 2.5, negro)
    cubo("cuello_borde", -0.05, 3.65, 5.2, 5.55, -1.65, 2.55, blanco)
    cubo("correa_tobillo", -0.15, 3.75, 4.2, 4.7, -1.75, 2.65, amarillo)
    cubo("tirador", 1.4, 2.2, 3.0, 5.9, 2.75, 3.0, amarillo)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("correctar", altura=40, cabeza=8, torso=(7, 12, 3.5), brazo=(2.8, 2.8), pierna=(3.5, 3.5))
    C, T, L = p.cuello, p.tope, p.lh                           # 32, 40, 20
    rnd = random.Random(11)

    # ================================================================ CABEZA y cara
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), sprite({"north": CARA}, PAL_CARA, base=piel), dens=3)

    # ================================================================ PELO en capas de paneles 2D
    g = "Head/pelo"
    p.caja(g, "casco_arriba", (-4.25, T - 0.3, -4.25), (4.25, T + 0.5, 4.25), pelo, dens=2)
    p.caja(g, "casco_nuca", (-4.25, C + 2.2, 3.75), (4.25, T - 0.3, 4.25), pelo, dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 3.75, s * 4.25))
        p.caja(g, f"casco_lado{s}", (x1, C + 3.6, -3.4), (x2, T - 0.3, 4.25), pelo, dens=2)
    p.caja(g, "casco_frente", (-4.25, T - 1.0, -4.25), (4.25, T - 0.3, -3.75), pelo, dens=2)

    def caras_casco(ancho, alto, fondo, largos, huecos=0.0, acentos=None, hacia_arriba=False):
        """Dibujos de mechones para los 4 costados de un casco. largos = {cara: [largos de izq a der]}
        (vistos desde afuera). acentos = {cara: {indice de hebra: letra}}."""
        out = {}
        for cara, ls in largos.items():
            w = math.ceil((ancho if cara in ("north", "south") else fondo) * 3)
            hh = math.ceil(alto * 3)
            filas = mechones(w, hh, hebras_parejas(w, ls, rnd, huecos=huecos), rnd, (acentos or {}).get(cara))
            out[cara] = filas[::-1] if hacia_arriba else filas
        return out

    # casco de adentro: flequillo (dos mechones cruzan los ojos), costados cortos adelante y largos atras, nuca larga
    ancho, alto, fondo = 9.0, 7.8, 9.0
    cas = caras_casco(ancho, alto, fondo, {
        "north": [14, 11, 9, 12, 17, 10, 9, 12, 17, 10, 11, 14],
        "south": [21, 24, 22, 24, 23, 24, 21, 23],
        "east": [24, 23, 22, 20, 18, 17, 16, 15, 14],              # la derecha vista de afuera empieza atras
        "west": [14, 15, 16, 17, 18, 20, 22, 23, 24]},             # la izquierda vista de afuera empieza adelante
        acentos={"west": {1: "w", 3: "g"}, "south": {0: "r", 7: "r"}})
    p.caja(g, "casco_pelo", (-ancho / 2, T + 0.8 - alto, -fondo / 2), (ancho / 2, T + 0.8, fondo / 2), casco_pelo(cas),
           dens=3)
    # casco de afuera, mas grande y desparejo: le da el volumen al peinado (adelante solo un flequillo corto)
    ancho, alto, fondo = 11.0, 7.0, 10.4
    cas = caras_casco(ancho, alto, fondo, {
        "north": [7, 5, 8, 4, 6, 8, 5, 7],
        "south": [14, 18, 12, 17, 15, 19, 13, 16],
        "east": [17, 16, 14, 13, 11, 9, 7],
        "west": [7, 9, 11, 13, 14, 16, 17]},
        huecos=0.18, acentos={"west": {0: "w", 2: "g", 4: "w"}, "south": {1: "r", 9: "r"}})
    p.caja(g, "casco_pelo2", (-ancho / 2, T + 1.5 - alto, -4.9), (ancho / 2, T + 1.5, 5.5), casco_pelo(cas), dens=3)
    # mechones parados arriba: casco chico con las puntas hacia arriba y sin tapa
    ancho, alto, fondo = 8.6, 2.4, 8.4
    cas = caras_casco(ancho, alto, fondo, {c: [4, 7, 3, 6, 7, 2, 5, 7, 4] for c in ("north", "south", "east", "west")},
                      huecos=0.15, hacia_arriba=True)
    p.caja(g, "copete", (-ancho / 2, T + 1.3, -3.9), (ancho / 2, T + 1.3 + alto, 4.5), casco_pelo(cas, arriba=False),
           dens=3)
    # mas mechones parados en el medio, girados 45 grados (asi arriba no queda una tapa plana)
    ancho, alto, fondo = 5.6, 2.8, 5.6
    cas = caras_casco(ancho, alto, fondo, {c: [5, 8, 4, 7, 8, 5] for c in ("north", "south", "east", "west")},
                      huecos=0.1, hacia_arriba=True)
    p.caja(g, "copete2", (-ancho / 2, T + 1.4, -2.6), (ancho / 2, T + 1.4 + alto, 3.0), casco_pelo(cas, arriba=False),
           rot=(0, 45, 0), piv=(0, T + 1.4, 0.2), dens=3)
    # algunos mechones sueltos que se escapan
    for k, (x, y, z, rx, rz, largo) in enumerate(((-5.2, T + 0.6, -1.0, 0, 55, 3.0), (5.4, T - 0.2, 1.2, 0, -60, 2.8),
                                                  (2.2, T + 3.2, -1.4, -20, -25, 2.4), (-1.6, T + 3.4, 2.0, 25, 20, 2.6),
                                                  (-4.6, T - 3.0, 3.6, -30, 40, 3.0), (4.4, T - 2.6, 4.2, -35, -40, 3.2))):
        p.caja(g, f"suelto{k}", (x - 0.45, y - largo, z - 0.45), (x + 0.45, y, z + 0.45), pelo,
               rot=(rx, 0, rz), piv=(x, y, z), dens=3)

    # cinta roja del lado izquierdo y broche blanco arriba
    p.caja(g, "cinta_roja", (-5.3, T - 2.8, -2.0), (-4.6, T + 0.4, -0.7), color(ROJO["b"]), rot=(0, 0, 18),
           piv=(-4.95, T + 0.4, -1.35), dens=2)
    p.caja(g, "cinta_roja2", (-5.7, T - 0.9, -1.9), (-4.7, T + 0.2, -0.6), color(ROJO["l"]), dens=2)

    # ================================================================ ARETE con talisman (izquierda)
    g = "Head/aretes"
    p.caja(g, "argolla", (-4.55, C + 2.4, -0.4), (-4.25, C + 3.2, 0.4), oro, dens=3)
    p.caja(g, "cadena", (-4.75, C + 1.4, -0.1), (-4.55, C + 2.6, 0.1), oro, dens=3)
    p.plano(g, "talisman", (-5.4, C - 1.2, -0.2), (-4.3, C + 1.5, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN), dens=3)

    # ================================================================ TORSO delgado
    torso = torso_dibujo(21, 36)
    pal_torso = {"p": PIEL["b"], "s": PIEL["s"], "k": "#181214", "d": PIEL["s2"]}
    p.caja("Body/torso", "torso", (-3.5, L, -1.75), (3.5, C, 1.75), sprite({"north": torso}, pal_torso, base=piel), dens=3)
    p.caja("Body/collar", "moneda", (-0.75, C - 4.3, -2.05), (0.75, C - 2.8, -1.75), oro, rot=(0, 0, 45),
           piv=(0, C - 3.55, -1.9), dens=3)
    p.caja("Body/collar", "moneda_centro", (-0.3, C - 3.85, -2.15), (0.3, C - 3.25, -2.0), color("#5A4416"), dens=3)

    # ================================================================ FAJA con nudo
    p.caja("Body/faja", "faja", (-3.9, L - 1.0, -2.15), (3.9, L + 1.2, 2.15), color(NEGRO2), dens=2)
    p.caja("Body/faja", "nudo", (-0.2, L - 1.3, -2.75), (1.8, L + 1.0, -2.15), color(NEGRO), dens=2)

    # ================================================================ HAORI de paneles 2D (abierto, caido de los hombros)
    g = "Body/haori"
    abajo = L - 5.0                                             # el haori llega a la cadera
    tela = manchas(blanco_abajo=L - 2, deshilachado=(1.0, 3))
    espalda = encima(manchas(blanco_abajo=L - 2, deshilachado=(1.0, 5), kanji=C - 8.5),
                     [("south", 3, 6, KANJI, {"W": BLANCO})])
    p.plano(g, "espalda", (-3.9, abajo, 2.25), (3.9, C + 0.4, 2.25), espalda, dens=3)
    for s in (1, -1):
        puesta = s > 0                                          # derecha puesta en el hombro, izquierda caida
        x1, x2 = sorted((s * 1.9, s * 3.9))
        p.plano(g, f"frente{s}", (x1, abajo, -2.25), (x2, C - 0.2 if puesta else C - 3.5, -2.25), tela, dens=3)
        x1, x2 = sorted((s * 1.7, s * 2.3))
        p.caja(g, f"solapa{s}", (x1, abajo + 0.4, -2.45), (x2, C if puesta else C - 3.1, -2.2), color(NEGRO), dens=2)
        x = s * 3.95
        p.plano(g, f"costado{s}", (x, abajo, -2.25), (x, C - 0.2 if puesta else C - 5.0, 2.25), tela, dens=3)

    # ================================================================ BRAZOS finos, hombros desnudos, MANGAS de paneles
    mano = C - 16.5                                             # punta de los dedos, a media pierna
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.5, s * 6.3))
        cara_fuera = "east" if s > 0 else "west"
        p.caja(f"{hueso}/brazo", "brazo", (x1, mano, -1.4), (x2, C, 1.4),
               encima(piel, [(cara_fuera, 2, 3, TATUAJE, {"k": "#181214"})]), dens=3)
        p.caja(f"{hueso}/anillo", "anillo", (x1 - 0.12, mano + 1.2, -1.52), (x2 + 0.12, mano + 1.6, 1.52),
               lambda t: hex_(ORO["b"] if t.i % 4 == 1 else NEGRO), dens=3)
        g = f"{hueso}/manga"
        xi, xo = s * 3.55, s * 8.0                               # tubo abierto de paneles
        bajo = mano + 3.5
        if s > 0:     # derecha: la chaqueta tapa el hombro; manga entera, mas negra, con bandas blancas abajo
            arriba = C + 0.3
            tela_m = manchas(blanco_abajo=bajo + 2.0, deshilachado=(1.0, 8), sesgo=-0.1)
        else:         # izquierda: caida del hombro (se ve el tatuaje); manga con manchones blancos grandes
            arriba = C - 4.0
            tela_m = manchas(blanco_abajo=bajo + 3.5, deshilachado=(1.0, 6), sesgo=0.14)
        x1, x2 = sorted((xi, xo))
        p.plano(g, "manga_frente", (x1, bajo, -2.8), (x2, arriba, -2.8), tela_m, dens=3)
        p.plano(g, "manga_atras", (x1, bajo - 2.2, 2.8), (x2, arriba, 2.8), tela_m, dens=3)    # la bolsa del kimono
        p.plano(g, "manga_fuera", (xo, bajo - 1.6, -2.8), (xo, arriba, 2.8), tela_m, dens=3)
        p.plano(g, "manga_dentro", (xi, bajo, -2.8), (xi, arriba, 2.8), tela_m, dens=3)
        p.plano(g, "manga_arriba", (x1, arriba, -2.8), (x2, arriba, 2.8), color(NEGRO), dens=2)

    # ================================================================ CINTAS: roja adelante y atras, amarilla con talisman
    g = "Body/cintas"
    p.plano(g, "roja_frente", (0.1, L - 8.0, -2.8), (1.6, L - 0.6, -2.8), cinta(ROJO), rot=(0, 0, -3),
            piv=(0.85, L - 0.6, -2.8), dens=3)
    p.plano(g, "roja_espalda", (0.6, abajo + 0.5, 2.45), (2.0, C - 6.6, 2.45), cinta(ROJO), dens=3)
    x = -4.5
    p.plano(g, "amarilla_lado", (x, L - 8.5, -1.4), (x, L - 1.0, -0.1), cinta(AMARILLO, "#6A4A08"),
            rot=(0, 0, -4), piv=(x, L - 1.0, -0.75), dens=3)
    p.plano(g, "talisman_lado", (x, L - 11.5, -1.3), (x, L - 8.3, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN),
            rot=(0, 0, -4), piv=(x, L - 1.0, -0.75), dens=3)

    # ================================================================ HAKAMA ancho y ZAPATILLAS gruesas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"

        def x(a, b):
            return sorted((s * a, s * b))
        a, b = x(0.1, 3.6)
        p.caja(f"{hueso}/pierna", "pierna", (a, 0, -1.75), (b, L, 1.75), color(NEGRO))
        for nombre, (xa, xb, y1, y2, d) in (("cadera", (0.0, 4.0, 16.5, L + 0.3, 2.5)),
                                            ("muslo", (0.0, 4.6, 11.5, 16.5, 2.9)),
                                            ("pierna_ancha", (-0.1, 5.1, 7.2, 11.5, 3.2)),
                                            ("puno", (0.1, 4.7, 6.1, 7.2, 2.9))):        # termina arriba de la zapatilla
            a, b = x(xa, xb)
            p.caja(f"{hueso}/pantalon", nombre, (a, y1, -d), (b, y2, d), pantalon, dens=2)
        g = f"{hueso}/zapatilla"
        zapatilla(p, g, x, s)
    return p


def accesorios():
    """La mascara amarilla de cubo (ojos en cruz y sonrisa), como modelo aparte."""
    o = Objeto("correctar_mascara")
    o.caja("cubo", (-4, 0, -4), (4, 8, 4), sprite({"north": CARA_MASCARA}, {"y": AMARILLO["b"], "k": "#161214"},
                                                   base=color(AMARILLO["b"])), dens=2)
    return [o]
