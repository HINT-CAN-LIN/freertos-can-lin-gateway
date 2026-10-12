# PC Diagnostic Tool — Raw CAN / DBC / Signal State Cache

Classic CAN raw 프레임을 수신·표시·기록·송신하는 독립 Python 패키지입니다.
Gateway CAN ID, message별 DLC, Signal bit layout/scale/enum은 정의하지 않습니다.
Phase 1 Raw CAN 기능 위에 명시적으로 지정한 DBC의 Decode/Encode와 PC 관찰용 State Cache를 제공합니다.
Phase 3B는 PySide6 Mock 전용 Raw CAN GUI를 제공합니다.
LIN, GUI의 DBC Decode/Logging/송신, ECU Health/Fault 정책, Fault Injection, KPI, 주기 송신, CAN FD는 미구현입니다.
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

CLI는 그대로 유지하며 GUI는 Raw CAN 관찰만 제공합니다. GUI에서 실제 CAN 연결이나
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
  채널은 `DEMO/TEST ONLY`입니다. GUI는 DBC를 로드하지 않고 Signal을 해석하지 않습니다.

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

미구현: GUI DBC Decode/State Cache 화면, GUI 파일 Logging, Filter, Replay, 실제 CAN
backend, 운전자 입력/송신, Health/Fault 판정, Fault Injection, standalone 배포.
기존 CLI의 monitor/log/send/decode/encode는 유지하며 실제 버스 시험은 이번 작업에
포함하지 않습니다. 생산용 Interface 변경은 **상대 담당자 리뷰 필요**입니다.

Thread lifecycle 참고: [Qt QThread 공식 문서](https://doc.qt.io/qtforpython-6.10/PySide6/QtCore/QThread.html),
[Qt 객체와 스레드](https://doc.qt.io/qtforpython-6.10/overviews/qtdoc-threads-qobject.html).


P2/P3 수정 검증 결과: 기존 CLI 140개 + GUI/버퍼/안내 30개, 전체 **170 passed**.
실제 Windows pythonw 오류 안내창과 정상 GUI 진입점을 별도로 확인했습니다.
현재 설치/팀 승인 상태와 검증 상세는 `VERIFICATION.md`의 최신 절을 참조하세요.
Windows API 근거: [Microsoft MessageBoxW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messageboxw).
