package com.mipack.objetos;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SimpleWaterloggedBlock;
import net.minecraft.world.level.block.TorchBlock;
import net.minecraft.world.level.block.WallTorchBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;

import javax.annotation.Nullable;

/**
 * La antorcha de grasa del ballenato: alumbra como una antorcha pero el agua no la apaga ni se la lleva (se puede
 * poner bajo el agua).
 */
public final class Antorcha {
    private static final BooleanProperty AGUA = BlockStateProperties.WATERLOGGED;

    private Antorcha() {
    }

    static boolean enAgua(BlockPlaceContext c) {
        return c.getLevel().getFluidState(c.getClickedPos()).getType() == Fluids.WATER;
    }

    public static final class Parada extends TorchBlock implements SimpleWaterloggedBlock {
        public Parada(Properties p) {
            super(p, ParticleTypes.FLAME);
            registerDefaultState(stateDefinition.any().setValue(AGUA, false));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
            b.add(AGUA);
        }

        @Nullable
        @Override
        public BlockState getStateForPlacement(BlockPlaceContext c) {
            BlockState s = super.getStateForPlacement(c);
            return s == null ? null : s.setValue(AGUA, enAgua(c));
        }

        @Override
        public FluidState getFluidState(BlockState s) {
            return s.getValue(AGUA) ? Fluids.WATER.getSource(false) : super.getFluidState(s);
        }

        @Override
        public BlockState updateShape(BlockState s, Direction d, BlockState otro, LevelAccessor nivel, BlockPos pos, BlockPos pos2) {
            if (s.getValue(AGUA))
                nivel.scheduleTick(pos, Fluids.WATER, Fluids.WATER.getTickDelay(nivel));
            return super.updateShape(s, d, otro, nivel, pos, pos2);
        }
    }

    public static final class Pared extends WallTorchBlock implements SimpleWaterloggedBlock {
        public Pared(Properties p) {
            super(p, ParticleTypes.FLAME);
            registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(AGUA, false));
        }

        @Override
        protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {
            super.createBlockStateDefinition(b);
            b.add(AGUA);
        }

        @Nullable
        @Override
        public BlockState getStateForPlacement(BlockPlaceContext c) {
            BlockState s = super.getStateForPlacement(c);
            return s == null ? null : s.setValue(AGUA, enAgua(c));
        }

        @Override
        public FluidState getFluidState(BlockState s) {
            return s.getValue(AGUA) ? Fluids.WATER.getSource(false) : super.getFluidState(s);
        }

        @Override
        public BlockState updateShape(BlockState s, Direction d, BlockState otro, LevelAccessor nivel, BlockPos pos, BlockPos pos2) {
            if (s.getValue(AGUA))
                nivel.scheduleTick(pos, Fluids.WATER, Fluids.WATER.getTickDelay(nivel));
            return super.updateShape(s, d, otro, nivel, pos, pos2);
        }
    }
}
