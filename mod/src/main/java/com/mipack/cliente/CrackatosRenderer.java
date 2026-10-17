package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.entidad.CrackatosEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;
import software.bernie.geckolib.renderer.layer.GeoRenderLayer;

/**
 * Crackatos con GeckoLib: geo/entity/crackatos.geo.json, animations/entity/crackatos.animation.json y
 * textures/entity/crackatos.png (generados con taller/exportar_mod.py); los ojos brillan con crackatos_glowmask.png y,
 * en su fase 2, todos sus cristales laten con crackatos_cristales.png.
 */
public class CrackatosRenderer extends GeoEntityRenderer<CrackatosEntity> {
    public CrackatosRenderer(EntityRendererProvider.Context contexto) {
        super(contexto, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, "crackatos")));
        this.withScale(CrackatosEntity.ESCALA);
        this.addRenderLayer(new AutoGlowingGeoLayer<>(this));
        this.addRenderLayer(new Cristales(this));
        this.shadowRadius = 1.6f * CrackatosEntity.ESCALA;
    }

    @Override
    protected float getDeathMaxRotation(CrackatosEntity animatable) {
        return 0f;                                // tiene su propia animacion de muerte: no se voltea de lado
    }

    /** Fase 2: los cristales de amatista brillan y laten. */
    private static final class Cristales extends GeoRenderLayer<CrackatosEntity> {
        private static final ResourceLocation TEXTURA = new ResourceLocation(Mipack.MODID, "textures/entity/crackatos_cristales.png");

        Cristales(GeoRenderer<CrackatosEntity> r) {
            super(r);
        }

        @Override
        public void render(PoseStack ps, CrackatosEntity c, BakedGeoModel modelo, RenderType tipo, MultiBufferSource buf,
                           VertexConsumer vc, float parcial, int luz, int overlay) {
            if (!c.fase2() || c.isDeadOrDying())
                return;
            float a = 0.55f + 0.45f * Mth.sin((c.tickCount + parcial) * 0.12f);
            RenderType brillo = CapaBrillo.tipo(TEXTURA);
            getRenderer().reRender(modelo, ps, buf, c, brillo, buf.getBuffer(brillo), parcial, LightTexture.FULL_BRIGHT,
                    OverlayTexture.NO_OVERLAY, 1f, 1f, 1f, a);
        }
    }
}
