package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.bichos.Bicho;
import com.mipack.bichos.BichosDatos.Especie;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/**
 * Un bicho de Velkia: geo/entity/bichos/{id}.geo.json con sus animaciones y su textura; manchado de mura usa
 * {id}_mura.png. Lo que brilla (ojos, marcas o las venas de mura) va en su glowmask.
 */
public class RenderBicho extends GeoEntityRenderer<Bicho> {
    private final ResourceLocation normal, mura;
    private final boolean brilla;

    public RenderBicho(EntityRendererProvider.Context c, Especie e) {
        super(c, new DefaultedEntityGeoModel<>(new ResourceLocation(Mipack.MODID, "bichos/" + e.id())));
        this.normal = new ResourceLocation(Mipack.MODID, "textures/entity/bichos/" + e.id() + ".png");
        this.mura = new ResourceLocation(Mipack.MODID, "textures/entity/bichos/" + e.id() + "_mura.png");
        this.brilla = e.brilla();
        this.shadowRadius = Math.min(1.2f, e.ancho() * 0.5f);
        this.addRenderLayer(new CapaBrillo<>(this) {
            @Override
            public void render(PoseStack ps, Bicho b, BakedGeoModel m, RenderType t, MultiBufferSource buf, VertexConsumer v,
                               float parcial, int luz, int overlay) {
                if (b.manchado() || brilla)
                    super.render(ps, b, m, t, buf, v, parcial, luz, overlay);
            }
        });
    }

    @Override
    public ResourceLocation getTextureLocation(Bicho b) {
        return b.manchado() ? this.mura : this.normal;
    }

    @Override
    public RenderType getRenderType(Bicho b, ResourceLocation textura, MultiBufferSource buf, float parcial) {
        return RenderType.entityCutoutNoCull(textura);
    }
}
