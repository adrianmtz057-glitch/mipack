"""
Khaset demonio: el ultimo rey humano de Thza, hoy dios del fuego corrompido. Hecho a mano con el kit segun
referencias/personajes/khaset_demonio.png (los rasgos, no la pose sentada) y lo que pidio el usuario: enorme, flaco,
inhumano, PARADO, con una pose natural y una silueta que no se lea humana. Es la silueta ACECHO con lo mejor de las
otras dos propuestas: la calavera esculpida y los pies de carbon de TORCIDO; el abanico, las manos enormes, la piel
y la brasa entre las costillas de ESPIGADO.

Silueta (de perfil es una zeta de huesos; un player mide 32 px):
  COLUMNA arqueada: la pelvis atras, el torso se vence hacia adelante y arriba hace joroba; la cintura hundida y
    las COSTILLAS en relieve, con la brasa de adentro asomando entre los surcos; vertebras en punta por la espalda
  HOMBROS altos y huesudos: clavicula, perilla del hombro y dos OMOPLATOS en espina (de punta negra) que suben por
    encima del abanico: de frente y de espaldas son dos cuernos que rompen el contorno
  CUELLO largo de buitre: sale adelante del pecho, se tuerce a su izquierda y entra a media nuca, debajo del yelmo;
    la CABEZA, chica para el cuerpo, cuelga adelante, mas baja que los hombros y descolgada a su izquierda, ladeada
    y mirando a ese lado (de frente la pose no es un espejo y se ven el pecho y el pectoral al lado de la calavera)
  BRAZOS larguisimos y arqueados (codo afuera y atras) con MANOS ENORMES de carbon que cuelgan por fuera de las
    rodillas y pasan debajo de ellas; como al caminar, el derecho adelante y el izquierdo atras
  PATAS DIGITIGRADAS con las rodillas abiertas y una pua en la rotula: muslo adelante, canilla atras hasta el garron
    alto (con un espolon grande) y un pie largo de carbon con tres dedos de garra. La izquierda adelante
Cabeza: CALAVERA esculpida color hueso rosado, mas clara que el cuerpo (placa con las cuencas huecas y los ojos de
  fuego al fondo, ceja en V, pomulos salientes, maxilar y mandibula mas angostos que el craneo, occipital achaflanado,
  y en reposo una mueca de dientes apretados: morder y rugir abren Head/mandibula);
  encima el YELMO DE JAGUAR (ceno en V, ojos rasgados, hocico arrugado, colmillos largos, solapas con orejeras) con
  dos CUERNOS negros al rojo, y detras el ABANICO de plumas turquesa de punta aguzada verde oscuro y filete naranja,
  con una fila de plumas negras con venas de brasa adelante; cada pluma lleva un raquis, asi tiene cuerpo de canto.
Adornos: PECTORAL de oro y mosaico turquesa (adelante un ala ancha con colgantes, atras un yugo pegado a la espalda,
  con un canto de cuentas), brazaletes, cinturon de oro con taparrabo negro de greca turquesa (pano adelante, pano
  atras y dos faldones a los costados), VENDAS crema en las palmas, munecas, rodillas y tobillos con tiras largas
  que cuelgan quebradas en dos tramos.
Pintura: piel carmesi de bloques (voxel de revolthir) cruzada por una red de VENAS que sigue de pieza a pieza; los
  antebrazos y las canillas se queman (con la matriz de Bayer) hasta el CARBON de manos y pies, que tiene grietas de
  brasa; garras negras con el filo de brasa. Nada al azar: el volumen lo termina la luz horneada, salvo en los ojos
  (que brillan), los dientes y las plumas, que ya vienen pintados con su sombra y asi el render ronda los 25 s.
Medidas: ~60 px de alto con los omoplatos (59.6; el abanico llega a 57.4), hombros a 49, la calavera cuelga de 37 a 45
  a la izquierda del eje (escala 0.85 de la de acecho), caderas a 31.5 y los dedos de los pies en y = 0.
Rig para animar en Figura (la pose va en la geometria):
  Head pivota en la nuca, donde el craneo se une al cuello (el cuello va en Body: al girar, la calavera no orbita ni
    se mete en el pecho). Head/mandibula pivota en la bisagra (giro_mandibula() da los angulos para abrirla derecha),
    Head/calavera/ojos son los ojos que brillan, Head/plumas pivota en el roseton y cada pluma (Head/plumas/p<fila>_<k>)
    tambien, para abrir y cerrar el abanico.
  Brazos desde el hombro: <brazo>/antebrazo en el codo, <brazo>/antebrazo/mano en la muneca y
    <brazo>/antebrazo/mano/dedos en los nudillos (abre y cierra la garra; el pulgar va con la mano).
  Piernas desde la cadera: <pierna>/canilla en la rodilla, <pierna>/canilla/pie en el garron (el tobillo) y
    <pierna>/canilla/pie/dedos en la planta (quedan apoyados cuando el garron se levanta).
  Body/taparrabo pivota en el cinturon y cada pano (pano_frente, pano_atras, faldon_der, faldon_izq) en su borde.
  script_figura() es el Lua del avatar: compensa el agachado y el golpe vanilla, hace brillar los ojos y cuida el
    abanico al mover la cabeza (puente.py lo escribe en el script.lua del avatar, debajo de ocultar el vanilla).
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..luz import L as LUZ_U, rot_matriz    # LUZ_U: de donde viene la luz (el filo de las garras)
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER, color, tubo, voxel

D = 3                                   # texeles por px en el cuerpo
DC = 4                                  # en la cabeza
DP = 3                                  # en las plumas

PIEL = tonos("#981C36")                 # carmesi magenta
CARBON = tonos("#2B1D20")               # manos y pies quemados
HUESO = tonos("#E6DAC0")                # dientes y colmillos
CARA = tonos("#C4405A")                 # la calavera: rosa hueso, mas clara que el cuerpo
ORO = tonos("#D6A13A")
JAGUAR = tonos("#E0782A")               # yelmo
TURQUESA = tonos("#22AA9C")             # plumas, mosaico, orejeras
PLUMA_NEGRA = tonos("#2A161E")          # la fila de plumas de adelante
NEGRO = tonos("#1C1418")                # cuernos, puntas de las puas, punta de las plumas
VENDA = tonos("#E3D3AE")
TELA = tonos("#33101A")                 # taparrabo negro rojizo
FUEGO = tonos("#F06A1E")                # filete de las plumas, cuentas del pectoral
BRASA, BRASA_VIVA = "#FF8A24", "#FFD25A"    # grietas del carbon, surcos de las costillas, puntas al rojo
OSCURO = "#0E0709"                      # fondo de las cuencas y de la boca
OJO, HALO = "#FFF6C8", "#F06A1E"        # brillo del ojo y su halo (fuego, no dorado: no se confunde con el jaguar)
MANCHA = "#2A1008"                      # rosetas y arrugas del jaguar
FILO, FILO_CUERNO = "#6B2A1E", "#5A2620"   # el brillo de lo negro (garras, puas, cuernos): calido, de brasa
ANCHO_VENA = 0.2                        # que tan gruesas salen las venas (en la suma de ondas)

SIN_ATRAS = ("north", "east", "west", "up", "down")     # cajas de la cara: la de atras queda adentro del craneo

# ---------------------------------------------------------------- anatomia (px; frente = -Z, derecha = +X)

# columna: (x, y, z, semiancho, semifondo) de abajo hacia arriba; se inclina adelante y hace joroba arriba
COLUMNA = ((0.0, 28.3, 3.3, 2.4, 1.9),     # pelvis abajo
           (0.0, 31.5, 3.4, 3.1, 2.35),    # cadera
           (0.0, 35.1, 3.3, 1.85, 1.55),   # cintura hundida
           (0.0, 38.7, 2.9, 3.2, 2.45),    # costillas flotantes
           (0.0, 42.5, 1.7, 3.75, 2.9),    # caja toracica
           (0.0, 46.1, -0.2, 3.55, 2.7),   # pecho
           (0.0, 48.7, -2.4, 2.9, 2.2))    # cintura de los hombros
CUELLO_BASE = (0.0, 47.5, -2.4)         # donde el cuello sale del pecho: pivote de Body
# costillas: (donde van en la columna atras, en puntos del camino; cuanto bajan hacia adelante; angulo atras;
# angulo adelante). Los angulos van desde el costado hacia el frente
COSTILLAS = ((3.0, 0.3, -50, 42), (3.65, 0.33, -60, 66), (4.3, 0.35, -64, 74), (4.95, 0.3, -60, 70))
RADIO_COSTILLA = 0.46
# cuello de buitre: sale adelante del pecho, se dobla hacia abajo y entra al craneo a media nuca (el ultimo punto
# sale de la cabeza: ENTRA_CUELLO)
CUELLO = ((0.0, 47.3, -2.4, 1.6, 1.5), (-0.5, 47.2, -5.0, 1.35, 1.3), (-1.8, 45.4, -7.0, 1.3, 1.3),
          (-2.9, 42.4, -8.3, 1.3, 1.3))
RADIO_CUELLO = 1.3
# pectoral: (donde va en la columna, cuanto se separa a lo ancho y de fondo), del borde de abajo al cuello: un ala
# ancha sobre los hombros que asoma a los costados de la cabeza
PECTORAL = ((5.0, 3.1, 1.9), (5.5, 0.9, 0.6), (6.0, 0.2, 0.2))
COLGANTES = (28, 58, 122, 152)  # angulos de los colgantes sobre el borde del pectoral (90 = adelante)
CINTURON = (32.5, 34.3, 3.35)           # alto de abajo, alto de arriba y centro z del cinturon
Y_PANOS = 33.4                          # de donde cuelgan los panos, pegados al cinturon (pivote de Body/taparrabo)
# panos del taparrabo: (nombre, z donde cuelga, ancho, largo, giro)
PANOS = (("pano_frente", 0.95, 3.4, 10.3, (8, 0, 0)), ("pano_atras", 5.62, 3.8, 9.8, (3, 0, 0)))
GROSOR_PANO, CORTE_PANO = 0.3, 1.4      # grueso de la tela y alto del corte en V de abajo
FALDONES = (3.0, 2.4, 6.0, 1.0, 6)      # a los costados: x, ancho, largo, corte y cuanto se abren (asi de perfil se ve
                                        # tela y no solo el pano de atras de canto)

# brazos: hombro, codo, muneca, hacia donde apunta la mano y cuanto cierra los dedos (grados por falange). Codos
# afuera y atras; como al caminar, el derecho adelante (la pierna izquierda avanza) y el izquierdo cuelga atras
BRAZOS = {1: ((6.2, 49.2, -1.8), (9.4, 36.2, 1.0), (9.3, 25.4, -6.2), (0.2, -1.0, -0.3), 8),
          -1: ((-6.2, 49.2, -1.8), (-9.6, 36.2, 2.4), (-9.4, 23.2, 1.4), (-0.2, -1.0, -0.17), 10)}
# piernas digitigradas: cadera, rodilla, garron (tobillo alto), planta. Las rodillas bien abiertas; la izquierda
# adelante y la derecha atras, con el garron mas alto
PIERNAS = {1: ((2.9, 31.5, 3.2), (6.1, 22.0, -2.0), (5.0, 11.8, 6.2), (4.6, 1.4, 2.0)),
           -1: ((-2.9, 31.5, 3.2), (-6.3, 22.6, -3.6), (-5.2, 11.0, 2.8), (-4.8, 1.4, -2.8))}

# ---------------------------------------------------------------- cabeza (en su sistema: origen en la nuca, a la
# escala de la cabeza de acecho; despues se achica ESCALA_CABEZA y se ladea LADEO)

NUCA = (-3.2, 41.8, -10.0)               # pivote de Head: donde el cuello entra al craneo
ESCALA_CABEZA = 0.85                    # cabeza chica: no tapa el pectoral y el cuerpo se ve mas alto
LADEO = (-8.0, 18.0, 22.0)              # baja la mirada, mira a su izquierda y se ladea
ENTRA_CUELLO = (0.0, -0.9, -1.6)        # el cuello termina adentro del craneo
# craneo: anillos (y, medio ancho, frente, atras, chaflan de las esquinas) de abajo hacia arriba
CRANEO = ((-2.4, 2.3, -4.7, -1.2, 0.7), (-1.0, 2.95, -5.0, 0.2, 0.9), (2.6, 3.0, -5.0, 0.4, 1.0),
          (3.4, 2.4, -4.6, -0.7, 0.9))
PLACA = ((-2.9, -1.6, -5.45), (2.9, 2.4, -5.0))     # la cara, con las cuencas y la nariz huecas
CUENCA = (1.35, 0.95, 1.1, 0.95)        # centro (|x|, y) y semiejes de cada cuenca
NARIZ = (-1.15, 0.1, 0.5)               # abajo, arriba y medio ancho abajo del hueco de la nariz
BISAGRA = (0.0, -1.7, -2.5)             # la mandibula gira desde aca (pivote de Head/mandibula)
ABRE = 0.0                              # en reposo, mueca de dientes apretados (morder y rugir la abren)
CASCO = ((-3.5, 2.3, -5.95), (3.5, 5.9, 0.9))
HOCICO = ((-1.8, 2.4, -7.3), (1.8, 4.3, -5.95))
OJO_JAGUAR = (1.85, 4.85, 20.0)         # centro (|x|, y) de los ojos del jaguar y cuanto suben hacia afuera
ROSETON = (0.0, 6.3, 1.4)               # base del abanico (pivote de Head/plumas), detras y arriba del yelmo
INCLINA = 14.0                          # el abanico se echa para atras...
CONO = (4.0, 16.0)                      # ...y cada pluma un poco mas (la del medio, las de las puntas)
# filas del abanico: (cantidad, de -a a a grados, largo al medio, largo en las puntas, medio ancho, z en el roseton)
FILAS_PLUMAS = ((11, 60, 11.5, 8.6, 1.25, 0.35), (7, 45, 7.0, 5.6, 0.95, -0.2))   # +-60: al mirar arriba no toca
                                                                                   # el cuello ni el hombro
DESDE_PLUMA = 1.0                       # las plumas nacen adentro del roseton
CUERNO = ((2.9, 5.4, -2.9), (4.2, 6.4, -2.3), (5.0, 8.6, -1.3), (4.8, 10.8, -0.2))   # sale del costado del yelmo
RADIO_CUERNO = (0.62, 0.5, 0.32, 0.04)
OREJERA = ((0.75, -2.55), 1.05)         # centro (y, z) y radio del disco de cada orejera, sobre la solapa

# manos (armadas colgando: dedos hacia -Y, la palma mirando a -X, a lo ancho en Z): palma por anillos (y, x, z,
# grueso, ancho) y dedos (z en la palma, largos de las tres falanges, cuanto se abren)
PALMA = ((-2.9, 0, 0, 0.64, 1.8), (0.1, 0, 0, 0.52, 0.95))
NUDILLOS = 2.75                         # de la muneca a los nudillos (pivote de <brazo>/antebrazo/mano/dedos)
VENDA_PALMA = ((-2.0, 0, 0, 0.74, 1.94), (0.35, 0, 0, 0.66, 1.12))
DEDOS = ((-0.95, (2.0, 1.6, 1.4), -10), (-0.32, (2.3, 1.85, 1.6), -3), (0.32, (2.2, 1.75, 1.55), 4),
         (0.95, (1.7, 1.35, 1.25), 11))
RADIOS_DEDO = (0.34, 0.3, 0.25)         # en los nudillos; la tercera falange es la garra
# pulgar: sale del borde de adelante, cerca de la muneca, y baja hacia adelante (puntos con radio y la garra)
PULGAR = ((-0.1, -0.7, -1.0, 0.36, 0.36), (-0.5, -2.2, -2.0, 0.3, 0.3), (-0.95, -3.5, -2.35, 0.25, 0.25))
PUNTA_PULGAR = (-1.5, -4.6, -2.45)
# pie: dedos (angulo hacia afuera, largo) que salen de la planta hacia adelante, y el espolon del garron (hacia
# afuera, arriba y atras: asi se ve tambien de frente)
DEDOS_PIE = ((-32, 3.0), (0, 3.7), (32, 2.9))
ESPOLON = (1.3, 1.6, 2.4)
LADOS_META = 5                          # lados del metatarso (el tubo de revolthir: lados, tapa de arriba, de abajo)


# ---------------------------------------------------------------- vectores

def _mas(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _menos(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _por(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _punto(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_punto(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def _entre(a, b, k):
    return _mas(a, _menos(b, a), k)


def _mul(A, B):
    return tuple(tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _girar(R, v):
    return tuple(_punto(fila, v) for fila in R)


def _desgirar(R, v):
    return tuple(R[0][i] * v[0] + R[1][i] * v[1] + R[2][i] * v[2] for i in range(3))


def angulos(R):
    """Angulos de Blockbench (rx, ry, rz; R = Rz * Ry * Rx) de una matriz de giro."""
    return (math.degrees(math.atan2(R[2][1], R[2][2])), math.degrees(math.asin(max(-1.0, min(1.0, -R[2][0])))),
            math.degrees(math.atan2(R[1][0], R[0][0])))


# ---------------------------------------------------------------- geometria

def ejes(t, ref=None):
    """Dos ejes perpendiculares a la direccion t: e1 lo mas parecido a 'ref' (+X, o +Y si t va casi en X) y
    e2 = t x e1 (con t hacia arriba, e2 es el frente -Z): asi los anillos salen como los pide geo.tronco."""
    if ref is None:
        ref = (1.0, 0.0, 0.0) if abs(t[0]) < 0.8 else (0.0, 1.0, 0.0)
    e1 = _unit(_menos(ref, _por(t, _punto(ref, t))))
    return e1, _cruz(t, e1)


def marcos(camino):
    """Por cada punto (x, y, z, rx, rz) del camino: (centro, direccion, rx, rz)."""
    out = []
    for k, q in enumerate(camino):
        a, b = camino[max(0, k - 1)], camino[min(len(camino) - 1, k + 1)]
        out.append((tuple(q[:3]), _unit(_menos(b[:3], a[:3])), q[3], q[4]))
    return out


def en_marcos(fr, k):
    """Marco interpolado en un indice fraccionario k del camino."""
    i = max(0, min(len(fr) - 2, int(k)))
    s = k - i
    (c0, t0, a0, b0), (c1, t1, a1, b1) = fr[i], fr[i + 1]
    return _entre(c0, c1, s), _unit(_entre(t0, t1, s)), a0 + (a1 - a0) * s, b0 + (b1 - b0) * s


def tubo_camino(camino, lados=6, giro=22.5, tapas=(True, True), ref=None):
    """Tubo que sigue una linea de puntos (x, y, z, rx, rz): un anillo perpendicular a la linea en cada punto. El
    marco de cada anillo se arrastra del anterior, asi el tubo no se retuerce aunque la linea se doble mucho."""
    anillos, e1 = [], ref
    for c, t, rx, rz in marcos(camino):
        e1, e2 = ejes(t, e1)
        anillos.append([_mas(_mas(c, e1, rx * math.cos(a)), e2, rz * math.sin(a))
                        for a in (math.radians(giro + 360.0 * k / lados) for k in range(lados))])
    return geo.loft_puntos(anillos, tapa_abajo=tapas[0], tapa_arriba=tapas[1])


def tramo(p0, p1, r0, r1, lados=5):
    """El tubo de revolthir sin tapas: para tramos que empiezan y terminan adentro de otra pieza, y para las vendas y
    brazaletes que envuelven un miembro (las tapas quedarian adentro del miembro)."""
    vs, cs = tubo(p0, p1, r0, r1, lados)
    return vs, cs[:lados]


def cono(base, punta, rx, rz=None, lados=4, giro=45.0):
    """Punta facetada desde el centro de la base hasta la punta: garras, puas, espolones, colmillos. Sin tapa: la base
    siempre queda metida en otra pieza."""
    e1, e2 = ejes(_unit(_menos(punta, base)))
    rz = rz or rx
    anillo = [_mas(_mas(base, e1, rx * math.cos(a)), e2, rz * math.sin(a))
              for a in (math.radians(giro + 360.0 * k / lados) for k in range(lados))]
    return geo.piramide(anillo, punta, tapa=False)


def perilla(c, r, lados=5):
    """Nudo de hueso en una articulacion: tapa la junta de dos tramos."""
    return geo.bipiramide(c, r, r * 0.85, r * 0.85, lados=lados, giro=30)


def octogono(y, ancho, frente, atras, chaflan):
    """Anillo de 8 puntos a la altura y: un rectangulo (medio ancho, z de adelante y de atras) con las esquinas
    cortadas, antihorario visto desde arriba como pide geo.tronco."""
    w, c = ancho, chaflan
    return [(w, y, atras - c), (w, y, frente + c), (w - c, y, frente), (c - w, y, frente),
            (-w, y, frente + c), (-w, y, atras - c), (c - w, y, atras), (w - c, y, atras)]


def orientar(malla, d):
    """Gira una malla armada colgando (hacia -Y) para que apunte en la direccion d (Rodrigues)."""
    bx, by, bz = _unit(d)
    seno, coseno = math.sqrt(bz * bz + bx * bx), -by
    if seno < 1e-9:
        return malla
    kx, kz = -bz / seno, bx / seno                            # eje: (0, -1, 0) x d
    vs, cs = malla

    def girar(v):
        x, y, z = v
        kv = kx * x + kz * z
        return (x * coseno - kz * y * seno + kx * kv * (1 - coseno), y * coseno + (kz * x - kx * z) * seno,
                z * coseno + kx * y * seno + kz * kv * (1 - coseno))
    return [girar(v) for v in vs], cs


class Juntar:
    """Varias mallas en una sola, cada una con su pintor: una malla por mano y por pie (asi la luz se arma una vez)."""

    def __init__(self):
        self.partes, self.pintores = [], []

    def poner(self, malla, pintor):
        self.partes.append(malla)
        self.pintores += [pintor] * len(malla[1])

    def malla(self):
        return geo.unir(*self.partes)


class Marco:
    """Sistema propio de la cabeza: se modela derecha (origen en la nuca, frente -Z, a la escala de acecho), se achica
    'escala' y se gira 'rot' alrededor de 'piv'. Los pintores reciben las coordenadas propias."""

    def __init__(self, piv, rot, escala):
        self.piv, self.k, self.R = piv, escala, rot_matriz(*rot)

    def mundo(self, q):
        return _mas(self.piv, _girar(self.R, _por(q, self.k)))

    def malla(self, m):
        vs, cs = m
        return [self.mundo(v) for v in vs], cs

    def pintor_malla(self, pintor):
        """Para una malla ya puesta en el mundo: el pintor recibe la posicion y la normal propias."""
        def p(t):
            x, y, z, n = t.x, t.y, t.z, t.n
            t.x, t.y, t.z = _por(_desgirar(self.R, _menos((x, y, z), self.piv)), 1 / self.k)
            t.n = _desgirar(self.R, n)
            c = pintor(t)
            t.x, t.y, t.z, t.n = x, y, z, n
            return c
        return p

    def caja(self, p, grupo, nombre, desde, hasta, pintor, giro=None, eje=(0.0, 0.0, 0.0), dens=DC, luz=True,
             caras=None):
        """Caja en el sistema propio; 'giro' (una matriz) la gira ademas alrededor de 'eje'. El pintor recibe las
        coordenadas propias de la caja sin girar. 'caras': solo esas (las que quedan adentro de otra pieza, no)."""
        R = self.R if giro is None else _mul(self.R, giro)
        Q, k = self.mundo(eje), self.k
        f = tuple(min(a, b) for a, b in zip(desde, hasta))
        h = tuple(max(a, b) for a, b in zip(desde, hasta))

        def pin(t):
            x, y, z, tf, tt = t.x, t.y, t.z, t.f, t.t
            t.x, t.y, t.z = _mas(eje, _menos((x, y, z), Q), 1 / k)
            t.f, t.t = f, h
            c = pintor(t)
            t.x, t.y, t.z, t.f, t.t = x, y, z, tf, tt
            return c
        p.caja(grupo, nombre, _mas(Q, _menos(f, eje), k), _mas(Q, _menos(h, eje), k), pin, rot=angulos(R), piv=Q,
               dens=dens, luz=luz, caras=caras)


# ---------------------------------------------------------------- pintores: piel, carbon, adornos

def vena(x, y, z):
    """Red de venas: la curva de nivel cero de una suma de ondas (sigue de una pieza a otra, siempre igual)."""
    f = (math.sin(0.95 * x + 0.45 * y + 0.2 * z) + math.sin(0.8 * z - 0.55 * y + 1.7)
         + 0.7 * math.sin(0.9 * y - 0.6 * x + 0.4 * z + 0.8))
    return abs(f) < ANCHO_VENA


def piel(claro=0.0, alto=None):
    """Piel carmesi de bloques con las venas oscuras encima."""
    base = voxel(PIEL, claro, alto)
    oscura = hex_(PIEL["s2"])

    def p(t):
        if t.cara != "down" and vena(t.x, t.y, t.z):
            return oscura
        return base(t)
    return p


PIEL_TEX = piel()
HUESOS = piel(claro=0.2)                 # lo que sale en relieve: vertebras, nudos, clavicula
COSTILLA_TEX = piel(claro=0.36)          # las costillas, mas claras: se leen contra los surcos
ORO_TEX = voxel(ORO, claro=0.12)
TURQ_TEX = voxel(TURQUESA)
CARBON_TEX = voxel(CARBON, 0.1)
TIRA_TEX = voxel(VENDA, claro=0.1)
TELA_TEX = voxel(TELA, claro=0.15)


def grieta(x, y, z):
    """Grietas de brasa en el carbon: dos ondas que se cruzan (a escala 0.6 y anchas: lineas, no puntos sueltos)."""
    x, y, z = x * 0.6, y * 0.6, z * 0.6
    a = math.sin(x * 2.3 + math.sin(y * 1.9 + z) * 1.6 + z * 1.7)
    b = math.sin(y * 2.1 - x * 1.2 + math.sin(z * 2.2) * 1.3)
    return abs(a) < 0.18 or abs(b) < 0.13


def carbon(t):
    """Carbon con grietas de brasa."""
    if grieta(t.x, t.y, t.z):
        return hex_(BRASA_VIVA if abs(math.sin(t.x * 3.1 + t.y * 2.7)) < 0.25 else BRASA)   # a trechos, casi amarilla
    return CARBON_TEX(t)


def quemado(p0, p1, desde, banda):
    """Piel que se va quemando de p0 a p1: carmesi, una banda tramada (Bayer) y carbon con grietas."""
    eje = _menos(p1, p0)
    largo2 = _punto(eje, eje)

    def p(t):
        u = (_punto(_menos((t.x, t.y, t.z), p0), eje) / largo2 - desde) / banda
        if u <= 0:
            return PIEL_TEX(t)
        if u >= 1:
            return carbon(t)
        b = (BAYER[int(t.y * D) % 4][int((t.x + t.z) * D) % 4] + 0.5) / 16
        return carbon(t) if u > b else PIEL_TEX(t)
    return p


def garra(t):
    """Garra negra con el filo de brasa: las caras que miran a la luz."""
    return hex_(FILO if _punto(t.n, LUZ_U) > 0.25 else NEGRO["o"])


def dedo_pie(base, punta):
    """Dedo del pie de una pieza: carbon con grietas y, en el ultimo tercio, la garra."""
    eje = _menos(punta, base)
    largo2 = _punto(eje, eje)

    def p(t):
        return garra(t) if _punto(_menos((t.x, t.y, t.z), base), eje) / largo2 > 0.66 else carbon(t)
    return p


def pua(base, punta):
    """Pua de hueso (omoplatos, rotulas, espolones): piel en la base que se oscurece hasta la punta negra."""
    eje = _menos(punta, base)
    largo2 = _punto(eje, eje)

    def p(t):
        k = _punto(_menos((t.x, t.y, t.z), base), eje) / largo2
        if k > 0.6:
            return hex_(FILO if _punto(t.n, LUZ_U) > 0.3 else NEGRO["b"])
        if k > 0.4:
            return hex_(PIEL["s2"] if k > 0.5 else PIEL["s"])
        return HUESOS(t)
    return p


def sobre_eje(p0, p1):
    """Coordenadas de un texel respecto de un hueso de p0 a p1: (largo desde p0 en px, vuelta de 0 a 1)."""
    t = _unit(_menos(p1, p0))
    e1, e2 = ejes(t)

    def f(q):
        d = _menos(q, p0)
        return _punto(d, t), (math.atan2(_punto(d, e2), _punto(d, e1)) / (2 * math.pi)) % 1.0
    return f


def venda(p0, p1):
    """Venda crema enrollada en espiral alrededor del hueso p0 -> p1: canto oscuro y canto claro en cada vuelta."""
    eje = sobre_eje(p0, p1)
    s, b, l = hex_(VENDA["s"]), hex_(VENDA["b"]), hex_(VENDA["l"])

    def p(t):
        largo, vuelta = eje((t.x, t.y, t.z))
        k = (largo * 0.8 + vuelta) % 1.0                # una vuelta cada 1.25 px: varios texeles por canto
        return s if k < 0.26 else l if k > 0.8 else b
    return p


def venda_plana(p0, p1):
    """Venda de la palma (una cara ancha y chata): vueltas rectas a lo largo de p0 -> p1, sin la espiral que en una
    cara plana sale como un damero."""
    eje = sobre_eje(p0, p1)
    s, b, l = hex_(VENDA["s"]), hex_(VENDA["b"]), hex_(VENDA["l"])

    def p(t):
        k = (eje((t.x, t.y, t.z))[0] * 0.6) % 1.0
        return s if k < 0.3 else l if k > 0.75 else b
    return p


def brazalete(p0, p1):
    """Brazalete de oro con una fila de piedras turquesa al medio."""
    eje = sobre_eje(p0, p1)
    largo_total = math.dist(p0, p1)

    def p(t):
        largo, vuelta = eje((t.x, t.y, t.z))
        if abs(largo / largo_total - 0.5) < 0.22 and (vuelta * 8) % 1.0 < 0.55:
            return TURQ_TEX(t)
        return ORO_TEX(t)
    return p


def tira_entera(t):
    """Tramo de arriba de una tira de venda: bordes mas oscuros y un doblez de vez en cuando."""
    c = (t.x - t.f[0]) / max(1e-6, t.t[0] - t.f[0])
    if t.cara in ("north", "south") and (c < 0.18 or c > 0.82 or (t.y * 1.3) % 1.0 < 0.12):
        return hex_(VENDA["s"])
    return TIRA_TEX(t)


def tira(t):
    """Tramo de abajo de una tira de venda: como el de arriba y con la punta deshilachada."""
    c = (t.x - t.f[0]) / max(1e-6, t.t[0] - t.f[0])
    if t.cara in ("north", "south") and t.y - t.f[1] < (0.35, 0.0, 0.55, 0.15, 0.4)[min(4, int(c * 5))]:
        return TRANSPARENTE
    return tira_entera(t)


def poner_tira(p, grupo, nombre, arriba, largo, giro=(0, 0, 0), ancho=0.75):
    """Tira de tela colgando desde 'arriba' (su borde de arriba, metido adentro de la venda), un poco movida por
    'giro'. Va en dos tramos: el de abajo, mas angosto, se quiebra en la bisagra y se abre mas (no cuelga rigida como
    un palito)."""
    x, y, z = arriba
    l1 = largo * 0.55
    p.caja(grupo, nombre, (x - ancho / 2, y - l1 - 0.05, z - 0.1), (x + ancho / 2, y, z + 0.1), tira_entera, rot=giro,
           piv=arriba, dens=D)
    j = _mas(arriba, _girar(rot_matriz(*giro), (0.0, -l1, 0.0)))
    a2 = ancho * 0.85
    giro2 = (giro[0] + math.copysign(12, giro[0] or 1), giro[1], giro[2] * 2.2)
    p.caja(grupo, nombre + "_punta", (j[0] - a2 / 2, j[1] - (largo - l1), j[2] - 0.1),
           (j[0] + a2 / 2, j[1], j[2] + 0.1), tira, rot=giro2, piv=j, dens=D)


# ---------------------------------------------------------------- pintores: torso

FR_COLUMNA = marcos(COLUMNA)


def sobre_columna(q):
    """Donde cae un punto respecto de la columna: (k, angulo), con k el indice fraccionario del camino y el angulo en
    grados desde el costado (en espejo) hacia el frente."""
    mejor = None
    for i in range(len(FR_COLUMNA) - 1):
        a, b = FR_COLUMNA[i][0], FR_COLUMNA[i + 1][0]
        ab = _menos(b, a)
        s = max(0.0, min(1.0, _punto(_menos(q, a), ab) / _punto(ab, ab)))
        d = math.dist(q, _mas(a, ab, s))
        if mejor is None or d < mejor[0]:
            mejor = (d, i + s)
    c, t, _, _ = en_marcos(FR_COLUMNA, mejor[1])
    e1, e2 = ejes(t)
    d = _menos(q, c)
    return mejor[1], math.degrees(math.atan2(_punto(d, e2), abs(_punto(d, e1))))


def costilla_en(i, angulo):
    """Donde pasa la costilla i (indice del camino) a ese angulo, o None si no llega hasta ahi."""
    kb, caida, a0, a1 = COSTILLAS[i]
    f = (angulo - a0) / (a1 - a0)
    return kb - caida * f if 0.0 <= f <= 1.0 else None


PIEL_TORSO = piel(alto=(COLUMNA[0][1], COLUMNA[-1][1]))


def torso(t):
    """Torso: piel con venas y, en los surcos entre costilla y costilla, la brasa de adentro (mas viva adelante)."""
    if t.cara != "down":
        k, angulo = sobre_columna((t.x, t.y, t.z))
        if angulo > -30:
            for i in range(len(COSTILLAS) - 1):
                k0, k1 = costilla_en(i, angulo), costilla_en(i + 1, angulo)
                if k0 is not None and k1 is not None and k0 < k < k1:
                    g = abs((k - k0) / (k1 - k0) - 0.5)
                    # la brasa asoma del costado al frente, mas ancha adelante, y se corta a trechos
                    ancho = 0.15 * min(1.0, max(0.0, angulo + 10) / 45)
                    if g < ancho and math.sin(angulo * 0.13 + i * 2.1) > -0.55:
                        return hex_(BRASA_VIVA if angulo > 35 and g < ancho * 0.45 else BRASA)
                    return hex_(PIEL["o"] if g < 0.32 else PIEL["s2"])
    return PIEL_TORSO(t)


def pectoral(c0, t, rx, rz, adentro):
    """Pectoral: banda de oro junto al cuello, mosaico turquesa, otra banda de oro y cuentas de brasa en el borde.
    Las bandas van por la distancia al eje (c0, t), medida contra el borde de afuera (rx, rz): 'adentro' es donde
    empieza el cuello (en esa misma medida) y 1 el borde."""
    e1, e2 = ejes(t)

    def p(q):
        d = _menos((q.x, q.y, q.z), c0)
        a, b = _punto(d, e1), _punto(d, e2)
        f = (math.hypot(a / rx, b / rz) - adentro) / (1 - adentro)
        ang = (math.atan2(b, a) / (2 * math.pi)) % 1.0
        if f < 0.2:
            return ORO_TEX(q)
        if f < 0.72:
            i, j = ang * 16, (f - 0.2) / 0.26
            if i % 1.0 < 0.17 or j % 1.0 < 0.2:
                return hex_(ORO["s"])                   # junta de oro del mosaico
            return hex_(TURQUESA["b"] if (math.floor(i) + math.floor(j)) % 2 else TURQUESA["l"])
        if f < 0.84:
            return ORO_TEX(q)
        k = (ang * 26) % 1.0
        if k < 0.15:
            return hex_(ORO["s"])
        return hex_(FUEGO["b"] if math.floor(ang * 26) % 2 else ORO["l"])
    return p


def cuentas(c0, e1, e2):
    """Canto del pectoral: cuentas de brasa y de oro alternadas alrededor del eje (c0; e1 al costado, e2 adelante)."""
    def p(t):
        d = _menos((t.x, t.y, t.z), c0)
        ang = (math.atan2(_punto(d, e2), _punto(d, e1)) / (2 * math.pi)) % 1.0
        return hex_(FUEGO["b"] if math.floor(ang * 26) % 2 else ORO["l"])
    return p


def cinturon(y0, y1, cz):
    """Cinturon de oro: cantos oscuros y placas turquesa alrededor."""
    def p(t):
        if t.cara in ("up", "down"):
            return ORO_TEX(t)
        if t.y < y0 + 0.25 or t.y > y1 - 0.25:
            return hex_(ORO["s"])
        ang = (math.atan2(t.z - cz, t.x) / (2 * math.pi)) % 1.0
        if abs(t.y - (y0 + y1) / 2) < 0.45 and (ang * 14) % 1.0 < 0.5:
            return TURQ_TEX(t)
        return ORO_TEX(t)
    return p


def taparrabo(arriba, giro, ancho, sol=True):
    """Pano negro que cuelga de 'arriba' girado 'giro': ribete de oro, una banda de rombos turquesa, un sol de brasa
    arriba (si 'sol') y los cantos de tela."""
    R = rot_matriz(*giro)

    def p(t):
        x, y, _ = _desgirar(R, _menos((t.x, t.y, t.z), arriba))
        if abs(_desgirar(R, t.n)[2]) < 0.6:
            return hex_(TELA["s"])                      # el canto
        a = -y
        if abs(x) > ancho / 2 - 0.35 or a < 0.35:
            return ORO_TEX(t)
        if 2.3 < a < 2.6 or 3.6 < a < 3.9:
            return ORO_TEX(t)
        if 2.6 <= a <= 3.6 and abs((x + 20) % 1.33 - 0.665) + abs(a - 3.1) < 0.5:
            return TURQ_TEX(t)
        r = math.hypot(x, a - 1.3)
        if sol and r < 0.42:
            return hex_(FUEGO["b"])
        if sol and 0.62 < r < 0.98:
            return ORO_TEX(t)
        return TELA_TEX(t)
    return p


def perfil_pano(ancho, largo, corte):
    """Silueta de un pano colgando de (0, 0): recto y abajo con un corte en V que lo parte en dos colas."""
    m = ancho / 2
    return [(-m, 0.0), (-m, -largo), (0.0, -largo + corte), (m, -largo), (m, 0.0)]


# ---------------------------------------------------------------- pintores: cabeza

def en_cuenca(x, y):
    """< 1 adentro de la cuenca. El borde de arriba baja hacia adentro: mirada de furia."""
    cx, cy, a, b = CUENCA
    du = (abs(x) - cx) / a
    dv = (y - cy - 0.3 * (abs(x) - cx)) / b
    return du * du + dv * dv


def en_nariz(x, y):
    """Si (x, y) cae en el hueco de la nariz: un triangulo angosto arriba y ancho abajo."""
    abajo, arriba, ancho = NARIZ
    return abajo <= y <= arriba and abs(x) <= ancho * (arriba - y) / (arriba - abajo)


CARA_TEX = voxel(CARA, 0.1)
CRANEO_TEX = piel(claro=0.05)


def placa(t):
    """Placa de la cara: las cuencas y la nariz huecas (por ahi se ve el fondo oscuro y el ojo), el bisel oscuro de
    las cuencas y de la nariz y las raices de los dientes de arriba."""
    x, y = t.x, t.y
    c = en_cuenca(x, y)
    if t.cara in ("north", "south") and (c <= 1.0 or en_nariz(x, y)):
        return TRANSPARENTE
    if t.cara == "north":
        if c < 1.55:
            return hex_(PIEL["s2"])                     # bisel de la cuenca
        if en_nariz(x * 0.8, y - 0.12):
            return hex_(PIEL["s"])                      # borde de la nariz
        if y < -1.25 and (abs(x) + 0.34) % 0.68 < 0.12:
            return hex_(PIEL["s2"])                     # raices de los dientes
    return CARA_TEX(t)


def craneo(t):
    """Craneo (malla en el sistema de la cabeza): adelante el fondo de las cuencas, casi negro; a los costados la sien
    hundida; el resto, piel con venas."""
    if t.n[2] < -0.8:
        return hex_(OSCURO)
    if abs(t.n[0]) > 0.8 and -3.8 < t.z < -1.6 and 0.4 < t.y < 2.3:
        return hex_(PIEL["s"])
    return CRANEO_TEX(t)


def hueso_cara(t):
    """Pomulos, ceja, maxilar y mandibula: piel mas clara arriba y el canto de abajo oscuro."""
    if t.cara == "down":
        return hex_(PIEL["s2"])
    if t.cara == "up":
        return hex_(CARA["l"])
    if t.y - t.f[1] < 0.18:
        return hex_(CARA["s"])
    return CARA_TEX(t)


def mandibula(t):
    """Mandibula: por dentro (arriba) la boca oscura; adelante la barbilla con un hoyo."""
    if t.cara == "up":
        return hex_(OSCURO if t.z < -2.6 else PIEL["o"])
    if t.cara == "north" and abs(t.x) < 0.35 and t.y - t.f[1] < 0.45:
        return hex_(PIEL["s"])
    return hueso_cara(t)


def mejilla(t):
    """Mejilla hundida: piel oscura con el borde de adelante mas oscuro todavia."""
    return hex_(PIEL["o"] if t.z < -4.4 else PIEL["s2"] if t.cara == "down" else PIEL["s"])


def diente(t):
    """Diente de hueso: la raiz mas oscura, la punta clara."""
    if t.cara in ("up", "down"):
        return hex_(HUESO["b"])
    r = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    return hex_(HUESO["s"] if r > 0.72 else HUESO["l"] if r < 0.3 else HUESO["b"])


def diente_abajo(t):
    """Diente de abajo: al reves que los de arriba, la raiz abajo."""
    r = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    if t.cara in ("up", "down"):
        return hex_(HUESO["b"])
    return hex_(HUESO["s"] if r < 0.28 else HUESO["l"] if r > 0.7 else HUESO["b"])


def colmillo(t):
    """Colmillo de jaguar (malla): hueso, con luz en lo que mira adelante y arriba."""
    return hex_(HUESO["l"] if _punto(t.n, LUZ_U) > 0.2 else HUESO["s"])


def roseta(u, v):
    """Manchas de jaguar: anillos rotos en una grilla corrida (siempre las mismas)."""
    fila = math.floor(v / 1.9)
    w = u + (fila % 2) * 1.1
    col = math.floor(w / 2.2)
    cu, cv = w - col * 2.2 - 1.1, v - fila * 1.9 - 0.95
    d = math.hypot(cu, cv * 1.15)
    if d < 0.26:
        return hex_(JAGUAR["s"])
    if 0.42 < d < 0.72 and (cu > 0) * 2 + (cv > 0) != (fila + col) % 4:     # cada anillo con un hueco distinto
        return hex_(MANCHA)
    return None


PELAJE = voxel(JAGUAR, claro=0.05)


def pelaje(t):
    """Pelaje de jaguar con rosetas en los costados, arriba y atras."""
    if t.cara == "down":
        return hex_(JAGUAR["s2"])
    if t.cara == "up":
        c = roseta(t.x, t.z)
    elif t.cara in ("east", "west"):
        c = roseta(t.z, t.y)
    else:
        c = roseta(t.x, t.y) if t.cara == "south" else None
    return c or PELAJE(t)


def ojo_jaguar(x, y):
    """Ojo rasgado del jaguar en el frente del yelmo: 0 afuera, 1 el aro crema, 2 lo negro, 3 la pupila de brasa."""
    cx, cy, sube = OJO_JAGUAR
    s, c = math.sin(math.radians(sube)), math.cos(math.radians(sube))
    dx, dy = abs(x) - cx, y - cy
    a, b = dx * c + dy * s, -dx * s + dy * c
    if abs(a) > 0.95:
        return 0
    alto = 0.34 * (1 - (a / 0.95) ** 2)
    if abs(b) < alto and abs(a + 0.05) < 0.13:
        return 3
    if abs(b) < alto:
        return 2
    return 1 if abs(b) < alto + 0.14 else 0


def casco(t):
    """Yelmo de jaguar: banda de oro abajo con teselas turquesa; adelante los ojos rasgados; el resto, pelaje."""
    y0 = CASCO[0][1]
    if t.cara not in ("up", "down") and t.y < y0 + 0.7:
        u = t.x if t.cara in ("north", "south") else t.z
        if abs(t.y - (y0 + 0.35)) < 0.2 and (u * 1.25) % 1.0 < 0.45:
            return TURQ_TEX(t)
        return ORO_TEX(t)
    if t.cara == "north":
        o = ojo_jaguar(t.x, t.y)
        if o:
            return hex_((HUESO["l"], NEGRO["o"], BRASA_VIVA)[o - 1])
        return PELAJE(t)
    return pelaje(t)


def ceno(t):
    """Cresta del ceno del jaguar: pelaje arriba y la sombra del ceno fruncido abajo y adelante."""
    if t.cara == "down" or (t.cara == "north" and t.y - t.f[1] < 0.22):
        return hex_(MANCHA)
    return PELAJE(t)


def hocico(t):
    """Hocico del jaguar: el labio de arriba oscuro, el surco al medio y las arrugas del gruñido arriba y a los
    costados (sin bigotes)."""
    y0, z0 = HOCICO[0][1], HOCICO[0][2]
    if t.cara == "down":
        return hex_(MANCHA)
    if t.cara == "north":
        if t.y - y0 < 0.3 or (abs(t.x) < 0.09 and t.y - y0 < 1.5):
            return hex_(MANCHA)                         # labio y surco
        if abs(t.y - y0 - 0.95 - 0.35 * abs(t.x)) < 0.08 and abs(t.x) > 0.5:
            return hex_(JAGUAR["s2"])                   # pliegue del labio
    if t.cara == "up":
        d = t.z - z0                                    # desde la punta del hocico
        for z1 in (0.55, 0.85, 1.1):
            if abs(d - z1 - 0.18 * abs(t.x)) < 0.07 and abs(t.x) < 1.3:
                return hex_(MANCHA)                     # arrugas sobre la nariz
    if t.cara in ("east", "west"):
        if abs(t.y - y0 - 0.5 - 0.45 * (t.z - z0)) < 0.08:
            return hex_(MANCHA)                         # arruga del costado
    return PELAJE(t)


def oreja(t):
    """Oreja de jaguar (piramide): pelaje con el adentro oscuro."""
    if t.n[2] < -0.4:
        return hex_(MANCHA if t.y < 7.0 else JAGUAR["s"])
    return PELAJE(t)


def solapa(t):
    """Solapa del yelmo sobre la sien: pelaje con el borde de abajo de oro."""
    if t.cara not in ("up", "down") and t.y - t.f[1] < 0.45:
        return ORO_TEX(t)
    return pelaje(t)


def orejera(t):
    """Orejera: disco de oro con la piedra turquesa al medio, en una caja con lo de afuera del disco vacio."""
    (y, z), r = OREJERA
    d = math.hypot(t.y - y, t.z - z)
    if t.cara in ("east", "west"):
        if d > r:
            return TRANSPARENTE
        if d < 0.6:
            return hex_(ORO["l"]) if d < 0.18 else TURQ_TEX(t)
        return hex_(ORO["s"]) if d > r - 0.15 or 0.6 < d < 0.72 else ORO_TEX(t)
    # el canto: solo donde lo toca el disco
    if (t.cara in ("north", "south") and abs(t.y - y) > 0.4) or (t.cara in ("up", "down") and abs(t.z - z) > 0.4):
        return TRANSPARENTE
    return hex_(ORO["s"])


def cuerno(base, punta):
    """Cuerno negro con anillos de crecimiento; desde poco mas de la mitad esta al rojo, cada vez mas encendido."""
    alcance = math.dist(base, punta)

    def p(t):
        k = math.dist((t.x, t.y, t.z), base) / alcance
        if k > 0.6:
            return hex_(BRASA_VIVA if k > 0.9 else BRASA if k > 0.78 else FUEGO["b"] if k > 0.68 else FUEGO["s2"])
        if (k * 9.0) % 1.0 < 0.18:
            return hex_(NEGRO["o"])
        return hex_(FILO_CUERNO if t.n[1] > 0.5 else NEGRO["b"])
    return p


def medio_ancho_pluma(k, ancho):
    """Medio ancho de la pluma a la fraccion k de su largo: angosta en el canon, ancha arriba y con punta."""
    contorno = ((0.0, 0.22), (0.3, 0.75), (0.62, 1.0), (0.86, 0.55), (1.0, 0.0))
    for (k0, a0), (k1, a1) in zip(contorno, contorno[1:]):
        if k0 <= k <= k1:
            return ancho * (a0 + (a1 - a0) * (k - k0) / (k1 - k0))
    return 0.0


def pluma(y0, largo, ancho, rampa, filete, punta):
    """Pluma recortada en un plano (coordenadas propias: x de costado, y a lo largo desde y0): canon de oro, cuerpo de
    la rampa con el raquis claro y las barbas oscuras en diagonal, un filete y la punta (dos tonos: cuerpo, extremo)."""
    def p(t):
        u, v = t.x, t.y - y0
        k = v / largo
        if abs(u) > medio_ancho_pluma(k, ancho):
            return TRANSPARENTE
        if k < 0.14:
            return hex_(ORO["l"] if abs(u) < 0.15 else ORO["b"])
        if k > 0.84:
            return hex_(punta[0] if k < 0.95 else punta[1])
        if k > 0.78:
            return hex_(filete["b"])
        if abs(u) < 0.12:
            return hex_(FUEGO["o"] if rampa is PLUMA_NEGRA else rampa["h"])     # en la negra, vena de brasa
        if (abs(u) * 1.8 - v * 0.9) % 1.0 < 0.22:
            return hex_(rampa["s"])
        return hex_(rampa["b"] if abs(u) < 0.6 else rampa["s2"])
    return p


def raquis(rampa):
    """Raquis de la pluma: oro en el canon y despues el tono mas claro de la pluma (en la negra, brasa: rayos rojos
    de sol en vez de un paraguas lila)."""
    claro = FUEGO["s2"] if rampa is PLUMA_NEGRA else rampa["l"]

    def p(t):
        return ORO_TEX(t) if t.y - t.f[1] < 0.8 else hex_(claro if t.cara != "down" else rampa["s"])
    return p


def roseton(t):
    """Roseton del abanico: oro con un anillo turquesa."""
    d = math.hypot(t.x - ROSETON[0], t.y - ROSETON[1])
    if 0.6 < d < 1.0 and abs(t.n[2]) > 0.7:
        return hex_(TURQUESA["b"])
    return ORO_TEX(t)


# ---------------------------------------------------------------- piezas: cabeza

def poner_cabeza(p, cab):
    # ================================ CALAVERA: craneo achaflanado, placa de la cara con las cuencas huecas
    g, OJOS = "Head/calavera", "Head/calavera/ojos"
    p.malla(g, "craneo", cab.malla(geo.loft_puntos([octogono(*a) for a in CRANEO])), cab.pintor_malla(craneo),
            dens=DC)
    cab.caja(p, g, "placa", PLACA[0], PLACA[1], placa, caras=SIN_ATRAS)
    cx, cy = CUENCA[0], CUENCA[1]
    for s in (1, -1):
        lado = "der" if s > 0 else "izq"
        x0, x1 = sorted((s * 1.95, s * 3.15))
        cab.caja(p, g, f"pomulo_{lado}", (x0, -0.75, -5.8), (x1, 0.15, -3.8), hueso_cara, caras=SIN_ATRAS)
        # ceja en V: cada mitad sube hacia afuera
        cab.caja(p, g, f"ceja_{lado}", (s * 1.55 - 1.45, 1.75, -5.85), (s * 1.55 + 1.45, 2.3, -5.4), hueso_cara,
                 giro=rot_matriz(0, 0, s * 11), eje=(s * 1.55, 2.0, -5.6), caras=SIN_ATRAS)
        # ojos de fuego al fondo de las cuencas, inclinados con la furia; el halo queda detras de la placa y solo se
        # ve por el hueco eliptico (asi la cuenca se ve encendida y no cuadrada). En su subgrupo: brillan en Figura
        furia = dict(giro=rot_matriz(0, 0, s * 16), eje=(s * cx, cy, -5.05))
        cab.caja(p, OJOS, f"ojo_{lado}", (s * cx - 0.55, cy - 0.4, -5.15), (s * cx + 0.55, cy + 0.4, -5.0), color(OJO),
                 luz=False, **furia)
        cab.caja(p, OJOS, f"halo_{lado}", (s * cx - 0.9, cy - 0.66, -5.07), (s * cx + 0.9, cy + 0.66, -5.01),
                 color(HALO), luz=False, **furia)
    cab.caja(p, g, "maxilar", (-2.2, -2.5, -5.6), (2.2, -1.3, -2.6), hueso_cara, caras=SIN_ATRAS)
    cab.caja(p, g, "boca", (-1.8, -4.2, -5.25), (1.8, -2.3, -3.2), color(OSCURO), luz=False)
    for s in (1, -1):                                    # mejillas hundidas: tapan la boca de costado, detras
        lado = "der" if s > 0 else "izq"
        x0, x1 = sorted((s * 1.6, s * 2.0))             # de los dientes
        cab.caja(p, g, f"mejilla_{lado}", (x0, -4.0, -4.7), (x1, -2.3, -2.4), mejilla, caras=SIN_ATRAS)
    for k in range(6):                                   # dientes de arriba, con los colmillos
        x = -2.0 + 0.68 * k
        largo = 1.4 if k in (1, 4) else 1.0
        cab.caja(p, g, f"diente{k}", (x + 0.04, -2.35 - largo, -5.85), (x + 0.6, -2.3, -5.35), diente, luz=False)

    # ================================ MANDIBULA entreabierta (gira desde la bisagra)
    g = "Head/mandibula"
    abre = dict(giro=rot_matriz(ABRE, 0, 0), eje=BISAGRA)
    cab.caja(p, g, "mandibula", (-2.1, -5.6, -5.7), (2.1, -4.4, -2.2), mandibula, **abre)
    for s in (1, -1):                                    # ramas: suben por detras hasta la bisagra
        lado = "der" if s > 0 else "izq"
        x0, x1 = sorted((s * 1.75, s * 2.45))
        cab.caja(p, g, f"rama_{lado}", (x0, -5.0, -3.3), (x1, -1.4, -1.8), hueso_cara, **abre)
    for k in range(5):
        x = -1.66 + 0.68 * k
        arriba = -3.1 if k in (0, 4) else -3.3
        cab.caja(p, g, f"diente_abajo{k}", (x + 0.04, -4.45, -5.65), (x + 0.6, arriba, -5.2), diente_abajo,
                 luz=False, **abre)

    # ================================ YELMO DE JAGUAR
    g = "Head/yelmo"
    cab.caja(p, g, "casco", CASCO[0], CASCO[1], casco)
    cab.caja(p, g, "hocico", HOCICO[0], HOCICO[1], hocico, caras=SIN_ATRAS)
    cab.caja(p, g, "nariz", (-0.75, 3.85, -7.55), (0.75, 4.45, -7.1), color(MANCHA), luz=False)
    yb, hb, hz = CASCO[0][1], HOCICO[0][1], HOCICO[0][2]
    for k, x in enumerate((-0.9, -0.3, 0.3, 0.9)):       # dientitos del jaguar
        cab.caja(p, g, f"incisivo{k}", (x - 0.18, hb - 0.45, hz + 0.15), (x + 0.18, hb + 0.05, hz + 0.5), diente,
                 luz=False)
    for s in (1, -1):
        lado = "der" if s > 0 else "izq"
        ojo = OJO_JAGUAR[0] * s
        # ceno en V: dos crestas sobre los ojos que bajan hacia el medio
        cab.caja(p, g, f"ceno_{lado}", (ojo - 1.15, 5.15, -6.45), (ojo + 1.15, 5.65, -5.85), ceno,
                 giro=rot_matriz(0, 0, s * 22), eje=(ojo, 5.4, -6.15), caras=SIN_ATRAS)
        p.malla(g, f"colmillo_{lado}", cab.malla(cono((s * 3.0, yb + 0.3, -5.95), (s * 2.8, -1.1, -6.15), 0.45)),
                colmillo, dens=DC)
        p.malla(g, f"canino_{lado}", cab.malla(cono((s * 1.45, hb + 0.2, hz + 0.4), (s * 1.35, hb - 1.45, hz + 0.5),
                                                0.3)), colmillo, dens=DC)
        p.malla(g, f"oreja_{lado}", cab.malla(geo.piramide(geo.anillo(s * 2.45, 5.85, -1.4, 0.85, 0.6, 4, 45),
                                                       (s * 3.0, 7.6, -0.9), tapa=False)),
                cab.pintor_malla(oreja), dens=DC)
        x0, x1 = sorted((s * 3.0, s * 3.55))
        cab.caja(p, g, f"solapa_{lado}", (x0, -0.8, -4.3), (x1, yb + 0.2, -0.8), solapa,
                 caras=("north", "south", "down", "east" if s > 0 else "west"))
        x0, x1 = sorted((s * 3.5, s * 3.95))
        (y, z), r = OREJERA
        cab.caja(p, g, f"orejera_{lado}", (x0, y - r, z - r), (x1, y + r, z + r), orejera)
        # cuernos negros al rojo que salen de los costados del yelmo y se abren hacia arriba
        camino = [(s * x, y, z, r, r) for (x, y, z), r in zip(CUERNO, RADIO_CUERNO)]
        base, punta = cab.mundo(camino[0][:3]), cab.mundo(camino[-1][:3])
        p.malla(g, f"cuerno_{lado}", cab.malla(tubo_camino(camino, 4, 45, (False, False))), cuerno(base, punta),
                dens=DC)

    # ================================ ABANICO: roseton, fila larga turquesa y fila corta negra adelante
    g = "Head/plumas"
    cx, cy, cz = ROSETON
    disco = geo.extruir([(cx + 1.5 * math.cos(a), cy + 1.5 * math.sin(a))
                         for a in (2 * math.pi * k / 8 for k in range(8))], cz - 0.5, cz + 0.5)
    p.malla(g, "roseton", cab.malla(geo.girar(disco, (INCLINA, 0, 0), ROSETON)), cab.pintor_malla(roseton), dens=DC)
    colores = ((TURQUESA, FUEGO, (TURQUESA["o"], NEGRO["o"])), (PLUMA_NEGRA, PIEL, (FUEGO["b"], BRASA_VIVA)))
    for fila, ((n, abre, largo_medio, largo_punta, ancho, dz), (rampa, filete, punta)) in enumerate(
            zip(FILAS_PLUMAS, colores)):
        for k in range(n):
            a = -abre + 2 * abre * k / (n - 1)
            largo = (largo_medio - (largo_medio - largo_punta) * (abs(a) / abre) ** 1.5) * (1.0, 0.92)[k % 2]
            cono_a = CONO[0] + (CONO[1] - CONO[0]) * abs(a) / abre
            giro = _mul(rot_matriz(INCLINA, 0, 0), _mul(rot_matriz(0, 0, -a), rot_matriz(cono_a, 0, 0)))
            eje = (cx, cy, cz + dz + 0.06 * (k % 2))
            y0 = cy + DESDE_PLUMA
            gp = f"{g}/p{fila}_{k}"                      # cada pluma se abre o se cierra por su lado
            p.m.pivotes[gp] = cab.mundo(eje)
            cab.caja(p, gp, f"pluma{fila}_{k}", (cx - ancho, y0, eje[2]), (cx + ancho, y0 + largo, eje[2]),
                     pluma(y0, largo, ancho, rampa, filete, punta), giro=giro, eje=eje, dens=DP,
                     luz=False)
            cab.caja(p, gp, f"raquis{fila}_{k}", (cx - 0.13, y0, eje[2] - 0.13), (cx + 0.13, y0 + largo * 0.8,
                                                                                  eje[2] + 0.13),
                     raquis(rampa), giro=giro, eje=eje, dens=DP, luz=False)


# ---------------------------------------------------------------- piezas: brazos y piernas

def mano(s, muneca, direccion, cierra):
    """Mano enorme de carbon: palma larga, cuatro dedos de tres falanges (la ultima es la garra) y el pulgar. Se arma
    colgando y se orienta hacia 'direccion'. Devuelve ((malla, pintores) de la palma con el pulgar, (malla, pintores)
    de los cuatro dedos, que van aparte para abrir y cerrar la garra, y la venda de la palma)."""
    j, jd = Juntar(), Juntar()
    j.poner(geo.loft(PALMA, 4, 45), carbon)
    for z0, largos, abre in DEDOS:
        giro, sp = 0.0, math.radians(abre)
        pts = [(0.0, -NUDILLOS, z0)]
        for f, largo in enumerate(largos):
            giro += math.radians(cierra * (0.6, 1.0, 1.25)[f])
            pts.append(_mas(pts[-1], (-math.sin(giro) * math.cos(sp), -math.cos(giro) * math.cos(sp), math.sin(sp)),
                            largo))
        jd.poner(tubo_camino([q + (r, r) for q, r in zip(pts, RADIOS_DEDO)], 3, 90, (False, False)), carbon)
        jd.poner(cono(pts[-2], pts[-1], RADIOS_DEDO[-1], lados=3, giro=90), garra)
    j.poner(tubo_camino(PULGAR, 3, 90, (False, False)), carbon)
    j.poner(cono(PULGAR[-1][:3], PUNTA_PULGAR, 0.25, lados=3, giro=90), garra)
    out = []
    for m in (j.malla(), jd.malla(), geo.loft(VENDA_PALMA, 4, 45, tapa_abajo=False, tapa_arriba=False)):
        if s < 0:
            m = geo.espejo_x(m)
        out.append(geo.mover(orientar(m, direccion), muneca))
    return (out[0], j.pintores), (out[1], jd.pintores), out[2]


def brazo(p, s, hombro, codo, muneca, direccion, cierra):
    """Brazo larguisimo: perilla del hombro y brazo con su brazalete; antebrazo que se quema hasta la muneca vendada,
    con dos tiras; la mano enorme de carbon con la palma vendada."""
    h = "RightArm" if s > 0 else "LeftArm"
    ga, gb, gm, gd = h, f"{h}/antebrazo", f"{h}/antebrazo/mano", f"{h}/antebrazo/mano/dedos"
    p.m.pivotes[gb], p.m.pivotes[gm] = codo, muneca
    p.m.pivotes[gd] = _mas(muneca, _unit(direccion), NUDILLOS)
    p.malla(ga, "hombro", perilla(hombro, 1.6, 4), HUESOS, dens=D)
    p.malla(ga, "brazo", tramo(hombro, codo, 1.25, 0.8), PIEL_TEX, dens=D)
    a0, a1 = _entre(hombro, codo, 0.16), _entre(hombro, codo, 0.28)
    p.malla(ga, "brazalete", tramo(a0, a1, 1.42, 1.36), brazalete(a0, a1), dens=D)
    # antebrazo
    p.malla(gb, "codo", perilla(codo, 0.95, 4), HUESOS, dens=D)
    p.malla(gb, "antebrazo", tramo(codo, muneca, 0.95, 0.62), quemado(codo, muneca, 0.5, 0.3), dens=D)
    a0, a1 = _entre(codo, muneca, 0.36), _entre(codo, muneca, 0.48)
    p.malla(gb, "pulsera", tramo(a0, a1, 1.04, 0.98), brazalete(a0, a1), dens=D)
    a0, a1 = _entre(codo, muneca, 0.8), _entre(codo, muneca, 1.04)
    p.malla(gb, "venda_muneca", tramo(a0, a1, 0.86, 0.8), venda(a0, a1), dens=D)
    c = _entre(codo, muneca, 0.9)
    poner_tira(p, gb, "tira0", (c[0] + s * 0.45, c[1], c[2] - 0.2), 4.8, (4, 0, s * 6))
    poner_tira(p, gb, "tira1", (c[0] - s * 0.1, c[1] - 0.2, c[2] + 0.45), 3.4, (-6, 0, -s * 4), ancho=0.62)
    # mano
    (carne, pintores), (dedos, pintores_dedos), palma = mano(s, muneca, direccion, cierra)
    p.malla(gm, "mano", carne, pintores, dens=D)
    p.malla(gd, "dedos", dedos, pintores_dedos, dens=D)
    p.malla(gm, "venda_mano", palma, venda_plana(muneca, _mas(muneca, _unit(direccion), 2.4)), dens=4)


def pie(tobillo, planta, s):
    """Pie de carbon: el garron con su espolon grande (sale hacia atras y afuera, asi se ve tambien de frente), el
    metatarso largo, tres dedos que terminan en garra y una garra chica atras. Devuelve (malla, pintores) del garron con
    el metatarso y (malla, pintores) de los dedos, que van aparte: asi quedan apoyados cuando el garron se levanta."""
    j, jd = Juntar(), Juntar()
    j.poner(perilla(tobillo, 0.85, 4), carbon)
    punta = (tobillo[0] + s * ESPOLON[0], tobillo[1] + ESPOLON[1], tobillo[2] + ESPOLON[2])
    j.poner(cono(tobillo, punta, 0.5), pua(tobillo, punta))
    vs, cs = tubo(tobillo, planta, 0.74, 0.6, LADOS_META)
    j.poner((vs, cs[:LADOS_META + 1]), carbon)          # el metatarso, cerrado abajo (arriba lo tapa el garron)
    for ang, largo in DEDOS_PIE:
        a = math.radians(ang + s * 8)
        f = (s * math.sin(a), 0.0, -math.cos(a))
        punta = (planta[0] + f[0] * (largo + 1.4), 0.0, planta[2] + f[2] * (largo + 1.4))
        jd.poner(cono(_mas(planta, (0.0, -0.3, 0.0)), punta, 0.55, lados=3, giro=90), dedo_pie(planta, punta))
    jd.poner(cono(planta, (planta[0] - s * 0.6, 0.45, planta[2] + 1.7), 0.4, lados=3, giro=90), garra)
    return (j.malla(), j.pintores), (jd.malla(), jd.pintores)


def pierna(p, s, cadera, rodilla, tobillo, planta):
    """Pierna digitigrada: muslo hacia adelante; canilla hacia atras (con la pua de la rotula) que se quema hasta el
    garron; el pie largo de carbon. Vendas en la rodilla y el tobillo, con tiras largas."""
    h = "RightLeg" if s > 0 else "LeftLeg"
    gm, gc, gp, gd = h, f"{h}/canilla", f"{h}/canilla/pie", f"{h}/canilla/pie/dedos"
    p.m.pivotes[gc], p.m.pivotes[gp], p.m.pivotes[gd] = rodilla, tobillo, planta
    p.malla(gm, "cadera", perilla(cadera, 1.45, 4), HUESOS, dens=D)
    p.malla(gm, "muslo", tramo(cadera, rodilla, 1.3, 0.85), PIEL_TEX, dens=D)
    # canilla
    p.malla(gc, "rodilla", perilla(rodilla, 1.15, 4), HUESOS, dens=D)
    base = _mas(rodilla, (0.0, 0.35, -0.4))
    punta = _mas(rodilla, (s * 0.4, 1.5, -2.7))
    p.malla(gc, "rotula", cono(base, punta, 0.62), pua(base, punta), dens=D)
    p.malla(gc, "canilla", tramo(rodilla, tobillo, 1.1, 0.62), quemado(rodilla, tobillo, 0.62, 0.3), dens=D)
    a0, a1 = _entre(rodilla, tobillo, 0.06), _entre(rodilla, tobillo, 0.24)
    p.malla(gc, "venda_rodilla", tramo(a0, a1, 1.42, 1.4), venda(a0, a1), dens=D)
    r = _entre(rodilla, tobillo, 0.18)
    poner_tira(p, gc, "tira_rodilla0", (r[0] + s * 0.5, r[1] + 0.5, r[2] - 1.0), 6.8, (6, 0, s * 4))
    poner_tira(p, gc, "tira_rodilla1", (r[0] - s * 0.3, r[1] + 0.3, r[2] - 0.95), 4.8, (3, 0, -s * 3), ancho=0.62)
    # pie
    (malla, pintores), (dedos, pintores_dedos) = pie(tobillo, planta, s)
    p.malla(gp, "pie", malla, pintores, dens=D)
    p.malla(gd, "dedos", dedos, pintores_dedos, dens=D)
    a0, a1 = _entre(tobillo, planta, 0.08), _entre(tobillo, planta, 0.3)
    p.malla(gp, "venda_tobillo", tramo(a0, a1, 0.95, 0.9), venda(a0, a1), dens=D)
    r = _entre(tobillo, planta, 0.2)
    poner_tira(p, gp, "tira_tobillo0", (r[0] + s * 0.6, r[1] + 0.3, r[2] + 0.3), 3.8, (-4, 0, s * 5))
    poner_tira(p, gp, "tira_tobillo1", (r[0] + s * 0.2, r[1], r[2] + 0.65), 2.7, (-8, 0, s * 2), ancho=0.6)


# ---------------------------------------------------------------- construccion

def construir():
    # el marco del player: caderas a 31.5, 18 px de torso hasta los hombros y lo que sube por encima de ellos
    p = Personaje("khaset", altura=56.8, cabeza=7.3, torso=(7.5, 18, 5.8), brazo=(2.5, 2.5), pierna=(3.4, 3.4))
    cab = Marco(NUCA, LADEO, ESCALA_CABEZA)
    p.m.pivotes = {"Head": NUCA, "Body": CUELLO_BASE,
                   "RightArm": BRAZOS[1][0], "LeftArm": BRAZOS[-1][0],
                   "RightLeg": PIERNAS[1][0], "LeftLeg": PIERNAS[-1][0],
                   "Head/mandibula": cab.mundo(BISAGRA), "Head/plumas": cab.mundo(ROSETON)}

    # ================================================================ TORSO encorvado, costillas y vertebras
    fr = FR_COLUMNA
    p.malla("Body/torso", "torso", tubo_camino(COLUMNA, 8), torso, dens=D)
    g = "Body/huesos"
    costillas = []
    for kb, caida, a0, a1 in COSTILLAS:
        pts = []
        for i in range(3):
            f = i / 2
            c, t, rx, rz = en_marcos(fr, kb - caida * f)
            e1, e2 = ejes(t)
            a = math.radians(a0 + (a1 - a0) * f)
            pts.append(_mas(_mas(c, e1, (rx + 0.1) * math.cos(a)), e2, (rz + 0.1) * math.sin(a))
                       + (RADIO_COSTILLA, RADIO_COSTILLA))
        costillas.append(tubo_camino(pts, 3, 90, (False, False), ref=(0.0, 1.0, 0.0)))
    malla = geo.unir(*costillas)
    p.malla(g, "costillas_der", malla, COSTILLA_TEX, dens=D)
    p.malla(g, "costillas_izq", geo.espejo_x(malla), COSTILLA_TEX, dens=D)
    esternon = []
    for k in (3.5, 4.2, 5.0):
        c, t, rx, rz = en_marcos(fr, k)
        esternon.append(_mas(c, ejes(t)[1], rz) + (0.4, 0.3))
    p.malla(g, "esternon", tubo_camino(esternon, 4, 45, (False, True)), HUESOS, dens=D)
    vertebras = []
    for k in range(5):                                   # hasta donde empieza el pectoral
        c, t, rx, rz = en_marcos(fr, 2.0 + k * 0.62)
        atras = _por(ejes(t)[1], -1)
        alto = 0.75 + 0.45 * math.sin(math.pi * k / 6)                        # mas grandes en la joroba
        vertebras.append(cono(_mas(c, atras, rz - 0.3), _mas(_mas(c, atras, rz + alto), t, 0.45), 0.5, 0.42, 3, 90))
    p.malla(g, "vertebras", geo.unir(*vertebras), HUESOS, dens=D)

    # ================================================================ HOMBROS: claviculas y omoplatos en espina
    for s in (1, -1):
        lado = "der" if s > 0 else "izq"
        hombro = BRAZOS[s][0]
        clavicula = tramo((s * 1.0, 47.6, -3.7), _mas(hombro, (-s * 0.6, 0.5, -0.4)), 0.62, 0.55, 4)
        p.malla(g, f"clavicula_{lado}", clavicula, HUESOS, dens=D)
        base, punta = (s * 2.2, 45.7, 0.8), (s * 6.6, 59.6, 3.8)
        p.malla(g, f"omoplato_{lado}", cono(base, punta, 1.5, 0.6, 4, 0), pua(base, punta), dens=D)

    # ================================================================ PECTORAL ancho de oro y turquesa, con colgantes
    g = "Body/pectoral"
    anillos, borde = [], None
    for k, mas_x, mas_z in PECTORAL:
        c, t, rx, rz = en_marcos(fr, k)
        e1, e2 = ejes(t)
        # adelante el ala ancha; atras (sin(a) < 0) se recoge contra la espalda como un yugo
        anillos.append([_mas(_mas(c, e1, (rx + mas_x * ala) * math.cos(a)), e2, (rz + mas_z * ala) * math.sin(a))
                        for a, ala in ((a, 1.0 if math.sin(a) > 0 else 0.15)
                                       for a in (math.radians(22.5 + 45 * i) for i in range(8)))])
        borde = borde or (c, e1, e2, rx + mas_x, rz + mas_z)
    c, t, rx, rz = en_marcos(fr, PECTORAL[-1][0])
    p.malla(g, "pectoral", geo.loft_puntos(anillos, tapa_abajo=False, tapa_arriba=False),
            pectoral(c, t, borde[3], borde[4], (rx + PECTORAL[-1][1]) / borde[3]), dens=D)
    c0, e1, e2, bx, bz = borde
    # el canto del borde: una banda de cuentas que le da grosor (de canto no queda un alambre)
    t0 = en_marcos(fr, PECTORAL[0][0])[1]
    bajo = [_mas(q, t0, -0.45) for q in anillos[0]]
    p.malla(g, "canto_pectoral", geo.loft_puntos([bajo, anillos[0]], False, False), cuentas(c0, e1, e2), dens=D)
    for k, ang in enumerate(COLGANTES):
        a = math.radians(ang)
        q = _mas(_mas(c0, e1, bx * math.cos(a)), e2, bz * math.sin(a))
        largo = 1.1 + 0.5 * (k % 2)
        p.malla(g, f"colgante{k}", geo.bipiramide((q[0], q[1] - 0.3, q[2]), 0.38, 0.5, largo, lados=3, giro=90),
                ORO_TEX if k % 2 else TURQ_TEX, dens=D)

    # ================================================================ CINTURON de oro y TAPARRABO (gira en el cinturon)
    g = "Body/cinturon"
    y0, y1, cz = CINTURON
    p.malla(g, "cinturon", geo.loft([(y0, 0, cz, 3.3, 2.6), (y1, 0, cz, 2.85, 2.25)], 8, 22.5, False, False),
            cinturon(y0, y1, cz), dens=D)
    g = "Body/taparrabo"
    p.m.pivotes[g] = (0.0, Y_PANOS, cz)
    panos = [(nombre, (0.0, Y_PANOS, z), ancho, largo, CORTE_PANO, giro, True)
             for nombre, z, ancho, largo, giro in PANOS]
    panos += [(f"faldon_{'der' if s > 0 else 'izq'}", (s * FALDONES[0], Y_PANOS, cz), *FALDONES[1:4],
               (0, s * 90, s * FALDONES[4]), False) for s in (1, -1)]
    for nombre, arriba, ancho, largo, corte, giro, sol in panos:
        gp = f"{g}/{nombre}"                             # cada pano gira en su borde de arriba
        p.m.pivotes[gp] = arriba
        m = geo.mover(geo.extruir(perfil_pano(ancho, largo, corte), -GROSOR_PANO / 2, GROSOR_PANO / 2), arriba)
        p.malla(gp, nombre, geo.girar(m, giro, arriba), taparrabo(arriba, giro, ancho, sol), dens=D)

    # ================================================================ CUELLO largo que sale adelante y baja (en Body)
    g = "Body/cuello"
    cuello = CUELLO + (cab.mundo(ENTRA_CUELLO) + (RADIO_CUELLO, RADIO_CUELLO),)
    p.malla(g, "cuello", tubo_camino(cuello, 5, 18, (False, True)), PIEL_TEX, dens=D)   # tapa adentro del craneo
    fc = marcos(cuello)
    nudos = []
    for k in (1.5, 2.3):
        c, t, rx, rz = en_marcos(fc, k)
        arriba = ejes(t, (0.0, 1.0, 0.0))[0]
        nudos.append(cono(_mas(c, arriba, rx - 0.3), _mas(_mas(c, arriba, rx + 0.6), t, -0.3), 0.4, 0.32))
    p.malla(g, "nudos", geo.unir(*nudos), HUESOS, dens=D)

    # ================================================================ CABEZA, BRAZOS y PIERNAS
    poner_cabeza(p, cab)
    for s in (1, -1):
        brazo(p, s, *BRAZOS[s])
        pierna(p, s, *PIERNAS[s])
    return p


# ---------------------------------------------------------------- para animar

def giro_mandibula(grados):
    """Angulos de Blockbench (rx, ry, rz) para abrir Head/mandibula 'grados' alrededor de su bisagra real: la cabeza
    va ladeada (LADEO horneado en la geometria), asi que girar solo X la abre torcida y la hace resbalar contra las
    mejillas. Abrir (grados negativos): -20 -> (-18.1, -6.1, 7.2), -30 -> (-27.4, -8.1, 11.5), -40 -> (-36.9, -9.5,
    16.0)."""
    R = rot_matriz(*LADEO)
    return angulos(_mul(R, _mul(rot_matriz(grados, 0, 0), tuple(zip(*R)))))


def script_figura():
    """Lua para el script.lua del avatar de Figura (va debajo de vanilla_model.PLAYER:setVisible(false)). Compensa lo
    que Figura copia del modelo vanilla: al agacharse Body se inclina 0.5 rad desde el pecho y baja 3.2, Head solo baja
    4.2 y las piernas van 4 atras, asi que sin esto el cuello (que cuelga de Body) se sale de la calavera y la pelvis
    del muslo; en el golpe Body gira en Y y la cabeza no. Ademas hace brillar los ojos, deja mirar arriba solo hasta
    donde el abanico no toca el cuello y contragira el abanico. Valores en px y grados de Blockbench, medidos con este
    modelo (el fin del cuello queda en NX, NZ respecto del pivote de Body); si en el juego un eje sale al reves, se le
    invierte el signo."""
    inclina = rot_matriz(-math.degrees(0.5), 0, 0)

    def agachado(q):                                    # donde queda un punto de Body al agacharse
        return _mas(_mas(CUELLO_BASE, _girar(inclina, _menos(q, CUELLO_BASE))), (0.0, -3.2, 0.0))
    fin = Marco(NUCA, LADEO, ESCALA_CABEZA).mundo(ENTRA_CUELLO)
    cabeza = _menos(_menos(agachado(fin), fin), (0.0, -4.2, 0.0))
    cadera = PIERNAS[1][0]
    pierna = _menos(agachado(cadera), _mas(cadera, (0.0, -0.2, 4.0)))
    nx, _, nz = _menos(fin, CUELLO_BASE)
    return LUA_FIGURA.format(nx=nx, nz=nz, cy=cabeza[1], cz=cabeza[2], py=pierna[1], pz=pierna[2])


LUA_FIGURA = """-- Khaset (generado por taller/personajes/khaset.py: script_figura)
local m = models.khaset                         -- el nombre del .bbmodel
m.Head.calavera.ojos:setLight(15, 15)           -- ojos de fuego: encendidos tambien de noche
local NX, NZ = {nx:.2f}, {nz:.2f}                 -- el fin del cuello respecto del pivote de Body
local ARRIBA = 30                               -- grados que puede mirar arriba (el abanico toca el cuello a 35)
local SIGNO_ARRIBA = -1                         -- signo de la rotacion X de la cabeza al mirar arriba (revisar)
local k = 0
function events.tick() k = player:isCrouching() and 1 or 0 end    -- agachado
function events.render(delta)
  -- golpe: Body gira en Y y la calavera tiene que seguir al fin del cuello
  local yb = math.rad(vanilla_model.BODY:getOriginRot().y)
  local c, s = math.cos(yb), math.sin(yb)
  m.Head:setPos(NX * (c - 1) + NZ * s, {cy:.2f} * k, -NX * s + NZ * (c - 1) + {cz:.2f} * k)
  m.RightLeg:setPos(0, {py:.2f} * k, {pz:.2f} * k)
  m.LeftLeg:setPos(0, {py:.2f} * k, {pz:.2f} * k)
  -- mirar arriba hasta ARRIBA grados; el abanico contragira lo que gira la cabeza
  local r = vanilla_model.HEAD:getOriginRot()
  local sobra = math.max(0, r.x * SIGNO_ARRIBA - ARRIBA)
  m.Head:setRot(-sobra * SIGNO_ARRIBA, 0, 0)
  m.Head.plumas:setRot(-(r.x - sobra * SIGNO_ARRIBA), -r.y, 0)
end
"""
