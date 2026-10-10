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


def liso(col):
    c = hex_(col)
    return lambda t: c


# el pelo: por ahora UNA sola pieza, como un bob con las puntas hacia adentro: cubre la nuca y los costados de la
# cabeza (la cara queda libre), se abre hacia afuera conforme baja, hace punta y abajo el borde se mete por debajo
# de la cabeza. De lado se ve el "<" atras; de atras y de frente, una campana con las esquinas en punta.
# Cada nivel es una U (abierta hacia la cabeza): (y, medio ancho, z de atras, z de las puntas de la U)
NIVELES_PELO = ((21.4, 5.3, 5.5, -4.5), (19.5, 5.8, 6.1, -4.5), (16.0, 6.6, 6.9, -4.5), (12.8, 7.6, 7.8, -4.5),
                (11.5, 6.6, 6.4, -4.4), (10.5, 5.4, 5.0, -4.0))
GROSOR_PELO = 0.7
ESQUINA_PELO = 1.5


def _azar(k):
    import math
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _suave(niveles, pasos=3):
    """Mas niveles entre los niveles dados (curva suave que pasa por ellos): mas poligonos, la forma redonda."""
    out = []
    n = len(niveles)
    for i in range(n - 1):
        p0, p1, p2, p3 = niveles[max(0, i - 1)], niveles[i], niveles[i + 1], niveles[min(n - 1, i + 2)]
        for k in range(pasos):
            t = k / pasos
            out.append(tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                    + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(niveles[-1])
    return out


def _u(y, w, zb, zf, g=0.0):
    """Una U de esquinas redondas atras: de la punta izquierda, por atras, a la punta derecha (adentro si g > 0), con
    los lados y la espalda partidos en tramos (mas poligonos)."""
    import math
    w, zb, r = w - g, zb - g, max(0.2, ESQUINA_PELO - g)
    pts = [(-w, y, zf + (zb - r - zf) * i / 4) for i in range(4)]
    pts += [(-w + r - r * math.cos(math.radians(90 * k / 6)), y, zb - r + r * math.sin(math.radians(90 * k / 6)))
            for k in range(6)]
    pts += [(-w + r + (2 * w - 2 * r) * i / 4, y, zb) for i in range(4)]
    pts += [(w - r + r * math.sin(math.radians(90 * k / 6)), y, zb - r + r * math.cos(math.radians(90 * k / 6)))
            for k in range(6)]
    pts += [(w, y, zb - r - (zb - r - zf) * i / 4) for i in range(5)]
    return pts


def _anillo_redondo(y, m, r=1.5, n=6):
    """Rectangulo de esquinas redondas cerrado (para la tapa de arriba), antihorario visto desde arriba: de +X hacia
    -Z (adelante), como geo.anillo."""
    import math
    pts = []
    c = m - r
    for cx, cz, a0 in ((c, -c, 0), (-c, -c, 90), (-c, c, 180), (c, c, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), y, cz - r * math.sin(a)))
    return pts


def mechon_malla(ancho, largo, grueso, k):
    """Un mechon con volumen: ancho arriba, se angosta y termina en una punta corrida a un lado (fija por k)."""
    from .. import malla as geo
    w = ancho / 2
    corre = (_azar(k + 7) - 0.5) * 0.5 * ancho
    perfil = [(-w, 0.0), (w, 0.0), (w * 0.92, -0.55 * largo), (corre + 0.12 * ancho, -largo),
              (corre - 0.12 * ancho, -largo + 0.15), (-w * 0.9, -0.6 * largo)]
    return geo.extruir(perfil, -grueso / 2, grueso / 2)


# el frente: el fleco y los mechones que enmarcan la cara, en tres capas que se distinguen (de atras hacia adelante,
# cada una mas corta, mas adelante y mas clara). (z, tono, cuanto mas corta, grueso)
CAPAS_FRENTE = ((-5.15, "s", 0.0, 0.55), (-5.55, "b", 0.8, 0.6), (-5.95, "l", 1.6, 0.55))


def frente(p, C, T):
    """El fleco y los mechones de la cara en tres capas; cada mechon de su ancho, largo y giro (al azar, fijo)."""
    from .. import malla as geo
    k = 0
    for capa, (z, tono, corto, grueso) in enumerate(CAPAS_FRENTE):
        x = -5.4 + 0.4 * capa
        while x < 5.4:
            ancho = 1.1 + 0.9 * _azar(k)
            cx = min(x + ancho / 2, 5.4 - ancho / 2)
            borde = abs(cx) > 3.3                              # a los lados de la cara: mechones largos
            if borde:
                largo = 7.5 + 2.5 * _azar(k + 40) - corto * 1.6
            else:
                largo = 3.2 + 1.3 * _azar(k + 40) - corto      # el fleco: llega arriba de las cejas
            m = mechon_malla(ancho, max(1.2, largo), grueso, k)
            giro = (6 * (_azar(k + 80) - 0.5) + (4 if borde else 0) * (1 if cx > 0 else -1))
            m = geo.girar(m, (-4 - 3 * capa, 0, giro))
            m = geo.mover(m, (cx, T + 0.3, z))
            p.malla("Head/pelo", f"frente{capa}_{k}", m, liso(PELO[tono]), dens=D)
            x += ancho * (0.8 + 0.25 * _azar(k + 120))
            k += 1


def pelo(p, C, T):
    """El pelo: la campana (bob con las puntas hacia adentro, ver NIVELES_PELO) con mas poligonos, la tapa de arriba
    redonda y el frente en capas."""
    from .. import malla as geo
    anillos = []
    for y, w, zb, zf in _suave(NIVELES_PELO):
        anillos.append(_u(y, w, zb, zf) + _u(y, w, zb, zf, GROSOR_PELO)[::-1])
    p.malla("Head/pelo", "campana", geo.loft_puntos(anillos[::-1]), liso(PELO["b"]), dens=D)
    tapa = [_anillo_redondo(y, m, r) for y, m, r in ((T - 0.4, 5.55, 0.9), (T + 0.5, 5.45, 1.0), (T + 1.0, 4.8, 1.6),
                                                     (T + 1.3, 3.6, 1.6))]
    p.malla("Head/pelo", "tapa", geo.loft_puntos(tapa), liso(PELO["l"]), dens=D)
    frente(p, C, T)


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
