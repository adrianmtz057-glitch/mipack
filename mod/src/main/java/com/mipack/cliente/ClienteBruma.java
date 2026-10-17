package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.bruma.Cordura;
import com.mipack.bruma.Poseido;
import com.mipack.bruma.RedBruma;
import com.mipack.objetos.EfectosObjetos;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.resources.DefaultPlayerSkin;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.client.event.RegisterGuiOverlaysEvent;
import net.minecraftforge.client.event.RenderPlayerEvent;
import net.minecraftforge.client.gui.overlay.IGuiOverlay;
import net.minecraftforge.client.gui.overlay.VanillaGuiOverlay;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** La cordura en pantalla, la camara del poseido, que no se le vea, y como se dibuja su doble. */
public final class ClienteBruma {
    private static float cordura = Cordura.MAX;
    private static boolean pelea, camaraCambiada;
    private static final Set<UUID> POSEIDOS = new HashSet<>();

    private ClienteBruma() {
    }

    public static void recibir(RedBruma.Estado e) {
        cordura = e.cordura();
        pelea = e.pelea();
    }

    @Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Registro {
        private Registro() {
        }

        @SubscribeEvent
        public static void renderers(EntityRenderersEvent.RegisterRenderers e) {
            e.registerEntityRenderer(Mipack.POSEIDO.get(), RenderPoseido::new);
        }

        @SubscribeEvent
        public static void pantalla(RegisterGuiOverlaysEvent e) {
            e.registerAbove(VanillaGuiOverlay.PLAYER_HEALTH.id(), "cordura", new Barra());
        }
    }

    @Mod.EventBusSubscriber(modid = Mipack.MODID, value = Dist.CLIENT)
    public static final class Juego {
        private Juego() {
        }

        @SubscribeEvent
        public static void tick(TickEvent.ClientTickEvent e) {
            Minecraft mc = Minecraft.getInstance();
            if (e.phase != TickEvent.Phase.END || mc.level == null || mc.player == null)
                return;
            POSEIDOS.clear();
            for (Entity x : mc.level.entitiesForRendering())
                if (x instanceof Poseido d && d.dueno() != null)
                    POSEIDOS.add(d.dueno());
            boolean yo = mc.player.hasEffect(EfectosObjetos.POSEIDO.get());
            if (yo && mc.options.getCameraType() == CameraType.FIRST_PERSON) {
                mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);   // te ves desde fuera mientras tu doble pelea
                camaraCambiada = true;
            } else if (!yo && camaraCambiada) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                camaraCambiada = false;
            }
        }

        /** El poseido no se ve (ni su armadura): su doble es el que anda. */
        @SubscribeEvent
        public static void esconder(RenderPlayerEvent.Pre e) {
            if (POSEIDOS.contains(e.getEntity().getUUID()))
                e.setCanceled(true);
        }
    }

    /** La barra de cordura (un ojo morado y la barra), arriba de los corazones, solo en la pelea con La Bruma. */
    static final class Barra implements IGuiOverlay {
        @Override
        public void render(net.minecraftforge.client.gui.overlay.ForgeGui gui, net.minecraft.client.gui.GuiGraphics g, float parcial, int ancho, int alto) {
            Minecraft mc = Minecraft.getInstance();
            if (!pelea || mc.options.hideGui || mc.player == null || mc.player.isCreative() || mc.player.isSpectator())
                return;
            int x = ancho / 2 - 91, y = alto - 39 - 22;
            float f = cordura / Cordura.MAX;
            boolean late = f < 0.25f && (mc.player.tickCount / 5) % 2 == 0;
            // el ojo
            g.fill(x, y + 1, x + 9, y + 6, 0xFF1A0F22);
            g.fill(x + 1, y, x + 8, y + 7, 0xFF1A0F22);
            g.fill(x + 1, y + 2, x + 8, y + 5, 0xFFD9C7E8);
            g.fill(x + 3, y + 1, x + 6, y + 6, late ? 0xFFE04060 : 0xFF8A3CC8);
            g.fill(x + 4, y + 2, x + 5, y + 5, 0xFF0A050E);
            // la barra
            int bx = x + 11, largo = 70;
            g.fill(bx - 1, y + 1, bx + largo + 1, y + 7, 0xFF0A050E);
            g.fill(bx, y + 2, bx + largo, y + 6, 0xFF2A1A35);
            g.fill(bx, y + 2, bx + Math.round(largo * f), y + 6, late ? 0xFFC0305A : 0xFF9A4CE0);
            g.fill(bx, y + 2, bx + Math.round(largo * f), y + 3, 0x55FFFFFF);
        }
    }

    /** El doble: la piel del jugador, oscurecida, con ojos de mura que brillan, y su armadura. */
    public static final class RenderPoseido extends HumanoidMobRenderer<Poseido, PlayerModel<Poseido>> {
        private static final ResourceLocation SOMBRA = new ResourceLocation(Mipack.MODID, "textures/entity/poseido_sombra.png");
        private static final ResourceLocation OJOS = new ResourceLocation(Mipack.MODID, "textures/entity/poseido_ojos.png");

        public RenderPoseido(EntityRendererProvider.Context c) {
            super(c, new PlayerModel<>(c.bakeLayer(ModelLayers.PLAYER), false), 0.5f);
            this.addLayer(new HumanoidArmorLayer<>(this, new HumanoidModel<>(c.bakeLayer(ModelLayers.PLAYER_INNER_ARMOR)),
                    new HumanoidModel<>(c.bakeLayer(ModelLayers.PLAYER_OUTER_ARMOR)), c.getModelManager()));
            this.addLayer(new Sombra(this));
            this.addLayer(new EyesLayer<>(this) {
                @Override
                public RenderType renderType() {
                    return RenderType.eyes(OJOS);
                }
            });
        }

        @Override
        public ResourceLocation getTextureLocation(Poseido d) {
            UUID u = d.dueno();
            if (u == null)
                return DefaultPlayerSkin.getDefaultSkin();
            var con = Minecraft.getInstance().getConnection();
            PlayerInfo info = con == null ? null : con.getPlayerInfo(u);
            return info != null ? info.getSkinLocation() : DefaultPlayerSkin.getDefaultSkin(u);
        }

        /** Una capa negra-morada medio transparente encima de la piel (sin tapar las capas de afuera). */
        static final class Sombra extends RenderLayer<Poseido, PlayerModel<Poseido>> {
            Sombra(RenderLayerParent<Poseido, PlayerModel<Poseido>> padre) {
                super(padre);
            }

            @Override
            public void render(PoseStack ps, MultiBufferSource buf, int luz, Poseido d, float a, float b, float parcial, float edad, float c, float e) {
                VertexConsumer v = buf.getBuffer(RenderType.entityTranslucent(SOMBRA));
                this.getParentModel().renderToBuffer(ps, v, luz, LivingEntityRenderer.getOverlayCoords(d, 0f), 1f, 1f, 1f, 0.78f);
            }
        }
    }
}
