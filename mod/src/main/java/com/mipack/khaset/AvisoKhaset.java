package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Un circulo de aviso en el piso (donde va a caer el salto del jaguar, donde sale la Xiuhcoatl): un anillo de color
 * con un disco que se llena hasta que pasa. Solo se ve; desaparece solo.
 */
public class AvisoKhaset extends Entity {
    private static final EntityDataAccessor<Float> RADIO = SynchedEntityData.defineId(AvisoKhaset.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> DURA = SynchedEntityData.defineId(AvisoKhaset.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> COLOR = SynchedEntityData.defineId(AvisoKhaset.class, EntityDataSerializers.INT);

    public AvisoKhaset(EntityType<? extends AvisoKhaset> tipo, Level nivel) {
        super(tipo, nivel);
        this.noPhysics = true;
    }

    public static void poner(Level nivel, Vec3 donde, float radio, int ticks, int color) {
        if (nivel.isClientSide)
            return;
        AvisoKhaset a = new AvisoKhaset(Mipack.AVISO.get(), nivel);
        a.setPos(donde);
        a.entityData.set(RADIO, radio);
        a.entityData.set(DURA, ticks);
        a.entityData.set(COLOR, color);
        nivel.addFreshEntity(a);
    }

    @Override
    protected void defineSynchedData() {
        this.entityData.define(RADIO, 2f);
        this.entityData.define(DURA, 20);
        this.entityData.define(COLOR, 0xFF7A1E);
    }

    public float radio() {
        return this.entityData.get(RADIO);
    }

    public int color() {
        return this.entityData.get(COLOR);
    }

    /** De 0 a 1: cuanto falta para que pase. */
    public float avance(float parcial) {
        return Math.min(1f, (this.tickCount + parcial) / Math.max(1, this.entityData.get(DURA)));
    }

    @Override
    public void tick() {
        super.tick();
        if (!this.level().isClientSide && this.tickCount > this.entityData.get(DURA) + 2)
            this.discard();
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag tag) {
        this.discard();
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag tag) {
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }
}
