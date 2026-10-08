"""
Escultura en voxeles de 1 px -> Modelo de Blockbench.

Se esculpe en una grilla de celdas (x, y, z) de 1 px; cada celda tiene color y hueso.
Al exportar, las celdas de cada grupo se funden en cajas grandes (menos cubos, misma silueta),
solo se texturizan las caras que se ven, y cada texel toma el color de su celda con
oclusion ambiental (rincones mas oscuros), asi el volumen se lee aunque no haya luz.
"""

import math

from .modelo import Modelo
from .textura import hex_a_rgba, tono

VECINOS6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0),
          "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
TANGENTES = {"north": ((1, 0, 0), (0, 1, 0)), "south": ((1, 0, 0), (0, 1, 0)),
             "east": ((0, 0, 1), (0, 1, 0)), "west": ((0, 0, 1), (0, 1, 0)),
             "up": ((1, 0, 0), (0, 0, 1)), "down": ((1, 0, 0), (0, 0, 1))}


def _rgba(c):
    return hex_a_rgba(c) if isinstance(c, str) else tuple(c)


class Voxeles:
    def __init__(self):
        self.c = {}            # (x, y, z) -> (rgba, grupo)  grupo = "Hueso/subgrupo"

    # ------------------------------------------------------------------ edicion
    def poner(self, x, y, z, color, grupo, pisar=True):
        k = (int(x), int(y), int(z))
        if color is None or (not pisar and k in self.c):
            return
        self.c[k] = (_rgba(color), grupo)

    def caja(self, x1, y1, z1, x2, y2, z2, color, grupo, pisar=True):
        """Celdas de [x1, x2) x [y1, y2) x [z1, z2). color = valor o funcion(x, y, z)."""
        for x in range(int(x1), int(x2)):
            for y in range(int(y1), int(y2)):
                for z in range(int(z1), int(z2)):
                    col = color(x, y, z) if callable(color) else color
                    self.poner(x, y, z, col, grupo, pisar)

    def quitar(self, x, y, z):
        self.c.pop((int(x), int(y), int(z)), None)

    def hay(self, x, y, z):
        return (x, y, z) in self.c

    def hueso(self, k):
        v = self.c.get(k)
        return v[1].split("/")[0] if v else None

    def linea(self, p0, p1, color, grupo, grosor=0, pisar=True):
        """Linea de voxeles entre dos puntos (para hojas, plumas, varas...)."""
        n = int(max(abs(p1[i] - p0[i]) for i in range(3))) + 1
        for k in range(n + 1):
            t = k / max(1, n)
            p = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
            col = color(t) if callable(color) else color
            for dx in range(-grosor, grosor + 1):
                for dy in range(-grosor, grosor + 1):
                    self.poner(math.floor(p[0]) + dx, math.floor(p[1]) + dy, math.floor(p[2]), col, grupo, pisar)

    def espejar_x(self, prefijo_grupo=None):
        """Copia lo que hay en x >= 0 al lado x < 0 (espejo exacto). Cambia Right <-> Left en el grupo."""
        nuevos = {}
        for (x, y, z), (col, g) in self.c.items():
            if x >= 0 and (prefijo_grupo is None or g.startswith(prefijo_grupo)):
                g2 = g.replace("Right", "\0").replace("Left", "Right").replace("\0", "Left")
                nuevos[(-x - 1, y, z)] = (col, g2)
        self.c.update(nuevos)

    # ------------------------------------------------------------------ exportar
    def a_modelo(self, nombre, pivotes, ao=0.075):
        m = Modelo(nombre)
        m.pivotes.update(pivotes)
        por_grupo = {}
        for k, (_, g) in self.c.items():
            por_grupo.setdefault(g, set()).add(k)
        c = self.c

        def pintor(t):
            n = NORMAL[t.cara]
            k = (math.floor(t.x - n[0] * 0.5), math.floor(t.y - n[1] * 0.5), math.floor(t.z - n[2] * 0.5))
            v = c.get(k)
            if not v:
                return (255, 0, 255, 255)
            col, g = v
            fuera = (k[0] + n[0], k[1] + n[1], k[2] + n[2])
            f = 1.0
            otro = c.get(fuera)
            if otro and otro[1].split("/")[0] != g.split("/")[0]:
                f *= 0.72                                    # tapado por otra parte del cuerpo
            for tx, ty, tz in TANGENTES[t.cara]:
                for s in (1, -1):
                    if (fuera[0] + tx * s, fuera[1] + ty * s, fuera[2] + tz * s) in c:
                        f -= ao                              # rincon: oclusion ambiental
            if t.cara == "up":
                f *= 1.04
            elif t.cara == "down":
                f *= 0.85
            return tono(col, max(0.55, f)) if f != 1.0 else col

        for grupo in sorted(por_grupo):
            celdas = por_grupo[grupo]
            hueso = grupo.split("/")[0]
            for n, ((x1, y1, z1), (x2, y2, z2)) in enumerate(fusionar(celdas)):
                caras = []
                for cara, (nx, ny, nz) in NORMAL.items():
                    if _cara_visible(c, hueso, x1, y1, z1, x2, y2, z2, nx, ny, nz):
                        caras.append(cara)
                if caras:
                    m.cubo(grupo, f"{grupo.split('/')[-1].lower()}_{n}", (x1, y1, z1), (x2, y2, z2),
                           pintor, caras=tuple(caras))
        return m


def _cara_visible(c, hueso, x1, y1, z1, x2, y2, z2, nx, ny, nz):
    if nx:
        xs = [x2 if nx > 0 else x1 - 1]
        rx, ry, rz = xs, range(y1, y2), range(z1, z2)
    elif ny:
        rx, ry, rz = range(x1, x2), [y2 if ny > 0 else y1 - 1], range(z1, z2)
    else:
        rx, ry, rz = range(x1, x2), range(y1, y2), [z2 if nz > 0 else z1 - 1]
    for x in rx:
        for y in ry:
            for z in rz:
                v = c.get((x, y, z))
                if v is None or v[1].split("/")[0] != hueso:
                    return True
    return False


def fusionar(celdas):
    """Une celdas en cajas grandes (codicioso: x, luego z, luego y). Devuelve [(desde, hasta)]."""
    resto = set(celdas)
    cajas = []
    for (i, y, j) in sorted(celdas, key=lambda c: (c[1], c[2], c[0])):
        if (i, y, j) not in resto:
            continue
        i2 = i
        while (i2 + 1, y, j) in resto:
            i2 += 1
        j2 = j
        while all((ii, y, j2 + 1) in resto for ii in range(i, i2 + 1)):
            j2 += 1
        y2 = y
        while all((ii, y2 + 1, jj) in resto for ii in range(i, i2 + 1) for jj in range(j, j2 + 1)):
            y2 += 1
        for ii in range(i, i2 + 1):
            for yy in range(y, y2 + 1):
                for jj in range(j, j2 + 1):
                    resto.discard((ii, yy, jj))
        cajas.append(((i, y, j), (i2 + 1, y2 + 1, j2 + 1)))
    return cajas


# ---------------------------------------------------------------------------- secciones 2D


def borde_seccion(sec):
    """Celdas (x, z) de la seccion que tocan el exterior."""
    return [(x, z) for (x, z) in sec
            if (x + 1, z) not in sec or (x - 1, z) not in sec or (x, z + 1) not in sec or (x, z - 1) not in sec]


def anillo(sec, d_in, d_out):
    """Celdas (x, z) fuera de 'sec' cuya distancia euclidea a la seccion esta en (d_in, d_out].
    Con distancia euclidea las esquinas salen redondeadas (mas organico que un rectangulo)."""
    if not sec:
        return {}
    borde = borde_seccion(sec)
    xs = [p[0] for p in sec]
    zs = [p[1] for p in sec]
    r = int(math.ceil(d_out)) + 1
    out = {}
    for x in range(min(xs) - r, max(xs) + r + 1):
        for z in range(min(zs) - r, max(zs) + r + 1):
            if (x, z) in sec:
                continue
            d = min(math.hypot(x - bx, z - bz) for bx, bz in borde)
            if d_in < d <= d_out:
                out[(x, z)] = d
    return out
