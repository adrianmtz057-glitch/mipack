package com.mipack.titanes;

import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.function.Predicate;

/**
 * El motor de rutas: busca por donde puede ir un titan sobre el mapa del terreno (A* en las celdas de 8x8), segun como
 * se mueve (caminando, nadando, volando, por las copas o bajo la arena) y lo que aguanta su cuerpo (que tanto sube de
 * una celda a otra, que tan hondo vadea, cuanto mide de ancho: todas las celdas bajo su cuerpo tienen que servir). Las
 * celdas que todavia no se conocen se pueden cruzar pero cuestan mas (cuando se conozcan, el titan vuelve a buscar).
 * Despues endereza el camino (quita las vueltas que no hacen falta).
 */
public final class Rutas {
    /** Como se mueve. */
    public enum Modo { TIERRA, AGUA, AIRE, COPAS, ARENA }

    /**
     * Lo que aguanta un titan: 'radio' en celdas bajo su cuerpo, 'paso' lo maximo que sube o baja entre dos celdas
     * vecinas (bloques), 'vadeo' que tan hondo puede caminar en agua, 'hondo' lo minimo de agua para nadar, y como le
     * gusta cada bioma (multiplica el costo: menos de 1 lo prefiere, 0 no entra).
     */
    public record Perfil(Modo modo, int radio, int paso, int vadeo, int hondo, Map<Terreno.Bioma, Double> gusto) {
        double gusto(Terreno.Bioma b) {
            return this.gusto.getOrDefault(b, 1.0);
        }
    }

    private static final int[][] VECINOS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}, {1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
    private static final double DESCONOCIDA = 2.5;

    private Rutas() {
    }

    /** La celda sola sirve para este perfil (sin mirar a los vecinos). */
    static boolean sirve(Perfil p, Terreno.Celda c) {
        if (c == null)
            return true;
        if (p.gusto(c.bioma()) <= 0)
            return false;
        return switch (p.modo()) {
            case TIERRA, COPAS -> c.sup() != Terreno.Superficie.LAVA && (!c.agua() || c.profundidad() <= p.vadeo());
            case AGUA -> c.agua() && c.profundidad() >= p.hondo();
            case ARENA -> c.sup() == Terreno.Superficie.ARENA;
            case AIRE -> true;
        };
    }

    /** La altura por la que va (para el paso entre celdas): el suelo, las copas o el agua. */
    static int altura(Perfil p, Terreno.Celda c) {
        return p.modo() == Modo.COPAS ? c.copas() : c.suelo();
    }

    private static final class Busqueda {
        final Terreno t;
        final Perfil p;
        final Map<Long, Boolean> cuerpoCabe = new HashMap<>();

        Busqueda(Terreno t, Perfil p) {
            this.t = t;
            this.p = p;
        }

        /** Todas las celdas bajo el cuerpo (radio) sirven y no hay escalones mas altos que el paso. */
        boolean cabe(int cx, int cz) {
            return this.cuerpoCabe.computeIfAbsent(Terreno.clave(cx, cz), k -> {
                Terreno.Celda centro = this.t.celda(cx, cz);
                if (!sirve(this.p, centro))
                    return false;
                if (this.p.modo() == Modo.AIRE)
                    return true;
                int r = this.p.radio();
                for (int i = -r; i <= r; i++)
                    for (int j = -r; j <= r; j++) {
                        if (i * i + j * j > r * r)
                            continue;
                        Terreno.Celda c = this.t.celda(cx + i, cz + j);
                        if (!sirve(this.p, c))
                            return false;
                        if (centro != null && c != null && this.p.modo() != Modo.AGUA
                                && Math.abs(altura(this.p, c) - altura(this.p, centro)) > this.p.paso() * Math.max(1, Math.hypot(i, j)))
                            return false;
                    }
                return true;
            });
        }

        double costo(int ax, int az, int bx, int bz) {
            Terreno.Celda a = this.t.celda(ax, az), b = this.t.celda(bx, bz);
            double d = (ax != bx && az != bz) ? 1.4142 : 1.0;
            if (b == null)
                return d * DESCONOCIDA;
            double c = d * this.p.gusto(b.bioma());
            if (a != null && this.p.modo() != Modo.AIRE && this.p.modo() != Modo.AGUA) {
                int dh = Math.abs(altura(this.p, b) - altura(this.p, a));
                if (dh > this.p.paso())
                    return Double.POSITIVE_INFINITY;
                c += d * 1.5 * dh / Math.max(1, this.p.paso());          // las cuestas cuestan
            }
            if (b.agua() && this.p.modo() == Modo.TIERRA)
                c *= 1.8;                                                    // vadear cansa
            return c;
        }
    }

    private record Nodo(int cx, int cz, double f) {
    }

    /**
     * El camino de 'desde' a 'hasta' (en bloques) como puntos del mundo (x, 0, z): la altura la pone quien lo sigue.
     * Devuelve una lista vacia si no hay camino (o si se pasa de 'maxNodos' celdas revisadas).
     */
    public static List<Vec3> buscar(Terreno t, Perfil p, Vec3 desde, Vec3 hasta, int maxNodos) {
        Busqueda b = new Busqueda(t, p);
        int sx = Terreno.celdaDe(desde.x), sz = Terreno.celdaDe(desde.z);
        int gx = Terreno.celdaDe(hasta.x), gz = Terreno.celdaDe(hasta.z);
        if (!b.cabe(gx, gz)) {
            int[] cerca = celdaCercana(b, gx, gz, 6);
            if (cerca == null)
                return List.of();
            gx = cerca[0];
            gz = cerca[1];
        }
        Map<Long, Double> g = new HashMap<>();
        Map<Long, Long> vino = new HashMap<>();
        PriorityQueue<Nodo> abiertos = new PriorityQueue<>((x, y) -> Double.compare(x.f, y.f));
        long inicio = Terreno.clave(sx, sz), meta = Terreno.clave(gx, gz);
        g.put(inicio, 0.0);
        abiertos.add(new Nodo(sx, sz, heuristica(sx, sz, gx, gz)));
        int revisados = 0;
        while (!abiertos.isEmpty() && revisados < maxNodos) {
            Nodo n = abiertos.poll();
            long k = Terreno.clave(n.cx, n.cz);
            if (k == meta)
                return enderezar(b, reconstruir(vino, meta), desde, hasta);
            double gn = g.getOrDefault(k, Double.POSITIVE_INFINITY);
            if (n.f - heuristica(n.cx, n.cz, gx, gz) > gn + 1e-9)
                continue;                                                  // ya habia uno mejor
            revisados++;
            for (int[] v : VECINOS) {
                int nx = n.cx + v[0], nz = n.cz + v[1];
                if (!b.cabe(nx, nz) && Terreno.clave(nx, nz) != meta)
                    continue;
                if (v[0] != 0 && v[1] != 0 && (!b.cabe(n.cx + v[0], n.cz) || !b.cabe(n.cx, n.cz + v[1])))
                    continue;                                              // no corta esquinas
                double c = b.costo(n.cx, n.cz, nx, nz);
                if (Double.isInfinite(c))
                    continue;
                long nk = Terreno.clave(nx, nz);
                double ng = gn + c;
                if (ng < g.getOrDefault(nk, Double.POSITIVE_INFINITY)) {
                    g.put(nk, ng);
                    vino.put(nk, k);
                    abiertos.add(new Nodo(nx, nz, ng + heuristica(nx, nz, gx, gz)));
                }
            }
        }
        return List.of();
    }

    private static double heuristica(int ax, int az, int bx, int bz) {
        int dx = Math.abs(ax - bx), dz = Math.abs(az - bz);
        return 0.6 * (Math.max(dx, dz) + 0.4142 * Math.min(dx, dz));     // por debajo del costo real (los gustos bajan)
    }

    private static int[] celdaCercana(Busqueda b, int cx, int cz, int radio) {
        for (int r = 1; r <= radio; r++)
            for (int i = -r; i <= r; i++)
                for (int j = -r; j <= r; j++)
                    if ((Math.abs(i) == r || Math.abs(j) == r) && b.cabe(cx + i, cz + j))
                        return new int[]{cx + i, cz + j};
        return null;
    }

    private static List<long[]> reconstruir(Map<Long, Long> vino, long meta) {
        List<long[]> out = new ArrayList<>();
        Long k = meta;
        while (k != null) {
            out.add(new long[]{k >> 32, (int) (long) k});
            k = vino.get(k);
        }
        Collections.reverse(out);
        return out;
    }

    /** Quita los puntos intermedios cuando se puede ir derecho (todas las celdas de la linea sirven). */
    private static List<Vec3> enderezar(Busqueda b, List<long[]> celdas, Vec3 desde, Vec3 hasta) {
        List<Vec3> puntos = new ArrayList<>();
        for (long[] c : celdas)
            puntos.add(new Vec3(c[0] * Terreno.CELDA + Terreno.CELDA / 2.0, 0, c[1] * Terreno.CELDA + Terreno.CELDA / 2.0));
        if (puntos.size() <= 2) {
            puntos.add(new Vec3(hasta.x, 0, hasta.z));
            return puntos;
        }
        List<Vec3> out = new ArrayList<>();
        out.add(puntos.get(0));
        int i = 0;
        while (i < puntos.size() - 1) {
            int j = puntos.size() - 1;
            while (j > i + 1 && !derecho(b, puntos.get(i), puntos.get(j)))
                j--;
            out.add(puntos.get(j));
            i = j;
        }
        return out;
    }

    private static boolean derecho(Busqueda b, Vec3 a, Vec3 c) {
        double d = a.distanceTo(c);
        int pasos = (int) Math.ceil(d / (Terreno.CELDA * 0.5));
        int px = Terreno.celdaDe(a.x), pz = Terreno.celdaDe(a.z);
        for (int k = 1; k <= pasos; k++) {
            Vec3 q = a.lerp(c, k / (double) pasos);
            int cx = Terreno.celdaDe(q.x), cz = Terreno.celdaDe(q.z);
            if (!b.cabe(cx, cz) || Double.isInfinite(b.costo(px, pz, cx, cz)))
                return false;
            Terreno.Celda celda = b.t.celda(cx, cz);
            if (celda == null && b.p.modo() != Modo.AIRE)
                return false;                                              // por lo desconocido, paso a paso
            px = cx;
            pz = cz;
        }
        return true;
    }

    /** La celda conocida mas cercana a 'centro' que cumple 'que' y donde cabe el titan (buscando en anillos). */
    public static Vec3 lugar(Terreno t, Perfil p, Vec3 centro, int radioCeldas, Predicate<Lugar> que) {
        Busqueda b = new Busqueda(t, p);
        int cx = Terreno.celdaDe(centro.x), cz = Terreno.celdaDe(centro.z);
        for (int r = 0; r <= radioCeldas; r++)
            for (int i = -r; i <= r; i++)
                for (int j = -r; j <= r; j++) {
                    if (Math.abs(i) != r && Math.abs(j) != r)
                        continue;
                    Terreno.Celda c = t.celda(cx + i, cz + j);
                    if (c == null || !que.test(new Lugar(t, cx + i, cz + j, c)) || !b.cabe(cx + i, cz + j))
                        continue;
                    return new Vec3((cx + i) * Terreno.CELDA + Terreno.CELDA / 2.0, 0, (cz + j) * Terreno.CELDA + Terreno.CELDA / 2.0);
                }
        return null;
    }

    /** Una celda candidata para un lugar (con acceso a sus vecinas: la orilla del rio, un claro en el bosque...). */
    public record Lugar(Terreno t, int cx, int cz, Terreno.Celda c) {
        public boolean juntoAlAgua() {
            for (int[] v : VECINOS) {
                Terreno.Celda n = this.t.celda(this.cx + v[0] * 2, this.cz + v[1] * 2);
                if (n != null && n.agua())
                    return true;
            }
            return false;
        }

        /** Sin arboles (las copas a la altura del suelo) en 'r' celdas alrededor. */
        public boolean claro(int r) {
            for (int i = -r; i <= r; i++)
                for (int j = -r; j <= r; j++) {
                    Terreno.Celda n = this.t.celda(this.cx + i, this.cz + j);
                    if (n == null || n.copas() - n.suelo() > 2)
                        return false;
                }
            return true;
        }

        /** Con arboles altos (para comer de las copas o caminar sobre ellas). */
        public boolean arbolado() {
            return this.c.copas() - this.c.suelo() >= 5;
        }
    }
}
