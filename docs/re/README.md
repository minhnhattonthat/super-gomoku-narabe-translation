# RE notes index - Super Gomoku Narabe Renju (SFC, Naxat 1994)

ROM: `Super Gomoku Narabe - Renju (Japan).sfc`, 524,288 bytes, LoROM FastROM (map $30), no SRAM, header checksum OK.
CRC32 5621000D, MD5 e4fbac9e377b5b08e7b88084766b1c03, SHA-1 8d8387305b6d65d4e1fab77bcd197dd05891e664.
No earlier fan translation found (web search 2026-10-15).

- [text.md](text.md) - both text systems, control codes, pointer/bank sites
- [graphics.md](graphics.md) - graphics-text survey (to do)

## Free space
ROM is nearly full (largest 0x00 run: 0x26802, 0x584 bytes). Plan: expand to 1 MB (banks $90-$9F = file 0x80000+).

## Input
Joypad via auto-read $4218 (pc 80:828F). Title accepts Start only after its intro (~f900 cold boot).
