"""Bucle del modelo de evolución del paisaje (fluvial + laderas) para una resolución dada."""
import time

import numpy as np

from . import lem


def ocean_mask(h, sl):
    """Celdas bajo el nivel del mar conectadas con el borde del mapa (el mar abierto)."""
    from scipy import ndimage as ndi
    below = h < sl
    lab, n = ndi.label(below)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border > 0]
    return np.isin(lab, border)


class LEMState:
    """Estado: superficie h (relativa al mar), roca b, malla de lado n y paso dx."""

    def __init__(self, h, b, dx):
        self.h = np.ascontiguousarray(h, np.float64)
        self.b = np.ascontiguousarray(b, np.float64)
        self.dx = float(dx)
        self.n = h.shape[0]
        self.Q = None
        self.rec = None
        self.stack = None
        self.filled = None
        self.qs_sea = None


def run(state, geo, forcing, t_years, dt, U_func, sea_level=0.0, K0=8e-5, Ks_mult=2.0,
        m=0.45, Gv=0.6, D_func=None, sinks=None, fixed_rec=None, fixed_h=None,
        log_every=10, label='', callback=None, P_floor_transport=0.3, baseflow=None,
        G_arr=None, Kmult_arr=None, breach=None):
    """Integra el LEM durante t_years con paso dt.

    U_func(t) -> array de levantamiento (m/a)
    D_func(state) -> array de difusividad (m2/a)
    sinks: bool array de sumideros internos (salar) que actúan como desagüe
    fixed_rec: receptores forzados (río antecedente) o None
    fixed_h: máscara de celdas con cota fija (no evolucionan) o None
    """
    n = state.n
    dx = state.dx
    area = dx * dx
    nsteps = int(round(t_years / dt))
    fr = np.full((n, n), -1, np.int64) if fixed_rec is None else fixed_rec
    t0 = time.time()
    for step in range(nsteps):
        t = step * dt
        sl = sea_level(t) if callable(sea_level) else sea_level
        outlet = ocean_mask(state.h, sl)
        if sinks is not None:
            outlet = outlet | sinks
        seed = outlet if fixed_rec is None else (outlet | (fr >= 0))
        rec, stack, filled = lem.route_flow(state.h, seed, 1e-4, fr)
        if fixed_rec is not None:
            stack = lem.fix_stack(rec, n * n)
        P = forcing.precip(state.h - sl)
        wq = (P * area).ravel()
        wd = (np.maximum(P, P_floor_transport) * area).ravel()
        if baseflow is not None:            # caudal de base (deshielo) inyectado en la cabecera
            wq = wq.copy()
            wd = wd.copy()
            wq[baseflow[0]] += baseflow[1]
            wd[baseflow[0]] += baseflow[1]
        Q = lem.accumulate(stack, rec, wq)
        Qd = lem.accumulate(stack, rec, wd)
        L = lem.rec_dist(rec, n, dx)
        U = U_func(t).ravel()
        Kb = geo.kb(state.b, K0)
        if Kmult_arr is not None:
            Kb = Kb * Kmult_arr
        lake = (filled.ravel() > state.h.ravel() + 1e-3) & ~seed.ravel()
        G = np.full(n * n, Gv) if G_arr is None else G_arr
        hf = state.h.ravel().copy()
        bf = state.b.ravel().copy()
        qs = lem.spl_ed(hf, bf, stack, rec, L, Q, Kb, Ks_mult, m, G, U, dt, lake,
                        outlet.ravel(), area, 4, sl, 0.0, filled.ravel(), Qd)
        h = hf.reshape(n, n)
        b = bf.reshape(n, n)
        # celdas de mar: sin levantamiento fluvial; el sedimento se reparte luego
        h = np.where(outlet & ~(sinks if sinks is not None else False), state.h, h)
        b = np.minimum(b, h)
        if D_func is not None:
            D = D_func(state)
            fixed = outlet.copy()
            if fixed_h is not None:
                fixed |= fixed_h
            h2 = lem.diffuse(h, D, dt, dx, fixed)
            # la difusión mueve regolito: lo que baja de la roca se vuelve sedimento
            b = np.minimum(b, h2)
            h = h2
        if breach is not None:
            h = np.ascontiguousarray(h)
            b = np.ascontiguousarray(b)
            lem.breach_chain(h, b, breach, 2e-4, dx)
        if fixed_h is not None:
            h = np.where(fixed_h, state.h, h)
            b = np.where(fixed_h, state.b, b)
        state.h, state.b = h, b
        state.Q = Q.reshape(n, n)
        state.rec, state.stack, state.filled = rec, stack, filled
        state.qs_sea = qs
        if log_every and (step % log_every == 0 or step == nsteps - 1):
            land = h > sl
            print(f'  [{label}] paso {step + 1}/{nsteps} t={t / 1e3:.0f} ka  '
                  f'hmax={h.max():.0f} hmed_tierra={np.median(h[land]) if land.any() else 0:.1f} '
                  f'tierra={land.mean():.3f}  ({time.time() - t0:.0f} s)', flush=True)
        if callback is not None:
            callback(step, state)
    return state
