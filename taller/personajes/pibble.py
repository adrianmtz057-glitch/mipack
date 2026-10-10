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
from .moles import _azar, faceta

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
LADO_TRIANGULO = 8.6
PUNTA_FRENTE = (0.0, 21.6, -4.0)                         # arriba en la frente (se recorre hacia enfrente lo justo)
Z_AFUERA = -3.0
GIRO_TRIANGULO = 12.0                                    # grados que se gira sobre su punta: lo de afuera baja
HACIA_ADENTRO = 25.0                                     # grados que lo de afuera se dobla hacia la cabeza
INCLINA = 20.0                                           # grados que la parte de abajo se inclina hacia enfrente
ALARGA = 2.0                                             # cuanto se alargan las dos esquinas de afuera (en punta)
PUNTA_ARRIBA = 3.2                                       # cuanto se alarga hacia arriba la esquina de arriba
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
MUESCA = (0.0, 21.5, 0.0)
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


def _fuera_de_cabeza(q, holgura=0.2):
    """Empuja el punto hacia afuera (en x) si cae dentro de la cabeza: en cada altura la cabeza es un ovalo de medio
    ancho el de sus anillos (con los cachetes en pico) y de medio hondo el de enfrente."""
    x, y, z = q
    perfil = [(y_, mx + sale.get(0, 0.0), mzf) for y_, mx, mzf, _, sale in CABEZA]
    if not perfil[0][0] <= y <= perfil[-1][0]:
        return q
    for (y0, a0, c0), (y1, a1, c1) in zip(perfil, perfil[1:]):
        if y <= y1:
            f = (y - y0) / (y1 - y0)
            ancho, hondo = a0 + (a1 - a0) * f + holgura, c0 + (c1 - c0) * f + holgura
            break
    limite = ancho * math.sqrt(max(0.0, 1 - (z / hondo) ** 2))
    return (math.copysign(max(abs(x), limite), x), y, z)


FORRO = ((0.34, "#0B0A0C"), (0.5, "#100F12"), (0.66, "#161418"), (9.0, "#1D1A1F"))   # negro de verdad
AZUL = ((0.34, "#1F2F42"), (0.5, "#283B50"), (0.66, "#31475D"), (9.0, "#3C556C"))
CENTRO_CABEZA = (0.0, 16.0, 0.0)
ORO = ((0.34, "#94713C"), (0.5, "#AD874A"), (0.66, "#C8A058"), (9.0, "#DEB974"))
# las runas azules de la capucha (como en la referencia, una flecha que baja y voltea): rectangulos en (|x|, y) sobre
# las caras de enfrente y de atras de los lados
RUNA = ((3.9, 4.3, 18.6, 20.4), (3.9, 5.1, 18.6, 19.0), (4.7, 5.1, 19.0, 19.5))
OREJA_NEGRA = 2.6                                        # lo que baja lo negro desde la punta de cada oreja
FILETE = 0.32                                            # lo ancho del filete dorado de la orilla de la cara


def _a_segmento(q, p0, p1):
    ex, ey, ez = (p1[i] - p0[i] for i in range(3))
    f = max(0.0, min(1.0, ((q[0] - p0[0]) * ex + (q[1] - p0[1]) * ey + (q[2] - p0[2]) * ez) / (ex * ex + ey * ey + ez * ez)))
    return math.dist(q, (p0[0] + ex * f, p0[1] + ey * f, p0[2] + ez * f))


def capucha_pintor(oreja_y, orilla):
    """Crema con grano de pixeles por fuera, con las orejas de punta negra, las runas azules y el filete dorado en la
    orilla de la cara; el forro negro por dentro (cada pieza es 2D: la cara que mira hacia la cabeza es el forro)."""
    crema = faceta(paleta=CREMA, grano=0.12, simetrico=True)
    forro = faceta(paleta=FORRO, grano=0.06, simetrico=True)
    azul = faceta(paleta=AZUL, grano=0.08, simetrico=True)
    oro = faceta(0.05, ORO, grano=0.08, simetrico=True)

    def pintor(t):
        if t.y > oreja_y - OREJA_NEGRA:                       # la punta de las orejas, negra (por fuera y por dentro)
            return forro(t)
        if _punto(t.n, _resta((t.x, t.y, t.z), CENTRO_CABEZA)) < 0:
            return forro(t)
        q = (abs(t.x), t.y, t.z)
        if t.z < 0 and _a_segmento(q, *orilla) < FILETE:
            return oro(t)
        if abs(t.n[2]) > 0.35 and any(x0 <= q[0] <= x1 and y0 <= t.y <= y1 for x0, x1, y0, y1 in RUNA):
            return azul(t)
        return crema(t)
    return pintor


def _colgante(arriba, eslabones=2):
    """Una cadenita dorada (eslabones de rombo) y un rombo dorado al final, colgando desde 'arriba'."""
    x, y, z = arriba
    piezas = [geo.bipiramide((x, y - 0.45 - 0.7 * i, z), 0.14, 0.3, 0.3) for i in range(eslabones)]
    piezas.append(geo.bipiramide((x, y - 0.7 * eslabones - 1.05, z), 0.42, 0.5, 0.9))
    return geo.unir(*piezas)


def joyas(p, grupo, aro, colgantes):
    """El aro dorado de lado (mira hacia afuera) con su gema azul, y los colgantes."""
    oro, gema = faceta(0.08, ORO, grano=0, simetrico=True), faceta(0.1, AZUL, grano=0, simetrico=True)
    lado = 90 if aro[0] < 0 else -90
    p.malla(grupo, "aro", geo.mover(geo.girar(geo.aro(1.6, 1.15, 0.35, 10), (0, lado, 0)), aro), oro, dens=4)
    p.malla(grupo, "gema", geo.bipiramide(aro, 0.5, 0.7, 0.7), gema, dens=4)
    for i, c in enumerate(colgantes):
        p.malla(grupo, f"colgante{i}", _colgante(c), oro, dens=4)


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
    crema = capucha_pintor(esquina[1], (vs[0], vs[k]))      # la orilla de la cara: de la punta a la esquina de abajo
    p.malla_par("Head/capucha", "lado", (vs, cs), crema, dens=4)
    p.malla_par("Head/capucha", "lado_atras", (vs_atras, cs), crema, dens=4)
    # el costado: une la orilla de afuera de enfrente (i = k, de la esquina de abajo a la de arriba) con la de atras
    orilla = [vs[j * (k + 1) + k] for j in range(k + 1)]
    orilla_atras = [vs_atras[j * (k + 1) + k] for j in range(k + 1)]
    filas = [[_fuera_de_cabeza(tuple(f[c] + (b_[c] - f[c]) * t / 4 for c in range(3))) for t in range(5)]
             for f, b_ in zip(orilla, orilla_atras)]
    p.malla_par("Head/capucha", "costado", _reticula_2d(filas), crema, dens=4)
    # atras no hay cara: la V de la copia se cierra uniendo la orilla de adentro de sus dos lados (j = 0, de la punta a
    # la esquina de abajo)
    adentro = [vs_atras[i] for i in range(k + 1)]
    filas = [[tuple(q[c] * (1 - 2 * t / 4) if c == 0 else q[c] for c in range(3)) for t in range(5)] for q in adentro]
    p.malla("Head/capucha", "cierre_atras", _reticula_2d(filas), crema, dens=4)
    # el techo de enfrente y su copia atras: pegados a la orilla de arriba de cada lado (la punta, la mitad y la
    # esquina de arriba); sus brazos se juntan en la muesca hundida, que comparten
    espejo = lambda q: (-q[0], q[1], q[2])
    techo = []
    for f, m in ((frente, mitad), (atras_z(frente), atras_z(mitad))):
        for tri in ((f, m, esquina), (f, esquina, MUESCA), (f, MUESCA, espejo(esquina)),
                    (f, espejo(esquina), espejo(m))):
            techo.append(_panel(list(tri)))
    p.malla("Head/capucha", "techo", geo.unir(*techo), crema, dens=4)
    # las joyas: el aro con la gema azul al costado izquierdo (a la mitad de la orilla de afuera) con su rombo colgando,
    # y un rombo colgando de cada esquina de abajo
    x, y, z = orilla[k // 2]
    aro = (-(x + 0.35), y, z)
    joyas(p, "Head/joyas", aro, [(-(x + 0.35), y - 1.9, z)] + [(sx * vs[k][0], vs[k][1] - 0.1, vs[k][2])
                                                              for sx in (1, -1)])


def liso(col):
    c = hex_(col)
    return lambda t: c


# ---------------------------------------------------------------- el cuerpo

# pachoncito, a escala de Minecraft: si un jugador (32 de alto, los ojos a ~26) estuviera enfrente, sus ojos le
# llegarian al pecho. La cabeza y la capucha se hicieron con el cuello en 11.2 y suben hasta CUELLO_Y
CUELLO_Y = 31.0
CUERPO = FORRO
# el torso, de huevo con la panza hacia enfrente: (y, medio ancho, medio hondo adelante, medio hondo atras)
TORSO = ((8.5, 4.5, 3.8, 3.6), (10.0, 6.4, 5.4, 5.0), (13.0, 7.4, 6.4, 5.8), (17.0, 7.7, 6.6, 6.0),
         (21.0, 7.3, 6.1, 5.7), (25.0, 6.5, 5.2, 5.0), (28.0, 5.6, 4.4, 4.3), (30.0, 4.2, 3.4, 3.4),
         (31.6, 2.8, 2.6, 2.6))
# las piernas cortas y gorditas (la derecha; la izquierda en espejo), con el pie hacia enfrente:
# (y, medio ancho, medio hondo, z del centro)
PIERNA_X = 3.0
PIERNA = ((0.0, 2.3, 3.1, -0.8), (1.4, 2.4, 3.1, -0.8), (2.3, 2.1, 2.3, -0.2), (5.0, 2.2, 2.3, 0.0),
          (9.8, 2.5, 2.5, 0.0))
# los brazos gorditos (el derecho), colgando por fuera de la panza: (x, y, z, radio) del hombro a la mano
BRAZO = ((6.4, 28.2, 0.0, 1.9), (8.2, 24.0, -0.2, 2.2), (9.3, 19.5, -0.3, 2.15), (9.7, 16.0, -0.4, 2.3),
         (9.7, 13.4, -0.4, 2.1), (9.6, 12.2, -0.4, 1.3))


TEXTURA = True                                           # con grano de pixeles (False: para ver la forma)
ESQUINA = 0.32                                           # cuanto de cada medio ancho se recorta en las esquinas


def _anillo_oval(cx, y, cz, mx, mzf, mzb, lados=None):
    """Anillo de caja con las esquinas recortadas (8 puntos, poco redondo, estilo Minecraft), antihorario visto desde
    arriba (de +X hacia -Z); mas hondo adelante (mzf) que atras (mzb)."""
    c = ESQUINA * min(mx, mzf, mzb)
    return [(cx + mx, y, cz - mzf + c), (cx + mx - c, y, cz - mzf), (cx - mx + c, y, cz - mzf),
            (cx - mx, y, cz - mzf + c), (cx - mx, y, cz + mzb - c), (cx - mx + c, y, cz + mzb),
            (cx + mx - c, y, cz + mzb), (cx + mx, y, cz + mzb - c)]


def tela(paleta, sesgo=0.0, grano=0.1):
    """El pintor de la ropa y el cuerpo (un tono por cara; con grano solo si TEXTURA)."""
    return faceta(sesgo, paleta, grano=grano if TEXTURA else 0.0, simetrico=True)


def _subir_cabeza(p, dy):
    """Sube dy las piezas de la cabeza (cabeza, ojos, capucha) sin mover su pivote (ya esta en el cuello); cada una se
    sigue pintando igual (su pintor la ve donde estaba)."""
    from .bashi import _bajar
    for m in p.m.mallas:
        if m.hueso.split("/")[0] == "Head":
            m.vertices = [(x, y + dy, z) for x, y, z in m.vertices]
            m.grupos = [(_bajar(pin, dy), poli) for pin, poli in m.grupos]


def cuerpo(p):
    negro = tela(CUERPO, grano=0.06)
    torso = geo.loft_puntos([_anillo_oval(0.0, y, 0.0, mx, mzf, mzb) for y, mx, mzf, mzb in TORSO])
    p.malla("Body/cuerpo", "torso", torso, negro, dens=4)
    pierna = geo.loft_puntos([_anillo_oval(PIERNA_X, y, cz, mx, mz, mz, 12) for y, mx, mz, cz in PIERNA])
    brazo = geo.loft_puntos([_anillo_oval(x, y, z, r, r, r, 12) for x, y, z, r in BRAZO][::-1])
    for s in (1, -1):
        pierna_s, brazo_s = (pierna, brazo) if s > 0 else (geo.espejo_x(pierna), geo.espejo_x(brazo))
        p.malla(f"{'RightLeg' if s > 0 else 'LeftLeg'}/pierna", "pierna", pierna_s, negro, dens=4)
        p.malla(f"{'RightArm' if s > 0 else 'LeftArm'}/brazo", "brazo", brazo_s, negro, dens=4)


# ---------------------------------------------------------------- la ropa

# la bata abierta: crema, en A, abierta adelante del cuello hacia abajo (cada vez mas), con solapas negras y su filete
# dorado, el borde de abajo dorado, el panel azul con runa atras y el forro negro. Cada nivel es una U abierta
# adelante: (y, medio ancho, medio hondo adelante, medio hondo atras, medio ancho de la abertura)
BATA = ((6.0, 9.9, 7.2, 7.3, 4.8), (9.0, 9.6, 7.0, 7.0, 4.2), (14.0, 9.4, 7.1, 6.6, 3.4), (19.0, 9.3, 7.0, 6.5, 2.8),
        (24.0, 9.2, 6.2, 5.8, 2.2), (28.5, 9.0, 5.2, 5.0, 1.6), (30.5, 5.5, 4.0, 4.0, 1.0))   # tipo capa: hombros anchos
GROSOR_BATA = 0.45
PLIEGUE = 0.8                                            # lo hondo de los pliegues de la bata abajo (arriba no hay)
PISOS_BATA = 2                                           # pisos entre cada nivel de BATA (mas poligonos)
SOLAPA = 1.6                                             # lo ancho de la solapa negra junto a la abertura
RUNA_BATA = ((7.2, 7.55, 8.0, 10.6), (6.0, 7.55, 8.0, 8.35), (6.0, 6.35, 8.35, 9.0))     # (|x|, y) adelante, abajo
# las puntas del borde de abajo (azules con filete dorado): a los lados y en las esquinas de la abertura
PUNTAS_BATA = (((9.95, 6.4, -3.0), (9.95, 6.4, 3.0), (10.15, 2.6, 0.0)),
               ((4.7, 6.4, -7.35), (7.7, 6.4, -7.35), (5.8, 2.9, -7.45)))
# el colgante de la bufanda: de donde cuelga (a su izquierda de la banda)
COLGANTE_BUFANDA = (-2.7, 29.4, -6.0)
# las mangas anchas: (a que tanto del brazo crecen, del hombro hasta donde, el puno negro de donde a donde)
MANGA = (1.1, 14.6, 16.0)
# la bufanda azul: el rollo en el cuello (tapa la boca) y la banda que cuelga adelante hasta acabar en punta
BUFANDA = ((29.2, 4.4, 3.8), (30.4, 5.2, 4.8), (31.6, 5.6, 5.4), (32.6, 5.7, 5.8))     # (y, medio ancho, medio hondo)
BANDA = (1.5, 30.0, 3.6)                                 # medio ancho, de donde baja, hasta donde (la punta)
# el pantalon abombado (por pierna) y las botitas negras con la punta en pico dorada
PANTALON = ((1.7, 2.5, 2.7), (2.6, 3.0, 3.2), (5.0, 3.2, 3.4), (8.0, 3.0, 3.2), (10.5, 2.8, 3.0))   # (y, mx, mz)
BOTA = ((2.2, 2.3, 2.4, 0.2), (2.8, 2.35, 2.45, 0.2))    # la cana: (y, mx, mz, z del centro)
PICO = (5.9, 1.1)                                        # que tan adelante llega la punta y a que altura
PANTALON_NEGRO = ((0.34, "#0C0C0E"), (0.5, "#121215"), (0.66, "#18181C"), (9.0, "#1F1F24"))
# la cola esponjada como la de Moles, mas grande: su camino escalado desde la parte de abajo de la espalda
COLA_PIBBLE = tuple((x * 1.8, 12.0 + (y - 4.2) * 1.8, 5.0 + (z - 1.8) * 1.8, r * 1.8)
                    for x, y, z, r in ((0.0, 4.2, 1.8, 0.95), (1.0, 3.4, 4.4, 1.7), (2.4, 4.4, 7.0, 2.4),
                                       (3.4, 6.6, 8.6, 2.7), (3.6, 8.8, 9.0, 2.45), (3.0, 10.6, 8.6, 1.85),
                                       (2.2, 11.6, 7.9, 1.1)))


def _u_bata(y, mx, mzf, mzb, xo, g=0.0):
    """La U de la bata: caja con las esquinas recortadas (como el torso, siempre mas grande) abierta adelante entre
    -xo y xo; de la orilla izquierda de la abertura, por atras, a la derecha (antihoraria vista desde arriba). g:
    cuanto mas adentro (el forro)."""
    mx, mzf, mzb = mx - g, mzf - g, mzb - g
    c = ESQUINA * min(mx, mzf, mzb)
    xo = min(xo, mx - c - 0.2)
    return [(-xo, y, -mzf), (-mx + c, y, -mzf), (-mx, y, -mzf + c), (-mx, y, mzb - c), (-mx + c, y, mzb),
            (mx - c, y, mzb), (mx, y, mzb - c), (mx, y, -mzf + c), (mx - c, y, -mzf), (xo, y, -mzf)]


def _abertura(y):
    for (y0, *_, x0), (y1, *_, x1) in zip(BATA, BATA[1:]):
        if y <= y1:
            return x0 + (x1 - x0) * max(0.0, y - y0) / (y1 - y0)
    return BATA[-1][-1]


def bata_pintor():
    crema = tela(CREMA, grano=0.12)
    negro, azul = tela(FORRO, grano=0.06), tela(AZUL, grano=0.08)
    oro = tela(ORO, 0.05, grano=0.08)

    def pintor(t):
        if t.n[0] * t.x + t.n[2] * t.z < 0:                    # el forro (mira hacia el cuerpo)
            return negro(t)
        ax = abs(t.x)
        if t.y < BATA[0][0] + 0.6:                              # el borde de abajo
            return oro(t)
        if t.z < -1.0:                                          # adelante: la solapa negra y su filete
            borde = _abertura(t.y) + SOLAPA
            if ax < borde:
                return negro(t)
            if ax < borde + 0.3:
                return oro(t)
            if any(x0 <= ax <= x1 and y0 <= t.y <= y1 for x0, x1, y0, y1 in RUNA_BATA):
                return oro(t)                                   # las runas doradas de abajo
        if t.z > 1.0 and ax < 2.0:                              # atras: el panel azul con su orilla y su runa
            if ax > 1.72 or any(0.42 < ax + abs(t.y - yc) * 0.7 < 0.66 for yc in (21.0, 19.4)):
                return oro(t)
            return azul(t)
        return crema(t)
    return pintor


def banda_pintor():
    azul, oro = tela(AZUL, grano=0.08), tela(ORO, 0.05, grano=0.08)

    def pintor(t):
        ax = abs(t.x)
        if t.n[2] > -0.3:
            return azul(t)
        if ax > BANDA[0] - 0.3:                                 # las orillas doradas
            return oro(t)
        if any(0.36 < ax + abs(t.y - yc) * 0.7 < 0.6 for yc in (19.0, 17.5)) or abs(t.y - 21.2) < 0.15:
            return oro(t)                                       # la runa: dos rombos encadenados y una raya
        return azul(t)
    return pintor


def _frente_panza(y):
    """Que tan adelante va la panza a esa altura (abajo de lo mas gordo la banda ya cuelga derecha)."""
    gorda = max(TORSO, key=lambda r: r[2])
    if y <= gorda[0]:
        return gorda[2]
    for (y0, _, f0, _), (y1, _, f1, _) in zip(TORSO, TORSO[1:]):
        if y <= y1:
            return f0 + (f1 - f0) * (y - y0) / (y1 - y0)
    return TORSO[-1][2]


def _doble(m):
    """Las caras por los dos lados (para piezas cerradas cuya orientacion no importa revisar)."""
    vs, cs = m
    return vs, list(cs) + [tuple(reversed(c)) for c in cs]


def _subdividir(pts, partes, cerrado=False):
    """Mas puntos entre cada dos puntos (en linea recta)."""
    pts = list(pts) + ([pts[0]] if cerrado else [])
    out = []
    for a, b in zip(pts, pts[1:]):
        out += [tuple(a[c] + (b[c] - a[c]) * i / partes for c in range(3)) for i in range(partes)]
    return out if cerrado else out + [pts[-1]]


def _normales_xz(pts, cerrado=False):
    """La normal hacia afuera (en x, z) de cada punto de una orilla horizontal."""
    n, out = len(pts), []
    for k in range(n):
        a, b = (pts[k - 1], pts[(k + 1) % n]) if cerrado else (pts[max(k - 1, 0)], pts[min(k + 1, n - 1)])
        nx, nz = b[2] - a[2], -(b[0] - a[0])
        largo = math.hypot(nx, nz) or 1.0
        nx, nz = nx / largo, nz / largo
        if nx * pts[k][0] + nz * pts[k][2] < 0 and not cerrado:
            nx, nz = -nx, -nz
        out.append((nx, nz))
    return out


def _plegar(pts, hondo, piso=0, cerrado=False, centro=(0.0, 0.0), orillas=2, gira=0.0):
    """Pliegues de tela: cada punto sale o se mete un poco a lo largo de su normal (aristas y valles alternados que
    bajan derechos; gira > 0 los va corriendo de piso en piso, como tela enrollada). Devuelve (puntos, normales)."""
    if cerrado:
        cx, cz = centro
        ns = []
        for x, _, z in pts:
            largo = math.hypot(x - cx, z - cz) or 1.0
            ns.append(((x - cx) / largo, (z - cz) / largo))
    else:
        ns = _normales_xz(pts)
    out = []
    for k, ((x, y, z), (nx, nz)) in enumerate(zip(pts, ns)):
        if not cerrado and (k < orillas or k >= len(pts) - orillas):
            d = 0.0
        elif gira:
            d = hondo * math.sin(k * math.pi / 2 + piso * gira)
        else:
            d = hondo * (0.6 if k % 2 else -0.4) * (0.85 + 0.3 * _azar(k * 3.7 + piso * 0.13))
        out.append((x + nx * d, y, z + nz * d))
    return out, ns


def _pisos(niveles, entre):
    """Mas niveles entre los niveles dados (en linea recta)."""
    out = []
    for a, b in zip(niveles, niveles[1:]):
        out += [tuple(a[c] + (b[c] - a[c]) * i / entre for c in range(len(a))) for i in range(entre)]
    return out + [niveles[-1]]


def _pintor_punta(pts):
    azul, oro = tela(AZUL, grano=0.08), tela(ORO, 0.05, grano=0.08)

    def pintor(t):
        q = (t.x, t.y, t.z)
        cerca = min(_a_segmento(q, pts[i], pts[(i + 1) % 3]) for i in range(3))
        return oro(t) if cerca < 0.3 else azul(t)
    return pintor


def ropa(p):
    g = "Body/ropa"
    # la bata
    anillos = []
    alto = BATA[-1][0] - BATA[0][0]
    for i, (y, mx, mzf, mzb, xo) in enumerate(_pisos(BATA, PISOS_BATA)):
        f = (BATA[-1][0] - y) / alto                       # 0 en los hombros, 1 abajo
        fuera, ns = _plegar(_subdividir(_u_bata(y, mx, mzf, mzb, xo), 2), PLIEGUE * f, piso=i)
        dentro = [(x - nx * GROSOR_BATA, yy, z - nz * GROSOR_BATA) for (x, yy, z), (nx, nz) in zip(fuera, ns)]
        anillos.append(fuera + dentro[::-1])
    p.malla(g, "bata", geo.loft_puntos(anillos), bata_pintor(), dens=4)
    # las mangas anchas con el puno negro (siguen al brazo hasta la muneca)
    crece, hasta, puno = MANGA
    camino = [b for b in BRAZO if b[1] >= hasta - 1.0]
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        aros = []
        for j, (x, y, z, r) in enumerate(_pisos(camino, 2)):
            aro = _subdividir(_anillo_oval(s * x, max(y, hasta), z, r + crece, r + crece, r + crece), 2, cerrado=True)
            aros.append(_plegar(aro, 0.35, piso=j, cerrado=True, centro=(s * x, z))[0])   # tela fruncida
        p.malla(f"{hueso}/ropa", "manga", geo.loft_puntos(aros[::-1]), tela(CREMA, grano=0.12), dens=4)
        x, _, z, r = camino[-1]
        aros = [_anillo_oval(s * x, y, z, r + crece + 0.1, r + crece + 0.1, r + crece + 0.1, 12) for y in (hasta, puno)]
        p.malla(f"{hueso}/ropa", "puno", geo.loft_puntos(aros), tela(FORRO, grano=0.06),
                dens=4)
    # la bufanda azul: el rollo del cuello y la banda que cuelga sobre la camisa (la panza) y acaba en punta
    azul = tela(AZUL, grano=0.08)
    rollo = [_plegar(_subdividir(_anillo_oval(0.0, y, 0.0, mx, mz, mz), 2, cerrado=True), 0.28, piso=i, cerrado=True,
                     gira=0.9)[0] for i, (y, mx, mz) in enumerate(_pisos(BUFANDA, 2))]     # tela enrollada
    p.malla("Head/bufanda", "rollo", geo.loft_puntos(rollo), azul, dens=4)
    w, y0, y1 = BANDA
    ys = [y0 - (y0 - y1 - 1.5) * i / 16 for i in range(17)]
    aros = []
    for i, y in enumerate(ys):                              # con una ondita y un pliegue al medio
        z = -_frente_panza(y) - 0.05 - 0.12 * math.sin(i * 1.3)
        x = 0.08 * math.sin(i * 0.9)
        aros.append([(x + w, y, z), (x + w, y, z - 0.3), (x + w / 3, y, z - 0.42), (x - w / 3, y, z - 0.42),
                     (x - w, y, z - 0.3), (x - w, y, z)])
    cuerpo_banda = geo.loft_puntos(aros[::-1], tapa_abajo=False)
    abajo = aros[-1]
    n = len(abajo)
    punta = (abajo + [(0.0, y1, -_frente_panza(y1) - 0.2)], [((i + 1) % n, i, n) for i in range(n)])
    p.malla(g, "banda", _doble(geo.unir(cuerpo_banda, punta)), banda_pintor(), dens=4)
    # las puntas del borde de abajo de la bata: azules con filete dorado (2D, por los dos lados)
    for i, tri in enumerate(PUNTAS_BATA):
        for s in (1, -1):
            pts = [(s * x, y, z) for x, y, z in tri]
            p.malla(g, f"punta{i}_{'der' if s > 0 else 'izq'}", _panel(pts), _pintor_punta(pts), dens=4)
    # el colgante dorado de la bufanda
    p.malla(g, "colgante_bufanda", _colgante(COLGANTE_BUFANDA, 3), tela(ORO, 0.08, grano=0), dens=4)
    # el pantalon y las botitas en pico
    negro_p = tela(PANTALON_NEGRO, grano=0.08)
    negro_b, oro = tela(FORRO, grano=0.06), tela(ORO, 0.05, grano=0.08)
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        cx = s * PIERNA_X
        p.malla(f"{hueso}/ropa", "pantalon",
                geo.loft_puntos([_anillo_oval(cx, y, 0.0, mx, mz, mz, 12) for y, mx, mz in PANTALON]), negro_p, dens=4)
        p.malla(f"{hueso}/ropa", "cana",
                geo.loft_puntos([_anillo_oval(cx, y, cz, mx, mz, mz, 12) for y, mx, mz, cz in BOTA]), negro_b, dens=4)
        largo, alto = PICO
        pie = [(cx + 2.3, 0.0, 2.2), (cx + 2.4, 0.0, -1.5), (cx - 2.4, 0.0, -1.5), (cx - 2.3, 0.0, 2.2),
               (cx + 2.3, 2.4, 2.2), (cx + 2.4, 2.2, -1.5), (cx - 2.4, 2.2, -1.5), (cx - 2.3, 2.4, 2.2),
               (cx, alto, -largo)]
        caras = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4), (1, 5, 8), (5, 6, 8), (6, 2, 8),
                 (2, 1, 8)]
        bota = lambda t: oro(t) if t.z < -largo + 2.0 else negro_b(t)
        p.malla(f"{hueso}/ropa", "bota", _doble((pie, caras)), bota, dens=4)
    # la cola esponjada como la de Moles: azul marino y la punta negra
    from .moles import cola
    from .revolthir import voxel
    cola(p, camino=COLA_PIBBLE, base=voxel({"s": "#1F2F42", "b": "#283B50", "l": "#3C556C"}, claro=0.3),
         punta=voxel({"s": "#0B0A0C", "b": "#121014", "l": "#1A171C"}, claro=0.3), corte=0.7)


def construir():
    p = Personaje("pibble", altura=42, cabeza=11, torso=(14, 22, 11), brazo=(4.4, 4.4), pierna=(5, 5))
    p.malla("Head/cabeza", "cabeza", cabeza_malla(), liso(VACIO), dens=4, luz=False)   # el vacio no se sombrea
    ojos(p)
    capucha(p)
    _subir_cabeza(p, CUELLO_Y - CABEZA[0][0])
    cuerpo(p)
    ropa(p)
    hombro, cadera = BRAZO[0], PIERNA_X
    p.m.pivotes.update({"RightArm": (hombro[0], hombro[1], 0.0), "LeftArm": (-hombro[0], hombro[1], 0.0),
                        "RightLeg": (cadera, PIERNA[-1][0], 0.0), "LeftLeg": (-cadera, PIERNA[-1][0], 0.0)})
    return p
