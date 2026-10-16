"""
LA BRUMA (version 3): un espectro hecho de una sola cobija larguisima que cae sobre un cuerpo flaco que no se ve.
  MANTO: un disco de tela que se suelta encima y se deja caer de verdad (taller/tela.py) sobre la capucha, los
    hombros encorvados, la joroba y los brazos; queda parejo y largo todo alrededor, con pliegues que salen solos y
    un viento suave que lo echa hacia atras (volumen atras sin quedar redondo). Abajo, el ruedo cosido con flecos;
    unos hoyos y rasgaduras de tela vieja.
  CAPUCHA puntiaguda y torcida (la opcion C que escogio el usuario): la tela cae sobre un cono que se dobla hacia
    adelante y a su derecha; adelante se abre la cara y adentro solo hay vacio.
  MANOS de hueso con dedos larguisimos y garras que salen por hoyos de la tela: la derecha se estira hacia
    adelante y la izquierda se encoge frente al pecho.
Textura: bandas limpias (sin ruido ni tramado) que siguen los pliegues: crestas claras, valles oscuros, mas clara
arriba; el ruedo con una costura clara.
Medidas en px (16 por bloque), a tamano real: unos 5 bloques de alto; flota. El frente es -Z, su derecha es +X.
Huesos: raiz / cuerpo / (capucha, manto, faldon_frente, faldon_atras, faldon_d, faldon_i, brazo_d / antebrazo_d /
mano_d, brazo_i / ...). Solo modelo (sin animaciones todavia).
"""

import hashlib
import math
import os

import numpy as np

from .. import malla as geo
from ..kit import Personaje
from ..tela import Capsula, Esfera, Tela
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import voxel
from .khaset import cono, tubo_camino

D = 2                                     # texeles por px (32 por bloque)

# la tela: de lo mas oscuro (valles, abajo) a lo mas claro (crestas, arriba)
RAMPA = ("#04060A", "#080B10", "#0D1217", "#131A21", "#1A232C", "#222D38", "#2C3946", "#384757")
HUESO = {"s": "#5E6355", "b": "#80857A", "l": "#A3A797"}
GARRA = "#1E1C19"
VACIO = "#020304"

# el cuerpo que no se ve (lo que sostiene la tela)
CABEZA = (0.0, 64.0, -2.5)
CAPUCHA = ((0.0, 64.0, -2.5, 6.6), (0.2, 67.5, -3.0, 6.0), (0.6, 71.0, -3.6, 4.8), (1.4, 74.2, -4.6, 3.4),
           (2.5, 77.2, -6.0, 2.2), (3.4, 79.3, -7.2, 1.2), (4.0, 80.5, -8.0, 0.5))
NUCA = ((0.0, 65.0, 1.5), 6.0)                         # volumen atras de la capucha
JOROBA = ((0.0, 55.5, 3.0), 5.4)                       # la espalda encorvada
HOMBROS = ((-7.4, 58.6, -1.2), (7.4, 58.6, -1.2), 3.1)
TORSO = (((0.0, 58.0, -1.0), (0.0, 46.0, 0.2), 5.2), ((0.0, 46.0, 0.2), (0.0, 30.0, 2.4), 4.4))
BRAZO_D = ((6.8, 58.4, -1.8), (10.4, 50.4, -6.6), (11.2, 47.4, -15.2))    # hombro, codo, muneca (se estira)
BRAZO_I = ((-6.8, 58.4, -1.8), (-9.9, 50.4, -3.8), (-5.4, 51.0, -9.2))    # se encoge frente al pecho
RADIO, PASO = 78.0, 2.5                                # la cobija: radio y separacion de los puntos
VIENTO = 0.022
CACHE = os.path.join(os.path.dirname(__file__), "bruma_tela.npz")


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


# ---------------------------------------------------------------- la cobija que cae

def cuerpo():
    """Lo que la tela no atraviesa."""
    c = [Capsula(a[:3], b[:3], a[3], b[3]) for a, b in zip(CAPUCHA, CAPUCHA[1:])]
    c += [Esfera(*NUCA), Esfera(*JOROBA), Capsula(*HOMBROS)]
    c += [Capsula(a, b, r) for a, b, r in TORSO]
    for hombro, codo, muneca in (BRAZO_D, BRAZO_I):
        c += [Capsula(hombro, codo, 2.4, 2.1), Capsula(codo, muneca, 2.1, 1.8)]
    return c


def _viento(P):
    f = np.zeros_like(P)
    k = np.clip((66.0 - P[:, 1]) / 50.0, 0.0, 1.0)
    f[:, 2] = VIENTO * k                                   # hacia atras, mas abajo
    f[:, 1] = VIENTO * 0.15 * k
    return f


def _hoyos(P):
    """Lo que se quita de la tela: la cara y por donde salen las manos."""
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    cara = (z < CABEZA[2] - 2.0) & (np.abs(x - 0.4) < 3.5) & (y > 58.5) & (y < 69.5) & (
        np.hypot(x - CABEZA[0], z - CABEZA[2]) < 11.0)
    m = cara
    for hombro, codo, muneca in (BRAZO_D, BRAZO_I):
        d = np.array(_norm(_menos(muneca, codo)))
        a = np.array(muneca) - d * 1.2
        b = np.array(muneca) + d * 7.0
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0.0, 1.0)
        m |= np.linalg.norm(P - (a + t[:, None] * ab), axis=1) < 3.3
    return m


def _clave():
    datos = repr((CAPUCHA, NUCA, JOROBA, HOMBROS, TORSO, BRAZO_D, BRAZO_I, RADIO, PASO, VIENTO, CABEZA, 3))
    return hashlib.sha1(datos.encode()).hexdigest()[:16]


def manto():
    """La cobija ya caida (se guarda en bruma_tela.npz; se vuelve a simular si cambian las medidas)."""
    punta = CAPUCHA[-1][:3]
    t = Tela((punta[0], punta[1] + 0.8, punta[2]), RADIO, PASO)
    centro = int(np.argmin(np.linalg.norm(t.uv, axis=1)))
    fijo = np.zeros(len(t.P), bool)
    fijo[centro] = True
    t.fijar(fijo)
    clave = _clave()
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        if str(z["clave"]) == clave and len(z["P"]) == len(t.P):
            t.P = z["P"].astype(float)
            t.vivo = z["vivo"].astype(bool)
            t._resortes()
            return t
    c = cuerpo()
    t.simular(c, pasos=520, vueltas=12, viento=_viento)
    t.quitar(_hoyos(t.P))
    t.simular(c, pasos=220, vueltas=12, viento=_viento)
    np.savez_compressed(CACHE, clave=clave, P=t.P.astype(np.float32), vivo=t.vivo)
    return t


# ---------------------------------------------------------------- la textura de la tela

def _tonos_por_punto(t, cuadros):
    """Un valor de luz por punto: luz de arriba y de frente, crestas claras y valles oscuros (contra la tela
    suavizada), mas clara hacia arriba."""
    n = t.normales(cuadros)
    liso = t.suavizada(cuadros, 5)
    pliegue = np.einsum("ij,ij->i", liso - t.P, n)        # > 0: valle
    L = np.array([0.0, 1.0, -0.5])
    L /= np.linalg.norm(L)
    luz = np.clip(n @ L, -0.2, 1.0)
    alto = (t.P[:, 1] - 4.0) / 76.0
    s = 0.40 + 0.26 * luz - np.clip(pliegue * 0.16, -0.22, 0.26) + 0.22 * (alto - 0.5)
    return s


def _orillas(t):
    """1 en los puntos que tienen algun vecino quitado (las orillas de los hoyos de la cara y las manos)."""
    I = t.idx
    e = np.zeros(len(t.P))
    for (di, dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k, (i, j) in enumerate(t.ij + (t.lado // 2)):
            ii, jj = i + di, j + dj
            if 0 <= ii < t.lado and 0 <= jj < t.lado:
                v = I[ii, jj]
                if v >= 0 and not t.vivo[v] and np.hypot(*t.uv[k]) < RADIO - 3:
                    e[k] = 1.0
    return e


# rasgaduras: (angulo en la cobija, desde que radio, ancho en el ruedo)
RASGADAS = tuple((2 * math.pi * _azar(k * 7.1 + 3.0), RADIO - 9.0 - 8.0 * _azar(k * 3.3), 0.6 + 0.5 * _azar(k))
                 for k in range(9))
# hoyos de tela vieja: (u, v, radio) en la cobija
HOYOS = tuple(((44.0 + 26.0 * _azar(k * 2.3)) * math.cos(2 * math.pi * _azar(k * 5.7)),
               (44.0 + 26.0 * _azar(k * 2.3)) * math.sin(2 * math.pi * _azar(k * 5.7)), 0.9 + 1.2 * _azar(k * 9.1))
              for k in range(12))


def _pintor_cuadro(A, S, UV, E):
    """El pintor de un cuadrito de tela: interpola la luz, la posicion en la cobija y la orilla dentro del cuadrito
    (por triangulos) y decide el tono; el ruedo, los flecos, los hoyos y las rasgaduras salen de la posicion en la
    cobija."""
    rampa = [hex_(c) for c in RAMPA]
    tris = []
    for (i0, i1, i2) in ((0, 1, 2), (0, 2, 3)):
        a, b, c = A[i0], A[i1], A[i2]
        v0, v1 = b - a, c - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        den = d00 * d11 - d01 * d01
        tris.append((tuple(a), tuple(v0), tuple(v1), d00, d01, d11, 1.0 / den if abs(den) > 1e-12 else 0.0,
                     (i0, i1, i2)))
    Sl, UVl, El = list(S), [tuple(x) for x in UV], list(E)

    def pintor(t):
        mejor = None
        for a, v0, v1, d00, d01, d11, inv, ids in tris:
            q = (t.x - a[0], t.y - a[1], t.z - a[2])
            d20 = q[0] * v0[0] + q[1] * v0[1] + q[2] * v0[2]
            d21 = q[0] * v1[0] + q[1] * v1[1] + q[2] * v1[2]
            v = (d11 * d20 - d01 * d21) * inv
            w = (d00 * d21 - d01 * d20) * inv
            u = 1.0 - v - w
            peor = min(u, v, w)
            if mejor is None or peor > mejor[0]:
                mejor = (peor, (u, v, w), ids)
        _, (u, v, w), (i0, i1, i2) = mejor
        u, v, w = max(u, 0.0), max(v, 0.0), max(w, 0.0)
        tot = u + v + w or 1.0
        u, v, w = u / tot, v / tot, w / tot
        s = u * Sl[i0] + v * Sl[i1] + w * Sl[i2]
        cu = u * UVl[i0][0] + v * UVl[i1][0] + w * UVl[i2][0]
        cv = u * UVl[i0][1] + v * UVl[i1][1] + w * UVl[i2][1]
        e = u * El[i0] + v * El[i1] + w * El[i2]
        r = math.hypot(cu, cv)
        ang = math.atan2(cv, cu) % (2 * math.pi)
        k = int(s * len(rampa))
        # flecos del ruedo: hilos de medio px, unos mas largos que otros
        if r > RADIO - 2.4:
            hilo = int(ang * r / 0.5)
            if hilo % 2 or r > RADIO - 2.4 + 2.4 * (0.35 + 0.65 * _azar(hilo * 1.3)):
                return TRANSPARENTE
            k -= 1
        elif r > RADIO - 6.0:                              # el ruedo: banda oscura con su costura clara
            k -= 1
            if abs(r - (RADIO - 4.2)) < 0.3 and int(ang * r / 1.1) % 2 == 0:
                k += 3
        # rasgaduras que suben desde el ruedo
        for a0, desde, ancho in RASGADAS:
            if r > desde:
                da = abs(((ang - a0 + math.pi) % (2 * math.pi)) - math.pi) * r
                medio = ancho * (r - desde) / (RADIO - desde)
                if da < medio:
                    return TRANSPARENTE
                if da < medio + 0.5:
                    k -= 2
        # hoyos de tela vieja (con la orilla oscura)
        for hu, hv, hr in HOYOS:
            dd = math.hypot(cu - hu, cv - hv)
            if dd < hr:
                return TRANSPARENTE
            if dd < hr + 0.6:
                k -= 2
        # orillas de los hoyos de la cara y las manos: oscuras y deshilachadas
        if e > 0.45:
            k -= 1
            if e > 0.75 and _azar(int(cu * 2) * 31 + int(cv * 2) * 17) < 0.5:
                return TRANSPARENTE
        return rampa[max(0, min(len(rampa) - 1, k))]
    return pintor


def _hueso_de(c):
    """A que hueso va un cuadrito de tela (por donde quedo): la capucha, el manto o un faldon (para que se mueva)."""
    x, y, z = c
    if y > 59.5 and math.hypot(x - CABEZA[0], z - CABEZA[2]) < 13.0:
        return "raiz/cuerpo/capucha"
    if y < 36.0:
        a = math.degrees(math.atan2(x, -(z - 1.0)))      # 0 adelante, 90 a su derecha
        if -45 <= a < 45:
            return "raiz/cuerpo/faldon_frente"
        if 45 <= a < 135:
            return "raiz/cuerpo/faldon_d"
        if -135 <= a < -45:
            return "raiz/cuerpo/faldon_i"
        return "raiz/cuerpo/faldon_atras"
    return "raiz/cuerpo/manto"


def tela_en_el_modelo(p, t):
    cuadros = t.cuadros()
    S = _tonos_por_punto(t, cuadros)
    E = _orillas(t)
    por_hueso = {}
    for q in cuadros:
        c = t.P[list(q)].mean(axis=0)
        por_hueso.setdefault(_hueso_de(c), []).append(q)
    for hueso, qs in por_hueso.items():
        usados = sorted({i for q in qs for i in q})
        nuevo = {v: k for k, v in enumerate(usados)}
        vs = [tuple(float(c) for c in t.P[i]) for i in usados]
        caras, pintores = [], []
        for q in qs:
            caras.append(tuple(nuevo[i] for i in q))
            ids = list(q)
            pintores.append(_pintor_cuadro(t.P[ids], S[ids], t.uv[ids], E[ids]))
        p.m.malla(hueso, hueso.split("/")[-1], vs, caras, pintores, dens=D, luz=False)


# ---------------------------------------------------------------- lo que asoma

def vacio(p):
    """Adentro de la capucha: el vacio negro (la cabeza y el cono de la capucha, un poco mas chicos que la tela)."""
    camino = [(x, y, z, r * 0.82, r * 0.82) for x, y, z, r in CAPUCHA[:-1]]
    negro = hex_(VACIO)
    p.malla("raiz/cuerpo/capucha", "vacio", tubo_camino(camino, lados=8), lambda t: negro, dens=1, luz=False)
    p.malla("raiz/cuerpo/capucha", "vacio_nuca", geo.loft([(60.0, 0.0, 0.5, 4.4, 4.6), (65.0, 0.0, 0.8, 5.2, 5.4),
                                                           (69.0, 0.0, 0.2, 3.6, 3.8)], 8),
            lambda t: negro, dens=1, luz=False)


def mano(p, g, muneca, adelante, abajo, nombre, cierra=0.0):
    """Mano de hueso: el hueso del antebrazo que asoma, los nudillos y cuatro dedos larguisimos de tres falanges que se
    curvan, con garra negra; y el pulgar. cierra: 0 abierta (para agarrar), 1 encogida."""
    hueso_ = voxel(HUESO, 0.08)
    garra = hex_(GARRA)
    adelante, abajo = _norm(adelante), _norm(abajo)
    lado = _norm(_cruz(adelante, abajo))
    atras = _mas(muneca, adelante, -2.8)
    p.malla(g, f"{nombre}_cubito", tubo_camino([(*atras, 0.6, 0.6), (*muneca, 0.5, 0.5)], lados=5), hueso_, dens=D)
    nudillos = _mas(muneca, adelante, 2.2)
    p.malla(g, f"{nombre}_palma", tubo_camino([(*muneca, 0.7, 0.45), (*nudillos, 1.3, 0.4)], lados=4, giro=45.0),
            hueso_, dens=D)
    for k, dx in enumerate((-1.05, -0.35, 0.35, 1.05)):
        base = _mas(nudillos, lado, dx)
        largo = 2.5 - 0.3 * abs(k - 1.5)
        dobla = 0.22 + 0.6 * cierra
        pts, d = [base], _norm(_mas(adelante, lado, dx * 0.35 * (1 - cierra)))
        for f in range(3):
            d = _norm(_mas(d, abajo, dobla * (f + 1) * 0.6))
            pts.append(_mas(pts[-1], d, largo * (1.0, 0.85, 0.7)[f]))
        for f in range(3):
            r0, r1 = (0.36, 0.3, 0.26)[f], (0.3, 0.26, 0.22)[f]
            p.malla(g, f"{nombre}_dedo{k}_{f}", tubo_camino([(*pts[f], r0, r0), (*pts[f + 1], r1, r1)], lados=4),
                    hueso_, dens=D)
        punta = _mas(pts[-1], _norm(_mas(d, abajo, 0.6)), 1.6)
        p.malla(g, f"{nombre}_garra{k}", cono(pts[-1], punta, 0.24, lados=4), lambda t: garra, dens=D)
    base = _mas(_mas(muneca, adelante, 0.8), lado, -1.0)
    medio = _mas(_mas(base, adelante, 1.3), lado, -0.8)
    punta = _mas(_mas(medio, adelante, 1.2), abajo, 0.6 + 0.6 * cierra)
    p.malla(g, f"{nombre}_pulgar0", tubo_camino([(*base, 0.34, 0.34), (*medio, 0.28, 0.28)], lados=4), hueso_, dens=D)
    p.malla(g, f"{nombre}_pulgar1", tubo_camino([(*medio, 0.28, 0.28), (*punta, 0.22, 0.22)], lados=4), hueso_, dens=D)
    p.malla(g, f"{nombre}_garra_pulgar", cono(punta, _mas(punta, _norm(_menos(punta, medio)), 1.2), 0.2, lados=4),
            lambda t: garra, dens=D)


def manos(p):
    for lado, (hombro, codo, muneca), cierra in (("d", BRAZO_D, 0.0), ("i", BRAZO_I, 0.9)):
        b = f"raiz/cuerpo/brazo_{lado}"
        a = f"{b}/antebrazo_{lado}"
        m = f"{a}/mano_{lado}"
        adelante = _norm(_menos(muneca, codo))
        abajo = _norm(_cruz(_cruz(adelante, (0.0, -1.0, 0.0)), adelante))
        if lado == "i":                                    # la izquierda: la palma hacia el pecho
            abajo = _norm(_mas(abajo, (1.0, 0.0, 0.0), 0.8))
        mano(p, m, _mas(muneca, adelante, 0.8), adelante, abajo, f"mano_{lado}", cierra)
        p.m.pivotes[b] = hombro
        p.m.pivotes[a] = codo
        p.m.pivotes[m] = muneca


def construir():
    p = Personaje("bruma", altura=64)
    p.m.luz = False                                         # la luz ya viene en la textura (bandas por pliegue)
    t = manto()
    tela_en_el_modelo(p, t)
    vacio(p)
    manos(p)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), "raiz/cuerpo": (0.0, 40.0, 0.0), "raiz/cuerpo/capucha": (0.0, 60.0, -2.0),
                        "raiz/cuerpo/manto": (0.0, 58.0, 0.0), "raiz/cuerpo/faldon_frente": (0.0, 36.0, -5.0),
                        "raiz/cuerpo/faldon_atras": (0.0, 36.0, 6.0), "raiz/cuerpo/faldon_d": (5.0, 36.0, 1.0),
                        "raiz/cuerpo/faldon_i": (-5.0, 36.0, 1.0)})
    return p
