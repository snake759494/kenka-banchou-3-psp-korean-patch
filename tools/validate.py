"""Validate a translated job file.
usage: python tools/validate.py trans/out/ev_00.json [...]
Output file format: same list as trans/jobs/<name>.json, each item gets "kr" (string) or "kr": null (= keep original, e.g. debug/garbage)."""
import json, re, sys, os

ALLOWED_SYM = set('！？…、。・：；（）「」『』～ー―＋－×％＆＊＠☆★○●◎◇◆□■△▲▽▼※→←↑↓♪　０１２３４５６７８９'
                  'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ〜·')


def ok_char(c):
    return '가' <= c <= '힣' or ' ' <= c <= '~' or c == '\n' or c in ALLOWED_SYM


def sjis_len(s):
    return sum(1 if (c == '\n' or ' ' <= c <= '~') else 2 for c in s)


def check(it):
    jp, kr = it['jp'], it.get('kr', '')
    if kr is None: return []
    err = []
    if not isinstance(kr, str) or not kr.strip(): return ['empty']
    if re.findall(r'<[0-9a-f]{2}>', jp) != re.findall(r'<[0-9a-f]{2}>', kr): err.append('control codes differ')
    if re.findall(r'%[0-9]*[sdx]', jp) != re.findall(r'%[0-9]*[sdx]', kr): err.append('format specifiers differ')
    if jp.count('\n') != kr.count('\n'): err.append('newline count %d != %d' % (kr.count('\n'), jp.count('\n')))
    bad = sorted({c for c in re.sub(r'<[0-9a-f]{2}>', '', kr) if not ok_char(c)})
    if bad: err.append('bad chars ' + ''.join(bad))
    if 'max_bytes' in it:
        n = sjis_len(kr)
        if n > it['max_bytes']: err.append('too long: %d bytes > max %d' % (n, it['max_bytes']))
    else:
        jl = [len(re.sub(r'<..>', '', x)) for x in re.split(r'\n|<ff>', jp)]
        for i, x in enumerate(re.split(r'\n|<ff>', kr)):
            L = len(re.sub(r'<..>', '', x))
            lim = min(20, max(16, jl[i] if i < len(jl) else 16))
            if L > lim: err.append('line %d too long (%d > %d)' % (i + 1, L, lim))
    return err


if __name__ == '__main__':
    tot = 0
    for p in sys.argv[1:]:
        out = json.load(open(p, encoding='utf-8'))
        src = json.load(open(p.replace(os.sep + 'out' + os.sep, os.sep + 'jobs' + os.sep).replace('/out/', '/jobs/'), encoding='utf-8'))
        if len(out) != len(src): print(p, 'LENGTH MISMATCH', len(out), len(src)); tot += 1; continue
        for i, (a, b) in enumerate(zip(src, out)):
            if a['jp'] != b['jp']: print(p, i, 'jp changed'); tot += 1; continue
            if 'kr' not in b: print(p, i, 'missing kr'); tot += 1; continue
            e = check(dict(a, kr=b['kr']))
            if e: tot += 1; print(p, i, repr(a['jp']), '=>', repr(b['kr']), '|', '; '.join(e))
    print('errors:', tot)
