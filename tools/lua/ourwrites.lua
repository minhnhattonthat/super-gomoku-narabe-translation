-- Log WRAM writes made by the patch code (PC in bank $90) outside its own variables ($1900-$195F) and the DP
-- temps the original renderer also used. Distinct (pc, addr) only. Optional FROM/TO frame window.
local from, to, seen = FROM or 0, TO or math.huge, {}
local ok = {}
for _, a in ipairs({0x0A, 0x0B, 0x16, 0x17, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x7C, 0x7D, 0x78, 0x79,
  0x91, 0x94}) do ok[a] = true end
L.on_write(0x7E0000, 0x7FFFFF, function(addr)
  if L.frame < from or L.frame > to then return end
  local pc = L.pc()
  if (pc >> 16) & 0x7F ~= 0x10 then return end
  local a = addr & 0x1FFFF
  if (a >= 0x1900 and a < 0x1960) or ok[a] or (a >= 0x2000 and a < 0x4400) or (a >= 0x150 and a < 0x162) then return end
  local key = pc * 0x20000 + a
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d pc=%06X wrote %05X", L.frame, pc, a))
end)
