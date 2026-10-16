package com.mipack.entidad;

import com.mipack.Golpes;
import com.mipack.Mipack;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.List;

/**
 * ESQUIRLAS DE AMATISTA: las puas de Crackatos dejan pedazos de cristal enterrados. Quitan vida poco a poco (mas rapido
 * y mas por cada nivel, hasta V) y no se van con leche ni con el tiempo: solo cuando Crackatos muere (o si te mueres).
 * Si Crackatos ya no esta cerca (se descargo el mundo, lo quitaron con comandos) se caen solas.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class EfectosCrackatos {
    public static final DeferredRegister<MobEffect> EFECTOS = DeferredRegister.create(ForgeRegistries.MOB_EFFECTS, Mipack.MODID);
    public static final RegistryObject<MobEffect> ESQUIRLAS = EFECTOS.register("esquirlas", Esquirlas::new);
    public static final int MAXIMO = 4;                           // V
    private static final double CERCA = 200.0;

    private EfectosCrackatos() {
    }

    /** Una pua mas que se le entierra: sube un nivel (hasta V). */
    public static void clavar(LivingEntity e) {
        MobEffectInstance antes = e.getEffect(ESQUIRLAS.get());
        int nivel = antes == null ? 0 : Math.min(MAXIMO, antes.getAmplifier() + 1);
        e.addEffect(new MobEffectInstance(ESQUIRLAS.get(), MobEffectInstance.INFINITE_DURATION, nivel, false, true, true));
    }

    /** Crackatos murio: a todos los que esten cerca se les caen las esquirlas. */
    public static void quitarCerca(ServerLevel nivel, LivingEntity jefe) {
        for (LivingEntity e : nivel.getEntitiesOfClass(LivingEntity.class, jefe.getBoundingBox().inflate(CERCA),
                x -> x.hasEffect(ESQUIRLAS.get()))) {
            e.removeEffect(ESQUIRLAS.get());
            nivel.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState()),
                    e.getX(), e.getY() + e.getBbHeight() * 0.5, e.getZ(), 20, 0.3, 0.4, 0.3, 0.1);
        }
    }

    @SubscribeEvent
    public static void revisar(TickEvent.PlayerTickEvent evento) {
        var p = evento.player;
        if (evento.phase != TickEvent.Phase.END || p.level().isClientSide || p.tickCount % 100 != 0
                || !p.hasEffect(ESQUIRLAS.get()))
            return;
        if (p.level().getEntitiesOfClass(CrackatosEntity.class, p.getBoundingBox().inflate(CERCA), LivingEntity::isAlive).isEmpty())
            p.removeEffect(ESQUIRLAS.get());
    }

    static final class Esquirlas extends MobEffect {
        Esquirlas() {
            super(MobEffectCategory.HARMFUL, 0x9A5CE6);
        }

        @Override
        public List<ItemStack> getCurativeItems() {
            return new ArrayList<>();
        }

        @Override
        public boolean isDurationEffectTick(int duracion, int nivel) {
            return true;                                          // dura para siempre: el ritmo lo lleva applyEffectTick
        }

        /** I: 1 de vida cada 3 s ... V: 2 de vida cada segundo. */
        @Override
        public void applyEffectTick(LivingEntity e, int nivel) {
            int cada = Math.max(20, 60 - 10 * nivel);
            if (!(e.level() instanceof ServerLevel sl) || e.tickCount % cada != 0)
                return;
            e.hurt(Golpes.fuente(e, Golpes.ESQUIRLAS, null), 1.0f + nivel * 0.25f);
            sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_CLUSTER.defaultBlockState()),
                    e.getX(), e.getY() + e.getBbHeight() * 0.6, e.getZ(), 3 + 2 * nivel, e.getBbWidth() * 0.3,
                    e.getBbHeight() * 0.25, e.getBbWidth() * 0.3, 0.05);
        }
    }
}
