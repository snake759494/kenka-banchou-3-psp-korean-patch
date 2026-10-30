"""Split the text into translation jobs: trans/jobs/*.json"""
import json, os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
J = os.path.join(ROOT, 'trans/jobs'); os.makedirs(J, exist_ok=True)
SKIP = [(0x17d000, 0x1b3100), (0x1b9767, 0x1b9f74), (0x1fafa4, 0x1fcec8), (0x2998b4, 0x2998b4 + 1)]
TANKA = (0x1b9f74, 0x1be240)


def dump(prefix, items, n):
    for k in range(0, len(items), n):
        json.dump(items[k:k + n], open(f'{J}/{prefix}_{k // n:02d}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(prefix, len(items), (len(items) + n - 1) // n)


for nm, pre, n in [('DTEventMes', 'ev', 380), ('DYTankaMes', 'dy', 400)]:
    t = json.load(open(f'{ROOT}/trans/{nm}_jp.json', encoding='utf-8'))
    seen = []; s = set()
    for x in t:
        if x not in s and re.search('[ぁ-ヶ一-龠]', x): s.add(x); seen.append(x)
    dump(pre, [{'jp': x} for x in seen], n)

eb = json.load(open(f'{ROOT}/work/eboot_str.json', encoding='utf-8'))
norm, tf = [], []
for e in eb:
    o = e['off']
    if any(a <= o < b for a, b in SKIP): continue
    if re.search(r'Byte|0x%|error|Error|\n$', e['jp']) and re.search('エラー|メモリ|失敗|警告|error|%08x', e['jp']): continue
    item = {'off': o, 'jp': e['jp'], 'max_bytes': e['cap']}
    (tf if TANKA[0] <= o < TANKA[1] else norm).append(item)
dump('eb', norm, 450)
dump('tf', tf, 760)
