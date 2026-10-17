package com.mipack.arena;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** El bloque central de la arena: donde lo pongas, ahi es la arena del jefe que salga cerca. Suelta chispas suaves. */
public final class BloqueCentro extends Block {
    public BloqueCentro(Properties p) {
        super(p);
    }

    @Override
    public void onPlace(BlockState s, Level nivel, BlockPos pos, BlockState antes, boolean mueve) {
        super.onPlace(s, nivel, pos, antes, mueve);
        if (nivel instanceof ServerLevel sl && !antes.is(this))
            Arena.Centros.de(sl).poner(pos, true);
    }

    @Override
    public void onRemove(BlockState s, Level nivel, BlockPos pos, BlockState despues, boolean mueve) {
        if (nivel instanceof ServerLevel sl && !despues.is(this))
            Arena.Centros.de(sl).poner(pos, false);
        super.onRemove(s, nivel, pos, despues, mueve);
    }

    @Override
    public void animateTick(BlockState s, Level nivel, BlockPos pos, RandomSource r) {
        if (r.nextInt(3) == 0)
            nivel.addParticle(ParticleTypes.END_ROD, pos.getX() + 0.2 + r.nextDouble() * 0.6, pos.getY() + 1.05,
                    pos.getZ() + 0.2 + r.nextDouble() * 0.6, 0, 0.02 + r.nextDouble() * 0.03, 0);
    }
}
