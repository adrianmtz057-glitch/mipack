"""
ESCARCHA, el mamut del glaciar: el titan de la nieve (ver la hoja de titanes del usuario). Un mamut enorme de lana
blanca azulada, la giba alta con una cresta de hielo que brilla azul, colmillos larguisimos que se curvan hacia
arriba, la trompa colgando y el fleco de lana hasta las rodillas. Camina por la orilla de los glaciares; los zorros
y conejos lo siguen por el calor.
Escala: el modelo se dibuja 6 veces mas grande (1 px = 3/8 de bloque): unos 30 bloques de alto con la cresta, 24 a
la cruz y unos 40 de largo con los colmillos. El origen va en el piso, entre las patas.
Huesos: raiz / cuerpo / (cabeza / (trompa1 / trompa2 / trompa3, colmillo_d, colmillo_i, oreja_d, oreja_i), cola,
pata_dd / canilla_dd ... (delantera o trasera, derecha o izquierda)).
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER, voxel
from .khaset import tubo_camino

ESCALA = 6.0
LANA = tonos("#D8E4EE")
PIEL = tonos("#4A5868")
MARFIL = tonos("#EDE3C9")
HIELO = tonos("#9EE6FF")
BRILLAN = [HIELO["l"], HIELO["h"]]

ALTO_CRUZ = 64.0                         # px: la cruz (los hombros)
PATAS = {"dd": (1, -24.0), "di": (-1, -24.0), "td": (1, 24.0), "ti": (-1, 24.0)}
ANCHO_PATAS = 13.0                       # x de las patas


def lana(claro=0.0):
    """Lana: mechones verticales (rayas de tres tonos que bajan) y nieve encima."""
    s, b, l, h = hex_(LANA["s"]), hex_(LANA["b"]), hex_(LANA["l"]), hex_(LANA["h"])

    def p(t):
        if t.cara == "up":
            return h
        u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
        cu = math.floor(u * 1.5 + 100)
        cv = math.floor(t.y * 0.8 + 100)
        f = 0.5 + 0.25 * math.sin(cu * 1.7) * math.cos(cu * 0.6 + cv * 0.15) + claro
        f += ((BAYER[cv % 4][cu % 4] + 0.5) / 16 - 0.5) * 0.25
        if t.cara == "down":
            f -= 0.25
        return s if f < 0.3 else b if f < 0.65 else l if f < 0.88 else h
    return p


def _fleco(t):
    """El fleco de lana colgando (un plano): borde de abajo en mechones disparejos."""
    u = t.i / max(1, t.tw - 1)
    v = t.j / max(1, t.th - 1)
    corte = 0.72 + 0.2 * abs(math.sin(u * 23.0)) + 0.08 * math.sin(u * 7.0)
    if v > corte:
        return TRANSPARENTE
    return hex_(LANA["s"] if v > corte - 0.12 else LANA["b"] if (math.floor(u * 40) % 3) else LANA["l"])


def _cristal(t):
    """Hielo: azul claro con vetas que brillan y el canto blanco."""
    if t.j < 1:
        return hex_("#FFFFFF")
    cu, cv = math.floor(t.i), math.floor(t.j)
    if (cu + cv * 2) % 5 == 0:
        return hex_(HIELO["h"])
    return hex_(HIELO["l"] if BAYER[cv % 4][cu % 4] < 9 else HIELO["b"])


def construir():
    p = Personaje("escarcha")
    G = "raiz/cuerpo"
    # cuerpo: la giba alta adelante, el lomo que baja hacia la grupa
    anillos = [(-34.0, 0.0, 44.0, 10.0, 12.0), (-26.0, 0.0, 50.0, 15.0, 17.0), (-12.0, 0.0, 52.0, 17.0, 19.0),
               (4.0, 0.0, 48.0, 17.0, 17.0), (20.0, 0.0, 44.0, 16.0, 15.0), (32.0, 0.0, 41.0, 12.0, 11.0),
               (36.0, 0.0, 40.0, 6.0, 6.0)]
    cuerpo = geo.loft([(z, 0.0, 0.0, rx, ry) for z, _x, _y, rx, ry in anillos], 10, 18.0)
    vs, cs = geo.girar(cuerpo, (90.0, 0.0, 0.0))
    # cada anillo sube a su altura (y) despues de acostarlo
    alturas = {round(z, 3): y for z, _x, y, _rx, _ry in anillos}
    vs = [(x, y + _interp(z, anillos), z) for x, y, z in vs]
    p.malla(G, "tronco", (vs, cs), lana(), dens=1)
    # el fleco de lana a los costados, hasta las rodillas
    for s in (1, -1):
        x = s * 16.5
        p.m.cubo(G, f"fleco_{'d' if s > 0 else 'i'}", (x, 22.0, -30.0), (x, 40.0, 30.0), _fleco, dens=1, luz=False)
    p.m.cubo(G, "fleco_pecho", (-12.0, 24.0, -33.0), (12.0, 42.0, -33.0), _fleco, dens=1, luz=False)
    # la cresta de hielo sobre la giba
    for i, (z, h, r) in enumerate(((-24.0, 12.0, 3.5), (-17.0, 16.0, 4.0), (-9.0, 14.0, 3.5), (-1.0, 11.0, 3.0), (7.0, 8.0, 2.5),
                                   (-20.0, 8.0, 2.4), (-5.0, 9.0, 2.5))):
        y = _interp(z, anillos) + 17.0
        x = 0.0 if i < 5 else (4.0 if i == 5 else -4.0)
        cristal = geo.bipiramide((x, y, z), r, h, 2.0, lados=5, giro=12.0 * i)
        p.malla(G, f"cristal_{i}", cristal, _cristal, dens=2, luz=False)
    # cabeza: craneo alto y abovedado
    C = f"{G}/cabeza"
    cab = geo.loft([(-6.0, 0.0, 0.0, 9.0, 10.0), (2.0, 0.0, 0.0, 10.0, 11.0), (10.0, 0.0, 0.0, 8.5, 9.0), (15.0, 0.0, 0.0, 5.0, 5.5)],
                   8, 22.5)
    cab = geo.girar(cab, (0.0, 0.0, 0.0))
    cab = geo.mover(cab, (0.0, 44.0, -40.0))
    p.malla(C, "craneo", cab, lana(0.05), dens=1)
    p.caja(C, "frente", (-7.0, 40.0, -48.0), (7.0, 52.0, -43.0), lana(0.1), dens=1)
    for s in (1, -1):
        lado = "d" if s > 0 else "i"
        # ojo pequeno y oscuro
        x0, x1 = sorted((s * 8.6, s * 9.4))
        p.caja(C, f"ojo_{lado}", (x0, 47.0, -45.0), (x1, 48.5, -43.5), lambda t: hex_("#1A2228"), dens=2)
        # oreja chica peluda
        og = f"{C}/oreja_{lado}"
        x0, x1 = sorted((s * 9.0, s * 13.0))
        p.caja(og, f"oreja_{lado}", (x0, 46.0, -38.0), (x1, 54.0, -35.0), lana(-0.05), dens=1)
        p.m.pivotes[og] = (s * 9.0, 50.0, -36.5)
        # colmillo: sale hacia abajo y adelante, se abre y se curva hacia arriba y adentro
        cg = f"{C}/colmillo_{lado}"
        base = (s * 5.5, 40.0, -46.0)
        p.malla(cg, f"colmillo_{lado}", tubo_camino(_colmillo(s, base), lados=6), _marfil, dens=1)
        p.m.pivotes[cg] = base
    # trompa en tres tramos que cuelgan
    ruta = C
    y, z = 41.0, -47.0
    for k, (largo, w) in enumerate(((10.0, 4.6), (10.0, 3.6), (9.0, 2.8))):
        ruta = f"{ruta}/trompa{k + 1}"
        p.caja(ruta, f"trompa_{k + 1}", (-w, y - largo, z - w), (w, y + 0.5, z + w), _trompa, dens=1)
        p.m.pivotes[ruta] = (0.0, y, z)
        y -= largo
    # patas: muslo con lana y canilla gruesa con la pata redonda
    for nombre, (s, z) in PATAS.items():
        g = f"{G}/pata_{nombre}"
        x = s * ANCHO_PATAS
        p.caja(g, f"muslo_{nombre}", (x - 6.5, 24.0, z - 6.5), (x + 6.5, 46.0, z + 6.5), lana(), dens=1)
        c = f"{g}/canilla_{nombre}"
        p.caja(c, f"canilla_{nombre}", (x - 5.5, 4.0, z - 5.5), (x + 5.5, 25.0, z + 5.5), lana(-0.08), dens=1)
        p.caja(c, f"pie_{nombre}", (x - 6.5, 0.0, z - 6.5), (x + 6.5, 4.5, z + 6.5), _trompa, dens=1)
        p.m.cubo(c, f"fleco_pata_{nombre}", (x - 6.6, 5.0, z - 6.6), (x + 6.6, 14.0, z - 6.6), _fleco, dens=1, luz=False)
        p.m.pivotes[g] = (x, 44.0, z)
        p.m.pivotes[c] = (x, 25.0, z)
    # cola corta con su borla
    cg = f"{G}/cola"
    p.caja(cg, "cola", (-1.5, 26.0, 36.0), (1.5, 40.0, 39.0), lana(-0.1), dens=1)
    p.caja(cg, "borla", (-2.5, 22.0, 35.5), (2.5, 27.0, 39.5), lambda t: hex_(PIEL["s"]), dens=1)
    p.m.pivotes[cg] = (0.0, 40.0, 37.5)
    p.m.pivotes.update({"raiz": (0.0, 0.0, 0.0), G: (0.0, 44.0, 0.0), C: (0.0, 48.0, -34.0)})
    for k in [k for k in list(p.m.pivotes) if k in ("Head", "Body", "RightArm", "LeftArm", "RightLeg", "LeftLeg")]:
        del p.m.pivotes[k]
    return p


def _colmillo(s, base, n=16):
    """La linea del colmillo (x, y, z, radio, radio): baja hacia adelante y afuera, se curva hacia arriba y termina
    apuntando hacia adentro (la espiral del mamut); se adelgaza hasta la punta."""
    from ..animar import suave
    guia = [(0.0, (0.0, 0.0, 0.0)), (0.14, (2.0, -6.0, -6.0)), (0.3, (5.0, -9.5, -14.0)), (0.46, (8.0, -8.0, -22.0)),
            (0.62, (9.5, -2.0, -28.5)), (0.76, (7.5, 5.5, -31.5)), (0.9, (3.5, 11.0, -30.5)), (1.0, (-0.5, 13.0, -28.0))]
    x0, y0, z0 = base
    puntos = []
    for k in range(n + 1):
        u = k / n
        dx, dy, dz = suave(u, guia)
        r = 2.5 * (1.0 - 0.75 * u)
        puntos.append((x0 + s * dx, y0 + dy, z0 + dz, r, r))
    return puntos


def _interp(z, anillos):
    """La altura del lomo en z (entre los anillos)."""
    for (z0, _a, y0, _b, _c), (z1, _d, y1, _e, _f) in zip(anillos, anillos[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return anillos[0][2] if z < anillos[0][0] else anillos[-1][2]


def _marfil(t):
    """Marfil con anillos de crecimiento; la punta de hielo."""
    if t.y > 44.0 and abs(t.z) > 0:
        pass
    cv = math.floor(t.j)
    return hex_(MARFIL["h"] if cv % 6 == 0 else MARFIL["l"] if cv % 3 == 0 else MARFIL["b"])


def _trompa(t):
    """Piel gris pizarra con arrugas horizontales."""
    cv = math.floor(t.y * 1.5 + 100)
    return hex_(PIEL["s"] if cv % 4 == 0 else PIEL["b"] if BAYER[cv % 4][math.floor(t.i) % 4] < 10 else PIEL["l"])


# ---------------------------------------------------------------- animaciones

from .. import animar                                    # noqa: E402
from ..animar import facil, suave                        # noqa: E402
from .crackatos_anim import Pose                         # noqa: E402

TROMPA = ("trompa1", "trompa2", "trompa3")


def _trompa_pose(p, t, T, amp=6.0, curva=0.0):
    w = 2 * math.pi * t / T
    for k, h in enumerate(TROMPA):
        p.rot(h, rx=curva * (k + 1) + amp * math.sin(w - k * 0.7), rz=amp * 0.4 * math.sin(w * 0.5 * 2 - k))


def mover(rig):
    """Camina: patas cruzadas (delantera derecha con trasera izquierda), el cuerpo sube y baja y se mece, la cabeza
    cabecea y la trompa se columpia."""
    T = 3.2

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        p.pos("raiz", y=0.8 * math.cos(2 * w))
        p.rot("cuerpo", rz=1.5 * math.sin(w), rx=0.8 * math.sin(2 * w))
        p.rot("cabeza", rx=-3.0 * math.sin(2 * w + 0.5), ry=3.0 * math.sin(w))
        for nombre, fase in (("dd", 0.0), ("ti", 0.0), ("di", math.pi), ("td", math.pi)):
            a = math.sin(w + fase)
            p.rot(f"pata_{nombre}", rx=18.0 * a)
            p.rot(f"canilla_{nombre}", rx=-22.0 * max(0.0, math.sin(w + fase + 1.2)))
        _trompa_pose(p, t, T, 8.0, 3.0)
        p.rot("cola", rz=10.0 * math.sin(w))
        for s, h in ((1, "oreja_d"), (-1, "oreja_i")):
            p.rot(h, ry=s * 5.0 * math.sin(2 * w))
        return p
    return T, pose, True


def quieto(rig):
    """Parado: respira, mueve las orejas, enrolla la trompa despacio y menea la cola."""
    T = 6.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        p.pos("raiz", y=0.4 * math.sin(w))
        p.rot("cabeza", rx=-2.0 + 2.0 * math.sin(w), ry=4.0 * math.sin(w * 0.5 * 2))
        _trompa_pose(p, t, T, 6.0, 4.0 + 3.0 * math.sin(w))
        p.rot("cola", rz=8.0 * math.sin(2 * w))
        for s, h in ((1, "oreja_d"), (-1, "oreja_i")):
            p.rot(h, ry=s * (6.0 + 8.0 * max(0.0, math.sin(2 * w + s))))
        return p
    return T, pose, True


def _echado(p, u):
    """Que tan echado esta (0 parado, 1 en el piso): dobla las patas y baja el cuerpo."""
    p.pos("raiz", y=-20.0 * u)
    for nombre in ("dd", "di"):
        p.rot(f"pata_{nombre}", rx=-55.0 * u)
        p.rot(f"canilla_{nombre}", rx=100.0 * u)
    for nombre in ("td", "ti"):
        p.rot(f"pata_{nombre}", rx=50.0 * u)
        p.rot(f"canilla_{nombre}", rx=-95.0 * u)
    p.rot("cabeza", rx=-8.0 * u)


def asentarse(rig):
    """Se echa en la nieve: dobla las patas de adelante, luego las de atras, y baja la cabeza."""
    L = 3.5

    def pose(t):
        p = Pose()
        _echado(p, facil(t / L))
        _trompa_pose(p, t, 3.5, 3.0, 8.0 * facil(t / L))
        return p
    return L, pose, "hold_on_last_frame"


def descansar(rig):
    """Echado: respira hondo (sube y baja) con la trompa en el piso; las orejas se mueven de vez en cuando."""
    T = 8.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        _echado(p, 1.0)
        p.pos("raiz", y=0.6 * math.sin(w))
        _trompa_pose(p, t, T, 2.0, 10.0)
        for s, h in ((1, "oreja_d"), (-1, "oreja_i")):
            p.rot(h, ry=s * 10.0 * max(0.0, math.sin(w * 3)) ** 8)
        return p
    return T, pose, True


def levantarse(rig):
    """Se levanta: primero las de atras, luego las de adelante, y sacude la cabeza (cae la nieve)."""
    L = 3.0

    def pose(t):
        p = Pose()
        u = 1 - facil(t / L)
        _echado(p, u)
        p.rot("cabeza", ry=10.0 * math.sin(t * 9.0) * max(0.0, 1 - abs(t - 2.4) / 0.5))
        return p
    return L, pose, False


def comer(rig):
    """Escarba la nieve con los colmillos y la trompa y se lleva el pasto a la boca."""
    T = 3.0

    def pose(t):
        p = Pose()
        baja = suave(t, [(0.0, 0.2), (0.8, 1.0), (1.6, 1.0), (2.2, 0.3), (T, 0.2)])
        p.rot("cabeza", rx=-22.0 * baja, ry=6.0 * math.sin(2 * math.pi * t / T * 2) * baja)
        enrolla = suave(t, [(0.0, 0.0), (1.6, 0.0), (2.2, 1.0), (2.6, 1.0), (T, 0.0)])
        for k, h in enumerate(TROMPA):
            p.rot(h, rx=10.0 * baja * (1 if k == 0 else 0.5) - 40.0 * enrolla * (k + 1) / 2)
        for nombre in ("dd", "di"):
            p.rot(f"canilla_{nombre}", rx=6.0 * baja)
        return p
    return T, pose, True


def beber(rig):
    """Mete la trompa al agua y se la lleva a la boca."""
    T = 4.0

    def pose(t):
        p = Pose()
        baja = suave(t, [(0.0, 0.0), (1.0, 1.0), (2.0, 1.0), (2.8, 0.0), (T, 0.0)])
        sube = suave(t, [(0.0, 0.0), (2.2, 0.0), (2.9, 1.0), (3.5, 1.0), (T, 0.0)])
        p.rot("cabeza", rx=-12.0 * baja + 6.0 * sube)
        for k, h in enumerate(TROMPA):
            p.rot(h, rx=8.0 * baja - 45.0 * sube * (k + 1) / 2)
        return p
    return T, pose, True


def especial(rig):
    """Barrita: levanta la cabeza y la trompa hacia el cielo, abre las orejas y se para un poco de manos."""
    L = 3.0

    def pose(t):
        p = Pose()
        alza = suave(t, [(0.0, 0.0), (0.7, 1.0), (2.2, 1.0), (L, 0.0)])
        tiembla = math.sin(t * 30.0) * alza
        p.rot("cuerpo", rx=6.0 * alza)
        p.rot("cabeza", rx=24.0 * alza + 0.8 * tiembla)
        for k, h in enumerate(TROMPA):
            p.rot(h, rx=-45.0 * alza * (1 + 0.4 * k) / 1.4 + tiembla)
        for s, h in ((1, "oreja_d"), (-1, "oreja_i")):
            p.rot(h, ry=s * 30.0 * alza)
        for nombre in ("dd", "di"):
            p.rot(f"pata_{nombre}", rx=-12.0 * alza)
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
