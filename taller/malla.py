"""
Geometria low-poly: mallas de Blockbench (vertices libres y caras planas de 3 o 4 vertices).

Convencion de las caras: vertices en orden ANTIHORARIO vista la cara desde afuera (regla de la mano
derecha: la normal sale hacia afuera). Es la misma que usa Blockbench para calcular la normal de una cara.

Las funciones de aca devuelven (vertices, caras):
    vertices = [(x, y, z), ...] en px del modelo
    caras    = [(i0, i1, i2) o (i0, i1, i2, i3), ...] indices a vertices
y se suman con unir(). Los cuadrilateros que no quedan planos se parten solos en dos triangulos.
Una cara puede ser un poligono plano de mas de 4 vertices (o concavo): se triangula al guardar y sus
triangulos comparten un solo rectangulo de textura (el pintor ve la cara entera, sin costuras).
"""

import math

TOL_PLANO = 0.02          # px: un cuadrilatero mas torcido que esto se parte en dos triangulos


# ----------------------------------------------------------------------------- vectores

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    ln = math.sqrt(_dot(a, a))
    return (a[0] / ln, a[1] / ln, a[2] / ln) if ln > 1e-12 else (0.0, 0.0, 0.0)


def normal(puntos):
    """Normal de un poligono (metodo de Newell): sale hacia el lado desde donde se ve antihorario."""
    nx = ny = nz = 0.0
    for k, p in enumerate(puntos):
        q = puntos[(k + 1) % len(puntos)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    return _norm((nx, ny, nz))


def cara_cercana(n):
    """Nombre de la cara de cubo mas parecida a la normal (para que los pintores de siempre sirvan)."""
    ax = max(range(3), key=lambda i: abs(n[i]))
    return (("west", "east"), ("down", "up"), ("north", "south"))[ax][n[ax] > 0]


def marco(puntos):
    """Ejes de la textura de una cara: (normal, derecha, arriba). La textura queda 'parada' (arriba = +Y)
    en caras de costado; en caras casi horizontales sigue la convencion de Blockbench para up/down."""
    n = normal(puntos)
    if abs(n[1]) <= 0.9:
        ref = (0.0, 1.0, 0.0)
    else:
        ref = (0.0, 0.0, -1.0) if n[1] > 0 else (0.0, 0.0, 1.0)
    d = _dot(ref, n)
    arriba = _norm((ref[0] - d * n[0], ref[1] - d * n[1], ref[2] - d * n[2]))
    derecha = _cross((-n[0], -n[1], -n[2]), arriba)          # derecha de quien mira la cara desde afuera
    return n, derecha, arriba


def plano(puntos):
    """Distancia maxima de los puntos al plano de la cara (0 = plana)."""
    n = normal(puntos)
    d0 = _dot(puntos[0], n)
    return max(abs(_dot(p, n) - d0) for p in puntos)


# ----------------------------------------------------------------------------- armado

def _cara(vs, idx):
    """Agrega una cara; un cuadrilatero torcido se parte en dos triangulos por la diagonal mas corta."""
    if len(idx) == 4 and plano([vs[i] for i in idx]) > TOL_PLANO:
        a, b, c, d = idx
        d1 = _dot(_sub(vs[a], vs[c]), _sub(vs[a], vs[c]))
        d2 = _dot(_sub(vs[b], vs[d]), _sub(vs[b], vs[d]))
        return [(a, b, c), (a, c, d)] if d1 <= d2 else [(a, b, d), (b, c, d)]
    return [tuple(idx)]


def triangular(pol):
    """Triangula un poligono 2D (antihorario, puede ser concavo) por recorte de orejas. Devuelve indices."""
    idx = list(range(len(pol)))
    tris = []

    def area(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def dentro(p, a, b, c):
        return area(a, b, p) >= -1e-9 and area(b, c, p) >= -1e-9 and area(c, a, p) >= -1e-9

    guardia = 0
    while len(idx) > 3 and guardia < 10000:
        guardia += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pol[i0], pol[i1], pol[i2]
            if area(a, b, c) <= 1e-9:
                continue
            if any(dentro(pol[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def _tapa(vs, idx, pol2d):
    """Tapa de un poligono: va entera como una sola cara (aunque tenga mas de 4 vertices o sea concava).
    El modelo la triangula al guardarla y todos sus triangulos comparten la misma textura."""
    return [tuple(idx)]


def _convexo(pol):
    s = 0
    for k in range(len(pol)):
        a, b, c = pol[k - 1], pol[k], pol[(k + 1) % len(pol)]
        z = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(z) < 1e-12:
            continue
        if s == 0:
            s = 1 if z > 0 else -1
        elif (z > 0) != (s > 0):
            return False
    return True


def unir(*partes):
    """Suma varias (vertices, caras) en una sola malla."""
    vs, cs = [], []
    for v, c in partes:
        base = len(vs)
        vs.extend(v)
        cs.extend(tuple(i + base for i in cara) for cara in c)
    return vs, cs


def tronco(abajo, arriba, tapa_abajo=True, tapa_arriba=True):
    """Tronco facetado entre dos anillos con la misma cantidad de puntos (antihorario visto desde arriba:
    de +X hacia -Z). Sirve para capuchas, faldas en A, mangas acampanadas, cuellos..."""
    n = len(abajo)
    assert len(arriba) == n, "los dos anillos necesitan la misma cantidad de puntos"
    vs = list(abajo) + list(arriba)
    cs = []
    for k in range(n):
        k2 = (k + 1) % n
        cs += _cara(vs, (k, k2, n + k2, n + k))
    if tapa_arriba:
        cs += _tapa(vs, list(range(n, 2 * n)), [(p[0], -p[2]) for p in arriba])
    if tapa_abajo:
        idx = list(range(n))[::-1]
        cs += _tapa(vs, idx, [(abajo[i][0], abajo[i][2]) for i in idx])
    return vs, cs


def piramide(base, apice, tapa=True):
    """Piramide facetada: base antihoraria vista desde arriba y un apice (orejas, puntas, gemas)."""
    n = len(base)
    vs = list(base) + [apice]
    cs = [(k, (k + 1) % n, n) for k in range(n)]
    if tapa:
        idx = list(range(n))[::-1]
        cs += _tapa(vs, idx, [(base[i][0], base[i][2]) for i in idx])
    return vs, cs


def extruir(perfil, z1, z2):
    """Extruye un perfil 2D (x, y) antihorario (puede ser concavo) entre z1 y z2 (z1 < z2).
    Para colas, paneles con dobladillo en punta, colgantes, hojas..."""
    n = len(perfil)
    if sum((perfil[k - 1][0] - perfil[k][0]) * (perfil[k - 1][1] + perfil[k][1]) for k in range(n)) < 0:
        perfil = perfil[::-1]                     # lo damos vuelta si vino horario
    vs = [(x, y, z1) for x, y in perfil] + [(x, y, z2) for x, y in perfil]
    cs = []
    for k in range(n):
        k2 = (k + 1) % n
        cs += _cara(vs, (k, k2, n + k2, n + k))
    cs += _tapa(vs, list(range(n, 2 * n)), list(perfil))                    # atras (+Z)
    idx = list(range(n))[::-1]
    cs += _tapa(vs, idx, [(-perfil[i][0], perfil[i][1]) for i in idx])      # frente (-Z)
    return vs, cs


def anillo(cx, y, cz, rx, rz, n, giro=0.0):
    """Puntos de un anillo (poligono regular estirado) antihorario visto desde arriba."""
    out = []
    for k in range(n):
        a = math.radians(giro + 360.0 * k / n)
        out.append((cx + rx * math.cos(a), y, cz - rz * math.sin(a)))
    return out


# ----------------------------------------------------------------------------- transformaciones

def girar(malla, rot, piv=(0.0, 0.0, 0.0)):
    """Gira (rx, ry, rz) en grados alrededor de piv, en el mismo orden que Blockbench (Z * Y * X)."""
    vs, cs = malla
    a, b, c = (math.radians(v) for v in rot)
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    out = []
    for p in vs:
        x, y, z = p[0] - piv[0], p[1] - piv[1], p[2] - piv[2]
        y, z = y * ca - z * sa, y * sa + z * ca             # X
        x, z = x * cb + z * sb, -x * sb + z * cb            # Y
        x, y = x * cc - y * sc, x * sc + y * cc             # Z
        out.append((x + piv[0], y + piv[1], z + piv[2]))
    return out, cs


def mover(malla, d):
    vs, cs = malla
    return [(p[0] + d[0], p[1] + d[1], p[2] + d[2]) for p in vs], cs


def escalar(malla, k, piv=(0.0, 0.0, 0.0)):
    vs, cs = malla
    kx, ky, kz = (k, k, k) if isinstance(k, (int, float)) else k
    return [(piv[0] + (p[0] - piv[0]) * kx, piv[1] + (p[1] - piv[1]) * ky, piv[2] + (p[2] - piv[2]) * kz)
            for p in vs], cs


def espejo_x(malla):
    """Refleja en X (lado derecho -> izquierdo) y da vuelta las caras para que sigan mirando afuera."""
    vs, cs = malla
    return [(-p[0], p[1], p[2]) for p in vs], [tuple(reversed(c)) for c in cs]
