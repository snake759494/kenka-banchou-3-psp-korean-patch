"""Render a Hangul/ASCII glyph into a 16x16 2-bit cell (values 0..3).
The glyph is drawn at `size` px; if its ink box is larger than `box` px it is shrunk to fit.
Ink is centred horizontally and placed on a common baseline."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_cache = {}


def font(name, size):
    k = (name, size)
    if k not in _cache: _cache[k] = ImageFont.truetype(os.path.join(ROOT, name), size)
    return _cache[k]


def render(ch, name='SeoulHangangEB.ttf', size=18, cell=16, ss=4, gamma=0.8, box=15, dy=0, bold=0, solid=False):
    f = font(name, size * ss)
    big = cell * ss * 2
    im = Image.new('L', (big, big), 0)
    d = ImageDraw.Draw(im)
    d.text((big // 4, big // 4), ch, font=f, fill=255)
    a = np.asarray(im)
    ys, xs = np.nonzero(a)
    if not len(xs): return np.zeros((cell, cell), np.uint8)
    # reference vertical frame: the font's em box at this size (keeps a common baseline)
    asc, desc = f.getmetrics()
    em = int(size * ss * 0.88)
    top = big // 4 + (asc + desc - em) // 2 + int(size * ss * 0.05)
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = min(ys.min(), top), max(ys.max() + 1, top + em)
    s = min(1.0, box * ss / (x1 - x0), (box + 1) * ss / (y1 - y0))
    crop = im.crop((x0, y0, x1, y1))
    w, h = max(1, round((x1 - x0) * s)), max(1, round((y1 - y0) * s))
    crop = crop.resize((w, h), Image.LANCZOS)
    canvas = Image.new('L', (cell * ss, cell * ss), 0)
    canvas.paste(crop, ((cell * ss - w) // 2, (cell * ss - h) // 2 + dy * ss))
    if bold: canvas = canvas.filter(ImageFilter.MaxFilter(bold))
    v = np.asarray(canvas.resize((cell, cell), Image.BOX), np.float32) / 255
    if solid:      # like the original font: solid body (3), faint 1px edge (1)
        return np.where(v >= 0.42, 3, np.where(v >= 0.14, 1, 0)).astype(np.uint8)
    v = v ** gamma
    return np.clip(np.rint(v * 3), 0, 3).astype(np.uint8)
