package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.MipackConfig;
import com.mojang.blaze3d.pipeline.RenderTarget;
import com.mojang.blaze3d.pipeline.TextureTarget;
import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexFormat;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.ShaderInstance;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.material.FogType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterShadersEvent;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;
import org.lwjgl.opengl.GL11;
import org.lwjgl.opengl.GL30;

import java.io.IOException;

/**
 * El "shader" ligero de Velkia: un efecto de pantalla que corre despues de dibujar el mundo, sin mods extra.
 * <ol>
 * <li>Copia la imagen (color y profundidad).</li>
 * <li>Saca lo que brilla a un cuarto de tamano y lo desenfoca dos veces (brillo suave: sol, auroras, ojos).</li>
 * <li>La mezcla final (shaders/core/velkia_final.fsh): ondas de calor en el desierto, perspectiva de aire, el
 *     brillo, rayos de sol (lo que se ve de cielo en el camino hacia el sol, por la profundidad), el tono de la hora
 *     (dorado al amanecer y atardecer, calido al mediodia, azul de noche con un toque verde de aurora) y vineta.</li>
 * </ol>
 * Solo en el mundo normal, y no bajo el agua ni con ceguera. Se apaga con efectos = false en mipack-client.toml.
 */
public final class EfectosVelkia {
    /** Para las fotos de antes y despues (CapturaCielo). */
    public static boolean activos = true;

    private static ShaderInstance brillo, desenfoque, fin;
    private static TextureTarget copia, luz1, luz2;

    private EfectosVelkia() {
    }

    @Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Registro {
        private Registro() {
        }

        @SubscribeEvent
        public static void shaders(RegisterShadersEvent evento) throws IOException {
            evento.registerShader(new ShaderInstance(evento.getResourceProvider(), new ResourceLocation(Mipack.MODID, "velkia_brillo"),
                    DefaultVertexFormat.POSITION_TEX), s -> brillo = s);
            evento.registerShader(new ShaderInstance(evento.getResourceProvider(), new ResourceLocation(Mipack.MODID, "velkia_desenfoque"),
                    DefaultVertexFormat.POSITION_TEX), s -> desenfoque = s);
            evento.registerShader(new ShaderInstance(evento.getResourceProvider(), new ResourceLocation(Mipack.MODID, "velkia_final"),
                    DefaultVertexFormat.POSITION_TEX), s -> fin = s);
        }
    }

    @Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
    public static final class Cuadro {
        private Cuadro() {
        }

        @SubscribeEvent
        public static void alTerminarElMundo(RenderLevelStageEvent evento) {
            if (evento.getStage() != RenderLevelStageEvent.Stage.AFTER_LEVEL)
                return;
            Minecraft mc = Minecraft.getInstance();
            ClientLevel nivel = mc.level;
            if (!activos || !MipackConfig.EFECTOS.get() || nivel == null || brillo == null || desenfoque == null || fin == null
                    || !(nivel.effects() instanceof CieloVelkia) || !usar(evento.getCamera()))
                return;
            aplicar(mc, nivel, evento);
        }
    }

    private static boolean usar(Camera camara) {
        if (camara.getFluidInCamera() != FogType.NONE)
            return false;
        return !(camara.getEntity() instanceof LivingEntity e && (e.hasEffect(MobEffects.BLINDNESS) || e.hasEffect(MobEffects.DARKNESS)));
    }

    private static TextureTarget objetivo(TextureTarget t, int w, int h, boolean profundidad) {
        if (t == null) {
            t = new TextureTarget(w, h, profundidad, Minecraft.ON_OSX);
            t.setFilterMode(GL11.GL_LINEAR);
        } else if (t.width != w || t.height != h) {
            t.resize(w, h, Minecraft.ON_OSX);
            t.setFilterMode(GL11.GL_LINEAR);
        }
        return t;
    }

    private static void aplicar(Minecraft mc, ClientLevel nivel, RenderLevelStageEvent evento) {
        RenderTarget principal = mc.getMainRenderTarget();
        int w = principal.width, h = principal.height, w4 = Math.max(1, w / 4), h4 = Math.max(1, h / 4);
        copia = objetivo(copia, w, h, true);
        luz1 = objetivo(luz1, w4, h4, false);
        luz2 = objetivo(luz2, w4, h4, false);
        float parcial = evento.getPartialTick();
        CieloVelkia.Momento m = CieloVelkia.Momento.de(nivel, parcial);
        Parametros p = Parametros.de(mc, nivel, m, evento);

        RenderSystem.disableBlend();
        RenderSystem.disableDepthTest();
        RenderSystem.depthMask(false);

        // 1. la copia de la imagen y de la profundidad
        GlStateManager._glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER, principal.frameBufferId);
        GlStateManager._glBindFramebuffer(GL30.GL_DRAW_FRAMEBUFFER, copia.frameBufferId);
        GlStateManager._glBlitFrameBuffer(0, 0, w, h, 0, 0, w, h, GL11.GL_COLOR_BUFFER_BIT | GL11.GL_DEPTH_BUFFER_BIT, GL11.GL_NEAREST);
        GlStateManager._glBindFramebuffer(GL30.GL_FRAMEBUFFER, 0);

        // 2. lo que brilla, a un cuarto, y desenfocado de lado y de arriba a abajo
        luz1.bindWrite(true);
        brillo.setSampler("Sampler0", copia.getColorTextureId());
        brillo.safeGetUniform("Texel").set(1f / w, 1f / h);
        brillo.safeGetUniform("Umbral").set(p.umbral);
        cuadro(brillo);
        luz2.bindWrite(true);
        desenfoque.setSampler("Sampler0", luz1.getColorTextureId());
        desenfoque.safeGetUniform("Direccion").set(1f / w4, 0f);
        cuadro(desenfoque);
        luz1.bindWrite(true);
        desenfoque.setSampler("Sampler0", luz2.getColorTextureId());
        desenfoque.safeGetUniform("Direccion").set(0f, 1f / h4);
        cuadro(desenfoque);

        // 3. la mezcla final, de vuelta en la imagen del juego
        principal.bindWrite(true);
        fin.setSampler("Sampler0", copia.getColorTextureId());
        fin.setSampler("DepthSampler", copia.getDepthTextureId());
        fin.setSampler("BloomSampler", luz1.getColorTextureId());
        fin.safeGetUniform("Tinte").set(p.tinte.x, p.tinte.y, p.tinte.z);
        fin.safeGetUniform("Sombras").set(p.sombras.x, p.sombras.y, p.sombras.z);
        fin.safeGetUniform("Luces").set(p.luces.x, p.luces.y, p.luces.z);
        fin.safeGetUniform("Saturacion").set(p.saturacion);
        fin.safeGetUniform("Contraste").set(p.contraste);
        fin.safeGetUniform("BloomFuerza").set(p.bloom);
        fin.safeGetUniform("SolPos").set(p.solX, p.solY);
        fin.safeGetUniform("SolFuerza").set(p.sol);
        fin.safeGetUniform("SolColor").set(p.solColor.x, p.solColor.y, p.solColor.z);
        fin.safeGetUniform("Neblina").set(p.neblina.x, p.neblina.y, p.neblina.z);
        fin.safeGetUniform("NeblinaFuerza").set(p.neblinaFuerza);
        fin.safeGetUniform("Lejos").set(mc.gameRenderer.getDepthFar());
        fin.safeGetUniform("Calor").set(p.calor);
        fin.safeGetUniform("Tiempo").set((nivel.getGameTime() % 24000L + parcial) / 20f);
        fin.safeGetUniform("Vineta").set(p.vineta);
        fin.safeGetUniform("Aspecto").set((float) w / h);
        cuadro(fin);

        RenderSystem.depthMask(true);
        RenderSystem.enableDepthTest();
        principal.bindWrite(true);
    }

    private static void cuadro(ShaderInstance s) {
        s.apply();
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
        bb.vertex(-1, -1, 0).uv(0, 0).endVertex();
        bb.vertex(1, -1, 0).uv(1, 0).endVertex();
        bb.vertex(1, 1, 0).uv(1, 1).endVertex();
        bb.vertex(-1, 1, 0).uv(0, 1).endVertex();
        BufferUploader.draw(bb.end());
        s.clear();
    }

    /** Los valores de cada cuadro, segun la hora: de noche, de dia y del atardecer, mezclados. */
    private static final class Parametros {
        Vector3f tinte, sombras, luces, solColor, neblina;
        float saturacion, contraste, bloom, umbral, sol, solX, solY, neblinaFuerza, calor, vineta;

        static Parametros de(Minecraft mc, ClientLevel nivel, CieloVelkia.Momento m, RenderLevelStageEvent evento) {
            Parametros p = new Parametros();
            float d = m.dia(), a = m.puesta(), ll = m.lluvia();
            float aurora = m.noche() * m.noche() * (1f - ll);
            // noche -> dia
            p.tinte = new Vector3f(0.86f, 0.93f, 1.12f).lerp(new Vector3f(1.03f, 1.0f, 0.95f), d);
            p.sombras = new Vector3f(0.90f - 0.04f * aurora, 0.96f + 0.06f * aurora, 1.10f).lerp(new Vector3f(0.95f, 0.97f, 1.04f), d);
            p.luces = new Vector3f(0.95f, 1.0f, 1.08f).lerp(new Vector3f(1.04f, 1.01f, 0.95f), d);
            p.saturacion = Mth.lerp(d, 0.86f, 1.12f);
            p.contraste = Mth.lerp(d, 1.04f, 1.05f);
            p.bloom = Mth.lerp(d, 0.45f, 0.32f);
            p.umbral = Mth.lerp(d, 0.52f, 0.82f);
            p.vineta = Mth.lerp(d, 0.30f, 0.18f);
            p.neblina = new Vector3f(CieloVelkia.HORIZONTE_NOCHE).lerp(CieloVelkia.HORIZONTE_DIA, d);
            p.neblinaFuerza = Mth.lerp(d, 0.10f, 0.12f);
            // -> la hora dorada
            p.tinte.lerp(new Vector3f(1.10f, 0.98f, 0.84f), a);
            p.sombras.lerp(new Vector3f(0.92f, 0.88f, 1.06f), a);
            p.luces.lerp(new Vector3f(1.10f, 1.0f, 0.86f), a);
            p.saturacion = Mth.lerp(a, p.saturacion, 1.2f);
            p.bloom = Mth.lerp(a, p.bloom, 0.5f);
            p.neblina.lerp(new Vector3f(CieloVelkia.ATARDECER), a * 0.6f);
            p.neblinaFuerza = Mth.lerp(a, p.neblinaFuerza, 0.18f);
            // la lluvia apaga los colores
            p.saturacion *= 1f - 0.3f * ll;
            p.tinte.lerp(new Vector3f(0.95f, 0.98f, 1.02f), ll);
            // el sol en la pantalla (para los rayos)
            p.solColor = new Vector3f(1.0f, 0.86f, 0.62f).lerp(new Vector3f(1.0f, 0.62f, 0.32f), a);
            float th = m.tiempo() * Mth.TWO_PI;
            Vector4f s = new Vector4f(-Mth.sin(th) * 100f, Mth.cos(th) * 100f, 0f, 1f);
            Matrix4f vista = evento.getPoseStack().last().pose();
            s.mul(vista);
            s.mul(evento.getProjectionMatrix());
            float fuerza = 0f;
            if (s.w > 0.01f) {
                float nx = s.x / s.w, ny = s.y / s.w;
                p.solX = nx * 0.5f + 0.5f;
                p.solY = ny * 0.5f + 0.5f;
                float fuera = Math.max(Math.abs(nx), Math.abs(ny));
                fuerza = 1f - Mth.clamp((fuera - 1.0f) / 0.6f, 0f, 1f);
            }
            p.sol = fuerza * Mth.clamp(m.alturaSol() * 4f + 0.3f, 0f, 1f) * (0.45f + 0.55f * a) * (1f - ll) * 0.9f;
            // el calor: en biomas calientes, de dia y sin lluvia
            float temp = nivel.getBiome(evento.getCamera().getBlockPosition()).value().getBaseTemperature();
            p.calor = Mth.clamp((temp - 1.0f) / 0.8f, 0f, 1f) * d * (1f - ll) * (1f - a);
            return p;
        }
    }
}
