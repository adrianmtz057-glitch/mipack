package com.mipack.prueba;

import com.mipack.Mipack;
import com.mipack.entidad.CrackatosEntity;
import com.mipack.entidad.CrackatosEntity.Estado;
import com.mipack.entidad.Ola;
import com.mipack.entidad.PuaCayendo;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.util.EnumSet;
import java.util.Set;

/**
 * La pelea de prueba (se corre sola con ./gradlew runGameTestServer): Crackatos en una arena de 33x33 con paredes
 * contra un husk aguantador (en modo de prueba tambien ataca mobs). Una embestida si y una no, el husk "esquiva"
 * (se hace a un lado al arrancar la embestida) para que se estrelle con la pared. Pasa cuando Crackatos hizo todo:
 * rugir, acechar, rascar, embestir, chocar, quedarse atorado, zafarse, el cabezazo, la sacudida con sus puas y el
 * azote con la ola; luego se le mata y se revisa que haga su muerte y desaparezca.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasCrackatos {
    private static final Set<Estado> TODOS = EnumSet.of(Estado.RUGIDO, Estado.ACECHAR, Estado.RASCAR, Estado.EMBESTIR,
            Estado.CHOCAR, Estado.ATORADO, Estado.ZAFARSE, Estado.CABEZAZO, Estado.SACUDIDA, Estado.ALZARSE);

    /** La altura del piso de la arena en las coordenadas de la prueba: GameTest pone la estructura un bloque arriba
     * de su origen, asi que el piso (la capa 0 de arena.nbt) queda en y=1 y se para uno arriba. */
    private static final int PISO = 2;

    private static final class Pelea {
        Husk blanco;
        Estado antes = Estado.QUIETO;
        int embestidas, atinadas, puas, bloquesDeOla;
        boolean segundaFase;
    }

    @GameTest(template = "arena", timeoutTicks = 6000)
    public static void pelea(GameTestHelper h) {
        CrackatosEntity jefe = h.spawn(Mipack.CRACKATOS.get(), new BlockPos(16, PISO, 16));
        Pelea p = new Pelea();
        AABB arena = new AABB(h.absolutePos(new BlockPos(1, PISO, 1)), h.absolutePos(new BlockPos(32, PISO + 7, 32)));
        h.onEachTick(() -> {
            if (jefe.isRemoved() || jefe.isDeadOrDying())
                return;
            if (p.blanco == null || !p.blanco.isAlive()) {
                p.blanco = h.spawn(EntityType.HUSK, new BlockPos(4 + h.getLevel().random.nextInt(25), PISO, 4));
                p.blanco.getAttribute(Attributes.MAX_HEALTH).setBaseValue(400.0);
                p.blanco.setHealth(400f);
                p.blanco.setPersistenceRequired();
                jefe.setTarget(p.blanco);
            }
            Estado ahora = jefe.getEstado();
            if (ahora == Estado.EMBESTIR && p.antes != Estado.EMBESTIR) {
                p.embestidas++;
                if (p.embestidas % 2 == 1)
                    esquivar(h, jefe, p.blanco);
            }
            if (ahora == Estado.CABEZAZO && p.antes == Estado.EMBESTIR)
                p.atinadas++;
            if (ahora == Estado.SACUDIDA && !p.segundaFase) {
                p.segundaFase = true;                 // a la mitad de la vida: despues de sacudirse se alza y azota
                jefe.setHealth(jefe.getMaxHealth() * 0.45f);
            }
            if (ahora != p.antes)
                Mipack.LOGGER.info("[Prueba] {} -> {} (embestidas {}, vida {})", p.antes, ahora, p.embestidas, (int) jefe.getHealth());
            p.antes = ahora;
            p.puas = Math.max(p.puas, h.getLevel().getEntitiesOfClass(PuaCayendo.class, arena.inflate(30)).size());
            p.bloquesDeOla = Math.max(p.bloquesDeOla, h.getLevel().getEntitiesOfClass(Display.BlockDisplay.class,
                    arena.inflate(30), d -> d.getTags().contains(Ola.ETIQUETA)).size());
        });
        h.startSequence()
                .thenWaitUntil(() -> {
                    Set<Estado> faltan = EnumSet.copyOf(TODOS);
                    faltan.removeAll(jefe.visitados());
                    if (!faltan.isEmpty() || p.atinadas == 0 || p.puas == 0 || p.bloquesDeOla == 0)
                        throw new GameTestAssertException("faltan " + faltan + " embestidas que pegaron " + p.atinadas
                                + " puas " + p.puas + " ola " + p.bloquesDeOla);
                })
                .thenExecute(() -> {
                    Mipack.LOGGER.info("[Prueba] hizo todo: {} embestidas ({} pegaron), hasta {} puas a la vez, hasta {} bloques de ola",
                            p.embestidas, p.atinadas, p.puas, p.bloquesDeOla);
                    jefe.kill();
                })
                .thenWaitUntil(() -> {
                    if (!jefe.isRemoved())
                        throw new GameTestAssertException("no ha desaparecido (estado " + jefe.getEstado() + ")");
                    if (!jefe.visitados().contains(Estado.MUERTE))
                        throw new GameTestAssertException("no hizo su muerte");
                })
                .thenSucceed();
    }

    /** El husk se hace a un lado (perpendicular a la embestida), como un jugador que la esquiva. */
    private static void esquivar(GameTestHelper h, CrackatosEntity jefe, Husk blanco) {
        Vec3 d = blanco.position().subtract(jefe.position());
        Vec3 lado = new Vec3(-d.z, 0, d.x).normalize().scale(8);
        // (relativePos de GameTest en 1.20.1 voltea x y z: se acota en coordenadas absolutas)
        BlockPos min = h.absolutePos(new BlockPos(2, PISO, 2)), max = h.absolutePos(new BlockPos(30, PISO, 30));
        Vec3 q = blanco.position().add(lado);
        Vec3 a = new Vec3(Math.max(Math.min(min.getX(), max.getX()) + 0.5, Math.min(Math.max(min.getX(), max.getX()) + 0.5, q.x)),
                min.getY(), Math.max(Math.min(min.getZ(), max.getZ()) + 0.5, Math.min(Math.max(min.getZ(), max.getZ()) + 0.5, q.z)));
        blanco.teleportTo(a.x, a.y, a.z);
        Mipack.LOGGER.info("[Prueba] el husk esquiva");
    }
}
