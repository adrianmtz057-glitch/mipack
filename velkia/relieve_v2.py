"""Relieve de la v2 a 1 bloque (lienzo aprobado).

  * volcán: isla redonda separada por un canal de mar; caldera llena de lava; bocas pequeñas en
    los flancos con caídas de lava ramificadas que no salen del volcán ni tocan el agua;
  * mura: agujas negras muy altas y delgadas; lago morado (manantial);
  * domos de piedra (Kata Tjuta): grupos de domos redondeados de paredes empinadas con pasillos
    de arena entre ellos;
  * dunas transversales en el desierto central (viento OSO -> ENE);
  * charcas: Jardines, cunas de agua de las montañas, pozas del salar (con palmeras).
Todas las funciones trabajan sobre Y (float32, bloques) y respetan 'protegido' (construcciones).
"""
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from .etapa4 import _densificar, cauce
from .layout import N, SEA
from .noise import spectral_noise
from .volcan import _trazar
from .zonas_v1 import Z, R_ISLA

NG = 1024
DX = N / NG


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _subir(a, z0, z1, x0, x1, order=1):
    """Muestrea un campo de la malla gruesa en la ventana de bloques [z0:z1, x0:x1]."""
    zz = (np.arange(z0, z1) + 0.5) / DX - 0.5
    xx = (np.arange(x0, x1) + 0.5) / DX - 0.5
    FZ, FX = np.meshgrid(zz, xx, indexing='ij')
    return ndi.map_coordinates(np.asarray(a, np.float32), [FZ, FX], order=order, mode='nearest')


def _ventana(cx, cz, r):
    return (max(0, int(cz - r)), min(N, int(cz + r)), max(0, int(cx - r)), min(N, int(cx + r)))


def distancia_rios(rios, ng=NG):
    """Distancia (bloques) al eje de río más cercano, en la malla gruesa."""
    m = np.zeros((ng, ng), bool)
    for r in rios:
        xy, = _densificar(r['xy'], 4.0)
        m[np.clip((xy[:, 1] / DX).astype(int), 0, ng - 1), np.clip((xy[:, 0] / DX).astype(int), 0, ng - 1)] = True
    return ndi.distance_transform_edt(~m) * DX


# ===================================================================== volcán
def canal_volcan(Y, caldera, protegido):
    """Canal de mar en anillo alrededor de la isla del volcán (R_ISLA .. R_ISLA+170)."""
    cx, cz = caldera[0], caldera[1]
    z0, z1, x0, x1 = _ventana(cx, cz, R_ISLA + 600)
    zz, xx = np.mgrid[z0:z1, x0:x1]
    rv = np.hypot(xx + 0.5 - cx, zz + 0.5 - cz)
    ang = np.arctan2(zz + 0.5 - cz, xx + 0.5 - cx)
    rc = R_ISLA + 85.0 + 12.0 * np.sin(3 * ang + 1.0) + 7.0 * np.sin(7 * ang)
    dist = np.abs(rv - rc)
    tope = SEA - 10.0 + np.maximum(0.0, dist - 45.0) * 0.32
    sub = Y[z0:z1, x0:x1]
    pr = protegido[z0:z1, x0:x1]
    Y[z0:z1, x0:x1] = np.where(pr, sub, np.minimum(sub, tope))


def lava_volcan(Y, WL, FL, d, z, mar, protegido, seed=5):
    """Caldera llena de lava y bocas pequeñas con caídas de lava ramificadas.  Devuelve
    (permitir, n_bocas, n_caidas)."""
    permitir = np.zeros((N, N), bool)
    cx, cz, cr = (float(v) for v in d['caldera'])
    # caldera: lago de lava hundido al fondo
    ll = ndi.zoom(d['lago_lava'].astype(np.float32), DX, order=1) > 0.5
    if ll.any():
        nv = int(np.floor(np.percentile(Y[ll], 30)))
        Y[ll] = np.minimum(Y[ll], nv - 2)
        WL[ll] = nv
        FL[ll] = 2
    # caídas desde las bocas (trazadas en la malla gruesa, como en el lienzo)
    h = d['h']
    rng = np.random.default_rng(seed)
    dmar = ndi.distance_transform_edt(~mar[::8, ::8]) * DX
    caidas = []
    bocas = []
    for k, ang in enumerate(np.deg2rad([20, 55, 95, 130, 165, 200, 250, 300, 335])):
        r0 = rng.uniform(cr + 60, 520)
        ini = (cx + r0 * np.cos(ang), cz + r0 * np.sin(ang))
        bocas.append(ini)
        pila = [(ini, 0, 4.0)]
        while pila:
            p0, nivel, ancho = pila.pop()
            pi, pj = _trazar(h, DX, p0, rng=np.random.default_rng(k * 31 + nivel * 7 + len(caidas)),
                             remonta=2.0, ruido=0.35)
            p = np.c_[(pj + 0.5) * DX, (pi + 0.5) * DX]
            rv = np.hypot(p[:, 0] - cx, p[:, 1] - cz)
            corte = np.nonzero((h[pi, pj] < 8) | (z[pi, pj] != Z['volcan']) | (rv > R_ISLA - 150) |
                               (dmar[pi, pj] < 80))[0]
            if corte.size:
                p = p[:corte[0]]
            if len(p) < 3:
                continue
            caidas.append((p, ancho))
            if nivel < 2:
                for f in (0.3, 0.6):
                    i = int(f * (len(p) - 1))
                    tg = p[min(i + 3, len(p) - 1)] - p[max(i - 3, 0)]
                    nr = np.array([-tg[1], tg[0]]) / (np.hypot(*tg) + 1e-9)
                    lado = 1 if rng.random() < 0.5 else -1
                    pila.append(((p[i][0] + lado * nr[0] * 70, p[i][1] + lado * nr[1] * 70), nivel + 1, ancho * 0.75))
    # bocas: conito con cráter de lava
    for bx, bz in bocas:
        z0, z1, x0, x1 = _ventana(bx, bz, 20)
        zz, xx = np.mgrid[z0:z1, x0:x1]
        r = np.hypot(xx + 0.5 - bx, zz + 0.5 - bz)
        g = float(np.median(Y[z0:z1, x0:x1]))
        cono = g + 7.0 * np.clip(1 - r / 16.0, 0, 1) ** 1.2
        sub = Y[z0:z1, x0:x1]
        sub = np.where(r < 16, np.maximum(sub, cono), sub)
        crat = r < 3.5
        top = int(np.floor(g + 4.5))
        sub = np.where(crat, np.minimum(sub, top - 2), sub)
        Y[z0:z1, x0:x1] = sub
        WL[z0:z1, x0:x1] = np.where(crat, top, WL[z0:z1, x0:x1])
        FL[z0:z1, x0:x1] = np.where(crat, 2, FL[z0:z1, x0:x1])
    # coladas: canal estrecho con lava al nivel del terreno que nunca sube; donde cae, cascada de lava
    for p, ancho in caidas:
        xy, = _densificar(p, 2.0)
        if len(xy) < 6:
            continue
        iz = np.clip(xy[:, 1].astype(int), 0, N - 1)
        ix = np.clip(xy[:, 0].astype(int), 0, N - 1)
        lv = np.minimum.accumulate(np.floor(ndi.median_filter(Y[iz, ix], 5, mode='nearest')))
        lvc = lv.copy()
        casc = np.zeros(len(xy), bool)
        for k in np.nonzero(np.diff(lv) < -3)[0]:
            lvc[k + 1:k + 3] = lv[k]
            casc[max(0, k - 2):k + 6] = True
        cauce(Y, WL, FL, xy, np.full(len(xy), ancho), lvc, 1.5, fluido=2, seco=protegido, sin_orilla=casc, mar=mar)
        for k in np.nonzero(casc)[0]:
            x, zc = xy[k]
            permitir[max(0, int(zc) - 8):int(zc) + 8, max(0, int(x) - 8):int(x) + 8] = True
    return permitir, len(bocas), len(caidas)


# ===================================================================== mura
def agujas_mura(Y, zb, z, h, drios, protegido, lago_c=(6650, 2250), n_max=70, seed=12):
    """Agujas negras muy altas y delgadas sobre las montañas de la mura (desfiladero de la muerte)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:NG, 0:NG]
    Xc, Zc = (xx + 0.5) * DX, (yy + 0.5) * DX
    dcosta = ndi.distance_transform_edt(z != 0) * DX
    apto = (z == Z['mura']) & (h > 90) & (drios > 140) & (dcosta > 200) & \
        (np.hypot(Xc - lago_c[0], Zc - lago_c[1]) > 380)
    cand = np.argwhere(apto)
    peso = h[apto] ** 2
    peso = peso / peso.sum()
    puestas = []
    for idx in rng.choice(len(cand), size=min(len(cand), 3000), replace=False, p=peso):
        i, j = cand[idx]
        x, zc = (j + 0.5) * DX + rng.uniform(-4, 4), (i + 0.5) * DX + rng.uniform(-4, 4)
        if all(np.hypot(x - a, zc - b) > 55 for a, b, _, _ in puestas):
            R0 = rng.uniform(7, 15)
            H = rng.uniform(80, 200)
            puestas.append((x, zc, R0, H))
        if len(puestas) >= n_max:
            break
    for x, zc, R0, H in puestas:
        z0, z1, x0, x1 = _ventana(x, zc, 2.2 * R0 + 4)
        zz, xx = np.mgrid[z0:z1, x0:x1]
        dxx, dzz = xx + 0.5 - x, zz + 0.5 - zc
        r = np.hypot(dxx, dzz)
        th = np.arctan2(dzz, dxx)
        fr = 1.0 + 0.18 * np.sin(3 * th + rng.uniform(0, 6)) + 0.1 * np.sin(5 * th + rng.uniform(0, 6))
        rn = r / (R0 * fr)
        sub = Y[z0:z1, x0:x1]
        g = float(np.percentile(sub, 20))
        H = min(H, 500.0 - g)
        aguja = H * np.clip(1 - rn, 0, 1) ** 0.6
        falda = 0.22 * H * np.clip(1 - rn / 2.2, 0, 1) ** 1.6
        forma = np.maximum(aguja, falda)
        pr = protegido[z0:z1, x0:x1] | (forma <= 0)           # solo dentro de la aguja
        Y[z0:z1, x0:x1] = np.where(pr, sub, np.maximum(sub, g + forma))
    return len(puestas)


def mancha_lago(cx, cz, ra, aspecto, ruido_g, forma=0.35):
    """Máscara (ventana) de un lago de contorno irregular: (z0, x0, máscara)."""
    z0, z1, x0, x1 = _ventana(cx, cz, ra * 1.6 + 8)
    zz, xx = np.mgrid[z0:z1, x0:x1]
    rr = np.hypot(xx + 0.5 - cx, (zz + 0.5 - cz) * aspecto) / ra
    return z0, x0, rr + forma * _subir(ruido_g, z0, z1, x0, x1) < 1.0


# ===================================================================== charcas
def charcas(Y, WL, FL, mascara, prof=2.0, dique=False, fluido=1, min_celdas=12):
    """Llena de agua cada mancha conexa de 'mascara' a un nivel plano.  Devuelve {etiqueta: nivel}.
    dique=False (terreno llano: salar, Jardines): nivel 1 bajo el borde más bajo, sin muros.
    dique=True (laderas: lago morado, cunas de agua): nivel = percentil 40 del suelo de la mancha;
    solo se inunda lo que está cerca de ese nivel (-8..+10) y el borde que quede bajo sube a nivel+1."""
    zs, xs = np.nonzero(mascara)
    if zs.size == 0:
        return {}
    z0, z1 = max(0, zs.min() - 4), min(N, zs.max() + 5)
    x0, x1 = max(0, xs.min() - 4), min(N, xs.max() + 5)
    m = mascara[z0:z1, x0:x1]
    sub = Y[z0:z1, x0:x1].copy()
    wl = WL[z0:z1, x0:x1].copy()
    fl = FL[z0:z1, x0:x1].copy()
    lab, nl = ndi.label(m)
    if nl == 0:
        return {}
    idx = np.arange(1, nl + 1)
    tam = ndi.sum(np.ones_like(lab), lab, idx)
    out = {}
    if dique:
        for i in idx[tam >= min_celdas]:
            c = lab == i
            L = float(np.floor(np.percentile(sub[c], 40)))
            agua = c & (sub <= L + 10) & (sub >= L - 8)
            agua = ndi.binary_opening(agua, iterations=2)
            lb, nb = ndi.label(agua)
            if nb == 0:
                continue
            agua = lb == (1 + int(np.argmax(ndi.sum(agua, lb, np.arange(1, nb + 1)))))
            dist = ndi.distance_transform_edt(agua)
            sub = np.where(agua, np.minimum(sub, L - 1.0 - np.minimum(prof - 1.0, dist / 3.0)), sub)
            borde = ndi.binary_dilation(agua, iterations=3) & ~agua
            sub = np.where(borde & (sub < L + 1), L + 1, sub)
            wl = np.where(agua, np.int16(L), wl)
            fl = np.where(agua, fluido, fl)
            out[int(i)] = L
    else:
        anillo_l = ndi.grey_dilation(lab, size=5)
        anillo_l = np.where(m, 0, anillo_l)
        niv = np.floor(np.asarray(ndi.minimum(sub, anillo_l, idx))) - 1.0
        niv = np.where(tam >= min_celdas, niv, np.nan)
        L = np.r_[np.nan, niv][lab]
        agua = m & np.isfinite(L)
        dist = ndi.distance_transform_edt(agua)
        sub = np.where(agua, np.minimum(sub, L - 1.0 - np.minimum(prof - 1.0, dist / 3.0)), sub)
        wl = np.where(agua, np.nan_to_num(L, nan=0).astype(np.int16), wl)
        fl = np.where(agua, fluido, fl)
        out = {int(i): float(v) for i, v in zip(idx, niv) if np.isfinite(v)}
    Y[z0:z1, x0:x1] = sub
    WL[z0:z1, x0:x1] = wl
    FL[z0:z1, x0:x1] = fl
    return out


def lagos_v2(Y, WL, FL, d, z, zb, drios, protegido, seed=5):
    """Lago morado de la mura, charcos de los Jardines, cunas de agua de las montañas y pozas del
    salar (15 % menos que la primera versión).  Devuelve (niveles, máscara_pozas_salar, info)."""
    rng = np.random.default_rng(seed)
    h = d['h']
    ruido_g = spectral_noise((NG, NG), 3.2, 43, kmax=40.0)
    info = {}
    niveles = {}
    # lago morado: manantial en la meseta de la mura
    z0, x0, m = mancha_lago(6650, 2250, 210, 1.3, ruido_g)
    big = np.zeros((N, N), bool)
    big[z0:z0 + m.shape[0], x0:x0 + m.shape[1]] = m
    big &= ~protegido
    nv = charcas(Y, WL, FL, big, prof=6.0, dique=True)
    niveles['lago_morado'] = max(nv.values()) if nv else None
    info['lago_morado'] = niveles['lago_morado']
    del big
    # charcos de los Jardines (en el fondo, lejos de los ríos)
    jard = (z == Z['jardines']) & (drios > 80)
    cand = np.argwhere(jard)
    mj = np.zeros((N, N), bool)
    for _ in range(14):
        i, j = cand[rng.integers(len(cand))]
        z0, x0, m = mancha_lago((j + 0.5) * DX, (i + 0.5) * DX, rng.uniform(30, 70), 1.0, ruido_g, 0.15)
        mj[z0:z0 + m.shape[0], x0:x0 + m.shape[1]] |= m
    mj &= (zb == Z['jardines']) & ~protegido & (FL == 0)
    info['charcos_jardines'] = len(charcas(Y, WL, FL, mj, prof=2.5))
    del mj
    # cunas de agua: hondonadas reales casi planas de la cordillera, lejos de los ríos
    mont = (z == Z['montanas']) & (h > 140)
    hondo = ndi.gaussian_filter(h, 6) - h
    gz, gx = np.gradient(ndi.gaussian_filter(h, 2), DX)
    apto = mont & (np.hypot(gz, gx) < 0.25) & (hondo > 1.0) & (drios > 200)
    pts = []
    for idx in np.argsort(-np.where(apto, hondo, -1e9).ravel()):
        i, j = divmod(int(idx), NG)
        if not apto[i, j] or len(pts) >= 8:
            break
        if all(np.hypot(i - a, j - b) > 45 for a, b in pts):
            pts.append((i, j))
    mc = np.zeros((N, N), bool)
    for i, j in pts:
        z0, x0, m = mancha_lago((j + 0.5) * DX, (i + 0.5) * DX, rng.uniform(40, 60), 1.0, ruido_g, 0.25)
        mc[z0:z0 + m.shape[0], x0:x0 + m.shape[1]] |= m
    mc &= (zb == Z['montanas']) & ~protegido & (FL == 0)
    info['cunas_de_agua'] = len(charcas(Y, WL, FL, mc, prof=4.0, dique=True))
    del mc
    # pozas del salar: el mismo umbral de ruido que el lienzo (85 % del área anterior)
    rp = spectral_noise((NG, NG), 2.0, 77, kmin=40.0)
    sal = z == Z['salar']
    dentro = sal & ~ndi.binary_dilation(~sal, iterations=3)
    area = ((rp > -0.35) & dentro).sum() * 0.85
    umbral = np.sort(rp[dentro])[::-1][int(area)]
    pozas = np.zeros((N, N), bool)
    zs, xs = np.nonzero(dentro)
    za, zb_, xa, xb = zs.min() * 8, (zs.max() + 1) * 8, xs.min() * 8, (xs.max() + 1) * 8
    for r0 in range(za, zb_, 1024):
        r1 = min(zb_, r0 + 1024)
        pozas[r0:r1, xa:xb] = _subir(rp, r0, r1, xa, xb) > umbral
    sal_b = zb == Z['salar']
    sal_b = sal_b & ~ndi.binary_dilation(~sal_b, iterations=20)
    pozas &= sal_b & ~protegido & (FL == 0)
    info['pozas_salar'] = len(charcas(Y, WL, FL, pozas, prof=2.0, min_celdas=20))
    return niveles, pozas, info


# ===================================================================== domos y dunas
def domos(Y, zb, z, drios, protegido, seed=31):
    """Grupos de domos redondeados (bornhardts tipo Kata Tjuta) con pasillos de arena."""
    rng = np.random.default_rng(seed)
    dmar = ndi.distance_transform_edt(z != 0) * DX
    prot_g = protegido[4::8, 4::8]
    dprot = ndi.distance_transform_edt(~prot_g) * DX
    apto = (z == Z['domos']) & (dmar > 220) & (drios > 170) & (dprot > 220)
    cand = np.argwhere(apto)
    if len(cand) == 0:
        return 0, np.zeros((N, N), bool)
    # centros de grupo lejos entre sí
    grupos = []
    for idx in rng.permutation(len(cand)):
        i, j = cand[idx]
        p = ((j + 0.5) * DX, (i + 0.5) * DX)
        if all(np.hypot(p[0] - a, p[1] - b) > 900 for a, b in grupos):
            grupos.append(p)
        if len(grupos) >= 4:
            break
    domos_l = []
    for gx, gz in grupos:
        for _ in range(60):
            a = rng.uniform(70, 165)
            b = a * rng.uniform(0.55, 0.9)
            x = gx + rng.normal(0, 260)
            zc = gz + rng.normal(0, 260)
            i, j = int(np.clip(zc / DX, 0, NG - 1)), int(np.clip(x / DX, 0, NG - 1))
            if not apto[i, j]:
                continue
            if all(np.hypot(x - x2, zc - z2) > 0.85 * (a + a2) + 28 for x2, z2, a2, _, _, _ in domos_l):
                domos_l.append((x, zc, a, b, rng.uniform(0, np.pi), a * rng.uniform(0.55, 0.85)))
            if sum(1 for d_ in domos_l if np.hypot(d_[0] - gx, d_[1] - gz) < 900) >= 12:
                break
    alto_dom = np.zeros((N, N), bool)
    for x, zc, a, b, th, H in domos_l:
        z0, z1, x0, x1 = _ventana(x, zc, a * 1.25 + 6)
        zz, xx = np.mgrid[z0:z1, x0:x1]
        dxx, dzz = xx + 0.5 - x, zz + 0.5 - zc
        u = dxx * np.cos(th) + dzz * np.sin(th)
        v = -dxx * np.sin(th) + dzz * np.cos(th)
        ang = np.arctan2(v / b, u / a)
        q = np.hypot(u / a, v / b) * (1 + 0.05 * np.sin(4 * ang + th * 3) + 0.03 * np.sin(9 * ang))
        perfil = H * np.clip(1 - np.clip(q, 0, 1) ** 2.4, 0, 1) ** 0.6
        surcos = 3.0 * np.abs(np.sin(11 * ang + 2 * th)) * np.clip(q, 0, 1) * (q < 1)
        sub = Y[z0:z1, x0:x1]
        g = float(np.percentile(sub, 15))
        alto = g + np.maximum(perfil - surcos, 0)
        pr = protegido[z0:z1, x0:x1] | (perfil <= 0)          # solo dentro del domo
        nuevo = np.where(pr, sub, np.maximum(sub, alto))
        alto_dom[z0:z1, x0:x1] |= nuevo > g + 6
        Y[z0:z1, x0:x1] = nuevo
    return len(domos_l), alto_dom


def dunas(Y, zb, z, drios, protegido, viento_deg=-22.5, seed=9):
    """Dunas transversales asimétricas (barlovento suave, sotavento empinado) en el desierto central."""
    zon = z == Z['dunas']
    borde = ndi.distance_transform_edt(zon) * DX
    prot_g = protegido[4::8, 4::8]
    dprot = ndi.distance_transform_edt(~prot_g) * DX
    gz, gx = np.gradient(ndi.gaussian_filter(Y[4::8, 4::8].astype(np.float32), 2), DX)
    llano = 1.0 - _sstep((np.hypot(gz, gx) - 0.12) / 0.15)
    amp = 13.0 * (0.55 + 0.45 * spectral_noise((NG, NG), 3.0, seed + 1)) * _sstep(borde / 350.0) * \
        _sstep((dprot - 90.0) / 160.0) * _sstep((drios - 70.0) / 120.0) * llano
    amp = np.clip(amp, 0, None)
    warp = spectral_noise((NG, NG), 3.4, seed + 2) * 55.0
    rompe = 0.65 + 0.35 * spectral_noise((NG, NG), 2.4, seed + 3, kmin=12.0)
    a = np.deg2rad(viento_deg)
    wx, wz = np.cos(a), np.sin(a)
    zs, xs = np.nonzero(amp > 0.3)
    if zs.size == 0:
        return 0.0
    z0, z1 = zs.min() * 8, (zs.max() + 1) * 8
    x0, x1 = xs.min() * 8, (xs.max() + 1) * 8
    for r0 in range(z0, z1, 512):
        r1 = min(z1, r0 + 512)
        zz, xx = np.mgrid[r0 - 8:r1 + 8, x0:x1].astype(np.float32)
        u = xx * wx + zz * wz
        A = _subir(amp, r0 - 8, r1 + 8, x0, x1) * _subir(rompe, r0 - 8, r1 + 8, x0, x1)
        lam = 175.0
        p = np.mod((u + _subir(warp, r0 - 8, r1 + 8, x0, x1)) / lam, 1.0)
        perfil = np.where(p < 0.72, p / 0.72, (1.0 - p) / 0.28)
        hd = ndi.gaussian_filter(A * perfil, 2.0)[8:-8]
        sub = Y[max(0, r0):r1, x0:x1]
        hd = hd[:sub.shape[0]]
        pr = protegido[max(0, r0):r1, x0:x1]
        Y[max(0, r0):r1, x0:x1] = np.where(pr, sub, sub + hd)
    return float(amp.max())


# ===================================================================== palmeras
TRONCO = 'minecraft:jungle_log[axis=y]'
HOJA = 'minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]'


def palmeras(Y, FL, zona_sal, agua, seed=7, paso=18, prob=0.35):
    """Palmeras en tierra del salar cerca de las pozas.  Devuelve (lista de bloques, n)."""
    rng = np.random.default_rng(seed)
    dist = np.full((N, N), 1e9, np.float32)
    zs, xs = np.nonzero(zona_sal)
    if zs.size == 0:
        return [], 0
    z0, z1, x0, x1 = zs.min(), zs.max() + 1, xs.min(), xs.max() + 1
    dist[z0:z1, x0:x1] = ndi.distance_transform_edt(~agua[z0:z1, x0:x1])
    apto = zona_sal & (FL == 0) & (dist >= 2) & (dist <= 9)
    bloques = []
    n = 0
    for gz in range(z0, z1, paso):
        for gx in range(x0, x1, paso):
            sub = apto[gz:gz + paso, gx:gx + paso]
            if not sub.any() or rng.random() > prob:
                continue
            cz, cx = np.argwhere(sub)[rng.integers(sub.sum())]
            x, z = gx + cx, gz + cz
            y0 = int(Y[z, x]) + 1
            H = int(rng.integers(6, 10))
            lx, lz = [(1, 0), (-1, 0), (0, 1), (0, -1)][rng.integers(4)]
            px, pz = x, z
            for k in range(H):
                if k == H // 2 + 1:                    # tronco algo inclinado
                    px, pz = px + lx, pz + lz
                bloques.append((px, y0 + k, pz, TRONCO))
            ty = y0 + H - 1
            bloques.append((px, ty + 1, pz, HOJA))
            for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                largo = 3 if ddx == 0 or ddz == 0 else 2
                for k in range(1, largo + 1):
                    bloques.append((px + ddx * k, ty + (1 if k == 1 else 0) - (1 if k == largo else 0), pz + ddz * k, HOJA))
            n += 1
    return bloques, n
