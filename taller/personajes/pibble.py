"""
Pibble, el semidios errante, hermano de Moles (de la misma estrella). Se rehace paso a paso con los mismos terminos
que ella: el mismo cuerpo chibi y la misma escala, todo low-poly de caras planas, segun referencias/personajes/pibble.png.

Por ahora solo la cabeza, esculpida como un gato de papel: redonda y mas ancha que alta, de caras triangulares, con
los cachetes en pico a los lados, el hocico con la nariz que sale, las cuencas de los ojos hundidas, la ceja y la
frente redonda; toda de vacio negro, con los ojos de almendra crema (piezas con las puntas afiladas, pegadas en las
cuencas, con orilla dorada) inclinados hacia arriba afuera y el rombo dorado al centro de la frente.
La capucha, paso a paso: por ahora los dos paneles de enfrente, unidos por la punta en la frente: doblados hacia la
cabeza, la parte de abajo inclinada hacia enfrente, la esquina de arriba alargada hacia arriba, y el hundido hecho con
el hundido curvo hacia adentro de caras pegadas, cortados a lo largo con la mitad de abajo hundida, muy cerca de la
cara sin tocarla; y el techo que sale de la punta de la frente, pegado a sus orillas de arriba hasta sus esquinas,
cortado como semi bumeran (acaba en una muesca a la mitad, con el medio hundido en valle); atras la copia en espejo
y los costados cerrados.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..textura import hex_a_rgba as hex_
from .moles import faceta

VACIO, OJO, OJO_ORILLA = "#0E0C10", "#EADCBF", "#C8A058"

# la cabeza, redonda como gato de papel (mas ancha que alta), de abajo hacia arriba: (y, medio ancho, medio hondo
# adelante, medio hondo atras, {punto: cuanto sale (+) o se mete (-)}). 16 puntos por anillo: 0 a su derecha (+X),
# 4 el frente, 8 a su izquierda, 12 atras; solo se dan los de la derecha y el medio (los de la izquierda en espejo)
CABEZA = ((11.2, 2.6, 2.6, 2.6, {4: 0.3}),
          (12.2, 4.0, 3.9, 3.6, {4: 0.5, 3: 0.2}),                           # la barbilla
          (13.4, 5.0, 4.5, 4.1, {4: 1.3, 3: 0.6, 0: 0.5, 1: 0.2}),           # el hocico y los cachetes en pico
          (14.6, 5.4, 4.6, 4.3, {4: 1.65, 3: 0.45, 0: 0.6}),                 # la punta de la nariz
          (15.6, 5.3, 4.6, 4.4, {4: 0.75, 3: -0.15, 2: -0.45}),              # el puente y las cuencas de los ojos
          (16.6, 5.15, 4.6, 4.4, {4: 0.3, 3: -0.2, 2: -0.45}),
          (17.6, 4.9, 4.6, 4.3, {4: 0.1, 3: 0.1, 2: 0.1}),                   # la ceja
          (19.0, 4.2, 3.9, 3.8, {}),
          (20.0, 2.9, 2.7, 2.7, {}),
          (20.6, 1.3, 1.2, 1.2, {}))
CORONILLA = (0.0, 20.8, 0.0)
LADOS = 16


def _anillo(y, mx, mzf, mzb, sale):
    sale = {**sale, **{(8 - k) % LADOS: v for k, v in sale.items()}}         # el espejo de cada punto
    pts = []
    for k in range(LADOS):
        a = 2 * math.pi * k / LADOS
        c, s = math.cos(a), math.sin(a)
        mz = mzf if s > 0 else mzb
        e = sale.get(k, 0.0)
        pts.append((mx * c + e * c, y, -mz * s - e * s))
    return pts


def cabeza_malla():
    anillos = [_anillo(*nivel) for nivel in CABEZA]
    return geo.unir(geo.loft_puntos(anillos, tapa_arriba=False), geo.piramide(anillos[-1], CORONILLA, tapa=False))


# los ojos: almendras con las puntas afiladas, pegadas en las cuencas (siguen la curva de la cara) y un poco
# inclinadas hacia arriba afuera, con la orilla dorada atras; el rombo dorado al centro de la frente con el centro negro
OJO_CENTRO = (2.4, 16.1, -3.95)                          # el derecho; el izquierdo en espejo
OJO_TAMANO = (1.25, 0.55)                                # medio largo, medio alto
OJO_GIRO = (0, -35, 9)                                   # sigue la curva de la cara y sube hacia afuera
ROMBO = ((0.0, 18.3, -4.35), (0.3, 0.55), 30)            # centro, medio ancho y medio alto, inclinado como la frente


def _almendra(largo, alto, n=6):
    """Contorno de almendra con las dos puntas afiladas."""
    arriba = [(-largo + 2 * largo * i / n, alto * math.sin(math.pi * i / n) ** 0.8) for i in range(n + 1)]
    abajo = [(x, -y) for x, y in arriba[-2:0:-1]]
    return arriba + abajo


def _placa(perfil, grueso, giro, centro, adelante=0.0):
    m = geo.extruir(perfil, -grueso / 2 - adelante, grueso / 2 - adelante)
    return geo.mover(geo.girar(m, giro), centro)


def ojos(p):
    largo, alto = OJO_TAMANO
    crema = _placa(_almendra(largo, alto), 0.14, OJO_GIRO, OJO_CENTRO, adelante=0.08)
    orilla = _placa(_almendra(largo + 0.16, alto + 0.12), 0.1, OJO_GIRO, OJO_CENTRO)
    p.malla_par("Head/ojos", "ojo", crema, liso(OJO), dens=8, luz=False)
    p.malla_par("Head/ojos", "orilla", orilla, liso(OJO_ORILLA), dens=8, luz=False)
    centro, (w, h), rx = ROMBO
    rombo = lambda a, b: [(0.0, -b), (a, 0.0), (0.0, b), (-a, 0.0)]
    p.malla("Head/ojos", "rombo", _placa(rombo(w, h), 0.1, (rx, 0, 0), centro), liso(OJO_ORILLA), dens=8, luz=False)
    p.malla("Head/ojos", "rombo_centro", _placa(rombo(w * 0.45, h * 0.5), 0.1, (rx, 0, 0), centro, adelante=0.06),
            liso(VACIO), dens=8, luz=False)


# la capucha, paso a paso: por ahora los dos paneles de enfrente, unidos por la punta justo en la frente. Cada uno (el
# derecho; el izquierdo en espejo) nace de un triangulo equilatero de lado LADO_TRIANGULO con la punta en la frente:
# las esquinas de afuera alargadas (en punta), girado sobre su punta (lo de afuera baja), doblado hacia la cabeza e
# inclinado (la parte de abajo hacia enfrente); y la esquina de arriba alargada hacia arriba desde la mitad de la
# orilla de arriba. El hundido (un triangulo de la mitad con la base sobre el lado de afuera, de su punta hasta el
# final) se curva hacia adentro con un bisel suave; cada lado se corta a lo largo y la mitad de abajo se hunde con un
# doblez suave. Cada lado es UNA malla 2D continua (cada cara con sus dos lados) de muchos poligonos: todo pegado
LADO_TRIANGULO = 9.5
PUNTA_FRENTE = (0.0, 19.8, -4.0)                         # en la frente (se recorre hacia enfrente lo justo)
Z_AFUERA = -3.0
GIRO_TRIANGULO = 20.0                                    # grados que se gira sobre su punta: lo de afuera baja
HACIA_ADENTRO = 25.0                                     # grados que lo de afuera se dobla hacia la cabeza
INCLINA = 20.0                                           # grados que la parte de abajo se inclina hacia enfrente
ALARGA = 2.2                                             # cuanto se alargan las dos esquinas de afuera (en punta)
PUNTA_ARRIBA = 3.5                                       # cuanto se alarga hacia arriba la esquina de arriba
HUECO = 0.5                                              # el hundido: el triangulo de la mitad
Z_HUECO = 0.15                                           # que tan atras empieza el hundido (en su punta)
HOLGURA = 0.1                                            # lo mas cerca que pasan de la cara, sin tocarla
HUNDE_MITAD = 0.35                                       # la mitad de abajo (cortada a lo largo) se hunde esto
CURVA = 0.6                                              # el hundido se curva hacia adentro: lo mas hondo, en la orilla
RETICULA = 14                                            # cada lado se arma con una reticula de RETICULA x RETICULA
DOBLEZ = 0.5                                             # lo ancho del doblez del corte (hacia la mitad de abajo)
BISEL = 0.45                                             # lo ancho del bisel con que entra el hundido
# el techo (el triangulo de arriba): de la punta de la frente, pegado a la orilla de arriba de cada lado hasta su
# esquina de arriba; cortado como semi bumeran: en vez de cerrar atras acaba en la MUESCA, a la mitad, hundida (de la
# punta a la mitad el medio se hunde en valle, sobre la cabeza sin tocarla). Atras va la copia en espejo (los dos
# lados y el techo), con su V cerrada (atras no hay cara), y los costados se cierran uniendo la orilla de afuera de
# enfrente con la de atras
MUESCA = (0.0, 21.25, 0.0)
CREMA = ((0.34, "#B8AD9A"), (0.5, "#CBC1AE"), (0.66, "#DCD3C3"), (9.0, "#E9E2D5"))


def _triangulo():
    """La punta en la frente y las dos esquinas de afuera (la de arriba y la de abajo)."""
    x0, y0, z0 = PUNTA_FRENTE
    l = LADO_TRIANGULO
    x = math.sqrt(l * l - (l / 2) ** 2 - (Z_AFUERA - z0) ** 2)
    cx = x * 2 / 3                                       # el centro del triangulo (respecto a la punta)
    g, h, k = math.radians(-GIRO_TRIANGULO), math.radians(HACIA_ADENTRO), math.radians(INCLINA)

    def esquina(dy):
        ex, ey = x - cx, dy
        d = math.hypot(ex, ey)
        dx, dy = cx + ex * (1 + ALARGA / d), ey * (1 + ALARGA / d)     # alargada desde el centro
        dx, dy = dx * math.cos(g) - dy * math.sin(g), dx * math.sin(g) + dy * math.cos(g)
        dz = Z_AFUERA - z0
        dx, dz = dx * math.cos(h) - dz * math.sin(h), dx * math.sin(h) + dz * math.cos(h)
        dy, dz = dy * math.cos(k) - dz * math.sin(k), dz * math.cos(k) + dy * math.sin(k)
        return (x0 + dx, y0 + dy, z0 + dz)
    return (PUNTA_FRENTE, esquina(l / 2), esquina(-l / 2))


def _resta(p, q):
    return tuple(x - y for x, y in zip(p, q))


def _punto(p, q):
    return sum(x * y for x, y in zip(p, q))


def _cruz(p, q):
    return (p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0])


def _unit(p):
    return tuple(x / math.sqrt(_punto(p, p)) for x in p)


def _dentro(pts, x, y, margen):
    """Si (x, y) cae dentro del poligono o a menos de margen de su orilla."""
    dentro = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            dentro = not dentro
        lx, ly = x1 - x0, y1 - y0
        f = max(0.0, min(1.0, ((x - x0) * lx + (y - y0) * ly) / (lx * lx + ly * ly or 1.0)))
        if math.hypot(x - x0 - lx * f, y - y0 - ly * f) < margen:
            return True
    return dentro


def _paneles(a, b, c, estorbos):
    """Un lado entero como una sola malla 2D (reticula pegada), su punta (ya recorrida) y la mitad de su orilla de
    arriba. Todo el lado se recorre hacia enfrente (solo en z, asi las puntas de los dos lados siguen juntas en el medio)
    lo justo para que nada de 'estorbos' (los vertices de la cabeza y los ojos) quede a menos de HOLGURA detras de lo
    mas hondo: muy cerca de la cara, sin meterse."""
    u = _unit(_resta(b, a))
    n = _unit(_cruz(_resta(b, a), _resta(c, a)))
    if n[2] < 0:
        n = tuple(-x for x in n)                          # atras = hacia la cabeza
    v = _cruz(n, u)
    t0, b1, b2 = [(_punto(_resta(q, a), u), _punto(_resta(q, a), v)) for q in (a, b, c)]
    mx, my = (b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2   # medio del lado de afuera
    lx, ly = b1[0] - b2[0], b1[1] - b2[1]
    largo = math.hypot(lx, ly)
    punta = (b1[0] + lx / largo * PUNTA_ARRIBA, b1[1] + ly / largo * PUNTA_ARRIBA)
    mitad = ((t0[0] + b1[0]) / 2, (t0[1] + b1[1]) / 2)
    h = HUNDE_MITAD
    recorre = 0.0
    for q in estorbos:
        d = _resta(q, a)
        if _dentro([t0, mitad, punta, b2], _punto(d, u), _punto(d, v), 0.6):
            recorre = max(recorre, HOLGURA + Z_HUECO + CURVA + h - _punto(d, n))
    a = (a[0], a[1], a[2] - recorre / n[2])              # solo hacia enfrente: la punta sigue en el medio (x = 0)

    def mezcla(p, q, f):
        return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)

    def suave(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3 - 2 * x)

    def lado_de(q, p0, p1):                               # distancia con signo de q a la recta p0-p1
        ex, ey = p1[0] - p0[0], p1[1] - p0[1]
        return ((q[0] - p0[0]) * ey - (q[1] - p0[1]) * ex) / math.hypot(ex, ey)

    medio = (mx, my)
    p, q1, q2 = [mezcla(medio, q, HUECO) for q in (t0, b1, b2)]   # el hueco, hacia el medio del lado de afuera
    abajo = 1.0 if lado_de(b2, t0, medio) > 0 else -1.0
    eje = math.hypot(mx - p[0], my - p[1])

    def hondo(q):
        """Que tan atras va cada punto: la mitad de abajo hundida (con un doblez suave en el corte) y el hundido, que
        entra con un bisel y se curva hacia adentro hacia la orilla de afuera."""
        z = h * suave(abajo * lado_de(q, t0, medio) / DOBLEZ)
        d1, d2 = lado_de(q, p, q1), lado_de(q, p, q2)
        dentro1, dentro2 = d1 * (1 if lado_de(q2, p, q1) > 0 else -1), d2 * (1 if lado_de(q1, p, q2) > 0 else -1)
        if dentro1 > 0 and dentro2 > 0:
            t = max(0.0, min(1.0, ((q[0] - p[0]) * (mx - p[0]) + (q[1] - p[1]) * (my - p[1])) / (eje * eje)))
            z += (Z_HUECO + CURVA * t * t) * suave(min(dentro1, dentro2) / BISEL)
        return z

    def en3d(q):
        z = hondo(q)
        return tuple(a[i] + q[0] * u[i] + q[1] * v[i] + z * n[i] for i in range(3))

    # la reticula sobre el contorno (la punta, el lado de abajo, el de afuera con la punta de arriba, la orilla de
    # arriba): cada celda en dos triangulos, asi todo queda plano por cara y pegado
    esquinas = (t0, b2, punta, mitad)
    k = RETICULA
    vs = []
    for j in range(k + 1):
        for i in range(k + 1):
            s_, r_ = i / k, j / k
            x = sum(w * c[0] for w, c in zip(((1 - s_) * (1 - r_), s_ * (1 - r_), s_ * r_, (1 - s_) * r_), esquinas))
            y = sum(w * c[1] for w, c in zip(((1 - s_) * (1 - r_), s_ * (1 - r_), s_ * r_, (1 - s_) * r_), esquinas))
            vs.append(en3d((x, y)))
    cs = []
    for j in range(k):
        for i in range(k):
            v00, v10, v11, v01 = j * (k + 1) + i, j * (k + 1) + i + 1, (j + 1) * (k + 1) + i + 1, (j + 1) * (k + 1) + i
            for tri in ((v00, v10, v11), (v00, v11, v01)):
                cs += [tri, tri[::-1]]                    # las dos caras (2D)
    return (vs, cs), en3d(t0), en3d(mitad), en3d(punta)


def _panel(vs):
    """Un poligono plano con sus dos caras (2D)."""
    m = len(vs)
    return vs, [tuple(range(m)), tuple(range(m))[::-1]]


def _reticula_2d(filas):
    """Malla 2D (dos caras) de una reticula de puntos (filas de la misma cantidad de puntos)."""
    ancho = len(filas[0])
    vs = [q for fila in filas for q in fila]
    cs = []
    for j in range(len(filas) - 1):
        for i in range(ancho - 1):
            v00, v10, v11, v01 = j * ancho + i, j * ancho + i + 1, (j + 1) * ancho + i + 1, (j + 1) * ancho + i
            for tri in ((v00, v10, v11), (v00, v11, v01)):
                a, b, c = (vs[t] for t in tri)
                if math.sqrt(_punto(*(2 * [_cruz(_resta(b, a), _resta(c, a))]))) > 1e-6:   # sin las que se juntan
                    cs += [tri, tri[::-1]]
    return vs, cs


FORRO = ((0.34, "#100E12"), (0.5, "#161318"), (0.66, "#1D1A1F"), (9.0, "#252127"))
CENTRO_CABEZA = (0.0, 16.0, 0.0)


def capucha_pintor():
    """Crema por fuera y el forro negro por dentro: cada pieza es 2D (dos caras), la que mira hacia la cabeza es el
    forro."""
    crema, forro = faceta(paleta=CREMA, grano=0), faceta(paleta=FORRO, grano=0)

    def pintor(t):
        hacia_fuera = _punto(t.n, _resta((t.x, t.y, t.z), CENTRO_CABEZA))
        return forro(t) if hacia_fuera < 0 else crema(t)
    return pintor


def capucha(p):
    estorbos = [q for m in p.m.mallas if m.hueso.split("/")[0] == "Head" for q in m.vertices]
    (vs, cs), frente, mitad, esquina = _paneles(*_triangulo(), estorbos)
    k = RETICULA
    atras_z = lambda q: (q[0], q[1], -q[2])
    # el lado de atras: el de enfrente en espejo (enfrente-atras), con su esquina de arriba jalada a la de enfrente
    # (asi las dos comparten la punta de arriba); en la reticula esa esquina es (i = k, j = k)
    jalon = esquina[2] - atras_z(esquina)[2]
    vs_atras = []
    for idx, q in enumerate(vs):
        j, i = divmod(idx, k + 1)
        x, y, z = atras_z(q)
        vs_atras.append((x, y, z + jalon * (i / k) * (j / k)))
    crema = capucha_pintor()
    p.malla_par("Head/capucha", "lado", (vs, cs), crema, dens=4, luz=False)
    p.malla_par("Head/capucha", "lado_atras", (vs_atras, cs), crema, dens=4, luz=False)
    # el costado: une la orilla de afuera de enfrente (i = k, de la esquina de abajo a la de arriba) con la de atras
    orilla = [vs[j * (k + 1) + k] for j in range(k + 1)]
    orilla_atras = [vs_atras[j * (k + 1) + k] for j in range(k + 1)]
    filas = [[tuple(f[c] + (b_[c] - f[c]) * t / 4 for c in range(3)) for t in range(5)]
             for f, b_ in zip(orilla, orilla_atras)]
    p.malla_par("Head/capucha", "costado", _reticula_2d(filas), crema, dens=4, luz=False)
    # atras no hay cara: la V de la copia se cierra uniendo la orilla de adentro de sus dos lados (j = 0, de la punta a
    # la esquina de abajo)
    adentro = [vs_atras[i] for i in range(k + 1)]
    filas = [[tuple(q[c] * (1 - 2 * t / 4) if c == 0 else q[c] for c in range(3)) for t in range(5)] for q in adentro]
    p.malla("Head/capucha", "cierre_atras", _reticula_2d(filas), crema, dens=4, luz=False)
    # el techo de enfrente y su copia atras: pegados a la orilla de arriba de cada lado (la punta, la mitad y la
    # esquina de arriba); sus brazos se juntan en la muesca hundida, que comparten
    espejo = lambda q: (-q[0], q[1], q[2])
    techo = []
    for f, m in ((frente, mitad), (atras_z(frente), atras_z(mitad))):
        for tri in ((f, m, esquina), (f, esquina, MUESCA), (f, MUESCA, espejo(esquina)),
                    (f, espejo(esquina), espejo(m))):
            techo.append(_panel(list(tri)))
    p.malla("Head/capucha", "techo", geo.unir(*techo), crema, dens=4, luz=False)


def liso(col):
    c = hex_(col)
    return lambda t: c


def construir():
    p = Personaje("pibble", altura=21, cabeza=10, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    p.malla("Head/cabeza", "cabeza", cabeza_malla(), liso(VACIO), dens=4, luz=False)   # el vacio no se sombrea
    ojos(p)
    capucha(p)
    return p
