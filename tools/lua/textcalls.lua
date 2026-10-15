-- Log text-string selections ($81:A7B0): frame, id ($14 -> gNN_ii), position ($12), caller (JSR return).
-- Logs a line only when (id, pos, caller) differs from the previous call; post-process with tools/textmap.py.
local last
local function rd(a) return emu.read(a, emu.memType.snesMemory) end
L.on_exec(0x81A7B0, 0x81A7B0, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = rd(0x7E0000 + sp + 1) | (rd(0x7E0000 + sp + 2) << 8)
  local id = rd(0x7E0014) | (rd(0x7E0015) << 8)
  local line = string.format("g%02d_%02d pos=%02X ret=%04X", id >> 5, id & 31, rd(0x7E0012), ret)
  if line ~= last then
    last = line
    L.log(string.format("f%d %s", L.frame, line))
  end
end)
