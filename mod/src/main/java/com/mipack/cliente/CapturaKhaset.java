package com.mipack.cliente;

import com.mipack.Mipack;
import com.mipack.khaset.EfectosKhaset;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.RedKhaset;
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
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
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
 * el altar (el cristal del sacrificio) y husks (en modo de prueba Khaset tambien caza mobs).
 * <ol>
 * <li>Khaset quieto desde varios lados y el altar de cerca.</li>
 * <li>La pelea siguiendolo; a la mitad de la vida (corona rota, serpientes) y al 15 % (guerreros calavera).</li>
 * <li>El jugador (de verdad, en supervivencia): derribado cerca de Khaset; lo agarra, sale la barra, se hacen los 3
 *     clics cuando el cursor pasa por lo dorado y se revisa que lo suelte (en el cliente tambien).</li>
 * <li>Otra vez agarrado, ahora con totem y sin zafarse: lo lleva al altar, lo acuesta (foto de lado) y el totem lo
 *     salva y lo suelta.</li>
 * <li>Las poses con jugadores de mentira (la del altar, encima de un altar, a lo largo de la piedra).</li>
 * </ol>
 * Fotos y notas en run/capturas_khaset/. No va en el jar.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CapturaKhaset {
    private static final boolean ACTIVA = "khaset".equals(System.getProperty("mipack.captura"));
    private static final Path CARPETA = Path.of("capturas_khaset");
    private static final int INICIO = 60, VISTAS_CADA = 25, PELEA_CADA = 8, FOTOS_PELEA = 45, FOTOS_FASE2 = 30, FOTOS_FASE3 = 25;
    private static final float[][] VISTAS = {{30, 26, 8}, {0, 24, 6}, {90, 24, 7}, {160, 26, 9}, {-40, 14, 9}, {15, 9, 8.5f}};

    private enum Paso { VISTAS, PELEA, AGARRE, SACRIFICIO, POSES, FIN }

    private static boolean creando;
    private static int ticks, enPaso, clics, fotosAltar, vioEn, fotoLuego = -1;
    private static Paso paso = Paso.VISTAS;
    private static BlockPos centro;
    private static boolean agarrado, vioBarra, soltado;
    private static int soltoEn;
    private static final List<String> notas = new ArrayList<>();

    private CapturaKhaset() {
    }

    private static void a(Paso p) {
        paso = p;
        enPaso = 0;
        Mipack.LOGGER.info("[CapturaK] paso {}", p);
        notas.add("== " + p);
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
        enPaso++;
        if (paso != Paso.AGARRE && paso != Paso.SACRIFICIO)
            mc.options.hideGui = true;
        if (paso == Paso.VISTAS || paso == Paso.PELEA || paso == Paso.POSES)
            mc.player.getAbilities().flying = true;
        if (ticks == 20) {
            centro = mc.player.blockPosition();
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            for (String c : new String[]{"time set 6000", "weather clear", "gamerule doDaylightCycle false",
                    "gamerule doWeatherCycle false", "gamerule doMobSpawning false", "gamerule doImmediateRespawn true",
                    "kill @e[type=!player]",
                    String.format("fill %d %d %d %d %d %d minecraft:polished_deepslate", x - 30, y - 1, z - 30, x + 30, y - 1, z + 30),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 31, y - 1, z - 31, x + 31, y + 4, z - 31),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 31, y - 1, z + 31, x + 31, y + 4, z + 31),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x - 31, y - 1, z - 31, x - 31, y + 4, z + 31),
                    String.format("fill %d %d %d %d %d %d minecraft:deepslate_bricks", x + 31, y - 1, z - 31, x + 31, y + 4, z + 31),
                    String.format("summon mipack:cristal_sacrificio %d %d %d {Rotation:[90f,0f]}", x - 16, y, z),
                    String.format("summon mipack:khaset %d %d %d {Rotation:[90f,0f],NoAI:1b}", x, y, z)})
                comando(server, c);
        }
        if (ticks < INICIO || centro == null) {
            enPaso = 0;
            return;
        }
        KhasetEntity k = mc.level.getEntitiesOfClass(KhasetEntity.class, mc.player.getBoundingBox().inflate(90)).stream()
                .filter(Entity::isAlive).findFirst().orElse(null);
        KhasetEntity ks = k == null ? null : server.overworld().getEntity(k.getUUID()) instanceof KhasetEntity e ? e : null;
        switch (paso) {
            case VISTAS -> vistas(mc, k);
            case PELEA -> pelea(mc, server, k, ks);
            case AGARRE -> agarre(mc, server, k, ks);
            case SACRIFICIO -> sacrificio(mc, server, k, ks);
            case POSES -> {
                if (enPaso == 1)
                    poses(mc, server);
                if (enPaso == 40)
                    foto(mc, "poses", null);
                if (enPaso == 41)
                    a(Paso.FIN);
            }
            case FIN -> {
                try {
                    Files.write(CARPETA.resolve("notas.txt"), notas);
                } catch (IOException ignored) {
                }
                mc.stop();
            }
        }
    }

    private static void vistas(Minecraft mc, KhasetEntity k) {
        if (k == null)
            return;
        int t = enPaso - 1;
        int vista = t / VISTAS_CADA;
        if (vista < VISTAS.length) {
            float[] v = VISTAS[vista];
            double a = Math.toRadians(v[0] + k.getYRot());
            Vec3 objetivo = k.position().add(0, v[2] > 8 ? 7.0 : 5.0, 0);
            Vec3 cam = k.position().add(-Math.sin(a) * v[1], v[2], Math.cos(a) * v[1]);
            mirar(mc, cam, objetivo);
            if (t % VISTAS_CADA == VISTAS_CADA - 1)
                foto(mc, String.format("vista_%d", vista), k);
            return;
        }
        // el altar de cerca, de lado y de tres cuartos
        Vec3 altar = Vec3.atBottomCenterOf(centro).add(-16, 0, 0);
        int u = t - VISTAS.length * VISTAS_CADA;
        if (u < 20)
            mirar(mc, altar.add(5.5, 2.6, 4.0), altar.add(0, 0.8, 0));
        else
            mirar(mc, altar.add(0.5, 2.2, 6.0), altar.add(0, 0.8, 0));
        if (u == 19)
            foto(mc, "altar_34", null);
        if (u == 39) {
            foto(mc, "altar_lado", null);
            a(Paso.PELEA);
        }
    }

    private static void pelea(Minecraft mc, MinecraftServer server, KhasetEntity k, KhasetEntity ks) {
        int p = enPaso;
        if (p == 1) {
            int x = centro.getX(), y = centro.getY(), z = centro.getZ();
            comando(server, "data merge entity @e[type=mipack:khaset,limit=1] {NoAI:0b}");
            for (int i = 0; i < 4; i++)
                comando(server, String.format("summon minecraft:husk %d %d %d {PersistenceRequired:1b,Health:600f,"
                        + "Attributes:[{Name:\"generic.max_health\",Base:600d}]}", x + 8 + 4 * i, y, z - 9 + 6 * i));
        }
        int fin1 = FOTOS_PELEA * PELEA_CADA, fin2 = fin1 + FOTOS_FASE2 * PELEA_CADA, fin3 = fin2 + FOTOS_FASE3 * PELEA_CADA;
        if (ks != null && (p == fin1 || p == fin2))
            server.execute(() -> ks.setHealth(ks.getMaxHealth() * (p == fin1 ? 0.45f : 0.15f)));
        if (k != null) {
            double a = Math.toRadians(30 + p * 0.6);
            Vec3 objetivo = k.position().add(0, 4.0, 0);
            Vec3 cam = k.position().add(-Math.sin(a) * 26, 13, Math.cos(a) * 26);
            mirar(mc, cam, objetivo);
        }
        if (p % PELEA_CADA == 0)
            foto(mc, String.format("pelea_%03d", p / PELEA_CADA), k);
        if (p >= fin3) {
            comando(server, "kill @e[type=minecraft:husk]");
            comando(server, "kill @e[type=mipack:guerrero_calavera]");
            comando(server, "kill @e[type=mipack:xiuhcoatl]");
            comando(server, "kill @e[type=mipack:khaset]");          // uno nuevo (fase 1) para el agarre y el altar
            comando(server, String.format("summon mipack:khaset %d %d %d {Rotation:[90f,0f]}", centro.getX() - 2,
                    centro.getY(), centro.getZ()));
            a(Paso.AGARRE);
        }
    }

    /** El jugador derribado junto a Khaset: lo agarra, sale la barra y se zafa con 3 aciertos. */
    private static void agarre(Minecraft mc, MinecraftServer server, KhasetEntity k, KhasetEntity ks) {
        if (enPaso < 80)
            return;                                                  // que termine de morir el de la pelea
        if (enPaso == 80) {
            mc.options.hideGui = false;
            mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            mc.player.getAbilities().flying = false;
            server.execute(() -> {
                ServerPlayer sp = server.getPlayerList().getPlayers().get(0);
                sp.setGameMode(GameType.SURVIVAL);
                sp.setHealth(sp.getMaxHealth());
                // que sus golpes no lo maten antes de agarrarlo (el sacrificio y el forcejeo atraviesan esto)
                sp.addEffect(new MobEffectInstance(net.minecraft.world.effect.MobEffects.DAMAGE_RESISTANCE, 4000, 4));
                if (ks != null) {
                    Vec3 frente = ks.position().add(Vec3.directionFromRotation(0, ks.getYRot()).scale(4));
                    sp.teleportTo(frente.x, ks.getY(), frente.z);
                    ks.setTarget(sp);
                }
                sp.addEffect(new MobEffectInstance(EfectosKhaset.DERRIBADO.get(), 200, 0));
            });
        }
        boolean ahora = mc.player.getVehicle() instanceof KhasetEntity;
        if (ahora && !agarrado) {
            agarrado = true;
            notas.add("agarrado en el tick " + enPaso);
        }
        RedKhaset.Barra b = BarraZafarse.estado();
        if (agarrado && b.activa()) {
            if (!vioBarra) {
                vioBarra = true;
                vioEn = enPaso;
            }
            if (enPaso == vioEn + 6)                             // la foto despues de que ya se dibujo la barra
                foto(mc, "barra_zafarse", k);
            float c = b.cursor(mc.level.getGameTime() + mc.getFrameTime());
            if (enPaso > vioEn + 8 && Math.abs(c - b.zona()) < b.ancho() * 0.3f && enPaso % 3 == 0 && clics < 3) {
                RedKhaset.CANAL.sendToServer(new RedKhaset.Clic(c));
                clics++;
                notas.add("clic " + clics + " en " + String.format("%.2f", c) + " (zona " + String.format("%.2f", b.zona()) + ")");
                if (clics == 2)
                    fotoLuego = enPaso + 3;                      // la barra con dos aciertos
            }
            if (enPaso == fotoLuego)
                foto(mc, "barra_dos_aciertos", k);
            if (clics > 0 && b.aciertos() < clics && enPaso % 3 == 1)
                clics = b.aciertos();                         // el servidor no lo conto: otra vez
        }
        if (agarrado && !ahora && !soltado) {
            soltado = true;
            soltoEn = enPaso;
            notas.add("SUELTO en el cliente en el tick " + enPaso + " (aciertos " + b.aciertos() + ")");
        }
        if (soltado && enPaso == soltoEn + 8)
            foto(mc, "zafado", k);
        if (soltado && enPaso > 0 && mc.player.getVehicle() == null && notas.stream().noneMatch(s -> s.startsWith("sigue suelto"))) {
            if (enPaso % 40 == 0)
                notas.add("sigue suelto: " + (mc.player.getVehicle() == null));
        }
        if ((soltado && enPaso > 480) || enPaso > 1400) {
            if (!soltado)
                notas.add("NO SE SOLTO (agarrado " + agarrado + ", barra " + vioBarra + ")");
            a(Paso.SACRIFICIO);
        }
    }

    /** Agarrado otra vez, con totem y sin zafarse: el altar y el totem. */
    private static void sacrificio(Minecraft mc, MinecraftServer server, KhasetEntity k, KhasetEntity ks) {
        if (enPaso == 1) {
            agarrado = soltado = false;
            server.execute(() -> {
                ServerPlayer sp = server.getPlayerList().getPlayers().get(0);
                sp.setHealth(sp.getMaxHealth());
                sp.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(Items.TOTEM_OF_UNDYING));
                if (ks != null) {
                    Vec3 frente = ks.position().add(Vec3.directionFromRotation(0, ks.getYRot()).scale(4));
                    sp.teleportTo(frente.x, ks.getY(), frente.z);
                    ks.setTarget(sp);
                }
                sp.addEffect(new MobEffectInstance(EfectosKhaset.DERRIBADO.get(), 200, 0));
            });
        }
        boolean ahora = mc.player.getVehicle() instanceof KhasetEntity;
        if (ahora && !agarrado) {
            agarrado = true;
            notas.add("agarrado otra vez en el tick " + enPaso);
        }
        if (ahora && k != null && k.presaEnAltar(mc.player) && fotosAltar < 3 && enPaso % 6 == 0) {
            mc.options.setCameraType(fotosAltar == 1 ? CameraType.THIRD_PERSON_FRONT : CameraType.THIRD_PERSON_BACK);
            foto(mc, "en_el_altar_" + fotosAltar, k);
            fotosAltar++;
        }
        if (agarrado && !ahora && !soltado) {
            soltado = true;
            mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            notas.add("suelto despues del sacrificio en el tick " + enPaso + " (vivo " + mc.player.isAlive() + ", totem "
                    + (k == null ? "?" : k.totems()) + ")");
        }
        if (soltado && enPaso % 20 == 0 && fotosAltar < 99) {
            foto(mc, "despues_del_totem", k);
            fotosAltar = 99;
        }
        if ((soltado && enPaso > 200) || enPaso > 1600) {
            if (!soltado)
                notas.add("NO TERMINO EL SACRIFICIO (agarrado " + agarrado + ")");
            server.execute(() -> server.getPlayerList().getPlayers().get(0).setGameMode(GameType.CREATIVE));
            mc.options.setCameraType(CameraType.FIRST_PERSON);
            comando(server, "kill @e[type=mipack:khaset]");
            a(Paso.POSES);
        }
    }

    /** Jugadores de mentira (solo en el cliente) en fila, cada uno con una pose; el del altar, encima de un altar. */
    private static void poses(Minecraft mc, MinecraftServer server) {
        Vec3 base = Vec3.atBottomCenterOf(centro).add(0, 0, 10);
        PosesJugador.Pose[] lista = {PosesJugador.Pose.NINGUNA, PosesJugador.Pose.AGARRADO, PosesJugador.Pose.DERRIBADO,
                PosesJugador.Pose.ATURDIDO, PosesJugador.Pose.HERIDO};
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
        // el altar (girado 30 grados, para ver que el cuerpo sigue a la piedra y no al jugador) con uno acostado
        Vec3 altar = base.add(6, 0, 0);
        comando(server, String.format("summon mipack:cristal_sacrificio %.1f %.1f %.1f {Rotation:[30f,0f]}", altar.x, altar.y, altar.z));
        RemotePlayer r = new RemotePlayer(mc.level, new GameProfile(UUID.randomUUID(), "altar"));
        r.moveTo(altar.x, altar.y + com.mipack.khaset.CristalSacrificio.ALTO_PIEDRA, altar.z, 180f, 0f);
        mc.level.addPlayer(-1100, r);
        PosesJugador.FORZADAS.put(r.getId(), PosesJugador.Pose.ALTAR);
        mirar(mc, base.add(1.5, 3.0, -9.0), base.add(1.5, 0.9, 0));
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
                    + String.format("%.2f", k.calor()) + (k.coronaRota() ? " corona rota" : "") + " ritmo "
                    + String.format("%.2f", k.ritmo());
            notas.add(nombre + " " + estado);
            Mipack.LOGGER.info("[CapturaK] {} {}", nombre, estado);
        } catch (IOException e) {
            Mipack.LOGGER.error("[CapturaK] no se pudo guardar {}", nombre, e);
        }
    }
}
