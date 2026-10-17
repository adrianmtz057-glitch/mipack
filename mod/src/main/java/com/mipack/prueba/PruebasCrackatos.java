package com.mipack.prueba;

import com.mipack.Dificultad;
import com.mipack.Mipack;
import com.mipack.entidad.AcaroAmatista;
import com.mipack.entidad.CrackatosEntity;
import com.mipack.entidad.EfectosCrackatos;
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
 * La pelea de prueba (se corre sola con ./gradlew runGameTestServer): Crackatos en una arena de 49x49 con paredes
 * contra dos husks aguantadores (en modo de prueba tambien ataca mobs). Una embestida si y una no, el husk al que va
 * "esquiva" (se hace a un lado al arrancar). Pasa cuando Crackatos hizo todo: rugir, acechar, rascar, embestir (sin
 * pararse hasta la pared), chocar, quedarse atorado, zafarse, la cornada, la sacudida con sus puas (que dejan
 * esquirlas), el azote con la ola, persiguio a los dos husks (no se clava con uno) y en la fase 2 saco acaros; luego
 * se le mata y se revisa que haga su muerte, desaparezca, se lleve a sus acaros y quite las esquirlas.
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
        final Husk[] husks = new Husk[2];
        Estado antes = Estado.QUIETO;
        int embestidas, atinadas, puas, bloquesDeOla, acaros;
        boolean segundaFase, pegoEstaEmbestida, esquirlas;
    }

    @GameTest(template = "arena", timeoutTicks = 12000)
    public static void pelea(GameTestHelper h) {
        Dificultad.poner(h.getLevel().getServer(), Dificultad.Jefe.CRACKATOS, Dificultad.Nivel.NORMAL);
        CrackatosEntity jefe = h.spawn(Mipack.CRACKATOS.get(), new BlockPos(24, PISO, 24));
        jefe.getPersistentData().remove("mipack_centro");        // pelea libre (sin la arena de otra prueba)
        Pelea p = new Pelea();
        AABB arena = new AABB(h.absolutePos(new BlockPos(1, PISO, 1)), h.absolutePos(new BlockPos(48, PISO + 9, 48)));
        h.onEachTick(() -> {
            if (jefe.isRemoved() || jefe.isDeadOrDying())
                return;
            for (int i = 0; i < p.husks.length; i++) {
                if (p.husks[i] != null && p.husks[i].isAlive())
                    continue;
                Husk x = h.spawn(EntityType.HUSK, new BlockPos(4 + h.getLevel().random.nextInt(41), PISO, i == 0 ? 4 : 44));
                x.getAttribute(Attributes.MAX_HEALTH).setBaseValue(400.0);
                x.setHealth(400f);
                x.setPersistenceRequired();
                p.husks[i] = x;
            }
            Estado ahora = jefe.getEstado();
            if (ahora == Estado.ACECHAR && !jefe.visitados().contains(Estado.CABEZAZO) && h.getTick() > 3000
                    && jefe.getTarget() instanceof Husk pegado) {        // alguien que se le queda pegado (para la cornada)
                Vec3 frente = jefe.position().add(jefe.getLookAngle().multiply(1, 0, 1).normalize().scale(jefe.getBbWidth() * 0.5 + 1.5));
                pegado.teleportTo(frente.x, jefe.getY(), frente.z);
            }
            if (ahora == Estado.EMBESTIR && p.antes != Estado.EMBESTIR) {
                p.embestidas++;
                p.pegoEstaEmbestida = false;
                if (p.embestidas % 2 == 1 && jefe.getTarget() instanceof Husk blanco)
                    esquivar(h, jefe, blanco);
            }
            if (ahora == Estado.EMBESTIR && !p.pegoEstaEmbestida)
                for (Husk x : p.husks)
                    if (x != null && x.hurtTime >= 8 && x.distanceTo(jefe) < 20) {
                        p.pegoEstaEmbestida = true;
                        p.atinadas++;
                    }
            if (ahora == Estado.SACUDIDA && !p.segundaFase) {
                p.segundaFase = true;                 // a la mitad de la vida: fase 2 (acaros) y despues se alza y azota
                jefe.setHealth(jefe.getMaxHealth() * 0.45f);
            }
            if (ahora != p.antes)
                Mipack.LOGGER.info("[Prueba] {} -> {} (embestidas {}, vida {})", p.antes, ahora, p.embestidas, (int) jefe.getHealth());
            p.antes = ahora;
            p.puas = Math.max(p.puas, h.getLevel().getEntitiesOfClass(PuaCayendo.class, arena.inflate(30)).size());
            p.acaros = Math.max(p.acaros, h.getLevel().getEntitiesOfClass(AcaroAmatista.class, arena.inflate(30)).size());
            for (Husk x : p.husks)
                if (x != null && x.hasEffect(EfectosCrackatos.ESQUIRLAS.get()))
                    p.esquirlas = true;
            p.bloquesDeOla = Math.max(p.bloquesDeOla, h.getLevel().getEntitiesOfClass(Display.BlockDisplay.class,
                    arena.inflate(30), d -> d.getTags().contains(Ola.ETIQUETA)).size());
        });
        h.startSequence()
                .thenWaitUntil(() -> {
                    Set<Estado> faltan = EnumSet.copyOf(TODOS);
                    faltan.removeAll(jefe.visitados());
                    if (!faltan.isEmpty() || p.atinadas == 0 || p.puas < 20 || p.bloquesDeOla == 0 || jefe.perseguidos() < 2
                            || !jefe.fase2() || p.acaros == 0 || !p.esquirlas)
                        throw new GameTestAssertException("faltan " + faltan + " embestidas que pegaron " + p.atinadas
                                + " puas " + p.puas + " ola " + p.bloquesDeOla + " perseguidos " + jefe.perseguidos()
                                + " fase2 " + jefe.fase2() + " acaros " + p.acaros + " esquirlas " + p.esquirlas);
                })
                .thenExecute(() -> {
                    Mipack.LOGGER.info("[Prueba] hizo todo: {} embestidas ({} pegaron), hasta {} puas a la vez, hasta {} bloques de ola, "
                            + "persiguio a {}, hasta {} acaros", p.embestidas, p.atinadas, p.puas, p.bloquesDeOla, jefe.perseguidos(), p.acaros);
                    jefe.kill();
                })
                .thenWaitUntil(() -> {
                    if (!jefe.isRemoved())
                        throw new GameTestAssertException("no ha desaparecido (estado " + jefe.getEstado() + ")");
                    if (!jefe.visitados().contains(Estado.MUERTE))
                        throw new GameTestAssertException("no hizo su muerte");
                    if (!h.getLevel().getEntitiesOfClass(AcaroAmatista.class, arena.inflate(30)).isEmpty())
                        throw new GameTestAssertException("quedaron acaros");
                    for (Husk x : p.husks)
                        if (x != null && x.isAlive() && x.hasEffect(EfectosCrackatos.ESQUIRLAS.get()))
                            throw new GameTestAssertException("no se quitaron las esquirlas");
                })
                .thenSucceed();
    }

    /** El husk se hace a un lado (perpendicular a la embestida), como un jugador que la esquiva. */
    private static void esquivar(GameTestHelper h, CrackatosEntity jefe, Husk blanco) {
        Vec3 d = blanco.position().subtract(jefe.position());
        Vec3 lado = new Vec3(-d.z, 0, d.x).normalize().scale(12);
        // (relativePos de GameTest en 1.20.1 voltea x y z: se acota en coordenadas absolutas)
        BlockPos min = h.absolutePos(new BlockPos(2, PISO, 2)), max = h.absolutePos(new BlockPos(46, PISO, 46));
        Vec3 q = blanco.position().add(lado);
        Vec3 a = new Vec3(Math.max(Math.min(min.getX(), max.getX()) + 0.5, Math.min(Math.max(min.getX(), max.getX()) + 0.5, q.x)),
                min.getY(), Math.max(Math.min(min.getZ(), max.getZ()) + 0.5, Math.min(Math.max(min.getZ(), max.getZ()) + 0.5, q.z)));
        blanco.teleportTo(a.x, a.y, a.z);
        Mipack.LOGGER.info("[Prueba] el husk esquiva");
    }
}
