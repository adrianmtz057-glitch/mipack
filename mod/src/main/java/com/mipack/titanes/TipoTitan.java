package com.mipack.titanes;

import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * Como es un titan (lo que cambia de uno a otro; el motor es el mismo para todos): su modelo y escala, como se mueve
 * (el perfil de rutas), que tan rapido camina y gira, a que altura vuela o que tan hundido va, sus animaciones y su
 * agenda (que hace segun la hora: comer, beber, descansar, ir a otro lugar).
 *
 * @param id         nombre del modelo y de la entidad (geo/entity/{id}.geo.json)
 * @param escala     cuanto crece el modelo al dibujarse
 * @param ancho      caja de golpes (bloques)
 * @param alto       caja de golpes (bloques)
 * @param perfil     por donde puede ir (motor de rutas)
 * @param velocidad  bloques por tick caminando (o nadando, o volando)
 * @param giro       grados por tick que puede girar
 * @param altitud    para los que vuelan: que tan arriba de las copas; para los demas, cuanto se hunde (negativo)
 * @param paso       bloques que avanza el cuerpo por segundo de la animacion de moverse a velocidad 1 (para que los
 *                   pies no patinen); 0 = la animacion va siempre a velocidad 1
 * @param agenda     que hace despues
 */
public record TipoTitan(String id, float escala, float ancho, float alto, Rutas.Perfil perfil, double velocidad, float giro,
                        double altitud, double paso, Agenda agenda) {

    /** Lo que va a hacer: ir a un lugar (o quedarse) y ahi hacer algo un rato. */
    public record Actividad(Vec3 lugar, Hacer hacer, int ticks) {
    }

    public enum Hacer { QUIETO, COMER, BEBER, DESCANSAR, MIRAR, ESPECIAL }

    @FunctionalInterface
    public interface Agenda {
        /** Lo siguiente (hora: 0 a 24000, la del mundo). 'lugar' null = ahi mismo. */
        Actividad siguiente(Terreno t, TipoTitan tipo, Vec3 donde, Vec3 casa, long hora, RandomSource azar);
    }
}
