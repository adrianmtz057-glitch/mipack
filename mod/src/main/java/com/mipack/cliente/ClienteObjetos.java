package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.objetos.EfectosArmadura;
import com.mipack.objetos.Escudo;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ComputeFovModifierEvent;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.MovementInputUpdateEvent;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.client.gui.overlay.VanillaGuiOverlay;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

/** Lo de los objetos que solo vive en el cliente. */
public final class ClienteObjetos {
    private ClienteObjetos() {
    }

    @Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Mod_ {
        private Mod_() {
        }

        @SubscribeEvent
        public static void preparar(FMLClientSetupEvent e) {
            e.enqueueWork(() -> {
                for (Item escudo : new Item[]{ObjetosMipack.ESCUDO_ESCAMAS.get(), ObjetosMipack.ESCUDO_CAPARAZON.get()})
                    ItemProperties.register(escudo, new ResourceLocation("blocking"),
                            (s, nivel, quien, sem) -> quien != null && quien.isUsingItem() && quien.getUseItem() == s ? 1.0f : 0.0f);
            });
        }

        @SubscribeEvent
        public static void renderers(EntityRenderersEvent.RegisterRenderers e) {
            e.registerEntityRenderer(ObjetosMipack.BOMBA.get(), ThrownItemRenderer::new);
            e.registerEntityRenderer(ObjetosMipack.SENUELO.get(), ThrownItemRenderer::new);
        }

        @SubscribeEvent
        public static void pantalla(RegisterGuiOverlaysEvent e) {
            e.registerAbove(VanillaGuiOverlay.FOOD_LEVEL.id(), "agua", new ClienteAgua.Barra());
            e.registerBelow(VanillaGuiOverlay.CHAT_PANEL.id(), "desmayo", new ClienteAgua.Desmayo());
        }
    }

    @Mod.EventBusSubscriber(modid = Mipack.MODID, value = Dist.CLIENT)
    public static final class Juego {
        private Juego() {
        }

        /** La ligereza de las armaduras no hace zoom: se quita su parte del cambio de campo de vision. */
        @SubscribeEvent
        public static void sinZoom(ComputeFovModifierEvent e) {
            AttributeInstance v = e.getPlayer().getAttribute(Attributes.MOVEMENT_SPEED);
            if (v == null || e.getPlayer().getAbilities().flying)
                return;
            AttributeModifier m = v.getModifier(EfectosArmadura.LIGEREZA);
            if (m == null)
                return;
            double con = v.getValue();
            double sin = con - v.getBaseValue() * m.getAmount();
            double camina = e.getPlayer().getAbilities().getWalkingSpeed();
            if (camina <= 0 || sin <= 0)
                return;
            float conF = (float) ((con / camina + 1.0) / 2.0), sinF = (float) ((sin / camina + 1.0) / 2.0);
            e.setNewFovModifier(e.getNewFovModifier() * sinF / conF);
        }

        /** El escudo de caparazon es ligero: al cubrirte casi no te alentas. */
        @SubscribeEvent
        public static void escudoLigero(MovementInputUpdateEvent e) {
            if (e.getEntity() instanceof LocalPlayer p && p.isUsingItem() && p.getUseItem().getItem() instanceof Escudo esc && esc.ligero()) {
                e.getInput().forwardImpulse *= 2.5f;
                e.getInput().leftImpulse *= 2.5f;
            }
        }
    }
}
