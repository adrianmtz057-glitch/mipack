package com.mipack.prueba;

import com.mipack.Dificultad;
import com.mipack.Mipack;
import com.mipack.bruma.BrumaEntity;
import com.mipack.bruma.BrumaEntity.Estado;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.util.EnumSet;
import java.util.Set;

/**
 * La pelea de prueba de La Bruma (./gradlew runGameTestServer): en la arena, contra tres husks aguantadores (en modo de
 * prueba tambien caza mobs) y con antorchas en el piso. De vez en cuando dos husks se le juntan (para que gire y los
 * azote) y uno se va a una esquina (para que se deshaga en bruma y aparezca detras). Pasa cuando hizo todo: gritar,
 * acechar, zarpazo, agarrar y drenar, disolverse, viajar, aparecer, jirones, apago antorchas, persiguio a varios y en la
 * fase 2 salieron almas en pena; junto a una piedra luminosa toma cuerpo; luego se le mata y se revisa que haga su
 * muerte, desaparezca y se lleve a sus almas.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasBruma {
    private static final Set<Estado> TODOS = EnumSet.of(Estado.GRITO, Estado.ACECHAR, Estado.ZARPAZO, Estado.AGARRAR,
            Estado.DRENAR, Estado.DISOLVERSE, Estado.VIAJAR, Estado.APARECER, Estado.JIRONES);
    private static final int PISO = 2;

    private static final class Pelea {
        final Husk[] husks = new Husk[3];
        Estado antes = Estado.QUIETO;
        int almas;
        boolean segundaFase;
    }

    @GameTest(template = "arena", timeoutTicks = 12000)
    public static void bruma(GameTestHelper h) {
        Dificultad.poner(h.getLevel().getServer(), Dificultad.Jefe.BRUMA, Dificultad.Nivel.NORMAL);
        for (int i = 0; i < 12; i++)                         // antorchas que tiene que apagar
            h.setBlock(new BlockPos(14 + (i % 4) * 7, PISO, 14 + (i / 4) * 10), Blocks.TORCH);
        BrumaEntity jefe = h.spawn(Mipack.BRUMA.get(), new BlockPos(24, PISO + 1, 24));
        Pelea p = new Pelea();
        AABB arena = new AABB(h.absolutePos(new BlockPos(1, PISO, 1)), h.absolutePos(new BlockPos(48, PISO + 9, 48)));
        h.onEachTick(() -> {
            if (jefe.isRemoved() || jefe.isDeadOrDying())
                return;
            for (int i = 0; i < p.husks.length; i++) {
                if (p.husks[i] != null && p.husks[i].isAlive())
                    continue;
                Husk x = h.spawn(EntityType.HUSK, new BlockPos(6 + h.getLevel().random.nextInt(37), PISO, 6 + h.getLevel().random.nextInt(37)));
                x.getAttribute(Attributes.MAX_HEALTH).setBaseValue(500.0);
                x.setHealth(500f);
                x.setPersistenceRequired();
                p.husks[i] = x;
            }
            long t = h.getTick();
            if (t % 300 >= 150 && t % 300 < 170 && !jefe.visitados().contains(Estado.JIRONES) && jefe.getEstado() == Estado.ACECHAR)
                for (int i = 0; i < 2; i++)                  // dos se le juntan
                    if (p.husks[i] != null && p.husks[i].getVehicle() == null)
                        p.husks[i].teleportTo(jefe.getX() + (i == 0 ? 2.5 : -2.5), h.absolutePos(new BlockPos(0, PISO, 0)).getY(), jefe.getZ() + 1.0);
            if (t % 400 == 300 && !jefe.visitados().contains(Estado.VIAJAR) && p.husks[2] != null && jefe.getTarget() == p.husks[2]
                    && p.husks[2].getVehicle() == null) {
                BlockPos lejos = h.absolutePos(new BlockPos(jefe.getX() > arena.getCenter().x ? 4 : 44, PISO, jefe.getZ() > arena.getCenter().z ? 4 : 44));
                p.husks[2].teleportTo(lejos.getX() + 0.5, lejos.getY(), lejos.getZ() + 0.5);   // se va a una esquina
            }
            Estado ahora = jefe.getEstado();
            if (!p.segundaFase && jefe.visitados().containsAll(EnumSet.of(Estado.ZARPAZO, Estado.GRITO)) && ahora == Estado.ACECHAR
                    && jefe.drenados() > 0) {
                p.segundaFase = true;                        // a la mitad de la vida: fase 2 (almas en pena)
                jefe.setHealth(jefe.getMaxHealth() * 0.45f);
            }
            if (ahora != p.antes)
                Mipack.LOGGER.info("[Prueba bruma] {} -> {} (vida {}, apagadas {}, drenados {})", p.antes, ahora,
                        (int) jefe.getHealth(), jefe.apagadas(), jefe.drenados());
            p.antes = ahora;
            p.almas = Math.max(p.almas, jefe.almasVivas());
        });
        h.startSequence()
                .thenWaitUntil(() -> {
                    Set<Estado> faltan = EnumSet.copyOf(TODOS);
                    faltan.removeAll(jefe.visitados());
                    if (!faltan.isEmpty() || jefe.apagadas() == 0 || jefe.drenados() == 0 || jefe.perseguidos() < 2
                            || !jefe.fase2() || p.almas == 0)
                        throw new GameTestAssertException("faltan " + faltan + " apagadas " + jefe.apagadas() + " drenados "
                                + jefe.drenados() + " perseguidos " + jefe.perseguidos() + " fase2 " + jefe.fase2() + " almas " + p.almas);
                })
                .thenExecute(() -> {                         // la luz fuerte (que no puede apagar) la obliga a tomar cuerpo
                    h.setBlock(new BlockPos(24, PISO, 8), Blocks.GLOWSTONE);
                    BlockPos junto = h.absolutePos(new BlockPos(24, PISO, 10));
                    jefe.teleportTo(junto.getX() + 0.5, junto.getY(), junto.getZ() + 0.5);
                })
                .thenWaitUntil(() -> {
                    if (!jefe.enLuz() || !jefe.corporea())
                        throw new GameTestAssertException("junto a la piedra luminosa no tomo cuerpo");
                })
                .thenExecute(() -> {
                    Mipack.LOGGER.info("[Prueba bruma] hizo todo: apago {} luces, drenados {}, persiguio a {}, hasta {} almas",
                            jefe.apagadas(), jefe.drenados(), jefe.perseguidos(), p.almas);
                    jefe.kill();
                })
                .thenWaitUntil(() -> {
                    if (!jefe.isRemoved())
                        throw new GameTestAssertException("no ha desaparecido (estado " + jefe.getEstado() + ")");
                    if (!jefe.visitados().contains(Estado.MUERTE))
                        throw new GameTestAssertException("no hizo su muerte");
                    if (!h.getLevel().getEntitiesOfClass(Vex.class, arena.inflate(30)).isEmpty())
                        throw new GameTestAssertException("quedaron almas en pena");
                    for (Husk x : p.husks)
                        if (x != null && x.isPassenger())
                            throw new GameTestAssertException("un husk se quedo colgado");
                })
                .thenSucceed();
    }
}
