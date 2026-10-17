package com.mipack.bruma;

import com.mipack.Amenaza;
import com.mipack.Dificultad;
import com.mipack.Golpes;
import com.mipack.Mipack;
import com.mipack.khaset.PosesKhaset;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.AABB;
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
 * La Bruma negra: un espectro enorme y flaco hecho de jirones, que flota encorvado dentro de su propia bruma.
 * <ul>
 * <li>LA BRUMA: a su alrededor todo se oscurece (Oscuridad a los que esten cerca) y se APAGAN LAS LUCES: antorchas y
 *     faroles se caen, las fogatas y las velas se apagan. La barra de jefe oscurece el cielo y trae niebla.</li>
 * <li>FORMA DE NIEBLA: casi no se le puede pegar (le entra una parte del dano) salvo cuando ataca, con fuego, o con
 *     LUZ FUERTE: las luces que no puede apagar (piedra luminosa, linterna de mar, luz de hongo, ranaluces...) la
 *     obligan a tomar cuerpo mientras este cerca de ellas. La forma corporea se ve solida; la de niebla, translucida.</li>
 * <li>ZARPAZO: la garra grande barre lo que tiene enfrente y deja marchitez.</li>
 * <li>AGARRAR y DRENAR: te levanta con la mano y te chupa el alma (vida que ella recupera, hambre); te suelta si los
 *     demas le pegan lo suficiente, si hay luz fuerte, si se te acaba el tiempo o si te salva un totem.</li>
 * <li>GRITO: se encoge y grita: dano de magia, oscuridad, lentitud, debilidad y te congela; tras una pared no te
 *     alcanza.</li>
 * <li>JIRONES: si tiene a varios encima, gira y los azota con las tiras (los avienta).</li>
 * <li>ATRAVESAR: se deshace en bruma, cruza paredes y aparece detras de alguien (asi tambien se zafa de los atorones).</li>
 * <li>Fase 2 (mitad de vida): se alza y la bruma crece; apaga mas lejos y mas seguido, ataca mas rapido y salen
 *     almas en pena (vexes que viven poco) a ayudarle.</li>
 * </ul>
 * Vida: 1200 mas 700 por jugador (por lo que diga /bruma difficult). Los tiempos (ticks) son los de sus animaciones
 * (taller/personajes/bruma_anim.py); el modelo (taller/personajes/bruma.py) mide 1.85 bloques y se dibuja ESCALA veces.
 */
public class BrumaEntity extends Monster implements GeoEntity {
    public enum Estado { QUIETO, ACECHAR, ZARPAZO, AGARRAR, DRENAR, GRITO, DISOLVERSE, VIAJAR, APARECER, JIRONES, FASE2, MUERTE }

    /** Cuanto crece el modelo en el juego (el render lo usa): unos 6 bloques de alto. */
    public static final float ESCALA = 3.2f;

    // duraciones de las animaciones (ticks) y sus momentos
    private static final int T_ZARPAZO = 20, GOLPE_ZARPAZO = 10, T_AGARRAR = 16, MANO_CIERRA = 10, T_GRITO = 40, SALE_GRITO = 14;
    private static final int T_DISOLVERSE = 14, T_APARECER = 14, MAX_VIAJE = 40, T_JIRONES = 24, T_FASE2 = 48, T_MUERTE = 60;
    private static final float VIDA_BASE = 1200f, VIDA_POR_JUGADOR = 700f;
    private static final float DANO_ZARPAZO = 14f, DANO_JIRONES = 10f, DANO_GRITO = 8f, DANO_DRENAR = 3f;
    private static final double RADIO_PELEA = 64.0, VISTA = 80.0;
    private static final double ALCANCE = 5.5, RADIO_JIRONES = 6.5, RADIO_GRITO = 14.0, RADIO_GRITO_2 = 20.0;
    private static final double RADIO_BRUMA = 14.0, RADIO_BRUMA_2 = 22.0, RADIO_APAGAR = 10, RADIO_APAGAR_2 = 15;
    /** Lo que tiene que alumbrar un bloque (0-15) para obligarla a tomar cuerpo, y a cuantos bloques de su cuerpo. */
    private static final int LUZ_FUERTE = 13;
    private static final double RADIO_LUZ = 4.5;
    /** La palma derecha en la animacion de drenar, en px del modelo (de bruma_anim.py; la presa cuelga de ahi). */
    private static final Vec3 MANO_DRENAR = new Vec3(4.9, 32.2, -17.6);

    /**
     * Lo que cambia con la dificultad (la vida y el dano los multiplica Dificultad.Nivel): cuanto drena como mucho
     * (ticks), que parte de su vida tienen que bajarle para que suelte, cada cuanto grita, cuantas almas en pena salen
     * como mucho y que parte del dano le entra en forma de niebla.
     */
    private record Ajustes(int drenar, float rescate, int gritoCada, int almas, float niebla) {
    }

    private static final Ajustes EASY = new Ajustes(80, 0.03f, 420, 2, 0.5f);
    private static final Ajustes NORMAL = new Ajustes(100, 0.05f, 320, 4, 0.35f);
    private static final Ajustes HARDCORE = new Ajustes(140, 0.07f, 240, 8, 0.25f);

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(BrumaEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> FASE2 = SynchedEntityData.defineId(BrumaEntity.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> CORPOREA = SynchedEntityData.defineId(BrumaEntity.class, EntityDataSerializers.BOOLEAN);

    private static final RawAnimation A_FLOTAR = RawAnimation.begin().thenLoop("animation.bruma.flotar");
    private static final RawAnimation A_AVANZAR = RawAnimation.begin().thenLoop("animation.bruma.avanzar");
    private static final RawAnimation A_ZARPAZO = RawAnimation.begin().thenPlay("animation.bruma.zarpazo");
    private static final RawAnimation A_AGARRAR = RawAnimation.begin().thenPlay("animation.bruma.agarrar").thenLoop("animation.bruma.drenar");
    private static final RawAnimation A_GRITO = RawAnimation.begin().thenPlay("animation.bruma.grito");
    private static final RawAnimation A_DISOLVERSE = RawAnimation.begin().thenPlayAndHold("animation.bruma.disolverse");
    private static final RawAnimation A_APARECER = RawAnimation.begin().thenPlay("animation.bruma.aparecer");
    private static final RawAnimation A_JIRONES = RawAnimation.begin().thenPlay("animation.bruma.jirones");
    private static final RawAnimation A_FASE2 = RawAnimation.begin().thenPlay("animation.bruma.fase2");
    private static final RawAnimation A_MUERTE = RawAnimation.begin().thenPlayAndHold("animation.bruma.muerte");

    private static final DustParticleOptions NEGRA = new DustParticleOptions(new Vector3f(0.05f, 0.05f, 0.06f), 1.6f);
    private static final DustParticleOptions GRIS = new DustParticleOptions(new Vector3f(0.18f, 0.19f, 0.21f), 1.2f);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final ServerBossEvent barra = (ServerBossEvent) new ServerBossEvent(this.getDisplayName(), BossEvent.BossBarColor.WHITE,
            BossEvent.BossBarOverlay.NOTCHED_10).setDarkenScreen(true).setCreateWorldFog(true);
    private final Amenaza amenaza = new Amenaza();
    private final Set<UUID> golpeados = new HashSet<>();
    private final EnumSet<Estado> visitados = EnumSet.noneOf(Estado.class);
    private final List<UUID> almas = new ArrayList<>();
    private final Set<UUID> objetivos = new HashSet<>();
    private int ticksEnEstado, maxJugadores, corporeaHasta, atascado;
    private int enfriar = 20, enfriarGrito = 120, enfriarAgarre = 100, enfriarJirones = 80, enfriarViaje = 160, enfriarAlmas;
    private boolean grito0, soltando, enLuz, avisoLuz;
    private LivingEntity presa;
    private float danoEnDrenaje;
    private int apagadas, drenados;                                // para las pruebas
    private Vec3 destino = Vec3.ZERO;

    public BrumaEntity(EntityType<? extends Monster> tipo, Level nivel) {
        super(tipo, nivel);
        this.setNoGravity(true);
        this.xpReward = 700;
        this.setPersistenceRequired();
    }

    public static AttributeSupplier.Builder atributos() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, VIDA_BASE)
                .add(Attributes.ARMOR, 4.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.3)
                .add(Attributes.FOLLOW_RANGE, VISTA)
                .add(Attributes.ATTACK_DAMAGE, DANO_ZARPAZO);
    }

    private Dificultad.Nivel nivel() {
        return Dificultad.de(this.level(), Dificultad.Jefe.BRUMA);
    }

    private Ajustes ajustes() {
        return switch (nivel()) {
            case EASY -> EASY;
            case NORMAL -> NORMAL;
            case HARDCORE -> HARDCORE;
        };
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, Estado.QUIETO.ordinal());
        this.entityData.define(FASE2, false);
        this.entityData.define(CORPOREA, false);
    }

    public Estado getEstado() {
        return Estado.values()[this.entityData.get(ESTADO)];
    }

    public boolean fase2() {
        return this.entityData.get(FASE2);
    }

    /** Solida (le entra todo el dano) o de niebla (translucida, casi intangible). */
    public boolean corporea() {
        return this.entityData.get(CORPOREA);
    }

    /** Viaja como bruma: no se dibuja ni se le puede pegar. */
    public boolean escondida() {
        return getEstado() == Estado.VIAJAR;
    }

    public boolean soltando() {
        return this.soltando;
    }

    // para las pruebas
    public Set<Estado> visitados() {
        return this.visitados;
    }

    public int perseguidos() {
        return this.objetivos.size();
    }

    public int apagadas() {
        return this.apagadas;
    }

    public int drenados() {
        return this.drenados;
    }

    public boolean enLuz() {
        return this.enLuz;
    }

    public int almasVivas() {
        return this.level() instanceof ServerLevel sl ? (int) this.almas.stream().filter(u -> sl.getEntity(u) != null).count() : 0;
    }

    private void cambiar(Estado nuevo) {
        if (Mipack.PRUEBA)
            Mipack.LOGGER.info("[Bruma] {} -> {} (vida {})", getEstado(), nuevo, (int) getHealth());
        this.entityData.set(ESTADO, nuevo.ordinal());
        this.ticksEnEstado = 0;
        this.visitados.add(nuevo);
        this.golpeados.clear();
    }

    private boolean valido(LivingEntity e) {
        if (e == null || !e.isAlive() || e == this || e instanceof BrumaEntity || esAlma(e))
            return false;
        if (e instanceof Player p)
            return !p.isCreative() && !p.isSpectator();
        return Mipack.PRUEBA && e instanceof Mob && !(e instanceof Vex) && !(e instanceof com.mipack.khaset.KhasetEntity)
                && !(e instanceof com.mipack.entidad.CrackatosEntity);
    }

    private boolean esAlma(Entity e) {
        return e instanceof Vex v && this.almas.contains(v.getUUID());
    }

    private List<LivingEntity> enemigos(double radio) {
        return this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(radio, radio * 0.6, radio), this::valido);
    }

    private LivingEntity escoger(boolean cambiar) {
        LivingEntity e = this.amenaza.escoger(this, enemigos(VISTA), cambiar, 30.0, this.level().getGameTime(), this.random);
        this.setTarget(e);
        if (e != null && this.objetivos.add(e.getUUID()) && Mipack.PRUEBA)
            Mipack.LOGGER.info("[Bruma] persigue a {} ({} distintos)", e.getName().getString(), this.objetivos.size());
        return e;
    }

    // ------------------------------------------------------------------ la pelea (servidor)

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        Estado e = getEstado();
        if (e == Estado.MUERTE)
            return;
        this.ticksEnEstado++;
        this.enfriar--;
        this.enfriarGrito--;
        this.enfriarAgarre--;
        this.enfriarJirones--;
        this.enfriarViaje--;
        this.enfriarAlmas--;
        if (this.tickCount % 20 == 0) {
            participantes();
            this.amenaza.olvidar();
            bruma();
        }
        if (this.tickCount % (fase2() ? 20 : 40) == 0 && getTarget() != null)
            apagarLuces();
        luz();
        this.entityData.set(CORPOREA, this.enLuz || this.tickCount < this.corporeaHasta || this.isOnFire()
                || e == Estado.ZARPAZO || e == Estado.AGARRAR || e == Estado.DRENAR || e == Estado.GRITO || e == Estado.JIRONES);
        this.barra.setProgress(this.getHealth() / this.getMaxHealth());
        if (!fase2() && this.getHealth() < this.getMaxHealth() * 0.5f && e != Estado.FASE2 && e != Estado.AGARRAR
                && e != Estado.DRENAR && e != Estado.VIAJAR && e != Estado.DISOLVERSE) {
            cambiar(Estado.FASE2);
            e = Estado.FASE2;
        }
        if (fase2() && this.enfriarAlmas <= 0 && getTarget() != null)
            almasEnPena();
        LivingEntity objetivo = getTarget();
        if (!valido(objetivo))
            objetivo = escoger(false);
        switch (e) {
            case QUIETO -> quieto(objetivo);
            case ACECHAR -> acechar(objetivo);
            case ZARPAZO -> zarpazo(objetivo);
            case AGARRAR -> agarrar(objetivo);
            case DRENAR -> drenar();
            case GRITO -> grito();
            case DISOLVERSE -> disolverse(objetivo);
            case VIAJAR -> viajar();
            case APARECER -> aparecer(objetivo);
            case JIRONES -> jirones();
            case FASE2 -> faseDos();
            default -> {
            }
        }
    }

    /** Quien entra a la pelea suma vida (nunca baja): 1200 mas 700 por jugador, por lo que diga la dificultad. */
    private void participantes() {
        int n = 0;
        for (Player p : this.level().players())
            if (valido(p) && p.distanceToSqr(this) < RADIO_PELEA * RADIO_PELEA)
                n++;
        this.maxJugadores = Math.max(this.maxJugadores, n);
        float antes = this.getMaxHealth(), ahora = (VIDA_BASE + VIDA_POR_JUGADOR * this.maxJugadores) * nivel().vida;
        if (Math.abs(ahora - antes) > 0.5f) {
            this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(ahora);
            this.setHealth(this.getHealth() * ahora / antes);
        }
    }

    /** La bruma: oscuridad a los de cerca (y debilidad en la fase 2). */
    private void bruma() {
        double r = fase2() ? RADIO_BRUMA_2 : RADIO_BRUMA;
        for (LivingEntity v : enemigos(r)) {
            if (v.distanceToSqr(this) > r * r)
                continue;
            v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 70, 0, true, false), this);
            if (fase2())
                v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 50, 0, true, false), this);
        }
    }

    /** Se apagan las luces: antorchas y faroles se caen; fogatas y velas se apagan. Las luces fuertes no. */
    private void apagarLuces() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        int r = (int) (fase2() ? RADIO_APAGAR_2 : RADIO_APAGAR), n = 0;
        BlockPos c = this.blockPosition().above(2);
        for (BlockPos p : BlockPos.betweenClosed(c.offset(-r, -r, -r), c.offset(r, r, r))) {
            if (p.distSqr(c) > r * r)
                continue;
            BlockState s = sl.getBlockState(p);
            boolean apagada = false;
            if (s.is(Blocks.TORCH) || s.is(Blocks.WALL_TORCH) || s.is(Blocks.SOUL_TORCH) || s.is(Blocks.SOUL_WALL_TORCH)
                    || s.is(Blocks.LANTERN) || s.is(Blocks.SOUL_LANTERN)) {
                sl.destroyBlock(p, true, this);
                apagada = true;
            } else if ((s.is(BlockTags.CAMPFIRES) || s.is(BlockTags.CANDLES) || s.is(BlockTags.CANDLE_CAKES))
                    && s.hasProperty(BlockStateProperties.LIT) && s.getValue(BlockStateProperties.LIT)) {
                sl.setBlock(p, s.setValue(BlockStateProperties.LIT, false), 11);
                apagada = true;
            }
            if (apagada) {
                this.apagadas++;
                sl.sendParticles(ParticleTypes.LARGE_SMOKE, p.getX() + 0.5, p.getY() + 0.6, p.getZ() + 0.5, 6, 0.15, 0.2, 0.15, 0.01);
                if (n++ < 6)
                    sl.playSound(null, p, SoundEvents.FIRE_EXTINGUISH, SoundSource.HOSTILE, 0.6f, 0.6f + this.random.nextFloat() * 0.3f);
                if (n > 40)
                    break;
            }
        }
    }

    /** Lo que ella apaga (o tira): antorchas, faroles, fogatas y velas. */
    private static boolean apagable(BlockState s) {
        return s.is(Blocks.TORCH) || s.is(Blocks.WALL_TORCH) || s.is(Blocks.SOUL_TORCH) || s.is(Blocks.SOUL_WALL_TORCH)
                || s.is(Blocks.LANTERN) || s.is(Blocks.SOUL_LANTERN) || s.is(BlockTags.CAMPFIRES) || s.is(BlockTags.CANDLES)
                || s.is(BlockTags.CANDLE_CAKES);
    }

    /** La luz fuerte (la que no puede apagar: piedra luminosa, linterna de mar, luz de hongo, ranaluz, calabaza
     * iluminada, faro...) cerca de su cuerpo la obliga a tomar cuerpo y le hace soltar a la presa. */
    private void luz() {
        boolean antes = this.enLuz;
        if (this.tickCount % 5 == 0) {
            BlockPos c = BlockPos.containing(this.getX(), this.getY() + this.getBbHeight() * 0.45, this.getZ());
            boolean hay = false;
            for (BlockPos p : BlockPos.betweenClosed(c.offset(-4, -4, -4), c.offset(4, 4, 4))) {
                if (p.distSqr(c) > RADIO_LUZ * RADIO_LUZ)
                    continue;
                BlockState s = this.level().getBlockState(p);
                if (s.getLightEmission() >= LUZ_FUERTE && !apagable(s)) {
                    hay = true;
                    break;
                }
            }
            this.enLuz = hay;
        }
        if (this.enLuz && !antes && !this.avisoLuz) {
            this.avisoLuz = true;
            for (Player p : this.level().players())
                if (p.distanceToSqr(this) < 48 * 48)
                    p.displayClientMessage(Component.translatable("bruma.mipack.luz"), true);
        }
        if (this.enLuz && this.level() instanceof ServerLevel sl && this.tickCount % 4 == 0)
            sl.sendParticles(ParticleTypes.WHITE_ASH, this.getX(), this.getY() + 3, this.getZ(), 6, 1.0, 2.0, 1.0, 0.0);
    }

    private void quieto(LivingEntity objetivo) {
        flotarEn(this.position(), 0.05);
        if (objetivo != null && objetivo.distanceTo(this) < 40) {
            mirar(objetivo.position());
            if (!this.grito0 && this.ticksEnEstado > 10) {     // al llegar alguien: grita
                this.grito0 = true;
                cambiar(Estado.GRITO);
            } else if (this.ticksEnEstado > 10) {
                cambiar(Estado.ACECHAR);
            }
        }
    }

    private void acechar(LivingEntity objetivo) {
        if (objetivo == null) {
            flotarEn(this.position(), 0.05);
            if (this.ticksEnEstado > 60)
                cambiar(Estado.QUIETO);
            return;
        }
        double d = horizontal(objetivo);
        // se pega a su presa a una distancia de garra, un poco arriba de ella
        Vec3 haciaEl = objetivo.position().subtract(this.position()).multiply(1, 0, 1);
        Vec3 punto = d > 3.5 ? objetivo.position().subtract(haciaEl.normalize().scale(3.5)) : this.position();
        punto = new Vec3(punto.x, objetivo.getY() + 0.3, punto.z);
        double v = (fase2() ? 0.42 : 0.34) * (this.enLuz ? 0.5 : 1.0);
        flotarEn(punto, v);
        mirar(objetivo.position());
        this.atascado = this.horizontalCollision ? this.atascado + 1 : Math.max(0, this.atascado - 1);
        if (this.enfriar > 0)
            return;
        int cerca = (int) enemigos(RADIO_JIRONES).stream().filter(x -> x.distanceToSqr(this) < RADIO_JIRONES * RADIO_JIRONES).count();
        if (cerca >= 2 && this.enfriarJirones <= 0)
            cambiar(Estado.JIRONES);
        else if (this.enfriarGrito <= 0 && d < RADIO_GRITO * 0.8)
            cambiar(Estado.GRITO);
        else if (this.atascado > 30 || (d > 18 && this.enfriarViaje <= 0) || (this.enfriarViaje <= 0 && d > 9 && this.random.nextInt(60) == 0))
            cambiar(Estado.DISOLVERSE);
        else if (d < ALCANCE && Math.abs(objetivo.getY() - this.getY()) < 4.5)
            cambiar(this.enfriarAgarre <= 0 && this.presa == null && this.random.nextInt(3) == 0 ? Estado.AGARRAR : Estado.ZARPAZO);
    }

    private void zarpazo(LivingEntity objetivo) {
        if (objetivo != null && this.ticksEnEstado < GOLPE_ZARPAZO)
            mirar(objetivo.position());
        flotarEn(this.position().add(adelante().scale(this.ticksEnEstado < GOLPE_ZARPAZO ? 0.6 : 0.0)), 0.25);
        if (this.ticksEnEstado == GOLPE_ZARPAZO - 2)
            this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0f, 0.5f);
        if (this.ticksEnEstado == GOLPE_ZARPAZO) {
            for (LivingEntity v : enfrente(ALCANCE + 0.5, 0.2)) {
                if (Golpes.pegar(v, this, DANO_ZARPAZO, 100)) {
                    v.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 0), this);
                    empujar(v, 1.1, 0.35);
                }
            }
        }
        if (this.ticksEnEstado >= T_ZARPAZO)
            terminarAtaque(fase2() ? 10 : 18);
    }

    private void agarrar(LivingEntity objetivo) {
        if (objetivo != null && this.ticksEnEstado < MANO_CIERRA) {
            mirar(objetivo.position());
            flotarEn(objetivo.position().add(0, 0.3, 0).subtract(adelante().scale(2.5)), 0.5);
        } else {
            flotarEn(this.position(), 0.1);
        }
        if (this.ticksEnEstado == MANO_CIERRA) {
            LivingEntity mejor = null;
            for (LivingEntity v : enfrente(ALCANCE + 1.0, 0.0))
                if (!v.isPassenger() && (mejor == null || v.distanceToSqr(this) < mejor.distanceToSqr(this)))
                    mejor = v;
            if (mejor != null && mejor.startRiding(this, true)) {
                this.presa = mejor;
                this.danoEnDrenaje = 0f;
                this.drenados++;
                this.playSound(SoundEvents.SOUL_ESCAPE, 3.0f, 0.5f);
            }
        }
        if (this.ticksEnEstado >= T_AGARRAR) {
            if (this.presa != null)
                cambiar(Estado.DRENAR);
            else
                terminarAtaque(10);
        }
    }

    private void drenar() {
        LivingEntity p = this.presa;
        flotarEn(this.position().add(0, 0.02, 0), 0.05);
        String suelta = p == null || !p.isAlive() || p.isRemoved() || p.getVehicle() != this ? "ya no esta"
                : this.enLuz ? "luz fuerte" : this.ticksEnEstado >= ajustes().drenar() ? "tiempo"
                : this.danoEnDrenaje >= this.getMaxHealth() * ajustes().rescate() ? "rescate" : null;
        if (suelta != null) {
            if (Mipack.PRUEBA)
                Mipack.LOGGER.info("[Bruma] suelta a su presa ({}) despues de {} ticks", suelta, this.ticksEnEstado);
            soltar();
            terminarAtaque(20);
            this.enfriarAgarre = 260;
            return;
        }
        if (this.ticksEnEstado % 10 == 5) {
            float antes = p.getHealth();
            if (p.hurt(Golpes.fuente(p, Golpes.DRENAR, this), DANO_DRENAR * Dificultad.dano(this))) {
                this.heal(DANO_DRENAR * 3f * (fase2() ? 1.5f : 1f));
                if (p instanceof Player j)
                    j.getFoodData().setFoodLevel(Math.max(0, j.getFoodData().getFoodLevel() - 1));
            }
            if (p.getHealth() > antes) {                         // un totem lo salvo: lo suelta
                soltar();
                terminarAtaque(20);
                return;
            }
            this.playSound(SoundEvents.WARDEN_HEARTBEAT, 2.0f, 0.6f);
        }
        if (this.level() instanceof ServerLevel sl && this.tickCount % 2 == 0) {   // el alma sube de la presa a la capucha
            Vec3 a = p.position().add(0, p.getBbHeight() * 0.6, 0), b = cabeza();
            for (int i = 0; i < 4; i++) {
                double u = this.random.nextDouble();
                Vec3 q = a.lerp(b, u);
                Vec3 vel = b.subtract(a).normalize().scale(0.15);
                sl.sendParticles(ParticleTypes.SOUL, q.x, q.y, q.z, 0, vel.x, vel.y, vel.z, 1.0);
            }
        }
    }

    /** Suelta a la presa (la avienta un poco y cae despacio). */
    private void soltar() {
        LivingEntity p = this.presa;
        this.presa = null;
        if (p == null)
            return;
        this.soltando = true;
        p.stopRiding();
        this.soltando = false;
        p.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 60, 0), this);
        empujar(p, 0.6, 0.2);
    }

    private void grito() {
        flotarEn(this.position(), 0.05);
        LivingEntity t = getTarget();
        if (t != null && this.ticksEnEstado < SALE_GRITO)
            mirar(t.position());
        if (this.ticksEnEstado == 4)
            this.playSound(SoundEvents.WARDEN_SONIC_CHARGE, 3.0f, 0.6f);
        if (this.ticksEnEstado == SALE_GRITO && this.level() instanceof ServerLevel sl) {
            double r = fase2() ? RADIO_GRITO_2 : RADIO_GRITO;
            this.playSound(SoundEvents.ELDER_GUARDIAN_CURSE, 4.0f, 0.55f);
            this.playSound(SoundEvents.WARDEN_SONIC_BOOM, 3.0f, 0.7f);
            Vec3 c = cabeza();
            sl.sendParticles(ParticleTypes.SONIC_BOOM, c.x, c.y, c.z, 1, 0, 0, 0, 0);
            for (int i = 0; i < 48; i++) {
                double a = i * Math.PI * 2 / 48;
                sl.sendParticles(ParticleTypes.SCULK_SOUL, c.x + Math.cos(a) * 2, c.y - 1, c.z + Math.sin(a) * 2, 0,
                        Math.cos(a) * 0.6, 0.02, Math.sin(a) * 0.6, 1.0);
            }
            for (LivingEntity v : enemigos(r)) {
                if (v.distanceToSqr(this) > r * r || !this.hasLineOfSight(v))
                    continue;
                v.hurt(this.damageSources().indirectMagic(this, this), DANO_GRITO * Dificultad.dano(this));
                v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 140, 0), this);
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2), this);
                v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 140, 0), this);
                v.setTicksFrozen(Math.max(v.getTicksFrozen(), v.getTicksRequiredToFreeze() + 160));
            }
        }
        if (this.ticksEnEstado >= T_GRITO) {
            this.enfriarGrito = ajustes().gritoCada() + this.random.nextInt(80);
            terminarAtaque(10);
        }
    }

    private void disolverse(LivingEntity objetivo) {
        flotarEn(this.position().add(0, 0.05, 0), 0.1);
        if (this.ticksEnEstado == 2)
            this.playSound(SoundEvents.PHANTOM_SWOOP, 3.0f, 0.5f);
        if (this.ticksEnEstado >= T_DISOLVERSE) {
            // a donde: detras de su objetivo (de espaldas a donde mira), a la altura de su cabeza
            LivingEntity t = objetivo != null ? objetivo : getTarget();
            if (t == null) {
                cambiar(Estado.APARECER);
                return;
            }
            Vec3 mira = Vec3.directionFromRotation(0, t.getYRot());
            this.destino = t.position().subtract(mira.scale(3.0)).add(0, 0.3, 0);
            this.noPhysics = true;
            cambiar(Estado.VIAJAR);
        }
    }

    private void viajar() {
        Vec3 d = this.destino.subtract(this.position());
        double largo = d.length();
        Vec3 v = largo < 1e-3 ? Vec3.ZERO : d.scale(Math.min(1.6, largo) / largo);
        this.setDeltaMovement(v);
        if (this.level() instanceof ServerLevel sl) {
            sl.sendParticles(NEGRA, this.getX(), this.getY() + 2.5, this.getZ(), 6, 0.8, 1.6, 0.8, 0.0);
            sl.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 2.5, this.getZ(), 2, 0.6, 1.2, 0.6, 0.02);
        }
        if (largo < 1.2 || this.ticksEnEstado > MAX_VIAJE) {
            this.noPhysics = false;
            salirDeLoSolido();
            this.setDeltaMovement(Vec3.ZERO);
            LivingEntity t = getTarget();
            if (t != null)
                mirar(t.position());
            cambiar(Estado.APARECER);
        }
    }

    /** Al aparecer no se queda metida en la tierra: sube hasta tener aire. */
    private void salirDeLoSolido() {
        for (int i = 0; i < 12 && !this.level().noCollision(this, this.getBoundingBox()); i++)
            this.setPos(this.getX(), this.getY() + 1.0, this.getZ());
    }

    private void aparecer(LivingEntity objetivo) {
        flotarEn(this.position(), 0.05);
        if (objetivo != null)
            mirar(objetivo.position());
        if (this.ticksEnEstado >= T_APARECER) {
            this.enfriarViaje = 200 + this.random.nextInt(100);
            this.atascado = 0;
            this.enfriar = 0;                                   // y en seguida ataca, si quedo cerca
            cambiar(Estado.ACECHAR);
        }
    }

    private void jirones() {
        flotarEn(this.position(), 0.05);
        if (this.ticksEnEstado == 5)
            this.playSound(SoundEvents.PHANTOM_SWOOP, 3.0f, 0.4f);
        if (this.ticksEnEstado >= 9 && this.ticksEnEstado <= 16)
            for (LivingEntity v : enemigos(RADIO_JIRONES)) {
                if (v.distanceToSqr(this) > RADIO_JIRONES * RADIO_JIRONES || !this.golpeados.add(v.getUUID()))
                    continue;
                if (Golpes.pegar(v, this, DANO_JIRONES, 60)) {
                    v.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 0), this);
                    empujar(v, 1.6, 0.5);
                }
            }
        if (this.ticksEnEstado >= T_JIRONES) {
            this.enfriarJirones = 140 + this.random.nextInt(60);
            terminarAtaque(12);
        }
    }

    private void faseDos() {
        flotarEn(this.position().add(0, this.ticksEnEstado < 20 ? 0.08 : 0.0, 0), 0.1);
        if (this.ticksEnEstado == 18 && this.level() instanceof ServerLevel sl) {
            this.entityData.set(FASE2, true);
            this.playSound(SoundEvents.ELDER_GUARDIAN_CURSE, 4.0f, 0.4f);
            this.playSound(SoundEvents.WITHER_SPAWN, 2.0f, 1.4f);
            sl.sendParticles(NEGRA, this.getX(), this.getY() + 3, this.getZ(), 80, 6, 3, 6, 0.0);
            for (Player p : this.level().players())
                if (p.distanceToSqr(this) < 64 * 64)
                    p.displayClientMessage(Component.translatable("bruma.mipack.fase2"), true);
            this.enfriarAlmas = 0;
        }
        if (this.ticksEnEstado >= T_FASE2) {
            this.enfriarGrito = Math.min(this.enfriarGrito, 60);
            terminarAtaque(10);
        }
    }

    /** Almas en pena: vexes que viven poco y van contra su objetivo (2 mas 1 por jugador, hasta lo que diga la dificultad). */
    private void almasEnPena() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        this.almas.removeIf(u -> sl.getEntity(u) == null);
        int quiere = Math.min(ajustes().almas(), 2 + this.maxJugadores);
        for (int i = this.almas.size(); i < quiere; i++) {
            Vex v = EntityType.VEX.create(sl);
            if (v == null)
                break;
            double a = this.random.nextDouble() * Math.PI * 2;
            v.moveTo(this.getX() + Math.cos(a) * 2.5, this.getY() + 3.0, this.getZ() + Math.sin(a) * 2.5, this.getYRot(), 0f);
            v.finalizeSpawn(sl, sl.getCurrentDifficultyAt(v.blockPosition()), MobSpawnType.MOB_SUMMONED, null, null);
            v.setOwner(this);
            v.setLimitedLife(20 * 30);
            v.setCustomName(Component.translatable("entity.mipack.alma_en_pena"));
            v.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, ItemStack.EMPTY);
            if (getTarget() != null)
                v.setTarget(getTarget());
            sl.addFreshEntity(v);
            this.almas.add(v.getUUID());
            sl.sendParticles(ParticleTypes.SCULK_SOUL, v.getX(), v.getY(), v.getZ(), 10, 0.3, 0.3, 0.3, 0.02);
        }
        this.enfriarAlmas = 500;
    }

    private void terminarAtaque(int enfriar) {
        this.enfriar = enfriar + this.random.nextInt(10);
        this.corporeaHasta = this.tickCount + 40;              // se queda corporea un momento despues de atacar
        escoger(true);
        cambiar(Estado.ACECHAR);
    }

    // ------------------------------------------------------------------ ayudas de movimiento y golpes

    private double horizontal(Entity e) {
        return Math.hypot(e.getX() - this.getX(), e.getZ() - this.getZ());
    }

    /** Vuela hacia un punto (sin gravedad), acelerando suave hasta vmax bloques por tick. */
    private void flotarEn(Vec3 punto, double vmax) {
        Vec3 d = punto.subtract(this.position());
        double largo = d.length();
        Vec3 quiere = largo < 1e-3 ? Vec3.ZERO : d.scale(Math.min(vmax, largo * 0.25) / largo);
        this.setDeltaMovement(this.getDeltaMovement().lerp(quiere, 0.2));
    }

    private void mirar(Vec3 p) {
        double dx = p.x - this.getX(), dz = p.z - this.getZ();
        if (dx * dx + dz * dz < 1e-4)
            return;
        float quiere = (float) (Mth.atan2(dz, dx) * (180.0 / Math.PI)) - 90f;
        float giro = Mth.approachDegrees(this.getYRot(), quiere, 12f);
        this.setYRot(giro);
        this.yBodyRot = giro;
        this.yHeadRot = giro;
    }

    private Vec3 adelante() {
        return Vec3.directionFromRotation(0, this.getYRot());
    }

    /** La capucha en el mundo (de donde salen el grito y a donde sube el alma). */
    private Vec3 cabeza() {
        return PosesKhaset.aMundo(this, this.getYRot(), new Vec3(0, 28, -4), ESCALA);
    }

    /** Lo que esta enfrente, dentro del alcance y del angulo (coseno minimo 'cono'). */
    private List<LivingEntity> enfrente(double alcance, double cono) {
        Vec3 f = adelante();
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity v : enemigos(alcance + 2)) {
            Vec3 d = v.position().subtract(this.position()).multiply(1, 0, 1);
            double l = d.length();
            if (l > alcance || v.getY() > this.getY() + this.getBbHeight() || v.getY() + v.getBbHeight() < this.getY() - 2)
                continue;
            if (l < 1.5 || d.scale(1 / l).dot(f) >= cono)
                out.add(v);
        }
        return out;
    }

    private void empujar(LivingEntity v, double fuerza, double arriba) {
        Vec3 d = v.position().subtract(this.position()).multiply(1, 0, 1);
        d = d.lengthSqr() < 1e-4 ? adelante() : d.normalize();
        v.setDeltaMovement(v.getDeltaMovement().add(d.scale(fuerza)).add(0, arriba, 0));
        v.hurtMarked = true;
    }

    @Override
    public void travel(Vec3 entrada) {
        if (!this.level().isClientSide) {                    // vuela: sin gravedad ni friccion del piso
            this.move(net.minecraft.world.entity.MoverType.SELF, this.getDeltaMovement());
            this.setDeltaMovement(this.getDeltaMovement().scale(0.9));
        }
        this.calculateEntityAnimation(false);
    }

    /** La presa va colgando: nunca la maneja (aunque en las pruebas sea un mob). */
    @Override
    public LivingEntity getControllingPassenger() {
        return null;
    }

    // ------------------------------------------------------------------ la presa en la mano

    @Override
    protected boolean canAddPassenger(Entity pasajero) {
        return this.getPassengers().isEmpty() && pasajero instanceof LivingEntity;
    }

    /** Si la presa se sale del juego, el juego se llevaria a La Bruma guardada con ella (como un caballo): no. */
    @Override
    public boolean hasExactlyOnePlayerPassenger() {
        return false;
    }

    /** La presa va colgando, no sentada. */
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

    /** La presa cuelga de la mano derecha (donde la deja la animacion de drenar). */
    @Override
    protected void positionRider(Entity pasajero, Entity.MoveFunction mover) {
        Vec3 m = PosesKhaset.aMundo(this, this.getYRot(), MANO_DRENAR, ESCALA);
        double vaiven = Math.sin(this.tickCount * 0.3) * 0.08;
        mover.accept(pasajero, m.x, m.y - pasajero.getBbHeight() * 0.95 + vaiven, m.z);
    }

    // ------------------------------------------------------------------ cliente: la bruma alrededor

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide && getEstado() != Estado.MUERTE && !escondida()) {
            int n = fase2() ? 4 : 2;                                 // poquitas y chicas: que no tapen el modelo
            double r = fase2() ? 4.0 : 2.5;
            for (int i = 0; i < n; i++) {
                double a = this.random.nextDouble() * Math.PI * 2, d = r * (0.3 + this.random.nextDouble());
                this.level().addParticle(i % 3 == 0 ? GRIS : NEGRA, this.getX() + Math.cos(a) * d,
                        this.getY() + this.random.nextDouble() * this.getBbHeight() * 0.8, this.getZ() + Math.sin(a) * d,
                        0, -0.01, 0);
            }
            if (!corporea() && this.random.nextInt(4) == 0)
                this.level().addParticle(ParticleTypes.SCULK_SOUL, this.getX() + (this.random.nextDouble() - 0.5) * 2,
                        this.getY() + this.random.nextDouble() * 4, this.getZ() + (this.random.nextDouble() - 0.5) * 2, 0, 0.02, 0);
            if (this.random.nextInt(3) == 0)                       // la niebla que se arrastra abajo
                this.level().addParticle(ParticleTypes.LARGE_SMOKE, this.getX() + (this.random.nextDouble() - 0.5) * r * 2,
                        this.getY() - 0.3, this.getZ() + (this.random.nextDouble() - 0.5) * r * 2, 0, 0.0, 0);
        }
    }

    // ------------------------------------------------------------------ dano, muerte y barra

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        Estado e = getEstado();
        boolean siempre = fuente.is(DamageTypeTags.BYPASSES_INVULNERABILITY);          // /kill
        if (!siempre && (e == Estado.VIAJAR || e == Estado.FASE2 || esAlma(fuente.getEntity()) || fuente.getEntity() == this))
            return false;
        boolean fuego = fuente.is(DamageTypeTags.IS_FIRE);
        if (fuego)
            this.corporeaHasta = this.tickCount + 100;          // el fuego la obliga a tomar cuerpo
        else if (!corporea() && !siempre)
            cantidad *= ajustes().niebla();
        boolean pego = super.hurt(fuente, cantidad);
        if (pego && !this.level().isClientSide) {
            this.amenaza.golpe(fuente.getEntity(), cantidad);
            if (e == Estado.DRENAR && fuente.getEntity() != this.presa)
                this.danoEnDrenaje += cantidad;
        }
        return pego;
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (!this.level().isClientSide) {
            soltar();
            this.noPhysics = false;
            cambiar(Estado.MUERTE);
            if (this.level() instanceof ServerLevel sl)
                for (UUID u : this.almas)
                    if (sl.getEntity(u) instanceof Vex v) {
                        sl.sendParticles(ParticleTypes.SCULK_SOUL, v.getX(), v.getY(), v.getZ(), 8, 0.3, 0.3, 0.3, 0.02);
                        v.discard();
                    }
            this.almas.clear();
            this.playSound(SoundEvents.ELDER_GUARDIAN_DEATH, 4.0f, 0.5f);
        }
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource fuente, int saqueo, boolean golpeReciente) {
        super.dropCustomDeathLoot(fuente, saqueo, golpeReciente);
        this.spawnAtLocation(new ItemStack(Items.ECHO_SHARD, 2 + this.random.nextInt(2)));
        this.spawnAtLocation(new ItemStack(Items.PHANTOM_MEMBRANE, 4 + this.random.nextInt(4)));
    }

    @Override
    protected void tickDeath() {
        this.deathTime++;
        this.setDeltaMovement(this.getDeltaMovement().scale(0.5).add(0, -0.01, 0));
        if (this.level() instanceof ServerLevel sl && this.deathTime % 3 == 0)
            sl.sendParticles(NEGRA, this.getX(), this.getY() + 2, this.getZ(), 10, 2.0, 2.0, 2.0, 0.0);
        if (this.deathTime >= T_MUERTE && !this.level().isClientSide()) {
            if (this.level() instanceof ServerLevel sl) {
                sl.sendParticles(NEGRA, this.getX(), this.getY() + 2, this.getZ(), 60, 3.0, 2.5, 3.0, 0.0);
                sl.sendParticles(ParticleTypes.SCULK_SOUL, this.getX(), this.getY() + 2, this.getZ(), 40, 2.0, 2.0, 2.0, 0.05);
            }
            this.level().broadcastEntityEvent(this, (byte) 60);
            this.remove(Entity.RemovalReason.KILLED);
        }
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.SOUL_ESCAPE;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 120;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource fuente) {
        return SoundEvents.PHANTOM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PHANTOM_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 0.45f + this.random.nextFloat() * 0.1f;
    }

    @Override
    protected float getSoundVolume() {
        return 3.0f;
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
        if (razon.shouldDestroy())
            soltar();
        super.remove(razon);
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return this.getBoundingBox().inflate(4.0, 1.5, 4.0);             // los brazos y las tiras salen de la caja
    }

    @Override
    public boolean causeFallDamage(float distancia, float multiplicador, DamageSource fuente) {
        return false;
    }

    @Override
    protected void checkFallDamage(double y, boolean enPiso, BlockState estado, BlockPos pos) {
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
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public boolean canBreatheUnderwater() {
        return true;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("Fase2", fase2());
        tag.putBoolean("Grito", this.grito0);
        tag.putInt("Jugadores", this.maxJugadores);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.entityData.set(FASE2, tag.getBoolean("Fase2"));
        this.grito0 = tag.getBoolean("Grito");
        this.maxJugadores = tag.getInt("Jugadores");
        if (this.hasCustomName())
            this.barra.setName(this.getDisplayName());
    }

    // ------------------------------------------------------------------ animaciones (GeckoLib)

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
        controladores.add(new AnimationController<>(this, "principal", 4, this::animar));
    }

    private PlayState animar(AnimationState<BrumaEntity> estado) {
        RawAnimation a = switch (getEstado()) {
            case QUIETO, ACECHAR -> estado.isMoving() || this.getDeltaMovement().horizontalDistanceSqr() > 0.004 ? A_AVANZAR : A_FLOTAR;
            case ZARPAZO -> A_ZARPAZO;
            case AGARRAR, DRENAR -> A_AGARRAR;
            case GRITO -> A_GRITO;
            case DISOLVERSE, VIAJAR -> A_DISOLVERSE;
            case APARECER -> A_APARECER;
            case JIRONES -> A_JIRONES;
            case FASE2 -> A_FASE2;
            case MUERTE -> A_MUERTE;
        };
        return estado.setAndContinue(a);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
