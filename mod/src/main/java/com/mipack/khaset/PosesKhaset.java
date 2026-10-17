package com.mipack.khaset;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import java.nio.ByteBuffer;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

/**
 * Donde van las manos de Khaset en cada momento de sus ataques (la palma y la punta de la garra de cada mano), sacado
 * de las mismas animaciones que ve el jugador (PosesKhasetDatos lo genera taller/exportar_mod.py). Con esto el dano
 * cae donde pasa la garra y la presa va en la mano, igual en el servidor y en el cliente.
 * Las coordenadas son las del modelo (px; frente -Z, derecha +X) y aMundo las lleva al mundo con el giro y la escala.
 */
public final class PosesKhaset {
    public enum Punto { PALMA, PUNTA }

    private static final Map<String, Integer> INICIO = new HashMap<>();
    private static final Map<String, Integer> CUADROS = new HashMap<>();
    private static final Map<String, Float> LARGOS = new HashMap<>();
    private static final short[] DATOS;

    static {
        byte[] b = Base64.getDecoder().decode(PosesKhasetDatos.DATOS);
        ByteBuffer buf = ByteBuffer.wrap(b);
        DATOS = new short[b.length / 2];
        for (int i = 0; i < DATOS.length; i++)
            DATOS[i] = buf.getShort();
        int inicio = 0;
        for (int i = 0; i < PosesKhasetDatos.ANIMS.length; i++) {
            INICIO.put(PosesKhasetDatos.ANIMS[i], inicio);
            CUADROS.put(PosesKhasetDatos.ANIMS[i], PosesKhasetDatos.CUADROS[i]);
            inicio += PosesKhasetDatos.CUADROS[i] * 12;
        }
        for (int i = 0; i < PosesKhasetDatos.LARGOS_NOMBRES.length; i++)
            LARGOS.put(PosesKhasetDatos.LARGOS_NOMBRES[i], PosesKhasetDatos.LARGOS[i]);
    }

    private PosesKhaset() {
    }

    /** Lo que dura una animacion (segundos). */
    public static float largo(String anim) {
        return LARGOS.getOrDefault(anim, 1f);
    }

    /** En ticks (redondeado). */
    public static int ticks(String anim) {
        return Math.round(largo(anim) * 20f);
    }

    public static boolean tiene(String anim) {
        return INICIO.containsKey(anim);
    }

    /** La mano ('d' o 'i') en el segundo t de la animacion (interpola entre cuadros; en bucle si 'bucle'). */
    public static Vec3 mano(String anim, char lado, Punto punto, float t, boolean bucle) {
        Integer base = INICIO.get(anim);
        if (base == null)
            return Vec3.ZERO;
        int n = CUADROS.get(anim);
        float f = t * 20f;
        if (bucle)
            f = f % (n - 1);
        f = Mth.clamp(f, 0f, n - 1);
        int i0 = (int) Math.floor(f), i1 = Math.min(n - 1, i0 + 1);
        float k = f - i0;
        int off = (lado == 'd' ? 0 : 6) + (punto == Punto.PALMA ? 0 : 3);
        double[] a = new double[3];
        for (int c = 0; c < 3; c++) {
            float v0 = DATOS[base + i0 * 12 + off + c] / 10f, v1 = DATOS[base + i1 * 12 + off + c] / 10f;
            a[c] = Mth.lerp(k, v0, v1);
        }
        return new Vec3(a[0], a[1], a[2]);
    }

    /**
     * Un punto del modelo (px) en el mundo para una entidad que mira hacia 'giro' (grados, el yaw del cuerpo) y se dibuja
     * 'escala' veces mas grande: lo mismo que hace GeoEntityRenderer (gira 180 - yaw sobre Y).
     */
    public static Vec3 aMundo(Entity e, float giro, Vec3 p, float escala) {
        return e.position().add(rotar(giro, p.scale(escala / 16f)));
    }

    /** Solo el giro (sin la posicion): de las coordenadas del modelo, ya en bloques, al mundo. */
    public static Vec3 rotar(float giro, Vec3 p) {
        double th = Math.toRadians(180f - giro);
        double c = Math.cos(th), s = Math.sin(th);
        return new Vec3(p.x * c + p.z * s, p.y, -p.x * s + p.z * c);
    }

    /** El altar (donde queda la presa acostada) respecto a Khaset, en px del modelo. */
    public static Vec3 altar() {
        float[] a = PosesKhasetDatos.ALTAR;
        return new Vec3(a[0], a[1], a[2]);
    }

    public static float escala() {
        return PosesKhasetDatos.ESCALA;
    }
}
