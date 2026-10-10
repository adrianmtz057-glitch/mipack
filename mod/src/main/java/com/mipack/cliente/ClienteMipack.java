package com.mipack.cliente;

import com.mipack.Mipack;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Lo que solo existe en el cliente: como se dibuja cada entidad. */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClienteMipack {
    private ClienteMipack() {
    }

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers evento) {
        evento.registerEntityRenderer(Mipack.CRACKATOS.get(), CrackatosRenderer::new);
        evento.registerEntityRenderer(Mipack.PUA.get(), PuaRenderer::new);
    }
}
