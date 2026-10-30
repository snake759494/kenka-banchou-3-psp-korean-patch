# 기술 문서

## 디스크 구성
- `PSP_GAME/SYSDIR/BOOT.BIN`: 암호화되지 않은 실행 파일(PRX, 재배치 포함). 패치는 이것을 고쳐 `EBOOT.BIN`·`BOOT.BIN` 양쪽에 넣습니다(그래서 커스텀 펌웨어·PPSSPP 전용).
- `PSP_GAME/USRDIR/**/*.lzs`: LZS 압축 아카이브. 메시지 파일(`DTEventMes.bin`, `DYTankaMes.bin`)과 UI 텍스처(TIM2)가 들어 있습니다.
- LZS: u32 원래 크기 + Okumura LZSS(N=4096, F=18, THRESHOLD=2, 링 초기값 0, r=0xFEE, 플래그 LSB부터, 1=리터럴). 크기가 빠듯한 곳은 최적 파싱(`lzs.compress_opt`)으로 원래 자리에 들어가게 합니다.
- 아카이브(`arc.py`): u16 개수, u16, 개수×0x40 항목(u32 오프셋, u32 크기, u32 번호, 이름[0x30], u32), 데이터 0x20 정렬.

## 문자 코드
- 게임 글자는 BOOT.BIN 0x16C704의 문자표(SJIS 문자열, 3,572자) 번호로 저장됩니다. 번호 i < 0xDF → 바이트 i+1, 그 외 → `0xE0|((i−0xDF)>>8)`, `(i−0xDF)&0xFF`. 0xEF 이상은 제어 코드(0xFE 줄바꿈 등).
- 2바이트 코드의 둘째 바이트가 0x00일 수 있으므로 문자열 끝은 코드 단위로 찾아야 합니다(`kbtext.strend`).
- 글꼴 텍스처 `kenka_font_jis00/01.tm2`: 번호 i → 텍스처 i//2048, 2비트 평면 (i//1024)%2, 16×16 칸 i%1024.
- 한글 배치(`kfont.py`): 번역에 쓰인 한글과 KS X 1001 완성형(총 2,393자)을 가나·한자 슬롯에 그립니다. 실행 파일의 SJIS 문자열에서는 한글을 그 슬롯의 원래 SJIS 글자로 바꿔 씁니다(`kfont.sjis_encode`).

## 텍스트 위치
| 종류 | 위치 | 처리 |
| --- | --- | --- |
| 이벤트 대사·단카 메시지 | `DTEventMes.bin`, `DYTankaMes.bin` (u32 오프셋 표 + 문자표 인코딩) | 다시 만들어 아카이브 재압축 |
| 실행 파일 SJIS 문자열 | BOOT.BIN .rodata/.data | 들어가면 제자리, 길면 빈 영역에 두고 모든 참조(R_MIPS_32, HI16/LO16)를 고침(`ebpatch.py`) |
| 표 인코딩 문자열(용어 사전·상점·아이템·인물) | BOOT.BIN 0x1763BC~0x1E05B0 사이 몇 구간 | 위와 같음 |
| 이벤트 스크립트 | BOOT.BIN .data 0x22D464 내장 팩(0x13D 항목, LZS) | 명령 `[op][size][00 00]문자열\0` 안에서 같은 길이로 교체(공백 채움, CRLF 줄바꿈 유지) |
| 세이브 정보·통신 오류 | BOOT.BIN 0x16C2CC~ UTF-8 | 같은 자리 안에서 교체 |
| 단카 글꼴 | BOOT.BIN 0x1B9767 SJIS 글자 목록 + `kenka_font_tanka00.tm2` | 빈 칸에 한글 배치(`tanka.py`) |
| 이름 입력 | BOOT.BIN 0x2A7314 행 포인터 표 | 한글 입력표로 교체(`nameentry.py`) |

## 그림 글자
- `images.py`가 `trans/images.json`, `trans/images2.json`의 사양(지우기·채우기·색 바꾸기·글자 그리기)대로 TIM2를 고치고 원래 팔레트로 다시 양자화합니다.
- BOOT.BIN .data 0x2906E4의 LZS TIM2(짱 용어 사전 제목)는 제자리에서 재압축합니다.
- XMB·세이브 아이콘(`ICON0.PNG` 3종)은 원래 로고를 인페인팅으로 지우고 한글 로고를 그립니다(`icons.py`).

## 검증
- 원본 BOOT.BIN의 재배치 참조 대상 전체를 SJIS·UTF-8·문자표로 해독해, 번역되지 않은 일본어 문자열이 남았는지 검사했습니다.
- USRDIR의 모든 압축·아카이브를 풀어 일본어 텍스트가 없는지, 패치하지 않은 UI 텍스처 353장에 일본어 글자가 없는지 확인했습니다.
