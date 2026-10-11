"""Asiento de las construcciones en el relieve: corte y relleno con borde suave.

Dentro de la huella el terreno se lleva a la cota objetivo de cada columna.  Fuera, la cota
del borde se extiende hacia afuera (celda de la huella más cercana) y se mezcla con smoothstep
con el terreno natural en una banda cuyo ancho depende del desnivel en el borde más cercano y
de la pendiente admisible: terraplén si hay que rellenar, desmonte si hay que cortar.  Más
allá de la banda el terreno no se toca.

Unidades: cotas y distancias en bloques.  h es una malla de celdas de dx bloques; la celda
(i, j) cubre z en [i·dx, (i+1)·dx) y x en [j·dx, (j+1)·dx), como en colocar._muestrear.
"""
import numpy as np
from scipy import ndimage as ndi
from scipy import sparse
from scipy.sparse.linalg import spsolve

K_SMOOTH = 1.5        # pendiente máxima de smoothstep (en t = 1/2): ancho = 1,5·|desnivel|/pendiente
LIPSCHITZ = 0.25      # variación lateral máxima del ancho de banda (bloques por bloque)
SOBREPASO = 1.7       # mezclar una cota plana con una ladera de pendiente g da hasta ~1,69·g
ENSANCHE = 1.25       # ensanche por iteración de los bordes cuya banda excede la pendiente
ENSANCHE_MAX = 4.0    # ensanche total máximo respecto del ancho inicial
ANCHO_MAX = 384.0     # tope absoluto del ancho de banda (bloques)
ITER_MAX = 10
TOL = 0.03


# --------------------------------------------------------------------- objetivos
def objetivo_plano(foot, y):
    """Cota objetivo constante y en toda la huella (NaN fuera)."""
    return np.where(foot, float(y), np.nan)


def objetivo_desde_sitio(maps, dy, modo='suelo'):
    """Cota objetivo por columna a partir de Sitio.maps() desplazado dy.
    'suelo': techo del terreno natural del schematic (construcciones diseñadas en ladera);
    las columnas sin terreno natural se interpolan (membrana armónica).
    'base': un bloque bajo la base de cada columna (construcciones de base plana)."""
    foot = maps['foot']
    if modo == 'base':
        return np.where(foot, maps['bottom'] - 1.0 + dy, np.nan)
    if modo != 'suelo':
        raise ValueError(f'modo desconocido: {modo}')
    g = maps['ground'].astype(np.float64)
    ok = foot & (g > -900)
    if not ok.any():
        return objetivo_desde_sitio(maps, dy, 'base')
    t = np.where(ok, g + dy, np.nan)
    hueco = foot & ~ok
    if hueco.any():
        t[hueco] = _rellenar_huecos(t, ok, hueco)
    return t


def _rellenar_huecos(t, ok, hueco):
    """Valores armónicos en 'hueco' con t fijo en 'ok' y flujo nulo hacia el resto."""
    _, (ii, jj) = ndi.distance_transform_edt(~ok, return_indices=True)
    ini = t[ii, jj][hueco]
    zz, xx = np.nonzero(hueco)
    k = zz.size
    idx = np.full(t.shape, -1, np.int64)
    idx[zz, xx] = np.arange(k)
    eps = 1e-6                      # ancla débil al vecino más cercano (huecos aislados)
    diag = np.full(k, eps)
    b = eps * ini
    filas, cols = [], []
    L, W = t.shape
    for dz, dxx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nz, nx = zz + dz, xx + dxx
        v = (nz >= 0) & (nz < L) & (nx >= 0) & (nx < W)
        nzv, nxv = np.where(v, nz, 0), np.where(v, nx, 0)
        es_h = v & hueco[nzv, nxv]
        es_ok = v & ok[nzv, nxv]
        diag += es_h | es_ok
        b += np.where(es_ok, t[nzv, nxv], 0.0)
        filas.append(np.nonzero(es_h)[0])
        cols.append(idx[nzv, nxv][es_h])
    filas, cols = np.concatenate(filas), np.concatenate(cols)
    A = sparse.coo_matrix((np.r_[diag, -np.ones(filas.size)],
                           (np.r_[np.arange(k), filas], np.r_[np.arange(k), cols])), shape=(k, k))
    return spsolve(A.tocsc(), b)


def _extension_continua(T, R, dist, dx):
    """Extiende T (definido en R) fuera de R sin discontinuidades."""
    W = R.astype(np.float64)
    V = np.where(R, T, 0.0)
    escalas = [max(1.0, 3.0 / dx), max(2.0, 12.0 / dx), max(4.0, 48.0 / dx)]   # sigmas en celdas
    campos = []
    for sg in escalas:
        num = ndi.gaussian_filter(V, sg, mode='nearest')
        den = ndi.gaussian_filter(W, sg, mode='nearest')
        campos.append(np.where(den > 1e-6, num / np.maximum(den, 1e-12), np.nan))
    # donde una escala fina no alcanza (den ~ 0) usar la siguiente
    for k in range(len(campos) - 2, -1, -1):
        campos[k] = np.where(np.isfinite(campos[k]), campos[k], campos[k + 1])
    lejos = campos[-1]
    lejos = np.where(np.isfinite(lejos), lejos, np.nanmedian(T[R]))
    c0 = np.where(np.isfinite(campos[0]), campos[0], lejos)
    c1 = np.where(np.isfinite(campos[1]), campos[1], lejos)
    d = dist / dx
    u1 = np.clip(d / 6.0, 0, 1)
    u2 = np.clip((d - 6.0) / 24.0, 0, 1)
    Te = c0 * (1 - u1) + c1 * u1
    Te = Te * (1 - u2) + lejos * u2
    return np.where(R, T, Te)


# --------------------------------------------------------------------- utilidades
def _rasterizar(foot, target, x0, z0, dx, shape):
    """Huella y objetivo en la malla de h.  Una celda entra si contiene alguna columna de la
    huella con objetivo (así ninguna columna queda sobre la banda) y toma la mediana de esos
    objetivos.  Devuelve (i0, j0, req, tgt) sobre la caja de celdas de la huella, o None."""
    ok = foot & np.isfinite(target)
    zz, xx = np.nonzero(ok)
    ci = ((z0 + zz) // dx).astype(np.int64)
    cj = ((x0 + xx) // dx).astype(np.int64)
    dentro = (ci >= 0) & (ci < shape[0]) & (cj >= 0) & (cj < shape[1])
    if not dentro.any():
        return None
    v = target[zz, xx][dentro].astype(np.float64)
    ci, cj = ci[dentro], cj[dentro]
    i0, j0 = int(ci.min()), int(cj.min())
    L, W = int(ci.max()) - i0 + 1, int(cj.max()) - j0 + 1
    key = (ci - i0) * W + (cj - j0)
    orden = np.lexsort((v, key))
    key, v = key[orden], v[orden]
    ini = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    cnt = np.diff(np.r_[ini, key.size])
    req = np.zeros(L * W, bool)
    tgt = np.full(L * W, np.nan)
    req[key[ini]] = True
    tgt[key[ini]] = 0.5 * (v[ini + (cnt - 1) // 2] + v[ini + cnt // 2])
    return i0, j0, req.reshape(L, W), tgt.reshape(L, W)


def _envolvente(F, dx):
    """Campo >= F cuya variación es <= LIPSCHITZ bloques por bloque (envolvente de conos).
    Se calcula en una malla de ~4 bloques y se interpola."""
    f = max(1, int(round(4.0 / dx)))
    L, W = F.shape
    Lc, Wc = -(-L // f), -(-W // f)
    G = np.full((Lc * f, Wc * f), -np.inf)
    G[:L, :W] = F
    G = G.reshape(Lc, f, Wc, f).max(axis=(1, 3))
    paso = dx * f
    r2 = np.sqrt(2.0)
    est = -LIPSCHITZ * paso * np.array([[r2, 1, r2], [1, 0, 1], [r2, 1, r2]])
    for _ in range(4096):
        Gn = ndi.grey_dilation(G, structure=est, mode='nearest')
        if np.all(Gn <= G + 1e-9):
            break
        G = Gn
    if f == 1:
        return G
    ci = (np.arange(L) + 0.5) / f - 0.5
    cj = (np.arange(W) + 0.5) / f - 0.5
    CI, CJ = np.meshgrid(ci, cj, indexing='ij')
    return np.maximum(ndi.map_coordinates(G, [CI, CJ], order=1, mode='nearest'), F)


def _pendiente(a, dx):
    gz, gx = np.gradient(a, dx)
    return np.hypot(gz, gx)


def _informe_vacio():
    return {'volumen_corte': 0.0, 'volumen_relleno': 0.0, 'corte_max': 0.0, 'relleno_max': 0.0,
            'ancho_borde_max': 0.0, 'desajuste_borde_antes': 0.0, 'desajuste_borde_despues': 0.0}


# --------------------------------------------------------------------- asiento
def asentar(h, dx, foot, x0, z0, target, slope_fill=0.70, slope_cut=1.2, border_min=6.0,
            return_report=True):
    """Corte y relleno de h (cotas absolutas, malla de dx bloques) para asentar una huella.

    foot, target: huella (bool) y cota de suelo requerida (NaN = sin requisito) por columna,
    en bloques, con esquina (x0, z0).  Dentro de la huella h queda en el objetivo; fuera, banda
    de ancho max(border_min, 1,5·|d|/p) según el desnivel d en el borde más cercano, con
    p = slope_fill si hay que rellenar o slope_cut si hay que cortar (el 1,5 es la pendiente
    máxima de smoothstep: así la pendiente local, no solo la media, no pasa de p).  Donde la
    banda aún excede la pendiente (laderas, ruido) se ensancha iterativamente.  Una pendiente
    <= 0 desactiva esa operación (slope_fill=0: solo corte).
    Devuelve (h_nuevo, informe), o solo h_nuevo si return_report es False.  informe:
    volumen_corte, volumen_relleno (bloques³), corte_max, relleno_max, ancho_borde_max,
    desajuste_borde_antes/despues (máx |terreno - objetivo| en el borde); además
    pendiente_max_banda, exceso_pendiente (pendiente / admisible; <= 1 cumple),
    dist_modificada_max, iteraciones y ventana (a0, a1, b0, b1) en celdas."""
    out = h.copy()
    ras = _rasterizar(foot, target, x0, z0, dx, h.shape)
    if ras is None or (slope_fill <= 0 and slope_cut <= 0):
        return (out, _informe_vacio()) if return_report else out
    i0, j0, req, tgt = ras
    pf = slope_fill if slope_fill > 0 else slope_cut
    pc = slope_cut if slope_cut > 0 else slope_fill
    n, m = h.shape
    # ventana de trabajo: caja de la huella más la banda más ancha posible
    hb = h[i0:i0 + req.shape[0], j0:j0 + req.shape[1]].astype(np.float64)
    borde = req & ~ndi.binary_erosion(req, border_value=0)
    d = (tgt - hb)[borde]
    w0 = max(border_min, K_SMOOTH * float(np.max(np.abs(d) / np.where(d > 0, pf, pc))))
    M = int(np.ceil(min(ANCHO_MAX, ENSANCHE_MAX * w0) / dx)) + 2
    a0, a1 = max(i0 - M, 0), min(i0 + req.shape[0] + M, n)
    b0, b1 = max(j0 - M, 0), min(j0 + req.shape[1] + M, m)
    H = h[a0:a1, b0:b1].astype(np.float64)
    R = np.zeros(H.shape, bool)
    T = np.full(H.shape, np.nan)
    sl = (slice(i0 - a0, i0 - a0 + req.shape[0]), slice(j0 - b0, j0 - b0 + req.shape[1]))
    R[sl], T[sl] = req, tgt
    # objetivo extendido hacia fuera de forma CONTINUA: convolución normalizada a tres escalas,
    # mezcladas según la distancia a la huella (el vecino de borde más cercano daría saltos en
    # las fronteras de Voronoi cuando el objetivo no es plano: patios, muescas, terrazas)
    dist, (ii, jj) = ndi.distance_transform_edt(~R, sampling=dx, return_indices=True)
    Te = _extension_continua(T, R, dist, dx)
    d0 = T[ii, jj] - H[ii, jj]
    p = np.where(d0 > 0, pf, pc)
    borde = R & ~ndi.binary_erosion(R, border_value=0)
    w_e = np.zeros(H.shape)
    w_e[borde] = np.clip(K_SMOOTH * np.abs(d0[borde]) / p[borde], border_min, ANCHO_MAX)
    tope = np.minimum(ENSANCHE_MAX * w_e, ANCHO_MAX)
    # pendiente admisible: la pedida, o la del objetivo o del terreno natural si ya son mayores
    # la pendiente propia del objetivo se mide DENTRO de la huella y se lleva al exterior por el
    # borde más cercano (no con la de Te, que ocultaría cualquier escalón de la banda)
    pt = np.where(R, _pendiente(np.where(R, T, np.nan), dx), 0.0)
    pt = np.nan_to_num(ndi.maximum_filter(np.nan_to_num(pt), size=3))
    adm = np.maximum(p, pt[ii, jj])
    adm = np.maximum(adm, SOBREPASO * ndi.maximum_filter(_pendiente(H, dx), size=3)) * (1 + TOL)
    fuera = ~R
    for it in range(ITER_MAX):
        Wb = np.maximum(_envolvente(w_e[ii, jj], dx), border_min)
        t = np.clip(dist / Wb, 0.0, 1.0)
        s = t * t * (3.0 - 2.0 * t)
        new = np.where(R, T, Te + (H - Te) * s)
        new = np.where(fuera & (dist >= Wb), H, new)
        if slope_fill <= 0:
            new = np.minimum(new, H)
        if slope_cut <= 0:
            new = np.maximum(new, H)
        zona = fuera & (dist < Wb + 1.5 * dx)
        G = _pendiente(new, dx)
        viol = zona & (G > adm)
        if not viol.any() or it == ITER_MAX - 1:
            break
        marca = np.zeros(H.shape, bool)
        marca[ii[viol], jj[viol]] = True
        crece = marca & (w_e < tope)
        if not crece.any():
            break
        w_e[crece] = np.minimum(w_e[crece] * ENSANCHE, tope[crece])
    out[a0:a1, b0:b1] = np.round(new) if np.issubdtype(h.dtype, np.integer) else new
    if not return_report:
        return out
    dif = new - H
    mod = fuera & (np.abs(dif) > 1e-9)
    banda = fuera & (dist < Wb)
    inf = {
        'volumen_corte': float(np.maximum(-dif, 0).sum() * dx * dx),
        'volumen_relleno': float(np.maximum(dif, 0).sum() * dx * dx),
        'corte_max': float(max(-dif.min(), 0.0)),
        'relleno_max': float(max(dif.max(), 0.0)),
        'ancho_borde_max': float(Wb[banda].max()) if banda.any() else float(border_min),
        'desajuste_borde_antes': evaluar_asiento(h, dx, foot, x0, z0, target)['desajuste_max'],
        'desajuste_borde_despues': evaluar_asiento(out, dx, foot, x0, z0, target)['desajuste_max'],
        'pendiente_max_banda': float(G[zona].max()) if zona.any() else 0.0,
        'exceso_pendiente': float((G / adm)[zona].max()) if zona.any() else 0.0,
        'dist_modificada_max': float(dist[mod].max()) if mod.any() else 0.0,
        'iteraciones': it + 1,
        'ventana': (int(a0), int(a1), int(b0), int(b1)),
    }
    return out, inf


def evaluar_asiento(h, dx, foot, x0, z0, target):
    """Flotación y enterramiento en el borde de la huella (bloques).
    Compara el terreno bajo cada columna del borde (con algún vecino fuera de la huella) con
    su cota objetivo: terreno más bajo, la construcción flota; más alto, queda enterrada."""
    borde = foot & ~ndi.binary_erosion(foot, border_value=0) & np.isfinite(target)
    zz, xx = np.nonzero(borde)
    ci = ((z0 + zz) // dx).astype(np.int64)
    cj = ((x0 + xx) // dx).astype(np.int64)
    v = (ci >= 0) & (ci < h.shape[0]) & (cj >= 0) & (cj < h.shape[1])
    if not v.any():
        return {'n_borde': 0, 'desajuste_max': 0.0, 'desajuste_medio': 0.0, 'flotacion_max': 0.0,
                'flotacion_media': 0.0, 'enterramiento_max': 0.0, 'enterramiento_media': 0.0,
                'frac_flotando': 0.0, 'frac_enterrado': 0.0}
    dif = h[ci[v], cj[v]].astype(np.float64) - target[zz[v], xx[v]]
    flo, ent = np.maximum(-dif, 0), np.maximum(dif, 0)
    return {
        'n_borde': int(v.sum()),
        'desajuste_max': float(np.abs(dif).max()),
        'desajuste_medio': float(np.abs(dif).mean()),
        'flotacion_max': float(flo.max()),
        'flotacion_media': float(flo.mean()),
        'enterramiento_max': float(ent.max()),
        'enterramiento_media': float(ent.mean()),
        'frac_flotando': float((dif < -0.5).mean()),
        'frac_enterrado': float((dif > 0.5).mean()),
    }
