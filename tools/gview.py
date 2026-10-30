"""python tools/gview.py OUT scale md5 [md5...]  -> grid sheet (8px minor, 32px major lines)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import images
from PIL import Image, ImageDraw
out, sc = sys.argv[1], int(sys.argv[2])
ims = []
for m in sys.argv[3:]:
    d = open(os.path.join(images.ROOT, 'work/texsrc', m + '.tm2'), 'rb').read()
    px, rp, o = images.decode(d); im = Image.fromarray(images.to_rgba(px, rp), 'RGBA')
    bg = Image.new('RGBA', im.size, (0, 90, 0, 255)); bg.alpha_composite(im)
    bg = bg.resize((im.size[0] * sc, im.size[1] * sc), Image.NEAREST); dr = ImageDraw.Draw(bg)
    for x in range(0, im.size[0], 8): dr.line([(x * sc, 0), (x * sc, bg.size[1])], fill=(255, 255, 0) if x % 32 == 0 else (120, 120, 0))
    for y in range(0, im.size[1], 8): dr.line([(0, y * sc), (bg.size[0], y * sc)], fill=(255, 255, 0) if y % 32 == 0 else (120, 120, 0))
    ims.append(bg)
W = sum(i.size[0] for i in ims) + 6 * len(ims); H = max(i.size[1] for i in ims)
sh = Image.new('RGB', (W, H), (60, 0, 60)); x = 0
for i in ims: sh.paste(i.convert('RGB'), (x, 0)); x += i.size[0] + 6
sh.save(os.path.join(os.environ['TMP'], 'kb', out))
