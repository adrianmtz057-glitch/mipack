"""
CANDIL, el ajolote del lodo: el titan del pantano (ver la hoja de titanes del usuario). Un ajolote enorme, hundido en
el lodo con solo la cabeza y los ojos afuera, la espalda cubierta de nenufares, musgo y hongos que brillan azul de
noche, y las seis branquias de pluma moradas con puntas que brillan. Casi siempre esta quieto; a ratos se mueve a
otro charco y atrapa algo.
Escala: el modelo se dibuja 4 veces mas grande (1 px = 1/4 de bloque): mide unos 26 bloques de la boca a la cola, la
cabeza 8 de ancho y con las branquias levantadas unos 7 de alto. El origen va en la panza; en el juego se hunde un
bloque en el fondo (en un pantano queda con la espalda al ras del agua) y quieto o dormido se hunde mas.
Huesos: raiz / cuerpo / (cabeza / mandibula, branquias_d1..3, branquias_i1..3), cola1 / cola2 / cola3, y las cuatro
patas (pata_dd, pata_di, pata_td, pata_ti: delantera o trasera, derecha o izquierda).
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER, voxel

ESCALA = 4.0
PIEL = tonos("#4A3F38")                 # lodo oscuro
PANZA = tonos("#7E6B55")
MANCHA = "#2E2724"
BRILLO = tonos("#5FE0FF")               # los puntos y las puntas que brillan
BRANQUIA = tonos("#9A4FD0")
HOJA = tonos("#3E8E3A")
HONGO = tonos("#4FB8FF")
TALLO = tonos("#D8D0B8")
OJO = "#14181C"

BRILLAN = [BRILLO[k] for k in ("b", "l", "h")] + [HONGO[k] for k in ("b", "l", "h")] + [BRANQUIA[k] for k in ("l", "h")]
CABEZA = (16.0, 14.0, (-40.0, -12.0))   # medio ancho, alto, z de adelante y de atras
CUELLO = (0.0, 7.0, -13.0)              # pivote de la cabeza
CUERPO = ((-13.0, 26.0), 12.0, 13.0)    # z, medio ancho, alto
COLA = ((26.0, 40.0), (40.0, 54.0), (54.0, 68.0))
PATAS = {"dd": (1, -6.0), "di": (-1, -6.0), "td": (1, 18.0), "ti": (-1, 18.0)}


def _puntos(t, densidad=0.06):
    """Los puntos que brillan (siempre los mismos, pocos y salteados)."""
    cu = math.floor(t.x * 0.7 + 100)
    cv = math.floor((t.z if t.cara in ("up", "down") else t.y + t.z * 0.5) * 0.7 + 100)
    return (cu * 7 + cv * 13) % 23 == 0 and BAYER[cv % 4][cu % 4] < 8 * densidad / 0.06


def piel(claro=0.0):
    """Lodo: casi liso (tres tonos cercanos), manchas oscuras grandes y los puntos que brillan."""
    s, b, l = hex_(PIEL["s"]), hex_(PIEL["b"]), hex_(PIEL["l"])
    medio = tuple((x + y) // 2 for x, y in zip(b, l))
    panza = voxel(PANZA, 0.05)

    def p(t):
        if t.cara == "down":
            return panza(t)
        if _puntos(t):
            return hex_(BRILLO["l"])
        u = t.x
        v = t.z if t.cara == "up" else t.y + 0.4 * t.z
        if math.sin(u * 0.35 + 1.0) * math.sin(v * 0.3 - 0.5) + 0.4 * math.sin(u * 0.9 + v * 0.7) > 0.75:
            return hex_(MANCHA)
        cu, cv = math.floor(u + 100), math.floor(v + 100)
        f = 0.5 + 0.18 * math.sin(cu * 0.9 + cv * 0.5) + claro + ((BAYER[cv % 4][cu % 4] + 0.5) / 16 - 0.5) * 0.3
        if t.cara == "up":
            f += 0.1
        return s if f < 0.3 else b if f < 0.72 else medio
    return p


def _branquia(t):
    """Una pluma de branquia: el raquis claro, los filamentos morados en diagonal y la punta que brilla."""
    u, v = t.i / max(1, t.tw - 1) - 0.5, 1 - t.j / max(1, t.th - 1)
    if abs(u) > 0.5 - 0.3 * abs(v - 0.55) * 1.6 or v > 0.97:
        return TRANSPARENTE
    if v < 0.18:
        return hex_(BRILLO["h"] if abs(u) < 0.2 else BRILLO["l"])
    if abs(u) < 0.08:
        return hex_(BRANQUIA["h"])
    if (abs(u) * 6 + v * 8) % 2 < 0.7:
        return hex_(BRANQUIA["s"])
    return hex_(BRANQUIA["b"] if abs(u) < 0.3 else BRANQUIA["l"])


def _ojo(t):
    u, v = t.i / max(1, t.tw - 1) - 0.5, t.j / max(1, t.th - 1) - 0.5
    d = math.hypot(u, v)
    if d < 0.28:
        return hex_(OJO)
    if d < 0.4:
        return hex_(BRILLO["b"])
    return hex_(PIEL["s"])


def _nenufar(t):
    """Un nenufar visto desde arriba: disco verde con un corte y las venas."""
    u, v = t.i / max(1, t.tw - 1) - 0.5, t.j / max(1, t.th - 1) - 0.5
    d = math.hypot(u, v)
    if d > 0.5 or (u > 0 and abs(v) < 0.08):
        return TRANSPARENTE
    a = math.atan2(v, u)
    if abs(math.sin(a * 4)) < 0.12:
        return hex_(HOJA["s"])
    return hex_(HOJA["l"] if d < 0.2 else HOJA["b"])


def _sombrero(t):
    if t.cara == "down":
        return hex_(HONGO["s2"])
    cu, cv = math.floor(t.x * 2 + 100), math.floor(t.z * 2 + 100)
    if (cu * 3 + cv * 5) % 7 == 0:
        return hex_(HONGO["h"])
    return hex_(HONGO["l"] if t.cara == "up" else HONGO["b"])


def _boca(t):
    """La cara de adelante de la cabeza: la sonrisa ancha del ajolote."""
    base = piel(0.05)
    if t.cara == "north":
        u = t.x / CABEZA[0]
        linea = 4.5 + 2.0 * u * u
        if abs(t.y - linea) < 0.45 and abs(u) < 0.85:
            return hex_(MANCHA)
    return base(t)


def construir():
    p = Personaje("candil")
    hx, hy, (z0, z1) = CABEZA
    G = "raiz/cuerpo"
    C = f"{G}/cabeza"
    # cabeza: ancha y plana, con los cachetes y la mandibula aparte
    p.caja(C, "craneo", (-hx, 5.0, z0), (hx, hy, z1), _boca, dens=2)
    p.caja(C, "frente", (-hx + 3.0, hy, z0 + 3.0), (hx - 3.0, hy + 1.5, z1 - 1.0), piel(0.1), dens=2)
    p.caja(f"{C}/mandibula", "mandibula", (-hx + 1.0, 0.5, z0 + 1.0), (hx - 1.0, 5.0, z1), piel(), dens=2)
    for s in (1, -1):
        lado = "d" if s > 0 else "i"
        x0, x1 = sorted((s * (hx - 1.0), s * (hx + 0.6)))
        p.caja(C, f"ojo_{lado}", (x0, 9.5, z0 + 6.0), (x1, 13.0, z0 + 10.5), _ojo, dens=4)
        # tres branquias por lado, de pluma: salen del costado de la nuca y se abren hacia arriba y atras
        for k, (y, abre) in enumerate(((12.5, 20.0), (9.0, 48.0), (5.5, 76.0))):
            g = f"{C}/branquias_{lado}{k + 1}"
            base = (s * (hx - 1.0), y, z1 - 3.0)
            largo = 17.0 - 2.0 * k
            p.m.cubo(g, f"branquia_{lado}{k}", (base[0], base[1], base[2] - 3.6), (base[0], base[1] + largo, base[2] + 3.6),
                     _branquia, rot=(-28.0, 0.0, -s * abre), origen=base, dens=2, luz=False)
            p.m.cubo(g, f"raquis_{lado}{k}", (base[0] - 0.4, base[1], base[2] - 0.4), (base[0] + 0.4, base[1] + largo * 0.9, base[2] + 0.4),
                     lambda t: hex_(BRANQUIA["h"]), rot=(-28.0, 0.0, -s * abre), origen=base, dens=2, luz=False)
            p.m.pivotes[g] = base
    # cuerpo
    (b0, b1), bw, bh = CUERPO
    perfil = geo.loft([(b0, 0.0, 0.0, bw, bh / 2), (b0 + 14, 0.0, 0.0, bw + 1.0, bh / 2 + 0.5), (b1, 0.0, 0.0, bw - 3.0, bh / 2 - 1.0)],
                      8, 22.5)
    # loft va de abajo hacia arriba en y: lo acostamos para que vaya a lo largo de z
    cuerpo = geo.girar(perfil, (90.0, 0.0, 0.0))
    cuerpo = geo.mover(cuerpo, (0.0, bh / 2, 0.0))
    p.malla(G, "tronco", cuerpo, piel(), dens=1)
    # la espalda: musgo, nenufares y hongos
    for i, (x, z, r) in enumerate(((-6.0, -7.0, 6.0), (6.0, 1.0, 6.5), (-4.0, 12.0, 5.5), (7.0, 19.0, 4.5), (-1.0, 24.0, 4.0))):
        y = bh + 0.6
        p.m.cubo(f"{G}", f"nenufar_{i}", (x - r, y, z - r), (x + r, y, z + r), _nenufar, dens=3, luz=False)
    for i, (x, z, h, r) in enumerate(((2.0, -10.0, 5.0, 3.0), (-8.0, 3.0, 3.5, 2.2), (8.5, 9.0, 6.5, 3.4), (-3.0, 18.0, 4.5, 2.6),
                                      (4.0, 25.0, 3.0, 2.0), (-7.0, -2.0, 2.5, 1.6))):
        y = bh - 0.5
        p.caja(G, f"tallo_{i}", (x - 0.5, y, z - 0.5), (x + 0.5, y + h, z + 0.5), voxel(TALLO), dens=2)
        p.caja(G, f"sombrero_{i}", (x - r, y + h, z - r), (x + r, y + h + 1.4, z + r), _sombrero, dens=2)
    # la aleta del lomo (de la mitad del cuerpo a la cola)
    p.m.cubo(G, "aleta_lomo", (0.0, bh - 1.0, 6.0), (0.0, bh + 2.5, b1), lambda t: hex_(PIEL["l"] if t.j < 1 else PIEL["s"]),
             dens=2, luz=False)
    # cola en tres tramos que se angostan, con la aleta arriba y abajo
    ruta = G
    for k, (c0, c1) in enumerate(COLA):
        ruta = f"{ruta}/cola{k + 1}"
        w = 9.0 - 2.6 * k
        h = 10.0 - 2.5 * k
        y0 = 1.5 + k * 1.0
        p.caja(ruta, f"cola_{k + 1}", (-w, y0, c0 - 0.5), (w, y0 + h, c1), piel(), dens=1)
        p.m.cubo(ruta, f"aleta_{k + 1}", (0.0, y0 - 3.0 - k, c0), (0.0, y0 + h + 4.0 + k, c1 + (3.0 if k == 2 else 0.0)),
                 lambda t: hex_(BRILLO["l"] if _puntos(t, 0.1) else PIEL["l"] if t.j < 2 else PIEL["b"]), dens=2, luz=False)
        p.m.pivotes[ruta] = (0.0, y0 + h / 2, c0)
    # patas cortas con cuatro dedos
    for nombre, (s, z) in PATAS.items():
        g = f"{G}/pata_{nombre}"
        x = s * (bw - 1.0)
        x0, x1 = sorted((x, x + s * 6.0))
        p.caja(g, f"brazo_{nombre}", (x0, 1.0, z - 2.5), (x1, 6.0, z + 2.5), piel(), dens=1)
        xa, xb = sorted((x + s * 5.0, x + s * 8.5))
        p.caja(g, f"mano_{nombre}", (xa, 0.0, z - 3.5), (xb, 1.5, z + 3.5), voxel(PANZA), dens=1)
        for d in range(4):
            dz = z - 3.0 + d * 2.0
            dx0, dx1 = sorted((x + s * 8.5, x + s * 10.5))
            p.caja(g, f"dedo_{nombre}{d}", (dx0, 0.0, dz - 0.5), (dx1, 1.0, dz + 0.5), voxel(PANZA, 0.1), dens=2)
        p.m.pivotes[g] = (x, 3.5, z)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), G: (0.0, 6.0, 0.0), C: CUELLO, f"{C}/mandibula": (0.0, 5.0, z1)})
    for k in [k for k in list(p.m.pivotes) if k in ("Head", "Body", "RightArm", "LeftArm", "RightLeg", "LeftLeg")]:
        del p.m.pivotes[k]
    return p


# ---------------------------------------------------------------- animaciones

from .. import animar                                    # noqa: E402
from ..animar import facil, suave                        # noqa: E402
from .crackatos_anim import Pose                         # noqa: E402

BRANQUIAS = [f"branquias_{l}{k}" for l in "di" for k in (1, 2, 3)]
COLAS = ("cola1", "cola2", "cola3")
PATAS_H = ("pata_dd", "pata_di", "pata_td", "pata_ti")


def _branquias(p, t, abre=0.0, amp=4.0, vel=1.0):
    for i, h in enumerate(BRANQUIAS):
        s = 1 if h[10] == "d" else -1
        p.rot(h, rz=s * (abre + amp * math.sin(t * vel * 2.0 + i * 0.9)), rx=1.5 * math.sin(t * vel + i))


def _hundido(p, y):
    p.pos("raiz", y=y)


def quieto(rig):
    """En el agua con solo la cabeza afuera: respira (sube y baja), las branquias se mecen y la cola apenas se mueve."""
    T = 6.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _hundido(p, -3.0 + 0.4 * math.sin(w))
        p.rot("cabeza", rx=6.0 + 1.0 * math.sin(w + 0.5), ry=2.0 * math.sin(w * 0.5 * 2))
        _branquias(p, t, 0.0, 5.0, 2 * math.pi / T * 2)
        for k, h in enumerate(COLAS):
            p.rot(h, ry=4.0 * math.sin(w - k * 0.8))
        for h in PATAS_H:
            p.rot(h, rz=(10.0 if h[-1] == "d" else -10.0))
        return p
    return T, pose, True


def mover(rig):
    """Repta por el lodo: una onda que va de la cabeza a la cola, las patas remando cruzadas y la cabeza compensando."""
    T = 2.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _hundido(p, 0.6 * math.cos(2 * w))
        p.rot("cuerpo", ry=6.0 * math.sin(w))
        p.rot("cabeza", ry=-5.0 * math.sin(w - 0.4), rx=3.0)
        for k, h in enumerate(COLAS):
            p.rot(h, ry=12.0 * math.sin(w - (k + 1) * 0.9))
        for h, f in (("pata_dd", 0.0), ("pata_ti", 0.0), ("pata_di", math.pi), ("pata_td", math.pi)):
            s = 1 if h[-1] == "d" else -1
            p.rot(h, ry=-s * 25.0 * math.sin(w + f), rz=s * (8.0 + 10.0 * max(0.0, math.cos(w + f))))
        _branquias(p, t, -15.0, 3.0, 2 * math.pi / T)
        return p
    return T, pose, True


def asentarse(rig):
    """Se hunde en el lodo hasta los ojos: baja, recoge las patas y echa las branquias hacia atras."""
    L = 3.0

    def pose(t):
        u = facil(t / L)
        p = Pose()
        _hundido(p, -3.0 - 6.0 * u)
        p.rot("cabeza", rx=6.0 + 6.0 * u)
        _branquias(p, t, -20.0 * u, 4.0 * (1 - u) + 1.0, 2.0)
        for h in PATAS_H:
            p.rot(h, rz=(10.0 + 25.0 * u) * (1 if h[-1] == "d" else -1))
        for k, h in enumerate(COLAS):
            p.rot(h, ry=6.0 * u * (1 if k % 2 else -1))
        return p
    return L, pose, "hold_on_last_frame"


def descansar(rig):
    """Dormido en el lodo: solo los ojos y las branquias afuera, que laten despacio."""
    T = 8.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _hundido(p, -9.0 + 0.3 * math.sin(w))
        p.rot("cabeza", rx=12.0)
        _branquias(p, t, -20.0 + 6.0 * (0.5 + 0.5 * math.sin(w)), 1.5, 2 * math.pi / T * 3)
        for h in PATAS_H:
            p.rot(h, rz=35.0 * (1 if h[-1] == "d" else -1))
        for k, h in enumerate(COLAS):
            p.rot(h, ry=6.0 * (1 if k % 2 else -1))
        return p
    return T, pose, True


def levantarse(rig):
    """Sale del lodo sacudiendo las branquias."""
    L = 2.5

    def pose(t):
        u = 1 - facil(t / L)
        p = Pose()
        _hundido(p, -3.0 - 6.0 * u)
        p.rot("cabeza", rx=6.0 + 6.0 * u + 8.0 * math.sin(math.pi * min(1.0, t / L)))
        _branquias(p, t, -20.0 * u, 6.0, 6.0)
        for h in PATAS_H:
            p.rot(h, rz=(10.0 + 25.0 * u) * (1 if h[-1] == "d" else -1))
        return p
    return L, pose, False


def comer(rig):
    """Atrapa algo: levanta la cabeza fuera del agua, abre la boca y la cierra de golpe (cada 2 s)."""
    T = 2.0

    def pose(t):
        p = Pose()
        alza = suave(t, [(0.0, 0.0), (0.6, 1.0), (0.85, 1.0), (1.2, 0.2), (T, 0.0)])
        boca = suave(t, [(0.0, 0.0), (0.5, 0.0), (0.75, 1.0), (0.9, 0.0), (T, 0.0)])
        _hundido(p, -3.0 + 2.0 * alza)
        p.rot("cabeza", rx=6.0 + 22.0 * alza)
        p.rot("mandibula", rx=-28.0 * boca)
        _branquias(p, t, 10.0 * alza, 4.0, math.pi)
        for k, h in enumerate(COLAS):
            p.rot(h, ry=5.0 * math.sin(2 * math.pi * t / T - k))
        return p
    return T, pose, True


def especial(rig):
    """Si lo molestan: azota el agua con la cola (de lado a lado, fuerte) y vuelve a hundirse."""
    L = 2.4

    def pose(t):
        p = Pose()
        golpe = suave(t, [(0.0, 0.0), (0.5, -1.0), (0.8, 1.0), (1.1, -0.6), (1.5, 0.3), (L, 0.0)])
        _hundido(p, -3.0 + 1.5 * math.sin(math.pi * min(1.0, t / L)))
        p.rot("cuerpo", ry=10.0 * golpe)
        for k, h in enumerate(COLAS):
            p.rot(h, ry=30.0 * golpe * (1 + 0.3 * k), rx=-10.0 * abs(golpe))
        p.rot("cabeza", rx=10.0, ry=-8.0 * golpe)
        _branquias(p, t, 15.0 * abs(golpe), 5.0, 5.0)
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
