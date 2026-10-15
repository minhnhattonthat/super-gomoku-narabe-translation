-- Log each text-string selection ($81:A7B0): frame, text id ($14 -> gNN_ii), position ($12), caller (JSR return).
-- Distinct (id, caller) pairs only unless ALL=true.
local seen = {}
local function rd(a) return emu.read(a, emu.memType.snesMemory) end
L.on_exec(0x81A7B0, 0x81A7B0, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = rd(0x7E0000 + sp + 1) | rd(0x7E0000 + sp + 2) << 8
  local id = rd(0x7E0014) | rd(0x7E0015) << 8
  local key = id * 65536 + ret
  if ALL or not seen[key] then
    seen[key] = true
    L.log(string.format("f%d g%02d_%02d pos=%02X ret=%04X", L.frame, id >> 5, id & 31, rd(0x7E0012), ret))
  end
end)
