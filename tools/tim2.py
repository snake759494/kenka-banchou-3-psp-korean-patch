"""Minimal TIM2 (single picture, 4bpp/8bpp indexed, linear) read/write."""
import struct
import numpy as np


def info(d):
    assert d[:4] == b'TIM2'
    p = 16
    tot, pal, img, hdr, clrs, fmt, mip, ct, it, w, h = struct.unpack_from('<IIIHHBBBBHH', d, p)
    return dict(tot=tot, pal=pal, img=img, hdr=hdr, clrs=clrs, ct=ct, it=it, w=w, h=h, data=p + hdr, palo=p + hdr + img)


def read(d):
    i = info(d); w, h = i['w'], i['h']
    raw = np.frombuffer(d, np.uint8, i['img'], i['data'])
    if i['it'] == 4:
        px = np.zeros(w * h, np.uint8); px[0::2] = raw & 15; px[1::2] = raw >> 4
    else:
        px = raw.copy()
    pal = np.frombuffer(d, np.uint8, i['pal'], i['palo']).reshape(-1, 4)
    return px.reshape(h, w), pal


def write(d, px):
    i = info(d); d = bytearray(d); px = px.reshape(-1).astype(np.uint8)
    if i['it'] == 4: raw = (px[0::2] & 15) | (px[1::2] << 4)
    else: raw = px
    d[i['data']:i['data'] + i['img']] = raw.tobytes()
    return bytes(d)


def unswizzle(raw, w_bytes, h):
    """PSP swizzle: 16-byte x 8-row blocks, row-major blocks"""
    a = np.frombuffer(raw, np.uint8).reshape(h // 8, w_bytes // 16, 8, 16)
    return a.transpose(0, 2, 1, 3).reshape(h, w_bytes)


def swizzle(lin, w_bytes, h):
    a = np.asarray(lin, np.uint8).reshape(h // 8, 8, w_bytes // 16, 16)
    return a.transpose(0, 2, 1, 3).reshape(-1)


def read_any(d):
    i = info(d); w, h = i['w'], i['h']
    raw = d[i['data']:i['data'] + i['img']]
    bpr = w // 2 if i['it'] == 4 else w
    lin = unswizzle(raw, bpr, h).reshape(-1) if i['ct'] & 0x80 else np.frombuffer(raw, np.uint8)
    if i['it'] == 4:
        px = np.zeros(w * h, np.uint8); px[0::2] = lin & 15; px[1::2] = lin >> 4
    else: px = lin.copy()
    pal = np.frombuffer(d, np.uint8, i['pal'], i['palo']).reshape(-1, 4)
    return px.reshape(h, w), pal


def write_any(d, px):
    i = info(d); d = bytearray(d); w, h = i['w'], i['h']; px = px.reshape(-1).astype(np.uint8)
    lin = (px[0::2] & 15) | (px[1::2] << 4) if i['it'] == 4 else px
    bpr = w // 2 if i['it'] == 4 else w
    raw = swizzle(lin, bpr, h) if i['ct'] & 0x80 else lin
    d[i['data']:i['data'] + i['img']] = raw.tobytes()
    return bytes(d)
