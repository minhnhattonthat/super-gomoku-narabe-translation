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

-- Game RAM (docs/re/screens.md "RAM map"): byte board $7E1040 + row*16 + col (0 empty, 1 black, 2 white),
-- rebuilt into the word board $0B00 before every win check; cursor col/row $013E/$013F.
-- Poked stones count for the rules and the AI but are not drawn (stones are drawn only when played).
function W.stones(color, cells)
  for _, rc in ipairs(cells) do wr(0x7E1040 + rc[1] * 16 + rc[2], color) end
end
function W.cursor(row, col) wr(0x7E013E, col); wr(0x7E013F, row) end

-- Controller 2 (2P plays white in a 2P free match): one press of BUTTONS ("a", "a+up"). The emulator's port 2 is
-- not configured, so this writes the game's pad-2 words right after its joypad read (80:82AA): $60 new presses,
-- $68 held.
local BIT = { a = 0x0080, x = 0x0040, l = 0x0020, r = 0x0010, b = 0x8000, y = 0x4000, select = 0x2000,
  start = 0x1000, up = 0x0800, down = 0x0400, left = 0x0200, right = 0x0100 }
local pad2 = 0
function W.pad2(spec)
  pad2 = 0
  for name in spec:gmatch("[^+]+") do pad2 = pad2 | assert(BIT[name], name) end
end
L.on_exec(0x8082AA, 0x8082AA, function()
  if pad2 ~= 0 then W.wr16(0x7E0060, pad2); W.wr16(0x7E0068, pad2); pad2 = 0 end
end)

-- Title staff roll: the title loop (81:A9D3) shows table 81:AA12 (g07_09..g07_17) but stops after 2 entries
-- (CMP #4 at 81:A9FB). Feed it every entry in turn and never let it leave the loop.
function W.all_credits()
  local i = 0
  L.on_exec(0x81AA36, 0x81AA36, function() W.wr16(0x7E04F4, i); i = (i + 2) % 18 end)
  L.on_exec(0x81A9F8, 0x81A9F8, function() W.wr16(0x7E04F4, 0) end)
end

-- Hidden "れんじゅ ますたぁ" debug menu (81:811A via stub 81:8002, never called): debug-only runtime patch of
-- the main loop's JSL $81808A (mode menu) at 80:8135 into JSL $818002. ROM file is untouched.
function W.debug_menu()
  local prg = emu.memType.snesPrgRom
  assert(emu.read(0x135, prg) == 0x22 and emu.read(0x136, prg) == 0x8A, "unexpected bytes at 80:8135")
  emu.write(0x136, 0x02, prg)
end

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
