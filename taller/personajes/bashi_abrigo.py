"""
Bashi: la bata (ver bashi.py), segun referencias/personajes/bashi_hoja2.png. Colores lisos por ahora (sin textura).

Volumenes gruesos de BLOQUE: cajas y tubos de seccion rectangular con las esquinas apenas cortadas (nada de
circulos de muchos lados).
  TORSO: la bata morada, cerrada, en bloque, con la solapa que cruza al medio; arriba el CUELLO alto (con el filo
    olivo) y adentro el cuello de piel.
  BRAZOS en capas, como la hoja: la bata es de MANGA CORTA (morada, hueca, hasta medio brazo); abajo asoma la
    CAMISA olivo hasta el codo y debajo la otra CAMISA beige, gruesa y esponjada, hasta la muneca, con un BRAZAL de
    cuero y hebilla dorada en la muneca (en los huesos de los brazos, abiertas como los brazos).
  La tunica termina en la cintura y la FALDA la faja: su faja (morado oscuro) aprieta la tunica y encima va el
    CINTURON de cuero con la hebilla dorada (la faja asoma arriba y abajo: el cinturon va encima). BUFANDA verde en
    rollo alrededor del cuello con dos puntas que cuelgan adelante. MOCHILA de cuero en la espalda, abierta arriba,
    con un pergamino enrollado y una pocion asomando, y la CORREA cruzada (hebilla de oro y tres frascos colgando).
  FALDON: sale de abajo de la faja en TIRAS que se abren un poco hacia afuera, cada una de un largo distinto (al
    azar, fijo) y con la punta escalonada, en dos capas (la de abajo mas oscura tapa los huecos). Algunas olivo.
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import BEIGE, C, CIAN, CUERO, CUERO_OSC, D, MORADO, OLIVO, ORO, OSCURO, PIEL, VIOLETA, azar, giro_brazo
from .meron import tubo_hueco


def plano(rampa):
    """Color liso de la pieza, apenas un tono por lado para que se lea la forma: arriba mas claro, los costados y
    abajo un tono mas oscuro."""
    b, m, s = hex_(rampa["b"]), hex_(rampa.get("m", rampa["l"])), hex_(rampa["s"])

    def p(t):
        n = t.n
        if n[1] > 0.6:
            return m
        if n[1] < -0.6 or abs(n[0]) > max(abs(n[2]), 0.7):
            return s
        return b
    return p


def oscuro(rampa):
    return plano({**rampa, "b": rampa["s"], "m": rampa["s"]})


def caja(p, grupo, nombre, desde, hasta, rampa, **kw):
    p.caja(grupo, nombre, desde, hasta, plano(rampa), dens=D, **kw)


def anillo(cx, y, mx, mz, ch, cz=0.0):
    """Seccion de bloque: rectangulo de medio ancho mx y medio hondo mz con las esquinas cortadas ch (8 puntos,
    antihorario visto desde arriba, de +X hacia -Z)."""
    return [(cx + mx, y, cz + mz - ch), (cx + mx, y, cz - mz + ch), (cx + mx - ch, y, cz - mz), (cx - mx + ch, y, cz - mz),
            (cx - mx, y, cz - mz + ch), (cx - mx, y, cz + mz - ch), (cx - mx + ch, y, cz + mz), (cx + mx - ch, y, cz + mz)]


def bloque(secciones, cx=0.0):
    """Bloque solido de esquinas cortadas a traves de varias secciones (y, mx, mz, ch)."""
    return geo.loft_puntos([anillo(cx, y, mx, mz, ch) for y, mx, mz, ch in secciones])


def aro_grueso(abajo, arriba, grosor):
    """Anillo grueso (pared de afuera, de adentro y tapas). abajo / arriba: (y, mx, mz, ch) de afuera."""
    y0, mx0, mz0, c0 = abajo
    y1, mx1, mz1, c1 = arriba
    afuera = [anillo(0.0, y0, mx0, mz0, c0), anillo(0.0, y1, mx1, mz1, c1)]
    adentro = [anillo(0.0, y0, mx0 - grosor, mz0 - grosor, c0), anillo(0.0, y1, mx1 - grosor, mz1 - grosor, c1)]
    vs, cs = geo.tronco(*afuera, tapa_abajo=False, tapa_arriba=False)
    vi, ci = geo.tronco(*adentro, tapa_abajo=False, tapa_arriba=False)
    vs, cs = geo.unir((vs, cs), (vi, [tuple(reversed(c)) for c in ci]))
    n = 8
    for k in range(n):                                           # tapas entre el anillo de afuera y el de adentro
        k2 = (k + 1) % n
        cs.append((n + k, n + k2, 3 * n + k2, 3 * n + k))
        cs.append((2 * n + k, 2 * n + k2, k2, k))
    return vs, cs


# ---------------------------------------------------------------------------------------------- torso
TORSO = ((-4.45, 21.2, -2.75), (4.45, C - 0.1, 2.75))
CUELLO = ((C - 0.2, 2.9, 2.6, 0.6), (C + 1.8, 3.05, 2.75, 0.6))     # el cuello alto: (y, mx, mz, ch) abajo y arriba
FILO = 0.45                             # la franja olivo del borde (cuello)


def torso(p):
    """La bata sobre el torso, cerrada y en bloque, con la solapa que cruza al medio, el cuello alto y adentro el
    cuello de piel."""
    g = "Body/bata"
    caja(p, g, "cuerpo", *TORSO, MORADO)
    caja(p, g, "solapa", (-1.0, 23.0, -2.95), (0.5, C - 0.1, -2.75), MORADO)
    (y0, mx0, mz0, c0), (y1, mx1, mz1, c1) = CUELLO
    malla, n_fuera = tubo_hueco(anillo(0.0, y0, mx0, mz0, c0), anillo(0.0, y1, mx1, mz1, c1), grosor=0.25, tapa=False)
    morado, olivo = plano(MORADO), plano(OLIVO)
    tela = lambda t: olivo(t) if t.y > y1 - FILO else morado(t)
    p.malla(g, "cuello", malla, [tela] * n_fuera + [oscuro(OSCURO)] * (len(malla[1]) - n_fuera), dens=D)
    p.malla(g, "cuello_piel", bloque([(y0, mx0 - 0.35, mz0 - 0.35, c0), (y1 - 0.2, mx0 - 0.35, mz0 - 0.35, c0)]),
            plano(PIEL), dens=D)


# ---------------------------------------------------------------------------------------------- brazos
CENTRO_BRAZO = 5.5                      # x del medio del brazo (sin girar)
MANGA_CORTA = ((26.0, 2.15, 2.25, 0.55), (C + 0.2, 1.95, 2.05, 0.55))     # la bata: hueca, hasta medio brazo
CAMISA_OLIVO = ((22.9, 1.6, 1.65, 0.4), (26.4, 1.6, 1.65, 0.4))
CAMISA_BEIGE = ((19.7, 2.05, 2.1, 0.55), (21.4, 2.2, 2.25, 0.6), (22.6, 2.1, 2.15, 0.55), (23.3, 1.75, 1.8, 0.45))
BRAZAL = ((18.6, 1.15, 1.2, 0.3), (20.0, 1.2, 1.25, 0.3))     # la muneca, flaca


def brazos(p):
    """Las capas del brazo, dibujadas rectas y abiertas con el brazo: la manga corta de la bata (hueca, se ve la
    camisa adentro), la camisa olivo hasta el codo, la camisa beige esponjada hasta la muneca (con un rollo arriba)
    y el brazal de cuero con la hebilla dorada por afuera."""
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        giro = giro_brazo(s)
        cx = s * CENTRO_BRAZO
        girar = lambda m: geo.girar(m, giro["rot"], giro["piv"])
        (y0, mx0, mz0, c0), (y1, mx1, mz1, c1) = MANGA_CORTA
        malla, n_fuera = tubo_hueco(anillo(cx, y0, mx0, mz0, c0), anillo(cx, y1, mx1, mz1, c1), grosor=0.2)
        malla = girar(malla)
        p.malla(f"{hueso}/manga", "manga_corta", malla,
                [plano(MORADO)] * n_fuera + [oscuro(OSCURO)] * (len(malla[1]) - n_fuera), dens=D)
        p.malla(f"{hueso}/camisa", "camisa_olivo", girar(bloque(CAMISA_OLIVO, cx)), plano(OLIVO), dens=D)
        p.malla(f"{hueso}/camisa", "camisa_beige", girar(bloque(CAMISA_BEIGE, cx)), plano(BEIGE), dens=D)
        p.malla(f"{hueso}/brazal", "brazal", girar(bloque(BRAZAL, cx)), plano(CUERO), dens=D)
        xa, xb = sorted((s * (CENTRO_BRAZO + 1.1), s * (CENTRO_BRAZO + 1.35)))
        caja(p, f"{hueso}/brazal", "hebilla", (xa, 18.9, -0.5), (xb, 19.7, 0.5), ORO, **giro)


# ---------------------------------------------------------------------------------------------- cinturon y faldon
FAJA = ((20.6, 4.7, 3.0, 0.5), (23.6, 4.7, 3.0, 0.5))      # la parte de arriba de la falda: faja la tunica
CINTURON = ((21.3, 4.95, 3.25, 0.55), (23.0, 4.95, 3.25, 0.55))   # encima de la faja (asoma arriba y abajo)
ARO = (4.4, 2.75)                       # donde nacen las tiras, adentro de la faja: medio ancho y hondo
TIRA_ARRIBA = 21.0                      # las tiras empiezan adentro de la faja y salen por debajo
RUEDO = (8.4, 12.4)                     # donde termina cada tira: entre estas alturas, al azar (fijo)


def cinturon(p):
    """La faja de la falda (morado oscuro) que aprieta la tunica en la cintura, y encima el cinturon de cuero con la
    hebilla dorada adelante: la faja asoma arriba y abajo del cinturon, asi se ve que el cinturon va encima."""
    g = "Body/cinturon"
    p.malla(g, "faja", bloque(FAJA), oscuro(MORADO), dens=D)
    p.malla(g, "cinto", bloque(CINTURON), plano(CUERO), dens=D)
    zf = -CINTURON[0][2]
    caja(p, g, "hebilla", (-0.8, 21.1, zf - 0.25), (0.8, 23.25, zf + 0.1), ORO)
    caja(p, g, "hebilla_hueco", (-0.42, 21.55, zf - 0.32), (0.42, 22.8, zf - 0.2), CUERO_OSC)


def borde(t):
    """Punto del borde donde nacen las tiras (un rectangulo de esquinas cortadas bajo el cinturon) y su angulo,
    para t de 0 a 1 (empieza adelante al medio)."""
    ang = 180 + 360 * t
    a = math.radians(ang)
    sx, sz = math.sin(a), math.cos(a)
    mx, mz = ARO
    r = 1.0 / max(abs(sx) / mx, abs(sz) / mz, (abs(sx) + abs(sz)) / (mx + mz - 0.6))
    return (r * sx, r * sz), ang


def tira(ancho, largo, k, grueso=0.5):
    """Malla de una tira de tela colgando desde (0, 0): recta, con la punta escalonada (dos muescas fijas)."""
    a = (0.0, 0.5, 1.0)[int(azar(k, 1) * 3) % 3]
    b = (0.0, 0.5, 0.75)[int(azar(k, 2) * 3) % 3]
    w = ancho / 2
    perfil = [(-w, 0.0), (w, 0.0)]
    perfil += [(w, -largo + a), (w * 0.3, -largo + a)] if a else [(w, -largo)]
    perfil += [(w * 0.3, -largo)] if a else []
    perfil += [(-w * 0.4, -largo), (-w * 0.4, -largo + b), (-w, -largo + b)] if b else [(-w, -largo)]
    return geo.extruir(perfil, -grueso / 2, grueso / 2)


def faldon(p):
    """El faldon en tiras que salen de abajo del cinturon y se abren un poco: dos capas, cada tira de un largo
    distinto."""
    g = "Body/faldon"
    k = 0
    for capa, (n, fuera, abre, os) in enumerate(((22, 0.0, 7.0, False), (22, -0.25, 5.0, True))):
        for i in range(n):
            t = (i + 0.5 * capa) / n
            (x, z), ang = borde(t)
            a = math.radians(ang)
            hasta = RUEDO[0] + (RUEDO[1] - RUEDO[0]) * azar(k, 3) + 0.3 * capa
            largo = TIRA_ARRIBA - hasta
            if os:
                rampa = OSCURO if azar(k, 4) < 0.5 else MORADO
            else:
                rampa = OLIVO if azar(k, 6) < 0.3 else MORADO
            m = tira(1.75 if capa == 0 else 1.9, largo, k)
            m = geo.girar(m, (abre + 2 * azar(k, 5), ang - 180, 0))
            m = geo.mover(m, (x + math.sin(a) * fuera, TIRA_ARRIBA, z + math.cos(a) * fuera))
            p.malla(g, f"tira{capa}_{k}", m, oscuro(rampa) if os else plano(rampa), dens=D)
            k += 1


# ---------------------------------------------------------------------------------------------- bufanda y mochila
def bufanda(p):
    """La bufanda verde: un rollo grueso alrededor del cuello alto, y dos puntas que cuelgan adelante, a su
    derecha, con el final escalonado."""
    g = "Body/bufanda"
    p.malla(g, "rollo", aro_grueso((C - 0.4, 3.9, 3.45, 0.8), (C + 1.2, 3.7, 3.25, 0.8), 0.9), plano(OLIVO), dens=D)
    p.malla(g, "rollo_alto", aro_grueso((C + 0.4, 4.1, 3.6, 0.85), (C + 0.9, 4.1, 3.6, 0.85), 0.6), plano(OLIVO),
            dens=D)
    for k, (x, ancho, largo, z, giro_punta, os) in enumerate(((1.45, 1.6, 4.6, -3.35, 5, False),
                                                             (2.1, 1.3, 3.4, -3.15, -4, True))):
        m = geo.mover(geo.girar(tira(ancho, largo, 300 + k, grueso=0.45), (0, 0, giro_punta)), (x, C + 0.6, z))
        p.malla(g, f"punta{k}", m, oscuro(OLIVO) if os else plano(OLIVO), dens=D)


MOCHILA = ((-2.4, 23.4, 2.78), (2.4, 27.4, 4.6))       # el cuerpo de la mochila (abierta arriba)
PERGAMINO = ((-1.0, 3.7), 0.6, 26.0, 29.6, 6.0)         # (x, z), radio, abajo, arriba (asoma media mochila) y giro
FRASCO_MOCHILA = ((1.05, 3.65), 26.6, -8.0)             # (x, z), abajo y giro de la pocion de la mochila
CORREA = ((-2.6, 29.7), (4.45, 24.1), 1.1, (-3.1, -2.78))   # de su hombro izquierdo a su cadera derecha: ancho y z
HEBILLA_X = -0.6                                        # la hebilla de oro, en medio de la correa (libre de la bufanda)
FRASCOS = ((-2.0, 0.9, 1.3, VIOLETA), (0.2, 0.55, 0.8, CIAN), (3.3, 0.7, 1.0, ORO))   # colgando: x, ancho, alto, color


def interior(rampa):
    """Pintor de la mochila: por fuera el cuero; la tapa de arriba es el adentro (oscuro), porque va abierta."""
    fuera, adentro = plano(rampa), hex_(OSCURO["s"])
    return lambda t: adentro if t.cara == "up" else fuera(t)


def enrollado(centro_arriba, radio):
    """Pintor del pergamino: el papel beige; en la tapa de arriba, el rollo pintado (anillos mas oscuros)."""
    papel, linea = plano(BEIGE), hex_(BEIGE["s2"])

    def p(t):
        if t.n[1] > 0.8:
            d = math.dist((t.x, t.y, t.z), centro_arriba) / radio
            if d > 0.15 and (d * 4.5) % 1.0 < 0.3:
                return linea
        return papel(t)
    return p


def frasco(p, g, nombre, x, y_arriba, z, ancho, alto, rampa, rot=None, piv=None):
    """Un frasco cuadrado: el cuerpo de vidrio, el cuello y el corcho, colgando desde y_arriba (la punta del corcho)."""
    kw = dict(rot=rot, piv=piv) if rot else {}
    w, c = ancho / 2, ancho * 0.22
    corcho, cuello = y_arriba - 0.3, y_arriba - 0.3 - 0.35
    caja(p, g, nombre + "_corcho", (x - c - 0.05, corcho, z - c - 0.05), (x + c + 0.05, y_arriba, z + c + 0.05), BEIGE, **kw)
    caja(p, g, nombre + "_cuello", (x - c, cuello, z - c), (x + c, corcho, z + c), rampa, **kw)
    caja(p, g, nombre + "_cuerpo", (x - w, cuello - alto, z - w), (x + w, cuello, z + w), rampa, **kw)


def mochila(p):
    """La mochila de cuero en la espalda, abierta arriba (sin tapa), con un pergamino enrollado (12 lados, asoma media
    mochila, el rollo pintado en la tapa) y una pocion asomando; la correa gordita cruzada: de la mochila sube a su
    hombro izquierdo (pasa bajo la bufanda), cruza el pecho hasta su cadera derecha (por detras de las puntas de la
    bufanda) con la hebilla de oro en medio, y rodea el costado hasta la mochila; de la correa cuelgan tres frascos
    de distinto tamano."""
    g = "Body/mochila"
    (x0, y0, z0), (x1, y1, z1) = MOCHILA
    p.caja(g, "cuerpo", (x0, y0, z0), (x1, y1, z1), interior(CUERO), dens=D)
    for nombre, a, b in (("borde_atras", (x0, y1, z1 - 0.25), (x1, y1 + 0.45, z1)),
                         ("borde_frente", (x0, y1, z0), (x1, y1 + 0.45, z0 + 0.25)),
                         ("borde_der", (x1 - 0.25, y1, z0), (x1, y1 + 0.45, z1)),
                         ("borde_izq", (x0, y1, z0), (x0 + 0.25, y1 + 0.45, z1))):
        caja(p, g, nombre, a, b, CUERO_OSC)
    # el pergamino: un plano enrollado de 12 lados, con la tapa de arriba pintada con el rollo
    (px, pz), r, ya, yb, giro = PERGAMINO
    anillos = [geo.anillo(px, y, pz, r, r, 12, 15) for y in (ya, yb)]
    malla = geo.girar(geo.loft_puntos(anillos), (0, 0, giro), (px, ya, pz))
    centro = geo.girar(([(px, yb, pz)], []), (0, 0, giro), (px, ya, pz))[0][0]
    p.malla(g, "pergamino", malla, enrollado(centro, r), dens=D)
    (fx, fz), fy, fgiro = FRASCO_MOCHILA
    frasco(p, g, "pocion", fx, fy + 2.7, fz, 1.1, 1.7, VIOLETA, rot=(0, 0, fgiro), piv=(fx, fy, fz))
    # la correa
    (ax, ay), (bx, by), ancho, (za, zb) = CORREA
    largo, ang = math.hypot(bx - ax, by - ay), math.degrees(math.atan2(by - ay, bx - ax))
    linea = lambda x: ay + (by - ay) * (x - ax) / (bx - ax)
    caja(p, g, "correa_frente", (ax, ay - ancho / 2, za), (ax + largo, ay + ancho / 2, zb), CUERO_OSC, rot=(0, 0, ang),
         piv=(ax, ay, za))
    caja(p, g, "correa_atras", (ax - 0.55, MOCHILA[1][1] - 0.2, 2.78), (ax + 0.55, C - 0.3, 3.12), CUERO_OSC)
    caja(p, g, "correa_lado", (4.48, by - 0.5, -2.8), (4.85, by + 0.6, 2.8), CUERO_OSC)
    caja(p, g, "correa_espalda", (x1, by - 0.5, 2.78), (4.85, by + 0.6, 3.12), CUERO_OSC)
    hy = linea(HEBILLA_X)
    caja(p, g, "hebilla", (HEBILLA_X - 0.6, hy - 0.72, za - 0.22), (HEBILLA_X + 0.6, hy + 0.72, za + 0.05), ORO,
         rot=(0, 0, ang), piv=(HEBILLA_X, hy, za))
    caja(p, g, "hebilla_hueco", (HEBILLA_X - 0.3, hy - 0.38, za - 0.3), (HEBILLA_X + 0.3, hy + 0.38, za - 0.15),
         CUERO_OSC, rot=(0, 0, ang), piv=(HEBILLA_X, hy, za))
    # los frascos que cuelgan de la correa (cada uno de un hilo)
    for k, (x, ancho_f, alto, rampa) in enumerate(FRASCOS):
        y_hilo = linea(x) - ancho / 2 + 0.1
        z = za - ancho_f / 2 - 0.12
        caja(p, g, f"hilo{k}", (x - 0.06, y_hilo - 0.45, z - 0.06), (x + 0.06, y_hilo, z + 0.06), OSCURO)
        frasco(p, g, f"frasco{k}", x, y_hilo - 0.45, z, ancho_f, alto, rampa)


def abrigo(p):
    torso(p)
    brazos(p)
    faldon(p)
    cinturon(p)
    bufanda(p)
    mochila(p)
