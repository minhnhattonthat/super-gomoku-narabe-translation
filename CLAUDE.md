# Super Gomoku Narabe Renju (SFC) - English + Vietnamese translation

Skill: translate-retro-game (H:\translation\super-gomoku-narabe\.claude\skills\translate-retro-game\SKILL.md). Read it before ROM, text or QA work.
SK = .claude/skills/translate-retro-game/scripts

## Commands (run from repo root)
- Check:    `python -X utf8 tools/check.py` (tests incl. identity build, lint en+vi; the pre-commit hook runs this)
- Build:    `python -X utf8 tools/build.py --lang en|vi` -> build/gomoku_<lang>.sfc (`--lang jp` = identity, `--marker`, `--set ID=TEXT`)
- Text:     edit trans/<lang>.tsv, then `python -X utf8 tools/merge.py trans/<lang>.tsv --lang <lang>`; `tools/lint.py --lang <lang>`
- Smoke:    `python -X utf8 $SK/emu.py build/gomoku_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 tools/debug/warp.py SCENE [--rom build/gomoku_en.sfc]` (`--list`, `--all --jobs 3`, `--script probe.lua`); never ask the user to play to a scene
- Release:  `python -X utf8 tools/release.py --lang en --version 1.0` (lint, tests, build, JP scan, smoke, checksum, BPS, zip; never publish without the user)

## Paths
- Original ROM: `rom/orig.sfc` (gitignored copy; hashes in docs/re/README.md). Emulator `tools/mesen/` MesenCE 2.2.1, asar `tools/asar/` 1.91 (both gitignored; settings copy `tools/emu-config/`).
- Text: `script/gNN.json` (jp, full, en, vi, kind). Sources `trans/en.tsv`, `trans/vi.tsv`. Box budgets `data/limits.json`. Fonts `font/en.txt` (+ `font/vi_marks.txt` composed).
- Engine: `asm/main.asm` (hooks: docs/re/hooks.md). Graphics: `tools/gfxpatch.py` (LZSS relocation). RE notes: docs/re/README.md, screens.md, graphics.md.

## Rulings (user, 2026-10-15)
- Pre-approved: keep going, report at end. English first, then Vietnamese. Credits translated. Graphics in scope.
- Standard English renju terms (glossary.md); Vietnamese terms glossary_vi.md. Western name order, no honorifics.
- Passwords and the kana password grid stay Japanese (compared with input). 連珠 calligraphy kept in the title logo.

## Gotchas
- Never change DB outside $80-$BF in engine code (game IRQ writes PPU with absolute addressing).
- Menus redraw labels every frame: keep draws fast (pre-shifted glyphs, redraw cache) or vblank uploads slip.
- Fixed-width fields: values/captions are padded ({to:N}, limits "pad") so a shorter text erases a longer one.

## Status
- Done: engine (VWF, caption, cache), EN + VI scripts reviewed, graphics (icons, card, certificates, title). Next: final QA tour, release.
