# Super Gomoku Narabe Renju (SFC) - English + Vietnamese translation

Skill: translate-retro-game (H:\translation\super-gomoku-narabe\.claude\skills\translate-retro-game\SKILL.md). Read it before ROM, text or QA work.
SK = .claude/skills/translate-retro-game/scripts

## Commands (run from repo root)
- Check:    `python -X utf8 tools/check.py` (tests; the pre-commit hook runs this)
- Extract:  `python -X utf8 tools/extract.py rom/orig.sfc` (writes script/gNN.json only if missing)
- Build:    (todo) `python -X utf8 tools/build.py --lang en` -> build/gomoku_en.sfc
- Smoke:    `python -X utf8 $SK/emu.py build/gomoku_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Font:     `python -X utf8 tools/fontsheet.py rom/orig.sfc out.png --tbl tbl/jp.tbl`

## Paths
- Original ROM: `rom/orig.sfc` (gitignored copy of `rom/Super Gomoku Narabe - Renju (Japan).sfc`; hashes in docs/re/README.md).
- Emulator: `tools/mesen/` MesenCE 2.2.1 (github.com/nesdev-org/MesenCE releases, gitignored). Settings copy:
  `tools/emu-config/mesen-settings.json` (needs `Snes.Port1.Type=SnesController` or scripted input is ignored).
- Text: `script/gNN.json` (jp, full = jp with phrases expanded, en, vi, kind). Tables: `tbl/`. RE notes: `docs/re/README.md`.

## Rulings (user, 2026-10-15)
- Specs/plans pre-approved: keep going, report at end. English first, then Vietnamese.
- Credits translated to English. Graphics text all in scope.
- Standard English renju terms (double-three, double-four, overline, forbidden move); Western name order, no honorifics.
- Edit source files only with the file-edit tool.

## Status
- Done: Step 0, recon of both text systems, extraction + roundtrip test. Next: debug tool, engine spike (8px font), build.
