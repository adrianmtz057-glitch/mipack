"""
Lo que acompana a Khaset en el mod (GeckoLib), con la misma paleta y la misma textura de bloques que el:
  - cristal(): el CRISTAL DEL SACRIFICIO. Una piedra de sacrificio azteca (techcatl) de tezontle, la piedra
    volcanica roja de los templos, sobre un zocalo de basalto con una franja de piramides escalonadas de oro sobre
    turquesa; la cara de arriba es abombada (la presa se acuesta de espaldas, arqueada) con un canal oscuro. Encima,
    a 6 bloques, flota un cristal de obsidiana con grietas de brasa (como las manos de Khaset) y dos aros de oro y
    turquesa que giran a su alrededor. Khaset lleva ahi a sus presas.
  - dardo(): el dardo del atlatl: una de las plumas de su abanico (turquesa con la punta verde y el filete naranja)
    con una punta de obsidiana.
  - xiuhcoatl(): la XIUHCOATL, la serpiente de fuego (en codices: turquesa, el cuerpo en placas, el hocico
    enroscado hacia arriba y la cola de rayos de sol). Cabeza con la mandibula aparte, diez tramos que se angostan
    (cada uno un hueso: el mod los encadena para que siga el camino de la cabeza) y la cola de fuego.
Unidades: px a escala 1 (16 px = 1 bloque); en el juego se dibujan tal cual (el cristal y el dardo) o al doble
(la serpiente). Frente = -Z.
"""

import math

from .. import malla as geo
from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .bloques import BAYER, voxel
from .khaset import FUEGO, ORO, TURQUESA, NEGRO, CARBON, grieta, medio_ancho_pluma, pluma

TEZONTLE = tonos("#7E3A2C")
BASALTO = tonos("#3B3337")
OBSIDIANA = tonos("#24141E")
SANGRE = tonos("#4C1014")
VERDE = tonos("#2E7D4F")

# medidas del cristal del sacrificio (px)
ZOCALO = (20.0, 3.0, 14.0)              # medio largo (x), alto, medio ancho (z)
PIEDRA = ((16.0, 10.0), (14.0, 8.0), 15.0, 17.6)   # medio largo y medio ancho abajo y arriba, alto de los lados, del lomo
ALTO_CRISTAL = 96.0                     # centro del cristal (6 bloques)
CRISTAL = (7.0, 14.0, 12.0)             # radio, punta de arriba, punta de abajo
ANILLO = (11.5, 10.0, 1.4)              # radio de afuera, de adentro y grosor


def _tezontle(claro=0.0):
    """Tezontle: la textura de bloques de la piedra con poros oscuros (siempre los mismos)."""
    base = voxel(TEZONTLE, claro)
    poro = hex_(TEZONTLE["s2"])

    def p(t):
        u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
        v = t.z if t.cara in ("up", "down") else t.y
        cu, cv = math.floor(u * 2 + 100), math.floor(v * 2 + 100)
        if math.sin(cu * 1.7 + cv * 2.3) * math.sin(cu * 0.6 - cv * 1.3) > 0.82:
            return poro
        return base(t)
    return p


ESCALON = ("...##...",
           "..####..",
           ".######.",
           "########")


def _zocalo(t):
    """Basalto con una franja de piramides escalonadas de oro sobre turquesa en los lados."""
    if t.cara in ("up", "down"):
        return voxel(BASALTO)(t)
    u = t.x if abs(t.n[2]) >= abs(t.n[0]) else t.z
    fila = int((ZOCALO[1] - t.y) * 2)                          # dos texeles por px de alto (dens 2)
    if 1 <= fila <= 4:
        col = math.floor(u * 2 + 100) % 8
        return hex_(ORO["b"] if ESCALON[fila - 1][col] == "#" else TURQUESA["s"])
    return hex_(ORO["s"]) if fila in (0, 5) else voxel(BASALTO)(t)


def _piedra(t):
    """Los lados de la piedra: tezontle con una greca tallada arriba y abajo y, al centro de los lados largos, un
    disco de sol con un mosaico de turquesa."""
    tez = _tezontle()
    if t.cara == "down":
        return tez(t)
    alto = t.y - ZOCALO[1]
    largo = abs(t.n[2]) >= abs(t.n[0])
    if t.cara != "up" and abs(t.n[1]) < 0.6:
        u = t.x if largo else t.z
        if 1.0 < alto < 2.0 or PIEDRA[2] - ZOCALO[1] - 2.5 < alto < PIEDRA[2] - ZOCALO[1] - 1.5:
            return hex_(TEZONTLE["s2"] if math.floor(u * 2 + 100) % 4 < 2 else TEZONTLE["s"])
        if largo:
            d = math.hypot(t.x, alto - 6.0)
            if d < 4.2:
                if d < 1.6:
                    return hex_(ORO["l"])
                if d < 3.0:
                    return hex_(TURQUESA["b"] if math.floor((math.atan2(alto - 6.0, t.x) + 4) * 8 / math.pi) % 2
                                else TURQUESA["l"])
                return hex_(ORO["b"])
    return tez(t)


def _lomo(t):
    """La cara de arriba: tezontle gastado con un canal oscuro a lo largo y manchas viejas."""
    tez = _tezontle(0.1)
    if abs(t.z) < 0.9 and abs(t.x) < PIEDRA[1][0] - 2:
        return hex_(SANGRE["s"] if math.floor(t.x * 2 + 100) % 3 else SANGRE["s2"])
    if math.sin(t.x * 0.9 + 1.0) * math.sin(t.z * 1.3) > 0.7:
        return hex_(SANGRE["b"])
    return tez(t)


def _obsidiana(t):
    """Obsidiana con grietas de brasa (las de las manos de Khaset, mas grandes) que arden mas en el centro, y los
    cantos de las caras un poco mas claros."""
    k = abs(t.y - ALTO_CRISTAL) / CRISTAL[1]
    if grieta(t.x * 0.75 + 3.0, t.y * 0.75, t.z * 0.75 - 2.0):
        return hex_(FUEGO["h"] if k < 0.2 else FUEGO["l"] if k < 0.5 else FUEGO["b"] if k < 0.8 else FUEGO["s"])
    if t.j < 1 or t.i < 1:
        return hex_(OBSIDIANA["l"])
    f = (BAYER[math.floor(t.j) % 4][math.floor(t.i) % 4] + 0.5) / 16
    if k < 0.3 and f < 0.25:
        return hex_(SANGRE["l"])                               # el fuego de adentro se asoma en el centro
    return hex_(OBSIDIANA["b"] if f < 0.7 else OBSIDIANA["s"])


def _aro(t):
    """Aro de oro con una linea de turquesa al centro."""
    r = math.hypot(t.x, t.y - ALTO_CRISTAL) if abs(t.n[2]) > 0.7 else 0
    if abs(t.n[2]) > 0.7 and abs(r - (ANILLO[0] + ANILLO[1]) / 2) < 0.35:
        return hex_(TURQUESA["l"])
    return voxel(ORO, 0.15)(t)


def cristal():
    p = Personaje("cristal_sacrificio")
    hx, h, hz = ZOCALO
    p.caja("piedra", "zocalo", (-hx, 0, -hz), (hx, h, hz), _zocalo, dens=2)
    (bx, bz), (ax, az), y1, y2 = PIEDRA
    anillo_ab = [(bx, h, bz), (bx, h, -bz), (-bx, h, -bz), (-bx, h, bz)][::-1]
    anillo_ar = [(ax, y1, az), (ax, y1, -az), (-ax, y1, -az), (-ax, y1, az)][::-1]
    p.malla("piedra", "techcatl", geo.tronco(_ccw(anillo_ab), _ccw(anillo_ar), tapa_arriba=False), _piedra, dens=2)
    # el lomo abombado: dos faldones que suben a una arista a lo largo (x)
    lomo = geo.Armador()
    a = [lomo.v(q) for q in ((ax, y1, az), (ax, y1, -az), (-ax, y1, -az), (-ax, y1, az))]
    c = [lomo.v(q) for q in ((ax - 1.0, y2, 0.0), (-ax + 1.0, y2, 0.0))]
    lomo.cara((a[1], a[2], c[1], c[0]), (0, 1, -1), "lomo")
    lomo.cara((a[3], a[0], c[0], c[1]), (0, 1, 1), "lomo")
    lomo.cara((a[0], a[1], c[0]), (1, 1, 0), "lomo")
    lomo.cara((a[2], a[3], c[1]), (-1, 1, 0), "lomo")
    p.malla("piedra", "lomo", (lomo.vs, lomo.caras), _lomo, dens=2)
    # el cristal y sus aros
    r, up, dn = CRISTAL
    p.malla("cristal", "obsidiana", geo.bipiramide((0.0, ALTO_CRISTAL, 0.0), r, up, dn, lados=6, giro=0.0),
            _obsidiana, dens=3)
    re, ri, g = ANILLO
    aro = geo.mover(geo.aro(re, ri, g, lados=12), (0.0, ALTO_CRISTAL, 0.0))
    p.malla("cristal/anillo_a", "aro_a", geo.girar(aro, (0.0, 0.0, 20.0), (0.0, ALTO_CRISTAL, 0.0)), _aro, dens=2)
    p.malla("cristal/anillo_b", "aro_b", geo.girar(aro, (0.0, 90.0, -20.0), (0.0, ALTO_CRISTAL, 0.0)), _aro, dens=2)
    p.m.pivotes = {"piedra": (0.0, 0.0, 0.0), "cristal": (0.0, ALTO_CRISTAL, 0.0),
                   "cristal/anillo_a": (0.0, ALTO_CRISTAL, 0.0), "cristal/anillo_b": (0.0, ALTO_CRISTAL, 0.0)}
    return p


def _ccw(pts):
    """Ordena un anillo antihorario visto desde arriba (de +X hacia -Z), como lo pide geo.tronco."""
    cx = sum(q[0] for q in pts) / len(pts)
    cz = sum(q[2] for q in pts) / len(pts)
    return sorted(pts, key=lambda q: math.atan2(-(q[2] - cz), q[0] - cx))


# ---------------------------------------------------------------- el dardo

LARGO_DARDO = 26.0


def dardo():
    """La pluma del abanico convertida en dardo, apuntando al frente (-Z): punta de obsidiana adelante, astil de oro
    y la pluma atras (dos planos en cruz, asi se ve de cualquier lado)."""
    p = Personaje("dardo")
    L = LARGO_DARDO
    largo_pluma, ancho = 15.0, 2.6
    pin = pluma(0.0, largo_pluma, ancho, TURQUESA, FUEGO, (VERDE["b"], VERDE["s2"]))
    z0 = L / 2 - largo_pluma

    def plano_pluma(t):
        # pluma() mide a lo largo en y desde el canon: aqui el canon va adelante (z0, en el astil) y la punta atras
        x = t.x if abs(t.n[0]) < 0.5 else t.y
        q = type("T", (), {})()
        q.x, q.y = x, t.z - z0
        return pin(q)
    p.plano("dardo", "pluma_h", (-ancho, 0.0, z0), (ancho, 0.0, L / 2), plano_pluma, dens=4)
    p.plano("dardo", "pluma_v", (0.0, -ancho, z0), (0.0, ancho, L / 2), plano_pluma, dens=4)
    p.caja("dardo", "astil", (-0.35, -0.35, -L / 2 + 3.0), (0.35, 0.35, z0 + 1.0), voxel(ORO, 0.1), dens=4)
    punta = geo.girar(geo.bipiramide((0.0, 0.0, 0.0), 0.9, 3.6, 0.8, lados=4, giro=45.0), (-90.0, 0.0, 0.0))
    p.malla("dardo", "punta", geo.mover(punta, (0.0, 0.0, -L / 2 + 3.2)), _punta_obsidiana, dens=4)
    p.m.pivotes = {"dardo": (0.0, 0.0, 0.0)}
    return p


def _punta_obsidiana(t):
    return hex_(OBSIDIANA["l"] if t.j == 0 else OBSIDIANA["b"])


# ---------------------------------------------------------------- la Xiuhcoatl

TRAMOS = 9                              # tramos del cuerpo detras de la cabeza
LARGO_TRAMO = 8.0
CABEZA_X = (6.0, 9.0, 14.0)             # medio ancho, alto y largo de la cabeza


def _medida_tramo(k):
    """Medio ancho y alto del tramo k (0 = el pegado a la cabeza): se angosta hacia la cola."""
    f = k / (TRAMOS - 1)
    return 5.5 - 3.0 * f, 8.5 - 4.5 * f


def flama(t_u, t_v):
    """Silueta de una flama recortada (u de -1 a 1 de costado, v de 0 abajo a 1 la punta): tres lenguas.
    Devuelve el color o TRANSPARENTE."""
    v = max(0.0, min(1.0, t_v))
    borde = (1.0 - v) ** 0.75 * (0.75 + 0.25 * math.sin(v * 9.0 + 1.0))
    lengua = 0.35 * max(0.0, math.sin(v * math.pi)) * math.cos(t_u * 5.0 + v * 6.0)
    if abs(t_u) > borde + lengua * (v > 0.3):
        return TRANSPARENTE
    r = abs(t_u) / max(1e-6, borde)
    if v > 0.85 or r > 0.85:
        return hex_(FUEGO["s"])
    if r < 0.35 and v < 0.6:
        return hex_(FUEGO["h"])
    return hex_(FUEGO["l"] if r < 0.6 else FUEGO["b"])


def _fuego(p, grupo, nombre, desde, hasta, rot=None, piv=None, dens=3):
    """Un plano de flama: sin luz horneada (es fuego, ya trae su color y brilla en lo oscuro)."""
    p.m.cubo(grupo, nombre, desde, hasta, _flama_plano(desde, hasta), rot, piv, dens=dens, luz=False)


def _flama_plano(desde, hasta):
    """Pintor de flama para un plano vertical de 'desde' a 'hasta' (la flama sube en y)."""
    (x0, y0, z0), (x1, y1, z1) = desde, hasta
    ancho_z = abs(z1 - z0) > abs(x1 - x0)

    def p(t):
        if ancho_z:
            u = (t.z - (z0 + z1) / 2) / max(1e-6, abs(z1 - z0) / 2)
        else:
            u = (t.x - (x0 + x1) / 2) / max(1e-6, abs(x1 - x0) / 2)
        return flama(u, (t.y - y0) / max(1e-6, y1 - y0))
    return p


def _placas(t):
    """El cuerpo: turquesa en placas (arriba, rayas de contorno cada 4 px y el lomo mas claro), una banda de oro al
    frente de cada tramo y la panza de fuego."""
    if t.cara == "down":
        return hex_(FUEGO["b"] if math.floor(t.z + 100) % 3 else FUEGO["s"])
    zl = (t.z - t.f[2])
    if zl < 1.0:
        return voxel(ORO, 0.1)(t)
    if t.cara == "up":
        if math.floor(t.z * 2 + 100) % 8 == 0:
            return hex_(TURQUESA["o"])
        return hex_(TURQUESA["l"] if abs(t.x) < 1.2 else TURQUESA["b"] if abs(t.x) < 3.2 else TURQUESA["s"])
    if t.y - t.f[1] < 1.2:
        return hex_(FUEGO["s"])                                # la orilla de la panza
    if math.floor(t.z * 2 + 100) % 8 == 0:
        return hex_(TURQUESA["o"])
    return voxel(TURQUESA)(t)


def _cabeza_x(t):
    """La cabeza: turquesa con el contorno de las placas y la ceja de oro."""
    if t.cara == "down":
        return hex_(TURQUESA["s2"])
    if t.cara == "up" and math.floor(t.z * 2 + 100) % 6 == 0:
        return hex_(TURQUESA["o"])
    return voxel(TURQUESA, 0.05)(t)


def _ojo_x(t):
    """Ojo de fuego: amarillo al centro, naranja y una orilla roja."""
    u, v = t.i / max(1, t.tw - 1) - 0.5, t.j / max(1, t.th - 1) - 0.5
    d = math.hypot(u, v)
    return hex_(FUEGO["h"] if d < 0.22 else FUEGO["l"] if d < 0.42 else FUEGO["s"])


def _colmillo(t):
    return hex_("#E6DAC0" if t.j < t.th - 1 else "#B9A98A")


def _boca(t):
    return hex_("#3A0A0E")


def xiuhcoatl():
    p = Personaje("xiuhcoatl")
    hx, hy, hz = CABEZA_X
    G = "cabeza"
    # craneo (la parte de arriba de la boca) y el hocico enroscado hacia arriba
    p.caja(G, "craneo", (-hx, 3.0, -hz), (hx, hy, 0.0), _cabeza_x, dens=2)
    p.caja(G, "frente", (-hx + 1.0, hy, -hz + 2.0), (hx - 1.0, hy + 1.5, -3.0), _cabeza_x, dens=2)
    p.caja(G, "nariz", (-3.0, 4.0, -hz - 3.0), (3.0, 8.0, -hz), _cabeza_x, dens=2)
    p.cadena(G, "enrosca", (0.0, 7.5, -hz - 1.5), [(0.0, 15.0), (0.0, 35.0), (0.0, 40.0), (0.0, 45.0), (0.0, 50.0)],
             2.6, 4.2, _cabeza_x, achica=0.86, dens=2)
    for s in (1, -1):
        lado = "der" if s > 0 else "izq"
        x0, x1 = sorted((s * hx, s * (hx + 0.6)))
        p.caja(f"{G}/ojos", f"ojo_{lado}", (x0, 5.5, -hz + 3.0), (x1, 8.0, -hz + 6.5), _ojo_x, dens=4)
        x0, x1 = sorted((s * (hx - 1.5), s * (hx + 1.0)))
        p.caja(G, f"ceja_{lado}", (x0, 8.0, -hz + 2.0), (x1, 9.5, -hz + 8.0), voxel(ORO, 0.1), dens=2)
        x0, x1 = sorted((s * 3.6, s * 4.8))
        p.caja(G, f"colmillo_{lado}", (x0, 1.0, -hz + 0.4), (x1, 3.0, -hz + 1.6), _colmillo, dens=4)
        # la cresta de flamas a los lados de la nuca
        x = s * (hx - 0.5)
        _fuego(p, G, f"cresta_{lado}", (x, hy - 2.0, -5.0), (x, hy + 7.0, 1.0), rot=(0.0, 0.0, s * -25.0),
               piv=(x, hy - 2.0, -2.0))
    p.caja(G, "paladar", (-hx + 0.5, 2.8, -hz + 0.2), (hx - 0.5, 3.2, -1.0), _boca, dens=2)
    p.caja(G, "collar", (-hx - 0.4, 2.0, -1.5), (hx + 0.4, hy + 0.6, 0.5), voxel(ORO, 0.12), dens=2)
    # la mandibula (se abre) con la lengua de fuego
    M = f"{G}/mandibula"
    p.caja(M, "mandibula", (-hx + 0.8, 0.0, -hz + 0.6), (hx - 0.8, 2.6, -1.0), _cabeza_x, dens=2)
    _fuego(p, M, "lengua", (-1.2, 2.6, -hz - 2.0), (1.2, 2.6, -4.0))
    # el cuerpo: cada tramo cuelga del anterior
    ruta = ""
    z = 0.0
    for k in range(TRAMOS):
        ruta = f"{ruta}/s{k + 1}" if ruta else f"s{k + 1}"
        w, h = _medida_tramo(k)
        p.caja(ruta, f"tramo_{k + 1}", (-w, 0.0, z - 0.4), (w, h, z + LARGO_TRAMO), _placas, dens=2)
        y0 = h - 0.5
        _fuego(p, ruta, f"flama_{k + 1}", (0.0, y0, z + 1.0), (0.0, y0 + 2.5 + 0.6 * h, z + LARGO_TRAMO - 0.5))
        p.m.pivotes[ruta] = (0.0, h / 2, z)
        z += LARGO_TRAMO
    # la cola de rayos: una placa de oro y tres flamas que se abren
    C = f"{ruta}/cola"
    w, h = _medida_tramo(TRAMOS - 1)
    p.caja(C, "placa", (-w - 1.0, 0.0, z - 0.4), (w + 1.0, h + 1.0, z + 2.0), voxel(ORO, 0.15), dens=2)
    for i, giro in enumerate((-35.0, 0.0, 35.0)):
        _fuego(p, C, f"rayo_{i}", (0.0, 0.5, z + 1.0), (0.0, 11.0, z + 7.0), rot=(-50.0, 0.0, giro),
               piv=(0.0, 2.0, z + 1.0))
    p.m.pivotes.update({G: (0.0, 5.0, 0.0), M: (0.0, 2.8, -1.5), f"{G}/ojos": (0.0, 5.0, 0.0), C: (0.0, h / 2, z)})
    for k in [k for k in list(p.m.pivotes) if k in ("Head", "Body", "RightArm", "LeftArm", "RightLeg", "LeftLeg")]:
        del p.m.pivotes[k]
    return p


def astilla():
    """El dardo de la fase 2 (ya sin penacho): una astilla de obsidiana con grietas de brasa, apuntando al frente."""
    p = Personaje("astilla")
    L = LARGO_DARDO * 0.8
    cuerpo = geo.girar(geo.bipiramide((0.0, 0.0, 0.0), 1.6, L * 0.62, L * 0.38, lados=5, giro=18.0), (-90.0, 0.0, 0.0))

    def pin(t):
        if grieta(t.x * 2.2 + 1.0, t.y * 2.2, t.z * 1.1):
            return hex_(FUEGO["l"] if abs(t.z) < L * 0.2 else FUEGO["b"])
        return hex_(OBSIDIANA["l"] if t.j == 0 else OBSIDIANA["b"])
    p.malla("dardo", "astilla", cuerpo, pin, dens=4)
    p.m.pivotes = {"dardo": (0.0, 0.0, 0.0)}
    return p


# ---------------------------------------------------------------- animaciones (GeckoLib)

from .. import animar                                    # noqa: E402
from ..animar import facil, suave                        # noqa: E402
from .crackatos_anim import Pose                         # noqa: E402


def cristal_quieto(rig):
    """Flota subiendo y bajando; el cristal gira despacio (60 grados por vuelta: tiene 6 caras, cierra sin brinco) y
    los aros giran al reves."""
    T = 4.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        p.pos("cristal", y=2.0 * math.sin(w))
        p.rot("cristal", ry=60.0 * t / T)
        p.rot("anillo_a", ry=-360.0 * t / T)
        p.rot("anillo_b", rx=360.0 * t / T)
        return p
    return T, pose, True


def cristal_llama(rig):
    """Khaset trae una presa: el cristal baja un poco, gira rapido y tiembla; los aros dan vueltas (en bucle)."""
    T = 1.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        p.pos("cristal", y=-6.0 + 0.6 * math.sin(4 * w), x=0.25 * math.sin(7 * w))
        p.rot("cristal", ry=120.0 * t / T)
        p.rot("anillo_a", ry=-360.0 * t / T, rz=10.0 * math.sin(w))
        p.rot("anillo_b", rx=360.0 * t / T)
        return p
    return T, pose, True


def cristal_sacrificio(rig):
    """Recibe el corazon: baja de golpe, sube con un tiron, da una vuelta entera y vuelve a su altura (se acompana
    con el destello y las particulas del mod)."""
    L = 2.0

    def pose(t):
        p = Pose()
        y = suave(t, [(0.0, -6.0), (0.25, -14.0), (0.55, 8.0), (1.2, 4.0), (L, 0.0)])
        p.pos("cristal", y=y)
        p.rot("cristal", ry=360.0 * facil(t / 1.4))
        p.rot("anillo_a", ry=-720.0 * facil(t / L), rz=25.0 * math.sin(math.pi * min(1.0, t / 1.2)))
        p.rot("anillo_b", rx=720.0 * facil(t / L))
        return p
    return L, pose, False


def _tramos():
    return [f"s{k + 1}" for k in range(TRAMOS)]


def xiuhcoatl_reptar(rig):
    """Repta: una onda que corre de la cabeza a la cola (cada tramo gira respecto al anterior), la cabeza compensa
    para mirar al frente y la boca se abre a ratos."""
    T = 1.0
    A = 16.0

    def pose(t):
        w = 2 * math.pi * t / T
        p = Pose()
        for k, h in enumerate(_tramos()):
            fase = w - (k + 1) * 0.75
            fase0 = w - k * 0.75
            p.rot(h, ry=A * (math.sin(fase) - (math.sin(fase0) if k else 0.0)))
        p.rot("cola", ry=A * 0.8 * math.sin(w - (TRAMOS + 1) * 0.75), rx=8.0 * math.sin(2 * w))
        boca = 8.0 + 8.0 * max(0.0, math.sin(w))
        p.rot("cabeza", ry=-A * 0.5 * math.sin(w - 0.75), rx=3.0 + 0.4 * boca + 2.0 * math.sin(2 * w))
        p.pos("cabeza", y=0.25 * boca)                       # al abrir la boca la cabeza se levanta: no muerde el piso
        p.rot("mandibula", rx=-boca)
        return p
    return T, pose, True


def xiuhcoatl_surgir(rig):
    """Sale del piso de golpe con la cabeza en alto y la boca abierta (rugido) y se tiende a reptar."""
    L = 1.2

    def pose(t):
        p = Pose()
        sube = facil(t / 0.45)
        alza = suave(t, [(0.0, 0.0), (0.4, 1.0), (0.8, 1.0), (L, 0.0)])
        p.pos("s1", y=-16.0 * (1 - sube))
        p.rot("cabeza", rx=40.0 * alza)
        p.rot("mandibula", rx=-30.0 * alza)
        for k, h in enumerate(_tramos()[:4]):
            p.rot(h, rx=(-14.0 if k == 0 else 6.0) * alza)
        return p
    return L, pose, "hold_on_last_frame"


def xiuhcoatl_morder(rig):
    """Lanza la cabeza al frente con la boca abierta y la cierra de golpe (a los 0.3 s)."""
    L = 0.7

    def pose(t):
        p = Pose()
        lanza = suave(t, [(0.0, 0.0), (0.2, 1.0), (0.35, 1.0), (L, 0.0)])
        boca = suave(t, [(0.0, 0.0), (0.18, 1.0), (0.3, 0.0), (L, 0.0)])
        p.pos("cabeza", z=-5.0 * lanza, y=2.0 * lanza + 10.0 * boca)
        p.rot("cabeza", rx=10.0 * lanza + 6.0 * boca)
        p.rot("mandibula", rx=-40.0 * boca)
        p.rot("s1", rx=-8.0 * lanza)
        return p
    return L, pose, False


def xiuhcoatl_deshacer(rig):
    """Se apaga: baja la cabeza y se hunde en el piso hecha brasas (se queda abajo)."""
    L = 1.0

    def pose(t):
        p = Pose()
        u = facil(t / L)
        p.pos("s1", y=-16.0 * u)
        p.rot("cabeza", rx=-20.0 * u)
        p.rot("mandibula", rx=-10.0 * u)
        return p
    return L, pose, "hold_on_last_frame"


ANIM_CRISTAL = {"quieto": cristal_quieto, "llamando": cristal_llama, "sacrificio": cristal_sacrificio}
ANIM_XIUHCOATL = {"reptar": xiuhcoatl_reptar, "surgir": xiuhcoatl_surgir, "morder": xiuhcoatl_morder,
                  "deshacer": xiuhcoatl_deshacer}


def hornear(rig, anims):
    out = {}
    for nombre, f in anims.items():
        largo, pose, bucle = f(rig)
        datos, cuadros = animar.hornear(rig, nombre, largo, pose, bucle)
        out[nombre] = (datos, cuadros, bucle)
    return out
