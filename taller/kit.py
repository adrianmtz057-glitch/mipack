"""
Kit para modelar personajes A MANO (un archivo por personaje en taller/personajes/<id>.py).

La idea: mezclar 3D y 2D como los modelos de la comunidad.
  - cajas 3D para el volumen (cuerpo, capas de ropa, coronas, botas)
  - PLANOS (grosor 0) con silueta recortada para lo fino: mechones, volados, encaje, llamas,
    esquirlas de hielo, plumas, flecos, bordes de capa
  - textura dibujada A MANO como pixel art en texto (sprite), con mas resolucion donde importa
    (dens=2 o 3: la cara de una cabeza de 8 px pasa a tener 16x16 o 24x24 pixeles)

Ejes: frente = -Z, derecha del personaje = +X, pies en y = 0. Unidades en px (16 px = 1 bloque).
Huesos: Head, Body, RightArm, LeftArm, RightLeg, LeftLeg (palabras clave de Figura).
Grupos: "Hueso/subgrupo" (ej. "Head/pelo"), el subgrupo es solo para ordenar.

Ejemplo minimo (ver taller/personajes/_ejemplo.py):

    from taller.kit import Personaje, sprite, dibujo, degradado
    p = Personaje("meron")                       # player de 32 px
    p.cuerpo(cabeza=..., torso=..., brazo=..., pierna=...)   # pintores
    p.caja("Head/corona", "aro", (-4.5, 31.5, -4.5), (4.5, 33, 4.5), metal("#E3B04B"))
    p.plano("Head/pelo", "mechon", (-2, 28, -4.6), (0, 32, -4.6), sprite(...), rot=(0, 0, 10), piv=(-1, 32, -4.6))
    modelo = p.m
"""

import math
import os
import textwrap

from .modelo import Modelo
from .pintura import Paleta
from .textura import TRANSPARENTE, hex_a_rgba

# ============================================================================ pintura a mano


def dibujo(texto):
    """Convierte un bloque de texto en filas de pixel art (quita sangria y lineas vacias)."""
    filas = [f.rstrip("\n") for f in textwrap.dedent(texto).splitlines()]
    filas = [f.strip() for f in filas if f.strip()]
    ancho = max(len(f) for f in filas)
    return [f.ljust(ancho, ".") for f in filas]


def sprite(caras, paleta, base=None, espejo_izq=False):
    """Pintor de pixel art dibujado a mano.

    caras:  {"north": filas, "south": filas, "east": ..., "west": ..., "up": ..., "down": ...,
             "lados": filas (para las 4 caras laterales), "todas": filas}
            filas = lista de strings (usa dibujo()). Se estira al tamano real de la cara (vecino mas cercano),
            asi que conviene dibujar con el MISMO tamano en texeles que la cara (px * dens).
    paleta: {"A": "#RRGGBB", ...}. "." = transparente. Un caracter que no este en la paleta usa 'base'.
    base:   pintor para lo que no esta dibujado (o None = transparente).
    espejo_izq: en piezas de par() del lado izquierdo, refleja el dibujo en horizontal.
    """
    pal = {k: hex_a_rgba(v) for k, v in paleta.items()}

    def p(t):
        g = caras.get(t.cara)
        if g is None and t.cara in ("north", "south", "east", "west"):
            g = caras.get("lados")
        if g is None:
            g = caras.get("todas")
        if g is None:
            return base(t) if base else TRANSPARENTE
        filas, cols = len(g), len(g[0])
        i = t.i
        if espejo_izq and getattr(t, "lado", 1) < 0:
            i = t.tw - 1 - i
        r = min(filas - 1, t.j * filas // max(1, t.th))
        c = min(cols - 1, i * cols // max(1, t.tw))
        ch = g[r][c]
        if ch == ".":
            return TRANSPARENTE
        if ch in pal:
            return pal[ch]
        return base(t) if base else TRANSPARENTE
    return p


def degradado(colores, contorno=None, brillo=None, arriba=None):
    """Degradado vertical a mano: colores de arriba a abajo (lista de hex), con fila de brillo arriba y
    contorno abajo opcionales. Las caras de arriba usan 'arriba' (o el primer color)."""
    cs = [hex_a_rgba(c) for c in colores]
    co = hex_a_rgba(contorno) if contorno else None
    br = hex_a_rgba(brillo) if brillo else None
    ar = hex_a_rgba(arriba) if arriba else cs[0]

    def p(t):
        if t.cara == "up":
            return ar
        if t.cara == "down":
            return cs[-1]
        if br and t.j == 0 and t.th >= 3:
            return br
        if co and t.fila_abajo == 0 and t.th >= 3:
            return co
        k = t.j / max(1, t.th - 1)
        return cs[min(len(cs) - 1, int(k * len(cs)))]
    return p


def solido(color):
    c = hex_a_rgba(color)
    return lambda t: c


def mezclar_pintores(principal, *otros):
    """Usa 'principal' y, donde devuelva transparente, el siguiente pintor."""
    def p(t):
        c = principal(t)
        if c[3] == 0:
            for o in otros:
                c = o(t)
                if c[3]:
                    return c
        return c
    return p


def tonos(color):
    """5 tonos de un color: {'o': contorno, 's2', 's': sombra, 'b': base, 'l': luz, 'h': brillo} en hex."""
    P = Paleta(color)
    a_hex = "#%02X%02X%02X"
    return {k: a_hex % tuple(getattr(P, k)[:3]) for k in ("o", "s2", "s", "b", "l", "h")}


# ============================================================================ personaje


class Personaje:
    """Esqueleto de player con medidas ajustables y atajos para agregar piezas."""

    def __init__(self, nombre, altura=32, cabeza=8, torso=(8, 12, 4), brazo=(4, 4), pierna=(4, 4)):
        self.nombre = nombre
        self.m = Modelo(nombre)
        hc = cabeza
        tw, th, td = torso
        aw, ad = brazo
        lw, ld = pierna
        lh = altura - hc - th
        self.cabeza, self.tw, self.th, self.td, self.aw, self.ad, self.lw, self.ld = hc, tw, th, td, aw, ad, lw, ld
        self.lh = lh                          # alto de las piernas (cintura)
        self.cuello = lh + th
        self.tope = self.cuello + hc          # arriba de la cabeza
        self.altura = altura
        self.m.pivotes = {
            "Head": (0, self.cuello, 0), "Body": (0, self.cuello, 0),
            "RightArm": (tw / 2 + aw / 2, self.cuello - 2, 0), "LeftArm": (-(tw / 2 + aw / 2), self.cuello - 2, 0),
            "RightLeg": (lw / 2, lh, 0), "LeftLeg": (-lw / 2, lh, 0),
        }

    # ------------------------------------------------------------------ medidas utiles
    @property
    def caja_cabeza(self):
        h = self.cabeza / 2
        return (-h, self.cuello, -h), (h, self.tope, h)

    @property
    def caja_torso(self):
        return (-self.tw / 2, self.lh, -self.td / 2), (self.tw / 2, self.cuello, self.td / 2)

    def caja_brazo(self, lado=1):
        x1, x2 = self.tw / 2, self.tw / 2 + self.aw
        if lado < 0:
            x1, x2 = -x2, -x1
        return (x1, self.cuello - self.th, -self.ad / 2), (x2, self.cuello, self.ad / 2)

    def caja_pierna(self, lado=1):
        x1, x2 = (0, self.lw) if lado > 0 else (-self.lw, 0)
        return (x1, 0, -self.ld / 2), (x2, self.lh, self.ld / 2)

    # ------------------------------------------------------------------ piezas
    def caja(self, grupo, nombre, desde, hasta, pintor, rot=None, piv=None, dens=1, caras=None):
        return self.m.cubo(grupo, nombre, desde, hasta, pintor, rot, piv, caras=caras, dens=dens)

    def par(self, grupo, nombre, desde, hasta, pintor, rot=None, piv=None, dens=1, caras=None):
        """Pieza del lado DERECHO (+X, hueso Right...) que se copia en espejo a la izquierda."""
        self.m.par(grupo, nombre, desde, hasta, pintor, rot, piv, caras=caras, dens=dens)

    def plano(self, grupo, nombre, desde, hasta, pintor, rot=None, piv=None, dens=1):
        """Plano 2D: 'desde' y 'hasta' iguales en un eje (grosor 0). Se ven sus dos caras.
        Ideal con sprite() y '.' transparentes para siluetas recortadas."""
        return self.m.cubo(grupo, nombre, desde, hasta, pintor, rot, piv, dens=dens)

    def plano_par(self, grupo, nombre, desde, hasta, pintor, rot=None, piv=None, dens=1):
        self.m.par(grupo, nombre, desde, hasta, pintor, rot, piv, dens=dens)

    def cadena(self, grupo, nombre, base, pasos, largo, grosor, pintor, achica=0.85, dens=1):
        """Segmentos encadenados que se curvan (cuernos, colas, mechones largos, capas que ondean).
        pasos = [(giro_z, giro_x), ...] en grados, acumulados segmento a segmento."""
        x, y, z = base
        az = ax = 0.0
        for k, (dz, dx) in enumerate(pasos):
            az += dz
            ax += dx
            w = grosor * (achica ** k)
            self.m.cubo(grupo, f"{nombre}{k}", (x - w / 2, y, z - w / 2), (x + w / 2, y + largo, z + w / 2), pintor,
                        rot=(ax, 0, az), origen=(x, y, z), dens=dens)
            rz, rx = math.radians(az), math.radians(ax)
            x += -math.sin(rz) * largo * 0.95
            y += math.cos(rz) * math.cos(rx) * largo * 0.95
            z += math.sin(rx) * largo * 0.95

    def cuerpo(self, cabeza, torso, brazo, pierna, mano=None, dens_cabeza=2, dens=1):
        """Las 6 partes del cuerpo. 'mano' (opcional) pinta los 3-4 px de abajo del brazo."""
        d, h = self.caja_cabeza
        self.caja("Head/cabeza", "cabeza", d, h, cabeza, dens=dens_cabeza)
        d, h = self.caja_torso
        self.caja("Body/torso", "torso", d, h, torso, dens=dens)
        for lado in (1, -1):
            hueso = "RightArm" if lado > 0 else "LeftArm"
            d, h = self.caja_brazo(lado)
            if mano:
                self.caja(f"{hueso}/brazo", "brazo", (d[0], d[1] + 4, d[2]), h, brazo, dens=dens)
                self.caja(f"{hueso}/brazo", "mano", d, (h[0], d[1] + 4, h[2]), mano, dens=dens)
            else:
                self.caja(f"{hueso}/brazo", "brazo", d, h, brazo, dens=dens)
            d, h = self.caja_pierna(lado)
            self.caja(("RightLeg" if lado > 0 else "LeftLeg") + "/pierna", "pierna", d, h, pierna, dens=dens)

    # ------------------------------------------------------------------ salida
    def guardar(self, carpeta, vista=True):
        """Escribe <carpeta>/<nombre>.bbmodel y, si se puede, la vista previa. Devuelve (ruta, lienzo, uvs)."""
        from . import vista as vista_mod
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, f"{self.nombre}.bbmodel")
        lienzo, uvs, _ = self.m.guardar(ruta)
        if vista:
            vista_mod.guardar_vista(self.m, lienzo, uvs, ruta[:-8] + "_vista.png", alto_px=640)
            vista_mod.guardar_vista(self.m, lienzo, uvs, ruta[:-8] + "_cara.png", alto_px=420,
                                    centro=(0, self.cuello + self.cabeza / 2, 0), radio=self.cabeza * 0.9,
                                    vistas=(("frente", 0, 5), ("3/4", 35, 10)))
        return ruta, lienzo, uvs


class Objeto:
    """Accesorio aparte (cetro, libro...). Hueso 'Item' con el agarre en (0, 0, 0)."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.m = Modelo(nombre)
        self.m.pivotes = {"Item": (0, 0, 0)}

    def caja(self, nombre, desde, hasta, pintor, rot=None, piv=None, dens=1, grupo="Item"):
        return self.m.cubo(grupo, nombre, desde, hasta, pintor, rot, piv, dens=dens)

    def plano(self, nombre, desde, hasta, pintor, rot=None, piv=None, dens=1, grupo="Item"):
        return self.m.cubo(grupo, nombre, desde, hasta, pintor, rot, piv, dens=dens)

    def guardar(self, carpeta, vista=True):
        from . import vista as vista_mod
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, f"{self.nombre}.bbmodel")
        lienzo, uvs, _ = self.m.guardar(ruta)
        if vista:
            vista_mod.guardar_vista(self.m, lienzo, uvs, ruta[:-8] + "_vista.png", alto_px=420)
        return ruta, lienzo, uvs
