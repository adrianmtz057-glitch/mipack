"""
Vista previa: rasterizador por software del modelo texturizado -> PNG con varias vistas.
Necesita numpy y Pillow (pip install numpy pillow). Es opcional: sin ellos no se genera la vista.
"""

import math

from .modelo import esquinas

VISTAS = (("frente", 0, 8), ("3/4", 35, 12), ("lado", 90, 8), ("espalda", 180, 8))


def _rot_matriz(rx, ry, rz):
    import numpy as np
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx                      # orden ZYX de Blockbench


def _caras_mundo(modelo, uvs):
    import numpy as np
    out = []
    for c in modelo.cubos:
        R = _rot_matriz(*c.rot) if c.rot else None
        o = np.array(c.origen, dtype=float)
        for cara in c.caras:
            tl, tr, bl = (np.array(p, dtype=float) for p in esquinas(c.desde, c.hasta, cara))
            br = tr + bl - tl
            P = np.stack([tl, tr, br, bl])
            if R is not None:
                P = (P - o) @ R.T + o
            u1, v1, u2, v2 = uvs[id(c)][cara]
            UV = np.array([[u1, v1], [u2, v1], [u2, v2], [u1, v2]], dtype=float)
            out.append((P, UV))
    for m in getattr(modelo, "mallas", []):
        for k, cara in enumerate(m.caras):
            orden = (0, 2, 1, 1) if len(cara) == 3 else (0, 3, 2, 1)     # el render quiere horario desde afuera
            P = np.array([m.vertices[cara[o]] for o in orden], dtype=float)
            UV = np.array([uvs[id(m)][k][o] for o in orden], dtype=float)
            out.append((P, UV))
    return out


def _render(caras, tex, yaw, pitch, escala, ancho, alto, centro):
    import numpy as np
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    # camara: yaw 0 mira el frente (desde -Z hacia +Z)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rp = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]])      # camara un poco por encima
    V = Rp @ Ry
    img = np.zeros((alto, ancho, 3), dtype=float)
    img[:] = (0.13, 0.13, 0.15)
    zbuf = np.full((alto, ancho), np.inf)
    th, tw = tex.shape[:2]
    for P, UV in caras:
        Q = (P - centro) @ V.T
        n = np.cross(P[3] - P[0], P[1] - P[0])          # normal hacia afuera
        nl = np.linalg.norm(n)
        if nl < 1e-9:
            continue
        n /= nl
        nv = V @ n
        if nv[2] >= 0:                       # mira hacia atras: la camara mira +Z
            continue
        luz = 0.6 * n[0] ** 2 + (1.0 if n[1] > 0 else 0.5) * n[1] ** 2 + 0.8 * n[2] ** 2
        sx = ancho / 2 - Q[:, 0] * escala     # la derecha del modelo (+X) sale a la izquierda en el frente
        sy_ = alto / 2 - Q[:, 1] * escala
        sz = Q[:, 2]
        for tri in ((0, 1, 2), (0, 2, 3)):
            x0, x1, x2 = sx[list(tri)]
            y0, y1, y2 = sy_[list(tri)]
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9:
                continue
            xa, xb = max(0, int(math.floor(min(x0, x1, x2)))), min(ancho - 1, int(math.ceil(max(x0, x1, x2))))
            ya, yb = max(0, int(math.floor(min(y0, y1, y2)))), min(alto - 1, int(math.ceil(max(y0, y1, y2))))
            if xa > xb or ya > yb:
                continue
            gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
            w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
            w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not m.any():
                continue
            z = w0 * sz[tri[0]] + w1 * sz[tri[1]] + w2 * sz[tri[2]]
            u = w0 * UV[tri[0], 0] + w1 * UV[tri[1], 0] + w2 * UV[tri[2], 0]
            v = w0 * UV[tri[0], 1] + w1 * UV[tri[1], 1] + w2 * UV[tri[2], 1]
            ui = np.clip(np.floor(u).astype(int), 0, tw - 1)
            vi = np.clip(np.floor(v).astype(int), 0, th - 1)
            col = tex[vi, ui]
            sub = zbuf[ya:yb + 1, xa:xb + 1]
            m &= (col[..., 3] > 0.5) & (z < sub - 1e-4)
            if not m.any():
                continue
            sub[m] = z[m]
            img[ya:yb + 1, xa:xb + 1][m] = col[..., :3][m] * luz
    return img


def guardar_vista(modelo, lienzo, uvs, ruta_png, alto_px=520, centro=None, radio=None, vistas=VISTAS):
    """Vistas del modelo en un PNG. Con centro/radio (en px del modelo) hace zoom a esa zona (ej. la cara)."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    tex = np.frombuffer(bytes(lienzo.px), dtype=np.uint8).reshape(lienzo.alto, lienzo.ancho, 4) / 255.0
    caras = _caras_mundo(modelo, uvs)
    todos = np.concatenate([P for P, _ in caras])
    lo, hi = todos.min(axis=0), todos.max(axis=0)
    zoom = centro is not None
    centro = (lo + hi) / 2 if centro is None else np.array(centro, dtype=float)
    radio = float(np.linalg.norm(hi - lo)) / 2 if radio is None else float(radio)
    escala = (alto_px * 0.9) / (2 * radio)
    ancho = alto_px if zoom else int(alto_px * 0.62)
    paneles = [_render(caras, tex, yaw, pitch, escala, ancho, alto_px, centro) for _, yaw, pitch in vistas]
    img = np.concatenate(paneles, axis=1)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(ruta_png)
    return ruta_png
