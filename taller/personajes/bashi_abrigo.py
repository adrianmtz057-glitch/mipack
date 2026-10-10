"""
Bashi: la bata (ver bashi.py), segun referencias/personajes/bashi_hoja2.png. Por ahora solo la forma con colores
lisos (sin accesorios ni textura).

  TORSO: la bata morada cubre el torso: espalda, costados y dos delanteros que se abren al medio; por la abertura
    se ve el chaleco oscuro y la camisa beige.
  MANGAS (en los huesos de los brazos, abiertas como los brazos): hombrera morada redonda, brazo morado, un bullon
    grande en el codo (olivo en la derecha, beige en la izquierda) y el puno enrollado del otro color.
  FALDON: de la cintura a la rodilla en TIRAS que se abren hacia abajo, de largos disparejos y con la punta
    escalonada, en dos capas (la de abajo mas oscura tapa los huecos); adelante se abre al medio y deja ver las
    piernas; atras baja mas. Los delanteros llevan olivo por afuera y morado al medio.
"""

import math

from .. import malla as geo
from ..textura import hex_a_rgba as hex_
from .bashi import BEIGE, BRAZO_X, C, D, MORADO, OLIVO, OSCURO, TORSO_CAJA, azar, giro_brazo

CINTURA_Y = 22.4                        # de aqui cuelga el faldon
ARO = (4.5, 2.8, 3.0)                   # el borde de la bata en la cintura: medio ancho, z adelante, z atras
ABERTURA = 15.0                         # grados a cada lado del frente sin tiras: la bata abierta
RUEDO = {"frente": 9.6, "lado": 10.4, "atras": 8.8}     # donde termina el faldon


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
    """La bata sobre el torso, abierta adelante: por la abertura se ve el chaleco oscuro y la camisa beige."""
    g = "Body/bata"
    (x0, y0, z0), (x1, y1, z1) = TORSO_CAJA
    caja(p, g, "chaleco", (x0, 21.0, z0), (x1, C, z1), OSCURO)
    caja(p, g, "camisa", (-1.3, 23.0, z0 - 0.15), (1.3, C - 0.1, z0), BEIGE)
    abajo = 21.4
    caja(p, g, "espalda", (-4.45, abajo, 2.25), (4.45, C + 0.25, 2.75), MORADO)
    for s in (1, -1):
        a, b = sorted((s * 4.0, s * 4.45))
        caja(p, g, f"costado{s}", (a, abajo, -2.75), (b, C + 0.25, 2.75), MORADO)
        a, b = sorted((s * 1.3, s * 4.45))
        caja(p, g, f"delantero{s}", (a, abajo, -2.75), (b, C + 0.25, -2.25), MORADO)
        a, b = sorted((s * 1.3, s * 2.1))                        # la solapa: el borde de la abertura doblado
        caja(p, g, f"solapa{s}", (a, 25.5, -3.0), (b, C + 0.25, -2.75), MORADO)
    caja(p, g, "hombros", (-4.45, C - 0.1, -2.75), (4.45, C + 0.35, 2.75), MORADO)


# ---------------------------------------------------------------------------------------------- mangas
def mangas(p):
    """Las mangas, dibujadas rectas y abiertas con el brazo: hombrera redonda, brazo, bullon en el codo y puno."""
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        g = f"{hueso}/manga"
        bullon, puno = (OLIVO, BEIGE) if s > 0 else (BEIGE, OLIVO)
        piezas = (
            ("hombrera", (3.8, 27.4, -1.95), (7.35, 30.5, 1.95), MORADO),
            ("hombrera_alta", (4.2, 30.5, -1.6), (7.0, 30.9, 1.6), MORADO),
            ("brazo", (4.05, 23.6, -1.7), (7.15, 27.4, 1.7), MORADO),
            ("bullon_alto", (3.95, 23.2, -1.85), (7.25, 23.6, 1.85), bullon),
            ("bullon", (3.7, 20.4, -2.1), (7.5, 23.2, 2.1), bullon),
            ("puno", (3.85, 19.0, -1.95), (7.35, 20.4, 1.95), puno),
        )
        for nombre, a, b, rampa in piezas:
            xa, xb = sorted((s * a[0], s * b[0]))
            caja(p, g, nombre, (xa, a[1], a[2]), (xb, b[1], b[2]), rampa, **giro_brazo(s))


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
    """El faldon en tiras: dos capas alrededor de la cintura; adelante abierto, atras mas largo."""
    g = "Body/faldon"
    k = 0
    for capa, (n, fuera, abre, oscuro) in enumerate(((22, 0.25, 9.0, False), (22, 0.0, 6.0, True))):
        for i in range(n):
            t = (i + 0.5 * capa) / n
            (x, z), ang = borde(t)
            frente = abs(((ang - 180 + 180) % 360) - 180)        # 0 adelante al medio, 180 atras
            if frente < ABERTURA - 5 * capa:
                continue
            a = math.radians(ang)
            zona = "frente" if frente < 60 else "lado" if frente < 120 else "atras"
            hasta = RUEDO[zona] + 0.8 * (azar(k, 3) - 0.5) + 0.3 * capa
            largo = CINTURA_Y - hasta
            if oscuro:
                rampa = OSCURO if azar(k, 4) < 0.5 else MORADO
            elif zona == "frente":
                rampa = OLIVO if abs(x) > 2.4 else MORADO
            else:
                rampa = OLIVO if i % 4 == 1 else MORADO
            m = tira(1.7 if capa == 0 else 1.9, largo, k)
            m = geo.girar(m, (abre + 3 * azar(k, 5), ang - 180, 0))
            m = geo.mover(m, (x + math.sin(a) * fuera, CINTURA_Y, z + math.cos(a) * fuera))
            p.malla(g, f"tira{capa}_{k}", m, plano(rampa if not oscuro else {**rampa, "b": rampa["s"]}), dens=D)
            k += 1


def abrigo(p):
    torso(p)
    mangas(p)
    faldon(p)
