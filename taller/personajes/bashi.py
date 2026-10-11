"""
Bashi, el sabio excentrico (avatar). Hecho a mano segun referencias/personajes/bashi_hoja.png, sin el cuerpo de
Steve: un sabio brillante y medio loco que se viste con lo primero que encuentra y carga sus experimentos encima.

Lo que se lee en la hoja:
  Silueta: unas 5 cabezas de alto mas un SOMBRERO de bruja enorme (casi dos cabezas de alto, el ala casi tres de
    ancho), chueco, con la punta doblada hacia un lado y cascabeles dorados colgando del ala y de la punta. Abrigo
    largo que se abre hacia abajo y termina en TIRAS disparejas a la altura de la rodilla; botas grandes y distintas.
    Nada es simetrico.
  Cabeza: piel blanca durazno, OJO DERECHO enorme cian que brilla (cuadro cian, blanco adentro y pupila cian), ceja gris
    levantada encima; el izquierdo entrecerrado, con el iris vino; SONRISA chueca abierta con los dientes de arriba;
    nariz de bloque que sale; pelo gris revuelto en mechones de bloque que salen por debajo del ala; bigote y barba
    gris en mechones que cuelgan.
  Sombrero: parches de morado, vino, olivo y mostaza en ladrillos; cinta con bloques; cristales celestes y cian que
    salen junto a la cinta; cascabeles dorados con una gotita morada abajo.
  Ropa: abrigo de parches (morado, olivo, vino, beige) en capas, bufanda olivo, camisa beige adentro con un pano
    que cuelga adelante; dos cinturones de cuero con hebillas de oro (uno cruzado del hombro derecho a la cadera
    izquierda y otro en la cintura); bolsas de cuero, una bolsa morada que brilla, frascos cian colgados y un
    MORRAL grande atras con broche dorado. Manga derecha beige enrollada y esponjada sobre una olivo; la izquierda
    con punos beige y brazalete de cuero y oro. Pantalon morado; la pierna izquierda vendada en beige; botas de
    cuero con suela oscura, una con la puntera beige y un mono morado.
  Magia: en la mano derecha un FRASCO violeta-azul que brilla, con un aro dorado que lo rodea y cubitos morados;
    junto a la mano izquierda flota un ARTEFACTO dorado en rombo con el centro cian que brilla; alrededor flotan
    runas (cubos con espiral morada o cian) y piedritas.

Se arma por partes, cada una en su modulo (asi se pueden trabajar por separado):
  bashi_cabeza.cabeza(p)              cabeza, cara, nariz, cejas, pelo, bigote y barba
  bashi_sombrero.sombrero(p)          el sombrero con cinta, cristales y cascabeles
  bashi_abrigo.abrigo(p)              el torso: abrigo, ruedo en tiras, bufanda, camisa, cinturones, bolsas y morral
  bashi_extremidades.extremidades(p)  brazos (mangas, brazaletes, manos) y piernas (pantalon, vendas, botas)
  bashi_magia.magia(p)                frasco con aro, artefacto dorado y runas que flotan
construir(partes) arma solo esas partes y pone un maniqui liso en lugar de la cabeza, el torso o las extremidades
que falten (sirve para probar una parte sola).
"""

import importlib
import importlib.util
import math

from ..kit import Personaje, tonos
from ..textura import hex_a_rgba as hex_

# ---------------------------------------------------------------------------------------------- medidas
D = 4                                   # texeles por px: ropa, sombrero, botas, objetos
DC = 8                                  # en la cabeza (la cara)
PX = 1.0 / D

ALTURA, CABEZA = 38, 8
TORSO = (8, 12, 4.5)                    # ancho, alto, hondo del torso (sin el abrigo)
BRAZO = (3, 3)
PIERNA = (3.6, 3.6)
L = ALTURA - CABEZA - TORSO[1]          # 18: alto de las piernas (cintura)
C = L + TORSO[1]                        # 30: cuello
T = C + CABEZA                          # 38: arriba de la cabeza (el sombrero va encima)

CABEZA_CAJA = ((-4.0, C, -4.0), (4.0, T, 4.0))
TORSO_CAJA = ((-4.0, L, -2.25), (4.0, C, 2.25))
BRAZO_X = (4.0, 7.0)                    # del hombro hacia afuera (lado derecho; el izquierdo es el espejo)
BRAZO_Z = 1.5                           # medio hondo del brazo
MANO_Y = (16.5, 19.0)                   # la mano, de la muneca para abajo (sin girar)
BRAZO_ABRE = 6.0                        # grados: los brazos cuelgan un poco abiertos, por fuera del abrigo
PIERNA_X = (0.2, 3.8)                   # cada pierna (derecha; la izquierda es el espejo)
PIERNA_Z = 1.8
BOTA_ALTO = 5.0                         # las botas, de y = 0 a 5; mas anchas y largas que la pierna
RUEDO_Y = 8.5                           # hasta donde baja el abrigo (las tiras mas largas)


def giro_brazo(s):
    """El giro de TODAS las piezas de un brazo (s = 1 derecho, -1 izquierdo): se abre BRAZO_ABRE desde el hombro.
    Las piezas se dibujan rectas (sin girar) y se les pasa esto: p.caja(..., **giro_brazo(s))."""
    return dict(rot=(0, 0, s * BRAZO_ABRE), piv=(s * BRAZO_X[0], C - 0.5, 0))


def girar_brazo(punto, s):
    """Donde queda un punto dibujado recto en el brazo s despues de abrirlo (para saber donde cae la mano)."""
    from .. import malla as geo
    g = giro_brazo(s)
    return geo.girar(([punto], []), g["rot"], g["piv"])[0][0]


def centro_mano(s):
    """Centro de la mano s, ya girada (en el mundo)."""
    return girar_brazo((s * sum(BRAZO_X) / 2, sum(MANO_Y) / 2, 0.0), s)


# ---------------------------------------------------------------------------------------------- paleta
def _rampa(hexa):
    """tonos() del kit mas 'm', el medio entre base y luz (los saltos base-luz son grandes para ladrillos)."""
    r = tonos(hexa)
    b, l = hex_(r["b"]), hex_(r["l"])
    r["m"] = "#%02X%02X%02X" % tuple((x + y) // 2 for x, y in zip(b[:3], l[:3]))
    return r


# colores de la paleta de referencias/personajes/bashi_hoja2.png
MORADO = _rampa("#4F2F51")
OSCURO = _rampa("#2E2A36")              # gris azulado oscuro: parches, suelas, lo de mas adentro
OLIVO = _rampa("#636442")
VINO = _rampa("#442934")                # vino oscuro del sombrero y el abrigo
BEIGE = _rampa("#B29A84")
ORO = _rampa("#C08F51")
MOSTAZA = _rampa("#9A8048")             # entre el olivo y el oro (bloques de la cinta)
CUERO = _rampa("#6E4A33")
CUERO_OSC = _rampa("#4A3226")
PIEL = _rampa("#DDAE8E")                # durazno claro: blanco pero no tanto
CANAS = _rampa("#B5ADA8")               # pelo, cejas, bigote y barba
CRISTAL = _rampa("#80C0B8")
SUELA = OSCURO
PIEDRA = _rampa("#8A8078")
MADERA = _rampa("#7A5536")              # la pata de palo

# lo que brilla (va con luz=False: no le cae sombra)
CIAN = {"o": "#16465A", "s": "#3B91AF", "b": "#59B9C2", "l": "#8FD8CF", "h": "#E6FFFB"}
VIOLETA = {"o": "#3A2560", "s": "#6A4AA0", "b": "#926DC7", "l": "#B898E6", "h": "#E8DCFF"}
AZUL_FRASCO = {"s": "#4A3C8C", "b": "#6A5CC0", "l": "#9A8CE6"}

PARCHES_SOMBRERO = (MORADO, OLIVO, MORADO, VINO, OLIVO, MORADO, OSCURO)
PARCHES_ABRIGO = (MORADO, MORADO, OLIVO, VINO, OSCURO, OLIVO, BEIGE)


# ---------------------------------------------------------------------------------------------- texturas
def _azar(k):
    """Numero fijo entre 0 y 1 para k (siempre el mismo: el modelo no cambia de un armado a otro)."""
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def azar(*ks):
    """_azar de varios enteros juntos (para celdas, ladrillos, piezas)."""
    k = 0
    for i, v in enumerate(ks):
        k = k * 131 + int(v) * (7 + 11 * i)
    return _azar(k)


def ejes(t):
    """(u, v) de un texel en su cara: u a lo ancho y v a lo alto (en las tapas, x y z). Sirve en cubos y mallas."""
    n = t.n
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if ay >= ax and ay >= az:
        return t.x, t.z
    if ax >= az:
        return t.z, t.y
    return t.x, t.y


def ladrillos(paletas, w=1.0, h=0.5, celda=(3, 4), semilla=0, junta="s"):
    """Pintor de parches de ladrillos, como la hoja: la cara se parte en ladrillos de w x h (cada fila corrida medio
    ladrillo) con una junta de 1 px; cada ladrillo toma un tono de su rampa (casi todos base, algunos sombra o medio)
    y los ladrillos se juntan en parches de celda = (ladrillos de ancho, filas de alto), cada parche de una de las
    'paletas'. Patron fijo (nada de ruido por pixel)."""
    def p(t):
        u, v = ejes(t)
        fila = math.floor(v / h)
        corre = 0.5 * w if fila % 2 else 0.0
        col = math.floor((u + corre) / w)
        cf = math.floor(fila / celda[1])
        cc = math.floor((col + 7 * cf) / celda[0])
        rampa = paletas[int(azar(cc, cf, semilla) * len(paletas)) % len(paletas)]
        if junta and ((v - fila * h) < PX * 0.999 or ((u + corre) - col * w) < PX * 0.999):
            return hex_(rampa[junta])
        r = azar(col, fila, semilla + 17)
        return hex_(rampa["s"] if r < 0.18 else rampa["m"] if r > 0.82 else rampa["b"])
    return p


def liso(hexa):
    c = hex_(hexa)
    return lambda t: c


def tiras(rampa, ancho=0.5, semilla=0):
    """Tela en tiras verticales de 'ancho' (para el ruedo, la bufanda o vendas de canto): cada tira un tono fijo y
    una junta de 1 px entre tira y tira."""
    def p(t):
        u, v = ejes(t)
        k = math.floor(u / ancho)
        if (u - k * ancho) < PX * 0.999:
            return hex_(rampa["s"])
        r = azar(k, semilla)
        return hex_(rampa["s"] if r < 0.2 else rampa["m"] if r > 0.8 else rampa["b"])
    return p


# ---------------------------------------------------------------------------------------------- armado
PARTES = ("cabeza", "sombrero", "abrigo", "extremidades", "magia")


def maniqui(p, parte):
    """Bloques lisos en lugar de una parte que todavia no se arma (para probar las otras en su lugar)."""
    gris = liso("#8A8A8A")
    if parte == "cabeza":
        p.caja("Head/maniqui", "cabeza", *CABEZA_CAJA, liso(PIEL["b"]), dens=1, luz=False)
    elif parte == "abrigo":
        p.caja("Body/maniqui", "torso", *TORSO_CAJA, gris, dens=1, luz=False)
    elif parte == "extremidades":
        for s in (1, -1):
            hb, hp = ("RightArm", "RightLeg") if s > 0 else ("LeftArm", "LeftLeg")
            x1, x2 = sorted((s * BRAZO_X[0], s * BRAZO_X[1]))
            p.caja(f"{hb}/maniqui", "brazo", (x1, MANO_Y[0], -BRAZO_Z), (x2, C, BRAZO_Z), gris, dens=1, luz=False,
                   **giro_brazo(s))
            x1, x2 = sorted((s * PIERNA_X[0], s * PIERNA_X[1]))
            p.caja(f"{hp}/maniqui", "pierna", (x1, 0, -PIERNA_Z), (x2, L, PIERNA_Z), gris, dens=1, luz=False)


CUELLO_ALTO = 1.5                       # la cabeza y el sombrero suben esto: se ve el cuello de la bata y la bufanda


class _Bajado:
    """Un texel visto dy mas abajo: asi una pieza que se subio se sigue pintando con su pintor de antes."""
    __slots__ = ("_tx", "_dy")

    def __init__(self, tx, dy):
        self._tx, self._dy = tx, dy

    def __getattr__(self, k):
        v = getattr(self._tx, k)
        if k == "y":
            return v - self._dy
        if k in ("f", "t"):
            return (v[0], v[1] - self._dy, v[2])
        return v


def _bajar(pintor, dy):
    return (lambda t: pintor(_Bajado(t, dy))) if pintor else pintor


def subir_cabeza(p, dy):
    """Sube todas las piezas de la cabeza (cara, pelo, sombrero...) dy, con sus pivotes; cada una se sigue pintando
    igual (su pintor la ve donde estaba)."""
    m = p.m
    for c in m.cubos:
        if c.hueso.split("/")[0] == "Head":
            c.desde[1] += dy
            c.hasta[1] += dy
            c.origen[1] += dy
            c.pintor = _bajar(c.pintor, dy)
    for ma in m.mallas:
        if ma.hueso.split("/")[0] == "Head":
            ma.vertices = [(x, y + dy, z) for x, y, z in ma.vertices]
            ma.grupos = [(_bajar(pin, dy), poli) for pin, poli in ma.grupos]
    for k, v in list(m.pivotes.items()):
        if k.split("/")[0] == "Head":
            m.pivotes[k] = (v[0], v[1] + dy, v[2])


def construir(partes=PARTES):
    p = Personaje("bashi", altura=ALTURA, cabeza=CABEZA, torso=TORSO, brazo=BRAZO, pierna=PIERNA)
    # luz horneada en el sombrero, el pelo, la barba y la ropa; la cara va sombreada a mano (luz=False)
    for parte in PARTES:
        if parte in partes and importlib.util.find_spec(f"{__package__}.bashi_{parte}"):
            modulo = importlib.import_module(f"{__package__}.bashi_{parte}")
            getattr(modulo, parte)(p)
        elif parte not in partes:
            maniqui(p, parte)                # una parte que se pidio pero no existe todavia (la magia) no se pone
    subir_cabeza(p, CUELLO_ALTO)
    return p
