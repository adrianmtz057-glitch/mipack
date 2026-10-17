"""
La piel de un bicho: lo que mas importa en estos (el diseno y la textura mas que el modelo).

Una Piel junta la paleta del animal y sus marcas, y da un pintor por parte del cuerpo (el nombre del cubo dice que
parte es: cuerpo, cabeza, hocico, oreja, pata, cola, ala, pico, cuerno, aleta...). Estilo de la casa ("soft"):
colores planos y limpios, arriba un paso mas claro y abajo uno mas oscuro (rampas con cambio de tono: las sombras
se enfrian y las luces se calientan), pocos detalles bien puestos y nada de ruido al azar.

Los patrones se calculan en 3D (con la posicion del texel en el modelo), asi siguen de una cara a otra sin cortes:
  manchas    circulos repartidos (venado, guepardo, salamandra)
  rayas      bandas que rodean el cuerpo (gato, chacal, abeja)
  dunas      ondas horizontales (la arena del ballenato)
  moteado    puntitos sueltos (huevo, sal, polvo)
  pelaje     mechones cortos verticales (casi todos los de pelo)
  escamas    hileras de escamas con su borde (reptiles, peces)
  plumas     hileras de plumas con la punta clara (aves)
  placas     placas con borde oscuro (caparazones, roca)
  grietas    red de grietas (lo que brilla: brasa, lava, mura)
  rombos     rombos sobre el lomo (serpientes)
  anillos    anillos alrededor del cuerpo (colas, serpientes)
Lo que brilla (ojos, el patron, las grietas, puntas...) sale ademas en una mascara aparte (la "glowmask" del mod).
"""

import math

from ..luz import paso
from ..textura import TRANSPARENTE, azar, hex_a_rgba

LATERALES = ("north", "south", "east", "west")
_CARA = {"north": 1, "south": 2, "east": 3, "west": 4, "up": 5, "down": 6}


def _c(h):
    return hex_a_rgba(h) if h is not None else None


def _celdas(x, y, z, tam, sem):
    """La distancia al centro mas cercano y al segundo de una red de celdas 3D (centros movidos por azar fijo)."""
    gx, gy, gz = math.floor(x / tam), math.floor(y / tam), math.floor(z / tam)
    d1 = d2 = 1e9
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for k in (-1, 0, 1):
                cx, cy, cz = gx + i, gy + j, gz + k
                px = (cx + 0.15 + 0.7 * azar(sem, cx, cy, cz, 1)) * tam
                py = (cy + 0.15 + 0.7 * azar(sem, cx, cy, cz, 2)) * tam
                pz = (cz + 0.15 + 0.7 * azar(sem, cx, cy, cz, 3)) * tam
                d = math.sqrt((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2)
                if d < d1:
                    d1, d2 = d, d1
                elif d < d2:
                    d2 = d
    return d1, d2


class Piel:
    """
    base: el color del lomo; vientre, patas, pezuna (la punta de las patas), cara, hocico, oreja (adentro), cuerno,
    pico, ala, punta_ala, cola, punta_cola, cresta: los de cada parte (None = el de base o el que toque).
    patron: (nombre, color, tamano en px, cantidad 0-1) y donde: las partes que lo llevan.
    ojo: color; ojo_brillo: el texel claro del ojo; ojos_al_frente: en la cara de enfrente (gato, mono, buho) o a los
    lados (casi todos).
    brilla: lo que va en la mascara de brillo: "ojos", "patron", "punta_cola", "cresta", "agallas", o nombres de
    partes enteras.
    mascara: (color, que tan abajo llega) una mascara oscura o clara en la cara (zorro, mapache).
    """

    def __init__(self, base, vientre=None, patas=None, pezuna=None, cara=None, hocico=None, nariz="#2B201C",
                 oreja=None, cuerno="#D8CDB4", pico="#E0A23A", ala=None, punta_ala=None, cola=None, punta_cola=None,
                 cresta=None, ojo="#16110F", ojo_brillo="#F4EFE6", ojos_al_frente=False, patron=None,
                 donde=("cuerpo", "cuello", "cabeza", "cola", "pata"), brilla=(), mascara=None, extras=None, sem=1):
        self.base = _c(base)
        self.vientre = _c(vientre)
        self.patas = _c(patas) or self.base
        self.pezuna = _c(pezuna)
        self.cara = _c(cara) or self.base
        self.hocico = _c(hocico) or self.cara
        self.nariz = _c(nariz)
        self.oreja = _c(oreja)
        self.cuerno = _c(cuerno)
        self.pico = _c(pico)
        self.ala = _c(ala) or self.base
        self.punta_ala = _c(punta_ala)
        self.cola = _c(cola) or self.base
        self.punta_cola = _c(punta_cola)
        self.cresta = _c(cresta)
        self.ojo = _c(ojo)
        self.ojo_brillo = _c(ojo_brillo)
        self.ojo_tipo, self.iris, self.anillo, self.ceja, self.ojo_tam = "punto", None, None, False, 1.0
        self.ojos_al_frente = ojos_al_frente
        # uno o varios patrones: (nombre, color, tamano, cantidad[, partes[, zona]]); zona: todo, lomo (arriba),
        # costados o abajo. Se aplican en orden (los de tono suman, los de color tapan).
        if patron and isinstance(patron[0], str):
            patron = [patron]
        self.patrones = []
        for p in (patron or []):
            p = tuple(p) + (None,) * (6 - len(p))
            self.patrones.append((p[0], _c(p[1]), p[2], p[3], tuple(p[4]) if p[4] else tuple(donde), p[5] or "todo"))
        self.donde = donde
        self.brilla = set(brilla)
        self.mascara = (_c(mascara[0]), mascara[1]) if mascara else None
        self.extras = {k: _c(v) for k, v in (extras or {}).items()}       # partes con su propio color
        self.sem = sem
        self.modo = "color"                    # "brillo": pinta solo lo que brilla (lo demas transparente)
        self.ojos = {}                          # cubo de la cabeza -> (y del ojo, z del ojo, radio) los pone el cuerpo

    # ------------------------------------------------------------------ patrones

    def _aplicar_patrones(self, c, t, parte, rel_y):
        """El color c con los patrones que le tocan; y si alguno que brilla le pego."""
        brilla = False
        for p in self.patrones:
            en = self._en_patron(t, parte, rel_y, p)
            if isinstance(en, int):
                c = paso(c, en)
            elif en is not None:
                c = en
                brilla = brilla or ("patron" in self.brilla and p[1] is not None)
        return c, brilla

    def _en_patron(self, t, parte, rel_y, p):
        """Si el texel cae en el patron p: devuelve un tono (int de pasos) o un color, o None."""
        nombre, color, tam, cant, donde, zona = p
        if not any(parte.startswith(d) for d in donde):
            return None
        if zona == "lomo" and not (t.cara == "up" or rel_y > 0.55 + 0.12 * math.sin(t.z * 0.9 + t.x * 0.7)):
            return None
        if zona == "costados" and (t.cara not in LATERALES or rel_y < 0.25 or rel_y > 0.85):
            return None
        if zona == "abajo" and not (t.cara == "down" or rel_y < 0.35):
            return None
        x, y, z = t.x, t.y, t.z
        s = self.sem
        if nombre == "manchas":
            d1, _ = _celdas(x, y, z, tam, s)
            r = tam * (0.18 + 0.22 * cant) * (0.7 + 0.6 * azar(s, math.floor(x / tam), math.floor(z / tam), 9))
            return color if d1 < r else None
        if nombre == "rayas":
            v = z / tam + 0.35 * math.sin(y * 0.45 + x * 0.3) + 0.15 * math.sin(z * 0.9)
            return color if (v % 1.0) < 0.22 + 0.25 * cant else None
        if nombre == "dunas":
            v = y / tam + 0.4 * math.sin(z * 0.35 + x * 0.2)
            return color if (v % 1.0) < 0.2 + 0.25 * cant else None
        if nombre == "moteado":
            return color if azar(s, round(x * 2), round(y * 2), round(z * 2), _CARA[t.cara]) < 0.08 + 0.3 * cant else None
        if nombre == "pelaje":
            col = round((x if t.cara in ("north", "south", "up", "down") else z) * 2)
            fila = math.floor(y * 2 / 3) if t.cara in LATERALES else round(z * 2)
            r = azar(s, col, fila, round((z if t.cara in ("north", "south") else x) * 2))
            return 1 if r < 0.04 * (1 + cant) else -1 if r > 1 - 0.07 * (1 + cant) else None
        if nombre in ("escamas", "plumas"):
            u = (x if t.cara in ("north", "south") else z) * 2
            v = y * 2 if t.cara in LATERALES else z * 2
            w, h = tam * 2, tam * 1.5
            fila = math.floor(v / h)
            du = ((u / w + 0.5 * (fila % 2)) % 1.0) - 0.5
            dv = (v / h) % 1.0
            if nombre == "escamas":
                borde = dv > 0.78 or abs(du) > 0.42
                return -1 if borde else (1 if dv < 0.2 and abs(du) < 0.15 else None)
            return 1 if dv > 0.7 and abs(du) < 0.3 else (-1 if abs(du) > 0.44 else None)
        if nombre in ("placas", "grietas"):
            d1, d2 = _celdas(x, y, z, tam, s)
            borde = (d2 - d1) < 0.32 + 0.4 * cant
            if nombre == "placas":
                return -1 if borde else None
            return color if borde else None
        if nombre == "rombos":
            u = abs(x) / tam
            v = ((z / tam) % 1.0) - 0.5
            if rel_y < 0.45 and t.cara != "up":
                return None
            d = u + abs(v) * 1.6
            return color if 0.28 < d < 0.62 else (-1 if d <= 0.28 else None)
        if nombre == "anillos":
            return color if ((z / tam) % 1.0) < 0.3 + 0.2 * cant else None
        return None

    # ------------------------------------------------------------------ el pintor

    def pintor(self, parte):
        """El pintor de una parte (el nombre del cubo sin el lado: 'pata_dd' -> 'pata')."""

        def p(t):
            col, brilla = self._color(t, parte)
            if self.modo == "brillo":
                return col if (brilla and col is not TRANSPARENTE) else TRANSPARENTE
            return col
        return p

    def _sombrear(self, c, t, fuerte=1):
        """Arriba un paso mas claro, abajo uno mas oscuro; en las caras altas, la orilla de abajo un poco mas."""
        if c is TRANSPARENTE or c[3] == 0:
            return c
        if t.cara == "up":
            return paso(c, 1)
        if t.cara == "down":
            return paso(c, -1)
        if t.th >= 4 and t.j >= t.th - max(1, t.th // 5):
            return paso(c, -1)
        return c

    def _color(self, t, parte):
        f, h = t.f, t.t
        alto = max(1e-6, h[1] - f[1])
        rel_y = (t.y - f[1]) / alto                        # 0 abajo, 1 arriba
        brilla = parte in self.brilla
        c = self.base
        # --- la parte
        if parte in self.extras:
            c = self.extras[parte]
            c, b2 = self._aplicar_patrones(c, t, parte, rel_y)
            return self._sombrear(c, t), brilla or b2
        if parte.startswith(("pata", "pie", "brazo", "canilla", "muslo")):
            c = self.patas
            if self.pezuna is not None and t.y - f[1] < min(1.5, alto * 0.3) and parte.startswith(("pata", "canilla", "pie", "brazo")):
                return self._sombrear(self.pezuna, t), "pezuna" in self.brilla
        elif parte.startswith("boca"):
            return paso(_c("#4A2224"), -1 if t.cara != "up" else 0), False
        elif parte.startswith("mandibula"):
            return self._sombrear(self.hocico, t), brilla
        elif parte.startswith("hocico") or parte.startswith("morro"):
            c = self.hocico
            if self.nariz is not None and t.cara == "north" and rel_y > 0.55:
                ancho = h[0] - f[0]
                dx = abs(t.x - (f[0] + h[0]) / 2)
                if ancho >= 1.5 and 0.15 * ancho < dx < 0.38 * ancho:
                    return self.nariz, False
                if ancho < 1.5 and dx < 0.3:
                    return self.nariz, False
        elif parte.startswith("oreja"):
            c = self.base
            if self.oreja is not None and t.cara == "north":
                ancho = h[0] - f[0]
                if abs(t.x - (f[0] + h[0]) / 2) < ancho * 0.3 and 0.15 < rel_y < 0.85:
                    c = self.oreja
        elif parte.startswith(("cuerno", "asta", "colmillo", "aguijon", "pinza_punta", "garra")):
            c = self.cuerno
            c, b2 = self._aplicar_patrones(paso(c, 1 if rel_y > 0.6 else 0), t, parte, rel_y)
            return self._sombrear(c, t), brilla or b2 or parte in self.brilla
        elif parte.startswith("pico"):
            c = self.pico
            return self._sombrear(c, t), brilla
        elif parte.startswith(("ala", "membrana")):
            c = self.ala
            if self.punta_ala is not None:
                largo = max(h[2] - f[2], h[0] - f[0])
                if t.z > h[2] - largo * 0.35 or (h[2] - f[2] < h[0] - f[0] and abs(t.x) > max(abs(f[0]), abs(h[0])) - largo * 0.3):
                    c = self.punta_ala
        elif parte.startswith("cola"):
            c = self.cola
            if self.punta_cola is not None and parte.endswith(("punta", "2", "3")) and t.z > (f[2] + h[2]) / 2 - 0.5:
                return self._sombrear(self.punta_cola, t), brilla or "punta_cola" in self.brilla
        elif parte.startswith(("cresta", "agalla", "branquia", "aleta_dorsal")):
            c = self.cresta or self.base
            return self._sombrear(c, t), brilla or "cresta" in self.brilla or "agallas" in self.brilla
        elif parte.startswith("cabeza") or parte.startswith("cara"):
            c = self.cara
        elif parte.startswith(("ojo",)):
            return self.ojo, "ojos" in self.brilla
        # el vientre: la cara de abajo y la parte baja de los lados del cuerpo y el cuello
        if self.vientre is not None and parte.startswith(("cuerpo", "cuello", "pecho", "abdomen", "panza")):
            if t.cara == "down" or (t.cara in LATERALES and rel_y < 0.32):
                c = self.vientre
            if parte.startswith(("cuello", "pecho")) and t.cara == "north":
                c = self.vientre
        # la mascara de la cara
        if self.mascara is not None and parte.startswith(("cabeza", "hocico")) and t.cara in LATERALES:
            mc, hasta = self.mascara
            if rel_y < hasta:
                c = mc
        # los patrones
        c, brilla_patron = self._aplicar_patrones(c, t, parte, rel_y)
        c = self._sombrear(c, t)
        # los ojos (los pone el cuerpo en la cabeza)
        ojo = self.ojos.get((tuple(f), tuple(h)))
        if ojo is not None:
            oy, oz, r = ojo
            r *= self.ojo_tam
            if self.ojos_al_frente:
                if t.cara == "north":
                    hit = self._ojo((abs(t.x) - oz) / r, (t.y - oy) / r, r, c)
                    if hit is not None:
                        return hit
            elif t.cara in ("east", "west"):
                hit = self._ojo((oz - t.z) / r, (t.y - oy) / r, r, c)
                if hit is not None:
                    return hit
        return c, brilla or brilla_patron

    def _ojo(self, u, v, r, piel):
        """Un ojo en coordenadas del ojo (u hacia el frente o hacia afuera, v hacia arriba, de -1 a 1).
        Tipos: punto (todo oscuro con su brillo), grande (oscuro y lustroso), redondo (iris con pupila redonda),
        rasgado (pupila vertical: gatos, reptiles), cabra (pupila horizontal), insecto (ojo compuesto lustroso).
        anillo: el borde de color (rapaces, ajolote); ceja: una raya oscura encima."""
        brilla = "ojos" in self.brilla
        t = self.ojo_tipo
        if self.ceja and abs(u) < 1.25 and 1.0 <= v < 1.0 + 1.1 / r:
            return paso(piel, -2), False
        if abs(u) >= 1.0 or abs(v) >= 1.0:
            return None
        if r >= 0.9 and abs(u) > 0.62 and abs(v) > 0.62 and t not in ("insecto",):
            return None                                        # las esquinas: que se vea redondito
        alto = r >= 0.6
        if alto and u > 0.3 and v > 0.3:
            return self.ojo_brillo, brilla                     # el brillito arriba adelante
        if self.anillo is not None and (abs(u) > 0.62 or abs(v) > 0.62):
            return self.anillo, brilla
        iris = self.iris or self.ojo
        pupila = self.ojo if self.iris else paso(self.ojo, -2)
        if t in ("punto", "grande"):
            if t == "grande" and v < -0.35 and u < 0.0:
                return paso(self.ojo, 1), brilla               # reflejo de abajo: se ve hondo y lustroso
            return self.ojo, brilla
        if t == "insecto":
            if (u + v) > 0.4 and alto:
                return paso(self.ojo, 2), brilla
            return (paso(self.ojo, 1) if (round(u * 4) + round(v * 4)) % 2 else self.ojo), brilla
        if t == "rasgado":
            return (pupila if abs(u) < 0.3 else iris), brilla
        if t == "cabra":
            return (pupila if abs(v) < 0.3 and abs(u) < 0.8 else iris), brilla
        return (pupila if abs(u) < 0.55 and abs(v) < 0.55 else iris), brilla      # redondo


def manchar_de_mura(img, sem=7):
    """La version 'manchada' (contagiada de mura) de cualquier textura: manchas negro-moradas que se comen el color y
    venas magenta que brillan. Devuelve (textura, mascara de brillo) como imagenes PIL."""
    from PIL import Image
    w, h = img.size
    src = img.convert("RGBA").load()
    out = Image.new("RGBA", (w, h))
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    po, pm = out.load(), mask.load()
    mura = (40, 22, 48)
    vena = (214, 70, 200)
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                po[x, y] = (0, 0, 0, 0)
                continue
            d1, d2 = _celdas(x * 0.5, y * 0.5, 0.0, 5.0, sem)
            mancha = d1 < 2.0 + 1.2 * azar(sem, x // 6, y // 6)
            borde = (d2 - d1) < 0.35
            gris = (r * 0.3 + g * 0.59 + b * 0.11)
            if mancha:
                k = 0.75
                c = (int(mura[0] * k + gris * 0.25 * (1 - k)), int(mura[1] * k + gris * 0.2 * (1 - k)),
                     int(mura[2] * k + gris * 0.3 * (1 - k)), 255)
                if borde:
                    c = vena + (255,)
                    pm[x, y] = c
            else:                                      # lo sano se ve enfermo: desaturado y frio
                c = (int(r * 0.55 + gris * 0.35), int(g * 0.5 + gris * 0.35), int(b * 0.6 + gris * 0.4), 255)
            po[x, y] = c
    return out, mask
