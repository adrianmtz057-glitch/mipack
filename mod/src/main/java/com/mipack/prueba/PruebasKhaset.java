package com.mipack.prueba;

import com.mipack.Dificultad;
import com.mipack.Mipack;
import com.mipack.khaset.CristalSacrificio;
import com.mipack.khaset.DardoAtlatl;
import com.mipack.khaset.KhasetEntity;
import com.mipack.khaset.KhasetEntity.Estado;
import com.mipack.khaset.Xiuhcoatl;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Set;

/**
 * La pelea de prueba de Khaset (./gradlew runGameTestServer): en la arena de 49x49, con el cristal del sacrificio de
 * un lado y tres husks aguantadores (en modo de prueba Khaset tambien caza mobs). Primero tiene que hacer su
 * repertorio, repartir el foco entre los husks, pisar con la presa en la mano y sacrificar a alguien en el cristal
 * (el calor sube); luego los husks traen totem (el totem salva del sacrificio y el los suelta) y se le baja a la
 * mitad de la vida: rompe la corona, invoca varias Xiuhcoatl; se le pega de frente hasta que se pone en guardia y
 * contraataca; despues al 15 %: el Quinto Sol saca guerreros calavera. Al final se le mata y los guerreros se deshacen.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasKhaset {
    private static final Set<Estado> FASE_1 = EnumSet.of(Estado.CAMINAR, Estado.TAJOS, Estado.SALTO, Estado.DARDO,
            Estado.SILBATO, Estado.AGARRAR, Estado.CARGAR, Estado.SACRIFICIO);
    private static final int PISO = 2;

    private static final class Pelea {
        final List<Husk> husks = new ArrayList<>();
        Estado antes = Estado.QUIETO;
        boolean mitad, golpes, totems;
        int dardos, serpientes;
        long esperaMinima = Long.MAX_VALUE;                       // lo menos que tardo en empezar a sacrificar desde que agarro
    }

    @GameTest(template = "arena", timeoutTicks = 30000)
    public static void pelea(GameTestHelper h) {
        var server = h.getLevel().getServer();                    // el comando: lo cambia y se guarda
        for (String nivel : new String[]{"hardcore", "easy", "normal"}) {
            server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(), "khaset difficult " + nivel);
            if (!Dificultad.de(h.getLevel(), Dificultad.Jefe.KHASET).nombre().equals(nivel))
                throw new GameTestAssertException("/khaset difficult " + nivel + " no cambio la dificultad");
        }
        KhasetEntity k = h.spawn(Mipack.KHASET.get(), new BlockPos(30, PISO, 24));
        CristalSacrificio cristal = h.spawn(Mipack.CRISTAL.get(), new BlockPos(8, PISO, 24));
        Pelea p = new Pelea();
        AABB arena = new AABB(h.absolutePos(new BlockPos(1, PISO, 1)), h.absolutePos(new BlockPos(48, PISO + 9, 48)));
        h.onEachTick(() -> {
            if (k.isRemoved() || k.isDeadOrDying())
                return;
            p.husks.removeIf(x -> !x.isAlive());
            while (p.husks.size() < 3) {
                Husk x = h.spawn(EntityType.HUSK, new BlockPos(18 + h.getLevel().random.nextInt(24), PISO, 6 + h.getLevel().random.nextInt(36)));
                x.getAttribute(Attributes.MAX_HEALTH).setBaseValue(300.0);
                x.setHealth(300f);
                x.setPersistenceRequired();
                if (p.totems)
                    x.setItemSlot(net.minecraft.world.entity.EquipmentSlot.OFFHAND,
                            new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.TOTEM_OF_UNDYING));
                p.husks.add(x);
            }
            Estado ahora = k.getEstado();
            if (ahora == Estado.SACRIFICIO && p.antes != Estado.SACRIFICIO)
                p.esperaMinima = Math.min(p.esperaMinima, k.agarradoHace());
            if (ahora != p.antes)
                Mipack.LOGGER.info("[PruebaK] {} -> {} (vida {}, calor {}, sacrificados {})", p.antes, ahora, (int) k.getHealth(),
                        String.format("%.2f", k.calor()), k.sacrificados());
            p.antes = ahora;
            p.dardos = Math.max(p.dardos, h.getLevel().getEntitiesOfClass(DardoAtlatl.class, arena.inflate(20)).size());
            p.serpientes = Math.max(p.serpientes, h.getLevel().getEntitiesOfClass(Xiuhcoatl.class, arena.inflate(20)).size());
        });
        h.startSequence()
                .thenWaitUntil(() -> {
                    Set<Estado> faltan = EnumSet.copyOf(FASE_1);
                    faltan.removeAll(k.visitados());
                    boolean barrio = k.visitados().contains(Estado.BARRIDO) || k.visitados().contains(Estado.BARRIDO_I);
                    boolean piso = k.visitados().contains(Estado.PISOTON) || k.visitados().contains(Estado.PISOTON_DOS);
                    if (!faltan.isEmpty() || !barrio || !piso || k.sacrificados() < 1 || p.dardos < 3 || k.perseguidos() < 2)
                        throw new GameTestAssertException("faltan " + faltan + (barrio ? "" : " BARRIDO") + (piso ? "" : " PISOTON")
                                + " sacrificados " + k.sacrificados() + " dardos " + p.dardos + " perseguidos " + k.perseguidos());
                    if (k.calor() < 0.035f)                       // en normal cada sacrificio sube 4 %
                        throw new GameTestAssertException("el sacrificio no subio el calor: " + k.calor());
                    if (p.esperaMinima < 140)                     // normal: 7 s agarrado antes de empezar a sacrificar
                        throw new GameTestAssertException("sacrifico muy pronto: " + p.esperaMinima + " ticks");
                })
                .thenExecute(() -> {
                    Mipack.LOGGER.info("[PruebaK] fase 1 completa: calor {}, sacrificados {}, persiguio a {}", k.calor(),
                            k.sacrificados(), k.perseguidos());
                    p.totems = true;
                    for (Husk x : p.husks)
                        x.setItemSlot(net.minecraft.world.entity.EquipmentSlot.OFFHAND,
                                new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.TOTEM_OF_UNDYING));
                    k.setHealth(k.getMaxHealth() * 0.45f);
                })
                .thenWaitUntil(() -> {
                    if (!k.coronaRota() || !k.visitados().contains(Estado.CORONA))
                        throw new GameTestAssertException("no rompio la corona (estado " + k.getEstado() + ")");
                    if (!k.visitados().contains(Estado.INVOCAR) || p.serpientes < 2)
                        throw new GameTestAssertException("no invoco a las Xiuhcoatl (" + p.serpientes + ")");
                })
                .thenExecute(() -> Mipack.LOGGER.info("[PruebaK] corona rota y serpiente: ahora la guardia"))
                .thenWaitUntil(() -> {
                    if (!k.visitados().contains(Estado.GUARDIA) || !k.visitados().contains(Estado.CONTRA)) {
                        Husk x = p.husks.isEmpty() ? null : p.husks.get(0);
                        if (x != null && (k.getEstado() == Estado.CAMINAR || k.getEstado() == Estado.QUIETO
                                || k.getEstado() == Estado.GUARDIA)) {
                            Vec3 frente = k.position().add(Vec3.directionFromRotation(0, k.getYRot()).scale(3));
                            x.teleportTo(frente.x, frente.y, frente.z);
                            k.hurt(k.damageSources().mobAttack(x), 1f);
                        }
                        throw new GameTestAssertException("no se puso en guardia ni contraataco");
                    }
                })
                .thenExecute(() -> {
                    Mipack.LOGGER.info("[PruebaK] guardia lista: ahora el Quinto Sol");
                    k.setHealth(k.getMaxHealth() * 0.15f);
                })
                .thenWaitUntil(() -> {
                    if (k.fase() < 3 || k.guerrerosSalidos() == 0)
                        throw new GameTestAssertException("no llego al Quinto Sol con guerreros (fase " + k.fase() + ")");
                    if (k.totems() < 1)
                        throw new GameTestAssertException("todavia no salva ningun totem (sacrificados " + k.sacrificados() + ")");
                })
                .thenExecute(() -> {
                    Mipack.LOGGER.info("[PruebaK] hizo todo: {} (totems {}, guerreros {})", k.visitados(), k.totems(), k.guerrerosSalidos());
                    k.kill();
                })
                .thenWaitUntil(() -> {
                    if (!k.isRemoved())
                        throw new GameTestAssertException("no ha desaparecido (estado " + k.getEstado() + ")");
                    if (!k.visitados().contains(Estado.MUERTE))
                        throw new GameTestAssertException("no hizo su muerte");
                })
                .thenWaitUntil(() -> {
                    int quedan = h.getLevel().getEntitiesOfClass(com.mipack.khaset.GuerreroCalavera.class, arena.inflate(30)).size();
                    if (quedan > 0)
                        throw new GameTestAssertException("quedan " + quedan + " guerreros");
                })
                .thenExecute(cristal::discard)
                .thenSucceed();
    }
}
