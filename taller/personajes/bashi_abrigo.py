"""
Bashi: la bata (ver bashi.py), segun referencias/personajes/bashi_hoja2.png. Por ahora solo la forma con colores
lisos (sin accesorios ni textura).

  TORSO: la bata morada, cerrada (toda unida) y de 12 lados, con la solapa que cruza al medio.
  MANGAS en tres ESCALONES redondos (12 lados), cada uno mas ancho que el de arriba, despegadas del brazo y hasta
    la muneca, con el final olivo (en los huesos de los brazos, abiertas como los brazos). Por dentro asoma la
    CAMISA beige de manga larga hasta la muneca.
  FALDON: de la cintura para abajo en TIRAS al ras del estomago que se abren apenas, cada una de un largo distinto (al azar, fijo) y con la
    punta escalonada, en dos capas (la de abajo mas oscura tapa los huecos), cerrado todo alrededor. Algunas tiras
    olivo entre las moradas.
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import BEIGE, C, D, MORADO, OLIVO, OSCURO, azar, giro_brazo
from .meron import tubo_hueco

CINTURA_Y = 22.4                        # de aqui cuelga el faldon
ARO = (4.37, 2.73)                      # el torso donde empieza el faldon: medio ancho y hondo (las tiras van al ras)
RUEDO = (8.4, 12.4)                     # donde termina cada tira: entre estas alturas, al azar (fijo)


def plano(rampa):
    """Color liso de la pieza, apenas un tono por lado para que se lea la forma: arriba mas claro, los costados y
    abajo un tono mas oscuro."""
    b, m, s = hex_(rampa["b"]), hex_(rampa["m"]), hex_(rampa["s"])

    def p(t):
        n = t.n
        if n[1] > 0.6:
            return m
        if n[1] < -0.6 or abs(n[0]) > max(abs(n[2]), 0.7):
            return s
        return b
    return p


def caja(p, grupo, nombre, desde, hasta, rampa, **kw):
    p.caja(grupo, nombre, desde, hasta, plano(rampa), dens=D, **kw)


# ---------------------------------------------------------------------------------------------- torso
LADOS = 12                              # todo redondo pero de caras: el torso y las mangas son de 12 lados
TORSO = ((19.0, 4.35, 2.72), (22.4, 4.37, 2.73), (24.5, 4.45, 2.8), (28.5, 4.5, 2.85), (C + 0.35, 4.3, 2.6))
# secciones del torso de la bata, de abajo del estomago (tapado por el faldon) a los hombros: (y, medio ancho,
# medio hondo)


def torso(p):
    """La bata sobre el torso, cerrada y de 12 lados (redonda pero de caras, como las mangas): un solo cuerpo morado
    y la solapa que cruza al medio, de su derecha a su izquierda."""
    g = "Body/bata"
    giro = 180.0 / LADOS                                         # un lado plano adelante, atras y a los costados
    anillos = [geo.anillo(0.0, y, 0.0, rx, rz, LADOS, giro) for y, rx, rz in TORSO]
    p.malla(g, "cuerpo", geo.loft_puntos(anillos), plano(MORADO), dens=D)
    zf = min(-rz * math.cos(math.radians(giro)) for _, _, rz in TORSO)     # el frente plano mas adelante
    caja(p, g, "solapa", (-1.0, 22.4, zf - 0.2), (0.5, C + 0.1, zf + 0.3), MORADO)


# ---------------------------------------------------------------------------------------------- mangas
# la manga en tres escalones, cada uno mas ancho que el de arriba y separado del brazo; abajo redonda (8 lados) y
# termina en la muneca. (y de abajo, y de arriba, medio ancho en x, medio ancho en z, corrimiento hacia afuera)
ESCALONES = ((25.8, C + 0.4, 1.8, 1.9, 0.0), (22.6, 25.9, 2.1, 2.2, 0.15), (19.6, 22.7, 2.45, 2.55, 0.35))
CENTRO_BRAZO = 5.5                      # x del medio del brazo (sin girar)
FINAL = 0.7                             # alto de la franja olivo en el borde de la manga


def escalon(cx, y0, y1, rx, rz):
    """Un escalon de la manga: tubo hueco de 12 lados (redondo de caras), con la tapa de arriba (el escalon) y
    abierto abajo."""
    abajo = geo.anillo(cx, y0, 0.0, rx * 1.04, rz * 1.04, LADOS, 180.0 / LADOS)
    arriba = geo.anillo(cx, y1, 0.0, rx, rz, LADOS, 180.0 / LADOS)
    return tubo_hueco(abajo, arriba, grosor=0.15)


def tela_manga(giro):
    """La manga morada con el final olivo: una franja en el borde de abajo del ultimo escalon."""
    morado, olivo = plano(MORADO), plano(OLIVO)
    y_final = ESCALONES[-1][0] + FINAL

    def p(t):
        y = geo.desgirar((t.x, t.y, t.z), giro["rot"], giro["piv"])[1] + giro["piv"][1]
        return olivo(t) if y < y_final else morado(t)
    return p


def mangas(p):
    """Las mangas en tres escalones redondos que se abren hacia la muneca, despegadas del brazo (moradas, con el
    forro oscuro y el final olivo), y adentro la camisa beige de manga larga hasta la muneca; todo abierto con el
    brazo."""
    forro = plano({**OSCURO, "b": OSCURO["s"]})
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        giro = giro_brazo(s)
        for k, (y0, y1, rx, rz, fuera) in enumerate(ESCALONES):
            malla, n_fuera = escalon(s * (CENTRO_BRAZO + fuera), y0, y1, rx, rz)
            malla = geo.girar(malla, giro["rot"], giro["piv"])
            pint = [tela_manga(giro)] * n_fuera + [forro] * (len(malla[1]) - n_fuera)
            p.malla(f"{hueso}/manga", f"escalon{k}", malla, pint, dens=D)
        g = f"{hueso}/camisa"
        xa, xb = sorted((s * 4.4, s * 6.6))                     # angosta: sus esquinas no pasan la manga redonda
        caja(p, g, "manga_camisa", (xa, 19.4, -1.1), (xb, 27.0, 1.1), BEIGE, **giro)
        xa, xb = sorted((s * 4.0, s * 7.0))
        caja(p, g, "puno_camisa", (xa, 19.0, -1.45), (xb, 19.8, 1.45), BEIGE, **giro)


# ---------------------------------------------------------------------------------------------- faldon
def borde(t):
    """Punto del borde de la bata en la cintura y su angulo, para t de 0 a 1 (empieza adelante al medio)."""
    ang = 180 + 360 * t
    a = math.radians(ang)
    mx, mz = ARO
    return (mx * math.sin(a), mz * math.cos(a)), ang


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
    """El faldon en tiras: dos capas alrededor de la cintura, cerrado, cada tira de un largo distinto."""
    g = "Body/faldon"
    k = 0
    for capa, (n, fuera, abre, oscuro) in enumerate(((22, -0.2, 2.5, False), (22, -0.45, 1.5, True))):
        for i in range(n):
            t = (i + 0.5 * capa) / n
            (x, z), ang = borde(t)
            a = math.radians(ang)
            hasta = RUEDO[0] + (RUEDO[1] - RUEDO[0]) * azar(k, 3) + 0.3 * capa
            largo = CINTURA_Y - hasta
            if oscuro:
                rampa = OSCURO if azar(k, 4) < 0.5 else MORADO
            else:
                rampa = OLIVO if azar(k, 6) < 0.3 else MORADO
            m = tira(1.7 if capa == 0 else 1.9, largo, k)
            m = geo.girar(m, (abre + 1.5 * azar(k, 5), ang - 180, 0))
            m = geo.mover(m, (x + math.sin(a) * fuera, CINTURA_Y, z + math.cos(a) * fuera))
            p.malla(g, f"tira{capa}_{k}", m, plano(rampa if not oscuro else {**rampa, "b": rampa["s"]}), dens=D)
            k += 1


def abrigo(p):
    torso(p)
    mangas(p)
    faldon(p)
