"""
Kemira, diosa de Thza (avatar). Hecha a mano con el kit con el estilo de referencias/personajes/kemira_estilo.png
(guerrera tribal de plumas; la imagen es inspiracion, no copia) y la complexion de kemira_complexion.png: cabeza
grande de cara anime, cuerpo esbelto con curvas, detalles en bloques. Tamano de dios.

Formas:
  CABEZA de piel oscura: ojos celestes rasgados con pestana negra, cejas finas, labios y marcas blancas en la mejilla
  PELO blanco en cubos desordenados; VINCHA tejida con cuentas que cuelgan sobre la frente
  PENACHO enorme de plumas negras con base y puntas blancas, en abanico detras de la cabeza
  Top negro sin tirantes, faja tejida, collar pintado, flecos de plumas en la cadera y falda larga negra con abertura
  Pelaje de plumas en el hombro izquierdo, vendas en antebrazos, guante sin dedos, pintura blanca en brazos y piernas
  BACULO largo en la mano derecha con cabeza curva en gancho y un rombo
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .revolthir import color, voxel

D = 4
D_CARA = 8

PIEL = {"s": "#5E3A28", "b": "#7A4B33", "l": "#8E5A3E"}
PELO = {"s": "#C9CBD0", "b": "#E8E9EC", "l": "#FAFAFB"}
NEGRO = {"s": "#17161B", "b": "#24232A", "l": "#34333C"}
GRIS = {"s": "#5E5B57", "b": "#7D7973", "l": "#9A958D"}
PLUMA_NEGRA = {"s": "#1A1C24", "b": "#2A2D38", "l": "#3B3F4D"}
BLANCO = "#F2F1EE"
OJO, PESTANA, LABIO = "#7EC3E8", "#141217", "#5A3438"

CUELLO, TOPE = 27.0, 36.0


def _en(u, v, u0, u1, v0, v1):
    return u0 <= u <= u1 and v0 <= v <= v1


PIEL_TEX = voxel(PIEL, claro=0.2)


def ojo(u, v):
    """Ojo rasgado (u absoluto desde el centro, v desde el menton)."""
    if not _en(u, v, 0.8, 3.4, 3.4, 5.0):
        return None
    arriba = 4.55 + 0.25 * (u - 0.8) / 2.6                       # sube hacia afuera: mirada afilada
    abajo = 3.65 + 0.15 * (u - 0.8) / 2.6
    if arriba <= v <= arriba + 0.4 or (u > 3.0 and abajo + 0.3 < v <= arriba + 0.4):
        return hex_(PESTANA)
    if not (abajo <= v < arriba):
        return None
    if _en(u, v, 1.5, 2.6, abajo, arriba):
        if _en(u, v, 1.75, 2.0, arriba - 0.45, arriba - 0.2):
            return hex_("#FFFFFF")
        return hex_("#2E5F86" if v > arriba - 0.3 or abs(u - 2.05) < 0.22 else OJO)
    return hex_(BLANCO)


def cara(t):
    u, v = -t.x, t.y - CUELLO
    au = abs(u)
    c = ojo(au, v)
    if c:
        return c
    if 0.9 <= au <= 3.1 and abs(v - (5.55 + 0.25 * (au - 0.9) / 2.2)) < 0.1:      # cejas finas hacia arriba
        return hex_("#D9D9DD")
    if _en(u, v, -0.9, 0.9, 1.6, 2.05):                                          # labios
        return hex_(LABIO if v > 1.82 or au < 0.7 else PIEL["s"])
    if u > 0 and any(abs(au - c0) < 0.1 for c0 in (2.3, 2.7)) and 2.3 <= v <= 3.35:   # marcas blancas en la mejilla
        return hex_(BLANCO)
    return PIEL_TEX(t)


def cabeza(t):
    return cara(t) if t.cara == "north" else PIEL_TEX(t)


PELO_TEX = voxel(PELO, claro=0.15)


def tejido(t):
    """Banda tejida: zigzag claro sobre gris oscuro."""
    u = t.x if t.cara in ("north", "south") else t.z
    v = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    z = abs(((u * 1.2) % 1.0) - 0.5) * 2
    if abs(v - (0.25 + 0.5 * z)) < 0.14:
        return hex_(BLANCO)
    return hex_(NEGRO["l"] if v > 0.85 or v < 0.15 else GRIS["s"])


def torso(t):
    """Piel con el collar pintado arriba del top: banda tejida y colgantes."""
    if t.cara == "north" and t.y > 25.2:
        if t.y > 26.3:
            return tejido(t)
        if any(abs(t.x - c) < 0.18 for c in (-1.4, -0.7, 0.0, 0.7, 1.4)) and t.y > 25.5 + abs(t.x) * 0.3:
            return hex_(BLANCO if abs(t.x) < 0.1 else GRIS["l"])
    return PIEL_TEX(t)


def pintura(t):
    """Piel de brazos y piernas con rayas blancas pintadas."""
    if t.cara != "up" and t.cara != "down" and (t.y % 3.2) < 0.22:
        return hex_(BLANCO)
    return PIEL_TEX(t)


def venda(t):
    v = (t.y * 2.2 + (t.x + t.z) * 0.6) % 1.0
    return hex_(GRIS["l"] if v < 0.45 else GRIS["b"] if v < 0.85 else GRIS["s"])


def flecos(t):
    """Flecos de plumas en la cadera: blancas y grises, con el borde de abajo en puntas."""
    u = t.x if t.cara in ("north", "south") else t.z
    k = int((u + 50) // 0.7)
    if t.cara not in ("up",) and t.y < t.f[1] + (0.0, 0.8, 0.3, 1.1, 0.5)[k % 5]:
        return TRANSPARENTE
    return hex_(BLANCO if k % 3 else GRIS["l"])


def penacho(p, T):
    """Abanico de plumas detras de la cabeza: una fila larga atras y una mas corta adelante. Cada pluma es una hoja
    low-poly negra con la base clara; una de cada tres lleva la punta blanca."""
    g = "Head/penacho"
    piv = (0.0, T - 2.6, 4.2)
    for fila, (n, largo, ancho, dz, abre) in enumerate(((15, 13.0, 2.4, 0.0, 115), (11, 9.5, 2.0, -0.5, 95))):
        for k in range(n):
            ang = -abre + 2 * abre * k / (n - 1)
            l = largo * (0.82 + 0.18 * math.cos(math.radians(ang)))
            w = ancho
            perfil = [(-0.25 * w, 0.0), (0.25 * w, 0.0), (0.5 * w, 0.3 * l), (0.42 * w, 0.72 * l), (0.0, l),
                      (-0.42 * w, 0.72 * l), (-0.5 * w, 0.3 * l)]
            z = piv[2] + dz
            m = geo.extruir([(piv[0] + a, piv[1] + b) for a, b in perfil], z - 0.12, z + 0.12)
            giro = (-18 - 6 * fila, 0, -ang)
            m = geo.girar(m, giro, (piv[0], piv[1], z))
            p.malla(g, f"pluma{fila}_{k}", m, _pintor_pluma(giro, (piv[0], piv[1], z), l, (k + fila) % 3 == 0), dens=D)


def _pintor_pluma(giro, piv, largo, punta_blanca):
    def p(t):
        u, v, _ = geo.desgirar((t.x, t.y, t.z), giro, piv)
        f = v / largo                                                  # 0 en la base, 1 en la punta
        if f < 0.12:
            return hex_("#DADADF")
        if punta_blanca and f > 0.76:
            return hex_(BLANCO)
        return hex_(PLUMA_NEGRA["l"] if abs(u) < 0.12 else PLUMA_NEGRA["b"])
    return p


def pelo(p, C, T):
    """Pelo blanco muy largo peinado hacia atras: nace detras de la diadema, cubre arriba y cae por la espalda en
    mechones de distinto largo; adelante solo unos mechones sueltos sobre la cara."""
    g = "Head/pelo"
    p.caja(g, "arriba", (-5.0, T - 1.7, -5.0), (5.0, T + 0.9, 5.2), PELO_TEX, dens=D)
    p.caja(g, "nuca", (-5.1, C + 1.0, 3.2), (5.1, T - 1.0, 5.6), PELO_TEX, dens=D)
    for s in (1, -1):                                          # costados que van hacia atras
        a, b = sorted((s * 4.6, s * 5.5))
        p.caja(g, f"costado{s}", (a, C + 0.6, -1.4), (b, T - 1.0, 5.4), PELO_TEX, dens=D)
    # la cola larga hacia atras: mechones que bajan por la espalda, abiertos un poco hacia afuera
    for k, (largo, giro) in enumerate(((13.0, 10), (15.5, 5), (17.0, 1), (16.0, -3), (14.0, -8), (11.5, -12))):
        x = -4.6 + k * (9.2 / 6)
        p.caja(g, f"largo{k}", (x, T - 1.0 - largo, 4.4), (x + 9.2 / 6, T - 0.6, 6.0), PELO_TEX,
               rot=(-14 - 2 * (k % 2), 0, giro), piv=(x + 4.6 / 6, T - 0.6, 5.2), dens=D)
    # mechones sueltos sobre la cara, debajo de la diadema
    for k, (x, abajo, ancho) in enumerate(((-3.9, C + 4.0, 1.3), (-2.0, C + 5.6, 1.1), (1.4, C + 5.2, 1.2),
                                          (3.0, C + 3.6, 1.4))):
        p.caja(g, f"mechon{k}", (x, abajo, -5.0), (x + ancho, T - 2.6, -4.55), PELO_TEX,
               rot=(0, 0, (k % 2 * 2 - 1) * 6), piv=(x + ancho / 2, T - 2.6, -4.8), dens=D)
    # diadema tejida con las cuentas que cuelgan sobre la frente; el pelo sale por detras de ella
    p.caja(g, "diadema", (-5.25, T - 2.9, -5.25), (5.25, T - 1.6, 1.0), tejido, dens=D)
    for k, x in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        largo = 1.6 - abs(x) * 0.6
        p.caja(g, f"cuenta{k}", (x - 0.12, T - 2.9 - largo, -5.4), (x + 0.12, T - 2.9, -5.25),
               color(GRIS["l"] if k % 2 else BLANCO), dens=D_CARA)
    p.caja(g, "gota", (-0.3, T - 5.0, -5.45), (0.3, T - 4.5, -5.25), color(OJO), dens=D_CARA)


def felpa(p, grupo, nombre, centro, rx, rz, n, tam, giro_y=0.0):
    """Anillo de felpa: cubitos negros y grises girados alrededor de un ovalo (cuello, cintura, brazos)."""
    cx, cy, cz = centro
    for k in range(n):
        a = math.radians(360 * k / n + giro_y)
        x, z = cx + rx * math.cos(a), cz + rz * math.sin(a)
        y = cy + 0.35 * math.sin(a * 3)
        l = tam * (0.85 + 0.25 * (k % 3) / 2)
        pint = voxel(PLUMA_NEGRA if k % 4 else GRIS, claro=0.12)
        p.caja(grupo, f"{nombre}{k}", (x - l / 2, y - l / 2, z - l / 2), (x + l / 2, y + l / 2, z + l / 2), pint,
               rot=((k * 31) % 50 - 25, (k * 17) % 50 - 25, (k * 23) % 50 - 25), dens=D)


def baculo(p, L):
    """Baculo largo en la mano derecha, con la empunadura vendada y la cabeza curva en gancho."""
    g = "RightArm/baculo"
    x, z = 6.5, -2.4
    p.caja(g, "vara", (x - 0.35, 2.0, z - 0.35), (x + 0.35, 41.0, z + 0.35), voxel(NEGRO, claro=0.1), dens=D)
    p.caja(g, "vendado", (x - 0.5, 34.5, z - 0.5), (x + 0.5, 40.6, z + 0.5), venda, dens=D)
    perfil = [(-3.6, 1.4), (-1.2, 2.6), (1.6, 2.8), (3.8, 1.8), (4.6, 0.0), (3.6, -1.6), (3.0, -0.2),
              (1.6, 0.6), (-0.6, 0.6), (-2.8, 0.0), (-4.0, -1.0)]
    cabeza_m = geo.extruir([(x + a, 41.0 + b) for a, b in perfil], z - 0.4, z + 0.4)

    def pint(t):
        if abs(t.n[2]) > 0.7 and abs(t.x - (x - 0.2)) + abs(t.y - 42.6) < 0.6:          # el rombo
            return hex_(BLANCO) if abs(t.x - (x - 0.2)) + abs(t.y - 42.6) > 0.35 else hex_(NEGRO["b"])
        if t.x > x + 3.0 or t.x < x - 3.2:                                              # puntas de hueso
            return hex_(BLANCO)
        return hex_("#2C3A48")
    p.malla(g, "cabeza", cabeza_m, pint, dens=D)


def construir():
    p = Personaje("kemira", altura=TOPE, cabeza=9, torso=(7.2, 10, 4.0), brazo=(2.6, 2.6), pierna=(3.6, 3.6))
    C, T, L = p.cuello, p.tope, p.lh                       # 27, 36, 17
    assert (C, T) == (CUELLO, TOPE)

    p.caja("Head/cabeza", "cabeza", (-4.5, C, -4.5), (4.5, T, 4.5), cabeza, dens=D_CARA)
    pelo(p, C, T)
    penacho(p, T)

    # torso relleno: hombros y pecho anchos, cintura marcada pero no de palo, cadera ancha
    g = "Body/cuerpo"
    p.caja(g, "pecho", (-3.6, 22.2, -2.0), (3.6, C, 2.0), torso, dens=D)
    p.caja(g, "cintura", (-2.9, L + 1.8, -1.7), (2.9, 22.2, 1.7), PIEL_TEX, dens=D)
    p.caja(g, "cadera", (-4.2, L, -2.2), (4.2, L + 2.4, 2.2), PIEL_TEX, dens=D)
    p.caja("Body/ropa", "top", (-3.8, 22.5, -3.3), (3.8, 25.5, 2.2), voxel(NEGRO, claro=0.15), dens=D)
    p.caja("Body/ropa", "top_medio", (-0.25, 22.8, -3.35), (0.25, 25.2, -3.25), color(NEGRO["s"]), dens=D)
    p.caja("Body/ropa", "faja", (-3.05, 20.2, -1.85), (3.05, 21.6, 1.85), tejido, dens=D)
    p.caja("Body/ropa", "flecos", (-4.45, L - 1.9, -2.45), (4.45, L + 1.7, 2.45), flecos, dens=D)
    p.caja("Body/ropa", "cinto", (-4.4, L + 1.5, -2.4), (4.4, L + 2.2, 2.4), voxel(NEGRO, claro=0.1), dens=D)
    felpa(p, "Body/felpa", "cuello", (0.0, C + 0.1, 0.0), 3.4, 2.2, 12, 1.5)
    felpa(p, "Body/felpa", "cintura", (0.0, 21.0, 0.0), 3.3, 2.1, 12, 1.2, 15)

    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.6, s * 6.2))
        p.caja(f"{hueso}/brazo", "brazo", (x1, L - 1.2, -1.3), (x2, C - 0.4, 1.3), pintura, dens=D)
        v1, v2 = sorted((s * 3.5, s * 6.3))
        p.caja(f"{hueso}/ropa", "venda", (v1, L + 0.6, -1.4), (v2, L + 4.8, 1.4), venda, dens=D)
        p.caja(f"{hueso}/ropa", "guante", (v1, L - 1.3, -1.4), (v2, L + 0.6, 1.4), voxel(NEGRO, claro=0.1), dens=D)
        felpa(p, f"{hueso}/ropa", "manga", (s * 4.9, C - 2.6, 0.0), 1.7, 1.6, 9, 1.2, 20 * s)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        m1, m2 = sorted((s * 0.0, s * 4.2))                # muslo ancho que se afina a la pantorrilla
        x1, x2 = sorted((s * 0.4, s * 3.5))
        p.caja(f"{hueso}/pierna", "muslo", (m1, 9.0, -2.1), (m2, L, 2.1), pintura, dens=D)
        p.caja(f"{hueso}/pierna", "pantorrilla", (x1, 1.0, -1.6), (x2, 9.0, 1.6), pintura, dens=D)
        p.caja(f"{hueso}/pierna", "pie", (x1, 0.0, -2.3), (x2, 1.0, 1.6), PIEL_TEX, dens=D)
        p.caja(f"{hueso}/ropa", "tobillo", (x1 - 0.1, 1.0, -1.7), (x2 + 0.1, 3.2, 1.7), venda, dens=D)
        if s > 0:                                          # falda larga de este lado; del otro, la abertura
            p.caja(f"{hueso}/ropa", "falda", (m1 - 0.2, 3.6, -2.3), (m2 + 0.2, L, 2.3), voxel(NEGRO, claro=0.1), dens=D)
        else:
            p.caja(f"{hueso}/ropa", "falda_atras", (m1 - 0.2, 3.6, 0.3), (m2 + 0.2, L, 2.3), voxel(NEGRO, claro=0.1),
                   dens=D)
            p.caja(f"{hueso}/ropa", "liga", (m1 - 0.12, 11.6, -2.22), (m2 + 0.12, 12.6, 2.22), voxel(NEGRO), dens=D)

    baculo(p, L)
    return p
