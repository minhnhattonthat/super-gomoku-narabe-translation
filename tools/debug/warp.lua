-- Debug-tool driver hooks (used by tools/debug/warp.py; appended after emu.py's driver).
-- Globals set by warp.py:
--   ACTS = { {frame, kind, addr, val}, ... }  kind "poke" (write once), "hold" (write every frame from then on),
--          "lua" (addr = Lua source run once at that frame). Frames count from cold boot.
--   MARK = frame where the scene's own steps start: text ids are re-logged from there.
-- Logs "T f<frame> gNN_ii [screen|phrase|var]" the first time each text id is drawn (again after MARK).
local function rd(a) return emu.read(a, emu.memType.snesMemory) end
local function wr(a, v) emu.write(a, v, emu.memType.snesMemory) end
W = { rd = rd, wr = wr }  -- for "lua" acts
function W.wr16(a, v) wr(a, v & 0xFF); wr(a + 1, (v >> 8) & 0xFF) end
function W.rd16(a) return rd(a) | (rd(a + 1) << 8) end

local seen = {}
local function text(g, i, kind)
  local key = g * 32 + i
  if not seen[key] then
    seen[key] = true
    L.log(string.format("T f%d g%02d_%02d %s", L.frame, g, i, kind))
  end
end
-- $81:A7B0 screen string, id in $14
L.on_exec(0x81A7B0, 0x81A7B0, function()
  local id = W.rd16(0x7E0014)
  text(id >> 5, id & 31, "screen")
end)
-- $81:A761 var (group 13 + X/2, index $0A); $81:A782 phrase (group 12 + X/2, index $0A)
L.on_exec(0x81A761, 0x81A761, function()
  text(13 + (emu.getState()["cpu.x"] >> 1), W.rd16(0x7E000A), "var")
end)
L.on_exec(0x81A782, 0x81A782, function()
  text(12 + (emu.getState()["cpu.x"] >> 1), W.rd16(0x7E000A), "phrase")
end)

local holds = {}
L.on_frame(function(f)
  if MARK and f == MARK then seen = {}; L.log("MARK f" .. f) end
  for _, a in ipairs(ACTS or {}) do
    if a[1] == f then
      if a[2] == "poke" then wr(a[3], a[4])
      elseif a[2] == "hold" then holds[a[3]] = a[4]
      elseif a[2] == "lua" then assert(load(a[3]))()
      end
      L.log(string.format("ACT f%d %s %s %s", f, a[2], tostring(a[3]), tostring(a[4])))
    end
  end
  for addr, v in pairs(holds) do wr(addr, v) end
end)
