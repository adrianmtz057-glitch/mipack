package com.mipack.prueba;

import com.mipack.Mipack;
import com.mipack.bruma.BrumaEntity;
import com.mipack.bruma.Cordura;
import com.mipack.bruma.Poseido;
import com.mipack.khaset.KhasetEntity;
import com.mipack.objetos.ObjetosMipack;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/**
 * La cordura y los objetos de rol (./gradlew runGameTestServer): en la pelea con La Bruma la cordura baja y cerca del
 * pedazo de piramide sube; en cero sale el doble y el jugador queda poseido e intocable; el doble solo cae con la
 * espada de vitae y regresa al jugador entero; el totem de Anj salva y da 2 s sin dano; la espada de hielo pega mucho
 * a Khaset; la armadura de tanque y la de hielo aguantan.
 */
@GameTestHolder(Mipack.MODID)
@PrefixGameTestTemplate(false)
public class PruebasRol {
    private static final int PISO = 2;

    private static void revisar(boolean ok, String que) {
        if (!ok)
            throw new GameTestAssertException(que);
    }

    private static Player jugador(GameTestHelper h, double x, double z) {
        Player p = h.makeMockSurvivalPlayer();
        p.moveTo(h.absoluteVec(new Vec3(x, PISO, z)));
        return p;
    }

    @GameTest(template = "arena", timeoutTicks = 100)
    public static void cordura_y_posesion(GameTestHelper h) {
        BrumaEntity b = h.spawn(Mipack.BRUMA.get(), new BlockPos(24, PISO + 1, 24));
        b.getPersistentData().remove("mipack_centro");
        h.runAfterDelay(2, () -> {
            Player p = jugador(h, 30.5, 24.5);
            Cordura.poner(p, 50f);
            Cordura.segundo(p);
            revisar(Cordura.de(p) < 50f, "en la pelea la cordura deberia bajar: " + Cordura.de(p));
            p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(ObjetosMipack.PEDAZO_PIRAMIDE.get()));
            Cordura.segundo(p);
            revisar(Cordura.de(p) > 50f, "junto al pedazo de piramide deberia subir: " + Cordura.de(p));
            p.setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY);
            Poseido d = Cordura.poseer(p, b);
            revisar(d != null && Cordura.poseido(p), "en cero deberia quedar poseido con su doble");
            float antes = p.getHealth();
            p.hurt(p.damageSources().generic(), 10f);
            revisar(p.getHealth() == antes, "el poseido no deberia recibir dano");
            Player amigo = jugador(h, 28.5, 24.5);
            revisar(!d.hurt(d.damageSources().playerAttack(amigo), 50f) && d.isAlive(), "sin vitae el doble no deberia caer");
            amigo.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ObjetosMipack.ESPADA_VITAE.get()));
            d.hurt(d.damageSources().playerAttack(amigo), 5f);
            revisar(d.isRemoved() && !Cordura.poseido(p) && Cordura.de(p) == Cordura.MAX, "la vitae deberia regresarlo con la cordura llena");
            b.discard();
            h.succeed();
        });
    }

    @GameTest(template = "arena", timeoutTicks = 60)
    public static void objetos_de_rol(GameTestHelper h) {
        KhasetEntity k = h.spawn(Mipack.KHASET.get(), new BlockPos(30, PISO, 24));
        k.getPersistentData().remove("mipack_centro");
        h.runAfterDelay(2, () -> {
            // el totem de Anj
            Player p = jugador(h, 20.5, 20.5);
            p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ObjetosMipack.TOTEM_ANJ.get()));
            LivingDeathEvent muerte = new LivingDeathEvent(p, p.damageSources().generic());
            revisar(MinecraftForge.EVENT_BUS.post(muerte), "el totem de Anj deberia salvarlo");
            revisar(p.getMainHandItem().isEmpty() && p.getHealth() >= 1f, "el totem se gasta y lo deja con vida");
            float v = p.getHealth();
            p.hurt(p.damageSources().generic(), 5f);
            revisar(p.getHealth() == v, "los 2 s de Anj: sin dano");
            // la espada de hielo contra Khaset
            Player kemira = jugador(h, 26.5, 24.5);
            kemira.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ObjetosMipack.ESPADA_HIELO.get()));
            LivingHurtEvent golpe = new LivingHurtEvent(k, k.damageSources().playerAttack(kemira), 6f);
            MinecraftForge.EVENT_BUS.post(golpe);
            revisar(golpe.getAmount() >= 30f, "la espada de hielo deberia pegarle mucho a Khaset: " + golpe.getAmount());
            // tanque y hielo
            Player tanque = jugador(h, 22.5, 26.5);
            tanque.setItemSlot(EquipmentSlot.HEAD, new ItemStack(ObjetosMipack.ARMADURAS.stream().filter(o -> o.getId().getPath().equals("tanque_casco")).findFirst().get().get()));
            tanque.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ObjetosMipack.ARMADURAS.stream().filter(o -> o.getId().getPath().equals("tanque_pechera")).findFirst().get().get()));
            tanque.setItemSlot(EquipmentSlot.LEGS, new ItemStack(ObjetosMipack.ARMADURAS.stream().filter(o -> o.getId().getPath().equals("tanque_pantalon")).findFirst().get().get()));
            tanque.setItemSlot(EquipmentSlot.FEET, new ItemStack(ObjetosMipack.ARMADURAS.stream().filter(o -> o.getId().getPath().equals("tanque_botas")).findFirst().get().get()));
            revisar(com.mipack.arena.Arena.tanque(tanque), "la armadura de tanque completa deberia contar para el centro");
            LivingHurtEvent g2 = new LivingHurtEvent(tanque, tanque.damageSources().mobAttack(k), 20f);
            MinecraftForge.EVENT_BUS.post(g2);
            revisar(g2.getAmount() < 12f, "el tanque deberia aguantar mucho: " + g2.getAmount());
            Player hielo = jugador(h, 22.5, 22.5);
            hielo.setItemSlot(EquipmentSlot.CHEST, new ItemStack(ObjetosMipack.ARMADURAS.stream().filter(o -> o.getId().getPath().equals("hielo_pechera")).findFirst().get().get()));
            LivingHurtEvent g3 = new LivingHurtEvent(hielo, hielo.damageSources().mobAttack(k), 20f);
            MinecraftForge.EVENT_BUS.post(g3);
            revisar(g3.getAmount() < 18f, "la pechera de hielo deberia aguantar a Khaset: " + g3.getAmount());
            k.discard();
            h.succeed();
        });
    }
}
