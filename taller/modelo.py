"""
Modelo en cubos con esqueleto de player, atlas de textura pintado y exportacion a .bbmodel.

Convenciones (las de Blockbench):
  - Unidades en px (16 px = 1 bloque). Pies en y = 0, el player mide 32 px.
  - El frente del modelo mira a -Z (cara "north"). La derecha del personaje es +X.
  - Cada cara se pinta texel a texel con un "pintor" que recibe la posicion 3D del texel.
"""

import base64
import json
import math
import uuid

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
    __slots__ = ("x", "y", "z", "cara", "i", "j", "tw", "th", "f", "t", "nombre", "lado")

    @property
    def fila_abajo(self):            # 0 = fila mas baja de una cara lateral
        return self.th - 1 - self.j

    @property
    def lateral(self):
        return self.cara not in ("up", "down")


class Cubo:
    __slots__ = ("nombre", "hueso", "desde", "hasta", "pintor", "rot", "origen", "uv", "caras", "lado")

    def __init__(self, nombre, hueso, desde, hasta, pintor, rot=None, origen=None, uv=None, caras=None, lado=1):
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


class Modelo:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.cubos: list[Cubo] = []

    # ------------------------------------------------------------------ construccion
    def cubo(self, hueso, nombre, desde, hasta, pintor, rot=None, origen=None, uv=None, caras=None, lado=1):
        if any(hasta[i] - desde[i] <= 0 for i in range(3)):
            return None
        c = Cubo(nombre, hueso, desde, hasta, pintor, rot, origen, uv, caras, lado)
        self.cubos.append(c)
        return c

    def par(self, hueso, nombre, desde, hasta, pintor, rot=None, origen=None):
        """Pieza simetrica: se da la del lado DERECHO (+X) y se refleja a la izquierda."""
        for lado in (1, -1):
            h = hueso if lado == 1 else ESPEJO_HUESO.get(hueso.split("/")[0], hueso.split("/")[0])
            if lado == -1 and "/" in hueso:
                h += "/" + hueso.split("/", 1)[1]
            x1, x2 = sorted((desde[0] * lado, hasta[0] * lado))
            r = None if rot is None else (rot[0], rot[1] * lado, rot[2] * lado)
            o = None if origen is None else (origen[0] * lado, origen[1], origen[2])
            self.cubo(h, f"{nombre}_{'der' if lado == 1 else 'izq'}", (x1, desde[1], desde[2]),
                      (x2, hasta[1], hasta[2]), pintor, r, o, lado=lado)

    # ------------------------------------------------------------------ textura
    def _empaquetar(self, ancho):
        """Reparte las caras sin UV fija en el atlas (el rincon 64x64 es la skin). Devuelve alto usado."""
        piezas = []
        for c in self.cubos:
            if c.uv:
                continue
            for cara in c.caras:
                w, h = tam_cara(c.desde, c.hasta, cara)
                piezas.append((max(1, math.ceil(h - 1e-6)), max(1, math.ceil(w - 1e-6)), c, cara))
        piezas.sort(key=lambda p: (-p[0], -p[1]))
        x, y, alto_fila, asign = 64, 0, 0, {}
        for th, tw, c, cara in piezas:
            x0 = 64 if y < 64 else 0
            if x + tw > ancho:
                y += alto_fila
                x, alto_fila = (64 if y < 64 else 0), 0
            if tw > ancho - (64 if y < 64 else 0):
                return None
            if alto_fila == 0:
                alto_fila = th
                x = max(x, x0)
            asign[(id(c), cara)] = (x, y, tw, th)
            x += tw
        return max(64, y + alto_fila), asign

    def pintar(self):
        """Pinta todas las caras. Devuelve (lienzo, uv por cubo)."""
        for ancho in (128, 256, 512, 1024):
            r = self._empaquetar(ancho)
            if r and r[0] <= ancho:
                usado, asign = r
                break
        else:
            raise RuntimeError("El modelo tiene demasiada superficie para un atlas de 1024 px")
        lado = ancho
        lienzo = Lienzo(lado, lado)
        uvs = {}
        tx = Texel()
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
            uvs[id(c)] = uvc
        return lienzo, uvs

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
            g = {"name": partes[-1], "origin": list(HUESOS.get(hueso, (0, 0, 0))), "color": 0,
                 "uuid": str(uuid.uuid4()), "export": True, "mirror_uv": False, "isOpen": len(partes) == 1,
                 "locked": False, "visibility": True, "autouv": 0, "children": []}
            (raiz if len(partes) == 1 else grupo("/".join(partes[:-1]))["children"]).append(g)
            grupos[ruta] = g
            return g

        for h in HUESOS:                                   # orden fijo de los huesos en el outliner
            if any(c.hueso.split("/")[0] == h for c in self.cubos):
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
