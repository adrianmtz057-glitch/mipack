"""
Version chibi de un personaje ya armado: la cabeza (y lo que va con ella) mas grande, crecida desde el cuello, y el
cuerpo mas chico y achaparrado (mas bajo que ancho). Cada pieza se sigue pintando igual: su pintor la ve donde
estaba (las coordenadas del texel se regresan a las de antes) y la densidad se ajusta para que tenga los mismos
texeles. No es un personaje (no tiene construir()).
"""

import math

from .. import malla as geo


class _Deshecho:
    """Un texel visto en el lugar donde estaba la pieza antes de achibarla: orig = a * nuevo + b, por eje."""
    __slots__ = ("_tx", "_a", "_b")

    def __init__(self, tx, a, b):
        self._tx, self._a, self._b = tx, a, b

    def __getattr__(self, k):
        v = getattr(self._tx, k)
        a, b = self._a, self._b
        if k in ("x", "y", "z"):
            i = "xyz".index(k)
            return a[i] * v + b[i]
        if k in ("f", "t"):
            return tuple(a[i] * v[i] + b[i] for i in range(3))
        if k == "n":                                           # la normal de antes: S * n (S = 1 / a)
            n = tuple(v[i] / a[i] for i in range(3))
            largo = math.sqrt(sum(c * c for c in n)) or 1.0
            return tuple(c / largo for c in n)
        return v


def _deshacer(pintor, a, b):
    return (lambda t: pintor(_Deshecho(t, a, b))) if pintor else pintor


def achibar(p, cabeza=1.35, cuerpo=(0.8, 0.6, 0.8), cuello=24.0, como_cabeza=()):
    """Achibar el personaje p (armado a tamano de jugador, con el cuello en 'cuello'): las piezas de Head (y los
    grupos en como_cabeza) crecen 'cabeza' desde el cuello, que baja con el cuerpo; lo demas se escala 'cuerpo'
    (x, y, z) desde el piso."""
    kx, ky, kz = cuerpo
    nuevo = cuello * ky

    def es_cabeza(hueso):
        return hueso.split("/")[0] == "Head" or hueso in como_cabeza

    def transformacion(hueso):
        """(k por eje, desplazamiento por eje): nuevo = k * orig + d."""
        if es_cabeza(hueso):
            return (cabeza,) * 3, (0.0, nuevo - cuello * cabeza, 0.0)
        return (kx, ky, kz), (0.0, 0.0, 0.0)

    def aplicar(punto, k, d):
        return tuple(k[i] * punto[i] + d[i] for i in range(3))

    m = p.m
    for c in m.cubos:
        k, d = transformacion(c.hueso)
        c.desde, c.hasta, c.origen = (list(aplicar(v, k, d)) for v in (c.desde, c.hasta, c.origen))
        a, b = tuple(1 / x for x in k), tuple(-d[i] / k[i] for i in range(3))
        c.pintor = _deshacer(c.pintor, a, b)
        c.dens = c.dens / min(k)
    for ma in m.mallas:
        k, d = transformacion(ma.hueso)
        ma.vertices = [aplicar(v, k, d) for v in ma.vertices]
        a, b = tuple(1 / x for x in k), tuple(-d[i] / k[i] for i in range(3))
        ma.grupos = [(_deshacer(pin, a, b), poli) for pin, poli in ma.grupos]
        ma.normales = [geo.normal([ma.vertices[i] for i in poli]) for _, poli in ma.grupos]
        ma.dens = ma.dens / min(k)
    for hueso, v in list(m.pivotes.items()):
        k, d = transformacion(hueso)
        m.pivotes[hueso] = aplicar(v, k, d)
    return p
