package com.mipack.bichos;

import java.util.List;

/** Generado por taller/bichos/exportar_bichos.py: no se edita a mano. */
public final class BichosDatos {
    public enum Conducta { PASIVO, NEUTRAL, HOSTIL, SAGRADO }

    /** ancho y alto en bloques; golpe y ataqueLargo en ticks; ambientes con su largo en ticks. */
    public record Especie(String id, float ancho, float alto, int vida, float dano, Conducta conducta, boolean vuela,
                          boolean fuego, boolean brilla, boolean ataque, int golpe, int ataqueLargo, boolean correr,
                          String[] ambientes, int[] largos) {
    }

    public static final List<Especie> TODAS = List.of(
            new Especie("cervatillo_musgo", 0.5f, 1.1f, 11, 4.1f, Conducta.SAGRADO, false, false, false, false, 8, 10, true, new String[]{"pastar", "echarse", "juguetear"}, new int[]{60, 80, 32}),
            new Especie("pato_estanque", 0.41f, 0.53f, 8, 3.3f, Conducta.PASIVO, true, false, false, true, 5, 10, true, new String[]{"beber_aves", "acicalarse_aves"}, new int[]{40, 52}),
            new Especie("liebre_dorada", 0.37f, 0.86f, 8, 3.5f, Conducta.PASIVO, false, false, true, true, 5, 10, true, new String[]{"mordisquear"}, new int[]{48}),
            new Especie("toro_arena", 1.18f, 1.51f, 48, 6.6f, Conducta.NEUTRAL, false, false, false, true, 10, 20, true, new String[]{"pastar", "echarse"}, new int[]{60, 80}),
            new Especie("escarabajo_sagrado", 0.81f, 0.31f, 10, 3.8f, Conducta.PASIVO, false, false, false, true, 7, 14, true, new String[]{"moldear_bola"}, new int[]{32}),
            new Especie("fenec", 0.74f, 1.06f, 18, 4.8f, Conducta.PASIVO, false, false, false, false, 8, 10, true, new String[]{"beber_lamiendo", "lamer_cria"}, new int[]{48, 56}),
            new Especie("chacal_ceniza", 1.26f, 1.67f, 59, 7.0f, Conducta.HOSTIL, false, false, true, true, 8, 18, true, new String[]{"beber_lamiendo", "lamer_cria", "sentarse_manada", "aullar"}, new int[]{48, 56, 80, 64}),
            new Especie("dromedario", 0.94f, 1.82f, 38, 6.2f, Conducta.PASIVO, false, false, false, true, 9, 18, true, new String[]{"pastar", "echarse"}, new int[]{60, 80}),
            new Especie("gato_thza", 0.44f, 0.91f, 9, 3.7f, Conducta.PASIVO, false, false, true, true, 6, 12, true, new String[]{"beber_lamiendo", "lamer_cria", "acicalarse_gato"}, new int[]{48, 56, 60}),
            new Especie("escorpion_luz", 0.78f, 0.5f, 12, 4.2f, Conducta.HOSTIL, false, false, true, true, 8, 14, true, new String[]{"cola_escorpion"}, new int[]{40}),
            new Especie("buitre", 0.62f, 0.94f, 13, 4.3f, Conducta.PASIVO, true, false, false, true, 5, 10, true, new String[]{"beber_aves", "acicalarse_aves", "alas_al_sol"}, new int[]{40, 52, 60}),
            new Especie("ballenato_duna", 1.59f, 0.75f, 44, 6.5f, Conducta.HOSTIL, false, false, false, true, 15, 32, true, new String[]{"soplar_arena"}, new int[]{60}),
            new Especie("cangrejo", 0.82f, 0.27f, 10, 3.7f, Conducta.NEUTRAL, false, false, false, true, 7, 12, true, new String[]{"limpiarse_ojos"}, new int[]{48}),
            new Especie("babuino", 0.54f, 0.96f, 12, 4.1f, Conducta.NEUTRAL, false, false, false, true, 7, 14, true, new String[]{"despiojar"}, new int[]{60}),
            new Especie("ibis", 0.6f, 1.01f, 13, 4.4f, Conducta.PASIVO, true, false, false, true, 5, 10, true, new String[]{"beber_aves", "acicalarse_aves", "una_pata"}, new int[]{40, 52, 60}),
            new Especie("hipopotamo", 0.93f, 1.24f, 27, 5.6f, Conducta.NEUTRAL, false, false, false, true, 11, 20, true, new String[]{"pastar", "echarse", "bostezo"}, new int[]{60, 80, 60}),
            new Especie("cocodrilo_luz", 1.52f, 0.48f, 28, 5.6f, Conducta.HOSTIL, false, false, true, true, 7, 28, true, new String[]{"boca_abierta"}, new int[]{60}),
            new Especie("serpiente_rio_seco", 1.09f, 0.25f, 9, 3.7f, Conducta.HOSTIL, false, false, false, true, 9, 16, true, new String[]{"enroscarse"}, new int[]{60}),
            new Especie("cria_varkhum", 1.75f, 0.28f, 23, 5.3f, Conducta.HOSTIL, false, false, false, true, 10, 18, true, new String[]{"enroscarse"}, new int[]{60}),
            new Especie("cria_moruvahn", 0.52f, 0.3f, 8, 3.2f, Conducta.HOSTIL, false, false, true, true, 7, 14, true, new String[]{"flotar_quieto"}, new int[]{60}),
            new Especie("ramita", 1.15f, 0.37f, 16, 4.6f, Conducta.HOSTIL, false, false, false, true, 11, 18, true, new String[]{"mecerse_rama"}, new int[]{60}),
            new Especie("bufalo_terracota", 1.3f, 1.51f, 57, 7.0f, Conducta.NEUTRAL, false, false, false, true, 10, 20, true, new String[]{"pastar", "echarse"}, new int[]{60, 80}),
            new Especie("lagarto_roca", 0.6f, 0.25f, 7, 3.2f, Conducta.PASIVO, false, false, false, true, 5, 10, true, new String[]{"lagartijeo"}, new int[]{48}),
            new Especie("halcon_cobre", 0.41f, 0.56f, 8, 3.3f, Conducta.HOSTIL, true, false, false, true, 9, 16, true, new String[]{"beber_aves", "acicalarse_aves", "ladear_cabeza"}, new int[]{40, 52, 48}),
            new Especie("salamandra_ceniza", 0.63f, 0.25f, 8, 3.3f, Conducta.HOSTIL, false, true, true, true, 9, 16, true, new String[]{"lagartijeo"}, new int[]{48}),
            new Especie("escarabajo_brasa", 0.81f, 0.34f, 10, 3.9f, Conducta.HOSTIL, false, true, true, true, 16, 16, true, new String[]{"frotar_patas"}, new int[]{32}),
            new Especie("lobo_fuego", 1.45f, 1.89f, 60, 7.9f, Conducta.HOSTIL, false, true, true, true, 8, 18, true, new String[]{"beber_lamiendo", "lamer_cria", "sentarse_manada", "aullar"}, new int[]{48, 56, 80, 64}),
            new Especie("cuervo_negro", 0.46f, 0.63f, 9, 3.5f, Conducta.PASIVO, true, false, true, true, 9, 16, true, new String[]{"beber_aves", "acicalarse_aves", "ladear_cabeza"}, new int[]{40, 52, 48}),
            new Especie("murcielago_mura", 1.06f, 0.62f, 20, 5.1f, Conducta.HOSTIL, true, false, true, true, 6, 12, true, new String[]{"colgarse"}, new int[]{60}),
            new Especie("flamenco", 0.51f, 1.5f, 14, 4.4f, Conducta.PASIVO, true, false, false, true, 5, 10, true, new String[]{"beber_aves", "acicalarse_aves", "una_pata"}, new int[]{40, 52, 60}),
            new Especie("lagartija_blanca", 0.48f, 0.25f, 7, 2.8f, Conducta.PASIVO, false, false, false, true, 5, 10, true, new String[]{"lagartijeo"}, new int[]{48}),
            new Especie("garrapata_sal", 0.42f, 0.25f, 6, 2.7f, Conducta.HOSTIL, false, false, false, true, 9, 14, true, new String[]{"esconderse"}, new int[]{48}),
            new Especie("cria_iskarum", 0.77f, 1.35f, 22, 5.2f, Conducta.HOSTIL, false, false, true, true, 10, 20, true, new String[]{"arrancar_con_trompa", "echarse"}, new int[]{48, 80}),
            new Especie("cabra_escarcha", 0.51f, 1.06f, 12, 4.1f, Conducta.NEUTRAL, false, false, false, true, 10, 20, true, new String[]{"pastar", "echarse"}, new int[]{60, 80}),
            new Especie("marmota", 0.49f, 0.59f, 9, 3.6f, Conducta.PASIVO, false, false, false, true, 5, 10, true, new String[]{"mordisquear", "silbar"}, new int[]{48, 52}),
            new Especie("aguila_gris", 0.56f, 0.77f, 11, 4.0f, Conducta.NEUTRAL, true, false, false, true, 9, 16, true, new String[]{"beber_aves", "acicalarse_aves", "alas_al_sol"}, new int[]{40, 52, 60}));

    private BichosDatos() {
    }
}
