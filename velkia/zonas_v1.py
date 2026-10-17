"""Zonas de la v1 (lienzo aprobado por el usuario) sobre la malla gruesa de 1024² (8 bloques/celda).

Parte de referencia/zonas_v6b.npy (contornos dibujados por el usuario digitalizados, con los
Jardines = solo el valle hundido) y aplica los ajustes del lienzo:
  * mitad norte de los domos -> arena normal;
  * la meseta gris que rodea los Jardines pasa a la zona vecina (terracota o dunas);
  * isla redonda del volcán (R = 1250 bloques alrededor de la caldera);
  * bordes a manchas (~200 bloques) salvo mar, Jardines y la isla, que quedan nítidos.
"""
import numpy as np
from scipy import ndimage as ndi

from .noise import spectral_noise

NOMBRES = ['mar', 'montanas', 'mura', 'jardines', 'terracota', 'dunas', 'volcan', 'salar', 'domos', 'arena']
Z = {k: i for i, k in enumerate(NOMBRES)}
R_ISLA = 1250.0


def zonas_v1(d, ruta='referencia/zonas_v6b.npy'):
    """Devuelve (z, z_mix): zonas nítidas y zonas con bordes a manchas (uint8, 1024²)."""
    z = np.load(ruta).astype(np.uint8)
    n = z.shape[0]
    dx = 8192.0 / n
    yy, xx = np.mgrid[0:n, 0:n]
    corte = 5000 + 180 * np.sin(xx * dx / 900.0)
    z = np.where((z == Z['domos']) & (yy * dx < corte), Z['arena'], z)
    # anillo de meseta alrededor de los Jardines -> terracota o dunas
    jd = ndi.distance_transform_edt(z != Z['jardines']) * dx
    anillo = (z == Z['montanas']) & (jd < 900) & (yy * dx > 1900)
    ok = (z == Z['terracota']) | (z == Z['dunas'])
    _, (ia, ja) = ndi.distance_transform_edt(~ok, return_indices=True)
    z = np.where(anillo, z[ia, ja], z)
    # isla redonda del volcán
    cx, cz, _ = d['caldera']
    rv = np.hypot((xx + 0.5) * dx - cx, (yy + 0.5) * dx - cz)
    fuera = (z == Z['volcan']) & (rv >= R_ISLA)
    otra = (z > 0) & (z != Z['volcan'])
    _, (ii, jj) = ndi.distance_transform_edt(~otra, return_indices=True)
    z = np.where(fuera, z[ii, jj], z)
    z = np.where((z > 0) & (rv < R_ISLA) & (z != Z['jardines']), Z['volcan'], z)
    # bordes a manchas
    peso = []
    for k in range(1, len(NOMBRES)):
        oh = ndi.gaussian_filter((z == k).astype(np.float32), 14)
        ruido = spectral_noise((n, n), 2.4, 200 + k, kmin=8.0, kmax=160.0)
        peso.append(oh * np.clip(1.0 + 0.9 * ruido, 0.15, None) * (oh > 0.02))
    z_mix = np.argmax(np.stack(peso), 0).astype(np.uint8) + 1
    nitidas = (z == 0) | (z == Z['jardines']) | (z == Z['volcan'])
    z_mix = np.where(nitidas, z, z_mix)
    z_mix = np.where(((z_mix == Z['jardines']) | (z_mix == Z['volcan'])) & (z_mix != z), z, z_mix)
    # tierra fuera de los contornos dibujados: zona de tierra más cercana
    _, (ii, jj) = ndi.distance_transform_edt(z_mix == 0, return_indices=True)
    z_tierra = z_mix[ii, jj]
    return z, z_mix, z_tierra
