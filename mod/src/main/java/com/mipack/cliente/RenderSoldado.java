package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.bruma.ClonBruma;
import com.mipack.bruma.SoldadoBruma;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.core.object.Color;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/** El ejercito de La Bruma (cuerpo humano de 64x64, el grande al doble) y sus clones (el modelo de ella, oscuro). */
public class RenderSoldado extends HumanoidMobRenderer<SoldadoBruma, HumanoidModel<SoldadoBruma>> {
    private static final ResourceLocation SOLDADO = new ResourceLocation(Mipack.MODID, "textures/entity/soldado_bruma.png");
    private static final ResourceLocation ARQUERO = new ResourceLocation(Mipack.MODID, "textures/entity/arquero_bruma.png");
    private static final ResourceLocation GRANDE = new ResourceLocation(Mipack.MODID, "textures/entity/soldado_grande.png");

    public RenderSoldado(EntityRendererProvider.Context c) {
        super(c, new HumanoidModel<>(c.bakeLayer(ModelLayers.ZOMBIE)), 0.5f);
    }

    @Override
    public ResourceLocation getTextureLocation(SoldadoBruma s) {
        return switch (s.tipo()) {
            case ARQUERO -> ARQUERO;
            case GRANDE -> GRANDE;
            default -> SOLDADO;
        };
    }

    @Override
    protected void scale(SoldadoBruma s, PoseStack ps, float parcial) {
        if (s.tipo() == SoldadoBruma.Tipo.GRANDE)
            ps.scale(2.15f, 2.15f, 2.15f);
    }

    @Override
    public void render(SoldadoBruma s, float giro, float parcial, PoseStack ps, MultiBufferSource buf, int luz) {
        this.model.rightArmPose = s.tipo() == SoldadoBruma.Tipo.ARQUERO && s.isAggressive()
                ? HumanoidModel.ArmPose.BOW_AND_ARROW : HumanoidModel.ArmPose.EMPTY;
        super.render(s, giro, parcial, ps, buf, luz);
    }

    /** El clon: el modelo de La Bruma, mas chico, oscuro y medio transparente. */
    public static class Clon extends GeoEntityRenderer<ClonBruma> {
        public Clon(EntityRendererProvider.Context c) {
            super(c, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, "bruma")));
            this.withScale(ClonBruma.ESCALA);
            this.shadowRadius = 0f;
        }

        @Override
        public RenderType getRenderType(ClonBruma b, ResourceLocation textura, MultiBufferSource buf, float parcial) {
            return RenderType.entityTranslucent(textura);
        }

        @Override
        public Color getRenderColor(ClonBruma b, float parcial, int luz) {
            return Color.ofRGBA(0.35f, 0.3f, 0.45f, 0.75f);
        }
    }
}
