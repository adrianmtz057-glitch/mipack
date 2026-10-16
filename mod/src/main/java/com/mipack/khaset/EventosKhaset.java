package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.event.entity.EntityMountEvent;
import net.minecraftforge.event.entity.living.MobEffectEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Lo que pasa fuera de las entidades de la pelea con Khaset:
 * <ul>
 * <li>las presas no se pueden bajar de su mano con shift (solo cuando el las suelta);</li>
 * <li>derribado o aturdido no se puede pegar;</li>
 * <li>con el calor a un cuarto el agua se evapora cerca de el (como en el Nether);</li>
 * <li>cuando cambian las heridas de alguien, todos los que lo ven se enteran (para las poses y las gotas).</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class EventosKhaset {
    private EventosKhaset() {
    }

    /** Solo el servidor decide cuando se suelta: si el cliente tambien lo cancelaba, al soltarte en el servidor tu
     * pantalla te dejaba pegado a su mano. Muerto o ya quitado, siempre se baja. */
    @SubscribeEvent
    public static void bajarse(EntityMountEvent evento) {
        if (evento.isDismounting() && !evento.getLevel().isClientSide()
                && evento.getEntityBeingMounted() instanceof KhasetEntity k && !k.soltando()
                && evento.getEntityMounting().isAlive() && !evento.getEntityMounting().isRemoved()
                && !(evento.getEntityMounting() instanceof ServerPlayer sp && sp.hasDisconnected()))
            evento.setCanceled(true);
    }

    @SubscribeEvent
    public static void pegar(AttackEntityEvent evento) {
        if (EfectosKhaset.sinControl(evento.getEntity()))
            evento.setCanceled(true);
    }

    @SubscribeEvent
    public static void agua(PlayerInteractEvent.RightClickBlock evento) {
        evaporar(evento.getEntity(), evento.getHand(), evento.getPos(), evento);
    }

    @SubscribeEvent
    public static void aguaAlAire(PlayerInteractEvent.RightClickItem evento) {
        evaporar(evento.getEntity(), evento.getHand(), evento.getEntity().blockPosition(), evento);
    }

    private static void evaporar(Player p, InteractionHand mano, BlockPos donde, PlayerInteractEvent evento) {
        ItemStack s = p.getItemInHand(mano);
        if (!s.is(Items.WATER_BUCKET) || !(p.level() instanceof ServerLevel sl))
            return;
        boolean caliente = !sl.getEntitiesOfClass(KhasetEntity.class, p.getBoundingBox().inflate(48),
                k -> k.calor() >= 0.25f && k.isAlive()).isEmpty();
        if (!caliente)
            return;
        evento.setCanceled(true);
        if (!p.getAbilities().instabuild)
            p.setItemInHand(mano, new ItemStack(Items.BUCKET));
        sl.playSound(null, donde, SoundEvents.FIRE_EXTINGUISH, SoundSource.PLAYERS, 0.8f, 2.0f);
        sl.sendParticles(ParticleTypes.LARGE_SMOKE, donde.getX() + 0.5, donde.getY() + 1.0, donde.getZ() + 0.5, 12, 0.4, 0.3, 0.4, 0.02);
    }

    private static boolean nuestro(MobEffect e) {
        return e == EfectosKhaset.DESANGRADO.get() || e == EfectosKhaset.DERRIBADO.get()
                || e == EfectosKhaset.ATURDIDO.get() || e == EfectosKhaset.DESORIENTADO.get();
    }

    @SubscribeEvent
    public static void efectoNuevo(MobEffectEvent.Added evento) {
        if (evento.getEffectInstance() != null && nuestro(evento.getEffectInstance().getEffect()))
            avisarLuego(evento.getEntity());
    }

    @SubscribeEvent
    public static void efectoQuitado(MobEffectEvent.Remove evento) {
        if (evento.getEffect() != null && nuestro(evento.getEffect()))
            avisarLuego(evento.getEntity());
    }

    @SubscribeEvent
    public static void efectoAcabado(MobEffectEvent.Expired evento) {
        if (evento.getEffectInstance() != null && nuestro(evento.getEffectInstance().getEffect()))
            avisarLuego(evento.getEntity());
    }

    /** El evento llega antes de que el efecto quede puesto o quitado: avisamos en el siguiente tick. */
    private static void avisarLuego(LivingEntity e) {
        if (e.level() instanceof ServerLevel sl && e instanceof Player)
            sl.getServer().tell(new net.minecraft.server.TickTask(sl.getServer().getTickCount() + 1, () -> RedKhaset.avisar(e)));
    }

    @SubscribeEvent
    public static void empiezaAVer(PlayerEvent.StartTracking evento) {
        if (evento.getTarget() instanceof Player otro && evento.getEntity() instanceof ServerPlayer yo)
            RedKhaset.CANAL.send(net.minecraftforge.network.PacketDistributor.PLAYER.with(() -> yo), RedKhaset.Estado.de(otro));
    }
}
