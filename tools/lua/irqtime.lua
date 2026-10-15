-- Scanline of each IRQ ($00:8361) and NMI ($00:820E) entry, and of the NMI handler's exit (RTI), frames FROM..TO.
local from, to = FROM or 0, TO or math.huge
local function sl() return emu.getState()["ppu.scanline"] end
for _, v in ipairs({{0x008361, "irq"}, {0x00820E, "nmi"}}) do
  L.on_exec(v[1], v[1], function()
    if L.frame >= from and L.frame <= to then L.log(string.format("f%d %s line %d", L.frame, v[2], sl())) end
  end)
end
