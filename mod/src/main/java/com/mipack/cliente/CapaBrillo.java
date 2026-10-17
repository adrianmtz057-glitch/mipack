package com.mipack.cliente;

import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexFormat;
import net.minecraft.Util;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.cache.texture.AutoGlowingTexture;
import software.bernie.geckolib.core.animatable.GeoAnimatable;
import software.bernie.geckolib.renderer.GeoRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

import java.util.function.Function;

/**
 * La capa de lo que brilla (glowmask) dibujando las dos caras: la de GeckoLib quita las caras de atras y en las mallas
 * (FabricaMallas) dejaba huecos negros donde iba el brillo. Usa la misma textura de brillo que arma GeckoLib.
 */
public class CapaBrillo<T extends GeoAnimatable> extends AutoGlowingGeoLayer<T> {
    public CapaBrillo(GeoRenderer<T> renderer) {
        super(renderer);
    }

    @Override
    protected RenderType getRenderType(T animatable) {
        ResourceLocation base = getTextureResource(animatable);
        AutoGlowingTexture.getRenderType(base);                  // que GeckoLib arme la textura de brillo (y la base sin ella)
        ResourceLocation brillo = new ResourceLocation(base.getNamespace(), base.getPath().replace(".png", "_glowmask.png"));
        return Tipos.BRILLO.apply(brillo);
    }

    /** El tipo de dibujo que brilla (las dos caras, translucido) para cualquier textura de brillo. */
    public static RenderType tipo(ResourceLocation brillo) {
        return Tipos.BRILLO.apply(brillo);
    }

    /** Solo para llegar a las piezas protegidas de RenderType. */
    private static final class Tipos extends RenderType {
        static final Function<ResourceLocation, RenderType> BRILLO = Util.memoize(t -> create("mipack_brillo",
                DefaultVertexFormat.NEW_ENTITY, VertexFormat.Mode.QUADS, 256, false, true,
                CompositeState.builder()
                        .setShaderState(RENDERTYPE_ENTITY_TRANSLUCENT_EMISSIVE_SHADER)
                        .setTextureState(new TextureStateShard(t, false, false))
                        .setTransparencyState(TRANSLUCENT_TRANSPARENCY)
                        .setCullState(NO_CULL)
                        .setWriteMaskState(COLOR_DEPTH_WRITE)
                        .setOverlayState(OVERLAY)
                        .createCompositeState(false)));

        private Tipos(String n, VertexFormat f, VertexFormat.Mode m, int b, boolean c, boolean s, Runnable a, Runnable d) {
            super(n, f, m, b, c, s, a, d);
        }
    }
}
