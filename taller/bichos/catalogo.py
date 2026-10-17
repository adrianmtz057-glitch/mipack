"""
El catalogo de bichos de Velkia: cada uno con su bioma, el modelo de vanilla en que se basa, su mecanica, lo que
suelta, su cuerpo (cuerpos.py) y, sobre todo, su piel (piel.py): la paleta y las marcas que lo hacen reconocible.

Las mecanicas aqui son el texto de diseno; las programa el motor de bichos del mod (cada una un modulo que se le
pone al bicho). Las "crias" de titanes llevan el nombre de su titan y se dibujan mas grandes (escala).
Los 'animales manchados' (zona de mura) no son un bicho aparte: cualquier bicho tiene su version manchada
(piel.manchar_de_mura) que el mod usa cuando se contagia.
"""

from . import cuerpos as C
from .piel import Piel


class Bicho:
    def __init__(self, ident, nombre, bioma, base, mecanica, suelta, crear):
        self.id, self.nombre, self.bioma, self.base, self.mecanica, self.suelta = ident, nombre, bioma, base, mecanica, suelta
        self.crear = crear


BIOMAS = ("Jardines", "Desierto", "Cañón", "Montañas de terracota", "Volcán", "Zona de mura", "Bioma de sales", "Montañas")
CATALOGO = {}


def bicho(ident, nombre, bioma, base, mecanica, suelta):
    def registrar(f):
        CATALOGO[ident] = Bicho(ident, nombre, bioma, base, mecanica, suelta, f)
        return f
    return registrar


# ====================================================================== Jardines

@bicho("cervatillo_musgo", "Cervatillo de musgo (cría de Aurevan)", "Jardines", "Ciervo",
       "Sigue a quien lleva hojas. Deja semillas que hacen crecer cultivos más rápido.", "Semilla de musgo")
def _():
    p = Piel("#8C6A45", vientre="#E3CFA8", patas="#7A5B3C", pezuna="#3A2A20", hocico="#C9AC86", oreja="#D9A08A",
             cuerno="#6E9A3E", cola="#E8DCC4", sem=11,
             patron=[("pelaje", None, 1, 0.4), ("manchas", "#F1E4C8", 1.5, 0.3, ("cuerpo",), "costados"),
                     ("manchas", "#6E9A3E", 2.0, 1.0, ("cuerpo", "cuello", "cabeza"), "lomo"),
                     ("moteado", "#557E2E", 1, 0.3, ("cuerpo", "cuello"), "lomo")])
    return C.cuadrupedo("cervatillo_musgo", p, cuerpo=(5, 5, 9), pata=(1.5, 7), cuello=(3.2, 2.4, 58), cabeza=(3.4, 3.4, 4),
                        hocico=(2.2, 1.9, 2.0), orejas=("punta", 1.1, 2.4), cuernos=("botones", 0.8, 1.4),
                        cola=("corta", 1.2, 1.5), ojo=(1.4, 1.2, 0.7))


@bicho("pato_estanque", "Pato de estanque", "Jardines", "Pollo",
       "Grazna cuando un hostil entra a los Jardines.", "Plumas, huevos")
def _():
    p = Piel("#8B7A66", vientre="#B9A890", cara="#2F6B4F", pico="#E8B33A", patas="#E58A2E", ala="#7C6C5A",
             punta_ala="#3D5FA8", cola="#3B342E", cresta="#F1EDE4", patron=("plumas", None, 1.4, 0.5),
             donde=("cuerpo", "ala"), sem=12)
    return C.ave("pato_estanque", p, cuerpo=(4.5, 4, 6.5), pata=(0.7, 2), cabeza=(3, 3, 3.2), pico=("ancho", 1.0, 2.0),
                 cola=(3, 1, 2), golilla=None, ojo=(1.0, 1.0, 0.5))


@bicho("liebre_dorada", "Liebre dorada", "Jardines", "Conejo", "Huye en zigzag. Brilla de noche.", "Piel, comida")
def _():
    p = Piel("#D9A84A", vientre="#F2E2B8", patas="#C99A42", oreja="#E9B7A6", hocico="#EBCB8A", cola="#FBF3DE",
             patron=("moteado", "#FFEFB0", 1, 0.25), donde=("cuerpo", "cabeza", "oreja"), brilla=("patron", "ojos"),
             ojo="#3A2410", sem=13)
    return C.cuadrupedo("liebre_dorada", p, cuerpo=(4.5, 4.5, 7), pata=(1.2, 2.6), patas_atras=(1.8, 3.4), cabeza=(3.2, 3.2, 3.4),
                        hocico=(2.0, 1.6, 1.2), orejas=("larga", 1.2, 5.0), cola=("corta", 1.8, 1.4), ojo=(1.1, 1.0, 0.65))


# ====================================================================== Desierto

@bicho("toro_arena", "Toro de arena", "Desierto", "Vaca con cuernos de piedra",
       "Embiste en línea recta. Si choca, queda aturdido 3 segundos.", "Cuero, cuerno")
def _():
    p = Piel("#C69B63", vientre="#E3C795", patas="#B3874F", pezuna="#3D2E22", hocico="#E1C08E", cuerno="#8E8A80",
             cola="#9C7446", sem=21,
             patron=[("pelaje", None, 1, 0.4), ("manchas", "#B48A56", 3.5, 0.5, ("cuerpo",), "lomo"),
                     ("placas", None, 1.3, 0.25, ("cuerno",))])
    return C.cuadrupedo("toro_arena", p, cuerpo=(12, 10, 17), pata=(3.4, 8), cabeza=(7, 6, 6), hocico=(5, 3.4, 2.4),
                        orejas=("caida", 1.4, 2.2), cuernos=("toro", 2.2, 7.5), cola=("latigo", 1.0, 9),
                        ojo=(1.4, 1.8, 0.7))


@bicho("escarabajo_sagrado", "Escarabajo sagrado", "Desierto", "Escarabajo",
       "Rueda una bola de arena. Si la rompes, suelta un objeto aleatorio.", "Caparazón")
def _():
    p = Piel("#1E2A30", patas="#18211F", cara="#22333A",
             extras={"caparazon": "#2B6F77", "bola": "#D6B57A"}, ojo="#E9C46A", sem=22,
             patron=[("placas", None, 2.2, 0.2, ("caparazon",)), ("moteado", "#B8955C", 1, 0.4, ("bola",))])
    return C.insecto("escarabajo_sagrado", p, tipo="escarabajo", cuerpo=(5, 2.4, 6), pata=(0.6, 3.6), cabeza=(3, 1.5, 2),
                     antenas=0.8, bola=4.5)


@bicho("fenec", "Fénec", "Desierto", "Zorro pequeño", "Roba objetos del suelo y huye.", "Piel")
def _():
    p = Piel("#E3C79A", vientre="#F6EDDD", patas="#D9B987", oreja="#E9A9A0", hocico="#F1E3C8", punta_cola="#3A2E26",
             cola="#E0C08E", patron=("pelaje", None, 1, 0.4), mascara=None, sem=23)
    return C.cuadrupedo("fenec", p, cuerpo=(4, 4, 7.5), pata=(1.1, 4), cabeza=(3.4, 3.0, 3.2), hocico=(1.6, 1.4, 2.0),
                        orejas=("larga", 2.2, 4.8), cola=("esponjosa", 2.0, 5.5), ojo=(1.0, 1.1, 0.6))


@bicho("chacal_ceniza", "Chacal de ceniza", "Desierto", "Lobo flaco",
       "Jauría nocturna cerca de la Esfinge. Si matas al líder, los demás huyen.", "Colmillo")
def _():
    p = Piel("#6F6A66", vientre="#B9B2A8", patas="#5B5652", hocico="#8E8780", oreja="#4A4643", cola="#5E5955",
             punta_cola="#2E2B29", patron=("rayas", "#4A4643", 2.6, 0.15), donde=("cuerpo",), ojo="#E0A040",
             brilla=("ojos",), sem=24)
    return C.cuadrupedo("chacal_ceniza", p, cuerpo=(4.5, 5, 11), pata=(1.4, 7), cabeza=(3.5, 3.5, 3.5),
                        hocico=(2.0, 1.8, 3.0), orejas=("punta", 1.4, 3.2), cola=("esponjosa", 1.6, 6), ojo=(1.1, 1.2, 0.55))


@bicho("dromedario", "Dromedario", "Desierto", "Llama o camello", "Montura. Va rápido en la arena.", "—")
def _():
    p = Piel("#C4935A", vientre="#DDB57F", patas="#B6844F", pezuna="#5A4330", hocico="#D7AE7A", cola="#8E6A42",
             extras={"silla": "#2F4E8C"}, patron=("pelaje", None, 1, 0.3), donde=("cuerpo", "cuello"), sem=25)
    return C.cuadrupedo("dromedario", p, cuerpo=(9, 9, 15), pata=(2.4, 13), cuello=(8, 3.4, 48), cabeza=(4, 4, 6),
                        hocico=(3.4, 3.0, 2.4), orejas=("punta", 1.0, 1.4), joroba=(7, 5, 7), cola=("latigo", 1.0, 6),
                        silla=(7, 8), ojo=(1.8, 1.2, 0.6))


@bicho("gato_thza", "Gato de Thza", "Desierto", "Gato", "Domable. Ahuyenta a las pesadillas menores.", "—")
def _():
    p = Piel("#C7A57A", vientre="#ECDDC2", patas="#B89670", oreja="#D9958A", hocico="#E6D3B4", cola="#B5926A",
             punta_cola="#3E3126", patron=("manchas", "#5E4A36", 2.0, 0.45), donde=("cuerpo", "cola", "pata"),
             extras={"collar": "#E2B13C"}, ojo="#7CC24A", ojo_brillo="#E9FFD0", ojos_al_frente=True,
             brilla=("ojos",), sem=26)
    return C.cuadrupedo("gato_thza", p, cuerpo=(3.5, 4, 8.5), pata=(1.1, 4), cabeza=(3.4, 3, 3), hocico=(1.6, 1.2, 1.0),
                        orejas=("punta", 1.3, 2.0), cola=("alzada", 0.9, 7), collar=True, ojo=(0.6, 1.2, 0.55))


@bicho("escorpion_luz", "Escorpión de luz", "Desierto", "Araña con cola", "Ralentiza al picar. Brilla de noche.", "Aguijón")
def _():
    p = Piel("#2E2219", patas="#281D15", cola="#2E2219", cuerno="#FFE08A", cara="#382A1C",
             patron=("grietas", "#F6C760", 3.2, 0.0), donde=("cuerpo", "cola", "pinza", "cabeza"),
             brilla=("patron", "aguijon", "ojos"), ojo="#FFD97A", sem=27)
    return C.insecto("escorpion_luz", p, tipo="escorpion", cuerpo=(5, 2, 7), pata=(0.6, 3.4), cabeza=(3, 1.6, 2),
                     pinzas=(1.6, 4.0), aguijon=(1.2, 8.0), antenas=0)


@bicho("buitre", "Buitre", "Desierto", "Ave grande", "Vuela en círculos sobre quien tiene poca vida.", "Plumas")
def _():
    p = Piel("#3A3029", vientre="#4A3E35", cara="#C98472", pico="#D9CDB0", patas="#8C8580", ala="#33291F",
             punta_ala="#1F1914", cola="#2A221C", cresta="#E8E0D2", patron=("plumas", None, 1.6, 0.5),
             donde=("cuerpo", "ala"), sem=28)
    return C.ave("buitre", p, cuerpo=(7, 7, 9), pata=(1.2, 4), cabeza=(3, 3, 3.5), cuello=(3, 2, 62), pico=("gancho", 1.4, 2.6),
                 cola=(4, 1, 4.5), calvo=True, golilla=True, ojo=(1.0, 1.1, 0.55))


@bicho("ballenato_duna", "Ballenato de duna (cría de Zharvak)", "Desierto", "Pez grande",
       "Sale de la arena, traga lo que hay encima y se vuelve a hundir.", "Grasa")
def _():
    p = Piel("#C8A46E", vientre="#EAD8B0", cara="#C29C66", hocico="#E8D2A6", ala="#B89260", cola="#B48C5A",
             patron=[("dunas", "#B48C58", 4.5, 0.05, ("cuerpo", "cabeza", "cola"), "lomo"),
                     ("moteado", "#E9D6AA", 1, 0.12, ("cuerpo", "cabeza"), "lomo")], nariz=None, sem=29)
    return C.pez("ballenato_duna", p, cuerpo=(12, 10, 20), cabeza=(11, 9, 7), cola=(14, 1.5, 7), aletas=(7, 0.8, 4),
                 aleta_dorsal=(1.0, 2.0, 4.0), escala=2.0, ojo=(1.6, 3.0, 0.8))


@bicho("cangrejo", "Cangrejo", "Desierto", "Cangrejo", "Pellizca si lo pisas (en la orilla).", "Comida")
def _():
    p = Piel("#C8623A", patas="#B2532F", cara="#C8623A", extras={"caparazon": "#D9744A"},
             patron=("placas", None, 1.8, 0.2), donde=("caparazon",), ojo="#1A1210", sem=30)
    return C.insecto("cangrejo", p, tipo="cangrejo", cuerpo=(6, 2, 5), pata=(0.6, 3.2), cabeza=(2.2, 1.2, 0.8),
                     pinzas=(1.6, 3.4), antenas=1.0)


# ====================================================================== Cañón

@bicho("babuino", "Babuino", "Cañón", "Mono", "Trepa las paredes y roba comida. Si le tiras dátiles, la devuelve.", "—")
def _():
    p = Piel("#8A7A52", vientre="#A69670", patas="#76684A", cara="#4A4440", hocico="#57504B", oreja="#3E3935",
             cola="#7A6B48", patron=("pelaje", None, 1, 0.5), extras={"melena": "#9C8A5E"}, ojos_al_frente=True,
             ojo="#C98A2E", sem=31)
    return C.cuadrupedo("babuino", p, cuerpo=(5.5, 6, 9), pata=(1.6, 7), patas_atras=(1.8, 5), cabeza=(3.8, 3.6, 3.4),
                        hocico=(2.4, 2.2, 3.0), orejas=("redonda", 1.0, 1.2), cola=("alzada", 1.0, 6),
                        melena=(6.5, 1.4, 4), ojo=(0.8, 1.2, 0.55))


@bicho("ibis", "Ibis", "Cañón", "Garza", "Alza el vuelo cuando se acerca algo hostil.", "Plumas")
def _():
    p = Piel("#EDE8DF", vientre="#F6F2EA", cara="#25211E", pico="#25211E", patas="#2B2724", ala="#E4DED3",
             punta_ala="#25211E", cola="#25211E", patron=("plumas", None, 1.4, 0.4), donde=("cuerpo", "ala"),
             extras={"cuello": "#25211E"}, sem=32)
    return C.ave("ibis", p, cuerpo=(4.5, 4.5, 7), pata=(0.7, 6), cuello=(5, 1.6, 62), cabeza=(2.4, 2.4, 2.6),
                 pico=("curvo", 0.8, 5), cola=(3.5, 1, 3.5), ojo=(0.8, 0.9, 0.45))


@bicho("hipopotamo", "Hipopótamo", "Cañón", "Cerdo grande", "Pacífico en tierra, agresivo en el agua.", "Carne")
def _():
    p = Piel("#7E6E78", vientre="#C9A0A0", patas="#6E5F68", hocico="#9A8088", oreja="#C9A0A0", cara="#7E6E78",
             cola="#6E5F68", nariz="#3A2E33", patron=("moteado", "#6A5A64", 1, 0.15), sem=33)
    return C.cuadrupedo("hipopotamo", p, cuerpo=(13, 11, 18), pata=(4, 5), cabeza=(9, 7, 7), hocico=(8, 5, 4),
                        orejas=("redonda", 1.5, 1.5), cola=("corta", 1.2, 2), panza=1.0, ojo=(1.2, 1.0, 0.7))


@bicho("cocodrilo_luz", "Cocodrilo de luz", "Cañón", "Lagarto grande", "Acecha en la orilla y arrastra al agua.", "Escamas")
def _():
    p = Piel("#3E4A33", vientre="#9A9A70", patas="#36412C", hocico="#46523A", cola="#3A4530", cresta="#2F3926",
             patron=("manchas", "#7CF0D0", 2.2, 0.15), donde=("cuerpo", "cola", "cresta"), brilla=("patron", "ojos"),
             ojo="#F2E06A", nariz=None, sem=34)
    return C.reptil("cocodrilo_luz", p, cuerpo=(8, 4.5, 16), pata=(2.2, 4), cabeza=(6, 3.2, 6), hocico=(4.4, 2.4, 6),
                    cola=(5, 22), cresta=(2, 0.8), ojo=(1.6, 0.5, 0.6))


@bicho("serpiente_rio_seco", "Serpiente río-seco", "Cañón", "Serpiente", "Se esconde en lechos secos.", "Piel")
def _():
    p = Piel("#B89A6A", vientre="#E3D3AE", cara="#A88A5C", hocico="#B89A6A", cola="#9E8358",
             patron=("rombos", "#5E4630", 2.2, 0.5), donde=("cuerpo", "cabeza", "cola"), nariz=None, ojo="#1C140C", sem=35)
    return C.serpiente("serpiente_rio_seco", p, tramos=9, grosor=2.2, largo_tramo=3.4, cabeza=(3.0, 2.0, 3.8))


@bicho("cria_varkhum", "Cría de Varkhum", "Cañón", "Serpiente grande",
       "Se enrosca en las paredes y cae sobre quien pasa.", "Escamas")
def _():
    p = Piel("#4E6B3A", vientre="#D9C46A", cara="#4A6536", hocico="#4E6B3A", cola="#435D32",
             patron=("manchas", "#22301C", 3.2, 0.55), donde=("cuerpo", "cabeza", "cola"), nariz=None, ojo="#E2C64A",
             sem=36)
    return C.serpiente("cria_varkhum", p, tramos=10, grosor=4.5, largo_tramo=5.0, cabeza=(5.4, 3.6, 6.0), escala=1.5,
                       ojo=(1.8, 1.0, 0.7))


@bicho("cria_moruvahn", "Cría de Moruvahn", "Cañón", "Ajolote", "Sale del río de noche. Se regenera si vuelve al agua.", "Branquia")
def _():
    p = Piel("#B98884", vientre="#D9AFA6", patas="#AD7C78", cara="#C49490", cola="#AD7C78", cresta="#FF7A6B",
             patron=("moteado", "#7E5652", 1, 0.3), donde=("cuerpo", "cabeza", "cola"), brilla=("cresta", "ojos"),
             ojo="#1A1016", nariz=None, sem=37)
    return C.reptil("cria_moruvahn", p, cuerpo=(4, 2.4, 7.5), pata=(1.0, 2.0), cabeza=(4.2, 2.2, 3.2), hocico=None,
                    cola=(2.2, 7), agallas=(0.6, 2.2), aleta_cola=True, ojo=(1.0, 0.5, 0.5))


# ====================================================================== Montañas de terracota

@bicho("ramita", "Ramita (cría de Khezar)", "Montañas de terracota", "Insecto palo",
       "Inmóvil hasta que pasas cerca. Parece roca.", "Quitina")
def _():
    p = Piel("#A0603F", patas="#8E5436", cara="#A0603F", patron=("placas", None, 1.6, 0.3),
             donde=("cuerpo", "pata", "cabeza"), ojo="#2A1A12", sem=41)
    return C.insecto("ramita", p, tipo="palo", cuerpo=(1.6, 1.6, 14), pata=(0.5, 6), cabeza=(1.6, 1.4, 1.6), antenas=3.0,
                     ojo=(0.5, 0.4, 0.35))


@bicho("bufalo_terracota", "Búfalo de terracota", "Montañas de terracota", "Vaca grande",
       "Va en manada. Si golpeas a uno, cargan todos.", "Cuero, carne")
def _():
    p = Piel("#7A3F2A", vientre="#8E5038", patas="#5E2F20", pezuna="#2A1A14", hocico="#4A2A1E", cuerno="#C9BFAE",
             cola="#5E2F20", extras={"melena": "#5E2F20"}, patron=("pelaje", None, 1, 0.5),
             donde=("cuerpo", "melena", "cabeza"), sem=42)
    return C.cuadrupedo("bufalo_terracota", p, cuerpo=(12, 11, 18), pata=(3.4, 8), cabeza=(7, 6, 5.5), hocico=(5, 3.4, 2.0),
                        orejas=("caida", 1.4, 2.0), cuernos=("bufalo", 1.6, 7.0), cola=("latigo", 1.0, 8),
                        melena=(13, 2.0, 8), ojo=(1.4, 1.8, 0.7))


@bicho("lagarto_roca", "Lagarto de roca", "Montañas de terracota", "Lagartija",
       "Trepa. Si lo golpeas, suelta la cola y huye.", "Cola")
def _():
    p = Piel("#9A7A62", vientre="#C9AE92", patas="#8A6C56", hocico="#A58670", cola="#8A6C56",
             patron=("escamas", None, 1.2, 0.5), donde=("cuerpo", "cola", "cabeza"), nariz=None, ojo="#2A1A10", sem=43)
    return C.reptil("lagarto_roca", p, cuerpo=(3.5, 2, 7), pata=(1.0, 2.0), cabeza=(2.8, 1.8, 3), hocico=(1.8, 1.2, 1.5),
                    cola=(1.6, 9), ojo=(1.0, 0.5, 0.45))


@bicho("halcon_cobre", "Halcón de cobre", "Montañas de terracota", "Ave", "Se lanza en picada y te roba un objeto.", "Plumas")
def _():
    p = Piel("#B8693A", vientre="#E9D2B0", cara="#B8693A", pico="#3A3A3A", patas="#E2B33A", ala="#A65C30",
             punta_ala="#4E9A86", cola="#8E4E28", patron=("plumas", None, 1.3, 0.5), donde=("cuerpo", "ala"),
             mascara=("#5A3220", 0.45), ojo="#1A1010", sem=44)
    return C.ave("halcon_cobre", p, cuerpo=(4, 4, 6.5), pata=(0.8, 2.5), cabeza=(3, 3, 3), pico=("gancho", 1.0, 1.6),
                 cola=(2.8, 1, 4), ojo=(0.9, 1.0, 0.55))


# ====================================================================== Volcán

@bicho("salamandra_ceniza", "Salamandra de ceniza", "Volcán", "Lagartija",
       "Nada en la lava y escupe brasas.", "Ingrediente de resistencia al fuego")
def _():
    p = Piel("#262220", vientre="#5A2A1E", patas="#221E1C", hocico="#2E2926", cola="#262220",
             patron=("manchas", "#FF8A2A", 1.8, 0.45), donde=("cuerpo", "cola", "cabeza", "pata"),
             brilla=("patron", "ojos"), ojo="#FFB040", nariz=None, sem=51)
    return C.reptil("salamandra_ceniza", p, cuerpo=(4, 2.4, 8), pata=(1.1, 2.4), cabeza=(3.2, 2, 3), hocico=(2, 1.3, 1.4),
                    cola=(2, 9), ojo=(1.0, 0.5, 0.5))


@bicho("escarabajo_brasa", "Escarabajo de brasa", "Volcán", "Escarabajo", "Explota en chispas al morir.", "Ceniza")
def _():
    p = Piel("#1E1A18", patas="#1A1614", cara="#2A2420", cuerno="#3A302A", extras={"caparazon": "#2A2522"},
             patron=("grietas", "#FF6A1F", 1.6, 0.3), donde=("caparazon", "cuerno"), brilla=("patron", "ojos"),
             ojo="#FF9A40", sem=52)
    return C.insecto("escarabajo_brasa", p, tipo="escarabajo", cuerpo=(5, 2.5, 6), pata=(0.6, 3.6), cabeza=(3, 1.6, 2),
                     cuerno=2.2, antenas=0.8)


@bicho("lobo_fuego", "Lobo de fuego (cría de Ezzor)", "Volcán", "Lobo",
       "Solo aparece después del evento de Crakatos. Caza en manada.", "Brasa")
def _():
    p = Piel("#3A3533", vientre="#4A4240", patas="#2E2A28", hocico="#4A4442", oreja="#FF7A2A", cola="#3A3533",
             punta_cola="#FFB347", patron=("grietas", "#FF7A2A", 2.2, 0.25), donde=("cuerpo", "cabeza", "pata", "cola"),
             brilla=("patron", "ojos", "punta_cola"), ojo="#FFD24A", sem=53)
    return C.cuadrupedo("lobo_fuego", p, cuerpo=(6, 6, 12), pata=(2, 7), cabeza=(5, 4.5, 4.5), hocico=(2.6, 2.2, 3.0),
                        orejas=("punta", 1.6, 2.6), cola=("esponjosa", 2.0, 7), ojo=(1.2, 1.4, 0.6))


# ====================================================================== Zona de mura

@bicho("cuervo_negro", "Cuervo negro", "Zona de mura", "Ave", "Si te sigue, aparecen más pesadillas.", "Pluma negra")
def _():
    p = Piel("#1E1B22", vientre="#26222B", cara="#1E1B22", pico="#2A2630", patas="#2A2630", ala="#231F29",
             punta_ala="#3A2E4A", cola="#191620", patron=("plumas", None, 1.3, 0.5), donde=("cuerpo", "ala"),
             ojo="#D9B8FF", ojo_brillo="#FFFFFF", brilla=("ojos",), sem=61)
    return C.ave("cuervo_negro", p, cuerpo=(4.5, 4.5, 7), pata=(0.8, 3), cabeza=(3.2, 3.2, 3.4), pico=("corto", 1.4, 2.4),
                 cola=(3, 1, 4), ojo=(1.0, 1.1, 0.55))


@bicho("murcielago_mura", "Murciélago de mura", "Zona de mura", "Murciélago", "Ataca en grupo y aplica wither leve.", "Mura")
def _():
    p = Piel("#2A1F33", ala="#4A2E5A", oreja="#5A3A6A", patas="#1E1626", cara="#2A1F33",
             patron=("grietas", "#E05ADB", 1.6, 0.2), donde=("membrana",), brilla=("patron", "ojos"),
             ojo="#FF6AF0", sem=62)
    return C.murcielago("murcielago_mura", p, cuerpo=(3, 3.5, 3), cabeza=(3, 3, 2.5), envergadura=7)


# ====================================================================== Bioma de sales

@bicho("flamenco", "Flamenco", "Bioma de sales", "Ave zancuda",
       "Va en bandada. Si corres, se espanta toda; agachado puedes acercarte.", "Plumas rosas")
def _():
    p = Piel("#E99AA6", vientre="#F2B8C0", cara="#EDA6B0", pico="#2A2024", patas="#E07A8C", ala="#E58C9A",
             punta_ala="#22191C", cola="#D9808E", patron=("plumas", None, 1.4, 0.4), donde=("cuerpo", "ala"),
             extras={"pico1": "#F1E6DA"}, sem=71)
    return C.ave("flamenco", p, cuerpo=(5, 5, 7), pata=(0.7, 10), cuello=(8, 1.5, 72), cabeza=(2.6, 2.6, 2.8),
                 pico=("doblado", 1.2, 3.0), cola=(3, 1, 2.5), ojo=(0.9, 1.0, 0.45))


@bicho("lagartija_blanca", "Lagartija blanca", "Bioma de sales", "Lagartija",
       "Se camufla en la sal. Solo se ve cuando se mueve.", "Sal")
def _():
    p = Piel("#E9E6DF", vientre="#F4F2EC", patas="#DCD7CE", hocico="#E2DED6", cola="#DEDAD2",
             patron=("moteado", "#C9C3B8", 1, 0.35), donde=("cuerpo", "cola", "cabeza"), nariz=None, ojo="#3A3430", sem=72)
    return C.reptil("lagartija_blanca", p, cuerpo=(3, 1.6, 6), pata=(0.8, 1.6), cabeza=(2.2, 1.4, 2.4), hocico=(1.4, 1.0, 1.2),
                    cola=(1.2, 7), ojo=(0.8, 0.4, 0.4))


@bicho("garrapata_sal", "Garrapata de sal", "Bioma de sales", "Insecto pequeño",
       "Se pega al jugador y le baja la comida poco a poco.", "—")
def _():
    p = Piel("#B07A86", patas="#6E4A52", cara="#7E525C", patron=("moteado", "#F0ECE6", 1, 0.45), donde=("cuerpo",),
             ojo="#1A1012", sem=73)
    return C.insecto("garrapata_sal", p, tipo="garrapata", cuerpo=(3, 1.8, 3.4), pata=(0.4, 1.6), cabeza=(1.2, 0.8, 0.8),
                     antenas=0, ojo=(0.3, 0.3, 0.25))


# ====================================================================== Montañas

@bicho("cria_iskarum", "Cría de Iskarum", "Montañas", "Mamut pequeño",
       "Lenta y territorial. Si embiste, hace caer nieve y piedras.", "Pelaje grueso")
def _():
    p = Piel("#D8E4EE", vientre="#C3D0DC", patas="#C9D6E2", pezuna="#4A5868", cara="#D0DDE8", hocico="#4A5868",
             oreja="#B7C6D4", cuerno="#EDE3C9", cola="#C3D0DC", cresta="#9EE6FF", patron=("pelaje", None, 1, 0.6),
             donde=("cuerpo", "cabeza", "pata", "oreja"), brilla=("cresta",), ojo="#1A2028", sem=81)
    return C.cuadrupedo("cria_iskarum", p, cuerpo=(10, 10, 13), pata=(3.4, 6), cabeza=(7, 7, 6), hocico=None,
                        trompa=(2.0, 7.0), colmillos=(1.0, 4.0), orejas=("redonda", 2.4, 3.0), cola=("corta", 1.2, 2.5),
                        joroba=(8, 2.5, 7), cresta=(1.6, 2.0, 6), escala=1.5, ojo=(1.6, 2.0, 0.65))


@bicho("cabra_escarcha", "Cabra de escarcha", "Montañas", "Cabra", "Empuja al vacío. Salta entre riscos.", "Cuerno, lana")
def _():
    p = Piel("#ECEFF2", vientre="#DCE2E8", patas="#D4DAE0", pezuna="#3A4048", hocico="#D9DEE4", oreja="#C9B6B6",
             cuerno="#7C8C9C", cola="#E0E5EA", patron=("pelaje", None, 1, 0.6), sem=82)
    return C.cuadrupedo("cabra_escarcha", p, cuerpo=(6, 6, 10), pata=(1.8, 6), cabeza=(3.6, 3.6, 4), hocico=(2.4, 2.0, 2.0),
                        orejas=("caida", 1.2, 1.8), cuernos=("cabra", 1.2, 5.0), cola=("corta", 1.2, 1.5), ojo=(1.4, 1.3, 0.6))


@bicho("marmota", "Marmota", "Montañas", "Conejo gordo", "Silba cuando hay hostiles cerca.", "Comida")
def _():
    p = Piel("#8A6A48", vientre="#C9A97E", patas="#6E5238", hocico="#D3B892", oreja="#6E5238", cola="#5E452E",
             mascara=("#5A4430", 0.55), patron=("pelaje", None, 1, 0.5), sem=83)
    return C.cuadrupedo("marmota", p, cuerpo=(6, 5, 8), pata=(1.6, 2.2), patas_atras=(1.8, 2.2), cabeza=(4, 3.6, 3.5),
                        hocico=(2.4, 1.8, 1.4), orejas=("redonda", 1.0, 1.0), cola=("esponjosa", 1.6, 3), panza=0.8,
                        ojo=(1.0, 1.2, 0.55))


@bicho("aguila_gris", "Águila gris", "Montañas", "Ave grande",
       "Vuela en círculos sobre las cumbres y baja en picada sobre quien escala.", "Plumas")
def _():
    p = Piel("#6B6E72", vientre="#8A8D90", cara="#DAD9D2", pico="#E8B83A", patas="#E8C24A", ala="#5E6165",
             punta_ala="#3A3C40", cola="#ECEBE6", patron=("plumas", None, 1.6, 0.5), donde=("cuerpo", "ala"), sem=84)
    return C.ave("aguila_gris", p, cuerpo=(6.5, 6, 9), pata=(1.2, 3.5), cabeza=(3.6, 3.6, 4), pico=("gancho", 1.4, 2.6),
                 cola=(4, 1, 5), ojo=(1.0, 1.2, 0.6))
