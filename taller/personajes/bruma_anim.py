"""
Animaciones de La Bruma para GeckoLib, hechas desde Python con taller/animar.py (y revisadas con GIFs de la
reconstruccion de GeckoLib).

Cada animacion es una funcion pose(t) -> {hueso: ((rx, ry, rz) grados, (x, y, z) px)} con lo que se le SUMA al giro de
reposo de cada hueso (asi lo hace GeckoLib). La tela no se anima tira por tira a mano: cada tira se mece con una onda
que baja por sus tramos (cada tramo un poco despues y mas que el de arriba), con su propia fase y fuerza, y encima
se le suma lo de la animacion: abrirse hacia su cara (el grito, el giro), irse para atras (la estela al avanzar) o
temblar. La estela se reparte en cada tira segun hacia donde mira: a las de atras las abre, a las de los lados las
ladea y a las de enfrente las pega al cuerpo (sin atravesarlo).

  flotar      (bucle 4 s)   quieta en el aire: sube y baja, mira despacio, los dedos se mueven solos
  avanzar     (bucle 2 s)   se desliza hacia adelante, mas inclinada, con la tela en estela
  zarpazo     (1 s)         la garra derecha se echa atras y barre (golpe a los 0.5 s)
  agarrar     (0.8 s)       se lanza y cierra la mano (agarra a los 0.5 s)
  drenar      (bucle 2 s)   con la presa en alto, la cabeza encima, la tela latiendo hacia afuera
  grito       (2 s)         se encoge y grita con los brazos abiertos; la tela sale volando (a los 0.7 s)
  disolverse  (0.7 s)       se deshace hacia arriba (luego el modelo se esconde y viaja como bruma)
  aparecer    (0.7 s)       al reves
  jirones     (1.2 s)       gira sobre si misma y azota con las tiras (pega de 0.45 a 0.8 s)
  fase2       (2.4 s)       a media vida: se alza, se retuerce y la bruma crece
  muerte      (3 s)         se le cae la cabeza, se le caen los brazos y se hunde; la tela se apaga
"""

import math

from .. import animar
from . import bruma

PASO = 0.1                                 # 10 cuadros por segundo (GeckoLib interpola): la tela no necesita mas


def _azar(k):
    return (math.sin(k * 12.9898 + 78.233) * 43758.5453) % 1.0


TIRAS = [(t[0], float(t[3]), float(t[6]), len(t[5])) for t in bruma.TIRAS]   # nombre, hacia, abre, tramos
TRAMOS = "", "b", "c"
DEDOS = [f"{l}_dedo{k}{s}" for l in "di" for k in range(1, 5) for s in ("", "b", "c")]


def _bump(t, centro, ancho):
    """0 lejos, 1 en el centro: una campana suave."""
    u = (t - centro) / ancho
    return math.exp(-u * u)


def kf(t, puntos):
    """Entre llaves [(t, valor)] con entrada y salida suaves (sin pasarse como catmull-rom)."""
    if t <= puntos[0][0]:
        return puntos[0][1]
    for (t1, a), (t2, b) in zip(puntos, puntos[1:]):
        if t <= t2:
            u = animar.facil((t - t1) / (t2 - t1) if t2 > t1 else 1.0)
            if isinstance(a, (tuple, list)):
                return tuple(x + (y - x) * u for x, y in zip(a, b))
            return a + (b - a) * u
    return puntos[-1][1]


class Pose(dict):
    def gira(self, hueso, r, p=(0.0, 0.0, 0.0)):
        (r0, p0) = self.get(hueso, ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        self[hueso] = (tuple(a + b for a, b in zip(r0, r)), tuple(a + b for a, b in zip(p0, p)))
        return self


def tela(pose, t, w, amp=1.0, abre=0.0, estela=0.0, ladeo=0.0, sacude=0.0, wsacude=37.0, caida=0.0):
    """Mece todas las tiras. w: velocidad de la onda (rad/s; en un bucle, vueltas enteras por animacion); amp: que
    tanto; abre: grados hacia su cara (todas); estela: grados hacia atras; ladeo: grados de lado (el giro);
    sacude: temblor rapido; caida (0 a 1): cuanto se cierran hacia abajo (se descuelgan derechas)."""
    for k, (n, hacia, abre0, ntramos) in enumerate(TIRAS):
        f = 2 * math.pi * _azar(k)
        fuerza = 0.7 + 0.6 * _azar(k + 50)
        th = math.radians(hacia)
        d_abre = abre - estela * math.cos(th) - caida * abre0
        d_abre = max(d_abre, -(abre0 + 4.0))                  # las de enfrente no atraviesan el cuerpo
        d_lado = estela * math.sin(th) * 0.8 + ladeo
        for j in range(ntramos):
            a = amp * fuerza * (2.5, 5.0, 8.0)[j]
            fase = w * t - 0.9 * j + f
            rx = a * math.sin(fase) + sacude * (0.6 + 0.4 * j) * math.sin(wsacude * t + 3.0 * f + j)
            rz = 0.45 * a * math.sin(fase + 1.9)
            if j == 0:
                rx, rz = rx + d_abre, rz + d_lado
            else:                                              # los tramos siguen la curva un poco
                rx += 0.3 * max(d_abre, 0.0) - 0.4 * caida * abre0 / ntramos
                rz += 0.25 * d_lado
            pose.gira(n + TRAMOS[j], (rx, 0.0, rz))
    return pose


def dedos(pose, lado, curva, onda=0.0, t=0.0, w=0.0):
    """Abre (+) o cierra (-) los dedos de una mano; onda: que se muevan solos, uno tras otro."""
    for k in range(1, 5):
        for j, s in enumerate(("", "b", "c")):
            extra = onda * math.sin(w * t + 0.8 * k + 0.5 * j) if onda else 0.0
            pose.gira(f"{lado}_dedo{k}{s}", (curva * (0.7 + 0.2 * j) + extra, 0.0, 0.0))
    pose.gira(f"{lado}_pulgar", (curva * 0.6, 0.0, 0.0))
    return pose


# ---------------------------------------------------------------- las animaciones

def flotar(t, L=4.0):
    w = 2 * math.pi / L
    p = Pose()
    p.gira("raiz", (0.8 * math.sin(w * t + 1.0), 0.0, 1.2 * math.sin(w * t + 2.1)), (0.0, 0.9 * math.sin(w * t), 0.0))
    p.gira("torso", (1.5 * math.sin(w * t + 0.5), 0.0, 0.0))
    p.gira("cabeza", (2.0 * math.sin(w * t + 1.2), 6.0 * math.sin(w * t + 0.3), 0.0))
    p.gira("brazo_d", (3.0 * math.sin(w * t + 0.8), 2.0 * math.sin(w * t), 0.0))
    p.gira("antebrazo_d", (4.0 * math.sin(w * t + 1.4), 0.0, 0.0))
    p.gira("mano_d", (5.0 * math.sin(w * t + 2.0), 0.0, 0.0))
    p.gira("brazo_i", (-3.0 * math.sin(w * t + 0.2), 0.0, 2.0 * math.sin(w * t + 1.0)))
    p.gira("antebrazo_i", (5.0 * math.sin(w * t + 0.9), 0.0, 0.0))
    p.gira("mano_i", (4.0 * math.sin(w * t + 1.6), 0.0, 0.0))
    dedos(p, "d", 0.0, onda=7.0, t=t, w=2 * w)
    dedos(p, "i", 0.0, onda=5.0, t=t, w=2 * w)
    return tela(p, t, 2 * w, amp=1.0, abre=2.0 * math.sin(w * t))


def avanzar(t, L=2.0):
    w = 2 * math.pi / L
    p = Pose()
    p.gira("raiz", (-6.0, 0.0, 2.0 * math.sin(w * t)), (0.0, 0.6 * math.sin(2 * w * t), 0.0))
    p.gira("torso", (-6.0 + math.sin(w * t), 0.0, 0.0))
    p.gira("cabeza", (9.0, 3.0 * math.sin(w * t), 0.0))
    p.gira("brazo_d", (6.0 + 2.0 * math.sin(w * t), 0.0, 0.0))
    p.gira("antebrazo_d", (-4.0, 0.0, 0.0))
    p.gira("brazo_i", (-15.0 + 3.0 * math.sin(w * t + 1.0), 0.0, -8.0))
    p.gira("antebrazo_i", (-20.0, 0.0, 0.0))
    dedos(p, "d", 4.0, onda=4.0, t=t, w=2 * w)
    return tela(p, t, 2 * w, amp=1.3, estela=28.0)


def zarpazo(t):
    p = Pose()
    p.gira("brazo_d", kf(t, [(0, (0, 0, 0)), (0.35, (35, -25, 15)), (0.5, (-30, 40, -10)), (0.75, (-20, 30, -5)),
                             (1.0, (0, 0, 0))]))
    p.gira("antebrazo_d", kf(t, [(0, (0, 0, 0)), (0.35, (25, 0, 0)), (0.5, (-10, 0, 0)), (1.0, (0, 0, 0))]))
    p.gira("mano_d", kf(t, [(0, (0, 0, 0)), (0.35, (20, 0, 0)), (0.5, (-30, 0, 0)), (1.0, (0, 0, 0))]))
    dedos(p, "d", kf(t, [(0, 0.0), (0.35, 28.0), (0.48, -18.0), (0.8, -10.0), (1.0, 0.0)]))
    p.gira("torso", kf(t, [(0, (0, 0, 0)), (0.35, (2, 15, 0)), (0.5, (-8, -20, 0)), (1.0, (0, 0, 0))]))
    p.gira("cabeza", kf(t, [(0, (0, 0, 0)), (0.35, (0, 8, 0)), (0.5, (-4, -10, 0)), (1.0, (0, 0, 0))]))
    p.gira("brazo_i", kf(t, [(0, (0, 0, 0)), (0.5, (-10, 0, -15)), (1.0, (0, 0, 0))]))
    p.gira("raiz", (0, 0, 0), kf(t, [(0, (0, 0, 0)), (0.35, (0, 0.6, 1.0)), (0.5, (0, 0, -3)), (1.0, (0, 0, 0))]))
    return tela(p, t, 2 * math.pi, amp=1.0 + 1.5 * _bump(t, 0.5, 0.15), estela=15.0 * _bump(t, 0.58, 0.15))


def agarrar(t):
    p = Pose()
    p.gira("raiz", (kf(t, [(0, 0.0), (0.45, -8.0), (0.8, -3.0)]), 0, 0),
           kf(t, [(0, (0, 0, 0)), (0.3, (0, 0.5, 1.0)), (0.5, (0, 0.5, -5)), (0.8, (0, 1.5, -2))]))
    p.gira("brazo_d", kf(t, [(0, (0, 0, 0)), (0.3, (-10, 0, 0)), (0.5, (10, 5, 0)), (0.8, (20, 0, 0))]))
    p.gira("antebrazo_d", kf(t, [(0, (0, 0, 0)), (0.3, (20, 0, 0)), (0.5, (-8, 0, 0)), (0.8, (-10, 0, 0))]))
    p.gira("mano_d", kf(t, [(0, (0, 0, 0)), (0.3, (15, 0, 0)), (0.5, (-15, 0, 0)), (0.8, (-10, 0, 0))]))
    dedos(p, "d", kf(t, [(0, 0.0), (0.3, 32.0), (0.46, 30.0), (0.55, -24.0), (0.8, -20.0)]))
    p.gira("cabeza", kf(t, [(0, (0, 0, 0)), (0.5, (-8, -10, 0)), (0.8, (-8, -15, 0))]))
    p.gira("brazo_i", kf(t, [(0, (0, 0, 0)), (0.5, (-10, 0, -20)), (0.8, (-10, 0, -35))]))
    p.gira("antebrazo_i", kf(t, [(0, (0, 0, 0)), (0.8, (-30, 0, 0))]))
    return tela(p, t, 2 * math.pi * 1.2, amp=1.2, estela=20.0 * _bump(t, 0.5, 0.18), abre=10.0 * animar.facil(t / 0.8))


def drenar(t, L=2.0):
    w = 2 * math.pi / L
    p = Pose()
    p.gira("raiz", (-3.0, 0.0, 0.0), (0.0, 1.5 + 0.8 * math.sin(w * t), -2.0))
    p.gira("torso", (0.8 * math.sin(w * t), 0.0, 0.0))
    p.gira("brazo_d", (20.0 + 3.0 * math.sin(w * t), 0.0, 0.0))
    p.gira("antebrazo_d", (-10.0, 0.0, 0.0))
    p.gira("mano_d", (-10.0, 0.0, 0.0))
    dedos(p, "d", -20.0, onda=3.0, t=t, w=2 * w)
    p.gira("cabeza", (-8.0 + 4.0 * math.sin(w * t), -15.0, 0.0))
    p.gira("brazo_i", (-10.0, 0.0, -35.0 + 4.0 * math.sin(w * t + 1.0)))
    p.gira("antebrazo_i", (-30.0, 0.0, 0.0))
    dedos(p, "i", 15.0, onda=8.0, t=t, w=2 * w)
    return tela(p, t, 2 * w, amp=0.8, abre=10.0 + 8.0 * math.sin(2 * w * t))


def grito(t):
    p = Pose()
    p.gira("torso", kf(t, [(0, (0, 0, 0)), (0.55, (-12, 0, 0)), (0.75, (12, 0, 0)), (1.6, (10, 0, 0)), (2.0, (0, 0, 0))]))
    p.gira("cabeza", kf(t, [(0, (0, 0, 0)), (0.55, (-15, 0, 0)), (0.75, (30, 0, 0)), (1.6, (26, 0, 0)), (2.0, (0, 0, 0))]))
    p.gira("brazo_d", kf(t, [(0, (0, 0, 0)), (0.55, (-30, 10, 0)), (0.75, (-20, -45, 30)), (1.6, (-18, -40, 28)),
                             (2.0, (0, 0, 0))]))
    p.gira("antebrazo_d", kf(t, [(0, (0, 0, 0)), (0.55, (25, 0, 0)), (0.75, (-6, 0, 0)), (2.0, (0, 0, 0))]))
    p.gira("brazo_i", kf(t, [(0, (0, 0, 0)), (0.55, (-20, 0, 10)), (0.75, (60, 0, -60)), (1.6, (55, 0, -55)),
                             (2.0, (0, 0, 0))]))
    p.gira("antebrazo_i", kf(t, [(0, (0, 0, 0)), (0.55, (10, 0, 0)), (0.75, (-70, 0, 0)), (1.6, (-65, 0, 0)),
                                 (2.0, (0, 0, 0))]))
    abre_dedos = kf(t, [(0, 0.0), (0.55, -15.0), (0.75, 35.0), (1.6, 30.0), (2.0, 0.0)])
    dedos(p, "d", abre_dedos)
    dedos(p, "i", abre_dedos)
    p.gira("raiz", (0, 0, 0), kf(t, [(0, (0, 0, 0)), (0.55, (0, -1, 0)), (0.75, (0, 3, 0)), (1.6, (0, 2.5, 0)),
                                     (2.0, (0, 0, 0))]))
    fuerte = kf(t, [(0, 0.0), (0.55, 0.0), (0.72, 1.0), (1.5, 0.8), (2.0, 0.0)])
    return tela(p, t, 2 * math.pi, amp=1.0, abre=-3.0 + 41.0 * fuerte, sacude=7.0 * fuerte)


def disolverse(t, L=0.7):
    u = animar.facil(t / L)
    p = Pose()
    p.gira("raiz", (0, 0, 0), (0.0, 4.0 * u, 0.0))
    p.gira("brazo_d", (20.0 * u, 0.0, 0.0))
    p.gira("brazo_i", (90.0 * u, 0.0, -20.0 * u))
    p.gira("antebrazo_i", (-60.0 * u, 0.0, 0.0))
    p.gira("cabeza", (25.0 * u, 0.0, 0.0))
    dedos(p, "d", 25.0 * u)
    dedos(p, "i", 25.0 * u)
    return tela(p, t, 2 * math.pi * 1.5, amp=1.0, abre=55.0 * u, sacude=4.0 * u)


def aparecer(t, L=0.7):
    return disolverse(L - t, L)


def jirones(t):
    p = Pose()
    giro = kf(t, [(0, 0.0), (0.25, -20.0), (0.8, 360.0), (1.2, 360.0)])
    p.gira("raiz", (0.0, giro, 0.0), (0.0, kf(t, [(0, 0.0), (0.5, 2.0), (1.2, 0.0)]), 0.0))
    p.gira("brazo_i", kf(t, [(0, (0, 0, 0)), (0.3, (60, 0, -50)), (0.85, (60, 0, -50)), (1.2, (0, 0, 0))]))
    p.gira("antebrazo_i", kf(t, [(0, (0, 0, 0)), (0.3, (-60, 0, 0)), (0.85, (-60, 0, 0)), (1.2, (0, 0, 0))]))
    p.gira("brazo_d", kf(t, [(0, (0, 0, 0)), (0.3, (-10, -30, 20)), (0.85, (-10, -30, 20)), (1.2, (0, 0, 0))]))
    fuerte = kf(t, [(0, 0.0), (0.3, 0.3), (0.5, 1.0), (0.85, 1.0), (1.2, 0.0)])
    return tela(p, t, 2 * math.pi * 1.5, amp=1.0, abre=40.0 * fuerte, ladeo=-25.0 * fuerte, sacude=3.0 * fuerte)


def fase2(t):
    p = Pose()
    sube = kf(t, [(0, 0.0), (0.5, -1.0), (0.9, 1.0), (2.0, 1.0), (2.4, 0.0)])
    p.gira("raiz", (0, 0, 0), (0.0, 6.0 * max(sube, 0.0) - 1.0 * max(-sube, 0.0), 0.0))
    p.gira("torso", kf(t, [(0, (0, 0, 0)), (0.5, (-15, 0, 0)), (0.9, (14, 0, 0)), (2.0, (10, 0, 0)), (2.4, (0, 0, 0))]))
    retuerce = 12.0 * math.sin(2 * math.pi * 2.5 * t) * kf(t, [(0, 0.0), (0.9, 1.0), (2.0, 1.0), (2.4, 0.0)])
    p.gira("cabeza", kf(t, [(0, (0, 0, 0)), (0.5, (-20, 0, 0)), (0.9, (35, 0, 0)), (2.0, (30, 0, 0)), (2.4, (0, 0, 0))]))
    p.gira("cabeza", (0.0, retuerce, retuerce * 0.5))
    p.gira("brazo_d", kf(t, [(0, (0, 0, 0)), (0.5, (-30, 10, 0)), (0.9, (-15, -50, 35)), (2.0, (-12, -45, 30)),
                             (2.4, (0, 0, 0))]))
    p.gira("brazo_i", kf(t, [(0, (0, 0, 0)), (0.5, (-20, 0, 10)), (0.9, (75, 0, -65)), (2.0, (70, 0, -60)),
                             (2.4, (0, 0, 0))]))
    p.gira("antebrazo_i", kf(t, [(0, (0, 0, 0)), (0.9, (-70, 0, 0)), (2.0, (-65, 0, 0)), (2.4, (0, 0, 0))]))
    abre_dedos = kf(t, [(0, 0.0), (0.5, -20.0), (0.9, 38.0), (2.0, 32.0), (2.4, 0.0)])
    dedos(p, "d", abre_dedos, onda=10.0, t=t, w=14.0)
    dedos(p, "i", abre_dedos, onda=10.0, t=t, w=14.0)
    fuerte = kf(t, [(0, 0.0), (0.5, 0.0), (0.9, 1.0), (2.0, 0.9), (2.4, 0.0)])
    return tela(p, t, 2 * math.pi * 1.5, amp=1.2, abre=48.0 * fuerte, sacude=8.0 * fuerte)


def muerte(t):
    p = Pose()
    p.gira("cabeza", kf(t, [(0, (0, 0, 0)), (0.3, (35, 0, 0)), (1.2, (-30, 10, 0)), (3.0, (-40, 15, 0))]))
    p.gira("brazo_d", kf(t, [(0, (0, 0, 0)), (0.3, (-10, -30, 20)), (1.4, (-100, 0, 0)), (3.0, (-105, 0, 5))]))
    p.gira("antebrazo_d", kf(t, [(0, (0, 0, 0)), (1.4, (-6, 0, 0))]))
    p.gira("brazo_i", kf(t, [(0, (0, 0, 0)), (0.3, (40, 0, -40)), (1.4, (-30, 0, 10)), (3.0, (-32, 0, 12))]))
    p.gira("antebrazo_i", kf(t, [(0, (0, 0, 0)), (0.3, (-50, 0, 0)), (1.4, (-75, 0, 0))]))
    afloja = kf(t, [(0, 0.0), (0.3, 30.0), (1.4, 18.0)])
    dedos(p, "d", afloja)
    dedos(p, "i", afloja)
    p.gira("torso", kf(t, [(0, (0, 0, 0)), (0.3, (10, 0, 0)), (1.6, (22, 0, 4)), (3.0, (26, 0, 6))]))
    p.gira("raiz", kf(t, [(0, (0, 0, 0)), (1.0, (-5, 0, 6)), (3.0, (-15, 0, 25))]),
           kf(t, [(0, (0, 0, 0)), (0.3, (0, 1.5, 0)), (3.0, (0, -14, 2))]))
    vida = kf(t, [(0, 1.0), (0.4, 1.4), (3.0, 0.0)])
    return tela(p, t, 2 * math.pi, amp=vida, caida=kf(t, [(0, 0.0), (0.4, 0.0), (2.5, 1.0)]),
                sacude=6.0 * _bump(t, 0.3, 0.2))


# nombre: (funcion, largo en segundos, bucle; True, False = se queda en el ultimo cuadro, "play_once")
ANIMACIONES = {
    "flotar": (flotar, 4.0, True),
    "avanzar": (avanzar, 2.0, True),
    "zarpazo": (zarpazo, 1.0, False),
    "agarrar": (agarrar, 0.8, False),
    "drenar": (drenar, 2.0, True),
    "grito": (grito, 2.0, False),
    "disolverse": (disolverse, 0.7, False),
    "aparecer": (aparecer, 0.7, False),
    "jirones": (jirones, 1.2, False),
    "fase2": (fase2, 2.4, False),
    "muerte": (muerte, 3.0, False),
}


def hornear_todas(rig):
    """{nombre: (datos del archivo, cuadros, bucle)}. El giro de jirones va a 20 cuadros por segundo."""
    out = {}
    for nombre, (f, largo, bucle) in ANIMACIONES.items():
        paso = animar.PASO if nombre == "jirones" else PASO
        datos, cuadros = animar.hornear(rig, nombre, largo, f, bucle=bucle, paso=paso)
        out[nombre] = (datos, cuadros, bucle)
    return out
