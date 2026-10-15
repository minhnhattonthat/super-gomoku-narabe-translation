# Graphics text survey (Japanese drawn as tiles, not by the text renderer)

Method: `tools/debug/warp.py` states, `probes/ppudump.lua` + `tiles.py map` per enabled BG layer (`work/gfx/<scene>/`,
scratch), `vramfind.py` against the ROM, and a hook on the decompressor to log which block feeds which VRAM address.

## How graphics are stored

- **All screen art is LZSS-compressed.** `vramfind.py` finds no raw tiles for any of the screens below (title, mode
  menu, game panel, certificates). Decompressor: `$80:8D32` (classic Okumura LZSS: 4 KB ring buffer cleared to 0,
  start position `$FEE`), source `[$22]`, packed length `$12`, output `$7F:1012`. Loader `$80:8B98` then DMAs the
  buffer to VRAM (word address in `$14`, pc `$80:8BD5`). Log every block with `work/gfx/lz.lua` (hook on `$80:8D32`).
- All screens run BG mode 1: BG1/BG2 4bpp art, BG3 2bpp = the 16-bit text buffer (`$7E:2000` -> chr `$C000`
  bytes, map `$F800`). Anything Japanese on BG3 is text and is covered by `script/`; everything below is not.

## Japanese in graphics

| What | Screen (warp scene) | Layer | Source block (file offset, packed len -> VRAM word) | Notes |
|---|---|---|---|---|
| Title logo 連珠 (big brush kanji) and スーパー五目ならべ (vertical, pink) | title | OBJ (sprites; absent from BG1-3) | 0x05ABAC len 0xBDE -> OBJ chr $0000 | Logo slides in during the intro. Biggest item: needs an English logo drawn in the same sprite tiles (check OAM layout with `.oam.bin`). |
| `naxat soft` boot logo | (boot, before title) | BG | 0x05B78A len 0x353 -> $2000 | Already Latin, leave. |
| Mode-menu card 設 (options card: kanji 設 in a circle) | mode_menu | BG1 (chr byte $4000, map $B000) | 0x05615A len 0x14E3 -> $2000 | The other three cards are pictures (dragon/tiger = 対局, `???` board = 詰め連珠, open book = 連珠辞典); the book pages carry unreadable pseudo-kanji scribbles, leave. Card captions under the cards (対 局 etc.) are BG3 text. |
| Match-menu cards (board with stones, vortex) | match_menu | BG1 | 0x05E522 len 0xBD0 -> $2000 | No text. Statues on BG2 (0x053ADB). |
| Game side panel icon `投了` (resign) | game_panel_menu | BG2 (chr byte $4000) | loaded with the game screen into BG2 chr: 0x058FB4 (len 0x135 -> $2000), 0x04F52A (len 0x926 -> $2200), 0x048000 (len 0x36B2 -> $2600); which block holds the icons is not pinned down | Opened menu bar: 効果音 (bell), 曲 (lute), song select (notes), 投了 (kanji). |
| Game side panel icons `再` (replay) and `始` (back to start) | game_panel_stones | BG2 | same blocks | Stones bar: 1手前 / 元に戻す (stone + arrow pictures), 再, 始 (kanji). |
| `1P`, `2P`, `COM` labels over the player faces | game_board, puzzle_solving, continue_win | OBJ | 0x060000 len 0x906 -> OBJ $0000 (faces too) | Already Latin (pink 1P, green COM); leave unless the font style matters. |
| Tournament certificate: あなたは / 難関の名人戦を / すべてクリアし / 勝ち抜いた / 栄誉をたたえ / ここに表彰 / いたします + 祝 seal | tournament_victory | BG1 (vertical text, chr byte $4000) | 0x05BDD5 len 0x1264 -> $2000 (frame/background on BG2: 0x0551E5 len 0xF75 -> $4000) | Shown 0x700 frames or until A (`$81:D0EC`). Vertical layout; an English version needs horizontal re-layout in the same frame. |
| Puzzle-clear certificate: あなたは / 難解な / 追い詰め問題を / 解答した / 栄誉をたたえ / ここに表彰 / いたします + 祝 | puzzle_clear | BG1 | same blocks as the tournament certificate (0x05BDD5 / 0x0551E5) | `$81:CE09`, after the last problem of a category with 5+ solved. The category word changes per category (追い詰め / 二手勝ち / 四追勝ち); only 追い詰め was reached (others: poke `$0131` before the last answer, as in `puzzle_clear`). Tilemap source not traced yet. |

## Checked and NOT graphics (text renderer, BG3, ids in screens.md)

名人戦 / 一回戦 / 二回戦 / 決勝戦 headers and `VS` (g01_18, g05_26..29), bracket names, round result lines,
げーむ おーばー (g06_00), 1P/COM win lines, 連珠 辞典 side caption (g05_15/16), puzzle side panel (黒から / 打出し /
四三勝 / 問題 01 番), password grid, options screens, title staff roll (g07_09..17 on the title, BG3), the free-match
settings screen including `VS` and `COM` (g05_26, g03_14).

8-bit font text (title `©1994 NAXAT SOFT` / `PUSH START`, debug menu) is drawn by the 8-bit text system, not graphics.

## Not checked

Sprites other than the logo/labels (cursor hand, runner on the panel, faces: pictures only), the dictionary board
diagrams (pictures), the puzzle-clear certificate for categories 二手勝ち / 四追勝ち, the board styles (木目/桜/富士:
pictures).
