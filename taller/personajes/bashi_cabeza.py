"""
Bashi: la cabeza (ver bashi.py). Hecha a mano segun referencias/personajes/bashi_hoja.png y los colores de
bashi_hoja2.png.

Lo que lleva, de adentro hacia afuera:
  CABEZA: no es un cubo: los pomulos van cortados en diagonal hacia los costados y la quijada se angosta en una
    barbilla mas chica. La cara es una PLACA delante del frente de la cabeza, con un hueco: la CUENCA del ojo grande,
    hundida, que baja hasta donde iria la ojera. Piel durazno con textura de bloques y la sombra y el brillo pintados
    a mano (la cara no lleva luz horneada: el ala no la oscurece). Densidad 8: la cara es un pixel art.
  OJO DERECHO (a la izquierda de quien lo ve): grande, REDONDO y que BRILLA, metido en la cuenca: contorno cian
    oscuro, aro cian con brillo arriba y mas oscuro abajo, y al medio un cuadro blanco que sale un poco con la pupila
    cian. Encima, la ceja gris en bloque, levantada.
  OJO IZQUIERDO: entrecerrado y mas alto que el grande, de picaro: blanco con el iris vino mirando de lado, un
    parpado de bloque que lo tapa a la mitad con la raya de las pestanas, y la ceja gris baja y caida hacia adentro.
  NARIZ delgada con su forma: nace fina en el puente entre los ojos y baja saliendo hasta la punta.
  SONRISA cerrada y tranquila: una raya corta con las puntas apenas levantadas (la de su izquierda un poco mas).
  PELO gris liso en MATAS de bloque pegadas a la cabeza: una capa pegada a los costados y la nuca con las puntas
    disparejas, otra encima mas corta que se abre apenas, unas matas sueltas a los lados (esponja) y matas sobre las
    esquinas de la frente, la de su derecha bajando junto al ojo.
  BIGOTE caido en dos mechones desde las puntas de la boca y BARBA corta de mechones disparejos.

Limites para las otras partes: el pelo no pasa de y = T - 0.8 (37.2); adelante nada sale mas alla de z = -4.9 (la
punta de la nariz); la barba baja hasta y ~ 29.3 por delante del cuello; el pelo de la nuca baja hasta y ~ 30.
Arriba de la cabeza no hay nada: ahi va el sombrero.
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import C, T, DC, PIEL, CANAS, CIAN, azar

G = "Head"
TOPE_PELO = T - 0.8                     # 37.2: de aqui para arriba manda el sombrero (cinta y ala)
TONOS = ("o", "s2", "s", "b", "m", "l", "h")      # de oscuro a claro, para correr un tono k pasos


def _t(rampa, k):
    """El tono k de la rampa (k = indice en TONOS, se recorta a la rampa)."""
    return rampa[TONOS[max(0, min(len(TONOS) - 1, k))]]


def _mezcla(a, b):
    ca, cb = hex_(a), hex_(b)
    return "#%02X%02X%02X" % tuple((x + y) // 2 for x, y in zip(ca[:3], cb[:3]))


PIEL_SB = _mezcla(PIEL["s"], PIEL["b"])  # sombra suave de la cara

# ---------------------------------------------------------------------------------------------- medidas de la cara
# en px del modelo; la cara mira a -Z y la derecha del personaje es +X (a la izquierda de quien lo ve)
FRENTE_Z = -3.625                       # el frente de la cabeza; la placa de la cara sale hasta z = -4
OJO = (1.75, 34.25, 1.25)               # centro (x, y) y radio del ojo grande
CUENCA = (0.25, 3.25, 32.25, 35.75)     # el hueco del ojo grande con la ojera abajo: x0, x1, y0, y1
LENTE_Z = (-3.875, FRENTE_Z)            # el ojo queda metido en la cuenca
BLANCO, BLANCO_Z = 0.625, -3.95         # medio lado y frente del cuadro blanco (sale un poco del ojo)
NARIZ_X = -0.4375                       # la nariz va entre los dos ojos, apenas hacia su izquierda
NARIZ = ((32.0, 0.375, -4.7), (32.375, 0.375, -4.9), (32.875, 0.3125, -4.7), (33.75, 0.25, -4.35),
         (34.5, 0.1875, -4.08))         # (y, medio ancho, z de la punta) de abajo (las fosas) al puente entre los ojos
PARPADO = ((-3.375, 34.75, -4.125), (-1.125, 35.25, -3.9))
CEJA_DER = ((0.0, 35.875, -4.625), (3.25, 36.5, -3.95), 8.0)      # sobre el ojo grande: levantada, la punta de afuera arriba
CEJA_IZQ = ((-3.375, 35.5, -4.5), (-0.75, 36.25, -3.95), -7.0)   # sobre el ojo chico: baja y caida hacia adentro
OJO_CHICO = 12                          # texeles que sube el ojo chico (queda mas alto que el grande)
BOCA = (-1.25, 1.5, 12)                 # u de punta a punta (de izquierda a derecha de quien lo ve) y fila de la raya

# la placa de la cara, en pedazos alrededor de la cuenca: ((x0, y0), (x1, y1)); abajo se angosta con la quijada
PLACA = (((-3.375, 32.0), (0.25, 36.75)), ((3.25, 32.0), (3.375, 36.75)), ((0.25, 35.75), (3.25, 36.75)),
         ((0.25, 32.0), (3.25, 32.25)), ((-2.75, 31.0), (2.75, 32.0)), ((-2.25, 30.0), (2.25, 31.0)))

# la forma de la cabeza: secciones de abajo (la barbilla) hacia arriba. Adelante es plana y los pomulos van cortados
# en diagonal hacia los costados; abajo la quijada se angosta en una barbilla mas chica.
# (y, medio ancho del frente, medio ancho de los costados, z donde el corte llega al costado, medio ancho atras,
#  z de atras)
FORMA = ((30.0, 2.25, 2.75, -3.125, 2.0, 1.5), (31.0, 2.75, 3.5, -2.875, 3.0, 3.0), (32.0, 3.375, 4.0, -3.0, 3.5, 4.0),
         (T, 3.375, 4.0, -3.0, 3.5, 4.0))


def boca(i, j):
    """La sonrisa cerrada: una raya de un texel con las puntas apenas levantadas (la de su izquierda un poco mas)."""
    i0, i1 = math.floor(BOCA[0] * 8), math.floor(BOCA[1] * 8) - 1
    if not i0 <= i <= i1:
        return False
    sube = 2 if i == i1 else 1 if (i <= i0 + 1 or i >= i1 - 2) else 0
    return j == BOCA[2] + sube


def cara(u, v):
    """La cara pixel a pixel (u, v en px: u de izquierda a derecha de quien la ve, v desde la barbilla). El ojo
    grande, la nariz, el parpado y las cejas son piezas 3D; aqui va lo pintado: el ojo chico y la sonrisa."""
    i, j = math.floor(u * 8), math.floor(v * 8)
    # --- el ojo chico (el parpado de bloque tapa la mitad de arriba); OJO_CHICO lo sube
    j -= OJO_CHICO
    if 10 <= i <= 25 and 20 <= j <= 25:
        if j == 20 and not 12 <= i <= 23:
            return PIEL["s2"]
        if 11 <= i <= 16:                                        # iris vino, mirando hacia la nariz
            if 13 <= i <= 14 and 21 <= j <= 23:
                return "#2A0C18"                                 # pupila
            if (i, j) == (15, 23):
                return "#F4E8EC"                                 # brillito
            if i in (11, 16) or j == 20:
                return "#4A1428"
            return "#7E2E50" if j >= 23 else "#9A4468"
        return "#EEE6DC"
    if j == 19 and 11 <= i <= 24:
        return PIEL["s2"]                                        # parpado de abajo
    if j == 26 and i in (9, 26):
        return PIEL["o"]                                         # las puntas de las pestanas
    j += OJO_CHICO
    if boca(i, j):
        return PIEL["o"]
    return PIEL["b"]


NARIZ_SOMBRA = {(j, i) for j in range(16, 30) for i in (2, 3)} | {(15, i) for i in range(-1, 4)}   # (j, i) a su izquierda


def textura_piel(u, v):
    """La piel con textura de bloques de 2 x 2 texeles: casi todos base y algunos un poco mas claros (patron fijo)."""
    r = azar(math.floor(u * 4), math.floor(v * 4), 31)
    return PIEL["m"] if r > 0.85 else PIEL["b"]


def sombra_cara(u, v, col):
    """Sombra y brillo pintados sobre la piel: la sombra suave bajo el pelo y el ala, la que hace la nariz hacia su
    izquierda (la luz viene de su derecha) y la del menton; el brillo en el pomulo bajo el ojo chico."""
    if col not in (PIEL["b"], PIEL["m"]):
        return col                                               # lo pintado (ojo, boca) no se toca
    i, j = math.floor(u * 8), math.floor(v * 8)
    if j >= 54 or j <= 1 or (j, i) in NARIZ_SOMBRA:
        return PIEL_SB if j < 60 else PIEL["s"]
    if 25 <= j <= 27 and 10 <= i <= 22:
        return PIEL["l"]                                         # brillo en el pomulo
    return col


def piel_cara(t):
    """La piel del frente de la cara (la placa): ojo chico y boca pintados, textura, sombra y brillo."""
    u, v = -t.x, t.y - C
    col = cara(u, v)
    if col == PIEL["b"]:
        col = textura_piel(u, v)
    return hex_(sombra_cara(u, v, col))


def placa(t):
    """Pintor de los pedazos de la placa: el frente es la cara; los cantos (las paredes de la cuenca) en sombra."""
    if t.cara == "north":
        return piel_cara(t)
    return hex_(PIEL["s"])


def cabeza_malla():
    """La cabeza con su forma: cada seccion es un octagono (el frente plano, los pomulos cortados, los costados y
    las esquinas de atras apenas cortadas)."""
    anillos = []
    for y, fw, sw, zc, bw, zb in FORMA:
        zbc = zb - (sw - bw)
        anillos.append([(sw, y, zbc), (sw, y, zc), (fw, y, FRENTE_Z), (-fw, y, FRENTE_Z), (-sw, y, zc),
                        (-sw, y, zbc), (-bw, y, zb), (bw, y, zb)])
    return geo.loft_puntos(anillos)


def piel_cabeza(t):
    """Pintor de la cabeza: el frente (casi todo tapado por la placa) en sombra dentro de la cuenca; los pomulos en
    sombra suave; arriba, a los costados y atras el pelo de mas adentro, gris liso, con las puntas disparejas
    sobre la piel."""
    nx, ny, nz = t.n
    v = t.y - C
    if nz < -0.95:
        x0, x1, y0, y1 = CUENCA
        return hex_(PIEL["s"] if x0 <= t.x <= x1 and y0 <= t.y <= y1 else PIEL["b"])
    if ny > 0.6:
        return hex_(CANAS["s"])
    if ny < -0.6:
        return hex_(PIEL["s"])
    if t.z < -2.5:                                               # los pomulos y la sien
        return hex_(CANAS["s"] if v > 6.25 else PIEL_SB)
    borde = 0.5 + _disparejo(t.z, 1 if nx > 0 else 2) if t.z < -1.0 else -1.0
    return hex_(CANAS["s"] if v > borde else PIEL["s"])


def _disparejo(u, semilla):
    """Borde de abajo del pelo pintado: cada tramo de 0.5 px baja distinto (puntas)."""
    k = math.floor((u + 50) / 0.5)
    return (0.0, 0.5, 0.25, 0.75, 0.375)[int(azar(k, semilla) * 5) % 5]


# ---------------------------------------------------------------------------------------------- el ojo grande
def _circulo(cx, cy, r, lados=16):
    return [(cx + r * math.cos(2 * math.pi * k / lados), cy + r * math.sin(2 * math.pi * k / lados))
            for k in range(lados)]


def lente(t):
    """El ojo redondo que brilla, de afuera hacia adentro: contorno cian oscuro, aro cian con un brillo arriba
    (del lado de quien lo ve a la izquierda) y mas oscuro abajo del otro lado, y una linea clara junto al blanco."""
    if abs(t.n[2]) < 0.9:
        return hex_(CIAN["o"])
    cx, cy, r = OJO
    dx, dy = t.x - cx, t.y - cy
    d = math.hypot(dx, dy)
    if d > r - 0.2:
        return hex_(CIAN["o"])
    if 0.9 <= d < 1.03:
        return hex_(CIAN["l"])
    if dx > 0.2 and dy > 0.2 and d < 0.9:
        return hex_(CIAN["h"] if dx + dy > 0.95 else CIAN["l"])  # brillo arriba
    if dx < -0.2 and dy < -0.2:
        return hex_(CIAN["s"])                                   # abajo, del otro lado, mas oscuro
    return hex_(CIAN["b"])


def blanco(t):
    """El cuadro blanco que sale un poco del ojo, con la pupila cuadrada cian al medio; sus cantos, cian claro."""
    if t.cara != "north":
        return hex_(CIAN["l"])
    n = t.tw - 1
    a, b = t.i, t.th - 1 - t.j
    d = min(a, n - a, b, n - b)
    if d >= 3:
        return hex_(CIAN["b"] if (a, b) == (4, 5) else CIAN["s"])       # pupila (con un puntito de brillo)
    if d == 2:
        return hex_(CIAN["l"])
    return hex_(CIAN["h"] if a + b > 2 else "#FFFFFF")


def ojo_grande(p):
    g = f"{G}/ojo"
    cx, cy, r = OJO
    p.malla(g, "lente", geo.extruir(_circulo(cx, cy, r), *LENTE_Z), lente, dens=DC, luz=False)
    p.caja(g, "blanco", (cx - BLANCO, cy - BLANCO, BLANCO_Z), (cx + BLANCO, cy + BLANCO, LENTE_Z[0] + 0.05), blanco,
           dens=DC, luz=False)


# ---------------------------------------------------------------------------------------------- nariz, parpado y cejas
def nariz_malla():
    """La nariz con su forma: delgada, nace fina en el puente entre los ojos, baja saliendo hasta la punta
    redondeada y abajo se ensancha apenas en las fosas."""
    anillos = []
    for y, w, zf in NARIZ:
        x0, x1, zb = NARIZ_X - w, NARIZ_X + w, -3.95
        anillos.append([(x1, y, zb), (x1, y, zf), (x0, y, zf), (x0, y, zb)])
    return geo.loft_puntos(anillos)


def nariz(t):
    """La nariz, un tono por lado para que se lea: el frente un poco mas claro que la cara, los costados un tono
    abajo y abajo las dos fosas."""
    nx, ny, nz = t.n
    if ny < -0.6:
        fosa = abs(abs(t.x - NARIZ_X) - 0.19) < 0.07 and t.z < -4.3
        return hex_(PIEL["o"] if fosa else PIEL["s"])
    if abs(nx) > 0.6:
        return hex_(PIEL["s"])
    return hex_(PIEL["m"])


def parpado(t):
    """El parpado de bloque del ojo chico: piel con la raya gruesa de las pestanas en el canto de abajo."""
    c = t.cara
    if c == "down" or (c == "north" and t.fila_abajo <= 1):
        return hex_("#3A1A1C" if c == "north" else PIEL["s2"])
    if c == "north":
        return hex_(PIEL["s"] if t.j == 0 else PIEL["b"])
    return hex_(PIEL["s"])


def ceja(t):
    """Ceja de bloque gris liso: el frente y arriba en su gris, abajo y los lados un tono mas oscuro."""
    if t.cara in ("north", "up"):
        return hex_(CANAS["m"])
    return hex_(CANAS["s"])


def facciones(p):
    g = f"{G}/cara"
    for k, (a, b) in enumerate(PLACA):
        p.caja(g, f"placa{k}", (a[0], a[1], -4.0), (b[0], b[1], FRENTE_Z), placa, dens=DC, luz=False)
    p.malla(g, "nariz", nariz_malla(), nariz, dens=DC, luz=False)
    p.caja(g, "parpado", *PARPADO, parpado, dens=DC, luz=False)
    for nombre, (a, b, giro) in (("ceja_der", CEJA_DER), ("ceja_izq", CEJA_IZQ)):
        centro = tuple((a[k] + b[k]) / 2 for k in range(3))
        p.caja(g, nombre, a, b, ceja, rot=(0, 0, giro), piv=centro, dens=DC, luz=False)


# ---------------------------------------------------------------------------------------------- pelo, bigote y barba
TONO_MATA = ("b", "m", "b", "l", "m", "b", "m")     # gris liso, cada mata con su tono


def gris(tono):
    c = hex_(CANAS[tono])
    return lambda t: c


def mata(p, nombre, desde, hasta, k, rot=None, piv=None, tono=None):
    """Una mata de pelo: un bloque gris liso."""
    p.caja(f"{G}/pelo", nombre, desde, hasta, gris(tono or TONO_MATA[k % len(TONO_MATA)]), rot=rot, piv=piv, dens=DC)


# a los costados, columnas a lo largo de z: (z0, z1, donde termina la de adentro); la de afuera va encima, mas corta
COSTADO = ((-3.7, -2.3, 31.2), (-2.45, -0.95, 30.6), (-1.1, 0.4, 30.9), (0.25, 1.75, 30.4), (1.6, 3.1, 30.7),
           (2.95, 4.7, 30.5))
COSTADO_AFUERA = ((-3.3, -1.8, 33.6), (-1.95, -0.45, 32.8), (-0.6, 0.9, 33.2), (0.75, 2.25, 32.6), (2.1, 3.6, 33.4))
NUCA = ((-4.3, -2.75, 30.4), (-2.9, -1.35, 30.0), (-1.5, 0.05, 30.6), (-0.1, 1.45, 30.1), (1.3, 2.85, 30.5),
        (2.7, 4.3, 30.2))
NUCA_AFUERA = ((-3.6, -2.0, 33.0), (-2.15, -0.55, 32.4), (-0.7, 0.9, 33.4), (0.75, 2.35, 32.6), (2.2, 3.8, 33.2))
ESPONJA = ((35.0, 36.6, -1.5, 0.0), (33.6, 35.2, 0.8, 2.3), (34.4, 36.0, -2.9, -1.7))     # (y0, y1, z0, z1)
FRENTE = (((2.2, 35.95), (3.5, 37.2)), ((3.3, 34.4), (4.15, 37.2)), ((-3.6, 36.0), (-2.2, 37.2)),
          ((-4.15, 34.8), (-3.4, 37.2)), ((-0.75, 36.3), (0.85, 37.2)))    # matas sobre la frente: ((x0, y0), (x1, y1))


def pelo(p):
    """El pelo gris liso en matas de bloque pegadas a la cabeza, que salen por debajo del ala: una capa pegada a los
    costados y la nuca con las puntas disparejas, otra encima mas corta que se abre apenas hacia afuera, unas matas
    sueltas a los costados (esponja) y matas sobre las esquinas de la frente."""
    y0 = TOPE_PELO
    k = 0
    for s in (1, -1):
        for n, (z0, z1, fin) in enumerate(COSTADO):
            x1, x2 = sorted((s * 3.95, s * 4.7))
            mata(p, f"costado{s}_{n}", (x1, fin - (0.3 if s < 0 and n % 2 else 0), z0), (x2, y0, z1), k)
            k += 1
        x1, x2 = sorted((s * 3.3, s * 4.0))                      # relleno junto a la quijada: no se ve el hueco
        mata(p, f"relleno{s}", (x1, 30.4, -2.9), (x2, 32.2, 3.6), k, tono="s")
        for n, (z0, z1, fin) in enumerate(COSTADO_AFUERA):
            x1, x2 = sorted((s * 4.55, s * 5.35))
            mata(p, f"afuera{s}_{n}", (x1, fin, z0), (x2, y0 - 0.2, z1), k + 1, rot=(0, 0, s * 7),
                 piv=(s * 4.55, y0 - 0.2, (z0 + z1) / 2))
            k += 1
        for n, (ya, yb, z0, z1) in enumerate(ESPONJA):
            x1, x2 = sorted((s * 5.2, s * 5.9))
            mata(p, f"esponja{s}_{n}", (x1, ya, z0), (x2, yb, z1), 3)
    for n, (x0, x1, fin) in enumerate(NUCA):
        mata(p, f"nuca{n}", (x0, fin, 3.95), (x1, y0, 4.7), k)
        k += 1
    for n, (x0, x1, fin) in enumerate(NUCA_AFUERA):
        mata(p, f"nuca_afuera{n}", (x0, fin, 4.55), (x1, y0 - 0.2, 5.3), k + 1, rot=(-7, 0, 0),
             piv=((x0 + x1) / 2, y0 - 0.2, 4.55))
        k += 1
    for n, (a, b) in enumerate(FRENTE):
        mata(p, f"frente{n}", (a[0], a[1], -4.45), (b[0], b[1], -4.0), n + 1)


def pintor_mechon(tono, k):
    """Mechon gris liso, en el tono del mechon."""
    return gris(TONOS[max(0, min(len(TONOS) - 1, tono))])


def mechon(p, nombre, raiz, lado, ancho, largo, grueso=0.5, abre=0.0, abanico=0.0, tono=3, k=0,
           largo2=0.0, dobla=0.0, gira2=0.0, grupo="pelo"):
    """Un mechon de bloque que cuelga desde 'raiz' (el medio de arriba de su cara de adentro, pegada a la cabeza).
    lado: 'e' (su derecha, +X), 'w' (su izquierda), 's' (atras) o 'n' (adelante). abre: cuanto se separa la punta
    de la cabeza (0 cuelga derecho, 90 sale de lado); abanico: giro en su propio plano. Con largo2 lleva una punta
    mas angosta que se dobla 'dobla' grados mas hacia afuera y 'gira2' mas en su plano."""
    g = f"{G}/{grupo}"

    def caja(n, r, an, la, gr, ab, abn, tn):
        x, y, z = r
        if lado in ("e", "w"):
            s = 1 if lado == "e" else -1
            x1, x2 = sorted((x, x + s * gr))
            desde, hasta, rot = (x1, y - la, z - an / 2), (x2, y + (0.15 if n != nombre else 0), z + an / 2), (abn, 0, s * ab)
        elif lado == "s":
            desde, hasta, rot = (x - an / 2, y - la, z), (x + an / 2, y + (0.15 if n != nombre else 0), z + gr), (-ab, 0, abn)
        else:
            desde, hasta, rot = (x - an / 2, y - la, z - gr), (x + an / 2, y + (0.15 if n != nombre else 0), z), (ab, 0, abn)
        p.caja(g, n, desde, hasta, pintor_mechon(tn, k), rot=rot, piv=r, dens=DC)
        return rot

    rot = caja(nombre, raiz, ancho, largo, grueso, abre, abanico, tono)
    if largo2:
        junta = geo.girar(([(raiz[0], raiz[1] - largo, raiz[2])], []), rot, raiz)[0][0]
        caja(nombre + "_p", junta, ancho * 0.75, largo2, grueso - 0.0625, abre + dobla, abanico + gira2,
             tono + (1 if azar(k, 9) > 0.5 else 0))


BARBA = ((-1.375, 1.0, 1.0, 0.5, -10, 3), (-0.25, 1.25, 1.375, 0.625, 4, 4), (1.0, 1.0, 0.875, 0.5, 12, 3))
# (x, ancho, largo, grueso, abanico, tono)


def bigote_y_barba(p):
    """Bigote caido: dos mechones que cuelgan de las puntas de la boca y se abren. Barba de chivo corta: una tira
    pegada bajo la boca con tres mechones disparejos que pasan el menton, y en la quijada mechones que la juntan
    con el pelo de los costados."""
    mechon(p, "bigote_der", (1.55, 31.95, -4.0), "n", 1.0, 1.375, grueso=0.5, abre=10, abanico=20, tono=4,
           k=200, largo2=1.125, gira2=-12, dobla=-4, grupo="bigote")
    mechon(p, "bigote_izq", (-1.8, 32.05, -4.0), "n", 0.875, 1.125, grueso=0.5, abre=10, abanico=-22, tono=4,
           k=201, largo2=0.875, gira2=10, dobla=-4, grupo="bigote")
    g = f"{G}/barba"
    p.caja(g, "base", (-1.875, 29.875, -4.375), (1.625, 30.5, -4.0), pintor_mechon(3, 202), dens=DC)
    k = 210
    for n, (x, an, la, gr, abn, tn) in enumerate(BARBA):
        mechon(p, f"barba{n}", (x, 30.5, -4.375), "n", an, la, grueso=gr, abre=6, abanico=abn, tono=tn, k=k,
               grupo="barba")
        k += 1
    for s, lado in ((1, "e"), (-1, "w")):
        mechon(p, f"quijada_{lado}", (s * 3.7, 31.5, -2.9), lado, 1.5, 1.75, grueso=0.75, abre=12, abanico=10,
               tono=3, k=k, grupo="barba")
        k += 1


# ---------------------------------------------------------------------------------------------- armado
def cabeza(p):
    p.malla(f"{G}/cabeza", "cabeza", cabeza_malla(), piel_cabeza, dens=DC, luz=False)
    ojo_grande(p)
    facciones(p)
    pelo(p)
    bigote_y_barba(p)
