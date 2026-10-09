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


PELO_TEX = voxel(PELO, claro=0.18)


def oreja_adentro(t):
    return hex_(ROSA_OREJA)


def pata(t):
    """Pata blanca con tres almohadillas rosas adelante."""
    if t.cara == "north" and t.y < 1.1:
        u = (t.x - t.f[0]) / max(1e-6, t.t[0] - t.f[0])
        if 0.3 < t.y < 0.9 and any(abs(u - c) < 0.11 for c in (0.22, 0.5, 0.78)):
            return hex_(RUBOR_FUERTE)
    return piel(t)


def pelo(p, C, T):
    g = "Head/pelo"
    # casco redondeado: tres escalones que se angostan hacia arriba
    for k, (ancho, y0, y1) in enumerate(((6.1, T - 2.6, T + 0.6), (5.5, T + 0.6, T + 1.4), (4.4, T + 1.4, T + 1.9))):
        p.caja(g, f"casco{k}", (-ancho, y0, -ancho + 0.1), (ancho, y1, ancho), PELO_TEX, dens=D)
    # volumen a los costados: bloques que bajan en escalon
    for s in (1, -1):
        for k, (x0, x1, y0, z0, z1) in enumerate(((5.0, 6.4, C + 1.0, -4.4, 4.8), (5.8, 6.9, C + 3.2, -3.6, 3.6))):
            a, b = sorted((s * x0, s * x1))
            p.caja(g, f"costado{s}_{k}", (a, y0, z0), (b, T - 1.0, z1), PELO_TEX, dens=D)
        for k, (z0, abajo) in enumerate(((-4.4, C - 0.6), (-1.6, C - 1.4), (1.4, C - 0.8))):   # puntas del costado
            a, b = sorted((s * 5.0, s * 6.3))
            p.caja(g, f"punta{s}_{k}", (a, abajo, z0), (b, C + 1.0, z0 + 2.6), PELO_TEX, dens=D)
    # melena de atras: un bloque ancho que llega a la nuca con puntas, y dos mechones largos en las esquinas
    for k, abajo in enumerate((C + 0.6, C + 1.2, C + 0.3, C + 1.0, C + 0.5, C + 1.3, C + 0.4, C + 1.1, C + 0.7)):
        x = -6.4 + k * (12.8 / 9)
        p.caja(g, f"atras{k}", (x, abajo, 3.8), (x + 12.8 / 9, T - 0.6, 6.7), PELO_TEX, dens=D)
    for s in (1, -1):
        a, b = sorted((s * 4.6, s * 6.5))
        p.caja(g, f"cola_pelo{s}", (a, C - 3.4, 4.0), (b, C + 1.5, 6.5), PELO_TEX, dens=D)
    # flequillo: mechones gruesos de distinto largo; un par baja entre los ojos
    ancho = 11.2 / 8
    for k, abajo in enumerate((C + 3.6, C + 5.6, C + 6.1, C + 4.9, C + 5.0, C + 6.2, C + 5.7, C + 3.6)):
        x = -5.6 + k * ancho
        p.caja(g, f"fleco{k}", (x, abajo, -6.7), (x + ancho, T + 0.2, -5.0), PELO_TEX, dens=D)
    p.caja(g, "fleco_esponja", (-6.0, T - 1.6, -7.2), (6.0, T + 0.7, -5.0), PELO_TEX, dens=D)   # el copete esponjado
    # mechones largos adelante que enmarcan la cara y bajan hasta el pecho
    for s in (1, -1):
        for k, (x0, x1, abajo) in enumerate(((5.0, 6.5, C - 3.6), (4.2, 5.3, C - 1.2))):
            a, b = sorted((s * x0, s * x1))
            p.caja(g, f"mechon{s}_{k}", (a, abajo, -6.7), (b, T - 1.5, -3.8), PELO_TEX, dens=D)


def mechones_2d(t):
    """Panel de pelo en 2D: rubio con el borde de abajo cortado en mechones de distinto largo (lo demas transparente)."""
    u = t.x if t.cara in ("north", "south") else t.z
    k = int((u + 50) // 1.1)
    if t.y < t.f[1] + (0.0, 0.9, 0.35, 1.3, 0.6)[k % 5]:
        return TRANSPARENTE
    return PELO_TEX(t)


def paneles(p, C, T):
    """Volumen pensado con paneles 2D: dos capas atras que se abren un poco hacia afuera y una a cada costado, como
    mechones que se separan de la melena."""
    g = "Head/pelo"
    for k, (x, y0, y1, z, giro) in enumerate(((5.9, C - 1.2, T - 1.6, 6.2, -14), (4.3, C - 2.3, T - 3.2, 6.45, -24))):
        p.plano(g, f"capa_atras{k}", (-x, y0, z), (x, y1, z), mechones_2d, rot=(giro, 0, 0), piv=(0, y1, z), dens=D)
    for s in (1, -1):
        x = s * 6.5
        p.plano(g, f"capa_costado{s}", (x, C - 0.9, -3.2), (x, T - 1.6, 4.4), mechones_2d, rot=(0, 0, 6 * s),
                piv=(x, T - 1.6, 0.6), dens=D)


PELUSA = {"s": "#F3E9DD", "b": "#FFF8EF", "l": "#FFFFFF"}


def orejas(p, T):
    """Orejas grandes, redondeadas y esponjosas en las esquinas de arriba, abiertas hacia afuera: escalones crema,
    el adentro rosa con pelusa blanca y copos de pelo en el borde."""
    g = "Head/orejas"
    for s in (1, -1):
        cx = s * 4.1
        piv = (cx, T + 1.0, 0.6)
        giro = dict(rot=(-8, 0, -32 * s), piv=piv)
        y = T + 0.6
        for k, (ancho, alto) in enumerate(((4.8, 2.0), (4.4, 1.6), (3.6, 1.4), (2.4, 1.0))):
            p.caja(g, f"oreja{s}_{k}", (cx - ancho / 2, y, -0.2), (cx + ancho / 2, y + alto, 1.4), voxel(OREJA, claro=0.15),
                   dens=D, **giro)
            y += alto
        p.caja(g, f"adentro{s}", (cx - 1.5, T + 1.4, -0.35), (cx + 1.5, T + 5.0, -0.2), oreja_adentro, dens=D, **giro)
        # pelusa blanca que sale de adentro, abajo
        for k, (dx, dy, l) in enumerate(((-0.9, 1.2, 1.3), (0.3, 1.0, 1.5), (1.1, 1.6, 1.1), (-0.3, 2.2, 1.0))):
            x0, y0 = cx + dx, T + dy
            p.caja(g, f"pelusa{s}_{k}", (x0 - l / 2, y0 - l / 2, -0.9), (x0 + l / 2, y0 + l / 2, -0.15),
                   voxel(PELUSA, claro=0.2), rot=(0, 0, (k * 27) % 40 - 20 - 32 * s), piv=(x0, y0, -0.5), dens=D)
        # copos de pelo en el borde de afuera: lo vuelven redondo y esponjoso
        for k, (dx, dy, l) in enumerate(((2.4, 1.8, 1.2), (2.2, 3.4, 1.1), (1.5, 4.8, 1.0), (0.2, 5.9, 1.1),
                                         (-1.4, 4.9, 1.0), (-2.3, 3.3, 1.1), (-2.5, 1.7, 1.2))):
            x0, y0 = cx + dx, T + dy
            p.caja(g, f"copo{s}_{k}", (x0 - l / 2, y0 - l / 2, -0.05), (x0 + l / 2, y0 + l / 2, 1.25),
                   voxel(OREJA, claro=0.2), rot=(0, 0, (k * 31) % 50 - 25), piv=(x0, y0, 0.6), dens=D)
            # los copos giran con la oreja: se arman en su lugar ya inclinado
        for c in p.m.cubos[-7:]:
            _inclinar(c, piv, -32 * s)


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


def construir():
    p = Personaje("moles", altura=21, cabeza=CABEZA_ALTO, torso=(5.6, 6, 3.2), brazo=(2.0, 2.0), pierna=(2.4, 2.4))
    C, T, L = p.cuello, p.tope, p.lh                           # 11, 21, 5
    assert C == CUELLO

    p.caja("Head/cabeza", "cabeza", (-5, C, -5), (5, T, 5), cabeza, dens=D_CARA, luz=False)   # sin sombra en la cara
    pestanas(p, C)
    pelo(p, C, T)
    paneles(p, C, T)
    orejas(p, T)

    p.caja("Body/cuerpo", "torso", (-2.8, L, -1.6), (2.8, C, 1.6), piel, dens=D, luz=False)
    for s in (1, -1):
        hueso = "RightArm" if s > 0 else "LeftArm"
        x1, x2 = sorted((s * 2.8, s * 4.8))
        p.caja(f"{hueso}/brazo", "brazo", (x1, L - 0.8, -1.0), (x2, C, 1.0), piel, dens=D, luz=False)
        hueso = "RightLeg" if s > 0 else "LeftLeg"
        x1, x2 = sorted((s * 0.1, s * 2.5))
        p.caja(f"{hueso}/pierna", "pierna", (x1, 1.2, -1.2), (x2, L, 1.2), piel, dens=D, luz=False)
        b1, b2 = sorted((s * 0.0, s * 2.8))
        p.caja(f"{hueso}/pata", "pata", (b1, 0.0, -1.8), (b2, 1.4, 1.4), pata, dens=D, luz=False)
    return p
