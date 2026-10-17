"""
SOMBRA ALTA, la manta del cielo: el titan de las llanuras y la sabana (ver la hoja de titanes del usuario). Una manta
enorme que vuela alto en circulos lentos; cuando pasa, su sombra oscurece todo. Indigo casi negra por arriba con
venas moradas que brillan de noche, la panza gris lavanda, los dos cuernos cefalicos al frente (se desenrollan para
comer) y la cola larga y delgada.
Escala: el modelo se dibuja 8 veces mas grande (1 px = 1/2 bloque): 60 bloques de envergadura y unos 45 de largo
con la cola. El origen va en el centro de la panza.
Huesos: raiz / cuerpo / (ala_d1 / ala_d2 / ala_d3, ala_i1..3, cuerno_d, cuerno_i, boca, cola1 / cola2 / cola3).
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER, voxel

ESCALA = 8.0
LOMO = tonos("#2A1F45")
PANZA = tonos("#8E86A8")
VENA = tonos("#B070FF")
BRILLAN = [VENA["b"], VENA["l"], VENA["h"]]

# la silueta del ala vista desde arriba (x hacia afuera, z: borde de adelante y de atras), del cuerpo a la punta
ALA = ((13.0, -15.0, 13.0), (24.0, -10.0, 10.0), (37.0, -3.5, 6.0), (51.0, 3.5, 4.5), (60.0, 9.0, 7.5))
GROSOR = (5.0, 3.0, 2.0, 1.2, 0.6)       # medio grueso del ala en cada corte (en y)
TRAMOS_ALA = ((0, 1), (1, 3), (3, 4))   # que cortes van en ala_x1, ala_x2 y ala_x3


def _vena(x, z):
    """Las venas que brillan: lineas que salen del cuerpo hacia las puntas, con ramitas."""
    a = math.atan2(z + 6.0, abs(x) + 1e-6)
    r = math.hypot(abs(x), z + 6.0)
    rayo = abs(math.sin(a * 7.0 + r * 0.04)) < 0.11
    anillo = abs(math.sin(r * 0.18)) < 0.07 and abs(x) > 16
    return (rayo or anillo) and abs(x) > 8


def lomo(t):
    if t.cara == "down" or (hasattr(t, "n") and t.n[1] < -0.3):
        cu, cv = math.floor(t.x * 0.5 + 100), math.floor(t.z * 0.5 + 100)
        return hex_(PANZA["l"] if (cu + cv) % 9 == 0 else PANZA["b"] if BAYER[cv % 4][cu % 4] < 11 else PANZA["s"])
    if _vena(t.x, t.z):
        return hex_(VENA["l"])
    cu, cv = math.floor(t.x * 0.5 + 100), math.floor(t.z * 0.5 + 100)
    f = 0.5 + 0.12 * math.sin(cu * 0.5 + cv * 0.3) + ((BAYER[cv % 4][cu % 4] + 0.5) / 16 - 0.5) * 0.2
    if (cu * 5 + cv * 3) % 97 == 0:
        return hex_(LOMO["h"])                                # pecas claras
    return hex_(LOMO["s"] if f < 0.35 else LOMO["b"] if f < 0.75 else LOMO["l"])


def _ala(s, i0, i1):
    """El tramo del ala entre los cortes i0 e i1 como malla: cada corte es un rombo (arriba, atras, abajo, adelante) y
    las caras miran hacia afuera del eje del ala."""
    cortes = list(range(i0, i1 + 1))
    m = geo.Armador()
    anillos, centros = [], []
    for k in cortes:
        x, z0, z1 = ALA[k]
        g, zc = GROSOR[k], (z0 + z1) / 2
        anillos.append([m.v((s * x, g, zc)), m.v((s * x, 0.0, z1)), m.v((s * x, -g * 0.6, zc)), m.v((s * x, 0.0, z0))])
        centros.append((s * x, 0.0, zc))
    for a, b, ca, cb in zip(anillos, anillos[1:], centros, centros[1:]):
        cm = tuple((u + v) / 2 for u, v in zip(ca, cb))
        for k in range(4):
            k2 = (k + 1) % 4
            cara = (a[k], a[k2], b[k2], b[k])
            c = m.centro(cara)
            m.cara(cara, (0.0, c[1] - cm[1], c[2] - cm[2]), "ala")
    if i1 == len(ALA) - 1:
        m.cara(tuple(anillos[-1]), (s, 0.0, 0.0), "punta")
    if i0 == 0:
        m.cara(tuple(anillos[0]), (-s, 0.0, 0.0), "raiz")
    return m.vs, m.caras


def construir():
    p = Personaje("sombra_alta")
    G = "raiz/cuerpo"
    # el cuerpo: un rombo grueso y aplanado
    cuerpo = geo.loft([(-21.0, 0.0, 0.0, 8.0, 2.5), (-15.0, 0.0, 0.0, 13.5, 4.5), (-2.0, 0.0, 0.0, 15.0, 5.0),
                       (10.0, 0.0, 0.0, 11.0, 4.0), (18.0, 0.0, 0.0, 4.0, 2.0)], 8, 22.5)
    # loft va a lo largo de y: lo acostamos a lo largo de z (adelante -z) y lo aplastamos
    cuerpo = geo.girar(cuerpo, (90.0, 0.0, 0.0))
    cuerpo = geo.escalar(cuerpo, (1.0, 0.75, 1.0))
    p.malla(G, "cuerpo", cuerpo, lomo, dens=2)
    for s in (1, -1):
        lado = "d" if s > 0 else "i"
        ruta = G
        for n, (i0, i1) in enumerate(TRAMOS_ALA):
            ruta = f"{ruta}/ala_{lado}{n + 1}"
            p.malla(ruta, f"ala_{lado}{n + 1}", _ala(s, i0, i1), lomo, dens=2)
            x0, z0, z1 = ALA[i0]
            p.m.pivotes[ruta] = (s * x0, 0.0, (z0 + z1) / 2)
        # los cuernos cefalicos (enrollados en reposo)
        cg = f"{G}/cuerno_{lado}"
        x = s * 9.0
        x0, x1 = sorted((x, x + s * 3.5))
        p.caja(cg, f"cuerno_{lado}", (x0, -1.5, -27.0), (x1, 1.5, -18.0), lomo, rot=(0.0, s * -12.0, s * 25.0),
               piv=(x, 0.0, -18.0), dens=1)
        p.m.pivotes[cg] = (x, 0.0, -18.0)
    # la boca: una ranura ancha abajo al frente
    p.caja(f"{G}/boca", "labio", (-6.0, -3.0, -21.0), (6.0, -1.5, -17.0), voxel(PANZA, -0.2), dens=1)
    p.m.pivotes[f"{G}/boca"] = (0.0, -1.5, -17.0)
    # la cola larga, en tres tramos
    ruta = G
    z = 17.0
    for k, (largo, w) in enumerate(((10.0, 1.6), (10.0, 1.1), (12.0, 0.6))):
        ruta = f"{ruta}/cola{k + 1}"
        p.caja(ruta, f"cola_{k + 1}", (-w, -w * 0.7, z), (w, w * 0.7, z + largo), lomo, dens=1)
        p.m.pivotes[ruta] = (0.0, 0.0, z)
        z += largo
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), G: (0.0, 0.0, 0.0)})
    for k in [k for k in list(p.m.pivotes) if k in ("Head", "Body", "RightArm", "LeftArm", "RightLeg", "LeftLeg")]:
        del p.m.pivotes[k]
    return p


# ---------------------------------------------------------------- animaciones

from .. import animar                                    # noqa: E402
from ..animar import facil, suave                        # noqa: E402
from .crackatos_anim import Pose                         # noqa: E402

ALAS = {s: [f"ala_{'d' if s > 0 else 'i'}{n}" for n in (1, 2, 3)] for s in (1, -1)}
COLAS = ("cola1", "cola2", "cola3")


def _aletear(p, t, T, amp, retraso=0.5, base=0.0):
    """La onda del ala: sube y baja del cuerpo a la punta con retraso (como una manta de verdad)."""
    w = 2 * math.pi * t / T
    for s, alas in ALAS.items():
        for n, h in enumerate(alas):
            p.rot(h, rz=s * (base + amp * (0.5 + 0.35 * n) * math.sin(w - n * retraso)))


def _cola(p, t, T, amp):
    w = 2 * math.pi * t / T
    for k, h in enumerate(COLAS):
        p.rot(h, ry=amp * math.sin(w - (k + 1) * 0.8), rx=amp * 0.4 * math.sin(w * 2 - k))


def mover(rig):
    """Vuela: aleteos lentos y hondos (la onda corre hacia la punta), el cuerpo sube y baja con cada golpe."""
    T = 4.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        p.pos("raiz", y=-2.0 * math.sin(w - 0.6))
        p.rot("cuerpo", rx=3.0 * math.sin(w - 1.2))
        _aletear(p, t, T, 22.0)
        _cola(p, t, T, 8.0)
        return p
    return T, pose, True


def quieto(rig):
    """Planea: las alas casi quietas, apenas onduladas, y la cola se mece."""
    T = 6.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        p.pos("raiz", y=-0.8 * math.sin(w))
        p.rot("cuerpo", rz=2.0 * math.sin(w))
        _aletear(p, t, T, 6.0, 0.7)
        _cola(p, t, T, 5.0)
        return p
    return T, pose, True


def asentarse(rig):
    """Baja a posarse: abre las alas planas y las deja caer sobre el piso."""
    L = 3.0

    def pose(t):
        u = facil(t / L)
        p = Pose()
        _aletear(p, t, 1.5, 10.0 * (1 - u), 0.5, -6.0 * u)
        p.rot("cuerpo", rx=-4.0 * math.sin(math.pi * u))
        for k, h in enumerate(COLAS):
            p.rot(h, rx=-6.0 * u)
        return p
    return L, pose, "hold_on_last_frame"


def descansar(rig):
    """Posada en la llanura con las alas extendidas sobre el pasto; respira (las alas suben y bajan apenas)."""
    T = 8.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _aletear(p, t, T, 1.5, 0.3, -6.0)
        p.pos("raiz", y=0.3 * math.sin(w))
        for k, h in enumerate(COLAS):
            p.rot(h, rx=-6.0, ry=3.0 * math.sin(w - k))
        return p
    return T, pose, True


def levantarse(rig):
    """Despega con tres aleteos fuertes."""
    L = 2.5

    def pose(t):
        p = Pose()
        u = facil(t / L)
        _aletear(p, t, 0.83, 30.0 * (1 - 0.4 * u), 0.4, -6.0 * (1 - u))
        p.rot("cuerpo", rx=8.0 * (1 - u))
        _cola(p, t, 1.25, 10.0)
        return p
    return L, pose, False


def comer(rig):
    """Come en vuelo (insectos, polen): desenrolla los cuernos hacia adelante y abre la boca mientras planea."""
    T = 4.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        abre = 0.75 + 0.25 * math.sin(w)
        for s, h in ((1, "cuerno_d"), (-1, "cuerno_i")):
            p.rot(h, ry=s * 25.0 * abre, rz=-s * 30.0 * abre)
        p.rot("boca", rx=-18.0 * abre)
        _aletear(p, t, T, 8.0, 0.6)
        _cola(p, t, T, 6.0)
        return p
    return T, pose, True


def especial(rig):
    """En picada: pliega las alas, baja la cabeza, y al final las abre de golpe (la rafaga)."""
    L = 3.0

    def pose(t):
        p = Pose()
        pliega = suave(t, [(0.0, 0.0), (0.6, 1.0), (2.0, 1.0), (2.3, -0.6), (L, 0.0)])
        p.rot("cuerpo", rx=-25.0 * max(0.0, pliega))
        for s, alas in ALAS.items():
            for n, h in enumerate(alas):
                p.rot(h, rz=s * (-18.0 * pliega * (1 + 0.5 * n)))
        _cola(p, t, 0.8, 4.0)
        return p
    return L, pose, False


ANIMACIONES = {"quieto": quieto, "mover": mover, "asentarse": asentarse, "descansar": descansar,
               "levantarse": levantarse, "comer": comer, "beber": quieto, "especial": especial}


def hornear_todas(rig):
    out = {}
    for nombre, f in ANIMACIONES.items():
        largo, pose, bucle = f(rig)
        datos, cuadros = animar.hornear(rig, nombre, largo, pose, bucle)
        out[nombre] = (datos, cuadros, bucle)
    return out
