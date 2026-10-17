package com.mipack.bruma;

import com.mipack.Golpes;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/**
 * Un clon de La Bruma: mas chico, oscuro y mucho mas debil. Flota hacia los jugadores y les tira zarpazos. Cada clon que
 * muere le quita vida a La Bruma; cuando caen todos ella baja y queda vulnerable.
 */
public class ClonBruma extends Monster implements GeoEntity {
    public static final float ESCALA = 1.7f;
    private static final RawAnimation AVANZAR = RawAnimation.begin().thenLoop("animation.bruma.avanzar");
    private static final RawAnimation ZARPAZO = RawAnimation.begin().thenPlay("animation.bruma.zarpazo");
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private UUID duena;
    private int enfriar = 30;

    public ClonBruma(EntityType<? extends ClonBruma> tipo, Level nivel) {
        super(tipo, nivel);
        this.setNoGravity(true);
        this.xpReward = 2;
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 40).add(Attributes.ARMOR, 2)
                .add(Attributes.ATTACK_DAMAGE, 7).add(Attributes.MOVEMENT_SPEED, 0.3).add(Attributes.FOLLOW_RANGE, 48);
    }

    public void deLaBruma(BrumaEntity b) {
        this.duena = b == null ? null : b.getUUID();
        this.setPersistenceRequired();
    }

    @Override
    public void tick() {
        super.tick();
        this.noPhysics = false;
        if (this.level().isClientSide) {
            if (this.random.nextInt(3) == 0)
                this.level().addParticle(ParticleTypes.SMOKE, this.getRandomX(0.8), this.getRandomY(), this.getRandomZ(0.8), 0, 0.01, 0);
            return;
        }
        if (this.tickCount % 20 == 0 && this.duena != null && this.level() instanceof ServerLevel sl
                && !(sl.getEntity(this.duena) instanceof BrumaEntity b && b.isAlive())) {
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, this.getX(), this.getY() + 1, this.getZ(), 12, 0.4, 0.8, 0.4, 0.02);
            this.discard();
            return;
        }
        if (this.enfriar > 0)
            this.enfriar--;
        Player p = this.level().getNearestPlayer(this, 48);
        if (p == null || p.isCreative() || p.isSpectator()) {
            this.setDeltaMovement(this.getDeltaMovement().scale(0.8));
            return;
        }
        Vec3 hacia = p.position().add(0, 0.4, 0).subtract(this.position());
        double d = hacia.length();
        Vec3 v = d > 2.2 ? hacia.normalize().scale(0.28) : Vec3.ZERO;
        this.setDeltaMovement(this.getDeltaMovement().scale(0.6).add(v.scale(0.4)));
        this.move(net.minecraft.world.entity.MoverType.SELF, this.getDeltaMovement());
        float giro = (float) (Math.toDegrees(Math.atan2(hacia.z, hacia.x)) - 90.0);
        this.setYRot(giro);
        this.yBodyRot = giro;
        this.yHeadRot = giro;
        if (d < 3.2 && this.enfriar == 0) {
            this.enfriar = 30;
            this.triggerAnim("golpe", "zarpazo");
            this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 1.0f, 0.6f);
            Golpes.pegar(p, this, (float) this.getAttributeValue(Attributes.ATTACK_DAMAGE), 0);
        }
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (fuente.getEntity() instanceof BrumaEntity || fuente.getEntity() instanceof ClonBruma)
            return false;
        return super.hurt(fuente, cantidad);
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (this.level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, this.getX(), this.getY() + 1, this.getZ(), 20, 0.4, 0.8, 0.4, 0.04);
            if (this.duena != null && sl.getEntity(this.duena) instanceof BrumaEntity b)
                b.murioUnClon();
        }
    }

    @Override
    protected void tickDeath() {
        if (++this.deathTime >= 6 && !this.level().isClientSide())
            this.remove(RemovalReason.KILLED);
    }

    @Override
    public boolean causeFallDamage(float d, float m, DamageSource f) {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double d) {
        return false;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar c) {
        c.add(new AnimationController<>(this, "cuerpo", 4, s -> s.setAndContinue(AVANZAR)));
        c.add(new AnimationController<>(this, "golpe", 2, s -> PlayState.STOP).triggerableAnim("zarpazo", ZARPAZO));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (this.duena != null)
            tag.putUUID("Duena", this.duena);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.duena = tag.hasUUID("Duena") ? tag.getUUID("Duena") : null;
    }
}
