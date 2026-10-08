"""
Constructor de personajes: ficha (ver ficha.py) -> Modelo con cuerpo vanilla + piezas 3D pintadas.

Estilo: player normal de Minecraft (cabeza 8x8x8, torso 8x12x4, brazos/piernas 4x12x4) y encima
pelo, ropa y accesorios hechos con cubos de 1 px o mas, pintados pixel a pixel.
Unidades en px. Frente = -Z, derecha del personaje = +X, pies en y = 0.
"""

import math

from .modelo import Modelo, uv_caja
from .textura import TRANSPARENTE, azar, hex_a_rgba, mezcla, ruido, tono

ORO = "#E3B04B"
CARA_ID = {"north": 1, "east": 2, "south": 3, "west": 4, "up": 5, "down": 6}


def _f(v):
    return int(math.floor(v + 1e-4))


def _px(t):
    """Coordenada entera del texel (estable en todas las caras)."""
    n = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0),
         "up": (0, 1, 0), "down": (0, -1, 0)}[t.cara]
    # se mete medio texel hacia dentro del cubo para que la cara caiga en la celda correcta
    return _f(t.x - n[0] * 0.25), _f(t.y - n[1] * 0.25), _f(t.z - n[2] * 0.25)


# ============================================================================ sombreado


def sombrear(c, t, semilla, fuerza=0.08, pliegues=True, borde=True):
    """Variacion por texel + pliegues verticales + linea oscura abajo de cada pieza (pixel art)."""
    if isinstance(c, str):
        c = hex_a_rgba(c)
    if c[3] == 0:
        return c
    X, Y, Z = _px(t)
    f = 1 + (azar(semilla, X, Y, Z, CARA_ID[t.cara]) - 0.5) * fuerza
    if t.lateral:
        if pliegues:
            col = X if t.cara in ("north", "south") else Z
            if azar(semilla + 7, col, CARA_ID[t.cara]) < 0.28:
                f *= 0.92
        if borde and t.th >= 2 and t.fila_abajo == 0:
            f *= 0.84
    elif t.cara == "up":
        f *= 1.05
    else:
        f *= 0.8
    return tono(c, f)


def patron(nombre, cols, t, semilla):
    """Color de un estampado en la posicion del texel. cols[0] = color principal."""
    c0 = cols[0]
    c1 = cols[1] if len(cols) > 1 else tono(c0, 0.85)
    c2 = cols[2] if len(cols) > 2 else c1
    c3 = cols[3] if len(cols) > 3 else c0
    X, Y, Z = _px(t)
    if nombre == "manchas":
        n = ruido(t.x, t.y * 0.8, t.z, 3.2, semilla)
        n2 = azar(semilla, X, Y, Z)
        if n < 0.5:
            return hex_a_rgba(c0) if n2 > 0.08 else hex_a_rgba(c3)
        if n < 0.66:
            return hex_a_rgba(c1 if n2 > 0.3 else c0)
        if n < 0.8:
            return hex_a_rgba(c1)
        return hex_a_rgba(c2)
    if nombre == "paneles":
        if t.cara in ("north", "south"):
            banda = _f((t.x + 6) / 3)
        elif t.cara in ("east", "west"):
            banda = _f((t.z + 6) / 3)
        else:
            banda = 0
        return hex_a_rgba([c0, c1, c0, c2][banda % 4])
    if nombre == "estrellas":
        base = hex_a_rgba(c0) if azar(semilla, X, Y, Z) > 0.15 else hex_a_rgba(c3 if len(cols) > 3 else tono(c0, 1.08))
        estrella = cols[1] if len(cols) > 1 else ORO
        if azar(semilla + 1, X, Y, Z) < 0.035:
            return tono(estrella, 1.15)
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            if azar(semilla + 1, X + dx, Y + dy, Z + dz) < 0.035 and azar(semilla + 2, X + dx, Y + dy, Z + dz) < 0.45:
                return hex_a_rgba(estrella)
        return base
    if nombre == "hojas":
        n = ruido(t.x, t.y, t.z, 2.5, semilla)
        if n > 0.68:
            return hex_a_rgba(c1)
        if n < 0.25:
            return hex_a_rgba(c2)
        if (X + Y + Z) % 4 == 0 and azar(semilla, X // 2, Y // 2, Z // 2) < 0.3:
            return tono(c1, 1.1)
        return hex_a_rgba(c0)
    if nombre == "rayas":
        return hex_a_rgba(c1 if (Y % 4) == 0 else c0)
    if nombre == "cuadros":
        return hex_a_rgba(c1 if ((X // 2 + Y // 2 + Z // 2) % 2) else c0)
    return hex_a_rgba(c0)


def mat(color, semilla, material="tela", color2=None):
    """Pintor simple de un material uniforme."""
    def p(t):
        if material == "metal":
            c = hex_a_rgba(color)
            if t.lateral and t.th >= 2:
                if t.j == 0:
                    c = tono(c, 1.25)
                elif t.fila_abajo == 0:
                    c = tono(c, 0.7)
            X, Y, Z = _px(t)
            if azar(semilla, X, Y, Z) < 0.06:
                c = tono(c, 1.35)
            return sombrear(c, t, semilla, 0.06, pliegues=False, borde=False)
        if material == "gema":
            c = hex_a_rgba(color)
            if t.i == 0 and t.j == 0:
                return tono(c, 1.6)
            return sombrear(c, t, semilla, 0.1, pliegues=False, borde=False)
        if material == "pelo":
            return pintor_pelo(color, color2, None, semilla)(t)
        if material == "madera":
            X, Y, Z = _px(t)
            c = tono(color, 0.85) if (X + Z + Y // 3) % 3 == 0 else hex_a_rgba(color)
            return sombrear(c, t, semilla, 0.1, pliegues=False)
        if material in ("piel", "hueso"):
            return sombrear(color, t, semilla, 0.05, pliegues=False, borde=False)
        if material == "cuero":
            return sombrear(color, t, semilla, 0.14, pliegues=False)
        return sombrear(color, t, semilla, 0.08)
    return p


def pintor_pelo(color, brillo=None, mechas=None, semilla=0):
    brillo = brillo or tono(color, 1.35)

    def p(t):
        X, Y, Z = _px(t)
        col = (X, Z) if t.cara in ("up", "down") else ((X, 0) if t.cara in ("north", "south") else (Z, 1))
        r = azar(semilla, *col)
        c = hex_a_rgba(color)
        if r < 0.22:
            c = tono(c, 0.78)
        elif r > 0.85:
            c = tono(c, 1.18)
        if t.cara == "up" and azar(semilla + 3, X, Z) < 0.16:
            c = hex_a_rgba(brillo)
        elif t.lateral and t.j == 0 and azar(semilla + 4, X, Y, Z) < 0.25:
            c = hex_a_rgba(brillo)
        if mechas and t.lateral and t.fila_abajo == 0 and azar(semilla + 5, X, Y, Z) < 0.55:
            c = hex_a_rgba(mechas)
        if t.lateral and Y < 28:
            c = tono(c, 0.92)
        return sombrear(c, t, semilla, 0.07, pliegues=False, borde=False)
    return p


# ============================================================================ pelo (voxel)


def celdas_pelo(estilo, volumen, semilla):
    """Celdas de 1 px alrededor de la cabeza (x -4..4, y 24..32, z -4..4). Devuelve set y limites."""
    if estilo == "ninguno":
        return set()
    v = volumen
    cfg = {
        #          arriba  lado  y_lado  y_atras  y_flequillo  bultos
        "corto": (1, 1, 29, 27, 31, 0.0),
        "rizos": (1 + (v >= 2), 1 + (v >= 3), 27, 25, 30, 0.38),
        "revuelto": (1 + (v >= 2), 1, 27, 26, 30, 0.3),
        "puntas": (1 + (v >= 3), 1, 27, 26, 30, 0.12),
        "lado": (1 + (v >= 3), 1, 26, 25, 30, 0.08),
        "largo": (1, 1, 20, 17, 30, 0.05),
    }[estilo]
    arriba, lado, y_lado, y_atras, y_fleq, bultos = cfg
    s = set()

    def fuera(cx, cy, cz):
        return max(0.0, abs(cx) - 4), max(0.0, cy - 32), max(0.0, cz - 4), max(0.0, -4 - cz)

    def fleq(ix):
        """y minimo del flequillo en la columna ix (frente)."""
        y = y_fleq
        r = azar(semilla, ix, 77)
        if estilo in ("rizos", "revuelto"):
            y -= 1 if r < 0.45 else 0
        elif estilo == "puntas":
            y -= 2 if (ix % 3 == 0) else (1 if r < 0.4 else 0)
        elif estilo == "lado":
            y = 28 + (ix + 4) * 0.5 if ix < 0 else 29 - ix * 0.25     # cae hacia la derecha del personaje
            y = 31 - (ix + 4) * 0.45
        elif estilo == "largo":
            y -= 0 if abs(ix + 0.5) > 1 else -1                          # raya al medio
        return y

    for ix in range(-7, 7):
        for iy in range(14, 39):
            for iz in range(-7, 7):
                cx, cy, cz = ix + 0.5, iy + 0.5, iz + 0.5
                if -4 < cx < 4 and 24 < cy < 32 and -4 < cz < 4:
                    continue                                              # dentro de la cabeza
                dx, dy, dz_a, dz_f = fuera(cx, cy, cz)
                if dz_f > 0:                                              # delante de la cara: flequillo
                    if dz_f <= 1 and dx <= 1 and cy >= fleq(ix) and cy <= 32 + arriba:
                        if dy <= arriba:
                            s.add((ix, iy, iz))
                    continue
                if dy > 0:                                                # encima
                    if dy <= arriba and dx <= lado and dz_a <= lado:
                        s.add((ix, iy, iz))
                    continue
                if dz_a > 0:                                              # detras
                    if dz_a <= lado and dx <= lado and cy >= y_atras:
                        s.add((ix, iy, iz))
                    continue
                if dx > 0 and dx <= lado:                                 # costados
                    ymin = y_lado
                    if cz < -2.5:                                         # patillas delante: mas cortas
                        ymin = max(y_lado, 28) if estilo != "largo" else 22
                    if cy >= ymin:
                        s.add((ix, iy, iz))

    # bultos (rizos / mechones) hacia afuera
    if bultos:
        borde = list(s)
        for (ix, iy, iz) in borde:
            if azar(semilla, ix, iy, iz, 9) < bultos:
                cx, cy, cz = ix + 0.5, iy + 0.5, iz + 0.5
                dx, dy, dz_a, dz_f = fuera(cx, cy, cz)
                if dz_f > 0:
                    continue
                d = (0, 1, 0) if dy > 0 else ((1 if cx > 0 else -1, 0, 0) if dx > 0 else (0, 0, 1))
                for k in range(1 + (d[1] == 0 and azar(semilla, ix, iy, iz, 3) < 0.25)):
                    n = (ix + d[0] * (k + 1), iy + d[1] * (k + 1), iz + d[2] * (k + 1))
                    s.add(n)
                    if azar(semilla, *n) < 0.5:                       # rizo de 2 px de ancho
                        s.add((n[0] + (d[1] != 0), n[1], n[2] + (d[0] != 0)))

    if estilo == "puntas":                                                # puntas hacia arriba y a los lados
        for ix in range(-4, 4, 2):
            for iz in range(-4, 4, 3):
                if azar(semilla, ix, iz, 5) < 0.6:
                    alto = 1 + int(azar(semilla, ix, iz, 6) * 3)
                    for k in range(alto):
                        s.add((ix, 32 + arriba + k, iz))
                        if k == 0:
                            s.add((ix + 1, 32 + arriba, iz))
        for lado_x in (-1, 1):
            for iy in (29, 31):
                base = 4 + lado if lado_x > 0 else -5 - lado
                for k in range(1 + int(azar(semilla, iy, lado_x) * 2)):
                    s.add((base + lado_x * k, iy, -1 + k))

    if estilo == "revuelto":
        for _ in range(10):
            ix = int(azar(semilla, _, 1) * 10) - 5
            iz = int(azar(semilla, _, 2) * 10) - 5
            s.add((ix, 32 + arriba, iz))
    return s


def fusionar(celdas):
    """Une celdas de 1 px en cajas grandes (menos cubos, misma silueta)."""
    resto = set(celdas)
    cajas = []
    for (i, y, j) in sorted(celdas, key=lambda c: (c[1], c[2], c[0])):
        if (i, y, j) not in resto:
            continue
        i2 = i
        while (i2 + 1, y, j) in resto:
            i2 += 1
        j2 = j
        while all((ii, y, j2 + 1) in resto for ii in range(i, i2 + 1)):
            j2 += 1
        y2 = y
        while all((ii, y2 + 1, jj) in resto for ii in range(i, i2 + 1) for jj in range(j, j2 + 1)):
            y2 += 1
        for ii in range(i, i2 + 1):
            for yy in range(y, y2 + 1):
                for jj in range(j, j2 + 1):
                    resto.discard((ii, yy, jj))
        cajas.append(((i, y, j), (i2 + 1, y2 + 1, j2 + 1)))
    return cajas


# ============================================================================ constructor


class Constructor:
    def __init__(self, ficha):
        self.F = ficha
        self.m = Modelo(ficha.get("_id") or ficha["nombre"])
        self.semilla = int(azar(*[ord(c) for c in ficha["nombre"]]) * 1e6)
        self.aw = 3 if ficha["brazos"] == "finos" else 4
        r = ficha["ropa"]
        self.tunica = r["tunica"]
        self.ab = 1.5 if (self.tunica and self.tunica["abierta"]) else 0.0
        self.pelo = celdas_pelo(ficha["pelo"]["estilo"], ficha["pelo"]["volumen"], self.semilla)
        if self.pelo:
            xs = [c[0] for c in self.pelo] + [c[0] + 1 for c in self.pelo]
            zs = [c[2] for c in self.pelo] + [c[2] + 1 for c in self.pelo]
            self.pelo_rx = max(max(xs), -min(xs), 4)
            self.pelo_zf = min(min(zs), -4)
            self.pelo_zb = max(max(zs), 4)
            self.pelo_top = max(max(c[1] + 1 for c in self.pelo), 32)
        else:
            self.pelo_rx, self.pelo_zf, self.pelo_zb, self.pelo_top = 4, -4, 4, 32
        self.s = 0

    def sem(self):
        self.s += 1
        return self.semilla + self.s * 101

    # ------------------------------------------------------------------ colores de la ropa
    def color_tunica(self, t, sem):
        tu = self.tunica
        return patron(tu["patron"], tu["colores"], t, sem)

    def ribete(self):
        tu = self.tunica
        return (tu and tu["ribete"]) or (tu and tono(tu["colores"][0], 0.7)) or "#444444"

    def con_banda(self, t, c):
        b = self.F["ropa"]["banda"]
        if not b or t.cara not in ("north", "south") or not (11.5 < t.y < 24.6):
            return c
        sx = 1 if t.cara == "north" else -1
        d = (t.x * sx) - (t.y - 18) * 0.62
        if abs(d) < 1.0:
            return hex_a_rgba(b["color"])
        if abs(d) < 1.6:
            return hex_a_rgba(b["detalle"])
        return c

    # ------------------------------------------------------------------ cuerpo base
    def cuerpo(self):
        aw = self.aw
        partes = [
            ("Head", "cabeza", (-4, 24, -4), (4, 32, 4), uv_caja(0, 0, 8, 8, 8)),
            ("Body", "torso", (-4, 12, -2), (4, 24, 2), uv_caja(16, 16, 8, 12, 4)),
            ("RightArm", "brazo_der", (4, 12, -2), (4 + aw, 24, 2), uv_caja(40, 16, aw, 12, 4)),
            ("LeftArm", "brazo_izq", (-4 - aw, 12, -2), (-4, 24, 2), uv_caja(32, 48, aw, 12, 4)),
            ("RightLeg", "pierna_der", (0, 0, -2), (4, 12, 2), uv_caja(0, 16, 4, 12, 4)),
            ("LeftLeg", "pierna_izq", (-4, 0, -2), (0, 12, 2), uv_caja(16, 48, 4, 12, 4)),
        ]
        for hueso, nombre, d, h, uv in partes:
            self.m.cubo(hueso, nombre, d, h, self.pintor_cuerpo(nombre), uv=uv)

    def pintor_cuerpo(self, parte):
        F = self.F
        r = F["ropa"]
        piel = F["piel"]
        sem = self.sem()
        pelo = pintor_pelo(F["pelo"]["color"], F["pelo"]["brillo"], None, sem)
        estilo = F["pelo"]["estilo"]

        def cabeza(t):
            if t.cara == "north":
                return self.cara(t)
            if t.cara == "down":
                return tono(piel, 0.8)
            if estilo == "ninguno":
                return sombrear(piel, t, sem, 0.04, False, False)
            if t.cara == "up":
                return pelo(t)
            lim = {"south": 25 if estilo != "largo" else 24, "east": 28, "west": 28}[t.cara]
            if estilo == "largo":
                lim = 24
            if t.cara in ("east", "west") and t.z < -2.5 and estilo != "largo":
                lim = 29
            return pelo(t) if t.y >= lim else sombrear(piel, t, sem, 0.04, False, False)

        def torso(t):
            if self.tunica:
                if t.cara == "north" and abs(t.x) < self.ab:
                    c = hex_a_rgba(r["camisa"]["color"])
                else:
                    c = self.color_tunica(t, sem)
            else:
                c = hex_a_rgba(r["camisa"]["color"])
            if t.cara == "up" and abs(t.x) < 2 and abs(t.z) < 2:
                c = hex_a_rgba(piel)
            return sombrear(self.con_banda(t, c), t, sem, 0.06, borde=False)

        def brazo(t):
            if t.y < 15:
                if r["guantes"]:
                    return sombrear(r["guantes"]["color"], t, sem, 0.1, False)
                return sombrear(piel, t, sem, 0.04, False, False)
            mg = r["mangas"]
            c = patron(mg["patron"], [mg["color"], mg["color2"]], t, sem) if mg else hex_a_rgba(r["camisa"]["color"])
            return sombrear(c, t, sem, 0.06, borde=False)

        def pierna(t):
            b = r["botas"]
            if t.y < b["alto"]:
                c = hex_a_rgba(b["color"])
                if b["ribete"] and t.y >= b["alto"] - 1:
                    c = hex_a_rgba(b["ribete"])
                if t.cara == "down":
                    c = tono(b["color"], 0.6)
                return sombrear(c, t, sem, 0.1, False, False)
            return sombrear(r["pantalon"]["color"], t, sem, 0.07, borde=False)

        return {"cabeza": cabeza, "torso": torso}.get(parte) or (brazo if "brazo" in parte else pierna)

    def cara(self, t):
        """Cara 8x8 (texel i de izquierda a derecha visto de frente, j de arriba abajo)."""
        F = self.F
        piel = hex_a_rgba(F["piel"])
        i, j = t.i, t.j
        ojos = F["cara"]["ojos"]
        exp = F["cara"]["expresion"]
        mascara = F["cara"]["mascara"]
        estilo = F["pelo"]["estilo"]
        pelo = pintor_pelo(F["pelo"]["color"], F["pelo"]["brillo"], None, self.semilla)
        blanco = (240, 238, 232, 255)
        pestana = tono(F["pelo"]["color"], 0.6)

        if mascara:
            m = hex_a_rgba(mascara)
            if j in (3, 4) and i in (1, 2, 5, 6):
                return tono(ojos, 1.35) if j == 3 else hex_a_rgba(ojos)
            if j == 5 and i in (1, 2, 5, 6):
                return tono(ojos, 0.75)
            if estilo != "ninguno" and j == 0:
                return pelo(t)
            return sombrear(m, t, self.semilla, 0.05, False, False)

        # pelo en la frente y patillas
        if estilo != "ninguno":
            if j == 0:
                return pelo(t)
            if j == 1 and (estilo in ("rizos", "revuelto", "puntas", "largo") or i in (0, 7)
                           or (estilo == "lado" and i <= 4)):
                return pelo(t)
            if j == 2 and (i in (0, 7) or (estilo == "lado" and i <= 1)):
                return pelo(t)
            if j in (3, 4) and i in (0, 7) and estilo in ("largo", "rizos"):
                return pelo(t)
        # ojos: columnas 1-2 (ojo derecho del personaje) y 5-6
        if i in (1, 2, 5, 6) and j in (3, 4):
            exterior = i in (1, 6)
            if exp == "traviesa" and i in (5, 6):                 # guino
                return pestana if j == 4 else piel
            if j == 3:
                return pestana if exterior else tono(ojos, 0.6)
            return blanco if exterior else hex_a_rgba(ojos)
        if exp == "seria" and j == 2 and i in (1, 2, 5, 6):
            return tono(F["pelo"]["color"], 0.9)                 # cejas
        # boca
        boca = tono(F["piel"], 0.55)
        if j == 6:
            if exp == "alegre" and i in (3, 4):
                return boca
            if exp == "traviesa" and i in (4, 5):
                return boca
            if exp in ("serena", "seria") and i in (3, 4):
                return tono(F["piel"], 0.75)
        if j == 5 and exp == "alegre" and i in (2, 5):
            return tono(F["piel"], 0.75)                         # comisuras de la sonrisa
        if F["cara"]["rubor"] and j == 5 and i in (1, 6):
            return mezcla(piel, (230, 120, 120, 255), 0.35)
        if j == 7:
            return tono(piel, 0.93)
        return sombrear(piel, t, self.semilla, 0.03, False, False)

    # ------------------------------------------------------------------ pelo 3D
    def pelo3d(self):
        F = self.F
        if not self.pelo:
            return
        p = pintor_pelo(F["pelo"]["color"], F["pelo"]["brillo"], F["pelo"]["mechas"], self.sem())
        for n, (d, h) in enumerate(fusionar(self.pelo)):
            self.m.cubo("Head/pelo", f"pelo_{n}", d, h, p)

    # ------------------------------------------------------------------ ropa
    def ropa(self):
        self.tunica3d()
        self.mangas3d()
        self.capa3d()
        self.bufanda3d()
        self.cinturon3d()
        self.hombreras3d()
        self.guantes3d()
        self.brazaletes3d()
        self.botas3d()

    def tunica3d(self):
        F = self.F
        r = self.F["ropa"]
        if self.tunica:
            sem = self.sem()
            ab = self.ab
            rib = self.ribete()

            def tun_torso(t):
                if t.cara == "north" and abs(t.x) < ab:
                    c = hex_a_rgba(r["camisa"]["color"])
                elif t.cara == "north" and ab and abs(t.x) < ab + 1:
                    c = hex_a_rgba(rib)
                elif t.cara == "up" and abs(t.x) < 3 and abs(t.z) < 2:
                    c = hex_a_rgba(F["piel"])
                else:
                    c = self.color_tunica(t, sem)
                return sombrear(self.con_banda(t, c), t, sem, 0.07)
            self.m.cubo("Body/tunica", "tunica_torso", (-4.5, 12, -2.5), (4.5, 24.5, 2.5), tun_torso)

            if ab:                                                       # solapas en relieve
                def solapa(t):
                    if t.cara == "north" and abs(t.x) < ab + 1:
                        c = hex_a_rgba(rib)
                    elif t.cara in ("east", "west") and abs(t.x) < 3:
                        c = hex_a_rgba(rib)
                    else:
                        c = self.color_tunica(t, sem)
                    return sombrear(self.con_banda(t, c), t, sem, 0.07)
                self.m.par("Body/tunica", "solapa", (ab, 14, -3), (4.5, 24.25, -2.5), solapa)

            # falda (en cada pierna para que se mueva al caminar)
            fondo = {"corta": 7, "media": 3.5, "larga": 0.5}[self.tunica["largo"]]
            medio = (12.25 + fondo) / 2 + 0.5
            abf = ab + 0.5 if ab else 0

            def falda(t):
                if t.cara == "north" and abs(t.x) < abf:
                    return sombrear(r["pantalon"]["color"], t, sem, 0.07)
                if t.cara == "north" and abf and abs(t.x) < abf + 1:
                    c = hex_a_rgba(rib)
                elif t.lateral and t.fila_abajo == 0 and t.f[1] <= fondo + 0.01:
                    X, Y, Z = _px(t)
                    if azar(sem, X, Z, 31) < 0.3:
                        return TRANSPARENTE                              # borde deshilachado
                    c = hex_a_rgba(rib)
                else:
                    c = self.color_tunica(t, sem)
                return sombrear(c, t, sem, 0.08)
            self.m.par("RightLeg/falda", "falda_alta", (0, medio, -2.5), (4.5, 12.5, 2.5), falda)
            self.m.par("RightLeg/falda", "falda_baja", (0, fondo, -3), (5, medio, 3), falda)

    def mangas3d(self):
        r = self.F["ropa"]
        aw = self.aw
        mg = r["mangas"]
        if mg or self.tunica:
            mg = mg or {"color": self.tunica["colores"][0], "color2": self.tunica["colores"][-1],
                        "forma": "ajustadas", "patron": self.tunica["patron"]}
            sem = self.sem()
            cols = [mg["color"], mg["color2"]]
            rib = self.ribete() if self.tunica else tono(mg["color2"], 0.8)

            def manga(t):
                c = patron(mg["patron"], cols, t, sem)
                if t.lateral and t.fila_abajo == 0:
                    c = hex_a_rgba(rib)
                return sombrear(c, t, sem, 0.07)
            if mg["forma"] == "anchas":
                self.m.par("RightArm/manga", "manga", (3.75, 17.5, -2.25), (4 + aw + 0.25, 24.25, 2.25), manga)
                self.m.par("RightArm/manga", "manga_campana", (3.75, 13.5, -2.75), (4 + aw + 0.75, 17.5, 2.75), manga)
            else:
                self.m.par("RightArm/manga", "manga", (3.75, 15, -2.25), (4 + aw + 0.25, 24.25, 2.25), manga)

    def capa3d(self):
        r = self.F["ropa"]
        aw = self.aw
        ca = r["capa"]
        if ca:
            sem = self.sem()
            cols = [ca["color"], ca["color2"]]
            if ca["patron"] == "estrellas":
                cols = [ca["color"], ORO, ca["color2"]]
            fondo = {"corta": 12, "media": 6, "larga": 1}[ca["largo"]]
            medio = (24 + fondo) / 2

            def capa(t):
                c = patron(ca["patron"], cols, t, sem)
                if t.cara == "south" or t.cara == "up":
                    pass
                elif t.cara == "north":
                    c = tono(ca["color2"], 0.9)                     # forro
                if t.lateral and t.fila_abajo == 0 and t.f[1] <= fondo + 0.01:
                    X, Y, Z = _px(t)
                    if azar(sem, X, 41) < 0.3:
                        return TRANSPARENTE
                return sombrear(c, t, sem, 0.08)
            self.m.cubo("Body/capa", "capa_alta", (-5, medio, 2.5), (5, 24.5, 3.5), capa)
            self.m.cubo("Body/capa", "capa_baja", (-5.5, fondo, 3), (5.5, medio, 4), capa)
            self.m.par("RightArm/capa", "capa_hombro", (3.5, 23.25, -1.5), (4 + aw + 0.75, 24.75, 3.5), capa)
            if ca["capucha"]:
                self.m.cubo("Body/capa", "capucha", (-4.5, 21.5, 3.25), (4.5, 26, 5.5), capa)
                self.m.cubo("Body/capa", "capucha_punta", (-2, 19, 3.5), (2, 21.5, 5), capa)

    def bufanda3d(self):
        r = self.F["ropa"]
        bu = r["bufanda"]
        if bu:
            sem = self.sem()
            cols = [bu["color"], bu["color"], bu["color2"]]

            def bufanda(t):
                c = patron("manchas", cols, t, sem) if bu["color2"] != bu["color"] else hex_a_rgba(bu["color"])
                if t.lateral and "cola" not in t.nombre and (_px(t)[1] + _px(t)[0] // 3) % 2 == 0:
                    c = tono(c, 0.9)                                 # vueltas de la tela
                if t.lateral and t.fila_abajo == 0 and "cola" in t.nombre:
                    X, Y, Z = _px(t)
                    if azar(sem, X, Z, 51) < 0.4:
                        return TRANSPARENTE
                return sombrear(c, t, sem, 0.1)
            if bu["tamano"] == "grande":
                self.m.cubo("Body/bufanda", "bufanda_base", (-5.5, 21, -3.75), (5.5, 24, 3.75), bufanda)
                self.m.cubo("Body/bufanda", "bufanda_cuello", (-4.75, 24, -4.75), (4.75, 25.25, 4.75), bufanda)
                self.m.cubo("Body/bufanda", "bufanda_nudo", (-4, 18.5, -4.5), (0.5, 21.5, -3.5), bufanda)
                if bu["colas"]:
                    self.m.cubo("Body/bufanda", "bufanda_cola1", (-3.5, 12.5, -4.25), (-0.5, 18.5, -3.5), bufanda)
                    self.m.cubo("Body/bufanda", "bufanda_cola2", (0.5, 14, -4), (3, 21, -3.25), bufanda)
                    self.m.cubo("Body/bufanda", "bufanda_cola3", (-4.5, 13, 3.5), (-1, 21, 4.25), bufanda)
            else:
                self.m.cubo("Body/bufanda", "bufanda_base", (-4.75, 22, -3.25), (4.75, 24.75, 3.25), bufanda)
                if bu["colas"]:
                    self.m.cubo("Body/bufanda", "bufanda_cola1", (1, 16, -3.75), (3, 22, -3.25), bufanda)

    def cinturon3d(self):
        r = self.F["ropa"]
        ci = r["cinturon"]
        if ci:
            sem = self.sem()
            self.m.cubo("Body/cinturon", "cinturon", (-4.75, 12, -2.75), (4.75, 13.5, 2.75),
                        mat(ci["color"], sem, "cuero"))
            self.m.cubo("Body/cinturon", "hebilla", (-1.25, 11.75, -3.25), (1.25, 13.75, -2.75),
                        mat(ci["hebilla"], sem, "metal"))

    def hombreras3d(self):
        r = self.F["ropa"]
        aw = self.aw
        ho = r["hombreras"]
        if ho:
            sem = self.sem()

            def hombrera(t):
                c = hex_a_rgba(ho["color"])
                if t.lateral and t.fila_abajo == 0:
                    c = hex_a_rgba(ho["detalle"])
                if t.cara in ("east", "west") and "alta" in t.nombre:
                    cz, cy = (t.f[2] + t.t[2]) / 2, (t.f[1] + t.t[1]) / 2
                    if abs(t.z - cz) < 1 and abs(t.y - cy - 0.4) < 1:
                        c = hex_a_rgba(ho["detalle"])                    # sol / emblema
                return sombrear(c, t, sem, 0.1, pliegues=False)
            self.m.par("RightArm/hombrera", "hombrera_alta", (3.5, 22, -2.75), (4 + aw + 1, 25, 2.75), hombrera)
            self.m.par("RightArm/hombrera", "hombrera_baja", (4 + aw - 1.5, 20.25, -3), (4 + aw + 1.5, 22, 3), hombrera)

    def guantes3d(self):
        r = self.F["ropa"]
        aw = self.aw
        gu = self.F["ropa"]["guantes"]
        gu = r["guantes"]
        if gu:
            sem = self.sem()
            self.m.par("RightArm/guante", "guante", (3.75, 11.75, -2.25), (4 + aw + 0.25, 15, 2.25),
                       mat(gu["color"], sem, "cuero"))
            self.m.par("RightArm/guante", "guante_puno", (3.5, 15, -2.5), (4 + aw + 0.5, 16.5, 2.5),
                       mat(gu["detalle"], sem, "metal"))

    def brazaletes3d(self):
        r = self.F["ropa"]
        aw = self.aw
        mg = self.F["ropa"]["mangas"]
        gu = self.F["ropa"]["guantes"]
        if r["brazaletes"] and not gu:
            sem = self.sem()
            anchas = mg and mg.get("forma") == "anchas"
            y1 = 12.75 if anchas else 15.25
            self.m.par("RightArm/brazalete", "brazalete", (3.75, y1, -2.25), (4 + aw + 0.25, y1 + 1, 2.25),
                       mat(r["brazaletes"], sem, "metal"))

    def botas3d(self):
        r = self.F["ropa"]
        b = r["botas"]
        sem = self.sem()
        alto = b["alto"]
        self.m.par("RightLeg/botas", "bota_borde", (0, alto - 0.5, -2.25), (4.25, alto + 0.75, 2.25),
                   mat(b["ribete"] or tono(b["color"], 1.15), sem, "cuero"))
        self.m.par("RightLeg/botas", "bota_puntera", (0.25, 0, -2.75), (3.75, 1.5, -2),
                   mat(tono(b["color"], 0.85), sem, "cuero"))

    # ------------------------------------------------------------------ cabeza
    def accesorios_cabeza(self):
        rx = self.pelo_rx
        top = self.pelo_top
        zf, zb = self.pelo_zf, self.pelo_zb
        for acc in self.F["cabeza"]:
            self._accesorio(acc, rx, top, zf, zb)

    def _accesorio(self, acc, rx, top, zf, zb):
        if True:
            tipo = acc["tipo"]
            sem = self.sem()
            col = acc["color"] or ORO
            col2 = acc["color2"] or tono(col, 0.75)
            if tipo == "laurel":
                hoja = mat(col, sem, "metal")
                y0 = 29.5
                k = 0
                for lado in (1, -1):
                    z = zf + 0.5
                    while z < zb - 1:
                        dy = 0.75 if k % 2 else 0
                        x1 = lado * (rx - 0.25)
                        self.m.cubo("Head/laurel", f"hoja_{k}", (x1, y0 + dy, z), (x1 + lado * 1, y0 + dy + 1.25, z + 1.75), hoja)
                        k += 1
                        z += 1.5
                for x in (-2.5, -0.75, 1.0):
                    dy = 0.75 if k % 2 else 0
                    self.m.cubo("Head/laurel", f"hoja_{k}", (x, y0 + dy, zb - 0.25), (x + 1.5, y0 + dy + 1.25, zb + 0.75), hoja)
                    k += 1
                for lado in (1, -1):                                     # hojas que suben hacia la frente
                    x1 = lado * (rx - 1.5)
                    self.m.cubo("Head/laurel", f"hoja_{k}", (x1, y0 + 1.25, zf - 0.25), (x1 + lado * 1.25, y0 + 2.75, zf + 1.25), hoja)
                    k += 1
                    self.m.cubo("Head/laurel", f"hoja_{k}", (x1 - lado * 1.25, y0 + 2.25, zf - 0.25), (x1, y0 + 3.25, zf + 1.0), hoja)
                    k += 1
            elif tipo in ("corona", "tiara"):
                oro = mat(col, sem, "metal")
                gema = mat(acc["color2"] or "#3A7BD5", sem, "gema")
                r_ = rx + 0.25
                if tipo == "corona":
                    y1, y2 = top - 1.5, top + 0.5
                    self.m.cubo("Head/corona", "corona_frente", (-r_, y1, zf - 0.5), (r_, y2, zf + 0.25), oro)
                    self.m.cubo("Head/corona", "corona_atras", (-r_, y1, zb - 0.25), (r_, y2, zb + 0.5), oro)
                    self.m.par("Head/corona", "corona_lado", (r_ - 0.75, y1, zf + 0.25), (r_, y2, zb - 0.25), oro)
                    for n, x in enumerate((-4, -1, 2)):
                        alto = 2.5 if n == 1 else 1.75
                        self.m.cubo("Head/corona", f"punta_f{n}", (x, y2, zf - 0.5), (x + 2, y2 + alto, zf + 0.25), oro)
                        self.m.cubo("Head/corona", f"punta_a{n}", (x, y2, zb - 0.25), (x + 2, y2 + 1.25, zb + 0.5), oro)
                    self.m.par("Head/corona", "punta_lado", (r_ - 0.75, y2, -1), (r_, y2 + 1.75, 1), oro)
                    self.m.cubo("Head/corona", "gema", (-0.75, y1 + 0.5, zf - 0.75), (0.75, y2 - 0.25, zf - 0.5), gema)
                else:
                    y1 = 31
                    self.m.cubo("Head/tiara", "tiara_frente", (-3.5, y1, zf - 0.5), (3.5, y1 + 0.75, zf), oro)
                    self.m.par("Head/tiara", "tiara_lado", (3, y1 - 0.5, zf - 0.25), (4, y1 + 0.5, zf + 0.25), oro)
                    self.m.cubo("Head/tiara", "tiara_punta", (-1, y1 + 0.75, zf - 0.5), (1, y1 + 2.5, zf), oro)
                    self.m.cubo("Head/tiara", "tiara_gema", (-0.5, y1 + 0.75, zf - 0.75), (0.5, y1 + 1.75, zf - 0.5), gema)
            elif tipo == "gafas":
                marco = hex_a_rgba(col)
                lente = (190, 225, 240, 255)

                def gafas(t):
                    if t.cara != "north":
                        return tono(marco, 0.85)
                    ax = abs(t.x)
                    if 0.5 < ax < 3.75:
                        borde = ax < 1.0 or ax > 3.25 or t.y > 28.5 or t.y < 26.5
                        if borde:
                            return marco
                        if t.i in (2, 6) and t.j == 1:
                            return lente
                        return TRANSPARENTE
                    if ax <= 0.5 and t.y > 27.5:
                        return marco
                    return TRANSPARENTE
                self.m.cubo("Head/gafas", "gafas", (-4, 26, -4.75), (4, 29, -4.25), gafas)
                self.m.par("Head/gafas", "gafas_patilla", (4, 28, -4.75), (4.5, 28.5, -1), mat(col, sem, "metal"))
            elif tipo == "plumas":
                cols = acc["colores"] or [col, col2, "#3FA7A6", "#F1E2C6"]
                for n, x in enumerate((-4.5, -3, -1.5, 0, 1.5, 3, 4.5)):
                    c = cols[n % len(cols)]
                    alto = 5.5 - abs(x) * 0.5
                    rz = -22.5 if x > 2 else (22.5 if x < -2 else 0)

                    def pluma(t, c=c):
                        base = hex_a_rgba(c)
                        if t.lateral and t.j < 2:
                            base = tono(c, 1.2)
                        if t.lateral and t.fila_abajo <= 1:
                            base = tono(c, 0.7)
                        return sombrear(base, t, sem, 0.08, False, False)
                    self.m.cubo("Head/plumas", f"pluma_{n}", (x - 0.6, top - 1, 1.5), (x + 0.6, top - 1 + alto, 2.5),
                                pluma, rot=(-22.5, 0, rz), origen=(x, top - 1, 2))
                for n, x in enumerate((-2.5, 1.5)):
                    c = cols[(n + 2) % len(cols)]
                    self.m.cubo("Head/plumas", f"pluma_frente_{n}", (x, top - 1, zf + 0.5), (x + 1, top + 2, zf + 1.25),
                                mat(c, sem), rot=(22.5, 0, 0), origen=(x, top - 1, zf + 1))
                self.m.cubo("Head/plumas", "plumas_banda", (-rx - 0.25, top - 2, zf - 0.25), (rx + 0.25, top - 1, zb + 0.25),
                            mat(col2, sem))
            elif tipo == "etiquetas":
                fondo = col2 if acc["color2"] else "#1F2447"

                def etiqueta(t):
                    if not t.lateral or t.cara in ("east", "west"):
                        return hex_a_rgba(col)
                    if t.i == 0 or t.j == 0 or t.i == t.tw - 1 or t.fila_abajo == 0:
                        return hex_a_rgba(col)
                    return hex_a_rgba(col) if (t.i + t.j) % 3 == 0 else hex_a_rgba(fondo)
                for n, (x, y, z, ry) in enumerate(((7, 30, -2, -22.5), (-7.5, 31.5, -1, 22.5),
                                                   (6, 35.5, 2, -22.5), (-5.5, 36, 3, 22.5))):
                    self.m.cubo("Head/etiquetas", f"etiqueta_{n}", (x - 1.5, y - 2, z - 0.25), (x + 1.5, y + 2, z + 0.25),
                                etiqueta, rot=(0, ry, 0), origen=(x, y, z))
            elif tipo == "flor":
                petalo = mat(col, sem)
                cx, cy, cz = rx + 0.25, 30.5, -1.5
                self.m.cubo("Head/flor", "flor_centro", (cx, cy - 0.75, cz - 0.75), (cx + 1, cy + 0.75, cz + 0.75),
                            mat(col2 if acc["color2"] else ORO, sem, "metal"))
                for n, (dy, dz) in enumerate(((1.5, 0), (-1.5, 0), (0, 1.5), (0, -1.5))):
                    self.m.cubo("Head/flor", f"petalo_{n}", (cx - 0.25, cy + dy - 0.9, cz + dz - 0.9),
                                (cx + 0.75, cy + dy + 0.9, cz + dz + 0.9), petalo)
            elif tipo == "cuernos":
                cuerno = mat(col if acc["color"] else "#E8DCC0", sem, "hueso")
                self.m.par("Head/cuernos", "cuerno_base", (2, top - 0.5, -2), (4, top + 2, 0), cuerno)
                self.m.par("Head/cuernos", "cuerno_medio", (3, top + 2, -1.5), (4.5, top + 4, 0), cuerno)
                self.m.par("Head/cuernos", "cuerno_punta", (3.75, top + 4, -1.25), (4.75, top + 5.5, -0.25), cuerno)
            elif tipo == "orejas":
                oreja = mat(col if acc["color"] else self.F["pelo"]["color"], sem, "pelo")
                self.m.par("Head/orejas", "oreja", (1.5, top - 0.5, -1), (4, top + 2.5, 0.5), oreja)
                self.m.par("Head/orejas", "oreja_punta", (2.25, top + 2.5, -0.75), (3.5, top + 3.75, 0.25), oreja)

    # ------------------------------------------------------------------ extras
    def extras(self):
        r = self.F["ropa"]
        grande = r["bufanda"] and r["bufanda"]["tamano"] == "grande"
        for ex in self.F["extras"]:
            self._extra(ex, grande)

    def _extra(self, ex, grande):
        if True:
            tipo = ex["tipo"]
            sem = self.sem()
            col = ex["color"] or ORO
            col2 = ex["color2"] or "#F1E2C6"
            if tipo == "libro":
                def libro(t):
                    if t.cara in ("east", "west"):
                        return sombrear(col, t, sem, 0.1, False)
                    if t.cara == "north" and t.i == 0:
                        return hex_a_rgba(ORO)
                    return sombrear(col2 if t.cara != "south" else col, t, sem, 0.05, False)
                self.m.cubo("Body/libro", "libro", (-6.25, 8.5, -2), (-4.75, 12.5, 1.5), libro)
                self.m.cubo("Body/libro", "libro_correa", (-5.75, 12.5, -0.75), (-5.25, 13.5, 0.25), mat("#3B2A1E", sem, "cuero"))
            elif tipo == "amuletos":
                cols = ex["colores"] or [col, "#3FA7A6", "#C2402E", "#E3B04B"]
                hilo = mat("#3B2A1E", sem, "cuero")
                for n, x in enumerate((-3.25, -1.5, 1.5, 3.25)):
                    largo = 2 + (n % 2) * 1.5
                    self.m.cubo("Body/amuletos", f"hilo_{n}", (x - 0.25, 12 - largo, -3.25), (x + 0.25, 12, -2.75), hilo)
                    self.m.cubo("Body/amuletos", f"amuleto_{n}", (x - 0.75, 12 - largo - 1.5, -3.5), (x + 0.75, 12 - largo, -2.75),
                                mat(cols[n % len(cols)], sem, "gema" if n % 2 else "madera"))
                for n, x in enumerate((-2.5, 2.5)):
                    self.m.cubo("Body/amuletos", f"amuleto_atras_{n}", (x - 0.75, 9, 2.75), (x + 0.75, 11, 3.5),
                                mat(cols[(n + 1) % len(cols)], sem, "madera"))
            elif tipo == "cintas":
                def cinta(t):
                    X, Y, Z = _px(t)
                    if t.lateral and t.fila_abajo == 0 and azar(sem, X, Z) < 0.5:
                        return TRANSPARENTE
                    return sombrear(col, t, sem, 0.08)
                self.m.par("Body/cintas", "cinta", (3.5, 5, -2.25), (4.25, 12, -1.25), cinta)
                self.m.cubo("Body/cintas", "cinta_atras", (0.5, 6, 2.75), (2, 12, 3.25), cinta)
            elif tipo == "emblema":
                y0 = 15.5 if grande else 18
                forma = ex["forma"]

                def emblema(t):
                    if t.cara != "north":
                        return tono(col, 0.75)
                    cx, cy = t.x, t.y - (y0 + 1.5)
                    d = max(abs(cx), abs(cy))
                    on = False
                    if forma == "sol":
                        on = d < 0.8 or (t.i in (0, 3) and t.j in (0, 3)) or (abs(cx) < 0.5 or abs(cy) < 0.5)
                    elif forma == "luna":
                        on = abs(cx + 0.5) + abs(cy) < 1.8 and not (abs(cx - 0.4) + abs(cy) < 1.0)
                    elif forma == "estrella":
                        on = abs(cx) < 0.5 or abs(cy) < 0.5
                    elif forma == "hoja":
                        on = abs(cx - cy * 0.4) < 0.9
                    elif forma == "diamante":
                        on = abs(cx) + abs(cy) < 1.6
                    elif forma == "ojo":
                        on = abs(cy) < 0.8 and abs(cx) < 1.5
                    return hex_a_rgba(col) if on else tono(col2, 0.8)
                self.m.cubo("Body/emblema", "emblema", (-1.5, y0, -3.25), (1.5, y0 + 3, -2.5), emblema)
            elif tipo == "bolsa":
                self.m.cubo("Body/bolsa", "bolsa", (2, 9.5, -3.5), (4.5, 12, -2.5), mat(col if ex["color"] else "#6B4A2A", sem, "cuero"))
            elif tipo == "espada":
                self.m.cubo("Body/espada", "vaina", (-5.25, 2, 3), (-4.25, 12, 4), mat(col2 if ex["color2"] else "#3B2A1E", sem, "cuero"),
                            rot=(0, 0, -22.5), origen=(-4.75, 12, 3.5))
                self.m.cubo("Body/espada", "empunadura", (-5.25, 12, 3), (-4.25, 15, 4), mat(col, sem, "metal"),
                            rot=(0, 0, -22.5), origen=(-4.75, 12, 3.5))
            elif tipo == "baston":
                self.m.cubo("Body/baston", "baston", (-0.5, 2, 3.5), (0.5, 30, 4.5), mat(col2 if ex["color2"] else "#6B4A2A", sem, "madera"),
                            rot=(0, 0, 22.5), origen=(0, 16, 4))
                self.m.cubo("Body/baston", "baston_punta", (-1, 30, 3.25), (1, 32, 4.75), mat(col, sem, "gema"),
                            rot=(0, 0, 22.5), origen=(0, 16, 4))

    def libres(self):
        for n, p in enumerate(self.F["piezas_libres"]):
            pintor = mat(p["color"], self.sem(), p["material"])
            ruta = f"{p['hueso']}/extra"
            if p["simetrica"]:
                self.m.par(ruta, p["nombre"], p["desde"], p["hasta"], pintor)
            else:
                self.m.cubo(ruta, f"{p['nombre']}_{n}", p["desde"], p["hasta"], pintor)

    # ------------------------------------------------------------------
    def construir(self) -> Modelo:
        self.cuerpo()
        self.pelo3d()
        self.ropa()
        self.accesorios_cabeza()
        self.extras()
        self.libres()
        return self.m


def construir(ficha) -> Modelo:
    return Constructor(ficha).construir()
