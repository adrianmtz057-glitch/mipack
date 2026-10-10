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


# los picos de la espalda: (z, y de la base, alto, ancho); los de la fila del centro
PICOS_CENTRO = ((-15.0, 25.0, 9, 4.0), (-10.5, 27.5, 15, 5.0), (-5.5, 27.0, 17, 5.5), (-0.5, 25.5, 15, 5.0),
                (4.5, 23.5, 12, 4.5), (9.5, 21.5, 10, 4.0), (14.0, 20.0, 8, 3.5))
# los de los lados: (x, z, y de la base, alto, ancho)
PICOS_LADO = ((6.5, -12.0, 24.0, 9, 3.5), (7.5, -6.5, 24.5, 11, 4.0), (7.0, -1.0, 23.0, 10, 3.5),
              (6.5, 4.5, 21.5, 8, 3.2), (6.0, 10.0, 19.5, 7, 3.0), (5.5, 15.0, 18.0, 5, 2.6))
# la cola: tramos (z de, z a, medio ancho, y abajo, y arriba); se afila y baja
COLA = ((16.0, 24.0, 6.0, 11.0, 18.5), (24.0, 32.0, 5.0, 9.5, 16.0), (32.0, 40.0, 4.0, 7.5, 13.0),
        (40.0, 48.0, 3.0, 5.5, 10.0), (48.0, 55.0, 2.2, 4.0, 7.5), (55.0, 61.0, 1.4, 3.0, 5.5))


def cabeza(p):
    piedra, clara, hocico = voxel(PIEDRA, 0.05), voxel(PIEDRA_C, 0.05), voxel(HOCICO, 0.1)
    amatista = voxel(AMATISTA, 0.1)
    g = "Head/cabeza"
    p.caja(g, "cuello", (-5.5, 12.0, -22.0), (5.5, 22.0, -13.0), piedra, rot=(-18, 0, 0), piv=(0, 17, -13), dens=D)
    p.caja(g, "craneo", (-6.0, 9.5, -30.0), (6.0, 17.5, -20.0), piedra, dens=D)
    p.caja(g, "frente", (-4.5, 15.0, -31.0), (4.5, 18.5, -24.0), clara, rot=(12, 0, 0), piv=(0, 15, -24), dens=D)
    # las cejas salidas sobre los ojos
    for s in (1, -1):
        a, b = sorted((s * 1.4, s * 6.4))
        p.caja(g, f"ceja{s}", (a, 14.4, -31.2), (b, 15.8, -27.0), clara, rot=(0, 0, s * -14),
               piv=(s * 1.4, 15.0, -29.0), dens=D)
    # el hocico de piedra palida que baja como pico
    p.caja(g, "hocico", (-3.6, 4.5, -33.0), (3.6, 12.5, -27.5), hocico, rot=(14, 0, 0), piv=(0, 12.5, -29.0), dens=D)
    p.caja(g, "mandibula", (-4.6, 7.0, -29.5), (4.6, 10.5, -21.0), piedra, dens=D)
    # los ojos que brillan
    for s in (1, -1):
        a, b = sorted((s * 2.0, s * 4.4))
        p.caja(g, f"ojo{s}", (a, 13.0, -30.25), (b, 14.4, -29.9), lambda t: hex_(OJO), dens=4, luz=False)
        a, b = sorted((s * 2.8, s * 3.6))
        p.caja(g, f"brillo{s}", (a, 13.4, -30.35), (b, 14.0, -30.2), lambda t: hex_(OJO_CENTRO), dens=4, luz=False)
    # la corona de picos: hacia atras arriba y hacia los lados
    picos = (((0.0, 17.0, -24.0), 4.5, 14.0, (-60, 0, 0)), ((2.6, 16.5, -26.0), 3.8, 13.0, (-55, 0, -20)),
             ((5.5, 15.5, -25.5), 3.8, 16.0, (-30, 0, -58)), ((6.0, 12.5, -24.0), 3.4, 15.0, (-15, 0, -78)),
             ((5.5, 10.0, -23.0), 3.0, 11.0, (-5, 0, -100)), ((4.5, 17.0, -21.5), 3.4, 11.0, (-70, 0, -32)))
    for i, (base, w, h, rot) in enumerate(picos):
        for s in ((1, -1) if base[0] else (1,)):
            x, y, z = base
            rx, ry, rz = rot
            p.malla(g, f"corona{i}_{s}", esquirla((s * x, y, z), w, h, (rx, ry, s * rz)), amatista, dens=D)


def cuerpo(p):
    piedra, clara = voxel(PIEDRA, 0.05), voxel(PIEDRA_C, 0.05)
    g = "Body/cuerpo"
    p.caja(g, "pecho", (-9.5, 11.0, -17.0), (9.5, 24.5, -4.0), piedra, dens=D)
    p.caja(g, "joroba", (-7.5, 24.0, -15.0), (7.5, 28.0, -2.0), clara, dens=D)
    p.caja(g, "panza", (-8.5, 11.5, -4.5), (8.5, 24.0, 7.0), piedra, dens=D)
    p.caja(g, "lomo", (-6.5, 23.5, -3.0), (6.5, 26.0, 8.0), clara, dens=D)
    p.caja(g, "cadera", (-8.0, 10.5, 6.5), (8.0, 21.0, 17.0), piedra, dens=D)
    p.caja(g, "lomo_cadera", (-5.5, 20.5, 7.5), (5.5, 22.5, 16.0), clara, dens=D)
    # la cola: tramos que se afilan y bajan
    for i, (z0, z1, w, y0, y1) in enumerate(COLA):
        p.caja("Body/cola", f"cola{i}", (-w, y0, z0), (w, y1, z1), piedra if i % 2 == 0 else clara, dens=D)


def picos(p):
    amatista = voxel(AMATISTA, 0.1)
    for i, (z, y, h, w) in enumerate(PICOS_CENTRO):
        p.malla("Body/picos", f"centro{i}", esquirla((0.0, y - 0.5, z), w, h, (-28, 0, 0)), amatista, dens=D)
    for i, (x, z, y, h, w) in enumerate(PICOS_LADO):
        for s in (1, -1):
            p.malla("Body/picos", f"lado{i}_{s}", esquirla((s * x, y - 0.5, z), w, h, (-22, 0, -s * 30)), amatista,
                    dens=D)
    # los picos de la cola: arriba (echados atras) y a los lados (hacia afuera), cada vez mas chicos
    for i, (z0, z1, w, y0, y1) in enumerate(COLA):
        z = (z0 + z1) / 2
        h = 7.0 - i * 1.1
        p.malla("Body/cola", f"pico_cola{i}", esquirla((0.0, y1 - 0.4, z), w * 0.7, h, (-35, 0, 0)), amatista,
                dens=D)
        if i < 5:
            for s in (1, -1):
                p.malla("Body/cola", f"pico_cola_lado{i}_{s}",
                        esquirla((s * (w - 0.4), (y0 + y1) / 2 + 1.0, z), w * 0.5, h * 0.7, (-30, 0, -s * 70)),
                        amatista, dens=D)


def patas(p):
    piedra, clara, garra = voxel(PIEDRA, 0.05), voxel(PIEDRA_C, 0.05), voxel(GARRA, 0.1)
    for s in (1, -1):
        # las de enfrente, enormes y abiertas
        h = "RightArm" if s > 0 else "LeftArm"
        a, b = sorted((s * 7.5, s * 15.0))
        p.caja(f"{h}/pata", "hombro", (a, 15.0, -16.0), (b, 25.0, -5.0), clara, dens=D)
        a, b = sorted((s * 9.0, s * 15.5))
        p.caja(f"{h}/pata", "brazo", (a, 4.0, -15.0), (b, 16.0, -7.0), piedra, rot=(0, 0, s * 8),
               piv=(s * 12.0, 16.0, -11.0), dens=D)
        a, b = sorted((s * 9.5, s * 17.5))
        p.caja(f"{h}/pata", "mano", (a, 0.0, -18.0), (b, 4.0, -7.0), clara, dens=D)
        for k, x in enumerate((10.5, 13.5, 16.5)):
            a, b = sorted((s * (x - 0.9), s * (x + 0.9)))
            p.caja(f"{h}/pata", f"garra{k}", (a, 0.0, -20.5), (b, 2.2, -17.5), garra, dens=D)
        # las de atras, mas chicas
        h = "RightLeg" if s > 0 else "LeftLeg"
        a, b = sorted((s * 6.0, s * 12.5))
        p.caja(f"{h}/pata", "muslo", (a, 8.0, 7.5), (b, 19.0, 16.5), clara, dens=D)
        a, b = sorted((s * 7.0, s * 12.0))
        p.caja(f"{h}/pata", "pierna", (a, 2.5, 9.5), (b, 9.5, 15.5), piedra, dens=D)
        a, b = sorted((s * 6.5, s * 13.0))
        p.caja(f"{h}/pata", "pie", (a, 0.0, 6.5), (b, 3.0, 15.5), clara, dens=D)
        for k, x in enumerate((8.0, 11.5)):
            a, b = sorted((s * (x - 0.8), s * (x + 0.8)))
            p.caja(f"{h}/pata", f"garra{k}", (a, 0.0, 4.5), (b, 1.8, 6.8), garra, dens=D)


def construir():
    p = Personaje("jefe_piedra", altura=32)
    p.m.luz_desde = LUZ_SIMETRICA
    cabeza(p)
    cuerpo(p)
    picos(p)
    patas(p)
    p.m.pivotes.update({"Head": (0.0, 18.0, -14.0), "Body": (0.0, 18.0, 0.0), "Body/cola": (0.0, 15.0, 16.0),
                        "RightArm": (11.0, 22.0, -10.5), "LeftArm": (-11.0, 22.0, -10.5),
                        "RightLeg": (9.0, 17.0, 12.0), "LeftLeg": (-9.0, 17.0, 12.0)})
    return p


def escalar(p, k):
    """Crece todo el jefe k veces desde el piso (para llevarlo al tamano del Ender Dragon)."""
    from .chibi import achibar
    return achibar(p, cabeza=k, cuerpo=(k, k, k), cuello=0.0)
