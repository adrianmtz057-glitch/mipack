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


# ---------------------------------------------------------------- las del jefe (guerrero jaguar)
# Se arman con poses clave: en cada una se pone el cuerpo y las manos van con IK (animar.ik_libre) a un punto del
# mundo (en px del modelo: el frente es -Z; en el juego todo se ve 3 veces mas grande, un bloque son 5.3 px). Entre
# claves se interpola suave cada hueso y las piernas se vuelven a plantar en cada cuadro.

CODO = {"d": (-45.0, 140.0), "i": (-30.0, 140.0)}
AVISOS = []                    # (t, lado, px) de las manos que no llegaron a su punto
MANOS = {"d": "RightArm_antebrazo_mano", "i": "LeftArm_antebrazo_mano"}
# los momentos que usa el mod (segundos)
BARRIDO = (0.72, 1.0)          # la garra barre el piso entre estos dos tiempos
DARDO = 0.95                   # suelta el dardo
CONTRA = 0.25                  # el golpe del contraataque
AGARRA = 1.05                  # cierra la mano sobre la presa
SOLTAR = 0.1
SACRIFICIO = (0.6, 2.2, 2.8)   # la acuesta en la piedra, le saca el corazon, lo ofrece al cristal
INVOCA = 1.1                   # las manos pegan en el piso: sale la Xiuhcoatl
CORONA = 1.5                   # se rompe el yelmo


def _arco(s, phi, r, y, z0=0.0):
    """Punto a 'r' px del eje del cuerpo, a la altura y, en el angulo phi (0 = al frente, + = hacia el lado s)."""
    a = math.radians(phi)
    return (s * r * math.sin(a), y, z0 - r * math.cos(a))


def _clave(rig, t, llenar, objetivos=None, previa=None):
    """Una pose clave: llenar(p) pone el cuerpo; objetivos {lado: punto} lleva cada mano con IK."""
    p = Pose()
    llenar(p)
    for lado, obj in (objetivos or {}).items():
        if callable(obj):                                     # un punto pegado a otro hueso (ver _en_hueso)
            obj = obj(rig, p)
        cad = BRAZOS[lado]
        semilla = None
        if previa is not None and cad[0] in previa[1]:
            r = previa[1][cad[0]][0]
            semilla = [r[0], r[1], r[2], previa[1].get(cad[1], ((0, 0, 0), (0, 0, 0)))[0][0]]
        err = animar.ik_libre(rig, p, cad, obj, semilla=semilla, codo=CODO[lado])
        if err > 1.5:
            AVISOS.append((t, lado, round(err, 1)))
    return (t, p)


def _en_hueso(hueso, punto):
    """Objetivo que sigue a un hueso: 'punto' (en reposo) llevado por la pose de 'hueso' en esa clave."""
    return lambda rig, p: rig.transformaciones(p)[hueso](punto)


def _claves(rig, lista):
    """[(t, llenar, objetivos)] -> claves, cada una sembrada con la anterior (el brazo sigue un camino continuo)."""
    out = []
    for t, llenar, objetivos in lista:
        out.append(_clave(rig, t, llenar, objetivos, out[-1] if out else None))
    return out


def _entre(claves, t):
    """La pose interpolada (catmull-rom por hueso) entre las claves."""
    nombres = set()
    for _t, p in claves:
        nombres |= set(p)
    p = Pose()
    cero = ((0, 0, 0), (0, 0, 0))
    for h in nombres:
        v = suave(t, [(tk, tuple(pk.get(h, cero)[0]) + tuple(pk.get(h, cero)[1])) for tk, pk in claves])
        p[h] = ((v[0], v[1], v[2]), (v[3], v[4], v[5]))
    return p


def _nada(p):
    pass


def barrido(rig, lado="d"):
    """Corte de piernas: se agacha y echa el brazo atras (el aviso), barre el piso con la garra de atras hacia el otro
    lado (BARRIDO) y se recupera. s = 1 con la derecha, -1 con la izquierda."""
    L = 1.9
    s = LADO[lado]
    otro = "i" if lado == "d" else "d"

    def cuerpo(y, rx, ry, rz=0.0, z=0.0, cabeza=(0.0, 0.0), dedos=0.0, plumas=0.0):
        def llenar(p):
            p.pos("raiz", x=s * 1.5 * min(1.0, -y / 7.0), y=y, z=z)
            p.rot("cintura", rx=rx, ry=s * ry, rz=s * rz)
            p.rot("Head", rx=cabeza[0], ry=s * cabeza[1])
            p.rot(DEDOS[lado], rx=dedos)
            _plumas(p, plumas, 0.0)
        return llenar

    def contra(rx, rz):          # el otro brazo hace contrapeso (doblado: con el cuerpo vencido no toca el piso)
        def llenar(p):
            p.rot(BRAZOS[otro][0], rx=rx, rz=-s * rz)
            p.rot(BRAZOS[otro][1], rx=45.0)
        return llenar

    def junto(*fs):
        def llenar(p):
            for f in fs:
                f(p)
        return llenar

    lista = [(0.0, _nada, None)]
    lista.append((0.6, junto(cuerpo(-10.0, -34.0, -38.0, 4.0, 0.0, (-2.0, 14.0), -20.0, 0.4), contra(30.0, 8.0)),
                  {lado: _arco(s, 130.0, 19.0, 19.0)}))
    lista.append((0.7, junto(cuerpo(-10.5, -36.0, -42.0, 4.0, 0.0, (-2.0, 16.0), -25.0, 0.5), contra(32.0, 8.0)),
                  {lado: _arco(s, 140.0, 19.0, 18.0)}))
    n = 6
    for i in range(n + 1):
        u = facil(i / n)
        t = BARRIDO[0] + (BARRIDO[1] - BARRIDO[0]) * i / n
        phi = 130.0 - 225.0 * u
        lista.append((t, junto(cuerpo(-11.0 - 2.0 * u, -42.0 - 4.0 * u, -42.0 + 86.0 * u, 4.0 - 8.0 * u, -4.0 * u,
                                      (-4.0, 16.0 - 28.0 * u), -30.0, 0.6), contra(32.0 - 55.0 * u, 8.0 + 10.0 * u)),
                      {lado: _arco(s, phi, 22.0, 10.5, -4.0 * u)}))
    lista.append((1.15, junto(cuerpo(-11.0, -36.0, 50.0, -4.0, -4.0, (-2.0, -14.0), -10.0, 0.3), contra(-25.0, 18.0)),
                  {lado: _arco(s, -118.0, 20.0, 17.0, -4.0)}))
    lista.append((L, _nada, None))
    claves = _claves(rig, lista)

    def pose(t):
        p = _entre(claves, t)
        _panos(p, t, 0.6, 3.0 + 9.0 * _bulto(t, 0.6, 1.3))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


def barrido_i(rig):
    return barrido(rig, "i")


def lanzar_dardo(rig):
    """Atlatl: arranca una pluma del abanico, echa el brazo atras apuntando con la otra mano y la lanza (DARDO)."""
    L = 1.5

    def c(y=0.0, rx=0.0, ry=0.0, cab=(0.0, 0.0), dedos=0.0, apunta=0.0, plumas=0.0):
        def llenar(p):
            p.pos("raiz", y=y)
            p.rot("cintura", rx=rx, ry=ry)
            p.rot("Head", rx=cab[0], ry=cab[1])
            p.rot(DEDOS["d"], rx=dedos)
            p.rot(BRAZOS["i"][0], rx=apunta, rz=-6.0 * apunta / 70.0)
            p.rot(BRAZOS["i"][1], rx=-10.0 * apunta / 70.0)
            _plumas(p, plumas, 0.0)
        return llenar
    lista = [(0.0, _nada, None),
             (0.4, c(0.0, 6.0, 10.0, (4.0, 18.0), -25.0, 0.0, 0.5), {"d": (3.0, 59.0, -2.0)}),
             (0.5, c(0.0, 6.0, 10.0, (4.0, 18.0), 35.0, 10.0, 0.4), {"d": (2.0, 59.0, -1.0)}),
             (0.82, c(-2.0, 10.0, -30.0, (6.0, -6.0), 35.0, 75.0, 0.3), {"d": (14.0, 57.0, 12.0)}),
             (0.95, c(-3.0, -10.0, 18.0, (2.0, -8.0), -20.0, 60.0, 0.3), {"d": (9.0, 56.0, -24.0)}),
             (1.1, c(-4.0, -18.0, 28.0, (-6.0, -10.0), -10.0, 20.0, 0.2), {"d": (3.0, 33.0, -24.0)}),
             (L, _nada, None)]
    claves = _claves(rig, lista)

    def pose(t):
        p = _entre(claves, t)
        _panos(p, t, 0.6, 3.0 + 5.0 * _bulto(t, 0.8, 1.3))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


def _guardia_llenar(t, T):
    w = 2 * math.pi * t / T

    def llenar(p):
        p.pos("raiz", y=-4.0 + 0.5 * math.sin(w))
        p.rot("cintura", rx=-12.0 + 1.0 * math.sin(w))
        p.rot("Head", rx=-14.0, ry=4.0)
        for k in DEDOS:
            p.rot(DEDOS[k], rx=-15.0)
        _plumas(p, 1.0 + 0.1 * math.sin(w), 0.0)
    return llenar


def _guardia_manos(t, T):
    w = 2 * math.pi * t / T
    return {"d": (-1.0, 50.0 + 0.6 * math.sin(w), -21.0), "i": (3.0, 46.0 + 0.6 * math.sin(w + 0.8), -20.0)}


def guardia(rig):
    """Guardia del jaguar: cruza los brazos delante de la cara, agachado y con el abanico abierto (en bucle)."""
    T = 1.2
    lista = [(t, _guardia_llenar(t, T), _guardia_manos(t, T)) for t in (0.0, 0.3, 0.6, 0.9, 1.2)]
    claves = _claves(rig, lista)
    claves[-1] = (T, claves[0][1])                      # cierra el bucle exacto

    def pose(t):
        p = _entre(claves, t)
        _plantar(rig, p, _quietos(rig))
        return p
    return T, pose, True


def contraataque(rig):
    """Desde la guardia: abre los brazos de golpe en una X de garras hacia el frente (CONTRA)."""
    L = 0.9

    def c(y, rx, z=0.0, dedos=-15.0, plumas=1.0, cab=-14.0):
        def llenar(p):
            p.pos("raiz", y=y, z=z)
            p.rot("cintura", rx=rx)
            p.rot("Head", rx=cab, ry=4.0)
            for k in DEDOS:
                p.rot(DEDOS[k], rx=dedos)
            _plumas(p, plumas, 0.0)
        return llenar
    lista = [(0.0, _guardia_llenar(0.0, 1.2), _guardia_manos(0.0, 1.2)),
             (0.12, c(-6.0, -16.0, 0.0, 10.0, 1.1, -16.0), {"d": (-1.0, 48.0, -19.0), "i": (3.0, 44.0, -18.0)}),
             (0.25, c(-6.0, -22.0, -4.0, -35.0, 1.3, -4.0), {"d": (24.0, 30.0, -20.0), "i": (-24.0, 28.0, -20.0)}),
             (0.42, c(-5.0, -18.0, -4.0, -25.0, 1.0, -2.0), {"d": (25.0, 22.0, -6.0), "i": (-25.0, 20.0, -6.0)}),
             (L, _nada, None)]
    claves = _claves(rig, lista)

    def pose(t):
        p = _entre(claves, t)
        _panos(p, t, 0.5, 4.0 + 8.0 * _bulto(t, 0.1, 0.6))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


# donde queda la mano con la presa (cargar): a la altura de la cara, adelante
SOSTEN = {"d": (8.0, 44.0, -17.0), "i": (-8.0, 42.0, -17.0)}


def _sosten_llenar(lados, y=-1.0, rx=-8.0, dedos=45.0):
    def llenar(p):
        p.pos("raiz", y=y)
        p.rot("cintura", rx=rx)
        p.rot("Head", rx=-6.0, ry=-10.0 if lados == ("d",) else 0.0)
        for k in lados:
            p.rot(DEDOS[k], rx=dedos)
        _plumas(p, 0.3, 0.0)
    return llenar


def agarrar(rig, lados=("d",)):
    """Estira la mano despacio (el aviso), la cierra sobre la presa (AGARRA) y la levanta a la altura de la cara."""
    L = 1.7

    def c(y, rx, cab, dedos, plumas=0.2):
        def llenar(p):
            p.pos("raiz", y=y)
            p.rot("cintura", rx=rx)
            p.rot("Head", rx=cab, ry=-8.0 if lados == ("d",) else 0.0)
            for k in lados:
                p.rot(DEDOS[k], rx=dedos)
            _plumas(p, plumas, 0.0)
        return llenar

    def objs(*pts):
        return {k: (LADO[k] * abs(pt[0]), pt[1], pt[2]) for k in lados for pt in [pts[0] if k == "d" else pts[1]]}
    lista = [(0.0, _nada, None),
             (0.5, c(-7.0, -30.0, -12.0, -30.0, 0.5), objs((8.0, 22.0, -23.0), (8.0, 20.0, -23.0))),
             (0.9, c(-11.0, -42.0, -10.0, -35.0, 0.6), objs((7.0, 12.0, -26.0), (7.0, 12.0, -26.0))),
             (AGARRA, c(-11.5, -44.0, -10.0, 45.0, 0.6), objs((6.0, 10.0, -26.0), (6.0, 10.0, -26.0))),
             (1.4, c(-2.0, -12.0, -8.0, 45.0, 0.4), objs((8.0, 34.0, -20.0), (8.0, 32.0, -20.0))),
             (L, _sosten_llenar(lados), {k: SOSTEN[k] for k in lados})]
    claves = _claves(rig, lista)

    def pose(t):
        p = _entre(claves, t)
        _panos(p, t, 0.7, 3.0)
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, "hold_on_last_frame"


def agarrar_dos(rig):
    return agarrar(rig, ("d", "i"))


def cargar(rig, lados=("d",)):
    """Camina (rapido, encorvado) con la presa en alto; la mano aprieta a pulsos (en bucle)."""
    T, zancada, alto, apoyo = 1.6, 14.0, 4.0, 0.6
    base = _clave(rig, 0.0, _sosten_llenar(lados), {k: SOSTEN[k] for k in lados})[1]

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose({h: v for h, v in base.items()})
        p.pos("raiz", x=0.5 * math.sin(w), y=-1.0 + 0.8 * math.cos(2 * w))
        p.rot("cintura", rx=1.5 * math.sin(2 * w), ry=3.0 * math.sin(w))
        for k in lados:                                   # el brazo que carga apenas se mece; la mano aprieta
            p.rot(BRAZOS[k][0], rx=1.5 * math.sin(2 * w))
            p.rot(DEDOS[k], rx=6.0 * max(0.0, math.sin(2 * w)))
        for k in BRAZOS:
            if k not in lados:
                p.rot(BRAZOS[k][0], rx=-LADO[k] * 14.0 * math.cos(w), rz=LADO[k] * 2.0)
                p.rot(BRAZOS[k][1], rx=8.0 + 6.0 * math.sin(w + 1.0))
        _panos(p, t, T / 2, 5.0)
        _plantar(rig, p, {k: _paso(rig, k, t / T + f, zancada, alto, apoyo) for k, f in (("d", 0.0), ("i", 0.5))})
        return p
    return T, pose, True


def cargar_dos(rig):
    return cargar(rig, ("d", "i"))


def soltar(rig):
    """Le pegaron lo suficiente: abre la mano de golpe (SOLTAR), echa el brazo atras de dolor y se recupera."""
    L = 1.0
    base = _clave(rig, 0.0, _sosten_llenar(("d", "i")), dict(SOSTEN))

    def c(y, rx, cab, dedos):
        def llenar(p):
            p.pos("raiz", y=y, z=3.0 * (y < 0))
            p.rot("cintura", rx=rx)
            p.rot("Head", rx=cab[0], rz=cab[1])
            for k in DEDOS:
                p.rot(DEDOS[k], rx=dedos)
        return llenar
    lista = [base,
             (0.1, c(-1.0, 4.0, (10.0, 6.0), -35.0), {"d": (12.0, 52.0, -12.0), "i": (-12.0, 50.0, -12.0)}),
             (0.35, c(-2.0, 10.0, (16.0, -8.0), -20.0), {"d": (16.0, 40.0, 6.0), "i": (-16.0, 38.0, 6.0)}),
             (L, _nada, None)]
    claves = [lista[0]] + _claves(rig, [(t, f, o) for t, f, o in lista[1:]])

    def pose(t):
        p = _entre(claves, t)
        p.rot("Head", ry=8.0 * math.sin(t * 30.0) * _bulto(t, 0.1, 0.7))
        _panos(p, t, 0.5, 6.0 * _bulto(t, 0.0, 0.8))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


# la piedra del sacrificio queda enfrente: la presa acostada encima, a 1 bloque del piso
ALTAR = (0.0, 9.0, -24.0)


def sacrificio(rig):
    """En el cristal: acuesta a la presa en la piedra (SACRIFICIO[0]) y la detiene con la otra mano, alza la garra
    (el cuchillo de obsidiana), la clava y le saca el corazon (SACRIFICIO[1]) y lo ofrece al cristal (SACRIFICIO[2])."""
    L = 3.6
    base = _clave(rig, 0.0, _sosten_llenar(("d",)), {"d": SOSTEN["d"]})
    ax, ay, az = ALTAR

    def c(y, rx, cab, dd, di, plumas=0.3, jaw=0.0, ry=0.0):
        def llenar(p):
            p.pos("raiz", y=y)
            p.rot("cintura", rx=rx, ry=ry)
            p.rot("Head", rx=cab)
            p.rot("mandibula", rx=jaw)
            p.rot(DEDOS["d"], rx=dd)
            p.rot(DEDOS["i"], rx=di)
            _plumas(p, plumas, 0.0)
        return llenar
    lista = [(SACRIFICIO[0], c(-7.0, -30.0, -20.0, 40.0, 0.0), {"d": (ax + 5.0, ay + 6.0, az)}),
             (0.85, c(-8.0, -30.0, -20.0, -10.0, 35.0), {"d": (ax + 10.0, ay + 14.0, az + 4.0), "i": (ax - 4.0, ay + 4.0, az + 1.0)}),
             (1.6, c(-9.0, -22.0, 8.0, -30.0, 35.0, 1.0, -10.0, -10.0), {"d": (ax + 12.0, ay + 46.0, az + 14.0), "i": (ax - 4.0, ay + 4.0, az + 1.0)}),
             (2.0, c(-9.0, -21.0, 10.0, -32.0, 35.0, 1.1, -14.0, -12.0), {"d": (ax + 12.0, ay + 48.0, az + 15.0), "i": (ax - 4.0, ay + 4.0, az + 1.0)}),
             (SACRIFICIO[1], c(-10.0, -32.0, -24.0, -10.0, 35.0, 1.2, -24.0, 6.0), {"d": (ax + 2.0, ay + 5.0, az), "i": (ax - 4.0, ay + 4.0, az + 1.0)}),
             (2.35, c(-10.0, -32.0, -24.0, 40.0, 35.0, 1.2, -20.0, 6.0), {"d": (ax + 3.0, ay + 6.0, az), "i": (ax - 4.0, ay + 4.0, az + 1.0)}),
             (SACRIFICIO[2], c(-3.0, -6.0, 22.0, 40.0, 0.0, 1.3, -26.0, 0.0), {"d": (ax + 8.0, ay + 50.0, az + 6.0), "i": (ax - 18.0, ay + 22.0, az + 12.0)}),
             (3.1, c(-3.0, -5.0, 24.0, 40.0, 0.0, 1.3, -28.0, 0.0), {"d": (ax + 8.0, ay + 51.0, az + 6.0), "i": (ax - 18.0, ay + 23.0, az + 12.0)}),
             (L, _nada, None)]
    claves = [base] + _claves(rig, [(t, f, o) for t, f, o in lista])

    def pose(t):
        p = _entre(claves, t)
        tiembla = math.sin(t * 40.0) * _bulto(t, 1.6, 2.1) + 0.6 * math.sin(t * 33.0) * _bulto(t, 2.7, 3.2)
        p.rot("Head", rz=2.0 * tiembla)
        p.rot(BRAZOS["d"][0], rz=1.5 * tiembla)
        _panos(p, t, 0.6, 3.0 + 6.0 * _bulto(t, 2.0, 2.6))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


def invocar(rig):
    """La Xiuhcoatl: se alza con los brazos arriba y el abanico abierto, rugiendo, y azota las dos manos en el piso
    (INVOCA); se queda abajo un momento mientras sale el fuego."""
    L = 2.0

    def c(y, rx, cab, jaw, dedos, plumas):
        def llenar(p):
            p.pos("raiz", y=y)
            p.rot("cintura", rx=rx)
            p.rot("Head", rx=cab)
            p.rot("mandibula", rx=jaw)
            for k in DEDOS:
                p.rot(DEDOS[k], rx=dedos)
            _plumas(p, plumas, 0.0)
        return llenar
    lista = [(0.0, _nada, None),
             (0.7, c(0.5, 10.0, 18.0, -22.0, -25.0, 1.2), {"d": (9.0, 64.0, -2.0), "i": (-9.0, 63.0, -2.0)}),
             (0.85, c(0.5, 11.0, 20.0, -26.0, -25.0, 1.25), {"d": (9.0, 65.0, -1.0), "i": (-9.0, 64.0, -1.0)}),
             (INVOCA, c(-10.0, -42.0, -12.0, -10.0, -30.0, 0.9), {"d": (8.0, 13.5, -24.0), "i": (-8.0, 13.5, -24.0)}),
             (1.4, c(-10.0, -42.0, -10.0, -8.0, -20.0, 0.8), {"d": (8.0, 13.5, -24.0), "i": (-8.0, 13.5, -24.0)}),
             (L, _nada, None)]
    claves = _claves(rig, lista)

    def pose(t):
        p = _entre(claves, t)
        tiembla = math.sin(t * 36.0) * (_bulto(t, 0.6, 1.0) + _bulto(t, 1.1, 1.5))
        p.rot("cintura", rz=0.8 * tiembla)
        p.rot("Head", rz=1.5 * tiembla)
        _panos(p, t, 0.5, 3.0 + 9.0 * _bulto(t, 1.0, 1.6))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


def corona_rota(rig):
    """Pasa a la fase 2: le pegan, se tambalea, se agarra el yelmo y sacude la cabeza; el yelmo se rompe (CORONA:
    el mod lo esconde) y ruge con los brazos abiertos."""
    L = 3.0

    def c(y, z, rx, cab, jaw=0.0, dedos=0.0, plumas=0.0):
        def llenar(p):
            p.pos("raiz", y=y, z=z)
            p.rot("cintura", rx=rx)
            p.rot("Head", rx=cab[0], rz=cab[1])
            p.rot("mandibula", rx=jaw)
            for k in DEDOS:
                p.rot(DEDOS[k], rx=dedos)
            _plumas(p, plumas, 0.0)
        return llenar
    yelmo = {"d": _en_hueso("Head", (1.6, 45.5, -12.5)), "i": _en_hueso("Head", (-12.4, 45.0, -12.5))}
    lista = [(0.0, _nada, None),
             (0.25, c(-1.0, 5.0, 14.0, (20.0, 10.0), -12.0, -20.0, 0.3), {"d": (18.0, 34.0, 8.0), "i": (-18.0, 32.0, 8.0)}),
             (0.7, c(-4.0, 3.0, -16.0, (-14.0, -6.0), -8.0, 35.0, 0.0), yelmo),
             (1.45, c(-5.0, 3.0, -18.0, (-16.0, 6.0), -14.0, 35.0, 0.0), yelmo),
             (CORONA, c(-3.0, 3.0, 2.0, (24.0, 0.0), -24.0, -30.0, 0.8), {"d": (20.0, 42.0, -10.0), "i": (-22.0, 41.0, -10.0)}),
             (1.9, c(-1.0, 2.0, 8.0, (30.0, -4.0), -32.0, -30.0, 1.3), {"d": (26.0, 54.0, -2.0), "i": (-26.0, 53.0, -2.0)}),
             (2.5, c(-1.0, 2.0, 9.0, (31.0, 4.0), -32.0, -30.0, 1.3), {"d": (27.0, 55.0, -2.0), "i": (-27.0, 54.0, -2.0)}),
             (L, _nada, None)]
    claves = _claves(rig, lista)

    def pose(t):
        p = _entre(claves, t)
        sacude = _bulto(t, 0.65, 1.5)
        p.rot("Head", rz=12.0 * math.sin(t * 30.0) * sacude, ry=8.0 * math.sin(t * 23.0) * sacude)
        p.rot("cintura", rz=2.0 * math.sin(t * 30.0) * sacude + 1.0 * math.sin(t * 38.0) * _bulto(t, 1.8, 2.6))
        _panos(p, t, 0.5, 3.0 + 7.0 * _bulto(t, 0.0, 0.6) + 5.0 * _bulto(t, 1.5, 2.6))
        _plantar(rig, p, _quietos(rig))
        return p
    return L, pose, False


ANIMACIONES = {"quieto": quieto, "acechar": acechar, "correr": correr, "zarpazos": zarpazos,
               "abalanzarse": abalanzarse, "grito": grito, "desvanecer": desvanecer, "aparecer": aparecer,
               "muerte": muerte, "mirar": mirar,
               "barrido": barrido, "barrido_i": barrido_i, "lanzar_dardo": lanzar_dardo, "guardia": guardia,
               "contraataque": contraataque, "agarrar": agarrar, "agarrar_dos": agarrar_dos, "cargar": cargar,
               "cargar_dos": cargar_dos, "soltar": soltar, "sacrificio": sacrificio, "invocar": invocar,
               "corona_rota": corona_rota}


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
