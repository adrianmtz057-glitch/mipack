"""Mapa geológico: provincias, dureza base y estratos con espesores irregulares.

La erodabilidad de la roca en una celda es  Kb = K0 * Kzona(x,z) * F_prov(zeta)
donde zeta es la cota estratigráfica (cota de la roca corregida por buzamiento y por
variación lateral de espesor) y F_prov es la tabla de dureza de la columna estratigráfica
de la provincia.  Capas duras (F < 1) generan acantilados, mesas y cascadas; capas blandas,
laderas suaves.  Las mismas capas se usan después para elegir los bloques (colores).
"""
import numpy as np
from numba import njit, prange

from .noise import spectral_noise, resize, blur

# provincias
GRANITO, METAMORFICO, ESTRATOS, BASALTO, SEDIMENTOS, EVAPORITAS, CORROMPIDO = range(7)
PROV_NAMES = ['granito', 'metamorfico', 'estratos', 'basalto', 'sedimentos', 'evaporitas', 'corrompido']

ZMIN, ZMAX, ZRES = -400.0, 800.0, 0.25          # rango de la tabla (m) y resolución
NT = int((ZMAX - ZMIN) / ZRES)

# Columna estratigráfica de la meseta (de abajo a arriba): (espesor m, dureza F, material)
# F < 1: dura.  Materiales: claves que materials.py traduce a bloques.
COLUMNA_MESETA = [
    (400, 0.30, 'basamento'),      # granito/esquisto bajo la discordancia
    (16, 2.2, 'lutita_roja'),
    (9, 0.45, 'arenisca_roja'),
    (22, 1.9, 'limolita'),
    (7, 0.35, 'caliza'),
    (14, 2.0, 'lutita_gris'),
    (12, 0.40, 'arenisca_blanca'),
    (18, 1.7, 'lutita_roja'),
    (6, 0.50, 'arenisca_amarilla'),
    (20, 1.6, 'limolita'),
    (15, 0.25, 'arenisca_crema'),  # cornisa principal (caprock)
    (10, 1.8, 'lutita_parda'),
    (11, 0.35, 'caliza'),
    (25, 1.5, 'lutita_roja'),
    (14, 0.30, 'arenisca_crema'),
    (400, 1.4, 'lutita_parda'),
]
BASE_MESETA = 30.0     # cota (sobre el mar) de la discordancia en el centro de la meseta


def _table_from_column(column, base, rng, jitter=0.15):
    """Devuelve (F[NT], idx_material[NT]) a lo largo de la cota estratigráfica."""
    F = np.ones(NT, np.float32)
    mat = np.zeros(NT, np.int16)
    z = base - column[0][0]
    for k, (th, f, _) in enumerate(column):
        th = th * (1.0 + jitter * rng.uniform(-1, 1))
        i0 = int((z - ZMIN) / ZRES)
        i1 = int((z + th - ZMIN) / ZRES)
        i0c, i1c = max(i0, 0), min(i1, NT)
        if i1c > i0c:
            F[i0c:i1c] = f
            mat[i0c:i1c] = k
        z += th
    if int((z - ZMIN) / ZRES) < NT:
        F[int((z - ZMIN) / ZRES):] = column[-1][1]
        mat[int((z - ZMIN) / ZRES):] = len(column) - 1
    return F, mat


def build_tables(seed=11):
    rng = np.random.default_rng(seed)
    F = np.ones((7, NT), np.float32)
    M = np.zeros((7, NT), np.int16)
    zs = ZMIN + (np.arange(NT) + 0.5) * ZRES
    # granito: diaclasas horizontales suaves (bandas de ±10 %)
    F[GRANITO] = 1.0 + 0.10 * np.sin(zs / 37.0) * np.sin(zs / 11.0)
    # metamórfico: bandas alternas de espesor variable (se inclinan con el buzamiento)
    z = ZMIN
    hard = True
    while z < ZMAX:
        th = rng.uniform(6, 30)
        i0, i1 = int((z - ZMIN) / ZRES), min(int((z + th - ZMIN) / ZRES), NT)
        F[METAMORFICO, i0:i1] = rng.uniform(0.45, 0.75) if hard else rng.uniform(1.3, 2.0)
        M[METAMORFICO, i0:i1] = 1 if hard else 0
        hard = not hard
        z += th
    # meseta estratificada
    F[ESTRATOS], M[ESTRATOS] = _table_from_column(COLUMNA_MESETA, BASE_MESETA, rng)
    # basalto: coladas duras de 5-14 m separadas por tobas/paleosuelos blandos de 1-4 m
    z = ZMIN
    while z < ZMAX:
        th = rng.uniform(5, 14)
        i0, i1 = int((z - ZMIN) / ZRES), min(int((z + th - ZMIN) / ZRES), NT)
        F[BASALTO, i0:i1] = rng.uniform(0.35, 0.6)
        M[BASALTO, i0:i1] = 1
        z += th
        th = rng.uniform(1, 4)
        i0, i1 = int((z - ZMIN) / ZRES), min(int((z + th - ZMIN) / ZRES), NT)
        F[BASALTO, i0:i1] = rng.uniform(1.8, 2.6)
        M[BASALTO, i0:i1] = 0
        z += th
    # sedimentos: blandos con costras calcáreas ocasionales
    F[SEDIMENTOS] = 1.0
    z = ZMIN
    while z < ZMAX:
        z += rng.uniform(15, 50)
        th = rng.uniform(1.5, 4)
        i0, i1 = int((z - ZMIN) / ZRES), min(int((z + th - ZMIN) / ZRES), NT)
        F[SEDIMENTOS, max(i0, 0):i1] = 0.55
        M[SEDIMENTOS, max(i0, 0):i1] = 1
        z += th
    F[EVAPORITAS] = 1.8
    # corrompido: roca fracturada, dureza muy variable en vertical
    z = ZMIN
    while z < ZMAX:
        th = rng.uniform(2, 12)
        i0, i1 = int((z - ZMIN) / ZRES), min(int((z + th - ZMIN) / ZRES), NT)
        F[CORROMPIDO, i0:i1] = rng.choice([0.4, 0.7, 1.3, 2.2])
        z += th
    return F, M


PERIODICA = np.array([False, True, False, True, True, False, True])


@njit(cache=True, inline='always')
def strat_index(zeta, prov, periodic, nt):
    k = int((zeta - ZMIN) / ZRES)
    if periodic[prov]:
        k = k % nt
        if k < 0:
            k += nt
    elif k < 0:
        k = 0
    elif k >= nt:
        k = nt - 1
    return k


@njit(parallel=True, cache=True)
def eval_kb(b, prov, kzone, zref, thick, F, periodic):
    """Erodabilidad de la roca en la cota b de cada celda."""
    n = b.size
    out = np.empty(n)
    nt = F.shape[1]
    for i in prange(n):
        zeta = (b[i] - zref[i]) / thick[i]
        k = strat_index(zeta, prov[i], periodic, nt)
        out[i] = kzone[i] * F[prov[i], k]
    return out


class Geology:
    """Campos geológicos a resolución n (derivados de Layout)."""

    def __init__(self, lay, seed=21):
        n = lay.n
        dx = lay.dx
        z = lay.zonas
        zz, xx = lay.coords()
        rng = np.random.default_rng(seed)
        self.F, self.M = build_tables(seed)
        # provincia dominante con contactos irregulares
        prov_w = np.zeros((7, n, n), np.float32)
        prov_w[GRANITO] += z['jardines'] * 1.2 + z['cordillera'] * 0.55
        prov_w[METAMORFICO] += z['cordillera'] * 0.45
        prov_w[ESTRATOS] += z['canones'] + z['oeste'] * 0.9 + z['este'] * 0.8
        prov_w[BASALTO] += z['volcanica']
        prov_w[SEDIMENTOS] += z['desierto'] + z['dunas'] + z['oeste'] * 0.1 + z['este'] * 0.2
        prov_w[EVAPORITAS] += z['salar']
        prov_w[CORROMPIDO] += z['corrompidas']
        # núcleo granítico en el eje de la cordillera, metamórfico en los flancos
        dcres, hcres = lay.cresta
        core = np.exp(-(dcres / 900.0) ** 2) * z['cordillera']
        prov_w[GRANITO] += core * 0.6
        prov_w[METAMORFICO] -= core * 0.3
        for k in range(7):
            prov_w[k] *= np.exp(0.35 * spectral_noise((n, n), 2.4, seed + 10 + k))
        self.prov = np.argmax(prov_w, 0).astype(np.int64)

        # dureza por zona (multiplicador de K)
        kz = np.ones((n, n), np.float32)
        kz *= np.exp(np.log(0.30) * z['cordillera'] + np.log(0.60) * z['jardines'] +
                     np.log(0.70) * z['corrompidas'] + np.log(0.8) * z['oeste'] +
                     np.log(0.7) * z['volcanica'] + np.log(0.40) * z['canones'] +
                     np.log(0.6) * z['este'] + np.log(1.6) * z['desierto'] +
                     np.log(1.6) * z['dunas'] + np.log(2.0) * z['salar'])
        # variabilidad lateral de dureza (fracturación)
        kz *= np.exp(0.25 * spectral_noise((n, n), 2.0, seed + 30))
        # peñones / inselbergs: plutones graníticos duros dispersos en el desierto
        self.knobs = np.zeros((n, n), np.float32)
        des = z['desierto'] + z['dunas'] + 0.5 * z['este'] + 0.4 * z['oeste']
        nk = 70
        cand = rng.uniform(0, n, (nk * 6, 2))
        placed = 0
        for cy, cx in cand:
            iy, ix = int(cy), int(cx)
            if des[iy, ix] < 0.6 or not lay.land[iy, ix] or lay.dist_coast[iy, ix] < 300:
                continue
            r = rng.uniform(25, 110) / dx
            d2 = ((zz / dx - cy) ** 2 + (xx / dx - cx) ** 2) / (r * r)
            self.knobs = np.maximum(self.knobs, np.exp(-d2 ** 2))
            placed += 1
            if placed >= nk:
                break
        kz *= np.exp(np.log(0.08) * self.knobs)
        # núcleo duro en el centro de los Jardines (domo granítico alrededor del cual se
        # dividió el glaciar) y macizo granítico de la Torre
        from .layout import poi_blocks
        for name, rad, f in (('jardines_de_velkia', 230.0, 0.30), ('torre_llama_eterna', 520.0, 0.6)):
            bx, bz = poi_blocks(name)
            d2 = ((xx - bx) ** 2 + (zz - bz) ** 2) / rad ** 2
            w = np.exp(-d2 ** 2)
            kz *= np.exp(np.log(f) * w)
            if name == 'torre_llama_eterna':
                self.prov[w > 0.5] = GRANITO
        self.kzone = kz.astype(np.float64)

        # cota de referencia (buzamiento + pliegues suaves) y espesor relativo de capas
        dip = np.zeros((n, n), np.float32)
        # metamórfico: buzamiento fuerte hacia el sur (capas en crestones E-O)
        dip += np.where(self.prov == METAMORFICO, 0.35 * (zz - zz.mean()), 0.0)
        # estratos: casi horizontales, suave abombamiento y ondulación
        warpf = blur(spectral_noise((n, n), 3.2, seed + 40), 2) * 25.0
        dip += np.where(self.prov == ESTRATOS, warpf, 0.0)
        dip += np.where(self.prov == BASALTO, 0.02 * np.hypot(xx - 2120, zz - 6171) + warpf * 0.4, 0.0)
        dip += np.where(self.prov == CORROMPIDO, spectral_noise((n, n), 2.2, seed + 41) * 30.0, 0.0)
        self.zref = dip.astype(np.float64)
        th = np.exp(0.22 * spectral_noise((n, n), 2.8, seed + 50))   # espesores irregulares
        self.thick = th.astype(np.float64)

    def kb(self, b, K0):
        return K0 * eval_kb(b.ravel(), self.prov.ravel(), self.kzone.ravel(),
                            self.zref.ravel(), self.thick.ravel(), self.F, PERIODICA)
