"""
Crackatos, el primer jefe, como MOB: el mismo modelo que jefe_piedra (su avatar) rehecho SOLO CON CUBOS (GeckoLib no
lee mallas) y con un esqueleto de huesos anidados para animarlo.
  Las puas en punta pasan a 3 o 4 cubos apilados que se angostan a lo largo de su eje (con el mismo giro); el cuerpo
  redondeado (cortes de ocho lados) a tres cubos encimados por tramo que dibujan el octagono; los cuernos y las cejas
  a un cubo girado por tramo; el hocico a tres cubos. Las rocas, las patas, los pies y los ojos ya eran cubos.
Esqueleto (cada nombre es un hueso de GeckoLib; el pivote es donde gira):
  cuerpo (en la cadera de atras: ahi gira al pararse en dos patas)
    pecho (la cintura) - cuello - cabeza - cuerno_d / cuerno_i;  puas_pecho;  hombro_dd - codo_dd - mano_dd (y _di)
    cadera (la cintura) - cola1 - cola2 - cola3 - cola4 - cola5;  puas_cadera;  muslo_td - rodilla_td - pie_td (y _ti)
La luz horneada va por grupo (luz_por = "grupo"): un hueso no le pinta sombra a otro que se mueve aparte.
Medidas en px como jefe_piedra (unos 7 bloques de largo); en el juego el render lo crece.
"""

import math

from ..kit import Personaje
from ..luz import LUZ_SIMETRICA
from ..textura import hex_a_rgba as hex_
from .bloques import voxel
from .jefe_piedra import (CABEZA, COLA, CUERPO, FORMAS, GARRA, HOCICO, OJO, OJO_CENTRO, PIEDRA, PIEDRA_C, _azar,
                          _norm, bloque, en_superficie, hacia, octagono, piedra, rocas_caja, tramo_de_piedra)

D = 2

# los huesos: ruta -> pivote
PECHO, CADERA = "cuerpo/pecho", "cuerpo/cadera"
CUELLO_B = PECHO + "/cuello"
CABEZA_B = CUELLO_B + "/cabeza"
PUAS_P, PUAS_C = PECHO + "/puas_pecho", CADERA + "/puas_cadera"
COLAS = [CADERA + "/cola1"]
for _k in range(2, 6):
    COLAS.append(COLAS[-1] + f"/cola{_k}")
CORTE = 0.0                                   # donde se parte el cuerpo en pecho (adelante) y cadera (atras)
# las patas: (hueso de cada tramo, pivote) de la de su derecha; la izquierda es el espejo
PATA_D = (("hombro_dd", (12.0, 27.0, -11.0)), ("codo_dd", (23.5, 17.5, -9.5)), ("mano_dd", (21.0, 4.8, -12.5)))
PATA_T = (("muslo_td", (10.5, 25.0, 14.0)), ("rodilla_td", (18.5, 15.0, 10.5)), ("pie_td", (17.0, 4.4, 15.5)))


def _ruta_pata(base, pata, s, hasta):
    """La ruta del hueso 'hasta' (0, 1 o 2) de una pata (base: pecho o cadera; s: lado)."""
    partes = [n if s > 0 else n[:-1] + "i" for n, _ in pata[:hasta + 1]]
    return base + "/" + "/".join(partes)


def huesos():
    """Todas las rutas de huesos con su pivote."""
    out = {"cuerpo": (0.0, 25.0, 12.0), PECHO: (0.0, 27.0, CORTE), CADERA: (0.0, 27.0, CORTE),
           CUELLO_B: (0.0, 27.0, -20.0), CABEZA_B: (0.0, 21.5, -30.0), PUAS_P: (0.0, 30.0, -10.0),
           PUAS_C: (0.0, 30.0, 8.0), CABEZA_B + "/cuerno_d": (7.0, 23.5, -33.0),
           CABEZA_B + "/cuerno_i": (-7.0, 23.5, -33.0)}
    for ruta, (z, y, *_r) in zip(COLAS, COLA):
        out[ruta] = (0.0, y, z)
    for base, pata in ((PECHO, PATA_D), (CADERA, PATA_T)):
        for s in (1, -1):
            for i, (_, piv) in enumerate(pata):
                out[_ruta_pata(base, pata, s, i)] = (s * piv[0], piv[1], piv[2])
    return out


# ---------------------------------------------------------------- las piezas en cubos

def cristal_cubos():
    """Los cristales en cubos: facetados como los de malla pero sin el tono casi blanco ni el grano (en las caras
    cuadradas de los cubos se veian como cuadritos claros con puntos)."""
    from .jefe_piedra import AMATISTA
    from .moles import faceta
    return faceta(paleta=((0.40, AMATISTA["s"]), (0.56, AMATISTA["b"]), (9.0, AMATISTA["l"])), grano=0,
                  simetrico=True)


def _eje(rot):
    """Hacia donde apunta +Y despues del giro (rx, ry, rz) de Blockbench (Z * Y * X)."""
    from ..luz import rot_matriz
    R = rot_matriz(*rot)
    return (R[0][1], R[1][1], R[2][1])


def tapas_sin_brillo(pintor, eje, rampa):
    """Las caras de una pua en cubos que miran a lo largo de su eje (los escalones entre cubo y cubo y la punta) van
    del tono base de la pua, no del claro de lo que mira arriba: asi no se ven anillos claros, se ve una pua."""
    base, sombra = hex_(rampa["b"]), hex_(rampa["s"])

    def p(t):
        d = sum(t.n[i] * eje[i] for i in range(3))
        if d > 0.6:
            return base
        if d < -0.6:
            return sombra
        return pintor(t)
    return p


def esquirla_cubos(p, grupo, nombre, base, ancho, alto, rot, forma, pintor, rampa=None):
    """Una pua en cubos: un cubo por tramo entre los cortes de su forma (ver FORMAS) y la punta en dos cubos cada vez
    mas delgados (la ultima casi una aguja); todos girados igual desde la base (como la pua de malla). Los escalones
    no brillan (ver tapas_sin_brillo)."""
    from .jefe_piedra import AMATISTA
    niveles = list(FORMAS[forma])
    cajas = []
    for (f0, x0, z0), (f1, x1, z1) in zip(niveles, niveles[1:]):
        cajas.append((f0, f1, (x0 + x1) / 2, (z0 + z1) / 2))
    f0, x0, z0 = niveles[-1]
    fm = f0 + (1.0 - f0) * 0.45
    cajas += [(f0, fm, x0 * 0.62, z0 * 0.62), (fm - 0.04, 1.0, x0 * 0.24, z0 * 0.24)]
    k = 0.7071 * ancho / 2                     # el corte en rombo de la malla es un cuadrado de este medio lado
    x, y, z = base
    pint = tapas_sin_brillo(pintor, _eje(rot), rampa or AMATISTA)
    for i, (a, b, fx, fz) in enumerate(cajas):
        p.caja(grupo, f"{nombre}_{i}", (x - k * fx, y + a * alto, z - k * fz), (x + k * fx, y + b * alto, z + k * fz),
               pint, rot=rot, piv=base, dens=D)


def barra(p, grupo, nombre, a, b, r0, r1, pintor):
    """Un tramo de cuerno o de ceja: un cubo girado de a a b (un poco mas largo, para que se peguen los tramos)."""
    d = tuple(b[i] - a[i] for i in range(3))
    largo = math.sqrt(sum(c * c for c in d))
    ey = _norm(d)
    ref = (0.0, 0.0, 1.0) if abs(ey[2]) < 0.9 else (1.0, 0.0, 0.0)
    ex = _norm((ey[1] * ref[2] - ey[2] * ref[1], ey[2] * ref[0] - ey[0] * ref[2], ey[0] * ref[1] - ey[1] * ref[0]))
    r = (r0 + r1) / 2
    centro = tuple((a[i] + b[i]) / 2 for i in range(3))
    bloque(p, grupo, nombre, centro, (r * 1.7, largo + r * 0.6, r * 1.7), ex, ey, pintor)


def tramo_octagonal(p, grupo, nombre, a, b, pintor, partes=2):
    """Un tramo del cuerpo (de un corte octagonal a otro) en cubos: en cada parte tres cubos encimados (uno ancho y
    plano, uno alto y angosto y uno en medio) que juntos dibujan el octagono; abajo mas plano, como el corte."""
    (za, *ca), (zb, *cb) = a, b
    for j in range(partes):
        f0, f1 = j / partes, (j + 1) / partes
        fm = (f0 + f1) / 2
        yc, mx, my = (u + (v - u) * fm for u, v in zip(ca, cb))
        z0, z1 = za + (zb - za) * f0, za + (zb - za) * f1
        for i, (fx, fy) in enumerate(((0.924, 0.383), (0.383, 0.924), (0.66, 0.66))):
            p.caja(grupo, f"{nombre}{j}_{i}", (-mx * fx, yc - my * fy * 0.7, min(z0, z1)),
                   (mx * fx, yc + my * fy, max(z0, z1)), pintor, dens=D)


def rocas_tramos(p, nombre, tabla, grupo_de, tam, pintores, semilla):
    """La piel rocosa (bloques encimados en tresbolillo sobre cada cara de cada tramo octagonal), cada tramo en su
    hueso (grupo_de: z del tramo -> ruta)."""
    from .jefe_piedra import rocas
    anillos = [octagono(z, y, mx, my) for z, y, mx, my in tabla]
    for j in range(len(anillos) - 1):
        zc = (tabla[j][0] + tabla[j + 1][0]) / 2
        rocas(p, grupo_de(zc), f"{nombre}{j}_", anillos[j:j + 2], tam, pintores, semilla + j * 31)


def picos_cubos(p, tabla, nombre, n, zona, alto, ancho, atras, semilla, grupo_de, formas=tuple(FORMAS)):
    """Las puas repartidas en espiral como en jefe_piedra (mismo azar, misma forma, tamano y giro), en cubos; cada
    una en el hueso que le toca por donde nace (grupo_de: z -> ruta)."""
    amatista = cristal_cubos()
    z0, z1, fi_max, fi_min = zona if len(zona) == 4 else (*zona, 0.0)
    k = 0
    for i in range(n):
        sem = semilla + i * 5.3
        z = z0 + (z1 - z0) * (i + 0.5 + 0.6 * (_azar(sem) - 0.5)) / n
        fi = (1 if i % 2 else -1) * (fi_min + ((i * 0.6180339) % 1.0) * (fi_max - fi_min)) if fi_min else \
            (((i * 0.6180339) % 1.0) * 2 - 1) * fi_max
        base, fuera = en_superficie(tabla, z, fi)
        tam = 0.55 + 0.9 * _azar(sem + 1)
        forma = formas[int(_azar(sem + 2) * len(formas))]
        h = alto(z, fi) * tam * (0.75 if forma in ("gruesa", "pilar") else 1.0)
        w = ancho * (0.7 + 0.6 * _azar(sem + 3)) * (1.5 if forma in ("gruesa", "pilar") else 1.0)
        d = (fuera[0], fuera[1], atras + 0.5 * (_azar(sem + 4) - 0.5))
        rx, ry, rz = hacia(d)
        g = grupo_de(z)
        esquirla_cubos(p, g, f"{nombre}{k}", base, w, h, (rx, 90 * _azar(sem + 5), rz), forma, amatista)
        k += 1
        if _azar(sem + 6) > 0.62:                              # racimo: una o dos chicas al lado
            for j in range(1 + int(_azar(sem + 7) > 0.5)):
                lado = 1 if j == 0 else -1
                d2 = (d[0] + lado * 0.45 * fuera[1], d[1] - lado * 0.45 * fuera[0], d[2] + 0.2)
                b2 = (base[0] + lado * 0.6 * w * fuera[1], base[1] - lado * 0.6 * w * fuera[0], base[2] + 0.4 * w)
                esquirla_cubos(p, g, f"{nombre}{k}", b2, w * 0.6, h * (0.4 + 0.2 * j), hacia(d2), "aguja", amatista)
                k += 1


# ---------------------------------------------------------------- el cuerpo, la cabeza y las patas

def _cola_de(z):
    for ruta, (z0, *_), (z1, *_r) in zip(COLAS, COLA, COLA[1:]):
        if z < z1:
            return ruta
    return COLAS[-1]


def cuerpo(p):
    piedra_o, clara = piedra(PIEDRA), piedra(PIEDRA_C)
    for j, (a, b) in enumerate(zip(CUERPO, CUERPO[1:])):
        tramo_octagonal(p, PECHO if (a[0] + b[0]) / 2 < CORTE else CADERA, f"cuerpo{j}_", a, b, piedra_o)
    for j, (a, b) in enumerate(zip(COLA, COLA[1:])):
        tramo_octagonal(p, _cola_de((a[0] + b[0]) / 2), f"cola{j}_", a, b, piedra_o, partes=1)
    rocas_tramos(p, "roca", CUERPO, lambda z: PECHO if z < CORTE else CADERA, (3.8, 1.6), [clara, piedra_o], 7)
    rocas_tramos(p, "roca_cola", COLA[:7], _cola_de, (2.8, 1.1), [clara, piedra_o], 40)

    def alto(z, fi):
        return (19.0 - abs(z + 9.0) * 0.38) * (1.0 - abs(fi) / 160.0)
    puas = lambda z: PUAS_P if z < CORTE else PUAS_C                     # noqa: E731
    picos_cubos(p, CUERPO, "pico", 120, (-21.0, 20.0, 105), alto, 4.4, 0.55, 1, puas)
    picos_cubos(p, COLA, "pico_cola", 48, (22.0, 66.0, 70),
                lambda z, fi: max(1.6, 8.5 - (z - 21.0) * 0.15) * (1.0 - abs(fi) / 140.0), 3.0, 0.9, 50, _cola_de)
    picos_cubos(p, CUERPO, "cristal_costado", 36, (-20.0, 19.0, 135, 100), lambda z, fi: 6.5, 3.4, 0.4, 70, puas,
                ("gruesa", "cristal", "pilar"))
    for k in range(11):                                       # las piedras cuadradas de los costados
        z, fi = -19.0 + 3.6 * k, (1 if k % 2 else -1) * (112 + 18 * _azar(k * 3.3))
        sem = 90 + k * 3.7
        base, fuera = en_superficie(CUERPO, z, fi, 0.98)
        w, h, d = (4.8 * (0.7 + 0.5 * _azar(sem + i)) for i in range(3))
        a = math.radians(fi)
        bloque(p, PECHO if z < CORTE else CADERA, f"piedra{k}", base, (w, h, d), (math.cos(a), -math.sin(a), 0.0),
               fuera, [clara, piedra_o][k % 2])
    for i, (x, y, d) in enumerate(((0.0, 24.0, (0.0, -0.3, -1.0)), (4.5, 21.5, (0.35, -0.4, -1.0)),
                                   (-4.5, 21.5, (-0.35, -0.4, -1.0)), (6.5, 27.5, (0.5, 0.2, -1.0)),
                                   (-6.5, 27.5, (-0.5, 0.2, -1.0)))):
        esquirla_cubos(p, PUAS_P, f"cristal_pecho{i}", (x, y, -21.5), 3.2, 5.5 - (i % 2), hacia(d),
                       ("gruesa", "cristal")[i % 2], cristal_cubos())


def cabeza(p):
    piedra_o, clara, hocico, amatista = piedra(PIEDRA), piedra(PIEDRA_C), voxel(HOCICO, 0.1), cristal_cubos()
    tramo_de_piedra(p, CUELLO_B, "cuello", (0.0, 27.5, -20.0), (0.0, 21.5, -30.0), (11.0, 9.5, 3.4), (8.6, 7.4, 3.0),
                    ("east", "west", "up"), [piedra_o, clara], 11)
    g = CABEZA_B
    for j, (a, b) in enumerate(zip(CABEZA, CABEZA[1:])):
        tramo_octagonal(p, g, f"craneo{j}_", a, b, clara)
    from .jefe_piedra import rocas
    rocas(p, g, "roca_craneo", [octagono(z, y, mx, my) for z, y, mx, my in CABEZA[:2]], (3.0, 1.2), [piedra_o, clara], 21)
    # el hocico de piedra palida pegado abajo de la cara, con su quilla
    p.caja(g, "hocico0", (-4.6, 16.0, -40.4), (4.6, 18.8, -37.4), hocico, dens=D)
    p.caja(g, "hocico1", (-3.4, 14.0, -40.2), (3.4, 16.2, -37.4), hocico, dens=D)
    p.caja(g, "quilla", (-0.9, 13.6, -41.4), (0.9, 18.6, -39.8), hocico, dens=D)
    for s in (1, -1):                                         # las cejas salidas
        barra(p, g, f"ceja{s}", (s * 0.8, 21.6, -38.4), (s * 6.4, 22.8, -36.4), 1.1, 0.9, clara)
    for s in (1, -1):                                         # los ojos que brillan
        a, b = sorted((s * 1.8, s * 4.3))
        p.caja(g, f"ojo{s}", (a, 19.5, -38.1), (b, 20.8, -37.95), lambda t: hex_(OJO), dens=4, luz=False)
        a, b = sorted((s * 2.6, s * 3.4))
        p.caja(g, f"brillo{s}", (a, 19.85, -38.2), (b, 20.45, -38.05), lambda t: hex_(OJO_CENTRO), dens=4, luz=False)
    camino = ((7.0, 23.5, -33.0, 3.1), (12.5, 26.3, -32.0, 2.6), (17.0, 29.0, -32.5, 1.9), (19.4, 31.2, -35.0, 1.3),
              (20.1, 32.4, -38.0, 0.6), (19.8, 33.0, -40.5, 0.1))
    for s, lado in ((1, "d"), (-1, "i")):
        for i, (a, b) in enumerate(zip(camino, camino[1:])):
            barra(p, f"{g}/cuerno_{lado}", f"cuerno{i}", (s * a[0], a[1], a[2]), (s * b[0], b[1], b[2]), a[3],
                  max(b[3], 0.35), amatista)


def pata(p, base, plantilla, s, radios, pie, garras):
    """Una pata de piedra como en jefe_piedra: cada tramo de bloques encimados en su hueso (hombro, codo...), la roca
    con rocas y cristales de cada articulacion en el hueso que gira ahi, y el pie con las garras en el ultimo."""
    piedra_o, clara, garra = piedra(PIEDRA), piedra(PIEDRA_C), voxel(GARRA, 0.1)
    afuera = "east" if s > 0 else "west"
    puntos = [(s * x, y, z) for _, (x, y, z) in plantilla]
    rutas = [_ruta_pata(base, plantilla, s, i) for i in range(3)]
    for i, (a, b) in enumerate(zip(puntos, puntos[1:])):
        ra, rb = radios[i], radios[i + 1]
        tramo_de_piedra(p, rutas[i], "tramo", a, b, (ra, ra * 0.9, ra), (rb, rb * 0.9, rb), (afuera, "north", "south"),
                        [piedra_o, clara] if i % 2 == 0 else [clara, piedra_o], 200 + 13 * i + s)
    for i, c in enumerate(puntos[:-1]):
        t = radios[i] * 1.3
        d, h = (c[0] - t, c[1] - t * 0.8, c[2] - t), (c[0] + t, c[1] + t * 0.8, c[2] + t)
        p.caja(rutas[i], "articulacion", d, h, clara if i % 2 == 0 else piedra_o, dens=D)
        for cara in (afuera, "north", "south", "up"):
            rocas_caja(p, rutas[i], f"roca_articulacion_{cara}_", d, h, cara, (3, 3), (3.6, 1.6), [piedra_o, clara],
                       300 + i * 7 + s + len(cara))
        for k, (dy, dz) in enumerate(((0.45, -0.35), (0.6, 0.4), (0.1, 0.05))):
            b0 = ((h[0] if s > 0 else d[0]) - s * 0.6, c[1] + dy * t * 0.8, c[2] + dz * t)
            esquirla_cubos(p, rutas[i], f"cristal_articulacion{k}", b0, 2.6 - 0.5 * k, 6.0 - 1.2 * k,
                           hacia((s * 1.0, 0.7 + 0.2 * k, 0.3 * dz)), ("cristal", "gruesa", "aguja")[k], cristal_cubos())
    (x, y, z0, z1, r) = pie
    a, b = sorted((s * (x - r * 1.15), s * (x + r * 1.15)))
    p.caja(rutas[2], "pie", (a, 0.0, min(z0, z1)), (b, y + r * 0.5, max(z0, z1)), clara, dens=D)
    a, b = sorted((s * (x - r * 0.9), s * (x + r * 0.9)))
    p.caja(rutas[2], "empeine", (a, y + r * 0.4, min(z0, z1) + 1.0), (b, y + r * 1.1, max(z0, z1) - 1.5), piedra_o, dens=D)
    for k, dx in enumerate(garras):
        esquirla_cubos(p, rutas[2], f"garra{k}", (s * (x + dx), 1.0, z1 + 0.6), 1.5, 3.0, hacia((0.0, -0.45, -1.0)),
                       "aguja", garra, GARRA)


def patas(p):
    for s in (1, -1):
        pata(p, PECHO, PATA_D, s, (7.4, 6.0, 4.6), (21.0, 2.8, -8.5, -19.0, 4.0), (-2.4, 0.0, 2.4))
        pata(p, CADERA, PATA_T, s, (6.6, 5.3, 4.1), (17.0, 2.6, 19.5, 9.0, 3.6), (-1.8, 1.8))


def construir():
    p = Personaje("crackatos", altura=32)
    p.m.luz_desde = LUZ_SIMETRICA
    p.m.luz_por = "grupo"
    cuerpo(p)
    cabeza(p)
    patas(p)
    p.m.pivotes = huesos()
    return p
