Super Gomoku Narabe Renju (SFC) - English translation patch v{version}
======================================================================

An unofficial fan translation of Naxat Soft's 1994 Super Famicom renju game
"Super Gomoku Narabe Renju" (スーパー五目ならべ 連珠). Menus, game messages,
the tournament, the renju puzzles, the Renju Dictionary lessons, options and
staff credits are in English, with a new variable-width font.

APPLYING THE PATCH
------------------
Apply Super_Gomoku_Narabe_Renju_EN_v{version}.bps to an unheadered ROM with
Flips, Floating IPS, beat or https://www.marcrobledo.com/RomPatcher.js/

Base ROM (No-Intro): Super Gomoku Narabe - Renju (Japan).sfc
  Size   524,288 bytes (no copier header)
  CRC32  {orig_crc}
  MD5    {orig_md5}
  SHA-1  {orig_sha1}

Patched ROM: 1,048,576 bytes, CRC32 {patched_crc}, SHA-1 {patched_sha1}

Tested in Mesen (MesenCE 2.2.1). Start the patched game from power-on; old
savestates from the Japanese ROM will not work with it.

NOTES
-----
- Puzzle passwords stay in Japanese kana: the game compares them with what you
  enter on the kana grid, so they must match exactly. Pick the kana that look
  the same as the ones shown.
- Opening names use the standard renju (RIF) names: Kansei, Keigetsu, ...
- Renju terms follow standard English usage: five, overline, straight four,
  four-three, double-four, double-three, forbidden move.

KNOWN ISSUES
------------
(none yet)

CREDITS
-------
Translation, font and engine patch: minhnhattonthat, with AI assistance
(Claude by Anthropic) for reverse engineering, code and the first draft of the
script.

This is an unofficial fan work, not affiliated with or endorsed by the rights
holders. Do not distribute pre-patched ROMs.
