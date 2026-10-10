"""
Bashi: la cabeza (ver bashi.py). Hecha a mano segun referencias/personajes/bashi_hoja.png (el acercamiento de la
cara y las cuatro vistas).

Lo que lleva, de adentro hacia afuera:
  CABEZA: cubo de 8 x 8 x 8 a densidad 8 (la cara es un pixel art de 64 x 64), piel durazno lisa y sin luz
    horneada: solo la sombra a mano donde hace falta (bajo la cinta del sombrero, la cuenca del ojo, la nariz, la
    boca y el menton). Arriba, a los costados y en la nuca va pintado el pelo de mas adentro (gris oscuro), asi entre
    mechon y mechon nunca se ve piel.
  OJO DERECHO (a la izquierda de quien lo ve): enorme, cuadrado y que BRILLA: un lente en 3D con las esquinas
    cortadas que sale de la cara, con contorno cian oscuro, aro cian, un cuadro blanco que sale un poco mas (el ojo
    se abomba) y la pupila cuadrada cian al medio. Encima, la ceja gris gruesa en bloque, levantada y chueca.
  OJO IZQUIERDO: chico y entrecerrado, de picaro: blanco con el iris vino mirando de lado, un parpado de bloque que
    lo tapa a la mitad con la raya gruesa de las pestanas, la ojera abajo y la ceja gris baja y caida hacia adentro.
  NARIZ de bloque que sale casi un px, con el puente arriba, pintada con su luz y su sombra.
  SONRISA chueca y abierta que sube hacia su izquierda: adentro rojo oscuro con la lengua, la fila de dientes de
    arriba, el labio marcado y las arrugas de la risa en las comisuras.
  PELO gris revuelto en mechones de bloque (cajas, sin luz y sin sombras adentro): una capa pegada a los costados y
    a la nuca con las puntas disparejas, otra encima con mechones que se abren hacia afuera (mas locos a su
    derecha), copetes que salen de lado justo bajo el ala y mechones que caen sobre las esquinas de la frente.
  BIGOTE caido en dos mechones de bloque que cuelgan de las comisuras (el de su derecha mas largo) y BARBA corta de
    mechones disparejos en el menton y la quijada.

Limites para las otras partes: el pelo no pasa de y = T - 0.8 (37.2) salvo los mechones que salen de lado bajo el
ala; adelante nada sale mas alla de z = -5.0 (la punta de la nariz); el bigote y la barba bajan hasta y ~ 29.3
por delante del cuello (z < -4); el pelo de la nuca baja hasta y ~ 29.8 por detras (z > 4). Arriba de la cabeza no
hay nada: ahi va el sombrero.
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import C, T, DC, CABEZA_CAJA, PIEL, CANAS, CIAN, azar

G = "Head"
TOPE_PELO = T - 0.8                     # 37.2: de aqui para arriba manda el sombrero (cinta y ala)
TONOS = ("o", "s2", "s", "b", "m", "l", "h")      # de oscuro a claro, para correr un tono k pasos


def _t(rampa, k):
    """El tono k de la rampa (k = indice en TONOS, se recorta a la rampa)."""
    return rampa[TONOS[max(0, min(len(TONOS) - 1, k))]]


# ---------------------------------------------------------------------------------------------- medidas de la cara
# en px del modelo; la cara mira a -Z (z = -4) y la derecha del personaje es +X (a la izquierda de quien lo ve)
LENTE = (0.25, 3.25, 32.75, 35.75)      # x0, x1, y0, y1 del ojo grande (3 x 3)
LENTE_Z = (-4.175, -3.95)               # sale 0.175 de la cara
CHAFLAN = 0.375                         # esquinas cortadas del lente
BLANCO_Z = -4.25                        # el cuadro blanco sale un poco mas: el ojo se abomba
NARIZ = ((-1.0, 32.0, -5.0), (0.125, 33.75, -4.0))
PUENTE = ((-0.875, 33.75, -4.5), (0.0, 34.5, -4.0))
PARPADO = ((-3.375, 33.25, -4.125), (-1.125, 33.75, -3.9))
CEJA_DER = ((0.0, 35.875, -4.625), (3.25, 36.5, -3.95), 8.0)      # sobre el ojo grande: levantada, la punta de afuera arriba
CEJA_IZQ = ((-3.375, 34.0, -4.5), (-0.75, 34.75, -3.95), -7.0)   # sobre el ojo chico: baja y caida hacia adentro
BOCA_IZQ, BOCA_DER = (-2.25, 1.375), (2.5, 2.0)                 # comisuras (u, v) en la cara: sube hacia su izquierda
BOCA_HONDO = 0.875


def _boca_arriba(u):
    """Altura v del labio de arriba (recto, chueco: sube de una comisura a la otra)."""
    (u0, v0), (u1, v1) = BOCA_IZQ, BOCA_DER
    return v0 + (u - u0) * (v1 - v0) / (u1 - u0)


def _boca_abajo(u):
    """Altura v del labio de abajo: una curva que baja al medio (mas honda un poco a su izquierda)."""
    (u0, _), (u1, _) = BOCA_IZQ, BOCA_DER
    medio, mitad = (u0 + u1) / 2 + 0.25, (u1 - u0) / 2
    q = max(0.0, 1.0 - ((u - medio) / mitad) ** 2)
    return _boca_arriba(u) - BOCA_HONDO * q ** 0.6


# texeles (i, j) de la cara (8 por px; i de izquierda a derecha de quien la ve, j desde la barbilla)
ARRUGAS = {(-19, 10), (-19, 12), (-20, 13), (-20, 14), (-21, 15), (-21, 16), (-22, 17),     # risa, comisura derecha
           (20, 15), (21, 17), (22, 18), (23, 19), (23, 20), (24, 21)}                       # risa, comisura izquierda


def cara(u, v):
    """La cara pixel a pixel (u, v en px: u de izquierda a derecha de quien la ve, v desde la barbilla). El ojo
    grande, la nariz, el parpado y las cejas son piezas 3D encima; aqui va lo pintado: la cuenca del ojo grande, el
    ojo chico, la sonrisa, las arrugas y las sombras a mano."""
    i, j = math.floor(u * 8), math.floor(v * 8)
    x0, x1, y0, y1 = LENTE
    li0, li1, lj0, lj1 = math.floor(-x1 * 8), math.floor(-x0 * 8) - 1, math.floor((y0 - C) * 8), math.floor((y1 - C) * 8) - 1
    # --- la cuenca del ojo grande: un anillo oscuro alrededor del lente y la sombra abajo
    if li0 - 1 <= i <= li1 + 1 and lj0 - 1 <= j <= lj1 + 1:
        if li0 <= i <= li1 and lj0 <= j <= lj1:
            return CIAN["o"]                                     # detras del lente (se ve en las esquinas cortadas)
        return PIEL["s2"]
    if li0 <= i <= li1 and j == lj0 - 2:
        return PIEL["s"]
    # --- el ojo chico (el parpado de bloque tapa la mitad de arriba)
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
        if j == 25:
            return "#BFB2A8"                                     # la sombra del parpado sobre el blanco
        return "#EEE6DC" if i < 24 else "#D8CEC4"
    if j == 19 and 11 <= i <= 24:
        return PIEL["s2"]                                        # parpado de abajo
    if j == 18 and 13 <= i <= 23:
        return PIEL["s"]                                         # la ojera
    if j == 26 and i in (9, 26):
        return PIEL["o"]                                         # las puntas de las pestanas
    # --- la sonrisa
    ua = (i + 0.5) / 8
    va = (j + 0.5) / 8
    (u0, _), (u1, _) = BOCA_IZQ, BOCA_DER
    if u0 < ua < u1:
        arriba, abajo = _boca_arriba(ua), _boca_abajo(ua)
        if abajo <= va < arriba:
            if arriba - va < 0.375 and u0 + 0.375 < ua < u1 - 0.375:
                if i % 4 == 0:
                    return "#5A1A1E"                             # entre diente y diente
                return "#F2ECDE" if arriba - va < 0.25 else "#D6CCBA"
            if va - abajo < 0.3 and abs(ua - 0.4) < 1.3:
                return "#B04A46" if va - abajo >= 0.18 else "#9A3A3A"       # la lengua
            return "#4A1216"
        if arriba <= va < arriba + 0.125:
            return PIEL["o"]                                     # el labio de arriba
        if abajo - 0.125 <= va < abajo:
            return PIEL["s2"]
        if abajo - 0.25 <= va < abajo - 0.125:
            return PIEL["l"]                                     # el brillo del labio de abajo
    if (i, j) in ARRUGAS:
        return PIEL["s2"]
    # --- sombras de la nariz (la luz viene de su derecha: la sombra cae a su izquierda y abajo)
    if i == 9 and 16 <= j <= 29:
        return PIEL["s"]
    if 1 <= i <= 9 and j == 15:
        return PIEL["s"]
    # --- la sombra bajo la cinta del sombrero y el contorno del menton
    if j >= 51:
        return PIEL["s"]
    if j == 0:
        return PIEL["s"]
    return PIEL["b"]


def _disparejo(u, semilla):
    """Borde de abajo del pelo pintado: cada tramo de 0.5 px baja distinto (puntas)."""
    k = math.floor((u + 50) / 0.5)
    return (0.0, 0.5, 0.25, 0.75, 0.375)[int(azar(k, semilla) * 5) % 5]


def piel_cabeza(t):
    """Pintor del cubo de la cabeza: la cara adelante; arriba, a los costados y atras el pelo de mas adentro (gris
    oscuro, con las puntas disparejas) y la piel abajo; bajo la barbilla, piel en sombra."""
    c, v = t.cara, t.y - C
    if c == "north":
        return hex_(cara(-t.x, v))
    if c == "up":
        return hex_(CANAS["s"])
    if c == "down":
        return hex_(PIEL["s"])
    if c in ("east", "west"):
        if t.z < -3.25:                                          # la orilla de la cara (quijada y sien)
            return hex_(CANAS["s2"] if v > 6.25 else PIEL["s"])
        borde = 0.5 + _disparejo(t.z, 1 if c == "east" else 2) if t.z < -2.0 else -1.0
    else:
        borde = -1.0
    return hex_(CANAS["s2"] if v > borde else PIEL["s"])


# ---------------------------------------------------------------------------------------------- el ojo grande
def _lente_perfil():
    x0, x1, y0, y1 = LENTE
    c = CHAFLAN
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c),
            (x0, y0 + c)]


def lente(t):
    """El ojo que brilla, de afuera hacia adentro: contorno cian oscuro (sigue las esquinas cortadas), aro cian con
    un brillo arriba a la izquierda y mas oscuro abajo a la derecha, y una linea clara junto al blanco. Los cantos del
    lente, cian oscuro."""
    if abs(t.n[2]) < 0.9:
        return hex_(CIAN["s"] if t.n[1] > 0.5 or t.n[0] < -0.5 else CIAN["o"])
    x0, x1, y0, y1 = LENTE
    a = math.floor((t.x - x0) * DC)                              # 0..23 de su derecha a su izquierda
    b = math.floor((t.y - y0) * DC)                              # 0..23 de abajo hacia arriba
    n = round((x1 - x0) * DC) - 1
    a = n - a                                                    # 0 a la izquierda de quien lo ve
    d = min(a, n - a, b, n - b)
    dd = min(a + b, (n - a) + b, a + (n - b), (n - a) + (n - b)) - round(CHAFLAN * DC)     # a la esquina cortada
    if d < 2 or dd < 2:
        return hex_(CIAN["o"])
    if d == 4:
        return hex_(CIAN["l"])
    if (a <= 6 and b >= n - 6 and d >= 2) and (a + (n - b)) <= 9:
        return hex_(CIAN["h"] if (a + (n - b)) <= 6 else CIAN["l"])        # brillo arriba a la izquierda
    if a + b >= 2 * n - 9:
        return hex_(CIAN["s"])                                   # abajo a la derecha, mas oscuro
    return hex_(CIAN["b"])


def blanco(t):
    """El cuadro blanco que se abomba, con la pupila cuadrada cian al medio; sus cantos, cian claro."""
    if t.cara != "north":
        return hex_(CIAN["l"])
    n = t.tw - 1
    a, b = t.i, t.th - 1 - t.j
    d = min(a, n - a, b, n - b)
    if d >= 5:
        return hex_(CIAN["b"] if (a, b) == (6, 7) else CIAN["s"])       # pupila (con un puntito de brillo)
    if d == 4:
        return hex_(CIAN["l"])
    return hex_(CIAN["h"] if a + b > 3 else "#FFFFFF")


def ojo_grande(p):
    g = f"{G}/ojo"
    p.malla(g, "lente", geo.extruir(_lente_perfil(), *LENTE_Z), lente, dens=DC)
    x0, x1, y0, y1 = LENTE
    m = 0.625                                                    # el blanco ocupa 14 de los 24 texeles
    p.caja(g, "blanco", (x0 + m, y0 + m, BLANCO_Z), (x1 - m, y1 - m, LENTE_Z[0] + 0.05), blanco, dens=DC,
           luz=False)


# ---------------------------------------------------------------------------------------------- nariz, parpado y cejas
def nariz(t):
    """La nariz de bloque, sombreada a mano: el frente claro con el canto de arriba mas claro y el de abajo en
    sombra, su derecha (de cara a la luz) en base y su izquierda en sombra; abajo, las fosas."""
    c = t.cara
    if c == "north":
        return hex_(PIEL["l"] if t.j == 0 else PIEL["s"] if t.fila_abajo == 0 else PIEL["m"])
    if c == "up":
        return hex_(PIEL["l"])
    if c == "east":
        return hex_(PIEL["b"] if t.fila_abajo > 0 else PIEL["s"])
    if c == "west":
        return hex_(PIEL["s"] if t.fila_abajo > 0 else PIEL["s2"])
    if c == "down":
        fosa = t.nombre == "nariz" and 1 <= t.j <= 3 and t.i in (1, 2, t.tw - 3, t.tw - 2)
        return hex_(PIEL["o"] if fosa else PIEL["s2"])
    return hex_(PIEL["s"])


def parpado(t):
    """El parpado de bloque del ojo chico: piel con la raya gruesa de las pestanas en el canto de abajo."""
    c = t.cara
    if c == "down" or (c == "north" and t.fila_abajo <= 1):
        return hex_("#3A1A1C" if c == "north" else PIEL["s2"])
    if c == "north":
        return hex_(PIEL["s"] if t.j == 0 else PIEL["b"])
    return hex_(PIEL["s"])


def ceja(t):
    """Ceja de bloque gris (sin luz horneada): el frente en medio con el canto de arriba claro y el de abajo en
    sombra, partida en dos bloques por una junta; arriba claro, abajo y los lados en sombra."""
    c = t.cara
    if c == "north":
        if t.i == t.tw // 2 - 3:
            return hex_(CANAS["s"])                              # junta entre bloque y bloque
        return hex_(CANAS["l"] if t.j == 0 else CANAS["s"] if t.fila_abajo == 0 else CANAS["m"])
    if c == "up":
        return hex_(CANAS["l"])
    if c == "down":
        return hex_(CANAS["s2"])
    return hex_(CANAS["s"])


def facciones(p):
    g = f"{G}/cara"
    p.caja(g, "nariz", *NARIZ, nariz, dens=DC, luz=False)
    p.caja(g, "puente", *PUENTE, nariz, dens=DC, luz=False)
    p.caja(g, "parpado", *PARPADO, parpado, dens=DC, luz=False)
    for nombre, (a, b, giro) in (("ceja_der", CEJA_DER), ("ceja_izq", CEJA_IZQ)):
        centro = tuple((a[k] + b[k]) / 2 for k in range(3))
        p.caja(g, nombre, a, b, ceja, rot=(0, 0, giro), piv=centro, dens=DC, luz=False)


# ---------------------------------------------------------------------------------------------- pelo, bigote y barba
def pintor_mechon(tono, k):
    """Mechon de bloque gris sin luz horneada: las caras anchas en su tono, los cantos un paso mas oscuros, arriba
    claro y las puntas (abajo) en sombra; una junta fija le parte el largo en dos bloques."""
    def p(t):
        c = t.cara
        if c == "up":
            return hex_(_t(CANAS, tono + 1))
        if c == "down":
            return hex_(_t(CANAS, tono - 1))
        f, h = t.f, t.t
        grueso = 0 if (h[0] - f[0]) < (h[2] - f[2]) else 2
        ancha = (c in ("east", "west")) == (grueso == 0)
        kk = tono if ancha else tono - 1
        if ancha and t.th > 6 and t.j == int(t.th * (0.3 + 0.4 * azar(k, 5))):
            kk -= 1                                              # la junta
        return hex_(_t(CANAS, kk))
    return p


def mechon(p, nombre, raiz, lado, ancho, largo, grueso=0.5, abre=0.0, abanico=0.0, tono=3, k=0,
           largo2=0.0, dobla=0.0, gira2=0.0, grupo="pelo"):
    """Un mechon de bloque que cuelga desde 'raiz' (el medio de arriba de su cara de adentro, pegada a la cabeza).
    lado: 'e' (su derecha, +X), 'w' (su izquierda), 's' (atras) o 'n' (adelante). abre: cuanto se separa la punta
    de la cabeza (0 cuelga derecho, 90 sale de lado); abanico: giro en su propio plano (adelante/atras en los
    costados, hacia +X en la nuca y la frente). Con largo2 lleva una punta mas angosta que se dobla 'dobla' grados
    mas hacia afuera y 'gira2' mas en su plano."""
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
        p.caja(g, n, desde, hasta, pintor_mechon(tn, k), rot=rot, piv=r, dens=DC, luz=False)
        return rot

    rot = caja(nombre, raiz, ancho, largo, grueso, abre, abanico, tono)
    if largo2:
        junta = geo.girar(([(raiz[0], raiz[1] - largo, raiz[2])], []), rot, raiz)[0][0]
        caja(nombre + "_p", junta, ancho * 0.75, largo2, grueso - 0.0625, abre + dobla, abanico + gira2,
             tono + (1 if azar(k, 9) > 0.5 else 0))


def _jit(k, a):
    """Corrimiento fijo entre -a/2 y a/2 para la pieza k."""
    return a * (azar(k, 77) - 0.5)


# Mechones del pelo, por lado y por capa. Costados ('e' su derecha, 'w' su izquierda): (z, arriba, ancho, largo,
# grueso, abre, abanico, tono, largo2, dobla). Nuca ('s'): lo mismo con x en lugar de z.
CAPA_PEGADA = {          # (z o x, donde terminan las puntas)
    "e": ((-3.5, 30.5), (-2.375, 31.25), (-1.25, 32.0), (-0.125, 31.5), (1.0, 31.0), (2.125, 30.75), (3.25, 30.5)),
    "w": ((-3.5, 30.75), (-2.375, 31.75), (-1.25, 31.25), (-0.125, 32.0), (1.0, 31.25), (2.125, 30.75),
          (3.25, 30.5)),
    "s": ((-3.5, 30.75), (-2.5, 30.0), (-1.5, 30.5), (-0.5, 29.875), (0.5, 30.25), (1.5, 29.875), (2.5, 30.25),
          (3.5, 30.75)),
}
CAPA_MEDIA = {           # desde arriba, se abren poco: le dan el bulto al pelo
    "e": ((-3.25, 37.0, 1.25, 2.5, 0.75, 34, 10, 4, 1.0, -18), (-2.0, 37.1, 1.5, 2.75, 0.75, 44, 4, 4, 0.75, -24),
          (-0.625, 36.95, 1.375, 3.0, 0.75, 30, -4, 3, 1.0, -14), (0.75, 37.05, 1.5, 2.75, 0.75, 40, -8, 4, 0, 0),
          (2.125, 37.0, 1.375, 3.0, 0.75, 28, -12, 3, 1.0, -12), (3.375, 37.1, 1.25, 2.5, 0.75, 34, -20, 3, 0, 0)),
    "w": ((-3.25, 37.0, 1.25, 2.75, 0.75, 22, 8, 3, 0.875, -12), (-1.875, 37.1, 1.5, 2.5, 0.75, 36, 2, 4, 0, 0),
          (-0.5, 36.95, 1.375, 3.0, 0.75, 26, -4, 3, 1.0, -16), (0.875, 37.05, 1.5, 2.5, 0.75, 38, -8, 3, 0, 0),
          (2.25, 37.0, 1.375, 2.75, 0.75, 24, -14, 3, 0.875, -10), (3.375, 37.1, 1.25, 2.5, 0.75, 30, -20, 2, 0, 0)),
    "s": ((-3.25, 37.0, 1.375, 3.0, 0.75, 22, -16, 3, 0.75, -12), (-2.0, 37.1, 1.5, 3.25, 0.75, 14, -8, 2, 0, 0),
          (-0.625, 36.95, 1.5, 3.5, 0.75, 18, 2, 3, 0.875, -10), (0.75, 37.05, 1.5, 3.25, 0.75, 24, 8, 2, 0, 0),
          (2.0, 37.0, 1.375, 3.0, 0.75, 16, 14, 3, 0.875, 12), (3.25, 37.1, 1.375, 2.75, 0.75, 26, 20, 3, 0, 0)),
}
CAPA_AFUERA = {          # mas abajo y encima de la pegada: salen mas de lado, el pelo revuelto como nube
    "e": ((-2.75, 35.5, 1.25, 2.0, 0.75, 62, 14, 5, 0.75, -26), (-1.25, 34.75, 1.125, 2.25, 0.625, 50, 6, 4, 0, 0),
          (0.25, 35.75, 1.25, 2.0, 0.75, 70, -6, 5, 0.75, -30), (1.75, 34.5, 1.125, 2.25, 0.625, 46, -10, 4, 0, 0),
          (3.0, 35.25, 1.25, 1.875, 0.75, 58, -18, 4, 0.625, -20), (-3.25, 33.25, 1.0, 1.75, 0.625, 36, 18, 4, 0, 0),
          (0.75, 32.5, 1.125, 1.75, 0.625, 30, -6, 3, 0, 0), (2.75, 32.25, 1.0, 1.875, 0.625, 24, -14, 3, 0, 0)),
    "w": ((-2.5, 35.25, 1.25, 1.875, 0.75, 52, 10, 4, 0.625, -22), (-0.75, 34.5, 1.125, 2.0, 0.625, 40, 2, 4, 0, 0),
          (1.0, 35.5, 1.25, 1.75, 0.75, 60, -8, 4, 0.625, -24), (2.75, 34.75, 1.125, 2.0, 0.625, 44, -16, 3, 0, 0),
          (-2.25, 33.0, 1.0, 1.75, 0.625, 30, 12, 3, 0, 0), (1.75, 32.5, 1.125, 1.875, 0.625, 26, -10, 3, 0, 0)),
    "s": ((-3.0, 34.75, 1.25, 2.25, 0.75, 40, -18, 4, 0.75, -16), (-1.0, 34.25, 1.125, 2.5, 0.625, 30, -6, 3, 0, 0),
          (1.0, 35.0, 1.25, 2.25, 0.75, 44, 10, 4, 0.75, -18), (3.0, 34.5, 1.125, 2.25, 0.625, 34, 18, 3, 0, 0),
          (-2.0, 32.25, 1.0, 2.0, 0.625, 18, -10, 3, 0, 0), (2.0, 32.0, 1.0, 2.25, 0.625, 14, 12, 3, 0, 0)),
}
COPETES = {              # bajo el ala, cortos y anchos, casi de lado: (z, largo, abre)
    "e": ((-2.5, 2.0, 84), (-0.75, 1.625, 80), (1.25, 2.125, 86), (2.875, 1.75, 78)),
    "w": ((-2.0, 1.75, 82), (0.25, 1.5, 78), (2.25, 1.875, 84)),
    "s": ((-2.25, 1.625, 76), (0.0, 1.875, 80), (2.25, 1.5, 74)),
}
FRENTE = ((3.75, 1.0, 2.75, 0.5, 12, 4), (2.875, 0.875, 1.25, 0.625, 30, 5), (-1.125, 1.0, 1.0, 0.375, -8, 4),
          (-3.75, 1.0, 3.25, 0.5, -10, 3), (-2.75, 0.75, 0.875, 0.625, -26, 4))     # (x, ancho, largo, grueso, abanico, tono)


def _raiz(lado, w, y, fuera):
    """Punto de arriba de un mechon: w es z en los costados y x en la nuca; fuera, a cuanto de la cabeza."""
    if lado == "s":
        return (w, y, 4.0 + fuera)
    return ((4.0 + fuera) * (1 if lado == "e" else -1), y, w)


def pelo(p):
    """El pelo gris revuelto en capas de mechones de bloque (sin luz: sin sombras adentro), como una nube de bloques
    que sale por debajo del ala: una capa pegada a los costados y a la nuca, colgando derecho con las puntas
    disparejas; la capa del medio, de mechones anchos que bajan abriendose (le dan el bulto); la de afuera, mas abajo,
    con mechones que salen mas de lado; copetes casi horizontales justo bajo el ala; y adelante los mechones que caen
    sobre las esquinas de la frente y entre las cejas. Su derecha va mas loca y un tono mas clara (de ahi viene la
    luz); lo de mas adentro, mas oscuro."""
    y0 = TOPE_PELO
    k = 0
    for lado, filas in CAPA_PEGADA.items():
        for n, (w, fin) in enumerate(filas):
            gr = 0.5 if n % 2 else 0.625
            ancho = 1.125 if lado == "s" else 1.25
            mechon(p, f"pegado_{lado}{n}", _raiz(lado, w, y0, 0.0), lado, ancho, y0 - fin - _jit(k, 0.375),
                   grueso=gr, tono=3 if lado == "e" else 2, k=k)
            k += 1
    for s, lado in ((1, "e"), (-1, "w")):                        # las esquinas de atras, mas gruesas
        mechon(p, f"esquina_{lado}", (s * 4.0, y0, 4.0), lado, 1.25, y0 - 30.5 - _jit(k, 0.5), grueso=0.75,
               tono=2, k=k)
        k += 1
        mechon(p, f"esquina_{lado}_afuera", (s * 4.75, 36.0, 4.0), lado, 1.25, 2.25, grueso=0.75, abre=40,
               abanico=-30, tono=3, k=k)
        k += 1
    for capa, filas_lado, fuera in (("medio", CAPA_MEDIA, 0.625), ("afuera", CAPA_AFUERA, 0.625)):
        for lado, filas in filas_lado.items():
            for n, (w, y, an, la, gr, ab, abn, tn, la2, db) in enumerate(filas):
                mechon(p, f"{capa}_{lado}{n}", _raiz(lado, w, y, fuera if capa == "medio" else 0.75), lado, an, la,
                       grueso=gr, abre=ab + _jit(k, 8), abanico=abn, tono=tn, k=k, largo2=la2, dobla=db)
                k += 1
    for lado, filas in COPETES.items():
        for n, (w, la, ab) in enumerate(filas):
            mechon(p, f"copete_{lado}{n}", _raiz(lado, w, 36.75, 0.75), lado, 1.5, la, grueso=0.75, abre=ab,
                   tono=4 if lado != "s" else 3, k=k)
            k += 1
    for n, (x, an, la, gr, abn, tn) in enumerate(FRENTE):
        mechon(p, f"frente{n}", (x, y0, -4.0), "n", an, la, grueso=gr, abre=4, abanico=abn, tono=tn, k=k)
        k += 1


BARBA = ((-1.375, 1.0, 1.0, 0.5, -10, 3), (-0.25, 1.25, 1.375, 0.625, 4, 4), (1.0, 1.0, 0.875, 0.5, 12, 3))
# (x, ancho, largo, grueso, abanico, tono)


def bigote_y_barba(p):
    """Bigote caido: dos mechones de bloque que cuelgan de las comisuras y se abren, con la punta mas derecha (el
    de su derecha mas largo). Barba de chivo corta: una tira pegada bajo la boca con tres mechones disparejos que
    pasan el menton, y en las esquinas de la quijada mechones que la juntan con el pelo de los costados."""
    mechon(p, "bigote_der", (2.375, 31.875, -4.0), "n", 1.125, 1.5, grueso=0.625, abre=10, abanico=24, tono=4,
           k=200, largo2=1.375, gira2=-14, dobla=-4, grupo="bigote")
    mechon(p, "bigote_izq", (-2.75, 32.0, -4.0), "n", 1.0, 1.25, grueso=0.625, abre=10, abanico=-26, tono=4,
           k=201, largo2=1.0, gira2=12, dobla=-4, grupo="bigote")
    g = f"{G}/barba"
    p.caja(g, "base", (-1.875, 29.875, -4.375), (1.625, 30.5, -4.0), pintor_mechon(3, 202), dens=DC, luz=False)
    k = 210
    for n, (x, an, la, gr, abn, tn) in enumerate(BARBA):
        mechon(p, f"barba{n}", (x, 30.5, -4.375), "n", an, la, grueso=gr, abre=6, abanico=abn, tono=tn, k=k,
               grupo="barba")
        k += 1
    for s, lado in ((1, "e"), (-1, "w")):
        mechon(p, f"quijada_{lado}", (s * 4.0, 31.5, -3.25), lado, 1.5, 1.75, grueso=0.75, abre=12, abanico=10,
               tono=3, k=k, grupo="barba")
        k += 1


# ---------------------------------------------------------------------------------------------- armado
def cabeza(p):
    p.caja(f"{G}/cabeza", "cabeza", *CABEZA_CAJA, piel_cabeza, dens=DC, luz=False)
    ojo_grande(p)
    facciones(p)
    pelo(p)
    bigote_y_barba(p)
