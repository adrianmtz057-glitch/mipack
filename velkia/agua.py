"""Agua superficial sobre el terreno: niveles del río, lagos, orillas y comprobaciones.

Reglas (las mismas que la etapa 4 aplica a resolución de bloque):
  * a lo largo del cauce, de la fuente al mar, el nivel del agua nunca sube;
  * el lecho queda siempre bajo el agua (si no, se encaja el cauce);
  * dentro de un lago el nivel es el del lago; el río que sale de él va encajado en el fondo;
  * ninguna celda de agua tiene al lado terreno más bajo que su nivel (no cuelga): donde lo
    habría, se levanta una orilla al nivel del agua.
"""
import numpy as np


def _vecinas(i, j, n):
    for a in (-1, 0, 1):
        for b in (-1, 0, 1):
            if (a or b) and 0 <= i + a < n and 0 <= j + b < n:
                yield i + a, j + b


def niveles_rio(Y, chain, lago=None, nivel_lago=None, mar=None, sea=62.0, prof=0.5):
    """Nivel del agua por celda del cauce (cotas absolutas).  Encaja el lecho donde haga falta.
    lago: máscara de lagos; nivel_lago: cota de su superficie.  mar: máscara del mar (el río
    termina al entrar).  Devuelve (Y, WL por celda del cauce hasta el mar, k_mar, encajado_max)."""
    Y = Y.copy()
    n = Y.shape[0]
    f = Y.ravel()
    lg = lago.ravel() if lago is not None else None
    mr = mar.ravel() if mar is not None else None
    wl = np.empty(chain.size)
    nivel = np.inf
    encaje = 0.0
    k_mar = chain.size
    for k, c in enumerate(chain):
        if mr is not None and mr[c]:
            k_mar = k
            break
        if lg is not None and lg[c]:
            obj = nivel_lago
        else:
            # el agua se pone al nivel del fondo del valle: si el trazado del cauce pasa junto
            # a terreno más bajo (celda gruesa desplazada del talweg), manda el más bajo
            i, j = divmod(int(c), n)
            # (sin contar el pie de un escarpe: eso es una cascada, no el fondo del valle)
            fondo = min([f[c]] + [Y[a, b] for a, b in _vecinas(i, j, n)
                                  if not (mr is not None and mr[a * n + b]) and Y[a, b] > f[c] - 12.0])
            obj = fondo + prof
        nivel = min(nivel, obj)
        nivel = max(nivel, sea)
        wl[k] = nivel
        if f[c] > nivel - 0.5:
            encaje = max(encaje, f[c] - (nivel - prof))
            f[c] = nivel - prof
    return Y, wl[:k_mar], k_mar, encaje


def orillas(Y, agua, WL, mar=None, saltar=None):
    """Levanta al nivel del agua las celdas de tierra vecinas más bajas (sin agua colgada).
    agua: máscara; WL: nivel por celda (NaN fuera).  Devuelve (Y, n_celdas, subida_max)."""
    Y = Y.copy()
    n = Y.shape[0]
    ii, jj = np.nonzero(agua)
    cnt, smax = 0, 0.0
    for i, j in zip(ii, jj):
        if saltar is not None and saltar[i, j]:
            continue                       # borde de una cascada: el agua cae, no se contiene
        w = WL[i, j]
        for a, b in _vecinas(i, j, n):
            if not agua[a, b] and Y[a, b] < w and not (mar is not None and mar[a, b]):
                smax = max(smax, w - Y[a, b])
                Y[a, b] = w
                cnt += 1
    return Y, cnt, smax


def comprobar(Y, chain_mar, wl, agua, WL, mar=None, saltar=None):
    """Continuidad del río y agua colgada.  Devuelve un dict con los resultados."""
    n = Y.shape[0]
    i, j = chain_mar // n, chain_mar % n
    saltos = np.maximum(np.abs(np.diff(i)), np.abs(np.diff(j)))
    sube = np.diff(wl) > 1e-6
    lecho_sobre = (Y.ravel()[chain_mar] > wl).sum()
    colgada = 0
    ii, jj = np.nonzero(agua)
    for a, b in zip(ii, jj):
        if saltar is not None and saltar[a, b]:
            continue
        w = WL[a, b]
        for p, q in _vecinas(a, b, n):
            if not agua[p, q] and Y[p, q] < w - 1e-6 and not (mar is not None and mar[p, q]):
                colgada += 1
                break
    return {'celdas': int(chain_mar.size), 'huecos': int((saltos > 1).sum()), 'subidas': int(sube.sum()),
            'lecho_sobre_agua': int(lecho_sobre), 'celdas_colgadas': int(colgada),
            'nivel_fuente': float(wl[0]) if wl.size else float('nan'),
            'nivel_final': float(wl[-1]) if wl.size else float('nan')}


def superficie(d, Y, mar, sea=62.0):
    """Agua y lava de la etapa 1 sobre el terreno Y (malla de d['h']).
    Devuelve (Y modificado, WL (NaN sin agua), tipo (0 nada, 1 río, 2 lago, 3 cascada, 4 lava,
    5 arroyo), informe)."""
    n = Y.shape[0]
    dx = 8192.0 / n
    WL = np.full(Y.shape, np.nan)
    tipo = np.zeros(Y.shape, np.uint8)
    inf = {}
    k0 = int(d['k_fuente']) if 'k_fuente' in d.files else 0
    lago = d['lagos_jardines'] if 'lagos_jardines' in d.files else None
    piso = float(d['jardines_piso']) + sea if 'jardines_piso' in d.files else None
    nivel_lago = piso - 0.5 if piso is not None else None
    if lago is not None:
        WL[lago] = nivel_lago
        tipo[lago] = 2
    # río principal
    ch = d['chain'][k0:]
    Y, wl, k_mar, enc = niveles_rio(Y, ch, lago, nivel_lago, mar, sea)
    chm = ch[:k_mar]
    WL.ravel()[chm] = np.where(np.isnan(WL.ravel()[chm]), wl, np.minimum(WL.ravel()[chm], wl))
    tipo.ravel()[chm] = np.where(tipo.ravel()[chm] == 2, 2, 1)
    inf['encaje_max'] = enc
    # cascadas del cauce (el nivel baja más de 3 m de una celda a la siguiente)
    salto = np.zeros(Y.shape, bool)
    kc = np.nonzero(np.diff(wl) < -3.0)[0]
    for k in kc:
        salto.ravel()[chm[k]] = True
        tipo.ravel()[chm[k]] = 3
    inf['cascadas_rio'] = [(float((chm[k] % n + 0.5) * dx), float((chm[k] // n + 0.5) * dx),
                            float(wl[k] - wl[k + 1])) for k in kc]
    # afluentes (cadenas 2.. de la etapa 1: Río Salado y cañón lateral)
    for k in sorted([k for k in d.files if k.startswith('cad_')], key=lambda s: int(s[4:]))[2:]:
        c = d[k][int(d['kf_' + k]) if 'kf_' + k in d.files else 0:]
        Y, w2, km2, _ = niveles_rio(Y, c, None, None, mar, sea)
        cc = c[:km2]
        libre = np.isnan(WL.ravel()[cc])
        WL.ravel()[cc[libre]] = w2[libre]
        tipo.ravel()[cc[libre]] = 1
    # cascadas de los valles colgados y sus arroyos
    if 'cascadas' in d.files:
        for x, z, yb, yp, ux, uz in d['cascadas']:
            for t in np.arange(-90.0, 0.0, dx / 2):          # cara de la pared bajo el borde
                i, j = int((z + uz * t) / dx), int((x + ux * t) / dx)
                if 0 <= i < n and 0 <= j < n and tipo[i, j] == 0:
                    tipo[i, j] = 3
            for t in np.arange(0.0, 380.0, dx / 2):          # arroyo del valle colgado
                i, j = int((z + uz * t) / dx), int((x + ux * t) / dx)
                if 0 <= i < n and 0 <= j < n and tipo[i, j] == 0:
                    tipo[i, j] = 5
    if 'lava_canal' in d.files:
        lv = d['lava_canal'] | d['lago_lava']
        tipo[lv] = 4
    agua = np.isfinite(WL) & ~mar
    Y, nb, smax = orillas(Y, agua, WL, mar, salto)
    inf['orillas_celdas'] = nb
    inf['orillas_subida_max'] = smax
    inf['rio'] = comprobar(Y, chm, wl, agua, WL, mar, salto)
    return Y, WL, tipo, inf


COLORES = {1: (45, 105, 210), 2: (40, 95, 200), 3: (225, 235, 245), 4: (235, 85, 20), 5: (70, 140, 230),
           6: (172, 162, 150)}   # 6: construcción


def pintar(rgb, tipo):
    """Pinta agua, cascadas y lava sobre una imagen RGB (H, W, 3) de la malla del terreno."""
    out = np.asarray(rgb).astype(np.float32).copy()
    for t, c in COLORES.items():
        m = tipo == t
        out[m] = out[m] * 0.25 + np.array(c, np.float32) * 0.75
    return out
