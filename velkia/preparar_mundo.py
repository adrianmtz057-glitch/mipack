"""Prepara los mapas de resolución completa (8192²) para mundo.py a partir de un terreno grueso.

Pasos: ampliar el terreno, agua (mar, río por tramos planos contenido entre orillas, lagos),
superficie y biomas por zona/pendiente/altura, construcciones recortadas y asentadas.

Reglas del agua (Minecraft la tiene plana por nivel):
  * cada celda de agua tiene un nivel entero; a lo largo del río el nivel nunca sube;
  * toda celda de agua tiene orillas sólidas a su nivel o agua vecina (nada cuelga);
  * donde el nivel baja (rápido o cascada) el tramo de abajo es agua: el agua del tramo de
    arriba cae sobre ella y no se derrama por tierra.
"""
import json
import os

import numpy as np
from scipy import ndimage as ndi

from .layout import N, SEA
from .noise import spectral_noise


def ampliar(h_coarse, factor, out_dtype=np.float32, chunk_rows=512):
    """Ampliación bicúbica por bloques de filas."""
    n = h_coarse.shape[0]
    M = n * factor
    out = np.empty((M, M), out_dtype)
    for r0 in range(0, M, chunk_rows):
        r1 = min(M, r0 + chunk_rows)
        y = (np.arange(r0, r1) + 0.5) / factor - 0.5
        x = (np.arange(M) + 0.5) / factor - 0.5
        Yg, Xg = np.meshgrid(y, x, indexing='ij')
        out[r0:r1] = ndi.map_coordinates(h_coarse, [Yg, Xg], order=3, mode='nearest')
    return out


def rio_full(Y, xy, ancho, nivel_ini, nivel_fin, nivel_fijo=None, prof=3.0):
    """Talla un río sobre Y (cotas absolutas, resolución de bloque) a lo largo de la polilínea xy.

    ancho: array por vértice (bloques).  nivel_fijo: lista de (i0, i1, nivel) tramos obligados.
    Devuelve (Y, WL) con WL el nivel del agua (-32768 sin agua)."""
    M = Y.shape[0]
    WL = np.full(Y.shape, -32768, np.int16)
    # nivel del agua a lo largo del curso: bajo el terreno, monótono decreciente, entero
    L = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    ix = np.clip(xy[:, 0].astype(int), 0, M - 1)
    iz = np.clip(xy[:, 1].astype(int), 0, M - 1)
    terreno = ndi.minimum_filter(Y, size=9)[iz, ix]
    lineal = nivel_ini + (nivel_fin - nivel_ini) * L / L[-1]
    nivel = np.minimum(terreno - 1.0, lineal)
    if nivel_fijo:
        for i0, i1, v in nivel_fijo:
            nivel[i0:i1] = v
    nivel = np.minimum.accumulate(nivel)
    nivel = np.floor(nivel).astype(np.int32)
    nivel = np.maximum(nivel, SEA)
    # rasterizar: para cada celda cerca del curso, vértice más cercano
    mask = np.zeros(Y.shape, bool)
    wmax = int(np.ceil(ancho.max())) + 6
    x0, x1 = max(0, ix.min() - wmax), min(M, ix.max() + wmax)
    z0, z1 = max(0, iz.min() - wmax), min(M, iz.max() + wmax)
    from scipy.spatial import cKDTree
    t = cKDTree(xy)
    zz, xx = np.mgrid[z0:z1, x0:x1]
    d, k = t.query(np.c_[xx.ravel() + 0.5, zz.ravel() + 0.5], distance_upper_bound=wmax)
    ok = np.isfinite(d)
    kk = np.where(ok, k, 0)
    half = 0.5 * ancho[kk]
    dentro = ok & (d <= half)
    lvl = nivel[kk]
    sub = Y[z0:z1, x0:x1].ravel()
    wl = WL[z0:z1, x0:x1].ravel()
    # cauce parabólico
    cauce = lvl - prof * (1.0 - (d / np.maximum(half, 1.0)) ** 2) - 0.5
    sub = np.where(dentro, np.minimum(sub, cauce), sub)
    wl = np.where(dentro, lvl, wl).astype(np.int16)
    # orillas: anillo de 2 bloques alrededor del agua al menos al nivel del agua
    orilla = ok & (d > half) & (d <= half + 2.5)
    sub = np.where(orilla, np.maximum(sub, lvl), sub)
    Y[z0:z1, x0:x1] = sub.reshape(zz.shape)
    WL[z0:z1, x0:x1] = wl.reshape(zz.shape)
    return Y, WL, nivel


def comprobar_agua(Y, WL):
    """Celdas de agua con un vecino sin agua cuyo terreno queda por debajo del nivel (fuga)."""
    agua = WL > -32768
    fugas = np.zeros(Y.shape, bool)
    for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        Yn = np.roll(Y, (dz, dx), (0, 1))
        Wn = np.roll(WL, (dz, dx), (0, 1))
        an = Wn > -32768
        fugas |= agua & ~an & (Yn < WL)
    return fugas
