package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.entidad.PuaCayendo;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/**
 * Las puas: el modelo (geo/entity/pua.geo.json, una pua del lomo de Crackatos) y, para las que caen, el circulo
 * morado de aviso en el piso con un disco que se va llenando hasta que cae.
 */
public class PuaRenderer extends GeoEntityRenderer<PuaCayendo> {
    private static final ResourceLocation CIRCULO = new ResourceLocation(Mipack.MODID, "textures/entity/circulo.png");
    private static final ResourceLocation RELLENO = new ResourceLocation(Mipack.MODID, "textures/entity/circulo_lleno.png");
    private static final float LARGO = 1.5f;                 // lo que mide la pua (bloques), de la base a la punta

    public PuaRenderer(EntityRendererProvider.Context contexto) {
        super(contexto, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, "pua")));
        this.shadowRadius = 0f;
    }

    @Override
    public void render(PuaCayendo pua, float giro, float parcial, PoseStack pose, MultiBufferSource buffers, int luz) {
        int brillo = LightTexture.pack(Math.max(LightTexture.block(luz), 9), LightTexture.sky(luz));
        if (pua.cae()) {
            float t = pua.edad(parcial);
            disco(pose, buffers, CIRCULO, PuaCayendo.RADIO, 0.7f + 0.3f * Mth.sin(t * 0.5f));
            disco(pose, buffers, RELLENO, PuaCayendo.RADIO * pua.avance(parcial), 0.75f);
            float h = pua.alturaQueFalta(parcial);
            if (h < 0)
                return;                           // todavia no cae: solo se ve el aviso
            pose.pushPose();
            pose.translate(0, h + LARGO, 0);
            pose.mulPose(Axis.YP.rotationDegrees(pua.getYRot()));
            pose.mulPose(Axis.XP.rotationDegrees(180f));      // la punta hacia abajo
            super.render(pua, 0f, parcial, pose, buffers, brillo);
            pose.popPose();
            return;
        }
        // las que salen del lomo: apuntan a donde van y giran sobre si mismas
        pose.pushPose();
        pose.translate(0, LARGO / 2, 0);
        pose.mulPose(Axis.YP.rotationDegrees(Mth.lerp(parcial, pua.yRotO, pua.getYRot())));
        pose.mulPose(Axis.XP.rotationDegrees(90f - Mth.lerp(parcial, pua.xRotO, pua.getXRot())));
        pose.mulPose(Axis.YP.rotationDegrees(pua.edad(parcial) * 30f));
        pose.translate(0, -LARGO / 2, 0);
        super.render(pua, 0f, parcial, pose, buffers, brillo);
        pose.popPose();
    }

    /** Un cuadro plano en el piso con la textura del circulo (de radio r), brillando aunque este oscuro. */
    private static void disco(PoseStack pose, MultiBufferSource buffers, ResourceLocation textura, float r, float alfa) {
        if (r < 0.02f)
            return;
        VertexConsumer vc = buffers.getBuffer(RenderType.entityTranslucentEmissive(textura));
        PoseStack.Pose p = pose.last();
        Matrix4f m = p.pose();
        Matrix3f n = p.normal();
        float y = 0.03f;
        punto(vc, m, n, -r, y, -r, 0f, 0f, alfa);
        punto(vc, m, n, -r, y, r, 0f, 1f, alfa);
        punto(vc, m, n, r, y, r, 1f, 1f, alfa);
        punto(vc, m, n, r, y, -r, 1f, 0f, alfa);
    }

    private static void punto(VertexConsumer vc, Matrix4f m, Matrix3f n, float x, float y, float z, float u, float v, float alfa) {
        vc.vertex(m, x, y, z).color(1f, 1f, 1f, alfa).uv(u, v).overlayCoords(OverlayTexture.NO_OVERLAY)
                .uv2(LightTexture.FULL_BRIGHT).normal(n, 0f, 1f, 0f).endVertex();
    }
}
