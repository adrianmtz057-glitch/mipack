package com.mipack.objetos;

import com.mipack.Mipack;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/**
 * Los efectos de los objetos y del clima. Los dos primeros son avisos (los pone el sistema de agua y frio mientras
 * dure la condicion; lo que hacen lo hace ese sistema): se ven en el menu para que el jugador sepa por que se le va
 * el agua o la comida.
 * <ul>
 * <li>SOFOCACION: en el desierto, de dia y con armadura que encierra el calor: el agua se va mas rapido.</li>
 * <li>FRIO: en el frio de las montanas sin abrigo: la comida se va mas rapido.</li>
 * <li>BRANQUIAS (la pocion de la branquia de Moruvahn): respiras bajo el agua y ahi adentro te regeneras.</li>
 * </ul>
 */
public final class EfectosObjetos {
    public static final DeferredRegister<MobEffect> EFECTOS = DeferredRegister.create(ForgeRegistries.MOB_EFFECTS, Mipack.MODID);

    public static final RegistryObject<MobEffect> SOFOCACION = EFECTOS.register("sofocacion", () -> new Aviso(0xE8892E));
    public static final RegistryObject<MobEffect> FRIO = EFECTOS.register("frio", () -> new Aviso(0x9ED8FF));
    public static final RegistryObject<MobEffect> BRANQUIAS = EFECTOS.register("branquias", Branquias::new);
    /** Poseido por La Bruma (cordura en cero): quieto e invisible mientras su doble pelea; la leche no lo quita. */
    public static final RegistryObject<MobEffect> POSEIDO = EFECTOS.register("poseido", () -> new Aviso(0x3B1450) {
        @Override
        public java.util.List<net.minecraft.world.item.ItemStack> getCurativeItems() {
            return new java.util.ArrayList<>();
        }
    }.addAttributeModifier(net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED,
            "4f0c6b1e-2a77-4d0e-9a1c-6f3e2b9d7a11", -1.0, net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.MULTIPLY_TOTAL));

    private EfectosObjetos() {
    }

    /** Un efecto que solo avisa (no hace nada por si mismo). */
    public static class Aviso extends MobEffect {
        Aviso(int color) {
            super(MobEffectCategory.HARMFUL, color);
        }
    }

    public static final class Branquias extends MobEffect {
        Branquias() {
            super(MobEffectCategory.BENEFICIAL, 0xF07A92);
        }

        @Override
        public void applyEffectTick(LivingEntity e, int nivel) {
            if (!e.isInWaterOrBubble())
                return;
            e.setAirSupply(e.getMaxAirSupply());
            if (e.tickCount % Math.max(10, 50 >> nivel) == 0 && e.getHealth() < e.getMaxHealth())
                e.heal(1.0f);
        }

        @Override
        public boolean isDurationEffectTick(int duracion, int nivel) {
            return true;
        }
    }
}
