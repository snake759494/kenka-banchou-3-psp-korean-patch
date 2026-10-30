"""Generates trans/images2.json (second texture pass: title logo, tanka prompt, diary, status, shops ...).
Background colours are sampled from the original textures."""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import images

ROOT = images.ROOT
EHV = 'NanumSquareNeo-eHv.ttf'; DEB = 'NanumSquareNeo-dEb.ttf'
SHM = 'SeoulHangangM.ttf'; SHB = 'SeoulHangangB.ttf'; G11 = 'Galmuri11-Bold.ttf'; G9 = 'Galmuri9.ttf'


def rgba(md5):
    d = open(f'{ROOT}/work/texsrc/{md5}.tm2', 'rb').read()
    px, rpal, _ = images.decode(d)
    return images.to_rgba(px, rpal)


def col(md5, x, y, w=4, h=4):
    a = rgba(md5)[y:y + h, x:x + w].reshape(-1, 4).astype(int)
    return [int(v) for v in np.median(a, 0)]


def T(box, text, font=EHV, **k):
    d = {'op': 'text', 'box': box, 'text': text, 'font': font}; d.update(k); return d


def F(box, c): return {'op': 'fill', 'box': box, 'color': c}
def C(box): return {'op': 'clear', 'box': box}
def PX(**k): return dict(aa=False, hard=True, **k)


BLK_WR = dict(fill=[10, 10, 10], stroke=[[[255, 255, 255], 2], [[210, 20, 20], 2]])
S = []

# title logo 256x160: ケンカバンチョウ / 喧嘩番長 / 全国制覇
S.append({'src': 'title_kenkalogo', 'md5': '9f42ccb613', 'ops': [
    C([0, 0, 256, 106]),
    {'op': 'key', 'box': [30, 104, 210, 50], 'match': [[[255, 255, 255], 90]], 'to': [214, 32, 40, 255], 'grow': 1},
    T([60, 4, 136, 22], '켄카 반쵸', EHV, max=16, fill=[214, 32, 40], stroke=[[[255, 255, 255], 1]]),
    T([4, 24, 248, 82], '싸움대장', EHV, max=70, **BLK_WR),
    T([46, 108, 196, 36], '전 국 제 패', EHV, max=26, fill=[255, 255, 255], stroke=[[[150, 0, 0], 1]]),
]})
# tanka prompt 512x96
S.append({'src': 'menu_tanka_huki00', 'md5': 'cfa2ba8a27', 'ops': [
    C([0, 0, 512, 96]),
    T([4, 6, 500, 84], '버튼을 눌러 탄카를 날려라!', EHV, max=54, fill=[230, 20, 20],
      stroke=[[[20, 0, 0], 3], [[255, 255, 255], 2]]),
]})
# album menu 256x128: 武勇伝 / 旅日記 on red strokes
S.append({'src': 'album_menu', 'md5': 'd54b35e9a0', 'ops': [
    {'op': 'key', 'box': [0, 0, 256, 128], 'match': [[[0, 0, 0], 110], [[255, 255, 255], 120], [[128, 128, 128], 60]],
     'to': [200, 10, 10, 255]},
    T([30, 4, 200, 56], '무용담', EHV, max=46, fill=[10, 10, 10], stroke=[[[255, 255, 255], 2]]),
    T([30, 66, 200, 56], '여행 일기', EHV, max=42, fill=[10, 10, 10], stroke=[[[255, 255, 255], 2]]),
]})
# diary list 256x192 (rows of 24px, dark blue-grey text)
c = [55, 75, 125]
rows = ['1일째 : 교토 도착', '2일째 : 키요미즈데라 관광', '3일째 : 니조성 관광', '4일째 : 키타노 텐만구 관광',
        '5일째 : 자유 행동', '6일째 : 토게츠 다리 관광', '7일째 : 자유 행동']
ops = [C([0, 0, 256, 192])]
for i, r in enumerate(rows): ops.append(T([8, i * 24 + 2, 246, 20], r, SHB, max=16, fill=c, align='l'))
ops.append(T([60, 168, 140, 22], '여행 메모', SHB, max=16, fill=c))
S.append({'src': 'diary_font00', 'md5': '468d19107c', 'ops': ops})
# diary pieces 256x96
c = [30, 30, 40]
ops = [C([0, 0, 256, 96])]
for box, t in [([4, 2, 60, 28], '여행'), ([66, 2, 58, 28], '일째'), ([126, 2, 68, 28], '마지막날'), ([196, 2, 56, 28], '메모'),
               ([4, 34, 60, 28], '오전'), ([66, 34, 58, 28], '오후'), ([130, 34, 60, 28], '귀로')]:
    ops.append(T(box, t, SHB, max=24, fill=c))
for k in range(7): ops.append(T([2 + k * 32, 66, 28, 28], str(k + 1), SHB, max=24, fill=c))
S.append({'src': 'diary_font01', 'md5': '51caf278a0', 'ops': ops})
# diary top page 512x272
h = '04b667eddb'
S.append({'src': 'diary_bgtop', 'md5': h, 'ops': [
    {'op': 'copy', 'box': [86, 48, 44, 32], 'from': [24, 48]}, {'op': 'copy', 'box': [130, 48, 44, 32], 'from': [24, 48]},
    T([86, 48, 88, 30], '여행 일기', SHM, max=24, fill=[60, 80, 130]),
    {'op': 'copy', 'box': [306, 40, 120, 24], 'from': [306, 110]},
    T([306, 40, 120, 24], '수학여행 예정', SHM, max=18, fill=[60, 80, 130]),
    F([38, 170, 84, 26], col(h, 150, 178)), T([38, 170, 84, 26], '추억', EHV, max=20, fill=[255, 255, 255]),
    {'op': 'copy', 'box': [296, 236, 140, 22], 'from': [296, 190]}, T([296, 236, 140, 22], '오후는 전부 자유 행동', SHM, max=14, fill=[60, 80, 130]),
]})
# result units 256x48 (row 32..48, 16px cells)
ops = [C([0, 32, 256, 16])]
for x, w, t in [(0, 32, '시간'), (48, 16, '명'), (80, 16, '회'), (112, 16, '엔'), (144, 16, '현'), (176, 16, '분')]:
    ops.append(T([x, 32, w, 16], t, G11, size=12, fill=[255, 255, 255], stroke=[[[40, 40, 40], 1]], **PX()))
S.append({'src': 'eva_number', 'md5': '65945c37f6', 'ops': ops})
# HUD gauges 128x32: 体 / 仲
for h, t, bgc in [('d5571844bc', '체', [60, 110, 200, 255]), ('d6501fc064', '동', [200, 40, 60, 255])]:
    S.append({'src': 'gauge_hp', 'md5': h, 'ops': [
        {'op': 'key', 'box': [4, 3, 24, 24], 'match': [[[255, 255, 255], 100]], 'to': bgc},
        T([3, 3, 26, 25], t, EHV, max=19, fill=[255, 255, 255], stroke=[[[20, 20, 40], 1]])]})
S.append({'src': 'kimoji', 'md5': '7f9b021c5b', 'ops': [C([0, 0, 32, 32]),
          T([2, 3, 28, 26], '기', EHV, max=22, fill=[150, 70, 40], stroke=[[[255, 240, 220], 2]])]})
S.append({'src': 'status02tamasii_', 'md5': 'e82dde7a63', 'ops': [
    {'op': 'key', 'box': [6, 20, 30, 26], 'match': [[[255, 255, 255], 120], [[0, 0, 0], 80], [[128, 128, 128], 60]], 'to': col('e82dde7a63', 50, 32, 2, 2)},
    T([7, 21, 28, 24], '혼', EHV, max=17, fill=[255, 255, 255], stroke=[[[106, 5, 4], 1]])]})
# main menu enter/move 64x64
S.append({'src': 'menu_main_in', 'md5': '085921b034', 'ops': [C([0, 32, 64, 32]),
          T([0, 34, 31, 16], '입장', G11, size=12, fill=[255, 255, 255], **PX()),
          T([32, 34, 31, 16], '이동', G11, size=12, fill=[255, 255, 255], **PX())]})
# name entry 256x216
h = '808a9cb70a'
S.append({'src': 'menu_name_area', 'md5': h, 'ops': [
    {'op': 'copy', 'box': [10, 10, 20, 14], 'from': [50, 10]}, T([10, 10, 30, 14], '성', G11, size=12, fill=[20, 20, 20], align='l', **PX()),
    {'op': 'copy', 'box': [98, 10, 18, 14], 'from': [140, 8]}, T([98, 10, 40, 14], '이름', G11, size=12, fill=[20, 20, 20], align='l', **PX()),
    {'op': 'copy', 'box': [10, 56, 44, 14], 'from': [80, 54]}, T([10, 56, 50, 14], '학교명', G11, size=12, fill=[20, 20, 20], align='l', **PX())]})
# ticket 256x128
h = 'ff7aa429c1'
S.append({'src': 'menu_route_tic', 'md5': h, 'ops': [
    {'op': 'copy', 'box': [156, 54, 24, 44], 'from': [126, 54]},
    T([154, 56, 28, 20], '엔', G11, size=16, fill=[10, 10, 10], **PX()),
    T([154, 78, 28, 20], '분', G11, size=16, fill=[10, 10, 10], **PX())]})
S.append({'src': 'menu_skills_star', 'md5': '0cea7da262', 'ops': [C([30, 0, 34, 32]),
          T([31, 6, 33, 20], '위력', G11, size=12, fill=[220, 255, 220], stroke=[[[40, 120, 40], 1]], **PX())]})
# phone status icons 256x64
ops = []
for x, t, fc in [(2, '호출OK', [40, 200, 255]), (50, '입원중', [230, 30, 30]), (96, '참전중', [240, 130, 20]), (144, '통화중', [60, 220, 60])]:
    ops += [C([x, 33, 46, 22]), T([x, 34, 46, 16], t, G11, size=12, fill=fc, stroke=[[[0, 0, 0], 1], [[255, 255, 255], 1]], **PX())]
S.append({'src': 'phone_callicon', 'md5': '5fb5e001f4', 'ops': ops})
# route legend 128x64
h = 'a90eaa4d98'
ops = []
for y, t in [(2, '전철'), (18, '버스'), (34, '택시')]:
    ops += [{'op': 'key', 'box': [8, y, 60, 14], 'match': [[[255, 255, 255], 100], [[0, 0, 0], 60], [[128, 128, 128], 70]],
             'to': col(h, 70, y + 5, 2, 2)[:3] + [255]},
            T([10, y, 30, 14], t, G11, size=12, fill=[255, 255, 255], stroke=[[[0, 0, 0], 1]], **PX())]
S.append({'src': 'route_color', 'md5': h, 'ops': ops})
# station names 64x288 (18 rows x 16)
names = ['교토역', '시청 앞', '기온', '야사카 신사', '신쿄고쿠', '니조성 앞', '니조성', '이케다 고교', '교토 교엔', '킨카쿠지 앞',
         '킨카쿠지', '키타노텐만구', '카미시치켄', '아라시야마 앞', '토게츠 다리', '지키시안', '니넨·산넨자카', '키요미즈데라']
ops = [C([0, 0, 64, 288])]
for i, n in enumerate(names):
    ops.append(T([0, i * 16 + 2, 64, 13], n, G9, size=10, fill=[20, 20, 20], **PX()))
S.append({'src': 'route_menu_tic_txit', 'md5': 'b8fa0233b3', 'ops': ops})
# sakusen 256x144 (white with red glow) and 128x72 (red)
cmds = ['때려눕혀!!!', '나한테 맡겨!!!', '고향에 돌아가!!!']
ops = [C([0, 0, 256, 144])]
for i, t in enumerate(cmds):
    ops.append(T([8, i * 48 + 6, 128, 36], t, EHV, max=22, fill=[255, 255, 255], stroke=[[[255, 40, 20], 2], [[150, 0, 0], 2]]))
S.append({'src': 'sakusen_panel01', 'md5': '00c384aa7b', 'ops': ops})
ops = [C([0, 0, 128, 72])]
for i, t in enumerate(cmds): ops.append(T([2, i * 24 + 1, 124, 22], t, EHV, max=17, fill=[240, 50, 70], stroke=[[[90, 0, 10], 1]]))
S.append({'src': 'sakusen_panel', 'md5': '12987b2c98', 'ops': ops})
h = '19c6621601'
S.append({'src': 'shiori_kenmei', 'md5': h, 'ops': [F([70, 5, 52, 22], col(h, 40, 14)),
          T([66, 6, 58, 20], '제패완료', G11, size=12, fill=[200, 255, 160], stroke=[[[60, 140, 40], 1]], **PX())]})
# shop signs 256x40
def tile(box, src_x, w):
    x, y, bw, bh = box; out = []
    while bw > 0:
        k = min(w, bw); out.append({'op': 'copy', 'box': [x, y, k, bh], 'from': [src_x, y]}); x += k; bw -= k
    return out


S.append({'src': 'shop_menu_board', 'md5': '494268230d', 'ops': [F([64, 8, 176, 17], col('494268230d', 180, 20)),
          T([64, 7, 176, 19], '시로쿠마트', EHV, max=17, fill=[30, 70, 170])]})
S.append({'src': 'shop_menu_board', 'md5': 'b01f91be60', 'ops': tile([60, 4, 140, 26], 0, 58) +
          [T([60, 5, 140, 22], '교토 기념품', EHV, max=18, fill=[30, 25, 20])]})
S.append({'src': 'shop_menu_board', 'md5': 'a9a52372c5', 'ops': [F([56, 6, 140, 22], col('a9a52372c5', 200, 8)),
          T([56, 6, 140, 22], '테일러 카구라', EHV, max=18, fill=[255, 255, 255])]})
S.append({'src': 'shop_menu_board', 'md5': 'e14618e98d', 'ops': tile([62, 6, 120, 22], 180, 34) +
          [T([60, 6, 124, 22], '바버 미야비', EHV, max=18, fill=[20, 20, 30])]})
# money panel 256x96
S.append({'src': 'shop_menu_money', 'md5': 'fb400a1751', 'ops': [
    F([18, 4, 66, 24], [0, 0, 0, 255]), T([18, 4, 66, 24], '소지금', EHV, max=16, fill=[0, 0, 0], stroke=[[[255, 255, 255], 1]]),
    F([8, 40, 86, 50], [0, 0, 0, 255]), T([8, 42, 86, 46], '포켓', EHV, max=30, fill=[0, 0, 0], stroke=[[[255, 255, 255], 2]])]})


# status windows 512x216
def status_ops(h, full=True):
    bg = col(h, 100, 60)
    W = dict(fill=[255, 255, 255]); O = dict(fill=[255, 160, 0])
    L = [([12, 128, 36, 18], '체력', O), ([12, 145, 40, 15], '스태미나', O), ([12, 160, 36, 18], '기합', O),
         ([128, 128, 54, 20], '사나이 그릇', O)]
    if full:
        L += [([236, 8, 36, 18], '체력', W), ([282, 10, 46, 38], '맷집', W), ([182, 30, 46, 18], '완력', W),
              ([190, 102, 50, 18], '폐활량', W), ([268, 102, 60, 18], '발 빠르기', W), ([184, 130, 56, 18], '찌질도', W)]
    ops = []
    for box, t, st in L:
        ops += [F(box, bg), T(box, t, DEB, max=14, align='l', **st)]
    return ops


h = '266e7dccf7'
ops = status_ops(h); bg = col(h, 100, 60)
for box, t in [([328, 14, 70, 24], '싸움 경험'), ([328, 56, 72, 26], '싸움혼'), ([328, 100, 64, 20], '플레이 시간'),
               ([328, 140, 66, 20], '쓰러뜨린 수'), ([446, 140, 18, 20], '명'), ([328, 174, 68, 26], '달성도'),
               ([12, 184, 46, 18], '소지금'), ([160, 184, 18, 18], '엔')]:
    ops += [F(box, bg), T(box, t, DEB, max=16, fill=[255, 255, 255], align='l')]
S.append({'src': 'status00_win00', 'md5': h, 'ops': ops})
for h, nm, full in [('952399cf29', 'status01_win00', True), ('5b51bfbe4e', 'sakusen_win', False)]:
    ops = status_ops(h, full); bg = col(h, 100, 60)
    ops += [F([12, 184, 36, 18], bg), T([12, 184, 46, 18], '작전', DEB, max=16, fill=[255, 255, 255], align='l')]
    S.append({'src': nm, 'md5': h, 'ops': ops})
# event item: school trip booklet 64x64 (vertical title)
h = '3320ea82bf'
S.append({'src': 'evit_000', 'md5': h, 'ops': [F([6, 14, 18, 48], col(h, 26, 20)),
          T([5, 14, 20, 48], '수학여행', G9, size=10, vertical=True, fill=[20, 10, 10], **PX())]})

# BOOT.BIN .data TIM2 (LZS) 256x32: 番長用語辞典
BOOT_TEX = {0x2906e4: [C([0, 0, 256, 32]), T([2, 1, 190, 30], '짱 용어 사전', EHV, max=24, fill=[10, 10, 10],
                                              stroke=[[[255, 255, 255], 1], [[220, 20, 20], 2]])]}

if __name__ == '__main__':
    json.dump(S, open(f'{ROOT}/trans/images2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(S))
