-- Oculta el cuerpo vanilla: el modelo ya trae cuerpo propio
vanilla_model.PLAYER:setVisible(false)

-- Khaset (generado por taller/personajes/khaset.py: script_figura)
local m = models.khaset                         -- el nombre del .bbmodel
m.Head.calavera.ojos:setLight(15, 15)           -- ojos de fuego: encendidos tambien de noche
local NX, NZ = -3.20, -8.78                 -- el fin del cuello respecto del pivote de Body
local ARRIBA = 30                               -- grados que puede mirar arriba (el abanico toca el cuello a 35)
local SIGNO_ARRIBA = -1                         -- signo de la rotacion X de la cabeza al mirar arriba (revisar)
local k = 0
function events.tick() k = player:isCrouching() and 1 or 0 end    -- agachado
function events.render(delta)
  -- golpe: Body gira en Y y la calavera tiene que seguir al fin del cuello
  local yb = math.rad(vanilla_model.BODY:getOriginRot().y)
  local c, s = math.cos(yb), math.sin(yb)
  m.Head:setPos(NX * (c - 1) + NZ * s, -2.39 * k, -NX * s + NZ * (c - 1) + 4.30 * k)
  m.RightLeg:setPos(0, 1.64 * k, 2.99 * k)
  m.LeftLeg:setPos(0, 1.64 * k, 2.99 * k)
  -- mirar arriba hasta ARRIBA grados; el abanico contragira lo que gira la cabeza
  local r = vanilla_model.HEAD:getOriginRot()
  local sobra = math.max(0, r.x * SIGNO_ARRIBA - ARRIBA)
  m.Head:setRot(-sobra * SIGNO_ARRIBA, 0, 0)
  m.Head.plumas:setRot(-(r.x - sobra * SIGNO_ARRIBA), -r.y, 0)
end
