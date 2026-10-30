"""Korean glyph slot assignment + font texture build for Kenka Banchou 3.

Glyph index i (table order at BOOT.BIN 0x16c704, 3572 entries) lives in
texture i//2048 (kenka_font_jis00/01), 2-bit plane (i//1024)%2, cell i%1024 (32x32 grid of 16x16).
Kept slots: every non kana/kanji table entry (punctuation, symbols, full-width alnum).
Free slots: kana, kanji, Greek, Cyrillic -> Hangul.  The text files use glyph indices,
EBOOT strings use the SJIS code of the table char that owns the slot."""
import os, sys, json, re, struct, unicodedata
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import kbtext, tim2, lzs, glyph

ROOT = kbtext.ROOT
FONT_OFF = [0x1ff514, 0x217a74]          # LZS TIM2 blobs in BOOT.BIN
FONT_CAP = [0x217a74 - 0x1ff514, 88552]  # bytes available for each compressed blob
FONT_NAME, FONT_SIZE = 'SeoulHangangEB.ttf', 18

# ASCII -> full-width table char for text files (game table has no ASCII)
ASCII_FW = {chr(c): chr(c + 0xfee0) for c in range(0x21, 0x7f)}
ASCII_FW.update({' ': '　', '~': '～', '-': 'ー' if False else '－'})


def is_free(c):
    o = ord(c)
    return (0x3041 <= o <= 0x30ff and c not in 'ー・ヽヾゝゞ゛゜') or 0x4e00 <= o <= 0x9fff or 0x391 <= o <= 0x3c9 or 0x401 <= o <= 0x451


def slots(T):
    free = [i for i, c in enumerate(T) if is_free(c)]
    return free


def assign(chars_by_freq, T, n1=None):
    """frequent chars -> 1-byte codes (index < 0xdf); rest alternate between textures
    so that both compressed blobs stay inside their slots."""
    free = slots(T)
    one = [i for i in free if i < 0xdf]
    t0 = [i for i in free if 0xdf <= i < 2048]
    t1 = [i for i in free if i >= 2048]
    cmap = {}
    seq = list(chars_by_freq)
    for i, ch in zip(one, seq): cmap[ch] = i
    rest = seq[len(one):]
    # proportion for texture 0 vs 1 (tex0 already holds the 1-byte block + most symbols)
    r0 = 0.47 if n1 is None else n1
    k0 = 0; k1 = 0
    for k, ch in enumerate(rest):
        want0 = (k0 + 1) <= r0 * (k + 1) and k0 < len(t0)
        if want0 or k1 >= len(t1):
            cmap[ch] = t0[k0]; k0 += 1
        else:
            cmap[ch] = t1[k1]; k1 += 1
    if len(cmap) < len(seq): raise ValueError('out of glyph slots: %d > %d' % (len(seq), len(free)))
    return cmap


def text_cmap(T, cmap):
    """char -> index for message files, including kept table chars and ASCII fallbacks"""
    m = {c: i for i, c in enumerate(T) if not is_free(c) and c != '　'}
    m['　'] = T.index('　', 0x100) if False else 0x162 if T[0x162] == '　' else T.index('　')
    m.update(cmap)
    for a, f in ASCII_FW.items():
        if a not in m and f in m: m[a] = m[f]
    for a, f in {"'": '’', '"': '”', '`': '‘', '·': '・', '〜': '～', '…': '…'}.items():
        if a not in m and f in m: m[a] = m[f]
    return m


def level_map(pal, pl):
    """intensity 0..3 -> 2-bit value, ordered by the palette alpha of that plane's CLUT"""
    a = [int(pal[16 * pl + (v << (2 * pl))][3]) for v in range(4)]
    return np.array(sorted(range(4), key=lambda v: a[v]), np.uint8)


def build_textures(cmap, T):
    boot = open(kbtext.BOOT, 'rb').read()
    texs = [bytearray(lzs.decompress(boot[o:o + 0x20000])) for o in FONT_OFF]
    pxs = [tim2.read(bytes(t))[0].copy() for t in texs]
    pals = [tim2.read(bytes(t))[1] for t in texs]
    # clear free slots
    for i, c in enumerate(T):
        if is_free(c):
            t, pl, cell = i // 2048, (i // 1024) % 2, i % 1024
            r, cc = divmod(cell, 32)
            blk = pxs[t][r * 16:r * 16 + 16, cc * 16:cc * 16 + 16]
            blk &= ~np.uint8(3 << (2 * pl)) & 0xf
    for ch, i in cmap.items():
        g0 = glyph.render(ch, FONT_NAME, FONT_SIZE, gamma=1.0)
        t, pl, cell = i // 2048, (i // 1024) % 2, i % 1024
        g = level_map(pals[t], pl)[g0]
        r, cc = divmod(cell, 32)
        blk = pxs[t][r * 16:r * 16 + 16, cc * 16:cc * 16 + 16]
        blk[:] = (blk & ~np.uint8(3 << (2 * pl)) & 0xf) | (g << (2 * pl))
    return [tim2.write(bytes(texs[k]), pxs[k]) for k in range(2)]


def patch_boot(boot, textures):
    """returns (boot, free ranges [start, end) left behind the new compressed blobs)"""
    boot = bytearray(boot); free = []
    for k, (o, cap) in enumerate(zip(FONT_OFF, FONT_CAP)):
        c = lzs.compress(textures[k])
        if len(c) > cap: raise ValueError('font %d too big: %d > %d' % (k, len(c), cap))
        boot[o:o + cap] = c + bytes(cap - len(c))
        free.append((o + len(c) + 16, o + cap))
    return bytes(boot), free


def sjis_encode(s, T, cmap):
    """EBOOT string encoder: Hangul -> SJIS of slot owner; ASCII stays; other table chars as-is"""
    out = bytearray()
    for ch in s:
        if ch in cmap: out += T[cmap[ch]].encode('cp932')
        elif ch == '\n' or ' ' <= ch <= '~': out += ch.encode('ascii')
        else: out += ch.encode('cp932')
    return bytes(out)
