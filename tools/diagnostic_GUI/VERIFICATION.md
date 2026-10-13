# HINT-48 Phase 3C 검증 — 2026-10-12 (Asia/Seoul)

이번 절은 Phase 3C의 실제 실행 결과입니다. 아래 기존 Phase 1~3B 기록은 보존했으며,
과거 절의 "미구현/기준 HEAD"는 당시 상태입니다. 테스트 통과는 담당자 리뷰나
Production Interface 승인, Hardware 검증을 의미하지 않습니다.

- 시작/종료 Branch: `PC-Diagnostic-Test`.
- 기준 HEAD: `69f904c7d74cf6238a37be7f2c4e02321962deb6`. 시작 Working Tree clean.
- 작업 시작 시 D: AGENTS.md, 팀 CONTRIBUTING/README, 핸드북 §11 (p29–30),
  실제 Loader/Codec/DecodeService/Cache 및 GUI 소스/테스트 계약을 확인했습니다.
- 실제 팀 DBC `network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc`의 VERSION은
  `0.4 - review-ready interface proposal`입니다. 승인된 Production 기본값으로
  등록하지 않았으며 GUI 자동 로드/실제 Bus 검증에 사용하지 않았습니다.
- Phase 2 DbcLoader 계약: 재로드 시 새 Cache, 실패 시 기존 lookup 제거.
  따라서 Worker/잔여 처리 종료 후 새 서비스 세션을 구성합니다.
- 실제 설치 환경: Python **3.14.6**, PySide6 **6.10.3**, python-can **4.6.1**,
  cantools **44.2.1**, pytest **9.1.1**. 패키지 재설치/버전 변경 없음.
  팀 승인 고정 버전 **미확정**, 다른 Python/OS/라이브러리 조합 **NOT VERIFIED**.

| 검증 | 실제 결과 / 제한 |
| --- | --- |
| 수정 전 전체 기준선 | **170 passed in 3.20s** |
| 기존 170개 테스트 소스 | 삭제/수정/약화 없음; 최종 전체 실행에 포함 |
| 최종 전체 pytest | **201 passed in 5.79s** — 기존 170 + 신규 31 |
| 신규 테스트 | GUI Mock 통합 26 + Qt 독립 DecodeSession 5 |
| CLI 기존 140개 | 전체 실행에서 모두 PASS; monitor/log/send/decode/encode 및 JSONL/CSV/Codec/Cache 회귀 보존 |
| CLI 진입점 | `python -m pc_diagnostic --help`, 설치된 `can-diag.exe --help` 성공 |
| GUI 진입점 | `python -m pc_diagnostic.gui --help`, 설치된 `can-diag-gui.exe --help` 성공; 실제 실행 창 노출 |
| 선택 의존성 | Qt/cantools 차단 모의에서도 Raw CLI/빈 DecodeSession 동작; cantools 부재 로드 실패 안내 |
| DBC 선택 | offscreen 파일 선택 버튼 및 취소 테스트 PASS; 사용자 직접 실제 파일 선택 **정상 확인** |
| DBC 미선택/로드 실패 | Mock Raw 수신 유지; missing/malformed 후 정상 파일 재시도 PASS |
| Decode | 기존 TEST ONLY fixture에서 STD/EXT 이름/값/Unit 및 Raw 참조 보존 PASS |
| Signal Cache | Channel/Message 분리, 반복 RX 갱신, TX 비갱신, 실패 시 값/원래 RX 시각 보존 PASS |
| Age | 원래 Timestamp 기준, 미제공/역행 unknown, 정지 중 타이머 갱신 PASS; Health 판정 없음 |
| 재로드 | 새 Cache 구성; 과거 Raw 해석/Unit 보존, 과거 세션과 현재 Cache 혼합 방지 PASS |
| 오류/동시 요청 | Unknown/length/decode/application 오류, Running/Stopping/잔여 버퍼 교체 차단, dialog 재진입/close 후 요청 차단 PASS |
| 유한 처리 | 2000 입력 → 1488 버퍼 제외 / 512 처리 / 500 Raw 이력; 제외 프레임 Decode 안 함 |
| 기존 Windows Raw native smoke | 실제 windows 플랫폼 창 노출, 3회 반복, Clear, active close; Mock 4개 해제·송신 없음 |
| Windows Decode native smoke | 실제 windows 플랫폼 창 노출, 명시적 TEST ONLY 파일 load API, DBC 없는 Raw, Decode/Cache, 3회 반복, 길이 실패 보존, active close; Mock 5개 해제·송신 없음 |
| 사용자 Windows 수동 확인 | 사용자가 직접 Select DBC → test_only.dbc → Start/STD 행 선택 → Measurement=-10.0 / test_unit / Cache / Age / Stop/Clear **정상 확인** 응답 |
| pip check | **No broken requirements found.** |
| 실제 CANable/ECU/Production Decode 정확도 | **NOT VERIFIED** |
| 실제 담당자 코드 리뷰 | **NOT VERIFIED** |
| Interface | 공통 CAN/LIN DBC/Matrix/ECU/Phase 1~2 Public Interface 변경 없음 |
| Git 업로드 | add/Commit/Push/PR/Merge 미실행; 이력 재작성 없음 |

자동 native smoke의 `human_manual_file_dialog=NOT VERIFIED` 출력은 자동화가 사람의
직접 파일 선택을 검증하지 않는다는 뜻입니다. 이후 사용자 응답은 위 별도 행에 기록했습니다.
Qt widget 렌더 `.test-tmp/phase3c-native-final.png`를 시각 확인했습니다.
Windows 화면 배율에서도 초기 창이 가용 화면에 들어오도록 크기를 제한했습니다.
OS 전체 캡처 또는 Hardware evidence가 아닙니다. 생성 Temp/렌더/캐시/가상환경은 Git 제외입니다.

### 실행 및 재현

패키지 폴더에서 실행했으며 pytest basetemp는 매 실행 새로운 테스트 전용 GUID 경로,
`-p no:cacheprovider`를 사용했습니다. 사용자 데이터 경로를 정리하지 않았습니다.

```powershell
New-Item -ItemType Directory -Force .test-tmp | Out-Null
$phase3c_temp = '.test-tmp/phase3c-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $phase3c_temp
.\.venv\Scripts\python.exe tests/gui_native_smoke.py --screenshot .test-tmp/raw-native.png
.\.venv\Scripts\python.exe tests/gui_decode_native_smoke.py --dbc tests/fixtures/test_only.dbc --screenshot .test-tmp/phase3c-native.png
.\.venv\Scripts\python.exe -m pip check
```

### Trouble Shooting / Jira 등록용 초안 — 외부 등록 미실행

**HINT-48 / 예상 밖 DecodeService 오류에서 최신 Cache 상태 표시 누락**
- 재현: 정상 TEST ONLY RX 후 `DecodeService.process`에 RuntimeError를 주입하고
  같은 Channel/Message 프레임을 수신. 최신 오류 조회 guard가 decoded=None을 제외하여
  정상 Cache 옆 최신 상태가 오류 대신 unavailable로 표시됨.
- 최초 통합 실행: **199 PASS / 1 FAIL**. 신규 assertion이 이 표시 결함을 검출함.
- 원인: 실패 관찰의 DBC Message 메타데이터가 있어도 decoded 결과가 없는 경로를 배제함.
- 수정: 기존 Loader의 Message 메타데이터를 기준으로 최신 시도를 조회하고
  application 오류와 codec invalid를 구분 표시. 성공 Cache 값/시각은 변경하지 않음.
- 최종: 해당 회귀 및 최종 전체 **201 PASS**. 담당자 리뷰는 **NOT VERIFIED**.
- 영향 범위: GUI 표시만. CAN/LIN 정의/공통 Public Interface/DBC 파일 변경 없음.


**HINT-48 / Error 프레임 mask의 DBC Message 오표시**
- 재현: 기존 TEST ONLY ID와 숫자가 같은 Error 프레임을 입력하면 Codec은 invalid를
  반환하지만 GUI 메타데이터 조회가 일반 DBC Message 이름/Cache를 연결함.
- 검출: 신규 Error mask 테스트가 수정 전 **1 FAIL**을 반환함.
- 원인: GUI 보조 조회가 is_error_frame 속성을 구분하지 않음.
- 수정: 기존 RawCanFrame 계약에 따라 Error ID를 Message lookup에 사용하지 않음.
  Raw ERROR 표시와 기존 invalid 결과는 유지하고 정상 RX Cache는 보존함.
- 최종 전체 **201 PASS**. CAN ID/Signal/DBC 파일은 변경하지 않음.

**HINT-48 / 팀 버전 및 운영 Cache 정책 확인 요청**
- 팀 Python/PySide6/python-can/cantools/pytest 고정 버전/lock 승인 기준 확인 필요.
- 기존 DBC session 재로드 계약은 적용했으나 Cache 영속화, 실제 backend 재연결,
  timestamp clock 동기화, 운영용 reset 정책은 Open/후속 범위.
- 현재 Clear/Start/Stop은 같은 DEMO DBC session을 유지함. 이를 차량 ECU 정책으로 확정하지 않음.
- Production DBC/Matrix 일치와 공식 Interface 승인에는 **상대 담당자 리뷰 필요**.
- Jira Issue/팀 메시지 등록이나 Jira Done 변경은 수행하지 않음.

### 변경 및 보존 범위

- 수정: `README.md`, `VERIFICATION.md`,
  `src/pc_diagnostic/gui/buffer.py`, `src/pc_diagnostic/gui/window.py`.
- 신규: `src/pc_diagnostic/gui/decode_session.py`,
  `tests/test_gui_decode.py`, `tests/test_gui_decode_session.py`,
  `tests/gui_decode_native_smoke.py`.
- `pyproject.toml`/기존 GUI app/receiver/demo 및 기존 테스트는 변경하지 않음.
- D: 원본 25개와 다른 worktree/미추적 리뷰 문서는 시작 SHA-256 기준으로 보존 검증.
  기존 리뷰 SHA-256: `751ecd803fc1866cc12a51ba2df4a93a64bd41f2cc441456eb9ea49b3178b975`.
- GUI 조합 계층은 기존 RawCanFrame/DecodedMessage를 참조하는 관찰 묶음만 추가했으며
  CAN Frame 모델/신호 변환을 중복 구현하지 않음.
- 미구현/미검증: 실제 CAN GUI 연결·송신, Production Interface 정합성, Logging/Export,
  수신 중 DBC 교체, Health/Fault, Fault Injection, standalone 배포, Hardware 시험.

향후 Commit 후보(실행하지 않음):
`[feat][YYYYMMDD][권도형] add DBC decode and signal cache GUI`.
날짜는 실제 Commit일을 사용합니다.

---

# PC Diagnostic 검증 기록

## HINT-48 Phase 3B — P2/P3 수정 (2026-10-12, Asia/Seoul)

판정: **PASS — 재현된 P2/P3 수정 및 요청된 소프트웨어 검증 완료**.
실제 팀 담당자 코드 리뷰 완료 또는 팀 고정 버전 승인을 뜻하지 않습니다.
아래 기존 Phase 3B/Phase 1/2 기록은 각각 당시 결과로 보존했습니다.

### 최소 변경 및 결함 검출

- 수정: `src/pc_diagnostic/gui/app.py`, `tests/test_gui.py`, README, VERIFICATION.
- 신규: `tests/test_gui_app.py` (Qt 설치 없이 실행 가능한 오류 안내 테스트 7개).
- 기존 미커밋 GUI 13개를 초기화/삭제하지 않았습니다. 기존 변경 13개 중 위 4개만
  이번 작업에서 변경했고 나머지 9개는 해시 동일. 최종 Git 후보는 14개 (신규 11 / 수정 3).
- P2: 콘솔은 고정된 PySide6 원인/설치 안내를 stderr로 출력합니다. 콘솔 부재 또는
  출력 실패 시 Qt를 import하지 않는 Windows MessageBoxW 함수로 안내합니다.
  ctypes 인수/반환 타입을 명시하고 API 반환 0은 실패로 처리합니다.
  안내 자체 실패는 False를 반환하고 main은 재시도 없이 종료 코드 1로 끝납니다.
  원래 ImportError 원문/내부 경로는 사용자 메시지에 넣지 않습니다.
- P2 검출 근거: production 수정 전 새 7개 테스트가 모두 실패했고, 콘솔 없는 경로의
  Windows 안내 호출 누락을 검출했습니다. 수정 후 7개 및 보완 반복 테스트 합계 8개 통과.
- P3: 각 Start 전 수신 수를 기록하고 새 수신 수 증가를 기다립니다. 매회 새 Mock 생성,
  shutdown 1회, 송신 없음 및 종료 thread 정리를 검증합니다. 이전 표시 행은 유지합니다.
- P3 검출 근거: 이전 리뷰에서는 3회 반복 테스트가 Mock 생성 1회로 PASS했습니다.
  보완 후 두 번째 실행의 recv를 무수신으로 메모리에서만 바꾸자 기존 행이 있어도
  `Qt condition timed out`으로 예상대로 실패했습니다. 주입은 process 종료 전 복원했습니다.
  실제 기능/테스트 소스를 결함 주입 상태로 저장하지 않았습니다.
- timeout 테스트의 1ms 설정은 close 거부/Error 검증까지만 적용하고, release 전에 원래
  정리 대기값으로 복원합니다. 초기 전체 실행의 169 PASS / 1 FAIL은 이 설정이 worker_finished
  정리까지 제한한 결과입니다. close timeout assertion은 유지하며 테스트를 삭제/약화하지 않았습니다.
- 기존 GUI/통신 모델/worker/buffer/Public Interface, CLI 소스 및 Phase 1/2 테스트는 변경 없음.

### 실제 재검증 결과

| 검증 | 결과 |
| --- | --- |
| P2 새 테스트 + P3 반복 테스트 | **8 passed in 0.55s** |
| GUI/버퍼/안내 테스트 최종 | **30 passed in 2.43s** (기존 23 + 신규 7) |
| 기존 CLI/Phase 1~2 별도 회귀 | **140 passed in 0.74s**, 기존 Phase 1 63개 포함 |
| 전체 pytest 최종 | **170 passed in 2.85s** |
| P3 무수신 결함 검출 | PASS, 두 번째 Mock 생성 후 신규 수신 0/이전 행 존재 상태에서 예상 실패 |
| 실제 Windows Native Smoke | PASS, Start/Stop 3회, Clear 전 12개 수신, active close, Mock 4개 해제/송신 없음 |
| 실제 정상 GUI main 진입점 | PASS, Windows 플랫폼, Mock 3개 수신 후 정상 종료 코드 0 |
| 실제 콘솔 없는 pythonw 오류창 | PASS, Qt import만 process 내 모의 실패, stdout/stderr=None 확인 |
| 오류창 사람 수동 확인 | PASS, 사용자 답변 “원인·설치 안내 확인 후 OK 클릭” |
| 오류창 닫힌 뒤 결과 | 종료 코드 1, native_notice_returned=true |
| CLI 설치 진입점 | PASS, --help / monitor / log(JSONL·CSV) / send(Mock) / decode / encode |
| GUI 모듈 --help 및 CLI 병행 | PASS |
| pip check | No broken requirements found |
| 실제 CANable/ECU/물리 CAN/LIN | **NOT VERIFIED — 수행하지 않음** |
| 팀 담당자 코드 리뷰 | **NOT VERIFIED** |

GUI 자동 테스트는 Qt offscreen과 기존 Mock을 사용합니다. 실제 Windows 창은 native
smoke 및 정상 main 진입점에서 별도 검증했고 오류창은 사람 확인을 받았습니다.
오류창 검증에서도 설치된 PySide6를 삭제하지 않았고 `.venv`를 손상시키지 않았습니다.

패키지 폴더에서 pytest cache를 비활성화하고 새 GUID basetemp를 사용했습니다:

```powershell
$fix_test_root = '.test-tmp/p2p3-' + [guid]::NewGuid().ToString('N')
New-Item -ItemType Directory -Path $fix_test_root | Out-Null
.\.venv\Scripts\python.exe -m pytest tests/test_gui_app.py tests/test_gui.py::test_start_stop_repeat_and_no_duplicate_worker -q -p no:cacheprovider --basetemp ($fix_test_root + '/targeted')
.\.venv\Scripts\python.exe -m pytest tests/test_gui.py tests/test_gui_buffer.py tests/test_gui_app.py -q -p no:cacheprovider --basetemp ($fix_test_root + '/gui')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --ignore tests/test_gui.py --ignore tests/test_gui_buffer.py --ignore tests/test_gui_app.py --basetemp ($fix_test_root + '/cli')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp ($fix_test_root + '/all')
.\.venv\Scripts\python.exe tests/gui_native_smoke.py --screenshot ($fix_test_root + '/native.png')
.\.venv\Scripts\python.exe -m pc_diagnostic.gui --help
.\.venv\Scripts\can-diag.exe --help
.\.venv\Scripts\python.exe -m pip check
```

### 환경 및 협업 상태

- Python 3.14.6 / PySide6 6.10.3 / python-can 4.6.1 / cantools 44.2.1 / pytest 9.1.1 그대로 유지.
  패키지 재설치/버전 변경 및 pyproject 변경 없음.
- 팀 고정 라이브러리 버전은 여전히 **미확정 / 검토 필요**. 현재 버전을 승인된 값으로 주장하지 않습니다.
- Windows API 근거: [MessageBoxW 공식 문서](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messageboxw).
- snake_case, 함수 책임 분리, 플랫폼 함수 분리 및 주요 흐름 한국어 주석 적용.
- 공식 CAN/LIN DBC/Matrix/Signal/Enum/Timeout/ECU 제어 변경 없음. 향후 변경은 상대 담당자 리뷰 필요.
- Branch/HEAD 유지: `PC-Diagnostic-Test` / `cde2ebfb511696c058b97b0d998d9d420ccdbf31`.
- D: 원본 25개 및 다른 worktree의 기존 리뷰 문서를 보존합니다. 리뷰 문서 SHA-256:
  `751ecd803fc1866cc12a51ba2df4a93a64bd41f2cc441456eb9ea49b3178b975`.
- Git add/Commit/Push/PR/Merge/Reset/Rebase/Force Push 및 이력 재작성 미실행.
- 후속 Commit 후보: `[feat][YYYYMMDD][권도형] add PySide6 GUI and mock CAN monitor`.
  날짜는 실제 Commit일로 작성해야 하며 Commit/Push 승인은 별도로 필요합니다.

Jira 기록용 후속 내용 (외부 등록 미실행): P2 native 의존성 안내 및 P3 새 수신 검증 수정,
위 재현/최종 결과로 검증 완료. 추가 Trouble Shooting: close timeout 테스트의 1ms 설정이
native thread 정리 단계까지 전파되던 문제를 검증 구간에만 제한했습니다. 팀 버전 합의와
담당자 코드 리뷰는 여전히 미완료입니다.

---

## HINT-48 Phase 3B — PySide6 Mock GUI (2026-10-12, Asia/Seoul)

판정: **PASS — Windows Mock GUI MVP 구현/검증 완료 후보**.
팀 고정 버전 합의와 담당자 코드 리뷰 완료를 의미하지 않습니다.
이 절 아래 Phase 1/2 내용은 원본 개발 환경의 과거 검증 기록으로 보존했습니다.

### 기준 및 보호 확인

- Worktree: `C:/CAN_LIN_Gateway/pc-diagnostic-test-worktree`.
- Branch: `PC-Diagnostic-Test`; 시작/최종 HEAD: `cde2ebfb511696c058b97b0d998d9d420ccdbf31`.
- 작업 시작 tracked 파일 370개, working tree clean 확인.
- AGENTS.md와 팀 README/CONTRIBUTING, 핸드북 §11 (PDF 29~30쪽) 확인.
  핸드북의 GUI/진단 로직 분리 및 smoke/manual evidence 원칙을 적용했습니다.
  통신 Interface 변경이 없어 Matrix/DBC의 새로운 정의를 조사/확정하지 않았습니다.
- 기존 Phase 1/2 Python 소스 13개, 테스트 8개 및 TEST ONLY DBC는 Git 기준 변경 없음.
- D: 원본 업로드 대상 25개 SHA-256은 이전 보존 기준과 모두 동일합니다.
- 다른 worktree 리뷰 문서는 미추적 상태 그대로 보존했습니다.
  SHA-256: `751ecd803fc1866cc12a51ba2df4a93a64bd41f2cc441456eb9ea49b3178b975`.
- 공통 CAN/LIN DBC/Matrix/Excel/ECU 소스/팀 설정 변경 없음.
- Git add/Commit/Push/PR/Merge/Reset/Rebase/Force Push: **미실행**. staged 항목 없음.

### 실행 환경 및 결과

Windows / Python **3.14.6**, PySide6 **6.10.3**, python-can **4.6.1**,
cantools **44.2.1**, pytest **9.1.1**. 독립 worktree `.venv`에 GUI extra를 editable 설치했습니다.
기존 Python >=3.10 및 기존 can/dbc/test 의존성 범위를 변경하지 않았습니다.

| 검증 | 실제 결과 / 근거 |
| --- | --- |
| editable GUI 설치 및 import | PASS, can-diag-gui.exe 생성 및 실제 창 실행 |
| pip check | PASS, No broken requirements found |
| 전체 pytest | **163 passed in 2.93s**: 기존 140 + 신규 GUI/버퍼 23 |
| 기존 Phase 1/2 별도 회귀 | **140 passed in 0.54s**; 기존 Phase 1 63개 포함 |
| Qt offscreen GUI 테스트 | PASS, 신규 Qt 13개 + Qt 독립 버퍼/데모 10개 |
| GUI module --help | PASS; PySide6 미설치 모의 상황 안내/CLI import 유지 포함 |
| 기존 설치된 CLI | PASS, --help / monitor / log(JSONL·CSV) / send(Mock) / decode / encode |
| GUI 수신 중 별도 CLI monitor | PASS, Mock backend로 실행 |
| native Windows 창 | PASS, `QApplication.platformName() == windows`, 창 exposed/visible 확인 |
| native Start/Stop | PASS, 3회 반복; Clear 전 수신 13개 |
| native Clear 및 재시작 | PASS, 행/계수 0 초기화 후 다시 수신 |
| native 활성 worker 종료 | PASS, Mock transport 4개 모두 해제, sent_frames 모두 비어 있음 |
| 사람의 수동 확인 | PASS, 사용자 답변: “창과 Start/Stop/Clear 정상 확인” |
| 실제 CANable/ECU/물리 CAN/LIN | **NOT VERIFIED — 수행하지 않음** |
| 담당자 코드 리뷰 / 팀 버전 승인 | **NOT VERIFIED / 검토 필요** |

GUI 자동 테스트 범위: 중복 Start, 반복 Stop/Start, Clear 중 수신 계속, Raw 표/계수,
STD/EXT/RTR/ERROR 및 누락 metadata, 즉시 Stop, close 시 해제, transport 생성/수신/해제
예외와 Error 복구, close timeout 시 창/worker 보존, 유한 버퍼/행 제한과 제외 수,
CLI 병행 실행 및 선택적 Qt 의존성 부재 안내.
Mock/VirtualBus 성공을 Hardware PASS나 ECU 응답으로 해석하지 않습니다.

실행 명령 (패키지 폴더 기준, basetemp는 매 실행 새 GUID 경로):

```powershell
.\.venv\Scripts\python.exe -m pip install 'PySide6==6.10.3'
.\.venv\Scripts\python.exe -m pip install -e '.[gui,test]'
New-Item -ItemType Directory -Force .test-tmp | Out-Null
$phase3_test_temp = '.test-tmp/phase3b-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $phase3_test_temp
# Qt offscreen과 별도의 실제 Windows 창 smoke
.\.venv\Scripts\python.exe tests/gui_native_smoke.py --screenshot .test-tmp/phase3b-native.png
.\.venv\Scripts\can-diag-gui.exe
```

Native 자동 smoke는 창을 실제로 열고 QtTest로 버튼을 조작합니다. Qt widget 렌더
`.test-tmp/phase3b-native.png`를 시각 확인했습니다. 이는 Qt 자체 렌더이며 OS 전체
스크린샷/Hardware 캡처가 아닙니다. 사람이 직접 수행한 버튼 검증은 별도로 위 표에 기록했습니다.
가상환경/캐시/egg-info/Temp/이 렌더 증거는 기존 .gitignore에 의해 제외됩니다.

### 구현 및 변경 범위

- 신규 GUI: `src/pc_diagnostic/gui/{__init__,__main__,app,buffer,demo,receiver,window}.py`.
- 신규 테스트: `tests/test_gui.py`, `tests/test_gui_buffer.py`, `tests/gui_native_smoke.py`.
- 수정: `pyproject.toml`, `README.md`, `VERIFICATION.md`. 삭제 없음.
- GUI optional dependency: `PySide6>=6.10,<7`; 독립 `[project.gui-scripts] can-diag-gui`.
  기존 `can-diag` 진입점과 CLI 소스/기존 테스트는 변경하지 않았습니다.
- 기존 TEST ONLY fixture 예제 ID/바이트만 재사용, 공식 CAN ID/Signal/Enum 신규 정의 없음.
  GUI는 DBC를 로드하거나 실제 ECU 제어/송신을 수행하지 않습니다.
- 기존 RawCanFrame 및 MockCanInterface 계약 재사용. UI와 worker/유한 버퍼 책임 분리.
  GUI 갱신/취소 상수는 CAN/LIN 타이밍이나 Fault 정책과 무관합니다.
- Thread lifecycle 근거: [Qt QThread](https://doc.qt.io/qtforpython-6.10/PySide6/QtCore/QThread.html),
  [Qt 객체와 스레드](https://doc.qt.io/qtforpython-6.10/overviews/qtdoc-threads-qobject.html).

### Trouble Shooting 및 팀 질문 초안 — 외부 등록 미실행

1. **HINT-48 / GUI 버전 기준 확인 요청**
   - 확인 범위: 팀 README/CONTRIBUTING/핸드북과 현재 requirements/lock/pyproject 검색.
   - 결과: 라이브러리 종류는 지정되어 있으나 팀 승인 고정 버전/lock은 확인되지 않음.
   - 검증 환경은 위 버전이며 GUI extra 범위는 로컬 구현 호환성 설정, 팀 확정값 아님.
   - 질문: 팀 기준 Python/PySide6/python-can/cantools/pytest 버전 및 고정 방법은 무엇인가?
   - 영향: 재현 가능한 설치 및 다른 담당자 환경 호환성. Python 3.10~3.13 미실행.

2. **HINT-48 / Windows CP949 GUI --help 출력 오류 (이번 작업에서 수정)**
   - 재현: 기본 CP949 콘솔에서 `python -m pc_diagnostic.gui --help`.
   - 원인: argparse 설명의 em dash 문자로 UnicodeEncodeError 발생.
   - 조치: 콘솔 도움말 구분자를 ASCII로 변경. GUI의 한국어 표시는 유지.
   - 검증: GUI entry point 회귀 테스트 통과. 팀 질문/Issue에 기록할 수 있는 초안이며 등록하지 않음.

3. **HINT-48 / Commit 컨벤션 문서 불일치 확인 요청**
   - CONTRIBUTING §7은 `Jira Key + 동사`, 팀 README/이번 사용자 지침은
     `[작업유형][YYYYMMDD][담당자] 변경 내용`을 안내합니다.
   - 이번 작업은 Commit하지 않았습니다. 후속 Commit은 최신 사용자 지정 팀 형식을 적용하고,
     실제 실행일/확인된 담당자명을 사용해야 합니다. 공통 문서 정합성은 팀 확인 필요.

첫 GUI pytest 실행은 161 PASS / 2 FAIL이었습니다. 위 CP949 출력 오류와 새 Qt 테스트의
이미 deleteLater 처리된 C++ 객체 참조가 원인이었습니다. 신규 테스트는 객체 유효성 또는
정상 thread 종료를 확인하도록 수정했고 최종 163개가 통과했습니다. 기존 테스트 변경/약화 없음.

### 팀 협업 규칙 준수 상태

| 항목 | 상태 | 근거 / 남은 확인 |
| --- | --- | --- |
| 1. 팀 버전 조사 및 대조 | NEEDS_FIX | 지정 라이브러리/현 환경 대조 완료; 팀 고정 버전 확인 필요 |
| 2. snake_case | PASS | Qt 필수 closeEvent/run 및 Qt 클래스/API 명칭은 예외 |
| 3. 책임 분리/상수 | PASS | 표시 제한/취소 설정에 명명된 상수 사용 |
| 4. GUI/통신/Application Logic 분리 | PASS | window / receiver / buffer·demo 분리, 기존 transport 재사용 |
| 5. 한국어 주석 | PASS | 신규 함수와 주요 제어/예외/테스트 흐름 설명 |
| 6. Public/통신 Interface 승인 | PASS | 타 담당자 Public Interface/공식 CAN/LIN 정의 변경 없음; 향후 상대 담당자 리뷰 필요 |
| 7. 결함/질문 기록 | PASS | 위 초안 작성; 승인 없는 외부 등록 없음 |
| 8. 테스트와 코드 리뷰 구분 | PASS | 테스트 PASS, 담당자 코드 리뷰 NOT VERIFIED |
| 9. Commit 형식 | NOT VERIFIED | Commit 미실행; 최신 지정 형식과 문서 불일치 기록 |
| 10. 승인 없는 Git 작업 금지 | PASS | add/Commit/Push/PR/Merge 미실행 |
| 11. cde2ebf 이력 보존 | PASS | 시작/최종 HEAD 동일, reset/rebase 등 미실행 |

미구현: 실제 CAN GUI backend/송신, GUI DBC Decode/Cache/Logging/Filter,
ECU Health/Fault, Fault Injection, standalone installer. 팀 Definition of Done의
실제 CAN 검증/담당자 리뷰는 완료하지 않았습니다. 이번 판정은 요청된 Mock GUI MVP 범위입니다.

---

## DBC / Signal State Cache 확장 (2026-10-11, Asia/Seoul)

목적: Phase 1 위에 향후 GUI/Logger가 공통으로 사용할 DBC Codec과 PC 관찰 데이터 계층 추가.
기존 `src/pc_diagnostic` 구조 유지. GUI, Health/Fault 정책, Fault Injection, KPI는 구현하지 않았습니다.

### 작업 전 상태와 Source of Truth

- 시작 시 `AGENTS.MD` 확인. 기존 Phase 1 소스와 테스트 3개 파일 확인.
- 기존 테스트 baseline: **63 passed in 0.40s**.
- `git status --short`, `git branch --show-current`: 둘 다 `not a git repository`.
  Git metadata 부재로 branch/uncommitted change/commit 기준 비교는 **확인 불가**입니다.
  Git 초기화, commit, push, merge, rebase, history rewrite를 수행하지 않았습니다.
- 파일 검색에서 공식 `vehicle.dbc`, `CAN_Matrix.xlsx`, 별도 최신 Message Definition·Requirements 파일은 발견되지 않았습니다.
  최신 공식 Interface 및 승인 상태는 **확인 불가**입니다. Matrix를 DBC 대용으로 추정하거나 생성하지 않았습니다.

| Source | 선택적으로 확인한 범위 | 이번 구현에서 적용한 경계 |
| --- | --- | --- |
| `design/Gateway_FreeRTOS_Design_Final_Aligned.xlsx` | Summary, 06_Cache_Ownership 관련 행 | 원래 RX 시각 보존, 실패 입력으로 정상값/시각 갱신 금지, 미승인 입력 활성화 보류 |
| `design/Gateway_Routing_Table_v1.0_최종.xlsx` | README, Required_Interface_Changes, Review_Summary 관련 행 | DBC/Matrix 부재와 Interface review gate 유지 |
| `design/Gateway_Signal_Cache_Design_Final.xlsx` | 02_Cache_Structure, 03_Access_Rule 관련 행 | 같은 Frame 값/시각 묶음, 미수신 구분, 관찰 Cache와 Health/Fault 책임 분리 |
| `design/gateway-sw-architecture-and-detailed-design_최종본.pdf` | §3.2, §10, §17.2/17.3, §25, DD-009~012 관련 부분 | PC Tool Logger/Cache 별도 경계 및 TBD/Open 유지 |
| cantools 공식 documentation | load_file, Message encode/decode API | strict load/encode, DBC scaling, truncated/excess payload 금지 |

설계 workbook/PDF, CAN/LIN Interface 정의, Routing/Cache 설계 문서는 수정하지 않았습니다.
이번 PC의 lock/snapshot API는 PC 내부 구현 선택이며 Gateway의 미정 RTOS API를 확정하지 않습니다.

### Architecture 및 동작

`CanInterface → capture → DecodeService → DbcCodec → DecodedMessage → SignalStateCache`

- DbcLoader: 명시적 path, 파일 검사, strict cantools load, load 상태/오류, name와 (ID, format) lookup.
  실패 시 이전 DBC lookup을 비웁니다. 중복 name 또는 같은 ID/format 정의는 거부합니다.
- DbcCodec: exact DBC length 검증, DBC를 통한 scaling/enum encode, decoded/unknown/invalid 결과.
  Unknown/invalid는 raw reference와 원인을 보존하고 다음 Frame으로 계속합니다.
- Encode: strict 필수값/범위 검증 후에만 frame을 반환합니다. CLI는 raw JSON을 출력하며 bus를 열거나 송신하지 않습니다.
- State Cache: 성공 RX만 저장, channel/message 격리, immutable Frame snapshot, Signal 조회,
  received/timestamp/age 제공, multiplex branch 전환 시 이전 branch 값 제거.
- 기존 Raw command/Logger/Interface/Sender는 유지하며 Decode CLI는 기존 capture loop를 사용합니다.
- Signal bit/scale/offset/enum/min/max/invalid와 project CAN ID/DLC 의미를 production 코드에 생성하지 않았습니다.

### 변경 파일

경로는 `tools/pc_diagnostic` 기준입니다.

| 구분 | 파일 |
| --- | --- |
| 신규 데이터 계층 | `src/pc_diagnostic/dbc_loader.py`, `dbc_codec.py`, `decoded_message.py`, `state_cache.py`, `decode_service.py` |
| 기존 코드 확장 | `src/pc_diagnostic/cli.py`, `src/pc_diagnostic/__init__.py` |
| 신규 테스트 | `tests/conftest.py`, `tests/test_dbc_loader.py`, `test_dbc_codec.py`, `test_state_cache.py`, `test_decode_integration.py` |
| 합성 fixture | `tests/fixtures/test_only.dbc` |
| 설정/문서 | `pyproject.toml`, `README.md`, `VERIFICATION.md`, Repository 루트 `.gitignore` (test scratch 제외) |

기존 Phase 1 테스트는 삭제/수정하지 않았습니다. 작업 시작/최종 확인 시 다음 SHA-256이 동일합니다:

```text
test_cli_logger_monitor.py  5ef6696becf8bdf2ed5efed1e55f9b79adbfa782de23c924c4fb67f9538bd8ea
test_frame.py              859bac16675f071c40cd1f27c80fe1c4de17f0e10821ac23f165f063d30f9bd4
test_interfaces.py         94161ff1de028188b4bb46766490e759da49613507a8da1427b313f6027ea87e
```

### 검증 환경/실행 명령

Windows / PowerShell, Python **3.14.6**, pytest **9.1.1**, python-can **4.6.1**, cantools **44.2.1**.
Editable install: `pip install -e './tools/pc_diagnostic[can,dbc,test]'` 성공.

Repository 루트에서:

```powershell
New-Item -ItemType Directory -Force tools/pc_diagnostic/.test-tmp | Out-Null

# 전체
.\.venv\Scripts\python.exe -m pytest tools/pc_diagnostic -q -p no:cacheprovider --basetemp tools/pc_diagnostic/.test-tmp/phase2-run1 --tb=short

# 기존 63개 회귀
.\.venv\Scripts\python.exe -m pytest tools/pc_diagnostic/tests/test_frame.py tools/pc_diagnostic/tests/test_interfaces.py tools/pc_diagnostic/tests/test_cli_logger_monitor.py -q -p no:cacheprovider --basetemp tools/pc_diagnostic/.test-tmp/final-regression --tb=short

# 신규
.\.venv\Scripts\python.exe -m pytest tools/pc_diagnostic/tests/test_dbc_loader.py tools/pc_diagnostic/tests/test_dbc_codec.py tools/pc_diagnostic/tests/test_state_cache.py tools/pc_diagnostic/tests/test_decode_integration.py -q -p no:cacheprovider --basetemp tools/pc_diagnostic/.test-tmp/final-new --tb=short
```

`--basetemp`는 테스트 전용 경로이며 재실행 시 pytest가 정리합니다. 사용자 데이터 경로를 사용하지 않습니다.

| 검증 | 결과 |
| --- | --- |
| 전체 pytest | **140 passed in 1.58s** |
| 기존 Phase 1 Regression 최종 실행 | **63 passed in 0.46s** — 기존 수 유지, 이상 없음 |
| 신규 DBC/Cache/통합 테스트 | **77 passed in 0.60s** |
| 설치된 can-diag.exe smoke | Encode byte 결과, Decode decoded→unknown→invalid 연속 처리 확인 |
| pip check | No broken requirements found |
| 실제 CANable/ECU, DBC 기반 실제 Bus Decode/Encode | **NOT VERIFIED** |
| ACK, ECU 동작, bus-off, timing/load | **NOT VERIFIED** |

최초 baseline 실행은 sandbox 기본 temp/cache 접근 오류로 6개 fixture setup이 실패했습니다.
작업 폴더 내부의 별도 basetemp와 cacheprovider 비활성화로 모두 정상 실행되었으며 테스트 조건은 약화하지 않았습니다.
실행 환경은 Python launcher의 real-location 경고를 출력하지만 실제 Python 실행/pytest/CLI 결과는 위와 같습니다.

신규 테스트 범위:

- Loader: valid/missing/directory/malformed/empty DBC, load 오류 후 재시도, 실패 시 old lookup 제거,
  name/ID lookup, standard/extended 동일 숫자 ID 분리, 중복 정의 거부, optional dependency 부재.
- Codec: factor/offset/signed/big endian, numeric enum 및 choice label encode, roundtrip,
  unknown ID/format, DBC length/DLC mismatch, RTR/error, decode 예외, missing/extra Signal,
  out-of-range/bad label/type/NaN/Infinity, multiplexer, unsupported FD definition.
- Cache: latest message/Signal/timestamp, 값 0·미수신 구분, 다중 message/channel 격리,
  invalid/unknown 및 TX가 성공 RX를 덮어쓰지 않음, snapshot immutability, concurrent 조회,
  원래 RX timestamp/age, mux stale Signal 제거, clear.
- Integration/CLI: Mock→Codec→Cache, unknown/invalid 이후 성공 Frame 계속 처리,
  raw reference 보존, load 실패 시 bus 미개방, Raw 기능 유지, Encode의 미송신/실패 시 출력 없음.

### 공식 DBC / Fixture / Interface

- official vehicle.dbc 사용: **아니오 — Repository에서 발견되지 않음**.
- CAN Matrix 사용: **아니오 — Repository에서 발견되지 않음**.
- Synthetic DBC 사용: **예 — tests/fixtures/test_only.dbc에 TEST ONLY 표기**.
  fixture 이름/Signal/ID는 합성 테스트 값이며 프로젝트 공식 정의를 복제하지 않았습니다.
  production default DBC가 없고 `--dbc` 필수입니다. 실제 CAN Bus에 fixture를 송신하지 않았습니다.
- Interface 변경: **없음, 이상 없음**. 승인되지 않은 VCU Body Command를 production Signal로 추가하지 않았습니다.
- 공식 DBC/Matrix/Message Definition 간 일치 및 IFC-01~06 승인: **확인 불가 / 상대 담당자 리뷰 필요**.
  이번 변경으로 관련 TBD/Open을 확정하지 않았습니다.

### Known Limitations / 다음 단계

- 프로젝트 공식 Interface Decode 정확도는 공식 파일 부재로 **NOT VERIFIED**.
  다음 Task는 승인된 DBC/Matrix/Message Definition 확보 및 정의/버전 대조와 실 캡처 기반 테스트입니다.
- CAN FD/container, LIN, GUI/PySide6, Health/Fault 정책, Fault Injection, KPI 미구현.
- `decoded`는 unpack 성공이며 signal invalid/reserved/min/max/Alive/timeout Health 판정이 아닙니다.
  수신 숫자를 그대로 관찰하며 프로젝트 invalid 값을 추정하지 않습니다.
- Cache 최신값은 처리 도착 순서. TX echo는 RX로 간주하지 않습니다.
  Timestamp 없는 RX도 received로 저장하지만 age는 None. Clock 동기화/역행 판정 정책 없음.
- DBC reload는 수신 중 지원하지 않습니다. 수신을 중지하고 Cache를 clear하거나 새 service를 구성해야 합니다.
- Python 3.10 이상을 선언했으나 이번 실행은 3.14.6만 검증. cantools 범위의 다른 버전/다른 OS는 **NOT VERIFIED**.
- Hardware test는 미수행. Software/Mock/VirtualBus 결과를 Hardware PASS로 주장하지 않습니다.
- Git status/현재 branch는 시작·최종 모두 **확인 불가** (Git metadata 없음).
  Commit/push/merge/rebase: **수행하지 않음**.

---

## Phase 1 기록 (보존)

검증일: 2026-10-08 (Asia/Seoul)

## 환경

- Windows / PowerShell
- Python 3.14.6
- pytest 9.1.1
- python-can 4.6.1
- 프로젝트 `.venv`에 editable package 설치
- 작업 디렉터리에 Git 메타데이터가 없어 commit/diff 기준 식별자는 없음

## 실행 및 결과

Repository 루트에서 실행:

```powershell
.\.venv\Scripts\python.exe -m pytest tools/pc_diagnostic -q
```

결과: **63 passed in 0.44s** (최종 실행). 기존 테스트가 없는 상태에서 새 테스트를
추가했으며 기존 테스트 삭제/약화는 없습니다.

| 검증 범위 | 결과 | 근거 및 한계 |
| --- | --- | --- |
| RawCanFrame | PASS (software) | 11/29-bit 경계, 0/8-byte, RTR, error, immutable payload, 잘못된 타입/ID/DLC/timestamp 거부, JSON roundtrip |
| MockCanInterface | PASS (software) | FIFO, timeout, TX/RX 분리, loopback, thread 주입, 종료 시 대기 해제, 종료 후 I/O 거부 |
| PythonCanInterface | PASS (software) | 실제 python-can VirtualBus 두 객체로 standard/extended/data/RTR 송수신, backend timestamp/channel 보존 |
| Adapter 실패 경로 | PASS (software) | open/recv/send 실패 전파, shutdown 1회, FD 및 malformed frame 거부; 실패는 stub로 주입 |
| Raw CAN Logger | PASS (software) | JSONL readback, CSV escaping/필드 보존, 덮어쓰기 거부, 잘못된 입력 줄 위치, 디스크 오류 처리 |
| Monitor/Sender/CLI | PASS (software) | 표시, count와 timeout 구분, duration 종료, 송신 검증, Ctrl+C cleanup, 열기 전 입력 검증, 잘못된 설정 거부 |
| 설치/진입점 | PASS (software smoke) | editable install, `can-diag --help`, `python -m pc_diagnostic monitor --duration 0.01` |
| 의존성 | PASS (software smoke) | `pip check`: No broken requirements found |
| python-can 없는 Mock 실행 | PASS (software smoke) | system Python에 can 모듈이 없는 것을 확인 후 Mock send 실행, 실제 adapter 요청 시 설치 안내 오류 확인 |
| 실제 CAN Hardware 송수신 | **NOT VERIFIED** | 장치/driver 연결과 실제 bus 시험 미수행 |
| ACK, ECU 수신/동작, bus-off, timing, bus load | **NOT VERIFIED** | 물리 bus capture 및 ECU 근거 없음 |
| 장시간/고속 무손실 logging, 전원 차단 내구성 | **NOT VERIFIED** | Phase 1 기능 테스트 범위 밖 |
| Python 3.10~3.13 및 다른 OS | **NOT VERIFIED** | 코드의 최소 버전 선언과 별개로 해당 환경에서 실행하지 않음 |

테스트의 CAN ID/payload는 합성 벡터입니다. Gateway message 정의나 승인된 송신 시나리오가
아니며 제품 기본값에 포함하지 않았습니다. VirtualBus 성공을 Hardware PASS로 사용하지 않습니다.

## 후속 Hardware 검증에 필요한 입력

장치 종류와 driver 버전, channel, 승인된 bitrate와 raw 송신 벡터, 물리 bus 구성,
독립 CAN capture/ECU 관찰 결과가 필요합니다. 해당 입력을 받기 전까지 위 Hardware
항목은 NOT VERIFIED입니다. CAN/LIN interface 변경이 필요해지면 상대 담당자 리뷰를
거쳐야 하며, 이 구현으로 TBD/Open 또는 Signal 정의가 확정되지는 않습니다.
