"""
Herramientas de bloques compartidas por los personajes (antes vivian en revolthir.py): color liso, la textura de
bloques de 1 px (voxel) y el tubo de 'lados' caras en cualquier direccion. No es un personaje (no tiene construir()).
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_

BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def color(hexa):
    c = hex_(hexa)
    return lambda t: c


def voxel(rampa, claro=0.0, alto=None):
    """Textura de bloques de 1 px: cada bloque toma un tono de la rampa (sombra, base, medio, luz) segun la altura
    dentro de la pieza (mas claro arriba), unas ondas suaves y una matriz de Bayer. Siempre el mismo patron.
    alto=(y0, y1): la altura se mide en ese tramo y no en la pieza, para que dos piezas pegadas se vean como una."""
    s, b, l = hex_(rampa["s"]), hex_(rampa["b"]), hex_(rampa["l"])
    medio = tuple((x + y) // 2 for x, y in zip(b, l))
    tonos4 = (s, b, medio, l)

    def p(t):
        if t.cara in ("up", "down"):
            u, v = t.x, t.z
            r = 1.0 if t.cara == "up" else 0.0
        else:
            u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
            v = t.y
            y0, y1 = alto or (t.f[1], t.t[1])
            r = (t.y - y0) / max(1e-6, y1 - y0)
        cu, cv = math.floor(u + 100), math.floor(v + 100)
        f = 0.5 + 0.2 * math.sin(cu * 0.9 + cv * 0.5) * math.cos(cv * 0.8 - cu * 0.35) + 0.28 * (r - 0.5) + claro
        f += ((BAYER[cv % 4][cu % 4] + 0.5) / 16 - 0.5) * 0.4
        return tonos4[0 if f < 0.22 else 1 if f < 0.6 else 2 if f < 0.8 else 3]
    return p


def tubo(p0, p1, r0, r1, lados=6):
    """Cono truncado de 'lados' caras que va de p0 (radio r0) a p1 (radio r1), en cualquier direccion."""
    d = [p1[i] - p0[i] for i in range(3)]
    largo = math.sqrt(sum(c * c for c in d))
    vs, cs = geo.loft([(0.0, 0, 0, r0, r0), (largo, 0, 0, r1, r1)], lados, 30)
    ux, uy, uz = (c / largo for c in d)
    eje = (uz, 0.0, -ux)                                       # (0, 1, 0) x u: el giro que lleva +Y a la direccion
    seno = math.sqrt(eje[0] ** 2 + eje[2] ** 2)
    coseno = uy
    if seno > 1e-9:
        kx, kz = eje[0] / seno, eje[2] / seno

        def girar(v):                                          # Rodrigues alrededor de (kx, 0, kz)
            x, y, z = v
            kv = kx * x + kz * z
            cx, cy, cz = -kz * y, kz * x - kx * z, kx * y        # k x v
            return (x * coseno + cx * seno + kx * kv * (1 - coseno), y * coseno + cy * seno,
                    z * coseno + cz * seno + kz * kv * (1 - coseno))
        vs = [girar(v) for v in vs]
    return [(x + p0[0], y + p0[1], z + p0[2]) for x, y, z in vs], cs
