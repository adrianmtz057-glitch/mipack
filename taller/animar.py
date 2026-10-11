"""
Animaciones para GeckoLib hechas desde Python, sin hacerlas a ciegas:
  - Rig: el esqueleto del .geo.json (padres y pivotes) y su cinematica directa (la misma de GeckoLib: cada hueso
    gira Z * Y * X alrededor de su pivote y hereda lo del padre).
  - ik_pata: IK de dos huesos (hombro y codo, o muslo y rodilla) en el plano del giro de la bisagra (eje X del
    padre) para poner el pie justo donde va (en el piso al apoyar), y la muneca o el tobillo que dejan el pie plano.
  - hornear: cada animacion se define como una funcion pose(t) y se hornea a 20 cuadros por segundo (un cuadro por
    tick de Minecraft) con interpolacion lineal: lo que se ve en el GIF es lo que reproduce GeckoLib.
  - exportar: el .animation.json (formato Bedrock 1.8.0) en la convencion de GeckoLib (rotacion -rx, -ry, rz;
    posicion -x, y, z).
  - revisar: pruebas (que nada atraviese el piso, que la animacion en bucle cierre sin brinco) y gif: los cuadros
    renderizados con la reconstruccion de GeckoLib.
Una pose es {hueso: ((rx, ry, rz) grados, (x, y, z) px)} en las coordenadas del kit (las de Blockbench).
"""

import math

from . import geckolib

PASO = 0.05                                   # segundos entre cuadros horneados (un tick)


def suave(t, puntos):
    """Curva suave (catmull-rom) que pasa por los puntos [(t, valor)] (valor numero o tupla); fuera del rango se
    queda en el extremo."""
    if t <= puntos[0][0]:
        return puntos[0][1]
    if t >= puntos[-1][0]:
        return puntos[-1][1]
    for i in range(len(puntos) - 1):
        (t1, p1), (t2, p2) = puntos[i], puntos[i + 1]
        if t1 <= t <= t2:
            p0 = puntos[max(0, i - 1)][1]
            p3 = puntos[min(len(puntos) - 1, i + 2)][1]
            u = (t - t1) / (t2 - t1) if t2 > t1 else 0.0

            def cr(a, b, c, d):
                return 0.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)
            if isinstance(p1, (tuple, list)):
                return tuple(cr(a, b, c, d) for a, b, c, d in zip(p0, p1, p2, p3))
            return cr(p0, p1, p2, p3)
    return puntos[-1][1]


def facil(u):
    """Entrada y salida suaves (0 a 1)."""
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


class Rig:
    def __init__(self, geo):
        huesos = geo["minecraft:geometry"][0]["bones"]
        self.padre = {b["name"]: b.get("parent") for b in huesos}
        self.pivote = {b["name"]: (-b["pivot"][0], b["pivot"][1], b["pivot"][2]) for b in huesos}
        self.geo = geo

    def transformaciones(self, pose):
        """{hueso: Transformacion de sus puntos (en px del modelo) al mundo} para la pose."""
        cache = {}

        def de(n):
            if n in cache:
                return cache[n]
            rot, tras = pose.get(n, ((0, 0, 0), (0, 0, 0)))
            T = geckolib._giro_en(self.pivote[n], tuple(math.radians(a) for a in rot), tuple(tras))
            if self.padre[n]:
                T = de(self.padre[n]).despues(T)
            cache[n] = T
            return T
        return {n: de(n) for n in self.padre}

    def a_archivo(self, pose):
        """La pose en la convencion del archivo de animacion de GeckoLib."""
        return {n: ((-r[0], -r[1], r[2]), (-p[0], p[1], p[2])) for n, (r, p) in pose.items()}

    def quads(self, pose):
        return geckolib.reconstruir(self.geo, self.a_archivo(pose))

    def inclinacion(self, pose, n):
        """Suma de los giros en X de los antepasados de n (para dejar el pie plano)."""
        total, h = 0.0, self.padre[n]
        while h:
            total += pose.get(h, ((0, 0, 0), (0, 0, 0)))[0][0]
            h = self.padre[h]
        return total


def _inversa(T):
    Rt = tuple(tuple(T.R[j][i] for j in range(3)) for i in range(3))
    t = tuple(-sum(Rt[i][k] * T.t[k] for k in range(3)) for i in range(3))
    return geckolib.Transformacion(Rt, t)


def ik_pata(rig, pose, cadena, objetivo, extra=0.0):
    """Pone en la pose los giros en X de los tres huesos de la pata (cadena: hombro, codo, mano) para que el pivote
    de la mano quede en 'objetivo' (mundo) y el pie quede plano (mas 'extra' grados de la mano). Devuelve True si
    alcanzo sin estirar de mas."""
    a, b, c = cadena
    T = rig.transformaciones(pose)
    padre = rig.padre[a]
    local = _inversa(T[padre])(objetivo) if padre else objetivo
    s, e, w = rig.pivote[a], rig.pivote[b], rig.pivote[c]

    def yz(p):
        return (p[1], p[2])
    s2, e2, w2, t2 = yz(s), yz(e), yz(w), yz(local)
    l1, l2 = math.dist(s2, e2), math.dist(e2, w2)
    d = math.dist(s2, t2)
    alcanza = abs(l1 - l2) + 1e-3 <= d <= l1 + l2 - 1e-3
    d = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, d))
    ang = lambda p, q: math.atan2(q[1] - p[1], q[0] - p[0])          # noqa: E731  (angulo en (y, z))
    # hacia donde dobla el codo en reposo (que siga doblando igual)
    cruz = (e2[0] - s2[0]) * (w2[1] - e2[1]) - (e2[1] - s2[1]) * (w2[0] - e2[0])
    signo = -1.0 if cruz > 0 else 1.0
    alfa = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    f1 = ang(s2, t2) + signo * alfa
    e_n = (s2[0] + l1 * math.cos(f1), s2[1] + l1 * math.sin(f1))
    a1 = f1 - ang(s2, e2)
    a2 = (ang(e_n, t2) - ang(e2, w2)) - a1
    a1, a2 = (math.atan2(math.sin(x), math.cos(x)) for x in (a1, a2))
    gx = math.degrees(a1)
    cx = math.degrees(a2)
    mx = -(rig.inclinacion(pose, a) + gx + cx) + extra
    for n, x in ((a, gx), (b, cx), (c, mx)):
        rot, tras = pose.get(n, ((0, 0, 0), (0, 0, 0)))
        pose[n] = ((x, rot[1], rot[2]), tras)
    return alcanza


def hornear(rig, nombre, largo, pose_en, bucle=True):
    """La animacion horneada: {hueso: {'rotation': {t: [..]}, 'position': {t: [..]}}} a un cuadro por tick, mas
    los cuadros mismos (para revisar y renderizar)."""
    n = int(round(largo / PASO))
    cuadros = [(round(i * PASO, 4), pose_en(i * PASO)) for i in range(n + 1)]
    huesos = {}
    for t, pose in cuadros:
        for h, ((rx, ry, rz), (px, py, pz)) in rig.a_archivo(pose).items():
            d = huesos.setdefault(h, {"rotation": {}, "position": {}})
            d["rotation"][f"{t:.4g}"] = [round(rx, 3), round(ry, 3), round(rz, 3)]
            d["position"][f"{t:.4g}"] = [round(px, 3), round(py, 3), round(pz, 3)]
    for d in huesos.values():                                 # lo que nunca cambia no se escribe
        for clave in ("rotation", "position"):
            valores = list(d[clave].values())
            if all(v == [0, 0, 0] for v in valores):
                del d[clave]
    huesos = {h: d for h, d in huesos.items() if d}
    datos = {"loop": True if bucle is True else bucle, "animation_length": round(largo, 4), "bones": huesos}
    if bucle is False:
        del datos["loop"]
    return datos, cuadros


def exportar(animaciones, identificador):
    """El dict del .animation.json: {'animation.<id>.<nombre>': datos}."""
    return {"format_version": "1.8.0", "animations": {f"animation.{identificador}.{n}": d for n, d in animaciones.items()}}


def revisar(rig, cuadros, bucle, piso=-0.6, cada=2):
    """Pruebas de una animacion horneada: lo mas bajo que llega y que hueso (nada debe atravesar el piso) y, si es en
    bucle, la diferencia entre el primer y el ultimo cuadro (debe ser 0 para que no brinque)."""
    bajo, hueso, cuando = 1e9, None, None
    for t, pose in cuadros[::cada]:
        for P, _uv, _c, _n, h in rig.quads(pose):
            y = min(q[1] for q in P)
            if y < bajo:
                bajo, hueso, cuando = y, h, t
    salto = 0.0
    if bucle and cuadros:
        a, b = cuadros[0][1], cuadros[-1][1]
        for h in set(a) | set(b):
            ra, pa = a.get(h, ((0, 0, 0), (0, 0, 0)))
            rb, pb = b.get(h, ((0, 0, 0), (0, 0, 0)))
            salto = max(salto, max(abs(x - y) for x, y in zip(ra + pa, rb + pb)))
    return {"mas_bajo": round(bajo, 2), "hueso": hueso, "en": cuando, "atraviesa_piso": bajo < piso,
            "brinco_del_bucle": round(salto, 3)}


def sobre_el_piso(rig, pose, cadena, puntos, margen=0.8, vueltas=4):
    """Levanta una cadena de huesos (ej. la cola, o el cuello y la cabeza) lo justo para que sus puntos (en px del
    modelo; por hueso, una lista de los puntos mas bajos de su tramo) no bajen del piso: hueso por hueso, desde la
    base, gira en X lo que haga falta (hacia arriba). Se repite porque en un tramo empinado el giro sube menos."""
    for h, pts in zip(cadena, puntos):
        for _ in range(vueltas):
            T = rig.transformaciones(pose)
            peor = min(pts, key=lambda q: T[h](q)[1])
            y = T[h](peor)[1]
            if y >= margen:
                break
            piv = T[h](rig.pivote[h])
            largo = max(1.0, math.dist(piv, T[h](peor)))
            delta = min(40.0, math.degrees(math.asin(max(-1.0, min(1.0, (margen - y) / largo)))) + 0.5)
            rot, tras = pose.get(h, ((0, 0, 0), (0, 0, 0)))
            lado = -1.0 if peor[2] > rig.pivote[h][2] else 1.0
            pose[h] = ((rot[0] + lado * delta, rot[1], rot[2]), tras)
    return pose


def gif(rig, lienzo, cuadros, ruta, cada=2, vista_=("3/4", 35, 14), centro=(0, 18, 15), radio=56, alto=300):
    """Renderiza los cuadros (con la reconstruccion de GeckoLib) en un GIF."""
    import io
    from PIL import Image, ImageEnhance
    from . import vista
    imgs = []
    for t, pose in cuadros[::cada]:
        caras = geckolib.caras_para_vista(rig.quads(pose))
        buf = io.BytesIO()
        tmp = ruta + ".cuadro.png"
        vista.guardar_vista(None, lienzo, None, tmp, alto_px=alto, centro=centro, radio=radio, vistas=(vista_,),
                            caras=caras)
        imgs.append(ImageEnhance.Brightness(Image.open(tmp).convert("RGB")).enhance(1.5))
        del buf
    imgs[0].save(ruta, save_all=True, append_images=imgs[1:], duration=int(1000 * PASO * cada), loop=0)
    import os
    os.remove(ruta + ".cuadro.png")
    return ruta
