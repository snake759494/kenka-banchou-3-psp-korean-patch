"""PSP PRX (BOOT.BIN) relocation helper: find every reference to an address.
file offset = vaddr + 0x74 for segment 0 (text+rodata+data)."""
import struct
FOFF = 0x74


def sections(b):
    shoff = struct.unpack_from('<I', b, 0x20)[0]; shn, shstr = struct.unpack_from('<HH', b, 0x30)
    sh = [struct.unpack_from('<10I', b, shoff + 40 * i) for i in range(shn)]
    so = sh[shstr][4]
    out = []
    for s in sh:
        n = b[so + s[0]:b.index(b'\0', so + s[0])].decode()
        out.append(dict(name=n, type=s[1], addr=s[3], off=s[4], size=s[5]))
    return out


def phdrs(b):
    phoff = struct.unpack_from('<I', b, 0x1c)[0]; n = struct.unpack_from('<H', b, 0x2c)[0]
    return [struct.unpack_from('<8I', b, phoff + 32 * i) for i in range(n)]


def relocs(b):
    ph = phdrs(b)
    rel = []
    for s in sections(b):
        if s['type'] != 0x700000a0 and s['type'] != 9: continue
        for k in range(0, s['size'], 8):
            off, info = struct.unpack_from('<II', b, s['off'] + k)
            typ = info & 0xff; ob = (info >> 8) & 0xff; ab = (info >> 16) & 0xff
            rel.append((typ, ph[ob][2] + off, ph[ab][2]))
    return rel


def refs(b):
    """returns {target_vaddr: [(kind, vaddr_of_ref, extra)]} for R_MIPS_32 and HI16/LO16 pairs"""
    ph = phdrs(b)
    seg_off = lambda va: va + (ph[0][1] if va < ph[1][2] else ph[1][1] - ph[1][2])
    word = lambda va: struct.unpack_from('<I', b, seg_off(va))[0]
    out = {}
    rl = relocs(b)
    his = []
    for i, (typ, va, base) in enumerate(rl):
        if typ == 2:
            out.setdefault(word(va) + base, []).append(('w32', va, None))
        elif typ == 5:
            his.append(va)
        elif typ == 6:
            lo = word(va) & 0xffff; lo = lo - 0x10000 if lo & 0x8000 else lo
            for h in his:
                tgt = ((word(h) & 0xffff) << 16) + lo + base
                out.setdefault(tgt, []).append(('lo', va, h))
            his_last = his
            # PSP loader: consecutive LO16s pair with the pending HI16 list until a new HI16 appears
            if i + 1 < len(rl) and rl[i + 1][0] != 6: his = []
    return out
