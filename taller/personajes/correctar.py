"""
Correcthar, el dios libre ("自由な神"). Hecho a mano con el kit (boceto 6, segun referencias/personajes/correctar_nuevo.png
y las siluetas correctar_silueta.png y correctar_zapatos_silueta.png).

Bases del pedido original: semidios cuyo poder es hacer cualquier cosa random; estilo unico, alocado, rebelde, sin
control y arriesgado; estilo japones; SIN MUCHOS DETALLES; pose neutra. Por eso: pocas piezas, bien marcadas.

Medidas: 2.5 bloques (40 px, 1.25 veces Steve). Alto y delgado por proporcion, no por tamano: cabeza de 8 px, torso
de 10 (7 de ancho), piernas de 22 (cintura alta), brazos finos de 15 (las manos a la altura de la entrepierna).

Capas, de adentro hacia afuera:
  BASE: cara a densidad 3 (ojos amarillos cansados de anime); torso de piel con abdominales, el engranaje tatuado,
    unas ramas de tinta y el cordon del collar; hombros desnudos con el engranaje tatuado
  PELO de anime a criterio propio: casco ajustado y mechones puntiagudos (piramides de base rectangular): flequillo
    barrido a la izquierda, costados que tapan las orejas, nuca hacia abajo y atras, puntas arriba; un tono por cara
    (brillo arriba, sombra abajo); mechones blancos y cinta roja del lado izquierdo, un mechon rojo atras
  ACCESORIOS 3D: arete con talisman (izquierda), moneda del collar, un anillo por mano
  HAORI: chaqueta aparte que se abre en la cadera, con manchones blancos, kanji atras y el FINAL BLANCO (franja
    blanca en el borde de abajo y al final de las mangas); mangas de kimono con la bolsa atras
  FAJA con nudo; tres cintas (roja adelante y atras, amarilla con talisman al costado izquierdo); HAKAMA en trapecio
  ancho, negro liso, que termina un poco arriba de la zapatilla; ZAPATILLAS gordas y bajas con puno del tobillo
"""

import math

from .. import malla as geo
from ..kit import Objeto, Personaje, dibujo, sprite, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_

PIEL = tonos("#C8966E")
PELO = {"k": "#171213", "h": "#33251F", "d": "#0D0A0B", "w": "#E9E5DF", "g": "#A9A39D", "r": "#B8242A"}
NEGRO, NEGRO2 = "#151314", "#221E20"
BLANCO, GRIS = "#E9E5DF", "#B8B2AC"
AMARILLO = tonos("#E2B42A")
ROJO = tonos("#C0262A")
ORO = tonos("#C9A14A")

# ---------------------------------------------------------------- cara (24 x 24, densidad 3)

CARA = dibujo("""
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    ppkkkkkkkkppppkkkkkkkkpp
    pppkWYLoYWppppWYoLYWkppp
    ppppWYYoGWppppWGoYYWpppp
    pppppGGGbppppppbGGGppppp
    ppppbbbbbppppppbbbbbpppp
    pppppppppppssppppppppppp
    pppppppppppppppppppppppp
    ppppppppppmmmmpppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    pppppppppppppppppppppppp
    ssssssssssssssssssssssss
""")
PAL_CARA = {"p": PIEL["b"], "s": PIEL["s"], "k": "#1E1416", "W": "#EDE6DC", "Y": "#F0C81E", "G": "#B88A12",
            "L": "#FFF0A0", "o": "#3A2808", "b": PIEL["s2"], "m": "#8A5A44"}

TATUAJE = dibujo("""
    .kkkk.
    k.kk.k
    kk..kk
    kk..kk
    k.kk.k
    .kkkk.
""")

KANJI = dibujo("""
    .......WW.......
    ..WWWWWWWWWWWW..
    ....W..WW..W....
    ...W.W.WW.W.W...
    ..W...WWWW...W..
    .....W....W.....
    ....WWWWWWWW....
    ......W..W......
    .....W....W.....
    ....WW....WW....
    ...W..W..W..W...
    ..W....WW....W..
    ......W..W......
    ....WW....WW....
""")

TALISMAN = dibujo("""
    wwwwww
    wwkkww
    wkkkkw
    wwkkww
    wkwwkw
    wkkkkw
    wwkkww
    wkwkww
    wkkkkw
    wwwkww
    wkwwkw
    wwwwww
""")
PAL_TALISMAN = {"w": BLANCO, "k": "#141214"}

CARA_MASCARA = dibujo("""
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yykykyyyyykykyyy
    yyykyyyyyyykyyyy
    yykykyyyyykykyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yykyyyyyyyyykyyy
    yyykyyyyyyykyyyy
    yyyykkkkkkkyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
    yyyyyyyyyyyyyyyy
""")


def torso_dibujo(W, H):
    """Frente del torso: cordon del collar en V, claviculas, pecho, abdominales, oblicuos, el engranaje tatuado en
    el pecho izquierdo (derecha de la imagen) y unas ramas de tinta en el derecho."""
    g = [["p"] * W for _ in range(H)]
    m = W // 2

    def pon(c, r, ch):
        if 0 <= r < H and 0 <= c < W:
            g[r][c] = ch

    def fila(f):
        return round(f * H)
    for r in range(11):                                         # cordon en V hasta la moneda
        pon(round(m - 6 + r * 0.55), r, "k")
        pon(round(m + 5 - r * 0.55), r, "k")
    for c in list(range(1, m - 2)) + list(range(m + 2, W - 1)):  # claviculas
        pon(c, 3, "s")
    for c in list(range(1, m - 1)) + list(range(m + 1, W - 1)):  # borde de abajo del pecho
        pon(c, fila(0.36), "s")
    for r in range(fila(0.38), fila(0.86)):                     # linea del medio
        pon(m, r, "s")
    for f in (0.5, 0.63, 0.76):                                 # abdominales
        for c in list(range(m - 6, m - 1)) + list(range(m + 2, m + 7)):
            pon(c, fila(f), "s")
    for r in range(fila(0.5), fila(0.92)):                      # oblicuos
        pon(2 + (r - fila(0.5)) // 6, r, "s")
        pon(W - 3 - (r - fila(0.5)) // 6, r, "s")
    pon(m, fila(0.84), "d")                                     # ombligo
    engranaje = ("..kkkk..", ".k.kk.k.", "k.k..k.k", "kk.kk.kk", "kk.kk.kk", "k.k..k.k", ".k.kk.k.", "..kkkk..")
    for r, fil in enumerate(engranaje):
        for c, ch in enumerate(fil):
            if ch == "k":
                pon(m + 2 + c, 3 + r, "k")
    for r in range(11, 15):                                     # tinta que chorrea
        if r % 2:
            pon(m + 4, r, "k")
    for c, r in ((1, 5), (2, 6), (3, 7), (4, 8), (7, 5), (6, 6), (5, 9), (6, 10)):    # ramas de tinta
        pon(c, r, "k")
    return ["".join(f) for f in g]


# ---------------------------------------------------------------- pintores

def _h(*v):
    """Ruido fijo por celda (0..1)."""
    n = 0
    for x in v:
        n = (n * 73856093) ^ (int(x) * 19349663 + 83492791)
    return ((n ^ (n >> 13)) * 1274126177 & 0xFFFF) / 65535.0


def color(hexa):
    c = hex_(hexa)
    return lambda t: c


def manchas(blanco_abajo=None, base=NEGRO, deshilachado=None, kanji=None, sesgo=0.0, borde=None):
    """Tela negra con manchones blancos. deshilachado: (alto del dobladillo en px, semilla) recorta el borde de abajo.
    kanji: altura desde la que la tela queda negra lisa (ahi va el kanji de la espalda).
    borde: funcion t -> altura del final de la tela en ese punto; los ultimos ~3 px quedan BLANCOS (franja con el
    borde de arriba ondulado como una pincelada y alguna salpicadura negra)."""
    def p(t):
        x, y, z = t.x, t.y, t.z
        if deshilachado and t.cara in ("north", "south", "east", "west"):
            alto, sem = deshilachado
            if t.fila_abajo < int(alto * 3 * _h(t.i // 2, sem)):
                return TRANSPARENTE
        if borde is not None and t.cara != "up":
            tope = borde(t) + 2.8 + 0.55 * math.sin(x * 1.4 + z * 1.1) + 0.3 * math.sin(x * 3.1 - z * 2.3)
            if y < tope:
                n = _h(x * 2 // 1, y * 2 // 1, z * 2 // 1)
                return hex_(NEGRO if n > 0.93 else (GRIS if n > 0.82 else BLANCO))
        if kanji is not None and t.cara in ("north", "south") and y > kanji:
            return hex_(NEGRO2 if _h(t.i // 3, t.j // 3) < 0.15 else NEGRO)
        f = (0.5 + 0.5 * math.sin(x * 0.9 + y * 0.35 + z * 0.3)) * (0.5 + 0.5 * math.cos(z * 0.8 - y * 0.45 + x * 0.2))
        f += 0.35 * _h(x // 1, y // 1, z // 1) - 0.1 + sesgo
        if blanco_abajo is not None and y < blanco_abajo:
            f += 0.35
        if f > 0.62:
            return hex_(BLANCO)
        if f > 0.52:
            return hex_(GRIS)
        return hex_(NEGRO2 if _h(x * 2 // 1, y * 2 // 1, z * 2 // 1) < 0.2 else base)
    return p


Y_MANCHAS_PANTALON = 11.0


def pantalon(t):
    """Hakama negro liso con pliegues verticales y pocas salpicaduras blancas abajo (distinto del haori)."""
    x, y, z = t.x, t.y, t.z
    if t.cara in ("down", "up"):
        return hex_(NEGRO2)
    pliegue = (abs(x) if abs(t.n[2]) > 0.5 else abs(z)) * 1.6
    if pliegue % 2 < 0.28:
        return hex_("#0C0A0B")
    if y < Y_MANCHAS_PANTALON:
        f = 0.6 * (0.5 + 0.5 * math.sin(x * 1.7 + y * 1.1)) * (0.5 + 0.5 * math.cos(z * 1.3 - y * 0.9)) \
            + 0.4 * _h(x * 1.5 // 1, y * 1.5 // 1, z * 1.5 // 1)
        if f > (0.66 if x > 0 else 0.76):
            return hex_(BLANCO if f > 0.74 else GRIS)
    return hex_(NEGRO)


def encima(base, capas):
    """Dibujos encima de otro pintor: capas = [(cara, i0, j0, filas, paleta)]."""
    capas = [(c, i0, j0, f, {k: hex_(v) for k, v in pal.items()}) for c, i0, j0, f, pal in capas]

    def p(t):
        for cara, i0, j0, filas, pal in capas:
            if t.cara == cara:
                r, c = t.j - j0, t.i - i0
                if 0 <= r < len(filas) and 0 <= c < len(filas[0]) and filas[r][c] != ".":
                    return pal[filas[r][c]]
        return base(t)
    return p


def piel(t):
    return hex_(PIEL["l"] if t.cara == "up" else PIEL["b"])


def cinta(c, marcas="#5A1010"):
    def p(t):
        if t.i % 3 == 1 and t.j % 4 in (1, 2) and _h(t.j // 4, len(t.nombre)) < 0.6:
            return hex_(marcas)
        return hex_(c["b"])
    return p


def oro(t):
    return hex_(ORO["l"] if t.cara == "up" else ORO["b"])


# ---------------------------------------------------------------- piezas de malla

def mecha(base, ancho, fondo, direccion, largo):
    """Mechon puntiagudo: piramide de base rectangular (ancho x fondo) que apunta en 'direccion'."""
    d = geo._norm(direccion)
    ref = (0.0, 1.0, 0.0) if abs(d[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = geo._norm(geo._cross(d, ref))
    v = geo._cross(u, d)
    pts = [tuple(base[i] + u[i] * a + v[i] * b for i in range(3))
           for a, b in ((ancho / 2, fondo / 2), (-ancho / 2, fondo / 2), (-ancho / 2, -fondo / 2), (ancho / 2, -fondo / 2))]
    if geo._dot(geo.normal(pts), d) < 0:
        pts.reverse()
    apice = tuple(base[i] + d[i] * largo for i in range(3))
    return geo.piramide(pts, apice)


def pelo_malla(medio, luz, sombra):
    """Pelo plano de anime: un tono por cara segun hacia donde mira (arriba con brillo, abajo en sombra)."""
    m, l, sm = hex_(medio), hex_(luz), hex_(sombra)
    return lambda t: l if t.n[1] > 0.45 else (sm if t.n[1] < -0.45 else m)


def pelo_plano(t):
    return hex_(PELO["h"] if t.cara == "up" else PELO["k"])



def tubo_hueco(abajo, arriba, grosor=0.15, tapa=True):
    """Tubo de 4 lados abierto abajo: cara de afuera y forro corrido hacia adentro (se ve por la abertura).
    Anillos de 4 puntos antihorarios vistos desde arriba. Devuelve (malla, cantidad de caras de afuera)."""
    afuera = geo.tronco(abajo, arriba, tapa_abajo=False, tapa_arriba=tapa)

    def encoger(r):
        cx, cz = sum(q[0] for q in r) / len(r), sum(q[2] for q in r) / len(r)
        out = []
        for x, y, z in r:
            d = math.hypot(x - cx, z - cz) or 1.0
            out.append((x - (x - cx) / d * grosor, y, z - (z - cz) / d * grosor))
        return out
    vs, cs = geo.tronco(encoger(abajo), encoger(arriba), tapa_abajo=False, tapa_arriba=False)
    return geo.unir(afuera, (vs, [tuple(reversed(c)) for c in cs])), len(afuera[1])


def haori(C, abajo, tela, espalda):
    """Cuerpo del haori como chaqueta aparte: espalda, costados y dos delanteros que se ABREN hacia la cadera (pasan
    por encima del pantalon y marcan el dobladillo). Abierto adelante; derecha puesta en el hombro, izquierda caida.
    Cada panel tiene forro corrido hacia adentro. Devuelve (malla, pintores)."""
    m = geo.Armador()
    pint = []
    afuera_de = (0.0, 0.0, 0.0)

    def panel(pts, pintor, solo_afuera=False):
        idx = [m.v(q) for q in pts]
        cx = sum(q[0] for q in pts) / 4
        cz = sum(q[2] for q in pts) / 4
        m.cara(tuple(idx), (cx - afuera_de[0], 0, cz - afuera_de[2]), "fuera")
        pint.append(pintor)
        if solo_afuera:
            return
        hacia = [(q[0] - 0.12 * (cx - afuera_de[0]) / max(0.01, math.hypot(cx, cz)), q[1],
                  q[2] - 0.12 * (cz - afuera_de[2]) / max(0.01, math.hypot(cx, cz))) for q in pts]
        idx2 = [m.v(q) for q in hacia]
        m.cara(tuple(idx2), (-(cx - afuera_de[0]), 0, -(cz - afuera_de[2])), "forro")
        pint.append(color(NEGRO2))
    zt_f, zt_b, zb_f, zb_b = -2.15, 2.2, -3.05, 3.1               # arriba ajustado, abajo abierto
    xt, xb = 3.85, 4.95
    sup_d, sup_i = C - 0.2, C - 3.5                               # delantero derecho puesto, izquierdo caido
    lado_d, lado_i = C - 0.2, C - 5.0
    panel([(-3.8, C + 0.4, zt_b), (3.8, C + 0.4, zt_b), (xb, abajo, zb_b), (-xb, abajo, zb_b)], espalda)
    panel([(xt, lado_d, zt_b), (xt, lado_d, zt_f), (xb, abajo, zb_f), (xb, abajo, zb_b)], tela)
    panel([(-xt, lado_i, zt_f), (-xt, lado_i, zt_b), (-xb, abajo, zb_b), (-xb, abajo, zb_f)], tela)
    panel([(1.9, sup_d, zt_f), (xt, sup_d, zt_f), (xb, abajo, zb_f), (2.4, abajo, zb_f)], tela)
    panel([(-xt, sup_i, zt_f), (-1.9, sup_i, zt_f), (-2.4, abajo, zb_f), (-xb, abajo, zb_f)], tela)
    # solapas negras a lo largo de la abertura (un poco adelante del delantero)
    for s, sup in ((1, sup_d), (-1, sup_i)):
        pts = [(s * 1.65, sup + 0.3, zt_f - 0.1), (s * 2.35, sup + 0.3, zt_f - 0.1),
               (s * 2.85, abajo + 0.3, zb_f - 0.1), (s * 2.15, abajo + 0.3, zb_f - 0.1)]
        if s < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        idx = [m.v((q[0], q[1], q[2])) for q in pts]
        m.cara(tuple(idx), (0, 0, -1), "solapa")
        pint.append(color(NEGRO))
    return (m.vs, m.caras), pint


MANGA_Z_FRENTE, MANGA_Z_ATRAS = -2.9, 3.3


def final_manga(mano):
    """Altura del borde de abajo de la manga segun z (adelante en la muneca, atras la bolsa cuelga mas)."""
    puno, bolsa = mano + 2.6, mano - 1.2

    def f(t):
        k = (t.z - MANGA_Z_FRENTE) / (MANGA_Z_ATRAS - MANGA_Z_FRENTE)
        return puno + (bolsa - puno) * max(0.0, min(1.0, k))
    return f


def manga_kimono(arriba, mano):
    """Manga ancha de kimono (lado derecho): trapecio que se abre hacia afuera y hacia abajo; adelante termina en la
    muneca (la mano sale por ahi) y atras cuelga mas, como la bolsa del kimono."""
    xi, xo_arriba, xo_abajo = 3.55, 6.7, 9.0
    puno, bolsa = mano + 2.6, mano - 1.2
    sup = [(xo_arriba, arriba, 1.7), (xo_arriba, arriba, -1.7), (xi, arriba, -1.7), (xi, arriba, 1.7)]
    inf = [(xo_abajo, bolsa, MANGA_Z_ATRAS), (xo_abajo, puno, MANGA_Z_FRENTE), (xi + 0.05, puno, MANGA_Z_FRENTE),
           (xi + 0.05, bolsa, MANGA_Z_ATRAS)]
    return tubo_hueco(inf, sup)


# ---------------------------------------------------------------- zapatillas, cubo por cubo

def suela_manchada(t):
    """Plataforma blanca con manchas negras irregulares (como la referencia)."""
    if t.cara == "down":
        return hex_(GRIS)
    f = _h(t.x * 1.4 // 1, t.y * 1.4 // 1, t.z * 1.4 // 1) * 0.6 + 0.4 * (0.5 + 0.5 * math.sin(t.z * 1.3 + t.x * 0.7))
    return hex_(NEGRO if f > 0.68 and t.cara != "up" else (BLANCO if t.cara != "up" else "#F4F1EC"))


def capellada(t):
    """Capellada negra con un panel blanco a cada costado."""
    if abs(t.n[0]) > 0.7 and -2.6 < t.z < 0.8 and 1.8 < t.y < 2.9 + 0.35 * (t.z + 2.6):
        return hex_(BLANCO)
    return hex_(NEGRO2 if t.cara == "up" else NEGRO)


def zapatilla(p, g, x, s):
    """Zapatilla de calle GORDA y baja, con la geometria del dibujo: plataforma con escalon (hueco en el arco),
    punta larga y baja, capellada que sube en rampa hasta el tobillo (perfil extruido), puntera y talonera blancas,
    cordones amarillos sobre la rampa, y arriba un PUNO del tobillo mas angosto con dos correas y hebilla."""
    def cubo(nombre, xa, xb, y1, y2, z1, z2, pintor, rot=None, piv=None):
        a, b = x(xa, xb)
        piv2 = None if piv is None else (s * piv[0], piv[1], piv[2])
        rot2 = None if rot is None else (rot[0], rot[1] * s, rot[2] * s)
        if abs(a - b) < 1e-6:
            p.plano(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=3)
        else:
            p.caja(g, nombre, (a, y1, z1), (b, y2, z2), pintor, rot2, piv2, dens=3)

    blanco, negro, amarillo = color(BLANCO), color(NEGRO), color(AMARILLO["b"])
    # plataforma ancha con escalon abajo (hueco en el arco) y bordes redondeados con dos cajas cruzadas
    cubo("suela_baja_frente", 0.45, 4.4, 0.0, 0.55, -4.1, -1.1, suela_manchada)
    cubo("suela_baja_atras", 0.45, 4.4, 0.0, 0.55, 0.7, 2.6, suela_manchada)
    cubo("suela_arco", 0.7, 4.15, 0.3, 0.55, -1.1, 0.7, color(GRIS))
    cubo("suela_ancha", 0.15, 4.7, 0.55, 1.6, -3.7, 2.3, suela_manchada)
    cubo("suela_larga", 0.45, 4.4, 0.55, 1.6, -4.2, 2.7, suela_manchada)
    # capellada: perfil de costado (punta baja, rampa, tobillo) extruido a lo ancho
    perfil = [(-4.0, 1.6), (-3.9, 2.35), (-3.2, 2.75), (-1.0, 3.55), (-0.75, 3.9), (2.45, 3.9), (2.6, 1.6)]
    malla = geo.extruir_x(perfil, 0.5, 4.3)
    p.malla(g, "capellada", malla if s > 0 else geo.espejo_x(malla), capellada, dens=3)
    cubo("puntera", 0.7, 4.1, 1.6, 2.25, -4.15, -3.45, blanco)
    cubo("talonera", 0.6, 4.0, 1.6, 3.4, 2.5, 2.75, blanco)
    rampa = dict(rot=(-20.0, 0, 0), piv=(2.3, 3.55, -1.0))
    cubo("cordon", 1.6, 3.0, 3.55, 3.67, -3.2, -1.0, amarillo, **rampa)
    for k, zc in enumerate((-2.7, -1.8)):
        cubo(f"cordon_cruce{k}", 1.0, 3.6, 3.55, 3.65, zc - 0.18, zc + 0.18, amarillo, **rampa)
    # puno del tobillo, mas angosto, con dos correas, hebilla amarilla y lengueta
    cubo("puno", 0.0, 3.8, 3.6, 5.2, -1.95, 2.3, negro)                   # rodea la pierna (que mide +-1.75)
    cubo("correa1", -0.05, 3.9, 3.85, 4.25, -2.05, 2.4, color("#D8D4CE"))
    cubo("correa2", -0.05, 3.9, 4.5, 4.95, -2.05, 2.4, negro)
    cubo("hebilla", 1.3, 2.4, 4.4, 5.05, -2.27, -2.03, amarillo)
    cubo("hebilla_perno", 1.7, 2.0, 4.6, 4.85, -2.34, -2.25, oro)
    cubo("lengueta", 1.1, 2.6, 3.5, 4.4, -2.15, -1.9, negro)
    cubo("lengueta_punta", 1.1, 2.6, 5.0, 5.6, -2.15, -1.9, blanco)
    cubo("tira_colgando", 3.95, 3.95, 3.0, 4.5, -1.3, -0.7, amarillo, rot=(0, 0, -8), piv=(3.95, 4.5, -1.0))


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("correctar", altura=40, cabeza=8, torso=(7, 10, 3.5), brazo=(2.8, 2.8), pierna=(3.5, 3.5))
    C, T, L = p.cuello, p.tope, p.lh                           # 32, 40, 22: cintura alta y piernas largas

    # ================================================================ CABEZA y cara
    p.caja("Head/cabeza", "cabeza", (-4, C, -4), (4, T, 4), sprite({"north": CARA}, PAL_CARA, base=piel), dens=3)

    # ================================================================ PELO: mechones puntiagudos de anime
    # casco ajustado (cajas) + mechones como piramides de base rectangular que apuntan cada uno a su lado:
    # flequillo barrido hacia la izquierda, costados que tapan las orejas, nuca hacia abajo y atras, puntas arriba
    g = "Head/pelo"
    p.caja(g, "casco_arriba", (-4.35, T - 0.6, -4.35), (4.35, T + 0.6, 4.35), pelo_plano, dens=2)
    p.caja(g, "casco_nuca", (-4.35, C + 1.4, 3.7), (4.35, T - 0.6, 4.35), pelo_plano, dens=2)
    for s in (1, -1):
        x1, x2 = sorted((s * 3.7, s * 4.35))
        p.caja(g, f"casco_lado{s}", (x1, C + 3.0, -3.6), (x2, T - 0.6, 3.7), pelo_plano, dens=2)
    p.caja(g, "casco_frente", (-4.35, T - 1.4, -4.35), (4.35, T - 0.6, -3.7), pelo_plano, dens=2)
    mechas = []
    for x, largo in ((-3.1, 3.3), (-1.5, 4.1), (0.2, 3.5), (1.8, 4.3), (3.3, 3.1)):        # flequillo
        mechas.append(((x, T - 0.4, -4.25), 2.1, 1.0, (-0.32, -1.0, -0.22), largo, "negro"))
    for s in (1, -1):                                                                      # costados
        for y, z, largo in ((T - 1.4, -2.6, 3.6), (T - 1.6, 0.0, 4.4), (T - 2.0, 2.6, 4.2),
                            (T - 3.6, -1.3, 3.4), (T - 4.0, 1.4, 3.8)):
            blanco = s < 0 and z < -2
            mechas.append(((s * 4.2, y, z), 0.9, 2.0, (s * 0.45, -1.0, 0.05), largo, "blanco" if blanco else "negro"))
    for x, y, largo in ((-3.0, T - 1.0, 3.8), (-1.0, T - 1.0, 4.4), (1.0, T - 1.0, 4.2), (3.0, T - 1.0, 3.6),
                        (-2.0, T - 3.2, 3.6), (0.0, T - 3.2, 4.0), (2.0, T - 3.2, 3.4)):    # nuca
        tinte = "rojo" if (x, y) == (-2.0, T - 3.2) else "negro"
        mechas.append(((x, y, 4.2), 2.2, 1.0, (x * 0.08, -1.0, 0.5), largo, tinte))
    for x, z, largo in ((-2.6, -2.4, 2.4), (0.0, -2.8, 2.8), (2.6, -2.2, 2.3), (-3.0, 0.4, 2.6), (0.2, 0.0, 3.0),
                        (3.1, 0.6, 2.4), (-1.6, 2.8, 2.6), (1.6, 3.0, 2.8), (0.0, 4.0, 2.2)):   # arriba
        tinte = "blanco" if (x, z) in ((-3.0, 0.4), (-2.6, -2.4)) else "negro"
        mechas.append(((x, T + 0.4, z), 2.4, 2.2, (x * 0.18, 1.0, 0.35 + z * 0.08), largo, tinte))
    pint = {"negro": pelo_malla(PELO["k"], PELO["h"], PELO["d"]), "blanco": pelo_malla(BLANCO, "#FFFFFF", GRIS),
            "rojo": pelo_malla(ROJO["b"], ROJO["l"], ROJO["s"])}
    for k, (base, ancho, fondo, direccion, largo, tinte) in enumerate(mechas):
        p.malla(g, f"mecha{k}", mecha(base, ancho, fondo, direccion, largo), pint[tinte], dens=3)
    # cinta roja del lado izquierdo
    p.caja(g, "cinta_roja", (-5.0, T - 2.8, -2.0), (-4.3, T + 0.4, -0.7), color(ROJO["b"]), rot=(0, 0, 18),
           piv=(-4.65, T + 0.4, -1.35), dens=2)
    p.caja(g, "cinta_roja2", (-5.4, T - 0.9, -1.9), (-4.4, T + 0.2, -0.6), color(ROJO["l"]), dens=2)

    # ================================================================ ARETE con talisman (izquierda)
    g = "Head/aretes"
    p.caja(g, "argolla", (-4.55, C + 2.4, -0.4), (-4.25, C + 3.2, 0.4), oro, dens=3)
    p.caja(g, "cadena", (-4.75, C + 1.4, -0.1), (-4.55, C + 2.6, 0.1), oro, dens=3)
    p.plano(g, "talisman", (-5.4, C - 1.2, -0.2), (-4.3, C + 1.5, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN), dens=3)

    # ================================================================ TORSO delgado
    torso = torso_dibujo(21, 30)
    pal_torso = {"p": PIEL["b"], "s": PIEL["s"], "k": "#181214", "d": PIEL["s2"]}
    p.caja("Body/torso", "torso", (-3.5, L, -1.75), (3.5, C, 1.75), sprite({"north": torso}, pal_torso, base=piel), dens=3)
    p.caja("Body/collar", "moneda", (-0.75, C - 4.3, -2.05), (0.75, C - 2.8, -1.75), oro, rot=(0, 0, 45),
           piv=(0, C - 3.55, -1.9), dens=3)
    p.caja("Body/collar", "moneda_centro", (-0.3, C - 3.85, -2.15), (0.3, C - 3.25, -2.0), color("#5A4416"), dens=3)

    # ================================================================ FAJA con nudo
    p.caja("Body/faja", "faja", (-3.9, L - 1.0, -2.15), (3.9, L + 1.2, 2.15), color(NEGRO2), dens=2)
    p.caja("Body/faja", "nudo", (-0.2, L - 1.3, -2.75), (1.8, L + 1.0, -2.15), color(NEGRO), dens=2)

    # ================================================================ HAORI: chaqueta aparte que se abre en la cadera
    g = "Body/haori"
    abajo = L - 5.4                                             # el haori llega a la cadera
    def final(t, y=abajo):                                      # la franja blanca va al final del haori
        return y
    tela = manchas(deshilachado=(1.0, 3), borde=final)
    espalda = encima(manchas(deshilachado=(1.0, 5), kanji=C - 8.5, borde=final),
                     [("south", 3, 6, KANJI, {"W": BLANCO})])
    malla, pintores = haori(C, abajo, tela, espalda)
    p.malla(g, "haori", malla, pintores, dens=3)

    # ================================================================ BRAZOS finos, hombros desnudos, MANGAS de paneles
    mano = C - 15.0                                             # punta de los dedos: a la altura de la entrepierna
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 3.5, s * 6.3))
        cara_fuera = "east" if s > 0 else "west"
        p.caja(f"{hueso}/brazo", "brazo", (x1, mano, -1.4), (x2, C, 1.4),
               encima(piel, [(cara_fuera, 2, 3, TATUAJE, {"k": "#181214"})]), dens=3)
        p.caja(f"{hueso}/anillo", "anillo", (x1 - 0.12, mano + 1.2, -1.52), (x2 + 0.12, mano + 1.6, 1.52),
               lambda t: hex_(ORO["b"] if t.i % 4 == 1 else NEGRO), dens=3)
        fin_manga = final_manga(mano)                           # el final de la manga queda blanco
        if s > 0:     # derecha: la chaqueta tapa el hombro; manga entera, mas negra
            arriba = C + 0.3
            tela_m = manchas(deshilachado=(1.0, 8), sesgo=-0.1, borde=fin_manga)
        else:         # izquierda: caida del hombro (se ve el tatuaje); manga con manchones blancos grandes
            arriba = C - 4.0
            tela_m = manchas(deshilachado=(1.0, 6), sesgo=0.14, borde=fin_manga)
        malla, n_fuera = manga_kimono(arriba, mano)
        if s < 0:
            malla = geo.espejo_x(malla)
        pint = [tela_m] * n_fuera + [color(NEGRO2)] * (len(malla[1]) - n_fuera)
        p.malla(f"{hueso}/manga", "manga", malla, pint, dens=3)

    # ================================================================ CINTAS: roja adelante y atras, amarilla con talisman
    g = "Body/cintas"
    p.plano(g, "roja_frente", (0.1, L - 8.0, -2.8), (1.6, L - 0.6, -2.8), cinta(ROJO), rot=(0, 0, -3),
            piv=(0.85, L - 0.6, -2.8), dens=3)
    y_arriba = C - 6.6
    z_arriba = 2.2 + 0.9 * (C + 0.4 - y_arriba) / (C + 0.4 - abajo) + 0.14
    p.plano(g, "roja_espalda", (0.6, abajo + 0.5, z_arriba), (2.0, y_arriba, z_arriba), cinta(ROJO),
            rot=(-3.3, 0, 0), piv=(1.3, y_arriba, z_arriba), dens=3)
    x = -5.25
    p.plano(g, "amarilla_lado", (x, abajo - 7.5, -1.4), (x, abajo + 0.2, -0.1), cinta(AMARILLO, "#6A4A08"),
            rot=(0, 0, -4), piv=(x, abajo + 0.2, -0.75), dens=3)
    p.plano(g, "talisman_lado", (x, abajo - 10.6, -1.3), (x, abajo - 7.3, -0.2), sprite({"todas": TALISMAN}, PAL_TALISMAN),
            rot=(0, 0, -4), piv=(x, abajo + 0.2, -0.75), dens=3)

    # ================================================================ HAKAMA ancho y ZAPATILLAS gruesas
    for s in (1, -1):
        hueso = "RightLeg" if s > 0 else "LeftLeg"

        def x(a, b):
            return sorted((s * a, s * b))
        a, b = x(0.1, 3.6)
        p.caja(f"{hueso}/pierna", "pierna", (a, 3.8, -1.75), (b, L, 1.75),
               lambda t: hex_(PIEL["b"] if t.y < 6.4 else NEGRO), dens=2)        # el tobillo se ve
        # hakama: trapecio ancho de la cintura a media pantorrilla
        cintura = [(3.8, L + 0.6, 2.3), (3.8, L + 0.6, -2.3), (0.05, L + 0.6, -2.3), (0.05, L + 0.6, 2.3)]
        ruedo = [(5.4, 6.4, 3.3), (5.4, 6.4, -3.4), (0.7, 6.4, -3.4), (0.7, 6.4, 3.3)]      # se separan abajo
        malla = geo.tronco(ruedo, cintura)
        p.malla(f"{hueso}/pantalon", "hakama", malla if s > 0 else geo.espejo_x(malla), pantalon, dens=2)
        g = f"{hueso}/zapatilla"
        zapatilla(p, g, x, s)
    return p


def accesorios():
    """La mascara amarilla de cubo (ojos en cruz y sonrisa), como modelo aparte."""
    o = Objeto("correctar_mascara")
    o.caja("cubo", (-4, 0, -4), (4, 8, 4), sprite({"north": CARA_MASCARA}, {"y": AMARILLO["b"], "k": "#161214"},
                                                   base=color(AMARILLO["b"])), dens=2)
    return [o]
