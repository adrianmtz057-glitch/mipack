package com.mipack.objetos;

import com.mipack.Mipack;
import com.mipack.khaset.ParticulasKhaset;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingChangeTargetEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.function.BiFunction;
import java.util.function.Supplier;

/**
 * Lo que se avienta: la bomba de brasa (estalla en fuego sin romper bloques) y el señuelo de plumas negras (los
 * hostiles de alrededor se olvidan de ti y van a donde cayo, un rato).
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID)
public final class Lanzables {
    private Lanzables() {
    }

    /** El objeto que se avienta (como una bola de nieve). */
    public static final class Lanzable extends Item {
        private final BiFunction<Level, LivingEntity, ThrowableItemProjectile> crear;
        private final String ayuda;

        public Lanzable(Properties p, BiFunction<Level, LivingEntity, ThrowableItemProjectile> crear, String ayuda) {
            super(p);
            this.crear = crear;
            this.ayuda = ayuda;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level nivel, Player p, InteractionHand mano) {
            ItemStack s = p.getItemInHand(mano);
            nivel.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.SNOWBALL_THROW, SoundSource.PLAYERS, 0.6f, 0.6f);
            if (!nivel.isClientSide) {
                ThrowableItemProjectile t = crear.apply(nivel, p);
                t.setItem(s.copyWithCount(1));
                t.shootFromRotation(p, p.getXRot(), p.getYRot(), 0.0f, 1.2f, 1.0f);
                nivel.addFreshEntity(t);
            }
            p.getCooldowns().addCooldown(this, 15);
            if (!p.getAbilities().instabuild)
                s.shrink(1);
            return InteractionResultHolder.sidedSuccess(s, nivel.isClientSide);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ObjetosSimples.ayuda(lineas, ayuda);
        }
    }

    // ------------------------------------------------------------------ bomba de brasa

    public static final class Bomba extends ThrowableItemProjectile {
        public Bomba(EntityType<? extends Bomba> t, Level l) {
            super(t, l);
        }

        public Bomba(Level l, LivingEntity quien) {
            super(ObjetosMipack.BOMBA.get(), quien, l);
        }

        @Override
        protected Item getDefaultItem() {
            return ObjetosMipack.BOMBA_BRASA.get();
        }

        @Override
        public void tick() {
            super.tick();
            if (level().isClientSide && tickCount % 2 == 0)
                level().addParticle(ParticleTypes.SMALL_FLAME, getX(), getY() + 0.2, getZ(), 0, 0.02, 0);
        }

        @Override
        protected void onHit(HitResult r) {
            super.onHit(r);
            if (level().isClientSide)
                return;
            ServerLevel nivel = (ServerLevel) level();
            nivel.explode(this, getX(), getY(), getZ(), 1.2f, false, Level.ExplosionInteraction.NONE);
            for (LivingEntity e : nivel.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(3.0)))
                if (!e.fireImmune())
                    e.setSecondsOnFire(6);
            nivel.sendParticles(ParticleTypes.FLAME, getX(), getY() + 0.3, getZ(), 40, 1.2, 0.4, 1.2, 0.03);
            nivel.sendParticles(ParticulasKhaset.BRASA.get(), getX(), getY() + 0.3, getZ(), 24, 1.0, 0.6, 1.0, 0.05);
            discard();
        }
    }

    // ------------------------------------------------------------------ senuelo de plumas negras

    private record Senuelo(ServerLevel nivel, Vec3 donde, long hasta) {
    }

    private static final List<Senuelo> SENUELOS = new ArrayList<>();
    private static final double RADIO = 16.0;

    public static final class Plumas extends ThrowableItemProjectile {
        public Plumas(EntityType<? extends Plumas> t, Level l) {
            super(t, l);
        }

        public Plumas(Level l, LivingEntity quien) {
            super(ObjetosMipack.SENUELO.get(), quien, l);
        }

        @Override
        protected Item getDefaultItem() {
            return ObjetosMipack.SENUELO_PLUMA.get();
        }

        @Override
        protected void onHit(HitResult r) {
            super.onHit(r);
            if (level() instanceof ServerLevel nivel) {
                SENUELOS.add(new Senuelo(nivel, position(), nivel.getGameTime() + 240));
                nivel.playSound(null, blockPosition(), SoundEvents.PARROT_IMITATE_PHANTOM, SoundSource.PLAYERS, 1.0f, 0.6f);
                discard();
            }
        }
    }

    static boolean cercaDeSenuelo(Mob m) {
        for (Senuelo s : SENUELOS)
            if (s.nivel == m.level() && s.donde.distanceToSqr(m.position()) < RADIO * RADIO)
                return true;
        return false;
    }

    @SubscribeEvent
    public static void tick(TickEvent.ServerTickEvent e) {
        if (e.phase != TickEvent.Phase.END || SENUELOS.isEmpty())
            return;
        Iterator<Senuelo> it = SENUELOS.iterator();
        while (it.hasNext()) {
            Senuelo s = it.next();
            long t = s.nivel.getGameTime();
            if (t > s.hasta) {
                it.remove();
                continue;
            }
            if (t % 4 == 0)
                s.nivel.sendParticles(ParticulasKhaset.PLUMA.get(), s.donde.x, s.donde.y + 0.4, s.donde.z, 2, 0.3, 0.3, 0.3, 0.01);
            if (t % 10 != 0)
                continue;
            for (Monster m : s.nivel.getEntitiesOfClass(Monster.class, new AABB(BlockPos.containing(s.donde)).inflate(RADIO))) {
                if (m.getTarget() instanceof Player)
                    m.setTarget(null);
                m.getNavigation().moveTo(s.donde.x, s.donde.y, s.donde.z, 1.15);
            }
        }
    }

    /** Mientras dure el senuelo, los hostiles de alrededor no le hacen caso a los jugadores. */
    @SubscribeEvent
    public static void objetivo(LivingChangeTargetEvent e) {
        if (e.getEntity() instanceof Monster m && e.getNewTarget() instanceof Player && cercaDeSenuelo(m))
            e.setCanceled(true);
    }

    static Supplier<Item> bomba() {
        return () -> new Lanzable(new Item.Properties().stacksTo(16), Bomba::new, "item.mipack.bomba_brasa.ayuda");
    }

    static Supplier<Item> senuelo() {
        return () -> new Lanzable(new Item.Properties().stacksTo(16), Plumas::new, "item.mipack.senuelo_pluma.ayuda");
    }
}
