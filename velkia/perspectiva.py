"""Renders en perspectiva (trazado de rayos sobre el mapa de alturas) con niebla atmosférica.

Para validar el terreno como lo vería un jugador: cámara a 1,6 bloques sobre el suelo, o
vistas lejanas elevadas.  La textura de color es el relieve sombreado del mapa.
"""
import math

import numpy as np
from numba import njit, prange
from PIL import Image

from .layout import N, SEA


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


@njit(parallel=True, cache=True)
def _render(Y, tex, dx, cam, yaw, pitch, fov, W, H, fog, sea, far):
    img = np.zeros((H, W, 3), np.float32)
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    f = 1.0 / math.tan(fov * 0.5)
    sky_top = np.array([110.0, 150.0, 210.0])
    sky_hor = np.array([205.0, 215.0, 228.0])
    for py in prange(H):
        for px in range(W):
            u = (2.0 * (px + 0.5) / W - 1.0)
            v = -(2.0 * (py + 0.5) / H - 1.0) * H / W
            # base de la cámara: rumbo 0 = norte (-z), 90° = este (+x)
            fwx, fwz = sy, -cy                 # adelante (horizontal)
            rtx, rtz = cy, sy                  # derecha
            # adelante e "arriba" inclinados por el pitch
            fx_ = fwx * cp
            fy_ = sp
            fz_ = fwz * cp
            ux = -fwx * sp
            uy = cp
            uz = -fwz * sp
            dxw = u * rtx + v * ux + f * fx_
            ry = v * uy + f * fy_
            dzw = u * rtz + v * uz + f * fz_
            nrm = math.sqrt(dxw * dxw + ry * ry + dzw * dzw)
            dxw /= nrm
            ry /= nrm
            dzw /= nrm
            t = 1.0
            hit = False
            col0 = 0.0
            col1 = 0.0
            col2 = 0.0
            while t < far:
                x = cam[0] + dxw * t
                yv = cam[1] + ry * t
                z = cam[2] + dzw * t
                gx = x / dx - 0.5
                gz = z / dx - 0.5
                if gx < 0 or gz < 0 or gx > Y.shape[1] - 1 or gz > Y.shape[0] - 1:
                    if yv < sea:
                        col0, col1, col2 = 45.0, 85.0, 140.0
                        hit = True
                    break
                hy = _bil(Y, gx, gz)
                ground = hy if hy > sea else sea
                if yv <= ground:
                    # refinar
                    t0 = t - max(0.4, t * 0.004)
                    for _ in range(8):
                        tm = 0.5 * (t0 + t)
                        xm = cam[0] + dxw * tm
                        ym = cam[1] + ry * tm
                        zm = cam[2] + dzw * tm
                        hm = _bil(Y, xm / dx - 0.5, zm / dx - 0.5)
                        gm = hm if hm > sea else sea
                        if ym <= gm:
                            t = tm
                        else:
                            t0 = tm
                    x = cam[0] + dxw * t
                    z = cam[2] + dzw * t
                    gx = x / dx - 0.5
                    gz = z / dx - 0.5
                    hy = _bil(Y, gx, gz)
                    if hy < sea:
                        depth = sea - hy
                        k = math.exp(-depth / 12.0)
                        col0 = 30.0 + 60.0 * k
                        col1 = 70.0 + 70.0 * k
                        col2 = 130.0 + 50.0 * k
                    else:
                        col0 = _bil(tex[:, :, 0], gx, gz)
                        col1 = _bil(tex[:, :, 1], gx, gz)
                        col2 = _bil(tex[:, :, 2], gx, gz)
                    hit = True
                    break
                t += max(0.4, t * 0.004)
            # cielo
            el = ry
            g = min(1.0, max(0.0, el * 3.0))
            s0 = sky_hor[0] * (1 - g) + sky_top[0] * g
            s1 = sky_hor[1] * (1 - g) + sky_top[1] * g
            s2 = sky_hor[2] * (1 - g) + sky_top[2] * g
            if hit:
                a = math.exp(-t / fog)
                img[py, px, 0] = col0 * a + sky_hor[0] * (1 - a)
                img[py, px, 1] = col1 * a + sky_hor[1] * (1 - a)
                img[py, px, 2] = col2 * a + sky_hor[2] * (1 - a)
            else:
                img[py, px, 0] = s0
                img[py, px, 1] = s1
                img[py, px, 2] = s2
    return img


def vista(Y, tex, x, z, rumbo, inclinacion=-2.0, altura_ojo=1.62, sobre_suelo=True, y_abs=None,
          fov=75.0, W=960, H=540, niebla=2500.0, far=9000.0):
    """Render desde (x, z) en bloques.  rumbo en grados (0 = norte, 90 = este)."""
    n = Y.shape[0]
    dx = N / n
    if y_abs is None:
        gy = float(_bil(Y, x / dx - 0.5, z / dx - 0.5))
        y = max(gy, SEA) + altura_ojo
    else:
        y = y_abs
    cam = np.array([x, y, z], np.float64)
    img = _render(Y.astype(np.float64), tex.astype(np.float32), dx, cam, math.radians(rumbo),
                  math.radians(inclinacion), math.radians(fov), W, H, niebla, float(SEA), far)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), y
