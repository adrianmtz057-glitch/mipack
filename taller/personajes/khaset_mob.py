"""
Khaset para el mod (GeckoLib): el mismo modelo del avatar (personajes/khaset.py, con sus mallas: ver
geo/FabricaMallas.java en el mod), sin remodelar. Solo cambia:
  - la luz horneada pareja (LUZ_SIMETRICA) y sin sombras entre piezas que se mueven (luz_por = "grupo");
  - el esqueleto: en Figura cabeza, cuerpo, brazos y piernas van sueltos; aqui hay una raiz (en el piso, para
    moverlo entero) y la cintura (en la cadera) que carga el cuerpo, la cabeza y los brazos, asi al encorvarse o
    ponerse en cuatro patas todo lo de arriba va junto.
En el juego se dibuja al triple (ESCALA), parejo de alto y de ancho: el modelo mide 59.6 px (3.7 bloques) y en el
juego unos 11 bloques, como Crackatos; con el brazo estirado barre unos 7 bloques alrededor.
"""

from ..luz import LUZ_SIMETRICA
from . import khaset

ESCALA = 3.0
CADERA = (0.0, 31.5, 3.2)
ARRIBA = ("Body", "Head", "RightArm", "LeftArm")       # lo que carga la cintura
ABAJO = ("RightLeg", "LeftLeg")


def ruta_nueva(ruta):
    raiz = ruta.split("/")[0]
    if raiz in ARRIBA:
        return "raiz/cintura/" + ruta
    if raiz in ABAJO:
        return "raiz/" + ruta
    return "raiz/" + ruta


def construir():
    p = khaset.construir()
    p.m.luz_desde = LUZ_SIMETRICA
    p.m.luz_por = "grupo"
    for e in list(p.m.cubos) + list(p.m.mallas):
        e.hueso = ruta_nueva(e.hueso)
    p.m.pivotes = {ruta_nueva(k): v for k, v in p.m.pivotes.items()}
    p.m.pivotes["raiz"] = (0.0, 0.0, 0.0)
    p.m.pivotes["raiz/cintura"] = CADERA
    return p
