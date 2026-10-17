package com.mipack.bruma;

import com.mipack.Mipack;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RangedBowAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.UUID;

/**
 * El ejercito de La Bruma: guerreros de armadura azteca negra que suben del piso cuando ella los mueve como titiritera.
 * <ul>
 * <li>Soldado: espada de hierro y escudo; de frente para la mitad de los golpes.</li>
 * <li>Arquero: arco con flechas que alentan.</li>
 * <li>Soldado grande: espera junto al centro y pega muy fuerte. Su escudo no se rompe con nada mas que con el pedazo de
 *     piramide (pegarle con el en la mano): mientras lo tenga no le entra ningun golpe. Cuando muere, La Bruma grita,
 *     pierde vida y se arrodilla.</li>
 * </ul>
 * Se deshacen cuando La Bruma muere o desaparece.
 */
public class SoldadoBruma extends Monster implements RangedAttackMob {
    public enum Tipo { SOLDADO, ARQUERO, GRANDE }

    private static final int T_SUBIR = 24;
    private int subiendo = T_SUBIR;
    private UUID duena;
    private BlockPos puesto;
    private boolean escudoRoto;

    public SoldadoBruma(EntityType<? extends SoldadoBruma> tipo, Level nivel) {
        super(tipo, nivel);
        this.xpReward = tipo() == Tipo.GRANDE ? 60 : 4;
    }

    public Tipo tipo() {
        EntityType<?> t = this.getType();
        return t == Mipack.ARQUERO_BRUMA.get() ? Tipo.ARQUERO : t == Mipack.SOLDADO_GRANDE.get() ? Tipo.GRANDE : Tipo.SOLDADO;
    }

    public static AttributeSupplier.Builder soldado() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 30).add(Attributes.ARMOR, 8)
                .add(Attributes.ATTACK_DAMAGE, 6).add(Attributes.MOVEMENT_SPEED, 0.28).add(Attributes.FOLLOW_RANGE, 40);
    }

    public static AttributeSupplier.Builder arquero() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 24).add(Attributes.ARMOR, 4)
                .add(Attributes.MOVEMENT_SPEED, 0.27).add(Attributes.FOLLOW_RANGE, 40);
    }

    public static AttributeSupplier.Builder grande() {
        return Monster.createMonsterAttributes().add(Attributes.MAX_HEALTH, 400).add(Attributes.ARMOR, 16)
                .add(Attributes.ATTACK_DAMAGE, 16).add(Attributes.MOVEMENT_SPEED, 0.24).add(Attributes.FOLLOW_RANGE, 24)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0).add(Attributes.ATTACK_KNOCKBACK, 1.5);
    }

    /** La saca del piso para su duena (null: con huevo, sin duena). */
    public void deLaBruma(BrumaEntity b) {
        this.duena = b == null ? null : b.getUUID();
        this.puesto = this.blockPosition();
        this.setPersistenceRequired();
        if (tipo() == Tipo.ARQUERO) {
            this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(Items.BOW));
        } else {
            this.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(tipo() == Tipo.GRANDE ? Items.NETHERITE_AXE : Items.IRON_SWORD));
            this.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(Items.SHIELD));
        }
        for (EquipmentSlot s : EquipmentSlot.values())
            this.setDropChance(s, 0f);
    }

    @Override
    public net.minecraft.world.entity.SpawnGroupData finalizeSpawn(net.minecraft.world.level.ServerLevelAccessor nivel, DifficultyInstance d,
            net.minecraft.world.entity.MobSpawnType razon, net.minecraft.world.entity.SpawnGroupData datos, CompoundTag tag) {
        var r = super.finalizeSpawn(nivel, d, razon, datos, tag);
        if (this.puesto == null)
            deLaBruma(null);
        return r;
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        if (this.getType() == Mipack.ARQUERO_BRUMA.get())
            this.goalSelector.addGoal(2, new RangedBowAttackGoal<>(this, 1.0, 30, 22f));
        else
            this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.15, true));
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this, SoldadoBruma.class, BrumaEntity.class, ClonBruma.class));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true,
                p -> this.tipo() != Tipo.GRANDE || this.puesto == null || p.blockPosition().closerThan(this.puesto, 10)));
    }

    public boolean subiendo() {
        return this.subiendo > 0;
    }

    @Override
    public void aiStep() {
        if (this.subiendo > 0 && !this.level().isClientSide) {          // sale del piso
            if (this.subiendo == T_SUBIR) {
                this.setPos(this.getX(), this.getY() - this.getBbHeight(), this.getZ());
                this.playSound(SoundEvents.ZOMBIE_VILLAGER_CURE, 0.6f, 0.4f);
            }
            this.noPhysics = true;
            this.setPos(this.getX(), this.getY() + this.getBbHeight() / T_SUBIR, this.getZ());
            this.setDeltaMovement(Vec3.ZERO);
            if (this.level() instanceof ServerLevel sl) {
                BlockState piso = sl.getBlockState(this.blockPosition().below());
                if (!piso.isAir())
                    sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, piso), this.getX(), this.getY() + 0.2, this.getZ(),
                            6, this.getBbWidth() * 0.4, 0.1, this.getBbWidth() * 0.4, 0.1);
                sl.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 0.5, this.getZ(), 1, 0.3, 0.2, 0.3, 0.02);
            }
            if (--this.subiendo == 0)
                this.noPhysics = false;
            return;
        }
        super.aiStep();
        if (this.level().isClientSide)
            return;
        if (this.tickCount % 20 == 0 && this.duena != null && this.level() instanceof ServerLevel sl
                && !(sl.getEntity(this.duena) instanceof BrumaEntity b && b.isAlive())) {
            sl.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 1, this.getZ(), 10, 0.3, 0.6, 0.3, 0.03);
            if (Mipack.PRUEBA)
                Mipack.LOGGER.info("[Soldado] sin duena, se deshace");
            this.discard();                                    // sin su duena se deshace
            return;
        }
        // el grande cuida su puesto
        if (tipo() == Tipo.GRANDE && this.puesto != null && this.getTarget() == null
                && this.distanceToSqr(Vec3.atBottomCenterOf(this.puesto)) > 9 && this.tickCount % 20 == 0)
            this.getNavigation().moveTo(this.puesto.getX() + 0.5, this.puesto.getY(), this.puesto.getZ() + 0.5, 0.9);
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (this.subiendo > 0 && !fuente.is(DamageTypeTags.BYPASSES_INVULNERABILITY))
            return false;
        if (fuente.is(DamageTypeTags.BYPASSES_INVULNERABILITY) || this.level().isClientSide)
            return super.hurt(fuente, cantidad);
        if (tipo() == Tipo.GRANDE && !this.escudoRoto) {
            if (fuente.getEntity() instanceof Player p && (p.getMainHandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get())
                    || p.getOffhandItem().is(ObjetosMipack.PEDAZO_PIRAMIDE.get()))) {
                this.escudoRoto = true;                           // el pedazo de piramide le rompe el escudo
                this.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
                this.playSound(SoundEvents.SHIELD_BREAK, 2.0f, 0.5f);
                this.playSound(SoundEvents.BEACON_DEACTIVATE, 2.0f, 1.5f);
                if (this.level() instanceof ServerLevel sl)
                    sl.sendParticles(ParticleTypes.END_ROD, this.getX(), this.getY() + 2, this.getZ(), 60, 0.8, 1.2, 0.8, 0.15);
                return super.hurt(fuente, cantidad);
            }
            this.playSound(SoundEvents.SHIELD_BLOCK, 1.5f, 0.6f);
            return false;
        }
        if (tipo() == Tipo.SOLDADO && fuente.getEntity() != null && !fuente.is(DamageTypeTags.BYPASSES_SHIELD)
                && this.random.nextBoolean() && deFrente(fuente.getSourcePosition())) {
            this.playSound(SoundEvents.SHIELD_BLOCK, 1.0f, 0.9f);
            return false;
        }
        return super.hurt(fuente, cantidad);
    }

    private boolean deFrente(Vec3 desde) {
        if (desde == null)
            return false;
        Vec3 a = desde.subtract(this.position()).normalize();
        Vec3 mira = this.getViewVector(1f);
        return a.x * mira.x + a.z * mira.z > 0.3;
    }

    @Override
    public void remove(RemovalReason razon) {
        if (Mipack.PRUEBA && !this.level().isClientSide && this.tickCount < 100)
            Mipack.LOGGER.info("[Soldado] se quita ({}) en {} a los {} ticks", razon, this.blockPosition(), this.tickCount);
        super.remove(razon);
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (!this.level().isClientSide && tipo() == Tipo.GRANDE && this.duena != null
                && ((ServerLevel) this.level()).getEntity(this.duena) instanceof BrumaEntity b)
            b.murioElGrande();
    }

    @Override
    public void performRangedAttack(LivingEntity blanco, float fuerza) {
        Arrow f = new Arrow(this.level(), this);
        f.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 100, 1));
        double dx = blanco.getX() - this.getX(), dz = blanco.getZ() - this.getZ();
        double dy = blanco.getY(0.33) - f.getY();
        f.shoot(dx, dy + Math.sqrt(dx * dx + dz * dz) * 0.2, dz, 1.6f, 6f);
        f.setBaseDamage(3.0);
        this.playSound(SoundEvents.SKELETON_SHOOT, 1.0f, 0.8f);
        this.level().addFreshEntity(f);
    }

    @Override
    public boolean canFireProjectileWeapon(net.minecraft.world.item.ProjectileWeaponItem arma) {
        return arma == Items.BOW;
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource fuente, int saqueo, boolean golpe) {
        if (tipo() == Tipo.GRANDE)
            this.spawnAtLocation(new ItemStack(Items.ECHO_SHARD, 1));
    }

    @Override
    public boolean removeWhenFarAway(double d) {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (this.duena != null)
            tag.putUUID("Duena", this.duena);
        if (this.puesto != null)
            tag.putLong("Puesto", this.puesto.asLong());
        tag.putBoolean("EscudoRoto", this.escudoRoto);
        tag.putInt("Subiendo", this.subiendo);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.duena = tag.hasUUID("Duena") ? tag.getUUID("Duena") : null;
        this.puesto = tag.contains("Puesto") ? BlockPos.of(tag.getLong("Puesto")) : null;
        this.escudoRoto = tag.getBoolean("EscudoRoto");
        this.subiendo = tag.getInt("Subiendo");
    }
}
