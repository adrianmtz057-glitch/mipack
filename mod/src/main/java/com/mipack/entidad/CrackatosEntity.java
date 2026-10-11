package com.mipack.entidad;

import com.mipack.Mipack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Crackatos, la bestia de piedra amatista: un jefe de esquivar.
 * <ul>
 * <li>ACECHAR: camina hacia su objetivo. Cerca o despues de un rato decide que hacer.</li>
 * <li>RASCAR: el aviso de la embestida (rasca el piso con la cabeza baja); al final fija la direccion.</li>
 * <li>EMBESTIR: corre en linea recta. Si choca con una pared se le atoran los cuernos (CHOCAR, ATORADO: recibe el
 *     doble de dano) y luego se zafa (ZAFARSE). Si pega, avienta (CABEZAZO): mucho dano mas el de la caida.
 *     Al caminar y correr pisa: lo que quede bajo sus patas recibe dano.</li>
 * <li>SACUDIDA: cada 2 o 3 embestidas se sacude; salen puas volando del lomo y luego caen del cielo sobre los
 *     jugadores con un circulo morado de aviso de 2 bloques de radio, y explotan.</li>
 * <li>ALZARSE: se para en dos patas y azota; la ola recorre toda la arena levantando los bloques del piso (solo
 *     se ven, el piso no cambia) y avienta a quien este en el piso cuando le llega: brincando se esquiva.</li>
 * </ul>
 * Los tiempos (en ticks) son los de sus animaciones (taller/personajes/crackatos_anim.py).
 */
public class CrackatosEntity extends Monster implements GeoEntity {
    public enum Estado { QUIETO, RUGIDO, ACECHAR, RASCAR, EMBESTIR, CHOCAR, ATORADO, ZAFARSE, CABEZAZO, SACUDIDA, ALZARSE, MUERTE }

    // duraciones de las animaciones (ticks) y los momentos clave
    private static final int T_RUGIDO = 36, T_RASCAR = 30, T_FIJA = 22, T_EMBESTIR_MAX = 64, T_CHOCAR = 10, T_ATORADO = 80;
    private static final int T_ZAFARSE = 16, T_CABEZAZO = 14, T_SACUDIDA = 44, T_SALEN_PUAS = 32, T_ALZARSE = 52;
    private static final int T_AZOTE = 31, T_MUERTE = 50;
    // dano (en medios corazones)
    private static final float DANO_EMBESTIDA = 14f, DANO_PISOTON = 6f, DANO_AZOTE = 12f, DANO_CORNADA = 10f;
    // cada cuanto puede repetir (ticks): el azote y la cornada de cerca
    private static final int ENFRIAR_ALZARSE = 240, ENFRIAR_CORNADA = 70, T_GOLPE_CORNADA = 4;
    private static final int MAX_SIN_EMBESTIR = 220;              // si lleva tanto sin embestir, embiste aunque este cerca

    /** Cuanto crece el modelo en el juego (el render lo usa; las animaciones van al paso de esta escala). */
    public static final float ESCALA = 2.0f;
    // a que velocidad (bloques por tick) avanza el cuerpo en las animaciones de caminar y galopar a velocidad 1:
    // el pie apoyado recorre su zancada (7 y 14 px del modelo) en lo que dura el apoyo (0.7 de 1.6 s, 0.42 de 0.6 s)
    private static final double PASO_CAMINAR = 7.0 / (0.7 * 1.6) * ESCALA / 16 / 20;
    private static final double PASO_GALOPE = 14.0 / (0.42 * 0.6) * ESCALA / 16 / 20;

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(CrackatosEntity.class, EntityDataSerializers.INT);

    private static final RawAnimation A_QUIETO = RawAnimation.begin().thenLoop("animation.crackatos.quieto");
    private static final RawAnimation A_CAMINAR = RawAnimation.begin().thenLoop("animation.crackatos.caminar");
    private static final RawAnimation A_RUGIDO = RawAnimation.begin().thenPlay("animation.crackatos.rugido");
    private static final RawAnimation A_RASCAR = RawAnimation.begin().thenPlayAndHold("animation.crackatos.rascar_piso");
    private static final RawAnimation A_EMBESTIR = RawAnimation.begin().thenLoop("animation.crackatos.embestir");
    private static final RawAnimation A_ATORADO = RawAnimation.begin().thenPlay("animation.crackatos.chocar").thenLoop("animation.crackatos.atorado");
    private static final RawAnimation A_ZAFARSE = RawAnimation.begin().thenPlay("animation.crackatos.zafarse");
    private static final RawAnimation A_CABEZAZO = RawAnimation.begin().thenPlay("animation.crackatos.cabezazo");
    private static final RawAnimation A_SACUDIDA = RawAnimation.begin().thenPlay("animation.crackatos.sacudida");
    private static final RawAnimation A_ALZARSE = RawAnimation.begin().thenPlay("animation.crackatos.alzarse_azotar");
    private static final RawAnimation A_MUERTE = RawAnimation.begin().thenPlayAndHold("animation.crackatos.muerte");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final ServerBossEvent barra = new ServerBossEvent(this.getDisplayName(), BossEvent.BossBarColor.PURPLE,
            BossEvent.BossBarOverlay.NOTCHED_10);

    private int ticksEnEstado;
    private Vec3 direccion = Vec3.ZERO;
    private int embestidas;
    private int embestidasAntesDeSacudir = 2;
    private int alzadasPendientes;
    private int enfriarAlzarse = 100, enfriarCornada, sinEmbestir;
    private boolean cornada;                       // el cabezazo es la cornada de cerca (no el remate de una embestida)
    private boolean rugioAlEmpezar;
    private final Set<UUID> golpeados = new HashSet<>();
    private final EnumSet<Estado> visitados = EnumSet.noneOf(Estado.class);
    private Ola ola;

    public CrackatosEntity(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.setMaxUpStep(1.5f);
        this.xpReward = 500;
        this.setPersistenceRequired();
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 600.0)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2)
                .add(Attributes.FOLLOW_RANGE, 64.0)
                .add(Attributes.ATTACK_DAMAGE, DANO_EMBESTIDA);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, Estado.QUIETO.ordinal());
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, false, false,
                e -> e instanceof Player p && !p.isCreative() && !p.isSpectator()));
        if (Mipack.PRUEBA)
            this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Mob.class, 10, false, false,
                    e -> !(e instanceof CrackatosEntity)));
    }

    public Estado getEstado() {
        return Estado.values()[this.entityData.get(ESTADO)];
    }

    /** Para las pruebas: por que estados ha pasado y cuanto lleva en el de ahora. */
    public Set<Estado> visitados() {
        return this.visitados;
    }

    public int ticksEnEstado() {
        return this.ticksEnEstado;
    }

    private void cambiar(Estado nuevo) {
        if (Mipack.PRUEBA)
            Mipack.LOGGER.info("[Crackatos] {} -> {} (vida {})", getEstado(), nuevo, (int) getHealth());
        this.entityData.set(ESTADO, nuevo.ordinal());
        this.ticksEnEstado = 0;
        this.visitados.add(nuevo);
    }

    private boolean valido(LivingEntity e) {
        if (e == null || !e.isAlive() || e == this || e instanceof CrackatosEntity)
            return false;
        if (e instanceof Player p)
            return !p.isCreative() && !p.isSpectator();
        return Mipack.PRUEBA && e instanceof Mob;
    }

    private boolean segundaFase() {
        return this.getHealth() < this.getMaxHealth() * 0.5f;
    }

    // ------------------------------------------------------------------ la pelea (servidor)

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        this.ticksEnEstado++;
        if (this.enfriarAlzarse > 0)
            this.enfriarAlzarse--;
        if (this.enfriarCornada > 0)
            this.enfriarCornada--;
        if (getEstado() == Estado.ACECHAR || (getEstado() == Estado.CABEZAZO && cornada))
            this.sinEmbestir++;
        LivingEntity objetivo = this.getTarget();
        if (!valido(objetivo))
            objetivo = null;
        switch (getEstado()) {
            case QUIETO -> {
                if (objetivo != null)
                    cambiar(rugioAlEmpezar ? Estado.ACECHAR : Estado.RUGIDO);
            }
            case RUGIDO -> {
                rugioAlEmpezar = true;
                quieto(objetivo);
                if (ticksEnEstado == 8)
                    this.playSound(SoundEvents.RAVAGER_ROAR, 4.0f, 0.55f);
                if (ticksEnEstado >= T_RUGIDO)
                    cambiar(Estado.ACECHAR);
            }
            case ACECHAR -> acechar(objetivo);
            case RASCAR -> {
                if (ticksEnEstado < T_FIJA && objetivo != null) {
                    mirarA(objetivo.position());
                    Vec3 d = objetivo.position().subtract(this.position());
                    this.direccion = new Vec3(d.x, 0, d.z).normalize();
                } else {
                    girarA(this.direccion);
                }
                if (ticksEnEstado % 12 == 6) {
                    this.playSound(SoundEvents.RAVAGER_STEP, 2.0f, 0.6f);
                    polvo(this.position().add(this.direccion.scale(4.0)), 12);
                }
                if (ticksEnEstado >= T_RASCAR) {
                    golpeados.clear();
                    sinEmbestir = 0;
                    if (Mipack.PRUEBA && objetivo != null)
                        Mipack.LOGGER.info("[Crackatos] embiste: blanco a {} bloques, direccion {}, apunta {}",
                                String.format("%.1f", this.distanceTo(objetivo)), this.direccion,
                                String.format("%.2f", objetivo.position().subtract(this.position()).normalize().dot(this.direccion)));
                    this.playSound(SoundEvents.RAVAGER_ROAR, 3.0f, 0.8f);
                    cambiar(Estado.EMBESTIR);
                }
            }
            case EMBESTIR -> embestir();
            case CHOCAR -> {
                girarA(this.direccion);
                if (ticksEnEstado >= T_CHOCAR)
                    cambiar(Estado.ATORADO);
            }
            case ATORADO -> {
                girarA(this.direccion);
                if (ticksEnEstado % 20 == 10)
                    this.playSound(SoundEvents.RAVAGER_STUNNED, 2.0f, 0.7f);
                if (ticksEnEstado >= T_ATORADO)
                    cambiar(Estado.ZAFARSE);
            }
            case ZAFARSE -> {
                girarA(this.direccion);
                if (ticksEnEstado == 3) {
                    this.playSound(SoundEvents.ZOMBIE_BREAK_WOODEN_DOOR, 2.0f, 0.5f);
                    polvo(this.position().add(this.direccion.scale(6.0)).add(0, 2, 0), 30);
                }
                if (ticksEnEstado >= T_ZAFARSE)
                    terminarEmbestida();
            }
            case CABEZAZO -> {
                if (cornada && ticksEnEstado < T_GOLPE_CORNADA && objetivo != null) {
                    Vec3 d = objetivo.position().subtract(this.position());
                    this.direccion = new Vec3(d.x, 0, d.z).normalize();
                }
                girarA(this.direccion);
                if (cornada && ticksEnEstado == T_GOLPE_CORNADA)
                    cornear();
                if (ticksEnEstado >= T_CABEZAZO) {
                    if (cornada)
                        cambiar(Estado.ACECHAR);
                    else
                        terminarEmbestida();
                }
            }
            case SACUDIDA -> {
                quieto(objetivo);
                if (ticksEnEstado == 8)
                    this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 3.0f, 0.5f);
                if (ticksEnEstado == T_SALEN_PUAS)
                    lanzarPuas();
                if (ticksEnEstado >= T_SACUDIDA) {
                    embestidas = 0;
                    embestidasAntesDeSacudir = (segundaFase() ? 3 : 2) + this.random.nextInt(2);
                    if (segundaFase())
                        alzadasPendientes++;
                    cambiar(Estado.ACECHAR);
                }
            }
            case ALZARSE -> {
                quieto(objetivo);
                if (ticksEnEstado == 6)
                    this.playSound(SoundEvents.RAVAGER_ROAR, 4.0f, 0.45f);
                if (ticksEnEstado == T_AZOTE)
                    azotar();
                if (ticksEnEstado >= T_ALZARSE)
                    cambiar(Estado.ACECHAR);
            }
            case MUERTE -> {
            }
        }
        if (this.ola != null && this.ola.tick())
            this.ola = null;
        this.barra.setProgress(this.getHealth() / this.getMaxHealth());
    }

    private void acechar(LivingEntity objetivo) {
        if (objetivo == null) {
            this.getMoveControl().setWantedPosition(this.getX(), this.getY(), this.getZ(), 0.0);
            if (ticksEnEstado > 100)
                cambiar(Estado.QUIETO);
            return;
        }
        double dist = this.distanceTo(objetivo);
        this.getMoveControl().setWantedPosition(objetivo.getX(), objetivo.getY(), objetivo.getZ(), 1.0);
        this.getLookControl().setLookAt(objetivo, 30f, 30f);
        if (ticksEnEstado % 10 == 0)
            pisoton();
        if (ticksEnEstado < 20)
            return;
        if (embestidas >= embestidasAntesDeSacudir) {
            cambiar(Estado.SACUDIDA);
        } else if (alzadasPendientes > 0 && ticksEnEstado > 30) {
            alzadasPendientes--;
            alzarse();
        } else if (sinEmbestir > MAX_SIN_EMBESTIR) {
            cambiar(Estado.RASCAR);               // no se queda nomas corneando: tambien embiste de cerca
        } else if (dist < this.getBbWidth() * 0.5 + 3.5 && enfriarCornada == 0) {
            // de cerca: la cornada (el cabezazo hacia arriba), que avienta para que no se le pueda pegar nomas
            this.cornada = true;
            this.enfriarCornada = ENFRIAR_CORNADA;
            cambiar(Estado.CABEZAZO);
        } else if (dist < 10 && enfriarAlzarse == 0 && ticksEnEstado > 50) {
            alzarse();
        } else if ((dist > 7 && (ticksEnEstado > 60 || this.random.nextInt(40) == 0)) || ticksEnEstado > 160) {
            cambiar(Estado.RASCAR);
        }
    }

    private void alzarse() {
        this.enfriarAlzarse = ENFRIAR_ALZARSE;
        cambiar(Estado.ALZARSE);
    }

    /** La cornada: lo que este enfrente de la cabeza sale volando para arriba. */
    private void cornear() {
        Vec3 c = this.position().add(this.direccion.scale(this.getBbWidth() * 0.5 + 1.2));
        AABB zona = new AABB(c.x - 2.5, this.getY() - 0.5, c.z - 2.5, c.x + 2.5, this.getY() + 4.5, c.z + 2.5);
        boolean pego = false;
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, zona, this::valido)) {
            e.hurt(this.damageSources().mobAttack(this), DANO_CORNADA);
            lanzar(e, this.direccion.scale(0.9), 1.1);
            pego = true;
        }
        this.playSound(pego ? SoundEvents.RAVAGER_ATTACK : SoundEvents.RAVAGER_STEP, 2.5f, 0.7f);
    }

    private void embestir() {
        girarA(this.direccion);
        double velocidad = segundaFase() ? 0.85 : 0.68;
        Vec3 antes = this.position();
        this.move(MoverType.SELF, new Vec3(this.direccion.x * velocidad, 0, this.direccion.z * velocidad));
        double avance = this.position().subtract(antes).dot(this.direccion);     // si roza una pared se resbala
        if (ticksEnEstado % 5 == 0) {
            this.playSound(SoundEvents.RAVAGER_STEP, 2.5f, 0.5f);
            pisoton();
        }
        // a quien alcanza: dano fuerte y lo avienta (el dano de caida lo pone el juego)
        AABB frente = this.getBoundingBox().inflate(0.6, 0.0, 0.6).move(this.direccion.x * 1.6, 0, this.direccion.z * 1.6);
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, frente, this::valido)) {
            if (golpeados.add(e.getUUID())) {
                e.hurt(this.damageSources().mobAttack(this), segundaFase() ? DANO_EMBESTIDA * 1.25f : DANO_EMBESTIDA);
                lanzar(e, this.direccion.scale(2.1), 1.3);
                this.playSound(SoundEvents.RAVAGER_ATTACK, 3.0f, 0.6f);
                this.cornada = false;
                cambiar(Estado.CABEZAZO);
                return;
            }
        }
        // se estrello: los cuernos se atoran en la pared (se ve por la cabeza, que va mas adelante que la caja)
        boolean cabeza = cabezaEnPared(), frenado = avance < velocidad * 0.35;
        if ((cabeza || frenado) && ticksEnEstado > 3) {
            if (Mipack.PRUEBA)
                Mipack.LOGGER.info("[Crackatos] choca en el tick {} (cabeza {}, frenado {}) en {}", ticksEnEstado, cabeza,
                        frenado, this.blockPosition());
            this.playSound(SoundEvents.ANVIL_LAND, 2.5f, 0.5f);
            this.playSound(SoundEvents.GENERIC_EXPLODE, 1.5f, 0.7f);
            BlockPos pared = BlockPos.containing(this.position().add(this.direccion.scale(this.getBbWidth() * 0.5 + 1.0)).add(0, 2, 0));
            BlockState bloque = this.level().getBlockState(pared);
            if (this.level() instanceof ServerLevel sl && !bloque.isAir())
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, bloque), pared.getX() + 0.5, pared.getY() + 0.5,
                        pared.getZ() + 0.5, 80, 1.5, 1.5, 1.5, 0.2);
            cambiar(Estado.CHOCAR);
            return;
        }
        if (ticksEnEstado >= T_EMBESTIR_MAX)
            terminarEmbestida();
    }

    /** Si lo de enfrente de la caja (donde van la cabeza y los cuernos) ya pega con algo solido. */
    private boolean cabezaEnPared() {
        Vec3 c = this.position().add(this.direccion.scale(this.getBbWidth() * 0.5 + 0.9));
        AABB cabeza = new AABB(c.x - 0.9, this.getY() + 1.4, c.z - 0.9, c.x + 0.9, this.getY() + 4.2, c.z + 0.9)
                .expandTowards(this.direccion.x * 0.5, 0, this.direccion.z * 0.5);
        return !this.level().noCollision(this, cabeza);
    }

    private void terminarEmbestida() {
        embestidas++;
        cambiar(Estado.ACECHAR);
    }

    /** Lo que quede bajo sus patas recibe dano y sale empujado. */
    private void pisoton() {
        AABB b = this.getBoundingBox();
        AABB pies = new AABB(b.minX, b.minY, b.minZ, b.maxX, b.minY + 1.4, b.maxZ);
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, pies, this::valido)) {
            e.hurt(this.damageSources().mobAttack(this), DANO_PISOTON);
            Vec3 afuera = e.position().subtract(this.position());
            lanzar(e, new Vec3(afuera.x, 0, afuera.z).normalize().scale(0.9), 0.4);
        }
    }

    private void lanzarPuas() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        this.playSound(SoundEvents.AMETHYST_CLUSTER_BREAK, 4.0f, 0.5f);
        // las que salen volando del lomo (solo se ven: el modelo no pierde ninguna)
        for (int i = 0; i < 10; i++) {
            Vec3 p = this.position().add((this.random.nextDouble() - 0.5) * 6, 5.5, (this.random.nextDouble() - 0.5) * 8);
            sl.addFreshEntity(PuaCayendo.subiendo(sl, p, new Vec3((this.random.nextDouble() - 0.5) * 0.6, 1.4, (this.random.nextDouble() - 0.5) * 0.6)));
        }
        // las que caen: sobre cada jugador cerca y alrededor, con su circulo de aviso
        List<Vec3> blancos = new ArrayList<>();
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(40), this::valido)) {
            blancos.add(e.position());
            blancos.add(deEsteLado(e.position().add((this.random.nextDouble() - 0.5) * 6, 0, (this.random.nextDouble() - 0.5) * 6)));
        }
        int extra = segundaFase() ? 10 : 6;
        for (int i = 0; i < extra; i++) {
            double ang = this.random.nextDouble() * Math.PI * 2, r = 5 + this.random.nextDouble() * 12;
            blancos.add(deEsteLado(this.position().add(Math.cos(ang) * r, 0, Math.sin(ang) * r)));
        }
        for (int i = 0; i < blancos.size(); i++) {
            Vec3 b = blancos.get(i);
            sl.addFreshEntity(PuaCayendo.cayendo(sl, this, piso(b), 20 + this.random.nextInt(12)));
        }
    }

    /** Si una pared queda entre el jefe y el punto, lo trae de este lado (las puas al azar caen dentro de la arena). */
    private Vec3 deEsteLado(Vec3 p) {
        Vec3 desde = this.position().add(0, 1.5, 0), hasta = new Vec3(p.x, this.getY() + 1.5, p.z);
        BlockHitResult r = this.level().clip(new ClipContext(desde, hasta, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (r.getType() == HitResult.Type.MISS)
            return p;
        Vec3 atras = hasta.subtract(desde).normalize().scale(PuaCayendo.RADIO + 0.5);
        return new Vec3(r.getLocation().x - atras.x, p.y, r.getLocation().z - atras.z);
    }

    /** El piso (lo de arriba del bloque solido) bajo un punto, buscando cerca de la altura del jefe. */
    private Vec3 piso(Vec3 p) {
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos(p.x, this.getY() + 3, p.z);
        for (int i = 0; i < 10; i++) {
            if (!this.level().getBlockState(m).isAir() && this.level().getBlockState(m.above()).isAir())
                return new Vec3(p.x, m.getY() + 1, p.z);
            m.move(0, -1, 0);
        }
        return new Vec3(p.x, this.getY(), p.z);
    }

    private void azotar() {
        this.playSound(SoundEvents.GENERIC_EXPLODE, 4.0f, 0.5f);
        this.playSound(SoundEvents.RAVAGER_STUNNED, 3.0f, 0.4f);
        Vec3 frente = this.position().add(Vec3.directionFromRotation(0, this.getYRot()).scale(5.0));
        polvo(frente, 60);
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, new AABB(frente, frente).inflate(6, 3, 6), this::valido)) {
            e.hurt(this.damageSources().mobAttack(this), DANO_AZOTE);
            Vec3 afuera = e.position().subtract(frente);
            lanzar(e, new Vec3(afuera.x, 0, afuera.z).normalize().scale(1.2), 1.0);
        }
        if (this.level() instanceof ServerLevel sl)
            this.ola = new Ola(sl, this, frente, segundaFase() ? 36 : 28);
    }

    // ------------------------------------------------------------------ ayudas

    static void lanzar(LivingEntity e, Vec3 horizontal, double arriba) {
        e.setDeltaMovement(horizontal.x, arriba, horizontal.z);
        e.hasImpulse = true;
        e.hurtMarked = true;                      // a un jugador le llega el empujon
    }

    private void polvo(Vec3 p, int n) {
        if (this.level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, p.x, p.y + 0.3, p.z, n / 3, 1.5, 0.3, 1.5, 0.02);
            sl.sendParticles(new DustParticleOptions(new Vector3f(0.55f, 0.35f, 0.85f), 2.0f), p.x, p.y + 0.5, p.z, n, 2.0, 0.4, 2.0, 0.0);
        }
    }

    private void quieto(LivingEntity objetivo) {
        this.getMoveControl().setWantedPosition(this.getX(), this.getY(), this.getZ(), 0.0);
        this.getNavigation().stop();
        if (objetivo != null && getEstado() != Estado.MUERTE)
            this.getLookControl().setLookAt(objetivo, 10f, 10f);
    }

    private void mirarA(Vec3 p) {
        Vec3 d = p.subtract(this.position());
        if (d.horizontalDistanceSqr() > 1e-4)
            fijarGiro((float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f);
    }

    private void girarA(Vec3 d) {
        if (d.horizontalDistanceSqr() > 1e-4)
            fijarGiro((float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f);
        this.getMoveControl().setWantedPosition(this.getX(), this.getY(), this.getZ(), 0.0);
    }

    private void fijarGiro(float yaw) {
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    // ------------------------------------------------------------------ dano, muerte y barra

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (getEstado() == Estado.ATORADO)
            cantidad *= 2f;                       // la ventana de castigo: con los cuernos atorados
        if (fuente.getDirectEntity() instanceof PuaCayendo)
            return false;
        return super.hurt(fuente, cantidad);
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (!this.level().isClientSide)
            cambiar(Estado.MUERTE);
        if (this.ola != null)
            this.ola.terminar();
    }

    @Override
    protected void tickDeath() {
        this.deathTime++;
        if (this.level() instanceof ServerLevel sl && this.deathTime % 5 == 0)
            sl.sendParticles(new DustParticleOptions(new Vector3f(0.55f, 0.35f, 0.85f), 2.5f), this.getX(), this.getY() + 2,
                    this.getZ(), 30, 3, 2, 3, 0.0);
        if (this.deathTime >= T_MUERTE && !this.level().isClientSide()) {
            this.level().broadcastEntityEvent(this, (byte) 60);
            this.remove(Entity.RemovalReason.KILLED);
        }
    }

    @Override
    public void startSeenByPlayer(ServerPlayer jugador) {
        super.startSeenByPlayer(jugador);
        this.barra.addPlayer(jugador);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer jugador) {
        super.stopSeenByPlayer(jugador);
        this.barra.removePlayer(jugador);
    }

    @Override
    public void remove(Entity.RemovalReason razon) {
        if (this.ola != null && razon.shouldDestroy())        // al descargarse no: esos bloques se borran al cargar
            this.ola.terminar();
        super.remove(razon);
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return this.getBoundingBox().inflate(6.5, 2.0, 6.5);      // la cola y la cabeza salen de la caja
    }

    @Override
    public boolean causeFallDamage(float distancia, float multiplicador, DamageSource fuente) {
        return false;
    }

    @Override
    public boolean removeWhenFarAway(double distancia) {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("Embestidas", this.embestidas);
        tag.putBoolean("Rugio", this.rugioAlEmpezar);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.embestidas = tag.getInt("Embestidas");
        this.rugioAlEmpezar = tag.getBoolean("Rugio");
        if (this.hasCustomName())
            this.barra.setName(this.getDisplayName());
    }

    // ------------------------------------------------------------------ animaciones (GeckoLib)

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
        controladores.add(new AnimationController<>(this, "principal", 4, this::animar)
                .setAnimationSpeedHandler(c -> c.velocidadDeAnimacion()));
    }

    /** Caminar y galopar van al paso de lo que avanza de verdad (asi los pies no patinan). */
    private double velocidadDeAnimacion() {
        double v = Math.hypot(this.getX() - this.xo, this.getZ() - this.zo);     // lo que avanzo este tick
        return switch (getEstado()) {
            case ACECHAR, QUIETO -> Mth.clamp(v / PASO_CAMINAR, 0.6, 2.5);
            case EMBESTIR -> Mth.clamp(v / PASO_GALOPE, 1.0, 3.0);
            default -> 1.0;
        };
    }

    private PlayState animar(AnimationState<CrackatosEntity> estado) {
        RawAnimation a = switch (getEstado()) {
            case QUIETO, ACECHAR -> estado.isMoving() ? A_CAMINAR : A_QUIETO;
            case RUGIDO -> A_RUGIDO;
            case RASCAR -> A_RASCAR;
            case EMBESTIR -> A_EMBESTIR;
            case CHOCAR, ATORADO -> A_ATORADO;
            case ZAFARSE -> A_ZAFARSE;
            case CABEZAZO -> A_CABEZAZO;
            case SACUDIDA -> A_SACUDIDA;
            case ALZARSE -> A_ALZARSE;
            case MUERTE -> A_MUERTE;
        };
        return estado.setAndContinue(a);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
