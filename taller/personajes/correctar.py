"""
Correcthar, el dios libre ("自由な神"). Hecho a mano con el kit (boceto 9, segun referencias/personajes/correctar_nuevo.png
y las siluetas correctar_silueta.png y correctar_zapatos_silueta.png).

Bases del pedido original: semidios cuyo poder es hacer cualquier cosa random; estilo unico, alocado, rebelde, sin
control y arriesgado; estilo japones; SIN MUCHOS DETALLES; pose neutra. Por eso: pocas piezas, bien marcadas.

Medidas: 2.5 bloques (40 px, 1.25 veces Steve). Alto y delgado por proporcion, no por tamano: cabeza de 8 px, torso
de 10 (7 de ancho), piernas de 22 (cintura alta), brazos finos de 15 (las manos a la altura de la entrepierna).

Pintura (textura a densidad 6): PALETA CERRADA de rampas de 5 tonos con hue shifting, una por material, y nada de
ruido al azar. El haori lleva pixel art sacado de la referencia con Pyxelate y limpiado (correctar_pixelart.py,
generado con taller/pixelar.py); el kanji de la espalda sale nitido de una fuente. El pelo es UN solo campo de
mechones que sigue de una caja a la otra sin cortarse.

Capas, de adentro hacia afuera:
  BASE: cara (la de 24 x 24 al doble, ojos amarillos cansados de anime); torso de piel con abdominales, el engranaje
    tatuado, unas ramas de tinta y el cordon del collar; hombros desnudos con el engranaje tatuado
  PELO simple: casco ajustado y flequillo con los mechones dibujados, terminados en puntas; unos pocos cubitos que lo
    despeinan (arriba, costados, nuca); un mechon blanco y la cinta roja a la izquierda
  ACCESORIOS 3D: arete con talisman (izquierda), moneda del collar, un anillo por mano
  HAORI: chaqueta aparte que se abre en la cadera, con manchones blancos de la referencia, kanji 変 atras y el FINAL
    BLANCO (franja de pincelada en el borde de abajo y al final de las mangas); mangas de kimono con la bolsa atras
  FAJA con nudo; tres cintas con "自由な神" escrito (roja adelante y atras, amarilla con talisman al costado
  izquierdo); HAKAMA en trapecio ancho, negro con pliegues, que termina un poco arriba de la zapatilla; ZAPATILLAS
  gordas y bajas con puno del tobillo
"""

import math

from .. import malla as geo
from . import correctar_pixelart as PX
from ..kit import Objeto, Personaje, dibujo, sprite, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_

PIEL = tonos("#C8966E")
# PALETA CERRADA: cada material usa solo su rampa fija de 5 tonos con hue shifting (sombras hacia el azul/violeta,
# luces hacia el calido). Nada de ruido al azar: todo dibujo sale de una forma pensada o de la referencia.
TELA_N = ("#0A0A12", "#141420", "#1E1C26", "#2C2832", "#3E3840")    # tela negra: hondo, base, pliegue, canto, brillo
TELA_B = ("#8E8C9E", "#B4B2C0", "#D4D0D4", "#ECE8E2", "#FFFBF0")    # tela blanca
PELO = ("#0B0910", "#15111A", "#221A22", "#3A2A2C", "#5C4238")      # pelo negro con reflejo cafe
NEGRO, NEGRO2 = TELA_N[1], TELA_N[2]
BLANCO, GRIS = TELA_B[3], TELA_B[1]
TINTA = "#181214"                                                   # tatuajes y escritura
AMARILLO = tonos("#E2B42A")
ROJO = tonos("#C0262A")
ORO = tonos("#C9A14A")
D = 6                                   # texeles por px en todo el modelo (textura grande, mas detalle)

# ---------------------------------------------------------------- cara (24 x 24, densidad 3)

def escalar_dibujo(filas, k):
    """Agranda un dibujo k veces (vecino mas cercano), para usarlo a la densidad nueva."""
    h, w = len(filas), len(filas[0])
    H, W = round(h * k), round(w * k)
    return ["".join(filas[min(h - 1, int(r / k))][min(w - 1, int(c / k))] for c in range(W)) for r in range(H)]


CARA_BASE = dibujo("""
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


def cara_dibujo():
    """La cara de antes (24 x 24) agrandada al doble (48 x 48, densidad 6) y repasada como pixel art: iris con
    degradado y brillo, pupila rasgada, pestanas con punta hacia afuera, ojeras suaves, sombra de la frente bajo el
    flequillo, nariz con sombra y brillo, labio, mejillas y mandibula con volumen."""
    g = [list(f) for f in escalar_dibujo(CARA_BASE, 2)]
    W = len(g)

    def pon(r, c, ch):
        if 0 <= r < W and 0 <= c < W:
            g[r][c] = ch
    for r in range(4):                                            # sombra del flequillo en la frente
        for c in range(W):
            g[r][c] = "s" if r < 2 else "q"
    for r in range(18, 46):                                       # costados de la cara mas oscuros (volumen)
        for c in (0, 1, W - 2, W - 1):
            g[r][c] = "q"
    for lado in (1, -1):
        def c(x):
            return x if lado > 0 else W - 1 - x
        pon(21, c(3), "k"), pon(21, c(4), "k"), pon(20, c(2), "k")          # punta de las pestanas hacia afuera
        pon(23, c(18), "p"), pon(23, c(19), "p")                            # la pestana se afina adentro
        for x in range(10, 18):                                             # iris: arriba mas claro
            if g[24][c(x)] == "Y":
                pon(24, c(x), "y")
        pon(24, c(12), "H")                                                 # brillo
        for r in (24, 25, 26, 27):                                          # pupila rasgada mas fina
            if g[r][c(15)] == "o":
                pon(r, c(15), "O")
        pon(28, c(6), "k")                                                  # pestana de abajo
        for x in range(8, 18):                                              # ojera mas suave abajo
            if g[31][c(x)] == "b":
                pon(31, c(x), "q")
    for c in (23, 24):                                            # nariz: brillo arriba, sombra abajo
        pon(30, c, "l"), pon(31, c, "l")
    for c in range(22, 26):
        pon(33, c, "s")
    pon(34, 22, "q"), pon(34, 25, "q")
    for c in range(20, 28):                                       # boca y labio
        pon(37, c, "p")
        pon(38, c, "m" if 21 <= c <= 26 else "s")
        pon(39, c, "n" if 22 <= c <= 25 else "p")
    for c in list(range(0, 7)) + list(range(W - 7, W)):           # curva de la mandibula
        pon(45, c, "s")
    return ["".join(f) for f in g]


CARA = cara_dibujo()
PAL_CARA = {"p": PIEL["b"], "s": PIEL["s"], "q": "#B98864", "l": PIEL["l"], "k": "#1E1416", "W": "#EDE6DC",
            "Y": "#F0C81E", "y": "#FADF5A", "G": "#B88A12", "L": "#FFF0A0", "H": "#FFFFFF", "o": "#3A2808",
            "O": "#5A4012", "b": PIEL["s2"], "m": "#8A5A44", "n": "#B07A60"}


TATUAJE = dibujo("""
    .kkkk.
    k.kk.k
    kk..kk
    kk..kk
    k.kk.k
    .kkkk.
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
PAL_TALISMAN = {"w": BLANCO, "k": TINTA}

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


def torso_dibujo(W, H, k=1.0):
    """Frente del torso: cordon del collar en V, claviculas, pecho, abdominales, oblicuos, el engranaje tatuado en
    el pecho izquierdo (derecha de la imagen) y unas ramas de tinta en el derecho. k: escala (densidad / 3)."""
    g = [["p"] * W for _ in range(H)]
    m = W // 2

    def pon(c, r, ch):
        if 0 <= r < H and 0 <= c < W:
            g[r][c] = ch

    def fila(f):
        return round(f * H)
    for r in range(round(11 * k)):                              # cordon en V hasta la moneda
        pon(round(m - 6 * k + r * 0.55), r, "k")
        pon(round(m + 5 * k - r * 0.55), r, "k")
    for c in list(range(1, m - 2)) + list(range(m + 2, W - 1)):  # claviculas
        pon(c, round(3 * k), "s")
    for c in list(range(1, m - 1)) + list(range(m + 1, W - 1)):  # borde de abajo del pecho
        pon(c, fila(0.36), "s")
    for r in range(fila(0.38), fila(0.86)):                     # linea del medio
        pon(m, r, "s")
    for f in (0.5, 0.63, 0.76):                                 # abdominales
        for c in list(range(m - round(6 * k), m - 1)) + list(range(m + 2, m + round(7 * k))):
            pon(c, fila(f), "s")
    for r in range(fila(0.5), fila(0.92)):                      # oblicuos
        pon(2 + (r - fila(0.5)) // 6, r, "s")
        pon(W - 3 - (r - fila(0.5)) // 6, r, "s")
    pon(m, fila(0.84), "d")                                     # ombligo
    for f in (0.36, 0.5, 0.63, 0.76):                           # brillo arriba de cada linea
        for c in range(2, W - 2):
            if g[fila(f)][c] == "s" and g[fila(f) - 1][c] == "p":
                g[fila(f) - 1][c] = "l"
    for r in range(round(4 * k), H):                            # costados del torso mas oscuros
        for c in (0, 1, W - 2, W - 1):
            if g[r][c] == "p":
                g[r][c] = "q"
    engranaje = ("...kkkk...", "..k.kk.k..", ".k.k..k.k.", "kk.k..k.kk", "k.kk..kk.k", "k.kk..kk.k",
                 "kk.k..k.kk", ".k.k..k.k.", "..k.kk.k..", "...kkkk...")
    for r, fil in enumerate(engranaje):
        for c, ch in enumerate(fil):
            if ch == "k":
                pon(m + 2 + c, round(3 * k) + r, "k")
    for r in range(round(3 * k) + 10, round(3 * k) + 15):          # tinta que chorrea
        if r % 2:
            pon(m + 5, r, "k")
        pon(m + 8, r - 1, "k")
    for c, r in ((1, 5), (2, 6), (3, 7), (4, 8), (5, 9), (9, 5), (8, 6), (7, 7), (6, 8), (5, 10), (6, 11),
                 (7, 12), (3, 11)):                             # ramas de tinta
        pon(c, round(r * k), "k")
    return ["".join(f) for f in g]


# ---------------------------------------------------------------- pintores (solo colores de las rampas, sin ruido)

CUELLO, TOPE = 32, 40                   # alturas de la cabeza (las fija construir: altura 40, cabeza 8)


def color(hexa):
    c = hex_(hexa)
    return lambda t: c


def _u(t):
    """Coordenada horizontal sobre la superficie (px): x en las caras de frente y espalda, z en los costados."""
    return t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z


def onda_pincel(c):
    """Cuantos texeles sube o baja el borde de arriba de la franja blanca en la columna c (pincelada ondulada)."""
    return round(2.2 * math.sin(c * 0.33) + 1.2 * math.sin(c * 0.87 + 1.3))


DIENTES = (0, 0, 1, 3, 2, 0, 0, 1, 0, 2, 4, 2, 1, 0)   # dobladillo deshilachado (texeles), por pares de columnas
GOTAS = {5: 4, 19: 6, 31: 3}                            # columna (cada 40) -> chorrito de tinta sobre lo blanco
PAL_PX = {"n": hex_(NEGRO), "g": hex_(TELA_B[1]), "b": hex_(TELA_B[3]), "h": hex_(TELA_B[4]),
          "k": hex_(TELA_B[3]), "a": hex_(TELA_N[3])}


def proyectar(filas, u_de, v_de):
    """Pixel art pegado por posicion: u_de(t), v_de(t) dan los px desde la esquina de arriba a la izquierda (de quien
    mira esa cara). Devuelve la funcion t -> letra del texel (None si cae afuera del dibujo)."""
    alto, ancho = len(filas), len(filas[0])

    def letra(t):
        c, r = math.floor(u_de(t) * D), math.floor(v_de(t) * D)
        if 0 <= r < alto and 0 <= c < ancho:
            return filas[r][c]
        return None
    return letra


def tela(borde=None, dibujo=None, franja=2.8):
    """Tela del haori. dibujo: t -> letra del pixel art de la referencia (o None); lo negro queda liso (las caras de
    arriba con luz). borde: t -> altura del final de la tela; los ultimos 'franja' px quedan BLANCOS: pincelada con
    el borde de arriba ondulado, chorritos de tinta, sombra del dobladillo y el borde deshilachado en dientes."""
    def p(t):
        y = t.y
        if borde is not None and t.cara not in ("up", "down"):
            c = math.floor(_u(t) * D) % 400
            d = (y - borde(t)) * D                              # texeles desde el final de la tela
            diente = DIENTES[(c // 2) % len(DIENTES)]
            if d < diente:
                return TRANSPARENTE
            tope = franja * D + onda_pincel(c)
            if d < tope:
                if GOTAS.get(c % 40, 0) > tope - d:
                    return hex_(NEGRO)
                if d >= tope - 1:
                    return hex_(TELA_B[2])                      # canto de la pincelada
                if d < diente + 2:
                    return hex_(TELA_B[1])                      # sombra del dobladillo
                return hex_(TELA_B[3])
        if dibujo is not None:
            letra = dibujo(t)
            if letra is not None and letra != "n":
                return PAL_PX[letra]
        return hex_(NEGRO2 if t.cara == "up" else NEGRO)
    return p


def pantalon(t):
    """Hakama negro liso: cada 8 texeles un pliegue hondo con el canto iluminado al lado; el ruedo mas oscuro."""
    if t.cara == "down":
        return hex_(TELA_N[0])
    if t.cara == "up":
        return hex_(NEGRO2)
    c = math.floor(abs(_u(t)) * D) % 8
    if c == 0 or t.y < 6.4 + 1.5 / D:
        return hex_(TELA_N[0])
    if c == 1:
        return hex_(TELA_N[2])
    return hex_(NEGRO)


def faja(t):
    """Faja negra con el canto de arriba y de abajo con luz."""
    if t.cara in ("north", "south", "east", "west") and (t.j == 0 or t.j == t.th - 1):
        return hex_(TELA_N[3])
    return hex_(NEGRO2)


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
    """Piel con volumen: arriba con luz, bordes de cada cara un poco mas oscuros."""
    if t.cara == "up":
        return hex_(PIEL["l"])
    if t.cara == "down":
        return hex_(PIEL["s"])
    if t.i < 2 or t.i >= t.tw - 2:
        return hex_("#B98864")
    return hex_(PIEL["b"])


CINTA_LETRAS = (PX.CINTA_0, PX.CINTA_1, PX.CINTA_2, PX.CINTA_3)


def cinta(c, marcas="#5A1010"):
    """Cinta de tela: cantos en sombra, brillo junto al canto y "自由な神" (dios libre) escrito hacia abajo."""
    def p(t):
        if t.i == 0 or t.i == t.tw - 1:
            return hex_(c["s"])
        if t.tw >= 8:
            k, r = divmod(t.j - 3, 10)
            cc = t.i - (t.tw - 7) // 2
            if t.j >= 3 and r < 7 and 0 <= cc < 7 and CINTA_LETRAS[k % 4][r][cc] == "k":
                return hex_(marcas)
        return hex_(c["l"] if t.i == 1 else c["b"])
    return p


def oro(t):
    return hex_(ORO["l"] if t.cara == "up" else ORO["b"])


# ---------------------------------------------------------------- pelo: un solo campo de mechones

CORONILLA = (0.0, 1.2)                  # (x, z) de donde salen los mechones (un remolino un poco atras)
MECHONES = 22                           # mechones en la vuelta entera de la cabeza
SUBE = (0.0, 0.5, 0.2, 0.8, 0.1, 0.6, 0.3)  # cuanto mas corto es cada mechon (px), en orden fijo
MECHON_BLANCO = (-4,)                   # mechon blanco del lado izquierdo, junto a la cinta roja
SUBE_FLEQUILLO = {-3: 0.0, -2: 0.9, -1: 0.6, 0: 0.35, 1: 1.0, 2: 0.0}   # flequillo: hasta los ojos, uno los cruza


def mechon(t):
    """Campo de mechones CONTINUO: depende solo de la posicion (angulo alrededor de la coronilla), asi el mismo
    mechon sigue de arriba al costado, a la nuca, al flequillo y a los cubitos sin cortarse entre cajas.
    Devuelve (numero de mechon, 0..1 a lo ancho del mechon)."""
    a = math.atan2(t.x - CORONILLA[0], -(t.z - CORONILLA[1])) + 0.08 * math.sin(t.y * 1.1)
    s = a / (2 * math.pi) * MECHONES
    n = math.floor(s)
    return n, s - n


def pelo(t, blanco=False):
    """Cada mechon: separacion honda, lado en sombra, cuerpo y canto con luz. Un anillo de brillo de anime que baja
    en diagonal en cada mechon; mas oscuro abajo, cerca del cuello."""
    n, k = mechon(t)
    rampa = TELA_B if (blanco or n in MECHON_BLANCO) else PELO
    if t.cara == "down":
        return hex_(rampa[0])
    i = 0 if k < 0.1 else 1 if k < 0.3 else 2 if k < 0.8 else 3 if k < 0.9 else 2
    if t.cara == "up":
        if math.hypot(t.x - CORONILLA[0], t.z - CORONILLA[1]) < 0.7:
            i = 1                                               # remolino
    else:
        anillo = TOPE - 1.9 + 0.35 * ((n % 3) - 1) + 0.6 * (k - 0.5)
        if abs(t.y - anillo) < 0.32 and 0.25 < k < 0.85:
            return hex_(rampa[4] if 0.45 < k < 0.65 else rampa[3])
        if t.y < CUELLO + 4.0:
            i = max(0, i - 1)
    return hex_(rampa[i])


def puntas(base, sube=SUBE, punta=1.0):
    """Recorta el borde de abajo de una caja de pelo en PUNTAS alineadas con los mechones: cada mechon termina en
    una punta (el centro baja mas) y unos son mas cortos que otros."""
    def p(t):
        if t.cara == "down":
            return TRANSPARENTE
        if t.cara != "up":
            n, k = mechon(t)
            alto = sube.get(n, 0.0) if isinstance(sube, dict) else sube[n % len(sube)]
            if t.y - t.f[1] < alto + punta * abs(2 * k - 1):
                return TRANSPARENTE
        return base(t)
    return p


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


def haori(C, abajo, pint_paneles):
    """Cuerpo del haori como chaqueta aparte: espalda, costados y dos delanteros que se ABREN hacia la cadera (pasan
    por encima del pantalon y marcan el dobladillo). Abierto adelante; derecha puesta en el hombro, izquierda caida.
    Cada panel tiene forro corrido hacia adentro. pint_paneles: pintores de espalda, costado derecho, costado
    izquierdo, delantero derecho y delantero izquierdo. Devuelve (malla, pintores)."""
    espalda, costado_d, costado_i, delantero_d, delantero_i = pint_paneles
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
        pint.append(color(TELA_N[0]))
    zt_f, zt_b, zb_f, zb_b = -2.15, 2.2, -3.05, 3.1               # arriba ajustado, abajo abierto
    xt, xb = 3.85, 4.95
    sup_d, sup_i = C - 0.2, C - 3.5                               # delantero derecho puesto, izquierdo caido
    lado_d, lado_i = C - 0.2, C - 5.0
    panel([(-3.8, C + 0.4, zt_b), (3.8, C + 0.4, zt_b), (xb, abajo, zb_b), (-xb, abajo, zb_b)], espalda)
    panel([(xt, lado_d, zt_b), (xt, lado_d, zt_f), (xb, abajo, zb_f), (xb, abajo, zb_b)], costado_d)
    panel([(-xt, lado_i, zt_f), (-xt, lado_i, zt_b), (-xb, abajo, zb_b), (-xb, abajo, zb_f)], costado_i)
    panel([(1.9, sup_d, zt_f), (xt, sup_d, zt_f), (xb, abajo, zb_f), (2.4, abajo, zb_f)], delantero_d)
    panel([(-xt, sup_i, zt_f), (-1.9, sup_i, zt_f), (-2.4, abajo, zb_f), (-xb, abajo, zb_f)], delantero_i)
    # solapas negras a lo largo de la abertura (un poco adelante del delantero)
    for s, sup in ((1, sup_d), (-1, sup_i)):
        pts = [(s * 1.65, sup + 0.3, zt_f - 0.1), (s * 2.35, sup + 0.3, zt_f - 0.1),
               (s * 2.85, abajo + 0.3, zb_f - 0.1), (s * 2.15, abajo + 0.3, zb_f - 0.1)]
        if s < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        idx = [m.v((q[0], q[1], q[2])) for q in pts]
        m.cara(tuple(idx), (0, 0, -1), "solapa")
        pint.append(lambda t: hex_(TELA_N[3] if t.i in (0, t.tw - 1) else NEGRO2))
    return (m.vs, m.caras), pint


MANGA_Z_FRENTE, MANGA_Z_ATRAS = -2.9, 3.3


def final_manga(mano):
    """Altura del borde de abajo de la manga segun z (adelante en la muneca, atras la bolsa cuelga mas)."""
    puno, bolsa = mano + 2.6, mano - 1.2

    def f(t):
        k = (t.z - MANGA_Z_FRENTE) / (MANGA_Z_ATRAS - MANGA_Z_FRENTE)
        return puno + (bolsa - puno) * max(0.0, min(1.0, k))
    return f


def manga_kimono(arriba, mano):
    """Manga ancha de kimono (lado derecho): trapecio que se abre hacia afuera y hacia abajo; adelante termina en la
    muneca (la mano sale por ahi) y atras cuelga mas, como la bolsa del kimono."""
    xi, xo_arriba, xo_abajo = 3.55, 6.7, 9.0
    puno, bolsa = mano + 2.6, mano - 1.2
    sup = [(xo_arriba, arriba, 1.7), (xo_arriba, arriba, -1.7), (xi, arriba, -1.7), (xi, arriba, 1.7)]
    inf = [(xo_abajo, bolsa, MANGA_Z_ATRAS), (xo_abajo, puno, MANGA_Z_FRENTE), (xi + 0.05, puno, MANGA_Z_FRENTE),
           (xi + 0.05, bolsa, MANGA_Z_ATRAS)]
    return tubo_hueco(inf, sup)


def tela_manga(s, arriba, mano):
    """Tela de la manga (s = 1 derecha, -1 izquierda): en la cara de afuera, la de adelante y la de atras va el pixel
    art sacado de la misma cara en la referencia; el final de la manga queda blanco."""
    lado = "DER" if s > 0 else "IZQ"
    v = (lambda t: arriba - t.y)
    dib = {
        "fuera": proyectar(getattr(PX, f"MANGA_{lado}_FUERA"),
                           (lambda t: MANGA_Z_ATRAS - t.z) if s > 0 else (lambda t: t.z - MANGA_Z_FRENTE), v),
        "frente": proyectar(getattr(PX, f"MANGA_{lado}_FRENTE"),
                            (lambda t: 9.0 - t.x) if s > 0 else (lambda t: -3.55 - t.x), v),
        "espalda": proyectar(getattr(PX, f"MANGA_{lado}_ESPALDA"),
                             (lambda t: t.x - 3.55) if s > 0 else (lambda t: t.x + 9.0), v),
    }

    def dibujo(t):
        n = t.n
        if abs(n[0]) > 0.7:
            return dib["fuera"](t) if n[0] * s > 0 else None
        if abs(n[2]) > 0.7:
            return dib["frente" if n[2] < 0 else "espalda"](t)
        return None
    return tela(final_manga(mano), dibujo)


# ---------------------------------------------------------------- zapatillas, cubo por cubo

MANCHAS_SUELA = ((-2.4, 1.1, 1.0, 0.42), (1.2, 0.95, 0.75, 0.5))   # (z, y, radio z, radio y) de cada mancha


def suela_manchada(t):
    """Plataforma blanca con manchas negras grandes (como la referencia), de forma fija."""
    if t.cara == "down":
        return hex_(TELA_B[0])
    if t.cara == "up":
        return hex_(TELA_B[4])
    if t.fila_abajo < 2:
        return hex_(TELA_B[1])                                 # sombra contra el piso
    if t.j < 1:
        return hex_(TELA_B[4])                                 # canto de arriba con luz
    if abs(t.n[0]) > 0.7:                                      # dos manchas negras a cada costado
        for zc, yc, rz, ry in MANCHAS_SUELA:
            if ((t.z - zc) / rz) ** 2 + ((t.y - yc) / ry) ** 2 < 1:
                return hex_(NEGRO)
    return hex_(BLANCO)


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
            p.plano(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=D)
        else:
            p.caja(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=D)

    blanco, negro, amarillo = color(BLANCO), color(NEGRO), color(AMARILLO["b"])
    # plataforma ancha con escalon abajo (hueco en el arco) y bordes redondeados con dos cajas cruzadas
    cubo("suela_baja_frente", 0.35, 3.65, 0.0, 0.55, -4.1, -1.1, suela_manchada)
    cubo("suela_baja_atras", 0.35, 3.65, 0.0, 0.55, 0.7, 2.6, suela_manchada)
    cubo("suela_arco", 0.6, 3.4, 0.3, 0.55, -1.1, 0.7, color(GRIS))
    cubo("suela_ancha", 0.12, 3.88, 0.55, 1.6, -3.7, 2.3, suela_manchada)
    cubo("suela_larga", 0.35, 3.65, 0.55, 1.6, -4.2, 2.7, suela_manchada)
    # capellada: perfil de costado (punta baja, rampa, tobillo) extruido a lo ancho
    perfil = [(-4.0, 1.6), (-3.9, 2.35), (-3.2, 2.75), (-1.0, 3.55), (-0.75, 3.9), (2.45, 3.9), (2.6, 1.6)]
    malla = geo.extruir_x(perfil, 0.4, 3.6)
    p.malla(g, "capellada", malla if s > 0 else geo.espejo_x(malla), capellada, dens=D)
    cubo("puntera", 0.6, 3.4, 1.6, 2.25, -4.15, -3.45, blanco)
    cubo("talonera", 0.6, 3.4, 1.6, 3.4, 2.5, 2.75, blanco)
    rampa = dict(rot=(-20.0, 0, 0), piv=(2.3, 3.55, -1.0))
    cubo("cordon", 1.4, 2.4, 3.55, 3.67, -3.2, -1.0, amarillo, **rampa)
    for k, zc in enumerate((-2.7, -1.8)):
        cubo(f"cordon_cruce{k}", 0.8, 3.0, 3.55, 3.65, zc - 0.18, zc + 0.18, amarillo, **rampa)
    # puno del tobillo, mas angosto, con dos correas, hebilla amarilla y lengueta
    cubo("puno", 0.0, 3.8, 3.6, 5.2, -1.95, 2.3, negro)                   # rodea la pierna (que mide +-1.75)
    cubo("correa1", -0.05, 3.9, 3.85, 4.25, -2.05, 2.4, color("#D8D4CE"))
    cubo("correa2", -0.05, 3.9, 4.5, 4.95, -2.05, 2.4, negro)
    cubo("hebilla", 1.3, 2.4, 4.4, 5.05, -2.27, -2.03, amarillo)
    cubo("hebilla_perno", 1.7, 2.0, 4.6, 4.85, -2.34, -2.25, oro)
    cubo("lengueta", 1.1, 2.6, 3.5, 4.4, -2.15, -1.9, negro)
    cubo("lengueta_punta", 1.1, 2.6, 5.0, 5.6, -2.15, -1.9, blanco)
    cubo("tira_colgando", 3.95, 3.95, 3.0, 4.6, -1.9, -1.3, amarillo, rot=(0, 0, -8), piv=(3.95, 4.6, -1.6))


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("correctar", altura=40, cabeza=8, torso=(7, 10, 3.5), brazo=(2.8, 2.8), pierna=(3.5, 3.5))
    C, T, L = p.cuello, p.tope, p.lh                           # 32, 40, 22: cintura alta y piernas largas
    assert (C, T) == (CUELLO, TOPE)

    # ================================================================ CABEZA y cara
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), sprite({"north": CARA}, PAL_CARA, base=piel), dens=D)

    # ================================================================ PELO simple: casco + flequillo + unos cubitos
    # todo pintado con el MISMO campo de mechones (continuo de una caja a otra); abajo termina en puntas
    g = "Head/pelo"
    p.caja(g, "casco_arriba", (-4.35, T - 0.6, -4.35), (4.35, T + 0.6, 4.35), pelo, dens=D)
    p.caja(g, "casco_nuca", (-4.35, C + 1.4, 3.7), (4.35, T - 0.6, 4.35), puntas(pelo), dens=D)
    for s in (1, -1):
        x1, x2 = sorted((s * 3.7, s * 4.35))
        p.caja(g, f"casco_lado{s}", (x1, C + 2.6, -3.95), (x2, T - 0.6, 3.7), puntas(pelo), dens=D)
    p.caja(g, "flequillo", (-4.35, C + 3.4, -4.35), (4.35, T - 0.6, -3.95), puntas(pelo, SUBE_FLEQUILLO, 1.2),
           dens=D)
    # unos pocos cubitos que lo despeinan: (centro, medidas, giro, de donde cuelga, color)
    cubitos = [((-2.0, T + 1.0, -1.2), (1.0, 1.6, 1.0), (10, 0, 22), "abajo", "negro"),
               ((0.9, T + 1.1, -1.8), (1.0, 1.8, 1.0), (-14, 0, -12), "abajo", "negro"),
               ((2.7, T + 0.9, 0.8), (1.0, 1.4, 1.0), (8, 0, -28), "abajo", "negro"),
               ((-0.8, T + 1.0, 2.0), (1.0, 1.5, 1.0), (24, 0, 10), "abajo", "negro"),
               ((-3.3, T + 0.9, -0.4), (1.0, 1.5, 1.0), (0, 0, 28), "abajo", "blanco"),
               ((-1.8, C + 2.4, 4.5), (1.0, 1.8, 0.8), (-25, 0, 8), "arriba", "negro"),
               ((0.6, C + 2.0, 4.5), (1.0, 2.0, 0.8), (-30, 0, -6), "arriba", "negro"),
               ((2.6, C + 2.6, 4.5), (1.0, 1.6, 0.8), (-22, 0, -12), "arriba", "negro")]
    for s in (1, -1):
        for y, z in ((C + 5.6, -1.4), (C + 4.0, 1.6)):
            tinte = "blanco" if (s < 0 and z < 0) else "negro"
            cubitos.append(((s * 4.45, y, z), (0.8, 1.8, 0.8), (0, 0, 25 * s), "arriba", tinte))
    tintes = {"negro": pelo, "blanco": lambda t: pelo(t, blanco=True)}
    for k, ((x, y, z), (w, h, d), rot, cuelga, tinte) in enumerate(cubitos):
        piv = (x, y - h / 2, z) if cuelga == "abajo" else (x, y + h / 2, z)
        p.caja(g, f"cubito{k}", (x - w / 2, y - h / 2, z - d / 2), (x + w / 2, y + h / 2, z + d / 2), tintes[tinte],
               rot=rot, piv=piv, dens=D)
    # cinta roja del lado izquierdo
    p.caja(g, "cinta_roja", (-5.0, T - 2.8, -2.0), (-4.3, T + 0.4, -0.7), color(ROJO["b"]), rot=(0, 0, 18),
           piv=(-4.65, T + 0.4, -1.35), dens=D)
    p.caja(g, "cinta_roja2", (-5.4, T - 0.9, -1.9), (-4.4, T + 0.2, -0.6), color(ROJO["l"]), dens=D)

    # ================================================================ ARETE con talisman (izquierda)
    g = "Head/aretes"
    p.caja(g, "argolla", (-4.55, C + 2.4, -0.4), (-4.25, C + 3.2, 0.4), oro, dens=D)
    p.caja(g, "cadena", (-4.75, C + 1.4, -0.1), (-4.55, C + 2.6, 0.1), oro, dens=D)
    p.plano(g, "talisman", (-5.4, C - 1.2, -0.2), (-4.3, C + 1.5, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN), dens=D)

    # ================================================================ TORSO delgado
    torso = torso_dibujo(7 * D, 10 * D, D / 3)
    pal_torso = {"p": PIEL["b"], "s": PIEL["s"], "k": TINTA, "d": PIEL["s2"], "l": PIEL["l"], "q": "#B98864"}
    p.caja("Body/torso", "torso", (-3.5, L, -1.75), (3.5, C, 1.75), sprite({"north": torso}, pal_torso, base=piel), dens=D)
    p.caja("Body/collar", "moneda", (-0.75, C - 4.3, -2.05), (0.75, C - 2.8, -1.75), oro, rot=(0, 0, 45),
           piv=(0, C - 3.55, -1.9), dens=D)
    p.caja("Body/collar", "moneda_centro", (-0.3, C - 3.85, -2.15), (0.3, C - 3.25, -2.0), color("#5A4416"), dens=D)

    # ================================================================ FAJA con nudo
    p.caja("Body/faja", "faja", (-3.9, L - 1.0, -2.15), (3.9, L + 1.2, 2.15), faja, dens=D)
    p.caja("Body/faja", "nudo", (-0.2, L - 1.3, -2.75), (1.8, L + 1.0, -2.15), color(NEGRO), dens=D)

    # ================================================================ HAORI: chaqueta aparte que se abre en la cadera
    g = "Body/haori"
    abajo = L - 5.4                                             # el haori llega a la cadera
    def final(t, y=abajo):                                      # la franja blanca va al final del haori
        return y
    # pixel art de la referencia en la espalda (con el kanji) y en los delanteros; los costados casi no se ven
    espalda = tela(final, proyectar(PX.ESPALDA, lambda t: t.x + 4.95, lambda t: C + 0.4 - t.y))
    delantero_d = tela(final, proyectar(PX.DELANTERO_DER, lambda t: 4.95 - t.x, lambda t: C - 0.2 - t.y))
    delantero_i = tela(final, proyectar(PX.DELANTERO_IZQ, lambda t: -1.9 - t.x, lambda t: C - 3.5 - t.y))
    malla, pintores = haori(C, abajo, (espalda, tela(final), tela(final), delantero_d, delantero_i))
    p.malla(g, "haori", malla, pintores, dens=D)

    # ================================================================ BRAZOS finos, hombros desnudos, MANGAS de paneles
    mano = C - 15.0                                             # punta de los dedos: a la altura de la entrepierna
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.5, s * 6.3))
        cara_fuera = "east" if s > 0 else "west"
        p.caja(f"{hueso}/brazo", "brazo", (x1, mano, -1.4), (x2, C, 1.4),
               encima(piel, [(cara_fuera, 2, 6, escalar_dibujo(TATUAJE, 2), {"k": TINTA})]), dens=D)
        p.caja(f"{hueso}/anillo", "anillo", (x1 - 0.12, mano + 1.2, -1.52), (x2 + 0.12, mano + 1.6, 1.52),
               lambda t: hex_(ORO["b"] if t.i % 4 == 1 else NEGRO), dens=D)
        # derecha: la chaqueta tapa el hombro; izquierda: caida del hombro (se ve el tatuaje)
        arriba = C + 0.3 if s > 0 else C - 4.0
        malla, n_fuera = manga_kimono(arriba, mano)
        if s < 0:
            malla = geo.espejo_x(malla)
        pint = [tela_manga(s, arriba, mano)] * n_fuera + [color(TELA_N[0])] * (len(malla[1]) - n_fuera)
        p.malla(f"{hueso}/manga", "manga", malla, pint, dens=D)

    # ================================================================ CINTAS: roja adelante y atras, amarilla con talisman
    g = "Body/cintas"
    p.plano(g, "roja_frente", (0.1, L - 8.0, -2.8), (1.6, L - 0.6, -2.8), cinta(ROJO), rot=(0, 0, -3),
            piv=(0.85, L - 0.6, -2.8), dens=D)
    y_arriba = C - 6.6
    z_arriba = 2.2 + 0.9 * (C + 0.4 - y_arriba) / (C + 0.4 - abajo) + 0.14
    p.plano(g, "roja_espalda", (0.6, abajo + 0.5, z_arriba), (2.0, y_arriba, z_arriba), cinta(ROJO),
            rot=(-3.3, 0, 0), piv=(1.3, y_arriba, z_arriba), dens=D)
    x = -5.25
    p.plano(g, "amarilla_lado", (x, abajo - 7.5, -1.4), (x, abajo + 0.2, -0.1), cinta(AMARILLO, "#6A4A08"),
            rot=(0, 0, -4), piv=(x, abajo + 0.2, -0.75), dens=D)
    p.plano(g, "talisman_lado", (x, abajo - 10.6, -1.3), (x, abajo - 7.3, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN),
            rot=(0, 0, -4), piv=(x, abajo + 0.2, -0.75), dens=D)

    # ================================================================ HAKAMA ancho y ZAPATILLAS gruesas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"

        def x(a, b):
            return sorted((s * a, s * b))
        a, b = x(0.1, 3.6)
        p.caja(f"{hueso}/pierna", "pierna", (a, 3.8, -1.75), (b, L, 1.75),
               lambda t: hex_(PIEL["b"] if t.y < 6.4 else NEGRO), dens=D)        # el tobillo se ve
        # hakama: trapecio ancho de la cintura a media pantorrilla
        cintura = [(3.8, L + 0.6, 2.3), (3.8, L + 0.6, -2.3), (0.05, L + 0.6, -2.3), (0.05, L + 0.6, 2.3)]
        ruedo = [(5.4, 6.4, 3.3), (5.4, 6.4, -3.4), (0.7, 6.4, -3.4), (0.7, 6.4, 3.3)]      # se separan abajo
        malla = geo.tronco(ruedo, cintura)
        p.malla(f"{hueso}/pantalon", "hakama", malla if s > 0 else geo.espejo_x(malla), pantalon, dens=D)
        g = f"{hueso}/zapatilla"
        zapatilla(p, g, x, s)
    return p


def accesorios():
    """La mascara amarilla de cubo (ojos en cruz y sonrisa), como modelo aparte."""
    o = Objeto("correctar_mascara")
    o.caja("cubo", (-4, 0, -4), (4, 8, 4), sprite({"north": CARA_MASCARA}, {"y": AMARILLO["b"], "k": "#161214"},
                                                   base=color(AMARILLO["b"])), dens=D)
    return [o]
