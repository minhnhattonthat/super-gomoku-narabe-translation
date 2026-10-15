-- Log the CPU PC every frame in FROM..TO (defaults 1100..1110): finds hangs.
local from, to = FROM or 1100, TO or 1110
L.on_frame(function(f)
  if f >= from and f <= to then
    local s = emu.getState()
    L.log(string.format("f%d pc=%02X%04X a=%04X x=%04X y=%04X", f, s["cpu.k"], s["cpu.pc"], s["cpu.a"], s["cpu.x"], s["cpu.y"]))
  end
end)
