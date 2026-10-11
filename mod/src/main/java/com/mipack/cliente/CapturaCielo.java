package com.mipack.cliente;

import com.mipack.Mipack;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
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

/**
 * Solo para revisar el cielo y las texturas sin jugar (./gradlew runClient -Pcaptura=cielo en una pantalla virtual):
 * arma una escenita con los bloques del paquete (dunas, arenisca, la pared del cañon en franjas de terracota, roca,
 * grava, pasto con un roble) y toma fotos a varias horas: manana, mediodia, atardecer, noche con auroras, amanecer y
 * con lluvia. Las fotos quedan en run/capturas_cielo/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaCielo {
    private static final boolean ACTIVA = "cielo".equals(System.getProperty("mipack.captura"));
    private static final int INICIO = 80, FASE = 70;
    // hora, clima, y las vistas: {nombre, yaw (0 = norte, 90 = este), pitch hacia arriba}
    private static final Object[][] FASES = {
            {1000, "clear", new Object[][]{{"manana_escena", 0f, 8f}, {"manana_este", 90f, 15f}}},
            {6000, "clear", new Object[][]{{"mediodia_escena", 0f, 8f}, {"mediodia_cielo", 30f, 55f}}},
            {12300, "clear", new Object[][]{{"atardecer_escena", -35f, 6f}, {"atardecer_oeste", -90f, 8f}}},
            {13200, "clear", new Object[][]{{"anochecer_oeste", -90f, 10f}, {"anochecer_norte", 0f, 15f}}},
            {18000, "clear", new Object[][]{{"noche_auroras", 0f, 22f}, {"noche_escena", 0f, 6f}, {"noche_cenit", 180f, 70f}}},
            {23200, "clear", new Object[][]{{"amanecer_este", 90f, 8f}, {"amanecer_escena", 40f, 6f}}},
            {6000, "rain", new Object[][]{{"lluvia_escena", 0f, 8f}}},
    };

    private static boolean creando;
    private static int ticks;
    private static BlockPos centro;

    private CapturaCielo() {
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_cielo",
                        new LevelSettings("captura_cielo", GameType.CREATIVE, false, Difficulty.PEACEFUL, true, new GameRules(),
                                WorldDataConfiguration.DEFAULT),
                        new WorldOptions(4321L, false, false),
                        r -> r.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(WorldPresets.FLAT).value().createWorldDimensions());
            }
            return;
        }
        MinecraftServer server = mc.getSingleplayerServer();
        if (mc.level == null || mc.player == null || server == null || mc.screen != null)
            return;
        ticks++;
        mc.options.hideGui = true;
        mc.player.getAbilities().flying = true;
        if (ticks == 20) {
            centro = mc.player.blockPosition();
            for (String c : escena(centro))
                comando(server, c);
        }
        if (ticks < INICIO || centro == null)
            return;
        int t = ticks - INICIO, fase = t / FASE, enFase = t % FASE;
        if (fase >= FASES.length) {
            mc.stop();
            return;
        }
        Object[] f = FASES[fase];
        Object[][] vistas = (Object[][]) f[2];
        if (enFase == 0) {
            comando(server, "time set " + f[0]);
            comando(server, "weather " + f[1]);
        }
        int cada = (FASE - 20) / vistas.length, k = Math.min(vistas.length - 1, Math.max(0, enFase - 20) / cada);
        Object[] v = vistas[k];
        Vec3 cam = new Vec3(centro.getX() + 0.5, centro.getY() + 4.5, centro.getZ() + 12.5);
        mirar(mc, cam, (Float) v[1], (Float) v[2]);
        if (enFase >= 20 && (enFase - 20) % cada == cada - 1)
            foto(mc, (String) v[0]);
    }

    /** La escenita: el norte es desierto con dunas, arenisca y la pared del cañon; el sur es pasto con un roble. */
    private static String[] escena(BlockPos c) {
        int x = c.getX(), y = c.getY(), z = c.getZ();
        java.util.List<String> l = new java.util.ArrayList<>(java.util.List.of(
                "weather clear", "gamerule doDaylightCycle false", "gamerule doWeatherCycle false",
                "gamerule doMobSpawning false", "kill @e[type=!player]"));
        l.add(f("fill %d %d %d %d %d %d minecraft:sand", x - 40, y - 1, z - 45, x + 40, y - 1, z - 3));
        l.add(f("fill %d %d %d %d %d %d minecraft:red_sand", x + 12, y - 1, z - 24, x + 24, y - 1, z - 12));
        for (int[] d : new int[][]{{-14, -16, 3, 2}, {-6, -22, 4, 3}, {16, -8, 3, 1}, {22, -20, 2, 2}})
            l.add(f("fill %d %d %d %d %d %d minecraft:sand", x + d[0] - d[2], y, z + d[1] - d[2], x + d[0] + d[2], y + d[3] - 1, z + d[1] + d[2]));
        String[] franjas = {"terracotta", "orange_terracotta", "yellow_terracotta", "white_terracotta", "red_terracotta",
                "orange_terracotta", "brown_terracotta", "light_gray_terracotta"};
        for (int i = 0; i < franjas.length; i++)
            l.add(f("fill %d %d %d %d %d %d minecraft:%s", x - 38, y + i * 2, z - 40, x + 38, y + i * 2 + 1, z - 34, franjas[i]));
        l.add(f("fill %d %d %d %d %d %d minecraft:sandstone", x + 6, y, z - 16, x + 8, y + 6, z - 14));
        l.add(f("fill %d %d %d %d %d %d minecraft:sandstone", x + 6, y + 7, z - 16, x + 12, y + 7, z - 14));
        l.add(f("fill %d %d %d %d %d %d minecraft:sandstone", x + 10, y, z - 16, x + 12, y + 6, z - 14));
        l.add(f("fill %d %d %d %d %d %d minecraft:stone", x - 12, y, z - 12, x - 8, y + 2, z - 8));
        l.add(f("fill %d %d %d %d %d %d minecraft:stone", x - 11, y + 3, z - 11, x - 9, y + 4, z - 9));
        l.add(f("fill %d %d %d %d %d %d minecraft:cobblestone", x - 14, y, z - 7, x - 7, y, z - 6));
        l.add(f("fill %d %d %d %d %d %d minecraft:gravel", x - 1, y - 1, z - 30, x + 1, y - 1, z + 6));
        l.add(f("fill %d %d %d %d %d %d minecraft:dirt", x + 8, y - 1, z + 2, x + 11, y - 1, z + 5));
        l.add(f("fill %d %d %d %d %d %d minecraft:oak_planks", x + 3, y, z + 1, x + 6, y, z + 4));
        l.add(f("fill %d %d %d %d %d %d minecraft:oak_leaves[persistent=true]", x - 9, y + 3, z - 1, x - 5, y + 6, z + 3));
        l.add(f("fill %d %d %d %d %d %d minecraft:oak_log", x - 7, y, z + 1, x - 7, y + 5, z + 1));
        return l.toArray(new String[0]);
    }

    private static String f(String formato, Object... args) {
        return String.format(formato, args);
    }

    private static void comando(MinecraftServer server, String c) {
        server.execute(() -> server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(), c));
    }

    private static void mirar(Minecraft mc, Vec3 cam, float yaw, float pitch) {
        // yaw del juego: 0 = sur, 180 = norte; aqui 0 = norte y 90 = este
        float yawJuego = Mth.wrapDegrees(yaw + 180f);
        mc.player.moveTo(cam.x, cam.y - mc.player.getEyeHeight(), cam.z, yawJuego, -pitch);
        mc.player.setYHeadRot(yawJuego);
        mc.player.setDeltaMovement(Vec3.ZERO);
    }

    private static void foto(Minecraft mc, String nombre) {
        try {
            Files.createDirectories(Path.of("capturas_cielo"));
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(Path.of("capturas_cielo", nombre + ".png"));
            }
            Mipack.LOGGER.info("[CapturaCielo] {}", nombre);
        } catch (IOException e) {
            Mipack.LOGGER.error("[CapturaCielo] no se pudo guardar {}", nombre, e);
        }
    }
}
