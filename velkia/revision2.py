"""Imágenes de revisión v2: colocación final y asiento de las construcciones sobre el terreno.

Genera:
  v2_mapa_construcciones.png   mapa sombreado (terreno ya asentado) + tabla de colocación
  v2_comparacion_referencia.png  mapa de referencia y generado con el mismo encuadre
  v2_acercamientos.png         acercamientos de las 8 construcciones y los 3 sitios reservados
y devuelve la lista de filas de la tabla.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

from .layout import N, SEA, POIS, RESERVADOS, px2b, b2px, REF
from .render import relief_image

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
POI_DE = ['gran_piramide', 'esfinge', 'thza', 'jardines_de_velkia', 'gran_canon_vieja_velkia',
          'aldea_fantasma_oeste', 'aldea_fantasma_sur', 'torre_llama_eterna']
RES_NOMBRE = {'crakatos': 'A Crakatos', 'cuarto_de_bashi': 'B Cuarto de Bashi', 'fuertes_en_ruinas': 'C Fuertes en ruinas'}


def _f(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)


def _contorno(m, dx, scale=1.0):
    f = m['foot']
    step = max(1, int(dx // 2))
    small = f[::step, ::step]
    edge = small & ~ndi.binary_erosion(small)
    zz, xx = np.nonzero(edge)
    return (xx * step + m['x0']) / dx * scale, (zz * step + m['z0']) / dx * scale


def _poly(xy, dx, scale=1.0):
    return [(p[0] / dx * scale, p[1] / dx * scale) for p in xy]


def generar(Y0, Ym, colocaciones, rio_xy, afluentes, lagos, ocean, out_dir, boca=None, perfil=None,
            notas=()):
    """Y0: terreno antes del asiento; Ym: terreno asentado (cotas absolutas, malla de 1024)."""
    os.makedirs(out_dir, exist_ok=True)
    n = Ym.shape[0]
    dx = N / n
    base = relief_image(Ym, dx, water=ocean | lagos)
    W = n
    filas = []
    for k, o in enumerate(colocaciones):
        m = o['maps']
        zz, xx = np.nonzero(m['foot'])
        ci = np.clip(((zz + m['z0']) / dx).astype(int), 0, n - 1)
        cj = np.clip(((xx + m['x0']) / dx).astype(int), 0, n - 1)
        v0 = Y0[ci, cj]
        inf = o.get('informe', {})
        dp = o.get('despues', {})
        filas.append({
            'n': k + 1, 'nombre': o['nombre'], 'shift': o['shift'], 'dy': o['dy'],
            'x': int(m['x0'] + xx.mean()), 'z': int(m['z0'] + zz.mean()),
            'terr': (float(v0.min()), float(np.median(v0)), float(v0.max())),
            'corte': inf.get('corte_max', 0.0), 'relleno': inf.get('relleno_max', 0.0),
            'flot': dp.get('flotacion_max', 0.0), 'ent': dp.get('enterramiento_max', 0.0),
        })

    # ------------------------------------------------ 1: mapa + tabla
    panel = 820
    img = Image.new('RGB', (W + panel, max(W, 1000)), (24, 26, 30))
    img.paste(base, (0, 0))
    d = ImageDraw.Draw(img)
    d.line(_poly(rio_xy, dx), fill=(70, 140, 255), width=2)
    for nm, xy in afluentes.items():
        d.line(_poly(xy, dx), fill=(110, 190, 255), width=2)
    if boca is not None:
        bx, bz = boca
        d.ellipse([bx / dx - 9, bz / dx - 9, bx / dx + 9, bz / dx + 9], outline=(120, 220, 255), width=2)
    for k, o in enumerate(colocaciones):
        px, pz = _contorno(o['maps'], dx)
        for x, z in zip(px, pz):
            d.point((x, z), fill=(255, 40, 40))
        cx, cz = px.mean(), pz.mean()
        d.ellipse([cx - 11, cz - 11, cx + 11, cz + 11], fill=(255, 255, 255), outline=(200, 0, 0), width=2)
        t = str(k + 1)
        d.text((cx - d.textlength(t, font=_f(16, True)) / 2, cz - 9), t, fill=(180, 0, 0), font=_f(16, True))
    for nm, (pxy, rad, tipo) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        r = rad / dx
        d.ellipse([bx / dx - r, bz / dx - r, bx / dx + r, bz / dx + r], outline=(255, 230, 80), width=2)
        d.text((bx / dx + r + 3, bz / dx - 8), RES_NOMBRE[nm][0], fill=(255, 230, 80), font=_f(16, True))
    x0 = W + 18
    d.text((x0, 14), 'Velkia v2 (1024², 8 bloques/celda) — colocación y asiento', fill=(240, 240, 240), font=_f(19, True))
    y = 46
    hdr = ['#', 'construcción', 'mov. (x,z)', 'dy', 'terreno antes', 'corte/relleno', 'borde después']
    xs = [0, 18, 200, 300, 350, 500, 630]
    for t, xo in zip(hdr, xs):
        d.text((x0 + xo, y), t, fill=(150, 200, 255), font=_f(12, True))
    y += 20
    for fl in filas:
        vals = [str(fl['n']), fl['nombre'], f"{fl['shift'][0]:+d},{fl['shift'][1]:+d}", f"{fl['dy']:+d}",
                f"{fl['terr'][0]:.0f}/{fl['terr'][1]:.0f}/{fl['terr'][2]:.0f}",
                f"{fl['corte']:.0f}/{fl['relleno']:.0f}", f"flota {fl['flot']:.0f} · ent. {fl['ent']:.0f}"]
        for t, xo in zip(vals, xs):
            d.text((x0 + xo, y), t, fill=(255, 255, 255), font=_f(12))
        y += 19
    y += 6
    d.text((x0, y), 'Sitios reservados (amarillo): ' + ', '.join(RES_NOMBRE.values()), fill=(255, 230, 80), font=_f(12))
    y += 24
    for t in notas:
        for linea in _envolver(d, t, _f(12), panel - 40):
            d.text((x0, y), linea, fill=(205, 205, 205), font=_f(12))
            y += 17
        y += 3
    if perfil is not None:
        prof, marcas = perfil
        y += 8
        ph, pw = 210, panel - 50
        d.rectangle([x0, y, x0 + pw, y + ph], outline=(120, 120, 120))
        d.text((x0 + 4, y + 4), 'Perfil del río Velkia (cota del lecho, fuente → estuario)', fill=(220, 220, 220), font=_f(12))
        lo, hi = SEA - 5, max(prof.max(), SEA + 20) + 5
        pts = [(x0 + i / (len(prof) - 1) * pw, y + ph - (v - lo) / (hi - lo) * ph) for i, v in enumerate(prof)]
        d.line(pts, fill=(80, 160, 255), width=2)
        sy = y + ph - (SEA - lo) / (hi - lo) * ph
        d.line([(x0, sy), (x0 + pw, sy)], fill=(40, 90, 200))
        for (idx, nombre) in marcas:
            mx = x0 + idx / (len(prof) - 1) * pw
            d.line([(mx, y + 18), (mx, y + ph)], fill=(255, 220, 120))
            d.text((mx + 3, y + 20), nombre, fill=(255, 220, 120), font=_f(11))
        sub = int((np.diff(prof) > 0.5).sum())
        d.text((x0 + 4, y + ph + 4), f'fuente Y={prof[0]:.0f} · estuario Y={prof[-1]:.0f} · tramos que suben: {sub}',
               fill=(200, 200, 200), font=_f(12))
    p1 = os.path.join(out_dir, 'v2_mapa_construcciones.png')
    img.save(p1)

    # ------------------------------------------------ 2: referencia vs generado
    ref = Image.open(REF).convert('RGB')
    (rx0, rz0), (rx1, rz1) = b2px(0, 0), b2px(N, N)
    refc = ref.crop((int(rx0), int(rz0), int(rx1), int(rz1))).resize((W, W))
    cmp_ = Image.new('RGB', (2 * W + 20, W + 40), (24, 26, 30))
    cmp_.paste(refc, (0, 40))
    cmp_.paste(img.crop((0, 0, W, W)), (W + 20, 40))
    dc = ImageDraw.Draw(cmp_)
    dc.text((10, 10), 'Mapa de referencia (mismo encuadre)', fill=(240, 240, 240), font=_f(16, True))
    dc.text((W + 30, 10), 'Velkia v2 generado (terreno asentado)', fill=(240, 240, 240), font=_f(16, True))
    for k, poi in enumerate(POI_DE):
        bx, bz = px2b(*POIS[poi])
        cx, cz = bx / N * W, bz / N * W + 40
        dc.ellipse([cx - 10, cz - 10, cx + 10, cz + 10], outline=(255, 255, 0), width=3)
        dc.text((cx + 12, cz - 9), str(k + 1), fill=(255, 255, 0), font=_f(16, True))
    for nm, (pxy, rad, tipo) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        cx, cz = bx / N * W, bz / N * W + 40
        dc.ellipse([cx - 8, cz - 8, cx + 8, cz + 8], outline=(255, 150, 0), width=2)
        dc.text((cx + 10, cz - 9), RES_NOMBRE[nm][0], fill=(255, 150, 0), font=_f(15, True))
    p2 = os.path.join(out_dir, 'v2_comparacion_referencia.png')
    cmp_.save(p2)

    # ------------------------------------------------ 3: acercamientos
    tile = 330
    items = [(fl['nombre'], fl['x'], fl['z'], colocaciones[i]['maps'], fl) for i, fl in enumerate(filas)]
    for nm, (pxy, rad, tipo) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        items.append((RES_NOMBRE[nm], bx, bz, None, None))
    cols = 4
    rows = (len(items) + cols - 1) // cols
    mos = Image.new('RGB', (cols * tile, rows * (tile + 34)), (24, 26, 30))
    dm = ImageDraw.Draw(mos)
    for k, (nombre, cxb, czb, m, fl) in enumerate(items):
        half = 900.0
        a0, a1 = int(max(0, (czb - half) / dx)), int(min(n, (czb + half) / dx))
        b0, b1 = int(max(0, (cxb - half) / dx)), int(min(n, (cxb + half) / dx))
        crop = base.crop((b0, a0, b1, a1)).resize((tile, tile), Image.BICUBIC)
        dd = ImageDraw.Draw(crop)
        sc = tile / (b1 - b0)
        if m is not None:
            px, pz = _contorno(m, dx)
            for x, z in zip(px, pz):
                dd.point(((x - b0) * sc, (z - a0) * sc), fill=(255, 40, 40))
        for xy, col in [(rio_xy, (70, 140, 255))] + [(v, (110, 190, 255)) for v in afluentes.values()]:
            pts = [((p[0] / dx - b0) * sc, (p[1] / dx - a0) * sc) for p in xy
                   if b0 * dx <= p[0] < b1 * dx and a0 * dx <= p[1] < a1 * dx]
            if len(pts) > 1:
                dd.line(pts, fill=col, width=2)
        if m is None:
            for nm, (pxy, rad, tipo) in RESERVADOS.items():
                bx, bz = px2b(*pxy)
                r = rad / dx * sc
                ccx, ccz = (bx / dx - b0) * sc, (bz / dx - a0) * sc
                dd.ellipse([ccx - r, ccz - r, ccx + r, ccz + r], outline=(255, 230, 80), width=2)
        ox, oy = (k % cols) * tile, (k // cols) * (tile + 34)
        mos.paste(crop, (ox, oy + 34))
        dm.text((ox + 6, oy + 2), (f"{k + 1}. " if fl else '') + nombre, fill=(255, 255, 255), font=_f(13, True))
        if fl:
            dm.text((ox + 6, oy + 18), f"dy {fl['dy']:+d} · terreno {fl['terr'][1]:.0f} · borde: flota {fl['flot']:.0f} ent. {fl['ent']:.0f}",
                    fill=(255, 220, 120), font=_f(11))
        else:
            i0, j0 = int(czb / dx), int(cxb / dx)
            dm.text((ox + 6, oy + 18), f"terreno Y={Ym[i0, j0]:.0f} (reservado)", fill=(255, 230, 80), font=_f(11))
    p3 = os.path.join(out_dir, 'v2_acercamientos.png')
    mos.save(p3)
    return [p1, p2, p3], filas


def _envolver(d, txt, f, ancho):
    lineas, actual = [], ''
    for pal in txt.split(' '):
        prueba = f'{actual} {pal}'.strip()
        if actual and d.textlength(prueba, font=f) > ancho:
            lineas.append(actual)
            actual = pal
        else:
            actual = prueba
    return lineas + [actual]
