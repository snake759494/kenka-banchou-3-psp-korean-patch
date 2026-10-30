"""Build the Korean ISO of Kenka Banchou 3 - Zenkoku Seiha.
  python tools/build.py [--out PATH] [--only-boot]
Inputs : trans/out/*.json (translations), trans/fix.json (optional manual overrides {jp: kr} or {"@off": kr})
Outputs: patched ISO (default: game folder / 싸움대장3_전국제패_한글.iso)"""
import os, sys, json, glob, re, struct, argparse, collections, time, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import kbtext, kfont, lzs, arc, isobuild, tanka, nameentry, images, ebpatch, bpack, images2_spec, icons

ROOT = kbtext.ROOT
ISO = os.path.join(ROOT, 'Kenka Banchou 3 - Zenkoku Seiha (Japan, Asia).iso')
OUT = os.path.join(ROOT, '싸움대장3_전국제패_한글.iso')
USR = os.path.join(ROOT, 'work/iso/PSP_GAME/USRDIR')
KS = [bytes([a, b]).decode('euc-kr') for a in range(0xb0, 0xc9) for b in range(0xa1, 0xff)]
JAMO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'


def load():
    fix = json.load(open(f'{ROOT}/trans/fix.json', encoding='utf-8')) if os.path.exists(f'{ROOT}/trans/fix.json') else {}
    msg, eb = {}, {}
    CAP = {e['off']: e['cap'] for e in json.load(open(f'{ROOT}/work/eboot_str.json', encoding='utf-8'))}
    for p in sorted(glob.glob(f'{ROOT}/trans/out/*.json')):
        if '.part' in p: continue
        for it in json.load(open(p, encoding='utf-8')):
            kr = it.get('kr')
            if 'off' in it:
                kr = fix.get('@%x' % it['off'], kr)
                if kr is not None: eb[it['off']] = (it['jp'], kr, CAP[it['off']])
            elif kr is not None:
                msg[it['jp']] = fix.get(it['jp'], kr)
    for p in sorted(glob.glob(f'{ROOT}/trans/jobs2/m_*.json')):    # message entries cut at a 0x00 trail byte before
        for it in json.load(open(p, encoding='utf-8')): msg[it['jp']] = fix.get(it['jp'], it['kr'])
    for p in sorted(glob.glob(f'{ROOT}/trans/jobs2/e_*.json')):    # SJIS strings the EBOOT extractor missed (1-char etc.)
        for it in json.load(open(p, encoding='utf-8')): eb[it['off']] = (it['jp'], it['kr'], it['cap'])
    return msg, eb


def load_extra():
    """{jp: kr} for table-encoded BOOT.BIN strings (work/tbl_str.json) and the event script pack"""
    tr = json.load(open(f'{ROOT}/work/tbl_auto.json', encoding='utf-8'))
    for p in sorted(glob.glob(f'{ROOT}/trans/jobs2/[xy]_*.json')):
        for it in json.load(open(p, encoding='utf-8')):
            if it['kr']: tr[it['jp']] = it['kr']
    return tr


def norm(s):
    return s.replace('〜', '～').replace('·', '・')


def char_order(msg, eb, ex):
    cnt = collections.Counter()
    for v in msg.values(): cnt.update(c for c in re.sub(r'<..>', '', norm(v)) if '가' <= c <= '힣')
    for v in ex.values(): cnt.update(c for c in re.sub(r'<..>', '', norm(v)) if '가' <= c <= '힣')
    extra = set()
    for _, v, _ in eb.values(): extra.update(c for c in v if '가' <= c <= '힣')
    allc = set(KS) | set(cnt) | extra
    order = sorted(allc, key=lambda c: (-cnt[c], c))
    return order + list(JAMO)


def walk_replace(d, name, repl):
    """repl: {entry_name: bytes}.  Recurses into archives and .lzs; returns new bytes or None if unchanged"""
    if arc.is_arc(d):
        new = {}
        for i, (nm, o, s) in enumerate(arc.parse(d)):
            if nm in repl: new[i] = repl[nm]; continue
            if d[o:o + 4] == b'TIM2':
                h = 'md5:' + hashlib.md5(d[o:o + s]).hexdigest()[:10]
                if h in repl: new[i] = repl[h]; continue
            if nm.endswith(('.pac', '.lzs')) or arc.is_arc(d[o:o + s]):
                r = walk_replace(d[o:o + s], nm, repl)
                if r is not None: new[i] = r
        return arc.rebuild(d, new) if new else None
    if name.endswith('.lzs'):
        r = walk_replace(lzs.decompress(d), name[:-4], repl)
        return lzs.compress(r) if r is not None else None
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=OUT); ap.add_argument('--only-boot', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    T = kbtext.table()
    msg, eb = load()
    ex = load_extra()
    order = char_order(msg, eb, ex)
    cmap = kfont.assign(order, T)
    tmap = kfont.text_cmap(T, cmap)
    print('translated msg', len(msg), 'eboot', len(eb), 'glyphs', len(cmap))

    # ---- message files
    newmes = {}
    miss = collections.Counter()
    for nm in ['DTEventMes', 'DYTankaMes']:
        d = open(f'{ROOT}/work/{nm}.bin', 'rb').read()
        es = kbtext.parse_mes(d); out = []; n = 0
        for e in es:
            jp = kbtext.decode(e, T)
            kr = msg.get(jp)
            if kr is None:
                out.append(e.rstrip(b'\0') + b'\0'); miss[nm] += bool(re.search('[ぁ-ヶ一-龠]', jp)); continue
            out.append(kbtext.encode(norm(kr), tmap)); n += 1
        newmes[nm + '.bin'] = kbtext.build_mes(out)
        print(nm, 'entries', len(es), 'translated', n, 'untranslated', miss[nm], 'size', len(d), '->', len(newmes[nm + '.bin']))

    # ---- BOOT.BIN (ELF): font textures first (their slack becomes the string pool), then strings
    boot = open(kbtext.BOOT, 'rb').read()
    tex = kfont.build_textures(cmap, T)
    boot, pool_ranges = kfont.patch_boot(boot, tex)
    pool = ebpatch.Pool(pool_ranges)
    boot = nameentry.patch(boot, T, cmap, pool)
    boot, tk_pos = tanka.patch_list(boot, eb, T, cmap)
    items = []
    for off, (jp, kr, cap) in sorted(eb.items()):
        s = norm(kr)
        if tanka.PHRASES[0] <= off < tanka.PHRASES[1]: s = tanka.norm_phrase(s)
        items.append((off, kfont.sjis_encode(s, T, cmap), cap))
    nt = 0
    for e in json.load(open(f'{ROOT}/work/tbl_str.json', encoding='utf-8')):
        if e['jp'] in ex:
            items.append((e['off'], kbtext.encode(norm(ex[e['jp']]), tmap)[:-1], e['cap'])); nt += 1
    print('table strings', nt)
    boot, bst, blong = bpack.patch(boot, {k: norm(v) for k, v in ex.items()}, T, cmap)
    print('event pack', bst, 'too long', len(blong))
    boot = bytearray(boot)
    for o, ops in images2_spec.BOOT_TEX.items():        # LZS TIM2 inside .data, followed by the next blob
        cap = 0x290fb4 - o
        c = lzs.compress_opt(images.render(lzs.decompress(bytes(boot[o:o + cap])), ops)[0])
        assert len(c) <= cap, (hex(o), len(c), cap)
        boot[o:o + cap] = c + bytes(cap - len(c))
    for p in sorted(glob.glob(f'{ROOT}/trans/jobs2/u_*.json')):    # UTF-8 strings (savedata / network dialogs)
        for it in json.load(open(p, encoding='utf-8')):
            e = it['kr'].encode('utf-8'); assert len(e) <= it['cap']
            boot[it['off']:it['off'] + it['cap']] = e + bytes(it['cap'] - len(e))
    boot = bytes(boot)
    for u, k, n, m in blong: print('  long', repr(u), repr(k), n, '>', m)
    boot, fail, st = ebpatch.apply(boot, items, pool)
    print('EBOOT strings', st, 'pool left', pool.left(), 'FAILED', len(fail))
    for off, why in fail: print('  fail', hex(off), why, repr(eb[off][1]), len(dict((o, b) for o, b, c in items)[off]), eb[off][2])
    open(f'{ROOT}/work/BOOT_kr.BIN', 'wb').write(boot)
    json.dump(cmap, open(f'{ROOT}/work/cmap.json', 'w', encoding='utf-8'), ensure_ascii=False)
    if a.only_boot: return

    # ---- archives containing the message files / textures
    img = images.build(T, cmap)                    # {entry_name: bytes} textures (incl. tanka font)
    img['kenka_font_tanka00.tm2'] = tanka.texture(tk_pos, tanka_orig())
    ico = icons.icons()                            # XMB / savedata icons with the Korean logo
    repl = dict(newmes); repl.update(img); repl['ICON0.PNG'] = ico.pop('ICON0.PNG')
    files = {}
    for p in sorted(glob.glob(USR + '/**/*.lzs', recursive=True)):
        rel = os.path.relpath(p, USR).replace(os.sep, '/')
        r = walk_replace(open(p, 'rb').read(), os.path.basename(p), repl)
        if r is not None: files[rel] = r
    print('rebuilt lzs', len(files), '%.0fs' % (time.time() - t0))

    if os.path.exists(a.out): os.remove(a.out)
    iso = isobuild.Iso(ISO, a.out)
    st = collections.Counter()
    for rel, d in sorted(files.items()):
        st[iso.replace('/PSP_GAME/USRDIR/' + rel, d)] += 1
    for path, d in ico.items(): st[iso.replace(path, d)] += 1
    iso.replace('/PSP_GAME/SYSDIR/EBOOT.BIN', boot)
    iso.replace('/PSP_GAME/SYSDIR/BOOT.BIN', boot)
    iso.replace('/PSP_GAME/PARAM.SFO', param_sfo(open(f'{ROOT}/work/iso/PSP_GAME/PARAM.SFO', 'rb').read()))
    iso.close()
    print('files', dict(st), '->', a.out, os.path.getsize(a.out), '%.0fs' % (time.time() - t0))


def tanka_orig():
    u = open(f'{ROOT}/work/common.bin', 'rb').read()
    for nm, o, s in arc.parse(u):
        if nm == 'kenka_font_tanka00.tm2': return u[o:o + s]


def param_sfo(d):
    d = bytearray(d)
    kt, dt, n = struct.unpack_from('<III', d, 8)
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', d, 0x14 + 16 * i)
        key = d[kt + ko:d.index(b'\0', kt + ko)]
        if key == b'TITLE':
            t = '싸움대장3 전국제패'.encode('utf-8') + b'\0'
            assert len(t) <= mx
            d[dt + do:dt + do + mx] = t + bytes(mx - len(t))
            struct.pack_into('<I', d, 0x14 + 16 * i + 4, len(t))
    return bytes(d)


if __name__ == '__main__':
    main()
