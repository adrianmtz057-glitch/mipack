package com.mipack.objetos;

import com.mipack.Mipack;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.ForgeMod;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingFallEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.Map;
import java.util.UUID;

/**
 * Lo que hacen las armaduras de Velkia, pieza por pieza (con una sola ya se nota; con el set completo, todo). No son
 * pociones: no salen en el menu de efectos y la ligereza no hace zoom (ver ClienteObjetos).
 * <ul>
 * <li>Plumas: ligereza (hasta +18% de velocidad) y caida de pluma (cae despacio y se lleva menos dano por caida).</li>
 * <li>Quitina: ligereza leve (hasta +6%).</li>
 * <li>Tortuga: nadas mas rapido (hasta +60%; el casco de tortuga de Minecraft tambien cuenta un poco).</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID)
public final class EfectosArmadura {
    public static final UUID LIGEREZA = UUID.fromString("0f1c9a54-6b2e-4f0a-9d33-2c7e5b8a4e11");
    private static final UUID NADO = UUID.fromString("0f1c9a54-6b2e-4f0a-9d33-2c7e5b8a4e12");
    /** Cuanto cuenta cada pieza para la ligereza, la caida y el nado. */
    private static final Map<EquipmentSlot, Float> PASO = Map.of(EquipmentSlot.HEAD, 0.15f, EquipmentSlot.CHEST, 0.30f,
            EquipmentSlot.LEGS, 0.30f, EquipmentSlot.FEET, 0.25f);
    private static final Map<EquipmentSlot, Float> CAIDA = Map.of(EquipmentSlot.HEAD, 0.10f, EquipmentSlot.CHEST, 0.35f,
            EquipmentSlot.LEGS, 0.25f, EquipmentSlot.FEET, 0.30f);
    private static final Map<EquipmentSlot, Float> NADAR = Map.of(EquipmentSlot.CHEST, 0.40f, EquipmentSlot.LEGS, 0.35f,
            EquipmentSlot.FEET, 0.25f);
    public static final float LIGEREZA_PLUMAS = 0.18f, LIGEREZA_QUITINA = 0.06f, NADO_TORTUGA = 0.6f;
    /** Cuanto de la gravedad le quita la caida de pluma con el set completo. */
    private static final float CAIDA_PLUMAS = 0.85f;

    private EfectosArmadura() {
    }

    /** Cuanto trae de un material (0 a 1) segun el peso de cada pieza. */
    static float cuanto(Player p, MaterialArmadura m, Map<EquipmentSlot, Float> pesos) {
        float f = 0.0f;
        for (Map.Entry<EquipmentSlot, Float> e : pesos.entrySet()) {
            ItemStack s = p.getItemBySlot(e.getKey());
            if (s.getItem() instanceof ArmaduraMipack a && a.material() == m)
                f += e.getValue();
        }
        return f;
    }

    public static float ligereza(Player p) {
        return LIGEREZA_PLUMAS * cuanto(p, MaterialArmadura.PLUMAS, PASO) + LIGEREZA_QUITINA * cuanto(p, MaterialArmadura.QUITINA, PASO);
    }

    static float caida(Player p) {
        return cuanto(p, MaterialArmadura.PLUMAS, CAIDA);
    }

    static float nado(Player p) {
        float f = cuanto(p, MaterialArmadura.TORTUGA, NADAR);
        if (p.getItemBySlot(EquipmentSlot.HEAD).is(Items.TURTLE_HELMET))
            f += 0.1f;
        return Math.min(1.0f, f) * NADO_TORTUGA;
    }

    @SubscribeEvent
    public static void tick(TickEvent.PlayerTickEvent e) {
        if (e.phase != TickEvent.Phase.END)
            return;
        Player p = e.player;
        if (!p.level().isClientSide && p.tickCount % 5 == 0) {
            poner(p.getAttribute(Attributes.MOVEMENT_SPEED), LIGEREZA, "mipack ligereza", ligereza(p));
            poner(p.getAttribute(ForgeMod.SWIM_SPEED.get()), NADO, "mipack nado", nado(p));
        }
        // la caida de pluma (en el cliente es la que cuenta para el jugador que se mueve)
        float c = caida(p);
        if (c > 0 && !p.onGround() && !p.isFallFlying() && !p.getAbilities().flying && !p.isInWater() && !p.isInLava()) {
            Vec3 v = p.getDeltaMovement();
            if (v.y < 0) {
                double k = CAIDA_PLUMAS * c;
                double y = v.y + 0.08 * 0.98 * k;
                double tope = -3.92 * (1.0 - k) - 0.12;
                p.setDeltaMovement(v.x, Math.max(y, tope), v.z);
            }
        }
    }

    private static void poner(AttributeInstance a, UUID id, String nombre, float valor) {
        if (a == null)
            return;
        AttributeModifier antes = a.getModifier(id);
        if (antes != null && Math.abs(antes.getAmount() - valor) < 1e-4)
            return;
        if (antes != null)
            a.removeModifier(id);
        if (valor > 0)
            a.addTransientModifier(new AttributeModifier(id, nombre, valor, AttributeModifier.Operation.MULTIPLY_BASE));
    }

    /** Con plumas se lleva menos dano por caida, segun cuanto traiga. */
    @SubscribeEvent
    public static void caer(LivingFallEvent e) {
        if (e.getEntity() instanceof Player p) {
            float c = caida(p);
            if (c > 0) {
                e.setDistance(e.getDistance() * (1.0f - 0.8f * c));
                e.setDamageMultiplier(e.getDamageMultiplier() * (1.0f - 0.6f * c));
            }
        }
    }
}
