"""v1, paso 1: recontextualizar biomas y materiales con las zonas del lienzo aprobado.

  python3 -m velkia.biomas_v1 [datos_entrada] [datos_salida]
      (por defecto salida/mundo_datos -> salida/v1_datos)

Toma el terreno y el agua ya preparados (Y, WL, FL de etapa4) y rehace solo SURF, SDEP, BIO, la
provincia de roca (geologia.npz) y el suelo de la torre.  Y/WL/FL se enlazan, no se copian.

Por zona (superficie / bioma; en laderas empinadas asoma la roca de la provincia):
  montañas   piedra y grava, nieve arriba          windswept_gravelly_hills / snowy_slopes / jagged_peaks
  mura       blackstone                            velkia:tierras_corrompidas (agua morada que daña)
  jardines   pasto                                 velkia:jardines
  terracota  arena roja en lo plano, bandas         badlands
             de terracota vanilla en las laderas
  dunas      arena                                 desert
  arena      arena                                 desert
  domos      arena roja; arenisca roja en domos    velkia:domos
  volcán     ceniza; basalto en laderas            velkia:volcanica
  salar      sal                                   velkia:salar (burbujas en toda el agua)
Costas con el material de su bioma (playa solo donde es arenoso); lechos y orillas por bioma.
"""
import json
import os
import shutil
import sys
import time

import numpy as np
from scipy import ndimage as ndi

from .geology import GRANITO, METAMORFICO, BASALTO, SEDIMENTOS, EVAPORITAS, CORROMPIDO
from .layout import N, SEA
from .materials import SUP, DOMOS, BADLANDS
from .noise import spectral_noise
from .zonas_v1 import Z, zonas_v1

BIOMAS = ['minecraft:ocean', 'minecraft:deep_ocean', 'minecraft:beach', 'minecraft:river', 'minecraft:desert',
          'minecraft:badlands', 'minecraft:eroded_badlands', 'minecraft:snowy_slopes', 'minecraft:jagged_peaks',
          'minecraft:windswept_gravelly_hills', 'minecraft:stony_shore', 'minecraft:warm_ocean',
          'velkia:salar', 'velkia:volcanica', 'velkia:tierras_corrompidas', 'velkia:jardines', 'velkia:domos']
B = {k.split(':')[1]: i for i, k in enumerate(BIOMAS)}

# zona -> (superficie en lo plano, superficie de lecho/orilla, superficie de costa, bioma, pendiente de roca)
POR_ZONA = {
    'montanas': ('roca', 'grava', 'grava', 'windswept_gravelly_hills', 0.0),
    'mura': ('corrompido', 'corrompido', 'corrompido', 'tierras_corrompidas', 1.1),
    'jardines': ('pradera', 'barro', 'pradera', 'jardines', 0.9),
    'terracota': ('arena_roja', 'arena_roja', 'arena_roja', 'badlands', 0.35),
    'dunas': ('arena', 'arena', 'arena', 'desert', 1.0),
    'arena': ('arena', 'arena', 'arena', 'desert', 1.0),
    'domos': ('arena_roja', 'arena_roja', 'arena_roja', 'domos', 0.5),
    'volcan': ('ceniza', 'arena_negra', 'arena_negra', 'volcanica', 0.5),
    'salar': ('sal', 'sal', 'arena', 'salar', 0.9),
}
ARENOSAS = ('dunas', 'arena', 'domos', 'salar')
# provincia de roca por zona (montañas y Jardines conservan la de la erosión)
PROV_ZONA = {'mura': CORROMPIDO, 'terracota': BADLANDS, 'dunas': SEDIMENTOS, 'arena': SEDIMENTOS,
             'domos': DOMOS, 'volcan': BASALTO, 'salar': EVAPORITAS}
# suelo de la torre (montículo de piedra, grava y tierra) -> material del bioma de arena
TORRE_SUELO = {'minecraft:stone': 'minecraft:sandstone', 'minecraft:gravel': 'minecraft:sand',
               'minecraft:dirt': 'minecraft:sand', 'minecraft:coarse_dirt': 'minecraft:sand'}


def zonas_bloque(zg):
    """Zonas de la malla gruesa a 1 bloque con bordes desplazados por ruido (sin escalones de celda)."""
    n = zg.shape[0]
    f = N // n
    wz = (spectral_noise((n, n), 3.0, 77) * 40.0).astype(np.float32)
    wx = (spectral_noise((n, n), 3.0, 78) * 40.0).astype(np.float32)
    out = np.empty((N, N), np.uint8)
    cols = (np.arange(N) + 0.5) / f - 0.5
    for r0 in range(0, N, 1024):
        filas = (np.arange(r0, r0 + 1024) + 0.5) / f - 0.5
        FZ, FX = np.meshgrid(filas, cols, indexing='ij')
        dz = ndi.map_coordinates(wz, [FZ, FX], order=1, mode='nearest')
        dxw = ndi.map_coordinates(wx, [FZ, FX], order=1, mode='nearest')
        zz = np.clip(((np.arange(r0, r0 + 1024)[:, None] + dz) / f).astype(np.int64), 0, n - 1)
        xx = np.clip(((np.arange(N)[None, :] + dxw) / f).astype(np.int64), 0, n - 1)
        out[r0:r0 + 1024] = zg[zz, xx]
    return out


def superficies_v1(Y, WL, FL, zb, log=print):
    """SURF, SDEP, BIO por columna a partir de las zonas a 1 bloque 'zb'."""
    mar = (FL == 1) & (WL == SEA) & (Y < SEA)
    mar = ndi.binary_propagation(mar & ndi.binary_erosion(mar, iterations=4), mask=mar)
    agua = (FL == 1) & ~mar
    Yf = Y.astype(np.float32)
    gz, gx = np.gradient(Yf)
    S = np.hypot(gz, gx)
    del gz, gx
    SURF = np.full((N, N), SUP['arena'], np.uint8)
    BIO = np.full((N, N), B['desert'], np.uint8)
    SDEP = np.full((N, N), 3, np.uint8)
    manchas = spectral_noise((N // 8, N // 8), 2.6, 501, kmin=20.0)
    manchas = np.repeat(np.repeat(manchas, 8, 0), 8, 1)
    for nm, (plano, _, _, bio, s_roca) in POR_ZONA.items():
        m = zb == Z[nm]
        SURF[m] = SUP[plano]
        BIO[m] = B[bio]
        if s_roca > 0:
            SURF[m & (S > s_roca)] = SUP['roca']
    log('  zonas pintadas')
    # montañas: piedra con manchas de grava en lo suave, nieve arriba, biomas por altura
    mo = zb == Z['montanas']
    SURF[mo & (S < 0.6) & (manchas > 0.35)] = SUP['grava']
    nieve = mo & (Y > 300 + 25 * manchas) & (S < 1.2)
    SURF[nieve] = SUP['nieve']
    BIO[mo & (Y > 300)] = B['snowy_slopes']
    BIO[mo & (Y > 350)] = B['jagged_peaks']
    # terracota: badlands erosionado en las laderas fuertes
    BIO[(zb == Z['terracota']) & (S > 0.9)] = B['eroded_badlands']
    # costa: material de su bioma, playa solo en las zonas arenosas
    costa = ndi.binary_dilation(mar, iterations=6) & ~mar & (Y <= SEA + 3) & (FL == 0)
    for nm, (_, _, cst, bio, _) in POR_ZONA.items():
        m = costa & (zb == Z[nm])
        SURF[m] = SUP[cst]
        if nm in ARENOSAS:
            BIO[m] = B['beach']
        elif nm == 'montanas':
            BIO[m] = B['stony_shore']
    log('  costas')
    # mar
    prof = (SEA - Yf).clip(0)
    SURF[mar] = np.where(prof[mar] < 8, SUP['arena'], SUP['grava'])
    BIO[mar] = np.where(prof[mar] > 30, B['deep_ocean'], B['warm_ocean'])
    # ríos y lagos: lecho y orillas con el material de su bioma
    orilla = ndi.binary_dilation(agua, iterations=3) & (FL == 0) & ~costa
    for nm, (_, lecho, _, _, _) in POR_ZONA.items():
        zm = zb == Z[nm]
        SURF[agua & zm] = SUP[lecho]
        SURF[orilla & zm & (S < 1.0)] = SUP[lecho]
    # bioma de río salvo en las zonas cuyo agua es especial (mura, salar, Jardines)
    rio = ndi.binary_dilation(agua, iterations=3) & ~mar
    propia = (zb == Z['mura']) | (zb == Z['salar']) | (zb == Z['jardines'])
    BIO[rio & ~propia] = B['river']
    log('  agua')
    # espesor de suelo
    SDEP[np.isin(SURF, [SUP['arena'], SUP['arena_roja']])] = 4
    SDEP[SURF == SUP['sal']] = 2
    return SURF, SDEP, BIO


def provincia_v1(prov, zref, thick, zg):
    """Provincia de roca por zona; las de bandas horizontales usan zref=0, thick=1."""
    prov, zref, thick = prov.copy(), zref.copy(), thick.copy()
    for nm, p in PROV_ZONA.items():
        m = zg == Z[nm]
        prov[m] = p
        if p in (DOMOS, BADLANDS):
            zref[m] = 0.0
            thick[m] = 1.0
    return prov, zref, thick


def torre_v1(estructuras, out_dir):
    """Suelo de la torre con el material del bioma (schematic reescrito en out_dir)."""
    from .schem import Schematic
    os.makedirs(out_dir, exist_ok=True)
    nuevas = []
    for e in estructuras:
        e = dict(e)
        if e['nombre'].startswith('Torre'):
            s = Schematic.load(e['archivo'])
            s.palette = [TORRE_SUELO.get(p, p) for p in s.palette]
            ruta = os.path.abspath(os.path.join(out_dir, os.path.basename(e['archivo'])))
            s.save(ruta)
            e['archivo'] = ruta
        nuevas.append(e)
    return nuevas


def recolorear(ent='salida/mundo_datos', sal='salida/v1_datos', etapa='salida/etapa1.npz'):
    t0 = time.time()
    log = lambda t: print(f'[{time.time() - t0:5.0f} s] {t}', flush=True)
    os.makedirs(sal, exist_ok=True)
    d = np.load(etapa)
    z, z_mix, z_tierra = zonas_v1(d)
    np.save(os.path.join(sal, 'zonas_v1.npy'), z_tierra)
    log('zonas v1')
    zb = zonas_bloque(z_tierra)
    log('zonas a 1 bloque')
    Y = np.load(os.path.join(ent, 'Y.npy'))
    WL = np.load(os.path.join(ent, 'WL.npy'))
    FL = np.load(os.path.join(ent, 'FL.npy'))
    SURF, SDEP, BIO = superficies_v1(Y, WL, FL, zb, log=log)
    # el sendero de la torre se conserva (código 18: ahora arenisca)
    SURF = np.where(np.load(os.path.join(ent, 'SURF.npy')) == SUP['sendero'], SUP['sendero'], SURF)
    for nm, a in (('SURF', SURF), ('SDEP', SDEP), ('BIO', BIO), ('ZONA', zb)):
        np.save(os.path.join(sal, nm + '.npy'), a)
    for nm in ('Y', 'WL', 'FL'):
        dst = os.path.join(sal, nm + '.npy')
        if not os.path.exists(dst):
            os.symlink(os.path.abspath(os.path.join(ent, nm + '.npy')), dst)
    g = np.load(os.path.join(ent, 'geologia.npz'))
    prov, zref, thick = provincia_v1(g['prov'], g['zref'], g['thick'], z_tierra)
    np.savez_compressed(os.path.join(sal, 'geologia.npz'), prov=prov, zref=zref, thick=thick)
    json.dump(BIOMAS, open(os.path.join(sal, 'biomas.json'), 'w'))
    est = json.load(open(os.path.join(ent, 'estructuras.json')))
    json.dump(torre_v1(est, os.path.join(sal, 'estructuras')),
              open(os.path.join(sal, 'estructuras.json'), 'w'), indent=1, ensure_ascii=False)
    shutil.copy(os.path.join(ent, 'info.json'), os.path.join(sal, 'info.json'))
    log(f'guardado en {sal}')


if __name__ == '__main__':
    recolorear(*sys.argv[1:])
