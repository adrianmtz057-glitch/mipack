"""
Correcthar, el semidios que corrige todo a su forma anterior (原状回復: volver al estado original). Hecho a mano con el
kit segun referencias/personajes/correctar_semidios.png. Estilo: serio, tranquilo, disciplinado, analitico, solitario.

Medidas: 2.5 bloques (40 px). Cabeza de 8, torso de 10 (7 de ancho), piernas de 22, brazos finos.
Pintura a densidad 8: cada px del modelo son 8 x 8 texeles (la cara es un pixel art de 64 x 64). Paleta cerrada de
rampas con hue shifting y sin ruido; el volumen lo termina la luz horneada del motor (taller/luz.py).

Capas, de adentro hacia afuera:
  BASE: cara serena de ojos grises; kimono negro cruzado en V con el cuello blanco, el pecho a la vista con el
    tatuaje del circulo y el collar de jade; manos con un anillo de plata
  PELO negro ordenado: casco, flequillo que cae sobre el ojo derecho, mechones que enmarcan la cara, un pelito
    parado arriba; todo con el mismo campo de mechones (continuo de una caja a otra) y puntas abajo
  ARETES en las dos orejas: argolla de plata, etiqueta blanca y borla azul hasta el hombro
  HAORI BLANCO largo hasta la canilla, abierto adelante con las bandas negras del cuello, el simbolo del circulo
    (aro con una gota y una cuerda) grande en la espalda y chico en cada manga, mangas de kimono con forro azul
  OBI azul con el cordon blanco y su nudo, cordones con borlas y la etiqueta 原状回復 colgando adelante y atras
  HAKAMA negro ancho con pliegues hasta el tobillo; calcetas a rayas; BOTAS gruesas negras y blancas
  KATANA a la izquierda, metida en el obi: mango con trenzado, tsuba y punta de oro, vaina negra hacia atras
"""

import math

from .. import malla as geo
from . import correctar_pixelart as PX
from ..kit import Personaje, sprite, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_

D = 8                                                   # texeles por px: la cara queda de 64 x 64
DENS_LETRAS = 12                                        # las etiquetas: 1.5 px de ancho = letra de 16 + borde

# PALETA CERRADA: cada material usa solo su rampa (oscuro -> claro); las sombras van al frio, las luces al calido
PIEL = tonos("#ECCDB2")
TELA_B = ("#9C9AAA", "#BEBCC8", "#DAD8DE", "#EFEDE9", "#FFFDF8")    # haori blanco
TELA_N = ("#0A0A12", "#141420", "#1E1C26", "#2C2832", "#3E3840")    # kimono y hakama negros
AZUL = ("#151B2E", "#222C46", "#33405E", "#4A5B7E", "#687CA0")      # obi, forro, borlas
PELO = ("#050508", "#0B0C11", "#12141B", "#1E2230", "#343B50")      # negro con reflejo frio
PLATA = tonos("#B9BEC9")
JADE = tonos("#4F8C70")
ORO = tonos("#C9A14A")
TINTA = "#15151C"
NEGRO, NEGRO2 = TELA_N[1], TELA_N[2]
BLANCO = TELA_B[3]

CUELLO, TOPE, CADERA = 32, 40, 22                       # alturas (las fija construir)


def color(hexa):
    c = hex_(hexa)
    return lambda t: c


# ---------------------------------------------------------------- dibujo con primitivas (pixel art a mano)

class Hoja:
    """Lienzo de letras para dibujar pixel art con primitivas: puntos, lineas, elipses."""

    def __init__(self, ancho, alto, fondo):
        self.w, self.h = ancho, alto
        self.g = [[fondo] * ancho for _ in range(alto)]

    def p(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def linea(self, x0, y0, x1, y1, c, grosor=1):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) * 2))
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
            for g in range(grosor):
                self.p(x, y + g, c)

    def filas(self):
        return ["".join(f) for f in self.g]


def cara_dibujo():
    """Cara serena de 64 x 64: ojos grises en almendra con el parpado caido (mirada fria y tranquila), raya gruesa de
    pestanas con la punta hacia afuera, iris con sombra del parpado arriba y luz abajo, brillo chico; cejas finas y
    rectas, nariz de una sombra, boca de una linea. Sin ojeras ni colores en las mejillas."""
    h = Hoja(64, 64, "p")
    for y in range(64):                                   # costados un poco mas oscuros (volumen)
        for x in (0, 1, 62, 63):
            h.p(x, y, "q")
    for lado in (1, -1):
        def X(x):
            return x if lado > 0 else 63 - x
        # el ojo de la izquierda de la imagen; el otro es su espejo. Esquina de afuera en x=9, de adentro en x=25
        for x in range(9, 26):
            u = (x - 9) / 16
            arriba = 33 - 3.4 * math.sin(math.pi * u) + 0.6 * (1 - u)   # parpado caido, mas bajo afuera
            abajo = 33.2 + 2.2 * math.sin(math.pi * u)
            for y in range(25, 40):
                if arriba < y < abajo:
                    h.p(X(x), y, "W")
            for g in range(3 if u < 0.35 else 2):         # raya de pestanas, mas gruesa afuera
                h.p(X(x), arriba - g, "k")
            if u > 0.12:
                h.p(X(x), arriba - 4.2, "s")              # pliegue del parpado
            if u < 0.4:
                h.p(X(x), abajo + 0.6, "k")               # pestana de abajo, solo afuera
            elif u < 0.9:
                h.p(X(x), abajo + 0.6, "s")
        h.linea(X(9), 32, X(6), 30.5, "k", 2)               # punta de las pestanas hacia afuera
        for y in range(25, 40):                           # iris y pupila, recortados por los parpados
            for x in range(9, 26):
                if h.g[y][X(x)] != "W":
                    continue
                d = math.hypot(x - 18, y - 32.6)
                if d < 1.7:
                    h.p(X(x), y, "o")
                elif d < 4.7:
                    h.p(X(x), y, "Y" if y < 31 else ("I" if y > 34 else "y"))
                elif y < 30.5:
                    h.p(X(x), y, "w")                     # sombra del parpado sobre lo blanco
        for x, y in ((15, 30), (16, 30), (15, 31), (16, 31)):
            h.p(X(x), y, "H")
        h.p(X(20), 34, "L")
        h.linea(X(8), 22.5, X(25), 21.5, "k")              # ceja fina y recta
        h.linea(X(9), 23.5, X(24), 22.5, "s")
    for y, x, c in ((40, 33, "s"), (41, 33, "s"), (42, 33, "s"), (43, 32, "s"), (42, 31, "l")):   # nariz
        h.p(x, y, c)
    for x in range(28, 37):                               # boca
        h.p(x, 50, "n" if 30 <= x <= 34 else "m")
    for x in range(30, 35):
        h.p(x, 52, "s")
    for x in range(64):                                   # mandibula
        h.p(x, 63, "s")
    return h.filas()


CARA = cara_dibujo()
PAL_CARA = {"p": PIEL["b"], "q": "#DDB79A", "s": PIEL["s"], "l": PIEL["l"], "k": "#1A1820", "W": "#F4F2EE",
            "w": "#C9C8D2", "Y": "#4E5870", "y": "#7D89A3", "I": "#A9B5CB", "o": "#22263A", "H": "#FFFFFF",
            "L": "#DDE6F2", "m": "#B07C6C", "n": "#8E5E54"}


def piel(t):
    """Piel con volumen: arriba con luz, bordes de cada cara un poco mas oscuros."""
    if t.cara == "up":
        return hex_(PIEL["l"])
    if t.cara == "down":
        return hex_(PIEL["s"])
    if t.i < 2 or t.i >= t.tw - 2:
        return hex_("#DDB79A")
    return hex_(PIEL["b"])


# ---------------------------------------------------------------- simbolo del circulo (equilibrio)

def simbolo(u, v, r):
    """El simbolo de Correcthar centrado en (0, 0), radio r (px): un aro, adentro una gota que apunta arriba y un
    circulito arriba del aro con la cuerda que sube. Devuelve True si (u, v) cae en la tinta (v hacia arriba)."""
    d = math.hypot(u, v)
    if abs(d - r) < r * 0.13:
        return True                                        # aro
    gota_c, gota_r = -0.12 * r, 0.36 * r
    if math.hypot(u, v - gota_c) < gota_r:
        return True                                        # panza de la gota
    alto = v - gota_c
    if 0 < alto < 0.78 * r and abs(u) < gota_r * (1 - alto / (0.78 * r)) ** 1.3:
        return True                                        # punta de la gota
    if abs(math.hypot(u, v - 1.13 * r) - 0.15 * r) < 0.06 * r:
        return True                                        # circulito arriba
    return False


# ---------------------------------------------------------------- pintores de la ropa

def kosode(t):
    """Kimono negro del torso, cruzado en V: adentro de la V se ve el pecho con el tatuaje del circulo y el cordon
    del collar; el borde de la V lleva el cuello blanco del kimono de abajo."""
    if t.cara == "up":
        return hex_(NEGRO2)
    if t.cara != "north":
        return hex_(NEGRO)
    x, y = t.x, t.y
    fondo = CUELLO - 5.6                                   # punta de la V (medio pecho)
    ancho = 0.0 if y < fondo else 1.75 * (y - fondo) / (CUELLO - fondo)
    if abs(x) < ancho:
        if y > CUELLO - 3.3 and abs(abs(x) - 0.62 * (y - (CUELLO - 3.3))) < 0.09:
            return hex_(TINTA)                             # cordon del collar
        if abs(math.hypot(x + 0.95, y - (CUELLO - 4.2)) - 0.48) < 0.08:
            return hex_(TINTA)                             # tatuaje del circulo (pecho izquierdo)
        if abs(x) > ancho - 0.18:
            return hex_(PIEL["s"])                         # sombra del borde del kimono
        return hex_(PIEL["b"])
    if abs(x) < ancho + 0.38:
        return hex_(BLANCO)                                # cuello blanco del kimono de abajo
    return hex_(NEGRO)


MANO = CUELLO - 15.0                                    # punta de los dedos
PUNO, BOLSA = MANO + 2.6, MANO - 1.2                    # final de la manga adelante (muneca) y atras (bolsa)


def brazo(t):
    """Brazo: manga negra del kimono hasta la muneca, despues la mano."""
    if t.y < MANO + 2.9:
        return piel(t)
    return hex_(NEGRO2 if t.cara == "up" else NEGRO)


OBI_ABAJO, OBI_ARRIBA = 24.4, 26.6
OBI_CORDON = 25.5


def obi(t):
    """Obi azul con dos lineas finas de luz (la tela doblada) y el cordon blanco pintado alrededor."""
    if t.cara in ("up", "down"):
        return hex_(AZUL[1])
    y = t.y
    if abs(y - OBI_CORDON) < 0.16:
        return hex_(BLANCO)
    if abs(y - OBI_CORDON) < 0.26:
        return hex_(TELA_B[1])
    if abs(y - (OBI_ABAJO + 0.5)) < 0.07 or abs(y - (OBI_ARRIBA - 0.45)) < 0.07:
        return hex_(AZUL[3])
    return hex_(AZUL[2])


def pantalon(t):
    """Hakama negro: cada 9 texeles un pliegue hondo con el canto iluminado al lado; el ruedo mas oscuro."""
    if t.cara == "down":
        return hex_(TELA_N[0])
    if t.cara == "up":
        return hex_(NEGRO2)
    u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
    c = math.floor(abs(u) * D) % 9
    if c == 0 or t.y < 5.4 + 1.5 / D:
        return hex_(TELA_N[0])
    if c == 1:
        return hex_(TELA_N[2])
    return hex_(NEGRO)


def pierna(t):
    """Calcetas a rayas blancas y negras abajo del hakama."""
    if t.y > 6.6:
        return hex_(NEGRO)
    return hex_(BLANCO if math.floor(t.y * 2.2) % 2 else NEGRO)


def etiqueta(letras=True, borde=TELA_B[1]):
    """Etiqueta de papel (ofuda) blanca con borde gris y 原状回復 escrito hacia abajo en pixel art de 16 x 16."""
    glifos = (PX.LETRA_0, PX.LETRA_1, PX.LETRA_2, PX.LETRA_3)

    def p(t):
        if t.i == 0 or t.i == t.tw - 1 or t.j == 0 or t.j == t.th - 1:
            return hex_(borde)
        if letras:
            k, r = divmod(t.j - 2, 18)
            c = t.i - (t.tw - 16) // 2
            if t.j >= 2 and k < 4 and r < 16 and 0 <= c < 16 and glifos[k][r][c] == "k":
                return hex_(TINTA)
        return hex_(BLANCO)
    return p


def oro(t):
    return hex_(ORO["l"] if t.cara == "up" else ORO["b"])


def plata(t):
    return hex_(PLATA["l"] if t.cara == "up" else PLATA["b"])


# ---------------------------------------------------------------- pelo: un solo campo de mechones

CORONILLA = (0.0, 1.0)
MECHONES = 24
SUBE = (0.0, 0.6, 0.25, 0.9, 0.15, 0.7, 0.35)           # cuanto mas corto es cada mechon (px), en orden fijo
SUBE_FLEQUILLO = {-3: 0.1, -2: 1.75, -1: 1.35, 0: 1.2, 1: 0.25, 2: 0.0}   # el mechon 1 cae sobre el ojo derecho


def mechon(t):
    """Campo de mechones continuo: el angulo alrededor de la coronilla. (numero de mechon, 0..1 a lo ancho)."""
    a = math.atan2(t.x - CORONILLA[0], -(t.z - CORONILLA[1])) + 0.07 * math.sin(t.y * 1.1)
    s = a / (2 * math.pi) * MECHONES
    n = math.floor(s)
    return n, s - n


def pelo(t):
    """Cada mechon: separacion honda, lado en sombra, cuerpo y canto con luz; anillo de brillo frio de anime."""
    n, k = mechon(t)
    if t.cara == "down":
        return hex_(PELO[0])
    i = 0 if k < 0.09 else 1 if k < 0.28 else 2 if k < 0.8 else 3 if k < 0.9 else 2
    if t.cara != "up":
        anillo = TOPE - 1.7 + 0.3 * ((n % 3) - 1) + 0.5 * (k - 0.5)
        if abs(t.y - anillo) < 0.3 and 0.25 < k < 0.85:
            return hex_(PELO[4] if 0.45 < k < 0.65 else PELO[3])
        if t.y < CUELLO + 3.0:
            i = max(0, i - 1)
    return hex_(PELO[i])


def puntas(base, sube=SUBE, punta=1.0):
    """Recorta el borde de abajo de una caja de pelo en puntas alineadas con los mechones."""
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


# ---------------------------------------------------------------- haori blanco y mangas

def tubo_hueco(abajo, arriba, grosor=0.15, tapa=True):
    """Tubo de 4 lados abierto abajo: cara de afuera y forro corrido hacia adentro. Devuelve (malla, caras de afuera)."""
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


HAORI_ABAJO = 6.0                                       # el haori llega a la canilla
SUP = CUELLO - 0.2                                      # alto de los hombros en los delanteros
ABERTURA = (1.7, 2.6)                                   # borde de la abertura: arriba y abajo (x)


def _pincelada(x, y):
    """Marca de tinta en forma de triangulo abierto (como la del haori de la referencia), cerca del ruedo."""
    u, v = x - 4.3, y - 8.6
    if -0.9 < u < 0.9 and abs(v - (0.9 - abs(u) * 1.1)) < 0.13:
        return True                                        # techo del triangulo
    return abs(u + 0.5) < 0.12 and -0.6 < v < 0.3          # palito de abajo


def haori_tela(espalda=False, delantero=0):
    """Tela blanca del haori. espalda: el simbolo grande con su cuerda y la banda negra del cuello. delantero (1
    derecho, -1 izquierdo): la banda negra a lo largo de la abertura y, en el izquierdo, una pincelada abajo."""
    def p(t):
        x, y = t.x, t.y
        if espalda:
            if y > CUELLO + 0.4 - 0.75 and abs(x) < 2.3:
                return hex_(NEGRO)                         # banda del cuello por detras
            if simbolo(x, y - (CUELLO - 5.4), 2.15):
                return hex_(TINTA)
            if abs(x) < 0.09 and CUELLO - 2.8 < y < CUELLO - 0.4:
                return hex_(TINTA)                         # la cuerda del simbolo
        if delantero:
            f = (SUP - y) / (SUP - HAORI_ABAJO)
            borde = ABERTURA[0] + (ABERTURA[1] - ABERTURA[0]) * max(0.0, min(1.0, f))
            if delantero * x - borde < 0.7:
                return hex_(NEGRO)                         # banda negra del cuello, hasta abajo
            if delantero < 0 and _pincelada(-x, y):
                return hex_(TINTA)
        return hex_(BLANCO)
    return p


def haori():
    """Cuerpo del haori: espalda, costados y dos delanteros que bajan casi rectos hasta la canilla, abierto adelante.
    Cada panel con forro azul corrido hacia adentro. Devuelve (malla, pintores)."""
    m = geo.Armador()
    pint = []

    def panel(pts, pintor):
        idx = [m.v(q) for q in pts]
        cx = sum(q[0] for q in pts) / 4
        cz = sum(q[2] for q in pts) / 4
        m.cara(tuple(idx), (cx, 0, cz), "fuera")
        pint.append(pintor)
        largo = max(0.01, math.hypot(cx, cz))
        adentro = [(q[0] - 0.12 * cx / largo, q[1], q[2] - 0.12 * cz / largo) for q in pts]
        m.cara(tuple(m.v(q) for q in adentro), (-cx, 0, -cz), "forro")
        pint.append(color(AZUL[1]))
    C, A = CUELLO, HAORI_ABAJO
    zt_f, zt_b, zb_f, zb_b = -2.15, 2.2, -3.4, 3.5
    xt, xb = 3.85, 5.6
    a0, a1 = ABERTURA
    panel([(-3.8, C + 0.4, zt_b), (3.8, C + 0.4, zt_b), (xb, A, zb_b), (-xb, A, zb_b)], haori_tela(espalda=True))
    panel([(xt, SUP, zt_b), (xt, SUP, zt_f), (xb, A, zb_f), (xb, A, zb_b)], haori_tela())
    panel([(-xt, SUP, zt_f), (-xt, SUP, zt_b), (-xb, A, zb_b), (-xb, A, zb_f)], haori_tela())
    panel([(a0, SUP, zt_f), (xt, SUP, zt_f), (xb, A, zb_f), (a1, A, zb_f)], haori_tela(delantero=1))
    panel([(-xt, SUP, zt_f), (-a0, SUP, zt_f), (-a1, A, zb_f), (-xb, A, zb_f)], haori_tela(delantero=-1))
    return (m.vs, m.caras), pint


MANGA_Z_FRENTE, MANGA_Z_ATRAS = -2.9, 3.3


def manga_kimono(arriba):
    """Manga ancha de kimono (lado derecho): trapecio que se abre hacia afuera y hacia abajo; adelante termina en la
    muneca y atras cuelga mas, como la bolsa del kimono."""
    xi, xo_arriba, xo_abajo = 3.55, 6.7, 9.0
    sup = [(xo_arriba, arriba, 1.7), (xo_arriba, arriba, -1.7), (xi, arriba, -1.7), (xi, arriba, 1.7)]
    inf = [(xo_abajo, BOLSA, MANGA_Z_ATRAS), (xo_abajo, PUNO, MANGA_Z_FRENTE), (xi + 0.05, PUNO, MANGA_Z_FRENTE),
           (xi + 0.05, BOLSA, MANGA_Z_ATRAS)]
    return tubo_hueco(inf, sup)


def manga_tela(s, arriba):
    """Manga blanca: el simbolo chico en la cara de afuera, arriba, y una banda negra fina en la boca de la manga."""
    def p(t):
        k = (t.z - MANGA_Z_FRENTE) / (MANGA_Z_ATRAS - MANGA_Z_FRENTE)
        fin = PUNO + (BOLSA - PUNO) * max(0.0, min(1.0, k))
        if t.cara != "up" and t.y - fin < 0.4:
            return hex_(NEGRO)
        if abs(t.n[0]) > 0.7 and t.n[0] * s > 0 and simbolo(t.z - 0.3, t.y - (arriba - 3.2), 1.05):
            return hex_(TINTA)
        return hex_(BLANCO)
    return p


# ---------------------------------------------------------------- botas

def suela(t):
    """Plataforma blanca gruesa con una franja negra al medio y sombra contra el piso."""
    if t.cara == "down":
        return hex_(TELA_B[0])
    if t.cara == "up":
        return hex_(TELA_B[4])
    if t.y < 0.25:
        return hex_(TELA_B[1])
    if 0.75 < t.y < 1.0:
        return hex_(NEGRO)
    return hex_(BLANCO)


def capellada(t):
    """Capellada negra con un panel blanco a cada costado."""
    if abs(t.n[0]) > 0.7 and -2.6 < t.z < 0.8 and 1.8 < t.y < 2.9 + 0.35 * (t.z + 2.6):
        return hex_(BLANCO)
    return hex_(NEGRO2 if t.cara == "up" else NEGRO)


def bota(p, g, x, s):
    """Bota gruesa: plataforma blanca con franja negra, capellada negra que sube en rampa, puntera y talon blancos,
    cordones de plata y un puno alto con dos correas y hebilla."""
    def cubo(nombre, xa, xb, y1, y2, z1, z2, pintor, rot=None, piv=None):
        a, b = x(xa, xb)
        piv2 = None if piv is None else (s * piv[0], piv[1], piv[2])
        rot2 = None if rot is None else (rot[0], rot[1] * s, rot[2] * s)
        p.caja(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=D)

    blanco, negro = color(BLANCO), color(NEGRO)
    cubo("suela_frente", 0.35, 3.65, 0.0, 0.55, -4.1, -1.1, suela)
    cubo("suela_atras", 0.35, 3.65, 0.0, 0.55, 0.7, 2.6, suela)
    cubo("suela_arco", 0.6, 3.4, 0.3, 0.55, -1.1, 0.7, color(TELA_B[1]))
    cubo("suela_ancha", 0.12, 3.88, 0.55, 1.6, -3.7, 2.3, suela)
    cubo("suela_larga", 0.35, 3.65, 0.55, 1.6, -4.2, 2.7, suela)
    perfil = [(-4.0, 1.6), (-3.9, 2.35), (-3.2, 2.75), (-1.0, 3.55), (-0.75, 3.9), (2.45, 3.9), (2.6, 1.6)]
    malla = geo.extruir_x(perfil, 0.4, 3.6)
    p.malla(g, "capellada", malla if s > 0 else geo.espejo_x(malla), capellada, dens=D)
    cubo("puntera", 0.6, 3.4, 1.6, 2.25, -4.15, -3.45, blanco)
    cubo("talonera", 0.6, 3.4, 1.6, 3.4, 2.5, 2.75, blanco)
    rampa = dict(rot=(-20.0, 0, 0), piv=(2.3, 3.55, -1.0))
    cubo("cordon", 1.4, 2.4, 3.55, 3.67, -3.2, -1.0, plata, **rampa)
    for k, zc in enumerate((-2.7, -1.8)):
        cubo(f"cordon_cruce{k}", 0.8, 3.0, 3.55, 3.65, zc - 0.18, zc + 0.18, plata, **rampa)
    cubo("puno", 0.0, 3.8, 3.6, 5.6, -1.95, 2.3, negro)
    cubo("correa1", -0.05, 3.9, 3.85, 4.25, -2.05, 2.4, blanco)
    cubo("correa2", -0.05, 3.9, 4.75, 5.15, -2.05, 2.4, negro)
    cubo("hebilla", 1.4, 2.3, 4.65, 5.25, -2.25, -2.03, plata)
    cubo("lengueta", 1.1, 2.6, 3.5, 4.4, -2.15, -1.9, negro)


# ---------------------------------------------------------------- katana

def katana(p):
    """Katana metida en el obi del lado izquierdo: el mango adelante y arriba, la vaina hacia atras y abajo."""
    g = "Body/katana"
    giro = dict(rot=(24.0, 0, 0), piv=(-5.05, 25.4, -1.0))

    def trenzado(t):
        if t.cara in ("north", "south"):
            return hex_(NEGRO)
        return hex_(BLANCO if (t.i + t.j) % 6 in (0, 1) and (t.i - t.j) % 6 in (0, 1) else NEGRO)

    def vaina(t):
        if t.cara == "up" and t.i in (1, 2):
            return hex_(TELA_N[3])                         # brillo de la laca
        return hex_(NEGRO2 if t.cara == "up" else NEGRO)
    x1, x2 = -5.35, -4.75
    p.caja(g, "mango", (x1 + 0.02, 25.1, -5.4), (x2 - 0.02, 25.7, -2.1), trenzado, dens=D, **giro)
    p.caja(g, "kashira", (x1, 25.05, -5.6), (x2, 25.75, -5.4), oro, dens=D, **giro)
    p.caja(g, "tsuba", (x1 - 0.3, 24.75, -2.1), (x2 + 0.3, 26.05, -1.85), oro, dens=D, **giro)
    p.caja(g, "vaina", (x1 + 0.03, 25.05, -1.85), (x2 - 0.03, 25.75, 8.4), vaina, dens=D, **giro)
    p.caja(g, "sageo", (x1 - 0.04, 25.0, -1.2), (x2 + 0.04, 25.8, -0.7), color(AZUL[2]), dens=D, **giro)
    p.caja(g, "kojiri", (x1, 25.03, 8.4), (x2, 25.77, 8.8), oro, dens=D, **giro)


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("correctar", altura=40, cabeza=8, torso=(7, 10, 3.5), brazo=(2.8, 2.8), pierna=(3.5, 3.5))
    C, T, L = p.cuello, p.tope, p.lh
    assert (C, T, L) == (CUELLO, TOPE, CADERA)

    # ================================================================ CABEZA y cara
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), sprite({"north": CARA}, PAL_CARA, base=piel), dens=D)

    # ================================================================ PELO negro ordenado
    g = "Head/pelo"
    p.caja(g, "casco_arriba", (-4.35, T - 0.6, -4.35), (4.35, T + 0.7, 4.4), pelo, dens=D)
    p.caja(g, "casco_nuca", (-4.35, C + 0.2, 3.7), (4.35, T - 0.6, 4.4), puntas(pelo, punta=1.3), dens=D)
    for s in (1, -1):
        x1, x2 = sorted((s * 3.7, s * 4.4))
        p.caja(g, f"casco_lado{s}", (x1, C + 0.9, -3.95), (x2, T - 0.6, 3.7), puntas(pelo), dens=D)
        # mechon largo que enmarca la cara, adelante de la oreja
        x1, x2 = sorted((s * 3.55, s * 4.45))
        p.caja(g, f"mechon_cara{s}", (x1, C - 0.6, -4.45), (x2, C + 4.2, -3.6), puntas(pelo, punta=1.4), dens=D)
    p.caja(g, "flequillo", (-4.35, C + 2.6, -4.45), (4.35, T - 0.6, -3.95), puntas(pelo, SUBE_FLEQUILLO, 1.3),
           dens=D)
    # pelito parado arriba, apenas inclinado
    p.caja(g, "pelito", (-0.15, T + 0.7, -0.6), (0.15, T + 2.1, 0.2), pelo, rot=(0, 0, -22),
           piv=(0, T + 0.7, -0.2), dens=D)
    p.caja(g, "pelito_punta", (-0.15, T + 1.7, -0.6), (0.15, T + 2.0, 0.6), pelo, rot=(0, 0, -22),
           piv=(0, T + 0.7, -0.2), dens=D)

    # ================================================================ ARETES largos con etiqueta y borla azul
    g = "Head/aretes"
    for s in (1, -1):
        x1, x2 = sorted((s * 4.45, s * 4.7))
        xm = s * 4.6
        p.caja(g, f"argolla{s}", (x1, C + 2.35, -0.25), (x2, C + 2.85, 0.25), plata, dens=D)
        p.caja(g, f"cadena{s}", (xm - 0.06, C + 1.95, -0.06), (xm + 0.06, C + 2.35, 0.06), plata, dens=D)
        p.plano(g, f"etiqueta{s}", (xm, C + 1.0, -0.35), (xm, C + 1.95, 0.35), etiqueta(letras=False), dens=D)
        p.caja(g, f"borla{s}", (xm - 0.16, C + 0.4, -0.16), (xm + 0.16, C + 1.0, 0.16), color(AZUL[3]), dens=D)

    # ================================================================ TORSO: kimono negro cruzado en V, collar de jade
    p.caja("Body/torso", "kosode", (-3.5, L, -1.75), (3.5, C, 1.75), kosode, dens=D)
    p.caja("Body/collar", "colgante", (-0.45, C - 3.85, -1.98), (0.45, C - 2.95, -1.76),
           sprite({"todas": [".pppp.", "pjjjjp", "pjkkjp", "pjkkjp", "pjjjjp", ".pppp."]},
                  {"p": PLATA["b"], "j": JADE["b"], "k": JADE["s"]}), dens=D)

    # ================================================================ OBI azul con cordon, nudo, borlas y etiqueta
    g = "Body/obi"
    p.caja(g, "obi", (-3.95, OBI_ABAJO, -2.2), (3.95, OBI_ARRIBA, 2.2), obi, dens=D)
    p.caja(g, "nudo", (-1.9, OBI_CORDON - 0.45, -2.55), (-0.9, OBI_CORDON + 0.45, -2.2), color(BLANCO), dens=D)
    for k, (x, largo) in enumerate(((-1.75, 4.6), (-1.15, 3.6))):
        p.caja(g, f"cordon{k}", (x - 0.08, OBI_CORDON - largo, -2.5), (x + 0.08, OBI_CORDON - 0.4, -2.36),
               color(BLANCO), dens=D)
        p.caja(g, f"borla{k}", (x - 0.22, OBI_CORDON - largo - 1.3, -2.58), (x + 0.22, OBI_CORDON - largo, -2.28),
               color(AZUL[3]), dens=D)
    p.plano(g, "etiqueta", (-3.4, OBI_ABAJO - 6.2, -2.95), (-1.9, OBI_ABAJO + 0.1, -2.95), etiqueta(),
            dens=DENS_LETRAS)

    # ================================================================ HAORI blanco largo
    malla, pintores = haori()
    p.malla("Body/haori", "haori", malla, pintores, dens=D)
    z_atras = 2.2 + 1.3 * (C + 0.4 - 18.0) / (C + 0.4 - HAORI_ABAJO) + 0.08
    p.plano("Body/haori", "etiqueta_espalda", (-0.75, 15.3, z_atras), (0.75, 21.6, z_atras), etiqueta(),
            rot=(-2.8, 0, 0), piv=(0, 21.6, z_atras), dens=DENS_LETRAS)

    # ================================================================ BRAZOS con manga de kimono blanca
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.5, s * 6.3))
        p.caja(f"{hueso}/brazo", "brazo", (x1, MANO, -1.4), (x2, C, 1.4), brazo, dens=D)
        p.caja(f"{hueso}/anillo", "anillo", (x1 - 0.1, MANO + 1.2, -1.5), (x2 + 0.1, MANO + 1.55, 1.5), plata, dens=D)
        arriba = C + 0.3
        malla, n_fuera = manga_kimono(arriba)
        if s < 0:
            malla = geo.espejo_x(malla)
        pint = [manga_tela(s, arriba)] * n_fuera + [color(AZUL[1])] * (len(malla[1]) - n_fuera)
        p.malla(f"{hueso}/manga", "manga", malla, pint, dens=D)

    # ================================================================ KATANA a la izquierda
    katana(p)

    # ================================================================ HAKAMA ancho, calcetas y BOTAS
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"

        def x(a, b):
            return sorted((s * a, s * b))
        a, b = x(0.1, 3.6)
        p.caja(f"{hueso}/pierna", "pierna", (a, 3.8, -1.75), (b, L, 1.75), pierna, dens=D)
        cintura = [(3.85, OBI_ABAJO + 0.2, 2.35), (3.85, OBI_ABAJO + 0.2, -2.35), (0.05, OBI_ABAJO + 0.2, -2.35),
                   (0.05, OBI_ABAJO + 0.2, 2.35)]
        ruedo = [(5.2, 5.4, 3.0), (5.2, 5.4, -3.0), (0.45, 5.4, -3.0), (0.45, 5.4, 3.0)]
        malla = geo.tronco(ruedo, cintura)
        p.malla(f"{hueso}/pantalon", "hakama", malla if s > 0 else geo.espejo_x(malla), pantalon, dens=D)
        bota(p, f"{hueso}/bota", x, s)
    return p
