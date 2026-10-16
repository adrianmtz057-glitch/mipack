package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * La Xiuhcoatl, la serpiente de fuego que invoca Khaset (de dos a seis a la vez): sale del piso, persigue a un
 * jugador reptando mas rapido de lo que se corre (gira menos: de lado se esquiva), muerde y quema, y deja un rastro de
 * fuego. A los 13 s se deshace en brasas. Se le puede matar (60 de vida). Lo de Khaset no le hace nada (ni el veneno
 * de sus dardos).
 */
public class Xiuhcoatl extends Monster implements GeoEntity {
    public static final float ESCALA = 2.0f;
    private static final int T_SURGIR = 20, T_MORDER = 12, T_DESHACER = 20, VIDA = 260;
    private static final float VELOCIDAD = 0.4f, GIRO = 7.5f, DANO_MORDIDA = 10f, DANO_CUERPO = 5f;
    /** Ticks de retraso entre un tramo y el siguiente (un tramo mide 1 bloque y avanza 0.4 por tick). */
    public static final int RETRASO = 3;

    private static final RawAnimation A_SURGIR = RawAnimation.begin().thenPlayAndHold("animation.xiuhcoatl.surgir");
    private static final RawAnimation A_REPTAR = RawAnimation.begin().thenLoop("animation.xiuhcoatl.reptar");
    private static final RawAnimation A_MORDER = RawAnimation.begin().thenPlay("animation.xiuhcoatl.morder");
    private static final RawAnimation A_DESHACER = RawAnimation.begin().thenPlayAndHold("animation.xiuhcoatl.deshacer");
    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(Xiuhcoatl.class, EntityDataSerializers.INT);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private UUID dueno, presa;
    private int ticksEnEstado;
    private final ArrayDeque<Vec3> camino = new ArrayDeque<>();
    private final Map<UUID, Integer> quemados = new HashMap<>();
    /** Para el cliente: hacia donde miraba en los ultimos ticks (los tramos siguen el camino de la cabeza). */
    public final float[] giros = new float[64];

    public Xiuhcoatl(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.setMaxUpStep(1.1f);
        this.xpReward = 20;
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 60.0).add(Attributes.ARMOR, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0).add(Attributes.MOVEMENT_SPEED, VELOCIDAD);
    }

    public void dueno(KhasetEntity k, LivingEntity objetivo) {
        this.dueno = k.getUUID();
        this.presa = objetivo == null ? null : objetivo.getUUID();
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, 0);
    }

    public int estado() {
        return this.entityData.get(ESTADO);
    }

    private void cambiar(int e) {
        this.entityData.set(ESTADO, e);
        this.ticksEnEstado = 0;
    }

    @Override
    protected void registerGoals() {
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide) {
            System.arraycopy(this.giros, 0, this.giros, 1, this.giros.length - 1);
            this.giros[0] = this.getYRot();
            if (estado() == 1 && this.tickCount % 2 == 0)
                this.level().addParticle(ParticleTypes.FLAME, this.getX(), this.getY() + 0.5, this.getZ(), 0, 0.03, 0);
        }
    }

    @Override
    protected void customServerAiStep() {
        this.ticksEnEstado++;
        this.quemados.replaceAll((k, v) -> v - 1);
        this.quemados.values().removeIf(v -> v <= 0);
        LivingEntity objetivo = buscarPresa();
        switch (estado()) {
            case 0 -> {                                           // surgir
                if (this.ticksEnEstado == 2 && this.level() instanceof ServerLevel sl)
                    sl.sendParticles(ParticleTypes.LAVA, this.getX(), this.getY() + 0.5, this.getZ(), 20, 1, 0.3, 1, 0.1);
                if (this.ticksEnEstado >= T_SURGIR)
                    cambiar(1);
            }
            case 1 -> {                                           // reptar
                if (objetivo != null) {
                    Vec3 d = objetivo.position().subtract(this.position());
                    float deseado = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
                    girar(this.getYRot() + Mth.clamp(Mth.wrapDegrees(deseado - this.getYRot()), -GIRO, GIRO));
                    if (d.horizontalDistance() < 2.6)
                        cambiar(2);
                }
                avanzar(VELOCIDAD);
                if (this.tickCount > VIDA)
                    cambiar(3);
            }
            case 2 -> {                                           // morder
                avanzar(VELOCIDAD * 0.4f);
                if (this.ticksEnEstado == 6) {
                    Vec3 boca = this.position().add(Vec3.directionFromRotation(0, this.getYRot()).scale(2.2)).add(0, 0.6, 0);
                    for (LivingEntity e : enemigos(boca, 1.8)) {
                        com.mipack.Golpes.pegar(e, this, DANO_MORDIDA, 60);
                        e.setSecondsOnFire(4);
                    }
                    this.playSound(SoundEvents.BLAZE_SHOOT, 1.5f, 0.6f);
                }
                if (this.ticksEnEstado >= T_MORDER)
                    cambiar(this.tickCount > VIDA ? 3 : 1);
            }
            case 3 -> {                                           // deshacerse
                if (this.level() instanceof ServerLevel sl && this.ticksEnEstado % 3 == 0)
                    sl.sendParticles(ParticulasKhaset.BRASA.get(), this.getX(), this.getY() + 0.5, this.getZ(), 10, 1.5, 0.3, 1.5, 0.05);
                if (this.ticksEnEstado >= T_DESHACER)
                    this.discard();
            }
            default -> {
            }
        }
        // el cuerpo quema y deja fuego
        this.camino.addFirst(this.position());
        while (this.camino.size() > RETRASO * 10)
            this.camino.removeLast();
        if (estado() == 1 || estado() == 2) {
            int i = 0;
            for (Vec3 p : this.camino) {
                if (i++ % RETRASO != 0)
                    continue;
                for (LivingEntity e : enemigos(p.add(0, 0.5, 0), 1.2))
                    if (!this.quemados.containsKey(e.getUUID())) {
                        com.mipack.Golpes.pegar(e, this, DANO_CUERPO, 0);
                        e.setSecondsOnFire(3);
                        this.quemados.put(e.getUUID(), 20);
                    }
                if (this.level() instanceof ServerLevel sl && this.tickCount % 4 == 0)
                    sl.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.3, p.z, 1, 0.3, 0.1, 0.3, 0.01);
            }
        }
    }

    private void girar(float yaw) {
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    private void avanzar(float v) {
        Vec3 d = Vec3.directionFromRotation(0, this.getYRot()).scale(v);
        Vec3 m = this.getDeltaMovement();
        this.setDeltaMovement(d.x, m.y, d.z);
    }

    @Override
    public void travel(Vec3 entrada) {
        if (this.isEffectiveAi()) {
            Vec3 m = this.getDeltaMovement();
            this.move(MoverType.SELF, m);
            double vy = this.onGround() ? 0 : (m.y - 0.08) * 0.98;
            this.setDeltaMovement(m.x * 0.0, vy, m.z * 0.0);
            this.calculateEntityAnimation(false);
        } else {
            super.travel(entrada);
        }
    }

    private LivingEntity buscarPresa() {
        if (this.presa != null && this.level() instanceof ServerLevel sl && sl.getEntity(this.presa) instanceof LivingEntity le
                && le.isAlive() && le.distanceToSqr(this) < 48 * 48)
            return le;
        KhasetEntity k = this.dueno != null && this.level() instanceof ServerLevel sl
                && sl.getEntity(this.dueno) instanceof KhasetEntity kk ? kk : null;
        LivingEntity mejor = null;
        double d = 40 * 40;
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(40),
                e -> k != null ? k.valido(e) : e instanceof net.minecraft.world.entity.player.Player p && !p.isCreative())) {
            double dd = e.distanceToSqr(this);
            if (dd < d) {
                d = dd;
                mejor = e;
            }
        }
        this.presa = mejor == null ? null : mejor.getUUID();
        return mejor;
    }

    private List<LivingEntity> enemigos(Vec3 p, double r) {
        KhasetEntity k = this.dueno != null && this.level() instanceof ServerLevel sl
                && sl.getEntity(this.dueno) instanceof KhasetEntity kk ? kk : null;
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(r)))
            if (e != this && !(e instanceof KhasetEntity) && !(e instanceof Xiuhcoatl) && !(e instanceof GuerreroCalavera)
                    && (k != null ? k.valido(e) : e instanceof net.minecraft.world.entity.player.Player pl && !pl.isCreative()))
                out.add(e);
        return out;
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (fuente.getEntity() instanceof KhasetEntity || fuente.getEntity() instanceof GuerreroCalavera
                || fuente.getDirectEntity() instanceof DardoAtlatl || fuente.is(EfectosKhaset.CALOR))
            return false;
        return super.hurt(fuente, cantidad);
    }

    /** El veneno de los dardos de Khaset no le hace nada. */
    @Override
    public boolean canBeAffected(net.minecraft.world.effect.MobEffectInstance efecto) {
        return efecto.getEffect() != net.minecraft.world.effect.MobEffects.POISON && super.canBeAffected(efecto);
    }

    @Override
    public boolean fireImmune() {
        return true;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double d) {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return this.getBoundingBox().inflate(12, 2, 12);
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
        controladores.add(new AnimationController<>(this, "principal", 3, this::animar));
    }

    private PlayState animar(AnimationState<Xiuhcoatl> estado) {
        return estado.setAndContinue(switch (estado()) {
            case 0 -> A_SURGIR;
            case 2 -> A_MORDER;
            case 3 -> A_DESHACER;
            default -> A_REPTAR;
        });
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
