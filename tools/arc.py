"""Kenka Banchou 3 archive: u16 count, u16 unk, then count*0x40 entries
(u32 off, u32 size, u32 index, char name[0x30] (NUL + 0xff pad), u32 extra), data aligned 0x20."""
import struct


def is_arc(d):
    if len(d) < 0x44: return False
    n = struct.unpack_from('<H', d)[0]
    if n == 0 or 4 + n * 0x40 > len(d): return False
    for i in range(n):
        o, s, idx = struct.unpack_from('<III', d, 4 + i * 0x40)
        if idx != i or o + s > len(d) or o < n * 0x40: return False
        nm = d[4 + i * 0x40 + 12:4 + i * 0x40 + 0x3c]
        if 0 not in nm: return False
    return True


def parse(d):
    n = struct.unpack_from('<H', d)[0]
    out = []
    for i in range(n):
        b = 4 + i * 0x40
        o, s, idx = struct.unpack_from('<III', d, b)
        nm = d[b + 12:b + 0x3c]; nm = nm[:nm.index(0)].decode('ascii', 'replace')
        out.append((nm, o, s))
    return out


def rebuild(d, repl):
    """repl: {index: bytes}; returns new archive keeping header/entry bytes and 0x20 alignment."""
    n = struct.unpack_from('<H', d)[0]
    ents = parse(d)
    first = min(o for _, o, _ in ents)
    out = bytearray(d[:first])
    for i, (nm, o, s) in enumerate(ents):
        data = repl.get(i, d[o:o + s])
        while len(out) % 0x20: out.append(0)
        struct.pack_into('<II', out, 4 + i * 0x40, len(out), len(data))
        out += data
    while len(out) % 0x20: out.append(0)
    return bytes(out)
