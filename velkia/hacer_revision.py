"""Genera las imágenes de revisión v2 a partir de salida/etapa1.npz (uso: python3 -m velkia.hacer_revision)."""
import sys

import numpy as np

from .colocar import colocar
from .layout import Layout, N, SEA
from .revision2 import generar
from .sim import ocean_mask


def main(etapa='salida/etapa1.npz', out='revision', prefijo='v2'):
    d = np.load(etapa)
    h = d['h']
    n = h.shape[0]
    dx = N / n
    Y0 = h + SEA
    lay = Layout(n)
    ch = d['chain']
    cy = Y0.ravel()[ch]
    cx, cz = (ch % n + 0.5) * dx, (ch // n + 0.5) * dx

    def rio_y(x, z):
        k = int(np.argmin(np.hypot(cx - x, cz - z)))
        return float(cy[k]) + 1.5

    out_c, Ym = colocar(Y0, dx, rio_y=rio_y, dist_costa=lay.dist_coast)
    # a 8 bloques/celda el asiento puede tapar celdas del cauce (calles de Vieja Velkia junto al
    # canal): se vuelve a imponer el cauce cuesta abajo fuera de los Jardines
    from . import lem
    k_in = int(np.argmin(np.hypot(cx - 2260, cz - 1950)))
    k_out = int(np.argmin(np.hypot(cx - 3040, cz - 2900)))
    hm = np.ascontiguousarray(Ym - SEA, np.float64)
    bm = hm.copy()
    for tramo in (ch[:k_in + 1], ch[k_out:]):
        lem.breach_chain(hm, bm, np.ascontiguousarray(tramo), 2e-4, dx)
    Ym = hm + SEA
    oc = ocean_mask(Ym - SEA, 0.0)
    lagos = d['lagos_jardines'] if 'lagos_jardines' in d.files else np.zeros_like(oc)
    afl = {str(k): d['afl_' + str(k)] for k in d['afluentes']} if 'afluentes' in d.files else {}
    boca = d['boca'] if 'boca' in d.files and np.any(d['boca']) else None
    # perfil del río en tierra con marcas
    en_mar = oc.ravel()[ch]
    k_fin = int(np.argmax(en_mar)) if en_mar.any() else ch.size
    prof = Ym.ravel()[ch][:k_fin]
    marcas = []
    for nombre, (x, z) in [('entra a Jardines', (2260, 1950)), ('sale de Jardines', (3040, 2900)),
                           ('Vieja Velkia', (6656, 5808))]:
        marcas.append((int(np.argmin(np.hypot(cx[:k_fin] - x, cz[:k_fin] - z))), nombre))
    notas = [
        'Gran Pirámide: la escalera monumental quedó en la cara SUR tras la rotación (mira a la Esfinge). '
        'La arena acumulada quedó en las caras ESTE y NORTE: es arena de sotavento, así que el viento dominante '
        'sopla desde el OSO hacia el ENE; las dunas se simularán con ese viento.',
        'Vieja Velkia: su canal (Y=87 en el schematic) queda a la cota del río; el fondo del cañón se ensancha en una vega '
        'en la confluencia con el cañón lateral. La arena que la entierra en parte va en la etapa de detalle.',
        'Torre: en la cima costera más cercana a su punto; su sendero viejo se recortó y el nuevo se trazará sobre la ladera.',
        'Aldea oeste: terrazas suaves de diseño (2,9° hacia el ESE): se buscó una ladera con esa pendiente y orientación.',
        'Mapa 2: no hay un segundo "árbol especial" al suroeste; el único es el de los Jardines (Jardines colgantes).',
    ]
    paths, filas = generar(Y0, Ym, out_c, d['rio_xy'], afl, lagos, oc, out, boca=boca,
                           perfil=(prof, marcas), notas=notas)
    from .validacion import generar as vistas
    pm, _ = vistas(Ym, oc, out, prefijo=prefijo, W=800, H=450)
    np.savez_compressed('salida/v2_asentado.npz', Y=Ym)
    return paths + [pm], filas, prof


if __name__ == '__main__':
    p, f, prof = main(*sys.argv[1:])
    for fl in f:
        print(fl)
    print('perfil: fuente', prof[0], 'fin', prof[-1], 'subidas', int((np.diff(prof) > 0.5).sum()))
    print(p)
