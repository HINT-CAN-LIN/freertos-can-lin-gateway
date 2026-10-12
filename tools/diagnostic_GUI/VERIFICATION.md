# PC Diagnostic 검증 기록

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
