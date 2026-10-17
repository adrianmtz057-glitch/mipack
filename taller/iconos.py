"""
Los iconos de los objetos (16x16, pixel art propio, nada recoloreado de Minecraft): cada uno se dibuja con formas
sencillas (lineas, elipses, poligonos) y al final se le pone el volumen (orilla de arriba-izquierda clara, la de
abajo-derecha oscura) y el contorno oscuro, como los objetos de Minecraft.
Uso: python -m taller.iconos  ->  mod/src/main/resources/assets/mipack/textures/item/<id>.png y
salida/objetos/iconos.png (la hoja para revisar, en grande)
"""

import math
import os
import sys

from PIL import Image, ImageDraw

from .luz import paso
from .textura import hex_a_rgba as hex_

RAIZ = os.path.join(os.path.dirname(__file__), "..")
TEXTURAS = os.path.join(RAIZ, "mod", "src", "main", "resources", "assets", "mipack", "textures")
SALIDA = os.path.join(RAIZ, "salida", "objetos")


class Icono:
    def __init__(self, lado=16):
        self.n = lado
        self.px = [[None] * lado for _ in range(lado)]
        self.fijo = set()                              # pixeles que el volumen no toca (brillos, detalles)

    def p(self, x, y, c, fijo=False):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.n and 0 <= y < self.n:
            self.px[y][x] = hex_(c) if isinstance(c, str) else c
            if fijo:
                self.fijo.add((x, y))

    def rect(self, x0, y0, x1, y1, c, fijo=False):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.p(x, y, c, fijo)

    def linea(self, x0, y0, x1, y1, c, grosor=1, fijo=False):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if grosor <= 1:
                self.p(x, y, c, fijo)
            else:
                r = (grosor - 1) / 2
                for dy in range(-math.ceil(r), math.ceil(r) + 1):
                    for dx in range(-math.ceil(r), math.ceil(r) + 1):
                        if dx * dx + dy * dy <= r * r + 0.3:
                            self.p(x + dx, y + dy, c, fijo)

    def elipse(self, cx, cy, rx, ry, c, fijo=False):
        for y in range(self.n):
            for x in range(self.n):
                if ((x - cx) / max(rx, 0.01)) ** 2 + ((y - cy) / max(ry, 0.01)) ** 2 <= 1.0:
                    self.p(x, y, c, fijo)

    def poli(self, puntos, c, fijo=False):
        im = Image.new("L", (self.n, self.n), 0)
        ImageDraw.Draw(im).polygon([(x, y) for x, y in puntos], fill=255)
        for y in range(self.n):
            for x in range(self.n):
                if im.getpixel((x, y)):
                    self.p(x, y, c, fijo)

    def lleno(self, x, y):
        return 0 <= x < self.n and 0 <= y < self.n and self.px[y][x] is not None

    def terminar(self, volumen=True, contorno=True, oscuro=3):
        n = self.n
        base = [fila[:] for fila in self.px]
        if volumen:
            for y in range(n):
                for x in range(n):
                    c = base[y][x]
                    if c is None or (x, y) in self.fijo:
                        continue
                    arriba = not (0 <= y - 1 < n and base[y - 1][x]) or not (0 <= x - 1 < n and base[y][x - 1])
                    abajo = not (y + 1 < n and base[y + 1][x]) or not (x + 1 < n and base[y][x + 1])
                    if abajo:
                        self.px[y][x] = paso(c, -1)
                    elif arriba:
                        self.px[y][x] = paso(c, 1)
        if contorno:
            lleno = [[base[y][x] is not None for x in range(n)] for y in range(n)]
            for y in range(n):
                for x in range(n):
                    if lleno[y][x]:
                        continue
                    vecinos = [base[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                               if 0 <= x + dx < n and 0 <= y + dy < n and lleno[y + dy][x + dx]]
                    if vecinos:
                        self.px[y][x] = paso(vecinos[0], -oscuro)
        return self

    def imagen(self):
        im = Image.new("RGBA", (self.n, self.n), (0, 0, 0, 0))
        for y in range(self.n):
            for x in range(self.n):
                if self.px[y][x] is not None:
                    im.putpixel((x, y), tuple(self.px[y][x]))
        return im


ICONOS = {}


def icono(nombre, carpeta="item"):
    def reg(f):
        ICONOS[nombre] = (f, carpeta)
        return f
    return reg


# ====================================================================== materiales de los animales

@icono("colmillo")
def _colmillo(i):
    i.poli([(11, 2), (13, 3), (12, 6), (9, 9), (6, 12), (3, 14), (4, 12), (7, 8), (10, 4)], "#EDE3C8")
    i.poli([(11, 2), (13, 3), (12.5, 5), (10.5, 4)], "#9C7A55")
    i.linea(11, 5, 6, 11, "#FFF8E6", fijo=True)
    return i.terminar()


@icono("aguijon")
def _aguijon(i):
    i.elipse(10, 4, 2.6, 2.2, "#7A4A22")
    i.linea(9, 6, 5, 10, "#E8A93A", grosor=3)
    i.linea(5, 10, 4, 13, "#E8A93A", grosor=2)
    i.linea(4, 13, 6, 14, "#3A2414", grosor=1)
    i.p(9, 3, "#A7703C", True)
    i.linea(8, 6, 5, 9, "#FFD27A", fijo=True)
    return i.terminar()


@icono("escamas")
def _escamas(i):
    for cx, cy in ((5, 5), (10, 5), (7.5, 9), (12.5, 9), (4.5, 12), (10, 12.5)):
        i.elipse(cx, cy, 2.6, 2.2, "#2F6A4A")
        i.elipse(cx - 0.4, cy - 0.5, 1.4, 1.1, "#4E9466")
    for x, y in ((5, 5), (12, 9), (10, 12)):
        i.p(x, y, "#7CF0D0", True)
    return i.terminar()


@icono("cuerno_piedra")
def _cuerno(i):
    i.poli([(3, 13), (6, 13), (8, 10), (11, 7), (13, 3), (12, 2), (9, 5), (5, 9)], "#8C8A86")
    i.poli([(3, 13), (6, 13), (6.5, 11), (4, 11)], "#6B5440")
    i.linea(8, 9, 10, 8, "#5E5C59", fijo=True)
    i.linea(6, 11, 7, 10, "#5E5C59", fijo=True)
    i.linea(11, 5, 12, 3, "#B3B1AC", fijo=True)
    return i.terminar()


@icono("caparazon")
def _caparazon(i):
    i.elipse(7.5, 8, 5.5, 6.2, "#2B6F77")
    i.linea(7.5, 2.5, 7.5, 13.5, "#174147")
    i.elipse(5.5, 5.5, 1.3, 2, "#56A3A8", fijo=True)
    i.elipse(10, 6, 0.8, 1.4, "#3E8E95", fijo=True)
    return i.terminar()


@icono("cola_lagarto")
def _cola(i):
    pts = [(3, 4), (6, 4.5), (9, 6), (11, 8.5), (12, 11), (11, 13), (9, 13.5)]
    for k in range(len(pts) - 1):
        g = max(1, 4 - k * 0.6)
        i.linea(*pts[k], *pts[k + 1], "#9C6B4A", grosor=g)
    for k, (x, y) in enumerate(pts[:-2]):
        i.p(x + 0.5, y + 0.5, "#6E4A32", True)
    i.rect(2, 3, 3, 5, "#C25A4A")
    return i.terminar()


@icono("branquia")
def _branquia(i):
    i.linea(4, 13, 9, 4, "#C2405A", grosor=2)
    for k, (x, y) in enumerate(((5.5, 11), (6.5, 9), (7.5, 7), (8.5, 5))):
        i.linea(x, y, x - 3, y - 1.5 + (k % 2) * 0.4, "#F07A92")
        i.linea(x, y, x + 3, y - 0.5, "#F07A92")
    i.p(9, 3, "#FFB0C0", True)
    return i.terminar()


@icono("ceniza")
def _ceniza(i):
    i.poli([(2, 13), (14, 13), (12, 10), (9, 7), (6, 8), (4, 10)], "#6E6A68")
    i.poli([(6, 10), (10, 9), (11, 11), (7, 12)], "#8C8885")
    for x, y in ((5, 11), (9, 10), (11, 12), (7, 9)):
        i.p(x, y, "#3E3B3A", True)
    return i.terminar()


@icono("brasa")
def _brasa(i):
    i.poli([(3, 10), (5, 5), (9, 3), (13, 6), (12, 11), (8, 13), (4, 12)], "#3A2420")
    i.linea(5, 9, 8, 6, "#FF7A1E", fijo=True)
    i.linea(8, 6, 11, 8, "#FFB43A", fijo=True)
    i.linea(7, 11, 10, 9, "#E8401E", fijo=True)
    i.p(8, 7, "#FFE07A", True)
    i.p(10, 8, "#FFE07A", True)
    return i.terminar()


def _pluma(i, base, raquis, brillo):
    i.poli([(13, 2), (14, 4), (10, 10), (6, 13), (4, 12), (6, 8), (10, 4)], base)
    i.linea(13, 3, 3, 14, raquis)
    i.linea(11, 4, 7, 8, brillo, fijo=True)
    i.p(9, 9, paso(hex_(base), -1), True)
    i.p(7, 11, paso(hex_(base), -1), True)


@icono("pluma_negra")
def _pluma_negra(i):
    _pluma(i, "#2A2234", "#120E18", "#5E4A7A")
    return i.terminar()


@icono("mura")
def _mura(i):
    i.elipse(8, 9, 5, 4.5, "#3A1446")
    i.elipse(6, 6, 2.5, 2.2, "#3A1446")
    i.elipse(11, 6.5, 2, 2, "#3A1446")
    i.elipse(7.5, 8.5, 2, 1.6, "#8A2AA0", fijo=True)
    i.p(7, 8, "#FF6AF0", True)
    i.p(11, 6, "#FF6AF0", True)
    i.p(5, 11, "#C24AD8", True)
    return i.terminar()


@icono("sal")
def _sal(i):
    i.poli([(2, 13), (14, 13), (11, 9), (8, 6), (5, 9)], "#E8E6E0")
    for (x, y) in ((6, 9), (9, 8), (11, 11), (5, 12), (8, 11)):
        i.p(x, y, "#FFFFFF", True)
    i.rect(8, 5, 8, 6, "#F4F2EC")
    i.p(10, 6, "#D6D2C8")
    return i.terminar()


@icono("semilla_musgo")
def _semilla(i):
    i.elipse(8, 9, 3.5, 4.5, "#6E9A3E")
    i.elipse(7, 8, 1.4, 2, "#9CC25A", fijo=True)
    i.linea(8, 4.5, 10, 2, "#557E2E")
    i.elipse(11, 2.5, 1.5, 1, "#88B44A")
    i.p(9, 11, "#3E5E22", True)
    return i.terminar()


@icono("grasa")
def _grasa(i):
    i.poli([(3, 11), (4, 6), (8, 4), (12, 5), (13, 10), (9, 13), (5, 13)], "#EADBA8")
    i.elipse(7, 7, 2, 1.4, "#FFF4D0", fijo=True)
    i.linea(6, 11, 11, 10, "#C9B480", fijo=True)
    return i.terminar()


@icono("pelaje_grueso")
def _pelaje(i):
    i.poli([(2, 10), (4, 5), (8, 3), (12, 4), (14, 8), (13, 12), (8, 13), (4, 13)], "#C9D3D8")
    for x in range(3, 14, 2):
        i.linea(x, 6 + (x % 3), x - 1, 12, "#8D9AA3", fijo=True)
    i.linea(6, 5, 10, 4, "#E8EEF2", fijo=True)
    return i.terminar()


@icono("quitina")
def _quitina(i):
    i.poli([(2, 6), (8, 3), (14, 6), (13, 12), (8, 14), (3, 12)], "#7A3B22")
    i.linea(3, 9, 13, 9, "#3B1C12")
    i.linea(4, 6, 8, 4, "#C9792E", fijo=True)
    i.linea(4, 10, 8, 11, "#A55A2C", fijo=True)
    i.p(10, 5, "#F2B33A", True)
    return i.terminar()


@icono("glandula_salamandra")
def _glandula(i):
    i.elipse(8, 9, 4.5, 4, "#B8401E")
    i.elipse(7, 8, 2, 1.6, "#FF8A3A", fijo=True)
    i.p(6, 7, "#FFD27A", True)
    i.linea(8, 5, 9, 2, "#7A2414")
    return i.terminar()


# ====================================================================== objetos

@icono("daga_colmillo")
def _daga(i):
    i.poli([(14, 1), (15, 2), (9, 9), (7, 7)], "#EDE3C8")
    i.linea(13, 2, 9, 6, "#FFF8E6", fijo=True)
    i.linea(5, 6, 10, 11, "#6B4A2A", grosor=2)
    i.linea(7, 9, 2, 14, "#4A3020", grosor=2)
    for k in range(3):
        i.p(6 - k * 1.5, 10 + k * 1.5, "#C9A27A", True)
    i.p(2, 14, "#E3B04B", True)
    return i.terminar()


@icono("martillo_cuerno")
def _martillo(i):
    i.linea(3, 14, 10, 7, "#6B4A2A", grosor=2)
    i.poli([(7, 6), (11, 2), (15, 6), (11, 10)], "#8C8A86")
    i.poli([(11, 2), (12, 0), (13, 1), (13, 3)], "#B3B1AC")
    i.poli([(15, 6), (16, 8), (14, 8)], "#B3B1AC")
    i.linea(9, 6, 11, 4, "#5E5C59", fijo=True)
    i.p(2, 15, "#4A3020")
    return i.terminar()


@icono("flecha_aguijon")
def _flecha(i):
    i.linea(3, 13, 11, 5, "#8A6A44")
    i.poli([(10, 3), (14, 2), (13, 6), (11, 6)], "#E8A93A")
    i.p(13, 3, "#3A2414", True)
    i.linea(2, 12, 4, 14, "#2A2234", grosor=2)
    i.p(2, 14, "#5E4A7A")
    return i.terminar()


@icono("carne_salada")
def _carne(i):
    i.poli([(2, 9), (4, 4), (10, 3), (14, 6), (13, 11), (8, 13), (3, 12)], "#8A3A2A")
    i.elipse(8, 8, 3, 2.4, "#A84A36")
    i.elipse(12, 9, 1.4, 1.4, "#EDE3C8")
    for x, y in ((5, 6), (9, 5), (7, 10), (11, 7), (4, 10)):
        i.p(x, y, "#F4F2EC", True)
    return i.terminar()


@icono("pulpa_cactus")
def _pulpa(i):
    i.poli([(3, 12), (4, 5), (8, 3), (12, 5), (13, 12), (8, 14)], "#4E8A3A")
    i.poli([(5, 11), (6, 6), (8, 5), (10, 6), (11, 11), (8, 12)], "#C8E08A")
    for x, y in ((7, 8), (9, 9), (8, 10)):
        i.p(x, y, "#9CC25A", True)
    for x, y in ((3, 7), (13, 8), (4, 11)):
        i.p(x, y, "#EDE3C8", True)
    return i.terminar()


@icono("fertilizante_musgo")
def _fertilizante(i):
    i.poli([(4, 13), (3, 8), (5, 5), (11, 5), (13, 8), (12, 13)], "#9C7A55")
    i.rect(6, 3, 10, 5, "#7A5A3C")
    i.linea(5, 5, 11, 5, "#557E2E", grosor=1)
    i.elipse(8, 9, 2.5, 2, "#6E9A3E")
    i.p(7, 8, "#9CC25A", True)
    i.p(9, 3, "#9CC25A", True)
    return i.terminar()


@icono("runa_pibble")
def _runa(i):
    i.poli([(3, 3), (12, 2), (13, 13), (4, 14)], "#2E5A9C")
    i.linea(8, 4, 8, 12, "#F2C84A", fijo=True)
    i.linea(6, 6, 10, 10, "#F2C84A", fijo=True)
    i.linea(10, 6, 6, 10, "#F2C84A", fijo=True)
    i.p(8, 8, "#FFF0A0", True)
    return i.terminar()


def _varita(i, vara, estrella, brillo, cascabel=None):
    i.linea(3, 14, 10, 7, vara, grosor=2)
    i.poli([(11, 1), (12, 4), (15, 4), (13, 6), (14, 9), (11, 7), (8, 9), (9, 6), (7, 4), (10, 4)], estrella)
    i.p(11, 5, brillo, True)
    i.p(12, 4, brillo, True)
    if cascabel:
        i.p(5, 9, cascabel, True)
        i.p(8, 13, cascabel, True)


@icono("varita_revolthir")
def _v_rev(i):
    _varita(i, "#C2387A", "#F2C84A", "#FFF0A0", "#FF8A3A")
    return i.terminar()


@icono("varita_correctar")
def _v_cor(i):
    _varita(i, "#2E4A8A", "#BFE6FF", "#FFFFFF", "#8AC8FF")
    return i.terminar()


@icono("bomba_brasa")
def _bomba(i):
    i.elipse(8, 9, 5, 5, "#6B4A3A")
    i.linea(5, 9, 8, 7, "#FF7A1E", fijo=True)
    i.linea(8, 11, 11, 9, "#E8401E", fijo=True)
    i.rect(7, 3, 9, 4, "#4A3020")
    i.linea(9, 3, 12, 1, "#C9A27A")
    i.p(12, 0, "#FFD27A", True)
    i.elipse(6, 7, 1, 1, "#8C6A58", fijo=True)
    return i.terminar()


@icono("senuelo_pluma")
def _senuelo(i):
    for dx, ang in ((0, 0), (-2, -0.5), (2, 0.5)):
        i.linea(8, 12, 8 + dx * 2 + ang * 4, 2, "#2A2234", grosor=2)
    i.rect(6, 10, 10, 11, "#C9A27A")
    i.linea(8, 12, 8, 14, "#C9A27A")
    i.p(7, 4, "#5E4A7A", True)
    i.p(11, 4, "#5E4A7A", True)
    return i.terminar()


@icono("antorcha_grasa")
def _antorcha(i):
    i.linea(7, 14, 8, 6, "#6B4A2A", grosor=2)
    i.rect(6, 4, 9, 6, "#EADBA8")
    i.elipse(7.5, 2.5, 1.8, 2, "#FF9A2E")
    i.p(7, 2, "#FFE07A", True)
    i.p(8, 3, "#FFE07A", True)
    return i.terminar()


def _escudo(i, base, borde, detalle):
    i.poli([(3, 2), (13, 2), (13, 9), (8, 14), (3, 9)], borde)
    i.poli([(4, 3), (12, 3), (12, 9), (8, 13), (4, 9)], base)
    detalle(i)


@icono("escudo_escamas")
def _escudo_escamas(i):
    def det(i):
        for cy in (5, 8, 11):
            for cx in range(5 + (cy % 2), 12, 2):
                if i.lleno(cx, cy):
                    i.p(cx, cy, "#4E9466", True)
        i.p(8, 7, "#7CF0D0", True)
    _escudo(i, "#2F6A4A", "#6B4A2A", det)
    return i.terminar()


@icono("escudo_caparazon")
def _escudo_cap(i):
    def det(i):
        i.linea(8, 3, 8, 12, "#174147", fijo=True)
        i.elipse(6, 6, 1, 1.6, "#56A3A8", fijo=True)
    _escudo(i, "#2B6F77", "#1E2A30", det)
    return i.terminar()


@icono("cantimplora")
def _cantimplora(i):
    i.elipse(8, 9.5, 5, 4.5, "#8A5A34")
    i.rect(7, 3, 9, 5, "#6B4A2A")
    i.rect(6.5, 2, 9.5, 2, "#4A3020")
    i.linea(3, 6, 6, 4, "#4A3020")
    i.linea(13, 6, 10, 4, "#4A3020")
    i.linea(4, 9, 12, 9, "#C9A27A", fijo=True)
    i.elipse(6, 8, 1.2, 1, "#A87448", fijo=True)
    return i.terminar()


@icono("cantimplora_reforzada")
def _cantimplora2(i):
    i.elipse(8, 9.5, 5.5, 5, "#7A4E2C")
    i.rect(7, 2, 9, 4, "#B8863A")
    i.rect(6.5, 1, 9.5, 1, "#E3B04B")
    i.linea(3, 7, 13, 7, "#E3B04B", fijo=True)
    i.linea(3, 12, 13, 12, "#E3B04B", fijo=True)
    i.elipse(6, 9, 1.2, 1, "#9C6A44", fijo=True)
    return i.terminar()


@icono("pedazo_piramide")
def _piramide(i):
    i.poli([(8, 2), (14, 13), (2, 13)], "#D9B87A")
    i.poli([(8, 2), (10, 5.5), (6, 5.5)], "#E3B04B")
    i.linea(4, 10, 12, 10, "#B8945A", fijo=True)
    i.linea(6, 7, 10, 7, "#B8945A", fijo=True)
    i.p(7, 9, "#2A4E9C", True)
    i.p(9, 12, "#2A4E9C", True)
    i.p(8, 3, "#FFF0A0", True)
    return i.terminar()


# ====================================================================== armaduras (silueta + su material)

def _casco(i, c):
    i.poli([(3, 4), (5, 2), (11, 2), (13, 4), (13, 11), (10, 11), (10, 8), (6, 8), (6, 11), (3, 11)], c)


def _pechera(i, c):
    i.poli([(2, 2), (5, 2), (6, 4), (10, 4), (11, 2), (14, 2), (14, 7), (12, 7), (12, 14), (4, 14), (4, 7), (2, 7)], c)


def _pantalon(i, c):
    i.poli([(3, 2), (13, 2), (13, 14), (9, 14), (9, 7), (7, 7), (7, 14), (3, 14)], c)


def _botas(i, c):
    i.poli([(2, 7), (6, 7), (6, 11), (7, 13), (7, 14), (2, 14)], c)
    i.poli([(9, 7), (13, 7), (13, 11), (14, 13), (14, 14), (9, 14)], c)


PIEZAS = {"casco": _casco, "pechera": _pechera, "pantalon": _pantalon, "botas": _botas}


def _armadura(nombre, base, detalle):
    for pieza, silueta in PIEZAS.items():
        def f(i, silueta=silueta, pieza=pieza):
            silueta(i, base)
            detalle(i, pieza)
            return i.terminar()
        ICONOS[f"{nombre}_{pieza}"] = (f, "item")


def _det_desierto(i, pieza):
    if pieza == "casco":
        for y in range(3, 11, 2):
            for x in range(3, 14):
                if i.lleno(x, y):
                    i.p(x, y, "#E3B04B", True)
        i.p(8, 2, "#E3B04B", True)
    elif pieza == "pechera":
        for y, c in ((4, "#E3B04B"), (5, "#2F9FA8"), (6, "#B5532F"), (7, "#E3B04B")):
            for x in range(4, 13):
                if i.lleno(x, y) and not (6 <= x <= 10 and y == 4):
                    i.p(x, y, c, True)
        i.rect(5, 8, 11, 14, "#B07A55")
        i.terminar_vacio = True
    elif pieza == "pantalon":
        i.rect(3, 2, 13, 3, "#2A4E9C")
        for x in range(4, 13, 2):
            i.p(x, 2, "#E3B04B", True)
        for x in range(3, 14, 2):
            for y in range(5, 14):
                if i.lleno(x, y):
                    i.p(x, y, "#D6C8A4", True)
    else:
        for x in list(range(2, 7)) + list(range(9, 14)):
            i.p(x, 9, "#E3B04B", True)


def _det_plumas(i, pieza):
    for y in range(2, 15, 3):
        for x in range(2 + (y % 2), 15, 2):
            if i.lleno(x, y):
                i.p(x, y, "#5A3A24", True)
    if pieza == "casco":
        i.linea(8, 2, 10, 0, "#EFE3CC")
        i.linea(9, 2, 12, 0, "#B8693A")
    if pieza == "botas":
        i.linea(6, 9, 8, 7, "#EFE3CC")
        i.linea(13, 9, 15, 7, "#EFE3CC")


def _det_quitina(i, pieza):
    for y in range(3, 15, 3):
        for x in range(16):
            if i.lleno(x, y):
                i.p(x, y, "#3B1C12", True)
            if i.lleno(x, y - 1) and y - 1 > 1:
                i.p(x, y - 1, "#C9792E" if (x + y) % 5 else "#F2B33A", True)
    if pieza == "casco":
        i.rect(5, 5, 6, 5, "#F2B33A", True)
        i.rect(10, 5, 11, 5, "#F2B33A", True)


def _det_tortuga(i, pieza):
    for y in range(3, 15, 3):
        for x in range(1 + (y % 2) * 2, 16, 4):
            if i.lleno(x, y):
                i.p(x, y, "#2F5A26", True)
                i.p(x + 1, y - 1, "#9FC25A", True) if i.lleno(x + 1, y - 1) else None
    if pieza == "pechera":
        i.rect(6, 6, 10, 12, "#D9C77A")
        i.linea(8, 6, 8, 12, "#8A7A3E", fijo=True)


def _det_pelaje(i, pieza):
    for x in range(1, 16, 2):
        for y in range(2, 15):
            if i.lleno(x, y) and (x * 7 + y * 3) % 5 == 0:
                i.p(x, y, "#8D9AA3", True)
    if pieza == "casco":
        i.rect(5, 5, 11, 8, "#EFE6D0")
        i.rect(6, 6, 10, 8, "#B07A55")
    elif pieza == "pechera":
        i.rect(7, 5, 9, 14, "#3D2B22")
        for y in (7, 10, 13):
            i.p(8, y, "#EFE6D0", True)
    elif pieza == "pantalon":
        i.rect(3, 2, 13, 9, "#3D2B22")
    else:
        i.rect(2, 13, 7, 14, "#3D2B22")
        i.rect(9, 13, 14, 14, "#3D2B22")


_armadura("desierto", "#E9DDBF", _det_desierto)
_armadura("plumas", "#B8693A", _det_plumas)
_armadura("quitina", "#7A3B22", _det_quitina)
_armadura("tortuga", "#4E8A3A", _det_tortuga)
_armadura("pelaje", "#C9D3D8", _det_pelaje)


def _det_hielo(i, pieza):
    for y in range(2, 15):
        for x in range(2, 15):
            if i.lleno(x, y) and (x + 2 * y) % 7 == 0:
                i.p(x, y, "#E8FAFF", True)
    if pieza == "casco":
        for x in (5, 7, 9, 11):
            i.p(x, 1, "#E8FAFF", True)
    elif pieza == "pechera":
        i.rect(7, 5, 9, 8, "#E8FAFF")


def _det_tanque(i, pieza):
    if pieza == "casco":
        i.rect(4, 7, 12, 7, "#6B2E8C")
        i.p(8, 1, "#6B2E8C", True)
    elif pieza == "pechera":
        for (x, y) in ((4, 4), (11, 4), (4, 11), (11, 11)):
            i.p(x, y, "#E3B04B", True)
    elif pieza == "pantalon":
        i.p(5, 8, "#9A7A2A", True)
        i.p(10, 8, "#9A7A2A", True)


_armadura("hielo", "#9FD8EE", _det_hielo)
_armadura("tanque", "#2E2B34", _det_tanque)
del ICONOS["tortuga_casco"]                           # el casco de tortuga es el de Minecraft


# ====================================================================== efectos (18x18)

@icono("sofocacion", "mob_effect")
def _sofocacion(i):
    i.elipse(9, 7, 4, 4, "#F2B33A")
    i.elipse(8, 6, 1.6, 1.6, "#FFE07A", fijo=True)
    for k in range(3):
        x = 4 + k * 5
        for y in range(12, 17):
            i.p(x + (1 if (y // 2) % 2 else 0), y, "#E87A2E")
    return i.terminar()


@icono("frio", "mob_effect")
def _frio(i):
    for ang in (0, 60, 120):
        a = math.radians(ang)
        i.linea(9 - 6 * math.cos(a), 9 - 6 * math.sin(a), 9 + 6 * math.cos(a), 9 + 6 * math.sin(a), "#BFE6FF")
    i.elipse(9, 9, 1.2, 1.2, "#FFFFFF")
    return i.terminar()


@icono("branquias", "mob_effect")
def _branquias(i):
    for k, y in enumerate((4, 8, 12)):
        i.linea(4, y + 2, 14, y, "#F07A92", grosor=2)
        i.p(14, y, "#FFB0C0", True)
    i.linea(4, 3, 4, 15, "#C2405A", grosor=2)
    return i.terminar()


# ====================================================================== objetos de rol (solo con /give)

@icono("espada_vitae")
def _vitae(i):
    i.poli([(14, 1), (15, 2), (8, 9), (6, 7)], "#7FBF5A")                 # hoja de madera viva
    i.linea(13, 2, 8, 7, "#C8F0A0", fijo=True)
    for (x, y) in ((12, 5), (10, 7), (9, 4)):
        i.p(x, y, "#3E8A3A", True)                                       # hojitas
    i.linea(4, 6, 9, 11, "#E3B04B", grosor=2)                             # guarda dorada
    i.linea(6, 10, 2, 14, "#6B4A2A", grosor=2)
    i.p(2, 14, "#9BE7FF", True)
    return i.terminar()


@icono("espada_hielo")
def _hielo(i):
    i.poli([(15, 0), (15, 3), (8, 10), (5, 7)], "#A9E4F5")
    i.linea(14, 1, 8, 7, "#F2FDFF", fijo=True)
    i.p(11, 3, "#6FC3E0", True)
    i.p(9, 6, "#6FC3E0", True)
    i.linea(4, 6, 9, 11, "#7FB8D6", grosor=2)
    i.linea(6, 10, 2, 14, "#3A4A66", grosor=2)
    i.p(2, 14, "#DDF6FF", True)
    return i.terminar()


@icono("martillo_negro")
def _martillo_negro(i):
    i.linea(2, 15, 9, 8, "#2B2230", grosor=2)
    i.poli([(5, 6), (10, 1), (16, 7), (11, 12)], "#1A161E")
    i.poli([(10, 1), (11, 0), (13, 1), (12, 3)], "#3A3342")
    i.poli([(16, 7), (16, 9), (14, 9)], "#3A3342")
    i.linea(7, 6, 11, 2, "#6B2E8C", fijo=True)
    i.linea(10, 10, 14, 6, "#6B2E8C", fijo=True)
    i.p(10, 6, "#C9A23A", True)
    return i.terminar()


@icono("totem_anj")
def _anj(i):
    i.elipse(8, 4, 3.2, 3.6, "#E3B04B")
    for y in range(i.n):                                                 # el ojo del ankh
        for x in range(i.n):
            if ((x - 8) / 1.3) ** 2 + ((y - 4) / 2.0) ** 2 <= 1.0:
                i.px[y][x] = None
    i.rect(7, 7, 9, 15, "#E3B04B")
    i.rect(3, 8, 13, 9, "#E3B04B")
    for (x, y) in ((8, 8), (8, 11), (8, 13)):
        i.p(x, y, "#2F9FA8", True)
    return i.terminar()


@icono("poseido", "mob_effect")
def _poseido(i):
    i.elipse(9, 9, 7, 4, "#D9C7E8")
    i.elipse(9, 9, 3, 3.5, "#8A3CC8")
    i.elipse(9, 9, 1.2, 2, "#0A050E")
    return i.terminar()


def main(ids=None):
    os.makedirs(SALIDA, exist_ok=True)
    hechos = []
    for nombre, (f, carpeta) in ICONOS.items():
        if ids and nombre not in ids:
            continue
        lado = 18 if carpeta == "mob_effect" else 16
        im = f(Icono(lado)).imagen()
        destino = os.path.join(TEXTURAS, carpeta)
        os.makedirs(destino, exist_ok=True)
        im.save(os.path.join(destino, f"{nombre}.png"))
        hechos.append((nombre, im))
    # la hoja para revisar
    from .bichos.hojas import _fuente
    col, k = 8, 8
    celda = 16 * k + 28
    filas = (len(hechos) + col - 1) // col
    hoja = Image.new("RGB", (col * celda, filas * celda), (52, 48, 44))
    d = ImageDraw.Draw(hoja)
    for n, (nombre, im) in enumerate(hechos):
        x, y = (n % col) * celda, (n // col) * celda
        grande = im.resize((im.width * k, im.height * k), Image.NEAREST)
        hoja.paste(grande, (x + 14, y + 4), grande)
        d.text((x + 6, y + celda - 22), nombre, fill=(240, 230, 210), font=_fuente(13))
    hoja.save(os.path.join(SALIDA, "iconos.png"))
    print(len(hechos), "iconos ->", os.path.join(SALIDA, "iconos.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
