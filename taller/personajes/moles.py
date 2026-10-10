"""
Moles, la hermana de Pibble: una sause (semidiosa) kitsune, nueva, de la misma estrella que el. Lo sigue porque
tambien se alimenta de diversion, pero no son unidos: es rara su relacion. Sarcastica, graciosa y muy alegre.
Hecha a mano con el kit segun referencias/personajes/moles.png. Chibi de la altura de Pibble, no humana.

Por ahora solo el cuerpo (sin ropa ni accesorios), con las proporciones del boceto: cabeza enorme y ancha, cuerpo
chiquito y piernas cortas con patas.
  CARA de la referencia: ojos grandes y separados, pestana negra gruesa con la punta hacia afuera, iris ambar con
    brillo, cejitas picaras, naricita rosa, boca de gatito abierta con la lengua y mucho rubor
  PELO rubio claro LOW-POLY: un bob de una sola pieza con pliegues (mechones gruesos en tonos planos por cara), que
    adelante se dobla hasta la cara; flequillo en tres capas de mechones de distinto largo y mechones largos adelante
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


# el pelo, LOW-POLY (como pelo de malla de Blockbench, no un casco liso): pocos anillos y pocos puntos, con PLIEGUES
# (aristas y valles que bajan como mechones gruesos) y cada cara pintada de un tono plano segun hacia donde mira, asi
# las caras se leen como poligonos. Es UNA pieza, como un bob con las puntas hacia adentro: cubre la nuca y los
# costados (la cara queda libre), se abre hacia afuera conforme baja, hace punta y abajo el borde se mete por debajo de
# la cabeza. De lado se ve el "<" atras; de atras y de frente, una campana con las esquinas en punta. Por dentro va
# pegado al costado de la cabeza (sin hueco) y la orilla de enfrente queda tapada por los mechones de la cara.
# Cada nivel es una U (abierta hacia la cara): (y, medio ancho, z de atras, z de las puntas de la U)
NIVELES_PELO = ((21.4, 5.3, 5.5, -5.1), (19.5, 5.8, 6.1, -5.1), (16.0, 6.6, 6.9, -5.1), (12.8, 7.6, 7.8, -5.0),
                (11.5, 6.6, 6.4, -5.1), (10.5, 5.4, 5.0, -4.9))
GROSOR_PELO = 0.7
ESQUINA_PELO = 1.5
COSTADO = 5.03                          # por dentro, el pelo va pegado al costado de la cabeza
TONOS_PELO = ((0.34, "#D6A64F"), (0.5, PELO["s"]), (0.66, PELO["b"]), (9.0, PELO["l"]))   # (hasta, tono)


def _azar(k):
    import math
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def _suave(niveles, pasos=3):
    """Mas niveles entre los niveles dados (curva suave que pasa por ellos)."""
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


def faceta(sesgo=0.0, paleta=None):
    """Pintor del pelo low-poly: cada cara de un tono PLANO segun hacia donde mira (arriba claro, hacia abajo oscuro,
    y en cada pliegue una cara clara y la otra oscura) y un poquito distinta de la de junto, para que las caras se lean
    como poligonos. Todas las piezas del pelo usan el mismo, asi se ven como una sola cabellera (nada pegado aparte)."""
    import math

    def pintor(t):
        nx, ny, nz = t.n
        # las dos caras de cada pliegue miran un poco a un lado y al otro: con sin(4 * angulo) una sale clara y la
        # otra oscura, igual en los dos costados, atras y adelante (no depende de un solo foco)
        h = math.hypot(nx, nz)
        b = 0.5 + 0.32 * ny - 0.12 * nz + 0.17 * h * math.sin(4 * math.atan2(nz, nx))
        b += sesgo + 0.06 * (_azar(round(nx, 2) * 37.1 + round(ny, 2) * 11.7 + round(nz, 2) * 5.3) - 0.5)
        return next(hex_(c) for hasta, c in (paleta or TONOS_PELO) if b <= hasta)
    return pintor


def _u(y, w, zb, zf, r, x_punta=None):
    """La U del pelo en pocos tramos (low-poly): de la punta izquierda, por atras, a la punta derecha. Cada punto con
    su normal hacia afuera (nx, nz) para levantar los pliegues. Con x_punta, la orilla de enfrente se DOBLA: el brazo
    se curva hacia adentro y acaba pegado al costado de la cabeza (x_punta), asi el pelo queda cerrado adelante."""
    import math
    largo = zb - r - zf                                            # el brazo, de la esquina de atras a la punta
    if x_punta is not None and w - x_punta > 0.05:
        rx = w - x_punta
        rz = min(0.85 * rx, 0.6 * largo)
    else:
        x_punta, rx, rz = w, 0.0, 0.4 * largo
    mitad = [((w - r) * i / 3, zb, 0.0, 1.0) for i in range(3)]                       # media espalda
    for k in range(3):                                                                 # la esquina de atras
        a = math.radians(30 * k)
        mitad.append((w - r + r * math.sin(a), zb - r + r * math.cos(a), math.sin(a), math.cos(a)))
    mitad += [(w, zb - r - (largo - rz) * i / 3, 1.0, 0.0) for i in range(3)]         # el brazo
    for k in range(4):                                                                 # el doblez de enfrente
        a = math.radians(30 * k)
        if rx:
            n = (math.cos(a) / rx, -math.sin(a) / rz)
            n = (n[0] / math.hypot(*n), n[1] / math.hypot(*n))
            mitad.append((x_punta + rx * math.cos(a), zf + rz - rz * math.sin(a)) + n)
        else:
            mitad.append((w, zf + rz * (1 - k / 3), 1.0, 0.0))
    lado = [((-x, y, z), (-nx, nz)) for x, z, nx, nz in mitad[1:]][::-1]
    return lado + [((x, y, z), (nx, nz)) for x, z, nx, nz in mitad]


def _pliegue(k, n, nivel, y):
    """Cuanto sale (o se mete) el punto k de la U: aristas y valles alternados que bajan como mechones gruesos, mas
    marcados abajo; las puntas de la U quedan lisas."""
    if k in (0, n - 1):
        return 0.0
    a = 0.25 + 0.4 * max(0.0, min(1.0, (21.4 - y) / 8.6))
    salto = (0.55 + 0.9 * _azar(k * 3.1 + 1)) if k % 2 else -0.25
    return a * salto * (0.9 + 0.2 * _azar(k * 7.3 + nivel * 1.9))


def _adentro(y, w):
    """Donde va el pelo por dentro: a la altura de la cabeza, pegado a su costado (el pelo es macizo hasta la cabeza,
    sin hueco); abajo de la cabeza, solo un poco mas adentro que por fuera."""
    return COSTADO if y >= CUELLO else w - GROSOR_PELO


def _u_pelo(nivel, y, w, zb, zf):
    """La U de afuera con sus pliegues, doblada adelante hasta el costado de la cabeza."""
    pts = _u(y, w, zb, zf, ESQUINA_PELO, x_punta=_adentro(y, w))
    out = []
    for k, ((x, yy, z), (nx, nz)) in enumerate(pts):
        d = _pliegue(k, len(pts), nivel, y)
        out.append((x + nx * d, yy, z + nz * d))
    return out


def campana(niveles):
    """La campana del pelo: por fuera la U con pliegues que adelante se dobla hasta la cabeza; por dentro pegada al
    costado de la cabeza, asi el pelo queda cerrado (no se ve el corte)."""
    from .. import malla as geo
    anillos = []
    for i, (y, w, zb, zf) in enumerate(niveles):
        g = GROSOR_PELO
        dentro = [p for p, _ in _u(y, _adentro(y, w), zb - g, zf + 0.05, max(0.3, ESQUINA_PELO - g))]
        anillos.append(_u_pelo(i, y, w, zb, zf) + dentro[::-1])
    return geo.loft_puntos(anillos[::-1])


def tapa(nivel_alto, T):
    """La tapa de arriba, parte de la misma cabellera: su primer anillo es la U de arriba de la campana (con los mismos
    pliegues) cerrada por enfrente sobre la frente; sube y se cierra en la coronilla, y los pliegues siguen hacia
    arriba juntandose."""
    from .. import malla as geo
    y0, w, zb, zf = nivel_alto
    base = _u_pelo(0, y0, w, zb, zf)
    base += [(w * f, T, zf - 0.15) for f in (0.6, 0.2, -0.2, -0.6)]          # cerrado por enfrente, sobre la frente
    cz = 0.15
    anillos = []
    for y, s in ((y0, 1.0), (T + 0.95, 0.95), (T + 1.35, 0.78), (T + 1.55, 0.5)):
        anillos.append([(x * s, y + (py - y0) * s, cz + (z - cz) * s) for x, py, z in base])
    cuerpo = geo.loft_puntos(anillos, tapa_abajo=False, tapa_arriba=False)
    punta = geo.piramide(anillos[-1], (0.0, T + 1.65, cz), tapa=False)
    return geo.unir(cuerpo, punta)


def mechon_malla(ancho, largo, grueso, k):
    """Un mechon low-poly: corte de rombo (una arista al frente, como un pliegue de pelo), ancho arriba, se angosta en
    dos tramos y acaba en una punta corrida a un lado (fija por k)."""
    from .. import malla as geo
    w, g = ancho / 2, grueso / 2
    corre = (_azar(k + 7) - 0.5) * 0.5 * ancho
    cresta = (_azar(k + 13) - 0.5) * 0.5 * ancho                 # la arista no va justo al medio
    anillos = []
    for f, a in ((0.0, 1.0), (0.42, 0.88 + 0.12 * _azar(k + 21)), (0.76, 0.5)):        # de arriba hacia abajo
        cx, y, ww = corre * f, -largo * f, w * a
        anillos.append([(cx + ww, y, 0.0), (cx + cresta * a, y, -g * (0.6 + 0.4 * a)), (cx - ww, y, 0.0),
                        (cx + cresta * a * 0.5, y, g * 0.6)])
    cuerpo = geo.loft_puntos(anillos[::-1], tapa_abajo=False, tapa_arriba=True)
    abajo = anillos[-1]
    n = len(abajo)
    punta = (abajo + [(corre, -largo, 0.0)], [((i + 1) % n, i, n) for i in range(n)])
    return geo.unir(cuerpo, punta)


# el frente: el fleco y los mechones que enmarcan la cara, en tres capas que se distinguen (de atras hacia adelante,
# cada una mas corta, mas adelante y mas clara). (z, sesgo de tono, cuanto mas corta, grueso)
CAPAS_FRENTE = ((-5.15, -0.08, 0.0, 0.8), (-5.6, 0.0, 0.8, 0.85), (-6.05, 0.08, 1.6, 0.8))
# los mechones de los costados de la cara, sobre la orilla de enfrente de la campana, siguiendo su orilla de afuera
# (unos 15 grados): (x, y de la raiz, largo, ancho, giro hacia afuera)
PATILLAS = ((4.6, 21.0, 8.4, 1.4, 14.0), (5.05, 19.4, 7.0, 1.3, 15.0), (5.55, 17.4, 5.0, 1.2, 16.0))


def frente(p, C, T):
    """El fleco y los mechones de la cara en tres capas; cada mechon de su ancho, largo y giro (al azar, fijo). A los
    lados, las patillas tapan la orilla de enfrente de la campana."""
    from .. import malla as geo
    k = 0
    for capa, (z, sesgo, corto, grueso) in enumerate(CAPAS_FRENTE):
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
            p.malla("Head/pelo", f"frente{capa}_{k}", m, faceta(sesgo), dens=D)
            x += ancho * (0.8 + 0.25 * _azar(k + 120))
            k += 1
    for s in (1, -1):
        for i, (x, y, largo, ancho, giro) in enumerate(PATILLAS):
            m = mechon_malla(ancho, largo, 0.9, 200 + i * 2 + (s > 0))
            m = geo.girar(m, (-3, 0, s * giro))
            m = geo.mover(m, (s * x, y, -5.45 - 0.15 * i))
            p.malla("Head/pelo", f"patilla{s}_{i}", m, faceta(-0.02), dens=D)


def pelo(p, C, T):
    """El pelo low-poly: la campana con pliegues, la tapa de arriba que sigue la misma cabellera y el frente en
    capas."""
    niveles = _suave(NIVELES_PELO, pasos=2)
    p.malla("Head/pelo", "campana", campana(niveles), faceta(), dens=D)
    p.malla("Head/pelo", "tapa", tapa(niveles[0], T), faceta(), dens=D)
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


# ---------------------------------------------------------------- la sudadera
# sudadera de cierre (como las de referencia): negra, holgada y cuadrada, con resorte abajo, hombros caidos,
# mangas abombadas que se juntan en un puno de resorte, el cierre al frente, la bolsa canguro partida por el cierre y
# la capucha caida en la espalda; la orilla de la capucha baja por el pecho en V hasta el cierre, bordada en zigzag
# cafe, y adentro de la V se ve la piel. Todo low-poly como el pelo: caras planas con su tono segun hacia donde miran.
NEGRO = ((0.34, "#141317"), (0.5, "#1D1C21"), (0.66, "#28272D"), (9.0, "#35343B"))
BORDADO, CIERRE, CIERRE_CLARO = "#C29A62", "#6B707C", "#A3A8B3"
ROJO, CREMA_DIJE = "#C8343A", "#FBF1DE"
# el cuerpo de la sudadera, de abajo hacia arriba: (y, medio ancho, medio hondo, esquina)
SUDADERA = ((5.05, 3.0, 1.85, 0.7), (5.6, 3.35, 2.1, 0.9), (7.2, 3.4, 2.15, 0.9), (9.2, 3.3, 2.05, 0.9),
            (10.4, 3.15, 1.95, 0.9), (11.05, 3.0, 1.8, 0.45))
RESORTE = (4.3, 5.2, 2.95, 1.8, 0.7)                     # el resorte de abajo: de y a y, medio ancho, medio hondo
MANGA_X = 3.8                                            # el centro del brazo
MANGA = ((4.95, 1.5), (5.7, 1.72), (6.8, 1.8), (8.2, 1.75), (9.5, 1.65), (10.5, 1.55), (11.1, 1.48))  # (y, radio)
PUNO = (4.1, 5.1, 1.47)
CAPUCHA = ((7.2, 0.9, 0.3, 2.2), (7.9, 2.0, 0.55, 2.4), (9.0, 2.6, 0.72, 2.55), (10.2, 2.8, 0.75, 2.5),
           (11.0, 2.6, 0.6, 2.3))                        # caida en la espalda: (y, medio ancho, medio hondo, z)
ORILLA = ((0.1, 9.55), (2.15, 10.85), 0.28)              # la orilla de la capucha en el pecho: de, a, medio ancho


def _rect(y, mx, mz, r, n=2, cz=0.0):
    """Rectangulo de esquinas redondas en pocos tramos (low-poly), antihorario visto desde arriba (de +X hacia -Z)."""
    import math
    r = min(r, mx - 0.05, mz - 0.05)
    pts = []
    for sx, sz, a0 in ((1, -1, 0), (-1, -1, 90), (-1, 1, 180), (1, 1, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((sx * (mx - r) + r * math.cos(a), y, cz + sz * (mz - r) - r * math.sin(a)))
    return pts


def resorte(paleta):
    """Resorte: costillas verticales (de lado a lado sigue la orilla de cada cara)."""
    import math
    claro, oscuro = hex_(paleta[1][1]), hex_(paleta[0][1])

    def pintor(t):
        nx, ny, nz = t.n
        if abs(ny) > 0.7:
            return oscuro
        if abs(nz) > 0.7 or abs(nx) > 0.7:
            u = t.x if abs(nz) > 0.7 else t.z
        else:                                   # las caras de la orilla redonda: una costilla por cara
            return claro if round(math.degrees(math.atan2(nz, nx)) / 22.5) % 2 else oscuro
        return claro if (u * 3.5) % 1.0 < 0.5 else oscuro
    return pintor


def frente_z(y):
    """Que tan adelante va el frente de la sudadera a esa altura (para pegarle el cierre)."""
    pts = [(RESORTE[0], RESORTE[3]), (RESORTE[1] - 0.05, RESORTE[3])] + [(yy, mz) for yy, _, mz, _ in SUDADERA[1:]]
    for (y0, m0), (y1, m1) in zip(pts, pts[1:]):
        if y <= y1:
            return -(m0 + (m1 - m0) * max(0.0, (y - y0)) / (y1 - y0))
    return -pts[-1][1]


def tela_v(pintor):
    """La tela del cuerpo con la V del cuello abierta: arriba de la orilla de la capucha (de enfrente) se ve la piel."""
    (ax, ay), (bx, by), _ = ORILLA
    pendiente = (by - ay) / (bx - ax)

    def pintar(t):
        if t.n[2] < -0.3 and t.y > ay + (abs(t.x) - ax) * pendiente:
            return hex_(PIEL)
        return pintor(t)
    return pintar


def cierre(t):
    """Los dientes del cierre: rayitas alternadas."""
    return hex_(CIERRE_CLARO if (t.y * 6) % 1.0 < 0.45 else CIERRE)


def orilla(t):
    """La orilla de la capucha: azul con el bordado en zigzag cafe a lo largo (en las caras de enfrente)."""
    import math
    (ax, ay), (bx, by), w = ORILLA
    if t.n[2] > -0.5:
        return hex_(NEGRO[0][1])
    lx, ly = bx - ax, by - ay
    largo = math.hypot(lx, ly)
    dx, dy = lx / largo, ly / largo
    px, py = abs(t.x) - ax, t.y - ay
    s, c = px * dx + py * dy, -px * dy + py * dx                     # a lo largo y de lado a lado de la orilla
    zig = abs(((s / 0.38) % 1.0) - 0.5) * 2                           # 0..1..0
    if abs(c - (-0.15 + 0.3 * zig)) < 0.07:
        return hex_(BORDADO)
    return hex_(NEGRO[1][1])


def calaverita(t):
    u = (t.x - t.f[0]) / max(1e-6, t.t[0] - t.f[0])
    v = (t.y - t.f[1]) / max(1e-6, t.t[1] - t.f[1])
    if t.cara == "north" and 0.6 < v < 0.83 and any(abs(u - c) < 0.13 for c in (0.27, 0.73)):
        return hex_(PESTANA)
    return hex_(CREMA_DIJE)


def ropa(p, C, L):
    """La sudadera de cierre, en sus propios grupos (aparte del cuerpo, para prenderla y apagarla en Figura)."""
    from .. import malla as geo
    g = "Body/ropa"
    tela = faceta(paleta=NEGRO)
    y0, y1, mx, mz, r = RESORTE
    p.malla(g, "resorte", geo.loft_puntos([_rect(y, mx, mz, r) for y in (y0, y1)]), resorte(NEGRO), dens=D)
    p.malla(g, "cuerpo", geo.loft_puntos([_rect(y, mx, mz, r) for y, mx, mz, r in SUDADERA]), tela_v(tela), dens=D)
    # el cierre: una tira que sigue el frente, del resorte hasta donde se juntan las orillas de la capucha
    ys = (RESORTE[0], RESORTE[1] - 0.05, 5.6, 7.2, 9.2, ORILLA[0][1])
    perfil = [(frente_z(y) - 0.08, y) for y in ys] + [(frente_z(y) + 0.12, y) for y in ys[::-1]]
    p.malla(g, "cierre", geo.extruir_x(perfil, -0.13, 0.13), cierre, dens=8)
    p.caja(g, "jalador", (-0.16, 8.7, -2.22), (0.16, 9.45, -2.12), color(CIERRE_CLARO), dens=8)
    # la bolsa canguro, partida por el cierre: cada mitad con su abertura en diagonal
    for s in (1, -1):
        perfil = [(0.22, 5.55), (2.55, 5.55), (2.55, 6.1), (1.55, 7.55), (0.22, 7.55)]
        m = geo.extruir(perfil, -2.3, -2.05)
        p.malla(g, f"bolsa{s}", m if s > 0 else geo.espejo_x(m), faceta(-0.1, NEGRO), dens=D)
    # la orilla de la capucha: baja por el pecho en V hasta el cierre, con el bordado
    (ax, ay), (bx, by), w = ORILLA
    import math
    largo = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / largo * w, (bx - ax) / largo * w
    perfil = [(ax - nx, ay - ny), (bx - nx, by - ny), (bx + nx, by + ny), (ax + nx, ay + ny)]
    for s in (1, -1):
        m = geo.extruir(perfil, -2.3, -1.7)
        p.malla(g, f"orilla{s}", m if s > 0 else geo.espejo_x(m), orilla, dens=8)
    # la capucha caida en la espalda (arriba queda debajo del pelo)
    p.malla(g, "capucha", geo.loft_puntos([_rect(y, mx, mz, 0.7, n=3, cz=cz) for y, mx, mz, cz in CAPUCHA]), tela, dens=D)
    # dije de calaverita colgado de una tira roja, a su izquierda, del resorte
    p.caja(g, "tira", (-2.15, 3.6, -1.97), (-1.9, 4.9, -1.82), color(ROJO), dens=D)
    p.caja(g, "calaverita", (-2.65, 2.3, -2.2), (-1.4, 3.75, -1.8), calaverita, dens=D)
    # las mangas: hombro caido, abombadas, y el puno de resorte apretado contra la mano
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        manga = geo.loft_puntos([geo.anillo(s * MANGA_X, y, 0.0, r, r, 16) for y, r in MANGA])
        p.malla(f"{hueso}/ropa", "manga", manga, tela, dens=D)
        ya, yb, r = PUNO
        puno = geo.loft_puntos([geo.anillo(s * MANGA_X, y, 0.0, r, r, 16) for y in (ya, yb)])
        p.malla(f"{hueso}/ropa", "puno", puno, resorte(NEGRO), dens=D)


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
