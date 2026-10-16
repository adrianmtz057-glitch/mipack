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
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Fotos de cerca de una entidad quieta para revisar texturas (./gradlew runClient -Pcaptura=detalle:khaset): la
 * rodea a tres alturas (pies, cuerpo y cabeza) y, si la entidad tiene una segunda forma (Khaset con la corona rota,
 * Crackatos en su fase 2), la cambia con NBT y repite. Quedan en run/capturas_detalle/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaDetalle {
    private static final String PROP = System.getProperty("mipack.captura", "");
    private static final boolean ACTIVA = PROP.startsWith("detalle:");
    private static final String QUE = ACTIVA ? PROP.substring("detalle:".length()) : "";
    private static final Path CARPETA = Path.of("capturas_detalle");
    private static final int INICIO = 60, CADA = 12, ANGULOS = 8;
    private static final float[] ALTURAS = {0.12f, 0.5f, 0.85f};

    private static boolean creando;
    private static int ticks;
    private static BlockPos centro;

    private CapturaDetalle() {
    }

    /** NBT de mas al invocarla (con NBT, /summon no le da su equipo). */
    private static String extra() {
        return switch (QUE) {
            case "guerrero_calavera" -> ",HandItems:[{id:\"mipack:macuahuitl\",Count:1b},{}]";
            default -> "";
        };
    }

    /** NBT de la segunda forma (o null si no tiene). */
    private static String segunda() {
        return switch (QUE) {
            case "khaset" -> "{CoronaRota:1b}";
            case "crackatos" -> "{Fase2:1b}";
            default -> null;
        };
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent evento) {
        if (!ACTIVA || evento.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_detalle",
                        new LevelSettings("captura_detalle", GameType.CREATIVE, false, Difficulty.NORMAL, true, new GameRules(),
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
                    String.format("fill %d %d %d %d %d %d minecraft:smooth_stone", x - 20, y - 1, z - 20, x + 20, y - 1, z + 20),
                    String.format("summon mipack:%s %d %d %d {Rotation:[0f,0f],NoAI:1b,PersistenceRequired:1b%s}", QUE, x, y, z, extra())})
                comando(server, c);
        }
        if (ticks < INICIO || centro == null)
            return;
        Entity e = mc.level.getEntitiesOfClass(Entity.class, new AABB(centro).inflate(40),
                x -> net.minecraft.world.entity.EntityType.getKey(x.getType()).getPath().equals(QUE)).stream().findFirst().orElse(null);
        if (e == null)
            return;
        int t = ticks - INICIO;
        int porForma = ANGULOS * ALTURAS.length * CADA;
        int forma = t / porForma, u = t % porForma;
        if (forma == 1 && u == 0 && segunda() == null) {
            mc.stop();
            return;
        }
        if (forma >= 2) {
            mc.stop();
            return;
        }
        if (forma == 1 && u == 0)
            comando(server, String.format("data merge entity @e[type=mipack:%s,limit=1] %s", QUE, segunda()));
        int foto = u / CADA, angulo = foto % ANGULOS, altura = foto / ANGULOS;
        double alto = e.getBbHeight(), ancho = Math.max(e.getBbWidth(), alto * 0.45);
        double a = Math.toRadians(angulo * 360.0 / ANGULOS + e.getYRot());
        double dist = alto < 1 ? 1.2 : alto < 3 ? alto * 1.25 : Math.max(4.0, ancho * 1.25);   // los chicos, de cerca
        Vec3 objetivo = e.position().add(0, alto * ALTURAS[altura], 0);
        Vec3 cam = objetivo.add(-Math.sin(a) * dist, alto < 1 ? dist * 0.5 : alto * 0.08, Math.cos(a) * dist);   // a los chiquitos, desde arriba
        mirar(mc, cam, objetivo);
        if (u % CADA == CADA - 1)
            foto(mc, String.format("%s_f%d_h%d_a%d", QUE, forma, altura, angulo));
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

    private static void foto(Minecraft mc, String nombre) {
        try {
            Files.createDirectories(CARPETA);
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(CARPETA.resolve(nombre + ".png"));
            }
        } catch (IOException ex) {
            Mipack.LOGGER.error("[CapturaD] no se pudo guardar {}", nombre, ex);
        }
    }
}
