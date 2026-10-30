"""Find word blobs in a texture: python tools/seg.py <md5> [dilate] [minarea]"""
import sys, os
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
import images


def boxes(md5, dil=4, minarea=30, amin=20):
    d = open(os.path.join(images.ROOT, 'work/texsrc', md5 + '.tm2'), 'rb').read()
    px, rpal, order = images.decode(d)
    rgba = images.to_rgba(px, rpal)
    m = rgba[..., 3] > amin
    md = ndimage.binary_dilation(m, iterations=dil)
    lab, n = ndimage.label(md)
    out = []
    for sl in ndimage.find_objects(lab):
        y, x = sl[0].start, sl[1].start; h, w = sl[0].stop - y, sl[1].stop - x
        if m[sl].sum() >= minarea: out.append([int(x), int(y), int(w), int(h)])
    out.sort(key=lambda b: (b[1] // 16, b[0]))
    return out, rgba


if __name__ == '__main__':
    bs, rgba = boxes(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4, int(sys.argv[3]) if len(sys.argv) > 3 else 30)
    print(rgba.shape)
    for b in bs: print(b)
