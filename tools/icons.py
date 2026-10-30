"""XMB / savedata icons (ICON0.PNG 144x80): the Japanese logo 喧嘩番長 / 全国制覇 is inpainted away
(the red '3' is kept) and the Korean logo is drawn in the title-logo style.
  icons() -> {name: png bytes} for PSP_GAME/ICON0.PNG, USRDIR/icon/sshot/ICON0.PNG and the copy inside the .lzs archives"""
import os, sys, io
import numpy as np
import cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import images

ROOT = images.ROOT
EHV = 'NanumSquareNeo-eHv.ttf'
OPS = [
    {'op': 'text', 'box': [30, 7, 70, 11], 'text': '켄카 반쵸', 'font': EHV, 'max': 9, 'fill': [214, 32, 40],
     'stroke': [[[255, 255, 255], 1]]},
    {'op': 'text', 'box': [4, 17, 100, 36], 'text': '싸움대장', 'font': EHV, 'max': 32, 'fill': [10, 10, 10],
     'stroke': [[[255, 255, 255], 1], [[210, 20, 20], 1]]},
    {'op': 'text', 'box': [14, 53, 88, 16], 'text': '전 국 제 패', 'font': EHV, 'max': 12, 'fill': [255, 255, 255],
     'stroke': [[[150, 0, 0], 1]]},
]


def korean(png):
    a = np.array(Image.open(io.BytesIO(png)).convert('RGBA'))
    rgb = np.ascontiguousarray(a[..., :3])
    r, g, b = (rgb[..., k].astype(int) for k in range(3))
    red = ((r > 150) & (g < 110) & (b < 110)).astype(np.uint8)
    red[:, :96] = 0
    red = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((4, 4), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(red, connectivity=4)
    three = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)   # the big red 3
    three = cv2.dilate(three, np.ones((5, 5), np.uint8)) > 0
    mask = np.zeros(a.shape[:2], np.uint8); mask[6:74, 4:124] = 1
    mask[three] = 1                               # fill behind the 3 from the background only, then put it back
    fill = cv2.inpaint(rgb, mask * 255, 7, cv2.INPAINT_TELEA)
    fill[three] = rgb[three]
    rgb = fill
    a = np.concatenate([rgb, a[..., 3:]], -1)
    out = images.apply_ops(a, OPS)
    buf = io.BytesIO(); Image.fromarray(out, 'RGBA').save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def icons():
    import lzs, arc
    out = {}
    for rel in ('ICON0.PNG', 'USRDIR/icon/sshot/ICON0.PNG'):
        out['/PSP_GAME/' + rel] = korean(open(f'{ROOT}/work/iso/PSP_GAME/{rel}', 'rb').read())
    d = lzs.decompress(open(f'{ROOT}/work/iso/PSP_GAME/USRDIR/testdata/result.lzs', 'rb').read())
    for nm, o, s in arc.parse(d):
        if nm == 'ICON0.PNG': out['ICON0.PNG'] = korean(d[o:o + s])
    return out


if __name__ == '__main__':
    os.makedirs(f'{ROOT}/work/aud_sheets', exist_ok=True)
    for i, (k, v) in enumerate(icons().items()):
        im = Image.open(io.BytesIO(v)).convert('RGBA')
        bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        bg.resize((im.width * 4, im.height * 4), Image.NEAREST).convert('RGB').save(f'{ROOT}/work/aud_sheets/kicon{i}.png')
        print(k, len(v))
