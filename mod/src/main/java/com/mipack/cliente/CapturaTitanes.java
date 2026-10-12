package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.titanes.Titan;
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
 * Para revisar a los titanes y el motor de rutas sin jugar (./gradlew runClient -Pcaptura=titanes): en un mundo
 * plano se arma un estanque y un muro alto con un hueco; se lee el terreno (/titanes escanear), se crea el titan de un
 * lado del muro y se le manda al otro: tiene que pasar por el hueco. Fotos desde arriba del recorrido y de cerca (de
 * dia y de noche, para ver lo que brilla). Quedan en run/capturas_titanes/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaTitanes {
    private static final String QUE = System.getProperty("mipack.captura", "");
    private static final boolean ACTIVA = QUE.startsWith("titanes");
    private static final String TIPO = QUE.contains(":") ? QUE.substring(QUE.indexOf(':') + 1) : "candil";
    private static final Path CARPETA = Path.of("capturas_titanes");
    private static final int CREAR = 260, MANDAR = 300, RECORRIDO = 2400, CADA = 120;

    private static boolean creando;
    private static int ticks;
    private static BlockPos centro;
    private static final List<String> notas = new ArrayList<>();

    private CapturaTitanes() {
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_titanes",
                        new LevelSettings("captura_titanes", GameType.CREATIVE, false, Difficulty.PEACEFUL, true, new GameRules(),
                                WorldDataConfiguration.DEFAULT),
                        new WorldOptions(777L, false, false),
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
        mc.options.renderDistance().set(16);
        if (ticks == 20) {
            BlockPos b = mc.player.blockPosition();
            centro = new BlockPos(b.getX(), mc.level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                    b.getX(), b.getZ()), b.getZ());
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            for (String c : new String[]{"time set 6000", "weather clear", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "kill @e[type=!player]",
                    // el estanque donde empieza (dos de hondo)
                    String.format("fill %d %d %d %d %d %d minecraft:water", x - 70, y - 2, z - 20, x - 30, y - 1, z + 20),
                    // un muro de 14 de alto con un hueco de 40 en medio
                    String.format("fill %d %d %d %d %d %d minecraft:stone_bricks", x - 4, y, z - 90, x + 4, y + 14, z - 20),
                    String.format("fill %d %d %d %d %d %d minecraft:stone_bricks", x - 4, y, z + 20, x + 4, y + 14, z + 90),
                    // unas lomas del otro lado
                    String.format("fill %d %d %d %d %d %d minecraft:grass_block", x + 30, y, z - 50, x + 50, y + 2, z - 30),
                    String.format("fill %d %d %d %d %d %d minecraft:grass_block", x + 34, y + 3, z - 46, x + 46, y + 5, z - 34)})
                comando(server, c);
        }
        if (ticks == 60)
            comando(server, String.format("execute positioned %d %d %d run titanes escanear 176", centro.getX(), centro.getY(), centro.getZ()));
        if (ticks == CREAR)
            comando(server, String.format("execute positioned %d %d %d rotated 90 0 run titanes crear %s", centro.getX() - 50,
                    centro.getY(), centro.getZ(), TIPO));
        if (ticks == MANDAR)
            comando(server, String.format("titanes mandar 1 %d %d", centro.getX() + 70, centro.getZ() - 60));
        if (ticks < CREAR + 20 || centro == null)
            return;
        Titan t = mc.level.getEntitiesOfClass(Titan.class, mc.player.getBoundingBox().inflate(300)).stream().findFirst().orElse(null);
        int p = ticks - MANDAR;
        if (p >= 0 && p <= RECORRIDO) {
            // desde arriba, sobre toda la zona
            mirar(mc, Vec3.atCenterOf(centro).add(-8, 120, 1), Vec3.atCenterOf(centro).add(0, 0, -10));
            if (p % CADA == 0)
                foto(mc, String.format("arriba_%03d", p / CADA), t);
            return;
        }
        int q = ticks - MANDAR - RECORRIDO;
        float[][] vistas = {{40, 1.4f, 0.5f}, {0, 1.2f, 0.35f}, {120, 1.5f, 0.7f}, {-70, 1.1f, 0.3f}};
        int cada = 40;
        int v = q / cada;
        if (t != null && v < vistas.length * 2) {
            if (q == vistas.length * cada)
                comando(server, "time set 18000");
            float[] w = vistas[v % vistas.length];
            double lejos = t.tipo.ancho() * 1.5 * w[1] + 8;
            double a = Math.toRadians(w[0] + t.getYRot());
            Vec3 obj = t.position().add(0, t.tipo.alto() * 0.4, 0);
            mirar(mc, t.position().add(-Math.sin(a) * lejos, lejos * w[2] + 4, Math.cos(a) * lejos), obj);
            if (q % cada == cada - 1)
                foto(mc, String.format("cerca_%d%s", v % vistas.length, v >= vistas.length ? "_noche" : ""), t);
            return;
        }
        if (q > vistas.length * 2 * cada + 5) {
            try {
                Files.write(CARPETA.resolve("notas.txt"), notas);
            } catch (IOException ignored) {
            }
            mc.stop();
        }
    }

    private static void comando(MinecraftServer server, String c) {
        server.execute(() -> server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(), c));
    }

    private static void mirar(Minecraft mc, Vec3 cam, Vec3 objetivo) {
        Vec3 d = objetivo.subtract(cam);
        float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
        float pitch = (float) -(Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)) * Mth.RAD_TO_DEG);
        mc.player.moveTo(cam.x, cam.y - mc.player.getEyeHeight(), cam.z, yaw, pitch);
        mc.player.setYHeadRot(yaw);
        mc.player.setDeltaMovement(Vec3.ZERO);
    }

    private static void foto(Minecraft mc, String nombre, Titan t) {
        try {
            Files.createDirectories(CARPETA);
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(CARPETA.resolve(nombre + ".png"));
            }
            String estado = t == null ? "-" : String.format("%s en %.0f %.0f %.0f (%s)", t.getEstado(), t.getX(), t.getY(), t.getZ(),
                    t.tipo.id());
            notas.add(nombre + " " + estado);
            Mipack.LOGGER.info("[CapturaT] {} {}", nombre, estado);
        } catch (IOException e) {
            Mipack.LOGGER.error("[CapturaT] no se pudo guardar {}", nombre, e);
        }
    }
}
