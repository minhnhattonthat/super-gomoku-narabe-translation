-- Log WRAM LO..HI (default $0070-$009F) at frame AT (default 1300).
local lo, hi, at = LO or 0x70, HI or 0x9F, AT or 1300
L.on_frame(function(f)
  if f == at then
    local t = {}
    for a = lo, hi do t[#t + 1] = string.format("%02X", emu.read(0x7E0000 + a, emu.memType.snesMemory)) end
    L.log(string.format("%04X: %s", lo, table.concat(t, " ")))
  end
end)
