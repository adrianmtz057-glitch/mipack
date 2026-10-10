"""
Moles, la hermana de Pibble: una sause (semidiosa) kitsune, nueva, de la misma estrella que el. Lo sigue porque
tambien se alimenta de diversion, pero no son unidos: es rara su relacion. Sarcastica, graciosa y muy alegre.
Hecha a mano con el kit segun referencias/personajes/moles.png. Chibi de la altura de Pibble, no humana.

Por ahora solo el cuerpo (sin ropa ni accesorios), con las proporciones del boceto: cabeza enorme y ancha, cuerpo
chiquito y piernas cortas con patas.
  CARA de la referencia: ojos grandes y separados, pestana negra gruesa con la punta hacia afuera, iris ambar con
    brillo, cejitas picaras, naricita rosa, boca de gatito abierta con la lengua y mucho rubor
  PELO rubio claro, todo en cubos: casco redondeado en escalones, flequillo en mechones de distinto largo, volumen a
    los costados, mechones largos adelante y la melena de atras en puntas
  OREJAS de zorro grandes y redondeadas, en las esquinas de arriba y abiertas hacia afuera
"""

from ..kit import Personaje, tonos
from ..textura import TRANSPARENTE, hex_a_rgba as hex_
from .revolthir import color, voxel

D = 4                                   # texeles por px
D_CARA = 8                              # la cabeza, con mas detalle para la cara

PELO = {"s": "#EBC567", "b": "#F7D77C", "l": "#FCE8A8"}              # rubio claro, con poca sombra
OREJA = {"s": "#EFE2D2", "b": "#FAF1E6", "l": "#FFFAF2"}
PIEL, PIEL_BAJO = "#FFEAE4", "#FCDDD6"                            # blanco rosita
RUBOR, RUBOR_FUERTE = "#F7B1A8", "#F29A93"
ROSA_OREJA = "#F4A9A6"
AMBAR, AMBAR_CLARO, PUPILA, PESTANA = "#EE8E2A", "#F9C54E", "#3A1A12", "#1C1418"
LENGUA, BOCA = "#F08A8F", "#5A2430"

CUELLO = 11.0                           # la cabeza va de 11 a 21
CABEZA_ALTO = 10.0


def _en(u, v, u0, u1, v0, v1):
    return u0 <= u <= u1 and v0 <= v <= v1


def piel(t):
    """Piel blanca calida, lisa: apenas mas rosada abajo."""
    alto = max(1e-6, t.t[1] - t.f[1])
    return hex_(PIEL_BAJO if (t.y - t.f[1]) / alto < 0.18 and t.cara != "up" else PIEL)


def ojo(u, v):
    """Un ojo como el del boceto (u en valor absoluto desde el centro de la cara, v desde el menton) o None: pestana
    negra gruesa arriba con la punta hacia afuera; adentro, el iris pegado a la nariz (mirada bizca, como en el
    boceto) con la pupila oscura arriba, naranja y amarillo abajo, un brillo, y lo blanco en la esquina de afuera."""
    if 4.0 <= u <= 4.95 and abs(v - (4.75 - (u - 4.0) * 0.9)) < 0.28:   # la linea de la esquina, hacia afuera
        return hex_(PESTANA)
    if not _en(u, v, 1.3, 4.5, 2.2, 5.0):
        return None
    arriba = 4.35 + 0.25 * (u - 1.3) / 3.2                               # la pestana sube hacia afuera
    if v > arriba or (u > 4.0 and v > 3.7):                              # pestana gruesa con la punta afuera
        # el borde de arriba de la pestana en picos suaves: se ve tupida, como pelusa, sin pelos sueltos
        pico = 0.3 * abs(((u * 2.2) % 1.0) - 0.5) * 2 + 0.2 * max(0.0, (u - 3.0) / 1.5)
        return hex_(PESTANA) if v < arriba + 0.38 + pico and not (u < 1.6 and v > 4.6) else None
    if u < 1.55 or u > 4.0:
        return hex_(PESTANA) if v > 3.0 else None                       # el borde solo arriba
    if u > 3.35:                                                         # lo blanco, en la esquina de afuera
        return hex_("#FFFFFF") if v >= 2.85 else None
    if _en(u, v, 1.75, 2.05, 3.85, 4.15):                               # brillo
        return hex_("#FFFFFF")
    if _en(u, v, 1.55, 2.75, 3.3, arriba):                              # pupila hacia la nariz: bizca
        return hex_(PUPILA)
    return hex_(AMBAR) if v >= 2.85 else None                          # abajo: cara, sin el naranja claro


def boca(u, v):
    """Boca sonriente de gatito: arriba la linea en w y abajo abierta en D, toda rosa."""
    au = abs(u)
    if au > 1.25:
        return None
    arriba = 2.05 - 0.25 * (1 - min(1.0, abs(au - 0.55) / 0.55))      # la w: baja en el medio de cada lado
    abajo = 0.75 + 0.85 * (au / 1.25) ** 2                             # fondo redondo, comisuras arriba
    if not (abajo <= v <= arriba + 0.12):
        return None
    if v > arriba - 0.08:                                              # la linea de arriba (la w)
        return hex_(BOCA)
    return hex_(LENGUA)                                                # toda rosa, sin dientes ni sombra


def cara(t):
    u, v = -t.x, t.y - CUELLO
    c = ojo(abs(u), v) or boca(u, v)
    if c:
        return c
    au = abs(u)
    if 1.5 <= au <= 3.5:                                               # cejas finas y arqueadas; la izquierda
        x = (au - 2.5) / 1.0                                           # (derecha de quien mira) mas levantada
        ceja = 5.2 + 0.22 * (1 - x * x) + (0.18 if u > 0 else 0.0)
        if abs(v - ceja) < 0.09:
            return hex_(PESTANA)
    if _en(abs(u), v, 2.5, 4.9, 1.2, 2.5):                             # rubor
        return hex_(RUBOR_FUERTE if _en(abs(u), v, 3.0, 4.4, 1.5, 2.2) else RUBOR)
    if _en(u, v, -0.25, 0.25, 2.45, 2.7) or _en(u, v, -0.12, 0.12, 2.3, 2.45):   # naricita
        return hex_(RUBOR_FUERTE)
    return piel(t)


def cabeza(t):
    return cara(t) if t.cara == "north" else piel(t)


PELO_TEX = voxel(PELO, claro=0.3)


def oreja_adentro(t):
    return hex_(ROSA_OREJA)


def pata(t):
    """Pata blanca con tres almohadillas rosas adelante."""
    if t.cara == "north" and t.y < 1.1:
        u = (t.x - t.f[0]) / max(1e-6, t.t[0] - t.f[0])
        if 0.3 < t.y < 0.9 and any(abs(u - c) < 0.11 for c in (0.22, 0.5, 0.78)):
            return hex_(RUBOR_FUERTE)
    return piel(t)


TONOS_MECHON = ("b", "l", "b", "s", "l", "b")             # cada mechon con su tono liso (se separan entre si)


def liso(col):
    c = hex_(col)
    return lambda t: c


def mechon(p, nombre, x0, x1, z0, z1, abajo, arriba, k, onda=0.0, eje="x"):
    """Un mechon de bloque que cuelga de 'arriba' a 'abajo' en tres tramos; con onda cada tramo se corre a un lado y
    al otro (se ve ondulado). eje: hacia donde se corre ('x' adelante/atras, 'z' en los costados)."""
    tono = liso(PELO[TONOS_MECHON[k % len(TONOS_MECHON)]])
    largo = (arriba - abajo) / 3
    for i in range(3):
        d = onda * (0, 1, -1)[i]
        dx, dz = (d, 0) if eje == "x" else (0, d)
        y1, y0 = arriba - i * largo, arriba - (i + 1) * largo
        p.caja("Head/pelo", f"{nombre}_{i}", (x0 + dx, y0, z0 + dz), (x1 + dx, y1 + 0.02, z1 + dz), tono, dens=D)


def pelo(p, C, T):
    """El pelo rubio en mechones lisos (cada uno de su tono): el casco, el flequillo disparejo arriba de los ojos,
    los mechones de adelante que enmarcan la cara (ondulados), los costados en mechones, y atras la melena que
    termina recta en la nuca con una capa de arriba mas corta al medio."""
    g = "Head/pelo"
    p.caja(g, "casco", (-5.5, T - 2.8, -5.5), (5.5, T + 0.5, 5.5), liso(PELO["b"]), dens=D)
    p.caja(g, "casco_alto", (-4.8, T + 0.5, -4.8), (4.8, T + 1.0, 4.8), liso(PELO["l"]), dens=D)
    k = 0
    # flequillo: arriba de las cejas, disparejo
    ancho = 11.0 / 8
    for i, abajo in enumerate((5.9, 6.4, 5.6, 6.2, 5.5, 6.3, 5.8, 6.5)):
        x = -5.5 + i * ancho
        z0 = -6.0 if i % 2 else -5.8
        mechon(p, f"fleco{i}", x, x + ancho, z0, -5.4, C + abajo, T + 0.4, k)
        k += 1
    for s in (1, -1):
        # mechones de adelante, a los lados de la cara, ondulados
        for i, (xa, xb, abajo) in enumerate(((4.3, 5.5, C - 1.0), (5.3, 6.3, C + 0.4))):
            a, b = sorted((s * xa, s * xb))
            mechon(p, f"lado_frente{s}_{i}", a, b, -6.0, -4.4, abajo, T - 0.5, k, onda=0.3 * s)
            k += 1
    campana(p, C, T, k)


def tira_pelo(ancho, largo, k, grueso=0.7):
    """Un mechon plano colgando desde (0, 0), con la punta escalonada (patron fijo por mechon)."""
    from .. import malla as geo
    w = ancho / 2
    a = (0.0, 0.5, 0.8)[k % 3]
    perfil = [(-w, 0.0), (w, 0.0), (w, -largo + a)] + ([(0.1, -largo + a)] if a else []) + [(0.1, -largo), (-w, -largo)]
    return geo.extruir(perfil, -grueso / 2, grueso / 2)


def campana(p, C, T, k0):
    """El pelo de los costados y de atras como una CAMPANA: mechones que nacen alrededor de la cabeza (menos en la
    cara) y se abren hacia afuera y hacia abajo hasta pasar la cabeza; atras son mas largos y hacia la cara mas cortos,
    asi el borde de abajo queda redondo. Dos capas, la de adentro un tono mas oscuro, tapa los huecos."""
    import math
    from .. import malla as geo
    for capa, (n, fuera, abre, oscuro) in enumerate(((20, 0.35, 16.0, False), (20, 0.0, 11.0, True))):
        for i in range(n):
            ang = 180 + 360 * (i + 0.5 * capa) / n
            frente = abs(((ang - 180 + 180) % 360) - 180)       # 0 adelante, 180 atras
            if frente < 55:
                continue                                         # la cara queda libre
            a = math.radians(ang)
            sx, sz = math.sin(a), math.cos(a)
            r = 1.0 / max(abs(sx), abs(sz)) * 5.4
            x, z = r * sx + sx * fuera, r * sz + sz * fuera
            atras = (frente - 55) / 125                          # 0 junto a la cara, 1 atras al medio
            largo = 7.0 + 5.5 * math.sin(atras * math.pi / 2) - 0.4 * capa
            m = tira_pelo(2.0, largo, k0 + i)
            m = geo.girar(m, (abre, ang - 180, 0))
            m = geo.mover(m, (x, T - 0.6, z))
            tono = PELO["s"] if oscuro else PELO[("b", "l", "b")[i % 3]]
            p.malla("Head/pelo", f"campana{capa}_{i}", m, liso(tono), dens=D)


PELUSA = {"s": "#F6DFA8", "b": "#FBEEC8", "l": "#FFF7E2"}


def orejas(p, T):
    """Orejas de zorro grandes y en punta: nacen al ras del costado de la cabeza (el borde de afuera sigue la linea
    del costado) y se angostan hacia adentro hasta la punta, a media cabeza; el adentro rosa adelante."""
    g = "Head/orejas"
    afuera = 5.5
    for s in (1, -1):
        y = T + 0.4
        for k, (ancho, alto) in enumerate(((5.0, 1.0), (4.4, 1.0), (3.8, 1.0), (3.1, 0.9), (2.4, 0.9), (1.6, 0.8),
                                           (0.9, 0.7))):
            a, b = sorted((s * (afuera - 0.25 * k), s * (afuera - 0.25 * k - ancho)))
            p.caja(g, f"oreja{s}_{k}", (a, y, -0.6), (b, y + alto, 0.8), liso(PELO["b"]), dens=D,
                   rot=(-6, 0, 0), piv=(s * 3.0, T + 0.4, 0.2))
            if k < 6:
                c, d = sorted((s * (afuera - 0.25 * k - 0.6), s * (afuera - 0.25 * k - ancho + 0.9)))
                p.caja(g, f"adentro{s}_{k}", (c, y + 0.1, -0.75), (d, y + alto, -0.6), liso(ROSA_OREJA), dens=D,
                       rot=(-6, 0, 0), piv=(s * 3.0, T + 0.4, 0.2))
            y += alto


def _inclinar(c, piv, rz):
    """Lleva un cubo suelto al giro de la oreja: mueve su centro alrededor de piv y le suma el giro en Z."""
    import math
    a = math.radians(rz)
    cx, cy = [(c.desde[i] + c.hasta[i]) / 2 for i in range(2)]
    dx, dy = cx - piv[0], cy - piv[1]
    nx, ny = piv[0] + dx * math.cos(a) - dy * math.sin(a), piv[1] + dx * math.sin(a) + dy * math.cos(a)
    for i, d in ((0, nx - cx), (1, ny - cy)):
        c.desde[i] += d
        c.hasta[i] += d
    c.origen = [nx, ny, c.origen[2]]
    c.rot = [c.rot[0], c.rot[1], c.rot[2] + rz] if c.rot else [0, 0, rz]


def pestanas(p, C):
    """Las pestanas en 3D: tiras negras chiquitas que salen de la cara sobre cada ojo, de alturas alternadas para que
    se vean tupidas, y la punta de afuera que baja en diagonal."""
    g = "Head/pestanas"
    for lado in (1, -1):                                       # lado 1: a la derecha de quien mira (u > 0)
        k = 0
        u = 1.3
        while u < 4.3:
            arriba = 4.35 + 0.25 * (u - 1.3) / 3.2
            alto = 0.45 + (0.28 if k % 2 else 0.08) + 0.2 * max(0.0, (u - 3.0) / 1.3)
            x1, x2 = sorted((-lado * u, -lado * (u + 0.34)))
            p.caja(g, f"pestana{lado}_{k}", (x1, C + arriba, -5.32), (x2, C + arriba + alto, -4.98), color(PESTANA),
                   dens=D_CARA, luz=False)
            u += 0.32
            k += 1
        for i, (du, dv) in enumerate(((0.0, 0.0), (0.3, -0.3), (0.55, -0.6))):   # la punta de afuera
            x1, x2 = sorted((-lado * (4.3 + du), -lado * (4.65 + du)))
            p.caja(g, f"punta{lado}_{i}", (x1, C + 4.25 + dv, -5.32), (x2, C + 4.75 + dv, -4.98), color(PESTANA),
                   dens=D_CARA, luz=False)


NEGRO = {"s": "#2C232B", "b": "#3D3340", "l": "#524555"}
ROJO, CREMA_DIJE = "#C8343A", "#FBF1DE"


def sudadera(t):
    """Negra de bloques; adelante, la etiqueta roja con su cuadrito blanco."""
    if t.cara == "north" and _en(t.x, t.y, -0.75, 0.75, 7.6, 9.6):
        return hex_("#F4EEE8" if _en(t.x, t.y, -0.3, 0.3, 7.9, 8.8) else ROJO)
    return voxel(NEGRO, claro=0.05)(t)


def calaverita(t):
    if t.cara == "north" and 4.15 < t.y < 4.5 and any(abs(t.x - c) < 0.17 for c in (-3.95, -3.35)):
        return hex_(PESTANA)
    return hex_(CREMA_DIJE)


def ropa(p, C, L):
    """La ropa, en sus propios grupos (aparte del pelo, para prenderla y apagarla en Figura): sudadera negra enorme
    con capucha atras, cordones rojos de punta blanca, etiqueta, dije de calaverita y mangas anchas."""
    g = "Body/ropa"
    p.caja(g, "sudadera", (-3.4, L - 1.6, -2.1), (3.4, C + 0.1, 2.1), sudadera, dens=D)
    p.caja(g, "capucha", (-2.9, C - 2.0, 2.1), (2.9, C + 0.4, 3.2), voxel(NEGRO, claro=0.1), dens=D)   # bajo la melena
    # cuello envolvente chiquito (como el de la foto): un rollo de tela alrededor y la solapa cruzada adelante
    p.caja(g, "cuello", (-3.0, C - 1.3, -2.75), (3.0, C, 2.6), voxel(NEGRO, claro=0.2), dens=D)
    p.caja(g, "solapa", (-2.6, C - 1.9, -3.0), (1.2, C - 0.4, -2.7), voxel(NEGRO, claro=0.25), rot=(0, 0, -22),
           piv=(-0.7, C - 1.1, -2.85), dens=D)
    for s, largo in ((1, 3.4), (-1, 2.8)):
        x1, x2 = sorted((s * 1.0, s * 1.3))
        p.caja(g, f"cordon{s}", (x1, C - largo, -2.3), (x2, C - 0.1, -2.1), color(ROJO), dens=D)
        p.caja(g, f"punta_cordon{s}", (x1 - 0.05, C - largo - 0.5, -2.35), (x2 + 0.05, C - largo, -2.1),
               color("#F4EEE8"), dens=D)
    # dije de calaverita colgado de una tira roja, a su derecha de la cadera
    p.caja(g, "tira", (-3.75, 4.6, -2.25), (-3.5, L + 0.6, -2.1), color(ROJO), dens=D)
    p.caja(g, "calaverita", (-4.3, 3.2, -2.6), (-3.0, 4.7, -2.2), calaverita, dens=D)
    # mangas con caida: hombro caido y angosto, el globo de tela que se junta abajo y se ensancha, y el puno de
    # elastico apretado contra la mano
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        partes = (("hombro", 2.8, 5.0, C - 2.2, C + 0.1, 1.25, voxel(NEGRO, claro=0.1)),
                  ("globo", 2.65, 5.55, L + 0.45, C - 1.9, 1.6, voxel(NEGRO, claro=0.02)),
                  ("puno", 3.0, 4.95, L - 0.5, L + 0.5, 1.1, puno))
        for nombre, x0, x1, y0, y1, z, pint in partes:
            a, b = sorted((s * x0, s * x1))
            p.caja(f"{hueso}/ropa", nombre, (a, y0, -z), (b, y1, z), pint, dens=D)


def puno(t):
    """Puno de elastico: rayitas verticales."""
    u = t.x if t.cara in ("north", "south") else t.z
    return hex_(NEGRO["s"] if (u * 4) % 1.0 < 0.3 else NEGRO["b"])


# ---------------------------------------------------------------- la cola

# la curva va hacia atras y hacia su derecha, y termina debajo y detras de la melena: no la toca
CAMINO_COLA = ((0.0, 4.2, 1.8, 0.95), (1.0, 3.4, 4.4, 1.7), (2.4, 4.4, 7.0, 2.4), (3.4, 6.6, 8.6, 2.7),
               (3.6, 8.8, 9.0, 2.45), (3.0, 10.6, 8.6, 1.85), (2.2, 11.6, 7.9, 1.1))     # (x, y, z, radio)
COLA_RUBIA = voxel(PELO, claro=0.3)
COLA_CREMA = voxel({"s": "#F6DFA8", "b": "#FBEEC8", "l": "#FFF7E2"}, claro=0.3)        # crema calida


def _cola_puntos(pasos=4):
    out = []
    for k in range(len(CAMINO_COLA) - 1):
        a, b = CAMINO_COLA[k], CAMINO_COLA[k + 1]
        for i in range(pasos):
            f = i / pasos
            out.append(tuple(a[j] + (b[j] - a[j]) * f for j in range(4)) + (k + f,))
    return out + [CAMINO_COLA[-1] + (len(CAMINO_COLA) - 1,)]


def cola(p):
    """Cola esponjosa de muchos cubos: en cada punto de la curva, un cubo grande del medio y seis copos alrededor, cada
    uno con su tamano y su giro (un patron fijo que va rotando). Rubia en la base y crema en la punta."""
    import math
    pts = _cola_puntos()
    total = len(CAMINO_COLA) - 1
    for k, (x, y, z, r, f) in enumerate(pts):
        pint = COLA_RUBIA if f / total < 0.62 else COLA_CREMA
        lado = r * 1.25
        p.caja("Body/cola", f"cola{k}", (x - lado / 2, y - lado / 2, z - lado / 2),
               (x + lado / 2, y + lado / 2, z + lado / 2), pint,
               rot=((k * 23) % 45 - 22, (k * 31) % 45 - 22, (k * 17) % 45 - 22), dens=D)
        for i in range(6):
            a = math.radians(i * 60 + k * 27)
            d = r * 0.78
            cx, cy, cz = x + d * math.cos(a), y + d * math.sin(a) * 0.8, z + d * math.sin(a + 1.1) * 0.7
            l2 = r * (0.62 + 0.18 * ((i + k) % 3) / 2)
            p.caja("Body/cola", f"copo{k}_{i}", (cx - l2 / 2, cy - l2 / 2, cz - l2 / 2),
                   (cx + l2 / 2, cy + l2 / 2, cz + l2 / 2), pint,
                   rot=((i * 37 + k * 11) % 60 - 30, (i * 53 + k * 7) % 60 - 30, (i * 29 + k * 13) % 60 - 30), dens=D)


def construir():
    p = Personaje("moles", altura=21, cabeza=CABEZA_ALTO, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    C, T, L = p.cuello, p.tope, p.lh                           # 11, 21, 5
    assert C == CUELLO

    p.caja("Head/cabeza", "cabeza", (-5, C, -5), (5, T, 5), cabeza, dens=D_CARA, luz=False)   # sin sombra en la cara
    pestanas(p, C)
    pelo(p, C, T)
    orejas(p, T)

    p.caja("Body/cuerpo", "torso", (-2.8, L, -1.6), (2.8, C, 1.6), piel, dens=D, luz=False)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 2.8, s * 4.8))
        p.caja(f"{hueso}/brazo", "brazo", (x1, L - 1.9, -1.0), (x2, C, 1.0), piel, dens=D, luz=False)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.1, s * 2.5))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 1.2, -1.2), (x2, L, 1.2), piel, dens=D, luz=False)
        b1, b2 = sorted((s * 0.0, s * 2.8))
        p.caja(f"{hueso}/pata", "pata", (b1, 0.0, -1.8), (b2, 1.4, 1.4), pata, dens=D, luz=False)
    ropa(p, C, L)
    cola(p)
    return p
