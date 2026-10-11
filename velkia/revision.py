"""Imágenes de revisión: mapa completo con las 8 construcciones marcadas, comparación con el
mapa de referencia, acercamientos y perfil del río.

Para cada construcción se informa: cota del terreno bajo la huella (mín/mediana/máx), cota de
suelo que necesita el schematic, desfase vertical (dy) que habría que aplicar al pegarla y
cuánta nivelación pediría (relieve dentro de la huella).
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

from .estructuras import SITIOS, Sitio
from .layout import N, SEA, POIS, px2b, b2px, REF
from .render import relief_image

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# 8 construcciones: (etiqueta, sitio de estructuras.py, carpetas, cota de suelo que necesita)
CONSTRUCCIONES = [
    ('Gran Pirámide', 'complejo_piramide', ['piramide'], 80),
    ('Esfinge (explanada)', 'complejo_piramide', ['explanada_esfinge'], 80),
    ('Thza', 'complejo_piramide', ['thza'], 82),
    ('Jardines colgantes', 'jardines_colgantes', ['jardines_colgantes'], 84),
    ('Vieja Velkia', 'vieja_velkia', ['vieja_velkia'], 89),
    ('Aldea fantasma oeste', 'aldea_fantasma_oeste', ['aldea_fantasma_norte'], 103),
    ('Aldea fantasma sur', 'aldea_fantasma_sur', ['aldea_fantasma_sur'], 95),
    ('Torre de la llama eterna', 'torre_llama_eterna', ['torre_llama_eterna'], None),
]
POI_DE = ['gran_piramide', 'esfinge', 'thza', 'jardines_de_velkia', 'gran_canon_vieja_velkia',
          'aldea_fantasma_oeste', 'aldea_fantasma_sur', 'torre_llama_eterna']


def _font(size, bold=False):
    try:
        return ImageFont.truetype(FONTB if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def huellas():
    """Huella (máscara 2D en bloques) y datos de cada construcción, con su transformación final."""
    out = []
    for (nombre, sitio, carpetas, suelo), poi in zip(CONSTRUCCIONES, POI_DE):
        cfg = dict(SITIOS[sitio])
        cfg['carpetas'] = carpetas
        s = Sitio(nombre, cfg)
        m = s.maps()
        foot = m['foot']
        if suelo is None:   # torre: suelo natural alrededor de la base de la torre
            top = m['top']
            ci = np.unravel_index(np.argmax(np.where(foot, top, -999)), top.shape)
            rr = np.hypot(*np.meshgrid(np.arange(foot.shape[0]) - ci[0], np.arange(foot.shape[1]) - ci[1],
                                       indexing='ij'))
            near = foot & (rr < 18) & (m['ground'] > -999)
            suelo = int(np.median(m['ground'][near])) if near.any() else int(m['bottom'][foot].min())
            # la huella de la torre incluye un sendero que se recortará: usar solo la torre
            foot = foot & (rr < 22)
        out.append({'nombre': nombre, 'x0': m['x0'], 'z0': m['z0'], 'foot': foot, 'suelo': suelo,
                    'poi': poi, 'water': m['water'], 'water_y': m['water_y']})
    return out


def _stats(h_y, dx, H):
    n = h_y.shape[0]
    zz, xx = np.nonzero(H['foot'])
    cz = ((zz + H['z0']) / dx).astype(int).clip(0, n - 1)
    cx = ((xx + H['x0']) / dx).astype(int).clip(0, n - 1)
    cells = np.unique(cz * n + cx)
    v = h_y.ravel()[cells]
    return float(v.min()), float(np.median(v)), float(v.max())


def _outline(H, dx, scale):
    """Contorno de la huella en píxeles de la imagen."""
    f = H['foot']
    step = max(1, int(dx // 2))
    small = f[::step, ::step]
    edge = small & ~ndi.binary_erosion(small)
    zz, xx = np.nonzero(edge)
    px = (xx * step + H['x0']) / dx * scale
    pz = (zz * step + H['z0']) / dx * scale
    return px, pz


def generar(etapa1_path, out_dir, ref_path=REF):
    os.makedirs(out_dir, exist_ok=True)
    d = np.load(etapa1_path)
    h = d['h']
    n = h.shape[0]
    dx = N / n
    Y = h + SEA
    chain = d['chain']
    from .sim import ocean_mask
    ocean = ocean_mask(h, 0.0)
    lake = (d['filled'] - h > 0.5) & ~ocean
    base = relief_image(Y, dx, water=ocean | lake)
    H = huellas()
    filas = []
    for k, Hk in enumerate(H):
        mn, med, mx = _stats(Y, dx, Hk)
        dy = int(round(med - Hk['suelo']))
        relieve = mx - mn
        # posición relativa en el entorno (percentil de la cota dentro de 800 bloques)
        zz, xx = np.nonzero(Hk['foot'])
        ci = int((Hk['z0'] + zz.mean()) / dx)
        cj = int((Hk['x0'] + xx.mean()) / dx)
        r = int(800 / dx)
        win = Y[max(0, ci - r):ci + r, max(0, cj - r):cj + r]
        pct = float((win < med).mean() * 100)
        partes = []
        if relieve > 25:
            partes.append(f'terreno irregular ({relieve:.0f} bl): requiere asiento')
        else:
            partes.append(f'relieve bajo la huella {relieve:.0f} bl')
        partes.append(f'percentil de altura en el entorno: {pct:.0f}%')
        if 'Torre' in Hk['nombre'] and pct < 90:
            partes.append('NO está en una cima')
        estado = '; '.join(partes)
        filas.append((k + 1, Hk['nombre'], mn, med, mx, Hk['suelo'], dy, estado))

    # ------------------------------------------------ imagen 1: mapa + tabla
    scale = 1
    W = n * scale
    panel = 760
    img = Image.new('RGB', (W + panel, max(W, 900)), (24, 26, 30))
    img.paste(base.resize((W, W)), (0, 0))
    dr = ImageDraw.Draw(img)
    # río
    pts = [((c % n + 0.5) * scale, (c // n + 0.5) * scale) for c in chain]
    dr.line(pts, fill=(60, 140, 255), width=2)
    f16, f14, f20 = _font(16, True), _font(14), _font(20, True)
    for k, Hk in enumerate(H):
        px, pz = _outline(Hk, dx, scale)
        for x, z in zip(px, pz):
            dr.point((x, z), fill=(255, 40, 40))
        cx, cz = px.mean(), pz.mean()
        r = 11
        dr.ellipse([cx - r, cz - r, cx + r, cz + r], fill=(255, 255, 255), outline=(200, 0, 0), width=2)
        t = str(k + 1)
        tw = dr.textlength(t, font=f16)
        dr.text((cx - tw / 2, cz - 9), t, fill=(180, 0, 0), font=f16)
    x0 = W + 20
    dr.text((x0, 18), 'Velkia v1 (1024², 8 bloques/celda)', fill=(240, 240, 240), font=f20)
    dr.text((x0, 46), 'Construcciones: cota del terreno bajo la huella vs. cota que necesitan',
            fill=(190, 190, 190), font=f14)
    y = 82
    dr.text((x0, y), '#  construcción            terreno Y (mín/med/máx)   suelo  dy', fill=(150, 200, 255),
            font=_font(13, True))
    y += 22
    for (k, nombre, mn, med, mx, suelo, dy, estado) in filas:
        dr.text((x0, y), f'{k}  {nombre}', fill=(255, 255, 255), font=f14)
        dr.text((x0 + 230, y), f'{mn:.0f} / {med:.0f} / {mx:.0f}', fill=(255, 255, 255), font=f14)
        dr.text((x0 + 440, y), f'{suelo}', fill=(255, 255, 255), font=f14)
        dr.text((x0 + 500, y), f'{dy:+d}', fill=(255, 220, 120), font=f14)
        y += 19
        dr.text((x0 + 18, y), estado, fill=(170, 170, 170), font=_font(12))
        y += 24
    y += 8
    notas = [
        'dy = desplazamiento vertical a aplicar al pegar (mediana del terreno − suelo).',
        'Mar a Y=62. Línea azul: río Velkia (trazado antecedente).',
        'Huellas en rojo; el complejo Pirámide-Esfinge-Thza va rotado 90°.',
        'Aún sin volcán, salar plano, dunas ni detalle fino (etapas siguientes).',
    ]
    for t in notas:
        dr.text((x0, y), t, fill=(200, 200, 200), font=_font(13))
        y += 20
    # perfil del río
    y += 14
    prof = Y.ravel()[chain]
    en_mar = ocean.ravel()[chain]
    if en_mar.any():
        prof = prof[:int(np.argmax(en_mar)) + 1]
    ph, pw = 190, panel - 50
    dr.rectangle([x0, y, x0 + pw, y + ph], outline=(120, 120, 120))
    dr.text((x0 + 4, y + 4), 'Perfil del río (Y del lecho, fuente → costa)', fill=(220, 220, 220), font=_font(12))
    lo, hi = min(prof.min(), SEA - 5), prof.max() + 5
    pts = [(x0 + i / (len(prof) - 1) * pw, y + ph - (v - lo) / (hi - lo) * ph) for i, v in enumerate(prof)]
    dr.line(pts, fill=(80, 160, 255), width=2)
    sy = y + ph - (SEA - lo) / (hi - lo) * ph
    dr.line([(x0, sy), (x0 + pw, sy)], fill=(40, 90, 200), width=1)
    dr.text((x0 + pw - 70, sy - 15), 'mar Y=62', fill=(120, 160, 255), font=_font(11))
    dr.text((x0 + 4, y + ph + 4), f'máx {prof.max():.0f}  mín {prof.min():.0f}  '
            f'tramos que suben: {int((np.diff(prof) > 0.5).sum())}', fill=(200, 200, 200), font=_font(12))
    p1 = os.path.join(out_dir, 'v1_mapa_construcciones.png')
    img.save(p1)

    # ------------------------------------------------ imagen 2: referencia vs generado
    ref = Image.open(ref_path).convert('RGB')
    # recortar la referencia al mismo encuadre de bloques que el mapa generado
    corners = [b2px(0, 0), b2px(N, N)]
    (rx0, rz0), (rx1, rz1) = corners
    refc = ref.crop((int(rx0), int(rz0), int(rx1), int(rz1))).resize((W, W))
    cmp_ = Image.new('RGB', (2 * W + 20, W + 40), (24, 26, 30))
    cmp_.paste(refc, (0, 40))
    cmp_.paste(img.crop((0, 0, W, W)), (W + 20, 40))
    dc = ImageDraw.Draw(cmp_)
    dc.text((10, 10), 'Mapa de referencia (mismo encuadre)', fill=(240, 240, 240), font=f16)
    dc.text((W + 30, 10), 'Velkia v1 generado', fill=(240, 240, 240), font=f16)
    for k, poi in enumerate(POI_DE):
        bx, bz = px2b(*POIS[poi])
        cx, cz = bx / N * W, bz / N * W + 40
        r = 10
        dc.ellipse([cx - r, cz - r, cx + r, cz + r], outline=(255, 255, 0), width=3)
        dc.text((cx + 12, cz - 9), str(k + 1), fill=(255, 255, 0), font=f16)
    p2 = os.path.join(out_dir, 'v1_comparacion_referencia.png')
    cmp_.save(p2)

    # ------------------------------------------------ imagen 3: acercamientos
    tile = 340
    mos = Image.new('RGB', (4 * tile, 2 * tile + 60), (24, 26, 30))
    dm = ImageDraw.Draw(mos)
    for k, Hk in enumerate(H):
        f = Hk['foot']
        zz, xx = np.nonzero(f)
        cxb = Hk['x0'] + xx.mean()
        czb = Hk['z0'] + zz.mean()
        half = 900.0
        a0 = int(max(0, (czb - half) / dx))
        a1 = int(min(n, (czb + half) / dx))
        b0 = int(max(0, (cxb - half) / dx))
        b1 = int(min(n, (cxb + half) / dx))
        crop = base.crop((b0, a0, b1, a1)).resize((tile, tile), Image.BICUBIC)
        dd = ImageDraw.Draw(crop)
        sx = tile / (b1 - b0)
        px, pz = _outline(Hk, dx, 1.0)
        for x, z in zip(px, pz):
            dd.point(((x - b0) * sx, (z - a0) * sx), fill=(255, 40, 40))
        cpts = [((c % n - b0 + 0.5) * sx, (c // n - a0 + 0.5) * sx) for c in chain
                if b0 <= c % n < b1 and a0 <= c // n < a1]
        if len(cpts) > 1:
            dd.line(cpts, fill=(60, 140, 255), width=2)
        ox, oy = (k % 4) * tile, (k // 4) * (tile + 30)
        mos.paste(crop, (ox, oy + 30))
        fk = filas[k]
        dm.text((ox + 6, oy + 2), f'{k + 1}. {fk[1]}', fill=(255, 255, 255), font=_font(13, True))
        dm.text((ox + 6, oy + 16), f'terreno {fk[3]:.0f} (±{(fk[4] - fk[2]) / 2:.0f})  suelo {fk[5]}  dy {fk[6]:+d}',
                fill=(255, 220, 120), font=_font(11))
    p3 = os.path.join(out_dir, 'v1_acercamientos.png')
    mos.save(p3)
    return [p1, p2, p3], filas
