package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.MipackConfig;
import com.mojang.blaze3d.platform.GlStateManager;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.BufferUploader;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.DimensionSpecialEffects;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.material.FogType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * El cielo de Velkia en el mundo normal: de dia un cielo de desierto (azul hondo arriba, polvo calido en el
 * horizonte, cirros), de noche estrellas con la via lactea (giran como las del juego) y auroras que ondulan.
 * Al amanecer y al atardecer el horizonte se pone naranja del lado del sol. La niebla toma el color del horizonte
 * para que el terreno lejano se funda con el cielo.
 * Las texturas las genera taller/cielo.py (cubos en atlas de 3 x 2; CARAS igual que alla).
 * Bajo el agua, en lava, con ceguera o en biomas de niebla espesa se deja el cielo del juego.
 */
public class CieloVelkia extends DimensionSpecialEffects.OverworldEffects {
    private static final ResourceLocation DIA = tex("cielo_dia"), NOCHE = tex("cielo_noche"),
            ESTRELLAS = tex("estrellas"), SOL = tex("sol");
    private static final ResourceLocation LUNA = new ResourceLocation("textures/environment/moon_phases.png");
    private static final int LADO_DIA = 192, LADO_NOCHE = 48, LADO_ESTRELLAS = 320;
    private static final float D = 50f;                       // la mitad del cubo del cielo

    // columna, fila, centro, derecha, arriba de la imagen (igual que CARAS en taller/cielo.py)
    private static final float[][] CARAS = {
            {0, 0, 0, 1, 0, -1, 0, 0, 0, 0, -1},
            {1, 0, 0, 0, -1, 1, 0, 0, 0, 1, 0},
            {2, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0},
            {0, 1, 0, -1, 0, -1, 0, 0, 0, 0, 1},
            {1, 1, 0, 0, 1, -1, 0, 0, 0, 1, 0},
            {2, 1, -1, 0, 0, 0, 0, -1, 0, 1, 0}};

    // el color del cielo justo arriba del horizonte (para la niebla): de dia, de noche y del atardecer
    private static final Vector3f HORIZONTE_DIA = new Vector3f(0.94f, 0.86f, 0.69f);
    private static final Vector3f HORIZONTE_NOCHE = new Vector3f(0.078f, 0.072f, 0.155f);
    private static final Vector3f ATARDECER = new Vector3f(1.0f, 0.52f, 0.24f), ATARDECER_LEJOS = new Vector3f(0.75f, 0.32f, 0.55f);

    private static ResourceLocation tex(String nombre) {
        return new ResourceLocation(Mipack.MODID, "textures/environment/" + nombre + ".png");
    }

    /** Lo que se necesita en cada cuadro: que tan de dia es, la lluvia, donde esta el sol. */
    private record Momento(float tiempo, float alturaSol, float dia, float noche, float lluvia, float puesta, float solX) {
        static Momento de(ClientLevel nivel, float parcial) {
            float t = nivel.getTimeOfDay(parcial);              // 0 mediodia, 0.25 atardecer, 0.5 medianoche
            float alto = Mth.cos(t * Mth.TWO_PI);
            float dia = Mth.clamp(alto * 2.4f + 0.42f, 0f, 1f);
            float lluvia = Mth.clamp(nivel.getRainLevel(parcial) * 0.75f + nivel.getThunderLevel(parcial) * 0.25f, 0f, 1f);
            float puesta = (float) Math.pow(Mth.clamp(1f - Math.abs(alto) / 0.36f, 0f, 1f), 1.4) * (1f - lluvia * 0.8f);
            return new Momento(t, alto, dia, 1f - dia, lluvia, puesta, -Mth.sin(t * Mth.TWO_PI));
        }
    }

    private static boolean usar(Camera camara, boolean niebla) {
        if (!MipackConfig.CIELO.get() || niebla || camara.getFluidInCamera() != FogType.NONE)
            return false;
        return !(camara.getEntity() instanceof LivingEntity e && (e.hasEffect(MobEffects.BLINDNESS) || e.hasEffect(MobEffects.DARKNESS)));
    }

    @Override
    public boolean renderSky(ClientLevel nivel, int ticks, float parcial, PoseStack pose, Camera camara, Matrix4f proyeccion,
                             boolean niebla, Runnable prepararNiebla) {
        if (!usar(camara, niebla))
            return false;
        Momento m = Momento.de(nivel, parcial);
        float segundos = (ticks + parcial) / 20f;
        Matrix4f fijo = pose.last().pose();

        RenderSystem.depthMask(false);
        RenderSystem.disableCull();
        RenderSystem.enableBlend();

        // 1. el fondo de la noche (opaco)
        RenderSystem.defaultBlendFunc();
        caja(fijo, NOCHE, LADO_NOCHE, 1f, 1f, 1f, 1f);

        // 2. las estrellas y la via lactea: se suman y giran con el cielo
        float estrellas = m.noche() * m.noche() * (1f - m.lluvia());
        if (estrellas > 0.01f) {
            pose.pushPose();
            pose.mulPose(Axis.YP.rotationDegrees(-90f));
            pose.mulPose(Axis.XP.rotationDegrees(m.tiempo() * 360f));
            sumar();
            caja(pose.last().pose(), ESTRELLAS, LADO_ESTRELLAS, estrellas, estrellas, estrellas, 1f);
            pose.popPose();
        }

        // 3. el dia encima (transparente al anochecer)
        RenderSystem.defaultBlendFunc();
        if (m.dia() > 0.002f)
            caja(fijo, DIA, LADO_DIA, 1f, 1f, 1f, m.dia());

        // 4. la lluvia: un velo gris
        if (m.lluvia() > 0.01f) {
            float g = 0.22f + 0.36f * m.dia();
            velo(fijo, g, g * 1.02f, g * 1.08f, m.lluvia() * 0.72f);
        }

        // 5. el resplandor del atardecer (del lado del sol)
        sumar();
        if (m.puesta() > 0.01f)
            atardecer(fijo, m);

        // 6. las auroras
        float aurora = m.noche() * m.noche() * (1f - m.lluvia()) * actividad(nivel);
        if (aurora > 0.01f)
            auroras(fijo, aurora, segundos);

        // 7. el sol y la luna
        pose.pushPose();
        pose.mulPose(Axis.YP.rotationDegrees(-90f));
        pose.mulPose(Axis.XP.rotationDegrees(m.tiempo() * 360f));
        astros(pose.last().pose(), nivel, 1f - m.lluvia());
        pose.popPose();

        if (nivel.getSkyFlashTime() > 0)                       // el relampago ilumina todo el cielo
            velo(fijo, 0.9f, 0.9f, 1f, 0.35f);

        RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
        RenderSystem.defaultBlendFunc();
        RenderSystem.disableBlend();
        RenderSystem.enableCull();
        RenderSystem.depthMask(true);
        return true;
    }

    private static void sumar() {
        RenderSystem.blendFunc(GlStateManager.SourceFactor.SRC_ALPHA, GlStateManager.DestFactor.ONE);
    }

    /** Unas noches hay mas aurora que otras (cambia despacio, de noche en noche). */
    private static float actividad(ClientLevel nivel) {
        double noche = nivel.getDayTime() / 24000.0;
        return (float) (0.62 + 0.38 * Math.sin(noche * 2.3 + 0.7));
    }

    /** Un cubo del cielo con su atlas de 3 x 2 caras. */
    private static void caja(Matrix4f m, ResourceLocation textura, int lado, float r, float g, float b, float a) {
        RenderSystem.setShader(GameRenderer::getPositionTexColorShader);
        RenderSystem.setShaderTexture(0, textura);
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX_COLOR);
        float eu = 0.5f / (3 * lado), ev = 0.5f / (2 * lado);   // medio texel adentro: no se cuela la cara vecina
        for (float[] c : CARAS) {
            float u0 = c[0] / 3f + eu, u1 = (c[0] + 1) / 3f - eu, v0 = c[1] / 2f + ev, v1 = (c[1] + 1) / 2f - ev;
            esquina(bb, m, c, -1, 1).uv(u0, v0).color(r, g, b, a).endVertex();
            esquina(bb, m, c, 1, 1).uv(u1, v0).color(r, g, b, a).endVertex();
            esquina(bb, m, c, 1, -1).uv(u1, v1).color(r, g, b, a).endVertex();
            esquina(bb, m, c, -1, -1).uv(u0, v1).color(r, g, b, a).endVertex();
        }
        BufferUploader.drawWithShader(bb.end());
    }

    private static VertexConsumer esquina(BufferBuilder bb, Matrix4f m, float[] c, int s, int t) {
        float x = (c[2] + s * c[5] + t * c[8]) * D, y = (c[3] + s * c[6] + t * c[9]) * D, z = (c[4] + s * c[7] + t * c[10]) * D;
        return bb.vertex(m, x, y, z);
    }

    /** Un cubo de un solo color (la lluvia, el relampago). */
    private static void velo(Matrix4f m, float r, float g, float b, float a) {
        RenderSystem.defaultBlendFunc();
        RenderSystem.setShader(GameRenderer::getPositionColorShader);
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        for (float[] c : CARAS) {
            esquina(bb, m, c, -1, 1).color(r, g, b, a).endVertex();
            esquina(bb, m, c, 1, 1).color(r, g, b, a).endVertex();
            esquina(bb, m, c, 1, -1).color(r, g, b, a).endVertex();
            esquina(bb, m, c, -1, -1).color(r, g, b, a).endVertex();
        }
        BufferUploader.drawWithShader(bb.end());
    }

    /** Que tanto brilla el atardecer en el rumbo (x, z): mas del lado del sol. */
    private static float ladoDelSol(float x, float z, Momento m) {
        float hacia = Math.max(0f, x * Math.signum(m.solX()) / Math.max(1e-3f, Mth.sqrt(x * x + z * z)));
        return 0.22f + 0.78f * hacia * hacia;
    }

    /** Una franja alrededor del horizonte, naranja del lado del sol y rosa morado del otro, que se desvanece hacia arriba. */
    private static void atardecer(Matrix4f m, Momento mo) {
        RenderSystem.setShader(GameRenderer::getPositionColorShader);
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        int n = 64;
        float abajo = -0.12f * D, medio = 0.10f * D, arriba = 0.48f * D;
        for (int i = 0; i < n; i++) {
            float a0 = Mth.TWO_PI * i / n, a1 = Mth.TWO_PI * (i + 1) / n;
            float x0 = Mth.cos(a0) * D, z0 = Mth.sin(a0) * D, x1 = Mth.cos(a1) * D, z1 = Mth.sin(a1) * D;
            float k0 = ladoDelSol(x0, z0, mo) * mo.puesta(), k1 = ladoDelSol(x1, z1, mo) * mo.puesta();
            Vector3f c0 = mezcla(k0 / Math.max(1e-3f, mo.puesta())), c1 = mezcla(k1 / Math.max(1e-3f, mo.puesta()));
            // de abajo al medio (lo mas fuerte) y del medio hacia arriba (se apaga)
            bb.vertex(m, x0, abajo, z0).color(c0.x, c0.y, c0.z, k0 * 0.5f).endVertex();
            bb.vertex(m, x1, abajo, z1).color(c1.x, c1.y, c1.z, k1 * 0.5f).endVertex();
            bb.vertex(m, x1, medio, z1).color(c1.x, c1.y, c1.z, k1 * 0.85f).endVertex();
            bb.vertex(m, x0, medio, z0).color(c0.x, c0.y, c0.z, k0 * 0.85f).endVertex();
            bb.vertex(m, x0, medio, z0).color(c0.x, c0.y, c0.z, k0 * 0.85f).endVertex();
            bb.vertex(m, x1, medio, z1).color(c1.x, c1.y, c1.z, k1 * 0.85f).endVertex();
            bb.vertex(m, x1, arriba, z1).color(c1.x, c1.y, c1.z, 0f).endVertex();
            bb.vertex(m, x0, arriba, z0).color(c0.x, c0.y, c0.z, 0f).endVertex();
        }
        BufferUploader.drawWithShader(bb.end());
    }

    private static Vector3f mezcla(float haciaElSol) {
        float k = Mth.clamp(haciaElSol, 0f, 1f);
        return new Vector3f(ATARDECER_LEJOS).lerp(ATARDECER, k);
    }

    /**
     * Las auroras: tres cortinas al norte que ondulan (se doblan hacia adelante y atras), con rayos que suben y bajan
     * de brillo; verdes abajo, aguamarina en medio y moradas arriba, sumadas al cielo.
     */
    private static void auroras(Matrix4f m, float intensidad, float s) {
        RenderSystem.setShader(GameRenderer::getPositionColorShader);
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR);
        int seg = 90;
        for (int c = 0; c < 3; c++) {
            float az0 = (-75f + 22f * c) * Mth.DEG_TO_RAD, az1 = (55f + 14f * c) * Mth.DEG_TO_RAD;
            float base = 0.16f + 0.07f * c, alto = 0.36f + 0.10f * c;
            float[][] p = new float[seg + 1][];
            for (int i = 0; i <= seg; i++) {
                float az = Mth.lerp((float) i / seg, az0, az1);
                float r = D * (1.05f + 0.16f * Mth.sin(i * 0.19f + s * 0.23f + c * 1.7f) + 0.07f * Mth.sin(i * 0.47f - s * 0.41f + c));
                float x = Mth.sin(az) * r, z = -Mth.cos(az) * r;
                float y0 = D * (base + 0.035f * Mth.sin(i * 0.15f + s * 0.31f + c * 2.1f));
                float h = D * alto * (0.72f + 0.28f * Mth.sin(i * 0.10f - s * 0.19f + c * 0.9f));
                float rayo = 0.45f + 0.55f * (0.5f + 0.5f * Mth.sin(i * 1.31f + s * 1.6f + c * 3f))
                        * (0.5f + 0.5f * Mth.sin(i * 0.29f - s * 0.55f + c));
                float orilla = Mth.sin(Mth.PI * i / seg);
                p[i] = new float[]{x, y0, z, h, intensidad * rayo * orilla * (0.85f - 0.15f * c)};
            }
            for (int i = 0; i < seg; i++) {
                float[] a = p[i], b = p[i + 1];
                franja(bb, m, a, b, 0f, 0.16f, 0.20f, 1.00f, 0.55f, 0.15f, 0.20f, 1.00f, 0.55f, 1.00f);
                franja(bb, m, a, b, 0.16f, 0.55f, 0.20f, 1.00f, 0.55f, 1.00f, 0.15f, 0.85f, 0.78f, 0.45f);
                franja(bb, m, a, b, 0.55f, 1.00f, 0.15f, 0.85f, 0.78f, 0.45f, 0.62f, 0.26f, 0.85f, 0.00f);
            }
        }
        BufferUploader.drawWithShader(bb.end());
    }

    /** Un pedazo de cortina entre dos alturas (fracciones de su alto), con color y fuerza abajo y arriba. */
    private static void franja(BufferBuilder bb, Matrix4f m, float[] a, float[] b, float f0, float f1,
                               float r0, float g0, float b0, float k0, float r1, float g1, float b1, float k1) {
        bb.vertex(m, a[0], a[1] + a[3] * f0, a[2]).color(r0, g0, b0, a[4] * k0).endVertex();
        bb.vertex(m, b[0], b[1] + b[3] * f0, b[2]).color(r0, g0, b0, b[4] * k0).endVertex();
        bb.vertex(m, b[0], b[1] + b[3] * f1, b[2]).color(r1, g1, b1, b[4] * k1).endVertex();
        bb.vertex(m, a[0], a[1] + a[3] * f1, a[2]).color(r1, g1, b1, a[4] * k1).endVertex();
    }

    /** El sol del desierto (con su halo) y la luna del juego, en el mismo giro que los del juego. */
    private static void astros(Matrix4f m, ClientLevel nivel, float visible) {
        RenderSystem.blendFuncSeparate(GlStateManager.SourceFactor.SRC_ALPHA, GlStateManager.DestFactor.ONE,
                GlStateManager.SourceFactor.ONE, GlStateManager.DestFactor.ZERO);
        RenderSystem.setShader(GameRenderer::getPositionTexShader);
        RenderSystem.setShaderColor(1f, 1f, 1f, visible);
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        float s = 36f;
        RenderSystem.setShaderTexture(0, SOL);
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
        bb.vertex(m, -s, 100f, -s).uv(0f, 0f).endVertex();
        bb.vertex(m, s, 100f, -s).uv(1f, 0f).endVertex();
        bb.vertex(m, s, 100f, s).uv(1f, 1f).endVertex();
        bb.vertex(m, -s, 100f, s).uv(0f, 1f).endVertex();
        BufferUploader.drawWithShader(bb.end());
        float l = 20f;
        int fase = nivel.getMoonPhase(), i = fase % 4, j = fase / 4 % 2;
        float u0 = i / 4f, v0 = j / 2f, u1 = (i + 1) / 4f, v1 = (j + 1) / 2f;
        RenderSystem.setShaderTexture(0, LUNA);
        bb.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_TEX);
        bb.vertex(m, -l, -100f, l).uv(u1, v1).endVertex();
        bb.vertex(m, l, -100f, l).uv(u0, v1).endVertex();
        bb.vertex(m, l, -100f, -l).uv(u0, v0).endVertex();
        bb.vertex(m, -l, -100f, -l).uv(u1, v0).endVertex();
        BufferUploader.drawWithShader(bb.end());
        RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
    }

    /** La niebla del color del horizonte (con la lluvia y el atardecer igual que el cielo): el terreno se funde con el. */
    @Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
    public static final class Niebla {
        private Niebla() {
        }

        @SubscribeEvent
        public static void color(ViewportEvent.ComputeFogColor evento) {
            ClientLevel nivel = Minecraft.getInstance().level;
            if (nivel == null || !(nivel.effects() instanceof CieloVelkia) || !usar(evento.getCamera(), false))
                return;
            Momento m = Momento.de(nivel, (float) evento.getPartialTick());
            Vector3f c = new Vector3f(HORIZONTE_NOCHE).lerp(HORIZONTE_DIA, m.dia());
            if (m.lluvia() > 0.01f) {
                float g = 0.22f + 0.36f * m.dia();
                c.lerp(new Vector3f(g, g * 1.02f, g * 1.08f), m.lluvia() * 0.72f);
            }
            if (m.puesta() > 0.01f) {                         // hacia el sol la niebla se pone naranja, como el cielo
                Vector3f mira = evento.getCamera().getLookVector();
                float k = ladoDelSol(mira.x(), mira.z(), m) * m.puesta() * 0.85f;
                c.add(new Vector3f(mezcla(k / Math.max(1e-3f, m.puesta()))).mul(k));
            }
            evento.setRed(Math.min(1f, c.x()));
            evento.setGreen(Math.min(1f, c.y()));
            evento.setBlue(Math.min(1f, c.z()));
        }
    }
}
