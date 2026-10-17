package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.EfectosKhaset;
import com.mipack.khaset.KhasetEntity;
import com.mojang.blaze3d.systems.RenderSystem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraftforge.client.gui.overlay.ForgeGui;
import net.minecraftforge.client.gui.overlay.IGuiOverlay;

/**
 * Lo que se ve encima de la pantalla en la pelea con Khaset: el borde rojo que late con el desangrado (mas fuerte en
 * cada nivel), el calor (un borde naranja que crece con la barra de calor) y un destello al quedar aturdido.
 */
public final class PantallaKhaset implements IGuiOverlay {
    private static final ResourceLocation VINETA = new ResourceLocation(Mipack.MODID, "textures/misc/vineta.png");

    @Override
    public void render(ForgeGui gui, GuiGraphics g, float parcial, int ancho, int alto) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.options.hideGui)
            return;
        float t = p.tickCount + parcial;
        float calor = 0f;
        for (KhasetEntity k : p.level().getEntitiesOfClass(KhasetEntity.class, p.getBoundingBox().inflate(64)))
            calor = Math.max(calor, k.calor());
        if (calor > 0.05f)
            vineta(g, ancho, alto, 1f, 0.45f, 0.1f, Math.min(0.7f, calor * 0.6f) * (0.85f + 0.15f * Mth.sin(t * 0.15f)));
        MobEffectInstance d = p.getEffect(EfectosKhaset.DESANGRADO.get());
        if (d != null) {
            float latido = (float) Math.pow(Math.max(0f, Mth.sin(t * (0.25f + 0.08f * d.getAmplifier()))), 6);
            vineta(g, ancho, alto, 0.75f, 0.02f, 0.05f, (0.25f + 0.2f * d.getAmplifier()) + 0.35f * latido);
        }
        MobEffectInstance a = p.getEffect(EfectosKhaset.ATURDIDO.get());
        if (a != null)
            vineta(g, ancho, alto, 1f, 1f, 1f, Math.min(0.8f, a.getDuration() / 30f * 0.8f));
    }

    private static void vineta(GuiGraphics g, int ancho, int alto, float r, float v, float b, float alfa) {
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.setShaderColor(r, v, b, Mth.clamp(alfa, 0f, 1f));
        g.blit(VINETA, 0, 0, 0, 0f, 0f, ancho, alto, ancho, alto);
        RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
        RenderSystem.disableBlend();
    }
}
