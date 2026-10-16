"""
LA BRUMA (version 4): el espectro con la ropa como la dibujo el usuario sobre su referencia.
  CUERPO derecho y flaco (no se ve: adentro solo hay vacio).
  CAPUCHA alta y angosta que acaba en punta (un poco torcida hacia adelante); la cara es un hueco negro.
  MANGAS anchas que cuelgan de los hombros hasta la cadera y se abren en campana; de cada puno sale una mano de hueso
    con dedos larguisimos y garras.
  FRENTE abierto: entre las mangas, del cuello a la cintura, la ropa se abre y solo se ve oscuridad; abajo tambien se
    abre un poco, como abrigo.
  FALDA: de la cintura para abajo se abre muchisimo (campana), con pliegues que bajan derechos y el ruedo roto en
    picos disparejos: largos y hacia afuera de su lado derecho, mas cortos y ondulados del izquierdo; atras es mas
    larga (volumen atras).
Cada pieza es una tela hecha a mano (rejillas de puntos), con su cara de adentro mas oscura. Textura: bandas limpias
que siguen los pliegues (crestas claras, valles oscuros, mas clara arriba) y las orillas deshilachadas.
Medidas en px (16 por bloque), a tamano real: unos 5.5 bloques con la punta; flota. El frente es -Z, su derecha +X.
Huesos: raiz / cuerpo / (capucha, manto, falda_frente, falda_atras, falda_d, falda_i, brazo_d / (manga_d, mano_d),
brazo_i / (manga_i, mano_i)). Solo modelo (sin animaciones todavia).
"""

import math

import numpy as np

from ..kit import Personaje
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import voxel
from .khaset import cono, tubo_camino

D = 2                                     # texeles por px (32 por bloque)

# la tela: de lo mas oscuro (valles, abajo) a lo mas claro (crestas, arriba)
RAMPA = ("#04060A", "#080B10", "#0D1217", "#131A21", "#1A232C", "#222D38", "#2C3946", "#384757")
HUESO = {"s": "#5E6355", "b": "#80857A", "l": "#A3A797"}
GARRA = "#1E1C19"
VACIO = "#020304"

# --- medidas (salen del dibujo del usuario: 1 px del modelo = unos 14.6 px del dibujo)
CUELLO, PECHO, CINTURA, RUEDO = 67.0, 55.0, 37.0, 8.0   # alturas
# la ropa del cuerpo: (y, medio ancho, hondo adelante, hondo atras, centro z, medio angulo de la abertura en grados)
CUERPO = ((67.0, 7.4, 4.8, 5.0, -0.4, 4), (63.0, 7.6, 4.8, 5.2, -0.3, 22), (55.0, 6.4, 4.4, 5.0, -0.2, 32),
          (45.0, 6.2, 4.4, 5.0, 0.0, 24), (37.0, 7.0, 5.0, 5.6, 0.4, 8), (30.0, 11.0, 8.0, 9.4, 1.6, 4),
          (20.0, 18.0, 13.0, 16.0, 3.6, 4), (8.0, 26.0, 19.0, 24.0, 6.0, 6))
# mangas: (hombro, medio, puno), radios (hombro, medio, puno), inclinacion del puno
MANGA_D = (((7.0, 66.5, -0.5), (10.2, 54.0, -1.0), (12.3, 41.5, -2.0)), (2.8, 3.6, 5.6), 1.6)
MANGA_I = (((-7.0, 66.5, -0.5), (-10.4, 54.5, -0.8), (-12.6, 42.5, -1.5)), (2.8, 3.5, 5.3), 1.2)
# capucha: (y, medio ancho, hondo adelante, hondo atras, centro z, corrimiento x, medio angulo de la cara en grados);
# las filas de abajo con angulo grande caen sobre la espalda
CAPUCHA = ((62.5, 7.8, 6.0, 7.4, 0.6, 0.0, 115), (66.5, 7.0, 5.8, 6.6, -0.2, 0.0, 16),
           (70.0, 5.8, 5.6, 5.6, -0.8, 0.0, 32), (73.5, 5.3, 5.6, 5.2, -1.2, 0.0, 34),
           (77.0, 4.8, 5.2, 4.8, -1.4, 0.2, 28), (80.0, 4.0, 4.4, 4.0, -1.4, 0.5, 14),
           (83.0, 2.8, 3.0, 2.8, -1.2, 0.9, 0), (85.8, 1.6, 1.7, 1.6, -1.0, 1.3, 0),
           (88.5, 0.35, 0.35, 0.35, -0.9, 1.6, 0))
CABEZA = ((0.0, 68.0, -0.8), (0.0, 77.0, -1.2), 3.6)          # el vacio de la cara (una capsula negra)
MANO_D = ((11.6, 43.5, -2.4), (-0.25, -0.95, -0.25), 0.25)   # muneca, hacia donde, que tanto cierra
MANO_I = ((-11.9, 44.5, -1.9), (0.22, -0.95, -0.25), 0.55)


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


def _interp(tabla, y, col):
    """Valor de la columna 'col' de una tabla por alturas (de arriba hacia abajo o al reves), en la altura y."""
    filas = sorted(tabla, key=lambda f: f[0])
    if y <= filas[0][0]:
        return filas[0][col]
    for a, b in zip(filas, filas[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return a[col] + (b[col] - a[col]) * t
    if y >= filas[-1][0]:
        return filas[-1][col]
    return filas[-1][col]


# ---------------------------------------------------------------- telas hechas a mano (rejillas)

class Pieza:
    """Una tela como rejilla de puntos P[i][j] (i a lo ancho, j a lo largo): de ahi salen los cuadritos, las normales,
    la luz de los pliegues, la posicion en la tela y la distancia a la orilla."""

    def __init__(self, P, borde):
        self.P = np.asarray(P, float)                          # (nu, nv, 3)
        self.borde = np.asarray(borde, float)                  # (nu, nv): px hasta la orilla suelta mas cercana

    def normales(self):
        P = self.P
        du = np.zeros_like(P)
        dv = np.zeros_like(P)
        du[1:-1] = P[2:] - P[:-2]
        du[0], du[-1] = P[1] - P[0], P[-1] - P[-2]
        dv[:, 1:-1] = P[:, 2:] - P[:, :-2]
        dv[:, 0], dv[:, -1] = P[:, 1] - P[:, 0], P[:, -1] - P[:, -2]
        n = np.cross(du, dv)
        return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)

    def luz(self):
        """Por punto: luz de arriba y de frente, crestas claras y valles oscuros, mas clara hacia arriba."""
        P, n = self.P, self.normales()
        Q = P.copy()
        for eje, k in ((0, 2), (1, 2)):
            a = np.roll(P, k, axis=eje)
            b = np.roll(P, -k, axis=eje)
            if eje == 0:
                a[:k], b[-k:] = P[:k], P[-k:]
            else:
                a[:, :k], b[:, -k:] = P[:, :k], P[:, -k:]
            Q = Q + a + b
        Q = Q / 5.0
        pliegue = np.einsum("ijk,ijk->ij", Q - P, n)          # > 0: valle
        L = np.array([0.0, 1.0, -0.5])
        L /= np.linalg.norm(L)
        luz = np.clip(n @ L, -0.2, 1.0)
        alto = (P[..., 1] - 4.0) / 84.0
        return 0.40 + 0.26 * luz - np.clip(pliegue * 0.5, -0.22, 0.26) + 0.22 * (alto - 0.5)

    def a_modelo(self, p, hueso_de, nombre):
        """Pasa la tela al modelo: por fuera con su luz y, un pelito adentro y al reves, la cara de adentro oscura."""
        nu, nv = self.P.shape[:2]
        S = self.luz()
        n = self.normales()
        adentro = self.P - n * 0.25
        por_hueso = {}
        for i in range(nu - 1):
            for j in range(nv - 1):
                q = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                pts = [self.P[a, b] for a, b in q]
                if any(np.linalg.norm(pts[k] - pts[(k + 1) % 4]) < 1e-4 for k in range(4)):
                    continue                                   # cuadrito aplastado (no se ve)
                c = np.mean(pts, axis=0)
                por_hueso.setdefault(hueso_de(c), []).append(((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)))
        for hueso, qs in por_hueso.items():
            usados = sorted({ij for q in qs for ij in q})
            nuevo = {ij: k for k, ij in enumerate(usados)}
            for capa, PP, voltea in (("", self.P, False), ("_dentro", adentro, True)):
                vs = [tuple(float(c) for c in PP[ij]) for ij in usados]
                caras, pintores = [], []
                for q in qs:
                    orden = list(q[::-1]) if voltea else list(q)
                    caras.append(tuple(nuevo[ij] for ij in orden))
                    A = np.array([PP[ij] for ij in orden])
                    pintores.append(_pintor_cuadro(A, [S[ij] for ij in orden], [self.borde[ij] for ij in orden],
                                                   dentro=voltea))
                p.m.malla(hueso, f"{nombre}_{hueso.split('/')[-1]}{capa}", vs, caras, pintores, dens=D, luz=False)


def _pintor_cuadro(A, S, B, dentro=False):
    """Interpola la luz y la distancia a la orilla dentro del cuadrito (por triangulos) y decide el tono; las orillas
    sueltas se deshilachan. dentro: la cara de adentro (mas oscura)."""
    rampa = [hex_(c) for c in RAMPA]
    tris = []
    for (i0, i1, i2) in ((0, 1, 2), (0, 2, 3)):
        a, b, c = A[i0], A[i1], A[i2]
        v0, v1 = b - a, c - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        den = d00 * d11 - d01 * d01
        tris.append((tuple(a), tuple(v0), tuple(v1), d00, d01, d11, 1.0 / den if abs(den) > 1e-12 else 0.0,
                     (i0, i1, i2)))
    Sl, Bl = [float(x) for x in S], [float(x) for x in B]

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
        b = u * Bl[i0] + v * Bl[i1] + w * Bl[i2]
        k = int(s * len(rampa)) - (3 if dentro else 0)
        if b < 1.6:                                            # la orilla suelta: hilos disparejos
            hilo = _azar(int(t.x * 2.0) * 7 + int(t.y * 2.0) * 13 + int(t.z * 2.0) * 3)
            if b < 1.6 * (0.2 + 0.8 * hilo):
                return TRANSPARENTE
            k -= 1
        elif b < 3.5:
            k -= 1
        return rampa[max(0, min(len(rampa) - 1, k))]
    return pintor


# ---------------------------------------------------------------- las piezas

def _picos_ruedo(th):
    """Cuanto mas abajo llega el ruedo en el angulo th (0 adelante, pi/2 su derecha): picos disparejos, largos y hacia
    afuera de su lado derecho, cortos y ondulados del izquierdo."""
    out = 0.0
    n = 15
    for k in range(n):
        c = 2 * math.pi * (k + 0.3 * _azar(k * 1.7)) / n
        derecha = max(0.0, math.sin(c))                        # 1 en su lado derecho
        izquierda = max(0.0, -math.sin(c))
        amp = (4.0 + 11.0 * derecha * (0.6 + 0.4 * _azar(k * 3.3)) + 2.0 * izquierda * _azar(k * 5.1)
               + 4.0 * max(0.0, -math.cos(c)) * _azar(k * 7.7))
        ancho = 2 * math.pi / n * (0.55 + 0.35 * _azar(k * 2.9))
        d = abs(((th - c + math.pi) % (2 * math.pi)) - math.pi)
        out = max(out, amp * max(0.0, 1 - d / ancho))
    return out + 1.2 * math.sin(th * 9.0 + 0.7) * (1 if math.sin(th) < 0 else 0)   # ondulado del izquierdo


def falda_y_cuerpo(p):
    """La ropa del cuerpo: del cuello al ruedo, abierta adelante. Cada columna llega a su propio ruedo (los picos)."""
    nu, nv = 84, 46
    filas_y = [f[0] for f in CUERPO]
    P = np.zeros((nu, nv, 3))
    borde = np.zeros((nu, nv))
    for i in range(nu):
        u = i / (nu - 1)
        for j in range(nv):
            v = j / (nv - 1)
            # la altura: de cuello a ruedo; el ruedo de esta columna depende de su angulo (se calcula con el de abajo)
            abre = math.radians(_interp(CUERPO, CINTURA, 5))
            th_ruedo = math.radians(_interp(CUERPO, RUEDO, 5))
            th = th_ruedo + u * (2 * math.pi - 2 * th_ruedo)
            base = RUEDO + 3.5 + 4.0 * math.cos(th)            # adelante mas corto, atras mas largo
            ruedo = base - _picos_ruedo(th)
            y = CUELLO + (ruedo - CUELLO) * v ** 1.0
            abre = math.radians(_interp(CUERPO, max(y, RUEDO), 5))
            th = abre + u * (2 * math.pi - 2 * abre)
            yy = max(y, RUEDO - 6.0)
            rx = _interp(CUERPO, yy, 1) + (max(0.0, RUEDO - y) * 0.7)
            rzf = _interp(CUERPO, yy, 2) + (max(0.0, RUEDO - y) * 0.5)
            rzb = _interp(CUERPO, yy, 3) + (max(0.0, RUEDO - y) * 0.7)
            zc = _interp(CUERPO, yy, 4)
            sn, cs = math.sin(th), math.cos(th)
            rz = rzb + (rzf - rzb) * (cs + 1) / 2
            # pliegues que bajan derechos, cada vez mas hondos
            hondo = 0.25 + 2.4 * max(0.0, (CINTURA + 4 - y) / (CINTURA + 4 - RUEDO)) ** 1.2
            pl = hondo * (0.62 * math.sin(11 * th + 0.4) + 0.38 * math.sin(17 * th + 1.9)
                          + 0.25 * math.sin(7 * th + 2.6 + y * 0.05))
            P[i, j] = (math.sin(th) * (rx + pl), y, zc - cs * (rz + pl))
    # distancia a la orilla: hacia abajo por la columna (el ruedo) y de lado hasta la abertura
    largo_col = np.concatenate([np.zeros((nu, 1)), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=-1), axis=1)], 1)
    al_ruedo = largo_col[:, -1:] - largo_col
    largo_fila = np.concatenate([np.zeros((1, nv)), np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=-1), axis=0)], 0)
    a_la_abertura = np.minimum(largo_fila, largo_fila[-1:] - largo_fila)
    borde = np.minimum(al_ruedo, a_la_abertura)

    def hueso_de(c):
        x, y, z = c
        if y > CINTURA - 2:
            return "raiz/cuerpo/manto"
        a = math.degrees(math.atan2(x, -(z - 2.0)))
        if -45 <= a < 45:
            return "raiz/cuerpo/falda_frente"
        if 45 <= a < 135:
            return "raiz/cuerpo/falda_d"
        if -135 <= a < -45:
            return "raiz/cuerpo/falda_i"
        return "raiz/cuerpo/falda_atras"
    Pieza(P, borde).a_modelo(p, hueso_de, "ropa")


def manga(p, lado, datos):
    """Una manga ancha que cuelga del hombro y se abre en campana; el puno inclinado y roto en picos chiquitos."""
    (hombro, medio, puno), (r0, r1, r2), inclina = datos
    nu, nv = 26, 18
    camino = []
    for j in range(nv):
        v = j / (nv - 1)
        if v < 0.5:
            c = _mas(hombro, _menos(medio, hombro), v * 2)
            r = r0 + (r1 - r0) * v * 2
        else:
            c = _mas(medio, _menos(puno, medio), v * 2 - 1)
            r = r1 + (r2 - r1) * (v * 2 - 1) ** 1.4
        camino.append((c, r))
    P = np.zeros((nu, nv, 3))
    s = 1 if lado == "d" else -1
    for j, (c, r) in enumerate(camino):
        a = camino[max(0, j - 1)][0]
        b = camino[min(nv - 1, j + 1)][0]
        eje = _norm(_menos(b, a))
        e1 = _norm(_cruz(eje, (0.0, 0.0, 1.0)))               # hacia afuera / adentro
        e2 = _norm(_cruz(e1, eje))
        v = j / (nv - 1)
        for i in range(nu):
            th = -2 * math.pi * i / (nu - 1)                   # este sentido deja la cara de afuera por fuera
            pl = (0.15 + 0.7 * v) * math.sin(7 * th + 1.1 * (s > 0))
            rr = r + pl
            q = _mas(_mas(c, e1, rr * math.cos(th)), e2, rr * math.sin(th) * 0.9)
            if j == nv - 1 or j == nv - 2:                     # el puno: inclinado y roto
                afuera = math.cos(th) * s
                baja = inclina * afuera + (1.4 * max(0.0, 1 - abs(((th * 3.0) % 2.0) - 1.0)) if j == nv - 1 else 0.0)
                q = _mas(q, eje, baja * (1.0 if j == nv - 1 else 0.4))
            P[i, j] = q
    largo_col = np.concatenate([np.zeros((nu, 1)), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=-1), axis=1)], 1)
    borde = largo_col[:, -1:] - largo_col
    Pieza(P, borde).a_modelo(p, lambda c: f"raiz/cuerpo/brazo_{lado}/manga_{lado}", f"manga_{lado}")
    p.m.pivotes[f"raiz/cuerpo/brazo_{lado}"] = hombro
    p.m.pivotes[f"raiz/cuerpo/brazo_{lado}/manga_{lado}"] = hombro


def capucha(p):
    """La capucha alta que acaba en punta: anillos de abajo hacia arriba con el hueco de la cara adelante (y la tela de
    atras que cae sobre la espalda), cerrada arriba en la punta."""
    nu = 36
    filas = []
    for a, b in zip(CAPUCHA, CAPUCHA[1:]):
        filas += [tuple(a[c] + (b[c] - a[c]) * k / 2 for c in range(len(a))) for k in range(2)]
    filas.append(CAPUCHA[-1])
    nv = len(filas)
    P = np.zeros((nu, nv, 3))
    for j, (y, rx, rzf, rzb, zc, xo, abre) in enumerate(filas):
        th0 = math.radians(abre)
        for i in range(nu):
            th = th0 + (2 * math.pi - 2 * th0) * i / (nu - 1)
            sn, cs = math.sin(th), math.cos(th)
            rz = rzb + (rzf - rzb) * (cs + 1) / 2
            pl = 0.45 * (1 - j / (nv - 1)) * math.sin(6 * th + 0.8)
            P[i, j] = (xo + (rx + pl) * sn, y, zc - (rz + pl) * cs)
    P = P[:, ::-1]                                             # de arriba hacia abajo (la punta en j = 0)
    largo_fila = np.concatenate([np.zeros((1, nv)), np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=-1), axis=0)], 0)
    a_la_cara = np.minimum(largo_fila, largo_fila[-1:] - largo_fila)
    largo_col = np.concatenate([np.zeros((nu, 1)), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=-1), axis=1)], 1)
    al_ruedo = largo_col[:, -1:] - largo_col
    abiertas = np.array([math.radians(f[6]) > 0.01 for f in filas[::-1]])
    borde = np.where(abiertas[None, :], np.minimum(a_la_cara, al_ruedo), al_ruedo)
    borde = np.maximum(borde, np.where(np.arange(nv)[None, :] < 3, 9.0, 0.0))     # la punta no se deshilacha
    Pieza(P, borde).a_modelo(p, lambda c: "raiz/cuerpo/capucha", "capucha")


def vacio(p):
    """Adentro: el vacio negro (la cabeza y el cuerpo), para que por la cara y la abertura solo se vea oscuridad."""
    negro = hex_(VACIO)
    a, b, r = CABEZA
    p.malla("raiz/cuerpo/capucha", "vacio", tubo_camino([(*a, r, r), (*b, r * 0.9, r * 0.9),
                                                         (0.6, 81.0, -1.4, 2.2, 2.2)], lados=8),
            lambda t: negro, dens=1, luz=False)
    p.malla("raiz/cuerpo/manto", "vacio_cuerpo", tubo_camino([(0.0, 66.0, -0.2, 5.6, 3.8), (0.0, 50.0, 0.0, 4.8, 3.4),
                                                               (0.0, 34.0, 0.6, 5.6, 4.2), (0.0, 22.0, 2.0, 9.0, 7.0)],
                                                              lados=8),
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
    for lado, (muneca, hacia, cierra) in (("d", MANO_D), ("i", MANO_I)):
        g = f"raiz/cuerpo/brazo_{lado}/mano_{lado}"
        adelante = _norm(hacia)
        s = 1 if lado == "d" else -1
        abajo = _norm(_cruz(adelante, (0.0, 0.0, s * 1.0)))     # los dedos se curvan hacia el cuerpo
        if abajo[0] * s > 0:
            abajo = tuple(-c for c in abajo)
        mano(p, g, muneca, adelante, abajo, f"mano_{lado}", cierra)
        p.m.pivotes[g] = muneca


def construir():
    p = Personaje("bruma", altura=64)
    p.m.luz = False                                         # la luz ya viene en la textura (bandas por pliegue)
    falda_y_cuerpo(p)
    manga(p, "d", MANGA_D)
    manga(p, "i", MANGA_I)
    capucha(p)
    vacio(p)
    manos(p)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), "raiz/cuerpo": (0.0, 40.0, 0.0),
                        "raiz/cuerpo/capucha": (0.0, 66.0, -0.5), "raiz/cuerpo/manto": (0.0, 64.0, 0.0),
                        "raiz/cuerpo/falda_frente": (0.0, CINTURA, -4.0), "raiz/cuerpo/falda_atras": (0.0, CINTURA, 5.0),
                        "raiz/cuerpo/falda_d": (5.0, CINTURA, 0.5), "raiz/cuerpo/falda_i": (-5.0, CINTURA, 0.5)})
    return p
