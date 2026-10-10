"""
Bashi: la bata (ver bashi.py), segun referencias/personajes/bashi_hoja2.png. Por ahora solo la forma con colores
lisos (sin accesorios ni textura).

  TORSO: la bata morada, cerrada (toda unida), con la solapa que cruza al medio.
  MANGAS de kimono como las de meron (en los huesos de los brazos, abiertas como los brazos): anchas, se abren hacia
    afuera y hacia abajo; adelante terminan en la muneca y atras cuelgan mas, como la bolsa del kimono. Por dentro
    asoma la CAMISA beige de manga larga hasta la muneca.
  FALDON: de la cintura para abajo en TIRAS que se abren, cada una de un largo distinto (al azar, fijo) y con la
    punta escalonada, en dos capas (la de abajo mas oscura tapa los huecos), cerrado todo alrededor. Algunas tiras
    olivo entre las moradas.
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import BEIGE, C, D, MORADO, OLIVO, OSCURO, TORSO_CAJA, azar, giro_brazo
from .meron import tubo_hueco

CINTURA_Y = 22.4                        # de aqui cuelga el faldon
ARO = (4.5, 2.8, 3.0)                   # el borde de la bata en la cintura: medio ancho, z adelante, z atras
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
def torso(p):
    """La bata sobre el torso, cerrada: un solo cuerpo morado y la solapa que cruza al medio, de su derecha a su
    izquierda."""
    g = "Body/bata"
    caja(p, g, "cuerpo", (-4.45, 21.4, -2.75), (4.45, C + 0.35, 2.75), MORADO)
    caja(p, g, "solapa", (-1.6, 21.4, -2.95), (0.6, C + 0.35, -2.75), MORADO)


# ---------------------------------------------------------------------------------------------- mangas
MANGA = (4.1, 7.0, 8.2, C + 0.4, 21.0, 17.0, -2.3, 2.6)
# x de adentro, x de afuera arriba y abajo; y del hombro, de la muneca (adelante) y de la bolsa (atras); z de
# adelante y de atras abajo


def manga_kimono():
    """Manga ancha de kimono del lado derecho (como la de meron): se abre hacia afuera y hacia abajo; adelante
    termina en la muneca y atras cuelga mas, como la bolsa. Hueca, con forro."""
    xi, xo_arriba, xo_abajo, arriba, puno, bolsa, zf, zb = MANGA
    sup = [(xo_arriba, arriba, 1.9), (xo_arriba, arriba, -1.9), (xi, arriba, -1.9), (xi, arriba, 1.9)]
    inf = [(xo_abajo, bolsa, zb), (xo_abajo, puno, zf), (xi + 0.05, puno, zf), (xi + 0.05, bolsa, zb)]
    return tubo_hueco(inf, sup)


def tela_manga(giro):
    """La manga morada con el final olivo: una franja en el borde de abajo, que sigue el corte (adelante en la
    muneca, atras en la bolsa)."""
    _, _, _, _, puno, bolsa, zf, zb = MANGA
    morado = plano(MORADO)
    olivo = plano(OLIVO)

    def p(t):
        x, y, z = geo.desgirar((t.x, t.y, t.z), giro["rot"], giro["piv"])        # relativo al hombro
        y, z = y + giro["piv"][1], z + giro["piv"][2]
        k = max(0.0, min(1.0, (z - zf) / (zb - zf)))
        return olivo(t) if y < puno + (bolsa - puno) * k + 0.75 else morado(t)
    return p


def mangas(p):
    """Las mangas de kimono (moradas, con el forro oscuro) y adentro la camisa beige de manga larga hasta la
    muneca, todo abierto con el brazo."""
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        giro = giro_brazo(s)
        malla, n_fuera = manga_kimono()
        if s < 0:
            malla = geo.espejo_x(malla)
        malla = geo.girar(malla, giro["rot"], giro["piv"])
        pint = [tela_manga(giro)] * n_fuera + [plano({**OSCURO, "b": OSCURO["s"]})] * (len(malla[1]) - n_fuera)
        p.malla(f"{hueso}/manga", "manga", malla, pint, dens=D)
        g = f"{hueso}/camisa"
        xa, xb = sorted((s * 4.15, s * 6.85))
        caja(p, g, "manga_camisa", (xa, 19.4, -1.3), (xb, 27.0, 1.3), BEIGE, **giro)
        xa, xb = sorted((s * 4.0, s * 7.0))
        caja(p, g, "puno_camisa", (xa, 19.0, -1.45), (xb, 19.8, 1.45), BEIGE, **giro)


# ---------------------------------------------------------------------------------------------- faldon
def borde(t):
    """Punto del borde de la bata en la cintura y su angulo, para t de 0 a 1 (empieza adelante al medio)."""
    ang = 180 + 360 * t
    a = math.radians(ang)
    sx, sz = math.sin(a), math.cos(a)
    mx, zf, zb = ARO
    r = 1.0 / max(abs(sx) / mx, abs(sz) / (zb if sz > 0 else zf))
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
    """El faldon en tiras: dos capas alrededor de la cintura, cerrado, cada tira de un largo distinto."""
    g = "Body/faldon"
    k = 0
    for capa, (n, fuera, abre, oscuro) in enumerate(((22, 0.25, 9.0, False), (22, 0.0, 6.0, True))):
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
            m = geo.girar(m, (abre + 3 * azar(k, 5), ang - 180, 0))
            m = geo.mover(m, (x + math.sin(a) * fuera, CINTURA_Y, z + math.cos(a) * fuera))
            p.malla(g, f"tira{capa}_{k}", m, plano(rampa if not oscuro else {**rampa, "b": rampa["s"]}), dens=D)
            k += 1


def abrigo(p):
    torso(p)
    mangas(p)
    faldon(p)
