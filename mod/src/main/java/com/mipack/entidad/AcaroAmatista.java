package com.mipack.entidad;

import com.mipack.Mipack;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Endermite;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import org.joml.Vector3f;

import java.util.UUID;

/**
 * Los acaros de amatista: salen de la bruma de Crackatos en su fase 2. Como endermites pero de cristal, mas grandes,
 * mucho mas rapidos y con mordida fuerte. Mueren cuando muere Crackatos (o si se alejan mucho de el).
 */
public class AcaroAmatista extends Endermite {
    private UUID jefe;

    public AcaroAmatista(EntityType<? extends Endermite> tipo, Level nivel) {
        super(tipo, nivel);
        this.xpReward = 2;
    }

    public static AttributeSupplier.Builder atributos() {
        return Endermite.createAttributes().add(Attributes.MAX_HEALTH, 12.0).add(Attributes.MOVEMENT_SPEED, 0.42)
                .add(Attributes.ATTACK_DAMAGE, 6.0).add(Attributes.FOLLOW_RANGE, 48.0).add(Attributes.ARMOR, 4.0);
    }

    public void deJefe(CrackatosEntity c) {
        this.jefe = c.getUUID();
        this.setPersistenceRequired();
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(1, new FloatGoal(this));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, 5, false, false,
                e -> e instanceof Player p && !p.isCreative() && !p.isSpectator()));
        if (Mipack.PRUEBA)
            this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, net.minecraft.world.entity.Mob.class, 5,
                    false, false, e -> !(e instanceof CrackatosEntity) && !(e instanceof AcaroAmatista) && !(e instanceof com.mipack.khaset.KhasetEntity)
                            && !(e instanceof com.mipack.khaset.Xiuhcoatl) && !(e instanceof com.mipack.khaset.GuerreroCalavera)));
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level() instanceof ServerLevel sl) {
            if (this.tickCount % 40 == 0 && this.jefe != null) {
                Entity j = sl.getEntity(this.jefe);
                if (!(j instanceof CrackatosEntity c) || !c.isAlive() || c.distanceToSqr(this) > 120 * 120)
                    deshacer(sl);
            }
        } else if (this.tickCount % 3 == 0) {
            this.level().addParticle(new DustParticleOptions(new Vector3f(0.7f, 0.4f, 1.0f), 0.8f),
                    this.getX(), this.getY() + 0.3, this.getZ(), 0, 0, 0);
        }
    }

    private boolean jefeVivo() {
        return this.jefe != null && this.level() instanceof ServerLevel sl && sl.getEntity(this.jefe) instanceof CrackatosEntity c
                && c.isAlive();
    }

    /** Se rompe en polvo de amatista. */
    public void deshacer(ServerLevel sl) {
        sl.sendParticles(new DustParticleOptions(new Vector3f(0.62f, 0.32f, 0.95f), 1.5f), this.getX(), this.getY() + 0.3,
                this.getZ(), 12, 0.3, 0.2, 0.3, 0.0);
        this.playSound(SoundEvents.AMETHYST_CLUSTER_BREAK, 0.8f, 1.4f);
        this.discard();
    }

    @Override
    public boolean doHurtTarget(Entity e) {
        boolean pego = super.doHurtTarget(e);
        if (pego && e instanceof LivingEntity le && this.random.nextInt(4) == 0 && jefeVivo())
            EfectosCrackatos.clavar(le);                          // a veces deja una esquirla (si Crackatos sigue vivo)
        return pego;
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (fuente.getEntity() instanceof CrackatosEntity || fuente.getDirectEntity() instanceof PuaCayendo)
            return false;
        return super.hurt(fuente, cantidad);
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (this.jefe != null)
            tag.putUUID("Jefe", this.jefe);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Jefe"))
            this.jefe = tag.getUUID("Jefe");
    }
}
