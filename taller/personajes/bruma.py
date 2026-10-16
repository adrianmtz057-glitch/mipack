"""
LA BRUMA (version 3): un espectro hecho de una sola cobija larguisima echada encima de un cuerpo que no se ve.
  CUERPO (la morfologia que dibujo el usuario): derecho, nada jorobado. La cabeza alta y ovalada, el cuello y el
    torso como un palo flaco, los hombros angostos y los brazos largos y delgados que cuelgan a los lados, un poco
    abiertos, con las manos a la altura de la cadera.
  MANTO: una cobija (un rectangulo de tela con las orillas rotas en picos disparejos) cosida por la linea del centro
    a la cresta de la capucha y soltada para que caiga de verdad (taller/tela.py) sobre la cabeza, los hombros y los
    brazos. Queda ABIERTA al frente (no es una tunica cerrada): por la abertura solo se ve oscuridad. Las MANGAS son
    la misma cobija colgando de los brazos; por eso todo es largo y abajo cuelgan picos asimetricos. Un viento suave
    la echa hacia atras (volumen atras sin quedar redonda).
  CAPUCHA puntiaguda y torcida (la opcion C que escogio el usuario): la cobija cae sobre la cabeza alta y una punta
    que se dobla hacia adelante y a su derecha; la orilla de la cobija enmarca la cara y adentro solo hay vacio.
  MANOS de hueso con dedos larguisimos y garras: la derecha cuelga con los dedos hacia abajo y la izquierda, mas
    abierta, los encoge.
Textura: bandas limpias (sin ruido ni tramado) que siguen los pliegues: crestas claras, valles oscuros, mas clara
arriba; por dentro mas oscura; las orillas deshilachadas y unos hoyos de tela vieja.
Medidas en px (16 por bloque), a tamano real: unos 5.3 bloques de alto; flota. El frente es -Z, su derecha es +X.
Huesos: raiz / cuerpo / (capucha, manto, faldon_frente, faldon_atras, faldon_d, faldon_i, brazo_d / (manga_d,
antebrazo_d / mano_d), brazo_i / ...). Solo modelo (sin animaciones todavia).
"""

import hashlib
import math
import os

import numpy as np

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

# el cuerpo que no se ve (lo que sostiene la tela): derecho y flaco
CABEZA = ((0.0, 69.0, -1.0), (0.0, 76.5, -1.3), 3.8)          # cabeza alta y ovalada: capsula de abajo a arriba
CAPUCHA = ((0.0, 76.5, -1.3, 3.6), (0.5, 80.0, -2.2, 2.7), (1.6, 83.5, -3.5, 1.8), (2.9, 86.4, -5.0, 1.0),
           (4.0, 88.6, -6.6, 0.4))                             # la punta torcida hacia adelante y a su derecha
NUCA = ((0.0, 73.0, 1.4), 4.2)                                 # un poco de volumen atras de la capucha
HOMBROS = ((-4.8, 65.0, -0.5), (4.8, 65.0, -0.5), 2.2)
TORSO = ((0.0, 66.0, -0.5), (0.0, 30.0, 0.0), 2.8)             # el palo
BRAZO_D = ((4.8, 65.0, -0.5), (8.5, 55.0, -1.5), (10.5, 46.0, -3.5))       # hombro, codo, muneca: cuelga
BRAZO_I = ((-4.8, 65.0, -0.5), (-11.5, 56.0, -1.0), (-16.5, 48.5, -4.0))   # mas abierto
GRUESO_BRAZO = (1.5, 1.2)
ANCHO, LARGO = 62.0, 50.0                              # la cobija: medio ancho (x) y medio largo (z)
PICOS_ATRAS, PICOS_LADO = 28.0, 20.0                   # cuanto se meten los picos de la orilla de atras y de los lados
PASO = 2.0                                             # separacion de los puntos de la tela
FRENTE = (0.3, 77.5, -5.3)                             # donde va la orilla de la cobija, sobre la frente
CRESTA = (FRENTE, (1.4, 82.0, -5.0), (4.0, 88.6, -6.6), (2.4, 84.5, -2.0), (0.9, 79.0, 2.4), (0.2, 73.5, 5.6),
          (0.0, 68.0, 4.6))                            # la costura: frente, punta de la capucha, nuca
# las manos agarran la orilla de la cobija: (cuanto de la orilla hay de la frente a la mano, donde la agarran)
AGARRE_D = (33.0, (11.6, 47.0, -4.6))
AGARRE_I = (-34.0, (-17.6, 49.5, -5.2))
VIENTO = 0.018
VUELO = 0.014                                          # que tanto se abre la tela de abajo
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
    c = [Capsula(*CABEZA)]
    c += [Capsula(a[:3], b[:3], a[3], b[3]) for a, b in zip(CAPUCHA, CAPUCHA[1:])]
    c += [Esfera(*NUCA), Capsula(*HOMBROS), Capsula(*TORSO)]
    for hombro, codo, muneca in (BRAZO_D, BRAZO_I):
        c += [Capsula(hombro, codo, GRUESO_BRAZO[0], GRUESO_BRAZO[1]),
              Capsula(codo, muneca, GRUESO_BRAZO[1], GRUESO_BRAZO[1] * 0.9)]
    return c


def _viento(P):
    """Un viento suave hacia atras y la bruma que levanta el vuelo de abajo (lo abre hacia afuera, como campana)."""
    f = np.zeros_like(P)
    k = np.clip((70.0 - P[:, 1]) / 55.0, 0.0, 1.0)
    f[:, 2] = VIENTO * k                                   # hacia atras, mas abajo
    afuera = P[:, [0, 2]] - np.array([0.0, 1.0])
    L = np.maximum(np.linalg.norm(afuera, axis=1), 1e-6)
    abre = VUELO * np.clip((58.0 - P[:, 1]) / 45.0, 0.0, 1.0)
    f[:, 0] += abre * afuera[:, 0] / L
    f[:, 2] += abre * afuera[:, 1] / L
    return f


def _picos(x, n, semilla, alto):
    """Una orilla rota en picos: dientes disparejos (ancho y alto) a lo largo de x (de -1 a 1)."""
    out = np.zeros_like(x, dtype=float)
    for k in range(n):
        c = -1 + 2 * (k + 0.5) / n
        w = 2.0 / n * (0.7 + 0.6 * _azar(k * 3.1 + semilla))
        a = alto * (0.35 + 0.65 * _azar(k * 5.3 + semilla))
        out = np.maximum(out, a * np.clip(1 - np.abs(x - c) / w, 0, 1))
    return out


def _forma(u, v):
    """La cobija en su propio plano (u a lo ancho, v de la frente hacia atras): un rectangulo con las orillas de atras
    y de los lados rotas en picos (distintos de cada lado)."""
    fu = u / ANCHO
    fv = (v + LARGO) / (2 * LARGO) * 2 - 1
    atras = v <= LARGO - PICOS_ATRAS + _picos(fu, 11, 1.0, PICOS_ATRAS)
    lados = np.where(u >= 0, u <= ANCHO - PICOS_LADO + _picos(fv, 7, 8.0, PICOS_LADO),
                     -u <= ANCHO - PICOS_LADO + _picos(fv, 7, 6.0, PICOS_LADO))
    return (v >= -LARGO) & atras & lados


def _en_cresta(d):
    acum = 0.0
    for a, b in zip(CRESTA, CRESTA[1:]):
        L = math.dist(a, b)
        if acum + L >= d:
            t = (d - acum) / L
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
        acum += L
    return CRESTA[-1]


def _manos_tapadas(P):
    """La tela que quedara encima de las manos se quita (las manos siempre se ven)."""
    m = np.zeros(len(P), bool)
    for hombro, codo, muneca in (BRAZO_D, BRAZO_I):
        d = np.array(_norm(_menos(muneca, codo)))
        a = np.array(muneca) + d * 1.4
        b = np.array(muneca) + d * 10.0
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0.0, 1.0)
        m |= np.linalg.norm(P - (a + t[:, None] * ab), axis=1) < 2.4
    return m


def _clave():
    datos = repr((CABEZA, CAPUCHA, NUCA, HOMBROS, TORSO, BRAZO_D, BRAZO_I, GRUESO_BRAZO, ANCHO, LARGO, PICOS_ATRAS,
                  PICOS_LADO, PASO, CRESTA, AGARRE_D, AGARRE_I, VIENTO, VUELO, 7))
    return hashlib.sha1(datos.encode()).hexdigest()[:16]


def manto():
    """La cobija ya caida (se guarda en bruma_tela.npz; se vuelve a simular si cambian las medidas)."""
    t = Tela((0.0, 88.0, FRENTE[2] + LARGO), max(ANCHO, LARGO) + 2.0, PASO, forma=_forma)
    largo_cresta = sum(math.dist(a, b) for a, b in zip(CRESTA, CRESTA[1:]))
    cosida = (np.abs(t.uv[:, 0]) < PASO * 0.6) & (t.uv[:, 1] + LARGO <= largo_cresta)
    a_donde = {int(k): _en_cresta(float(t.uv[k, 1] + LARGO)) for k in np.nonzero(cosida)[0]}
    orilla = t.uv[:, 1] < -LARGO + PASO * 0.6                  # la orilla de adelante de la cobija
    for u, donde in (AGARRE_D, AGARRE_I):                     # la que agarran las manos
        k = int(np.argmin(np.where(orilla, np.abs(t.uv[:, 0] - u), 1e9)))
        a_donde[k] = donde
    fijo = np.zeros(len(t.P), bool)
    fijo[list(a_donde)] = True
    t.fijar(fijo)
    destino = np.array([a_donde[int(k)] for k in np.nonzero(fijo)[0]])
    t.P[fijo] = destino
    t.antes[fijo] = destino
    clave = _clave()
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        if str(z["clave"]) == clave and len(z["P"]) == len(t.P):
            t.P = z["P"].astype(float)
            t.vivo = z["vivo"].astype(bool)
            t._resortes()
            return t
    c = cuerpo()
    t.simular(c, pasos=600, vueltas=12, viento=_viento, a_donde=destino)
    tapadas = _manos_tapadas(t.P) & ~t.fijo
    if tapadas.any():
        t.quitar(tapadas)
        t.simular(c, pasos=160, vueltas=12, viento=_viento, a_donde=destino)
    t.quitar(~t.pegados())                                 # pedacitos que quedaron sueltos
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
    alto = (t.P[:, 1] - 4.0) / 80.0
    return 0.40 + 0.26 * luz - np.clip(pliegue * 0.16, -0.22, 0.26) + 0.22 * (alto - 0.5)


# hoyos de tela vieja: (u, v, radio) en la cobija, lejos de la capucha
HOYOS = tuple(((-40.0 + 80.0 * _azar(k * 2.3)), (-10.0 + 46.0 * _azar(k * 5.7)), 0.8 + 1.0 * _azar(k * 9.1))
              for k in range(10))


def _pintor_cuadro(A, S, UV, B, dentro=False):
    """El pintor de un cuadrito de tela: interpola la luz, la posicion en la cobija y la distancia a la orilla dentro
    del cuadrito (por triangulos) y decide el tono; las orillas se deshilachan y hay unos hoyos. dentro: la cara de
    adentro de la cobija (mas oscura)."""
    rampa = [hex_(c) for c in RAMPA]
    tris = []
    for (i0, i1, i2) in ((0, 1, 2), (0, 2, 3)):
        a, b, c = A[i0], A[i1], A[i2]
        v0, v1 = b - a, c - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        den = d00 * d11 - d01 * d01
        tris.append((tuple(a), tuple(v0), tuple(v1), d00, d01, d11, 1.0 / den if abs(den) > 1e-12 else 0.0,
                     (i0, i1, i2)))
    Sl, UVl, Bl = list(S), [tuple(x) for x in UV], list(B)

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
        b = u * Bl[i0] + v * Bl[i1] + w * Bl[i2]
        k = int(s * len(rampa)) - (3 if dentro else 0)
        # la orilla: se deshilacha (hilos disparejos) y es mas oscura
        if b < 2.0:
            hilo = _azar(int(cu * 2.0) * 7 + int(cv * 2.0) * 13)
            if b < 2.0 * (0.25 + 0.75 * hilo):
                return TRANSPARENTE
            k -= 1
        elif b < 4.0:
            k -= 1
        # hoyos de tela vieja (con la orilla oscura)
        for hu, hv, hr in HOYOS:
            dd = math.hypot(cu - hu, cv - hv)
            if dd < hr:
                return TRANSPARENTE
            if dd < hr + 0.6:
                k -= 2
        return rampa[max(0, min(len(rampa) - 1, k))]
    return pintor


def _hueso_de(c):
    """A que hueso va un cuadrito de tela (por donde quedo): la capucha, las mangas (la tela que cuelga de cada
    brazo), el manto o un faldon (para que se mueva)."""
    x, y, z = c
    if y > 66.5 and math.hypot(x, z + 1.0) < 9.0:
        return "raiz/cuerpo/capucha"
    for lado, (hombro, codo, muneca) in (("d", BRAZO_D), ("i", BRAZO_I)):
        if (x > 6.5 if lado == "d" else x < -6.5) and y > 30.0:
            return f"raiz/cuerpo/brazo_{lado}/manga_{lado}"
    if y < 38.0:
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
    """La cobija en el modelo: por fuera con su luz y, un pelito mas adentro y al reves, la cara de adentro mas
    oscura (en el juego la tela se ve de los dos lados; asi por la abertura y por debajo se ve oscura)."""
    cuadros = t.cuadros()
    S = _tonos_por_punto(t, cuadros)
    B = t.a_la_orilla()
    n = t.normales(cuadros)
    adentro = t.P - n * 0.25
    por_hueso = {}
    for q in cuadros:
        c = t.P[list(q)].mean(axis=0)
        por_hueso.setdefault(_hueso_de(c), []).append(q)
    for hueso, qs in por_hueso.items():
        usados = sorted({i for q in qs for i in q})
        nuevo = {v: k for k, v in enumerate(usados)}
        for capa, P, voltea in (("", t.P, False), ("_dentro", adentro, True)):
            vs = [tuple(float(c) for c in P[i]) for i in usados]
            caras, pintores = [], []
            for q in qs:
                ids = list(q)
                cara = tuple(nuevo[i] for i in q)
                caras.append(tuple(reversed(cara)) if voltea else cara)
                orden = ids[::-1] if voltea else ids
                pintores.append(_pintor_cuadro(P[orden], S[orden], t.uv[orden], B[orden], dentro=voltea))
            p.m.malla(hueso, hueso.split("/")[-1] + capa, vs, caras, pintores, dens=D, luz=False)


# ---------------------------------------------------------------- lo que asoma

def vacio(p):
    """Adentro: el vacio negro (la cabeza alta y el palo del cuerpo, un poco mas chicos que lo que sostiene la tela),
    para que por la cara y por la abertura del frente solo se vea oscuridad."""
    negro = hex_(VACIO)
    (a, b, r) = CABEZA
    p.malla("raiz/cuerpo/capucha", "vacio", tubo_camino([(*a, r * 0.85, r * 0.85), (*b, r * 0.8, r * 0.8),
                                                         (*CAPUCHA[1][:3], 2.2, 2.2)], lados=8),
            lambda t: negro, dens=1, luz=False)
    a, b, r = TORSO
    p.malla("raiz/cuerpo/manto", "vacio_cuerpo", tubo_camino([(*a, r * 1.4, r * 1.2), (*b, r * 1.2, r * 1.1)], lados=8),
            lambda t: negro, dens=1, luz=False)


def mano(p, g, muneca, adelante, abajo, nombre, cierra=0.0, k=1.6):
    """Mano de hueso: el hueso del antebrazo que asoma, los nudillos y cuatro dedos larguisimos de tres falanges que se
    curvan, con garra negra; y el pulgar. cierra: 0 abierta, 1 encogida. k: que tan grande (los dedos larguisimos)."""
    hueso_ = voxel(HUESO, 0.08)
    garra = hex_(GARRA)
    adelante, abajo = _norm(adelante), _norm(abajo)
    lado = _norm(_cruz(adelante, abajo))
    atras = _mas(muneca, adelante, -3.0)
    p.malla(g, f"{nombre}_cubito", tubo_camino([(*atras, 0.6, 0.6), (*muneca, 0.5, 0.5)], lados=5), hueso_, dens=D)
    nudillos = _mas(muneca, adelante, 2.2 * k * 0.8)
    p.malla(g, f"{nombre}_palma", tubo_camino([(*muneca, 0.7, 0.45), (*nudillos, 1.3, 0.4)], lados=4, giro=45.0),
            hueso_, dens=D)
    for f_, dx in enumerate((-1.05, -0.35, 0.35, 1.05)):
        base = _mas(nudillos, lado, dx)
        largo = (2.5 - 0.3 * abs(f_ - 1.5)) * k
        dobla = 0.12 + 0.55 * cierra
        pts, d = [base], _norm(_mas(adelante, lado, dx * 0.3 * (1 - cierra)))
        for f in range(3):
            d = _norm(_mas(d, abajo, dobla * (f + 1) * 0.6))
            pts.append(_mas(pts[-1], d, largo * (1.0, 0.85, 0.7)[f]))
        for f in range(3):
            r0, r1 = (0.36, 0.3, 0.26)[f], (0.3, 0.26, 0.22)[f]
            p.malla(g, f"{nombre}_dedo{f_}_{f}", tubo_camino([(*pts[f], r0, r0), (*pts[f + 1], r1, r1)], lados=4),
                    hueso_, dens=D)
        punta = _mas(pts[-1], _norm(_mas(d, abajo, 0.6)), 1.6)
        p.malla(g, f"{nombre}_garra{f_}", cono(pts[-1], punta, 0.24, lados=4), lambda t: garra, dens=D)
    base = _mas(_mas(muneca, adelante, 0.8), lado, -1.0)
    medio = _mas(_mas(base, adelante, 1.3 * k), lado, -0.8)
    punta = _mas(_mas(medio, adelante, 1.2 * k), abajo, 0.6 + 0.6 * cierra)
    p.malla(g, f"{nombre}_pulgar0", tubo_camino([(*base, 0.34, 0.34), (*medio, 0.28, 0.28)], lados=4), hueso_, dens=D)
    p.malla(g, f"{nombre}_pulgar1", tubo_camino([(*medio, 0.28, 0.28), (*punta, 0.22, 0.22)], lados=4), hueso_, dens=D)
    p.malla(g, f"{nombre}_garra_pulgar", cono(punta, _mas(punta, _norm(_menos(punta, medio)), 1.2), 0.2, lados=4),
            lambda t: garra, dens=D)


def manos(p):
    for lado, (hombro, codo, muneca), cierra in (("d", BRAZO_D, 0.15), ("i", BRAZO_I, 0.6)):
        b = f"raiz/cuerpo/brazo_{lado}"
        a = f"{b}/antebrazo_{lado}"
        m = f"{a}/mano_{lado}"
        adelante = _norm(_menos(muneca, codo))
        abajo = _norm(_mas(_cruz(_cruz(adelante, (0.0, 0.0, -1.0)), adelante), (0.0, 0.0, -0.4)))
        mano(p, m, _mas(muneca, adelante, 0.6), adelante, abajo, f"mano_{lado}", cierra)
        p.m.pivotes[b] = hombro
        p.m.pivotes[f"{b}/manga_{lado}"] = hombro
        p.m.pivotes[a] = codo
        p.m.pivotes[m] = muneca


def construir():
    p = Personaje("bruma", altura=64)
    p.m.luz = False                                         # la luz ya viene en la textura (bandas por pliegue)
    t = manto()
    tela_en_el_modelo(p, t)
    vacio(p)
    manos(p)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), "raiz/cuerpo": (0.0, 40.0, 0.0), "raiz/cuerpo/capucha": (0.0, 67.0, -1.0),
                        "raiz/cuerpo/manto": (0.0, 65.0, 0.0), "raiz/cuerpo/faldon_frente": (0.0, 38.0, -4.0),
                        "raiz/cuerpo/faldon_atras": (0.0, 38.0, 5.0), "raiz/cuerpo/faldon_d": (4.0, 38.0, 0.5),
                        "raiz/cuerpo/faldon_i": (-4.0, 38.0, 0.5)})
    return p
