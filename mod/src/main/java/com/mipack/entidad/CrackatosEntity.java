package com.mipack.entidad;

import com.mipack.Amenaza;
import com.mipack.Golpes;
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
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.BodyRotationControl;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
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
 * Crackatos, la bestia de piedra amatista: un jefe de esquivar para muchos jugadores.
 * <ul>
 * <li>Reparte el foco: despues de cada ataque escoge a otro (le gusta el que le pega y el que hace mas que no
 *     persigue, ver Amenaza), y ve hasta 96 bloques.</li>
 * <li>RASCAR: el aviso de la estampida. Marca en el piso el camino (una linea morada) y todos los que esten en ese
 *     camino se alentan: hay que salirse a tiempo.</li>
 * <li>EMBESTIR: la estampida. Acelera y no se detiene hasta toparse con una pared (o despues de 180 bloques); a todo lo
 *     que se lleva en el camino le pega mas mientras mas lleva corriendo. Contra la pared se le atoran los cuernos
 *     (ATORADO: recibe el doble de dano) y luego se zafa.</li>
 * <li>SACUDIDA: salen puas volando del lomo y caen del cielo por toda la arena (con circulo de aviso). Cada pua que te
 *     pega te deja ESQUIRLAS (EfectosCrackatos): quitan vida hasta que Crackatos muere.</li>
 * <li>ALZARSE: se para en dos patas y azota; la ola recorre la arena y avienta a quien este en el piso.</li>
 * <li>Fase 2 (mitad de vida): ruge, sus cristales brillan, se rodea de bruma de amatista, salen acaros de amatista
 *     de la bruma, embiste mas rapido y en la estampida va soltando puas.</li>
 * </ul>
 * Sus golpes atraviesan la armadura (Proteccion si cuenta) y tiran el escudo. Vida: 1500 mas 900 por jugador.
 * Los tiempos (en ticks) son los de sus animaciones (taller/personajes/crackatos_anim.py).
 */
public class CrackatosEntity extends Monster implements GeoEntity {
    public enum Estado { QUIETO, RUGIDO, ACECHAR, RASCAR, EMBESTIR, CHOCAR, ATORADO, ZAFARSE, CABEZAZO, SACUDIDA, ALZARSE, MUERTE }

    // duraciones de las animaciones (ticks) y los momentos clave
    private static final int T_RUGIDO = 36, T_RASCAR = 30, T_FIJA = 20, T_CHOCAR = 10, T_ATORADO = 80;
    private static final int T_ZAFARSE = 16, T_CABEZAZO = 14, T_SACUDIDA = 44, T_SALEN_PUAS = 32, T_ALZARSE = 52;
    private static final int T_AZOTE = 31, T_MUERTE = 50;
    // vida: base mas lo que suma cada jugador que entra a la pelea
    private static final float VIDA_BASE = 1500f, VIDA_POR_JUGADOR = 900f;
    private static final double RADIO_PELEA = 64.0, VISTA = 96.0;
    // dano (atraviesa la armadura): la embestida crece con lo que lleva corriendo, hasta el triple
    private static final float DANO_EMBESTIDA = 16f, DANO_PISOTON = 12f, DANO_AZOTE = 18f, DANO_CORNADA = 16f;
    private static final double CRECE_EMBESTIDA = 18.0;            // bloques corridos por cada vez mas de dano
    // la estampida: arranca, acelera y corre hasta una pared (o hasta MAX_ESTAMPIDA bloques)
    private static final double V0 = 0.7, ACELERA = 0.05, VMAX = 1.9, VMAX_FASE2 = 2.3, MAX_ESTAMPIDA = 180.0;
    // cada cuanto puede repetir (ticks): el azote y la cornada de cerca
    private static final int ENFRIAR_ALZARSE = 220, ENFRIAR_CORNADA = 60, T_GOLPE_CORNADA = 4;
    private static final int MAX_SIN_EMBESTIR = 160;              // si lleva tanto sin embestir, embiste aunque este cerca

    /** Cuanto crece el modelo en el juego (el render lo usa; las animaciones van al paso de esta escala). */
    public static final float ESCALA = 4.5f;
    /** Lo que crecio respecto al tamano con el que se diseñaron los alcances (escala 2): todo se multiplica por esto. */
    private static final float K = ESCALA / 2f;
    // que tan rapido gira (grados por tick): caminando, apuntando la embestida, la cornada y quieto mirando
    private static final float GIRO_CAMINAR = 4.5f, GIRO_APUNTAR = 6.5f, GIRO_CORNADA = 10f, GIRO_QUIETO = 2.5f;
    // a que velocidad (bloques por tick) avanza el cuerpo en las animaciones de caminar y galopar a velocidad 1:
    // el pie apoyado recorre su zancada (7 y 14 px del modelo) en lo que dura el apoyo (0.7 de 1.6 s, 0.42 de 0.6 s)
    private static final double PASO_CAMINAR = 7.0 / (0.7 * 1.6) * ESCALA / 16 / 20;
    private static final double PASO_GALOPE = 14.0 / (0.42 * 0.6) * ESCALA / 16 / 20;

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(CrackatosEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> FASE2 = SynchedEntityData.defineId(CrackatosEntity.class, EntityDataSerializers.BOOLEAN);

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
    private final Amenaza amenaza = new Amenaza();

    private int ticksEnEstado;
    private Vec3 direccion = Vec3.ZERO;
    private double recorrido, largoCamino;
    private int embestidas;
    private int embestidasAntesDeSacudir = 2;
    private int alzadasPendientes;
    private int enfriarAlzarse = 100, enfriarCornada, sinEmbestir, enfriarAcaros, enfriarLluvia;
    private boolean cornada;                       // el cabezazo es la cornada de cerca (no el remate de una embestida)
    private boolean rugioAlEmpezar, rugioFase2;
    private int maxJugadores;
    private final Set<UUID> golpeados = new HashSet<>();
    private final EnumSet<Estado> visitados = EnumSet.noneOf(Estado.class);
    private final List<UUID> acaros = new ArrayList<>();
    private final Set<UUID> objetivos = new HashSet<>();           // para las pruebas: a quienes ha perseguido
    private Ola ola;

    public CrackatosEntity(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.setMaxUpStep(1.5f * K);
        this.moveControl = new MovimientoPesado(this);
        this.xpReward = 900;
        this.setPersistenceRequired();
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, VIDA_BASE)
                .add(Attributes.ARMOR, 14.0)
                .add(Attributes.ARMOR_TOUGHNESS, 8.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.26)
                .add(Attributes.FOLLOW_RANGE, VISTA)
                .add(Attributes.ATTACK_DAMAGE, DANO_EMBESTIDA);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, Estado.QUIETO.ordinal());
        this.entityData.define(FASE2, false);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));        // el objetivo lo escoge el mismo (Amenaza)
    }

    public Estado getEstado() {
        return Estado.values()[this.entityData.get(ESTADO)];
    }

    /** Fase 2: cristales que brillan, bruma y acaros (el cliente lo usa para dibujarlo). */
    public boolean fase2() {
        return this.entityData.get(FASE2);
    }

    /** Para las pruebas: por que estados ha pasado, cuanto lleva en el de ahora y a cuantos ha perseguido. */
    public Set<Estado> visitados() {
        return this.visitados;
    }

    public int ticksEnEstado() {
        return this.ticksEnEstado;
    }

    public int perseguidos() {
        return this.objetivos.size();
    }

    private void cambiar(Estado nuevo) {
        if (Mipack.PRUEBA)
            Mipack.LOGGER.info("[Crackatos] {} -> {} (vida {})", getEstado(), nuevo, (int) getHealth());
        this.entityData.set(ESTADO, nuevo.ordinal());
        this.ticksEnEstado = 0;
        this.visitados.add(nuevo);
    }

    private boolean valido(LivingEntity e) {
        if (e == null || !e.isAlive() || e == this || e instanceof CrackatosEntity || e instanceof AcaroAmatista)
            return false;
        if (e instanceof Player p)
            return !p.isCreative() && !p.isSpectator();
        // en las pruebas tambien caza mobs (pero no a otros jefes ni a lo suyo)
        return Mipack.PRUEBA && e instanceof Mob && !(e instanceof com.mipack.khaset.KhasetEntity)
                && !(e instanceof com.mipack.khaset.Xiuhcoatl) && !(e instanceof com.mipack.khaset.GuerreroCalavera);
    }

    private List<LivingEntity> enemigos(double radio) {
        return this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(radio, radio * 0.5, radio), this::valido);
    }

    private boolean segundaFase() {
        return this.getHealth() < this.getMaxHealth() * 0.5f;
    }

    /** Escoge a quien ir. 'cambiar': acaba de atacar, asi que va por otro si hay. */
    private LivingEntity escoger(boolean cambiar) {
        List<LivingEntity> c = enemigos(VISTA);
        LivingEntity e = this.amenaza.escoger(this, c, cambiar, 40.0, this.level().getGameTime(), this.random);
        this.setTarget(e);
        if (e != null && this.objetivos.add(e.getUUID()) && Mipack.PRUEBA)
            Mipack.LOGGER.info("[Crackatos] persigue a {} ({} distintos)", e.getName().getString(), this.objetivos.size());
        return e;
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
        if (this.enfriarAcaros > 0)
            this.enfriarAcaros--;
        if (this.enfriarLluvia > 0)
            this.enfriarLluvia--;
        if (this.tickCount % 20 == 0) {
            participantes();
            this.amenaza.olvidar();
        }
        if (getEstado() == Estado.ACECHAR || (getEstado() == Estado.CABEZAZO && cornada))
            this.sinEmbestir++;
        LivingEntity objetivo = this.getTarget();
        if (!valido(objetivo) || objetivo.distanceTo(this) > VISTA)
            objetivo = objetivo != null || this.tickCount % 10 == 0 ? escoger(false) : null;
        else if (getEstado() == Estado.ACECHAR && this.ticksEnEstado % 160 == 159)
            objetivo = escoger(true);                             // nadie se queda sin su visita
        if (segundaFase() && !fase2() && (getEstado() == Estado.ACECHAR || getEstado() == Estado.QUIETO)) {
            this.entityData.set(FASE2, true);
            this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 4.0f, 0.4f);
            cambiar(Estado.RUGIDO);
            rugioFase2 = true;
        }
        switch (getEstado()) {
            case QUIETO -> {
                if (objetivo != null)
                    cambiar(rugioAlEmpezar ? Estado.ACECHAR : Estado.RUGIDO);
            }
            case RUGIDO -> {
                rugioAlEmpezar = true;
                quieto(objetivo);
                if (ticksEnEstado == 8)
                    this.playSound(SoundEvents.RAVAGER_ROAR, 5.0f, 0.5f);
                if (ticksEnEstado == 20 && rugioFase2) {
                    rugioFase2 = false;
                    acaros(4);
                }
                if (ticksEnEstado >= T_RUGIDO)
                    cambiar(Estado.ACECHAR);
            }
            case ACECHAR -> acechar(objetivo);
            case RASCAR -> rascar(objetivo);
            case EMBESTIR -> embestir();
            case CHOCAR -> {
                quedarse();
                if (ticksEnEstado >= T_CHOCAR)
                    cambiar(Estado.ATORADO);
            }
            case ATORADO -> {
                quedarse();
                if (ticksEnEstado % 20 == 10)
                    this.playSound(SoundEvents.RAVAGER_STUNNED, 2.5f, 0.7f);
                if (ticksEnEstado >= (fase2() ? T_ATORADO - 20 : T_ATORADO))
                    cambiar(Estado.ZAFARSE);
            }
            case ZAFARSE -> {
                quedarse();
                if (ticksEnEstado == 3) {
                    this.playSound(SoundEvents.ZOMBIE_BREAK_WOODEN_DOOR, 2.5f, 0.5f);
                    polvo(this.position().add(this.direccion.scale(6.0 * K)).add(0, 2 * K, 0), 30);
                }
                if (ticksEnEstado >= T_ZAFARSE)
                    terminarEmbestida();
            }
            case CABEZAZO -> {
                if (cornada && ticksEnEstado < T_GOLPE_CORNADA && objetivo != null)
                    girarHacia(objetivo.position(), GIRO_CORNADA);
                else
                    quedarse();
                this.direccion = adelante();
                if (cornada && ticksEnEstado == T_GOLPE_CORNADA)
                    cornear();
                if (ticksEnEstado >= T_CABEZAZO) {
                    escoger(true);
                    cambiar(Estado.ACECHAR);
                }
            }
            case SACUDIDA -> {
                quieto(objetivo);
                if (ticksEnEstado == 8)
                    this.playSound(SoundEvents.AMETHYST_BLOCK_RESONATE, 4.0f, 0.5f);
                if (ticksEnEstado == T_SALEN_PUAS)
                    lanzarPuas();
                if (ticksEnEstado >= T_SACUDIDA) {
                    embestidas = 0;
                    embestidasAntesDeSacudir = 2 + this.random.nextInt(2);
                    if (segundaFase())
                        alzadasPendientes++;
                    escoger(true);
                    cambiar(Estado.ACECHAR);
                }
            }
            case ALZARSE -> {
                quieto(ticksEnEstado < T_AZOTE - 8 ? objetivo : null);
                if (ticksEnEstado == 6)
                    this.playSound(SoundEvents.RAVAGER_ROAR, 5.0f, 0.45f);
                if (ticksEnEstado == T_AZOTE)
                    azotar();
                if (ticksEnEstado >= T_ALZARSE) {
                    escoger(true);
                    cambiar(Estado.ACECHAR);
                }
            }
            case MUERTE -> {
            }
        }
        if (fase2() && getEstado() != Estado.MUERTE)
            faseDos();
        if (this.ola != null && this.ola.tick())
            this.ola = null;
        this.barra.setProgress(this.getHealth() / this.getMaxHealth());
    }

    /** Quien entra a la pelea suma vida (nunca baja): 1500 mas 900 por jugador. */
    private void participantes() {
        int n = 0;
        for (Player p : this.level().players())
            if (valido(p) && p.distanceToSqr(this) < RADIO_PELEA * RADIO_PELEA)
                n++;
        if (n > this.maxJugadores) {
            float antes = this.getMaxHealth();
            this.maxJugadores = n;
            float ahora = VIDA_BASE + VIDA_POR_JUGADOR * n;
            this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(ahora);
            this.setHealth(this.getHealth() * ahora / antes);
        }
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
        if (ticksEnEstado % 10 == 0)
            pisoton();
        if (ticksEnEstado < 14)
            return;
        double cerca = this.getBbWidth() * 0.5 + 3.5;
        if (embestidas >= embestidasAntesDeSacudir) {
            cambiar(Estado.SACUDIDA);
        } else if (alzadasPendientes > 0 && ticksEnEstado > 24) {
            alzadasPendientes--;
            alzarse();
        } else if (sinEmbestir > MAX_SIN_EMBESTIR) {
            cambiar(Estado.RASCAR);               // no se queda nomas corneando: tambien embiste de cerca
        } else if (dist < cerca && enfriarCornada == 0) {
            // de cerca: la cornada (el cabezazo hacia arriba), que avienta para que no se le pueda pegar nomas
            this.cornada = true;
            this.enfriarCornada = ENFRIAR_CORNADA;
            cambiar(Estado.CABEZAZO);
        } else if (enemigos(10 * K).size() >= 3 && enfriarAlzarse == 0 && ticksEnEstado > 30) {
            alzarse();                            // muchos juntos: el azote con la ola
        } else if (dist < 10 * K && enfriarAlzarse == 0 && ticksEnEstado > 50) {
            alzarse();
        } else if (dist > cerca + 2 && (ticksEnEstado > 40 || this.random.nextInt(30) == 0) || ticksEnEstado > 120) {
            cambiar(Estado.RASCAR);
        }
    }

    private void alzarse() {
        this.enfriarAlzarse = ENFRIAR_ALZARSE;
        cambiar(Estado.ALZARSE);
    }

    /** Rasca el piso apuntando; marca el camino y alenta a todos los que esten en el. */
    private void rascar(LivingEntity objetivo) {
        if (ticksEnEstado < T_FIJA && objetivo != null)
            girarHacia(objetivo.position(), GIRO_APUNTAR);
        else
            quedarse();
        this.direccion = adelante();
        if (ticksEnEstado == 1 || ticksEnEstado % 4 == 0)
            this.largoCamino = largoHastaPared();
        marcarCamino(ticksEnEstado % 3 == 0);
        if (ticksEnEstado % 12 == 6) {
            this.playSound(SoundEvents.RAVAGER_STEP, 2.5f, 0.6f);
            polvo(this.position().add(this.direccion.scale(4.0 * K)), 12);
        }
        if (ticksEnEstado >= T_RASCAR) {
            golpeados.clear();
            sinEmbestir = 0;
            recorrido = 0;
            if (Mipack.PRUEBA && objetivo != null)
                Mipack.LOGGER.info("[Crackatos] embiste: blanco a {} bloques, camino de {}, apunta {}",
                        String.format("%.1f", this.distanceTo(objetivo)), String.format("%.0f", this.largoCamino),
                        String.format("%.2f", objetivo.position().subtract(this.position()).normalize().dot(this.direccion)));
            this.playSound(SoundEvents.RAVAGER_ROAR, 4.0f, 0.8f);
            cambiar(Estado.EMBESTIR);
        }
    }

    /** Hasta donde llega la estampida si nada la para: la primera pared en linea recta (o MAX_ESTAMPIDA). */
    private double largoHastaPared() {
        Vec3 desde = this.position().add(0, 2.0 * K, 0);
        Vec3 hasta = desde.add(this.direccion.scale(MAX_ESTAMPIDA));
        BlockHitResult r = this.level().clip(new ClipContext(desde, hasta, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        return r.getType() == HitResult.Type.MISS ? MAX_ESTAMPIDA : r.getLocation().distanceTo(desde);
    }

    /** Lo que va a recorrer: una franja del ancho de su cuerpo. Quien este dentro se alenta (y la ve en el piso). */
    private void marcarCamino(boolean dibujar) {
        double medio = this.getBbWidth() * 0.5 + 1.0;
        Vec3 lado = new Vec3(-this.direccion.z, 0, this.direccion.x);
        for (LivingEntity e : enemigos(this.largoCamino + 4)) {
            Vec3 d = e.position().subtract(this.position());
            double a = d.dot(this.direccion), l = Math.abs(d.dot(lado));
            if (a > 0 && a < this.largoCamino + 2 && l < medio && Math.abs(d.y) < 4 * K)
                e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 12, 1, false, false, true));
        }
        if (!dibujar || !(this.level() instanceof ServerLevel sl))
            return;
        // la linea se manda a todos los que esten en la pelea aunque esten lejos (las particulas normales solo llegan a 32)
        DustParticleOptions polvo = new DustParticleOptions(new Vector3f(0.75f, 0.35f, 1.0f), 3.0f);
        List<ServerPlayer> ven = new ArrayList<>();
        for (ServerPlayer sp : sl.players())
            if (sp.distanceToSqr(this) < 96 * 96)
                ven.add(sp);
        for (double a = this.getBbWidth() * 0.5; a < Math.min(this.largoCamino, 90); a += 2.5)
            for (int s = -1; s <= 1; s += 2) {
                Vec3 p = this.position().add(this.direccion.scale(a)).add(lado.scale(s * medio));
                for (ServerPlayer sp : ven)
                    sl.sendParticles(sp, polvo, true, p.x, this.getY() + 0.25, p.z, 2, 0.15, 0.05, 0.15, 0.0);
            }
    }

    /** La cornada: lo que este enfrente de la cabeza sale volando para arriba. */
    private void cornear() {
        Vec3 c = this.position().add(this.direccion.scale(this.getBbWidth() * 0.5 + 1.2 * K));
        AABB zona = new AABB(c.x - 2.5 * K, this.getY() - 0.5, c.z - 2.5 * K, c.x + 2.5 * K, this.getY() + 4.5 * K, c.z + 2.5 * K);
        boolean pego = false;
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, zona, this::valido)) {
            Golpes.pegar(e, this, DANO_CORNADA, 100);
            lanzar(e, this.direccion.scale(1.0), 1.2);
            pego = true;
        }
        this.playSound(pego ? SoundEvents.RAVAGER_ATTACK : SoundEvents.RAVAGER_STEP, 3.0f, 0.7f);
    }

    private void embestir() {
        quedarse();
        double vmax = fase2() ? VMAX_FASE2 : VMAX;
        double velocidad = Math.min(vmax, V0 + ACELERA * ticksEnEstado);
        Vec3 antes = this.position();
        this.move(MoverType.SELF, new Vec3(this.direccion.x * velocidad, 0, this.direccion.z * velocidad));
        double avance = this.position().subtract(antes).dot(this.direccion);     // si roza una pared se resbala
        this.recorrido += Math.max(0, avance);
        if (ticksEnEstado < 10)
            marcarCamino(false);                  // al arrancar todavia alenta a los que siguen en el camino
        if (ticksEnEstado % 4 == 0) {
            this.playSound(SoundEvents.RAVAGER_STEP, 3.0f, 0.5f);
            pisoton();
        }
        if (fase2() && ticksEnEstado % 6 == 0 && this.level() instanceof ServerLevel sl) {
            Vec3 atras = this.position().subtract(this.direccion.scale(this.getBbWidth()))
                    .add((this.random.nextDouble() - 0.5) * 8, 0, (this.random.nextDouble() - 0.5) * 8);
            sl.addFreshEntity(PuaCayendo.cayendo(sl, this, piso(atras), 16));
        }
        // todo lo que alcanza: dano que crece con lo que lleva corriendo, y sale aventado de lado
        float dano = DANO_EMBESTIDA * (float) (1.0 + Math.min(2.0, this.recorrido / CRECE_EMBESTIDA));
        Vec3 lado = new Vec3(-this.direccion.z, 0, this.direccion.x);
        AABB frente = this.getBoundingBox().inflate(1.0 * K, 0.0, 1.0 * K).move(this.direccion.x * 1.2 * K, 0, this.direccion.z * 1.2 * K);
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, frente, this::valido)) {
            if (golpeados.add(e.getUUID())) {
                Golpes.pegar(e, this, dano, 160);
                double s = Math.signum(e.position().subtract(this.position()).dot(lado));
                lanzar(e, this.direccion.scale(1.6).add(lado.scale((s == 0 ? 1 : s) * 1.2)), 1.3);
                this.playSound(SoundEvents.RAVAGER_ATTACK, 3.0f, 0.6f);
            }
        }
        // se estrello: los cuernos se atoran en la pared (se ve por la cabeza, que va mas adelante que la caja)
        boolean cabeza = cabezaEnPared(), frenado = avance < velocidad * 0.35;
        if ((cabeza || frenado) && ticksEnEstado > 3) {
            if (Mipack.PRUEBA)
                Mipack.LOGGER.info("[Crackatos] choca despues de {} bloques (cabeza {}, frenado {}) en {}",
                        String.format("%.0f", this.recorrido), cabeza, frenado, this.blockPosition());
            this.playSound(SoundEvents.ANVIL_LAND, 3.0f, 0.5f);
            this.playSound(SoundEvents.GENERIC_EXPLODE, 2.0f, 0.7f);
            BlockPos pared = BlockPos.containing(this.position().add(this.direccion.scale(this.getBbWidth() * 0.5 + 1.0)).add(0, 2 * K, 0));
            BlockState bloque = this.level().getBlockState(pared);
            if (this.level() instanceof ServerLevel sl && !bloque.isAir())
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, bloque), pared.getX() + 0.5, pared.getY() + 0.5,
                        pared.getZ() + 0.5, 100, 1.5 * K, 1.5 * K, 1.5 * K, 0.2);
            cambiar(Estado.CHOCAR);
            return;
        }
        if (this.recorrido >= MAX_ESTAMPIDA || ticksEnEstado > 400)
            terminarEmbestida();                  // sin pared en todo el camino: se para y voltea
    }

    /** Si lo de enfrente de la caja (donde van la cabeza y los cuernos) ya pega con algo solido. */
    private boolean cabezaEnPared() {
        Vec3 c = this.position().add(this.direccion.scale(this.getBbWidth() * 0.5 + 0.9 * K));
        AABB cabeza = new AABB(c.x - 0.9 * K, this.getY() + 1.4 * K, c.z - 0.9 * K, c.x + 0.9 * K, this.getY() + 4.2 * K, c.z + 0.9 * K)
                .expandTowards(this.direccion.x * 0.5 * K, 0, this.direccion.z * 0.5 * K);
        return !this.level().noCollision(this, cabeza);
    }

    private void terminarEmbestida() {
        embestidas++;
        escoger(true);                            // despues de cada estampida va por otro
        cambiar(Estado.ACECHAR);
    }

    /** Lo que quede bajo sus patas recibe dano y sale empujado. */
    private void pisoton() {
        AABB b = this.getBoundingBox();
        AABB pies = new AABB(b.minX, b.minY, b.minZ, b.maxX, b.minY + 1.4 * K, b.maxZ);
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, pies, this::valido)) {
            Golpes.pegar(e, this, DANO_PISOTON, 100);
            Vec3 afuera = e.position().subtract(this.position());
            lanzar(e, new Vec3(afuera.x, 0, afuera.z).normalize().scale(1.0), 0.45);
        }
    }

    private void lanzarPuas() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        this.playSound(SoundEvents.AMETHYST_CLUSTER_BREAK, 5.0f, 0.5f);
        // las que salen volando del lomo (solo se ven: el modelo no pierde ninguna)
        for (int i = 0; i < 18; i++) {
            Vec3 p = this.position().add((this.random.nextDouble() - 0.5) * 6 * K, 5.5 * K, (this.random.nextDouble() - 0.5) * 8 * K);
            sl.addFreshEntity(PuaCayendo.subiendo(sl, p, new Vec3((this.random.nextDouble() - 0.5) * 0.7, 1.5, (this.random.nextDouble() - 0.5) * 0.7)));
        }
        // las que caen: encima de cada uno y alrededor, y muchas mas por toda la arena (en tandas, unos 3 s)
        List<Vec3> blancos = new ArrayList<>();
        List<LivingEntity> todos = enemigos(RADIO_PELEA);
        for (LivingEntity e : todos) {
            blancos.add(e.position());
            for (int i = 0; i < 3; i++)
                blancos.add(deEsteLado(e.position().add((this.random.nextDouble() - 0.5) * 10, 0, (this.random.nextDouble() - 0.5) * 10)));
        }
        int extra = (fase2() ? 40 : 26) + 3 * todos.size();
        for (int i = 0; i < extra; i++) {
            double ang = this.random.nextDouble() * Math.PI * 2, r = (3 + this.random.nextDouble() * 16) * K;
            blancos.add(deEsteLado(this.position().add(Math.cos(ang) * r, 0, Math.sin(ang) * r)));
        }
        for (int i = 0; i < Math.min(130, blancos.size()); i++)
            sl.addFreshEntity(PuaCayendo.cayendo(sl, this, piso(blancos.get(i)), 18 + this.random.nextInt(50)));
    }

    /** Fase 2: la bruma suelta acaros cada tanto y caen puas sueltas sobre los que esten lejos. */
    private void faseDos() {
        if (this.enfriarAcaros == 0 && getEstado() != Estado.RUGIDO) {
            this.acaros.removeIf(u -> !(((ServerLevel) this.level()).getEntity(u) instanceof AcaroAmatista a) || !a.isAlive());
            int tope = Math.min(16, 4 + 2 * Math.max(1, this.maxJugadores));
            if (this.acaros.size() < tope)
                acaros(Math.min(tope - this.acaros.size(), 3 + this.maxJugadores / 2));
            this.enfriarAcaros = 240;
        }
        if (this.enfriarLluvia == 0 && this.level() instanceof ServerLevel sl) {
            for (LivingEntity e : enemigos(RADIO_PELEA))
                if (e.distanceTo(this) > 12 * K || this.random.nextBoolean())
                    sl.addFreshEntity(PuaCayendo.cayendo(sl, this, piso(e.position()), 24));
            this.enfriarLluvia = 120;
        }
    }

    /** Salen acaros de amatista de la bruma alrededor de el. */
    private void acaros(int n) {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        for (int i = 0; i < n; i++) {
            double ang = this.random.nextDouble() * Math.PI * 2, r = this.getBbWidth() * 0.6 + this.random.nextDouble() * 4 * K;
            Vec3 p = piso(this.position().add(Math.cos(ang) * r, 0, Math.sin(ang) * r));
            AcaroAmatista a = Mipack.ACARO.get().create(sl);
            if (a == null)
                return;
            a.moveTo(p.x, p.y, p.z, this.random.nextFloat() * 360f, 0f);
            a.deJefe(this);
            LivingEntity t = this.getTarget();
            if (t != null)
                a.setTarget(t);
            sl.addFreshEntity(a);
            this.acaros.add(a.getUUID());
            sl.sendParticles(new DustParticleOptions(new Vector3f(0.62f, 0.32f, 0.95f), 2.0f), p.x, p.y + 0.3, p.z, 12, 0.4, 0.2, 0.4, 0.0);
        }
        this.playSound(SoundEvents.AMETHYST_BLOCK_CHIME, 3.0f, 0.6f);
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
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos(p.x, Math.max(this.getY(), p.y) + 3 * K, p.z);
        for (int i = 0; i < 12 * K; i++) {
            if (!this.level().getBlockState(m).isAir() && this.level().getBlockState(m.above()).isAir())
                return new Vec3(p.x, m.getY() + 1, p.z);
            m.move(0, -1, 0);
        }
        return new Vec3(p.x, this.getY(), p.z);
    }

    private void azotar() {
        this.playSound(SoundEvents.GENERIC_EXPLODE, 5.0f, 0.5f);
        this.playSound(SoundEvents.RAVAGER_STUNNED, 4.0f, 0.4f);
        Vec3 frente = this.position().add(adelante().scale(5.0 * K));
        polvo(frente, 60);
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, new AABB(frente, frente).inflate(6 * K, 3 * K, 6 * K), this::valido)) {
            Golpes.pegar(e, this, DANO_AZOTE, 100);
            Vec3 afuera = e.position().subtract(frente);
            lanzar(e, new Vec3(afuera.x, 0, afuera.z).normalize().scale(1.3), 1.1);
        }
        if (this.level() instanceof ServerLevel sl)
            this.ola = new Ola(sl, this, frente, Math.round((fase2() ? 36 : 28) * K));
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

    /** Parado: no avanza y, si hay objetivo, gira despacio hacia el (una bestia asi no voltea de golpe). */
    private void quieto(LivingEntity objetivo) {
        this.getNavigation().stop();
        if (objetivo != null && getEstado() != Estado.MUERTE)
            girarHacia(objetivo.position(), GIRO_QUIETO);
        else
            quedarse();
    }

    /** Hacia donde mira el cuerpo (en el piso). */
    private Vec3 adelante() {
        return Vec3.directionFromRotation(0, this.getYRot());
    }

    /** Gira hacia un punto como mucho 'max' grados (y no avanza). */
    private void girarHacia(Vec3 p, float max) {
        Vec3 d = p.subtract(this.position());
        if (d.horizontalDistanceSqr() > 1e-4) {
            float deseado = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
            fijarGiro(this.getYRot() + Mth.clamp(Mth.wrapDegrees(deseado - this.getYRot()), -max, max));
        }
        this.getMoveControl().setWantedPosition(this.getX(), this.getY(), this.getZ(), 0.0);
    }

    /** No gira ni avanza (embistiendo, atorado, zafandose: el rumbo ya esta fijo). */
    private void quedarse() {
        this.getMoveControl().setWantedPosition(this.getX(), this.getY(), this.getZ(), 0.0);
    }

    private void fijarGiro(float yaw) {
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    /** El cuerpo y la cabeza siempre van hacia donde va (sin esto, parado, el cuerpo se quedaba girado y se veia chueco). */
    @Override
    protected BodyRotationControl createBodyControl() {
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
                CrackatosEntity.this.yBodyRot = CrackatosEntity.this.getYRot();
                CrackatosEntity.this.yHeadRot = CrackatosEntity.this.getYRot();
            }
        };
    }

    /** Camina como bestia pesada: gira de a poco hacia donde va y casi no avanza si tiene que dar la vuelta. */
    private static final class MovimientoPesado extends MoveControl {
        MovimientoPesado(CrackatosEntity jefe) {
            super(jefe);
        }

        @Override
        public void tick() {
            if (this.operation != MoveControl.Operation.MOVE_TO) {
                this.mob.setZza(0f);
                return;
            }
            this.operation = MoveControl.Operation.WAIT;
            double dx = this.wantedX - this.mob.getX(), dz = this.wantedZ - this.mob.getZ();
            if (dx * dx + dz * dz < 2.5e-7 || this.speedModifier <= 0) {
                this.mob.setZza(0f);
                return;
            }
            float deseado = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90f;
            float giro = Mth.wrapDegrees(deseado - this.mob.getYRot());
            float yaw = this.mob.getYRot() + Mth.clamp(giro, -GIRO_CAMINAR, GIRO_CAMINAR);
            this.mob.setYRot(yaw);
            this.mob.yBodyRot = yaw;
            this.mob.yHeadRot = yaw;
            float alineado = Mth.clamp(1f - Math.abs(giro) / 80f, 0.2f, 1f);
            this.mob.setSpeed((float) (this.speedModifier * this.mob.getAttributeValue(Attributes.MOVEMENT_SPEED)) * alineado);
        }
    }

    // ------------------------------------------------------------------ cliente: la bruma de la fase 2

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide && fase2() && getEstado() != Estado.MUERTE) {
            DustParticleOptions bruma = new DustParticleOptions(new Vector3f(0.6f, 0.3f, 0.95f), 4.0f);
            DustParticleOptions clara = new DustParticleOptions(new Vector3f(0.85f, 0.6f, 1.0f), 3.0f);
            for (int i = 0; i < 16; i++) {                         // la bruma: un anillo espeso al ras del piso
                double a = this.random.nextDouble() * Math.PI * 2, r = this.getBbWidth() * (0.45 + this.random.nextDouble() * 0.9);
                this.level().addParticle(i % 4 == 0 ? clara : bruma, this.getX() + Math.cos(a) * r,
                        this.getY() + this.random.nextDouble() * (i % 3 == 0 ? 3.0 * K : 1.2 * K), this.getZ() + Math.sin(a) * r,
                        0, 0.02, 0);
            }
            if (this.random.nextInt(3) == 0)
                this.level().addParticle(ParticleTypes.PORTAL, this.getX() + (this.random.nextDouble() - 0.5) * this.getBbWidth(),
                        this.getY() + this.random.nextDouble() * 3 * K, this.getZ() + (this.random.nextDouble() - 0.5) * this.getBbWidth(),
                        0, 0, 0);
        }
    }

    // ------------------------------------------------------------------ dano, muerte y barra

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (fuente.getDirectEntity() instanceof PuaCayendo || fuente.getEntity() instanceof AcaroAmatista)
            return false;
        if (getEstado() == Estado.ATORADO)
            cantidad *= 2f;                       // la ventana de castigo: con los cuernos atorados
        else if (fuente.getDirectEntity() instanceof Projectile)
            cantidad *= 0.75f;                    // la piedra aguanta flechas: hay que acercarse
        boolean pego = super.hurt(fuente, cantidad);
        if (pego && !this.level().isClientSide)
            this.amenaza.golpe(fuente.getEntity(), cantidad);
        return pego;
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (!this.level().isClientSide) {
            cambiar(Estado.MUERTE);
            if (this.level() instanceof ServerLevel sl) {
                EfectosCrackatos.quitarCerca(sl, this);
                for (UUID u : this.acaros)
                    if (sl.getEntity(u) instanceof AcaroAmatista a)
                        a.deshacer(sl);
            }
        }
        if (this.ola != null)
            this.ola.terminar();
    }

    @Override
    protected void tickDeath() {
        this.deathTime++;
        if (this.level() instanceof ServerLevel sl && this.deathTime % 5 == 0)
            sl.sendParticles(new DustParticleOptions(new Vector3f(0.55f, 0.35f, 0.85f), 2.5f), this.getX(), this.getY() + 2,
                    this.getZ(), 30, 3 * K, 2 * K, 3 * K, 0.0);
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
        return this.getBoundingBox().inflate(6.5 * K, 2.0 * K, 6.5 * K);      // la cola y la cabeza salen de la caja
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
        tag.putBoolean("Fase2", fase2());
        tag.putInt("Jugadores", this.maxJugadores);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.embestidas = tag.getInt("Embestidas");
        this.rugioAlEmpezar = tag.getBoolean("Rugio");
        this.entityData.set(FASE2, tag.getBoolean("Fase2"));
        this.maxJugadores = tag.getInt("Jugadores");
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
