"""
Colores, ruido y lienzo de textura (PNG) sin dependencias externas.

Todo el pintado del modelo pasa por aqui: cada texel de cada cara se pinta con una
funcion "pintor" que recibe la posicion 3D del texel en el modelo (en px de Blockbench),
asi la ropa, el pelo o los patrones se describen por su lugar en el cuerpo y no por
coordenadas UV.
"""

import struct
import zlib

# ----------------------------------------------------------------------------- colores

RGBA = tuple  # (r, g, b, a) 0..255


def hex_a_rgba(h, a=255) -> RGBA:
    if isinstance(h, (tuple, list)):
        return tuple(h) if len(h) == 4 else (h[0], h[1], h[2], a)
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
    except (ValueError, IndexError):
        return (255, 0, 255, a)          # magenta: color invalido, salta a la vista


def es_hex(h) -> bool:
    h = str(h).strip().lstrip("#")
    return len(h) in (3, 6) and all(c in "0123456789abcdefABCDEF" for c in h)


def a_hex(c: RGBA) -> str:
    return "#%02X%02X%02X" % tuple(c[:3])


def _cl(v):
    return 0 if v < 0 else (255 if v > 255 else int(round(v)))


def tono(c, f: float) -> RGBA:
    """Aclara (f > 1) u oscurece (f < 1) conservando un poco de saturacion en las sombras."""
    c = hex_a_rgba(c) if isinstance(c, str) else c
    if f < 1:
        # sombras levemente mas frias/saturadas, como en el pixel art de Minecraft
        r, g, b = c[0] * f, c[1] * f, c[2] * (f + (1 - f) * 0.15)
    else:
        r, g, b = (v + (255 - v) * (f - 1) * 0.6 for v in c[:3])
    return (_cl(r), _cl(g), _cl(b), c[3])


def mezcla(a, b, t: float) -> RGBA:
    a = hex_a_rgba(a) if isinstance(a, str) else a
    b = hex_a_rgba(b) if isinstance(b, str) else b
    return tuple(_cl(a[i] + (b[i] - a[i]) * t) for i in range(4))


def con_alfa(c, a: int) -> RGBA:
    c = hex_a_rgba(c) if isinstance(c, str) else c
    return (c[0], c[1], c[2], a)


TRANSPARENTE = (0, 0, 0, 0)

# ----------------------------------------------------------------------------- ruido


def azar(*valores) -> float:
    """Hash entero determinista -> [0, 1). Mismo resultado en cualquier PC."""
    n = 0x811C9DC5
    for v in valores:
        n ^= int(v) & 0xFFFFFFFF
        n = (n * 0x01000193) & 0xFFFFFFFF
        n ^= n >> 15
        n = (n * 0x2C1B3C6D) & 0xFFFFFFFF
        n ^= n >> 12
    n = (n * 0x297A2D39) & 0xFFFFFFFF
    n ^= n >> 15
    return n / 4294967296.0


def _suave(t):
    return t * t * (3 - 2 * t)


def ruido(x, y, z, escala=3.0, semilla=0) -> float:
    """Ruido de valor 3D suave en [0, 1) (manchas grandes)."""
    x, y, z = x / escala, y / escala, z / escala
    xi, yi, zi = int(x // 1), int(y // 1), int(z // 1)
    fx, fy, fz = _suave(x - xi), _suave(y - yi), _suave(z - zi)

    def v(a, b, c):
        return azar(semilla, xi + a, yi + b, zi + c)

    def l(a, b, t):
        return a + (b - a) * t

    return l(l(l(v(0, 0, 0), v(1, 0, 0), fx), l(v(0, 1, 0), v(1, 1, 0), fx), fy),
             l(l(v(0, 0, 1), v(1, 0, 1), fx), l(v(0, 1, 1), v(1, 1, 1), fx), fy), fz)


# ----------------------------------------------------------------------------- lienzo


class Lienzo:
    def __init__(self, ancho: int, alto: int):
        self.ancho, self.alto = ancho, alto
        self.px = bytearray(ancho * alto * 4)

    def poner(self, x: int, y: int, c: RGBA):
        if 0 <= x < self.ancho and 0 <= y < self.alto:
            i = (y * self.ancho + x) * 4
            self.px[i:i + 4] = bytes((_cl(c[0]), _cl(c[1]), _cl(c[2]), _cl(c[3] if len(c) > 3 else 255)))

    def leer(self, x: int, y: int) -> RGBA:
        i = (y * self.ancho + x) * 4
        return tuple(self.px[i:i + 4])

    def recortar(self, alto: int):
        self.px = self.px[:self.ancho * alto * 4]
        self.alto = alto

    def png(self) -> bytes:
        filas = b"".join(b"\x00" + bytes(self.px[y * self.ancho * 4:(y + 1) * self.ancho * 4])
                         for y in range(self.alto))

        def trozo(tipo, datos):
            c = struct.pack(">I", len(datos)) + tipo + datos
            return c + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)

        return (b"\x89PNG\r\n\x1a\n"
                + trozo(b"IHDR", struct.pack(">IIBBBBB", self.ancho, self.alto, 8, 6, 0, 0, 0))
                + trozo(b"IDAT", zlib.compress(filas, 9)) + trozo(b"IEND", b""))
