"""
Los cuerpos de los bichos: plantillas de cubos (sencillas, a escala de Minecraft: 16 px por bloque, pies en y=0, el
frente a -Z y la derecha a +X), cada una con sus huesos para animarlas despues con un motor comun:
  cuadrupedo  raiz / cuerpo / (cuello / cabeza / (hocico, oreja_*, cuerno_*), cola*), raiz / pata_{dd,di,td,ti}
  ave         raiz / cuerpo / (cuello / cabeza / pico, ala_d, ala_i, cola), raiz / pata_{d,i}
  reptil      raiz / cuerpo / (cabeza / hocico, cola1 / cola2 / cola3), raiz / pata_{dd,di,td,ti}
  serpiente   raiz / s0 (cabeza) ... sN: cada tramo hijo del anterior (para que ondule)
  insecto     raiz / cuerpo / (cabeza / antenas, abdomen, pata_1..6), y sus variantes (escarabajo, palo, escorpion,
              garrapata, cangrejo)
  pez         raiz / cuerpo / (cabeza, cola / aleta_cola, aleta_d, aleta_i)
  murcielago  raiz / cuerpo / (cabeza / oreja_*, ala_d, ala_i), raiz / pata_*
  mono        como cuadrupedo, con brazos largos y la cola alzada
El diseno de cada bicho va en su Piel (piel.py): aqui solo las formas. Las piezas inclinadas (cuernos, cuellos,
patas de insecto) son cubos girados con el giro del cubo, asi la luz horneada cuadra en reposo.
"""

import math

from ..luz import LUZ_SIMETRICA
from ..modelo import Modelo

D = 2                                     # texeles por px


def _rot_hacia(d):
    """Giro (rx, ry, 0) de Blockbench que lleva -Y a la direccion d (unitaria)."""
    dx, dy, dz = d
    a = math.acos(max(-1.0, min(1.0, -dy)))
    if math.sin(a) < 1e-6:
        return (0.0 if dy < 0 else 180.0, 0.0, 0.0)
    b = math.atan2(-dx, -dz)
    return (math.degrees(a), math.degrees(b), 0.0)


def _unit(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def _mas(a, b, k=1.0):
    return tuple(a[i] + b[i] * k for i in range(3))


class Armado:
    """Un modelo en construccion: sus huesos (con pivote) y sus cubos (cada uno pintado por la piel segun su parte)."""

    def __init__(self, ident, piel, escala=1.0):
        self.id = ident
        self.piel = piel
        self.escala = escala                  # cuanto se dibuja mas grande en el juego (las crias de titanes, etc.)
        self.m = Modelo(ident)
        self.m.pivotes = {"raiz": (0.0, 0.0, 0.0)}
        self.m.luz_desde = LUZ_SIMETRICA
        self.m.luz_por = "grupo"

    def hueso(self, ruta, pivote):
        self.m.pivotes[ruta] = tuple(float(v) for v in pivote)
        return ruta

    def caja(self, ruta, nombre, desde, hasta, rot=None, origen=None, caras=None, parte=None):
        parte = parte or nombre.split("_")[0]
        return self.m.cubo(ruta, nombre, desde, hasta, self.piel.pintor(parte), rot=rot, origen=origen, caras=caras,
                           dens=D)

    def centrada(self, ruta, nombre, centro, tam, parte=None, rot=None):
        cx, cy, cz = centro
        w, h, l = tam
        return self.caja(ruta, nombre, (cx - w / 2, cy - h / 2, cz - l / 2), (cx + w / 2, cy + h / 2, cz + l / 2),
                         rot=rot, origen=centro if rot else None, parte=parte)

    def segmento(self, ruta, nombre, p0, p1, ancho, grueso=None, parte=None):
        """Un cubo de p0 a p1 (de seccion ancho x grueso), girado para seguir la linea."""
        grueso = ancho if grueso is None else grueso
        d = tuple(p1[i] - p0[i] for i in range(3))
        largo = math.sqrt(sum(c * c for c in d))
        rot = _rot_hacia(_unit(d))
        x, y, z = p0
        return self.caja(ruta, nombre, (x - ancho / 2, y - largo, z - grueso / 2), (x + ancho / 2, y, z + grueso / 2),
                         rot=rot if any(abs(r) > 1e-3 for r in rot) else None, origen=p0, parte=parte)

    def cadena(self, ruta, nombre, puntos, anchos, parte=None):
        """Segmentos seguidos (una cola, un cuerno curvo): puntos [p0, p1, ...] y el ancho de cada tramo."""
        for k in range(len(puntos) - 1):
            a = anchos[min(k, len(anchos) - 1)]
            self.segmento(ruta, f"{nombre}{k + 1}" if len(puntos) > 2 else nombre, puntos[k], puntos[k + 1], a,
                          parte=parte)

    def ojos(self, caja_cabeza, y, z, r=0.6):
        """Pone los ojos en la cabeza (a los lados, o al frente si la piel lo dice: entonces z es la separacion en x)."""
        f, h = caja_cabeza.desde, caja_cabeza.hasta
        self.piel.ojos[(tuple(f), tuple(h))] = (y, z, r)


# ====================================================================== cuadrupedo

def cuadrupedo(ident, piel, cuerpo=(8, 8, 14), pata=(2.5, 8), cabeza=(5, 5, 5), hocico=(3, 2.5, 3), cuello=None,
               orejas=("punta", 1.4, 2.5), cuernos=None, cola=("corta", 1.5, 3), joroba=None, colmillos=None,
               trompa=None, melena=None, ojo=(1.2, 1.4, 0.6), escala=1.0, patas_atras=None, panza=0.0, alto_extra=0.0,
               cresta=None, collar=None, silla=None):
    """cuerpo: (ancho, alto, largo); pata: (grosor, largo); cuello: (largo, grosor, grados sobre la horizontal);
    orejas: (tipo punta/larga/caida/redonda, ancho, alto); cuernos: (tipo toro/cabra/bufalo/astas/botones, grosor,
    largo); cola: (tipo corta/larga/esponjosa/latigo/alzada, grosor, largo); joroba: (ancho, alto, largo);
    patas_atras: (grosor, largo) si son distintas (liebre, marmota)."""
    a = Armado(ident, piel, escala)
    w, h, l = cuerpo
    g, L = pata
    ga, La = patas_atras or pata
    base = max(L, La) + alto_extra
    a.hueso("raiz/cuerpo", (0, base + h / 2, 0))
    a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
    if panza:
        a.caja("raiz/cuerpo", "panza", (-w / 2 + 0.5, base - panza, -l / 2 + 2), (w / 2 - 0.5, base + 0.5, l / 2 - 2),
               parte="cuerpo")
    if joroba:
        jw, jh, jl = joroba
        a.caja("raiz/cuerpo", "joroba", (-jw / 2, base + h - 0.5, -jl / 2), (jw / 2, base + h + jh, jl / 2), parte="cuerpo")
    if cresta:                                             # una cresta a lo largo del lomo (hielo, puas)
        rw, rh, rl = cresta
        a.caja("raiz/cuerpo", "cresta", (-rw / 2, base + h - 0.2 + (joroba[1] if joroba else 0), -rl / 2),
               (rw / 2, base + h + rh + (joroba[1] if joroba else 0), rl / 2))
    if silla:                                              # la manta de montar sobre el lomo (o la joroba)
        sw, sl = silla
        jh, jl = (joroba[1], joroba[2]) if joroba else (0.0, sl)
        a.caja("raiz/cuerpo", "silla", (-w / 2 - 0.3, base + h - 2.5, -jl / 2 - 0.6), (w / 2 + 0.3, base + h + jh + 0.3, jl / 2 + 0.6))
    if melena:
        mw, mh, ml = melena
        a.caja("raiz/cuerpo", "melena", (-mw / 2, base + h * 0.25, -l / 2 - 0.5), (mw / 2, base + h + mh, -l / 2 + ml),
               parte="cuerpo")
    # patas
    for lado, s in (("d", 1), ("i", -1)):
        for fila, gz, gg, LL in (("d", -l / 2 + g / 2 + 0.6, g, L), ("t", l / 2 - ga / 2 - 0.6, ga, La)):
            x = s * (w / 2 - gg / 2 - 0.4)
            ruta = a.hueso(f"raiz/pata_{fila}{lado}", (x, LL + alto_extra, gz))
            a.caja(ruta, f"pata_{fila}{lado}", (x - gg / 2, 0, gz - gg / 2), (x + gg / 2, LL + alto_extra + 1.0, gz + gg / 2),
                   parte="pata")
    # cuello y cabeza
    hw, hh, hl = cabeza
    frente = (0.0, base + h * 0.72, -l / 2 + 1.0)
    if cuello:
        cl, cg, ang = cuello
        d = (0.0, math.sin(math.radians(ang)), -math.cos(math.radians(ang)))
        fin = _mas(frente, d, cl)
        a.hueso("raiz/cuerpo/cuello", frente)
        a.segmento("raiz/cuerpo/cuello", "cuello", frente, fin, cg, cg, parte="cuello")
        centro = (0.0, fin[1] + hh * 0.15, fin[2] - hl / 2 + 1.0)
        ruta_cab = a.hueso("raiz/cuerpo/cuello/cabeza", fin)
    else:
        centro = (0.0, base + h * 0.75 + hh * 0.25, -l / 2 - hl / 2 + 1.0)
        ruta_cab = a.hueso("raiz/cuerpo/cabeza", (0.0, centro[1] - hh * 0.3, centro[2] + hl / 2))
    cab = a.centrada(ruta_cab, "cabeza", centro, cabeza)
    cx, cy, cz = centro
    if hocico:
        sw, sh, sl = hocico
        a.caja(ruta_cab, "hocico", (-sw / 2, cy - hh / 2, cz - hl / 2 - sl), (sw / 2, cy - hh / 2 + sh, cz - hl / 2 + 0.01))
    if piel.ojos_al_frente:                                # al frente: ojo[0] es la separacion en x
        a.ojos(cab, cy + hh / 2 - ojo[1], ojo[0], ojo[2])
    else:
        a.ojos(cab, cy + hh / 2 - ojo[1], cz - hl / 2 + ojo[0], ojo[2])
    if collar:
        a.caja(ruta_cab, "collar", (-hw / 2 - 0.3, cy - hh / 2 - 0.2, cz + hl / 2 - 1.2), (hw / 2 + 0.3, cy - hh / 2 + 0.8, cz + hl / 2 + 0.3))
    # orejas
    if orejas:
        tipo, ow, oh = orejas
        for s in (1, -1):
            base_o = (s * (hw / 2 - ow / 2), cy + hh / 2 - 0.3, cz + hl / 2 - ow / 2 - 0.5)
            if tipo == "punta":
                fin = _mas(base_o, _unit((s * 0.45, 1.0, 0.15)), oh)
                a.segmento(ruta_cab, f"oreja_{'d' if s > 0 else 'i'}", base_o, fin, ow, 0.6, parte="oreja")
            elif tipo == "larga":
                fin = _mas(base_o, _unit((s * 0.18, 1.0, 0.25)), oh)
                a.segmento(ruta_cab, f"oreja_{'d' if s > 0 else 'i'}", base_o, fin, ow, 0.6, parte="oreja")
            elif tipo == "caida":
                b2 = (s * (hw / 2 + 0.2), cy + hh / 2 - 0.6, cz)
                fin = _mas(b2, _unit((s * 0.8, -0.6, 0.1)), oh)
                a.segmento(ruta_cab, f"oreja_{'d' if s > 0 else 'i'}", b2, fin, ow, 0.6, parte="oreja")
            elif tipo == "redonda":
                a.centrada(ruta_cab, f"oreja_{'d' if s > 0 else 'i'}", (s * (hw / 2 - ow / 2 + 0.2), cy + hh / 2 + oh / 2 - 0.2,
                                                                         cz + hl / 4), (ow, oh, 0.8), parte="oreja")
    # cuernos
    if cuernos:
        tipo, cg, cl = cuernos
        for s in (1, -1):
            lado = "d" if s > 0 else "i"
            b0 = (s * (hw / 2 - cg / 2), cy + hh / 2 - 0.2, cz - hl / 6)
            if tipo == "toro":
                pts = [b0, _mas(b0, (s * cl * 0.55, cl * 0.1, 0)), _mas(b0, (s * cl * 0.8, cl * 0.5, -cl * 0.3))]
            elif tipo == "bufalo":
                pts = [b0, _mas(b0, (s * cl * 0.6, -cl * 0.05, cl * 0.1)), _mas(b0, (s * cl, cl * 0.45, -cl * 0.1))]
            elif tipo == "cabra":
                pts = [b0, _mas(b0, (s * cl * 0.1, cl * 0.55, cl * 0.25)), _mas(b0, (s * cl * 0.25, cl * 0.7, cl * 0.75)),
                       _mas(b0, (s * cl * 0.35, cl * 0.45, cl * 1.05))]
            elif tipo == "astas":
                pts = [b0, _mas(b0, (s * cl * 0.25, cl * 0.6, cl * 0.15)), _mas(b0, (s * cl * 0.5, cl, cl * 0.1))]
                a.segmento(ruta_cab, f"asta_{lado}_rama", pts[1], _mas(pts[1], (s * cl * 0.05, cl * 0.35, -cl * 0.3)), cg * 0.8,
                           parte="asta")
            else:                                            # botones
                pts = [b0, _mas(b0, (s * cl * 0.2, cl, 0))]
            anchos = [cg, cg * 0.8, cg * 0.65]
            a.cadena(ruta_cab, f"cuerno_{lado}" if tipo != "astas" else f"asta_{lado}", pts, anchos,
                     parte="asta" if tipo == "astas" else "cuerno")
    if colmillos:
        cg, cl = colmillos
        for s in (1, -1):
            b0 = (s * (hw / 2 - 1.0), cy - hh / 2 + 0.6, cz - hl / 2 - 0.5)
            pts = [b0, _mas(b0, (s * 0.4, -cl * 0.45, -cl * 0.45)), _mas(b0, (s * 0.8, -cl * 0.25, -cl * 0.95))]
            a.cadena(ruta_cab, f"colmillo_{'d' if s > 0 else 'i'}", pts, [cg, cg * 0.75], parte="colmillo")
    if trompa:
        tg, tl = trompa
        b0 = (0.0, cy - hh / 4, cz - hl / 2)
        pts = [b0, _mas(b0, (0, -tl * 0.45, -tl * 0.25)), _mas(b0, (0, -tl * 0.85, -tl * 0.2)), _mas(b0, (0, -tl, 0.0))]
        ruta_t = a.hueso(ruta_cab + "/trompa", b0)
        a.cadena(ruta_t, "hocico_trompa", pts, [tg, tg * 0.8, tg * 0.65], parte="hocico")
    # cola
    if cola:
        tipo, cg, cl = cola
        b0 = (0.0, base + h * 0.8, l / 2 - 0.3)
        ruta_c = a.hueso("raiz/cuerpo/cola", b0)
        if tipo == "corta":
            a.segmento(ruta_c, "cola", b0, _mas(b0, _unit((0, -0.3, 1)), cl), cg)
        elif tipo == "esponjosa":
            pts = [b0, _mas(b0, (0, -cl * 0.25, cl * 0.5)), _mas(b0, (0, -cl * 0.45, cl))]
            a.cadena(ruta_c, "cola", pts, [cg, cg * 1.15])
            a.segmento(ruta_c, "cola_punta", pts[2], _mas(pts[2], (0, -cl * 0.1, cl * 0.25)), cg * 0.9, parte="cola")
        elif tipo == "alzada":
            pts = [b0, _mas(b0, (0, cl * 0.45, cl * 0.35)), _mas(b0, (0, cl * 0.85, cl * 0.2)), _mas(b0, (0, cl, -cl * 0.15))]
            a.cadena(ruta_c, "cola", pts, [cg, cg * 0.85, cg * 0.7])
        elif tipo == "latigo":
            pts = [b0, _mas(b0, (0, -cl * 0.35, cl * 0.4)), _mas(b0, (0, -cl * 0.75, cl * 0.55)), _mas(b0, (0, -cl, cl * 0.5))]
            a.cadena(ruta_c, "cola", pts, [cg, cg * 0.8, cg * 0.6])
        else:                                                 # larga
            pts = [b0, _mas(b0, (0, -cl * 0.2, cl * 0.5)), _mas(b0, (0, -cl * 0.55, cl * 0.85))]
            a.cadena(ruta_c, "cola", pts, [cg, cg * 0.8])
    return a


# ====================================================================== ave

def ave(ident, piel, cuerpo=(5, 5, 7), pata=(0.8, 3), cabeza=(3.5, 3.5, 3.5), pico=("corto", 1.5, 2), cuello=None,
        cola=(3.5, 1, 3), cresta=None, alas="plegadas", envergadura=None, ojo=(1.0, 1.2, 0.55), escala=1.0,
        calvo=None, golilla=None):
    """pico: (tipo corto/ancho/gancho/largo/curvo/doblado, grosor, largo); cuello: (largo, grosor, grados);
    alas: 'plegadas' o 'abiertas' (las que planean); envergadura: largo de cada ala abierta."""
    a = Armado(ident, piel, escala)
    w, h, l = cuerpo
    g, L = pata
    base = L
    a.hueso("raiz/cuerpo", (0, base + h / 2, 0))
    a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
    a.caja("raiz/cuerpo", "pecho", (-w / 2 + 0.5, base + 0.5, -l / 2 - 1.0), (w / 2 - 0.5, base + h - 0.8, -l / 2 + 0.5),
           parte="pecho")
    if golilla:
        a.caja("raiz/cuerpo", "golilla", (-w / 2 - 0.3, base + h - 1.5, -l / 2 - 0.6), (w / 2 + 0.3, base + h + 0.6, -l / 2 + 1.8),
               parte="cresta")
    for s, lado in ((1, "d"), (-1, "i")):
        x = s * w / 4
        ruta = a.hueso(f"raiz/pata_{lado}", (x, base, 0.5))
        a.caja(ruta, f"pata_{lado}", (x - g / 2, 0.6, 0.5 - g / 2), (x + g / 2, base + 0.6, 0.5 + g / 2), parte="pata")
        a.caja(ruta, f"pie_{lado}", (x - g * 1.3, 0, 0.5 - g * 2.2), (x + g * 1.3, 0.6, 0.5 + g * 0.6), parte="pie")
    hw, hh, hl = cabeza
    frente = (0.0, base + h * 0.85, -l / 2 + 0.5)
    if cuello:
        cl, cg, ang = cuello
        d = (0.0, math.sin(math.radians(ang)), -math.cos(math.radians(ang)))
        fin = _mas(frente, d, cl)
        a.hueso("raiz/cuerpo/cuello", frente)
        a.segmento("raiz/cuerpo/cuello", "cuello", frente, fin, cg, cg, parte="cuello")
        centro = (0.0, fin[1] + hh * 0.3, fin[2] - hl * 0.25)
        ruta_cab = a.hueso("raiz/cuerpo/cuello/cabeza", fin)
    else:
        centro = (0.0, base + h + hh * 0.3, -l / 2 + hl * 0.2)
        ruta_cab = a.hueso("raiz/cuerpo/cabeza", (0.0, base + h - 0.5, -l / 2 + hl * 0.4))
    cab = a.centrada(ruta_cab, "cabeza" if not calvo else "cara", centro, cabeza)
    cx, cy, cz = centro
    a.ojos(cab, cy + hh / 2 - ojo[1], cz - hl / 2 + ojo[0], ojo[2])
    tipo, pg, pl = pico
    b0 = (0.0, cy - hh * 0.05, cz - hl / 2)
    if tipo == "ancho":
        a.caja(ruta_cab, "pico", (-hw * 0.4, cy - hh * 0.3, cz - hl / 2 - pl), (hw * 0.4, cy + pg * 0.4 - hh * 0.3, cz - hl / 2 + 0.2))
    elif tipo in ("largo", "curvo", "doblado"):
        if tipo == "largo":
            pts = [b0, _mas(b0, (0, -pl * 0.15, -pl))]
        elif tipo == "curvo":
            pts = [b0, _mas(b0, (0, -pl * 0.1, -pl * 0.55)), _mas(b0, (0, -pl * 0.45, -pl * 0.95))]
        else:
            pts = [b0, _mas(b0, (0, -pl * 0.05, -pl * 0.5)), _mas(b0, (0, -pl * 0.7, -pl * 0.7))]
        a.cadena(ruta_cab, "pico", pts, [pg, pg * 0.75], parte="pico")
    elif tipo == "gancho":
        a.segmento(ruta_cab, "pico", b0, _mas(b0, (0, -pl * 0.2, -pl * 0.7)), pg, parte="pico")
        a.segmento(ruta_cab, "pico_punta", _mas(b0, (0, -pl * 0.2, -pl * 0.7)), _mas(b0, (0, -pl * 0.7, -pl * 0.85)), pg * 0.7,
                   parte="pico")
    else:
        a.segmento(ruta_cab, "pico", b0, _mas(b0, (0, -pl * 0.25, -pl)), pg, parte="pico")
    if cresta:
        cw, ch, cl2 = cresta
        a.caja(ruta_cab, "cresta", (-cw / 2, cy + hh / 2 - 0.2, cz - cl2 / 2), (cw / 2, cy + hh / 2 + ch, cz + cl2 / 2))
    # alas
    for s, lado in ((1, "d"), (-1, "i")):
        ruta = a.hueso(f"raiz/cuerpo/ala_{lado}", (s * w / 2, base + h - 0.6, -l / 2 + 1.0))
        if alas == "abiertas":
            e = envergadura or l * 1.4
            a.caja(ruta, f"ala_{lado}", (min(s * w / 2, s * (w / 2 + e)), base + h - 1.2, -l / 2 + 0.5),
                   (max(s * w / 2, s * (w / 2 + e)), base + h - 0.6, -l / 2 + 0.5 + l * 0.75), parte="ala")
        else:
            a.caja(ruta, f"ala_{lado}", (s * w / 2 - (0.0 if s > 0 else 1.0), base + 0.6, -l / 2 + 0.8),
                   (s * w / 2 + (1.0 if s > 0 else 0.0), base + h - 0.4, l / 2 + l * 0.25), parte="ala")
    cw, ch, cl3 = cola
    ruta = a.hueso("raiz/cuerpo/cola", (0, base + h * 0.6, l / 2))
    a.caja(ruta, "cola", (-cw / 2, base + h * 0.45, l / 2 - 0.5), (cw / 2, base + h * 0.45 + ch, l / 2 + cl3),
           rot=(12.0, 0.0, 0.0), origen=(0, base + h * 0.5, l / 2), parte="cola")
    return a


# ====================================================================== reptil

def reptil(ident, piel, cuerpo=(4, 2.5, 8), pata=(1.2, 2.5), cabeza=(3.2, 2.2, 3.5), hocico=(2.2, 1.5, 2), cola=(2.2, 9),
           cresta=None, agallas=None, ojo=(1.2, 0.6, 0.5), escala=1.0, aleta_cola=False):
    """Cuerpo bajo, patas abiertas a los lados, cabeza plana y cola larga en tres tramos (cada uno su hueso)."""
    a = Armado(ident, piel, escala)
    w, h, l = cuerpo
    g, L = pata
    base = L * 0.6
    a.hueso("raiz/cuerpo", (0, base + h / 2, 0))
    a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
    if cresta:
        a.caja("raiz/cuerpo", "cresta", (-cresta[0] / 2, base + h - 0.1, -l / 2 + 0.5), (cresta[0] / 2, base + h + cresta[1], l / 2 - 0.5))
    for lado, s in (("d", 1), ("i", -1)):
        for fila, z in (("d", -l / 2 + g), ("t", l / 2 - g)):
            p0 = (s * (w / 2 - 0.3), base + h * 0.35, z)
            codo = (s * (w / 2 + L * 0.6), base + h * 0.35, z - 0.2)
            pie = (s * (w / 2 + L * 0.75), 0.0, z - 0.6)
            ruta = a.hueso(f"raiz/cuerpo/pata_{fila}{lado}", p0)
            a.segmento(ruta, f"pata_{fila}{lado}", p0, codo, g, parte="pata")
            a.segmento(ruta, f"canilla_{fila}{lado}", codo, pie, g * 0.9, parte="pata")
    hw, hh, hl = cabeza
    centro = (0.0, base + h * 0.55, -l / 2 - hl / 2 + 0.6)
    ruta_cab = a.hueso("raiz/cuerpo/cabeza", (0.0, centro[1], -l / 2 + 0.6))
    cab = a.centrada(ruta_cab, "cabeza", centro, cabeza)
    cx, cy, cz = centro
    if hocico:
        sw, sh, sl = hocico
        a.caja(ruta_cab, "hocico", (-sw / 2, cy - hh / 2, cz - hl / 2 - sl), (sw / 2, cy - hh / 2 + sh, cz - hl / 2 + 0.01))
    a.ojos(cab, cy + hh / 2 - ojo[1], cz - hl / 2 + ojo[0], ojo[2])
    if agallas:
        ag, al = agallas
        for s in (1, -1):
            for k, (dy, dz) in enumerate(((0.6, 0.0), (-0.1, 0.6), (-0.8, 0.2))):
                b0 = (s * hw / 2, cy + dy, cz + hl / 2 - 0.8 + dz)
                a.segmento(ruta_cab, f"agalla_{'d' if s > 0 else 'i'}{k}", b0, _mas(b0, _unit((s * 1.0, 0.45 + dy * 0.3, 0.55)), al),
                           ag, 0.4, parte="agalla")
    cg, cl = cola
    p = (0.0, base + h * 0.55, l / 2 - 0.3)
    ruta = "raiz/cuerpo"
    for k in range(3):
        ruta = a.hueso(f"{ruta}/cola{k + 1}", p)
        q = _mas(p, _unit((0.0, -0.06 - 0.05 * k, 1.0)), cl / 3)
        a.segmento(ruta, f"cola{k + 1}", p, q, cg * (1 - 0.25 * k), cg * (1 - 0.25 * k) * 0.8, parte="cola")
        p = q
    if aleta_cola:
        a.caja(ruta, "aleta_dorsal", (-0.2, p[1] - 0.2, p[2] - cl / 3), (0.2, p[1] + cg * 1.4, p[2]), parte="cresta")
    return a


# ====================================================================== serpiente

def serpiente(ident, piel, tramos=8, grosor=2.5, largo_tramo=3.5, cabeza=(3.2, 2.2, 4), escala=1.0, onda=14.0,
              ojo=(1.2, 0.6, 0.5)):
    """Una cadena de tramos (s0 la cabeza): cada uno hijo del anterior, para que ondule; en reposo va en S."""
    a = Armado(ident, piel, escala)
    hw, hh, hl = cabeza
    y = grosor / 2
    ruta = a.hueso("raiz/s0", (0.0, y, 0.0))
    cab = a.centrada(ruta, "cabeza", (0.0, hh / 2, -hl / 2), cabeza)
    a.ojos(cab, hh - ojo[1], -hl + ojo[0], ojo[2])
    a.caja(ruta, "hocico", (-hw * 0.35, 0.0, -hl - 0.8), (hw * 0.35, hh * 0.6, -hl + 0.01))
    p = (0.0, y, 0.0)
    ang = 0.0
    for k in range(1, tramos + 1):
        ang += math.radians(onda) * (1 if (k // 2) % 2 == 0 else -1)
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = _mas(p, d, largo_tramo)
        ruta = a.hueso(f"{ruta}/s{k}", p)
        g = grosor * (1.0 if k < tramos - 2 else 0.8 if k < tramos else 0.55)
        a.segmento(ruta, f"cuerpo{k}" if k < tramos else "cola", p, q, g, g, parte="cuerpo" if k < tramos else "cola")
        p = q
    return a


# ====================================================================== insectos

def insecto(ident, piel, tipo="escarabajo", cuerpo=(5, 3, 6), pata=(0.6, 4), cabeza=(2.5, 2, 2), escala=1.0,
            cuerno=None, antenas=1.5, bola=None, pinzas=None, aguijon=None, ojo=(0.6, 0.5, 0.45)):
    """tipo escarabajo (domo con cuerno), palo (ramita larga y flaca), escorpion (pinzas y cola alzada con aguijon),
    garrapata (bolita), cangrejo (caparazon ancho y pinzas)."""
    a = Armado(ident, piel, escala)
    w, h, l = cuerpo
    g, L = pata
    base = L * 0.45 if tipo != "garrapata" else 0.4
    a.hueso("raiz/cuerpo", (0, base + h / 2, 0))
    if tipo == "palo":
        a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l * 0.15))
        a.caja("raiz/cuerpo", "abdomen", (-w * 0.4, base + 0.1, l * 0.15), (w * 0.4, base + h * 0.85, l / 2), parte="cuerpo")
    elif tipo == "cangrejo":
        a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
        a.caja("raiz/cuerpo", "caparazon", (-w / 2 + 0.6, base + h - 0.01, -l / 2 + 0.6), (w / 2 - 0.6, base + h + 0.8, l / 2 - 0.6),
               parte="caparazon")
    else:
        a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
        if tipo == "escarabajo":
            a.caja("raiz/cuerpo", "caparazon", (-w / 2 + 0.3, base + h - 0.01, -l / 2 + 0.8), (w / 2 - 0.3, base + h + 0.9, l / 2 - 0.3),
                   parte="caparazon")
    hw, hh, hl = cabeza
    if tipo == "palo":
        centro = (0.0, base + hh / 2, -l / 2 - hl / 2 + 0.2)
    else:
        centro = (0.0, base + hh / 2 + 0.2, -l / 2 - hl / 2 + 0.3)
    ruta_cab = a.hueso("raiz/cuerpo/cabeza", (0.0, centro[1], -l / 2))
    cab = a.centrada(ruta_cab, "cabeza", centro, cabeza)
    cx, cy, cz = centro
    a.ojos(cab, cy + hh / 2 - ojo[1], cz - hl / 2 + ojo[0], ojo[2])
    if antenas:
        for s in (1, -1):
            b0 = (s * hw * 0.3, cy + hh / 2 - 0.2, cz - hl / 2 + 0.3)
            a.cadena(ruta_cab, f"antena_{'d' if s > 0 else 'i'}", [b0, _mas(b0, (s * antenas * 0.3, antenas * 0.5, -antenas * 0.5)),
                                                                   _mas(b0, (s * antenas * 0.6, antenas * 0.6, -antenas))],
                     [0.35, 0.3], parte="pata")
    if cuerno:
        b0 = (0.0, cy + hh / 2 - 0.3, cz - hl / 2 + 0.4)
        a.cadena(ruta_cab, "cuerno", [b0, _mas(b0, (0, cuerno * 0.6, -cuerno * 0.4)), _mas(b0, (0, cuerno, -cuerno * 0.1))], [0.8, 0.6])
    # patas: tres pares, abiertas a los lados
    nz = (-l * 0.3, 0.0, l * 0.3) if tipo not in ("palo",) else (-l * 0.42, -l * 0.25, 0.05)
    for k, z in enumerate(nz):
        for s in (1, -1):
            lado = "d" if s > 0 else "i"
            p0 = (s * (w / 2 - 0.2), base + h * 0.3, z)
            abierto = 1.1 if tipo == "palo" else 0.75
            codo = (s * (w / 2 + L * abierto), base + h * 0.3 + L * 0.35, z + (k - 1) * L * 0.25)
            pie = (s * (w / 2 + L * (abierto + 0.25)), 0.0, z + (k - 1) * L * 0.45)
            ruta = a.hueso(f"raiz/cuerpo/pata_{k + 1}{lado}", p0)
            a.segmento(ruta, f"pata_{k + 1}{lado}", p0, codo, g, parte="pata")
            a.segmento(ruta, f"canilla_{k + 1}{lado}", codo, pie, g * 0.85, parte="pata")
    if pinzas:
        pg, pl = pinzas
        for s in (1, -1):
            lado = "d" if s > 0 else "i"
            p0 = (s * (w / 2 - 0.3), base + h * 0.5, -l / 2 + 0.5)
            codo = (s * (w / 2 + pl * 0.45), base + h * 0.6, -l / 2 - pl * 0.35)
            ruta = a.hueso(f"raiz/cuerpo/pinza_{lado}", p0)
            a.segmento(ruta, f"brazo_{lado}", p0, codo, pg * 0.6, parte="pata")
            a.centrada(ruta, f"pinza_{lado}", _mas(codo, (s * 0.2, 0.2, -pg * 0.9)), (pg * 1.1, pg * 0.9, pg * 1.8), parte="pinza")
            a.segmento(ruta, f"pinza_punta_{lado}", _mas(codo, (s * pg * 0.25, 0.3, -pg * 1.7)),
                       _mas(codo, (-s * pg * 0.1, 0.3, -pg * 2.7)), pg * 0.4, parte="pinza")
    if aguijon:
        ag, al = aguijon
        p = (0.0, base + h * 0.6, l / 2 - 0.3)
        ruta = "raiz/cuerpo"
        dirs = [(0, 0.25, 1), (0, 0.9, 0.6), (0, 1, -0.2), (0, 0.4, -1)]
        for k, d in enumerate(dirs):
            ruta = a.hueso(f"{ruta}/cola{k + 1}", p)
            q = _mas(p, _unit(d), al / len(dirs))
            a.segmento(ruta, f"cola{k + 1}", p, q, ag * (1 - 0.12 * k), parte="cola")
            p = q
        a.segmento(ruta, "aguijon", p, _mas(p, _unit((0, -0.6, -1)), ag * 1.3), ag * 0.55, parte="aguijon")
    if bola:
        # la bola va detras: el escarabajo la empuja de reversa con las patas de atras
        a.hueso("raiz/bola", (0.0, bola / 2, l / 2 + bola / 2 + 0.2))
        a.centrada("raiz/bola", "bola", (0.0, bola / 2, l / 2 + bola / 2 + 0.2), (bola, bola, bola), parte="bola")
    return a


# ====================================================================== pez (y ballenato)

def pez(ident, piel, cuerpo=(8, 7, 14), cabeza=(7, 6, 5), cola=(9, 1, 5), aletas=(5, 0.6, 3), escala=1.0,
        aleta_dorsal=None, ojo=(1.2, 2.0, 0.6), boca=True):
    a = Armado(ident, piel, escala)
    w, h, l = cuerpo
    base = 0.0
    a.hueso("raiz/cuerpo", (0, base + h / 2, 0))
    a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
    hw, hh, hl = cabeza
    centro = (0.0, base + hh / 2, -l / 2 - hl / 2 + 0.5)
    ruta_cab = a.hueso("raiz/cuerpo/cabeza", (0, base + h / 2, -l / 2))
    cab = a.centrada(ruta_cab, "cabeza", centro, cabeza)
    a.ojos(cab, centro[1] + hh / 2 - ojo[1], centro[2] - hl / 2 + ojo[0], ojo[2])
    if boca:
        a.caja(ruta_cab, "hocico", (-hw / 2 + 0.3, base, centro[2] - hl / 2 - 0.6), (hw / 2 - 0.3, base + hh * 0.35, centro[2] - hl / 2 + 0.01))
    cw, ch, cl = cola
    ruta = a.hueso("raiz/cuerpo/cola", (0, base + h / 2, l / 2))
    a.caja(ruta, "cola", (-w / 4, base + h * 0.25, l / 2 - 0.5), (w / 4, base + h * 0.7, l / 2 + cl * 0.8))
    a.caja(ruta, "aleta_cola", (-cw / 2, base + h * 0.42, l / 2 + cl * 0.6), (cw / 2, base + h * 0.42 + ch, l / 2 + cl * 1.3),
           parte="cola_punta")
    aw, ag, al = aletas
    for s in (1, -1):
        ruta = a.hueso(f"raiz/cuerpo/aleta_{'d' if s > 0 else 'i'}", (s * w / 2, base + h * 0.3, -l / 4))
        a.caja(ruta, f"aleta_{'d' if s > 0 else 'i'}", (min(s * w / 2, s * (w / 2 + aw)), base + h * 0.25, -l / 4),
               (max(s * w / 2, s * (w / 2 + aw)), base + h * 0.25 + ag, -l / 4 + al), rot=(0.0, 0.0, -s * 18.0),
               origen=(s * w / 2, base + h * 0.3, -l / 4), parte="ala")
    if aleta_dorsal:
        dw, dh, dl = aleta_dorsal
        a.caja("raiz/cuerpo", "aleta_dorsal", (-dw / 2, base + h - 0.1, 0.0), (dw / 2, base + h + dh, dl))
    return a


# ====================================================================== murcielago

def murcielago(ident, piel, cuerpo=(3, 3.5, 3), cabeza=(3, 3, 2.5), envergadura=7, escala=1.0, ojo=(0.6, 1.0, 0.5)):
    a = Armado(ident, piel, escala)
    w, h, l = cuerpo
    base = 2.0
    a.hueso("raiz/cuerpo", (0, base + h / 2, 0))
    a.caja("raiz/cuerpo", "cuerpo", (-w / 2, base, -l / 2), (w / 2, base + h, l / 2))
    hw, hh, hl = cabeza
    centro = (0.0, base + h + hh / 2 - 0.3, -0.3)
    ruta_cab = a.hueso("raiz/cuerpo/cabeza", (0.0, base + h, 0.0))
    cab = a.centrada(ruta_cab, "cabeza", centro, cabeza)
    a.ojos(cab, centro[1] + hh / 2 - ojo[1], centro[2] - hl / 2 + ojo[0], ojo[2])
    for s in (1, -1):
        b0 = (s * (hw / 2 - 0.5), centro[1] + hh / 2 - 0.2, centro[2])
        a.segmento(ruta_cab, f"oreja_{'d' if s > 0 else 'i'}", b0, _mas(b0, _unit((s * 0.4, 1, 0.1)), 2.2), 1.0, 0.5, parte="oreja")
        ruta = a.hueso(f"raiz/cuerpo/ala_{'d' if s > 0 else 'i'}", (s * w / 2, base + h - 0.5, 0.0))
        a.caja(ruta, f"membrana_{'d' if s > 0 else 'i'}", (min(s * w / 2, s * (w / 2 + envergadura)), base + 0.3, -0.25),
               (max(s * w / 2, s * (w / 2 + envergadura)), base + h + 0.8, 0.25), parte="membrana")
        a.segmento(ruta, f"ala_hueso_{'d' if s > 0 else 'i'}", (s * w / 2, base + h + 0.6, 0.0),
                   (s * (w / 2 + envergadura), base + h + 0.9, 0.0), 0.5, parte="pata")
    for s in (1, -1):
        ruta = a.hueso(f"raiz/pata_{'d' if s > 0 else 'i'}", (s * 0.8, base, 0.3))
        a.caja(ruta, f"pata_{'d' if s > 0 else 'i'}", (s * 0.8 - 0.3, 0.2, 0.0), (s * 0.8 + 0.3, base + 0.2, 0.6), parte="pata")
    return a


# ====================================================================== canino (lobos, chacales, zorros: grandes y robustos)

def canino(ident, piel, k=1.0, flaco=0.0, orejas=1.0, cola=1.0, hocico=1.0, cresta=True, escala=1.0, boca_abierta=12.0):
    """Lobo robusto (como los lobos de los paquetes de mobs): pecho hondo y ancho, melena de pelo alrededor del cuello,
    cachetes peludos, frente marcada, hocico largo con la mandibula entreabierta y colmillos, patas gruesas en dos
    tramos con la pata (mano) grande, cadera fuerte, cola esponjosa en tres tramos y mechones en el lomo.
    k: tamano (1 = lobo de ~1.6 bloques a la cruz); flaco: 0 a 1 (adelgaza cintura y patas); orejas, cola, hocico:
    cuanto crecen esas partes."""
    a = Armado(ident, piel, escala)
    f = 1.0 - 0.25 * flaco
    base = 10.0 * k
    a.hueso("raiz/cuerpo", (0, base + 5 * k, 0))
    R = "raiz/cuerpo"
    a.caja(R, "pecho", (-6.2 * k, base - 1.5 * k, -12 * k), (6.2 * k, base + 10.5 * k, -3 * k), parte="pecho")
    a.caja(R, "cuerpo", (-4.2 * k * f, base + 1 * k, -4 * k), (4.2 * k * f, base + 8.6 * k, 5 * k))
    a.caja(R, "cuerpo_cadera", (-4.8 * k, base + 0.5 * k, 4 * k), (4.8 * k, base + 9 * k, 10 * k), parte="cuerpo")
    a.caja(R, "cuello_melena", (-7.6 * k, base + 2.5 * k, -14.5 * k), (7.6 * k, base + 14 * k, -8 * k), parte="cuello")
    for s in (1, -1):                                         # mechones del pecho y los hombros
        a.caja(R, f"cuerpo_mechon_{s}", (s * 5.4 * k - 0.8 * k, base + 1 * k, -11 * k), (s * 5.4 * k + 0.8 * k, base + 7 * k, -6 * k),
               rot=(0.0, 0.0, s * 10.0), origen=(s * 5.4 * k, base + 7 * k, -8.5 * k), parte="cuerpo")
    if cresta:                                                # mechones a lo largo del lomo
        for n, z in enumerate((-9.5, -5.5, -1.5, 2.5, 6.5)):
            a.caja(R, f"cresta{n}", (-1.2 * k, base + 8.4 * k + (2.6 * k if n == 0 else 0), z * k), (1.2 * k, base + 10.2 * k + (2.6 * k if n == 0 else 0), (z + 3) * k),
                   rot=(-22.0, 0.0, 0.0), origen=(0, base + 9 * k, z * k), parte="cresta")
    # cabeza
    cy, cz = base + 13.5 * k, -16.5 * k
    ruta_cab = a.hueso(R + "/cabeza", (0, base + 10 * k, -12 * k))
    craneo = a.caja(ruta_cab, "cabeza", (-4.3 * k, cy - 3.6 * k, cz - 3 * k), (4.3 * k, cy + 3.6 * k, cz + 3 * k))
    a.caja(ruta_cab, "cabeza_frente", (-4.0 * k, cy + 2.6 * k, cz - 3.5 * k), (4.0 * k, cy + 4.0 * k, cz - 1.2 * k), parte="cabeza")
    for s in (1, -1):                                         # cachetes peludos
        a.caja(ruta_cab, f"cuello_cachete_{s}", (min(s * 4.0 * k, s * 6.2 * k), cy - 3.8 * k, cz - 1.8 * k),
               (max(s * 4.0 * k, s * 6.2 * k), cy + 0.8 * k, cz + 2.8 * k), parte="cuello")
    hl = 5 * k * hocico
    z0 = cz - 3 * k
    a.caja(ruta_cab, "hocico", (-2.5 * k, cy - 1.6 * k, z0 - hl), (2.5 * k, cy + 1.2 * k, z0 + 0.01))
    ruta_m = a.hueso(ruta_cab + "/mandibula", (0, cy - 1.4 * k, z0))
    rot_m = (-boca_abierta, 0.0, 0.0) if boca_abierta else None
    a.caja(ruta_m, "mandibula", (-2.1 * k, cy - 3.0 * k, z0 - hl + 0.8 * k), (2.1 * k, cy - 1.5 * k, z0 + 0.2 * k),
           rot=rot_m, origen=(0, cy - 1.4 * k, z0) if rot_m else None)
    a.caja(ruta_m, "boca", (-1.4 * k, cy - 2.3 * k, z0 - hl + 1.0 * k), (1.4 * k, cy - 1.3 * k, z0 - 0.1 * k),
           rot=rot_m, origen=(0, cy - 1.4 * k, z0) if rot_m else None)
    for s in (1, -1):                                         # colmillos
        a.caja(ruta_cab, f"colmillo_{s}", (s * 1.35 * k - 0.35 * k, cy - 2.2 * k, z0 - hl + 0.3 * k),
               (s * 1.35 * k + 0.35 * k, cy - 1.35 * k, z0 - hl + 1.0 * k), parte="colmillo")
    a.ojos(craneo, cy + 0.9 * k, cz - 3 * k + 1.3 * k, 0.6 * k)
    for s in (1, -1):
        b0 = (s * 2.3 * k, cy + 2.9 * k, cz + 1.2 * k)
        d = _unit((s * 0.35, 1.0, 0.12))
        lo = 4.0 * k * orejas
        ancho = 2.6 * k * min(orejas, 1.4)
        lado = 'd' if s > 0 else 'i'                          # oreja en punta: base ancha y punta angosta
        a.segmento(ruta_cab, f"oreja_{lado}", b0, _mas(b0, d, lo * 0.55), ancho, 1.1 * k, parte="oreja")
        a.segmento(ruta_cab, f"oreja_{lado}_punta", _mas(b0, d, lo * 0.5), _mas(b0, d, lo), ancho * 0.5, 0.9 * k, parte="oreja")
    # patas: delanteras (brazo, antebrazo, mano) y traseras (muslo, canilla, pie)
    for s, lado in ((1, "d"), (-1, "i")):
        x = s * 4.4 * k
        ruta = a.hueso(f"raiz/pata_d{lado}", (x, base + 6 * k, -8.5 * k))
        a.caja(ruta, f"pata_d{lado}_brazo", (x - 2.2 * k, base - 2.5 * k, -11 * k), (x + 2.2 * k, base + 7 * k, -6 * k), parte="pata")
        a.caja(ruta, f"pata_d{lado}", (x - 1.8 * k * f, 1.5 * k, -10 * k), (x + 1.8 * k * f, base - 2 * k, -6.8 * k), parte="pata")
        a.caja(ruta, f"pie_d{lado}", (x - 2.2 * k, 0, -11.8 * k), (x + 2.2 * k, 2.0 * k, -6.4 * k), parte="pie")
        ruta = a.hueso(f"raiz/pata_t{lado}", (x, base + 5 * k, 7.5 * k))
        a.caja(ruta, f"pata_t{lado}_muslo", (x - 2.4 * k, base - 3 * k, 4 * k), (x + 2.4 * k, base + 6.5 * k, 10.5 * k), parte="pata")
        a.caja(ruta, f"pata_t{lado}", (x - 1.7 * k * f, 1.5 * k, 7.8 * k), (x + 1.7 * k * f, base - 2.5 * k, 10.8 * k), parte="pata")
        a.caja(ruta, f"pie_t{lado}", (x - 2.2 * k, 0, 6.2 * k), (x + 2.2 * k, 2.0 * k, 11.4 * k), parte="pie")
    # cola esponjosa
    ruta_c = a.hueso(R + "/cola", (0, base + 8 * k, 10 * k))
    c = cola
    p0, p1, p2, p3 = (0, base + 8 * k, 9.5 * k), (0, base + 6 * k, 9.5 * k + 5 * k * c), (0, base + 2.5 * k, 9.5 * k + 9 * k * c), \
        (0, base + 0.2 * k, 9.5 * k + 11.5 * k * c)
    a.segmento(ruta_c, "cola1", p0, p1, 3.2 * k)
    a.segmento(ruta_c, "cola2", p1, p2, 4.8 * k)
    a.segmento(ruta_c, "cola_punta", p2, p3, 3.0 * k, parte="cola")
    return a
