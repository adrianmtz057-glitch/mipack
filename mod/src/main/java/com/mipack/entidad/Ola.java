package com.mipack.entidad;

import com.mojang.math.Transformation;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * La ola del azote de Crackatos: un anillo que sale de donde pego y crece hasta cubrir la arena. Por donde pasa, los
 * bloques del piso brincan (copias en block display que suben y bajan con interpolacion; el piso de verdad no
 * cambia) y a quien este parado en el piso cuando le llega lo avienta para arriba: se esquiva brincando.
 */
public class Ola {
    /** La etiqueta de los bloques que levanta (si el mundo se guarda a media ola, se borran al cargar). */
    public static final String ETIQUETA = "mipack_ola";
    private static final double VELOCIDAD = 0.9;             // bloques por tick
    private static final int MAX_POR_TICK = 110;             // bloques que levanta por tick, como mucho
    private static final int SUBE = 3, BAJA = 4, VIDA = 9;   // ticks: subiendo, bajando y en total
    private static final float DANO = 8f;

    private record Levantado(Display.BlockDisplay bloque, int nacio, float alto, Quaternionf giro) {}

    private final ServerLevel nivel;
    private final CrackatosEntity jefe;
    private final Vec3 centro;
    private final int radioMax;
    private final RandomSource azar;
    private double radio = 1.5;
    private int tiempo;
    private final List<Levantado> bloques = new ArrayList<>();
    private final Set<UUID> golpeados = new HashSet<>();
    private final Set<Long> columnas = new HashSet<>();

    public Ola(ServerLevel nivel, CrackatosEntity jefe, Vec3 centro, int radioMax) {
        this.nivel = nivel;
        this.jefe = jefe;
        this.centro = centro;
        this.radioMax = radioMax;
        this.azar = nivel.random;
        this.golpeados.add(jefe.getUUID());
    }

    /** Un tick de la ola. Devuelve true cuando ya llego al borde y bajaron todos los bloques. */
    public boolean tick() {
        this.tiempo++;
        if (this.radio < this.radioMax) {
            double r0 = this.radio, r1 = Math.min(this.radioMax, this.radio + VELOCIDAD);
            levantar(r0, r1);
            golpear(r0, r1);
            if (this.tiempo % 2 == 0)
                sonar(r1);
            this.radio = r1;
        }
        Iterator<Levantado> it = this.bloques.iterator();
        while (it.hasNext()) {
            Levantado l = it.next();
            int edad = this.tiempo - l.nacio();
            if (edad == 1)
                mover(l.bloque(), transformacion(l.alto(), l.giro()), SUBE);
            else if (edad == 1 + SUBE)
                mover(l.bloque(), transformacion(0.02f, new Quaternionf()), BAJA);
            else if (edad >= VIDA || l.bloque().isRemoved()) {
                l.bloque().discard();
                it.remove();
            }
        }
        return this.radio >= this.radioMax && this.bloques.isEmpty();
    }

    /** La quita de golpe (el jefe murio o desaparecio). */
    public void terminar() {
        for (Levantado l : this.bloques)
            l.bloque().discard();
        this.bloques.clear();
        this.radio = this.radioMax;
    }

    private void levantar(double r0, double r1) {
        List<BlockPos> banda = new ArrayList<>();
        int cx = (int) Math.floor(this.centro.x), cz = (int) Math.floor(this.centro.z), n = (int) Math.ceil(r1) + 1;
        for (int dx = -n; dx <= n; dx++) {
            for (int dz = -n; dz <= n; dz++) {
                double x = cx + dx + 0.5 - this.centro.x, z = cz + dz + 0.5 - this.centro.z;
                double d = Math.sqrt(x * x + z * z);
                if (d < r0 || d >= r1 || !this.columnas.add(BlockPos.asLong(cx + dx, 0, cz + dz)))
                    continue;
                BlockPos piso = piso(cx + dx, cz + dz);
                if (piso != null)
                    banda.add(piso);
            }
        }
        float p = Math.min(1f, (float) MAX_POR_TICK / Math.max(1, banda.size())) * 0.8f;
        for (BlockPos b : banda) {
            if (this.azar.nextFloat() > p)
                continue;
            BlockState estado = this.nivel.getBlockState(b);
            float cerca = 1f - (float) (Math.sqrt(b.distToCenterSqr(this.centro.x, b.getY() + 0.5, this.centro.z)) / this.radioMax);
            float alto = 0.45f + 0.75f * cerca + this.azar.nextFloat() * 0.25f;
            Quaternionf giro = new Quaternionf().rotateXYZ((this.azar.nextFloat() - 0.5f) * 0.45f, 0f,
                    (this.azar.nextFloat() - 0.5f) * 0.45f);
            Display.BlockDisplay d = EntityType.BLOCK_DISPLAY.create(this.nivel);
            if (d == null)
                return;
            CompoundTag tag = new CompoundTag();
            tag.put("block_state", NbtUtils.writeBlockState(estado));
            tag.put("transformation", transformacion(0.02f, new Quaternionf()));
            tag.putInt("interpolation_duration", SUBE);
            tag.putFloat("view_range", 1.5f);
            d.load(tag);
            // la entidad va en el bloque de aire de arriba (para que tome su luz) y el bloque se dibuja uno abajo
            d.setPos(b.getX(), b.getY() + 1, b.getZ());
            d.addTag(ETIQUETA);
            this.nivel.addFreshEntity(d);
            this.bloques.add(new Levantado(d, this.tiempo, alto, giro));
            if (this.azar.nextInt(6) == 0)
                this.nivel.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, estado), b.getX() + 0.5,
                        b.getY() + 1.1, b.getZ() + 0.5, 4, 0.3, 0.1, 0.3, 0.1);
        }
    }

    /** El bloque de piso de la columna: solido, de modelo normal y con aire (o algo sin colision) arriba. */
    private BlockPos piso(int x, int z) {
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos(x, (int) Math.floor(this.centro.y) + 2, z);
        for (int i = 0; i < 6; i++) {
            m.move(0, -1, 0);
            BlockState s = this.nivel.getBlockState(m);
            if (s.isAir() || s.getRenderShape() != RenderShape.MODEL || s.hasBlockEntity() || !s.getFluidState().isEmpty())
                continue;
            BlockPos arriba = m.above();
            if (this.nivel.getBlockState(arriba).getCollisionShape(this.nivel, arriba).isEmpty())
                return m.immutable();
            return null;                          // una pared: ahi no brinca nada
        }
        return null;
    }

    private void golpear(double r0, double r1) {
        AABB zona = new AABB(this.centro, this.centro).inflate(r1 + 1, 4, r1 + 1);
        for (LivingEntity e : this.nivel.getEntitiesOfClass(LivingEntity.class, zona, Ola::alcanzable)) {
            double dx = e.getX() - this.centro.x, dz = e.getZ() - this.centro.z;
            double d = Math.sqrt(dx * dx + dz * dz);
            if (d < r0 - 1.0 || d >= r1 + 0.5 || !e.onGround() || Math.abs(e.getY() - this.centro.y) > 3)
                continue;
            if (!this.golpeados.add(e.getUUID()))
                continue;
            e.hurt(this.nivel.damageSources().mobAttack(this.jefe), DANO);
            Vec3 afuera = d > 1e-3 ? new Vec3(dx / d, 0, dz / d) : Vec3.ZERO;
            CrackatosEntity.lanzar(e, afuera.scale(0.7), 1.15);
        }
    }

    private static boolean alcanzable(LivingEntity e) {
        if (!e.isAlive() || e instanceof CrackatosEntity)
            return false;
        return !(e instanceof Player p) || (!p.isCreative() && !p.isSpectator());
    }

    /** El ruido de la ola, en el punto del anillo mas cercano a cada jugador. */
    private void sonar(double r) {
        for (ServerPlayer j : this.nivel.players()) {
            Vec3 d = new Vec3(j.getX() - this.centro.x, 0, j.getZ() - this.centro.z);
            if (d.length() > this.radioMax + 24)
                continue;
            Vec3 p = this.centro.add(d.lengthSqr() > 1e-4 ? d.normalize().scale(r) : Vec3.ZERO);
            this.nivel.playSound(null, p.x, p.y, p.z, SoundEvents.DEEPSLATE_BREAK, SoundSource.HOSTILE, 1.6f,
                    0.6f + this.azar.nextFloat() * 0.3f);
        }
    }

    private static void mover(Display.BlockDisplay d, net.minecraft.nbt.Tag transformacion, int ticks) {
        // los setters del display son privados: se le cambia la transformacion por NBT (como /data merge)
        CompoundTag tag = d.saveWithoutId(new CompoundTag());
        tag.put("transformation", transformacion);
        tag.putInt("start_interpolation", 0);
        tag.putInt("interpolation_duration", ticks);
        d.load(tag);
    }

    private static net.minecraft.nbt.Tag transformacion(float alto, Quaternionf giro) {
        // un pelito mas grande que el bloque de verdad (para que no parpadeen las caras encimadas) y girado sobre
        // su centro
        Vector3f c = new Vector3f(0.503f);
        Vector3f mov = new Vector3f(-0.003f, -1f + alto - 0.003f, -0.003f).add(c).sub(giro.transform(new Vector3f(c)));
        Transformation t = new Transformation(mov, giro, new Vector3f(1.006f), new Quaternionf());
        return Transformation.EXTENDED_CODEC.encodeStart(NbtOps.INSTANCE, t).result().orElseThrow();
    }
}
