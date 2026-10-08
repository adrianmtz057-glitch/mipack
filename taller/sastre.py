"""
Sastre: ficha -> Modelo hecho POR PIEZAS (como los modelos de la comunidad).

  - cuerpo con medidas propias (altura, cabeza, complexion)
  - ropa por capas: camisa pintada, tunica con abertura real, solapas, faldon en paneles que se
    abren desde la cintura (y se cortan en tiras), mangas anchas, capa inclinada, bufanda envolvente
  - piezas inclinadas: mechones, cuellos en V, correas cruzadas, hojas, plumas, cuernos
  - ribetes de contraste en los bordes y pintura de pixel art por material (pintura.py)

Ejes: frente = -Z, derecha del personaje = +X, pies en y = 0. Unidades en px (16 = 1 bloque).
"""

import math

from .modelo import Modelo
from .pintura import Paleta, cuero, metal, pelo, piel, plano, tela
from .textura import TRANSPARENTE, azar, hex_a_rgba, mezcla

ORO = "#E3B04B"


class Sastre:
    def __init__(self, F):
        self.F = F
        self.semilla = int(azar(*[ord(c) for c in F["nombre"]]) * 1e6)
        self._s = 0
        self._medidas()
        self.m = Modelo(F.get("_id") or F["nombre"])
        self.m.pivotes.update(self.pivotes)

    def sem(self):
        self._s += 1
        return self.semilla + self._s * 131

    # ------------------------------------------------------------------ medidas
    def _medidas(self):
        p = self.F["proporciones"]
        H = p["altura"]
        hh = max(7, min(11, round(8 * p["cabeza"])))
        hw = hh if hh % 2 == 0 else hh + 1
        comp = p["complexion"]
        tw = {"delgada": 8, "normal": 8, "robusta": 10}[comp]
        td = {"delgada": 4, "normal": 4, "robusta": 5}[comp]
        aw = {"delgada": 3.5, "normal": 4, "robusta": 5}[comp]
        if self.F["brazos"] == "finos":
            aw = 3
        resto = max(10, H - hh)
        lh = round(resto * 0.5)
        th = resto - lh
        self.hh, self.hw, self.hd = hh, hw, hw
        self.tw, self.td, self.aw, self.ad = tw, td, aw, 4 if aw >= 4 else aw + 0.5
        self.lh, self.th = lh, th
        self.lw = tw / 2
        self.ld = td
        self.cuello = lh + th
        self.hy0, self.hy1 = self.cuello, self.cuello + hh
        self.ay0 = lh                                    # punta de la mano (como el player)
        self.pivotes = {
            "Head": (0, self.cuello, 0), "Body": (0, self.cuello, 0),
            "RightArm": (tw / 2 + aw / 2, self.cuello - 1.5, 0), "LeftArm": (-(tw / 2 + aw / 2), self.cuello - 1.5, 0),
            "RightLeg": (self.lw / 2, lh, 0), "LeftLeg": (-self.lw / 2, lh, 0),
        }

    # ------------------------------------------------------------------ atajos
    def caja(self, hueso, nombre, x1, y1, z1, x2, y2, z2, pintor, rot=None, piv=None):
        return self.m.cubo(hueso, nombre, (x1, y1, z1), (x2, y2, z2), pintor, rot, piv)

    def par(self, hueso, nombre, x1, y1, z1, x2, y2, z2, pintor, rot=None, piv=None):
        self.m.par(hueso, nombre, (x1, y1, z1), (x2, y2, z2), pintor, rot, piv)

    def tiras(self, hueso, nombre, eje, a1, a2, y1, y2, fijo1, fijo2, pintor, rot, piv, sem, ancho=2.0, var=2.5,
              simetrico=True):
        """Panel cortado en tiras verticales de distinto largo (borde inferior irregular)."""
        n = max(1, round((a2 - a1) / ancho))
        paso = (a2 - a1) / n
        for k in range(n):
            b1, b2 = a1 + k * paso, a1 + (k + 1) * paso
            extra = round(azar(sem, k, round(a1 * 4), 3) * var * 2) / 2 - var * 0.3
            yb = min(y2 - 1, y1 - extra)
            if eje == "x":
                d, h = (b1, yb, fijo1), (b2, y2, fijo2)
            else:
                d, h = (fijo1, yb, b1), (fijo2, y2, b2)
            if simetrico:
                self.m.par(hueso, f"{nombre}{k}", d, h, pintor, rot, piv)
            else:
                self.m.cubo(hueso, f"{nombre}{k}", d, h, pintor, rot, piv)

    # ------------------------------------------------------------------ cuerpo
    def cuerpo(self):
        F = self.F
        r = F["ropa"]
        tw, td, aw, ad, lw, ld = self.tw, self.td, self.aw, self.ad, self.lw, self.ld
        sem = self.sem()
        camisa = tela(r["camisa"]["color"], [r["camisa"]["color"], Paleta(r["camisa"]["color"]).s],
                      patron=r["camisa"].get("patron", "liso"), sem=sem, bordes=())
        pantalon = tela(r["pantalon"]["color"], sem=sem, bordes=())
        pi = piel(F["piel"])
        guantes = r["guantes"]

        self.caja("Body/torso", "torso", -tw / 2, self.lh, -td / 2, tw / 2, self.cuello, td / 2, camisa)
        self.par("RightArm/brazo", "brazo", tw / 2, self.ay0 + 3, -ad / 2, tw / 2 + aw, self.cuello, ad / 2, camisa)
        mano = cuero(guantes["color"]) if (guantes and not guantes.get("sin_dedos", True)) else pi
        self.par("RightArm/brazo", "mano", tw / 2, self.ay0, -ad / 2, tw / 2 + aw, self.ay0 + 3, ad / 2, mano)
        self.par("RightLeg/pierna", "pierna", 0, 0, -ld / 2, lw, self.lh, ld / 2, pantalon)
        self.caja("Head/cabeza", "cabeza", -self.hw / 2, self.hy0, -self.hd / 2, self.hw / 2, self.hy1, self.hd / 2,
                  self.pintor_cabeza())

    def pintor_cabeza(self):
        F = self.F
        P = Paleta(F["piel"])
        H = Paleta(F["pelo"]["color"])
        estilo = F["pelo"]["estilo"]
        cara = self.pintor_cara()

        M = Paleta(F["cara"]["mascara"]) if F["cara"]["mascara"] else None

        def p(t):
            if t.cara == "north":
                return cara(t)
            if M:                                          # la mascara/capucha cubre toda la cabeza
                return M.l if (t.cara == "up" and (t.i + t.j) % 4 == 0) else (M.s if t.cara == "down" else M.b)
            if t.cara == "down":
                return P.s
            if estilo == "ninguno":
                return P.b if t.cara != "up" else P.l
            fila = t.th - 1 - t.j
            if t.cara == "up" or t.cara == "south" and fila >= 1:
                return H.b if (t.i + t.j) % 3 else H.s
            if t.cara in ("east", "west"):
                frente = (t.i >= t.tw - 2) if t.cara == "east" else (t.i <= 1)
                if fila >= (5 if frente else 3) or estilo == "largo":
                    return H.s if t.i % 2 else H.b
            return P.b if fila > 0 else P.s
        return p

    def pintor_cara(self):
        F = self.F
        c = F["cara"]
        P = Paleta(F["piel"])
        O = Paleta(c["ojos"])
        H = Paleta(F["pelo"]["color"])
        exp = c["expresion"]
        estilo = F["pelo"]["estilo"]
        brillan = c.get("brillo", False)
        mascara = Paleta(c["mascara"]) if c["mascara"] else None
        blanco = (240, 238, 232, 255)
        pestana = H.o if estilo != "ninguno" else (30, 22, 22, 255)
        rubor = mezcla(P.b, (220, 110, 110, 255), 0.35)
        y0 = 2 if self.hh <= 8 else 3                    # fila baja de los ojos (0 = menton)
        ancho_ojo = 2 if self.hw <= 8 else 3

        def p(t):
            fila = t.th - 1 - t.j
            u = t.i - (t.tw - 1) / 2                     # u > 0 = derecha del que mira
            au = abs(u)
            ojo = 1.4 <= au <= 1.6 + ancho_ojo - 1
            interior = au < 2
            exterior = au > 0.9 + ancho_ojo - 1
            if mascara:
                if ojo and fila in (y0, y0 + 1):
                    return O.h if fila == y0 + 1 else O.l
                if estilo != "ninguno" and fila >= t.th - 1:
                    return H.b
                return mascara.b if (t.i + fila) % 4 else mascara.s
            if estilo != "ninguno":
                if fila >= t.th - 2:
                    return H.b if (t.i % 3) else H.s
                if fila == t.th - 3 and azar(self.semilla, t.i, 7) < 0.5:
                    return H.s
                if au >= t.tw / 2 - 0.6 and fila >= y0 + 1:
                    return H.s                            # patillas
            if ojo and fila in (y0, y0 + 1):
                if brillan:
                    return O.h if (fila == y0 + 1 and interior) else (O.l if fila == y0 + 1 else O.b)
                if exp == "traviesa" and u < 0:          # guino
                    return pestana if fila == y0 else P.b
                if exterior and not interior:
                    return blanco if fila == y0 + 1 else mezcla(blanco, P.b, 0.25)
                return O.s if fila == y0 + 1 else O.b
            if fila == y0 + 2 and ojo:                   # cejas
                if exp == "seria" or (exp != "alegre" and not interior) or brillan:
                    return H.s if estilo != "ninguno" else P.s2
            if fila == y0 - 1:
                if au < 1:
                    return {"alegre": mezcla(P.s2, (120, 50, 50, 255), 0.5), "seria": P.s2,
                            "serena": P.s, "traviesa": P.s2 if u > 0 else P.s}[exp]
                if exp == "traviesa" and 0.9 < u < 1.6:
                    return P.s2
                if c["rubor"] and ojo and exterior:
                    return rubor
            return P.b
        return p

    # ------------------------------------------------------------------ pelo
    def pelo3d(self):
        F = self.F
        P = F["pelo"]
        est = P["estilo"]
        if est == "ninguno":
            return
        sem = self.sem()
        pin1 = pelo(P["color"], P["brillo"], P["mechas"], sem)
        if P.get("bicolor"):                                   # mitad de otro color (lado izquierdo, -X)
            pin2 = pelo(P["bicolor"], None, None, sem + 1)

            def pin(t):
                return pin2(t) if t.x < 0 else pin1(t)
        else:
            pin = pin1
        vol = P["volumen"]
        hw, hd, hy0, hy1 = self.hw / 2, self.hd / 2, self.hy0, self.hy1
        lado = 0.5 + 0.25 * vol
        arriba = 0.75 + 0.5 * vol
        g = "Head/pelo"
        # masa principal
        self.caja(g, "pelo_tapa", -hw - lado, hy1 - 1, -hd - 0.75, hw + lado, hy1 + arriba, hd + lado, pin)
        bajo_atras = hy0 + 1 if est != "largo" else hy0 - 7
        self.caja(g, "pelo_nuca", -hw - lado, bajo_atras, hd - 0.5, hw + lado, hy1, hd + lado + 0.25, pin)
        bajo_lado = hy0 + 3 if est != "largo" else hy0 - 3
        self.par(g, "pelo_lado", hw, bajo_lado, -hd + 1.5, hw + lado, hy1, hd, pin)
        # flequillo: mechones inclinados delante de la frente
        n = max(4, round(self.hw / 2))
        ancho = (2 * hw + 1) / n
        for k in range(n):
            x1 = -hw - 0.5 + k * ancho
            r = azar(sem, k, 1)
            largo = {"rizos": 2.5 + r * 1.5, "revuelto": 2.5 + r * 2, "puntas": 2 + (k % 2) * 2,
                     "lado": 1.5 + (k / n) * 3.5, "largo": 2.5 + r, "corto": 1.5 + r * 0.8}[est]
            ang = {"lado": -22.5, "puntas": (-22.5 if x1 + ancho / 2 > 0 else 22.5)}.get(est, (r - 0.5) * 30)
            yb = max(self.hy0 + 5.2, hy1 + 0.5 - largo)
            piv = (x1 + ancho / 2, hy1 + 0.5, -hd - 0.5)
            self.caja(g, f"flequillo{k}", x1, yb, -hd - 1.0, x1 + ancho + 0.25, hy1 + 0.75, -hd - 0.25, pin,
                      rot=(0, 0, round(ang / 7.5) * 7.5), piv=piv)
        # mechones laterales delante de las orejas
        for s in (1, -1):
            x = hw - 0.25
            largo = {"largo": 9, "rizos": 4.5, "revuelto": 4, "lado": 4 + (s > 0) * 2}.get(est, 3)
            d, h = (x, hy1 - largo, -hd - 0.25), (x + 1.5, hy1, -hd + 2.0)
            if s < 0:
                d, h = (-h[0], d[1], d[2]), (-d[0], h[1], h[2])
            self.m.cubo(g, f"mechon_lado_{s}", d, h, pin, rot=(0, 0, 7.5 * s), origen=((d[0] + h[0]) / 2, hy1, -hd))
        # estilo
        if est in ("rizos", "revuelto"):
            n = 18 + 6 * vol if est == "rizos" else 12
            for k in range(n):
                a = azar(sem, k, 11) * math.pi * 2
                zona = azar(sem, k, 12)
                if zona < 0.45:                                   # arriba
                    cx = math.cos(a) * (hw + lado * 0.5) * azar(sem, k, 13) ** 0.5
                    cz = math.sin(a) * (hd + lado * 0.5) * azar(sem, k, 13) ** 0.5
                    cy = hy1 + arriba - 0.5
                elif zona < 0.75:                                 # atras
                    cx = (azar(sem, k, 14) * 2 - 1) * (hw + lado)
                    cz = hd + lado
                    cy = hy0 + 2 + azar(sem, k, 15) * (self.hh - 1)
                else:                                             # costados
                    s = 1 if azar(sem, k, 16) < 0.5 else -1
                    cx = s * (hw + lado)
                    cz = (azar(sem, k, 17) * 2 - 1) * hd
                    cy = hy0 + 4 + azar(sem, k, 18) * (self.hh - 3)
                t = 1.5 + azar(sem, k, 19) * (1.0 + 0.4 * vol)
                eje = int(azar(sem, k, 20) * 3)
                rot = [0, 0, 0]
                rot[eje] = (-1) ** k * 22.5
                self.caja(g, f"rizo{k}", cx - t / 2, cy - t / 2, cz - t / 2, cx + t / 2, cy + t / 2, cz + t / 2, pin,
                          rot=tuple(rot), piv=(cx, cy, cz))
        if est == "puntas":
            for k in range(9):
                a = k / 9 * math.pi * 2
                cx, cz = math.cos(a) * (hw - 1), math.sin(a) * (hd - 1)
                base = hy1 + arriba - 0.5
                largo = 3 + azar(sem, k, 21) * 3
                rz = -22.5 if cx > 1 else (22.5 if cx < -1 else 0)
                rx = 22.5 if cz > 1 else (-22.5 if cz < -1 else 0)
                self.caja(g, f"punta{k}", cx - 1, base - 1, cz - 1, cx + 1, base + largo, cz + 1, pin,
                          rot=(rx, 0, rz), piv=(cx, base, cz))
        if est == "largo":
            for s in (1, -1):                                     # mechones largos al frente del hombro
                x = (hw - 1.5) if s > 0 else -(hw - 0.5)
                self.caja(g, f"melena_frente_{s}", x, hy0 - 6, -hd + 0.5, x + 2, hy1 - 2, -hd + 2.5, pin,
                          rot=(0, 0, 7.5 * s), piv=(x + 1, hy1 - 2, -hd + 1.5))
        self.pelo_top = hy1 + arriba
        self.pelo_lado = hw + lado

    # ------------------------------------------------------------------ ropa
    def tunica(self):
        F = self.F
        r = F["ropa"]
        tu = r["tunica"]
        if not tu:
            return
        sem = self.sem()
        tw, td, lw, ld = self.tw, self.td, self.lw, self.ld
        cols = tu["colores"]
        rib = tu["ribete"] or Paleta(cols[0]).o
        cuerpo_p = tela(cols[0], cols, tu["patron"], rib, ("abajo",), sem=sem)
        borde_p = tela(cols[0], cols, tu["patron"], rib, ("todo",), sem=sem)
        ribete_p = tela(rib, sem=sem, bordes=(), pliegues=False)
        ab = 1.25 if tu["abierta"] else 0
        g = "Body/tunica"
        e = 0.6                                                   # grosor de la tela
        # ---- torso
        self.caja(g, "tunica_espalda", -tw / 2 - e, self.lh - 0.5, td / 2, tw / 2 + e, self.cuello + 0.5, td / 2 + e,
                  cuerpo_p)
        self.par(g, "tunica_costado", tw / 2, self.lh - 0.5, -td / 2, tw / 2 + e, self.cuello + 0.5, td / 2, cuerpo_p)
        if ab:
            self.par(g, "tunica_frente", ab, self.lh - 0.5, -td / 2 - e, tw / 2 + e, self.cuello + 0.5, -td / 2,
                     borde_p)
            self.par(g, "tunica_tapeta", ab - 0.25, self.lh - 0.5, -td / 2 - e - 0.4, ab + 0.9, self.cuello + 0.25,
                     -td / 2 - e + 0.1, ribete_p)
            bu = r["bufanda"]
            if not (bu and bu["tamano"] == "grande"):            # solapas en V
                self.par(g, "solapa", ab, self.cuello - 5, -td / 2 - e - 0.6, ab + 2.2, self.cuello + 0.5,
                         -td / 2 - e - 0.1, borde_p, rot=(0, 0, -22.5), piv=(ab, self.cuello + 0.5, -td / 2))
        else:
            self.caja(g, "tunica_frente", -tw / 2 - e, self.lh - 0.5, -td / 2 - e, tw / 2 + e, self.cuello + 0.5,
                      -td / 2, borde_p)
        self.caja(g, "tunica_hombros", -tw / 2 - e, self.cuello, -td / 2 - e, tw / 2 + e, self.cuello + 0.5,
                  td / 2 + e, cuerpo_p)
        # ---- faldon (paneles que se abren, en las piernas)
        bota = r["botas"]["alto"]
        fondo = {"corta": self.lh * 0.55, "media": self.lh * 0.3, "larga": bota + 0.5}[tu["largo"]]
        ang = {"corta": 10, "media": 7.5, "larga": 5}[tu["largo"]]
        top = self.lh + 0.5
        gl = "RightLeg/faldon"
        hilo = tela(cols[0], cols, tu["patron"], rib, ("abajo",), sem=sem, deshilachado=0.25)
        tiras = tu.get("borde", "tiras") == "tiras"
        za, zb = -ld / 2 - 0.9, -ld / 2 - 0.9 + e
        xa = (ab + 0.4) if ab else 0
        xb = lw + 0.9
        rot_f, piv_f = (ang, 0, 0), ((xa + xb) / 2, top, za)
        rot_l, piv_l = (0, 0, ang), (xb, top, 0)
        rot_b, piv_b = (-ang, 0, 0), ((xa + xb) / 2, top, ld / 2 + 0.9)
        if tiras:
            self.tiras(gl, "faldon_frente", "x", xa, xb, fondo, top, za, zb, hilo, rot_f, piv_f, sem)
            self.tiras(gl, "faldon_lado", "z", -ld / 2 - 0.9, ld / 2 + 0.9, fondo, top, xb - e, xb, hilo, rot_l, piv_l,
                       sem + 1)
            self.tiras(gl, "faldon_atras", "x", 0, xb, fondo - 1, top, ld / 2 + 0.9 - e, ld / 2 + 0.9, hilo, rot_b,
                       piv_b, sem + 2)
        else:
            self.par(gl, "faldon_frente", xa, fondo, za, xb, top, zb, borde_p, rot_f, piv_f)
            self.par(gl, "faldon_lado", xb - e, fondo, -ld / 2 - 0.9, xb, top, ld / 2 + 0.9, borde_p, rot_l, piv_l)
            self.par(gl, "faldon_atras", 0, fondo - 1, ld / 2 + 0.9 - e, xb, top, ld / 2 + 0.9, borde_p, rot_b, piv_b)
        if ab:
            self.par(gl, "faldon_tapeta", xa - 0.25, fondo + 1, za - 0.4, xa + 0.8, top, za + 0.2, ribete_p, rot_f,
                     piv_f)
        if tu.get("panel"):                                        # tela que cuelga en la abertura
            pp = tela(tu["panel"], sem=sem, bordes=("abajo",), ribete=Paleta(tu["panel"]).s, deshilachado=0.2)
            self.caja("Body/panel", "panel", -ab - 0.25, fondo + 1, -td / 2 - 0.5, ab + 0.25, self.lh + 4, -td / 2 - 0.1,
                      pp)
        self.fondo = fondo

    def mangas(self):
        F = self.F
        r = F["ropa"]
        mg = r["mangas"]
        tu = r["tunica"]
        if not mg and not tu:
            return
        if not mg:
            mg = {"color": tu["colores"][0], "color2": tu["colores"][-1], "forma": "ajustadas", "patron": tu["patron"]}
        sem = self.sem()
        tw, aw, ad = self.tw, self.aw, self.ad
        cols = [mg["color"], mg["color2"]] + ((tu["colores"][1:]) if tu and mg["patron"] in ("manchas", "camuflaje") else [])
        rib = (tu and tu["ribete"]) or Paleta(mg["color2"]).o
        p = tela(mg["color"], cols, mg["patron"], rib, ("abajo",), sem=sem)
        g = "RightArm/manga"
        x1, x2 = tw / 2 - 0.3, tw / 2 + aw + 0.5
        base = self.ay0 + 3
        if mg["forma"] == "ajustadas":
            self.par(g, "manga", x1, base, -ad / 2 - 0.5, x2, self.cuello + 0.5, ad / 2 + 0.5, p)
        else:
            corte = base + 3.5
            self.par(g, "manga", x1, corte, -ad / 2 - 0.5, x2, self.cuello + 0.5, ad / 2 + 0.5,
                     tela(mg["color"], cols, mg["patron"], None, (), sem=sem))
            desh = tela(mg["color"], cols, mg["patron"], rib, ("abajo",), sem=sem, deshilachado=0.3)
            self.par(g, "manga_campana", x1 + 0.2, base - 1, -ad / 2 - 1.1, x2 + 0.9, corte + 0.5, ad / 2 + 1.1, desh,
                     rot=(0, 0, 10), piv=(x1, corte + 0.5, 0))
            if mg["forma"] == "capas":
                self.par(g, "manga_capa", x1 + 0.3, corte + 1.5, -ad / 2 - 0.9, x2 + 0.6, self.cuello - 1,
                         ad / 2 + 0.9, desh, rot=(0, 0, 7.5), piv=(x1, self.cuello - 1, 0))
        self.par(g, "hombro", x1, self.cuello - 2.5, -ad / 2 - 0.8, x2 + 0.4, self.cuello + 0.9, ad / 2 + 0.8,
                 tela(mg["color"], cols, mg["patron"], rib, ("abajo",), sem=sem + 1))

    def bufanda(self):
        F = self.F
        bu = F["ropa"]["bufanda"]
        if not bu:
            return
        sem = self.sem()
        tw, td = self.tw, self.td
        cols = [bu["color"], Paleta(bu["color"]).l, bu["color"], bu["color2"]]
        base = tela(bu["color"], cols, "manchas", None, (), sem=sem, pliegues=False)

        def vueltas(t):
            c = base(t)
            if t.cara in ("north", "south", "east", "west") and (t.j % 3 == 2):
                return Paleta(bu["color"]).s if c == Paleta(bu["color"]).b else c
            return c
        colas = tela(bu["color"], cols, "manchas", Paleta(bu["color"]).s, ("abajo", "lados"), sem=sem, deshilachado=0.35)
        g = "Body/bufanda"
        grande = bu["tamano"] == "grande"
        T = 2.2 if grande else 1.3
        y1, y2 = self.cuello - (3 if grande else 2), self.cuello + 1
        # anillo alrededor del cuello
        self.caja(g, "bufanda_frente", -tw / 2 - 0.5, y1, -td / 2 - T, tw / 2 + 0.5, y2, -td / 2 + 0.5, vueltas)
        self.caja(g, "bufanda_atras", -tw / 2 - 0.5, y1, td / 2 - 0.5, tw / 2 + 0.5, y2, td / 2 + T, vueltas)
        self.par(g, "bufanda_lado", tw / 2 - 1, y1, -td / 2 - T + 0.2, tw / 2 + T * 0.6, y2, td / 2 + T - 0.2, vueltas)
        if grande:                                                 # segunda vuelta, abraza el menton
            self.caja(g, "bufanda_vuelta", -self.hw / 2 + 0.5, y2 - 1.2, -self.hd / 2 - 1.2, self.hw / 2 - 0.5, y2 + 0.4,
                      self.hd / 2 - 1.0, vueltas)
            self.caja(g, "bufanda_nudo", -3.5, y1 - 2, -td / 2 - T - 0.8, 0.5, y1 + 1, -td / 2 - T + 0.4, vueltas,
                      rot=(0, 0, 15), piv=(-1.5, y1, -td / 2))
        if bu["colas"]:
            largas = bu.get("largo") == "largo"
            fin = (self.lh - 5 if largas else self.lh - 1) if grande else self.lh + self.th / 2
            ancho = 3.6 if grande else 2.4
            self.caja(g, "bufanda_cola1", 0.3, fin, -td / 2 - T - 0.6, 0.3 + ancho, y1 + 0.5, -td / 2 - T + 0.3, colas,
                      rot=(0, 0, -7.5), piv=(0.3 + ancho / 2, y1, -td / 2 - T))
            if grande:
                self.caja(g, "bufanda_cola2", -3.2, fin + 4, -td / 2 - T - 0.1, 0.0, y1, -td / 2 - T + 0.6, colas,
                          rot=(0, 0, 7.5), piv=(-1.6, y1, -td / 2 - T))
                fin_b = self.lh - (8 if largas else 2)
                self.caja(g, "bufanda_cola_atras", -4, fin_b, td / 2 + T - 0.3, -0.8, y2, td / 2 + T + 0.6, colas,
                          rot=(-5, 0, 7.5), piv=(-2.4, y2, td / 2 + T))

    def capa(self):
        F = self.F
        ca = F["ropa"]["capa"]
        if not ca:
            return
        sem = self.sem()
        tw, td, aw, ad = self.tw, self.td, self.aw, self.ad
        cols = [ca["color"], ca["color2"]] if ca["patron"] != "estrellas" else [ca["color"], ORO, ca["color2"]]
        rib = Paleta(ca["color2"]).s
        p = tela(ca["color"], cols, ca["patron"], rib, ("abajo", "lados"), sem=sem, deshilachado=0.2)
        fondo = {"corta": self.lh, "media": self.lh * 0.45, "larga": 1.0}[ca["largo"]]
        zc = td / 2 + 1.0
        if F["ropa"]["bufanda"] and F["ropa"]["bufanda"]["tamano"] == "grande":
            zc = td / 2 + 2.4
        g = "Body/capa"
        self.tiras(g, "capa", "x", 0, tw / 2 + 1.5, fondo, self.cuello + 0.5, zc, zc + 0.75, p, (-6, 0, 0),
                   (0, self.cuello + 0.5, zc), sem, ancho=2.5, var=2)
        hombro = tela(ca["color"], cols, ca["patron"], rib, ("abajo",), sem=sem)
        self.par("RightArm/capa", "capa_hombro", tw / 2 - 0.5, self.cuello - 1.2, -ad / 2 - 0.9, tw / 2 + aw + 1.1,
                 self.cuello + 1.2, zc + 0.5, hombro)
        if ca["capucha"]:
            self.caja(g, "capucha", -self.hw / 2 + 1, self.cuello - 1.5, zc - 0.5, self.hw / 2 - 1, self.cuello + 3,
                      zc + 3, hombro, rot=(-15, 0, 0), piv=(0, self.cuello, zc))
            self.caja(g, "capucha_punta", -1.5, self.cuello - 3.5, zc + 0.5, 1.5, self.cuello - 1, zc + 2.5, hombro,
                      rot=(-15, 0, 0), piv=(0, self.cuello, zc))

    def cinturon(self):
        F = self.F
        r = F["ropa"]
        ci = r["cinturon"]
        if not ci:
            return
        sem = self.sem()
        tw, td = self.tw, self.td
        g = "Body/cinturon"
        c = cuero(ci["color"], sem)
        self.caja(g, "cinturon", -tw / 2 - 0.9, self.lh, -td / 2 - 0.9, tw / 2 + 0.9, self.lh + 1.75, td / 2 + 0.9, c)
        self.caja(g, "hebilla", -1.25, self.lh - 0.3, -td / 2 - 1.4, 1.25, self.lh + 2.05, -td / 2 - 0.85,
                  metal(ci["hebilla"], sem))
        if ci.get("bolsas", True):
            self.par(g, "bolsa", tw / 2 - 2.5, self.lh - 2.5, -td / 2 - 1.8, tw / 2 + 0.2, self.lh + 0.5, -td / 2 - 0.6,
                     cuero(ci["color"], sem + 1))
            self.par(g, "bolsa_tapa", tw / 2 - 2.7, self.lh - 0.5, -td / 2 - 2.0, tw / 2 + 0.4, self.lh + 0.75,
                     -td / 2 - 0.6, metal(ci["hebilla"], sem))
            self.par(g, "colgante", 1.5, self.lh - 4, td / 2 + 0.9, 2.3, self.lh, td / 2 + 1.5, c, rot=(0, 0, 7.5),
                     piv=(1.9, self.lh, td / 2 + 1))

    def correas(self):
        F = self.F
        co = F["ropa"]["correas"]
        if not co:
            return
        sem = self.sem()
        td = self.td
        g = "Body/correas"
        yc = self.lh + self.th * 0.55
        L = self.th * 1.15
        c = cuero(co["color"], sem, costura=False)
        z1 = -td / 2 - 1.5
        for s, nombre in ((1, "a"), (-1, "b")):
            self.caja(g, f"correa_{nombre}", -0.7, yc - L / 2, z1, 0.7, yc + L / 2, z1 + 0.5, c,
                      rot=(0, 0, 33.75 * s), piv=(0, yc, z1))
            self.caja(g, f"correa_atras_{nombre}", -0.7, yc - L / 2, td / 2 + 1.0, 0.7, yc + L / 2, td / 2 + 1.5, c,
                      rot=(0, 0, 33.75 * s), piv=(0, yc, td / 2 + 1))
        self.caja(g, "correa_anillo", -1, yc - 1, z1 - 0.4, 1, yc + 1, z1 + 0.1, metal(co["detalle"], sem))

    def banda(self):
        F = self.F
        b = F["ropa"]["banda"]
        if not b:
            return
        sem = self.sem()
        td = self.td
        yc = self.lh + self.th * 0.5
        L = self.th * 1.25
        p = tela(b["color"], ribete=b["detalle"], bordes=("lados",), sem=sem, pliegues=False)
        self.caja("Body/banda", "banda", -1.1, yc - L / 2, -td / 2 - 1.3, 1.1, yc + L / 2, -td / 2 - 0.75, p,
                  rot=(0, 0, -33.75), piv=(0, yc, 0))
        self.caja("Body/banda", "banda_atras", -1.1, yc - L / 2, td / 2 + 0.75, 1.1, yc + L / 2, td / 2 + 1.3, p,
                  rot=(0, 0, 33.75), piv=(0, yc, 0))

    def hombreras(self):
        ho = self.F["ropa"]["hombreras"]
        if not ho:
            return
        sem = self.sem()
        tw, aw, ad = self.tw, self.aw, self.ad
        g = "RightArm/hombrera"
        p = tela(ho["color"], ribete=ho["detalle"], bordes=("abajo", "lados"), sem=sem, pliegues=False)
        self.par(g, "hombrera", tw / 2 - 0.8, self.cuello - 1.5, -ad / 2 - 1.3, tw / 2 + aw + 1.3, self.cuello + 1.4,
                 ad / 2 + 1.3, p, rot=(0, 0, -15), piv=(tw / 2, self.cuello, 0))
        self.par(g, "hombrera_baja", tw / 2 + 0.6, self.cuello - 3.6, -ad / 2 - 1.1, tw / 2 + aw + 1.9,
                 self.cuello - 1.2, ad / 2 + 1.1, p, rot=(0, 0, -22.5), piv=(tw / 2 + 0.6, self.cuello - 1.2, 0))
        self.par(g, "hombrera_gema", tw / 2 + aw + 1.0, self.cuello - 0.8, -1, tw / 2 + aw + 1.6, self.cuello + 0.8, 1,
                 metal(ho["detalle"], sem), rot=(0, 0, -15), piv=(tw / 2, self.cuello, 0))

    def manos(self):
        F = self.F
        r = F["ropa"]
        gu, br = r["guantes"], r["brazaletes"]
        sem = self.sem()
        tw, aw, ad = self.tw, self.aw, self.ad
        g = "RightArm/guante"
        if gu:
            y1 = self.ay0 + (1.0 if gu.get("sin_dedos", True) else -0.25)
            self.par(g, "guante", tw / 2 - 0.25, y1, -ad / 2 - 0.3, tw / 2 + aw + 0.3, self.ay0 + 3.2, ad / 2 + 0.3,
                     cuero(gu["color"], sem))
            self.par(g, "guante_puno", tw / 2 - 0.45, self.ay0 + 2.8, -ad / 2 - 0.55, tw / 2 + aw + 0.55,
                     self.ay0 + 4.2, ad / 2 + 0.55, metal(gu["detalle"], sem))
        elif br:
            self.par("RightArm/brazalete", "brazalete", tw / 2 - 0.3, self.ay0 + 3, -ad / 2 - 0.4, tw / 2 + aw + 0.4,
                     self.ay0 + 4.2, ad / 2 + 0.4, metal(br, sem))

    def botas(self):
        b = self.F["ropa"]["botas"]
        sem = self.sem()
        lw, ld = self.lw, self.ld
        alto = b["alto"]
        g = "RightLeg/bota"
        c = cuero(b["color"], sem)
        self.par(g, "bota", 0, 0, -ld / 2 - 0.4, lw + 0.4, alto, ld / 2 + 0.4, c)
        ribete = b["ribete"] or Paleta(b["color"]).l
        self.par(g, "bota_cana", -0.0, alto - 1.5, -ld / 2 - 0.7, lw + 0.7, alto + 0.4, ld / 2 + 0.7,
                 tela(b["color"], ribete=ribete, bordes=("arriba",), sem=sem, pliegues=False))
        self.par(g, "bota_puntera", 0.2, 0, -ld / 2 - 1.6, lw + 0.2, 1.8, -ld / 2, cuero(b["color"], sem + 1))
        self.par(g, "bota_suela", -0.1, -0.01, -ld / 2 - 1.7, lw + 0.5, 0.6, ld / 2 + 0.5,
                 cuero(Paleta(b["color"]).o, sem, costura=False))
        if b.get("hebillas"):
            yh = max(1.2, alto * 0.45)
            self.par(g, "bota_correa", -0.05, yh, -ld / 2 - 0.55, lw + 0.55, yh + 1, ld / 2 + 0.55,
                     cuero(Paleta(b["color"]).l, sem, costura=False))
            self.par(g, "bota_hebilla", lw + 0.5, yh - 0.25, -0.9, lw + 0.9, yh + 1.25, 0.9, metal(b["hebillas"], sem))

    def pechera(self):
        pe = self.F["ropa"].get("pechera")
        if not pe:
            return
        sem = self.sem()
        tw, td = self.tw, self.td
        y1, y2 = self.cuello - self.th * 0.55, self.cuello + 0.2
        placa = tela(pe["color"], ribete=pe["detalle"], bordes=("todo",), sem=sem, pliegues=False)
        self.caja("Body/pechera", "pechera", -tw / 2 - 0.9, y1, -td / 2 - 1.1, tw / 2 + 0.9, y2, -td / 2 - 0.4, placa)
        self.caja("Body/pechera", "pechera_atras", -tw / 2 - 0.9, y1 + 1, td / 2 + 0.4, tw / 2 + 0.9, y2, td / 2 + 1.0,
                  placa)
        self.caja("Body/pechera", "pechera_gema", -1, y1 + 1.5, -td / 2 - 1.5, 1, y1 + 3.5, -td / 2 - 1.0,
                  metal(pe["detalle"], sem, gema=pe.get("gema") or "#3A7BD5"))

    # ------------------------------------------------------------------ cabeza
    def accesorios_cabeza(self):
        for acc in self.F["cabeza"]:
            getattr(self, "acc_" + acc["tipo"], lambda a: None)(acc)

    def ramillete(self, g, nombre, cx, cy, cz, color, sem, hojas=6, largo=2.6, ancho=1.1, lado=1):
        """Hojas que salen de un centro, en abanico (multiplo de 22.5 grados para que sirva en cualquier formato)."""
        p = metal(color, sem) if hex_a_rgba(color)[0] > 150 else tela(color, sem=sem, bordes=(), pliegues=False)
        for k in range(hojas):
            ang = -67.5 + k * (180 / max(1, hojas - 1))
            ang = round(ang / 22.5) * 22.5
            L = largo * (0.8 + 0.4 * azar(sem, k))
            self.m.cubo(g, f"{nombre}{k}", (cx - 0.35 * lado, cy, cz - ancho / 2), (cx + 0.35 * lado, cy + L, cz + ancho / 2), p,
                        rot=(ang, 0, -22.5 * lado), origen=(cx, cy, cz))
        self.m.cubo(g, f"{nombre}_centro", (cx - 0.6, cy - 0.6, cz - 0.6), (cx + 0.6, cy + 0.6, cz + 0.6),
                    metal(color, sem), origen=(cx, cy, cz))

    def acc_laurel(self, acc):
        col = acc["color"] or ORO
        sem = self.sem()
        g = "Head/laurel"
        x = (self.pelo_lado if hasattr(self, "pelo_lado") else self.hw / 2) + 1.2
        y = self.hy1 - 1.0
        for s in (1, -1):
            self.ramillete(g, f"laurel_{'d' if s > 0 else 'i'}", s * (x + 0.2), y, -self.hd / 2 + 2, col, sem + s, lado=s,
                           hojas=7, largo=3.2, ancho=1.4)
            self.ramillete(g, f"laurel_t{'d' if s > 0 else 'i'}", s * (x - 0.5), y + 1.5, self.hd / 2 - 1, col, sem + 3 * s,
                           hojas=4, largo=2.0, lado=s)

    def acc_flor(self, acc):
        sem = self.sem()
        x = getattr(self, "pelo_lado", self.hw / 2) + 0.2
        self.ramillete("Head/flor", "flor", x, self.hy1 - 2, -self.hd / 2 + 2.5, acc["color"] or "#E8832A", sem,
                       hojas=6, largo=2.0, ancho=1.6)

    def acc_corona(self, acc):
        sem = self.sem()
        oro = metal(acc["color"] or ORO, sem)
        top = getattr(self, "pelo_top", self.hy1)
        r = getattr(self, "pelo_lado", self.hw / 2) - 0.2
        zf, zb = -self.hd / 2 - 1.0, self.hd / 2 + 0.8
        g = "Head/corona"
        y1, y2 = top - 1.8, top + 0.2
        self.caja(g, "corona_frente", -r, y1, zf - 0.6, r, y2, zf, metal(acc["color"] or ORO, sem, gema=acc["color2"] or "#2E8A6E"))
        self.caja(g, "corona_atras", -r, y1, zb, r, y2, zb + 0.6, oro)
        self.par(g, "corona_lado", r - 0.6, y1, zf, r, y2, zb, oro)
        for k, x in enumerate((-r + 0.2, -1, r - 1.2)):
            alto = 3 if k == 1 else 2
            self.caja(g, f"punta{k}", x, y2, zf - 0.6, x + 1.0 + (k == 1), y2 + alto, zf, oro)
            self.caja(g, f"punta_a{k}", x, y2, zb, x + 1.0, y2 + 1.5, zb + 0.6, oro)
        self.par(g, "punta_lado", r - 0.6, y2, -0.6, r, y2 + 1.8, 0.6, oro)

    def acc_capucha(self, acc):
        """Capucha puesta: envuelve la cabeza y enmarca la cara."""
        sem = self.sem()
        col = acc["color"] or "#3A2A5A"
        p = tela(col, [col, acc["color2"] or col], "liso", Paleta(col).o, ("abajo",), sem=sem)
        hw, hd = self.hw / 2 + 1.0, self.hd / 2 + 1.0
        top = max(self.hy1 + 0.8, getattr(self, "pelo_top", self.hy1) + 0.3)
        g = "Head/capucha"
        self.caja(g, "capucha_arriba", -hw, top - 1.2, -hd, hw, top, hd, p)
        self.caja(g, "capucha_atras", -hw, self.hy0 - 1.5, hd - 1.0, hw, top - 1.2, hd, p)
        self.par(g, "capucha_lado", hw - 1.0, self.hy0 - 1.0, -hd, hw, top - 1.2, hd - 1.0, p)
        self.caja(g, "capucha_visera", -hw, top - 2.4, -hd - 0.6, hw, top - 1.0, -hd + 0.6, p,
                  rot=(-15, 0, 0), piv=(0, top - 1.2, -hd))
        self.caja(g, "capucha_punta", -1.5, self.hy0 - 2.5, hd - 0.5, 1.5, self.hy0, hd + 1.2, p,
                  rot=(15, 0, 0), piv=(0, self.hy0, hd))

    def acc_gorro(self, acc):
        """Gorro alto (tipo sombrero de erudito) con banda y emblema."""
        sem = self.sem()
        col = acc["color"] or "#1A1A1A"
        det = acc["color2"] or ORO
        top = getattr(self, "pelo_top", self.hy1)
        hw, hd = self.hw / 2 + 0.8, self.hd / 2 + 0.8
        g = "Head/gorro"
        self.caja(g, "gorro", -hw, top - 1.5, -hd, hw, top + 4, hd,
                  tela(col, ribete=det, bordes=("arriba",), sem=sem, pliegues=False))
        self.caja(g, "gorro_banda", -hw - 0.3, top - 1.7, -hd - 0.3, hw + 0.3, top - 0.2, hd + 0.3, metal(det, sem))
        self.caja(g, "gorro_emblema", -1.2, top + 0.5, -hd - 0.5, 1.2, top + 2.9, -hd, metal(det, sem, gema="#3FA7A6"))

    def acc_tiara(self, acc):
        sem = self.sem()
        oro = metal(acc["color"] or ORO, sem)
        zf = -self.hd / 2 - 1.1
        y = self.hy1 - 0.8
        g = "Head/tiara"
        self.caja(g, "tiara", -3.5, y, zf - 0.4, 3.5, y + 0.8, zf + 0.2, oro)
        self.par(g, "tiara_lado", 3.5, y - 0.6, zf - 0.3, 4.6, y + 0.4, zf + 1.8, oro, rot=(0, 0, 15), piv=(3.5, y, zf))
        self.caja(g, "tiara_punta", -0.9, y + 0.8, zf - 0.4, 0.9, y + 3, zf + 0.2, oro)
        self.caja(g, "tiara_gema", -0.6, y + 0.9, zf - 0.7, 0.6, y + 2.1, zf - 0.3,
                  metal(acc["color2"] or "#3A7BD5", sem))

    def acc_gafas(self, acc):
        sem = self.sem()
        p = metal(acc["color"] or ORO, sem)
        g = "Head/gafas"
        y0 = self.hy0 + (2 if self.hh <= 9 else 3)
        z1, z2 = -self.hd / 2 - 0.6, -self.hd / 2 - 0.15
        for s in (1, -1):
            xs = (0.6, 4.2)
            self.par(g, "gafa_arriba", xs[0], y0 + 2.9, z1, xs[1], y0 + 3.4, z2, p)
            self.par(g, "gafa_abajo", xs[0], y0 - 0.5, z1, xs[1], y0, z2, p)
            self.par(g, "gafa_int", xs[0], y0, z1, xs[0] + 0.5, y0 + 2.9, z2, p)
            self.par(g, "gafa_ext", xs[1] - 0.5, y0, z1, xs[1], y0 + 2.9, z2, p)
            self.par(g, "patilla", self.hw / 2, y0 + 2.4, -self.hd / 2, self.hw / 2 + 0.4, y0 + 2.9, 1, p)
            break
        self.caja(g, "puente", -0.6, y0 + 2.2, z1, 0.6, y0 + 2.7, z2, p)

    def acc_plumas(self, acc):
        sem = self.sem()
        cols = acc["colores"] or [acc["color"] or ORO, "#C2402E", "#3FA7A6", "#F1E2C6"]
        top = getattr(self, "pelo_top", self.hy1)
        g = "Head/plumas"
        angulos = (-67.5, -45, -22.5, 0, 22.5, 45, 67.5)
        for k, a in enumerate(angulos):
            c = cols[k % len(cols)]
            c2 = cols[(k + 1) % len(cols)]
            largo = 7 - abs(a) / 22.5
            x = math.sin(math.radians(a)) * 2.5
            self.caja(g, f"pluma{k}", x - 1.1, top - 1, 1.4, x + 1.1, top - 1 + largo, 1.6,
                      plano(c, [c2, c, c], sem=sem), rot=(-15, 0, -a), piv=(x, top - 1, 1.5))
        self.caja(g, "plumas_banda", -self.hw / 2 - 0.7, top - 2.2, -self.hd / 2 - 1.2, self.hw / 2 + 0.7, top - 1,
                  self.hd / 2 + 0.9, tela(cols[0], cols, "rayas", sem=sem, bordes=(), pliegues=False))

    def acc_etiquetas(self, acc):
        borde = acc["color"] or ORO
        fondo = acc["color2"] or "#1F2447"
        P, B = Paleta(fondo), Paleta(borde)

        def etiqueta(t):
            if t.cara not in ("north", "south"):
                return B.b
            if t.i == 0 or t.j == 0 or t.i == t.tw - 1 or t.j == t.th - 1:
                return B.l if t.j == 0 else B.b
            return B.h if (t.i == t.tw // 2 and t.j in (1, 2)) else P.b
        g = "Head/etiquetas"
        hw = self.hw / 2
        for k, (x, y, z, ry) in enumerate(((hw + 3, self.hy1 - 2, -1, -22.5), (-hw - 5.5, self.hy1, 0, 22.5),
                                            (hw + 2, self.hy1 + 3, 2.5, -45), (-hw - 4, self.hy1 + 4, 3, 45))):
            self.caja(g, f"etiqueta{k}", x, y, z, x + 2.5, y + 3.5, z + 0.5, etiqueta, rot=(0, ry, 7.5 * (-1) ** k),
                      piv=(x + 1.25, y + 1.75, z + 0.25))

    def cadena(self, g, nombre, base, angulos, largo, grosor, pintor, achica=0.8):
        """Segmentos encadenados que se curvan (cuernos, colas). angulos en grados sobre Z (y X)."""
        x, y, z = base
        ax = az = 0.0
        for k, (dz, dx) in enumerate(angulos):
            az += dz
            ax += dx
            w = grosor * (achica ** k)
            self.m.cubo(g, f"{nombre}{k}", (x - w / 2, y, z - w / 2), (x + w / 2, y + largo, z + w / 2), pintor,
                        rot=(ax, 0, az), origen=(x, y, z))
            rz, rx = math.radians(az), math.radians(ax)
            x += -math.sin(rz) * largo * 0.92
            y += math.cos(rz) * math.cos(rx) * largo * 0.92
            z += math.sin(rx) * largo * 0.92

    def acc_cuernos(self, acc):
        sem = self.sem()
        p = cuero(acc["color"] or "#E8DCC0", sem, costura=False)
        top = getattr(self, "pelo_top", self.hy1) - 1
        for s in (1, -1):
            self.cadena("Head/cuernos", f"cuerno_{s}", (s * (self.hw / 2 - 1.5), top, -0.5),
                        [(-22.5 * s, -7.5), (-22.5 * s, -7.5), (22.5 * s, -15)], 2.6, 2.2, p)

    def acc_orejas(self, acc):
        sem = self.sem()
        p = tela(acc["color"] or self.F["pelo"]["color"], sem=sem, bordes=(), pliegues=False)
        top = getattr(self, "pelo_top", self.hy1) - 1
        for s in (1, -1):
            self.cadena("Head/orejas", f"oreja_{s}", (s * (self.hw / 2 - 1.5), top, 0),
                        [(-15 * s, 0), (-7.5 * s, 0)], 2.5, 2.4, p, achica=0.6)

    # ------------------------------------------------------------------ extras
    def extras(self):
        for ex in self.F["extras"]:
            getattr(self, "ex_" + ex["tipo"], lambda a: None)(ex)

    def ex_amuletos(self, ex):
        sem = self.sem()
        cols = ex["colores"] or [ex["color"] or ORO, "#3FA7A6", "#C2402E", "#E3B04B"]
        td = self.td
        hilo = cuero("#3B2A1E", sem, costura=False)
        for k, x in enumerate((-3, -1.2, 1.2, 3)):
            largo = 2 + (k % 2) * 1.5
            z = -td / 2 - 1.3
            self.caja("Body/amuletos", f"hilo{k}", x - 0.2, self.lh - largo, z, x + 0.2, self.lh, z + 0.4, hilo,
                      rot=(0, 0, 7.5 * (-1) ** k), piv=(x, self.lh, z))
            c = cols[k % len(cols)]
            self.caja("Body/amuletos", f"amuleto{k}", x - 0.8, self.lh - largo - 1.8, z - 0.4, x + 0.8, self.lh - largo,
                      z + 0.6, metal(c, sem, gema=cols[(k + 1) % len(cols)]) if k % 2 else cuero(c, sem),
                      rot=(0, 0, 7.5 * (-1) ** k), piv=(x, self.lh, z))

    def ex_cintas(self, ex):
        sem = self.sem()
        p = tela(ex["color"] or "#E8832A", sem=sem, bordes=(), deshilachado=0.4)
        for s in (1, -1):
            x = s * (self.tw / 2 - 0.5)
            self.caja(("Right" if s > 0 else "Left") + "Leg/cintas", f"cinta_{s}", x - 0.6, self.lh - 7, -self.td / 2 - 1.2,
                      x + 0.6, self.lh, -self.td / 2 - 0.8, p, rot=(0, 0, 10 * s), piv=(x, self.lh, 0))

    def ex_emblema(self, ex):
        col = ex["color"] or ORO
        fondo = ex["color2"] or "#3B2A1E"
        forma = ex["forma"]
        C, Fd = Paleta(col), Paleta(fondo)

        def p(t):
            if t.cara != "north":
                return Fd.s
            cx, cy = t.i - (t.tw - 1) / 2, t.j - (t.th - 1) / 2
            on = {"sol": abs(cx) < 0.6 or abs(cy) < 0.6 or abs(abs(cx) - abs(cy)) < 0.6,
                  "cruz": abs(cx) < 0.6 or (abs(cy + 0.5) < 0.6),
                  "estrella": abs(cx) < 0.6 or abs(cy) < 0.6,
                  "hoja": abs(cx + cy * 0.6) < 0.9,
                  "luna": cx < 0.2 and abs(cy) < 1.6,
                  "ojo": abs(cy) < 0.6 and abs(cx) < 1.6}.get(forma, abs(cx) + abs(cy) < 1.6)
            if on:
                return C.h if (cx <= 0 and cy <= 0) else C.b
            return Fd.b if (t.i in (0, t.tw - 1) or t.j in (0, t.th - 1)) else Fd.s
        yc = self.lh + self.th * 0.55
        self.caja("Body/emblema", "emblema", -2, yc - 2, -self.td / 2 - 2.2, 2, yc + 2, -self.td / 2 - 1.6, p)

    def ex_bolsa(self, ex):
        sem = self.sem()
        x = -self.tw / 2
        self.caja("Body/bolsa", "bolsa", x - 1.5, self.lh - 3, -1.5, x + 0.5, self.lh + 0.5, 1.5, cuero(ex["color"] or "#6B4A2A", sem))

    def libres(self):
        for p in self.F["piezas_libres"]:
            pin = tela(p["color"], sem=self.sem(), bordes=()) if p["material"] in ("tela", "pelo") else (
                metal(p["color"]) if p["material"] in ("metal", "gema") else cuero(p["color"]))
            d, h = p["desde"], p["hasta"]
            g = f"{p['hueso']}/extra"
            if p["simetrica"]:
                self.m.par(g, p["nombre"], d, h, pin)
            else:
                self.m.cubo(g, p["nombre"], d, h, pin)

    # ------------------------------------------------------------------
    def construir(self):
        self.cuerpo()
        self.pelo3d()
        self.botas()
        self.tunica()
        self.mangas()
        self.manos()
        self.hombreras()
        self.pechera()
        self.correas()
        self.cinturon()
        self.banda()
        self.bufanda()
        self.capa()
        self.accesorios_cabeza()
        self.extras()
        self.libres()
        return self.m


def construir(ficha) -> Modelo:
    return Sastre(ficha).construir()


__all__ = ["construir", "Sastre", "TRANSPARENTE"]
