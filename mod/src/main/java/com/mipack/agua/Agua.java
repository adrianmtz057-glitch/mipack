package com.mipack.agua;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.player.Player;

/**
 * El agua del jugador (0 a 20, como la comida): se guarda en sus datos (se pierde al morir: reaparece con la barra
 * llena). Aqui solo lo basico para que los objetos puedan dar o quitar agua; el sistema completo (cuanto baja, la
 * sofocacion, el desmayo) esta en SistemaAgua.
 */
public final class Agua {
    public static final float MAX = 20.0f;
    static final String CLAVE = "mipack_agua";

    private Agua() {
    }

    static CompoundTag datos(Player p) {
        return p.getPersistentData();
    }

    public static float agua(Player p) {
        CompoundTag d = datos(p);
        return d.contains(CLAVE) ? d.getFloat(CLAVE) : MAX;
    }

    public static void poner(Player p, float valor) {
        datos(p).putFloat(CLAVE, Math.max(0.0f, Math.min(MAX, valor)));
    }

    /** Da (o quita, si es negativo) agua. */
    public static void beber(Player p, float cuanto) {
        if (p.level().isClientSide)
            return;
        poner(p, agua(p) + cuanto);
        SistemaAgua.avisar(p);
    }
}
