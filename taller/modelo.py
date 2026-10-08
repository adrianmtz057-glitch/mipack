"""
Modelo en cubos y mallas low-poly con esqueleto de player, atlas de textura pintado y exportacion a .bbmodel.

Convenciones (las de Blockbench):
  - Unidades en px (16 px = 1 bloque). Pies en y = 0, el player mide 32 px.
  - El frente del modelo mira a -Z (cara "north"). La derecha del personaje es +X.
  - Cada cara se pinta texel a texel con un "pintor" que recibe la posicion 3D del texel.
"""

import base64
import json
import math
import uuid

from . import malla as geo
from .luz import Luz, rot_matriz, _aplicar
from .textura import Lienzo, TRANSPARENTE

CARAS = ("north", "east", "south", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0),
          "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}

# Huesos del player. Los nombres son palabras clave de Figura (sirven tal cual en ModelEngine).
HUESOS = {
    "Head": (0, 24, 0),
    "Body": (0, 24, 0),
    "RightArm": (5, 22, 0),
    "LeftArm": (-5, 22, 0),
    "RightLeg": (2, 12, 0),
    "LeftLeg": (-2, 12, 0),
}
ESPEJO_HUESO = {"RightArm": "LeftArm", "LeftArm": "RightArm",
                "RightLeg": "LeftLeg", "LeftLeg": "RightLeg"}


def esquinas(f, t, cara):
    """(arriba-izq, arriba-der, abajo-izq) de la cara vista desde fuera, igual que la UV de Blockbench."""
    x1, y1, z1 = f
    x2, y2, z2 = t
    return {
        "north": ((x2, y2, z1), (x1, y2, z1), (x2, y1, z1)),
        "south": ((x1, y2, z2), (x2, y2, z2), (x1, y1, z2)),
        "east": ((x2, y2, z2), (x2, y2, z1), (x2, y1, z2)),
        "west": ((x1, y2, z1), (x1, y2, z2), (x1, y1, z1)),
        "up": ((x1, y2, z1), (x2, y2, z1), (x1, y2, z2)),
        "down": ((x1, y1, z2), (x2, y1, z2), (x1, y1, z1)),
    }[cara]


def tam_cara(f, t, cara):
    dx, dy, dz = (t[i] - f[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy),
            "up": (dx, dz), "down": (dx, dz)}[cara]


def uv_caja(ox, oy, w, h, d):
    """UV de una caja con el layout de las skins de Minecraft (box UV de Blockbench)."""
    return {
        "east": [ox, oy + d, ox + d, oy + d + h],
        "north": [ox + d, oy + d, ox + d + w, oy + d + h],
        "west": [ox + d + w, oy + d, ox + 2 * d + w, oy + d + h],
        "south": [ox + 2 * d + w, oy + d, ox + 2 * d + 2 * w, oy + d + h],
        "up": [ox + d + w, oy + d, ox + d, oy],
        "down": [ox + d + 2 * w, oy, ox + d + w, oy + d],
    }


class Texel:
    """Lo que recibe un pintor: posicion 3D del texel y datos de la cara/cubo."""
    __slots__ = ("x", "y", "z", "cara", "i", "j", "tw", "th", "f", "t", "nombre", "lado", "n")

    @property
    def fila_abajo(self):            # 0 = fila mas baja de una cara lateral
        return self.th - 1 - self.j

    @property
    def lateral(self):
        return self.cara not in ("up", "down")


class Cubo:
    __slots__ = ("nombre", "hueso", "desde", "hasta", "pintor", "rot", "origen", "uv", "caras", "lado", "dens")

    def __init__(self, nombre, hueso, desde, hasta, pintor, rot=None, origen=None, uv=None, caras=None, lado=1,
                 dens=1):
        self.nombre, self.hueso, self.pintor = nombre, hueso, pintor
        self.desde = [min(desde[i], hasta[i]) for i in range(3)]
        self.hasta = [max(desde[i], hasta[i]) for i in range(3)]
        self.rot = rot if rot and any(abs(r) > 1e-6 for r in rot) else None
        if self.rot and origen is None:
            origen = [(self.desde[i] + self.hasta[i]) / 2 for i in range(3)]
        self.origen = list(origen) if origen is not None else list(HUESOS.get(hueso.split("/")[0], (0, 0, 0)))
        self.uv = uv                     # dict cara -> [u1, v1, u2, v2] (solo cubos del cuerpo base)
        self.caras = caras or CARAS      # caras que existen (las demas quedan sin textura)
        self.lado = lado
        self.dens = dens                 # texeles por px (1 = normal, 2 = el doble de detalle)


class Malla:
    """Malla low-poly de Blockbench: vertices libres y caras planas de 3 o 4 vertices (antihorario desde afuera).
    Cada poligono original (grupo) tiene su pintor y su rectangulo en el atlas, proyectado sobre su plano:
    la textura nunca se estira aunque la cara este inclinada, y los triangulos de un mismo poligono
    comparten textura."""
    __slots__ = ("nombre", "hueso", "vertices", "caras", "grupo", "grupos", "normales", "lado", "dens")

    def __init__(self, nombre, hueso, vertices, lado=1, dens=1):
        self.nombre, self.hueso, self.lado, self.dens = nombre, hueso, lado, dens
        self.vertices = [tuple(float(c) for c in v) for v in vertices]
        self.caras = []          # triangulos y quads que se exportan
        self.grupo = []          # por cara: indice del grupo (poligono original)
        self.grupos = []         # por grupo: (pintor, indices del poligono original)
        self.normales = []       # por grupo: normal de la cara que se dio (un quad torcido partido en dos la comparte)


class Modelo:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.cubos: list[Cubo] = []
        self.mallas: list[Malla] = []
        self.pivotes = dict(HUESOS)
        self.luz = True          # luz horneada (taller/luz.py): volumen con sombras y cantos de luz

    def malla(self, hueso, nombre, vertices, caras, pintor, lado=1, dens=1):
        """Malla de caras planas antihorarias vistas desde afuera. Una cara puede tener 3, 4 o mas vertices
        (los poligonos de 5+ o concavos se triangulan; un quad torcido se parte en dos triangulos).
        pintor: uno para todas las caras o una lista (uno por cara)."""
        caras = [tuple(c) for c in caras]
        pintores = pintor if isinstance(pintor, (list, tuple)) else [pintor] * len(caras)
        if len(pintores) != len(caras):
            raise ValueError(f"{nombre}: {len(pintores)} pintores para {len(caras)} caras")
        m = Malla(nombre, hueso, vertices, lado, dens)
        vs = m.vertices

        def grupo_nuevo(pin, poli, tris):
            m.grupos.append((pin, tuple(poli)))
            m.normales.append(geo.normal([vs[i] for i in c]))
            for t in tris:
                m.caras.append(tuple(t))
                m.grupo.append(len(m.grupos) - 1)

        for c, pin in zip(caras, pintores):
            pts = [vs[i] for i in c]
            if len(c) < 3 or geo.normal(pts) == (0.0, 0.0, 0.0):
                raise ValueError(f"{nombre}: cara degenerada {c}")
            if len(c) == 3:
                grupo_nuevo(pin, c, [c])
                continue
            if len(c) == 4 and geo.plano(pts) > geo.TOL_PLANO:      # quad torcido: dos triangulos
                for t in geo._cara(vs, c):
                    grupo_nuevo(pin, t, [t])
                continue
            if geo.plano(pts) > 0.1:
                raise ValueError(f"{nombre}: el poligono {c} no es plano")
            _, der, arr = geo.marco(pts)
            pol2d = [(geo._dot(p, der), geo._dot(p, arr)) for p in pts]
            if len(c) == 4 and geo._convexo(pol2d):
                grupo_nuevo(pin, c, [c])
            else:
                grupo_nuevo(pin, c, [tuple(c[i] for i in t) for t in geo.triangular(pol2d)])
        self.mallas.append(m)
        return m

    def malla_par(self, hueso, nombre, vertices, caras, pintor, dens=1):
        """Malla del lado DERECHO (+X) que se copia en espejo a la izquierda (hueso Left...)."""
        for lado in (1, -1):
            h = hueso if lado == 1 else ESPEJO_HUESO.get(hueso.split("/")[0], hueso.split("/")[0])
            if lado == -1 and "/" in hueso:
                h += "/" + hueso.split("/", 1)[1]
            vs, cs = (vertices, caras) if lado == 1 else geo.espejo_x((vertices, caras))
            pint = pintor if lado == 1 or not isinstance(pintor, (list, tuple)) else list(pintor)
            self.malla(h, f"{nombre}_{'der' if lado == 1 else 'izq'}", vs, cs, pint, lado=lado, dens=dens)

    def huesos_usados(self):
        return {e.hueso.split("/")[0] for e in list(self.cubos) + list(self.mallas)}

    # ------------------------------------------------------------------ construccion
    def cubo(self, hueso, nombre, desde, hasta, pintor, rot=None, origen=None, uv=None, caras=None, lado=1, dens=1):
        """Cubo de 'desde' a 'hasta'. Si un eje mide 0 es un PLANO (solo sus dos caras grandes)."""
        tam = [abs(hasta[i] - desde[i]) for i in range(3)]
        ceros = [i for i in range(3) if tam[i] < 1e-6]
        if len(ceros) > 1:
            return None
        if ceros and caras is None:
            caras = {0: ("east", "west"), 1: ("up", "down"), 2: ("north", "south")}[ceros[0]]
        if origen is None and not rot:
            origen = self.pivotes.get(hueso.split("/")[0], (0, 0, 0))
        c = Cubo(nombre, hueso, desde, hasta, pintor, rot, origen, uv, caras, lado, dens)
        self.cubos.append(c)
        return c

    def par(self, hueso, nombre, desde, hasta, pintor, rot=None, origen=None, caras=None, dens=1):
        """Pieza simetrica: se da la del lado DERECHO (+X) y se refleja a la izquierda."""
        for lado in (1, -1):
            h = hueso if lado == 1 else ESPEJO_HUESO.get(hueso.split("/")[0], hueso.split("/")[0])
            if lado == -1 and "/" in hueso:
                h += "/" + hueso.split("/", 1)[1]
            x1, x2 = sorted((desde[0] * lado, hasta[0] * lado))
            r = None if rot is None else (rot[0], rot[1] * lado, rot[2] * lado)
            o = None if origen is None else (origen[0] * lado, origen[1], origen[2])
            self.cubo(h, f"{nombre}_{'der' if lado == 1 else 'izq'}", (x1, desde[1], desde[2]),
                      (x2, hasta[1], hasta[2]), pintor, r, o, caras=caras, lado=lado, dens=dens)

    # ------------------------------------------------------------------ textura
    def _empaquetar(self, ancho):
        """Reparte las caras sin UV fija en el atlas (el rincon 64x64 es la skin). Devuelve alto usado."""
        piezas = []
        for c in self.cubos:
            if c.uv:
                continue
            for cara in c.caras:
                w, h = tam_cara(c.desde, c.hasta, cara)
                d = c.dens
                piezas.append((max(1, math.ceil(h * d - 1e-6)), max(1, math.ceil(w * d - 1e-6)), c, cara))
        for m in self.mallas:
            for g in range(len(m.grupos)):
                w, h = self._medida_grupo(m, g)[:2]
                piezas.append((max(1, math.ceil(h * m.dens - 1e-6)), max(1, math.ceil(w * m.dens - 1e-6)), m, g))
        piezas.sort(key=lambda p: (-p[0], -p[1]))
        skin = 64 if any(c.uv for c in self.cubos) else 0      # rincon reservado a la skin

        def x_ini(y):
            return skin if y < skin else 0
        x, y, alto_fila, asign = x_ini(0), 0, 0, {}
        for th, tw, c, cara in piezas:
            x0 = x_ini(y)
            if x + tw > ancho:
                y += alto_fila
                x, alto_fila = x_ini(y), 0
            if tw > ancho - x_ini(y):
                return None
            if alto_fila == 0:
                alto_fila = th
                x = max(x, x0)
            asign[(id(c), cara)] = (x, y, tw, th)
            x += tw
        return max(skin, y + alto_fila), asign

    @staticmethod
    def _medida_grupo(m, g):
        """(ancho, alto, s_min, t_min, normal, derecha, arriba) del poligono g de la malla m en su propio plano."""
        pts = [m.vertices[i] for i in m.grupos[g][1]]
        n, der, arr = geo.marco(pts)
        ss = [geo._dot(p, der) for p in pts]
        ts = [-geo._dot(p, arr) for p in pts]
        return max(ss) - min(ss), max(ts) - min(ts), min(ss), min(ts), n, der, arr

    @staticmethod
    def _marco_luz(c, cara, tl, tr, bl):
        """Datos de una cara de cubo para la luz horneada: (pos(s, r) en el mundo, normal, ancho, alto, dueno,
        lateral). Tiene en cuenta el giro del cubo."""
        R = rot_matriz(*c.rot) if c.rot else None
        o = c.origen
        ancho, alto = tam_cara(c.desde, c.hasta, cara)

        def pos(s, r):
            p = tuple(tl[i] + s * (tr[i] - tl[i]) + r * (bl[i] - tl[i]) for i in range(3))
            if R is None:
                return p
            q = _aplicar(R, (p[0] - o[0], p[1] - o[1], p[2] - o[2]))
            return (q[0] + o[0], q[1] + o[1], q[2] + o[2])
        n = NORMAL[cara] if R is None else _aplicar(R, NORMAL[cara])
        return pos, n, ancho, alto, id(c), abs(n[1]) < 0.7

    @staticmethod
    def _cantos_malla(m):
        """Aristas de la malla que son canto de verdad: abiertas (de un solo poligono) o con un quiebre fuerte
        (mas de 50 grados entre las caras). Las aristas entre paneles de una superficie suave no llevan canto."""
        def clave(i):
            return tuple(round(c, 3) for c in m.vertices[i])
        usos = {}
        for _, poli in m.grupos:
            n = geo.normal([m.vertices[i] for i in poli])
            for k in range(len(poli)):
                a, b = clave(poli[k - 1]), clave(poli[k])
                usos.setdefault((min(a, b), max(a, b)), []).append(n)
        cantos = set()
        for arista, ns in usos.items():
            if len(ns) == 1 or any(geo._dot(ns[0], q) < math.cos(math.radians(50)) for q in ns[1:]):
                cantos.add(arista)
        return cantos, clave

    def _marco_luz_malla(self, m, g, d, n, der, arr, s0, t0, w, h, cantos):
        """Lo mismo para un poligono de malla, con la prueba de si un punto cae adentro del poligono y con sus
        aristas que son canto (en el plano del poligono)."""
        poli = m.grupos[g][1]
        pol = [(geo._dot(m.vertices[i], der), -geo._dot(m.vertices[i], arr)) for i in poli]
        aristas, clave = cantos
        mios = []
        for k in range(len(poli)):
            a, b = clave(poli[k - 1]), clave(poli[k])
            if (min(a, b), max(a, b)) in aristas:
                mios.append((pol[k - 1], pol[k]))

        cx, cy = sum(q[0] for q in pol) / len(pol), sum(q[1] for q in pol) / len(pol)

        def adentro(x, y):
            dentro = False
            for k in range(len(pol)):
                (x1, y1), (x2, y2) = pol[k], pol[k - 1]
                if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    dentro = not dentro
            return dentro

        def pos(a, b):
            """Punto de la grilla de luz sobre el poligono: si cae afuera (el rect es mas grande que un triangulo)
            se trae al borde, asi la muestra queda sobre la superficie de verdad y no detras de la cara vecina."""
            s, t = s0 + a * w, t0 + b * h
            if not adentro(s, t):
                mejor = None
                for k in range(len(pol)):
                    (x1, y1), (x2, y2) = pol[k - 1], pol[k]
                    dx, dy = x2 - x1, y2 - y1
                    u = max(0.0, min(1.0, ((s - x1) * dx + (t - y1) * dy) / ((dx * dx + dy * dy) or 1e-9)))
                    px, py = x1 + u * dx, y1 + u * dy
                    dd = (px - s) ** 2 + (py - t) ** 2
                    if mejor is None or dd < mejor[0]:
                        mejor = (dd, px, py)
                _, s, t = mejor
                s, t = s + (cx - s) * 0.02, t + (cy - t) * 0.02
            return (d * n[0] + s * der[0] - t * arr[0], d * n[1] + s * der[1] - t * arr[1],
                    d * n[2] + s * der[2] - t * arr[2])

        def cruza(a, b, db):
            """Si al moverse db (en 0..1 del alto) desde (a, b) se cruza una arista que es canto."""
            x, y1, y2 = s0 + a * w, t0 + b * h, t0 + (b + db) * h
            lo, hi = min(y1, y2), max(y1, y2)
            for (xa, ya), (xb, yb) in mios:
                if (xa > x) == (xb > x) or xa == xb:
                    continue
                y = ya + (x - xa) * (yb - ya) / (xb - xa)
                if lo <= y <= hi:
                    return True
            return False
        return pos, n, w, h, id(m), abs(n[1]) < 0.7, cruza, m.normales[g]

    def pintar(self):
        """Pinta todas las caras y, si self.luz, hornea la luz encima. Devuelve (lienzo, uv por cubo/malla)."""
        for ancho in (128, 256, 512, 1024, 2048):
            r = self._empaquetar(ancho)
            if r and r[0] <= ancho:
                usado, asign = r
                break
        else:
            raise RuntimeError("El modelo tiene demasiada superficie para un atlas de 2048 px")
        lado = ancho
        lienzo = Lienzo(lado, lado)
        uvs = {}
        tx = Texel()
        caras_luz = []           # lo que hace falta para hornear la luz despues, cuando ya esta todo pintado
        for c in self.cubos:
            uvc = {}
            for cara in c.caras:
                if c.uv:
                    u1, v1, u2, v2 = c.uv[cara]
                    tw, th = int(abs(u2 - u1)), int(abs(v2 - v1))
                else:
                    x, y, tw, th = asign[(id(c), cara)]
                    u1, v1, u2, v2 = x, y, x + tw, y + th
                uvc[cara] = [u1, v1, u2, v2]
                tl, tr, bl = esquinas(c.desde, c.hasta, cara)
                ux, uy = min(u1, u2), min(v1, v2)
                tx.cara, tx.tw, tx.th, tx.f, tx.t, tx.nombre, tx.lado = cara, tw, th, c.desde, c.hasta, c.nombre, c.lado
                tx.n = NORMAL[cara]
                for jy in range(th):
                    r = (jy + 0.5) / th
                    if v1 > v2:
                        r = 1 - r
                    for ix in range(tw):
                        s = (ix + 0.5) / tw
                        if u1 > u2:
                            s = 1 - s
                        tx.x = tl[0] + s * (tr[0] - tl[0]) + r * (bl[0] - tl[0])
                        tx.y = tl[1] + s * (tr[1] - tl[1]) + r * (bl[1] - tl[1])
                        tx.z = tl[2] + s * (tr[2] - tl[2]) + r * (bl[2] - tl[2])
                        tx.i, tx.j = int(s * tw), int(r * th)
                        col = c.pintor(tx) if c.pintor else TRANSPARENTE
                        lienzo.poner(ux + ix, uy + jy, col)
                if self.luz:
                    caras_luz.append((self._marco_luz(c, cara, tl, tr, bl) + (th, None), ux, uy, tw, th,
                                      u1 > u2, v1 > v2))
            uvs[id(c)] = uvc
        for m in self.mallas:
            cantos = self._cantos_malla(m) if self.luz else None
            xs, ys, zs = zip(*m.vertices)
            tx.f, tx.t, tx.nombre, tx.lado = (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)), m.nombre, m.lado
            marcos = []
            for g, (pintor, _) in enumerate(m.grupos):
                w, h, s0, t0, n, der, arr = self._medida_grupo(m, g)
                ux, uy, tw, th = asign[(id(m), g)]
                kx, ky = tw / max(w, 1e-9), th / max(h, 1e-9)
                marcos.append((ux, uy, kx, ky, s0, t0, der, arr))
                d = geo._dot(m.vertices[m.grupos[g][1][0]], n)
                tx.cara, tx.tw, tx.th, tx.n = geo.cara_cercana(n), tw, th, n
                for jy in range(th):
                    t = t0 + (jy + 0.5) / ky
                    for ix in range(tw):
                        s = s0 + (ix + 0.5) / kx
                        tx.x = d * n[0] + s * der[0] - t * arr[0]
                        tx.y = d * n[1] + s * der[1] - t * arr[1]
                        tx.z = d * n[2] + s * der[2] - t * arr[2]
                        tx.i, tx.j = ix, jy
                        lienzo.poner(ux + ix, uy + jy, pintor(tx) if pintor else TRANSPARENTE)
                if self.luz:
                    # en la malla la textura no se da vuelta: s y r salen directo de la columna y la fila
                    marco = self._marco_luz_malla(m, g, d, n, der, arr, s0, t0, w, h, cantos)
                    caras_luz.append((marco[:6] + (th, marco[6], marco[7]), ux, uy, tw, th, False, False))
            uvm = []
            for cara, g in zip(m.caras, m.grupo):
                ux, uy, kx, ky, s0, t0, der, arr = marcos[g]
                uvm.append([(ux + (geo._dot(m.vertices[i], der) - s0) * kx,
                             uy + (-geo._dot(m.vertices[i], arr) - t0) * ky) for i in cara])
            uvs[id(m)] = uvm
        if self.luz:
            self._hornear_luz(lienzo, uvs, caras_luz)
        return lienzo, uvs

    def _hornear_luz(self, lienzo, uvs, caras_luz):
        """Segunda pasada: con todo ya pintado (asi lo transparente no tapa la luz), corre cada texel unos pasos de su
        rampa segun la oclusion, la sombra proyectada y los cantos (taller/luz.py)."""
        luz = Luz(self, lienzo, uvs)
        for datos, ux, uy, tw, th, voltea_u, voltea_v in caras_luz:
            sombrear = luz.cara(*datos)
            for jy in range(th):
                r = (jy + 0.5) / th
                if voltea_v:
                    r = 1 - r
                for ix in range(tw):
                    s = (ix + 0.5) / tw
                    if voltea_u:
                        s = 1 - s
                    col = lienzo.leer(ux + ix, uy + jy)
                    nuevo = sombrear(col, s, r)
                    if nuevo is not col:
                        lienzo.poner(ux + ix, uy + jy, nuevo)

    # ------------------------------------------------------------------ exportar
    def a_bbmodel(self, lienzo=None, uvs=None) -> dict:
        if lienzo is None:
            lienzo, uvs = self.pintar()
        grupos: dict[str, dict] = {}
        raiz: list = []

        def grupo(ruta):
            if ruta in grupos:
                return grupos[ruta]
            partes = ruta.split("/")
            hueso = partes[0]
            g = {"name": partes[-1], "origin": list(self.pivotes.get(hueso, (0, 0, 0))), "color": 0,
                 "uuid": str(uuid.uuid4()), "export": True, "mirror_uv": False, "isOpen": len(partes) == 1,
                 "locked": False, "visibility": True, "autouv": 0, "children": []}
            (raiz if len(partes) == 1 else grupo("/".join(partes[:-1]))["children"]).append(g)
            grupos[ruta] = g
            return g

        usados = self.huesos_usados()
        for h in self.pivotes:                             # orden fijo de los huesos en el outliner
            if h in usados:
                grupo(h)

        elementos = []
        for c in self.cubos:
            uid = str(uuid.uuid4())
            e = {"name": c.nombre, "box_uv": False, "rescale": False, "locked": False,
                 "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
                 "from": [round(v, 4) for v in c.desde], "to": [round(v, 4) for v in c.hasta],
                 "autouv": 0, "color": abs(hash(c.hueso)) % 8,
                 "origin": [round(v, 4) for v in c.origen],
                 "faces": {cara: ({"uv": uvs[id(c)][cara], "texture": 0} if cara in c.caras
                                  else {"uv": [0, 0, 0, 0], "texture": None}) for cara in CARAS},
                 "type": "cube", "uuid": uid}
            if c.rot:
                e["rotation"] = [round(r, 3) for r in c.rot]
            elementos.append(e)
            grupo(c.hueso)["children"].append(uid)

        for m in self.mallas:                              # mallas: vertices en coordenadas del modelo
            uid = str(uuid.uuid4())
            claves = [f"v{i:03d}" for i in range(len(m.vertices))]
            caras = {}
            for k, cara in enumerate(m.caras):
                caras[f"f{k:03d}"] = {
                    "uv": {claves[i]: [round(u, 4), round(v, 4)] for i, (u, v) in zip(cara, uvs[id(m)][k])},
                    "vertices": [claves[i] for i in cara], "texture": 0}
            elementos.append({
                "name": m.nombre, "color": abs(hash(m.hueso)) % 8, "origin": [0, 0, 0], "rotation": [0, 0, 0],
                "export": True, "visibility": True, "locked": False, "render_order": "default",
                "allow_mirror_modeling": True,
                "vertices": {k: [round(c, 4) for c in v] for k, v in zip(claves, m.vertices)},
                "faces": caras, "type": "mesh", "uuid": uid})
            grupo(m.hueso)["children"].append(uid)

        png = lienzo.png()
        nombre_tex = f"{self.nombre}.png"
        return {
            "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": self.nombre, "model_identifier": "", "visible_box": [1, 1, 0],
            "variable_placeholders": "", "variable_placeholder_buttons": [], "unhandled_root_fields": {},
            "resolution": {"width": lienzo.ancho, "height": lienzo.alto},
            "elements": elementos, "outliner": raiz,
            "textures": [{"path": "", "name": nombre_tex, "folder": "", "namespace": "", "id": "0",
                          "width": lienzo.ancho, "height": lienzo.alto,
                          "uv_width": lienzo.ancho, "uv_height": lienzo.alto,
                          "particle": False, "render_mode": "default", "render_sides": "auto",
                          "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                          "frame_interpolation": False, "visible": True, "internal": True, "saved": False,
                          "uuid": str(uuid.uuid4()),
                          "source": "data:image/png;base64," + base64.b64encode(png).decode()}],
        }

    def guardar(self, ruta_bbmodel: str):
        lienzo, uvs = self.pintar()
        datos = self.a_bbmodel(lienzo, uvs)
        with open(ruta_bbmodel, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        return lienzo, uvs, datos
