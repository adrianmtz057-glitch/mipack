package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.RedKhaset;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.client.gui.overlay.ForgeGui;
import net.minecraftforge.client.gui.overlay.IGuiOverlay;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * La barra para zafarse de la mano de Khaset: abajo de la pantalla, un cursor que va y viene y una zona dorada. Clic
 * (el boton de pegar) cuando el cursor esta en lo dorado: a los 3 aciertos te suelta. Cada fallo te quita la mitad de
 * la vida que tengas. El servidor decide (RedKhaset.Barra / Clic); aqui solo se dibuja y se manda el clic.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class BarraZafarse implements IGuiOverlay {
    private static RedKhaset.Barra barra = RedKhaset.Barra.NADA;
    private static long falloEn = -100, aciertoEn = -100;
    private static int aciertosAntes;

    public static void recibir(RedKhaset.Barra b) {
        Minecraft mc = Minecraft.getInstance();
        long t = mc.level == null ? 0 : mc.level.getGameTime();
        if (b.fallo())
            falloEn = t;
        if (b.aciertos() > aciertosAntes)
            aciertoEn = t;
        aciertosAntes = b.activa() ? b.aciertos() : 0;
        barra = b;
    }

    private static boolean agarrado(LocalPlayer p) {
        return p != null && barra.activa() && p.getVehicle() instanceof KhasetEntity;
    }

    @Override
    public void render(ForgeGui gui, GuiGraphics g, float parcial, int ancho, int alto) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (!agarrado(p) || mc.options.hideGui)
            return;
        double t = p.level().getGameTime() + parcial;
        int w = 200, h = 12, x0 = (ancho - w) / 2, y0 = alto - 72;
        boolean rojo = t - falloEn < 8, verde = t - aciertoEn < 6;
        g.fill(x0 - 3, y0 - 3, x0 + w + 3, y0 + h + 3, rojo ? 0xE0B01818 : verde ? 0xE018A040 : 0xE0181014);
        g.fill(x0, y0, x0 + w, y0 + h, 0xFF3A2A22);
        int z0 = x0 + Math.round((barra.zona() - barra.ancho() / 2) * w), z1 = x0 + Math.round((barra.zona() + barra.ancho() / 2) * w);
        g.fill(Math.max(x0, z0), y0, Math.min(x0 + w, z1), y0 + h, 0xFFE0A830);
        g.fill(Math.max(x0, z0), y0, Math.min(x0 + w, z1), y0 + 2, 0xFFFFE07A);
        int c = x0 + Math.round(barra.cursor(t) * w);
        g.fill(c - 1, y0 - 4, c + 2, y0 + h + 4, 0xFFFFFFFF);
        for (int i = 0; i < 3; i++) {                              // los tres aciertos
            int px = ancho / 2 - 22 + i * 16;
            g.fill(px, y0 + h + 7, px + 12, y0 + h + 15, 0xFF181014);
            if (i < barra.aciertos())
                g.fill(px + 1, y0 + h + 8, px + 11, y0 + h + 14, 0xFF3CE06A);
        }
        Component txt = Component.translatable("gui.mipack.zafarse");
        float pulso = 0.75f + 0.25f * Mth.sin((float) t * 0.4f);
        int col = ((int) (255 * pulso) << 24) | 0xFFE6C8;
        g.drawCenteredString(mc.font, txt, ancho / 2, y0 - 14, col);
    }

    /** Agarrado: el boton de pegar es el clic de la barra (no pega) y no se usan objetos. */
    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void clic(InputEvent.InteractionKeyMappingTriggered evento) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (!agarrado(p))
            return;
        if (evento.isAttack())
            RedKhaset.CANAL.sendToServer(new RedKhaset.Clic(barra.cursor(p.level().getGameTime() + mc.getFrameTime())));
        if (evento.isAttack() || evento.isUseItem()) {
            evento.setCanceled(true);
            evento.setSwingHand(false);
        }
    }
}
