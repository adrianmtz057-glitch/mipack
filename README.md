# puente: personajes 3D estilo Minecraft con un prompt

```
"crea a meron"  ->  Groq diseña la ficha  ->  el motor Python arma cubos + pinta la textura  ->  meron.bbmodel
```

- **La IA diseña; Python construye.** Groq no calcula coordenadas (en eso los modelos de lenguaje son malos).
  Escribe una *ficha* JSON: proporciones, estilo de pelo, expresión, prendas, colores, estampados y accesorios.
- **Modelos por piezas, como los de la comunidad:** cuerpo con medidas propias (altura, cabeza, complexión),
  ropa por capas (túnica con abertura real, faldón en paneles que se abren y terminan en tiras, mangas anchas,
  bufanda envolvente, capa inclinada), mechones y rizos inclinados, cuellos en V, correas cruzadas, hojas y plumas.
- **Textura en pixel art:** cada material tiene su paleta (sombras frías, luces cálidas), luz arriba, contorno
  abajo, pliegues, ribetes de contraste y estampados limpios. El `.bbmodel` se abre con todo puesto.
- **Luz horneada en cualquier modelo** (`taller/luz.py`): después de pintar, el motor mira la geometría de todo el
  modelo y le da volumen a la textura: sombra de contacto donde una pieza tapa a otra, sombra proyectada de una luz
  de arriba, brillo en lo que mira a la luz y canto con luz en los bordes. En pasos de la rampa de cada color (la
  sombra se va al frío, la luz al cálido), sin ruido. Lo transparente no tapa. Se apaga con `modelo.luz = False`.
- **Accesorios aparte:** cetro, libro, mochila, brújula, medallón, espada, bastón y farol salen como modelos propios.
- **Esqueleto listo para animar:** huesos `Head`, `Body`, `RightArm`, `LeftArm`, `RightLeg`, `LeftLeg`.
  El faldón va en las piernas para que se mueva al caminar.

## Instalación

Necesitás Python 3.10 o más nuevo. El motor no usa librerías externas. Para la vista previa en PNG:

```
pip install numpy pillow
```

## Uso

```
python puente.py "crea a meron"                 # personaje del lore (no gasta Groq)
python puente.py --todos                        # genera los 8 personajes del lore
python puente.py "meron con armadura de oro"    # variante: Groq modifica la ficha de Meron
python puente.py "un herrero enano de Thza"     # personaje nuevo: Groq escribe la ficha
python puente.py --ficha lore/personajes/meron.json
```

Lo generado queda en `salida/`:

| Archivo | Para qué |
|---|---|
| `meron.bbmodel` | Abrir en Blockbench (Archivo → Abrir) y retocar a mano |
| `meron_vista.png` | Vista previa: frente, 3/4, lado y espalda |
| `accesorios/` | Objetos del personaje como modelos aparte (ej. `khaset_cetro.bbmodel`) |
| `figura/meron/` | Avatar para el mod **Figura**: copiar la carpeta a `.minecraft/figura/avatars/` |

### Clave de Groq

Hay dos opciones:

- Definir la variable de entorno `GROQ_API_KEY`.
- Crear un archivo `groq_key.txt` (al lado de `puente.py`) con la clave.

Ese archivo está en `.gitignore`, así que **nunca lo subas al repo**. Con el plan gratis alcanza: cada
personaje es una sola llamada. Si un modelo no existe o está saturado, el programa prueba el siguiente.
Para elegir el modelo, usá `GROQ_MODEL`.

## Cómo mejorar un personaje

1. Abrí su ficha en `lore/personajes/<nombre>.json`. Las fichas nuevas que crea Groq también se guardan ahí.
2. Cambiá colores, `estilo` de pelo, `largo` de túnica, `patron`, accesorios, etc.
3. Volvé a generar con `python puente.py --ficha lore/personajes/<nombre>.json`.

`lore/mundo.md` es el lore que la IA lee antes de diseñar: agregá ahí mundos, facciones y estilos.

### Qué sabe hacer el motor

| Categoría | Opciones |
|---|---|
| Proporciones | `altura` (20 a 44 px), `cabeza` (0.8 a 1.3), `complexion` (`delgada`, `normal`, `robusta`) |
| Pelo | `rizos`, `puntas`, `lado`, `revuelto`, `largo`, `corto`, `ninguno` (con brillo, mechas y volumen 1 a 3) |
| Cara | ojos de 2 px; expresión `alegre`, `serena`, `seria` o `traviesa`; rubor; `mascara` (rostro cubierto) |
| Ropa | camisa, pantalón, botas (con hebillas), túnica (corta/media/larga, abierta o cerrada, borde en tiras/picos/recto, panel colgante), mangas (ajustadas/anchas/capas), bufanda (pequeña/grande, colas cortas o largas), capa (con capucha), cinturón con bolsas, correas cruzadas, banda, hombreras, guantes (con o sin dedos), brazaletes |
| Estampados | `liso`, `manchas`, `tiras`, `camuflaje`, `paneles`, `estrellas`, `hojas`, `rayas`, `cuadros` |
| Cabeza | laurel, corona, tiara, gafas, plumas, etiquetas flotantes, flor, cuernos, orejas |
| Extras (puestos) | amuletos, cintas, emblema (sol, luna, estrella, hoja, diamante, ojo), bolsa |
| Accesorios (aparte) | cetro, libro, mochila, brújula, medallón, espada, bastón, farol |
| `piezas_libres` | cubos extra que la IA puede agregar para lo que no esté en la lista |

## Estructura

```
puente.py            programa principal
taller/ia.py         Groq -> ficha JSON
taller/ficha.py      formato de la ficha + corrección de lo que la IA invente mal
taller/sastre.py     el personaje por piezas: cuerpo, cara, pelo, ropa y accesorios de cabeza
taller/objetos.py    accesorios como modelos aparte
taller/pintura.py    pintores de materiales en pixel art (tela, metal, cuero, piel, pelo, plumas)
taller/modelo.py     cubos, huesos, atlas de textura y exportación .bbmodel
taller/textura.py    colores, ruido y PNG
taller/vista.py      vista previa (render por software)
lore/                mundo y fichas de personajes
legacy/puente_32.py  la versión anterior, como referencia
```

## Próximos pasos

- **Pose y expresión:** inclinaciones leves de cabeza y brazos, más expresiones de cara.
- **Criaturas:** cuerpos de cuadrúpedo, volador, serpiente, araña y bípedo monstruoso, con el mismo sistema de ficha.
- **Revisión con visión:** la IA mira la vista previa, la compara con la descripción y corrige la ficha.
- **Exportación para ModelEngine**, si los personajes van a ser NPCs en vez de skins de jugador.
