"""Write tbl/jp.tbl from the glyph order read off tools/fontsheet.py sheets (codes 0x000-0x1BF, 8 per row)."""
ROWS = """
01234567 89ABCDEF GHIJKLMN OPQRSTUV WXYZ!?:/ 。「」、・をぁぃ ぅぇぉゃゅょっー あいうえおかきく
けこさしすせそた ちつてとなにぬね のはひふへほまみ むめもやゆよらり るれろわんがぎぐ げござじずぜぞだ ぢづでどばびぶべ ぼぱぴぷぺぽヲァ
ィゥェォャュョッ アイウエオカキク ケコサシスセソタ チツテトナニヌネ ノハヒフヘホマミ ムメモヤユヨラリ ルレロワンガギグ ゲゴザジズゼゾダ
ヂヅデドバビブベ ボパピプペポ局毎 交代勝敗先何背景 木目富士桜変夜青 空打始黒白行連数 珠盤型設定発級後 外戻碁石開手前再 現元番投了盲見音
曲消出効果対戦者 画面選間直休接号 続熱利点気分努狙 弱当然結含別子楽 表示操作系試聴演 奏停止速遅定移動 星月寒渓疎花残雨 金松丘新負飛瑞山
長峡恒水流雲浦嵐 銀明斜名夏化坂田 吾朗私腐問題挑来 実力考解制々認協 項用語辞典決反転 回顔攻答禁逃一二 三四五六七八九十 上下左右組立時伸
切段初詰出両活妙 防逆称形順難場所 危険無理追大抵抗 心読正強落筋注意 思引▲▼◀▶満文 字位人中他端片敵 急各本線央天同方 並次度以有浩監修
"""
chars = "".join(ROWS.split())
assert len(chars) == 0x1C0, len(chars)
with open("tbl/jp.tbl", "w", encoding="utf-8", newline="\n") as f:
    f.write("# 16x16 font codes (16-bit LE in ROM). Controls (bit 15) are handled in tools/codec.py.\n")
    for i, c in enumerate(chars):
        f.write("%03X=%s\n" % (i, c))
