package com.mipack;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.RangedAttribute;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;

/**
 * Lo que comparten los jefes para pegar de verdad:
 * <ul>
 * <li>tipos de dano propios (data/mipack/damage_type): el golpe de un jefe atraviesa la armadura (la proteccion de los
 *     encantamientos si cuenta, asi que la netherita con Proteccion IV aguanta, pero no es inmortal) y el escudo no lo
 *     para;</li>
 * <li>si le pegan a alguien que se cubre con escudo, el escudo se cae (como con un hacha) y no se puede volver a
 *     levantar en un rato;</li>
 * <li>la vida maxima del juego llega a 1024: los jefes de raid necesitan mas (se sube el tope al cargar el mod).</li>
 * </ul>
 */
public final class Golpes {
    /** Un golpe fisico de jefe: atraviesa la armadura y el escudo (Proteccion si cuenta). */
    public static final ResourceKey<DamageType> JEFE = tipo("golpe_jefe");
    /** Lo que quita forcejear mal en la mano de Khaset: parte de la vida segun la dificultad (nada lo reduce). */
    public static final ResourceKey<DamageType> FORCEJEO = tipo("forcejeo");
    /** Las esquirlas de amatista de Crackatos: sangran poco a poco (nada lo reduce). */
    public static final ResourceKey<DamageType> ESQUIRLAS = tipo("esquirlas");

    private Golpes() {
    }

    private static ResourceKey<DamageType> tipo(String nombre) {
        return ResourceKey.create(Registries.DAMAGE_TYPE, new ResourceLocation(Mipack.MODID, nombre));
    }

    public static DamageSource fuente(Entity en, ResourceKey<DamageType> tipo, Entity quien) {
        Holder<DamageType> h = en.level().registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(tipo);
        return quien == null ? new DamageSource(h) : new DamageSource(h, quien);
    }

    /** Un golpe de jefe: tira el escudo de quien se cubra y pega aunque se cubra (con el dano de su dificultad). */
    public static boolean pegar(LivingEntity victima, Entity jefe, float dano, int sinEscudo) {
        tirarEscudo(victima, sinEscudo);
        return victima.hurt(fuente(victima, JEFE, jefe), dano * Dificultad.dano(jefe));
    }

    /** Si se esta cubriendo con escudo, se le cae (como con un hacha: 5 s sin poder subirlo) y si 'ticks' es mas, mas. */
    public static void tirarEscudo(LivingEntity e, int ticks) {
        if (e instanceof Player p && p.isBlocking()) {
            p.disableShield(true);
            if (ticks > 100)
                p.getCooldowns().addCooldown(Items.SHIELD, ticks);
        }
    }

    /** Sube el tope de la vida maxima del juego (1024) para los jefes de raid. Se llama una vez al cargar el mod. */
    static void subirTopeDeVida() {
        try {
            ObfuscationReflectionHelper.setPrivateValue(RangedAttribute.class, (RangedAttribute) Attributes.MAX_HEALTH,
                    1_000_000.0, "f_22308_");
        } catch (RuntimeException ex) {
            Mipack.LOGGER.warn("[Mipack] no se pudo subir el tope de vida (los jefes quedan en 1024)", ex);
        }
    }
}
