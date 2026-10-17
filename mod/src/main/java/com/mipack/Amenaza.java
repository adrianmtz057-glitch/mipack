package com.mipack;

import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * A quien va un jefe cuando pelean muchos: para que no se clave con uno e ignore a los demas. Lleva la cuenta de
 * cuanto le ha pegado cada quien (se va olvidando) y de cuando fue la ultima vez que persiguio a cada uno. Al escoger
 * le gustan: el que mas le pega (asi el que dispara de lejos tambien se gana su visita), el que hace mas que no
 * persigue y un poco de azar; y le cuesta repetir con el de ahora.
 */
public final class Amenaza {
    private final Map<UUID, Float> dano = new HashMap<>();
    private final Map<UUID, Long> ultimaVez = new HashMap<>();
    private UUID actual;

    /** Alguien le pego. */
    public void golpe(Entity quien, float cantidad) {
        if (quien != null)
            this.dano.merge(quien.getUUID(), cantidad, Float::sum);
    }

    /** Cada segundo: lo que le pegaron se va olvidando. */
    public void olvidar() {
        this.dano.replaceAll((k, v) -> v * 0.92f);
        this.dano.values().removeIf(v -> v < 0.5f);
    }

    public UUID actual() {
        return this.actual;
    }

    /**
     * Escoge objetivo entre los candidatos. 'cambiar': acaba de terminar un ataque, asi que prefiere a otro (el de
     * ahora solo repite si no hay nadie mas). 'lejos': la distancia que ya no le importa (mas alla pesa menos).
     */
    public LivingEntity escoger(Entity jefe, List<LivingEntity> candidatos, boolean cambiar, double lejos, long ahora,
                                RandomSource azar) {
        LivingEntity mejor = null;
        double puntos = -1e9;
        for (LivingEntity e : candidatos) {
            double p = 1.0 + Math.min(5.0, this.dano.getOrDefault(e.getUUID(), 0f) / 25.0);
            long ult = this.ultimaVez.getOrDefault(e.getUUID(), ahora - 1200);
            p += Math.min(4.0, (ahora - ult) / 200.0);                    // el que hace mas que no persigue
            double d = e.distanceTo(jefe);
            p -= Math.max(0.0, d - lejos) / 20.0;
            if (e.getUUID().equals(this.actual))
                p -= cambiar ? 6.0 : -2.0;                                // sin cambiar, se queda con el de ahora
            p += azar.nextDouble() * 1.5;
            if (p > puntos) {
                puntos = p;
                mejor = e;
            }
        }
        if (mejor != null) {
            this.ultimaVez.put(mejor.getUUID(), ahora);
            this.actual = mejor.getUUID();
        } else {
            this.actual = null;
        }
        return mejor;
    }
}
