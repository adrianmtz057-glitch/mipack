"""Imágenes de revisión a partir de salida/etapa1.npz (uso: python3 -m velkia.hacer_revision [prefijo]).

1. Amplía el terreno a resolución de bloque (8192²) y asienta allí las construcciones (talud 1:2).
2. Vuelve a la malla gruesa para el mapa y las vistas; impone el cauce cuesta abajo.
3. Agua: niveles del río, lagos, cascadas, orillas y comprobación de continuidad (agua.py).
4. Mapa + tabla, comparación con la referencia, acercamientos, perfiles y vistas en perspectiva.
"""
import json
import sys
import time

import numpy as np

from . import agua, lem
from .colocar import colocar
from .layout import Layout, N, SEA, poi_blocks
from .preparar_mundo import ampliar
from .revision2 import generar
from .sim import ocean_mask


def vistas_extra(d, Y, dx):
    """Vistas de los elementos de esta revisión: mesas, volcán, paredes y cascada de los Jardines."""
    out = []
    grupos = json.loads(str(d['relieves_json'])) if 'relieves_json' in d.files else []
    mesas = [g for g in grupos if g['tipo'] == 'mesa']
    if mesas:
        g = max(mesas, key=lambda g: len(g['miembros']))
        m0 = g['miembros'][0]
        out.append(dict(titulo='Mesas y buttes del desierto (jugador)',
                        desde=(m0['x'] + 650.0, m0['z'] + 420.0), objetivo=(m0['x'], m0['z'], m0.get('cima', 120) + SEA),
                        inclinacion=None))
    domos = [g for g in grupos if g['tipo'] == 'domo']
    if domos:
        m0 = domos[0]['miembros'][0]
        out.append(dict(titulo='Domos de granito (jugador)', desde=(m0['x'] - 420.0, m0['z'] + 380.0),
                        objetivo=(m0['x'], m0['z']), inclinacion=None))
    if 'caldera' in d.files:
        cx, cz, cr = d['caldera']
        out.append(dict(titulo='Volcán desde el llano (jugador)', desde=(cx + 1500.0, cz - 900.0),
                        objetivo=(cx, cz, float(Y[int(cz / dx), int((cx + cr) / dx)])), inclinacion=None))
        out.append(dict(titulo='Caldera desde su borde (jugador)', desde=(cx + cr + 30.0, cz + 20.0),
                        objetivo=(cx - 0.4 * cr, cz, float(Y[int(cz / dx), int(cx / dx)])), inclinacion=None))
    if 'jardines_domo' in d.files:
        jx, jz, jr = d['jardines_domo']
        jp, jpz = poi_blocks('jardines_de_velkia')
        out.append(dict(titulo='Jardines: pared y domo cortado a pico desde el fondo (jugador)',
                        desde=(jx + (jp - jx) * 0.75, jz + (jpz - jz) * 0.75),
                        objetivo=(jx, jz, float(np.max(Y[int(jz / dx) - 3:int(jz / dx) + 4, int(jx / dx) - 3:int(jx / dx) + 4]))),
                        inclinacion=None))
    if 'cascadas' in d.files and len(d['cascadas']):
        x, z, yb, yp, ux, uz = d['cascadas'][0]
        out.append(dict(titulo='Jardines: valle colgado y cascada (jugador)',
                        desde=(x - ux * 520.0, z - uz * 520.0), objetivo=(x, z, yb + SEA), inclinacion=None))
    return out


def main(etapa='salida/etapa1.npz', out='revision', prefijo='v3'):
    t0 = time.time()
    d = np.load(etapa)
    h = d['h']
    n = h.shape[0]
    dx = N / n
    f = int(dx)
    Y0 = h + SEA
    lay = Layout(n)
    ch = d['chain']
    cy = Y0.ravel()[ch]
    cx, cz = (ch % n + 0.5) * dx, (ch // n + 0.5) * dx

    def rio_y(x, z):
        k = int(np.argmin(np.hypot(cx - x, cz - z)))
        return float(cy[k]) + 1.5

    # ------------------------------------------------ asiento a resolución de bloque
    print('ampliando a 8192²...', flush=True)
    Y1 = ampliar(Y0.astype(np.float32), f)
    print(f'  {time.time() - t0:.0f} s; asentando...', flush=True)
    out_c, Y1m = colocar(Y1, 1.0, rio_y=rio_y, busqueda=(Y0, dx, lay.dist_coast))
    print(f'  {time.time() - t0:.0f} s', flush=True)
    # superficie con el suelo propio de cada schematic (losas, canal, terrazas): bajo las
    # construcciones el terreno queda en su base y el schematic pone su suelo al pegarse
    Ys1 = Y1m.copy()
    huella = np.zeros(Ys1.shape, bool)
    edif = np.zeros(Ys1.shape, bool)
    for o in out_c:
        m = o['maps']
        zz, xx = np.nonzero(m['foot'] & (m['ground'] > -900))
        Ys1[zz + m['z0'], xx + m['x0']] = np.maximum(Ys1[zz + m['z0'], xx + m['x0']], m['ground'][zz, xx] + o['dy'])
        zz, xx = np.nonzero(m['foot'])
        huella[zz + m['z0'], xx + m['x0']] = True
        zz, xx = np.nonzero(m['built'])
        edif[zz + m['z0'], xx + m['x0']] = True
    Ym = Ys1.reshape(n, f, n, f).mean(axis=(1, 3)).astype(np.float64)
    # el cauce vuelve a bajar siempre (fuera de los Jardines)
    hm = np.ascontiguousarray(Ym - SEA, np.float64)
    bm = hm.copy()
    for k in sorted([k for k in d.files if k.startswith('cad_')], key=lambda s: int(s[4:])):
        lem.breach_chain(hm, bm, np.ascontiguousarray(d[k]), 2e-4, dx)
    Ym = hm + SEA
    oc = ocean_mask(Ym - SEA, 0.0)
    # ------------------------------------------------ agua
    Ym, WL, tipo, inf_agua = agua.superficie(d, Ym, oc)
    print('agua:', inf_agua, flush=True)
    lagos = d['lagos_jardines'] if 'lagos_jardines' in d.files else np.zeros_like(oc)
    afl = {str(k): d['afl_' + str(k)] for k in d['afluentes']} if 'afluentes' in d.files else {}
    boca = d['boca'] if 'boca' in d.files and np.any(d['boca']) else None
    # perfil del río (nivel del agua) con marcas
    k0 = int(d['k_fuente']) if 'k_fuente' in d.files else 0
    chr_ = ch[k0:]
    prof = WL.ravel()[chr_]
    prof = prof[:int(np.argmax(~np.isfinite(prof))) if (~np.isfinite(prof)).any() else prof.size]
    marcas = []
    cxr, czr = cx[k0:k0 + prof.size], cz[k0:k0 + prof.size]
    for nombre, (x, z) in [('entra a Jardines', (2260, 1950)), ('sale de Jardines', (3040, 2900)),
                           ('Vieja Velkia', (6656, 5808))]:
        marcas.append((int(np.argmin(np.hypot(cxr - x, czr - z))), nombre))
    rio = inf_agua['rio']
    notas = [
        f"Agua: el río va continuo de la fuente (Y={rio['nivel_fuente']:.0f}) al mar (Y={rio['nivel_final']:.0f}) por "
        f"{rio['celdas']} celdas: {rio['huecos']} huecos, {rio['subidas']} tramos que suben, {rio['celdas_colgadas']} celdas "
        f"con agua colgada. Cascadas del cauce: " + ', '.join(f'{c[2]:.0f} m' for c in inf_agua['cascadas_rio']) +
        f". Orillas levantadas: {inf_agua['orillas_celdas']} celdas, como mucho {inf_agua['orillas_subida_max']:.1f} m.",
        'Vieja Velkia: el río cruza la ciudad por su canal (a 6 bloques de media del eje del canal, 13 como máximo); '
        'hay construcción a ambos lados. La vega es solo corte, para que la roca no la entierre.',
        'Asiento a resolución de bloque, con talud 1:2 alrededor de cada huella; la tabla mide flotación y '
        'enterramiento en el borde, bloque a bloque.',
        'Aldea oeste: en su punto del mapa 2, sobre una ladera de ~3° preparada con la orientación del diseño '
        '(baja hacia el ESE).',
        'Gran Pirámide: escalera en la cara SUR tras la rotación; arena de sotavento en las caras E y N '
        '(viento del OSO).',
    ]
    paths, filas = generar(Y0, Ym, out_c, d['rio_xy'], afl, lagos, oc, out, boca=boca,
                           perfil=(prof, marcas), notas=notas, prefijo=prefijo, tipo=tipo,
                           Yfino=Y1m, Yfino0=Y1)
    print(f'  imágenes {time.time() - t0:.0f} s', flush=True)
    # vistas en perspectiva con las construcciones encima (techo de lo construido)
    for o in out_c:
        m = o['maps']
        zz, xx = np.nonzero(m['built'])
        Ys1[zz + m['z0'], xx + m['x0']] = np.maximum(Ys1[zz + m['z0'], xx + m['x0']], m['top'][zz, xx] + o['dy'])
    Yv = Ys1.reshape(n, f, n, f).mean(axis=(1, 3))
    hc = huella.reshape(n, f, n, f).any(axis=(1, 3))
    ec = edif.reshape(n, f, n, f).mean(axis=(1, 3)) > 0.3
    del Ys1, huella, edif
    Yvis = np.where(hc, np.maximum(Ym, Yv), Ym)
    tipo_v = tipo.copy()
    tipo_v[ec & (tipo_v == 0)] = 6
    from .validacion import generar as vistas
    pm, _ = vistas(Yvis, oc, out, prefijo=prefijo, W=800, H=450, tipo=tipo_v, WL=WL, extra=vistas_extra(d, Ym, dx))
    np.savez_compressed(f'salida/{prefijo}_asentado.npz', Y=Ym, WL=WL, tipo=tipo)
    np.save(f'salida/{prefijo}_asentado_fino.npy', np.round(Y1m).astype(np.int16))
    with open(f'salida/{prefijo}_colocacion.json', 'w') as fh:
        json.dump([{'nombre': o['nombre'], 'shift': list(o['shift']), 'dy': int(o['dy'])} for o in out_c], fh,
                  ensure_ascii=False, indent=1)
    print(f'listo en {time.time() - t0:.0f} s', flush=True)
    return paths + [pm], filas, prof, inf_agua


if __name__ == '__main__':
    pre = sys.argv[1] if len(sys.argv) > 1 else 'v3'
    p, f, prof, ia = main(prefijo=pre)
    for fl in f:
        print(fl)
    print(p)
