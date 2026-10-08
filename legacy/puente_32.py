"""
puente.py  --  Groq (intérprete) -> Python (geometría) -> Blockbench MCP (place_cube)

Groq SOLO decide el tipo de objeto y unos pocos parámetros de alto nivel.
Python construye la geometría con piezas grandes, paneles rotados y simetría.

Uso:
    python puente.py                      # pregunta por consola
    python puente.py "crea una capa"      # petición directa
    python puente.py "crea una capa" --seco   # no toca Blockbench, solo muestra piezas

Unidades: los generadores trabajan en BLOQUES (1 bloque = 16 px de Blockbench).
Convención de ejes de Blockbench: Y arriba, el frente del modelo mira a -Z,
por lo tanto "hacia atrás" = +Z.
"""

import argparse
import asyncio
import json
import math
import os
import random
import re
import sys
from typing import Any

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GROQ_MODEL = "openai/gpt-oss-20b"
BLOCKBENCH_URL = "http://localhost:3000/bb-mcp"

PX_POR_BLOQUE = 16.0   # 1 bloque = 16 unidades de Blockbench
MAX_PIEZAS = 400       # tope de seguridad (el personaje completo usa unos 200)

# Si una rotación se ve al revés en Blockbench, cambia el signo (1 <-> -1).
ROT_X_SIGNO = -1       # inclinación de paneles (parte baja hacia atrás)
ROT_Y_SIGNO = 1        # apertura de las alas laterales
ROT_Z_SIGNO = 1        # piezas curvas


# ======================================================================
# Utilidades
# ======================================================================

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def cubo(nombre, x1, y1, z1, x2, y2, z2, origen=None, rot=None) -> dict[str, Any]:
    """Cubo en bloques. from/to se ordenan solos. origin = pivote de rotación."""
    el = {
        "name": nombre,
        "from": [min(x1, x2), min(y1, y2), min(z1, z2)],
        "to": [max(x1, x2), max(y1, y2), max(z1, z2)],
    }
    if origen is not None:
        el["origin"] = list(origen)
    if rot is not None and any(abs(r) > 1e-6 for r in rot):
        el["rotation"] = [round(r, 3) for r in rot]
    return el


def a_pixeles(elementos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convierte bloques -> unidades de Blockbench."""
    s = PX_POR_BLOQUE
    salida = []
    for e in elementos:
        n = dict(e)
        for k in ("from", "to", "origin", "position"):
            if k in n:
                n[k] = [round(v * s, 3) for v in n[k]]
        if "vertices" in n:
            n["vertices"] = [[round(c * s, 3) for c in v] for v in n["vertices"]]
        salida.append(n)
    return salida


def detalle_a_n(detalle: int, opciones=(4, 7, 10)) -> int:
    return opciones[max(1, min(3, int(detalle))) - 1]


# ======================================================================
# Generadores (todos devuelven elementos en BLOQUES)
# ======================================================================

def gen_cubo(p):
    a, h, d = p["ancho"], p["alto"], p["profundidad"]
    return [cubo("cubo", -a / 2, 0, -d / 2, a / 2, h, d / 2)]


def gen_linea(p):
    """Una sola barra larga (no 12 cubitos)."""
    largo, grosor, d = p["ancho"], p["alto"], p["profundidad"]
    return [cubo("linea", -largo / 2, 0, -d / 2, largo / 2, grosor, d / 2)]


def gen_pared(p):
    """Un solo cuboide grande."""
    a, h, d = p["ancho"], p["alto"], p["profundidad"]
    return [cubo("pared", -a / 2, 0, -d / 2, a / 2, h, d / 2)]


def gen_plataforma(p):
    """Losa plana: 'alto' es el grosor."""
    a, h, d = p["ancho"], p["alto"], p["profundidad"]
    return [cubo("plataforma", -a / 2, 0, -d / 2, a / 2, h, d / 2)]


def gen_escalera(p):
    """Un cuboide por escalón, macizo (cada uno sube hasta el suelo)."""
    pasos = max(2, int(p["pasos"]))
    a, h_total, d_total = p["ancho"], p["alto"], p["profundidad"]
    h, d = h_total / pasos, d_total / pasos
    return [
        cubo(f"escalon_{i}", -a / 2, 0, i * d, a / 2, (i + 1) * h, (i + 1) * d)
        for i in range(pasos)
    ]


def gen_punta(p):
    """Pirámide escalonada: cada pieza más pequeña que la anterior."""
    n = detalle_a_n(p["detalle"], (3, 5, 8))
    a, h, d = p["ancho"], p["alto"], p["profundidad"]
    paso = h / n
    els = []
    for i in range(n):
        t = i / n
        k = max(0.08, 1 - t) ** 1.0
        w, dd = a * k, d * k
        els.append(cubo(f"punta_{i}", -w / 2, i * paso, -dd / 2, w / 2, (i + 1) * paso, dd / 2))
    return els


def gen_espada(p):
    """Pomo + empuñadura + guarda + hoja que se afila + punta. 'alto' = largo total."""
    L = p["alto"]
    anch = max(0.05, p["ancho"])         # ancho de la hoja
    prof = max(0.03, p["profundidad"])
    pomo, grip, guarda = 0.12 * L, 0.18 * L, 0.06 * L
    hoja = L - pomo - grip - guarda
    y = 0.0
    els = []
    s = anch * 0.8
    els.append(cubo("pomo", -s / 2, y, -s / 2, s / 2, y + pomo, s / 2)); y += pomo
    g = anch * 0.45
    els.append(cubo("empunadura", -g / 2, y, -g / 2, g / 2, y + grip, g / 2)); y += grip
    gw = anch * 2.4
    els.append(cubo("guarda", -gw / 2, y, -prof, gw / 2, y + guarda, prof)); y += guarda
    # hoja en 3 tramos que se estrechan + remate
    tramos = [(0.40, 1.0), (0.35, 0.8), (0.15, 0.55), (0.10, 0.28)]
    for i, (frac, k) in enumerate(tramos):
        hh = hoja * frac
        w = anch * k
        els.append(cubo(f"hoja_{i}", -w / 2, y, -prof / 2, w / 2, y + hh, prof / 2))
        y += hh
    return els


def gen_curva(p):
    """Arco hecho de segmentos alargados rotados sobre Z. 'angulo' en grados."""
    n = detalle_a_n(p["detalle"], (5, 8, 12))
    R = p["ancho"] / 2
    ang = math.radians(max(10, min(360, p["angulo"])))
    grosor, d = p["alto"], p["profundidad"]
    dth = ang / n
    chord = 2 * (R - grosor / 2) * math.sin(dth / 2) + 0.05   # +0.05: solapa para no dejar huecos
    rc = R - grosor / 2
    els = []
    for i in range(n):
        th = math.pi - (i + 0.5) * dth
        cx, cy = rc * math.cos(th), rc * math.sin(th)
        rz = ROT_Z_SIGNO * (math.degrees(th) - 90)
        els.append(cubo(f"curva_{i}", cx - chord / 2, cy - grosor / 2, -d / 2,
                        cx + chord / 2, cy + grosor / 2, d / 2,
                        origen=(cx, cy, 0), rot=(0, 0, rz)))
    return els


def gen_capa(p):
    """
    Capa con volumen real:
      - filas apiladas de arriba a abajo (ancho crece de 'ancho' a 'ancho_inferior')
      - curvatura vertical: cada fila se aleja en Z (t^2) y se inclina con la pendiente
      - ENVOLVENTE horizontal: cada fila se divide en 3 o 5 segmentos que se doblan hacia
        atras desde el centro (como medio cilindro). 'pliegue' = angulo total de envoltura
        en grados (0 = lamina plana).
    """
    ancho_sup = p["ancho"]
    ancho_inf = p["ancho_inferior"] if p["ancho_inferior"] > 0 else ancho_sup * 1.35
    alto, prof, curv = p["alto"], p["profundidad"], p["curvatura"]
    envol = max(0.0, p["pliegue"])

    m = 1 if envol <= 0 else (3 if p["detalle"] <= 1 else 5)
    n = detalle_a_n(p["detalle"], (5, 6, 8))
    n = max(2, min(n, int(math.ceil(alto))))
    if m > 1:
        n = min(n, MAX_PIEZAS // m)

    # angulo de cada segmento respecto al centro (0, step, 2*step ...)
    mitad = m // 2
    paso_ang = math.radians(envol) / (2 * mitad) if mitad else 0.0

    h = alto / n
    els = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        tm = (t0 + t1) / 2
        w = lerp(ancho_sup, ancho_inf, tm)
        zc = curv * tm ** 2
        pend = 2 * curv * tm / alto
        inc = ROT_X_SIGNO * math.degrees(math.atan(pend))

        y_sup = alto - i * h
        y1, y2 = y_sup - h - 0.04, y_sup
        ym = (y1 + y2) / 2

        sw = w / m
        # centro de cada segmento (cadena desde el centro hacia afuera)
        cx = [0.0] * (mitad + 1)
        cz = [0.0] * (mitad + 1)
        for k in range(1, mitad + 1):
            a0, a1 = (k - 1) * paso_ang, k * paso_ang
            cx[k] = cx[k - 1] + (sw / 2) * (math.cos(a0) + math.cos(a1))
            cz[k] = cz[k - 1] + (sw / 2) * (math.sin(a0) + math.sin(a1))

        for k in range(-mitad, mitad + 1):
            kk = abs(k)
            ang = math.degrees(kk * paso_ang)
            lado = -1 if k < 0 else 1
            x = lado * cx[kk]
            z = zc + cz[kk]
            yaw = -lado * ROT_Y_SIGNO * ang          # izq +, der -
            ancho_seg = sw * (1.0 if m == 1 else 1.08)   # solape para tapar huecos
            nombre = f"capa_{i}_{k + mitad}"
            els.append(cubo(nombre,
                            x - ancho_seg / 2, y1, z - prof / 2,
                            x + ancho_seg / 2, y2, z + prof / 2,
                            origen=(x, ym, z), rot=(inc, yaw, 0)))
    return els


def gen_abrigo(p):
    """
    Abrigo / saco largo que RODEA el cuerpo (espalda + costados + frente).
      - Cada fila es un anillo eliptico (vista desde arriba) de segmentos tangentes.
      - Cada segmento se INCLINA hacia afuera segun la pendiente real de la silueta
        (ensanchado y recogido) -> caida lisa, no anillos apilados.
      - 'curvatura' es una FRACCION del alto (0 a 0.2): cuanto se echa hacia atras abajo.
      - Frente cerrado por defecto ('abertura_frontal' = grados de hueco, 0 = entero).
      - Muesca trasera redondeada: 'abertura_trasera' (altura, bloques), 'ancho_muesca'.
    """
    ancho = p["ancho"]
    ancho_inf = p["ancho_inferior"] if p["ancho_inferior"] > 0 else ancho * 1.3
    fondo = p["fondo"] if p["fondo"] > 0 else ancho * 0.5
    fondo_inf = fondo * (ancho_inf / ancho) ** 0.6
    alto, grosor = p["alto"], p["profundidad"]
    curv = max(0.0, min(0.3, p["curvatura"])) * alto
    g = math.radians(max(0.0, p["abertura_frontal"])) / 2
    rv = max(0.05, min(0.5, p["ancho_muesca"]))
    recogido = max(0.0, min(0.4, p["recogido"]))

    n = detalle_a_n(p["detalle"], (5, 6, 8))
    m = detalle_a_n(p["detalle"], (8, 10, 12))
    h = alto / n
    filas_vent = min(int(round(max(0.0, p["abertura_trasera"]) / h)), n - 1)

    ini = max(0.0, min(0.85, p["inicio_campana"]))

    def dims(t):
        # torso: ancho constante hasta 'inicio_campana'; despues la campana se abre suave
        u = max(0.0, (t - ini) / (1 - ini))
        u = u * u * (3 - 2 * u)
        k = 1 - recogido * max(0.0, (t - 0.6) / 0.4) ** 1.5
        a = lerp(ancho, ancho_inf, u) / 2 * k
        b = lerp(fondo, fondo_inf, u) / 2 * k
        return a, b, curv * t ** 2

    els = []
    for i in range(n):
        t0, t1, tm = i / n, (i + 1) / n, (i + 0.5) / n
        a, b, zc = dims(tm)
        (a0, b0, _), (a1, b1, _) = dims(t0), dims(t1)
        y2 = alto - i * h
        y1 = y2 - h * 1.08                       # solape entre filas (hay inclinacion)
        ym = (y1 + y2) / 2

        def pt(phi):
            # zc (echarse hacia atras) pesa 1 en la espalda y 0 en costados/frente
            return (a * math.sin(phi), -b * math.cos(phi) + zc * max(0.0, -math.cos(phi)))

        for j in range(m):
            f0 = g + (2 * math.pi - 2 * g) * j / m
            f1 = g + (2 * math.pi - 2 * g) * (j + 1) / m
            fm = (f0 + f1) / 2

            r = abs(fm - math.pi) / max(1e-6, (math.pi - g))
            if filas_vent and r < rv:
                faltan = int(round(filas_vent * math.sqrt(1 - (r / rv) ** 2)))
                if i >= n - faltan:
                    continue

            (x0, z0), (x1, z1) = pt(f0), pt(f1)
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            L = math.hypot(x1 - x0, z1 - z0) * 1.07
            th = math.atan2(-(z1 - z0), (x1 - x0))
            if th > math.pi / 2:
                th -= math.pi
            elif th <= -math.pi / 2:
                th += math.pi

            # pendiente radial de la silueta en este angulo (arriba -> abajo)
            rad = lambda aa, bb: math.hypot(aa * math.sin(fm), bb * math.cos(fm))
            pend = (rad(a1, b1) - rad(a0, b0)) / h
            (_, _, zc0), (_, _, zc1) = dims(t0), dims(t1)
            nn = math.hypot(math.sin(fm) / a, math.cos(fm) / b)
            nzu = -math.cos(fm) / b / nn
            pend += (zc1 - zc0) / h * max(0.0, -math.cos(fm)) * nzu
            ang = math.degrees(math.atan(pend))
            # el eje local +Z del cubo, tras girar 'th', apunta hacia afuera o hacia adentro?
            nx, nz = math.sin(fm) / a, -math.cos(fm) / b
            sentido = 1 if (math.sin(th) * nx + math.cos(th) * nz) > 0 else -1
            tilt = ROT_X_SIGNO * ang * sentido

            els.append(cubo(f"abrigo_{i}_{j}",
                            cx - L / 2, y1, cz - grosor / 2,
                            cx + L / 2, y2, cz + grosor / 2,
                            origen=(cx, ym, cz),
                            rot=(tilt, ROT_Y_SIGNO * math.degrees(th), 0)))
    return els


def _normal_newell(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        x0, y0, z0 = pts[i]
        x1, y1, z1 = pts[(i + 1) % len(pts)]
        nx += (y0 - y1) * (z0 + z1)
        ny += (z0 - z1) * (x0 + x1)
        nz += (x0 - x1) * (y0 + y1)
    return nx, ny, nz


def gen_capa_malla(p):
    """
    Capa/abrigo como MALLA (place_mesh): superficie parametrica con grosor.
      - CUELLO + HOMBROS: arriba es estrecha (cuello) y baja en pendiente hasta el ancho de hombros
      - frente CERRADO arriba (pecho) y abierto mas abajo (cierre_pecho, abertura_frontal)
      - torso recto y entallado; la campana empieza en 'inicio_campana'
      - espalda echada hacia atras (curvatura = fraccion del alto), costados rectos
      - muesca trasera redondeada y borde inferior en picos triangulares
    Se genera con la base en y=0 y el centro en x=z=0, y se coloca con pos_x/pos_y/pos_z.
    Todo en bloques; devuelve UN elemento malla.
    """
    ancho = p["ancho"]
    ancho_inf = p["ancho_inferior"] if p["ancho_inferior"] > 0 else ancho * 1.3
    fondo = p["fondo"] if p["fondo"] > 0 else ancho * 0.5
    fondo_inf = fondo * (ancho_inf / ancho) ** 0.6
    alto = p["alto"]
    th = max(0.01, p["profundidad"])
    curv = max(0.0, min(0.3, p["curvatura"])) * alto
    g_full = math.radians(max(0.0, p["abertura_frontal"])) / 2
    rv = max(0.05, min(0.5, p["ancho_muesca"]))
    recogido = max(0.0, min(0.4, p["recogido"]))
    ini = max(0.0, min(0.85, p["inicio_campana"]))
    esc = max(0.0, min(0.5, p["esclavina"]))
    cuello = max(0.15, min(1.0, p["cuello"]))
    hs = max(0.02, min(0.5, p["caida_hombros"]))
    cierre = max(0.0, min(0.8, p["cierre_pecho"]))
    pu = max(0, int(p["puntas"]))
    vent = max(0.0, min(0.7, p["abertura_trasera"] / alto))
    dient = 0.05 if pu > 0 else 0.0

    M0, R = {1: (24, 8), 2: (36, 10), 3: (48, 12)}[max(1, min(3, int(p["detalle"])))]
    if pu > 0:
        kd = max(2, 2 * round(M0 / (2 * pu)))
        M = pu * kd
    else:
        kd, M = 1, M0
    cerrado = g_full < 1e-3
    K = M if cerrado else M + 1

    def sm(u):
        u = max(0.0, min(1.0, u))
        return u * u * (3 - 2 * u)

    def g_de(t):                                   # medio hueco frontal segun la altura
        return g_full * sm((t - cierre) / 0.2)

    def dims(t):
        u = sm((t - ini) / (1 - ini)) if t > ini else 0.0
        k = 1 - recogido * max(0.0, (t - 0.6) / 0.4) ** 1.5
        sh = 1 + esc * max(0.0, 1 - t / 0.25) ** 2
        nf = lerp(cuello, 1.0, sm(t / hs))         # cuello -> hombros
        return (lerp(ancho, ancho_inf, u) / 2 * k * sh * nf,
                lerp(fondo, fondo_inf, u) / 2 * k * nf,
                curv * t ** 2)

    def phi_v(k, t):
        g = g_de(t)
        return g + (2 * math.pi - 2 * g) * k / M

    def phi_full(k):
        return g_full + (2 * math.pi - 2 * g_full) * k / M

    def t_fin(k):
        phi = phi_full(k)
        r = abs(phi - math.pi) / max(1e-6, math.pi - g_full)
        notch = vent * math.sqrt(1 - (r / rv) ** 2) if (vent > 0 and r < rv) else 0.0
        if pu > 0:
            ph = (k % kd) / kd
            base = 1 - dient + dient * (1 - abs(2 * ph - 1))
        else:
            base = 1.0
        return max(0.25, base - notch)

    def t_de(k, v):                                # filas mas densas arriba (hombros)
        return t_fin(k) * (v / R) ** 1.35

    V = []
    ext, inte, mid = {}, {}, {}
    for kk in range(K):
        for v in range(R + 1):
            t = t_de(kk, v)
            phi = phi_v(kk, t)
            a, b, zc = dims(t)
            x = a * math.sin(phi)
            z = -b * math.cos(phi) + zc * max(0.0, -math.cos(phi))
            y = alto * (1 - t)
            nx, nz = math.sin(phi) / a, -math.cos(phi) / b
            nn = math.hypot(nx, nz)
            nx, nz = nx / nn, nz / nn
            ext[(kk, v)] = len(V)
            V.append([x + nx * th / 2, y, z + nz * th / 2])
            inte[(kk, v)] = len(V)
            V.append([x - nx * th / 2, y, z - nz * th / 2])
            mid[(kk, v)] = (x, y, z)

    def O(k, v): return ext[(k % K, v)]
    def I(k, v): return inte[(k % K, v)]
    def Mp(k, v): return mid[(k % K, v)]

    caras = []

    def add(ids, esperado):
        pts = [V[i] for i in ids]
        n = _normal_newell(pts)
        if n[0] * esperado[0] + n[1] * esperado[1] + n[2] * esperado[2] < 0:
            ids = ids[::-1]
        caras.append(list(ids))

    for k in range(M):
        for v in range(R):
            tm = (t_de(k, v) + t_de(k, v + 1)) / 2
            phim = phi_v(k + 0.5, tm)
            exp = (math.sin(phim), 0.0, -math.cos(phim))
            add([O(k, v), O(k + 1, v), O(k + 1, v + 1), O(k, v + 1)], exp)
            add([I(k, v), I(k + 1, v), I(k + 1, v + 1), I(k, v + 1)], (-exp[0], 0.0, -exp[2]))
        add([O(k, 0), O(k + 1, 0), I(k + 1, 0), I(k, 0)], (0.0, 1.0, 0.0))            # borde superior (cuello)
        d = tuple(Mp(k, R)[c] - Mp(k, R - 1)[c] for c in range(3))
        add([O(k, R), I(k, R), I(k + 1, R), O(k + 1, R)], d)                           # borde inferior
    if not cerrado:                                                                   # bordes del frente
        for v in range(R):
            if g_de(t_de(0, v)) < 1e-3 and g_de(t_de(0, v + 1)) < 1e-3:
                continue                                                              # pecho cerrado: sin borde
            e0 = tuple(Mp(0, v)[c] - Mp(1, v)[c] for c in range(3))
            e1 = tuple(Mp(M, v)[c] - Mp(M - 1, v)[c] for c in range(3))
            add([O(0, v), O(0, v + 1), I(0, v + 1), I(0, v)], e0)
            add([O(M, v), O(M, v + 1), I(M, v + 1), I(M, v)], e1)

    return [{"name": "capa_malla",
             "position": [p["pos_x"], p["pos_y"], p["pos_z"]],
             "vertices": [[round(c, 4) for c in v] for v in V], "faces": caras}]


def gen_faldon(p):
    """
    Faldon con flecos + hombreras, ajustado al torso del personaje (no envuelve el cuerpo).
      - Delante y detras: un panel central y dos paneles laterales que se abren hacia afuera.
      - Cada panel = cuerpo + dientes alternos largo/corto (borde en picos).
      - Dos hombreras escalonadas por lado, sobre el brazo.
    Referencia: 'ancho', 'alto', 'fondo' = medidas del TORSO; 'pos_y' = altura de la base del torso.
    El torso se supone centrado en x=z=0 (+ pos_x/pos_z). Internamente trabaja en px.
    """
    px = PX_POR_BLOQUE
    a = p["ancho"] * px / 2                                   # medio ancho del torso
    d = (p["fondo"] if p["fondo"] > 0 else p["ancho"] * 0.57) * px / 2   # media profundidad
    t = max(0.5, p["profundidad"] * px)                       # grosor de la tela
    yb = p["pos_y"] * px                                      # base del torso
    yt = yb + p["alto"] * px                                  # parte alta del torso
    largo = max(1.0, p["largo"] * px)
    brazo = max(0.5, p["ancho_brazo"] * px)
    flare = ROT_Z_SIGNO * max(0.0, min(45.0, p["pliegue"]))   # apertura de los paneles laterales
    n_dientes = max(2, min(10, int(p["puntas"])))
    ox, oz = p["pos_x"] * px, p["pos_z"] * px
    y0 = yb + 1.5                                             # arranque de los paneles (bajo la cintura)
    els = []

    def caja(nombre, x1, y1, z1, x2, y2, z2, piv=None, rz=0.0):
        els.append(cubo(nombre,
                        (x1 + ox) / px, y1 / px, (z1 + oz) / px,
                        (x2 + ox) / px, y2 / px, (z2 + oz) / px,
                        origen=None if piv is None else ((piv[0] + ox) / px, piv[1] / px, (piv[2] + oz) / px),
                        rot=None if piv is None else (0, 0, rz)))

    def panel(nombre, x1, x2, zc, largo_p, rz=0.0, pivx=None):
        """Cuerpo + dientes. Todas las piezas giran rigidas sobre el mismo pivote."""
        piv = (x1 if pivx is None else pivx, y0, zc)
        z1, z2 = zc - t / 2, zc + t / 2
        caja(f"{nombre}_cuerpo", x1, y0 - largo_p, z1, x2, y0, z2, piv, rz)
        w = x2 - x1
        nd = max(2, min(n_dientes, int(w // 0.7)))
        dw = w / nd
        for i in range(nd):
            ld = 2.0 if i % 2 == 0 else 1.0
            xa = x1 + i * dw
            caja(f"{nombre}_diente{i}", xa + 0.05, y0 - largo_p - ld, z1,
                 xa + dw - 0.05, y0 - largo_p, z2, piv, rz)

    # --- paneles delanteros y traseros ---------------------------------
    wc = max(2.0, a * 0.85)                                   # ancho del panel central
    x_in = wc / 2 + 0.3
    x_out = max(a + 0.4, x_in + 1.0)
    for cara, zc in (("del", -(d + t / 2)), ("tras", d + t / 2)):
        panel(f"faldon_{cara}_centro", -wc / 2, wc / 2, zc, largo)
        panel(f"faldon_{cara}_der", x_in, x_out, zc, largo * 1.2, rz=flare, pivx=x_in)
        panel(f"faldon_{cara}_izq", -x_out, -x_in, zc, largo * 1.2, rz=-flare, pivx=-x_in)

    # --- hombreras (dos escalones por lado) ----------------------------
    for lado, nom in ((-1, "izq"), (1, "der")):
        x1, x2 = sorted((lado * (a - 0.25), lado * (a + brazo + 0.6)))
        caja(f"hombrera_{nom}_0", x1, yt - 1.5, -(d + 0.5), x2, yt + 0.25, d + 0.5)
        x1, x2 = sorted((lado * a, lado * (a + brazo + 0.9)))
        caja(f"hombrera_{nom}_1", x1, yt - 3.0, -(d + 0.75), x2, yt - 1.5, d + 0.75)
    return els


# Si la V y el arco "principal" salen en la espalda en vez de al frente, pon False.
FRENTE_EN_Z_NEGATIVO = True
EXP_FORMA = 0.62        # forma de la seccion: 1 = elipse, menor = mas cuadrada (torso tipo bloque)


def gen_faldon_malla(p):
    """
    Faldon / casaca como UNA malla cerrada alrededor del torso (costados unidos).
      - Seccion cuadrada redondeada que abraza el torso y se ensancha ('vuelo') desde la cintura al borde.
      - CUELLO EN V al frente (y una V pequena atras).
      - ARCO bajo la cintura, delante y detras, que deja ver las piernas.
      - Borde inferior en picos (flecos triangulares) fuera de los arcos.
    Medidas en BLOQUES; internamente en px. 'ancho/alto/fondo' = torso, 'pos_y' = base del torso,
    'largo' = cuanto baja el borde bajo la base del torso, 'profundidad' = grosor de la tela.
    Los vertices salen en coordenadas absolutas (position = 0) desplazadas por pos_x / pos_z.
    """
    px = PX_POR_BLOQUE
    a_t = p["ancho"] * px / 2
    b_t = (p["fondo"] if p["fondo"] > 0 else p["ancho"] * 0.57) * px / 2
    th = max(0.4, p["profundidad"] * px)
    yb = p["pos_y"] * px                           # base del torso
    yt = yb + p["alto"] * px                       # parte alta del torso
    hem = yb - max(0.5, p["largo"] * px)           # borde inferior (sin picos)
    vuelo = max(0.0, p["vuelo"] * px)
    amp = 1.0                                      # largo de los picos (px)
    ox, oz = p["pos_x"] * px, p["pos_z"] * px

    a0 = a_t + 0.1 + th / 2                        # linea central de la tela (deja 0.1 px al torso)
    b0 = b_t + 0.1 + th / 2
    ua = min(0.95, max(0.1, p["arco_ancho"] * px / a0))     # semiancho del arco (fraccion del ancho)
    y_ap = min(yt - 1.0, hem + max(0.5, p["arco_alto"] * px))   # cima del arco
    uv = min(0.95, max(0.1, p["v_ancho"] * px / a0))        # semiancho de la V arriba
    vprof = max(0.0, p["v_prof"] * px)

    M0, R = {1: (48, 10), 2: (64, 12), 3: (80, 14)}[max(1, min(3, int(p["detalle"])))]
    pu = max(0, int(p["puntas"]))
    if pu > 0:
        kd = max(2, 2 * round(M0 / (2 * pu)))
        M = pu * kd
    else:
        kd, M = 1, M0

    def sm(u):
        u = max(0.0, min(1.0, u))
        return u * u * (3 - 2 * u)

    y_w = yb + 0.5                                 # aqui empieza a ensancharse

    def dims(y):
        f = sm((y_w - y) / max(1e-6, (y_w - hem)))
        return a0 + vuelo * f, b0 + vuelo * 0.8 * f

    def curva(phi, y):
        a, b = dims(y)
        s, c = math.sin(phi), math.cos(phi)
        return (a * math.copysign(abs(s) ** EXP_FORMA, s),
                -b * math.copysign(abs(c) ** EXP_FORMA, c))     # phi = 0 -> frente (z negativa)

    def u_k(k):
        s = math.sin(2 * math.pi * k / M)
        return math.copysign(abs(s) ** EXP_FORMA, s)

    def y_top_k(k):                                # cuello en V
        prof = vprof if math.cos(2 * math.pi * k / M) > 0 else vprof * 0.4
        return yt - prof * max(0.0, 1 - abs(u_k(k)) / uv)

    def y_bot_k(k):                                # arco + picos
        u = abs(u_k(k))
        if u < ua:
            return hem + (y_ap - hem) * math.sqrt(1 - (u / ua) ** 2)
        diente = 0.0
        if pu > 0:
            ph = (k % kd) / kd
            diente = amp * (1 - abs(2 * ph - 1)) * sm((u - ua) / 0.15)
        return hem - diente

    V, ext, inte, mid = [], {}, {}, {}
    for k in range(M):
        phi = 2 * math.pi * k / M
        ytk, ybk = y_top_k(k), y_bot_k(k)
        for v in range(R + 1):
            y = ytk + (ybk - ytk) * v / R
            x, z = curva(phi, y)
            xa_, za_ = curva(phi + 0.01, y)
            xb_, zb_ = curva(phi - 0.01, y)
            nx, nz = (za_ - zb_), -(xa_ - xb_)
            nn = math.hypot(nx, nz) or 1.0
            nx, nz = nx / nn, nz / nn
            ext[(k, v)] = len(V); V.append([x + nx * th / 2, y, z + nz * th / 2])
            inte[(k, v)] = len(V); V.append([x - nx * th / 2, y, z - nz * th / 2])
            mid[(k, v)] = (x, y, z)

    def O(k, v): return ext[(k % M, v)]
    def I(k, v): return inte[(k % M, v)]
    def Mp(k, v): return mid[(k % M, v)]

    caras = []

    def add(ids, esperado):
        n = _normal_newell([V[i] for i in ids])
        if n[0] * esperado[0] + n[1] * esperado[1] + n[2] * esperado[2] < 0:
            ids = ids[::-1]
        caras.append(list(ids))

    def hacia_fuera(dv, t):
        """Componente de dv perpendicular a t: direccion 'hacia afuera' del borde, dentro de la tela."""
        tn = math.sqrt(sum(c * c for c in t)) or 1.0
        t = tuple(c / tn for c in t)
        dot = sum(dv[c] * t[c] for c in range(3))
        return tuple(dv[c] - dot * t[c] for c in range(3))

    for k in range(M):
        phim = 2 * math.pi * (k + 0.5) / M
        exp = (math.sin(phim), 0.0, -math.cos(phim))
        for v in range(R):
            add([O(k, v), O(k + 1, v), O(k + 1, v + 1), O(k, v + 1)], exp)
            add([I(k, v), I(k + 1, v), I(k + 1, v + 1), I(k, v + 1)], (-exp[0], 0.0, -exp[2]))
        t0 = tuple(Mp(k + 1, 0)[c] - Mp(k, 0)[c] for c in range(3))
        d0 = tuple(Mp(k, 0)[c] - Mp(k, 1)[c] for c in range(3))
        add([O(k, 0), O(k + 1, 0), I(k + 1, 0), I(k, 0)], hacia_fuera(d0, t0))      # borde del cuello
        t1 = tuple(Mp(k + 1, R)[c] - Mp(k, R)[c] for c in range(3))
        d1 = tuple(Mp(k, R)[c] - Mp(k, R - 1)[c] for c in range(3))
        add([O(k, R), I(k, R), I(k + 1, R), O(k + 1, R)], hacia_fuera(d1, t1))      # borde inferior

    if not FRENTE_EN_Z_NEGATIVO:
        for vtx in V:
            vtx[2] = -vtx[2]
        caras = [c[::-1] for c in caras]

    verts = [[round((vtx[0] + ox) / px, 4), round(vtx[1] / px, 4), round((vtx[2] + oz) / px, 4)] for vtx in V]
    return [{"name": "faldon", "position": [0.0, 0.0, 0.0], "vertices": verts, "faces": caras}]


def _fusionar_celdas(celdas):
    """Une celdas de 1 px en cuboides grandes (menos cubos). Devuelve (i1,y1,j1,i2,y2,j2) con fin exclusivo."""
    resto = set(celdas)
    cajas = []
    for (i, y, j) in sorted(celdas, key=lambda c: (c[1], c[2], c[0])):
        if (i, y, j) not in resto:
            continue
        i2 = i
        while (i2 + 1, y, j) in resto:
            i2 += 1
        j2 = j
        while all((ii, y, j2 + 1) in resto for ii in range(i, i2 + 1)):
            j2 += 1
        y2 = y
        while all((ii, y2 + 1, jj) in resto for ii in range(i, i2 + 1) for jj in range(j, j2 + 1)):
            y2 += 1
        for ii in range(i, i2 + 1):
            for yy in range(y, y2 + 1):
                for jj in range(j, j2 + 1):
                    resto.discard((ii, yy, jj))
        cajas.append((i, y, j, i2 + 1, y2 + 1, j2 + 1))
    return cajas


def gen_faldon_voxel(p):
    """
    Faldon estilo Minecraft: celdas de 1 px fusionadas en cubos. Frente = -Z, espalda = +Z.
      - Anillo cerrado de 1 px alrededor del torso (costados unidos) que se ensancha 'vuelo' px en la falda.
      - PECHERA y ESPALDAR con relieve ('relieve' px hacia afuera) en el cuerpo.
      - CUELLO EN V: delante ancha y profunda ('v_ancho', 'v_prof'); detras, la mitad. La V corta primero el
        relieve y, mas arriba, tambien la tela: queda un escalon hacia atras.
      - Falda: delante una UVE muy abierta ('v_bajo' = semiancho abajo); detras un ARCO ('arco_ancho').
      - Flecos en dos niveles en el borde inferior si 'puntas' > 0.
      - Hombreras de dos escalones por lado.
    Medidas en bloques (px/16). Internamente todo en px enteros.
    """
    px = PX_POR_BLOQUE
    a_t = p["ancho"] * px / 2
    b_t = (p["fondo"] if p["fondo"] > 0 else p["ancho"] * 0.57) * px / 2
    yb = int(round(p["pos_y"] * px))                       # base del torso
    n_cuerpo = max(2, int(round(p["alto"] * px)))
    n_falda = max(1, int(round(p["largo"] * px)))
    flare = max(0, int(round(p["vuelo"] * px)))
    relieve = max(0, min(2, int(round(p["relieve"] * px))))
    A = max(2, int(round(a_t + 1.5)))                      # semiancho exterior del anillo
    B = max(2, int(round(b_t + 1.0)))                      # semifondo exterior
    yt = yb + n_cuerpo
    hem = yb - n_falda
    ox, oz = p["pos_x"] * px, p["pos_z"] * px
    celdas = set()

    def anillo(y, aa, bb):
        for i in range(-aa, aa):
            for j in range(-bb, bb):
                if -aa + 1 <= i <= aa - 2 and -bb + 1 <= j <= bb - 2:
                    continue
                celdas.add((i, y, j))

    ax = max(1, int(round(a_t - 0.5)))             # borde interior del brazo (los brazos quedan a la vista)
    anillo(yb, A, B)                               # fila de union con la falda
    for y in range(yb + 1, yt):                    # arriba: solo frente y espalda entre los brazos
        for i in range(-ax, ax):
            celdas.add((i, y, -B))
            celdas.add((i, y, B - 1))
    for y in range(hem, yb):
        anillo(y, A + flare, B + flare)

    # relieve: pechera (delante) y espaldar (detras), entre los brazos
    for y in range(yb, yt):
        for r in range(1, relieve + 1):
            for i in range(-ax, ax):
                celdas.add((i, y, -B - r))
                celdas.add((i, y, B - 1 + r))

    # cuello en V (delante ancho/profundo, atras la mitad)
    Wv = max(1.0, p["v_ancho"] * px)
    prof_f = max(1, int(round(p["v_prof"] * px)))
    Wb, prof_b = max(1.0, Wv / 2), max(1, prof_f // 2)
    for lado, W, prof in ((-1, Wv, prof_f), (1, Wb, prof_b)):
        for d in range(prof):
            y = yt - 1 - d
            hw = W * (1 - d / prof)
            for i in range(-A - 2, A + 2):
                if abs(i + 0.5) < hw:
                    for r in range(1, relieve + 1):
                        celdas.discard((i, y, (-B - r) if lado < 0 else (B - 1 + r)))
            if lado < 0 and d < max(1, prof // 2):          # solo delante: la V corta tambien la tela
                for i in range(-A - 2, A + 2):
                    if abs(i + 0.5) < hw - 1:
                        celdas.discard((i, y, -B))

    # falda: delante UVE muy abierta, detras ARCO
    Wf = max(1.0, p["v_bajo"] * px)
    Wa = max(1.0, p["arco_ancho"] * px)
    zf, zt = -(B + flare), B + flare - 1
    for r in range(n_falda):
        y = yb - 1 - r
        t = (r + 0.5) / n_falda
        hw_v = Wf * t
        hw_a = Wa * math.sqrt(max(0.0, 1 - (1 - t) ** 2))
        for i in range(-(A + flare), A + flare):
            if abs(i + 0.5) < hw_v:
                celdas.discard((i, y, zf))
            if abs(i + 0.5) < hw_a:
                celdas.discard((i, y, zt))

    # flecos (dos niveles) bajo la fila inferior
    if int(p["puntas"]) > 0:
        base = [c for c in celdas if c[1] == hem]
        for (i, y, j) in base:
            if (i + j) % 2 == 0:
                celdas.add((i, hem - 1, j))
                if (i + j) % 6 == 0:                       # pocos flecos largos, para que no parezcan pilares
                    celdas.add((i, hem - 2, j))

    els = []
    for n, (i1, y1, j1, i2, y2, j2) in enumerate(_fusionar_celdas(celdas)):
        els.append(cubo(f"faldon_{n}", (i1 + ox) / px, y1 / px, (j1 + oz) / px,
                        (i2 + ox) / px, y2 / px, (j2 + oz) / px))

    # hombreras (dos escalones por lado), sobre los brazos
    brazo = max(0.5, p["ancho_brazo"] * px)
    for lado, nom in ((-1, "izq"), (1, "der")):
        x1, x2 = sorted((lado * (a_t - 0.25), lado * (a_t + brazo + 0.6)))
        els.append(cubo(f"hombrera_{nom}_0", (x1 + ox) / px, (yt - 1.5) / px, (-(b_t + 0.5) + oz) / px,
                        (x2 + ox) / px, (yt + 0.25) / px, ((b_t + 0.5) + oz) / px))
        x1, x2 = sorted((lado * a_t, lado * (a_t + brazo + 0.9)))
        els.append(cubo(f"hombrera_{nom}_1", (x1 + ox) / px, (yt - 3.0) / px, (-(b_t + 0.75) + oz) / px,
                        (x2 + ox) / px, (yt - 1.5) / px, ((b_t + 0.75) + oz) / px))
    return els


# ----------------------------------------------------------------------
# Partes del personaje (todas en px; frente = -Z; ajustadas al cuerpo actual:
# torso 7x6x4 con base en pos_y, brazos en x = +-(3..5), cabeza 10x10x8 apoyada sobre el torso)
# ----------------------------------------------------------------------

def _medidas(p):
    px = PX_POR_BLOQUE
    a_t = p["ancho"] * px / 2
    b_t = (p["fondo"] if p["fondo"] > 0 else p["ancho"] * 0.57) * px / 2
    yb = p["pos_y"] * px
    yt = yb + p["alto"] * px
    relieve = max(0, min(2, int(round(p["relieve"] * px))))
    zp = int(round(b_t + 1.0)) + relieve          # cara externa de la pechera / espaldar
    return dict(px=px, a=a_t, b=b_t, yb=yb, yt=yt, zp=zp,
                brazo=max(0.5, p["ancho_brazo"] * px),
                hw=a_t + 1.5, hz=b_t + 2.0,       # media anchura / media profundidad de la cabeza (con inflate)
                ox=p["pos_x"] * px, oz=p["pos_z"] * px)


def _caja(els, m, nombre, x1, y1, z1, x2, y2, z2):
    px = m["px"]
    els.append(cubo(nombre, (x1 + m["ox"]) / px, y1 / px, (z1 + m["oz"]) / px,
                    (x2 + m["ox"]) / px, y2 / px, (z2 + m["oz"]) / px))


def gen_cinturon(p):
    """Banda entre los brazos, delante y detras, con hebilla (marco + remache) al frente."""
    m = _medidas(p)
    els = []
    y1, y2 = m["yb"] + 0.5, m["yb"] + 1.75
    x = m["a"] - 0.6                               # justo hasta los brazos
    zp = m["zp"]
    _caja(els, m, "cinturon_frente", -x, y1, -(zp + 0.5), x, y2, -zp)
    _caja(els, m, "cinturon_espalda", -x, y1, zp, x, y2, zp + 0.5)
    _caja(els, m, "hebilla_marco", -1.25, y1 - 0.25, -(zp + 1.0), 1.25, y2 + 0.25, -(zp + 0.5))
    _caja(els, m, "hebilla_centro", -0.5, y1 + 0.25, -(zp + 1.25), 0.5, y2 - 0.25, -(zp + 1.0))
    return els


def gen_guantes(p):
    """Mano + puño (un escalon mas ancho) en cada brazo."""
    m = _medidas(p)
    els = []
    ax1 = m["a"] - 0.5                             # el brazo empieza 0.5 px dentro del torso
    ax2 = ax1 + m["brazo"]
    for lado, nom in ((-1, "izq"), (1, "der")):
        x1, x2 = sorted((lado * (ax1 - 0.35), lado * (ax2 + 0.35)))
        _caja(els, m, f"guante_{nom}_mano", x1, m["yb"], -1.45, x2, m["yb"] + 2.0, 1.45)
        x1, x2 = sorted((lado * (ax1 - 0.45), lado * (ax2 + 0.45)))
        _caja(els, m, f"guante_{nom}_puno", x1, m["yb"] + 2.0, -1.55, x2, m["yb"] + 3.25, 1.55)
    return els


def _cara(p, tallada=False):
    """
    Ojos HUNDIDOS y vigote que sobresale.
      tallada=True : la cabeza propia (gen_cabeza) trae huecos; globo y pupila quedan al fondo.
      tallada=False: sobre una cabeza ajena (sin hueco) se pone un marco saliente alrededor del ojo,
                     con el globo casi a ras: el ojo se ve hundido respecto al marco.
    """
    m = _medidas(p)
    els = []
    zf = -m["hz"]                                  # plano frontal de la cabeza
    hb = m["yt"]                                   # base de la cabeza
    for lado, nom in ((-1, "izq"), (1, "der")):
        def lx(a, b):
            return tuple(sorted((lado * a, lado * b)))
        if tallada:
            x1, x2 = lx(1.0, 4.0)
            _caja(els, m, f"ojo_{nom}_globo", x1, hb + 3.25, zf + 0.75, x2, hb + 5.75, zf + 1.0)
            x1, x2 = lx(1.4, 2.9)
            _caja(els, m, f"ojo_{nom}_pupila", x1, hb + 3.25, zf + 0.5, x2, hb + 4.9, zf + 0.75)
        else:
            marco = {"arriba": (0.25, 4.75, 5.75, 6.5), "abajo": (0.25, 4.75, 2.5, 3.25),
                     "interior": (0.25, 1.0, 3.25, 5.75), "exterior": (4.0, 4.75, 3.25, 5.75)}
            for sub, (a, b, ya, yz) in marco.items():
                x1, x2 = lx(a, b)
                _caja(els, m, f"ojo_{nom}_marco_{sub}", x1, hb + ya, zf - 0.75, x2, hb + yz, zf)
            x1, x2 = lx(1.0, 4.0)
            _caja(els, m, f"ojo_{nom}_globo", x1, hb + 3.25, zf - 0.25, x2, hb + 5.75, zf)
            x1, x2 = lx(1.4, 2.9)
            _caja(els, m, f"ojo_{nom}_pupila", x1, hb + 3.25, zf - 0.5, x2, hb + 4.9, zf - 0.25)
    # vigote: barra con puntas que bajan y bulto central
    _caja(els, m, "vigote_centro", -0.75, hb + 2.5, zf - 1.25, 0.75, hb + 3.25, zf)
    for lado, nom in ((-1, "izq"), (1, "der")):
        x1, x2 = sorted((lado * 0.0, lado * 3.0))
        _caja(els, m, f"vigote_{nom}", x1, hb + 1.5, zf - 1.0, x2, hb + 2.5, zf)
        x1, x2 = sorted((lado * 3.0, lado * 4.0))
        _caja(els, m, f"vigote_{nom}_punta", x1, hb + 0.9, zf - 0.75, x2, hb + 1.9, zf)
    return els


def gen_cara(p):
    """Cara para la cabeza que ya tienes en Blockbench: ojos hundidos (con marco) y vigote."""
    return _cara(p, tallada=False)


def gen_corona(p):
    """Anillo grueso alrededor de la cabeza (4 lados + labio superior) con remaches."""
    m = _medidas(p)
    els = []
    hw, hz, hb = m["hw"], m["hz"], m["yt"]
    y1, y2 = hb + 6.5, hb + 10.0
    ya = y2 - 1.0                                  # labio superior
    # banda (1 px de grosor)
    _caja(els, m, "corona_frente", -(hw + 1), y1, -(hz + 1), hw + 1, y2, -hz)
    _caja(els, m, "corona_espalda", -(hw + 1), y1, hz, hw + 1, y2, hz + 1)
    _caja(els, m, "corona_izq", -(hw + 1), y1, -hz, -hw, y2, hz)
    _caja(els, m, "corona_der", hw, y1, -hz, hw + 1, y2, hz)
    # labio superior (la hace mas gruesa arriba)
    _caja(els, m, "corona_labio_frente", -(hw + 1.5), ya, -(hz + 1.5), hw + 1.5, y2, -(hz + 1))
    _caja(els, m, "corona_labio_espalda", -(hw + 1.5), ya, hz + 1, hw + 1.5, y2, hz + 1.5)
    _caja(els, m, "corona_labio_izq", -(hw + 1.5), ya, -(hz + 1), -(hw + 1), y2, hz + 1)
    _caja(els, m, "corona_labio_der", hw + 1, ya, -(hz + 1), hw + 1.5, y2, hz + 1)
    # remaches: centro delante y detras, y a los costados
    ys1, ys2 = hb + 7.5, hb + 9.0
    _caja(els, m, "corona_remache_frente", -1.5, ys1, -(hz + 2), 1.5, ys2, -(hz + 1))
    _caja(els, m, "corona_remache_espalda", -1.5, ys1, hz + 1, 1.5, ys2, hz + 2)
    _caja(els, m, "corona_remache_izq", -(hw + 2), ys1, -1.5, -(hw + 1), ys2, 1.5)
    _caja(els, m, "corona_remache_der", hw + 1, ys1, -1.5, hw + 2, ys2, 1.5)
    return els


def gen_plumas(p):
    """Abanico de 8 plumas (2 capas de profundidad); las del borde se inclinan hacia afuera."""
    m = _medidas(p)
    els = []
    hw, hz = m["hw"], m["hz"]
    base = m["yt"] + 9.5                           # arrancan dentro del labio de la corona
    alturas = [4.5, 6.5, 8.5, 10.5, 10.5, 8.5, 6.5, 4.5]
    w = 2 * hw / len(alturas)
    capas = (("del", -(hz - 1.0), 0.0, -2.5), ("tras", 0.0, hz - 1.0, -0.5))
    for i, h in enumerate(alturas):
        x1 = -hw + i * w
        x2 = x1 + w
        lado = -1 if i < len(alturas) / 2 else 1
        inclina = 0.6 * lado if abs(i - 3.5) >= 1.5 else 0.0
        for nom, z1, z2, dh in capas:
            alto = h + dh
            corte = base + alto * 0.6
            _caja(els, m, f"pluma_{i}_{nom}_a", x1 + 0.04, base, z1, x2 - 0.04, corte, z2)
            _caja(els, m, f"pluma_{i}_{nom}_b", x1 + 0.04 + inclina, corte, z1,
                  x2 - 0.04 + inclina, base + alto, z2)
    return els


def gen_pelo(p):
    """Mechones de 1 px a los lados y atras de la cabeza, con largos irregulares."""
    m = _medidas(p)
    els = []
    hw, hz, hb = m["hw"], m["hz"], m["yt"]
    tope = hb + 6.5                                # debajo de la corona
    largos = [1.0, 2.0, 0.5, 1.75, 1.25, 2.25, 0.75]
    n = 0
    for k, i in enumerate(range(-int(hw), int(hw))):          # espalda
        _caja(els, m, f"pelo_{n}", i, hb + largos[k % 7], hz, i + 1, tope, hz + 1); n += 1
    for lado in (-1, 1):                                       # costados
        for k, j in enumerate(range(-2, int(hz))):
            x1, x2 = sorted((lado * hw, lado * (hw + 1)))
            _caja(els, m, f"pelo_{n}", x1, hb + largos[(k + 3) % 7], j, x2, tope, j + 1); n += 1
    return els


def gen_cuerpo(p):
    """Torso, brazos, piernas y botas lisos (la base del esqueleto). Brazo/pierna 'izq' = x negativa."""
    m = _medidas(p)
    els = []
    a, yb, yt = m["a"], m["yb"], m["yt"]
    _caja(els, m, "torso", -a, yb, -m["b"], a, yt, m["b"])
    ax1 = a - 0.5                                  # el brazo se mete 0.5 px en el torso
    ax2 = ax1 + m["brazo"]
    for lado, nom in ((-1, "izq"), (1, "der")):
        x1, x2 = sorted((lado * ax1, lado * ax2))
        _caja(els, m, f"brazo_{nom}", x1, yb + 1.0, -1.0, x2, yt, 1.0)
        x1, x2 = sorted((lado * 1.0, lado * 3.0))
        _caja(els, m, f"pierna_{nom}", x1, yb - 3.0, -1.0, x2, yb, 1.0)
        x1, x2 = sorted((lado * 0.75, lado * 3.25))
        _caja(els, m, f"bota_{nom}_pie", x1, yb - 5.0, -2.25, x2, yb - 3.5, 1.25)
        _caja(els, m, f"bota_{nom}_cana", x1, yb - 3.5, -1.25, x2, yb - 2.0, 1.25)
    return els


def gen_cabeza(p):
    """Cabeza propia 10x10x8: nuca maciza y capa frontal de 1 px con dos huecos para los ojos (+ ojos y vigote)."""
    m = _medidas(p)
    els = []
    hw, hz, hb = m["hw"], m["hz"], m["yt"]
    y_ojo1, y_ojo2 = hb + 3.25, hb + 5.75
    _caja(els, m, "cabeza_nuca", -hw, hb, -hz + 1.0, hw, hb + 10.0, hz)
    _caja(els, m, "cabeza_frente_abajo", -hw, hb, -hz, hw, y_ojo1, -hz + 1.0)
    _caja(els, m, "cabeza_frente_arriba", -hw, y_ojo2, -hz, hw, hb + 10.0, -hz + 1.0)
    _caja(els, m, "cabeza_frente_izq", -hw, y_ojo1, -hz, -4.0, y_ojo2, -hz + 1.0)
    _caja(els, m, "cabeza_frente_centro", -1.0, y_ojo1, -hz, 1.0, y_ojo2, -hz + 1.0)
    _caja(els, m, "cabeza_frente_der", 4.0, y_ojo1, -hz, hw, y_ojo2, -hz + 1.0)
    return els + _cara(p, tallada=True)


def _grupo_de(nombre):
    """Hueso (ruta de grupo) al que pertenece cada pieza del modelo completo."""
    lado = "Izq." if "_izq" in nombre else ("Der." if "_der" in nombre else None)
    if nombre.startswith(("hombrera_", "guante_", "brazo_")):
        return f"Cuerpo/Parte Alta/Brazo {lado}"
    if nombre.startswith(("pierna_", "bota_")):
        return f"Cuerpo/Parte Baja/Pierna {lado}"
    if nombre.startswith(("cabeza_", "ojo_", "vigote", "corona_", "pluma_", "pelo_")):
        return "Cuerpo/Parte Alta/Cabeza"
    if nombre.startswith(("torso", "cinturon_", "hebilla_")):
        return "Cuerpo/Parte Alta/Torso"
    if nombre.startswith("faldon_"):
        return "Cuerpo/Faldon"
    return "Cuerpo"


def gen_modelo_completo(p):
    """Modelo entero con esqueleto: cuerpo + cabeza con ojos hundidos + faldon + hombreras + cinturon + guantes
    + corona + plumas (+ pelo). Cada pieza lleva 'grupo' (hueso); se guarda como .bbmodel."""
    els = gen_cuerpo(p) + gen_cabeza(p) + gen_faldon_voxel(p)
    for g in (gen_cinturon, gen_guantes, gen_corona, gen_plumas):
        els += g(p)
    if int(p["pelo"]) > 0:
        els += gen_pelo(p)
    for e in els:
        e["grupo"] = _grupo_de(e["name"])
    return els


def gen_personaje(p):
    """Accesorios para tu cuerpo ya existente: faldon + hombreras + cinturon + guantes + cara + corona + plumas (+ pelo)."""
    els = gen_faldon_voxel(p)
    for g in (gen_cinturon, gen_guantes, gen_cara, gen_corona, gen_plumas):
        els += g(p)
    if int(p["pelo"]) > 0:
        els += gen_pelo(p)
    return els


# ----------------------------------------------------------------------
# HERRAMIENTAS DE MANO (escala Minecraft: personaje = 32 px = 2 bloques)
# Todas: verticales, base (mango) en y=0, centradas en x=z=0, cabeza hacia +Y.
# 'alto' = largo total, 'ancho' = grosor del mango, 'detalle' = 1..3 (mas adornos).
# Nombres: cuerpo_* (madera/negro), oro_* (dorado), metal_* (hoja/cabeza).
# ----------------------------------------------------------------------

def _octo(els, nombre, w, y1, y2, cx=0.0, cz=0.0):
    """Prisma octogonal: dos cubos iguales, uno girado 45 grados. Si es muy fino, un solo cubo."""
    c = w / 2
    els.append(cubo(f"{nombre}_a", cx - c, y1, cz - c, cx + c, y2, cz + c))
    if w >= 1.75 / PX_POR_BLOQUE:
        els.append(cubo(f"{nombre}_b", cx - c, y1, cz - c, cx + c, y2, cz + c,
                        origen=(cx, (y1 + y2) / 2, cz), rot=(0, 45, 0)))


def _det(p):
    return max(1, min(3, int(p["detalle"])))


def gen_baston(p):
    """
    Baston tipo Jingu Bang (Wukong): cuerpo octogonal + remate dorado de 5 piezas en cada extremo
    (labio, aro grueso con tachones, ranura, aro fino, cono) + bandas finas en el cuerpo.
    """
    L, g, det = p["alto"], max(0.03, p["ancho"]), _det(p)
    els = []
    _octo(els, "cuerpo", g, 0.0, L)

    cl = L * 0.14                                            # largo de cada remate
    piezas = [(0.00, 0.12, 1.90), (0.12, 0.62, 1.55), (0.62, 0.70, 1.20),
              (0.70, 0.84, 1.75), (0.84, 1.00, 1.30)]       # (inicio, fin, ancho) desde la punta
    for fin, signo in (("base", 1), ("tope", -1)):
        for i, (a, b, k) in enumerate(piezas):
            s1, s2 = a * cl, b * cl
            y1, y2 = (s1, s2) if signo == 1 else (L - s2, L - s1)
            _octo(els, f"oro_{fin}_{i}", g * k, y1, y2)
        if det >= 2:                                         # tachones en el aro grueso
            s1, s2 = piezas[1][0] * cl, piezas[1][1] * cl
            ym = (s1 + s2) / 2 if signo == 1 else L - (s1 + s2) / 2
            r = g * 1.55 / 2
            t = max(g * 0.2, 0.3 / PX_POR_BLOQUE)           # medio lado del tachon
            dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if det == 3:
                dirs += [(0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]
            for j, (dx, dz) in enumerate(dirs):
                cx, cz = dx * (r + t * 0.4), dz * (r + t * 0.4)
                els.append(cubo(f"oro_{fin}_tachon_{j}", cx - t, ym - t, cz - t, cx + t, ym + t, cz + t,
                                origen=(cx, ym, cz), rot=(0, 45 if (dx and dz) else 0, 0)))

    pos = {1: [0.5], 2: [0.5, 0.3, 0.7], 3: [0.5, 0.35, 0.65, 0.2, 0.8]}[det]
    for i, f in enumerate(pos):
        oy = g * 0.22
        _octo(els, f"oro_banda_{i}", g * (1.4 if i == 0 else 1.25), L * f - oy, L * f + oy)
    return els


def gen_varita(p):
    """Varita: pomo, mango con anillos, cuerpo que se afina, engaste y cristal. det 3: nudos en la rama."""
    L, g, det = p["alto"], max(0.02, p["ancho"]), _det(p)
    els = []
    partes = [(0.00, 0.07, 2.6, "oro_pomo"), (0.07, 0.33, 1.9, "cuerpo_mango"),
              (0.33, 0.39, 2.5, "oro_anillo"), (0.39, 0.62, 1.4, "cuerpo_a"),
              (0.62, 0.80, 1.15, "cuerpo_b"), (0.80, 0.89, 0.9, "cuerpo_c"),
              (0.89, 0.93, 1.8, "oro_engaste"), (0.93, 1.00, 1.7, "oro_cristal")]
    for a, b, k, n in partes:
        _octo(els, n, g * k, a * L, b * L)
    if det >= 2:
        for i, (a, b) in enumerate(((0.13, 0.16), (0.22, 0.25))):
            _octo(els, f"oro_grip_{i}", g * 2.1, a * L, b * L)
    if det == 3:
        n = max(0.3 / PX_POR_BLOQUE, g * 0.3)
        for i, (f, dx, dz, r) in enumerate(((0.47, 1, 0, 0.9), (0.56, -1, 0, 0.8), (0.68, 0, 1, 0.65))):
            cx, cz = dx * (g * r), dz * (g * r)
            els.append(cubo(f"cuerpo_nudo_{i}", cx - n, L * f - n, cz - n, cx + n, L * f + n, cz + n))
    return els


def gen_lanza(p):
    """Lanza: contera dorada, asta, bandas, collar y punta de hoja escalonada con nervio y borlas."""
    L, g, det = p["alto"], max(0.02, p["ancho"]), _det(p)
    els = []
    _octo(els, "oro_contera", g * 1.5, 0.0, 0.03 * L)
    _octo(els, "cuerpo_asta", g, 0.03 * L, 0.80 * L)
    for i, f in enumerate({1: [0.5], 2: [0.5, 0.3, 0.68], 3: [0.5, 0.3, 0.68, 0.15, 0.4]}[det]):
        _octo(els, f"oro_banda_{i}", g * 1.35, L * f - g * 0.25, L * f + g * 0.25)
    _octo(els, "oro_collar", g * 1.9, 0.78 * L, 0.82 * L)
    zt = max(g * 0.5, 0.5 / PX_POR_BLOQUE)
    hoja = [(0.82, 0.87, 1.6), (0.87, 0.91, 2.4), (0.91, 0.95, 1.8), (0.95, 0.98, 1.1), (0.98, 1.00, 0.5)]
    for i, (a, b, k) in enumerate(hoja):
        w = g * k
        els.append(cubo(f"metal_hoja_{i}", -w / 2, a * L, -zt / 2, w / 2, b * L, zt / 2))
    if det >= 2:
        w, z = g * 0.3, zt / 2 + 0.2 / PX_POR_BLOQUE
        els.append(cubo("metal_nervio", -w / 2, 0.84 * L, -z, w / 2, 0.97 * L, z))
        for i, lado in enumerate((-1, 1)):
            x = lado * g * 0.9
            els.append(cubo(f"cuerpo_borla_{i}", x - g * 0.25, 0.70 * L, -g * 0.25, x + g * 0.25, 0.78 * L, g * 0.25))
    return els


def gen_hacha(p):
    """Hacha: mango con pomo, collar y cabeza escalonada (3 columnas que crecen hacia el filo) con contrapeso atras."""
    L, g, det = p["alto"], max(0.03, p["ancho"]), _det(p)
    els = []
    _octo(els, "cuerpo_mango", g, 0.0, L)
    _octo(els, "oro_pomo", g * 1.6, 0.0, 0.05 * L)
    if det >= 2:
        for i, f in enumerate((0.12, 0.2)):
            _octo(els, f"oro_grip_{i}", g * 1.3, f * L, f * L + g * 0.4)
    yh1, yh2 = 0.60 * L, 0.98 * L
    H, ym = yh2 - yh1, (yh1 + yh2) / 2
    _octo(els, "metal_cuello", g * 1.6, yh1, yh2)
    cw, x0 = 0.10 * L, g * 0.8
    cols = [(0.70, 1.4), (0.90, 1.0), (1.00, 0.6)]          # (alto relativo, grosor relativo a g)
    for i, (hr, tk) in enumerate(cols):
        x1, x2 = x0 + i * cw, x0 + (i + 1) * cw
        els.append(cubo(f"metal_hoja_{i}", x1, ym - H * hr / 2, -g * tk / 2, x2, ym + H * hr / 2, g * tk / 2))
    els.append(cubo("metal_contrapeso", -g * 1.7, ym - H * 0.3, -g * 0.7, -g * 0.8, ym + H * 0.3, g * 0.7))
    if det == 3:
        els.append(cubo("oro_filo", x0 + 3 * cw, ym - H * 0.45, -g * 0.2, x0 + 3 * cw + g * 0.35, ym + H * 0.45, g * 0.2))
    return els


def gen_pico(p):
    """Pico: mango y cabeza en arco hecha de escalones que bajan hacia las puntas finas."""
    L, g, det = p["alto"], max(0.03, p["ancho"]), _det(p)
    els = []
    _octo(els, "cuerpo_mango", g, 0.0, L)
    _octo(els, "oro_pomo", g * 1.6, 0.0, 0.05 * L)
    if det >= 2:
        for i, f in enumerate((0.12, 0.2)):
            _octo(els, f"oro_grip_{i}", g * 1.3, f * L, f * L + g * 0.4)
    yt = 0.94 * L
    seg = 0.09 * L
    _octo(els, "metal_centro", g * 1.7, yt - g * 0.9, yt + g * 0.9)
    espesor = [1.5, 1.2, 0.9, 0.5]                          # alto de cada escalon (x g)
    zt = [1.2, 1.0, 0.8, 0.5]
    for lado, nom in ((1, "der"), (-1, "izq")):
        x = g * 0.85
        yc = yt
        for i in range(4):
            x1, x2 = sorted((lado * x, lado * (x + seg)))
            h, z = g * espesor[i], g * zt[i]
            els.append(cubo(f"metal_{nom}_{i}", x1, yc - h / 2, -z / 2, x2, yc + h / 2, z / 2))
            x += seg
            yc -= 0.035 * L
    if det >= 2:
        _octo(els, "oro_atadura_0", g * 1.5, yt - g * 1.5, yt - g * 1.1)
        _octo(els, "oro_atadura_1", g * 1.5, yt + g * 1.1, yt + g * 1.5)
    if det == 3:
        els.append(cubo("metal_remate", -g * 0.4, yt + g * 0.9, -g * 0.4, g * 0.4, yt + g * 2.0, g * 0.4))
    return els


def gen_pala(p):
    """Pala: empunadura en T abajo, mango, collar y hoja ancha que se redondea en la punta."""
    L, g, det = p["alto"], max(0.03, p["ancho"]), _det(p)
    els = []
    _octo(els, "cuerpo_mango", g, g, 0.80 * L)
    els.append(cubo("cuerpo_empunadura", -g * 2.2, 0.0, -g * 0.55, g * 2.2, g, g * 0.55))
    if det >= 2:
        _octo(els, "oro_banda_0", g * 1.35, 0.35 * L, 0.35 * L + g * 0.45)
    _octo(els, "metal_cuello", g * 1.6, 0.78 * L, 0.84 * L)
    zt = max(g * 0.6, 0.5 / PX_POR_BLOQUE)
    hoja = [(0.82, 0.87, 1.8), (0.87, 0.92, 3.0), (0.92, 0.96, 3.4), (0.96, 0.99, 2.6), (0.99, 1.00, 1.4)]
    for i, (a, b, k) in enumerate(hoja):
        w = g * k
        els.append(cubo(f"metal_hoja_{i}", -w / 2, a * L, -zt / 2, w / 2, b * L, zt / 2))
    if det >= 2:
        w, z = g * 0.35, zt / 2 + 0.2 / PX_POR_BLOQUE
        els.append(cubo("metal_nervio", -w / 2, 0.84 * L, -z, w / 2, 0.97 * L, z))
    return els


def gen_martillo(p):
    """Martillo de guerra: mango con pomo y bandas; cabeza de bloque con aros dorados y caras en ambos lados."""
    L, g, det = p["alto"], max(0.03, p["ancho"]), _det(p)
    els = []
    _octo(els, "cuerpo_mango", g, 0.0, 0.93 * L)
    _octo(els, "oro_pomo", g * 1.7, 0.0, 0.06 * L)
    if det >= 2:
        for i, f in enumerate((0.14, 0.22)):
            _octo(els, f"oro_grip_{i}", g * 1.35, f * L, f * L + g * 0.4)
    hx, hy, hz = 0.36 * L, 0.22 * L, 0.24 * L
    ym = 0.82 * L
    els.append(cubo("metal_cabeza", -hx * 0.3, ym - hy / 2, -hz / 2, hx * 0.3, ym + hy / 2, hz / 2))
    for lado, nom in ((1, "der"), (-1, "izq")):
        x1, x2 = sorted((lado * hx * 0.3, lado * hx * 0.42))
        els.append(cubo(f"oro_aro_{nom}", x1, ym - hy * 0.56, -hz * 0.56, x2, ym + hy * 0.56, hz * 0.56))
        x1, x2 = sorted((lado * hx * 0.42, lado * hx * 0.5))
        els.append(cubo(f"metal_cara_{nom}", x1, ym - hy * 0.45, -hz * 0.45, x2, ym + hy * 0.45, hz * 0.45))
    if det >= 2:
        _octo(els, "oro_cuello_0", g * 1.5, ym - hy / 2 - g * 0.5, ym - hy / 2)
        _octo(els, "oro_cuello_1", g * 1.5, ym + hy / 2, ym + hy / 2 + g * 0.5)
    if det == 3:
        els.append(cubo("metal_pico_top", -g * 0.5, ym + hy / 2 + g * 0.5, -g * 0.5, g * 0.5, ym + hy / 2 + g * 1.8, g * 0.5))
    return els


# ======================================================================
# Registro de tipos: defaults (en bloques) + generador
# ======================================================================

# ======================================================================
# PERSONAJES DE VELKIA
# Player NORMAL de Minecraft (cabeza 8x8x8, torso 8x12x4, brazos/piernas 4x12x4, 32 px de alto,
# pies en y=0, frente = -Z) con pelo y ropa en 3D hechos de cubos. Cada cubo lleva 'color' (hex)
# y 'grupo' (hueso). Se guardan como .bbmodel con una textura de paleta ya pintada.
# ======================================================================

G_CAB = "Cuerpo/Cabeza"
G_TOR = "Cuerpo/Torso"
G_BR = "Cuerpo/Brazo {L}"
G_PI = "Cuerpo/Pierna {L}"
G_CAPA = "Cuerpo/Torso/Capa"
G_FAL = "Cuerpo/Falda"

ORO = "#E3B04B"
ORO_OSC = "#B9852E"


def _hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _tono(h, f):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v * f)))) for v in _hex_rgb(h))


class _Pieza:
    """Acumula cubos en PX (se convierten a bloques al guardarlos, igual que el resto de generadores)."""

    def __init__(self, semilla):
        self.els = []
        self.rng = random.Random(semilla)

    def caja(self, nombre, x1, y1, z1, x2, y2, z2, color, grupo, piv=None, rot=None, jit=0.0):
        if jit:
            color = _tono(color, 1 + self.rng.uniform(-jit, jit))
        if rot is not None and piv is None:
            piv = ((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2)
        e = cubo(nombre, x1 / 16, y1 / 16, z1 / 16, x2 / 16, y2 / 16, z2 / 16,
                 origen=None if piv is None else (piv[0] / 16, piv[1] / 16, piv[2] / 16), rot=rot)
        e["color"] = color
        if "{L}" in grupo:
            grupo = grupo.replace("{L}", "Der." if (x1 + x2) > 0 else "Izq.")
        e["grupo"] = grupo
        self.els.append(e)

    def centro(self, nombre, cx, cy, cz, sx, sy, sz, color, grupo, rot=None, jit=0.0):
        self.caja(nombre, cx - sx / 2, cy - sy / 2, cz - sz / 2, cx + sx / 2, cy + sy / 2, cz + sz / 2,
                  color, grupo, rot=rot, jit=jit)

    def lr(self, nombre, x1, y1, z1, x2, y2, z2, color, grupo, piv=None, rot=None, jit=0.0):
        """Pieza simetrica. x1,x2 se dan en el lado derecho (+X); el izquierdo se refleja."""
        for lado, suf in ((-1, "izq"), (1, "der")):
            xa, xb = sorted((lado * x1, lado * x2))
            pv = None if piv is None else (lado * piv[0], piv[1], piv[2])
            rt = None if rot is None else (rot[0], lado * rot[1], lado * rot[2])
            self.caja(f"{nombre}_{suf}", xa, y1, z1, xb, y2, z2, color, grupo, piv=pv, rot=rt, jit=jit)


# ---------------------------------------------------------------- datos
PERSONAJES = {
    "revoltir": dict(
        desc="Semidiós de la risa · Caos. Joven, inquieto, bromista. Bufanda naranja, ropa crema, cintas y detalles dorados.",
        piel="#E3A57C", ojos="#D9772B", pelo="#17120F", pelo2=ORO, pelo_estilo="puntas", cabeza=["flor"],
        base="#F1E2C6", pantalon="#6B3F26", botas="#5A3520", botas2=ORO,
        bata=dict(largo="corta", colores=["#E8832A", "#F1E2C6", "#C96A1E", "#6B3F26"], ribete=ORO),
        mangas="#F1E2C6", mangas2="#E8832A", bufanda=("#E8832A", "grande", True),
        hombreras=("#8A4E2A", ORO), cinturon=("#6B3F26", ORO), cintas="#E8832A", brazaletes=ORO),
    "correcthar": dict(
        desc="Semidiós de la redención · Orden. Sereno, paciente, preciso. Túnica azul marino con paneles celestes y crema.",
        piel="#E7B48F", ojos="#3C5BA0", pelo="#1F2447", pelo2="#8FA3C9", pelo_estilo="lado", cabeza=[],
        base="#232B52", pantalon="#1B2040", botas="#1B2040", botas2="#7FA7C4",
        bata=dict(largo="media", colores=["#232B52", "#7FA7C4", "#EDE3D0", "#2E3A6E"], ribete="#4FA3A5"),
        mangas="#232B52", mangas2="#7FA7C4", bufanda=("#8FB4D4", "pequena", True),
        cinturon=("#2B2F55", "#4FA3A5"), banda=("#4FA3A5", "#EDE3D0"), brazaletes="#4FA3A5"),
    "bashi": dict(
        desc="Semidiós del conocimiento · Sabiduría. Gafas, etiquetas flotando, túnica azul oscuro con detalles turquesa y dorados.",
        piel="#E3AE88", ojos="#6A8CC0", pelo="#17151F", pelo2="#2F4A8A", pelo_estilo="revuelto",
        cabeza=["gafas", "etiquetas"],
        base="#1F2447", pantalon="#16182E", botas="#16182E", botas2=ORO,
        bata=dict(largo="larga", colores=["#1F2447", "#EDE3D0", "#2B3466", "#1F2447"], ribete=ORO),
        mangas="#1F2447", mangas2="#EDE3D0", bufanda=("#3D9EA0", "pequena", False),
        cinturon=("#3B2A1E", ORO), banda=("#3D9EA0", ORO), libro=True, brazaletes="#3D9EA0"),
    "pibble": dict(
        desc="Semidiós errante · Diversión. Cara negra con ojos naranja brillantes, corona de plumas de colores, amuletos y tótems.",
        piel="#D9A06B", ojos="#F28A2E", pelo="#141012", pelo2="#141012", pelo_estilo="ninguno",
        cabeza=["mascara", "plumas"],
        base="#C2402E", pantalon="#5A3520", botas="#E3B04B", botas2="#3FA7A6",
        bata=dict(largo="corta", colores=["#C2402E", "#F1E2C6", "#3FA7A6", "#E3B04B"], ribete="#3FA7A6"),
        mangas="#C2402E", mangas2="#E3B04B", bufanda=("#C2402E", "grande", True),
        hombreras=("#3FA7A6", ORO), cinturon=("#5A3520", ORO), amuletos=True, brazaletes="#3FA7A6"),
    "khaset": dict(
        desc="Rey de Thza · Protector. Corona dorada, túnica larga crema, hombreras marrones con sol dorado y capa.",
        piel="#C98E5E", ojos="#4A2E1A", pelo="#3A2415", pelo2="#5A3A22", pelo_estilo="corto", cabeza=["corona"],
        base="#7A4A2A", pantalon="#5A3520", botas="#5A3520", botas2=ORO,
        bata=dict(largo="larga", colores=["#F1E4CC", "#E8D9BC", "#F6EEDB", "#D9C49E"], ribete=ORO, abierta=True),
        mangas="#F1E4CC", mangas2="#7A4A2A", bufanda=("#8A5A32", "grande", False),
        capa=dict(color="#F1E4CC", color2="#D9C49E", largo=2.5),
        hombreras=("#7A4A2A", ORO), cinturon=("#5A3520", ORO), guantes=("#6B3F26", ORO), emblema=ORO,
        banda=("#8A5A32", ORO)),
    "kemira": dict(
        desc="Reina de Thza · Exploradora. Curiosa y escandalosa; vestido azul con estrellas, falda crema, tiara y capa estrellada.",
        piel="#D9A57A", ojos="#8A5A2A", pelo="#1A1620", pelo2="#2A2433", pelo_estilo="largo", cabeza=["tiara"],
        base="#232B5E", pantalon="#1B2040", botas="#1B2040", botas2=ORO,
        bata=dict(largo="media", colores=["#F2E8D3", "#E9DDC2", "#F6EEDB", "#DCCFAE"],
                  arriba=["#232B5E", "#2B3470", "#232B5E"], ribete=ORO, abierta=True),
        mangas="#F2E8D3", mangas2="#232B5E", bufanda=("#F2E8D3", "pequena", False),
        capa=dict(color="#232B5E", color2="#2B3470", largo=3.0, estrellas=True),
        cinturon=("#8A5A2A", ORO), banda=(ORO, "#232B5E"), estrellas=12, brazaletes=ORO),
    "meron": dict(
        desc="Dios de Velkia. Alegría, libertad y caos controlado. Bufanda crema enorme, túnica crema y dorada, laurel dorado.",
        piel="#DDAA80", ojos="#7A4B2A", pelo="#1B1410", pelo2="#2C2018", pelo_estilo="rizos", cabeza=["laurel"],
        laurel=ORO,
        base="#231A14", pantalon="#231A14", botas="#2A1E16", botas2="#F1E2C6",
        bata=dict(largo="media", colores=["#F1E2C6", "#E8D3A8", "#F7EEDA", "#D9B974"], ribete=ORO, abierta=True),
        mangas="#F1E2C6", mangas2="#E8D3A8", bufanda=("#F1E2C6", "grande", True),
        cinturon=("#C99434", "#F1E2C6"), brazaletes=ORO),
    "anteros": dict(
        desc="Dios de Aseris. Disciplina, estrategia, equilibrio. Capa verde del bosque, túnica oscura, laurel verde.",
        piel="#D5A27A", ojos="#3E7A4A", pelo="#14100E", pelo2="#221A14", pelo_estilo="rizos", cabeza=["laurel"],
        laurel="#2F5B34",
        base="#1E1B1A", pantalon="#1A1716", botas="#221C18", botas2="#CFCBB8",
        bata=dict(largo="media", colores=["#1E1B1A", "#2A2A26", "#CFCBB8", "#274B2E"], ribete="#2F5B34", abierta=True),
        mangas="#274B2E", mangas2="#1E1B1A", bufanda=("#2F5B34", "grande", False),
        capa=dict(color="#274B2E", color2="#33603A", largo=1.5, capucha=True),
        cinturon=("#3B2A1E", "#CFCBB8"), brazaletes="#CFCBB8"),
}


# ---------------------------------------------------------------- base y cara
def _v_base(P, c):
    sk = c["piel"]
    P.lr("pierna", 0, 0, -2, 4, 12, 2, c["pantalon"], G_PI, jit=0.03)
    P.lr("bota", 0, 0, -2.4, 4.3, 4, 2.3, c["botas"], G_PI)
    P.lr("bota_punta", 0, 0, -3.3, 4.3, 2, -2.4, c["botas"], G_PI)
    P.lr("bota_borde", 0, 4, -2.5, 4.4, 5.2, 2.4, c["botas2"], G_PI)
    P.caja("torso", -4, 12, -2, 4, 24, 2, c["base"], G_TOR)
    P.lr("brazo_mano", 4, 12, -2, 8, 16.5, 2, sk, G_BR)
    P.lr("brazo_manga", 4, 16.5, -2, 8, 24, 2, c["base"], G_BR)
    P.caja("cabeza", -4, 24, -4, 4, 32, 4, sk, G_CAB)


def _v_cara(P, c):
    if "mascara" in c["cabeza"]:
        P.caja("mascara", -4.4, 23.8, -4.4, 4.4, 32.4, 4.4, "#141012", G_CAB)
        P.lr("ojo_brillo", 1, 26.5, -4.75, 2.9, 28.6, -4.4, c["ojos"], G_CAB)
        P.lr("ojo_nucleo", 1.5, 27, -4.9, 2.4, 28.1, -4.75, "#FFD36B", G_CAB)
        P.caja("marca_frente", -0.8, 29.6, -4.8, 0.8, 31.4, -4.4, "#C2402E", G_CAB)
        return
    sk2 = _tono(c["piel"], 0.86)
    P.lr("ojo_blanco", 0.9, 26.6, -4.25, 3.1, 28.2, -4.0, "#F4EFE6", G_CAB)
    P.lr("ojo_iris", 1.3, 26.6, -4.4, 3.1, 28.2, -4.25, c["ojos"], G_CAB)
    P.lr("ojo_pupila", 1.9, 26.8, -4.5, 2.7, 27.8, -4.4, "#15110E", G_CAB)
    P.lr("ceja", 0.8, 28.7, -4.35, 3.4, 29.3, -4.0, c["pelo"], G_CAB)
    P.caja("nariz", -0.5, 25.8, -4.35, 0.5, 26.7, -4.0, sk2, G_CAB)
    P.caja("boca", -1.3, 24.9, -4.2, 1.3, 25.5, -4.0, "#8A4B3A", G_CAB)


# ---------------------------------------------------------------- pelo 3D
def _v_pelo(P, c):
    st = c["pelo_estilo"]
    if st == "ninguno":
        return
    h, h2, r, G = c["pelo"], c["pelo2"], P.rng, G_CAB
    P.caja("pelo_tapa", -4.5, 31.2, -4.5, 4.5, 32.7, 4.5, h, G, jit=0.05)
    P.caja("pelo_nuca", -4.5, 25.5, 3.0, 4.5, 32.7, 4.6, h, G, jit=0.05)
    P.lr("pelo_lado", 4, 27.5, -1.2, 4.6, 32.7, 4.6, h, G, jit=0.05)

    largos = {"puntas": [1.2, 2.4, 1.6, 3.0, 2.0, 2.8, 1.4, 2.2],
              "revuelto": [2.0, 3.0, 2.4, 1.6, 3.0, 2.2, 2.8, 1.8],
              "lado": [3.0, 2.8, 2.6, 2.2, 2.0, 1.6, 1.2, 1.0],
              "largo": [2.4, 3.0, 2.2, 1.2, 1.2, 2.2, 3.0, 2.4],
              "corto": [1.6, 2.0, 1.4, 1.8, 1.8, 1.4, 2.0, 1.6],
              "rizos": [2.0, 2.8, 1.6, 2.4, 2.4, 1.6, 2.8, 2.0]}[st]
    n = len(largos)
    w = 9.2 / n
    for i, ln in enumerate(largos):
        x1 = -4.6 + i * w
        col = h2 if (st == "lado" and i < 3 and i % 2 == 0) else h
        P.caja(f"pelo_flequillo_{i}", x1, 32.7 - ln, -4.7, x1 + w, 32.7, -4.0, col, G, jit=0.07)

    if st in ("puntas", "revuelto", "corto"):
        esc, cant = {"puntas": (1.0, 9), "revuelto": (0.65, 7), "corto": (0.4, 5)}[st]
        for i in range(cant):
            x, z = r.uniform(-3.8, 3.8), r.uniform(-3.6, 3.4)
            hh, ww = r.uniform(1.6, 3.6) * esc, r.uniform(1.2, 1.9)
            col = h2 if r.random() < 0.2 else h
            P.caja(f"pelo_pua_{i}", x - ww / 2, 32.5, z - ww / 2, x + ww / 2, 32.5 + hh, z + ww / 2, col, G,
                   piv=(x, 32.5, z), rot=(r.uniform(-15, 15), 0, r.uniform(-28, 28) * ROT_Z_SIGNO), jit=0.06)
        for lado in (-1, 1):
            for j in range(3 if st != "corto" else 1):
                z = -2 + j * 2.4 + r.uniform(-0.4, 0.4)
                ln = r.uniform(1.5, 3.0) * (1.0 if st == "puntas" else 0.8)
                y = 29 + r.uniform(0, 2.5)
                xa, xb = sorted((lado * 4.5, lado * (4.5 + ln)))
                P.caja(f"pelo_mechon_{lado}_{j}", xa, y, z, xb, y + 1.4, z + 1.4,
                       h2 if r.random() < 0.15 else h, G, jit=0.06)
        for i in range(6):
            x = -4.4 + i * 1.5
            P.caja(f"pelo_cola_{i}", x, 24.6 + r.uniform(0, 1.5), 4.2, x + 1.5, 25.8, 5.3, h, G, jit=0.06)

    elif st == "rizos":
        for i in range(44):
            a = r.uniform(-math.pi, math.pi)
            y = r.uniform(27.5, 33.8)
            if abs(a) < 1.15 and y < 30.4:
                continue
            m = max(abs(math.sin(a)), abs(math.cos(a)))
            f = r.uniform(0.15, 1.0) if y > 32.2 else 1.0
            R = (4.5 + r.uniform(0, 0.8)) / m * f
            s = r.uniform(1.7, 2.7)
            col = h2 if r.random() < 0.12 else h
            P.centro(f"pelo_rizo_{i}", R * math.sin(a), y, -R * math.cos(a), s, s * r.uniform(0.8, 1.1), s, col, G,
                     rot=(0, r.choice([0, 22.5, 45]), 0), jit=0.06)

    elif st == "largo":
        k = 8
        wk = 9.4 / k
        for i in range(k):
            x1 = -4.7 + i * wk
            hem = r.choice([14.0, 15.0, 16.5, 15.5, 13.5, 16.0, 14.5, 15.0])
            P.caja(f"pelo_espalda_{i}", x1, hem, 4.0, x1 + wk, 31.5, 5.3, h, G, jit=0.06)
        P.lr("pelo_mechon_largo", 4.1, 16.5, -3.6, 5.4, 31, -2.0, h, G, jit=0.05)
        P.lr("pelo_mechon_punta", 4.3, 14.6, -3.4, 5.2, 16.6, -2.2, h2, G, jit=0.05)

    elif st == "lado":
        for i, (x, hh) in enumerate([(-2.5, 2.0), (0.5, 2.6), (2.8, 1.8)]):
            P.caja(f"pelo_mecha_{i}", x - 1.0, 32.5, -3.0 + i * 1.5, x + 1.0, 32.5 + hh, -1.0 + i * 1.5, h2, G,
                   piv=(x, 32.5, 0), rot=(0, 0, (-1) ** i * 12 * ROT_Z_SIGNO), jit=0.05)
        P.lr("pelo_patilla", 4, 26.2, -3.2, 4.6, 29, -1.0, h, G, jit=0.05)
        P.caja("pelo_nuca_baja", -4.3, 23.5, 3.0, 4.3, 25.6, 4.4, h, G, jit=0.05)


# ---------------------------------------------------------------- accesorios de cabeza
def _v_laurel(P, c):
    col, r = c.get("laurel", ORO), P.rng
    n = 16
    for i in range(n):
        a = 2 * math.pi * i / n
        m = max(abs(math.sin(a)), abs(math.cos(a)))
        R = 4.95 / m
        P.centro(f"laurel_{i}", R * math.sin(a), 31.2 + (i % 2) * 0.55, -R * math.cos(a), 1.7, 1.0, 1.7, col, G_CAB,
                 rot=(r.uniform(-12, 12), math.degrees(a) * ROT_Y_SIGNO, 0), jit=0.08)


def _v_corona(P, c):
    G = G_CAB
    P.caja("corona_frente", -4.9, 32.3, -5.1, 4.9, 34.0, -4.6, ORO, G)
    P.caja("corona_espalda", -4.9, 32.3, 4.6, 4.9, 34.0, 5.1, ORO, G)
    P.lr("corona_lado", 4.6, 32.3, -4.6, 5.1, 34.0, 4.6, ORO, G)
    for i, (x, hh) in enumerate([(-3.6, 1.8), (-1.8, 2.8), (0.0, 4.2), (1.8, 2.8), (3.6, 1.8)]):
        P.caja(f"corona_pua_f{i}", x - 0.6, 34.0, -5.1, x + 0.6, 34.0 + hh, -4.6, ORO, G, jit=0.04)
    for i, x in enumerate((-3.0, 0.0, 3.0)):
        P.caja(f"corona_pua_t{i}", x - 0.6, 34.0, 4.6, x + 0.6, 36.0 if i == 1 else 35.2, 5.1, ORO, G)
    P.lr("corona_pua_lado", 4.6, 34.0, -0.6, 5.1, 35.4, 0.6, ORO, G)
    P.caja("corona_gema", -0.6, 32.7, -5.4, 0.6, 33.7, -5.1, "#C2402E", G)


def _v_tiara(P, c):
    G = G_CAB
    P.caja("tiara_frente", -4.8, 31.6, -5.0, 4.8, 32.8, -4.6, ORO, G)
    P.lr("tiara_lado", 4.6, 31.6, -4.6, 5.0, 32.8, 1.5, ORO, G)
    for i, (x, hh) in enumerate([(0.0, 3.0), (-2.2, 1.6), (2.2, 1.6)]):
        P.caja(f"tiara_pua_{i}", x - 0.6, 32.8, -5.0, x + 0.6, 32.8 + hh, -4.6, ORO, G)
    P.caja("tiara_gema", -0.5, 31.9, -5.3, 0.5, 32.7, -5.0, "#6FB2D8", G)
    for i, (x, y) in enumerate([(-3.4, 34.0), (3.2, 34.4)]):
        P.centro(f"tiara_estrella_{i}", x, y, -3.5, 1.2, 1.2, 0.6, ORO, G, rot=(0, 0, 45))


def _v_plumas(P, c):
    G, cols = G_CAB, ["#C2402E", "#3FA7A6", ORO, "#F1E2C6"]
    alt = [4, 5.5, 7, 8, 9, 8, 7, 5.5, 4]
    for i, hh in enumerate(alt):
        x = (i - 4) * 1.0
        ang = -(i - 4) * 9 * ROT_Z_SIGNO
        piv = (x, 32.2, 0)
        P.caja(f"pluma_{i}_tallo", x - 0.6, 32.2, -0.7, x + 0.6, 32.2 + hh * 0.55, 0.7, cols[(i + 1) % 4], G, piv=piv,
               rot=(0, 0, ang), jit=0.05)
        P.caja(f"pluma_{i}_punta", x - 0.6, 32.2 + hh * 0.55, -0.7, x + 0.6, 32.2 + hh, 0.7, cols[i % 4], G, piv=piv,
               rot=(0, 0, ang), jit=0.05)
    for lado in (-1, 1):
        piv = (lado * 4.6, 31.2, 0)
        for j, (y1, y2, col) in enumerate([(31.2, 33.4, "#3FA7A6"), (33.4, 35.6, ORO)]):
            xa, xb = sorted((lado * 4.2, lado * 5.6))
            P.caja(f"pluma_lado_{lado}_{j}", xa, y1, -0.8, xb, y2, 0.8, col, G, piv=piv,
                   rot=(0, 0, -lado * 40 * ROT_Z_SIGNO))
    P.caja("diadema_pibble", -4.7, 31.0, -4.9, 4.7, 32.4, -4.5, ORO, G)


def _v_flor(P, c):
    G = G_CAB
    P.centro("flor_centro", -2.6, 33.4, -1.6, 1.4, 1.0, 1.4, ORO, G)
    for i, (dx, dz) in enumerate([(-1.6, 0), (1.6, 0), (0, -1.6), (0, 1.6)]):
        P.centro(f"flor_petalo_{i}", -2.6 + dx, 33.2, -1.6 + dz, 1.6, 0.9, 1.6, "#E8832A", G, jit=0.06)
    P.caja("flor_hoja", -5.6, 30.4, -1.0, -4.6, 31.8, 0.4, "#C96A1E", G)


def _v_gafas(P, c):
    G = G_CAB
    P.lr("gafa_arriba", 0.4, 29.0, -4.95, 3.9, 29.55, -4.4, ORO, G)
    P.lr("gafa_abajo", 0.4, 25.8, -4.95, 3.9, 26.35, -4.4, ORO, G)
    P.lr("gafa_int", 0.4, 25.8, -4.95, 0.95, 29.55, -4.4, ORO, G)
    P.lr("gafa_ext", 3.35, 25.8, -4.95, 3.9, 29.55, -4.4, ORO, G)
    P.caja("gafa_puente", -0.5, 27.9, -4.95, 0.5, 28.6, -4.4, ORO, G)
    P.lr("gafa_patilla", 3.9, 27.9, -4.95, 4.7, 28.5, 0.5, ORO, G)
    P.lr("gafa_brillo", 1.1, 28.0, -5.05, 1.9, 28.9, -4.95, "#9FD3EE", G)


def _v_etiquetas(P, c):
    G = G_CAB
    pos = [(-6.4, 30.5, -1.5), (-7.2, 27.5, 1.8), (-6.2, 33.0, 2.0), (6.6, 30.0, -0.8), (7.2, 27.2, 2.2)]
    for i, (x, y, z) in enumerate(pos):
        P.centro(f"etiqueta_{i}", x, y, z, 1.8, 2.4, 0.6, ORO, G, rot=(0, 20 * (-1) ** i, 8 * (-1) ** i), jit=0.05)
        P.centro(f"etiqueta_centro_{i}", x, y, z + (-0.35 if z > 0 else -0.35), 1.0, 1.4, 0.3, "#6FB2D8", G,
                 rot=(0, 20 * (-1) ** i, 8 * (-1) ** i))


# ---------------------------------------------------------------- ropa 3D
def _v_bufanda(P, c):
    b = c.get("bufanda")
    if not b:
        return
    col, tam, colas = b
    g = tam == "grande"
    t = 1.5 if g else 0.8
    y1, y2 = (21.8, 24.6) if g else (22.4, 24.4)
    P.caja("bufanda_f", -4.9, y1, -(2.4 + t), 4.9, y2, -2.0, col, G_TOR, jit=0.05)
    P.caja("bufanda_t", -4.9, y1, 2.0, 4.9, y2, 2.4 + t, col, G_TOR, jit=0.05)
    P.lr("bufanda_lado", 4.0, y1, -(2.4 + t), 4.9 + (0.4 if g else 0), y2, 2.4 + t, col, G_TOR, jit=0.05)
    if g:
        P.lr("bufanda_hombro", 3.6, 23.5, -3.3, 7.8, 25.0, 3.3, col, G_TOR, jit=0.05)
    if colas:
        zf = -(2.4 + t)
        P.caja("bufanda_cola_1", 0.8, 10.0, zf - 0.7, 3.6, y1 + 0.4, zf, col, G_TOR, jit=0.06)
        P.caja("bufanda_cola_2", -3.2, 14.0, zf - 0.7, -0.8, y1 + 0.4, zf, _tono(col, 0.9), G_TOR, jit=0.06)


def _v_bata(P, c):
    b = c.get("bata")
    if not b:
        return
    r, cols = P.rng, b["colores"]
    arr = b.get("arriba", cols)
    hem0 = {"corta": 8.0, "media": 4.5, "larga": 1.8}[b["largo"]]
    abierta, rib = b.get("abierta", False), b.get("ribete")
    ed = [-4.7 + i * (9.4 / 6) for i in range(7)]
    for cara, (za, zb, zla, zlb) in (("f", (-2.75, -2.0, -3.55, -2.9)), ("t", (2.0, 2.75, 2.9, 3.55))):
        for i in range(6):
            x1, x2 = ed[i], ed[i + 1]
            ym = r.uniform(16.5, 19.0)
            P.caja(f"bata_{cara}_alto_{i}", x1, ym, za, x2, 23.4, zb, arr[(i + (0 if cara == "f" else 2)) % len(arr)],
                   G_TOR, jit=0.06)
            P.caja(f"bata_{cara}_medio_{i}", x1, 12.0, za, x2, ym, zb, arr[r.randrange(len(arr))], G_TOR, jit=0.06)
            if abierta and cara == "f" and i in (2, 3):
                continue
            hem = hem0 + r.choice([0, 0, 0.9, 1.8, 2.7])
            ymid = (hem + 12.0) / 2 + r.uniform(-1, 1)
            xs1, xs2 = x1 * 1.06, x2 * 1.06
            P.caja(f"bata_{cara}_falda_a_{i}", xs1, ymid, min(za, zla + 0.35) if cara == "f" else za, xs2, 12.0,
                   zb if cara == "f" else max(zb, zlb - 0.35), cols[r.randrange(len(cols))], G_FAL, jit=0.06)
            P.caja(f"bata_{cara}_falda_b_{i}", xs1, hem, zla, xs2, ymid, zlb, cols[r.randrange(len(cols))], G_FAL,
                   jit=0.06)
            if rib:
                P.caja(f"bata_{cara}_ribete_{i}", xs1, hem, zla, xs2, hem + 0.7, zlb, rib, G_FAL)
    for j, (za, zb) in enumerate(((-2.9, 0.0), (0.0, 2.9))):
        hem = hem0 + r.choice([0, 0.9, 1.8])
        P.lr(f"bata_lado_{j}", 4.4, hem, za, 5.1, 12.0, zb, cols[r.randrange(len(cols))], G_FAL, jit=0.06)
        if rib:
            P.lr(f"bata_lado_ribete_{j}", 4.4, hem, za, 5.1, hem + 0.7, zb, rib, G_FAL)
    if abierta and rib:
        P.lr("bata_borde", 1.5, hem0, -3.6, 2.0, 12.0, -2.9, rib, G_FAL)


def _v_capa(P, c):
    k = c.get("capa")
    if not k:
        return
    r = P.rng
    piv, rot = (0, 23.5, 3.0), (ROT_X_SIGNO * 7, 0, 0)
    n = 6
    w = 12.6 / n
    for i in range(n):
        x1 = -6.3 + i * w
        hem = k["largo"] + r.choice([0, 1.2, 2.4, 0.6, 1.8])
        P.caja(f"capa_{i}", x1, hem, 2.9, x1 + w, 23.6, 3.7, k["color"] if i % 2 == 0 else k["color2"], G_CAPA,
               piv=piv, rot=rot, jit=0.05)
    P.lr("capa_manto", 4.0, 22.8, -2.9, 7.6, 24.2, 3.7, k["color"], G_TOR, jit=0.04)
    if k.get("estrellas"):
        for i in range(14):
            x, y = r.uniform(-5.6, 5.6), r.uniform(k["largo"] + 1.5, 22.5)
            P.caja(f"capa_estrella_{i}", x - 0.5, y - 0.5, 3.7, x + 0.5, y + 0.5, 3.95, ORO, G_CAPA, piv=piv, rot=rot)
    if k.get("capucha"):
        P.caja("capucha", -4.9, 21.0, 4.6, 4.9, 29.5, 5.5, k["color"], G_CAB, jit=0.05)
        P.caja("capucha_borde", -4.9, 29.5, 4.6, 4.9, 30.5, 5.2, k["color2"], G_CAB)


def _v_extras(P, c):
    r = P.rng
    m = c.get("mangas")
    if m:
        m2 = c.get("mangas2") or m
        P.lr("manga", 3.9, 17.0, -2.5, 8.5, 23.4, 2.5, m, G_BR, jit=0.04)
        P.lr("manga_vuelo_f", 4.0, 13.8, -3.0, 9.2, 17.2, 0.2, m2, G_BR, jit=0.06)
        P.lr("manga_vuelo_t", 4.0, 14.8, -0.2, 9.2, 17.2, 3.0, m, G_BR, jit=0.06)
    if c.get("guantes"):
        g1, g2 = c["guantes"]
        P.lr("guante", 3.8, 12.0, -2.4, 8.4, 16.2, 2.4, g1, G_BR, jit=0.04)
        P.lr("guante_borde", 3.7, 16.2, -2.6, 8.6, 17.4, 2.6, g2, G_BR)
    if c.get("brazaletes"):
        P.lr("brazalete", 3.9, 15.2, -2.3, 8.1, 16.6, 2.3, c["brazaletes"], G_BR)
    if c.get("hombreras"):
        col, emb = c["hombreras"]
        P.lr("hombrera", 3.6, 23.0, -2.9, 8.8, 24.8, 2.9, col, G_BR, jit=0.04)
        P.lr("hombrera_2", 4.2, 21.5, -3.3, 9.3, 23.0, 3.3, _tono(col, 0.85), G_BR, jit=0.04)
        if emb:
            P.lr("hombrera_emblema", 5.0, 24.8, -1.2, 7.4, 25.25, 1.2, emb, G_BR)
    if c.get("cinturon"):
        col, heb = c["cinturon"]
        P.caja("cinturon_f", -4.6, 11.6, -2.9, 4.6, 13.4, -2.1, col, G_TOR)
        P.caja("cinturon_t", -4.6, 11.6, 2.1, 4.6, 13.4, 2.9, col, G_TOR)
        P.lr("cinturon_lado", 4.1, 11.6, -2.1, 4.8, 13.4, 2.1, col, G_TOR)
        P.caja("hebilla", -1.3, 11.4, -3.5, 1.3, 13.6, -2.9, heb, G_TOR)
        P.caja("hebilla_centro", -0.5, 11.9, -3.7, 0.5, 13.1, -3.5, col, G_TOR)
    if c.get("cintas"):
        for i in range(5):
            x, ln = -4 + i * 2.0, r.uniform(6, 11)
            P.caja(f"cinta_{i}", x, 12 - ln, -3.5, x + 1.2, 12, -3.0, c["cintas"] if i % 2 == 0 else ORO, G_FAL,
                   piv=(x + 0.6, 12, -3.2), rot=(r.uniform(-8, 8), 0, r.uniform(-10, 10)), jit=0.08)
    if c.get("amuletos"):
        cs = ["#3FA7A6", ORO, "#C2402E", "#F1E2C6"]
        for i in range(10):
            x, y, s = r.uniform(-4.4, 4.4), r.uniform(5, 10.5), r.uniform(1.1, 2.1)
            P.caja(f"amuleto_hilo_{i}", x - 0.15, y + s, -3.3, x + 0.15, 12.2, -3.1, ORO_OSC, G_FAL)
            P.centro(f"amuleto_{i}", x, y + s / 2, -3.2, s, s, 0.9, cs[i % 4], G_FAL, rot=(0, 0, 45 if i % 3 == 0 else 0))
    if c.get("emblema"):
        e = c["emblema"]
        P.caja("emblema_centro", -1.0, 17.4, -3.4, 1.0, 19.4, -2.9, e, G_TOR)
        for nom, a, b_, c_, d in (("n", -0.4, 19.6, 0.4, 20.8), ("s", -0.4, 16.0, 0.4, 17.2),
                                  ("e", 1.2, 17.9, 2.4, 18.9), ("o", -2.4, 17.9, -1.2, 18.9)):
            P.caja(f"emblema_rayo_{nom}", a, b_, -3.3, c_, d, -2.9, e, G_TOR)
    if c.get("banda"):
        col, orn = c["banda"]
        hem = {"corta": 8.0, "media": 4.5, "larga": 1.8}[c["bata"]["largo"]] if c.get("bata") else 6.0
        P.caja("banda_alta", -1.2, 12.0, -3.25, 1.2, 21.0, -2.75, col, G_TOR)
        P.caja("banda_baja", -1.2, hem + 1.0, -3.95, 1.2, 12.0, -3.55, col, G_FAL)
        P.caja("banda_orn_1", -0.9, 15.0, -3.5, 0.9, 17.0, -3.25, orn, G_TOR)
        P.caja("banda_orn_2", -0.9, hem + 3.0, -4.2, 0.9, hem + 5.0, -3.95, orn, G_FAL)
    if c.get("estrellas"):
        hem = {"corta": 8.0, "media": 4.5, "larga": 1.8}[c["bata"]["largo"]] if c.get("bata") else 6.0
        for i in range(c["estrellas"]):
            x, y = r.uniform(-4.5, 4.5), r.uniform(hem + 1, 22)
            z = (-3.9, -3.5) if y < 12 else (-3.1, -2.7)
            if i % 3 == 0:
                z = (2.7, 3.1) if y >= 12 else (3.5, 3.9)
            P.caja(f"estrella_{i}", x - 0.5, y - 0.5, z[0], x + 0.5, y + 0.5, z[1], ORO, G_FAL)
    if c.get("libro"):
        P.caja("libro_cordon", -5.1, 10.4, -0.3, -4.7, 12.0, 0.3, ORO_OSC, G_TOR)
        P.caja("libro_1", -6.8, 7.0, -1.8, -4.8, 10.6, 1.8, "#1F2447", G_TOR)
        P.caja("libro_lomo", -6.8, 7.0, -1.8, -6.3, 10.6, 1.8, ORO, G_TOR)
        P.caja("libro_hojas", -5.6, 7.3, -1.5, -4.8, 10.3, 1.5, "#EDE3D0", G_TOR)


def gen_velkia(p):
    """Personaje de Velkia: player normal + pelo y ropa 3D. p['personaje'] = nombre (ver PERSONAJES)."""
    nombre = str(p.get("personaje") or "meron").lower().strip()
    if nombre not in PERSONAJES:
        print(f"Personaje '{nombre}' desconocido; uso 'meron'.")
        nombre = "meron"
    c = PERSONAJES[nombre]
    P = _Pieza(sum(map(ord, nombre)) * 7919)
    _v_base(P, c)
    _v_cara(P, c)
    _v_pelo(P, c)
    for h in c["cabeza"]:
        {"laurel": _v_laurel, "corona": _v_corona, "tiara": _v_tiara, "plumas": _v_plumas, "flor": _v_flor,
         "gafas": _v_gafas, "etiquetas": _v_etiquetas}.get(h, lambda *_: None)(P, c)
    _v_bata(P, c)
    _v_bufanda(P, c)
    _v_capa(P, c)
    _v_extras(P, c)
    return P.els


def detectar_personaje(texto: str):
    """Busca el nombre de un personaje en el texto (sin acentos). Devuelve la clave o None."""
    import unicodedata
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    alias = {"revoltir": "revoltir", "correcthar": "correcthar", "corecthar": "correcthar", "bashi": "bashi",
             "pibble": "pibble", "khaset": "khaset", "kaset": "khaset", "kemira": "kemira", "kimera": "kemira",
             "meron": "meron", "anteros": "anteros"}
    for a, k in alias.items():
        if a in t:
            return k
    return None


BASE = dict(ancho=1.0, alto=1.0, profundidad=1.0, ancho_inferior=0.0,
            curvatura=0.0, pliegue=0.0, detalle=2, pasos=4, angulo=180,
            fondo=0.0, abertura_trasera=0.0, abertura_frontal=0.0,
            ancho_muesca=0.35, recogido=0.12, inicio_campana=0.45,
            puntas=12, esclavina=0.12,
            cuello=0.45, caida_hombros=0.18, cierre_pecho=0.3,
            largo=0.0, ancho_brazo=0.0,
            vuelo=0.0, arco_ancho=0.0, arco_alto=0.0, v_prof=0.0, v_ancho=0.0,
            v_bajo=0.0, relieve=0.0, pelo=1,
            pos_x=0.0, pos_y=0.0, pos_z=0.0)

TIPOS = {
    # Personajes de Velkia: player normal + pelo y ropa 3D, con color y esqueleto. Parametro: personaje.
    "velkia":     (gen_velkia,     dict()),
    "cubo":       (gen_cubo,       dict(ancho=1, alto=1, profundidad=1)),
    "linea":      (gen_linea,      dict(ancho=8, alto=1, profundidad=1)),
    "pared":      (gen_pared,      dict(ancho=8, alto=4, profundidad=1)),
    "plataforma": (gen_plataforma, dict(ancho=6, alto=0.5, profundidad=6)),
    "escalera":   (gen_escalera,   dict(ancho=3, alto=4, profundidad=4, pasos=4)),
    "punta":      (gen_punta,      dict(ancho=3, alto=6, profundidad=3)),
    "espada":     (gen_espada,     dict(ancho=0.14, alto=1.5, profundidad=0.07)),
    # Herramientas de mano a escala Minecraft (personaje = 2 bloques = 32 px)
    "baston":     (gen_baston,     dict(ancho=0.125, alto=2.0, detalle=2)),
    "varita":     (gen_varita,     dict(ancho=1 / 16, alto=0.9, detalle=2)),
    "lanza":      (gen_lanza,      dict(ancho=1.5 / 16, alto=2.0, detalle=2)),
    "hacha":      (gen_hacha,      dict(ancho=1.5 / 16, alto=1.5, detalle=2)),
    "pico":       (gen_pico,       dict(ancho=1.5 / 16, alto=1.5, detalle=2)),
    "pala":       (gen_pala,       dict(ancho=1.5 / 16, alto=1.5, detalle=2)),
    "martillo":   (gen_martillo,   dict(ancho=1.5 / 16, alto=1.5, detalle=2)),
    "curva":      (gen_curva,      dict(ancho=8, alto=1, profundidad=2, angulo=180)),
    "abrigo":     (gen_abrigo,     dict(ancho=6, alto=8, profundidad=0.5, ancho_inferior=11,
                                        fondo=3, curvatura=0.15, abertura_trasera=3.5,
                                        abertura_frontal=90, ancho_muesca=0.4,
                                        recogido=0.1, inicio_campana=0.45)),
    "capa_malla": (gen_capa_malla, dict(ancho=6, alto=8, profundidad=0.3, ancho_inferior=8.5,
                                        fondo=3, curvatura=0.12, abertura_trasera=3,
                                        abertura_frontal=80, ancho_muesca=0.4,
                                        recogido=0.08, inicio_campana=0.55,
                                        puntas=12, esclavina=0.0, detalle=2,
                                        cuello=0.45, caida_hombros=0.18, cierre_pecho=0.3)),
    "capa":       (gen_capa,       dict(ancho=6, alto=8, profundidad=1.0,
                                        ancho_inferior=8, curvatura=1.5, pliegue=70)),
    # Defaults = torso del personaje actual (7 x 6 x 4 px, base en Y=5), todo en bloques (px/16)
    "faldon_cubos": (gen_faldon,    dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, profundidad=1 / 16,
                                        largo=3 / 16, ancho_brazo=2 / 16, pliegue=18, puntas=5,
                                        pos_y=5 / 16)),
    # Malla cerrada ajustada al torso: V, arcos delante/detras, picos. Medidas en px/16.
    "faldon_malla": (gen_faldon_malla, dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, profundidad=1 / 16,
                                        largo=2.5 / 16, vuelo=1.2 / 16, arco_ancho=2.6 / 16,
                                        arco_alto=2 / 16, v_prof=3 / 16, v_ancho=2 / 16,
                                        puntas=16, detalle=2, pos_y=5 / 16)),
    # Estilo Minecraft: celdas de 1 px fusionadas en cubos. Medidas en px/16.
    "faldon":     (gen_faldon_voxel, dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16,
                                        largo=3 / 16, vuelo=1 / 16, relieve=1 / 16,
                                        v_ancho=3 / 16, v_prof=4 / 16, v_bajo=5.6 / 16,
                                        arco_ancho=3 / 16, ancho_brazo=2 / 16, puntas=12,
                                        pos_y=5 / 16)),
    # Partes sueltas del personaje (mismas medidas del cuerpo) y el conjunto completo
    "cinturon":   (gen_cinturon,   dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, relieve=1 / 16,
                                        ancho_brazo=2 / 16, pos_y=5 / 16)),
    "guantes":    (gen_guantes,    dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, relieve=1 / 16,
                                        ancho_brazo=2 / 16, pos_y=5 / 16)),
    "cara":       (gen_cara,       dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, relieve=1 / 16,
                                        ancho_brazo=2 / 16, pos_y=5 / 16)),
    "corona":     (gen_corona,     dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, relieve=1 / 16,
                                        ancho_brazo=2 / 16, pos_y=5 / 16)),
    "plumas":     (gen_plumas,     dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, relieve=1 / 16,
                                        ancho_brazo=2 / 16, pos_y=5 / 16)),
    "pelo":       (gen_pelo,       dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16, relieve=1 / 16,
                                        ancho_brazo=2 / 16, pos_y=5 / 16)),
    "personaje":  (gen_personaje,  dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16,
                                        largo=3 / 16, vuelo=1 / 16, relieve=1 / 16,
                                        v_ancho=3 / 16, v_prof=4 / 16, v_bajo=5.6 / 16,
                                        arco_ancho=3 / 16, ancho_brazo=2 / 16, puntas=12,
                                        pos_y=5 / 16)),
    # Modelo entero con esqueleto (grupos). Sale como archivo .bbmodel.
    "personaje_completo": (gen_modelo_completo,
                           dict(ancho=7 / 16, alto=6 / 16, fondo=4 / 16,
                                largo=3 / 16, vuelo=1 / 16, relieve=1 / 16,
                                v_ancho=3 / 16, v_prof=4 / 16, v_bajo=5.6 / 16,
                                arco_ancho=3 / 16, ancho_brazo=2 / 16, puntas=12,
                                pos_y=5 / 16)),
}


def construir(plan: dict[str, Any]) -> list[dict[str, Any]]:
    tipo = str(plan.get("tipo", "pared")).lower().strip()
    if tipo not in TIPOS:
        print(f"Tipo '{tipo}' desconocido; uso 'pared'.")
        tipo = "pared"
    gen, defaults = TIPOS[tipo]

    p = dict(BASE)
    p.update(defaults)
    for k in BASE:
        if plan.get(k) is not None:
            try:
                p[k] = type(BASE[k])(plan[k]) if isinstance(BASE[k], int) else float(plan[k])
            except (TypeError, ValueError):
                pass
    p["personaje"] = str(plan.get("personaje") or "")
    if tipo == "velkia" and not p["personaje"]:
        p["personaje"] = detectar_personaje(str(plan.get("_prompt", ""))) or "meron"
    p["alto"] = min(64.0, max(0.05, p["alto"]))             # tope: medidas absurdas colgaban el programa
    p["ancho"] = min(64.0, max(0.02, p["ancho"]))
    p["profundidad"] = min(64.0, max(0.02, p["profundidad"]))

    elementos = gen(p)
    if len(elementos) > MAX_PIEZAS:
        print(f"Aviso: {len(elementos)} piezas, recorto a {MAX_PIEZAS}.")
        elementos = elementos[:MAX_PIEZAS]
    return a_pixeles(elementos)


# ======================================================================
# Groq (solo interpreta)
# ======================================================================

SYSTEM = """Eres el diseñador de alto nivel de un sistema que construye modelos estilo Minecraft en Blockbench.
NO creas cubos: eliges un TIPO y parámetros; otro programa genera la geometría.
Todas las medidas están en BLOQUES (1 bloque = 16 px). Si el usuario da medidas en px/píxeles, divídelas entre 16.

Tipos:
- cubo: un solo bloque.
- linea: una barra larga (ancho = largo, alto = grosor).
- pared: un cuboide grande (ancho, alto, profundidad = grosor).
- plataforma: losa plana (ancho, profundidad, alto = grosor pequeño).
- escalera: pasos (ancho, alto total, profundidad total, pasos).
- punta: pirámide escalonada que se afila (ancho/profundidad base, alto).
- espada: espada de mano (1.5 bloques por defecto); alto = largo total, ancho = ancho de la hoja.
REFERENCIA DE ESCALA: un personaje de Minecraft mide 32 px = 2 bloques. Las HERRAMIENTAS DE MANO ya salen con el tamaño correcto
  para ese personaje: NO envíes medidas salvo que el usuario las pida (si da px, divide entre 16). 'detalle' 3 = más adornos.
- baston: bastón / vara / palo tipo Jingu Bang (Wukong), remates dorados en ambos extremos, tachones y bandas (2 bloques).
- varita: varita mágica con pomo, mango anillado, engaste y cristal en la punta (0.9 bloques).
- lanza: lanza con contera, asta, collar y punta de hoja con nervio y borlas (2 bloques).
- hacha: hacha de mano con cabeza escalonada y contrapeso (1.5 bloques).
- pico: pico de minero con cabeza en arco (1.5 bloques).
- pala: pala con empuñadura en T y hoja ancha (1.5 bloques).
- martillo: martillo de guerra con cabeza de bloque y aros dorados (1.5 bloques).
- curva: arco (ancho = diámetro, alto = grosor, profundidad, angulo en grados).
- capa: prenda/capa. ancho = ancho arriba, ancho_inferior = ancho abajo (mayor),
  alto, profundidad (grosor, ~1), curvatura = cuánto se aleja hacia atrás la parte
  inferior (0.5 a 3), pliegue = grados TOTALES con que la capa envuelve el cuerpo en horizontal
  (por defecto 70; 0 = lámina plana; 100-140 = muy envolvente). Solo envíalo si el usuario pide más/menos volumen o plana.
- abrigo: saco / abrigo largo / gabardina / capa que RODEA el cuerpo (espalda + costados + frente con abertura).
  ancho = ancho del torso con holgura (arriba), fondo = grosor del torso (frente-atrás),
  ancho_inferior = ancho abajo, alto, profundidad = grosor de la tela (~0.5),
  curvatura = FRACCIÓN del alto que la ESPALDA se echa hacia atrás abajo, los costados caen rectos (0 a 0.25, normal 0.12), abertura_trasera = altura en bloques de la muesca
  trasera a la altura de las piernas (0 = sin muesca), abertura_frontal = grados de hueco al frente (80 por defecto = frente abierto como una capa; 0 = cerrado como saco),
  ancho_muesca = anchura de la muesca trasera (0.2 estrecha, 0.35 normal, 0.5 muy ancha),
  recogido = cuánto se curvan hacia adentro los bordes delanteros abajo (0 a 0.35, normal 0.1),
  inicio_campana = fracción del alto (0 a 0.8) donde termina el torso recto y empieza a abrirse la campana (normal 0.45).
  Usa 'abrigo' cuando el usuario hable de saco, abrigo, frente, costados o que cubra el cuerpo; 'capa' solo si es una lámina que cuelga de la espalda.
- faldon: casaca/faldón ESTILO MINECRAFT (cubos de 1 px con volúmenes) pegado al torso del personaje actual,
  con hombreras. Cerrado por los costados, pechera y espaldar con relieve, cuello en V (delante más ancha y
  profunda que detrás), delante abajo una UVE muy abierta, detrás abajo un ARCO que deja ver las piernas,
  y flecos en el borde. USA ESTE TIPO cuando pidan faldón, casaca, falda, capa, abrigo o ropa de ESTE personaje.
  Los valores por defecto YA encajan con su cuerpo: NO envíes medidas salvo que el usuario las pida.
  Opcionales (bloques = px/16): ancho/alto/fondo = medidas del torso, pos_y = altura de la base del torso,
  largo = cuánto baja la falda bajo la cintura (0.19), vuelo = cuánto se ensancha abajo (0.06),
  relieve = cuánto sobresale la pechera/espaldar (0.06), v_ancho = semiancho de la V del cuello delante (0.19),
  v_prof = profundidad de la V del cuello (0.25), v_bajo = semiancho de la uve abierta de abajo delante (0.35),
  arco_ancho = semiancho del arco trasero (0.19), ancho_brazo (0.125), puntas = 0 quita los flecos.
- velkia: personajes del lore de Velkia: player NORMAL de Minecraft (cabeza 8x8x8, cuerpo 8x12x4, brazos y piernas 4x12x4)
  con color, esqueleto, y SOLO el pelo y la ropa en 3D (cubos). Rellena 'personaje' con uno de estos 8 (no envíes medidas):
    revoltir  = semidiós de la risa · caos. Joven, inquieto, bromista. Pelo negro de puntas con detalles dorados, flor/lazo naranja,
                bufanda naranja grande con colas, ropa crema y naranja, hombreras marrones, cintas, botas con ribete dorado.
    correcthar = semidiós de la redención · orden. Sereno, preciso. Pelo azul oscuro de lado con mechas celestes, túnica azul marino
                con paneles celestes/crema, banda turquesa, ribetes turquesa.
    bashi     = semidiós del conocimiento · sabiduría. Gafas doradas, etiquetas/placas flotando alrededor de la cabeza, pelo negro revuelto,
                túnica larga azul oscuro y crema con detalles turquesa y dorados, libro colgando del cinturón.
    pibble    = semidiós errante · diversión. Rostro negro con ojos naranja brillantes, corona de plumas de colores (rojo, turquesa, dorado, crema),
                ropa roja con turquesa, hombreras, muchos amuletos y tótems colgando, botas doradas.
    khaset    = rey de Thza · protector. Corona dorada, pelo castaño corto, túnica larga crema, hombreras marrones con detalles dorados,
                emblema de sol dorado en el pecho, guantes y capa larga crema. Guerrero cercano a su gente.
    kemira    = reina de Thza · exploradora. Pelo negro largo, tiara dorada con gema azul, vestido azul marino con estrellas doradas,
                falda crema, capa azul estrellada.
    meron     = dios de Velkia (sol, desierto, risa). Pelo negro rizado con laurel dorado, bufanda crema enorme, túnica crema y dorada abierta,
                ropa interior oscura, botas oscuras con ribete crema.
    anteros   = dios de Aseris (bosque, orden, estrategia), hermano de Meron. Pelo negro rizado con laurel verde, capa verde con capucha,
                túnica oscura abierta con detalles crema, ropa verde del bosque.
  USA ESTE TIPO siempre que pidan a uno de estos personajes (o los describan: "el rey de Thza", "la reina exploradora", "el dios del sol"...).
  Se guarda como <personaje>.bbmodel (con pelo y ropa 3D ya coloreados).
- personaje_completo: el MODELO ENTERO sin color, estilo Minecraft, CON ESQUELETO (huesos/grupos para animar):
  cuerpo, brazos, piernas y botas, cabeza con ojos HUNDIDOS (huecos reales) y vigote que sobresale, faldón/casaca,
  hombreras, cinturón con hebilla, guantes, corona en anillo grueso, plumas y pelo. Se guarda como archivo .bbmodel.
  USA ESTE TIPO cuando pidan "el personaje completo", "todo", "con esqueleto" o "el modelo entero".
  Mismos parámetros que 'faldon' más pelo = 0 para quitar el pelo. No envíes medidas salvo que el usuario las pida.
- personaje: solo los ACCESORIOS para el cuerpo que el usuario ya tiene en Blockbench (faldón, hombreras, cinturón,
  guantes, cara con ojos hundidos con marco, corona, plumas, pelo). Sin cuerpo ni esqueleto.
- Partes sueltas del mismo personaje (usa solo la que pidan): cinturon, guantes, cara, corona, plumas, pelo.
- faldon_malla: versión suave (superficie lisa, sin estilo cubo); solo si piden malla lisa.
- faldon_cubos: versión antigua de paneles sueltos; solo si la piden expresamente.
- capa_malla: capa/abrigo/poncho/prenda con forma, hecha como UNA malla suave con borde en picos triangulares.
  USA ESTE TIPO solo si piden una capa/abrigo GRANDE y suelto que no sea para este personaje. Parámetros iguales a 'abrigo' más:
  profundidad = grosor de la tela (0.1 a 0.5), puntas = número de picos triangulares del borde inferior (0 = borde liso, 12 normal),
  Forma de abrigo cerrado sobre los hombros: ancho = ancho de HOMBROS, cuello = ancho del cuello respecto a los hombros (0.3 a 0.6, normal 0.45),
  caida_hombros = fracción del alto que ocupa la pendiente de los hombros (0.1 a 0.3, normal 0.18),
  cierre_pecho = fracción del alto hasta donde el frente va cerrado (0 = abierto desde arriba, normal 0.3),
  ancho_inferior = ancho abajo (entallado: 1.2 a 1.5 veces 'ancho'; campana amplia: 1.8+).
  Colocación en bloques (px/16) del modelo: pos_x, pos_y (altura del borde inferior), pos_z. Si el usuario da medidas del cuerpo, úsalas.
  'abrigo' (cubos) solo si piden expresamente bloques/voxel.
detalle: 1 = pocas piezas, 2 = normal, 3 = más suave/curvo.
Usa los valores que pida el usuario; si no dice nada, deja que decida el programa omitiendo el parámetro.
Responde SOLO llamando a la herramienta."""


def _herramienta_params() -> dict[str, Any]:
    props: dict[str, Any] = {"tipo": {"type": "string", "enum": list(TIPOS.keys())},
                             "personaje": {"type": "string", "enum": list(PERSONAJES.keys()),
                                           "description": "Solo con tipo=velkia."}}
    for k, v in BASE.items():
        if k in ("detalle",):
            props[k] = {"type": "integer", "enum": [1, 2, 3]}
        elif k == "pelo":
            props[k] = {"type": "integer", "enum": [0, 1]}
        elif k == "angulo":
            props[k] = {"type": "number"}
        elif isinstance(v, int):
            props[k] = {"type": "integer"}
        else:
            props[k] = {"type": "number"}
    return {"type": "object", "properties": props, "required": ["tipo"]}


def _extraer_json(texto: str):
    """Saca el primer objeto JSON de un texto (sirve para 'failed_generation' de Groq o respuestas con relleno)."""
    if not texto:
        return None
    for m in re.finditer(r"\{", texto):
        prof = 0
        for j in range(m.start(), len(texto)):
            prof += {"{": 1, "}": -1}.get(texto[j], 0)
            if prof == 0:
                try:
                    return json.loads(texto[m.start():j + 1])
                except ValueError:
                    break
    return None


def _plan_valido(plan) -> dict[str, Any] | None:
    if not isinstance(plan, dict):
        return None
    if "arguments" in plan and isinstance(plan["arguments"], dict):      # {"name":..., "arguments": {...}}
        plan = plan["arguments"]
    if "tipo" not in plan:
        return None
    plan = {k: v for k, v in plan.items() if v is not None}
    if str(plan["tipo"]).lower().strip() not in TIPOS:
        return None
    return plan


def obtener_plan_groq(prompt: str) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("Falta el paquete 'openai':  pip install openai")
    clave = os.environ.get("GROQ_API_KEY")
    if not clave:
        raise RuntimeError("Falta la variable de entorno GROQ_API_KEY.")
    client = OpenAI(api_key=clave, base_url="https://api.groq.com/openai/v1", timeout=20, max_retries=0)   # falla rápido: antes podía quedarse minutos colgado

    descripcion = "Elige el tipo de objeto y sus parámetros de alto nivel (en bloques)."
    params = _herramienta_params()
    mensajes = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    herramienta = {"type": "function", "function": {"name": "crear_modelo_voxel", "description": descripcion,
                                                    "parameters": params}}
    errores: list[str] = []

    def rescatar(e: Exception):
        """Groq devuelve 400 'tool_use_failed' con el JSON mal envuelto en failed_generation: lo rescatamos."""
        return _plan_valido(_extraer_json(str(getattr(e, "body", "") or "") + " " + str(e)))

    # 1) Chat Completions con la herramienta forzada, y luego 'required' (algunos modelos rechazan la forzada)
    for eleccion in ({"type": "function", "function": {"name": "crear_modelo_voxel"}}, "required"):
        print("  Groq: chat con herramienta...", flush=True)
        try:
            r = client.chat.completions.create(model=GROQ_MODEL, messages=mensajes, tools=[herramienta],
                                               tool_choice=eleccion, temperature=0)
            msg = r.choices[0].message
            for c in (msg.tool_calls or []):
                if c.function.name == "crear_modelo_voxel":
                    plan = _plan_valido(json.loads(c.function.arguments))
                    if plan:
                        return plan
            plan = _plan_valido(_extraer_json(msg.content or ""))
            if plan:
                return plan
        except Exception as e:
            errores.append(f"chat({'forzada' if isinstance(eleccion, dict) else eleccion}): "
                           f"{type(e).__name__}: {str(e)[:120]}")
            plan = rescatar(e)
            if plan:
                return plan

    # 2) Modo JSON (sin herramientas): le pedimos el JSON directamente
    print("  Groq: modo JSON...", flush=True)
    try:
        ayuda = (SYSTEM + "\n\nResponde SOLO con un objeto JSON con las claves: tipo (uno de "
                 + ", ".join(TIPOS) + "), personaje (solo si tipo=velkia) y los parámetros que apliquen.")
        r = client.chat.completions.create(
            model=GROQ_MODEL, temperature=0, response_format={"type": "json_object"},
            messages=[{"role": "system", "content": ayuda}, {"role": "user", "content": prompt}])
        plan = _plan_valido(_extraer_json(r.choices[0].message.content or ""))
        if plan:
            return plan
    except Exception as e:
        errores.append(f"json: {type(e).__name__}: {str(e)[:120]}")
        plan = rescatar(e)
        if plan:
            return plan

    # 3) Responses API (ultimo recurso) (formato plano de herramienta)
    print("  Groq: responses API...", flush=True)
    try:
        r = client.responses.create(
            model=GROQ_MODEL, input=mensajes,
            tools=[{"type": "function", "name": "crear_modelo_voxel",
                    "description": descripcion, "parameters": params}],
            tool_choice={"type": "function", "name": "crear_modelo_voxel"},
        )
        for item in r.output:
            if getattr(item, "type", None) == "function_call" and item.name == "crear_modelo_voxel":
                plan = _plan_valido(json.loads(item.arguments))
                if plan:
                    return plan
    except Exception as e:
        errores.append(f"responses: {type(e).__name__}: {str(e)[:120]}")
        plan = rescatar(e)
        if plan:
            return plan


    raise RuntimeError("Groq no devolvió un plan válido. Detalles:\n  " + "\n  ".join(errores))


# ======================================================================
# Blockbench MCP
# ======================================================================

async def diagnostico():
    """Lista las herramientas del MCP de Blockbench y el esquema de place_cube (para ver el formato real)."""
    from mcp import ClientSession
    try:
        from mcp.client.streamable_http import streamable_http_client
    except ImportError:
        from mcp.client.streamable_http import streamablehttp_client as streamable_http_client
    async with streamable_http_client(BLOCKBENCH_URL) as (r, w, *_):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            print(f"Conectado a {BLOCKBENCH_URL}. Herramientas ({len(tools)}):")
            for t in tools:
                print(" -", t.name)
            for t in tools:
                if "cube" in t.name.lower():
                    esquema = getattr(t, "inputSchema", None) or getattr(t, "input_schema", None)
                    print(f"\nEsquema de {t.name}:\n", json.dumps(esquema, indent=2, ensure_ascii=False)[:3000])
            res = await s.call_tool("place_cube", arguments={"elements": [
                {"name": "prueba", "from": [0, 0, 0], "to": [16, 16, 16]}], "faces": True})
            print("\nCubo de prueba:", str(res)[:400])


async def enviar_a_blockbench(elementos: list[dict[str, Any]]):
    from mcp import ClientSession
    try:
        from mcp.client.streamable_http import streamable_http_client
    except ImportError:                      # versiones antiguas del SDK
        from mcp.client.streamable_http import streamablehttp_client as streamable_http_client

    cubos = [e for e in elementos if "vertices" not in e]
    mallas = [e for e in elementos if "vertices" in e]
    ok = True

    async with streamable_http_client(BLOCKBENCH_URL) as (read_stream, write_stream, *_):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("MCP conectado.")
            if cubos:
                res = await session.call_tool("place_cube", arguments={"elements": cubos, "faces": True})
                print("place_cube:", str(res)[:300])
                if getattr(res, "isError", False) or getattr(res, "is_error", False):
                    print("AVISO: Blockbench respondió con error; revisa el mensaje de arriba.")
                    ok = False
            if mallas:
                res = await session.call_tool("place_mesh", arguments={"elements": mallas})
                print("place_mesh:", str(res)[:300])
    return ok


# ======================================================================
# Archivo .bbmodel (con esqueleto = grupos). No depende del MCP.
# ======================================================================

# Pivote (px) de cada hueso, para el cuerpo actual (torso base en Y=5)
ESQUELETO_ORIGEN = {
    "Cuerpo": (0, 5, 0),
    "Cuerpo/Parte Alta": (0, 5, 0),
    "Cuerpo/Parte Alta/Torso": (0, 8, 0),
    "Cuerpo/Parte Alta/Cabeza": (0, 11, 0),            # cuello
    "Cuerpo/Parte Alta/Brazo Izq.": (-4, 11, 0),       # hombro
    "Cuerpo/Parte Alta/Brazo Der.": (4, 11, 0),
    "Cuerpo/Parte Baja": (0, 5, 0),
    "Cuerpo/Parte Baja/Pierna Izq.": (-2, 5, 0),       # cadera
    "Cuerpo/Parte Baja/Pierna Der.": (2, 5, 0),
    "Cuerpo/Faldon": (0, 5, 0),
}

# Esqueleto del PLAYER NORMAL de Minecraft (32 px de alto, pies en y=0). Usado por los personajes de Velkia.
ESQUELETO_PLAYER = {
    "Cuerpo": (0, 12, 0),
    "Cuerpo/Torso": (0, 24, 0),
    "Cuerpo/Torso/Capa": (0, 23.5, 3),
    "Cuerpo/Cabeza": (0, 24, 0),                    # cuello
    "Cuerpo/Brazo Izq.": (-5, 22, 0),               # hombro
    "Cuerpo/Brazo Der.": (5, 22, 0),
    "Cuerpo/Pierna Izq.": (-2, 12, 0),              # cadera
    "Cuerpo/Pierna Der.": (2, 12, 0),
    "Cuerpo/Falda": (0, 12, 0),
}


def _png_paleta(colores):
    """PNG (RGBA) de lado x lado px con 1 pixel por color. Devuelve (bytes, lado, {color: (x, y)})."""
    import struct
    import zlib
    lado = 16
    while lado * lado < max(1, len(colores)):
        lado *= 2
    pos, filas = {}, [bytearray(lado * 4) for _ in range(lado)]
    for i, c in enumerate(colores):
        x, y = i % lado, i // lado
        pos[c] = (x, y)
        r, g, b = (int(c[k:k + 2], 16) for k in (1, 3, 5))
        filas[y][x * 4:x * 4 + 4] = bytes((r, g, b, 255))
    crudo = b"".join(b"\x00" + bytes(f) for f in filas)

    def trozo(tipo, datos):
        c = struct.pack(">I", len(datos)) + tipo + datos
        return c + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", lado, lado, 8, 6, 0, 0, 0))
           + trozo(b"IDAT", zlib.compress(crudo, 9)) + trozo(b"IEND", b""))
    return png, lado, pos


def _ruta_salida(ruta: str) -> str:
    """Devuelve una ruta donde SI se pueda escribir. Si la carpeta actual no deja (OneDrive, Escritorio protegido,
    archivo bloqueado o de solo lectura), usa ~/puente_salida y luego la carpeta temporal."""
    import tempfile
    nombre = os.path.basename(ruta)
    candidatos = [ruta,
                  os.path.join(os.path.expanduser("~"), "puente_salida", nombre),
                  os.path.join(tempfile.gettempdir(), "puente_salida", nombre)]
    for c in candidatos:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(c)), exist_ok=True)
            with open(c, "a", encoding="utf-8"):
                pass
            if c != ruta:
                print(f"(No pude escribir en '{ruta}'; uso '{c}')")
            return c
        except OSError:
            continue
    raise PermissionError(f"No pude escribir '{nombre}' en ninguna carpeta. Ejecuta el programa desde una "
                          f"carpeta fuera de OneDrive/Escritorio, por ejemplo C:\\Blockbench")


def escribir_bbmodel(elementos: list[dict[str, Any]], ruta: str, nombre: str = "personaje") -> dict[str, int]:
    """Guarda los cubos (en px) como modelo libre de Blockbench, con jerarquia de grupos segun 'grupo'."""
    import uuid

    import base64

    raiz: list[Any] = []
    nodos: dict[str, dict[str, Any]] = {}
    es_player = any(str(e.get("grupo", "")).startswith("Cuerpo/Cabeza") for e in elementos)
    origenes = ESQUELETO_PLAYER if es_player else ESQUELETO_ORIGEN

    colores = sorted({e["color"] for e in elementos if isinstance(e.get("color"), str) and e["color"].startswith("#")
                      and len(e["color"]) == 7})
    png, lado, pos_color = _png_paleta(colores) if colores else (b"", 16, {})

    def grupo(path: str) -> dict[str, Any]:
        if path in nodos:
            return nodos[path]
        partes = path.split("/")
        destino = raiz if len(partes) == 1 else grupo("/".join(partes[:-1]))["children"]
        g = {"name": partes[-1], "origin": list(origenes.get(path, (0, 0, 0))), "color": 0,
             "uuid": str(uuid.uuid4()), "export": True, "isOpen": True, "locked": False,
             "visibility": True, "autouv": 0, "children": []}
        destino.append(g)
        nodos[path] = g
        return g

    cubos = []
    for e in elementos:
        if "vertices" in e:
            continue                                        # las mallas no van en este archivo
        uid = str(uuid.uuid4())
        path = e.get("grupo") or ""
        cubo_bb = {
            "name": e["name"], "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
            "from": e["from"], "to": e["to"], "autouv": 0,
            "color": sum(map(ord, path or e["name"])) % 8,
            "origin": e.get("origin", [0, 0, 0]),
            "faces": {c: {"uv": [0, 0, 16, 16], "texture": None}
                      for c in ("north", "east", "south", "west", "up", "down")},
            "type": "cube", "uuid": uid,
        }
        if "rotation" in e:
            cubo_bb["rotation"] = e["rotation"]
        if e.get("color") in pos_color:                      # pinta la cara con su pixel de la paleta
            x, y = pos_color[e["color"]]
            for cara in cubo_bb["faces"].values():
                cara["uv"] = [x + 0.25, y + 0.25, x + 0.75, y + 0.75]
                cara["texture"] = 0
        cubos.append(cubo_bb)
        (grupo(path)["children"] if path else raiz).append(uid)

    modelo = {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
        "name": nombre, "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [], "unhandled_root_fields": {},
        "resolution": {"width": lado if png else 128, "height": lado if png else 128},
        "elements": cubos, "outliner": raiz,
        "textures": [{"path": "", "name": "paleta.png", "folder": "", "namespace": "", "id": "0",
                      "particle": False, "render_mode": "default", "render_sides": "auto", "frame_time": 1,
                      "frame_order_type": "loop", "frame_order": "", "frame_interpolation": False,
                      "visible": True, "internal": True, "saved": False, "uuid": str(uuid.uuid4()),
                      "source": "data:image/png;base64," + base64.b64encode(png).decode()}] if png else [],
    }
    ruta = _ruta_salida(ruta)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(modelo, f, indent=2, ensure_ascii=False)
    return {"cubos": len(cubos), "grupos": len(nodos), "ruta": ruta}


# ======================================================================
# main
# ======================================================================

def _norm(t: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(ch for ch in t if not unicodedata.combining(ch))


def _es_generico(prompt: str) -> bool:
    """'crea', 'hazme uno', 'crea un personaje'... sin decir cual: Groq solo devolveria un cubo."""
    t = _norm(prompt)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    palabras = [w for w in t.split() if w not in ("un", "una", "el", "la", "los", "las", "a", "de", "del", "uno",
                                                    "personaje", "modelo", "por", "favor", "me", "mi")]
    return all(w in ("crea", "crear", "creame", "haz", "hazme", "hacer", "genera", "generar", "genera", "dame",
                     "quiero", "construye", "modelo", "nuevo") for w in palabras)


def elegir_personaje() -> str | None:
    print("\n¿Qué personaje de Velkia quieres crear?")
    claves = list(PERSONAJES)
    for i, k in enumerate(claves, 1):
        print(f"  {i}. {k.capitalize():<11} {PERSONAJES[k]['desc'].split('.')[0]}")
    print("  9. Todos (en fila)")
    r = _norm(input("> ")).strip()
    if r in ("9", "todos", "todo"):
        return "todos"
    if r.isdigit() and 1 <= int(r) <= len(claves):
        return claves[int(r) - 1]
    return detectar_personaje(r)


def _desplazar_x(elementos, dx_px):
    """Copia los elementos movidos dx_px en X (para poner varios personajes en fila)."""
    salida = []
    for e in elementos:
        n = dict(e)
        for k in ("from", "to", "origin"):
            if k in n:
                n[k] = [n[k][0] + dx_px] + list(n[k][1:])
        salida.append(n)
    return salida


def _guardar_personaje(clave: str, carpeta: str = ".") -> str:
    els = construir({"tipo": "velkia", "personaje": clave})
    info = escribir_bbmodel(els, os.path.join(carpeta, f"{clave}.bbmodel"), clave)
    print(f"  {clave:<11} {info['cubos']:>3} cubos, {info['grupos']} grupos -> {info['ruta']}")
    return info["ruta"]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", help="petición en lenguaje natural")
    ap.add_argument("--seco", action="store_true", help="no enviar a Blockbench")
    ap.add_argument("--mcp", action="store_true",
                    help="con modelos que traen esqueleto (.bbmodel), enviar ademas los cubos por MCP (sin grupos)")
    ap.add_argument("--diagnostico", action="store_true", help="prueba la conexión con Blockbench y muestra su formato")
    ap.add_argument("--sin-pausa", action="store_true", help="no esperar Enter al terminar")
    ap.add_argument("--sin-mcp", action="store_true", help="solo guardar el .bbmodel, sin enviar a Blockbench")
    ap.add_argument("--todos", action="store_true",
                    help="genera los 8 personajes de Velkia (.bbmodel) sin usar Groq")
    ap.add_argument("--groq", action="store_true",
                    help="usa Groq aunque el nombre del personaje ya se reconozca en la petición")
    ap.add_argument("--carpeta", default="personajes_velkia", help="carpeta de salida para --todos")
    args = ap.parse_args()

    print("=" * 60)
    print(" BLOCKBENCH + GROQ")
    print("=" * 60)

    if args.diagnostico:
        try:
            await diagnostico()
        except Exception as e:
            while getattr(e, "exceptions", None):
                e = e.exceptions[0]
            print(f"No conectó con Blockbench ({BLOCKBENCH_URL}): {type(e).__name__}: {e}")
        return

    if args.todos:
        os.makedirs(args.carpeta, exist_ok=True)
        print(f"\nGenerando personajes en '{args.carpeta}/':")
        for clave in PERSONAJES:
            _guardar_personaje(clave, args.carpeta)
        print("En Blockbench: File > Open Model y elige el .bbmodel.")
        return

    prompt = (args.prompt or input("\n¿Qué quieres crear?\n> ")).strip()
    if not prompt:
        print("No escribiste ninguna petición.")
        return

    clave = detectar_personaje(prompt)
    if not clave and ("todos" in _norm(prompt) or "los 8" in _norm(prompt)):
        clave = "todos"
    if not clave and _es_generico(prompt):
        clave = elegir_personaje()
        if not clave:
            print("No reconocí esa opción.")
            return

    if clave == "todos":
        os.makedirs(args.carpeta, exist_ok=True)
        print(f"\nGenerando los 8 personajes (archivos en '{args.carpeta}/'):")
        lotes = []
        for i, k in enumerate(PERSONAJES):
            _guardar_personaje(k, args.carpeta)
            lotes.append(_desplazar_x(construir({"tipo": "velkia", "personaje": k}), (i - 3.5) * 26))
        if args.sin_mcp or args.seco:
            return
        print("\nEnviando a Blockbench (en fila)...")
        try:
            for k, lote in zip(PERSONAJES, lotes):
                limpio = [{a: b for a, b in e.items() if a not in ("grupo", "color")} for e in lote]
                await enviar_a_blockbench(limpio)
        except Exception as e:
            while getattr(e, "exceptions", None):
                e = e.exceptions[0]
            print(f"No pude hablar con Blockbench: {type(e).__name__}: {e}")
            print(f"Abre los .bbmodel de '{args.carpeta}/' con File > Open Model.")
        return

    plan = None
    if clave and not args.groq:
        plan = {"tipo": "velkia", "personaje": clave}
        print(f"\nPersonaje reconocido: {clave} (no hace falta Groq; usa --groq para forzarlo).")
    else:
        print("\nConsultando Groq...")
        try:
            plan = obtener_plan_groq(prompt)
        except Exception as e:
            print(f"\nGroq falló: {e}")
            if clave:
                print(f"Uso el personaje reconocido en tu texto: {clave}.")
                plan = {"tipo": "velkia", "personaje": clave}
            else:
                print("No pude interpretar la petición. Revisa la clave/red o escribe el nombre de un personaje.")
                return
    if str(plan.get("tipo")).lower() == "cubo" and len(prompt.split()) <= 3 and "cubo" not in _norm(prompt) \
            and "bloque" not in _norm(prompt):
        print("\nGroq solo propuso un cubo para una petición muy corta.")
        k = elegir_personaje()
        if not k or k == "todos":
            print("Usa: python puente.py --todos   (o escribe el nombre de un personaje).")
            return
        plan = {"tipo": "velkia", "personaje": k}
    plan["_prompt"] = prompt
    print("\nPlan recibido:")
    print(json.dumps({k: v for k, v in plan.items() if k != "_prompt"}, indent=2, ensure_ascii=False))

    elementos = construir(plan)
    print(f"\nPython generó {len(elementos)} piezas.")
    for e in elementos:
        if "vertices" in e:
            print(f"  malla '{e['name']}': {len(e['vertices'])} vértices, {len(e['faces'])} caras")

    try:
        ruta_json = _ruta_salida("ultimo_modelo.json")
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(elementos, f, indent=2, ensure_ascii=False)
        print(f"Guardado en {ruta_json}")
    except OSError as e:                                    # no es crítico: es solo una copia de respaldo
        print(f"(No pude guardar ultimo_modelo.json: {e}; sigo igual)")

    if any("grupo" in e for e in elementos):
        nombre = plan.get("personaje") or "personaje"
        if str(plan.get("tipo")).lower() != "velkia":
            nombre = "personaje"
        elif nombre not in PERSONAJES:
            nombre = detectar_personaje(prompt) or "meron"
        info = escribir_bbmodel(elementos, f"{nombre}.bbmodel", nombre)
        ruta = info["ruta"]
        print(f"Modelo con esqueleto: {info['cubos']} cubos en {info['grupos']} grupos -> {ruta}")
        print(f"En Blockbench: File > Open Model y elige {ruta}.")
        if args.sin_mcp or args.seco:
            return
        print("\nEnviando también a Blockbench por MCP...")
        completo = elementos
        simple = [{k: v for k, v in e.items() if k not in ("grupo", "color")} for e in elementos]
        for etiqueta, lote in (("con color y grupos", completo), ("sin color ni grupos", simple)):
            try:
                if await enviar_a_blockbench(lote):
                    print(f"Listo ({etiqueta}).")
                    return
                print(f"Blockbench rechazó el envío {etiqueta}; pruebo otra forma...")
            except Exception as e:
                while getattr(e, "exceptions", None):
                    e = e.exceptions[0]
                print(f"No pude hablar con Blockbench ({etiqueta}): {type(e).__name__}: {e}")
                break
        print(f"Plan B: abre {ruta} con File > Open Model (tiene color y esqueleto).")
        return
    else:
        elementos = [{k: v for k, v in e.items() if k != "color"} for e in elementos]

    if args.seco:
        print(json.dumps(elementos, indent=2, ensure_ascii=False))
        return

    print("\nConectando con Blockbench...")
    try:
        await enviar_a_blockbench(elementos)
    except Exception as e:
        while getattr(e, "exceptions", None):                # ExceptionGroup de anyio -> causa real
            e = e.exceptions[0]
        print(f"\nNo pude hablar con Blockbench en {BLOCKBENCH_URL}: {type(e).__name__}: {e}")
        print("¿Está abierto Blockbench con el plugin MCP activo? El modelo quedó guardado en ultimo_modelo.json.")
        return
    print("\nListo.")


if __name__ == "__main__":
    print(f"[puente.py] archivo en uso: {os.path.abspath(__file__)}")
    try:
        asyncio.run(main())
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print("\nCancelado.")
    except Exception:
        import traceback
        print("\n*** ERROR ***")
        traceback.print_exc()
    # Evita que la ventana se cierre sola antes de poder leer el resultado
    if "--sin-pausa" not in sys.argv:
        try:
            input("\nPresiona Enter para cerrar...")
        except EOFError:
            pass
