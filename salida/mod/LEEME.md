# Mipack: Crackatos y Khaset (Forge 1.20.1)

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

## Cómo pelea
**Tamaño:** unos 10 bloques de alto y 21 de largo (con la cola).

**Arena:** una arena cerrada de unos 50×50 o más, con paredes de 6 bloques o más.

**Al verte:** ruge y luego te acecha caminando hacia ti.

**Embestida:**
- Primero rasca el piso con la cabeza baja (ese es el aviso) y luego fija la dirección y corre en línea recta.
- **Si la esquivas** y se estrella con la pared, se le atoran los cuernos unos 4 segundos. Ahí recibe **el doble de daño**.
- **Si te pega**, te avienta lejos: mucho daño, más el de la caída.
- Al caminar y al correr **pisa**: si estás bajo sus patas, te hace daño.

**Cornada:** si te quedas pegado a él, levanta los cuernos y te avienta para arriba. Si llevas mucho rato cerca, también te embiste de cerca.

**Sacudida (cada 2 o 3 embestidas):**
- Se queda quieto, se sacude y le salen púas volando del lomo.
- Luego aparecen **círculos morados** de 2 bloques de radio en el piso, sobre ti y alrededor. Se van llenando, y cuando se llenan cae una púa del cielo y explota. **Sal del círculo.**

**Alzarse y azotar:**
- Se para en dos patas y azota el piso.
- Sale una **ola** que recorre toda la arena levantando los bloques del piso. Los bloques son solo efecto: el piso no se rompe. Las paredes y los pilares la frenan.
- Si la ola te agarra parado en el piso, te avienta. **Brinca justo cuando te llegue.**

**Segunda fase (menos de la mitad de vida):** corre más rápido, caen más púas y después de cada sacudida se alza y azota.

**Datos:** 600 de vida (300 corazones) y armadura 10. Al morir hace su animación y suelta mucha experiencia.

## Khaset, el dios del fuego corrompido (jefe de raid)
**Cómo sale:**
- **Con el huevo:** en la pestaña **Mipack** está el "Huevo de Khaset".
- **Con comando:** `/summon mipack:khaset`.
- **El cristal del sacrificio:** también en la pestaña Mipack. Úsalo sobre un bloque y se pone mirando hacia ti. Es a donde Khaset lleva a sus presas. Solo se quita pegándole en creativo.
- Como Crackatos, te ignora en creativo.

**Tamaño:** unos 11 bloques de alto. Con el brazo estirado barre unos 5 a 6 bloques alrededor.

**Vida:** 300, más 150 por cada jugador que entra a la pelea (en 48 bloques).

**Su estilo es de guerrero jaguar:** no busca matarte, sino herirte, tirarte y capturarte para el sacrificio.

**Heridas (efectos nuevos; la leche no los quita):**
- **Desangrado I a III:** te quita vida cada tanto, te alenta y la pantalla late en rojo. En el III te caes.
- **Derribado:** de rodillas, sin poder moverte ni pegar. En ese estado te puede capturar.
- **Aturdido:** te tapas los oídos, sin moverte ni pegar.
- **Desorientado:** la cámara se mece y se tuerce.

**Ataques:**
- **Tajos:** combo de 3 golpes. Cada uno te desangra y te prende fuego.
- **Corte de piernas:** se agacha, echa el brazo atrás y barre el piso. Te tira de rodillas y te desangra 2 niveles. Brincando alto se esquiva.
- **Salto del jaguar:** se agacha, sale un círculo naranja donde va a caer y cae sobre el grupo. Si te cae cerca, te tira.
- **Dardos de átlatl:** se arranca una pluma del penacho y te la avienta. Donde pega deja una nube de veneno corto (2.5 s por cada vez que te toca).
- **Guardia del jaguar:** si le pegan mucho de frente, cruza los brazos. Si le pegas de frente mientras está así, te regresa un contraataque. Mejor pégale por la espalda.
- **Silbato de la muerte:** echa la cabeza atrás y grita. Aturde y desorienta a todos los que lo vean. **Escóndete detrás de una columna.**

**Captura y sacrificio:**
- Agarra a un jugador **derribado o con desangrado II**, lo levanta y lo aprieta, y camina al cristal. Si el cristal está arriba (en la pirámide), salta.
- **Mientras carga a alguien recibe doble daño.** Si el grupo le baja suficiente vida, lo suelta. El que está atrapado también puede pegarle, pero cuenta poco.
- En el cristal lo acuesta en la piedra, le saca el corazón y lo ofrece al cristal. Cada sacrificio sube el calor un 15 % y él se cura un poco.

**El calor (la segunda barra):** sube solo y se llena en unos 10 minutos. Las pociones de resistencia al fuego no lo quitan.
- **25 %:** el agua se evapora cerca de él.
- **50 %:** donde pisa queda ceniza ardiendo y da más hambre.
- **75 %:** te quemas cada tanto.
- **100 %:** todos se queman sin parar, cada vez más fuerte.

**Fases:**
- **Fase 2, la corona rota (50 %):** se le rompen el yelmo y el penacho (salen volando las plumas quemándose). Las brasas arden más, puede capturar a dos a la vez, avienta tres astillas de obsidiana en vez de un dardo e invoca a la **Xiuhcóatl**, la serpiente de fuego. La serpiente te persigue unos 9 segundos, muerde, quema y deja fuego (40 de vida, se le puede matar).
- **Fase 3, el Quinto Sol (20 %):** el calor sube 3 veces más rápido y sacrifica ahí mismo donde captura, así que el rescate dura muy poco.

**Arena recomendada:** una plaza de unos 60×60 con columnas (para el silbato) y el cristal del sacrificio de un lado o arriba de una pirámide.

**Sonidos:** por ahora usa sonidos de Minecraft; los suyos van después.

## El cielo y los efectos
El mod también trae el cielo de Velkia (desierto de día, estrellas y auroras de noche) y un shader ligero (brillo suave, rayos de sol, tono de la hora). Se apagan en `config/mipack-client.toml` (`cielo = false`, `efectos = false`).

## Fotos
En `fotos_en_el_juego/` hay capturas del juego de verdad (Forge 1.20.1 con el mod), tomadas solas durante peleas de prueba contra husks (los `khaset_*` son de Khaset).

## Si algo sale mal
- **"Missing mod geckolib":** te falta GeckoLib, o es de otra versión de Minecraft o de otro cargador (tiene que ser Forge 1.20.1).
- **Se ve morado y negro, o invisible:** avísame y mándame el `latest.log` de la carpeta `logs`.
