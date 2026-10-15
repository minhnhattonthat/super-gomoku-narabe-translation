# Text

## 1. 16-bit text (all visible Japanese), 16x16 2bpp font

- Font: $88:9000 (file 0x41000), 0x1C0 glyphs. Glyph for code c: `$9000 + ((c & $3F8) << 6) + ((c & 7) << 5)`;
  8 glyphs per $200 band (16 tiles of top halves, then 16 of bottom halves). Table: `tbl/jp.tbl` (built by
  `tools/mktbl_jp.py`, checked with `tools/fontsheet.py --tbl`). Digits 000-009, A-Z 00A-023 (uppercase only),
  kana, ~230 kanji. No space glyph: spaces are `{sp:N}`.
- Renderer: $81:A4B2 reads word at [$70],y ($78 = y). Glyph -> $81:A4E2 copies 16x16 into WRAM buffer
  `$7E:2000 + $7C` ($7C += $20 per glyph, +$100 skip at band end; line = $400 via $88). Buffer is DMA'd to BG3 chr
  each frame (e.g. 7E3400 -> VRAM $7200 on the mode menu).
- Strings: 16-bit LE words ended by $8000. Controls (bit 15; jump table $81:A56D, index = high byte & $0F):
  `80 end, 81 ph (insert group-12 phrase, low byte = index), 82 nl, 83 no-op, 84 var (group-13 string chosen by
  RAM $9A), 85 num (2 digits from $0102/$0103), 86 wait (button, blinking ▼ $1A3), 87 sp:N (N blank cells),
  88 se:XX (JSL $8080D2 with $011D=XX; in dictionary text it steps the board demo)`.
- Block: group table 83:8237 (14 x 16-bit ptrs, bank $83), strings 83:8253-83:A2D7 (file 0x18237-0x1A2D7).
  Id = group << 5 | index; strings found by counting terminators. 409 strings, ~3.5k JP chars.
- Code that hardcodes the text bank/table (all bank $81, file offset = CPU addr):
  - $A7B0 screen text: `LDA $838237,x` @A7C4, `LDA #$0083` @A7CA and @A7F6 (-> $72).
  - $A763 phrase: `LDA $83824F,x` @A779 (group 12), `LDA #$0083` @A77F, @A7A9 (-> $82).
  - $A742 var: `LDA $838251,x` @A756 (group 13), `LDA #$0083` @A75C.
  - Other `LDA #$0083` sites (01289, 01C61, 08254... 0D341) point at palettes/graphics after the block: leave.
- Groups 4 (15-20) and 11 (0-8) + 4 (11, 21-24): password entry grid and 8-kana password strings; likely compared
  with player input -> treat as data until the password screen is understood.

## 2. 8-bit text, 8x8 2bpp font

- Font $88:8000 (file 0x40000), tile = code. ASCII $20-$7E ($40 = ©), hiragana $81-$BD, katakana $C6-$FD
  (JIS X0201 order), $BE/$BF dakuten/handakuten written BEFORE the kana. `$02 XX` control, `$04` end.
  Codec `tools/codec8.py`.
- Tables 83:801A and 83:8022 (script VM $81:97E8 / $81:9837, bank $83). Strings 0x18032-0x18236:
  title (`©1994 NAXAT SOFT`, `PUSH START`), copier warning (English), `VER. 1.66`, a **debug menu**
  (げーむすたーと / れんじゅますたぁ / さうんどてすと / OBJ pattern test / map test / palette...), and unused
  katakana names from another game. Visible text is already English; debug menu stays Japanese unless reached.
