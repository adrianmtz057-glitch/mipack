"""
Ejemplo de personaje hecho a mano con el kit (guia de estilo, no es del lore).

Muestra: cara dibujada a 16x16 (cabeza con dens=2), flequillo en planos recortados, abrigo por capas
con frente dibujado, capa en plano con borde recortado, cinturon, botas de dos niveles y un volado.
Generar:  python -c "from taller.personajes import _ejemplo; _ejemplo.construir().guardar('salida/ejemplo')"
"""

from ..kit import Personaje, degradado, dibujo, mezclar_pintores, sprite, tonos
from ..pintura import cuero, metal, tela

PIEL = tonos("#8A5A40")
PELO = tonos("#2A2030")
OJOS = tonos("#C83A3A")
ABRIGO = tonos("#3A3448")
ORO = "#E3B04B"

CARA = dibujo("""
    HHHHHHHHHHHHHHHH
    HHLHHHHLHHHHLHHH
    HHHHHHhHHHHHHHHH
    HHhHhHSHhHhHhHHH
    HhSHShShSHShSHhH
    HSShSSSSShSSShSH
    HSSSSSSSSSSSSSSH
    HSBBBSSSSSSBBBSH
    hSSSSSSSSSSSSSSh
    SkkkkSSSSSSkkkkS
    SWIidSSSSSSdiIWS
    SWidkSSSSSSkdiWS
    SsSSSSSssSSSSSsS
    SSSSSSSSSSSSSSSS
    sSSSSSSmmSSSSSSs
    zsSSSSSSSSSSSSsz
""")

PAL_CARA = {"H": PELO["b"], "h": PELO["s"], "L": PELO["l"], "S": PIEL["b"], "s": PIEL["s"], "z": PIEL["s2"],
            "B": PELO["s"], "k": PELO["o"], "W": "#F2EEE8", "I": OJOS["h"], "i": OJOS["b"], "d": OJOS["s2"],
            "m": PIEL["s2"]}

MECHON = dibujo("""
    HHHH
    HHHH
    HHHh
    hHHh
    .Hh.
    .h..
""")


def construir():
    p = Personaje("ejemplo")
    pelo = tela(PELO["b"], bordes=(), pliegues=False)
    cabeza = sprite({"north": CARA}, PAL_CARA,
                    base=lambda t: (tela(PELO["b"], bordes=())(t) if t.cara != "down" else tela(PIEL["s"])(t)))
    p.cuerpo(cabeza=cabeza, torso=tela("#1E1A24", bordes=()), brazo=tela(ABRIGO["b"], bordes=()),
             pierna=tela("#2A2430", bordes=()), mano=tela(PIEL["b"], bordes=()))

    # pelo: casco + mechones en planos recortados delante de la frente
    p.caja("Head/pelo", "casco", (-4.5, 28, -4.5), (4.5, 33, 4.5), pelo, caras=("up", "east", "west", "south"))
    pal_mechon = {"H": PELO["b"], "h": PELO["s"]}
    for k, (x, rot) in enumerate(((-3.5, 15), (-1.5, -5), (0.5, 10), (2.5, -15))):
        p.plano("Head/pelo", f"mechon{k}", (x, 29, -4.6), (x + 2, 32.5, -4.6), sprite({"todas": MECHON}, pal_mechon),
                rot=(0, 0, rot), piv=(x + 1, 32.5, -4.6), dens=2)

    # abrigo: capa de tela un poco mas grande que el torso, frente dibujado con abertura y botones
    frente = dibujo("""
        AAAA..AAAA
        AAAAo.oAAA
        AAAAo.oAAA
        AAAAoGoAAA
        AAAAo.oAAA
        AAAAoGoAAA
        AAAAo.oAAA
        AAAAoGoAAA
        AAAAo.oAAA
        AAAAo.oAAA
        AAAAo.oAAA
        aaaao.oaaa
    """)
    abrigo = mezclar_pintores(sprite({"north": frente}, {"A": ABRIGO["b"], "a": ABRIGO["s"], "o": ABRIGO["o"],
                                                        "G": ORO}),
                              tela(ABRIGO["b"], bordes=()))
    p.caja("Body/abrigo", "abrigo", (-4.5, 11.5, -2.5), (4.5, 24.25, 2.5), abrigo)
    # faldon en paneles que se abren
    faldon = degradado([ABRIGO["b"], ABRIGO["b"], ABRIGO["s"]], contorno=ABRIGO["o"])
    p.par("RightLeg/faldon", "faldon", (0.5, 5, -2.6), (4.6, 12, -2.1), faldon, rot=(8, 0, 0), piv=(2.5, 12, -2.4))
    p.par("RightLeg/faldon", "faldon_lado", (4.1, 5, -2.6), (4.6, 12, 2.6), faldon, rot=(0, 0, 8), piv=(4.4, 12, 0))
    # volado blanco recortado bajo el faldon (plano 2D)
    volado = dibujo("""
        WWWWWWWW
        WwWwWwWw
        W.W.W.W.
    """)
    p.plano_par("RightLeg/faldon", "volado", (0.5, 4.2, -3.6), (4.6, 5.4, -3.6),
                sprite({"todas": volado}, {"W": "#EDEAF2", "w": "#C8C4D0"}), rot=(8, 0, 0), piv=(2.5, 12, -2.4), dens=2)

    # capa: plano detras con borde inferior recortado
    capa = dibujo("""
        CCCCCCCCCC
        CCCCCCCCCC
        CCCCCCCCCC
        CCCCCCCCCC
        CCCCCCCCCC
        CCCCCCCCCC
        cCcCCcCCcC
        cCcCcccCcc
        .c.cc.c.c.
        ...c....c.
    """)
    p.plano("Body/capa", "capa", (-5, 6, 2.8), (5, 24, 2.8),
            sprite({"todas": capa}, {"C": "#7A1E2A", "c": "#5A1420"}), rot=(-6, 0, 0), piv=(0, 24, 2.8))

    # cinturon y botas
    p.caja("Body/cinturon", "cinturon", (-4.75, 11.5, -2.75), (4.75, 13, 2.75), cuero("#3A2A20"))
    p.caja("Body/cinturon", "hebilla", (-1, 11.25, -3), (1, 13.25, -2.75), metal(ORO))
    for lado in (1, -1):
        hueso = "RightLeg" if lado > 0 else "LeftLeg"
        x1, x2 = (0, 4.4) if lado > 0 else (-4.4, 0)
        p.caja(f"{hueso}/bota", "bota", (x1, 0, -2.4), (x2, 4, 2.4), cuero("#2A1E18"))
        p.caja(f"{hueso}/bota", "cana", (x1 - 0.1 * lado, 3.5, -2.7), (x2 + 0.2 * lado, 5, 2.7), cuero("#4A3428"))
    return p
