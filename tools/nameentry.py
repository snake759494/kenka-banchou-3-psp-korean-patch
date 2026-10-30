"""Name entry (生徒手帳入力) -> Korean input.

Original data (BOOT.BIN file offsets):
  ROWS  0x2a7314 : array of 376 string pointers (one per displayed row, 11 chars max)
  GRP   0x2a78f4 : 49 pointers into ROWS (first row of each group)
  CNT   0x2a79b8 : 49 row counts
  group 0 = kana page (5 rows, 46 kana cells), 1 = alnum/symbol page, 2 = Greek/Cyrillic page,
  3..48 = conversion list of each kana in gojuon order (row 0 = header with kana variants, then kanji rows).
Korean layout: the 46 kana cells become 46 (initial consonant, vowel band) groups; the cell shows the
first syllable of its band and the group lists every KS X 1001 syllable of the band
(header row = syllables without final consonant)."""
import struct

F = 0x74
ROWS, GRP, CNT = 0x2a7314, 0x2a78f4, 0x2a79b8
NROWS, NGRP = (GRP - ROWS) // 4, 49
STR_REGION = (0x1fafa4, 0x1fcec8)         # original IME strings (rewritten completely)

INI = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
BAND3 = [(0, 8), (8, 18), (18, 21)]        # ㅏ-ㅖ / ㅗ-ㅠ / ㅡ-ㅣ  (jungseong index ranges)
BAND2 = [(0, 8), (8, 21)]
# 46 cells in gojuon order (left block rows then right block rows), as (initial, band)
LAYOUT = []
for c in 'ㄱㄴㄷㅁㅂㅅㅇㅈ':
    LAYOUT += [(c, b) for b in BAND3]
for c in 'ㄹㅊㅋㅌㅍㅎㄲㄸㅃㅆㅉ':
    LAYOUT += [(c, b) for b in BAND2]
# reorder so the grid reads naturally: see doc in build notes (left: 가고그 나노 / 느다도드라 / ...)
ORDER = ['가', '고', '그', '나', '노', '느', '다', '도', '드', '라', '로', '마', '모', '므', '바',
         '보', '브', '사', '소', '스', '아', '오', '으', '자', '조',
         '즈', '차', '초', '카', '코', '타', '토', '파', '포', '하', '호', '까', '꼬',
         '따', '또', '빠', '뽀', '싸', '쏘', '짜', '쪼']
JAMO_ROWS = ['ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆ', 'ㅇㅈㅉㅊㅋㅌㅍㅎ', 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙ', 'ㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ']


def syl(i, v, t=0):
    return chr(0xac00 + (i * 21 + v) * 28 + t)


def band_of(label):
    o = ord(label) - 0xac00
    i, v = o // 588, (o % 588) // 28
    c = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'[i]
    bands = BAND3 if c in 'ㄱㄴㄷㅁㅂㅅㅇㅈ' else BAND2
    for b in bands:
        if b[0] <= v < b[1]: return i, b
    raise ValueError(label)


def groups(ks):
    ks = set(ks)
    out = []
    for label in ORDER:
        i, (v0, v1) = band_of(label)
        head = [syl(i, v) for v in range(v0, v1) if syl(i, v) in ks]
        rest = [syl(i, v, t) for v in range(v0, v1) for t in range(1, 28) if syl(i, v, t) in ks]
        rows = [''.join(head[k:k + 11]) for k in range(0, len(head), 11)]
        rows[0] = rows[0]                               # header row (first char = cell label)
        rows += [''.join(rest[k:k + 11]) for k in range(0, len(rest), 11)]
        out.append(rows)
    return out


def page0():
    """5 rows x 11 cols, col 5 spacer; right block rows 3 and 5 only use cols 6, 8, 10"""
    L = ORDER
    left = [L[0:5], L[5:10], L[10:15], L[15:20], L[20:25]]
    r = L[25:]
    right = [r[0:5], r[5:10], [r[10], '　', r[11], '　', r[12]], r[13:18], [r[18], '　', r[19], '　', r[20]]]
    return [''.join(a) + '　' + ''.join(b) for a, b in zip(left, right)]


def patch(boot, T, cmap, pool=None):
    import kfont
    boot = bytearray(boot)
    rd = lambda o: struct.unpack_from('<I', boot, o)[0]
    sj = lambda s: kfont.sjis_encode(s, T, cmap)
    # current groups (to keep page 1 = alnum/symbols)
    old = []
    for k in range(NGRP):
        p, c = rd(GRP + 4 * k), rd(CNT + 4 * k)
        rows = []
        for i in range(c):
            va = rd(p + F + 4 * i); fo = va + F
            rows.append(bytes(boot[fo:boot.index(0, fo)]))
        old.append(rows)
    ks = [bytes([a, b]).decode('euc-kr') for a in range(0xb0, 0xc9) for b in range(0xa1, 0xff)]
    new = [[sj(r) for r in page0()], old[1], [sj(r) for r in JAMO_ROWS]] + [[sj(r) for r in g] for g in groups(ks)]
    assert len(new) == NGRP
    total = sum(len(g) for g in new)
    assert total <= NROWS, total
    # write strings into the old region (then the pool)
    cur = [STR_REGION[0]]
    boot[STR_REGION[0]:STR_REGION[1]] = bytes(STR_REGION[1] - STR_REGION[0])
    cache = {}

    def put(b):
        if b in cache: return cache[b]
        n = len(b) + 1
        if cur[0] + n <= STR_REGION[1]:
            o = cur[0]; cur[0] = (o + n + 3) & ~3
        else:
            o = pool.alloc(n)
        boot[o:o + n] = b + b'\0'
        cache[b] = o
        return o
    idx = 0
    for k, g in enumerate(new):
        struct.pack_into('<I', boot, GRP + 4 * k, ROWS - F + 4 * idx)
        struct.pack_into('<I', boot, CNT + 4 * k, len(g))
        for r in g:
            struct.pack_into('<I', boot, ROWS + 4 * idx, put(r) - F); idx += 1
    for i in range(idx, NROWS):
        struct.pack_into('<I', boot, ROWS + 4 * i, put(b'') - F)
    print('name entry: %d groups, %d rows, region used %d/%d' % (len(new), total, cur[0] - STR_REGION[0], STR_REGION[1] - STR_REGION[0]))
    return bytes(boot)
