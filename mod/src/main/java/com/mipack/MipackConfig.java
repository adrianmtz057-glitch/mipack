package com.mipack;

import net.minecraftforge.common.ForgeConfigSpec;

/** Opciones del mod (config/mipack-client.toml). */
public final class MipackConfig {
    public static final ForgeConfigSpec CLIENTE;
    /** El cielo de Velkia (desierto de dia, estrellas y auroras de noche). En false se ve el cielo normal. */
    public static final ForgeConfigSpec.BooleanValue CIELO;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        CIELO = b.comment("El cielo de Velkia: desierto de dia, estrellas y auroras de noche (false = el cielo normal)")
                .define("cielo", true);
        CLIENTE = b.build();
    }

    private MipackConfig() {
    }
}
