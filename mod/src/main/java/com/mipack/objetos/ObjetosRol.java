package com.mipack.objetos;

import com.mipack.Mipack;
import com.mipack.khaset.KhasetEntity;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.util.List;

/**
 * Los objetos de rol (solo con /give, sin receta): la espada de vitae, la espada de hielo de Kemira, el martillo negro
 * del tanque y el totem de Anj. Las armaduras de hielo y de tanque estan en MaterialArmadura.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class ObjetosRol {
    private static final String ANJ = "mipack_anj";
    /** Por cuanto multiplica la espada de hielo el dano contra Khaset (contra lo demas pega como una de hierro). */
    private static final float HIELO_KHASET = 6f;

    private ObjetosRol() {
    }

    private static void ayuda(List<Component> l, String clave) {
        ObjetosSimples.ayuda(l, clave);
    }

    /** Espada de vitae (Baru, ramas de los Jardines): pegarle al doble de un poseido lo regresa entero. */
    public static final class Vitae extends SwordItem {
        public Vitae(Properties p) {
            super(Tiers.DIAMOND, 2, -2.4f, p.rarity(Rarity.EPIC).fireResistant());
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.espada_vitae.ayuda");
        }

        @Override
        public boolean isFoil(ItemStack s) {
            return true;
        }
    }

    /** Espada de hielo (Kemira): contra Khaset pega muchisimo; contra lo demas, como de hierro. */
    public static final class Hielo extends SwordItem {
        public Hielo(Properties p) {
            super(Tiers.IRON, 3, -2.4f, p.rarity(Rarity.EPIC));
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.espada_hielo.ayuda");
        }
    }

    /** El martillo negro del tanque: enorme, lento, avienta lejos. */
    public static final class MartilloNegro extends SwordItem {
        public MartilloNegro(Properties p) {
            super(Tiers.NETHERITE, 9, -3.4f, p.rarity(Rarity.EPIC).fireResistant());
        }

        @Override
        public boolean hurtEnemy(ItemStack s, LivingEntity v, LivingEntity quien) {
            v.knockback(1.6, quien.getX() - v.getX(), quien.getZ() - v.getZ());
            return super.hurtEnemy(s, v, quien);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.martillo_negro.ayuda");
        }
    }

    /** Totem de Anj (el ankh): lo del totem normal, mas 2 s sin recibir dano y Velocidad II. */
    public static final class Anj extends Item {
        public Anj(Properties p) {
            super(p.stacksTo(1).rarity(Rarity.EPIC));
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.totem_anj.ayuda");
        }
    }

    @SubscribeEvent
    public static void hielo(LivingHurtEvent e) {
        if (e.getEntity() instanceof KhasetEntity k && e.getSource().getEntity() instanceof LivingEntity a
                && e.getSource().getDirectEntity() == a && a.getMainHandItem().is(ObjetosMipack.ESPADA_HIELO.get())) {
            e.setAmount(e.getAmount() * HIELO_KHASET);
            if (k.level() instanceof ServerLevel sl)
                sl.sendParticles(ParticleTypes.SNOWFLAKE, k.getX(), k.getY() + k.getBbHeight() * 0.6, k.getZ(), 30, 0.6, 1.0, 0.6, 0.1);
            k.playSound(SoundEvents.GLASS_BREAK, 1.5f, 0.6f);
        }
    }

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void anj(LivingDeathEvent e) {
        if (!(e.getEntity() instanceof Player p) || p.level().isClientSide)
            return;
        for (InteractionHand mano : InteractionHand.values()) {
            ItemStack s = p.getItemInHand(mano);
            if (!s.is(ObjetosMipack.TOTEM_ANJ.get()))
                continue;
            e.setCanceled(true);
            s.shrink(1);
            p.setHealth(1f);
            p.removeAllEffects();
            p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 900, 1));
            p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 100, 1));
            p.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 800, 0));
            p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 100, 1));
            p.getPersistentData().putLong(ANJ, p.level().getGameTime() + 40);
            p.level().broadcastEntityEvent(p, (byte) 35);
            p.level().playSound(null, p.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.5f, 1.4f);
            if (p.level() instanceof ServerLevel sl)
                sl.sendParticles(ParticleTypes.END_ROD, p.getX(), p.getY() + 1, p.getZ(), 50, 0.5, 1.0, 0.5, 0.15);
            return;
        }
    }

    /** Los 2 s de Anj: no entra ningun golpe. */
    @SubscribeEvent
    public static void protegido(LivingAttackEvent e) {
        if (e.getEntity() instanceof Player p && p.getPersistentData().getLong(ANJ) > p.level().getGameTime())
            e.setCanceled(true);
    }
}
