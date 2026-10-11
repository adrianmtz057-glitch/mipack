package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.entidad.CrackatosEntity;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/**
 * Crackatos con GeckoLib: geo/entity/crackatos.geo.json, animations/entity/crackatos.animation.json y
 * textures/entity/crackatos.png (generados con taller/exportar_mod.py); los ojos brillan con crackatos_glowmask.png.
 */
public class CrackatosRenderer extends GeoEntityRenderer<CrackatosEntity> {
    public CrackatosRenderer(EntityRendererProvider.Context contexto) {
        super(contexto, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, "crackatos")));
        this.withScale(CrackatosEntity.ESCALA);
        this.addRenderLayer(new AutoGlowingGeoLayer<>(this));
        this.shadowRadius = 3.2f;
    }

    @Override
    protected float getDeathMaxRotation(CrackatosEntity animatable) {
        return 0f;                                // tiene su propia animacion de muerte: no se voltea de lado
    }
}
