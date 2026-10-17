package com.mipack;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

/** Los sonidos propios (assets/mipack/sounds.json; los .ogg los hace taller/sonidos.py). */
public final class SonidosMipack {
    public static final DeferredRegister<SoundEvent> SONIDOS = DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, Mipack.MODID);

    /** El silbato de la muerte: un grito de viento que aturde. */
    public static final RegistryObject<SoundEvent> SILBATO = sonido("khaset.silbato");
    /** Khaset ruge (al saltar, al pisar, al romperse la corona). */
    public static final RegistryObject<SoundEvent> RUGIDO = sonido("khaset.rugido");
    /** El sacrificio: el latido y el fuego del cristal. */
    public static final RegistryObject<SoundEvent> SACRIFICIO = sonido("khaset.sacrificio");

    private SonidosMipack() {
    }

    private static RegistryObject<SoundEvent> sonido(String nombre) {
        return SONIDOS.register(nombre, () -> SoundEvent.createVariableRangeEvent(new ResourceLocation(Mipack.MODID, nombre)));
    }
}
