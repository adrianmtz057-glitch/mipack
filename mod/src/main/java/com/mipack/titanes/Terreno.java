package com.mipack.titanes;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraftforge.common.Tags;

import java.util.HashMap;
import java.util.Map;

/**
 * El mapa del terreno que leen los titanes para moverse sin atorarse: el mundo en celdas de 8x8 bloques y, de cada
 * una, la altura del suelo (sin hojas), la de las copas (con hojas), el fondo si hay agua, que hay en la superficie y
 * el bioma. Se llena solo con cada chunk que se carga (lo que los jugadores van recorriendo) y con
 * {@code /titanes escanear} (carga chunks de a poco para leer una zona entera, para un mapa ya hecho). Se guarda con
 * el mundo (data/mipack_terreno.dat).
 */
public final class Terreno extends SavedData {
    public static final int CELDA = 8;
    private static final String NOMBRE = "mipack_terreno";

    /** Que hay arriba. */
    public enum Superficie { TIERRA, ARENA, NIEVE, HIELO, PIEDRA, AGUA, LAVA }

    /** El tipo de bioma, en grueso (lo que le importa a un titan). */
    public enum Bioma { OTRO, BOSQUE, JUNGLA, DESIERTO, NIEVE, OCEANO, RIO, PANTANO, LLANURA, MONTANA, CANON }

    /** Una celda leida. 'fondo' == 'suelo' si no hay agua. */
    public record Celda(short suelo, short copas, short fondo, Superficie sup, Bioma bioma) {
        public int profundidad() {
            return this.suelo - this.fondo;
        }

        public boolean agua() {
            return this.sup == Superficie.AGUA;
        }
    }

    private final Map<Long, Celda> celdas = new HashMap<>();

    public static Terreno de(ServerLevel nivel) {
        return nivel.getDataStorage().computeIfAbsent(Terreno::cargar, Terreno::new, NOMBRE);
    }

    public static long clave(int cx, int cz) {
        return ((long) cx << 32) | (cz & 0xFFFFFFFFL);
    }

    public static int celdaDe(double bloque) {
        return Math.floorDiv((int) Math.floor(bloque), CELDA);
    }

    public Celda celda(int cx, int cz) {
        return this.celdas.get(clave(cx, cz));
    }

    public boolean conocida(int cx, int cz) {
        return this.celdas.containsKey(clave(cx, cz));
    }

    public int conocidas() {
        return this.celdas.size();
    }

    public void poner(int cx, int cz, Celda c) {
        this.celdas.put(clave(cx, cz), c);
        this.setDirty();
    }

    /** Lee las celdas de un chunk ya generado (las 4 de 8x8 que tiene), con sus mapas de altura. */
    public void leerChunk(ServerLevel nivel, ChunkAccess chunk) {
        int x0 = chunk.getPos().getMinBlockX(), z0 = chunk.getPos().getMinBlockZ();
        for (int i = 0; i < 16 / CELDA; i++)
            for (int j = 0; j < 16 / CELDA; j++) {
                int lx = i * CELDA + CELDA / 2, lz = j * CELDA + CELDA / 2;
                int suelo = chunk.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, lx, lz);
                int copas = chunk.getHeight(Heightmap.Types.MOTION_BLOCKING, lx, lz);
                int fondo = chunk.getHeight(Heightmap.Types.OCEAN_FLOOR, lx, lz);
                BlockPos arriba = new BlockPos(x0 + lx, suelo, z0 + lz);
                BlockState b = chunk.getBlockState(arriba);
                BlockState abajo = chunk.getBlockState(arriba.below());
                Superficie sup;
                if (b.getFluidState().is(Fluids.WATER) || b.getFluidState().is(Fluids.FLOWING_WATER) || abajo.getFluidState().isSource()
                        && abajo.getFluidState().is(Fluids.WATER))
                    sup = Superficie.AGUA;
                else if (abajo.getFluidState().is(Fluids.LAVA) || b.getFluidState().is(Fluids.LAVA))
                    sup = Superficie.LAVA;
                else if (abajo.is(BlockTags.SAND) || abajo.is(Blocks.RED_SANDSTONE) || abajo.is(Blocks.SANDSTONE))
                    sup = Superficie.ARENA;
                else if (abajo.is(Blocks.SNOW_BLOCK) || b.is(Blocks.SNOW) || abajo.is(Blocks.POWDER_SNOW))
                    sup = Superficie.NIEVE;
                else if (abajo.is(BlockTags.ICE))
                    sup = Superficie.HIELO;
                else if (abajo.is(BlockTags.BASE_STONE_OVERWORLD) || abajo.is(BlockTags.TERRACOTTA))
                    sup = Superficie.PIEDRA;
                else
                    sup = Superficie.TIERRA;
                Holder<Biome> bio = nivel.getBiome(arriba);
                poner(Math.floorDiv(x0, CELDA) + i, Math.floorDiv(z0, CELDA) + j,
                        new Celda((short) suelo, (short) Math.max(copas, suelo), (short) Math.min(fondo, suelo), sup, bioma(bio)));
            }
    }

    public static Bioma bioma(Holder<Biome> b) {
        if (b.is(BiomeTags.IS_OCEAN) || b.is(BiomeTags.IS_DEEP_OCEAN))
            return Bioma.OCEANO;
        if (b.is(BiomeTags.IS_RIVER))
            return Bioma.RIO;
        if (b.is(BiomeTags.IS_BADLANDS))
            return Bioma.CANON;
        if (b.is(BiomeTags.IS_JUNGLE))
            return Bioma.JUNGLA;
        if (b.is(Tags.Biomes.IS_DESERT))
            return Bioma.DESIERTO;
        if (b.is(Tags.Biomes.IS_SWAMP))
            return Bioma.PANTANO;
        if (b.is(Tags.Biomes.IS_SNOWY))
            return Bioma.NIEVE;
        if (b.is(BiomeTags.IS_MOUNTAIN) || b.is(Tags.Biomes.IS_PEAK) || b.is(Tags.Biomes.IS_SLOPE))
            return Bioma.MONTANA;
        if (b.is(BiomeTags.IS_FOREST) || b.is(BiomeTags.IS_TAIGA))
            return Bioma.BOSQUE;
        if (b.is(Tags.Biomes.IS_PLAINS) || b.is(BiomeTags.IS_SAVANNA))
            return Bioma.LLANURA;
        return Bioma.OTRO;
    }

    // ------------------------------------------------------------------ guardar y cargar

    @Override
    public CompoundTag save(CompoundTag tag) {
        // por regiones de 32x32 celdas: cada celda en un int (suelo, copas) y otro (fondo, superficie, bioma)
        Map<Long, int[][]> regiones = new HashMap<>();
        for (Map.Entry<Long, Celda> e : this.celdas.entrySet()) {
            int cx = (int) (e.getKey() >> 32), cz = (int) (long) e.getKey();
            long r = clave(Math.floorDiv(cx, 32), Math.floorDiv(cz, 32));
            int[][] a = regiones.computeIfAbsent(r, k -> new int[2][32 * 32]);
            int i = Math.floorMod(cx, 32) * 32 + Math.floorMod(cz, 32);
            Celda c = e.getValue();
            a[0][i] = ((c.suelo() + 1024) << 16) | (c.copas() + 1024) | 0x80000000;
            a[1][i] = ((c.fondo() + 1024) << 16) | (c.sup().ordinal() << 8) | c.bioma().ordinal();
        }
        ListTag lista = new ListTag();
        for (Map.Entry<Long, int[][]> e : regiones.entrySet()) {
            CompoundTag r = new CompoundTag();
            r.putLong("r", e.getKey());
            r.putIntArray("a", e.getValue()[0]);
            r.putIntArray("b", e.getValue()[1]);
            lista.add(r);
        }
        tag.put("regiones", lista);
        return tag;
    }

    private static Terreno cargar(CompoundTag tag) {
        Terreno t = new Terreno();
        for (Tag x : tag.getList("regiones", Tag.TAG_COMPOUND)) {
            CompoundTag r = (CompoundTag) x;
            long k = r.getLong("r");
            int rx = (int) (k >> 32), rz = (int) k;
            int[] a = r.getIntArray("a"), b = r.getIntArray("b");
            for (int i = 0; i < Math.min(a.length, b.length); i++) {
                if ((a[i] & 0x80000000) == 0)
                    continue;
                int suelo = ((a[i] >> 16) & 0x7FFF) - 1024, copas = (a[i] & 0xFFFF) - 1024;
                int fondo = ((b[i] >> 16) & 0xFFFF) - 1024;
                Superficie s = Superficie.values()[Math.min(Superficie.values().length - 1, (b[i] >> 8) & 0xFF)];
                Bioma bi = Bioma.values()[Math.min(Bioma.values().length - 1, b[i] & 0xFF)];
                t.celdas.put(clave(rx * 32 + i / 32, rz * 32 + i % 32), new Celda((short) suelo, (short) copas, (short) fondo, s, bi));
            }
        }
        return t;
    }
}
