"""
Ficha de personaje: la descripcion estructurada que escribe la IA (o vos a mano) y que el
motor convierte en modelo 3D. Este archivo define los valores validos, rellena lo que falte
y corrige lo que la IA invente mal (colores invalidos, estilos que no existen, etc.).
"""

import copy
import json
import re
import unicodedata

from .textura import es_hex

ESTILOS_PELO = ("rizos", "puntas", "lado", "revuelto", "largo", "corto", "ninguno")
EXPRESIONES = ("alegre", "serena", "seria", "traviesa")
LARGOS = ("corta", "media", "larga")
PATRONES = ("liso", "manchas", "paneles", "estrellas", "hojas", "rayas", "cuadros")
ACCESORIOS_CABEZA = ("laurel", "corona", "tiara", "gafas", "plumas", "etiquetas", "flor", "cuernos", "orejas")
EXTRAS = ("libro", "amuletos", "cintas", "emblema", "bolsa", "espada", "baston")
FORMAS_EMBLEMA = ("sol", "luna", "estrella", "hoja", "diamante", "ojo")
MATERIALES = ("tela", "metal", "pelo", "piel", "cuero", "gema", "madera", "hueso")
HUESOS_VALIDOS = ("Head", "Body", "RightArm", "LeftArm", "RightLeg", "LeftLeg")

BASE = {
    "nombre": "Personaje",
    "titulo": "",
    "descripcion": "",
    "brazos": "normal",
    "piel": "#C99B7A",
    "cara": {"ojos": "#4A3020", "expresion": "alegre", "rubor": False, "mascara": None},
    "pelo": {"estilo": "corto", "color": "#2A1D14", "brillo": None, "mechas": None, "volumen": 2},
    "ropa": {
        "camisa": {"color": "#6B6B6B"},
        "pantalon": {"color": "#3A3A4A"},
        "botas": {"color": "#3A2A1E", "ribete": None, "alto": 4},
        "tunica": None,
        "mangas": None,
        "bufanda": None,
        "capa": None,
        "cinturon": None,
        "banda": None,
        "hombreras": None,
        "guantes": None,
        "brazaletes": None,
    },
    "cabeza": [],
    "extras": [],
    "piezas_libres": [],
}

# Descripcion para la IA: se pega tal cual en el prompt de sistema.
ESQUEMA_IA = """
Devuelve SOLO un objeto JSON con esta forma (todas las claves en minusculas, colores en "#RRGGBB"):
{
  "nombre": "Nombre", "titulo": "rol corto", "descripcion": "1-2 frases",
  "brazos": "normal" | "finos",                       // finos = brazos de 3 px (estilo Alex)
  "piel": "#RRGGBB",
  "cara": {"ojos": "#RRGGBB", "expresion": "alegre|serena|seria|traviesa", "rubor": true|false,
           "mascara": null | "#RRGGBB"},              // mascara = rostro cubierto de ese color (solo se ven los ojos)
  "pelo": {"estilo": "rizos|puntas|lado|revuelto|largo|corto|ninguno", "color": "#RRGGBB",
           "brillo": "#RRGGBB" | null, "mechas": "#RRGGBB" | null, "volumen": 1|2|3},
  "ropa": {
    "camisa":   {"color": "#RRGGBB"},                 // ropa interior pegada al cuerpo
    "pantalon": {"color": "#RRGGBB"},
    "botas":    {"color": "#RRGGBB", "ribete": "#RRGGBB"|null, "alto": 3..7},
    "tunica":   null | {"largo": "corta|media|larga", "abierta": true|false,
                        "colores": ["#principal", "#secundario", "#terciario"], "patron": PATRON,
                        "ribete": "#RRGGBB"|null},   // tunica/abrigo/vestido/casaca encima de la camisa
    "mangas":   null | {"color": "#RRGGBB", "color2": "#RRGGBB", "forma": "ajustadas|anchas", "patron": PATRON},
    "bufanda":  null | {"color": "#RRGGBB", "color2": "#RRGGBB", "tamano": "pequena|grande", "colas": true|false},
    "capa":     null | {"color": "#RRGGBB", "color2": "#RRGGBB", "largo": "corta|media|larga",
                        "capucha": true|false, "patron": PATRON},
    "cinturon": null | {"color": "#RRGGBB", "hebilla": "#RRGGBB"},
    "banda":    null | {"color": "#RRGGBB", "detalle": "#RRGGBB"},   // banda cruzada en diagonal al pecho
    "hombreras":null | {"color": "#RRGGBB", "detalle": "#RRGGBB"},
    "guantes":  null | {"color": "#RRGGBB", "detalle": "#RRGGBB"},
    "brazaletes": null | "#RRGGBB"
  },
  "cabeza": [ {"tipo": "laurel|corona|tiara|gafas|plumas|etiquetas|flor|cuernos|orejas",
               "color": "#RRGGBB", "color2": "#RRGGBB", "colores": ["#..", "#.."]} ],
  "extras": [ {"tipo": "libro|amuletos|cintas|emblema|bolsa|espada|baston", "color": "#RRGGBB",
               "color2": "#RRGGBB", "colores": ["#..."], "forma": "sol|luna|estrella|hoja|diamante|ojo"} ],
  "piezas_libres": [ {"hueso": "Head|Body|RightArm|LeftArm|RightLeg|LeftLeg", "nombre": "texto",
                      "desde": [x,y,z], "hasta": [x,y,z], "color": "#RRGGBB",
                      "material": "tela|metal|pelo|piel|cuero|gema|madera|hueso", "simetrica": true|false} ]
}
PATRON = "liso|manchas|paneles|estrellas|hojas|rayas|cuadros".
"""

REFERENCIA_CUERPO = """
Cuerpo base (px de Blockbench, 16 px = 1 bloque, pies en y=0, el frente mira a -Z, la DERECHA del personaje es +X):
  cabeza  x -4..4,  y 24..32, z -4..4      torso x -4..4, y 12..24, z -2..2
  brazo derecho x 4..8 (finos 4..7), y 12..24, z -2..2   brazo izquierdo = espejo en -X
  pierna derecha x 0..4, y 0..12, z -2..2   pierna izquierda = espejo en -X
'piezas_libres' son cubos extra para lo que no exista en la lista (cuernos raros, alas pequenas, cola, joyas...).
Usa pocas (0 a 8), del tamano del cuerpo (1 a 8 px), pegadas a su hueso. Con "simetrica": true se copia al otro lado
(escribe la del lado derecho, +X). Prefiere SIEMPRE las piezas con nombre de la lista antes que piezas_libres.
"""


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "personaje"


def _color(v, defecto):
    if isinstance(v, str) and es_hex(v):
        v = v.strip()
        return v if v.startswith("#") else "#" + v
    return defecto


def _opcion(v, validas, defecto):
    v = slug(v) if isinstance(v, str) else v
    return v if v in validas else defecto


def _num(v, lo, hi, defecto):
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return defecto


def _colores(lista, defecto):
    if isinstance(lista, str):
        lista = [lista]
    out = [_color(c, None) for c in (lista or []) if c]
    out = [c for c in out if c]
    return out or list(defecto)


def normalizar(ficha_in: dict) -> dict:
    """Devuelve una ficha completa y valida a partir de lo que haya (aunque venga incompleta o con errores)."""
    f = copy.deepcopy(BASE)
    src = ficha_in if isinstance(ficha_in, dict) else {}
    for k in ("nombre", "titulo", "descripcion"):
        if isinstance(src.get(k), str) and src[k].strip():
            f[k] = src[k].strip()[:300]
    f["brazos"] = _opcion(src.get("brazos"), ("normal", "finos"), "normal")
    f["piel"] = _color(src.get("piel"), f["piel"])

    cara = src.get("cara") or {}
    f["cara"] = {"ojos": _color(cara.get("ojos"), "#4A3020"),
                 "expresion": _opcion(cara.get("expresion"), EXPRESIONES, "alegre"),
                 "rubor": bool(cara.get("rubor", False)),
                 "mascara": _color(cara.get("mascara"), None)}

    pelo = src.get("pelo") or {}
    f["pelo"] = {"estilo": _opcion(pelo.get("estilo"), ESTILOS_PELO, "corto"),
                 "color": _color(pelo.get("color"), "#2A1D14"),
                 "brillo": _color(pelo.get("brillo"), None),
                 "mechas": _color(pelo.get("mechas"), None),
                 "volumen": int(_num(pelo.get("volumen"), 1, 3, 2))}

    ropa_in = src.get("ropa") or {}
    r = f["ropa"]
    r["camisa"] = {"color": _color((ropa_in.get("camisa") or {}).get("color"), r["camisa"]["color"])}
    r["pantalon"] = {"color": _color((ropa_in.get("pantalon") or {}).get("color"), r["pantalon"]["color"])}
    b = ropa_in.get("botas") or {}
    r["botas"] = {"color": _color(b.get("color"), "#3A2A1E"), "ribete": _color(b.get("ribete"), None),
                  "alto": int(_num(b.get("alto"), 2, 8, 4))}

    t = ropa_in.get("tunica")
    if isinstance(t, dict):
        cols = _colores(t.get("colores") or t.get("color"), ["#8A6A4A"])
        r["tunica"] = {"largo": _opcion(t.get("largo"), LARGOS, "media"), "abierta": bool(t.get("abierta", False)),
                       "colores": cols, "patron": _opcion(t.get("patron"), PATRONES, "liso"),
                       "ribete": _color(t.get("ribete"), None)}
    m = ropa_in.get("mangas")
    if isinstance(m, dict):
        base = r["tunica"]["colores"][0] if r["tunica"] else r["camisa"]["color"]
        c1 = _color(m.get("color"), base)
        r["mangas"] = {"color": c1, "color2": _color(m.get("color2"), c1),
                       "forma": _opcion(m.get("forma"), ("ajustadas", "anchas"), "ajustadas"),
                       "patron": _opcion(m.get("patron"), PATRONES, r["tunica"]["patron"] if r["tunica"] else "liso")}
    bu = ropa_in.get("bufanda")
    if isinstance(bu, dict):
        c1 = _color(bu.get("color"), "#C0392B")
        r["bufanda"] = {"color": c1, "color2": _color(bu.get("color2"), c1),
                        "tamano": _opcion(bu.get("tamano"), ("pequena", "grande"), "pequena"),
                        "colas": bool(bu.get("colas", True))}
    ca = ropa_in.get("capa")
    if isinstance(ca, dict):
        c1 = _color(ca.get("color"), "#6B2A2A")
        r["capa"] = {"color": c1, "color2": _color(ca.get("color2"), c1),
                     "largo": _opcion(ca.get("largo"), LARGOS, "larga"), "capucha": bool(ca.get("capucha", False)),
                     "patron": _opcion(ca.get("patron"), PATRONES, "liso")}
    for clave, d1, d2, k2 in (("cinturon", "#4A3220", "#E3B04B", "hebilla"),
                              ("banda", "#8A2A2A", "#E3B04B", "detalle"),
                              ("hombreras", "#6B4A2A", "#E3B04B", "detalle"),
                              ("guantes", "#5A3A22", "#E3B04B", "detalle")):
        v = ropa_in.get(clave)
        if isinstance(v, dict):
            r[clave] = {"color": _color(v.get("color"), d1), k2: _color(v.get(k2), d2)}
    r["brazaletes"] = _color(ropa_in.get("brazaletes"), None)

    def piezas(lista, validos):
        out = []
        for p in lista or []:
            if isinstance(p, str):
                p = {"tipo": p}
            if not isinstance(p, dict):
                continue
            tipo = _opcion(p.get("tipo"), validos, None)
            if not tipo:
                continue
            q = {"tipo": tipo, "color": _color(p.get("color"), None), "color2": _color(p.get("color2"), None),
                 "colores": _colores(p.get("colores"), []), "forma": _opcion(p.get("forma"), FORMAS_EMBLEMA, "sol")}
            out.append(q)
        return out[:8]

    f["cabeza"] = piezas(src.get("cabeza"), ACCESORIOS_CABEZA)
    f["extras"] = piezas(src.get("extras"), EXTRAS)

    libres = []
    for p in (src.get("piezas_libres") or [])[:12]:
        if not isinstance(p, dict):
            continue
        try:
            d = [float(v) for v in p["desde"]][:3]
            h = [float(v) for v in p["hasta"]][:3]
        except (KeyError, TypeError, ValueError):
            continue
        if len(d) != 3 or len(h) != 3:
            continue
        d = [max(-24, min(48, v)) for v in d]
        h = [max(-24, min(48, v)) for v in h]
        if any(abs(h[i] - d[i]) < 0.25 for i in range(3)):
            continue
        libres.append({"hueso": p.get("hueso") if p.get("hueso") in HUESOS_VALIDOS else "Body",
                       "nombre": slug(p.get("nombre") or "pieza")[:24], "desde": d, "hasta": h,
                       "color": _color(p.get("color"), "#888888"),
                       "material": _opcion(p.get("material"), MATERIALES, "tela"),
                       "simetrica": bool(p.get("simetrica", False))})
    f["piezas_libres"] = libres
    return f


def cargar(ruta: str) -> dict:
    with open(ruta, encoding="utf-8") as fh:
        return normalizar(json.load(fh))
