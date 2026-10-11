"""Ruido fractal (síntesis espectral) y utilidades de remuestreo."""
import numpy as np
from scipy import ndimage as ndi


def spectral_noise(shape, beta=2.0, seed=0, kmin=None, kmax=None, dtype=np.float32):
    """Ruido gaussiano con espectro de potencia ~ k^-beta (beta=2: browniano 2D).

    Periódico; normalizado a media 0, desviación 1. kmin/kmax en ciclos por dominio
    (pasa-banda opcional).
    """
    rng = np.random.default_rng(seed)
    ny, nx = shape
    ky = np.fft.fftfreq(ny) * ny
    kx = np.fft.rfftfreq(nx) * nx
    k = np.sqrt(ky[:, None] ** 2 + kx[None, :] ** 2)
    k[0, 0] = 1.0
    amp = k ** (-beta / 2.0)
    if kmin is not None:
        amp *= 1.0 / (1.0 + (kmin / k) ** 8)
    if kmax is not None:
        amp *= 1.0 / (1.0 + (k / kmax) ** 8)
    amp[0, 0] = 0.0
    ph = rng.standard_normal((ny, kx.size)) + 1j * rng.standard_normal((ny, kx.size))
    f = np.fft.irfft2(ph * amp, s=shape)
    f -= f.mean()
    f /= f.std() + 1e-12
    return f.astype(dtype)


def ridged(n):
    """Transforma ruido gaussiano en ruido 'de crestas' en [0,1]."""
    return 1.0 - np.abs(np.tanh(n))


def resize(a, shape, order=1):
    """Remuestreo con alineación de centros de celda (zoom de scipy)."""
    zy = shape[0] / a.shape[0]
    zx = shape[1] / a.shape[1]
    if order == 0:
        iy = np.minimum((np.arange(shape[0]) / zy).astype(np.int64), a.shape[0] - 1)
        ix = np.minimum((np.arange(shape[1]) / zx).astype(np.int64), a.shape[1] - 1)
        return a[iy][:, ix]
    # coordenadas de centros
    y = (np.arange(shape[0]) + 0.5) / zy - 0.5
    x = (np.arange(shape[1]) + 0.5) / zx - 0.5
    out = np.empty(shape, dtype=np.float32 if a.dtype != np.float64 else np.float64)
    # por bloques de filas para controlar memoria
    step = max(1, int(2 ** 24 // max(shape[1], 1)))
    for r0 in range(0, shape[0], step):
        yy = y[r0:r0 + step]
        Y, X = np.meshgrid(yy, x, indexing='ij')
        out[r0:r0 + step] = ndi.map_coordinates(a, [Y, X], order=order, mode='nearest')
    return out


def blur(a, sigma):
    return ndi.gaussian_filter(a, sigma, mode='nearest')


def warp(a, du, dv, order=1):
    """Deforma a según desplazamientos (en celdas)."""
    ny, nx = a.shape
    Y, X = np.meshgrid(np.arange(ny, dtype=np.float32), np.arange(nx, dtype=np.float32), indexing='ij')
    return ndi.map_coordinates(a, [Y + dv, X + du], order=order, mode='nearest')
