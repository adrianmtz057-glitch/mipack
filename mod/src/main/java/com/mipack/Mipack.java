package com.mipack;

import com.mipack.entidad.CrackatosEntity;
import com.mipack.entidad.PuaCayendo;
import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.slf4j.Logger;

/**
 * Mipack: los jefes y criaturas de Velkia. Por ahora Crackatos, la bestia de piedra amatista (modelo y animaciones
 * de GeckoLib generados con taller/ en el repo).
 */
@Mod(Mipack.MODID)
public class Mipack {
    public static final String MODID = "mipack";
    public static final Logger LOGGER = LogUtils.getLogger();
    /** Modo de prueba (-Dmipack.prueba=true): los jefes tambien atacan a otros mobs y cuentan en el log lo que hacen. */
    public static final boolean PRUEBA = Boolean.getBoolean("mipack.prueba");

    public static final DeferredRegister<EntityType<?>> ENTIDADES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, MODID);
    public static final DeferredRegister<Item> OBJETOS = DeferredRegister.create(ForgeRegistries.ITEMS, MODID);
    public static final DeferredRegister<CreativeModeTab> PESTANAS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    /** Crackatos: en el juego mide como el Ender Dragon (el render lo crece 2 veces); la caja de golpes es la del cuerpo. */
    public static final RegistryObject<EntityType<CrackatosEntity>> CRACKATOS = ENTIDADES.register("crackatos",
            () -> EntityType.Builder.of(CrackatosEntity::new, MobCategory.MONSTER)
                    .sized(6.0f, 5.5f).fireImmune().clientTrackingRange(16).updateInterval(1)
                    .build(MODID + ":crackatos"));

    /** Las puas de amatista que salen volando de su lomo y las que caen del cielo. */
    public static final RegistryObject<EntityType<PuaCayendo>> PUA = ENTIDADES.register("pua",
            () -> EntityType.Builder.<PuaCayendo>of(PuaCayendo::new, MobCategory.MISC)
                    .sized(0.8f, 1.6f).fireImmune().clientTrackingRange(10).updateInterval(1)
                    .build(MODID + ":pua"));

    public static final RegistryObject<Item> HUEVO_CRACKATOS = OBJETOS.register("crackatos_spawn_egg",
            () -> new ForgeSpawnEggItem(CRACKATOS, 0x231A31, 0x8A64CC, new Item.Properties()));

    public static final RegistryObject<CreativeModeTab> PESTANA = PESTANAS.register("mipack",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.mipack"))
                    .icon(() -> new ItemStack(HUEVO_CRACKATOS.get()))
                    .displayItems((params, out) -> out.accept(HUEVO_CRACKATOS.get()))
                    .build());

    public Mipack() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ENTIDADES.register(bus);
        OBJETOS.register(bus);
        PESTANAS.register(bus);
        bus.addListener(this::atributos);
        if (PRUEBA)
            LOGGER.info("[Mipack] modo de prueba: los jefes atacan tambien a otros mobs");
    }

    private void atributos(EntityAttributeCreationEvent event) {
        event.put(CRACKATOS.get(), CrackatosEntity.atributos().build());
    }
}
