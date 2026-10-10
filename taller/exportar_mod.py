"""
Genera los recursos del mod de Forge (mod/src/main/resources/assets/mipack/) desde el taller:
  - Crackatos: geo/entity/crackatos.geo.json, textures/entity/crackatos.png (con la luz horneada),
    textures/entity/crackatos_glowmask.png (solo los ojos: brillan en lo oscuro) y
    animations/entity/crackatos.animation.json (todas las de personajes/crackatos_anim.py).
  - La pua que sale del lomo y cae del cielo: geo/entity/pua.geo.json y textures/entity/pua.png.
  - El circulo morado de aviso: textures/entity/circulo.png y circulo_lleno.png.
  - Los nombres (lang) y el modelo del huevo.
Uso: python -m taller.exportar_mod
"""

import gzip
import io
import json
import math
import os
import struct

from PIL import Image

from . import animar, geckolib
from .kit import Personaje
from .luz import LUZ_SIMETRICA
from .personajes import crackatos, crackatos_anim

RAIZ = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources", "assets", "mipack")
ESCALA = 2.0                                  # la de CrackatosEntity.ESCALA


def _escribir_json(ruta, datos, compacto=True):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        if compacto:
            json.dump(datos, f, separators=(",", ":"), ensure_ascii=False)
        else:
            json.dump(datos, f, indent=2, ensure_ascii=False)


def _imagen(lienzo):
    return Image.open(io.BytesIO(lienzo.png())).convert("RGBA")


def mascara_de_brillo(modelo, uvs, img, nombres=("ojo", "brillo")):
    """Una textura igual de grande con solo las caras de los cubos que brillan (lo demas transparente)."""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for c in modelo.cubos:
        if not c.nombre.startswith(nombres):
            continue
        for u1, v1, u2, v2 in uvs[id(c)].values():
            caja = (int(min(u1, u2)) - 1, int(min(v1, v2)) - 1, int(max(u1, u2)) + 1, int(max(v1, v2)) + 1)
            out.paste(img.crop(caja), caja[:2])
    return out


def crackatos_assets():
    p = crackatos.construir()
    lienzo, uvs = p.m.pintar()
    geo = geckolib.exportar_geo(p.m, uvs, lienzo, "crackatos")
    geckolib.comprobar(p.m, uvs, geo)
    img = _imagen(lienzo)
    _escribir_json(os.path.join(RAIZ, "geo", "entity", "crackatos.geo.json"), geo)
    os.makedirs(os.path.join(RAIZ, "textures", "entity"), exist_ok=True)
    img.save(os.path.join(RAIZ, "textures", "entity", "crackatos.png"))
    mascara_de_brillo(p.m, uvs, img).save(os.path.join(RAIZ, "textures", "entity", "crackatos_glowmask.png"))

    rig = animar.Rig(geo)
    horneadas = crackatos_anim.hornear_todas(rig)
    malas = []
    for nombre, (_datos, cuadros, bucle) in horneadas.items():
        r = animar.revisar(rig, cuadros, bucle is True)
        if r["atraviesa_piso"] or r["brinco_del_bucle"] > 1e-3:
            malas.append((nombre, r))
    if malas:
        raise RuntimeError(f"animaciones que no pasan las pruebas: {malas}")
    anims = animar.exportar({n: d for n, (d, _c, _b) in horneadas.items()}, "crackatos")
    _escribir_json(os.path.join(RAIZ, "animations", "entity", "crackatos.animation.json"), anims)

    xs = [v for c in p.m.cubos for v in (c.desde[0], c.hasta[0])]
    ys = [v for c in p.m.cubos for v in (c.desde[1], c.hasta[1])]
    zs = [v for c in p.m.cubos for v in (c.desde[2], c.hasta[2])]
    medidas = tuple((max(v) - min(v)) * ESCALA / 16 for v in (xs, ys, zs))
    return {"cubos": len(p.m.cubos), "textura": img.size, "animaciones": list(horneadas),
            "medidas_en_bloques (ancho, alto, largo)": tuple(round(m, 2) for m in medidas)}


def pua_assets():
    """Una pua del lomo (la forma 'cristal'), parada: base en el origen y punta en +Y, 1.5 bloques."""
    p = Personaje("pua", altura=32)
    p.m.luz_desde = LUZ_SIMETRICA
    crackatos.esquirla_cubos(p, "pua", "pua", (0.0, 0.0, 0.0), 8.0, 24.0, (0.0, 0.0, 0.0), "cristal",
                             crackatos.cristal_cubos())
    p.m.pivotes = {"pua": (0.0, 0.0, 0.0)}
    lienzo, uvs = p.m.pintar()
    geo = geckolib.exportar_geo(p.m, uvs, lienzo, "pua")
    geckolib.comprobar(p.m, uvs, geo)
    _escribir_json(os.path.join(RAIZ, "geo", "entity", "pua.geo.json"), geo)
    _imagen(lienzo).save(os.path.join(RAIZ, "textures", "entity", "pua.png"))
    return {"cubos": len(p.m.cubos)}


def circulos(lado=128):
    """El aviso: un anillo morado (con un relleno tenue y un anillo interior) y el disco que se va llenando."""
    anillo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    lleno = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    claro, medio = (214, 150, 255), (170, 90, 245)
    c = (lado - 1) / 2
    for y in range(lado):
        for x in range(lado):
            r = math.hypot(x - c, y - c) / (lado / 2)
            if r > 1.0:
                continue
            borde = max(0.0, 1 - abs(r - 0.94) / 0.06)            # el anillo de afuera
            interior = max(0.0, 1 - abs(r - 0.55) / 0.025) * 0.5  # una raya adentro
            a = max(borde, interior, 0.16)
            col = claro if borde > 0.5 else medio
            anillo.putpixel((x, y), col + (int(255 * a),))
            a2 = 0.35 + 0.45 * r ** 3                               # mas fuerte en la orilla del disco
            if r > 0.93:
                a2 = 0.9
            lleno.putpixel((x, y), medio + (int(255 * a2),))
    anillo.save(os.path.join(RAIZ, "textures", "entity", "circulo.png"))
    lleno.save(os.path.join(RAIZ, "textures", "entity", "circulo_lleno.png"))


def textos():
    en = {"entity.mipack.crackatos": "Crackatos", "entity.mipack.pua": "Amethyst Spike",
          "item.mipack.crackatos_spawn_egg": "Crackatos Spawn Egg", "itemGroup.mipack": "Mipack"}
    es = {"entity.mipack.crackatos": "Crackatos", "entity.mipack.pua": "Púa de amatista",
          "item.mipack.crackatos_spawn_egg": "Huevo de Crackatos", "itemGroup.mipack": "Mipack"}
    for idioma, d in (("en_us", en), ("es_mx", es), ("es_es", es)):
        _escribir_json(os.path.join(RAIZ, "lang", f"{idioma}.json"), d, compacto=False)
    _escribir_json(os.path.join(RAIZ, "models", "item", "crackatos_spawn_egg.json"),
                   {"parent": "minecraft:item/template_spawn_egg"}, compacto=False)


# ---------------------------------------------------------------- la arena de la prueba automatica (GameTest)

def _nbt(nombre, valor, tipo=None):
    """NBT binario minimo: Int, String, List de Int / Compound, Compound (los dict)."""
    def nom(n):
        b = n.encode("utf-8")
        return struct.pack(">H", len(b)) + b

    def carga(v, t):
        if t == 3:
            return struct.pack(">i", v)
        if t == 8:
            return nom(v)
        if t == 10:
            return b"".join(_nbt(k, x) for k, x in v.items()) + b"\x00"
        if t == 9:
            sub = 3 if v and isinstance(v[0], int) else (10 if v else 0)
            return struct.pack(">bi", sub, len(v)) + b"".join(carga(x, sub) for x in v)
        raise ValueError(t)
    t = tipo or (3 if isinstance(valor, int) else 8 if isinstance(valor, str) else 10 if isinstance(valor, dict) else 9)
    return struct.pack(">b", t) + nom(nombre) + carga(valor, t)


def arena(lado=33, alto=8):
    """data/mipack/structures/arena.nbt: piso de piedra, paredes de ladrillo de pizarra de 5 de alto y aire adentro
    (la pelea de prueba: Crackatos tiene que poder embestir y chocar con las paredes)."""
    paleta = [{"Name": "minecraft:stone"}, {"Name": "minecraft:deepslate_bricks"}, {"Name": "minecraft:air"}]
    bloques = []
    for x in range(lado):
        for z in range(lado):
            borde = x in (0, lado - 1) or z in (0, lado - 1)
            for y in range(alto):
                if y == 0:
                    estado = 0
                elif borde and y <= 5:
                    estado = 1
                else:
                    estado = 2
                bloques.append({"pos": [x, y, z], "state": estado})
    raiz = {"DataVersion": 3465, "size": [lado, alto, lado], "palette": paleta, "blocks": bloques, "entities": []}
    ruta = os.path.join(RAIZ, "..", "..", "data", "mipack", "structures", "arena.nbt")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(gzip.compress(_nbt("", raiz)))
    return os.path.normpath(ruta)


def main():
    print("crackatos:", crackatos_assets())
    print("pua:", pua_assets())
    circulos()
    textos()
    print("arena:", arena())
    print("listo en", os.path.normpath(RAIZ))


if __name__ == "__main__":
    main()
