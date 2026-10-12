package com.mipack.titanes;

import com.mipack.Mipack;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
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
import java.util.List;

/**
 * Un titan: una criatura enorme que no le pide permiso al mundo. No pelea ni se le hace dano: vive su agenda (camina,
 * come, bebe, descansa, se queda mirando a quien se le acerca) siguiendo las rutas del motor (Rutas sobre el mapa del
 * Terreno). Se mueve sin chocar con los bloques (pasa entre los arboles como si nada) pero sigue el piso (o el agua, o
 * las copas, o vuela por encima) para no quedar enterrado ni flotando. Lo maneja TitanesMundo: aparece cuando hay
 * jugadores cerca y, si no, sigue su camino de forma virtual (no se guarda con el chunk).
 */
public class Titan extends Mob implements GeoEntity {
    public enum Estado { QUIETO, MOVER, ASENTARSE, DESCANSAR, LEVANTARSE, COMER, BEBER, MIRAR, ESPECIAL }

    private static final EntityDataAccessor<Integer> ESTADO = SynchedEntityData.defineId(Titan.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> INICIO = SynchedEntityData.defineId(Titan.class, EntityDataSerializers.INT);

    public final TipoTitan tipo;
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private int ticksEnEstado;
    private TipoTitan.Actividad actividad;
    private List<Vec3> camino = new ArrayList<>();
    private int indice;
    private Vec3 casa;
    private int idMundo = -1;
    private Vec3 marca;
    private int sinAvanzar, revisar, enfriarMirar;
    private Player mirando;
    private final RawAnimation[] anims = new RawAnimation[Estado.values().length];

    public Titan(EntityType<? extends Titan> tipoEntidad, Level nivel, TipoTitan tipo) {
        super(tipoEntidad, nivel);
        this.tipo = tipo;
        this.noPhysics = true;
        this.setNoGravity(true);
        this.setPersistenceRequired();
        this.setInvulnerable(true);
        String base = "animation." + tipo.id() + ".";
        for (Estado e : Estado.values())
            this.anims[e.ordinal()] = switch (e) {
                case QUIETO, MIRAR -> RawAnimation.begin().thenLoop(base + "quieto");
                case MOVER -> RawAnimation.begin().thenLoop(base + "mover");
                case ASENTARSE -> RawAnimation.begin().thenPlayAndHold(base + "asentarse");
                case DESCANSAR -> RawAnimation.begin().thenLoop(base + "descansar");
                case LEVANTARSE -> RawAnimation.begin().thenPlay(base + "levantarse");
                case COMER -> RawAnimation.begin().thenLoop(base + "comer");
                case BEBER -> RawAnimation.begin().thenLoop(base + "beber");
                case ESPECIAL -> RawAnimation.begin().thenPlay(base + "especial");
            };
    }

    public static AttributeSupplier.Builder atributos() {
        return Mob.createMobAttributes().add(Attributes.MAX_HEALTH, 1000.0).add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.MOVEMENT_SPEED, 0.2);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ESTADO, 0);
        this.entityData.define(INICIO, 0);
    }

    public Estado getEstado() {
        return Estado.values()[this.entityData.get(ESTADO)];
    }

    public int inicioEstado() {
        return this.entityData.get(INICIO);
    }

    private void cambiar(Estado e) {
        this.entityData.set(ESTADO, e.ordinal());
        this.entityData.set(INICIO, (int) this.level().getGameTime());
        this.ticksEnEstado = 0;
    }

    /** Lo pone TitanesMundo al crearlo: su numero en el registro, su casa y el camino que llevaba. */
    public void ligar(int id, Vec3 casa, List<Vec3> camino, int indice, TipoTitan.Actividad act) {
        this.idMundo = id;
        this.casa = casa;
        this.camino = new ArrayList<>(camino);
        this.indice = indice;
        this.actividad = act;
        if (!this.camino.isEmpty() && this.indice < this.camino.size())
            cambiar(Estado.MOVER);
    }

    public int idMundo() {
        return this.idMundo;
    }

    public List<Vec3> camino() {
        return this.camino;
    }

    public int indice() {
        return this.indice;
    }

    public TipoTitan.Actividad actividad() {
        return this.actividad;
    }

    /** Para probar o con /titanes mandar: que vaya a un punto. */
    public boolean mandar(Vec3 destino) {
        this.actividad = new TipoTitan.Actividad(destino, TipoTitan.Hacer.QUIETO, 100);
        return planear();
    }

    // ------------------------------------------------------------------ el cerebro (servidor)

    @Override
    public void tick() {
        super.tick();
        this.setDeltaMovement(Vec3.ZERO);
        if (!this.level().isClientSide)
            cerebro();
    }

    private void cerebro() {
        this.ticksEnEstado++;
        if (this.casa == null)
            this.casa = this.position();
        if (this.enfriarMirar > 0)
            this.enfriarMirar--;
        switch (getEstado()) {
            case QUIETO -> {
                if (this.ticksEnEstado > (this.actividad == null ? 40 : 10))
                    siguiente();
                curiosidad();
            }
            case MOVER -> {
                seguir();
                curiosidad();
            }
            case ASENTARSE -> {
                if (this.ticksEnEstado >= 60)
                    cambiar(Estado.DESCANSAR);
            }
            case DESCANSAR -> {
                if (this.ticksEnEstado >= duracion())
                    cambiar(Estado.LEVANTARSE);
            }
            case LEVANTARSE -> {
                if (this.ticksEnEstado >= 50)
                    terminar();
            }
            case COMER, BEBER, ESPECIAL -> {
                if (this.ticksEnEstado >= duracion())
                    terminar();
            }
            case MIRAR -> {
                if (this.mirando != null && this.mirando.isAlive())
                    girarHacia(this.mirando.position(), this.tipo.giro() * 0.5f);
                if (this.ticksEnEstado >= 120 || this.mirando == null || this.mirando.distanceTo(this) > curiosidadRadio() * 1.5) {
                    this.enfriarMirar = 600;
                    cambiar(this.camino.isEmpty() || this.indice >= this.camino.size() ? Estado.QUIETO : Estado.MOVER);
                }
            }
        }
        // sigue el piso aunque este quieto (por si el terreno cambia debajo)
        double y = alturaObjetivo(this.getX(), this.getZ());
        if (getEstado() != Estado.MOVER && Math.abs(y - this.getY()) > 0.05)
            this.setPos(this.getX(), Mth.lerp(0.15, this.getY(), y), this.getZ());
    }

    private int duracion() {
        return this.actividad == null ? 200 : Math.max(40, this.actividad.ticks());
    }

    private void terminar() {
        this.actividad = null;
        cambiar(Estado.QUIETO);
    }

    /** Escoge lo que sigue de la agenda y busca el camino. */
    private void siguiente() {
        if (!(this.level() instanceof ServerLevel sl))
            return;
        if (this.actividad == null)
            this.actividad = this.tipo.agenda().siguiente(Terreno.de(sl), this.tipo, this.position(), this.casa,
                    sl.getDayTime() % 24000, this.random);
        if (this.actividad == null)
            return;
        if (this.actividad.lugar() == null || this.actividad.lugar().distanceToSqr(this.getX(), this.actividad.lugar().y, this.getZ()) < 16) {
            hacer();
            return;
        }
        if (!planear())
            this.actividad = null;                                // no hay camino: otra cosa la proxima vez
    }

    private boolean planear() {
        if (!(this.level() instanceof ServerLevel sl) || this.actividad == null || this.actividad.lugar() == null)
            return false;
        List<Vec3> c = Rutas.buscar(Terreno.de(sl), this.tipo.perfil(), this.position(), this.actividad.lugar(), 40000);
        if (c.isEmpty()) {
            if (Mipack.PRUEBA)
                Mipack.LOGGER.info("[Titan {}] sin camino a {}", this.tipo.id(), this.actividad.lugar());
            return false;
        }
        this.camino = new ArrayList<>(c);
        this.indice = Math.min(1, this.camino.size() - 1);
        this.marca = this.position();
        this.sinAvanzar = 0;
        if (Mipack.PRUEBA)
            Mipack.LOGGER.info("[Titan {}] camino de {} puntos a {}", this.tipo.id(), this.camino.size(), this.actividad.lugar());
        cambiar(Estado.MOVER);
        return true;
    }

    private void hacer() {
        TipoTitan.Hacer h = this.actividad == null ? TipoTitan.Hacer.QUIETO : this.actividad.hacer();
        this.camino.clear();
        switch (h) {
            case COMER -> cambiar(Estado.COMER);
            case BEBER -> cambiar(Estado.BEBER);
            case DESCANSAR -> cambiar(Estado.ASENTARSE);
            case ESPECIAL -> cambiar(Estado.ESPECIAL);
            default -> {
                this.actividad = this.actividad == null ? null : new TipoTitan.Actividad(null, TipoTitan.Hacer.QUIETO, 0);
                this.actividad = null;
                cambiar(Estado.QUIETO);
            }
        }
    }

    /** Camina hacia el siguiente punto del camino girando de a poco; si no avanza o algo cambio, vuelve a buscar. */
    private void seguir() {
        if (this.indice >= this.camino.size()) {
            hacer();
            return;
        }
        Vec3 w = this.camino.get(this.indice);
        Vec3 d = new Vec3(w.x - this.getX(), 0, w.z - this.getZ());
        double dist = d.length();
        double llegar = Math.max(3.0, this.tipo.ancho() * 0.4);
        if (dist < llegar) {
            this.indice++;
            return;
        }
        float deseado = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
        float falta = Mth.wrapDegrees(deseado - this.getYRot());
        fijarGiro(this.getYRot() + Mth.clamp(falta, -this.tipo.giro(), this.tipo.giro()));
        double v = this.tipo.velocidad() * Mth.clamp(1.0 - Math.abs(falta) / 100.0, 0.15, 1.0);
        Vec3 f = Vec3.directionFromRotation(0, this.getYRot());
        double nx = this.getX() + f.x * v, nz = this.getZ() + f.z * v;
        double y = alturaObjetivo(nx, nz);
        this.setPos(nx, Mth.lerp(0.25, this.getY(), y), nz);
        // atorado: casi no avanza en 5 s
        if (++this.revisar >= 100) {
            this.revisar = 0;
            if (this.marca != null && this.marca.distanceTo(this.position()) < this.tipo.velocidad() * 100 * 0.2) {
                if (++this.sinAvanzar >= 2) {
                    if (Mipack.PRUEBA)
                        Mipack.LOGGER.info("[Titan {}] atorado en {}: busca otra vez", this.tipo.id(), this.blockPosition());
                    this.sinAvanzar = 0;
                    if (!planear())
                        terminar();
                }
            } else {
                this.sinAvanzar = 0;
            }
            this.marca = this.position();
            if (this.random.nextInt(4) == 0 && !caminoSigueSirviendo())
                planear();
        }
    }

    /** Las celdas que se conocieron despues de planear siguen sirviendo para lo que falta del camino. */
    private boolean caminoSigueSirviendo() {
        if (!(this.level() instanceof ServerLevel sl))
            return true;
        Terreno t = Terreno.de(sl);
        Vec3 a = this.position();
        for (int i = this.indice; i < Math.min(this.camino.size(), this.indice + 3); i++) {
            Vec3 b = this.camino.get(i);
            int pasos = (int) Math.ceil(a.distanceTo(b) / 4.0);
            for (int k = 1; k <= pasos; k++) {
                Vec3 q = a.lerp(b, k / (double) pasos);
                Terreno.Celda c = t.celda(Terreno.celdaDe(q.x), Terreno.celdaDe(q.z));
                if (c != null && !Rutas.sirve(this.tipo.perfil(), c))
                    return false;
            }
            a = b;
        }
        return true;
    }

    /** Si un jugador se acerca, a veces se para a mirarlo (curiosidad de gigante: luego sigue con lo suyo). */
    private void curiosidad() {
        if (this.enfriarMirar > 0 || this.tickCount % 20 != 0)
            return;
        Player p = this.level().getNearestPlayer(this, curiosidadRadio());
        if (p != null && !p.isSpectator() && this.random.nextInt(4) == 0) {
            this.mirando = p;
            cambiar(Estado.MIRAR);
        }
    }

    private double curiosidadRadio() {
        return Math.max(16.0, this.tipo.alto() * 1.5);
    }

    /** La altura a la que va su origen segun como se mueve: piso (o fondo al vadear), copas, agua o vuelo. */
    public double alturaObjetivo(double x, double z) {
        Rutas.Modo modo = this.tipo.perfil().modo();
        double r = this.tipo.ancho() * 0.35;
        double[][] puntos = {{0, 0}, {r, 0}, {-r, 0}, {0, r}, {0, -r}};
        double alto = -1e9, suma = 0;
        int n = 0;
        for (double[] q : puntos) {
            double h = altura(modo, x + q[0], z + q[1]);
            alto = Math.max(alto, h);
            suma += h;
            n++;
        }
        double base = modo == Rutas.Modo.AIRE ? alto : 0.6 * alto + 0.4 * (suma / n);
        return base + this.tipo.altitud();
    }

    private double altura(Rutas.Modo modo, double x, double z) {
        BlockPos b = BlockPos.containing(x, 0, z);
        if (this.level().hasChunkAt(b)) {
            return switch (modo) {
                case TIERRA -> this.level().getHeight(Heightmap.Types.OCEAN_FLOOR, b.getX(), b.getZ());
                case COPAS, AIRE -> this.level().getHeight(Heightmap.Types.MOTION_BLOCKING, b.getX(), b.getZ());
                case AGUA -> this.level().getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, b.getX(), b.getZ());
                case ARENA -> this.level().getHeight(Heightmap.Types.OCEAN_FLOOR, b.getX(), b.getZ());
            };
        }
        if (this.level() instanceof ServerLevel sl) {
            Terreno.Celda c = Terreno.de(sl).celda(Terreno.celdaDe(x), Terreno.celdaDe(z));
            if (c != null)
                return switch (modo) {
                    case TIERRA, ARENA -> c.fondo();
                    case COPAS, AIRE -> c.copas();
                    case AGUA -> c.suelo();
                };
        }
        return this.getY() - this.tipo.altitud();
    }

    private void girarHacia(Vec3 p, float max) {
        Vec3 d = p.subtract(this.position());
        if (d.horizontalDistanceSqr() < 1e-4)
            return;
        float deseado = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
        fijarGiro(this.getYRot() + Mth.clamp(Mth.wrapDegrees(deseado - this.getYRot()), -max, max));
    }

    private void fijarGiro(float yaw) {
        this.setYRot(yaw);
        this.yBodyRot = yaw;
        this.yHeadRot = yaw;
    }

    // ------------------------------------------------------------------ no pelea, no se guarda con el chunk

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (fuente.is(DamageTypes.FELL_OUT_OF_WORLD) || fuente.is(DamageTypes.GENERIC_KILL))
            return super.hurt(fuente, cantidad);
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void doPush(net.minecraft.world.entity.Entity e) {
    }

    @Override
    public boolean removeWhenFarAway(double d) {
        return false;
    }

    @Override
    public boolean shouldBeSaved() {
        return false;
    }

    @Override
    public boolean causeFallDamage(float distancia, float multiplicador, DamageSource fuente) {
        return false;
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return this.getBoundingBox().inflate(this.tipo.ancho() * 1.5, this.tipo.alto() * 0.5, this.tipo.ancho() * 1.5);
    }

    @Override
    public boolean shouldRenderAtSqrDistance(double d) {
        double lejos = 256 + this.tipo.alto() * 8;
        return d < lejos * lejos;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("IdMundo", this.idMundo);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.idMundo = tag.getInt("IdMundo");
    }

    // ------------------------------------------------------------------ animaciones

    private int inicioVisto = Integer.MIN_VALUE;

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controladores) {
        controladores.add(new AnimationController<>(this, "principal", 10, this::animar)
                .setAnimationSpeedHandler(t -> t.velocidadDeAnimacion()));
    }

    private double velocidadDeAnimacion() {
        if (getEstado() != Estado.MOVER || this.tipo.paso() <= 0)
            return 1.0;
        double v = Math.hypot(this.getX() - this.xo, this.getZ() - this.zo) * 20.0;
        return Mth.clamp(v / this.tipo.paso(), 0.3, 2.5);
    }

    private PlayState animar(AnimationState<Titan> estado) {
        if (this.inicioVisto != inicioEstado()) {
            if (this.inicioVisto != Integer.MIN_VALUE && getEstado() == Estado.ESPECIAL)
                estado.getController().forceAnimationReset();
            this.inicioVisto = inicioEstado();
        }
        Estado e = getEstado();
        if (e == Estado.MOVER && Math.hypot(this.getX() - this.xo, this.getZ() - this.zo) < 1e-3)
            e = Estado.QUIETO;
        return estado.setAndContinue(this.anims[e.ordinal()]);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
