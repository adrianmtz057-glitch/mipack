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
from .personajes import crackatos, crackatos_anim, khaset_anim, khaset_extras, khaset_mob

RAIZ = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources", "assets", "mipack")
ESCALA = 3.0                                  # la de CrackatosEntity.ESCALA


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
    os.makedirs(os.path.join(RAIZ, "textures", "item"), exist_ok=True)
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


# ---------------------------------------------------------------- Khaset

def _rects_de(elemento, uvs):
    """Los rectangulos de textura (u1, v1, u2, v2) de un cubo o de cada cara de una malla."""
    datos = uvs[id(elemento)]
    if isinstance(datos, dict):                                   # cubo: {cara: (u1, v1, u2, v2)}
        return [tuple(r) for r in datos.values()]
    out = []
    for cara in datos:                                            # malla: por cara, la UV de cada vertice
        us, vs = [q[0] for q in cara], [q[1] for q in cara]
        out.append((min(us), min(vs), max(us), max(vs)))
    return out


def _brasas(img, rect, fuerza=1.0):
    """Los pixeles color brasa (naranja o amarillo encendido) del rectangulo: lo que brilla en lo oscuro."""
    u1, v1, u2, v2 = (int(min(rect[0], rect[2])), int(min(rect[1], rect[3])), int(max(rect[0], rect[2])) + 1,
                      int(max(rect[1], rect[3])) + 1)
    for y in range(max(0, v1), min(img.height, v2)):
        for x in range(max(0, u1), min(img.width, u2)):
            r, g, b, a = img.getpixel((x, y))
            if a > 0 and r > 190 and 70 < g < 215 and b < 90 and r - b > 140:
                yield x, y, (r, g, b, a)


def khaset_mascaras(modelo, uvs, img):
    """La glowmask de Khaset (los ojos completos y las brasas de las grietas de manos, pies y costillas) y la textura
    de la fase 2 (khaset_furia: las brasas mas encendidas)."""
    brillo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    furia = img.copy()
    quema = ("antebrazo", "mano", "dedos", "canilla", "pie", "torso", "huesos")
    for e in list(modelo.cubos) + list(modelo.mallas):
        hueso = e.hueso.split("/")[-1]
        for rect in _rects_de(e, uvs):
            if hueso == "ojos":
                caja = (int(min(rect[0], rect[2])), int(min(rect[1], rect[3])), int(max(rect[0], rect[2])) + 1,
                        int(max(rect[1], rect[3])) + 1)
                brillo.paste(img.crop(caja), caja[:2])
            elif hueso in quema:
                for x, y, (r, g, b, a) in _brasas(img, rect):
                    brillo.putpixel((x, y), (r, g, b, a))
                    furia.putpixel((x, y), (255, min(255, g + 45), min(255, b + 40), a))
    return brillo, furia


def _puntos_de_mano(rig, pose, lado):
    """La palma (el centro de la mano con los dedos) y la punta de la garra (lo mas lejos de la muneca)."""
    pref = khaset_anim.MANOS[lado]
    pts = [q for P, _u, _c, _n, h in rig.quads(pose) if h.startswith(pref) for q in P]
    palma = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
    T = rig.transformaciones(pose)
    muneca = T[pref](rig.pivote[pref])
    punta = max(pts, key=lambda p: math.dist(p, muneca))
    return [round(v, 2) for v in palma], [round(v, 2) for v in punta]


JAVA = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "java", "com", "mipack")


def escribir_poses_java(valores, cuadros_por, largos, tiempos):
    """PosesKhasetDatos.java: las manos (palma y punta, derecha e izquierda, x10 en enteros de 16 bits en base64),
    los tiempos clave y lo que dura cada animacion."""
    import base64
    datos = base64.b64encode(struct.pack(f">{len(valores)}h", *[round(v * 10) for v in valores])).decode()

    def flotantes(xs):
        return "{" + ", ".join(f"{x}f" for x in xs) + "}"
    lineas = ["// Generado por taller/exportar_mod.py (khaset_assets): no editar a mano.",
              "package com.mipack.khaset;", "",
              "/** Datos de las animaciones de Khaset para el servidor (ver PosesKhaset). */",
              "final class PosesKhasetDatos {",
              f"    static final float ESCALA = {khaset_mob.ESCALA}f;",
              f"    static final float[] ALTAR = {flotantes(khaset_anim.ALTAR)};",
              "    static final String[] ANIMS = {" + ", ".join(f'"{n}"' for n in POSES_KHASET) + "};",
              "    static final int[] CUADROS = {" + ", ".join(str(n) for n in cuadros_por) + "};"]
    for k, v in tiempos.items():
        lineas.append(f"    static final float[] {k} = {flotantes(v)};" if isinstance(v, list)
                      else f"    static final float {k} = {v}f;")
    lineas.append("    static final String[] LARGOS_NOMBRES = {" + ", ".join(f'"{n}"' for n in largos) + "};")
    lineas.append(f"    static final float[] LARGOS = {flotantes(largos.values())};")
    trozos = [datos[i:i + 100] for i in range(0, len(datos), 100)]
    lineas.append("    static final String DATOS = " + "\n            + ".join(f'"{t}"' for t in trozos) + ";")
    lineas += ["", "    private PosesKhasetDatos() {", "    }", "}", ""]
    ruta = os.path.join(JAVA, "khaset", "PosesKhasetDatos.java")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas))


POSES_KHASET = ("zarpazos", "barrido", "barrido_i", "contraataque", "lanzar_dardo", "agarrar", "agarrar_dos",
                "cargar", "cargar_dos", "soltar", "sacrificio", "invocar", "abalanzarse")
PASAN_EL_PISO = ("desvanecer", "aparecer")          # se hunden a proposito


def khaset_assets():
    p = khaset_mob.construir()
    lienzo, uvs = p.m.pintar()
    geo = geckolib.exportar_geo(p.m, uvs, lienzo, "khaset")
    peor, _sin_pareja = geckolib.comprobar(p.m, uvs, geo)          # (las mallas no entran en esta comparacion)
    if peor > 1e-2:
        raise RuntimeError(f"khaset: la reconstruccion de GeckoLib no coincide ({peor} px)")
    img = _imagen(lienzo)
    _escribir_json(os.path.join(RAIZ, "geo", "entity", "khaset.geo.json"), geo)
    carpeta = os.path.join(RAIZ, "textures", "entity")
    img.save(os.path.join(carpeta, "khaset.png"))
    brillo, furia = khaset_mascaras(p.m, uvs, img)
    brillo.save(os.path.join(carpeta, "khaset_glowmask.png"))
    furia.save(os.path.join(carpeta, "khaset_furia.png"))
    brillo.save(os.path.join(carpeta, "khaset_furia_glowmask.png"))

    rig = animar.Rig(geo)
    horneadas = khaset_anim.hornear_todas(rig)
    malas = []
    for nombre, (_datos, cuadros, bucle) in horneadas.items():
        r = animar.revisar(rig, cuadros, bucle is True)
        if (r["atraviesa_piso"] and nombre not in PASAN_EL_PISO) or r["brinco_del_bucle"] > 1e-3:
            malas.append((nombre, r))
    if malas:
        raise RuntimeError(f"animaciones que no pasan las pruebas: {malas}")
    anims = animar.exportar({n: d for n, (d, _c, _b) in horneadas.items()}, "khaset")
    _escribir_json(os.path.join(RAIZ, "animations", "entity", "khaset.animation.json"), anims)

    # para el servidor y el cliente: donde van las manos en cada tick de los ataques (el dano y la presa siguen a la
    # animacion); va como una clase de Java generada (mod/.../khaset/PosesKhasetDatos.java)
    valores = []
    cuadros_por = []
    for nombre in POSES_KHASET:
        _d, cuadros, _b = horneadas[nombre]
        cuadros_por.append(len(cuadros))
        for _t, pose in cuadros:
            for lado in ("d", "i"):
                pa, pu = _puntos_de_mano(rig, pose, lado)
                valores += pa + pu
    A = khaset_anim
    largos = {n: round(d["animation_length"], 4) for n, (d, _c, _b) in horneadas.items()}
    escribir_poses_java(valores, cuadros_por, largos, {
        "GOLPES_ZARPAZOS": list(A.GOLPES_ZARPAZOS), "BARRIDO": list(A.BARRIDO), "SACRIFICIO": list(A.SACRIFICIO),
        "SALTO": A.SALTO, "HUNDIDO": A.HUNDIDO, "DARDO": A.DARDO, "CONTRA": A.CONTRA, "AGARRA": A.AGARRA,
        "SOLTAR": A.SOLTAR, "INVOCA": A.INVOCA, "CORONA": A.CORONA})
    alto = max(q[1] for P, *_ in rig.quads({}) for q in P)
    return {"cubos": len(p.m.cubos), "mallas": len(p.m.mallas), "textura": img.size, "animaciones": len(horneadas),
            "alto_en_bloques": round(alto * khaset_mob.ESCALA / 16, 2)}


def _mascara_extras(modelo, uvs, img, enteros=(), brasas_en=()):
    """Glowmask: las piezas cuyo nombre empieza con 'enteros' brillan completas; en las de 'brasas_en' solo los
    pixeles color brasa."""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for e in list(modelo.cubos) + list(modelo.mallas):
        hueso = e.hueso.split("/")[-1]
        for rect in _rects_de(e, uvs):
            if e.nombre.startswith(tuple(enteros)) or hueso in enteros:
                caja = (int(min(rect[0], rect[2])), int(min(rect[1], rect[3])), int(max(rect[0], rect[2])) + 1,
                        int(max(rect[1], rect[3])) + 1)
                out.paste(img.crop(caja), caja[:2])
            elif e.nombre.startswith(tuple(brasas_en)):
                for x, y, c in _brasas(img, rect):
                    out.putpixel((x, y), c)
    return out


def _bucle_cierra(cuadros, simetria):
    """Si el primer y el ultimo cuadro son iguales salvo vueltas completas (o la simetria del hueso)."""
    a, b = cuadros[0][1], cuadros[-1][1]
    peor = 0.0
    for h in set(a) | set(b):
        ra, pa = a.get(h, ((0, 0, 0), (0, 0, 0)))
        rb, pb = b.get(h, ((0, 0, 0), (0, 0, 0)))
        paso = simetria.get(h, 360.0)
        for x, y in zip(ra, rb):
            d = (x - y) % paso
            peor = max(peor, min(d, paso - d))
        peor = max(peor, max(abs(x - y) for x, y in zip(pa, pb)))
    return peor < 1e-3


def extras_assets():
    """El cristal del sacrificio, la Xiuhcoatl, el dardo y la astilla (ver personajes/khaset_extras.py)."""
    X = khaset_extras
    info = {}
    piezas = (("cristal_sacrificio", X.cristal, X.ANIM_CRISTAL, dict(brasas_en=("obsidiana",)), {"cristal": 60.0}, ()),
              ("xiuhcoatl", X.xiuhcoatl, X.ANIM_XIUHCOATL,
               dict(enteros=("cresta", "lengua", "flama", "rayo", "ojos")), {}, ("surgir", "deshacer")),
              ("dardo", X.dardo, None, None, {}, ()),
              ("astilla", X.astilla, None, dict(brasas_en=("astilla",)), {}, ()))
    for ident, construir, anims, brillo, simetria, bajo_piso in piezas:
        p = construir()
        p.m.luz_desde = LUZ_SIMETRICA
        p.m.luz_por = "grupo"
        lienzo, uvs = p.m.pintar()
        geo = geckolib.exportar_geo(p.m, uvs, lienzo, ident)
        img = _imagen(lienzo)
        _escribir_json(os.path.join(RAIZ, "geo", "entity", f"{ident}.geo.json"), geo)
        img.save(os.path.join(RAIZ, "textures", "entity", f"{ident}.png"))
        if brillo:
            _mascara_extras(p.m, uvs, img, **brillo).save(os.path.join(RAIZ, "textures", "entity", f"{ident}_glowmask.png"))
        if anims:
            rig = animar.Rig(geo)
            horneadas = X.hornear(rig, anims)
            for nombre, (_d, cuadros, bucle) in horneadas.items():
                r = animar.revisar(rig, cuadros, False)
                if r["atraviesa_piso"] and nombre not in bajo_piso:
                    raise RuntimeError(f"{ident}.{nombre} atraviesa el piso: {r}")
                if bucle is True and not _bucle_cierra(cuadros, simetria):
                    raise RuntimeError(f"{ident}.{nombre} no cierra el bucle")
            _escribir_json(os.path.join(RAIZ, "animations", "entity", f"{ident}.animation.json"),
                           animar.exportar({n: d for n, (d, _c, _b) in horneadas.items()}, ident))
        info[ident] = {"cubos": len(p.m.cubos), "mallas": len(p.m.mallas), "textura": img.size}
    return info


def textos():
    en = {"entity.mipack.crackatos": "Crackatos", "entity.mipack.pua": "Amethyst Spike",
          "item.mipack.crackatos_spawn_egg": "Crackatos Spawn Egg", "itemGroup.mipack": "Mipack",
          "entity.mipack.khaset": "Khaset", "entity.mipack.cristal_sacrificio": "Sacrificial Crystal",
          "entity.mipack.xiuhcoatl": "Xiuhcoatl", "entity.mipack.dardo_atlatl": "Atlatl Dart", "entity.mipack.aviso": "Warning",
          "item.mipack.khaset_spawn_egg": "Khaset Spawn Egg", "item.mipack.cristal_sacrificio": "Sacrificial Crystal",
          "effect.mipack.desangrado": "Bleeding", "effect.mipack.derribado": "Knocked Down",
          "effect.mipack.aturdido": "Stunned", "effect.mipack.desorientado": "Disoriented", "boss.mipack.calor": "Heat",
          "death.attack.mipack.calor": "%1$s burned in the heat of Khaset",
          "death.attack.mipack.calor.player": "%1$s burned in the heat of %2$s",
          "death.attack.mipack.desangrado": "%1$s bled out",
          "death.attack.mipack.desangrado.player": "%1$s bled out fighting %2$s",
          "death.attack.mipack.sacrificio": "%1$s was sacrificed",
          "death.attack.mipack.sacrificio.player": "%1$s was sacrificed by %2$s"}
    es = {"entity.mipack.crackatos": "Crackatos", "entity.mipack.pua": "Púa de amatista",
          "item.mipack.crackatos_spawn_egg": "Huevo de Crackatos", "itemGroup.mipack": "Mipack",
          "entity.mipack.khaset": "Khaset", "entity.mipack.cristal_sacrificio": "Cristal del sacrificio",
          "entity.mipack.xiuhcoatl": "Xiuhcóatl", "entity.mipack.dardo_atlatl": "Dardo de átlatl", "entity.mipack.aviso": "Aviso",
          "item.mipack.khaset_spawn_egg": "Huevo de Khaset", "item.mipack.cristal_sacrificio": "Cristal del sacrificio",
          "effect.mipack.desangrado": "Desangrado", "effect.mipack.derribado": "Derribado",
          "effect.mipack.aturdido": "Aturdido", "effect.mipack.desorientado": "Desorientado", "boss.mipack.calor": "Calor",
          "death.attack.mipack.calor": "%1$s se quemó en el calor de Khaset",
          "death.attack.mipack.calor.player": "%1$s se quemó en el calor de %2$s",
          "death.attack.mipack.desangrado": "%1$s se desangró",
          "death.attack.mipack.desangrado.player": "%1$s se desangró peleando con %2$s",
          "death.attack.mipack.sacrificio": "%1$s fue sacrificado",
          "death.attack.mipack.sacrificio.player": "%1$s fue sacrificado por %2$s"}
    for idioma, d in (("en_us", en), ("es_mx", es), ("es_es", es)):
        _escribir_json(os.path.join(RAIZ, "lang", f"{idioma}.json"), d, compacto=False)
    for huevo in ("crackatos_spawn_egg", "khaset_spawn_egg"):
        _escribir_json(os.path.join(RAIZ, "models", "item", f"{huevo}.json"),
                       {"parent": "minecraft:item/template_spawn_egg"}, compacto=False)
    _escribir_json(os.path.join(RAIZ, "models", "item", "cristal_sacrificio.json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": "mipack:item/cristal_sacrificio"}},
                   compacto=False)
    icono_cristal().save(os.path.join(RAIZ, "textures", "item", "cristal_sacrificio.png"))


def icono_cristal():
    """El icono del objeto (16x16): el cristal de obsidiana con brasa sobre la piedra roja."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    obs, obs_l, fuego, oro = (36, 20, 30, 255), (70, 44, 60, 255), (240, 106, 30, 255), (214, 161, 58, 255)
    tez, tez_s = (126, 58, 44, 255), (84, 34, 28, 255)
    for y in range(1, 10):
        w = (y if y < 5 else 9 - y) * 0.75
        for x in range(16):
            if abs(x + 0.5 - 8) <= w:
                img.putpixel((x, y), fuego if (x + y) % 4 == 0 else obs_l if x < 8 else obs)
    for x in range(3, 13):
        img.putpixel((x, 5), oro)
    for y in range(11, 16):
        for x in range(2, 14):
            img.putpixel((x, y), tez_s if y == 15 or x in (2, 13) else tez)
    return img


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


def arena(lado=49, alto=10):
    """data/mipack/structures/arena.nbt: piso de piedra, paredes de ladrillo de pizarra de 7 de alto y aire adentro
    (la pelea de prueba: Crackatos tiene que poder embestir y chocar con las paredes)."""
    paleta = [{"Name": "minecraft:stone"}, {"Name": "minecraft:deepslate_bricks"}, {"Name": "minecraft:air"}]
    bloques = []
    for x in range(lado):
        for z in range(lado):
            borde = x in (0, lado - 1) or z in (0, lado - 1)
            for y in range(alto):
                if y == 0:
                    estado = 0
                elif borde and y <= 7:
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
    print("khaset:", khaset_assets())
    print("extras:", extras_assets())
    print("pua:", pua_assets())
    circulos()
    textos()
    print("arena:", arena())
    print("listo en", os.path.normpath(RAIZ))


if __name__ == "__main__":
    main()
