"""
Mete los 36 bichos de Velkia al mod: su modelo (geo), su textura, la manchada de mura (con lo que brilla), sus
animaciones (caminar, correr, atacar y las de ambiente), lo que sueltan (loot tables), sus nombres y los datos que
usa el mod (mod/src/main/java/com/mipack/bichos/BichosDatos.java: medidas, vida, dano, conducta, si vuela, cuando
pega y que animaciones tiene).

    python -m taller.bichos.exportar_bichos
"""

import json
import os

import numpy as np
from PIL import Image

from .. import animar, geckolib
from .catalogo import CATALOGO
from .hojas import armar
from .mover import AMBIENTE, ATACAR, CAMINAR, CORRER, GOLPE, Listo
from .piel import manchar_de_mura

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..", "mod", "src", "main")
ASSETS = os.path.join(RAIZ, "resources", "assets", "mipack")
DATA = os.path.join(RAIZ, "resources", "data", "mipack")
JAVA = os.path.join(RAIZ, "java", "com", "mipack", "bichos", "BichosDatos.java")

# conducta: PASIVO (huye), NEUTRAL (pega si le pegan; la manada de su especie se le va encima), HOSTIL, SAGRADO (el
# cervatillo: nadie le hace dano y nunca ataca)
CONDUCTA = {
    "cervatillo_musgo": "SAGRADO",
    "toro_arena": "NEUTRAL", "bufalo_terracota": "NEUTRAL", "hipopotamo": "NEUTRAL", "cabra_escarcha": "NEUTRAL",
    "babuino": "NEUTRAL", "cangrejo": "NEUTRAL", "aguila_gris": "NEUTRAL",
    "chacal_ceniza": "HOSTIL", "lobo_fuego": "HOSTIL", "escorpion_luz": "HOSTIL", "ballenato_duna": "HOSTIL",
    "cocodrilo_luz": "HOSTIL", "serpiente_rio_seco": "HOSTIL", "cria_varkhum": "HOSTIL", "cria_moruvahn": "HOSTIL",
    "ramita": "HOSTIL", "halcon_cobre": "HOSTIL", "salamandra_ceniza": "HOSTIL", "escarabajo_brasa": "HOSTIL",
    "murcielago_mura": "HOSTIL", "garrapata_sal": "HOSTIL", "cria_iskarum": "HOSTIL",
}
VUELAN = ("pato_estanque", "buitre", "halcon_cobre", "aguila_gris", "cuervo_negro", "ibis", "flamenco", "murcielago_mura")
FUEGO = ("salamandra_ceniza", "escarabajo_brasa", "lobo_fuego")
NOMBRE_EN = {
    "cervatillo_musgo": "Moss Fawn", "pato_estanque": "Pond Duck", "liebre_dorada": "Golden Hare", "toro_arena": "Sand Bull",
    "escarabajo_sagrado": "Sacred Scarab", "fenec": "Fennec", "chacal_ceniza": "Ash Jackal", "dromedario": "Dromedary",
    "gato_thza": "Thza Cat", "escorpion_luz": "Light Scorpion", "buitre": "Vulture", "ballenato_duna": "Dune Whaleling",
    "cangrejo": "Crab", "babuino": "Baboon", "ibis": "Ibis", "hipopotamo": "Hippo", "cocodrilo_luz": "Light Crocodile",
    "serpiente_rio_seco": "Dry River Snake", "cria_varkhum": "Varkhum Hatchling", "cria_moruvahn": "Moruvahn Hatchling",
    "ramita": "Twig Bug", "bufalo_terracota": "Terracotta Buffalo", "lagarto_roca": "Rock Lizard", "halcon_cobre": "Copper Hawk",
    "salamandra_ceniza": "Ash Salamander", "escarabajo_brasa": "Ember Beetle", "lobo_fuego": "Fire Wolf",
    "cuervo_negro": "Black Raven", "murcielago_mura": "Mura Bat", "flamenco": "Flamingo", "lagartija_blanca": "White Gecko",
    "garrapata_sal": "Salt Tick", "cria_iskarum": "Iskarum Calf", "cabra_escarcha": "Frost Goat", "marmota": "Marmot",
    "aguila_gris": "Grey Eagle",
}
# lo que suelta: (objeto, minimo, maximo)
SUELTA = {
    "cervatillo_musgo": [("mipack:semilla_musgo", 1, 2)], "pato_estanque": [("minecraft:feather", 0, 2), ("minecraft:egg", 0, 1)],
    "liebre_dorada": [("minecraft:rabbit_hide", 0, 1), ("minecraft:rabbit", 1, 1)],
    "toro_arena": [("minecraft:leather", 0, 2), ("mipack:cuerno_piedra", 0, 1)], "escarabajo_sagrado": [("mipack:caparazon", 1, 1)],
    "fenec": [("minecraft:rabbit_hide", 1, 1)], "chacal_ceniza": [("mipack:colmillo", 0, 2)], "dromedario": [("minecraft:leather", 0, 1)],
    "gato_thza": [("minecraft:string", 0, 1)], "escorpion_luz": [("mipack:aguijon", 1, 1)], "buitre": [("minecraft:feather", 1, 2)],
    "ballenato_duna": [("mipack:grasa", 1, 3)], "cangrejo": [("minecraft:cod", 1, 1)], "babuino": [],
    "ibis": [("minecraft:feather", 1, 1)], "hipopotamo": [("minecraft:beef", 2, 4)], "cocodrilo_luz": [("mipack:escamas", 1, 2)],
    "serpiente_rio_seco": [("minecraft:leather", 0, 1)], "cria_varkhum": [("mipack:escamas", 2, 3)],
    "cria_moruvahn": [("mipack:branquia", 1, 1)], "ramita": [("mipack:quitina", 1, 2)],
    "bufalo_terracota": [("minecraft:leather", 1, 2), ("minecraft:beef", 1, 2)], "lagarto_roca": [("mipack:cola_lagarto", 1, 1)],
    "halcon_cobre": [("minecraft:feather", 1, 2)], "salamandra_ceniza": [("mipack:glandula_salamandra", 1, 1)],
    "escarabajo_brasa": [("mipack:ceniza", 1, 2)], "lobo_fuego": [("mipack:brasa", 1, 1)],
    "cuervo_negro": [("mipack:pluma_negra", 1, 2)], "murcielago_mura": [("mipack:mura", 1, 1)],
    "flamenco": [("minecraft:pink_dye", 1, 1), ("minecraft:feather", 0, 1)], "lagartija_blanca": [("mipack:sal", 1, 2)],
    "garrapata_sal": [], "cria_iskarum": [("mipack:pelaje_grueso", 1, 3)],
    "cabra_escarcha": [("mipack:cuerno_piedra", 0, 1), ("minecraft:white_wool", 0, 1)], "marmota": [("minecraft:rabbit", 1, 1)],
    "aguila_gris": [("minecraft:feather", 1, 2)],
}


def _grupo(tabla, ident):
    for nombre, (f, ids) in tabla.items():
        if ident in ids:
            return nombre, f
    return None, None


def _png(lienzo, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    Image.frombytes("RGBA", (lienzo.ancho, lienzo.alto), bytes(lienzo.px)).save(ruta)


def _json(ruta, d):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))


def _golpe(grupo, ident):
    g = GOLPE.get(grupo, 0.4)
    if isinstance(g, dict):
        g = g.get(ident, g.get("*", 0.4))
    return g


def _loot(ident):
    pools = [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": o, "functions": [
        {"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": a, "max": b}},
        {"function": "minecraft:looting_enchant", "count": {"type": "minecraft:uniform", "min": 0, "max": 1}}]}]}
        for o, a, b in SUELTA.get(ident, [])]
    return {"type": "minecraft:entity", "pools": pools}


def exportar(ident):
    b = CATALOGO[ident]
    L = Listo(ident)
    _, _, _, mascara = armar(b)
    carpeta = os.path.join(ASSETS, "textures", "entity", "bichos")
    _json(os.path.join(ASSETS, "geo", "entity", "bichos", f"{ident}.geo.json"), L.geo)
    _png(L.lienzo, os.path.join(carpeta, f"{ident}.png"))
    brilla = mascara is not None
    if brilla:
        m = Image.frombytes("RGBA", (mascara.ancho, mascara.alto), bytes(mascara.px))
        a = np.array(m)
        a[a[..., 3] > 0, 3] = 255
        Image.fromarray(a).save(os.path.join(carpeta, f"{ident}_glowmask.png"))
    tex = Image.frombytes("RGBA", (L.lienzo.ancho, L.lienzo.alto), bytes(L.lienzo.px))
    mura, brillo = manchar_de_mura(tex, sem=hash(ident) % 97)
    ma, ta = np.array(mura), np.array(tex)
    ma[..., 3] = ta[..., 3]                              # lo transparente sigue transparente
    Image.fromarray(ma).save(os.path.join(carpeta, f"{ident}_mura.png"))
    bm = np.array(brillo)
    bm[ta[..., 3] == 0] = 0
    Image.fromarray(bm).save(os.path.join(carpeta, f"{ident}_mura_glowmask.png"))
    # las animaciones
    anims, ambientes = {}, []
    golpe = 0.4
    for clave, tabla, bucle in (("caminar", CAMINAR, True), ("correr", CORRER, True), ("atacar", ATACAR, False)):
        g, f = _grupo(tabla, ident)
        if f is None:
            continue
        largo, pose_en = f(L)
        datos, _ = animar.hornear(L.rig, clave, largo, pose_en, bucle=bucle)
        anims[clave] = datos
        if clave == "atacar":
            golpe = _golpe(g, ident)
            anims[clave]["animation_length"] = round(largo, 4)
            ataque_largo = largo
    for g, (f, ids) in AMBIENTE.items():
        if ident in ids:
            largo, pose_en = f(L)
            datos, _ = animar.hornear(L.rig, g, largo, pose_en, bucle=True)
            anims[g] = datos
            ambientes.append((g, largo))
    _json(os.path.join(ASSETS, "animations", "entity", "bichos", f"{ident}.animation.json"), animar.exportar(anims, ident))
    _json(os.path.join(DATA, "loot_tables", "entities", f"{ident}.json"), _loot(ident))
    # medidas: la caja de todo el modelo quieto (px -> bloques)
    quads = geckolib.caras_para_vista(L.rig.quads({}))
    todos = np.concatenate([P for P, _ in quads])
    lo, hi = todos.min(axis=0), todos.max(axis=0)
    ancho = float(min(max(hi[0] - lo[0], (hi[2] - lo[2]) * 0.5), 2.5 * 16)) / 16
    alto = float(hi[1] - max(lo[1], 0)) / 16
    vol = ancho * ancho * alto
    conducta = CONDUCTA.get(ident, "PASIVO")
    vida = int(max(4, min(60, round(6 + 20 * vol))))
    dano = round(max(2.0, min(8.0, 1.5 + 4 * vol ** (1 / 3))), 1)
    return {"id": ident, "ancho": round(max(0.3, ancho), 2), "alto": round(max(0.25, alto), 2), "vida": vida, "dano": dano,
            "conducta": conducta, "vuela": ident in VUELAN, "fuego": ident in FUEGO, "brilla": brilla,
            "ataque": "atacar" in anims, "golpe": int(round(golpe * 20)),
            "ataque_largo": int(round((ataque_largo if "atacar" in anims else 0.5) * 20)),
            "correr": "correr" in anims, "ambientes": ambientes, "nombre": b.nombre}


def _java(datos):
    filas = []
    for d in datos:
        amb = ", ".join(f'"{g}"' for g, _ in d["ambientes"])
        largos = ", ".join(str(int(round(l * 20))) for _, l in d["ambientes"])
        filas.append(f'            new Especie("{d["id"]}", {d["ancho"]}f, {d["alto"]}f, {d["vida"]}, {d["dano"]}f, '
                     f'Conducta.{d["conducta"]}, {str(d["vuela"]).lower()}, {str(d["fuego"]).lower()}, {str(d["brilla"]).lower()}, '
                     f'{str(d["ataque"]).lower()}, {d["golpe"]}, {d["ataque_largo"]}, {str(d["correr"]).lower()}, '
                     f'new String[]{{{amb}}}, new int[]{{{largos}}})')
    texto = (
        "package com.mipack.bichos;\n\n"
        "import java.util.List;\n\n"
        "/** Generado por taller/bichos/exportar_bichos.py: no se edita a mano. */\n"
        "public final class BichosDatos {\n"
        "    public enum Conducta { PASIVO, NEUTRAL, HOSTIL, SAGRADO }\n\n"
        "    /** ancho y alto en bloques; golpe y ataqueLargo en ticks; ambientes con su largo en ticks. */\n"
        "    public record Especie(String id, float ancho, float alto, int vida, float dano, Conducta conducta, boolean vuela,\n"
        "                          boolean fuego, boolean brilla, boolean ataque, int golpe, int ataqueLargo, boolean correr,\n"
        "                          String[] ambientes, int[] largos) {\n"
        "    }\n\n"
        "    public static final List<Especie> TODAS = List.of(\n" + ",\n".join(filas) + ");\n\n"
        "    private BichosDatos() {\n    }\n}\n")
    os.makedirs(os.path.dirname(JAVA), exist_ok=True)
    with open(JAVA, "w", encoding="utf-8") as f:
        f.write(texto)


def _lang(datos):
    for idioma in ("es_es", "es_mx", "en_us"):
        ruta = os.path.join(ASSETS, "lang", f"{idioma}.json")
        d = json.load(open(ruta, encoding="utf-8"))
        for b in datos:
            es = b["nombre"].split(" (")[0]
            n = es if idioma != "en_us" else NOMBRE_EN[b["id"]]
            d[f"entity.mipack.{b['id']}"] = n
            d[f"item.mipack.{b['id']}_spawn_egg"] = (f"Huevo de {es.lower()}" if idioma != "en_us" else f"{n} Spawn Egg")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        for b in datos:
            _json(os.path.join(ASSETS, "models", "item", f"{b['id']}_spawn_egg.json"), {"parent": "minecraft:item/template_spawn_egg"})


def main():
    datos = []
    for ident in CATALOGO:
        d = exportar(ident)
        print(f"{ident}: {d['ancho']}x{d['alto']} vida {d['vida']} dano {d['dano']} {d['conducta']} "
              f"anims {'atacar ' if d['ataque'] else ''}{len(d['ambientes'])} ambiente")
        datos.append(d)
    _java(datos)
    _lang(datos)


if __name__ == "__main__":
    main()
