package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.entidad.AcaroAmatista;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.EndermiteModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.resources.ResourceLocation;

/**
 * El acaro de amatista: los segmentos del endermite (el juego los menea igual), 1.8 veces mas grande, de la piedra de
 * Crackatos con una geoda en el lomo, un cuernito, colmillos y seis patas. Los cristales, sus puntas y los ojos
 * brillan. La textura la pinta taller/personajes/acaro.py (mismas cajas y texOffs que capa()).
 */
public class AcaroRenderer extends MobRenderer<AcaroAmatista, EndermiteModel<AcaroAmatista>> {
    public static final ModelLayerLocation CAPA = new ModelLayerLocation(new ResourceLocation(Mipack.MODID, "acaro_amatista"), "main");
    private static final ResourceLocation TEXTURA = new ResourceLocation(Mipack.MODID, "textures/entity/acaro_amatista.png");
    private static final RenderType BRILLO = RenderType.eyes(new ResourceLocation(Mipack.MODID, "textures/entity/acaro_amatista_brillo.png"));

    public AcaroRenderer(EntityRendererProvider.Context c) {
        super(c, new EndermiteModel<>(c.bakeLayer(CAPA)), 0.55f);
        this.addLayer(new EyesLayer<>(this) {
            @Override
            public RenderType renderType() {
                return BRILLO;
            }
        });
    }

    /** Los segmentos del endermite (mismos nombres, medidas y lugares) con los cristales, colmillos y patas pegados. */
    public static LayerDefinition capa() {
        MeshDefinition malla = new MeshDefinition();
        PartDefinition raiz = malla.getRoot();
        PartDefinition s0 = raiz.addOrReplaceChild("segment0", CubeListBuilder.create().texOffs(0, 0).addBox(-2f, 0f, -1f, 4f, 3f, 2f),
                PartPose.offset(0f, 21f, -3.5f));
        PartDefinition s1 = raiz.addOrReplaceChild("segment1", CubeListBuilder.create().texOffs(0, 6).addBox(-3f, 0f, -2.5f, 6f, 4f, 5f),
                PartPose.offset(0f, 20f, 0f));
        PartDefinition s2 = raiz.addOrReplaceChild("segment2", CubeListBuilder.create().texOffs(0, 16).addBox(-1.5f, 0f, -0.5f, 3f, 3f, 1f),
                PartPose.offset(0f, 21f, 3f));
        raiz.addOrReplaceChild("segment3", CubeListBuilder.create().texOffs(0, 21).addBox(-0.5f, 0f, -0.5f, 1f, 2f, 1f),
                PartPose.offset(0f, 22f, 4f));
        // la geoda del lomo: cada cristal sale para arriba y se inclina hacia afuera
        s1.addOrReplaceChild("cristal0", CubeListBuilder.create().texOffs(24, 0).addBox(-1f, -7f, -1f, 2f, 7f, 2f),
                PartPose.offsetAndRotation(0.5f, 0.6f, 0.6f, -0.3f, 0f, 0.12f));
        s1.addOrReplaceChild("cristal1", CubeListBuilder.create().texOffs(34, 0).addBox(-1f, -5f, -1f, 2f, 5f, 2f),
                PartPose.offsetAndRotation(-1.6f, 0.6f, -0.8f, 0.2f, 0f, -0.45f));
        s1.addOrReplaceChild("cristal2", CubeListBuilder.create().texOffs(44, 0).addBox(-0.5f, -4f, -0.5f, 1f, 4f, 1f),
                PartPose.offsetAndRotation(2.0f, 0.5f, -1.4f, 0.3f, 0f, 0.55f));
        s1.addOrReplaceChild("cristal3", CubeListBuilder.create().texOffs(50, 0).addBox(-0.5f, -3f, -0.5f, 1f, 3f, 1f),
                PartPose.offsetAndRotation(-2.1f, 0.5f, 1.5f, -0.35f, 0f, -0.6f));
        s2.addOrReplaceChild("cristal4", CubeListBuilder.create().texOffs(54, 0).addBox(-0.5f, -3f, -0.5f, 1f, 3f, 1f),
                PartPose.offsetAndRotation(0f, 0.4f, 0f, -0.6f, 0f, 0f));
        s0.addOrReplaceChild("cuerno", CubeListBuilder.create().texOffs(58, 0).addBox(-0.5f, -2f, -0.5f, 1f, 2f, 1f),
                PartPose.offsetAndRotation(0f, 0.4f, -0.2f, 0.5f, 0f, 0f));
        // los colmillos, para adelante y cerrando como pinzas
        s0.addOrReplaceChild("colmillo_der", CubeListBuilder.create().texOffs(24, 12).addBox(-0.5f, -0.5f, -2f, 1f, 1f, 2f),
                PartPose.offsetAndRotation(-1.3f, 2.4f, -0.8f, 0.25f, -0.35f, 0f));
        s0.addOrReplaceChild("colmillo_izq", CubeListBuilder.create().texOffs(24, 12).mirror().addBox(-0.5f, -0.5f, -2f, 1f, 1f, 2f),
                PartPose.offsetAndRotation(1.3f, 2.4f, -0.8f, 0.25f, 0.35f, 0f));
        // tres pares de patas, abiertas hacia adelante y hacia atras, apoyadas en el piso
        for (int i = 0; i < 3; i++) {
            float z = -1.7f + 1.7f * i, abre = (i - 1) * 0.5f;
            s1.addOrReplaceChild("pata_der" + i, CubeListBuilder.create().texOffs(32, 12).addBox(-3f, -0.5f, -0.5f, 3f, 1f, 1f),
                    PartPose.offsetAndRotation(-2.8f, 2.2f, z, 0f, abre, -0.55f));
            s1.addOrReplaceChild("pata_izq" + i, CubeListBuilder.create().texOffs(32, 12).mirror().addBox(0f, -0.5f, -0.5f, 3f, 1f, 1f),
                    PartPose.offsetAndRotation(2.8f, 2.2f, z, 0f, -abre, 0.55f));
        }
        return LayerDefinition.create(malla, 64, 32);
    }

    @Override
    protected void scale(AcaroAmatista a, PoseStack ps, float parcial) {
        ps.scale(1.8f, 1.8f, 1.8f);
    }

    @Override
    protected float getFlipDegrees(AcaroAmatista a) {
        return 180f;
    }

    @Override
    public ResourceLocation getTextureLocation(AcaroAmatista a) {
        return TEXTURA;
    }
}
