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

from .. import malla as geo
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
                pon(m + 2 + c, 3 + r, "k")
    for r in range(11, 15):                                     # tinta que chorrea
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


Y_MANCHAS_PANTALON = 11.0


def pantalon(t):
    """Hakama negro liso con pliegues verticales y pocas salpicaduras blancas abajo (distinto del haori)."""
    x, y, z = t.x, t.y, t.z
    if t.cara in ("down", "up"):
        return hex_(NEGRO2)
    pliegue = (abs(x) if abs(t.n[2]) > 0.5 else abs(z)) * 1.6
    if pliegue % 2 < 0.28:
        return hex_("#0C0A0B")
    if y < Y_MANCHAS_PANTALON:
        f = 0.6 * (0.5 + 0.5 * math.sin(x * 1.7 + y * 1.1)) * (0.5 + 0.5 * math.cos(z * 1.3 - y * 0.9)) \
            + 0.4 * _h(x * 1.5 // 1, y * 1.5 // 1, z * 1.5 // 1)
        if f > (0.66 if x > 0 else 0.76):
            return hex_(BLANCO if f > 0.74 else GRIS)
    return hex_(NEGRO)


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


# ---------------------------------------------------------------- piezas de malla

def tubo_hueco(abajo, arriba, grosor=0.15, tapa=True):
    """Tubo de 4 lados abierto abajo: cara de afuera y forro corrido hacia adentro (se ve por la abertura).
    Anillos de 4 puntos antihorarios vistos desde arriba. Devuelve (malla, cantidad de caras de afuera)."""
    afuera = geo.tronco(abajo, arriba, tapa_abajo=False, tapa_arriba=tapa)

    def encoger(r):
        cx, cz = sum(q[0] for q in r) / len(r), sum(q[2] for q in r) / len(r)
        out = []
        for x, y, z in r:
            d = math.hypot(x - cx, z - cz) or 1.0
            out.append((x - (x - cx) / d * grosor, y, z - (z - cz) / d * grosor))
        return out
    vs, cs = geo.tronco(encoger(abajo), encoger(arriba), tapa_abajo=False, tapa_arriba=False)
    return geo.unir(afuera, (vs, [tuple(reversed(c)) for c in cs])), len(afuera[1])


def haori(C, abajo, tela, espalda):
    """Cuerpo del haori como chaqueta aparte: espalda, costados y dos delanteros que se ABREN hacia la cadera (pasan
    por encima del pantalon y marcan el dobladillo). Abierto adelante; derecha puesta en el hombro, izquierda caida.
    Cada panel tiene forro corrido hacia adentro. Devuelve (malla, pintores)."""
    m = geo.Armador()
    pint = []
    afuera_de = (0.0, 0.0, 0.0)

    def panel(pts, pintor, solo_afuera=False):
        idx = [m.v(q) for q in pts]
        cx = sum(q[0] for q in pts) / 4
        cz = sum(q[2] for q in pts) / 4
        m.cara(tuple(idx), (cx - afuera_de[0], 0, cz - afuera_de[2]), "fuera")
        pint.append(pintor)
        if solo_afuera:
            return
        hacia = [(q[0] - 0.12 * (cx - afuera_de[0]) / max(0.01, math.hypot(cx, cz)), q[1],
                  q[2] - 0.12 * (cz - afuera_de[2]) / max(0.01, math.hypot(cx, cz))) for q in pts]
        idx2 = [m.v(q) for q in hacia]
        m.cara(tuple(idx2), (-(cx - afuera_de[0]), 0, -(cz - afuera_de[2])), "forro")
        pint.append(color(NEGRO2))
    zt_f, zt_b, zb_f, zb_b = -2.15, 2.2, -3.05, 3.1               # arriba ajustado, abajo abierto
    xt, xb = 3.85, 4.95
    sup_d, sup_i = C - 0.2, C - 3.5                               # delantero derecho puesto, izquierdo caido
    lado_d, lado_i = C - 0.2, C - 5.0
    panel([(-3.8, C + 0.4, zt_b), (3.8, C + 0.4, zt_b), (xb, abajo, zb_b), (-xb, abajo, zb_b)], espalda)
    panel([(xt, lado_d, zt_b), (xt, lado_d, zt_f), (xb, abajo, zb_f), (xb, abajo, zb_b)], tela)
    panel([(-xt, lado_i, zt_f), (-xt, lado_i, zt_b), (-xb, abajo, zb_b), (-xb, abajo, zb_f)], tela)
    panel([(1.9, sup_d, zt_f), (xt, sup_d, zt_f), (xb, abajo, zb_f), (2.4, abajo, zb_f)], tela)
    panel([(-xt, sup_i, zt_f), (-1.9, sup_i, zt_f), (-2.4, abajo, zb_f), (-xb, abajo, zb_f)], tela)
    # solapas negras a lo largo de la abertura (un poco adelante del delantero)
    for s, sup in ((1, sup_d), (-1, sup_i)):
        pts = [(s * 1.65, sup + 0.3, zt_f - 0.1), (s * 2.35, sup + 0.3, zt_f - 0.1),
               (s * 2.85, abajo + 0.3, zb_f - 0.1), (s * 2.15, abajo + 0.3, zb_f - 0.1)]
        if s < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        idx = [m.v((q[0], q[1], q[2])) for q in pts]
        m.cara(tuple(idx), (0, 0, -1), "solapa")
        pint.append(color(NEGRO))
    return (m.vs, m.caras), pint


def manga_kimono(arriba, mano):
    """Manga ancha de kimono (lado derecho): trapecio que se abre hacia afuera y hacia abajo; adelante termina en la
    muneca (la mano sale por ahi) y atras cuelga mas, como la bolsa del kimono."""
    xi, xo_arriba, xo_abajo = 3.55, 6.7, 9.0
    puno, bolsa = mano + 2.6, mano - 1.2
    sup = [(xo_arriba, arriba, 1.7), (xo_arriba, arriba, -1.7), (xi, arriba, -1.7), (xi, arriba, 1.7)]
    inf = [(xo_abajo, bolsa, 3.3), (xo_abajo, puno, -2.9), (xi + 0.05, puno, -2.9), (xi + 0.05, bolsa, 3.3)]
    return tubo_hueco(inf, sup)


# ---------------------------------------------------------------- zapatillas, cubo por cubo

def suela_manchada(t):
    """Plataforma blanca con manchas negras irregulares (como la referencia)."""
    if t.cara == "down":
        return hex_(GRIS)
    f = _h(t.x * 1.4 // 1, t.y * 1.4 // 1, t.z * 1.4 // 1) * 0.6 + 0.4 * (0.5 + 0.5 * math.sin(t.z * 1.3 + t.x * 0.7))
    return hex_(NEGRO if f > 0.68 and t.cara != "up" else (BLANCO if t.cara != "up" else "#F4F1EC"))


def capellada(t):
    """Capellada negra con un panel blanco a cada costado."""
    if abs(t.n[0]) > 0.7 and -2.6 < t.z < 0.8 and 1.8 < t.y < 2.9 + 0.35 * (t.z + 2.6):
        return hex_(BLANCO)
    return hex_(NEGRO2 if t.cara == "up" else NEGRO)


def zapatilla(p, g, x, s):
    """Zapatilla de calle GORDA y baja, con la geometria del dibujo: plataforma con escalon (hueco en el arco),
    punta larga y baja, capellada que sube en rampa hasta el tobillo (perfil extruido), puntera y talonera blancas,
    cordones amarillos sobre la rampa, y arriba un PUNO del tobillo mas angosto con dos correas y hebilla."""
    def cubo(nombre, xa, xb, y1, y2, z1, z2, pintor, rot=None, piv=None):
        a, b = x(xa, xb)
        piv2 = None if piv is None else (s * piv[0], piv[1], piv[2])
        rot2 = None if rot is None else (rot[0], rot[1] * s, rot[2] * s)
        if abs(a - b) < 1e-6:
            p.plano(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=3)
        else:
            p.caja(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=3)

    blanco, negro, amarillo = color(BLANCO), color(NEGRO), color(AMARILLO["b"])
    # plataforma ancha con escalon abajo (hueco en el arco) y bordes redondeados con dos cajas cruzadas
    cubo("suela_baja_frente", 0.35, 4.45, 0.0, 0.55, -4.4, -1.1, suela_manchada)
    cubo("suela_baja_atras", 0.35, 4.45, 0.0, 0.55, 0.7, 2.6, suela_manchada)
    cubo("suela_arco", 0.6, 4.2, 0.3, 0.55, -1.1, 0.7, color(GRIS))
    cubo("suela_ancha", 0.0, 4.8, 0.55, 1.6, -4.0, 2.3, suela_manchada)
    cubo("suela_larga", 0.35, 4.45, 0.55, 1.6, -4.5, 2.7, suela_manchada)
    # capellada: perfil de costado (punta baja, rampa, tobillo) extruido a lo ancho
    perfil = [(-4.3, 1.6), (-4.2, 2.35), (-3.5, 2.75), (-1.0, 3.55), (-0.75, 3.9), (2.45, 3.9), (2.6, 1.6)]
    malla = geo.extruir_x(perfil, 0.35, 4.3)
    p.malla(g, "capellada", malla if s > 0 else geo.espejo_x(malla), capellada, dens=3)
    cubo("puntera", 0.6, 4.1, 1.6, 2.25, -4.45, -3.75, blanco)
    cubo("talonera", 0.6, 4.0, 1.6, 3.4, 2.5, 2.75, blanco)
    rampa = dict(rot=(-17.7, 0, 0), piv=(2.3, 3.55, -1.0))
    cubo("cordon", 1.6, 3.0, 3.55, 3.67, -3.5, -1.0, amarillo, **rampa)
    for k, zc in enumerate((-2.9, -1.9)):
        cubo(f"cordon_cruce{k}", 1.0, 3.6, 3.55, 3.65, zc - 0.18, zc + 0.18, amarillo, **rampa)
    # puno del tobillo, mas angosto, con dos correas, hebilla amarilla y lengueta
    cubo("puno", -0.1, 3.8, 3.6, 5.2, -1.95, 2.3, negro)                  # rodea la pierna (que mide +-1.75)
    cubo("correa1", -0.2, 3.9, 3.85, 4.25, -2.05, 2.4, color("#D8D4CE"))
    cubo("correa2", -0.2, 3.9, 4.5, 4.95, -2.05, 2.4, negro)
    cubo("hebilla", 1.3, 2.4, 4.4, 5.05, -2.27, -2.03, amarillo)
    cubo("hebilla_perno", 1.7, 2.0, 4.6, 4.85, -2.34, -2.25, oro)
    cubo("lengueta", 1.1, 2.6, 3.5, 4.4, -2.15, -1.9, negro)
    cubo("lengueta_punta", 1.1, 2.6, 5.0, 5.6, -2.15, -1.9, blanco)
    cubo("tira_colgando", 3.95, 3.95, 3.0, 4.5, -1.3, -0.7, amarillo, rot=(0, 0, -8), piv=(3.95, 4.5, -1.0))


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("correctar", altura=40, cabeza=8, torso=(7, 10, 3.5), brazo=(2.8, 2.8), pierna=(3.5, 3.5))
    C, T, L = p.cuello, p.tope, p.lh                           # 32, 40, 22: cintura alta y piernas largas
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
    torso = torso_dibujo(21, 30)
    pal_torso = {"p": PIEL["b"], "s": PIEL["s"], "k": "#181214", "d": PIEL["s2"]}
    p.caja("Body/torso", "torso", (-3.5, L, -1.75), (3.5, C, 1.75), sprite({"north": torso}, pal_torso, base=piel), dens=3)
    p.caja("Body/collar", "moneda", (-0.75, C - 4.3, -2.05), (0.75, C - 2.8, -1.75), oro, rot=(0, 0, 45),
           piv=(0, C - 3.55, -1.9), dens=3)
    p.caja("Body/collar", "moneda_centro", (-0.3, C - 3.85, -2.15), (0.3, C - 3.25, -2.0), color("#5A4416"), dens=3)

    # ================================================================ FAJA con nudo
    p.caja("Body/faja", "faja", (-3.9, L - 1.0, -2.15), (3.9, L + 1.2, 2.15), color(NEGRO2), dens=2)
    p.caja("Body/faja", "nudo", (-0.2, L - 1.3, -2.75), (1.8, L + 1.0, -2.15), color(NEGRO), dens=2)

    # ================================================================ HAORI: chaqueta aparte que se abre en la cadera
    g = "Body/haori"
    abajo = L - 5.4                                             # el haori llega a la cadera
    tela = manchas(blanco_abajo=L - 2, deshilachado=(1.0, 3))
    espalda = encima(manchas(blanco_abajo=L - 2, deshilachado=(1.0, 5), kanji=C - 8.5),
                     [("south", 3, 6, KANJI, {"W": BLANCO})])
    malla, pintores = haori(C, abajo, tela, espalda)
    p.malla(g, "haori", malla, pintores, dens=3)

    # ================================================================ BRAZOS finos, hombros desnudos, MANGAS de paneles
    mano = C - 15.0                                             # punta de los dedos: a la altura de la entrepierna
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.5, s * 6.3))
        cara_fuera = "east" if s > 0 else "west"
        p.caja(f"{hueso}/brazo", "brazo", (x1, mano, -1.4), (x2, C, 1.4),
               encima(piel, [(cara_fuera, 2, 3, TATUAJE, {"k": "#181214"})]), dens=3)
        p.caja(f"{hueso}/anillo", "anillo", (x1 - 0.12, mano + 1.2, -1.52), (x2 + 0.12, mano + 1.6, 1.52),
               lambda t: hex_(ORO["b"] if t.i % 4 == 1 else NEGRO), dens=3)
        if s > 0:     # derecha: la chaqueta tapa el hombro; manga entera, mas negra, con bandas blancas abajo
            arriba = C + 0.3
            tela_m = manchas(blanco_abajo=mano + 4.5, deshilachado=(1.0, 8), sesgo=-0.1)
        else:         # izquierda: caida del hombro (se ve el tatuaje); manga con manchones blancos grandes
            arriba = C - 4.0
            tela_m = manchas(blanco_abajo=mano + 5.5, deshilachado=(1.0, 6), sesgo=0.14)
        malla, n_fuera = manga_kimono(arriba, mano)
        if s < 0:
            malla = geo.espejo_x(malla)
        pint = [tela_m] * n_fuera + [color(NEGRO2)] * (len(malla[1]) - n_fuera)
        p.malla(f"{hueso}/manga", "manga", malla, pint, dens=3)

    # ================================================================ CINTAS: roja adelante y atras, amarilla con talisman
    g = "Body/cintas"
    p.plano(g, "roja_frente", (0.1, L - 8.0, -2.8), (1.6, L - 0.6, -2.8), cinta(ROJO), rot=(0, 0, -3),
            piv=(0.85, L - 0.6, -2.8), dens=3)
    y_arriba = C - 6.6
    z_arriba = 2.2 + 0.9 * (C + 0.4 - y_arriba) / (C + 0.4 - abajo) + 0.14
    p.plano(g, "roja_espalda", (0.6, abajo + 0.5, z_arriba), (2.0, y_arriba, z_arriba), cinta(ROJO),
            rot=(-3.3, 0, 0), piv=(1.3, y_arriba, z_arriba), dens=3)
    x = -5.25
    p.plano(g, "amarilla_lado", (x, abajo - 7.5, -1.4), (x, abajo + 0.2, -0.1), cinta(AMARILLO, "#6A4A08"),
            rot=(0, 0, -4), piv=(x, abajo + 0.2, -0.75), dens=3)
    p.plano(g, "talisman_lado", (x, abajo - 10.6, -1.3), (x, abajo - 7.3, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN),
            rot=(0, 0, -4), piv=(x, abajo + 0.2, -0.75), dens=3)

    # ================================================================ HAKAMA ancho y ZAPATILLAS gruesas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"

        def x(a, b):
            return sorted((s * a, s * b))
        a, b = x(0.1, 3.6)
        p.caja(f"{hueso}/pierna", "pierna", (a, 0, -1.75), (b, L, 1.75),
               lambda t: hex_(PIEL["b"] if t.y < 6.4 else NEGRO), dens=2)        # el tobillo se ve
        # hakama: trapecio ancho de la cintura a media pantorrilla
        arriba = [(3.8, L + 0.6, 2.3), (3.8, L + 0.6, -2.3), (0.05, L + 0.6, -2.3), (0.05, L + 0.6, 2.3)]
        abajo = [(5.4, 6.4, 3.3), (5.4, 6.4, -3.4), (0.7, 6.4, -3.4), (0.7, 6.4, 3.3)]      # se separan abajo
        malla = geo.tronco(abajo, arriba)
        p.malla(f"{hueso}/pantalon", "hakama", malla if s > 0 else geo.espejo_x(malla), pantalon, dens=2)
        g = f"{hueso}/zapatilla"
        zapatilla(p, g, x, s)
    return p


def accesorios():
    """La mascara amarilla de cubo (ojos en cruz y sonrisa), como modelo aparte."""
    o = Objeto("correctar_mascara")
    o.caja("cubo", (-4, 0, -4), (4, 8, 4), sprite({"north": CARA_MASCARA}, {"y": AMARILLO["b"], "k": "#161214"},
                                                   base=color(AMARILLO["b"])), dens=2)
    return [o]
