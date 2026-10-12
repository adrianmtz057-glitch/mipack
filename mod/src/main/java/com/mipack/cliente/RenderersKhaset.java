package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.AvisoKhaset;
import com.mipack.khaset.CristalSacrificio;
import com.mipack.khaset.DardoAtlatl;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.Xiuhcoatl;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/** Como se dibuja lo de Khaset (los modelos, texturas y animaciones los genera taller/exportar_mod.py). */
public final class RenderersKhaset {
    private RenderersKhaset() {
    }

    private static ResourceLocation rl(String p) {
        return new ResourceLocation(Mipack.MODID, p);
    }

    /** Khaset al triple; los ojos y las brasas brillan. Con la corona rota se esconden el yelmo y el penacho. */
    public static final class Khaset extends GeoEntityRenderer<KhasetEntity> {
        private static final ResourceLocation FURIA = rl("textures/entity/khaset_furia.png");

        public Khaset(EntityRendererProvider.Context c) {
            super(c, new DefaultedEntityGeoModel<>(rl("khaset")) {
                @Override
                public ResourceLocation getTextureResource(KhasetEntity k) {
                    return k.coronaRota() ? FURIA : super.getTextureResource(k);
                }

                @Override
                public void setCustomAnimations(KhasetEntity k, long id, AnimationState<KhasetEntity> estado) {
                    super.setCustomAnimations(k, id, estado);
                    boolean rota = k.coronaRota();
                    getBone("yelmo").ifPresent(b -> b.setHidden(rota));
                    getBone("plumas").ifPresent(b -> b.setHidden(rota));
                }
            });
            this.withScale(KhasetEntity.ESCALA);
            this.addRenderLayer(new AutoGlowingGeoLayer<>(this));
            this.shadowRadius = 2.0f;
        }

        @Override
        protected float getDeathMaxRotation(KhasetEntity k) {
            return 0f;
        }
    }

    public static final class Cristal extends GeoEntityRenderer<CristalSacrificio> {
        public Cristal(EntityRendererProvider.Context c) {
            super(c, new DefaultedEntityGeoModel<>(rl("cristal_sacrificio")));
            this.addRenderLayer(new AutoGlowingGeoLayer<>(this));
            this.shadowRadius = 1.2f;
        }
    }

    public static final class Serpiente extends GeoEntityRenderer<Xiuhcoatl> {
        public Serpiente(EntityRendererProvider.Context c) {
            super(c, new DefaultedEntityGeoModel<>(rl("xiuhcoatl")));
            this.withScale(Xiuhcoatl.ESCALA);
            this.addRenderLayer(new AutoGlowingGeoLayer<>(this));
            this.shadowRadius = 1.0f;
        }

        @Override
        protected float getDeathMaxRotation(Xiuhcoatl x) {
            return 0f;
        }
    }

    /** El dardo apunta a donde vuela (pluma o astilla de obsidiana). */
    public static final class Dardo extends GeoEntityRenderer<DardoAtlatl> {
        public Dardo(EntityRendererProvider.Context c) {
            super(c, new GeoModel<>() {
                @Override
                public ResourceLocation getModelResource(DardoAtlatl d) {
                    return rl(d.astilla() ? "geo/entity/astilla.geo.json" : "geo/entity/dardo.geo.json");
                }

                @Override
                public ResourceLocation getTextureResource(DardoAtlatl d) {
                    return rl(d.astilla() ? "textures/entity/astilla.png" : "textures/entity/dardo.png");
                }

                @Override
                public ResourceLocation getAnimationResource(DardoAtlatl d) {
                    return rl("animations/entity/cristal_sacrificio.animation.json");
                }
            });
            this.shadowRadius = 0f;
        }

        @Override
        protected void applyRotations(DardoAtlatl d, PoseStack ps, float edad, float giro, float parcial) {
            ps.mulPose(Axis.YP.rotationDegrees(Mth.lerp(parcial, d.yRotO, d.getYRot())));
            ps.mulPose(Axis.XP.rotationDegrees(-Mth.lerp(parcial, d.xRotO, d.getXRot())));
            ps.mulPose(Axis.YP.rotationDegrees(180f));
        }
    }

    /** El circulo de aviso en el piso: el anillo y el disco que se va llenando, del color del aviso. */
    public static final class Aviso extends EntityRenderer<AvisoKhaset> {
        private static final ResourceLocation ANILLO = rl("textures/entity/aviso.png");
        private static final ResourceLocation RELLENO = rl("textures/entity/aviso_lleno.png");

        public Aviso(EntityRendererProvider.Context c) {
            super(c);
        }

        @Override
        public void render(AvisoKhaset a, float giro, float parcial, PoseStack ps, MultiBufferSource b, int luz) {
            float t = a.tickCount + parcial;
            int c = a.color();
            float r = ((c >> 16) & 255) / 255f, g = ((c >> 8) & 255) / 255f, bl = (c & 255) / 255f;
            disco(ps, b, ANILLO, a.radio(), r, g, bl, 0.7f + 0.3f * Mth.sin(t * 0.6f));
            disco(ps, b, RELLENO, a.radio() * a.avance(parcial), r, g, bl, 0.75f);
        }

        private static void disco(PoseStack ps, MultiBufferSource b, ResourceLocation tex, float rad, float r, float g, float bl, float alfa) {
            if (rad < 0.02f)
                return;
            VertexConsumer vc = b.getBuffer(RenderType.entityTranslucentEmissive(tex));
            Matrix4f m = ps.last().pose();
            Matrix3f n = ps.last().normal();
            float y = 0.04f;
            float[][] q = {{-rad, -rad, 0, 0}, {-rad, rad, 0, 1}, {rad, rad, 1, 1}, {rad, -rad, 1, 0}};
            for (float[] v : q)
                vc.vertex(m, v[0], y, v[1]).color(r, g, bl, alfa).uv(v[2], v[3]).overlayCoords(OverlayTexture.NO_OVERLAY)
                        .uv2(LightTexture.FULL_BRIGHT).normal(n, 0f, 1f, 0f).endVertex();
        }

        @Override
        public ResourceLocation getTextureLocation(AvisoKhaset a) {
            return ANILLO;
        }
    }
}
