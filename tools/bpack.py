"""File pack embedded in BOOT.BIN .data: 0x13d entries of (u32 off, u32 size, char name[0x38]) at PACK,
entry 0's offset field holds the count (offset 0). Data (LZS files) start right after the table."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import lzs

PACK = 0x22d464
END = 0x28cc34          # next object (TIM2) in .data


def parse(b):
    n = struct.unpack_from('<I', b, PACK)[0]
    base = PACK + n * 0x40
    out = []
    for i in range(n):
        o, s = struct.unpack_from('<II', b, PACK + i * 0x40)
        if i == 0: o = 0
        nm = b[PACK + i * 0x40 + 8:PACK + i * 0x40 + 0x40].split(b'\0')[0].decode()
        out.append((nm, base + o, s))
    return base, out


def patch(b, repl, T, cmap):
    """repl: {jp: kr}. Rewrites strings of the event script pack in place (same byte length, ASCII-space
    padded), recompresses only the changed files and rebuilds the pack. returns (boot, stats, too_long)"""
    import kfont, bpack_text
    b = bytearray(b)
    base, ents = parse(b)
    blobs = []; st = {'files': 0, 'strings': 0}; long_ = []
    for nm, off, sz in ents:
        raw = bytes(b[off:off + sz])
        d = bytearray(lzs.decompress(raw)); ch = False
        for s, n, u in bpack_text.strings(bytes(d)):
            if u not in repl: continue
            e = kfont.sjis_encode(repl[u], T, cmap).replace(b'\n', b'\r\n')
            if len(e) > n: long_.append((u, repl[u], len(e), n)); continue
            d[s:s + n] = e + b' ' * (n - len(e)); ch = True; st['strings'] += 1
        if ch:
            raw = lzs.compress_opt(bytes(d)); st["files"] += 1
            assert lzs.decompress(raw) == bytes(d)
        blobs.append(raw)
    n = len(ents); o = 0
    for i, raw in enumerate(blobs):
        struct.pack_into('<I', b, PACK + i * 0x40 + 4, len(raw))
        if i: struct.pack_into('<I', b, PACK + i * 0x40, o)
        o += len(raw)
    data = b''.join(blobs)
    if base + len(data) > END: raise ValueError('event pack too big: %d > %d' % (len(data), END - base))
    b[base:END] = data + bytes(END - base - len(data))
    return bytes(b), st, long_
