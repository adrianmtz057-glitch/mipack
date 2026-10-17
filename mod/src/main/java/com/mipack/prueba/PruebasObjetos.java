package com.mipack.prueba;

import com.mipack.Mipack;
import com.mipack.agua.Agua;
import com.mipack.agua.Cantimplora;
import com.mipack.agua.SistemaAgua;
import com.mipack.objetos.EfectosArmadura;
import com.mipack.objetos.Lanzables;
import com.mipack.objetos.ObjetosMipack;
import com.mipack.objetos.Piramide;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionUtils;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraftforge.common.brewing.BrewingRecipeRegistry;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import net.minecraftforge.registries.ForgeRegistries;

/**
 * Las pruebas de los objetos de Velkia (./gradlew runGameTestServer): lo que sofoca cada armadura, la sed y el
 * desmayo, la ligereza y el nado de las armaduras, la cantimplora, las pociones, las recetas, la bomba de brasa, la
 * antorcha bajo el agua y la zona del pedazo de piramide.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasObjetos {
    private static final int PISO = 2;

    private static Player jugador(GameTestHelper h) {
        Player p = h.makeMockSurvivalPlayer();
        p.moveTo(h.absoluteVec(new net.minecraft.world.phys.Vec3(24.5, PISO + 1, 24.5)));
        CompoundTag siempre = p.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
        siempre.putInt("mipack_jugado", 1_000_000);                  // ya paso la gracia de los nuevos
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, siempre);
        return p;
    }

    private static void vestir(Player p, Item casco, Item pecho, Item pantalon, Item botas) {
        p.setItemSlot(EquipmentSlot.HEAD, casco == null ? ItemStack.EMPTY : new ItemStack(casco));
        p.setItemSlot(EquipmentSlot.CHEST, pecho == null ? ItemStack.EMPTY : new ItemStack(pecho));
        p.setItemSlot(EquipmentSlot.LEGS, pantalon == null ? ItemStack.EMPTY : new ItemStack(pantalon));
        p.setItemSlot(EquipmentSlot.FEET, botas == null ? ItemStack.EMPTY : new ItemStack(botas));
    }

    private static Item obj(String id) {
        return ForgeRegistries.ITEMS.getValue(new ResourceLocation(Mipack.MODID, id));
    }

    private static void cerca(GameTestHelper h, double a, double b, String que) {
        if (Math.abs(a - b) > 1e-3)
            h.fail(que + ": " + a + " en vez de " + b);
    }

    @GameTest(template = "arena", timeoutTicks = 40)
    public static void sofocacion(GameTestHelper h) {
        Player p = jugador(h);
        cerca(h, SistemaAgua.sofocacion(p), 1.0, "sin armadura");
        vestir(p, Items.DIAMOND_HELMET, Items.DIAMOND_CHESTPLATE, Items.DIAMOND_LEGGINGS, Items.DIAMOND_BOOTS);
        cerca(h, SistemaAgua.sofocacion(p), 2.0, "diamante");
        vestir(p, Items.NETHERITE_HELMET, Items.NETHERITE_CHESTPLATE, Items.NETHERITE_LEGGINGS, Items.NETHERITE_BOOTS);
        cerca(h, SistemaAgua.sofocacion(p), 3.0, "netherita");
        vestir(p, Items.DIAMOND_HELMET, null, null, null);
        cerca(h, SistemaAgua.sofocacion(p), 1.15, "solo el casco de diamante");
        vestir(p, obj("desierto_casco"), obj("desierto_pechera"), obj("desierto_pantalon"), obj("desierto_botas"));
        if (SistemaAgua.sofocacion(p) >= 1.0f)
            h.fail("la del desierto sofoca");
        vestir(p, obj("pelaje_casco"), obj("pelaje_pechera"), obj("pelaje_pantalon"), obj("pelaje_botas"));
        cerca(h, SistemaAgua.abrigo(p), 1.0, "abrigo del pelaje");
        h.succeed();
    }

    @GameTest(template = "arena", timeoutTicks = 400)
    public static void sed_y_desmayo(GameTestHelper h) {
        Player p = jugador(h);
        Agua.poner(p, 20.0f);
        p.tickCount = 20;
        SistemaAgua.tick(new TickEvent.PlayerTickEvent(TickEvent.Phase.END, p));
        float baja = 20.0f - Agua.agua(p);
        if (baja <= 0.0f || baja > 0.05f)
            h.fail("en un segundo bajo " + baja);
        Agua.poner(p, 0.0001f);
        SistemaAgua.tick(new TickEvent.PlayerTickEvent(TickEvent.Phase.END, p));
        if (!SistemaAgua.desmayado(p))
            h.fail("no se desmayo sin agua");
        if (p.getAttribute(Attributes.MOVEMENT_SPEED).getValue() > 1e-6)
            h.fail("desmayado se puede mover");
        for (int i = 0; i < 400 && SistemaAgua.desmayado(p); i++)
            SistemaAgua.tick(new TickEvent.PlayerTickEvent(TickEvent.Phase.END, p));
        if (SistemaAgua.desmayado(p) || Agua.agua(p) < 3.9f || p.getAttribute(Attributes.MOVEMENT_SPEED).getValue() < 0.05)
            h.fail("no desperto bien: agua " + Agua.agua(p));
        ItemStack botella = PotionUtils.setPotion(new ItemStack(Items.POTION), Potions.WATER);
        float antes = Agua.agua(p);
        net.minecraftforge.common.MinecraftForge.EVENT_BUS.post(
                new net.minecraftforge.event.entity.living.LivingEntityUseItemEvent.Finish(p, botella, 0, ItemStack.EMPTY));
        if (Agua.agua(p) < antes + 5.9f)
            h.fail("la botella de agua no dio agua");
        h.succeed();
    }

    @GameTest(template = "arena", timeoutTicks = 40)
    public static void armaduras_ligeras(GameTestHelper h) {
        Player p = jugador(h);
        vestir(p, obj("plumas_casco"), obj("plumas_pechera"), obj("plumas_pantalon"), obj("plumas_botas"));
        cerca(h, EfectosArmadura.ligereza(p), EfectosArmadura.LIGEREZA_PLUMAS, "plumas completa");
        vestir(p, null, null, null, obj("plumas_botas"));
        if (EfectosArmadura.ligereza(p) <= 0.0f)
            h.fail("con una sola pieza no se nota");
        vestir(p, obj("quitina_casco"), obj("quitina_pechera"), obj("quitina_pantalon"), obj("quitina_botas"));
        cerca(h, EfectosArmadura.ligereza(p), EfectosArmadura.LIGEREZA_QUITINA, "quitina completa");
        double base = p.getAttribute(Attributes.MOVEMENT_SPEED).getValue();
        p.tickCount = 5;
        EfectosArmadura.tick(new TickEvent.PlayerTickEvent(TickEvent.Phase.END, p));
        double con = p.getAttribute(Attributes.MOVEMENT_SPEED).getValue();
        if (con <= base)
            h.fail("la quitina no hace mas rapido: " + base + " -> " + con);
        vestir(p, null, obj("tortuga_pechera"), obj("tortuga_pantalon"), obj("tortuga_botas"));
        EfectosArmadura.tick(new TickEvent.PlayerTickEvent(TickEvent.Phase.END, p));
        if (p.getAttribute(net.minecraftforge.common.ForgeMod.SWIM_SPEED.get()).getValue() <= 1.0)
            h.fail("la de tortuga no hace nadar mas rapido");
        h.succeed();
    }

    @GameTest(template = "arena", timeoutTicks = 40)
    public static void cantimplora_y_pociones(GameTestHelper h) {
        Cantimplora c = (Cantimplora) ObjetosMipack.CANTIMPLORA.get();
        ItemStack s = new ItemStack(c);
        if (c.sorbos(s) != 0)
            h.fail("nueva deberia venir vacia");
        c.poner(s, 99);
        if (c.sorbos(s) != 3)
            h.fail("la normal lleva 3 sorbos, tiene " + c.sorbos(s));
        ItemStack torpe = PotionUtils.setPotion(new ItemStack(Items.POTION), Potions.AWKWARD);
        for (Item ingrediente : new Item[]{ObjetosMipack.COLA_LAGARTO.get(), ObjetosMipack.GLANDULA.get(), ObjetosMipack.BRANQUIA.get()})
            if (!BrewingRecipeRegistry.hasOutput(torpe, new ItemStack(ingrediente)))
                h.fail("no hay pocion con " + ingrediente);
        var recetas = h.getLevel().getServer().getRecipeManager();
        for (String r : new String[]{"daga_colmillo", "martillo_cuerno", "flecha_aguijon", "cantimplora", "escudo_escamas",
                "antorcha_grasa", "pedazo_piramide", "desierto_pechera", "plumas_botas", "tortuga_pechera", "pelaje_casco"})
            if (recetas.byKey(new ResourceLocation(Mipack.MODID, r)).isEmpty())
                h.fail("falta la receta " + r);
        h.succeed();
    }

    @GameTest(template = "arena", timeoutTicks = 200)
    public static void bomba_de_brasa(GameTestHelper h) {
        Zombie z = h.spawn(EntityType.ZOMBIE, new BlockPos(24, PISO, 24));
        z.setNoAi(true);
        Lanzables.Bomba b = new Lanzables.Bomba(ObjetosMipack.BOMBA.get(), h.getLevel());
        BlockPos arriba = h.absolutePos(new BlockPos(24, PISO + 4, 24));
        b.setPos(arriba.getX() + 0.5, arriba.getY(), arriba.getZ() + 0.5);
        b.setDeltaMovement(0, -0.5, 0);
        h.getLevel().addFreshEntity(b);
        h.succeedWhen(() -> {
            if (!z.isOnFire())
                h.fail("el zombie no se prendio");
            h.assertBlockPresent(Blocks.AIR, new BlockPos(24, PISO + 2, 24));
        });
    }

    @GameTest(template = "arena", timeoutTicks = 100)
    public static void antorcha_y_piramide(GameTestHelper h) {
        BlockPos pos = new BlockPos(20, PISO, 20);
        BlockState mojada = ObjetosMipack.ANTORCHA.get().defaultBlockState().setValue(BlockStateProperties.WATERLOGGED, true);
        h.setBlock(pos, mojada);
        h.setBlock(pos.east(), Blocks.WATER);
        BlockPos pir = new BlockPos(30, PISO, 30);
        h.setBlock(pir, ObjetosMipack.PIRAMIDE.get());
        h.runAfterDelay(40, () -> {
            h.assertBlockPresent(ObjetosMipack.ANTORCHA.get(), pos);
            if (!h.getLevel().getFluidState(h.absolutePos(pos)).isSource())
                h.fail("la antorcha no tiene agua adentro");
            if (!Piramide.protegido(h.getLevel(), h.absolutePos(pir.offset(10, 0, 10))))
                h.fail("la zona del pedazo de piramide no cubre 14 bloques");
            if (Piramide.protegido(h.getLevel(), h.absolutePos(pir.offset(40, 0, 0))))
                h.fail("la zona llega demasiado lejos");
            h.setBlock(pir, Blocks.AIR);
            if (Piramide.protegido(h.getLevel(), h.absolutePos(pir)))
                h.fail("al quitarla la zona sigue");
            h.succeed();
        });
    }
}
