package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.agua.RedAgua;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.MovementInputUpdateEvent;
import net.minecraftforge.client.gui.overlay.ForgeGui;
import net.minecraftforge.client.gui.overlay.IGuiOverlay;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Lo del agua en el cliente: la barra de gotas (arriba de la comida), el desmayo (los ojos se cierran, todo negro; el
 * chat se sigue viendo y se puede usar) y el trago del rio (agachado, clic derecho con la mano vacia mirando agua).
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, value = Dist.CLIENT)
public final class ClienteAgua {
    private static final ResourceLocation GOTAS = new ResourceLocation(Mipack.MODID, "textures/gui/agua.png");
    static float agua = 20.0f;
    static int desmayo, total = 1;
    static boolean activa;

    private ClienteAgua() {
    }

    public static void recibir(RedAgua.Estado e) {
        agua = e.agua();
        desmayo = e.desmayo();
        total = Math.max(1, e.total());
        activa = e.activa();
    }

    public static boolean desmayado() {
        return desmayo > 0;
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent e) {
        if (e.phase == TickEvent.Phase.END && desmayo > 0 && !Minecraft.getInstance().isPaused())
            desmayo--;
    }

    /** Desmayado no se mueve, no brinca ni se agacha. */
    @SubscribeEvent
    public static void quieto(MovementInputUpdateEvent e) {
        if (desmayo > 0) {
            e.getInput().forwardImpulse = 0;
            e.getInput().leftImpulse = 0;
            e.getInput().jumping = false;
            e.getInput().shiftKeyDown = false;
        }
    }

    @SubscribeEvent
    public static void tragoDelRio(PlayerInteractEvent.RightClickEmpty e) {
        if (e.getHand() == net.minecraft.world.InteractionHand.MAIN_HAND && e.getEntity().isShiftKeyDown()
                && e.getEntity().getMainHandItem().isEmpty() && activa)
            RedAgua.CANAL.sendToServer(new RedAgua.Beber());
    }

    /** La barra de agua: 10 gotas, arriba de la comida. */
    public static final class Barra implements IGuiOverlay {
        @Override
        public void render(ForgeGui gui, GuiGraphics g, float parcial, int ancho, int alto) {
            Minecraft mc = Minecraft.getInstance();
            if (!activa || mc.options.hideGui || !gui.shouldDrawSurvivalElements() || mc.player == null)
                return;
            gui.setupOverlayRenderState(true, false);
            int x0 = ancho / 2 + 91;
            int y = alto - gui.rightHeight;
            gui.rightHeight += 10;
            boolean poca = agua < 6.0f;
            for (int i = 0; i < 10; i++) {
                int x = x0 - i * 8 - 9;
                int dy = poca && (mc.player.tickCount + i * 3) % 24 < 2 ? -1 : 0;
                g.blit(GOTAS, x, y + dy, 0, 0, 9, 9, 32, 16);
                float v = agua - i * 2;
                if (v >= 2.0f)
                    g.blit(GOTAS, x, y + dy, 9, 0, 9, 9, 32, 16);
                else if (v >= 1.0f)
                    g.blit(GOTAS, x, y + dy, 18, 0, 9, 9, 32, 16);
            }
        }
    }

    /**
     * El desmayo: los parpados bajan y suben (de arriba y de abajo) y en medio todo negro con el aviso. Va debajo del
     * chat, asi el chat se sigue viendo.
     */
    public static final class Desmayo implements IGuiOverlay {
        @Override
        public void render(ForgeGui gui, GuiGraphics g, float parcial, int ancho, int alto) {
            if (desmayo <= 0)
                return;
            float pasado = total - desmayo + parcial;
            float cierra = Mth.clamp(pasado / 25.0f, 0.0f, 1.0f);
            float abre = Mth.clamp((desmayo - parcial) / 20.0f, 0.0f, 1.0f);
            float f = Math.min(cierra, abre);
            f = f * f * (3 - 2 * f);
            int parpado = (int) Math.ceil(alto / 2.0 * f);
            g.fill(0, 0, ancho, parpado, 0xFF000000);
            g.fill(0, alto - parpado, ancho, alto, 0xFF000000);
            if (f > 0.98f) {
                Component t = Component.translatable("agua.mipack.desmayado");
                g.drawCenteredString(Minecraft.getInstance().font, t, ancho / 2, alto / 2 - 4, 0x8A8A8A);
            }
        }
    }
}
