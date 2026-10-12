package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Los efectos de la pelea con Khaset. Ninguno se quita con leche: son heridas, no pociones.
 * <ul>
 * <li>DESANGRADO (I a III): las garras de obsidiana cortan. Quita vida cada tanto y te alenta; en III te caes
 *     (DERRIBADO) y el desangrado vuelve a II. Se ve: gotas de sangre y la pantalla late en rojo.</li>
 * <li>DERRIBADO: de rodillas, sin poder moverte ni pegar (el corte de piernas, el salto del jaguar, el desangrado
 *     III). Khaset puede capturarte.</li>
 * <li>ATURDIDO: el silbato de la muerte: te tapas los oidos, sin moverte ni pegar.</li>
 * <li>DESORIENTADO: despues del silbato: la camara se mece y se tuerce.</li>
 * </ul>
 * Tambien aqui: los tipos de dano propios (data/mipack/damage_type).
 */
public final class EfectosKhaset {
    public static final DeferredRegister<MobEffect> EFECTOS = DeferredRegister.create(ForgeRegistries.MOB_EFFECTS, Mipack.MODID);

    public static final RegistryObject<MobEffect> DESANGRADO = EFECTOS.register("desangrado", Desangrado::new);
    public static final RegistryObject<MobEffect> DERRIBADO = EFECTOS.register("derribado",
            () -> new Herida(0x7A1E1E).addAttributeModifier(Attributes.MOVEMENT_SPEED, "9b3f2a8e-4c11-4a52-9a43-6b1c1e0d0a01",
                    -1.0, AttributeModifier.Operation.MULTIPLY_TOTAL));
    public static final RegistryObject<MobEffect> ATURDIDO = EFECTOS.register("aturdido",
            () -> new Herida(0xE6C84A).addAttributeModifier(Attributes.MOVEMENT_SPEED, "9b3f2a8e-4c11-4a52-9a43-6b1c1e0d0a02",
                    -1.0, AttributeModifier.Operation.MULTIPLY_TOTAL));
    public static final RegistryObject<MobEffect> DESORIENTADO = EFECTOS.register("desorientado", () -> new Herida(0x8A5CE0));

    public static final ResourceKey<DamageType> CALOR = dano("calor");
    public static final ResourceKey<DamageType> SANGRE = dano("desangrado");
    public static final ResourceKey<DamageType> SACRIFICIO = dano("sacrificio");

    private EfectosKhaset() {
    }

    private static ResourceKey<DamageType> dano(String nombre) {
        return ResourceKey.create(Registries.DAMAGE_TYPE, new ResourceLocation(Mipack.MODID, nombre));
    }

    public static DamageSource fuente(Level nivel, ResourceKey<DamageType> tipo, Entity quien) {
        Holder<DamageType> h = nivel.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(tipo);
        return quien == null ? new DamageSource(h) : new DamageSource(h, quien);
    }

    /** Sube el desangrado 'niveles' (hasta III: ahi se cae y vuelve a II). Dura 8 s desde el ultimo corte. */
    public static void cortar(LivingEntity e, int niveles) {
        MobEffectInstance antes = e.getEffect(DESANGRADO.get());
        int nivel = (antes == null ? -1 : antes.getAmplifier()) + niveles;
        if (nivel >= 2) {
            derribar(e, 60);
            nivel = 1;
        }
        e.addEffect(new MobEffectInstance(DESANGRADO.get(), 160, Math.max(0, nivel), false, true, true));
    }

    public static void derribar(LivingEntity e, int ticks) {
        e.addEffect(new MobEffectInstance(DERRIBADO.get(), ticks, 0, false, false, true));
    }

    public static boolean derribado(LivingEntity e) {
        return e.hasEffect(DERRIBADO.get());
    }

    /** Se puede capturar: esta en el piso o muy herido (desangrado II o mas). */
    public static boolean capturable(LivingEntity e) {
        MobEffectInstance d = e.getEffect(DESANGRADO.get());
        return derribado(e) || (d != null && d.getAmplifier() >= 1);
    }

    public static boolean sinControl(LivingEntity e) {
        return e.hasEffect(DERRIBADO.get()) || e.hasEffect(ATURDIDO.get());
    }

    /** Un efecto que no se quita con leche. */
    static class Herida extends MobEffect {
        Herida(int color) {
            super(MobEffectCategory.HARMFUL, color);
        }

        @Override
        public List<ItemStack> getCurativeItems() {
            return new ArrayList<>();
        }
    }

    /** Desangrado: quita 1 de vida cada 3 s en I y cada 2 s en II; alenta un 15 % por nivel. */
    static final class Desangrado extends Herida {
        Desangrado() {
            super(0xA1141E);
            addAttributeModifier(Attributes.MOVEMENT_SPEED, "9b3f2a8e-4c11-4a52-9a43-6b1c1e0d0a03", -0.15,
                    AttributeModifier.Operation.MULTIPLY_TOTAL);
        }

        @Override
        public boolean isDurationEffectTick(int duracion, int nivel) {
            int cada = nivel >= 1 ? 40 : 60;
            return duracion % cada == 0;
        }

        @Override
        public void applyEffectTick(LivingEntity e, int nivel) {
            if (e.level() instanceof ServerLevel sl) {
                e.hurt(fuente(sl, SANGRE, null), 1.0f);
                sl.sendParticles(ParticulasKhaset.SANGRE.get(), e.getX(), e.getY() + e.getBbHeight() * 0.6, e.getZ(),
                        4 + 3 * nivel, e.getBbWidth() * 0.3, e.getBbHeight() * 0.2, e.getBbWidth() * 0.3, 0.0);
            }
        }
    }
}
