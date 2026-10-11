package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.entidad.CrackatosEntity;
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
import java.util.ArrayList;
import java.util.List;

/**
 * Solo para revisar el mod sin jugar (./gradlew runClient -Pcaptura=true en una pantalla virtual): crea un mundo
 * plano, construye una arena, invoca a Crackatos y toma fotos desde varios lados; luego lo pone a pelear contra un
 * husk y toma una foto cada tanto mientras la camara lo sigue. Las fotos quedan en run/capturas/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class Captura {
    private static final boolean ACTIVA = Boolean.getBoolean("mipack.captura");
    private static final int INICIO = 60, VISTAS_CADA = 25, PELEA_CADA = 10, FOTOS_PELEA = 90;
    // las vistas del jefe quieto: angulo alrededor (0 = de frente), distancia y altura de la camara
    private static final float[][] VISTAS = {{35, 17, 4}, {90, 17, 3}, {0, 15, 3}, {150, 18, 5}, {-60, 12, 1.5f}};

    private static boolean creando;
    private static int ticks;
    private static BlockPos centro;
    private static final List<String> notas = new ArrayList<>();

    private Captura() {
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura",
                        new LevelSettings("captura", GameType.CREATIVE, false, Difficulty.NORMAL, true, new GameRules(),
                                WorldDataConfiguration.DEFAULT),
                        new WorldOptions(1234L, false, false),
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
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            for (String c : new String[]{"time set 6000", "weather clear", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "kill @e[type=!player]",
                    String.format("fill %d %d %d %d %d %d minecraft:polished_deepslate", x - 20, y - 1, z - 20, x + 20, y - 1, z + 20),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 21, y - 1, z - 21, x + 21, y + 4, z - 21),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 21, y - 1, z + 21, x + 21, y + 4, z + 21),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 21, y - 1, z - 21, x - 21, y + 4, z + 21),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x + 21, y - 1, z - 21, x + 21, y + 4, z + 21),
                    String.format("summon mipack:crackatos %d %d %d {Rotation:[0f,0f]}", x, y, z)})
                comando(server, c);
        }
        if (ticks < INICIO || centro == null)
            return;
        CrackatosEntity jefe = mc.level.getEntitiesOfClass(CrackatosEntity.class, mc.player.getBoundingBox().inflate(80)).stream()
                .findFirst().orElse(null);
        int t = ticks - INICIO;
        int vista = t / VISTAS_CADA;
        if (vista < VISTAS.length) {
            // el jefe quieto, desde varios lados
            if (jefe == null)
                return;
            float[] v = VISTAS[vista];
            double a = Math.toRadians(v[0] + jefe.getYRot());
            Vec3 objetivo = jefe.position().add(0, 2.6, 0);
            Vec3 cam = jefe.position().add(-Math.sin(a) * v[1], v[2], Math.cos(a) * v[1]);
            mirar(mc, cam, objetivo);
            if (t % VISTAS_CADA == VISTAS_CADA - 1)
                foto(mc, String.format("vista_%d", vista), jefe);
            return;
        }
        int p = t - VISTAS.length * VISTAS_CADA;
        if (p == 0) {
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            comando(server, String.format("summon minecraft:husk %d %d %d {PersistenceRequired:1b,Health:400f,"
                    + "Attributes:[{Name:\"generic.max_health\",Base:400d}]}", x + 12, y, z - 12));
        }
        if (jefe != null) {                       // la camara le da vueltas despacio, cerca
            double a = Math.toRadians(40 + p * 0.5);
            Vec3 objetivo = jefe.position().add(0, 2.0, 0);
            Vec3 cam = jefe.position().add(-Math.sin(a) * 15, 7.5, Math.cos(a) * 15);
            mirar(mc, cam, objetivo);
        }
        if (p > 0 && p % PELEA_CADA == 0) {
            foto(mc, String.format("pelea_%03d", p / PELEA_CADA), jefe);
            if (p / PELEA_CADA >= FOTOS_PELEA) {
                try {
                    Files.write(Path.of("capturas", "notas.txt"), notas);
                } catch (IOException ignored) {
                }
                mc.stop();
            }
        }
    }

    private static void comando(MinecraftServer server, String c) {
        server.execute(() -> server.getCommands().performPrefixedCommand(
                server.createCommandSourceStack().withSuppressedOutput(), c));
    }

    private static void mirar(Minecraft mc, Vec3 cam, Vec3 objetivo) {
        Vec3 d = objetivo.subtract(cam);
        float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
        float pitch = (float) -(Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)) * Mth.RAD_TO_DEG);
        mc.player.moveTo(cam.x, cam.y - mc.player.getEyeHeight(), cam.z, yaw, pitch);
        mc.player.setYHeadRot(yaw);
        mc.player.setDeltaMovement(Vec3.ZERO);
    }

    private static void foto(Minecraft mc, String nombre, CrackatosEntity jefe) {
        try {
            Files.createDirectories(Path.of("capturas"));
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(Path.of("capturas", nombre + ".png"));
            }
            String estado = jefe == null ? "?" : jefe.getEstado() + " " + (int) jefe.getHealth();
            notas.add(nombre + " " + estado);
            Mipack.LOGGER.info("[Captura] {} {}", nombre, estado);
        } catch (IOException e) {
            Mipack.LOGGER.error("[Captura] no se pudo guardar {}", nombre, e);
        }
    }
}
