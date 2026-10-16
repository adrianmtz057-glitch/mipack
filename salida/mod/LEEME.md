# Mipack: Crackatos, Khaset y los titanes (Forge 1.20.1)

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
- **Zafarte tú solo (barra nueva):** cuando te agarra sale una barra abajo de la pantalla con un cursor que va y viene. **Haz clic (el botón de pegar) cuando el cursor esté en lo dorado.** Con 3 aciertos te suelta. **Cada fallo te quita la mitad de la vida que tengas** (si tienes 10 corazones pierdes 5, si tienes 4 pierdes 2).
- **El tótem funciona:** si te sacrifica y tienes tótem, te salva y te suelta.
- Cada sacrificio sube el calor **un 5 %** y él se cura un poco.

**El calor:** sube solo y se llena en unos 14 minutos. 25 %: el agua se evapora. 50 %: deja ceniza ardiendo donde pisa y da más hambre. 75 %: te quemas cada tanto. 100 %: todos se queman sin parar.

**Fases:**
- **Fase 2, la corona rota (50 %):** se le rompen el yelmo y el penacho y sigue igual pero más rápido; los dardos son astillas de obsidiana que queman.
- **Fase 3, el Quinto Sol (20 %):** el calor sube al doble, sacrifica ahí mismo donde captura y **salen del piso guerreros calavera** con penacho y **macuahuitl** de obsidiana (cortan y desangran). Salen más cada 20 segundos. Se deshacen cuando Khaset muere. A veces sueltan su macuahuitl.

**Golpes:** atraviesan la armadura (Protección sí cuenta) y tiran el escudo.

**Arena recomendada:** una plaza de 60×60 o más con columnas (para el silbato) y el altar de un lado o arriba de una pirámide.

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

## El cielo y los efectos
El mod también trae el cielo de Velkia (desierto de día, estrellas y auroras de noche) y un shader ligero (brillo suave, rayos de sol, tono de la hora). Se apagan en `config/mipack-client.toml` (`cielo = false`, `efectos = false`).

## Fotos
En `fotos_en_el_juego/` hay capturas del juego de verdad (Forge 1.20.1 con el mod), tomadas solas durante peleas de prueba contra husks. Las de la versión 2: `crackatos_v2_*` (tamaño, estampida, fase 2 con los cristales encendidos) y `khaset_v2_*` (el altar nuevo, la barra para zafarse, acostado en el altar, el tótem, los guerreros calavera). De cerca: `acaro_amatista_*` y `guerrero_calavera_*`.

## Si algo sale mal
- **"Missing mod geckolib":** te falta GeckoLib, o es de otra versión de Minecraft o de otro cargador (tiene que ser Forge 1.20.1).
- **Se ve morado y negro, o invisible:** avísame y mándame el `latest.log` de la carpeta `logs`.
