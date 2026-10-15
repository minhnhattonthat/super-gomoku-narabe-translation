; Super Gomoku Narabe Renju - translation engine patch (asar 1.91, applied to the 1 MB expanded ROM by tools/build.py)
; - text block moved from bank $83 to TEXT ($91:8000), same group/index ids
; - VWF: 8x16 proportional font (bank $92) for codes $200+, JP 16x16 glyphs still drawn for codes $24-$1FF
; Hook list: docs/re/hooks.md
lorom

!TEXT = $918000            ; group table (14 words) + strings, written by build.py
!FONT = $928000            ; code $200+n: 32 bytes (16 rows x 2 planes), rows 0-7 then 8-15
!FONTW = $92C000           ; code $200+n: advance width in px (<= 8)
!BUF = $7E2000             ; the game's text tile buffer

; WRAM (never written by the game in $1532-$19FF, docs/re/hooks.md)
!VX = $7E1900              ; pixel x of the next glyph in the current line
!V7C = $7E1902             ; $7C value vwf_adv left behind; a mismatch means someone moved the cursor
!VW = $7E1904              ; width of the glyph just drawn, consumed by vwf_adv (0 = cell advance)
!LINE = $7E1906            ; current line base ($7C & $FC00)
!SH = $7E1908              ; x & 7
!TA = $7E190A              ; buffer offset of the tile at x (top half)
!TB = $7E190C              ; ... and of the next tile
!KA = $7E190E              ; keep-mask for tile A (byte)
!KB = $7E1910              ; keep-mask for tile B (byte)
!G0 = $7E1912              ; shifted plane 0 (word: hi = tile A, lo = tile B)
!G1 = $7E1914
!WD = $7E1916              ; width for draw8
!SHTAB = $92D000           ; s = 1-8: 256 words ((p << 8) >> s), written by build.py
!CPOS = $7E1920            ; redraw cache: $12 and $14 of the last instant draw
!CID = $7E1922
!CVALID = $7E1924          ; 1 = the buffer still holds exactly that draw
!INST = $7E1926            ; 1 while an instant draw runs
!SB = $7E191C             ; SHTAB offset for the current shift
!P = $7E191E               ; source row word
!GBUF = $7E1940            ; the glyph being drawn, 16 rows x 2 bytes

; ---------------------------------------------------------------- text bank
org $81A756 : lda.l !TEXT+$1A,x      ; {var}: group 13
org $81A75C : lda.w #!TEXT>>16
org $81A779 : lda.l !TEXT+$18,x      ; {ph}: group 12
org $81A77F : lda.w #!TEXT>>16
org $81A7A9 : lda.w #!TEXT>>16
org $81A7C4 : lda.l !TEXT,x          ; screen text
org $81A7CA : lda.w #!TEXT>>16
org $81A7F6 : lda.w #!TEXT>>16

; ---------------------------------------------------------------- renderer hooks
org $81A4E2                          ; draw glyph $16 at $7C
    jsl vwf_draw
    rts
org $81A4CC                          ; advance $7C
    jsl vwf_adv
    rts
org $81A7B3                          ; select string (REP #$30 here): LDA $14 / AND #$001F
    jsl sel_hook
    nop
org $81A86D                          ; single glyph at $12 (A83D): JSR A4E2 / JSR A3CD
    jsl draw_fresh
    nop
    nop
org $81A5D9                          ; {num}: a blank tens digit takes no space (BEQ $A5EA)
    db $F0,$0F

; Redraw cache. Menus redraw their labels every frame through the instant draw ($81:A35A); VWF is too slow to
; redo a long label each frame (the menu stops taking input), so an identical redraw (same $12 position and $14
; id, no other buffer write since) is skipped.
org $81A35A                          ; PHP / REP #$30 / JSR $A3BE
    jml inst_hook
org $81A3B5                          ; SEP #$30 here: STZ $91 / STZ $94
    jsl inst_end
org $80A0BA                          ; text buffer clear: LDX #$0000 / LDA #$0000
    jsl clr_hook
    nop
    nop

; ---------------------------------------------------------------- new code
org $908000
inst_hook:                           ; entered by JML from $81:A35A (caller did JSR)
    php
    rep #$30
    lda.l !CVALID
    beq .miss
    lda $12
    cmp.l !CPOS
    bne .miss
    lda $14
    cmp.l !CID
    bne .miss
    plp
    jml $81A3BD                      ; RTS
.miss:
    lda $12
    sta.l !CPOS
    lda $14
    sta.l !CID
    lda #$0000
    sta.l !CVALID
    inc
    sta.l !INST
    sep #$30                         ; = JSR $A3BE: clear the 9 line-dirty flags
    ldx #$00
-   stz $0159,x
    inx
    cpx #$09
    bcc -
    rep #$30
    jml $81A360

inst_end:
    stz $91
    stz $94
    php
    rep #$20
    lda #$0000
    sta.l !INST
    inc
    sta.l !CVALID
    plp
    rtl

clr_hook:
    lda.w #$0000
    sta.l !CVALID
    ldx.w #$0000
    rtl

; any glyph or cell write outside an instant draw makes the cached draw stale
invalidate:
    lda.l !INST
    bne +
    sta.l !CVALID
+   rts

sel_hook:
    lda #$FFFF
    sta.l !V7C
    lda $14
    and #$001F
    rtl

draw_fresh:                          ; = JSR A4E2 ; JSR A3CD with a forced resync
    php
    rep #$30
    lda #$FFFF
    sta.l !V7C
    jsl vwf_draw
    sep #$30
    ldx #$00
-   lda $0159,x
    sta $0150,x
    inx
    cpx #$09
    bcc -
    plp
    rtl

vwf_draw:
    php
    rep #$30
    phx
    phy
    jsr invalidate
    lda $16
    cmp #$01A3                       ; blinking page arrow: drawn and cleared per cell at $7C
    bne +
    jsr fixed_draw
    bra .mark
+   lda $7C
    cmp.l !V7C
    beq +
    jsr resync
+   lda $16
    cmp #$0024
    bcs .notlatin
    cmp #$000A
    bcs .letter
    adc #$0230                       ; 0-9 -> '0'-'9' (carry clear)
    bra .latin
.letter:
    adc #$0236                       ; A-Z ($0A-$23) -> 'A'-'Z' ($241-$25A), carry set
.latin:
    sta $16
    bra .eng
.notlatin:
    cmp #$0200
    bcs .eng
    jsr jp_draw
    bra .mark
.eng:
    jsr eng_draw
.mark:
    sep #$20
    ldy $9E
    lda #$01
    sta $0159,y
    rep #$30
    ply
    plx
    plp
    rtl

vwf_adv:
    php
    rep #$30
    lda.l !VW
    beq .cell
    clc
    adc.l !VX
    sta.l !VX
    lda #$0000
    sta.l !VW
    lda.l !VX                        ; $7C = first whole cell after the text
    clc
    adc #$000F
    lsr
    lsr
    lsr
    lsr
    cmp #$0010
    bcc +
    lda #$000F
+   jsr celloff
    ora.l !LINE
    sta $7C
    sta.l !V7C
    plp
    rtl
.cell:                               ; original $81:A4CC (also the cell clears of {sp} and line clears)
    jsr invalidate
    lda $7C
    clc
    adc #$0020
    sta $7C
    and #$00FF
    bne +
    lda $7C
    clc
    adc #$0100
    sta $7C
+   plp
    rtl

; A = cell 0-15 -> buffer offset within a line
celloff:
    pha
    and #$0008
    asl
    asl
    asl
    asl
    asl
    asl
    sta.l !TB                        ; scratch
    pla
    and #$0007
    asl
    asl
    asl
    asl
    asl
    ora.l !TB
    rts

resync:
    lda $7C
    and #$FC00
    sta.l !LINE
    lda $7C
    and #$0200
    lsr
    lsr
    lsr
    lsr
    lsr
    lsr                              ; 8 if band 1
    sta.l !VX
    lda $7C
    and #$00E0
    lsr
    lsr
    lsr
    lsr
    lsr
    clc
    adc.l !VX
    asl
    asl
    asl
    asl
    sta.l !VX
    rts

; original 16x16 copy at $7C (cell-aligned), for the page arrow
fixed_draw:
    jsr jp_src
    lda $7C
    clc
    adc.w #!BUF
    sta $26
    lda.w #!BUF>>16
    sta $28
    ldy #$0000
-   lda [$22],y
    sta [$26],y
    iny
    iny
    cpy #$0020
    bcc -
    ldy #$0100
-   lda [$22],y
    sta [$26],y
    iny
    iny
    cpy #$0120
    bcc -
    rts

; [$22] = JP glyph of code $16 (bank $88)
jp_src:
    lda $16
    and #$03F8
    asl
    asl
    asl
    asl
    asl
    asl
    sta $22
    lda $16
    and #$0007
    asl
    asl
    asl
    asl
    asl
    ora $22
    clc
    adc #$9000
    sta $22
    lda #$0088
    sta $24
    rts

jp_draw:                             ; 16 px: two 8 px halves
    jsr jp_src
    lda $22
    clc
    adc #$0100
    sta $26
    lda #$0088
    sta $28
    lda #$0008
    sta.l !WD
    jsr draw8
    lda.l !VX
    clc
    adc #$0008
    sta.l !VX
    jsr jp_src                       ; draw8 clobbers $22/$26: recompute, right half = +$10
    lda $22
    clc
    adc #$0010
    sta $22
    clc
    adc #$0100
    sta $26
    lda #$0088
    sta $28
    jsr draw8
    lda.l !VX
    sec
    sbc #$0008
    sta.l !VX
    lda #$0010
    sta.l !VW
    rts

eng_draw:
    lda $16
    sec
    sbc #$0200
    tax
    lda.l !FONTW,x
    and #$00FF
    sta.l !WD
    sta.l !VW
    txa
    asl
    asl
    asl
    asl
    asl
    clc
    adc.w #!FONT
    sta $22
    clc
    adc #$0010
    sta $26
    lda.w #!FONT>>16
    sta $24
    sta $28
    lda.l !WD
    beq +
    jsr draw8
+   rts

; tile offset (top half) of tile A (0-31) within the current line
tileoff:
    pha
    and #$0010
    asl
    asl
    asl
    asl
    asl
    sta.l !TB
    pla
    and #$000F
    asl
    asl
    asl
    asl
    ora.l !TB
    ora.l !LINE
    rts

; OR an up-to-8 px wide, 16 row glyph at VX: rows 0-7 from [$22], rows 8-15 from [$26] (2 bytes per row).
; Runs every frame for menu labels the game redraws, so it must stay cheap. DB is never changed (the game's IRQ
; writes PPU registers with absolute addressing): the glyph is copied to GBUF, destinations go through [$22],y
; (tile A) and [$26],y (tile B), shifts come from SHTAB. x & 7 == 0 is drawn as shift 8 into the previous tile
; (keep mask $FF there), so the shift is always 1-8.
draw8:
    ldy #$0000
-   lda [$22],y
    tyx
    sta.l !GBUF,x
    lda [$26],y
    sta.l !GBUF+16,x
    iny
    iny
    cpy #$0010
    bcc -
    lda.l !VX
    and #$0007
    bne +
    lda #$0008
+   sta.l !SH
    tax
    lda.l !VX
    lsr
    lsr
    lsr
    cpx #$0008
    bne +
    dec
+   pha
    inc
    jsr tileoff
    clc
    adc.w #!BUF
    sta $26                          ; tile B
    pla
    jsr tileoff
    clc
    adc.w #!BUF
    sta $22                          ; tile A
    lda.w #!BUF>>16
    sta $24
    sta $28
    lda.l !SH                        ; SHTAB row for this shift
    dec
    xba
    asl
    sta.l !SB
    ; keep masks: ~(~($FFFF >> w) >> sh)
    lda.l !WD
    tax
    lda #$FFFF
-   cpx #$0000
    beq +
    lsr
    dex
    bra -
+   eor #$FFFF
    pha
    lda.l !SH
    tax
    pla
-   lsr
    dex
    bne -
    eor #$FFFF
    sta.l !KB                        ; low byte = tile B
    xba
    sta.l !KA                        ; low byte = tile A
    ldy #$0000
.row:
    rep #$20
    tyx
    lda.l !GBUF,x                    ; plane 0 | plane 1 << 8
    beq .blank
    sta.l !P
    and #$00FF
    asl
    adc.l !SB
    tax
    lda.l !SHTAB,x
    sta.l !G0
    lda.l !P
    xba
    and #$00FF
    asl
    adc.l !SB
    tax
    lda.l !SHTAB,x
    sta.l !G1
    sep #$20
    lda [$22],y
    and.l !KA
    ora.l !G0+1
    sta [$22],y
    lda [$26],y
    and.l !KB
    ora.l !G0
    sta [$26],y
    iny
    lda [$22],y
    and.l !KA
    ora.l !G1+1
    sta [$22],y
    lda [$26],y
    and.l !KB
    ora.l !G1
    sta [$26],y
    bra .next
.blank:
    sep #$20
    lda [$22],y
    and.l !KA
    sta [$22],y
    lda [$26],y
    and.l !KB
    sta [$26],y
    iny
    lda [$22],y
    and.l !KA
    sta [$22],y
    lda [$26],y
    and.l !KB
    sta [$26],y
.next:
    rep #$20
    iny
    cpy #$0010                       ; rows 8-15: bottom tiles are $100 further, so [ptr],y needs +$F0
    bne +
    lda $22
    clc
    adc #$00F0
    sta $22
    lda $26
    clc
    adc #$00F0
    sta $26
+   cpy #$0020
    bcs +
    jmp .row
+   rts

assert pc() <= $90FFFF
