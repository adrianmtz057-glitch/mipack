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


CAMINAR = {
    "pesados": (caminar_pesado, ["hipopotamo", "cria_iskarum"]),
}
ANIMACIONES = {"caminar": CAMINAR}


# ====================================================================== revisar

def gif(listos, nombre, poses, ruta, alto=300, cada=1):
    """Un GIF de todos los bichos del grupo lado a lado (de 3/4 y de lado), en caminadora."""
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
        radio = float(np.max(hi - lo)) * 0.66
        cuadros_img = []
        for _t, pose in cuadros[::cada]:
            caras = geckolib.caras_para_vista(L.rig.quads(pose))
            fila = []
            for yaw, pitch in ((35, 12), (90, 4)):
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
        print("  ->", gif(listos, nombre, [f(L) for L in listos], os.path.join(SALIDA, f"{nombre}_{g}.gif")))


if __name__ == "__main__":
    main(sys.argv[1:])
