# Engine patch (asm/main.asm) - hook list

ROM expanded to 1 MB by tools/build.py (header $7FD7 = $0A). New banks: $90 code, $91 text block, $92 font
($92:8000 glyphs, $92:C000 widths, $92:D000 SHTAB shift table). WRAM $7E:1900-$195F (never written by the game
in $1532-$19FF on title, menus, match, dictionary, puzzle routes: tools/lua/wramuse.lua).

| Site | Was | Why |
|---|---|---|
| $81:A756/A75C, A779/A77F, A7A9, A7C4/A7CA, A7F6 | `$83xxxx` table / `#$0083` | text block -> $91 |
| $81:A4E2 | glyph copy at $7C | `JSL vwf_draw` (code $24-$1FF: JP 16x16 as two 8 px halves; $200+: VWF font; 0-$23 -> Latin font; $1A3 ▼ cell-aligned) |
| $81:A4CC | $7C += $20 | `JSL vwf_adv` (after a VWF glyph: VX += width, $7C = next whole cell; else original cell step) |
| $81:A7B3 | LDA $14 / AND #$1F | invalidate VWF cursor sync on every new string |
| $81:A86D | JSR A4E2 / JSR A3CD | single glyph draw, forced resync |
| $81:A5D9 | BEQ $A5E7 | {num}: blank tens digit takes no space |
| $81:A35A | PHP/REP/JSR A3BE | instant draw: redraw cache (menus redraw labels every frame; VWF too slow for that) |
| $81:A3B5 | STZ $91 / STZ $94 | instant draw end: cache valid |
| $80:A0BA | LDX #0 / LDA #0 | text buffer clear: cache invalid |

| $81:A55F | control dispatch | `JML ctrl_hook`: new codes $89 {move} (move no. = $0110+1) and $8A {turn} (group 13 string by $010F bit 0); {var}/{num}/{move}/{turn} draws are never cached |
| $80:943D | per-move caption: digits + 黒/白 single glyphs | redraw g00_02 at pos 0 instead |
| $80:9FA5, $80:9637 | first caption / caption after opening: colour + digit glyphs | skipped |
| $81:B1E6, $80:A242 | single glyph 手 (move limit), 番 (puzzle no.) | code $27F, width 0 |
| draw_fresh | single-glyph draws ($81:A83D) | digits drawn in adjacent cells are joined (no 16 px gaps) |

Gotchas found:
- Never change DB in code that can run while the game's IRQ is armed: its handler writes PPU registers with
  absolute addressing, so DB=$7E sent them to WRAM (lower half of the game screen went green).
- draw8 clobbers $22-$28 (as the original A4E2 did); callers recompute their source pointers, banks included.
- The VWF cursor (VX) is resynced from $7C whenever $7C differs from what vwf_adv left (newline, {sp}, new string).
