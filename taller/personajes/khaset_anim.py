"""
Las animaciones de Khaset (para GeckoLib, sobre el esqueleto de personajes/khaset_mob.py), como poses en funcion del
tiempo horneadas a 20 cuadros por segundo (taller/animar.py). Las piernas apoyadas van con IK (el tobillo exacto, el
pie con su inclinacion de reposo: los dedos quedan en el piso); al correr en cuatro patas tambien los brazos.
Convenciones del kit: el frente es -Z, su derecha +X. Giro en X positivo levanta lo de adelante (un brazo colgando se
va hacia adelante); en Z positivo un brazo derecho se abre hacia afuera.
  quieto        (4.0 s, bucle)  respira encorvado, los dedos se abren y cierran, un tic brusco de la cabeza
  acechar       (2.4 s, bucle)  camina despacio, encorvado, a zancadas largas y los brazos colgando
  correr        (0.7 s, bucle)  en cuatro patas: el torso casi acostado y los brazos de patas delanteras
  zarpazos      (1.6 s)         derecho, izquierdo y los dos juntos (golpes a 0.38, 0.78 y 1.22 s)
  abalanzarse   (1.4 s)         se agacha, salta con las garras por delante y cae agazapado (sale a 0.45 s)
  grito         (2.2 s)         echa la cabeza atras, abre la quijada, el abanico y los brazos, y tiembla
  desvanecer    (1.2 s)         se encoge y se hunde en el piso (para teletransportarse)
  aparecer      (1.2 s)         sale del piso y se endereza
  muerte        (2.6 s)         se le doblan las rodillas y cae de frente
  mirar         (1.6 s, bucle)  se congela cuando lo ven: la cabeza ladeada, apenas tiembla
"""

import math

from .. import animar
from ..animar import facil, suave
from .crackatos_anim import Pose

PIERNAS = {"d": ("RightLeg", "RightLeg_canilla", "RightLeg_canilla_pie"),
           "i": ("LeftLeg", "LeftLeg_canilla", "LeftLeg_canilla_pie")}
BRAZOS = {"d": ("RightArm", "RightArm_antebrazo", "RightArm_antebrazo_mano"),
          "i": ("LeftArm", "LeftArm_antebrazo", "LeftArm_antebrazo_mano")}
DEDOS = {"d": "RightArm_antebrazo_mano_dedos", "i": "LeftArm_antebrazo_mano_dedos"}
DEDOS_PIE = {"d": "RightLeg_canilla_pie_dedos", "i": "LeftLeg_canilla_pie_dedos"}
PANOS = ("pano_frente", "pano_atras", "faldon_der", "faldon_izq")
LADO = {"d": 1.0, "i": -1.0}
# los momentos que usa el mod (segundos)
GOLPES_ZARPAZOS = (0.38, 0.78, 1.22)
SALTO = 0.45
HUNDIDO = 1.1


def _tobillo(rig, lado, z=None):
    """El tobillo en reposo (con la z comun de los dos pies si se da: asi el paso es parejo)."""
    x, y, z0 = rig.pivote[PIERNAS[lado][2]]
    return (x, y, z0 if z is None else z)


Z_PIE = None


def _z_pies(rig):
    global Z_PIE
    if Z_PIE is None:
        Z_PIE = (rig.pivote[PIERNAS["d"][2]][2] + rig.pivote[PIERNAS["i"][2]][2]) / 2
    return Z_PIE


def _paso(rig, lado, u, zancada, alto, apoyo, adelante=0.0):
    """El tobillo en el ciclo u (0..1): apoyado se va de adelante hacia atras; en el aire vuelve levantandose."""
    x, y, z = _tobillo(rig, lado, _z_pies(rig) + adelante)
    u %= 1.0
    if u < apoyo:
        f = u / apoyo
        return (x, y, z - zancada / 2 + zancada * f), 0.0
    f = (u - apoyo) / (1 - apoyo)
    return (x, y + alto * math.sin(math.pi * f), z + zancada / 2 - zancada * facil(f)), -18.0 * math.sin(math.pi * f)


def _plantar(rig, p, objetivos):
    """{lado: (tobillo, giro extra del pie)} con IK."""
    for lado, (obj, extra) in objetivos.items():
        animar.ik_pata(rig, p, PIERNAS[lado], obj, extra)


def _quietos(rig, adelante=0.0):
    return {k: (_tobillo(rig, k, _z_pies(rig) + adelante), 0.0) for k in PIERNAS}


def _manos(p, curl):
    for k in DEDOS:
        p.rot(DEDOS[k], rx=curl)


def _plumas(p, abrir=0.0, mece=0.0):
    """Abre el abanico (cada pluma se aparta del centro) y lo mece."""
    p.rot("plumas", rz=mece)
    for fila, n in ((0, 11), (1, 7)):
        for k in range(n):
            p.rot(f"p{fila}_{k}", rz=abrir * (k - (n - 1) / 2) / ((n - 1) / 2) * 14.0)


def _panos(p, t, periodo, amp, fase=0.0):
    for i, h in enumerate(PANOS):
        p.rot(h, rx=amp * math.sin(2 * math.pi * t / periodo + fase + i * 0.7))


def _bulto(t, t0, t1):
    """0 fuera de [t0, t1] y una joroba suave adentro."""
    if t <= t0 or t >= t1:
        return 0.0
    return math.sin(math.pi * (t - t0) / (t1 - t0)) ** 2


# ---------------------------------------------------------------- las animaciones

def quieto(rig):
    T = 4.0

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        p.pos("raiz", y=0.3 * math.sin(w))
        p.rot("cintura", rx=-1.5 + 1.5 * math.sin(w))
        p.rot("Body", rx=0.8 * math.sin(w + 0.5))
        tic = _bulto(t, 2.55, 2.8)
        p.rot("Head", rx=1.5 * math.sin(w + 1.0), ry=5.0 * math.sin(w * 0.5 * 2), rz=14.0 * tic)
        for k, s in LADO.items():
            b = BRAZOS[k]
            p.rot(b[0], rx=2.0 * math.sin(w + (0 if s > 0 else math.pi)), rz=s * 1.0 * math.sin(w))
            p.rot(b[1], rx=3.0 + 2.0 * math.sin(w + 1.3))
        _manos(p, 8.0 + 10.0 * (0.5 + 0.5 * math.sin(2 * w)))
        _plumas(p, 0.1, 2.0 * math.sin(w))
        _panos(p, t, T, 3.0)
        _plantar(rig, p, _quietos(rig))
        return p
    return T, pose, True


def acechar(rig):
    T, zancada, alto, apoyo = 2.4, 16.0, 4.5, 0.62

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        p.pos("raiz", x=0.6 * math.sin(w), y=-1.5 + 0.9 * math.cos(2 * w))
        p.rot("cintura", rx=-10.0 + 2.0 * math.sin(2 * w), ry=4.0 * math.sin(w), rz=-1.5 * math.sin(w))
        p.rot("Head", rx=8.0 - 1.5 * math.sin(2 * w), ry=-3.0 * math.sin(w))
        for k, s in LADO.items():
            b = BRAZOS[k]
            p.rot(b[0], rx=-s * 14.0 * math.cos(w), rz=s * 2.0)
            p.rot(b[1], rx=8.0 + 6.0 * math.sin(w + (0 if s > 0 else math.pi) + 1.0))
        _manos(p, 12.0 + 6.0 * math.sin(2 * w))
        _plumas(p, 0.1, 2.5 * math.sin(w))
        _panos(p, t, T / 2, 5.0)
        _plantar(rig, p, {k: _paso(rig, k, t / T + f, zancada, alto, apoyo) for k, f in (("d", 0.0), ("i", 0.5))})
        return p
    return T, pose, True


def correr(rig):
    T, zancada, alto, apoyo = 0.7, 22.0, 6.0, 0.4

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        p.pos("raiz", y=-8.0 + 1.5 * math.sin(2 * w))
        p.rot("cintura", rx=-66.0 + 4.0 * math.sin(2 * w + 0.6))
        p.rot("Head", rx=52.0 - 4.0 * math.sin(2 * w))
        _plumas(p, -0.2, 0.0)
        p.rot("plumas", rx=-18.0)
        _panos(p, t, T / 2, 10.0)
        _manos(p, -10.0)
        _plantar(rig, p, {k: _paso(rig, k, t / T + f, zancada, alto, apoyo, adelante=2.0) for k, f in (("d", 0.0), ("i", 0.08))})
        # los brazos de patas delanteras: la muneca va al piso adelante de los hombros
        tr = rig.transformaciones(p)
        for k, f in (("d", 0.5), ("i", 0.58)):
            hombro = tr[BRAZOS[k][0]](rig.pivote[BRAZOS[k][0]])
            u = (t / T + f) % 1.0
            x = hombro[0] + LADO[k] * 2.0
            if u < apoyo:
                z = hombro[2] - zancada / 2 + zancada * (u / apoyo)
                y = 8.6
            else:
                g = (u - apoyo) / (1 - apoyo)
                z = hombro[2] + zancada / 2 - zancada * facil(g)
                y = 8.6 + 7.0 * math.sin(math.pi * g)
            animar.ik_pata(rig, p, BRAZOS[k], (x, y, z - 3.0))
        return p
    return T, pose, True


def zarpazos(rig):
    L = 1.6
    # (tiempo, (hombro rx, hombro rz, codo rx)) de cada brazo y del torso (ry, rx)
    derecho = [(0.0, (0, 0, 0)), (0.22, (150, 10, 50)), (0.38, (10, -25, 5)), (0.55, (0, 0, 10)),
               (0.95, (0, 0, 10)), (1.08, (155, 15, 45)), (1.22, (15, -20, 5)), (1.6, (0, 0, 0))]
    izquierdo = [(0.0, (0, 0, 0)), (0.45, (0, 0, 10)), (0.62, (150, -10, 50)), (0.78, (10, 25, 5)),
                 (0.95, (0, 0, 10)), (1.08, (155, -15, 45)), (1.22, (15, 20, 5)), (1.6, (0, 0, 0))]
    torso = [(0.0, (0, 0)), (0.22, (18, -4)), (0.38, (-14, -14)), (0.62, (-18, -6)), (0.78, (14, -14)),
             (1.0, (0, -4)), (1.08, (0, 2)), (1.22, (0, -20)), (1.6, (0, 0))]

    def pose(t):
        p = Pose()
        ry, rx = suave(t, torso)
        p.rot("cintura", rx=rx - 2.0, ry=ry)
        p.pos("raiz", y=-2.0 * _bulto(t, 0.1, 1.5))
        p.rot("Head", rx=-rx * 0.6 + 4.0, ry=-ry * 0.5)
        for k, curva in (("d", derecho), ("i", izquierdo)):
            hx, hz, cx = suave(t, curva)
            p.rot(BRAZOS[k][0], rx=hx, rz=hz)
            p.rot(BRAZOS[k][1], rx=cx)
        golpe = max(_bulto(t, 0.3, 0.5), _bulto(t, 0.7, 0.9), _bulto(t, 1.14, 1.34))
        _manos(p, 10.0 - 35.0 * golpe)
        _plumas(p, 0.2 + 0.4 * golpe, 3.0 * math.sin(t * 9))
        _panos(p, t, 0.8, 6.0)
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


def abalanzarse(rig):
    L = 1.4

    def pose(t):
        p = Pose()
        agacha = suave(t, [(0.0, 0.0), (0.35, 1.0), (0.45, 0.6), (0.55, 0.0), (0.95, 0.0), (1.05, 0.8), (1.4, 0.0)])
        vuelo = _bulto(t, 0.45, 0.97)
        y = -7.0 * agacha + 16.0 * vuelo
        p.pos("raiz", y=y)
        lanza = suave(t, [(0.0, 0.0), (0.35, -0.3), (0.5, 1.0), (0.9, 1.0), (1.05, 0.4), (1.4, 0.0)])
        p.rot("cintura", rx=-12.0 * agacha - 38.0 * max(lanza, 0.0))
        p.rot("Head", rx=10.0 * agacha + 30.0 * max(lanza, 0.0))
        for k, s in LADO.items():
            p.rot(BRAZOS[k][0], rx=-40.0 * agacha * (1 - max(lanza, 0)) + 115.0 * max(lanza, 0.0), rz=s * 8.0 * max(lanza, 0))
            p.rot(BRAZOS[k][1], rx=10.0 + 25.0 * agacha)
        _manos(p, 15.0 - 40.0 * max(lanza, 0.0))
        _plumas(p, 0.6 * max(lanza, 0.0), 0.0)
        p.rot("plumas", rx=-20.0 * vuelo)
        _panos(p, t, 0.7, 8.0 + 10.0 * vuelo)
        # en el piso los pies se quedan; en el aire las piernas se van atras con el cuerpo
        objetivos = {}
        for k in PIERNAS:
            x, yy, z = _tobillo(rig, k, _z_pies(rig))
            objetivos[k] = ((x, yy + max(0.0, y) * 0.75 + 3.0 * vuelo, z + 9.0 * vuelo), -25.0 * vuelo)
        _plantar(rig, p, objetivos)
        return p
    return L, pose, False


def grito(rig):
    L = 2.2

    def pose(t):
        p = Pose()
        toma = _bulto(t, 0.0, 0.55)
        grita = suave(t, [(0.0, 0.0), (0.4, 0.0), (0.6, 1.0), (1.7, 1.0), (2.2, 0.0)])
        tiembla = math.sin(t * 38.0) * grita
        p.rot("cintura", rx=-8.0 * toma + 6.0 * grita + 0.6 * tiembla)
        p.rot("Body", rx=4.0 * grita)
        p.rot("Head", rx=-15.0 * toma + 34.0 * grita + 1.5 * tiembla, rz=-6.0 * grita)
        p.rot("mandibula", rx=-30.0 * grita)
        for k, s in LADO.items():
            p.rot(BRAZOS[k][0], rx=-10.0 * toma + 25.0 * grita, rz=s * (-6.0 * toma + 50.0 * grita + 1.2 * tiembla))
            p.rot(BRAZOS[k][1], rx=10.0 * toma + 15.0 * grita)
        _manos(p, 10.0 * toma - 30.0 * grita)
        _plumas(p, 1.0 * grita, 1.5 * tiembla)
        p.rot("plumas", rx=12.0 * grita)
        _panos(p, t, 0.5, 4.0 * grita)
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


def _encoger(p, e, hundir):
    p.pos("raiz", y=-62.0 * hundir)
    p.rot("cintura", rx=-28.0 * e)
    p.rot("Head", rx=-20.0 * e)
    for k, s in LADO.items():
        p.rot(BRAZOS[k][0], rx=35.0 * e, rz=-s * 18.0 * e)
        p.rot(BRAZOS[k][1], rx=45.0 * e)
    _manos(p, 30.0 * e)
    _plumas(p, -0.3 * e, 0.0)


def desvanecer(rig):
    L = 1.2

    def pose(t):
        p = Pose()
        e = facil(t / 0.5)
        h = facil((t - 0.45) / 0.65)
        _encoger(p, e, h)
        # mientras no se hunde, los pies en el piso; luego se van con el cuerpo
        if h <= 0.0:
            _plantar(rig, p, _quietos(rig))
        else:
            obj = {k: ((v[0][0], v[0][1] - 62.0 * h, v[0][2]), 0.0) for k, v in _quietos(rig).items()}
            _plantar(rig, p, obj)
        return p
    return L, pose, "hold_on_last_frame"


def aparecer(rig):
    L = 1.2

    def pose(t):
        p = Pose()
        h = 1.0 - facil(t / 0.6)
        e = 1.0 - facil((t - 0.55) / 0.65)
        _encoger(p, e, h)
        if h <= 0.0:
            _plantar(rig, p, _quietos(rig))
        else:
            obj = {k: ((v[0][0], v[0][1] - 62.0 * h, v[0][2]), 0.0) for k, v in _quietos(rig).items()}
            _plantar(rig, p, obj)
        return p
    return L, pose, False


def muerte(rig):
    L = 2.6

    def pose(t):
        p = Pose()
        retro = _bulto(t, 0.0, 0.6)
        rodillas = facil((t - 0.45) / 0.7)
        cae = facil((t - 1.15) / 0.75)
        p.pos("raiz", y=-12.0 * rodillas - 3.5 * cae, z=-6.0 * cae)
        p.rot("cintura", rx=14.0 * retro - 10.0 * rodillas - 60.0 * cae)
        p.rot("Head", rx=18.0 * retro - 10.0 * rodillas + 34.0 * cae, ry=28.0 * cae, rz=14.0 * cae)
        p.rot("mandibula", rx=-18.0 * retro - 4.0 * cae)
        for k, s in LADO.items():
            p.rot(BRAZOS[k][0], rx=40.0 * retro - 14.0 * cae, rz=s * (20.0 * retro + 40.0 * cae))
            p.rot(BRAZOS[k][1], rx=10.0 + 30.0 * cae)
        _manos(p, -20.0 * retro + 25.0 * cae)
        _plumas(p, 0.5 * retro - 0.4 * cae, 0.0)
        _panos(p, t, 0.9, 5.0 * (1 - cae))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, "hold_on_last_frame"


def mirar(rig):
    T = 1.6

    def pose(t):
        p = Pose()
        tiembla = 0.35 * math.sin(2 * math.pi * t / T * 6)
        p.rot("cintura", rx=-4.0)
        p.rot("Head", rx=6.0 + tiembla, rz=28.0, ry=-6.0)
        for k, s in LADO.items():
            p.rot(BRAZOS[k][0], rz=s * 4.0)
        _manos(p, -25.0 + tiembla * 4)
        _plumas(p, 0.35, 0.0)
        _plantar(rig, p, _quietos(rig))
        return p
    return T, pose, True


ANIMACIONES = {"quieto": quieto, "acechar": acechar, "correr": correr, "zarpazos": zarpazos,
               "abalanzarse": abalanzarse, "grito": grito, "desvanecer": desvanecer, "aparecer": aparecer,
               "muerte": muerte, "mirar": mirar}


def hornear_todas(rig, solo=None):
    """{nombre: (datos para el json, cuadros, bucle)}."""
    out = {}
    for nombre, f in ANIMACIONES.items():
        if solo and nombre not in solo:
            continue
        largo, pose, bucle = f(rig)
        datos, cuadros = animar.hornear(rig, nombre, largo, pose, bucle)
        out[nombre] = (datos, cuadros, bucle)
    return out
