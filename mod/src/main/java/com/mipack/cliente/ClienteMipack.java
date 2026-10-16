package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.ParticulasKhaset;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.world.level.dimension.BuiltinDimensionTypes;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterDimensionSpecialEffectsEvent;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.client.event.RegisterParticleProvidersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;

/** Lo que solo existe en el cliente: como se dibuja cada entidad, las particulas, la pantalla y el cielo. */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClienteMipack {
    private ClienteMipack() {
    }

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers evento) {
        evento.registerEntityRenderer(Mipack.CRACKATOS.get(), CrackatosRenderer::new);
        evento.registerEntityRenderer(Mipack.PUA.get(), PuaRenderer::new);
        evento.registerEntityRenderer(Mipack.ACARO.get(), AcaroRenderer::new);
        evento.registerEntityRenderer(Mipack.GUERRERO.get(), RenderGuerrero::new);
        evento.registerEntityRenderer(Mipack.KHASET.get(), RenderersKhaset.Khaset::new);
        evento.registerEntityRenderer(Mipack.CRISTAL.get(), RenderersKhaset.Cristal::new);
        evento.registerEntityRenderer(Mipack.XIUHCOATL.get(), RenderersKhaset.Serpiente::new);
        evento.registerEntityRenderer(Mipack.DARDO.get(), RenderersKhaset.Dardo::new);
        evento.registerEntityRenderer(Mipack.AVISO.get(), RenderersKhaset.Aviso::new);
        for (var e : com.mipack.titanes.Titanes.entidades().entrySet()) {
            var tipo = com.mipack.titanes.Titanes.tipo(e.getKey());
            evento.registerEntityRenderer(e.getValue().get(), c -> new RenderTitan(c, tipo));
        }
    }

    @SubscribeEvent
    public static void modelos(EntityRenderersEvent.RegisterLayerDefinitions evento) {
        evento.registerLayerDefinition(RenderGuerrero.CAPA, RenderGuerrero::capa);
    }

    /** El jugador con las poses de la pelea con Khaset (agarrado, en el altar, de rodillas, tapandose los oidos). */
    @SubscribeEvent
    public static void capas(EntityRenderersEvent.AddLayers evento) {
        for (String piel : evento.getSkins()) {
            LivingEntityRenderer<?, ?> r = evento.getSkin(piel);
            if (r == null)
                continue;
            boolean delgado = piel.equals("slim");
            PosesJugador.Modelo m = new PosesJugador.Modelo(
                    evento.getEntityModels().bakeLayer(delgado ? ModelLayers.PLAYER_SLIM : ModelLayers.PLAYER), delgado);
            ObfuscationReflectionHelper.setPrivateValue(LivingEntityRenderer.class, r, m, "f_115290_");
        }
    }

    @SubscribeEvent
    public static void particulas(RegisterParticleProvidersEvent evento) {
        evento.registerSpriteSet(ParticulasKhaset.VENENO.get(), s -> new ParticulasCliente.Proveedor(s, ParticulasCliente.Tipo.VENENO));
        evento.registerSpriteSet(ParticulasKhaset.SANGRE.get(), s -> new ParticulasCliente.Proveedor(s, ParticulasCliente.Tipo.SANGRE));
        evento.registerSpriteSet(ParticulasKhaset.BRASA.get(), s -> new ParticulasCliente.Proveedor(s, ParticulasCliente.Tipo.BRASA));
        evento.registerSpriteSet(ParticulasKhaset.PLUMA.get(), s -> new ParticulasCliente.Proveedor(s, ParticulasCliente.Tipo.PLUMA));
        evento.registerSpriteSet(ParticulasKhaset.CENIZA.get(), s -> new ParticulasCliente.Proveedor(s, ParticulasCliente.Tipo.CENIZA));
    }

    @SubscribeEvent
    public static void pantalla(RegisterGuiOverlaysEvent evento) {
        evento.registerAboveAll("khaset", new PantallaKhaset());
        evento.registerAboveAll("zafarse", new BarraZafarse());
    }

    /** El cielo de Velkia en el mundo normal (el Nether y el End no cambian). */
    @SubscribeEvent
    public static void cielos(RegisterDimensionSpecialEffectsEvent evento) {
        evento.register(BuiltinDimensionTypes.OVERWORLD_EFFECTS, new CieloVelkia());
    }
}
