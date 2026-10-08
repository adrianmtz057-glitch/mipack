"""
Sacerdote del desierto. Estilo Minecraft serio, hecho a mano con el kit.

Capucha blanca que cae, diadema dorada, rastas con anillos dorados, perilla, collar ancho,
pecho descubierto, manto blanco sobre los hombros (mas largo del lado izquierdo), faja oscura,
panel frontal oscuro con triangulos y sol dorados, falda blanca con borde anguloso, brazaletes,
muñequeras y sandalias con correas.
"""

from ..kit import Personaje, dibujo, mezclar_pintores, sprite, tonos
from ..pintura import metal
from ..textura import TRANSPARENTE, azar, hex_a_rgba

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
    PPpPPppqqppPPpPP
    PPPpPPPPPPPPpPPP
    PPPPpPPqqPPpPPPP
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


def picos(sem, prof=6, minimo=2, maximo=5, largo=96):
    """Cortes por columna que dejan el borde de la tela en picos triangulares irregulares."""
    out = []
    k = 0
    while len(out) < largo:
        ancho = minimo + int(azar(sem, k, 1) * (maximo - minimo + 1))
        hondo = 1 + int(azar(sem, k, 2) * prof)
        for c in range(ancho):
            mitad = (ancho - 1) / 2
            out.append(round(abs(c - mitad) / max(0.5, mitad) * hondo))
        k += 1
    return out


def pierna_sandalia(t):
    """Piel con correas finas que suben cruzadas (piel visible entre las tiras)."""
    if t.cara == "down":
        return hex_a_rgba(PIEL["s"])
    if t.cara == "up":
        return hex_a_rgba(PIEL["b"])
    h = t.fila_abajo
    if h < 9 and ((t.i + h) % 7 == 0 or (t.i - h) % 7 == 0):
        return hex_a_rgba(CUERO)
    if h == 9:
        return hex_a_rgba(CUERO)
    return hex_a_rgba(PIEL["s"] if t.i in (0, t.tw - 1) else PIEL["b"])


# ---------------------------------------------------------------- construccion

def construir():
    # figura esbelta: cabeza normal (8), torso y piernas mas largos
    p = Personaje("sacerdote", altura=40, torso=(8, 14, 4), brazo=(3.5, 4))
    C, L = p.cuello, p.lh                                # C = cuello (32), L = cintura (18)
    oro = metal(ORO["b"], 3)
    oro_gema = metal(ORO["b"], 4, gema="#B03A2A")

    cabeza = sprite({"north": CARA}, PAL_CARA,
                    base=lambda t: hex_a_rgba(PELO if t.cara != "down" else PIEL["s"]))
    torso = sprite({"north": TORSO}, PAL_TORSO, base=piel_lisa)
    p.cuerpo(cabeza=cabeza, torso=torso, brazo=piel_lisa, pierna=pierna_sandalia, dens=2)

    # ---- capucha: mas chica, cima redondeada, costados que caen a los hombros con borde irregular
    p.caja("Head/capucha", "capucha_arriba", (-5.1, C + 8.0, -4.7), (5.1, C + 8.6, 5.2),
           tela_blanca(oro_abajo=False, semilla=1))
    p.caja("Head/capucha", "capucha_cima", (-4.1, C + 8.6, -3.7), (4.1, C + 9.0, 4.4),
           tela_blanca(oro_abajo=False, semilla=2))
    p.par("Head/capucha", "capucha_lado", (4.4, C - 2.5, -4.4), (5.1, C + 8.0, 5.2),
          tela_blanca(cortes=picos(31, prof=4), oro_abajo=False, semilla=3),
          rot=(0, 0, 7), piv=(4.75, C + 8.0, 0), dens=2)
    p.caja("Head/capucha", "capucha_atras", (-5.1, C - 3.0, 4.4), (5.1, C + 8.0, 5.2),
           tela_blanca(cortes=picos(32, prof=5), oro_abajo=False, semilla=4), dens=2)
    p.caja("Head/diadema", "diadema_gema", (-0.7, C + 4.9, -4.25), (0.7, C + 6.3, -4.0), oro_gema)

    # ---- rastas irregulares: distinto largo, grosor, angulo y anillos
    rastas = [  # (x, z, fondo relativo al cuello, grosor, giro_z, giro_x, anillos)
        (4.45, -3.6, -10.5, 0.9, 3, 7, 2), (4.15, -2.5, -6.0, 0.7, -3, 5, 1), (3.8, -1.7, -8.5, 0.8, 6, 10, 1),
        (-4.45, -3.6, -8.0, 0.8, -4, 8, 1), (-4.2, -2.4, -11.5, 0.9, 2, 6, 2), (-3.8, -1.6, -6.5, 0.7, -7, 10, 1),
    ]
    for k, (x, z, fondo, g, rz, rx, anillos) in enumerate(rastas):
        h = g / 2
        p.caja("Head/rastas", f"rasta{k}", (x - h, C + fondo, z - h), (x + h, C + 6.5, z + h), rasta(k),
               rot=(rx, 0, rz), piv=(x, C + 6.5, z))
        for a in range(anillos):
            y = C + fondo + 0.8 + a * 3.2
            p.caja("Head/rastas", f"anillo{k}_{a}", (x - h - 0.2, y, z - h - 0.2), (x + h + 0.2, y + 0.7, z + h + 0.2),
                   oro, rot=(rx, 0, rz), piv=(x, C + 6.5, z))
    atras = [(-3.8, -9, 1.0, -3), (-2.4, -13, 0.8, 2), (-1.0, -10, 1.1, -1), (0.6, -14, 0.9, 3), (2.0, -9.5, 1.0, -2),
             (3.5, -12, 0.8, 4)]
    for k, (x, fondo, g, rz) in enumerate(atras):
        h = g / 2
        p.caja("Head/rastas", f"rasta_atras{k}", (x - h, C + fondo, 4.9 - h), (x + h, C - 2.0, 4.9 + h), rasta(k + 6),
               rot=(-5, 0, rz), piv=(x, C - 2.0, 4.9))
        if k % 2 == 0:
            y = C + fondo + 1.0
            p.caja("Head/rastas", f"anillo_atras{k}", (x - h - 0.2, y, 4.7 - h), (x + h + 0.2, y + 0.7, 5.1 + h), oro,
                   rot=(-5, 0, rz), piv=(x, C - 2.0, 4.9))

    # ---- collar ancho dorado con colgantes
    p.caja("Body/collar", "collar", (-4.6, C - 1.7, -2.6), (4.6, C + 0.1, 2.6), oro)
    for k, x in enumerate((-3.0, -1.5, 0.0, 1.5, 3.0)):
        largo = 1.8 if k % 2 == 0 else 1.2
        p.caja("Body/collar", f"colgante{k}", (x - 0.4, C - 1.7 - largo, -2.75), (x + 0.4, C - 1.7, -2.6), oro)

    # ---- manto: hombros cortos, atras hasta los tobillos en 3 paneles con caida distinta y picos
    for lado in (1, -1):
        hueso = "RightArm" if lado > 0 else "LeftArm"
        x1, x2 = sorted((lado * 3.6, lado * 8.4))
        p.caja(f"{hueso}/manto", "manto_hombro", (x1, C - 4.6, -2.7), (x2, C + 0.7, 2.7),
               tela_blanca(cortes=picos(40 + lado, prof=3), semilla=5), rot=(0, 0, -8 * lado),
               piv=(lado * 3.8, C + 0.7, 0), dens=2)
    paneles = [(-5.3, -2.3, 1.0, 3, -7), (-2.6, 2.6, 0.5, 0, -4), (2.3, 5.3, 2.0, -3, -6)]
    for k, (x1, x2, fondo, rz, rx) in enumerate(paneles):
        p.caja("Body/manto", f"manto_atras{k}", (x1, fondo, 2.4 + k * 0.05), (x2, C + 0.8, 3.0 + k * 0.05),
               tela_blanca(cortes=picos(50 + k, prof=7), oro_lados=(k != 1), semilla=6 + k), rot=(rx, 0, rz),
               piv=((x1 + x2) / 2, C + 0.8, 2.6), dens=2)
    # caida larga del lado izquierdo, por delante, hasta los tobillos
    p.caja("Body/manto", "caida_oscura", (-7.2, 2.5, -2.85), (-3.8, C - 2.0, -2.45),
           tela_oscura(1, picos(60, prof=5)), rot=(0, 0, 3), piv=(-5.5, C - 2.0, -2.6), dens=2)
    p.caja("Body/manto", "caida", (-7.6, 1.2, -3.25), (-4.4, C + 0.5, -2.85),
           tela_blanca(cortes=picos(61, prof=8), oro_lados=True, semilla=9), rot=(0, 0, 4),
           piv=(-6.0, C + 0.5, -3.0), dens=2)
    # estola interior
    p.caja("Body/manto", "estola", (-4.4, L - 9, -3.05), (-2.4, C - 0.5, -2.7),
           tela_blanca(cortes=picos(62, prof=4, minimo=2, maximo=3), oro_lados=True, semilla=10), dens=2)

    # ---- brazaletes y muñequeras doradas
    for lado in (1, -1):
        hueso = "RightArm" if lado > 0 else "LeftArm"
        x1, x2 = sorted((lado * 3.8, lado * 7.7))
        p.caja(f"{hueso}/oro", "brazalete", (x1, C - 6.2, -2.2), (x2, C - 5.2, 2.2), oro)
        x1, x2 = sorted((lado * 3.75, lado * 7.75))
        p.caja(f"{hueso}/oro", "munequera", (x1, C - 11.4, -2.25), (x2, C - 8.6, 2.25),
               mezclar_pintores(sprite({"lados": MUNEQUERA}, {"G": ORO["b"], "g": ORO["s"]}), oro), dens=2)

    # ---- faja oscura, broche y punta colgante
    p.caja("Body/faja", "faja", (-4.75, L - 0.2, -2.75), (4.75, L + 2.0, 2.75), tela_oscura(2))
    p.caja("Body/faja", "broche", (-2.6, L + 0.2, -3.05), (-1.0, L + 1.6, -2.75), oro_gema)
    p.caja("Body/faja", "punta", (-3.4, L - 5, -2.95), (-2.2, L, -2.8), tela_oscura(3, [0, 1, 2, 1]),
           rot=(0, 0, -6), piv=(-2.8, L, -2.9), dens=2)

    # ---- panel frontal oscuro con triangulos y sol dorados (termina en punta, debajo de la rodilla)
    p.caja("Body/panel", "panel", (-2.0, L - 12.5, -3.2), (2.0, L + 0.5, -2.8),
           sprite({"north": PANEL, "south": PANEL}, PAL_PANEL, base=tela_oscura(4)), dens=2,
           rot=(4, 0, 0), piv=(0, L + 0.5, -3))

    # ---- falda blanca en capas con picos (en las piernas)
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = sorted((0, lado * 4.7))
        p.caja(f"{hueso}/falda", "falda", (x1, L * 0.38, -2.7), (x2, L + 0.4, 2.7),
               tela_blanca(cortes=picos(70 + lado, prof=4), semilla=9 + lado), dens=2)
        x1, x2 = sorted((lado * 0.3, lado * 5.0))
        p.caja(f"{hueso}/falda", "falda_capa", (x1, L * 0.5, -3.0), (x2, L + 0.2, -2.75),
               tela_blanca(cortes=picos(72 + lado, prof=6), oro_lados=True, semilla=11), rot=(6, 0, -3 * lado),
               piv=((x1 + x2) / 2, L + 0.2, -2.9), dens=2)
    p.caja("LeftLeg/falda", "falda_oscura", (-5.0, L * 0.3, -2.6), (-4.6, L, 2.6), tela_oscura(5, picos(74, prof=4)),
           rot=(0, 0, -5), piv=(-4.8, L, 0), dens=2)

    # ---- sandalias: suela, tira de los dedos y atadura dorada arriba de las correas
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = sorted((lado * -0.1, lado * 4.2))
        p.caja(f"{hueso}/sandalia", "suela", (x1, 0, -2.8), (x2, 0.45, 2.3), metal(CUERO, 5))
        p.caja(f"{hueso}/sandalia", "tira_dedos", (x1, 0.45, -2.15), (x2, 0.95, -1.4), metal(CUERO, 6))
        p.caja(f"{hueso}/sandalia", "atadura", (x1, 4.5, -2.15), (x2, 5.0, 2.15), oro)
    return p
