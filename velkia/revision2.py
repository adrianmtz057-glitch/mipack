"""Imágenes de revisión: colocación final y asiento de las construcciones sobre el terreno.

Genera (prefijo = versión):
  <p>_mapa_construcciones.png     mapa sombreado (terreno ya asentado) + tabla de colocación
  <p>_comparacion_referencia.png  mapa de referencia y generado con el mismo encuadre
  <p>_acercamientos.png           acercamientos de las 8 construcciones y los 3 sitios reservados
  <p>_perfiles.png                cortes por cada construcción (terreno antes/después, suelo y techo)
y devuelve la lista de filas de la tabla.  Con Yfino (resolución de bloque) los acercamientos,
los perfiles y la tabla de flotación/enterramiento salen de la malla de 1 bloque.
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
            notas=(), prefijo='v2', tipo=None, Yfino=None, Yfino0=None, titulo=None):
    """Y0: terreno antes del asiento; Ym: terreno asentado (cotas absolutas, malla de 1024).
    tipo: agua y lava (agua.superficie) para pintar.  Yfino/Yfino0: terreno asentado y antes del
    asiento a resolución de bloque (8192²)."""
    os.makedirs(out_dir, exist_ok=True)
    n = Ym.shape[0]
    dx = N / n
    base = relief_image(Ym, dx, water=ocean | lagos)
    if tipo is not None:
        from .agua import pintar
        base = Image.fromarray(np.clip(pintar(base, tipo), 0, 255).astype(np.uint8))
    W = n
    filas = []
    for k, o in enumerate(colocaciones):
        m = o['maps']
        zz, xx = np.nonzero(m['foot'])
        ci = np.clip(((zz + m['z0']) / dx).astype(int), 0, n - 1)
        cj = np.clip(((xx + m['x0']) / dx).astype(int), 0, n - 1)
        v0 = Y0[ci, cj] if Yfino0 is None else Yfino0[zz + m['z0'], xx + m['x0']]
        inf = o.get('informe', {})
        dp = o.get('despues', {})
        filas.append({
            'n': k + 1, 'nombre': o['nombre'], 'shift': o['shift'], 'dy': o['dy'],
            'x': int(m['x0'] + xx.mean()), 'z': int(m['z0'] + zz.mean()),
            'terr': (float(v0.min()), float(np.median(v0)), float(v0.max())),
            'corte': inf.get('corte_max', 0.0), 'relleno': inf.get('relleno_max', 0.0),
            'flot': dp.get('flotacion_max', 0.0), 'ent': dp.get('enterramiento_max', 0.0),
            'talud': o['talud'][1] if 'talud' in o else inf.get('pendiente_max_banda', 0.0),
        })

    # ------------------------------------------------ 1: mapa + tabla
    panel = 820
    img = Image.new('RGB', (W + panel, max(W, 1000)), (24, 26, 30))
    img.paste(base, (0, 0))
    d = ImageDraw.Draw(img)
    if tipo is None:
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
    for nm, (pxy, rad, _t) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        r = rad / dx
        d.ellipse([bx / dx - r, bz / dx - r, bx / dx + r, bz / dx + r], outline=(255, 230, 80), width=2)
        d.text((bx / dx + r + 3, bz / dx - 8), RES_NOMBRE[nm][0], fill=(255, 230, 80), font=_f(16, True))
    x0 = W + 18
    d.text((x0, 14), titulo or f'Velkia {prefijo} (1024², 8 bloques/celda) — colocación y asiento',
           fill=(240, 240, 240), font=_f(19, True))
    y = 46
    hdr = ['#', 'construcción', 'mov. (x,z)', 'dy', 'terreno antes', 'corte/rell.', 'borde después', 'talud p99']
    xs = [0, 18, 190, 280, 325, 465, 560, 700]
    for t, xo in zip(hdr, xs):
        d.text((x0 + xo, y), t, fill=(150, 200, 255), font=_f(12, True))
    y += 20
    for fl in filas:
        vals = [str(fl['n']), fl['nombre'], f"{fl['shift'][0]:+d},{fl['shift'][1]:+d}", f"{fl['dy']:+d}",
                f"{fl['terr'][0]:.0f}/{fl['terr'][1]:.0f}/{fl['terr'][2]:.0f}",
                f"{fl['corte']:.0f}/{fl['relleno']:.0f}", f"flota {fl['flot']:.0f} · ent. {fl['ent']:.0f}",
                f"1:{1 / max(fl['talud'], 1e-3):.1f}" if fl['talud'] > 0 else '-']
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
    p1 = os.path.join(out_dir, f'{prefijo}_mapa_construcciones.png')
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
    dc.text((W + 30, 10), f'Velkia {prefijo} generado (terreno asentado)', fill=(240, 240, 240), font=_f(16, True))
    for k, poi in enumerate(POI_DE):
        bx, bz = px2b(*POIS[poi])
        cx, cz = bx / N * W, bz / N * W + 40
        dc.ellipse([cx - 10, cz - 10, cx + 10, cz + 10], outline=(255, 255, 0), width=3)
        dc.text((cx + 12, cz - 9), str(k + 1), fill=(255, 255, 0), font=_f(16, True))
    for nm, (pxy, rad, _t) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        cx, cz = bx / N * W, bz / N * W + 40
        dc.ellipse([cx - 8, cz - 8, cx + 8, cz + 8], outline=(255, 150, 0), width=2)
        dc.text((cx + 10, cz - 9), RES_NOMBRE[nm][0], fill=(255, 150, 0), font=_f(15, True))
    p2 = os.path.join(out_dir, f'{prefijo}_comparacion_referencia.png')
    cmp_.save(p2)

    # ------------------------------------------------ 3: acercamientos
    tile = 330
    items = [(fl['nombre'], fl['x'], fl['z'], colocaciones[i]['maps'], fl) for i, fl in enumerate(filas)]
    for nm, (pxy, rad, _t) in RESERVADOS.items():
        bx, bz = px2b(*pxy)
        items.append((RES_NOMBRE[nm], bx, bz, None, None))
    cols = 4
    rows = (len(items) + cols - 1) // cols
    mos = Image.new('RGB', (cols * tile, rows * (tile + 34)), (24, 26, 30))
    dm = ImageDraw.Draw(mos)
    for k, (nombre, cxb, czb, m, fl) in enumerate(items):
        half = 900.0 if (m is None or Yfino is None) else 0.5 * max(m['foot'].shape) + 260.0
        o = colocaciones[k] if fl else None
        if Yfino is not None:
            crop, (b0, a0, sc) = _vista_fina(Yfino, cxb, czb, half, tile, o, tipo, dx)
            esc = 1.0                               # coordenadas de dibujo en bloques
        else:
            a0, a1 = int(max(0, (czb - half) / dx)), int(min(n, (czb + half) / dx))
            b0, b1 = int(max(0, (cxb - half) / dx)), int(min(n, (cxb + half) / dx))
            crop = base.crop((b0, a0, b1, a1)).resize((tile, tile), Image.BICUBIC)
            sc = tile / (b1 - b0)
            esc = dx
        dd = ImageDraw.Draw(crop)
        if m is not None:
            px, pz = _contorno(m, esc)
            for x, z in zip(px, pz):
                dd.point(((x - b0) * sc, (z - a0) * sc), fill=(255, 40, 40))
        for xy, col in [(rio_xy, (70, 140, 255))] + [(v, (110, 190, 255)) for v in afluentes.values()]:
            pts = [((p[0] / esc - b0) * sc, (p[1] / esc - a0) * sc) for p in xy
                   if abs(p[0] - cxb) < half and abs(p[1] - czb) < half]
            if len(pts) > 1 and tipo is None:
                dd.line(pts, fill=col, width=2)
        if m is None:
            for nm, (pxy, rad, tipo_r) in RESERVADOS.items():
                bx, bz = px2b(*pxy)
                r = rad / esc * sc
                ccx, ccz = (bx / esc - b0) * sc, (bz / esc - a0) * sc
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
    p3 = os.path.join(out_dir, f'{prefijo}_acercamientos.png')
    mos.save(p3)
    paths = [p1, p2, p3]
    if Yfino is not None:
        paths.append(_perfiles(Yfino, Yfino0, colocaciones, os.path.join(out_dir, f'{prefijo}_perfiles.png')))
    return paths, filas


def _vista_fina(Yf, cx, cz, half, tile, o, tipo, dx):
    """Acercamiento desde la malla de bloque, con los edificios encima (gris)."""
    M = Yf.shape[0]
    a0, a1 = int(max(0, cz - half)), int(min(M, cz + half))
    b0, b1 = int(max(0, cx - half)), int(min(M, cx + half))
    f = max(1, int(round((b1 - b0) / 600)))
    a1 = a0 + (a1 - a0) // f * f
    b1 = b0 + (b1 - b0) // f * f
    win = np.asarray(Yf[a0:a1, b0:b1], np.float64)
    vis = win.copy()
    edif = np.zeros(win.shape, bool)
    if o is not None:
        m = o['maps']
        zz, xx = np.nonzero(m['built'])
        gz, gx = zz + m['z0'] - a0, xx + m['x0'] - b0
        ok = (gz >= 0) & (gz < win.shape[0]) & (gx >= 0) & (gx < win.shape[1])
        top = m['top'][zz, xx].astype(np.float64) + o['dy']
        vis[gz[ok], gx[ok]] = np.maximum(vis[gz[ok], gx[ok]], top[ok])
        edif[gz[ok], gx[ok]] = True
        # suelo propio del schematic (losas, terrazas): se pega con la construcción
        zz, xx = np.nonzero(m['foot'] & (m['ground'] > -900))
        gz, gx = zz + m['z0'] - a0, xx + m['x0'] - b0
        ok = (gz >= 0) & (gz < win.shape[0]) & (gx >= 0) & (gx < win.shape[1])
        gr = m['ground'][zz, xx].astype(np.float64) + o['dy']
        vis[gz[ok], gx[ok]] = np.maximum(vis[gz[ok], gx[ok]], gr[ok])
    L, W = vis.shape
    vs = vis.reshape(L // f, f, W // f, f).max(axis=(1, 3))
    es = edif.reshape(L // f, f, W // f, f).any(axis=(1, 3))
    from .render import hypso_color
    col = hypso_color(vs - SEA)
    col[es] = (175, 165, 155)
    if tipo is not None:
        ti = tipo[np.clip(((np.arange(a0, a1, f) + f / 2) / dx).astype(int), 0, tipo.shape[0] - 1)][:,
                  np.clip(((np.arange(b0, b1, f) + f / 2) / dx).astype(int), 0, tipo.shape[1] - 1)]
        agua = (ti > 0) & (ti != 4) & ~es & (vs <= SEA + 400)
        lava = ti == 4
        col[agua] = col[agua] * 0.3 + np.array([50, 110, 215]) * 0.7
        col[lava] = col[lava] * 0.3 + np.array([235, 85, 20]) * 0.7
    col[vs < SEA] = (60, 110, 190)
    im = relief_image(vs, float(f), colors=col)
    sc = tile / (b1 - b0)
    return im.resize((tile, tile), Image.LANCZOS), (b0, a0, sc)


def _perfiles(Yf, Yf0, colocaciones, path, ancho=520, alto=210):
    """Corte O-E por el centro de cada construcción: terreno antes (gris), terreno asentado
    (marrón), suelo pedido (rojo) y techo de lo construido (negro)."""
    cols = 2
    filas = (len(colocaciones) + 1) // 2
    img = Image.new('RGB', (cols * ancho, filas * (alto + 26)), (250, 250, 248))
    d = ImageDraw.Draw(img)
    M = Yf.shape[0]
    for k, o in enumerate(colocaciones):
        m = o['maps']
        zz, xx = np.nonzero(m['foot'])
        zc = int(np.median(zz))
        x0g, x1g = m['x0'] - 150, m['x0'] + m['foot'].shape[1] + 150
        xs = np.arange(max(0, x0g), min(M, x1g))
        zg = m['z0'] + zc
        t1 = np.asarray(Yf[zg, xs], np.float64)
        t0 = np.asarray(Yf0[zg, xs], np.float64) if Yf0 is not None else t1
        rx = xs - m['x0']
        dentro = (rx >= 0) & (rx < m['foot'].shape[1])
        ref = np.full(xs.size, np.nan)
        top = np.full(xs.size, np.nan)
        fila_f = m['foot'][zc]
        ii = rx[dentro]
        ref[dentro] = np.where(fila_f[ii], o['ref'][zc, ii] + o['dy'], np.nan)
        topv = m['top'][zc, ii].astype(np.float64)
        top[dentro] = np.where(m['built'][zc, ii], topv + o['dy'], np.nan)
        vals = np.r_[t0, t1, ref[np.isfinite(ref)], top[np.isfinite(top)]]
        lo, hi = float(np.nanmin(vals)) - 4, float(np.nanmax(vals)) + 4
        ox, oy = (k % cols) * ancho, (k // cols) * (alto + 26)
        pw, ph = ancho - 50, alto - 30
        # misma escala en x y en y si cabe (para ver la pendiente real del talud)
        sx = pw / xs.size
        sy = min(ph / (hi - lo), sx * 4)
        def P(i, v):
            return ox + 40 + i * sx, oy + 26 + ph - (v - lo) * sy
        d.text((ox + 8, oy + 4), f"{k + 1}. {o['nombre']} (z={zg}, escala vertical ×{sy / sx:.1f})", fill=(20, 20, 20), font=_f(12, True))
        for serie, col, w in ((t0, (160, 160, 160), 1), (t1, (140, 90, 40), 2)):
            d.line([P(i, v) for i, v in enumerate(serie)], fill=col, width=w)
        for serie, col in ((top, (20, 20, 20)), (ref, (220, 30, 30))):
            pts = [P(i, v) for i, v in enumerate(serie) if np.isfinite(v)]
            for p in pts:
                d.point(p, fill=col)
        for yv in range(int(lo // 10 * 10), int(hi) + 1, 10 if hi - lo < 120 else 50):
            _, py = P(0, yv)
            if oy + 20 < py < oy + 26 + ph:
                d.text((ox + 2, py - 6), str(yv), fill=(120, 120, 120), font=_f(9))
    img.save(path)
    return path


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
