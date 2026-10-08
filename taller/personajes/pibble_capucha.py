"""
Capucha de Pibble sola (para trabajarla aparte antes de ponerla en el personaje).

Piezas low-poly independientes, con las mismas reglas:
  - ovalo: un ovalo COMPLETO acostado (mas ancho que alto), armado panel a panel: paneles chicos donde hay
    curva (alrededor de la cara y en el contorno) y paneles grandes atras. En el medio del frente, el agujero
    de la cara, con un tunel corto hacia adentro y el vacio con los ojos al fondo.
  - dos orejas de gato: cuna triangular con el frente hundido (la parte de adentro de la oreja), base ancha y
    punta fina, en las esquinas de arriba del ovalo, inclinadas hacia afuera y atras.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from .pibble import CREMA, ORO, VACIO, hex_

# medidas (px). Frente = -Z, derecha del personaje = +X.
CX, CY, CZ = 0.0, 22.5, 0.0         # centro del ovalo
RX, RY, RZ = 8.5, 6.5, 6.5          # semiejes: ancho, alto, fondo
# columnas (grados desde el frente hacia +X) y filas (grados de altura): mas juntas cerca de la cara
ALFAS = (0, 27, 72, 126, 180, 234, 288, 333)
BETAS = (-66, -32, 0, 32, 60, 80)
# borde del agujero de la cara: 8 vertices del ovalo (columna, fila)
BORDE = ((333, -32), (0, -32), (27, -32), (27, 0), (27, 32), (0, 32), (333, 32), (333, 0))
ESQUINAS = {(333, -32), (27, -32), (27, 32), (333, 32)}
Z_CARA = -3.6                       # profundidad del vacio con los ojos


def punto(a, b):
    p = _sobre_ovalo(a, b)
    if (a, b) in ESQUINAS:                     # esquinas del agujero: se meten hacia el centro -> agujero ovalado
        x, y = CX + (p[0] - CX) * 0.82, CY + (p[1] - CY) * 0.82
        k = max(0.0, 1 - ((x - CX) / RX) ** 2 - ((y - CY) / RY) ** 2)
        p = (x, y, CZ - RZ * math.sqrt(k))     # sigue sobre la superficie del ovalo
    return p


def _sobre_ovalo(a, b):
    a, b = math.radians(a), math.radians(b)
    return (CX + RX * math.cos(b) * math.sin(a), CY + RY * math.sin(b), CZ - RZ * math.cos(b) * math.cos(a))


class Armador:
    """Junta vertices y caras orientando cada cara hacia el lado 'afuera' que se le indica."""

    def __init__(self):
        self.vs, self.caras, self.tipos = [], [], []

    def v(self, p):
        self.vs.append(tuple(p))
        return len(self.vs) - 1

    def centro(self, idx):
        return tuple(sum(self.vs[i][k] for i in idx) / len(idx) for k in range(3))

    def cara(self, idx, afuera, tipo):
        partes = geo._cara(self.vs, tuple(idx)) if len(idx) == 4 else [tuple(idx)]
        for parte in partes:
            dirc = afuera(self.centro(parte)) if callable(afuera) else afuera
            if geo._dot(geo.normal([self.vs[i] for i in parte]), dirc) < 0:
                parte = tuple(reversed(parte))
            self.caras.append(parte)
            self.tipos.append(tipo)


def ovalo():
    """Ovalo completo con el agujero de la cara. Devuelve (vertices, caras, tipos)."""
    m = Armador()
    V = {(a, b): m.v(punto(a, b)) for a in ALFAS for b in BETAS}
    centro = (CX, CY, CZ)
    hueco = {(a, b) for a in (333, 0) for b in (-32, 0)}            # 4 paneles del frente que se sacan
    for i, b in enumerate(BETAS[:-1]):
        b2 = BETAS[i + 1]
        for k, a in enumerate(ALFAS):
            a2 = ALFAS[(k + 1) % len(ALFAS)]
            if (a, b) in hueco:
                continue
            m.cara((V[a, b], V[a2, b], V[a2, b2], V[a, b2]), lambda c: geo._sub(c, centro), "fuera")
    m.cara(tuple(V[a, BETAS[-1]] for a in ALFAS), (0, 1, 0), "fuera")      # techo chico
    m.cara(tuple(V[a, BETAS[0]] for a in ALFAS), (0, -1, 0), "fuera")      # abajo
    # agujero de la cara: borde de 8 vertices del ovalo -> tunel corto -> vacio plano con los ojos
    borde = BORDE
    adentro = []
    for a, b in borde:
        x, y, _ = punto(a, b)
        adentro.append(m.v((CX + (x - CX) * 0.9, CY + (y - CY) * 0.9, Z_CARA)))
    for k in range(len(borde)):
        k2 = (k + 1) % len(borde)
        m.cara((V[borde[k]], V[borde[k2]], adentro[k2], adentro[k]), lambda c: (CX - c[0], CY - c[1], 0), "dentro")
    m.cara(tuple(adentro), (0, 0, -1), "cara")
    return m.vs, m.caras, m.tipos


def oreja():
    """Oreja de gato (derecha, +X): base ancha en forma de flecha, punta fina, frente hundido (adentro de la oreja).
    Las dos caras de adelante forman una canaleta; las de atras son lomo. Devuelve (malla, tipos)."""
    L, R = (-2.3, 0, 0.0), (2.3, 0, 0.0)          # base de lado a lado
    F, B = (0.0, 0, 0.8), (0.0, 0, 2.0)           # F metido hacia atras: frente concavo; B lomo de atras
    T = (0.4, 6.6, 1.1)                           # punta, un poco corrida hacia afuera y atras
    vs = [L, R, F, B, T]
    caras = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (0, 3, 1, 2)]
    tipos = ["adentro", "adentro", "lomo", "lomo", "base"]
    m = Armador()
    m.vs = list(vs)
    c0 = (0.0, 2.0, 1.0)
    for idx, tipo in zip(caras, tipos):
        m.cara(idx, lambda c: geo._sub(c, c0), tipo)
    malla = geo.girar((m.vs, m.caras), (8, -12, -14))              # mira un poco hacia afuera, se abre y va atras
    pie = punto(50, 54)                                            # esquina de arriba del ovalo
    malla = geo.mover(malla, (pie[0] - 0.3, pie[1] - 0.8, pie[2] + 0.3))
    return malla, m.tipos


# ---------------------------------------------------------------- pintores

def _dist_borde(x, y):
    """Distancia (de frente) desde (x, y) al contorno del agujero de la cara."""
    pol = [punto(a, b)[:2] for a, b in BORDE]
    mejor = 1e9
    for k, (ax, ay) in enumerate(pol):
        bx, by = pol[(k + 1) % len(pol)]
        dx, dy = bx - ax, by - ay
        u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        mejor = min(mejor, math.hypot(x - ax - u * dx, y - ay - u * dy))
    return mejor


def tela(t):
    """Crema plano (el sombreado lo dan las caras); filete dorado parejo alrededor del agujero."""
    if t.z < CZ - 4.3 and _dist_borde(t.x, t.y) < 0.7:
        return hex_(ORO["l"] if t.y > CY + 1 else ORO["b"])
    if t.cara == "up":
        return hex_(CREMA["l"])
    return hex_(CREMA["b"] if t.y > CY - 3 else CREMA["s"])


def cara_vacio(t):
    """Vacio con dos ojos cuadrados (1.5 px): claro arriba hacia afuera, dorado abajo hacia adentro."""
    for ox in (1.9, -1.9):
        dx, dy = t.x - ox, t.y - (CY + 0.3)
        if abs(dx) < 0.75 and abs(dy) < 0.75:
            fuera = (dx > 0) == (ox > 0)
            if dy > 0:
                return hex_("#F6E2AE" if fuera else "#E9CF92")
            return hex_("#DDB267" if fuera else "#9C7440")
    return hex_(VACIO)


def oreja_adentro(t):
    return hex_("#1E2533")                      # azul casi negro: se lee la forma de la oreja


def oreja_lomo(t):
    return hex_("#1A161C" if t.n[1] > 0.3 else "#141016")


def construir():
    p = Personaje("pibble_capucha", altura=27, cabeza=10, torso=(8, 11, 5), brazo=(4, 5))
    vs, caras, tipos = ovalo()
    pint = {"fuera": tela, "dentro": lambda t: hex_(VACIO), "cara": cara_vacio}
    p.malla("Head/capucha", "ovalo", (vs, caras), [pint[k] for k in tipos])
    malla, tipos = oreja()
    pint = {"adentro": oreja_adentro, "lomo": oreja_lomo, "base": oreja_lomo}
    p.malla_par("Head/capucha", "oreja", malla, [pint[k] for k in tipos])
    return p
