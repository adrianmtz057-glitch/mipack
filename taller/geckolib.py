"""
Exportacion a GeckoLib (geometria Bedrock .geo.json y animaciones .animation.json) y su reconstruccion: arma el
modelo como lo arma GeckoLib 4.8 al cargarlo (leido de su codigo: BakedModelFactory, GeoQuad, RenderUtils y
BakedAnimationsAdapter) para comprobar que lo exportado se ve igual que el modelo del kit, y para posarlo (cinematica
directa) y renderizar las animaciones antes de meterlas al juego.

Convenciones de GeckoLib (todas en px; 16 por bloque):
  - geometria: origin.x = -(lo maximo en x), pivot.x = -x, rotation = (-rx, -ry, rz). Al cargar lo invierte de
    vuelta, asi que el modelo queda en las mismas coordenadas que en Blockbench (y que en el kit).
  - cada cara: uv (esquina) y uv_size; la esquina 0 del quad recibe (u + ancho, v), la 1 (u, v), la 2 (u, v + alto)
    y la 3 (u + ancho, v + alto), con los vertices de cada direccion en el orden de VertexSet.
  - giros: Z, luego Y, luego X (igual que Blockbench); de un cubo alrededor de su pivote, de un hueso alrededor del
    suyo, los hijos heredan los giros del padre.
  - animacion: rotacion en grados (-rx, -ry, rz) que se SUMA al giro del hueso; posicion (-px, py, pz).
"""

import json
import math

from .modelo import NORMAL, esquinas

DIRECCIONES = ("west", "east", "north", "south", "up", "down")     # el orden de buildQuads


def _r(v, n=4):
    return round(v + 0.0, n)


def _vertices_gecko(desde, hasta):
    """VertexSet de GeckoLib (ya en coordenadas del kit): nombres como en su codigo (Back/Front = x min/max,
    Left/Right = z min/max)."""
    (x1, y1, z1), (x2, y2, z2) = desde, hasta
    return {"bottomLeftBack": (x1, y1, z1), "bottomRightBack": (x1, y1, z2), "topLeftBack": (x1, y2, z1),
            "topRightBack": (x1, y2, z2), "topLeftFront": (x2, y2, z1), "topRightFront": (x2, y2, z2),
            "bottomLeftFront": (x2, y1, z1), "bottomRightFront": (x2, y1, z2)}


QUADS = {"west": ("topRightBack", "topLeftBack", "bottomLeftBack", "bottomRightBack"),
         "east": ("topLeftFront", "topRightFront", "bottomRightFront", "bottomLeftFront"),
         "north": ("topLeftBack", "topLeftFront", "bottomLeftFront", "bottomLeftBack"),
         "south": ("topRightFront", "topRightBack", "bottomRightBack", "bottomRightFront"),
         "up": ("topRightBack", "topRightFront", "topLeftFront", "topLeftBack"),
         "down": ("bottomLeftBack", "bottomLeftFront", "bottomRightFront", "bottomRightBack")}


def _uv_del_kit(desde, hasta, cara, uv):
    """La UV que el kit le da a cada esquina de la cara: {posicion: (u, v)}."""
    tl, tr, bl = esquinas(desde, hasta, cara)
    u1, v1, u2, v2 = uv
    br = tuple(tr[i] + bl[i] - tl[i] for i in range(3))
    return {tuple(_r(c) for c in tl): (u1, v1), tuple(_r(c) for c in tr): (u2, v1),
            tuple(_r(c) for c in bl): (u1, v2), tuple(_r(c) for c in br): (u2, v2)}


def uv_cara(desde, hasta, cara, uv):
    """(uv, uv_size) de Bedrock para que GeckoLib ponga en cada esquina la misma UV que el kit."""
    kit = _uv_del_kit(desde, hasta, cara, uv)
    vs = _vertices_gecko(desde, hasta)
    q = [kit[tuple(_r(c) for c in vs[nombre])] for nombre in QUADS[cara]]
    u, v = q[1]
    su, sv = q[0][0] - u, q[2][1] - v
    if abs(q[3][0] - (u + su)) > 1e-6 or abs(q[3][1] - (v + sv)) > 1e-6:
        raise ValueError(f"la cara {cara} no cuadra con GeckoLib")
    return [_r(u), _r(v)], [_r(su), _r(sv)]


def exportar_geo(modelo, uvs, lienzo, identificador):
    """El dict del .geo.json (geometria Bedrock 1.12.0) de un modelo hecho solo de cubos."""
    if modelo.mallas:
        raise ValueError("GeckoLib no lee mallas: el modelo tiene que ser solo de cubos")
    rutas = set(modelo.pivotes)
    for c in modelo.cubos:
        partes = c.hueso.split("/")
        rutas.update("/".join(partes[:i + 1]) for i in range(len(partes)))
    for r in list(rutas):
        partes = r.split("/")
        rutas.update("/".join(partes[:i + 1]) for i in range(len(partes)))
    nombres = [r.split("/")[-1] for r in rutas]
    if len(set(nombres)) != len(nombres):
        raise ValueError("dos huesos con el mismo nombre (GeckoLib los identifica por nombre)")
    huesos = {}
    for ruta in sorted(rutas, key=lambda r: (r.count("/"), r)):
        piv = modelo.pivotes.get(ruta, (0.0, 0.0, 0.0))
        b = {"name": ruta.split("/")[-1], "pivot": [_r(-piv[0]), _r(piv[1]), _r(piv[2])], "cubes": []}
        if "/" in ruta:
            b["parent"] = ruta.rsplit("/", 1)[0].split("/")[-1]
        huesos[ruta] = b
    for c in modelo.cubos:
        (x1, y1, z1), (x2, y2, z2) = c.desde, c.hasta
        cubo = {"origin": [_r(-x2), _r(y1), _r(z1)], "size": [_r(x2 - x1), _r(y2 - y1), _r(z2 - z1)], "uv": {}}
        if c.rot:
            o = c.origen
            cubo["pivot"] = [_r(-o[0]), _r(o[1]), _r(o[2])]
            cubo["rotation"] = [_r(-c.rot[0], 3), _r(-c.rot[1], 3), _r(c.rot[2], 3)]
        for cara in c.caras:
            uv, tam = uv_cara(c.desde, c.hasta, cara, uvs[id(c)][cara])
            cubo["uv"][cara] = {"uv": uv, "uv_size": tam}
        huesos[c.hueso]["cubes"].append(cubo)
    for b in huesos.values():
        if not b["cubes"]:
            del b["cubes"]
    xs = [v for c in modelo.cubos for v in (c.desde[0], c.hasta[0])]
    ys = [v for c in modelo.cubos for v in (c.desde[1], c.hasta[1])]
    zs = [v for c in modelo.cubos for v in (c.desde[2], c.hasta[2])]
    ancho = max(max(map(abs, xs)), max(map(abs, zs))) * 2 / 16 + 2
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.{identificador}", "texture_width": lienzo.ancho,
                        "texture_height": lienzo.alto, "visible_bounds_width": _r(ancho, 1),
                        "visible_bounds_height": _r((max(ys) - min(ys)) / 16 + 2, 1),
                        "visible_bounds_offset": [0, _r((max(ys) + min(ys)) / 32, 2), 0]},
        "bones": list(huesos.values())}]}


# ---------------------------------------------------------------- reconstruccion como GeckoLib

def _matriz(rx, ry, rz):
    """Giro Z * Y * X (radianes) como en RenderUtils.rotateMatrixAroundBone/Cube."""
    ca, sa, cb, sb, cc, sc = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = ((1, 0, 0), (0, ca, -sa), (0, sa, ca))
    Y = ((cb, 0, sb), (0, 1, 0), (-sb, 0, cb))
    Z = ((cc, -sc, 0), (sc, cc, 0), (0, 0, 1))

    def mul(P, Q):
        return tuple(tuple(sum(P[i][k] * Q[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mul(mul(Z, Y), X)


def _aplicar(M, p):
    return tuple(sum(M[i][k] * p[k] for k in range(3)) for i in range(3))


class Transformacion:
    """Transformacion rigida p -> R p + t (para encadenar los huesos)."""

    def __init__(self, R=((1, 0, 0), (0, 1, 0), (0, 0, 1)), t=(0.0, 0.0, 0.0)):
        self.R, self.t = R, t

    def despues(self, otra):
        """self aplicada despues de 'otra' (self * otra)."""
        R = tuple(tuple(sum(self.R[i][k] * otra.R[k][j] for k in range(3)) for j in range(3)) for i in range(3))
        t = tuple(_aplicar(self.R, otra.t)[i] + self.t[i] for i in range(3))
        return Transformacion(R, t)

    def __call__(self, p):
        q = _aplicar(self.R, p)
        return tuple(q[i] + self.t[i] for i in range(3))


def _giro_en(pivote, rot_rad, traslado=(0.0, 0.0, 0.0)):
    """translateMatrixToBone + translateToPivot + rotate + translateAwayFromPivot (en px)."""
    R = _matriz(*rot_rad)
    rp = _aplicar(R, pivote)
    return Transformacion(R, tuple(pivote[i] - rp[i] + traslado[i] for i in range(3)))


def reconstruir(geo, pose=None):
    """Los quads del modelo como los arma y dibuja GeckoLib: [(4 posiciones en px del kit, 4 UV en px, cara,
    normal hacia afuera, hueso)].
    pose: {nombre de hueso: ((rx, ry, rz) grados como en el ARCHIVO de animacion, (px, py, pz) como en el archivo)}."""
    g = geo["minecraft:geometry"][0]
    huesos = {b["name"]: b for b in g["bones"]}
    pose = pose or {}
    cache = {}

    def de_hueso(nombre):
        if nombre in cache:
            return cache[nombre]
        b = huesos[nombre]
        px, py, pz = b["pivot"]
        piv = (-px, py, pz)                                   # updatePivot(-x, y, z)
        rb = b.get("rotation", [0, 0, 0])
        rot = [math.radians(-rb[0]), math.radians(-rb[1]), math.radians(rb[2])]
        tras = (0.0, 0.0, 0.0)
        if nombre in pose:
            (ax, ay, az), (tx, ty, tz) = pose[nombre]
            rot = [rot[0] + math.radians(-ax), rot[1] + math.radians(-ay), rot[2] + math.radians(az)]
            tras = (-tx, ty, tz)                              # translateMatrixToBone(-posX, posY, posZ)
        T = _giro_en(piv, rot, tras)
        if "parent" in b:
            T = de_hueso(b["parent"]).despues(T)
        cache[nombre] = T
        return T

    out = []
    for b in g["bones"]:
        T = de_hueso(b["name"])
        for cubo in b.get("cubes", []):
            ox, oy, oz = cubo["origin"]
            sx, sy, sz = cubo["size"]
            desde = (-(ox + sx), oy, oz)                      # origin = -(origin.x + size.x)
            hasta = (desde[0] + sx, oy + sy, oz + sz)
            vs = _vertices_gecko(desde, hasta)
            if "rotation" in cubo:
                cpx, cpy, cpz = cubo["pivot"]
                rc = cubo["rotation"]
                C = _giro_en((-cpx, cpy, cpz), (math.radians(-rc[0]), math.radians(-rc[1]), math.radians(rc[2])))
            else:
                C = Transformacion()
            M = T.despues(C)
            for cara in DIRECCIONES:
                f = cubo["uv"].get(cara)
                if f is None:
                    continue
                (u, v), (su, sv) = f["uv"], f["uv_size"]
                uvq = [(u + su, v), (u, v), (u, v + sv), (u + su, v + sv)]   # GeoQuad.build sin espejo
                P = [M(vs[n]) for n in QUADS[cara]]
                out.append((P, uvq, cara, _aplicar(M.R, NORMAL[cara]), b["name"]))
    return out


def caras_para_vista(quads):
    """Los quads en el formato de vista._caras_mundo (horario visto desde afuera)."""
    import numpy as np
    out = []
    for P, UV, cara, normal, _ in quads:
        P = np.array(P, dtype=float)
        UV = np.array(UV, dtype=float)
        if np.dot(np.cross(P[3] - P[0], P[1] - P[0]), normal) < 0:      # el render: horario desde afuera
            P, UV = P[::-1].copy(), UV[::-1].copy()
        out.append((P, UV))
    return out


def comprobar(modelo, uvs, geo, tolerancia=1e-3):
    """Compara cara por cara (posicion de cada esquina y su UV) el modelo del kit contra la reconstruccion de
    GeckoLib en reposo. Devuelve el error maximo de posicion (px) y de UV (texeles)."""
    from .luz import rot_matriz
    kit = {}
    for c in modelo.cubos:
        R = rot_matriz(*c.rot) if c.rot else None
        o = c.origen
        for cara in c.caras:
            mapa = _uv_del_kit(c.desde, c.hasta, cara, uvs[id(c)][cara])
            for pos, uv in mapa.items():
                p = pos
                if R is not None:
                    q = _aplicar(R, tuple(pos[i] - o[i] for i in range(3)))
                    p = tuple(q[i] + o[i] for i in range(3))
                kit.setdefault((round(uv[0], 3), round(uv[1], 3)), []).append(p)
    peor_pos = 0.0
    sin_pareja = 0
    for P, UV, cara, *_ in reconstruir(geo):
        for p, uv in zip(P, UV):
            cand = kit.get((round(uv[0], 3), round(uv[1], 3)))
            if not cand:
                sin_pareja += 1
                continue
            peor_pos = max(peor_pos, min(math.dist(p, q) for q in cand))
    return peor_pos, sin_pareja


def guardar(modelo, carpeta, identificador, animaciones=None):
    """Escribe <identificador>.geo.json, <identificador>.png y, si hay, <identificador>.animation.json."""
    import os
    os.makedirs(carpeta, exist_ok=True)
    lienzo, uvs = modelo.pintar()
    geo = exportar_geo(modelo, uvs, lienzo, identificador)
    with open(os.path.join(carpeta, f"{identificador}.geo.json"), "w", encoding="utf-8") as f:
        json.dump(geo, f, separators=(",", ":"))
    with open(os.path.join(carpeta, f"{identificador}.png"), "wb") as f:
        f.write(lienzo.png())
    if animaciones:
        with open(os.path.join(carpeta, f"{identificador}.animation.json"), "w", encoding="utf-8") as f:
            json.dump(animaciones, f, indent=1)
    return geo, lienzo, uvs
