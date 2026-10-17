package com.mipack.bichos;

import com.mipack.bichos.BichosDatos.Conducta;
import com.mipack.bichos.BichosDatos.Especie;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.SmallFireball;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.List;

/**
 * Un bicho de Velkia (los 36 son esta clase con los datos de su especie, BichosDatos). Camina, corre, ataca y hace sus
 * animaciones de ambiente (pastar, beber, acicalarse...) cuando esta tranquilo. Segun su conducta huye, se defiende con
 * su manada o caza. Las aves (y el murcielago) vuelan: se espantan, alzan el vuelo y despues bajan a caminar.
 * <p>
 * MANCHADO DE MURA: cualquier bicho se mancha si le das mura (clic derecho con el material) o si lo muerde uno manchado.
 * Manchado se ve oscuro con venas que brillan y caza a los jugadores, sea cual sea su conducta (el cervatillo no).
 * <p>
 * Lo propio de cada uno (por su id): el cervatillo no recibe dano, sigue a quien lleva hojas y hace crecer cultivos; el
 * pato y la marmota avisan si hay hostiles; el escorpion alenta; el murcielago marchita; la garrapata da hambre; la
 * serpiente envenena; el lobo de fuego quema; el cocodrilo jala; el halcon te tira lo que traes en la mano; el babuino
 * roba comida; la salamandra escupe brasas; el escarabajo de brasa revienta al morir; la lagartija de roca suelta la
 * cola; la lagartija blanca no se ve quieta; la ramita no se mueve hasta que pasas cerca; el hipopotamo ataca en el
 * agua; la cria de Moruvahn se cura en el agua; el fenec recoge cosas del piso; el dromedario se monta y corre en la
 * arena; el buitre vuela en circulos sobre quien tiene poca vida.
 */
public class Bicho extends PathfinderMob implements GeoEntity {
    private static final EntityDataAccessor<Boolean> MANCHADO = SynchedEntityData.defineId(Bicho.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Boolean> VOLANDO = SynchedEntityData.defineId(Bicho.class, EntityDataSerializers.BOOLEAN);
    private static final EntityDataAccessor<Integer> AMBIENTE = SynchedEntityData.defineId(Bicho.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Boolean> CORRIENDO = SynchedEntityData.defineId(Bicho.class, EntityDataSerializers.BOOLEAN);

    public final Especie especie;
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final RawAnimation caminar, correr, atacar;
    private final RawAnimation[] ambientes;
    private int ambienteHasta, vueloTicks, enfriarGolpe, enfriarEscupir, cuandoSemilla, avisoTicks;
    private Vec3 destino;
    private boolean colaSuelta, despierta;

    public Bicho(EntityType<? extends Bicho> tipo, Level nivel, Especie e) {
        super(tipo, nivel);
        this.especie = e;
        String base = "animation." + e.id() + ".";
        this.caminar = RawAnimation.begin().thenLoop(base + "caminar");
        this.correr = RawAnimation.begin().thenLoop(base + (e.correr() ? "correr" : "caminar"));
        this.atacar = RawAnimation.begin().thenPlay(base + "atacar");
        this.ambientes = new RawAnimation[e.ambientes().length];
        for (int i = 0; i < this.ambientes.length; i++)
            this.ambientes[i] = RawAnimation.begin().thenLoop(base + e.ambientes()[i]);
        this.cuandoSemilla = 2400 + this.random.nextInt(3600);
        this.xpReward = e.conducta() == Conducta.HOSTIL ? 5 : 2;
        if (id("fenec"))
            this.setCanPickUpLoot(true);
        metas();
    }

    public static AttributeSupplier.Builder atributos(Especie e) {
        double v = e.vuela() ? 0.22 : e.ancho() > 1.1 ? 0.24 : 0.27;
        return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, e.vida()).add(Attributes.ATTACK_DAMAGE, e.dano())
                .add(Attributes.MOVEMENT_SPEED, v).add(Attributes.FOLLOW_RANGE, 24).add(Attributes.FLYING_SPEED, 0.4)
                .add(Attributes.ATTACK_KNOCKBACK, e.ancho() > 1.0 ? 1.0 : 0.2);
    }

    private boolean id(String s) {
        return this.especie != null && this.especie.id().equals(s);
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(MANCHADO, false);
        this.entityData.define(VOLANDO, false);
        this.entityData.define(AMBIENTE, -1);
        this.entityData.define(CORRIENDO, false);
    }

    public boolean manchado() {
        return this.entityData.get(MANCHADO);
    }

    public boolean volando() {
        return this.entityData.get(VOLANDO);
    }

    public void manchar() {
        if (manchado() || id("cervatillo_musgo"))
            return;
        this.entityData.set(MANCHADO, true);
        this.playSound(SoundEvents.ZOMBIE_VILLAGER_CONVERTED, 0.8f, 0.6f);
        if (this.level() instanceof ServerLevel sl)
            sl.sendParticles(ParticleTypes.SQUID_INK, this.getX(), this.getY() + this.getBbHeight() / 2, this.getZ(), 20,
                    this.getBbWidth() / 2, this.getBbHeight() / 2, this.getBbWidth() / 2, 0.02);
        metas();
    }

    /** Pasivo: huye. Neutral: se defiende con su manada. Hostil (o manchado): caza jugadores. */
    private boolean caza() {
        return manchado() || this.especie.conducta() == Conducta.HOSTIL;
    }

    @Override
    protected void registerGoals() {
        // las metas dependen de la especie (que aun no esta aqui): se ponen en metas()
    }

    private void metas() {
        if (this.especie == null || this.level().isClientSide)
            return;
        this.goalSelector.removeAllGoals(g -> true);
        this.targetSelector.removeAllGoals(g -> true);
        Conducta c = this.especie.conducta();
        this.goalSelector.addGoal(0, new FloatGoal(this));
        if (c == Conducta.SAGRADO) {
            this.goalSelector.addGoal(2, new TemptGoal(this, 1.0, Ingredient.of(ItemTags.LEAVES), false));
        } else if (c == Conducta.PASIVO && !manchado()) {
            this.goalSelector.addGoal(1, new PanicGoal(this, id("liebre_dorada") ? 2.0 : 1.6));
            if (id("fenec") || id("flamenco") || id("lagarto_roca") || id("lagartija_blanca") || id("liebre_dorada"))
                this.goalSelector.addGoal(2, new AvoidEntityGoal<>(this, Player.class, 8f, 1.2, 1.6,
                        p -> !(id("flamenco") && p.isShiftKeyDown())));
        }
        if (c != Conducta.SAGRADO && (c != Conducta.PASIVO || manchado())) {
            this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.25, true));
            this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
            if (caza())
                this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
                        p -> !id("ramita") || p.distanceTo(this) < 5));
        }
        this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8f));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    // ------------------------------------------------------------------ cada tick

    @Override
    public void aiStep() {
        super.aiStep();
        if (this.level().isClientSide) {
            if (manchado() && this.random.nextInt(8) == 0)
                this.level().addParticle(ParticleTypes.SQUID_INK, this.getRandomX(0.6), this.getRandomY(), this.getRandomZ(0.6), 0, 0.01, 0);
            return;
        }
        if (this.enfriarGolpe > 0)
            this.enfriarGolpe--;
        this.entityData.set(CORRIENDO, this.getTarget() != null || this.getDeltaMovement().horizontalDistanceSqr() > 0.012);
        ambiente();
        if (this.especie.vuela())
            vuelo();
        propio();
    }

    /** Las animaciones de ambiente: tranquilo y quieto, de vez en cuando hace una (pastar, beber, sentarse...). */
    private void ambiente() {
        int a = this.entityData.get(AMBIENTE);
        boolean tranquilo = this.getTarget() == null && !volando() && this.onGround() && this.getNavigation().isDone();
        if (a >= 0 && (!tranquilo || this.tickCount > this.ambienteHasta))
            this.entityData.set(AMBIENTE, -1);
        else if (a < 0 && tranquilo && this.ambientes.length > 0 && this.random.nextInt(260) == 0) {
            int i = this.random.nextInt(this.ambientes.length);
            this.entityData.set(AMBIENTE, i);
            int largo = Math.max(40, this.especie.largos()[i]);
            this.ambienteHasta = this.tickCount + largo * (1 + this.random.nextInt(3));
        }
        if (this.entityData.get(AMBIENTE) >= 0)
            this.getNavigation().stop();
    }

    /** Volar: se espanta y alza el vuelo, da vueltas un rato y baja a caminar. Los que cazan vuelan hacia su presa. */
    private void vuelo() {
        LivingEntity t = this.getTarget();
        Player cerca = this.level().getNearestPlayer(this, id("flamenco") ? 10 : 6);
        boolean susto = cerca != null && !cerca.isCreative() && !cerca.isSpectator()
                && (id("flamenco") ? cerca.isSprinting() : !cerca.isShiftKeyDown());
        if (id("ibis"))
            susto |= !this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(8), x -> x instanceof Enemy).isEmpty();
        Player debil = null;
        if (id("buitre"))
            for (Player p : this.level().players())
                if (p.distanceTo(this) < 32 && p.getHealth() < 8 && !p.isCreative())
                    debil = p;
        boolean quiere = id("murcielago_mura") || t != null || (susto && this.especie.conducta() != Conducta.HOSTIL) || debil != null
                || (id("cuervo_negro") && cerca != null);
        if (!volando()) {
            if (quiere && (t == null || t.distanceTo(this) > 2.5)) {
                this.entityData.set(VOLANDO, true);
                this.vueloTicks = 0;
                this.setNoGravity(true);
                this.goalSelector.disableControlFlag(Goal.Flag.MOVE);
                this.goalSelector.disableControlFlag(Goal.Flag.JUMP);
                Vec3 lejos = cerca != null ? this.position().subtract(cerca.position()).multiply(1, 0, 1).normalize() : Vec3.ZERO;
                this.destino = this.position().add(lejos.scale(10)).add(0, 6 + this.random.nextInt(5), 0);
                this.playSound(SoundEvents.PARROT_FLY, 0.8f, 0.8f);
            }
            return;
        }
        this.vueloTicks++;
        this.getNavigation().stop();
        if (t != null && t.isAlive()) {
            this.destino = t.position().add(0, t.getBbHeight() * 0.6, 0);
            if (this.distanceTo(t) < 1.8 + this.getBbWidth() && this.enfriarGolpe == 0)
                this.doHurtTarget(t);
        } else if (debil != null) {
            double a = this.tickCount * 0.05;
            this.destino = debil.position().add(Math.cos(a) * 6, 8, Math.sin(a) * 6);
        } else if (id("cuervo_negro") && cerca != null) {
            this.destino = cerca.position().add(Math.cos(this.tickCount * 0.04) * 4, 4, Math.sin(this.tickCount * 0.04) * 4);
        } else if (this.vueloTicks > 140 && !id("murcielago_mura")) {
            BlockPos piso = this.level().getHeightmapPos(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, this.blockPosition());
            this.destino = new Vec3(this.getX(), piso.getY(), this.getZ());
            if (this.onGround() || this.getY() - piso.getY() < 0.3) {     // ya bajo: a caminar
                this.entityData.set(VOLANDO, false);
                this.setNoGravity(false);
                this.goalSelector.enableControlFlag(Goal.Flag.MOVE);
                this.goalSelector.enableControlFlag(Goal.Flag.JUMP);
                return;
            }
        } else if (this.destino == null || this.destino.distanceToSqr(this.position()) < 2) {
            this.destino = this.position().add(this.random.nextGaussian() * 8, this.random.nextGaussian() * 2, this.random.nextGaussian() * 8);
        }
        Vec3 d = this.destino.subtract(this.position());
        double v = this.getAttributeValue(Attributes.FLYING_SPEED);
        Vec3 quiere2 = d.lengthSqr() > 1e-4 ? d.normalize().scale(Math.min(v, d.length() * 0.3)) : Vec3.ZERO;
        this.setDeltaMovement(this.getDeltaMovement().scale(0.7).add(quiere2.scale(0.3)));
        if (d.horizontalDistanceSqr() > 0.01) {
            float giro = (float) (Math.toDegrees(Math.atan2(d.z, d.x)) - 90.0);
            this.setYRot(giro);
            this.yBodyRot = giro;
            this.yHeadRot = giro;
        }
    }

    @Override
    public void travel(Vec3 v) {
        if (volando() && !this.level().isClientSide) {
            this.move(net.minecraft.world.entity.MoverType.SELF, this.getDeltaMovement());
            return;
        }
        super.travel(v);
    }

    /** Lo de cada especie que pasa solo (no al pegar). */
    private void propio() {
        String i = this.especie.id();
        switch (i) {
            case "cervatillo_musgo" -> {                       // deja semillas y hace crecer cultivos
                if (--this.cuandoSemilla <= 0) {
                    this.spawnAtLocation(new ItemStack(ObjetosMipack.SEMILLA_MUSGO.get()));
                    this.cuandoSemilla = 2400 + this.random.nextInt(3600);
                }
                if (this.tickCount % 200 == 0 && this.level() instanceof ServerLevel sl) {
                    BlockPos p = this.blockPosition().offset(this.random.nextInt(9) - 4, this.random.nextInt(3) - 1, this.random.nextInt(9) - 4);
                    BlockState s = sl.getBlockState(p);
                    if (s.getBlock() instanceof CropBlock c && c.isValidBonemealTarget(sl, p, s, false)) {
                        c.performBonemeal(sl, this.random, p, s);
                        sl.sendParticles(ParticleTypes.HAPPY_VILLAGER, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 6, 0.3, 0.3, 0.3, 0);
                    }
                }
            }
            case "pato_estanque", "marmota" -> {               // avisan si hay hostiles; el pato pone huevos
                if (i.equals("pato_estanque") && --this.cuandoSemilla <= 0) {
                    this.spawnAtLocation(new ItemStack(Items.EGG));
                    this.cuandoSemilla = 6000 + this.random.nextInt(6000);
                }
                if (++this.avisoTicks >= 100) {
                    this.avisoTicks = 0;
                    if (!this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(16), x -> x instanceof Enemy).isEmpty())
                        this.playSound(i.equals("marmota") ? SoundEvents.RABBIT_ATTACK : SoundEvents.CHICKEN_HURT, 1.5f, i.equals("marmota") ? 2.0f : 0.6f);
                }
            }
            case "salamandra_ceniza" -> {                      // escupe brasas
                LivingEntity t = this.getTarget();
                if (t != null && --this.enfriarEscupir <= 0 && this.distanceTo(t) > 3 && this.distanceTo(t) < 14 && this.hasLineOfSight(t)) {
                    this.enfriarEscupir = 50;
                    this.triggerAnim("golpe", "atacar");
                    Vec3 d = t.getEyePosition().subtract(this.getEyePosition());
                    SmallFireball f = new SmallFireball(this.level(), this, d.x, d.y, d.z);
                    f.setPos(this.getX(), this.getEyeY(), this.getZ());
                    this.level().addFreshEntity(f);
                    this.playSound(SoundEvents.BLAZE_SHOOT, 0.8f, 1.4f);
                }
            }
            case "lagartija_blanca" -> this.setInvisible(!manchado() && this.getDeltaMovement().horizontalDistanceSqr() < 0.0004 && this.getTarget() == null);
            case "ramita" -> {                                 // tiesa como roca hasta que pasas cerca
                Player p = this.level().getNearestPlayer(this, 5);
                if (p != null && !p.isCreative())
                    this.despierta = true;
                if (!this.despierta && !manchado())
                    this.getNavigation().stop();
            }
            case "hipopotamo" -> {                             // en el agua se enoja
                if (this.isInWater() && this.getTarget() == null && this.tickCount % 20 == 0) {
                    Player p = this.level().getNearestPlayer(this, 10);
                    if (p != null && !p.isCreative())
                        this.setTarget(p);
                }
            }
            case "cria_moruvahn" -> {
                if (this.isInWater() && this.tickCount % 20 == 0)
                    this.heal(1f);
            }
            default -> {
            }
        }
    }

    // ------------------------------------------------------------------ pegar y recibir

    @Override
    public boolean doHurtTarget(Entity e) {
        if (this.enfriarGolpe > 0)
            return false;
        this.enfriarGolpe = Math.max(16, this.especie.ataqueLargo());
        if (this.especie.ataque())
            this.triggerAnim("golpe", "atacar");
        boolean pego = super.doHurtTarget(e);
        if (!pego || !(e instanceof LivingEntity v))
            return pego;
        switch (this.especie.id()) {
            case "escorpion_luz" -> v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 80, 1), this);
            case "murcielago_mura" -> v.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 0), this);
            case "garrapata_sal" -> v.addEffect(new MobEffectInstance(MobEffects.HUNGER, 200, 1), this);
            case "serpiente_rio_seco" -> v.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), this);
            case "cria_varkhum" -> v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2), this);
            case "lobo_fuego" -> v.setSecondsOnFire(4);
            case "cocodrilo_luz" -> {
                Vec3 jala = this.position().subtract(v.position()).normalize().scale(0.6);
                v.push(jala.x, 0.1, jala.z);
                v.hurtMarked = true;
            }
            case "toro_arena", "bufalo_terracota", "cria_iskarum", "cabra_escarcha" -> {
                Vec3 avienta = v.position().subtract(this.position()).normalize().scale(id("cabra_escarcha") ? 1.6 : 1.1);
                v.push(avienta.x, 0.45, avienta.z);
                v.hurtMarked = true;
            }
            case "halcon_cobre" -> {                           // te tira lo que traes en la mano
                if (v instanceof Player p && !p.getMainHandItem().isEmpty() && this.random.nextInt(3) == 0) {
                    ItemStack s = p.getMainHandItem().copy();
                    p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                    p.drop(s, true);
                }
            }
            case "babuino" -> {                                // se lleva comida
                if (v instanceof Player p && this.getMainHandItem().isEmpty())
                    for (int k = 0; k < p.getInventory().getContainerSize(); k++) {
                        ItemStack s = p.getInventory().getItem(k);
                        if (s.isEdible()) {
                            this.setItemSlot(EquipmentSlot.MAINHAND, s.split(1));
                            this.setDropChance(EquipmentSlot.MAINHAND, 1f);
                            break;
                        }
                    }
            }
            default -> {
            }
        }
        if (manchado() && v instanceof Bicho otro && this.random.nextInt(4) == 0)
            otro.manchar();                                    // la mura se pega
        return true;
    }

    @Override
    public boolean hurt(DamageSource fuente, float cantidad) {
        if (id("cervatillo_musgo") && !fuente.is(DamageTypeTags.BYPASSES_INVULNERABILITY))
            return false;                                      // al cervatillo nadie le hace dano
        boolean pego = super.hurt(fuente, cantidad);
        if (pego && !this.level().isClientSide) {
            this.entityData.set(AMBIENTE, -1);
            this.despierta = true;
            if (id("lagarto_roca") && !this.colaSuelta) {      // suelta la cola y huye
                this.colaSuelta = true;
                this.spawnAtLocation(new ItemStack(ObjetosMipack.COLA_LAGARTO.get()));
            }
        }
        return pego;
    }

    @Override
    public void die(DamageSource fuente) {
        super.die(fuente);
        if (!(this.level() instanceof ServerLevel sl))
            return;
        if (id("escarabajo_brasa")) {                          // revienta en chispas
            sl.explode(this, this.getX(), this.getY(), this.getZ(), 1.6f, true, Level.ExplosionInteraction.NONE);
            sl.sendParticles(ParticleTypes.LAVA, this.getX(), this.getY() + 0.3, this.getZ(), 20, 0.4, 0.3, 0.4, 0.1);
        } else if (id("escarabajo_sagrado")) {                 // su bola suelta algo al azar
            List<ItemStack> premios = List.of(new ItemStack(Items.GOLD_NUGGET, 3), new ItemStack(Items.SAND, 4),
                    new ItemStack(Items.BONE), new ItemStack(Items.LAPIS_LAZULI, 2), new ItemStack(Items.EMERALD));
            this.spawnAtLocation(premios.get(this.random.nextInt(premios.size())).copy());
        }
        if (manchado() && this.random.nextInt(3) == 0)
            this.spawnAtLocation(new ItemStack(ObjetosMipack.MURA.get()));
    }

    @Override
    protected InteractionResult mobInteract(Player p, InteractionHand mano) {
        ItemStack s = p.getItemInHand(mano);
        if (s.is(ObjetosMipack.MURA.get()) && !manchado() && !id("cervatillo_musgo")) {
            if (!this.level().isClientSide) {
                manchar();
                if (!p.getAbilities().instabuild)
                    s.shrink(1);
            }
            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
        if (id("dromedario") && !manchado() && s.isEmpty() && !this.isVehicle() && !p.isShiftKeyDown()) {
            if (!this.level().isClientSide)
                p.startRiding(this);
            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
        return super.mobInteract(p, mano);
    }

    // ------------------------------------------------------------------ el dromedario se monta

    @Override
    public LivingEntity getControllingPassenger() {
        return id("dromedario") && this.getFirstPassenger() instanceof Player p ? p : null;
    }

    @Override
    protected void tickRidden(Player p, Vec3 v) {
        super.tickRidden(p, v);
        this.setRot(p.getYRot(), p.getXRot() * 0.5f);
        this.yRotO = this.yBodyRot = this.yHeadRot = this.getYRot();
    }

    @Override
    protected Vec3 getRiddenInput(Player p, Vec3 v) {
        float lado = p.xxa * 0.5f, frente = p.zza;
        if (frente <= 0)
            frente *= 0.25f;
        return new Vec3(lado, 0, frente);
    }

    @Override
    protected float getRiddenSpeed(Player p) {
        boolean arena = this.level().getBlockState(this.getBlockPosBelowThatAffectsMyMovement()).is(BlockTags.SAND);
        return (float) this.getAttributeValue(Attributes.MOVEMENT_SPEED) * (arena ? 1.6f : 1.1f);
    }

    @Override
    public double getPassengersRidingOffset() {
        return this.getBbHeight() * 0.85;
    }

    // ------------------------------------------------------------------ lo demas

    @Override
    public boolean causeFallDamage(float d, float m, DamageSource f) {
        return !this.especie.vuela() && super.causeFallDamage(d, m, f);
    }

    @Override
    public boolean removeWhenFarAway(double d) {
        return false;
    }

    @Override
    protected SoundEvent getAmbientSound() {
        return switch (this.especie.id()) {
            case "toro_arena", "bufalo_terracota", "hipopotamo", "cria_iskarum" -> SoundEvents.COW_AMBIENT;
            case "chacal_ceniza", "lobo_fuego" -> SoundEvents.WOLF_GROWL;
            case "fenec" -> SoundEvents.FOX_AMBIENT;
            case "gato_thza" -> SoundEvents.CAT_AMBIENT;
            case "pato_estanque" -> SoundEvents.CHICKEN_AMBIENT;
            case "cabra_escarcha" -> SoundEvents.GOAT_AMBIENT;
            case "dromedario" -> SoundEvents.LLAMA_AMBIENT;
            case "murcielago_mura" -> SoundEvents.BAT_AMBIENT;
            case "ballenato_duna" -> SoundEvents.DOLPHIN_AMBIENT;
            case "cria_moruvahn" -> SoundEvents.AXOLOTL_IDLE_AIR;
            case "babuino" -> SoundEvents.PANDA_AMBIENT;
            case "buitre", "halcon_cobre", "aguila_gris", "cuervo_negro", "ibis", "flamenco" -> SoundEvents.PARROT_AMBIENT;
            case "escorpion_luz", "garrapata_sal", "ramita", "escarabajo_sagrado", "escarabajo_brasa", "cangrejo" -> SoundEvents.SPIDER_AMBIENT;
            case "liebre_dorada", "marmota" -> SoundEvents.RABBIT_AMBIENT;
            case "cervatillo_musgo" -> SoundEvents.GOAT_AMBIENT;
            default -> SoundEvents.SILVERFISH_AMBIENT;
        };
    }

    @Override
    public float getVoicePitch() {
        return super.getVoicePitch() * (this.getBbHeight() > 1.3f ? 0.7f : this.getBbHeight() < 0.5f ? 1.4f : 1.0f);
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putBoolean("Manchado", manchado());
        tag.putBoolean("ColaSuelta", this.colaSuelta);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        this.entityData.set(MANCHADO, tag.getBoolean("Manchado"));
        this.colaSuelta = tag.getBoolean("ColaSuelta");
        metas();
    }

    // ------------------------------------------------------------------ animaciones

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar c) {
        c.add(new AnimationController<>(this, "cuerpo", 5, this::animar));
        c.add(new AnimationController<>(this, "golpe", 2, s -> PlayState.STOP).triggerableAnim("atacar", this.atacar));
    }

    private PlayState animar(AnimationState<Bicho> s) {
        int a = this.entityData.get(AMBIENTE);
        if (a >= 0 && a < this.ambientes.length)
            return s.setAndContinue(this.ambientes[a]);
        if (volando())
            return s.setAndContinue(this.correr);
        if (s.isMoving() || this.getDeltaMovement().horizontalDistanceSqr() > 0.0006)
            return s.setAndContinue(this.entityData.get(CORRIENDO) ? this.correr : this.caminar);
        return PlayState.STOP;
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return this.cache;
    }
}
