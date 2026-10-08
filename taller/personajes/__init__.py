"""
Personajes modelados a mano: un modulo por personaje (taller/personajes/<id>.py).

Cada modulo define:
    construir() -> taller.kit.Personaje          (obligatorio)
    accesorios() -> list[taller.kit.Objeto]      (opcional: objetos aparte)

puente.py usa estos modulos cuando existen; si no, arma el personaje con el motor generico (sastre.py).
"""

import importlib


def cargar(ident):
    try:
        return importlib.import_module(f"{__name__}.{ident}")
    except ModuleNotFoundError as e:
        if e.name == f"{__name__}.{ident}":
            return None
        raise
