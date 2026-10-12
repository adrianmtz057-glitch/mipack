"""
Pixel art de las particulas y los iconos de los efectos de Khaset (todo dibujado con codigo, sin ruido al azar):
  - particulas (textures/particle, 8x8 por cuadro; cada una con su particles/<nombre>.json):
      veneno   4 cuadros: una bocanada verde que se abre y se desvanece (lo que dejan los dardos)
      sangre   4 cuadros: la gota redonda, alargada al caer y la salpicadura (desangrado)
      brasa    3 cuadros: chispas de fuego que titilan
      pluma    4 cuadros: una pluma turquesa del penacho que se quema hasta hacerse brasa (corona rota)
      ceniza   3 cuadros: copos grises (el rastro que deja al pisar con calor)
  - iconos de efectos (textures/mob_effect, 18x18): desangrado (animado: la gota late y escurre), derribado,
    aturdido (animado: estrellas que giran) y desorientado (animado: un remolino).
Uso: python -m taller.particulas  (escribe en mod/src/main/resources/assets/mipack/)
"""

import json
import math
import os

from PIL import Image

RAIZ = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources", "assets", "mipack")
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def _hex(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def _lienzo(n=8):
    return Image.new("RGBA", (n, n), (0, 0, 0, 0))


def _disco(img, cx, cy, r, color, borde=None):
    for y in range(img.height):
        for x in range(img.width):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                img.putpixel((x, y), borde if borde and d > r - 1.0 else color)


# ---------------------------------------------------------------- particulas

def veneno():
    claro, medio, oscuro = _hex("#B8F06A"), _hex("#6FC23C"), _hex("#2F7A3A")
    out = []
    for k in range(4):
        img = _lienzo()
        r = 1.6 + k * 0.75
        alfa = 255 - k * 45
        for y in range(8):
            for x in range(8):
                d = math.hypot(x + 0.5 - 4, y + 0.5 - 4.2)
                if d > r:
                    continue
                f = d / r + (BAYER[y % 4][x % 4] / 16 - 0.5) * 0.5
                if k >= 2 and f > 0.55 and BAYER[y % 4][x % 4] > 8 + 2 * k:
                    continue                                   # se deshace en puntos
                c = claro if f < 0.35 else medio if f < 0.75 else oscuro
                img.putpixel((x, y), c[:3] + (alfa,))
        out.append(img)
    return out


def sangre():
    claro, medio, oscuro = _hex("#E0303A"), _hex("#A1141E"), _hex("#5C0910")
    out = []
    # la gota redonda
    img = _lienzo()
    _disco(img, 4, 4.5, 2.2, medio, oscuro)
    img.putpixel((3, 3), claro)
    out.append(img)
    # alargada (cayendo)
    img = _lienzo()
    for y in range(1, 8):
        w = 1.0 if y < 3 else 1.6 if y < 5 else 2.0
        for x in range(8):
            if abs(x + 0.5 - 4) <= w - 0.3:
                img.putpixel((x, y), oscuro if y == 7 or abs(x + 0.5 - 4) > w - 1.0 else medio)
    img.putpixel((3, 4), claro)
    out.append(img)
    # la salpicadura
    for k in range(2):
        img = _lienzo()
        for x in range(8):
            if abs(x + 0.5 - 4) < 3.5 - k:
                img.putpixel((x, 6), medio if 1 < x < 6 else oscuro)
        for (x, y) in ((1, 5 - k), (6, 5 - k), (2, 4 - 2 * k), (5, 4 - 2 * k)):
            img.putpixel((x, max(0, y)), medio)
        img.putpixel((3, 7), oscuro)
        img.putpixel((4, 7), oscuro)
        out.append(img)
    return out


def brasa():
    blanco, amarillo, naranja, rojo = _hex("#FFF4C8"), _hex("#FFD24A"), _hex("#F06A1E"), _hex("#A82410")
    out = []
    for k, r in enumerate((2.0, 1.4, 2.4)):
        img = _lienzo()
        for y in range(8):
            for x in range(8):
                d = math.hypot(x + 0.5 - 4, y + 0.5 - 4)
                if d < r * 0.45:
                    img.putpixel((x, y), blanco)
                elif d < r * 0.8:
                    img.putpixel((x, y), amarillo)
                elif d < r:
                    img.putpixel((x, y), naranja)
                elif d < r + 0.8 and (x + y + k) % 2 == 0:
                    img.putpixel((x, y), rojo[:3] + (150,))
        out.append(img)
    return out


def pluma():
    turq, turq_c, turq_o = _hex("#22AA9C"), _hex("#5FD6C3"), _hex("#0E5550")
    verde, oro = _hex("#2E7D4F"), _hex("#D6A13A")
    fuego, brasa_, ceniza = _hex("#F06A1E"), _hex("#FFD24A"), _hex("#4A4044")
    out = []
    for k in range(4):
        img = _lienzo()
        quema = k / 3.0                                       # cuanto de la pluma ya se quemo (desde la punta)
        for y in range(8):
            for x in range(8):
                u = x + 0.5 - 4
                v = (7.5 - y) / 7.0                            # 0 abajo (canon) a 1 arriba (punta)
                ancho = 0.6 + 2.2 * math.sin(math.pi * min(1.0, v * 1.1))
                if abs(u) > ancho or v > 0.98:
                    continue
                if v > 1.0 - quema:
                    frente = 1.0 - quema
                    c = brasa_ if v - frente < 0.12 else fuego if v - frente < 0.25 else ceniza
                    if v - frente > 0.25 and BAYER[y % 4][x % 4] > 9:
                        continue
                elif v < 0.14:
                    c = oro
                elif v > 0.82:
                    c = verde
                elif abs(u) < 0.5:
                    c = turq_c
                else:
                    c = turq if abs(u) < ancho - 0.8 else turq_o
                img.putpixel((x, y), c)
        out.append(img)
    return out


def ceniza():
    claro, medio, oscuro = _hex("#9A9094"), _hex("#6A6064"), _hex("#3A3236")
    formas = (((3, 3), (4, 3), (3, 4), (4, 4), (5, 4)), ((2, 4), (3, 4), (4, 3), (5, 3)), ((4, 2), (3, 3), (4, 3), (4, 4), (3, 5)))
    out = []
    for k, puntos in enumerate(formas):
        img = _lienzo()
        for i, p in enumerate(puntos):
            img.putpixel(p, (claro, medio, oscuro)[(i + k) % 3])
        out.append(img)
    return out


PARTICULAS = {"veneno": veneno, "sangre": sangre, "brasa": brasa, "pluma": pluma, "ceniza": ceniza}


# ---------------------------------------------------------------- iconos de efectos (18x18)

def _gota(img, cx, cy, r, colores, estira=1.0):
    claro, medio, oscuro = colores
    for y in range(img.height):
        for x in range(img.width):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if dy < 0:                                           # la punta de arriba
                dentro = abs(dx) <= r * (1 + dy / (r * 1.9 * estira)) and dy > -r * 1.9 * estira
            else:
                dentro = math.hypot(dx, dy) <= r
            if dentro:
                borde = math.hypot(dx, max(dy, 0)) > r - 1.0 or (dy < 0 and abs(dx) > r * (1 + dy / (r * 1.9 * estira)) - 1)
                img.putpixel((x, y), oscuro if borde else medio)
    img.putpixel((int(cx - r * 0.4), int(cy - r * 0.2)), claro)


def icono_desangrado():
    """8 cuadros: la gota late (crece y se encoge) y una gotita escurre hacia abajo."""
    col = (_hex("#FF6A6A"), _hex("#C0141E"), _hex("#5C0910"))
    tira = Image.new("RGBA", (18, 18 * 8), (0, 0, 0, 0))
    for k in range(8):
        img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        late = 1.0 + 0.12 * math.sin(2 * math.pi * k / 8)
        _gota(img, 9, 10, 4.6 * late, col)
        y = 3 + k * 2
        if y < 17:
            img.putpixel((13, min(17, y)), col[1])
            if y + 1 < 18:
                img.putpixel((13, y + 1), col[2])
        tira.paste(img, (0, 18 * k))
    return tira, {"animation": {"frametime": 3}}


def icono_derribado():
    """Una figura de rodillas con un corte en las piernas."""
    img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    piel, sombra, rojo = _hex("#D9B08C"), _hex("#7A5A44"), _hex("#C0141E")
    for (x0, y0, x1, y1, c) in ((7, 2, 10, 5, piel), (6, 6, 11, 11, sombra), (4, 6, 5, 10, piel), (12, 6, 13, 10, piel),
                                (6, 12, 11, 13, sombra), (5, 14, 12, 15, sombra)):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                img.putpixel((x, y), c)
    for i in range(7):
        img.putpixel((3 + i * 2 // 1 if 3 + i * 2 < 18 else 17, 16 - i // 2), rojo)
    return img, None


def icono_aturdido():
    """6 cuadros: tres estrellas giran sobre una cabeza."""
    tira = Image.new("RGBA", (18, 18 * 6), (0, 0, 0, 0))
    amarillo, naranja, piel = _hex("#FFE15A"), _hex("#E0902A"), _hex("#D9B08C")
    for k in range(6):
        img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        for y in range(10, 17):
            for x in range(5, 13):
                img.putpixel((x, y), piel if 0 < x - 5 < 7 else _hex("#7A5A44"))
        for s in range(3):
            a = 2 * math.pi * (k / 6 + s / 3)
            cx, cy = 9 + 6 * math.cos(a), 6 + 2.5 * math.sin(a)
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                x, y = int(cx + dx), int(cy + dy)
                if 0 <= x < 18 and 0 <= y < 18:
                    img.putpixel((x, y), amarillo if (dx, dy) == (0, 0) else naranja)
        tira.paste(img, (0, 18 * k))
    return tira, {"animation": {"frametime": 2}}


def icono_desorientado():
    """8 cuadros: un remolino que gira."""
    tira = Image.new("RGBA", (18, 18 * 8), (0, 0, 0, 0))
    claro, medio, oscuro = _hex("#C9A8FF"), _hex("#8A5CE0"), _hex("#3E2272")
    for k in range(8):
        img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        for i in range(60):
            t = i / 60
            a = 2 * math.pi * (t * 2.2 + k / 8)
            r = 1.0 + 7.0 * t
            x, y = int(9 + r * math.cos(a)), int(9 + r * math.sin(a))
            if 0 <= x < 18 and 0 <= y < 18:
                img.putpixel((x, y), claro if t < 0.3 else medio if t < 0.7 else oscuro)
        tira.paste(img, (0, 18 * k))
    return tira, {"animation": {"frametime": 2}}


ICONOS = {"desangrado": icono_desangrado, "derribado": icono_derribado, "aturdido": icono_aturdido,
          "desorientado": icono_desorientado}


def avisos(lado=128):
    """El circulo de aviso de Khaset en blanco (el mod lo tine): un anillo con una raya adentro y el disco que se llena."""
    anillo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lleno = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    c = (lado - 1) / 2
    for y in range(lado):
        for x in range(lado):
            r = math.hypot(x - c, y - c) / (lado / 2)
            if r > 1.0:
                continue
            borde = max(0.0, 1 - abs(r - 0.94) / 0.06)
            interior = max(0.0, 1 - abs(r - 0.55) / 0.025) * 0.5
            a = max(borde, interior, 0.14)
            anillo.putpixel((x, y), (255, 255, 255, int(255 * a)))
            a2 = 0.9 if r > 0.93 else 0.35 + 0.45 * r ** 3
            lleno.putpixel((x, y), (255, 255, 255, int(255 * a2)))
    return anillo, lleno


def vineta(lado=256):
    """Una vineta blanca (transparente al centro, opaca en las orillas) para teñir la pantalla: sangre y calor."""
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    c = (lado - 1) / 2
    for y in range(lado):
        for x in range(lado):
            r = math.hypot((x - c) / c, (y - c) / c) / math.sqrt(2)
            a = max(0.0, min(1.0, (r - 0.35) / 0.65)) ** 1.6
            img.putpixel((x, y), (255, 255, 255, int(255 * a)))
    return img


def main():
    carpeta = os.path.join(RAIZ, "textures", "particle")
    os.makedirs(carpeta, exist_ok=True)
    os.makedirs(os.path.join(RAIZ, "particles"), exist_ok=True)
    for nombre, f in PARTICULAS.items():
        cuadros = f()
        nombres = []
        for k, img in enumerate(cuadros):
            img.save(os.path.join(carpeta, f"{nombre}_{k}.png"))
            nombres.append(f"mipack:{nombre}_{k}")
        with open(os.path.join(RAIZ, "particles", f"{nombre}.json"), "w") as fh:
            json.dump({"textures": nombres}, fh, indent=2)
    carpeta = os.path.join(RAIZ, "textures", "mob_effect")
    os.makedirs(carpeta, exist_ok=True)
    for nombre, f in ICONOS.items():
        img, meta = f()
        img.save(os.path.join(carpeta, f"{nombre}.png"))
        if meta:
            with open(os.path.join(carpeta, f"{nombre}.png.mcmeta"), "w") as fh:
                json.dump(meta, fh, indent=2)
    anillo, lleno = avisos()
    anillo.save(os.path.join(RAIZ, "textures", "entity", "aviso.png"))
    lleno.save(os.path.join(RAIZ, "textures", "entity", "aviso_lleno.png"))
    os.makedirs(os.path.join(RAIZ, "textures", "misc"), exist_ok=True)
    vineta().save(os.path.join(RAIZ, "textures", "misc", "vineta.png"))
    print("particulas:", list(PARTICULAS), "iconos:", list(ICONOS))


if __name__ == "__main__":
    main()
