"""
Las animaciones de Crackatos (para GeckoLib), definidas como poses en funcion del tiempo y horneadas a 20 cuadros
por segundo (ver taller/animar.py). Las patas que apoyan van con IK: el pie queda exacto en el piso.
Convenciones del kit: el frente es -Z, su derecha +X. Giro en X positivo levanta lo de adelante (y baja lo de
atras); en Y positivo lo de adelante va a su izquierda (-X) y lo de atras a su derecha.
  quieto          (4.0 s, bucle)  respira, mira despacio, la cola se mece
  caminar         (1.6 s, bucle)  paso pesado en secuencia lateral (pata trasera izq, delantera izq, trasera der,
                                  delantera der), el cuerpo sube y baja y se ladea, la cola ondea
  rascar_piso     (1.5 s)         el aviso de la embestida: baja la cabeza, se echa atras y rasca dos veces con la
                                  pata delantera derecha, la cola se alza
  embestir        (0.6 s, bucle)  galope con la cabeza baja y los cuernos al frente
  chocar          (0.5 s)         se estrella: rebota, la cabeza se clava
  atorado         (1.2 s, bucle)  los cuernos atorados: jala con el cuerpo y tuerce la cabeza
  zafarse         (0.8 s)         se suelta de un jalon y se sacude
  cabezazo        (0.7 s)         avienta para arriba al que embistio
  sacudida        (2.2 s)         se agacha y sacude la cadera; las puas vibran (a 1.6 s salen las puas que caen)
  alzarse_azotar  (2.6 s)         se para en dos patas rugiendo y azota al piso (el golpe a 1.55 s: la ola)
  rugido          (1.8 s)         ruge con la cabeza en alto
  muerte          (2.5 s)         se le doblan las patas y cae
"""

import math

from .. import animar
from ..animar import facil, suave

PATAS = {"dd": ("hombro_dd", "codo_dd", "mano_dd"), "di": ("hombro_di", "codo_di", "mano_di"),
         "td": ("muslo_td", "rodilla_td", "pie_td"), "ti": ("muslo_ti", "rodilla_ti", "pie_ti")}
COLAS = ("cola1", "cola2", "cola3", "cola4", "cola5")
# los momentos que el mod usa (segundos desde que empieza la animacion)
GOLPE_AZOTE = 1.55
SALEN_PUAS = 1.6


class Pose(dict):
    def rot(self, h, rx=0.0, ry=0.0, rz=0.0):
        (ax, ay, az), p = self.get(h, ((0, 0, 0), (0, 0, 0)))
        self[h] = ((ax + rx, ay + ry, az + rz), p)

    def pos(self, h, x=0.0, y=0.0, z=0.0):
        r, (px, py, pz) = self.get(h, ((0, 0, 0), (0, 0, 0)))
        self[h] = (r, (px + x, py + y, pz + z))


def _pie(rig, pata):
    """Donde va el pivote de la muneca o el tobillo de una pata en reposo."""
    return rig.pivote[PATAS[pata][2]]


def _paso(rig, pata, u, zancada, alto, apoyo):
    """Donde va el pie en el ciclo u (0..1): apoyado se va de adelante hacia atras en el piso; en el aire vuelve
    adelante levantandose 'alto'."""
    x, y, z = _pie(rig, pata)
    u %= 1.0
    if u < apoyo:
        f = u / apoyo
        return (x, y, z - zancada / 2 + zancada * f)
    f = (u - apoyo) / (1 - apoyo)
    g = facil(f)
    return (x, y + alto * math.sin(math.pi * f), z + zancada / 2 - zancada * g)


def _plantar(rig, pose, objetivos):
    for pata, obj in objetivos.items():
        animar.ik_pata(rig, pose, PATAS[pata], obj)
    _cola_arriba(rig, pose)


# los puntos mas bajos de cada tramo de la cola (al principio y al final del tramo, abajo, con las rocas) y los de
# la cabeza (la quilla del hocico, la quijada): asi la cola y la cabeza nunca atraviesan el piso
_BAJOS = {}


def _cola_arriba(rig, pose):
    if not _BAJOS:
        from .jefe_piedra import COLA
        tramos = [(COLA[i], COLA[i + 1]) for i in range(4)] + [(COLA[4], COLA[-1])]
        _BAJOS["cola"] = [[(0.0, y - my * 0.7 - 0.8, z) for z, y, mx, my in tramo] for tramo in tramos]
        _BAJOS["cabeza"] = [[(0.0, 16.0, -30.0)], [(0.0, 13.6, -41.4), (0.0, 13.0, -36.0), (0.0, 14.0, -31.0)]]
    animar.sobre_el_piso(rig, pose, COLAS, _BAJOS["cola"])
    animar.sobre_el_piso(rig, pose, ("cuello", "cabeza"), _BAJOS["cabeza"])


def _cola(pose, t, periodo, amplitud, alza=0.0, fase=0.6):
    for i, h in enumerate(COLAS):
        pose.rot(h, alza if i == 0 else alza * 0.3, amplitud * (0.6 + 0.25 * i) * math.sin(2 * math.pi * t / periodo - i * fase))


# ---------------------------------------------------------------- las animaciones

def quieto(rig):
    T = 4.0

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        p.pos("cuerpo", y=0.35 * math.sin(w))
        p.rot("pecho", rx=1.2 * math.sin(w))
        p.rot("cuello", rx=-2.0 + 1.5 * math.sin(w + 0.6))
        p.rot("cabeza", ry=7.0 * math.sin(w), rx=1.5 * math.sin(2 * w))
        _cola(p, t, T, 4.0)
        _plantar(rig, p, {k: _pie(rig, k) for k in PATAS})
        return p
    return T, pose, True


def caminar(rig):
    T, zancada, alto, apoyo = 1.6, 7.0, 3.0, 0.7
    fases = {"ti": 0.0, "di": 0.25, "td": 0.5, "dd": 0.75}

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        p.pos("cuerpo", y=-0.4 + 0.4 * math.cos(2 * w))
        p.rot("cuerpo", rz=1.5 * math.sin(w))
        p.rot("pecho", ry=2.0 * math.sin(w))
        p.rot("cadera", ry=-2.0 * math.sin(w))
        p.rot("cuello", rx=-3.0 + 2.0 * math.sin(2 * w + 0.5))
        p.rot("cabeza", ry=-2.5 * math.sin(w))
        _cola(p, t, T, 5.0)
        _plantar(rig, p, {k: _paso(rig, k, t / T + f, zancada, alto, apoyo) for k, f in fases.items()})
        return p
    return T, pose, True


def rascar_piso(rig):
    L = 1.5

    def pose(t):
        p = Pose()
        baja = facil(t / 0.4)
        p.rot("cuerpo", rx=-3.0 * baja)
        p.pos("cuerpo", y=-1.0 * baja, z=1.2 * baja)
        p.rot("cuello", rx=-22.0 * baja)
        p.rot("cabeza", rx=-6.0 * baja, rz=2.0 * math.sin(t * 9) * baja)
        _cola(p, t, 0.5, 4.0 * baja, alza=-10.0 * baja)
        objetivos = {k: _pie(rig, k) for k in PATAS}
        x, y, z = _pie(rig, "dd")
        if 0.3 <= t <= 1.5:                       # dos rascadas: adelante en el aire, atras arrastrando
            u = ((t - 0.3) / 0.6) % 1.0
            if u < 0.35:
                f = facil(u / 0.35)
                objetivos["dd"] = (x, y + 3.5 * math.sin(math.pi * f), z + 3.0 - 8.0 * f)
            else:
                f = (u - 0.35) / 0.65
                objetivos["dd"] = (x, y, z - 5.0 + 8.0 * f)
        _plantar(rig, p, objetivos)
        return p
    return L, pose, False


def _cabeza_baja(p, f=1.0):
    p.rot("cuello", rx=-22.0 * f)
    p.rot("cabeza", rx=-8.0 * f)


def embestir(rig):
    T, zancada, alto, apoyo = 0.6, 14.0, 5.0, 0.42
    fases = {"ti": 0.0, "td": 0.08, "di": 0.5, "dd": 0.58}

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        p.rot("cuerpo", rx=4.0 * math.sin(w), rz=1.0 * math.sin(w + 1))
        p.pos("cuerpo", y=-0.3 + 1.2 * math.sin(w + 0.4))
        _cabeza_baja(p)
        p.rot("cabeza", rz=1.5 * math.sin(w))
        p.rot("puas_pecho", rx=1.5 * math.sin(2 * w))
        p.rot("puas_cadera", rx=-1.5 * math.sin(2 * w))
        _cola(p, t, T, 4.0, alza=-12.0)
        _plantar(rig, p, {k: _paso(rig, k, t / T + f, zancada, alto, apoyo) for k, f in fases.items()})
        return p
    return T, pose, True


def chocar(rig):
    L = 0.5

    def pose(t):
        p = Pose()
        golpe = suave(t, [(0.0, 0.0), (0.08, 1.0), (0.25, 0.6), (0.5, 0.75)])
        p.pos("cuerpo", z=2.5 * golpe, y=-0.8 * golpe)
        p.rot("cuerpo", rx=-6.0 * golpe)
        p.rot("cuello", rx=-22.0 - 8.0 * golpe)
        p.rot("cabeza", rx=-8.0, rz=6.0 * math.sin(t * 40) * (1 - t / L))
        _cola(p, t, 0.25, 6.0 * (1 - t / L), alza=-12.0 + 8.0 * (t / L))
        objetivos = {k: _pie(rig, k) for k in PATAS}
        for k in ("dd", "di"):                    # las de enfrente se abren al frenar
            x, y, z = objetivos[k]
            objetivos[k] = (x * (1 + 0.06 * golpe), y, z - 2.0 * golpe)
        _plantar(rig, p, objetivos)
        return p
    return L, pose, False


def atorado(rig):
    T = 1.2

    def pose(t):
        p = Pose()
        w = 2 * math.pi * t / T
        jala = 0.5 - 0.5 * math.cos(w)
        p.pos("cuerpo", z=1.9 + 1.4 * jala, y=-0.6 - 0.4 * jala)
        p.rot("cuerpo", rx=-6.0 + 3.0 * jala)
        p.rot("cuello", rx=-30.0 + 4.0 * jala)
        p.rot("cabeza", rx=-8.0, ry=8.0 * math.sin(w), rz=7.0 * math.sin(w + 1.2))
        _cola(p, t, T / 2, 7.0, alza=-4.0)
        objetivos = {k: _pie(rig, k) for k in PATAS}
        for k in ("td", "ti"):                    # las de atras escarban
            x, y, z = objetivos[k]
            fase = 0.0 if k == "td" else 0.5
            u = (t / T + fase) % 1.0
            objetivos[k] = (x, y + (1.5 * math.sin(2 * math.pi * u) if u < 0.5 else 0.0), z + 2.0 * math.sin(2 * math.pi * u))
        for k in ("dd", "di"):
            x, y, z = objetivos[k]
            objetivos[k] = (x * 1.06, y, z - 2.0)
        _plantar(rig, p, objetivos)
        return p
    return T, pose, True


def zafarse(rig):
    L = 0.8

    def pose(t):
        p = Pose()
        tiron = suave(t, [(0.0, 0.0), (0.15, 1.0), (0.45, 0.2), (0.8, 0.0)])
        resto = 1.0 - facil(t / L)
        p.pos("cuerpo", z=1.9 * resto + 2.5 * tiron, y=-0.6 * resto)
        p.rot("cuerpo", rx=-6.0 * resto + 4.0 * tiron)
        p.rot("cuello", rx=-30.0 * resto + 12.0 * tiron)
        p.rot("cabeza", rx=-8.0 * resto, rz=10.0 * math.sin(t * 28) * (1 - t / L))
        _cola(p, t, 0.3, 6.0 * (1 - t / L))
        _plantar(rig, p, {k: _pie(rig, k) for k in PATAS})
        return p
    return L, pose, False


def cabezazo(rig):
    L = 0.7

    def pose(t):
        p = Pose()
        sube = suave(t, [(0.0, 0.0), (0.22, 1.0), (0.45, 0.4), (0.7, 0.0)])
        baja = 1.0 - facil(t / L)
        p.rot("cuello", rx=-22.0 * baja + 40.0 * sube)
        p.rot("cabeza", rx=-8.0 * baja + 10.0 * sube)
        p.rot("cuerpo", rx=6.0 * sube)
        _cola(p, t, 0.35, 5.0)
        _plantar(rig, p, {k: _pie(rig, k) for k in PATAS})
        return p
    return L, pose, False


def sacudida(rig):
    L = 2.2

    def pose(t):
        p = Pose()
        agacha = suave(t, [(0.0, 0.0), (0.4, 1.0), (1.6, 1.0), (2.2, 0.0)])
        fuerza = suave(t, [(0.0, 0.0), (0.4, 0.0), (0.6, 1.0), (1.45, 1.0), (1.6, 1.6), (1.8, 0.0), (2.2, 0.0)])
        w = 2 * math.pi * 5.0 * t
        p.pos("cuerpo", y=-2.0 * agacha)
        p.rot("cadera", ry=14.0 * fuerza * math.sin(w), rz=8.0 * fuerza * math.sin(w + 1.0))
        p.rot("pecho", ry=-6.0 * fuerza * math.sin(w), rz=-3.0 * fuerza * math.sin(w + 1.0))
        p.rot("puas_cadera", rx=6.0 * fuerza * math.sin(2 * w), rz=5.0 * fuerza * math.sin(2 * w + 2))
        p.rot("puas_pecho", rx=-5.0 * fuerza * math.sin(2 * w + 1), rz=4.0 * fuerza * math.sin(2 * w))
        p.rot("cuello", rx=-10.0 * agacha)
        p.rot("cabeza", rz=4.0 * fuerza * math.sin(w + 2))
        _cola(p, t, 0.2, 9.0 * fuerza)
        _plantar(rig, p, {k: _pie(rig, k) for k in PATAS})
        return p
    return L, pose, False


def alzarse_azotar(rig):
    L = 2.6
    sube = [(0.0, 0.0), (0.9, 38.0), (1.3, 40.0), (1.45, 20.0), (GOLPE_AZOTE, -6.0), (1.75, 1.5), (2.0, -1.0), (2.6, 0.0)]

    def pose(t):
        p = Pose()
        alza = suave(t, sube)
        p.rot("cuerpo", rx=alza)
        temblor = 1.5 * math.sin(t * 35) if 0.9 <= t <= 1.3 else 0.0
        p.rot("cuello", rx=suave(t, [(0.0, 0.0), (0.9, 18.0), (1.3, 22.0), (GOLPE_AZOTE, -14.0), (2.0, -4.0), (2.6, 0.0)]))
        p.rot("cabeza", rx=suave(t, [(0.0, 0.0), (0.9, 10.0), (1.3, 12.0), (GOLPE_AZOTE, -6.0), (2.6, 0.0)]), rz=temblor)
        p.rot("puas_pecho", rx=-4.0 * math.sin(t * 30) * (1.0 if GOLPE_AZOTE <= t <= 2.0 else 0.0))
        p.rot("puas_cadera", rx=4.0 * math.sin(t * 30) * (1.0 if GOLPE_AZOTE <= t <= 2.0 else 0.0))
        for i, h in enumerate(COLAS):              # la cola contrarresta el alzarse: se queda tendida atras
            p.rot(h, rx=-alza * (0.85 if i == 0 else 0.0) + suave(t, [(0.0, 0.0), (0.9, -4.0), (GOLPE_AZOTE, 3.0), (2.6, 0.0)]))
        objetivos = {k: _pie(rig, k) for k in ("td", "ti")}
        _plantar(rig, p, objetivos)
        # las de adelante: en el aire manotean (giros directos); al bajar, IK al piso para el azote
        peso_ik = suave(t, [(0.0, 1.0), (0.35, 0.0), (1.3, 0.0), (1.48, 1.0), (2.6, 1.0)])
        for k, fase in (("dd", 0.0), ("di", math.pi)):
            libre = Pose(p)
            h, c, m = PATAS[k]
            manoteo = math.sin(t * 9 + fase) * (1.0 if 0.6 <= t <= 1.3 else 0.0)
            libre.rot(h, rx=-alza * 0.55 + 18.0 * manoteo)
            libre.rot(c, rx=alza * 0.9 + 12.0 * manoteo)
            libre.rot(m, rx=-alza * 0.4)
            con_ik = Pose(p)
            x, y, z = _pie(rig, k)
            animar.ik_pata(rig, con_ik, PATAS[k], (x, y, z - 2.5 * facil((t - 1.3) / 0.25)))
            for b in (h, c, m):
                (ax, ay, az), tr = libre.get(b, ((0, 0, 0), (0, 0, 0)))
                (bx, by, bz), _ = con_ik.get(b, ((0, 0, 0), (0, 0, 0)))
                p[b] = ((ax + (bx - ax) * peso_ik, ay, az), tr)
        return p
    return L, pose, False


def rugido(rig):
    L = 1.8

    def pose(t):
        p = Pose()
        alto = suave(t, [(0.0, 0.0), (0.35, 1.0), (1.4, 1.0), (1.8, 0.0)])
        p.rot("cuerpo", rx=4.0 * alto)
        p.rot("cuello", rx=16.0 * alto)
        p.rot("cabeza", rx=-10.0 * alto, rz=3.0 * math.sin(t * 30) * alto)
        p.rot("puas_pecho", rx=2.0 * math.sin(t * 40) * alto)
        _cola(p, t, 0.4, 8.0 * alto, alza=-8.0 * alto)
        _plantar(rig, p, {k: _pie(rig, k) for k in PATAS})
        return p
    return L, pose, False


def muerte(rig):
    L = 2.5

    def pose(t):
        p = Pose()
        cae = suave(t, [(0.0, 0.0), (0.5, 0.15), (1.2, 0.8), (1.5, 1.05), (1.8, 1.0), (2.5, 1.0)])
        p.pos("cuerpo", y=-6.5 * cae)
        p.rot("cuerpo", rz=7.0 * cae, rx=-2.0 * cae)
        p.rot("cuello", rx=-8.0 * cae)
        p.rot("cabeza", rz=14.0 * cae, rx=-4.0 * cae)
        for i, h in enumerate(COLAS):
            p.rot(h, rx=4.0 * cae, ry=6.0 * cae * (i % 2 * 2 - 1))
        # las patas se abren hacia los lados (no con IK: al caer se despatarra)
        for k, (h, c, m) in PATAS.items():
            s = 1.0 if k[1] == "d" else -1.0
            p.rot(h, rz=s * 44.0 * cae, rx=(-6.0 if k[0] == "d" else 6.0) * cae)
            p.rot(c, rz=-s * 12.0 * cae)
            p.rot(m, rz=-s * 30.0 * cae)
        _cola_arriba(rig, p)
        bajo = min(min(q[1] for q in P) for P, *_ in rig.quads(p))   # que nada quede bajo el piso al caer
        if bajo < -0.3:
            p.pos("cuerpo", y=-0.3 - bajo)
        return p
    return L, pose, "hold_on_last_frame"


ANIMACIONES = {"quieto": quieto, "caminar": caminar, "rascar_piso": rascar_piso, "embestir": embestir,
               "chocar": chocar, "atorado": atorado, "zafarse": zafarse, "cabezazo": cabezazo, "sacudida": sacudida,
               "alzarse_azotar": alzarse_azotar, "rugido": rugido, "muerte": muerte}


def hornear_todas(rig, solo=None):
    """{nombre: (datos para el json, cuadros, bucle)}."""
    out = {}
    for nombre, f in ANIMACIONES.items():
        if solo and nombre not in solo:
            continue
        largo, pose, bucle = f(rig)
        datos, cuadros = animar.hornear(rig, nombre, largo, pose, bucle)
        out[nombre] = (datos, cuadros, bucle)
    return out
