# Mipack: el mod de Crackatos (Forge 1.20.1)

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
**Arena:** una arena cerrada de unos 30×30 o más, con paredes de 4 bloques o más.

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

## Fotos
En `fotos_en_el_juego/` hay capturas del juego de verdad (Forge 1.20.1 con el mod), tomadas solas durante una pelea de prueba contra un husk.

## Si algo sale mal
- **"Missing mod geckolib":** te falta GeckoLib, o es de otra versión de Minecraft o de otro cargador (tiene que ser Forge 1.20.1).
- **Se ve morado y negro, o invisible:** avísame y mándame el `latest.log` de la carpeta `logs`.
