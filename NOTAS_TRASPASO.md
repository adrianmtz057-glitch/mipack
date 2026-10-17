# Velkia — nota de traspaso (para retomar sin redescubrir)

Última actualización: 2026-10-16. Rama: `claude/admiring-hamilton-27emzc`.

## Qué es esto

Generador del mapa de Minecraft 1.20.1 "Velkia" (8192×8192 bloques, mar a Y=62, altura
−64…511 por datapack) a partir de:
- `referencia/mapa_referencia_biomas.webp` (mapa 2: disposición y puntos de interés);
- el plan "Nivel 2" del usuario (relieve por procesos físicos);
- las construcciones del ZIP (`referencia/construcciones_originales/`, Sponge v2).

El ZIP NO traía ningún motor de generación de ciudades: los `.schem` se usan tal cual (decisión confirmada).

## Etapas (numeración del usuario)

1. ✓ Digitalizar el mapa.
2. ✓ Motor de erosión (se acepta la calibración; solo se toca lo roto de verdad).
3. ✓ Versión completa a baja resolución + imágenes (v3 enviada: `revision/v3_*`).
4. ✓ Mundo jugable de baja resolución con las construcciones (salida/mundo/Velkia, zip salida/Velkia_v4.zip ~264 MB enviado al usuario). Probado en el servidor 1.20.1: carga sin errores; agua de río/lago, lava, canal de Vieja Velkia y bloques de las construcciones comprobados con comandos; 38 columnas releídas de los .mca coinciden. Sendero nuevo de la torre (897 bloques, pendiente ≤ 0,14). ← **AQUÍ: esperar lo que diga el usuario al recorrerlo**.
5. Procesos de detalle.
6. Estructuras: recortar losas y asentar (hecho lo básico: asiento a 1 bloque con talud 1:2).
7. Materiales, biomas, vegetación y pasada 3D.
8. Versión final.

**Al cerrar cada etapa:** renders en perspectiva a altura de jugador y vistas lejanas con niebla.
Etapa 3: `velkia/validacion.py` (vía `hacer_revision`). Etapa 4: `velkia/validar4.py` (desde los mapas de bloque).

**Regla del usuario:** la disposición de v3 coincide con el mapa 2 → se pasó al mundo jugable aunque queden detalles.

## v1 (rediseño aprobado sobre el lienzo)

Lienzo aprobado: zonas `referencia/zonas_v6b.npy` + ajustes de `velkia/zonas_v1.py` (domos/arena, isla del
volcán, bordes a manchas). Orden acordado: 1 biomas/materiales → 2 ríos con valles (según la altura;
los del sureste no deben verse "partiendo" montañas) → 3 volcán (isla, caldera llena, bocas) → 4 mura
(agujas, lago morado, manantial) → 5 relieves por bioma (domos, terracota, dunas, charcas+palmeras del
salar, charcos de Jardines, Fuertes fuera) → 6 cuevas y minerales sin oro → imagen → reconstruir.
Cada paso se aprueba con imagen; el usuario NO quiere cambios en el world sin aprobación.

- Paso 1 hecho: `python3 -m velkia.biomas_v1` (salida/mundo_datos -> salida/v1_datos, ~45 s).
  Provincias de mundo nuevas DOMOS=7 y BADLANDS=8 (bandas horizontales, materials.BANDAS).
  Datapack: salar con burbujas, agua de la mura morada que daña, bioma velkia:domos.

## Cómo correr (orden)

```bash
pip install numpy scipy numba pillow
# 1) historia erosiva a 1024² (≈13 min) -> salida/etapa1_p4.npz (y p1, p2)
python3 -c "import sys; sys.path.insert(0,'.'); from velkia.etapa1 import etapa1; etapa1(1024, out_dir='salida', log_every=50, modelar=False)"
# 2) modelado final sobre P4 (≈10 s; iterar aquí) -> salida/etapa1.npz
python3 -m velkia.modelado
# 3) imágenes de revisión v3 (≈70 s): asiento a 1 bloque, agua, mapa, acercamientos, perfiles, 12 vistas
python3 -m velkia.hacer_revision v3
# 4) mundo: mapas de bloque (≈2 min) y regiones (≈13 min, 256 regiones, ~1 GB)
python3 -m velkia.etapa4 preparar      # -> salida/mundo_datos/
python3 -m velkia.etapa4 construir     # -> salida/mundo/Velkia/  (o: construir 8,6 8,7 para regiones sueltas)
python3 -m velkia.validar4 vistas      # -> revision/v4_*.png
python3 -m velkia.validar4 regiones    # relee columnas de los .mca y las compara con lo esperado
```
Servidor de prueba: `scratchpad/mc/` (server-1.20.1.jar, eula aceptada para prueba local, `level-name` en
server.properties) y `scratchpad/servidor.py "cmd1" "cmd2"...` (arranca, espera Done, manda comandos, para).

## Módulos (`velkia/`)

| Módulo | Qué hace |
|---|---|
| `layout.py` | px→bloques, zonas, POIs, `RESERVADOS`, costa fractal, `jardines_r`. |
| `geology.py` | Provincias, estratos, K por zona. Ya NO hay peñones cilíndricos (daban agujas). |
| `tectonica.py` | Levantamiento P1/P2 (reducido tras la corrección de la roca), umbral salar–costa sur, salar, Bashi. |
| `lem.py`, `sim.py` | LEM numba. `b += U*dt` (el levantamiento sube la roca). |
| `glacier.py`, `etapa1.py` | Historia P1→P2→volcán→P3→P4. `etapa1(..., modelar=False)` guarda `etapa1_p4.npz`. |
| `modelado.py` | Sobre P4: fuente natural del río (y afluentes), Jardines, volcán joven + río de lava, mesas/buttes/domos en grupos, dolina de Bashi, promontorio de Fuertes, repisa de Crakatos, ladera de 3° de la aldea oeste. Parámetros guardados (`relieves_json`, `aldea_oeste_json`). |
| `jardines.py` | Valle en U tipo Yosemite: paredes de 230 m (75 bloques de ancho), meseta, valles colgados (`cascadas`), domo cortado a pico, roca aborregada, lagos, garganta. |
| `volcan.py` | `build_volcano` (coladas viejas) + `rejuvenecer` (cono, caldera, conos parásitos, barrancos por incisión, coladas jóvenes). |
| `agua.py` | Niveles del río que nunca suben, lagos, cascadas, orillas, comprobación de continuidad (malla gruesa). |
| `colocar.py`, `asiento.py` | Asiento a dx=1: talud 1:2; complejo asentado como UNA huella; dy por la costura (franja de 8 bloques); dentro de la huella el terreno baja a la base del schematic (trae su suelo); evaluación final + `talud_anillo`. |
| `hacer_revision.py`, `revision2.py`, `validacion.py` | Imágenes de revisión (v3) y vistas (con agua, lava y construcciones). |
| `etapa4.py` | `preparar`: terreno de bloque, mar, río/afluentes por niveles enteros con orillas, lagos, lava, sellado, superficies/biomas, construcciones exportadas (`estructuras/*.schem` + `estructuras.json`). `construir`: llama a `mundo.construir`. |
| `mundo.py`, `anvil.py` | Escritor de chunks 1.20.1 (probado en servidor real). Corregido: estratos con cota sobre el mar (`ys - SEA`). |
| `validar4.py` | Vistas desde los mapas de bloque a 2 bloques/celda y relectura de los .mca. |

## Estado v3 / mundo (datos)

- Cumbre máx. Y≈406 (Corrompidas, Crakatos); la cordillera ~Y 378. Río: fuente Y≈159 → mar, 1826–1863 celdas, 0 huecos, 0 subidas, 0 agua colgada; cascada de 56 m al entrar a los Jardines.
- Jardines: fondo Y≈82, lagos a Y=81, meseta Y≈312, domo ~Y 410.
- Volcán: borde de caldera Y≈347, fondo Y≈262, cono interior con lago de lava; río de lava NO y SE con 3 ramales.
- Construcciones (dy): complejo +8, Jardines colgantes +1, Vieja Velkia −22 (canal a Y=65), aldea oeste −31, aldea sur −27, torre +9 (desplazada −50,+50 a la cima costera, Y≈254). Borde: flota 0 / ent. 0 en las 8.
- Vieja Velkia: el río cruza por su canal (6 bloques de media del eje, 13 máx.); dentro de la huella el agua la pone el schematic.
- Mundo: mar 35,5 % del mapa; fugas de agua 0 (fuera de huellas y cascadas).

## Pendientes conocidos (siguientes etapas)

- Dunas (dunas.py, Werner) sin integrar; Mar de Dunas hoy es arena lisa. Viento OSO→ENE (`VIENTO_DUNAS_DEG=-35`).
- Arena que entierra en parte Vieja Velkia (no la roca).
- Cascadas de los valles colgados: hoy solo geometría (y en el render); en el mundo no hay arroyos en ellos.
- Playa de arena negra: península px (160–300, 1044–1152) aún no modelada aparte (hay arena negra en la costa volcánica).
- Montañas: crestas y picos afilados en la etapa de detalle (erosión térmica + glaciar fino).
- Vegetación, biomas finos, pasada 3D (arcos, cuevas, extraplomos).
- Talud p99: Jardines colgantes 0,90 (sin localizar: ¿sendero estrecho o lagos?), torre 0,73 (probablemente la ladera natural de la cima), Vieja Velkia 1,24 (paredes de la vega del cañón, a propósito).

## Trampas conocidas

- `pkill -f`/`pgrep -f "texto"` se encuentran a sí mismos (el texto está en el propio comando). Usar el PID guardado.
- No escribir dos corridas al mismo log.
- En esta máquina (4 núcleos) los workflows corren 2 agentes a la vez; usarlos con moderación.
- La cabecera de un cauce forzado (`fixed_rec`) recibe muy poco caudal y se queda como cresta: `modelado.fuente_natural` la corrige (no recalibrar por eso).
- A 8 bloques/celda los "flota/ent." son errores de malla: lo que vale es el asiento a dx=1 (hacer_revision/etapa4 ya lo hacen).
- El aviso `key missing: DragonFight` del servidor es inocuo.
