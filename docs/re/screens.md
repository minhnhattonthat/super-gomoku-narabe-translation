# Screens: debug-tool scenes, text ids per screen, text areas

Debug tool (phase 2): `tools/debug/warp.py` + `tools/debug/scenes.txt` + `tools/debug/warp.lua`.

```
python -X utf8 tools/debug/warp.py --list                         # scene names + one-line descriptions
python -X utf8 tools/debug/warp.py game_win [--rom build/gomoku_en.sfc] [--out DIR] [--then "8 a;60 -"]
python -X utf8 tools/debug/warp.py --all [--rom ROM] [--jobs 3]   # every scene, 3 at a time (~15 min)
```

Each run boots cold, plays the scene's route (its `base:` chain first) and pokes, and writes `DIR/sheet.png` (shots of
the scene's own steps), `final.png`, `log.txt`, `texts.txt` (text ids drawn during the scene's own steps, first frame
each) and the savestate `work/states/<scene>.mss` (other ROMs: `work/states/<rom name>/<scene>.mss`). Default DIR
`work/warp/<scene>`, `--all` uses `work/warp/<rom name>/<scene>`. Text ids are logged by hooks on the text code
(`$81:A7B0` screen string, `$81:A761` var, `$81:A782` phrase), so they work on translated builds too.

Verified 2026-10-15: all 78 scenes reach their screen from a cold boot on `rom/orig.sfc` and on `build/gomoku_en.sfc`
(same text ids per scene, apart from phrase ids the English text no longer uses and the two random picks noted below).

## RAM and code map (found for the debug tool)

| Address | Meaning |
|---|---|
| `$04F4` | mode-menu result (0 対局, 1 詰め連珠, 2 連珠辞典, 3 オプション; main loop `80:8139` dispatches via table `80:8143`), also a generic frame counter in screens |
| `$5E` / `$60`, `$66` / `$68` | pad 1 / pad 2 new presses, held (written at `80:828C..82A8`); the player to move reads `$5E + 2*($010F & 1)` |
| `$7E1040 + row*16 + col` | the board (15x15 bytes, 0 empty, 1 black, 2 white). Copied to the word board `$0B00` (+`$22` border, stride `$20`) by `80:B4C2` before every check |
| `$1140..` | move list, one byte per move `row<<4 | col`; `$0110` = moves played |
| `$013E` / `$013F` | board cursor column / row (the panel cursor is separate) |
| `$010F` | side to move (0 black, 1 white) |
| `$0115` | game over flag (game loop `80:90FC` runs until it is set) |
| `$12B4` | result code: 1 投了, 2 長連禁, 3 三々禁, 4 四々禁, 5 五連, 6 満局 (text table `80:B30E`; check `80:B537`, line scan `80:CFEB`) |
| `$012A` / `$012B`, `$012D` | wins of 1P / 2P-COM, winner colour of the last game (0 black) |
| `$0123..$013D` | free-match settings (defaults at `80:8157`): `$012C` wins needed, `$013C` move limit (150) |
| `$0144` | 名人戦 round 0-2 (`80:819A`: bracket `81:B49C`, round result `81:B7EC`, loss `81:B929` げーむおーばー, after round 3 `81:D0EC` certificate) |
| `$0131` | puzzle category 0 追い詰め, 1 二手勝ち, 2 四追勝ち, 3 実力認定 |
| `$0133` / `$0134` | puzzle problem number units / tens (0-based); +1 on each correct answer (`80:AF12`) |
| `$0136` | puzzle answer 1 正解 / 2 まちがい; `$0138` solved count; `$0139` = 2 when the category is finished (`80:AF31`, limits at `80:AFAB`) |

Puzzle exit `81:CDA5`: finished category (not 実力認定) with 5+ solved -> certificate `81:CE09`; category 実力認定 ->
`81:CEEC`: `$0133` = 6 -> NAXAT password `81:D00E`, otherwise password screen `81:CF51` (`$0133` = 1 shows nothing).

How scenes force results (the real game code then draws every text):
- Win / loss / forbidden move: four stones of a colour poked into the byte board on row 0 (or a 3-3 shape at
  rows 11-13), board cursor poked, then the real move. **Poked stones are not drawn** (stones are drawn only when
  played), so the board picture shows only the final move.
- Move limit / wrong puzzle answer: `$013C` poked to the current move count.
- Tournament rounds: `$0144` poked before the winning move.
- 2P: `W.pad2` writes the game's pad-2 words after its joypad read (Mesen's port 2 is not configured).
- Title staff roll: hooks feed every entry of the credits table (see "Dead or cut text").
- Debug menu: runtime patch of `80:8135` `JSL $81808A` -> `JSL $818002` (PRG-ROM write in Mesen, file untouched).

## Text areas (16 px cells; the screen is 16 cells wide)

| Area | Where | Size |
|---|---|---|
| H header | top line of game / puzzle / dictionary screens (x 0-190) | 1 line x 11-12 cells |
| B bottom box | dark strip over the board: opening select, opening list, 投了 confirm, song list, puzzle 続けますか, dictionary list and dictionary pages | 3 lines x 11-12 cells (dictionary pages: 3 lines per ▼ page) |
| P side panel | right column of game / puzzle / dictionary screens (x 192-255): 先手 / 0勝, 黒から / 打出し / 四三勝 / 問題 01 番, 連珠 / 辞典 | 4 cells (3 + margin) |
| F full screen | mode / match menu header, free settings (labels ~6 cells left, values ~5 cells right of VS), options, password grid, round result, continue prompt, bracket (names column 4 cells) | 16 cells, centred items |
| T title | title staff roll lines, centred | ~13 cells x 2 lines |

## Scene table

`(W)` / `(WxL)` = JP width of the string in 16 px cells (longest line) x lines (▼ waits count as line breaks).
Ids are the ones first drawn during the scene's own steps (`texts.txt`); phrases (g12) and vars (g13: 黒 / 白, the
〇 in g03_12) are omitted.

| Scene | Area | Text ids (JP width) |
|---|---|---|
| title | - | (8-bit text only: ©1994 NAXAT SOFT, PUSH START) |
| title_credits | T | g07_09 監修 坂田吾朗 (10x2); g07_10 制作協力 (9x2); g07_11 き画 (11x2); g07_12, g07_13 グラフィック (11x2); g07_14 テスト・プレイ (9x2); g07_15 サウンド (13x2); g07_16, g07_17 せい作きょう力 (11x2); g07_18 blank line eraser (15) |
| mode_menu | F | g01_12 モードを選んでください。 (12); g01_13 対 局 (5) (card caption under the cursor card; g01_14..16 when moved) |
| debug_menu / debug_lookrom | - | 8-bit text only (れんじゅ ますたぁ menu, るっく ろむ page) |
| match_menu | F | g01_17 フリー対局 (6); g01_18 名人戦 when moved up |
| tournament_bracket | F | g01_18 名 人 戦 (5); g05_27 一回戦 (3); g05_26 VS (2); g01_00 1 P (6); names g00_30 ペス, g01_04 じゅんじ, g01_06 えいこ, g01_09 げんしち, g01_11 めいじん (4 each) |
| tournament_game | B, H, P | g00_05 先手, g00_06 後手 (2); g00_07 勝 (2); g01_23 珠型を選んでください。 (11); g01_25 直接型 (3); g01_26 間接型 (3); g01_27 COMまかせ (6); g01_24 珠型はどうしますか? (11); g02_31 山月, g02_20 寒星, g02_21 渓月 (2); g01_28 直接1号 寒星 (7); g00_02 手目 番 (9, the move number is drawn by the number routine) |
| tournament_round_win | H, F | g03_19 五 連 (3); g03_12 〇の勝ちです (10); g01_18 (5); g05_27 一回戦 (3); g05_30 1Pの勝ちです。 (9) |
| tournament_round2 | F | g05_28 二回戦 (3) + bracket ids |
| tournament_final_bracket | F | g05_28 二回戦, g05_30, then g05_29 決勝戦 (3) + bracket ids |
| tournament_victory | F | g05_29 決勝戦; g05_30; then the certificate (graphics, graphics.md) |
| game_over | H, F | g03_12 (白); g05_31 1Pの負けです。 (9); g06_00 げーむ おーばー (8) |
| free_settings | F | g06_07 設定を選んでください。 (11); labels g06_08 対戦者, g06_09 レベル, g06_11 勝利数 (3), g06_10 1Pの先後手 (6), g06_12 満了 (2), g00_25 連珠盤 (3), g00_26 決定 (2); g05_26 VS; values g03_14 COM (3), g06_14 級外 (2), g00_05 先手, g06_13 勝先勝 (3, digit drawn separately), g06_30 150 (3), g00_27 木目一 (4) |
| free_opponent | F | g01_01 2 P (3); g03_14 COM (3) |
| free_level | F | g06_14 級外, g06_15..g06_24 十級..一級, g06_25 名人 (2 each) |
| free_first | F | g00_05 先手 / g00_06 後手 (2) |
| free_wins | F | none (1..9 drawn by the number routine before g06_13) |
| free_movelimit | F | g06_27..g07_01 75 / 100 / 125 / 150 / 175 / 200 / 225 (3) |
| free_board | F | g00_27..29 木目一 / 木目二 / 桜一, g03_15..18 木目三 / 桜二 / 木目四 / 木目五, g07_25..26 富士一 / 富士二 (4) |
| game_opening_select | B, P | as tournament_game, up to COMまかせ |
| game_opening_list | B | g01_24 (11); names g02_20..g03_11 (2 each) scroll through the box |
| game_opening_indirect | B | g01_24; g03_00..g03_11 長星..名月 (2) |
| game_opening_com | H | the opening COM picked, e.g. g02_03 直接8号 松月 (7) (random pick: the English run got g02_18) |
| game_board | H | g01_29 直接2号 渓月 (7); g00_02 手目 番 (9) |
| game_panel_menu | H | g00_16 メニューを開きます (9) |
| game_panel_sfx | H | g00_10 効果音を消します, g00_11 効果音を出します (9) |
| game_panel_music | H | g00_08 曲を消します, g00_09 曲を出します (9) |
| game_panel_song | H, B | g00_12 曲をかえますか? (11); g05_11 楽曲 さくら (6), g05_12 楽曲 じんせい (7), g05_13 楽曲 たび (5) |
| game_panel_resign | H, B | g00_13 投了しますか (9); g00_21 はい いいえ (7) |
| game_resigned | H | g03_12 (白の勝ちです) then the next game's opening select |
| game_panel_stones | H | g00_15 碁石をどうしますか (9) |
| game_panel_undo / _replay / _redo / _tostart | H | g00_17 1手前に戻ります / g00_18 1手ずつ再現します / g00_19 元に戻します / g00_20 始めに戻ります (9) |
| game_win / game_lose | H | g03_19 五 連 (3); g03_12 黒 / 白の勝ちです (10) |
| game_overline / game_double_four / game_double_three | H | g03_22 長連禁 / g03_20 四々禁 / g03_21 三々禁 (3); g03_12 白の勝ちです |
| game_move_limit | H | g03_23 満局 (2) |
| free1_board / free2p_board | H, P | as game_board (勝利数 1; free2p_board: 1P vs 2P, g01_01 2 P, stops at 4手目 白番 = 2P's turn) |
| continue_win / continue_lose / continue_2p | F | g05_30 1Pの勝ちです。 / g06_05 COMの勝ちです。 / g06_04 2Pの勝ちです。 (9); g06_06 続けますか? / はい いいえ (11x2) |
| puzzle_menu | F | g04_06 問題を選んでください。 (11); g04_07 追い詰め 二手勝ち, g04_08 四追勝ち 実力認定 (11); g04_09 問題 番 (5, number separate); g00_26 決定 |
| puzzle_solving | H, P | g05_23 勝つまで打って下さい。 (11); P: g04_27 黒から, g04_29 打出し, g05_00 四三勝, g05_22 問 題 (3), g05_05 blank (3) |
| puzzle_panel | H | g04_10 何をしますか? (11); g00_16 メニューを開きます (9) |
| puzzle_correct / puzzle_wrong | H, B | g07_04 正解です。 (11) / g07_05 まちがいです。 (12); g07_06 続けますか? (12); g00_21 はい いいえ (7) |
| puzzle_next | P | g05_01 追詰勝 (3) (problem 02) |
| puzzle_clear | - | g07_04, then the certificate (graphics) |
| password_entry | F | g04_12 パスワードをいれて下さい。 (13); g04_25 ・・・・・・・・ (8, input line); grid g04_15..g04_20 (12-13) |
| password_wrong | F | g04_14 パスワードがちがいます。 (13). Before it the checker runs every password string through the text code without showing it: g04_21..g04_24 and g08_25..g10_24 (8 each) |
| jitsuryoku_solving | P | adds g04_30 二手で (3) |
| jitsuryoku_password | F | g04_13 あなたのパスワードです。 (12); one 8-kana password, here g04_22 これはこまつた。 (8) |
| naxat_password | F | g04_13 (12); g04_11 とぶにみようあり (8); g11_09 このパスワードを / NAXATまで / おくってください。 (11x3) |
| dictionary_menu | H, P, B | g05_17 項目を選んでください。 (11); P: g05_15 連珠, g05_16 辞典 (2); list items g08_10..g08_24 (8, padded) |
| dict_board | B | g07_27 (10x5) |
| dict_five / dict_overline / dict_three / dict_tobi3 | B | g07_28 (10x9) / g07_29 (10x9) / g07_30 (10x24) / g07_31 (9x8) |
| dict_four / dict_tobi4 / dict_43 / dict_44 | B | g08_00 (11x14) / g08_01 (9x4) / g08_02 (10x13) / g08_03 (10x11) |
| dict_33 / dict_false3 / dict_false43 / dict_foul / dict_oite / dict_natsudome | B | g08_04 (10x7) / g08_05 (10x10) / g08_06 (10x12) / g08_07 (10x11) / g08_08 (11x31) / g08_09 (10x3) |
| options_menu | F | g01_22 何をしますか? (7); g01_20 音をいじる (5); g01_21 表示をいじる (6); g03_25 戻る (2) |
| options_sound | F | g03_26 音をどうしますか? (9); g03_27 ステレオ モノラル (11); g03_28 曲 (2); g03_29 効果音 (3); g03_25 戻る; g03_30 スタート Aボタン, g04_05 ストップ Bボタン (9) |
| options_display | F | g03_31 表示をどうしますか? (10); g04_00 文字スピード (6); g04_01 速い ふつう 遅い (9, also used for the cursor row); g04_04 カーソルスピード (8); g03_25 戻る |

Random picks (differ between runs/builds, both are real): the 名人戦 bracket's first opponent (orig run g00_30 ペス,
English run g00_31 まさお) and the COMまかせ opening.

## Text ids never drawn in any scene

Reachable but not given a scene (same screen as an existing scene, different choice):
- Opening headers g01_30..g02_07 (直接3号..12号) and g02_08..g02_19 (間接1号..12号), names g02_23..g02_30 in the
  list: `game_opening_list` + down x(N-1) + A (all 12 direct ones checked by hand); indirect via the 間接型 list.
- Bracket names g00_31 まさお (seen in the English run), g01_02 のりひさ, g01_03 なおこ, g01_05 ともゆき, g01_07 ごろう,
  g01_08 じゅりあ, g01_10 みみ: the bracket draw is random.
- Puzzle side-panel descriptors of later problems: g04_28 白から, g04_31 四の, g05_02 白勝ち, g05_03 黒勝ち, g05_04 連続で
  (pick other problem numbers in `puzzle_menu`).
- Passwords g10_25..g11_08 (8 each): the checker loop stopped at g10_24 for this input; probably the 実力認定 result
  passwords for other scores (`jitsuryoku_password` pokes `$0133` = 2 -> g04_22).

Not found on any screen (no code reference found, or the routine that draws them is never called):
- g00_00, g00_01 無理な戦いはするもんじゃない。 (15), g12_01 無理な戦い (phrase) - no caller found.
- g00_03 `{num}手目 {var}番` (9): the header uses g00_02 + number/var drawn separately; no caller seen.
- g00_04 ヒント: 画面をよく見て、Aボタン連打!! (8x3): drawn only by `80:9299`, which nothing calls (dead hint).
- g07_07 名人戦では、ヒントは出せません。... (10x3): no caller found (hint is dead).
- g00_14 戻ります (9): `LDA #$000E / STA $14` at `80:AA4E/AA9A/B096/B0E2` (panel code; may be a plain number, not
  this id); not drawn by any panel route tried (probably the "close" caption of a panel bar).
- g00_22 設定画面のつもりです。, g00_23 1Pの顔, g00_24 2Pの顔, g01_19 何を設定しますか?: leftovers of an unfinished settings
  screen (the 81:8179 area that looks like it draws them uses the 8-bit text routine with ids 0x16..0x1A).
- g03_13 2P/COM, g03_24 投{sp}了 (resigning showed 白の勝ちです without it), g06_26 ▲▼, g04_02 ふつう, g04_03 遅い,
  g04_26 問題 番 (second copy).
- g05_06..g05_09 category names, g05_10 問題クリア, g05_14 ください。: drawn only by `81:CE66`, never called (the clear
  screen is the graphics certificate instead).
- g06_01 ゆうしょう!, g06_02 あなたは名人戦に, g06_03 勝利しました。: drawn only by `81:D174`, never called (the
  tournament ends with the graphics certificate).
- g07_02 中止しますか? (11), g07_03 解答決定ですか? (11): referenced at `80:AD6E` / `80:9FAA`, `80:AE67`; not reached.
- g07_08 連 珠 / スタッフ (9x2): not in the title credits table `81:AA12` (which lists g07_09..g07_17).
- g07_19..g07_24 proverbs (トブに妙あり ...), g05_18..g05_21 (五連 / 長連 / 四連 / トビ四), g05_24, g05_25 (alternate
  dictionary texts for 四 / トビ四): no caller found.
- g12_00 WWWW, g12_04 ぷれーやー, g12_12 0123456789 (phrases): not used by any string seen.

## Dead or cut content found on the way

- **Title staff roll:** the title loop shows credits from table `81:AA12` (g07_09..g07_17) but stops after 2 entries
  (`CMP #$0004` at `81:A9FB`); scene `title_credits` shows all 9. g07_08 is in no table.
- **Debug menu** れんじゅ ますたぁ (`81:811A`, stub `81:8002`, never called): るっく ろむ (4 COLOR) / (16 COLOR),
  おぶじぇ みる, まっぷ てすと, でばっぐ やめる. 8-bit text group 0 ids 0x16, 0x18.. (`JSR $9498` with id in `$14`).
  The げーむすたーと / さうんどてすと strings (ids 0x15, 0x17) have no reference. Scene `debug_menu`.
