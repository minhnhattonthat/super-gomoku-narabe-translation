-- Trace the 16-bit string reader ($81:A4B9, after LDA [$70],y): frame, $78 index, word read. Frames FROM..TO.
local from, to = FROM or 0, TO or math.huge
L.on_exec(0x81A4B9, 0x81A4B9, function()
  if L.frame < from or L.frame > to then return end
  local s = emu.getState()
  L.log(string.format("f%d y=%04X a=%04X", L.frame, s["cpu.y"], s["cpu.a"]))
end)
