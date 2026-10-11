"""
El sombrero de Bashi (referencias/personajes/bashi_hoja.png): un sombrero de bruja enorme y chueco, de parches.

Lo que se lee en la hoja (vistas, el detalle de la cabeza y el sombrero suelto):
  Cinta: la base de la copa abraza lo de arriba de la cabeza (un poco mas grande que el cubo de 8) y es una fila
    de bloques vino, olivo y mostaza, con una hebilla dorada al frente del lado derecho y bloques que sobresalen.
  Ala: muy ancha (casi tres cabezas), gruesa y de ladrillos en parches; no es plana: se va doblando hacia abajo
    hacia la orilla y del lado DERECHO del personaje (+X, a la izquierda de quien lo ve de frente) cae mucho mas,
    como en la vista de frente y la de espalda de la hoja. Junto a la cara se queda arriba de las cejas.
  Copa: un cono escalonado (bloques apilados que se van achicando, cada piso con su escaloncito) que sube chueco y en
    el tercio de arriba se DOBLA hacia la derecha del personaje (+X) y un poco hacia atras: queda como un brazo
    casi horizontal que termina caido en una puntita, con un cascabel colgando de la punta y otro del medio.
  Cristales: celestes y uno cian, en prismas que salen de la cinta adelante a la IZQUIERDA del personaje (a la
    derecha de quien lo ve), con un par de bloques beige y mostaza entre ellos.
  Cascabeles: dorados y cuadrados, con su tapita, una ranura oscura y una gotita morada que brilla abajo; cuelgan
    de hilos oscuros cortos desde la orilla del ala y desde la punta.

Tecnicas: el ala es una sola malla gruesa por anillos (sin rayas de escalones); la copa es una malla por anillos
que sigue una espina doblada, con un escalon entre piso y piso; la cinta, la hebilla, los bloques, los hilos y las
gotitas son cajas; los cristales y las campanas, mallas chicas. Las texturas son fijas (parches de ladrillos y
bloques elegidos con azar(), nada de ruido por pixel).

Grupos: "Head/sombrero" (cinta, ala, copa baja, cristales y cascabeles del ala), "Head/sombrero/punta" (lo que se
dobla, con su pivote en el doblez para que se bambolee en Figura) y cada cascabel en su subgrupo con el pivote
arriba del hilo ("Head/sombrero/cascabel_N" y "Head/sombrero/punta/cascabel_N").

Limites para las otras partes (ver sombrero()): la cinta va de y = T-1.2 a T+1.6 con medio ancho 4.45; el ala,
pegada a la cinta, tiene la cara de abajo en y = T-0.6 y se dobla hacia afuera (ver ala_abajo(x, z)).
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import (BEIGE, CIAN, CRISTAL, CUERO_OSC, D, MORADO, MOSTAZA, OLIVO, ORO, PARCHES_SOMBRERO, PX,
                    SUELA, T, VINO, VIOLETA, azar, ejes, ladrillos)

G = "Head/sombrero"
GP = G + "/punta"

# ---------------------------------------------------------------------------------------------- medidas
BANDA_R = 4.45                          # medio ancho de la cinta (la cabeza mide 4)
BANDA_Y = (T - 1.2, T + 1.6)            # de donde a donde va la cinta
ALA_Y = T + 0.4                         # arriba del ala, junto a la cinta
ALA_GROSOR = (1.0, 1.0, 0.75)           # adentro, al medio (desde el escalon de arriba) y en la orilla
ESCALON = 0.3                           # el ala tiene dos pisos: el de adentro un escalon mas alto
ALA_LADOS = 16                          # vertices de la orilla del ala (un poligono chueco)
ALA_RADIOS = {"der": 11.0, "izq": 10.2, "frente": 9.4, "atras": 10.2}   # hasta donde llega el ala
ALA_MEDIO = 0.45                        # donde va el anillo del medio (de la cinta a la orilla)


def _suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _orilla(k):
    """Punto (x, z) de la orilla del ala en el vertice k: un cuadrado redondeado y chueco (cada lado con su largo y
    cada vertice corrido un poco)."""
    a = math.radians(360.0 * k / ALA_LADOS)
    c, s = math.cos(a), math.sin(a)             # a = 0 es +X (derecha del personaje), 90 es -Z (el frente)
    rx = ALA_RADIOS["der"] if c > 0 else ALA_RADIOS["izq"]
    rz = ALA_RADIOS["frente"] if s > 0 else ALA_RADIOS["atras"]
    n = 3.0                                     # superelipse: entre circulo y cuadrado
    r = 1.0 / ((abs(c) / rx) ** n + (abs(s) / rz) ** n) ** (1.0 / n)
    r += 0.7 * (azar(k, 31) - 0.5)
    return r * c, -r * s


def _adentro(k):
    """Punto (x, z) del anillo de adentro del ala: sobre un cuadrado de 4.2 (queda escondido dentro de la cinta)."""
    a = math.radians(360.0 * k / ALA_LADOS)
    c, s = math.cos(a), math.sin(a)
    m = max(abs(c), abs(s))
    return 4.2 * c / m, -4.2 * s / m


def _cae(x, z, k):
    """Cuanto baja la orilla del ala en (x, z): un poco en todo el borde, mucho del lado derecho del personaje y un
    poquito atras de ese lado; cada vertice con su pizca (asi el ala queda chueca y no de torno)."""
    return (0.3 + 1.9 * _suave((x - 2.0) / 9.0) + 0.35 * _suave((z - 2.0) / 8.0) * _suave(x / 6.0)
            + 0.25 * (azar(k, 47) - 0.5))


def _anillos_ala():
    """Los anillos del ala por vertice: adentro (x, z, arriba, abajo), medio (x, z, arriba del piso de adentro,
    arriba del piso de afuera, abajo) y orilla (x, z, arriba, abajo)."""
    out = []
    for k in range(ALA_LADOS):
        xi, zi = _adentro(k)
        xo, zo = _orilla(k)
        xm, zm = xi + (xo - xi) * ALA_MEDIO, zi + (zo - zi) * ALA_MEDIO
        cae = _cae(xo, zo, k)
        ym = ALA_Y - 0.3 * cae
        yo = ALA_Y - cae - ESCALON
        out.append(((xi, zi, ALA_Y, ALA_Y - ALA_GROSOR[0]), (xm, zm, ym, ym - ESCALON, ym - ALA_GROSOR[1]),
                    (xo, zo, yo, yo - ALA_GROSOR[2])))
    return out


def ala_abajo(x, z):
    """Altura de la cara de abajo del ala cerca de (x, z) (para que el pelo y las runas no la atraviesen). Toma el
    vertice del ala en esa direccion e interpola de la cinta a la orilla."""
    k = round(math.degrees(math.atan2(-z, x)) / (360.0 / ALA_LADOS)) % ALA_LADOS
    adentro, medio, orilla = _anillos_ala()[k]
    d = math.hypot(x, z)
    di, dm, do = (math.hypot(a[0], a[1]) for a in (adentro, medio, orilla))
    if d <= dm:
        f = max(0.0, (d - di) / max(1e-6, dm - di))
        return adentro[3] + (medio[4] - adentro[3]) * f
    f = min(1.0, (d - dm) / max(1e-6, do - dm))
    return medio[4] + (orilla[3] - medio[4]) * f


# ---------------------------------------------------------------------------------------------- pintores
def _oscura(r):
    """La misma rampa corrida un paso hacia la sombra (para la cara de abajo del ala)."""
    return {"o": r["o"], "s2": r["o"], "s": r["s2"], "b": r["s"], "m": r["b"], "l": r["b"], "h": r["m"]}


PARCHES_ABAJO = tuple(_oscura(r) for r in PARCHES_SOMBRERO)


class _EnCara:
    """Un texel visto en su propia cara (u, v alineados con la grilla de la textura): asi ejes() devuelve (u, v) y
    los ladrillos quedan derechos aunque la cara este inclinada."""
    __slots__ = ("x", "y", "z", "n")


def _marco(n):
    """(derecha, arriba) de la textura de una cara con normal n (igual que taller.malla.marco)."""
    if abs(n[1]) <= 0.9:
        ref = (0.0, 1.0, 0.0)
    else:
        ref = (0.0, 0.0, -1.0) if n[1] > 0 else (0.0, 0.0, 1.0)
    d = ref[0] * n[0] + ref[1] * n[1] + ref[2] * n[2]
    arr = geo._norm((ref[0] - d * n[0], ref[1] - d * n[1], ref[2] - d * n[2]))
    return geo._cross((-n[0], -n[1], -n[2]), arr), arr


def en_cara(pintor):
    """Pintor que ve cada texel en las coordenadas de su cara (para mallas con caras inclinadas)."""
    q = _EnCara()

    def p(t):
        der, arr = _marco(t.n)
        q.x = t.x * der[0] + t.y * der[1] + t.z * der[2]
        q.y = t.x * arr[0] + t.y * arr[1] + t.z * arr[2]
        q.z, q.n = 0.0, (0.0, 0.0, -1.0)
        return pintor(q)
    return p


def _region_ala(x, z):
    """En que lado del ala cae (x, z) (0 derecha, 1 frente, 2 izquierda, 3 atras) y sus (u, v): v es la distancia
    hacia afuera y u corre a lo largo de la orilla. Asi las filas de ladrillos dan la vuelta como un marco."""
    rx = ALA_RADIOS["der"] if x > 0 else ALA_RADIOS["izq"]
    rz = ALA_RADIOS["frente"] if z < 0 else ALA_RADIOS["atras"]
    if abs(x) / rx >= abs(z) / rz:
        return (0, z, x) if x > 0 else (2, -z, -x)
    return (1, x, -z) if z < 0 else (3, -x, z)


def pintor_ala():
    """El ala: arriba ladrillos en parches grandes cuyas filas siguen la orilla (como tablas que dan la vuelta);
    abajo los mismos un paso mas oscuros; el canto, ladrillos de un solo alto (se ven las puntas)."""
    arriba = [ladrillos(PARCHES_SOMBRERO, w=1.25, h=0.75, celda=(3, 3), semilla=3 + 13 * k) for k in range(4)]
    abajo = [ladrillos(PARCHES_ABAJO, w=1.25, h=0.75, celda=(3, 3), semilla=3 + 13 * k) for k in range(4)]
    canto = en_cara(ladrillos(PARCHES_SOMBRERO, w=0.75, h=4.0, celda=(3, 1), semilla=5))
    q = _EnCara()

    def p(t):
        if abs(t.n[1]) <= 0.3:
            return canto(t)
        k, q.x, q.y = _region_ala(t.x, t.z)
        q.z, q.n = 0.0, (0.0, 0.0, -1.0)
        return (arriba if t.n[1] > 0 else abajo)[k](q)
    return p


BLOQUES_CINTA = (VINO, OLIVO, MOSTAZA, VINO, OLIVO, MORADO, MOSTAZA, VINO)


def _bloque_cinta(u):
    """(indice, distancia a la junta de la izquierda) del bloque de la cinta en u: bloques de 1.6 con las juntas
    corridas un poco (anchos parejos pero no iguales)."""
    junta = lambda n: 1.6 * n + 0.45 * math.sin(n * 2.3)
    n = math.floor(u / 1.6)
    while junta(n) > u:
        n -= 1
    while junta(n + 1) <= u:
        n += 1
    return n, u - junta(n)


def pintor_cinta(t):
    """La cinta: una fila de bloques de anchos distintos (vino, olivo, mostaza), cada uno con la junta oscura, el
    canto de arriba claro y el de abajo en sombra; algunos partidos en dos."""
    if t.cara in ("up", "down"):
        return ladrillos(PARCHES_SOMBRERO, w=1.0, h=0.5, semilla=9)(t)
    u = {"north": t.x, "south": -t.x + 9.3, "east": t.z + 17.6, "west": -t.z + 27.1}[t.cara]
    v = t.y - BANDA_Y[0]
    k, dj = _bloque_cinta(u)
    r = BLOQUES_CINTA[int(azar(k, 3) * len(BLOQUES_CINTA))]
    alto = BANDA_Y[1] - BANDA_Y[0]
    mitad = alto * (0.42 + 0.16 * azar(k, 6)) if azar(k, 5) < 0.4 else None
    if mitad is not None and v >= mitad:
        v, techo, r = v - mitad, alto - mitad, BLOQUES_CINTA[int(azar(k, 4) * len(BLOQUES_CINTA))]
    else:
        techo = mitad if mitad is not None else alto
    if dj < PX * 0.999:
        return hex_(r["s2"])
    if techo - v < PX:
        return hex_(r["l"])
    if v < PX:
        return hex_(r["s"])
    return hex_(r["m"] if v > techo - 3 * PX and dj > 2 * PX else r["b"])


def plano(rampa, borde="s", centro="b", brillo="l"):
    """Pintor de un bloque: centro parejo, el contorno de 1 px un tono abajo y el canto de arriba con brillo."""
    def p(t):
        if t.cara in ("up", "down"):
            return hex_(rampa[brillo] if t.cara == "up" else rampa[borde])
        if t.j == 0:
            return hex_(rampa[brillo])
        if t.fila_abajo == 0 or t.i == 0 or t.i == t.tw - 1:
            return hex_(rampa[borde])
        return hex_(rampa[centro])
    return p


def pintor_hebilla(t):
    """Hebilla dorada: marco de oro con el agujero oscuro al medio (por donde pasa la cinta)."""
    if t.cara != "north":
        return hex_(ORO["s"])
    bi, bj = min(t.i, t.tw - 1 - t.i), min(t.j, t.th - 1 - t.j)
    if bi >= 2 and bj >= 2:
        return hex_(CUERO_OSC["s"] if bi >= 3 or bj >= 3 else ORO["s2"])
    return hex_(ORO["l"] if t.j == 0 or t.i == 0 else ORO["b"])


def pintor_cristal(rampa):
    """Prisma de cristal: cada cara de un tono plano segun mire a la luz, con una rayita de brillo en la orilla."""
    luz = geo._norm((0.35, 1.0, -0.45))

    def p(t):
        d = t.n[0] * luz[0] + t.n[1] * luz[1] + t.n[2] * luz[2]
        if t.i == 1 and t.cara not in ("up", "down"):
            return hex_(rampa["h"])
        tono = "l" if d > 0.45 else "m" if d > 0.0 else "b" if d > -0.4 else "s"
        return hex_(rampa.get(tono, rampa["b"]))
    return p


def pintor_campana(t):
    """Cascabel dorado: oro con el canto de arriba claro y una ranura oscura vertical en cada cara."""
    cx, cz = (t.f[0] + t.t[0]) / 2, (t.f[2] + t.t[2]) / 2
    alto = t.y - t.f[1]
    if abs(t.n[1]) < 0.7:
        u = (t.x - cx) if abs(t.n[2]) >= abs(t.n[0]) else (t.z - cz)
        if abs(u) < 0.13 and 0.12 < alto < 0.55:
            return hex_(ORO["o"] if abs(u) < 0.07 else ORO["s2"])
        if t.j == 0:
            return hex_(ORO["h"])
        return hex_(ORO["l"] if (t.n[0] > 0.3 or t.n[2] < -0.3) else ORO["b"])
    return hex_(ORO["l"] if t.n[1] > 0 else ORO["s"])


def pintor_gota(t):
    """Gotita morada que brilla (va con luz=False)."""
    if t.cara == "up":
        return hex_(VIOLETA["l"])
    if t.cara == "down":
        return hex_(VIOLETA["s"])
    if t.j == 0 and t.i == 0:
        return hex_(VIOLETA["h"])
    return hex_(VIOLETA["l"] if t.i == 0 else VIOLETA["b"])


# ---------------------------------------------------------------------------------------------- piezas
def ala(p):
    """El ala: una sola malla gruesa por anillos (la cinta, el medio y la orilla) que se dobla hacia abajo hacia la
    orilla, mucho mas del lado derecho del personaje, en dos pisos: el de adentro un escalon mas alto. Arriba, el
    canto, abajo y el canto de adentro (escondido en la cinta) cierran el solido."""
    anillos = _anillos_ala()
    # la seccion del ala dando la vuelta (antihorario visto de lado, asi las caras miran afuera): orilla abajo,
    # orilla arriba, piso de afuera, escalon, piso de adentro, adentro (escondido en la cinta) y abajo
    pasos = ((2, 3), (2, 2), (1, 3), (1, 2), (0, 2), (0, 3), (1, 4))
    sec = [[(a[i][0], a[i][j], a[i][1]) for a in anillos] for i, j in pasos]
    sec.append(sec[0])
    p.malla(G, "ala", geo.loft_puntos(sec, tapa_abajo=False, tapa_arriba=False), pintor_ala(), dens=D)


def cinta(p):
    """La cinta y la base de la copa: un bloque que abraza lo de arriba de la cabeza, con la hebilla y bloques que
    sobresalen un poco (pegados, metidos en la cinta)."""
    r = BANDA_R
    p.caja(G, "cinta", (-r, BANDA_Y[0], -r), (r, BANDA_Y[1], r), pintor_cinta, dens=D)
    y0 = ALA_Y - 0.1
    p.caja(G, "hebilla", (1.3, y0, -r - 0.2), (2.9, BANDA_Y[1] + 0.15, -r + 0.1), pintor_hebilla, dens=D)
    bloques = (                                  # (desde, hasta, rampa)
        ((-0.9, y0, -r - 0.25), (0.4, BANDA_Y[1] + 0.35, -r + 0.2), BEIGE),
        ((r - 0.2, y0, -2.6), (r + 0.25, BANDA_Y[1] - 0.15, -1.2), OLIVO),
        ((r - 0.2, y0, 1.4), (r + 0.3, BANDA_Y[1] + 0.25, 3.1), MOSTAZA),
        ((-1.6, y0, r - 0.2), (0.3, BANDA_Y[1] + 0.2, r + 0.25), OLIVO),
        ((-r - 0.25, y0, 2.0), (-r + 0.2, BANDA_Y[1] - 0.1, 3.4), VINO),
    )
    for k, (a, b, rampa) in enumerate(bloques):
        p.caja(G, f"bloque{k}", a, b, plano(rampa), dens=D)


# la copa: tramos de la espina (largo, se inclina hacia +X, se inclina hacia atras, radio abajo, radio arriba)
COPA_BASE = (0.15, BANDA_Y[1] - 0.3, 0.25)
TRAMOS = (
    (2.5, 2, 2, 4.10, 3.72),
    (2.3, 4, 3, 3.48, 3.12),
    (2.2, 6, 4, 2.88, 2.52),
    (2.0, 10, 5, 2.30, 2.00),
    (1.7, 32, 8, 1.80, 1.58),                    # desde aca, la punta que se dobla
    (1.7, 62, 12, 1.42, 1.25),
    (2.0, 90, 14, 1.12, 0.98),
    (1.9, 104, 12, 0.86, 0.75),
    (1.5, 128, 10, 0.64, 0.53),
    (1.0, 155, 8, 0.44, 0.28),
)
DOBLA_EN = 4                                     # el tramo donde empieza la punta (su propio grupo)
CHAFLAN = 0.32                                   # la seccion es un cuadrado con las esquinas cortadas


def _direccion(ax, az):
    a, b = math.radians(ax), math.radians(az)
    return geo._norm((math.sin(a) * math.cos(b), math.cos(a) * math.cos(b), math.sin(b)))


def _girar_v(v, eje, ang):
    """Rodrigues: gira v alrededor de eje (unitario) ang radianes."""
    c, s = math.cos(ang), math.sin(ang)
    kv = geo._dot(eje, v)
    kx = geo._cross(eje, v)
    return tuple(v[i] * c + kx[i] * s + eje[i] * kv * (1 - c) for i in range(3))


def _transportar(u, d0, d1):
    """Lleva el vector u del marco con direccion d0 al de direccion d1 (sin torcerlo)."""
    eje = geo._cross(d0, d1)
    s = math.sqrt(geo._dot(eje, eje))
    if s < 1e-9:
        return u
    return _girar_v(u, (eje[0] / s, eje[1] / s, eje[2] / s), math.atan2(s, geo._dot(d0, d1)))


def espina():
    """Juntas de la copa: por junta (punto, direccion de la junta, U, W) con U x W = direccion; la junta entre dos
    tramos va en la bisectriz (inglete), asi el escalon entre piso y piso queda plano."""
    dirs = [_direccion(ax, az) for _, ax, az, _, _ in TRAMOS]
    pts = [COPA_BASE]
    for (largo, *_), d in zip(TRAMOS, dirs):
        q = pts[-1]
        pts.append((q[0] + d[0] * largo, q[1] + d[1] * largo, q[2] + d[2] * largo))
    juntas = []
    u, prev = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    for k, q in enumerate(pts):
        if k == 0:
            j = dirs[0]
        elif k == len(dirs):
            j = dirs[-1]
        else:
            j = geo._norm(tuple(a + b for a, b in zip(dirs[k - 1], dirs[k])))
        u = _transportar(u, prev, j)
        prev = j
        juntas.append((q, j, u, geo._cross(j, u)))
    return juntas, dirs


def _seccion(junta, r, sx=1.0, sw=1.0):
    """Anillo de la copa en una junta: cuadrado de medio ancho r con las esquinas cortadas."""
    q, _, u, w = junta
    c = CHAFLAN
    forma = ((1, -1 + c), (1, 1 - c), (1 - c, 1), (-1 + c, 1), (-1, 1 - c), (-1, -1 + c), (-1 + c, -1), (1 - c, -1))
    return [tuple(q[i] + r * (a * sx * u[i] + b * sw * w[i]) for i in range(3)) for a, b in forma]


def _mover_junta(junta, dist):
    q, j, u, w = junta
    return (tuple(q[i] + j[i] * dist for i in range(3)), j, u, w)


def copa(p):
    """La copa: anillos por la espina doblada; cada tramo es un piso que se angosta y entre piso y piso un
    escaloncito (dos anillos en la misma junta). Abajo (metida en la cinta) va en el grupo del sombrero; desde
    DOBLA_EN, en el grupo de la punta con el pivote en el doblez."""
    juntas, _ = espina()
    pintor = en_cara(ladrillos(PARCHES_SOMBRERO, w=1.0, h=0.75, celda=(3, 4), semilla=11))
    trozos = ((0, DOBLA_EN, G, "copa"), (DOBLA_EN, len(TRAMOS), GP, "punta"))
    for a, b, grupo, nombre in trozos:
        anillos = []
        for k in range(a, b):
            _, _, _, r0, r1 = TRAMOS[k]
            sx, sw = 1.0 + 0.05 * (azar(k, 61) - 0.5), 1.0 + 0.05 * (azar(k, 62) - 0.5)
            ja = juntas[k] if k > a or a == 0 else _mover_junta(juntas[k], -0.2)   # la punta se mete en la copa
            anillos.append(_seccion(ja, r0, sx, sw))
            anillos.append(_seccion(juntas[k + 1], r1, sx, sw))
        p.malla(grupo, nombre, geo.loft_puntos(anillos), pintor, dens=D)
    p.m.pivotes[GP] = juntas[DOBLA_EN][0]


def punto_espina(k, f):
    """Punto de la espina en el tramo k, a la fraccion f de su largo, y su direccion."""
    juntas, dirs = espina()
    q0, q1 = juntas[k][0], juntas[k + 1][0]
    return tuple(q0[i] + (q1[i] - q0[i]) * f for i in range(3)), dirs[k]


def aro_punta(p):
    """Un aro dorado con un cuadrito oscuro (como hebilla) alrededor del brazo de la punta."""
    juntas, dirs = espina()
    k = 6
    q, d = punto_espina(k, 0.55)
    _, _, u, w = juntas[k]
    u = _transportar(u, juntas[k][1], d)
    w = geo._cross(d, u)
    r = TRAMOS[k][3] * 0.93 + 0.14
    anillos = [_seccion((tuple(q[i] - d[i] * 0.25 for i in range(3)), d, u, w), r),
               _seccion((tuple(q[i] + d[i] * 0.25 for i in range(3)), d, u, w), r)]
    oro = en_cara(lambda t: hex_(ORO["l"] if abs(t.x % 1.0 - 0.5) < 0.2 and abs(t.y % 1.0 - 0.5) < 0.2 else
                                 ORO["b"]))
    p.malla(GP, "aro", geo.loft_puntos(anillos), oro, dens=D)


def cascabel(p, grupo, nombre, arriba, hilo):
    """Un cascabel colgando de 'arriba' (x, y, z) con un hilo oscuro de largo 'hilo': tapita, campana cuadrada que
    se abre abajo con su ranura, un labio y la gotita morada abajo. Va en su subgrupo con el pivote arriba del hilo
    (para que se mueva en Figura)."""
    g = f"{grupo}/{nombre}"
    p.m.pivotes[g] = arriba
    x, y, z = arriba
    oscuro = lambda t: hex_(SUELA["b"] if t.i == 0 else SUELA["m"] if t.i == t.tw - 1 else SUELA["s"])
    y1 = y - hilo
    p.caja(g, "hilo", (x - 0.08, y1, z - 0.08), (x + 0.08, y + 0.2, z + 0.08), oscuro, dens=D, luz=False)
    p.caja(g, "tapa", (x - 0.2, y1 - 0.3, z - 0.2), (x + 0.2, y1 + 0.05, z + 0.2), plano(ORO, "s", "b", "h"), dens=D)
    y2 = y1 - 0.25
    alto = 1.0
    campana = geo.tronco(geo.anillo(x, y2 - alto, z, 0.52, 0.52, 4, 45), geo.anillo(x, y2, z, 0.33, 0.33, 4, 45))
    p.malla(g, "campana", campana, pintor_campana, dens=D)
    y3 = y2 - alto
    p.caja(g, "labio", (x - 0.42, y3 - 0.16, z - 0.42), (x + 0.42, y3 + 0.02, z + 0.42), plano(ORO, "s2", "s", "b"),
           dens=D)
    p.caja(g, "gota", (x - 0.15, y3 - 0.6, z - 0.15), (x + 0.15, y3 - 0.12, z + 0.15), pintor_gota,
           rot=(0, 45, 0), piv=(x, y3, z), dens=D, luz=False)


def cascabeles(p):
    """Cinco cascabeles de la orilla del ala (en vertices del ala, ninguno delante de la cara) y dos en la punta:
    uno al medio del brazo y otro colgando de la puntita."""
    anillos = _anillos_ala()
    for n, (k, hilo) in enumerate(((1, 0.9), (6, 0.55), (9, 1.2), (11, 0.7), (14, 1.0))):
        _, medio, orilla = anillos[k]
        f = 0.88                                     # un poco antes de la orilla, bajo el ala
        x, z = medio[0] + (orilla[0] - medio[0]) * f, medio[1] + (orilla[1] - medio[1]) * f
        y = medio[4] + (orilla[3] - medio[4]) * f
        cascabel(p, G, f"cascabel{n}", (x, y + 0.05, z), hilo)
    q, _ = punto_espina(6, 0.5)
    cascabel(p, GP, "cascabel5", (q[0], q[1] - TRAMOS[6][3] * 0.9, q[2]), 0.8)
    juntas, _ = espina()
    q = juntas[-1][0]
    cascabel(p, GP, "cascabel6", (q[0], q[1] - 0.1, q[2]), 0.6)


def _cristal(base, alto, ancho, hondo, rot, rampa, k):
    """Malla de un cristal: prisma de 6 caras aplastado con la punta en piramide (un poco corrida), parado en
    'base' y girado rot = (rx, ry, rz) desde ahi."""
    cuerpo = alto * (0.62 + 0.1 * azar(k, 71))
    abajo = geo.anillo(0, -0.6, 0, ancho / 2, hondo / 2, 6, 0)
    arriba = geo.anillo(0, cuerpo, 0, ancho / 2 * 0.95, hondo / 2 * 0.95, 6, 0)
    prisma = geo.tronco(abajo, arriba, tapa_arriba=False)
    punta = geo.piramide(arriba, (ancho * 0.12 * (azar(k, 72) - 0.5), alto, 0.0), tapa=False)
    m = geo.girar(geo.unir(prisma, punta), rot)
    return geo.mover(m, base)


def cristales(p):
    """Cristales celestes y uno cian que salen de la cinta adelante a la izquierda del personaje, abiertos hacia
    afuera, y un par de bloques beige y mostaza entre ellos."""
    lista = (                                    # (base, alto, ancho, hondo, giro, rampa)
        ((-2.5, BANDA_Y[1] - 0.2, -3.7), 3.4, 1.3, 0.75, (-12, 20, 14), CRISTAL),
        ((-4.3, ALA_Y, -2.4), 3.7, 0.95, 0.7, (-6, -10, 30), CIAN),
        ((-3.9, BANDA_Y[1] - 0.6, -4.3), 2.0, 0.8, 0.6, (-32, 30, 30), CRISTAL),
        ((-1.0, BANDA_Y[1] - 0.2, -4.0), 1.6, 0.7, 0.5, (-30, -15, -8), CRISTAL),
    )
    for k, (base, alto, ancho, hondo, rot, rampa) in enumerate(lista):
        p.malla(G, f"cristal{k}", _cristal(base, alto, ancho, hondo, rot, rampa, k), pintor_cristal(rampa), dens=D,
                luz=False)                                       # ya trae sus caras con luz y brillo pintados
    p.caja(G, "piedra_beige", (-4.0, BANDA_Y[1] - 0.5, -3.6), (-2.9, BANDA_Y[1] + 0.5, -2.5), plano(BEIGE),
           rot=(0, 18, 8), piv=(-3.45, BANDA_Y[1] - 0.5, -3.05), dens=D)
    p.caja(G, "piedra_mostaza", (-5.6, ALA_Y - 0.3, -1.2), (-4.6, ALA_Y + 0.6, -0.1), plano(MOSTAZA),
           rot=(0, -12, -10), piv=(-5.1, ALA_Y - 0.3, -0.65), dens=D)


def sombrero(p):
    """El sombrero completo de Bashi en "Head/sombrero" (ver el docstring del modulo).
    Limites que respetan las otras partes:
      cinta: x, z en [-4.45, 4.45], y de T-1.2 (36.8) a T+1.6 (39.6)
      ala: cara de abajo en y = T-0.65 junto a la cinta; adelante (|x| < 4) no baja de ~T-0.9; hacia +X cae hasta
           ~T-3.4 en la orilla (x ~ 11); llega a x de -10.2 a +11, z de -9.4 a +10.2 (ver ala_abajo)
      copa: sube hasta y ~ T+13 y se dobla hacia +X hasta x ~ 8.5 (la punta cae hasta y ~ T+8)."""
    cinta(p)
    ala(p)
    copa(p)
    aro_punta(p)
    cristales(p)
    cascabeles(p)
