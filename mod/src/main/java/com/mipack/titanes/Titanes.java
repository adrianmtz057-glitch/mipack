package com.mipack.titanes;

import com.mipack.Mipack;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Predicate;

/**
 * Los titanes del mundo de Velkia (uno por bioma), de mas facil a mas dificil. Cada uno es un TipoTitan sobre el mismo
 * motor (Titan, Rutas, Terreno, TitanesMundo); aqui va como es cada uno y su agenda.
 */
public final class Titanes {
    private static final Map<String, TipoTitan> TIPOS = new LinkedHashMap<>();
    private static final Map<String, RegistryObject<EntityType<Titan>>> ENTIDADES = new LinkedHashMap<>();

    private Titanes() {
    }

    // ------------------------------------------------------------------ los titanes

    /**
     * Candil, el ajolote del lodo (pantano): siempre quieto en el agua, hundido en el lodo con solo los ojos afuera y
     * nenufares y hongos que brillan en la espalda. A ratos se mueve a otro charco del pantano y atrapa algo.
     */
    public static final TipoTitan CANDIL = tipo(new TipoTitan("candil", 4.0f, 8.0f, 4.0f,
            new Rutas.Perfil(Rutas.Modo.TIERRA, 1, 4, 30, 0, Map.of(Terreno.Bioma.PANTANO, 0.5, Terreno.Bioma.RIO, 0.8,
                    Terreno.Bioma.OCEANO, 0.0, Terreno.Bioma.DESIERTO, 0.0, Terreno.Bioma.MONTANA, 0.0, Terreno.Bioma.NIEVE, 0.0)),
            0.06, 2.0f, -1.0, 1.6, Titanes::agendaCandil));

    private static TipoTitan.Actividad agendaCandil(Terreno t, TipoTitan tipo, Vec3 donde, Vec3 casa, long hora, RandomSource azar) {
        boolean noche = hora > 13000 && hora < 23000;
        int r = azar.nextInt(100);
        if (noche || r < 45)
            return new TipoTitan.Actividad(null, TipoTitan.Hacer.QUIETO, 1200 + azar.nextInt(1800));
        if (r < 60)
            return new TipoTitan.Actividad(null, TipoTitan.Hacer.DESCANSAR, 1200 + azar.nextInt(1200));
        if (r < 70)
            return new TipoTitan.Actividad(null, TipoTitan.Hacer.COMER, 100);
        Vec3 otro = lugarAlAzar(t, tipo, casa, 14, azar, l -> l.c().agua() || l.c().bioma() == Terreno.Bioma.PANTANO);
        return otro == null ? new TipoTitan.Actividad(null, TipoTitan.Hacer.QUIETO, 600)
                : new TipoTitan.Actividad(otro, azar.nextBoolean() ? TipoTitan.Hacer.COMER : TipoTitan.Hacer.QUIETO, 160);
    }

    /**
     * Sombra Alta, la manta del cielo (llanura y sabana): vuela alto en vueltas largas y lentas; a ratos planea o come en
     * vuelo; de noche baja a posarse en un claro de la llanura.
     */
    public static final TipoTitan SOMBRA_ALTA = tipo(new TipoTitan("sombra_alta", 8.0f, 30.0f, 5.0f,
            new Rutas.Perfil(Rutas.Modo.AIRE, 0, 999, 999, 0, Map.of(Terreno.Bioma.LLANURA, 0.7)),
            0.32, 1.2f, 38.0, 0.0, Titanes::agendaSombra));

    private static TipoTitan.Actividad agendaSombra(Terreno t, TipoTitan tipo, Vec3 donde, Vec3 casa, long hora, RandomSource azar) {
        boolean noche = hora > 13000 && hora < 23000;
        if (noche) {
            Vec3 claro = lugarAlAzar(t, tipo, donde, 30, azar, l -> l.claro(1));
            return new TipoTitan.Actividad(claro, TipoTitan.Hacer.DESCANSAR, 3000 + azar.nextInt(3000));
        }
        int r = azar.nextInt(100);
        if (r < 60) {
            Vec3 lejos = lugarAlAzar(t, tipo, casa, 50, azar, l -> true);
            return new TipoTitan.Actividad(lejos, TipoTitan.Hacer.QUIETO, 300 + azar.nextInt(500));
        }
        if (r < 85)
            return new TipoTitan.Actividad(null, TipoTitan.Hacer.COMER, 600);
        return new TipoTitan.Actividad(null, TipoTitan.Hacer.QUIETO, 600);
    }

    // ------------------------------------------------------------------ ayudas para las agendas

    /** Un lugar que cumpla 'que' cerca de un punto al azar alrededor de 'centro' (hasta 'radio' celdas). */
    static Vec3 lugarAlAzar(Terreno t, TipoTitan tipo, Vec3 centro, int radio, RandomSource azar, Predicate<Rutas.Lugar> que) {
        for (int intento = 0; intento < 4; intento++) {
            double a = azar.nextDouble() * Math.PI * 2, d = (0.4 + 0.6 * azar.nextDouble()) * radio * Terreno.CELDA;
            Vec3 p = centro.add(Math.cos(a) * d, 0, Math.sin(a) * d);
            Vec3 l = Rutas.lugar(t, tipo.perfil(), p, 4, que);
            if (l != null)
                return l;
        }
        return null;
    }

    // ------------------------------------------------------------------ registro

    private static TipoTitan tipo(TipoTitan t) {
        TIPOS.put(t.id(), t);
        return t;
    }

    public static TipoTitan tipo(String id) {
        return TIPOS.get(id);
    }

    public static Map<String, TipoTitan> tipos() {
        return TIPOS;
    }

    public static EntityType<Titan> entidad(String id) {
        return ENTIDADES.get(id).get();
    }

    public static Map<String, RegistryObject<EntityType<Titan>>> entidades() {
        return ENTIDADES;
    }

    /** Una entidad por titan (cada una con su modelo); se llama al construir el mod. */
    public static void registrar(DeferredRegister<EntityType<?>> reg) {
        for (TipoTitan t : TIPOS.values())
            ENTIDADES.put(t.id(), reg.register("titan_" + t.id(), () -> EntityType.Builder.<Titan>of(
                            (tipoEntidad, nivel) -> new Titan(tipoEntidad, nivel, t), MobCategory.MISC)
                    .sized(t.ancho(), t.alto()).fireImmune().clientTrackingRange(24).updateInterval(2)
                    .build(Mipack.MODID + ":titan_" + t.id())));
    }

    public static void atributos(EntityAttributeCreationEvent evento) {
        for (RegistryObject<EntityType<Titan>> e : ENTIDADES.values())
            evento.put(e.get(), Titan.atributos().build());
    }
}
