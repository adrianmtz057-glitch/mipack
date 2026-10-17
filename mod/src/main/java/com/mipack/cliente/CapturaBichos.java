package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.bichos.BichosDatos;
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

import java.nio.file.Files;
import java.nio.file.Path;

/** Solo para revisar los 36 bichos sin jugar (./gradlew runClient -Pcaptura=bichos). Fotos en run/capturas_bichos/. */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaBichos {
    private static final boolean ACTIVA = "bichos".equals(System.getProperty("mipack.captura"));
    private static boolean creando;
    private static int ticks;
    private static BlockPos c;

    private CapturaBichos() {
    }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent e) {
        if (!ACTIVA || e.phase != TickEvent.Phase.END)
            return;
        Minecraft mc = Minecraft.getInstance();
        if (!creando) {
            if (mc.screen instanceof TitleScreen) {
                creando = true;
                mc.createWorldOpenFlows().createFreshLevel("captura_bichos",
                        new LevelSettings("captura_bichos", GameType.CREATIVE, false, Difficulty.PEACEFUL, true, new GameRules(), WorldDataConfiguration.DEFAULT),
                        new WorldOptions(7L, false, false),
                        r -> r.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(WorldPresets.FLAT).value().createWorldDimensions());
            }
            return;
        }
        MinecraftServer s = mc.getSingleplayerServer();
        if (mc.level == null || mc.player == null || s == null || mc.screen != null)
            return;
        ticks++;
        if (ticks == 20) {
            c = mc.player.blockPosition();
            comando(s, "time set 6000");
            comando(s, "gamerule doDaylightCycle false");
            comando(s, "gamerule doMobSpawning false");
            comando(s, "kill @e[type=!player]");
            int i = 0;
            for (BichosDatos.Especie b : BichosDatos.TODAS) {
                int x = c.getX() + (i % 9) * 4, z = c.getZ() + 6 + (i / 9) * 5;
                comando(s, String.format("summon mipack:%s %d %d %d {NoAI:1b,Rotation:[200f,0f]%s}", b.id(), x, c.getY(), z,
                        i % 9 == 8 ? ",Manchado:1b" : ""));
                i++;
            }
        }
        if (c == null)
            return;
        mc.options.hideGui = true;
        mc.player.getAbilities().flying = true;
        if (ticks > 60 && ticks < 200) {
            Vec3 cam = new Vec3(c.getX() + 16, c.getY() + 9, c.getZ() - 4), mira = new Vec3(c.getX() + 16, c.getY(), c.getZ() + 15);
            mirar(mc, cam, mira);
        }
        for (int fila = 0; fila < 4; fila++)
            if (ticks == 220 + fila * 40) {
                Vec3 mira = new Vec3(c.getX() + 16, c.getY() + 0.6, c.getZ() + 6 + fila * 5);
                mirar(mc, mira.add(0, 4.5, -9), mira);
            }
        if (ticks == 190)
            foto(mc, "todos");
        for (int fila = 0; fila < 4; fila++)
            if (ticks == 250 + fila * 40)
                foto(mc, "fila" + fila);
        if (ticks > 420)
            mc.stop();
    }

    private static void comando(MinecraftServer s, String k) {
        s.execute(() -> s.getCommands().performPrefixedCommand(s.createCommandSourceStack().withSuppressedOutput(), k));
    }

    private static void mirar(Minecraft mc, Vec3 cam, Vec3 objetivo) {
        Vec3 d = objetivo.subtract(cam);
        float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
        float pitch = (float) -(Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)) * Mth.RAD_TO_DEG);
        mc.player.moveTo(cam.x, cam.y - mc.player.getEyeHeight(), cam.z, yaw, pitch);
        mc.player.setYHeadRot(yaw);
        mc.player.setDeltaMovement(Vec3.ZERO);
    }

    private static void foto(Minecraft mc, String n) {
        try {
            Path p = Path.of("capturas_bichos");
            Files.createDirectories(p);
            try (NativeImage img = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
                img.writeToFile(p.resolve(n + ".png"));
            }
        } catch (Exception ex) {
            Mipack.LOGGER.error("[CapturaB] {}", n, ex);
        }
    }
}
