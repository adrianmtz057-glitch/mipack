package com.mipack.entidad;

import com.mipack.Mipack;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/**
 * Una pua de amatista de Crackatos. Dos clases:
 * <ul>
 * <li>Subiendo: las que salen volando del lomo cuando se sacude. Solo se ven (el modelo del jefe no pierde
 *     ninguna): suben girando y desaparecen.</li>
 * <li>Cayendo: la entidad se queda en el piso donde va a caer; primero se ve el circulo morado de aviso (2 bloques
 *     de radio) y despues de la espera la pua cae del cielo y explota al tocar el piso. La altura de la pua se
 *     calcula con el tiempo del mundo (igual en el servidor y en el cliente), asi cae suave sin mandar posiciones.</li>
 * </ul>
 */
public class PuaCayendo extends Entity implements GeoEntity {
    public static final float ALTURA = 18f;                  // de donde cae (bloques sobre el piso)
    public static final float RADIO = 2f;                    // el circulo de aviso y la explosion
    private static final float DANO = 8f;
    private static final float V0 = 0.8f, ACEL = 0.09f;       // caida: h(t) = ALTURA - (V0 t + ACEL t^2)
    public static final float T_CAIDA = (float) ((-V0 + Math.sqrt(V0 * V0 + 4 * ACEL * ALTURA)) / (2 * ACEL));
    private static final int VIDA_SUBIENDO = 26;

    private static final EntityDataAccessor<Boolean> CAE = SynchedEntityData.defineId(PuaCayendo.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> INICIO = SynchedEntityData.defineId(PuaCayendo.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> ESPERA = SynchedEntityData.defineId(PuaCayendo.class, EntityDataSerializers.INT);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private UUID jefe;

    public PuaCayendo(EntityType<? extends PuaCayendo> tipo, Level nivel) {
        super(tipo, nivel);
        this.noPhysics = true;
    }

    /** Una de las que salen volando del lomo (solo se ve). */
    public static PuaCayendo subiendo(ServerLevel nivel, Vec3 donde, Vec3 velocidad) {
        PuaCayendo p = new PuaCayendo(Mipack.PUA.get(), nivel);
        p.setPos(donde);
        p.setDeltaMovement(velocidad);
        p.entityData.set(INICIO, (int) nivel.getGameTime());
        p.apuntar(velocidad);
        return p;
    }

    /** Una que cae en 'suelo' (lo de arriba del piso) despues de 'espera' ticks de aviso. */
    public static PuaCayendo cayendo(ServerLevel nivel, CrackatosEntity jefe, Vec3 suelo, int espera) {
        PuaCayendo p = new PuaCayendo(Mipack.PUA.get(), nivel);
        p.setPos(suelo);
        p.entityData.set(CAE, true);
        p.entityData.set(INICIO, (int) nivel.getGameTime());
        p.entityData.set(ESPERA, espera);
        p.setYRot(nivel.random.nextFloat() * 360f);
        p.jefe = jefe.getUUID();
        return p;
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(CAE, false);
        this.entityData.define(INICIO, 0);
        this.entityData.define(ESPERA, 20);
    }

    public boolean cae() {
        return this.entityData.get(CAE);
    }

    /** Ticks desde que salio (con la fraccion del cuadro). */
    public float edad(float parcial) {
        return (int) this.level().getGameTime() - this.entityData.get(INICIO) + parcial;
    }

    /** Cuanto le falta a la pua para tocar el piso (bloques), o -1 si todavia no empieza a caer. */
    public float alturaQueFalta(float parcial) {
        float t = edad(parcial) - this.entityData.get(ESPERA);
        if (t < 0)
            return -1f;
        return Math.max(0f, ALTURA - (V0 * t + ACEL * t * t));
    }

    /** Del 0 (aparece el aviso) al 1 (cae): para dibujar el circulo que se va llenando. */
    public float avance(float parcial) {
        return Mth.clamp(edad(parcial) / (this.entityData.get(ESPERA) + T_CAIDA), 0f, 1f);
    }

    @Override
    public void tick() {
        super.tick();
        if (!cae()) {
            Vec3 v = this.getDeltaMovement();
            if (!this.level().isClientSide) {
                this.setPos(this.position().add(v));
                this.setDeltaMovement(v.x * 0.97, v.y - 0.06, v.z * 0.97);
                this.apuntar(v);
                if (edad(0) > VIDA_SUBIENDO)
                    this.discard();
            }
            return;
        }
        if (this.level() instanceof ServerLevel sl && edad(0) >= this.entityData.get(ESPERA) + T_CAIDA)
            explotar(sl);
    }

    private void apuntar(Vec3 v) {
        double h = v.horizontalDistance();
        this.setYRot((float) (Mth.atan2(v.x, v.z) * Mth.RAD_TO_DEG));
        this.setXRot((float) (Mth.atan2(v.y, h) * Mth.RAD_TO_DEG));
    }

    private void explotar(ServerLevel sl) {
        double x = this.getX(), y = this.getY(), z = this.getZ();
        sl.sendParticles(ParticleTypes.EXPLOSION, x, y + 0.5, z, 3, 0.8, 0.3, 0.8, 0.0);
        sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState()),
                x, y + 0.6, z, 50, 0.7, 0.5, 0.7, 0.25);
        sl.sendParticles(new DustParticleOptions(new Vector3f(0.62f, 0.32f, 0.95f), 2.0f), x, y + 0.3, z, 40,
                RADIO * 0.6, 0.2, RADIO * 0.6, 0.0);
        sl.playSound(null, x, y, z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 1.6f, 1.25f);
        sl.playSound(null, x, y, z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.HOSTILE, 2.0f, 0.6f);
        Entity dueno = this.jefe != null ? sl.getEntity(this.jefe) : null;
        AABB zona = new AABB(x - RADIO, y - 1, z - RADIO, x + RADIO, y + 2.5, z + RADIO);
        for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, zona, PuaCayendo::alcanzable)) {
            Vec3 afuera = new Vec3(e.getX() - x, 0, e.getZ() - z);
            if (afuera.length() > RADIO + 0.4)
                continue;
            e.hurt(this.damageSources().explosion(this, dueno), DANO);
            Vec3 dir = afuera.lengthSqr() > 1e-4 ? afuera.normalize() : Vec3.ZERO;
            CrackatosEntity.lanzar(e, dir.scale(0.5), 0.5);
        }
        this.discard();
    }

    private static boolean alcanzable(LivingEntity e) {
        if (!e.isAlive() || e instanceof CrackatosEntity)
            return false;
        return !(e instanceof Player p) || (!p.isCreative() && !p.isSpectator());
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        if (cae())                                // el circulo en el piso y la pua que viene de arriba
            return this.getBoundingBox().inflate(RADIO + 0.2, 0, RADIO + 0.2).expandTowards(0, ALTURA + 2, 0);
        return super.getBoundingBoxForCulling();
    }

    @Override
    public boolean shouldBeSaved() {
        return false;                             // si se descarga el mundo a media pelea, no se queda
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
