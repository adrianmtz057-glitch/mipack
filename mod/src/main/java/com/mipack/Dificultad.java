package com.mipack;

import com.mipack.entidad.CrackatosEntity;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.Xiuhcoatl;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.EnumMap;
import java.util.Locale;

/**
 * La dificultad de cada jefe: {@code /khaset difficult <easy|normal|hardcore>} y {@code /crackatos difficult ...}
 * (sin nivel dice cual tiene). Solo los operadores la cambian, la respuesta solo le llega a quien la escribio y en el
 * juego no se ve en ningun lado. Se guarda con el mundo; empieza en normal.
 * <ul>
 * <li>hardcore: la pelea original (la de "semana 2");</li>
 * <li>normal: menos vida y dano, mas tiempo para zafarse antes del sacrificio, barra mas facil y mas aviso antes de la
 *     estampida;</li>
 * <li>easy: todavia mas.</li>
 * </ul>
 * Lo propio de cada jefe esta en su clase (KhasetEntity.Ajustes, CrackatosEntity.Ajustes); aqui, la vida y el dano.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class Dificultad extends SavedData {
    public enum Nivel {
        EASY(0.6f, 0.65f), NORMAL(0.8f, 0.8f), HARDCORE(1f, 1f);

        /** Por cuanto se multiplica la vida del jefe y el dano de sus golpes. */
        public final float vida, dano;

        Nivel(float vida, float dano) {
            this.vida = vida;
            this.dano = dano;
        }

        public String nombre() {
            return name().toLowerCase(Locale.ROOT);
        }
    }

    public enum Jefe {KHASET, CRACKATOS}

    private static final String ARCHIVO = "mipack_dificultad";
    private final EnumMap<Jefe, Nivel> niveles = new EnumMap<>(Jefe.class);

    private Dificultad() {
        for (Jefe j : Jefe.values())
            this.niveles.put(j, Nivel.NORMAL);
    }

    private static Dificultad cargar(CompoundTag tag) {
        Dificultad d = new Dificultad();
        for (Jefe j : Jefe.values()) {
            String n = tag.getString(j.name());
            for (Nivel v : Nivel.values())
                if (v.name().equals(n))
                    d.niveles.put(j, v);
        }
        return d;
    }

    @Override
    public CompoundTag save(CompoundTag tag) {
        this.niveles.forEach((j, n) -> tag.putString(j.name(), n.name()));
        return tag;
    }

    private static Dificultad de(MinecraftServer s) {
        return s.overworld().getDataStorage().computeIfAbsent(Dificultad::cargar, Dificultad::new, ARCHIVO);
    }

    /** El nivel de ese jefe en este mundo (en el cliente, normal: alla no se usa). */
    public static Nivel de(Level nivel, Jefe j) {
        return nivel instanceof ServerLevel sl ? de(sl.getServer()).niveles.get(j) : Nivel.NORMAL;
    }

    /** Cambia el nivel de ese jefe (el comando y las pruebas). */
    public static void poner(MinecraftServer s, Jefe j, Nivel n) {
        Dificultad d = de(s);
        d.niveles.put(j, n);
        d.setDirty();
    }

    /** Por cuanto se multiplica un golpe de jefe (Khaset y sus serpientes, Crackatos con sus puas y su ola). */
    public static float dano(Entity quien) {
        if (quien == null)
            return 1f;
        if (quien instanceof KhasetEntity || quien instanceof Xiuhcoatl)
            return de(quien.level(), Jefe.KHASET).dano;
        if (quien instanceof CrackatosEntity)
            return de(quien.level(), Jefe.CRACKATOS).dano;
        return 1f;
    }

    @SubscribeEvent
    public static void comandos(RegisterCommandsEvent evento) {
        CommandDispatcher<CommandSourceStack> d = evento.getDispatcher();
        for (Jefe j : Jefe.values()) {
            LiteralArgumentBuilder<CommandSourceStack> dif = Commands.literal("difficult").executes(c -> {
                Nivel n = de(c.getSource().getServer()).niveles.get(j);
                c.getSource().sendSuccess(() -> Component.literal(nombre(j) + ": " + n.nombre()), false);
                return n.ordinal();
            });
            for (Nivel n : Nivel.values())
                dif.then(Commands.literal(n.nombre()).executes(c -> {
                    poner(c.getSource().getServer(), j, n);
                    c.getSource().sendSuccess(() -> Component.literal(nombre(j) + " en " + n.nombre()), false);   // solo a quien lo puso
                    return 1;
                }));
            d.register(Commands.literal(j.name().toLowerCase(Locale.ROOT)).requires(s -> s.hasPermission(2)).then(dif));
        }
    }

    private static String nombre(Jefe j) {
        return j == Jefe.KHASET ? "Khaset" : "Crackatos";
    }
}
