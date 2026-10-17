"""
Personajes modelados a mano: un modulo por personaje (taller/personajes/<id>.py).

Cada modulo define:
    construir() -> taller.kit.Personaje          (obligatorio)
    accesorios() -> list[taller.kit.Objeto]      (opcional: objetos aparte)

Los modulos sin construir() son piezas o datos de otro personaje (ej. pibble_capucha.py, meron_pixelart.py).
puente.py usa estos modulos cuando existen; si no, arma el personaje con el motor generico (sastre.py).
"""

import importlib
import os


def cargar(ident):
    try:
        return importlib.import_module(f"{__name__}.{ident}")
    except ModuleNotFoundError as e:
        if e.name == f"{__name__}.{ident}":
            return None
        raise


def disponibles():
    """Ids de los personajes modelados a mano (los modulos que tienen construir())."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    ids = sorted(n[:-3] for n in os.listdir(aqui) if n.endswith(".py") and not n.startswith("_"))
    return [i for i in ids if hasattr(cargar(i), "construir")]
