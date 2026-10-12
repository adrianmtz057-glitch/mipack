package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.EfectosKhaset;
import com.mipack.khaset.KhasetEntity;
import com.mojang.authlib.GameProfile;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.player.RemotePlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
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
import java.util.UUID;

/**
 * Solo para revisar a Khaset sin jugar (./gradlew runClient -Pcaptura=khaset en una pantalla virtual): una arena con
 * el cristal del sacrificio y tres husks (en modo de prueba Khaset tambien caza mobs). Fotos de Khaset quieto desde
 * varios lados (que las mallas se dibujen), de la pelea siguiendolo, de la corona rota con la Xiuhcoatl y de las
 * poses del jugador (con jugadores de mentira, solo en el cliente). Quedan en run/capturas_khaset/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaKhaset {
    private static final boolean ACTIVA = "khaset".equals(System.getProperty("mipack.captura"));
    private static final Path CARPETA = Path.of("capturas_khaset");
    private static final int INICIO = 60, VISTAS_CADA = 25, PELEA_CADA = 6, FOTOS_PELEA = 70, FOTOS_FASE2 = 40;
    private static final float[][] VISTAS = {{30, 26, 8}, {0, 24, 6}, {90, 24, 7}, {160, 26, 9}, {-40, 14, 9}, {15, 9, 8.5f}};

    private static boolean creando;
    private static int ticks;
    private static BlockPos centro;
    private static final List<String> notas = new ArrayList<>();

    private CapturaKhaset() {
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_khaset",
                        new LevelSettings("captura_khaset", GameType.CREATIVE, false, Difficulty.NORMAL, true, new GameRules(),
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
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            for (String c : new String[]{"time set 6000", "weather clear", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "kill @e[type=!player]",
                    String.format("fill %d %d %d %d %d %d minecraft:polished_deepslate", x - 30, y - 1, z - 30, x + 30, y - 1, z + 30),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 31, y - 1, z - 31, x + 31, y + 4, z - 31),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 31, y - 1, z + 31, x + 31, y + 4, z + 31),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 31, y - 1, z - 31, x - 31, y + 4, z + 31),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x + 31, y - 1, z - 31, x + 31, y + 4, z + 31),
                    String.format("summon mipack:cristal_sacrificio %d %d %d {Rotation:[90f,0f]}", x - 16, y, z),
                    String.format("summon mipack:khaset %d %d %d {Rotation:[90f,0f],NoAI:1b}", x, y, z)})
                comando(server, c);
        }
        if (ticks < INICIO || centro == null)
            return;
        KhasetEntity k = mc.level.getEntitiesOfClass(KhasetEntity.class, mc.player.getBoundingBox().inflate(90)).stream()
                .findFirst().orElse(null);
        int t = ticks - INICIO;
        int vista = t / VISTAS_CADA;
        if (vista < VISTAS.length) {
            if (k == null)
                return;
            float[] v = VISTAS[vista];
            double a = Math.toRadians(v[0] + k.getYRot());
            Vec3 objetivo = k.position().add(0, v[2] > 8 ? 7.0 : 5.0, 0);
            Vec3 cam = k.position().add(-Math.sin(a) * v[1], v[2], Math.cos(a) * v[1]);
            mirar(mc, cam, objetivo);
            if (t % VISTAS_CADA == VISTAS_CADA - 1)
                foto(mc, String.format("vista_%d", vista), k);
            return;
        }
        int p = t - VISTAS.length * VISTAS_CADA;
        if (p == 0) {
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            comando(server, String.format("data merge entity @e[type=mipack:khaset,limit=1] {NoAI:0b}"));
            for (int i = 0; i < 3; i++)
                comando(server, String.format("summon minecraft:husk %d %d %d {PersistenceRequired:1b,Health:300f,"
                        + "Attributes:[{Name:\"generic.max_health\",Base:300d}]}", x + 8 + 4 * i, y, z - 6 + 6 * i));
        }
        int finPelea = FOTOS_PELEA * PELEA_CADA, finFase2 = finPelea + FOTOS_FASE2 * PELEA_CADA;
        if (p == finPelea && k != null) {                         // a la mitad de la vida: corona rota y serpiente
            Entity e = server.overworld().getEntity(k.getUUID());
            if (e instanceof KhasetEntity ks)
                server.execute(() -> ks.setHealth(ks.getMaxHealth() * 0.45f));
        }
        if (p < finFase2) {
            if (k != null) {
                double a = Math.toRadians(30 + p * 0.6);
                Vec3 objetivo = k.position().add(0, 4.0, 0);
                Vec3 cam = k.position().add(-Math.sin(a) * 24, 12, Math.cos(a) * 24);
                mirar(mc, cam, objetivo);
            }
            if (p > 0 && p % PELEA_CADA == 0)
                foto(mc, String.format("pelea_%03d", p / PELEA_CADA), k);
            return;
        }
        int q = p - finFase2;
        if (q == 0)
            poses(mc, server);
        if (q == 30)
            foto(mc, "poses", null);
        if (q == 31) {
            mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            server.execute(() -> {
                var sp = server.getPlayerList().getPlayers().get(0);
                sp.setGameMode(GameType.SURVIVAL);
                sp.addEffect(new MobEffectInstance(EfectosKhaset.DESANGRADO.get(), 200, 1));
            });
        }
        if (q == 45)
            foto(mc, "pantalla_desangrado", null);
        if (q == 46)
            server.execute(() -> server.getPlayerList().getPlayers().get(0)
                    .addEffect(new MobEffectInstance(EfectosKhaset.DESORIENTADO.get(), 200, 0)));
        if (q == 60)
            foto(mc, "pantalla_desorientado", null);
        if (q == 61) {
            try {
                Files.write(CARPETA.resolve("notas.txt"), notas);
            } catch (IOException ignored) {
            }
            mc.stop();
        }
    }

    /** Jugadores de mentira (solo en el cliente) en fila, cada uno con una pose, y la camara enfrente. */
    private static void poses(Minecraft mc, MinecraftServer server) {
        comando(server, "kill @e[type=!player]");
        Vec3 base = Vec3.atBottomCenterOf(centro).add(0, 0, 10);
        PosesJugador.Pose[] lista = {PosesJugador.Pose.NINGUNA, PosesJugador.Pose.AGARRADO, PosesJugador.Pose.DERRIBADO,
                PosesJugador.Pose.ATURDIDO, PosesJugador.Pose.HERIDO, PosesJugador.Pose.ALTAR};
        for (int i = 0; i < lista.length; i++) {
            RemotePlayer r = new RemotePlayer(mc.level, new GameProfile(UUID.randomUUID(), "pose" + i));
            double x = base.x - 5 + i * 2.0;
            double y = base.y + (lista[i] == PosesJugador.Pose.AGARRADO ? 1.0 : 0.0);
            r.moveTo(x, y, base.z, 180f, 0f);
            r.setYHeadRot(180f);
            r.yBodyRot = 180f;
            mc.level.addPlayer(-1000 - i, r);
            PosesJugador.FORZADAS.put(r.getId(), lista[i]);
        }
        mirar(mc, base.add(0, 2.2, -7.5), base.add(0, 0.9, 0));
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

    private static void foto(Minecraft mc, String nombre, KhasetEntity k) {
        try {
            Files.createDirectories(CARPETA);
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(CARPETA.resolve(nombre + ".png"));
            }
            String estado = k == null ? "-" : k.getEstado() + " vida " + (int) k.getHealth() + " calor "
                    + String.format("%.2f", k.calor()) + (k.coronaRota() ? " corona rota" : "");
            notas.add(nombre + " " + estado);
            Mipack.LOGGER.info("[CapturaK] {} {}", nombre, estado);
        } catch (IOException e) {
            Mipack.LOGGER.error("[CapturaK] no se pudo guardar {}", nombre, e);
        }
    }
}
