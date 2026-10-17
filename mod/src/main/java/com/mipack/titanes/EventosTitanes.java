package com.mipack.titanes;

import com.mipack.Mipack;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.level.ChunkEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Lo que mueve a los titanes desde afuera: cada chunk que carga se lee al mapa del terreno, cada tick avanza el
 * registro de titanes, y los comandos /titanes (crear, quitar, lista, ir, mandar, ruta, escanear, terreno).
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class EventosTitanes {
    private static final List<Escaneo> ESCANEOS = new ArrayList<>();

    private record Escaneo(ServerLevel nivel, ArrayDeque<ChunkPos> faltan, int total, CommandSourceStack quien) {
    }

    private EventosTitanes() {
    }

    @SubscribeEvent
    public static void chunk(ChunkEvent.Load evento) {
        if (evento.getLevel() instanceof ServerLevel sl && evento.getChunk() instanceof LevelChunk c)
            Terreno.de(sl).leerChunk(sl, c);
    }

    @SubscribeEvent
    public static void tick(TickEvent.LevelTickEvent evento) {
        if (evento.phase != TickEvent.Phase.END || !(evento.level instanceof ServerLevel sl))
            return;
        TitanesMundo.de(sl).tick(sl);
        for (Escaneo e : new ArrayList<>(ESCANEOS)) {
            if (e.nivel != sl)
                continue;
            for (int i = 0; i < 3 && !e.faltan.isEmpty(); i++) {
                ChunkPos p = e.faltan.poll();
                Terreno.de(sl).leerChunk(sl, sl.getChunk(p.x, p.z));
            }
            int hechos = e.total - e.faltan.size();
            if (e.faltan.isEmpty()) {
                ESCANEOS.remove(e);
                e.quien.sendSuccess(() -> Component.literal("Terreno leido: " + e.total + " chunks (" + Terreno.de(sl).conocidas()
                        + " celdas conocidas)"), true);
            } else if (hechos % 200 == 0) {
                e.quien.sendSuccess(() -> Component.literal("Leyendo terreno: " + hechos + " / " + e.total), false);
            }
        }
    }

    @SubscribeEvent
    public static void comandos(RegisterCommandsEvent evento) {
        evento.getDispatcher().register(Commands.literal("titanes").requires(s -> s.hasPermission(2))
                .then(Commands.literal("crear").then(Commands.argument("tipo", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(Titanes.tipos().keySet(), b))
                        .executes(c -> {
                            TipoTitan t = Titanes.tipo(StringArgumentType.getString(c, "tipo"));
                            if (t == null) {
                                c.getSource().sendFailure(Component.literal("No existe ese titan"));
                                return 0;
                            }
                            CommandSourceStack s = c.getSource();
                            TitanesMundo.Registro r = TitanesMundo.de(s.getLevel()).crear(s.getLevel(), t, s.getPosition(),
                                    s.getRotation().y);
                            s.sendSuccess(() -> Component.literal("Titan " + t.id() + " #" + r.id + " creado"), true);
                            return r.id;
                        })))
                .then(Commands.literal("quitar").then(Commands.argument("id", IntegerArgumentType.integer(1)).executes(c -> {
                    boolean ok = TitanesMundo.de(c.getSource().getLevel()).quitar(c.getSource().getLevel(), IntegerArgumentType.getInteger(c, "id"));
                    c.getSource().sendSuccess(() -> Component.literal(ok ? "Quitado" : "No existe"), true);
                    return ok ? 1 : 0;
                })))
                .then(Commands.literal("lista").executes(c -> {
                    ServerLevel sl = c.getSource().getLevel();
                    TitanesMundo m = TitanesMundo.de(sl);
                    for (TitanesMundo.Registro r : m.registros()) {
                        boolean visto = m.entidad(sl, r) != null;
                        String txt = String.format("#%d %s en %d %d %d %s, %s", r.id, r.tipo, (int) r.pos.x, (int) r.pos.y, (int) r.pos.z,
                                visto ? "(aqui)" : "(virtual)", r.act == null ? "pensando" : r.act.hacer().name().toLowerCase());
                        c.getSource().sendSuccess(() -> Component.literal(txt), false);
                    }
                    return m.registros().size();
                }))
                .then(Commands.literal("ir").then(Commands.argument("id", IntegerArgumentType.integer(1)).executes(c -> {
                    TitanesMundo.Registro r = TitanesMundo.de(c.getSource().getLevel()).registro(IntegerArgumentType.getInteger(c, "id"));
                    if (r == null || c.getSource().getPlayer() == null)
                        return 0;
                    c.getSource().getPlayer().teleportTo(r.pos.x + 20, r.pos.y + 25, r.pos.z + 20);
                    return 1;
                })))
                .then(Commands.literal("mandar").then(Commands.argument("id", IntegerArgumentType.integer(1))
                        .then(Commands.argument("x", IntegerArgumentType.integer()).then(Commands.argument("z", IntegerArgumentType.integer())
                                .executes(c -> {
                                    ServerLevel sl = c.getSource().getLevel();
                                    TitanesMundo m = TitanesMundo.de(sl);
                                    TitanesMundo.Registro r = m.registro(IntegerArgumentType.getInteger(c, "id"));
                                    if (r == null)
                                        return 0;
                                    Vec3 a = new Vec3(IntegerArgumentType.getInteger(c, "x"), 0, IntegerArgumentType.getInteger(c, "z"));
                                    Titan t = m.entidad(sl, r);
                                    boolean ok;
                                    if (t != null) {
                                        ok = t.mandar(a);
                                    } else {
                                        List<Vec3> cam = Rutas.buscar(Terreno.de(sl), Titanes.tipo(r.tipo).perfil(), r.pos, a, 60000);
                                        ok = !cam.isEmpty();
                                        if (ok) {
                                            r.camino = new ArrayList<>(cam);
                                            r.indice = Math.min(1, cam.size() - 1);
                                            r.act = new TipoTitan.Actividad(a, TipoTitan.Hacer.QUIETO, 200);
                                        }
                                    }
                                    boolean fin = ok;
                                    c.getSource().sendSuccess(() -> Component.literal(fin ? "En camino" : "No hay camino por ahi"), true);
                                    return ok ? 1 : 0;
                                })))))
                .then(Commands.literal("ruta").then(Commands.argument("id", IntegerArgumentType.integer(1)).executes(c -> {
                    ServerLevel sl = c.getSource().getLevel();
                    TitanesMundo.Registro r = TitanesMundo.de(sl).registro(IntegerArgumentType.getInteger(c, "id"));
                    if (r == null)
                        return 0;
                    Titan t = TitanesMundo.de(sl).entidad(sl, r);
                    List<Vec3> cam = t != null ? t.camino() : r.camino;
                    Vec3 a = r.pos;
                    for (Vec3 p : cam) {
                        int n = (int) (a.distanceTo(p) / 2) + 1;
                        for (int k = 0; k <= n; k++) {
                            Vec3 q = a.lerp(p, k / (double) n);
                            int y = sl.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING, (int) q.x, (int) q.z);
                            sl.sendParticles(ParticleTypes.END_ROD, q.x, y + 1.5, q.z, 1, 0, 0, 0, 0);
                        }
                        a = p;
                    }
                    c.getSource().sendSuccess(() -> Component.literal("Camino de " + cam.size() + " puntos"), false);
                    return cam.size();
                })))
                .then(Commands.literal("escanear").then(Commands.argument("radio", IntegerArgumentType.integer(16, 4096)).executes(c -> {
                    CommandSourceStack s = c.getSource();
                    int radio = IntegerArgumentType.getInteger(c, "radio");
                    ChunkPos centro = new ChunkPos(net.minecraft.core.BlockPos.containing(s.getPosition()));
                    int rc = radio / 16;
                    List<ChunkPos> lista = new ArrayList<>();
                    for (int i = -rc; i <= rc; i++)
                        for (int j = -rc; j <= rc; j++)
                            if (i * i + j * j <= rc * rc)
                                lista.add(new ChunkPos(centro.x + i, centro.z + j));
                    lista.sort(Comparator.comparingInt(p -> (p.x - centro.x) * (p.x - centro.x) + (p.z - centro.z) * (p.z - centro.z)));
                    ESCANEOS.add(new Escaneo(s.getLevel(), new ArrayDeque<>(lista), lista.size(), s));
                    s.sendSuccess(() -> Component.literal("Leyendo " + lista.size() + " chunks del terreno (de a poco)"), true);
                    return lista.size();
                })))
                .then(Commands.literal("terreno").executes(c -> {
                    int n = Terreno.de(c.getSource().getLevel()).conocidas();
                    c.getSource().sendSuccess(() -> Component.literal(n + " celdas de 8x8 conocidas (" + (n * 64L) + " bloques de piso)"), false);
                    return n;
                })));
    }
}
