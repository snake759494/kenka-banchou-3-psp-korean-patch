"""Table-encoded (kbtext) strings in BOOT.BIN outside the message files: dictionary, shop lines, item/outfit names.
Taken sequentially from the text regions below. -> work/tbl_str.json [{off, cap, jp}]"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import kbtext

REGIONS = [(0x1763bc, 0x176400), (0x1ccc20, 0x1ccc40), (0x1d5e94, 0x1d6268), (0x1d8640, 0x1dcc2c),
           (0x1dcd1c, 0x1dd000), (0x1df680, 0x1e05b0)]
JP = re.compile('[ぁ-ゖァ-ヺ一-龠]')
JUNK = re.compile('^[ァ-ヶぁ-ゖ]{1,3}$')


def valid(b, o, T):
    j = o
    while b[j]:
        c = b[j]
        if 0xe0 <= c < 0xef:
            if ((c - 0xe0) << 8 | b[j + 1]) + 0xdf >= len(T): return None
            j += 2
        else: j += 1
    return j


def extract(b, T):
    out = []
    for lo, hi in REGIONS:
        o = lo
        while o < hi:
            if b[o] == 0: o += 1; continue
            e = kbtext.strend(b, o)
            if valid(b, o, T) is not None and not all(0x20 <= c < 0x7f for c in b[o:e]):
                s = kbtext.decode(b[o:e + 1], T)
                if JP.search(s):
                    k = e + 1
                    while k < len(b) and b[k] == 0: k += 1
                    out.append({'off': o, 'cap': k - o - 1, 'jp': s})
            o = e + 1
    return out


if __name__ == '__main__':
    T = kbtext.table(); b = open(kbtext.BOOT, 'rb').read()
    r = extract(b, T)
    json.dump(r, open(os.path.join(kbtext.ROOT, 'work/tbl_str.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    open(os.path.join(kbtext.ROOT, 'work/peek.txt'), 'w', encoding='utf-8').write('\n'.join('%x %d %s' % (x['off'], x['cap'], x['jp'].replace('\n', '⏎')) for x in r))
    print(len(r), sum(len(x['jp']) for x in r))
