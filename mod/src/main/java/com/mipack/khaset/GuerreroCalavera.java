package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.MobType;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import javax.annotation.Nullable;
import java.util.UUID;

/**
 * Los guerreros calavera del Quinto Sol: en la ultima fase de Khaset salen del piso (tardan 1.5 s en salir, sin poder
 * moverse) esqueletos con penacho, la cara pintada y un macuahuitl de obsidiana. El macuahuitl corta (a veces deja
 * desangrado). Se deshacen cuando Khaset muere. Se dibujan con el modelo del esqueleto (ver cliente/RenderGuerrero).
 */
public class GuerreroCalavera extends Monster implements RangedAttackMob {
    public static final int T_SURGIR = 30;
    private UUID jefe;

    public GuerreroCalavera(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.xpReward = 8;
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 30.0).add(Attributes.ARMOR, 4.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3).add(Attributes.ATTACK_DAMAGE, 4.0).add(Attributes.FOLLOW_RANGE, 48.0);
    }

    public void deJefe(KhasetEntity k) {
        this.jefe = k.getUUID();
        this.setPersistenceRequired();
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Mipack.MACUAHUITL.get()));
        this.setDropChance(EquipmentSlot.MAINHAND, 0.06f);
    }

    /** Con huevo o con /summon tambien sale con su macuahuitl. */
    @Override
    public SpawnGroupData finalizeSpawn(ServerLevelAccessor nivel, DifficultyInstance d, MobSpawnType tipo,
                                        @Nullable SpawnGroupData datos, @Nullable CompoundTag tag) {
        SpawnGroupData r = super.finalizeSpawn(nivel, d, tipo, datos, tag);
        this.populateDefaultEquipmentSlots(this.random, d);
        return r;
    }

    @Override
    protected void populateDefaultEquipmentSlots(net.minecraft.util.RandomSource azar, DifficultyInstance d) {
        this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Mipack.MACUAHUITL.get()));
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.25, true));
        this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.9));
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 12f));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, Player.class, 5, false, false,
                e -> e instanceof Player p && !p.isCreative() && !p.isSpectator()));
        if (Mipack.PRUEBA)
            this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Mob.class, 5, false, false,
                    e -> !(e instanceof KhasetEntity) && !(e instanceof GuerreroCalavera) && !(e instanceof Xiuhcoatl)
                            && !(e instanceof com.mipack.entidad.CrackatosEntity) && !(e instanceof com.mipack.entidad.AcaroAmatista)));
    }

    /** Saliendo del piso no se mueve. */
    @Override
    protected boolean isImmobile() {
        return this.tickCount < T_SURGIR || super.isImmobile();
    }

    @Override
    public void tick() {
        super.tick();
        if (this.tickCount < T_SURGIR && this.tickCount % 2 == 0) {
            BlockState piso = this.level().getBlockState(BlockPos.containing(this.getX(), this.getY() - 0.5, this.getZ()));
            if (piso.isAir())
                piso = Blocks.SOUL_SOIL.defaultBlockState();
            this.level().addParticle(new BlockParticleOption(ParticleTypes.BLOCK, piso), this.getX(), this.getY() + 0.1,
                    this.getZ(), 0, 0.1, 0);
            this.level().addParticle(ParticleTypes.SOUL_FIRE_FLAME, this.getX() + (this.random.nextDouble() - 0.5) * 0.8,
                    this.getY() + 0.2, this.getZ() + (this.random.nextDouble() - 0.5) * 0.8, 0, 0.04, 0);
        }
        if (this.level() instanceof ServerLevel sl && this.tickCount % 40 == 0 && this.jefe != null) {
            Entity j = sl.getEntity(this.jefe);
            if (!(j instanceof KhasetEntity k) || !k.isAlive())
                deshacer(sl);
        }
    }

    /** Se cae en huesos y ceniza. */
    public void deshacer(ServerLevel sl) {
        sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.BONE_BLOCK.defaultBlockState()),
                this.getX(), this.getY() + 1.0, this.getZ(), 25, 0.3, 0.6, 0.3, 0.1);
        sl.sendParticles(ParticulasKhaset.CENIZA.get(), this.getX(), this.getY() + 1.0, this.getZ(), 15, 0.3, 0.6, 0.3, 0.02);
        this.playSound(SoundEvents.SKELETON_DEATH, 1f, 0.7f);
        this.discard();
    }

    @Override
    public boolean doHurtTarget(Entity e) {
        boolean pego = super.doHurtTarget(e);
        if (pego && e instanceof LivingEntity le && this.random.nextInt(3) == 0)
            EfectosKhaset.cortar(le, 1);                          // las navajas de obsidiana cortan
        return pego;
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        Entity q = fuente.getEntity();
        if (q instanceof KhasetEntity || q instanceof Xiuhcoatl || q instanceof GuerreroCalavera
                || fuente.getDirectEntity() instanceof DardoAtlatl || fuente.is(EfectosKhaset.CALOR))
            return false;
        return super.hurt(fuente, cantidad);
    }

    @Override
    public void performRangedAttack(LivingEntity objetivo, float fuerza) {
    }

    @Override
    public MobType getMobType() {
        return MobType.UNDEAD;
    }

    @Override
    public boolean fireImmune() {
        return true;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.SKELETON_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource fuente) {
        return SoundEvents.SKELETON_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.SKELETON_DEATH;
    }

    @Override
    protected void playStepSound(BlockPos pos, BlockState b) {
        this.playSound(SoundEvents.SKELETON_STEP, 0.15f, 1.0f);
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
