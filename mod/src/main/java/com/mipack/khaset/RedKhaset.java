package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Supplier;

/**
 * El estado de las heridas de cada jugador para los demas (el cliente solo sabe sus propios efectos): derribado,
 * aturdido, desorientado y el nivel de desangrado. Con eso se dibujan las poses y las gotas en todos los clientes.
 */
public final class RedKhaset {
    private static final String VERSION = "1";
    public static final SimpleChannel CANAL = NetworkRegistry.newSimpleChannel(new ResourceLocation(Mipack.MODID, "khaset"),
            () -> VERSION, VERSION::equals, VERSION::equals);

    private RedKhaset() {
    }

    public static void registrar() {
        CANAL.messageBuilder(Estado.class, 0, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(Estado::escribir).decoder(Estado::leer).consumerMainThread(Estado::recibir).add();
    }

    /** Manda el estado de 'e' a quien lo ve (y a el mismo). */
    public static void avisar(LivingEntity e) {
        if (e.level().isClientSide)
            return;
        CANAL.send(PacketDistributor.TRACKING_ENTITY_AND_SELF.with(() -> e), Estado.de(e));
    }

    public record Estado(int id, int derribado, int aturdido, int desorientado, int desangrado) {
        static Estado de(LivingEntity e) {
            MobEffectInstance d = e.getEffect(EfectosKhaset.DESANGRADO.get());
            return new Estado(e.getId(), resto(e, EfectosKhaset.DERRIBADO.get()), resto(e, EfectosKhaset.ATURDIDO.get()),
                    resto(e, EfectosKhaset.DESORIENTADO.get()), d == null ? 0 : d.getAmplifier() + 1);
        }

        private static int resto(LivingEntity e, net.minecraft.world.effect.MobEffect ef) {
            MobEffectInstance i = e.getEffect(ef);
            return i == null ? 0 : i.getDuration();
        }

        void escribir(FriendlyByteBuf b) {
            b.writeVarInt(id);
            b.writeVarInt(derribado);
            b.writeVarInt(aturdido);
            b.writeVarInt(desorientado);
            b.writeVarInt(desangrado);
        }

        static Estado leer(FriendlyByteBuf b) {
            return new Estado(b.readVarInt(), b.readVarInt(), b.readVarInt(), b.readVarInt(), b.readVarInt());
        }

        void recibir(Supplier<NetworkEvent.Context> ctx) {
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> com.mipack.cliente.PosesJugador.recibir(this));
        }
    }
}
