"""
Herramienta: convierte recortes de una imagen de referencia en pixel art LIMPIO para las texturas, y lo guarda como
un modulo de Python con filas de letras (una letra por texel), asi el motor no necesita PIL para usarlo.

Pasos por recorte:
  1. Pyxelate (bajada de resolucion que respeta los bordes) al tamano exacto de la cara en texeles.
  2. Cada pixel pasa a una clase de la rampa fija: n negro, g gris (blanco en sombra), b blanco, h blanco con luz.
     Lo saturado (cintas rojas o amarillas, piel) se vuelve tela negra: esas piezas van aparte en 3D.
  3. Limpieza como haria un pixel artist: filtro de moda (saca los puntitos sueltos), borra manchas de menos de
     3 texeles, y le da volumen a cada manchon blanco (canto de arriba con luz, canto de abajo en sombra).
Nada de ruido: los colores salen solo de la rampa y la forma sale de la referencia.

Uso (necesita PIL, numpy y pyxelate; pyxelate se puede usar desde el codigo fuente con PYTHONPATH):
    PYTHONPATH=ruta/a/pyxelate python -m taller.pixelar correctar
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE_KANJI = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FUENTE_PIXEL = "/usr/share/fonts/opentype/unifont/unifont_jp.otf"   # fuente de pixel art 16 x 16 (kanji nitidos)

# clase -> letra. 1 (negro claro de la iluminacion del render) se junta con el negro.
LETRA = {0: "n", 1: "n", 2: "g", 3: "b", 4: "h"}


def clases(rgb):
    """Pixel -> clase de la rampa por luminancia; 9 = saturado (rojo, amarillo, piel)."""
    import numpy as np
    a = rgb.astype(float) / 255
    mx, mn = a.max(2), a.min(2)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    c = np.zeros(lum.shape, int)
    c[lum > 0.17] = 1
    c[lum > 0.30] = 2
    c[lum > 0.50] = 3
    c[lum > 0.80] = 3
    c[(sat > 0.28) & (mx > 0.3)] = 9
    return c


def moda(c, veces=2, minimo=5):
    """Cada texel toma la clase de la mayoria de sus 8 vecinos si al menos 'minimo' coinciden."""
    import numpy as np
    h, w = c.shape
    for _ in range(veces):
        p = np.pad(c, 1, mode="edge")
        nuevo = c.copy()
        for y in range(h):
            for x in range(w):
                vec = np.delete(p[y:y + 3, x:x + 3].ravel(), 4)
                vals, cnt = np.unique(vec, return_counts=True)
                k = cnt.argmax()
                if cnt[k] >= minimo:
                    nuevo[y, x] = vals[k]
        c = nuevo
    return c


def sin_migas(c, minimo=3):
    """Borra las manchas claras de menos de 'minimo' texeles (quedan negras)."""
    h, w = c.shape
    visto = set()
    for y0 in range(h):
        for x0 in range(w):
            if c[y0, x0] < 2 or (y0, x0) in visto:
                continue
            pila, comp = [(y0, x0)], []
            visto.add((y0, x0))
            while pila:
                y, x = pila.pop()
                comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and c[yy, xx] >= 2 and (yy, xx) not in visto:
                        visto.add((yy, xx))
                        pila.append((yy, xx))
            if len(comp) < minimo:
                for y, x in comp:
                    c[y, x] = 0
    return c


def volumen(c):
    """Canto de arriba de cada manchon blanco con luz y canto de abajo en sombra (luz de arriba)."""
    out = c.copy()
    h, w = c.shape
    for y in range(h):
        for x in range(w):
            if c[y, x] == 3:
                if y + 1 < h and c[y + 1, x] < 2:
                    out[y, x] = 2
                elif y == 0 or c[y - 1, x] < 2:
                    out[y, x] = 4
    return out


def pixelar(ref, caja, w, h):
    """Recorte (x1, y1, x2, y2) de la referencia -> matriz de clases de w x h texeles, ya limpia."""
    import numpy as np
    from PIL import Image
    from pyxelate import Pyx
    im = ref.crop(caja).resize((w * 3, h * 3), Image.LANCZOS)
    arr = np.asarray(im)
    pyx = Pyx(factor=3, palette=10, dither="none", sobel=3)
    pyx.fit(arr)
    out = pyx.transform(arr)[:, :, :3]
    out = np.asarray(Image.fromarray(out).resize((w, h), Image.NEAREST))
    c = clases(out)
    c[c == 9] = 0
    c[c == 1] = 0
    c = sin_migas(moda(c))
    return volumen(c)


def kanji(texto, lado, fuente=FUENTE_KANJI, grosor=1, nativo=False):
    """Un kanji como mascara de lado x lado (True = trazo), con el trazo engrosado 'grosor' texeles.
    nativo: la fuente ya es de pixel art (Unifont, 16 x 16): se dibuja a su tamano, sin achicar, y queda nitida."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    if nativo:
        im = Image.new("L", (lado, lado), 0)
        ImageDraw.Draw(im).text((0, 0), texto, font=ImageFont.truetype(fuente, lado), fill=255)
        m = np.asarray(im) > 127
    else:
        k = 8                                         # se dibuja grande y se baja: bordes limpios
        im = Image.new("L", (lado * k, lado * k), 0)
        f = ImageFont.truetype(fuente, int(lado * k * 0.98))
        d = ImageDraw.Draw(im)
        x1, y1, x2, y2 = d.textbbox((0, 0), texto, font=f)
        d.text(((lado * k - (x2 - x1)) / 2 - x1, (lado * k - (y2 - y1)) / 2 - y1), texto, font=f, fill=255)
        m = np.asarray(im.resize((lado, lado), Image.BOX)) > 70
    for _ in range(grosor):
        g = m.copy()
        g[:, 1:] |= m[:, :-1]
        g[1:, :] |= m[:-1, :]
        m = g
    return m


def a_filas(c):
    return ["".join(LETRA.get(int(v), "n") for v in fila) for fila in c]


def escribir_modulo(ruta, doc, piezas):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write('"""\n' + doc.strip() + '\n\nGenerado por taller/pixelar.py: no editar a mano, volver a generarlo.\n'
                'Letras: n negro, g gris (blanco en sombra), b blanco, h blanco con luz, k kanji, a aro del kanji, . nada.\n"""\n')
        for nombre, filas in piezas:
            f.write(f"\n{nombre} = (\n")
            for fila in filas:
                f.write(f'    "{fila}",\n')
            f.write(")\n")


# ---------------------------------------------------------------- recetas

def receta_correctar():
    """Correcthar (referencias/personajes/correctar_semidios.png): la escritura de sus etiquetas, "原状回復" (volver
    al estado original, su poder), en letras de pixel art de 16 x 16 (Unifont). El resto de su ropa se pinta con
    formas pensadas."""
    piezas = []
    for k, letra in enumerate("原状回復"):
        m = kanji(letra, 16, FUENTE_PIXEL, grosor=0, nativo=True)
        piezas.append((f"LETRA_{k}", ["".join("k" if v else "." for v in fila) for fila in m]))
    destino = os.path.join(RAIZ, "taller/personajes/correctar_pixelart.py")
    escribir_modulo(destino, "Letras de las etiquetas de Correcthar: 原状回復.", piezas)
    return destino


RECETAS = {"correctar": receta_correctar}

if __name__ == "__main__":
    print(RECETAS[sys.argv[1]]())
