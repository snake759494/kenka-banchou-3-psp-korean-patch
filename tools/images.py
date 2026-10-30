"""Texture translations.
Spec: trans/images.json = [{"src": "<archive path as in work/tex index>", "md5": "<10 hex>", "ops": [...]}, ...]
ops (coordinates in texture pixels):
  {"op": "clear", "box": [x, y, w, h]}                      -> transparent
  {"op": "fill",  "box": [...], "color": [r, g, b, a]}
  {"op": "bg",    "box": [...], "color": [r, g, b]}        -> every visible pixel in box becomes color (keeps alpha)
  {"op": "copy",  "box": [...], "from": [x, y]}             -> copy a same-size patch (inpainting by cloning)
  {"op": "text",  "box": [...], "text": "...", "font": "NanumSquareNeo-eHv.ttf", "size": 0 (auto),
   "fill": [r,g,b], "stroke": [[r,g,b], w] or [[...],w],[...]], "shadow": [[r,g,b,a], dx, dy],
   "align": "c"|"l"|"r", "valign": "c"|"t"|"b", "vertical": false, "spacing": 0, "aa": true}
Output: build() -> {"md5:<hash>": tm2 bytes}"""
import os, sys, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import tim2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FONTDIRS = [ROOT, os.path.join(ROOT, 'work/fonts')]
SPEC = os.path.join(ROOT, 'trans/images.json')
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        for d in FONTDIRS:
            p = os.path.join(d, name)
            if os.path.exists(p): _fc[k] = ImageFont.truetype(p, size); break
        else: raise FileNotFoundError(name)
    return _fc[k]


# ---------- palette helpers
def csm1(n):
    idx = np.arange(n)
    return (idx & ~0x18) | ((idx & 0x08) << 1) | ((idx & 0x10) >> 1) if n == 256 else idx


def decode(d):
    i = tim2.info(d)
    px, pal = tim2.read_any(d)
    pal = pal.astype(np.int32)
    order = csm1(len(pal)) if i['it'] == 5 else np.arange(len(pal))
    rpal = pal[order]                       # logical index -> rgba (alpha 0..128)
    return px.astype(np.int64), rpal, order


def to_rgba(px, rpal):
    a = np.minimum(255, rpal[:, 3] * 2)
    lut = np.concatenate([rpal[:, :3], a[:, None]], 1).astype(np.uint8)
    return lut[px % len(lut)]


def quantize(rgba, rpal):
    a = np.minimum(255, rpal[:, 3] * 2).astype(np.float32)
    P = np.concatenate([rpal[:, :3].astype(np.float32), a[:, None]], 1)
    X = rgba.reshape(-1, 4).astype(np.float32)
    # premultiplied-ish distance: colour matters less when nearly transparent
    w = np.array([1, 1, 1, 2.0], np.float32)
    out = np.empty(len(X), np.int64)
    for s in range(0, len(X), 1024):
        x = X[s:s + 1024]
        xa = x[:, 3:4] / 255; pa = P[:, 3][None, :] / 255
        dc = ((x[:, None, :3] * xa[:, None] - P[None, :, :3] * pa[:, :, None]) ** 2).sum(2)
        da = ((x[:, None, 3] - P[None, :, 3]) ** 2) * w[3]
        out[s:s + 1024] = np.argmin(dc + da, 1)
    return out.reshape(rgba.shape[:2])


# ---------- drawing
def text_layer(size_wh, op):
    W, H = size_wh
    txt = op['text']; fname = op.get('font', 'NanumSquareNeo-eHv.ttf')
    strokes = op.get('stroke', [])
    if strokes and not isinstance(strokes[0][0], list): strokes = [strokes]
    sw = sum(s[1] for s in strokes)
    vertical = op.get('vertical', False)
    sp = op.get('spacing', 0)
    lines = txt.split('\n')
    ss = 4

    def measure(sz):
        f = font(fname, sz * ss)
        if vertical:
            cw = max(f.getbbox(c)[2] - f.getbbox(c)[0] for c in txt if c != '\n')
            ch = sz * ss + sp * ss
            return cw + 2 * sw * ss, ch * len(txt) - sp * ss + 2 * sw * ss
        ws = [f.getbbox(l)[2] - f.getbbox(l)[0] + max(0, len(l) - 1) * sp * ss for l in lines]
        asc, desc = f.getmetrics()
        lh = int(sz * ss * op.get('lh', 1.1))
        return max(ws) + 2 * sw * ss, lh * (len(lines) - 1) + sz * ss + 2 * sw * ss
    sz = op.get('size', 0)
    if not sz:
        sz = op.get('max', 64)
        while sz > 6:
            w, h = measure(sz)
            if w <= W * ss and h <= H * ss: break
            sz -= 1
    f = font(fname, sz * ss)
    w, h = measure(sz)
    sx = op.get('sx', 1.0)
    canvas = Image.new('L', (W * ss * 2, H * ss * 2), 0)
    d = ImageDraw.Draw(canvas)
    al, va = op.get('align', 'c'), op.get('valign', 'c')
    ox = {'l': sw * ss, 'c': (W * ss - w) // 2 + sw * ss, 'r': W * ss - w + sw * ss}[al]
    oy = {'t': sw * ss, 'c': (H * ss - h) // 2 + sw * ss, 'b': H * ss - h + sw * ss}[va]
    ox += op.get('dx', 0) * ss; oy += op.get('dy', 0) * ss
    if vertical:
        y = oy
        for c in txt:
            bb = f.getbbox(c)
            d.text((ox + (w - 2 * sw * ss - (bb[2] - bb[0])) // 2 - bb[0], y - int(sz * ss * 0.12)), c, font=f, fill=255)
            y += sz * ss + sp * ss
    else:
        lh = int(sz * ss * op.get('lh', 1.1))
        asc, desc = f.getmetrics()
        for k, l in enumerate(lines):
            bb = f.getbbox(l)
            lw = bb[2] - bb[0] + max(0, len(l) - 1) * sp * ss
            x = ox + {'l': 0, 'c': (w - 2 * sw * ss - lw) // 2, 'r': w - 2 * sw * ss - lw}[al] - bb[0]
            y = oy + k * lh - (bb[1] if len(lines) == 1 else int(sz * ss * 0.12))
            if sp:
                for c in l:
                    d.text((x, y), c, font=f, fill=255); x += f.getbbox(c)[2] - f.getbbox(c)[0] + sp * ss
            else:
                d.text((x, y), l, font=f, fill=255)
    canvas = canvas.crop((0, 0, W * ss, H * ss))
    if sx != 1.0:
        cw = int(W * ss * sx); sc = canvas.resize((cw, H * ss), Image.LANCZOS)
        canvas = Image.new('L', (W * ss, H * ss), 0); canvas.paste(sc, ((W * ss - cw) // 2, 0))
    layers = []        # (mask, colour) from outermost to innermost
    acc = canvas
    rings = []
    tot = 0
    for col, wd in strokes:
        tot += wd
        rings.append((canvas.filter(ImageFilter.MaxFilter(2 * tot * ss + 1)), col))
    for m, col in reversed(rings): layers.append((m, col))
    layers.append((canvas, op.get('fill', [255, 255, 255])))
    return layers, ss


def apply_ops(rgba, ops):
    img = Image.fromarray(rgba, 'RGBA')
    for op in ops:
        x, y, w, h = op['box']
        if op['op'] == 'clear':
            img.paste((0, 0, 0, 0), (x, y, x + w, y + h))
        elif op['op'] == 'fill':
            img.paste(tuple(op['color']), (x, y, x + w, y + h))
        elif op['op'] == 'bg':
            a = np.array(img); reg = a[y:y + h, x:x + w]
            m = reg[..., 3] > op.get('amin', 0)
            if 'wmin' in op: m &= reg[..., :3].min(-1) >= op['wmin']
            reg[m, :3] = op['color']
            if 'alpha' in op: reg[m, 3] = op['alpha']
            img = Image.fromarray(a, 'RGBA')
        elif op['op'] == 'key':
            a = np.array(img); reg = a[y:y + h, x:x + w].astype(np.int32)
            m = np.zeros(reg.shape[:2], bool)
            for col, tol in op['match']:
                m |= (np.abs(reg[..., :3] - np.array(col)).max(-1) <= tol) & (reg[..., 3] > 0)
            if 'pred' in op and op['pred'] == 'reddish':
                m |= (reg[..., 0] > 140) & (reg[..., 1] < 120) & (reg[..., 2] < 120) & (reg[..., 3] > 0)
            if op.get('grow'):
                from scipy import ndimage
                m = ndimage.binary_dilation(m, iterations=op['grow'])
            sub = a[y:y + h, x:x + w]; sub[m] = op['to']
            img = Image.fromarray(a, 'RGBA')
        elif op['op'] == 'copy':
            fx, fy = op['from']; patch = img.crop((fx, fy, fx + w, fy + h)); img.paste(patch, (x, y))
        elif op['op'] == 'text':
            layers, ss = text_layer((w, h), op)
            sh = op.get('shadow')
            base = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
            if sh:
                m = layers[0][0]
                sm = Image.new('L', m.size, 0); sm.paste(m, (sh[1] * ss, sh[2] * ss))
                col = tuple(sh[0][:3]) + (255,)
                base.paste(Image.new('RGBA', m.size, col), (0, 0), sm.point(lambda v: v * sh[0][3] // 255))
            for m, col in layers:
                base.paste(Image.new('RGBA', m.size, tuple(col[:3]) + (255,)), (0, 0), m)
            small = base.resize((w, h), Image.LANCZOS if op.get('aa', True) else Image.NEAREST)
            if op.get('hard'):
                arr = np.array(small); arr[..., 3] = np.where(arr[..., 3] > 110, 255, 0); small = Image.fromarray(arr)
            region = img.crop((x, y, x + w, y + h))
            region.alpha_composite(small)
            img.paste(region, (x, y))
    return np.array(img)


def render(d, ops):
    px, rpal, order = decode(d)
    rgba = to_rgba(px, rpal)
    out = apply_ops(rgba, ops)
    q = quantize(out, rpal)                       # logical palette index
    phys = np.argsort(order)[q] if False else order[q]
    return tim2.write_any(d, phys.astype(np.uint8)), out


def preview(d, ops, path, scale=2):
    _, out = render(d, ops)
    im = Image.fromarray(out, 'RGBA')
    bg = Image.new('RGBA', im.size, (0, 90, 0, 255)); bg.alpha_composite(im)
    bg.resize((im.size[0] * scale, im.size[1] * scale), Image.NEAREST).save(path)


def load_spec():
    out = []
    for p in (SPEC, SPEC.replace('images.json', 'images2.json')):
        if os.path.exists(p): out += json.load(open(p, encoding='utf-8'))
    return out


def build(T=None, cmap=None):
    """returns {'md5:<10hex>': new tm2 bytes} using originals from work/texsrc/<md5>.tm2"""
    out = {}
    for sp in load_spec():
        src = os.path.join(ROOT, 'work/texsrc', sp['md5'] + '.tm2')
        d = open(src, 'rb').read()
        out['md5:' + sp['md5']], _ = render(d, sp['ops'])
    return out
