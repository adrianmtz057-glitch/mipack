"""Texturas 64x64 (cuerpo humano, como el zombi) del ejercito de La Bruma: armadura azteca negra con mura morada.
Salen a mod/src/main/resources/assets/mipack/textures/entity/{soldado_bruma,arquero_bruma,soldado_grande}.png."""
import os, random
from PIL import Image

SALIDA = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources", "assets", "mipack", "textures", "entity")
PIEL, PIEL2 = (42, 32, 38), (30, 23, 28)
NEGRO, NEGRO2 = (20, 18, 24), (34, 31, 40)
MURA, MURA2 = (122, 58, 168), (176, 108, 230)
ORO = (201, 162, 58)


def caja(px, u, v, w, h, d, pintar):
    """Pinta las 6 caras de una caja de Minecraft (w ancho, h alto, d fondo) con pintar(cara, x, y, ancho, alto)."""
    caras = {"arriba": (u + d, v, w, d), "abajo": (u + d + w, v, w, d), "der": (u, v + d, d, h),
             "frente": (u + d, v + d, w, h), "izq": (u + d + w, v + d, d, h), "atras": (u + d + w + d, v + d, w, h)}
    for cara, (x0, y0, cw, ch) in caras.items():
        for y in range(ch):
            for x in range(cw):
                c = pintar(cara, x, y, cw, ch)
                if c is not None:
                    px[x0 + x, y0 + y] = c + (255,) if len(c) == 3 else c


def ruido(c, r, k=6):
    v = r.randint(-k, k)
    return tuple(max(0, min(255, a + v)) for a in c)


def hacer(nombre, tipo):
    r = random.Random(nombre)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()
    trim = ORO if tipo == "grande" else MURA

    def cabeza(cara, x, y, w, h):
        if cara == "frente":
            if y < 3:                                   # la banda del yelmo con colmillos
                return trim if (y == 2 and x in (1, 2, 5, 6)) else ruido(NEGRO, r)
            if y == 4 and x in (2, 5):
                return MURA2                            # ojos de mura
            if y == 4 and x in (1, 6):
                return MURA if tipo == "grande" else ruido(PIEL2, r)
            if x in (0, 7):
                return ruido(NEGRO2, r)                 # carrilleras
            return ruido(PIEL, r) if y < 7 else ruido(PIEL2, r)
        if cara == "arriba":
            return ruido(NEGRO, r) if (x + y) % 3 else ruido(NEGRO2, r)
        if cara == "abajo":
            return ruido(PIEL2, r)
        return ruido(NEGRO2 if y % 3 == 0 else NEGRO, r) if y < 6 else ruido(PIEL2, r)

    def penacho(cara, x, y, w, h):                    # la capa de encima: plumas moradas atras y arriba
        if tipo == "arquero":
            if cara in ("atras", "izq", "der") and y < 3:
                return (120, 120, 128) if (x + y) % 2 else (90, 90, 98)
            return None
        if cara == "arriba" and 2 <= x <= 5:
            return MURA if (x + y) % 2 else MURA2
        if cara == "atras" and y < 5 and 2 <= x <= 5:
            return MURA if (x + y) % 2 else NEGRO
        return None

    def cuerpo(cara, x, y, w, h):
        if y >= h - 3:                                 # faja
            return trim if y == h - 3 else ruido((48, 26, 60), r)
        if tipo == "arquero":
            return ruido((58, 54, 64), r) if (x + y) % 4 else ruido((44, 41, 50), r)      # algodon acolchado
        if cara == "frente" and 1 <= x <= w - 2 and 1 <= y <= 6:
            if tipo == "grande" and 2 <= x <= 5 and 2 <= y <= 5:                         # la calavera del pecho
                return (210, 205, 190) if not (y == 3 and x in (3, 4)) else NEGRO
            return ruido(NEGRO, r) if (x + y) % 2 else ruido(NEGRO2, r)                 # placas de obsidiana
        if y == 7:
            return trim if x % 2 == 0 else NEGRO
        return ruido((52, 48, 58), r) if (x // 2 + y // 2) % 2 else ruido((40, 37, 45), r)

    def brazo(cara, x, y, w, h):
        if cara == "arriba" or y < 4:
            return ruido(NEGRO, r) if y != 3 else trim  # hombrera
        if y >= 8:
            return ruido(NEGRO2, r) if y not in (8, 11) else trim   # brazal
        return ruido(PIEL, r)

    def pierna(cara, x, y, w, h):
        if y < 4:
            return ruido((48, 26, 60), r) if cara in ("frente", "atras") else ruido(NEGRO2, r)   # taparrabo
        if y >= 6:
            return ruido(NEGRO, r) if y not in (6, 11) else trim    # grebas y sandalia
        return ruido(PIEL, r)

    caja(px, 0, 0, 8, 8, 8, cabeza)
    caja(px, 32, 0, 8, 8, 8, penacho)
    caja(px, 16, 16, 8, 12, 4, cuerpo)
    caja(px, 40, 16, 4, 12, 4, brazo)
    caja(px, 0, 16, 4, 12, 4, pierna)
    os.makedirs(SALIDA, exist_ok=True)
    img.save(os.path.join(SALIDA, nombre + ".png"))
    return img


if __name__ == "__main__":
    hoja = Image.new("RGBA", (64 * 3 * 4, 64 * 4), (40, 40, 40, 255))
    for i, (n, t) in enumerate((("soldado_bruma", "soldado"), ("arquero_bruma", "arquero"), ("soldado_grande", "grande"))):
        hoja.paste(hacer(n, t).resize((256, 256), Image.NEAREST), (i * 256, 0))
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "salida", "bruma"), exist_ok=True)
    hoja.save(os.path.join(os.path.dirname(__file__), "..", "salida", "bruma", "soldados_texturas.png"))
