package com.mipack.objetos;

import com.mipack.Mipack;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.LongArrayTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraftforge.event.entity.living.MobSpawnEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import javax.annotation.Nullable;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * El pedazo de piramide de Velkia: en la mano, con clic derecho dice hacia donde y a cuanto queda la piramide mas
 * cercana (y mientras lo traes, el calor del desierto te sofoca la mitad; ver SistemaAgua); colocado, hace una zona
 * de "sol de Velkia" de 24 bloques donde no aparecen hostiles.
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID)
public final class Piramide {
    public static final TagKey<Structure> PIRAMIDES = TagKey.create(Registries.STRUCTURE, new ResourceLocation(Mipack.MODID, "piramides"));
    public static final int RADIO = 24;
    private static final String[] RUMBOS = {"este", "sureste", "sur", "suroeste", "oeste", "noroeste", "norte", "noreste"};

    private Piramide() {
    }

    /** El bloque: una piramide chiquita de arenisca con la punta de oro. */
    public static final class Bloque extends Block {
        private static final VoxelShape FORMA = Shapes.or(Block.box(1, 0, 1, 15, 5, 15), Block.box(4, 5, 4, 12, 10, 12),
                Block.box(6.5, 10, 6.5, 9.5, 14, 9.5));

        public Bloque(Properties p) {
            super(p);
        }

        @Override
        public VoxelShape getShape(BlockState s, BlockGetter g, BlockPos pos, CollisionContext c) {
            return FORMA;
        }

        @Override
        public void onPlace(BlockState s, Level nivel, BlockPos pos, BlockState antes, boolean mueve) {
            super.onPlace(s, nivel, pos, antes, mueve);
            if (nivel instanceof ServerLevel sl && !antes.is(this))
                Zonas.de(sl).poner(pos, true);
        }

        @Override
        public void onRemove(BlockState s, Level nivel, BlockPos pos, BlockState despues, boolean mueve) {
            if (nivel instanceof ServerLevel sl && !despues.is(this))
                Zonas.de(sl).poner(pos, false);
            super.onRemove(s, nivel, pos, despues, mueve);
        }
    }

    /** El objeto: se coloca como bloque, y con clic derecho al aire busca la piramide. */
    public static final class Objeto extends BlockItem {
        public Objeto(Block b, Properties p) {
            super(b, p);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level nivel, Player p, InteractionHand mano) {
            ItemStack s = p.getItemInHand(mano);
            if (!(nivel instanceof ServerLevel sl))
                return InteractionResultHolder.success(s);
            p.getCooldowns().addCooldown(this, 100);
            BlockPos aqui = p.blockPosition();
            BlockPos donde = sl.findNearestMapStructure(PIRAMIDES, aqui, 64, false);
            if (donde == null) {
                p.displayClientMessage(Component.translatable("item.mipack.pedazo_piramide.nada").withStyle(ChatFormatting.GOLD), true);
                return InteractionResultHolder.fail(s);
            }
            double dx = donde.getX() - aqui.getX(), dz = donde.getZ() - aqui.getZ();
            int metros = (int) Math.round(Math.sqrt(dx * dx + dz * dz));
            int k = Math.floorMod((int) Math.round(Math.toDegrees(Math.atan2(dz, dx)) / 45.0), 8);
            p.displayClientMessage(Component.translatable("item.mipack.pedazo_piramide.rumbo", metros,
                    Component.translatable("rumbo.mipack." + RUMBOS[k])).withStyle(ChatFormatting.GOLD), true);
            sl.playSound(null, aqui, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0f, 0.7f);
            return InteractionResultHolder.consume(s);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ObjetosSimples.ayuda(lineas, "item.mipack.pedazo_piramide.ayuda");
        }
    }

    /** Donde hay pedazos de piramide colocados en cada mundo. */
    public static final class Zonas extends SavedData {
        private final Set<Long> lugares = new HashSet<>();

        static Zonas de(ServerLevel nivel) {
            return nivel.getDataStorage().computeIfAbsent(Zonas::cargar, Zonas::new, "mipack_piramides");
        }

        static Zonas cargar(CompoundTag t) {
            Zonas z = new Zonas();
            for (long l : t.getLongArray("lugares"))
                z.lugares.add(l);
            return z;
        }

        void poner(BlockPos pos, boolean hay) {
            if (hay ? lugares.add(pos.asLong()) : lugares.remove(pos.asLong()))
                setDirty();
        }

        boolean cerca(BlockPos pos) {
            for (long l : lugares)
                if (BlockPos.of(l).distSqr(pos) <= RADIO * RADIO)
                    return true;
            return false;
        }

        @Override
        public CompoundTag save(CompoundTag t) {
            t.put("lugares", new LongArrayTag(lugares.stream().mapToLong(Long::longValue).toArray()));
            return t;
        }
    }

    @SubscribeEvent
    public static void aparecer(MobSpawnEvent.FinalizeSpawn e) {
        if (e.getSpawnType() != MobSpawnType.NATURAL || !(e.getEntity() instanceof Enemy))
            return;
        ServerLevel sl = e.getLevel().getLevel();
        if (Zonas.de(sl).cerca(e.getEntity().blockPosition()))
            e.setSpawnCancelled(true);
    }
}
