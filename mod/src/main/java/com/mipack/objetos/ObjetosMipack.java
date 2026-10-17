package com.mipack.objetos;

import com.mipack.Mipack;
import com.mipack.agua.Cantimplora;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.StandingAndWallBlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.Potion;
import net.minecraft.world.item.alchemy.PotionUtils;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraftforge.common.brewing.BrewingRecipeRegistry;
import net.minecraftforge.common.crafting.StrictNBTIngredient;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

/**
 * Los objetos de Velkia: los materiales que sueltan los animales, lo que se hace con ellos, las armaduras, la
 * cantimplora y las reliquias. Todos van en la pestana "Velkia: objetos".
 */
public final class ObjetosMipack {
    public static final DeferredRegister<Item> OBJETOS = DeferredRegister.create(ForgeRegistries.ITEMS, Mipack.MODID);
    public static final DeferredRegister<Potion> POCIONES = DeferredRegister.create(ForgeRegistries.POTIONS, Mipack.MODID);
    public static final DeferredRegister<CreativeModeTab> PESTANAS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, Mipack.MODID);
    public static final DeferredRegister<Block> BLOQUES = DeferredRegister.create(ForgeRegistries.BLOCKS, Mipack.MODID);
    public static final DeferredRegister<EntityType<?>> ENTIDADES = DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, Mipack.MODID);
    private static final List<RegistryObject<Item>> EN_PESTANA = new ArrayList<>();

    // ------------------------------------------------------------------ materiales de los animales
    public static final RegistryObject<Item> COLMILLO = material("colmillo");
    public static final RegistryObject<Item> AGUIJON = material("aguijon");
    public static final RegistryObject<Item> ESCAMAS = material("escamas");
    public static final RegistryObject<Item> CUERNO_PIEDRA = material("cuerno_piedra");
    public static final RegistryObject<Item> CAPARAZON = material("caparazon");
    public static final RegistryObject<Item> COLA_LAGARTO = material("cola_lagarto");
    public static final RegistryObject<Item> BRANQUIA = material("branquia");
    public static final RegistryObject<Item> CENIZA = material("ceniza");
    public static final RegistryObject<Item> BRASA = material("brasa");
    public static final RegistryObject<Item> PLUMA_NEGRA = material("pluma_negra");
    public static final RegistryObject<Item> MURA = material("mura");
    public static final RegistryObject<Item> SAL = material("sal");
    public static final RegistryObject<Item> SEMILLA_MUSGO = material("semilla_musgo");
    public static final RegistryObject<Item> GRASA = material("grasa");
    public static final RegistryObject<Item> PELAJE_GRUESO = material("pelaje_grueso");
    public static final RegistryObject<Item> QUITINA = material("quitina");
    public static final RegistryObject<Item> GLANDULA = material("glandula_salamandra");

    // ------------------------------------------------------------------ objetos
    static final ObjetosSimples.Material MAT_COLMILLO = new ObjetosSimples.Material(260, 6.0f, 1.5f, 2, 16, () -> COLMILLO);
    static final ObjetosSimples.Material MAT_CUERNO = new ObjetosSimples.Material(420, 4.0f, 3.0f, 2, 8, () -> CUERNO_PIEDRA);

    public static final RegistryObject<Item> DAGA = objeto("daga_colmillo", () -> new ObjetosSimples.Daga(MAT_COLMILLO, new Item.Properties()));
    public static final RegistryObject<Item> MARTILLO = objeto("martillo_cuerno", () -> new ObjetosSimples.Martillo(MAT_CUERNO, new Item.Properties()));
    public static final RegistryObject<Item> FLECHA_AGUIJON = objeto("flecha_aguijon", () -> new ObjetosSimples.FlechaAguijon(new Item.Properties()));
    public static final RegistryObject<Item> CARNE_SALADA = objeto("carne_salada", () -> new ObjetosSimples.Comida(new Item.Properties()
            .food(new FoodProperties.Builder().nutrition(9).saturationMod(0.95f).meat().build()), -1.0f, true));
    public static final RegistryObject<Item> PULPA_CACTUS = objeto("pulpa_cactus", () -> new ObjetosSimples.Comida(new Item.Properties()
            .food(new FoodProperties.Builder().nutrition(1).saturationMod(0.1f).alwaysEat().fast().build()), 3.0f, false));
    public static final RegistryObject<Item> FERTILIZANTE = objeto("fertilizante_musgo", () -> new ObjetosSimples.Fertilizante(new Item.Properties()));
    public static final RegistryObject<Item> RUNA_PIBBLE = objeto("runa_pibble", () -> new ObjetosSimples.Runa(new Item.Properties().stacksTo(16)));
    public static final RegistryObject<Item> VARITA_REVOLTHIR = objeto("varita_revolthir", () -> new ObjetosSimples.Varita(new Item.Properties().durability(96), true));
    public static final RegistryObject<Item> VARITA_CORRECTAR = objeto("varita_correctar", () -> new ObjetosSimples.Varita(new Item.Properties().durability(96), false));

    // ------------------------------------------------------------------ lanzables
    public static final RegistryObject<EntityType<Lanzables.Bomba>> BOMBA = ENTIDADES.register("bomba_brasa",
            () -> EntityType.Builder.<Lanzables.Bomba>of(Lanzables.Bomba::new, MobCategory.MISC).sized(0.3f, 0.3f)
                    .clientTrackingRange(4).updateInterval(10).build(Mipack.MODID + ":bomba_brasa"));
    public static final RegistryObject<EntityType<Lanzables.Plumas>> SENUELO = ENTIDADES.register("senuelo_pluma",
            () -> EntityType.Builder.<Lanzables.Plumas>of(Lanzables.Plumas::new, MobCategory.MISC).sized(0.3f, 0.3f)
                    .clientTrackingRange(4).updateInterval(10).build(Mipack.MODID + ":senuelo_pluma"));
    public static final RegistryObject<Item> BOMBA_BRASA = objeto("bomba_brasa", Lanzables.bomba());
    public static final RegistryObject<Item> SENUELO_PLUMA = objeto("senuelo_pluma", Lanzables.senuelo());

    // ------------------------------------------------------------------ escudos, cantimploras
    public static final RegistryObject<Item> ESCUDO_ESCAMAS = objeto("escudo_escamas",
            () -> new Escudo(new Item.Properties().durability(560), "escudo_escamas", false, () -> ESCAMAS.get()));
    public static final RegistryObject<Item> ESCUDO_CAPARAZON = objeto("escudo_caparazon",
            () -> new Escudo(new Item.Properties().durability(260), "escudo_caparazon", true, () -> CAPARAZON.get()));
    public static final RegistryObject<Item> CANTIMPLORA = objeto("cantimplora", () -> new Cantimplora(new Item.Properties(), 3));
    public static final RegistryObject<Item> CANTIMPLORA_REFORZADA = objeto("cantimplora_reforzada", () -> new Cantimplora(new Item.Properties(), 5));

    // ------------------------------------------------------------------ bloques
    public static final RegistryObject<Block> ANTORCHA = BLOQUES.register("antorcha_grasa",
            () -> new Antorcha.Parada(BlockBehaviour.Properties.copy(Blocks.TORCH).lightLevel(s -> 15)));
    public static final RegistryObject<Block> ANTORCHA_PARED = BLOQUES.register("antorcha_grasa_pared",
            () -> new Antorcha.Pared(BlockBehaviour.Properties.copy(Blocks.WALL_TORCH).lightLevel(s -> 15).lootFrom(ANTORCHA)));
    public static final RegistryObject<Item> ANTORCHA_ITEM = objeto("antorcha_grasa",
            () -> new StandingAndWallBlockItem(ANTORCHA.get(), ANTORCHA_PARED.get(), new Item.Properties(), Direction.DOWN));
    public static final RegistryObject<Block> PIRAMIDE = BLOQUES.register("pedazo_piramide",
            () -> new Piramide.Bloque(BlockBehaviour.Properties.copy(Blocks.SANDSTONE).noOcclusion().lightLevel(s -> 6)));
    public static final RegistryObject<Item> PEDAZO_PIRAMIDE = objeto("pedazo_piramide",
            () -> new Piramide.Objeto(PIRAMIDE.get(), new Item.Properties().stacksTo(1)));

    // ------------------------------------------------------------------ armaduras
    public static final List<RegistryObject<Item>> ARMADURAS = new ArrayList<>();

    static {
        for (MaterialArmadura m : MaterialArmadura.values()) {
            for (ArmorItem.Type t : new ArmorItem.Type[]{ArmorItem.Type.HELMET, ArmorItem.Type.CHESTPLATE, ArmorItem.Type.LEGGINGS, ArmorItem.Type.BOOTS}) {
                if (m == MaterialArmadura.TORTUGA && t == ArmorItem.Type.HELMET)
                    continue;                                   // el casco de tortuga es el de Minecraft
                String pieza = switch (t) {
                    case HELMET -> "casco";
                    case CHESTPLATE -> "pechera";
                    case LEGGINGS -> "pantalon";
                    case BOOTS -> "botas";
                };
                ARMADURAS.add(objeto(m.modelo() + "_" + pieza, () -> new ArmaduraMipack(m, t, new Item.Properties())));
            }
        }
    }

    // ------------------------------------------------------------------ pociones
    public static final RegistryObject<Potion> POCION_BRANQUIAS = POCIONES.register("branquias",
            () -> new Potion("branquias", new MobEffectInstance(EfectosObjetos.BRANQUIAS.get(), 3600)));
    public static final RegistryObject<Potion> POCION_BRANQUIAS_LARGA = POCIONES.register("branquias_larga",
            () -> new Potion("branquias", new MobEffectInstance(EfectosObjetos.BRANQUIAS.get(), 9600)));

    /** Pociones para probar cada efecto del mod (solo en el creativo: no se preparan). */
    public static final List<RegistryObject<Potion>> POCIONES_PRUEBA = new ArrayList<>();

    static {
        prueba("desangrado", () -> com.mipack.khaset.EfectosKhaset.DESANGRADO.get(), 2);
        prueba("derribado", () -> com.mipack.khaset.EfectosKhaset.DERRIBADO.get(), 0);
        prueba("aturdido", () -> com.mipack.khaset.EfectosKhaset.ATURDIDO.get(), 0);
        prueba("desorientado", () -> com.mipack.khaset.EfectosKhaset.DESORIENTADO.get(), 0);
        prueba("esquirlas", () -> com.mipack.entidad.EfectosCrackatos.ESQUIRLAS.get(), 2);
        prueba("sofocacion", () -> EfectosObjetos.SOFOCACION.get(), 0);
        prueba("frio", () -> EfectosObjetos.FRIO.get(), 0);
    }

    private static void prueba(String nombre, Supplier<net.minecraft.world.effect.MobEffect> efecto, int nivel) {
        POCIONES_PRUEBA.add(POCIONES.register("prueba_" + nombre,
                () -> new Potion("prueba_" + nombre, new MobEffectInstance(efecto.get(), 400, nivel))));
    }

    public static final RegistryObject<CreativeModeTab> PESTANA = PESTANAS.register("objetos",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.mipack.objetos"))
                    .icon(() -> new ItemStack(COLMILLO.get()))
                    .withTabsBefore(Mipack.PESTANA.getKey())
                    .displayItems((params, out) -> {
                        for (RegistryObject<Item> o : EN_PESTANA)
                            out.accept(o.get());
                        out.accept(PotionUtils.setPotion(new ItemStack(Items.POTION), POCION_BRANQUIAS.get()));
                        out.accept(PotionUtils.setPotion(new ItemStack(Items.SPLASH_POTION), POCION_BRANQUIAS.get()));
                    })
                    .build());

    private ObjetosMipack() {
    }

    static RegistryObject<Item> material(String nombre) {
        return objeto(nombre, () -> new Item(new Item.Properties()));
    }

    public static <T extends Item> RegistryObject<Item> objeto(String nombre, Supplier<T> fabrica) {
        RegistryObject<Item> o = OBJETOS.register(nombre, fabrica);
        EN_PESTANA.add(o);
        return o;
    }

    public static void registrar(IEventBus bus) {
        BLOQUES.register(bus);
        ENTIDADES.register(bus);
        OBJETOS.register(bus);
        POCIONES.register(bus);
        PESTANAS.register(bus);
        EfectosObjetos.EFECTOS.register(bus);
    }

    /** Las recetas del soporte para pociones (se llama en el common setup). */
    public static void preparar() {
        mezcla(Potions.AWKWARD, COLA_LAGARTO.get(), Potions.REGENERATION);
        mezcla(Potions.AWKWARD, GLANDULA.get(), Potions.FIRE_RESISTANCE);
        mezcla(Potions.AWKWARD, BRANQUIA.get(), POCION_BRANQUIAS.get());
        mezcla(POCION_BRANQUIAS.get(), Items.REDSTONE, POCION_BRANQUIAS_LARGA.get());
    }

    private static void mezcla(Potion de, Item con, Potion a) {
        for (Item frasco : new Item[]{Items.POTION, Items.SPLASH_POTION, Items.LINGERING_POTION}) {
            BrewingRecipeRegistry.addRecipe(StrictNBTIngredient.of(PotionUtils.setPotion(new ItemStack(frasco), de)),
                    Ingredient.of(con), PotionUtils.setPotion(new ItemStack(frasco), a));
        }
    }
}
