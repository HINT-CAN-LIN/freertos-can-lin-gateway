# PC Diagnostic Tool — Raw CAN / DBC / Signal State Cache

Classic CAN raw 프레임을 수신·표시·기록·송신하는 독립 Python 패키지입니다.
Gateway CAN ID, message별 DLC, Signal bit layout/scale/enum은 정의하지 않습니다.
Phase 1 Raw CAN 기능 위에 명시적으로 지정한 DBC의 Decode/Encode와 PC 관찰용 State Cache를 제공합니다.
Phase 3B는 Mock Raw GUI, Phase 3C는 명시적 DBC Decode/Cache, Phase 3D-1은 사용자 매핑 Vehicle Status를 제공합니다.
Phase 3D-2는 명시적 ECU/Fault 관측과 처리된 Raw RX 통계를 제공합니다. Health/Fault 판정은 하지 않습니다.
Phase 3E는 Raw Logging GUI, Phase 3F는 Mock/Live CAN 연결, Phase 3G는 명시적 DBC Signal Graph를 제공합니다. 아래 이전 Phase 절은 당시 기록입니다.
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

## Phase 3F — Mock / Live CAN Connection GUI

하나의 GUI에서 입력 Source만 선택합니다. 기본은 기존 **Mock / DEMO / TEST ONLY**이며,
Live는 기존 CLI의 `PythonCanInterface`를 재사용합니다. Live GUI에는 CAN application TX 기능이 없습니다.
아래 이전 Phase의 “GUI backend 미구현” 설명은 당시 기록입니다.

### 실행과 연결 설정

Repository root에서 기존 `python -m pc_diagnostic.gui` 또는 `can-diag-gui.exe` 실행 방법을 사용합니다.
필요한 선택적 의존성은 PC Tool 디렉터리의 현재 가상환경에 **사용자 승인 후** 설치하세요.
Phase 3F 작업에서는 패키지·USB driver·CANable firmware를 설치하거나 변경하지 않았습니다.

- Mode=Mock: 이전 DEMO 생성/Start/Stop/Clear 기능을 유지합니다. 실제 ECU 응답이 아닙니다.
- Mode=Live: Backend, Channel, Bitrate를 명시적으로 입력한 후 Start합니다.
- Backend=`slcan`: 실제 장치의 serial port 문자열을 입력합니다. 예: 사용자가 확인한 COM port.
  `COM7`을 기본 장치로 가정하지 않습니다. 필요하면 `port@baudrate`로 serial baudrate를 지정할 수 있습니다.
- Backend=`gs_usb`: 사용자가 확인한 0 이상 device index를 입력합니다. 문자열 channel과 구분합니다.
  이 GUI MVP는 index 선택을 제공하며 CLI의 문자열 channel 지원은 변경하지 않습니다.
- Bitrate 초기 표시값 `500000`은 분석한 Cluster commit `4633779`의 Classic CAN 설정에 따른
  **통합 시험 기준**입니다. 실제 장치 탐색이나 팀 Interface 승인 결과가 아닙니다.
- 설정 선택만으로 Connected가 되지 않습니다. 실제 Worker open 완료 뒤 Connected를 표시하며,
  무수신은 No Data입니다. Connected는 ECU Online/Healthy 또는 배선 검증 결과가 아닙니다.

SLCAN은 serial firmware와 Windows port/driver 확인 및 `pyserial`이 필요합니다.
candleLight/gs_usb 계열은 호환 firmware, `gs-usb`, `pyusb`, OS USB backend/driver 준비가 필요합니다.
어느 backend가 현재 실제 CANable에서 동작하는지는 **미확정**입니다.
기존 `can` extra만으로 backend별 optional dependency가 모두 설치되는 것은 아닙니다.

승인 후 선택 설치 예시 (이번 작업에서 실행하지 않음):

```powershell
# tools/diagnostic_GUI 디렉터리의 활성 가상환경에서 장치에 맞는 한 가지 경로 선택
python -m pip install -e ".[gui,dbc,slcan]"
python -m pip install -e ".[gui,dbc,gs-usb]"
```

근거: [python-can 4.6.1 SLCAN](https://python-can.readthedocs.io/en/v4.6.1/interfaces/slcan.html),
[gs_usb](https://python-can.readthedocs.io/en/v4.6.1/interfaces/gs_usb.html).
Missing dependency는 설치 명령과 함께 GUI 오류 영역에 표시합니다. 자동 설치/Mock fallback은 없습니다.

### 수신 전용과 공통 파이프라인

`Mock/Live → RawCanFrame → Logging Queue + GUI FrameBuffer → DecodeSession → Cache/Vehicle/ECU/Fault`

Live Worker는 `recv(timeout)`만 사용하며 `inject`, DEMO generator, `send`를 호출하지 않습니다.
Raw ID/DLC/DATA/STD·EXT/Channel/Timestamp/RX·TX는 기존 Adapter가 반환한 그대로 보존합니다.
기존 CLI Sender는 변경하지 않았습니다. 애플리케이션 TX 미호출은 **hardware listen-only**가 아닙니다.
현재 Adapter는 listen-only 설정을 요청하지 않으며, controller ACK/error signaling 등 물리 무송신을 보장하지 않습니다.

프레임별 Qt Signal을 만들지 않고 기존 유한 표시 Buffer와 제한된 batch/timer 갱신을 유지합니다.
Logger는 표시 drop 이전의 동일 Raw 객체를 독립 Logging Queue에 받습니다.
CSV/JSONL schema, exclusive-create, no overwrite/append, write/flush/close 및 Drop 계수 계약은 동일합니다.
로그 파일에 새 Source 필드를 추가하지 않습니다. 파일 출처는 GUI의 기록 시작 Source 표시 및 별도 시험 Evidence로 관리하세요.
CSV/JSONL의 byte 호환성은 Fake Live 자동 시험으로 확인했고 실제 버스의 무손실 기록 보장은 아닙니다.

### Source 전환·Cache·출처 정책

Mode/Backend/Channel/Bitrate는 연결 중, 수신 중, Stop/Transport 해제 중, 잔여 Buffer 처리 중,
Logging writer drain 중에는 잠깁니다. 실제 Receiver/Writer 종료와 잔여 표시 처리 완료 후에만 변경할 수 있습니다.

- **같은 Source의 Stop/Start/Clear:** 기존 계약 유지. Stop 후 마지막 성공 Cache 값과 Age를 유지하며,
  Clear는 Raw 표시 및 ECU/통계 관측 구간을 비웁니다. Logging 중 Clear는 파일 기록을 초기화하지 않습니다.
- **Source 설정 변경:** 새 관측 Session. Raw/Buffer/계수, Cache, latest attempt, Vehicle/ECU/Fault 매핑과
  통계를 초기화합니다. 사용자가 명시적으로 로드한 DBC 정의는 유지하지만 매핑은 다시 확인해야 합니다.
- **DBC Reload:** 기존 새 DBC Session 정책 유지. 수신 및 잔여 처리 중 Reload는 차단됩니다.
- Monitor/Decode/Cache, Vehicle, ECU/Statistics/Fault, Logging은 현재 Source를 표시합니다.
  Live에는 DEMO channel 기본 후보를 넣지 않고 실제 Raw에서 관찰한 channel만 추가합니다.
- 완료된 파일의 **File source**는 기록 시작 Source를 유지하므로 이후 Mode 변경으로 과거 파일을 재분류하지 않습니다.
- 주입된 시험 backend는 모든 주요 화면에 **Injected backend / TEST ONLY**로 표시합니다.
  정상 프로그램 실행에는 Fake backend 자동 선택 기능이 없습니다.
- Age는 backend Timestamp와 동일한 시간 기준에서만 의미가 있습니다. timestamp 미제공은 unknown이며,
  실제 backend clock/USB timestamp 정확도는 이번 Fake 시험으로 검증하지 않습니다.
  Age만으로 Fault/Offline을 판정하지 않습니다.

### 오류와 종료

설정 오류, 필수 모듈 미설치, open/receive/shutdown 실패는 원인과 함께 Error로 표시합니다.
Live 실패 후 자동 Mock 전환·자동 재연결은 없습니다. 정상 해제 후 사용자가 Start로 재시도합니다.
Stop은 취소 요청이며 Worker가 transport 생성부터 shutdown까지 소유합니다.

Backend open/recv/shutdown 자체가 막히면 강제 QThread terminate하지 않습니다.
Close는 기존 유한 대기 후 창을 유지하고 오류를 표시합니다. open 중 Stop 요청은 open 완료 직후 확인하여
recv 전에 해제합니다. 실제 OS/driver의 blocking 호출을 강제 취소하거나 종료 시간을 보장하지 않습니다.
Live shutdown 실패는 재연결/Source 변경을 차단합니다. Close 중 해제 오류는 첫 Close에서 창을 유지해 안내하고,
다음 Close로 종료할 수 있지만 해제 성공으로 기록하지 않습니다.

### Fake Live 검증과 남은 범위

`tests/fake_live.py`는 기존 `tests/fixtures/test_only.dbc`와 DEMO raw payload를 재사용합니다.
Production DBC, CAN ID, Signal/Layout, Timeout/Fault policy는 추가·수정하지 않았습니다.
자동화는 Fake Live와 offscreen Qt를 사용하며 Native Smoke는 실제 Windows 창에서 Fake Live로 실행합니다.

```powershell
python -m pytest -q -p no:cacheprovider --basetemp $newWritableTestTemp
python tests/gui_live_native_smoke.py --output-dir $newExistingEvidenceDirectory
```

시험에는 매번 새 쓰기 가능 Temp/Evidence 경로를 사용하고 기존 Capture를 덮어쓰지 마세요.
실제 결과는 VERIFICATION의 Phase 3F 절을 참조하세요.

미구현/미검증: 실제 CANable firmware/driver 연결, 실제 Cluster 외부 CAN/LCD 비교, hardware listen-only,
자동 재연결, 사용자 매핑 영구 저장, CAN FD, GUI TX/운전자 입력, Fault 판정·전파 검증.
**Hardware 및 이번 사람 수동 GUI 확인 NOT VERIFIED**, 팀 고정 버전 미확정, 담당자 코드 리뷰 NOT VERIFIED.
Commit/Push/PR/Merge는 수행하지 않습니다.

## Phase 3G — Real-time Signal Graph

**Signal Graph**는 단일 DBC Signal의 기존 per-frame Decode 결과를 표시합니다.
기존 Mock/Live 연결, Raw/Signal/Cache, Vehicle/ECU/Fault 관측, Logging과 같은 수신 파이프라인을 사용하며,
Graph에서 Payload를 다시 Decode하거나 Cache의 마지막 값을 timer마다 새 Sample로 복사하지 않습니다.
기존 탭 위치는 유지하고 마지막에 Graph 탭을 추가했습니다.

### 사용법과 명시적 선택

1. 기존 방식으로 GUI를 실행하고 Mock 또는 사용자가 확인한 Live 설정을 선택합니다.
2. **Select DBC...**에서 DBC를 명시적으로 로드합니다. 기본 Production DBC/Signal 자동 연결은 없습니다.
3. **Signal Graph** 탭에서 **CAN Channel**을 타입까지 확인하여 선택합니다.
   Mock의 DEMO 채널은 TEST ONLY입니다. Live는 실제 Raw에서 관찰한 Channel만 목록에 추가하며,
   None은 unknown Channel의 명시적 선택이고 wildcard가 아닙니다.
4. **Message Name / CAN ID / STD·EXT**와 **Exact Signal**을 선택하고 **Apply signal**을 누릅니다.
   Signal 이름이 다른 Message와 같아도 첫 후보/유사 이름으로 자동 연결하지 않습니다.
   **DBC Unit**은 읽기 전용이며 파일 metadata 그대로 사용합니다. 미정 단위를 임의 생성하지 않습니다.
5. CAN Receiver를 Start하면 선택된 Source/Channel/ID/Format/Message/Signal의 처리된 RX만 Sample로 추가합니다.
   마지막 숫자 관측값·단위·원래 Timestamp·Sample 수와 오류/제외 계수를 표시합니다.

최신 숫자 관측값은 정상 Decode 숫자 기준입니다. 시간축에 넣을 수 없는 Timestamp의 경우
숫자와 원래 Timestamp/unknown은 표시하고, 해당 점은 그래프에 추가하지 않습니다.

### Sample·Timestamp·품질 정책

- Graph Sample에는 Source, DBC/Source session ID, typed Channel, CAN ID, STD/EXT,
  Message/Signal 이름, Unit, Raw Timestamp, 원래 숫자 값과 표시 segment를 보관합니다.
- Sample Buffer는 **1000개**입니다. 초과 시 가장 오래된 Graph 이력만 제외하며 **Graph history omitted**를 증가시킵니다.
  이 수치는 수신 CAN 손실이나 Logging Queue Drop이 아닙니다.
- Graph 렌더링은 별도 Qt timer **200 ms**입니다. CAN 수신/Decode 빈도와 독립적인 GUI 설정이며
  ECU 주기·Fault Timeout·측정 KPI가 아닙니다.
- X축은 첫 **현재 retained Sample의 Raw RX Timestamp**를 0으로 한 경과 초입니다.
  rolling history에서 가장 오래된 점이 제외되면 기준도 이동합니다. 원래 Timestamp는 숫자 표시와 Sample에 유지됩니다.
  backend clock 정확도·실제 수신 시각은 Hardware 검증이 필요합니다.
- 동일 Timestamp의 서로 다른 실제 처리 프레임은 순서대로 보관합니다.
  누락 Timestamp와 마지막 accepted Timestamp보다 역전된 값은 **Unsupported Timestamp**로 표시하고
  별도 제외 계수를 증가시킵니다. PC 현재 시각을 대신 넣거나 Sample을 정렬하지 않습니다.
- 정상 Decode된 유한 int/float만 허용합니다. Text/enum label/bool, NaN/Infinity, 표시 불가능한 숫자는
  **Unsupported Value**로 구분합니다. 현재 codec은 numeric enum을 반환하므로 숫자 enum은 그대로 관측합니다.
  문자열 enum을 임의 숫자로 변환하지 않습니다.
- 기존 DecodedMessage는 비숫자·NaN/Infinity를 upstream에서 거부할 수 있습니다.
  그 경우 Graph는 **Decode Error**이며 Unsupported Value 방어는 경계 모의 테스트로도 검증합니다.
- Decode 실패 시 마지막 정상값을 새 Sample로 추가하지 않습니다. mux frame에 선택 Signal이 없으면 No Data입니다.
  TX echo 및 error-mask ID는 Signal RX Sample로 사용하지 않습니다.
- 오류·Timestamp 제외·GUI Buffer Drop 이후에는 다음 정상점과 이전점을 선으로 연결하지 않습니다.
  선 연결은 관측점의 표시일 뿐 중간 값이 실제 측정됐다는 뜻이 아닙니다.
- Invalid/Reserved 패턴이나 DBC min/max 밖 숫자는 기존 Decode 관측 계약을 따릅니다.
  decoded 값/곡선이 있다고 ECU Healthy·실차 값 유효·Fault 해제라고 판정하지 않습니다.
- Graph 화면의 GUI Buffer dropped는 기존 표시 처리 전 제외량입니다. Graph는 GUI가 실제 처리한 RX만 보므로
  Sample 수는 전체 Bus 수신량이 아닙니다. 실제 CAN 손실률·CPU·Jitter는 측정하지 않았습니다.

### Pause / Resume / Clear / Session

**표시만 Pause**하는 정책을 선택했습니다. CAN Receiver, Decode, Cache, Statistics, Logger와 Graph Sample 수집은
계속합니다. Pause는 곡선 snapshot만 유지하며 최신 숫자/상태/계수는 계속 갱신합니다.
Resume은 현재 유한 Buffer를 표시합니다. 오래 Pause하면 이전 Graph 이력 일부가 상한으로 제외될 수 있고
해당 계수로 확인할 수 있습니다. Sample 수집까지 멈추는 정책은 중간 데이터가 없어지는 단점이 있어 채택하지 않았습니다.

**Clear Graph**는 Sample/곡선/Graph 품질 계수만 비우고 선택은 유지합니다.
Raw Monitor, 성공 Cache, ECU Statistics, Logging과 CAN Worker는 변경하지 않습니다.
Pause 중 Clear하면 곡선은 비어 있고 수집은 계속하며 Resume에서 현재 Buffer를 표시합니다.
기존 상단 Raw Clear는 Graph를 초기화하지 않습니다.

같은 Source의 CAN Start/Stop 반복은 Graph 이력을 유지합니다.
DBC Reload 또는 Mock/Live/Backend/Channel/Bitrate 설정 전환은 기존 session generation 정책을 따라
Graph 데이터·선택·Channel 후보와 paused snapshot을 초기화합니다. 이전 곡선을 새 Source로 표시하지 않습니다.
어떤 timer도 샘플 Timestamp를 새로 합성하지 않습니다.

### 구현·의존성·검증

`ReceiveWorker → 기존 FrameBuffer → DecodeSession.process → FrameObservation → SignalGraphModel → QPainter`

기존 **PySide6 QtGui QPainter**를 사용하여 외부 plotting package를 추가·설치하지 않았습니다.
Graph Model은 Qt 독립이고 Canvas는 유한 snapshot만 표시합니다. UI/그리기는 Qt 메인 스레드에서만 수행하며,
Graph timer는 MainWindow의 정상 Close에서 정리합니다. 기존 Logger/Worker 종료 계약은 유지합니다.
Qt/Python 호환성은 실제 기존 환경에서 검증했고 팀 고정 버전 승인을 의미하지 않습니다.
로컬 PySide6 metadata의 라이선스는 LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only입니다.
배포 라이선스 선택·고지는 팀 배포 검토 항목이며 이번 구현으로 승인 완료를 주장하지 않습니다.

근거: [Qt 6.10 QPainter](https://doc.qt.io/qtforpython-6.10/PySide6/QtGui/QPainter.html),
[Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html).

기존 TEST ONLY DBC로 Mock 및 Fake Live를 검증합니다. 기본 Mock Measurement는 기존 고정 -10.0이므로
시간에 따라 같은 값의 선이 표시됩니다. 변화하는 곡선은 Native 시험의 Fake producer가 기존 TEST ONLY Signal을
기존 DBC Encoder로 생성한 값이며 실제 ECU 데이터가 아닙니다. Production Fixture/Interface는 수정하지 않았습니다.

```powershell
python -m pytest -q tests/test_signal_graph.py tests/test_graph_view.py -p no:cacheprovider --basetemp $newWritableTemp
python tests/gui_graph_native_smoke.py --output-dir $newExistingEvidenceDirectory
```

단일 Signal, 마지막1000개 rolling graph만 제공합니다. 다중 Signal·Graph Export·Cursor/Zoom·영구 선택 저장은 후속 범위입니다.
**Hardware 및 이번 사용자 수동 확인 NOT VERIFIED**, 팀 고정 버전 미확정, 담당자 코드 리뷰 NOT VERIFIED.
실행한 결과는 VERIFICATION의 Phase 3G 절을 참조하세요. Commit/Push/PR/Merge는 이번 작업에서 수행하지 않습니다.


## Phase 3H-1 — Fault Monitor 관측 이력

**Fault Monitor** 탭은 사용자가 명시적으로 연결한 DBC Message/Channel의 처리된 RX를 보관합니다.
기존 ECU Health Observation → Fault Observation의 마지막 정상 Signal 화면은 유지합니다.
실제 ECU Fault 감지·전체 Active Fault 복원·ECU 해제 기능이 아닙니다.
DBC/Signal/Frame/Transport/Logger 계약을 변경하지 않았습니다.

### 사용 방법

1. 기존 GUI에서 Mock 또는 확인한 Live 수신 설정을 선택하고 **Select DBC...**로 파일을 직접 로드합니다.
2. **Fault Monitor**에서 Source Channel과 **Exact DBC Message / ID / Format**을 선택합니다.
3. 출처 확인을 체크하고 **Add observation source**를 누릅니다.
   ID/IDE는 선택한 DBC 정의에서만 가져옵니다. Fault 이름/유사 문자열/0x310을 기본 자동 연결하지 않습니다.
   여러 Message/Channel을 각각 추가할 수 있습니다. 출처 확인은 팀 Interface 승인이 아닙니다.
4. Start 후 Order, RX Run, Raw Timestamp, Source, typed Channel, CAN ID/STD·EXT,
   Message, 실제 FaultCode 값(존재할 때), Decode 상태와 **Status Unknown**을 확인합니다.
5. FaultCode의 정확한 숫자, Channel, Message/ID/Format 및 **Decode Error only**로 필터링합니다.
   필터는 retained history의 조회이며 수신/Decode/Logging에 영향을 주지 않습니다.
   None Channel은 unknown Channel이며 All/wildcard가 아닙니다. 0과 '0'도 구별합니다.
6. 행을 선택하면 Raw DLC/Payload/RTR, DBC/Source session, Receiver run, Timestamp 품질,
   per-frame Signal/Unit/DBC Choice/Error와 별도 상태 해석 단계가 상세에 표시됩니다.
7. **Remove source**는 향후 관측 연결만 제거합니다. 이미 저장한 이력은 유지합니다.
   **Clear History**는 PC 이력/계수만 비우며 ECU Clear, 파일 삭제, CAN TX가 아닙니다.

DBC가 없으면 **No DBC**, 정의/매핑은 있지만 수신 이력이 없으면 **No Data**입니다.
DBC 없이 임의 ID를 Fault Frame으로 분류하지 않고 기존 Raw Monitor 수신은 계속합니다.
선택 Message의 성공 결과는 **Observed**, 실패 결과는 **Decode Error**입니다.
**Fault not observed ≠ No Fault**이며 실제 Fault 상태 해석은 **Status Unknown**입니다.
FaultCode=0, RecoveryState=1, SystemState=NORMAL만으로 전체 Fault가 없거나 해제됐다고 추론하지 않습니다.
DBC Choice ACTIVE/CLEARED/INVALID/NORMAL 문자열은 파일 metadata 그대로 보여줍니다.
Current Fault, Severity, 발생/해제 쌍, Offline bit 판단과 ACTIVE/CLEARED 필터는 구현하지 않았습니다.

### 모델·Buffer·Timestamp·Session

ReceiveWorker → 기존 FrameBuffer → DecodeSession.process → FrameObservation → FaultHistoryModel → FaultMonitorView

- 기존 per-frame Decode 결과와 immutable RawCanFrame만 사용합니다. 재Decode/bit 해석/Cache backfill 없음.
- 기존 Fault Observation의 MessageMapping 검증을 재사용하고 metadata 후보가 여러 개면 Ambiguous로 거부합니다.
- History는 기존 Raw 표 정책과 같은 **500개**입니다. 초과 시 oldest observation을 제거하고
  **Oldest history omitted**를 표시합니다. Source 설정은 별도 PC 로컬 상한 **32개**입니다.
  CAN/LIN 주기, Gateway Queue 크기, Fault Threshold가 아니며 초기값-수정 가능 PC 표시 정책입니다.
- 반복 Frame도 독립 관측으로 보존합니다. Observed count는 처리된 선택 RX 수이며 Fault 발생 횟수/전체 CAN 수신량이 아닙니다.
  History 제거, GUI Buffer drop, Logging Queue drop을 구분합니다. 실제 CAN 유실률/무손실 성능은 미검증입니다.
- Raw Timestamp를 유지합니다. 누락은 unknown/Missing, 직전 동일 출처 관측보다 역전하면 Reversed입니다.
  이력을 삭제하거나 PC 현재 시각으로 대체하지 않습니다. 시간으로 정렬하지 않고 수신 처리 순서로 표시합니다.
  최신 관측 Timestamp는 최근 처리 항목의 Raw 값이며 최대 Timestamp가 아닙니다.
- Mock/Live, Backend/설정 Channel/Bitrate 변경 및 성공·실패한 DBC Reload는 기존 DecodeSession generation에 맞춰
  이력·매핑·필터·상세·채널 후보를 초기화합니다. 과거 결과를 새 DBC로 재해석하지 않습니다.
- 같은 Source의 Stop/Start, Transport 오류 후 재접속은 이력을 유지하되 **RX Run**으로 Start 구간을 구별합니다.
  새 Start 시 이전 Raw backlog가 있으면 그 구간의 RX Run은 **Unknown**입니다.
  FrameObservation에는 transport run ID가 없으므로 원래 run을 추측하지 않습니다.
  Stop 동안 누락된 이벤트를 복원하거나 과거 이력을 현재 ECU 상태라고 주장하지 않습니다.
- Clear History 이후 순서 번호를 재사용하지 않으며 매핑은 유지합니다.
  Clear는 GUI가 처리한 이력을 비우며 처리 대기 프레임이 이후 새 행으로 나타날 수 있습니다.
  상단 Raw Clear는 Fault 이력을 지우지 않지만 기존 계약대로 Raw pending buffer를 비웁니다.
- 추가 Worker/Timer 없이 기존 유한 GUI batch와 main-thread refresh를 재사용합니다.
  revision 변경 때만 bounded QAbstractTableModel snapshot을 갱신합니다.
  수신 중 선택한 Source/상세/스크롤을 유지하고 filter/eviction으로 행이 사라지면 상세를 비웁니다.
  Receiver/Writer 종료 뒤 화면을 닫습니다. Qt 필수 override 명칭은 snake_case의 예외입니다.

사용자 매핑 실패 원인은 **Last mapping error**로 정상 재시도/새 세션까지 보존합니다.
정기 RX refresh가 이 안내를 지우지 않으며 Decode Error/실제 Fault와 구분합니다.
새 Native 시험에서 Writer 종료 flag와 UI Source unlock의 비동기 차이를 재현했습니다.
실제 controls 활성화를 이벤트 조건으로 기다리며 제품의 Source 잠금 정책은 유지합니다.

### 실제 Fault 계약 조사 — 의미 승인과 구분

| 근거 | 실제 확인 내용 / 상태 |
|---|---|
| network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc (본문 VERSION 0.4) | Fault_Status 0x310 STD DLC8, Gateway→Cluster/PC. Signal/Choice는 파일 정의로 확인. proposal 및 counterpart review gate 명시 |
| docs/requirements/02__메시지_정의서_ver1.2.xlsx, CAN_Message_Definition 11/20, CAN_Signal_Definition 26~29 | ID/STD/DLC 및 bit 구성은 DBC와 일치. Team Encoding/FIX와 상대 담당자 리뷰 필요 표기가 함께 있음. 승인 완료 Evidence 미확인 |
| 위 Workbook Value_Table 36~56 / Fault_Timeout_Policy POL-008 | FaultCode 0..6, Reserved7..254, Invalid255. ECUOffline은 4-bit node enum 0..7/Reserved8..14/Invalid15이며 bitmask가 아님. Recovery0=ACTIVE/1=CLEARED, SystemState는 대표 상태. 개별 전이 Event는 결정안/리뷰 대상 |
| docs/archive/initial/FreeRTOS_CAN_LIN_Project_핸드북_kr_초기버전.pdf (본문 Handbook v1.0 pp14,27~28) | Fault_Status Event/전파 역할은 기술. bit layout, 재접속 Replay 세부 승인 근거는 아님 |
| docs/architecture/system/03__CAN-LIN_D07_Fault_Failsafe_설계보고서_v1.0.pdf (본문 v0.9 pp9~10,13~14) | D07-9 per-transition Event 상세가 제안/미확정. 후속 설계와 문서 버전·결정 상태 동기화 검토 필요 |
| network/routing/Gateway_Routing_Table_v0.4_CAN_to_LIN_Decision_Baseline.xlsx, Interface_Ref 28~33 | FaultSource/FaultSeverity/FaultState/FaultRecovery/FaultMultiFault 등이 OPEN. DBC의 ECUOffline/RecoveryState/SystemState와 명칭·상세 불일치. 임의 구현하지 않음 |
| 사용자 Source of Truth: design/Gateway_FreeRTOS_Design_Final_Aligned.xlsx 02_RTOS_Object14 / 03_Health_Fault | ACTIVE/CLEARED 및 FaultManager 책임 기술. Event transport/order/retry/loss/resync는 OPEN/TBD |
| 사용자 Source of Truth: design/gateway-sw-architecture-and-detailed-design_최종본.pdf pp18~19,25,28~30 | per-transition publication은 확정 정책. Node mapping 일부와 ordering/retry/loss/API/측정은 Open/Review/측정 후 확정. 이전 D07-9 미확정과 후속 결정 상태 구분 필요 |
| 사용자 Source of Truth: design/Gateway_Routing_Table_v1.0_최종.xlsx | Fault/Recovery 전파 참조. route에 Review/Needs Review가 남음. 팀 승인 완료로 사용하지 않음 |
| origin/Cluster_ECU 4633779f3f0fe989730181f6e48ef777b041076a, Core/Src/cluster_state.c:97~109, Core/Inc/cluster_state.h:44~49 | STD/DATA/DLC8, code/node 범위 검사, (code,node)별 ACTIVE/CLEARED latch. NONE은 reset-all이 아님. gap_seen/관측 불확실성 보존 |
| origin/Gateway_ECU 542f50a2c3557c4c47dfa4f629be0a2a55150eeb, Core C/H9개 | 조사한 Core에 FaultManager/Fault_Status/RecoveryState/ECUOffline/0x310 publication 구현 근거 없음. E2E Fault 처리 완료 확인 불가 |

Cluster/Gateway 분석은 **로컬 저장 origin 참조 Commit**의 코드이며 이번에 fetch하지 않았습니다.
GitHub 최신 HEAD, Firmware Flash 상태, Runtime 전파는 별도 확인 필요입니다.

수치 정의가 일치하는 부분이 있지만 산출물의 결정 상태/명칭이 모두 동기화된 것은 아닙니다.
따라서 **관측 기능은 구현**, Production 의미 승인·Current Active Fault 재구성·발생/해제 매칭은 **검토 필요/Open**입니다.
PC의 Frame 수신은 Gateway Detection/Action/Recovery/External Propagation DoD 완료의 증거가 아닙니다.

### 검증·미확정·후속 Jira 초안

기존 TEST ONLY DBC/Mock를 그대로 사용합니다. FaultCode/Recovery metadata 시험은 기존 저장소 DBC를
시험자가 명시적으로 읽고 기존 Encoder로 만든 Fake TEST ONLY 수신입니다.
Production DBC 기본 연결, 신규 CAN ID/Signal/Layout/Enum 정의는 없습니다.
CSV/JSONL Raw Logger schema, exclusive-create/flush/close, Queue/Count 계약 및 CLI byte 출력을 유지합니다.
새 Fault 전용 Export는 없습니다. 실제 결과는 VERIFICATION의 Phase3H-1 절에 기록합니다.

    python -m pytest -q tests/test_fault_history.py tests/test_fault_monitor_view.py -p no:cacheprovider --basetemp $newWritableTemp
    python tests/gui_fault_native_smoke.py --output-dir $newExistingEvidenceDirectory

- 확정: 기존 수신/Decode/Cache/Raw Logger 계약, 파일에서 확인한 Raw/metadata, PC 관측과 상태 판정 책임 분리.
- 초기값-수정 가능: PC History500/Source32 및 layout. Gateway Fault 정책과 무관.
- 측정 후 확정: 실제 Timestamp 품질, CANable/Cluster E2E, 고부하·장시간 표시 성능/누락.
- 검토 필요: lifecycle Freeze Evidence, D07/DBC/Matrix/Route/Cluster 결정 상태 동기화,
  generic ALIVE_ERROR/QUEUE_DROP node mapping, Production Fault 의미.
- TBD: publication transport primitive/depth/Full 처리 및 재접속 동기화 API.
- Open: Event 순서/retry/loss/Replay/resync, Active Fault 완전성 및 발생/해제 쌍. 조건부 의미 기능 미구현.

Jira 후보(외부 등록/상태 변경 미실행):
1. **[HINT-48][Interface Review] Fault lifecycle 산출물 동기화** (1~2일).
   Owner: Gateway/CAN/Cluster/PC. D07-9, Workbook Team Encoding, DBC proposal, Routing OPEN 차이 대조;
   Freeze/Reviewer/Date/Evidence 확보. 상대 담당자 리뷰 필요.
2. **[HINT-48][Interface Review] Fault event loss/replay/resync 계약** (1~3일).
   Owner: Gateway/CAN/Cluster/PC/Test. 중복/순서/누락, 재접속 동기화, generic node 의미 결정.
   PC observed count와 Gateway event count를 구분하는 검증 기준 필요.
3. **[HINT-48][Test] Fault propagation HIL capture** (1~3일, 승인 계약/실장 후).
   Owner: Gateway/Cluster/PC/Test. 승인 Fault 발생/복구를 동일 Bus Raw/DBC/LCD에서 비교;
   실제 Timestamp/누락 증거 수집. 이번 Fake 결과를 Hardware PASS로 사용하지 않음.
4. **[HINT-48][Bug draft] Fault source/detail selection resets during RX refresh**.
   재현: source 여러 개/상세 선택 후 새 RX → 첫 source/상세 스크롤 초기화 가능.
   로컬 수정에서 선택·immutable 상세 유지/eviction 정리를 적용하고 회귀 확인.
   신규 모델의 removed-source timestamp 누적 가능성도 제거. 담당자 리뷰 NOT VERIFIED; 외부 등록 미실행.

신규 패키지 설치/의존성 변경 없음. 팀 고정 버전·배포 라이선스 승인 미확정.
담당자 코드 리뷰·사용자 수동 Fault GUI·CANable/ECU Hardware·고부하/장시간 성능 **NOT VERIFIED**.
Git add/Commit/Push/PR/Merge/Jira Done 미실행.

## Phase 3H-2 — Test Automation GUI (Mock/Fake TEST ONLY)

기존 MainWindow의 **Test Automation** 탭에서 고정된 내부 시나리오를 선택하고
수신 파이프라인의 실제 관측 결과를 검사합니다. Frame을 주입했다는 이유만으로
PASS하지 않습니다. 실제 CAN/HIL/ECU 시험 또는 Fault 상태 판정 기능이 아닙니다.

### 사용법

1. 기존 `python -m pc_diagnostic.gui` 또는 `can-diag-gui`로 실행하고 Mode=Mock을 선택합니다.
2. Raw 시나리오를 제외한 시나리오는 Select DBC로 **기존 tests/fixtures/test_only.dbc**를
   명시적으로 로드해야 합니다. Production DBC 기본 매핑/자동 연결은 없습니다.
3. Test Automation에서 Scenario를 선택합니다. 입력 Frame과 고정 기대값이 미리 표시됩니다.
4. CSV/JSONL 시나리오는 **Select test folder...**로 쓰기 가능한 시험 폴더를 명시적으로 선택합니다.
   새 `hint48-mock-*` 하위 폴더만 사용하고 종료 시 정리합니다. 기존 파일은 덮어쓰지 않습니다.
5. **Run isolated TEST ONLY**를 누르고 Assertion별 Expected / Actual observation / Result / Reason을
   확인합니다. 잘린 항목의 전체 내용은 tooltip으로 확인할 수 있습니다.
6. **Cancel / Retry cleanup**은 취소 또는 정리 재시도입니다. **Clear results**는 결과 메모리만 지웁니다.
   실행/정리 미완료 중에는 새 Run·Clear 및 사용자 Source/DBC 편집을 차단합니다.
   탭 전환은 가능하며 기존 사용자 Mock Receiver/Logger는 계속 동작합니다.

사용자 Source가 Live이면 Run을 비활성화하며 직접 호출도 ERROR/BLOCKED로 거부합니다.
현재 Receiver/Logger를 자동으로 중지하거나 Source를 전환하지 않습니다.
일반 CAN Logging과 시험 결과를 구분하며 새로운 Report 포맷·자동 Report 저장은 없습니다.

### 실제 계약과 입력 근거

- 기존 `RawCanFrame`, `MockCanInterface` FIFO, ReceiveWorker, FrameObservation,
  DecodeSession/DecodeService/SignalStateCache, 각 GUI View 및 LoggingSession/RawCanLogger를 재사용합니다.
- 입력은 기존 gui/demo.py의 TEST_ONLY_ID/TEST_ONLY_PAYLOADS 및
  tests/fixtures/test_only.dbc의 정의만 사용합니다. DBC는 변경하지 않았습니다.
- Fixture SHA-256:
  `9ff1750df33163d0b9591912f202be56dda2a61af9dd97fa398f5a2c2c13a93b`입니다.
- 기존 TestOnlySample: 0x651 STD/DLC4, payload `28 00 01 07`;
  Measurement=-10.0/test_unit, Mode=1, Counter=7.
  기존 TestOnlyExtended: 같은 숫자 ID의 EXT/DLC2, payload `01 01`, Reading=515.
  STD/EXT를 서로 다른 Source Message로 관측합니다.
- 반복 시각 10.0/11.0과 AUTOMATION / TEST ONLY 채널은 **PC 시험 입력**입니다.
  CAN 전송 주기·ECU Timeout·차량 측정값을 정의하지 않습니다.
- 기존 Production DBC의 Fault_Status 정의, Message Definition의 리뷰 gate와 Routing OPEN 정의는
  동기화/의미 승인 검토 대상입니다. 이번 Catalog의 Fault는 기존 TEST ONLY Message의
  **History 관측 인프라**만 검사하고 FaultCode·ACTIVE/CLEARED 의미를 생성하지 않습니다.
  이전 Phase3H-1의 조사 근거/미결정 사항은 그대로 유지합니다.
- 외부 입력 자료·새 다운로드·사용자 Python 스크립트를 도입하지 않았습니다.
  도구 범위의 명시적 LICENSE/SECURITY 정책 파일은 확인되지 않았으며 배포 라이선스 승인은 미확정입니다.

### 고정 Catalog v1

전체 ID는 `HINT48-MOCK-<아래 suffix>-v1`입니다.
동일 ID는 동일 입력/기대값 계약을 의미하며 변경된 DBC를 그대로 사용하지 않습니다.

| suffix | 입력 / 실제 기대 관측 |
|---|---|
| RAW | STD/EXT 2프레임, typed Channel/ID/DLC/DATA/시각/플래그가 Raw table에서 일치 |
| DECODE | STD/EXT 모두 decoded; TestOnlySample(-10.0,1,7) 및 TestOnlyExtended(515) |
| DECODE-ERROR | 정상 STD 후 DLC1 시험 입력; decoded/invalid, 실패 Signal은 비어 있고 Raw는 보존 |
| CACHE | 동일 STD 2회; Cache Measurement=-10.0, 마지막 timestamp=11.0 |
| VEHICLE | DBC Observation 명시 매핑; -10.0 / test_unit / Valid 표시 |
| ECU | Gateway라는 시험 카드에 명시 매핑; State: Observed, count=2. 실제 Gateway Online/Health 아님 |
| FAULT | 반복 관측 이력 2개, sequence1/2 및 -10.0; State=Observed, Fault status=Status Unknown |
| GRAPH | 기존 Decode 결과의 두 점 (-10.0,10.0,test_unit), (-10.0,11.0,test_unit) |
| JSONL | 기존 schema로 Raw 2개 기록/읽기 일치; closed/received/written/drop/unconfirmed=(True,2,2,0,0) |
| CSV | 위 Raw 계약과 동일, 기존 CSV header/scalar 표현 유지 |
| SOURCE | 격리 창에서만 Source 변경: Raw/Cache/Graph/Fault 및 매핑 reset, 새 generation·두 번째 채널만 관측 |

모든 시나리오는 application TX=0, transport/worker/writer/timer 해제,
사용자 Source 설정 보존도 검사합니다. 실제값은 Raw table의 FrameObservation, Cache,
Vehicle 셀·ECU 관측·Fault History·Graph samples 및 종료된 Raw 파일에서 얻습니다.
Decode 기대값은 고정 Fixture 계약으로 선언하고 실제 Decode 결과로 다시 계산하지 않습니다.
누락/불일치 actual은 FAIL이며, 주입 성공이나 불완전한 관측을 PASS로 대체하지 않습니다.

### 격리와 상태 전이

Runner는 별도 숨겨진 기존 MainWindow를 생성합니다(재귀 Automation 탭 없음).
ScenarioInput은 기존 MockCanInterface를 조합한 유한 FIFO이며,
Fake factory를 기존 ReceiveWorker에 주입합니다.
**실제 python-can Bus를 만들지 않고 Bus.send도 호출하지 않습니다.**
hidden session의 Live 표시는 기존 수신 경로 재사용을 위한 Fake 설정이며 물리 연결이 아닙니다.
사용자의 MainWindow·Worker·Cache·Logger를 시험 데이터로 대체하지 않습니다.

`IDLE → RUNNING(PREPARING → OPENING → [WRITER_OPENING] → RECEIVING → STOPPING
→ CLEANING) → PASSED/FAILED/ERROR/CANCELLED`.
Source 시험은 격리 창에서만 두 번째 OPENING/RECEIVING을 수행합니다.

- PASSED: 필요한 실제 관측과 자원 정리 Assertion 전부 일치.
- FAILED: 실행은 완료했으나 기대값과 actual이 다르거나 필요한 관측이 누락.
- ERROR: DBC/준비/수신/쓰기/실행 제한/정리 실패. 원인을 보존하며 성공으로 처리하지 않습니다.
- CANCELLED: 관측 완료 전 취소. 해당 Assertion은 NOT EVALUATED이며 PASS가 아닙니다.
- 정리 제한 초과: ERROR와 cleanup_complete=False, session 참조 보존 및 polling 중단.
  Run/Clear는 계속 잠기고 Cancel/Close로 명시적으로 정리를 재시도합니다.
  이미 발생한 ERROR를 취소 성공으로 숨기지 않습니다.

UI 접근/상태 전이는 Qt main thread, 수신/기록은 기존 Worker/Writer입니다.
GUI recv·Writer wait 또는 무한 polling을 추가하지 않습니다.
PC 내부 초기 정책은 tick25ms / 실행5s / 정리3s, 입력8개·Assertion16개 이하,
최신 결과10개 메모리 보관입니다. CAN Period/Fault Timeout/Threshold와 무관합니다.
화면은 최신 결과 상세를 표시하며 이전 결과는 유한 메모리 모델에만 보관합니다.
과거 결과 선택 UI·Export·외부 Script는 이번 MVP에 없습니다.

Close는 먼저 격리 시험을 취소/정리한 뒤 기존 사용자 창의 종료 경로를 다시 실행합니다.
Stop/Close 시 Queue drain과 flush/close는 기존 Logger 계약을 따릅니다.
시험 임시 파일은 성공/실패/취소 후 소유 subfolder 경계를 확인해 정리합니다.
파일 정리 실패도 ERROR로 표시하고 세션 참조를 유지합니다.
일반 사용자 CAN log 및 기존 폴더 파일은 삭제하지 않습니다.

### 검증과 Open 항목

자동화 시험은 `test_automation.py`, `test_scenario_runner.py`, `test_automation_view.py`입니다.
실제 Windows 자동 검증은 `tests/gui_automation_native_smoke.py --output-dir <새 시험 증적 폴더>`입니다.
기존 466개 테스트와 Native8종을 보존합니다. 실제 결과는 VERIFICATION의 Phase3H-2 기록을 참고하세요.

- 현재 Repository/editable 설치 MVP의 내부 tests/fixtures 위치를 사용합니다.
  Fixture가 없는 독립 wheel/배포 설치는 ERROR이며 packaging/resource 정책 후속 검토가 필요합니다.
- Production Fault 상태/Threshold, Active Fault 재구성, 실제 ECU 제어·TX·HIL Assertion은 미지원.
  필요 시 별도 Jira와 **상대 담당자 리뷰 필요**로 분리합니다.
- 고부하/장시간 성능·무손실 기록·실제 디스크/ACL 실패 검증, 실제 CANable/ECU: **NOT VERIFIED**.
- 팀 고정 버전·배포 라이선스 승인: 미확정. 담당자 코드 리뷰·사용자 수동 Automation GUI: **NOT VERIFIED**.
- Jira 후보(외부 등록/상태 변경 미실행):
  1. **[HINT-48][Test] Automation Catalog v1 팀 계약 리뷰**: PC/Test 담당자,
     입력/기대값/실패 검출/자원 정리 Evidence를 대조; 팀 리뷰 완료 근거 확보(1일).
  2. **[HINT-48][Packaging] 내부 TEST ONLY Fixture resource 배포 정책**:
     PC/배포 담당자, wheel에 fixture 포함 여부·위치/버전/라이선스 결정 후 설치본 시험(1~2일).
  3. **[HINT-48][Troubleshooting] Automation 준비 취소의 임시 폴더 잔류**:
     PREPARING signal에서 CSV 시험 취소 → 새 subfolder 잔류 재현.
     이번 로컬 수정에서 CANCELLED 완료 전 cleanup을 수행하며 회귀로 검증; 담당자 리뷰 NOT VERIFIED.
  4. **[HINT-48][Interface Review] Production/HIL Assertion 계약 확보**:
     Gateway/CAN/Cluster/PC/Test와 Fault 산출물 동기화·승인·실 캡처 근거 확보 후 별도 구현(1~3일).

신규 의존성·라이브러리 설치/버전 변경·공통 Interface 변경 없음.
Git add/Commit/Push/PR/Merge/Jira Done 미실행.

## Phase 3H-3 — Packaging / Fixture Distribution 검토 (NEEDS_REVIEW)

2026-10-14, 기준 HEAD e5621aa9f156a0bcbc97190a64a1b0450eb237a8.
사용자는 기존 TEST ONLY DBC에 대해 **“아직 미승인 — 자동 포함을 보류하세요”**라고 확인했습니다.
따라서 Package Data 추가·Fixture 복사·리소스 조회 코드 변경은 **보류**합니다.
현재 Wheel은 원인 분석용 로컬 산출물이며 팀원 배포 승인/완성된 배포 패키지가 아닙니다.

### 정적 리소스 Inventory

| 실제 경로 (이 도구 기준) | 용도·Scenario 의존 | 출처·추적 | Wheel 처리 / 승인 |
|---|---|---|---|
| tests/fixtures/test_only.dbc | TEST ONLY Signal/STD·EXT/Choice 정의. 현재 Runner는 모든 시나리오의 내부 무결성 확인에 사용; Raw 이외는 명시적 DBC 로드도 필요 | TEST ONLY 합성·프로젝트 정의 복제 아님으로 표기, cde2ebf/DHK, Git tracked | 현재 미포함. 모든 11개 시나리오의 독립 실행에 필요하지만 배포 미승인; 자동 포함 보류 |
| src/pc_diagnostic/gui/demo.py | 기존 TEST_ONLY_ID / 두 payload; Mock 입력 재사용 | 69f904c/DHK, 기존 Fixture/codec 예제 출처 주석, Git tracked | 기존 Python 모듈로 Wheel에 포함. 새 별도 데이터 파일 아님; 정식 배포 권한·정책은 별도 검토 |
| src/pc_diagnostic/gui/automation.py | 고정 Catalog11 / 입력 조합 / Assertion 기대값 / TEST_ONLY DBC SHA | e5621aa/DHK, Git tracked | 기존 Python 모듈로 Wheel에 포함. Expected를 actual로 생성하지 않음; 새 Frame/Signal 정의 없음 |

무결성 SHA-256:
- test_only.dbc (823 bytes): `9ff1750df33163d0b9591912f202be56dda2a61af9dd97fa398f5a2c2c13a93b`
- demo.py (675 bytes): `db7899aa9545b8676f92322e493cf65756133c89ec1f43353e4507f434d8ef3b`
- automation.py (9236 bytes): `b222bafff19c299e839b8d0c30d9ef1fa02d09be488539ad57ff70b424707bc9`

Mock payload와 Expected Value는 위 Python 모듈 내부의 기존 상수/고정 계약입니다.
추가 Scenario 파일·외부 DBC·Capture·새 합성 Fixture를 만들지 않았습니다.
Git author와 합성 자료라는 주석은 출처의 근거이며 법적 소유·재배포 권한·팀 승인을 대신하지 않습니다.
현재 도구의 명시적 LICENSE/SECURITY/redistribution 승인 근거는 확인되지 않았습니다.
Production DBC/Matrix/Routing/Firmware는 Wheel 입력에 넣지 않습니다.

### 방식 비교와 보류 설계

| 기준 | A: Package Data + importlib.resources | B: 외부 Fixture 디렉터리 | C: 사용자가 파일 명시 선택 |
|---|---|---|---|
| Wheel 독립성 | 승인된 자료까지 포함하면 가장 높음 | 별도 자료가 있어야 완성 | 사용자가 적법한 자료를 준비해야 완성 |
| 재현성 | 고정 SHA·버전으로 높음 | 외부 파일 버전/누락 관리 필요 | 선택한 파일의 SHA/조건 검증 필요 |
| 보안 | 고정 내부 데이터·읽기 전용 접근; 실행 스크립트 없음 | 자동 검색 대신 명시 경로·허용 자료 검증 필요 | 자동 Production 연결 없이 사용자 선택·무결성 확인 |
| 배포 권한 | 자료 포함 전 승인 필수 | 별도 자료 배포도 사용권 승인 필요 | 도구가 자료를 배포하지 않아도 사용자가 가진 자료의 사용권 확인 필요 |
| 개발 호환성 | 표준 locator와 기존 Fixture 계약의 동등성 회귀 필요 | CWD/개인 경로 하드코딩 금지 | 기존 Select DBC 유지 가능 |
| 유지보수 | 자료 중복 시 byte 동일성·버전 정책 필요 | 외부 디렉터리 수명·설정 정책 필요 | UI에서 미선택/누락/오류 안내 필요 |

권장 **후보**는 승인 확보 후 A입니다. 단, 구현·확정하지 않았습니다.
승인 후 기존 DBC의 바이트를 그대로 package resource에 포함하고, 기존 Scenario SHA를 유지하며
Python 표준 importlib.resources로 조회하는 안을 검토합니다.
파일 경로가 필요한 loader에는 resource context 수명을 Runner cleanup까지 유지해야 합니다.
설치 디렉터리에 쓰지 않고 CWD/개인 PC 절대 경로에 의존하지 않아야 합니다.
TEST ONLY 선택은 명시적으로 안내하고 Production DBC 자동 선택은 계속 금지합니다.

B/C도 아직 구현하지 않았습니다. **현재 Select DBC로 외부 파일을 선택하는 것만으로는 해결되지 않습니다.**
Runner가 먼저 개발 구조의 내부 fixture_path()를 검사하므로 Wheel에서 실패합니다.
B/C를 채택하려면 적법한 사용자 선택 자료의 무결성 확인과 내부 locator 의존 제거를
별도 승인 범위로 구현·회귀 검증해야 합니다. Fixture 경로를 임의로 새 기본값으로 넣지 않습니다.

### 현재 Build / 설치 구조

- 기존 setuptools.build_meta, src package discovery, Requires-Python >=3.10을 유지합니다.
- Package Data는 설정되어 있지 않으며 tests/fixtures는 src 밖에 있습니다.
- 현재 locator는 __file__.parents[3] / tests/fixtures/test_only.dbc입니다.
  개발 트리에서는 동작하지만 Wheel에서는 설치 환경의 Lib/tests/fixtures를 가리킵니다.
- 선언 의존성은 기본 없음, 선택 extras:
  GUI PySide6>=6.10,<7, CAN python-can>=4.6,<5, DBC cantools>=40,<45,
  test pytest>=8,<10 및 CAN/DBC. 기존 slcan/gs-usb extras도 유지합니다.
- CLI can-diag, GUI can-diag-gui 및 모듈 진입점을 유지합니다.
- 개발 환경 검증 버전과 팀 승인 고정 버전은 구분합니다. 팀 고정 버전/배포 라이선스는 미확정입니다.

이번에는 기존 설치된 Build 도구(Python3.12.14/setuptools84.0.0/wheel0.48.0)만 사용해
새 임시 src/pyproject/README 복사본에서 기존 backend로 Wheel을 만들었습니다.
원래 Worktree의 build/egg-info 생성이나 pyproject/source 변경은 없습니다.
프로젝트 .venv에는 setuptools/wheel/build가 설치되어 있지 않았으며 이를 재설치하지 않았습니다.

승인 후 절차(현재 미완료):
1. TEST ONLY DBC 사용권·재배포 범위/담당자/날짜/Evidence 및 팀 배포 정책 확보.
2. 승인된 resource만 포함하고 표준 resource locator 구현; 기존 Fixture/Expected 계약 유지.
3. 기존 backend로 새 임시 Build 입력에서 Wheel 생성·Archive Inventory/SHA 검사.
4. Worktree 밖 새 venv/CWD에서 설치 및 resource/GUI/11개 Scenario 실행 검증.
5. read-only resource 접근·누락 안내·Source/Live 보호·종료/정리 신규 시험.
6. 기존517/CLI140/Native9 회귀 후 팀원 PC 검증·코드 리뷰. Git 업로드는 별도 승인.

현재 기본 Wheel만 오프라인 설치하는 진단 절차는 다음 형태입니다.
Build 도구가 설치된 실행 Python과 완전히 새 출력/venv를 사용합니다.

    python -c "import setuptools.build_meta; print(setuptools.build_meta.build_wheel('NEW_WHEEL_OUTPUT'))"
    python -m venv --without-pip NEW_CLEAN_VENV
    python -m pip --python NEW_CLEAN_VENV/Scripts/python.exe install --no-index --no-deps PATH_TO_LOCAL_WHEEL
    python -m pip --python NEW_CLEAN_VENV/Scripts/python.exe check
    NEW_CLEAN_VENV/Scripts/python.exe -I -B -m pc_diagnostic --help
    NEW_CLEAN_VENV/Scripts/python.exe -I -B -m pc_diagnostic.gui --help

Build 명령의 CWD는 Worktree 자체가 아닌 새 Build 입력 복사본입니다.
--no-deps 기본 설치에는 PySide6/cantools/python-can가 없으므로 GUI 실제 실행·Decode/Live 지원을
증명하지 않습니다. 승인된 배포 환경에서는 필요한 기존 extras를 별도 설치·검증해야 하며
이번에 외부 패키지 다운로드·설치나 새 버전 고정은 하지 않았습니다.
GUI --help 성공은 정상 창 실행 성공과 다릅니다.

### 현재 결과·Gate·후속 검토

실제 Wheel Inventory/Clean Install/누락 재현·회귀 결과는 VERIFICATION의 Phase3H-3에 기록합니다.
독립 설치에서 Catalog11 로드는 가능하지만 필요한 DBC가 없으므로 11개 실행은 미검증/보류입니다.
Package Resource 조회 구현·승인 Fixture 포함·완성된 Wheel GUI 배포 완료를 주장하지 않습니다.

Jira 초안(외부 등록/Done 미실행):
1. **[HINT-48][Review] TEST ONLY DBC 재배포 승인** (PC/배포/팀 담당자, 1일):
   위 SHA·출처·Wheel 포함 범위·허용 배포 대상·승인 담당자/날짜/Evidence 기록.
2. **[HINT-48][Packaging] 승인 Fixture resource locator 구현** (PC/Test, 1~2일, 위 승인 후):
   Package Data/importlib.resources·읽기 전용/누락/CWD/11개 시나리오·Clean GUI 검증.
3. **[HINT-48][Troubleshooting] pip 임시 디렉터리 정리 권한**:
   외부 clean install의 기본 sandbox Temp 정리 경고 재현. 전용 TEMP/TMP/TMPDIR 지정 후
   새 환경의 설치·pip check·진입점 재실행에 경고 없음/전용 Temp 비어 있음 확인.
   타인/기존 Temp 디렉터리 수동 삭제 없음.
4. **[HINT-48][Test] 팀원 PC 배포·라이선스 체크** (PC/팀원/Test, 1~2일):
   승인된 extras/지원 Python·설치·Mock GUI·11개 시나리오·배포 조건을 실제 팀원 PC에서 확인.

최종 상태는 **NEEDS_REVIEW**. 배포 승인 Gate는 **미승인/보류**입니다.
Hardware·사용자 수동 GUI·팀원 PC·담당자 리뷰: NOT VERIFIED.
CAN/LIN Interface 변경 시 상대 담당자 리뷰 필요. Git add/Commit/Push/PR/Merge/Jira Done 미실행.

## Phase 3J-1 — Driver Control / Mock Input (2026-10-14)

기존 GUI에서 **Driver Control** 탭을 선택한다. GUI 실행 방식은 그대로다.
Repository 루트에서 .\tools\diagnostic_GUI\.venv\Scripts\python.exe -m pc_diagnostic.gui
또는 기존 설치 진입점 can-diag-gui를 실행한다.

1. Mode=Mock을 유지한다. DBC/Receiver 실행 없이도 PC 내부 입력을 검증할 수 있다.
2. Accelerator, Brake, Gear를 명시적으로 설정한다. 초기값은 Not Configured이며 0/OFF와 구분한다.
3. Window Open/Close, Light ON/OFF 버튼은 편집만 한다. **Apply Mock Input**이 메모리 Mock Adapter에 전달한다.
4. Request State의 Mock Input / Mock Accepted / Input Error, PC 생성 시각과 내부 이력을 확인한다.
5. **Reset Mock Inputs**는 PC 메모리만 초기화한다. 차량 정지/해제 명령은 아니다.
6. 기존 Start/Stop/Clear는 CAN 관측 기능이다. 동일 Source에서는 Driver 입력/마지막 Mock 수락을 유지한다.
   Source 설정 변경은 기존 Receiver/Writer 정리 후 가능하며 미적용 입력·수락 결과·입력 이력을 폐기한다.

### 입력 모델 / Adapter 경계

- DriverControlView → DriverInputModel → MockDriverAdapter 구조다. Qt 메인 스레드에서 짧은 메모리 처리만 한다.
  Driver 경로는 Bus, Receiver, RawCanFrame, Encoder, 기존 CLI Sender를 호출하지 않는다.
- Accelerator 0..100%는 핸드북9.1/임시안의 **Mock 모델 정책**이다. Production Scale/단위/범위 승인으로 보지 않는다.
- Brake는 Mock ON/OFF(bool), Gear는 P/N/D/R 이름, Window는 OPEN/CLOSE 의도, Light는 ON/OFF 의도만 보관한다.
  PC 입력 CAN Enum/bit layout을 정의하거나 기존 ECU Enum 숫자로 변환하지 않는다.
  Ignition, Window STOP/세부 모드, 개별 Lamp 선택은 이번 범위에 없다.
- 숫자 변환 실패, 범위 초과, NaN/Infinity, 잘못된 타입/선택을 거부한다.
  Accelerator+Brake 동시 입력은 그대로 보관한다. Torque 제한/우선순위/Fail-safe는 VCU 책임이며 계산하지 않는다.
- 매 Apply는 PC 내부 번호와 생성 시각을 가진 명시적 요청이다. 주기 송신·자동 재시도·무한 큐는 없다.
  재진입 호출을 거부하며 입력 이력/Mock 수락 이력은 각각 최대128건이다. CAN AliveCounter/Timeout이 아니다.
- Mock Accepted는 **메모리 요청 처리 성공**이다. ECU Response Not Verified는 계속 유지한다.
  현재 편집/실패의 Applied=False와 과거 Last Mock Accepted를 별도로 표시한다.
  Adapter 생성/수락/정리 실패는 오류 종류를 표시하며 내부 경로/인증정보를 오류 문자열에서 노출하지 않는다.
- Live는 버튼과 모델 양쪽에서 차단한다. disabled 버튼의 직접 Slot 호출/모델 호출도 송신하지 않는다.
  현재 코드에는 Interface 승인이나 Live 운전자 송신을 활성화하는 경로가 없다.
- TorqueRequest는 VCU 계산 결과의 관측 항목이다. 이 탭은 자동 신호 매핑/값 계산을 하지 않는다.
  실제 RX 값은 기존 CAN Monitor/Signals 또는 명시적으로 매핑한 Vehicle Status/Signal Graph에서 확인한다.
- Mock 수락을 Raw RX/Signal Cache/Graph/Fault/CAN Logger에 가짜 ECU 응답으로 넣지 않는다.
  입력 이력은 PC 메모리 표시이며 기존 CSV/JSONL Raw Logger 계약을 변경하지 않는다.

### 실제 산출물 / 임시설계 대조 결과

- 외부 제공 HINT48_PC_Driver_Input_Interface_임시설계_v0.1.xlsx의 5개 sheet를 읽었다.
  SHA-256: 871e172dcd591c3b12a4dae796ef4b5f2c4e1f54e0f27ef3134a9e180f423476.
  Repository 밖의 임시 초안이며 수정/복사/패키지 포함을 하지 않았다.
- 메시지_제안 row2의 PC_Driver_Input ID 0x600은 개발 임시 후보이며 DLC/Payload/주기/Timeout은 TBD다.
  PC_Body_Input 경로와 ID도 Open이다. 이 후보 ID는 소스의 CAN 생성/설정 값으로 쓰지 않았다.
- 현재 network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc 내부 VERSION은 0.4 - review-ready interface proposal이다.
  파일명만으로 승인된 최종본이라고 취급하지 않는다. PC_Driver_Input/PC_Body_Input 정의는 없다.
  후보 ID가 DBC에 없다는 사실은 예약/충돌 검사 완료를 뜻하지 않는다.
- 이 DBC와 docs/requirements/02__메시지_정의서_ver1.2.xlsx CAN_Message_Definition row6은
  VCU_Command=0x100, Standard, DLC8, VCU 송신, 10ms를 정의한다.
  TorqueRequest/Gear/Brake/AliveCounter는 **VCU 출력**이며 PC가 대신 송신하지 않는다.
  Gear 이름 P/N/D/R은 기존 DBC Value Table과 일치하나 PC 입력 CAN Encoding은 미승인이다.
- 핸드북9.1의 Brake/Torque 제한 예시는 VCU 설계 책임이다.
  docs/requirements/05__요구사항_명세서_ver1.2.xlsx Requirements row8(SYS_REQ_003)도
  VCU 입력 기반 제어 요구사항이며 PC 입력 CAN 수신 계약/동시 입력 우선순위를 확정하지 않는다.
- 현재 PC 브랜치 VCU 폴더는 scaffold다. fetch 없이 로컬 보관 origin/VCU_ECU
  (95a3e55d4b5b9a51ca7d136858f86b6adb3144e3)의 Core/Src/main.c를 읽었다.
  HAL 초기화/빈 main loop이며 운전자 CAN 입력 해석을 확인하지 못했다. 최신 원격 구현 확인 결과는 아니다.
- 임시안 신호_제안 row7의 Window 목적지는 Door ECU로 적혀 있다.
  메시지 정의서 LIN_Frame_Definition row10과 Requirements row49~50은 별도 Window ECU/로컬 limit-stop을 명시한다.
  **검토 필요 차이**다. OPEN/CLOSE→UP/DOWN 변환 및 로컬/원격 우선순위는 구현하지 않았다.
- network/routing/Gateway_Routing_Table_v0.4_CAN_to_LIN_Decision_Baseline.xlsx CAN_to_LIN row4/9/12/13은
  VCU_Command Byte3의 Body 제어 후보와 Gateway→LIN Light/Door/Window 경로를 제안한다.
  현재 DBC에는 해당 Body 요청 신호가 없다. Matrix/DBC/LDF 동기화와 **상대 담당자 리뷰 필요** 상태를 유지한다.
  Window/Light 입력은 이 Routing 후보를 적용하지 않는 메모리 의도다. Door 입력은 이번 UI 범위가 아니다.
- 별도 CAN_Matrix.xlsx 및 승인된 PC 입력 Interface는 확인되지 않았다.
  핸드북4.2/5.5 및 CONTRIBUTING Interface Change 절차 이후에만 Production 구현을 검토한다.

### 검증 / 미완료 / 다음 협업

2026-10-14 전체569(기존517+신규52), CLI별도140, Windows Native10종 PASS.
Driver 자동 검증에서 CAN 생성/송신 경계 호출0회. 실제 수동 확인/Hardware 검증은 아니다.
새 라이브러리 설치/pyproject 변경 없음. 팀 고정 버전 미확정, 담당자 코드 리뷰 NOT VERIFIED.
Hardware 및 Driver GUI 사용자 수동 확인 NOT VERIFIED. Fixture Wheel 재배포 미승인 상태도 유지한다.

후속 Jira 등록용 초안(외부 등록하지 않음):

- **1~2일 / HINT-48 PC→VCU Interface 승인**: PC/VCU/Gateway/시스템 담당.
  후보 ID 충돌/예약, DLC/Signal/Scale/Enum, 주기/Timeout/Fail-safe, 모드/권한/수신 확인을 검토.
  완료 증거는 담당자 승인과 Matrix/DBC 동기화 diff이며 Mock PASS로 대체하지 않는다.
- **1~3일 / Body 입력 경로·Window 책임 정합성**: VCU/Gateway/Door/Light/Window 및 PC 담당.
  PC→VCU 또는 Gateway 진입점, Window 대상 오류, OPEN/CLOSE 의미, 동시 입력/로컬 우선순위,
  Lamp 범위와 Routing Byte3/DBC 차이를 정리한다. 상대 담당자 리뷰 필요.
- **1~3일 / 승인 후 PC 송신 및 응답 분리 시험**: PC/VCU/Gateway/테스트 담당.
  앞선 Interface 승인 이후 별도 작업으로 Encoder/권한/수신 확인/실기 Gate를 설계한다.
  CANable/ECU 실측은 현재 Hardware 준비 조건 충족 전에는 진행하지 않는다.
