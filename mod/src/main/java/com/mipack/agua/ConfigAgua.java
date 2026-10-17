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
    public static final ForgeConfigSpec.ConfigValue<java.util.List<? extends String>> CALIENTES;
    public static final ForgeConfigSpec.ConfigValue<java.util.List<? extends String>> FRESCOS;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_FRESCO;

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
        CALIENTES = b.comment("Biomas que sofocan (desierto, volcan, canon, sales...): ahi la Sofocacion esta siempre y el agua dura",
                        "minutos_desierto (menos con armadura). Ids de bioma (\"minecraft:desert\") o etiquetas con # (\"#minecraft:is_badlands\")")
                .defineListAllowEmpty("biomas_calientes", java.util.List.of("minecraft:desert", "#minecraft:is_badlands", "#forge:is_desert"),
                        o -> o instanceof String);
        FRESCOS = b.comment("Biomas frescos (montanas, jardines...): sin sofocacion y el agua baja mas lento (minutos_fresco)")
                .defineListAllowEmpty("biomas_frescos", java.util.List.of("#minecraft:is_mountain", "minecraft:flower_forest",
                        "minecraft:meadow", "minecraft:cherry_grove"), o -> o instanceof String);
        MINUTOS_FRESCO = b.comment("Minutos que dura la barra llena en los biomas frescos").defineInRange("minutos_fresco", 90.0, 5.0, 600.0);
        b.pop();
        b.push("frio");
        FRIO = b.comment("El frio de las montanas nevadas (gasta comida si no traes abrigo de pelaje)").define("activo", true);
        b.pop();
        SPEC = b.build();
    }

    private ConfigAgua() {
    }
}
