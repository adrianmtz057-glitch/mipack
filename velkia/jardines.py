"""Jardines de Velkia: excavación glaciar del valle (modelo Yosemite).

El glaciar que bajaba de la cordillera llenó la cubeta de los Jardines y la excavó en U:
fondo plano, paredes de granito casi verticales que se tienden hacia arriba, un domo
central más duro que el hielo rodeó (roca aborregada) y, a su alrededor, cubetas
sobreexcavadas que hoy son un anillo de lagos.  El umbral rocoso de la salida (riegel)
retiene los lagos; el río sale por una garganta al sureste.

Se aplica al final de la fase glaciar como plantilla de la erosión del glaciar de los
Jardines (el modelo SIA a 8 bloques/celda no resuelve bien una cubeta de este tamaño);
la erosión fluvial y de laderas posterior actúa sobre ella.
"""
import numpy as np
from scipy import ndimage as ndi

from .layout import jardines_r, poi_blocks
from .noise import spectral_noise


def excavar(h, b, lay, chain, floor_h=58.0, dome_h=16.0, lake_depth=7.0, seed=17):
    """Devuelve (h, b, lagos) con el valle excavado.  h, b relativos al mar."""
    n = lay.n
    dx = lay.dx
    zz, xx = lay.coords()
    r = jardines_r(xx, zz)
    h = h.copy()
    b = b.copy()
    # perfil en U: fondo plano hasta r=0.80, paredes que se empinan hacia arriba hasta r=1
    s = np.clip((r - 0.80) / 0.20, 0, 1) ** 1.7
    target = floor_h + np.maximum(h - floor_h, 0) * s
    # domo central (roca aborregada) donde se asientan los Jardines colgantes
    dome = dome_h * np.clip(1 - (r / 0.30) ** 2, 0, 1) ** 0.8
    target = np.where(r < 0.80, floor_h + dome, target)
    # anillo de cubetas sobreexcavadas (lagos) alrededor del domo
    ruido = spectral_noise((n, n), 3.0, seed)
    anillo = np.exp(-((r - 0.56) / 0.10) ** 2) * (ruido > -0.2)
    anillo = ndi.gaussian_filter(anillo.astype(np.float64), 1.2)
    target = target - lake_depth * anillo * (r < 0.78)
    nuevo = np.where(r <= 1.0, np.minimum(h, target), h)
    # garganta de salida y entrada del río: a lo largo del cauce entre r=0.75 y r=1.4
    cauce = np.zeros(n * n, bool)
    cauce[chain] = True
    cauce = cauce.reshape(n, n)
    d = ndi.distance_transform_edt(~cauce) * dx
    rr = r
    zona = (rr > 0.75) & (rr < 1.40)
    # el río sale por el sureste: la garganta (umbral) queda 1 m bajo el fondo
    bx, bz = poi_blocks('jardines_de_velkia')
    sureste = (xx - bx) > 0
    lip = floor_h - 1.0
    garganta = zona & sureste & (d < 90)
    perfil = lip + np.maximum(nuevo - lip, 0) * np.clip(d / 90.0, 0, 1) ** 1.5
    nuevo = np.where(garganta, np.minimum(nuevo, perfil), nuevo)
    lagos = (anillo > 0.35) & (r < 0.78)
    sed = 3.0 * (r < 0.80)
    b = np.minimum(b, nuevo - sed)
    return nuevo, b, lagos
