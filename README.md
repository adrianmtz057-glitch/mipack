# puente: personajes 3D estilo Minecraft con un prompt

```
"crea a meron"  ->  Groq diseña la ficha  ->  el motor Python arma cubos + pinta la textura  ->  meron.bbmodel
```

- **La IA diseña; Python construye.** Groq no calcula coordenadas (en eso los modelos de lenguaje son malos).
  Escribe una *ficha* JSON: estilo de pelo, expresión, prendas, colores, estampados y accesorios.
  El motor la convierte en un player de Minecraft (Steve) con pelo, ropa y accesorios en relieve.
- **La textura viene pintada y aplicada.** Cada píxel se pinta según su lugar en el cuerpo
  (manchas en la tela, ribetes, pliegues, estrellas...). El `.bbmodel` se abre en Blockbench con todo puesto.
- **Esqueleto listo para animar:** huesos `Head`, `Body`, `RightArm`, `LeftArm`, `RightLeg`, `LeftLeg`.
  La falda va en las piernas para que se mueva al caminar.

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
| Pelo | `rizos`, `puntas`, `lado`, `revuelto`, `largo`, `corto`, `ninguno` (con brillo, mechas y volumen 1 a 3) |
| Cara | ojos de 2 px; expresión `alegre`, `serena`, `seria` o `traviesa`; rubor; `mascara` (rostro cubierto) |
| Ropa | camisa, pantalón, botas, túnica (corta/media/larga, abierta o cerrada), mangas (ajustadas/anchas), bufanda (pequeña/grande, con colas), capa (con capucha), cinturón, banda cruzada, hombreras, guantes, brazaletes |
| Estampados | `liso`, `manchas`, `paneles`, `estrellas`, `hojas`, `rayas`, `cuadros` |
| Cabeza | laurel, corona, tiara, gafas, plumas, etiquetas flotantes, flor, cuernos, orejas |
| Extras | libro, amuletos, cintas, emblema (sol, luna, estrella, hoja, diamante, ojo), bolsa, espada, bastón |
| `piezas_libres` | cubos extra que la IA puede agregar para lo que no esté en la lista |

## Estructura

```
puente.py            programa principal
taller/ia.py         Groq -> ficha JSON
taller/ficha.py      formato de la ficha + corrección de lo que la IA invente mal
taller/personaje.py  cuerpo, pelo (vóxeles), ropa y accesorios
taller/modelo.py     cubos, huesos, atlas de textura y exportación .bbmodel
taller/textura.py    colores, ruido y PNG
taller/vista.py      vista previa (render por software)
lore/                mundo y fichas de personajes
legacy/puente_32.py  la versión anterior, como referencia
```

## Próximos pasos

- **Criaturas:** cuerpos de cuadrúpedo, volador, serpiente, araña y bípedo monstruoso, con el mismo sistema de ficha.
- **Revisión con visión:** la IA mira la vista previa, la compara con la descripción y corrige la ficha.
- **Exportación para ModelEngine**, si los personajes van a ser NPCs en vez de skins de jugador.
