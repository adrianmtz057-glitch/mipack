package com.mipack.khaset;

import com.mipack.Mipack;
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
import net.minecraft.sounds.SoundSource;
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
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Khaset, el ultimo rey de Thza, dios del fuego corrompido: un jefe de raid (10 o mas jugadores) con el estilo de
 * los guerreros jaguar aztecas. No busca matar: hiere (desangrado), derriba, captura y lleva a sus presas al cristal
 * del sacrificio; cada sacrificio calienta la sala. Una segunda barra, el CALOR, sube sola: si llega al tope todos
 * se queman.
 * <ul>
 * <li>Ataques: tajos (combo de 3, cada uno desangra), barrido bajo (corte de piernas: te tira de rodillas), salto del
 *     jaguar (cae sobre el grupo), dardos de atlatl (nube de veneno corto), guardia del jaguar (bloquea de frente y
 *     regresa un contraataque), silbato de la muerte (aturde y desorienta; detras de una columna te salvas).</li>
 * <li>Captura: agarra a un jugador derribado o muy herido, lo lleva al cristal (salta si esta arriba de la piramide)
 *     y lo sacrifica. Mientras lo carga recibe el doble de dano y si le bajan suficiente vida lo suelta.</li>
 * <li>Fase 2, la corona rota (50 %): se le rompen el yelmo y el penacho, puede capturar a dos e invoca a la
 *     Xiuhcoatl. Fase 3, el Quinto Sol (20 %): el calor sube 3 veces mas rapido y sacrifica donde captura.</li>
 * </ul>
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
        MUERTE("muerte", false);

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
            return this == CARGAR || this == CARGAR_DOS || this == SALTO_ALTAR || this == SACRIFICIO;
        }
    }

    public static final float ESCALA = PosesKhaset.escala();
    // vida: base mas lo que suma cada jugador que entra a la pelea
    private static final float VIDA_BASE = 300f, VIDA_POR_JUGADOR = 150f;
    private static final double RADIO_PELEA = 48.0;
    // dano
    private static final float DANO_TAJO = 8f, DANO_BARRIDO = 9f, DANO_SALTO = 12f, DANO_CONTRA = 10f, DANO_DARDO = 6f;
    private static final float DANO_APRETAR = 2f;
    // rescate: lo que hay que bajarle (fraccion de su vida maxima) mientras carga para que suelte
    private static final float RESCATE = 0.12f;
    // calor: cuanto tarda en llenarse (ticks) y cuanto sube cada sacrificio
    private static final float LLENADO_CALOR = 12000f, CALOR_SACRIFICIO = 0.15f;
    // giros (grados por tick)
    private static final float GIRO_CAMINAR = 7f, GIRO_APUNTAR = 9f;
    // a que velocidad avanza el cuerpo (bloques por tick) en acechar y correr a velocidad 1 de la animacion
    private static final double PASO_CAMINAR = 16.0 / (0.62 * 2.4) * ESCALA / 16 / 20;
    private static final double PASO_CORRER = 22.0 / (0.4 * 0.7) * ESCALA / 16 / 20;
    private static final double PASO_CARGAR = 14.0 / (0.6 * 1.6) * ESCALA / 16 / 20;

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> INICIO = SynchedEntityData.defineId(KhasetEntity.class, EntityDataSerializers.INT);
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

    private int ticksEnEstado;
    private int fase = 1;
    private BlockPos casa;
    private int maxJugadores;
    private final EnumMap<Estado, Integer> enfriar = new EnumMap<>(Estado.class);
    private final Set<UUID> golpeados = new HashSet<>();
    private final EnumSet<Estado> visitados = EnumSet.noneOf(Estado.class);
    private LivingEntity presaElegida;             // a quien va a capturar
    private Vec3 salida = Vec3.ZERO, destino = Vec3.ZERO;
    private int duracionSalto;
    private float danoEnCarga;
    private int golpesDeFrente, ventanaGolpes;
    private boolean contraPendiente;
    private boolean soltando;
    private Vec3 tipAnterior;
    private int sacrificados;
    private final List<Huella> huellas = new ArrayList<>();
    private int ticksAlTope;

    private record Huella(Vec3 p, long hasta) {
    }

    public KhasetEntity(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.setMaxUpStep(3.0f);
        this.moveControl = new Movimiento(this);
        this.xpReward = 800;
        this.setPersistenceRequired();
        this.barraCalor.setProgress(0f);
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, VIDA_BASE)
                .add(Attributes.ARMOR, 8.0)
                .add(Attributes.ARMOR_TOUGHNESS, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, 64.0)
                .add(Attributes.ATTACK_DAMAGE, DANO_TAJO);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, Estado.QUIETO.ordinal());
        this.entityData.define(INICIO, 0);
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

    /** Segundos desde que empezo el estado (igual en el servidor y en el cliente). */
    public float tiempoEnEstado(float parcial) {
        return (this.level().getGameTime() - this.entityData.get(INICIO) + parcial) / 20f;
    }

    public int inicioEstado() {
        return this.entityData.get(INICIO);
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

    private void cambiar(Estado nuevo) {
        if (Mipack.PRUEBA)
            Mipack.LOGGER.info("[Khaset] {} -> {} (vida {}/{}, calor {}, fase {})", getEstado(), nuevo, (int) getHealth(),
                    (int) getMaxHealth(), String.format("%.2f", calor()), fase);
        this.entityData.set(ESTADO, nuevo.ordinal());
        this.entityData.set(INICIO, (int) this.level().getGameTime());
        this.ticksEnEstado = 0;
        this.golpeados.clear();
        this.tipAnterior = null;
        this.visitados.add(nuevo);
    }

    private float t() {
        return this.ticksEnEstado / 20f;
    }

    /** True solo en el tick en que el estado pasa por el segundo 's'. */
    private boolean en(float s) {
        return this.ticksEnEstado == Math.round(s * 20f);
    }

    private boolean termino() {
        return this.ticksEnEstado >= PosesKhaset.ticks(getEstado().anim);
    }

    private boolean listo(Estado e) {
        return this.enfriar.getOrDefault(e, 0) <= 0;
    }

    private void enfriarA(Estado e, int ticks) {
        this.enfriar.put(e, ticks);
    }

    boolean valido(LivingEntity e) {
        if (e == null || !e.isAlive() || e == this || e instanceof KhasetEntity || e instanceof Xiuhcoatl)
            return false;
        if (this.casa != null && e.distanceToSqr(Vec3.atCenterOf(this.casa)) > RADIO_PELEA * RADIO_PELEA * 1.5)
            return false;
        if (e instanceof Player p)
            return !p.isCreative() && !p.isSpectator();
        return Mipack.PRUEBA && e instanceof Mob && !(e instanceof Xiuhcoatl);
    }

    private List<LivingEntity> enemigos(double radio) {
        return this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(radio), this::valido);
    }

    // ------------------------------------------------------------------ la pelea (servidor)

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        if (this.casa == null)
            this.casa = this.blockPosition();
        this.ticksEnEstado++;
        this.enfriar.replaceAll((k, v) -> Math.max(0, v - 1));
        if (this.ventanaGolpes > 0 && --this.ventanaGolpes == 0)
            this.golpesDeFrente = 0;
        if (this.tickCount % 20 == 0)
            participantes();
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
            case CONTRA -> contra();
            case SILBATO -> silbato();
            case AGARRAR, AGARRAR_DOS -> agarrar();
            case CARGAR, CARGAR_DOS -> cargar();
            case SOLTAR -> {
                quedarse(null, 0f);
                if (en(PosesKhasetDatos.SOLTAR))
                    soltarPresas(true);
                if (termino())
                    cambiar(Estado.CAMINAR);
            }
            case SACRIFICIO -> sacrificio();
            case INVOCAR -> invocar(objetivo);
            case CORONA -> corona();
            default -> {
            }
        }
        calorYHuellas();
    }

    private LivingEntity elegirObjetivo() {
        LivingEntity actual = this.getTarget();
        if (valido(actual) && actual.distanceToSqr(this) < 40 * 40 && this.tickCount % 40 != 0)
            return actual;
        LivingEntity mejor = null;
        double d = Double.MAX_VALUE;
        for (LivingEntity e : enemigos(40)) {
            if (e.isPassenger() && e.getVehicle() == this)
                continue;
            double dd = e.distanceToSqr(this);
            if (dd < d) {
                d = dd;
                mejor = e;
            }
        }
        this.setTarget(mejor);
        return mejor;
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
        }
    }

    /** Quien entra a la pelea suma vida (nunca baja): 300 mas 150 por jugador. */
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
        if (this.ticksEnEstado > 6) {
            Estado ataque = elegirAtaque(objetivo, d);
            if (ataque != null) {
                cambiar(ataque);
                return;
            }
        }
        if (this.presaElegida != null) {
            irA(this.presaElegida.position(), 1.6);
            return;
        }
        if (d > 18 && this.ticksEnEstado > 20) {
            cambiar(Estado.CORRER);
            return;
        }
        if (d > 4.0)
            irA(objetivo.position(), 0.9);
        else
            quedarse(objetivo.position(), GIRO_CAMINAR);
    }

    private void correr(LivingEntity objetivo) {
        if (objetivo == null || this.ticksEnEstado > 120) {
            cambiar(Estado.CAMINAR);
            return;
        }
        LivingEntity hacia = this.presaElegida != null ? this.presaElegida : objetivo;
        irA(hacia.position(), 2.2);
        double d = this.distanceTo(hacia);
        Estado ataque = elegirAtaque(objetivo, this.distanceTo(objetivo));
        if (ataque != null && this.ticksEnEstado > 4)
            cambiar(ataque);
        else if (d < 7 && this.presaElegida == null)
            cambiar(Estado.CAMINAR);
    }

    /** El repertorio: segun la distancia, lo que este listo y la fase (con un poco de azar). */
    private Estado elegirAtaque(LivingEntity objetivo, double d) {
        // capturar va primero: alguien derribado o muy herido cerca
        if (listo(Estado.AGARRAR)) {
            List<LivingEntity> presas = new ArrayList<>();
            for (LivingEntity e : enemigos(18))
                if (EfectosKhaset.capturable(e) && !e.isPassenger())
                    presas.add(e);
            if (!presas.isEmpty()) {
                presas.sort((a, b) -> Double.compare(a.distanceToSqr(this), b.distanceToSqr(this)));
                LivingEntity p = presas.get(0);
                this.presaElegida = p;
                if (this.distanceTo(p) < 5.6) {
                    boolean dos = this.fase >= 2 && presas.size() >= 2 && presas.get(1).distanceTo(this) < 7.5;
                    return dos ? Estado.AGARRAR_DOS : Estado.AGARRAR;
                }
                return null;                                     // se acerca (caminar/correr van hacia la presa)
            }
        }
        this.presaElegida = null;
        List<Estado> op = new ArrayList<>();
        List<Integer> peso = new ArrayList<>();
        int cerca = enemigos(20).size();
        if (listo(Estado.SILBATO) && (cerca >= 2 || this.random.nextInt(400) == 0) && d < 22) {
            op.add(Estado.SILBATO);
            peso.add(this.fase == 3 ? 4 : 2);
        }
        if (d < 6.5) {
            if (listo(Estado.TAJOS)) {
                op.add(Estado.TAJOS);
                peso.add(4);
            }
            if (listo(Estado.BARRIDO)) {
                op.add(this.random.nextBoolean() ? Estado.BARRIDO : Estado.BARRIDO_I);
                peso.add(3);
            }
        } else if (d < 16) {
            if (listo(Estado.SALTO) && d > 7) {
                op.add(Estado.SALTO);
                peso.add(3);
            }
            if (listo(Estado.DARDO) && d > 9) {
                op.add(Estado.DARDO);
                peso.add(2);
            }
            if (this.fase >= 2 && listo(Estado.INVOCAR)) {
                op.add(Estado.INVOCAR);
                peso.add(2);
            }
        } else {
            if (listo(Estado.DARDO)) {
                op.add(Estado.DARDO);
                peso.add(3);
            }
            if (this.fase >= 2 && listo(Estado.INVOCAR)) {
                op.add(Estado.INVOCAR);
                peso.add(2);
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

    private void tajos(LivingEntity objetivo) {
        if (t() < 0.3f && objetivo != null)
            quedarse(objetivo.position(), GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        float[] g = PosesKhasetDatos.GOLPES_ZARPAZOS;
        if (en(g[0]))
            golpeGarra("zarpazos", 'd', g[0]);
        if (en(g[1]))
            golpeGarra("zarpazos", 'i', g[1]);
        if (en(g[2])) {
            golpeGarra("zarpazos", 'd', g[2]);
            golpeGarra("zarpazos", 'i', g[2]);
        }
        if (termino()) {
            enfriarA(Estado.TAJOS, 40);
            cambiar(Estado.CAMINAR);
        }
    }

    /** Un tajo: lo que este a menos de 2.6 bloques de la punta de la garra (o en el frente cercano) recibe el corte. */
    private void golpeGarra(String anim, char lado, float s) {
        Vec3 punta = PosesKhaset.aMundo(this, this.getYRot(), PosesKhaset.mano(anim, lado, PosesKhaset.Punto.PUNTA, s, false), ESCALA);
        this.golpeados.clear();
        for (LivingEntity e : enemigos(10)) {
            AABB caja = e.getBoundingBox().inflate(2.0);
            if (caja.contains(punta) || e.getBoundingBox().getCenter().distanceTo(punta) < 2.6) {
                e.hurt(this.damageSources().mobAttack(this), DANO_TAJO);
                EfectosKhaset.cortar(e, 1);
                e.setSecondsOnFire(2);
                empujar(e, 0.6, 0.25);
            }
        }
        chispas(punta, 10);
        this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0f, 0.6f);
    }

    private void barrido(LivingEntity objetivo) {
        float[] b = PosesKhasetDatos.BARRIDO;
        if (t() < 0.6f && objetivo != null)
            quedarse(objetivo.position(), GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        String anim = getEstado().anim;
        char lado = getEstado() == Estado.BARRIDO ? 'd' : 'i';
        if (t() >= b[0] - 0.05f && t() <= b[1] + 0.05f) {
            Vec3 punta = PosesKhaset.aMundo(this, this.getYRot(), PosesKhaset.mano(anim, lado, PosesKhaset.Punto.PUNTA, t(), false), ESCALA);
            Vec3 antes = this.tipAnterior == null ? punta : this.tipAnterior;
            for (LivingEntity e : enemigos(10)) {
                if (this.golpeados.contains(e.getUUID()))
                    continue;
                AABB caja = e.getBoundingBox();
                if (caja.minY > this.getY() + 2.8)
                    continue;                                    // brincando muy alto se esquiva
                Vec3 c = new Vec3(caja.getCenter().x, Math.min(caja.getCenter().y, this.getY() + 0.8), caja.getCenter().z);
                if (distanciaASegmento(c, antes, punta) < 1.4 + e.getBbWidth() / 2) {
                    this.golpeados.add(e.getUUID());
                    e.hurt(this.damageSources().mobAttack(this), DANO_BARRIDO);
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
        if (termino()) {
            enfriarA(Estado.BARRIDO, 70);
            cambiar(Estado.CAMINAR);
        }
    }

    /** Salto del jaguar (sobre el grupo) o salto al altar con la presa: se agacha, salta en arco y cae. */
    private void salto(LivingEntity objetivo, boolean alAltar) {
        float s0 = PosesKhasetDatos.SALTO;
        int despega = Math.round(s0 * 20f);
        if (this.ticksEnEstado == 1) {
            this.salida = this.position();
            if (alAltar) {
                this.destino = puntoDelAltar();
            } else {
                Vec3 centro = objetivo != null ? centroDelGrupo(objetivo) : this.position().add(adelante().scale(8));
                Vec3 d = centro.subtract(this.position());
                double largo = Math.min(14.0, d.horizontalDistance());
                this.destino = suelo(this.position().add(new Vec3(d.x, 0, d.z).normalize().scale(Math.max(2.0, largo - 1.5))));
                AvisoKhaset.poner(this.level(), this.destino, 4.5f, despega + 10, 0xFF7A1E);
            }
            this.duracionSalto = 10;
        }
        if (this.ticksEnEstado < despega) {
            quedarse(this.destino, GIRO_APUNTAR * 2);
        } else if (this.ticksEnEstado <= despega + this.duracionSalto) {
            float u = (this.ticksEnEstado - despega) / (float) this.duracionSalto;
            double alto = 3.5 + Math.max(0, this.destino.y - this.salida.y);
            Vec3 p = this.salida.lerp(this.destino, u).add(0, alto * 4 * u * (1 - u), 0);
            this.setDeltaMovement(Vec3.ZERO);
            this.move(MoverType.SELF, p.subtract(this.position()));
            this.fallDistance = 0;
            if (this.ticksEnEstado == despega + this.duracionSalto)
                aterrizar(alAltar);
        } else {
            quedarse(null, 0f);
        }
        if (termino()) {
            if (alAltar) {
                cambiar(Estado.SACRIFICIO);
            } else {
                enfriarA(Estado.SALTO, 140);
                cambiar(Estado.CAMINAR);
            }
        }
    }

    private void aterrizar(boolean alAltar) {
        polvo(this.position(), 30);
        this.playSound(SoundEvents.GENERIC_EXPLODE, 2.0f, 0.6f);
        if (alAltar)
            return;
        for (LivingEntity e : enemigos(6)) {
            double d = e.position().distanceTo(this.position());
            if (d > 4.5)
                continue;
            e.hurt(this.damageSources().mobAttack(this), DANO_SALTO * (float) (1.0 - 0.5 * d / 4.5));
            Vec3 fuera = e.position().subtract(this.position()).multiply(1, 0, 1);
            fuera = fuera.lengthSqr() < 1e-4 ? adelante() : fuera.normalize();
            lanzar(e, fuera.scale(1.1), 0.45);
            if (d < 2.5)
                EfectosKhaset.derribar(e, 40);
        }
    }

    private void dardo(LivingEntity objetivo) {
        if (objetivo != null && t() < PosesKhasetDatos.DARDO)
            quedarse(objetivo.position(), GIRO_APUNTAR);
        else
            quedarse(null, 0f);
        if (en(PosesKhasetDatos.DARDO) && objetivo != null) {
            Vec3 mano = PosesKhaset.aMundo(this, this.getYRot(),
                    PosesKhaset.mano("lanzar_dardo", 'd', PosesKhaset.Punto.PALMA, PosesKhasetDatos.DARDO, false), ESCALA);
            int n = this.fase >= 2 ? 3 : 1;
            for (int i = 0; i < n; i++) {
                float abre = n == 1 ? 0f : (i - 1) * 9f;
                DardoAtlatl.lanzar(this.level(), this, mano, objetivo, abre, coronaRota());
            }
            this.playSound(SoundEvents.TRIDENT_THROW, 2.0f, 0.7f);
        }
        if (termino()) {
            enfriarA(Estado.DARDO, 80);
            cambiar(Estado.CAMINAR);
        }
    }

    private void guardia(LivingEntity objetivo) {
        quedarse(objetivo == null ? null : objetivo.position(), 4f);
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

    private void contra() {
        quedarse(null, 0f);
        if (en(PosesKhasetDatos.CONTRA)) {
            Vec3 adelante = adelante();
            for (LivingEntity e : enemigos(8)) {
                Vec3 d = e.position().subtract(this.position()).multiply(1, 0, 1);
                if (d.length() < 7.0 && d.normalize().dot(adelante) > 0.2) {
                    e.hurt(this.damageSources().mobAttack(this), DANO_CONTRA);
                    EfectosKhaset.cortar(e, 1);
                    lanzar(e, d.normalize().scale(1.4), 0.5);
                }
            }
            chispas(this.position().add(adelante.scale(3)).add(0, 4, 0), 20);
            this.playSound(SoundEvents.PLAYER_ATTACK_STRONG, 3.0f, 0.5f);
        }
        if (termino())
            cambiar(Estado.CAMINAR);
    }

    /** El silbato de la muerte: aturde y desorienta a quien lo oiga de frente (sin un bloque en medio). */
    private void silbato() {
        quedarse(null, 0f);
        if (en(0.6f)) {
            Vec3 cabeza = this.position().add(0, 8.0, 0);
            for (LivingEntity e : enemigos(28)) {
                if (e.distanceTo(this) > 28)
                    continue;
                HitResult r = this.level().clip(new ClipContext(cabeza, e.getEyePosition(), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, this));
                if (r.getType() == HitResult.Type.BLOCK)
                    continue;                                    // detras de una columna: se salva
                e.addEffect(new MobEffectInstance(EfectosKhaset.ATURDIDO.get(), 30, 0, false, false, true));
                e.addEffect(new MobEffectInstance(EfectosKhaset.DESORIENTADO.get(), 120, 0, false, false, true));
            }
            if (this.level() instanceof ServerLevel sl)
                for (int i = 0; i < 3; i++)
                    sl.sendParticles(ParticleTypes.SONIC_BOOM, cabeza.x + adelante().x * (2 + i * 3), cabeza.y - i,
                            cabeza.z + adelante().z * (2 + i * 3), 1, 0, 0, 0, 0);
            this.playSound(SoundEvents.WARDEN_SONIC_BOOM, 3.0f, 1.4f);
        }
        if (termino()) {
            enfriarA(Estado.SILBATO, this.fase == 3 ? 260 : 400);
            cambiar(Estado.CAMINAR);
        }
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
                Vec3 palma = PosesKhaset.aMundo(this, this.getYRot(),
                        PosesKhaset.mano(getEstado().anim, lado, PosesKhaset.Punto.PALMA, PosesKhasetDatos.AGARRA, false), ESCALA);
                LivingEntity mejor = null;
                double d = 2.8;
                for (LivingEntity e : enemigos(10)) {
                    if (!EfectosKhaset.capturable(e) || e.isPassenger())
                        continue;
                    double dd = e.getBoundingBox().getCenter().distanceTo(palma);
                    if (dd < d) {
                        d = dd;
                        mejor = e;
                    }
                }
                if (mejor != null && mejor.startRiding(this, true)) {
                    this.entityData.set(lado == 'd' ? PRESA_D : PRESA_I, mejor.getId());
                    mejor.removeEffect(EfectosKhaset.DERRIBADO.get());
                    this.playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2.0f, 0.5f);
                }
            }
            this.danoEnCarga = 0;
        }
        if (termino()) {
            this.presaElegida = null;
            if (presas().isEmpty()) {
                enfriarA(Estado.AGARRAR, 60);
                cambiar(Estado.CAMINAR);
            } else if (this.fase >= 3) {
                cambiar(dos ? Estado.CARGAR_DOS : Estado.CARGAR);    // en el Quinto Sol: casi en el lugar
            } else {
                cambiar(dos && presas().size() > 1 ? Estado.CARGAR_DOS : Estado.CARGAR);
            }
        }
    }

    private void cargar() {
        if (presas().isEmpty()) {
            cambiar(Estado.CAMINAR);
            return;
        }
        if (this.ticksEnEstado % 20 == 10)
            for (LivingEntity p : presas())
                p.hurt(this.damageSources().mobAttack(this), DANO_APRETAR);
        if (this.danoEnCarga >= this.getMaxHealth() * RESCATE) {
            cambiar(Estado.SOLTAR);
            return;
        }
        CristalSacrificio cristal = this.fase >= 3 ? null : cristalCercano();
        this.entityData.set(CRISTAL, cristal == null ? -1 : cristal.getId());
        if (cristal == null) {
            quedarse(null, 0f);
            if (this.ticksEnEstado >= (this.fase >= 3 ? 50 : 60))
                cambiar(Estado.SACRIFICIO);                      // sin cristal (o en el Quinto Sol): ahi mismo
            return;
        }
        cristal.llamar();
        Vec3 donde = puntoDelAltar();
        double dh = donde.subtract(this.position()).horizontalDistance();
        if (dh < 1.2) {
            mirarA(cristal.position());
            cambiar(Estado.SACRIFICIO);
        } else if (dh < 14 && donde.y - this.getY() > 1.5) {
            cambiar(Estado.SALTO_ALTAR);
        } else if (this.ticksEnEstado > 500) {
            cambiar(Estado.SACRIFICIO);
        } else {
            irA(donde, 1.1);
        }
    }

    private void sacrificio() {
        float[] s = PosesKhasetDatos.SACRIFICIO;
        CristalSacrificio cristal = cristalPorId();
        if (cristal != null && this.ticksEnEstado < 3)
            mirarA(cristal.position());
        quedarse(null, 0f);
        if (cristal != null && t() < s[1])
            cristal.llamar();
        if (t() < s[1] && this.danoEnCarga >= this.getMaxHealth() * RESCATE) {
            cambiar(Estado.SOLTAR);
            return;
        }
        if (en(s[1])) {
            for (LivingEntity p : presas()) {
                p.hurt(EfectosKhaset.fuente(this.level(), EfectosKhaset.SACRIFICIO, this), 10000f);
                sangre(p);
                if (!p.isAlive())
                    this.sacrificados++;
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
            ponerCalor(calor() + CALOR_SACRIFICIO * Math.max(1, muertos));
            this.heal(this.getMaxHealth() * 0.05f * Math.max(1, muertos));
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
            enfriarA(Estado.AGARRAR, 120);
            cambiar(Estado.CAMINAR);
        }
    }

    private void invocar(LivingEntity objetivo) {
        quedarse(objetivo == null ? null : objetivo.position(), t() < 0.6f ? GIRO_APUNTAR : 0f);
        float s = PosesKhasetDatos.INVOCA;
        Vec3 manos = PosesKhaset.mano("invocar", 'd', PosesKhaset.Punto.PALMA, s, false)
                .add(PosesKhaset.mano("invocar", 'i', PosesKhaset.Punto.PALMA, s, false)).scale(0.5);
        Vec3 donde = suelo(PosesKhaset.aMundo(this, this.getYRot(), new Vec3(manos.x, 0, manos.z - 6), ESCALA));
        if (this.ticksEnEstado == 1)
            AvisoKhaset.poner(this.level(), donde, 2.5f, Math.round(s * 20f) + 6, 0x37D6C0);
        if (en(s)) {
            Xiuhcoatl x = new Xiuhcoatl(Mipack.XIUHCOATL.get(), this.level());
            x.moveTo(donde.x, donde.y, donde.z, this.getYRot(), 0f);
            x.dueno(this, objetivo);
            this.level().addFreshEntity(x);
            polvo(donde, 30);
            this.playSound(SoundEvents.BLAZE_SHOOT, 3.0f, 0.4f);
        }
        if (termino()) {
            enfriarA(Estado.INVOCAR, 400);
            cambiar(Estado.CAMINAR);
        }
    }

    private void corona() {
        quedarse(null, 0f);
        if (en(PosesKhasetDatos.CORONA)) {
            this.entityData.set(CORONA_ROTA, true);
            Vec3 c = this.position().add(PosesKhaset.rotar(this.getYRot(), new Vec3(-0.9, 8.4, -2.0)));
            if (this.level() instanceof ServerLevel sl) {
                sl.sendParticles(ParticulasKhaset.PLUMA.get(), c.x, c.y + 1.0, c.z, 45, 1.2, 0.8, 1.2, 0.12);
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.ORANGE_TERRACOTTA.defaultBlockState()),
                        c.x, c.y, c.z, 40, 0.8, 0.6, 0.8, 0.3);
                sl.sendParticles(ParticleTypes.FLAME, c.x, c.y, c.z, 30, 0.8, 0.8, 0.8, 0.1);
            }
            this.playSound(SoundEvents.ITEM_BREAK, 3.0f, 0.5f);
            this.playSound(SoundEvents.RAVAGER_ROAR, 4.0f, 0.5f);
        }
        if (termino()) {
            this.enfriar.put(Estado.INVOCAR, 60);
            cambiar(Estado.CAMINAR);
        }
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

    /** Suelta a las presas (con caida lenta para que no se maten); 'golpe': las suelta de dolor. */
    private void soltarPresas(boolean golpe) {
        this.soltando = true;
        for (Entity e : new ArrayList<>(this.getPassengers())) {
            e.stopRiding();
            if (e instanceof LivingEntity le && le.isAlive()) {
                le.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 50, 0, false, false));
                if (golpe)
                    lanzar(le, adelante().scale(0.4), 0.2);
            }
        }
        this.soltando = false;
        this.entityData.set(PRESA_D, -1);
        this.entityData.set(PRESA_I, -1);
        if (golpe)
            enfriarA(Estado.AGARRAR, 200);
    }

    public boolean soltando() {
        return this.soltando || !this.isAlive();
    }

    @Override
    protected boolean canAddPassenger(Entity e) {
        return this.getPassengers().size() < 2;
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
            Vec3 a = altarDelSacrificio();
            Vec3 eje = PosesKhaset.rotar(giro, new Vec3(1, 0, 0));
            return lado == 'd' ? a.add(eje.scale(0.45)) : a.subtract(eje.scale(0.65));
        }
        String anim;
        boolean bucle = false;
        switch (e) {
            case AGARRAR, AGARRAR_DOS, SOLTAR, SACRIFICIO -> anim = e.anim;
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

    // ---- el calor

    private void calorYHuellas() {
        boolean pelea = getEstado() != Estado.QUIETO && !enemigos(RADIO_PELEA).isEmpty();
        if (pelea)
            ponerCalor(calor() + (this.fase >= 3 ? 3f : 1f) / LLENADO_CALOR);
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
        if (fuente.getDirectEntity() instanceof DardoAtlatl || quien instanceof Xiuhcoatl || quien == this
                || fuente.is(EfectosKhaset.CALOR))
            return false;
        if (quien != null && !this.level().isClientSide) {
            Vec3 d = quien.position().subtract(this.position()).multiply(1, 0, 1);
            boolean deFrente = d.lengthSqr() > 1e-4 && d.normalize().dot(adelante()) > 0.3;
            if (e == Estado.GUARDIA && deFrente) {
                this.contraPendiente = true;
                this.playSound(SoundEvents.SHIELD_BLOCK, 2.0f, 0.5f);
                return false;
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
        if (e.cargando() && e != Estado.SALTO_ALTAR) {
            if (quien != null && quien.getVehicle() == this) {
                this.danoEnCarga += cantidad * 0.5f;              // la presa forcejea: cuenta, pero poco
            } else {
                cantidad *= 2f;                                   // mientras carga a la presa: doble dano
                this.danoEnCarga += cantidad;
            }
        }
        return super.hurt(fuente, cantidad);
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
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, objetivo.getBoundingBox().inflate(6), this::valido)) {
            suma = suma.add(e.position());
            n++;
        }
        return n == 0 ? objetivo.position() : suma.scale(1.0 / n);
    }

    /** El piso bajo un punto (para los saltos y la serpiente). */
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

    /** Caminar, correr y cargar van al paso de lo que avanza de verdad (asi los pies no patinan). */
    private double velocidadDeAnimacion() {
        double v = Math.hypot(this.getX() - this.xo, this.getZ() - this.zo);
        return switch (getEstado()) {
            case CAMINAR -> Mth.clamp(v / PASO_CAMINAR, 0.5, 3.0);
            case CORRER -> Mth.clamp(v / PASO_CORRER, 0.25, 1.5);
            case CARGAR, CARGAR_DOS -> Mth.clamp(v / PASO_CARGAR, 0.4, 2.5);
            default -> 1.0;
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
