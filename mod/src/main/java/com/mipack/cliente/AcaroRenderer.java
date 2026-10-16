package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.entidad.AcaroAmatista;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.EndermiteModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.resources.ResourceLocation;

/** El acaro de amatista: el modelo del endermite, 1.8 veces mas grande, de cristal (sus puntas brillan). */
public class AcaroRenderer extends MobRenderer<AcaroAmatista, EndermiteModel<AcaroAmatista>> {
    private static final ResourceLocation TEXTURA = new ResourceLocation(Mipack.MODID, "textures/entity/acaro_amatista.png");
    private static final RenderType BRILLO = RenderType.eyes(new ResourceLocation(Mipack.MODID, "textures/entity/acaro_amatista_brillo.png"));

    public AcaroRenderer(EntityRendererProvider.Context c) {
        super(c, new EndermiteModel<>(c.bakeLayer(ModelLayers.ENDERMITE)), 0.55f);
        this.addLayer(new EyesLayer<>(this) {
            @Override
            public RenderType renderType() {
                return BRILLO;
            }
        });
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
