"""
puente.py -- Crea personajes 3D estilo Minecraft con un prompt.

    Groq (disenador)  ->  ficha JSON  ->  motor Python (cubos + textura pintada)  ->  .bbmodel

Uso:
    python puente.py "crea a meron"                 # personaje del lore (no gasta Groq)
    python puente.py "meron con armadura de oro"    # variante: Groq modifica la ficha de Meron
    python puente.py "un herrero enano de Thza"     # personaje nuevo: Groq escribe la ficha
    python puente.py --todos                        # genera los personajes de lore/personajes
    python puente.py --ficha mi_ficha.json          # genera desde una ficha escrita a mano

Salida (carpeta 'salida'):
    <nombre>.bbmodel        -> abrir en Blockbench (Archivo > Abrir). Textura ya aplicada.
    <nombre>_vista.png      -> vista previa (necesita: pip install numpy pillow)
    accesorios/             -> los objetos del personaje como modelos aparte (cetro, libro, mochila...)
    figura/<nombre>/        -> avatar listo para el mod Figura (copiar a .minecraft/figura/avatars)

Clave de Groq: variable de entorno GROQ_API_KEY o un archivo groq_key.txt al lado de este script.
"""

import argparse
import json
import os
import sys
import unicodedata

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from taller import ficha as fichas          # noqa: E402
from taller import ia, objetos, personajes, sastre, vista     # noqa: E402

LORE = os.path.join(AQUI, "lore")
PERSONAJES = os.path.join(LORE, "personajes")
SALIDA = os.path.join(AQUI, "salida")

PALABRAS_VACIAS = {"crea", "crear", "creame", "hazme", "haz", "hace", "hacer", "genera", "generar", "dame",
                   "quiero", "a", "al", "el", "la", "los", "las", "un", "una", "de", "del", "modelo", "personaje",
                   "skin", "3d", "por", "favor", "porfa", "porfavor", "y", "me", "nuevo", "otra", "vez"}


def _norm(t):
    return unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()


def lore_personajes():
    out = {}
    if os.path.isdir(PERSONAJES):
        for n in sorted(os.listdir(PERSONAJES)):
            if n.endswith(".json"):
                out[n[:-5]] = os.path.join(PERSONAJES, n)
    return out


def leer_lore():
    ruta = os.path.join(LORE, "mundo.md")
    texto = open(ruta, encoding="utf-8").read() if os.path.exists(ruta) else ""
    resumen = []
    for clave, ruta_p in lore_personajes().items():
        try:
            d = json.load(open(ruta_p, encoding="utf-8"))
            resumen.append(f"- {d.get('nombre', clave)}: {d.get('titulo', '')}. {d.get('descripcion', '')}")
        except (OSError, ValueError):
            pass
    if resumen:
        texto += "\n\nPersonajes ya creados (no los dupliques; usalos de referencia de estilo):\n" + "\n".join(resumen)
    return texto


def detectar(prompt):
    """Devuelve (clave del personaje del lore o None, palabras extra del pedido)."""
    palabras = [w.strip(".,;:!?¡¿\"'") for w in _norm(prompt).split()]
    palabras = [w for w in palabras if w]
    claves = lore_personajes()
    encontrado = next((w for w in palabras if w in claves), None)
    extra = [w for w in palabras if w not in PALABRAS_VACIAS and w != encontrado]
    return encontrado, extra


def exportar_figura(ficha, ruta_bbmodel, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    nombre = fichas.slug(ficha["nombre"])
    with open(ruta_bbmodel, encoding="utf-8") as f:
        datos = f.read()
    with open(os.path.join(carpeta, f"{nombre}.bbmodel"), "w", encoding="utf-8") as f:
        f.write(datos)
    with open(os.path.join(carpeta, "avatar.json"), "w", encoding="utf-8") as f:
        json.dump({"name": ficha["nombre"], "description": ficha.get("titulo", ""),
                   "authors": ["puente.py"]}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(carpeta, "script.lua"), "w", encoding="utf-8") as f:
        f.write("-- Oculta el cuerpo vanilla: el modelo ya trae cuerpo propio\n"
                "vanilla_model.PLAYER:setVisible(false)\n")


def generar(ficha_cruda, guardar_ficha=None, a_mano=True):
    f = fichas.normalizar(ficha_cruda)
    nombre = fichas.slug(f["nombre"])
    f["_id"] = nombre
    os.makedirs(SALIDA, exist_ok=True)
    modulo = personajes.cargar(nombre) if a_mano else None
    if modulo:                                       # personaje modelado a mano (taller/personajes/<id>.py)
        p = modulo.construir()
        p.nombre = p.m.nombre = nombre
        ruta, lienzo, uvs = p.guardar(SALIDA)
        print(f"  Modelo (hecho a mano): {ruta}  ({len(p.m.cubos)} cubos, textura {lienzo.ancho}x{lienzo.alto})")
        exportar_figura(f, ruta, os.path.join(SALIDA, "figura", nombre))
        for obj in getattr(modulo, "accesorios", lambda: [])():
            r_obj, _, _ = obj.guardar(os.path.join(SALIDA, "accesorios"))
            print(f"  Accesorio: {r_obj}")
        return ruta
    if guardar_ficha:
        sin_id = {k: v for k, v in f.items() if not k.startswith("_")}
        with open(guardar_ficha, "w", encoding="utf-8") as fh:
            json.dump(sin_id, fh, ensure_ascii=False, indent=2)
        print(f"  Ficha guardada: {guardar_ficha}  (podes editarla y volver a generar con --ficha)")
    modelo = sastre.construir(f)
    ruta = os.path.join(SALIDA, f"{nombre}.bbmodel")
    lienzo, uvs, _ = modelo.guardar(ruta)
    print(f"  Modelo: {ruta}  ({len(modelo.cubos)} cubos, textura {lienzo.ancho}x{lienzo.alto})")
    png = vista.guardar_vista(modelo, lienzo, uvs, os.path.join(SALIDA, f"{nombre}_vista.png"))
    print(f"  Vista previa: {png}" if png else "  (Sin vista previa: pip install numpy pillow)")
    exportar_figura(f, ruta, os.path.join(SALIDA, "figura", nombre))
    for acc in f["accesorios"]:
        obj = objetos.construir(acc, f"{nombre}_{acc['tipo']}")
        if not obj:
            continue
        carpeta = os.path.join(SALIDA, "accesorios")
        os.makedirs(carpeta, exist_ok=True)
        r_obj = os.path.join(carpeta, f"{nombre}_{acc['tipo']}.bbmodel")
        lz, uv, _ = obj.guardar(r_obj)
        vista.guardar_vista(obj, lz, uv, r_obj[:-8] + "_vista.png", alto_px=360)
        print(f"  Accesorio: {r_obj}")
    return ruta


def main():
    ap = argparse.ArgumentParser(description="Crea personajes 3D estilo Minecraft con un prompt.")
    ap.add_argument("pedido", nargs="*", help="lo que queres crear")
    ap.add_argument("--todos", action="store_true", help="genera todos los personajes de lore/personajes")
    ap.add_argument("--ficha", help="genera desde un archivo de ficha JSON")
    ap.add_argument("--ia", action="store_true", help="usa Groq aunque el personaje ya exista en el lore")
    args = ap.parse_args()

    if args.todos:
        for clave, ruta in lore_personajes().items():
            print(f"\n{clave}:")
            generar(json.load(open(ruta, encoding="utf-8")))
        return
    if args.ficha:
        generar(json.load(open(args.ficha, encoding="utf-8")))
        return

    pedido = " ".join(args.pedido).strip() or input("¿Que personaje queres crear? > ").strip()
    if not pedido:
        return
    clave, extra = detectar(pedido)
    base = json.load(open(lore_personajes()[clave], encoding="utf-8")) if clave else None

    if base and not extra and not args.ia:
        print(f"\nPersonaje del lore: {base['nombre']} (sin Groq; usa --ia para que lo rediseñe)")
        generar(base)
        return

    key = ia.obtener_clave(AQUI)
    if not key:
        sys.exit("Falta la clave de Groq: define GROQ_API_KEY o crea groq_key.txt al lado de puente.py.")
    print("\nDiseñando con Groq" + (f" (variante de {base['nombre']})" if base else "") + "...")
    crudo = ia.disenar(pedido, key, leer_lore(), base)
    if base:
        destino = os.path.join(SALIDA, f"{clave}_variante.json")
        os.makedirs(SALIDA, exist_ok=True)
    else:
        destino = os.path.join(PERSONAJES, fichas.slug(crudo.get("nombre") or pedido) + ".json")
        if os.path.exists(destino):
            destino = destino[:-5] + "_nuevo.json"
    generar(crudo, guardar_ficha=destino, a_mano=False)      # las variantes usan el motor generico


if __name__ == "__main__":
    main()
