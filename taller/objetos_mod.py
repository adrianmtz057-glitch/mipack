"""
Los recursos de los objetos de Velkia para el mod: modelos de los objetos, bloques (antorcha de grasa y pedazo de
piramide), texturas que no son iconos (escudos, antorcha, gotas de agua), las armaduras (geo + textura de GeckoLib),
las recetas, las etiquetas, lo que sueltan los bloques y los nombres (es/en).
Uso: python -m taller.objetos_mod   (despues de python -m taller.iconos)
"""

import json
import os

from PIL import Image

from . import armaduras, geckolib
from .textura import hex_a_rgba as hex_

RAIZ = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources")
ASSETS = os.path.join(RAIZ, "assets", "mipack")
DATA = os.path.join(RAIZ, "data")

MATERIALES = ["colmillo", "aguijon", "escamas", "cuerno_piedra", "caparazon", "cola_lagarto", "branquia", "ceniza", "brasa",
              "pluma_negra", "mura", "sal", "semilla_musgo", "grasa", "pelaje_grueso", "quitina", "glandula_salamandra"]
PLANOS = MATERIALES + ["flecha_aguijon", "carne_salada", "pulpa_cactus", "fertilizante_musgo", "runa_pibble", "bomba_brasa",
                       "senuelo_pluma", "cantimplora", "cantimplora_reforzada"]
EN_MANO = ["daga_colmillo", "martillo_cuerno", "varita_revolthir", "varita_correctar"]
PIEZAS = ("casco", "pechera", "pantalon", "botas")
ARMADURAS = [f"{m}_{p}" for m in ("desierto", "plumas", "quitina", "tortuga", "pelaje") for p in PIEZAS
             if not (m == "tortuga" and p == "casco")]
ESCUDOS = ["escudo_escamas", "escudo_caparazon"]

NOMBRES = {  # id: (es, en)
    "colmillo": ("Colmillo de chacal", "Jackal fang"), "aguijon": ("Aguijón de escorpión", "Scorpion stinger"),
    "escamas": ("Escamas de luz", "Glowing scales"), "cuerno_piedra": ("Cuerno de piedra", "Stone horn"),
    "caparazon": ("Caparazón de escarabajo", "Beetle shell"), "cola_lagarto": ("Cola de lagarto", "Lizard tail"),
    "branquia": ("Branquia de Moruvahn", "Moruvahn gill"), "ceniza": ("Ceniza", "Ash"), "brasa": ("Brasa", "Ember"),
    "pluma_negra": ("Pluma negra", "Black feather"), "mura": ("Mura", "Mura"), "sal": ("Sal", "Salt"),
    "semilla_musgo": ("Semilla de musgo", "Moss seed"), "grasa": ("Grasa de ballenato", "Dune whale blubber"),
    "pelaje_grueso": ("Pelaje grueso", "Thick fur"), "quitina": ("Quitina", "Chitin"),
    "glandula_salamandra": ("Glándula de salamandra", "Salamander gland"),
    "daga_colmillo": ("Daga de colmillo", "Fang dagger"), "martillo_cuerno": ("Martillo de cuerno", "Horn hammer"),
    "flecha_aguijon": ("Flecha de aguijón", "Stinger arrow"), "carne_salada": ("Carne salada", "Salted meat"),
    "pulpa_cactus": ("Pulpa de cactus", "Cactus pulp"), "fertilizante_musgo": ("Fertilizante de musgo", "Moss fertilizer"),
    "runa_pibble": ("Runa de Pibble", "Pibble's rune"), "varita_revolthir": ("Varita de Revolthir", "Revolthir's wand"),
    "varita_correctar": ("Varita de Correctar", "Correctar's wand"), "bomba_brasa": ("Bomba de brasa", "Ember bomb"),
    "senuelo_pluma": ("Señuelo de plumas", "Feather lure"), "escudo_escamas": ("Escudo de escamas", "Scale shield"),
    "escudo_caparazon": ("Escudo de caparazón", "Shell shield"), "cantimplora": ("Cantimplora", "Canteen"),
    "cantimplora_reforzada": ("Cantimplora reforzada", "Reinforced canteen"),
    "antorcha_grasa": ("Antorcha de grasa", "Blubber torch"), "pedazo_piramide": ("Pedazo de pirámide", "Pyramid shard"),
}
MAT_NOMBRE = {"desierto": ("del desierto", "Desert"), "plumas": ("de plumas", "Feather"), "quitina": ("de quitina", "Chitin"),
              "tortuga": ("de tortuga", "Turtle"), "pelaje": ("de pelaje", "Fur")}
PIEZA_NOMBRE = {"casco": ("Casco", "Helmet"), "pechera": ("Pechera", "Chestplate"), "pantalon": ("Pantalón", "Leggings"),
                "botas": ("Botas", "Boots")}
for _a in ARMADURAS:
    _m, _p = _a.split("_")
    NOMBRES[_a] = (f"{PIEZA_NOMBRE[_p][0]} {MAT_NOMBRE[_m][0]}", f"{MAT_NOMBRE[_m][1]} {PIEZA_NOMBRE[_p][1]}")

AYUDA = {  # id.ayuda: (es, en)
    "daga_colmillo": ("Rápida; a veces desangra", "Fast; sometimes causes bleeding"),
    "martillo_cuerno": ("Lento y pesado: avienta lejos", "Slow and heavy: knocks far back"),
    "carne_salada": ("Llena mucho y quita el hambre; da un poco de sed", "Very filling and cures Hunger; makes you a bit thirsty"),
    "pulpa_cactus": ("Un trago de agua en el desierto", "A sip of water in the desert"),
    "fertilizante_musgo": ("Hace crecer todo en un cuadro de 3x3", "Grows everything in a 3x3 area"),
    "runa_pibble": ("Te lleva a donde moriste por última vez (se gasta)", "Takes you to where you last died (single use)"),
    "varita_revolthir": ("Caos: lo que golpea recibe un efecto al azar", "Chaos: whatever it hits gets a random effect"),
    "varita_correctar": ("Orden: quita los efectos de lo que golpea; clic derecho, los tuyos",
                         "Order: removes effects from what it hits; right-click for your own"),
    "bomba_brasa": ("Estalla en fuego sin romper bloques", "Bursts into fire without breaking blocks"),
    "senuelo_pluma": ("Los hostiles cercanos se olvidan de ti y van a donde cae", "Nearby hostiles forget you and go where it lands"),
    "escudo_escamas": ("Aguanta mucho más que el de madera", "Lasts much longer than a wooden shield"),
    "escudo_caparazon": ("Ligero: al cubrirte casi no te alentas", "Light: you barely slow down while blocking"),
    "cantimplora": ("Clic derecho mirando agua para llenarla", "Right-click on water to fill it"),
    "pedazo_piramide": ("Clic derecho: hacia dónde queda la pirámide. Colocado: no aparecen hostiles cerca. "
                        "En la mano: el calor sofoca menos",
                        "Right-click: points to the nearest pyramid. Placed: no hostiles spawn nearby. "
                        "Held: the heat smothers you less"),
}
TEXTOS = {  # (es, en)
    "itemGroup.mipack.objetos": ("Velkia: objetos", "Velkia: items"),
    "effect.mipack.sofocacion": ("Sofocación", "Smothering heat"), "effect.mipack.frio": ("Frío", "Cold"),
    "effect.mipack.branquias": ("Branquias", "Gills"),
    "item.minecraft.potion.effect.branquias": ("Poción de branquias", "Potion of Gills"),
    "item.minecraft.splash_potion.effect.branquias": ("Poción arrojadiza de branquias", "Splash Potion of Gills"),
    "item.minecraft.lingering_potion.effect.branquias": ("Poción persistente de branquias", "Lingering Potion of Gills"),
    "item.minecraft.tipped_arrow.effect.branquias": ("Flecha de branquias", "Arrow of Gills"),
    "armadura.mipack.desierto": ("Abierta: no sofoca en el desierto", "Open: doesn't smother you in the desert"),
    "armadura.mipack.plumas": ("Ligereza y caída de pluma (cada pieza suma)", "Lightness and feather fall (each piece adds up)"),
    "armadura.mipack.quitina": ("Ligereza leve (cada pieza suma)", "Slight lightness (each piece adds up)"),
    "armadura.mipack.tortuga": ("Nadas más rápido (cada pieza suma)", "Swim faster (each piece adds up)"),
    "armadura.mipack.pelaje": ("Abriga del frío de las montañas; sofoca mucho en el desierto",
                               "Keeps out the mountain cold; very hot in the desert"),
    "agua.mipack.desmayo": ("Te desmayaste de sed...", "You fainted from thirst..."),
    "agua.mipack.desmayado": ("Te desmayaste de sed...", "You fainted from thirst..."),
    "item.mipack.cantimplora.sorbos": ("Sorbos: %s/%s", "Sips: %s/%s"),
    "item.mipack.runa_pibble.nada": ("La runa no encuentra dónde moriste", "The rune can't find where you died"),
    "item.mipack.pedazo_piramide.nada": ("No sientes ninguna pirámide cerca", "You sense no pyramid nearby"),
    "item.mipack.pedazo_piramide.rumbo": ("La pirámide está a %s bloques al %s", "The pyramid is %s blocks to the %s"),
    "rumbo.mipack.norte": ("norte", "north"), "rumbo.mipack.noreste": ("noreste", "northeast"),
    "rumbo.mipack.este": ("este", "east"), "rumbo.mipack.sureste": ("sureste", "southeast"),
    "rumbo.mipack.sur": ("sur", "south"), "rumbo.mipack.suroeste": ("suroeste", "southwest"),
    "rumbo.mipack.oeste": ("oeste", "west"), "rumbo.mipack.noroeste": ("noroeste", "northwest"),
    "entity.mipack.bomba_brasa": ("Bomba de brasa", "Ember bomb"), "entity.mipack.senuelo_pluma": ("Señuelo de plumas", "Feather lure"),
}


def textos():
    """(es, en): todos los nombres de los objetos (para el lang)."""
    es, en = {}, {}
    for i, (a, b) in NOMBRES.items():
        clave = f"block.mipack.{i}" if i in ("antorcha_grasa",) else f"item.mipack.{i}"
        es[clave], en[clave] = a, b
        if i == "pedazo_piramide":
            es["block.mipack.pedazo_piramide"], en["block.mipack.pedazo_piramide"] = a, b
    es["block.mipack.antorcha_grasa_pared"], en["block.mipack.antorcha_grasa_pared"] = NOMBRES["antorcha_grasa"]
    for i, (a, b) in AYUDA.items():
        es[f"item.mipack.{i}.ayuda"], en[f"item.mipack.{i}.ayuda"] = a, b
    for k, (a, b) in TEXTOS.items():
        es[k], en[k] = a, b
    return es, en


def _json(ruta, d):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ====================================================================== texturas que no son iconos

def _gotas():
    """La barra de agua: gota vacia, llena y media (9x9 cada una)."""
    forma = ["....X....", "...XBX...", "..XBBBX..", "..XBBBX..", ".XBBBBBX.", ".XBWBBBX.", ".XBBBBBX.", "..XBBBX..",
             "...XXX..."]
    im = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    for k, (borde, dentro, brillo) in enumerate((("#1A1C22", "#3A3E48", "#3A3E48"), ("#14305A", "#3FA9F5", "#BFE6FF"),
                                                 ("#14305A", "#3FA9F5", "#BFE6FF"))):
        for y, fila in enumerate(forma):
            for x, ch in enumerate(fila):
                if ch == ".":
                    continue
                if k == 2 and x > 4 and ch != "X":
                    continue                                   # la media: solo la mitad izquierda
                c = {"X": borde, "B": dentro, "W": brillo}[ch]
                im.putpixel((k * 9 + x, y), hex_(c))
    _guardar(im, os.path.join(ASSETS, "textures", "gui", "agua.png"))


def _antorcha():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(6, 16):
        for x in (7, 8):
            if y <= 7:
                c = "#FFE07A" if x == 7 else "#FF9A2E"
            elif y <= 9:
                c = "#FFF4D0" if x == 7 else "#EADBA8"
            else:
                c = "#8A6A44" if x == 7 else "#6B4A2A"
            im.putpixel((x, y), hex_(c))
    _guardar(im, os.path.join(ASSETS, "textures", "block", "antorcha_grasa.png"))


def _escudo(nombre, frente, borde, detalle, atras="#6B4A2A"):
    """Textura del escudo con el modelo del de Minecraft (64x64): el frente en (1,1)-(13,23)."""
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    cf, cb, ca = hex_(frente), hex_(borde), hex_(atras)
    for y in range(0, 24):
        for x in range(0, 27):
            if y == 0 and not (1 <= x < 25):
                continue
            im.putpixel((x, y), cb if (x in (0, 13) or y in (0,) or not 1 <= x < 26) else ca)
    for y in range(1, 23):
        for x in range(1, 13):
            orilla = x in (1, 12) or y in (1, 22)
            im.putpixel((x, y), cb if orilla else detalle(x - 1, y - 1, cf))
    for y in range(0, 12):
        for x in range(26, 42):
            im.putpixel((x, y), hex_("#4A3020") if (x + y) % 3 else hex_("#6B4A2A"))
    _guardar(im, os.path.join(ASSETS, "textures", "entity", "escudo", f"{nombre}.png"))


def _det_escamas(x, y, c):
    fila = y // 2
    cu = ((x + (1 if fila % 2 else 0)) % 3)
    if y % 2 == 1 and cu != 1:
        return hex_("#1E4A34")
    if (x, y) in ((5, 9), (6, 10)):
        return hex_("#7CF0D0")
    return hex_("#4E9466") if cu == 1 and y % 2 == 0 else c


def _det_caparazon(x, y, c):
    if x in (5, 6):
        return hex_("#174147")
    if 2 <= x <= 3 and 3 <= y <= 8:
        return hex_("#56A3A8")
    return c


def _guardar(im, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    im.save(ruta)


# ====================================================================== modelos, recetas, etiquetas

def _modelos():
    m = os.path.join(ASSETS, "models")
    for i in PLANOS + ARMADURAS:
        _json(os.path.join(m, "item", f"{i}.json"), {"parent": "minecraft:item/generated", "textures": {"layer0": f"mipack:item/{i}"}})
    for i in EN_MANO:
        _json(os.path.join(m, "item", f"{i}.json"), {"parent": "minecraft:item/handheld", "textures": {"layer0": f"mipack:item/{i}"}})
    base = os.path.join(os.path.dirname(__file__), "..", "mod", "src", "main", "resources")
    escudo = json.load(open(os.path.join(os.path.dirname(__file__), "plantillas", "shield.json")))
    bloqueo = json.load(open(os.path.join(os.path.dirname(__file__), "plantillas", "shield_blocking.json")))
    for i in ESCUDOS:
        e = dict(escudo)
        e["textures"] = {"particle": f"mipack:item/{i}"}
        e["overrides"] = [{"predicate": {"blocking": 1}, "model": f"mipack:item/{i}_bloqueando"}]
        b = dict(bloqueo)
        b["textures"] = {"particle": f"mipack:item/{i}"}
        _json(os.path.join(m, "item", f"{i}.json"), e)
        _json(os.path.join(m, "item", f"{i}_bloqueando.json"), b)
    # la antorcha
    _json(os.path.join(m, "block", "antorcha_grasa.json"), {"parent": "minecraft:block/template_torch", "textures": {"torch": "mipack:block/antorcha_grasa"}})
    _json(os.path.join(m, "block", "antorcha_grasa_pared.json"), {"parent": "minecraft:block/template_torch_wall", "textures": {"torch": "mipack:block/antorcha_grasa"}})
    _json(os.path.join(m, "item", "antorcha_grasa.json"), {"parent": "minecraft:item/generated", "textures": {"layer0": "mipack:item/antorcha_grasa"}})
    bs = os.path.join(ASSETS, "blockstates")
    _json(os.path.join(bs, "antorcha_grasa.json"), {"variants": {"": {"model": "mipack:block/antorcha_grasa"}}})
    _json(os.path.join(bs, "antorcha_grasa_pared.json"), {"variants": {
        f"facing={f}": ({"model": "mipack:block/antorcha_grasa_pared", "y": y} if y else {"model": "mipack:block/antorcha_grasa_pared"})
        for f, y in (("east", 0), ("north", 270), ("south", 90), ("west", 180))}})
    # el pedazo de piramide: tres escalones de arenisca y la punta de oro
    tex = {"arena": "minecraft:block/sandstone_top", "lado": "minecraft:block/cut_sandstone", "oro": "minecraft:block/gold_block",
           "particle": "minecraft:block/cut_sandstone"}

    def caja(a, b, t, tapa="#arena"):
        caras = {c: {"texture": t} for c in ("north", "south", "east", "west")}
        caras["up"] = {"texture": tapa}
        caras["down"] = {"texture": "#arena"}
        return {"from": a, "to": b, "faces": caras}
    _json(os.path.join(m, "block", "pedazo_piramide.json"), {"parent": "minecraft:block/block", "textures": tex, "elements": [
        caja([1, 0, 1], [15, 5, 15], "#lado"), caja([4, 5, 4], [12, 10, 12], "#lado"),
        caja([6.5, 10, 6.5], [9.5, 14, 9.5], "#oro", "#oro")]})
    _json(os.path.join(m, "item", "pedazo_piramide.json"), {"parent": "minecraft:item/generated", "textures": {"layer0": "mipack:item/pedazo_piramide"}})
    _json(os.path.join(bs, "pedazo_piramide.json"), {"variants": {"": {"model": "mipack:block/pedazo_piramide"}}})
    del base


def _recetas():
    r = os.path.join(DATA, "mipack", "recipes")

    def forma(nombre, patron, claves, cantidad=1, resultado=None):
        _json(os.path.join(r, f"{nombre}.json"), {"type": "minecraft:crafting_shaped", "pattern": patron,
                                                   "key": {k: (v if isinstance(v, (dict, list)) else {"item": v}) for k, v in claves.items()},
                                                   "result": {"item": resultado or f"mipack:{nombre}", "count": cantidad}})

    def sin_forma(nombre, ingredientes, cantidad=1, resultado=None):
        _json(os.path.join(r, f"{nombre}.json"), {"type": "minecraft:crafting_shapeless",
                                                   "ingredients": [i if isinstance(i, (dict, list)) else {"item": i} for i in ingredientes],
                                                   "result": {"item": resultado or f"mipack:{nombre}", "count": cantidad}})
    palo = "minecraft:stick"
    forma("daga_colmillo", ["C", "S"], {"C": "mipack:colmillo", "S": palo})
    forma("martillo_cuerno", ["CCC", " S ", " S "], {"C": "mipack:cuerno_piedra", "S": palo})
    forma("flecha_aguijon", ["A", "S", "F"], {"A": "mipack:aguijon", "S": palo, "F": "minecraft:feather"}, 4)
    sin_forma("carne_salada", ["mipack:sal", [{"item": "minecraft:cooked_beef"}, {"item": "minecraft:cooked_porkchop"},
                                              {"item": "minecraft:cooked_mutton"}, {"item": "minecraft:cooked_chicken"},
                                              {"item": "minecraft:cooked_rabbit"}]])
    sin_forma("pulpa_cactus", ["minecraft:cactus"], 2)
    sin_forma("fertilizante_musgo", ["mipack:semilla_musgo", "minecraft:bone_meal", "minecraft:bone_meal"], 2)
    forma("runa_pibble", ["LGL", "GEG", "LGL"], {"L": "minecraft:lapis_lazuli", "G": "minecraft:gold_ingot", "E": "minecraft:ender_pearl"})
    forma("varita_revolthir", [" AG", " BA", "B  "], {"A": "minecraft:amethyst_shard", "G": "minecraft:glowstone_dust", "B": "minecraft:blaze_rod"})
    forma("varita_correctar", [" PQ", " BP", "B  "], {"P": "minecraft:prismarine_crystals", "Q": "minecraft:quartz", "B": "minecraft:blaze_rod"})
    sin_forma("bomba_brasa", ["mipack:ceniza", "mipack:brasa", "minecraft:gunpowder"], 2)
    sin_forma("senuelo_pluma", ["mipack:pluma_negra", "mipack:pluma_negra", "mipack:pluma_negra", "minecraft:string"])
    forma("escudo_escamas", ["EPE", "EEE", " E "], {"E": "mipack:escamas", "P": {"tag": "minecraft:planks"}})
    forma("escudo_caparazon", ["CPC", "CCC", " C "], {"C": "mipack:caparazon", "P": {"tag": "minecraft:planks"}})
    forma("cantimplora", [" S ", "L L", " L "], {"S": "minecraft:string", "L": "minecraft:leather"})
    sin_forma("cantimplora_reforzada", ["mipack:cantimplora", "mipack:grasa", "mipack:grasa", "minecraft:iron_ingot"])
    forma("antorcha_grasa", ["G", "S"], {"G": "mipack:grasa", "S": palo}, 4)
    forma("pedazo_piramide", [" O ", "SCS", "SSS"], {"O": "minecraft:gold_ingot", "S": "minecraft:cut_sandstone", "C": "minecraft:compass"})
    materiales = {"desierto": "minecraft:cut_sandstone", "plumas": "minecraft:feather", "quitina": "mipack:quitina",
                  "tortuga": "minecraft:scute", "pelaje": "mipack:pelaje_grueso"}
    patrones = {"casco": ["XXX", "X X"], "pechera": ["X X", "XXX", "XXX"], "pantalon": ["XXX", "X X", "X X"], "botas": ["X X", "X X"]}
    for a in ARMADURAS:
        m, p = a.split("_")
        forma(a, patrones[p], {"X": materiales[m]})


def _etiquetas_y_botin():
    _json(os.path.join(DATA, "minecraft", "tags", "items", "arrows.json"), {"replace": False, "values": ["mipack:flecha_aguijon"]})
    _json(os.path.join(DATA, "mipack", "tags", "worldgen", "structure", "piramides.json"), {"replace": False, "values": ["minecraft:desert_pyramid"]})
    _json(os.path.join(DATA, "minecraft", "tags", "blocks", "mineable", "pickaxe.json"), {"replace": False, "values": ["mipack:pedazo_piramide"]})
    for b, objeto in (("antorcha_grasa", "antorcha_grasa"), ("antorcha_grasa_pared", "antorcha_grasa"), ("pedazo_piramide", "pedazo_piramide")):
        _json(os.path.join(DATA, "mipack", "loot_tables", "blocks", f"{b}.json"), {
            "type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"mipack:{objeto}"}],
                                                  "conditions": [{"condition": "minecraft:survives_explosion"}]}]})


def _armaduras():
    for ident in armaduras.ARMADURAS:
        m = armaduras.armar(ident)
        lienzo, uvs = m.pintar()
        geo = geckolib.exportar_geo(m, uvs, lienzo, f"armor_{ident}")
        _json(os.path.join(ASSETS, "geo", "armor", f"{ident}.geo.json"), geo)
        destino = os.path.join(ASSETS, "textures", "armor", f"{ident}.png")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        lienzo.guardar(destino) if hasattr(lienzo, "guardar") else _lienzo_png(lienzo, destino)
        print(ident, "huesos:", sorted(b["name"] for b in geo["minecraft:geometry"][0]["bones"]))
    _json(os.path.join(ASSETS, "animations", "armor", "quieta.animation.json"), {"format_version": "1.8.0", "animations": {}})


def _lienzo_png(lienzo, ruta):
    im = Image.frombytes("RGBA", (lienzo.ancho, lienzo.alto), bytes(lienzo.px))
    im.save(ruta)


def _lang():
    es, en = textos()
    for idioma, d in (("es_es", es), ("es_mx", es), ("en_us", en)):
        ruta = os.path.join(ASSETS, "lang", f"{idioma}.json")
        actual = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
        actual.update(d)
        _json(ruta, actual)


def main():
    _gotas()
    _antorcha()
    _escudo("escudo_escamas", "#2F6A4A", "#6B4A2A", _det_escamas)
    _escudo("escudo_caparazon", "#2B6F77", "#1E2A30", _det_caparazon, atras="#3A4A50")
    _modelos()
    _recetas()
    _etiquetas_y_botin()
    _armaduras()
    _lang()
    print("listo")


if __name__ == "__main__":
    main()
