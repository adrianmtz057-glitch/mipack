"""
ESCULTOR DE BLOQUES: para que los titanes se vean como construcciones de bloques vivas (la hoja de titanes del
usuario). Se esculpe en una rejilla de voxeles (1 voxel = 1 px del modelo; en el juego el titan se agranda con su
ESCALA, asi cada voxel es un bloque grande):

  FORMAS que suman, quitan o repintan material: elipsoides (giradas), capsulas que se adelgazan, tubos que siguen un
    camino, cajas (giradas) y cualquier campo (una funcion de x, y, z)
  REGLAS DE SUPERFICIE: cubrir lo de arriba (musgo, nieve, pasto), salpicar manchas, vetas por posicion
  DECORACIONES (planos y cubitos aparte): lianas y raices que cuelgan, matas y flores encima, carambanos, y piezas
    sueltas (faroles, cascadas)

Al armar en el kit solo salen las caras que se ven, juntadas en rectangulos grandes (planos de una sola cara), con la
textura de cada material bloque por bloque (dibujos de 8x8 en el estilo de Velkia: colores planos y pocos detalles
bien puestos) y la sombra de las esquinas como en Minecraft (oclusion por vertice) ya pintada. Lo que brilla no lleva
sombra y sus colores salen en brillan() para la mascara de brillo.
Las caras entre dos huesos distintos tambien salen: cuando se animen, las juntas no dejan hoyos.
"""

import math

import numpy as np

from .modelo import esquinas
from .textura import hex_a_rgba

N = 8                                     # texeles por cara de voxel

# ------------------------------------------------------------------ dibujos de 8x8
# letras: o contorno, s sombra, b base, l luz, h brillo ('.' transparente, solo en decoraciones)
PATRONES = {
    "liso": (("bbbbbbbb", "bbbbbblb", "bbbbbbbb", "bbsbbbbb", "bbbbbbbb", "bbbbbbbb", "blbbbsbb", "bbbbbbbb"),
             ("bbbbbbbb", "bbbbbbbb", "bblbbbbb", "bbbbbbbb", "bbbbbsbb", "bbbbbbbb", "bbbbbbbb", "bbbsbbbl")),
    "musgo": (("bblbbsbb", "blhlbbbb", "bblbbbbl", "sbbbbblh", "bbbsbbbl", "bbblbbbb", "blbhlbsb", "bbblbbbb"),
              ("bbbbblbb", "bsbblhlb", "bbbbblbb", "blbbbbbs", "lhlbsbbb", "blbbbbbb", "bbbbblbb", "bbsbblhb")),
    "hojas": (("blbbsbbl", "lhlbssbb", "blbbbblb", "sbbsblhl", "ssbbbblb", "bblbbsbb", "blhlbssb", "bblbbbbl"),
              ("bbsblbbb", "bsslhlbs", "bbbblbbb", "lbbsbbsb", "hlbssblh", "lbbbbbbl", "bbblbsbb", "sbbhlbss")),
    "corteza": (("bsbblbsb", "bsbblbsb", "bsblbbsb", "bsblbbbs", "bsblbbbs", "sbblbsbs", "sbbblsbb", "sbbblsbb"),
                ("bslbbsbb", "bslbbsbl", "bsbbbsbl", "sblbbsbl", "sblbsbbl", "sbbbsblb", "bsbbsblb", "bsbbsblb")),
    "piedra": (("bbbbsbbb", "blbbsbbl", "bbbsbbbb", "ssssbbbb", "bbbbsssb", "blbbbbsb", "bbbbblsb", "bbbbbbsb"),
               ("bbsbbbbb", "blsbbblb", "bbsssbbb", "bbbbsbbb", "sbbbbsss", "sblbbbbb", "sbbbbblb", "bsbbbbbb")),
    "ladrillo": (("ssssssss", "lbbbsbbb", "bbbbsbbb", "bbbbsbbb", "ssssssss", "bbsbbblb", "bbsbbbbb", "bbsbbbbb"),
                 ("ssssssss", "bbbslbbb", "bbbsbbbb", "bbbsbbbb", "ssssssss", "lbbbbbsb", "bbbbbbsb", "bbbbbbsb")),
    "tallado": (("ssssssss", "slllllls", "slbbbbbs", "slbsbbbs", "slbbbbbs", "slbbbsbs", "sbbbbbbs", "ssssssss"),
                ("ssssssss", "sllllllb", "slbbbbbs", "slbbbbbs", "slbbsbbs", "slbbbbbs", "sbbbbbbs", "ssssssss")),
    "arena": (("bbbbbbbb", "bblbbbbb", "bbbbbsbb", "bbbbbbbb", "bsbbbbbl", "bbbblbbb", "bbbbbbbb", "blbbbbsb"),
              ("bbbbbbbb", "bbbbbblb", "bsbbbbbb", "bbbbbbbb", "bbblbbbb", "bbbbbbsb", "blbbbbbb", "bbbbsbbb")),
    "escamas": (("bllbbllb", "lbbslbbs", "bbbsbbbs", "sssbsssb", "llbbllbb", "bbslbbsl", "bbsbbbsb", "ssbsssbs"),
                ("llbbllbb", "bbslbbsl", "bbsbbbsb", "ssbsssbs", "bllbbllb", "lbbslbbs", "bbbsbbbs", "sssbsssb")),
    "hielo": (("hhhhhhhh", "lllhllll", "llhlllll", "lhllllbl", "hlllllbl", "lllllbll", "llllblll", "bllbllll"),
              ("hhhhhhhh", "llllhlll", "lllhllll", "lllhllbl", "llhlllbl", "lhllllll", "hlllbbll", "llllllll")),
    "nieve": (("hhhhhhhh", "hhhhlhhh", "hhhhhhhh", "hlhhhhhh", "hhhhhhlh", "hhhhhhhh", "hhhlhhhh", "hhhhhhhh"),
              ("hhhhhhhh", "hhhhhhhh", "hhlhhhhh", "hhhhhhhh", "hhhhhlhh", "hlhhhhhh", "hhhhhhhh", "hhhhhhlh")),
    "lana": (("blbsblbb", "blbsblbs", "blbbsbbs", "lbbbsblb", "lbsbbblb", "lbsblbbs", "bbsblbbs", "bsbblbsb"),
             ("bbsblbbl", "sbsblbbl", "sbbsbbbl", "blbsbbbl", "blbbbsbl", "sbblbsbl", "sbblbsbb", "bsblbbsb")),
    "brillo": (("bbllllbb", "blhhhhlb", "lhhhhhhl", "lhhhhhhl", "lhhhhhhl", "lhhhhhhl", "blhhhhlb", "bbllllbb"),
               ("bbllllbb", "blhhhhlb", "lhhhhhhl", "lhhhhhhl", "lhhhhhhl", "lhhhhhhl", "blhhhhlb", "bbllllbb")),
    "agua": (("bbbbbbbb", "blllbbbb", "bbbbbbbb", "bbbbblll", "bbbbbbbb", "bbllbbbb", "bbbbbbbb", "lbbbbbll"),
             ("bbbbbbbb", "bbbblllb", "bbbbbbbb", "llbbbbbb", "bbbbbbbb", "bbbbbllb", "bbbbbbbb", "blllbbbb")),
    "madera": (("bbbbbbbb", "bblbbbbb", "ssssssss", "bbbbbbbb", "bbbbblbb", "ssssssss", "bbbbbbbb", "blbbbbbb"),
               ("bbbbbbbb", "bbbbbblb", "ssssssss", "bbbbbbbb", "blbbbbbb", "ssssssss", "bbbbbbbb", "bbbblbbb")),
    "piel": (("bbbbbbbb", "bblbbbbb", "bbbbbbbb", "bbbbbblb", "bbbbbbbb", "blbbbbbb", "bbbbblbb", "bbbbbbbb"),
             ("bbbbbbbb", "bbbbblbb", "blbbbbbb", "bbbbbbbb", "bbbblbbb", "bbbbbbbb", "bblbbbbb", "bbbbbbbl")),
    "rayas": (("llllllll", "bbbbbbbb", "bbbbbbbb", "ssssssss", "llllllll", "bbbbbbbb", "bbbbbbbb", "ssssssss"),
              ("llllllll", "bbbbbbbb", "bbbbbbbb", "ssssssss", "llllllll", "bbbbbbbb", "bbbbbbbb", "ssssssss")),
}

# letras -> indice de tono
_LETRA = {"o": "o", "s": "s", "b": "b", "l": "l", "h": "h"}


def _azar(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def hash3(i, j, k, s=0.0):
    """Un numero fijo entre 0 y 1 por voxel (para repartir cosas; vectorizado con numpy)."""
    v = np.sin(i * 12.9898 + j * 78.233 + k * 37.719 + s * 4.581) * 43758.5453
    return v - np.floor(v)


def _rgba(c):
    return np.array(hex_a_rgba(c), dtype=np.float64)


def dibujo8(filas, colores):
    """Un dibujo de 8x8 (o NxN): letras -> colores (dict letra -> hex; '.' transparente). Devuelve uint8 (N, N, 4)."""
    img = np.zeros((len(filas), len(filas[0]), 4), dtype=np.float64)
    for j, fila in enumerate(filas):
        for i, ch in enumerate(fila):
            if ch != "." and ch in colores:
                img[j, i] = _rgba(colores[ch])
    if img.shape[0] != N:
        k = N / img.shape[0]
        idx = (np.arange(N) / k).astype(int)
        img = img[idx][:, idx]
    return img


class Material:
    """Un material de bloque: tonos {o, s, b, l, h} y un patron (nombre de PATRONES o una lista de dibujos propios).
    brilla: no lleva sombra y entra a la mascara de brillo. arriba: otro patron para la cara de arriba (ej. pasto)."""

    def __init__(self, nombre, tonos, patron="liso", brilla=False, arriba=None, abajo=None):
        self.nombre, self.tonos, self.brilla = nombre, dict(tonos), brilla
        self.tonos.setdefault("o", self.tonos.get("s"))
        self.tonos.setdefault("h", self.tonos.get("l"))
        self.lados = self._variantes(patron)
        self.arriba = self._variantes(arriba) if arriba else self.lados
        self.abajo = self._variantes(abajo) if abajo else self.lados

    def _variantes(self, patron):
        dibujos = PATRONES[patron] if isinstance(patron, str) else patron
        return [dibujo8(d, self.tonos) for d in dibujos]

    def colores(self):
        return sorted({self.tonos[k] for k in ("o", "s", "b", "l", "h")})


# sombra de las esquinas: cada combinacion de los 4 valores de esquina (0..3) -> factor por texel (N x N)
_AO_NIVEL = np.array([0.58, 0.72, 0.86, 1.0])
_F = (np.arange(N) + 0.5) / N


def _tabla_ao():
    tabla = {}
    fu, fv = np.meshgrid(_F, _F)                  # [fila (v), columna (u)]
    for a00 in range(4):
        for a10 in range(4):
            for a01 in range(4):
                for a11 in range(4):
                    v = (_AO_NIVEL[a00] * (1 - fu) * (1 - fv) + _AO_NIVEL[a10] * fu * (1 - fv)
                         + _AO_NIVEL[a01] * (1 - fu) * fv + _AO_NIVEL[a11] * fu * fv)
                    tabla[(a00, a10, a01, a11)] = np.round(v / 0.07) * 0.07     # escalones, no degradado
    return tabla


_AO = _tabla_ao()

CARA = {(0, 1): "east", (0, -1): "west", (1, 1): "up", (1, -1): "down", (2, -1): "north", (2, 1): "south"}


class Escultor:
    def __init__(self, nombre, desde, hasta):
        """La rejilla cubre de 'desde' a 'hasta' (px del modelo, se redondea a voxeles enteros)."""
        self.nombre = nombre
        self.o = np.array([math.floor(v) for v in desde], dtype=int)
        fin = np.array([math.ceil(v) for v in hasta], dtype=int)
        self.n = tuple(int(v) for v in fin - self.o)
        self.mat = np.zeros(self.n, dtype=np.int16)
        self.hue = np.zeros(self.n, dtype=np.int16)
        self.materiales = [None]
        self.huesos = [None]
        self.pivotes = {}
        self.decor = []                          # (hueso, nombre, desde, hasta, cara(s), imagen, brilla, rot, origen)

    # ------------------------------------------------------------ registro
    def material(self, *args, **kw):
        m = args[0] if isinstance(args[0], Material) else Material(*args, **kw)
        self.materiales.append(m)
        return len(self.materiales) - 1

    def hueso(self, ruta, pivote):
        if ruta in self.huesos:
            return self.huesos.index(ruta)
        self.huesos.append(ruta)
        self.pivotes[ruta] = tuple(pivote)
        return len(self.huesos) - 1

    # ------------------------------------------------------------ formas
    def _rejilla(self, lo, hi):
        i0 = [max(0, math.floor(lo[a] - self.o[a])) for a in range(3)]
        i1 = [min(self.n[a], math.ceil(hi[a] - self.o[a]) + 1) for a in range(3)]
        if any(i1[a] <= i0[a] for a in range(3)):
            return None
        ejes = [self.o[a] + np.arange(i0[a], i1[a]) + 0.5 for a in range(3)]
        X, Y, Z = np.meshgrid(*ejes, indexing="ij")
        return (slice(i0[0], i1[0]), slice(i0[1], i1[1]), slice(i0[2], i1[2])), X, Y, Z

    def campo(self, f, lo, hi, mat, hueso, modo="sumar"):
        """Aplica una forma dada como funcion f(X, Y, Z) -> mascara (centros de voxel en px) dentro de lo..hi. mat
        puede ser un numero o una funcion (X, Y, Z) -> numeros. modos: sumar (solo donde no hay), encima (pisa lo
        que haya), restar (quita), pintar (cambia el material de lo que ya hay, sin cambiar su hueso)."""
        r = self._rejilla(lo, hi)
        if r is None:
            return
        sl, X, Y, Z = r
        m = f(X, Y, Z)
        if not m.any():
            return
        M, H = self.mat[sl], self.hue[sl]
        valor = mat(X, Y, Z) if callable(mat) else mat
        if modo == "restar":
            M[m] = 0
            H[m] = 0
            return
        if modo == "sumar":
            m = m & (M == 0)
        elif modo == "pintar":
            m = m & (M > 0)
        M[m] = valor[m] if isinstance(valor, np.ndarray) else valor
        if modo != "pintar" and hueso:
            H[m] = hueso

    def elipsoide(self, c, r, mat, hueso, modo="sumar", rot=None):
        r = (r, r, r) if np.isscalar(r) else r
        R = _matriz(rot) if rot else None
        ext = max(r) if R is not None else None

        def f(X, Y, Z):
            P = np.stack([X - c[0], Y - c[1], Z - c[2]], axis=-1)
            if R is not None:
                P = P @ R                         # al marco propio de la elipsoide
            return (P[..., 0] / r[0]) ** 2 + (P[..., 1] / r[1]) ** 2 + (P[..., 2] / r[2]) ** 2 <= 1.0
        e = (ext, ext, ext) if ext else r
        self.campo(f, [c[a] - e[a] - 1 for a in range(3)], [c[a] + e[a] + 1 for a in range(3)], mat, hueso, modo)

    def capsula(self, a, b, ra, rb, mat, hueso, modo="sumar", achata=None, ejes=None):
        """Del punto a (radio ra) al b (radio rb): cono con puntas redondas. achata=ky aplasta en Y; ejes=(kx, ky,
        kz) aplasta o estira en cada eje (ej. una cola angosta y alta: (0.5, 1.2, 1))."""
        a, b = np.array(a, float), np.array(b, float)
        d = b - a
        dd = max(1e-9, float(d @ d))
        k = np.array(ejes if ejes else (1.0, achata or 1.0, 1.0), float)

        def f(X, Y, Z):
            P = np.stack([X - a[0], Y - a[1], Z - a[2]], axis=-1)
            t = np.clip((P @ d) / dd, 0.0, 1.0)
            Q = (P - t[..., None] * d) / k
            return np.sqrt((Q ** 2).sum(-1)) <= ra + (rb - ra) * t
        r = max(ra, rb) * float(k.max())
        lo = np.minimum(a, b) - r - 1
        hi = np.maximum(a, b) + r + 1
        self.campo(f, lo, hi, mat, hueso, modo)

    def tubo(self, camino, mat, hueso, modo="sumar", achata=None, ejes=None):
        """Camino de puntos (x, y, z, r): capsulas de punto a punto."""
        for p0, p1 in zip(camino, camino[1:]):
            self.capsula(p0[:3], p1[:3], p0[3], p1[3], mat, hueso, modo, achata, ejes)

    def superelipsoide(self, c, r, mat, hueso, modo="sumar", p=4.0, rot=None):
        """Como la elipsoide pero mas cuadrada (p = 2 es elipsoide; 3 o 4, una caja de esquinas redondas)."""
        r = (r, r, r) if np.isscalar(r) else r
        R = _matriz(rot) if rot else None

        def f(X, Y, Z):
            P = np.stack([X - c[0], Y - c[1], Z - c[2]], axis=-1)
            if R is not None:
                P = P @ R
            return (np.abs(P[..., 0] / r[0]) ** p + np.abs(P[..., 1] / r[1]) ** p + np.abs(P[..., 2] / r[2]) ** p) <= 1.0
        e = (max(r),) * 3 if R is not None else r
        self.campo(f, [c[a] - e[a] - 1 for a in range(3)], [c[a] + e[a] + 1 for a in range(3)], mat, hueso, modo)

    def caja(self, desde, hasta, mat, hueso, modo="sumar", rot=None, centro=None):
        lo, hi = np.minimum(desde, hasta), np.maximum(desde, hasta)
        if not rot:
            def f(X, Y, Z):
                return (X >= lo[0]) & (X <= hi[0]) & (Y >= lo[1]) & (Y <= hi[1]) & (Z >= lo[2]) & (Z <= hi[2])
            self.campo(f, lo, hi, mat, hueso, modo)
            return
        c = np.array(centro if centro is not None else (lo + hi) / 2, float)
        R = _matriz(rot)
        lo_, hi_ = lo - c, hi - c

        def f(X, Y, Z):
            P = np.stack([X - c[0], Y - c[1], Z - c[2]], axis=-1) @ R
            return ((P[..., 0] >= lo_[0]) & (P[..., 0] <= hi_[0]) & (P[..., 1] >= lo_[1]) & (P[..., 1] <= hi_[1])
                    & (P[..., 2] >= lo_[2]) & (P[..., 2] <= hi_[2]))
        e = float(np.linalg.norm(np.maximum(abs(lo_), abs(hi_)))) + 1
        self.campo(f, c - e, c + e, mat, hueso, modo)

    # ------------------------------------------------------------ superficie
    def solido(self):
        return self.mat > 0

    def _vecino(self, s, eje, signo):
        """s desplazado: en cada voxel, si el vecino en esa direccion es solido (fuera de la rejilla: vacio)."""
        v = np.zeros_like(s)
        if signo > 0:
            idx_d = [slice(None)] * 3
            idx_o = [slice(None)] * 3
            idx_d[eje], idx_o[eje] = slice(0, -1), slice(1, None)
        else:
            idx_d = [slice(None)] * 3
            idx_o = [slice(None)] * 3
            idx_d[eje], idx_o[eje] = slice(1, None), slice(0, -1)
        v[tuple(idx_d)] = s[tuple(idx_o)]
        return v

    def expuestos(self, eje=1, signo=1):
        s = self.solido()
        return s & ~self._vecino(s, eje, signo)

    def superficie(self):
        s = self.solido()
        m = np.zeros_like(s)
        for eje in range(3):
            for signo in (1, -1):
                m |= s & ~self._vecino(s, eje, signo)
        return m

    def _indices(self):
        return np.meshgrid(*[np.arange(n) for n in self.n], indexing="ij")

    def cubrir(self, mat, solo=None, prob=1.0, semilla=0.0, grosor=1, donde=None, lado=(1, 1)):
        """Lo de arriba (la capa expuesta hacia +Y, y 'grosor' voxeles hacia adentro) se vuelve 'mat'. solo: lista de
        materiales que se cubren. donde: funcion (X, Y, Z) -> mascara para limitar la zona. lado=(eje, signo): otra
        direccion (ej. (1, -1) la panza)."""
        eje, signo = lado
        s = self.solido()
        tapa = s & ~self._vecino(s, eje, signo)
        m = tapa.copy()
        cur = tapa
        for _ in range(grosor - 1):
            cur = self._vecino(cur, eje, signo) & s            # el siguiente hacia adentro
            m |= cur
        self._aplicar_regla(m, mat, solo, prob, semilla, donde)

    def salpicar(self, mat, prob, solo=None, semilla=0.0, donde=None, solo_superficie=True):
        m = self.superficie() if solo_superficie else self.solido()
        self._aplicar_regla(m, mat, solo, prob, semilla, donde)

    def _aplicar_regla(self, m, mat, solo, prob, semilla, donde):
        I, J, K = self._indices()
        if solo is not None:
            m &= np.isin(self.mat, solo)
        if prob < 1.0:
            m &= hash3(I, J, K, semilla) < prob
        if donde is not None:
            X, Y, Z = (self.o[a] + G + 0.5 for a, G in enumerate((I, J, K)))
            m &= donde(X, Y, Z)
        self.mat[m] = mat

    def vetas(self, f, solo=None, donde=None):
        """Material por posicion: f(X, Y, Z, M) -> nuevos materiales (o 0 para dejarlo) para los voxeles solidos."""
        I, J, K = self._indices()
        X, Y, Z = (self.o[a] + G + 0.5 for a, G in enumerate((I, J, K)))
        nuevo = f(X, Y, Z, self.mat)
        m = self.solido() & (nuevo > 0)
        if solo is not None:
            m &= np.isin(self.mat, solo)
        if donde is not None:
            m &= donde(X, Y, Z)
        self.mat[m] = nuevo[m]

    # ------------------------------------------------------------ decoraciones
    def pieza(self, hueso, nombre, desde, hasta, imagen, caras=None, brilla=False, rot=None, origen=None):
        """Una pieza suelta (cubito o plano) con su imagen: un dict cara -> imagen uint8 (h, w, 4), o una sola imagen
        para todas las caras (se estira o repite a lo que mida cada cara)."""
        self.decor.append((hueso, nombre, desde, hasta, caras, imagen, brilla, rot, origen))

    def colgar(self, dibujo, prob, largo, solo=None, semilla=0.0, punta=None, ancho=1.0, donde=None, hueso=None,
               brilla=False):
        """Cuelgan tiras (lianas, raices, musgo) de la cara de abajo de los voxeles: dos planos en cruz por tira.
        dibujo: imagen de NxN que se repite a lo largo; punta: la imagen del ultimo tramo. largo=(min, max) voxeles."""
        s = self.solido()
        abajo = s & ~self._vecino(s, 1, -1)
        I, J, K = self._indices()
        if solo is not None:
            abajo &= np.isin(self.mat, solo)
        abajo &= hash3(I, J, K, semilla + 11.0) < prob
        if donde is not None:
            X, Y, Z = (self.o[a] + G + 0.5 for a, G in enumerate((I, J, K)))
            abajo &= donde(X, Y, Z)
        for i, j, k in np.argwhere(abajo):
            L = int(round(largo[0] + (largo[1] - largo[0]) * float(hash3(i, j, k, semilla + 23.0))))
            if L <= 0:
                continue
            h = self.hue[i, j, k] if hueso is None else hueso
            x, y, z = self.o[0] + i + 0.5, self.o[1] + j, self.o[2] + k + 0.5
            img = _tira(dibujo, punta, L)
            g = float(hash3(i, j, k, semilla + 5.0)) * 0.6 - 0.3
            w = ancho / 2
            self.decor.append((h, f"cuelga_{i}_{j}_{k}_a", (x - w, y - L, z + g * 0.3), (x + w, y, z + g * 0.3),
                               ("north", "south"), img, brilla, None, None))
            self.decor.append((h, f"cuelga_{i}_{j}_{k}_b", (x + g * 0.3, y - L, z - w), (x + g * 0.3, y, z + w),
                               ("east", "west"), img, brilla, None, None))

    def plantar(self, dibujo, prob, alto=1.0, solo=None, semilla=0.0, donde=None, hueso=None, brilla=False):
        """Matas y flores en cruz encima de los voxeles de arriba (dos planos de 1 voxel de ancho)."""
        s = self.solido()
        tapa = s & ~self._vecino(s, 1, 1)
        I, J, K = self._indices()
        if solo is not None:
            tapa &= np.isin(self.mat, solo)
        tapa &= hash3(I, J, K, semilla + 31.0) < prob
        if donde is not None:
            X, Y, Z = (self.o[a] + G + 0.5 for a, G in enumerate((I, J, K)))
            tapa &= donde(X, Y, Z)
        for i, j, k in np.argwhere(tapa):
            h = self.hue[i, j, k] if hueso is None else hueso
            x, y, z = self.o[0] + i + 0.5, self.o[1] + j + 1, self.o[2] + k + 0.5
            img = dibujo
            self.decor.append((h, f"mata_{i}_{j}_{k}_a", (x - 0.5, y, z), (x + 0.5, y + alto, z), ("north", "south"),
                               img, brilla, (0.0, 45.0, 0.0), (x, y, z)))
            self.decor.append((h, f"mata_{i}_{j}_{k}_b", (x - 0.5, y, z), (x + 0.5, y + alto, z), ("north", "south"),
                               img, brilla, (0.0, -45.0, 0.0), (x, y, z)))

    def carambanos(self, mat, prob, largo, solo=None, semilla=0.0, donde=None):
        """Carambanos: dos o tres cubitos que se adelgazan, colgando de la cara de abajo."""
        m = self.materiales[mat]
        s = self.solido()
        abajo = s & ~self._vecino(s, 1, -1)
        I, J, K = self._indices()
        if solo is not None:
            abajo &= np.isin(self.mat, solo)
        abajo &= hash3(I, J, K, semilla + 41.0) < prob
        if donde is not None:
            X, Y, Z = (self.o[a] + G + 0.5 for a, G in enumerate((I, J, K)))
            abajo &= donde(X, Y, Z)
        for i, j, k in np.argwhere(abajo):
            L = largo[0] + (largo[1] - largo[0]) * float(hash3(i, j, k, semilla + 43.0))
            h = self.hue[i, j, k]
            x, y, z = self.o[0] + i + 0.5, self.o[1] + j, self.o[2] + k + 0.5
            tramos = 3 if L > 2.5 else 2
            for t in range(tramos):
                w = 0.42 * (1 - t / tramos) + 0.06
                y1 = y - L * t / tramos
                y0 = y - L * (t + 1) / tramos
                self.decor.append((h, f"caramb_{i}_{j}_{k}_{t}", (x - w, y0, z - w), (x + w, y1, z + w), None,
                                   m.lados[t % len(m.lados)], m.brilla, None, None))

    # ------------------------------------------------------------ armar en el kit
    def armar(self, p, semilla=0.0):
        """Pasa todo al modelo del kit (p: Personaje o algo con .m). Devuelve cuantos planos salieron."""
        modelo = p.m
        s = self.solido()
        ocupa = np.pad(s, 1)                                    # para la sombra de las esquinas (vecinos fuera = vacio)
        total = 0
        for b in range(1, len(self.huesos)):
            ruta = self.huesos[b]
            del_hueso = s & (self.hue == b)
            if not del_hueso.any():
                continue
            for eje in range(3):
                for signo in (1, -1):
                    vecino_mio = self._vecino(del_hueso, eje, signo)
                    cara_ve = del_hueso & ~vecino_mio
                    if not cara_ve.any():
                        continue
                    total += self._planos(modelo, ruta, cara_ve, eje, signo, ocupa, semilla)
        for k, (b, nombre, desde, hasta, caras, imagen, brilla, rot, origen) in enumerate(self.decor):
            ruta = self.huesos[b] if isinstance(b, (int, np.integer)) else b
            self._pieza_kit(modelo, ruta, nombre, desde, hasta, caras, imagen, rot, origen)
        modelo.pivotes.update(self.pivotes)
        return total

    def _planos(self, modelo, ruta, cara_ve, eje, signo, ocupa, semilla):
        otros = [a for a in range(3) if a != eje]
        nombre = CARA[(eje, signo)]
        cuantos = 0
        for capa in range(self.n[eje]):
            idx = [slice(None)] * 3
            idx[eje] = capa
            M = cara_ve[tuple(idx)].copy()
            if not M.any():
                continue
            for r0, c0 in np.argwhere(M):
                if not M[r0, c0]:
                    continue
                w = 1
                while c0 + w < M.shape[1] and M[r0, c0 + w]:
                    w += 1
                h = 1
                while r0 + h < M.shape[0] and M[r0 + h, c0:c0 + w].all():
                    h += 1
                M[r0:r0 + h, c0:c0 + w] = False
                desde, hasta = [0.0] * 3, [0.0] * 3
                plano = self.o[eje] + capa + (1 if signo > 0 else 0)
                desde[eje] = hasta[eje] = float(plano)
                desde[otros[0]], hasta[otros[0]] = float(self.o[otros[0]] + r0), float(self.o[otros[0]] + r0 + h)
                desde[otros[1]], hasta[otros[1]] = float(self.o[otros[1]] + c0), float(self.o[otros[1]] + c0 + w)
                img = self._imagen_cara(desde, hasta, nombre, eje, signo, ocupa, semilla)
                lista = img.tolist()
                modelo.cubo(ruta, f"{self.nombre}_{nombre}_{cuantos}_{capa}", desde, hasta,
                            lambda t, L=lista: tuple(L[t.j][t.i]), caras=(nombre,), dens=N, luz=False)
                cuantos += 1
        return cuantos

    def _imagen_cara(self, desde, hasta, nombre, eje, signo, ocupa, semilla):
        tl, tr, bl = (np.array(v, float) for v in esquinas(desde, hasta, nombre))
        du, dv = tr - tl, bl - tl
        w, h = int(round(np.abs(du).sum())), int(round(np.abs(dv).sum()))
        uu, vv = du / max(w, 1), dv / max(h, 1)                  # un voxel en cada direccion de la imagen
        n = np.zeros(3)
        n[eje] = signo
        img = np.zeros((h * N, w * N, 4), dtype=np.uint8)
        eu = np.round(uu).astype(int)
        ev = np.round(vv).astype(int)
        en = n.astype(int)
        for tv in range(h):
            for tu in range(w):
                c = tl + (tu + 0.5) * uu + (tv + 0.5) * vv - 0.5 * n
                vox = np.floor(c - self.o).astype(int)
                i, j, k = vox
                mid = self.mat[i, j, k]
                m = self.materiales[mid]
                if nombre == "up":
                    var = m.arriba
                elif nombre == "down":
                    var = m.abajo
                else:
                    var = m.lados
                hv = (i * 73856093 ^ j * 19349663 ^ k * 83492791 ^ (eje * 2 + (signo > 0)) * 2654435761 ^ int(semilla)) & 0xFFFF
                tile = var[hv % len(var)]
                if nombre not in ("up", "down") and (hv >> 4) & 1:
                    tile = tile[:, ::-1]                         # espejo de lado: menos repeticion
                if m.brilla:
                    out = tile
                else:
                    L = vox + 1 + en                             # la capa de afuera (en la rejilla con orilla)
                    a = []
                    for cv in (-1, 1):
                        for cu in (-1, 1):
                            su = ocupa[tuple(L + cu * eu)]
                            sv = ocupa[tuple(L + cv * ev)]
                            sc = ocupa[tuple(L + cu * eu + cv * ev)]
                            a.append(0 if (su and sv) else 3 - int(su) - int(sv) - int(sc))
                    f = _AO[(a[0], a[1], a[2], a[3])]
                    out = tile.copy()
                    out[..., :3] = tile[..., :3] * f[..., None]
                img[tv * N:(tv + 1) * N, tu * N:(tu + 1) * N] = np.clip(out, 0, 255).astype(np.uint8)
        return img

    def _pieza_kit(self, modelo, ruta, nombre, desde, hasta, caras, imagen, rot, origen):
        c = modelo.cubo(ruta, nombre, desde, hasta, None, rot=rot, origen=origen, caras=caras, dens=N, luz=False)
        if c is None:
            return
        imgs = imagen if isinstance(imagen, dict) else None

        def pintor(t, imgs=imgs, imagen=imagen):
            im = imgs.get(t.cara) if imgs else imagen
            if im is None:
                return (0, 0, 0, 0)
            hh, ww = im.shape[:2]
            jj = min(hh - 1, int(t.j * hh / max(1, t.th))) if hh > t.th else t.j % hh
            ii = min(ww - 1, int(t.i * ww / max(1, t.tw))) if ww > t.tw else t.i % ww
            return tuple(int(v) for v in im[jj, ii])
        c.pintor = pintor

    # ------------------------------------------------------------ datos
    def brillan(self):
        """Los colores que brillan (para la mascara de brillo del exportador)."""
        out = set()
        for m in self.materiales[1:]:
            if m.brilla:
                out.update(m.colores())
        return sorted(out)

    def cuenta(self):
        return {"voxeles": int(self.solido().sum()), "decoraciones": len(self.decor)}


def _tira(dibujo, punta, L):
    """Imagen de una tira colgante de L voxeles: el dibujo repetido y la punta al final (N de ancho, L*N de alto)."""
    partes = [dibujo] * (L - 1) + [punta if punta is not None else dibujo]
    return np.concatenate(partes, axis=0).astype(np.uint8)


def _matriz(rot):
    """Rotacion ZYX de Blockbench (grados); P_mundo = R @ P_propio, asi P_propio = P_mundo @ R."""
    a, b, c = (math.radians(v) for v in rot)
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
