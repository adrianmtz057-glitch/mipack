"""
Sacerdote del desierto. Estilo Minecraft serio, hecho a mano con el kit.

Capucha blanca que cae, diadema dorada, rastas con anillos dorados, perilla, collar ancho,
pecho descubierto, manto blanco sobre los hombros (mas largo del lado izquierdo), faja oscura,
panel frontal oscuro con triangulos y sol dorados, falda blanca con borde anguloso, brazaletes,
muñequeras y sandalias con correas.
"""

from ..kit import Personaje, dibujo, mezclar_pintores, sprite, tonos
from ..pintura import metal
from ..textura import TRANSPARENTE, hex_a_rgba

PIEL = tonos("#5A3828")
PELO = "#16100E"
BLANCO = tonos("#E6E0D2")
ORO = tonos("#C9A050")
OSCURO = tonos("#2E1E26")
CUERO = "#2A1A14"

# ---------------------------------------------------------------- dibujos (pixel art a mano)

CARA = dibujo("""
    HHHHHHHHHHHHHHHH
    HhHHhHHhHHhHHhHH
    gggggggOOggggggg
    GGGGGGGRRGGGGGGG
    sSSSSSSSSSSSSSSs
    sSSBBBSSSSBBBSSs
    sSkkkkSSSSkkkkSs
    sSWAadSSSSdaAWSs
    sSSsssSSSSsssSSs
    sSSSSSSssSSSSSSs
    sSSSSSSzzSSSSSSs
    sSSSSSbbbbSSSSSs
    sSSSSbSmmSbSSSSs
    zsSSSSSbbSSSSSsz
    zsSSSSbbbbSSSSsz
    zzsSSSSbbSSSSszz
""")
PAL_CARA = {"H": PELO, "h": "#2A201C", "g": ORO["h"], "G": ORO["b"], "O": ORO["h"], "R": "#B03A2A",
            "S": PIEL["b"], "s": PIEL["s"], "z": PIEL["s2"], "B": "#1E1210", "k": "#120A08",
            "W": "#EDE6D8", "A": "#F0B040", "a": "#C07818", "d": "#5A2E0C", "b": "#120C0A", "m": "#4A2018"}

TORSO = dibujo("""
    PPPPPPPPPPPPPPPP
    PPPPPPPPPPPPPPPP
    PPPLPPPPPPPPLPPP
    PPLLLPPPPPPLLLPP
    PLLLLLPppPLLLLLP
    PLLLLLLppLLLLLLP
    PPLLLLPqqPLLLLPP
    PPPPPppqqppPPPPP
    PPpppPPqqPPpppPP
    PPPPPPPqqPPPPPPP
    PPPPPLLqqLLPPPPP
    PPPPLLLqqLLLPPPP
    PPPPPppqqppPPPPP
    PPPPPLLqqLLPPPPP
    PPPPLLLqqLLLPPPP
    PPPPPppqqppPPPPP
    PPPPPLLqqLLPPPPP
    PPPPLLLqqLLLPPPP
    PPPPPppqqppPPPPP
    PPPpPPPqqPPPpPPP
    PPPPpPPPPPPpPPPP
    PPPPPpPPPPpPPPPP
    PPPPPPpPPpPPPPPP
    PPPPPPPppPPPPPPP
""")
PAL_TORSO = {"P": PIEL["b"], "p": PIEL["s"], "q": PIEL["s2"], "L": PIEL["l"]}

PANEL = dibujo("""
    GGGGGGGG
    GdDDDDdG
    GDDGGDDG
    GDGDDGDG
    GGGGGGGG
    GDDDDDDG
    GDDggDDG
    GDgGGgDG
    GDgGGgDG
    GDDggDDG
    GDDDDDDG
    GDDDGDDG
    GDDDGDDG
    GDDDGDDG
    GDDDGDDG
    GdDDGDdG
    .GDDGDG.
    ..GDDG..
    ...GG...
""")
PAL_PANEL = {"G": ORO["b"], "g": ORO["h"], "D": OSCURO["b"], "d": OSCURO["s"]}

PIERNA = dibujo("""
    PPPP
    PPPP
    PPPP
    PPPP
    PPPP
    PPPP
    PPPP
    PPPP
    kPPk
    PkkP
    kPPk
    PkkP
    kPPk
    kkkk
""")

MUNEQUERA = dibujo("""
    GGGG
    GggG
    GGGG
    gGGg
    GGGG
    GggG
""")


# ---------------------------------------------------------------- pintores a mano

def tela_blanca(cortes=None, oro_lados=False, oro_abajo=True, semilla=0, oro_frente=False):
    """Tela blanca: luz arriba, pliegues verticales, borde dorado y borde inferior anguloso
    (cortes = cuantos texeles se recortan abajo en cada columna)."""
    def p(t):
        if oro_frente and t.cara == "north":
            return hex_a_rgba(ORO["b"])
        if t.cara in ("up", "down"):
            return hex_a_rgba(BLANCO["s"] if t.cara == "down" else BLANCO["l"])
        col = t.i
        corte = 0
        if cortes:
            corte = cortes[(col + semilla) % len(cortes)]
            if t.fila_abajo < corte:
                return TRANSPARENTE
        if oro_lados and (col == 0 or col == t.tw - 1):
            return hex_a_rgba(ORO["b"])
        if oro_abajo and t.fila_abajo == corte:
            return hex_a_rgba(ORO["s"])
        if oro_abajo and t.fila_abajo == corte + 1 and (col + semilla) % 3 == 1:
            return hex_a_rgba(ORO["b"])                      # bordado
        k = t.j / max(1, t.th - 1)
        c = BLANCO["l"] if k < 0.12 else (BLANCO["b"] if k < 0.72 else BLANCO["s"])
        if (col + semilla) % 4 == 0 and t.fila_abajo > corte + 2:
            c = BLANCO["s"] if k < 0.72 else BLANCO["s2"]    # pliegue
        return hex_a_rgba(c)
    return p


def tela_oscura(semilla=0, cortes=None):
    def p(t):
        if t.cara in ("up", "down"):
            return hex_a_rgba(OSCURO["s"])
        if cortes and t.fila_abajo < cortes[(t.i + semilla) % len(cortes)]:
            return TRANSPARENTE
        k = t.j / max(1, t.th - 1)
        if (t.i + semilla) % 3 == 0:
            return hex_a_rgba(OSCURO["s"])
        return hex_a_rgba(OSCURO["l"] if k < 0.1 else OSCURO["b"])
    return p


def rasta(semilla=0):
    def p(t):
        if t.cara in ("up", "down"):
            return hex_a_rgba(PELO)
        return hex_a_rgba("#3A2E28" if (t.j + t.i + semilla) % 3 == 0 else PELO)
    return p


def piel_lisa(t):
    if t.cara == "down":
        return hex_a_rgba(PIEL["s"])
    return hex_a_rgba(PIEL["s"] if t.fila_abajo == 0 and t.th > 2 else PIEL["b"])


# ---------------------------------------------------------------- construccion

def construir():
    p = Personaje("sacerdote", altura=34)              # piernas mas largas: figura esbelta
    C, L = p.cuello, p.lh                                # C = cuello (26), L = cintura (14)
    oro = metal(ORO["b"], 3)
    oro_gema = metal(ORO["b"], 4, gema="#B03A2A")

    cabeza = sprite({"north": CARA}, PAL_CARA,
                    base=lambda t: hex_a_rgba(PELO if t.cara != "down" else PIEL["s"]))
    torso = sprite({"north": TORSO}, PAL_TORSO, base=piel_lisa)
    pierna = sprite({"lados": PIERNA}, {"P": PIEL["b"], "k": CUERO}, base=piel_lisa)
    p.cuerpo(cabeza=cabeza, torso=torso, brazo=piel_lisa, pierna=pierna, dens=2)

    # ---- capucha: tela mas ancha que la cabeza, redondeada arriba, que cae a los costados y la espalda
    capu = tela_blanca(oro_abajo=False, semilla=1, oro_frente=True)
    p.caja("Head/capucha", "capucha_arriba", (-5.6, C + 8.0, -4.9), (5.6, C + 8.8, 5.6), capu)
    p.caja("Head/capucha", "capucha_cima", (-4.6, C + 8.8, -4.2), (4.6, C + 9.5, 4.8),
           tela_blanca(oro_abajo=False, semilla=2))
    p.par("Head/capucha", "capucha_lado", (4.9, C - 1.2, -4.6), (5.7, C + 8.0, 5.6),
          tela_blanca(cortes=[0, 1, 2, 1, 3, 0], oro_abajo=False, semilla=3, oro_frente=True),
          rot=(0, 0, -6), piv=(5.3, C + 8.0, 0))
    p.caja("Head/capucha", "capucha_atras", (-5.6, C - 2.0, 4.9), (5.6, C + 8.0, 5.7),
           tela_blanca(cortes=[0, 1, 3, 1, 0, 2], oro_abajo=False, semilla=4))
    # caida de la capucha sobre la espalda
    p.caja("Body/capucha", "capucha_caida", (-4.6, C - 7.0, 2.4), (4.6, C + 0.6, 3.2),
           tela_blanca(cortes=[0, 1, 2, 1, 0, 2, 3, 1, 0], semilla=5), rot=(-6, 0, 0), piv=(0, C + 0.6, 2.4))
    p.caja("Head/diadema", "diadema_gema", (-0.7, C + 4.9, -4.25), (0.7, C + 6.3, -4.0), oro_gema)

    # ---- rastas que salen de la capucha enmarcando la cara y caen sobre el pecho
    for s in (1, -1):
        for k, (x, z, fondo, giro) in enumerate(((4.45, -3.6, C - 9, 3), (4.6, -2.4, C - 7, -2))):
            xx = s * x
            p.caja("Head/rastas", f"rasta_{'d' if s > 0 else 'i'}{k}", (xx - 0.45, fondo, z - 0.45),
                   (xx + 0.45, C + 6.5, z + 0.45), rasta(k), rot=(7, 0, s * giro), piv=(xx, C + 6.5, z))
            for y in (fondo + 1.0, fondo + 4.0):
                p.caja("Head/rastas", f"anillo_{'d' if s > 0 else 'i'}{k}_{int(y)}", (xx - 0.65, y, z - 0.65),
                       (xx + 0.65, y + 0.7, z + 0.65), oro, rot=(7, 0, s * giro), piv=(xx, C + 6.5, z))
    for k, x in enumerate((-3.6, -1.8, 0.0, 1.8, 3.6)):          # por la espalda, salen de abajo de la capucha
        fondo = C - 11 + (k % 2) * 2
        p.caja("Head/rastas", f"rasta_atras{k}", (x - 0.55, fondo, 4.4), (x + 0.55, C - 1.0, 5.4), rasta(k + 4),
               rot=(-5, 0, (k - 2) * 2), piv=(x, C - 1.0, 4.9))

    # ---- collar ancho dorado con colgantes
    p.caja("Body/collar", "collar", (-4.6, C - 1.7, -2.6), (4.6, C + 0.1, 2.6), oro)
    for k, x in enumerate((-3.0, -1.5, 0.0, 1.5, 3.0)):
        largo = 1.8 if k % 2 == 0 else 1.2
        p.caja("Body/collar", f"colgante{k}", (x - 0.4, C - 1.7 - largo, -2.75), (x + 0.4, C - 1.7, -2.6), oro)

    # ---- manto sobre los hombros: derecho corto, izquierdo largo (cae hasta la rodilla)
    p.caja("RightArm/manto", "manto_hombro", (3.6, C - 4.6, -2.7), (8.7, C + 0.7, 2.7),
           tela_blanca(cortes=[0, 2, 1, 3, 1, 0], semilla=5), rot=(0, 0, -8), piv=(4.0, C + 0.7, 0))
    p.caja("LeftArm/manto", "manto_largo", (-8.9, C - 15, -2.8), (-3.4, C + 0.8, 2.8),
           tela_blanca(cortes=[0, 2, 4, 1, 3, 5, 2, 0], oro_lados=True, semilla=6), rot=(0, 0, 6),
           piv=(-4.0, C + 0.8, 0))
    p.caja("Body/manto", "manto_atras", (-5.0, L - 7, 2.4), (5.0, C + 0.8, 3.1),
           tela_blanca(cortes=[0, 2, 1, 4, 2, 0, 3, 1, 2, 5, 1], oro_lados=True, semilla=7), rot=(-5, 0, 0),
           piv=(0, C + 0.8, 2.4))
    # estola que cae por delante del lado izquierdo, con capa oscura debajo
    p.caja("Body/manto", "estola_oscura", (-4.9, L - 7, -2.75), (-2.9, C - 2, -2.3), tela_oscura(1, [0, 2, 1]))
    p.caja("Body/manto", "estola", (-4.5, L - 6, -3.05), (-2.4, C - 0.5, -2.7),
           tela_blanca(cortes=[0, 2, 4, 1], oro_lados=True, semilla=8))

    # ---- brazaletes y muñequeras doradas
    for lado in (1, -1):
        hueso = "RightArm" if lado > 0 else "LeftArm"
        x1, x2 = sorted((lado * 3.8, lado * 8.2))
        p.caja(f"{hueso}/oro", "brazalete", (x1, C - 6.0, -2.2), (x2, C - 5.0, 2.2), oro)
        x1, x2 = sorted((lado * 3.75, lado * 8.25))
        p.caja(f"{hueso}/oro", "munequera", (x1, C - 9.2, -2.25), (x2, C - 6.6, 2.25),
               mezclar_pintores(sprite({"lados": MUNEQUERA}, {"G": ORO["b"], "g": ORO["s"]}), oro), dens=2)

    # ---- faja oscura, broche y punta colgante
    p.caja("Body/faja", "faja", (-4.75, L - 0.2, -2.75), (4.75, L + 2.0, 2.75), tela_oscura(2))
    p.caja("Body/faja", "broche", (-2.6, L + 0.2, -3.05), (-1.0, L + 1.6, -2.75), oro_gema)
    p.caja("Body/faja", "punta", (-3.4, L - 4, -2.95), (-2.2, L, -2.8), tela_oscura(3, [0, 1]), rot=(0, 0, -6),
           piv=(-2.8, L, -2.9))

    # ---- panel frontal oscuro con triangulos y sol dorados (termina en punta)
    p.caja("Body/panel", "panel", (-2.0, L - 9.5, -3.2), (2.0, L + 0.5, -2.8),
           sprite({"north": PANEL, "south": PANEL}, PAL_PANEL, base=tela_oscura(4)), dens=2,
           rot=(4, 0, 0), piv=(0, L + 0.5, -3))

    # ---- falda blanca en capas, borde anguloso (en las piernas)
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = sorted((0, lado * 4.7))
        p.caja(f"{hueso}/falda", "falda", (x1, L * 0.36, -2.7), (x2, L + 0.4, 2.7),
               tela_blanca(cortes=[0, 1, 3, 1, 0, 2], semilla=9 + lado))
    p.caja("RightLeg/falda", "falda_capa", (0.4, L * 0.22, -3.0), (4.9, L + 0.2, -2.75),
           tela_blanca(cortes=[0, 2, 4, 2, 0, 3], oro_lados=True, semilla=11), rot=(6, 0, 0),
           piv=(2.6, L + 0.2, -2.9))
    p.caja("LeftLeg/falda", "falda_oscura", (-5.0, L * 0.25, -2.6), (-4.6, L, 2.6), tela_oscura(5, [0, 2, 1, 3]),
           rot=(0, 0, -5), piv=(-4.8, L, 0))

    # ---- sandalias: suela, tira de los dedos, tobillera y correas finas que suben cruzadas (pintadas en la pierna)
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = sorted((lado * -0.1, lado * 4.2))
        p.caja(f"{hueso}/sandalia", "suela", (x1, 0, -2.7), (x2, 0.5, 2.3), metal(CUERO, 5))
        p.caja(f"{hueso}/sandalia", "tira_dedos", (x1, 0.5, -2.2), (x2, 1.2, -1.2), metal(CUERO, 6))
        p.caja(f"{hueso}/sandalia", "tobillera", (x1, 1.6, -2.15), (x2, 2.2, 2.15), metal(CUERO, 7))
        p.caja(f"{hueso}/sandalia", "correa_oro", (x1, 5.6, -2.2), (x2, 6.1, 2.2), oro)
    return p
