package com.mipack.agua;

import net.minecraftforge.common.ForgeConfigSpec;

/** Las opciones del agua y el frio (config/mipack-common.toml). */
public final class ConfigAgua {
    public static final ForgeConfigSpec SPEC;
    public static final ForgeConfigSpec.BooleanValue ACTIVA;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_FUERA;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_DESIERTO;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_MINIMO;
    public static final ForgeConfigSpec.IntValue SEGUNDOS_DESMAYO;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_GRACIA;
    public static final ForgeConfigSpec.BooleanValue FRIO;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        b.push("agua");
        ACTIVA = b.comment("La barra de agua (false = no hay sed)").define("activa", true);
        MINUTOS_FUERA = b.comment("Minutos que dura la barra llena fuera del desierto").defineInRange("minutos_fuera", 60.0, 5.0, 600.0);
        MINUTOS_DESIERTO = b.comment("Minutos que dura en el desierto sin armadura (la armadura los divide: diamante entre 2, netherita entre 3)")
                .defineInRange("minutos_desierto", 35.0, 5.0, 600.0);
        MINUTOS_MINIMO = b.comment("Lo menos que puede durar en el desierto, con la armadura que sea").defineInRange("minutos_minimo", 15.0, 1.0, 600.0);
        SEGUNDOS_DESMAYO = b.comment("Cuanto dura el desmayo al quedarse sin agua").defineInRange("segundos_desmayo", 10, 3, 120);
        MINUTOS_GRACIA = b.comment("Minutos sin sed para los jugadores nuevos").defineInRange("minutos_gracia", 10.0, 0.0, 600.0);
        b.pop();
        b.push("frio");
        FRIO = b.comment("El frio de las montanas nevadas (gasta comida si no traes abrigo de pelaje)").define("activo", true);
        b.pop();
        SPEC = b.build();
    }

    private ConfigAgua() {
    }
}
