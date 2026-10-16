package com.mipack.khaset;

import com.mipack.Amenaza;
import com.mipack.Golpes;
import com.mipack.Mipack;
import com.mipack.SonidosMipack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.chat.Component;
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
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Khaset, el ultimo rey de Thza, dios del fuego corrompido: un jefe de raid (10 o mas jugadores) con el estilo de
 * los guerreros jaguar aztecas. No busca matar: hiere (desangrado), derriba, captura y lleva a sus presas al cristal
 * del sacrificio; cada sacrificio calienta la sala. Una segunda barra, el CALOR, sube sola: si llega al tope todos
 * se queman.
 * <ul>
 * <li>Frenesi: entre menos vida, mas rapido ataca (sus animaciones y tiempos van al RITMO de cada ataque) y menos
 *     descansa entre ataques. Avanza mientras tira tajos y barridos. Reparte el foco (ver Amenaza): al que le dispara de
 *     lejos tambien le toca.</li>
 * <li>Ataques: tajos (combo de 3, cada uno desangra), barrido bajo (corte de piernas: te tira de rodillas), salto del
 *     jaguar (hasta 26 bloques; cae sobre el grupo y sale una onda de fuego por el piso: se brinca), dardos de atlatl
 *     en abanico (nubes de veneno corto), guardia del jaguar (bloquea de frente, tambien flechas, y regresa un
 *     contraataque), silbato de la muerte (aturde y desorienta; detras de una columna te salvas) y la Xiuhcoatl (de
 *     dos a seis serpientes).</li>
 * <li>Captura: agarra hasta a dos (derribados o muy heridos), los lleva al cristal y los sacrifica. Cargando sigue
 *     peleando: pisa y saca ondas de fuego; mientras sacrifica hace erupciones bajo los que se acercan. Cargando
 *     recibe el doble de dano y si le bajan el 5 % de su vida suelta. El agarrado puede zafarse con la barra (3
 *     aciertos; cada fallo le quita la mitad de la vida). El totem salva del sacrificio (y te suelta).</li>
 * <li>Fase 2, la corona rota (50 %): se le rompen el yelmo y el penacho y sigue igual pero mas rapido; sus dardos son
 *     astillas de obsidiana. Fase 3, el Quinto Sol (20 %): el calor sube al doble, sacrifica donde captura y salen
 *     del piso guerreros calavera con macuahuitl.</li>
 * </ul>
 * Vida: 2000 mas 1200 por jugador. Sus golpes atraviesan la armadura (Proteccion si cuenta) y tiran el escudo.
 * Todos los tiempos y las posiciones de las manos vienen de sus animaciones (PosesKhaset).
 */
public class KhasetEntity extends Monster implements GeoEntity {
    public enum Estado {
        QUIETO("quieto", true), CAMINAR("acechar", true), CORRER("correr", true), TAJOS("zarpazos", false),
        BARRIDO("barrido", false), BARRIDO_I("barrido_i", false), SALTO("abalanzarse", false),
        DARDO("lanzar_dardo", false), GUARDIA("guardia", true), CONTRA("contraataque", false), SILBATO("grito", false),
        AGARRAR("agarrar", false), AGARRAR_DOS("agarrar_dos", false), CARGAR("cargar", true),
        CARGAR_DOS("cargar_dos", true), SOLTAR("soltar", false), SALTO_ALTAR("abalanzarse", false),
        SACRIFICIO("sacrificio", false), INVOCAR("invocar", false), CORONA("corona_rota", false),
        MUERTE("muerte", false), PISOTON("pisoton", false), PISOTON_DOS("pisoton_dos", false);

        public final String anim;
        public final boolean bucle;
        final RawAnimation raw;

        Estado(String anim, boolean bucle) {
            this.anim = anim;
            this.bucle = bucle;
            String n = "animation.khaset." + anim;
            this.raw = bucle ? RawAnimation.begin().thenLoop(n)
                    : anim.equals("muerte") || anim.startsWith("agarrar") ? RawAnimation.begin().thenPlayAndHold(n)
                    : RawAnimation.begin().thenPlay(n);
        }

        public boolean cargando() {
            return this == CARGAR || this == CARGAR_DOS || this == SALTO_ALTAR || this == SACRIFICIO
                    || this == PISOTON || this == PISOTON_DOS;
        }
    }

    public static final float ESCALA = PosesKhaset.escala();
    // vida: base mas lo que suma cada jugador que entra a la pelea
    private static final float VIDA_BASE = 2000f, VIDA_POR_JUGADOR = 1200f;
    private static final double RADIO_PELEA = 48.0;
    // dano (atraviesa la armadura)
    private static final float DANO_TAJO = 11f, DANO_BARRIDO = 12f, DANO_SALTO = 18f, DANO_CONTRA = 14f;
    private static final float DANO_PISOTON = 10f, DANO_ONDA = 8f, DANO_ERUPCION = 12f, DANO_APRETAR = 2f;
    // rescate: lo que hay que bajarle (fraccion de su vida maxima) mientras carga para que suelte
    private static final float RESCATE = 0.05f;
    // calor: cuanto tarda en llenarse (ticks) y cuanto sube cada sacrificio
    private static final float LLENADO_CALOR = 16800f, CALOR_SACRIFICIO = 0.05f;
    // las flechas y demas proyectiles le hacen menos (para que no se le gane nomas de lejos)
    private static final float A_DISTANCIA = 0.6f;
    // giros (grados por tick)
    private static final float GIRO_CAMINAR = 8f, GIRO_APUNTAR = 11f;
    // a que velocidad avanza el cuerpo (bloques por tick) en acechar y correr a velocidad 1 de la animacion
    private static final double PASO_CAMINAR = 16.0 / (0.62 * 2.4) * ESCALA / 16 / 20;
    private static final double PASO_CORRER = 22.0 / (0.4 * 0.7) * ESCALA / 16 / 20;
    private static final double PASO_CARGAR = 14.0 / (0.6 * 1.6) * ESCALA / 16 / 20;
    // el salto: alcance maximo (bloques), radio del golpe al caer y hasta donde llega la onda
    private static final double ALCANCE_SALTO = 26.0, RADIO_SALTO = 7.0, ONDA_SALTO = 13.0;

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> INICIO = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> RITMO = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Boolean> CORONA_ROTA = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Float> CALOR = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> PRESA_D = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> PRESA_I = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> CRISTAL = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final ServerBossEvent barra = new ServerBossEvent(this.getDisplayName(), BossEvent.BossBarColor.RED,
            BossEvent.BossBarOverlay.NOTCHED_10);
    private final ServerBossEvent barraCalor = new ServerBossEvent(Component.translatable("boss.mipack.calor"),
            BossEvent.BossBarColor.YELLOW, BossEvent.BossBarOverlay.NOTCHED_20);
    private final Amenaza amenaza = new Amenaza();

    private int ticksEnEstado;
    /** Lo que va de la animacion del estado (segundos de animacion: avanza RITMO/20 por tick). */
    private float avance, avanceAntes;
    private int fase = 1;
    private BlockPos casa;
    private int maxJugadores;
    private final EnumMap<Estado, Integer> enfriar = new EnumMap<>(Estado.class);
    private final Set<UUID> golpeados = new HashSet<>();
    private final EnumSet<Estado> visitados = EnumSet.noneOf(Estado.class);
    private LivingEntity presaElegida;             // a quien va a capturar
    private Vec3 salida = Vec3.ZERO, destino = Vec3.ZERO;
    private int vuelo, despegue = -1, saltosSeguidos;
    private long agarroEn;
    private float danoEnCarga;
    private int golpesDeFrente, ventanaGolpes, lejosTicks;
    private boolean contraPendiente;
    private boolean soltando;
    private Vec3 tipAnterior;
    private int sacrificados, totems, zafados, guerrerosSalidos;
    private final List<Huella> huellas = new ArrayList<>();
    private final List<Onda> ondas = new ArrayList<>();
    private final List<Erupcion> erupciones = new ArrayList<>();
    private final Map<UUID, Forcejeo> forcejeos = new HashMap<>();
    private final Map<UUID, Long> noAgarrar = new HashMap<>();
    private final List<UUID> guerreros = new ArrayList<>();
    private final Set<UUID> objetivos = new HashSet<>();
    private int ticksAlTope, enfriarGuerreros;

    private record Huella(Vec3 p, long hasta) {
    }

    /** Una onda de fuego que corre por el piso desde 'c' (se esquiva brincando). */
    private static final class Onda {
        final Vec3 c;
        final double max, vel;
        final float dano;
        double r;
        final Set<UUID> golpeados = new HashSet<>();

        Onda(Vec3 c, double max, double vel, float dano) {
            this.c = c;
            this.max = max;
            this.vel = vel;
            this.dano = dano;
            this.r = 1.0;
        }
    }

    private record Erupcion(Vec3 p, long cuando) {
    }

    /** La barra para zafarse de un agarrado. */
    private static final class Forcejeo {
        int aciertos;
        float zona, ancho;
        int periodo;
        long inicio, bloqueo;
    }

    public KhasetEntity(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.setMaxUpStep(3.0f);
        this.moveControl = new Movimiento(this);
        this.xpReward = 1200;
        this.setPersistenceRequired();
        this.barraCalor.setProgress(0f);
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, VIDA_BASE)
                .add(Attributes.ARMOR, 10.0)
                .add(Attributes.ARMOR_TOUGHNESS, 6.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.32)
                .add(Attributes.FOLLOW_RANGE, 64.0)
                .add(Attributes.ATTACK_DAMAGE, DANO_TAJO);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, Estado.QUIETO.ordinal());
        this.entityData.define(INICIO, 0);
        this.entityData.define(RITMO, 1f);
        this.entityData.define(CORONA_ROTA, false);
        this.entityData.define(CALOR, 0f);
        this.entityData.define(PRESA_D, -1);
        this.entityData.define(PRESA_I, -1);
        this.entityData.define(CRISTAL, -1);
    }

    @Override
    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
    }

    // ------------------------------------------------------------------ estado (para el cliente y las pruebas)

    public Estado getEstado() {
        return Estado.values()[this.entityData.get(ESTADO)];
    }

    /** Segundos de animacion desde que empezo el estado (igual en el servidor y en el cliente: van al ritmo). */
    public float tiempoEnEstado(float parcial) {
        return (this.level().getGameTime() - this.entityData.get(INICIO) + parcial) / 20f * ritmo();
    }

    public int inicioEstado() {
        return this.entityData.get(INICIO);
    }

    /** A que velocidad va la animacion del estado de ahora (1 = normal; sube con el frenesi). */
    public float ritmo() {
        return this.entityData.get(RITMO);
    }

    public boolean coronaRota() {
        return this.entityData.get(CORONA_ROTA);
    }

    public float calor() {
        return this.entityData.get(CALOR);
    }

    public int fase() {
        return this.fase;
    }

    public Set<Estado> visitados() {
        return this.visitados;
    }

    public int sacrificados() {
        return this.sacrificados;
    }

    /** Para las pruebas: cuantos se salvaron con totem, cuantos se zafaron y a cuantos distintos ha perseguido. */
    public int totems() {
        return this.totems;
    }

    public int zafados() {
        return this.zafados;
    }

    public int perseguidos() {
        return this.objetivos.size();
    }

    public int guerrerosSalidos() {
        return this.guerrerosSalidos;
    }

    public int ticksEnEstado() {
        return this.ticksEnEstado;
    }

    /** Para las pruebas: fuerza un estado (solo en el servidor). */
    public void forzar(Estado e) {
        cambiar(e);
    }

    public void ponerCalor(float c) {
        this.entityData.set(CALOR, Mth.clamp(c, 0f, 1f));
    }

    /** El frenesi: entre menos vida, mas rapido (1 con la vida llena, 1.75 casi muerto; un poco mas en el Quinto Sol). */
    public float furia() {
        float f = 1f + 0.75f * (1f - this.getHealth() / this.getMaxHealth()) + (this.fase >= 3 ? 0.1f : 0f);
        return Mth.clamp(f, 1f, 1.85f);
    }

    private float ritmoPara(Estado e) {
        if (e.bucle || e == Estado.CORONA || e == Estado.MUERTE || e == Estado.SALTO_ALTAR || e == Estado.SOLTAR
                || e == Estado.SACRIFICIO)
            return 1f;                                            // el sacrificio no se apura: es la ventana del rescate
        if (e == Estado.SALTO)
            return Math.min(1.4f, furia() * 1.15f);               // el salto del jaguar: rapido, pero se ve venir
        return furia();
    }

    private void cambiar(Estado nuevo) {
        if (Mipack.PRUEBA)
            Mipack.LOGGER.info("[Khaset] {} -> {} (vida {}/{}, calor {}, fase {}, ritmo {})", getEstado(), nuevo, (int) getHealth(),
                    (int) getMaxHealth(), String.format("%.2f", calor()), fase, String.format("%.2f", ritmoPara(nuevo)));
        this.entityData.set(ESTADO, nuevo.ordinal());
        this.entityData.set(INICIO, (int) this.level().getGameTime());
        this.entityData.set(RITMO, ritmoPara(nuevo));
        this.ticksEnEstado = 0;
        this.avance = 0f;
        this.avanceAntes = -1f;
        this.golpeados.clear();
        this.tipAnterior = null;
        this.despegue = -1;
        this.visitados.add(nuevo);
    }

    private float t() {
        return this.avance;
    }

    /** True solo en el tick en que la animacion pasa por el segundo 's'. */
    private boolean en(float s) {
        return this.avanceAntes < s && s <= this.avance;
    }

    private boolean termino() {
        return this.avance >= PosesKhaset.largo(getEstado().anim);
    }

    private boolean listo(Estado e) {
        return this.enfriar.getOrDefault(e, 0) <= 0;
    }

    /** Lo que tarda en volver a usar un ataque (menos entre mas furioso). */
    private void enfriarA(Estado e, int ticks) {
        this.enfriar.put(e, Math.round(ticks / furia()));
    }

    /** Termino un ataque: va por otro objetivo y sigue. */
    private void trasAtaque(Estado e, int enfriamiento) {
        if (e != null)
            enfriarA(e, enfriamiento);
        escoger(true);
        cambiar(Estado.CAMINAR);
    }

    boolean valido(LivingEntity e) {
        if (e == null || !e.isAlive() || e == this || e instanceof KhasetEntity || e instanceof Xiuhcoatl
                || e instanceof GuerreroCalavera)
            return false;
        if (this.casa != null && e.distanceToSqr(Vec3.atCenterOf(this.casa)) > RADIO_PELEA * RADIO_PELEA * 1.5)
            return false;
        if (e instanceof Player p)
            return !p.isCreative() && !p.isSpectator();
        // en las pruebas tambien caza mobs (pero no a otros jefes ni a lo suyo)
        return Mipack.PRUEBA && e instanceof Mob && !(e instanceof com.mipack.entidad.CrackatosEntity)
                && !(e instanceof com.mipack.entidad.AcaroAmatista);
    }

    private List<LivingEntity> enemigos(double radio) {
        return this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(radio), this::valido);
    }

    /** Los enemigos que no lleva en la mano. */
    private List<LivingEntity> libres(double radio) {
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : enemigos(radio))
            if (e.getVehicle() != this)
                out.add(e);
        return out;
    }

    // ------------------------------------------------------------------ la pelea (servidor)

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        if (this.casa == null)
            this.casa = this.blockPosition();
        this.ticksEnEstado++;
        this.avanceAntes = this.avance;
        this.avance += ritmo() / 20f;
        this.enfriar.replaceAll((k, v) -> Math.max(0, v - 1));
        if (this.ventanaGolpes > 0 && --this.ventanaGolpes == 0)
            this.golpesDeFrente = 0;
        if (this.tickCount % 20 == 0) {
            participantes();
            this.amenaza.olvidar();
            long ahora = this.level().getGameTime();
            this.noAgarrar.values().removeIf(v -> v < ahora);
        }
        if (this.tickCount % 20 == 5)
            for (Entity e : new ArrayList<>(this.getPassengers()))
                if (e.isRemoved() || !e.isAlive() || (e instanceof ServerPlayer sp && sp.hasDisconnected())) {
                    this.soltando = true;                         // se salio, se murio o lo quitaron: se baja
                    e.stopRiding();
                    this.soltando = false;
                    terminarForcejeo(e);
                }
        if (getEstado() == Estado.MUERTE)
            return;
        LivingEntity objetivo = elegirObjetivo();
        cambiosDeFase();
        switch (getEstado()) {
            case QUIETO -> {
                quedarse(objetivo == null ? null : objetivo.position(), 3f);
                if (objetivo != null && this.ticksEnEstado > 10)
                    cambiar(Estado.CAMINAR);
            }
            case CAMINAR -> caminar(objetivo);
            case CORRER -> correr(objetivo);
            case TAJOS -> tajos(objetivo);
            case BARRIDO, BARRIDO_I -> barrido(objetivo);
            case SALTO -> salto(objetivo, false);
            case SALTO_ALTAR -> salto(null, true);
            case DARDO -> dardo(objetivo);
            case GUARDIA -> guardia(objetivo);
            case CONTRA -> contra(objetivo);
            case SILBATO -> silbato();
            case AGARRAR, AGARRAR_DOS -> agarrar();
            case CARGAR, CARGAR_DOS -> cargar();
            case PISOTON, PISOTON_DOS -> pisoton();
            case SOLTAR -> {
                quedarse(null, 0f);
                if (en(PosesKhasetDatos.SOLTAR))
                    soltarPresas(true);
                if (termino())
                    trasAtaque(null, 0);
            }
            case SACRIFICIO -> sacrificio();
            case INVOCAR -> invocar(objetivo);
            case CORONA -> corona();
            default -> {
            }
        }
        if (this.fase >= 3 && --this.enfriarGuerreros <= 0)
            guerreros(2 + this.maxJugadores / 4);
        ondas();
        erupciones();
        calorYHuellas();
    }

    /** A quien va: el de ahora mientras siga cerca; cada tanto (y despues de cada ataque) reparte (Amenaza). */
    private LivingEntity elegirObjetivo() {
        LivingEntity actual = this.getTarget();
        if (valido(actual) && actual.getVehicle() != this && actual.distanceToSqr(this) < 40 * 40 && this.tickCount % 120 != 0)
            return actual;
        if (actual != null || this.tickCount % 10 == 0)
            return escoger(false);
        return null;
    }

    private LivingEntity escoger(boolean cambiar) {
        LivingEntity e = this.amenaza.escoger(this, libres(40), cambiar, 24.0, this.level().getGameTime(), this.random);
        this.setTarget(e);
        if (e != null && this.objetivos.add(e.getUUID()) && Mipack.PRUEBA)
            Mipack.LOGGER.info("[Khaset] persigue a {} ({} distintos)", e.getName().getString(), this.objetivos.size());
        return e;
    }

    private void cambiosDeFase() {
        Estado e = getEstado();
        boolean ocupado = e.cargando() || e == Estado.AGARRAR || e == Estado.AGARRAR_DOS || e == Estado.CORONA
                || e == Estado.SOLTAR || e == Estado.SALTO;
        if (ocupado)
            return;
        if (this.fase == 1 && this.getHealth() < this.getMaxHealth() * 0.5f) {
            this.fase = 2;
            cambiar(Estado.CORONA);
        } else if (this.fase == 2 && this.getHealth() < this.getMaxHealth() * 0.2f) {
            this.fase = 3;
            this.enfriar.put(Estado.SILBATO, 0);
            cambiar(Estado.SILBATO);
            guerreros(Math.min(10, 3 + this.maxJugadores / 2));
        }
    }

    /** Quien entra a la pelea suma vida (nunca baja): 2000 mas 1200 por jugador. */
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
        // las barras: a los que estan cerca
        for (ServerPlayer sp : this.level() instanceof ServerLevel sl ? sl.players() : List.<ServerPlayer>of()) {
            boolean cerca = sp.distanceToSqr(this) < 64 * 64;
            if (cerca) {
                this.barra.addPlayer(sp);
                this.barraCalor.addPlayer(sp);
            } else {
                this.barra.removePlayer(sp);
                this.barraCalor.removePlayer(sp);
            }
        }
    }

    // ---- caminar, correr y escoger ataque

    private void caminar(LivingEntity objetivo) {
        if (objetivo == null) {
            if (this.casa != null && this.distanceToSqr(Vec3.atCenterOf(this.casa)) > 9)
                irA(Vec3.atBottomCenterOf(this.casa), 0.9);
            else if (this.ticksEnEstado > 60)
                cambiar(Estado.QUIETO);
            else
                quedarse(null, 0f);
            return;
        }
        double d = this.distanceTo(objetivo);
        this.lejosTicks = d > 16 ? this.lejosTicks + 1 : Math.max(0, this.lejosTicks - 2);
        if (this.ticksEnEstado > (furia() > 1.3f ? 1 : 4)) {     // furioso casi no descansa entre ataques
            Estado ataque = elegirAtaque(objetivo, d);
            if (ataque != null) {
                cambiar(ataque);
                return;
            }
        }
        if (this.presaElegida != null) {
            irA(this.presaElegida.position(), 1.7);
            return;
        }
        if (d > 14 && this.ticksEnEstado > 10) {
            cambiar(Estado.CORRER);
            return;
        }
        if (d > 4.0)
            irA(objetivo.position(), 1.0);
        else
            quedarse(objetivo.position(), GIRO_CAMINAR);
    }

    private void correr(LivingEntity objetivo) {
        if (objetivo == null || this.ticksEnEstado > 120) {
            cambiar(Estado.CAMINAR);
            return;
        }
        LivingEntity hacia = this.presaElegida != null ? this.presaElegida : objetivo;
        irA(hacia.position(), 2.6);
        double d = this.distanceTo(hacia);
        this.lejosTicks = d > 16 ? this.lejosTicks + 1 : Math.max(0, this.lejosTicks - 2);
        Estado ataque = elegirAtaque(objetivo, this.distanceTo(objetivo));
        if (ataque != null && this.ticksEnEstado > 3)
            cambiar(ataque);
        else if (d < 7 && this.presaElegida == null)
            cambiar(Estado.CAMINAR);
    }

    private boolean agarrable(LivingEntity e) {
        return EfectosKhaset.capturable(e) && !e.isPassenger() && !this.noAgarrar.containsKey(e.getUUID());
    }

    /** El repertorio: segun la distancia, lo que este listo y la fase (con un poco de azar). */
    private Estado elegirAtaque(LivingEntity objetivo, double d) {
        // capturar va primero: alguien derribado o muy herido cerca (y le caben dos en las manos)
        if (listo(Estado.AGARRAR) && this.getPassengers().size() < 2) {
            List<LivingEntity> presas = new ArrayList<>();
            for (LivingEntity e : enemigos(18))
                if (agarrable(e))
                    presas.add(e);
            if (!presas.isEmpty()) {
                presas.sort((a, b) -> Double.compare(a.distanceToSqr(this), b.distanceToSqr(this)));
                LivingEntity p = presas.get(0);
                this.presaElegida = p;
                if (this.distanceTo(p) < 5.6) {
                    boolean dos = presas.size() >= 2 && presas.get(1).distanceTo(this) < 7.5;
                    return dos ? Estado.AGARRAR_DOS : Estado.AGARRAR;
                }
                return null;                                     // se acerca (caminar/correr van hacia la presa)
            }
        }
        this.presaElegida = null;
        List<Estado> op = new ArrayList<>();
        List<Integer> peso = new ArrayList<>();
        boolean lejos = this.lejosTicks > 50;                    // se le estan alejando: no se deja
        if (listo(Estado.SILBATO) && d < 28) {
            op.add(Estado.SILBATO);
            peso.add((this.fase == 3 ? 5 : 3) + (lejos ? 3 : 0));
        }
        if (d < 7) {
            if (listo(Estado.TAJOS)) {
                op.add(Estado.TAJOS);
                peso.add(5);
            }
            if (listo(Estado.BARRIDO)) {
                op.add(this.random.nextBoolean() ? Estado.BARRIDO : Estado.BARRIDO_I);
                peso.add(3);
            }
        } else {
            if (listo(Estado.SALTO) && d > 6 && d < ALCANCE_SALTO + 2) {
                op.add(Estado.SALTO);
                peso.add(lejos ? 8 : 4);
            }
            if (listo(Estado.DARDO) && d > 8) {
                op.add(Estado.DARDO);
                peso.add(lejos ? 5 : 3);
            }
            if (listo(Estado.INVOCAR)) {
                op.add(Estado.INVOCAR);
                peso.add(this.fase >= 2 ? 3 : 2);
            }
        }
        if (op.isEmpty())
            return null;
        int total = peso.stream().mapToInt(Integer::intValue).sum();
        int r = this.random.nextInt(total);
        for (int i = 0; i < op.size(); i++) {
            r -= peso.get(i);
            if (r < 0)
                return op.get(i);
        }
        return null;
    }

    // ---- los ataques

    /** Mientras ataca se le va encima: si esta en una ventana de avance y lejos, avanza; si no, gira hacia el. */
    private void acometer(LivingEntity objetivo, boolean avanza, double velocidad, float giro) {
        if (objetivo == null) {
            quedarse(null, 0f);
            return;
        }
        if (avanza && this.distanceTo(objetivo) > 3.2)
            irA(objetivo.position(), velocidad);
        else
            quedarse(objetivo.position(), giro);
    }

    private void tajos(LivingEntity objetivo) {
        float[] g = PosesKhasetDatos.GOLPES_ZARPAZOS;
        float s = t();
        boolean avanza = (s > g[0] - 0.3f && s < g[0]) || (s > g[1] - 0.3f && s < g[1]) || (s > g[2] - 0.35f && s < g[2]);
        if (s < g[2])
            acometer(objetivo, avanza, 1.8, GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        if (en(g[0]))
            golpeGarra("zarpazos", 'd', g[0]);
        if (en(g[1]))
            golpeGarra("zarpazos", 'i', g[1]);
        if (en(g[2])) {
            golpeGarra("zarpazos", 'd', g[2]);
            golpeGarra("zarpazos", 'i', g[2]);
        }
        if (termino()) {
            if (objetivo != null && this.distanceTo(objetivo) < 6.5 && listo(Estado.BARRIDO) && this.random.nextInt(3) > 0) {
                enfriarA(Estado.TAJOS, 30);
                cambiar(this.random.nextBoolean() ? Estado.BARRIDO : Estado.BARRIDO_I);   // combo: remata abajo
            } else {
                trasAtaque(Estado.TAJOS, 30);
            }
        }
    }

    /** Un tajo: lo que este cerca de la punta de la garra (o en el frente cercano) recibe el corte. */
    private void golpeGarra(String anim, char lado, float s) {
        Vec3 punta = PosesKhaset.aMundo(this, this.getYRot(), PosesKhaset.mano(anim, lado, PosesKhaset.Punto.PUNTA, s, false), ESCALA);
        this.golpeados.clear();
        for (LivingEntity e : enemigos(10)) {
            if (e.getVehicle() == this)
                continue;
            AABB caja = e.getBoundingBox().inflate(2.4);
            if (caja.contains(punta) || e.getBoundingBox().getCenter().distanceTo(punta) < 3.2) {
                Golpes.pegar(e, this, DANO_TAJO, 100);
                EfectosKhaset.cortar(e, 1);
                e.setSecondsOnFire(2);
                empujar(e, 0.6, 0.25);
            }
        }
        chispas(punta, 10);
        this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.5f, 0.6f);
    }

    private void barrido(LivingEntity objetivo) {
        float[] b = PosesKhasetDatos.BARRIDO;
        float s = t();
        if (s < b[0] - 0.35f)
            acometer(objetivo, false, 0, GIRO_APUNTAR);
        else if (s < b[1])
            irA(this.position().add(adelante().scale(4)), 1.9);  // barre avanzando
        else
            quedarse(null, 0f);
        String anim = getEstado().anim;
        char lado = getEstado() == Estado.BARRIDO ? 'd' : 'i';
        if (s >= b[0] - 0.05f && s <= b[1] + 0.05f) {
            Vec3 punta = PosesKhaset.aMundo(this, this.getYRot(), PosesKhaset.mano(anim, lado, PosesKhaset.Punto.PUNTA, s, false), ESCALA);
            Vec3 antes = this.tipAnterior == null ? punta : this.tipAnterior;
            for (LivingEntity e : enemigos(10)) {
                if (this.golpeados.contains(e.getUUID()) || e.getVehicle() == this)
                    continue;
                AABB caja = e.getBoundingBox();
                if (caja.minY > this.getY() + 2.8)
                    continue;                                    // brincando muy alto se esquiva
                Vec3 c = new Vec3(caja.getCenter().x, Math.min(caja.getCenter().y, this.getY() + 0.8), caja.getCenter().z);
                if (distanciaASegmento(c, antes, punta) < 1.6 + e.getBbWidth() / 2) {
                    this.golpeados.add(e.getUUID());
                    Golpes.pegar(e, this, DANO_BARRIDO, 100);
                    EfectosKhaset.cortar(e, 2);
                    EfectosKhaset.derribar(e, 30);               // el corte de piernas: de rodillas
                    empujar(e, 0.4, 0.15);
                    sangre(e);
                }
            }
            if (this.ticksEnEstado % 2 == 0)
                polvo(punta, 4);
            this.tipAnterior = punta;
        }
        if (en(b[0]))
            this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 3.0f, 0.45f);
        if (termino())
            trasAtaque(Estado.BARRIDO, 60);
    }

    /** Salto del jaguar (sobre el grupo, hasta 26 bloques) o salto al altar con la presa: se agacha, salta y cae. */
    private void salto(LivingEntity objetivo, boolean alAltar) {
        float s0 = PosesKhasetDatos.SALTO;
        if (this.ticksEnEstado == 1) {
            this.salida = this.position();
            if (alAltar) {
                this.destino = puntoDelAltar();
            } else {
                Vec3 centro = objetivo != null ? centroDelGrupo(objetivo) : this.position().add(adelante().scale(10));
                Vec3 d = centro.subtract(this.position());
                double largo = Math.min(ALCANCE_SALTO, d.horizontalDistance());
                Vec3 dir = new Vec3(d.x, 0, d.z).normalize();
                Vec3 meta = this.position().add(dir.scale(Math.max(2.0, largo - 1.5)));
                // no se brinca las paredes de la arena: si hay una en medio, cae antes de ella
                Vec3 ojo = this.position().add(0, 1.5, 0);
                HitResult pared = this.level().clip(new ClipContext(ojo, meta.add(0, 1.5, 0), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, this));
                if (pared.getType() == HitResult.Type.BLOCK) {
                    double hasta = Math.max(0.0, pared.getLocation().subtract(ojo).horizontalDistance() - this.getBbWidth() / 2 - 1.5);
                    meta = this.position().add(dir.scale(hasta));
                }
                this.destino = suelo(meta);
            }
            // en el aire va lo que dura esa parte de la animacion (al ritmo): mas lejos, mas rapido
            this.vuelo = Math.max(6, Math.round(0.5f * 20f / ritmo()));
            int hasta = Math.round(s0 * 20f / ritmo()) + this.vuelo;
            if (!alAltar)
                AvisoKhaset.poner(this.level(), this.destino, (float) RADIO_SALTO, hasta + 4, 0xFF7A1E);
            this.playSound(SonidosMipack.RUGIDO.get(), 3.0f, 1.1f);
        }
        if (en(s0))
            this.despegue = this.ticksEnEstado;
        if (this.despegue < 0) {
            quedarse(this.destino, GIRO_APUNTAR * 2);
        } else if (this.ticksEnEstado <= this.despegue + this.vuelo) {
            float u = (this.ticksEnEstado - this.despegue) / (float) this.vuelo;
            double dist = this.salida.subtract(this.destino).horizontalDistance();
            double alto = 3.0 + dist * 0.18 + Math.max(0, this.destino.y - this.salida.y);
            Vec3 p = this.salida.lerp(this.destino, u).add(0, alto * 4 * u * (1 - u), 0);
            this.setDeltaMovement(Vec3.ZERO);
            this.move(MoverType.SELF, p.subtract(this.position()));
            this.fallDistance = 0;
            if (this.ticksEnEstado == this.despegue + this.vuelo)
                aterrizar(alAltar);
        } else {
            quedarse(null, 0f);
        }
        if (termino()) {
            if (alAltar) {
                cambiar(presas().isEmpty() ? Estado.CAMINAR : Estado.SACRIFICIO);
            } else if (this.fase >= 2 && this.saltosSeguidos == 0 && this.random.nextInt(2) == 0) {
                this.saltosSeguidos++;                            // furioso: otro salto sobre otro grupo
                escoger(true);
                cambiar(Estado.SALTO);
            } else {
                this.saltosSeguidos = 0;
                trasAtaque(Estado.SALTO, 120);
            }
        }
    }

    private void aterrizar(boolean alAltar) {
        polvo(this.position(), 40);
        this.playSound(SoundEvents.GENERIC_EXPLODE, 3.0f, 0.6f);
        if (alAltar)
            return;
        for (LivingEntity e : libres(RADIO_SALTO + 1)) {
            double d = e.position().distanceTo(this.position());
            if (d > RADIO_SALTO)
                continue;
            Golpes.pegar(e, this, DANO_SALTO * (float) (1.0 - 0.5 * d / RADIO_SALTO), 100);
            Vec3 fuera = e.position().subtract(this.position()).multiply(1, 0, 1);
            fuera = fuera.lengthSqr() < 1e-4 ? adelante() : fuera.normalize();
            lanzar(e, fuera.scale(1.2), 0.5);
            if (d < RADIO_SALTO * 0.5)
                EfectosKhaset.derribar(e, 40);
        }
        this.ondas.add(new Onda(this.position(), ONDA_SALTO, 0.75, DANO_ONDA));
    }

    private void dardo(LivingEntity objetivo) {
        if (objetivo != null && t() < PosesKhasetDatos.DARDO)
            quedarse(objetivo.position(), GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        if (en(PosesKhasetDatos.DARDO) && objetivo != null) {
            Vec3 mano = PosesKhaset.aMundo(this, this.getYRot(),
                    PosesKhaset.mano("lanzar_dardo", 'd', PosesKhaset.Punto.PALMA, PosesKhasetDatos.DARDO, false), ESCALA);
            int n = this.fase == 1 ? 3 : this.fase == 2 ? 5 : 7;
            for (int i = 0; i < n; i++) {
                float abre = (i - (n - 1) / 2f) * 11f;
                DardoAtlatl.lanzar(this.level(), this, mano, objetivo, abre, coronaRota());
            }
            if (this.fase >= 2) {                                // y uno a cada quien que este lejos
                int extra = 0;
                for (LivingEntity e : libres(32))
                    if (e != objetivo && extra++ < 4)
                        DardoAtlatl.lanzar(this.level(), this, mano, e, 0f, coronaRota());
            }
            this.playSound(SoundEvents.TRIDENT_THROW, 2.5f, 0.7f);
        }
        if (termino())
            trasAtaque(Estado.DARDO, 70);
    }

    private void guardia(LivingEntity objetivo) {
        quedarse(objetivo == null ? null : objetivo.position(), 5f);
        if (this.contraPendiente) {
            this.contraPendiente = false;
            cambiar(Estado.CONTRA);
            return;
        }
        if (this.ticksEnEstado >= 40) {
            enfriarA(Estado.GUARDIA, 200);
            cambiar(Estado.CAMINAR);
        }
    }

    private void contra(LivingEntity objetivo) {
        if (t() < PosesKhasetDatos.CONTRA)
            acometer(objetivo, true, 2.0, GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        if (en(PosesKhasetDatos.CONTRA)) {
            Vec3 adelante = adelante();
            for (LivingEntity e : libres(9)) {
                Vec3 d = e.position().subtract(this.position()).multiply(1, 0, 1);
                if (d.length() < 7.5 && d.normalize().dot(adelante) > 0.2) {
                    Golpes.pegar(e, this, DANO_CONTRA, 120);
                    EfectosKhaset.cortar(e, 1);
                    lanzar(e, d.normalize().scale(1.4), 0.5);
                }
            }
            chispas(this.position().add(adelante.scale(3)).add(0, 4, 0), 20);
            this.playSound(SoundEvents.PLAYER_ATTACK_STRONG, 3.0f, 0.5f);
        }
        if (termino())
            trasAtaque(null, 0);
    }

    /** El silbato de la muerte: aturde y desorienta a quien lo oiga de frente (sin un bloque en medio). */
    private void silbato() {
        quedarse(null, 0f);
        if (this.ticksEnEstado == 1)
            this.playSound(SonidosMipack.SILBATO.get(), 6.0f, 1.0f);
        if (en(0.6f)) {
            Vec3 cabeza = this.position().add(0, 8.0, 0);
            for (LivingEntity e : libres(32)) {
                if (e.distanceTo(this) > 32)
                    continue;
                HitResult r = this.level().clip(new ClipContext(cabeza, e.getEyePosition(), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, this));
                if (r.getType() == HitResult.Type.BLOCK)
                    continue;                                    // detras de una columna: se salva
                e.addEffect(new MobEffectInstance(EfectosKhaset.ATURDIDO.get(), this.fase >= 3 ? 50 : 35, 0, false, false, true));
                e.addEffect(new MobEffectInstance(EfectosKhaset.DESORIENTADO.get(), 140, 0, false, false, true));
            }
            if (this.level() instanceof ServerLevel sl)
                for (int i = 0; i < 4; i++)
                    sl.sendParticles(ParticleTypes.SONIC_BOOM, cabeza.x + adelante().x * (2 + i * 3), cabeza.y - i,
                            cabeza.z + adelante().z * (2 + i * 3), 1, 0, 0, 0, 0);
            this.playSound(SoundEvents.WARDEN_SONIC_BOOM, 3.0f, 1.4f);
        }
        if (termino())
            trasAtaque(Estado.SILBATO, this.fase == 3 ? 220 : 320);
    }

    // ---- captura y sacrificio

    private void agarrar() {
        boolean dos = getEstado() == Estado.AGARRAR_DOS;
        if (this.presaElegida != null && t() < PosesKhasetDatos.AGARRA - 0.2f)
            quedarse(this.presaElegida.position(), GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        if (en(PosesKhasetDatos.AGARRA)) {
            for (char lado : dos ? new char[]{'d', 'i'} : new char[]{'d'}) {
                if (this.entityData.get(lado == 'd' ? PRESA_D : PRESA_I) >= 0 && presa(lado) != null)
                    continue;
                Vec3 palma = PosesKhaset.aMundo(this, this.getYRot(),
                        PosesKhaset.mano(getEstado().anim, lado, PosesKhaset.Punto.PALMA, PosesKhasetDatos.AGARRA, false), ESCALA);
                LivingEntity mejor = null;
                double d = 3.0;
                for (LivingEntity e : enemigos(10)) {
                    if (!agarrable(e))
                        continue;
                    double dd = e.getBoundingBox().getCenter().distanceTo(palma);
                    if (dd < d) {
                        d = dd;
                        mejor = e;
                    }
                }
                if (mejor != null && mejor.startRiding(this, true)) {
                    this.agarroEn = this.level().getGameTime();
                    this.entityData.set(lado == 'd' ? PRESA_D : PRESA_I, mejor.getId());
                    mejor.removeEffect(EfectosKhaset.DERRIBADO.get());
                    if (mejor instanceof ServerPlayer sp)
                        iniciarForcejeo(sp);
                    this.playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2.0f, 0.5f);
                }
            }
            this.danoEnCarga = 0;
        }
        if (termino()) {
            this.presaElegida = null;
            if (presas().isEmpty())
                trasAtaque(Estado.AGARRAR, 60);
            else
                cambiar(presas().size() > 1 ? Estado.CARGAR_DOS : Estado.CARGAR);
        }
    }

    private void cargar() {
        if (presas().isEmpty()) {
            trasAtaque(Estado.AGARRAR, 60);
            return;
        }
        if (this.ticksEnEstado % 20 == 10)
            for (LivingEntity p : presas())
                Golpes.pegar(p, this, DANO_APRETAR, 0);
        if (this.danoEnCarga >= this.getMaxHealth() * RESCATE) {
            cambiar(Estado.SOLTAR);
            return;
        }
        if (this.level().getGameTime() - this.agarroEn > 420) {
            cambiar(Estado.SACRIFICIO);                          // no llega al cristal: ahi mismo
            return;
        }
        // con las manos llenas tambien pelea: si alguien se le acerca, pisa
        if (listo(Estado.PISOTON) && this.ticksEnEstado > 8 && !libres(9).isEmpty()) {
            cambiar(presas().size() > 1 ? Estado.PISOTON_DOS : Estado.PISOTON);
            return;
        }
        CristalSacrificio cristal = this.fase >= 3 ? null : cristalCercano();
        this.entityData.set(CRISTAL, cristal == null ? -1 : cristal.getId());
        if (cristal == null) {
            quedarse(null, 0f);
            if (this.ticksEnEstado >= (this.fase >= 3 ? 40 : 60))
                cambiar(Estado.SACRIFICIO);                      // sin cristal (o en el Quinto Sol): ahi mismo
            return;
        }
        cristal.llamar();
        Vec3 donde = puntoDelAltar();
        double dh = donde.subtract(this.position()).horizontalDistance();
        if (dh < 1.2) {
            mirarA(cristal.position());
            cambiar(Estado.SACRIFICIO);
        } else if (dh < 16 && donde.y - this.getY() > 1.5) {
            cambiar(Estado.SALTO_ALTAR);
        } else if (this.ticksEnEstado > 300) {
            cambiar(Estado.SACRIFICIO);
        } else {
            irA(donde, 1.5);
        }
    }

    /** Con la presa en alto, pisa: sale una onda de fuego por el piso y lo de junto a su pie sale volando. */
    private void pisoton() {
        LivingEntity cerca = null;
        for (LivingEntity e : libres(12))
            if (cerca == null || e.distanceToSqr(this) < cerca.distanceToSqr(this))
                cerca = e;
        quedarse(cerca == null ? null : cerca.position(), t() < 0.35f ? GIRO_APUNTAR : 0f);
        if (this.ticksEnEstado == 1)
            this.playSound(SonidosMipack.RUGIDO.get(), 3.0f, 0.9f);
        if (en(PosesKhasetDatos.PISA)) {
            Vec3 pie = PosesKhaset.aMundo(this, this.getYRot(), new Vec3(3.0, 0, -4.0), ESCALA);
            for (LivingEntity e : libres(5)) {
                if (e.position().distanceTo(pie) < 4.0) {
                    Golpes.pegar(e, this, DANO_PISOTON, 100);
                    Vec3 fuera = e.position().subtract(pie).multiply(1, 0, 1);
                    lanzar(e, fuera.lengthSqr() < 1e-4 ? adelante() : fuera.normalize().scale(1.0), 0.7);
                    e.setSecondsOnFire(3);
                }
            }
            this.ondas.add(new Onda(pie, 11.0, 0.8, DANO_ONDA));
            polvo(pie, 30);
            this.playSound(SoundEvents.GENERIC_EXPLODE, 2.5f, 0.5f);
        }
        if (presas().isEmpty()) {
            trasAtaque(Estado.AGARRAR, 60);
            return;
        }
        if (termino()) {
            enfriarA(Estado.PISOTON, 70);
            cambiar(presas().size() > 1 ? Estado.CARGAR_DOS : Estado.CARGAR);
        }
    }

    private void sacrificio() {
        float[] s = PosesKhasetDatos.SACRIFICIO;
        CristalSacrificio cristal = cristalPorId();
        if (cristal != null && this.ticksEnEstado < 3)
            mirarA(cristal.position());
        quedarse(null, 0f);
        if (presas().isEmpty() && t() < s[1]) {                  // se le zafaron todos
            trasAtaque(Estado.AGARRAR, 80);
            return;
        }
        if (cristal != null && t() < s[1])
            cristal.llamar();
        // tambien pelea mientras sacrifica: erupciones bajo los que esten cerca
        if (this.ticksEnEstado == 1 || en(s[1] - 0.6f))
            for (LivingEntity e : libres(16))
                erupcion(e.position(), Math.round(10 + 8 / ritmo()));
        if (this.ticksEnEstado == 1)
            this.playSound(SonidosMipack.SACRIFICIO.get(), 4.0f, 1.0f);
        if (t() < s[1] && this.danoEnCarga >= this.getMaxHealth() * RESCATE) {
            cambiar(Estado.SOLTAR);
            return;
        }
        if (en(s[1])) {
            for (LivingEntity p : new ArrayList<>(presas())) {
                p.invulnerableTime = 0;
                p.hurt(EfectosKhaset.fuente(this.level(), EfectosKhaset.SACRIFICIO, this), 10000f);
                sangre(p);
                if (!p.isAlive()) {
                    this.sacrificados++;
                } else {                                          // el totem lo salvo: se suelta
                    this.totems++;
                    soltarUna(p, true);
                }
            }
            this.playSound(SoundEvents.WARDEN_HEARTBEAT, 4.0f, 0.6f);
        }
        if (en(s[2])) {
            int muertos = 0;
            for (LivingEntity p : new ArrayList<>(presas()))
                if (!p.isAlive())
                    muertos++;
            if (muertos == 0)
                muertos = this.sacrificados > 0 ? 1 : 0;
            ponerCalor(calor() + CALOR_SACRIFICIO * muertos);
            this.heal(this.getMaxHealth() * 0.03f * muertos);
            if (cristal != null)
                cristal.sacrificio();
            Vec3 mano = PosesKhaset.aMundo(this, this.getYRot(),
                    PosesKhaset.mano("sacrificio", 'd', PosesKhaset.Punto.PALMA, s[2], false), ESCALA);
            if (this.level() instanceof ServerLevel sl) {
                sl.sendParticles(ParticulasKhaset.BRASA.get(), mano.x, mano.y, mano.z, 40, 0.6, 0.6, 0.6, 0.15);
                sl.sendParticles(ParticleTypes.FLAME, mano.x, mano.y, mano.z, 30, 0.4, 0.4, 0.4, 0.08);
            }
            this.playSound(SoundEvents.BLAZE_SHOOT, 3.0f, 0.5f);
        }
        if (termino()) {
            soltarPresas(false);
            this.entityData.set(CRISTAL, -1);
            trasAtaque(Estado.AGARRAR, 100);
        }
    }

    private void invocar(LivingEntity objetivo) {
        quedarse(objetivo == null ? null : objetivo.position(), t() < 0.6f ? GIRO_APUNTAR : 0f);
        float s = PosesKhasetDatos.INVOCA;
        Vec3 manos = PosesKhaset.mano("invocar", 'd', PosesKhaset.Punto.PALMA, s, false)
                .add(PosesKhaset.mano("invocar", 'i', PosesKhaset.Punto.PALMA, s, false)).scale(0.5);
        Vec3 donde = suelo(PosesKhaset.aMundo(this, this.getYRot(), new Vec3(manos.x, 0, manos.z - 6), ESCALA));
        int n = Math.min(6, 2 + (this.fase >= 2 ? 1 : 0) + (this.fase >= 3 ? 1 : 0) + this.maxJugadores / 4);
        if (this.ticksEnEstado == 1)
            AvisoKhaset.poner(this.level(), donde, 3.5f, Math.round(s * 20f / ritmo()) + 6, 0x37D6C0);
        if (en(s)) {
            List<LivingEntity> blancos = libres(40);
            for (int i = 0; i < n; i++) {
                double a = Math.toRadians(this.getYRot() + (i - (n - 1) / 2.0) * 35.0);
                Vec3 p = suelo(donde.add(-Math.sin(a) * 2.5, 0, Math.cos(a) * 2.5));
                Xiuhcoatl x = new Xiuhcoatl(Mipack.XIUHCOATL.get(), this.level());
                x.moveTo(p.x, p.y, p.z, this.getYRot() + (i - (n - 1) / 2f) * 35f, 0f);
                x.dueno(this, blancos.isEmpty() ? objetivo : blancos.get(i % blancos.size()));
                this.level().addFreshEntity(x);
                polvo(p, 15);
            }
            this.playSound(SoundEvents.BLAZE_SHOOT, 3.0f, 0.4f);
        }
        if (termino())
            trasAtaque(Estado.INVOCAR, 360);
    }

    private void corona() {
        quedarse(null, 0f);
        if (en(PosesKhasetDatos.CORONA)) {
            this.entityData.set(CORONA_ROTA, true);
            Vec3 c = this.position().add(PosesKhaset.rotar(this.getYRot(), new Vec3(-0.9, 8.4, -2.0)));
            if (this.level() instanceof ServerLevel sl) {
                sl.sendParticles(ParticulasKhaset.PLUMA.get(), c.x, c.y + 1.0, c.z, 90, 1.6, 1.0, 1.6, 0.18);
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.ORANGE_TERRACOTTA.defaultBlockState()),
                        c.x, c.y, c.z, 60, 0.9, 0.7, 0.9, 0.35);
                sl.sendParticles(ParticleTypes.FLAME, c.x, c.y, c.z, 40, 0.9, 0.9, 0.9, 0.12);
                sl.sendParticles(ParticleTypes.FLASH, c.x, c.y, c.z, 1, 0, 0, 0, 0);
            }
            this.playSound(SoundEvents.ITEM_BREAK, 4.0f, 0.5f);
            this.playSound(SonidosMipack.RUGIDO.get(), 6.0f, 0.8f);
        }
        if (termino()) {
            this.enfriar.put(Estado.INVOCAR, 40);
            trasAtaque(null, 0);
        }
    }

    /** Del piso salen guerreros calavera alrededor (sin pasarse de un tope que crece con los jugadores). */
    private void guerreros(int n) {
        this.enfriarGuerreros = 400;
        if (!(this.level() instanceof ServerLevel sl))
            return;
        this.guerreros.removeIf(u -> !(sl.getEntity(u) instanceof GuerreroCalavera g) || !g.isAlive());
        int tope = Math.min(14, 4 + this.maxJugadores);
        List<LivingEntity> blancos = libres(40);
        for (int i = 0; i < n && this.guerreros.size() < tope; i++) {
            double a = this.random.nextDouble() * Math.PI * 2, r = 6 + this.random.nextDouble() * 14;
            Vec3 p = suelo(this.position().add(Math.cos(a) * r, 0, Math.sin(a) * r));
            GuerreroCalavera g = Mipack.GUERRERO.get().create(sl);
            if (g == null)
                return;
            g.moveTo(p.x, p.y, p.z, this.random.nextFloat() * 360f, 0f);
            g.deJefe(this);
            if (!blancos.isEmpty())
                g.setTarget(blancos.get(this.random.nextInt(blancos.size())));
            sl.addFreshEntity(g);
            this.guerreros.add(g.getUUID());
            this.guerrerosSalidos++;
            AvisoKhaset.poner(sl, p, 1.2f, GuerreroCalavera.T_SURGIR, 0x7A6BFF);
        }
        this.playSound(SoundEvents.SKELETON_HORSE_AMBIENT, 3.0f, 0.5f);
    }

    public List<LivingEntity> presas() {
        List<LivingEntity> out = new ArrayList<>();
        for (EntityDataAccessor<Integer> a : List.of(PRESA_D, PRESA_I)) {
            Entity e = this.level().getEntity(this.entityData.get(a));
            if (e instanceof LivingEntity le && e.getVehicle() == this && e.isAlive())
                out.add(le);
        }
        return out;
    }

    private LivingEntity presa(char lado) {
        Entity e = this.level().getEntity(this.entityData.get(lado == 'd' ? PRESA_D : PRESA_I));
        return e instanceof LivingEntity le && e.getVehicle() == this && e.isAlive() ? le : null;
    }

    /** Suelta a las presas (con caida lenta para que no se maten); 'golpe': las suelta de dolor. */
    private void soltarPresas(boolean golpe) {
        this.soltando = true;
        for (Entity e : new ArrayList<>(this.getPassengers())) {
            e.stopRiding();
            if (e instanceof LivingEntity le && le.isAlive()) {
                le.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 50, 0, false, false));
                if (golpe)
                    lanzar(le, adelante().scale(0.4), 0.2);
                this.noAgarrar.put(le.getUUID(), this.level().getGameTime() + 160);
            }
            terminarForcejeo(e);
        }
        this.soltando = false;
        this.entityData.set(PRESA_D, -1);
        this.entityData.set(PRESA_I, -1);
        if (golpe)
            enfriarA(Estado.AGARRAR, 200);
    }

    /** Suelta solo a una (se zafo o la salvo un totem): sale aventada y en un rato no la vuelve a agarrar. */
    private void soltarUna(LivingEntity e, boolean aventar) {
        this.soltando = true;
        e.stopRiding();
        this.soltando = false;
        if (this.entityData.get(PRESA_D) == e.getId())
            this.entityData.set(PRESA_D, -1);
        if (this.entityData.get(PRESA_I) == e.getId())
            this.entityData.set(PRESA_I, -1);
        terminarForcejeo(e);
        this.noAgarrar.put(e.getUUID(), this.level().getGameTime() + 200);
        if (e.isAlive()) {
            e.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0, false, false));
            e.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 40, 1, false, false));
            if (aventar)
                lanzar(e, adelante().scale(-0.2).add(e.position().subtract(this.position()).multiply(1, 0, 1).normalize().scale(0.8)), 0.5);
        }
    }

    public boolean soltando() {
        return this.soltando || !this.isAlive();
    }

    // ---- la barra para zafarse

    private void iniciarForcejeo(ServerPlayer p) {
        Forcejeo f = new Forcejeo();
        f.ancho = this.fase == 1 ? 0.24f : this.fase == 2 ? 0.2f : 0.17f;
        f.periodo = this.fase == 1 ? 16 : this.fase == 2 ? 14 : 12;     // rapido: caben varios intentos
        f.zona = 0.15f + this.random.nextFloat() * 0.7f;
        f.inicio = this.level().getGameTime();
        this.forcejeos.put(p.getUUID(), f);
        mandarBarra(p, f, false);
    }

    private void terminarForcejeo(Entity e) {
        if (this.forcejeos.remove(e.getUUID()) != null && e instanceof ServerPlayer sp)
            RedKhaset.barra(sp, RedKhaset.Barra.NADA);
    }

    private static void mandarBarra(ServerPlayer p, Forcejeo f, boolean fallo) {
        RedKhaset.barra(p, new RedKhaset.Barra(true, f.aciertos, f.zona, f.ancho, f.periodo, f.inicio, fallo));
    }

    /** El agarrado hizo clic: si el cursor estaba en lo dorado cuenta; si no, pierde la mitad de su vida. */
    public void clic(ServerPlayer p, float cursorCliente) {
        Forcejeo f = this.forcejeos.get(p.getUUID());
        if (f == null || p.getVehicle() != this)
            return;
        long ahora = this.level().getGameTime();
        if (ahora < f.bloqueo)
            return;
        f.bloqueo = ahora + 5;
        float servidor = new RedKhaset.Barra(true, 0, 0, 0, f.periodo, f.inicio, false).cursor(ahora);
        float u = Math.abs(cursorCliente - servidor) < 0.3f ? cursorCliente : servidor;   // la latencia: confia un poco
        boolean acierto = Math.abs(u - f.zona) <= f.ancho / 2 + 0.02f;
        if (acierto) {
            f.aciertos++;
            p.level().playSound(null, p.blockPosition(), SoundEvents.EXPERIENCE_ORB_PICKUP, net.minecraft.sounds.SoundSource.PLAYERS, 1f, 0.8f + 0.2f * f.aciertos);
            if (f.aciertos >= 3) {
                this.zafados++;
                soltarUna(p, true);
                this.playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2.0f, 0.6f);
                if (presas().isEmpty() && getEstado().cargando() && getEstado() != Estado.SALTO_ALTAR)
                    trasAtaque(Estado.AGARRAR, 80);
                return;
            }
        } else {
            p.invulnerableTime = 0;
            p.hurt(Golpes.fuente(p, Golpes.FORCEJEO, null), p.getHealth() / 2f);
            p.level().playSound(null, p.blockPosition(), SoundEvents.PLAYER_HURT_SWEET_BERRY_BUSH, net.minecraft.sounds.SoundSource.PLAYERS, 1f, 0.6f);
            f.inicio = ahora;
        }
        float vieja = f.zona;
        do {
            f.zona = 0.12f + this.random.nextFloat() * 0.76f;
        } while (Math.abs(f.zona - vieja) < 0.2f);
        mandarBarra(p, f, !acierto);
    }

    @Override
    protected void removePassenger(Entity e) {
        super.removePassenger(e);
        if (!this.level().isClientSide)
            terminarForcejeo(e);
    }

    @Override
    protected boolean canAddPassenger(Entity e) {
        return this.getPassengers().size() < 2;
    }

    /** Si el agarrado se sale del juego, el juego se llevaria a Khaset guardado con el (como un caballo): no. */
    @Override
    public boolean hasExactlyOnePlayerPassenger() {
        return false;
    }

    @Override
    public boolean shouldRiderSit() {
        return false;
    }

    @Override
    public double getPassengersRidingOffset() {
        return 0.0;
    }

    @Override
    public Vec3 getDismountLocationForPassenger(LivingEntity pasajero) {
        return pasajero.position();
    }

    /** La presa va en la mano (o acostada en el altar): donde diga la animacion, igual en el servidor y el cliente. */
    @Override
    protected void positionRider(Entity pasajero, Entity.MoveFunction mover) {
        Vec3 p = posicionDePresa(pasajero, 0f);
        if (p != null)
            mover.accept(pasajero, p.x, p.y, p.z);
    }

    public Vec3 posicionDePresa(Entity pasajero, float parcial) {
        char lado = pasajero.getId() == this.entityData.get(PRESA_I) ? 'i' : 'd';
        Estado e = getEstado();
        float t = tiempoEnEstado(parcial);
        float giro = this.getYRot();
        if (e == Estado.SACRIFICIO && t >= PosesKhasetDatos.SACRIFICIO[0]) {
            // acostada a lo largo de la piedra; si son dos, una junto a la otra
            Vec3 a = altarDelSacrificio();
            Vec3 ancho = PosesKhaset.rotar(giroDelAltar(), new Vec3(0, 0, 1));
            boolean dos = this.entityData.get(PRESA_D) >= 0 && this.entityData.get(PRESA_I) >= 0;
            return dos ? a.add(ancho.scale(lado == 'd' ? 0.4 : -0.4)) : a;
        }
        String anim;
        boolean bucle = false;
        switch (e) {
            case AGARRAR, AGARRAR_DOS, SOLTAR, SACRIFICIO, PISOTON, PISOTON_DOS -> anim = e.anim;
            case CARGAR, CARGAR_DOS -> {
                anim = e.anim;
                bucle = true;
            }
            case SALTO_ALTAR -> anim = "abalanzarse";
            default -> {
                anim = "cargar";
                t = 0f;
            }
        }
        if (e == Estado.SACRIFICIO)
            lado = 'd';
        Vec3 palma = PosesKhaset.aMundo(this, giro, PosesKhaset.mano(anim, lado, PosesKhaset.Punto.PALMA, t, bucle), ESCALA);
        return palma.subtract(0, pasajero.getBbHeight() * 0.78, 0);
    }

    /** Donde queda acostada la presa: la piedra del cristal o, sin cristal, el piso enfrente. */
    public Vec3 altarDelSacrificio() {
        CristalSacrificio c = cristalPorId();
        if (c != null)
            return c.position().add(0, CristalSacrificio.ALTO_PIEDRA, 0);
        Vec3 a = PosesKhaset.aMundo(this, this.getYRot(), PosesKhaset.altar(), ESCALA);
        return new Vec3(a.x, this.getY() + 0.05, a.z);
    }

    /** El giro de la piedra (su lado largo es su eje x): la presa se acuesta a lo largo de ella. Sin piedra, el de el. */
    public float giroDelAltar() {
        CristalSacrificio c = cristalPorId();
        return c != null ? c.getYRot() : this.getYRot();
    }

    public boolean presaEnAltar(Entity pasajero) {
        return getEstado() == Estado.SACRIFICIO && tiempoEnEstado(0f) >= PosesKhasetDatos.SACRIFICIO[0]
                && pasajero.getVehicle() == this;
    }

    private CristalSacrificio cristalPorId() {
        Entity e = this.level().getEntity(this.entityData.get(CRISTAL));
        return e instanceof CristalSacrificio c ? c : null;
    }

    private CristalSacrificio cristalCercano() {
        CristalSacrificio mejor = null;
        double d = 64 * 64;
        for (CristalSacrificio c : this.level().getEntitiesOfClass(CristalSacrificio.class, this.getBoundingBox().inflate(64))) {
            double dd = c.distanceToSqr(this);
            if (dd < d) {
                d = dd;
                mejor = c;
            }
        }
        return mejor;
    }

    /** Donde se para para sacrificar: del lado largo de la piedra que le queda mas cerca, a la distancia del altar. */
    private Vec3 puntoDelAltar() {
        CristalSacrificio c = cristalPorId();
        if (c == null)
            c = cristalCercano();
        if (c == null)
            return this.position();
        Vec3 nz = PosesKhaset.rotar(c.getYRot(), new Vec3(0, 0, 1));
        double lejos = -PosesKhaset.altar().z * ESCALA / 16.0;
        Vec3 a = c.position().add(nz.scale(lejos)), b = c.position().subtract(nz.scale(lejos));
        return a.distanceToSqr(this.position()) < b.distanceToSqr(this.position()) ? a : b;
    }

    // ---- ondas de fuego y erupciones

    private void ondas() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        Iterator<Onda> it = this.ondas.iterator();
        while (it.hasNext()) {
            Onda o = it.next();
            double r0 = o.r;
            o.r = Math.min(o.max, o.r + o.vel);
            for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(o.c, o.c).inflate(o.r + 1, 3, o.r + 1), this::valido)) {
                double d = Math.hypot(e.getX() - o.c.x, e.getZ() - o.c.z);
                if (d < r0 - 0.7 || d > o.r + 0.6 || !e.onGround() || Math.abs(e.getY() - o.c.y) > 2.5 || e.getVehicle() == this)
                    continue;
                if (!o.golpeados.add(e.getUUID()))
                    continue;
                Golpes.pegar(e, this, o.dano, 60);
                e.setSecondsOnFire(3);
                Vec3 fuera = new Vec3(e.getX() - o.c.x, 0, e.getZ() - o.c.z);
                lanzar(e, fuera.lengthSqr() < 1e-4 ? Vec3.ZERO : fuera.normalize().scale(0.6), 0.8);
            }
            int n = (int) (o.r * 5);
            for (int i = 0; i < n; i++) {
                double a = 2 * Math.PI * i / n;
                double x = o.c.x + Math.cos(a) * o.r, z = o.c.z + Math.sin(a) * o.r;
                sl.sendParticles(i % 3 == 0 ? ParticleTypes.FLAME : ParticulasKhaset.BRASA.get(), x, o.c.y + 0.15, z, 1, 0.05, 0.05, 0.05, 0.01);
            }
            if (o.r >= o.max)
                it.remove();
        }
    }

    /** En 'ticks' revienta fuego del piso en ese punto (con su circulo de aviso). */
    private void erupcion(Vec3 donde, int ticks) {
        Vec3 p = suelo(donde);
        AvisoKhaset.poner(this.level(), p, 2.6f, ticks, 0xFF3010);
        this.erupciones.add(new Erupcion(p, this.level().getGameTime() + ticks));
    }

    private void erupciones() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        long ahora = sl.getGameTime();
        Iterator<Erupcion> it = this.erupciones.iterator();
        while (it.hasNext()) {
            Erupcion er = it.next();
            if (ahora < er.cuando)
                continue;
            it.remove();
            Vec3 p = er.p;
            for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(2.8, 3, 2.8), this::valido)) {
                if (e.getVehicle() == this || Math.hypot(e.getX() - p.x, e.getZ() - p.z) > 2.6)
                    continue;
                Golpes.pegar(e, this, DANO_ERUPCION, 80);
                e.setSecondsOnFire(4);
                lanzar(e, Vec3.ZERO, 1.1);
            }
            sl.sendParticles(ParticleTypes.LAVA, p.x, p.y + 0.3, p.z, 12, 0.8, 0.2, 0.8, 0.1);
            for (int i = 0; i < 6; i++)
                sl.sendParticles(ParticleTypes.FLAME, p.x, p.y + i * 0.7, p.z, 8, 0.5, 0.3, 0.5, 0.03);
            sl.playSound(null, p.x, p.y, p.z, SoundEvents.FIRECHARGE_USE, net.minecraft.sounds.SoundSource.HOSTILE, 1.6f, 0.6f);
        }
    }

    // ---- el calor

    private void calorYHuellas() {
        boolean pelea = getEstado() != Estado.QUIETO && !enemigos(RADIO_PELEA).isEmpty();
        if (pelea)
            ponerCalor(calor() + (this.fase >= 3 ? 2f : 1f) / LLENADO_CALOR);
        float c = calor();
        this.barraCalor.setProgress(c);
        this.barraCalor.setColor(c >= 0.75f ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.YELLOW);
        this.barra.setProgress(this.getHealth() / this.getMaxHealth());
        if (!pelea || !(this.level() instanceof ServerLevel sl))
            return;
        long ahora = sl.getGameTime();
        List<LivingEntity> todos = enemigos(RADIO_PELEA);
        if (c >= 0.5f) {
            if (this.tickCount % 8 == 0 && this.position().distanceToSqr(this.xo, this.yo, this.zo) > 1e-4)
                this.huellas.add(new Huella(this.position(), ahora + 120));
            this.huellas.removeIf(h -> h.hasta < ahora);
            if (this.tickCount % 6 == 0)
                for (Huella h : this.huellas) {
                    sl.sendParticles(ParticulasKhaset.CENIZA.get(), h.p.x, h.p.y + 0.2, h.p.z, 2, 0.6, 0.1, 0.6, 0.01);
                    sl.sendParticles(ParticleTypes.SMALL_FLAME, h.p.x, h.p.y + 0.1, h.p.z, 1, 0.5, 0.0, 0.5, 0.0);
                }
            for (LivingEntity e : todos) {
                if (e instanceof Player p)
                    p.causeFoodExhaustion(0.02f);
                if (this.tickCount % 10 == 0)
                    for (Huella h : this.huellas)
                        if (e.position().distanceToSqr(h.p) < 1.8 * 1.8) {
                            e.setSecondsOnFire(2);
                            e.hurt(EfectosKhaset.fuente(sl, EfectosKhaset.CALOR, this), 1f);
                            break;
                        }
            }
        }
        if (c >= 0.75f && this.tickCount % 160 == 0)
            for (LivingEntity e : todos) {
                e.hurt(EfectosKhaset.fuente(sl, EfectosKhaset.CALOR, this), 2f);
                e.setSecondsOnFire(3);
            }
        if (c >= 1f) {
            this.ticksAlTope++;
            if (this.ticksAlTope % 20 == 0)
                for (LivingEntity e : todos)
                    e.hurt(EfectosKhaset.fuente(sl, EfectosKhaset.CALOR, this), 2f + this.ticksAlTope / 40f);
        }
    }

    // ------------------------------------------------------------------ dano, muerte y barras

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        Estado e = getEstado();
        if (e == Estado.CORONA || e == Estado.MUERTE)
            return false;
        Entity quien = fuente.getEntity();
        if (fuente.getDirectEntity() instanceof DardoAtlatl || quien instanceof Xiuhcoatl || quien instanceof GuerreroCalavera
                || quien == this || fuente.is(EfectosKhaset.CALOR))
            return false;
        boolean proyectil = fuente.getDirectEntity() instanceof Projectile;
        if (quien != null && !this.level().isClientSide) {
            Entity desde = fuente.getDirectEntity() != null ? fuente.getDirectEntity() : quien;
            Vec3 d = desde.position().subtract(this.position()).multiply(1, 0, 1);
            boolean deFrente = d.lengthSqr() > 1e-4 && d.normalize().dot(adelante()) > 0.3;
            if (e == Estado.GUARDIA && deFrente) {
                if (!proyectil)
                    this.contraPendiente = true;
                this.playSound(SoundEvents.SHIELD_BLOCK, 2.0f, 0.5f);
                return false;                                     // la guardia para tambien flechas
            }
            if (deFrente && !e.cargando()) {
                this.golpesDeFrente++;
                this.ventanaGolpes = 40;
                if (this.golpesDeFrente >= 4 && listo(Estado.GUARDIA) && (e == Estado.CAMINAR || e == Estado.QUIETO)) {
                    this.golpesDeFrente = 0;
                    cambiar(Estado.GUARDIA);
                }
            }
        }
        if (proyectil)
            cantidad *= A_DISTANCIA;
        if (e.cargando() && e != Estado.SALTO_ALTAR) {
            if (quien != null && quien.getVehicle() == this) {
                this.danoEnCarga += cantidad * 0.5f;              // la presa forcejea: cuenta, pero poco
            } else {
                cantidad *= 2f;                                   // mientras carga a la presa: doble dano
                this.danoEnCarga += cantidad;
            }
        }
        boolean pego = super.hurt(fuente, cantidad);
        if (pego && !this.level().isClientSide)
            this.amenaza.golpe(quien, cantidad);
        return pego;
    }

    @Override
    public boolean canBeAffected(MobEffectInstance efecto) {
        return efecto.getEffect() != MobEffects.POISON && efecto.getEffect() != EfectosKhaset.DESANGRADO.get()
                && efecto.getEffect() != EfectosKhaset.DERRIBADO.get() && efecto.getEffect() != EfectosKhaset.ATURDIDO.get()
                && super.canBeAffected(efecto);
    }

    @Override
    public boolean fireImmune() {
        return true;
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (!this.level().isClientSide) {
            soltarPresas(false);
            cambiar(Estado.MUERTE);
            if (this.level() instanceof ServerLevel sl)
                for (UUID u : this.guerreros)
                    if (sl.getEntity(u) instanceof GuerreroCalavera g)
                        g.deshacer(sl);
        }
    }

    @Override
    protected void tickDeath() {
        this.deathTime++;
        if (this.level() instanceof ServerLevel sl && this.deathTime % 4 == 0)
            sl.sendParticles(ParticulasKhaset.BRASA.get(), this.getX(), this.getY() + 4, this.getZ(), 25, 2, 3, 2, 0.05);
        if (this.deathTime >= 60 && !this.level().isClientSide()) {
            this.level().broadcastEntityEvent(this, (byte) 60);
            this.remove(Entity.RemovalReason.KILLED);
        }
    }

    @Override
    public void remove(Entity.RemovalReason razon) {
        if (!this.level().isClientSide)
            for (Entity e : new ArrayList<>(this.getPassengers()))
                terminarForcejeo(e);
        this.barra.removeAllPlayers();
        this.barraCalor.removeAllPlayers();
        super.remove(razon);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer jugador) {
        super.stopSeenByPlayer(jugador);
        this.barra.removePlayer(jugador);
        this.barraCalor.removePlayer(jugador);
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return this.getBoundingBox().inflate(6.0, 2.0, 6.0);
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
        tag.putInt("Fase", this.fase);
        tag.putBoolean("CoronaRota", coronaRota());
        tag.putFloat("Calor", calor());
        tag.putInt("Jugadores", this.maxJugadores);
        if (this.casa != null)
            tag.put("Casa", NbtUtils.writeBlockPos(this.casa));
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.fase = Math.max(1, tag.getInt("Fase"));
        this.entityData.set(CORONA_ROTA, tag.getBoolean("CoronaRota"));
        ponerCalor(tag.getFloat("Calor"));
        this.maxJugadores = tag.getInt("Jugadores");
        if (tag.contains("Casa"))
            this.casa = NbtUtils.readBlockPos(tag.getCompound("Casa"));
        if (this.hasCustomName())
            this.barra.setName(this.getDisplayName());
    }

    // ------------------------------------------------------------------ ayudas

    static void lanzar(LivingEntity e, Vec3 horizontal, double arriba) {
        e.setDeltaMovement(horizontal.x, arriba, horizontal.z);
        e.hasImpulse = true;
        e.hurtMarked = true;
    }

    private void empujar(LivingEntity e, double fuerza, double arriba) {
        Vec3 d = e.position().subtract(this.position()).multiply(1, 0, 1);
        if (d.lengthSqr() > 1e-4)
            lanzar(e, d.normalize().scale(fuerza), arriba);
    }

    private static double distanciaASegmento(Vec3 p, Vec3 a, Vec3 b) {
        Vec3 ab = b.subtract(a);
        double l = ab.lengthSqr();
        double u = l < 1e-8 ? 0 : Mth.clamp(p.subtract(a).dot(ab) / l, 0, 1);
        return p.distanceTo(a.add(ab.scale(u)));
    }

    /** El centro de los enemigos alrededor del objetivo (para caer sobre el grupo). */
    private Vec3 centroDelGrupo(LivingEntity objetivo) {
        Vec3 suma = Vec3.ZERO;
        int n = 0;
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, objetivo.getBoundingBox().inflate(7), this::valido)) {
            if (e.getVehicle() == this)
                continue;
            suma = suma.add(e.position());
            n++;
        }
        return n == 0 ? objetivo.position() : suma.scale(1.0 / n);
    }

    /** El piso bajo un punto (para los saltos, la serpiente, las erupciones y los guerreros). */
    private Vec3 suelo(Vec3 p) {
        BlockPos b = BlockPos.containing(p.x, p.y + 3, p.z);
        for (int i = 0; i < 10 && !this.level().getBlockState(b.below()).isSolid(); i++)
            b = b.below();
        for (int i = 0; i < 6 && this.level().getBlockState(b).isSolid(); i++)
            b = b.above();
        return new Vec3(p.x, b.getY(), p.z);
    }

    private void polvo(Vec3 p, int n) {
        if (this.level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, p.x, p.y + 0.3, p.z, Math.max(1, n / 4), 1.2, 0.2, 1.2, 0.02);
            sl.sendParticles(ParticulasKhaset.CENIZA.get(), p.x, p.y + 0.4, p.z, n, 1.5, 0.3, 1.5, 0.02);
        }
    }

    private void chispas(Vec3 p, int n) {
        if (this.level() instanceof ServerLevel sl)
            sl.sendParticles(ParticulasKhaset.BRASA.get(), p.x, p.y, p.z, n, 0.4, 0.4, 0.4, 0.1);
    }

    private void sangre(LivingEntity e) {
        if (this.level() instanceof ServerLevel sl)
            sl.sendParticles(ParticulasKhaset.SANGRE.get(), e.getX(), e.getY() + e.getBbHeight() * 0.5, e.getZ(), 14,
                    0.3, 0.3, 0.3, 0.05);
    }

    private Vec3 adelante() {
        return Vec3.directionFromRotation(0, this.getYRot());
    }

    private void mirarA(Vec3 p) {
        Vec3 d = p.subtract(this.position());
        if (d.horizontalDistanceSqr() > 1e-4)
            fijarGiro((float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f);
    }

    /** Parado; si hay un punto, gira hacia el como mucho 'max' grados por tick. */
    private void quedarse(Vec3 mirar, float max) {
        this.getNavigation().stop();
        if (mirar != null && max > 0) {
            Vec3 d = mirar.subtract(this.position());
            if (d.horizontalDistanceSqr() > 1e-4) {
                float deseado = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
                fijarGiro(this.getYRot() + Mth.clamp(Mth.wrapDegrees(deseado - this.getYRot()), -max, max));
            }
        }
        this.getMoveControl().setWantedPosition(this.getX(), this.getY(), this.getZ(), 0.0);
    }

    private void irA(Vec3 p, double velocidad) {
        this.getMoveControl().setWantedPosition(p.x, p.y, p.z, velocidad);
    }

    private void fijarGiro(float yaw) {
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    @Override
    protected BodyRotationControl createBodyControl() {
        return new BodyRotationControl(this) {
            @Override
            public void clientTick() {
                KhasetEntity.this.yBodyRot = KhasetEntity.this.getYRot();
                KhasetEntity.this.yHeadRot = KhasetEntity.this.getYRot();
            }
        };
    }

    /** Gira de a poco hacia donde va y casi no avanza si tiene que dar la vuelta. */
    private static final class Movimiento extends MoveControl {
        Movimiento(KhasetEntity jefe) {
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
            if (dx * dx + dz * dz < 0.04 || this.speedModifier <= 0) {
                this.mob.setZza(0f);
                this.mob.setSpeed(0f);
                return;
            }
            float deseado = (float) (Mth.atan2(dz, dx) * Mth.RAD_TO_DEG) - 90f;
            float giro = Mth.wrapDegrees(deseado - this.mob.getYRot());
            float yaw = this.mob.getYRot() + Mth.clamp(giro, -GIRO_CAMINAR, GIRO_CAMINAR);
            this.mob.setYRot(yaw);
            this.mob.yBodyRot = yaw;
            this.mob.yHeadRot = yaw;
            float alineado = Mth.clamp(1f - Math.abs(giro) / 90f, 0.25f, 1f);
            this.mob.setSpeed((float) (this.speedModifier * this.mob.getAttributeValue(Attributes.MOVEMENT_SPEED)) * alineado);
        }
    }

    // ------------------------------------------------------------------ animaciones (GeckoLib)

    private int inicioVisto = Integer.MIN_VALUE;

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
        controladores.add(new AnimationController<>(this, "principal", 4, this::animar)
                .setAnimationSpeedHandler(k -> k.velocidadDeAnimacion()));
    }

    /** Caminar, correr y cargar van al paso de lo que avanza de verdad (asi los pies no patinan); los ataques, al ritmo. */
    private double velocidadDeAnimacion() {
        double v = Math.hypot(this.getX() - this.xo, this.getZ() - this.zo);
        return switch (getEstado()) {
            case CAMINAR -> Mth.clamp(v / PASO_CAMINAR, 0.5, 3.0);
            case CORRER -> Mth.clamp(v / PASO_CORRER, 0.25, 1.6);
            case CARGAR, CARGAR_DOS -> Mth.clamp(v / PASO_CARGAR, 0.4, 2.5);
            default -> ritmo();
        };
    }

    private PlayState animar(AnimationState<KhasetEntity> estado) {
        Estado e = getEstado();
        if (this.inicioVisto != inicioEstado()) {                 // otro ataque igual al anterior: empieza de nuevo
            if (this.inicioVisto != Integer.MIN_VALUE && !e.bucle)
                estado.getController().forceAnimationReset();
            this.inicioVisto = inicioEstado();
        }
        RawAnimation a = e.raw;
        if (e == Estado.CAMINAR && !estado.isMoving())
            a = Estado.QUIETO.raw;
        return estado.setAndContinue(a);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
