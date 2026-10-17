package com.mipack.bruma;

import com.mipack.objetos.ObjetosMipack;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

import java.util.Optional;
import java.util.UUID;

/**
 * El doble de un jugador poseido: su misma piel pero oscura y con ojos de mura, con su espada y su armadura (copias que
 * no se sueltan). Pelea contra los demas jugadores. Solo la espada de vitae le hace algo: lo deshace y regresa al
 * jugador ahi mismo con la cordura llena. Si La Bruma muere o pasan 2 minutos, el jugador regresa solo.
 */
public class Poseido extends Monster {
    private static final EntityDataAccessor<Optional<UUID>> DUENO = SynchedEntityData.defineId(Poseido.class, EntityDataSerializers.OPTIONAL_UUID);
    private static final int MAX_TICKS = 20 * 120;
    private Player jugador;

    public Poseido(EntityType<? extends Poseido> tipo, Level nivel) {
        super(tipo, nivel);
        this.xpReward = 0;
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 100).add(Attributes.ATTACK_DAMAGE, 6)
                .add(Attributes.MOVEMENT_SPEED, 0.32).add(Attributes.FOLLOW_RANGE, 40);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DUENO, Optional.empty());
    }

    public UUID dueno() {
        return this.entityData.get(DUENO).orElse(null);
    }

    /** Toma la forma de 'p': su nombre, su arma y su armadura. */
    public void de(Player p) {
        this.jugador = p;
        this.entityData.set(DUENO, Optional.of(p.getUUID()));
        this.setCustomName(p.getDisplayName());
        for (EquipmentSlot s : EquipmentSlot.values()) {
            this.setItemSlot(s, p.getItemBySlot(s).copy());
            this.setDropChance(s, 0f);
        }
        this.setPersistenceRequired();
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, true));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                p -> !p.getUUID().equals(dueno()) && !Cordura.poseido((Player) p)));
    }

    private Player jugador() {
        if (this.jugador != null && !this.jugador.isRemoved())
            return this.jugador;
        UUID u = dueno();
        return u == null ? null : this.level().getPlayerByUUID(u);
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level().isClientSide) {
            if (this.random.nextInt(4) == 0)
                this.level().addParticle(ParticleTypes.SMOKE, this.getRandomX(0.5), this.getRandomY(), this.getRandomZ(0.5), 0, 0.02, 0);
            return;
        }
        if (this.tickCount % 20 != 0)
            return;
        Player p = jugador();
        if (p == null || !Cordura.poseido(p)) {
            this.discard();
            return;
        }
        if (this.tickCount > MAX_TICKS || this.level().getEntitiesOfClass(BrumaEntity.class, this.getBoundingBox().inflate(128),
                BrumaEntity::isAlive).isEmpty())
            curar(false);
    }

    /** Se deshace y regresa al jugador (con la vitae, donde estaba el doble; si no, donde se quedo). */
    public void curar(boolean aqui) {
        Player p = jugador();
        if (p != null)
            Cordura.liberar(p, aqui ? this.position() : null);
        if (this.level() instanceof ServerLevel sl)
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, this.getX(), this.getY() + 1, this.getZ(), 30, 0.3, 0.8, 0.3, 0.03);
        this.discard();
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (fuente.is(DamageTypeTags.BYPASSES_INVULNERABILITY))
            return super.hurt(fuente, cantidad);
        if (this.level().isClientSide)
            return false;
        if (fuente.getEntity() instanceof Player p && fuente.getDirectEntity() == p && p.getMainHandItem().is(ObjetosMipack.ESPADA_VITAE.get())) {
            com.mipack.arena.Mvp.sumar(com.mipack.arena.Mvp.jefeCerca(this), p, com.mipack.arena.Mvp.Cat.CURADOS, 1);
            curar(true);
            return true;
        }
        if (fuente.getEntity() != null) {                     // lo demas solo lo empuja
            this.knockback(0.5, fuente.getEntity().getX() - this.getX(), fuente.getEntity().getZ() - this.getZ());
            this.playSound(SoundEvents.SOUL_ESCAPE, 1.0f, 0.7f);
        }
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double d) {
        return false;
    }

    @Override
    public boolean shouldDropExperience() {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (dueno() != null)
            tag.putUUID("Dueno", dueno());
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("Dueno"))
            this.entityData.set(DUENO, Optional.of(tag.getUUID("Dueno")));
    }
}
