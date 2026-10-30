"""Write translated SJIS strings into BOOT.BIN.
Fits -> in place.  Too long -> appended to a free pool inside the loaded image and every
reference (R_MIPS_32 words, HI16/LO16 pairs) is redirected.  A HI16 shared with an unrelated
LO16 is only rewritten when the new address keeps the same high half."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import elfrel

FOFF = 0x74


class Pool:
    def __init__(self, ranges):
        self.r = [list(x) for x in ranges]   # [file_off_start, file_off_end)

    def alloc(self, n):
        for x in self.r:
            a = (x[0] + 3) & ~3
            if a + n <= x[1]:
                x[0] = a + n; return a
        raise MemoryError('string pool full')

    def left(self):
        return sum(max(0, b - ((a + 3) & ~3)) for a, b in self.r)


def apply(boot, items, pool):
    """items: [(file_off, encoded_bytes_without_nul, cap)].  returns (boot, failed list, stats)"""
    boot = bytearray(boot)
    R = elfrel.refs(bytes(boot))
    # every LO16 that uses a given HI16 -> its target, to detect sharing
    hi_users = {}
    for tgt, lst in R.items():
        for kind, va, h in lst:
            if kind == 'lo': hi_users.setdefault(h, set()).add(tgt)
    word = lambda va: struct.unpack_from('<I', boot, va + FOFF)[0]
    put = lambda va, w: struct.pack_into('<I', boot, va + FOFF, w)
    fail = []; st = {'inplace': 0, 'moved': 0}
    for off, b, cap in items:
        if len(b) <= cap:
            boot[off:off + cap + 1] = b + bytes(cap + 1 - len(b)); st['inplace'] += 1; continue
        va = off - FOFF
        refs = R.get(va, [])
        if not refs: fail.append((off, 'no refs')); continue
        ok = True
        for kind, rva, h in refs:
            if kind == 'lo' and len(hi_users.get(h, ())) > 1: ok = False
        if not ok:
            fail.append((off, 'shared hi16')); continue
        new = pool.alloc(len(b) + 1)
        boot[new:new + len(b) + 1] = b + b'\0'
        nva = new - FOFF
        for kind, rva, h in refs:
            if kind == 'w32':
                put(rva, word(rva) - va + nva)
            else:
                hi = (nva + 0x8000) >> 16; lo = nva & 0xffff
                put(h, (word(h) & 0xffff0000) | hi)
                put(rva, (word(rva) & 0xffff0000) | lo)
        st['moved'] += 1
    return bytes(boot), fail, st
