package com.mipack.bruma;

import com.mipack.Mipack;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.entity.EntityMountEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** La presa de La Bruma no se puede bajar de su mano con shift: solo cuando ella la suelta (o se muere o se desconecta). */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class EventosBruma {
    private EventosBruma() {
    }

    @SubscribeEvent
    public static void bajarse(EntityMountEvent evento) {
        if (evento.isDismounting() && !evento.getLevel().isClientSide()
                && evento.getEntityBeingMounted() instanceof BrumaEntity b && !b.soltando() && b.isAlive()
                && evento.getEntityMounting().isAlive() && !evento.getEntityMounting().isRemoved()
                && !(evento.getEntityMounting() instanceof ServerPlayer sp && sp.hasDisconnected()))
            evento.setCanceled(true);
    }
}
