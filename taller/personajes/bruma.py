"""
LA BRUMA (version 2, para mob): un espectro como dementor (ver las referencias del usuario). Alto y flaco, flota
inclinado hacia adelante:
  CAPUCHA alta y redondeada que cae sobre la cara, mas clara arriba (le pega la luz); adentro solo el vacio negro
  TUNICA angosta y larga, con pliegues hondos; abajo se deshace en JIRONES larguisimos de tela que se van hacia atras
    (como si avanzara) y en las puntas se vuelven humo (la tela se deshilacha y se transparenta)
  MANTO corto sobre los hombros, roto, con jirones que vuelan detras de la espalda
  BRAZOS largos y huesudos en mangas anchas que cuelgan en tiras; MANOS de hueso con dedos largos y garras: la derecha
    se estira hacia adelante (para agarrar), la izquierda se encoge frente al pecho
  HUMO: hilos de bruma que se enroscan alrededor de los jirones
Medidas en px (16 por bloque), a tamano real: unos 4.8 bloques de la punta de la capucha a la punta de los jirones,
y flota (no tiene piernas). El frente es -Z, su derecha es +X.
Huesos: raiz / cuerpo / (capucha, manto, jirones, humo, brazo_d / antebrazo_d / mano_d, brazo_i / ...).
Solo modelo (sin animaciones todavia).
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..luz import LUZ_SIMETRICA
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER, voxel
from .khaset import cono, tubo_camino
from .pibble import _anillo_oval, _doble, _plegar, _subdividir, _u_bata

D = 2                                     # texeles por px (32 por bloque)

TELA = {"s": "#090C10", "b": "#11171D", "l": "#1C252E"}           # la tunica: negro azulado
TELA_C = {"s": "#121A21", "b": "#1B252E", "l": "#28343F"}         # el manto y las mangas, un poco mas claros
HUMO = {"s": "#2B3743", "b": "#3D4C5A", "l": "#5A6B7B"}           # donde la tela se vuelve humo
CIMA = {"s": "#3A434C", "b": "#525C66", "l": "#727D88"}           # la punta de la capucha, donde le pega la luz
HUESO = {"s": "#5E6355", "b": "#80857A", "l": "#A3A797"}          # las manos
GARRA = "#1E1C19"
VACIO = "#020304"

# la tunica: (y, medio ancho, medio hondo adelante, medio hondo atras, z del centro); de los hombros al ruedo
TUNICA = ((62.0, 5.2, 3.6, 4.0, -2.6), (58.0, 6.4, 4.2, 4.6, -2.4), (52.0, 5.6, 4.0, 4.4, -1.6),
          (46.0, 4.8, 3.8, 4.4, -0.6), (41.0, 5.4, 4.2, 5.0, 0.4), (36.0, 6.2, 4.8, 5.6, 1.6))
# la capucha: (y, medio ancho, hondo adelante, hondo atras, medio ancho de la abertura, z del centro)
CAPUCHA = ((59.0, 6.0, 5.0, 5.2, 0.6, -1.6), (61.5, 6.6, 6.0, 5.6, 2.8, -2.6), (64.5, 6.6, 6.8, 5.8, 3.6, -3.6),
           (67.5, 6.3, 7.2, 5.6, 3.2, -4.4), (70.0, 5.6, 7.0, 5.0, 1.4, -5.0), (72.0, 4.4, 6.0, 4.0, 0.0, -5.2),
           (73.6, 2.8, 4.2, 2.8, 0.0, -5.0), (74.6, 1.0, 1.6, 1.0, 0.0, -4.6), (74.9, 0.15, 0.2, 0.15, 0.0, -4.5))
# el manto de los hombros: (y, medio ancho, hondo adelante, hondo atras, z del centro); abierto abajo
MANTO = ((61.0, 6.8, 4.8, 5.2, -2.4), (57.5, 7.8, 5.4, 6.0, -2.1), (54.5, 8.2, 5.6, 6.4, -1.8))
HOMBRO = 6.6                              # x de los hombros
MANO_D = ((HOMBRO, 59.0, -2.0), (10.2, 50.5, -6.4), (11.0, 47.5, -15.0))     # hombro, codo, muneca (se estira)
MANO_I = ((-HOMBRO, 59.0, -2.0), (-9.8, 50.5, -3.6), (-5.2, 51.0, -9.0))     # se encoge frente al pecho


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _mas(a, b, k=1.0):
    return tuple(a[i] + b[i] * k for i in range(3))


def _menos(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _norm(v):
    largo = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / largo for c in v)


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _suave(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _mezcla(c1, c2, t):
    a, b = hex_(c1), hex_(c2)
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)) + (255,)


# ---------------------------------------------------------------- pintores

def tela_pintor(rampa, oscuro_abajo=None):
    """La tela: bloquecitos de 1 px (voxel) y, si oscuro_abajo=(y0, y1), mas oscura hacia abajo."""
    base = voxel(rampa, 0.05)
    s = hex_(rampa["s"])

    def p(t):
        c = base(t)
        if oscuro_abajo and t.y < oscuro_abajo[1]:
            f = _suave(oscuro_abajo[0], oscuro_abajo[1], t.y)
            if (BAYER[int(t.j) % 4][int(t.i) % 4] + 0.5) / 16 > f:
                return s
        return c
    return p


def jiron_pintor(y0, y1, semilla, humo_desde=0.6, deshecho=0.85, rampa=TELA):
    """Un jiron que se vuelve humo: de la tela (arriba, y0) al humo azulado (abajo, y1); desde 'humo_desde' (fraccion
    del largo) se deshilacha: se transparenta con tramado y se le comen las orillas, hasta 'deshecho' en la punta."""
    tela = voxel(rampa, 0.0)
    humo = voxel(HUMO, 0.0)

    def p(t):
        f = min(1.0, max(0.0, (y0 - t.y) / max(1e-6, y0 - y1)))
        d = (BAYER[int(t.j) % 4][int(t.i) % 4] + 0.5) / 16
        u = (t.i + 0.5) / max(1, t.tw)
        orilla = min(u, 1 - u)
        hilo = 0.5 + 0.5 * math.sin(t.i * 2.7 + semilla * 5.0)          # hebras: unas aguantan mas que otras
        come = _suave(humo_desde, 1.0, f) * deshecho
        if d < come * (0.75 + 0.5 * hilo) or orilla < come * 0.35 * hilo:
            return TRANSPARENTE
        mezcla = _suave(humo_desde * 0.9, 1.05, f) * 0.8
        if d < mezcla:
            return humo(t)
        return tela(t)
    return p


def humo_pintor(semilla):
    """El humo: azul gris, ralo (la mitad de los texeles) y mas ralo en las orillas."""
    humo = voxel(HUMO, 0.1)

    def p(t):
        d = (BAYER[int(t.j) % 4][int(t.i) % 4] + 0.5) / 16
        u = (t.i + 0.5) / max(1, t.tw)
        v = (t.j + 0.5) / max(1, t.th)
        orilla = min(u, 1 - u, v, 1 - v)
        if d < 0.45 + 0.4 * (1 - _suave(0.0, 0.3, orilla)) + 0.08 * math.sin(semilla + t.i):
            return TRANSPARENTE
        return humo(t)
    return p


def capucha_pintor():
    """Por fuera tela, mas clara hacia la punta (le pega la luz); por dentro el vacio."""
    tela = voxel(TELA_C, 0.05)
    cima = voxel(CIMA, 0.0)
    vacio = hex_(VACIO)
    ys = [c[0] for c in CAPUCHA]

    def centro_z(y):
        for a, b in zip(CAPUCHA, CAPUCHA[1:]):
            if a[0] <= y <= b[0]:
                k = (y - a[0]) / (b[0] - a[0])
                return a[5] + (b[5] - a[5]) * k
        return CAPUCHA[0][5] if y < ys[0] else CAPUCHA[-1][5]

    def p(t):
        cz = centro_z(59.0 + (t.y - 59.0) / 0.9) * 0.9
        if t.n[0] * t.x + t.n[2] * (t.z - cz) < 0:              # mira hacia adentro
            return vacio
        f = _suave(63.5, 72.5, t.y) * 3
        d = (BAYER[int(t.j) % 4][int(t.i) % 4] + 0.5) / 16
        nivel = min(3, int(f) + (1 if d < f - int(f) else 0))
        a, b = tela(t), cima(t)
        return tuple(int(a[k] + (b[k] - a[k]) * nivel / 3) for k in range(3)) + (255,)
    return p


# ---------------------------------------------------------------- piezas

def cinta(camino, anchos, lado):
    """Tira de tela (dos caras) a lo largo de un camino de puntos; 'anchos' es el medio ancho en cada punto y 'lado'
    la direccion de lo ancho (se endereza para que siempre quede de canto al camino). La ultima termina en punta."""
    vs, cs = [], []
    n = len(camino)
    for k, (c, w) in enumerate(zip(camino, anchos)):
        a, b = camino[max(0, k - 1)], camino[min(n - 1, k + 1)]
        tng = _norm(_menos(b, a))
        l = _norm(_menos(lado, tuple(tng[i] * sum(lado[j] * tng[j] for j in range(3)) for i in range(3))))
        if k == n - 1 and w <= 1e-6:
            vs.append(c)
        else:
            vs += [_mas(c, l, -w), _mas(c, l, w)]
    filas = (len(vs) - (1 if anchos[-1] <= 1e-6 else 0)) // 2
    for f in range(filas - 1):
        a = 2 * f
        cs.append((a, a + 1, a + 3, a + 2))
    if anchos[-1] <= 1e-6:
        a = 2 * (filas - 1)
        cs.append((a, a + 1, len(vs) - 1))
    return _doble((vs, cs))


def flujo(inicio, fuera, largo, atras, abre, ondula, fase, pasos=7, baja=1.0):
    """El camino de un jiron que cae y se va hacia atras (como si el espectro avanzara): baja 'largo', se va
    'atras' en +Z (cada vez mas), se abre 'abre' hacia afuera y ondula de lado."""
    lado = _norm((-fuera[2], 0.0, fuera[0]))
    pts = []
    for k in range(pasos + 1):
        t = k / pasos
        c = (inicio[0] + fuera[0] * abre * t + lado[0] * ondula * math.sin(t * 4.2 + fase) * t,
             inicio[1] - largo * (t ** baja),
             inicio[2] + atras * t ** 1.7 + fuera[2] * abre * t + lado[2] * ondula * math.sin(t * 4.2 + fase) * t)
        pts.append(c)
    return pts, lado


def tunica(p):
    """El cuerpo: angosto, encorvado hacia adelante, con pliegues que se hacen mas hondos hacia abajo."""
    g = "raiz/cuerpo"
    anillos = []
    for i, (y, mx, mzf, mzb, zc) in enumerate(TUNICA):
        f = (TUNICA[0][0] - y) / (TUNICA[0][0] - TUNICA[-1][0])
        aro = _subdividir(_anillo_oval(0.0, y, zc, mx, mzf, mzb), 2, cerrado=True)
        anillos.append(_plegar(aro, 0.3 + 1.3 * f, piso=i, cerrado=True, centro=(0.0, zc))[0])
    p.malla(g, "tunica", geo.loft_puntos(anillos[::-1], tapa_abajo=False), tela_pintor(TELA, (36.0, 42.0)), dens=D)
    return anillos[-1]


def jirones(p, ruedo):
    """Los jirones del ruedo: uno por cada tramo de la orilla. Los de atras son mas largos y se van mas hacia atras;
    los de adelante caen casi derechos. Encima, una capa de jirones mas largos que salen mas arriba."""
    g = "raiz/cuerpo/jirones"
    n = len(ruedo)
    for k in range(n):
        a, b = ruedo[k], ruedo[(k + 1) % n]
        m = tuple((a[i] + b[i]) / 2 for i in range(3))
        fuera = _norm((m[0], 0.0, m[2] - 1.0))
        atras = max(0.0, fuera[2])                              # 0 adelante, 1 atras
        az = _azar(k * 3.3)
        largo = 19.0 + 10.0 * atras + 6.0 * az
        camino, lado = flujo(m, fuera, largo, 9.0 + 14.0 * atras + 3.0 * az, 1.5 + 1.5 * az, 0.8 + 0.8 * az, k * 1.7)
        w = math.dist(a, b) / 2 * 1.15
        anchos = [w * (1 - (j / 7) ** 1.4) for j in range(8)]
        anchos[-1] = 0.0
        p.malla(g, f"jiron{k}", cinta(camino, anchos, lado), jiron_pintor(m[1], camino[-1][1], k), dens=D)
    # la capa de encima: jirones largos que salen de la tunica a media altura y pasan por fuera del ruedo
    capa = 11
    for k in range(capa):
        ang = 2 * math.pi * (k + 0.5) / capa
        fuera = (math.sin(ang), 0.0, -math.cos(ang))            # k = 0 adelante
        atras = max(0.0, fuera[2])
        az = _azar(k * 7.7 + 1.0)
        y = 42.0 + 3.0 * az
        r = 5.6 + 0.6 * az
        inicio = (fuera[0] * r, y, fuera[2] * (r - 0.3) + 1.6)
        largo = 26.0 + 12.0 * atras + 6.0 * az
        camino, lado = flujo(inicio, fuera, largo, 12.0 + 18.0 * atras, 2.5 + 2.0 * az, 1.2, k * 2.3 + 0.5, pasos=8)
        w = 1.6 + 0.8 * az
        anchos = [w * (1 - (j / 8) ** 1.3) for j in range(9)]
        anchos[-1] = 0.0
        p.malla(g, f"capa{k}", cinta(camino, anchos, lado), jiron_pintor(y, camino[-1][1], k + 40, 0.55, rampa=TELA_C),
                dens=D)


def capucha(p):
    g = "raiz/cuerpo/capucha"
    anillos = []
    for y, mx, mzf, mzb, xo, cz in CAPUCHA:
        y, mx, mzf, mzb, xo, cz = 59.0 + (y - 59.0) * 0.9, mx * 0.88, mzf * 0.88, mzb * 0.88, xo * 0.88, cz * 0.9
        fuera = [(x, yy, z + cz) for x, yy, z in _u_bata(y, mx, mzf, mzb, xo)]
        dentro = [(x, yy, z + cz) for x, yy, z in _u_bata(y, mx, mzf, mzb, xo, 0.6)]
        anillos.append(fuera + dentro[::-1])
    p.malla(g, "capucha", geo.loft_puntos(anillos), capucha_pintor(), dens=D)
    # adentro, el vacio: no tiene cara (una caja negra que llena la capucha)
    p.caja(g, "vacio", (-3.1, 60.0, -6.2), (3.1, 68.0, 0.0), lambda t: hex_(VACIO), dens=1, luz=False)
    # la orilla de la capucha cae en dos picos rotos sobre el pecho
    for s in (1, -1):
        a = (s * 3.0, 60.0, -6.6)
        b = (s * 5.6, 59.0, -5.4)
        camino, lado = flujo(((a[0] + b[0]) / 2, 59.5, -6.0), (s * 0.3, 0.0, -0.9), 7.0, 1.5, 0.6, 0.3, s, pasos=4)
        p.malla(g, f"pico_{'d' if s > 0 else 'i'}", cinta(camino, [1.4, 1.2, 0.9, 0.5, 0.0], (1.0, 0.0, 0.0)),
                jiron_pintor(59.5, camino[-1][1], 90 + s, 0.5, rampa=TELA_C), dens=D)
    p.m.pivotes[g] = (0.0, 60.0, -2.0)


def manto(p):
    """El manto corto de los hombros, abierto abajo y roto en tiras; las de atras vuelan lejos."""
    g = "raiz/cuerpo/manto"
    anillos = []
    for i, (y, mx, mzf, mzb, zc) in enumerate(MANTO):
        aro = _subdividir(_anillo_oval(0.0, y, zc, mx, mzf, mzb), 2, cerrado=True)
        anillos.append(_plegar(aro, 0.3 + 0.5 * i, piso=i + 9, cerrado=True, centro=(0.0, zc))[0])
    p.malla(g, "manto", _doble(geo.loft_puntos(anillos[::-1], tapa_abajo=False, tapa_arriba=False)),
            tela_pintor(TELA_C), dens=D)
    orilla = anillos[-1]
    n = len(orilla)
    for k in range(n):
        a, b = orilla[k], orilla[(k + 1) % n]
        m = tuple((a[i] + b[i]) / 2 for i in range(3))
        fuera = _norm((m[0], 0.0, m[2] + 1.4))
        atras = max(0.0, fuera[2])
        az = _azar(k * 5.1 + 2.0)
        if atras > 0.35:                                        # los de la espalda: vuelan detras
            largo = 16.0 + 14.0 * atras + 6.0 * az
            camino, lado = flujo(m, fuera, largo, 10.0 + 14.0 * atras + 4.0 * az, 1.0 + az, 1.4, k * 1.3, pasos=8,
                                 baja=0.8)
            pasos = 8
        else:                                                   # adelante y a los lados: cortos, caidos
            largo = 4.0 + 5.0 * az
            camino, lado = flujo(m, fuera, largo, 1.0, 0.6, 0.3, k, pasos=4)
            pasos = 4
        w = math.dist(a, b) / 2 * 1.1
        anchos = [w * (1 - (j / pasos) ** 1.3) for j in range(pasos + 1)]
        anchos[-1] = 0.0
        p.malla(g, f"tira{k}", cinta(camino, anchos, lado), jiron_pintor(m[1], camino[-1][1], k + 70, 0.6, rampa=TELA_C),
                dens=D)
    p.m.pivotes[g] = (0.0, 60.0, -2.0)


def manga(p, g, hombro, codo, muneca, nombre):
    """Manga ancha y caida que sigue al brazo (cortes de 7 lados) y cuelga en tiras largas debajo del antebrazo."""
    camino = []
    for k in range(5):
        t = k / 4
        c = _mas(_mas(hombro, _menos(codo, hombro), min(1.0, t * 2)), _menos(muneca, codo), max(0.0, t * 2 - 1))
        r = 2.0 + 1.6 * t
        camino.append((c[0], c[1], c[2], r, r * 0.9))
    camino[-1] = (*_mas(muneca, _norm(_menos(codo, muneca)), 1.4), 3.5, 3.1)
    vs, cs = tubo_camino(camino, lados=7, tapas=(False, False))
    p.malla(g, nombre, _doble((vs, cs)), tela_pintor(TELA_C), dens=D)
    # las tiras que cuelgan de la boca de la manga (cuelgan derecho: la tela pesa)
    boca = vs[-7:]
    for k in range(7):
        a, b = boca[k], boca[(k + 1) % 7]
        m = tuple((a[i] + b[i]) / 2 for i in range(3))
        bajo = (max(q[1] for q in boca) - m[1]) / max(1e-6, max(q[1] for q in boca) - min(q[1] for q in boca))
        az = _azar(k * 2.9 + len(nombre))
        largo = 3.0 + 12.0 * bajo * (0.6 + 0.6 * az)
        fuera = _norm((m[0] - muneca[0], 0.0, m[2] - muneca[2]))
        camino_t, lado = flujo(m, fuera, largo, 3.0 + 4.0 * bajo, 0.5, 0.5, k, pasos=5)
        w = math.dist(a, b) / 2 * 1.1
        anchos = [w * (1 - (j / 5) ** 1.3) for j in range(6)]
        anchos[-1] = 0.0
        p.malla(g, f"{nombre}_tira{k}", cinta(camino_t, anchos, lado),
                jiron_pintor(m[1], camino_t[-1][1], k + 20 + len(nombre), 0.45, rampa=TELA_C), dens=D)


def mano(p, g, muneca, adelante, abajo, nombre, cierra=0.0):
    """Mano de hueso: el hueso del antebrazo que asoma, los nudillos y cuatro dedos larguisimos de tres falanges que se
    curvan, con garra negra; y el pulgar. cierra: 0 abierta (para agarrar), 1 encogida."""
    hueso_ = voxel(HUESO, 0.08)
    garra = hex_(GARRA)
    adelante, abajo = _norm(adelante), _norm(abajo)
    lado = _norm(_cruz(adelante, abajo))
    atras = _mas(muneca, adelante, -2.4)
    p.malla(g, f"{nombre}_cubito", tubo_camino([(*atras, 0.55, 0.55), (*muneca, 0.5, 0.5)], lados=5), hueso_, dens=D)
    nudillos = _mas(muneca, adelante, 2.2)
    p.malla(g, f"{nombre}_palma", tubo_camino([(*muneca, 0.7, 0.45), (*nudillos, 1.3, 0.4)], lados=4, giro=45.0),
            hueso_, dens=D)
    for k, dx in enumerate((-1.05, -0.35, 0.35, 1.05)):
        base = _mas(nudillos, lado, dx)
        largo = 2.4 - 0.3 * abs(k - 1.5)
        dobla = 0.22 + 0.6 * cierra
        pts, d = [base], _norm(_mas(adelante, lado, dx * 0.35 * (1 - cierra)))
        for f in range(3):
            d = _norm(_mas(d, abajo, dobla * (f + 1) * 0.6))
            pts.append(_mas(pts[-1], d, largo * (1.0, 0.85, 0.7)[f]))
        for f in range(3):
            r0, r1 = (0.36, 0.3, 0.26)[f], (0.3, 0.26, 0.22)[f]
            p.malla(g, f"{nombre}_dedo{k}_{f}", tubo_camino([(*pts[f], r0, r0), (*pts[f + 1], r1, r1)], lados=4),
                    hueso_, dens=D)
        punta = _mas(pts[-1], _norm(_mas(d, abajo, 0.6)), 1.5)
        p.malla(g, f"{nombre}_garra{k}", cono(pts[-1], punta, 0.24, lados=4), lambda t: garra, dens=D)
    base = _mas(_mas(muneca, adelante, 0.8), lado, -1.0)
    medio = _mas(_mas(base, adelante, 1.3), lado, -0.8)
    punta = _mas(_mas(medio, adelante, 1.2), abajo, 0.6 + 0.6 * cierra)
    p.malla(g, f"{nombre}_pulgar0", tubo_camino([(*base, 0.34, 0.34), (*medio, 0.28, 0.28)], lados=4), hueso_, dens=D)
    p.malla(g, f"{nombre}_pulgar1", tubo_camino([(*medio, 0.28, 0.28), (*punta, 0.22, 0.22)], lados=4), hueso_, dens=D)
    p.malla(g, f"{nombre}_garra_pulgar", cono(punta, _mas(punta, _norm(_menos(punta, medio)), 1.2), 0.2, lados=4),
            lambda t: garra, dens=D)


def brazos(p):
    for lado, (hombro, codo, muneca), cierra in (("d", MANO_D, 0.0), ("i", MANO_I, 0.9)):
        b = f"raiz/cuerpo/brazo_{lado}"
        a = f"{b}/antebrazo_{lado}"
        m = f"{a}/mano_{lado}"
        manga(p, b, hombro, codo, muneca, f"manga_{lado}")
        adelante = _norm(_menos(muneca, codo))
        abajo = _norm(_cruz(_cruz(adelante, (0.0, -1.0, 0.0)), adelante))
        if lado == "i":                                         # la izquierda: la palma hacia el pecho
            abajo = _norm(_mas(abajo, (1.0, 0.0, 0.0), 0.8))
        mano(p, m, _mas(muneca, adelante, 0.6), adelante, abajo, f"mano_{lado}", cierra)
        p.m.pivotes[b] = hombro
        p.m.pivotes[a] = codo
        p.m.pivotes[m] = muneca


def humo(p):
    """Hilos de bruma: tiras ralas que se enroscan alrededor de los jirones y se van hacia atras."""
    g = "raiz/cuerpo/humo"
    for k in range(9):
        a0 = 2 * math.pi * k / 9 + 0.3
        pts = []
        for j in range(9):
            t = j / 8
            a = a0 + 2.2 * t
            r = 7.5 + 5.0 * t + 1.5 * _azar(k)
            pts.append((math.cos(a) * r, 30.0 - 22.0 * t - 4.0 * _azar(k + 3) + 2.0 * math.sin(t * 5 + k),
                        math.sin(a) * r + 9.0 * t ** 1.5 + 2.0))
        tng = _norm(_menos(pts[-1], pts[0]))
        lado = _norm(_cruz(tng, (0.0, 1.0, 0.0)))
        anchos = [2.6 * math.sin(math.pi * (j + 0.6) / 9.2) for j in range(9)]
        p.malla(g, f"humo{k}", cinta(pts, anchos, _mas(lado, (0.0, 1.0, 0.0), 0.8)), humo_pintor(k), dens=D, luz=False)


def construir():
    p = Personaje("bruma", altura=64)
    p.m.luz_desde = LUZ_SIMETRICA
    p.m.luz_por = "grupo"
    ruedo = tunica(p)
    jirones(p, ruedo)
    manto(p)
    capucha(p)
    brazos(p)
    humo(p)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), "raiz/cuerpo": (0.0, 40.0, 0.0),
                        "raiz/cuerpo/jirones": (0.0, 30.0, 1.0), "raiz/cuerpo/humo": (0.0, 28.0, 1.0)})
    return p
