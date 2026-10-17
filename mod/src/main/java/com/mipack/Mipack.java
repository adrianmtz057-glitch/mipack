package com.mipack;

import com.mipack.bruma.BrumaEntity;
import com.mipack.entidad.CrackatosEntity;
import com.mipack.geo.FabricaMallas;
import com.mipack.entidad.Ola;
import com.mipack.entidad.PuaCayendo;
import com.mipack.khaset.AvisoKhaset;
import com.mipack.khaset.CristalSacrificio;
import com.mipack.khaset.DardoAtlatl;
import com.mipack.khaset.EfectosKhaset;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.ParticulasKhaset;
import com.mipack.khaset.RedKhaset;
import com.mipack.khaset.Xiuhcoatl;
import com.mipack.titanes.Titanes;
import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;
import org.slf4j.Logger;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Mipack: los jefes y criaturas de Velkia: Crackatos, la bestia de piedra amatista, Khaset, el dios del fuego
 * corrompido, y La Bruma negra (modelos y animaciones de GeckoLib generados con taller/ en el repo).
 */
@Mod(Mipack.MODID)
public class Mipack {
    public static final String MODID = "mipack";
    public static final Logger LOGGER = LogUtils.getLogger();
    /** Modo de prueba (-Dmipack.prueba=true): los jefes tambien atacan a otros mobs y cuentan en el log lo que hacen. */
    public static final boolean PRUEBA = Boolean.getBoolean("mipack.prueba") || "khaset".equals(System.getProperty("mipack.captura"))
            || "bruma".equals(System.getProperty("mipack.captura"))
            || System.getProperty("mipack.captura", "").startsWith("titanes");

    public static final DeferredRegister<EntityType<?>> ENTIDADES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, MODID);
    public static final DeferredRegister<Item> OBJETOS = DeferredRegister.create(ForgeRegistries.ITEMS, MODID);
    public static final DeferredRegister<CreativeModeTab> PESTANAS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    /** Crackatos: el modelo se dibuja 4.5 veces mas grande (mas que el Ender Dragon); la caja de golpes es la del cuerpo. */
    public static final RegistryObject<EntityType<CrackatosEntity>> CRACKATOS = ENTIDADES.register("crackatos",
            () -> EntityType.Builder.of(CrackatosEntity::new, MobCategory.MONSTER)
                    .sized(3.5f * CrackatosEntity.ESCALA, 2.75f * CrackatosEntity.ESCALA).fireImmune().clientTrackingRange(16).updateInterval(1)
                    .build(MODID + ":crackatos"));

    /** Los acaros de amatista que salen de la bruma de Crackatos en su fase 2 (el modelo del endermite, mas grande). */
    public static final RegistryObject<EntityType<com.mipack.entidad.AcaroAmatista>> ACARO = ENTIDADES.register("acaro_amatista",
            () -> EntityType.Builder.<com.mipack.entidad.AcaroAmatista>of(com.mipack.entidad.AcaroAmatista::new, MobCategory.MONSTER)
                    .sized(0.4f * 1.8f, 0.3f * 1.8f).clientTrackingRange(8)
                    .build(MODID + ":acaro_amatista"));

    /** Las puas de amatista que salen volando de su lomo y las que caen del cielo. */
    public static final RegistryObject<EntityType<PuaCayendo>> PUA = ENTIDADES.register("pua",
            () -> EntityType.Builder.<PuaCayendo>of(PuaCayendo::new, MobCategory.MISC)
                    .sized(0.8f, 1.6f).fireImmune().clientTrackingRange(10).updateInterval(1)
                    .build(MODID + ":pua"));

    /** Khaset: el modelo mide 3.7 bloques y se dibuja al triple (11 bloques); la caja de golpes es la del cuerpo flaco. */
    public static final RegistryObject<EntityType<KhasetEntity>> KHASET = ENTIDADES.register("khaset",
            () -> EntityType.Builder.of(KhasetEntity::new, MobCategory.MONSTER)
                    .sized(3.0f, 10.5f).fireImmune().clientTrackingRange(16).updateInterval(1)
                    .build(MODID + ":khaset"));

    /** El cristal del sacrificio: la caja de piedra tallada (2.75 x 1.2 bloques) con el cristal flotando arriba. */
    public static final RegistryObject<EntityType<CristalSacrificio>> CRISTAL = ENTIDADES.register("cristal_sacrificio",
            () -> EntityType.Builder.<CristalSacrificio>of(CristalSacrificio::new, MobCategory.MISC)
                    .sized(2.75f, 1.2f).fireImmune().clientTrackingRange(16).updateInterval(5)
                    .build(MODID + ":cristal_sacrificio"));

    public static final RegistryObject<EntityType<DardoAtlatl>> DARDO = ENTIDADES.register("dardo_atlatl",
            () -> EntityType.Builder.<DardoAtlatl>of(DardoAtlatl::new, MobCategory.MISC)
                    .sized(0.5f, 0.5f).clientTrackingRange(8).updateInterval(1)
                    .build(MODID + ":dardo_atlatl"));

    public static final RegistryObject<EntityType<Xiuhcoatl>> XIUHCOATL = ENTIDADES.register("xiuhcoatl",
            () -> EntityType.Builder.of(Xiuhcoatl::new, MobCategory.MONSTER)
                    .sized(2.2f, 1.6f).fireImmune().clientTrackingRange(10).updateInterval(1)
                    .build(MODID + ":xiuhcoatl"));

    /** Los guerreros calavera del Quinto Sol (la ultima fase de Khaset): el modelo del esqueleto con penacho. */
    public static final RegistryObject<EntityType<com.mipack.khaset.GuerreroCalavera>> GUERRERO = ENTIDADES.register("guerrero_calavera",
            () -> EntityType.Builder.<com.mipack.khaset.GuerreroCalavera>of(com.mipack.khaset.GuerreroCalavera::new, MobCategory.MONSTER)
                    .sized(0.6f, 1.99f).fireImmune().clientTrackingRange(8)
                    .build(MODID + ":guerrero_calavera"));

    public static final RegistryObject<EntityType<AvisoKhaset>> AVISO = ENTIDADES.register("aviso",
            () -> EntityType.Builder.<AvisoKhaset>of(AvisoKhaset::new, MobCategory.MISC)
                    .sized(0.5f, 0.1f).clientTrackingRange(10).updateInterval(20)
                    .build(MODID + ":aviso"));

    /** La Bruma: el modelo mide 1.85 bloques y se dibuja 3.2 veces (unos 6 bloques); flota, la caja es la del cuerpo. */
    public static final RegistryObject<EntityType<BrumaEntity>> BRUMA = ENTIDADES.register("bruma",
            () -> EntityType.Builder.of(BrumaEntity::new, MobCategory.MONSTER)
                    .sized(1.8f, 5.4f).clientTrackingRange(16).updateInterval(1)
                    .build(MODID + ":bruma"));

    public static final RegistryObject<Item> HUEVO_CRACKATOS = OBJETOS.register("crackatos_spawn_egg",
            () -> new ForgeSpawnEggItem(CRACKATOS, 0x231A31, 0x8A64CC, new Item.Properties()));
    public static final RegistryObject<Item> HUEVO_KHASET = OBJETOS.register("khaset_spawn_egg",
            () -> new ForgeSpawnEggItem(KHASET, 0x981C36, 0x22AA9C, new Item.Properties()));
    public static final RegistryObject<Item> HUEVO_BRUMA = OBJETOS.register("bruma_spawn_egg",
            () -> new ForgeSpawnEggItem(BRUMA, 0x0E0F11, 0x9A9384, new Item.Properties()));
    public static final RegistryObject<Item> HUEVO_ACARO = OBJETOS.register("acaro_amatista_spawn_egg",
            () -> new ForgeSpawnEggItem(ACARO, 0x3B2154, 0xC9A0FF, new Item.Properties()));
    public static final RegistryObject<Item> HUEVO_XIUHCOATL = OBJETOS.register("xiuhcoatl_spawn_egg",
            () -> new ForgeSpawnEggItem(XIUHCOATL, 0x1E8A7A, 0xF2A33A, new Item.Properties()));
    public static final RegistryObject<Item> HUEVO_GUERRERO = OBJETOS.register("guerrero_calavera_spawn_egg",
            () -> new ForgeSpawnEggItem(GUERRERO, 0xE8E2D0, 0x2A1C14, new Item.Properties()));
    public static final RegistryObject<Item> CRISTAL_ITEM = OBJETOS.register("cristal_sacrificio",
            () -> new CristalSacrificio.Objeto(new Item.Properties().stacksTo(1)));

    /** El macuahuitl de los guerreros calavera: un mazo de madera con navajas de obsidiana (a veces lo sueltan). */
    public static final RegistryObject<Item> MACUAHUITL = OBJETOS.register("macuahuitl",
            () -> new net.minecraft.world.item.SwordItem(net.minecraft.world.item.Tiers.STONE, 4, -2.8f, new Item.Properties()));

    public static final RegistryObject<CreativeModeTab> PESTANA = PESTANAS.register("mipack",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.mipack"))
                    .icon(() -> new ItemStack(HUEVO_CRACKATOS.get()))
                    .displayItems((params, out) -> {
                        out.accept(HUEVO_CRACKATOS.get());
                        out.accept(HUEVO_KHASET.get());
                        out.accept(HUEVO_BRUMA.get());
                        out.accept(HUEVO_ACARO.get());
                        out.accept(HUEVO_XIUHCOATL.get());
                        out.accept(HUEVO_GUERRERO.get());
                        out.accept(net.minecraft.world.item.Items.VEX_SPAWN_EGG);   // las almas en pena de la Bruma
                        for (var p : com.mipack.objetos.ObjetosMipack.POCIONES_PRUEBA)
                            out.accept(net.minecraft.world.item.alchemy.PotionUtils.setPotion(
                                    new ItemStack(net.minecraft.world.item.Items.POTION), p.get()));
                        out.accept(CRISTAL_ITEM.get());
                        out.accept(MACUAHUITL.get());
                    })
                    .build());

    public Mipack() {
        Golpes.subirTopeDeVida();
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        Titanes.registrar(ENTIDADES);
        ENTIDADES.register(bus);
        OBJETOS.register(bus);
        PESTANAS.register(bus);
        com.mipack.objetos.ObjetosMipack.registrar(bus);
        EfectosKhaset.EFECTOS.register(bus);
        com.mipack.entidad.EfectosCrackatos.EFECTOS.register(bus);
        SonidosMipack.SONIDOS.register(bus);
        ParticulasKhaset.PARTICULAS.register(bus);
        bus.addListener(this::preparar);
        bus.addListener(this::atributos);
        ModLoadingContext.get().registerConfig(ModConfig.Type.CLIENT, MipackConfig.CLIENTE);
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, com.mipack.agua.ConfigAgua.SPEC);
        // los modelos de mipack pueden traer mallas (GeckoLib solo dibuja cubos): ver geo/FabricaMallas
        GeckoLibUtil.addCustomBakedModelFactory(MODID, new FabricaMallas());
        MinecraftForge.EVENT_BUS.addListener(this::alEntrar);
        if (PRUEBA)
            LOGGER.info("[Mipack] modo de prueba: los jefes atacan tambien a otros mobs");
    }

    private void atributos(EntityAttributeCreationEvent event) {
        event.put(CRACKATOS.get(), CrackatosEntity.atributos().build());
        event.put(ACARO.get(), com.mipack.entidad.AcaroAmatista.atributos().build());
        event.put(KHASET.get(), KhasetEntity.atributos().build());
        event.put(BRUMA.get(), BrumaEntity.atributos().build());
        event.put(XIUHCOATL.get(), Xiuhcoatl.atributos().build());
        event.put(GUERRERO.get(), com.mipack.khaset.GuerreroCalavera.atributos().build());
        Titanes.atributos(event);
    }

    private void preparar(FMLCommonSetupEvent event) {
        event.enqueueWork(RedKhaset::registrar);
        event.enqueueWork(com.mipack.agua.RedAgua::registrar);
        event.enqueueWork(com.mipack.objetos.ObjetosMipack::preparar);
    }

    /** Los bloques de una ola que quedaron guardados (se cerro el mundo a media ola) no vuelven a aparecer. */
    private void alEntrar(EntityJoinLevelEvent event) {
        if (event.loadedFromDisk() && event.getEntity().getTags().contains(Ola.ETIQUETA))
            event.setCanceled(true);
    }
}
