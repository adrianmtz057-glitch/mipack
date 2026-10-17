package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.bruma.BrumaEntity;
import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
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

/**
 * Solo para revisar a La Bruma sin jugar (./gradlew runClient -Pcaptura=bruma en una pantalla virtual): una arena con
 * antorchas, un pilar de piedra luminosa y husks (en modo de prueba tambien caza mobs).
 * <ol>
 * <li>Quieta (sin IA) de dia, desde varios lados y de cerca.</li>
 * <li>De noche, la pelea siguiendola (apaga las antorchas, zarpazo, agarrar y drenar, grito, jirones, bruma).</li>
 * <li>A la mitad de la vida: la fase 2 y sus almas en pena.</li>
 * <li>Junto a la piedra luminosa (corporea) y lejos (niebla).</li>
 * <li>Su muerte.</li>
 * </ol>
 * Fotos y notas en run/capturas_bruma/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaBruma {
    private static final boolean ACTIVA = "bruma".equals(System.getProperty("mipack.captura"));
    private static final Path CARPETA = Path.of("capturas_bruma");
    private static final int INICIO = 60, VISTAS_CADA = 25, PELEA_CADA = 8, FOTOS_PELEA = 40, FOTOS_FASE2 = 24, FOTOS_MUERTE = 10;
    // angulo alrededor (0 = de frente), distancia y altura de la camara; altura a la que mira
    private static final float[][] VISTAS = {{35, 13, 4, 3}, {0, 12, 3, 3}, {90, 12, 3, 3}, {180, 12, 3.5f, 3}, {-130, 12, 5, 3},
            {20, 6, 5.2f, 5}, {-50, 7, 3, 3.5f}};

    private enum Paso { VISTAS, PELEA, FASE2, LUZ, MUERTE, FIN }

    private static boolean creando;
    private static int ticks, enPaso, fotos;
    private static Paso paso = Paso.VISTAS;
    private static BlockPos centro;
    private static final List<String> notas = new ArrayList<>();

    private CapturaBruma() {
    }

    private static void a(Paso p) {
        paso = p;
        enPaso = 0;
        fotos = 0;
        notas.add("== " + p);
        Mipack.LOGGER.info("[CapturaB] paso {}", p);
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_bruma",
                        new LevelSettings("captura_bruma", GameType.CREATIVE, false, Difficulty.NORMAL, true, new GameRules(),
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
        enPaso++;
        mc.options.hideGui = true;
        mc.player.getAbilities().flying = true;
        if (ticks == 20) {
            centro = mc.player.blockPosition();
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            List<String> cs = new ArrayList<>(List.of("time set 6000", "weather clear", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "kill @e[type=!player]",
                    String.format("fill %d %d %d %d %d %d minecraft:polished_deepslate", x - 26, y - 1, z - 26, x + 26, y - 1, z + 26),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 27, y - 1, z - 27, x + 27, y + 4, z - 27),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 27, y - 1, z + 27, x + 27, y + 4, z + 27),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 27, y - 1, z - 27, x - 27, y + 4, z + 27),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x + 27, y - 1, z - 27, x + 27, y + 4, z + 27),
                    String.format("fill %d %d %d %d %d %d minecraft:glowstone", x + 18, y, z - 18, x + 19, y + 3, z - 17),
                    String.format("summon mipack:bruma %d %d %d {Rotation:[0f,0f],NoAI:1b}", x, y, z)));
            for (int i = -2; i <= 2; i++)                      // antorchas por la arena (las va a apagar)
                for (int j = -2; j <= 2; j++)
                    if ((i + j) % 2 == 0)
                        cs.add(String.format("setblock %d %d %d minecraft:torch", x + i * 8, y, z + j * 8 + 3));
            for (String c : cs)
                comando(server, c);
        }
        if (ticks < INICIO || centro == null) {
            enPaso = 0;
            return;
        }
        BrumaEntity b = mc.level.getEntitiesOfClass(BrumaEntity.class, mc.player.getBoundingBox().inflate(90)).stream()
                .filter(e -> !e.isRemoved()).findFirst().orElse(null);
        BrumaEntity bs = b == null ? null : server.overworld().getEntity(b.getUUID()) instanceof BrumaEntity e ? e : null;
        switch (paso) {
            case VISTAS -> {
                int v = enPaso / VISTAS_CADA;
                if (b == null)
                    return;
                if (v >= VISTAS.length) {
                    comando(server, "data merge entity @e[type=mipack:bruma,limit=1] {NoAI:0b}");
                    for (int i = 0; i < 2; i++)
                        comando(server, String.format("summon minecraft:husk %d %d %d {PersistenceRequired:1b,Health:600f,"
                                + "Attributes:[{Name:\"generic.max_health\",Base:600d}]}", centro.getX() + (i == 0 ? 10 : -9),
                                centro.getY(), centro.getZ() + (i == 0 ? -8 : 9)));
                    a(Paso.PELEA);
                    return;
                }
                float[] w = VISTAS[v];
                double ang = Math.toRadians(w[0] + b.getYRot());
                mirar(mc, b.position().add(-Math.sin(ang) * w[1], w[2], Math.cos(ang) * w[1]), b.position().add(0, w[3], 0));
                if (enPaso % VISTAS_CADA == VISTAS_CADA - 1)
                    foto(mc, "vista_" + v, b);
            }
            case PELEA, FASE2 -> {
                if (b != null) {                                // la camara le da vueltas despacio, de cerca y adentro de la arena
                    double ang = Math.toRadians(30 + ticks * 0.6);
                    Vec3 cam = b.position().add(-Math.sin(ang) * 12, 5, Math.cos(ang) * 12);
                    cam = new Vec3(Mth.clamp(cam.x, centro.getX() - 25, centro.getX() + 25), cam.y,
                            Mth.clamp(cam.z, centro.getZ() - 25, centro.getZ() + 25));
                    mirar(mc, cam, b.position().add(0, 3, 0));
                }
                if (enPaso % PELEA_CADA == 0) {
                    foto(mc, String.format("%s_%03d", paso == Paso.PELEA ? "pelea" : "fase2", ++fotos), b);
                    if (paso == Paso.PELEA && fotos >= FOTOS_PELEA) {
                        comando(server, "time set 18000");      // la fase 2, de noche
                        if (bs != null)
                            server.execute(() -> bs.setHealth(bs.getMaxHealth() * 0.45f));
                        a(Paso.FASE2);
                    } else if (paso == Paso.FASE2 && fotos >= FOTOS_FASE2) {
                        a(Paso.LUZ);
                    }
                }
            }
            case LUZ -> {
                if (enPaso == 1)
                    comando(server, "time set 6000");
                if (bs != null && enPaso < 40 && (bs.getEstado() == BrumaEntity.Estado.VIAJAR || bs.getEstado() == BrumaEntity.Estado.DISOLVERSE))
                    enPaso = 2;                                 // que acabe de viajar
                if (bs != null && enPaso >= 3 && enPaso <= 20)    // junto al pilar de piedra luminosa
                    server.execute(() -> bs.teleportTo(centro.getX() + 16.5, centro.getY(), centro.getZ() - 14.5));
                if (bs != null && enPaso >= 23 && enPaso <= 40)
                    server.execute(() -> bs.teleportTo(centro.getX() - 10.5, centro.getY(), centro.getZ() + 10.5));
                if (b != null)
                    mirar(mc, b.position().add(-8, 4.5, 8), b.position().add(0, 3, 0));
                if (enPaso == 20)
                    foto(mc, "luz_corporea", b);
                if (enPaso == 40)
                    foto(mc, "lejos_niebla", b);
                if (enPaso == 42) {
                    if (bs != null)
                        server.execute(bs::kill);
                    a(Paso.MUERTE);
                }
            }
            case MUERTE -> {
                if (b != null)
                    mirar(mc, b.position().add(-8, 4.5, 8), b.position().add(0, 3, 0));
                if (enPaso % 6 == 0 && fotos < FOTOS_MUERTE)
                    foto(mc, String.format("muerte_%02d", ++fotos), b);
                if (enPaso > 80) {
                    a(Paso.FIN);
                    try {
                        Files.write(CARPETA.resolve("notas.txt"), notas);
                    } catch (IOException ignored) {
                    }
                    mc.stop();
                }
            }
            default -> {
            }
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

    private static void foto(Minecraft mc, String nombre, BrumaEntity b) {
        try {
            Files.createDirectories(CARPETA);
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(CARPETA.resolve(nombre + ".png"));
            }
            String estado = b == null ? "?" : b.getEstado() + " vida " + (int) b.getHealth() + (b.fase2() ? " fase2" : "")
                    + (b.corporea() ? " corporea" : " niebla") + (b.isPassenger() || !b.getPassengers().isEmpty() ? " con presa" : "");
            notas.add(nombre + " " + estado);
            Mipack.LOGGER.info("[CapturaB] {} {}", nombre, estado);
        } catch (IOException e) {
            Mipack.LOGGER.error("[CapturaB] no se pudo guardar {}", nombre, e);
        }
    }

    @SuppressWarnings("unused")
    private static boolean vivo(Entity e) {
        return e != null && e.isAlive();
    }
}
