import sys, os, glob, collections
sys.path.insert(0, os.path.dirname(__file__)); import lzs, arc
R = 'work/iso/PSP_GAME/USRDIR'


def walk(d, path, out):
    if arc.is_arc(d):
        for nm, o, s in arc.parse(d):
            walk(d[o:o + s], path + '/' + nm, out)
    elif path.endswith('.lzs'):
        try: walk(lzs.decompress(d), path + '!', out)
        except Exception as e: out.append((path, len(d), 'ERR ' + str(e)))
    else: out.append((path, len(d), d[:4].hex()))


def files():
    for p in sorted(glob.glob(R + '/**/*.lzs', recursive=True)):
        yield p, os.path.relpath(p, R).replace(os.sep, '/')


if __name__ == '__main__':
    out = []
    for p, rel in files():
        walk(open(p, 'rb').read(), rel, out)
    print(collections.Counter(os.path.splitext(p.rstrip('!'))[1] for p, _, _ in out))
    with open('work/survey.txt', 'w') as f:
        for x in out: f.write('%s\t%d\t%s\n' % x)
