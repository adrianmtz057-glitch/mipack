# Velkia — nota de traspaso (para retomar sin redescubrir)

Última actualización: 2026-10-12. Rama: `claude/admiring-hamilton-27emzc`.

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
3. ◐ Versión completa a baja resolución + imágenes para revisión ← **AQUÍ**.
4. Mundo jugable de baja resolución con las construcciones.
5. Procesos de detalle.
6. Estructuras: recortar losas y asentar (reubicar ya está hecho).
7. Materiales, biomas, vegetación y pasada 3D.
8. Versión final.

**Al cerrar cada etapa:** renders en perspectiva a altura de jugador y vistas lejanas con niebla (`velkia/validacion.py`).

**Regla del usuario:** si con la próxima corrida la disposición ya coincide con el mapa 2, pasar al mundo jugable (etapa 4) aunque queden detalles; recorrerlo dice más que otra ronda de imágenes.

## Cómo correr

```bash
pip install numpy scipy numba pillow nbtlib tifffile imagecodecs
# etapa 1 completa a 1024² (≈18 min, 4 núcleos) -> salida/etapa1.npz (salida/ está en .gitignore)
python3 -c "import sys; sys.path.insert(0,'.'); from velkia.etapa1 import etapa1; etapa1(1024, out_dir='salida', log_every=50)" > salida/etapa1.log 2>&1
# imágenes de revisión v2 + colocación/asiento + vistas (≈3 min) -> revision/v2_*.png
python3 -m velkia.hacer_revision
# prueba rápida solo de fases tectónicas a 512² (≈1 min): script en el scratchpad (tune.py), equivale a
#   etapa1(512, out_dir=..., solo_tectonica=True) e imprime percentiles de cota por zona + perfil del río
```

## Módulos (`velkia/`)

| Módulo | Qué hace |
|---|---|
| `layout.py` | Mapeo px→bloques (`px2b`: x=520+(px−11)·6.75, z=330+(py−35)·6.6). Zonas, POIs, `RESERVADOS` (Crakatos, Cuarto de Bashi, Fuertes), costa fractal, `jardines_r`, `VIENTO_DUNAS_DEG=-35`. |
| `geology.py` | Provincias, estratos (`COLUMNA_MESETA`), K por zona, peñones (`knobs`), buttes, paredes de granito de los Jardines. |
| `tectonica.py` | Levantamiento P1 (orogenia) y P2 (meseta), precipitación pluvial/árida, topografía inicial, promontorios costeros, salar, Bashi. |
| `lem.py`, `sim.py` | LEM en numba: priority-flood + D8, ley de potencia fluvial con depósito (Yuan 2019), difusión ADI, `breach_chain` (río antecedente), `river_floor` (perfil graduado), `ocean_mask`. |
| `glacier.py` | Hielo de capa delgada (SIA) + erosión por deslizamiento; sobreexcavación limitada a ~25 m. |
| `etapa1.py` | Historia completa: P1 2 Ma → P2 1 Ma (meseta, aridez) → volcán → P3 glaciaciones 30 ka (mar −40) → excavación de los Jardines → P4 Holoceno 10 ka. |
| `rios.py` | Río Velkia: fuente `FUENTE=(3050,1480)`, meandros Howard-Knutson variables por tramo, estuario en la costa (`disenar_rio(..., land, dx)` devuelve `boca`). `AFLUENTES`: Río Salado (al sur de la aldea sur, muere en el salar) y cañón lateral (se une al final del canal de Vieja Velkia). |
| `jardines.py` | Valle en U siguiendo el eje del río: valles colgados, roca aborregada alargada, cadena de lagos, garganta con umbral. |
| `volcan.py` | Volcán por coladas apiladas + piroclastos (altura normalizada). |
| `dunas.py` | Modelo de Werner (probado en pequeño, aún no integrado). |
| `estructuras.py` | `SITIOS` y `Sitio`: transformaciones (complejo rotado 90° antihorario alrededor de (4000,3900), destino (4306,3452)); `canal_vieja_velkia`; `recortar` (losas y entorno → structure_void; sendero viejo de la torre fuera). |
| `ubicacion.py`, `colocar.py` | Cima costera para la torre, búsqueda de ladera (aldea oeste), un `dy` para el complejo, vega de Vieja Velkia, asiento. |
| `asiento.py` | Corte y relleno con borde suave y extensión continua del objetivo (verificado; corregidos escalones de Voronoi y un bug de índices float). |
| `perspectiva.py`, `validacion.py` | Render por trazado de rayos; cámara a suelo+2; detecta vistas tapadas y busca posición. |
| `revision2.py`, `hacer_revision.py` | Imágenes v2: mapa+tabla, comparación con la referencia, acercamientos, perfil del río. |
| `anvil.py` | Escritor 1.20.1 **probado en un servidor real**: carga sin errores, respeta la altura ampliada, calcula la luz, conserva los biomas propios. |
| `mundo.py` | Constructor de chunks: estratos, fluidos y construcciones pegadas con cofres. Sin probar todavía. |
| `preparar_mundo.py` | Esqueleto de la etapa 4: ampliar a 8192², río por tramos planos con orillas, comprobación de fugas. Incompleto. |
| `materials.py` | Bloques por estrato y por código de superficie. |
| `nbt.py`, `schem.py` | E/S de NBT y schematics; rotación de estados de bloque. |

## Cambios en el árbol de trabajo SIN PROBAR (incluidos en el último commit)

1. **`lem.py` — corrección física importante.** El levantamiento subía la superficie pero no la roca (`b`). Todo lo que se elevaba se contaba como sedimento y la difusión aluvial lo aplanaba. Ahora `b += U*dt`.
   Era la causa de que no aparecieran el promontorio de los Fuertes, la depresión de Bashi y las colinas del oeste.
2. **`tectonica.py` — levantamiento de montañas reducido** para compensar la corrección anterior:
   - cordillera de `0.20e-3+1.25e-3·crest` a `0.15e-3+0.80e-3·crest`;
   - Tierras Corrompidas de `1.30e-3` a `0.95e-3`.

   Con la corrección y los valores viejos, a 512² la cordillera llegaba a Y≈524, por encima del techo de 511. **Falta comprobarlo con `tune.py` a 512²**, apuntando a una cumbre máxima ≈ Y 400–460.
3. **`geology.py`** — peñones menos duros (K×0.25 en vez de ×0.08), para que no salgan agujas.

## Resultados de análisis (no repetir)

- **Gran Pirámide**
  - Escalera monumental en la cara OESTE original, que tras la rotación queda en la SUR (mira a la Esfinge).
  - Arena de sotavento en las caras S y E originales, que rotadas quedan E y N.
  - Viento dominante desde el OSO hacia el ENE: `wind_deg=-35` (convención de `dunas.py`).
  - La caja empieza en Y=81 sobre una plataforma de cut_sandstone de Y=81–83; necesita el suelo en Y=80.
- **Aldea fantasma "norte" → aldea oeste**
  - Terrazas suaves: 0,051 bloques/bloque (2,9°), bajando hacia 25,7° desde el este hacia el sur (ESE).
  - Desnivel de 7 bloques y escalones de 1–2.
- **Aldea sur**
  - Pendiente de 1,5–1,85° hacia el SSO; el río queda en su borde S/SO.
  - Agua a Y=93 en el schematic, 1 bloque bajo la terraza más baja.
- **Torre**
  - Base a Y=245, fuste de 15×15 centrado en (7252,3844) original; plaza de radio ~14–19.
  - Sendero viejo: 143 bloques y −41 de desnivel. Ya se recorta; hay que trazar uno nuevo sobre la ladera.
- **Vieja Velkia**
  - Canal de 3 de ancho y 3 de profundidad, agua a Y=87, cruza la ciudad de O a ESE.
  - Lo construido mide 160–403 bloques de ancho perpendicular al canal; el suelo está a Y=88–89.
  - La vega necesita unos 420×565 bloques.
- **Mapa 2**
  - NO hay "árbol especial" al suroeste: el único está en los Jardines y es el árbol de las nueces de los Jardines colgantes.
  - El Cuarto de Bashi está en una depresión romboidal de ~340×360 bloques centrada en px (633,735).
  - Playa de arena negra: península de px (160–300, 1044–1152).
  - Río de lava principal de px (140,838) a la costa en px (372,1135), con 4 ramales.
  - Costa: relación costa/envolvente de 1,84; lo más recortado es el O/SO, lo más liso el E y la playa negra.
  - Jardines: cadena ramificada de lagos; el agua sale por el ESTE.
  - Este: meseta costera de 20–60 bloques sobre el mar.

## Estado de la versión 2 (última corrida, ANTES de la corrección de la roca)

**Bien:**
- valle de los Jardines;
- río desde la cordillera (Y≈251) hasta el estuario (Y=62);
- Río Salado junto a la aldea sur;
- torre sobre el promontorio costero (Y≈161);
- volcán con cráter;
- costa recortada;
- las 6 cámaras despejadas;
- la mesa vista desde el mar.

**Mal (detectado):**
- peñones como agujas;
- Bashi sin depresión, porque se rellena;
- Fuertes sin promontorio;
- sigue el entrante recto del sur, en x≈3460–3520, z≈6640–7700: es el valle de desagüe del salar, ahogado por el mar. Propuesta: un umbral (levantamiento positivo) entre el salar y la costa sur para que el salar quede cerrado;
- la aldea oeste quedó en el borde de los Jardines.

## Pendientes del usuario (revisión de v2) — incorporar en la próxima corrida

1. **Bordes de las construcciones.** El complejo y Vieja Velkia parecen losas con paredes verticales (Thza flota 9 / ent. 6; Velkia flota 11 / ent. 8). El corte y relleno necesita un talud de transición de 1:2 o más suave (en el desierto, de arena), sin ningún escalón alrededor.
   Pista: en `colocar.py`/`asiento.py`, `slope_fill`/`slope_cut` ≤ 0.5. A 8 bloques/celda los desajustes son de malla: comprobar a dx=1.
2. **Vieja Velkia:** la ciudad se diseñó a ambos lados del río. Confirmar que el río cruce por su canal, no por el borde sur. Comparar la cadena del río con `canal_vieja_velkia()` a resolución de bloque.
3. **Aldea oeste:** NO mover la aldea al terreno; preparar el terreno para la aldea. En su punto del mapa 2 (oeste, cerca de la costa) generar una ladera de ~3° con la orientación original (bajada hacia 25,7°). Quitar la búsqueda de ladera en `colocar.py`: dejarla en su POI y modelar el terreno con un objetivo inclinado y bordes suaves.
4. **Jardines:** las paredes son bajas y suaves. Hacerlas más altas y casi verticales, con valles colgados y cascadas cayendo al valle, y el domo con una cara cortada a pico (tipo Half Dome).
5. **Peñones:** en vez de agujas, mesas y buttes de cima plana (capa dura arriba, talud abajo) y algunos domos redondeados. Menos y agrupados.
6. **Volcán:** se ve como un domo suave. Debe tener cráter o caldera, flancos superiores más empinados, barrancos radiales y coladas.
7. **Agua:** en la vista del cañón el río se ve cortado en tramos sueltos. Confirmar que el agua sea continua de la fuente al mar. El render de validación hoy no pinta el río, solo el mar: dibujar el cauce y los lagos en la textura y verificar la continuidad de la cadena.
8. **Montañas:** las cumbres siguen redondeadas. Si es por la resolución, está bien, pero en la etapa de detalle deben salir crestas y picos afilados (erosión térmica con pendiente crítica y glaciar a resolución fina).

## Próximo paso exacto

1. Comprobar la corrección de la roca con `tune.py` a 512². Ajustar solo la escala del levantamiento de montañas si la cumbre máxima pasa de Y≈460.
2. Implementar los pendientes 1, 3, 4, 5 y 6, el umbral del salar y la excavación post‑sedimentaria de Bashi (dolina de colapso tras P4, para que no se rellene).
3. Corrida completa a 1024² (≈18 min). Después `python3 -m velkia.hacer_revision`.
4. Comprobar 2 y 7 con datos.
5. Mandar al usuario las imágenes de construcciones, las vistas en perspectiva y el mapa completo junto a la referencia.
6. Si la disposición coincide, pasar a la etapa 4:
   - `preparar_mundo.py`: ampliar a 8192²; asiento a dx=1; río y lagos con niveles planos por tramos y orillas; superficies y biomas simples; construcciones recortadas con su `dy`; sendero nuevo de la torre;
   - `mundo.construir(...)`;
   - probar en el servidor 1.20.1 (hay que volver a bajar el jar de Mojang al scratchpad y aceptar el EULA solo para la prueba local).

## Trampas conocidas

- `pkill -f "texto"` mata la propia shell si el texto aparece en el comando. Usar el PID.
- No escribir dos corridas al mismo log: se truncó y mezcló una vez.
- En esta máquina (4 núcleos) los workflows corren solo 2 agentes a la vez. Un flujo de 9 agentes tardó 43 min y agotó el límite de sesión: usarlos con moderación.
- A 8 bloques/celda, los "flota/ent." de la tabla de asiento son errores de malla. Lo que vale es la comprobación a dx=1.
- El salar es una cuenca cerrada: el último punto del Río Salado actúa como sumidero, con piso a Y=70.
- Fuera de los Jardines, el cauce principal se fuerza cuesta abajo (`breach_chain`) y es nivel de base para la difusión. El tramo aluvial lleva un piso graduado: 0,5 m sobre el mar en la boca + 0,07 %.
