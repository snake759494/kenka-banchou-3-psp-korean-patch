"""List SJIS strings in BOOT.BIN .rodata/.data (file offsets). writes work/eboot_str.json"""
import re, json, sys
b = open('work/iso/PSP_GAME/SYSDIR/BOOT.BIN', 'rb').read()
LO, HI = 0x1663e4, 0x1ff514 + 0xb98cf
TBL = (0x16c704, b.index(b'\0', 0x16c704))
out = []
TS = set(b[TBL[0]:TBL[1]].decode('cp932')) - {'　'} | {'　'}
i = LO
pat = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x09\x0a\x20-\x7e\xa1-\xdf])+')
for m in pat.finditer(b, LO, HI):
    s, e = m.start(), m.end()
    if b[e:e + 1] != b'\0' or b[s - 1:s] != b'\0': continue
    if TBL[0] <= s < TBL[1]: continue
    try: t = b[s:e].decode('cp932')
    except UnicodeDecodeError: continue
    if not re.search('[ぁ-ヶー一-龠]', t): continue
    if any(not (c in TS or c in '\n\t' or ' ' <= c <= '~') for c in t): continue
    if sum(c in TS for c in t) < 2: continue
    if len(t) <= 4 and not re.search('[ぁ-ヶー]', t) and not re.search('^[一-龠]+$', t): continue
    if 0x1ff514 <= s < 0x1ff514 + 0x95000: continue  # compressed blobs in .data
    cap = e - s
    lim = (e + 4) // 4 * 4 - 1 - s    # stay inside this string's 4-byte aligned slot
    while cap < lim and b[s + cap + 1:s + cap + 2] == b'\0': cap += 1   # trailing NUL padding usable
    out.append(dict(off=s, jp=t, cap=cap))
json.dump(out, open('work/eboot_str.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(out), sum(len(x['jp']) for x in out))
