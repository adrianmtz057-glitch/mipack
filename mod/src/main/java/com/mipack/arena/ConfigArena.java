package com.mipack.arena;

import net.minecraftforge.common.ForgeConfigSpec;

/** Las opciones de las arenas de los jefes (config/mipack-arena.toml). */
public final class ConfigArena {
    public static final ForgeConfigSpec SPEC;
    public static final ForgeConfigSpec.IntValue RADIO;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_REINICIO;
    public static final ForgeConfigSpec.DoubleValue MINUTOS_FURIA;
    public static final ForgeConfigSpec.IntValue DISTANCIA_LEJOS;
    public static final ForgeConfigSpec.IntValue ALTURA_ARRIBA;
    public static final ForgeConfigSpec.DoubleValue VIDA_CRACKATOS;
    public static final ForgeConfigSpec.DoubleValue VIDA_KHASET;
    public static final ForgeConfigSpec.DoubleValue VIDA_BRUMA;
    public static final ForgeConfigSpec.IntValue JUGADORES_PLENOS;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        b.push("arena");
        RADIO = b.comment("Radio de la arena alrededor del bloque central: el jefe no sale de ahi y las reglas valen adentro")
                .defineInRange("radio", 48, 12, 160);
        MINUTOS_REINICIO = b.comment("Si no queda ningun jugador vivo adentro este tiempo, el jefe se cura y vuelve al centro")
                .defineInRange("minutos_reinicio", 3.0, 0.5, 60.0);
        MINUTOS_FURIA = b.comment("Despues de este tiempo peleando el jefe se enfurece: pega mas fuerte, pero tambien recibe mas dano")
                .defineInRange("minutos_furia", 15.0, 1.0, 120.0);
        DISTANCIA_LEJOS = b.comment("Quien le pega al jefe desde mas lejos que esto (o desde fuera de la arena) hace poco dano y la arena lo castiga")
                .defineInRange("distancia_lejos", 32, 8, 160);
        ALTURA_ARRIBA = b.comment("Lo mismo para quien le pega desde tantos bloques arriba del bloque central")
                .defineInRange("altura_arriba", 14, 4, 128);
        b.pop();
        b.push("vida");
        JUGADORES_PLENOS = b.comment("Con cuantos jugadores el jefe tiene toda su vida (con menos baja; con mas no sube)")
                .defineInRange("jugadores_plenos", 30, 1, 200);
        VIDA_CRACKATOS = b.comment("Vida de Crackatos con todos los jugadores (en normal es el 80 %, en easy el 60 %)")
                .defineInRange("crackatos", 28000.0, 100.0, 1_000_000.0);
        VIDA_KHASET = b.comment("Vida de Khaset con todos los jugadores").defineInRange("khaset", 36000.0, 100.0, 1_000_000.0);
        VIDA_BRUMA = b.comment("Vida de La Bruma con todos los jugadores").defineInRange("bruma", 22000.0, 100.0, 1_000_000.0);
        b.pop();
        SPEC = b.build();
    }

    private ConfigArena() {
    }
}
