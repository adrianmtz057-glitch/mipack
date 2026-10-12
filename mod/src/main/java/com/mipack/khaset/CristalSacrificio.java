package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * El cristal del sacrificio: la piedra de tezontle (techcatl) con el cristal de obsidiana flotando a 6 bloques. Se
 * pone con su objeto (como un cristal del End) mirando hacia quien lo pone; Khaset lleva ahi a sus presas. No se
 * rompe: solo un jugador en creativo lo quita pegandole. Se puede pisar.
 * Estados: QUIETO (flota), LLAMANDO (Khaset trae una presa: gira rapido y baja) y SACRIFICIO (recibe el corazon).
 */
public class CristalSacrificio extends Entity implements GeoEntity {
    /** Alto de la cara de arriba de la piedra (bloques): ahi se acuesta la presa. */
    public static final double ALTO_PIEDRA = 1.1;

    private static final RawAnimation A_QUIETO = RawAnimation.begin().thenLoop("animation.cristal_sacrificio.quieto");
    private static final RawAnimation A_LLAMANDO = RawAnimation.begin().thenLoop("animation.cristal_sacrificio.llamando");
    private static final RawAnimation A_SACRIFICIO = RawAnimation.begin().thenPlay("animation.cristal_sacrificio.sacrificio");

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(CristalSacrificio.class, EntityDataSerializers.INT);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int llamado, sacrificio;

    public CristalSacrificio(EntityType<? extends CristalSacrificio> tipo, Level nivel) {
        super(tipo, nivel);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(ESTADO, 0);
    }

    public int estado() {
        return this.entityData.get(ESTADO);
    }

    /** Khaset viene con una presa (se llama cada tick mientras tanto). */
    public void llamar() {
        this.llamado = 10;
    }

    /** Khaset ofrecio el corazon. */
    public void sacrificio() {
        this.sacrificio = 40;
        if (this.level() instanceof ServerLevel sl) {
            double y = this.getY() + 6.0;
            sl.sendParticles(ParticulasKhaset.BRASA.get(), this.getX(), y, this.getZ(), 80, 1.0, 1.0, 1.0, 0.25);
            sl.sendParticles(ParticleTypes.FLASH, this.getX(), y, this.getZ(), 1, 0, 0, 0, 0);
            sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, this.getX(), y, this.getZ(), 40, 0.8, 0.8, 0.8, 0.1);
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide) {
            if (this.random.nextInt(estado() == 1 ? 1 : 6) == 0) {
                double a = this.random.nextDouble() * Math.PI * 2;
                double y = this.getY() + 5.0 + this.random.nextDouble() * 2.0;
                this.level().addParticle(ParticulasKhaset.BRASA.get(), this.getX() + Math.cos(a) * 1.2, y,
                        this.getZ() + Math.sin(a) * 1.2, 0, 0.02, 0);
            }
            if (estado() == 1)                                    // un hilo de fuego de la piedra al cristal
                for (int i = 0; i < 3; i++)
                    this.level().addParticle(ParticleTypes.FLAME, this.getX() + (this.random.nextDouble() - 0.5) * 0.3,
                            this.getY() + ALTO_PIEDRA + this.random.nextDouble() * 4.8,
                            this.getZ() + (this.random.nextDouble() - 0.5) * 0.3, 0, 0.05, 0);
            return;
        }
        if (this.llamado > 0)
            this.llamado--;
        if (this.sacrificio > 0)
            this.sacrificio--;
        int e = this.sacrificio > 0 ? 2 : this.llamado > 0 ? 1 : 0;
        if (e != estado())
            this.entityData.set(ESTADO, e);
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (!this.level().isClientSide && fuente.getEntity() instanceof Player p && p.isCreative()) {
            this.discard();
            return true;
        }
        return false;
    }

    @Override
    public boolean isPickable() {
        return !this.isRemoved();
    }

    @Override
    public boolean canBeCollidedWith() {
        return true;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public ItemStack getPickResult() {
        return new ItemStack(Mipack.CRISTAL_ITEM.get());
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return this.getBoundingBox().inflate(1.5, 0, 1.5).expandTowards(0, 7.5, 0);
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double d) {
        return d < 160 * 160;
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
        controladores.add(new AnimationController<>(this, "principal", 6, this::animar));
    }

    private PlayState animar(AnimationState<CristalSacrificio> estado) {
        return estado.setAndContinue(switch (estado()) {
            case 1 -> A_LLAMANDO;
            case 2 -> A_SACRIFICIO;
            default -> A_QUIETO;
        });
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }

    /** El objeto que lo pone: en la cara de arriba del bloque, con el lado largo hacia quien lo pone. */
    public static final class Objeto extends net.minecraft.world.item.Item {
        public Objeto(Properties p) {
            super(p);
        }

        @Override
        public net.minecraft.world.InteractionResult useOn(net.minecraft.world.item.context.UseOnContext c) {
            Level nivel = c.getLevel();
            if (!(nivel instanceof ServerLevel sl))
                return net.minecraft.world.InteractionResult.SUCCESS;
            net.minecraft.core.BlockPos encima = c.getClickedPos().relative(c.getClickedFace());
            CristalSacrificio cr = new CristalSacrificio(Mipack.CRISTAL.get(), sl);
            float giro = c.getPlayer() != null ? c.getPlayer().getYRot() : 0f;
            cr.moveTo(encima.getX() + 0.5, encima.getY(), encima.getZ() + 0.5, giro, 0f);
            if (!sl.noCollision(cr, cr.getBoundingBox()))
                return net.minecraft.world.InteractionResult.FAIL;
            sl.addFreshEntity(cr);
            if (c.getPlayer() == null || !c.getPlayer().getAbilities().instabuild)
                c.getItemInHand().shrink(1);
            return net.minecraft.world.InteractionResult.CONSUME;
        }
    }
}
