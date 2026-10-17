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
    private static final String VERSION = "3";
    public static final SimpleChannel CANAL = NetworkRegistry.newSimpleChannel(new ResourceLocation(Mipack.MODID, "khaset"),
            () -> VERSION, VERSION::equals, VERSION::equals);

    private RedKhaset() {
    }

    public static void registrar() {
        CANAL.messageBuilder(Estado.class, 0, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(Estado::escribir).decoder(Estado::leer).consumerMainThread(Estado::recibir).add();
        CANAL.messageBuilder(Barra.class, 1, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(Barra::escribir).decoder(Barra::leer).consumerMainThread(Barra::recibir).add();
        CANAL.messageBuilder(Clic.class, 2, NetworkDirection.PLAY_TO_SERVER)
                .encoder(Clic::escribir).decoder(Clic::leer).consumerMainThread(Clic::recibir).add();
        CANAL.messageBuilder(PegarMano.class, 3, NetworkDirection.PLAY_TO_SERVER)
                .encoder(PegarMano::escribir).decoder(PegarMano::leer).consumerMainThread(PegarMano::recibir).add();
    }

    /**
     * La barra para zafarse de la mano de Khaset (al que va agarrado): el cursor va y viene (un viaje dura 'periodo'
     * ticks desde 'inicio', el tiempo del mundo) y hay que darle cuando pasa por la zona ('zona' es el centro, de 0 a
     * 1, y 'ancho' lo que mide). 'aciertos' de 3. 'fallo': el ultimo clic fallo (para el destello rojo).
     */
    public record Barra(boolean activa, int aciertos, float zona, float ancho, int periodo, long inicio, boolean fallo) {
        public static final Barra NADA = new Barra(false, 0, 0.5f, 0.2f, 20, 0L, false);

        /** Donde va el cursor (0 a 1) en el tiempo 't' del mundo (con fraccion). */
        public float cursor(double t) {
            double f = ((t - inicio) / periodo) % 2.0;
            if (f < 0)
                f += 2.0;
            return (float) (f <= 1.0 ? f : 2.0 - f);
        }

        void escribir(FriendlyByteBuf b) {
            b.writeBoolean(activa);
            b.writeVarInt(aciertos);
            b.writeFloat(zona);
            b.writeFloat(ancho);
            b.writeVarInt(periodo);
            b.writeLong(inicio);
            b.writeBoolean(fallo);
        }

        static Barra leer(FriendlyByteBuf b) {
            return new Barra(b.readBoolean(), b.readVarInt(), b.readFloat(), b.readFloat(), b.readVarInt(), b.readLong(),
                    b.readBoolean());
        }

        void recibir(Supplier<NetworkEvent.Context> ctx) {
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> com.mipack.cliente.BarraZafarse.recibir(this));
        }
    }

    /** El clic del que va agarrado, con donde vio el cursor. */
    public record Clic(float cursor) {
        void escribir(FriendlyByteBuf b) {
            b.writeFloat(cursor);
        }

        static Clic leer(FriendlyByteBuf b) {
            return new Clic(b.readFloat());
        }

        void recibir(Supplier<NetworkEvent.Context> ctx) {
            var jugador = ctx.get().getSender();
            if (jugador != null && jugador.getVehicle() instanceof KhasetEntity k)
                k.clic(jugador, cursor);
        }
    }

    /** El agarrado le pega a Khaset (desde la mano no se le puede apuntar): pega como un golpe normal, con su carga. */
    public record PegarMano() {
        void escribir(FriendlyByteBuf b) {
        }

        static PegarMano leer(FriendlyByteBuf b) {
            return new PegarMano();
        }

        void recibir(Supplier<NetworkEvent.Context> ctx) {
            var jugador = ctx.get().getSender();
            if (jugador != null && jugador.getVehicle() instanceof KhasetEntity k && !EfectosKhaset.sinControl(jugador)) {
                jugador.attack(k);
                jugador.resetAttackStrengthTicker();
                jugador.swing(net.minecraft.world.InteractionHand.MAIN_HAND, true);
            }
        }
    }

    public static void barra(net.minecraft.server.level.ServerPlayer p, Barra b) {
        CANAL.send(PacketDistributor.PLAYER.with(() -> p), b);
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
