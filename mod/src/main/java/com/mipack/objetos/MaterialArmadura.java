package com.mipack.objetos;

import com.mipack.Mipack;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;

import java.util.function.Supplier;

/**
 * Los materiales de las armaduras de Velkia. Cada pieza da su armadura como en Minecraft (la pechera mas, las botas
 * menos). calor: lo que sofoca en el desierto (1 = nada; diamante 2, netherita 3); abrigo: cuanto protege del frio.
 */
public enum MaterialArmadura implements ArmorMaterial {
    //        modelo      dura  botas pant pech casco encant  calor  abrigo
    DESIERTO("desierto", 9, new int[]{1, 2, 3, 1}, 12, 0.85f, 0.0f, () -> Items.SANDSTONE, SoundEvents.ARMOR_EQUIP_LEATHER),
    PLUMAS("plumas", 7, new int[]{1, 3, 5, 2}, 25, 1.1f, 0.0f, () -> Items.FEATHER, SoundEvents.ARMOR_EQUIP_ELYTRA),
    QUITINA("quitina", 11, new int[]{2, 4, 5, 2}, 12, 1.25f, 0.0f, () -> ObjetosMipack.QUITINA.get(), SoundEvents.ARMOR_EQUIP_TURTLE),
    TORTUGA("tortuga", 18, new int[]{2, 5, 6, 2}, 9, 1.3f, 0.0f, () -> Items.SCUTE, SoundEvents.ARMOR_EQUIP_TURTLE),
    PELAJE("pelaje", 8, new int[]{1, 2, 3, 1}, 15, 2.2f, 1.0f, () -> ObjetosMipack.PELAJE_GRUESO.get(), SoundEvents.ARMOR_EQUIP_LEATHER);

    private static final int[] BASE = {13, 15, 16, 11};
    private final String modelo;
    private final int durabilidad;
    private final int[] defensa;
    private final int encantable;
    private final float calor, abrigo;
    private final Supplier<Item> reparar;
    private final SoundEvent sonido;

    MaterialArmadura(String modelo, int durabilidad, int[] defensa, int encantable, float calor, float abrigo,
                     Supplier<Item> reparar, SoundEvent sonido) {
        this.modelo = modelo;
        this.durabilidad = durabilidad;
        this.defensa = defensa;
        this.encantable = encantable;
        this.calor = calor;
        this.abrigo = abrigo;
        this.reparar = reparar;
        this.sonido = sonido;
    }

    public String modelo() {
        return modelo;
    }

    public float calor() {
        return calor;
    }

    public float abrigo() {
        return abrigo;
    }

    private static int indice(ArmorItem.Type t) {
        return switch (t) {
            case BOOTS -> 0;
            case LEGGINGS -> 1;
            case CHESTPLATE -> 2;
            case HELMET -> 3;
        };
    }

    @Override
    public int getDurabilityForType(ArmorItem.Type t) {
        return BASE[indice(t)] * durabilidad;
    }

    @Override
    public int getDefenseForType(ArmorItem.Type t) {
        return defensa[indice(t)];
    }

    @Override
    public int getEnchantmentValue() {
        return encantable;
    }

    @Override
    public SoundEvent getEquipSound() {
        return sonido;
    }

    @Override
    public Ingredient getRepairIngredient() {
        return Ingredient.of(reparar.get());
    }

    @Override
    public String getName() {
        return Mipack.MODID + ":" + modelo;
    }

    @Override
    public float getToughness() {
        return 0.0f;
    }

    @Override
    public float getKnockbackResistance() {
        return 0.0f;
    }
}
