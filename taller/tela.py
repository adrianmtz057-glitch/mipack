"""
TELA: una simulacion sencilla de tela (dinamica por posiciones) para que un manto caiga de verdad: se suelta una
cobija plana encima del personaje y se deja caer sobre su cuerpo (esferas y capsulas que la tela no atraviesa), con
gravedad y viento. Asi los pliegues salen solos, como en tela de verdad, y el modelo final es la tela ya quieta.

  t = Tela(centro, radio, paso)              # un disco plano (de radio 'radio') a la altura del centro
  t.fijar(mascara) / t.quitar(mascara)       # puntos que no se mueven / hoyos (la cara, las manos)
  t.simular(cuerpo, pasos)                   # cuerpo: lista de Esfera / Capsula
  t.cuadros()                                # los cuadritos de la malla (indices de 4 puntos), por fuera

Todo con numpy; los numeros son px del modelo (16 por bloque).
"""

import math

import numpy as np


class Esfera:
    def __init__(self, c, r):
        self.c, self.r = np.array(c, float), float(r)

    def empujar(self, P, grosor):
        d = P - self.c
        L = np.linalg.norm(d, axis=1)
        m = L < self.r + grosor
        if m.any():
            L = np.maximum(L, 1e-9)
            P[m] = self.c + d[m] / L[m, None] * (self.r + grosor)
        return m


class Capsula:
    """De a (radio ra) a b (radio rb)."""

    def __init__(self, a, b, ra, rb=None):
        self.a, self.b = np.array(a, float), np.array(b, float)
        self.ra, self.rb = float(ra), float(ra if rb is None else rb)

    def empujar(self, P, grosor):
        d = self.b - self.a
        dd = max(1e-9, float(d @ d))
        t = np.clip(((P - self.a) @ d) / dd, 0.0, 1.0)
        Q = self.a + t[:, None] * d
        v = P - Q
        L = np.linalg.norm(v, axis=1)
        r = self.ra + (self.rb - self.ra) * t + grosor
        m = L < r
        if m.any():
            L = np.maximum(L, 1e-9)
            P[m] = Q[m] + v[m] / L[m, None] * r[m, None]
        return m


class Tela:
    def __init__(self, centro, radio, paso, forma=None):
        """Una cobija plana a la altura del centro: un disco de radio 'radio' o, con forma(u, v) -> mascara (u en x,
        v en z, en px desde el centro, dentro de un cuadro de +-radio), la figura que se quiera (ej. un rectangulo con
        las orillas en picos)."""
        self.paso = float(paso)
        n = int(math.ceil(radio / paso))
        ii, jj = np.meshgrid(np.arange(-n, n + 1), np.arange(-n, n + 1), indexing="ij")
        dentro = np.hypot(ii, jj) * paso <= radio if forma is None else forma(ii * paso, jj * paso)
        self.lado = 2 * n + 1
        self.idx = -np.ones(ii.shape, dtype=int)
        self.idx[dentro] = np.arange(int(dentro.sum()))
        self.ij = np.stack([ii[dentro], jj[dentro]], axis=1)          # coordenadas en la cobija (en pasos)
        self.uv = self.ij * paso                                       # en px, desde el centro de la cobija
        self.radio = float(radio)
        c = np.array(centro, float)
        self.P = np.stack([c[0] + self.uv[:, 0], np.full(len(self.uv), c[1]), c[2] + self.uv[:, 1]], axis=1)
        self.antes = self.P.copy()
        self.fijo = np.zeros(len(self.P), bool)
        self.vivo = np.ones(len(self.P), bool)
        self._resortes()

    def _resortes(self):
        """Los resortes en grupos de colores: dentro de un grupo ningun punto se repite, asi cada grupo se corrige de un
        jalon y la tela casi no se estira (como Gauss-Seidel)."""
        self.grupos = []
        for (di, dj, k) in ((1, 0, 1.0), (0, 1, 1.0), (1, 1, 0.8), (1, -1, 0.8), (2, 0, 0.3), (0, 2, 0.3)):
            i0, i1 = max(0, -di), self.lado - max(0, di)
            j0, j1 = max(0, -dj), self.lado - max(0, dj)
            a = self.idx[i0:i1, j0:j1]
            b = self.idx[i0 + di:i1 + di, j0 + dj:j1 + dj]
            ii = np.arange(i0, i1)[:, None] + np.zeros((1, j1 - j0), int)
            jj = np.arange(j0, j1)[None, :] + np.zeros((i1 - i0, 1), int)
            paso = max(abs(di), abs(dj))
            # color: por la paridad del eje en que avanza (con salto de 2: de a cuatro)
            eje = ii if di != 0 else jj
            color = (eje % (2 * paso)) // paso if paso == 2 else eje % 2
            for col in np.unique(color):
                m = (a >= 0) & (b >= 0) & (color == col)
                aa, bb = a[m], b[m]
                vv = self.vivo[aa] & self.vivo[bb]
                aa, bb = aa[vv], bb[vv]
                if len(aa):
                    self.grupos.append((aa, bb, self.paso * math.hypot(di, dj), k))

    def fijar(self, m):
        self.fijo |= m

    def quitar(self, m):
        """Hace hoyos: esos puntos dejan de existir (la cara, por donde salen las manos)."""
        self.vivo &= ~m
        self._resortes()

    def simular(self, cuerpo, pasos=400, vueltas=12, gravedad=0.06, viento=None, amortigua=0.985, grosor=0.6,
                friccion=0.6, a_donde=None):
        """viento: funcion P -> fuerza (N, 3) por paso. a_donde: si se da, los puntos fijos van ahi."""
        g = np.array([0.0, -gravedad, 0.0])
        libres = self.vivo & ~self.fijo
        ancla = self.P[self.fijo][0] if self.fijo.any() else None
        tope = np.linalg.norm(self.uv - self.uv[self.fijo][0], axis=1) * 1.02 if ancla is not None else None
        for paso in range(pasos):
            v = (self.P - self.antes) * amortigua
            self.antes = self.P.copy()
            f = np.broadcast_to(g, self.P.shape).copy()
            if viento is not None:
                f += viento(self.P)
            nuevo = self.P + v + f
            self.P[libres] = nuevo[libres]
            if a_donde is not None:
                self.P[self.fijo] = a_donde
            for _ in range(vueltas):
                for a, b, largo, k in self.grupos:
                    d = self.P[b] - self.P[a]
                    L = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
                    corr = ((L - largo) / L * k)[:, None] * d
                    wa = libres[a].astype(float)
                    wb = libres[b].astype(float)
                    tot = np.maximum(wa + wb, 1e-9)
                    self.P[a] += corr * (wa / tot)[:, None]
                    self.P[b] -= corr * (wb / tot)[:, None]
                if ancla is not None:                                # amarras: nadie se aleja del ancla mas que su largo
                    d = self.P - ancla
                    L = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
                    lejos = (L > tope) & libres
                    self.P[lejos] = ancla + d[lejos] / L[lejos, None] * tope[lejos, None]
                for c in cuerpo:
                    antes = self.P.copy()
                    choco = c.empujar(self.P, grosor) & libres
                    self.P[~libres] = antes[~libres]
                    if choco.any():                                  # friccion: lo que toca el cuerpo se resbala menos
                        self.antes[choco] = self.antes[choco] + (self.P[choco] - self.antes[choco]) * friccion
        return self

    def a_la_orilla(self):
        """Por punto, que tan lejos (px, en la cobija) esta de la orilla mas cercana (de afuera o de un hoyo)."""
        from scipy.ndimage import distance_transform_edt
        m = np.zeros((self.lado, self.lado), bool)
        vivos = self.ij[self.vivo] + self.lado // 2
        m[vivos[:, 0], vivos[:, 1]] = True
        d = distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1] * self.paso
        k = self.ij + self.lado // 2
        return d[k[:, 0], k[:, 1]]

    def cuadros(self):
        """Cuadritos de 4 puntos vivos (a, b, c, d) antihorarios vistos desde el lado de ARRIBA de la cobija (el que
        queda por fuera al caer)."""
        out = []
        I = self.idx
        for i in range(self.lado - 1):
            for j in range(self.lado - 1):
                a, b, c, d = I[i, j], I[i, j + 1], I[i + 1, j + 1], I[i + 1, j]
                if min(a, b, c, d) < 0 or not (self.vivo[a] and self.vivo[b] and self.vivo[c] and self.vivo[d]):
                    continue
                out.append((a, b, c, d))
        return out

    def pegados(self):
        """Los puntos vivos que estan pegados al pedazo mas grande de tela (por cuadritos); los demas son sueltos."""
        from scipy.ndimage import label
        m = np.zeros((self.lado - 1, self.lado - 1), bool)
        for a, b, c, d in self.cuadros():
            i, j = self.ij[a] + self.lado // 2
            m[i, j] = True
        etiq, n = label(m)
        if n <= 1:
            return self.vivo.copy()
        mayor = np.argmax(np.bincount(etiq.ravel())[1:]) + 1
        ok = np.zeros(len(self.P), bool)
        I = self.idx
        for i, j in np.argwhere(etiq == mayor):
            for di, dj in ((0, 0), (0, 1), (1, 0), (1, 1)):
                ok[I[i + di, j + dj]] = True
        return ok & self.vivo

    def normales(self, cuadros):
        n = np.zeros_like(self.P)
        for a, b, c, d in cuadros:
            q = np.cross(self.P[c] - self.P[a], self.P[d] - self.P[b])
            for k in (a, b, c, d):
                n[k] += q
        L = np.linalg.norm(n, axis=1)
        return n / np.maximum(L, 1e-9)[:, None]

    def suavizada(self, cuadros, veces):
        """Las posiciones promediadas con sus vecinos 'veces' veces (para medir pliegues: valles y crestas)."""
        vec = [set() for _ in range(len(self.P))]
        for a, b, c, d in cuadros:
            for x, y in ((a, b), (b, c), (c, d), (d, a)):
                vec[x].add(y)
                vec[y].add(x)
        Q = self.P.copy()
        idx = [np.array(sorted(v)) if v else np.array([k]) for k, v in enumerate(vec)]
        for _ in range(veces):
            Q = np.array([Q[v].mean(axis=0) for v in idx])
        return Q
