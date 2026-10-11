"""
Texturas de bloques de Velkia (paquete de texturas para Minecraft 1.20.1) en estilo "soft": colores planos y
limpios, sin grano ni tramado, con pocos detalles bien puestos (rayitas, piedritas, juntas) y degradados muy suaves,
para que se vean bien sin shaders. Todas repiten sin costura cada 16 pixeles.
El pasto y las hojas van en grises (el juego les pone el color del bioma) y van tambien los mapas de color del pasto y
del follaje, con verdes suaves (oliva en lo seco, verde fresco en lo humedo).
Uso: python -m taller.texturas_bloques  ->  salida/velkia_texturas.zip
"""

import io
import json
import math
import os
import zipfile

import numpy as np
from PIL import Image, ImageDraw

N = 16
Y, X = np.mgrid[0:N, 0:N]
SALIDA = os.path.join(os.path.dirname(__file__), "..", "salida")


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def gris(v):
    return np.array([v, v, v], dtype=float) * 255


def lienzo(color):
    img = np.zeros((N, N, 4))
    img[..., :3] = color
    img[..., 3] = 255
    return img


def suave(img, fuerza, kx=1, ky=1, fase=0.0):
    """Un degradado muy suave (repite cada 16): aclara y oscurece apenas zonas grandes."""
    f = 1 + fuerza * np.sin(2 * math.pi * (kx * X + ky * Y) / N + fase) * np.cos(2 * math.pi * (ky * X - kx * Y) / N + fase * 0.7)
    img[..., :3] *= f[..., None]
    return img


def punto(img, x, y, color, alfa=None):
    img[y % N, x % N, :3] = color
    if alfa is not None:
        img[y % N, x % N, 3] = alfa


def raya(img, x, y, largo, color, vertical=True):
    for k in range(largo):
        punto(img, x, y + k, color) if vertical else punto(img, x + k, y, color)


def mancha(img, cx, cy, r, color, mezcla=1.0, achatada=1.0):
    """Una mancha redondeada (con la vuelta de 16 pixeles)."""
    dx = np.minimum(np.abs(X - cx), N - np.abs(X - cx))
    dy = np.minimum(np.abs(Y - cy), N - np.abs(Y - cy)) / achatada
    m = dx * dx + dy * dy <= r * r
    img[m, :3] = img[m, :3] * (1 - mezcla) + np.asarray(color) * mezcla
    return m


def lugares(n, semilla, separacion=3.0):
    """n lugares al azar fijos, separados (con la vuelta de 16) para que los detalles no se amontonen."""
    rng = np.random.default_rng(semilla)
    out = []
    intentos = 0
    while len(out) < n and intentos < 2000:
        intentos += 1
        p = (int(rng.integers(N)), int(rng.integers(N)))
        if all(min(abs(p[0] - q[0]), N - abs(p[0] - q[0])) ** 2 + min(abs(p[1] - q[1]), N - abs(p[1] - q[1])) ** 2
               >= separacion ** 2 for q in out):
            out.append(p)
    return out


# ---------------------------------------------------------------- los colores

TIERRA, TIERRA_O, TIERRA_C = hexrgb("#8C5B3C"), hexrgb("#76492F"), hexrgb("#9E6C4A")
PIEDRA, PIEDRA_O, PIEDRA_C = hexrgb("#8B8B90"), hexrgb("#75757B"), hexrgb("#9B9BA0")
ARENA, ARENA_O, ARENA_C = hexrgb("#E4D09E"), hexrgb("#D2BB86"), hexrgb("#EFDFB6")
ROJA, ROJA_O, ROJA_C = hexrgb("#C8733F"), hexrgb("#B05F31"), hexrgb("#D9884F")
ARENISCA, ARENISCA_O, ARENISCA_C = hexrgb("#DCC38C"), hexrgb("#C6AB72"), hexrgb("#E8D4A2")
CORTEZA, CORTEZA_O, CORTEZA_C = hexrgb("#6E5136"), hexrgb("#5A4029"), hexrgb("#80613F")
MADERA, MADERA_O, MADERA_C = hexrgb("#BA8C52"), hexrgb("#9C7341"), hexrgb("#C99C62")
VERDE_COSTADO = hexrgb("#7FA046")
TERRACOTAS = {
    "terracotta": hexrgb("#A0644A"), "white_terracotta": hexrgb("#D6BCAB"), "orange_terracotta": hexrgb("#AD6230"),
    "yellow_terracotta": hexrgb("#C38F35"), "red_terracotta": hexrgb("#95412F"), "brown_terracotta": hexrgb("#5A3D2B"),
    "light_gray_terracotta": hexrgb("#998580"),
}


# ---------------------------------------------------------------- las texturas

def grass_block_top():
    img = suave(lienzo(gris(0.64)), 0.025, 1, 1, 0.4)
    for x, y in lugares(11, 3, 3.6):                      # rayitas cortas, como briznas
        raya(img, x, y, 2, gris(0.56))
    for x, y in lugares(4, 9, 5):
        punto(img, x, y, gris(0.70))
    return img


def _orilla():
    """Cuanto baja el pasto en cada columna del costado: una orilla ondulada limpia."""
    return [3 + round(1.2 + 1.2 * math.sin(2 * math.pi * x / N * 2 + 0.6) + 0.6 * math.sin(2 * math.pi * x / N * 5))
            for x in range(N)]


def dirt():
    img = suave(lienzo(TIERRA), 0.03, 1, 1, 1.2)
    for x, y in lugares(5, 5, 5):
        mancha(img, x + 0.5, y + 0.5, 0.9, TIERRA_O)
        punto(img, x, y, TIERRA_O)
    for x, y in lugares(4, 7, 5):
        punto(img, x, y, TIERRA_C)
    return img


def grass_block_side():
    img = dirt()
    orilla = _orilla()
    for x in range(N):
        for y in range(orilla[x]):
            img[y, x, :3] = VERDE_COSTADO * (1.04 if y == 0 else 1.0)
        img[orilla[x], x, :3] = TIERRA_O                  # la sombrita bajo el pasto
    return img


def grass_block_side_overlay():
    img = np.zeros((N, N, 4))
    orilla = _orilla()
    for x in range(N):
        for y in range(orilla[x]):
            img[y, x, :3] = gris(0.66 if y == 0 else 0.62)
            img[y, x, 3] = 255
    return img


def stone():
    img = suave(lienzo(PIEDRA), 0.03, 1, 1, 0.3)
    mancha(img, 4, 11, 3.2, PIEDRA_C, 0.5, 0.7)
    mancha(img, 12, 4, 2.6, PIEDRA_O, 0.35, 0.8)
    for x, y, l, v in ((2, 2, 3, False), (9, 9, 4, False), (12, 12, 2, True), (5, 6, 2, True)):
        raya(img, x, y, l, PIEDRA_O, v)
    return img


def cobblestone():
    img = lienzo(PIEDRA_O * 0.82)                          # la junta
    piedras = [(1, 1, 6, 5), (8, 0, 7, 4), (0, 7, 5, 5), (6, 5, 6, 6), (13, 5, 3, 5), (1, 13, 6, 3), (8, 12, 7, 4)]
    for k, (x, y, w, h) in enumerate(piedras):
        base = PIEDRA * (0.96 + 0.06 * (k % 3))
        for i in range(w):
            for j in range(h):
                if (i in (0, w - 1)) and (j in (0, h - 1)):
                    continue                              # esquinas redondeadas
                c = base
                if j == 0 or i == 0:
                    c = base * 1.07                       # luz arriba a la izquierda
                elif j == h - 1 or i == w - 1:
                    c = base * 0.9
                punto(img, x + i, y + j, c)
    return img


def sand(base=ARENA, oscuro=ARENA_O, claro=ARENA_C, semilla=2):
    img = suave(lienzo(base), 0.02, 1, 1, 0.8)
    for y in (4, 12):                                     # dos ondas de viento, apenas mas claras
        for x in range(N):
            if (x + y) % 8 != 0:
                punto(img, x, y + round(0.8 * math.sin(2 * math.pi * x / N + y)), base * 0.4 + claro * 0.6)
    for x, y in lugares(6, semilla, 4):
        punto(img, x, y, oscuro)
    return img


def red_sand():
    return sand(ROJA, ROJA_O, ROJA_C, 6)


def sandstone():
    img = lienzo(ARENISCA)
    img[0:3, :, :3] = ARENISCA_C                          # la franja de arriba
    img[3, :, :3] = ARENISCA_O
    img[9, :, :3] = ARENISCA_O * 1.04                     # una capa en medio
    img[13:16, :, :3] = ARENISCA * 0.96                   # la de abajo
    img[13, :, :3] = ARENISCA_O
    for x in (5, 11):
        punto(img, x, 6, ARENISCA_O)
    return img


def sandstone_top():
    img = suave(lienzo(ARENISCA), 0.02, 1, 1, 2.0)
    for x, y in lugares(4, 12, 5):
        punto(img, x, y, ARENISCA_C)
    return img


def sandstone_bottom():
    img = suave(lienzo(ARENISCA * 0.97), 0.025, 1, 2, 0.5)
    for x, y in lugares(6, 14, 4):
        punto(img, x, y, ARENISCA_O)
    return img


def gravel():
    img = lienzo(hexrgb("#7C7670"))
    colores = [hexrgb("#9A948D"), hexrgb("#8A847E"), hexrgb("#A59B8D"), hexrgb("#6E6964")]
    for k, (x, y) in enumerate(lugares(11, 21, 4.2)):
        c = colores[k % len(colores)]
        mancha(img, x + 0.5, y + 0.5, 1.6, c)
        punto(img, x, y + 1, c * 0.82)                   # su sombrita abajo
        punto(img, x - 1, y - 1, c * 1.08)
    return img


def oak_log():
    img = lienzo(CORTEZA)
    for x in (1, 5, 9, 13):
        for y in range(N):
            if (y + x * 3) % 7 != 0:
                punto(img, x, y, CORTEZA_O)
    for x, y in lugares(5, 23, 5):
        raya(img, x, y, 3, CORTEZA_C)
    return img


def oak_log_top():
    img = lienzo(MADERA_C)
    r = np.maximum(np.abs(X - 7.5), np.abs(Y - 7.5))
    img[(r > 2.6) & (r < 3.6), :3] = MADERA
    img[(r > 4.6) & (r < 5.6), :3] = MADERA
    img[r >= 6.6, :3] = CORTEZA                           # la corteza alrededor
    img[(r >= 6.6) & ((X + Y) % 5 == 0), :3] = CORTEZA_O
    return img


def oak_planks():
    img = lienzo(MADERA)
    for k in range(4):
        y0 = k * 4
        img[y0:y0 + 4, :, :3] *= (1.0, 1.03, 0.98, 1.01)[k]
        img[y0 + 3, :, :3] = MADERA_O                     # la junta entre tablas
        corte = (k * 7 + 3) % N
        img[y0:y0 + 3, corte, :3] = MADERA_O              # donde acaba cada tabla
        punto(img, (corte + 6) % N, y0 + 1, MADERA_C)     # un poco de veta
        punto(img, (corte + 7) % N, y0 + 1, MADERA_C)
    return img


def oak_leaves():
    """Racimos lisos (en grises) con su sombrita adentro, marquitas de hoja y pocos huecos."""
    img = lienzo(gris(0.60))
    for x, y in lugares(5, 37, 6):
        mancha(img, x + 0.5, y + 0.5, 2.6, gris(0.66))    # el lado con luz de cada racimo
        mancha(img, x + 1.5, y + 2.0, 1.4, gris(0.53))    # y su sombra
    for x, y in lugares(6, 41, 4.5):                      # marquitas en cruz
        punto(img, x, y, gris(0.72))
        punto(img, x - 1, y, gris(0.68))
        punto(img, x + 1, y, gris(0.68))
    for x, y in lugares(5, 43, 5):                        # unos huecos (en hojas detalladas)
        punto(img, x, y, gris(0.5), 0)
    return img


def terracota(base, semilla):
    img = suave(lienzo(base), 0.02, 1, 1, semilla)
    img[5, :, :3] = base * 0.95
    img[11, :, :3] = base * 1.04
    for x, y in lugares(3, semilla + 50, 6):
        punto(img, x, y, base * 0.93)
    return img


def mapa_de_color(seco, templado, humedo, frio, lado=256):
    """El mapa de color de pasto o follaje: x = temperatura (izquierda caliente), y = humedad (arriba humedo)."""
    temp = 1 - (np.arange(lado)[None, :] + 0.5) / lado     # 1 caliente ... 0 frio
    hum = 1 - (np.arange(lado)[:, None] + 0.5) / lado      # 1 humedo ... 0 seco
    hum = hum * temp                                       # el juego usa el triangulo de abajo
    c = (seco[None, None] * ((1 - hum) * temp)[..., None] + humedo[None, None] * (hum * temp)[..., None]
         + frio[None, None] * (1 - temp)[..., None])
    c = c * 0.75 + templado[None, None] * 0.25
    img = np.zeros((lado, lado, 4))
    img[..., :3] = c
    img[..., 3] = 255
    return img


def todas():
    t = {"stone": stone(), "cobblestone": cobblestone(), "dirt": dirt(), "grass_block_top": grass_block_top(),
         "grass_block_side": grass_block_side(), "grass_block_side_overlay": grass_block_side_overlay(),
         "sand": sand(), "red_sand": red_sand(), "sandstone": sandstone(), "sandstone_top": sandstone_top(),
         "sandstone_bottom": sandstone_bottom(), "gravel": gravel(), "oak_log": oak_log(), "oak_log_top": oak_log_top(),
         "oak_planks": oak_planks(), "oak_leaves": oak_leaves()}
    for k, (nombre, c) in enumerate(TERRACOTAS.items()):
        t[nombre] = terracota(c, k + 1)
    return t


def mapas():
    return {"grass": mapa_de_color(hexrgb("#C2B460"), hexrgb("#8DBA4C"), hexrgb("#5FAE52"), hexrgb("#7FAE8E")),
            "foliage": mapa_de_color(hexrgb("#AFA44C"), hexrgb("#6FA83E"), hexrgb("#469A3E"), hexrgb("#5E9A72"))}


def _png(img):
    buf = io.BytesIO()
    Image.fromarray(np.clip(img, 0, 255).round().astype(np.uint8), "RGBA").save(buf, "PNG")
    return buf.getvalue()


def icono():
    """pack.png: el cielo del desierto sobre un bloque de pasto y arena."""
    img = Image.new("RGBA", (128, 128))
    d = ImageDraw.Draw(img)
    for y in range(128):
        u = min(1, y / 80)
        c = tuple(int(a + (b - a) * u) for a, b in zip((52, 107, 194), (240, 214, 160)))
        d.line([(0, y), (127, y)], fill=c + (255,))
    for x in range(0, 128, 32):
        img.paste(Image.fromarray(np.clip(sand(), 0, 255).astype(np.uint8), "RGBA").resize((32, 32), Image.NEAREST), (x, 96))
    lado = np.clip(grass_block_side(), 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(lado, "RGBA").resize((48, 48), Image.NEAREST), (40, 48))
    return img


def armar_zip(ruta=None):
    ruta = ruta or os.path.join(SALIDA, "velkia_texturas.zip")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    t = todas()
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps({"pack": {"pack_format": 15, "description":
                                                       "Velkia soft: bloques limpios (1.20.1)"}}, indent=2))
        buf = io.BytesIO()
        icono().save(buf, "PNG")
        z.writestr("pack.png", buf.getvalue())
        for nombre, img in t.items():
            z.writestr(f"assets/minecraft/textures/block/{nombre}.png", _png(img))
        for nombre, img in mapas().items():
            z.writestr(f"assets/minecraft/textures/colormap/{nombre}.png", _png(img))
    return ruta, t


def hoja_de_muestra(t, ruta, rep=3, zoom=6, tinte=(0.55, 0.73, 0.30)):
    """Cada textura repetida rep x rep (para ver que no tenga costuras), con su nombre."""
    lado = N * rep * zoom
    cols = 6
    filas = math.ceil(len(t) / cols)
    hoja = Image.new("RGB", (cols * (lado + 8), filas * (lado + 22)), (30, 30, 34))
    d = ImageDraw.Draw(hoja)
    for k, (nombre, img) in enumerate(t.items()):
        arr = np.clip(img, 0, 255).copy()
        if nombre in ("grass_block_top", "oak_leaves", "grass_block_side_overlay"):
            arr[..., :3] *= np.array(tinte) / 0.62                       # como el verde de un bioma
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (60, 70, 90, 255)), im)
        rejilla = Image.new("RGBA", (N * rep, N * rep))
        for i in range(rep):
            for j in range(rep):
                rejilla.paste(im, (i * N, j * N))
        x, y = (k % cols) * (lado + 8), (k // cols) * (lado + 22)
        hoja.paste(rejilla.resize((lado, lado), Image.NEAREST), (x, y + 18))
        d.text((x + 2, y + 3), nombre, fill=(240, 220, 120))
    hoja.save(ruta)
    return ruta


if __name__ == "__main__":
    ruta, t = armar_zip()
    print("listo:", os.path.normpath(ruta), len(t), "texturas y 2 mapas de color")
