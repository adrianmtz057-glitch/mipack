package com.mipack.bruma;

import com.mipack.Mipack;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Supplier;

/** La cordura del jugador para su pantalla. */
public final class RedBruma {
    private static final String VERSION = "1";
    public static final SimpleChannel CANAL = NetworkRegistry.newSimpleChannel(new ResourceLocation(Mipack.MODID, "bruma"),
            () -> VERSION, VERSION::equals, VERSION::equals);

    private RedBruma() {
    }

    public static void registrar() {
        CANAL.messageBuilder(Estado.class, 0, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(Estado::escribir).decoder(Estado::leer).consumerMainThread(Estado::recibir).add();
    }

    public static void enviar(ServerPlayer p, Estado e) {
        try {
            CANAL.send(PacketDistributor.PLAYER.with(() -> p), e);
        } catch (NullPointerException sinConexion) {
            // los jugadores de las pruebas no tienen conexion
        }
    }

    /** cordura: 0 a 100; pelea: si esta en la pelea con La Bruma (si no, la barra no se ve). */
    public record Estado(float cordura, boolean pelea) {
        void escribir(FriendlyByteBuf b) {
            b.writeFloat(cordura);
            b.writeBoolean(pelea);
        }

        static Estado leer(FriendlyByteBuf b) {
            return new Estado(b.readFloat(), b.readBoolean());
        }

        void recibir(Supplier<NetworkEvent.Context> c) {
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> com.mipack.cliente.ClienteBruma.recibir(this));
        }
    }
}
