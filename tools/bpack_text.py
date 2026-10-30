"""SJIS strings inside the BOOT.BIN event script pack (see bpack.py).
A string sits in an instruction [op u8][size u8][u16 0][string\0][tail]; it is rewritten in place with the
same byte length (shorter translations padded with ASCII spaces) so instruction sizes never change."""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
import bpack, lzs

PAT = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]|\r\n)+\x00')


def strings(d):
    out = []
    for m in PAT.finditer(d):
        s = m.start(); t = m.group()[:-1]
        if s < 4 or d[s - 2:s] != b'\0\0': continue
        size = d[s - 3]
        if not 0 <= size - 4 - len(t) - 1 <= 8: continue
        try: u = t.decode('cp932').replace('\r\n', '\n')
        except UnicodeDecodeError: continue
        if not re.search('[ぁ-ヶ一-龠ー]', u): continue
        out.append((s, len(t), u))
    return out


def extract(b):
    base, ents = bpack.parse(b)
    res = []
    for nm, off, sz in ents:
        d = lzs.decompress(b[off:off + sz])
        for s, n, u in strings(d): res.append(dict(file=nm, pos=s, len=n, jp=u))
    return res


if __name__ == '__main__':
    b = open(os.path.join(bpack.ROOT if hasattr(bpack, 'ROOT') else '.', 'work/iso/PSP_GAME/SYSDIR/BOOT.BIN'), 'rb').read()
    r = extract(b)
    json.dump(r, open('work/bpack_str.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    u = sorted(set(x['jp'] for x in r))
    open('work/bpack_uniq.txt', 'w', encoding='utf-8').write('\n'.join(u))
    print(len(r), len(u))
