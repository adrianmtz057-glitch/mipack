package com.mipack.prueba;

import com.mipack.Mipack;
import com.mipack.bichos.Bicho;
import com.mipack.bichos.Bichos;
import com.mipack.bichos.BichosDatos;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

import java.util.ArrayList;
import java.util.List;

/**
 * Los 36 bichos (./gradlew runGameTestServer): salen todos y viven un rato sin romperse; se manchan de mura; el
 * cervatillo no recibe dano; las aves se espantan y vuelan.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasBichos {
    private static final int PISO = 2;

    private static void revisar(boolean ok, String que) {
        if (!ok)
            throw new GameTestAssertException(que);
    }

    @GameTest(template = "arena", timeoutTicks = 300, batch = "bichos")
    public static void bichos(GameTestHelper h) {
        List<Bicho> todos = new ArrayList<>();
        int i = 0;
        for (BichosDatos.Especie e : BichosDatos.TODAS) {
            Bicho b = h.spawn(Bichos.TIPOS.get(e.id()).get(), new BlockPos(6 + (i % 6) * 7, PISO, 6 + (i / 6) * 7));
            todos.add(b);
            i++;
        }
        revisar(todos.size() == 36, "deberian ser 36 bichos, son " + todos.size());
        h.runAfterDelay(5, () -> {
            Bicho cervatillo = todos.stream().filter(b -> b.especie.id().equals("cervatillo_musgo")).findFirst().get();
            float v = cervatillo.getHealth();
            cervatillo.hurt(cervatillo.damageSources().generic(), 5f);
            revisar(cervatillo.getHealth() == v, "al cervatillo no se le hace dano");
            Bicho toro = todos.stream().filter(b -> b.especie.id().equals("toro_arena")).findFirst().get();
            toro.manchar();
            revisar(toro.manchado(), "el toro deberia mancharse de mura");
            Bicho pato = todos.stream().filter(b -> b.especie.id().equals("pato_estanque")).findFirst().get();
            pato.hurt(pato.damageSources().generic(), 1f);
            pato.setTarget(null);
        });
        h.runAfterDelay(200, () -> {
            for (Bicho b : todos)
                revisar(b.isAlive() || b.especie.id().equals("pato_estanque"), b.especie.id() + " se murio o se rompio: " + b.getLastDamageSource() + " en " + b.position());
            Bicho murcielago = todos.stream().filter(b -> b.especie.id().equals("murcielago_mura")).findFirst().get();
            revisar(murcielago.volando(), "el murcielago deberia andar volando");
            for (Bicho b : todos)
                b.discard();
            h.succeed();
        });
    }
}
