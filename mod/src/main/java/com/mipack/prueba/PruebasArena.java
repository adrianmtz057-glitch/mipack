package com.mipack.prueba;

import com.mipack.Mipack;
import com.mipack.arena.Arena;
import com.mipack.khaset.KhasetEntity;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/**
 * La arena (./gradlew runGameTestServer): el jefe toma el bloque central, su vida con pocos jugadores, que no sale del
 * radio, que el centro tapado bloquea su ataque y lastima al que lo tapa, el PvP apagado y el castigo de lejos.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasArena {
    private static final int PISO = 2;

    private static void revisar(boolean ok, String que) {
        if (!ok)
            throw new GameTestAssertException(que);
    }

    @GameTest(template = "arena", timeoutTicks = 120)
    public static void arena_jefe(GameTestHelper h) {
        BlockPos rel = new BlockPos(24, PISO, 24), centro = h.absolutePos(rel);
        h.setBlock(rel, ObjetosMipack.CENTRO_ARENA.get());
        KhasetEntity k = h.spawn(Mipack.KHASET.get(), new BlockPos(30, PISO, 24));
        Vec3 sobre = Arena.encima(centro);
        h.runAfterDelay(30, () -> {
            revisar(centro.equals(Arena.centro(k)), "Khaset no tomo el bloque central: " + Arena.centro(k));
            float vida = k.getMaxHealth();
            revisar(vida > 1000 && vida < 2200, "la vida con un jugador deberia ser poca, es " + vida);
            // no sale del radio
            k.teleportTo(sobre.x + Arena.radio() + 20, k.getY(), sobre.z);
        });
        h.runAfterDelay(34, () -> {
            revisar(!Arena.fuera(k), "Khaset se salio de la arena: " + k.position());
            k.teleportTo(sobre.x + 3, sobre.y, sobre.z);
            // tapar el centro: el ataque no sale y al que lo tapa le duele
            Player tapa = h.makeMockSurvivalPlayer();
            tapa.moveTo(sobre.x, sobre.y, sobre.z);
            float antes = tapa.getHealth();
            revisar(!Arena.intentarCentro(k, java.util.List.of(tapa)), "con alguien en el centro el ataque debio bloquearse");
            revisar(tapa.getHealth() < antes - 4, "al que tapo el centro no le dolio: " + antes + " -> " + tapa.getHealth());
            Player libre = h.makeMockSurvivalPlayer();
            libre.moveTo(sobre.x + 6, sobre.y, sobre.z);
            revisar(Arena.intentarCentro(k, java.util.List.of(libre)), "sin nadie encima el ataque debio salir");
            // sin PvP adentro
            boolean cancelado = MinecraftForge.EVENT_BUS.post(new LivingAttackEvent(libre, libre.damageSources().playerAttack(tapa), 5f));
            revisar(cancelado, "el PvP no se cancelo dentro de la arena");
            // el de arriba hace la cuarta parte
            Player arriba = h.makeMockSurvivalPlayer();
            arriba.moveTo(sobre.x + 4, sobre.y + 30, sobre.z);
            LivingHurtEvent golpe = new LivingHurtEvent(k, k.damageSources().playerAttack(arriba), 20f);
            MinecraftForge.EVENT_BUS.post(golpe);
            revisar(golpe.getAmount() < 6f, "el que pega desde arriba deberia hacer poco, hizo " + golpe.getAmount());
            LivingHurtEvent cerca = new LivingHurtEvent(k, k.damageSources().playerAttack(libre), 20f);
            MinecraftForge.EVENT_BUS.post(cerca);
            revisar(cerca.getAmount() > 19f, "el de cerca deberia pegar completo, pego " + cerca.getAmount());
            k.discard();
            h.succeed();
        });
    }
}
