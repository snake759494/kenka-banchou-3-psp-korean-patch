# 빌드 방법

번역 대본·원문은 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 ISO `Kenka Banchou 3 - Zenkoku Seiha (Japan, Asia).iso` (MD5 `00037a2c6b682b6189d0c23062e13930`)
- Python 3.12+ : `pip install pillow numpy scipy opencv-python websocket-client`
- 글꼴: `SeoulHangangEB/B/M/L.ttf`, `NanumSquareNeo-*.ttf` (작업 폴더), `Galmuri*.ttf` (`work/fonts/`)

## 폴더 구성
```
<작업 폴더>/
  Kenka Banchou 3 - Zenkoku Seiha (Japan, Asia).iso
  *.ttf
  tools/        (이 저장소의 tools)
  trans/        out/*.json, jobs2/*.json, images.json, images2.json  (번역 — 저장소 미포함)
  work/iso/     ISO를 풀어 둔 폴더
  work/         DTEventMes.bin, DYTankaMes.bin, common.bin, eboot_str.json, tbl_str.json, texsrc/ ...
```

## 순서
1. ISO 풀기: `python tools/extract_iso.py` → `work/iso/`
2. 원문 추출
   - 메시지: `python tools/extract.py` → `work/DTEventMes.bin`, `work/DYTankaMes.bin`
   - 실행 파일 SJIS 문자열: `python tools/eboot_scan.py` → `work/eboot_str.json`
   - 표 인코딩 문자열: `python tools/tbl_extract.py` → `work/tbl_str.json`
   - 이벤트 스크립트: `python tools/bpack_text.py` → `work/bpack_str.json`
   - 텍스처: `python tools/tex_dump.py work/tex` → `work/texsrc/*.tm2`
3. 번역 작성
   - `trans/out/*.json` = `[{"jp": 원문, "kr": 번역}]` (실행 파일 문자열은 `"off"` 포함)
   - `trans/jobs2/x_*.json`, `y_*.json` = 표 문자열·이벤트 스크립트 `[{"jp", "kr"}]`, `m_*.json` = 메시지 보충, `e_*.json` = 추가 SJIS `[{"off", "cap", "jp", "kr"}]`, `u_*.json` = UTF-8 문자열
   - 그림 글자: `python tools/images2_spec.py` → `trans/images2.json` (`trans/images.json`은 직접 작성)
4. 빌드: `python tools/build.py` → `싸움대장3_전국제패_한글.iso`
5. 차분: `xdelta3 -e -0 -s 원본.iso 한글.iso 패치.xdelta`

PPSSPP 원격 디버거로 자동 확인할 때는 `python tools/emu.py start <ISO>` / `shot` / `press` / `seq` 를 씁니다.
