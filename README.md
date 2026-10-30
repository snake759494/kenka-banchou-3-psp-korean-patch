# 싸움대장3 ～전국제패～ (PSP) 비공식 한글패치

PSP 일본판 **喧嘩番長3 ～全国制覇～ (켄카 반쵸 3 전국제패, ULJS-00166)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.iso`** 를 준비합니다. (CSO·CHD 등으로 변환한 이미지에는 적용할 수 없습니다.)
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\Kenka Banchou 3 - Zenkoku Seiha (Japan, Asia).iso'`
2. xdeltaUI 같은 도구로 원본 `.iso` 에 `KenkaBanchou3_Zenkoku_Seiha_KO_v1.0.xdelta` 를 적용합니다. (Patch = xdelta, Source File = 원본 ISO, Output File = 새 파일명)
   - 명령줄: `xdelta3 -d -s "Kenka Banchou 3 - Zenkoku Seiha (Japan, Asia).iso" KenkaBanchou3_Zenkoku_Seiha_KO_v1.0.xdelta "Kenka Banchou 3 - Zenkoku Seiha (Korean).iso"`
3. 만들어진 ISO를 PPSSPP 또는 커스텀 펌웨어(PSP·PS Vita Adrenaline 등)에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ISO 크기 | 521,109,504 바이트 |
| 원본 ISO MD5 | `00037a2c6b682b6189d0c23062e13930` |
| 원본 ISO SHA-256 | `fc7c0a4b5acee97a56aaae9edcfd3c39cc32e5ef929b526cfd7f380da541b646` |
| xdelta SHA-256 | `47800417384da2d36685572b9414b0a227bca18968e2833224118882839ed6bd` |
| 결과 ISO 크기 | 556,398,592 바이트 |
| 결과 ISO SHA-256 | `25ac41a5514fc42bbe7cc34f8392d16921a8871e235a0ced88b6ccd801a51850` |

## 주의
- 복호화한 실행 파일(BOOT.BIN)을 EBOOT로 넣었기 때문에 **PPSSPP·커스텀 펌웨어 전용**입니다. 정품 펌웨어에서는 부팅되지 않습니다.
- 원본이나 다른 버전 패치에서 만든 **상태저장(세이브 스테이트)** 은 불러오지 마세요. 일반 세이브는 그대로 쓸 수 있습니다.
- xdelta는 압축하지 않은 형식(`-0`)이라 크기가 큽니다(약 200MB).

## 한글화 내용
- 이벤트 대사 3,600개, 단카(啖呵) 메시지 791개 전체 직접 번역
- 실행 파일 문자열 4,454개 — 메뉴, 도움말, 아이템·의상·기술 설명, 단카 문구, 상점·전화·여행 일기, 시스템 메시지
- 실행 파일 안의 표 인코딩 문자열 792개 — 짱 용어 사전, 상점 점원 대사, 아이템·의상·헤어 이름, 인물 이름
- 실행 파일에 내장된 이벤트 스크립트 문자열 474개 — 튜토리얼 안내, 아이템·전화번호 입수 알림
- 세이브 데이터 정보·통신 오류 문구
- 그림 글자 약 150장 — 타이틀 로고(싸움대장 / 전국제패), 메뉴 패널, 단카 안내, HUD, 스테이터스, 여행 일기, 상점 간판, 전화 아이콘, 역 이름, 커맨드 패널, 짱 용어 사전 제목, XMB·세이브 아이콘
- 이름 입력(학생수첩) 한글 입력, 단카 전용 글꼴 한글화
- 글꼴: 본문 서울한강체, 그림 글자 나눔스퀘어네오, 아주 작은 글자 갈무리

## 그대로 둔 것
- 음성, 3D 배경 속 간판 등 맵 텍스처, 개발용 디버그 문자열

## 검증 범위
PPSSPP에서 타이틀, 오프닝 이벤트, 메뉴, 대화, 단카 배틀, 상점 등을 확인했습니다. 실행 파일·메시지·스크립트의 문자열과 UI 텍스처를 전수 검사해 화면에 나오는 일본어가 남지 않은 것을 확인했습니다. 전체 플레이 검증은 하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
