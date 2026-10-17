package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.bruma.BrumaEntity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.core.object.Color;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/**
 * La Bruma con GeckoLib: geo/entity/bruma.geo.json, animations/entity/bruma.animation.json y textures/entity/bruma.png
 * (128x128 con alpha; generados con taller/exportar_mod.py). La tela son tiras planas con hoyos: se dibuja recortada
 * (cutout) y sin descartar caras. En forma de niebla se ve translucida; mientras viaja como bruma no se dibuja; al
 * morir se desvanece.
 */
public class BrumaRenderer extends GeoEntityRenderer<BrumaEntity> {
    public BrumaRenderer(EntityRendererProvider.Context contexto) {
        super(contexto, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, "bruma")));
        this.withScale(BrumaEntity.ESCALA);
        this.shadowRadius = 0f;                        // flota en su bruma: sin sombra
    }

    private static float alfa(BrumaEntity b, float parcial) {
        if (b.isDeadOrDying())
            return Math.max(0f, 1f - (b.deathTime + parcial) / 60f);
        return b.corporea() ? 1f : 0.55f;
    }

    @Override
    public RenderType getRenderType(BrumaEntity b, ResourceLocation textura, MultiBufferSource buf, float parcial) {
        return alfa(b, parcial) >= 1f ? RenderType.entityCutoutNoCull(textura) : RenderType.entityTranslucent(textura);
    }

    @Override
    public Color getRenderColor(BrumaEntity b, float parcial, int luz) {
        return Color.ofRGBA(1f, 1f, 1f, alfa(b, parcial));
    }

    @Override
    public void render(BrumaEntity b, float giro, float parcial, PoseStack ps, MultiBufferSource buf, int luz) {
        if (!b.escondida())
            super.render(b, giro, parcial, ps, buf, luz);
    }

    @Override
    protected float getDeathMaxRotation(BrumaEntity b) {
        return 0f;                                     // tiene su propia muerte: no se voltea de lado
    }
}
