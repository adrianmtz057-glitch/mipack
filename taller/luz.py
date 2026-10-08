"""
Luz horneada: le da volumen a CUALQUIER modelo (cubos, planos y mallas) sin saber nada del personaje.

Despues de que el pintor de una cara da el color de cada texel, el motor lo corre unos PASOS de su propia rampa
(hue shifting: la sombra se va hacia el azul/violeta y se satura, la luz se va hacia el amarillo) segun la geometria
de todo el modelo, en pose de reposo:
  - oclusion de contacto: donde otra pieza tapa el cielo del texel (pelo sobre la frente, ropa sobre el cuerpo,
    el cuello bajo la cabeza, entre las piernas...)
  - sombra proyectada de una luz que viene de arriba, un poco de frente y de la derecha del personaje
  - canto con luz arriba y contorno abajo en cada cara de costado
La oclusion y la sombra se calculan en una grilla gruesa sobre cada cara y se interpolan, asi las bandas salen
limpias y parejas (nada de ruido ni dithering). Todo en Python puro.
"""

import colorsys
import math
from functools import lru_cache

LUZ = (0.35, 1.0, -0.45)                 # de donde viene la luz (arriba, de frente, de la derecha del personaje)
RADIO_OCLUSION = 3.5                     # px: hasta donde una pieza cercana oscurece
LARGO_SOMBRA = 40.0                      # px: hasta donde llega la sombra proyectada
PASO_GRILLA = 0.5                        # px entre muestras de la grilla de cada cara
UMBRAL_1, UMBRAL_2 = 0.22, 0.45          # oclusion para bajar 1 y 2 pasos
DE_CARA = 0.55                           # lo que mira asi de derecho a la luz y no esta tapado sube un paso
SEPARACION = 0.02                        # px: las muestras salen un poco de la cara para no chocar con ella misma


def _norm(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _punto(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


L = _norm(LUZ)


def rot_matriz(rx, ry, rz):
    """Matriz de giro de Blockbench (orden Z * Y * X), en grados."""
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    X = ((1, 0, 0), (0, ca, -sa), (0, sa, ca))
    Y = ((cb, 0, sb), (0, 1, 0), (-sb, 0, cb))
    Z = ((cc, -sc, 0), (sc, cc, 0), (0, 0, 1))

    def mul(P, Q):
        return tuple(tuple(sum(P[i][k] * Q[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mul(mul(Z, Y), X)


def _aplicar(R, v):
    return (R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
            R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
            R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2])


def _aplicar_t(R, v):                     # traspuesta = giro inverso
    return (R[0][0] * v[0] + R[1][0] * v[1] + R[2][0] * v[2],
            R[0][1] * v[0] + R[1][1] * v[1] + R[2][1] * v[2],
            R[0][2] * v[0] + R[1][2] * v[1] + R[2][2] * v[2])


# ---------------------------------------------------------------- colores: pasos de rampa con hue shifting

def _hacia(h, objetivo, t):
    d = ((objetivo - h + 0.5) % 1.0) - 0.5
    return (h + d * t) % 1.0


@lru_cache(maxsize=65536)
def paso(c, k):
    """El color c (RGBA) corrido k pasos de su rampa: k < 0 sombra (mas oscura, fria y saturada), k > 0 luz (mas
    clara y calida). En los negros y grises la sombra igual se nota un poco (se van al azul) y la luz levanta poco."""
    if k == 0 or c[3] == 0:
        return c
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    gris = s < 0.08
    if k < 0:
        n = -k
        if gris:
            h, s = 0.68, s + 0.06 * n
        else:
            h, s = _hacia(h, 0.68, 0.08 * n), s + (1 - s) * 0.12 * n
        v = v * (1 - 0.17 * n)
    else:
        if gris:
            h, s = 0.11, s + 0.03 * k
        else:
            h, s = _hacia(h, 0.13, 0.07 * k), s * (1 - 0.1 * k)
        v = v + ((1 - v) * 0.35 * v + 0.04) * k
    r, g, b = colorsys.hsv_to_rgb(h, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return (round(r * 255), round(g * 255), round(b * 255), c[3])


# ---------------------------------------------------------------- piezas que tapan (cajas y triangulos)

CARA_DE_EJE = (("west", "east"), ("down", "up"), ("north", "south"))   # (cara del lado min, cara del lado max)


class _Caja:
    """Un cubo (o plano) del modelo. Un rayo solo choca donde la cara tiene un texel opaco."""
    __slots__ = ("lo", "hi", "R", "o", "alo", "ahi", "dueno", "caras", "opaco")

    def __init__(self, c, opaco):
        from .modelo import esquinas            # aca y no arriba: modelo.py importa este modulo
        lo, hi, o = tuple(c.desde), tuple(c.hasta), tuple(c.origen)
        R = rot_matriz(*c.rot) if c.rot else None
        self.lo, self.hi, self.R, self.o, self.dueno, self.opaco = lo, hi, R, o, id(c), opaco
        self.caras = {}
        for cara in c.caras:
            tl, tr, bl = esquinas(lo, hi, cara)
            du = (tr[0] - tl[0], tr[1] - tl[1], tr[2] - tl[2])
            dv = (bl[0] - tl[0], bl[1] - tl[1], bl[2] - tl[2])
            self.caras[cara] = (tl, du, _punto(du, du) or 1.0, dv, _punto(dv, dv) or 1.0)
        pts = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        if R is not None:
            pts = [tuple(o[i] + w[i] for i in range(3)) for w in
                   (_aplicar(R, (p[0] - o[0], p[1] - o[1], p[2] - o[2])) for p in pts)]
        self.alo = tuple(min(p[i] for p in pts) for i in range(3))
        self.ahi = tuple(max(p[i] for p in pts) for i in range(3))

    def choca(self, p, d, tmax):
        if self.R is not None:
            o = self.o
            p = _aplicar_t(self.R, (p[0] - o[0], p[1] - o[1], p[2] - o[2]))
            p = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
            d = _aplicar_t(self.R, d)
        lo, hi = self.lo, self.hi
        t0, t1, e0, e1 = -1e30, 1e30, None, None
        for i in range(3):
            if -1e-12 < d[i] < 1e-12:
                if p[i] < lo[i] - 1e-9 or p[i] > hi[i] + 1e-9:
                    return None
                continue
            a, b = (lo[i] - p[i]) / d[i], (hi[i] - p[i]) / d[i]
            entra, sale = CARA_DE_EJE[i] if d[i] > 0 else CARA_DE_EJE[i][::-1]
            if a > b:
                a, b = b, a
            if a > t0:
                t0, e0 = a, entra
            if b < t1:
                t1, e1 = b, sale
            if t0 > t1:
                return None
        for t, cara in ((t0, e0), (t1, e1)):        # entra por una cara; si ahi es transparente, prueba la otra
            if cara is None or not (1e-6 < t < tmax) or cara not in self.caras:
                continue
            tl, du, uu, dv, vv = self.caras[cara]
            q = (p[0] + d[0] * t - tl[0], p[1] + d[1] * t - tl[1], p[2] + d[2] * t - tl[2])
            if self.opaco(self.dueno, cara, _punto(q, du) / uu, _punto(q, dv) / vv):
                return t
        return None


class _Tri:
    """Un triangulo de una malla, con su UV para saber si donde choca el rayo es opaco."""
    __slots__ = ("a", "e1", "e2", "alo", "ahi", "dueno", "uv", "opaco")

    def __init__(self, a, b, c, uv, dueno, opaco):
        self.a, self.dueno, self.uv, self.opaco = a, dueno, uv, opaco
        self.e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        self.e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        self.alo = tuple(min(a[i], b[i], c[i]) for i in range(3))
        self.ahi = tuple(max(a[i], b[i], c[i]) for i in range(3))

    def choca(self, p, d, tmax):
        e1, e2 = self.e1, self.e2
        h = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0])
        det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
        if -1e-9 < det < 1e-9:
            return None
        f = 1.0 / det
        s = (p[0] - self.a[0], p[1] - self.a[1], p[2] - self.a[2])
        u = f * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
        if u < 0.0 or u > 1.0:
            return None
        q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0])
        v = f * (d[0] * q[0] + d[1] * q[1] + d[2] * q[2])
        if v < 0.0 or u + v > 1.0:
            return None
        t = f * (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2])
        if not 1e-6 < t < tmax:
            return None
        (a0, b0), (a1, b1), (a2, b2) = self.uv
        w = 1 - u - v
        return t if self.opaco(None, None, w * a0 + u * a1 + v * a2, w * b0 + u * b1 + v * b2) else None


def _solapa(alo, ahi, blo, bhi):
    return all(alo[i] <= bhi[i] and blo[i] <= ahi[i] for i in range(3))


def _suavizar(g):
    """Promedio 1-2-1 en las dos direcciones: saca el serrucho de los rayos rasantes antes de cuantizar."""
    nr, ns = len(g), len(g[0])
    if nr < 3 and ns < 3:
        return g

    def f(fila):
        n = len(fila)
        if n < 3:
            return fila[:]
        return [(fila[max(i - 1, 0)] + 2 * fila[i] + fila[min(i + 1, n - 1)]) / 4 for i in range(n)]
    h = [f(fila) for fila in g]
    cols = [f([h[b][a] for b in range(nr)]) for a in range(ns)]
    return [[cols[a][b] for a in range(ns)] for b in range(nr)]


# ---------------------------------------------------------------- rayos de la oclusion (fijos, en el marco de la cara)

def _direcciones():
    out = [(0.0, 0.0, 1.0, 1.0)]
    for th, n, giro in ((38, 6, 0), (68, 8, 22.5)):
        t = math.radians(th)
        for k in range(n):
            f = math.radians(giro + k * 360 / n)
            out.append((math.sin(t) * math.cos(f), math.sin(t) * math.sin(f), math.cos(t), math.cos(t)))
    return out


DIRECCIONES = _direcciones()


class Luz:
    """La geometria de un modelo lista para tirarle rayos. Se arma una vez por modelo antes de pintar."""

    def __init__(self, modelo, lienzo, uvs):
        px, ancho, alto = lienzo.px, lienzo.ancho, lienzo.alto
        rects = {}
        for c in modelo.cubos:
            for cara, (u1, v1, u2, v2) in uvs[id(c)].items():
                rects[(id(c), cara)] = (min(u1, u2), min(v1, v2), int(abs(u2 - u1)), int(abs(v2 - v1)), u1 > u2, v1 > v2)

        def opaco(dueno, cara, a, b):
            """Si el texel en (a, b) es opaco: en un cubo a, b son 0..1 sobre la cara; en una malla son la UV."""
            if dueno is None:
                x, y = int(a), int(b)
            else:
                x0, y0, tw, th, vu, vv = rects[(dueno, cara)]
                a = min(max(1 - a if vu else a, 0.0), 0.999999)
                b = min(max(1 - b if vv else b, 0.0), 0.999999)
                x, y = x0 + int(a * tw), y0 + int(b * th)
            if 0 <= x < ancho and 0 <= y < alto:
                return px[(y * ancho + x) * 4 + 3] > 0
            return True
        self.piezas = [_Caja(c, opaco) for c in modelo.cubos if c.luz]       # luz=False: no hace sombra
        for m in modelo.mallas:
            for k, cara in enumerate(m.caras):
                vs = [m.vertices[i] for i in cara]
                uv = uvs[id(m)][k]
                for j in range(1, len(vs) - 1):
                    self.piezas.append(_Tri(vs[0], vs[j], vs[j + 1], (uv[0], uv[j], uv[j + 1]), id(m), opaco))

    # ---------------------------------------------------------- una cara
    def cara(self, pos, n, ancho, alto, dueno, lateral, filas, cruza=None, n_luz=None):
        """Prepara la luz de una cara. pos(s, r) -> punto 3D (s, r en 0..1, r = 0 arriba); n: normal hacia afuera;
        ancho/alto en px; dueno: id de la pieza (una caja no se tapa a si misma); lateral: cara de costado (lleva
        canto con luz y contorno); filas: alto en texeles; cruza(s, r, dr): para mallas, si al moverse dr se cruza
        una arista que es canto (en un cubo los cantos son el borde de arriba y el de abajo de la cara); n_luz: normal
        para decidir cuanto mira a la luz (la de la cara original si un quad torcido se partio en dos triangulos, asi
        las dos mitades quedan iguales). Devuelve una funcion (color, s, r) -> color con los pasos aplicados."""
        n = _norm(n)
        ns = max(2, math.ceil(ancho / PASO_GRILLA) + 1)
        nr = max(2, math.ceil(alto / PASO_GRILLA) + 1)
        puntos = [[pos(a / (ns - 1), b / (nr - 1)) for a in range(ns)] for b in range(nr)]
        xs = [p[0] for fila in puntos for p in fila]
        ys = [p[1] for fila in puntos for p in fila]
        zs = [p[2] for fila in puntos for p in fila]
        lo, hi = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
        R = RADIO_OCLUSION
        cerca = [q for q in self.piezas if not (isinstance(q, _Caja) and q.dueno == dueno)
                 and _solapa((lo[0] - R, lo[1] - R, lo[2] - R), (hi[0] + R, hi[1] + R, hi[2] + R), q.alo, q.ahi)]
        mira_luz = _punto(_norm(n_luz) if n_luz else n, L)
        sombra_de = []
        if mira_luz > 0.05:
            fin_lo = tuple(min(lo[i], lo[i] + L[i] * LARGO_SOMBRA) for i in range(3))
            fin_hi = tuple(max(hi[i], hi[i] + L[i] * LARGO_SOMBRA) for i in range(3))
            sombra_de = [q for q in self.piezas if not (isinstance(q, _Caja) and q.dueno == dueno)
                         and _solapa(fin_lo, fin_hi, q.alo, q.ahi)]
        # marco de la cara para girar los rayos fijos
        t1 = _norm(_cruz(n, (0, 1, 0)) if abs(n[1]) < 0.9 else _cruz(n, (1, 0, 0)))
        t2 = _cruz(n, t1)
        rayos = [(t1[0] * a + t2[0] * b + n[0] * c, t1[1] * a + t2[1] * b + n[1] * c,
                  t1[2] * a + t2[2] * b + n[2] * c, w) for a, b, c, w in DIRECCIONES]
        peso = sum(w for *_, w in rayos)
        ocl = [[0.0] * ns for _ in range(nr)]
        som = [[0.0] * ns for _ in range(nr)]
        Lx, Ly, Lz = L[0] * LARGO_SOMBRA, L[1] * LARGO_SOMBRA, L[2] * LARGO_SOMBRA
        for b in range(nr):
            for a in range(ns):
                p = puntos[b][a]
                x, y, z = p[0] + n[0] * SEPARACION, p[1] + n[1] * SEPARACION, p[2] + n[2] * SEPARACION
                p = (x, y, z)
                aqui = [q for q in cerca if q.alo[0] <= x + R and q.ahi[0] >= x - R and q.alo[1] <= y + R
                        and q.ahi[1] >= y - R and q.alo[2] <= z + R and q.ahi[2] >= z - R]
                if aqui or y < R:
                    o = 0.0
                    for dx, dy, dz, w in rayos:
                        d = (dx, dy, dz)
                        ex, ey, ez = x + dx * R, y + dy * R, z + dz * R
                        lx, hx = (x, ex) if x < ex else (ex, x)
                        ly, hy = (y, ey) if y < ey else (ey, y)
                        lz, hz = (z, ez) if z < ez else (ez, z)
                        mejor = R
                        for q in aqui:
                            qa, qb = q.alo, q.ahi
                            if qa[0] > hx or qb[0] < lx or qa[1] > hy or qb[1] < ly or qa[2] > hz or qb[2] < lz:
                                continue
                            t = q.choca(p, d, mejor)
                            if t is not None and t < mejor:
                                mejor = t
                        if dy < -1e-6 and -y / dy < mejor:
                            mejor = -y / dy                    # el piso (y = 0)
                        if mejor < R:
                            o += w * (1 - mejor / R)
                    ocl[b][a] = o / peso
                if sombra_de:
                    ex, ey, ez = x + Lx, y + Ly, z + Lz
                    lx, hx = (x, ex) if x < ex else (ex, x)
                    ly, hy = (y, ey) if y < ey else (ey, y)
                    lz, hz = (z, ez) if z < ez else (ez, z)
                    for q in sombra_de:
                        qa, qb = q.alo, q.ahi
                        if qa[0] > hx or qb[0] < lx or qa[1] > hy or qb[1] < ly or qa[2] > hz or qb[2] < lz:
                            continue
                        if q.choca(p, L, LARGO_SOMBRA) is not None:
                            som[b][a] = 1.0
                            break

        ocl, som = _suavizar(ocl), _suavizar(som)

        def interp(g, s, r):
            x, y = s * (ns - 1), r * (nr - 1)
            a, b = min(int(x), ns - 2), min(int(y), nr - 2)
            fx, fy = x - a, y - b
            return ((g[b][a] * (1 - fx) + g[b][a + 1] * fx) * (1 - fy)
                    + (g[b + 1][a] * (1 - fx) + g[b + 1][a + 1] * fx) * fy)

        hay_ocl = any(v > 0 for fila in ocl for v in fila)
        hay_cantos = lateral and filas >= 4
        grosor = max(1, round(0.2 * filas / max(alto, 1e-9)))   # ~0.2 px de canto, al menos 1 texel
        un_texel = grosor / max(1, filas)
        de_cara = mira_luz > 0.3
        brilla = mira_luz > DE_CARA

        def aplicar(col, s, r):
            if col[3] == 0:
                return col
            k = 0
            if sombra_de and interp(som, s, r) > 0.5:
                k -= 1
            if hay_ocl:
                o = interp(ocl, s, r)
                if o > UMBRAL_1:
                    k -= 1
                if o > UMBRAL_2:
                    k -= 1
            k = max(k, -2)
            if k == 0 and brilla:
                k = 1                                  # lo que mira a la luz sin nada encima: brillo
            elif k == 0 and hay_cantos:
                arriba = r - un_texel < 0 if cruza is None else cruza(s, r, -un_texel)
                abajo = r + un_texel > 1 if cruza is None else cruza(s, r, un_texel)
                if arriba:
                    k = 1                              # canto con luz
                elif abajo and filas >= 6:
                    k = -1                             # contorno de abajo
            if de_cara and k == 0 and col[0] + col[1] + col[2] < 150:
                k = 1                                  # en lo muy oscuro la sombra casi no se ve: sube la luz
            return paso(col, k) if k else col
        return aplicar
