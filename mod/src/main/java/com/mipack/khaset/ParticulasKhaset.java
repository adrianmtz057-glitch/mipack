package com.mipack.khaset;

import com.mipack.Mipack;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/** Las particulas de Khaset (texturas en textures/particle, dibujadas por taller/particulas.py). */
public final class ParticulasKhaset {
    public static final DeferredRegister<ParticleType<?>> PARTICULAS = DeferredRegister.create(ForgeRegistries.PARTICLE_TYPES, Mipack.MODID);

    /** La nube de los dardos: verde, sube despacio y se deshace. */
    public static final RegistryObject<SimpleParticleType> VENENO = PARTICULAS.register("veneno", () -> new SimpleParticleType(false));
    /** Gotas del desangrado: caen y salpican. */
    public static final RegistryObject<SimpleParticleType> SANGRE = PARTICULAS.register("sangre", () -> new SimpleParticleType(false));
    /** Chispas: suben titilando, brillan en lo oscuro. */
    public static final RegistryObject<SimpleParticleType> BRASA = PARTICULAS.register("brasa", () -> new SimpleParticleType(false));
    /** Las plumas del penacho cuando se rompe la corona: caen meciendose y se queman. */
    public static final RegistryObject<SimpleParticleType> PLUMA = PARTICULAS.register("pluma", () -> new SimpleParticleType(false));
    /** El rastro de ceniza al pisar con calor. */
    public static final RegistryObject<SimpleParticleType> CENIZA = PARTICULAS.register("ceniza", () -> new SimpleParticleType(false));

    private ParticulasKhaset() {
    }
}
