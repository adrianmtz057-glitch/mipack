package com.mipack.bichos;

import com.mipack.Mipack;
import com.mipack.bichos.BichosDatos.Especie;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.Item;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/** Los 36 bichos de Velkia: un tipo de entidad y un huevo por especie (sin aparicion natural todavia). */
public final class Bichos {
    public static final Map<String, RegistryObject<EntityType<Bicho>>> TIPOS = new LinkedHashMap<>();
    public static final Map<String, RegistryObject<Item>> HUEVOS = new LinkedHashMap<>();
    private static final Map<String, Especie> POR_ID = new HashMap<>();

    private Bichos() {
    }

    public static Especie especie(String id) {
        return POR_ID.get(id);
    }

    public static void registrar(DeferredRegister<EntityType<?>> entidades, DeferredRegister<Item> objetos) {
        for (Especie e : BichosDatos.TODAS) {
            POR_ID.put(e.id(), e);
            RegistryObject<EntityType<Bicho>> t = entidades.register(e.id(), () -> {
                EntityType.Builder<Bicho> b = EntityType.Builder.<Bicho>of((tipo, nivel) -> new Bicho(tipo, nivel, e),
                        e.conducta() == BichosDatos.Conducta.HOSTIL ? MobCategory.MONSTER : MobCategory.CREATURE)
                        .sized(e.ancho(), e.alto()).clientTrackingRange(10);
                if (e.fuego())
                    b.fireImmune();
                return b.build(Mipack.MODID + ":" + e.id());
            });
            TIPOS.put(e.id(), t);
            int h = e.id().hashCode();
            int fondo = 0xFF000000 | (h & 0x7F7F7F) + 0x202020, puntos = 0xFF000000 | ((h >>> 8) & 0xFFFFFF) | 0x404040;
            HUEVOS.put(e.id(), objetos.register(e.id() + "_spawn_egg", () -> new ForgeSpawnEggItem(t, fondo, puntos, new Item.Properties())));
        }
    }

    public static void atributos(EntityAttributeCreationEvent evento) {
        for (Especie e : BichosDatos.TODAS)
            evento.put(TIPOS.get(e.id()).get(), Bicho.atributos(e).build());
    }
}
