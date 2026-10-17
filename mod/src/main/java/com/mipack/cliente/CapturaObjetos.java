package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.agua.Agua;
import com.mipack.agua.SistemaAgua;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Solo para revisar los objetos sin jugar (./gradlew runClient -Pcaptura=objetos en una pantalla virtual): las cinco
 * armaduras puestas en soportes, los escudos en las manos, la antorcha de grasa bajo el agua, el pedazo de piramide, y
 * la pantalla del jugador en el desierto (la barra de agua, la sofocacion y el desmayo). Fotos en
 * run/capturas_objetos/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaObjetos {
    private static final boolean ACTIVA = "objetos".equals(System.getProperty("mipack.captura"));
    private static final Path CARPETA = Path.of("capturas_objetos");
    private static final String[] SETS = {"desierto", "plumas", "quitina", "tortuga", "pelaje"};
    private static boolean creando;
    private static int ticks;
    private static BlockPos c;

    private CapturaObjetos() {
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_objetos",
                        new LevelSettings("captura_objetos", GameType.CREATIVE, false, Difficulty.PEACEFUL, true, new GameRules(),
                                WorldDataConfiguration.DEFAULT),
                        new WorldOptions(778L, false, false),
                        r -> r.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(WorldPresets.FLAT).value().createWorldDimensions());
            }
            return;
        }
        MinecraftServer server = mc.getSingleplayerServer();
        if (mc.level == null || mc.player == null || server == null || mc.screen != null)
            return;
        ticks++;
        if (ticks == 20) {
            c = mc.player.blockPosition();
            int x = c.getX(), y = c.getY(), z = c.getZ();
            List<String> cs = new ArrayList<>(List.of("time set 5000", "weather clear", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "kill @e[type=!player]",
                    String.format("fillbiome %d %d %d %d %d %d minecraft:desert", x - 14, y - 4, z - 14, x + 14, y + 12, z + 8),
                    String.format("fill %d %d %d %d %d %d minecraft:smooth_sandstone", x - 20, y - 1, z - 20, x + 20, y - 1, z + 20),
                    String.format("fill %d %d %d %d %d %d minecraft:cut_sandstone", x - 12, y, z + 6, x + 12, y + 5, z + 6),
                    "gamerule announceAdvancements false",
                    String.format("fill %d %d %d %d %d %d minecraft:sandstone", x + 7, y - 4, z - 11, x + 13, y - 4, z - 5),
                    String.format("fill %d %d %d %d %d %d minecraft:water", x + 8, y - 3, z - 10, x + 12, y - 1, z - 6),
                    String.format("setblock %d %d %d mipack:antorcha_grasa[waterlogged=true]", x + 10, y - 3, z - 8),
                    String.format("setblock %d %d %d mipack:antorcha_grasa[waterlogged=true]", x + 9, y - 3, z - 7),
                    String.format("setblock %d %d %d mipack:antorcha_grasa_pared[facing=west,waterlogged=true]", x + 12, y - 2, z - 8),
                    String.format("setblock %d %d %d mipack:pedazo_piramide", x - 9, y, z - 6)));
            for (int i = 0; i < SETS.length; i++) {
                String s = SETS[i];
                String casco = s.equals("tortuga") ? "minecraft:turtle_helmet" : "mipack:" + s + "_casco";
                String manos = i == 1 ? "HandItems:[{id:\"mipack:daga_colmillo\",Count:1b},{id:\"mipack:escudo_escamas\",Count:1b}],"
                        : i == 3 ? "HandItems:[{id:\"mipack:martillo_cuerno\",Count:1b},{id:\"mipack:escudo_caparazon\",Count:1b}],"
                        : i == 2 ? "HandItems:[{id:\"mipack:varita_revolthir\",Count:1b},{id:\"mipack:cantimplora\",Count:1b}]," : "";
                cs.add(String.format("summon minecraft:armor_stand %d %d %d {ShowArms:1b,NoBasePlate:1b,Rotation:[180f,0f],%s"
                                + "ArmorItems:[{id:\"mipack:%s_botas\",Count:1b},{id:\"mipack:%s_pantalon\",Count:1b},"
                                + "{id:\"mipack:%s_pechera\",Count:1b},{id:\"%s\",Count:1b}],Pose:{RightArm:[-20f,0f,10f],LeftArm:[-20f,0f,-10f]}}",
                        x - 8 + i * 4, y, z + 3, manos, s, s, s, casco));
            }
            for (String k : cs)
                comando(server, k);
        }
        if (c == null || ticks < 70)
            return;
        int t = ticks - 70;
        mc.player.getAbilities().flying = true;
        if (t < 200) {                                          // las armaduras en los soportes
            mc.options.hideGui = true;
            int v = t / 20;
            Vec3 objetivo = new Vec3(c.getX() + 0.5, c.getY() + 1.1, c.getZ() + 3.5);
            if (v == 0)
                mirar(mc, objetivo.add(-3, 2.5, -9), objetivo);
            else if (v <= 5)
                mirar(mc, new Vec3(c.getX() - 8 + (v - 1) * 4 + 0.5 - 1.2, c.getY() + 1.7, c.getZ() + 0.6), new Vec3(c.getX() - 8 + (v - 1) * 4 + 0.5, c.getY() + 1.15, c.getZ() + 3.5));
            else if (v == 6)
                mirar(mc, new Vec3(c.getX() + 3, c.getY() + 2.2, c.getZ() + 5.4), new Vec3(c.getX() - 2, c.getY() + 1.0, c.getZ() + 3.5));
            else if (v == 7)
                mirar(mc, new Vec3(c.getX() + 8.5, c.getY() - 0.2, c.getZ() - 9.5), new Vec3(c.getX() + 10.5, c.getY() - 2.6, c.getZ() - 7.5));
            else if (v == 8)
                mirar(mc, new Vec3(c.getX() - 7, c.getY() + 1.6, c.getZ() - 8.5), new Vec3(c.getX() - 8.5, c.getY() + 0.3, c.getZ() - 5.5));
            if (t % 20 == 19 && v <= 8)
                foto(mc, new String[]{"armaduras", "desierto", "plumas", "quitina", "tortuga", "pelaje", "espaldas", "antorcha_agua", "piramide"}[v]);
            return;
        }
        ServerPlayer sp = server.getPlayerList().getPlayer(mc.player.getUUID());
        if (sp == null)
            return;
        if (t == 200) {                                         // en supervivencia, en el desierto y de diamante
            mc.options.hideGui = false;
            comando(server, "gamemode survival @a");
            comando(server, "item replace entity @a armor.head with minecraft:diamond_helmet");
            comando(server, "item replace entity @a armor.chest with minecraft:diamond_chestplate");
            comando(server, "item replace entity @a armor.legs with minecraft:diamond_leggings");
            comando(server, "item replace entity @a armor.feet with minecraft:diamond_boots");
            comando(server, "item replace entity @a hotbar.0 with mipack:cantimplora_reforzada");
            server.execute(() -> {
                CompoundTag siempre = sp.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
                siempre.putInt("mipack_jugado", 1_000_000);
                sp.getPersistentData().put(Player.PERSISTED_NBT_TAG, siempre);
                sp.teleportTo(c.getX() + 0.5, c.getY(), c.getZ() - 2.5);
                Agua.poner(sp, 9.0f);
                SistemaAgua.avisar(sp);
            });
        }
        if (t > 200 && t < 260) {
            mc.player.setYRot(0f);
            mc.getToasts().clear();
        }
        if (t == 250) {
            foto(mc, "pantalla_sed");
            boolean desierto = sp.level().getBiome(sp.blockPosition()).is(net.minecraftforge.common.Tags.Biomes.IS_DESERT);
            Mipack.LOGGER.info("[CapturaO] desierto={} sofocacion={} efecto={} agua={}", desierto, SistemaAgua.sofocacion(sp),
                    sp.hasEffect(com.mipack.objetos.EfectosObjetos.SOFOCACION.get()), Agua.agua(sp));
        }
        if (t == 260) {
            server.execute(() -> {
                Agua.poner(sp, 0.001f);
                SistemaAgua.avisar(sp);
            });
            mc.gui.getChat().addMessage(Component.literal("<Amigo> ¿estás bien? jaja"));
        }
        if (t == 290)
            foto(mc, "desmayo_cerrando");
        if (t == 330)
            foto(mc, "desmayo_negro_con_chat");
        if (t == 490)
            foto(mc, "despierta");
        if (t > 500) {
            try {
                Files.write(CARPETA.resolve("notas.txt"), List.of("agua " + Agua.agua(sp)));
            } catch (IOException ignored) {
            }
            mc.stop();
        }
    }

    private static void comando(MinecraftServer server, String k) {
        server.execute(() -> server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(), k));
    }

    private static void mirar(Minecraft mc, Vec3 cam, Vec3 objetivo) {
        Vec3 d = objetivo.subtract(cam);
        float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
        float pitch = (float) -(Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)) * Mth.RAD_TO_DEG);
        mc.player.moveTo(cam.x, cam.y - mc.player.getEyeHeight(), cam.z, yaw, pitch);
        mc.player.setYHeadRot(yaw);
        mc.player.setDeltaMovement(Vec3.ZERO);
    }

    private static void foto(Minecraft mc, String nombre) {
        try {
            Files.createDirectories(CARPETA);
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(CARPETA.resolve(nombre + ".png"));
            }
            Mipack.LOGGER.info("[CapturaO] {}", nombre);
        } catch (IOException e) {
            Mipack.LOGGER.error("[CapturaO] no se pudo guardar {}", nombre, e);
        }
    }
}
