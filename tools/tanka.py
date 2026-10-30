"""Tanka (啖呵) phrase font: kenka_font_tanka00.tm2 (common.lzs, swizzled 512x512 4bpp, two 2-bit planes,
24x24 cells, 21 per row, 441 per plane) indexed by the SJIS char list at BOOT.BIN 0x1b9767 (723 chars).
Korean: every Hangul used by the tanka phrases is written into the list as its main-font proxy SJIS char
(the table char owning its glyph slot) and drawn into the matching cell."""
import os, sys, re
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import arc, tim2, glyph, kbtext

LIST_OFF, LIST_LEN = 0x1b9767, 1444
PHRASES = (0x1b9f74, 0x1be240)
FONT = ('NanumSquareNeo-eHv.ttf', 22)
FW = {chr(c): chr(c + 0xfee0) for c in range(0x30, 0x7b) if chr(c).isalnum()}
FW.update({'!': '！', '?': '？', ' ': '　', '~': '～', '.': '．', ',': '，', '-': '－', '(': '（', ')': '）', ':': '：'})


def is_free(c):
    o = ord(c)
    return 0x3041 <= o <= 0x30f6 and c not in 'ー' or 0x4e00 <= o <= 0x9fff


def norm_phrase(s):
    return ''.join(FW.get(c, c) for c in s)


def patch_list(boot, eb, T, cmap):
    """returns (boot, {list_position: hangul})"""
    boot = bytearray(boot)
    lst = list(boot[LIST_OFF:LIST_OFF + LIST_LEN].decode('cp932'))
    used = ['　']
    for off, (jp, kr, cap) in sorted(eb.items()):
        if PHRASES[0] <= off < PHRASES[1]:
            for c in norm_phrase(kr):
                if ('가' <= c <= '힣' or c not in lst) and c not in used: used.append(c)
    free = [i for i, c in enumerate(lst) if is_free(c)]
    if len(used) > len(free): raise ValueError('tanka font: %d hangul > %d free cells' % (len(used), len(free)))
    pos = {}
    for i, h in zip(free, used):
        lst[i] = T[cmap[h]] if '가' <= h <= '힣' else h; pos[i] = h
    for i in free[len(used):]:
        lst[i] = '　' if False else lst[i]
    enc = ''.join(lst).encode('cp932')
    assert len(enc) == LIST_LEN
    boot[LIST_OFF:LIST_OFF + LIST_LEN] = enc
    print('tanka font: %d chars / %d free cells' % (len(used), len(free)), ''.join(c for c in used if not '가' <= c <= '힣'))
    return bytes(boot), pos


def texture(pos, orig):
    """orig: original tm2 bytes; pos: {list_position: hangul}"""
    px, _ = tim2.read_any(orig)
    px = px.copy()
    for i, h in pos.items():
        pl, cell = i // 441, i % 441
        r, c = divmod(cell, 21)
        g = np.zeros((24, 24), np.uint8) if h == '　' else glyph.render(h, FONT[0], FONT[1], cell=24, box=22, gamma=0.9)
        blk = px[r * 24:r * 24 + 24, c * 24:c * 24 + 24]
        blk[:] = (blk & ~np.uint8(3 << (2 * pl)) & 0xf) | (g << (2 * pl))
    return tim2.write_any(orig, px)
