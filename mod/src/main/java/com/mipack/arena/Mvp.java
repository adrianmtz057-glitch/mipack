package com.mipack.arena;

import com.mipack.Mipack;
import com.mipack.bruma.ClonBruma;
import com.mipack.bruma.Poseido;
import com.mipack.bruma.SoldadoBruma;
import com.mipack.entidad.AcaroAmatista;
import com.mipack.khaset.GuerreroCalavera;
import com.mipack.khaset.Xiuhcoatl;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * La tabla de MVP y el botin personal de cada pelea de jefe. Mientras pelean se cuenta, por jugador: el dano que le
 * hizo al jefe, el dano que aguanto (del jefe y de los suyos), los rescates (que Khaset soltara a alguien), los bichos
 * que mato (soldados, clones, acaros, guerreros, serpientes, almas), el tiempo parado en el centro y los poseidos que
 * curo. Al morir el jefe sale la tabla en el chat para todos los de la pelea; el que gana cada categoria se lleva 3
 * diamantes y el que mas dano hizo, un totem de Anj. El botin del jefe es personal: a cada quien que peleo le toca su
 * propia copia, directo a su inventario.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class Mvp {
    public enum Cat { DANO, AGUANTE, RESCATES, BICHOS, CENTRO, CURADOS }

    private static final Map<UUID, Pelea> PELEAS = new HashMap<>();
    private static final double RADIO = 96;

    private Mvp() {
    }

    private static final class Pelea {
        final Map<UUID, float[]> cuentas = new LinkedHashMap<>();
        final Map<UUID, Component> nombres = new HashMap<>();

        void sumar(Player p, Cat c, float v) {
            this.cuentas.computeIfAbsent(p.getUUID(), u -> new float[Cat.values().length])[c.ordinal()] += v;
            this.nombres.put(p.getUUID(), p.getDisplayName());
        }
    }

    public static void sumar(Mob jefe, Player p, Cat c, float v) {
        if (jefe == null || p == null || p.isCreative() || v <= 0)
            return;
        PELEAS.computeIfAbsent(jefe.getUUID(), u -> new Pelea()).sumar(p, c, v);
    }

    /** El jefe mas cercano a 'e' (los suyos y los poseidos cuentan para su pelea). */
    public static Mob jefeCerca(Entity e) {
        Mob mejor = null;
        double d = RADIO * RADIO;
        for (Mob m : e.level().getEntitiesOfClass(Mob.class, e.getBoundingBox().inflate(RADIO), Arena::esJefe)) {
            double dd = m.distanceToSqr(e);
            if (m.isAlive() && dd < d) {
                d = dd;
                mejor = m;
            }
        }
        return mejor;
    }

    private static boolean delJefe(Entity e) {
        return e instanceof SoldadoBruma || e instanceof ClonBruma || e instanceof AcaroAmatista || e instanceof GuerreroCalavera
                || e instanceof Xiuhcoatl || e instanceof Poseido || e instanceof Vex;
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void dano(LivingDamageEvent e) {
        LivingEntity v = e.getEntity();
        if (v.level().isClientSide)
            return;
        Entity quien = e.getSource().getEntity();
        if (v instanceof Mob jefe && Arena.esJefe(jefe) && quien instanceof Player p)
            sumar(jefe, p, Cat.DANO, Math.min(e.getAmount(), v.getHealth()));
        else if (v instanceof Player p && quien != null && (Arena.esJefe(quien) || delJefe(quien)))
            sumar(Arena.esJefe(quien) ? (Mob) quien : jefeCerca(quien), p, Cat.AGUANTE, e.getAmount());
    }

    @SubscribeEvent
    public static void muerte(LivingDeathEvent e) {
        LivingEntity v = e.getEntity();
        if (v.level().isClientSide)
            return;
        if (delJefe(v) && !(v instanceof Poseido) && e.getSource().getEntity() instanceof Player p)
            sumar(jefeCerca(v), p, Cat.BICHOS, 1);
        if (v instanceof Mob jefe && Arena.esJefe(jefe) && PELEAS.containsKey(jefe.getUUID()))
            tabla(jefe, PELEAS.get(jefe.getUUID()));
    }

    /** El botin personal: cada quien que peleo recibe su copia; el jefe no suelta nada al piso. */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void botin(LivingDropsEvent e) {
        if (!(e.getEntity() instanceof Mob jefe) || !Arena.esJefe(jefe) || !(jefe.level() instanceof ServerLevel sl))
            return;
        Pelea pelea = PELEAS.remove(jefe.getUUID());
        List<Player> quienes = new ArrayList<>();
        for (Player p : sl.players())
            if (!p.isSpectator() && (pelea != null && pelea.cuentas.containsKey(p.getUUID()) || p.distanceTo(jefe) < 64))
                quienes.add(p);
        if (quienes.isEmpty())
            return;                                            // nadie: que caiga normal
        List<ItemStack> botin = new ArrayList<>();
        for (ItemEntity i : e.getDrops())
            botin.add(i.getItem());
        e.setCanceled(true);
        for (Player p : quienes)
            for (ItemStack s : botin)
                dar(p, s.copy());
    }

    private static void dar(Player p, ItemStack s) {
        if (!p.getInventory().add(s))
            p.drop(s, false);
    }

    private static void tabla(Mob jefe, Pelea pelea) {
        if (!(jefe.level() instanceof ServerLevel sl) || pelea.cuentas.isEmpty())
            return;
        List<Component> lineas = new ArrayList<>();
        lineas.add(Component.translatable("mvp.mipack.titulo", jefe.getDisplayName()).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
        Map<UUID, Integer> premios = new HashMap<>();
        UUID masDano = null;
        for (Cat c : Cat.values()) {
            UUID mejor = null;
            float max = 0;
            for (Map.Entry<UUID, float[]> en : pelea.cuentas.entrySet())
                if (en.getValue()[c.ordinal()] > max) {
                    max = en.getValue()[c.ordinal()];
                    mejor = en.getKey();
                }
            if (mejor == null)
                continue;
            if (c == Cat.DANO)
                masDano = mejor;
            premios.merge(mejor, 3, Integer::sum);
            String valor = c == Cat.CENTRO ? Math.round(max / 20f) + " s" : String.valueOf(Math.round(max));
            MutableComponent l = Component.translatable("mvp.mipack." + c.name().toLowerCase(), pelea.nombres.get(mejor), valor);
            lineas.add(l.withStyle(ChatFormatting.YELLOW));
        }
        for (Map.Entry<UUID, Integer> en : premios.entrySet()) {
            Player p = sl.getPlayerByUUID(en.getKey());
            if (p != null)
                dar(p, new ItemStack(Items.DIAMOND, en.getValue()));
        }
        Player top = masDano == null ? null : sl.getPlayerByUUID(masDano);
        if (top != null)
            dar(top, new ItemStack(ObjetosMipack.TOTEM_ANJ.get()));
        lineas.add(Component.translatable("mvp.mipack.premios").withStyle(ChatFormatting.AQUA));
        for (Player p : sl.players())
            if (pelea.cuentas.containsKey(p.getUUID()) || p.distanceTo(jefe) < RADIO) {
                for (Component l : lineas)
                    p.sendSystemMessage(l);
                sl.playSound(null, p.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 0.8f, 1.0f);
            }
    }
}
