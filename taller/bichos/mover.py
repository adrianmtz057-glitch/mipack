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


def _onda(p, huesos, u, amplitud, desfase, eje="ry", crece=0.0, rampa=0):
    """Una onda que corre hacia atras por una cadena de huesos (colas, serpientes); rampa: en cuantos tramos llega a
    toda su amplitud (el cuello de la serpiente dobla menos)."""
    for k, h in enumerate(huesos):
        a = amplitud * (1 + crece * k) * math.sin(TAU * u - desfase * (k + 1))
        if rampa:
            a *= min(1.0, (k + 1) / rampa)
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
        a = 32.0 * math.sin(TAU * u)
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
        _onda(p, tramos[1:], u, 16.0, 0.75, rampa=3)
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
# ====================================================================== correr

def _montar_patas(L, p):
    """Las patas cuelgan de la raiz: si el cuerpo sube, se mece o se ladea, la cadera de cada pata lo sigue (si el
    cuerpo baja no hace falta: se encima sobre la pata, que queda escondida adentro)."""
    T = L.rig.transformaciones(p)
    T0 = L.rig.transformaciones({})
    local = animar._inversa(T["raiz"]).despues(T["cuerpo"])          # lo que se movio el cuerpo sobre la raiz
    local0 = animar._inversa(T0["raiz"]).despues(T0["cuerpo"])
    for h in L.huesos:
        if h.startswith("pata") and L.rig.padre[h] == "raiz":
            piv = L.rig.pivote[h]
            a, b = local(piv), local0(piv)
            p.pos(h, x=a[0] - b[0], y=max(0.0, a[1] - b[1]), z=a[2] - b[2])
    return p


def _galope(L, p, fases, u, apoyo, amplitud, alza, atras=1.0):
    """Las cuatro patas rigidas con su fase cada una (galope, brinco, estampida); atras: cuanto de la zancada dan
    las de atras."""
    for h, f in fases.items():
        giro, sube = _pata(u + f, apoyo, amplitud * (atras if h[5] == "t" else 1.0), alza)
        p.rot(h, giro)
        p.pos(h, y=sube)


def correr_lobo(L):
    """Galope de lobo (lobo de fuego, chacal), no de perro: galope transversal largo y parejo (trasera izq, trasera
    der, delantera izq, delantera der) con un tramo en el aire; el lomo se mece poco, la cabeza va baja y fija al
    frente (la cabeza compensa el meneo del cuerpo), las orejas atras y la cola horizontal."""
    largo = 0.55
    fases = {"pata_ti": 0.0, "pata_td": 0.1, "pata_di": 0.5, "pata_dd": 0.6}

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _galope(L, p, fases, u, 0.42, 42.0, 0.8, atras=0.7)
        meneo = 5.0 * math.sin(TAU * u + 0.6)
        p.rot("cuerpo", rx=meneo)
        p.pos("cuerpo", y=0.6 + 0.6 * math.sin(2 * TAU * u))
        p.rot("cabeza", rx=-meneo - 9.0)                 # baja y firme
        p.rot("mandibula", rx=-4.0 - 3.0 * math.sin(2 * TAU * u))
        p.rot("cola", rx=-14.0 + 3.0 * math.sin(TAU * u), ry=3.0 * math.sin(TAU * u))
        return _montar_patas(L, p)
    return largo, pose_en


def correr_zorro(L):
    """Fenec: galope rasante y rapido con la cola de timon, estirada atras."""
    largo = 0.4
    fases = {"pata_ti": 0.0, "pata_td": 0.08, "pata_di": 0.5, "pata_dd": 0.58}

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _galope(L, p, fases, u, 0.4, 40.0, 0.6, atras=0.7)
        meneo = 6.0 * math.sin(TAU * u + 0.6)
        p.rot("cuerpo", rx=meneo)
        p.pos("cuerpo", y=0.4 + 0.5 * math.sin(2 * TAU * u))
        p.rot("cabeza", rx=-meneo - 5.0)
        p.rot("cola", rx=-22.0 + 2.0 * math.sin(TAU * u), ry=6.0 * math.sin(TAU * u))
        return _montar_patas(L, p)
    return largo, pose_en


def correr_felino(L):
    """Gato: galope rotatorio con el lomo muy flexible (se encoge y se estira), pegado al piso; la cola balancea."""
    largo = 0.45
    fases = {"pata_ti": 0.0, "pata_td": 0.08, "pata_dd": 0.5, "pata_di": 0.58}

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _galope(L, p, fases, u, 0.38, 48.0, 1.4)
        meneo = 10.0 * math.sin(TAU * u + 0.5)
        p.rot("cuerpo", rx=meneo)
        p.pos("cuerpo", y=-0.4 + 0.5 * math.sin(2 * TAU * u))
        p.rot("cabeza", rx=-meneo - 3.0)
        p.rot("cola", rx=-10.0 + 10.0 * math.sin(TAU * u - 0.8), ry=8.0 * math.sin(TAU * u))
        return _montar_patas(L, p)
    return largo, pose_en


def correr_estampida(L):
    """Estampida (toro, bufalo, hipopotamo, cria de Iskarum): galope pesado, la cabeza baja (los cuernos al frente),
    todo el cuerpo rebota y se mece; la trompa y la cola van sueltas."""
    largo = {"cria_iskarum": 0.75, "hipopotamo": 0.65}.get(L.b.id, 0.6)
    fases = {"pata_ti": 0.0, "pata_td": 0.12, "pata_di": 0.5, "pata_dd": 0.62}

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _galope(L, p, fases, u, 0.5, 30.0, 1.8)
        meneo = 5.0 * math.sin(TAU * u + 0.6)
        p.rot("cuerpo", rx=meneo, rz=2.0 * math.sin(TAU * u))
        p.pos("cuerpo", y=0.3 + 0.9 * math.sin(2 * TAU * u))
        p.rot("cabeza", rx=-meneo - 14.0, rz=-2.0 * math.sin(TAU * u))
        p.rot("trompa", rx=14.0 * math.sin(2 * TAU * u - 1.0), rz=6.0 * math.sin(TAU * u))
        p.rot("cola", rx=-12.0 + 8.0 * math.sin(2 * TAU * u), rz=8.0 * math.sin(TAU * u))
        return _montar_patas(L, p)
    return largo, pose_en


def correr_brincos(L):
    """Brincos por pares (babuino, liebre, marmota): las manos juntas y luego las patas juntas, el lomo se dobla y
    se estira. La liebre corre en zigzag (cambia de lado cada dos brincos)."""
    ident = L.b.id
    ciclo = {"babuino": 0.5, "marmota": 0.4, "liebre_dorada": 0.4}[ident]
    largo = ciclo * (4 if ident == "liebre_dorada" else 1)
    fases = {"pata_dd": 0.0, "pata_di": 0.06, "pata_td": 0.5, "pata_ti": 0.56}

    def pose_en(t):
        u = t / ciclo
        p = L.pose()
        liebre = ident == "liebre_dorada"
        _galope(L, p, fases, u, 0.42, 30.0 if liebre else 36.0, 1.0 if liebre else 2.0)
        meneo = 9.0 * math.sin(TAU * u)
        p.rot("cuerpo", rx=meneo)
        p.pos("cuerpo", y=0.8 + 0.8 * math.sin(TAU * u - 0.5))
        p.rot("cabeza", rx=-meneo * 0.8)
        p.rot("cola", rx=-6.0 * math.sin(TAU * u - 1.0))
        if ident == "liebre_dorada":                   # zigzag: gira a un lado y luego al otro
            p.rot("raiz", ry=18.0 * math.sin(TAU * t / largo))
        return _montar_patas(L, p)
    return largo, pose_en


def correr_elastico(L):
    """Saltos elasticos (cervatillo, cabra): rebota con las cuatro patas tiesas (las de adelante un poco adelante,
    las de atras atras), todo el cuerpo en el aire; la cabeza en alto y la cola parada."""
    largo = 0.6

    def pose_en(t):
        u = (t / largo) % 1.0
        p = L.pose()
        aire = math.sin(math.pi * min(1.0, u / 0.7)) if u < 0.7 else 0.0
        p.pos("raiz", y=5.0 * aire)
        abre = 10.0 * aire
        p.rot("pata_dd", abre)
        p.rot("pata_di", abre)
        p.rot("pata_td", -abre)
        p.rot("pata_ti", -abre)
        if u >= 0.7:                                    # al caer se agacha y rebota
            f = (u - 0.7) / 0.3
            p.pos("cuerpo", y=-0.8 * math.sin(math.pi * f))
        p.rot("cuerpo", rx=4.0 * math.sin(TAU * u))
        p.rot("cuello", rx=-3.0 * math.sin(TAU * u))
        p.rot("cabeza", rx=4.0 * aire)
        p.rot("cola", rx=-25.0)
        return p
    return largo, pose_en


def correr_camello(L):
    """Dromedario: ambladura rapida (la montura que vuela en la arena): zancadas largas, el cuello estirado al
    frente y bien mecido de lado a lado."""
    largo = 0.7

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for lado, f in (("d", 0.0), ("i", 0.5)):
            for fila in "dt":
                giro, alza = _pata(u + f, 0.5, 28.0, 2.4)
                p.rot(f"pata_{fila}{lado}", giro)
                p.pos(f"pata_{fila}{lado}", y=alza)
        p.rot("cuerpo", rz=5.0 * math.sin(TAU * u))
        p.pos("cuerpo", y=0.4 + 0.5 * math.cos(2 * TAU * u))
        p.rot("cuello", rx=-14.0 + 4.0 * math.sin(2 * TAU * u - 0.6), rz=-3.0 * math.sin(TAU * u))
        p.rot("cabeza", rx=12.0 - 3.5 * math.sin(2 * TAU * u - 0.6))
        p.rot("cola", rx=-15.0, rz=10.0 * math.sin(TAU * u - 0.8))
        return _montar_patas(L, p)
    return largo, pose_en


def correr_escurridizo(L):
    """Escurridizos (lagarto, lagartija): patitas a toda velocidad, la S del cuerpo mas marcada y la cola alzada
    meciendose."""
    largo = 0.3

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, s, f in (("pata_dd", 1, 0.0), ("pata_ti", -1, 0.0), ("pata_di", -1, 0.5), ("pata_td", 1, 0.5)):
            _lateral(p, h, s, u + f, 0.5, 32.0, 22.0)
        dobla = 12.0 * math.sin(TAU * u)
        p.rot("cuerpo", ry=dobla)
        p.rot("cabeza", ry=-dobla * 1.1, rx=4.0)
        p.rot("cola1", rx=-14.0)
        _onda(p, ("cola1", "cola2", "cola3"), u, 12.0, 1.0, crece=0.2)
        return p
    return largo, pose_en


def correr_bajo(L):
    """Carrera baja (cocodrilo, salamandra, ajolote): serpentea fuerte pegado al piso, con zancadas largas."""
    largo = {"cocodrilo_luz": 0.8, "salamandra_ceniza": 0.55, "cria_moruvahn": 0.6}[L.b.id]

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, s, f in (("pata_dd", 1, 0.0), ("pata_ti", -1, 0.0), ("pata_di", -1, 0.5), ("pata_td", 1, 0.5)):
            _lateral(p, h, s, u + f, 0.5, 34.0, 20.0)
        dobla = 15.0 * math.sin(TAU * u)
        p.rot("cuerpo", ry=dobla)
        p.pos("cuerpo", y=0.25 * math.cos(2 * TAU * u))
        p.rot("cabeza", ry=-dobla * 1.15)
        _onda(p, ("cola1", "cola2", "cola3"), u, 15.0, 1.1, crece=0.3)
        return p
    return largo, pose_en


def acelerado(f, k=2.0):
    """La misma animacion k veces mas rapida (las patitas: insectos, aracnidos, cangrejo)."""
    def g(L):
        largo, pose_en = f(L)
        return round(largo / k / 0.05) * 0.05, lambda t: pose_en(t * largo / (round(largo / k / 0.05) * 0.05))
    return g


def correr_serpiente(L):
    """Serpientes: la onda mas rapida y mas ancha, con la cabeza alzada."""
    tramos = sorted((h for h in L.huesos if h.startswith("s") and h[1:].isdigit()), key=lambda h: int(h[1:]))
    largo = 0.9 if L.b.id == "cria_varkhum" else 0.7

    def pose_en(t):
        u = t / largo
        p = L.pose()
        _onda(p, tramos[1:], u, 15.0 if L.b.id == "cria_varkhum" else 22.0, 0.8, rampa=3)
        p.rot(tramos[0], rx=8.0, ry=-8.0 * math.sin(TAU * u - 0.8))
        p.rot(tramos[1], rx=-8.0)
        return p
    return largo, pose_en


def correr_despegue(L):
    """Despegue (todas las aves): corre a pasitos rapidos inclinada al frente con las alas abiertas aleteando, como
    al tomar vuelo."""
    largo = 0.4 if L.largo_pata("pata_d") < 5 else 0.5

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for h, f in (("pata_d", 0.0), ("pata_i", 0.5)):
            giro, alza = _pata(u + f, 0.5, 30.0, 1.6)
            p.rot(h, giro)
            p.pos(h, y=alza)
        p.rot("cuerpo", rx=-10.0)
        p.pos("cuerpo", y=0.5 + 0.4 * math.sin(2 * TAU * u))
        aleteo = 75.0 + 30.0 * math.sin(2 * TAU * u)
        p.rot("ala_d", rz=aleteo)
        p.rot("ala_i", rz=-aleteo)
        p.rot("cuello", rx=-12.0)
        p.rot("cabeza", rx=10.0)
        p.rot("cola", rx=8.0)
        return _montar_patas(L, p)
    return largo, pose_en


def correr_murcielago(L):
    """Murcielago: aleteo mas rapido, inclinado al frente."""
    largo = 0.25

    def pose_en(t):
        u = t / largo
        p = L.pose()
        a = 32.0 * math.sin(TAU * u)
        p.rot("cuerpo", rx=-18.0)
        p.rot("ala_d", rz=a)
        p.rot("ala_i", rz=-a)
        p.pos("cuerpo", y=1.0 - 0.6 * math.sin(TAU * u))
        for h in ("pata_d", "pata_i"):
            p.pos(h, y=1.0 - 0.6 * math.sin(TAU * u))
            p.rot(h, 40.0)
        p.rot("cabeza", rx=14.0)
        return p
    return largo, pose_en


def correr_ballenato(L):
    """Ballenato: nada rapido y brinca fuera de la arena como delfin (sale de punta, arquea y se clava)."""
    largo = 1.6

    def pose_en(t):
        u = (t / largo) % 1.0
        p = L.pose()
        brinco = math.sin(math.pi * min(1.0, u / 0.55)) if u < 0.55 else 0.0
        f = min(1.0, u / 0.55)
        p.pos("raiz", y=9.0 * brinco)
        p.rot("raiz", rx=(22.0 - 44.0 * f) * (1.0 if u < 0.55 else 0.0))
        nado = 1.0 - brinco
        p.rot("cola", rx=-24.0 * math.sin(TAU * 3 * u - 1.2) * nado + 10.0 * brinco)
        p.rot("cuerpo", rx=4.0 * math.sin(TAU * 3 * u) * nado)
        p.pos("cuerpo", y=1.0)
        p.rot("aleta_d", rz=-25.0 * brinco + 10.0 * math.sin(TAU * 3 * u) * nado)
        p.rot("aleta_i", rz=25.0 * brinco - 10.0 * math.sin(TAU * 3 * u) * nado)
        return p
    return largo, pose_en


def correr_ramita(L):
    """Ramita: no corre; se queda tiesa fingiendo ser rama (las patas pegadas al cuerpo, a lo largo) y apenas se
    mece con el viento."""
    largo = 2.0

    def pose_en(t):
        u = t / largo
        p = L.pose()
        for k, s in ((1, 1), (1, -1), (2, 1), (2, -1), (3, 1), (3, -1)):
            h = f"pata_{k}{'d' if s > 0 else 'i'}"
            p.rot(h, ry=s * (35.0 if k == 1 else -30.0), rz=s * 4.0)
        p.rot("cabeza", rx=-4.0)
        p.rot("cuerpo", rz=1.5 * math.sin(TAU * u))
        return p
    return largo, pose_en


CORRER = {
    "galope_lobo": (correr_lobo, ["lobo_fuego", "chacal_ceniza"]),
    "zorro": (correr_zorro, ["fenec"]),
    "felino": (correr_felino, ["gato_thza"]),
    "estampida": (correr_estampida, ["toro_arena", "bufalo_terracota", "hipopotamo", "cria_iskarum"]),
    "brincos": (correr_brincos, ["babuino", "liebre_dorada", "marmota"]),
    "elasticos": (correr_elastico, ["cervatillo_musgo", "cabra_escarcha"]),
    "camello": (correr_camello, ["dromedario"]),
    "escurridizos": (correr_escurridizo, ["lagarto_roca", "lagartija_blanca"]),
    "carrera_baja": (correr_bajo, ["cocodrilo_luz", "salamandra_ceniza", "cria_moruvahn"]),
    "patitas_insectos": (acelerado(caminar_insecto), ["escarabajo_sagrado", "escarabajo_brasa"]),
    "patitas_aracnidos": (acelerado(caminar_aracnido), ["escorpion_luz", "garrapata_sal"]),
    "patitas_cangrejo": (acelerado(caminar_cangrejo), ["cangrejo"]),
    "serpientes": (correr_serpiente, ["serpiente_rio_seco", "cria_varkhum"]),
    "despegue": (correr_despegue, ["pato_estanque", "buitre", "halcon_cobre", "aguila_gris", "cuervo_negro", "ibis",
                                   "flamenco"]),
    "murcielago": (correr_murcielago, ["murcielago_mura"]),
    "ballenato": (correr_ballenato, ["ballenato_duna"]),
    "ramita_tiesa": (correr_ramita, ["ramita"]),
}

# ====================================================================== atacar
# Un solo ataque por grupo (lo indispensable), con el estilo de su caminado. No van en bucle. GOLPE: el segundo en
# que pega (el mod aplica el dano y la mecanica ahi).

def _k(t, *puntos):
    """Curva suave por los puntos (t, valor)."""
    return animar.suave(t, list(puntos))


def atacar_embestida(L):
    """Embestida (toro, bufalo, cria de Iskarum, cabra): se echa atras con la cabeza baja, arremete y al final
    avienta la cabeza para arriba."""
    largo = 1.0

    def pose_en(t):
        p = L.pose()
        p.pos("cuerpo", z=_k(t, (0, 0), (0.3, 1.5), (0.5, -3.0), (0.75, -1.0), (1.0, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.3, 4.0), (0.5, -6.0), (0.75, 2.0), (1.0, 0)))
        p.rot("cabeza", rx=_k(t, (0, 0), (0.35, -25.0), (0.5, -20.0), (0.62, 15.0), (1.0, 0)))
        p.rot("trompa", rx=_k(t, (0, 0), (0.35, 25.0), (0.62, -20.0), (1.0, 0)))
        for h in ("pata_dd", "pata_di"):
            p.rot(h, _k(t, (0, 0), (0.3, 12.0), (0.5, -10.0), (1.0, 0)))
        for h in ("pata_td", "pata_ti"):
            p.rot(h, _k(t, (0, 0), (0.3, 8.0), (0.5, -18.0), (1.0, 0)))
        p.rot("cola", rx=_k(t, (0, 0), (0.5, -18.0), (1.0, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def atacar_mordida_grande(L):
    """Mordida grande: el hipopotamo alza la cabeza enorme y la azota; el cocodrilo arremete, muerde y da el giro
    de la muerte (para arrastrar al agua); el ballenato sale de la arena de punta, traga y se vuelve a hundir."""
    ident = L.b.id
    if ident == "cocodrilo_luz":
        largo = 1.4

        def pose_en(t):
            p = L.pose()
            p.pos("cuerpo", z=_k(t, (0, 0), (0.15, 0.8), (0.32, -3.0), (0.6, -2.0), (1.4, 0)))
            p.rot("cabeza", rx=_k(t, (0, 0), (0.2, 22.0), (0.35, -6.0), (0.6, 0.0), (1.4, 0)))
            f = min(1.0, max(0.0, (t - 0.6) / 0.6))
            p.rot("cuerpo", rz=360.0 * animar.facil(f))
            p.pos("cuerpo", y=6.0 * math.sin(math.pi * f))
            _onda(p, ("cola1", "cola2", "cola3"), t / 0.5, 10.0 * (1 - f), 1.0)
            return p
        return largo, pose_en
    if ident == "ballenato_duna":
        largo = 1.6

        def pose_en(t):
            p = L.pose()
            p.pos("raiz", y=_k(t, (0, 0), (0.3, -2.5), (0.6, 7.0), (0.8, 6.0), (1.2, -1.0), (1.6, 0)))
            p.rot("raiz", rx=_k(t, (0, 0), (0.3, -8.0), (0.6, 38.0), (0.8, 30.0), (1.2, -18.0), (1.6, 0)))
            p.rot("cabeza", rx=_k(t, (0, 0), (0.55, 8.0), (0.75, -6.0), (1.0, 0)))
            p.rot("cola", rx=_k(t, (0, 0), (0.45, -20.0), (0.7, 15.0), (1.1, -15.0), (1.6, 0)))
            p.rot("aleta_d", rz=_k(t, (0, 0), (0.6, -30.0), (1.2, 10.0), (1.6, 0)))
            p.rot("aleta_i", rz=_k(t, (0, 0), (0.6, 30.0), (1.2, -10.0), (1.6, 0)))
            p.pos("cuerpo", y=1.0)
            return p
        return largo, pose_en
    largo = 1.0

    def pose_en(t):
        p = L.pose()
        p.rot("cabeza", rx=_k(t, (0, 0), (0.4, 32.0), (0.55, -12.0), (0.7, -8.0), (1.0, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.4, 3.0), (0.55, -3.0), (1.0, 0)))
        p.pos("cuerpo", z=_k(t, (0, 0), (0.4, 0.8), (0.55, -2.0), (1.0, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def atacar_jauria(L):
    """Mordida de jauria (lobo de fuego, chacal): se agacha, se lanza con las manos al frente, abre el hocico y
    muerde, y jala sacudiendo la cabeza de lado a lado."""
    largo = 0.9

    def pose_en(t):
        p = L.pose()
        p.pos("cuerpo", y=_k(t, (0, 0), (0.2, -1.0), (0.4, 1.0), (0.55, 0.0), (0.9, 0)),
              z=_k(t, (0, 0), (0.2, 1.0), (0.4, -4.0), (0.7, -3.0), (0.9, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.2, -4.0), (0.4, 5.0), (0.55, 0.0), (0.9, 0)))
        p.rot("cabeza", rx=_k(t, (0, 0), (0.2, -8.0), (0.4, 4.0), (0.55, -6.0), (0.9, 0)),
              ry=_k(t, (0, 0), (0.45, 0.0), (0.52, 14.0), (0.6, -14.0), (0.68, 12.0), (0.76, 0.0), (0.9, 0)))
        p.rot("mandibula", rx=_k(t, (0, 0), (0.3, -32.0), (0.4, 0.0), (0.8, 0.0), (0.9, 0)))
        for h in ("pata_dd", "pata_di"):
            p.rot(h, _k(t, (0, 0), (0.2, -8.0), (0.38, 34.0), (0.55, 10.0), (0.9, 0)))
        for h in ("pata_td", "pata_ti"):
            p.rot(h, _k(t, (0, 0), (0.2, 10.0), (0.4, -22.0), (0.9, 0)))
        p.rot("cola", rx=_k(t, (0, 0), (0.4, -16.0), (0.9, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def atacar_zarpazo(L):
    """Zarpazo: el gato se alza y suelta un manotazo con la derecha; el babuino se para de manos y barre con el brazo
    de afuera hacia adentro (asi arrebata la comida)."""
    babuino = L.b.id == "babuino"
    largo = 0.7 if babuino else 0.6
    golpe = 0.35 if babuino else 0.3

    def pose_en(t):
        p = L.pose()
        p.rot("cuerpo", rx=_k(t, (0, 0), (golpe - 0.12, 12.0 if babuino else 9.0), (golpe, 6.0), (largo, 0)),
              ry=_k(t, (0, 0), (golpe - 0.12, -10.0 if babuino else 0.0), (golpe, 10.0 if babuino else 0.0), (largo, 0)))
        p.rot("pata_dd", _k(t, (0, 0), (golpe - 0.12, 80.0 if babuino else 65.0), (golpe, 5.0), (largo, 0)),
              rz=_k(t, (0, 0), (golpe - 0.12, 25.0 if babuino else 8.0), (golpe, -25.0 if babuino else -4.0), (largo, 0)))
        p.pos("pata_dd", y=_k(t, (0, 0), (golpe - 0.12, 1.2), (golpe, 0.3), (largo, 0)))
        p.rot("cabeza", rx=_k(t, (0, 0), (golpe - 0.12, -10.0), (golpe, -4.0), (largo, 0)))
        p.rot("cola", rx=_k(t, (0, 0), (golpe, -12.0), (largo, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def atacar_picada(L):
    """Picada (halcon, aguila, cuervo, murcielago): abre las alas, se clava inclinado al frente con las garras
    adelante y pega; el cuervo y el murcielago rematan con el pico o la mordida."""
    murcielago = L.b.id == "murcielago_mura"
    largo = 0.6 if murcielago else 0.8
    golpe = 0.3 if murcielago else 0.45

    def pose_en(t):
        p = L.pose()
        if murcielago:
            a = _k(t, (0, 0), (0.15, 30.0), (golpe, -10.0), (0.45, 26.0), (largo, 0))
            p.rot("ala_d", rz=a)
            p.rot("ala_i", rz=-a)
            p.rot("cuerpo", rx=_k(t, (0, 0), (golpe, -25.0), (largo, 0)))
            p.pos("cuerpo", y=1.0, z=_k(t, (0, 0), (golpe, -2.0), (largo, 0)))
            for h in ("pata_d", "pata_i"):
                p.pos(h, y=1.0, z=_k(t, (0, 0), (golpe, -2.0), (largo, 0)))
            p.rot("cabeza", rx=_k(t, (0, 0), (golpe - 0.08, 15.0), (golpe, -15.0), (largo, 0)))
            return p
        alas = _k(t, (0, 0), (0.15, 95.0), (0.35, 40.0), (golpe, 100.0), (0.65, 60.0), (largo, 0))
        p.rot("ala_d", rz=alas)
        p.rot("ala_i", rz=-alas)
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.35, -28.0), (golpe, -12.0), (largo, 0)))
        p.pos("cuerpo", y=_k(t, (0, 0), (0.2, 1.5), (golpe, 0.5), (largo, 0)))
        for h in ("pata_d", "pata_i"):
            p.rot(h, _k(t, (0, 0), (0.3, -10.0), (golpe, 45.0), (0.65, 18.0), (largo, 0)))
        cab = "cabeza"
        p.rot(cab, rx=_k(t, (0, 0), (golpe - 0.05, 10.0), (golpe + 0.05, -22.0), (largo, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def atacar_pinza(L):
    """Pinza o aguijon: el escorpion abre las pinzas y clava la cola por encima de la espalda; el cangrejo alza la
    pinza grande y la cierra de golpe."""
    if L.b.id == "escorpion_luz":
        largo = 0.7

        def pose_en(t):
            p = L.pose()
            for k, h in enumerate(("cola1", "cola2", "cola3", "cola4")):
                p.rot(h, rx=_k(t, (0, 0), (0.25, 6.0), (0.4, -14.0 - 6.0 * k), (0.55, -8.0), (0.7, 0)))
            p.rot("pinza_d", ry=_k(t, (0, 0), (0.25, 18.0), (0.45, -6.0), (0.7, 0)))
            p.rot("pinza_i", ry=_k(t, (0, 0), (0.25, -18.0), (0.45, 6.0), (0.7, 0)))
            p.pos("cuerpo", z=_k(t, (0, 0), (0.25, 0.6), (0.4, -0.8), (0.7, 0)))
            return p
        return largo, pose_en
    largo = 0.6

    def pose_en(t):
        p = L.pose()
        p.rot("pinza_d", rx=_k(t, (0, 0), (0.2, 40.0), (0.35, -10.0), (0.6, 0)))
        p.rot("pinza_i", rx=_k(t, (0, 0), (0.15, 15.0), (0.4, -5.0), (0.6, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.2, 6.0), (0.35, -3.0), (0.6, 0)))
        return p
    return largo, pose_en


def atacar_lanzarse(L):
    """Lanzarse y morder: la serpiente alza la cabeza, se recoge en S y se dispara al frente; el ajolote arremete con
    todo el cuerpo y muerde."""
    tramos = sorted((h for h in L.huesos if h.startswith("s") and h[1:].isdigit()), key=lambda h: int(h[1:]))
    if tramos:
        largo = 0.9 if L.b.id == "cria_varkhum" else 0.8
        g = 0.45 * largo / 0.8
        alza = 8.0 if L.b.id == "cria_varkhum" else 11.0

        def pose_en(t):
            p = L.pose()
            p.rot(tramos[0], rx=_k(t, (0, 0), (g - 0.15, alza), (g, 4.0), (largo, 0)))
            p.pos(tramos[0], z=_k(t, (0, 0), (g - 0.15, 2.0), (g, -5.0), (g + 0.15, -4.0), (largo, 0)))
            p.rot(tramos[1], rx=_k(t, (0, 0), (g - 0.15, -alza), (g, -4.0), (largo, 0)))
            curva = _k(t, (0, 0), (g - 0.15, 1.0), (g, 0.2), (largo, 0))
            for k, h in enumerate(tramos[2:6]):
                p.rot(h, ry=curva * (18.0 if k % 2 == 0 else -18.0))
            return p
        return largo, pose_en
    largo = 0.7

    def pose_en(t):
        p = L.pose()
        p.pos("cuerpo", z=_k(t, (0, 0), (0.2, 0.8), (0.35, -2.5), (0.7, 0)))
        p.rot("cabeza", rx=_k(t, (0, 0), (0.2, 15.0), (0.35, -10.0), (0.7, 0)))
        _onda(p, ("cola1", "cola2", "cola3"), t / 0.35, 12.0, 1.0)
        return p
    return largo, pose_en


def atacar_emboscada(L):
    """Emboscada (ramita): tiesa como rama y de golpe se despliega: alza el frente y azota las patas de adelante."""
    largo = 0.9
    tiesa = {1: 35.0, 2: -30.0, 3: -30.0}

    def pose_en(t):
        p = L.pose()
        f = _k(t, (0, 1.0), (0.25, 1.0), (0.4, 0.0), (0.9, 0.0))      # 1 = tiesa
        for k in (1, 2, 3):
            for lado, s in (("d", 1), ("i", -1)):
                h = f"pata_{k}{lado}"
                p.rot(h, ry=s * tiesa[k] * f, rz=s * 4.0 * f)
        p.rot("pata_1d", rz=_k(t, (0, 0), (0.4, 45.0), (0.55, -8.0), (0.9, 0)))
        p.rot("pata_1i", rz=_k(t, (0, 0), (0.4, -45.0), (0.55, 8.0), (0.9, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.25, 0.0), (0.42, 22.0), (0.55, 8.0), (0.9, 0)))
        p.pos("cuerpo", y=_k(t, (0, 0), (0.25, 0.0), (0.42, 1.5), (0.9, 0)))
        return p
    return largo, pose_en


def atacar_pegarse(L):
    """Pegarse (garrapata): se agacha y salta con las patas abiertas para agarrarse."""
    largo = 0.7

    def pose_en(t):
        p = L.pose()
        p.pos("raiz", y=_k(t, (0, 0), (0.15, 0.0), (0.32, 3.5), (0.5, 1.0), (0.7, 0)),
              z=_k(t, (0, 0), (0.15, 0.5), (0.45, -4.0), (0.7, 0)))
        p.rot("raiz", rx=_k(t, (0, 0), (0.3, 10.0), (0.5, -3.0), (0.7, 0)))
        abre = _k(t, (0, 0), (0.15, 0.0), (0.35, 30.0), (0.5, 20.0), (0.7, 0))
        for k in (1, 2, 3):
            p.rot(f"pata_{k}d", rz=abre)
            p.rot(f"pata_{k}i", rz=-abre)
        return p
    return largo, pose_en


def atacar_escupir(L):
    """Escupir (salamandra): echa la cabeza atras tomando aire y la avienta al frente escupiendo la brasa."""
    largo = 0.8

    def pose_en(t):
        p = L.pose()
        p.rot("cabeza", rx=_k(t, (0, 0), (0.3, 22.0), (0.45, -10.0), (0.6, -4.0), (0.8, 0)))
        p.pos("cuerpo", z=_k(t, (0, 0), (0.3, 1.0), (0.45, -1.0), (0.8, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.3, 5.0), (0.45, -3.0), (0.8, 0)))
        p.rot("cola1", ry=_k(t, (0, 0), (0.3, 10.0), (0.45, -10.0), (0.8, 0)))
        return p
    return largo, pose_en


def atacar_explotar(L):
    """Explotar (escarabajo de brasa, al morir): tiembla cada vez mas fuerte, se alza con las patas tiesas y revienta
    (las chispas las pone el mod al final)."""
    largo = 0.8

    def pose_en(t):
        p = L.pose()
        f = t / largo
        temblor = 0.35 * f * math.sin(TAU * 9 * t)
        p.pos("cuerpo", x=temblor, y=1.2 * f + abs(temblor))
        p.rot("cuerpo", rz=8.0 * f * math.sin(TAU * 7 * t))
        for k in (1, 2, 3):
            p.rot(f"pata_{k}d", rz=28.0 * f)
            p.rot(f"pata_{k}i", rz=-28.0 * f)
        return p
    return largo, pose_en


def atacar_generico(L):
    """El ataque generico de los que solo atacan manchados de mura: las aves dan picotazo, los chicos (liebre,
    marmota, lagartos) una mordida rapida, el dromedario patea atras y el escarabajo sagrado da un cabezazo."""
    ident = L.b.id
    if ident == "dromedario":
        largo = 0.9

        def pose_en(t):
            p = L.pose()
            p.rot("cuerpo", rx=_k(t, (0, 0), (0.3, -4.0), (0.45, -9.0), (0.9, 0)))
            for h in ("pata_td", "pata_ti"):
                p.rot(h, _k(t, (0, 0), (0.3, 10.0), (0.45, -55.0), (0.65, -10.0), (0.9, 0)))
                p.pos(h, y=_k(t, (0, 0), (0.45, 1.5), (0.9, 0)))
            p.rot("cuello", rx=_k(t, (0, 0), (0.45, -12.0), (0.9, 0)))
            p.rot("cabeza", rx=_k(t, (0, 0), (0.45, 10.0), (0.9, 0)))
            return _montar_patas(L, p)
        return largo, pose_en
    if ident == "escarabajo_sagrado":
        largo = 0.7

        def pose_en(t):
            p = L.pose()
            p.pos("cuerpo", z=_k(t, (0, 0), (0.2, 0.8), (0.35, -2.0), (0.7, 0)))
            p.rot("cuerpo", rx=_k(t, (0, 0), (0.2, 6.0), (0.35, -6.0), (0.7, 0)))
            p.pos("cuerpo", y=_k(t, (0, 0), (0.2, 0.5), (0.35, 0.3), (0.7, 0)))
            p.rot("cabeza", rx=_k(t, (0, 0), (0.2, 12.0), (0.35, -10.0), (0.7, 0)))
            return p
        return largo, pose_en
    if "ala_d" in L.huesos:                                  # aves: picotazo
        largo = 0.5

        def pose_en(t):
            p = L.pose()
            cab = "cuello" if "cuello" in L.huesos else "cabeza"
            p.rot(cab, rx=_k(t, (0, 0), (0.12, 12.0), (0.25, -32.0), (0.5, 0)))
            p.rot("cuerpo", rx=_k(t, (0, 0), (0.25, -8.0), (0.5, 0)))
            p.rot("ala_d", rz=_k(t, (0, 0), (0.25, 20.0), (0.5, 0)))
            p.rot("ala_i", rz=_k(t, (0, 0), (0.25, -20.0), (0.5, 0)))
            return _montar_patas(L, p)
        return largo, pose_en
    largo = 0.5                                               # mordida rapida

    def pose_en(t):
        p = L.pose()
        p.pos("cuerpo", z=_k(t, (0, 0), (0.12, 0.6), (0.25, -1.5), (0.5, 0)))
        p.rot("cabeza", rx=_k(t, (0, 0), (0.12, 12.0), (0.25, -12.0), (0.5, 0)))
        return _montar_patas(L, p) if "pata_dd" in L.huesos and L.rig.padre["pata_dd"] == "raiz" else p
    return largo, pose_en


ATACAR = {
    "embestida": (atacar_embestida, ["toro_arena", "bufalo_terracota", "cria_iskarum", "cabra_escarcha"]),
    "mordida_grande": (atacar_mordida_grande, ["hipopotamo", "cocodrilo_luz", "ballenato_duna"]),
    "jauria": (atacar_jauria, ["lobo_fuego", "chacal_ceniza"]),
    "zarpazo": (atacar_zarpazo, ["gato_thza", "babuino"]),
    "picada": (atacar_picada, ["halcon_cobre", "aguila_gris", "cuervo_negro", "murcielago_mura"]),
    "pinza": (atacar_pinza, ["escorpion_luz", "cangrejo"]),
    "lanzarse": (atacar_lanzarse, ["serpiente_rio_seco", "cria_varkhum", "cria_moruvahn"]),
    "emboscada": (atacar_emboscada, ["ramita"]),
    "pegarse": (atacar_pegarse, ["garrapata_sal"]),
    "escupir": (atacar_escupir, ["salamandra_ceniza"]),
    "explotar": (atacar_explotar, ["escarabajo_brasa"]),
    "generico_mura": (atacar_generico, ["pato_estanque", "ibis", "flamenco", "buitre", "liebre_dorada", "marmota",
                                        "lagarto_roca", "lagartija_blanca", "dromedario", "escarabajo_sagrado"]),
}
GOLPE = {"embestida": 0.5, "mordida_grande": {"hipopotamo": 0.55, "cocodrilo_luz": 0.35, "ballenato_duna": 0.75},
         "jauria": 0.4, "zarpazo": {"gato_thza": 0.3, "babuino": 0.35},
         "picada": {"murcielago_mura": 0.3, "*": 0.45}, "pinza": {"escorpion_luz": 0.4, "cangrejo": 0.35},
         "lanzarse": {"cria_varkhum": 0.5, "serpiente_rio_seco": 0.45, "cria_moruvahn": 0.35}, "emboscada": 0.55,
         "pegarse": 0.45, "escupir": 0.45, "explotar": 0.8,
         "generico_mura": {"dromedario": 0.45, "escarabajo_sagrado": 0.35, "*": 0.25}}


# ====================================================================== ambiente
# Animaciones de ambiente: chiquitas y por grupos estrictos (hasta de uno). Todas en bucle: las que son una postura
# (echarse, sentarse, colgarse) se quedan respirando; GeckoLib hace la transicion al entrar y al salir.

def _seguir(L, p, h):
    """La pata h (colgada de la raiz) sigue por completo a su cadera en el cuerpo (tambien si baja)."""
    T = L.rig.transformaciones(p)
    T0 = L.rig.transformaciones({})
    local = animar._inversa(T["raiz"]).despues(T["cuerpo"])
    local0 = animar._inversa(T0["raiz"]).despues(T0["cuerpo"])
    piv = L.rig.pivote[h]
    a, b = local(piv), local0(piv)
    p.pos(h, x=a[0] - b[0], y=a[1] - b[1], z=a[2] - b[2])
    return a


def _sentar(L, p, angulo, f=1.0):
    """Sentado sobre las ancas: el lomo se alza 'angulo' (por f, de 0 a 1) sin que se muevan las manos del piso, y
    las patas de atras se doblan al frente hasta que el pie llega al piso."""
    th = math.radians(angulo * f)
    c = L.rig.pivote["cuerpo"]
    y0, zf = L.rig.pivote["pata_dd"][1], L.rig.pivote["pata_dd"][2]
    sube = (y0 - c[1]) * (math.cos(th) - 1) - (zf - c[2]) * math.sin(th)
    p.rot("cuerpo", rx=angulo * f)
    p.pos("cuerpo", y=-sube)
    for h in ("pata_dd", "pata_di"):
        _seguir(L, p, h)
    cajas = _cajas(L)
    for h in ("pata_td", "pata_ti"):
        _seguir(L, p, h)
        rot, tras = p.get(h, ((0, 0, 0), (0, 0, 0)))
        bajo, alto = 0.0, 110.0                         # el giro mas chico con el que la pata ya no entra al piso
        for _ in range(14):
            medio = (bajo + alto) / 2
            p[h] = ((medio, rot[1], rot[2]), tras)
            T = L.rig.transformaciones(p)
            y = min(T[h](q)[1] for giro, a, b in cajas[h] for q in _esquinas(giro, a, b))
            bajo, alto = (bajo, medio) if y >= 0.05 else (medio, alto)
        p[h] = ((alto, rot[1], rot[2]), tras)
    return p


def _pararse(L, p, angulo, f=1.0):
    """Parado en las patas de atras (o sentado en las ancas): el lomo gira 'angulo' alrededor de la cadera de atras,
    que no se mueve; las de adelante se alzan con el pecho."""
    p.rot("cuerpo", rx=angulo * f)
    T = L.rig.transformaciones(p)
    T0 = L.rig.transformaciones({})
    cadera = L.rig.pivote["pata_td"]
    a, b = T["cuerpo"](cadera), T0["cuerpo"](cadera)
    p.pos("cuerpo", x=b[0] - a[0], y=b[1] - a[1], z=b[2] - a[2])
    for h in ("pata_dd", "pata_di"):
        _seguir(L, p, h)
    return p


def _echar(L, p, f=1.0):
    """Echado: el cuerpo baja hasta el piso y las patas se doblan debajo (las de adelante hacia atras, las de atras
    hacia adelante)."""
    g = 0.0
    for c in L.a.m.cubos:
        if c.nombre == "pata_dd" or c.nombre.startswith("pata_dd"):
            g = c.hasta[0] - c.desde[0]
            break
    panza = min(c.desde[1] for c in L.a.m.cubos if c.hueso == "raiz/cuerpo")       # lo mas bajo del cuerpo
    baja = (panza - 0.05) * f
    p.pos("cuerpo", y=-baja)
    for h, s in (("pata_dd", -1), ("pata_di", -1), ("pata_td", 1), ("pata_ti", 1)):
        p.rot(h, s * 90.0 * f)
        p.pos(h, y=-(L.largo_pata(h) - g / 2 - 0.1) * f)
    return p


def _ciclo3(t, largo, entra=0.5, sale=0.5):
    """De 0 a 1 al entrar, 1 en medio y de vuelta a 0 al final (para las que van y vuelven en el bucle)."""
    return _k(t, (0, 0.0), (entra, 1.0), (largo - sale, 1.0), (largo, 0.0))


def ambiente_pastar(L):
    """Pastar (toro, bufalo, cabra, cervatillo, dromedario, hipopotamo): baja la cabeza, arranca y mastica, y la alza
    a mirar."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        f = _ciclo3(t, largo, 0.6, 0.6)
        mordida = 4.0 * math.sin(TAU * 4 * t) * _k(t, (0, 0), (0.7, 0), (0.9, 1), (2.0, 1), (2.2, 0), (3.0, 0))
        if "cuello" in L.huesos:
            p.rot("cuello", rx=-38.0 * f)
            p.rot("cabeza", rx=12.0 * f + mordida)
        else:
            p.rot("cabeza", rx=-30.0 * f + mordida)
        p.rot("cola", rz=6.0 * math.sin(TAU * t / 1.5))
        return p
    return largo, pose_en


def ambiente_trompa(L):
    """Cria de Iskarum: arranca pasto con la trompa y se lo lleva a la boca."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        p.rot("cabeza", rx=_k(t, (0, 0), (0.5, -12.0), (1.6, -6.0), (2.4, 0)))
        p.rot("trompa", rx=_k(t, (0, 0), (0.5, -25.0), (0.8, -30.0), (1.4, 40.0), (1.8, 35.0), (2.4, 0)),
              rz=_k(t, (0, 0), (0.8, 6.0), (1.4, -4.0), (2.4, 0)))
        return p
    return largo, pose_en


def ambiente_mordisquear(L):
    """Liebre y marmota: se sientan en las ancas con la comida entre las manos y mordisquean rapidito."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        f = _ciclo3(t, largo, 0.4, 0.4)
        _pararse(L, p, 38.0, f)
        for h in ("pata_dd", "pata_di"):
            p.rot(h, 55.0 * f)
        p.rot("cabeza", rx=-30.0 * f + 3.0 * math.sin(TAU * 6 * t) * f)
        p.rot("cola", rx=-30.0 * f)
        return p
    return largo, pose_en


def ambiente_beber_lamiendo(L):
    """Caninos y gato: bajan la cabeza al agua y beben a lengüetazos."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        f = _ciclo3(t, largo, 0.5, 0.5)
        p.rot("cuerpo", rx=-5.0 * f)
        p.rot("cabeza", rx=-38.0 * f + 3.5 * math.sin(TAU * 5 * t) * f)
        p.rot("mandibula", rx=(-6.0 - 6.0 * math.sin(TAU * 5 * t)) * f)
        p.rot("cola", rx=-4.0 * f, ry=6.0 * math.sin(TAU * t / 1.2))
        return _montar_patas(L, p)
    return largo, pose_en


def ambiente_beber_ave(L):
    """Aves: meten el pico, lo sacan y alzan la cabeza para tragar."""
    largo = 2.0

    def pose_en(t):
        p = L.pose()
        cab = "cuello" if "cuello" in L.huesos else "cabeza"
        p.rot(cab, rx=_k(t, (0, 0), (0.4, -45.0), (0.8, -42.0), (1.2, 18.0), (1.5, 18.0), (2.0, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.4, -10.0), (0.9, -8.0), (1.2, 4.0), (2.0, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def ambiente_lamer_cria(L):
    """Caninos y gato: bajan la cabeza de lado hacia la cria y la lamen a lengüetazos largos."""
    largo = 2.8

    def pose_en(t):
        p = L.pose()
        f = _ciclo3(t, largo, 0.5, 0.5)
        p.rot("cabeza", rx=(-16.0 + 5.0 * math.sin(TAU * 2 * t)) * f, ry=12.0 * f, rz=-4.0 * f)
        p.rot("mandibula", rx=-8.0 * f)
        p.rot("cola", ry=10.0 * math.sin(TAU * t / 0.7))
        return p
    return largo, pose_en


def ambiente_sentarse(L):
    """Lobo y chacal: se sientan en manada a vigilar, jadeando y mirando alrededor."""
    largo = 4.0

    def pose_en(t):
        p = L.pose()
        _sentar(L, p, 30.0)
        p.rot("cabeza", rx=-22.0, ry=14.0 * math.sin(TAU * t / largo))
        p.rot("mandibula", rx=-6.0 - 3.0 * math.sin(TAU * 3 * t))
        p.rot("cola", rx=-45.0)
        p.pos("cuerpo", y=0.12 * math.sin(TAU * 3 * t))
        return p
    return largo, pose_en


def ambiente_aullar(L):
    """Lobo y chacal: sentados, alzan la cabeza y aullan."""
    largo = 3.2

    def pose_en(t):
        p = L.pose()
        _sentar(L, p, 30.0)
        aullido = _k(t, (0, 0), (0.6, 1.0), (2.4, 1.0), (3.2, 0))
        p.rot("cabeza", rx=-22.0 + 62.0 * aullido)
        p.rot("mandibula", rx=-22.0 * aullido * (0.85 + 0.15 * math.sin(TAU * 2 * t)))
        p.rot("cola", rx=-45.0)
        return p
    return largo, pose_en


def ambiente_acicalarse_gato(L):
    """Gato: sentado se lame la mano y se la pasa por la cara."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        _sentar(L, p, 35.0)
        f = _ciclo3(t, largo, 0.5, 0.5)
        p.rot("pata_dd", 50.0 * f)
        p.pos("pata_dd", y=1.0 * f)
        lame = math.sin(TAU * 2.5 * t)
        p.rot("cabeza", rx=-35.0 + (-14.0 + 6.0 * lame) * f, ry=-10.0 * f + 8.0 * lame * f * (t > 1.8))
        p.rot("cola", rx=25.0, ry=10.0 * math.sin(TAU * t / 1.5))
        return p
    return largo, pose_en


def ambiente_acicalarse_ave(L):
    """Aves: voltean la cabeza atras, alzan el ala y se acomodan las plumas a piquetitos."""
    largo = 2.6

    def pose_en(t):
        p = L.pose()
        f = _ciclo3(t, largo, 0.5, 0.5)
        cab = "cuello" if "cuello" in L.huesos else "cabeza"
        p.rot(cab, ry=65.0 * f, rx=(-14.0 + 5.0 * math.sin(TAU * 4 * t)) * f)
        p.rot("ala_d", rz=22.0 * f)
        return p
    return largo, pose_en


def ambiente_despiojar(L):
    """Babuino: sentado se rasca y se busca entre el pelo del costado."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        _sentar(L, p, 15.0)
        f = _ciclo3(t, largo, 0.5, 0.5)
        p.rot("pata_dd", 45.0 * f + 8.0 * math.sin(TAU * 3 * t) * f, rz=-18.0 * f)
        p.pos("pata_dd", y=2.0 * f)
        p.rot("cabeza", rx=-4.0 - 1.0 * f, ry=4.0 * f)
        p.rot("cola", rx=10.0)
        return p
    return largo, pose_en


def ambiente_una_pata(L):
    """Flamenco e ibis: se paran en una pata (la otra doblada arriba) y meten la cabeza."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        p.rot("pata_i", -70.0)
        p.pos("pata_i", y=2.5)
        p.pos("cuerpo", x=0.4, y=0.1 * math.sin(TAU * t / 1.5))
        p.rot("cuerpo", rz=-3.0)
        p.rot("cuello", rx=18.0 + 2.0 * math.sin(TAU * t / 1.5))
        p.rot("cabeza", rx=-14.0)
        return p
    return largo, pose_en


def ambiente_alas_al_sol(L):
    """Buitre y aguila: abren las alas al sol y las dejan extendidas, meciendose con el aire."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        a = 100.0 + 4.0 * math.sin(TAU * t / 1.5)
        p.rot("ala_d", rz=a)
        p.rot("ala_i", rz=-a)
        p.rot("cuerpo", rx=-4.0)
        p.rot("cabeza", ry=20.0 * math.sin(TAU * t / largo))
        return p
    return largo, pose_en


def ambiente_boca_abierta(L):
    """Cocodrilo: se asolea con el hocico abierto, quieto."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        p.rot("cabeza", rx=18.0 + 1.0 * math.sin(TAU * t / 1.5))
        p.rot("cola3", ry=4.0 * math.sin(TAU * t / largo))
        return p
    return largo, pose_en


def ambiente_lagartijeo(L):
    """Lagarto, lagartija y salamandra: lagartijas (se alzan y bajan con las manos) y cabecean."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        sube = max(0.0, math.sin(TAU * t / 0.4)) if t < 1.2 else 0.0
        p.pos("cuerpo", y=0.7 * sube)
        for h, s in (("pata_dd", 1), ("pata_di", -1), ("pata_td", 1), ("pata_ti", -1)):
            p.rot(h, rz=-s * 16.0 * sube)
        p.rot("cabeza", rx=6.0 * sube + 3.0 * math.sin(TAU * t / 0.8) * (t >= 1.2))
        return p
    return largo, pose_en


def ambiente_silbar(L):
    """Marmota: se para en dos patas a vigilar y silba (la cabeza da tironcitos)."""
    largo = 2.6

    def pose_en(t):
        p = L.pose()
        f = _ciclo3(t, largo, 0.4, 0.4)
        _pararse(L, p, 62.0, f)
        for h in ("pata_dd", "pata_di"):
            p.rot(h, 40.0 * f)
        p.rot("cola", rx=-62.0 * f)
        silbido = max(0.0, math.sin(TAU * 2 * t)) if 0.8 < t < 1.9 else 0.0
        p.rot("cabeza", rx=(-55.0 + 10.0 * silbido) * f)
        return p
    return largo, pose_en


def ambiente_colgarse(L):
    """Murcielago: colgado de cabeza, con las alas cerradas, se mece."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        p.rot("raiz", rz=180.0, rx=3.0 * math.sin(TAU * t / largo))
        p.pos("raiz", y=11.0)
        p.rot("ala_d", rz=-55.0)
        p.rot("ala_i", rz=55.0)
        p.rot("cabeza", ry=15.0 * math.sin(TAU * t / largo))
        return p
    return largo, pose_en


def ambiente_enroscarse(L):
    """Serpientes: se enroscan a dormir (respirando)."""
    tramos = sorted((h for h in L.huesos if h.startswith("s") and h[1:].isdigit()), key=lambda h: int(h[1:]))
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        giro = 15.0 if L.b.id == "cria_varkhum" else 31.0
        for h in tramos[1:]:
            p.rot(h, ry=giro + 0.6 * math.sin(TAU * t / largo))
        p.rot(tramos[0], ry=-10.0)
        return p
    return largo, pose_en


def ambiente_limpiarse_ojos(L):
    """Cangrejo: se limpia los ojos con una pinza y luego con la otra."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        d = _k(t, (0, 0), (0.3, 1.0), (1.0, 1.0), (1.2, 0), (2.4, 0))
        i = _k(t, (0, 0), (1.2, 0), (1.5, 1.0), (2.2, 1.0), (2.4, 0))
        p.rot("pinza_d", rx=(35.0 + 6.0 * math.sin(TAU * 4 * t)) * d, ry=-20.0 * d)
        p.rot("pinza_i", rx=(35.0 + 6.0 * math.sin(TAU * 4 * t)) * i, ry=20.0 * i)
        return p
    return largo, pose_en


def ambiente_echarse(L):
    """Los grandes (toro, bufalo, hipopotamo, Iskarum, dromedario, cervatillo, cabra): echados descansando,
    respirando, rumiando y mirando alrededor."""
    largo = 4.0

    def pose_en(t):
        p = L.pose()
        _echar(L, p)
        p.pos("cuerpo", y=0.15 * math.sin(TAU * t / 2.0))
        mira = 14.0 * math.sin(TAU * t / largo)
        if "cuello" in L.huesos:
            p.rot("cuello", rx=-8.0)
        p.rot("cabeza", ry=mira, rx=2.0 * math.sin(TAU * 3 * t / largo))
        p.rot("cola", rx=-25.0, rz=8.0 * math.sin(TAU * t / 2.0))
        return p
    return largo, pose_en


def ambiente_bostezo(L):
    """Hipopotamo: bostezo enorme con la cabeza bien alzada."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        p.rot("cabeza", rx=_k(t, (0, 0), (0.8, 40.0), (2.0, 42.0), (3.0, 0)))
        p.rot("cuerpo", rx=_k(t, (0, 0), (0.8, 3.0), (2.0, 3.0), (3.0, 0)))
        return _montar_patas(L, p)
    return largo, pose_en


def ambiente_moldear_bola(L):
    """Escarabajo sagrado: con la cabeza abajo palmea la bola con las patas de atras para redondearla."""
    largo = 1.6

    def pose_en(t):
        p = L.pose()
        p.rot("cuerpo", rx=-7.0)
        p.pos("cuerpo", y=0.3)
        for lado, s, f in (("d", 1, 0.0), ("i", -1, 0.5)):
            a = math.sin(TAU * (2 * t / largo + f))
            p.rot(f"pata_3{lado}", ry=-s * (18.0 + 10.0 * a), rz=s * (14.0 + 8.0 * a))
        return p
    return largo, pose_en


def ambiente_rama(L):
    """Ramita: quieta como rama, se mece con el viento."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        p.rot("cuerpo", rz=2.5 * math.sin(TAU * t / largo), ry=2.0 * math.sin(TAU * 2 * t / largo))
        p.pos("cuerpo", x=0.3 * math.sin(TAU * t / largo))
        p.rot("cabeza", rz=-2.0 * math.sin(TAU * t / largo))
        return p
    return largo, pose_en


def ambiente_cola_escorpion(L):
    """Escorpion: mece la cola alzada y chasquea las pinzas."""
    largo = 2.0

    def pose_en(t):
        p = L.pose()
        _onda(p, ("cola1", "cola2", "cola3", "cola4"), t / largo, 6.0, 0.7)
        p.rot("cola4", rx=-6.0 * max(0.0, math.sin(TAU * 2 * t / largo)))
        chasquido = 8.0 * max(0.0, math.sin(TAU * 4 * t / largo))
        p.rot("pinza_d", ry=chasquido)
        p.rot("pinza_i", ry=-chasquido)
        return p
    return largo, pose_en


def ambiente_soplar(L):
    """Ballenato: asoma de la arena, sopla arena por el lomo y se vuelve a acomodar."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        p.pos("raiz", y=_k(t, (0, 0), (0.8, 1.5), (1.2, 2.0), (2.0, 1.5), (3.0, 0)))
        p.rot("raiz", rx=_k(t, (0, 0), (0.8, -5.0), (2.0, -4.0), (3.0, 0)))
        p.pos("cuerpo", y=1.0 + _k(t, (0, 0), (1.0, 0), (1.15, 0.5), (1.4, 0), (3.0, 0)))
        p.rot("cola", rx=6.0 * math.sin(TAU * t / 1.5))
        return p
    return largo, pose_en


def ambiente_esconderse(L):
    """Garrapata: se aplasta contra el piso con las patas recogidas, y de vez en cuando mueve una."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        p.pos("cuerpo", y=-0.4)
        for k in (1, 2, 3):
            p.rot(f"pata_{k}d", rz=12.0)
            p.rot(f"pata_{k}i", rz=-12.0)
        p.rot("pata_1d", ry=10.0 * max(0.0, math.sin(TAU * 2 * t / largo)))
        return p
    return largo, pose_en


def ambiente_frotar_patas(L):
    """Escarabajo de brasa: se frota las patas de adelante."""
    largo = 1.6

    def pose_en(t):
        p = L.pose()
        a = math.sin(TAU * 3 * t / largo)
        p.rot("pata_1d", rz=18.0, ry=10.0 * a)
        p.rot("pata_1i", rz=-18.0, ry=10.0 * a)
        p.rot("cabeza", rx=-4.0)
        return p
    return largo, pose_en


def ambiente_flotar(L):
    """Cria de Moruvahn: reposa meciendo la cola despacio y cabeceando, como en el agua."""
    largo = 3.0

    def pose_en(t):
        p = L.pose()
        _onda(p, ("cola1", "cola2", "cola3"), t / largo, 8.0, 0.9)
        p.rot("cabeza", rx=3.0 * math.sin(TAU * t / 1.5), ry=6.0 * math.sin(TAU * t / largo))
        p.pos("cuerpo", y=0.15 * math.sin(TAU * t / 1.5))
        return p
    return largo, pose_en


def ambiente_ladear(L):
    """Cuervo y halcon: ladean la cabeza con curiosidad a un lado y al otro."""
    largo = 2.4

    def pose_en(t):
        p = L.pose()
        p.rot("cabeza", rz=_k(t, (0, 0), (0.3, 25.0), (0.9, 25.0), (1.2, -20.0), (1.9, -20.0), (2.4, 0)),
              ry=_k(t, (0, 0), (0.3, 10.0), (1.2, -10.0), (2.4, 0)))
        return p
    return largo, pose_en


def ambiente_juguetear(L):
    """Cervatillo (el que nunca ataca): brinca juguetón de un lado a otro sacudiendo la cabeza."""
    largo = 1.6

    def pose_en(t):
        p = L.pose()
        u = (t / 0.8) % 1.0
        brinco = math.sin(math.pi * min(1.0, u / 0.6)) if u < 0.6 else 0.0
        p.pos("raiz", y=3.0 * brinco)
        p.rot("raiz", ry=20.0 * math.sin(TAU * t / largo))
        p.rot("cabeza", rz=12.0 * math.sin(TAU * 2 * t / largo))
        p.rot("cola", rx=-20.0 * brinco)
        for h in ("pata_dd", "pata_di"):
            p.rot(h, 15.0 * brinco)
        for h in ("pata_td", "pata_ti"):
            p.rot(h, -15.0 * brinco)
        return p
    return largo, pose_en


AMBIENTE = {
    "pastar": (ambiente_pastar, ["toro_arena", "bufalo_terracota", "cabra_escarcha", "cervatillo_musgo", "dromedario",
                                 "hipopotamo"]),
    "arrancar_con_trompa": (ambiente_trompa, ["cria_iskarum"]),
    "mordisquear": (ambiente_mordisquear, ["liebre_dorada", "marmota"]),
    "beber_lamiendo": (ambiente_beber_lamiendo, ["lobo_fuego", "chacal_ceniza", "fenec", "gato_thza"]),
    "beber_aves": (ambiente_beber_ave, ["pato_estanque", "ibis", "flamenco", "cuervo_negro", "buitre", "halcon_cobre",
                                        "aguila_gris"]),
    "lamer_cria": (ambiente_lamer_cria, ["lobo_fuego", "chacal_ceniza", "fenec", "gato_thza"]),
    "sentarse_manada": (ambiente_sentarse, ["lobo_fuego", "chacal_ceniza"]),
    "aullar": (ambiente_aullar, ["lobo_fuego", "chacal_ceniza"]),
    "acicalarse_gato": (ambiente_acicalarse_gato, ["gato_thza"]),
    "acicalarse_aves": (ambiente_acicalarse_ave, ["pato_estanque", "halcon_cobre", "aguila_gris", "cuervo_negro",
                                                  "buitre", "ibis", "flamenco"]),
    "despiojar": (ambiente_despiojar, ["babuino"]),
    "una_pata": (ambiente_una_pata, ["flamenco", "ibis"]),
    "alas_al_sol": (ambiente_alas_al_sol, ["buitre", "aguila_gris"]),
    "boca_abierta": (ambiente_boca_abierta, ["cocodrilo_luz"]),
    "lagartijeo": (ambiente_lagartijeo, ["lagarto_roca", "lagartija_blanca", "salamandra_ceniza"]),
    "silbar": (ambiente_silbar, ["marmota"]),
    "colgarse": (ambiente_colgarse, ["murcielago_mura"]),
    "enroscarse": (ambiente_enroscarse, ["serpiente_rio_seco", "cria_varkhum"]),
    "limpiarse_ojos": (ambiente_limpiarse_ojos, ["cangrejo"]),
    "echarse": (ambiente_echarse, ["toro_arena", "bufalo_terracota", "hipopotamo", "cria_iskarum", "dromedario",
                                   "cervatillo_musgo", "cabra_escarcha"]),
    "bostezo": (ambiente_bostezo, ["hipopotamo"]),
    "moldear_bola": (ambiente_moldear_bola, ["escarabajo_sagrado"]),
    "mecerse_rama": (ambiente_rama, ["ramita"]),
    "cola_escorpion": (ambiente_cola_escorpion, ["escorpion_luz"]),
    "soplar_arena": (ambiente_soplar, ["ballenato_duna"]),
    "esconderse": (ambiente_esconderse, ["garrapata_sal"]),
    "frotar_patas": (ambiente_frotar_patas, ["escarabajo_brasa"]),
    "flotar_quieto": (ambiente_flotar, ["cria_moruvahn"]),
    "ladear_cabeza": (ambiente_ladear, ["cuervo_negro", "halcon_cobre"]),
    "juguetear": (ambiente_juguetear, ["cervatillo_musgo"]),
}

ANIMACIONES = {"caminar": CAMINAR, "correr": CORRER, "atacar": ATACAR, "ambiente": AMBIENTE}
EN_BUCLE = {"caminar": True, "correr": True, "atacar": False, "ambiente": True}
DESDE_ARRIBA = ("reptiles", "serpientes", "cangrejo", "insectos", "aracnidos", "escurridizos", "carrera_baja",
                "patitas_insectos", "patitas_aracnidos", "patitas_cangrejo", "ramita_tiesa", "lanzarse", "emboscada",
                "pegarse", "escupir", "explotar", "enroscarse", "limpiarse_ojos", "moldear_bola", "cola_escorpion",
                "esconderse", "frotar_patas", "flotar_quieto", "lagartijeo", "mecerse_rama")   # la segunda vista, desde arriba


# ====================================================================== revisar

def _cajas(L):
    """{hueso de GeckoLib: [(giro del cubo o None, desde, hasta)]}: los cubos de cada hueso en px del modelo."""
    rutas = set(L.a.m.pivotes)
    for c in L.a.m.cubos:
        partes = c.hueso.split("/")
        rutas.update("/".join(partes[:i + 1]) for i in range(len(partes)))
    nombre = geckolib.nombres_de_huesos(rutas)
    cajas = {}
    for c in L.a.m.cubos:
        giro = geckolib._giro_en(tuple(c.origen), tuple(math.radians(r) for r in c.rot)) if c.rot else None
        cajas.setdefault(nombre[c.hueso], []).append((giro, tuple(c.desde), tuple(c.hasta)))
    return cajas


def _esquinas(giro, f, h):
    pts = [(x, y, z) for x in (f[0], h[0]) for y in (f[1], h[1]) for z in (f[2], h[2])]
    return [giro(p) for p in pts] if giro else pts


def _fuera(p, cajas):
    """Lo que el punto p (px del modelo) queda fuera del cubo mas cercano de la lista (0 si esta adentro)."""
    mejor = 1e9
    for giro, f, h in cajas:
        q = animar._inversa(giro)(p) if giro else p
        d = math.sqrt(sum(max(f[i] - q[i], 0.0, q[i] - h[i]) ** 2 for i in range(3)))
        mejor = min(mejor, d)
    return mejor


def revisar_uniones(L, cuadros, tolerancia=0.3, cada=1):
    """Que ninguna pieza se despegue de aquella a la que va pegada (su padre, o el cuerpo si cuelga de la raiz):
    las esquinas de la pieza que en reposo quedan dentro de la otra deben seguir dentro en cada cuadro.
    Devuelve [(hueso, pegado a, cuanto se separa en px, en que segundo)] de los que fallan (en reposo: t = None)."""
    cajas = _cajas(L)
    fallas = []
    for b in cajas:
        padre = L.rig.padre.get(b)
        if b == "cuerpo" or padre is None or (padre == "raiz" and b in ("bola",)) or b.startswith("s0"):
            continue
        a = padre if padre in cajas else "cuerpo"
        if a not in cajas or a == b:
            continue
        reposo = L.rig.transformaciones({})

        def pegadas(x, y):
            """Las esquinas de x que en reposo quedan dentro de y."""
            pts = [p for giro, f, h in cajas[x] for p in _esquinas(giro, f, h)]
            dentro = [p for p in pts if _fuera(animar._inversa(reposo[y])(reposo[x](p)), cajas[y]) <= 1e-3]
            if dentro:                                   # la union es la bisagra: las esquinas cerca del pivote
                piv = L.rig.pivote[b]
                cerca = min(math.dist(q, piv) for q in dentro)
                dentro = [q for q in dentro if math.dist(q, piv) <= cerca + 1.5]
            return dentro, pts
        dentro, esquinas = pegadas(b, a)
        x, y = b, a
        if not dentro:                                   # o al reves: el cuello que se mete en la cabeza
            dentro, _ = pegadas(a, b)
            x, y = a, b
        if not dentro:
            d = min(_fuera(animar._inversa(reposo[a])(reposo[b](p)), cajas[a]) for p in esquinas)
            fallas.append((b, a, round(d, 2), None))
            continue
        peor, cuando = 0.0, None
        for t, pose in cuadros[::cada]:
            T = L.rig.transformaciones(pose)
            inv = animar._inversa(T[y])
            d = max(_fuera(inv(T[x](p)), cajas[y]) for p in dentro)
            if d > peor:
                peor, cuando = d, t
        if peor > tolerancia:
            fallas.append((b, a, round(peor, 2), cuando))
    return fallas


def gif(listos, nombre, poses, ruta, alto=None, cada=1, vistas=((35, 12), (90, 4)), bucle=True):
    """Un GIF de todos los bichos del grupo lado a lado (de 3/4 y de lado), en caminadora."""
    alto = alto or (300 if len(listos) <= 2 else 230)
    columnas = []
    for L, (largo, pose_en) in zip(listos, poses):
        datos, cuadros = animar.hornear(L.rig, nombre, largo, pose_en, bucle=bucle)
        rev = animar.revisar(L.rig, cuadros, bucle)
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
        print("  ->", gif(listos, nombre, [f(L) for L in listos], os.path.join(SALIDA, f"{nombre}_{g}.gif"), vistas=vistas,
                          bucle=EN_BUCLE.get(nombre, True)))


if __name__ == "__main__":
    main(sys.argv[1:])
