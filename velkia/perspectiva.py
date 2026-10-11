"""Renders en perspectiva (trazado de rayos sobre el mapa de alturas) con niebla atmosférica.

Para validar el terreno como lo vería un jugador: cámara a 2 bloques sobre el suelo, o vistas
lejanas elevadas.  La textura de color es el relieve sombreado del mapa.  Antes de renderizar se
comprueba con una rejilla de rayos que la vista no esté tapada (cámara metida en el terreno o
mirando contra una ladera) y, si lo está, se busca otra posición cercana (encuadrar).
"""
import math
from dataclasses import dataclass

import numpy as np
from numba import njit, prange
from PIL import Image

from .layout import N, SEA

OJO = 2.0           # altura de la cámara de jugador sobre el suelo (bloques)
REJILLA = (15, 9)   # rayos de comprobación (columnas, filas)
UMBRAL = 250.0      # mediana mínima de la distancia al primer impacto en la franja central
CERCA = 60.0        # impacto "cercano" (bloques)
FRAC_CERCA = 0.6    # fracción máxima de rayos con impacto cercano
VISION = 0.8        # fracción del camino hasta el objetivo que debe estar libre de terreno
RADIO = 600.0       # radio de búsqueda de una posición alternativa


@njit(cache=True, inline='always')
def _bil(a, x, z):
    n0, n1 = a.shape[0], a.shape[1]
    if x < 0:
        x = 0.0
    if z < 0:
        z = 0.0
    if x > n1 - 1.001:
        x = n1 - 1.001
    if z > n0 - 1.001:
        z = n0 - 1.001
    i = int(z)
    j = int(x)
    fz = z - i
    fx = x - j
    return (a[i, j] * (1 - fx) * (1 - fz) + a[i, j + 1] * fx * (1 - fz) +
            a[i + 1, j] * (1 - fx) * fz + a[i + 1, j + 1] * fx * fz)


@njit(cache=True, inline='always')
def _rayo(yaw, pitch, f, u, v):
    """Dirección unitaria del rayo de pantalla (u, v).  Rumbo 0 = norte (-z), 90° = este (+x)."""
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    fwx, fwz = sy, -cy                 # adelante (horizontal)
    rtx, rtz = cy, sy                  # derecha
    # adelante y "arriba" inclinados por el pitch
    dxw = u * rtx - v * fwx * sp + f * fwx * cp
    ry = v * cp + f * sp
    dzw = u * rtz - v * fwz * sp + f * fwz * cp
    nrm = math.sqrt(dxw * dxw + ry * ry + dzw * dzw)
    return dxw / nrm, ry / nrm, dzw / nrm


@njit(cache=True)
def _march(Y, dx, ox, oy, oz, rx, ry, rz, sea, far):
    """Avanza un rayo sobre el relieve (el mar hace de suelo mínimo).

    Devuelve (t, código): 0 = cielo, 1 = terreno o agua, 2 = mar fuera del mapa.
    """
    n0, n1 = Y.shape[0], Y.shape[1]
    t = 1.0
    while t < far:
        x = ox + rx * t
        yv = oy + ry * t
        z = oz + rz * t
        gx = x / dx - 0.5
        gz = z / dx - 0.5
        if gx < 0 or gz < 0 or gx > n1 - 1 or gz > n0 - 1:
            return t, (2 if yv < sea else 0)
        hy = _bil(Y, gx, gz)
        if yv <= max(hy, sea):
            # refinar
            t0 = t - max(0.4, t * 0.004)
            for _ in range(8):
                tm = 0.5 * (t0 + t)
                hm = _bil(Y, (ox + rx * tm) / dx - 0.5, (oz + rz * tm) / dx - 0.5)
                if oy + ry * tm <= max(hm, sea):
                    t = tm
                else:
                    t0 = tm
            return t, 1
        t += max(0.4, t * 0.004)
    return far, 0


@njit(parallel=True, cache=True)
def _render(Y, tex, dx, cam, yaw, pitch, fov, W, H, fog, sea, far):
    img = np.zeros((H, W, 3), np.float32)
    f = 1.0 / math.tan(fov * 0.5)
    sky_top = np.array([110.0, 150.0, 210.0])
    sky_hor = np.array([205.0, 215.0, 228.0])
    for py in prange(H):
        for px in range(W):
            u = (2.0 * (px + 0.5) / W - 1.0)
            v = -(2.0 * (py + 0.5) / H - 1.0) * H / W
            rx, ry, rz = _rayo(yaw, pitch, f, u, v)
            t, cod = _march(Y, dx, cam[0], cam[1], cam[2], rx, ry, rz, sea, far)
            if cod == 0:
                g = min(1.0, max(0.0, ry * 3.0))
                for c in range(3):
                    img[py, px, c] = sky_hor[c] * (1 - g) + sky_top[c] * g
                continue
            if cod == 2:
                col0, col1, col2 = 45.0, 85.0, 140.0
            else:
                gx = (cam[0] + rx * t) / dx - 0.5
                gz = (cam[2] + rz * t) / dx - 0.5
                hy = _bil(Y, gx, gz)
                if hy < sea:
                    k = math.exp(-(sea - hy) / 12.0)
                    col0 = 30.0 + 60.0 * k
                    col1 = 70.0 + 70.0 * k
                    col2 = 130.0 + 50.0 * k
                else:
                    col0 = _bil(tex[:, :, 0], gx, gz)
                    col1 = _bil(tex[:, :, 1], gx, gz)
                    col2 = _bil(tex[:, :, 2], gx, gz)
            a = math.exp(-t / fog)
            img[py, px, 0] = col0 * a + sky_hor[0] * (1 - a)
            img[py, px, 1] = col1 * a + sky_hor[1] * (1 - a)
            img[py, px, 2] = col2 * a + sky_hor[2] * (1 - a)
    return img


@njit(parallel=True, cache=True)
def _distancias(Y, dx, cams, yaws, pitches, fov, aspect, nu, nv, sea, far):
    """Distancia al primer impacto de una rejilla nv x nu de rayos para cada cámara (inf = cielo)."""
    K = cams.shape[0]
    out = np.empty((K, nv, nu))
    f = 1.0 / math.tan(fov * 0.5)
    for idx in prange(K * nv * nu):
        k = idx // (nv * nu)
        r = idx - k * nv * nu
        iv = r // nu
        iu = r - iv * nu
        u = 2.0 * (iu + 0.5) / nu - 1.0
        v = -(2.0 * (iv + 0.5) / nv - 1.0) * aspect
        rx, ry, rz = _rayo(yaws[k], pitches[k], f, u, v)
        t, cod = _march(Y, dx, cams[k, 0], cams[k, 1], cams[k, 2], rx, ry, rz, sea, far)
        out[k, iv, iu] = t if cod > 0 else np.inf
    return out


@njit(parallel=True, cache=True)
def _vision(Y, dx, cams, objs, sea):
    """Fracción del segmento cámara -> objetivo recorrida antes de cortar el terreno (1 = libre)."""
    K = cams.shape[0]
    out = np.ones(K)
    for k in prange(K):
        ddx = objs[k, 0] - cams[k, 0]
        ddy = objs[k, 1] - cams[k, 1]
        ddz = objs[k, 2] - cams[k, 2]
        D = math.sqrt(ddx * ddx + ddy * ddy + ddz * ddz)
        if D < 2.0:
            continue
        t, cod = _march(Y, dx, cams[k, 0], cams[k, 1], cams[k, 2], ddx / D, ddy / D, ddz / D, sea, D)
        if cod == 1:
            out[k] = t / D
    return out


def _f64(Y):
    return np.ascontiguousarray(Y, np.float64)


def suelo(Y, x, z):
    """Cota de la superficie en (x, z) bloques: misma interpolación que el render, mar como mínimo."""
    dx = N / Y.shape[0]
    return max(float(_bil(_f64(Y), x / dx - 0.5, z / dx - 0.5)), float(SEA))


def vision(Y, cams, objetivo):
    """Fracción libre del camino desde cada cámara (K, 3) hasta el objetivo (x, y, z)."""
    cams = np.ascontiguousarray(np.atleast_2d(cams), np.float64)
    objs = np.ascontiguousarray(np.broadcast_to(np.asarray(objetivo, np.float64), cams.shape))
    return _vision(_f64(Y), N / Y.shape[0], cams, objs, float(SEA))


def orientar(x, y, z, objetivo, inclinacion=None):
    """Rumbo (y, si inclinacion es None, inclinación) en grados para mirar desde (x, y, z) al objetivo."""
    tx, ty, tz = objetivo
    rumbo = math.degrees(math.atan2(tx - x, -(tz - z))) % 360.0
    if inclinacion is None:
        inclinacion = float(np.clip(math.degrees(math.atan2(ty - y, math.hypot(tx - x, tz - z))), -25.0, 5.0))
    return rumbo, inclinacion


@dataclass
class Camara:
    x: float
    z: float
    y: float
    rumbo: float              # grados, 0 = norte, 90 = este
    inclinacion: float        # grados, positivo hacia arriba
    origen: tuple             # (x, z, y) de la cámara pedida
    movida: bool = False
    mediana: float = 0.0      # mediana de la distancia al primer impacto en la franja central
    cerca: float = 0.0        # fracción de rayos con impacto a menos de CERCA bloques
    vision: float = 1.0       # fracción libre del camino al objetivo (1 sin objetivo)
    tapada: bool = False      # la vista final no cumple la comprobación
    motivo: str = ''          # por qué se movió o reorientó la cámara

    @property
    def desplazamiento(self):
        return math.hypot(self.x - self.origen[0], self.z - self.origen[1])


def distancias(Y, cams, rumbos, inclinaciones, fov=75.0, W=960, H=540, far=9000.0):
    """Distancia al primer impacto de la rejilla REJILLA de rayos de cada cámara (K, 3): (K, filas,
    columnas), inf = cielo."""
    nu, nv = REJILLA
    return _distancias(_f64(Y), N / Y.shape[0], np.ascontiguousarray(np.atleast_2d(cams), np.float64),
                       np.radians(np.atleast_1d(rumbos)).astype(np.float64),
                       np.radians(np.atleast_1d(inclinaciones)).astype(np.float64),
                       math.radians(fov), H / W, nu, nv, float(SEA), far)


def diagnostico(d, far=9000.0):
    """Mediana de la franja central (tercio medio de filas) y fracción de impactos cercanos."""
    nv = d.shape[1]
    cen = d[:, nv // 3:nv - nv // 3].reshape(len(d), -1)
    med = np.median(np.where(np.isfinite(cen), cen, far), axis=1)
    cerca = (d < CERCA).mean(axis=(1, 2))
    return med, cerca


def _candidatos(Ys, x, z, atras, radio, aereo):
    """Posiciones alternativas: espiral alrededor de (x, z), retroceso en la dirección `atras`
    y, para el jugador, la cima local junto a cada punto (Y elevada en las vistas aéreas)."""
    dx = N / Ys.shape[0]
    paso = 75.0 if aereo else 45.0
    pts = []
    k = 1
    while True:                                   # espiral de Fermat: densidad uniforme
        r = paso * math.sqrt(k / math.pi)
        if r > radio:
            break
        a = k * 2.399963
        pts.append((x + r * math.cos(a), z + r * math.sin(a)))
        k += 1
    for r in np.arange(paso, radio + 1, paso):    # retroceso en sentido contrario al rumbo
        for lat in (0.0, -0.25 * r, 0.25 * r):
            pts.append((x + atras[0] * r - atras[1] * lat, z + atras[1] * r + atras[0] * lat))
    pts = [(px, pz) for px, pz in pts if 16 <= px <= N - 16 and 16 <= pz <= N - 16]
    out = [(px, pz, 0.0) for px, pz in pts]
    if aereo:
        out += [(px, pz, dy) for px, pz in [(x, z)] + pts for dy in (60.0, 140.0)]
    else:
        w = max(1, int(round(paso / dx)))
        n0, n1 = Ys.shape
        vistos = set()
        for px, pz in pts:
            i, j = int(pz / dx), int(px / dx)
            i0, j0 = max(0, i - w), max(0, j - w)
            win = Ys[i0:min(n0, i + w + 1), j0:min(n1, j + w + 1)]
            ii, jj = np.unravel_index(np.argmax(win), win.shape)
            c = (i0 + ii, j0 + jj)
            if c not in vistos:
                vistos.add(c)
                out.append(((c[1] + 0.5) * dx, (c[0] + 0.5) * dx, 0.0))
    return out


def encuadrar(Y, x, z, rumbo=None, inclinacion=0.0, objetivo=None, ojo=OJO, y_abs=None,
              fov=75.0, W=960, H=540, radio=RADIO, far=9000.0):
    """Cámara desde (x, z) que no esté tapada; si lo está, busca la mejor posición cercana.

    Jugador (y_abs None): ojo a `ojo` bloques sobre el suelo.  Vista elevada: Y absoluta y_abs
    (nunca por debajo del suelo + ojo).  Con objetivo (x, y, z) se mira hacia él (rumbo e,
    inclinacion None, inclinación) y se exige que el terreno no corte el rayo antes de VISION
    de la distancia.  La vista está tapada si la mediana de la franja central es menor que
    UMBRAL o más de FRAC_CERCA de los rayos impactan a menos de CERCA bloques.  La búsqueda
    recorre una espiral de `radio` bloques, retrocede en sentido contrario al rumbo y prueba
    puntos más altos; puntúa la apertura de la vista y penaliza el desplazamiento.
    """
    Y = _f64(Y)
    dx = N / Y.shape[0]
    Ys = np.maximum(Y, SEA)
    aereo = y_abs is not None

    def camaras(pos):
        cams = np.empty((len(pos), 3))
        ori = np.empty((len(pos), 2))
        for k, (px, pz, dy) in enumerate(pos):
            g = suelo(Y, px, pz) + ojo
            py = max(y_abs + dy, g) if aereo else g
            cams[k] = px, py, pz
            ori[k] = orientar(px, py, pz, objetivo, inclinacion) if objetivo is not None else (rumbo, inclinacion)
        return cams, ori

    def evaluar(pos):
        cams, ori = camaras(pos)
        med, cerca = diagnostico(distancias(Y, cams, ori[:, 0], ori[:, 1], fov, W, H, far), far)
        vis = vision(Y, cams, objetivo) if objetivo is not None else np.ones(len(pos))
        ok = (med >= UMBRAL) & (cerca <= FRAC_CERCA) & (vis >= VISION)
        return cams, ori, med, cerca, vis, ok

    def camara(cams, ori, med, cerca, vis, ok, k, motivo=''):
        movida = math.hypot(cams[k, 0] - x, cams[k, 2] - z) > 1.0 or abs(cams[k, 1] - cams[0, 1]) > 0.5
        return Camara(float(cams[k, 0]), float(cams[k, 2]), float(cams[k, 1]), float(ori[k, 0]),
                      float(ori[k, 1]), (x, z, float(cams[0, 1])), movida, float(med[k]), float(cerca[k]),
                      float(vis[k]), not bool(ok[k]), motivo)

    r0 = evaluar([(x, z, 0.0)])
    if r0[-1][0]:
        return camara(*r0, 0)
    med0, cerca0, vis0 = r0[2][0], r0[3][0], r0[4][0]
    motivos = []
    if med0 < UMBRAL or cerca0 > FRAC_CERCA:
        motivos.append(f'tapada: mediana {med0:.0f} bl, {100 * cerca0:.0f}% a <{CERCA:.0f} bl')
    if vis0 < VISION:
        motivos.append(f'sin línea de visión al objetivo ({100 * vis0:.0f}% libre)')
    motivo = '; '.join(motivos)

    rb = math.radians(r0[1][0, 0])
    atras = (-math.sin(rb), math.cos(rb))
    pos = [(x, z, 0.0)] + _candidatos(Ys, x, z, atras, radio, aereo)
    cams, ori, med, cerca, vis, ok = evaluar(pos)
    p = np.array(pos)
    ddx, ddz = p[:, 0] - x, p[:, 1] - z
    b = ddx * atras[0] + ddz * atras[1]                  # componente hacia atrás
    lat = -ddx * atras[1] + ddz * atras[0]
    efec = np.hypot(np.where(b > 0, 0.5 * b, b), lat)    # retroceder cuesta la mitad
    puntaje = (np.minimum(med, 1500.0) / 1500.0 - 0.5 * cerca - 0.4 * efec / radio
               - 0.2 * p[:, 2] / 200.0 + 0.3 * np.minimum(vis / VISION, 1.0))
    if not aereo:
        puntaje -= 2.0 * (Y[np.clip((p[:, 1] / dx).astype(int), 0, Y.shape[0] - 1),
                            np.clip((p[:, 0] / dx).astype(int), 0, Y.shape[1] - 1)] < SEA - 0.5)
    k = int(np.argmax(np.where(ok, puntaje, puntaje - 10.0)))
    if not ok[k] and objetivo is None and inclinacion < 2.0:
        # mirando hacia abajo (o en ladera suave) ninguna posición cumple: último recurso, alzar la vista
        c = encuadrar(Y, x, z, rumbo, 2.0, None, ojo, y_abs, fov, W, H, radio, far)
        if not c.tapada:
            c.motivo = f'{motivo}; inclinación {inclinacion:.0f}° -> 2°' + (f' (con 2°, {c.motivo})' if c.motivo else '')
            return c
    return camara(cams, ori, med, cerca, vis, ok, k, motivo)


def render(Y, tex, cam, W=960, H=540, fov=75.0, niebla=2500.0, far=9000.0):
    """Render desde una Camara."""
    dx = N / Y.shape[0]
    pos = np.array([cam.x, cam.y, cam.z], np.float64)
    img = _render(_f64(Y), np.ascontiguousarray(tex, np.float32), dx, pos, math.radians(cam.rumbo),
                  math.radians(cam.inclinacion), math.radians(fov), W, H, niebla, float(SEA), far)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def vista(Y, tex, x, z, rumbo, inclinacion=-2.0, altura_ojo=OJO, sobre_suelo=True, y_abs=None,
          fov=75.0, W=960, H=540, niebla=2500.0, far=9000.0):
    """Render desde (x, z) en bloques, sin comprobar la vista.  rumbo en grados (0 = norte, 90 = este)."""
    y = suelo(Y, x, z) + altura_ojo if y_abs is None else y_abs
    cam = Camara(x, z, y, rumbo, inclinacion, (x, z, y))
    return render(Y, tex, cam, W, H, fov, niebla, far), y
