"""
LA BRUMA (version 7, en cubos): el espectro armado como en Blockbench, solo con cubos (nada de mallas). La tela
desgarrada no sale de geometria complicada sino de muchas tiras planas con una textura recortada (alpha).
  ESQUELETO delgado: torso 4x8x2 inclinado 15 grados adelante y 6 de lado (encorvado); brazos de dos tramos (1x6x1),
    cada tramo en su grupo con el pivote en la articulacion: el derecho extendido hacia adelante y arriba, el
    izquierdo doblado. La cabeza se va mas adelante y abajo.
  CAPUCHA de 4 placas de 0.5 de grueso (techo, dos lados y atras) alrededor del craneo, nada de cono; el techo cae
    por delante y deja la orilla baja sobre la cara. Adentro y el craneo: negro puro, sin borde ni brillo.
  MANOS de hueso grandes, en garra: palma 1.5x2x0.5 y dedos de 3 falanges de 0.4x1.5x0.4 (cada una en su grupo, con
    el pivote en el nudillo), mas el pulgar.
  TELA: 30 tiras planas (0.8 a 2.5 de ancho, 4 a 18 de largo, 0.1 a 0.2 de grueso) colgadas del torso, los hombros
    y los antebrazos. Las largas van en 2 o 3 tramos, cada tramo en un grupo hijo del anterior con el pivote en su
    orilla de arriba. Cada una con su largo, ancho y giro (disparejas, con huecos entre ellas); cuelgan con la
    gravedad aunque el cuerpo este inclinado, y las de atras se van para atras como si avanzara. No hay pies: las de
    abajo acaban bajo el cuerpo.
Textura de 128x128 con alpha (en el juego va con render cutout / alpha test, sin descartar caras). Cada tira tiene
su propia zona (sus dos caras grandes comparten la zona, la de atras volteada, asi los hoyos coinciden): degradado
de gris oscuro arriba a casi negro abajo, hilos verticales de 1 texel un tono mas claros u oscuros, el ruedo
deshilachado en los ultimos 3 a 6 texeles (mas hueco entre mas abajo, puntas de 1 o 2 texeles), algunos agujeros
sueltos y orillas mordidas. Los cantos (el grueso) van del tono mas oscuro, solo donde hay tela. 8 colores en total.
Medidas en px (16 por bloque, 2 texeles por px); el frente es -Z y su derecha +X. Solo modelo (sin animaciones).
"""

import math
import random

from ..luz import rot_matriz
from ..modelo import Modelo, tam_cara
from ..textura import TRANSPARENTE, hex_a_rgba

D = 2                                     # texeles por px
LADO_ATLAS = 128

# --- paleta: 8 colores
HILO, C1, C2, C3, C4 = "#353A40", "#2A2E33", "#1F2226", "#16181B", "#0E0F11"
RAMPA = (HILO, C1, C2, C3, C4)            # de claro a casi negro (C1 arriba de cada tira, C4 abajo)
NEGRO = "#000000"
HUESO_CLARO, HUESO_OSCURO = "#9A9384", "#5E594F"
_RGBA = {h: hex_a_rgba(h) for h in RAMPA + (NEGRO, HUESO_CLARO, HUESO_OSCURO)}

# --- esqueleto (coordenadas de reposo; el torso se inclina con el giro de su grupo)
BASE = 18.0                               # abajo del torso
HOMBRO_X, HOMBRO_Y = 2.4, BASE + 7.2
CUELLO = (0.0, BASE + 8.0, 0.0)
GIRO_TORSO = (-15.0, 0.0, 6.0)            # 15 adelante, 6 de lado (hacia su izquierda)
GIRO_CABEZA = (4.0, -12.0, -4.0)          # la cara al frente aunque el torso se incline, mirando hacia la mano
ADELANTE_CABEZA = 1.0                     # la cabeza salida hacia adelante (encorvado)
# brazos: (hombro, codo, muneca) giros de cada grupo
BRAZO_D = ((118.0, -18.0, 0.0), (6.0, 0.0, 4.0), (-28.0, 0.0, 0.0))      # extendido adelante y arriba
BRAZO_I = ((35.0, 0.0, -12.0), (75.0, 0.0, 10.0), (-35.0, 0.0, 0.0))      # doblado
# dedos: (abanico rz, giro de cada falange rx) por dedo; negativo = se cierra hacia la palma
DEDOS_D = ((-12.0, (-18.0, -30.0, -34.0)), (-4.0, (-22.0, -34.0, -38.0)), (4.0, (-16.0, -28.0, -40.0)),
           (12.0, (-24.0, -36.0, -30.0)))
DEDOS_I = ((-10.0, (-38.0, -48.0, -40.0)), (-3.0, (-44.0, -52.0, -36.0)), (5.0, (-36.0, -50.0, -44.0)),
           (11.0, (-42.0, -46.0, -38.0)))

# --- tiras: (nombre, padre, ancla, cara hacia, ancho, tramos, abre, ladea, tuerce, dobleces, grueso, agujeros)
#   padre: "torso" (ancla en px desde abajo-centro del torso), "brazo_d/i" (desde el hombro), "antebrazo_d/i" (desde
#   la muneca); cara hacia: a donde mira su cara plana (0 adelante, 90 su derecha, 180 atras, 270 su izquierda);
#   abre: cuanto se separa la punta hacia afuera; ladea: hacia un lado; tuerce: sobre su largo; dobleces: el giro de
#   cada tramo despues del primero (positivo: sigue abriendo).
TIRAS = (
    # al frente
    ("t01", "torso", (-1.3, 7.0, -1.05), -12, 2.3, (5.5, 5.0, 4.5), 4, -3, 8, (3, -2), 0.15, False),
    ("t02", "torso", (0.4, 5.6, -1.05), 6, 1.6, (6.0, 5.0), 2, 4, -10, (5,), 0.10, True),
    ("t03", "torso", (1.5, 6.8, -1.05), 22, 2.5, (5.0, 4.5, 5.0), 7, 2, 4, (-3, 4), 0.18, True),
    ("t04", "torso", (-1.0, 2.6, -1.05), -4, 0.8, (5.5, 4.5), 1, -6, 12, (-4,), 0.12, False),
    ("t05", "torso", (1.4, 1.0, -1.05), 30, 1.5, (6.0, 5.5), 5, 7, -6, (6,), 0.15, True),
    # su lado derecho
    ("t06", "torso", (2.05, 7.6, -0.3), 95, 2.5, (5.0, 4.0), 9, 0, -15, (4,), 0.20, False),
    ("t07", "torso", (2.05, 4.0, 0.4), 82, 1.4, (6.0, 6.0, 4.0), 6, -4, 10, (-4, 3), 0.12, True),
    ("t08", "torso", (2.05, 1.2, -0.5), 105, 1.9, (4.5,), 15, 6, 0, (), 0.15, False),
    # atras: se van para atras como si avanzara
    ("t09", "torso", (1.4, 7.7, 1.05), 165, 2.2, (6.0, 6.0, 6.0), 28, 6, -8, (10, 14), 0.18, True),
    ("t10", "torso", (0.2, 6.4, 1.05), 188, 1.6, (5.5, 5.5, 5.0), 34, -4, 6, (12, 8), 0.15, False),
    ("t11", "torso", (-1.2, 7.4, 1.05), 205, 2.5, (6.0, 6.0, 5.5), 24, -8, -12, (16, 14), 0.20, True),
    ("t12", "torso", (0.9, 3.5, 1.05), 176, 1.0, (5.0, 5.0), 40, 3, 10, (6,), 0.10, False),
    ("t13", "torso", (-0.5, 1.4, 1.05), 196, 1.8, (5.5, 5.0, 4.5), 30, -6, -4, (8, 12), 0.15, True),
    ("t14", "torso", (1.6, 0.6, 1.05), 150, 1.3, (6.5,), 22, 5, 14, (), 0.12, False),
    # su lado izquierdo
    ("t15", "torso", (-2.05, 7.5, 0.2), 262, 2.1, (5.5, 5.0), 12, 3, 8, (6,), 0.15, False),
    ("t16", "torso", (-2.05, 5.0, -0.4), 280, 1.1, (6.0, 6.0, 5.0), 8, -5, -10, (5, 9), 0.10, True),
    ("t17", "torso", (-2.05, 2.5, 0.5), 238, 2.4, (5.5, 5.5, 4.5), 26, -10, 6, (14, 16), 0.18, False),
    ("t18", "torso", (-1.9, 6.4, -1.05), -38, 2.2, (5.0, 4.5), 5, 8, -6, (-3,), 0.12, True),
    # de abajo del torso: acaban bajo el cuerpo (no hay pies)
    ("t19", "torso", (0.1, 0.05, -0.2), -20, 2.0, (6.5, 6.0, 4.5), 2, 3, 20, (2, -3), 0.15, False),
    ("t20", "torso", (0.7, 0.05, 0.5), 160, 2.0, (5.5, 5.5), 16, 4, -14, (8,), 0.20, True),
    ("t21", "torso", (-1.5, 0.05, 0.6), 215, 1.3, (5.5, 5.0, 3.5), 12, -6, 8, (6, 10), 0.12, True),
    # hombros
    ("h01", "brazo_d", (0.0, -3.0, 0.55), 100, 2.4, (5.0, 4.5), 6, 2, 6, (5,), 0.18, False),
    ("h02", "brazo_i", (0.0, -0.8, -0.55), 300, 2.0, (6.5,), 6, -3, -8, (), 0.15, True),
    # mangas: jirones que cuelgan de los antebrazos
    ("m01", "antebrazo_d", (0.0, 5.2, 0.55), 70, 2.2, (5.5, 4.5), 6, 0, 0, (4,), 0.15, True),
    ("m02", "antebrazo_d", (0.55, 3.4, 0.0), 110, 1.4, (7.5,), 3, 5, -8, (), 0.12, False),
    ("m03", "antebrazo_d", (0.0, 1.7, 0.55), 85, 1.8, (4.5,), 9, -4, 10, (), 0.15, False),
    ("m04", "antebrazo_d", (-0.55, 4.3, 0.0), 40, 1.0, (6.0, 5.0), 2, -6, 14, (-3,), 0.10, True),
    ("m05", "antebrazo_i", (0.0, 5.0, 0.55), 250, 2.0, (6.5, 5.0), 8, 3, -6, (6,), 0.18, False),
    ("m06", "antebrazo_i", (-0.55, 2.8, 0.0), 275, 1.2, (5.5,), 5, -4, 12, (), 0.12, True),
    ("m07", "antebrazo_i", (0.0, 1.4, 0.55), 300, 1.6, (4.0,), 12, 6, -10, (), 0.15, False),
)


# ---------------------------------------------------------------- matrices

def _mul(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _tras(A):
    return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))


def _euler(R):
    """Los giros (rx, ry, rz) de Blockbench (R = Z * Y * X) de una matriz de giro."""
    b = math.asin(max(-1.0, min(1.0, -R[2][0])))
    a = math.atan2(R[2][1], R[2][2])
    c = math.atan2(R[1][0], R[0][0])
    return tuple(round(math.degrees(v), 3) for v in (a, b, c))


def _px(v):
    """Texeles de un largo en px."""
    return max(1, int(v * D + 0.5))


# ---------------------------------------------------------------- el atlas: cada cara con su zona, a mano

class Atlas:
    """Zonas de textura pedidas por clave (dos caras con la misma clave comparten zona; 'voltea' la pone al reves
    en u, para que la cara de atras de una tira coincida con la de adelante) y repartidas en estantes."""

    def __init__(self, lado=LADO_ATLAS):
        self.lado = lado
        self.piezas = {}
        self.usos = []

    def pedir(self, cubo, cara, clave, w, h, voltea=False):
        w, h = max(1, int(w)), max(1, int(h))
        if self.piezas.setdefault(clave, (w, h)) != (w, h):
            raise ValueError(f"la zona {clave} se pidio de dos tamanos")
        self.usos.append((cubo, cara, clave, voltea))

    def repartir(self):
        orden = sorted(self.piezas, key=lambda k: (-self.piezas[k][1], -self.piezas[k][0], str(k)))
        x = y = alto = 0
        pos = {}
        for k in orden:                                    # 1 texel transparente entre zonas
            w, h = self.piezas[k]
            if x + w > self.lado:
                y, x, alto = y + alto + 1, 0, 0
            pos[k] = (x, y)
            x, alto = x + w + 1, max(alto, h)
        if y + alto > self.lado:
            raise RuntimeError(f"no cabe en {self.lado}x{self.lado}: {y + alto} de alto")
        for c, cara, k, voltea in self.usos:
            (u, v), (w, h) = pos[k], self.piezas[k]
            c.uv = c.uv or {}
            c.uv[cara] = [u + w, v, u, v + h] if voltea else [u, v, u + w, v + h]


# ---------------------------------------------------------------- texturas

def _imagen_tela(W, H, semilla, tonos=(1, 4), deshilacha=(3, 6), agujeros=False, mordidas=True, recorte=None):
    """Una tira de tela de W x H texeles (fila 0 arriba): indices de RAMPA o None (transparente).
    Degradado de arriba a abajo (bandas que no van parejas), hilos de 1 texel un tono mas claros u oscuros, el
    ruedo deshilachado (puntas de 1 o 2 texeles y mas hueco entre mas abajo), agujeros sueltos a media altura y
    orillas mordidas. recorte(c, r) -> True: ese texel no existe (la forma de la capucha)."""
    rng = random.Random(semilla)
    t0, t1 = tonos
    img = [[0] * W for _ in range(H)]
    corr = [rng.uniform(-0.09, 0.09) for _ in range(W)]
    for r in range(H):
        for c in range(W):
            f = min(0.999, max(0.0, (r + 0.5) / H + corr[c]))
            img[r][c] = t0 + int(f * (t1 - t0 + 1))
    for c in range(W):                                     # hilos
        for _ in range(rng.choice((0, 1, 1, 2))):
            r0 = rng.randrange(0, max(1, H - 2))
            largo = rng.randint(2, max(2, H // 2))
            d = rng.choice((-1, 1))
            for r in range(r0, min(H, r0 + largo)):
                if rng.random() < 0.88:
                    img[r][c] = max(0, min(4, img[r][c] + d))
    if deshilacha:                                         # el ruedo
        F = max(2, min(rng.randint(*deshilacha), H // 3))
        corte = []
        while len(corte) < W + 3:
            corte += [rng.choice((0, 0, 1))] * rng.choice((1, 1, 2))            # una punta de 1 o 2 texeles
            corte += [rng.randint(max(2, F - 2), F) for _ in range(rng.choice((1, 1, 2)))]
        s0 = rng.randrange(0, 3)
        corte = corte[s0:s0 + W]
        for c in range(W):
            for r in range(H - corte[c], H):
                img[r][c] = None
            for r in range(H - F, H - corte[c]):           # mas hueco entre mas abajo
                u = (r - (H - F) + 1) / F
                if rng.random() < 0.6 * u ** 1.6 * (0.5 if corte[c] <= 1 else 1.0):
                    img[r][c] = None
        for r in range(H - F, H):                          # sin pelusa suelta: nada colgando del aire
            for c in range(W):
                if img[r][c] is None:
                    continue
                arriba = r > 0 and img[r - 1][c] is not None
                lados = (c > 0 and img[r][c - 1] is not None) or (c < W - 1 and img[r][c + 1] is not None)
                if not arriba and not lados:
                    img[r][c] = None
    if mordidas and W > 1:                                 # orillas que no van derechas
        p = 0.05 if W <= 2 else 0.08
        for r in range(2, H - 3):
            for c in (0, W - 1):
                if rng.random() < p + 0.05 * r / H:
                    img[r][c] = None
    if agujeros:                                           # agujeros sueltos a media altura
        for _ in range(rng.randint(2, 5)):
            r = rng.randint(int(H * 0.3), max(int(H * 0.3), int(H * 0.7)))
            c = rng.randrange(0, W)
            img[r][c] = None
    if recorte:
        for r in range(H):
            for c in range(W):
                if recorte(c, r):
                    img[r][c] = None
    return [[None if k is None else RAMPA[k] for k in fila] for fila in img]


def _pintor_lamina(img, fila0, desde, hasta, ea, eb, caras_tela, cara_adentro=None, cantos=None):
    """Pinta una placa (o un tramo de tira): el texel (columna, fila) sale de su posicion en el cubo, asi las dos
    caras grandes y los cantos ven el mismo hoyo. ea: eje de las columnas (desde su minimo); eb: el de las filas
    (desde su maximo). caras_tela: las caras con la textura; cara_adentro: la de adentro (negro donde hay tela);
    cantos: {cara: color} del grueso (por omision el tono mas oscuro), solo donde la orilla tiene tela."""
    W = len(img[0])
    sa, sb = hasta[ea] - desde[ea], hasta[eb] - desde[eb]
    filas = _px(sb)
    cantos = cantos or {}

    def pintor(t):
        p = (t.x, t.y, t.z)
        c = min(W - 1, max(0, int((p[ea] - desde[ea]) / sa * W)))
        r = min(filas - 1, max(0, int((hasta[eb] - p[eb]) / sb * filas)))
        col = img[fila0 + r][c]
        if col is None:
            return TRANSPARENTE
        if t.cara in caras_tela:
            return _RGBA[col]
        if t.cara == cara_adentro:
            return _RGBA[NEGRO]
        return _RGBA[cantos.get(t.cara, C4)]
    return pintor


def _pintor_solido(por_cara):
    """por_cara: {cara: funcion(t) -> color hex} (o un color); lo que falte, el tono mas oscuro."""
    def pintor(t):
        f = por_cara.get(t.cara, C4)
        return _RGBA[f(t) if callable(f) else f]
    return pintor


def _solido(m, atlas, hueso, nombre, desde, hasta, por_cara, caras=None, rot=None, origen=None):
    c = m.cubo(hueso, nombre, desde, hasta, _pintor_solido(por_cara), rot=rot, origen=origen, caras=caras, dens=D,
               luz=False)
    for cara in c.caras:
        w, h = tam_cara(c.desde, c.hasta, cara)
        atlas.pedir(c, cara, (nombre, cara), _px(w), _px(h))
    return c


# ---------------------------------------------------------------- piezas

def esqueleto(m, atlas):
    """Torso, craneo y brazos (cubos delgados oscuros: casi no se ven bajo la tela)."""
    torso = "raiz/torso"
    m.pivotes["raiz"] = (0.0, 0.0, 0.0)
    m.pivotes[torso] = (0.0, BASE, 0.0)
    m.giros[torso] = GIRO_TORSO

    def fibras(t):                                         # casi negro: se lee como la sombra adentro del manto
        k = t.i * 7 + 3 + 31 * ("north", "south", "east", "west").index(t.cara)
        return C3 if random.Random(k).random() < 0.3 else C4
    _solido(m, atlas, torso, "torso", (-2.0, BASE, -1.0), (2.0, BASE + 8.0, 1.0),
            {k: fibras for k in ("north", "south", "east", "west")})
    cabeza = f"{torso}/cabeza"
    m.pivotes[cabeza] = CUELLO
    m.giros[cabeza] = GIRO_CABEZA
    za = -ADELANTE_CABEZA
    _solido(m, atlas, cabeza, "craneo", (-1.5, BASE + 8.4, -2.2 + za), (1.5, BASE + 11.9, 0.8 + za),
            {k: NEGRO for k in ("north", "south", "east", "west", "up", "down")})
    for lado, giros in (("d", BRAZO_D), ("i", BRAZO_I)):
        s = 1 if lado == "d" else -1
        x = s * HOMBRO_X
        hombro, codo, muneca = HOMBRO_Y, HOMBRO_Y - 6.0, HOMBRO_Y - 12.0
        g1 = f"{torso}/brazo_{lado}"
        g2 = f"{g1}/antebrazo_{lado}"
        g3 = f"{g2}/mano_{lado}"
        for g, y, giro in ((g1, hombro, giros[0]), (g2, codo, giros[1]), (g3, muneca, giros[2])):
            m.pivotes[g] = (x, y, 0.0)
            m.giros[g] = giro
        _solido(m, atlas, g1, f"brazo_{lado}", (x - 0.5, codo, -0.5), (x + 0.5, hombro, 0.5),
                {"north": C4, "south": C4, "east": C4, "west": C4})

        def antebrazo(t, muneca=muneca):                   # la muneca ya es hueso
            if t.y < muneca + 1.2:
                return HUESO_CLARO if t.cara == "north" else HUESO_OSCURO
            return C4
        _solido(m, atlas, g2, f"antebrazo_{lado}", (x - 0.5, muneca, -0.5), (x + 0.5, codo, 0.5),
                {k: antebrazo for k in ("north", "south", "east", "west")})
        mano(m, atlas, g3, lado, x, muneca)


def mano(m, atlas, g, lado, x, muneca):
    """Palma 1.5x2x0.5 (el dorso a -Z, la palma a +Z: los dedos se cierran hacia +Z) y 4 dedos de 3 falanges de
    0.4x1.5x0.4, cada falange en un grupo hijo de la anterior con el pivote en su nudillo; el pulgar de 2 falanges."""
    s = 1 if lado == "d" else -1
    abajo = muneca - 2.0

    def palma_dorso(t):
        return C4 if t.y < abajo + 0.5 else (HUESO_OSCURO if t.i in (0, t.tw - 1) else HUESO_CLARO)

    def palma_dentro(t):
        return C4 if t.y < abajo + 0.5 else HUESO_OSCURO
    _solido(m, atlas, g, f"palma_{lado}", (x - 0.75, abajo, -0.25), (x + 0.75, muneca, 0.25),
            {"north": palma_dorso, "south": palma_dentro, "east": HUESO_OSCURO, "west": HUESO_OSCURO, "down": C4})

    def falange(t, punta=False):
        if t.cara == "up":
            return C4
        if t.cara == "down":
            return HUESO_OSCURO if punta else C4
        if t.j == 0:                                        # sombra del nudillo
            return C4
        return HUESO_CLARO if t.cara == "north" else HUESO_OSCURO
    dedos = DEDOS_D if lado == "d" else DEDOS_I
    for k, (abanico, curvas) in enumerate(dedos):
        xd = x + (-0.56 + 0.373 * k) * s
        padre, y = g, abajo
        for f, curva in enumerate(curvas):
            nombre = f"{lado}_dedo{k + 1}" + "abc"[f] if f else f"{lado}_dedo{k + 1}"
            grupo = f"{padre}/{nombre}"
            m.pivotes[grupo] = (xd, y, 0.0)
            m.giros[grupo] = (curva, 0.0, abanico * s if f == 0 else 0.0)
            punta = f == len(curvas) - 1
            _solido(m, atlas, grupo, f"{nombre}_hueso", (xd - 0.2, y - 1.5, -0.2), (xd + 0.2, y, 0.2),
                    {cara: (lambda t, p=punta: falange(t, p)) for cara in ("north", "south", "east", "west", "up",
                                                                           "down")})
            padre, y = grupo, y - 1.5
    # el pulgar: del lado de adentro (hacia el cuerpo cuando el brazo cuelga con la palma atras)
    xp = x - 0.65 * s
    padre, y = g, muneca - 0.7
    for f, (rx, rz) in enumerate(((-20.0, -40.0), (-32.0, 0.0))):
        nombre = f"{lado}_pulgar" + ("b" if f else "")
        grupo = f"{padre}/{nombre}"
        m.pivotes[grupo] = (xp, y, 0.05)
        m.giros[grupo] = (rx, 0.0, rz * s)
        _solido(m, atlas, grupo, f"{nombre}_hueso", (xp - 0.2, y - 1.3, -0.15), (xp + 0.2, y, 0.25),
                {cara: (lambda t, p=(f == 1): falange(t, p)) for cara in ("north", "south", "east", "west", "up",
                                                                         "down")})
        padre, y = grupo, y - 1.3


def capucha(m, atlas):
    """4 placas de 0.5 alrededor del craneo: el techo cae por delante (orilla baja sobre la cara), los lados se
    abren abajo y se recortan en diagonal por delante, la de atras se va hacia la espalda. Adentro, negro."""
    g = "raiz/torso/cabeza"
    y0 = BASE + 8.0
    placas = (
        # nombre, desde, hasta, giro, origen, eje fino, ea, eb, cara de tela, cara de adentro, recorte
        ("capucha_techo", (-2.25, y0 + 4.0, -3.8), (2.25, y0 + 4.5, 1.6), (-12.0, 0.0, 0.0), (0.0, y0 + 4.25, 1.6),
         0, 2, "up", "down", None),
        ("capucha_d", (1.8, y0 - 1.4, -3.2), (2.3, y0 + 4.4, 1.6), (0.0, 6.0, 8.0), (2.05, y0 + 4.4, -0.8),
         2, 1, "east", "west", "frente"),
        ("capucha_i", (-2.3, y0 - 2.0, -3.0), (-1.8, y0 + 4.4, 1.7), (0.0, -5.0, -6.0), (-2.05, y0 + 4.4, -0.65),
         2, 1, "west", "east", "frente"),
        ("capucha_atras", (-2.2, y0 - 2.8, 1.4), (2.4, y0 + 4.4, 1.9), (-14.0, 0.0, 0.0), (0.1, y0 + 4.4, 1.65),
         0, 1, "south", "north", None),
    )
    za = -ADELANTE_CABEZA
    for k, (nombre, desde, hasta, giro, origen, ea, eb, tela, adentro, recorte) in enumerate(placas):
        desde, hasta, origen = ((p[0], p[1], p[2] + za) for p in (desde, hasta, origen))
        W, H = _px(hasta[ea] - desde[ea]), _px(hasta[eb] - desde[eb])
        if nombre == "capucha_techo":                     # filas de atras (0) a la orilla de enfrente
            img = _imagen_tela(W, H, 700 + k, tonos=(1, 2), deshilacha=(2, 3), mordidas=False,
                               recorte=_esquinas(W, H, 0.45, (True, True, False, False)))
        else:
            redondo = _esquinas(W, H, 0.42, (False, True, False, False) if recorte == "frente" else
                                (True, True, False, False))           # lados: la nuca redonda; atras: los hombros
            cortar = redondo
            if recorte == "frente":                       # la boca de la capucha: diagonal mordida abajo adelante
                rr = random.Random(900 + k)
                ruido = [rr.randint(0, 1) for _ in range(H)]

                def cortar(c, r, H=H, ruido=ruido, redondo=redondo):
                    return (r > H * 0.5 and c < (r - H * 0.5) * 0.9 + ruido[r]) or redondo(c, r)
            img = _imagen_tela(W, H, 700 + k, tonos=(1, 3), deshilacha=(3, 5), agujeros=(k == 3), recorte=cortar)
        cantos = {"north": NEGRO}                          # nada de borde claro en la boca de la capucha
        quitar = {"capucha_techo": (), "capucha_atras": ("down",)}.get(nombre, ("down",))
        caras = tuple(c for c in ("north", "south", "east", "west", "up", "down") if c not in quitar)
        c = m.cubo(g, nombre, desde, hasta, _pintor_lamina(img, 0, desde, hasta, ea, eb, (tela,), adentro, cantos),
                   rot=giro, origen=origen, caras=caras, dens=D, luz=False)
        for cara in caras:
            w, h = tam_cara(desde, hasta, cara)
            atlas.pedir(c, cara, (nombre, cara), _px(w), _px(h))


def _esquinas(W, H, k, cuales):
    """Recorte que redondea esquinas de una placa (sin geometria: con la transparencia). cuales: (arriba-izq,
    arriba-der, abajo-izq, abajo-der) con la columna 0 a la izquierda y la fila 0 arriba; k: radio / lado menor."""
    R = max(1.0, k * min(W, H))

    def fuera(c, r):
        for n, (cx, cy) in enumerate(((R - 0.5, R - 0.5), (W - R - 0.5, R - 0.5), (R - 0.5, H - R - 0.5),
                                      (W - R - 0.5, H - R - 0.5))):
            if not cuales[n]:
                continue
            dx = c - cx if (n % 2) else cx - c
            dy = cy - r if n < 2 else r - cy
            if dx > 0 and dy > 0 and dx * dx + dy * dy > R * R:
                return True
        return False
    return fuera


def tiras(m, atlas):
    """Cada tira: un grupo con el pivote en su ancla (orilla de arriba) y uno mas por tramo, hijo del anterior, con
    el pivote en la orilla de arriba de ese tramo. En reposo cuelgan derechas hacia -Y con la cara a -Z; el grupo
    <tira>_eje las orienta en el mundo (con la gravedad, aunque el padre este inclinado), el de la tira la abre y la
    ladea, y los de los tramos la doblan."""
    for k, (nombre, padre, ancla, hacia, ancho, tramos, abre, ladea, tuerce, dobleces, grueso, agujeros) in \
            enumerate(TIRAS):
        if padre == "torso":
            gp = "raiz/torso"
            a = (ancla[0], BASE + ancla[1], ancla[2])
        else:
            lado = padre[-1]
            s = 1 if lado == "d" else -1
            gp = f"raiz/torso/brazo_{lado}" + (f"/antebrazo_{lado}" if padre.startswith("ante") else "")
            y_ref = HOMBRO_Y if padre.startswith("brazo") else HOMBRO_Y - 12.0
            a = (s * HOMBRO_X + ancla[0] * s, y_ref + ancla[1], ancla[2])
        # en el mundo: mira hacia 'hacia' (el grupo fijo <tira>_eje, que compensa el giro del padre para que cuelgue
        # con la gravedad) y luego, ya en su marco, abre hacia su cara, ladea y tuerce (el grupo de la tira: giros
        # chicos, asi se anima sin el bloqueo de cardan de las que miran de lado)
        Rp, _ = m.a_mundo(gp)
        eje = f"{gp}/{nombre}_eje"
        m.pivotes[eje] = a
        m.giros[eje] = _euler(_mul(_tras(Rp), rot_matriz(0.0, -hacia, 0.0)))
        giro_tira = _euler(_mul(rot_matriz(abre, 0.0, 0.0), _mul(rot_matriz(0.0, 0.0, ladea),
                                                                  rot_matriz(0.0, tuerce, 0.0))))
        rr = random.Random(5000 + 31 * k)
        W = _px(ancho)
        largos = [_px(L) for L in tramos]
        img = _imagen_tela(W, sum(largos), 1000 + 37 * k, agujeros=agujeros)
        grupo, y, fila0 = f"{eje}/{nombre}", a[1], 0
        for f, L in enumerate(tramos):
            if f:
                grupo = f"{grupo}/{nombre}{'abc'[f]}"
            m.pivotes[grupo] = (a[0], y, a[2])
            m.giros[grupo] = giro_tira if f == 0 else (float(dobleces[f - 1]), 0.0, round(rr.uniform(-3.0, 3.0), 2))
            desde, hasta = (a[0] - ancho / 2, y - L, a[2] - grueso / 2), (a[0] + ancho / 2, y, a[2] + grueso / 2)
            c = m.cubo(grupo, f"{nombre}{'abc'[f] if f else ''}_tela", desde, hasta,
                       _pintor_lamina(img, fila0, desde, hasta, 0, 1, ("north", "south")),
                       caras=("north", "south", "east", "west"), dens=D, luz=False)
            atlas.pedir(c, "north", (nombre, f), W, largos[f])
            atlas.pedir(c, "south", (nombre, f), W, largos[f], voltea=True)      # la misma zona: los hoyos coinciden
            atlas.pedir(c, "east", (nombre, f, "e"), 1, largos[f])
            atlas.pedir(c, "west", (nombre, f, "w"), 1, largos[f])
            y, fila0 = y - L, fila0 + largos[f]


def construir():
    m = Modelo("bruma")
    m.pivotes = {}
    m.luz = False                                         # tonos planos pintados (y la luz horneada no sabe de giros)
    atlas = Atlas()
    esqueleto(m, atlas)
    capucha(m, atlas)
    tiras(m, atlas)
    atlas.repartir()
    return m
