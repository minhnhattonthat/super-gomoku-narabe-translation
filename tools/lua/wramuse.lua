-- Which low-WRAM bytes ($0000-$1FFF) get written after boot (frame > FROM, default 60)?
-- Writes <out>/wramuse.bin (1 byte per address: 1 = written) at the last frame.
--   emu.py ... --frames N --script tools/lua/wramuse.lua
local used, from = {}, FROM or 60
L.on_write(0x7E0000, 0x7E1FFF, function(addr)
  if L.frame > from then used[addr & 0x1FFF] = true end
end)
L.on_frame(function(f)
  if f == (FRAMES or 0) - 1 then
    local t = {}
    for i = 0, 0x1FFF do t[#t + 1] = used[i] and "\1" or "\0" end
    local fh = io.open(OUT .. "wramuse.bin", "wb"); fh:write(table.concat(t)); fh:close()
    L.log("wramuse written")
  end
end)
