"""
YACUMAMA, la anaconda: el titan de las montanas y el canon (ver la hoja de titanes del usuario y la referencia de la
anaconda verde de voxel). Una anaconda verde olivo enorme con manchas negras en pares por el lomo, ocelos ocres a los
lados, la panza crema con manchas, la cabeza ancha con la raya naranja del ojo a la quijada, ojos amarillos y la
lengua bifida oscura. Duerme en las montanas, baja con paradas, anida en un claro del canon y regresa (su nido
explica las serpientes de la semana 3).
Escala: el modelo se dibuja 8 veces mas grande (1 px = 1/2 bloque): unos 52 bloques de largo, el cuerpo de hasta 8
de grueso y con la cabeza en alto unos 11. Origen en el piso, bajo el cuello.
Huesos: raiz / (cabeza / (mandibula, lengua), s1 / s2 / ... / s12): cada tramo cuelga del anterior y el motor los
hace seguir el camino de la cabeza.
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER

ESCALA = 8.0
VERDE = tonos("#5B6B2F")
PANZA = tonos("#C9B26A")
OCRE = tonos("#B88A2E")
NEGRO = "#1C1E14"
NARANJA = tonos("#D88A2A")
LENGUA = "#3A1E2E"
BRILLAN = []

TRAMOS = 12
LARGO = 8.0
CABEZA = (6.0, 4.6, 14.0)                 # medio ancho, medio alto, largo


def radio_tramo(k):
    """Radio del cuerpo al principio y al final del tramo k (0 = el cuello): parejo casi todo el cuerpo (un poco mas
    grueso a la mitad) y se afina en el ultimo tercio hasta la punta de la cola."""
    def r(f):
        if f < 0.12:
            return 4.6 + (6.2 - 4.6) * f / 0.12
        if f < 0.62:
            return 6.2 + 0.5 * math.sin(math.pi * (f - 0.12) / 0.5)
        return max(0.7, 6.2 * (1 - (f - 0.62) / 0.38) ** 0.9)
    return r(k / TRAMOS), r((k + 1) / TRAMOS)


def piel(t):
    """Anaconda verde: el lomo olivo con pares de manchas negras ovaladas, a los lados ocelos ocres con borde negro y
    la panza crema con manchitas. La posicion a lo largo (z) y el angulo alrededor del cuerpo deciden el dibujo."""
    eje_y = getattr(t, "f", (0, 0, 0))
    centro_y = 5.0
    a = math.atan2(t.y - centro_y, t.x)                     # -pi/2 abajo, pi/2 arriba
    z = t.z
    if a < -0.9:                                            # panza
        cu, cv = math.floor(t.x * 1.2 + 100), math.floor(z * 1.2 + 100)
        if (cu * 3 + cv * 5) % 17 == 0:
            return hex_(NEGRO)
        return hex_(PANZA["l"] if BAYER[cv % 4][cu % 4] < 6 else PANZA["b"])
    # lomo: pares de manchas a cada lado del espinazo, cada 6 px
    zz = (z % 6.0) - 3.0
    lado = abs(a - math.pi / 2)
    if lado < 0.7:
        dz, da = zz / 2.2, (lado - 0.35) / 0.25
        if dz * dz + da * da < 1.0:
            return hex_(NEGRO)
    # ocelos a los costados, alternados
    zz2 = ((z + 3.0) % 6.0) - 3.0
    if -0.6 < a < 0.6 or (math.pi - 0.6 < abs(a) and False):
        dz, da = zz2 / 2.0, a / 0.45
        d = dz * dz + da * da
        if d < 0.45:
            return hex_(OCRE["l"])
        if d < 1.0:
            return hex_(NEGRO)
    cu, cv = math.floor(t.x * 1.0 + 100), math.floor((t.y + z) * 1.0 + 100)
    f = 0.5 + 0.15 * math.sin(cu * 0.8 + cv * 0.5) + ((BAYER[cv % 4][cu % 4] + 0.5) / 16 - 0.5) * 0.3
    if a > 1.2:
        f += 0.1
    return hex_(VERDE["s"] if f < 0.32 else VERDE["b"] if f < 0.72 else VERDE["l"])


def cabeza_piel(t):
    """La cabeza: olivo con la raya naranja del ojo hacia atras, la mancha negra en la coronilla y la quijada crema."""
    if t.y < 2.4:
        return hex_(PANZA["l"])
    if t.cara == "up":
        if abs(t.x) < 2.0 and -10.0 < t.z < -3.0:
            return hex_(NEGRO)
        return hex_(VERDE["l"] if (math.floor(t.x) + math.floor(t.z)) % 5 else VERDE["b"])
    if t.cara in ("east", "west"):
        if abs(t.y - (5.6 + (t.z + 12.0) * 0.12)) < 0.55:
            return hex_(NARANJA["b"])
        if abs(t.y - (4.4 + (t.z + 12.0) * 0.12)) < 0.4:
            return hex_(NEGRO)
    return hex_(VERDE["b"] if BAYER[math.floor(t.j) % 4][math.floor(t.i) % 4] < 10 else VERDE["s"])


def _ojo(t):
    u, v = t.i / max(1, t.tw - 1) - 0.5, t.j / max(1, t.th - 1) - 0.5
    if abs(u) < 0.1 and abs(v) < 0.4:
        return hex_(NEGRO)
    return hex_("#E8C23A" if math.hypot(u, v) < 0.42 else "#8A6A1E")


def _lengua(t):
    u, v = t.i / max(1, t.tw - 1), t.j / max(1, t.th - 1)
    if v > 0.55 and abs(u - 0.5) < 0.12:
        return TRANSPARENTE                                  # la horquilla
    if abs(u - 0.5) > 0.35 - 0.2 * (1 - v):
        return TRANSPARENTE
    return hex_(LENGUA)


def construir():
    p = Personaje("yacumama")
    hx, hy, hl = CABEZA
    C = "raiz/cabeza"
    yc = 5.0                                                # alto del eje de la cabeza
    cab = geo.loft([(-1.0, 0.0, 0.0, hx * 0.8, hy * 0.9), (5.0, 0.0, 0.0, hx, hy), (10.0, 0.0, 0.0, hx * 0.85, hy * 0.8),
                    (hl, 0.0, 0.0, hx * 0.5, hy * 0.55)], 8, 22.5)
    cab = geo.girar(cab, (-90.0, 0.0, 0.0))                 # el loft va en +y: girado queda hacia adelante (-z)
    cab = geo.mover(cab, (0.0, yc, 0.0))
    p.malla(C, "craneo", cab, cabeza_piel, dens=2)
    p.caja(f"{C}/mandibula", "quijada", (-hx * 0.55, yc - hy * 0.78, -hl + 3.0), (hx * 0.55, yc - hy * 0.35, -1.5),
           lambda t: hex_(PANZA["b"] if t.cara != "up" else "#5A2A2A"), dens=2)
    for s in (1, -1):
        lado = "d" if s > 0 else "i"
        x0, x1 = sorted((s * (hx * 0.86), s * (hx * 0.86 + 0.5)))
        p.caja(C, f"ojo_{lado}", (x0, yc + 0.6, -9.5), (x1, yc + 2.4, -7.5), _ojo, dens=4)
    p.m.cubo(f"{C}/lengua", "lengua", (-0.8, yc - 1.2, -hl - 5.0), (0.8, yc - 1.2, -hl + 1.0), _lengua, dens=4, luz=False)
    # el cuerpo: tramos que se encadenan hacia atras
    ruta = "raiz"
    z = 0.0
    for k in range(TRAMOS):
        ruta = f"{ruta}/s{k + 1}"
        r0, r1 = radio_tramo(k)
        eje = (r0 + r1) / 2 * 0.92                          # el eje de cada tramo a la altura de su radio: apoya en el piso
        tramo = geo.loft([(z - 0.6, 0.0, 0.0, r0, r0 * 0.92), (z + LARGO, 0.0, 0.0, r1, r1 * 0.92)], 8, 22.5,
                         tapa_abajo=k == 0, tapa_arriba=k == TRAMOS - 1)
        vs, cs = geo.girar(tramo, (90.0, 0.0, 0.0))           # de a lo largo de y a a lo largo de z (hacia atras)
        vs = [(x, y + eje, zz) for x, y, zz in vs]
        p.malla(ruta, f"tramo_{k + 1}", (vs, cs), piel, dens=1)
        p.m.pivotes[ruta] = (0.0, eje, z)
        z += LARGO
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), C: (0.0, yc, 0.0), f"{C}/mandibula": (0.0, yc - 1.0, -1.0),
                        f"{C}/lengua": (0.0, yc - 1.2, -hl + 1.0)})
    for k in [k for k in list(p.m.pivotes) if k in ("Head", "Body", "RightArm", "LeftArm", "RightLeg", "LeftLeg")]:
        del p.m.pivotes[k]
    return p


# ---------------------------------------------------------------- animaciones

from .. import animar                                    # noqa: E402
from ..animar import facil, suave                        # noqa: E402
from .crackatos_anim import Pose                         # noqa: E402

CUERPO = [f"s{k + 1}" for k in range(TRAMOS)]


def _onda(p, t, T, amp, desfase=0.6, cola=1.0):
    """La onda que corre por el cuerpo (cada tramo gira respecto al anterior), mas fuerte hacia la cola."""
    w = 2 * math.pi * t / T
    for k, h in enumerate(CUERPO):
        f = 0.6 + 0.4 * cola * k / TRAMOS
        p.rot(h, ry=amp * f * (math.sin(w - (k + 1) * desfase) - math.sin(w - k * desfase)) / max(0.3, desfase))


def _saca_lengua(p, t, cada=3.0):
    """Saca la lengua dos veces rapido cada tanto."""
    u = (t % cada) / cada
    sale = max(0.0, math.sin(min(1.0, u / 0.15) * math.pi)) if u < 0.15 else 0.0
    p.pos("lengua", z=-5.0 * (1 - sale))
    p.rot("mandibula", rx=-4.0 * sale)


def mover(rig):
    """Repta: la onda lateral corre de la cabeza a la cola; la cabeza va derecha y saca la lengua."""
    T = 3.0

    def pose(t):
        p = Pose()
        _onda(p, t, T, 10.0)
        p.rot("cabeza", ry=-3.0 * math.sin(2 * math.pi * t / T), rx=2.0)
        _saca_lengua(p, t, 1.5)
        return p
    return T, pose, True


def quieto(rig):
    """Quieta con la cabeza un poco en alto: respira despacio (ondita), mueve la cabeza y saca la lengua."""
    T = 6.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _onda(p, t, T, 2.0, 0.8, 0.5)
        p.rot("cabeza", rx=8.0 + 2.0 * math.sin(w), ry=6.0 * math.sin(w * 0.5 * 2))
        p.rot("s1", rx=-6.0)
        _saca_lengua(p, t, 3.0)
        return p
    return T, pose, True


ENROSCA = 28.0                                           # grados por tramo al enroscarse (12 tramos: una vuelta)


def _enroscada(p, u):
    for k, h in enumerate(CUERPO):
        p.rot(h, ry=ENROSCA * u * (0.7 + 0.6 * k / TRAMOS))
    p.rot("cabeza", rx=-6.0 * u, ry=-30.0 * u)


def asentarse(rig):
    """Se enrosca: el cuerpo da la vuelta sobre si mismo y la cabeza queda encima, en el centro."""
    L = 4.0

    def pose(t):
        p = Pose()
        _enroscada(p, facil(t / L))
        p.pos("cabeza", y=3.0 * facil(t / L))
        return p
    return L, pose, "hold_on_last_frame"


def descansar(rig):
    """Enroscada, dormida: respira (el cuerpo se aprieta y afloja apenas)."""
    T = 8.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _enroscada(p, 1.0 + 0.03 * math.sin(w))
        p.pos("cabeza", y=3.0)
        _saca_lengua(p, t, 8.0)
        return p
    return T, pose, True


def levantarse(rig):
    """Se desenrosca y estira el cuello."""
    L = 3.0

    def pose(t):
        p = Pose()
        u = 1 - facil(t / L)
        _enroscada(p, u)
        p.pos("cabeza", y=3.0 * u)
        p.rot("s1", rx=-12.0 * math.sin(math.pi * min(1.0, t / L)))
        return p
    return L, pose, False


def comer(rig):
    """Ataca a una presa: echa la cabeza atras, se lanza con la boca abierta y la cierra; luego traga."""
    T = 3.0

    def pose(t):
        p = Pose()
        atras = suave(t, [(0.0, 0.0), (0.6, 1.0), (0.8, 1.0), (1.0, -1.0), (1.3, -0.6), (2.0, 0.0), (T, 0.0)])
        boca = suave(t, [(0.0, 0.0), (0.7, 0.6), (0.95, 1.0), (1.1, 0.0), (T, 0.0)])
        p.rot("s1", rx=-14.0 * max(0.0, atras))
        p.pos("cabeza", z=4.0 * atras, y=4.0 * max(0.0, atras))
        p.rot("cabeza", rx=6.0 * atras)
        p.rot("mandibula", rx=-35.0 * boca)
        _onda(p, t, T, 3.0)
        return p
    return T, pose, True


def beber(rig):
    """Baja la cabeza al agua y la lengua entra y sale."""
    T = 3.0

    def pose(t):
        p = Pose()
        p.rot("cabeza", rx=-14.0)
        p.rot("s1", rx=6.0)
        _saca_lengua(p, t, 1.0)
        _onda(p, t, T, 1.5)
        return p
    return T, pose, True


def especial(rig):
    """El coletazo: la cola se va a un lado y azota hacia el otro (avienta a quien este cerca de ella)."""
    L = 2.5

    def pose(t):
        p = Pose()
        golpe = suave(t, [(0.0, 0.0), (0.7, -1.0), (1.0, 1.2), (1.3, 0.8), (L, 0.0)])
        for k, h in enumerate(CUERPO):
            f = max(0.0, (k - 5) / (TRAMOS - 6))
            p.rot(h, ry=26.0 * golpe * f)
        p.rot("cabeza", rx=10.0, ry=-12.0 * golpe)
        return p
    return L, pose, False


ANIMACIONES = {"quieto": quieto, "mover": mover, "asentarse": asentarse, "descansar": descansar,
               "levantarse": levantarse, "comer": comer, "beber": beber, "especial": especial}


def hornear_todas(rig):
    out = {}
    for nombre, f in ANIMACIONES.items():
        largo, pose, bucle = f(rig)
        datos, cuadros = animar.hornear(rig, nombre, largo, pose, bucle)
        out[nombre] = (datos, cuadros, bucle)
    return out
