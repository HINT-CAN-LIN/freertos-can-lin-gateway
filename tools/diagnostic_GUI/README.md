# PC Diagnostic Tool — Raw CAN / DBC / Signal State Cache

Classic CAN raw 프레임을 수신·표시·기록·송신하는 독립 Python 패키지입니다.
Gateway CAN ID, message별 DLC, Signal bit layout/scale/enum은 정의하지 않습니다.
Phase 1 Raw CAN 기능 위에 명시적으로 지정한 DBC의 Decode/Encode와 PC 관찰용 State Cache를 제공합니다.
Phase 3B는 Mock Raw GUI, Phase 3C는 명시적 DBC Decode/Cache, Phase 3D-1은 사용자 매핑 Vehicle Status를 제공합니다.
Phase 3D-2는 명시적 ECU/Fault 관측과 처리된 Raw RX 통계를 제공합니다. Health/Fault 판정은 하지 않습니다.
Phase 3E는 기존 Raw Logger 계약의 CSV/JSONL 파일 기록 GUI를 제공합니다. 아래 이전 Phase 절은 당시 기록입니다.
LIN, GUI의 송신, ECU Health/Fault 정책, Fault Injection, KPI, 주기 송신, CAN FD는 미구현입니다.
CAN FD 수신 시 명시적 오류로 중단하며 Classic CAN으로 변환하거나 조용히 버리지 않습니다.

## 설계 근거 및 경계

이 절의 설계 근거 경로와 파일 검색 결과는 원본 개발 폴더 기준의 과거 기록입니다.
팀 Repository의 현재 파일 존재 여부나 Interface 승인 상태를 뜻하지 않습니다.

- 작업 전 Repository `AGENTS.MD` 확인.
- `design/gateway-sw-architecture-and-detailed-design_최종본.pdf` §3.2, §10,
  §25, DD-012의 PC Tool/file Logger 책임 경계와 미정 사항 참조.
- PC 파일 Logger는 Gateway 내부 Logger와 별도입니다. 아래 파일 schema는 PC 도구의
  로컬 저장 형식이며 Gateway transport/retention protocol을 확정하지 않습니다.
- DBC/Cache 확장에서는 FreeRTOS workbook의 `Summary`, `06_Cache_Ownership`,
  Routing workbook의 `README`, `Required_Interface_Changes`, `Review_Summary`,
  Signal Cache workbook의 `02_Cache_Structure`, `03_Access_Rule`에서 관련 행만 확인했습니다.
  PDF §17.2/17.3과 DD-009/010도 확인했습니다. 설계 문서는 수정하지 않았습니다.
- Repository 검색 결과 공식 `vehicle.dbc`, `CAN_Matrix.xlsx`, 별도 최신 Message Definition·Requirements는
  없습니다. 실제 프로젝트 Signal 해석에는 승인된 최신 DBC와 담당자 확인이 필요합니다.
  Load 성공은 파일 parsing 성공이며 승인/버전 호환성 인증을 의미하지 않습니다.
- 프로젝트 CAN/LIN interface 및 TBD/Open 항목을 변경하지 않았습니다.
  향후 변경 시 상대 담당자 리뷰가 필요합니다.

## 설치 및 테스트

Repository 루트에서 PowerShell:

```powershell
python -m venv tools/diagnostic_GUI/.venv
.\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pip install -e './tools/diagnostic_GUI[can,dbc,test]'
.\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pytest tools/diagnostic_GUI -q
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe --help
```

Python 3.10 이상을 대상으로 작성했습니다. 실제 검증 환경과 결과는
`VERIFICATION.md`에 기록합니다. `python-can` 없이 Mock만 사용하려면 extras 없이
`pip install -e ./tools/diagnostic_GUI`으로 설치합니다.
`python -m pc_diagnostic`도 같은 CLI를 실행합니다.
DBC만 추가하려면 `pip install -e './tools/diagnostic_GUI[dbc]'`로 cantools를 설치합니다.
Raw command는 cantools를 import하지 않습니다. DBC 의존성/파일이 없어도 Raw mode를 사용할 수 있습니다.
Sandbox에서 pytest 기본 임시 경로에 접근할 수 없으면 작업 폴더의 새 경로를 지정합니다:

```powershell
New-Item -ItemType Directory -Force tools/diagnostic_GUI/.test-tmp | Out-Null
.\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pytest tools/diagnostic_GUI -q -p no:cacheprovider --basetemp tools/diagnostic_GUI/.test-tmp/local-run
```

`--basetemp`는 pytest가 정리하는 전용 임시 폴더입니다. 사용자 데이터 경로로 지정하지 않습니다.

## CLI

기본 backend는 `mock`입니다. 자동 연결, 자동 생성 트래픽, 기본 프로젝트 ID/bitrate는 없습니다.
예제 변수에는 사용자가 준비한 입력이나 승인된 설정을 넣습니다.

```powershell
# $fixture: 아래 schema로 작성한 JSONL 파일 경로
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe monitor --input $fixture
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe log --input $fixture --output capture.jsonl
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe log --input $fixture --output capture.csv --format csv

# 빈 Mock에서 1초 동안 대기하고 종료 (CAN 통신 타이밍 설정이 아님)
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe monitor --duration 1

# $canId, $payloadHex: 사용자가 지정한 raw ID와 hex payload. 실제 버스로 보내지 않음.
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe send --id $canId --data $payloadHex

# 실제 장치 설정을 명시적으로 전달. 장치/드라이버별 검증은 별도로 필요.
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe monitor --backend python-can --interface $driver --channel $channel --bitrate $bitrate --duration 10
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe log --backend python-can --interface $driver --channel $channel --bitrate $bitrate --duration 10 --output hardware-capture.jsonl
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe send --backend python-can --interface $driver --channel $channel --bitrate $bitrate --id $canId --data $payloadHex
```

- ID는 decimal 또는 `0x` prefix hex. 29-bit 프레임은 `--extended` 필요.
- `--data`는 hex 문자열이며 공백이 있으면 따옴표로 묶습니다. 생략 시 빈 payload.
- Data frame DLC는 payload byte 수로 도출하거나 `--dlc`로 동일한 값을 지정합니다.
  message별 DLC 의미를 추정하지 않습니다.
- RTR 송신은 `--rtr --dlc <요청 길이>`로 지정하고 payload는 비웁니다.
- Error frame은 capture-only이며 Sender에서는 거부합니다.
- 숫자 채널을 요구하는 backend는 `--channel-index`를 사용합니다.
- Hardware backend에는 `--interface`, channel, `--bitrate`가 필수입니다.
  `python-can` 외부 설정 자동 로딩을 끄므로 숨은 환경 설정을 사용하지 않습니다.
  SocketCAN처럼 OS에서 bitrate를 설정하는 backend는 장치를 사전 설정하고,
  그 설정과 CLI 값의 일치 여부를 사용자가 확인해야 합니다. adapter는 이를 검증하지 않습니다.
- `--count`는 수신 프레임 수, `--duration`은 wall-clock 제한입니다. 둘 다 지정하면
  먼저 도달하는 조건에서 종료합니다. Timeout은 프레임 수로 세지 않습니다.
- 실제 bus에서 두 제한이 없으면 Ctrl+C까지 대기합니다. `--count`만 지정하면
  트래픽이 없는 동안 계속 기다립니다.
- Mock fixture는 FIFO로 즉시 제공하며 기록된 timestamp에 맞춘 재생은 하지 않습니다.
  Mock은 제한 생략 시 fixture 끝에서 종료하며, 무한 대기가 예상되는 설정은 거부합니다.
- Logger는 JSONL/CSV를 지원하고 기존 파일은 덮어쓰지 않습니다. 프레임마다 flush하지만
  전원 차단 내구성(fs sync), rotation, 고속 수신 무손실, 저장 용량 보장은 범위 밖입니다.
- 종료 코드: 0 정상, 1 동작/파일/프레임 오류, 2 CLI 인수 오류, 130 Ctrl+C.
- 송신 성공은 backend 제출 성공입니다. ECU 수신/실행 또는 Hardware PASS를 의미하지 않습니다.

## 데이터 모델과 파일 형식

`RawCanFrame`은 immutable이며 payload도 `bytes`로 복사해 보관합니다.
일반 프레임은 11/29-bit ID와 Classic CAN 0..8-byte 범위만 검증합니다.
Error frame ID는 backend error mask 보존을 위해 29-bit 범위를 허용하며 해석하지 않습니다.

| 필드 | 의미 |
| --- | --- |
| `arbitration_id` | 정수 raw ID, 프로젝트 의미 없음 |
| `data` | Python 모델은 bytes, 파일은 대문자 hex 문자열 |
| `dlc` | 0..8, RTR은 요청 길이, 나머지는 payload byte 수와 일치 |
| `is_extended_id` | 29-bit 형식 여부 |
| `is_remote_frame` | RTR 여부 |
| `is_error_frame` | backend가 보고한 error frame 여부 |
| `timestamp` | backend가 제공한 초 단위 값, 미제공은 null; timestamp를 새로 합성하지 않음 |
| `channel` | backend의 문자열/정수 채널, 미제공은 null |
| `is_rx` | backend RX/TX 표시; Mock TX echo는 false |

JSONL은 한 줄에 한 JSON object입니다. `arbitration_id`는 필수이고 나머지는 모델 기본값을
사용할 수 있습니다. 알 수 없는 필드, 잘못된 타입/hex/DLC는 오류입니다.
Logger 출력에는 모든 필드가 포함됩니다. JSONL은 `--input`으로 다시 읽을 수 있습니다.
CSV는 같은 필드를 header로 가지며 null은 빈 셀, bool은 `True`/`False`로 저장합니다.
CSV 입력/재생은 제공하지 않습니다.

실제 RX timestamp는 driver가 반환한 값을 그대로 유지합니다. 서로 다른 장치 간 clock 동기화,
정확도 및 gateway source age는 이 도구가 보장하지 않습니다.

## 코드 구성

```text
src/pc_diagnostic/
  frame.py        RawCanFrame 및 검증/JSON record 변환
  interfaces.py   CanInterface, MockCanInterface, PythonCanInterface skeleton
  monitor.py      capture loop 및 사람이 읽을 raw 표시
  logger.py       JSONL/CSV 파일 logger, JSONL fixture reader
  sender.py       단일 raw 송신
  dbc_loader.py   cantools strict load, 상태 및 이름/ID lookup
  dbc_codec.py    RawCanFrame ↔ DBC signals
  decoded_message.py  immutable decode 결과와 raw 참조
  state_cache.py  최근 RX observation과 thread-safe snapshot
  decode_service.py   Codec → Cache 공통 처리
  cli.py          monitor / log / send / decode / encode
  gui/            선택적 PySide6 Mock 창, worker, 유한 표시 버퍼, TEST ONLY demo
tests/            기존 Phase 1 + DBC/State/통합 검증
tests/fixtures/test_only.dbc  TEST ONLY synthetic DBC
```

Interface는 생성 시 열리며 context manager 또는 `shutdown()`으로 닫습니다.
`recv(None)`은 대기, `recv(0)`은 polling, timeout은 `None`을 반환합니다.
종료 후 I/O와 backend 오류는 `CanInterfaceError`입니다.
Mock은 thread-safe 주입과 종료 시 수신 대기 해제를 지원합니다. 임의의 hardware backend에서
동시 호출/종료를 안전하게 수행하는 것은 보장하지 않습니다. CLI는 단일 수신 루프입니다.

PythonCanInterface는 device별 확장이 가능한 최소 adapter입니다. 자체 재연결, bus-off 복구,
hardware filter, driver 설치, 장치 탐색은 제공하지 않습니다.
Backend API 근거: [python-can Bus](https://python-can.readthedocs.io/en/stable/bus.html),
[Message](https://python-can.readthedocs.io/en/stable/message.html),
[Virtual interface](https://python-can.readthedocs.io/en/stable/interfaces/virtual.html).
Virtual bus 테스트는 같은 process의 Python 객체 간 통신이며 물리 CAN 검증이 아닙니다.

## DBC mode

`monitor`, `log`, `send`는 Phase 1 raw mode입니다. payload의 Signal 의미를 해석하지 않습니다.
`decode`, `encode`는 DBC mode이며 매번 `--dbc <path>`가 필수입니다.
프로젝트별 bit/scale/offset/enum을 Python에 중복 정의하지 않고
[cantools Message API](https://cantools.readthedocs.io/en/stable/)를 통해 처리합니다.

```powershell
# $dbc: 사용자가 제공한 승인된 DBC 경로. $fixture: Raw JSONL 입력
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe decode --dbc $dbc --input $fixture
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe decode --dbc $dbc --backend python-can --interface $driver --channel $channel --bitrate $bitrate --duration 10

# $messageName: DBC에 존재하는 이름; $signalJson: Signal 이름→값 JSON object
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe encode --dbc $dbc --message $messageName --signals $signalJson
```

Decode는 기존 capture loop를 재사용하고 한 프레임당 JSON object를 stdout에 출력합니다.
`DecodedMessage.to_record()`의 `timestamp`, `arbitration_id`, `message_name`, `signals`,
`decode_status`, `error`, `raw_frame`을 포함합니다. Raw Frame은 실패 결과에도 보존됩니다.
`signals`는 DBC factor/offset을 적용한 숫자 값이며 enum은 숫자로 반환합니다.
Cache는 같은 표현을 사용하며 choice label을 임의로 생성하지 않습니다.

| 결과 | 의미 | Cache |
| --- | --- | --- |
| `decoded` | 정상 형식/길이로 cantools unpack 성공 | RX일 때만 최신 observation 갱신 |
| `unknown` | 해당 ID와 standard/extended 형식 조합이 DBC에 없음 | 기존 값/시각 보존 |
| `invalid` | 길이 불일치, RTR/error, unsupported DBC message, decode 예외 등 | 기존 값/시각 보존 |

`decoded`는 codec 성공 상태입니다. reserved/invalid raw pattern, DBC min/max 밖 수신값,
ECU Health, timeout, Alive Counter 유효성을 정상이라고 판정하는 상태가 아닙니다.
이 단계에서는 해당 수신 숫자를 observation으로 보관하고 Health/Fault 정책을 적용하지 않습니다.
지원하는 프레임은 ordinary Classic CAN message와 cantools가 처리하는 multiplexed message입니다.
CAN FD/container message는 Codec에서 명확히 거부합니다.

Decode 실패는 해당 프레임의 `invalid` 결과로 출력하고 다음 프레임을 처리합니다.
Unknown/invalid 결과가 있어도 capture 자체가 완료되면 종료 코드는 0입니다.
DBC load 실패는 시작 전 오류(종료 코드 1)로 반환하고 bus를 열지 않습니다.
Raw Frame 생성 단계의 잘못된 JSON/프레임과 transport failure는 기존 Phase 1 오류 처리를 따릅니다.

Encode는 scaled numeric 값 또는 DBC에 정의된 choice label 문자열을 받습니다.
`strict=True`로 필수 Signal 누락, 추가 Signal, DBC 범위 밖 값과 잘못된 label을 거부합니다.
NaN/Infinity, bool, null도 거부합니다. 정수/physical 값의 양자화는 cantools 동작을 따릅니다.
성공하면 Phase 1 JSONL과 동일한 raw object 하나를 출력하며 timestamp/channel은 미제공,
`is_rx=false`입니다. **Encode CLI는 bus를 열거나 송신하지 않습니다.**
실패하면 원인만 stderr에 출력하고 Raw Frame 출력/생성을 완료하지 않습니다.
Library 호출자는 성공한 `RawCanFrame`만 별도로 Sender에 전달할 수 있습니다.

### TEST ONLY 예제

아래 예제는 프로젝트 Signal과 무관한 합성 fixture로 encode→decode를 확인합니다.
Production DBC 기본값으로 등록하지 않으며 실제 bus에 송신하는 예제가 아닙니다.

```powershell
$testDbc = 'tools/diagnostic_GUI/tests/fixtures/test_only.dbc'
$testSignals = '{"Measurement":-10,"Mode":"ONE","Counter":7}'
.\tools\diagnostic_GUI\.venv\Scripts\can-diag.exe encode --dbc $testDbc --message TestOnlySample --signals $testSignals

# Mock RX 입력도 사용자가 지정. 출력 JSON이 아니라 Raw Frame JSONL을 --input으로 전달.
# Encode 출력은 TX 표시이므로 decode는 가능하지만 received Cache는 갱신하지 않음.
```

## Signal State Cache

```text
CanInterface → capture → DecodeService → DbcCodec → DecodedMessage
                                 └→ SignalStateCache → 향후 Logger / thin GUI consumers
```

PC Cache는 Gateway Signal Cache/HealthTask/FaultManager를 대체하지 않습니다.
성공한 RX decode 결과만 Message별로 저장하며 key는 `(channel, message_name)`입니다.
같은 Signal 이름도 message/channel별로 분리하고, TX 제출/echo를 실제 RX로 세지 않습니다.

```python
from pc_diagnostic import DbcLoader, DbcCodec, DecodeService

loader = DbcLoader().load(dbc_path)   # 호출자가 제공한 경로
service = DecodeService(DbcCodec(loader))
result = service.process(raw_frame)  # capture callback에서도 동일하게 사용
latest = service.cache.get_message(message_name, channel=channel)
value = service.cache.get_signal(message_name, signal_name, channel=channel)
received = service.cache.has_received(message_name, channel=channel)
rx_stamp = service.cache.last_timestamp(message_name, channel=channel)
snapshot = service.cache.snapshot()
```

- `get_signal_state()`는 value와 timestamp/ID/message/channel을 함께 반환합니다.
- 마지막 성공 RX message와 모든 signals가 같은 immutable snapshot에 포함됩니다.
  Mapping을 복사해 보관하고 lock으로 교체/읽기를 보호합니다.
- snapshot은 조회 시점의 읽기 전용 사본입니다. 이후 갱신으로 이전 사본이 변경되지 않습니다.
- multiplex branch가 바뀌면 최신 message 전체를 교체하므로 이전 branch signal은 최신 조회에서 사라집니다.
- 최신은 처리 도착 순서입니다. 서로 다른 backend clock을 비교해 정렬하지 않습니다.
- `last_timestamp()`는 원래 RX timestamp를 반환합니다. 미제공은 `None`이며 cache commit time을 합성하지 않습니다.
- `age(message_name, now=..., channel=...)`는 호출자가 **같은 clock 기준**의 현재 시각을 제공할 때 차이만 계산합니다.
  미수신/시각 미제공/역행 시각은 `None`이며 timeout/offline 판정은 하지 않습니다.
- 미수신과 값 0을 구분합니다. `has_received()`는 성공 RX observation 존재 여부이며 link Health 상태가 아닙니다.
- DBC Loader는 수신 thread를 시작하기 전에 설정합니다. 동시 reload는 지원하지 않습니다.
  DBC 변경 시 새 DecodeService/Cache를 만들거나 수신을 멈추고 기존 Cache를 `clear()`합니다.
- CLI 프로세스 종료 시 Cache는 소멸합니다. 저장/과거 이력/재연결·시간 동기화 정책은 향후 범위입니다.


## Phase 3B — Windows Mock GUI

CLI는 그대로 유지합니다. Phase 3B Raw GUI에 Phase 3C의 명시적 DBC Decode/Cache 표시를 추가했습니다. GUI에서 실제 CAN 연결이나
송신을 선택할 수 없습니다. 창 상단의 **Mock / DEMO / TEST ONLY** 표시는 실제 ECU 응답이
아님을 뜻합니다. Hardware **NOT VERIFIED**.

Repository 루트에서 GUI 선택 의존성 설치 및 실행:

```powershell
.\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pip install -e './tools/diagnostic_GUI[gui,test]'
.\tools\diagnostic_GUI\.venv\Scripts\can-diag-gui.exe
# 동일한 GUI를 모듈로 실행
.\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pc_diagnostic.gui
```

설치 후 탐색기에서 `tools/diagnostic_GUI/.venv/Scripts/can-diag-gui.exe`를 더블클릭해
콘솔 명령 없이 Windows 창을 열 수 있습니다. 이것은 가상환경의 GUI 실행 진입점이며,
Python이 포함된 배포용 standalone EXE/installer는 아닙니다. CLI만 설치하면 PySide6가
필요하지 않습니다. GUI는 cantools/python-can 없이도 기존 Mock과 RawCanFrame을 사용합니다.

PySide6가 없거나 import할 수 없으면 콘솔 실행은 stderr에 원인과 설치 안내를 표시합니다.
콘솔 없는 Windows 실행은 Qt 없이 `user32.MessageBoxW` 오류창을 한 번 표시합니다.
`tools/diagnostic_GUI` 폴더의 활성 환경에서 `pip install -e '.[gui]'`로 설치하라는 안내를
제공하며 import 예외의 내부 경로/원문은 노출하지 않습니다. 안내 함수 자체가 실패해도
추가 재시도 없이 종료 코드 1로 끝납니다. 정상 GUI의 실행 경로는 유지했습니다.

- **Start**: 새 Mock 수신 worker 시작. 실행 중 중복 Start를 차단합니다.
- **Stop**: 비동기 취소 후 transport 해제. 종료가 완료되면 재시작할 수 있습니다.
- **Clear**: 표시 행, 수신 계수, 버퍼 제외 계수 초기화. 수신 중에는 새 프레임이 다시 표시됩니다.
- 상태: Disconnected / Running / Stopped / Error. 오류 영역에 예외 종류와 원인을 표시합니다.
- Timestamp / Channel / CAN ID / DLC / DATA는 실제 수신 RawCanFrame에서 읽습니다.
  STD/EXT/RTR/ERROR 속성을 구분하며 ID 숫자와 DLC를 변환하지 않습니다.
- 데모는 기존 `tests/fixtures/test_only.dbc` 및 `test_dbc_codec.py`의 합성 예제를 재사용합니다.
  새 공식 ID/Signal/Enum을 정의하지 않습니다. 데모 timestamp는 PC에서 생성한 시간이며
  채널은 `DEMO/TEST ONLY`입니다. 사용자가 DBC를 선택하기 전에는 Signal을 해석하지 않습니다.

구조: `MockCanInterface.recv → 기존 RawCanFrame → ReceiveWorker → FrameBuffer → Qt timer/slot → MainWindow`.
Qt 오류/종료 signal만 사용하며 프레임마다 signal을 발행하지 않습니다. 수신은 QThread에서,
화면 갱신은 메인 스레드에서 수행합니다. 기존 CLI capture loop는 변경하지 않았고 GUI는
취소 이벤트를 확인하는 별도 수신 pump로 동일 recv 계약을 사용합니다.

버퍼 512개, 화면 500행, 최대 100개 batch/50 ms 갱신, DEMO 생성 간격 0.1초,
recv polling 0.05초, 창 종료 대기 1000 ms는 **GUI 내부 자원/취소 설정**입니다.
CAN/LIN 주기나 Fault Timeout을 정의하지 않습니다. 버퍼가 가득 차면 가장 오래된 표시
대기 프레임을 제외하고 제외 수를 보여줍니다. 수신 카운터는 Clear 이후 전체 수신 수이며
보이는 행 수와 다릅니다. 화면 행 제한은 과거 표시를 제거하며 캡처 파일을 기록하지 않습니다.
Stop 후 남은 버퍼는 제한 batch로 비웁니다. 종료 지연 시 창을 유지해 Error를 표시하며
worker를 강제 terminate하지 않습니다. 오류 후 Start로 새 Mock을 시작할 수 있습니다.

검증 명령은 패키지 폴더에서 실행합니다:

```powershell
cd tools/diagnostic_GUI
New-Item -ItemType Directory -Force .test-tmp | Out-Null
$gui_test_temp = '.test-tmp/run-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $gui_test_temp
# 실제 Windows 창을 열어 자동 smoke 및 widget 렌더 증거 저장 (offscreen과 별도)
.\.venv\Scripts\python.exe tests/gui_native_smoke.py --screenshot .test-tmp/gui-native.png
```

`test_gui_app.py`는 설치된 Qt를 삭제하지 않고 import 실패/콘솔 부재/Windows API 오류를
모의합니다. 반복 Start/Stop 테스트는 이전 표시 행이 남아 있어도 매회 새로운 수신 계수
증가와 독립 Mock의 생성·해제를 확인합니다. 테스트 결함 검출은 무수신 주입으로 확인했고,
native smoke는 실제 Windows 창 검증이라는 별도 목적을 갖습니다.

`test_gui.py`는 Qt offscreen + 기존 Mock을 사용합니다. GUI extra가 없으면 Qt 테스트는
skip하고 기존 CLI 테스트와 Qt 독립 버퍼 테스트를 실행합니다. native smoke는 Windows
Qt 플랫폼을 요구하고 창 노출, 반복 Start/Stop, Clear, 활성 worker 종료/해제를 확인합니다.
별도로 사람이 창과 버튼을 확인한 결과는 `VERIFICATION.md`에 구분해 기록합니다.

이번 Windows 검증 버전은 Python 3.14.6 / PySide6 6.10.3 / python-can 4.6.1 /
cantools 44.2.1 / pytest 9.1.1입니다. 기존 Python >=3.10 조건과 기존 의존성 범위는
유지했습니다. GUI extra `PySide6>=6.10,<7`은 이번 구현의 호환성 범위이며 팀의 승인된
고정 버전이 아닙니다. 팀 README/CONTRIBUTING/핸드북/설정에서 고정 버전은 확인되지
않았습니다. 팀 버전 합의와 Python 3.10~3.13 검증은 **검토 필요 / NOT VERIFIED**입니다.

미구현: GUI 파일 Logging, Filter, Replay, 실제 CAN
backend, 운전자 입력/송신, Health/Fault 판정, Fault Injection, standalone 배포.
기존 CLI의 monitor/log/send/decode/encode는 유지하며 실제 버스 시험은 이번 작업에
포함하지 않습니다. 생산용 Interface 변경은 **상대 담당자 리뷰 필요**입니다.

Thread lifecycle 참고: [Qt QThread 공식 문서](https://doc.qt.io/qtforpython-6.10/PySide6/QtCore/QThread.html),
[Qt 객체와 스레드](https://doc.qt.io/qtforpython-6.10/overviews/qtdoc-threads-qobject.html).


P2/P3 수정 검증 결과: 기존 CLI 140개 + GUI/버퍼/안내 30개, 전체 **170 passed**.
실제 Windows pythonw 오류 안내창과 정상 GUI 진입점을 별도로 확인했습니다.
현재 설치/팀 승인 상태와 검증 상세는 `VERIFICATION.md`의 최신 절을 참조하세요.
Windows API 근거: [Microsoft MessageBoxW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messageboxw).

## Phase 3C — 명시적 DBC Decode / Signal Cache GUI

GUI 실행 진입점은 그대로입니다. 패키지 폴더의 활성 환경에서
`pip install -e '.[gui,dbc]'`로 필요한 선택 의존성을 설치할 수 있습니다.
CLI만 사용하는 경우 GUI extra는 필요하지 않습니다. 이번 작업에서는 패키지를
재설치하거나 버전 범위를 바꾸지 않았습니다.

1. GUI를 열면 **DBC: not selected / Decode disabled**입니다. 아무 파일도 자동 로드하지 않습니다.
2. **Select DBC...**에서 파일을 직접 선택합니다. 파일명, Loaded / Load failed,
   Decode enabled / disabled를 확인합니다. 로드 성공은 팀 Interface 승인을 의미하지 않습니다.
3. DEMO 검증에만 `tests/fixtures/test_only.dbc`를 선택한 뒤 **Start**를 누릅니다.
   공식/검토 중인 DBC와 합성 DEMO 프레임의 의미를 연결하거나 실제 ECU 응답으로 해석하지 않습니다.
4. Raw 행을 선택하면 원래 Timestamp/Channel/CAN ID/DLC/DATA, DBC Message 이름 및
   해당 프레임의 Decode 결과/오류가 보입니다. STD/EXT 형식은 기존 Codec 계약을 따릅니다.
5. **Selected frame signals**는 선택한 프레임의 값/Unit/원래 Timestamp입니다.
   **Last successful RX Cache**는 같은 Channel/Message에서 마지막으로 성공한 RX의 값,
   원래 Timestamp / Age와 최신 처리 시도 상태입니다. 과거 프레임을 선택하면 두 화면의
   Timestamp와 값이 다를 수 있으며, Cache 값이 선택 프레임의 값으로 표시되지는 않습니다.

신호 이름/Unit은 명시적으로 로드한 DBC, 값은 기존 DbcCodec 결과에서만 가져옵니다.
빈 Unit은 그대로 비워 둡니다. Unknown ID는 Raw를 유지하고 **Unknown / Undefined**로
표시하며 가짜 Signal을 만들지 않습니다. Error frame의 ID는 오류 mask일 수 있어 DBC Message로 연결하지 않습니다. DLC 불일치/Decode 예외는 기존 `invalid`
결과를 표시하고 정상 Cache 값/시각은 유지합니다. 최신 실패 원인은 Cache 영역에도
따로 표시합니다. TX의 해석 성공은 정상 RX Cache를 갱신하지 않습니다.

DBC가 없거나 로드가 실패해도 Raw Monitor는 동작합니다. 선택 취소는 기존 세션을
유지합니다. Loader 계약에 따라 **파일 교체 시도마다 새 DecodeService/Cache**를 만들며,
실패한 교체는 Decode를 비활성화합니다. 이전 Raw 행에는 그 당시 Decode 결과와 Unit을
보존하고 **historical DBC session**으로 표시하여 새 Cache와 섞지 않습니다.
**Stop 후 Worker 종료와 잔여 버퍼 처리 완료 전에는 파일 교체가 차단**됩니다.
수신 중 핫 리로드는 지원하지 않습니다.

기존 **Clear**는 표시 행/카운터/대기 버퍼를 초기화하며 같은 DBC 세션의 정상 Cache는
보존합니다. Start/Stop도 같은 DBC 세션을 유지합니다. 프로그램 종료 시 Cache는 소멸합니다.
별도 Cache 영속화, 실제 backend 재연결/clock 동기화/운영 정책은 **Open / 향후 검토**이며
현재 DEMO 동작을 제품 정책으로 확정하지 않습니다.

Age는 DEMO가 사용하는 PC wall clock과 원래 RX Timestamp의 차이를 기존 Cache API로
계산합니다. Timestamp 미제공/역행은 **unknown**이며 수신을 멈춰도 Age 표시는 갱신됩니다.
Age만으로 Offline/Healthy/Fault를 판정하지 않습니다.

구조:
`ReceiveWorker → FrameBuffer → 제한된 메인 스레드 batch → DecodeSession → 기존 DecodeService/DbcCodec/SignalStateCache → Qt 표시`.
CAN 수신은 기존 QThread에서 처리하고 GUI 조합 계층은 Qt 독립입니다.
버퍼 512개, Raw 이력 500행, batch 100개 제한을 유지합니다. 최신 처리 상태 메타데이터도
512개 Channel/Message key로 제한하며 제외된 key는 최신 시도를 조회할 수 없다고 표시합니다.
기존 Cache의 저장 계약은 변경하지 않았습니다.
**Received / 표시 버퍼 제외 / Raw/Decode processed**를 구분합니다. 처리 전에 제외된
프레임은 Decode/Cache에 전달하지 않으며 전체 수신을 모두 해석했다고 주장하지 않습니다.
250 ms Age 갱신과 화면 크기/여백은 GUI 설정이며 CAN/LIN 규격 수치가 아닙니다.

패키지 폴더에서 검증:
```powershell
New-Item -ItemType Directory -Force .test-tmp | Out-Null
$phase3c_temp = '.test-tmp/phase3c-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $phase3c_temp
# 실제 Windows 창 자동 검증: 호출자가 TEST ONLY DBC를 명시
.\.venv\Scripts\python.exe tests/gui_decode_native_smoke.py --dbc tests/fixtures/test_only.dbc --screenshot .test-tmp/phase3c-native.png
```

현재 검증: 기존 170개 보존 + 신규 31개, 전체 **201 passed**.
Qt offscreen, Windows native 자동 검증, 사용자 직접 파일 선택/화면 확인은 서로 구분하여
`VERIFICATION.md`에 기록합니다. **Hardware NOT VERIFIED**,
팀 고정 라이브러리 버전 미확정, 담당자 코드 리뷰 **NOT VERIFIED**를 유지합니다.

미구현: 실제 CAN GUI backend/송신, 파일 Logging/Export, Filter/Replay,
운전자 입력, ECU Health/Fault, Fault Injection, standalone 배포, 수신 중 DBC 교체.
Production DBC/Matrix 정합성 및 Interface 승인은 **상대 담당자 리뷰 필요**입니다.

## Phase 3D-1 — Vehicle Status

기존 GUI 실행 방법은 동일합니다. **Vehicle Status** 탭은 같은 DecodeSession의
SignalStateCache를 조회하며 CAN 수신/DBC Decode/Scale/Enum 규칙을 새로 구현하지 않습니다.
기존 CAN Monitor / Signals 탭과 CLI를 유지합니다.

표시 후보는 Vehicle Speed / Motor RPM / Gear / Brake / Torque이며 **기본 매핑은 없습니다**.
이 이름들은 화면 항목일 뿐 CAN Signal 정의가 아닙니다. 로드한 DBC의 exact Message,
Signal과 실제 Channel을 사용자가 선택해야 합니다. Signal 이름의 유사 문자열, 단일 후보,
동일 이름의 첫 Message를 자동 선택하지 않습니다.

1. **Select DBC...**로 파일을 명시적으로 로드하고 Vehicle Status 탭을 엽니다.
2. **Display item**, **Channel**, **DBC Message**, **Exact Signal**을 선택합니다.
   Message 목록은 로드한 DBC의 실제 CAN ID/STD·EXT 속성을 함께 표시합니다.
   Signal의 Unit/comment를 읽고 의미와 출처를 확인하세요. 요청 토크/적용 토크,
   Motor 직접 값/Gateway 전달 값은 출처를 구분해야 합니다.
3. **선택 출처/표시 의미 확인**을 체크하고 **Apply mapping**을 누릅니다.
   이는 진단 도구 내부 표시 설정이며 팀 Interface 승인이 아닙니다.
   Message/Signal/Channel 변경 시 이전 확인은 해제됩니다.
4. 표에서 Source Message.Signal, 타입을 포함한 Channel, Value, Unit,
   원래 RX Last Update, Age, State와 상세 이유를 확인합니다.
   긴 출처/오류는 셀 tooltip으로 전체 내용을 볼 수 있습니다.
5. **Remove mapping**은 해당 표시 연결만 제거합니다. 정상 수신 Cache는 수정하지 않습니다.

Channel은 문자열/정수/None을 구분합니다. None은 명시적으로 선택한 unknown backend
channel이며 모든 Channel을 뜻하지 않습니다. 기본 선택은 비어 있고, 기존 DEMO 채널과
실제로 관찰된 Channel만 선택 목록에 제공합니다. 목록은 GUI 자원 제한인 128개까지이며
물리 CAN 채널 수를 정의하지 않습니다. 같은 Signal 이름도 Message/Channel이 다르면
값을 합치지 않습니다. 매핑은 메모리의 고정 6개 표시 항목 안에서만 관리합니다.

| State | 의미 |
| --- | --- |
| No DBC | 파일 미로드/로드 실패; Value는 No Data |
| Not Defined | 사용자가 지정한 exact Message/Signal이 현재 DBC에 없음 |
| No Data | 완전한 매핑은 있으나 성공 RX Cache 값이 없음 |
| Valid | 마지막 Decode 성공 RX 값이 존재함; ECU Health/물리값 유효성 판정이 아님 |
| Decode Error | 해당 Channel/Message의 최신 처리 시도 실패; 마지막 정상 RX 값/시각은 유지 |
| Ambiguous | 미매핑, Message/Channel 미선택, 의미 미확인 또는 동일 이름의 대상 불명확 |

따라서 DBC 로드 후 **미매핑 후보는 Ambiguous**, 출처를 명시한 뒤 아직 수신하지 않은
항목은 **No Data**입니다. 없는 신호를 Vehicle 이름과 비슷한 다른 신호로 대체하지 않습니다.
정의가 없는 exact 이름은 Not Defined로 표시합니다.
Age는 기존 Cache API에 DEMO RX와 같은 PC wall clock을 전달해 계산합니다.
Timestamp 미제공/clock 역행은 unknown이며, 정지 후에도 Age가 갱신됩니다.
Age가 커져도 값을 삭제하거나 Healthy/Offline/Fault를 선언하지 않습니다.
TX 성공은 RX 값을 만들지 않으며 최신 TX 여부를 상세 이유에 구분합니다.
Unknown/Error frame은 기존 Raw 정책을 유지하며 추정 Vehicle 값을 생성하지 않습니다.

기존 **Clear**는 Raw 표시/계수를 초기화하고 같은 DBC session의 Vehicle 매핑/정상 Cache는
보존합니다. Start/Stop도 같은 DBC session입니다.
**DBC 교체 시도(성공/실패 포함)**는 기존 새 Cache 계약과 함께 Vehicle 사용자 매핑과
편집기 선택을 초기화합니다. 새 파일의 데이터를 이전 출처로 표시하지 않습니다.
파일 선택 취소는 기존 세션을 유지합니다. 수신 중 파일 교체 제한은 Phase 3C와 동일합니다.
사용자 매핑 저장/자동 복구, 실제 backend 재연결 정책은 아직 구현하지 않았습니다.

Cache 값은 마지막으로 정상 수신·해석한 관찰값입니다. Stop/Clear 후에도 값과 원래 수신 시각을
유지하므로 Age는 계속 증가하는 것이 정상입니다. 새 정상 RX를 받으면 Last Update가 바뀌고
Age가 다시 작은 값으로 갱신됩니다. Clear로 Cache/시각을 수신 없이 초기화하지 않습니다.

### DEMO 검증과 실제 차량 의미의 구분

기존 `tests/fixtures/test_only.dbc`에는 실제 Speed/RPM 신호가 없습니다.
Fixture를 확장하거나 합성 Measurement를 차량 속도/RPM으로 기본 연결하지 않았습니다.
화면/Cache 검증에는 **Display item=DBC Observation**, Channel=`DEMO/TEST ONLY`,
Message=`TestOnlySample`, Signal=`Measurement`를 직접 선택합니다.
확인 체크 후 Apply mapping → Start를 누르면 **-10.0 / test_unit**이 표시됩니다.
이 값은 기존 합성 테스트 벡터이며 실제 차량 측정이 아닙니다.

실제 Repository의 DBC는 review-ready 제안본이고 메시지 정의서의 관련 Signal도
상대 담당자 리뷰가 필요합니다. Vehicle_Status.Speed는 Gateway 가상값이며, RPM/Gear/Brake는
여러 Message에 존재하고 TorqueRequest/TorqueApplied는 역할이 다릅니다.
이 조사 결과를 승인된 Production 매핑으로 내장하지 않았습니다.
DBC/Matrix/Message Definition 정합성 및 실제 차량 의미 검증은 후속 리뷰가 필요합니다.

패키지 폴더에서:
```powershell
New-Item -ItemType Directory -Force .test-tmp | Out-Null
$vehicle_temp = '.test-tmp/vehicle-' + [guid]::NewGuid().ToString('N')
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $vehicle_temp
.\.venv\Scripts\python.exe tests/gui_vehicle_native_smoke.py --dbc tests/fixtures/test_only.dbc --screenshot .test-tmp/vehicle-native.png
```

최종 전체 **239 passed**: 기존 201개 + 신규 38개.
모델 테스트는 Qt 독립, 화면 테스트는 Mock/offscreen, native smoke는 실제 Windows 창을 사용합니다.
사람의 수동 확인은 VERIFICATION에서 자동 검증과 구분합니다.
팀 고정 버전 **미확정**, 담당자 코드 리뷰 **NOT VERIFIED**,
CANable/ECU/실제 Vehicle 값 **NOT VERIFIED**. Git 업로드는 이번 작업에 포함하지 않습니다.

추후 Commit 후보: `[feat][YYYYMMDD][권도형] add vehicle status GUI` (실행하지 않음).

## Phase 3D-2 — ECU Health Observation / CAN Message Statistics

ECU Health Observation 탭은 **PC Tool의 관측 상태**를 표시합니다.
**Observed = 선택한 출처의 처리된 CAN RX가 존재함**이며 Healthy/Online, 실제 ECU 정상,
LIN 수신, Fault 전파 성공 또는 Recovery 완료를 보장하지 않습니다.
Age는 원래 RX Timestamp 이후 경과 시간이며 Offline/Timeout/Fault 임계값은 없습니다.

### 실행과 명시적 매핑

기존 GUI 설치/실행 방식과 CLI monitor/log/send/decode/encode는 유지합니다.

```powershell
.\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pc_diagnostic.gui
```

1. Select DBC로 원하는 파일을 직접 선택합니다. 자동 Production DBC 로드/기본 매핑은 없습니다.
2. ECU Health Observation에서 ECU / Fault target, Channel, 정확한 DBC Message를 선택합니다.
   ID와 STD/EXT는 선택한 실제 DBC 정의에서 가져와 검증합니다.
3. Door/Light/Window는 **개별 Signal**도 선택합니다. Body_Status 전체 수신만으로 세 ECU를
   관측 완료/정상으로 표시하지 않습니다. 개별 Signal이 없으면 Not Available입니다.
4. 출처/표시 목적을 확인하고 Apply mapping을 누릅니다.
   체크박스는 진단 도구 내부 설정 확인이며 팀 Interface 승인이 아닙니다.
   Source 변경 시 다시 확인해야 합니다.
5. Start를 누르고 ECU Dashboard / CAN Message Statistics / Fault Observation을 확인합니다.

Gateway/VCU/Motor/Cluster는 CAN 직접 관측 카드, Door/Light/Window는 Gateway 경유 CAN 관측 카드입니다.
카드 이름은 프로젝트 구성요소 목록이며 어떤 Message를 그 ECU에 자동 연결하지 않습니다.
Message 송신자 정보는 DBC metadata로 보여주며 CAN ID만으로 물리 송신 ECU를 식별/인증하지 않습니다.
같은 Channel/Message/개별 Signal을 여러 ECU에 연결하면 Ambiguous로 표시합니다.
동일 Message 안의 서로 다른 개별 LIN Signal은 분리해서 선택할 수 있습니다.
Channel은 None/정수 0/문자열 '0'을 구분합니다.

| 카드 상태 | 의미 |
| --- | --- |
| Not Configured | 사용자 매핑 없음 |
| No DBC | 선택한 출처를 검사할 DBC 미로드 |
| Not Defined | 정확한 Message/Signal 정의 없음 |
| Ambiguous | 선택/확인 미완료, ID/format 불일치, 중복 출처/Signal |
| Not Available | LIN ECU의 개별 Signal 미선택 |
| No Data | 해당 구간에 처리된 RX가 없거나 개별 Signal이 최신 mux 응답에 없음 |
| Observed | 해당 출처 RX 관측 사실; ECU Health 판정 아님 |
| Decode Error | 해당 출처 최신 처리 실패; Raw Monitor는 프레임을 보존 |

미수신/시각 미제공/clock 역행은 unknown으로 표시하며 시간을 합성하지 않습니다.
Count는 그 Source Message의 **처리된 RX 수**이며 개별 Signal 업데이트 횟수 또는 전체 Bus 수신량이 아닙니다.

### CAN Message Statistics / 자원 상한

- 키: Raw Channel + CAN ID + STD/EXT + ERROR/RTR 속성. TX는 RX 통계에서 제외하고 별도 계수합니다.
- DLC는 최신 실제 Raw DLC, First Seen/Last Seen은 첫/마지막 처리 RX의 원래 Timestamp입니다.
  시각이 역행해도 도착 순서를 바꾸지 않습니다.
- 현재 DBC에서 정의를 찾을 수 있으면 Message Name을 표시합니다.
  미로드/Unknown은 Unknown / Undefined, Error Frame ID는 backend mask라 DBC 조회하지 않습니다.
- 저장은 최대 **512개 키**입니다. 기존 키의 계수는 유지하고 상한 도달 후 새로운 키 프레임을 제외합니다.
  Capacity excluded frames가 그 제외 수입니다. 항목 자동 eviction/전체 수신량 복원은 하지 않습니다.
- 화면은 기존 **512 Buffer / 100 batch / Raw 500행**의 처리 결과만 받습니다.
  Buffer dropped, Pending, Raw/Decode processed, Processed RX, Ignored TX,
  Capacity excluded frames를 구분하여 표시합니다.
  Buffer received는 Clear 이후, 새 통계는 Clear/DBC Reload 이후의 구간입니다.
- **누락 후 No Data는 실제 ECU 무수신/Offline의 증거가 아닙니다.**
  버퍼에서 제외된 Raw 프레임은 새 통계/Decode/Cache에 입력하지 않습니다.
- Channel 선택 목록은 최대 128개, Fault Signal 표는 최대 64행입니다.
  Fault 표 생략 수는 표시합니다. 이는 PC 자원 설정이며 통신/Fault 규격이 아닙니다.

### Fault 읽기 전용 관측

Fault Observation target에 사용자가 DBC Message를 명시적으로 선택합니다.
Fault_Status를 자동 검색/연결하거나 Fault Code를 만들어 해석하지 않습니다.
선택된 메시지의 RX 시각/Count/Source와 **기존 Decode 결과**의 Signal 값·Unit·DBC Choice를 표시합니다.
FaultCode/ECUOffline/RecoveryState 등이 선택한 DBC에 있으면 그대로 표시합니다.
Decode 실패 시 실패 프레임 시각/상태와 마지막 정상 decoded 값의 시각을 분리합니다.
PC에서 수신한 이벤트는 Cluster 수신, 실제 고장, Recovery 성공의 증거가 아닙니다.
Fault Injection, ECU 제어/실제 CAN 송신, Alive 검사 및 Health 정책은 구현하지 않았습니다.

### Lifecycle와 기존 화면

- Start/Stop: Worker 계약 유지, Count/마지막 관측과 사용자 매핑 유지, Stop 후 Age는 계속 증가합니다.
- Clear: Raw/표시 카운터와 새 ECU/Fault 관측·통계 구간을 초기화합니다.
  새 화면은 No Data로 돌아가고 마지막 Fault 표도 비웁니다.
  **사용자 매핑과 기존 Signal Cache/Vehicle 마지막 정상값은 보존**합니다.
  Clear는 수신 중단이 아니며 활성 Worker의 다음 RX부터 다시 집계합니다.
- DBC Reload 성공/실패: 기존 계약대로 새 DecodeSession/Cache 사용.
  새 ECU/Fault 매핑, 편집기 확인, 관측·통계도 초기화합니다.
  과거 Raw 행을 새 관측 구간으로 재집계하지 않습니다.
- 종료: 기존 Worker의 취소/유한 wait 완료 후 새 화면 갱신과 입력을 차단합니다.
  수신은 별도 Worker, UI와 새 관측 모델은 메인 스레드에서만 처리합니다.

### Mock 검증 및 한계

기존 `tests/fixtures/test_only.dbc`를 수정 없이 재사용했습니다.
VCU 카드에 TestOnlySample을 수동 연결하는 것은 **화면 검증용 테스트 출처**이며 VCU 응답이 아닙니다.
Fault target에 같은 합성 메시지를 선택하면 Measurement=-10.0/test_unit,
Mode=1/DBC Choice=ONE 등의 TEST ONLY 값이 보입니다. 실제 Fault Code가 아닙니다.
Production Fixture, Signal/ID/Enum/Invalid/Alive/Timeout/정책 및 기본 매핑은 추가하지 않았습니다.

관련 정의서는 Gateway_Status(GatewayAlive/QueueUsage), Fault_Status(FaultCode/ECUOffline/
RecoveryState/SystemState)를 기록하지만 상대 담당자 리뷰가 필요합니다.
review-ready DBC는 Interface 승인 완료가 아닙니다. 기존 IFC-REV-006의 GatewayAlive
정상 sequence/Invalid 충돌과 IFC-REV-008의 Receiver 범위 질문은 그대로 Open입니다.

```powershell
# tools/diagnostic_GUI 위치에서 매회 새 테스트 전용 폴더 사용
$test_root = Join-Path '.test-tmp' ('phase3d2-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $test_root | Out-Null
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp (Join-Path $test_root 'pytest')
.\.venv\Scripts\python.exe tests/gui_ecu_native_smoke.py --dbc tests/fixtures/test_only.dbc --screenshot-prefix (Join-Path $test_root 'ecu-native')
```

이번 실제 결과: **286 passed** = 기존 239 + 신규 47(모델 34, GUI 13).
Windows Native ECU/Vehicle Smoke 통과. 자동 테스트와 사람 수동 확인은 VERIFICATION에서 구분합니다.
팀 고정 라이브러리 버전 미확정, 담당자 코드 리뷰 NOT VERIFIED,
Production 의미·출처 및 실제 Fault 전파 검토 필요, CANable/ECU Hardware NOT VERIFIED.
매핑 영구 저장, 실제 GUI backend, Fault Injection/제어/Health 판정은 후속 범위입니다.
Commit 후보만 제시: `[feat][YYYYMMDD][권도형] add ECU observation and CAN statistics GUI`.
이번 작업에서는 Git add/Commit/Push/PR/Merge를 실행하지 않습니다.

## Phase 3E — CAN Logging GUI

Logging 탭은 기존 CLI `RawCanLogger`로 Mock RawCanFrame을 CSV/JSONL에 기록합니다.
GUI/Receiver 시작만으로는 파일을 만들지 않습니다. **Mock / DEMO / TEST ONLY**이며
실제 CANable/ECU 검증 또는 무손실 저장·Hardware 성능·KPI 보장이 아닙니다.

### 사용 방법

1. 기존 방식으로 `python -m pc_diagnostic.gui` 또는 `can-diag-gui.exe` 실행.
2. Logging 탭에서 JSONL/CSV를 선택하고 **Select output file...**로 새 파일 경로를 직접 선택.
   파일 확장자로 형식을 자동 추론하거나 원본 경로를 변경하지 않습니다.
3. 상단 **Start**로 CAN Receiver 실행. 이때 Logging은 자동 시작되지 않습니다.
4. **Start Logging**을 눌러 기록 시작. 파일 opening 중에는 별도 안내와 written=0을 표시합니다.
5. **Stop Logging**은 기록 admission을 닫고 이미 받은 Queue를 drain한 뒤 flush/close를 완료합니다.
   Receiver는 계속 동작합니다. 상단 CAN **Stop**은 Logging도 seal/drain하게 합니다.
6. 상태·파일명·성공 기록 Count·Queue Drop·실패/미확인·pending/in-flight·마지막 오류를 확인합니다.
   새 기록은 새 경로를 선택한 뒤 시작합니다.

상태: Idle / Recording / Stopping / Stopped / Error.
파일 I/O는 Session writer가 소유하며 UI와 Receiver는 직접 파일을 열거나 쓰지 않습니다.
기록 중에는 형식/경로 변경 및 중복 Start를 차단합니다.
GUI는 파일 권한 변경, 상위 디렉터리 생성, 기존 파일 삭제를 자동 수행하지 않습니다.

### 기존 CLI 파일 계약

`logger.py`는 수정하지 않았습니다. 같은 JSONL/CSV schema, 원래 Raw ID/DLC/DATA,
STD/EXT/RTR/ERROR, Channel, Timestamp, RX/TX 필드를 그대로 직렬화합니다.
Timestamp는 기존 초 단위 값이며 미제공 값을 보정/합성하지 않습니다.
CSV header/null/bool, JSONL hex/data와 FIFO 순서도 기존 CLI와 같습니다.
JSONL은 기존 `read_jsonl`로 읽을 수 있으며 CSV 입력/Replay는 구현하지 않습니다.
Decoded Signal/Unit/quality나 핸드북의 decoded export schema는 Raw 파일에 추가하지 않습니다.

기존 Logger의 `open(..., "x")` 정책을 그대로 사용합니다.
**덮어쓰기·Append 미지원**입니다. 이미 존재하는 빈 파일도 Error로 거부합니다.
선택 Dialog에서 기존 파일을 지정해도 overwrite 승인을 요청하거나 덮어쓰지 않습니다.
파일 오류 이후 파일이 남아 있으면 부분 기록일 수 있으므로 검토하고 새 이름으로 재시작하세요.
자동 삭제/재시도/임의 파일 복구는 하지 않습니다.

### Queue / Count / Drop

- Receiver는 표시 Buffer에 넣기 전에 **동일 immutable RawCanFrame**을 Logging Session에 전달합니다.
  표시 Buffer Drop만으로 파일 손실을 단정하지 않습니다.
- Logging Queue는 최대 **512 pending + 1 in-flight**입니다. 초과하면 가장 새 입력을 제외하고
  `Queue dropped`를 올립니다. FIFO 기존 대상은 유지합니다.
- `Receiver frames during this Logging session`은 Recording admission 구간의 입력 수입니다.
  Recording 이전/Stop 이후 프레임은 이번 파일의 대상이 아니므로 이 수에 포함하지 않습니다.
- `Logged`는 기존 Logger.write 및 그 안의 flush가 **모두 반환한** 프레임 수입니다.
  실패한 write/flush를 성공으로 세지 않습니다.
- `Failed/unconfirmed`는 실패한 in-flight 및 미처리 Queue 대상입니다.
  실패 프레임은 실제 파일에 일부 또는 전부 존재할 수도 있어 정확한 누락 수로 단정하지 않습니다.
- pending/in-flight도 별도 표시합니다. 정상 종료 후
  received = logged + queue_dropped + failed/unconfirmed입니다.
- 상단 Receiver received/GUI processed/Buffer dropped는 **Clear 이후** 구간,
  Logging 계수는 **Logging Start 이후** 구간입니다. 표시/파일의 수가 같을 필요는 없습니다.
- Queue Drop/오류가 있으면 INCOMPLETE 경고를 표시하며 전체 무손실 capture 성공으로 보고하지 않습니다.

파일은 기존 Logger처럼 프레임마다 flush하지만 fsync/전원 차단 내구성, 파일 rotation,
디스크 용량 보장, 고속 Hardware 무손실은 미검증·범위 밖입니다.
출력 파일은 Source와 분리해 보관하세요. 이번 테스트의 전용 `.test-tmp/`만 Git 제외를 확인했습니다.

### Stop / Clear / Reload / Close와 오류

- Clear/DBC Reload는 Raw 화면/Decode 관측 계약을 유지하며 **Logging 파일/계수는 초기화하지 않습니다**.
  파일에는 DBC가 아니라 Raw 프레임만 저장합니다.
- Stop Logging/CAN Stop은 새 대상 접수를 닫고 Queue의 기존 대상을 완료한 뒤 파일을 닫습니다.
  Receiver 오류에도 이미 접수한 파일 Queue를 drain합니다.
- Open/권한/파일 잠금/직렬화/write/flush/close 오류는 Error와 원인으로 표시합니다.
  오류 후에도 CAN Monitor/Decode는 유지되며 새 경로로 다음 Session을 시작할 수 있습니다.
- GUI 종료는 CAN Worker와 파일 writer 종료를 확인합니다.
  파일 I/O가 종료 제한 안에 끝나지 않으면 강제 종료하지 않고 창과 worker 참조를 유지합니다.
- **종료 drain 중 기록 오류가 있으면 첫 Close에서 창을 유지하고 오류를 표시합니다.**
  부분 파일을 확인한 뒤 다시 Close하면 종료할 수 있습니다.
  새 Session의 오류는 다시 표시합니다. 재시도 Close는 파일 정상 저장 인증이 아닙니다.
- 내부 generation은 오류 알림을 Session별로 구분하는 GUI metadata이며 CSV/JSONL 필드가 아닙니다.

### 검증

```powershell
# tools/diagnostic_GUI 위치, 실행마다 새 폴더 생성
$test_root = Join-Path '.test-tmp' ('phase3e-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $test_root | Out-Null
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp (Join-Path $test_root 'pytest')
.\.venv\Scripts\python.exe tests/gui_logging_native_smoke.py --output-dir $test_root
```

전체 **321 passed** = 기존 286 + 신규 35(Session 21 / GUI 14).
CSV/JSONL 출력의 기존 CLI와 byte 일치, Queue/Count/오류/반복/종료 검증 완료.
Logging 및 기존 Raw/Decode/Vehicle/ECU Windows Native Smoke 통과.
**Logging 사용자 수동 확인 NOT VERIFIED**, Hardware NOT VERIFIED,
팀 고정 버전 미확정, 담당자 코드 리뷰 NOT VERIFIED.
확인된 종료 오류와 후속 질문은 VERIFICATION의 Jira 등록용 초안에 기록했습니다.
이번 작업에서 Git add/Commit/Push/PR/Merge 미실행.
향후 Commit 후보: `[feat][YYYYMMDD][권도형] add CAN logging GUI`.
