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
    g = "Head/pelo"
    p.caja(g, "casco", (-5.0, T - 2.2, -5.0), (5.0, T + 0.7, 5.0), PELO_TEX, dens=D)
    for k, abajo in enumerate((C + 5.0, C + 6.2, C + 5.6, C + 6.4, C + 5.2, C + 6.0, C + 4.6)):
        x = -4.9 + k * 1.4
        p.caja(g, f"fleco{k}", (x, abajo, -5.4), (x + 1.4, T - 0.5, -4.6), PELO_TEX, rot=(0, 0, (k % 3 - 1) * 6),
               piv=(x + 0.7, T - 0.5, -5.0), dens=D)
    for s in (1, -1):
        for k, (z0, abajo) in enumerate(((-4.8, C + 0.6), (-2.2, C - 0.6), (0.6, C + 0.2), (3.0, C - 0.2))):
            a, b = sorted((s * 4.6, s * 5.5))
            p.caja(g, f"lado{s}_{k}", (a, abajo, z0), (b, T - 1.0, z0 + 2.6), PELO_TEX, rot=(0, 0, s * 5),
                   piv=(s * 5.0, T - 1.0, z0 + 1.3), dens=D)
    # melena de atras desordenada: mechones de distinto largo y hondura, algunos un poco girados
    for k, (abajo, hondo) in enumerate(((C - 1.4, 5.6), (C + 0.6, 5.2), (C - 2.4, 6.0), (C - 0.4, 5.4),
                                        (C - 2.0, 5.9), (C + 0.8, 5.3), (C - 1.0, 5.7))):
        x = -5.0 + k * (10.0 / 7)
        p.caja(g, f"atras{k}", (x, abajo, 4.3), (x + 10.0 / 7, T - 1.0, hondo), PELO_TEX, rot=(-8 - 4 * (k % 2), 0, (k % 3 - 1) * 7),
               piv=(x + 5.0 / 7, T - 1.0, 4.8), dens=D)
    # vincha tejida y las cuentas que cuelgan sobre la frente
    p.caja(g, "vincha", (-5.15, T - 2.9, -5.6), (5.15, T - 1.9, 5.15), tejido, dens=D)
    for k, x in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        largo = 1.6 - abs(x) * 0.6
        p.caja(g, f"cuenta{k}", (x - 0.12, T - 2.9 - largo, -5.75), (x + 0.12, T - 2.9, -5.55),
               color(GRIS["l"] if k % 2 else BLANCO), dens=D_CARA)
    p.caja(g, "gota", (-0.3, T - 5.0, -5.8), (0.3, T - 4.5, -5.55), color(OJO), dens=D_CARA)


def baculo(p, L):
    """Baculo largo en la mano derecha, con la empunadura vendada y la cabeza curva en gancho."""
    g = "RightArm/baculo"
    x, z = 5.4, -2.2
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
    p = Personaje("kemira", altura=TOPE, cabeza=9, torso=(6.0, 10, 3.4), brazo=(2.0, 2.2), pierna=(2.7, 2.9))
    C, T, L = p.cuello, p.tope, p.lh                       # 27, 36, 17
    assert (C, T) == (CUELLO, TOPE)

    p.caja("Head/cabeza", "cabeza", (-4.5, C, -4.5), (4.5, T, 4.5), cabeza, dens=D_CARA)
    pelo(p, C, T)
    penacho(p, T)

    # torso esbelto: cintura angosta, top negro con volumen, faja tejida, flecos y falda
    g = "Body/cuerpo"
    p.caja(g, "pecho", (-3.1, 22.4, -1.7), (3.1, C, 1.7), torso, dens=D)
    p.caja(g, "cintura", (-2.2, L + 1.6, -1.3), (2.2, 22.4, 1.3), PIEL_TEX, dens=D)       # cintura fina
    p.caja(g, "cadera", (-3.6, L, -1.9), (3.6, L + 2.2, 1.9), PIEL_TEX, dens=D)           # cadera ancha
    p.caja("Body/ropa", "top", (-3.3, 22.7, -2.9), (3.3, 25.4, 1.9), voxel(NEGRO, claro=0.15), dens=D)
    p.caja("Body/ropa", "top_medio", (-0.25, 23.0, -2.95), (0.25, 25.1, -2.85), color(NEGRO["s"]), dens=D)
    p.caja("Body/ropa", "faja", (-2.45, 20.4, -1.5), (2.45, 21.6, 1.5), tejido, dens=D)
    p.caja("Body/ropa", "flecos", (-3.85, L - 1.8, -2.15), (3.85, L + 1.6, 2.15), flecos, dens=D)
    p.caja("Body/ropa", "cinto", (-3.8, L + 1.4, -2.1), (3.8, L + 2.1, 2.1), voxel(NEGRO, claro=0.1), dens=D)

    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.0, s * 5.0))
        p.caja(f"{hueso}/brazo", "brazo", (x1, L - 1.0, -1.1), (x2, C - 0.4, 1.1), pintura, dens=D)
        v1, v2 = sorted((s * 2.9, s * 5.1))
        p.caja(f"{hueso}/ropa", "venda", (v1, L + 0.6, -1.2), (v2, L + 4.6, 1.2), venda, dens=D)
        p.caja(f"{hueso}/ropa", "guante", (v1, L - 1.1, -1.2), (v2, L + 0.6, 1.2), voxel(NEGRO, claro=0.1), dens=D)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        m1, m2 = sorted((s * 0.0, s * 3.5))                # muslo ancho que se afina a la pantorrilla
        x1, x2 = sorted((s * 0.3, s * 2.9))
        p.caja(f"{hueso}/pierna", "muslo", (m1, 9.0, -1.8), (m2, L, 1.8), pintura, dens=D)
        p.caja(f"{hueso}/pierna", "pantorrilla", (x1, 1.0, -1.4), (x2, 9.0, 1.4), pintura, dens=D)
        p.caja(f"{hueso}/pierna", "pie", (x1, 0.0, -2.0), (x2, 1.0, 1.4), PIEL_TEX, dens=D)
        p.caja(f"{hueso}/ropa", "tobillo", (x1 - 0.1, 1.0, -1.5), (x2 + 0.1, 3.2, 1.5), venda, dens=D)
        if s > 0:                                          # falda larga de este lado; del otro, la abertura
            p.caja(f"{hueso}/ropa", "falda", (m1 - 0.2, 3.6, -2.0), (m2 + 0.2, L, 2.0), voxel(NEGRO, claro=0.1), dens=D)
        else:
            p.caja(f"{hueso}/ropa", "falda_atras", (m1 - 0.2, 3.6, 0.3), (m2 + 0.2, L, 2.0), voxel(NEGRO, claro=0.1),
                   dens=D)
            p.caja(f"{hueso}/ropa", "liga", (m1 - 0.12, 11.6, -1.92), (m2 + 0.12, 12.6, 1.92), voxel(NEGRO), dens=D)

    # pelaje de plumas en el hombro izquierdo
    for k in range(9):
        a = math.radians(k * 40)
        cx, cy, cz = -4.2 + 1.3 * math.cos(a), C - 1.2 + 0.7 * math.sin(a), 1.2 * math.sin(a + 0.7)
        l = 1.5 + 0.3 * (k % 3)
        p.caja("LeftArm/ropa", f"pelaje{k}", (cx - l / 2, cy - l / 2, cz - l / 2), (cx + l / 2, cy + l / 2, cz + l / 2),
               voxel(PLUMA_NEGRA if k % 3 else GRIS, claro=0.1), rot=((k * 31) % 50 - 25, (k * 17) % 50 - 25, (k * 23) % 50 - 25),
               dens=D)

    baculo(p, L)
    return p
