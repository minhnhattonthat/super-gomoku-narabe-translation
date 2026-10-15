-- For frames FROM..TO and scanlines LO..HI: at each IRQ entry ($00:8361) log the scanline, H counter and the
-- interrupted PC (pushed on the stack: P, PCL, PCH, PBR).
local from, to, lo, hi = FROM or 0, TO or math.huge, LO or 0, HI or 261
local function rd(a) return emu.read(a, emu.memType.snesMemory) end
L.on_exec(0x008361, 0x008361, function()
  if L.frame < from or L.frame > to then return end
  local s = emu.getState()
  local line = s["ppu.scanline"]
  if line < lo or line > hi then return end
  local sp = s["cpu.sp"]
  local pc = rd(0x7E0000 + sp + 2) | rd(0x7E0000 + sp + 3) << 8 | rd(0x7E0000 + sp + 4) << 16
  L.log(string.format("f%d line %d h %d pc %06X", L.frame, line, s["ppu.cycle"] or -1, pc))
end)
