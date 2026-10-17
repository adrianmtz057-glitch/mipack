# Mipack: Crackatos, Khaset, La Bruma, los titanes y los objetos de Velkia (Forge 1.20.1)

## Qué necesitas
1. **Minecraft 1.20.1 con Forge 47.4.10**, la versión que ya tienes.
2. **GeckoLib para Forge 1.20.1**, versión 4.4 o más nueva. El mod se probó con la 4.8.4.
   - Bájalo de Modrinth, busca "GeckoLib" y elige Forge 1.20.1.
   - O bájalo de CurseForge.
3. **`mipack-0.1.0.jar`**, que está en esta misma carpeta.

En esta carpeta también va `geckolib-forge-1.20.1-4.8.4.jar` (GeckoLib es libre, licencia MIT), por si no quieres bajarlo.

Pon los dos `.jar` (GeckoLib y mipack) en la carpeta `mods` de tu instancia. En SKLauncher es la carpeta `.minecraft/mods` del perfil de Forge.

## Cómo sale Crackatos
- **Con el huevo:** en creativo, en la pestaña **Mipack**, está el "Huevo de Crackatos".
- **Con comando:** `/summon mipack:crackatos`
- Para que te ataque tienes que estar en **supervivencia o aventura**; en creativo te ignora.
- Si quieres verlo atacar a otros mobs, pon `-Dmipack.prueba=true` en los argumentos de Java.

## Cómo pelea (versión 2: para muchos jugadores)
**Tamaño:** unos 16 bloques de alto y 32 de largo (con la cola). Necesita una arena grande: de **80×80 o más**, con paredes de **6 bloques o más** (tiene que poder chocar con ellas).

**Reparte el foco:** ya no se clava con uno. Después de cada ataque escoge a otro: le gusta el que más le pega (también al que dispara de lejos) y el que lleva más rato sin que lo persiga. Te ve hasta 96 bloques.

**Estampida:**
- Primero rasca el piso. Mientras tanto **marca en el piso una línea morada** con el camino que va a recorrer, y **a todos los que estén en ese camino los alenta**. Sal del camino a tiempo.
- Luego corre **acelerando** y **no se detiene hasta topar con pared** (o después de 180 bloques). A todo lo que se lleva en el camino le pega, **más fuerte mientras más lleva corriendo** (hasta el triple), y lo avienta de lado.
- Contra la pared se le atoran los cuernos unos 4 segundos (3 en la fase 2). Ahí recibe **el doble de daño**.

**Cornada:** si te quedas pegado a él, levanta los cuernos y te avienta para arriba. **Pisa:** bajo sus patas te hace daño.

**Sacudida (cada 2 o 3 estampidas):** salen púas volando del lomo y caen **muchísimas** del cielo por toda la arena, con su círculo morado (2.5 bloques de radio). Caen en tandas durante unos 3 segundos.
- **Esquirlas de amatista (efecto nuevo):** cada púa que te pega te deja una esquirla clavada. Te quitan vida poco a poco, más rápido por cada nivel (hasta V). **No se quitan con leche ni con el tiempo: solo cuando Crackatos muere.**

**Alzarse y azotar:** se para en dos patas y azota. Sale una **ola** que recorre toda la arena. **Brinca justo cuando te llegue.** Si hay 3 o más juntos cerca de él, lo hace más seguido.

**Fase 2 (mitad de vida):** ruge, **sus cristales empiezan a brillar y latir** y **se rodea de bruma morada**. De la bruma salen **ácaros de amatista** (como endermites, pero más grandes, con una geoda de cristales que brillan en el lomo, colmillos y seis patas; rápidos y de mordida fuerte, a veces dejan esquirla), mientras corre va soltando púas y caen púas sueltas sobre los que estén lejos.

**Golpes:** atraviesan la armadura (los encantamientos de Protección sí cuentan, así que la netherita con Protección IV aguanta pero ya no es inmortal) y **te tiran el escudo** como un hacha. Las flechas le hacen 75 %.

**Vida:** 1500, más 900 por cada jugador que entra a la pelea. Armadura 14. Al morir suelta mucha experiencia, se le caen las esquirlas a todos y se deshacen sus ácaros.

## Dificultad de los jefes (solo operadores)
Cada jefe tiene su nivel: **easy**, **normal** o **hardcore**. Empieza en **normal** y se guarda con el mundo.
- `/khaset difficult <easy|normal|hardcore>`, `/crackatos difficult <...>` y `/bruma difficult <...>` lo cambian.
- `/khaset difficult`, `/crackatos difficult` y `/bruma difficult`, sin nivel, te dicen cuál tiene.
- Solo los operadores pueden usarlos. La respuesta solo te llega a ti y en el juego no se ve en ningún lado: nadie más sabe en qué nivel está.
- Si lo cambias a media pelea, la vida se ajusta y conserva el mismo porcentaje.

**Hardcore** es la pelea como estaba (la de "semana 2"). Los números de las secciones de cada jefe son los de hardcore.

| | easy | normal | hardcore |
|---|---|---|---|
| Vida de los jefes | 60 % | 80 % | 100 % |
| Daño de sus golpes (también serpientes, púas y ola) | 65 % | 80 % | 100 % |
| **Khaset:** tiempo agarrado antes de empezar el sacrificio (más 2.2 s del sacrificio) | 11 s | 7 s | 3 s |
| Khaset: barra para zafarse | zona más ancha, cursor más lento | un poco más fácil | como estaba |
| Khaset: lo que quita cada fallo de la barra | ¼ de tu vida | ⅓ | la mitad |
| Khaset: lo que hay que bajarle para que suelte | 3 % | 4 % | 5 % |
| Khaset: el calor se llena en | 21 min | 17.5 min | 14 min |
| Khaset: frenesí (qué tan rápido se pone) | hasta 1.5× | hasta 1.7× | hasta 1.85× |
| **Crackatos:** aviso de la estampida (rascando) | 3.3 s | 2.5 s | 1.5 s |
| Crackatos: con el camino ya fijo, antes de arrancar | 2 s | 1.3 s | 0.5 s |
| Crackatos: lentitud en el camino marcado | I | II | II |
| Crackatos: tiempo atorado en la pared | +1.5 s | +0.5 s | como estaba |
| **La Bruma:** daño que le entra en forma de niebla | 50 % | 35 % | 25 % |
| La Bruma: lo más que te drena | 4 s | 5 s | 7 s |
| La Bruma: lo que hay que bajarle para que suelte | 3 % | 5 % | 7 % |
| La Bruma: grita cada | ~21 s | ~16 s | ~12 s |
| La Bruma: almas en pena a la vez (fase 2) | hasta 2 | hasta 4 | hasta 8 |

Ahora, aunque te agarre junto al altar, Khaset **se queda parado en el altar con la presa en alto** hasta que se cumple ese tiempo. Mientras, te puedes zafar con la barra o tus amigos te pueden rescatar. Si alguien se le acerca, sigue pisando.

## Khaset, el dios del fuego corrompido (jefe de raid)
**Cómo sale:**
- **Con el huevo:** en la pestaña **Mipack** está el "Huevo de Khaset".
- **Con comando:** `/summon mipack:khaset`.
- **El cristal del sacrificio:** también en la pestaña Mipack. Es una **caja de piedra tallada azteca** (guerreros en relieve, la serpiente ondulada arriba) con el cristal de obsidiana flotando. Úsalo sobre un bloque: queda con el lado largo hacia ti. Ahí acuesta Khaset a sus presas. Solo se quita pegándole en creativo.
- Te ignora en creativo.

**Tamaño:** unos 11 bloques de alto.

**Vida:** 2000, más 1200 por cada jugador que entra a la pelea (en 48 bloques). Con 10 jugadores son 14,000.

**Frenesí:** entre menos vida le queda, **más rápido ataca** (hasta casi el doble) y menos descansa entre ataques. La fase 2 es como la 1, pero más frenética. **Avanza mientras tira tajos y barridos**, y reparte el foco igual que Crackatos.

**Heridas (la leche no las quita):** desangrado I a III (en el III te caes), derribado, aturdido y desorientado.

**Ataques:**
- **Tajos:** combo de 3 golpes que te desangran y te prenden fuego. Si sigues cerca, remata con el corte de piernas.
- **Corte de piernas:** barre el piso avanzando. Te tira de rodillas. Brincando alto se esquiva.
- **Salto del jaguar:** hasta **26 bloques**. Sale un círculo naranja de 7 bloques donde va a caer. Al caer sale **una onda de fuego por el piso**: **brínca** cuando te llegue. En la fase 2 a veces salta dos veces seguidas.
- **Dardos de átlatl:** en abanico (3, luego 5, luego 7) y en la fase 2 también uno a cada quien que esté lejos. Las nubes de veneno corto son grandes (4.5 bloques).
- **Guardia del jaguar:** si le pegan mucho de frente, cruza los brazos. Para golpes **y flechas**, y si le pegas de frente te regresa un contraataque. Pégale por la espalda.
- **Silbato de la muerte:** grita (**ya tiene su sonido**). Aturde y desorienta a todos en 32 bloques que lo vean. **Escóndete detrás de una columna.** Lo usa mucho más seguido y más si te estás alejando.
- **Xiuhcóatl:** invoca **de 2 a 6 serpientes de fuego** (más con más jugadores), más rápidas que tú corriendo. A sus serpientes ya no les hace daño su propio veneno.
- **Para que no se le gane de lejos:** las flechas le hacen 60 %, y si te alejas salta sobre ti o te avienta dardos.

**Captura y sacrificio:**
- Agarra **hasta a dos desde el principio** (derribados o con desangrado II) y los lleva al cristal.
- **Con las manos llenas sigue peleando:** si te acercas, **pisa** y sale una onda de fuego. Mientras sacrifica, **revientan erupciones de fuego** bajo los que estén cerca (círculo rojo: sal de ahí).
- Mientras carga recibe **doble daño**. Si el grupo le baja **el 5 % de su vida**, suelta.
- **Zafarte tú solo (barra nueva):** cuando te agarra sale una barra abajo de la pantalla con un cursor que va y viene. **Haz clic (el botón de pegar) cuando el cursor esté en lo dorado.** Con 3 aciertos te suelta. **Cada fallo te quita la mitad de la vida que tengas** (si tienes 10 corazones pierdes 5, si tienes 4 pierdes 2; en normal ⅓ y en easy ¼).
- **El tótem funciona:** si te sacrifica y tienes tótem, te salva y te suelta.
- Cada sacrificio sube el calor **un 5 %** y él se cura un poco.

**El calor:** sube solo y se llena en unos 14 minutos. 25 %: el agua se evapora. 50 %: deja ceniza ardiendo donde pisa y da más hambre. 75 %: te quemas cada tanto. 100 %: todos se queman sin parar.

**Fases:**
- **Fase 2, la corona rota (50 %):** se le rompen el yelmo y el penacho y sigue igual pero más rápido; los dardos son astillas de obsidiana que queman.
- **Fase 3, el Quinto Sol (20 %):** el calor sube al doble, sacrifica ahí mismo donde captura y **salen del piso guerreros calavera** con penacho y **macuahuitl** de obsidiana (cortan y desangran). Salen más cada 20 segundos. Se deshacen cuando Khaset muere. A veces sueltan su macuahuitl.

**Golpes:** atraviesan la armadura (Protección sí cuenta) y tiran el escudo.

**Arena recomendada:** una plaza de 60×60 o más con columnas (para el silbato) y el altar de un lado o arriba de una pirámide.

## La Bruma negra (jefe)
Un espectro enorme y flaco, hecho de jirones de tela negra, que flota encorvado dentro de su propia bruma, con una garra de hueso estirada.

**Cómo sale:**
- **Con el huevo:** en la pestaña **Mipack** está el "Huevo de La Bruma".
- **Con comando:** `/summon mipack:bruma`.
- Te ignora en creativo. Cuando llega alguien, **grita**.

**Tamaño:** unos 6 bloques de alto. Flota: no pisa el piso y no recibe daño de caída.

**Vida:** 1200, más 700 por cada jugador que entra a la pelea (en 64 bloques). Armadura 4.

**La bruma:**
- A su alrededor todo se oscurece: a los que estén cerca les da **Oscuridad**. Su barra de jefe **oscurece el cielo y trae niebla**.
- **Apaga las luces:** las antorchas y los faroles cercanos se caen (los puedes recoger), y las fogatas y las velas se apagan.
- **En la fase 2** la bruma llega más lejos, apaga más seguido y además da Debilidad.

**Forma de niebla (lo más importante):**
- Casi siempre está hecha de niebla: se ve **translúcida** y **solo le entra una parte del daño** (35 % en normal).
- Toma cuerpo (se ve sólida y le entra todo) en tres casos:
  - mientras ataca, y un par de segundos después;
  - **con fuego:** flechas en llamas, Aspecto ígneo, lava;
  - **con luz fuerte:** las luces que no puede apagar la obligan a tomar cuerpo mientras esté cerca de ellas. Son la piedra luminosa, la linterna de mar, la luz de hongo, las ranaluces y la calabaza iluminada. Si la llevas a tu zona de luz, se vuelve sólida, más lenta, y suelta a quien esté drenando.

**Ataques:**
- **Zarpazo:** echa la garra para atrás y barre lo que tiene enfrente. Te avienta y te deja **Marchitez**.
- **Agarrar y drenar:** se lanza, te agarra con la mano y **te levanta** (no te puedes bajar con shift). Te chupa el alma: te quita vida, te baja el hambre y ella se cura. Te suelta en estos casos:
  - si los demás le bajan **el 5 %** de su vida mientras drena;
  - si hay luz fuerte;
  - si se acaba el tiempo (5 s en normal);
  - si te salva un tótem.

  Al soltarte caes despacio.
- **Grito:** se encoge y grita. A todos los que la vean, en 14 bloques (20 en la fase 2), les hace daño mágico y les da Oscuridad, Lentitud III y Debilidad, además de **congelarlos**. **Detrás de una pared no te alcanza.**
- **Jirones:** si tiene a 2 o más encima, gira sobre sí misma y **azota con las tiras**. Los avienta y les da Marchitez.
- **Atravesar:** se deshace en bruma y **cruza paredes** (no se dibuja ni se le puede pegar), y **aparece detrás de alguien** para atacarlo. Lo hace si te alejas o si se atora.

**Fase 2 (mitad de vida):** se alza y se retuerce. La bruma crece y ataca más rápido. **Salen almas en pena**, vexes que viven 30 segundos y van contra quien ella persigue: 2 más 1 por jugador, hasta 4 en normal. Salen otra vez cada 25 segundos.

**Reparte el foco** igual que los otros jefes.

**Golpes:** el zarpazo y los jirones atraviesan la armadura (Protección sí cuenta) y tiran el escudo.

**Al morir:** se le cae la cabeza y se hunde en su bruma hasta desvanecerse. Se llevan a sus almas. Suelta experiencia, fragmentos de eco y membranas de phantom.

**Para pelear:** lleva **arco con Llama** o espada con **Aspecto ígneo**, y **piedra luminosa o linternas de mar** para poner tu zona de luz. Las antorchas no aguantan. Usa paredes o columnas para cubrirte del grito.

## Los titanes (en construcción)
Criaturas enormes que no pelean ni reciben daño: viven su agenda (caminan, comen, descansan y se quedan mirando a quien se acerca) y se mueven solos por el mapa con el **motor de rutas**. Por ahora está **Candil, el ajolote del lodo** (pantano, unos 27 bloques de largo). Los demás van saliendo de más fácil a más difícil.

**Cómo funcionan:**
- **Siempre existen.** Cuando hay un jugador a menos de unos 160 bloques, el titán aparece donde va. Si todos se alejan, se quita y sigue su camino sin que nadie lo vea. Así, cuando vuelves, lo encuentras en otro lado.
- **Leen el terreno.** El mod guarda un mapa por celdas de 8×8 bloques: la altura del suelo, la de las copas de los árboles, el agua y su hondura, qué hay arriba (arena, nieve, hielo, piedra) y el bioma. Con eso cada titán busca por dónde caber:
  - cuánto puede subir de una celda a otra;
  - qué tan hondo puede vadear;
  - cuánto mide de ancho;
  - qué biomas le gustan y en cuáles no entra.
- **No se atoran.** Si dejan de avanzar o el terreno cambió, vuelven a buscar camino. Pasan entre los árboles como si nada, pero siguen el piso, el agua o las copas.
- El mapa del terreno se llena solo con lo que se va cargando. **En un mapa ya hecho, conviene leerlo una vez** con `/titanes escanear <radio>`: va cargando chunks de a poco y avisa cuando acaba.

**Comandos (operador):**
- `/titanes crear candil`: crea a Candil donde estás.
- `/titanes lista`: dónde está cada uno, si está aquí o virtual, y qué hace.
- `/titanes ir <número>`: te lleva a verlo.
- `/titanes mandar <número> <x> <z>`: que vaya a un punto.
- `/titanes ruta <número>`: muestra con partículas el camino que va a seguir.
- `/titanes escanear <radio>`: lee el terreno alrededor tuyo.
- `/titanes terreno`: cuánto del mapa ya conoce.
- `/titanes quitar <número>`: lo borra.

**Candil:**
- Casi siempre está quieto en el agua, hundido en el lodo con la cabeza al ras. Los nenúfares y los hongos de su espalda y las puntas de sus branquias brillan de noche.
- A ratos se hunde a dormir, atrapa algo o se mueve a otro charco del pantano.
- Solo entra a pantanos, ríos y tierra común (no al mar, al desierto, a la nieve ni a las montañas).

## Los objetos de Velkia
Van en la pestaña **Velkia: objetos** del creativo. Los materiales los van a soltar los animales de cada bioma (todavía no están en el juego: por ahora salen en el creativo o con `/give`).

**Materiales:** colmillo de chacal, aguijón de escorpión, escamas de luz, cuerno de piedra, caparazón de escarabajo, cola de lagarto, branquia de Moruvahn, ceniza, brasa, pluma negra, mura, sal, semilla de musgo, grasa de ballenato, pelaje grueso, quitina y glándula de salamandra.

**Lo que se hace con ellos:**
| Objeto | Receta | Qué hace |
|---|---|---|
| Daga de colmillo | colmillo sobre palo | Rápida; a veces desangra |
| Martillo de cuerno | 3 cuernos arriba, 2 palos abajo | Lento y pesado; avienta lejos |
| Flecha de aguijón (×4) | aguijón, palo y pluma en columna | Alenta al que pica |
| Carne salada | sal + cualquier carne cocida | Llena mucho y quita el efecto de hambre; da un poco de sed |
| Pulpa de cactus (×2) | un cactus | Un trago de agua |
| Fertilizante de musgo (×2) | semilla de musgo + 2 harinas de hueso | Hace crecer todo en un cuadro de 3×3 |
| Runa de Pibble | lapislázuli y oro alrededor de una perla de ender | Te lleva a donde moriste por última vez (se gasta) |
| Varita de Revolthir | 2 varas de blaze, 2 de amatista y polvo de piedra luminosa | Lo que golpea recibe un efecto al azar |
| Varita de Correctar | 2 varas de blaze, 2 cristales de prismarina y cuarzo | Quita los efectos de lo que golpea; clic derecho, los tuyos (cada 30 s) |
| Bomba de brasa (×2) | ceniza + brasa + pólvora | Estalla en fuego sin romper bloques |
| Señuelo de plumas | 3 plumas negras + hilo | Los hostiles de alrededor se olvidan de ti y van a donde cae (12 s) |
| Escudo de escamas | forma de escudo con escamas y una tabla | Dura mucho más que el de madera |
| Escudo de caparazón | forma de escudo con caparazones y una tabla | Ligero: al cubrirte casi no te alentas |
| Cantimplora | 3 cueros + hilo | 3 sorbos de agua; se llena con clic derecho mirando agua |
| Cantimplora reforzada | cantimplora + 2 grasas + hierro | 5 sorbos |
| Antorcha de grasa (×4) | grasa sobre palo | Alumbra como antorcha y el agua no la apaga (se pone bajo el agua) |
| Pedazo de pirámide | oro, brújula y arenisca cortada | Ver abajo |

**Pociones** (en el soporte, con poción rara): cola de lagarto → regeneración; glándula de salamandra → resistencia al fuego; branquia → **branquias** (respiras bajo el agua y ahí adentro te regeneras; con redstone dura más). Todas se pueden hacer arrojadizas.

**Pedazo de pirámide:**
- **En la mano:** con clic derecho te dice hacia dónde y a cuántos bloques queda la pirámide del desierto más cercana. Mientras lo traes, el calor del desierto te sofoca la mitad.
- **Colocado:** en 24 bloques alrededor no aparecen hostiles.

## Las armaduras de Velkia
Cada una tiene **forma propia** (no son recolores) y se hace con la forma de siempre de las armaduras. Cada pieza da su armadura como en Minecraft y **cada pieza suma su efecto**: con una sola ya se nota, con el set completo, todo. Estos efectos no salen en el menú ni hacen zoom: simplemente se sienten.

| Armadura | Material | Dura como | Efecto |
|---|---|---|---|
| Del desierto (egipcia, abierta) | arenisca cortada | menos que hierro | **No sofoca** en el desierto (refresca un poco) |
| De plumas | plumas | oro | Ligereza (hasta +18%) y **caída de pluma**: caes despacio y te haces menos daño |
| De quitina | quitina | entre oro y hierro | Ligereza leve (hasta +6%) |
| De tortuga (pechera, pantalón y botas; el casco es el de Minecraft) | escudos de tortuga | más que hierro | Nadas más rápido (hasta +60%) |
| De pelaje | pelaje grueso | cuero | **Abriga** del frío de las montañas, pero sofoca mucho en el desierto |

## El agua y el frío
- **Barra de agua** arriba de la comida (10 gotas). Siempre baja: **fuera del desierto dura 60 minutos**.
- **En el desierto** dura **35 minutos** sin armadura. La armadura **sofoca** y la acorta, pieza por pieza: el diamante completo la deja a la mitad y la netherita a un tercio, pero **nunca menos de 15 minutos**. Mientras te sofoca, ves el efecto **Sofocación**. De noche no sofoca y a la sombra sofoca la mitad. La armadura del desierto no sofoca.
- **Dónde tomar agua:**
  - la cantimplora;
  - botellas de agua (un buen trago);
  - el río: agachado, con la mano vacía, clic derecho mirando el agua;
  - la lluvia, estando afuera;
  - la pulpa de cactus, la sandía, la leche, los guisos y las bayas.
- **Si llega a cero te desmayas:** los ojos se cierran y todo se ve negro unos 10 segundos. No te puedes mover ni hacer nada, pero **el chat sí se ve y se puede usar**. Los mobs sí te pueden pegar. Despiertas con un poco de agua.
- Los **jugadores nuevos** tienen 10 minutos sin sed. En creativo no hay sed.
- **Frío:** donde nieva, lejos de una fogata, fuego o lava, la comida se va más rápido (efecto **Frío**). La armadura de pelaje lo quita, pieza por pieza.
- Todo se ajusta en `config/mipack-common.toml`: si hay sed, los minutos de cada caso, el mínimo, cuánto dura el desmayo, la gracia de los nuevos y si hay frío.

## El cielo y los efectos
El mod también trae el cielo de Velkia (desierto de día, estrellas y auroras de noche) y un shader ligero (brillo suave, rayos de sol, tono de la hora). Se apagan en `config/mipack-client.toml` (`cielo = false`, `efectos = false`).

## Fotos
En `fotos_en_el_juego/` hay capturas del juego de verdad (Forge 1.20.1 con el mod), tomadas solas durante peleas de prueba contra husks. Las de la versión 2: `crackatos_v2_*` (tamaño, estampida, fase 2 con los cristales encendidos) y `khaset_v2_*` (el altar nuevo, la barra para zafarse, acostado en el altar, el tótem, los guerreros calavera). De cerca: `acaro_amatista_*` y `guerrero_calavera_*`. La Bruma: `bruma_*` (de cerca, la garra, de lado, el grito, el zarpazo, en forma de niebla, la fase 2 de noche y su muerte). Los objetos: `objetos_*` (las cinco armaduras puestas, los escudos y armas en la mano, la antorcha de grasa bajo el agua, el pedazo de pirámide, la barra de agua con la sofocación y el desmayo con el chat).

## Si algo sale mal
- **"Missing mod geckolib":** te falta GeckoLib, o es de otra versión de Minecraft o de otro cargador (tiene que ser Forge 1.20.1).
- **Se ve morado y negro, o invisible:** avísame y mándame el `latest.log` de la carpeta `logs`.
