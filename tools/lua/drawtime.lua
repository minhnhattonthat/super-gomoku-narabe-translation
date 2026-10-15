-- Scanlines spent in the instant text draw ($81:A3A0 select .. $81:A3BC exit), frames FROM..TO.
local from, to, t0 = FROM or 1150, TO or 1160, nil
local function sl() local s = emu.getState(); return s["ppu.scanline"], s["ppu.frameCount"] end
L.on_exec(0x81A3A0, 0x81A3A0, function() if L.frame >= from and L.frame <= to then t0 = { sl() } end end)
L.on_exec(0x81A3BC, 0x81A3BC, function()
  if t0 then
    local s, fc = sl()
    L.log(string.format("f%d start=%d end=%d frames+%d", L.frame, t0[1], s, fc - t0[2]))
    t0 = nil
  end
end)
