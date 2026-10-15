-- Log frame + scanline each time ADDR executes (both bank mirrors), frames FROM..TO, at most MAX lines.
local addr, from, to, max, n = ADDR, FROM or 0, TO or math.huge, MAX or 200, 0
L.on_exec(addr, addr, function()
  if L.frame < from or L.frame > to or n >= max then return end
  n = n + 1
  L.log(string.format("f%d %06X line %d", L.frame, addr, emu.getState()["ppu.scanline"]))
end)
