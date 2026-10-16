package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.EfectosKhaset;
import com.mipack.khaset.CristalSacrificio;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.PosesKhaset;
import com.mipack.khaset.ParticulasKhaset;
import com.mipack.khaset.RedKhaset;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.client.event.MovementInputUpdateEvent;
import net.minecraftforge.client.event.RenderPlayerEvent;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Quaternionf;

import java.util.HashMap;
import java.util.Map;

/**
 * Las poses del jugador en la pelea con Khaset (todos las ven, ver RedKhaset):
 * <ul>
 * <li>AGARRADO: en la mano de Khaset, colgando: patalea y forcejea con los brazos arriba.</li>
 * <li>ALTAR: acostado de espaldas en la piedra del sacrificio, con los brazos abiertos.</li>
 * <li>DERRIBADO: de rodillas, con una mano en el piso y la cabeza baja (el corte de piernas, el desangrado III).</li>
 * <li>ATURDIDO: se tapa los oidos y sacude la cabeza (el silbato).</li>
 * <li>HERIDO: desangrado II: se agarra el costado.</li>
 * </ul>
 * Tambien: no moverse ni pegar si esta derribado o aturdido, la camara que se mece desorientado y las gotas de sangre.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class PosesJugador {
    public enum Pose { NINGUNA, AGARRADO, ALTAR, DERRIBADO, ATURDIDO, HERIDO }

    private record Estado(long derribado, long aturdido, long desorientado, int desangrado) {
    }

    private static final Map<Integer, Estado> ESTADOS = new HashMap<>();
    /** Para las fotos de prueba: una pose fija para una entidad. */
    public static final Map<Integer, Pose> FORZADAS = new HashMap<>();

    private PosesJugador() {
    }

    public static void recibir(RedKhaset.Estado e) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null)
            return;
        long t = mc.level.getGameTime();
        ESTADOS.put(e.id(), new Estado(t + e.derribado(), t + e.aturdido(), t + e.desorientado(), e.desangrado()));
    }

    private static Estado estado(Player p) {
        if (p == Minecraft.getInstance().player)                  // el jugador propio sabe sus efectos
            return new Estado(hasta(p, EfectosKhaset.DERRIBADO.get()), hasta(p, EfectosKhaset.ATURDIDO.get()),
                    hasta(p, EfectosKhaset.DESORIENTADO.get()), nivel(p));
        return ESTADOS.get(p.getId());
    }

    private static long hasta(Player p, net.minecraft.world.effect.MobEffect e) {
        MobEffectInstance i = p.getEffect(e);
        return i == null ? 0 : p.level().getGameTime() + i.getDuration();
    }

    private static int nivel(Player p) {
        MobEffectInstance i = p.getEffect(EfectosKhaset.DESANGRADO.get());
        return i == null ? 0 : i.getAmplifier() + 1;
    }

    public static Pose pose(Player p) {
        Pose f = FORZADAS.get(p.getId());
        if (f != null)
            return f;
        if (p.getVehicle() instanceof KhasetEntity k)
            return k.presaEnAltar(p) ? Pose.ALTAR : Pose.AGARRADO;
        Estado e = estado(p);
        if (e == null)
            return Pose.NINGUNA;
        long t = p.level().getGameTime();
        if (e.derribado > t)
            return Pose.DERRIBADO;
        if (e.aturdido > t)
            return Pose.ATURDIDO;
        if (e.desangrado >= 2)
            return Pose.HERIDO;
        return Pose.NINGUNA;
    }

    // ------------------------------------------------------------------ el modelo con las poses

    /** El modelo del jugador de siempre, con la pose de la pelea encima de lo que haga vanilla. */
    public static final class Modelo extends PlayerModel<AbstractClientPlayer> {
        public Modelo(ModelPart raiz, boolean delgado) {
            super(raiz, delgado);
        }

        @Override
        public void setupAnim(AbstractClientPlayer p, float paso, float cuanto, float edad, float cabezaY, float cabezaX) {
            super.setupAnim(p, paso, cuanto, edad, cabezaY, cabezaX);
            Pose pose = pose(p);
            if (pose == Pose.NINGUNA)
                return;
            float t = edad;
            switch (pose) {
                case AGARRADO -> {
                    this.rightArm.xRot = -2.7f + 0.35f * Mth.sin(t * 0.45f);
                    this.leftArm.xRot = -2.7f + 0.35f * Mth.sin(t * 0.45f + 2f);
                    this.rightArm.zRot = -0.25f;
                    this.leftArm.zRot = 0.25f;
                    this.rightLeg.xRot = 0.7f * Mth.sin(t * 0.6f);
                    this.leftLeg.xRot = -0.7f * Mth.sin(t * 0.6f);
                    this.head.xRot = 0.5f;
                }
                case ALTAR -> {
                    this.rightArm.xRot = 0f;
                    this.leftArm.xRot = 0f;
                    this.rightArm.zRot = 1.35f + 0.05f * Mth.sin(t * 0.3f);
                    this.leftArm.zRot = -1.35f - 0.05f * Mth.sin(t * 0.3f);
                    this.rightLeg.xRot = 0f;
                    this.leftLeg.xRot = 0f;
                    this.rightLeg.zRot = 0.15f;
                    this.leftLeg.zRot = -0.15f;
                    this.head.xRot = -0.3f;
                    this.head.yRot = 0.4f * Mth.sin(t * 0.25f);
                }
                case DERRIBADO -> {
                    this.rightLeg.xRot = 1.25f;
                    this.leftLeg.xRot = 1.25f;
                    this.rightLeg.yRot = 0.1f;
                    this.leftLeg.yRot = -0.1f;
                    this.rightArm.xRot = -0.55f;
                    this.rightArm.zRot = 0.1f;
                    this.leftArm.xRot = -0.9f;
                    this.leftArm.yRot = 0.6f;
                    this.leftArm.zRot = 0.3f;
                    this.head.xRot = 0.55f;
                    this.body.xRot = 0.25f;
                }
                case ATURDIDO -> {
                    this.rightArm.xRot = -2.55f;
                    this.leftArm.xRot = -2.55f;
                    this.rightArm.zRot = -0.5f;
                    this.leftArm.zRot = 0.5f;
                    this.head.yRot = 0.35f * Mth.sin(t * 1.3f);
                    this.head.xRot = 0.15f;
                }
                case HERIDO -> {
                    this.leftArm.xRot = -0.9f;
                    this.leftArm.yRot = 0.6f;
                    this.leftArm.zRot = 0.3f;
                    this.head.xRot = Math.max(this.head.xRot, 0.25f);
                }
                default -> {
                }
            }
            this.hat.copyFrom(this.head);
            this.jacket.copyFrom(this.body);
            this.leftSleeve.copyFrom(this.leftArm);
            this.rightSleeve.copyFrom(this.rightArm);
            this.leftPants.copyFrom(this.leftLeg);
            this.rightPants.copyFrom(this.rightLeg);
        }
    }

    // ------------------------------------------------------------------ el cuerpo entero: de rodillas, acostado

    @SubscribeEvent
    public static void antes(RenderPlayerEvent.Pre evento) {
        Player p = evento.getEntity();
        Pose pose = pose(p);
        var ps = evento.getPoseStack();
        ps.pushPose();
        if (pose == Pose.DERRIBADO) {
            ps.translate(0, -0.42, 0);
        } else if (pose == Pose.ALTAR) {
            float eje = ejeDelAltar(p);                          // a lo largo de la piedra (derecho, no chueco)
            p.yBodyRot = eje;
            p.yBodyRotO = eje;
            p.yHeadRot = eje;
            p.yHeadRotO = eje;
            Vec3 f = Vec3.directionFromRotation(0, eje);
            Vec3 derecha = new Vec3(-f.z, 0, f.x);
            // al acostarlo la cabeza queda hacia +f desde los pies: los pies van 0.9 hacia -f y asi el cuerpo queda
            // centrado en la piedra
            ps.translate(-f.x * 0.9, 0.35, -f.z * 0.9);
            ps.mulPose(new Quaternionf().rotationAxis((float) Math.toRadians(-90), (float) derecha.x, 0f, (float) derecha.z));
        } else if (pose == Pose.AGARRADO) {
            ps.mulPose(Axis.ZP.rotationDegrees(6f * Mth.sin((p.tickCount + evento.getPartialTick()) * 0.3f)));
        }
    }

    /** El giro del cuerpo acostado: a lo largo del lado largo de la piedra del sacrificio (su eje x). */
    static float ejeDelAltar(Player p) {
        Float giro = null;
        if (p.getVehicle() instanceof KhasetEntity k)
            giro = k.giroDelAltar();
        else
            for (CristalSacrificio c : p.level().getEntitiesOfClass(CristalSacrificio.class, p.getBoundingBox().inflate(2.5)))
                giro = c.getYRot();
        if (giro == null)
            return p.getYRot();
        Vec3 largo = PosesKhaset.rotar(giro, new Vec3(1, 0, 0));
        return (float) Math.toDegrees(Math.atan2(-largo.x, largo.z));
    }

    @SubscribeEvent
    public static void despues(RenderPlayerEvent.Post evento) {
        evento.getPoseStack().popPose();
    }

    // ------------------------------------------------------------------ control, camara y gotas

    @SubscribeEvent
    public static void moverse(MovementInputUpdateEvent evento) {
        if (evento.getEntity() instanceof LocalPlayer p && EfectosKhaset.sinControl(p)) {
            var in = evento.getInput();
            in.forwardImpulse = 0;
            in.leftImpulse = 0;
            in.up = in.down = in.left = in.right = false;
            in.jumping = false;
            in.shiftKeyDown = false;
        }
    }

    @SubscribeEvent
    public static void teclas(InputEvent.InteractionKeyMappingTriggered evento) {
        LocalPlayer p = Minecraft.getInstance().player;
        if (p != null && EfectosKhaset.sinControl(p) && (evento.isAttack() || evento.isUseItem())) {
            evento.setCanceled(true);
            evento.setSwingHand(false);
        }
    }

    @SubscribeEvent
    public static void camara(ViewportEvent.ComputeCameraAngles evento) {
        LocalPlayer p = Minecraft.getInstance().player;
        if (p == null)
            return;
        MobEffectInstance d = p.getEffect(EfectosKhaset.DESORIENTADO.get());
        if (d == null)
            return;
        float f = Math.min(1f, d.getDuration() / 20f);
        float t = (float) (p.tickCount + evento.getPartialTick());
        evento.setRoll(evento.getRoll() + 11f * f * Mth.sin(t * 0.13f));
        evento.setYaw(evento.getYaw() + 6f * f * Mth.sin(t * 0.07f));
        evento.setPitch(evento.getPitch() + 3f * f * Mth.sin(t * 0.11f));
    }

    @SubscribeEvent
    public static void fov(ViewportEvent.ComputeFov evento) {
        LocalPlayer p = Minecraft.getInstance().player;
        if (p != null && p.hasEffect(EfectosKhaset.DESORIENTADO.get()))
            evento.setFOV(evento.getFOV() * (1.0 + 0.06 * Math.sin((p.tickCount + evento.getPartialTick()) * 0.2)));
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        Minecraft mc = Minecraft.getInstance();
        if (evento.phase != TickEvent.Phase.END || mc.level == null || mc.isPaused())
            return;
        for (Player p : mc.level.players()) {
            Estado e = estado(p);
            if (e == null || e.desangrado <= 0)
                continue;
            int cada = e.desangrado >= 2 ? 6 : 12;
            if ((p.tickCount + p.getId()) % cada == 0)
                mc.level.addParticle(ParticulasKhaset.SANGRE.get(), p.getX() + (p.getRandom().nextDouble() - 0.5) * 0.5,
                        p.getY() + 0.6 + p.getRandom().nextDouble() * 0.6, p.getZ() + (p.getRandom().nextDouble() - 0.5) * 0.5,
                        0, 0, 0);
        }
        if (mc.level.getGameTime() % 200 == 0)
            ESTADOS.keySet().removeIf(id -> mc.level.getEntity(id) == null);
    }
}
