package com.mipack.prueba;

import com.mipack.Mipack;
import com.mipack.bruma.BrumaEntity;
import com.mipack.bruma.BrumaEntity.Estado;
import com.mipack.bruma.ClonBruma;
import com.mipack.bruma.SoldadoBruma;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.util.List;

/**
 * El ejercito y los clones de La Bruma (./gradlew runGameTestServer): sale el ejercito con el grande, ella queda
 * intocable arriba, al morir el grande grita, pierde vida y se arrodilla; luego los clones: cada uno que muere le quita
 * vida y al caer todos se arrodilla; al morir ella se deshacen los suyos.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasEjercito {
    private static final int PISO = 2;

    private static void revisar(boolean ok, String que) {
        if (!ok)
            throw new GameTestAssertException(que);
    }

    @GameTest(template = "arena", timeoutTicks = 400)
    public static void ejercito(GameTestHelper h) {
        BrumaEntity b = h.spawn(Mipack.BRUMA.get(), new BlockPos(24, PISO + 1, 24));
        AABB todo = new AABB(h.absolutePos(new BlockPos(0, 0, 0)), h.absolutePos(new BlockPos(48, 20, 48))).inflate(8);
        float[] vida = new float[1];
        b.getPersistentData().remove("mipack_centro");          // sin arena (la de otra prueba queda cerca)
        h.runAfterDelay(2, () -> b.probar(Estado.TITIRITERA));
        h.runAfterDelay(40, () -> {
            List<SoldadoBruma> s = h.getLevel().getEntitiesOfClass(SoldadoBruma.class, todo);
            long grandes = s.stream().filter(x -> x.tipo() == SoldadoBruma.Tipo.GRANDE).count();
            long arqueros = s.stream().filter(x -> x.tipo() == SoldadoBruma.Tipo.ARQUERO).count();
            revisar(s.size() >= 20 && grandes == 1 && arqueros >= 4, "el ejercito salio incompleto: " + s.size() + " (grandes " + grandes + ", arqueros " + arqueros + ")");
            revisar(b.getEstado() == Estado.TITIRITERA, "deberia seguir de titiritera, esta en " + b.getEstado());
            revisar(!b.hurt(b.damageSources().generic(), 50f), "de titiritera deberia ser intocable");
            vida[0] = b.getHealth();
            s.stream().filter(x -> x.tipo() == SoldadoBruma.Tipo.GRANDE).forEach(x -> x.kill());
        });
        h.runAfterDelay(46, () -> {
            revisar(b.getEstado() == Estado.RODILLAS, "al morir el grande deberia arrodillarse, esta en " + b.getEstado());
            revisar(b.getHealth() < vida[0] - b.getMaxHealth() * 0.1f, "al morir el grande deberia perder vida");
        });
        h.runAfterDelay(180, () -> b.probar(Estado.CLONES));
        h.runAfterDelay(200, () -> {
            List<ClonBruma> c = h.getLevel().getEntitiesOfClass(ClonBruma.class, todo);
            revisar(c.size() >= 5, "salieron pocos clones: " + c.size());
            vida[0] = b.getHealth();
            c.forEach(x -> x.hurt(x.damageSources().generic(), 100f));
        });
        h.runAfterDelay(206, () -> {
            revisar(b.getEstado() == Estado.RODILLAS, "al caer los clones deberia arrodillarse, esta en " + b.getEstado());
            revisar(b.getHealth() < vida[0] - b.getMaxHealth() * 0.1f, "los clones muertos deberian quitarle vida");
            b.kill();
        });
        h.runAfterDelay(300, () -> {
            revisar(h.getLevel().getEntitiesOfClass(SoldadoBruma.class, todo).isEmpty(), "al morir ella, sus soldados deberian deshacerse");
            h.succeed();
        });
    }
}
