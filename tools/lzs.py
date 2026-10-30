"""LZS: u32 raw size + Okumura LZSS (N=4096, F=18, THRESHOLD=2, ring init 0, r=0xfee, flag LSB first, 1=literal)"""
import struct, sys


try:
    import numba, numpy as np

    @numba.njit(cache=True)
    def _dec(src, n):
        out = np.zeros(n, np.uint8); ring = np.zeros(4096, np.uint8)
        r = 0xfee; i = 4; o = 0; flags = 0
        while o < n:
            flags >>= 1
            if not flags & 0x100:
                flags = src[i] | 0xff00; i += 1
            if flags & 1:
                c = src[i]; i += 1
                out[o] = c; o += 1; ring[r] = c; r = (r + 1) & 0xfff
            else:
                a = src[i]; b = src[i + 1]; i += 2
                p = a | (b & 0xf0) << 4; l = (b & 0xf) + 3
                for k in range(l):
                    c = ring[(p + k) & 0xfff]
                    if o < n: out[o] = c
                    o += 1; ring[r] = c; r = (r + 1) & 0xfff
        return out

    def decompress(d):
        n = struct.unpack_from('<I', d)[0]
        return _dec(np.frombuffer(d, np.uint8), n).tobytes()

    @numba.njit(cache=True)
    def _comp(src):
        n = len(src)
        out = np.zeros(n + n // 8 + 16, np.uint8)
        head = np.full(1 << 16, -1, np.int64); prev = np.full(max(n, 1), -1, np.int64)
        o = 0; i = 0
        while i < n:
            fpos = o; o += 1; flags = 0
            for bit in range(8):
                if i >= n: break
                bl = 0; best = 0
                if i + 3 <= n:
                    h = (src[i] << 8 ^ src[i + 1] << 4 ^ src[i + 2]) & 0xffff
                    p = head[h]; tries = 0
                    mx = min(18, n - i)
                    while p >= 0 and i - p <= 4078 and tries < 128:
                        if src[p] == src[i] and src[p + 1] == src[i + 1] and src[p + 2] == src[i + 2]:
                            l = 3
                            while l < mx and src[p + l] == src[i + l]: l += 1
                            if l > bl:
                                bl = l; best = p
                                if l == mx: break
                        p = prev[p]; tries += 1
                if bl >= 3:
                    off = (best + 0xfee) & 0xfff
                    out[o] = off & 0xff; out[o + 1] = ((off >> 4) & 0xf0) | (bl - 3); o += 2
                    for k in range(bl):
                        q = i + k
                        if q + 3 <= n:
                            h2 = (src[q] << 8 ^ src[q + 1] << 4 ^ src[q + 2]) & 0xffff
                            prev[q] = head[h2]; head[h2] = q
                    i += bl
                else:
                    flags |= 1 << bit; out[o] = src[i]; o += 1
                    if i + 3 <= n:
                        h2 = (src[i] << 8 ^ src[i + 1] << 4 ^ src[i + 2]) & 0xffff
                        prev[i] = head[h2]; head[h2] = i
                    i += 1
            out[fpos] = flags
        return out[:o]

    def compress(d):
        return struct.pack('<I', len(d)) + _comp(np.frombuffer(d, np.uint8)).tobytes()
except ImportError:
    pass


def decompress_py(d):
    n = struct.unpack_from('<I', d)[0]
    ring = bytearray(4096); r = 0xfee
    out = bytearray(); i = 4; flags = 0
    while len(out) < n:
        flags >>= 1
        if not flags & 0x100:
            flags = d[i] | 0xff00; i += 1
        if flags & 1:
            c = d[i]; i += 1
            out.append(c); ring[r] = c; r = (r + 1) & 0xfff
        else:
            a, b = d[i], d[i + 1]; i += 2
            o = a | (b & 0xf0) << 4; l = (b & 0xf) + 3
            for k in range(l):
                c = ring[(o + k) & 0xfff]
                out.append(c); ring[r] = c; r = (r + 1) & 0xfff
    return bytes(out[:n])


def compress_py(d):
    """greedy LZSS with hash chains; refs into the zero-filled initial ring are not used."""
    n = len(d); out = bytearray(struct.pack('<I', n))
    head = {}; prev = [-1] * n
    i = 0
    def ins(p):
        if p + 3 <= n:
            k = d[p:p + 3]; prev[p] = head.get(k, -1); head[k] = p
    while i < n:
        fpos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n: break
            best, bl = 0, 0
            if i + 3 <= n:
                p = head.get(d[i:i + 3], -1); tries = 0
                mx = min(18, n - i)
                while p >= 0 and i - p <= 4078 and tries < 64:
                    l = 3
                    while l < mx and d[p + l] == d[i + l]: l += 1
                    if l > bl: bl, best = l, p
                    if l == mx: break
                    p = prev[p]; tries += 1
            if bl >= 3:
                o = (best + 0xfee) & 0xfff
                out += bytes([o & 0xff, (o >> 4) & 0xf0 | (bl - 3)])
                for k in range(bl): ins(i + k)
                i += bl
            else:
                flags |= 1 << bit; out.append(d[i]); ins(i); i += 1
        out[fpos] = flags
    return bytes(out)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); u = decompress(d)
    if len(sys.argv) > 2: open(sys.argv[2], 'wb').write(u)
    print(len(d), '->', len(u))


def compress_opt(d, tries=256):
    """optimal-parse LZSS (bit-cost DP over hash-chain matches; zero runs may also reference the
    zero-filled initial ring).  Smaller output than compress() for small files."""
    n = len(d); head = {}; prev = [-1] * n
    for p in range(n - 2):
        k = d[p:p + 3]; prev[p] = head.get(k, -1); head[k] = p
    # matches[i] = (len, src) longest found; shorter lengths reuse the same src
    best = [(0, 0)] * n
    nxt = {}
    for i in range(n - 2):
        k = d[i:i + 3]
        p = prev[i]; t = 0; bl, bs = 0, 0; mx = min(18, n - i)
        while p >= 0 and i - p <= 4078 and t < tries:
            l = 3
            while l < mx and d[p + l] == d[i + l]: l += 1
            if l > bl: bl, bs = l, p
            if l == mx: break
            p = prev[p]; t += 1
        if False and i + 18 <= 4078 and d[i] == 0:
            z = 0
            while z < mx and d[i + z] == 0: z += 1
            if z >= 3 and z > bl: bl, bs = z, -18
        best[i] = (bl, bs)
    INF = 1 << 60
    cost = [INF] * (n + 1); cost[n] = 0; choice = [0] * n
    for i in range(n - 1, -1, -1):
        c = cost[i + 1] + 9; ch = 0
        bl = best[i][0]
        for l in range(3, bl + 1):
            v = cost[i + l] + 17
            if v < c: c, ch = v, l
        cost[i] = c; choice[i] = ch
    out = bytearray(struct.pack('<I', n)); i = 0
    while i < n:
        fpos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n: break
            l = choice[i]
            if l:
                o = (best[i][1] + 0xfee) & 0xfff
                out += bytes([o & 0xff, (o >> 4) & 0xf0 | (l - 3)]); i += l
            else:
                flags |= 1 << bit; out.append(d[i]); i += 1
        out[fpos] = flags
    return bytes(out)
