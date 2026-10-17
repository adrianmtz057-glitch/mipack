package com.mipack.agua;

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

/** El agua del jugador para su pantalla, y el "tomar agua del rio" del cliente al servidor. */
public final class RedAgua {
    private static final String VERSION = "1";
    public static final SimpleChannel CANAL = NetworkRegistry.newSimpleChannel(new ResourceLocation(Mipack.MODID, "agua"),
            () -> VERSION, VERSION::equals, VERSION::equals);

    private RedAgua() {
    }

    public static void registrar() {
        CANAL.messageBuilder(Estado.class, 0, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(Estado::escribir).decoder(Estado::leer).consumerMainThread(Estado::recibir).add();
        CANAL.messageBuilder(Beber.class, 1, NetworkDirection.PLAY_TO_SERVER)
                .encoder(Beber::escribir).decoder(Beber::leer).consumerMainThread(Beber::recibir).add();
    }

    public static void enviar(ServerPlayer p, Estado e) {
        CANAL.send(PacketDistributor.PLAYER.with(() -> p), e);
    }

    /** agua: 0 a 20; desmayo: ticks que le quedan (y total: cuanto duraba); activa: si hay sed (no en creativo). */
    public record Estado(float agua, int desmayo, int total, boolean activa) {
        void escribir(FriendlyByteBuf b) {
            b.writeFloat(agua);
            b.writeVarInt(desmayo);
            b.writeVarInt(total);
            b.writeBoolean(activa);
        }

        static Estado leer(FriendlyByteBuf b) {
            return new Estado(b.readFloat(), b.readVarInt(), b.readVarInt(), b.readBoolean());
        }

        void recibir(Supplier<NetworkEvent.Context> c) {
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> com.mipack.cliente.ClienteAgua.recibir(this));
        }
    }

    public record Beber() {
        void escribir(FriendlyByteBuf b) {
        }

        static Beber leer(FriendlyByteBuf b) {
            return new Beber();
        }

        void recibir(Supplier<NetworkEvent.Context> c) {
            ServerPlayer p = c.get().getSender();
            if (p != null)
                SistemaAgua.beberDelRio(p);
        }
    }
}
