"""
Capucha de Pibble sola (para trabajarla aparte antes de ponerla en el personaje).

Piezas low-poly independientes, con las mismas reglas:
  - ovalo: un ovalo acostado (mas ancho que alto), armado panel a panel: paneles chicos donde hay curva
    (alrededor de la cara y en el contorno) y paneles grandes atras. Es una cascara con grosor: afuera crema,
    adentro negra. En el medio del frente, el agujero ovalado de la cara con filete dorado. Abajo queda
    abierta, a la altura del cuello, para conectarse con el cuerpo.
  - cabeza: un cubo de vacio adentro de la capucha, con los dos ojos; se ve por el agujero.
  - dos orejas de gato: conos de base redonda arriba de la cabeza, abiertos un poco hacia los costados.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from .pibble import CREMA, ORO, hex_

# medidas (px). Frente = -Z, derecha del personaje = +X.
CX, CY, CZ = 0.0, 22.5, 0.0         # centro del ovalo
RX, RY, RZ = 8.5, 7.0, 7.0          # semiejes: ancho, alto, fondo
GROSOR = 0.8                        # grosor de la tela de la capucha
# columnas (grados desde el frente hacia +X) y filas (grados de altura): mas juntas cerca de la cara
HA, HB = 31, 36                     # medio ancho y medio alto del agujero de la cara (en grados del ovalo)
ALFAS = (0, HA, 72, 126, 180, 234, 288, 360 - HA)
BETAS = (-48, -HB, 0, HB, 60, 80)   # abajo queda abierta (ahi se conecta el cuerpo)
# borde del agujero de la cara: 8 vertices del ovalo (columna, fila)
BORDE = ((360 - HA, -HB), (0, -HB), (HA, -HB), (HA, 0), (HA, HB), (0, HB), (360 - HA, HB), (360 - HA, 0))
ESQUINAS = {(360 - HA, -HB), (HA, -HB), (HA, HB), (360 - HA, HB)}
HUECO = {(a, b) for a in (360 - HA, 0) for b in (-HB, 0)}  # los 4 paneles del frente que se sacan

CABEZA = 7.0                        # lado del cubo de la cabeza
CABEZA_Z = -0.7                     # centro del cubo (un poco hacia adelante, para que se vea por el agujero)
FORRO = "#080608"                   # adentro de la capucha
VACIO_CABEZA = "#17131A"            # la cabeza, apenas mas clara que el forro para que se lea el cubo


def punto(a, b, enc=0.0):
    """Vertice del ovalo en (columna a, fila b); enc achica los semiejes (cascara de adentro)."""
    rx, ry, rz = RX - enc, RY - enc, RZ - enc
    ar, br = math.radians(a), math.radians(b)
    p = (CX + rx * math.cos(br) * math.sin(ar), CY + ry * math.sin(br), CZ - rz * math.cos(br) * math.cos(ar))
    if (a, b) in ESQUINAS:                     # esquinas del agujero: se meten hacia el centro -> agujero ovalado
        x, y = CX + (p[0] - CX) * 0.84, CY + (p[1] - CY) * 0.84
        k = max(0.0, 1 - ((x - CX) / rx) ** 2 - ((y - CY) / ry) ** 2)
        p = (x, y, CZ - rz * math.sqrt(k))     # sigue sobre la superficie del ovalo
    return p


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
    """Cascara del ovalo con el agujero de la cara. Devuelve (vertices, caras, tipos)."""
    m = Armador()
    V = {(a, b): m.v(punto(a, b)) for a in ALFAS for b in BETAS}              # afuera
    W = {(a, b): m.v(punto(a, b, GROSOR)) for a in ALFAS for b in BETAS}      # adentro (forro)
    centro = (CX, CY, CZ)
    for i, b in enumerate(BETAS[:-1]):
        b2 = BETAS[i + 1]
        for k, a in enumerate(ALFAS):
            if (a, b) in HUECO:
                continue
            a2 = ALFAS[(k + 1) % len(ALFAS)]
            m.cara((V[a, b], V[a2, b], V[a2, b2], V[a, b2]), lambda c: geo._sub(c, centro), "fuera")
            m.cara((W[a, b], W[a2, b], W[a2, b2], W[a, b2]), lambda c: geo._sub(centro, c), "forro")
    m.cara(tuple(V[a, BETAS[-1]] for a in ALFAS), (0, 1, 0), "fuera")         # techo chico
    m.cara(tuple(W[a, BETAS[-1]] for a in ALFAS), (0, -1, 0), "forro")
    b = BETAS[0]                                                             # abajo abierta: solo el canto
    for k, a in enumerate(ALFAS):
        a2 = ALFAS[(k + 1) % len(ALFAS)]
        m.cara((V[a, b], V[a2, b], W[a2, b], W[a, b]), (0, -1, 0), "forro")
    for k in range(len(BORDE)):                                              # canto del agujero (el grosor)
        q, q2 = BORDE[k], BORDE[(k + 1) % len(BORDE)]
        m.cara((V[q], V[q2], W[q2], W[q]), lambda c: (CX - c[0], CY - c[1], 0), "forro")
    return m.vs, m.caras, m.tipos


def oreja():
    """Oreja de gato (derecha, +X): un cono de base redonda (10 lados), con la base hundida en el ovalo."""
    cono = geo.piramide(geo.anillo(0, 0, 0, 2.4, 2.4, 10), (0, 6.8, 0))
    cono = geo.girar(cono, (0, 0, -22))                            # abierta hacia el costado, sin ir hacia atras
    pie = punto(85, 60)                                            # arriba y mas atras, sobre la cabeza
    return geo.mover(cono, (pie[0], pie[1] - 0.9, pie[2] + 0.4))


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


def cabeza(t):
    """Cubo de vacio; adelante, dos ojos cuadrados (1.4 px): claro arriba hacia afuera, dorado abajo hacia adentro."""
    if t.cara == "north":
        for ox in (1.6, -1.6):
            dx, dy = t.x - ox, t.y - (CY + 0.4)
            if abs(dx) < 0.7 and abs(dy) < 0.7:
                fuera = (dx > 0) == (ox > 0)
                if dy > 0:
                    return hex_("#F6E2AE" if fuera else "#E9CF92")
                return hex_("#DDB267" if fuera else "#9C7440")
    return hex_(VACIO_CABEZA)


def cono_negro(t):
    return hex_("#1C181E" if t.n[1] > 0.3 else "#141016")


def construir():
    p = Personaje("pibble_capucha", altura=27, cabeza=10, torso=(8, 11, 5), brazo=(4, 5))
    vs, caras, tipos = ovalo()
    pint = {"fuera": tela, "forro": lambda t: hex_(FORRO)}
    p.malla("Head/capucha", "ovalo", (vs, caras), [pint[k] for k in tipos])
    h = CABEZA / 2
    p.caja("Head/cabeza", "cabeza", (CX - h, CY - h, CABEZA_Z - h), (CX + h, CY + h, CABEZA_Z + h), cabeza, dens=2)
    p.malla_par("Head/capucha", "oreja", oreja(), cono_negro)
    return p
