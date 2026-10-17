package com.mipack.bruma;

import com.mipack.Mipack;
import com.mipack.arena.Arena;
import com.mipack.objetos.EfectosObjetos;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.List;

/**
 * La cordura (0 a 100), solo en la pelea con La Bruma, y la arena oscura:
 * <ul>
 * <li>en la pelea baja despacio (de llena a cero en unos 6 minutos) y todo esta a oscuras;</li>
 * <li>cerca del pedazo de piramide (en la mano de quien sea, a 10 bloques) hay luz fuerte: se quita la oscuridad y la
 *     cordura sube rapido;</li>
 * <li>cerca de un brasero encendido (fogata, a 6 bloques) hay luz debil: la oscuridad se va y la cordura no baja;</li>
 * <li>fuera de la pelea se recupera sola;</li>
 * <li>en cero: POSEIDO. El jugador se queda quieto, invisible y sin que le peguen (camara en tercera persona) y sale su
 *     doble oscuro con ojos de mura a pelear contra los demas. Pegarle al doble con la espada de vitae lo regresa ahi
 *     mismo con la cordura llena: no muere, no pierde nada y no gasta totem.</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class Cordura {
    public static final float MAX = 100f;
    private static final String CLAVE = "mipack_cordura", ENVIADA = "mipack_cordura_env";
    private static final float BAJA = 0.28f, PEDAZO = 4f, RECUPERA = 2f;   // por segundo
    private static final double RADIO_PELEA = 64, RADIO_PEDAZO = 10, RADIO_BRASERO = 6;

    private Cordura() {
    }

    public static float de(Player p) {
        return p.getPersistentData().contains(CLAVE) ? p.getPersistentData().getFloat(CLAVE) : MAX;
    }

    public static void poner(Player p, float v) {
        p.getPersistentData().putFloat(CLAVE, Math.max(0f, Math.min(MAX, v)));
    }

    public static boolean poseido(Player p) {
        return p.hasEffect(EfectosObjetos.POSEIDO.get());
    }

    /** La Bruma viva en cuya pelea esta (su arena, o a 64 bloques). */
    public static BrumaEntity pelea(Player p) {
        for (BrumaEntity b : p.level().getEntitiesOfClass(BrumaEntity.class, p.getBoundingBox().inflate(RADIO_PELEA * 1.5))) {
            if (!b.isAlive())
                continue;
            BlockPos c = Arena.centro(b);
            if (c != null ? Arena.dentro(c, p) : b.distanceTo(p) < RADIO_PELEA)
                return b;
        }
        return null;
    }

    public static boolean cercaDelPedazo(Player p) {
        if (p.getMainHandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get()) || p.getOffhandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get()))
            return true;
        for (Player o : p.level().getEntitiesOfClass(Player.class, p.getBoundingBox().inflate(RADIO_PEDAZO)))
            if (o.isAlive() && (o.getMainHandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get()) || o.getOffhandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get())))
                return true;
        return false;
    }

    public static boolean cercaDeBrasero(Player p) {
        BlockPos c = p.blockPosition();
        int r = (int) RADIO_BRASERO;
        for (BlockPos b : BlockPos.betweenClosed(c.offset(-r, -2, -r), c.offset(r, 3, r))) {
            BlockState s = p.level().getBlockState(b);
            if (s.getBlock() instanceof CampfireBlock && s.getValue(CampfireBlock.LIT))
                return true;
        }
        return false;
    }

    /** Un paso de un segundo de la cordura de este jugador (se llama tambien desde las pruebas). */
    public static void segundo(Player p) {
        if (p.isCreative() || p.isSpectator() || poseido(p))
            return;
        BrumaEntity b = pelea(p);
        float c = de(p);
        if (b == null) {
            poner(p, c + RECUPERA);
        } else {
            boolean pedazo = cercaDelPedazo(p), brasero = !pedazo && cercaDeBrasero(p);
            if (pedazo) {
                poner(p, c + PEDAZO);
                p.removeEffect(MobEffects.DARKNESS);
                p.removeEffect(MobEffects.BLINDNESS);
            } else if (brasero) {
                p.removeEffect(MobEffects.DARKNESS);
            } else {
                poner(p, c - BAJA);
                p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 70, 0, false, false, false));
            }
            if (de(p) <= 0f)
                poseer(p, b);
        }
        if (p instanceof ServerPlayer sp) {
            int ahora = Math.round(de(p) * 2) * 2 + (b != null ? 1 : 0);
            if (sp.getPersistentData().getInt(ENVIADA) != ahora + 1) {
                sp.getPersistentData().putInt(ENVIADA, ahora + 1);
                RedBruma.enviar(sp, new RedBruma.Estado(de(p), b != null));
            }
        }
    }

    /** Se lo lleva La Bruma: quieto e invisible; sale su doble. */
    public static Poseido poseer(Player p, BrumaEntity b) {
        if (!(p.level() instanceof ServerLevel sl) || poseido(p))
            return null;
        Poseido d = Mipack.POSEIDO.get().create(sl);
        if (d == null)
            return null;
        d.moveTo(p.getX(), p.getY(), p.getZ(), p.getYRot(), 0f);
        d.de(p);
        sl.addFreshEntity(d);
        p.addEffect(new MobEffectInstance(EfectosObjetos.POSEIDO.get(), 20 * 60 * 10, 0, false, false, true));
        p.setInvisible(true);
        sl.playSound(null, p.blockPosition(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 3.0f, 0.5f);
        sl.playSound(null, p.blockPosition(), SoundEvents.SOUL_ESCAPE, SoundSource.HOSTILE, 3.0f, 0.6f);
        sl.sendParticles(ParticleTypes.SCULK_SOUL, p.getX(), p.getY() + 1, p.getZ(), 30, 0.4, 0.8, 0.4, 0.05);
        Component msj = Component.translatable("bruma.mipack.poseido", p.getDisplayName()).withStyle(ChatFormatting.DARK_PURPLE);
        for (Player o : sl.players())
            if (o.distanceTo(p) < 96)
                o.displayClientMessage(msj, false);
        return d;
    }

    /** Lo regresa (en 'donde', con la cordura llena). */
    public static void liberar(Player p, net.minecraft.world.phys.Vec3 donde) {
        p.removeEffect(EfectosObjetos.POSEIDO.get());
        p.setInvisible(false);
        poner(p, MAX);
        if (donde != null)
            p.teleportTo(donde.x, donde.y, donde.z);
        p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 60, 0));
        p.level().playSound(null, p.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.8f, 1.3f);
        if (p.level() instanceof ServerLevel sl)
            sl.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, p.getX(), p.getY() + 1, p.getZ(), 40, 0.4, 0.8, 0.4, 0.3);
        if (p instanceof ServerPlayer sp)
            RedBruma.enviar(sp, new RedBruma.Estado(MAX, pelea(p) != null));
    }

    @SubscribeEvent
    public static void tick(TickEvent.PlayerTickEvent e) {
        Player p = e.player;
        if (e.phase != TickEvent.Phase.END || p.level().isClientSide)
            return;
        if (poseido(p)) {
            p.setInvisible(true);
            p.setDeltaMovement(0, Math.min(0, p.getDeltaMovement().y), 0);
            if (p.tickCount % 20 == 0 && p.level().getEntitiesOfClass(Poseido.class, p.getBoundingBox().inflate(128),
                    d -> p.getUUID().equals(d.dueno())).isEmpty())
                liberar(p, null);                              // su doble ya no esta: se le regresa
            return;
        }
        if (p.tickCount % 20 == 0)
            segundo(p);
        if (p.tickCount % 10 == 0 && p.level() instanceof ServerLevel sl
                && (p.getMainHandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get()) || p.getOffhandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get()))
                && pelea(p) != null)                           // la luz del pedazo
            for (int i = 0; i < 12; i++) {
                double a = i * Math.PI / 6 + p.tickCount * 0.05;
                sl.sendParticles(ParticleTypes.END_ROD, p.getX() + Math.cos(a) * 1.5, p.getY() + 1.2, p.getZ() + Math.sin(a) * 1.5, 1, 0, 0.05, 0, 0.01);
            }
    }

    // el poseido no recibe golpes ni puede hacer nada
    @SubscribeEvent
    public static void intocable(LivingAttackEvent e) {
        if (e.getEntity() instanceof Player p && poseido(p))
            e.setCanceled(true);
    }

    @SubscribeEvent
    public static void sinPegar(AttackEntityEvent e) {
        if (poseido(e.getEntity()))
            e.setCanceled(true);
    }

    @SubscribeEvent
    public static void sinUsar(PlayerInteractEvent e) {
        if (e.isCancelable() && poseido(e.getEntity()))
            e.setCanceled(true);
    }

    @SubscribeEvent
    public static void sale(PlayerEvent.PlayerLoggedOutEvent e) {
        Player p = e.getEntity();
        if (poseido(p)) {
            for (Poseido d : p.level().getEntitiesOfClass(Poseido.class, p.getBoundingBox().inflate(128), d -> p.getUUID().equals(d.dueno())))
                d.discard();
            liberar(p, null);
        }
    }

    @SubscribeEvent
    public static void entra(PlayerEvent.PlayerLoggedInEvent e) {
        if (poseido(e.getEntity()))
            liberar(e.getEntity(), null);
    }
}
