"""Campos de forzamiento: levantamiento por zona y fase, precipitación, topografía inicial."""
import numpy as np

from .layout import poi_blocks, RESERVADOS, px2b, jardines_r
from .noise import spectral_noise, blur


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Forcing:
    def __init__(self, lay, geo, seed=31):
        n = lay.n
        z = lay.zonas
        zz, xx = lay.coords()
        self.lay = lay
        dcres, hcres = lay.cresta
        land = lay.land_soft
        nz = spectral_noise((n, n), 2.2, seed)
        # ---------------------------------------------------------- levantamiento (m/a)
        U1 = np.zeros((n, n), np.float32)
        crest = hcres * np.exp(-(dcres / 1500.0) ** 2)
        U1 += z['cordillera'] * (0.20e-3 + 1.25e-3 * crest)
        U1 += z['corrompidas'] * (1.30e-3 * np.exp(0.25 * nz))
        U1 += z['jardines'] * 0.06e-3
        U1 += z['oeste'] * 0.16e-3 * np.exp(0.35 * nz)      # colinas de desierto rocoso
        U1 += z['este'] * 0.07e-3                           # costa rocosa baja
        U1 += z['volcanica'] * 0.05e-3                      # el volcán se construye aparte
        U1 += z['canones'] * 0.10e-3
        U1 += z['desierto'] * 0.04e-3                       # deja en pie peñones de roca dura
        U1 += z['dunas'] * 0.0
        U1 += z['salar'] * 0.0
        # anillo de roca alrededor de los Jardines (las paredes del valle glaciar)
        rj = jardines_r(xx, zz)
        U1 += 0.32e-3 * np.exp(-((rj - 1.18) / 0.22) ** 2)
        # promontorio de la Torre cerca de la costa este
        tx, tz = poi_blocks('torre_llama_eterna')
        U1 += 0.22e-3 * np.exp(-(((xx - tx) ** 2 + (zz - tz) ** 2) / 330.0 ** 2) ** 1.5)
        # sitios reservados con relieve propio
        for nombre, (pxy, rad, tipo) in RESERVADOS.items():
            bx, bz = px2b(*pxy)
            g = np.exp(-(((xx - bx) ** 2 + (zz - bz) ** 2) / rad ** 2) ** 1.5)
            if tipo == 'promontorio':
                U1 += 0.12e-3 * g
            elif tipo == 'colina':
                U1 += 0.06e-3 * g
            elif tipo == 'meseta':
                U1 += 0.05e-3 * g
        U1 *= smoothstep(lay.dist_coast, -100, 500)
        self.U_orogeny = U1.astype(np.float64)
        # fase de levantamiento de la meseta (cañones) y abombamiento del este
        U2 = np.zeros((n, n), np.float32)
        U2 += z['canones'] * 0.20e-3
        U2 += z['oeste'] * 0.02e-3
        U2 *= smoothstep(lay.dist_coast, -100, 700)
        # cuenca cerrada del salar (hundimiento tectónico, tipo pull-apart)
        sx, sz = poi_blocks('bioma_de_sales')
        U2 += -0.06e-3 * np.exp(-((xx - sx) ** 2 + (zz - sz) ** 2) / 430.0 ** 2)
        # Cuarto de Bashi: depresión romboidal de bordes suaves (hundimiento por disolución de
        # evaporitas a lo largo de dos familias de fracturas a 45°)
        (bpx, rad, _) = RESERVADOS['cuarto_de_bashi']
        bx, bz = px2b(*bpx)
        rombo = (np.abs(xx - bx) ** 1.3 + np.abs(zz - bz) ** 1.3) ** (1 / 1.3) / rad
        U2 += -0.035e-3 * np.exp(-rombo ** 3)
        self.U_plateau = U2.astype(np.float64)
        # ---------------------------------------------------------- precipitación (m/a)
        P = (z['cordillera'] * 1.2 + z['corrompidas'] * 0.7 + z['jardines'] * 1.0 +
             z['oeste'] * 0.35 + z['este'] * 0.20 + z['volcanica'] * 0.35 +
             z['canones'] * 0.12 + z['desierto'] * 0.06 + z['dunas'] * 0.04 + z['salar'] * 0.05)
        self.P_arid = blur(P, 200.0 / lay.dx).astype(np.float64)
        # clima pluvial antiguo (desierto verde): más lluvia en las zonas hoy áridas
        Pp = P + 0.22 * (z['desierto'] + z['dunas'] + z['salar']) + 0.10 * (z['canones'] + z['este'])
        self.P_pluvial = blur(Pp, 200.0 / lay.dx).astype(np.float64)
        self.P_base = self.P_pluvial
        # ---------------------------------------------------------- topografía inicial
        d = lay.dist_coast
        h = np.where(d > 0, 4.0 + 26.0 * (1 - np.exp(-d / 1500.0)), 0.0)
        h += 3.0 * spectral_noise((n, n), 2.0, seed + 1) * (d > 0)
        sea = -2.0 - 28.0 * (1 - np.exp(np.minimum(d, 0) / 300.0)) - 45.0 * smoothstep(-d, 350, 1100)
        h = np.where(d > 0, h, sea)
        self.h0 = h.astype(np.float64)

    def precip(self, h):
        """Precipitación orográfica: aumenta con la altura en zonas húmedas."""
        oro = 1.0 + np.clip(h, 0, None) / 250.0
        return self.P_base * oro
