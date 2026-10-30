"""Dump unique UI textures (TIM2) to PNG + contact sheets.  usage: python tools/tex_dump.py OUTDIR"""
import sys, os, glob, hashlib, json
sys.path.insert(0, os.path.dirname(__file__))
import lzs, arc, tim2, survey
import numpy as np
from PIL import Image, ImageDraw

SKIP_DIR = ('charadata/',)


def to_rgba(d):
    i = tim2.info(d)
    px, pal = tim2.read_any(d)
    pal = pal.astype(np.uint16)
    if i['it'] == 5 and len(pal) == 256:      # 8bpp: CSM1 palette swizzle
        idx = np.arange(256); blk = (idx & ~0x18) | ((idx & 0x08) << 1) | ((idx & 0x10) >> 1)
        pal = pal[blk]
    a = pal[:, 3].copy(); a = np.minimum(255, a * 2) if a.max() <= 128 else a
    rgba = np.concatenate([pal[:, :3], a[:, None]], 1).astype(np.uint8)
    return rgba[px.astype(np.int64) % len(rgba)]


def collect():
    seen = {}
    for p, rel in survey.files():
        if rel.startswith(SKIP_DIR): continue
        def walk(d, path):
            if arc.is_arc(d):
                for nm, o, s in arc.parse(d): walk(d[o:o + s], path + '/' + nm)
            elif path.endswith('.lzs'): walk(lzs.decompress(d), path + '!')
            elif d[:4] == b'TIM2':
                h = hashlib.md5(d).hexdigest()[:10]
                seen.setdefault(h, (path, d))
        walk(open(p, 'rb').read(), rel)
    return seen


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    seen = collect(); idx = {}
    for h, (path, d) in seen.items():
        nm = path.split('/')[-1]
        if nm.startswith(('npc_', 'tex_', 'mtl_', 'item_', 'we_', 'obj', 'hair', 'ha_', 'up_', 'lo_', 'ft_', 'env', 'pt_', 'car_', 'TH_', 'fa_', 'gl_', 'hd_', 'ma_', 'e_0')): continue
        try: im = Image.fromarray(to_rgba(d), 'RGBA')
        except Exception as e: print('fail', path, e); continue
        fn = f'{nm[:-4]}_{h}.png'
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'work/texsrc'), exist_ok=True)
        open(os.path.join(os.path.dirname(__file__), '..', 'work/texsrc', h + '.tm2'), 'wb').write(d)
        im.save(os.path.join(out, fn)); idx[fn] = path
    json.dump(idx, open(os.path.join(out, 'index.json'), 'w'), indent=0)
    print(len(idx))
