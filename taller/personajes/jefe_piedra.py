"""
El primer jefe (inspirado en Azdaha): una bestia de piedra oscura en cuatro patas, con la espalda llena de picos de
piedra amatista. Diseno simple (las formas grandes) armado CHICO y bien proporcionado: despues se crece entero
(escalar) hasta el tamano del Ender Dragon.
  CABEZA baja y hacia adelante: el craneo anguloso, el hocico de piedra palida que baja como pico, dos ojos morados
    que brillan, las cejas salidas y una corona de picos que salen hacia atras y a los lados
  CUERPO pesado con la joroba de los hombros (lo mas alto) que baja hacia la cadera; las PATAS de enfrente enormes
    y abiertas, las de atras mas chicas, todas con garras
  PICOS de piedra en la espalda: una fila al centro (los mas altos en los hombros) y dos a los lados mas chicos e
    inclinados hacia afuera, todos echados hacia atras; siguen por la COLA larga, que se afila y baja
Medidas en px (16 por bloque); el frente es -Z, su derecha es +X. Mide unos 5 bloques de largo con la cola.
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


def esquirla(base, ancho, alto, rot=(0, 0, 0)):
    """Un pico de piedra: el cuerpo cuadrado que se angosta y acaba en punta (como un cristal), parado en 'base' y
    girado (rx, ry, rz) desde su base."""
    x, y, z = base
    abajo = geo.anillo(x, y, z, ancho / 2, ancho / 2, 4, 45)
    medio = geo.anillo(x, y + alto * 0.62, z, ancho * 0.36, ancho * 0.36, 4, 45)
    m = geo.unir(geo.tronco(abajo, medio, tapa_abajo=True, tapa_arriba=False),
                 geo.piramide(medio, (x, y + alto, z), tapa=False))
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
CUELLO = ((-21.0, 26.0, 10.0, 8.5), (-26.0, 22.5, 8.5, 7.5), (-30.0, 20.0, 7.8, 6.8))
CABEZA = ((-30.0, 20.0, 8.2, 7.0), (-34.0, 19.0, 7.4, 6.3), (-37.5, 17.5, 5.9, 5.2))


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


def picos(p, grupo, tabla, nombre, zs, fis, alto, ancho, atras, semilla):
    """Picos que salen del lomo en abanico: cada uno hacia afuera de donde nace (arriba, de lado...), echados un poco
    hacia atras y cada uno un poco distinto."""
    amatista = voxel(AMATISTA, 0.1)
    k = 0
    for i, z in enumerate(zs):
        for fi in fis:
            sem = semilla + k * 5.3
            fi_ = fi + 14 * (_azar(sem) - 0.5) + (7 if i % 2 else -7) * (fi != 0)
            base, fuera = en_superficie(tabla, z + 1.2 * (_azar(sem + 1) - 0.5), fi_)
            d = (fuera[0], fuera[1], atras + 0.35 * (_azar(sem + 2) - 0.5))
            h = alto(z, fi) * (0.8 + 0.4 * _azar(sem + 3))
            p.malla(grupo, f"{nombre}{k}", esquirla(base, ancho * (0.8 + 0.4 * _azar(sem + 4)), h, hacia(d)),
                    amatista, dens=D)
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
    piedra, clara, hocico, amatista = voxel(PIEDRA, 0.05), voxel(PIEDRA_C, 0.05), voxel(HOCICO, 0.1), voxel(AMATISTA, 0.1)
    g = "Head/cabeza"
    p.malla(g, "cuello", loft_z([octagono(z, y, mx, my) for z, y, mx, my in CUELLO]), piedra, dens=D)
    p.malla(g, "craneo", loft_z([octagono(z, y, mx, my) for z, y, mx, my in CABEZA]), clara, dens=D)
    rocas(p, g, "roca_cuello", [octagono(z, y, mx, my) for z, y, mx, my in CUELLO], (3.4, 1.4), [clara, piedra], 11)
    rocas(p, g, "roca_craneo", [octagono(z, y, mx, my) for z, y, mx, my in CABEZA[:2]], (3.0, 1.2), [piedra, clara], 21)
    # el hocico (la boca): un pico ancho de piedra palida pegado a la cara abajo de los ojos, con la quilla al
    # centro, que baja y sale hacia adelante hasta una punta roma
    from .bloques import tubo
    perfil = ((0.0, 17.2), (4.8, 16.8), (4.3, 12.2), (1.6, 7.6), (0.0, 6.8), (-1.6, 7.6), (-4.3, 12.2), (-4.8, 16.8))
    atras = [(x, y, -36.8) for x, y in perfil]
    adelante = [(x * 0.82, y - 0.8, -40.2 - (1.0 if x == 0 else 0.0) + 0.12 * abs(y - 12.0)) for x, y in perfil]
    p.malla(g, "hocico", loft_z([atras, adelante], abanico=True), hocico, dens=D)
    # las cejas salidas sobre los ojos
    for s in (1, -1):
        p.malla(g, f"ceja{s}", tubo((s * 0.8, 20.9, -38.0), (s * 6.0, 22.1, -36.0), 1.0, 0.8, 4), clara, dens=D)
    # los ojos que brillan (en la cara de enfrente)
    for s in (1, -1):
        a, b = sorted((s * 1.6, s * 4.0))
        p.caja(g, f"ojo{s}", (a, 18.7, -37.6), (b, 20.0, -37.45), lambda t: hex_(OJO), dens=4, luz=False)
        a, b = sorted((s * 2.4, s * 3.2))
        p.caja(g, f"brillo{s}", (a, 19.05, -37.7), (b, 19.65, -37.55), lambda t: hex_(OJO_CENTRO), dens=4, luz=False)
    # solo los cuernos: de los lados de la cabeza, hacia afuera y apenas arriba, y la punta curvea adelante
    camino = ((6.5, 22.0, -32.0, 2.9), (11.5, 24.8, -31.0, 2.4), (15.8, 27.6, -31.5, 1.8), (18.2, 29.8, -34.0, 1.2),
              (18.9, 31.0, -37.0, 0.6), (18.6, 31.6, -39.5, 0.1))
    for s in (1, -1):
        for i, (a, b) in enumerate(zip(camino, camino[1:])):
            p.malla(g, f"cuerno{s}_{i}", tubo((s * a[0], a[1], a[2]), (s * b[0], b[1], b[2]), a[3], b[3], 6), amatista,
                    dens=D)


def cuerpo(p):
    piedra, clara = voxel(PIEDRA, 0.05), voxel(PIEDRA_C, 0.05)
    p.malla("Body/cuerpo", "cuerpo", loft_z([octagono(z, y, mx, my) for z, y, mx, my in CUERPO]), piedra, dens=D)
    p.malla("Body/cola", "cola", loft_z([octagono(z, y, mx, my) for z, y, mx, my in COLA]), piedra, dens=D)
    # la piel rocosa: bloques encimados en todo el cuerpo y la cola
    rocas(p, "Body/rocas", "roca", [octagono(z, y, mx, my) for z, y, mx, my in CUERPO], (3.8, 1.6), [clara, piedra], 7)
    rocas(p, "Body/cola", "roca_cola", [octagono(z, y, mx, my) for z, y, mx, my in COLA[:6]], (2.8, 1.1),
          [clara, piedra], 40)
    # los picos del lomo en abanico (los mas altos en los hombros) y los de la cola
    def alto(z, fi):
        return (18.0 - abs(z + 9.0) * 0.38) * (1.0 - abs(fi) / 150.0)
    picos(p, "Body/picos", CUERPO, "pico", [-19.0 + 3.4 * i for i in range(12)], (0, 28, -28, 55, -55, 82, -82),
          alto, 4.2, 0.55, 1)
    picos(p, "Body/cola", COLA, "pico_cola", [23.0 + 4.0 * i for i in range(11)], (0, 45, -45),
          lambda z, fi: max(1.5, 8.0 - (z - 21.0) * 0.15) * (1.0 - abs(fi) / 130.0), 2.8, 0.9, 50)


def pata(p, hueso, s, articulaciones, radios, pie, garras):
    """Una pata de varios tramos poligonales (hombro, codo, muneca...) con su piel rocosa, una roca en cada
    articulacion, el pie y las garras."""
    from .bloques import tubo
    piedra, clara, garra = voxel(PIEDRA, 0.05), voxel(PIEDRA_C, 0.05), voxel(GARRA, 0.1)
    g = f"{hueso}/pata"
    puntos = [(s * x, y, z) for x, y, z in articulaciones]
    for i, (a, b) in enumerate(zip(puntos, puntos[1:])):
        anillos = anillos_tubo(a, b, radios[i], radios[i + 1])
        p.malla(g, f"tramo{i}", loft_z(anillos), piedra if i % 2 == 0 else clara, dens=D)
        rocas(p, g, f"roca{i}_", anillos, (3.0, 1.3), [clara, piedra], 200 + 13 * i + s)
    for i, c in enumerate(puntos[:-1]):                       # las rocas de las articulaciones (hombro y codo)
        t = radios[i] * 2.1
        rot = tuple(40 * (_azar(i * 9.1 + s + j) - 0.5) for j in range(3))
        p.caja(g, f"articulacion{i}", (c[0] - t / 2, c[1] - t / 2, c[2] - t / 2),
               (c[0] + t / 2, c[1] + t / 2, c[2] + t / 2), clara if i % 2 == 0 else piedra, rot=rot, piv=c, dens=D)
    (x, y, z0, z1, r) = pie
    p.malla(g, "pie", tubo((s * x, y, z0), (s * x, y, z1), r, r * 0.8, 6), clara, dens=D)
    for k, dx in enumerate(garras):
        p.malla(g, f"garra{k}", esquirla((s * (x + dx), y - 0.6, z1 + 0.6), 1.5, 3.0, hacia((0.0, -0.45, -1.0))), garra,
                dens=D)


def patas(p):
    for s in (1, -1):
        # las de enfrente: el hombro sale del cuerpo, el codo abierto hacia afuera y el antebrazo baja a la mano
        pata(p, "RightArm" if s > 0 else "LeftArm", s, ((11.5, 27.0, -11.0), (22.0, 17.5, -9.5), (19.5, 4.5, -12.5)),
             (6.2, 4.9, 3.7), (19.5, 2.5, -9.0, -18.5, 3.4), (-2.1, 0.0, 2.1))
        # las de atras: la cadera, la rodilla hacia afuera y adelante, el tobillo
        pata(p, "RightLeg" if s > 0 else "LeftLeg", s, ((10.0, 25.0, 14.0), (17.5, 15.0, 10.5), (16.0, 4.0, 15.5)),
             (5.4, 4.3, 3.3), (16.0, 2.3, 19.0, 9.5, 3.0), (-1.6, 1.6))


def construir():
    p = Personaje("jefe_piedra", altura=32)
    p.m.luz_desde = LUZ_SIMETRICA
    cabeza(p)
    cuerpo(p)
    patas(p)
    p.m.pivotes.update({"Head": (0.0, 26.0, -20.0), "Body": (0.0, 26.0, 0.0), "Body/cola": (0.0, 22.5, 21.0),
                        "RightArm": (11.5, 27.0, -11.0), "LeftArm": (-11.5, 27.0, -11.0),
                        "RightLeg": (10.0, 25.0, 14.0), "LeftLeg": (-10.0, 25.0, 14.0)})
    return p


def escalar(p, k):
    """Crece todo el jefe k veces desde el piso (para llevarlo al tamano del Ender Dragon)."""
    from .chibi import achibar
    return achibar(p, cabeza=k, cuerpo=(k, k, k), cuello=0.0)
