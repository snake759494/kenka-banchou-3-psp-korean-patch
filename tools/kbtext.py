"""Kenka Banchou 3 text codec.  Glyph index i (0..4095): i<0xdf -> byte i+1, else 0xe0|((i-0xdf)>>8), (i-0xdf)&0xff.
Bytes >= 0xef are control codes (0xfe newline ...).  Shown as <xx> in text form; '\n' for 0xfe."""
import struct, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BOOT = os.path.join(ROOT, 'work/iso/PSP_GAME/SYSDIR/BOOT.BIN')
TBL_OFF = 0x16c704


def table():
    b = open(BOOT, 'rb').read()
    return b[TBL_OFF:b.index(b'\0', TBL_OFF)].decode('cp932')


def decode(x, T):
    out = []; i = 0
    while i < len(x):
        c = x[i]; i += 1
        if c == 0: break
        if 0xe0 <= c < 0xef:
            n = ((c - 0xe0) << 8 | x[i]) + 0xdf; i += 1
            out.append(T[n] if n < len(T) and T[n] != '\u3000' or n == 0x162 else '{%d}' % n)
        elif c == 0xfe: out.append('\n')
        elif c >= 0xef: out.append('<%02x>' % c)
        else: out.append(T[c - 1])
    return ''.join(out)


def encode(s, cmap):
    """cmap: char -> glyph index"""
    out = bytearray(); i = 0
    while i < len(s):
        ch = s[i]
        if ch == '<' and re.match(r'<[0-9a-f]{2}>', s[i:i + 4]):
            out.append(int(s[i + 1:i + 3], 16)); i += 4; continue
        if ch == '{':
            j = s.index('}', i); n = int(s[i + 1:j]); i = j + 1
        else:
            if ch == '\n': out.append(0xfe); i += 1; continue
            n = cmap[ch]; i += 1
        if n < 0xdf: out.append(n + 1)
        else:
            n -= 0xdf; out += bytes([0xe0 | n >> 8, n & 0xff])
    return bytes(out) + b'\0'


def parse_mes(d):
    first = struct.unpack_from('<I', d)[0]
    n = first // 4
    offs = [struct.unpack_from('<I', d, 4 * i)[0] for i in range(n)]
    return [d[o:strend(d, o) + 1] for o in offs]


def strend(d, o):
    """index of the terminating NUL (a 2-byte code may have 0x00 as its second byte)"""
    while d[o]:
        o += 2 if 0xe0 <= d[o] < 0xef else 1
    return o


def build_mes(entries):
    n = len(entries); out = bytearray(4 * n)
    for i, e in enumerate(entries):
        struct.pack_into('<I', out, 4 * i, len(out)); out += e
    return bytes(out)
