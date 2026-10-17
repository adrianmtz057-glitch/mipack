package com.mipack.arena;

import com.mipack.Golpes;
import com.mipack.Mipack;
import com.mipack.bruma.BrumaEntity;
import com.mipack.entidad.CrackatosEntity;
import com.mipack.khaset.KhasetEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.LongArrayTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.entity.EntityLeaveLevelEvent;
import net.minecraftforge.event.entity.EntityTeleportEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.level.BlockEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Las arenas de los jefes. Un jefe que sale cerca de un bloque central (mipack:centro_arena) toma esa arena:
 * <ul>
 * <li>no sale del radio (config/mipack-arena.toml) y si no queda nadie vivo adentro unos minutos se cura y vuelve;</li>
 * <li>sus ataques de centro (Crackatos: la lluvia de puas y el azote; Khaset: el silbato) solo los hace parado en el
 *     bloque. Si alguien esta parado en el bloque cuando llega, el ataque no sale y el jefe se aturde, pero a quien lo
 *     bloqueo le pega fuerte, salvo que traiga la armadura de tanque completa (etiqueta mipack:armadura_tanque);</li>
 * <li>adentro, mientras hay jefe: sin PvP, sin poner ni romper bloques y sin perlas ni coros;</li>
 * <li>quien le pega de muy lejos, desde fuera o desde muy arriba hace la cuarta parte y le cae un rayo de castigo;</li>
 * <li>si la pelea se alarga se enfurece: pega 40 % mas, pero recibe 30 % mas.</li>
 * </ul>
 * La vida de los jefes se ajusta aqui tambien: llena con 30 jugadores (config) y menos con menos.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class Arena {
    public static final TagKey<Item> TANQUE = TagKey.create(Registries.ITEM, new ResourceLocation(Mipack.MODID, "armadura_tanque"));
    private static final String CENTRO = "mipack_centro", PELEA = "mipack_pelea", VACIO = "mipack_vacio",
            FURIA = "mipack_furia", CASTIGO = "mipack_castigo";
    private static final float FURIA_PEGA = 1.4f, FURIA_RECIBE = 1.3f, LEJOS = 0.25f;
    private static final Set<Mob> JEFES = new LinkedHashSet<>();

    private Arena() {
    }

    public static boolean esJefe(Entity e) {
        return e instanceof CrackatosEntity || e instanceof KhasetEntity || e instanceof BrumaEntity;
    }

    public static int radio() {
        return ConfigArena.RADIO.get();
    }

    /** La vida del jefe con 'n' jugadores: toda con los jugadores plenos (30), y con menos una parte (casi lineal). */
    public static float vida(double llena, int n) {
        int plenos = ConfigArena.JUGADORES_PLENOS.get();
        double parte = 0.02 + 0.98 * Math.min(Math.max(n, 1), plenos) / plenos;
        return (float) (llena * parte);
    }

    /** El centro de la arena de este jefe (o null si no tiene). */
    public static BlockPos centro(Mob jefe) {
        CompoundTag d = jefe.getPersistentData();
        return d.contains(CENTRO) ? BlockPos.of(d.getLong(CENTRO)) : null;
    }

    /** Este jefe tiene arena y ya se salio del radio (para que no corra mas alla). */
    public static boolean fuera(Mob jefe) {
        BlockPos c = centro(jefe);
        return c != null && horizontal(jefe.position(), c) > radio();
    }

    /** Ya llego al bloque (esta parado encima o casi). */
    public static boolean enCentro(Mob jefe) {
        BlockPos c = centro(jefe);
        return c != null && horizontal(jefe.position(), c) < Math.max(2.0, jefe.getBbWidth() * 0.3);
    }

    public static Vec3 encima(BlockPos c) {
        return new Vec3(c.getX() + 0.5, c.getY() + 1.0, c.getZ() + 0.5);
    }

    private static double horizontal(Vec3 p, BlockPos c) {
        double dx = p.x - (c.getX() + 0.5), dz = p.z - (c.getZ() + 0.5);
        return Math.sqrt(dx * dx + dz * dz);
    }

    public static boolean dentro(BlockPos c, Entity e) {
        double dy = e.getY() - c.getY();
        return horizontal(e.position(), c) <= radio() && dy > -24 && dy < 40;
    }

    public static boolean valido(Player p) {
        return p.isAlive() && !p.isSpectator() && !p.isCreative();
    }

    /** Cuantos jugadores pelean: los de la arena si tiene, o los que esten a 'radioSin' si no. */
    public static int jugadores(Mob jefe, double radioSin) {
        BlockPos c = centro(jefe);
        int n = 0;
        for (Player p : jefe.level().players())
            if (valido(p) && (c != null ? dentro(c, p) : p.distanceToSqr(jefe) < radioSin * radioSin))
                n++;
        return n;
    }

    public static boolean tanque(Player p) {
        int piezas = 0;
        for (ItemStack s : p.getArmorSlots())
            if (s.is(TANQUE))
                piezas++;
        return piezas >= 4;
    }

    /**
     * El jefe llego al centro para su ataque de centro: si alguien esta parado en el bloque, lo bloquea (el ataque no
     * sale, a ese le pega fuerte si no es tanque) y regresa false. Si no, true: que ataque.
     */
    public static boolean intentarCentro(Mob jefe) {
        return !(jefe.level() instanceof ServerLevel sl) || intentarCentro(jefe, sl.players());
    }

    /** Lo mismo, viendo solo a estos jugadores (las pruebas). */
    public static boolean intentarCentro(Mob jefe, List<? extends Player> jugadores) {
        BlockPos c = centro(jefe);
        if (c == null || !(jefe.level() instanceof ServerLevel sl))
            return true;
        Player bloquea = null;
        for (Player p : jugadores)
            if (valido(p) && Math.abs(p.getX() - (c.getX() + 0.5)) < 1.0 && Math.abs(p.getZ() - (c.getZ() + 0.5)) < 1.0
                    && p.getY() > c.getY() + 0.5 && p.getY() < c.getY() + 3.0)
                bloquea = p;
        if (bloquea == null)
            return true;
        boolean tanque = tanque(bloquea);
        Golpes.pegar(bloquea, jefe, tanque ? 4f : 24f, 100);
        Vec3 empuje = bloquea.position().subtract(jefe.position()).normalize();
        bloquea.push(empuje.x * (tanque ? 0.2 : 1.2), tanque ? 0.1 : 0.6, empuje.z * (tanque ? 0.2 : 1.2));
        bloquea.hurtMarked = true;
        sl.playSound(null, c, SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 3.0f, 0.6f);
        sl.playSound(null, c, SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 3.0f, 0.7f);
        sl.sendParticles(ParticleTypes.CRIT, c.getX() + 0.5, c.getY() + 1.5, c.getZ() + 0.5, 60, 1.0, 1.0, 1.0, 0.4);
        sl.sendParticles(ParticleTypes.EXPLOSION, c.getX() + 0.5, c.getY() + 1.2, c.getZ() + 0.5, 3, 0.5, 0.3, 0.5, 0);
        Component msj = Component.translatable(tanque ? "arena.mipack.bloqueo_tanque" : "arena.mipack.bloqueo",
                bloquea.getDisplayName(), jefe.getDisplayName()).withStyle(ChatFormatting.GOLD);
        for (Player p : sl.players())
            if (dentro(c, p))
                p.displayClientMessage(msj, true);
        return false;
    }

    public static boolean furioso(Mob jefe) {
        return jefe.getPersistentData().getBoolean(FURIA);
    }

    /** La arena con jefe en la que esta 'e' (o null). */
    public static BlockPos activa(Entity e) {
        for (Mob j : JEFES) {
            if (j.level() != e.level() || !j.isAlive())
                continue;
            BlockPos c = centro(j);
            if (c != null && dentro(c, e))
                return c;
        }
        return null;
    }

    // ------------------------------------------------------------------ los jefes de cada arena

    @SubscribeEvent
    public static void entra(EntityJoinLevelEvent evento) {
        if (evento.getLevel().isClientSide() || !(evento.getEntity() instanceof Mob jefe) || !esJefe(jefe))
            return;
        JEFES.add(jefe);
        if (centro(jefe) == null && evento.getLevel() instanceof ServerLevel sl) {
            BlockPos c = Centros.de(sl).cerca(jefe.blockPosition(), radio() * 1.5);
            if (c != null)
                jefe.getPersistentData().putLong(CENTRO, c.asLong());
        }
    }

    @SubscribeEvent
    public static void sale(EntityLeaveLevelEvent evento) {
        JEFES.remove(evento.getEntity());
    }

    @SubscribeEvent
    public static void tick(TickEvent.LevelTickEvent evento) {
        if (evento.phase != TickEvent.Phase.END || !(evento.level instanceof ServerLevel sl))
            return;
        for (Mob jefe : new ArrayList<>(JEFES)) {
            if (jefe.level() != sl)
                continue;
            if (jefe.isRemoved()) {
                JEFES.remove(jefe);
                continue;
            }
            BlockPos c = centro(jefe);
            if (c == null || !jefe.isAlive())
                continue;
            if (sl.getGameTime() % 100 == 0 && sl.isLoaded(c) && !(sl.getBlockState(c).getBlock() instanceof BloqueCentro)) {
                jefe.getPersistentData().remove(CENTRO);          // quitaron el bloque: ya no hay arena
                continue;
            }
            correa(jefe, c);
            if (sl.getGameTime() % 10 == 0)
                pelea(sl, jefe, c);
        }
    }

    /** No sale del radio: si se pasa, lo regresa a la orilla. */
    private static void correa(Mob jefe, BlockPos c) {
        double r = radio(), d = horizontal(jefe.position(), c);
        if (d <= r)
            return;
        Vec3 centro = encima(c);
        Vec3 desde = new Vec3(jefe.getX() - centro.x, 0, jefe.getZ() - centro.z).scale((r - 0.5) / d);
        jefe.setPos(centro.x + desde.x, jefe.getY(), centro.z + desde.z);
        Vec3 v = jefe.getDeltaMovement();
        jefe.setDeltaMovement(v.x * -0.2, v.y, v.z * -0.2);
    }

    /** Cada medio segundo: cuanto lleva la pelea, la furia y el reinicio si se quedo solo. */
    private static void pelea(ServerLevel sl, Mob jefe, BlockPos c) {
        CompoundTag d = jefe.getPersistentData();
        List<Player> adentro = new ArrayList<>();
        for (Player p : sl.players())
            if (valido(p) && dentro(c, p))
                adentro.add(p);
        if (!adentro.isEmpty()) {
            d.putInt(VACIO, 0);
            for (Player p : adentro)                           // el tiempo en el centro (tabla de MVP)
                if (Math.abs(p.getX() - (c.getX() + 0.5)) < 1.0 && Math.abs(p.getZ() - (c.getZ() + 0.5)) < 1.0
                        && p.getY() > c.getY() + 0.5 && p.getY() < c.getY() + 3.0)
                    Mvp.sumar(jefe, p, Mvp.Cat.CENTRO, 10);
            int t = d.getInt(PELEA) + 10;
            d.putInt(PELEA, t);
            if (!d.getBoolean(FURIA) && t > ConfigArena.MINUTOS_FURIA.get() * 1200) {
                d.putBoolean(FURIA, true);
                sl.playSound(null, jefe.blockPosition(), SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 4.0f, 0.6f);
                Component msj = Component.translatable("arena.mipack.furia", jefe.getDisplayName()).withStyle(ChatFormatting.RED);
                for (Player p : adentro)
                    p.displayClientMessage(msj, false);
            }
            if (d.getBoolean(FURIA))
                sl.sendParticles(ParticleTypes.ANGRY_VILLAGER, jefe.getX(), jefe.getY() + jefe.getBbHeight() * 0.8, jefe.getZ(),
                        2, jefe.getBbWidth() * 0.4, jefe.getBbHeight() * 0.2, jefe.getBbWidth() * 0.4, 0);
            return;
        }
        int vacio = d.getInt(VACIO) + 10;
        d.putInt(VACIO, vacio);
        if (vacio > ConfigArena.MINUTOS_REINICIO.get() * 1200 && (d.getInt(PELEA) > 0 || jefe.getHealth() < jefe.getMaxHealth())) {
            d.putInt(PELEA, 0);
            d.putBoolean(FURIA, false);
            jefe.setHealth(jefe.getMaxHealth());
            jefe.setTarget(null);
            Vec3 e = encima(c);
            jefe.teleportTo(e.x, e.y, e.z);
            sl.sendParticles(ParticleTypes.CLOUD, e.x, e.y + 1, e.z, 40, 2, 1, 2, 0.05);
        }
    }

    // ------------------------------------------------------------------ el dano: furia y los de lejos

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void dano(LivingHurtEvent evento) {
        LivingEntity victima = evento.getEntity();
        DamageSource s = evento.getSource();
        if (victima.level().isClientSide())
            return;
        if (s.getEntity() instanceof Mob jefe && esJefe(jefe) && furioso(jefe))
            evento.setAmount(evento.getAmount() * FURIA_PEGA);
        if (!(victima instanceof Mob jefe) || !esJefe(jefe))
            return;
        BlockPos c = centro(jefe);
        if (c == null)
            return;
        if (furioso(jefe))
            evento.setAmount(evento.getAmount() * FURIA_RECIBE);
        if (s.getEntity() instanceof Player p && !p.isCreative()) {
            double lejos = p.distanceTo(jefe) - jefe.getBbWidth() * 0.5;
            if (!dentro(c, p) || lejos > ConfigArena.DISTANCIA_LEJOS.get() || p.getY() > c.getY() + ConfigArena.ALTURA_ARRIBA.get()) {
                evento.setAmount(evento.getAmount() * LEJOS);
                castigar(p, jefe);
            }
        }
    }

    /** El rayo de castigo (solo se ve) para el que pega de lejos o desde arriba: duele, alenta y lo marca. */
    private static void castigar(Player p, Mob jefe) {
        CompoundTag d = p.getPersistentData();
        long ahora = p.level().getGameTime();
        if (ahora - d.getLong(CASTIGO) < 60 || !(p.level() instanceof ServerLevel sl))
            return;
        d.putLong(CASTIGO, ahora);
        LightningBolt rayo = EntityType.LIGHTNING_BOLT.create(sl);
        if (rayo != null) {
            rayo.moveTo(p.getX(), p.getY(), p.getZ());
            rayo.setVisualOnly(true);
            sl.addFreshEntity(rayo);
        }
        p.hurt(jefe.damageSources().indirectMagic(jefe, jefe), 6f);
        p.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0, false, false, true));
        p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1, false, false, true));
        p.displayClientMessage(Component.translatable("arena.mipack.lejos").withStyle(ChatFormatting.RED), true);
    }

    // ------------------------------------------------------------------ las reglas adentro

    @SubscribeEvent
    public static void pvp(LivingAttackEvent evento) {
        if (evento.getEntity() instanceof Player v && evento.getSource().getEntity() instanceof Player a && v != a
                && !v.level().isClientSide() && (activa(v) != null || activa(a) != null))
            evento.setCanceled(true);
    }

    @SubscribeEvent
    public static void romper(BlockEvent.BreakEvent evento) {
        Player p = evento.getPlayer();
        if (!p.isCreative() && !p.level().isClientSide() && activa(p) != null) {
            evento.setCanceled(true);
            p.displayClientMessage(Component.translatable("arena.mipack.bloques").withStyle(ChatFormatting.GRAY), true);
        }
    }

    @SubscribeEvent
    public static void poner(BlockEvent.EntityPlaceEvent evento) {
        if (evento.getEntity() instanceof Player p && !p.isCreative() && !p.level().isClientSide() && activa(p) != null) {
            evento.setCanceled(true);
            p.displayClientMessage(Component.translatable("arena.mipack.bloques").withStyle(ChatFormatting.GRAY), true);
        }
    }

    @SubscribeEvent
    public static void perla(EntityTeleportEvent.EnderPearl evento) {
        Player p = evento.getPlayer();
        if (!p.isCreative() && (activa(p) != null || activaEn(p, evento.getTarget()))) {
            evento.setCanceled(true);
            p.displayClientMessage(Component.translatable("arena.mipack.perlas").withStyle(ChatFormatting.GRAY), true);
        }
    }

    @SubscribeEvent
    public static void coro(EntityTeleportEvent.ChorusFruit evento) {
        if (evento.getEntityLiving() instanceof Player p && !p.isCreative() && activa(p) != null)
            evento.setCanceled(true);
    }

    private static boolean activaEn(Entity e, Vec3 donde) {
        for (Mob j : JEFES) {
            BlockPos c = centro(j);
            if (j.level() == e.level() && j.isAlive() && c != null && horizontal(donde, c) <= radio())
                return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ donde estan los bloques centrales

    /** Los bloques centrales puestos en cada dimension (se guardan con el mundo). */
    public static final class Centros extends SavedData {
        private static final String ARCHIVO = "mipack_arenas";
        private final Set<Long> centros = new HashSet<>();

        public static Centros de(ServerLevel sl) {
            return sl.getDataStorage().computeIfAbsent(Centros::cargar, Centros::new, ARCHIVO);
        }

        private static Centros cargar(CompoundTag tag) {
            Centros c = new Centros();
            for (long l : tag.getLongArray("centros"))
                c.centros.add(l);
            return c;
        }

        @Override
        public CompoundTag save(CompoundTag tag) {
            tag.put("centros", new LongArrayTag(new ArrayList<>(this.centros)));
            return tag;
        }

        public void poner(BlockPos pos, boolean hay) {
            if (hay ? this.centros.add(pos.asLong()) : this.centros.remove(pos.asLong()))
                setDirty();
        }

        public BlockPos cerca(BlockPos de, double max) {
            BlockPos mejor = null;
            double d = max * max;
            for (long l : this.centros) {
                BlockPos p = BlockPos.of(l);
                double dd = p.distSqr(de);
                if (dd < d) {
                    d = dd;
                    mejor = p;
                }
            }
            return mejor;
        }
    }
}
