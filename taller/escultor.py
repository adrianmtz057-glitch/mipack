"""
Escultor de personajes en voxeles: ficha -> Voxeles -> Modelo (.bbmodel).

No es un Steve repintado: el cuerpo tiene proporciones propias (altura, cabeza, complexion) y la
ropa se construye por capas alrededor del cuerpo (anillos desplazados), con tiras sueltas,
solapas, pliegues, bufandas que envuelven, correas, hebillas y accesorios hechos voxel a voxel.

Ejes: frente = -Z, derecha del personaje = +X, pies en y = 0. 1 voxel = 1 px.
"""

import math

from .textura import azar, hex_a_rgba, mezcla, ruido, tono
from .voxel import Voxeles, anillo

ORO = "#E3B04B"


def _lerp(a, b, t):
    return a + (b - a) * t


# ============================================================================ telas


def tela(nombre, cols, sem, brillo=0.08):
    """Funcion color(x, y, z) de un estampado en voxeles. cols[0] = principal."""
    cols = [hex_a_rgba(c) for c in cols] or [hex_a_rgba("#888888")]
    c0 = cols[0]
    c1 = cols[1] if len(cols) > 1 else tono(c0, 0.86)
    c2 = cols[2] if len(cols) > 2 else c1
    c3 = cols[3] if len(cols) > 3 else tono(c0, 0.7)

    def jit(c, x, y, z):
        return tono(c, 1 + (azar(sem, x, y, z, 99) - 0.5) * brillo)

    def f(x, y, z):
        if nombre == "manchas":
            n = ruido(x, y * 0.75, z, 2.6, sem)
            r = azar(sem, x, y, z)
            if n < 0.46:
                c = c0 if r > 0.1 else c1
            elif n < 0.6:
                c = c1
            elif n < 0.8:
                c = c2
            else:
                c = c3 if r < 0.6 else c2
        elif nombre == "tiras":
            r = azar(sem, x, z, 7)
            c = c0 if r < 0.5 else (c1 if r < 0.8 else c2)
            if ruido(x, y, z, 3.0, sem) > 0.72:
                c = c3
        elif nombre == "camuflaje":
            n = ruido(x, y, z, 2.4, sem)
            m = ruido(x, y, z, 1.3, sem + 5)
            c = c0 if n < 0.45 else (c1 if n < 0.7 else c2)
            if m > 0.78:
                c = c3
        elif nombre == "paneles":
            banda = math.floor((x + 40) / 3)
            c = (c0, c1, c0, c2)[banda % 4]
        elif nombre == "estrellas":
            c = c0 if azar(sem, x, y, z) > 0.12 else tono(c0, 1.12)
            if azar(sem + 1, x, y, z) < 0.04:
                c = tono(c1, 1.15)
            elif any(azar(sem + 1, x + a, y + b, z + d) < 0.04 and azar(sem + 2, x + a, y + b, z + d) < 0.5
                     for a, b, d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                c = c1
        elif nombre == "hojas":
            n = ruido(x, y, z, 2.2, sem)
            c = c1 if n > 0.66 else (c2 if n < 0.28 else c0)
            if (x + y + z) % 4 == 0 and azar(sem, x // 2, y // 2, z // 2) < 0.3:
                c = c3
        elif nombre == "rayas":
            c = c1 if y % 3 == 0 else c0
        elif nombre == "cuadros":
            c = c1 if ((x // 2 + y // 2 + z // 2) % 2) else c0
            if azar(sem, x // 2, y // 2, z // 2) < 0.15:
                c = c2
        else:
            c = c0
        return jit(c, x, y, z)
    return f


def liso(color, sem, brillo=0.06):
    c = hex_a_rgba(color)
    return lambda x, y, z: tono(c, 1 + (azar(sem, x, y, z, 98) - 0.5) * brillo)


def metal(color, sem):
    c = hex_a_rgba(color)

    def f(x, y, z):
        r = azar(sem, x, y, z, 97)
        return tono(c, 1.3) if r < 0.12 else (tono(c, 0.8) if r > 0.85 else c)
    return f


# ============================================================================ escultor


class Escultor:
    def __init__(self, F):
        self.F = F
        self.v = Voxeles()
        self.semilla = int(azar(*[ord(c) for c in F["nombre"]]) * 1e6)
        self._s = 0
        self._medidas()

    def sem(self):
        self._s += 1
        return self.semilla + self._s * 131

    # ------------------------------------------------------------------ proporciones
    def _medidas(self):
        p = self.F["proporciones"]
        H = int(p["altura"])
        cab = p["cabeza"]
        comp = p["complexion"]
        hh = max(7, min(11, round(9 * cab)))
        hw = 10 if hh >= 9 else 8
        hd = hw - 1
        resto = max(10, H - hh)
        lh = round(resto * 0.56)
        th = resto - lh
        tw = {"delgada": 8, "normal": 8, "robusta": 10}[comp]
        tw = min(tw, hw)
        td = {"delgada": 4, "normal": 5, "robusta": 6}[comp]
        aw = {"delgada": 3, "normal": 4, "robusta": 5}[comp]
        if self.F["brazos"] == "finos":
            aw = max(3, aw - 1)
        self.hh, self.hw, self.hd, self.lh, self.th, self.tw, self.td, self.aw = hh, hw, hd, lh, th, tw, td, aw
        self.tx1 = tw // 2
        self.tz0 = -((td + 1) // 2)
        self.tz1 = self.tz0 + td
        self.cuello = lh + th                         # y del cuello = arriba del torso
        self.hy0, self.hy1 = self.cuello, self.cuello + hh
        self.hx1 = hw // 2
        self.hz0 = -((hd + 1) // 2)
        self.hz1 = self.hz0 + hd
        self.lw = tw // 2 - 1
        self.ld = td - 1
        self.lz0 = -((self.ld + 1) // 2)
        self.lz1 = self.lz0 + self.ld
        self.ad = 4
        self.az0 = -2
        self.ay0 = max(2, lh - 2)                      # las manos bajan un poco mas que el torso
        self.mano = 3
        self.pivotes = {
            "Head": (0, self.cuello, 0), "Body": (0, self.cuello, 0),
            "RightArm": (self.tx1 + aw / 2, self.cuello - 2, 0), "LeftArm": (-(self.tx1 + aw / 2), self.cuello - 2, 0),
            "RightLeg": (self.lw / 2, lh, 0), "LeftLeg": (-self.lw / 2, lh, 0),
        }

    # ------------------------------------------------------------------ utilidades
    def lado(self, s, x):
        """Celda x del lado derecho (x >= 0) llevada al lado s (1 der, -1 izq)."""
        return x if s > 0 else -x - 1

    def hueso_lado(self, base, s):
        return ("Right" if s > 0 else "Left") + base

    def frente(self, x, y, desde=-30):
        """Primera z libre delante de lo que haya en la columna (x, y)."""
        for z in range(desde, 30):
            if (x, y, z) in self.v.c:
                return z - 1
        return None

    def atras(self, x, y):
        for z in range(30, -30, -1):
            if (x, y, z) in self.v.c:
                return z + 1
        return None

    def seccion_torso(self):
        return {(x, z) for x in range(-self.tx1, self.tx1) for z in range(self.tz0, self.tz1)}

    def seccion_piernas(self):
        return {(x, z) for x in range(-self.lw, self.lw) for z in range(self.lz0, self.lz1)}

    def seccion_brazo(self, s):
        xs = [self.lado(s, x) for x in range(self.tx1, self.tx1 + self.aw)]
        return {(x, z) for x in xs for z in range(self.az0, self.az0 + self.ad)}

    # ------------------------------------------------------------------ cuerpo
    def cuerpo(self):
        F, v = self.F, self.v
        r = F["ropa"]
        sem = self.sem()
        piel = liso(F["piel"], sem, 0.05)
        camisa = tela(r["camisa"].get("patron", "liso"), [r["camisa"]["color"], tono(r["camisa"]["color"], 0.85)], sem)
        pantalon = liso(r["pantalon"]["color"], sem)
        # piernas
        for s in (1, -1):
            xs = sorted(self.lado(s, x) for x in range(0, self.lw))
            v.caja(xs[0], 0, self.lz0, xs[-1] + 1, self.lh, self.lz1, pantalon, self.hueso_lado("Leg/pierna", s))
        # torso
        v.caja(-self.tx1, self.lh, self.tz0, self.tx1, self.cuello, self.tz1, camisa, "Body/torso")
        # brazos
        guantes = r["guantes"]
        for s in (1, -1):
            xs = sorted(self.lado(s, x) for x in range(self.tx1, self.tx1 + self.aw))
            g = self.hueso_lado("Arm/brazo", s)
            v.caja(xs[0], self.ay0 + self.mano, self.az0, xs[-1] + 1, self.cuello, self.az0 + self.ad, camisa, g)
            mano = liso(guantes["color"], sem) if guantes else piel
            v.caja(xs[0], self.ay0, self.az0, xs[-1] + 1, self.ay0 + self.mano, self.az0 + self.ad, mano, g)
            if guantes and guantes.get("sin_dedos", True):
                for x in xs:                          # dedos asomando abajo
                    for z in range(self.az0, self.az0 + self.ad):
                        if z == self.az0 or x == (xs[0] if s > 0 else xs[-1]):
                            v.poner(x, self.ay0, z, piel(x, self.ay0, z), g)
        # cabeza
        v.caja(-self.hx1, self.hy0, self.hz0, self.hx1, self.hy1, self.hz1, self.color_cabeza(piel), "Head/cabeza")

    def color_cabeza(self, piel):
        F = self.F
        pelo = hex_a_rgba(F["pelo"]["color"])
        estilo = F["pelo"]["estilo"]
        hz0, hy0 = self.hz0, self.hy0

        def f(x, y, z):
            fila = y - hy0                             # 0 = menton
            if z == hz0:
                return self.cara(x, fila, piel)
            if estilo != "ninguno" and (fila >= self.hh - 2 or (z > hz0 + 2 and fila >= 2)):
                return tono(pelo, 0.9)
            return piel(x, y, z)
        return f

    def cara(self, x, fila, piel):
        F = self.F
        cara = F["cara"]
        ojos = hex_a_rgba(cara["ojos"])
        exp = cara["expresion"]
        pelo = hex_a_rgba(F["pelo"]["color"])
        estilo = F["pelo"]["estilo"]
        hh = self.hh
        y0 = max(2, round(hh * 0.3))                  # fila baja de los ojos
        ew = 3 if self.hw >= 10 else 2
        # columnas de los ojos: ojo derecho del personaje en x >= 1, izquierdo espejado
        k = None
        if 1 <= x < 1 + ew:
            k, lado = x - 1, 1
        elif -1 - ew <= x < -1:
            k, lado = -2 - x, -1
        pestana = tono(pelo, 0.55) if estilo != "ninguno" else (25, 18, 18, 255)
        blanco = (244, 240, 232, 255)

        if cara["mascara"]:
            m = hex_a_rgba(cara["mascara"])
            if k is not None and k < 2 and y0 + 1 <= fila <= y0 + 2:
                return tono(ojos, 1.35) if fila == y0 + 2 else ojos
            if k is not None and k < 2 and fila == y0:
                return tono(ojos, 0.6)
            return tono(m, 1 + (azar(x, fila, 5) - 0.5) * 0.08)

        if estilo != "ninguno":
            if fila >= hh - 2 or (fila >= y0 + 3 and azar(x, 17) < (0.75 if fila == y0 + 3 else 0.9)):
                return tono(pelo, 0.95 if fila >= hh - 2 else 0.8)
            if fila >= y0 + 2 and abs(x + 0.5) >= self.hx1 - 1:
                return tono(pelo, 0.9)               # patillas
        if k is not None and y0 <= fila <= y0 + 2:
            if exp == "traviesa" and lado == -1:      # guino
                return pestana if fila == y0 + 1 else piel(x, fila, 0)
            if fila == y0 + 2:
                return pestana
            if exp == "seria" and fila == y0 + 1 and k == ew - 1:
                return pestana
            if fila == y0 + 1:
                return blanco if k == ew - 1 else (tono(ojos, 1.5) if k == ew - 2 else tono(ojos, 0.7))
            return tono(ojos, 1.15) if k == 0 else ojos
        if exp == "seria" and k is not None and fila == y0 + 3:
            return tono(pelo, 0.85)                    # cejas
        if F["cara"]["rubor"] and fila == y0 - 1 and k is not None and k == ew - 1:
            return mezcla(piel(x, fila, 0), (235, 120, 120, 255), 0.4)
        if fila == y0 - 1:
            sonrisa = {"alegre": (-1, 0), "traviesa": (0, 1), "serena": (-1, 0), "seria": (-1, 0)}[exp]
            if x in sonrisa:
                return tono(F["piel"], 0.55 if exp in ("alegre", "traviesa") else 0.75)
        return piel(x, fila, 0)

    # ------------------------------------------------------------------ pelo
    def pelo(self):
        F, v = self.F, self.v
        P = F["pelo"]
        est = P["estilo"]
        if est == "ninguno":
            return
        sem = self.sem()
        vol = P["volumen"]
        hx0, hx1, hy0, hy1, hz0, hz1 = -self.hx1, self.hx1, self.hy0, self.hy1, self.hz0, self.hz1
        arriba = {1: 1.4, 2: 2.3, 3: 3.1}[vol]
        lado = {1: 1.0, 2: 1.6, 3: 2.3}[vol]
        amp = {"rizos": 2.6, "revuelto": 2.2, "puntas": 1.4, "lado": 1.0, "largo": 0.8, "corto": 0.7}[est]
        y_lado = hy0 + (3 if est != "largo" else -1)
        y_atras = hy0 + (1 if est != "largo" else -1)
        celdas = set()
        for x in range(hx0 - 5, hx1 + 5):
            for y in range(hy0 - 2, hy1 + 6):
                for z in range(hz0, hz1 + 5):
                    if hx0 <= x < hx1 and hy0 <= y < hy1 and hz0 <= z < hz1:
                        continue
                    cx, cy, cz = x + 0.5, y + 0.5, z + 0.5
                    dx = max(hx0 - cx, 0, cx - hx1)
                    dy = max(hy0 - cy, 0, cy - hy1)
                    dz = max(0, cz - hz1)
                    d = math.sqrt(dx * dx + dy * dy + dz * dz)
                    n = ruido(x, y * 0.8, z, 2.0, sem)
                    if cy > hy1:
                        T = arriba
                    elif cz > hz1:
                        T = lado + 0.4
                        if cy < y_atras:
                            continue
                    else:
                        T = lado
                        if cy < y_lado and not (est == "largo"):
                            continue
                        if cz < hz0 + 2 and cy < hy1 - 2 and est != "largo":
                            T = min(T, 1.0)            # delante de la oreja: mas fino
                    T += (n - 0.5) * amp
                    if cy > hy1 and (abs(cx) > self.hx1 - 1.5 or cz < hz0 + 1.5 or cz > hz1 - 1.5):
                        T -= 0.9                       # esquinas de arriba redondeadas
                    if est == "lado" and cy > hy1 and x > 0:
                        T += 0.6
                    if 0 < d <= T:
                        celdas.add((x, y, z))
        # mechones sobre la frente
        y_ojos = hy0 + max(2, round(self.hh * 0.3)) + 2
        for x in range(hx0, hx1):
            borde = x == hx0 or x == hx1 - 1
            r = azar(sem, x, 3)
            largo = 1 + int(r * (3 if est in ("rizos", "revuelto") else 2))
            if est == "lado":
                largo = 1 + int((x - hx0) / (hx1 - hx0) * 4)
            if est == "puntas":
                largo = 3 if x % 2 == 0 else 1
            if est == "corto":
                largo = 1
            ymin = hy0 + 2 if borde else y_ojos + 1
            for y in range(max(ymin, hy1 - largo), hy1 + int(arriba)):
                celdas.add((x, y, hz0 - 1))
            if est in ("rizos", "revuelto") and azar(sem, x, 4) < 0.45:
                celdas.add((x, hy1 - 1, hz0 - 2))
                celdas.add((x, hy1, hz0 - 2))
        if est == "largo":                             # melena por la espalda y mechones al frente
            for x in range(hx0 - 1, hx1 + 1):
                fondo = hy0 - 6 - int(azar(sem, x, 8) * 3)
                for y in range(fondo, hy0 + 2):
                    for z in range(hz1 - 1, hz1 + 1):
                        if not (hx0 <= x < hx1 and hy0 <= y and z < hz1):
                            celdas.add((x, y, z))
            for s in (1, -1):
                x = hx1 if s > 0 else hx0 - 1
                for y in range(hy0 - 3, hy1 - 1):
                    for z in range(hz0, hz0 + 3):
                        celdas.add((x, y, z))
        if est == "puntas":
            for k in range(7):
                ang = k / 7 * math.pi * 2
                px = round(math.cos(ang) * (self.hx1 - 1))
                pz = round(math.sin(ang) * (self.hd / 2 - 1)) + (hz0 + hz1) // 2
                alto = 2 + int(azar(sem, k) * 3)
                for j in range(alto):
                    celdas.add((px + round(math.cos(ang) * j * 0.6), hy1 + int(arriba) + j, pz + round(math.sin(ang) * j * 0.6)))
        # el cuerpo no se tapa (los mechones bajos no atraviesan el torso)
        celdas = {c for c in celdas if c not in v.c}
        color = hex_a_rgba(P["color"])
        brillo = hex_a_rgba(P["brillo"]) if P["brillo"] else tono(color, 1.45)
        mechas = hex_a_rgba(P["mechas"]) if P["mechas"] else None
        for (x, y, z) in celdas:
            r = azar(sem, x, z, 11)
            c = tono(color, 0.8) if r < 0.25 else (tono(color, 1.15) if r > 0.85 else color)
            if (x, y + 1, z) not in celdas and azar(sem, x, y, z) < 0.35:
                c = brillo
            if mechas and (x, y - 1, z) not in celdas and y < hy1 and azar(sem, x, y, z, 2) < 0.6:
                c = mechas
            c = tono(c, 1 + (azar(sem, x, y, z, 5) - 0.5) * 0.1)
            v.poner(x, y, z, c, "Head/pelo", pisar=False)
        self.celdas_pelo = celdas

    def superficie_pelo(self, x, y, z, d):
        """Avanza desde (x, y, z) en direccion d hasta salir del pelo/cabeza. Devuelve la primera celda libre."""
        p = [x, y, z]
        for _ in range(12):
            if tuple(p) not in self.v.c:
                return tuple(p)
            p = [p[i] + d[i] for i in range(3)]
        return tuple(p)

    # ------------------------------------------------------------------ ropa
    def tunica(self):
        F, v = self.F, self.v
        tu = F["ropa"]["tunica"]
        if not tu:
            return
        sem = self.sem()
        col = tela(tu["patron"], tu["colores"], sem)
        ribete = hex_a_rgba(tu["ribete"] or tono(tu["colores"][0], 0.7))
        panel = liso(tu["panel"], sem) if tu.get("panel") else None
        ab = 2.0 if tu["abierta"] else 0.0
        oscuro = tono(tu["colores"][0], 0.7)

        # ---- parte alta (torso)
        sec = self.seccion_torso()
        aro = anillo(sec, 0, 1.0)
        for y in range(self.lh, self.cuello + 1):
            arriba = self.cuello - y
            abertura = ab + (max(0, 3 - arriba) * 0.6 if ab else 0)       # escote en V
            for (x, z) in aro:
                if y == self.cuello and abs(x + 0.5) < self.hx1 - 1 and self.tz0 <= z < self.tz1:
                    continue
                if ab and z < self.tz0 and abs(x + 0.5) < abertura:
                    continue
                borde = ab and z < self.tz0 and abs(x + 0.5) < abertura + 1
                c = ribete if borde else col(x, y, z)
                v.poner(x, y, z, c, "Body/tunica", pisar=False)
                if not borde and y < self.cuello - 1 and azar(sem, x, y, z, 23) < 0.13:
                    nx = 1 if x >= self.tx1 else (-1 if x < -self.tx1 else 0)
                    nz = 1 if z >= self.tz1 else (-1 if z < self.tz0 else 0)
                    v.poner(x + nx, y, z + nz, tono(c, 1.07), "Body/tunica", pisar=False)
            if y == self.cuello:                           # hombros
                for (x, z) in sec:
                    if abs(x + 0.5) >= 2.5:
                        v.poner(x, y, z, col(x, y, z), "Body/tunica", pisar=False)
        if ab:                                             # solapas en relieve
            for y in range(self.lh + 2, self.cuello + 1):
                arriba = self.cuello - y
                abertura = ab + max(0, 3 - arriba) * 0.6
                for s in (1, -1):
                    x = self.lado(s, math.ceil(abertura - 0.5))
                    v.poner(x, y, self.tz0 - 2, ribete if y % 3 else tono(ribete, 1.2), "Body/tunica")

        # ---- falda (en las piernas para que se mueva al caminar)
        bota = F["ropa"]["botas"]["alto"]
        fondo = {"corta": round(self.lh * 0.6), "media": round(self.lh * 0.35), "larga": bota + 1}[tu["largo"]]
        sec = self.seccion_piernas()
        tiras = tu.get("borde", "tiras")
        for y in range(fondo, self.lh):
            t = (self.lh - y) / max(1, self.lh - fondo)
            d = 1.0 + round(t * 1.6)
            aro = anillo(sec, d - 1.0, d)
            abertura = (ab + t * 1.5) if ab else 0
            for (x, z) in aro:
                if z < self.lz0 and abertura and abs(x + 0.5) < abertura:
                    if panel:
                        v.poner(x, y, self.lz0 - 1, panel(x, y, z), ("Right" if x >= 0 else "Left") + "Leg/panel", pisar=False)
                    continue
                c = ribete if (z < self.lz0 and abertura and abs(x + 0.5) < abertura + 1) else col(x, y, z)
                g = ("Right" if x >= 0 else "Left") + "Leg/tunica"
                v.poner(x, y, z, c, g, pisar=False)
                # solapas sueltas: tiras que se separan del cuerpo
                if t > 0.25 and azar(sem, x, z, 21) < 0.22 and not (z < self.lz0 and abertura and abs(x + 0.5) < abertura + 1.5):
                    nx = (x > 0) - (x < -1) if abs(x + 0.5) > self.lw else 0
                    nz = -1 if z < self.lz0 else (1 if z >= self.lz1 else 0)
                    v.poner(x + nx, y, z + nz, tono(col(x, y, z), 1.06), g, pisar=False)
        # borde inferior: tiras de distinto largo
        if tiras != "recto":
            filas = {}
            for (x, y, z), (cc, g) in list(v.c.items()):
                if "Leg/tunica" in g or "Leg/panel" in g:
                    if (x, z) not in filas or y < filas[(x, z)][0]:
                        filas[(x, z)] = (y, cc, g)
            for (x, z), (y, cc, g) in filas.items():
                if tiras == "picos":
                    largo = (abs(x) + abs(z)) % 3
                else:
                    largo = int(azar(sem, x, z, 31) * 4.5)
                if y > fondo + 1:
                    continue
                for k in range(1, largo + 1):
                    if y - k < 0:
                        break
                    cc2 = col(x, y - k, z) if "panel" not in g else cc
                    if k == largo:
                        cc2 = tono(cc2, 0.85)
                    v.poner(x, y - k, z, cc2, g, pisar=False)
        self.fondo_tunica = fondo
        self.oscuro_tunica = oscuro

    def mangas(self):
        F, v = self.F, self.v
        r = F["ropa"]
        mg = r["mangas"]
        if not mg and not r["tunica"]:
            return
        if not mg:
            tu = r["tunica"]
            mg = {"color": tu["colores"][0], "color2": tu["colores"][-1], "forma": "ajustadas", "patron": tu["patron"]}
        sem = self.sem()
        cols = [mg["color"], mg["color2"]] + ([ORO] if mg["patron"] == "estrellas" else [])
        if r["tunica"] and mg["patron"] in ("manchas", "tiras", "camuflaje"):
            cols = [mg["color"], mg["color2"]] + r["tunica"]["colores"][1:]
        col = tela(mg["patron"], cols, sem)
        ribete = hex_a_rgba((r["tunica"] and r["tunica"]["ribete"]) or tono(mg["color2"], 0.8))
        base = self.ay0 + self.mano
        for s in (1, -1):
            sec = self.seccion_brazo(s)
            g = self.hueso_lado("Arm/manga", s)
            for y in range(base, self.cuello + 1):
                t = (self.cuello - y) / max(1, self.cuello - base)
                if mg["forma"] == "anchas":
                    d = 1.0 + (1.0 if t > 0.55 else 0) + (0.5 if t > 0.85 else 0)
                elif mg["forma"] == "capas":
                    d = 1.0 + (1.0 if (t > 0.45 and (y - base) % 4 < 2) else 0)
                else:
                    d = 1.0
                for (x, z), dist in anillo(sec, 0, d).items():
                    if s > 0 and x < self.tx1 and z >= self.tz0 - 1 and z < self.tz1 + 1 and y > self.lh:
                        continue                          # no atraviesa el torso
                    if s < 0 and x >= -self.tx1 and z >= self.tz0 - 1 and z < self.tz1 + 1 and y > self.lh:
                        continue
                    c = ribete if y == base else col(x, y, z)
                    v.poner(x, y, z, c, g, pisar=False)
            if mg["forma"] in ("anchas", "capas"):           # puño deshilachado
                for (x, z) in anillo(sec, 1.0, 2.5):
                    if azar(sem, x, z, 41) < 0.5:
                        v.poner(x, base - 1, z, tono(col(x, base, z), 0.9), g, pisar=False)
            for (x, z) in sec:                                # hombro abultado
                v.poner(x, self.cuello, z, col(x, self.cuello, z), g, pisar=False)

    def bufanda(self):
        F, v = self.F, self.v
        bu = F["ropa"]["bufanda"]
        if not bu:
            return
        sem = self.sem()
        col = tela("manchas", [bu["color"], tono(bu["color"], 1.08), bu["color2"], tono(bu["color2"], 0.8)], sem)
        grande = bu["tamano"] == "grande"
        T = 2.6 if grande else 1.6
        g = "Body/bufanda"
        cuello = {(x, z) for x in range(-self.hx1 + 1, self.hx1 - 1) for z in range(self.tz0, self.tz1)}
        cabeza = {(x, z) for x in range(-self.hx1, self.hx1) for z in range(self.hz0, self.hz1)}
        filas = range(self.cuello - (3 if grande else 2), self.cuello + 1)
        for y in filas:
            sec = cabeza if y >= self.cuello else cuello
            grosor = T if y < self.cuello else T - 1.2
            for (x, z), d in anillo(sec, 0, grosor + 0.7).items():
                if d > grosor + (ruido(x, y, z, 1.6, sem) - 0.5) * 1.4:
                    continue
                c = col(x, y, z)
                if (y + (x + z) // 3) % 3 == 0:
                    c = tono(c, 0.88)                      # vueltas de la tela
                v.poner(x, y, z, c, g, pisar=False)
        if not bu["colas"]:
            return
        largas = bu.get("largo") == "largo"
        fin_frente = self.lh - (4 if largas else 0) if grande else self.lh + self.th // 2
        x0 = 1
        y = self.cuello - 2
        while y >= fin_frente:                              # cola delantera (cae y se abre)
            paso = (self.cuello - y) // 4
            for x in range(x0 + paso // 2, x0 + 3 + paso // 2):
                zf = self.frente(x, y)
                if zf is not None:
                    v.poner(x, y, zf, col(x, y, zf), g if y >= self.lh else "RightLeg/bufanda")
                    if grande and (x + y) % 3 == 0:
                        v.poner(x, y, zf - 1, tono(col(x, y, zf), 1.05), g if y >= self.lh else "RightLeg/bufanda")
            y -= 1
        for x in range(x0, x0 + 3):                         # punta deshilachada
            if azar(sem, x, 51) < 0.6:
                zf = self.frente(x, fin_frente - 1)
                if zf is not None:
                    v.poner(x, fin_frente - 1, zf, col(x, fin_frente, zf), "RightLeg/bufanda" if fin_frente - 1 < self.lh else g)
        if grande:                                         # cola trasera sobre el hombro
            fin = self.lh - (6 if largas else 1)
            for y in range(fin, self.cuello):
                for x in range(-4, 0):
                    za = self.atras(x, y)
                    if za is not None:
                        gg = g if y >= self.lh else "LeftLeg/bufanda"
                        v.poner(x, y, za, col(x, y, za), gg)
            for x in range(-4, 0):
                if azar(sem, x, 52) < 0.5:
                    za = self.atras(x, fin - 1)
                    if za is not None:
                        v.poner(x, fin - 1, za, col(x, fin, za), "LeftLeg/bufanda")

    def capa(self):
        F, v = self.F, self.v
        ca = F["ropa"]["capa"]
        if not ca:
            return
        sem = self.sem()
        cols = [ca["color"], ca["color2"]] + ([ORO] if ca["patron"] == "estrellas" else [tono(ca["color"], 0.8)])
        if ca["patron"] == "estrellas":
            cols = [ca["color"], ORO, ca["color2"]]
        col = tela(ca["patron"], cols, sem)
        fondo = {"corta": self.lh, "media": round(self.lh * 0.45), "larga": 1}[ca["largo"]]
        g = "Body/capa"
        for y in range(fondo, self.cuello + 1):
            t = (self.cuello - y) / max(1, self.cuello - fondo)
            ancho = self.tx1 + 1 + round(t * 2)
            for x in range(-ancho, ancho):
                za = max(self.tz1 + 1, (self.atras(x, y) or self.tz1))
                if y >= self.lh - 1:
                    za = max(za, self.atras(x, y) or za)
                v.poner(x, y, za, col(x, y, za), g)
                if azar(sem, x, 61) < 0.3 and t > 0.3:
                    v.poner(x, y, za + 1, tono(col(x, y, za), 1.06), g)
        for x in range(-self.tx1 - 3, self.tx1 + 3):          # bajo deshilachado
            for k in range(1, 1 + int(azar(sem, x, 62) * 3)):
                if fondo - k >= 0:
                    za = self.atras(x, fondo) or self.tz1 + 1
                    v.poner(x, fondo - k, za - 1, col(x, fondo - k, za), g, pisar=False)
        for s in (1, -1):                                     # caida sobre los hombros
            for x in range(self.tx1 - 1, self.tx1 + self.aw + 1):
                xx = self.lado(s, x)
                for z in range(self.az0 - 1, self.tz1 + 2):
                    v.poner(xx, self.cuello + 1, z, col(xx, self.cuello + 1, z), self.hueso_lado("Arm/capa", s), pisar=False)
        if ca["capucha"]:
            zc = self.hz1
            for x in range(-self.hx1 + 1, self.hx1 - 1):
                for y in range(self.cuello - 2, self.cuello + 3):
                    for z in range(zc, zc + 3):
                        if abs(x + 0.5) + (z - zc) * 1.5 + abs(y - self.cuello) * 0.8 < self.hx1 + 1:
                            v.poner(x, y, z, col(x, y, z), "Body/capa", pisar=False)

    def cinturon(self):
        F, v = self.F, self.v
        ci = F["ropa"]["cinturon"]
        if not ci:
            return
        sem = self.sem()
        cuero = liso(ci["color"], sem, 0.12)
        oro = metal(ci["hebilla"], sem)
        g = "Body/cinturon"
        sec = self.seccion_torso()
        for y in (self.lh, self.lh + 1):
            for (x, z) in anillo(sec, 0, 2.0):
                k = (x, y, z)
                if k in v.c and v.c[k][1].startswith("Body/tunica") or k not in v.c:
                    if anillo is not None and (k not in v.c or True):
                        v.poner(x, y, z, cuero(x, y, z), g)
        zf = self.tz0 - 3
        v.caja(-1, self.lh, zf + 1, 1, self.lh + 2, zf + 2, oro, g)           # hebilla
        if ci.get("bolsas", True):
            for s in (1, -1):
                x = self.lado(s, self.tx1 - 3)
                v.caja(min(x, x + s * 2), self.lh - 2, self.tz0 - 3, max(x, x + s * 2) + 1, self.lh, self.tz0 - 1, cuero, g, pisar=False)
                v.poner(x, self.lh - 1, self.tz0 - 4, oro(x, 0, 0), g)
            for x in (-3, 2):                                  # correas colgando
                for y in range(self.lh - 3, self.lh):
                    v.poner(x, y, self.tz1 + 2, cuero(x, y, 0), g, pisar=False)

    def correas(self):
        F, v = self.F, self.v
        co = F["ropa"]["correas"]
        if not co:
            return
        sem = self.sem()
        cuero = liso(co["color"], sem, 0.12)
        oro = metal(co["detalle"], sem)
        g = "Body/correas"
        for y in range(self.lh + 2, self.cuello):
            t = (y - self.lh - 2) / max(1, self.cuello - self.lh - 3)
            for s in (1, -1):
                x = round(_lerp(-self.tx1 + 1, self.tx1 - 2, t)) * s - (1 if s < 0 else 0)
                for zfun in (self.frente, None):
                    if zfun:
                        z = self.frente(x, y)
                    else:
                        z = self.atras(x, y)
                    if z is None:
                        continue
                    c = oro(x, y, z) if (zfun and (y - self.lh) % 6 == 3) else cuero(x, y, z)
                    v.poner(x, y, z, c, g)

    def banda(self):
        F, v = self.F, self.v
        b = F["ropa"]["banda"]
        if not b:
            return
        sem = self.sem()
        c1 = liso(b["color"], sem)
        c2 = liso(b["detalle"], sem)
        for y in range(self.lh, self.cuello + 1):
            t = (y - self.lh) / max(1, self.th)
            xc = round(_lerp(-self.tx1, self.tx1 - 1, t))
            for x in (xc - 1, xc):
                for zf in (self.frente(x, y), self.atras(x, y)):
                    if zf is not None:
                        v.poner(x, y, zf, c2(x, y, zf) if x == xc - 1 else c1(x, y, zf), "Body/banda")

    def hombreras(self):
        F, v = self.F, self.v
        ho = F["ropa"]["hombreras"]
        if not ho:
            return
        sem = self.sem()
        c = liso(ho["color"], sem, 0.12)
        d = metal(ho["detalle"], sem)
        for s in (1, -1):
            g = self.hueso_lado("Arm/hombrera", s)
            xs = sorted(self.lado(s, x) for x in range(self.tx1 - 1, self.tx1 + self.aw + 2))
            v.caja(xs[0], self.cuello - 2, self.az0 - 2, xs[-1] + 1, self.cuello + 2, self.az0 + self.ad + 2, c, g)
            xs2 = sorted(self.lado(s, x) for x in range(self.tx1 + 1, self.tx1 + self.aw + 3))
            v.caja(xs2[0], self.cuello - 4, self.az0 - 2, xs2[-1] + 1, self.cuello - 2, self.az0 + self.ad + 2, d, g)
            xo = self.lado(s, self.tx1 + self.aw + 2)
            v.caja(xo, self.cuello - 1, -1, xo + 1, self.cuello + 1, 1, d, g)

    def guantes(self):
        F, v = self.F, self.v
        gu = F["ropa"]["guantes"]
        b = F["ropa"]["brazaletes"]
        sem = self.sem()
        y = self.ay0 + self.mano
        for s in (1, -1):
            sec = self.seccion_brazo(s)
            if gu:
                g = self.hueso_lado("Arm/guante", s)
                for (x, z) in anillo(sec, 0, 1.0):
                    v.poner(x, y, z, metal(gu["detalle"], sem)(x, y, z), g)
                    v.poner(x, y - 1, z, liso(gu["color"], sem)(x, y, z), g, pisar=False)
            elif b:
                g = self.hueso_lado("Arm/brazalete", s)
                for (x, z) in anillo(sec, 0, 1.0):
                    v.poner(x, y, z, metal(b, sem)(x, y, z), g, pisar=False)

    def botas(self):
        F, v = self.F, self.v
        b = F["ropa"]["botas"]
        sem = self.sem()
        alto = b["alto"]
        cuero = liso(b["color"], sem, 0.12)
        ribete = metal(b["ribete"], sem) if b["ribete"] else liso(tono(b["color"], 1.2), sem)
        hebilla = metal(b.get("hebillas") or ORO, sem) if b.get("hebillas") else None
        for s in (1, -1):
            g = self.hueso_lado("Leg/bota", s)
            xs = sorted(self.lado(s, x) for x in range(0, self.lw))
            sec = {(x, z) for x in xs for z in range(self.lz0, self.lz1)}
            for y in range(0, alto):
                for (x, z) in anillo(sec, 0, 1.0):
                    if s > 0 and x < 0 or s < 0 and x >= 0:
                        continue
                    c = cuero(x, y, z)
                    if y == alto - 1:
                        c = ribete(x, y, z)
                    if y == 0:
                        c = tono(b["color"], 0.6)
                    v.poner(x, y, z, c, g)
                for (x, z) in sec:
                    v.poner(x, y, z, tono(b["color"], 0.6) if y == 0 else cuero(x, y, z), g)
            for y in range(0, 2):                             # puntera
                for x in xs:
                    v.poner(x, y, self.lz0 - 2, tono(b["color"], 0.85 if y else 0.6), g)
            if hebilla:
                yh = max(1, alto // 2)
                for (x, z) in anillo(sec, 0, 1.0):              # correa de la bota
                    if (s > 0 and x < 0) or (s < 0 and x >= 0):
                        continue
                    v.poner(x, yh, z, tono(b["color"], 1.35), g)
                xo = self.lado(s, self.lw)                     # hebilla al costado de afuera
                v.caja(xo, yh - 1, -1, xo + 1, yh + 1, 1, hebilla, g)

    # ------------------------------------------------------------------ cabeza
    def accesorios_cabeza(self):
        for acc in self.F["cabeza"]:
            getattr(self, "acc_" + acc["tipo"], lambda a: None)(acc)

    def ramillete(self, centro, color, n_hojas, largo, sem, g, plano="yz"):
        """Grupo de hojas que salen de un centro (laurel / flores doradas)."""
        v = self.v
        c = hex_a_rgba(color)
        cx, cy, cz = centro
        for k in range(n_hojas):
            ang = (k / n_hojas) * math.pi * 2 + azar(sem, k) * 0.5
            if math.sin(ang) > 0.8:                        # nada de palitos para arriba
                ang += 0.9
            L = largo + (k % 2)
            for j in range(1, L + 1):
                if plano in ("+x", "-x"):                  # abanico 3D que se abre hacia afuera
                    sx = 1 if plano == "+x" else -1
                    p = (cx + sx * round(j * 0.6), cy + round(math.sin(ang) * j), cz + round(math.cos(ang) * j))
                elif plano == "yz":
                    p = (cx, cy + round(math.sin(ang) * j), cz + round(math.cos(ang) * j))
                else:
                    p = (cx + round(math.cos(ang) * j), cy + round(math.sin(ang) * j), cz)
                col = tono(c, 1.25) if j == L else (c if j > 1 else tono(c, 0.85))
                v.poner(*p, col, g)
                if 1 <= j < L or L == 1:                       # hoja de 2 px de ancho
                    perp = (0, 1, 0) if abs(math.cos(ang)) > abs(math.sin(ang)) else (0, 0, 1)
                    v.poner(p[0] + perp[0], p[1] + perp[1], p[2] + perp[2], tono(c, 0.92), g)
        v.poner(cx, cy, cz, tono(c, 0.75), g)

    def acc_laurel(self, acc):
        sem = self.sem()
        col = acc["color"] or ORO
        g = "Head/hojas"
        y = self.hy1 - 1
        for s in (1, -1):
            x = self.lado(s, self.hx1 - 1)
            sup = self.superficie_pelo(x, y - 1, self.hz0 + 2, (s, 0, 0))
            self.ramillete(sup, col, 7, 1, sem + s, g, "+x" if s > 0 else "-x")
            sup2 = self.superficie_pelo(self.lado(s, self.hx1 - 1), self.hy1 + 1, self.hz1 - 2, (s, 0, 0))
            self.ramillete(sup2, col, 5, 1, sem + 3 * s, g, "+x" if s > 0 else "-x")


    def acc_flor(self, acc):
        sem = self.sem()
        x = self.hx1 - 1
        sup = self.superficie_pelo(x, self.hy1 - 2, self.hz0 + 2, (1, 0, 0))
        self.ramillete(sup, acc["color"] or "#E8832A", 6, 2, sem, "Head/flor", "+x")
        self.v.poner(*sup, hex_a_rgba(acc["color2"] or ORO), "Head/flor")

    def acc_corona(self, acc):
        v = self.v
        sem = self.sem()
        oro = metal(acc["color"] or ORO, sem)
        gema = hex_a_rgba(acc["color2"] or "#2E8A6E")
        g = "Head/corona"
        top = max((c[1] for c in getattr(self, "celdas_pelo", [])), default=self.hy1) + 1
        y0 = top - 2
        sec = {(x, z) for x in range(-self.hx1 + 1, self.hx1 - 1) for z in range(self.hz0 + 1, self.hz1 - 1)}
        for (x, z) in anillo(sec, 0, 1.0):
            for y in (y0, y0 + 1):
                v.poner(x, y, z, oro(x, y, z), g)
            if (x + z) % 3 == 0:
                for y in range(y0 + 2, y0 + 3 + ((x * 7 + z) % 2)):
                    v.poner(x, y, z, oro(x, y, z), g)
        zf = self.hz0
        for y in range(y0 + 2, y0 + 5):
            v.poner(-1, y, zf, oro(-1, y, zf), g)
            v.poner(0, y, zf, oro(0, y, zf), g)
        v.poner(-1, y0 + 1, zf - 1, gema, g)
        v.poner(0, y0 + 1, zf - 1, gema, g)

    def acc_tiara(self, acc):
        v = self.v
        sem = self.sem()
        oro = metal(acc["color"] or ORO, sem)
        gema = hex_a_rgba(acc["color2"] or "#3A7BD5")
        g = "Head/tiara"
        y = self.hy1 - 1
        for x in range(-self.hx1 + 1, self.hx1 - 1):
            zf = self.frente(x, y, desde=self.hz0 - 6)
            if zf is not None:
                v.poner(x, y, zf, oro(x, y, zf), g)
        for x in (-1, 0):
            zf = self.frente(x, y + 1, desde=self.hz0 - 6)
            for yy in range(y + 1, y + 3):
                v.poner(x, yy, zf, oro(x, yy, zf), g)
            v.poner(x, y, (self.frente(x, y, desde=self.hz0 - 6) or self.hz0 - 2), gema, g)
        for x in (-3, 2):
            zf = self.frente(x, y + 1, desde=self.hz0 - 6)
            v.poner(x, y + 1, zf, oro(x, y + 1, zf), g)

    def acc_gafas(self, acc):
        v = self.v
        oro = hex_a_rgba(acc["color"] or ORO)
        g = "Head/gafas"
        y0 = self.hy0 + max(2, round(self.hh * 0.3))
        z = self.hz0 - 1
        for s in (1, -1):
            for x in range(0, 5):
                xx = self.lado(s, x)
                for y in range(y0 - 1, y0 + 4):
                    borde = x in (0, 4) or y in (y0 - 1, y0 + 3)
                    if borde:
                        v.poner(xx, y, z, oro, g)
            for zz in range(self.hz0, self.hz0 + 4):
                v.poner(self.lado(s, self.hx1), y0 + 2, zz, oro, g)

    def acc_plumas(self, acc):
        v = self.v
        cols = acc["colores"] or [acc["color"] or ORO, "#C2402E", "#3FA7A6", "#F1E2C6"]
        g = "Head/plumas"
        top = self.hy1
        n = 9
        for k in range(n):
            t = k / (n - 1)
            ang = math.pi * (0.1 + 0.8 * t)
            x0 = round(math.cos(ang) * (self.hx1 + 0.5)) - (1 if math.cos(ang) < 0 else 0)
            z0 = self.hz0 + 1 + round((1 - math.sin(ang)) * 2)
            c = hex_a_rgba(cols[k % len(cols)])
            alto = 5 + round(math.sin(ang) * 3)
            for j in range(alto):
                x = x0 + round(math.cos(ang) * j * 0.5)
                y = top - 1 + j
                z = z0 + round(j * 0.35)
                col = tono(c, 1.2) if j >= alto - 2 else (c if j > 0 else tono(c, 0.7))
                v.poner(x, y, z, col, g)
                if j > 1 and j < alto - 1:
                    v.poner(x + (1 if math.cos(ang) >= 0 else -1), y, z, tono(c, 0.9), g)
        for x in range(-self.hx1, self.hx1):                  # diadema
            v.poner(x, top - 1, self.hz0 - 1, hex_a_rgba(cols[(x + 10) % len(cols)]), g)

    def acc_etiquetas(self, acc):
        v = self.v
        fondo = hex_a_rgba(acc["color2"] or "#1F2447")
        borde = hex_a_rgba(acc["color"] or ORO)
        g = "Head/etiquetas"
        for k, (x, y, z) in enumerate(((self.hx1 + 2, self.hy1 - 2, -1), (-self.hx1 - 4, self.hy1, 0),
                                        (self.hx1 + 1, self.hy1 + 3, 2), (-self.hx1 - 3, self.hy1 + 4, 3))):
            for dx in range(3):
                for dy in range(4):
                    b = dx in (0, 2) or dy in (0, 3)
                    c = borde if b or (dx == 1 and dy == 2) else fondo
                    v.poner(x + dx, y + dy, z, c, g)

    def acc_cuernos(self, acc):
        v = self.v
        c = hex_a_rgba(acc["color"] or "#E8DCC0")
        for s in (1, -1):
            for j in range(6):
                x = self.lado(s, self.hx1 - 3 + j // 2)
                v.poner(x, self.hy1 + j, -1 + j // 3, tono(c, 0.8 + j * 0.06), "Head/cuernos")

    def acc_orejas(self, acc):
        v = self.v
        c = hex_a_rgba(acc["color"] or self.F["pelo"]["color"])
        for s in (1, -1):
            for j in range(4):
                for x in range(self.hx1 - 4 + j // 2, self.hx1 - 1):
                    v.poner(self.lado(s, x), self.hy1 + j, -1, tono(c, 1.1 if j == 3 else 1.0), "Head/orejas")

    # ------------------------------------------------------------------ extras
    def extras(self):
        for ex in self.F["extras"]:
            getattr(self, "ex_" + ex["tipo"], lambda a: None)(ex)

    def ex_amuletos(self, ex):
        v = self.v
        cols = ex["colores"] or [ex["color"] or ORO, "#3FA7A6", "#C2402E", "#E3B04B"]
        for k, x in enumerate((-4, -2, 1, 3)):
            largo = 2 + k % 2
            z = (self.frente(x, self.lh - 1) or self.tz0 - 2)
            for y in range(self.lh - largo, self.lh):
                v.poner(x, y, z, "#3B2A1E", "Body/amuletos")
            c = hex_a_rgba(cols[k % len(cols)])
            v.caja(x - (k % 2), self.lh - largo - 2, z - 1, x + 1, self.lh - largo, z + 1, c, "Body/amuletos", pisar=False)

    def ex_cintas(self, ex):
        v = self.v
        sem = self.sem()
        c = tela("manchas", [ex["color"] or "#E8832A", tono(ex["color"] or "#E8832A", 0.85)], sem)
        for s in (1, -1):
            x = self.lado(s, self.tx1 - 1)
            fin = self.lh - 6 - int(azar(sem, s) * 3)
            for y in range(fin, self.lh):
                z = self.frente(x, y) if y < self.lh - 1 else self.tz0 - 2
                if z is not None:
                    v.poner(x, y, z, c(x, y, z), ("Right" if s > 0 else "Left") + "Leg/cintas")

    def ex_emblema(self, ex):
        v = self.v
        col = hex_a_rgba(ex["color"] or ORO)
        fondo = hex_a_rgba(ex["color2"] or "#3B2A1E")
        forma = ex["forma"]
        yc = self.lh + self.th // 2 + 1
        for dx in range(-2, 2):
            for dy in range(-1, 3):
                x, y = dx, yc + dy
                z = self.frente(x, y)
                if z is None:
                    continue
                cx, cy = dx + 0.5, dy - 0.5
                if forma == "sol":
                    on = abs(cx) < 1 or abs(cy) < 1 or abs(abs(cx) - abs(cy)) < 0.5
                elif forma == "estrella":
                    on = abs(cx) < 1 or abs(cy) < 1
                elif forma == "hoja":
                    on = abs(cx - cy * 0.5) < 1
                elif forma == "luna":
                    on = cx < 0.5
                else:
                    on = abs(cx) + abs(cy) < 2
                v.poner(x, y, z, col if on else fondo, "Body/emblema")

    def ex_bolsa(self, ex):
        x = -self.tx1 + 1
        self.v.caja(x - 1, self.lh - 3, self.tz0 - 3, x + 2, self.lh, self.tz0 - 1, hex_a_rgba(ex["color"] or "#6B4A2A"),
                    "Body/bolsa", pisar=False)

    def libres(self):
        for p in self.F["piezas_libres"]:
            d, h = p["desde"], p["hasta"]
            col = liso(p["color"], self.sem())
            g = f"{p['hueso']}/extra"
            self.v.caja(math.floor(d[0]), math.floor(d[1]), math.floor(d[2]), math.ceil(h[0]), math.ceil(h[1]), math.ceil(h[2]),
                        col, g, pisar=False)
            if p["simetrica"]:
                g2 = g.replace("Right", "\0").replace("Left", "Right").replace("\0", "Left")
                self.v.caja(-math.ceil(h[0]), math.floor(d[1]), math.floor(d[2]), -math.floor(d[0]), math.ceil(h[1]),
                            math.ceil(h[2]), col, g2, pisar=False)

    # ------------------------------------------------------------------
    def esculpir(self):
        self.cuerpo()
        self.pelo()
        self.botas()
        self.tunica()
        self.mangas()
        self.guantes()
        self.hombreras()
        self.correas()
        self.cinturon()
        self.banda()
        self.bufanda()
        self.capa()
        self.accesorios_cabeza()
        self.extras()
        self.libres()
        return self.v

    def modelo(self):
        self.esculpir()
        return self.v.a_modelo(self.F.get("_id") or self.F["nombre"], self.pivotes)


def construir(ficha):
    return Escultor(ficha).modelo()
