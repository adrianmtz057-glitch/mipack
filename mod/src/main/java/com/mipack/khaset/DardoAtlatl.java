package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.AreaEffectCloud;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * El dardo del atlatl: una pluma del penacho (o, sin corona, una astilla de obsidiana ardiendo). Deja un rastro verde y
 * donde pega abre una nube grande (4.5 bloques de radio) de veneno CORTO: 2.5 s de veneno por cada vez que te toca la nube (el normal dura mucho mas).
 */
public class DardoAtlatl extends AbstractArrow implements GeoEntity {
    private static final float DANO = 7f, VELOCIDAD = 2.1f;
    private static final EntityDataAccessor<Boolean> ASTILLA = SynchedEntityData.defineId(DardoAtlatl.class, EntityDataSerializers.BOOLEAN);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    public DardoAtlatl(EntityType<? extends DardoAtlatl> tipo, Level nivel) {
        super(tipo, nivel);
        this.pickup = Pickup.DISALLOWED;
    }

    /** Lanza un dardo desde 'mano' hacia el objetivo (adelantandose a donde va), abierto 'abre' grados de lado. */
    public static void lanzar(Level nivel, KhasetEntity dueno, Vec3 mano, LivingEntity objetivo, float abre, boolean astilla) {
        DardoAtlatl d = new DardoAtlatl(Mipack.DARDO.get(), nivel);
        d.setOwner(dueno);
        d.setPos(mano);
        d.entityData.set(ASTILLA, astilla);
        Vec3 blanco = objetivo.getEyePosition().subtract(0, 0.4, 0);
        double dist = blanco.distanceTo(mano);
        blanco = blanco.add(objetivo.getDeltaMovement().multiply(1, 0, 1).scale(dist / VELOCIDAD));
        Vec3 dir = blanco.subtract(mano);
        double h = Math.sqrt(dir.x * dir.x + dir.z * dir.z);
        double cae = h * 0.012;                                   // compensa la caida del arco
        Vec3 v = new Vec3(dir.x, dir.y + cae * h, dir.z).normalize();
        double a = Math.toRadians(abre);
        v = new Vec3(v.x * Math.cos(a) - v.z * Math.sin(a), v.y, v.x * Math.sin(a) + v.z * Math.cos(a));
        d.shoot(v.x, v.y, v.z, VELOCIDAD, 0f);
        nivel.addFreshEntity(d);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ASTILLA, false);
    }

    public boolean astilla() {
        return this.entityData.get(ASTILLA);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide && !this.inGround) {
            this.level().addParticle(ParticulasKhaset.VENENO.get(), this.getX(), this.getY(), this.getZ(), 0, 0.01, 0);
            if (astilla())
                this.level().addParticle(ParticulasKhaset.BRASA.get(), this.getX(), this.getY(), this.getZ(), 0, 0.02, 0);
        }
    }

    @Override
    protected void onHitEntity(EntityHitResult r) {
        if (r.getEntity() instanceof KhasetEntity || r.getEntity() instanceof Xiuhcoatl || r.getEntity() instanceof GuerreroCalavera)
            return;
        r.getEntity().hurt(this.damageSources().arrow(this, this.getOwner()), DANO);
        if (astilla())
            r.getEntity().setSecondsOnFire(3);
        nube(r.getLocation());
        this.discard();
    }

    @Override
    protected void onHitBlock(BlockHitResult r) {
        super.onHitBlock(r);
        nube(r.getLocation());
        this.discard();
    }

    private void nube(Vec3 p) {
        if (this.level().isClientSide)
            return;
        AreaEffectCloud n = new AreaEffectCloud(this.level(), p.x, p.y, p.z);
        if (this.getOwner() instanceof LivingEntity le)
            n.setOwner(le);
        n.setParticle(ParticulasKhaset.VENENO.get());
        n.setRadius(4.5f);
        n.setRadiusPerTick(-0.015f);
        n.setDuration(90);
        n.setWaitTime(0);
        n.addEffect(new MobEffectInstance(MobEffects.POISON, 50, 0));
        this.level().addFreshEntity(n);
    }

    @Override
    protected ItemStack getPickupItem() {
        return ItemStack.EMPTY;
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
