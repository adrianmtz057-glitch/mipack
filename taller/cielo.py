"""
El cielo de Velkia (lo dibuja el mod: cliente/CieloVelkia.java). Aqui se generan sus texturas, en pixeles como los
modelos (un texel del cielo mide casi lo que uno del sol de Minecraft):
  - cielo_dia.png: el dia de desierto (azul hondo arriba, polvo calido y arena en el horizonte, cirros altos).
  - cielo_noche.png: el fondo de la noche (azul casi negro, el horizonte un poco mas claro).
  - estrellas.png: estrellas y la via lactea, sobre negro (se suma encima y gira con el cielo, como las del juego).
  - sol.png: el sol del desierto con su halo.
Cada cielo es un cubo: un atlas de 3 x 2 caras (arriba, norte, este / abajo, sur, oeste). El pixel (s, t) de una
cara (s de izquierda a derecha y t de arriba a abajo, de -1 a 1) es la direccion centro + s * derecha - t * arriba;
el mod pone las esquinas igual (CARAS tiene que coincidir con CieloVelkia.CARAS).
Uso: python -m taller.cielo
"""

import math
import os

import numpy as np
from PIL import Image

RAIZ = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources", "assets", "mipack", "textures",
                    "environment")

# nombre: (columna, fila, centro, derecha, arriba de la imagen)
CARAS = {
    "arriba": (0, 0, (0, 1, 0), (-1, 0, 0), (0, 0, -1)),
    "norte": (1, 0, (0, 0, -1), (1, 0, 0), (0, 1, 0)),
    "este": (2, 0, (1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "abajo": (0, 1, (0, -1, 0), (-1, 0, 0), (0, 0, 1)),
    "sur": (1, 1, (0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    "oeste": (2, 1, (-1, 0, 0), (0, 0, -1), (0, 1, 0)),
}


def direcciones(lado):
    """{cara: (lado, lado, 3) direcciones unitarias de cada pixel}."""
    c = (np.arange(lado) + 0.5) / lado * 2 - 1
    s, t = np.meshgrid(c, c)                      # s: columnas, t: filas
    out = {}
    for nombre, (_c, _f, centro, der, arr) in CARAS.items():
        d = (np.array(centro)[None, None, :] + s[..., None] * np.array(der)[None, None, :]
             - t[..., None] * np.array(arr)[None, None, :])
        out[nombre] = d / np.linalg.norm(d, axis=-1, keepdims=True)
    return out


def armar_atlas(caras, lado):
    """Junta las caras (lado, lado, 4) floats 0..1 en el atlas de 3 x 2."""
    atlas = np.zeros((lado * 2, lado * 3, 4))
    for nombre, img in caras.items():
        col, fila = CARAS[nombre][:2]
        atlas[fila * lado:(fila + 1) * lado, col * lado:(col + 1) * lado] = img
    return atlas


def muestrear(atlas, d):
    """El color del atlas en las direcciones d (como lo dibuja el mod, sin suavizar): para la vista previa."""
    lado = atlas.shape[0] // 2
    out = np.zeros(d.shape[:-1] + (atlas.shape[2],))
    ad = np.abs(d)
    for nombre, (col, fila, centro, der, arr) in CARAS.items():
        centro, der, arr = np.array(centro), np.array(der), np.array(arr)
        eje = int(np.argmax(np.abs(centro)))
        m = (np.argmax(ad, axis=-1) == eje) & (np.sign(d[..., eje]) == np.sign(centro[eje]))
        if not m.any():
            continue
        q = d[m] / np.abs(d[m][:, eje:eje + 1])
        s, t = q @ der, -(q @ arr)
        i = np.clip(((s + 1) / 2 * lado).astype(int), 0, lado - 1)
        j = np.clip(((t + 1) / 2 * lado).astype(int), 0, lado - 1)
        out[m] = atlas[fila * lado + j, col * lado + i]
    return out


# ---------------------------------------------------------------- ruido en la esfera

def _hash(ix, iy, iz, semilla):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + semilla * 144665) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def ruido(p, semilla=0):
    """Ruido de valor 3D suave (0..1) en los puntos p (..., 3)."""
    f = np.floor(p).astype(np.int64)
    r = p - f
    u = r * r * (3 - 2 * r)
    total = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = ((u[..., 0] if dx else 1 - u[..., 0]) * (u[..., 1] if dy else 1 - u[..., 1])
                     * (u[..., 2] if dz else 1 - u[..., 2]))
                total = total + w * _hash(f[..., 0] + dx, f[..., 1] + dy, f[..., 2] + dz, semilla)
    return total


def fbm(p, octavas=4, semilla=0):
    total, amp, norma = 0.0, 1.0, 0.0
    for o in range(octavas):
        total = total + amp * ruido(p * (2 ** o), semilla + o * 17)
        norma += amp
        amp *= 0.5
    return total / norma


def _degradado(x, paradas):
    """Interpola colores por paradas [(x, (r, g, b))] (x creciente) con curva suave."""
    out = np.zeros(x.shape + (3,))
    xs = [p[0] for p in paradas]
    for i in range(len(paradas) - 1):
        (x0, c0), (x1, c1) = paradas[i], paradas[i + 1]
        m = (x >= x0) & (x <= x1) if i == 0 else (x > x0) & (x <= x1)
        u = np.clip((x[m] - x0) / (x1 - x0), 0, 1)
        u = u * u * (3 - 2 * u)
        out[m] = np.array(c0) + (np.array(c1) - np.array(c0)) * u[:, None]
    out[x < xs[0]] = paradas[0][1]
    out[x > xs[-1]] = paradas[-1][1]
    return out


def _grano(d, fuerza, semilla):
    """Un poquito de variacion por texel (como el grano de las texturas de los modelos)."""
    return 1 + (ruido(d * 260, semilla) - 0.5) * fuerza


# ---------------------------------------------------------------- los cielos

DIA = [(-1.0, (0.78, 0.64, 0.46)), (-0.03, (0.88, 0.74, 0.54)), (0.0, (0.96, 0.86, 0.66)), (0.035, (0.92, 0.86, 0.72)),
       (0.10, (0.74, 0.80, 0.84)), (0.25, (0.50, 0.68, 0.88)), (0.55, (0.32, 0.56, 0.84)), (1.0, (0.20, 0.42, 0.76))]

NOCHE = [(-1.0, (0.020, 0.020, 0.045)), (-0.10, (0.050, 0.048, 0.105)), (0.02, (0.078, 0.072, 0.155)),
         (0.20, (0.050, 0.055, 0.130)), (0.50, (0.028, 0.036, 0.098)), (1.0, (0.012, 0.018, 0.060))]


def cielo_dia(d):
    y = d[..., 1]
    col = _degradado(y, DIA)
    # polvo del desierto: manchas calidas cerca del horizonte
    cerca = np.exp(-np.maximum(y, 0) / 0.09) * (y > -0.15)
    polvo = fbm(d * np.array([3.0, 9.0, 3.0]), 4, 3)
    col = col + (np.array([0.10, 0.06, -0.02]) * ((polvo - 0.5) * 2)[..., None]) * cerca[..., None]
    # cirros: vetas blancas largas en un "techo" alto (se ven acostadas y se juntan hacia el horizonte)
    k = 1.0 / (np.maximum(y, 0.0) + 0.25)
    plano = np.stack([d[..., 0] * k * 0.8, np.zeros_like(y), d[..., 2] * k * 6.0], axis=-1)
    vetas = fbm(plano + 11.0, 5, 21)
    alto = np.clip((y - 0.12) / 0.25, 0, 1) * np.clip((0.95 - y) / 0.35, 0, 1)
    cirro = np.clip((vetas - 0.60) / 0.13, 0, 1) ** 1.6 * alto * 0.6
    col = col * (1 - cirro[..., None]) + np.array([0.97, 0.96, 0.93]) * cirro[..., None]
    return np.clip(col * _grano(d, 0.03, 5)[..., None], 0, 1)


def cielo_noche(d):
    y = d[..., 1]
    col = _degradado(y, NOCHE)
    brillo = fbm(d * 5.0 + 3.0, 3, 41)                       # el resplandor del aire, apenas
    cerca = np.exp(-np.abs(y) / 0.12)
    col = col + np.array([0.02, 0.012, 0.03]) * (brillo * cerca)[..., None]
    return np.clip(col * _grano(d, 0.04, 9)[..., None], 0, 1)


VIA = np.array([0.30, 0.62, 0.72]) / np.linalg.norm([0.30, 0.62, 0.72])     # la normal del plano de la via lactea
NUCLEO = np.array([0.55, -0.35, 0.76]) / np.linalg.norm([0.55, -0.35, 0.76])


def via_lactea(d):
    """La via lactea (0..~1) y su color: una banda con nubes de estrellas y lineas de polvo oscuro."""
    dist = d @ VIA
    banda = np.exp(-(dist / 0.26) ** 2)
    detalle = fbm(d * 5.0, 5, 61)
    polvo = fbm(d * 11.0 + 4.0, 4, 77)
    nucleo = np.clip(d @ NUCLEO, 0, 1) ** 3
    v = banda * (0.35 + 0.9 * detalle) * (1 - 0.55 * np.clip((polvo - 0.54) / 0.10, 0, 1)) * (0.55 + 0.9 * nucleo)
    color = np.array([0.55, 0.58, 0.80])[None, None, :] * (1 - nucleo[..., None]) + \
        np.array([0.95, 0.80, 0.62])[None, None, :] * nucleo[..., None]
    return v, color


def estrellas(lado, semilla=7):
    """Atlas (lado * 2, lado * 3, 4) con las estrellas y la via lactea sobre negro (rgb, alfa = 1)."""
    rng = np.random.default_rng(semilla)
    dirs = direcciones(lado)
    caras = {}
    for nombre, d in dirs.items():
        v, color = via_lactea(d)
        neb = fbm(d * 3.0 + 9.0, 4, 91)
        nebulosa = np.clip((neb - 0.55) / 0.2, 0, 1) ** 2 * 0.05
        rgb = color * (v * 0.42)[..., None] + np.array([0.35, 0.18, 0.55]) * nebulosa[..., None]
        caras[nombre] = np.concatenate([rgb, np.ones(rgb.shape[:-1] + (1,))], axis=-1)
    atlas = armar_atlas(caras, lado)
    # las estrellas: mas en la via lactea, de brillo de ley de potencia y de colores de estrella
    colores = np.array([(1.0, 1.0, 1.0), (0.80, 0.88, 1.0), (1.0, 0.95, 0.80), (1.0, 0.82, 0.62), (0.72, 0.80, 1.0)])
    pesos = np.array([0.45, 0.22, 0.18, 0.08, 0.07])
    n = int(lado * lado * 0.06)
    hechas = 0
    while hechas < n:
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        if rng.random() > 0.35 + 0.65 * math.exp(-((d @ VIA) / 0.25) ** 2):
            continue
        hechas += 1
        b = rng.random() ** 5
        c = colores[rng.choice(len(colores), p=pesos)]
        _poner_estrella(atlas, lado, d, b, c)
    return atlas


def _pixel(lado, d):
    """(fila, columna) del atlas para la direccion d."""
    ad = np.abs(d)
    for nombre, (col, fila, centro, der, arr) in CARAS.items():
        centro = np.array(centro)
        eje = int(np.argmax(np.abs(centro)))
        if int(np.argmax(ad)) == eje and np.sign(d[eje]) == np.sign(centro[eje]):
            q = d / abs(d[eje])
            s, t = q @ np.array(der), -(q @ np.array(arr))
            i = min(lado - 1, int((s + 1) / 2 * lado))
            j = min(lado - 1, int((t + 1) / 2 * lado))
            return fila * lado + j, col * lado + i, fila * lado, col * lado
    raise ValueError(d)


def _poner_estrella(atlas, lado, d, b, c):
    j, i, j0, i0 = _pixel(lado, d)
    puntos = [(0, 0, 0.25 + 0.75 * b)]
    if b > 0.72:                                   # solo las muy brillantes en cruz
        puntos += [(dj, di, 0.12 + 0.30 * b) for dj, di in ((-1, 0), (1, 0), (0, -1), (0, 1))]
    for dj, di, k in puntos:
        jj, ii = j + dj, i + di
        if j0 <= jj < j0 + lado and i0 <= ii < i0 + lado:
            atlas[jj, ii, :3] = np.maximum(atlas[jj, ii, :3], np.array(c) * k)


def sol(lado=64):
    """El sol del desierto: disco blanco calido, anillo dorado y halo que se desvanece (con alfa)."""
    c = (np.arange(lado) + 0.5) / lado * 2 - 1
    x, y = np.meshgrid(c, c)
    r = np.sqrt(x * x + y * y)
    img = np.zeros((lado, lado, 4))
    disco = r < 0.30
    anillo = (r >= 0.30) & (r < 0.40)
    halo = np.clip(1 - (r - 0.30) / 0.70, 0, 1) ** 3.0
    img[..., :3] = np.array([1.0, 0.74, 0.40]) * halo[..., None]
    img[..., 3] = halo * 0.42
    img[anillo] = (1.0, 0.86, 0.55, 1.0)
    img[disco] = (1.0, 0.98, 0.88, 1.0)
    # rayos cortos en cruz (pixeles)
    rayo = ((np.abs(x) < 0.04) | (np.abs(y) < 0.04)) & (r < 0.50) & ~disco & ~anillo
    img[rayo] = np.maximum(img[rayo], (1.0, 0.90, 0.66, 0.55))
    return img


def _guardar(img, nombre):
    os.makedirs(RAIZ, exist_ok=True)
    Image.fromarray((np.clip(img, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(RAIZ, nombre))


def generar(lado_dia=192, lado_noche=48, lado_estrellas=320):
    dirs = direcciones(lado_dia)
    dia = armar_atlas({k: np.concatenate([cielo_dia(d), np.ones(d.shape[:-1] + (1,))], -1) for k, d in dirs.items()}, lado_dia)
    dirs = direcciones(lado_noche)
    noche = armar_atlas({k: np.concatenate([cielo_noche(d), np.ones(d.shape[:-1] + (1,))], -1) for k, d in dirs.items()}, lado_noche)
    est = estrellas(lado_estrellas)
    _guardar(dia, "cielo_dia.png")
    _guardar(noche, "cielo_noche.png")
    _guardar(est, "estrellas.png")
    _guardar(sol(), "sol.png")
    return dia, noche, est


def vista(atlas, ruta, yaw=0.0, pitch=10.0, fov=80.0, ancho=640, alto=360, extra=None):
    """Vista previa en perspectiva (mirando a yaw grados desde el norte hacia el este, pitch hacia arriba)."""
    f = math.tan(math.radians(fov) / 2)
    xs = (np.arange(ancho) + 0.5) / ancho * 2 - 1
    ys = (np.arange(alto) + 0.5) / alto * 2 - 1
    X, Y = np.meshgrid(xs * f * ancho / alto, -ys * f)
    a, p = math.radians(yaw), math.radians(pitch)
    adelante = np.array([math.sin(a) * math.cos(p), math.sin(p), -math.cos(a) * math.cos(p)])
    der = np.array([math.cos(a), 0, math.sin(a)])
    arriba = np.cross(der, adelante)
    d = adelante[None, None] + X[..., None] * der[None, None] + Y[..., None] * arriba[None, None]
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    img = muestrear(atlas, d)[..., :3]
    if extra is not None:
        img = extra(img, d)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(ruta)
    return ruta


if __name__ == "__main__":
    generar()
    print("listo en", os.path.normpath(RAIZ))
