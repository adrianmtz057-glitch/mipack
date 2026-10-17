"""
Hojas de revision de los bichos: por bioma, cada bicho de 3/4 (y de lado), con su nombre, en que se basa, su
mecanica, lo que suelta y lo que mide; los que brillan llevan ademas un recuadro de noche.
Uso: python -m taller.bichos.hojas [ids...]  ->  salida/bichos/<bioma>.png (o solo esos bichos en prueba.png)
"""

import os
import sys
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .. import vista
from .catalogo import BIOMAS, CATALOGO

SALIDA = os.path.join(os.path.dirname(__file__), "..", "..", "salida", "bichos")
FONDO = ((0.86, 0.85, 0.80), (0.66, 0.64, 0.58))
NOCHE = ((0.07, 0.08, 0.13), (0.03, 0.03, 0.06))


def _fuente(tam):
    for ruta in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def armar(b):
    """(armado, lienzo, uvs, mascara de brillo o None)."""
    a = b.crear()
    lienzo, uvs = a.m.pintar()
    mascara = None
    if a.piel.brilla:
        a.piel.modo = "brillo"
        luz = a.m.luz
        a.m.luz = False
        lz2, _ = a.m.pintar()
        a.m.luz = luz
        a.piel.modo = "color"
        mascara = lz2
    return a, lienzo, uvs, mascara


def _tex(lz):
    return np.frombuffer(bytes(lz.px), dtype=np.uint8).reshape(lz.alto, lz.ancho, 4) / 255.0


def render(a, lienzo, uvs, mascara=None, vistas=((35, 14), (90, 6)), alto=300, noche=False):
    tex = _tex(lienzo)
    if noche:                                        # de noche: todo oscuro y lo que brilla, encendido
        tex = tex.copy()
        tex[..., :3] *= 0.22
        if mascara is not None:
            m = _tex(mascara)
            on = m[..., 3] > 0.5
            tex[on, :3] = np.clip(m[on, :3] * 1.15, 0, 1)
    caras = vista._caras_mundo(a.m, uvs)
    todos = np.concatenate([P for P, _ in caras])
    lo, hi = todos.min(axis=0), todos.max(axis=0)
    centro = (lo + hi) / 2
    radio = float(np.max(hi - lo)) * 0.62
    ims = []
    for yaw, pitch in vistas:
        img = vista._render(caras, tex, yaw, pitch, alto * 0.9 / (2 * radio), alto, alto, centro, NOCHE if noche else FONDO, True)
        ims.append(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)))
    out = Image.new("RGB", (alto * len(ims), alto))
    for k, im in enumerate(ims):
        out.paste(im, (alto * k, 0))
    return out, (hi - lo) * a.escala / 16.0


def tarjeta(b, alto=300):
    a, lz, uvs, mascara = armar(b)
    img, medidas = render(a, lz, uvs, mascara, alto=alto)
    if mascara is not None:
        noche, _ = render(a, lz, uvs, mascara, vistas=((35, 14),), alto=alto, noche=True)
        img2 = Image.new("RGB", (img.width + noche.width, alto))
        img2.paste(img, (0, 0))
        img2.paste(noche, (img.width, 0))
        img = img2
    ancho = alto * 3
    t = Image.new("RGB", (ancho, alto + 118), (26, 24, 22))
    t.paste(img, (0, 0))
    d = ImageDraw.Draw(t)
    d.text((10, alto + 6), b.nombre, fill=(245, 235, 210), font=_fuente(20))
    d.text((10, alto + 32), f"Base: {b.base}  ·  Suelta: {b.suelta}  ·  {medidas[1]:.1f} bloques de alto, {max(medidas[0], medidas[2]):.1f} de largo",
           fill=(190, 182, 165), font=_fuente(14))
    for k, linea in enumerate(textwrap.wrap(b.mecanica, 100)[:3]):
        d.text((10, alto + 54 + 18 * k), linea, fill=(220, 210, 190), font=_fuente(15))
    return t


def hoja(titulo, bichos, por_fila=2):
    tarjetas = [tarjeta(b) for b in bichos]
    w, h = tarjetas[0].size
    filas = (len(tarjetas) + por_fila - 1) // por_fila
    out = Image.new("RGB", (w * por_fila, h * filas + 50), (18, 17, 16))
    d = ImageDraw.Draw(out)
    d.text((14, 10), titulo, fill=(250, 238, 200), font=_fuente(28))
    for k, t in enumerate(tarjetas):
        out.paste(t, ((k % por_fila) * w, 50 + (k // por_fila) * h))
    return out


def main(ids=None):
    os.makedirs(SALIDA, exist_ok=True)
    if ids:
        hoja("Prueba", [CATALOGO[i] for i in ids]).save(os.path.join(SALIDA, "prueba.png"))
        return
    for bioma in BIOMAS:
        bs = [b for b in CATALOGO.values() if b.bioma == bioma]
        if bs:
            nombre = bioma.lower().replace(" ", "_").replace("ñ", "n").replace("á", "a").replace("ó", "o")
            hoja(bioma, bs).save(os.path.join(SALIDA, f"{nombre}.png"))
            print(bioma, len(bs))


if __name__ == "__main__":
    main(sys.argv[1:])
