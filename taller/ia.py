"""
Groq como DISENADOR: lee el pedido + el lore y escribe una ficha de personaje (JSON).
No toca coordenadas: elige estilos, colores, prendas y accesorios de la lista del motor.
Usa la API compatible con OpenAI de Groq con urllib (sin instalar nada).
"""

import json
import os
import re
import urllib.error
import urllib.request

from .ficha import ESQUEMA_IA, REFERENCIA_CUERPO

URL = "https://api.groq.com/openai/v1/chat/completions"
# Se prueban en orden; si uno no existe o esta saturado se pasa al siguiente.
MODELOS = [m for m in (os.environ.get("GROQ_MODEL"),
                       "openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b") if m]

SISTEMA = """Eres el disenador de personajes de un servidor de Minecraft. Conviertes un pedido en una FICHA JSON
que un programa transforma en un modelo 3D estilo Minecraft: cuerpo de player normal (Steve) con pelo, ropa y
accesorios en relieve, pintados pixel a pixel.

Reglas de diseno:
- Respeta el lore y las descripciones que te pasen: colores, prendas y personalidad.
- Paleta de 3 a 5 colores principales bien contrastados; usa un color de acento (dorado, turquesa...) en ribetes,
  hebillas, brazaletes y accesorios. Evita que todo sea del mismo tono: la ropa interior (camisa/pantalon) suele ser
  mas oscura que la tunica, o al reves.
- La expresion y el estilo de pelo deben reflejar la personalidad.
- No inventes claves ni valores fuera del esquema. Si algo no existe en la lista, aproximalo con lo que hay o con
  unas pocas 'piezas_libres'.
""" + ESQUEMA_IA + REFERENCIA_CUERPO


def obtener_clave(carpeta: str) -> str | None:
    clave = os.environ.get("GROQ_API_KEY")
    if clave:
        return clave.strip()
    ruta = os.path.join(carpeta, "groq_key.txt")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return f.read().strip() or None
    return None


def extraer_json(texto: str):
    """Saca el primer objeto JSON de una respuesta (aunque venga con texto o ```json alrededor)."""
    if not texto:
        return None
    texto = re.sub(r"```(?:json)?", "", texto)
    ini = texto.find("{")
    while ini != -1:
        prof = 0
        for i in range(ini, len(texto)):
            if texto[i] == "{":
                prof += 1
            elif texto[i] == "}":
                prof -= 1
                if prof == 0:
                    try:
                        return json.loads(texto[ini:i + 1])
                    except json.JSONDecodeError:
                        break
        ini = texto.find("{", ini + 1)
    return None


def _llamar(clave, modelo, mensajes, json_mode=True):
    cuerpo = {"model": modelo, "messages": mensajes, "temperature": 0.7, "max_tokens": 4000}
    if json_mode:
        cuerpo["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(URL, data=json.dumps(cuerpo).encode(), method="POST", headers={
        "Authorization": f"Bearer {clave}", "Content-Type": "application/json", "User-Agent": "puente-velkia/2"})
    with urllib.request.urlopen(req, timeout=90) as r:
        datos = json.loads(r.read().decode())
    return datos["choices"][0]["message"].get("content") or ""


def disenar(pedido: str, clave: str, lore: str = "", base: dict | None = None, registro=print) -> dict:
    """Devuelve la ficha (sin normalizar) que propone la IA."""
    usuario = []
    if lore:
        usuario.append("LORE DEL SERVIDOR:\n" + lore.strip())
    if base:
        usuario.append("FICHA ACTUAL DEL PERSONAJE (modificala segun el pedido, conserva lo demas):\n"
                       + json.dumps(base, ensure_ascii=False))
    usuario.append("PEDIDO: " + pedido)
    mensajes = [{"role": "system", "content": SISTEMA}, {"role": "user", "content": "\n\n".join(usuario)}]

    errores = []
    for modelo in MODELOS:
        for json_mode in (True, False):
            try:
                registro(f"  Groq ({modelo}{', modo JSON' if json_mode else ''})...")
                ficha = extraer_json(_llamar(clave, modelo, mensajes, json_mode))
                if isinstance(ficha, dict) and ficha:
                    return ficha
                errores.append(f"{modelo}: respuesta sin JSON")
            except urllib.error.HTTPError as e:
                detalle = e.read().decode(errors="replace")[:300]
                errores.append(f"{modelo}: HTTP {e.code} {detalle}")
                if e.code in (401, 403):
                    raise RuntimeError("Groq rechazo la clave (401/403). Revisa GROQ_API_KEY o groq_key.txt.")
                if e.code == 400 and json_mode and "json" in detalle.lower():
                    continue                                  # reintenta sin modo JSON
                break                                         # modelo inexistente / limite: siguiente modelo
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
                errores.append(f"{modelo}: {e}")
                break
    raise RuntimeError("Groq no devolvio una ficha valida:\n  " + "\n  ".join(errores))
