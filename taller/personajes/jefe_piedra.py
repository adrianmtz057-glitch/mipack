"""
El primer jefe (inspirado en Azdaha): una bestia de piedra oscura en cuatro patas, gorda y con la espalda llena de
puas de amatista. Armado CHICO y bien proporcionado: despues se crece entero (escalar) hasta el tamano del Ender
Dragon.
  CABEZA baja y hacia adelante: el craneo poligonal, el hocico de piedra palida pegado abajo de la cara (con su
    quilla), dos ojos morados que brillan, las cejas salidas y solo los CUERNOS, que salen a los lados y curvean
    hacia adelante; el CUELLO y la nuca gordos de bloques de piedra encimados
  CUERPO alto y gordo (cortes de ocho lados) con la joroba de los hombros, todo cubierto de piedra: bloques encimados
    en tresbolillo, piedras cuadradas y cristales en los costados y el pecho
  PATAS de piedra (bloques derechos encimados) con hombro, codo y muneca, una roca grande con rocas y cristales en
    cada articulacion, pies de dos bloques y garras; lo levantan del piso
  PUAS repartidas en espiral (no en filas), cada una hacia afuera de donde nace y echada atras, de cinco formas
    (aguja, gruesa, hoja, pilar, cristal), tamanos distintos y algunas en racimo; siguen por la COLA larga y baja
Texturas: piedra de bloques de 1 px con grietas y motitas; cristales facetados. Luz horneada pareja (simetrica).
Medidas en px (16 por bloque); el frente es -Z, su derecha es +X. Mide unos 7 bloques de largo con la cola.
"""

import math

from .. import malla as geo
from ..kit import Personaje
from ..luz import LUZ_SIMETRICA
from ..textura import hex_a_rgba as hex_
from .bloques import voxel

D = 2                                   # texeles por px (es grande: con 2 alcanza)

PIEDRA = {"s": "#17121F", "b": "#231A31", "l": "#322645"}          # la piedra oscura del cuerpo
PIEDRA_C = {"s": "#2C2140", "b": "#3B2C56", "l": "#4E3B70"}        # las placas mas claras (lomo, patas)
AMATISTA = {"s": "#46296F", "b": "#6340A0", "l": "#8A64CC"}        # los picos
HOCICO = {"s": "#55516A", "b": "#736F8C", "l": "#9692AE"}          # el hocico de piedra palida
GARRA = {"s": "#2A2638", "b": "#3C374E", "l": "#555070"}
OJO, OJO_CENTRO = "#B26BFF", "#F4DEFF"


# las formas de las puas: cortes (a que fraccion del alto, cuanto del ancho en x, cuanto en z) y luego la punta
FORMAS = {"aguja": ((0.0, 1.0, 1.0), (0.62, 0.36, 0.36)),
          "gruesa": ((0.0, 1.0, 1.0), (0.42, 0.78, 0.78)),
          "hoja": ((0.0, 1.0, 0.36), (0.6, 0.62, 0.24)),
          "pilar": ((0.0, 1.0, 1.0), (0.8, 0.82, 0.82)),
          "cristal": ((0.0, 0.8, 0.8), (0.32, 1.0, 1.0), (0.72, 0.55, 0.55))}


def piedra(rampa, claro=0.05):
    """Textura de piedra: los bloques de 1 px (voxel) con grietas finas mas oscuras y motitas claras."""
    base, grieta, mota = voxel(rampa, claro), hex_(rampa["s"]), hex_(rampa["l"])

    def p(t):
        u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
        v = t.z if abs(t.n[1]) > 0.7 else t.y
        cu, cv = math.floor(u * D), math.floor(v * D)
        r = _azar(cu * 3.1 + cv * 7.7 + round(t.n[0] * 3) * 13 + round(t.n[2] * 3) * 29)
        if abs(math.sin(u * 0.9 + v * 0.45) * 3.0 + math.cos(v * 0.7 - u * 0.3) * 2.0) < 0.22:
            return grieta
        if r > 0.95:
            return mota
        return base(t)
    return p


def cristal():
    """Los cristales de amatista: cada cara de un tono segun hacia donde mira (facetas), con grano suave."""
    from .moles import faceta
    return faceta(paleta=((0.36, AMATISTA["s"]), (0.52, AMATISTA["b"]), (0.68, AMATISTA["l"]), (9.0, "#B79BEA")),
                  grano=0.06, simetrico=True)


def esquirla(base, ancho, alto, rot=(0, 0, 0), forma="aguja"):
    """Una pua de piedra parada en 'base' y girada (rx, ry, rz) desde su base: sus cortes cuadrados (ver FORMAS) que
    se angostan y la punta."""
    x, y, z = base
    cortes = [geo.anillo(x, y + f * alto, z, ancho / 2 * fx, ancho / 2 * fz, 4, 45) for f, fx, fz in FORMAS[forma]]
    partes = [geo.tronco(a, b, tapa_abajo=(i == 0), tapa_arriba=False) for i, (a, b) in enumerate(zip(cortes, cortes[1:]))]
    m = geo.unir(*partes, geo.piramide(cortes[-1], (x, y + alto, z), tapa=False))
    return geo.girar(m, rot, base)


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _norm(v):
    largo = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / largo for c in v)


def hacia(d):
    """El giro (rx, 0, rz) que lleva +Y (hacia donde apunta una esquirla) a la direccion d."""
    dx, dy, dz = _norm(d)
    return (math.degrees(math.asin(max(-1.0, min(1.0, dz)))), 0, math.degrees(math.atan2(-dx, dy)))


def octagono(z, yc, mx, my, plano=0.7):
    """Corte de ocho lados del cuerpo a lo largo de z (de frente a atras): medio ancho mx, medio alto my; abajo un
    poco mas plano (la panza)."""
    out = []
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        y = math.cos(a) * my
        out.append((math.sin(a) * mx, yc + (y if y > 0 else y * plano), z))
    return out


def loft_z(anillos, tapas=True, abanico=False):
    """Malla que une cortes (listas de puntos en el mismo orden) uno tras otro, con tapas; las caras miran afuera.
    abanico: las tapas en triangulos desde su centro (para cortes que no son planos)."""
    vs, cs = [], []
    n = len(anillos[0])
    for a in anillos:
        vs.extend(a)
    centros = [tuple(sum(p[i] for p in a) / n for i in range(3)) for a in anillos]
    for j in range(len(anillos) - 1):
        for k in range(n):
            q = (j * n + k, j * n + (k + 1) % n, (j + 1) * n + (k + 1) % n, (j + 1) * n + k)
            pc = tuple(sum(vs[i][c] for i in q) / 4 for c in range(3))
            mc = tuple((centros[j][c] + centros[j + 1][c]) / 2 for c in range(3))
            if sum(geo.normal([vs[i] for i in q])[c] * (pc[c] - mc[c]) for c in range(3)) < 0:
                q = q[::-1]
            cs.append(q)
    if tapas:
        for j, otro in ((0, 1), (len(anillos) - 1, len(anillos) - 2)):
            t = [j * n + k for k in range(n)]
            if abanico:
                vs.append(centros[j])
                caras = [(len(vs) - 1, t[k], t[(k + 1) % n]) for k in range(n)]
            else:
                caras = [tuple(t)]
            for cara in caras:
                if sum(geo.normal([vs[i] for i in cara])[c] * (centros[j][c] - centros[otro][c]) for c in range(3)) < 0:
                    cara = cara[::-1]
                cs.append(tuple(cara))
    return vs, cs


# el cuerpo, alto (las patas lo levantan): cortes (z, y del centro, medio ancho, medio alto); la joroba en los hombros
CUERPO = ((-22.0, 26.0, 11.0, 9.0), (-15.0, 28.0, 14.5, 12.0), (-8.0, 28.5, 15.0, 12.5), (0.0, 27.0, 14.0, 11.5),
          (8.0, 26.0, 13.0, 10.5), (15.0, 25.0, 11.5, 9.5), (21.0, 23.5, 8.5, 7.5))
# la cola, baja y larga, casi arrastrando
COLA = ((21.0, 23.5, 8.5, 7.5), (28.0, 18.0, 6.6, 5.4), (36.0, 11.5, 4.2, 3.4), (44.0, 7.0, 3.3, 2.7),
        (52.0, 4.2, 2.5, 2.1), (60.0, 2.6, 1.7, 1.5), (67.0, 1.8, 1.0, 1.0), (72.0, 1.4, 0.3, 0.3))
# el cuello y la cabeza (baja, hacia adelante)
CUELLO = ((-21.0, 27.0, 11.5, 10.0), (-26.0, 24.0, 10.5, 9.0), (-30.5, 21.5, 9.2, 8.2))
CABEZA = ((-30.5, 21.5, 9.4, 8.2), (-34.5, 20.0, 8.0, 6.8), (-38.0, 18.0, 6.4, 5.6))


def corte_en(tabla, z):
    """(y del centro, medio ancho, medio alto) del cuerpo o la cola en z (interpolado)."""
    for (z0, *a), (z1, *b) in zip(tabla, tabla[1:]):
        if z0 <= z <= z1:
            f = (z - z0) / (z1 - z0)
            return tuple(x + (y - x) * f for x, y in zip(a, b))
    return None


def en_superficie(tabla, z, fi, hundido=0.9):
    """Punto de la superficie (un poco adentro) y la direccion hacia afuera, a la altura z y al angulo fi (0 arriba,
    90 a su derecha)."""
    yc, mx, my = corte_en(tabla, z)
    a = math.radians(fi)
    return (math.sin(a) * mx * hundido, yc + math.cos(a) * my * hundido, z), (math.sin(a), math.cos(a), 0.0)


def picos(p, grupo, tabla, nombre, n, zona, alto, ancho, atras, semilla, formas=tuple(FORMAS)):
    """n puas repartidas parejo (en espiral, no en filas) por la zona (z de, z a, angulo maximo desde arriba y, si
    va, el minimo) del lomo: cada una sale hacia afuera de donde nace, echada un poco atras y distinta (forma,
    tamano, giro); algunas con una o dos chicas a su lado (racimo)."""
    amatista = cristal()
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
        p.malla(grupo, f"{nombre}{k}", esquirla(base, w, h, (rx, 90 * _azar(sem + 5), rz), forma), amatista, dens=D)
        k += 1
        if _azar(sem + 6) > 0.62:                              # racimo: una o dos chicas al lado
            for j in range(1 + int(_azar(sem + 7) > 0.5)):
                lado = 1 if j == 0 else -1
                d2 = (d[0] + lado * 0.45 * fuera[1], d[1] - lado * 0.45 * fuera[0], d[2] + 0.2)
                b2 = (base[0] + lado * 0.6 * w * fuera[1], base[1] - lado * 0.6 * w * fuera[0], base[2] + 0.4 * w)
                p.malla(grupo, f"{nombre}{k}", esquirla(b2, w * 0.6, h * (0.4 + 0.2 * j), hacia(d2), "aguja"), amatista,
                        dens=D)
                k += 1


def bloque(p, grupo, nombre, centro, tam, ex, ey, pintor):
    """Un bloque de tam (ancho, alto, hondo) centrado en 'centro', con su ancho a lo largo de ex y su alto a lo largo
    de ey (el giro de Blockbench, Z * Y * X, sale de esos ejes)."""
    ez = (ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0])
    rx = math.degrees(math.atan2(ey[2], ez[2]))
    ry = math.degrees(-math.asin(max(-1.0, min(1.0, ex[2]))))
    rz = math.degrees(math.atan2(ex[1], ex[0]))
    w, h, d = (c / 2 for c in tam)
    x, y, z = centro
    p.caja(grupo, nombre, (x - w, y - h, z - d), (x + w, y + h, z + d), pintor, rot=(rx, ry, rz), piv=centro, dens=D)


def rocas(p, grupo, nombre, anillos, tam, pintores, semilla, desde=0):
    """La piel rocosa: en cada cara entre dos cortes, una reja de bloques derechos pegados a la cara (todos miran
    hacia afuera de su cara), de tamanos parejos con un poco de diferencia y hundidos a medias, encimados en
    tresbolillo. tam = (lo ancho de cada bloque, lo que sale)."""
    k = 0
    n = len(anillos[0])
    for j in range(desde, len(anillos) - 1):
        a, b = anillos[j], anillos[j + 1]
        centro_eje = tuple((sum(q[c] for q in a) + sum(q[c] for q in b)) / (2 * n) for c in range(3))
        for i in range(n):
            p0, p1, p2, p3 = a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]
            u = _norm(tuple(p1[c] - p0[c] + p2[c] - p3[c] for c in range(3)))
            v = tuple(p3[c] - p0[c] + p2[c] - p1[c] for c in range(3))
            nn = _norm((u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]))
            medio = tuple((p0[c] + p1[c] + p2[c] + p3[c]) / 4 for c in range(3))
            if sum(nn[c] * (medio[c] - centro_eje[c]) for c in range(3)) < 0:
                nn = tuple(-c for c in nn)
            v = _norm(tuple(v[c] - nn[c] * sum(v[e] * nn[e] for e in range(3)) for c in range(3)))
            ancho = math.dist(p0, p1) * 0.5 + math.dist(p3, p2) * 0.5
            largo = math.dist(p0, p3) * 0.5 + math.dist(p1, p2) * 0.5
            nu, nv = max(1, round(ancho / tam[0])), max(1, round(largo / tam[0]))
            for iu in range(nu):
                for iv in range(nv):
                    sem = semilla + k * 7.7
                    fu = (iu + 0.5 + (0.25 if iv % 2 else -0.25) + 0.25 * (_azar(sem) - 0.5)) / nu - 0.5
                    fv = (iv + 0.5 + 0.25 * (_azar(sem + 1) - 0.5)) / nv - 0.5
                    w = ancho / nu * (0.75 + 0.45 * _azar(sem + 2))
                    d = largo / nv * (0.75 + 0.45 * _azar(sem + 3))
                    h = tam[1] * (0.6 + 0.8 * _azar(sem + 4))
                    c = tuple(medio[e] + u[e] * fu * ancho * 0.9 + v[e] * fv * largo * 0.9 + nn[e] * h * 0.05
                              for e in range(3))
                    bloque(p, grupo, f"{nombre}{k}", c, (w, h, d), u, nn, pintores[k % len(pintores)])
                    k += 1


def rocas_caja(p, grupo, nombre, desde, hasta, cara, n, tam, pintores, semilla, margen=0.5):
    """Rocas sobre una cara de una caja derecha: una reja de n = (columnas, filas) bloques derechos (como la caja),
    de tamanos parejos con un poco de diferencia, hundidos a medias y en tresbolillo. tam = (ancho, lo que salen)."""
    eje = {"up": 1, "down": 1, "east": 0, "west": 0, "north": 2, "south": 2}[cara]
    signo = 1 if cara in ("up", "east", "south") else -1
    u, v = [i for i in range(3) if i != eje]
    k = 0
    for i in range(n[0]):
        for j in range(n[1]):
            sem = semilla + k * 7.7
            fu = (i + 0.5 + 0.35 * (_azar(sem) - 0.5) + (0.5 if j % 2 else 0.0)) / (n[0] + 0.5)
            fv = (j + 0.5 + 0.3 * (_azar(sem + 1) - 0.5)) / n[1]
            cu = desde[u] + margen + (hasta[u] - desde[u] - 2 * margen) * fu
            cv = desde[v] + margen + (hasta[v] - desde[v] - 2 * margen) * fv
            wu = min(tam[0], (hasta[u] - desde[u]) / n[0]) * (0.75 + 0.5 * _azar(sem + 2)) / 2
            wv = min(tam[0], (hasta[v] - desde[v]) / n[1]) * (0.75 + 0.5 * _azar(sem + 3)) / 2
            sale = tam[1] * (0.6 + 0.8 * _azar(sem + 4))
            c = hasta[eje] if signo > 0 else desde[eje]
            a, b = [0.0] * 3, [0.0] * 3
            a[u], b[u], a[v], b[v] = cu - wu, cu + wu, cv - wv, cv + wv
            a[eje], b[eje] = sorted((c - signo * sale * 0.45, c + signo * sale * 0.55))
            p.caja(grupo, f"{nombre}{k}", tuple(a), tuple(b), pintores[k % len(pintores)], dens=D)
            k += 1


def tramo_de_piedra(p, grupo, nombre, a, b, medio_a, medio_b, caras, pintores, semilla, n=None):
    """Un tramo de pata o de cuello hecho de bloques de piedra derechos encimados que van de a a b (cada uno un poco
    distinto, cada vez del medio tamano que toca), con rocas salidas en las caras dadas. medio = (x, y, z).
    n: cuantos bloques (si no se da, uno por cada vez su ancho)."""
    largo = math.dist(a, b)
    n = n or max(2, math.ceil(largo / (min(medio_a) * 1.1)))
    for i in range(n):
        f = i / (n - 1)
        sem = semilla + i * 4.1
        c = tuple(a[e] + (b[e] - a[e]) * f for e in range(3))
        m = tuple((medio_a[e] + (medio_b[e] - medio_a[e]) * f) * (0.88 + 0.24 * _azar(sem + e)) for e in range(3))
        d, h = tuple(c[e] - m[e] for e in range(3)), tuple(c[e] + m[e] for e in range(3))
        p.caja(grupo, f"{nombre}{i}", d, h, pintores[i % len(pintores)], dens=D)
        for cara in caras:
            ancho = (h[2] - d[2]) if cara in ("east", "west", "up") else (h[0] - d[0])
            alto = (h[1] - d[1]) if cara != "up" else (h[0] - d[0])
            rocas_caja(p, grupo, f"{nombre}{i}_{cara}_", d, h, cara, (max(1, round(ancho / 3.4)), max(1, round(alto / 3.4))),
                       (3.4, 1.5), pintores[::-1], sem + 50)


def anillos_tubo(a, b, r0, r1, lados=6):
    """Los dos cortes (de 'lados' lados) de un tramo de a a b, para la malla y para su piel rocosa."""
    t = _norm(tuple(b[i] - a[i] for i in range(3)))
    ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm((t[1] * ref[2] - t[2] * ref[1], t[2] * ref[0] - t[0] * ref[2], t[0] * ref[1] - t[1] * ref[0]))
    w = (t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0])
    out = []
    for c, r in ((a, r0), (b, r1)):
        out.append([tuple(c[i] + r * (math.cos(2 * math.pi * k / lados) * u[i] + math.sin(2 * math.pi * k / lados) * w[i])
                          for i in range(3)) for k in range(lados)])
    return out


def cabeza(p):
    piedra_o, clara, hocico, amatista = piedra(PIEDRA), piedra(PIEDRA_C), voxel(HOCICO, 0.1), cristal()
    g = "Head/cabeza"
    tramo_de_piedra(p, g, "cuello", (0.0, 27.5, -20.0), (0.0, 21.5, -30.0), (11.0, 9.5, 3.4), (8.6, 7.4, 3.0),
                    ("east", "west", "up"), [piedra_o, clara], 11)
    p.malla(g, "craneo", loft_z([octagono(z, y, mx, my) for z, y, mx, my in CABEZA]), clara, dens=D)
    rocas(p, g, "roca_craneo", [octagono(z, y, mx, my) for z, y, mx, my in CABEZA[:2]], (3.0, 1.2), [piedra_o, clara], 21)
    # el hocico (la boca): la parte de abajo de la cara, de piedra palida, bien pegada a la cabeza y saliendo hacia
    # adelante, con la quilla al centro
    from .bloques import tubo
    perfil = ((0.0, 18.8), (5.0, 18.4), (4.8, 16.0), (3.0, 14.2), (0.0, 13.6), (-3.0, 14.2), (-4.8, 16.0), (-5.0, 18.4))
    atras = [(x, y, -37.6) for x, y in perfil]
    adelante = [(x * 0.86, y, -40.6 - (0.8 if x == 0 else 0.0)) for x, y in perfil]
    p.malla(g, "hocico", loft_z([atras, adelante], abanico=True), hocico, dens=D)
    # las cejas salidas sobre los ojos
    for s in (1, -1):
        p.malla(g, f"ceja{s}", tubo((s * 0.8, 21.6, -38.4), (s * 6.4, 22.8, -36.4), 1.1, 0.9, 4), clara, dens=D)
    # los ojos que brillan (en la cara de enfrente)
    for s in (1, -1):
        a, b = sorted((s * 1.8, s * 4.3))
        p.caja(g, f"ojo{s}", (a, 19.5, -38.1), (b, 20.8, -37.95), lambda t: hex_(OJO), dens=4, luz=False)
        a, b = sorted((s * 2.6, s * 3.4))
        p.caja(g, f"brillo{s}", (a, 19.85, -38.2), (b, 20.45, -38.05), lambda t: hex_(OJO_CENTRO), dens=4, luz=False)
    # solo los cuernos: de los lados de la cabeza, hacia afuera y apenas arriba, y la punta curvea adelante
    camino = ((7.0, 23.5, -33.0, 3.1), (12.5, 26.3, -32.0, 2.6), (17.0, 29.0, -32.5, 1.9), (19.4, 31.2, -35.0, 1.3),
              (20.1, 32.4, -38.0, 0.6), (19.8, 33.0, -40.5, 0.1))
    for s in (1, -1):
        for i, (a, b) in enumerate(zip(camino, camino[1:])):
            p.malla(g, f"cuerno{s}_{i}", tubo((s * a[0], a[1], a[2]), (s * b[0], b[1], b[2]), a[3], b[3], 6), amatista,
                    dens=D)


def piedras_cuadradas(p, grupo, tabla, nombre, lista, tam, pintores, semilla):
    """Piedras cuadradas grandes encajadas en el cuerpo, derechas con la superficie: (z, fi)."""
    for k, (z, fi) in enumerate(lista):
        sem = semilla + k * 3.7
        base, fuera = en_superficie(tabla, z, fi, 0.98)
        w, h, d = (tam * (0.7 + 0.5 * _azar(sem + i)) for i in range(3))
        a = math.radians(fi)
        bloque(p, grupo, f"{nombre}{k}", base, (w, h, d), (math.cos(a), -math.sin(a), 0.0), fuera,
               pintores[k % len(pintores)])


def cuerpo(p):
    piedra_o, clara = piedra(PIEDRA), piedra(PIEDRA_C)
    p.malla("Body/cuerpo", "cuerpo", loft_z([octagono(z, y, mx, my) for z, y, mx, my in CUERPO]), piedra_o, dens=D)
    p.malla("Body/cola", "cola", loft_z([octagono(z, y, mx, my) for z, y, mx, my in COLA]), piedra_o, dens=D)
    # la piel rocosa: bloques encimados en todo el cuerpo y la cola
    rocas(p, "Body/rocas", "roca", [octagono(z, y, mx, my) for z, y, mx, my in CUERPO], (3.8, 1.6), [clara, piedra_o], 7)
    rocas(p, "Body/cola", "roca_cola", [octagono(z, y, mx, my) for z, y, mx, my in COLA[:6]], (2.8, 1.1),
          [clara, piedra_o], 40)
    # las puas del lomo (las mas altas en los hombros, mas chicas a los lados) y las de la cola
    def alto(z, fi):
        return (19.0 - abs(z + 9.0) * 0.38) * (1.0 - abs(fi) / 160.0)
    picos(p, "Body/picos", CUERPO, "pico", 120, (-21.0, 20.0, 105), alto, 4.4, 0.55, 1)
    picos(p, "Body/cola", COLA, "pico_cola", 48, (22.0, 66.0, 70),
          lambda z, fi: max(1.6, 8.5 - (z - 21.0) * 0.15) * (1.0 - abs(fi) / 140.0), 3.0, 0.9, 50)
    # el relleno de los costados (que no quede liso): cristales chicos y piedras cuadradas, y en el pecho
    picos(p, "Body/picos", CUERPO, "cristal_costado", 36, (-20.0, 19.0, 135, 100), lambda z, fi: 6.5, 3.4, 0.4, 70,
          ("gruesa", "cristal", "pilar"))
    piedras_cuadradas(p, "Body/rocas", CUERPO, "piedra", [(-19.0 + 3.6 * i, (1 if i % 2 else -1) * (112 + 18 * _azar(i * 3.3)))
                                                        for i in range(11)], 4.8, [clara, piedra_o], 90)
    for i, (x, y, d) in enumerate(((0.0, 24.0, (0.0, -0.3, -1.0)), (4.5, 21.5, (0.35, -0.4, -1.0)),
                                   (-4.5, 21.5, (-0.35, -0.4, -1.0)), (6.5, 27.5, (0.5, 0.2, -1.0)),
                                   (-6.5, 27.5, (-0.5, 0.2, -1.0)))):
        p.malla("Body/picos", f"cristal_pecho{i}", esquirla((x, y, -21.5), 3.2, 5.5 - (i % 2), hacia(d),
                                                            ("gruesa", "cristal")[i % 2]), cristal(), dens=D)


def pata(p, hueso, s, articulaciones, radios, pie, garras):
    """Una pata de piedra: cada tramo (hombro a codo, codo a muneca...) de bloques derechos encimados con rocas
    salidas por afuera, adelante y atras; una roca grande en cada articulacion, el pie de dos bloques y las garras."""
    piedra_o, clara, garra = piedra(PIEDRA), piedra(PIEDRA_C), voxel(GARRA, 0.1)
    g = f"{hueso}/pata"
    afuera = "east" if s > 0 else "west"
    puntos = [(s * x, y, z) for x, y, z in articulaciones]
    for i, (a, b) in enumerate(zip(puntos, puntos[1:])):
        ra, rb = radios[i], radios[i + 1]
        tramo_de_piedra(p, g, f"tramo{i}_", a, b, (ra, ra * 0.9, ra), (rb, rb * 0.9, rb), (afuera, "north", "south"),
                        [piedra_o, clara] if i % 2 == 0 else [clara, piedra_o], 200 + 13 * i + s)
    for i, c in enumerate(puntos[:-1]):                       # las rocas de las articulaciones (hombro y codo)
        t = radios[i] * 1.3                                  # medio tamano
        d, h = (c[0] - t, c[1] - t * 0.8, c[2] - t), (c[0] + t, c[1] + t * 0.8, c[2] + t)
        p.caja(g, f"articulacion{i}", d, h, clara if i % 2 == 0 else piedra_o, dens=D)
        for cara in (afuera, "north", "south", "up"):          # que no quede ninguna cara lisa
            rocas_caja(p, g, f"roca_articulacion{i}_{cara}_", d, h, cara, (3, 3), (3.6, 1.6), [piedra_o, clara],
                       300 + i * 7 + s + len(cara))
        for k, (dy, dz) in enumerate(((0.45, -0.35), (0.6, 0.4), (0.1, 0.05))):   # cristales por afuera
            base = ((h[0] if s > 0 else d[0]) - s * 0.6, c[1] + dy * t * 0.8, c[2] + dz * t)
            p.malla(g, f"cristal_articulacion{i}_{k}",
                    esquirla(base, 2.6 - 0.5 * k, 6.0 - 1.2 * k, hacia((s * 1.0, 0.7 + 0.2 * k, 0.3 * dz)),
                             ("cristal", "gruesa", "aguja")[k]), cristal(), dens=D)
    (x, y, z0, z1, r) = pie
    a, b = sorted((s * (x - r * 1.15), s * (x + r * 1.15)))
    p.caja(g, "pie", (a, 0.0, min(z0, z1)), (b, y + r * 0.5, max(z0, z1)), clara, dens=D)
    a, b = sorted((s * (x - r * 0.9), s * (x + r * 0.9)))
    p.caja(g, "empeine", (a, y + r * 0.4, min(z0, z1) + 1.0), (b, y + r * 1.1, max(z0, z1) - 1.5), piedra_o, dens=D)
    for k, dx in enumerate(garras):
        p.malla(g, f"garra{k}", esquirla((s * (x + dx), 1.0, z1 + 0.6), 1.5, 3.0, hacia((0.0, -0.45, -1.0))), garra,
                dens=D)


def patas(p):
    for s in (1, -1):
        # las de enfrente: el hombro sale del cuerpo, el codo abierto hacia afuera y el antebrazo baja a la mano
        pata(p, "RightArm" if s > 0 else "LeftArm", s, ((12.0, 27.0, -11.0), (23.5, 17.5, -9.5), (21.0, 4.8, -12.5)),
             (7.4, 6.0, 4.6), (21.0, 2.8, -8.5, -19.0, 4.0), (-2.4, 0.0, 2.4))
        # las de atras: la cadera, la rodilla hacia afuera y adelante, el tobillo
        pata(p, "RightLeg" if s > 0 else "LeftLeg", s, ((10.5, 25.0, 14.0), (18.5, 15.0, 10.5), (17.0, 4.4, 15.5)),
             (6.6, 5.3, 4.1), (17.0, 2.6, 19.5, 9.0, 3.6), (-1.8, 1.8))


def construir():
    p = Personaje("jefe_piedra", altura=32)
    p.m.luz_desde = LUZ_SIMETRICA
    cabeza(p)
    cuerpo(p)
    patas(p)
    p.m.pivotes.update({"Head": (0.0, 27.0, -20.0), "Body": (0.0, 26.0, 0.0), "Body/cola": (0.0, 22.5, 21.0),
                        "RightArm": (12.0, 27.0, -11.0), "LeftArm": (-12.0, 27.0, -11.0),
                        "RightLeg": (10.5, 25.0, 14.0), "LeftLeg": (-10.5, 25.0, 14.0)})
    return p


def escalar(p, k):
    """Crece todo el jefe k veces desde el piso (para llevarlo al tamano del Ender Dragon)."""
    from .chibi import achibar
    return achibar(p, cabeza=k, cuerpo=(k, k, k), cuello=0.0)
