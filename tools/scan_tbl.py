"""Find table-encoded (kbtext) strings in BOOT.BIN: python tools/scan_tbl.py -> work/tbl_str.json"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
import kbtext

KANA = re.compile('[ぁ-ゖァ-ヺ]')


def scan(b, T):
    out = []; i = 0; n = len(b)
    while i < n:
        if b[i] == 0: i += 1; continue
        j = i; ok = True; chars = []
        while j < n and b[j]:
            c = b[j]
            if 0xe0 <= c < 0xef:
                if j + 1 >= n or b[j + 1] == 0: ok = False; break
                k = ((c - 0xe0) << 8 | b[j + 1]) + 0xdf
                if k >= len(T): ok = False; break
                chars.append(T[k]); j += 2
            elif c >= 0xef:
                if c not in (0xfe, 0xff, 0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xf6, 0xf7, 0xf8, 0xf9, 0xfa, 0xfb, 0xfc, 0xfd): ok = False
                chars.append('\n'); j += 1
            else:
                chars.append(T[c - 1]); j += 1
        s = ''.join(chars)
        if ok and len(s) >= 2 and len(KANA.findall(s)) >= max(1, len(s) // 5) and not re.search('[\x00-\x1f]', s.replace('\n', '')):
            out.append((i, j - i, kbtext.decode(b[i:j + 1], T)))
        i = j + 1
    return out


if __name__ == '__main__':
    T = kbtext.table()
    b = open(kbtext.BOOT, 'rb').read()
    r = scan(b, T)
    json.dump([{'off': o, 'len': l, 'jp': s} for o, l, s in r], open(os.path.join(kbtext.ROOT, 'work/tbl_str.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(r))
