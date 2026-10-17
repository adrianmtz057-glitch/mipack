"""
El motor de animaciones de los bichos: cada animacion es de un GRUPO de bichos que se mueven igual (los grupos se
arman de nuevo para cada animacion: caminar, correr, atacar...), definida como pose(t) sobre los huesos de la
plantilla (cuerpos.py) y horneada a un cuadro por tick con animar.hornear (lo que se ve en el GIF es lo que
reproduce GeckoLib).
Convenciones del kit: el frente es -Z, su derecha +X. Giro en X positivo levanta lo de adelante; en Z positivo
ladea hacia la izquierda.
Uso: python -m taller.bichos.mover <animacion> [grupo|bicho ...]  ->  salida/bichos/anim/<animacion>_<grupo>.gif
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from .. import animar, geckolib, vista
from .catalogo import CATALOGO
from .hojas import FONDO, _fuente, _tex, armar

SALIDA = os.path.join(os.path.dirname(__file__), "..", "..", "salida", "bichos", "anim")
TAU = 2 * math.pi


class Pose(dict):
    def __init__(self, huesos):
        super().__init__()
        self.huesos = huesos

    def rot(self, h, rx=0.0, ry=0.0, rz=0.0):
        if h not in self.huesos:
            return
        (ax, ay, az), p = self.get(h, ((0, 0, 0), (0, 0, 0)))
        self[h] = ((ax + rx, ay + ry, az + rz), p)

    def pos(self, h, x=0.0, y=0.0, z=0.0):
        if h not in self.huesos:
            return
        r, (px, py, pz) = self.get(h, ((0, 0, 0), (0, 0, 0)))
        self[h] = (r, (px + x, py + y, pz + z))


class Listo:
    """Un bicho armado y listo para animar: su rig de GeckoLib, su textura y sus medidas."""

    def __init__(self, ident):
        self.b = CATALOGO[ident]
        self.a, self.lienzo, self.uvs, _ = armar(self.b)
        self.geo = geckolib.exportar_geo(self.a.m, self.uvs, self.lienzo, ident)
        self.rig = animar.Rig(self.geo)
        self.huesos = set(self.rig.padre)

    def pose(self):
        return Pose(self.huesos)

    def largo_pata(self, h):
        return self.rig.pivote[h][1]


def _pata(u, apoyo, amplitud, alto):
    """El giro (grados en X) y lo que se alza (px) una pata rigida en el ciclo u (0..1): apoyada va de adelante
    hacia atras (de +amplitud a -amplitud en X: giro positivo lleva el pie adelante); en el aire vuelve adelante
    alzandose."""
    u %= 1.0
    if u < apoyo:
        f = u / apoyo
        return amplitud - 2 * amplitud * f, 0.0
    f = (u - apoyo) / (1 - apoyo)
    return -amplitud + 2 * amplitud * animar.facil(f), alto * math.sin(math.pi * f)


# ====================================================================== caminar

def caminar_pesado(L):
    """Pesados (hipopotamo, cria de Iskarum): paso lento en secuencia lateral (trasera izq, delantera izq, trasera
    der, delantera der) con tres patas siempre en el piso; el cuerpo se hunde con cada pisada y se mece hacia la
    pata que carga, la cabeza cabecea baja y la trompa y la cola se columpian con retraso."""
    largo = 1.8
    fases = {"pata_ti": 0.0, "pata_di": 0.25, "pata_td": 0.5, "pata_dd": 0.75}

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, f in fases.items():
            giro, alza = _pata(u + f, 0.75, 13.0, 0.9)
            p.rot(h, giro)
            p.pos(h, y=alza)
        p.pos("cuerpo", y=-0.35 - 0.35 * math.cos(2 * TAU * u))      # se hunde con cada pisada delantera
        p.rot("cuerpo", rz=2.6 * math.sin(TAU * u), ry=1.2 * math.sin(TAU * u + 0.5))
        p.rot("cabeza", rx=-2.5 * math.cos(2 * TAU * u - 0.6), ry=-2.0 * math.sin(TAU * u), rz=-1.5 * math.sin(TAU * u))
        p.rot("trompa", rx=6.0 * math.sin(TAU * u - 1.0), rz=7.0 * math.sin(TAU * u - 1.6))
        p.rot("cola", rx=4.0 * math.cos(2 * TAU * u), rz=10.0 * math.sin(TAU * u - 0.8))
        return p
    return largo, pose_en


def _ciclo(L, h, minimo=0.5, maximo=1.3, k=0.07):
    """Lo que tarda un paso completo segun lo largo de la pata h (a cuadros enteros de 0.05 s)."""
    largo = max(minimo, min(maximo, 0.35 + k * L.largo_pata(h)))
    return round(largo / 0.05) * 0.05


def _lateral(p, h, s, u, apoyo, amplitud, alza):
    """Una pata abierta a un lado (insectos, reptiles): apoyada barre de adelante hacia atras girando en Y y en el
    aire se alza girando en Z. s: +1 la derecha, -1 la izquierda (en Y positivo la punta derecha va adelante y la
    izquierda atras; en Z positivo la derecha sube y la izquierda baja)."""
    giro, sube = _pata(u, apoyo, amplitud, alza)
    p.rot(h, ry=s * giro, rz=s * sube)


def _onda(p, huesos, u, amplitud, desfase, eje="ry", crece=0.0):
    """Una onda que corre hacia atras por una cadena de huesos (colas, serpientes)."""
    for k, h in enumerate(huesos):
        a = amplitud * (1 + crece * k) * math.sin(TAU * u - desfase * (k + 1))
        p.rot(h, **{eje: a})


def caminar_mc(L):
    """Como los cuadrupedos de Minecraft (vaca, cabra, gato, zorro, lobo): las patas en pares diagonales se mecen
    sin doblar; la cola se columpia y la cabeza apenas cabecea."""
    largo = _ciclo(L, "pata_dd")

    def pose_en(t):
        u = t / largo
        p = L.pose()
        a = 24.0 * math.cos(TAU * u)
        for h, s in (("pata_dd", 1), ("pata_ti", 1), ("pata_di", -1), ("pata_td", -1)):
            p.rot(h, s * a)
        p.rot("cabeza", rx=1.5 * math.cos(2 * TAU * u))
        p.rot("cuello", rx=1.5 * math.cos(2 * TAU * u))
        p.rot("cola", ry=8.0 * math.sin(TAU * u), rx=2.0 * math.cos(2 * TAU * u))
        return p
    return largo, pose_en


def caminar_camello(L):
    """Como el camello de Minecraft: ambladura (las dos patas del mismo lado a la vez), el cuerpo se mece de lado a
    lado y el cuello cabecea con cada paso."""
    largo = 1.3

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for lado, f in (("d", 0.0), ("i", 0.5)):
            for fila in "dt":
                giro, alza = _pata(u + f, 0.6, 16.0, 1.2)
                p.rot(f"pata_{fila}{lado}", giro)
                p.pos(f"pata_{fila}{lado}", y=alza)
        p.rot("cuerpo", rz=3.0 * math.sin(TAU * u))
        p.pos("cuerpo", y=-0.3 * math.cos(2 * TAU * u))
        p.rot("cuello", rx=4.0 * math.sin(2 * TAU * u - 0.6))
        p.rot("cabeza", rx=-3.5 * math.sin(2 * TAU * u - 0.6))
        p.rot("cola", rz=8.0 * math.sin(TAU * u - 0.8))
        return p
    return largo, pose_en


def caminar_conejo(L):
    """Como el conejo de Minecraft: avanza a brincos (se impulsa con las de atras, estira las de adelante en el aire y
    aterriza) y luego se asienta."""
    largo = 0.7

    def pose_en(t):
        u = (t / largo) % 1.0
        p = L.pose()
        if u < 0.45:
            f = u / 0.45
            alto = 3.0 * math.sin(math.pi * f)
            for h in L.huesos:
                if h.startswith("pata"):
                    p.pos(h, y=alto)
            p.pos("cuerpo", y=alto)
            p.rot("cuerpo", rx=-14.0 * math.sin(math.pi * f) + 8.0 * math.sin(TAU * f) * 0.5)
            p.rot("pata_td", -35.0 * math.sin(math.pi * min(1, f * 1.4)))
            p.rot("pata_ti", -35.0 * math.sin(math.pi * min(1, f * 1.4)))
            p.rot("pata_dd", 30.0 * math.sin(math.pi * f))
            p.rot("pata_di", 30.0 * math.sin(math.pi * f))
            p.rot("cola", rx=12.0 * math.sin(math.pi * f))
        else:
            f = (u - 0.45) / 0.55
            p.pos("cuerpo", y=-0.6 * math.sin(math.pi * f))
            p.rot("cabeza", rx=3.0 * math.sin(math.pi * f))
        return p
    return largo, pose_en


def caminar_ave(L):
    """Como el pollo de Minecraft: las patas alternan, el cuerpo se balancea un poco (mas los grandes) y la cabeza
    va y viene."""
    largo = _ciclo(L, "pata_d", 0.5, 1.0, 0.09)
    grande = L.largo_pata("pata_d") >= 3.5

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, f in (("pata_d", 0.0), ("pata_i", 0.5)):
            giro, alza = _pata(u + f, 0.55, 20.0 if grande else 24.0, 0.8)
            p.rot(h, giro)
            p.pos(h, y=alza)
        p.rot("cuerpo", rz=(4.0 if grande else 2.0) * math.sin(TAU * u))
        p.pos("cuerpo", y=-0.25 * math.cos(2 * TAU * u))
        cab = "cuello" if "cuello" in L.huesos else "cabeza"
        p.pos(cab, z=-0.6 * math.sin(2 * TAU * u))
        p.rot("ala_d", rz=2.0 * math.sin(2 * TAU * u))
        p.rot("ala_i", rz=-2.0 * math.sin(2 * TAU * u))
        p.rot("cola", ry=4.0 * math.sin(TAU * u))
        return p
    return largo, pose_en


def caminar_murcielago(L):
    """Como el murcielago de Minecraft (siempre vuela): aletea, el cuerpo sube y baja y las patas cuelgan."""
    largo = 0.4

    def pose_en(t):
        u = t / largo
        p = L.pose()
        a = 38.0 * math.sin(TAU * u)
        p.rot("ala_d", rz=a, ry=-6.0 * math.cos(TAU * u))
        p.rot("ala_i", rz=-a, ry=6.0 * math.cos(TAU * u))
        p.pos("cuerpo", y=1.0 - 0.8 * math.sin(TAU * u))
        for h in ("pata_d", "pata_i"):
            p.pos(h, y=1.0 - 0.8 * math.sin(TAU * u))
            p.rot(h, 20.0)
        p.rot("cabeza", rx=-4.0 * math.sin(TAU * u - 0.5))
        return p
    return largo, pose_en


def caminar_delfin(L):
    """Como el delfin de Minecraft (nada en la arena): el cuerpo ondula de arriba a abajo, la cola bate con
    retraso y las aletas reman."""
    largo = 1.2

    def pose_en(t):
        u = t / largo
        p = L.pose()
        p.rot("cuerpo", rx=3.0 * math.sin(TAU * u))
        p.pos("cuerpo", y=1.0 + 0.6 * math.sin(TAU * u + 1.2))
        p.rot("cola", rx=-16.0 * math.sin(TAU * u - 1.2))
        p.rot("cabeza", rx=-2.5 * math.sin(TAU * u))
        p.rot("aleta_d", rz=10.0 * math.sin(TAU * u - 0.6), ry=6.0 * math.cos(TAU * u))
        p.rot("aleta_i", rz=-10.0 * math.sin(TAU * u - 0.6), ry=-6.0 * math.cos(TAU * u))
        return p
    return largo, pose_en


def caminar_primate(L):
    """Babuino: en cuatro patas apoyado en los nudillos, en secuencia diagonal (trasera izq, delantera der, trasera
    der, delantera izq); los brazos dan pasos largos, los hombros suben y bajan, la cadera se mece y la cabeza se
    queda firme mirando al frente."""
    largo = 1.1
    fases = {"pata_ti": 0.0, "pata_dd": 0.25, "pata_td": 0.5, "pata_di": 0.75}

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, f in fases.items():
            delantera = h[5] == "d"
            giro, alza = _pata(u + f, 0.62, 22.0 if delantera else 17.0, 1.4 if delantera else 0.9)
            p.rot(h, giro, rz=(2.0 if h.endswith("d") else -2.0) * alza)
            p.pos(h, y=alza)
        p.rot("cuerpo", rz=3.5 * math.sin(TAU * u + 1.0), ry=4.0 * math.sin(TAU * u + 1.0))
        p.pos("cuerpo", y=-0.4 * math.cos(2 * TAU * u))
        p.rot("cabeza", ry=-4.0 * math.sin(TAU * u + 1.0), rz=-3.0 * math.sin(TAU * u + 1.0), rx=1.5 * math.cos(2 * TAU * u))
        p.rot("cola", rz=7.0 * math.sin(TAU * u - 0.4), rx=3.0 * math.cos(2 * TAU * u))
        return p
    return largo, pose_en


def caminar_roedor(L):
    """Marmota: pasitos cortos y rapidos al trote, la panza se bambolea de lado a lado y la cabeza husmea."""
    largo = 0.5

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, f in (("pata_dd", 0.0), ("pata_ti", 0.0), ("pata_di", 0.5), ("pata_td", 0.5)):
            giro, alza = _pata(u + f, 0.55, 22.0, 0.7)
            p.rot(h, giro)
            p.pos(h, y=alza)
        p.rot("cuerpo", rz=5.0 * math.sin(TAU * u), rx=1.5 * math.cos(2 * TAU * u))
        p.pos("cuerpo", y=0.35 * abs(math.sin(TAU * u)))
        p.rot("cabeza", rz=-4.0 * math.sin(TAU * u), rx=2.0 * math.sin(2 * TAU * u))
        p.rot("cola", rz=10.0 * math.sin(TAU * u - 0.8))
        return p
    return largo, pose_en


REPTILES = {"cocodrilo_luz": 1.6, "lagarto_roca": 0.7, "salamandra_ceniza": 1.0, "lagartija_blanca": 0.6,
            "cria_moruvahn": 1.2}


def caminar_reptil(L):
    """Reptiles (y el ajolote): pegados al piso con las patas abiertas, en pares diagonales; la espalda dobla en S
    hacia la pata que avanza (la cabeza la compensa para seguir mirando al frente) y la onda sigue por la cola."""
    largo = REPTILES.get(L.b.id, 1.0)

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, s, f in (("pata_dd", 1, 0.0), ("pata_ti", -1, 0.0), ("pata_di", -1, 0.5), ("pata_td", 1, 0.5)):
            _lateral(p, h, s, u + f, 0.6, 26.0, 18.0)
        dobla = 9.0 * math.sin(TAU * u)
        p.rot("cuerpo", ry=dobla)
        p.rot("cabeza", ry=-dobla * 1.2)
        _onda(p, ("cola1", "cola2", "cola3"), u, 10.0, 1.1, crece=0.25)
        p.rot("cola1", rx=1.5 * math.cos(2 * TAU * u))
        return p
    return largo, pose_en


def caminar_serpiente(L):
    """Serpientes: ondulacion lateral, una onda que corre de la cabeza a la cola; la cabeza se queda firme."""
    tramos = sorted((h for h in L.huesos if h.startswith("s") and h[1:].isdigit()), key=lambda h: int(h[1:]))
    largo = 1.6 if L.b.id == "cria_varkhum" else 1.2

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _onda(p, tramos[1:], u, 16.0, 0.75)
        p.rot(tramos[0], ry=-6.0 * math.sin(TAU * u - 0.75))
        p.rot(tramos[0], rx=1.0 * math.sin(2 * TAU * u))
        return p
    return largo, pose_en


def _tripode(p, u, apoyo, amplitud, alza, atras=False):
    """Seis patas en tripode alterno: (1d, 2i, 3d) y (1i, 2d, 3i). atras: caminando de reversa."""
    for k in (1, 2, 3):
        for lado, s in (("d", 1), ("i", -1)):
            f = 0.0 if (k % 2 == 1) == (lado == "d") else 0.5
            v = -u if atras else u
            _lateral(p, f"pata_{k}{lado}", s, v + f, apoyo, -amplitud if atras else amplitud, alza)


def caminar_insecto(L):
    """Insectos: tripode alterno. El escarabajo sagrado camina de reversa empujando su bola con las patas de atras
    (se voltea: lo que va al frente es la bola) con la cabeza agachada y la bola rodando; la ramita va lenta y se
    mece de lado a lado como rama al viento."""
    ident = L.b.id
    if ident == "escarabajo_sagrado":
        largo = 2.4

        def pose_en(t):
            u = t / 0.8
            p = L.pose()
            _tripode(p, u, 0.55, 16.0, 14.0, atras=True)
            p.rot("raiz", ry=180.0)
            p.rot("cuerpo", rx=-10.0 + 1.5 * math.sin(2 * TAU * u))
            p.pos("cuerpo", y=0.6)
            p.rot("cabeza", rx=-8.0)
            p.rot("pata_3d", rx=20.0)
            p.rot("pata_3i", rx=20.0)
            giro = 360.0 * t / largo
            p.rot("bola", rx=giro)
            r = L.rig.pivote["bola"][1]                    # medio lado: al rodar, la esquina no se entierra
            p.pos("bola", y=r * (math.sqrt(2) * math.cos(math.radians(giro % 90 - 45)) - 1))
            return p
        return largo, pose_en
    if ident == "ramita":
        largo = 1.6

        def pose_en(t):
            u = t / largo
            p = L.pose()
            _tripode(p, u, 0.65, 12.0, 10.0)
            p.rot("cuerpo", rz=3.0 * math.sin(2 * TAU * u), ry=2.0 * math.sin(TAU * u))
            p.pos("cuerpo", x=0.4 * math.sin(2 * TAU * u))
            p.rot("cabeza", rz=-2.0 * math.sin(2 * TAU * u))
            return p
        return largo, pose_en
    largo = 0.6

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _tripode(p, u, 0.55, 18.0, 16.0)
        p.rot("cuerpo", rz=1.5 * math.sin(TAU * u))
        p.pos("cuerpo", y=0.15 * math.cos(2 * TAU * u))
        p.rot("cabeza", ry=2.0 * math.sin(TAU * u))
        return p
    return largo, pose_en


def caminar_aracnido(L):
    """Aracnidos: las patas en ola (de adelante hacia atras en cada lado, un lado a medio ciclo del otro), el cuerpo
    bajo. El escorpion lleva la cola alzada meciendose y las pinzas al frente; la garrapata corretea rapido."""
    escorpion = L.b.id == "escorpion_luz"
    largo = 0.9 if escorpion else 0.45

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for k in (1, 2, 3):
            for lado, s, f0 in (("d", 1, 0.0), ("i", -1, 0.5)):
                _lateral(p, f"pata_{k}{lado}", s, u + f0 + (k - 1) / 3.0, 0.62, 18.0, 15.0)
        p.rot("cuerpo", rz=1.5 * math.sin(TAU * u), rx=0.8 * math.sin(2 * TAU * u))
        if escorpion:
            _onda(p, ("cola1", "cola2", "cola3", "cola4"), u, 3.5, 0.6)
            p.rot("cola1", rx=2.5 * math.sin(2 * TAU * u))
            p.rot("cola4", rx=-4.0 * math.sin(2 * TAU * u - 1.0))
            p.rot("pinza_d", rx=3.0 * math.sin(TAU * u), ry=4.0 * math.sin(TAU * u))
            p.rot("pinza_i", rx=3.0 * math.sin(TAU * u + math.pi), ry=-4.0 * math.sin(TAU * u + math.pi))
        else:
            p.pos("cuerpo", y=0.15 * abs(math.sin(2 * TAU * u)))
        return p
    return largo, pose_en


def caminar_zancuda(L):
    """Zancudas (ibis, flamenco): pasos largos y lentos alzando mucho la pata; el cuello empuja la cabeza adelante con
    cada paso y la regresa."""
    largo = 1.4

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, f in (("pata_d", 0.0), ("pata_i", 0.5)):
            giro, alza = _pata(u + f, 0.6, 18.0, 2.2)
            p.rot(h, giro)
            p.pos(h, y=alza)
        p.rot("cuerpo", rz=2.0 * math.sin(TAU * u), rx=1.0 * math.cos(2 * TAU * u))
        p.pos("cuerpo", y=-0.3 * math.cos(2 * TAU * u))
        empuje = math.sin(2 * TAU * u)
        p.rot("cuello", rx=-6.0 * empuje)
        p.rot("cabeza", rx=6.0 * empuje)
        p.rot("cola", rx=2.0 * empuje)
        return p
    return largo, pose_en


def caminar_cangrejo(L):
    """Cangrejo: camina de lado (se voltea: lo que va al frente es su costado derecho); las patas se alzan y jalan en
    tripode alterno, el cuerpo se ladea y las pinzas suben y bajan."""
    largo = 0.6

    def pose_en(t):
        u = t / largo
        p = L.pose()
        p.rot("raiz", ry=90.0)
        for k in (1, 2, 3):
            for lado, s in (("d", 1), ("i", -1)):
                f = 0.0 if (k % 2 == 1) == (lado == "d") else 0.5
                giro, alza = _pata(u + f, 0.55, 10.0, 16.0)
                p.rot(f"pata_{k}{lado}", rz=s * (alza + giro * 0.6), ry=s * 4.0 * math.sin(TAU * (u + f)))
        p.rot("cuerpo", rz=2.5 * math.sin(2 * TAU * u))
        p.pos("cuerpo", y=0.2 * math.cos(2 * TAU * u))
        p.rot("pinza_d", rx=8.0 * math.sin(TAU * u))
        p.rot("pinza_i", rx=8.0 * math.sin(TAU * u + math.pi))
        return p
    return largo, pose_en


CAMINAR = {
    # los que ya tienen forma de Minecraft: el caminado de ese animal
    "como_cuadrupedo_mc": (caminar_mc, ["toro_arena", "bufalo_terracota", "cabra_escarcha", "cervatillo_musgo",
                                        "gato_thza", "fenec", "chacal_ceniza", "lobo_fuego"]),
    "como_camello": (caminar_camello, ["dromedario"]),
    "como_conejo": (caminar_conejo, ["liebre_dorada"]),
    "como_pollo": (caminar_ave, ["pato_estanque", "buitre", "halcon_cobre", "aguila_gris", "cuervo_negro"]),
    "como_murcielago": (caminar_murcielago, ["murcielago_mura"]),
    "como_delfin": (caminar_delfin, ["ballenato_duna"]),
    # los de forma nueva
    "pesados": (caminar_pesado, ["hipopotamo", "cria_iskarum"]),
    "primate": (caminar_primate, ["babuino"]),
    "roedor": (caminar_roedor, ["marmota"]),
    "reptiles": (caminar_reptil, list(REPTILES)),
    "serpientes": (caminar_serpiente, ["serpiente_rio_seco", "cria_varkhum"]),
    "insectos": (caminar_insecto, ["escarabajo_sagrado", "escarabajo_brasa", "ramita"]),
    "aracnidos": (caminar_aracnido, ["escorpion_luz", "garrapata_sal"]),
    "zancudas": (caminar_zancuda, ["ibis", "flamenco"]),
    "cangrejo": (caminar_cangrejo, ["cangrejo"]),
}
ANIMACIONES = {"caminar": CAMINAR}
DESDE_ARRIBA = ("reptiles", "serpientes", "cangrejo", "insectos", "aracnidos")   # la segunda vista, desde arriba


# ====================================================================== revisar

def gif(listos, nombre, poses, ruta, alto=None, cada=1, vistas=((35, 12), (90, 4))):
    """Un GIF de todos los bichos del grupo lado a lado (de 3/4 y de lado), en caminadora."""
    alto = alto or (300 if len(listos) <= 2 else 230)
    columnas = []
    for L, (largo, pose_en) in zip(listos, poses):
        datos, cuadros = animar.hornear(L.rig, nombre, largo, pose_en)
        rev = animar.revisar(L.rig, cuadros, True)
        print(f"  {L.b.id}: {len(cuadros)} cuadros, lo mas bajo {rev['mas_bajo']} ({rev['hueso']}), "
              f"brinco del bucle {rev['brinco_del_bucle']}")
        tex = _tex(L.lienzo)
        quieto = geckolib.caras_para_vista(L.rig.quads({}))
        todos = np.concatenate([P for P, _ in quieto])
        lo, hi = todos.min(axis=0), todos.max(axis=0)
        centro = (lo + hi) / 2
        radio = float(np.max(hi - lo)) * 0.58
        cuadros_img = []
        for _t, pose in cuadros[::cada]:
            caras = geckolib.caras_para_vista(L.rig.quads(pose))
            fila = []
            for yaw, pitch in vistas:
                img = vista._render(caras, tex, yaw, pitch, alto * 0.9 / (2 * radio), alto, alto, centro, FONDO, True)
                fila.append(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)))
            im = Image.new("RGB", (alto * 2, alto + 22), (26, 24, 22))
            im.paste(fila[0], (0, 22))
            im.paste(fila[1], (alto, 22))
            ImageDraw.Draw(im).text((8, 3), f"{L.b.nombre}  ·  {nombre}", fill=(245, 235, 210), font=_fuente(15))
            cuadros_img.append(im)
        columnas.append(cuadros_img)
    n = max(len(c) for c in columnas)
    w, h = columnas[0][0].size
    por_fila = 1 if len(columnas) == 1 else 2
    filas = (len(columnas) + por_fila - 1) // por_fila
    salida = []
    for k in range(n):
        lienzo = Image.new("RGB", (w * por_fila, h * filas), (18, 17, 16))
        for i, c in enumerate(columnas):
            lienzo.paste(c[k % len(c)], ((i % por_fila) * w, (i // por_fila) * h))
        salida.append(lienzo)
    salida[0].save(ruta, save_all=True, append_images=salida[1:], duration=int(1000 * animar.PASO * cada), loop=0)
    return ruta


def main(args):
    nombre = args[0]
    grupos = ANIMACIONES[nombre]
    pedidos = args[1:] or list(grupos)
    os.makedirs(SALIDA, exist_ok=True)
    for g in pedidos:
        if g in grupos:
            f, ids = grupos[g]
        else:
            f, ids = next((f, [g]) for f, ids in grupos.values() if g in ids)
        listos = [Listo(i) for i in ids]
        print(nombre, g)
        vistas = ((35, 12), (15, 70)) if g in DESDE_ARRIBA else ((35, 12), (90, 4))
        print("  ->", gif(listos, nombre, [f(L) for L in listos], os.path.join(SALIDA, f"{nombre}_{g}.gif"), vistas=vistas))


if __name__ == "__main__":
    main(sys.argv[1:])
