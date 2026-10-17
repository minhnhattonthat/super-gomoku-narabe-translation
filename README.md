# Super Gomoku Narabe Renju - English and Vietnamese translation

Unofficial fan translation patches for the Super Famicom game *Super Gomoku Narabe Renju* (スーパー五目ならべ 連珠,
Naxat Soft, 1994).

**Download the patches from the [Releases](../../releases) page.** Apply the `.bps` to your own dump of the Japanese ROM
(`Super Gomoku Narabe - Renju (Japan).sfc`, 524,288 bytes, CRC32 `5621000D`, SHA-1
`8d8387305b6d65d4e1fab77bcd197dd05891e664`) with Flips, beat or RomPatcher.js.

This repository contains source only (script, font, engine patch in 65816 assembly, build tools): no ROM data and no
pre-patched ROMs.

## Building

Needs Python 3.10+ with Pillow, [asar](https://github.com/RPGHacker/asar) 1.91 at `tools/asar/asar.exe`, and your ROM
copied to `rom/orig.sfc`.

```
python -X utf8 tools/check.py                      # tests: identity build, lint (en, vi)
python -X utf8 tools/build.py --lang en            # -> build/gomoku_en.sfc  (or --lang vi)
python -X utf8 tools/release.py --lang en --version 1.0
```

Layout: `trans/` script sources, `script/` extracted text, `font/` pixel fonts, `asm/main.asm` engine patch,
`tools/gfxpatch.py` graphics, `docs/re/` reverse-engineering notes, `tools/debug/` warp tool (reaches 78 scenes from a
cold boot in an emulator). See `CLAUDE.md` for the full command list.

## Credits

Translation, font and engine patch: minhnhattonthat, with AI assistance (Claude by Anthropic). Not affiliated with or
endorsed by the rights holders.

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)
