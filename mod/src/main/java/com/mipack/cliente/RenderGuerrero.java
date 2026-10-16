package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.GuerreroCalavera;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.SkeletonModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;

/**
 * El guerrero calavera: el esqueleto del juego con un penacho de plumas de quetzal (siete plumas en abanico detras
 * de la cabeza), la cara pintada de negro y rojo, orejeras de oro y el maxtlatl rojo (la textura la pinta
 * taller/exportar_mod.py). Al salir del piso sube desde abajo.
 */
public class RenderGuerrero extends HumanoidMobRenderer<GuerreroCalavera, SkeletonModel<GuerreroCalavera>> {
    public static final ModelLayerLocation CAPA = new ModelLayerLocation(new ResourceLocation(Mipack.MODID, "guerrero_calavera"), "main");
    private static final ResourceLocation TEXTURA = new ResourceLocation(Mipack.MODID, "textures/entity/guerrero_calavera.png");
    private static final int PLUMAS = 7;

    public RenderGuerrero(EntityRendererProvider.Context c) {
        super(c, new SkeletonModel<>(c.bakeLayer(CAPA)), 0.5f);
    }

    /** Los huesos del esqueleto (como SkeletonModel) mas el penacho en la cabeza. Textura de 64x64. */
    public static LayerDefinition capa() {
        MeshDefinition malla = HumanoidModel.createMesh(CubeDeformation.NONE, 0f);
        PartDefinition raiz = malla.getRoot();
        raiz.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(40, 16).addBox(-1f, -2f, -1f, 2f, 12f, 2f),
                PartPose.offset(-5f, 2f, 0f));
        raiz.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(40, 16).mirror().addBox(-1f, -2f, -1f, 2f, 12f, 2f),
                PartPose.offset(5f, 2f, 0f));
        raiz.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(0, 16).addBox(-1f, 0f, -1f, 2f, 12f, 2f),
                PartPose.offset(-2f, 12f, 0f));
        raiz.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(0, 16).mirror().addBox(-1f, 0f, -1f, 2f, 12f, 2f),
                PartPose.offset(2f, 12f, 0f));
        PartDefinition cabeza = raiz.getChild("head");
        for (int i = 0; i < PLUMAS; i++) {
            float f = (i - (PLUMAS - 1) / 2f) / ((PLUMAS - 1) / 2f);   // -1 .. 1
            cabeza.addOrReplaceChild("pluma" + i, CubeListBuilder.create().texOffs(i * 4, 32).addBox(-1f, -11f, 0f, 2f, 11f, 0f),
                    PartPose.offsetAndRotation(f * 3.2f, -7.5f, 3.2f, -0.35f, 0f, f * 0.75f));
        }
        cabeza.addOrReplaceChild("diadema", CubeListBuilder.create().texOffs(0, 48).addBox(-4.5f, -9.0f, -4.5f, 9f, 2f, 9f),
                PartPose.ZERO);
        return LayerDefinition.create(malla, 64, 64);
    }

    @Override
    public void render(GuerreroCalavera g, float giro, float parcial, PoseStack ps, MultiBufferSource buf, int luz) {
        float u = Math.min(1f, (g.tickCount + parcial) / GuerreroCalavera.T_SURGIR);
        ps.pushPose();
        if (u < 1f)
            ps.translate(0, -2.0 * (1f - u) * (1f - u), 0);
        super.render(g, giro, parcial, ps, buf, luz);
        ps.popPose();
    }

    @Override
    public ResourceLocation getTextureLocation(GuerreroCalavera g) {
        return TEXTURA;
    }
}
