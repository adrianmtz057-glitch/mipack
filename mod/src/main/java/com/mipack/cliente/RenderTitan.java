package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.titanes.TipoTitan;
import com.mipack.titanes.Titan;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/** Un titan con su modelo (geo/entity/{id}.geo.json) a su escala; si tiene glowmask, lo que brilla brilla. */
public class RenderTitan extends GeoEntityRenderer<Titan> {
    public RenderTitan(EntityRendererProvider.Context c, TipoTitan tipo) {
        super(c, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, tipo.id())) {
            @Override
            public void setCustomAnimations(Titan t, long id, AnimationState<Titan> estado) {
                super.setCustomAnimations(t, id, estado);
                float parcial = estado.getPartialTick();
                for (int i = 1; i <= t.tipo.tramos(); i++) {             // el cuerpo sigue el camino de la cabeza
                    float g = t.giroDeTramo(i, parcial) * Mth.DEG_TO_RAD;
                    getBone("s" + i).ifPresent(b -> b.setRotY(b.getRotY() + g));
                }
            }
        });
        this.withScale(tipo.escala());
        this.shadowRadius = tipo.ancho() * 0.4f;
        ResourceLocation brillo = new ResourceLocation(Mipack.MODID, "textures/entity/" + tipo.id() + "_glowmask.png");
        if (Minecraft.getInstance().getResourceManager().getResource(brillo).isPresent())
            this.addRenderLayer(new CapaBrillo<>(this));
    }

    @Override
    protected float getDeathMaxRotation(Titan t) {
        return 0f;
    }
}
