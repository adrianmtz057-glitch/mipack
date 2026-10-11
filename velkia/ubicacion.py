"""Ubicación fina de construcciones sobre el terreno generado.

* Torre: cima o promontorio más cercano a su punto del mapa 2, cerca de la costa.
* Aldea oeste (casas en terrazas): ladera con pendiente y orientación parecidas a las de diseño.
* Vieja Velkia: se mantiene en el canal del río; su fondo de cañón se ensancha (vega).
* El resto: se mantiene en su punto del mapa 2 y se asienta con corte y relleno.
"""
import numpy as np
from scipy import ndimage as ndi

from .layout import N, SEA


def _celda(x, z, dx, n):
    return int(np.clip(z / dx, 0, n - 1)), int(np.clip(x / dx, 0, n - 1))


def buscar_cima(Y, dx, x, z, radio=650.0, dist_costa=None, max_costa=700.0, prominencia=60.0):
    """Cima local (máximo en una ventana de ~120 bloques) más alta cerca de (x, z),
    opcionalmente a menos de max_costa bloques de la costa.  Devuelve (x, z, Y)."""
    n = Y.shape[0]
    i0, j0 = _celda(x, z, dx, n)
    r = int(radio / dx)
    a0, a1, b0, b1 = max(0, i0 - r), min(n, i0 + r), max(0, j0 - r), min(n, j0 + r)
    win = Y[a0:a1, b0:b1]
    loc = ndi.maximum_filter(win, size=max(3, int(120 / dx))) == win
    ii, jj = np.nonzero(loc)
    best = None
    for i, j in zip(ii, jj):
        gi, gj = a0 + i, b0 + j
        if dist_costa is not None and not (0 < dist_costa[gi, gj] < max_costa):
            continue
        d = np.hypot(gi - i0, gj - j0) * dx
        if d > radio:
            continue
        # prominencia simple: altura sobre la mediana del entorno de 400 bloques
        k = int(400 / dx)
        ent = Y[max(0, gi - k):gi + k, max(0, gj - k):gj + k]
        prom = Y[gi, gj] - np.median(ent)
        if prom < prominencia * 0.5:
            continue
        score = Y[gi, gj] + 0.6 * prom - 0.05 * d
        if best is None or score > best[0]:
            best = (score, gi, gj)
    if best is None:
        i, j = np.unravel_index(np.argmax(win), win.shape)
        best = (0, a0 + i, b0 + j)
    _, gi, gj = best
    return (gj + 0.5) * dx, (gi + 0.5) * dx, float(Y[gi, gj])


def buscar_ladera(Y, dx, x, z, radio, pendiente, aspecto_deg, tam, excluir=None):
    """Lugar cuya pendiente media (bloques/bloque) y orientación de bajada (grados desde el
    este hacia el sur) en una ventana de tam bloques se parezcan a las de diseño."""
    n = Y.shape[0]
    gz, gx = np.gradient(Y, dx)
    k = max(3, int(tam / dx))
    mgx = ndi.uniform_filter(gx, k)
    mgz = ndi.uniform_filter(gz, k)
    rug = np.sqrt(ndi.uniform_filter(gx ** 2 + gz ** 2, k) - (mgx ** 2 + mgz ** 2)).clip(0)
    s = np.hypot(mgx, mgz)
    asp = np.degrees(np.arctan2(-mgz, -mgx)) % 360   # dirección de bajada
    da = np.abs((asp - aspecto_deg + 180) % 360 - 180)
    zz, xx = np.meshgrid((np.arange(n) + 0.5) * dx, (np.arange(n) + 0.5) * dx, indexing='ij')
    d = np.hypot(xx - x, zz - z)
    coste = (np.abs(s - pendiente) / max(pendiente, 0.02)) * 2.0 + da / 45.0 + rug / max(pendiente, 0.02) + d / radio
    coste[(d > radio) | (Y < SEA + 3)] = np.inf
    if excluir is not None:
        coste[excluir] = np.inf
    i, j = np.unravel_index(np.argmin(coste), coste.shape)
    return (j + 0.5) * dx, (i + 0.5) * dx, {'pendiente': float(s[i, j]), 'aspecto': float(asp[i, j]),
                                            'rugosidad': float(rug[i, j]), 'coste': float(coste[i, j])}
