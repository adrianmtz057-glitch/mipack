package com.mipack;

import net.minecraftforge.common.ForgeConfigSpec;

/** Opciones del mod (config/mipack-client.toml). */
public final class MipackConfig {
    public static final ForgeConfigSpec CLIENTE;
    /** El cielo de Velkia (desierto de dia, estrellas y auroras de noche). En false se ve el cielo normal. */
    public static final ForgeConfigSpec.BooleanValue CIELO;
    /** El shader ligero de Velkia (brillo suave, rayos de sol, tono de la hora, neblina, calor, vineta). */
    public static final ForgeConfigSpec.BooleanValue EFECTOS;
    /** Las ondas de calor (la distorsion del aire en el desierto de dia). En false se quitan solo esas. */
    public static final ForgeConfigSpec.BooleanValue CALOR;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        CIELO = b.comment("El cielo de Velkia: desierto de dia, estrellas y auroras de noche (false = el cielo normal)")
                .define("cielo", true);
        EFECTOS = b.comment("El shader ligero de Velkia: brillo suave, rayos de sol, tono de la hora, neblina, calor y vineta")
                .define("efectos", true);
        CALOR = b.comment("Las ondas de calor del desierto (la distorsion del aire de dia). false = sin ondas, el resto del shader sigue")
                .define("calor", true);
        CLIENTE = b.build();
    }

    private MipackConfig() {
    }
}
