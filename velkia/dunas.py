"""Mar de dunas: modelo de losas de Werner (1995) con lecho no erosionable.

Reglas (viento hacia +x en el marco rotado):
  1. Se elige una celda al azar con arena que no esté en sombra; se levanta una losa.
  2. La losa salta L celdas a sotavento; se deposita con probabilidad ps (si hay arena) o
     pns (si no hay), o siempre si cae en zona de sombra (15° detrás de una cresta).
  3. Avalanchas: si la pendiente supera el ángulo de reposo (~33°), la arena se reparte.
  4. Los cauces actúan como sumidero (la arena que cae al río se la lleva el agua) y el borde
     de barlovento aporta arena (deflación de la llanura del río y del salar).
Con aporte alto salen dunas transversales; con aporte bajo, barjanes; con viento variable,
crestas sinuosas.
"""
import numpy as np
from numba import njit
from scipy import ndimage as ndi


@njit(cache=True)
def _in_shadow(s, bed, i, j, tan_sh, kmax):
    ny, nx = s.shape
    hz = bed[i, j] + s[i, j]
    for k in range(1, kmax):
        jj = j - k
        if jj < 0:
            break
        if bed[i, jj] + s[i, jj] - hz > k * tan_sh:
            return True
    return False


@njit(cache=True)
def _avalanche(s, bed, i, j, rep, fixed):
    """Relaja pendientes > rep (en losas por celda) alrededor de (i, j)."""
    ny, nx = s.shape
    stack_i = np.empty(4096, np.int64)
    stack_j = np.empty(4096, np.int64)
    top = 0
    stack_i[0] = i
    stack_j[0] = j
    top = 1
    it = 0
    while top > 0 and it < 20000:
        it += 1
        top -= 1
        ci = stack_i[top]
        cj = stack_j[top]
        if s[ci, cj] <= 0:
            continue
        hc = bed[ci, cj] + s[ci, cj]
        best = 0.0
        bi, bj = -1, -1
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ii = (ci + di) % ny
                jj = cj + dj
                if jj < 0 or jj >= nx:
                    continue
                d = 1.414 if (di != 0 and dj != 0) else 1.0
                g = (hc - bed[ii, jj] - s[ii, jj]) / d
                if g > best:
                    best = g
                    bi, bj = ii, jj
        if best > rep and bi >= 0:
            s[ci, cj] -= 1
            if not fixed[bi, bj]:
                s[bi, bj] += 1
            if top + 2 < 4096:
                stack_i[top] = bi
                stack_j[top] = bj
                top += 1
                stack_i[top] = ci
                stack_j[top] = cj
                top += 1


@njit(cache=True)
def werner(s, bed, sinks, sweeps, L, ps, pns, tan_sh, rep, supply, seed):
    """s: losas de arena (int32), bed: lecho en losas (float). Periódico en filas (y)."""
    np.random.seed(seed)
    ny, nx = s.shape
    n = ny * nx
    kmax = 60
    for sw in range(sweeps):
        # aporte por el borde de barlovento
        for i in range(ny):
            if np.random.random() < supply:
                s[i, 0] += 1
        for _ in range(n):
            i = np.random.randint(ny)
            j = np.random.randint(nx)
            if s[i, j] <= 0 or sinks[i, j]:
                continue
            if _in_shadow(s, bed, i, j, tan_sh, kmax):
                continue
            s[i, j] -= 1
            _avalanche(s, bed, i, j, rep, sinks)   # reajuste del hueco dejado
            jj = j
            while True:
                jj += L
                if jj >= nx:
                    break          # sale por sotavento
                if sinks[i, jj]:
                    break          # cae al río
                if _in_shadow(s, bed, i, jj, tan_sh, kmax):
                    s[i, jj] += 1
                    _avalanche(s, bed, i, jj, rep, sinks)
                    break
                p = ps if s[i, jj] > 0 else pns
                if np.random.random() < p:
                    s[i, jj] += 1
                    _avalanche(s, bed, i, jj, rep, sinks)
                    break
    return s


def simulate_dunes(bed_m, sand_m, sinks, cell=2.0, slab=0.5, wind_deg=12.0, sweeps=900, seed=9,
                   supply=0.15, log=True):
    """Corre el modelo sobre una ventana.

    bed_m: lecho (m), sand_m: espesor inicial de arena (m), sinks: celdas sumidero (ríos/mar)
    wind_deg: dirección HACIA la que sopla, en grados desde el este (+x), positivo hacia el sur.
    Devuelve el espesor final de arena (m) sobre la malla original.
    """
    # rotar para que el viento sea +x
    rot = lambda a, order: ndi.rotate(a, wind_deg, reshape=True, order=order, mode='nearest')
    b = rot(bed_m, 1) / slab
    s0 = np.maximum(rot(sand_m, 1), 0) / slab
    sk = rot(sinks.astype(np.float32), 0) > 0.5
    valid = rot(np.ones_like(bed_m), 0) > 0.5
    sk |= ~valid
    s = np.round(s0).astype(np.int32)
    s[sk] = 0
    tan_sh = np.tan(np.deg2rad(15.0)) * cell / slab
    rep = np.tan(np.deg2rad(33.0)) * cell / slab
    chunk = 50
    done = 0
    while done < sweeps:
        k = min(chunk, sweeps - done)
        s = werner(s, b.astype(np.float64), sk, k, 5, 0.6, 0.4, tan_sh, rep, supply, seed + done)
        done += k
        if log:
            print(f'  [dunas] barrido {done}/{sweeps}  arena media={s[~sk].mean() * slab:.2f} m  '
                  f'máx={s.max() * slab:.1f} m', flush=True)
    out = ndi.rotate(s.astype(np.float32) * slab, -wind_deg, reshape=True, order=1, mode='constant')
    # recortar al tamaño original (centrado)
    oy = (out.shape[0] - bed_m.shape[0]) // 2
    ox = (out.shape[1] - bed_m.shape[1]) // 2
    return out[oy:oy + bed_m.shape[0], ox:ox + bed_m.shape[1]]
