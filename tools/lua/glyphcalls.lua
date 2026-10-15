-- Log single-glyph draws ($81:A83D): frame, glyph ($14), position ($12), JSR return address. Changes only.
local last
local function rd(a) return emu.read(a, emu.memType.snesMemory) end
L.on_exec(0x81A83D, 0x81A83D, function()
  local sp = emu.getState()["cpu.sp"]
  local ret = rd(0x7E0000 + sp + 1) | (rd(0x7E0000 + sp + 2) << 8)
  local stk = {}
  for i = 3, 8 do stk[#stk + 1] = string.format("%02X", rd(0x7E0000 + sp + i)) end
  local line = string.format("glyph=%03X pos=%02X ret=%04X stack+3=%s", rd(0x7E0014) | (rd(0x7E0015) << 8),
    rd(0x7E0012), ret, table.concat(stk, " "))
  if line ~= last then last = line; L.log(string.format("f%d %s", L.frame, line)) end
end)
