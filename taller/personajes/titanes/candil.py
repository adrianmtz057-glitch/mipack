"""
CANDIL, el axolote titan (hoja nueva: "Axolote Titan"). Un ajolote enorme de bloques azul lavanda con manchas rosas,
la cabeza ancha y plana con la boca en linea, ojos chicos con la pupila que brilla magenta y una mancha rosa que
brilla en la mejilla; tres branquias por lado como plumas de coral (rosa coral, magenta y lila en las puntas), una
cresta lila por el lomo que sigue por arriba y por abajo de la cola larga y aplanada, cuatro patas cortas con dedos
abiertos de punta rosa y unos puntitos turquesa que brillan en los costados.
Escala: 1 voxel = 0.4 bloques (ESCALA 6.4): unos 30 bloques de largo y 11 de alto con las branquias.
Huesos: raiz / cuerpo / (cabeza / (branquias_d, branquias_i), cola1 / cola2 / cola3, pata_dd, pata_di, pata_td,
pata_ti). Solo modelo.
"""

import math

import numpy as np

from ...escultor import Escultor, Material
from ...kit import Personaje

ESCALA = 6.4

PIEL = {"o": "#6A7DA0", "s": "#8196BA", "b": "#9DB1D3", "l": "#B6C8E5", "h": "#CFDDF1"}
PANZA = {"o": "#8696B4", "s": "#A3B4D2", "b": "#BCCBE5", "l": "#D2DEF0", "h": "#E4ECF8"}
MANCHA = {"o": "#A04682", "s": "#C35E9E", "b": "#DC7DB6", "l": "#EC9FCB", "h": "#F5BEDC"}
CORAL = {"o": "#A63E5C", "s": "#C8536F", "b": "#E2708A", "l": "#F093A8", "h": "#F8B6C4"}
MAGENTA = {"o": "#963D7E", "s": "#B44E95", "b": "#D86BB2", "l": "#EB90CA", "h": "#F5B4DD"}
LILA = {"o": "#8668AA", "s": "#A285C6", "b": "#C3A6E2", "l": "#D8C3EF", "h": "#EADCF8"}
TURQUESA = {"o": "#2E8C82", "s": "#3FAA9E", "b": "#5FC6B8", "l": "#8DE0D3", "h": "#BDF2EA"}
OJO = {"o": "#120C20", "s": "#24183C", "b": "#5E2A92", "l": "#B848E8", "h": "#F0A0FF"}
MEJILLA = {"o": "#C2408E", "s": "#D857A4", "b": "#EC74BC", "l": "#F79AD2", "h": "#FDC2E6"}
BOCA = {"o": "#3A3550", "s": "#4A4562", "b": "#5A5574", "l": "#6A6586", "h": "#7A7598"}

DIBUJO_OJO = ("oooooooo", "oossssoo", "osbllbso", "oslhhlso", "oslhhlso", "osbllbso", "oossssoo", "oooooooo")
DIBUJO_MEJILLA = ("bbllllbb", "blhhhhlb", "lhhhhhhl", "lhhhhhhl", "lhhhhhhl", "lhhhhhhl", "blhhhhlb", "bbllllbb")

CUERPO = ((0.0, 13.0, -1.0), (9.5, 7.0, 16.0), 3.2)      # centro, medios, p
CABEZA = ((0.0, 14.0, -24.0), (11.5, 7.5, 9.0), 3.6)


def _arriba(forma, x, z):
    """La altura de arriba de una superelipsoide en (x, z) (o None si no pasa por ahi)."""
    (cx, cy, cz), (rx, ry, rz), p = forma
    k = 1 - abs((x - cx) / rx) ** p - abs((z - cz) / rz) ** p
    return None if k <= 0 else cy + ry * k ** (1 / p)


def _branquia(e, base, puntos, hueso, mats, semilla):
    """Una branquia: el tallo de coral que sale de la cabeza y se curva, con plumitas a los lados que cambian de color
    hacia la punta (coral, magenta, lila)."""
    coral, magenta, lila = mats
    camino = [base] + puntos
    n = len(camino)
    tramos = []
    for k in range(n - 1):
        r0 = 1.15 - 0.55 * k / (n - 1)
        r1 = 1.15 - 0.55 * (k + 1) / (n - 1)
        tramos.append((camino[k], camino[k + 1], r0, r1))
    for k, (a, b, r0, r1) in enumerate(tramos):
        e.capsula(a, b, r0, r1, coral if k < n // 2 else magenta, hueso)
    # plumitas: cada voxel y medio, alternando de lado, mas largas a media branquia
    total = sum(math.dist(a, b) for a, b, _, _ in tramos)
    paso, d = 1.5, 1.0
    k = 0
    while d < total - 0.5:
        # punto a la distancia d
        acum = 0.0
        for a, b, _, _ in tramos:
            L = math.dist(a, b)
            if acum + L >= d:
                t = (d - acum) / L
                c = tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
                tng = tuple((b[i] - a[i]) / L for i in range(3))
                break
            acum += L
        f = d / total
        largo = 1.5 + 2.2 * math.sin(math.pi * min(1.0, f * 1.15))
        # de lado: arriba/abajo del tallo, un poco hacia adelante
        lado = 1 if k % 2 == 0 else -1
        arriba = (0.0, 1.0, 0.0)
        perp = tuple(arriba[i] - tng[i] * sum(arriba[j] * tng[j] for j in range(3)) for i in range(3))
        lp = math.sqrt(sum(v * v for v in perp)) or 1.0
        perp = tuple(v / lp for v in perp)
        punta = tuple(c[i] + perp[i] * largo * lado - tng[i] * 0.6 for i in range(3))
        mat = coral if f < 0.35 else magenta if f < 0.7 else lila
        e.capsula(c, punta, 0.55, 0.45, mat, hueso)
        if f > 0.55:
            e.capsula(punta, tuple(punta[i] - tng[i] * 0.2 + perp[i] * 0.8 * lado for i in range(3)), 0.45, 0.4, lila,
                      hueso)
        d += paso
        k += 1


def construir():
    e = Escultor("candil", (-26, -1, -36), (26, 34, 54))
    piel = e.material("piel", PIEL, "piel")
    panza = e.material("panza", PANZA, "piel")
    mancha = e.material("mancha", MANCHA, "piel")
    coral = e.material("coral", CORAL, "liso")
    magenta = e.material("magenta", MAGENTA, "liso")
    lila = e.material("lila", LILA, "liso")
    turquesa = e.material("turquesa", TURQUESA, "brillo", brilla=True)
    ojo = e.material(Material("ojo", OJO, (DIBUJO_OJO,), brilla=True))
    mejilla = e.material(Material("mejilla", MEJILLA, (DIBUJO_MEJILLA,), brilla=True))
    boca = e.material("boca", BOCA, "liso")

    raiz = e.hueso("raiz", (0, 0, 0))
    cuerpo = e.hueso("raiz/cuerpo", (0, 13, 0))
    cabeza = e.hueso("raiz/cuerpo/cabeza", (0, 13, -14))
    br_d = e.hueso("raiz/cuerpo/cabeza/branquias_d", (10, 15, -17))
    br_i = e.hueso("raiz/cuerpo/cabeza/branquias_i", (-10, 15, -17))
    cola1 = e.hueso("raiz/cuerpo/cola1", (0, 13, 14))
    cola2 = e.hueso("raiz/cuerpo/cola1/cola2", (0, 13, 27))
    cola3 = e.hueso("raiz/cuerpo/cola1/cola2/cola3", (0, 12.5, 39))
    patas = {}
    for nombre, x, z in (("dd", 1, -12), ("di", -1, -12), ("td", 1, 12), ("ti", -1, 12)):
        patas[nombre] = e.hueso(f"raiz/cuerpo/pata_{nombre}", (x * 8.5, 8.5, z))

    # --- la cabeza: ancha y plana, la boca en linea
    c, r, p = CABEZA
    e.superelipsoide(c, r, piel, cabeza, p=p)
    # --- el cuerpo y la cola larga, aplanada de lado
    c, r, p = CUERPO
    e.superelipsoide(c, r, piel, cuerpo, p=p)
    cola = [(0.0, 13.0, 12.0, 6.6), (0.0, 13.4, 22.0, 5.6), (0.0, 13.2, 31.0, 4.2), (0.0, 12.6, 40.0, 2.8),
            (0.0, 12.0, 48.0, 1.4), (0.0, 11.8, 52.0, 0.6)]
    huesos_cola = (cola1, cola1, cola2, cola3, cola3)
    for (a, b, h) in zip(cola, cola[1:], huesos_cola):
        e.capsula(a[:3], b[:3], a[3], b[3], piel, h, ejes=(0.55, 1.0, 1.0))
    # --- las patas: cortas, con el codo hacia afuera y cuatro dedos abiertos de punta rosa
    for nombre, (x, z, haciaz) in (("dd", (1, -12, -1)), ("di", (-1, -12, -1)), ("td", (1, 12, 1)), ("ti", (-1, 12, 1))):
        h = patas[nombre]
        hombro = (x * 8.0, 9.5, z)
        codo = (x * 13.0, 5.5, z + haciaz * 1.5)
        pie = (x * 14.5, 1.4, z + haciaz * 2.5)
        e.capsula(hombro, codo, 2.6, 2.1, piel, h)
        e.capsula(codo, pie, 2.1, 1.7, piel, h)
        for k, ang in enumerate((-40.0, -12.0, 15.0, 42.0)):
            a = math.radians(ang)
            dx, dz = math.sin(a) * x, -math.cos(a) * (-haciaz if haciaz > 0 else 1)
            if haciaz > 0:
                dz = math.cos(a)
            punta = (pie[0] + dx * 3.6 + x * 1.0, 0.6, pie[2] + dz * 3.6)
            medio = tuple((pie[i] + punta[i]) / 2 for i in range(3))
            e.capsula(pie, medio, 0.8, 0.7, piel, h)
            e.capsula(medio, punta, 0.7, 0.6, coral, h)
    # --- la cresta del lomo y las aletas de la cola (una lamina de un voxel, dispareja)
    for z in range(-13, 15):
        y0 = _arriba(CUERPO, 0.0, z + 0.5)
        if y0 is None:
            continue
        alto = 1.5 + 2.5 * (0.5 + 0.5 * math.sin(z * 0.9)) * (1 - abs(z) / 16) + (z % 3 == 0)
        e.caja((-0.5, y0 - 1, z), (0.5, y0 + alto, z + 1), lila if z % 4 else magenta, cuerpo)
    for (a, b, h) in zip(cola, cola[1:], huesos_cola):
        z0, z1 = int(a[2]), int(b[2])
        for z in range(z0, z1):
            t = (z - a[2]) / (b[2] - a[2])
            yc = a[1] + (b[1] - a[1]) * t
            rr = a[3] + (b[3] - a[3]) * t
            arriba = 2.0 + 2.5 * (0.5 + 0.5 * math.sin(z * 1.3)) + 2.0 * (z % 5 == 0)
            abajo = 1.5 + 2.0 * (0.5 + 0.5 * math.cos(z * 1.1)) + 1.5 * (z % 4 == 1)
            e.caja((-0.5, yc + rr - 1, z), (0.5, yc + rr + arriba, z + 1), lila if z % 3 else magenta, h)
            e.caja((-0.5, yc - rr - abajo, z), (0.5, yc - rr + 1, z + 1), lila if z % 3 != 1 else magenta, h)
    # --- branquias: tres por lado
    for s, h in ((1, br_d), (-1, br_i)):
        _branquia(e, (s * 10.0, 19.0, -18.0), [(s * 12.5, 24.0, -16.0), (s * 15.0, 28.5, -12.5), (s * 16.5, 32.0, -8.0)],
                  h, (coral, magenta, lila), 1)
        _branquia(e, (s * 11.0, 15.0, -17.0), [(s * 15.0, 17.0, -15.0), (s * 19.0, 18.5, -12.0), (s * 22.5, 19.5, -8.5)],
                  h, (coral, magenta, lila), 2)
        _branquia(e, (s * 10.5, 11.0, -16.0), [(s * 14.0, 9.5, -14.0), (s * 17.5, 7.5, -11.5), (s * 20.0, 6.0, -8.0)],
                  h, (coral, magenta, lila), 3)

    # --- la piel: panza clara, manchas rosas (un campo fijo de ondas), boca, ojos, mejillas y puntitos turquesa
    e.cubrir(panza, solo=[piel], lado=(1, -1), grosor=1)

    def manchas(X, Y, Z, M):
        v = (np.sin(X * 0.42 + Z * 0.29) * np.cos(Y * 0.55 - Z * 0.21) + 0.6 * np.sin(Z * 0.17 + X * 0.13 + 1.3)
             + 0.35 * np.cos(X * 0.9 - Y * 0.7 + Z * 0.5))
        return np.where(v > 1.05, mancha, 0).astype(np.int16)
    e.vetas(manchas, solo=[piel])
    e.caja((-11.0, 9.0, -34.0), (11.0, 10.0, -27.0), boca, cabeza, modo="pintar")
    for s in (1, -1):
        x0, x1 = sorted((s * 10.0, s * 12.0))
        e.caja((x0, 16.0, -30.0), (x1, 17.0, -29.0), ojo, cabeza, modo="pintar")
        e.caja((x0, 13.0, -27.0), (x1, 14.0, -26.0), mejilla, cabeza, modo="pintar")
    e.salpicar(turquesa, 0.012, solo=[piel], semilla=7.0,
               donde=lambda X, Y, Z: (np.abs(X) > 5.0) & (Y > 9.0) & (Y < 18.0) & (Z > -14.0) & (Z < 30.0))

    p = Personaje("candil", altura=32)
    p.m.pivotes = {}
    p.m.luz = False
    e.armar(p)
    construir.escultor = e
    return p


def brillan():
    e = getattr(construir, "escultor", None)
    if e is None:
        construir()
        e = construir.escultor
    return e.brillan()
