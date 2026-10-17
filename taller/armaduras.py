"""
Las armaduras con forma propia (no recolores): modelos de cubos para GeckoLib (GeoArmorRenderer), cada una en el
estilo del server, con su textura pintada texel a texel.
Huesos (los que busca GeckoLib, con los pivotes del player): armorHead, armorBody, armorRightArm, armorLeftArm,
armorRightLeg, armorLeftLeg, armorRightBoot, armorLeftBoot. Que se ve con cada pieza: casco -> armorHead; pechera
-> armorBody y los brazos; pantalon -> las piernas; botas -> las botas.
Ejes del kit: frente -Z, derecha del personaje +X, pies en y = 0, 16 px por bloque. El player: cabeza de y 24 a 32,
cuerpo de 12 a 24 (z de -2 a 2), brazos de x 4 a 8, piernas de x 0 a 4.
Uso: python -m taller.armaduras [ids...]  ->  salida/armaduras/<id>.png (puesta en un maniqui) y hoja.png
"""

import math
import os
import sys

from . import modelo as kit
from . import vista
from .luz import paso
from .modelo import Modelo
from .textura import TRANSPARENTE, azar, hex_a_rgba as hex_, mezcla

SALIDA = os.path.join(os.path.dirname(__file__), "..", "salida", "armaduras")
D = 2                                               # texeles por px (como los bichos)

PIVOTES = {"armorHead": (0, 24, 0), "armorBody": (0, 24, 0), "armorRightArm": (5, 22, 0),
           "armorLeftArm": (-5, 22, 0), "armorRightLeg": (2, 12, 0), "armorLeftLeg": (-2, 12, 0),
           "armorRightBoot": (2, 12, 0), "armorLeftBoot": (-2, 12, 0)}
kit.ESPEJO_HUESO.update({"armorRightArm": "armorLeftArm", "armorLeftArm": "armorRightArm",
                         "armorRightLeg": "armorLeftLeg", "armorLeftLeg": "armorRightLeg",
                         "armorRightBoot": "armorLeftBoot", "armorLeftBoot": "armorRightBoot"})
CAB, CUE, BRA, PIE, BOT = "armorHead", "armorBody", "armorRightArm", "armorRightLeg", "armorRightBoot"


# ====================================================================== pintura

def _uv(t):
    """(u, v) en px sobre la cara: u a lo ancho, v hacia arriba (en las de arriba y abajo, v es z)."""
    if t.cara in ("north", "south"):
        return t.x, t.y
    if t.cara in ("east", "west"):
        return t.z, t.y
    return t.x, t.z


def _caja_uv(t):
    """Lo que mide la cara en (u, v): (u0, u1, v0, v1)."""
    f, h = t.f, t.t
    if t.cara in ("north", "south"):
        return f[0], h[0], f[1], h[1]
    if t.cara in ("east", "west"):
        return f[2], h[2], f[1], h[1]
    return f[0], h[0], f[2], h[2]


def _grano(c, t, k=0.05, sem=0):
    a = azar(round(t.x * 2), round(t.y * 2), round(t.z * 2), sem)
    return paso(c, 1) if a > 1 - k * 4 else paso(c, -1) if a < k * 4 else c


def _canto(c, t, abajo=True, arriba=True):
    """Oscurece la fila de abajo y aclara la de arriba de las caras laterales (volumen de la pieza)."""
    if t.cara in ("up", "down"):
        return c
    u0, u1, v0, v1 = _caja_uv(t)
    if abajo and t.y - v0 < 0.5:
        return paso(c, -1)
    if arriba and v1 - t.y < 0.5:
        return paso(c, 1)
    return c


def liso(color, k=0.04, sem=0, cantos=True):
    c0 = hex_(color)

    def p(t):
        c = _grano(c0, t, k, sem)
        return _canto(c, t) if cantos else c
    return p


def oro(color="#E3B04B"):
    """Metal: brillo arriba, sombra abajo y algun destello."""
    c0 = hex_(color)

    def p(t):
        u0, u1, v0, v1 = _caja_uv(t)
        u, v = _uv(t)
        r = (v - v0) / max(1e-6, v1 - v0)
        c = paso(c0, 1) if r > 0.7 else paso(c0, -1) if r < 0.25 else c0
        if azar(round(u * 2), round(v * 2), 7) > 0.93:
            c = paso(c0, 2)
        return c
    return p


def rayas(c1, c2, ancho=0.75, vertical=False):
    a, b = hex_(c1), hex_(c2)

    def p(t):
        u, v = _uv(t)
        k = int(math.floor((u if vertical else v) / ancho + 1000))
        return _canto(a if k % 2 else b, t)
    return p


def tablero(c1, c2, lado=0.75):
    a, b = hex_(c1), hex_(c2)

    def p(t):
        u, v = _uv(t)
        k = int(math.floor(u / lado + 1000)) + int(math.floor(v / lado + 1000))
        return _canto(a if k % 2 else b, t)
    return p


def plisado(color, hem="#E3B04B", linea=0.75):
    """Lino plisado (rayas verticales finas) con el ruedo de oro."""
    c0, ch = hex_(color), hex_(hem)

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        if t.cara not in ("up", "down") and v - v0 < 0.5:
            return ch
        if t.cara not in ("up", "down") and ((u / linea) % 1.0) < 0.34:
            return paso(c0, -1)
        return _grano(c0, t, 0.015)
    return p


def cuentas(colores, banda=0.75, gotas=True, cuello=None):
    """Collar ancho de cuentas (usekh): bandas que bajan desde arriba, cada cuenta su brillo, y abajo gotas
    colgando (lo de entre gotas, transparente). cuello: (ancho, hondo) del hueco del cuello en la cara de arriba y en la
    de adelante."""
    cs = [hex_(c) for c in colores]

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        if t.cara in ("up", "down"):
            if cuello and abs(t.x) < cuello[0] and abs(t.z) < 2.3:
                return TRANSPARENTE
            return cs[0]
        if cuello and t.cara in ("north", "south") and abs(t.x) < cuello[0] and v1 - v < cuello[1]:
            return TRANSPARENTE
        baja = v1 - v
        if gotas and v - v0 < 1.0:                       # la ultima fila: gotas
            fu = (u / 1.0) % 1.0
            alto = 1.0 - (v - v0)
            if abs(fu - 0.5) > 0.32 * (1.1 - alto * 0.6):
                return TRANSPARENTE
            return paso(cs[-1], 1 if fu < 0.5 else 0)
        c = cs[int(baja / banda) % len(cs)]
        return paso(c, 1) if (u / 0.5) % 2 < 1 else c
    return p


def plumas(base, punta, oscuro=None, ancho=3.0, alto=4.0, cortar=True):
    """Plumas encimadas en filas (como tejas), cada fila corrida media pluma: la pluma con la punta redonda y su
    orilla oscura, el raquis al centro y la punta del color de punta; abajo de la pieza, lo que queda entre las puntas
    es transparente."""
    cb, cp = hex_(base), hex_(punta)
    co = hex_(oscuro) if oscuro else paso(cb, -2)

    def celda(lu, lv, fila):
        x = lu + (ancho / 2 if fila % 2 else 0.0)
        cu = ((x % ancho) / ancho) * 2 - 1                 # -1 a 1 a lo ancho de la pluma
        cv = lv / alto - fila                              # 0 arriba, 1 abajo
        return cu, cv

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        if t.cara in ("up", "down"):
            return _grano(cb, t)
        lu, lv = u - u0, v1 - v
        fila = int(lv / alto)
        cu, cv = celda(lu, lv, fila)
        dentro = cv < 0.55 or cu * cu + ((cv - 0.55) / 0.45) ** 2 <= 1.0
        if not dentro:                                     # se ve la pluma de la fila de abajo (su parte de arriba)
            if cortar and v - v0 < alto * 0.5:
                return TRANSPARENTE
            fila += 1
            cu, cv = celda(lu, lv, fila)
        borde = cu * cu + ((max(cv, 0.55) - 0.55) / 0.45) ** 2
        c = mezcla(cb, cp, max(0.0, (cv - 0.62) / 0.38))
        if azar(int(math.floor((lu + (ancho / 2 if fila % 2 else 0.0)) / ancho)), fila, 4) > 0.55:
            c = paso(c, -1)
        if borde > 0.62 and cv > 0.25:
            return paso(c, -2)
        if abs(cu) > 0.86:
            return paso(c, -1)
        if abs(cu) < 0.1 and cv > 0.1:
            return paso(co, 1)
        if -0.75 < cu < -0.3 and cv < 0.6:
            return paso(c, 1)
        return c
    return p


def pluma_sola(base, punta, largo="z", desde_alto=False):
    """Una pluma suelta en un plano (penachos, alitas): forma de pluma con su raquis, lo de afuera transparente.
    largo: eje a lo largo de la pluma ('z' o 'y'); la base es el lado chico del eje (o el grande si desde_alto)."""
    cb, cp = hex_(base), hex_(punta)

    def p(t):
        f, h = t.f, t.t
        ia = {"x": 0, "y": 1, "z": 2}[largo]
        a = (getattr(t, largo) - f[ia]) / max(1e-6, h[ia] - f[ia])
        if desde_alto:
            a = 1 - a
        otro = 1 if largo != "y" else (2 if t.cara in ("east", "west") else 0)
        if t.cara in ("east", "west") and largo == "z":
            otro = 1
        b = ((getattr(t, "xyz"[otro]) - f[otro]) / max(1e-6, h[otro] - f[otro])) * 2 - 1
        ancho = 0.95 * math.sin(math.pi * min(1.0, a * 1.1) ** 0.75) if a < 0.97 else 0.0
        if abs(b) > ancho:
            return TRANSPARENTE
        if abs(b) < 0.12:
            return paso(cb, -2)
        c = mezcla(cb, cp, max(0.0, (a - 0.55) / 0.45))
        return paso(c, -1) if (a * 9 + abs(b) * 2) % 1.0 < 0.25 else c
    return p


def quitina(base, brillo, oscuro, banda=None):
    """Placa de exoesqueleto lustrosa y abombada: clara arriba, oscura abajo, con un destello en diagonal y la junta
    oscura en la orilla de abajo. banda: si la placa se parte en segmentos de ese alto."""
    cb, cl, co = hex_(base), hex_(brillo), hex_(oscuro)

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        mu = (u - u0) / max(1e-6, u1 - u0)
        if t.cara in ("up", "down"):
            mv = (v - v0) / max(1e-6, v1 - v0)
            d = math.hypot(mu - 0.4, mv - 0.4)
            return paso(cb, 2) if d < 0.12 else mezcla(cl, cb, min(1.0, d * 1.6))
        if banda:
            r = 1 - ((v1 - v) % banda) / banda
            alto = banda
        else:
            r = (v - v0) / max(1e-6, v1 - v0)
            alto = v1 - v0
        if r * alto < 0.5:
            return co
        if r > 0.78:
            c = mezcla(cb, cl, (r - 0.78) / 0.22)
        elif r < 0.35:
            c = mezcla(co, cb, r / 0.35)
        else:
            c = cb
        if 0.18 < (mu + r * 0.5) % 1.0 < 0.26:
            c = paso(c, 2)
        return c
    return p


def placas(color, linea, columnas=2, filas=4):
    """Una cara partida en placas rectangulares (el plastron de la tortuga): lineas oscuras y el centro mas claro."""
    c0, cl = hex_(color), hex_(linea)

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        fu = (u - u0) / max(1e-6, u1 - u0) * columnas
        fv = (v - v0) / max(1e-6, v1 - v0) * filas
        du, dv = abs((fu % 1.0) - 0.5), abs((fv % 1.0) - 0.5)
        if t.cara in ("north", "south") and (du > 0.42 or dv > 0.4):
            return cl
        return paso(c0, 1) if du < 0.2 and dv < 0.2 else _grano(c0, t, 0.02)
    return p


def escamas(base, borde, claro=None, ancho=2.0, alto=1.5):
    """Escamas en filas encontradas: la orilla de abajo de cada una oscura y el centro mas claro."""
    cb, cbo = hex_(base), hex_(borde)
    cc = hex_(claro) if claro else paso(cb, 1)

    def p(t):
        u, v = _uv(t)
        fila = int(math.floor(v / alto + 1000))
        lu = u + (ancho / 2 if fila % 2 else 0.0)
        cu = (lu % ancho) / ancho * 2 - 1
        cv = (v % alto) / alto
        if cv < 0.25 + 0.5 * cu * cu:
            return cbo
        return cc if cv > 0.7 and abs(cu) < 0.4 else _grano(cb, t, 0.02)
    return p


def caparazon(base, linea, claro, lado=2.0):
    """Escudos hexagonales del caparazon: lineas oscuras entre placas, el centro de cada placa mas claro."""
    cb, cl, cc = hex_(base), hex_(linea), hex_(claro)

    def p(t):
        u, v = _uv(t)
        w = lado * math.sqrt(3)
        fila = int(math.floor(v / (lado * 1.5) + 1000))
        lu = u + (w / 2 if fila % 2 else 0.0)
        cu = (lu % w) / w * 2 - 1
        cv = (v % (lado * 1.5)) / (lado * 1.5) * 2 - 1
        d = max(abs(cu), (abs(cu) * 0.5 + abs(cv) * 0.866))
        if d > 0.86:
            return cl
        if d < 0.35:
            return cc
        return _canto(_grano(cb, t, 0.03), t)
    return p


def pelaje(base, oscuro, fleco=True):
    """Pelo grueso: mechones verticales de distinto tono y, abajo de la pieza, fleco disparejo (transparente)."""
    cb, co = hex_(base), hex_(oscuro)

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        col = int(math.floor(u * 2 + 1000))
        a = azar(col, 3)
        if fleco and t.cara not in ("up", "down") and v - v0 < 0.9 * a:
            return TRANSPARENTE
        c = mezcla(cb, co, 0.15 + 0.5 * azar(col, int(v * 1.5), 5))
        if azar(col, int(v * 4), 9) > 0.85:
            c = paso(c, 1)
        return c
    return p


def cuero(color, costura="#C9A27A"):
    c0, cs = hex_(color), hex_(costura)

    def p(t):
        u, v = _uv(t)
        u0, u1, v0, v1 = _caja_uv(t)
        if t.cara not in ("up", "down") and (abs(v - v0 - 0.75) < 0.25 or abs(v1 - v - 0.75) < 0.25):
            return cs if (u * 2) % 2 < 1 else c0
        return _canto(_grano(c0, t, 0.02), t)
    return p


def ventana(pintor, dentro):
    """El pintor, pero transparente donde dentro(t) (el hueco de la cara en una capucha, etc.)."""
    def p(t):
        return TRANSPARENTE if dentro(t) else pintor(t)
    return p


# ====================================================================== maniqui (solo para las vistas)

PIEL, PELO, ROPA = "#B07A55", "#2E2620", "#5C5650"


def maniqui(m):
    piel, pelo, ropa = hex_(PIEL), hex_(PELO), hex_(ROPA)

    def cabeza(t):
        if t.cara == "north" and 26.5 < t.y < 27.6 and 0.8 < abs(t.x) < 2.2:
            return hex_("#1A1410")
        if t.y > 30.5 or (t.cara in ("south", "up")) or (t.cara in ("east", "west") and t.y > 28.5):
            return pelo
        return piel

    def short(t):
        return ropa if t.y > 7.5 else piel
    m.cubo("Head", "cabeza", (-4, 24, -4), (4, 32, 4), cabeza)
    m.cubo("Body", "cuerpo", (-4, 12, -4 + 2), (4, 24, 2), lambda t: ropa if t.y < 14 else piel)
    m.par("RightArm", "brazo", (4, 12, -2), (8, 24, 2), lambda t: piel)
    m.par("RightLeg", "pierna", (0, 0, -2), (4, 12, 2), short)


# ====================================================================== armaduras

LINO, LAPIS, ORO, TURQUESA, TERRACOTA = "#E9DDBF", "#2A4E9C", "#E3B04B", "#2F9FA8", "#B5532F"


def desierto(m):
    """Velkia, egipcia y abierta (por eso no sofoca): tocado nemes a rayas de lapislazuli y oro con la cobra al
    frente y la cola de tela atras; collar ancho de cuentas sobre el pecho descubierto con hombreras de cuentas,
    brazaletes y munequeras; faldellin de lino plisado con cinturon a cuadros y paño al frente; sandalias con
    tobillera de oro."""
    nemes = rayas(LAPIS, ORO, 0.75)
    m.cubo(CAB, "casquete", (-4.6, 28.4, -4.6), (4.6, 32.7, 4.7), nemes, dens=D)
    m.cubo(CAB, "frente", (-4.75, 28.2, -4.8), (4.75, 29.2, -4.55), oro(), dens=D)
    m.par(CAB, "aleta", (4.55, 23.8, -3.7), (5.4, 29.0, -0.6), nemes, dens=D)
    m.par(CAB, "aleta_pecho", (2.5, 19.6, -3.6), (5.4, 24.2, -2.75), nemes, dens=D)
    m.par(CAB, "aleta_borde", (2.45, 19.2, -3.65), (5.45, 19.7, -2.7), oro(), dens=D)
    m.cubo(CAB, "cola", (-3.2, 22.2, 4.5), (3.2, 29.0, 5.2), nemes, dens=D)
    m.cubo(CAB, "cola_atada", (-1.4, 20.4, 4.6), (1.4, 22.3, 5.1), oro(), dens=D)
    m.cubo(CAB, "cobra", (-0.4, 29.0, -5.15), (0.4, 31.0, -4.6), oro(), dens=D)
    m.cubo(CAB, "cobra_capucha", (-0.85, 30.3, -5.3), (0.85, 31.6, -4.95), oro("#D49A34"), dens=D)
    collar = cuentas((ORO, LAPIS, ORO, TURQUESA, TERRACOTA, ORO), cuello=(2.3, 1.2))
    m.cubo(CUE, "collar", (-5.0, 20.0, -2.75), (5.0, 24.15, -2.15), collar, dens=D)
    m.cubo(CUE, "collar_atras", (-5.0, 21.0, 2.15), (5.0, 24.15, 2.75), collar, dens=D)
    m.cubo(CUE, "collar_arriba", (-5.0, 24.0, -2.75), (5.0, 24.6, 2.75), collar, dens=D)
    m.par(BRA, "hombrera", (3.9, 22.4, -2.65), (8.45, 24.6, 2.65), cuentas((ORO, TURQUESA, LAPIS, ORO), gotas=True), dens=D)
    m.par(BRA, "brazalete", (3.55, 18.4, -2.45), (8.45, 19.7, 2.45), oro(), dens=D)
    m.par(BRA, "brazalete_piedra", (3.5, 18.75, -2.5), (8.5, 19.35, 2.5), liso(LAPIS), dens=D)
    m.par(BRA, "munequera", (3.55, 12.4, -2.45), (8.45, 14.6, 2.45), rayas(ORO, LAPIS, 0.55), dens=D)
    m.par(PIE, "cinturon", (-0.1, 10.6, -2.6), (4.6, 12.6, 2.6), tablero(LAPIS, ORO), dens=D)
    m.par(PIE, "faldellin", (-0.05, 5.4, -2.55), (4.55, 10.7, 2.55), plisado(LINO), dens=D)
    m.par(PIE, "pano", (-0.05, 4.0, -2.95), (2.3, 10.7, -2.55), plisado("#F2E8CF", ORO, 0.6), dens=D)
    m.par(BOT, "suela", (-0.3, 0.0, -2.9), (4.3, 0.5, 2.3), liso("#9C6B42"), dens=D)
    m.par(BOT, "tira", (-0.15, 0.45, -2.75), (4.15, 1.1, -1.7), cuero("#7A4E2C"), dens=D)
    m.par(BOT, "tira_empeine", (1.55, 0.45, -2.35), (2.45, 2.3, -1.95), liso("#7A4E2C"), dens=D)
    m.par(BOT, "tobillera", (-0.25, 2.0, -2.35), (4.25, 2.8, 2.35), oro(), dens=D)


COBRE, CREMA, CAFE_OSC, CUERO = "#B8693A", "#EFE3CC", "#5A3A24", "#7A5234"


def plumas_set(m):
    """Plumas (halcon de cobre): casco de plumas con penacho que se va atras y plumas en las sienes; manto de plumas
    en tres filas sobre la espalda y hombreras de plumas encimadas; arneses de cuero cruzados con broche; pantalon de
    cuero con mechones de pluma en la cadera; botas de cuero con alitas en el tobillo."""
    pl = plumas(COBRE, CAFE_OSC)
    m.cubo(CAB, "gorro", (-4.6, 28.0, -4.6), (4.6, 32.8, 4.6), plumas(COBRE, CAFE_OSC, ancho=2.0, alto=2.5), dens=D)
    m.cubo(CAB, "ceja", (-4.75, 29.2, -5.25), (4.75, 30.4, -4.55), cuero(CAFE_OSC, COBRE), dens=D)
    m.cubo(CAB, "pico", (-0.6, 28.4, -5.7), (0.6, 30.2, -5.0), liso("#E8D9A8"), dens=D)
    for k, (x, alto, giro) in enumerate(((0.0, 7.0, 0.0), (-1.2, 6.0, -10.0), (1.2, 6.0, 10.0), (-2.3, 4.8, -20.0),
                                        (2.3, 4.8, 20.0))):
        m.cubo(CAB, f"penacho{k}", (x, 32.4, 0.6), (x, 32.4 + alto, 3.0), pluma_sola(COBRE, CREMA, largo="y"),
               rot=(-38.0, 0.0, giro), origen=(x, 32.4, 1.8), dens=D)
    m.par(CAB, "sien", (4.62, 28.6, -0.5), (4.62, 31.6, 4.0), pluma_sola(CREMA, CAFE_OSC, largo="z"),
          rot=(0.0, 18.0, 0.0), origen=(4.62, 30.0, -0.5), dens=D)
    m.cubo(CUE, "manto1", (-5.2, 19.0, 2.2), (5.2, 24.4, 3.0), pl, dens=D)
    m.cubo(CUE, "manto2", (-5.6, 15.0, 2.6), (5.6, 20.2, 3.4), plumas(mezcla_hex(COBRE, CAFE_OSC), CAFE_OSC), dens=D)
    m.cubo(CUE, "manto3", (-5.9, 10.8, 3.0), (5.9, 16.2, 3.8), plumas(CAFE_OSC, "#2A1A10"), dens=D)
    m.cubo(CUE, "cuello", (-4.4, 23.6, -2.6), (4.4, 24.6, 2.6), plumas(CREMA, COBRE, cortar=False), dens=D)
    for s in (1, -1):
        m.cubo(CUE, f"arnes{s}", (-0.45, 12.4, -2.6), (0.45, 24.4, -2.2), cuero(CUERO), rot=(0.0, 0.0, 30.0 * s),
               origen=(0.0, 18.4, -2.4), dens=D)
    m.cubo(CUE, "broche", (-1.0, 17.4, -2.85), (1.0, 19.4, -2.45), oro("#C9873A"), dens=D)
    m.par(BRA, "hombro1", (3.6, 21.6, -2.8), (8.7, 24.7, 2.8), plumas(CREMA, COBRE, ancho=2.0, alto=2.5), dens=D)
    m.par(BRA, "hombro2", (3.9, 19.0, -3.0), (8.9, 22.3, 3.0), pl, dens=D)
    m.par(BRA, "brazal", (3.6, 12.4, -2.5), (8.4, 15.4, 2.5), cuero(CUERO), dens=D)
    m.par(PIE, "pantalon", (-0.3, 3.6, -2.45), (4.45, 12.3, 2.45), cuero(CUERO), dens=D)
    m.par(PIE, "mechon", (4.5, 6.8, -1.6), (4.5, 11.8, 1.6), pluma_sola(CREMA, COBRE, largo="y", desde_alto=True),
          rot=(0.0, 0.0, -14.0), origen=(4.5, 11.8, 0.0), dens=D)
    m.par(BOT, "bota", (-0.35, 0.0, -2.7), (4.35, 4.0, 2.45), cuero(CAFE_OSC, COBRE), dens=D)
    m.par(BOT, "borde", (-0.45, 3.4, -2.55), (4.45, 4.5, 2.55), plumas(CREMA, COBRE, cortar=False, ancho=1.5, alto=1.1), dens=D)
    for k, (alto, largo, giro) in enumerate(((3.4, 4.8, -24.0), (2.8, 4.0, -8.0), (2.2, 3.2, 8.0))):
        m.par(BOT, f"alita{k}", (4.5, 2.4, 0.2), (4.5, 2.4 + alto, 0.2 + largo), pluma_sola(CREMA, COBRE, largo="z"),
              rot=(giro, 12.0, 0.0), origen=(4.5, 3.2, 0.2), dens=D)


def mezcla_hex(a, b, t=0.5):
    c = mezcla(hex_(a), hex_(b), t)
    return "#%02X%02X%02X" % c[:3]


QUI, QUI_BRILLO, QUI_OSC, AMBAR = "#7A3B22", "#C9792E", "#3B1C12", "#F2B33A"


def quitina_set(m):
    """Quitina (de la ramita): exoesqueleto de placas segmentadas; casco con cresta, visera de mandibulas, ojos de
    ambar y antenas cortas; pecho de bandas encimadas como abdomen de insecto; hombreras como elitros; muslos de
    placas con rodillera; grebas segmentadas con garras."""
    q = quitina(QUI, QUI_BRILLO, QUI_OSC)
    m.cubo(CAB, "domo", (-4.7, 27.8, -4.7), (4.7, 33.0, 4.7), quitina(QUI, QUI_BRILLO, QUI_OSC, banda=2.6), dens=D)
    m.cubo(CAB, "cresta", (-0.6, 32.8, -4.2), (0.6, 33.7, 4.4), liso(QUI_OSC), dens=D)
    m.cubo(CAB, "visera", (-4.9, 28.6, -5.3), (4.9, 30.2, -4.6), q, dens=D)
    m.par(CAB, "ojo", (1.9, 28.85, -5.45), (3.9, 30.0, -5.2), oro(AMBAR), dens=D)
    m.par(CAB, "mandibula", (1.0, 25.3, -5.6), (4.4, 26.5, -4.7), q, rot=(0.0, 18.0, -6.0), origen=(4.4, 26.0, -4.9), dens=D)
    m.par(CAB, "mandibula_punta", (0.3, 25.0, -6.4), (1.5, 26.0, -5.4), liso(QUI_OSC), rot=(0.0, 18.0, -6.0),
          origen=(4.4, 26.0, -4.9), dens=D)
    m.par(CAB, "antena", (1.2, 32.6, -4.5), (1.7, 36.4, -4.0), liso(QUI_OSC), rot=(-28.0, 0.0, -16.0),
          origen=(1.45, 32.6, -4.25), dens=D)
    for k in range(4):
        y1 = 24.3 - 3.0 * k
        z = 2.7 + 0.14 * (3 - k)
        m.cubo(CUE, f"banda{k}", (-4.9 + 0.15 * k, y1 - 3.4, -z), (4.9 - 0.15 * k, y1, -2.15), q, dens=D)
        m.cubo(CUE, f"banda_atras{k}", (-4.9 + 0.15 * k, y1 - 3.4, 2.15), (4.9 - 0.15 * k, y1, z), q, dens=D)
    m.par(BRA, "elitro", (3.5, 20.0, -2.95), (8.9, 24.9, 2.95), q, dens=D)
    m.par(BRA, "elitro_orilla", (3.7, 19.4, -3.1), (9.1, 20.4, 3.1), liso(QUI_BRILLO), dens=D)
    m.par(BRA, "brazal", (3.55, 12.3, -2.5), (8.45, 16.6, 2.5), quitina(QUI, QUI_BRILLO, QUI_OSC, banda=2.1), dens=D)
    m.par(PIE, "muslo", (-0.25, 7.0, -2.55), (4.55, 12.4, 2.55), quitina(QUI, QUI_BRILLO, QUI_OSC, banda=2.7), dens=D)
    m.par(PIE, "rodillera", (0.6, 4.9, -3.15), (3.4, 7.5, -2.4), quitina(QUI_BRILLO, AMBAR, QUI), dens=D)
    m.par(BOT, "greba", (-0.35, 0.0, -2.75), (4.35, 5.2, 2.6), quitina(QUI, QUI_BRILLO, QUI_OSC, banda=2.6), dens=D)
    for k in range(3):
        m.par(BOT, f"garra{k}", (0.3 + 1.3 * k, 0.0, -3.7), (1.0 + 1.3 * k, 0.8, -2.7), liso(QUI_OSC), dens=D)


TORTUGA, TORTUGA_OSC, TORTUGA_CLARO, PLASTRON = "#4E8A3A", "#2F5A26", "#9FC25A", "#D9C77A"


def tortuga_set(m):
    """Tortuga (el casco es el de Minecraft): caparazon en domo en la espalda con escudos hexagonales y plastron
    claro adelante; escamas en hombros, antebrazos y piernas; rodilleras de escudo; botas con aletas palmeadas."""
    cap = caparazon(TORTUGA, TORTUGA_OSC, TORTUGA_CLARO)
    m.cubo(CUE, "caparazon1", (-4.8, 12.8, 2.1), (4.8, 23.8, 3.6), cap, dens=D)
    m.cubo(CUE, "caparazon2", (-4.0, 14.2, 3.5), (4.0, 22.4, 4.6), cap, dens=D)
    m.cubo(CUE, "caparazon3", (-2.8, 15.6, 4.5), (2.8, 21.0, 5.2), cap, dens=D)
    m.cubo(CUE, "plastron", (-4.4, 12.6, -2.75), (4.4, 23.4, -2.15), placas(PLASTRON, "#8A7A3E"), dens=D)
    m.cubo(CUE, "costados", (-4.6, 13.2, -2.3), (4.6, 23.0, 2.3), liso(TORTUGA_OSC), dens=D)
    m.par(BRA, "hombro", (3.6, 20.6, -2.6), (8.6, 24.5, 2.6), escamas(TORTUGA, TORTUGA_OSC, TORTUGA_CLARO), dens=D)
    m.par(BRA, "antebrazo", (3.6, 12.4, -2.5), (8.4, 16.0, 2.5), escamas(TORTUGA, TORTUGA_OSC, TORTUGA_CLARO), dens=D)
    m.par(PIE, "pierna", (-0.25, 4.0, -2.55), (4.5, 12.4, 2.55), escamas(TORTUGA, TORTUGA_OSC, TORTUGA_CLARO), dens=D)
    m.par(PIE, "rodilla", (0.5, 5.2, -3.05), (3.5, 7.6, -2.5), caparazon(TORTUGA_CLARO, TORTUGA_OSC, PLASTRON, 1.2), dens=D)
    m.par(BOT, "bota", (-0.35, 0.0, -2.7), (4.35, 3.6, 2.5), escamas(TORTUGA_OSC, "#1E3A18", TORTUGA), dens=D)

    def aleta(t):
        u, v = t.x, t.z
        fx = (u + 0.8) / 5.6                            # 0 a 1 a lo ancho
        fz = (-2.0 - v) / 4.2                           # 0 junto al pie, 1 en la punta
        lobulo = abs(((fx * 3.0) % 1.0) - 0.5) * 2      # tres dedos
        if fz > 0.55 + 0.45 * (1 - lobulo):
            return TRANSPARENTE
        if lobulo < 0.18 and fz > 0.1:
            return hex_(TORTUGA_OSC)
        return mezcla(hex_(TORTUGA), hex_(TORTUGA_CLARO), fz * 0.6)
    m.par(BOT, "aleta", (-0.8, 0.15, -6.2), (4.8, 0.15, -2.0), aleta, dens=D)


PELO_HIELO, PELO_OSC, CUERO_OSC, MARFIL = "#C9D3D8", "#8D9AA3", "#3D2B22", "#EFE6D0"


def pelaje_set(m):
    """Pelaje (frio de las Montañas): capucha de pelaje de Iskarum con orilla gruesa de pelo alrededor de la cara y
    colmillos; abrigo grueso con cuello de pelo, cinturon y botones de colmillo; mangas de pelo con puños oscuros;
    pantalon de cuero con banda de pelo; botas peludas."""
    pel = pelaje(PELO_HIELO, PELO_OSC)
    hueco = lambda t: t.cara == "north" and abs(t.x) < 3.4 and 26.4 < t.y < 31.1      # noqa: E731
    m.cubo(CAB, "capucha", (-4.9, 26.4, -4.5), (4.9, 33.4, 5.0), ventana(pelaje(PELO_HIELO, PELO_OSC, fleco=False), hueco), dens=D)
    m.cubo(CAB, "orilla_arriba", (-4.95, 31.0, -5.2), (4.95, 32.5, -4.4), pelaje(MARFIL, PELO_HIELO, fleco=False), dens=D)
    m.par(CAB, "orilla_lado", (3.4, 25.6, -5.2), (5.15, 32.5, -4.4), pelaje(MARFIL, PELO_HIELO), dens=D)
    m.par(CAB, "colmillo", (4.7, 24.6, -4.7), (5.3, 26.8, -4.1), liso(MARFIL), rot=(28.0, 0.0, 0.0),
          origen=(5.0, 26.8, -4.4), dens=D)
    m.cubo(CUE, "abrigo", (-5.0, 10.8, -3.0), (5.0, 24.4, 3.0), pel, dens=D)
    m.cubo(CUE, "frente", (-0.9, 11.0, -3.15), (0.9, 23.0, -2.95), cuero(CUERO_OSC, PELO_OSC), dens=D)
    for k in range(3):
        m.cubo(CUE, f"boton{k}", (-0.35, 15.0 + 2.8 * k, -3.6), (0.35, 16.4 + 2.8 * k, -3.1), liso(MARFIL), dens=D)
    m.cubo(CUE, "cuello", (-5.6, 22.6, -3.6), (5.6, 25.4, 3.6),
           ventana(pelaje(MARFIL, PELO_HIELO), lambda t: t.cara in ("up", "down") and abs(t.x) < 3.4 and abs(t.z) < 2.6), dens=D)
    m.cubo(CUE, "cinturon", (-5.1, 13.0, -3.1), (5.1, 14.4, 3.1), cuero(CUERO_OSC), dens=D)
    m.par(BRA, "manga", (3.4, 15.4, -2.8), (8.6, 24.6, 2.8), pel, dens=D)
    m.par(BRA, "puno", (3.3, 12.0, -3.0), (8.7, 14.6, 3.0), pelaje(PELO_OSC, "#5E6A72"), dens=D)
    m.par(PIE, "pantalon", (-0.3, 3.6, -2.5), (4.45, 12.4, 2.5), cuero(CUERO_OSC, PELO_OSC), dens=D)
    m.par(PIE, "banda", (-0.45, 5.0, -2.75), (4.6, 6.8, 2.75), pelaje(PELO_HIELO, PELO_OSC), dens=D)
    m.par(BOT, "bota", (-0.6, 0.6, -2.9), (4.6, 5.0, 2.7), pel, dens=D)
    m.par(BOT, "suela", (-0.65, 0.0, -2.95), (4.65, 0.6, 2.75), liso(CUERO_OSC), dens=D)


HIELO, HIELO_CLARO, HIELO_OSC, ESCARCHA = "#9FD8EE", "#E8FAFF", "#4E8FB5", "#CFEFFA"
NEGRO_T, NEGRO_T2, ACERO_T, MURA_T = "#1C1A20", "#2E2B34", "#4A4752", "#6B2E8C"


def hielo_set(m):
    """Hielo (Kemira, contra Khaset): yelmo de hielo con corona de picos de cristal y visera abierta; peto de placas
    de hielo con escarcha y un cristal grande al centro; hombreras con picos de hielo que salen hacia arriba;
    faldar de laminas; grebas de hielo con picos en la rodilla."""
    placa = quitina(HIELO, HIELO_CLARO, HIELO_OSC)
    hueco = lambda t: t.cara == "north" and abs(t.x) < 2.9 and 25.4 < t.y < 29.6      # noqa: E731
    m.cubo(CAB, "yelmo", (-4.6, 24.6, -4.6), (4.6, 32.5, 4.6), ventana(placa, hueco), dens=D)
    for k, (x, alto) in enumerate(((-3.2, 2.4), (-1.2, 3.6), (0.8, 3.6), (2.8, 2.4))):
        m.cubo(CAB, f"pico{k}", (x - 0.45, 32.3, -3.2), (x + 0.45, 32.3 + alto, -2.3), liso(HIELO_CLARO), dens=D)
    m.cubo(CAB, "nasal", (-0.45, 26.2, -4.95), (0.45, 29.6, -4.5), liso(HIELO_OSC), dens=D)
    m.cubo(CUE, "peto", (-4.7, 12.4, -2.85), (4.7, 24.3, 2.85), placas(HIELO, HIELO_OSC, 2, 4), dens=D)
    m.cubo(CUE, "cristal", (-1.3, 17.5, -3.4), (1.3, 21.5, -2.8), liso(HIELO_CLARO), dens=D)
    m.cubo(CUE, "escarcha", (-4.8, 12.0, -2.95), (4.8, 13.2, 2.95), liso(ESCARCHA), dens=D)
    m.par(BRA, "hombrera", (3.6, 21.4, -2.9), (8.8, 24.8, 2.9), placa, dens=D)
    m.par(BRA, "pico_hombro", (6.0, 24.6, -0.6), (7.2, 27.6, 0.6), liso(HIELO_CLARO), rot=(0.0, 0.0, -18.0),
          origen=(6.6, 24.6, 0.0), dens=D)
    m.par(BRA, "brazal", (3.5, 12.2, -2.55), (8.5, 16.4, 2.55), placas(HIELO, HIELO_OSC, 1, 2), dens=D)
    m.par(PIE, "faldar", (-0.2, 7.6, -2.65), (4.6, 12.6, 2.65), rayas(HIELO, HIELO_OSC, 0.75, vertical=True), dens=D)
    m.par(BOT, "greba", (-0.4, 0.0, -2.75), (4.4, 6.2, 2.6), placa, dens=D)
    m.par(BOT, "pico_rodilla", (1.4, 5.0, -3.4), (2.6, 7.4, -2.6), liso(HIELO_CLARO), dens=D)


def tanque_set(m):
    """Tanque (el que aguanta el centro): todo pesado y negro. Yelmo cerrado con rendija morada y cresta; peto
    grueso de placas con remaches de oro; hombreras enormes de tres laminas; guanteletes; quijotes y grebas
    gruesas con rodilleras; botas de placas anchas."""
    placa = placas(NEGRO_T, "#0E0D11", 2, 3)
    rendija = lambda t: t.cara == "north" and abs(t.x) < 3.2 and 27.6 < t.y < 28.6      # noqa: E731
    m.cubo(CAB, "yelmo", (-4.9, 24.2, -4.9), (4.9, 33.0, 4.9), ventana(quitina(NEGRO_T, ACERO_T, "#0E0D11"), rendija), dens=D)
    m.cubo(CAB, "rendija", (-3.2, 27.6, -4.7), (3.2, 28.6, -4.5), liso(MURA_T), dens=D)
    m.cubo(CAB, "cresta", (-0.6, 32.8, -4.0), (0.6, 34.6, 4.4), liso(MURA_T), dens=D)
    m.cubo(CUE, "peto", (-5.0, 11.6, -3.2), (5.0, 24.6, 3.2), placa, dens=D)
    for k, (x, y) in enumerate(((-3.6, 22.8), (3.0, 22.8), (-3.6, 13.0), (3.0, 13.0))):
        m.cubo(CUE, f"remache{k}", (x, y, -3.6), (x + 0.6, y + 0.6, -3.1), oro(), dens=D)
    for k in range(3):
        m.par(BRA, f"hombrera{k}", (3.4 + 0.2 * k, 23.0 - 1.6 * k, -3.3 + 0.2 * k), (9.4 - 0.2 * k, 25.4 - 1.6 * k, 3.3 - 0.2 * k),
              quitina(NEGRO_T2, ACERO_T, "#0E0D11"), dens=D)
    m.par(BRA, "guantelete", (3.3, 11.8, -2.8), (8.7, 16.6, 2.8), placa, dens=D)
    m.par(PIE, "quijote", (-0.4, 5.8, -2.9), (4.7, 12.6, 2.9), placa, dens=D)
    m.par(PIE, "rodillera", (0.6, 4.8, -3.4), (3.8, 7.2, -2.8), oro("#9A7A2A"), dens=D)
    m.par(BOT, "bota", (-0.6, 0.0, -3.4), (4.6, 5.4, 2.9), placa, dens=D)


ARMADURAS = {"desierto": desierto, "plumas": plumas_set, "quitina": quitina_set, "tortuga": tortuga_set,
             "pelaje": pelaje_set, "hielo": hielo_set, "tanque": tanque_set}
NOMBRES = {"desierto": "Armadura del desierto", "plumas": "Armadura de plumas", "quitina": "Armadura de quitina",
           "tortuga": "Armadura de tortuga", "pelaje": "Armadura de pelaje", "hielo": "Armadura de hielo",
           "tanque": "Armadura de tanque"}


def armar(ident, con_maniqui=False):
    m = Modelo(ident)
    m.pivotes = dict(PIVOTES)
    if con_maniqui:
        m.pivotes.update(kit.HUESOS)
        maniqui(m)
    ARMADURAS[ident](m)
    return m


def vistas(ident, alto=420):
    m = armar(ident, con_maniqui=True)
    lienzo, uvs = m.pintar()
    ruta = os.path.join(SALIDA, f"{ident}.png")
    vista.guardar_vista(m, lienzo, uvs, ruta, alto_px=alto,
                        vistas=(("3/4", 30, 10), ("frente", 0, 6), ("lado", 90, 6), ("espalda", 180, 8)))
    return ruta


def main(ids):
    from PIL import Image, ImageDraw
    from .bichos.hojas import _fuente
    os.makedirs(SALIDA, exist_ok=True)
    rutas = [(i, vistas(i)) for i in (ids or ARMADURAS)]
    ims = [(i, Image.open(r)) for i, r in rutas]
    w = max(im.width for _, im in ims)
    h = sum(im.height + 34 for _, im in ims)
    hoja = Image.new("RGB", (w, h), (24, 22, 20))
    d = ImageDraw.Draw(hoja)
    y = 0
    for i, im in ims:
        d.text((10, y + 6), NOMBRES[i], fill=(245, 235, 210), font=_fuente(20))
        hoja.paste(im, (0, y + 34))
        y += im.height + 34
    hoja.save(os.path.join(SALIDA, "hoja.png"))
    print(os.path.join(SALIDA, "hoja.png"))


if __name__ == "__main__":
    main(sys.argv[1:])
