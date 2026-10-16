"""
LA BRUMA (version 6): el espectro del dibujo del usuario (morfologia derecha, estilo de la casa), sobre la base v5.
  SILUETA: angosta arriba (las mangas hacen los lados) y con mucho vuelo de la cadera para abajo, sin cintura; mas
    abierta y mas inclinada de su lado derecho (+X); flota (nada toca el piso salvo las puntas mas largas).
  CAPUCHA de domo con la punta que se tuerce hacia su derecha y un poco adelante; atras tiene volumen y una costura
    marcada; la cara es un ovalo aparte con la orilla enrollada: filo claro por fuera y el forro que se oscurece hacia
    adentro hasta el vacio. Su capa cae sobre los hombros en ondas suaves, en V por el pecho y en punta por la espalda.
  MANGAS de la misma tela: nacen angostas bajo la capa, cuelgan pegadas al costado del hombro a la cadera y se abren
    en una campana con el puno cortado en diagonal; de cada puno salen el cubito y una mano de hueso grande con dedos
    en abanico.
  FRENTE abierto en V invertida (cerrado bajo la barbilla, cada vez mas abierto hacia abajo); la orilla se dobla y
    enseña el forro, con un filo claro.
  PLIEGUES: arriba pocos y grandes, disparejos; de la cadera para abajo un acordeon de tubos derechos que se hacen mas
    hondos hacia el ruedo (de su lado derecho se van en diagonal con los picos) y un tablon hundido en la espalda.
  RUEDO: de su lado derecho picos grandes que se separan en tiras y se abren hacia afuera; atras picos medianos (mas
    largo que adelante); del lado izquierdo ondas cortas.
Textura en el estilo de la casa: un tono plano por cara en bandas que siguen los pliegues (la luz de la tela lisa, y
cada cresta un paso mas clara y cada valle uno mas oscuro, con un acento verde azulado en las crestas de abajo), vetas
verticales de tela gastada, orillas con muescas dibujadas y un filo claro de 1 texel; por dentro el forro oscuro.
Medidas en px (16 por bloque), a tamano real: unos 5.7 bloques con la punta; flota. El frente es -Z, su derecha +X.
Huesos: raiz / cuerpo / (capucha, manto, falda_frente, falda_atras, falda_d, falda_i,
brazo_d / (manga_d, mano_d), brazo_i / (manga_i, mano_i)). Solo modelo (sin animaciones todavia).
"""

import math

import numpy as np

from ..kit import Personaje
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .khaset import cono, tubo_camino

D = 2                                     # texeles por px (32 por bloque)

# --- colores (tono plano por cara, como Khaset y Crackatos)
TELA = {"s": "#151B22", "b": "#212C36", "l": "#31414E", "cresta": "#465B6B", "valle": "#0E1318"}
ACENTO = "#3F6E68"                        # el verde azulado de la pintura, en las crestas de abajo
FILO, CONTRA = "#5E7787", "#0A0D11"      # el filo claro de las orillas y su texel oscuro por dentro
MAS_OSCURO = {TELA["cresta"]: TELA["l"], TELA["l"]: TELA["b"], TELA["b"]: TELA["s"], TELA["s"]: TELA["valle"],
              TELA["valle"]: "#090C10", ACENTO: TELA["b"]}
FORRO = ("#06080B", "#0B0F14", "#121A20", "#1A2427")
VACIO = "#020304"
HUESO = {"o": "#3A3B33", "s": "#6E6F62", "b": "#A3A493", "l": "#C9C7B4"}
GARRA = "#16140F"

# --- medidas
Y_ARRIBA = 66.0                           # donde empieza la ropa del cuerpo (bajo la capa de la capucha)
# (y, medio ancho a su derecha, a su izquierda, hondo adelante, hondo atras, centro z): un trapecio sin cintura
CUERPO = ((66.0, 9.0, 9.0, 6.0, 7.5, 0.5), (60.0, 10.5, 10.5, 6.5, 8.5, 0.6), (54.0, 11.0, 10.8, 7.0, 9.5, 0.8),
          (46.0, 12.0, 11.5, 7.5, 10.5, 1.0), (38.0, 14.0, 13.0, 8.5, 12.0, 1.3), (30.0, 17.5, 16.0, 10.5, 14.0, 1.6),
          (24.0, 21.5, 19.0, 12.5, 16.0, 2.0), (18.0, 25.5, 21.5, 15.0, 18.0, 2.3), (12.0, 28.5, 23.5, 17.0, 20.0, 2.6),
          (2.0, 31.0, 25.0, 19.0, 21.5, 2.8))
# abertura del frente: (y, medio ancho en x): cerrada bajo la barbilla, en V invertida hacia abajo
ABRE = ((63.0, 0.0), (56.0, 3.0), (44.0, 5.0), (30.0, 6.5), (2.0, 8.5))
# el ruedo: (angulo centro, medio ancho en grados, y de la punta, y de la muesca, forma, cuanto se abre hacia afuera)
# angulo: 0 adelante, 90 su derecha (+X), 180 atras, 270 su izquierda
RUEDO = ((18, 9, 9.0, 13.0, "pico", 0.15), (38, 10, 8.0, 14.0, "pico", 0.2),
         (58, 10, 7.0, 16.0, "pico", 0.45), (78, 10, 5.0, 17.0, "pico", 0.5), (97, 10, 3.5, 16.5, "pico", 0.55),
         (116, 10, 7.5, 16.0, "pico", 0.5), (135, 9, 9.5, 15.0, "pico", 0.35),
         (155, 11, 6.5, 12.5, "pico", 0.25), (178, 12, 5.5, 12.0, "pico", 0.25), (202, 12, 6.5, 12.5, "pico", 0.2),
         (222, 7, 12.5, 16.0, "onda", 0.08), (236, 7, 13.0, 16.5, "onda", 0.08), (250, 7, 13.5, 17.0, "onda", 0.08),
         (264, 7, 14.0, 17.0, "onda", 0.08), (278, 7, 13.5, 17.0, "onda", 0.08), (292, 7, 13.5, 16.5, "onda", 0.08),
         (306, 7, 12.5, 16.0, "onda", 0.08), (320, 7, 12.0, 15.5, "onda", 0.08), (338, 10, 10.0, 14.0, "pico", 0.15))
# cortes entre picos (tiras sueltas): angulos entre picos vecinos y que tan arriba suben desde la muesca
CORTES = ((48, 4.0), (68, 9.0), (87.5, 11.0), (106.5, 10.0), (126, 8.0), (144.5, 6.0), (166, 7.0), (190, 7.0))
# pliegues grandes: (angulo, medio ancho en grados, que tan hondo, desde que altura)
PLIEGUES = ((25, 16, 1.0, 66), (62, 15, 1.3, 64), (98, 17, 1.5, 64), (138, 16, 1.2, 66), (205, 18, 1.2, 66),
            (240, 15, 1.1, 64), (290, 16, 1.0, 64), (330, 14, 0.9, 66))
# mangas: (hombro, codo, puno), radios (hombro, codo, puno, campana)
MANGA_D = (((6.0, 67.0, 0.5), (13.5, 57.5, 0.0), (17.0, 46.5, -2.0)), (3.4, 4.4, 4.6, 7.6))
MANGA_I = (((-6.0, 67.0, 0.5), (-13.0, 58.0, 0.0), (-16.0, 47.5, -1.6)), (3.4, 4.3, 4.5, 7.3))
# capucha: (y, medio ancho, hondo adelante, hondo atras, centro z, corrimiento x, medio angulo de la cara)
CAPUCHA = ((62.5, 13.2, 7.6, 9.6, 0.5, 0.0, 0), (65.5, 11.0, 7.2, 9.2, 0.5, 0.0, 0), (68.0, 8.8, 6.9, 8.9, 0.4, 0.0, 0),
           (70.0, 6.8, 6.4, 8.5, 0.3, 0.0, 26),
           (74.0, 6.4, 6.6, 8.6, 0.0, 0.0, 33), (78.0, 6.2, 6.4, 8.2, -0.3, 0.3, 30), (80.5, 5.6, 5.8, 7.5, -0.3, 0.7, 14),
           (82.0, 5.4, 5.6, 7.2, -0.3, 1.0, 0), (85.0, 3.8, 3.8, 5.2, -0.6, 2.4, 0), (87.5, 2.2, 2.2, 3.0, -1.0, 4.5, 0),
           (89.5, 1.1, 1.1, 1.4, -1.5, 6.6, 0), (90.8, 0.3, 0.3, 0.3, -1.9, 8.0, 0))
# manos: muneca, hacia donde, que tanto cierra, lado
MANO_D = ((18.6, 44.6, -3.2), (0.30, -0.92, -0.25), 0.15)
MANO_I = ((-16.9, 45.6, -2.6), (-0.25, -0.94, -0.20), 0.40)


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
    filas = sorted(tabla, key=lambda f: f[0])
    if y <= filas[0][0]:
        return filas[0][col]
    for a, b in zip(filas, filas[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return a[col] + (b[col] - a[col]) * t
    return filas[-1][col]


def _dang(a, b):
    """Diferencia de angulos en grados (de -180 a 180)."""
    return (a - b + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------- el pintor de las telas

def _pintor(A, D_libre, D_abre, U, tono, forro=False, rim=None, muescas=True, H=None):
    """Pinta un cuadrito de tela: el tono plano de la cara y, cerca de las orillas, el detalle dibujado.
    D_libre: px a la orilla suelta (ruedo, puno, capa): muescas en diente de sierra y filo claro.
    D_abre: px a la orilla de la abertura (frente o cara): la tela se dobla y ensena el forro, con filo.
    U: posicion a lo largo de la orilla (para las muescas). forro: la cara de adentro. rim: escalones del forro de la
    cara (hacia el vacio) por distancia a la orilla. H: la coordenada de los hilos (constante a lo largo de cada
    columna de la tela): unas vetas verticales de tela gastada, un tono mas oscuras."""
    tris = []
    for (i0, i1, i2) in ((0, 1, 2), (0, 2, 3)):
        a, b, c = A[i0], A[i1], A[i2]
        v0, v1 = b - a, c - a
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        den = d00 * d11 - d01 * d01
        tris.append((tuple(a), tuple(v0), tuple(v1), d00, d01, d11, 1.0 / den if abs(den) > 1e-12 else 0.0,
                     (i0, i1, i2)))
    DL, DA, UU = [float(x) for x in D_libre], [float(x) for x in D_abre], [float(x) for x in U]
    HH = [float(x) for x in H] if H is not None else None
    c_tono, c_filo, c_contra = hex_(tono), hex_(FILO), hex_(CONTRA)
    c_veta = hex_(MAS_OSCURO.get(tono, tono))
    c_forro = [hex_(c) for c in FORRO]
    c_vacio = hex_(VACIO)

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
        dl = u * DL[i0] + v * DL[i1] + w * DL[i2]
        da = u * DA[i0] + v * DA[i1] + w * DA[i2]
        pos = u * UU[i0] + v * UU[i1] + w * UU[i2]
        # la orilla suelta: muescas en diente de sierra (periodo de 5 texeles, hasta 2 de hondo) y el filo
        if dl < 2.5:
            paso = int(pos * D) % 5
            hondo = (0, 1, 2, 1, 0)[paso] / D if muescas else 0.0
            if dl < hondo:
                return TRANSPARENTE
            if dl < hondo + 0.5:
                return c_filo
            if dl < hondo + 1.0:
                return c_contra
        if rim is not None:                                    # el forro de la cara: del filo al vacio
            if da < 0.5:
                return c_filo
            if da < 1.2:
                return c_forro[3]
            if da < 2.2:
                return c_forro[1]
            if da < 3.4:
                return c_forro[0]
            return c_vacio
        if da < 1.8 and not forro:                             # la orilla de la abertura: se dobla y ensena el forro
            if da < 0.5:
                return c_filo
            return c_forro[3] if da > 1.2 else c_forro[2]
        if HH is not None:                                     # vetas: unas columnas de hilo mas oscuras, a ratos
            col = int(u * HH[i0] + v * HH[i1] + w * HH[i2])
            if _azar(col * 1.37 + 0.5) < 0.13:
                y0 = 4.0 + 64.0 * _azar(col * 2.11 + 1.0)
                if y0 <= t.y <= y0 + 3.0 + 9.0 * _azar(col * 3.7 + 2.0):
                    return c_veta
        return c_tono
    return pintor


ESCALA_TONOS = (TELA["valle"], TELA["s"], TELA["b"], TELA["l"], TELA["cresta"])


def _tono_cara(n, pliegue, y, forro=False):
    """El tono plano de una cara (estilo de la casa): la luz de la tela lisa (n: su normal sin pliegues) da el tono
    de base, y el pliegue (de -1 valle a 1 cresta) lo sube o lo baja un paso. Asi los tonos salen en bandas limpias
    que siguen cada pliegue, no en manchas. Las crestas de abajo llevan el acento verde azulado."""
    L = (0.0, 0.894, -0.447)
    luz = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
    if forro:
        return FORRO[2] if luz > 0.45 else FORRO[1] if luz > -0.1 else FORRO[0]
    k = 3 if luz > 0.5 else 2 if luz > -0.05 else 1
    if pliegue > 0.4:
        k += 1
        if y < 15.0 and luz > -0.3:
            return ACENTO
    elif pliegue < -0.4:
        k -= 1
    return ESCALA_TONOS[max(0, min(4, k))]


class Tela:
    """Una tela como rejilla de puntos P[i, j] (i a lo ancho, j a lo largo) con lo que necesita el pintor por punto y
    los cuadritos que se saltan (cortes)."""

    def __init__(self, P, d_libre, d_abre, u_arco, saltar=None, muescas=True, liso=None, pliegue=None, hilos=None):
        """liso: la misma rejilla sin pliegues (de ahi sale la luz de cada cara); pliegue: por punto, de -1 (valle) a 1
        (cresta); hilos: por punto, la coordenada de las vetas (constante a lo largo de cada columna)."""
        self.P = np.asarray(P, float)
        self.muescas = muescas
        self.liso = np.asarray(liso, float) if liso is not None else self.P
        self.pl = np.asarray(pliegue, float) if pliegue is not None else None
        self.hilos = np.asarray(hilos, float) if hilos is not None else None
        self.d_libre, self.d_abre, self.u = (np.asarray(x, float) for x in (d_libre, d_abre, u_arco))
        self.saltar = saltar if saltar is not None else np.zeros((self.P.shape[0] - 1, self.P.shape[1] - 1), bool)

    def normales(self, P=None):
        P = self.P if P is None else P
        du = np.zeros_like(P)
        dv = np.zeros_like(P)
        du[1:-1] = P[2:] - P[:-2]
        du[0], du[-1] = P[1] - P[0], P[-1] - P[-2]
        dv[:, 1:-1] = P[:, 2:] - P[:, :-2]
        dv[:, 0], dv[:, -1] = P[:, 1] - P[:, 0], P[:, -1] - P[:, -2]
        n = np.cross(du, dv)
        return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)

    def pliegues(self, n):
        """> 0 en los valles y < 0 en las crestas (contra el promedio de los vecinos a 2 puntos)."""
        P = self.P
        Q = P.copy()
        for eje in (0, 1):
            for k in (-2, 2):
                R = np.roll(P, k, axis=eje)
                if eje == 0:
                    if k > 0:
                        R[:k] = P[:k]
                    else:
                        R[k:] = P[k:]
                else:
                    if k > 0:
                        R[:, :k] = P[:, :k]
                    else:
                        R[:, k:] = P[:, k:]
                Q = Q + R
        Q = Q / 5.0
        return np.einsum("ijk,ijk->ij", Q - P, n)

    def a_modelo(self, p, hueso_de, nombre, grueso=0.5, rim=False):
        nu, nv = self.P.shape[:2]
        n = self.normales()
        n0 = self.normales(self.liso)
        pl = self.pl if self.pl is not None else -np.clip(self.pliegues(n) * 2.0, -1.0, 1.0)
        adentro = self.P - n * grueso
        por_hueso = {}
        for i in range(nu - 1):
            for j in range(nv - 1):
                if self.saltar[i, j]:
                    continue
                q = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                pts = [self.P[ij] for ij in q]
                if any(np.linalg.norm(pts[k] - pts[(k + 1) % 4]) < 1e-4 for k in range(4)):
                    continue
                por_hueso.setdefault(hueso_de(np.mean(pts, axis=0)), []).append(q)
        for hueso, qs in por_hueso.items():
            usados = sorted({ij for q in qs for ij in q})
            nuevo = {ij: k for k, ij in enumerate(usados)}
            for capa, PP, es_forro in (("", self.P, False), ("_dentro", adentro, True)):
                vs = [tuple(float(c) for c in PP[ij]) for ij in usados]
                caras, pintores = [], []
                for q in qs:
                    orden = list(q[::-1]) if es_forro else list(q)
                    caras.append(tuple(nuevo[ij] for ij in orden))
                    A = np.array([PP[ij] for ij in orden])
                    nf = np.mean([(n if es_forro else n0)[ij] for ij in q], axis=0)
                    nf = nf / (np.linalg.norm(nf) or 1.0)
                    if es_forro:
                        nf = -nf
                    tono = _tono_cara(nf, float(np.mean([pl[ij] for ij in q])), float(A[:, 1].mean()), es_forro)
                    hilos = [self.hilos[ij] for ij in orden] if (self.hilos is not None and not es_forro) else None
                    pintores.append(_pintor(A, [self.d_libre[ij] for ij in orden], [self.d_abre[ij] for ij in orden],
                                            [self.u[ij] for ij in orden], tono, forro=es_forro,
                                            rim=(True if (rim and es_forro) else None), muescas=self.muescas, H=hilos))
                p.m.malla(hueso, f"{nombre}_{hueso.split('/')[-1]}{capa}", vs, caras, pintores, dens=D, luz=False)


def _arcos(P):
    """Largo acumulado a lo ancho (por fila) y a lo largo (por columna)."""
    a_u = np.concatenate([np.zeros((1, P.shape[1])), np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=-1), axis=0)], 0)
    a_v = np.concatenate([np.zeros((P.shape[0], 1)), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=-1), axis=1)], 1)
    return a_u, a_v


# ---------------------------------------------------------------- el cuerpo y la falda

def _ruedo(th):
    """(y del ruedo, cuanto se abre hacia afuera, y de la muesca) en el angulo th (grados)."""
    mejor = None
    for c, hw, punta, muesca, forma, abre in RUEDO:
        d = abs(_dang(th, c))
        if d <= hw:
            f = d / hw
            y = muesca - (muesca - punta) * ((1 - f * f) if forma == "onda" else (1 - f) ** 0.9)
            return y, abre, muesca
        if mejor is None or d - hw < mejor[0]:
            mejor = (d - hw, muesca, abre)
    return mejor[1], mejor[2], mejor[1]


def _abre(y):
    return _interp(ABRE, y, 1)


def cuerpo(p):
    nu, nv = 112, 30
    P = np.zeros((nu, nv, 3))
    P0 = np.zeros((nu, nv, 3))
    PL = np.zeros((nu, nv))
    d_abre = np.full((nu, nv), 99.0)
    th_cols = np.zeros(nu)
    muesca_col = np.zeros(nu)
    for i in range(nu):
        u = i / (nu - 1)
        # el angulo de la columna en el ruedo (para que los pliegues y los picos bajen derechos)
        w_ab = _abre(8.0)
        t0 = math.asin(min(0.9, w_ab / _interp(CUERPO, 8.0, 1)))
        t1 = 2 * math.pi - math.asin(min(0.9, w_ab / _interp(CUERPO, 8.0, 2)))
        th_r = t0 + u * (t1 - t0)
        th_cols[i] = math.degrees(th_r)
        hem, abre_afuera, muesca = _ruedo(th_cols[i])
        muesca_col[i] = muesca
        for j in range(nv):
            v = j / (nv - 1)
            y = Y_ARRIBA + (hem - Y_ARRIBA) * v
            w = _abre(y)
            rxp, rxn = _interp(CUERPO, y, 1), _interp(CUERPO, y, 2)
            a0 = math.asin(min(0.9, w / rxp)) if w > 0.05 else 0.0
            a1 = 2 * math.pi - (math.asin(min(0.9, w / rxn)) if w > 0.05 else 0.0)
            th = a0 + u * (a1 - a0)
            sn, cs = math.sin(th), math.cos(th)
            rx = rxp if sn >= 0 else rxn
            rzf, rzb, zc = _interp(CUERPO, y, 3), _interp(CUERPO, y, 4), _interp(CUERPO, y, 5)
            rz = rzf if cs >= 0 else rzb
            # pliegues: acordeon de crestas y valles que bajan derechos (los de su derecha se van en diagonal)
            off = 0.0
            for c, hw, hondo, desde in PLIEGUES:
                if y > desde:
                    continue
                cc = c + (0.7 * (38.0 - y) if (40 <= c <= 125 and y < 38.0) else 0.0)
                d = abs(_dang(th_cols[i], cc))
                if d < hw:
                    crece = min(1.0, (desde - y) / 22.0) * (0.35 + 0.65 * min(1.0, (60.0 - y) / 45.0 + 0.2))
                    off += hondo * crece * (1.0 - 2.0 * d / hw) * (0.8 + 0.4 * _azar(c))
            # el vuelo de la falda: un acordeon de tubos que bajan derechos (del lado derecho se van en diagonal con
            # los picos) y se hacen mas hondos hacia el ruedo, porque ahi se junta toda la tela
            if y < 40.0:
                ta = math.radians(th_cols[i] - 0.5 * (40.0 - y) * max(0.0, math.sin(math.radians(th_cols[i]))) ** 2)
                fase = 0.7 * math.sin(3 * ta + 1.0) + 0.4 * math.sin(5 * ta + 2.3)
                alto = (0.75 + 0.5 * _azar(round(math.degrees(ta) / 20.0)))
                off += 1.9 * min(1.0, (40.0 - y) / 26.0) ** 0.8 * alto * math.cos(18 * ta + fase)
            # el tablon hundido de la espalda
            d = abs(_dang(th_cols[i], 180.0))
            if d < 7.0:
                off -= 1.8 * (1.0 - d / 7.0) * min(1.0, (Y_ARRIBA - y) / 10.0 + 0.3)
            PL[i, j] = max(-1.0, min(1.0, off / 0.7))
            # las puntas del ruedo se abren hacia afuera
            sale = (muesca - y) * abre_afuera if y < muesca else 0.0
            P[i, j] = (sn * (rx + off + sale), y, zc - cs * (rz + off + sale))
            P0[i, j] = (sn * (rx + sale), y, zc - cs * (rz + sale))
            if w > 0.3:
                d_abre[i, j] = 0.0                              # se calcula abajo con el arco
    # cortes entre picos: una columna sin tela desde el ruedo hasta un poco arriba de la muesca
    saltar = np.zeros((nu - 1, nv - 1), bool)
    cortes_col = []
    for c, sube in CORTES:
        i = int(np.argmin([abs(_dang(t, c)) for t in th_cols[:-1]]))
        cortes_col.append((i, muesca_col[i] + sube))
        for j in range(nv - 1):
            if (P[i, j, 1] + P[i, j + 1, 1]) / 2 < muesca_col[i] + sube:
                saltar[i, j] = True
    a_u, a_v = _arcos(P)
    al_ruedo = a_v[:, -1:] - a_v
    d_libre = al_ruedo.copy()
    for i, hasta in cortes_col:                                 # las orillas de los cortes tambien son sueltas
        for di in (-3, -2, -1, 0, 1, 2, 3, 4):
            k = i + di
            if 0 <= k < nu:
                lado = abs(a_u[k] - (a_u[i] + a_u[min(i + 1, nu - 1)]) / 2)
                d_libre[k] = np.where(P[k, :, 1] < hasta, np.minimum(d_libre[k], np.maximum(0.0, lado - 0.6)),
                                      d_libre[k])
    abierta = d_abre < 50
    d_ab = np.minimum(a_u, a_u[-1:] - a_u)
    d_abre = np.where(abierta, d_ab, 99.0)

    def hueso_de(c):
        x, y, z = c
        if y > 38.0:
            return "raiz/cuerpo/manto"
        a = math.degrees(math.atan2(x, -(z - 2.0)))
        if -45 <= a < 45:
            return "raiz/cuerpo/falda_frente"
        if 45 <= a < 135:
            return "raiz/cuerpo/falda_d"
        if -135 <= a < -45:
            return "raiz/cuerpo/falda_i"
        return "raiz/cuerpo/falda_atras"
    hilos = np.repeat((np.arange(nu) * 2.6)[:, None], nv, axis=1)
    Tela(P, d_libre, d_abre, a_u, saltar, liso=P0, pliegue=PL, hilos=hilos).a_modelo(p, hueso_de, "ropa")


# ---------------------------------------------------------------- mangas

def manga(p, lado, datos):
    (hombro, codo, puno), (r0, r1, r2, campana) = datos
    s = 1 if lado == "d" else -1
    nu, nv = 32, 16
    P = np.zeros((nu, nv, 3))
    P0 = np.zeros((nu, nv, 3))
    PL = np.zeros((nu, nv))
    for i in range(nu):
        phi = -2 * math.pi * i / (nu - 1)                      # este sentido deja la cara de afuera por fuera
        for j in range(nv):
            v = j / (nv - 1)
            if v < 0.45:
                c = _mas(hombro, _menos(codo, hombro), v / 0.45)
                r = r0 + (r1 - r0) * v / 0.45
            else:
                c = _mas(codo, _menos(puno, codo), (v - 0.45) / 0.55)
                r = r1 + (r2 - r1) * (v - 0.45) / 0.55
            if v > 0.7:                                        # la campana en los ultimos px
                r += (campana - r2) * ((v - 0.7) / 0.3) ** 1.6
            a = _norm(_menos(codo, hombro) if v < 0.45 else _menos(puno, codo))
            e1 = _norm(_cruz(a, (0.0, 0.0, 1.0)))
            e2 = _norm(_cruz(e1, a))
            afuera = math.cos(phi) * (-1.0 if e1[0] * s < 0 else 1.0)   # 1 del lado de afuera
            onda = math.sin(4 * phi + 0.6 * s) + 0.35 * math.sin(7 * phi + 1.3)
            pl = (0.2 + 0.8 * v) * 0.8 * onda
            q = _mas(_mas(c, e1, (r + pl) * math.cos(phi)), e2, (r + pl) * math.sin(phi) * 0.92)
            q0 = _mas(_mas(c, e1, r * math.cos(phi)), e2, r * math.sin(phi) * 0.92)
            if v > 0.86:                                       # el puno cortado en diagonal: mas largo por fuera
                q = _mas(q, a, ((v - 0.86) / 0.14) * (1.8 * afuera + 0.4))
                q0 = _mas(q0, a, ((v - 0.86) / 0.14) * (1.8 * afuera + 0.4))
            P[i, j] = q
            P0[i, j] = q0
            PL[i, j] = max(-1.0, min(1.0, onda * min(1.0, 0.3 + v)))
    a_u, a_v = _arcos(P)
    d_libre = a_v[:, -1:] - a_v
    d_abre = np.full((nu, nv), 99.0)
    hilos = np.repeat((np.arange(nu) * 2.2 + (40 if lado == "d" else 90))[:, None], nv, axis=1)
    Tela(P, d_libre, d_abre, a_u, muescas=False, liso=P0, pliegue=PL, hilos=hilos).a_modelo(
        p, lambda c: f"raiz/cuerpo/brazo_{lado}/manga_{lado}", f"manga_{lado}")
    p.m.pivotes[f"raiz/cuerpo/brazo_{lado}"] = hombro
    p.m.pivotes[f"raiz/cuerpo/brazo_{lado}/manga_{lado}"] = hombro


# ---------------------------------------------------------------- capucha

def capucha(p):
    nu = 40
    filas = []
    for a, b in zip(CAPUCHA, CAPUCHA[1:]):
        filas += [tuple(a[c] + (b[c] - a[c]) * k / 2 for c in range(len(a))) for k in range(2)]
    filas.append(CAPUCHA[-1])
    filas = filas[::-1]                                        # de la punta hacia abajo
    nv = len(filas)
    P = np.zeros((nu, nv, 3))
    P0 = np.zeros((nu, nv, 3))
    PL = np.zeros((nu, nv))
    cara = np.zeros(nv, bool)
    for j, (y, rx, rzf, rzb, zc, xo, abre) in enumerate(filas):
        th0 = math.radians(abre)
        cara[j] = abre > 0.5
        for i in range(nu):
            th = th0 + (2 * math.pi - 2 * th0) * i / (nu - 1)
            sn, cs = math.sin(th), math.cos(th)
            rz = rzf if cs >= 0 else rzb
            # la costura de atras: filo y valle a lo largo de la espalda de la capucha
            d = abs(_dang(math.degrees(th), 180.0))
            costura = (0.7 * (1 - d / 8.0) if d < 8 else 0.0) - (0.4 * (1 - abs(d - 12) / 5.0) if 7 < d < 17 else 0.0)
            # la capa cae en ondas suaves que crecen hacia su orilla (y se aplanan en la V del pecho)
            ondas = 0.75 * math.sin(6 * th + 0.8) * min(1.0, (70.0 - y) / 6.0) * (1.0 - 0.6 * max(0.0, cs) ** 4) \
                if y < 70.0 else 0.0
            # dos dobleces que bajan de la punta por los lados de la capucha
            for c_, hw_ in ((70.0, 16.0), (290.0, 16.0)):
                dd = abs(_dang(math.degrees(th), c_))
                if dd < hw_ and 68.0 < y < 86.0:
                    ondas += 0.5 * (1 - 2 * dd / hw_) * math.sin(math.pi * (y - 68.0) / 18.0)
            yy = y
            if y < 67.5:                                       # la capa baja en V por el pecho y en punta atras
                k = (67.5 - y) / 5.0
                yy = y - k * (4.5 * max(0.0, cs) ** 2 + 6.0 * max(0.0, -cs) ** 6)
            P[i, j] = (xo + (rx + costura + ondas) * sn, yy, zc - (rz + costura + ondas) * cs)
            P0[i, j] = (xo + rx * sn, y, zc - rz * cs)              # la luz, sin la V (si no, sale un cuadro)
            PL[i, j] = max(-1.0, min(1.0, (costura + ondas) / 0.4))
    a_u, a_v = _arcos(P)
    al_ruedo = a_v[:, -1:] - a_v
    d_libre = al_ruedo
    d_abre = np.where(cara[None, :], np.minimum(a_u, a_u[-1:] - a_u), 99.0)
    Tela(P, d_libre, d_abre, a_u, muescas=False, liso=P0, pliegue=PL).a_modelo(
        p, lambda c: "raiz/cuerpo/capucha", "capucha", grueso=1.2, rim=True)


def vacio(p):
    """El vacio de la cara, 3 px mas adentro que la orilla, y el palo del cuerpo (muy oscuro) que se ve por la
    abertura."""
    negro = hex_(VACIO)
    p.malla("raiz/cuerpo/capucha", "vacio", tubo_camino([(0.0, 68.0, 0.6, 3.6, 3.4), (0.2, 74.0, 0.4, 4.0, 3.8),
                                                         (0.6, 79.0, 0.2, 3.2, 3.0)], lados=8),
            lambda t: negro, dens=1, luz=False)
    oscuro = hex_(FORRO[0])
    p.malla("raiz/cuerpo/manto", "vacio_cuerpo", tubo_camino([(0.0, 64.0, 1.0, 5.5, 4.0), (0.0, 50.0, 1.2, 5.0, 3.6),
                                                               (0.0, 34.0, 1.8, 6.0, 4.6), (0.0, 18.0, 3.0, 9.0, 7.0)],
                                                              lados=8),
            lambda t: oscuro, dens=1, luz=False)


# ---------------------------------------------------------------- manos

def mano(p, g, muneca, adelante, nombre, cierra, s, escala=1.3):
    """Mano de hueso grande (dedos en abanico, secciones cuadradas de 1 px que se leen de lejos): el cubito y el radio
    que asoman del puno, la palma, cuatro dedos de tres falanges con nudillos oscuros y garra, y el pulgar."""
    oscuro, claro, base, sombra = hex_(HUESO["o"]), hex_(HUESO["l"]), hex_(HUESO["b"]), hex_(HUESO["s"])

    def hueso(t):
        return claro if t.n[1] > 0.4 else sombra if t.n[1] < -0.4 else base
    garra = hex_(GARRA)

    def malla(nombre_, geo_, pintor, dens):                   # todo a escala desde la muneca
        vs, cs = geo_
        vs = [tuple(muneca[k] + (v[k] - muneca[k]) * escala for k in range(3)) for v in vs]
        p.malla(g, nombre_, (vs, cs), pintor, dens=dens)
    adelante = _norm(adelante)
    hacia_cuerpo = _norm((-s, 0.0, 0.0))
    abajo = _norm(_cruz(_cruz(adelante, hacia_cuerpo), adelante))   # hacia donde se curvan los dedos (al cuerpo)
    lado = _norm(_cruz(adelante, abajo))
    atras = _mas(muneca, adelante, -3.4)
    for k, dx in enumerate((-0.45, 0.45)):                     # cubito y radio
        malla(f"{nombre}_antebrazo{k}", tubo_camino([(*_mas(atras, lado, dx), 0.5, 0.5),
                                                          (*_mas(muneca, lado, dx * 0.6), 0.45, 0.45)], lados=4),
                hueso, dens=D)
    nudillos = _mas(muneca, adelante, 2.8)
    malla(f"{nombre}_palma", tubo_camino([(*muneca, 0.9, 0.5), (*nudillos, 1.4, 0.5)], lados=4, giro=45.0),
            hueso, dens=D)
    for f, dx in enumerate((-1.2, -0.4, 0.4, 1.2)):
        base_d = _mas(nudillos, lado, dx)
        largos = (3.0, 2.5, 2.0)
        d = _norm(_mas(adelante, lado, dx * 0.38 * (1.0 - 0.5 * cierra)))    # en abanico
        pts = [base_d]
        for k in range(3):
            d = _norm(_mas(d, abajo, (0.18 + 0.35 * cierra) * (k + 1)))
            pts.append(_mas(pts[-1], d, largos[k] * (1.0 - 0.08 * abs(f - 1.5))))
        for k in range(3):
            r = (0.5, 0.45, 0.4)[k]
            malla(f"{nombre}_dedo{f}_{k}", tubo_camino([(*pts[k], r, r), (*pts[k + 1], r * 0.9, r * 0.9)], lados=4),
                    hueso, dens=D)
            malla(f"{nombre}_nudillo{f}_{k}", tubo_camino([(*pts[k], r * 1.25, r * 1.25),
                                                               (*_mas(pts[k], d, 0.35), r * 1.25, r * 1.25)], lados=4),
                    lambda t: oscuro, dens=D)
        malla(f"{nombre}_garra{f}", cono(pts[-1], _mas(pts[-1], _norm(_mas(d, abajo, 0.5)), 1.5), 0.38, lados=4),
                lambda t: garra, dens=D)
    b = _mas(_mas(muneca, adelante, 1.0), lado, -1.3)
    m = _mas(_mas(b, adelante, 1.8), lado, -1.1)
    pu = _mas(_mas(m, adelante, 1.6), abajo, 0.8 + 0.6 * cierra)
    malla(f"{nombre}_pulgar0", tubo_camino([(*b, 0.48, 0.48), (*m, 0.42, 0.42)], lados=4), hueso, dens=D)
    malla(f"{nombre}_pulgar1", tubo_camino([(*m, 0.42, 0.42), (*pu, 0.38, 0.38)], lados=4), hueso, dens=D)
    malla(f"{nombre}_garra_pulgar", cono(pu, _mas(pu, _norm(_menos(pu, m)), 1.3), 0.34, lados=4),
            lambda t: garra, dens=D)


def manos(p):
    for lado, (muneca, hacia, cierra), s in (("d", MANO_D, 1), ("i", MANO_I, -1)):
        g = f"raiz/cuerpo/brazo_{lado}/mano_{lado}"
        mano(p, g, muneca, hacia, f"mano_{lado}", cierra, s)
        p.m.pivotes[g] = muneca


def construir():
    p = Personaje("bruma", altura=64)
    p.m.luz = False                                            # el tono va por cara en el pintor (estilo de la casa)
    cuerpo(p)
    manga(p, "d", MANGA_D)
    manga(p, "i", MANGA_I)
    capucha(p)
    vacio(p)
    manos(p)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), "raiz/cuerpo": (0.0, 40.0, 0.0),
                        "raiz/cuerpo/capucha": (0.0, 66.0, 0.5), "raiz/cuerpo/manto": (0.0, 64.0, 0.6),
                        "raiz/cuerpo/falda_frente": (0.0, 38.0, -6.0), "raiz/cuerpo/falda_atras": (0.0, 38.0, 12.0),
                        "raiz/cuerpo/falda_d": (17.0, 38.0, 1.0), "raiz/cuerpo/falda_i": (-15.0, 38.0, 1.0),
                        })
    return p
