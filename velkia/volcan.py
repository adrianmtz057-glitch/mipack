"""Construcción volcánica: coladas de lava apiladas + caída de piroclastos.

Cada colada parte del cráter (o de un respiradero lateral), avanza por máxima pendiente
con desvíos aleatorios y se ensancha lateralmente; deja un depósito de espesor decreciente
hacia los bordes (con albardones).  Miles de coladas construyen un estratovolcán irregular,
con lóbulos y lenguas de lava que luego la erosión fluvial disecciona.
"""
import math

import numpy as np
from numba import njit

DI8 = np.array([-1, -1, -1, 0, 0, 1, 1, 1])
DJ8 = np.array([-1, 0, 1, -1, 1, -1, 0, 1])
DD8 = np.array([1.414, 1.0, 1.414, 1.0, 1.0, 1.414, 1.0, 1.414])


@njit(cache=True)
def _flow(h, dep, i0, j0, length_cells, width_cells, thick, seed, sea_cells):
    np.random.seed(seed)
    ny, nx = h.shape
    i, j = i0, j0
    di_prev, dj_prev = 0, 0
    path_i = np.empty(length_cells, np.int64)
    path_j = np.empty(length_cells, np.int64)
    n = 0
    for step in range(length_cells):
        path_i[n] = i
        path_j[n] = j
        n += 1
        # elegir vecino con máxima pendiente + ruido + inercia
        best = -1e9
        bi, bj = i, j
        for d in range(8):
            ii = i + DI8[d]
            jj = j + DJ8[d]
            if ii < 1 or ii >= ny - 1 or jj < 1 or jj >= nx - 1:
                continue
            s = (h[i, j] + dep[i, j] - h[ii, jj] - dep[ii, jj]) / DD8[d]
            s += 0.15 * np.random.randn() + 0.25 * (DI8[d] * di_prev + DJ8[d] * dj_prev)
            if s > best:
                best = s
                bi, bj = ii, jj
        if bi == i and bj == j:
            break
        di_prev, dj_prev = bi - i, bj - j
        i, j = bi, bj
        if h[i, j] < 0.0 and sea_cells:   # la lava se detiene al entrar al mar (deja un delta de lava)
            break
    # depósito: perfil transversal con albardones, espesor que crece hacia el frente
    for k in range(n):
        frac = k / max(n - 1, 1)
        w = width_cells * (0.6 + 0.8 * frac)
        t = thick * (0.6 + 0.9 * frac)
        ci, cj = path_i[k], path_j[k]
        r = int(w) + 1
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                ii = ci + a
                jj = cj + b
                if ii < 0 or ii >= ny or jj < 0 or jj >= nx:
                    continue
                d = math.sqrt(a * a + b * b) / w
                if d > 1.0:
                    continue
                prof = (1.0 - d ** 4) * (0.85 + 0.35 * math.exp(-((d - 0.8) / 0.12) ** 2))
                v = t * prof
                if v > dep[ii, jj] * 0.0 + 0.0:
                    dep[ii, jj] += v / (1.0 + 0.15 * (2 * r + 1) / max(w, 1.0))
    return n


def build_volcano(h, dx, center, height=250.0, radius=1100.0, n_flows=2600, seed=5, crater_r=110.0,
                  vents_lat=6, log=True):
    """Construye un volcán sobre h (m sobre el mar). Devuelve h nuevo y el espesor de lava."""
    rng = np.random.default_rng(seed)
    ny, nx = h.shape
    cy, cx = center[1] / dx, center[0] / dx
    zz, xx = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
    r = np.hypot((zz - cy) * dx, (xx - cx) * dx)
    dep = np.zeros_like(h)
    # piroclastos: perfil cóncavo típico de estratovolcán (h ~ exp)
    tephra = height * 0.55 * np.exp(-r / (radius * 0.28))
    dep += tephra
    lat = [(cy + rng.uniform(-1, 1) * radius * 0.35 / dx, cx + rng.uniform(-1, 1) * radius * 0.35 / dx)
           for _ in range(vents_lat)]
    for k in range(n_flows):
        if rng.random() < 0.8:
            a = rng.uniform(0, 2 * np.pi)
            i0 = int(cy + np.sin(a) * crater_r / dx)
            j0 = int(cx + np.cos(a) * crater_r / dx)
        else:
            vi, vj = lat[rng.integers(len(lat))]
            i0, j0 = int(vi), int(vj)
        L = int(rng.uniform(0.3, 1.25) * radius / dx)
        W = rng.uniform(25, 70) / dx
        T = rng.uniform(0.8, 2.2) * (height / 250.0) * 0.35
        _flow(h, dep, i0, j0, L, W, T, int(seed * 100000 + k), True)
        if log and k % 500 == 0:
            print(f'  [volcán] colada {k}/{n_flows}  cumbre={float((h + dep).max()):.0f} m', flush=True)
    # cráter: depresión de paredes empinadas en la cima
    crater = np.clip(1.0 - (r / crater_r) ** 2, 0, None)
    dep -= crater * height * 0.22
    return h + dep, dep
