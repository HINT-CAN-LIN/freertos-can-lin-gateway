# Phase 3J-1 Driver Control Panel / Mock Input 검증 — 2026-10-14

**최종 판정: PASS (Mock 소프트웨어 구현/자동 검증 범위). Production TX는 미구현/차단.**
기준 Branch PC-Diagnostic-Test / HEAD e5621aa9f156a0bcbc97190a64a1b0450eb237a8.
시작 시 기존 Phase3H-3/3I-1 README.md, VERIFICATION.md 수정2개와 빈 Stage를 확인했다.
기존 문서 전체를 유지하고 본 기록만 앞에 추가한다.
팀 고정 버전 미확정, 담당자 코드 리뷰/Driver 사용자 수동 검증/Hardware 모두 NOT VERIFIED다.

## 이번 실제 실행 결과

| 검증 | 결과 |
|---|---|
| 새 입력 모델/Adapter 테스트 | 40 PASS |
| 새 Driver Qt 테스트 | 12 PASS |
| 신규 합계 | 52 PASS (1.25s) |
| 전체 pytest | 569 PASS (51.78s) = 기존517 + 신규52 |
| 원본 Phase1/2 목록 기반 CLI 별도 회귀 | 140 PASS (0.53s) |
| Windows Driver Control Native | PASS; Windows 플랫폼 실제 창 노출 |
| 기존 Windows Native | Raw/Decode/Vehicle/ECU/Logging/Fake Live/Graph/Fault/Automation 9/9 PASS |
| 전체 Native | 10/10 PASS; 수동 확인/Hardware와 별개 |
| CLI/GUI 모듈 --help | PASS |
| 설치 can-diag.exe / can-diag-gui.exe --help | PASS |
| CLI monitor --backend mock | 종료0; fixture 미주입 Captured0 (실기 결과 아님) |
| pip check | No broken requirements found. |

pytest는 매 실행 새 .test-tmp/phase3j1-* 경로를 사용하고 캐시를 비활성화했다.
검증 산출물/스크린샷은 Git 제외 경로에만 생성했다. Windows Driver 화면 캡처도 실제 열어 확인했다.
첫 focused 실행50 PASS/2 FAIL은 신규 테스트의 잘못된 Sender 이름과 이미 삭제된 Qt Worker 참조 검사 때문이었다.
실제 RawCanSender.send 및 isValid 검사를 사용하도록 신규 테스트만 정정했다.
그 후 신규52/전체569 모두 통과했다. CLI 첫 부분 선택97 PASS는 전체140 검증으로 사용하지 않았으며,
원본 파일 목록으로 다시 실행한140 PASS를 위에 기록했다. 기존 테스트는 수정/삭제/약화하지 않았다.

## 검증된 범위

- Accelerator 범위/변환/NaN/Infinity/타입, Brake ON/OFF, Gear P/N/D/R, Window OPEN/CLOSE, Light ON/OFF.
- Brake+Accelerator 동시 값 보존. VCU 우선순위/토크 계산 미구현.
- 편집/명시적 Apply/현재 Applied/과거 Last Mock Accepted/Input Error 분리.
- 잘못된 편집 후 이전 draft 재적용 차단, Adapter 생성/수락/잘못된 receipt/정리 오류, Reset 후 회복.
- 생성 시각 오류, 재진입 차단, 반복 요청의 독립 PC 번호, 각128건 이력 상한.
- Receiver/DBC 없이 Mock 입력. 수락 결과를 Raw/Cache/Logger/Graph/Fault에 ECU 데이터로 넣지 않음.
- Source 변경에서 입력/Mock 결과/이력 초기화; Live UI 및 직접 Slot/모델 호출 차단.
- 기존 can.Bus / BusABC.send / MockCanInterface.send / PythonCanInterface.send / RawCanSender.send 경계를
  감시한 Driver 테스트에서 호출0회. 실제 CANable/ACK/배선 검증이 아니다.
- Driver Native: 전체 버튼/동시 입력/세 번의 새 Receiver 수신·정지/Raw Clear와 입력 분리/
  Live 전환·직접 호출 차단/Reset 및 활성 Worker 종료.
- Driver Adapter는 메모리만 소유하고 추가 Thread/Timer/파일/Bus 없음. 종료 후 입력 거부.
  기존 Receiver/Logger/Graph 자원 계약과 Native 회귀 유지.
- Logging Native: CSV/JSONL Raw 저장의 CLI byte 호환성과 기존 파일 보호 재확인.
  PC 입력 이력을 Raw Logger Schema에 합치지 않았다.

## Interface 근거 및 Open

외부 임시 Excel SHA-256: 871e172dcd591c3b12a4dae796ef4b5f2c4e1f54e0f27ef3134a9e180f423476.
메시지_제안 row2~4, 신호_제안 row2~8 등 실제5개 sheet를 읽었다.
0x600은 제안일 뿐이며 소스의 CAN ID로 사용하지 않았다. PC Payload/주기/Timeout/Fail-safe는 Open이다.
DBC의 VCU_Command0x100은 VCU 송신이며 PC가 대신 송신하지 않는다.
DBC 내부 VERSION은 review-ready proposal이며 파일명만으로 승인 여부를 확정하지 않았다.
Window 임시안의 Door 목적지와 별도 Window ECU 정의가 다르며 Routing Body Byte3 후보와 DBC 부재도 검토 필요다.
README에 근거 행/책임과 후속 Jira 초안을 기록했다.
공통 DBC/Matrix/Requirements/Routing/Firmware 및 CLI 공개 Interface 변경 없음.
CAN/LIN Interface는 상대 담당자 리뷰 필요 상태다. 새 Frame/Bit Layout/Timeout/Fail-safe는 생성하지 않았다.

## 환경 / 보존 / 협업

실제 .venv Python3.14.6 / PySide6 6.10.3 / python-can4.6.1 / cantools44.2.1 / pytest9.1.1.
기존 설치 환경이며 팀 승인 고정 버전이 아니다. 새 설치/가상환경 재설정/pyproject 변경 없음.
Git add/Commit/Push/PR/Merge/Reset/Rebase 및 Jira 등록/Done 없음.
Fixture Wheel 배포 승인 보류와 Phase3I-1 Hardware BLOCKED/NOT RUN 기록 유지.
실제 CANable/ECU, Driver 사용자 수동 확인, ECU 수신/제어 결과, Production 의미/권한/안전 정책,
담당자 리뷰, 배포 라이선스/Fixture 승인, Integration Merge는 완료로 주장하지 않는다.

## 최종 보존 검사

최종 git diff --check PASS, Stage 비어 있음. 추적 수정3개/미추적 신규6개/삭제0개.
기존 테스트 및 공통 산출물 SHA-256 변경 없음. D: 원본25개, 다른 Worktree 추적 파일/HEAD/Status,
리뷰 문서(SHA-256 751ecd803fc1866cc12a51ba2df4a93a64bd41f2cc441456eb9ea49b3178b975),
기존 Git refs 모두 작업 시작 기준과 동일함을 확인했다.
기존 README/VERIFICATION 내용도 작업 시작 바이트를 SHA-256으로 확인했다.
.venv/.test-tmp는 git check-ignore로 제외 확인. 신규 소스/테스트 비밀키·토큰·개인 절대경로 검색 결과 없음.

---

# Phase 3I-1 CANable Pro Live Hardware Integration 사전 검증 — 2026-10-14

**최종 판정: BLOCKED (Hardware Gate). Software 회귀는 PASS.**
사용자가 CANable Pro·ECU 미연결, CAN 배선 미연결, ECU 전원 미인가,
실제 송신 노드 없음 및 실기 설정/Flash 버전 미확인을 명시했다.
사용자 지시에 따라 실제 CAN 연결·수신·실기 Decode는 시도하지 않았다.
추가 패키지 설치·Firmware/Driver 변경도 수행하지 않았다.

기준 Branch PC-Diagnostic-Test / HEAD e5621aa9f156a0bcbc97190a64a1b0450eb237a8.
시작 상태는 기존 Phase3H-3 README.md/VERIFICATION.md 수정2개, Stage 비어 있음.
해당 내용을 보존하고 이번 Phase3I-1 기록만 VERIFICATION 앞에 추가한다.

## Gate A — Windows 장치 조사 (READ ONLY)

2026-10-14 13:13:38 +09:00의 실제 조회:
- Win32_PnPEntity에서 USB/Ports 및 CANable/candleLight/CANtact/gs_usb/SLCAN 이름 검색.
  조회된 USB/Ports 항목6개, CAN 이름 후보0개. 관련 항목은 내장 장치이며 CANable을 식별하지 못했다.
- Win32_SerialPort: **0개**, 실제 COM 목록 비어 있음.
- HKLM HARDWARE/DEVICEMAP/SERIALCOMM: **없음**.
- pnputil /enum-devices /connected /class Ports: **No devices were found on the system.**
- CANable VID/PID: **UNKNOWN**. Firmware/Driver/Service/포트 점유: **UNKNOWN / NOT VERIFIED**.
  확인되지 않은 COM 포트나 gs_usb index를 임의로 선택하지 않았다.
- 사용자 확인과 일치: **CANable Pro USB-C 미연결**.
  케이블 형태로 SLCAN/candleLight/gs_usb Firmware를 추정하지 않았다.
- 최초 sandbox CIM 조회는 리소스 접근 오류였으며, 시스템 변경 없는 읽기 전용 조회로 다시 확인했다.
  이 권한 오류를 장치 Firmware/Driver 결함으로 단정하지 않았다.
- Device Manager에 해당하는 Windows PnP 정보를 조사했으나 GUI Device Manager 조작/Driver 변경은 없었다.
  장치가 없으므로 실제 Device Manager 후보의 상세 Driver/Hardware 정보 확인은 미완료다.

**Gate A BLOCKED.** Windows의 미검출 관측과 사용자가 확인한 미연결 상태를 구분해 기록한다.
장치 모델/Revision·VID/PID·현재 Firmware·Driver·Backend·점유 여부는 재연결 후 다시 확인해야 한다.

## 물리 상태 — 사용자 확인 (실측 아님)

| 항목 | 사용자 응답 |
|---|---|
| CANable Pro USB-C | 미연결 |
| CAN_H / CAN_L | 미연결 |
| CAN Transceiver / 종단저항 / GND·절연 | 미확인 |
| ECU 전원 | 미인가 |
| 실제 CAN 송신 노드 | 없음 |
| 각 노드의 500000 bps | 실기 미확인 |
| 실제 Cluster Flash 버전 | 미확인 |

소프트웨어로 배선/절연/저항/전원을 확인했다고 주장하지 않는다.
현재 실제 Live RX 측정은 하지 않았으므로 **RX=0 실측**이 아니라 **RX NOT RUN**이다.
송신 노드 없이 수신0이 될 수 있다는 일반 조건과 실제 수신 측정 결과를 혼동하지 않는다.
500000 bit/s / Classic CAN / STD는 사용자 제시 Cluster 시험 기준과 현재 GUI의 초기값이며,
연결 장치/실행 Firmware의 측정·설정 확인 결과가 아니다.

## Gate B — Backend 의존성 / 기존 GUI 계약

현재 개발 .venv Python3.14.6의 배포 설치 정보와 실제 Runtime import를 각각 검사했다.

| 패키지 / import | 설치 Version | import 결과 |
|---|---|---|
| python-can / can | 4.6.1 | PASS |
| pyserial / serial | 미설치 | ModuleNotFoundError |
| gs-usb / gs_usb | 미설치 | ModuleNotFoundError |
| pyusb / usb | 미설치 | ModuleNotFoundError |
| PySide6 | 6.10.3 | PASS (Qt 창 실행은 Native 회귀에서 별도 확인) |
| cantools | 44.2.1 | PASS |

pyserial이 없으므로 serial.tools.list_ports의 추가 열거는 수행할 수 없었다.
이는 Win32/PnP/레지스트리에서 확인한 COM0과 별도로 기록한다.
gs_usb/pyusb 및 실제 USB backend library/Driver 준비는 확인되지 않았다.
모듈 설치/명목 Windows 지원을 실제 Firmware/Driver 통신 성공으로 간주하지 않는다.

확인한 기존 코드:
- gui/connection.py:7~17: Mock/Live, slcan/gs_usb 선택 및 시험 bitrate500000.
- connection.py:29~38: SLCAN의 명시 port string, gs_usb의 명시 nonnegative index,
  입력 bitrate 검증. 코드에서 COM3/index0을 자동 선택하지 않는다.
- connection.py:47~67: 선택 Backend 의존성 확인 후 기존 PythonCanInterface 생성.
- gui/window.py:303~323: 선택 Source에 맞는 Factory를 Worker에 전달;
  Live 실패를 Mock로 자동 대체하지 않는 기존 정책.
- gui/receiver.py:39~62: factory 생성·Live transport 계약 확인·기존 recv loop.
  GUI Live 수신 경로는 application CAN send를 호출하지 않는다.
- window.py:330/501 이후: 기존 Stop/Close/Receiver/Writer 정리 경로.
- python-can Adapter의 CLI send API는 기존 기능으로 보존되나 이번 실제 Hardware 작업에서 호출하지 않았다.

현재 Backend·Channel은 **UNKNOWN / 미선택**이다. 실 CAN bitrate 적용도 **NOT RUN**.
**Gate B 미완료**: 장치/Firmware 미확인 및 선택 의존성 누락.
다른 프로그램의 실제 장치 점유/해제도 장치가 없으므로 확인하지 않았다.

### 의존성 준비 후보 — 설치 미실행

아래는 재연결 후 Firmware/Backend를 확인하고 사용자 설치 승인을 받은 경우에만 검토할 후보다.
현재 사용자 지시대로 **설치하지 않는다**.

- SLCAN이 실제 확인될 경우:
  `.venv/Scripts/python.exe -m pip install "python-can[serial]==4.6.1" "pyserial==3.5"`
- gs_usb/candleLight가 실제 확인될 경우:
  `.venv/Scripts/python.exe -m pip install "python-can[gs-usb]==4.6.1" "gs-usb==0.3.1" "pyusb==1.3.1"`

현재 python-can4.6.1 metadata의 선택 제약:
serial extra → pyserial~=3.0, gs-usb extra → gs-usb>=0.2.1, Requires-Python>=3.9.
위 버전은 이 제약과 공식 배포 정보에 따른 **설치 검토 후보**이며 팀 승인 고정 버전이 아니다.
Python3.14.6에서 해당 미설치 패키지의 실제 Runtime/장치 연동 호환성은 NOT VERIFIED.
GS 계열은 PyUSB에 더해 실제 USB backend library/Windows Driver 준비가 필요하다.
Firmware Flash·Driver 교체·Zadig 등은 이번 범위에서 실행하지 않으며 별도 승인/검토 대상이다.
python-can의 현재 설치 metadata License-Expression은 LGPL-3.0-only.
라이선스 확인을 조직 배포 승인으로 해석하지 않는다.

공식 참고 (2026-10-14 조회, 자료의 샘플 송신 코드는 실행하지 않음):
- [python-can4.6.1 SLCAN](https://python-can.readthedocs.io/en/v4.6.1/interfaces/slcan.html):
  serial port 기반, bitrate와 tty baudrate 구분, listen_only 옵션 계약.
- [python-can4.6.1 gs_usb](https://python-can.readthedocs.io/en/v4.6.1/interfaces/gs_usb.html):
  Windows 지원 설명·명시 index/channel 및 PyUSB backend library 필요.
- [pyserial 공식 License](https://github.com/pyserial/pyserial/blob/master/LICENSE.txt):
  BSD-3-Clause. [pyserial 배포3.5](https://pypi.org/project/pyserial/).
- [gs-usb 배포0.3.1 / License](https://pypi.org/project/gs-usb/):
  MIT 표기.
- [PyUSB 공식 License](https://github.com/pyusb/pyusb/blob/master/LICENSE):
  BSD 3조항. [PyUSB 배포1.3.1](https://pypi.org/project/pyusb/):
  Python>=3.9 및 pre-built USB backend 필요.
실제 설치본 License/NOTICE·전이 의존성/USB library 조건은 설치 승인 후 다시 확인해야 한다.
프로젝트/팀 배포 라이선스 승인 미확정 상태는 유지한다.

## 실제 Hardware Gate 결과

| Gate / 항목 | 결과 |
|---|---|
| A 장치 식별 / 점유 | BLOCKED, USB 미연결 / CANable 미검출; 점유 미확인 |
| B Backend·Channel·Driver 준비 | 미완료, UNKNOWN 및 미설치 의존성 |
| C 실제 Live Connect / Disconnect / Shutdown | **NOT RUN** |
| D 실제 Raw RX / ID·STD·EXT·DLC·timestamp·payload·출처 | **NOT RUN** |
| E 실제 Repository DBC 선택·DLC/Signal Decode·Invalid/Reserved/Error | **NOT RUN** |
| F 실제 Signal Graph / CSV·JSONL / Fault Frame / Flush | **NOT RUN** |
| Cluster LCD와 PC 비교 / 실행 Firmware | **NOT RUN / NOT VERIFIED** |
| Frame Loss / Jitter / Cycle / Fault 전파 지연 | **NOT MEASURED** |
| Hardware PASS | **없음** |

실 CAN application TX, 물리 Replay, Fault Injection, ECU 제어/Reset은 수행하지 않았다.
Controller를 열지 않았으며, 향후 application TX0만으로 하드웨어 ACK가 없는
완전한 Listen-only라고 주장하지 않는다.
기존 Adapter/GUI는 별도 listen-only 강제를 적용하지 않는 계약을 유지한다.
CAN/LIN ID·Signal·FaultCode·Timeout·DBC/Matrix/Route/Firmware 변경 없음.

## 이번 Software 회귀 (Hardware와 분리)

| 시험 | 실제 결과 |
|---|---|
| 전체 pytest | **517 passed in 58.98s**, 기존517 유지, 실패/skip 없음 |
| CLI 별도 회귀 | **140 passed in 0.80s** |
| pip check | No broken requirements found. |
| Windows Native | **9종 PASS**, 실제 Windows 창 + 기존 Mock/Fake TEST ONLY |
| Mock/Live Source 격리·오류·정리 | 기존 테스트/Fake Native PASS; 물리 Live 성공 의미 아님 |
| Software GUI 종료·Writer flush | PASS (Mock/Fake). 실제 USB device release는 NOT RUN |

Native 실제 결과:
- Raw: 실제 창/3회 Start-Stop/Clear/active close, Mock4 해제.
- Decode: TEST ONLY 명시 load/Raw/Cache/invalid/반복/close, Mock5 해제.
- Vehicle: -10.0/test_unit/Valid/Age/오류/Reload/close, Mock4 해제.
- ECU: 7카드/STD-EXT/Fault 관측/반복/Reload/close, Mock4 해제.
- Logging: JSONL5/CSV5, 기존 CLI bytes equal, 파일 보호/error restart/close.
- Fake Live: JSONL6/CSV7, CLI bytes equal, transport4 해제·application send0.
- Graph: Pause/Resume/Clear·Logging 동시, JSONL6, transport3 해제·send0.
- Fault: 필터/상세/기존 DBC Fake metadata/Source/Reload/close, JSONL11, transport3 해제·send0.
- Automation: 기존 Fixture의 11개 PASSED, expected mismatch FAILED, cancel/close CANCELLED,
  사용자 receiver/logger 유지, Live Source BLOCKED, send0.

CLI 회귀의 Mock/VirtualBus send 시험과 실 CAN 송신은 구분한다.
실기 송신은 하지 않았으며 Native Fake의 application send0을 실제 버스 측정으로 사용하지 않는다.
이번 시험은 .test-tmp/phase3i1-8a59aa75의 새 basetemp/증적 경로,
cacheprovider 비활성화·bytecode 비활성화 상태에서 실행했다.
로그·스크린샷·임시 파일은 Git 제외 대상이며 Hardware capture가 아니다.

## Hardware 준비 조건 및 추후 재개 절차

1. **장치 식별부터 재개**:
   CANable Pro USB를 실제 연결하고 Windows PnP의 VID/PID·장치명·Driver/Service/
   현재 Firmware 근거·실제 COM 또는 USB device identity를 읽기 전용 확인한다.
   USB-C 형태만으로 Backend를 정하지 않는다.
2. **점유 및 Backend 준비**:
   장치 점유 프로그램/포트 사용 상태를 확인하고 Firmware에 맞는 Backend를 선택한다.
   확인된 Channel만 사용한다. 필요한 패키지 설치는 별도 사용자 승인 후 진행하고
   현재 .venv import/pip check 및 실제 USB backend library/Driver 준비를 검증한다.
   추가 설치와 Firmware/Driver 변경은 현재 지시에서 금지된 상태다.
3. **물리 Gate C 사용자 확인**:
   CAN_H/CAN_L, 각 CAN Transceiver, 실제 종단저항, 기준 GND·절연 구조,
   ECU 전원, 실제 송신 노드, 각 노드 bitrate/Classical CAN/STD 설정을 확인한다.
   제조사/실제 회로의 접지·절연 기준을 따라 확인하며 소프트웨어만으로 PASS하지 않는다.
   Cluster에 실제 Flash된 Commit/버전과 실행 상태도 확보한다.
4. **승인된 RX 연결**:
   위 조건이 충족된 뒤 기존 GUI에서 Live·확인 Backend·확인 Channel·확인 bitrate로 연결한다.
   자동 Mock 전환 없는 연결 성공/실패와 오류 원인을 기록한다.
   application send·Replay·Fault Injection 없이 제한된 시간 수신한다.
   실제 연결 후 수신0일 때만 RX=0을 실측으로 기록하고 송신 ECU/배선/설정 근거를 조사한다.
5. **Raw → 명시 DBC → Graph/Logging**:
   실제 RX ID/Format/DLC/timestamp/payload/출처를 확보하고 기존 Repository DBC를 명시적으로 로드한다.
   실제 DLC·Signal/Scale/Unit/정의된 Invalid/Reserved와 Decode Error/Unknown을 대조한다.
   unpack 성공은 Health/정책 승인 근거가 아니다. 근거 없는 Signal/Fault 의미를 만들지 않는다.
   실제 Signal에만 명시 Graph 매핑, CSV/JSONL exclusive-create/flush/close를 검증한다.
   실제 Frame이 없으면 후속 Graph/Logging은 NOT RUN.
6. **Cluster / 종료 비교**:
   동일 실 CAN Frame·확인된 Flash 버전일 때만 LCD와 PC를 비교한다.
   Stop/Disconnect/Close의 Receiver/Writer/device release를 확인한다.
   Fault Frame 부재를 시스템 No Fault로 판정하지 않는다.

Jira 초안(외부 등록/Done 미실행):
- **[HINT-48][Hardware Prep] CANable Pro 장치 식별/Backend Evidence** (PC/HW, 1일):
  USB/PnP/Firmware/Driver·점유/Channel 및 선택 dependencies 승인 근거 확보.
- **[HINT-48][Integration] CAN bus 준비 및 RX-only capture** (HW/송신 ECU/Cluster/PC, 1~2일):
  배선·절연/종단/전원·동일 bitrate·실 송신 확인 후 Raw/DBC/LCD/Graph/Logging 대조와 종료 증거.
- **[HINT-48][Interface Review] 실 Frame ↔ DBC/ECU 의미 정합성** (CAN/VCU/Gateway/Cluster/PC):
  실제 불일치 발견 시 별도 Issue/상대 담당자 리뷰. 이번에 Interface 변경·승인 완료 없음.

## 보존 및 협업 상태

이번 Phase에서 VERIFICATION에 본 절만 추가했다. README는 Phase3H-3 내용 그대로다.
기존 Phase3H-3 VERIFICATION 및 모든 이전 기록은 바이트를 보존해 뒤에 유지한다.
Source·Fixture·기존517 테스트·pyproject·공통 DBC/Matrix/Routing/Requirements/Firmware,
D: 원본25개, 다른 Worktree·리뷰 문서·모든 브랜치 참조는 SHA 기준으로 보존한다.
현재 전체 Git 변경은 기존 문서2개뿐이며 Stage 비어 있음, HEAD/branch/이력 유지.
추가 패키지/Driver/Firmware 설치·변경, Git add/Commit/Push/PR/Merge/
Reset/Rebase/Fetch 및 Jira 등록/Done 미실행.
Phase3H-3 Fixture 배포 미승인/NEEDS_REVIEW 상태도 변경하지 않는다.

Hardware·실 CANable/ECU/Cluster·사용자 수동 Live·팀 담당자 코드 리뷰: **NOT VERIFIED**.
팀 고정 버전·배포 라이선스 승인: 미확정.
실기 Gate는 **BLOCKED / NOT RUN**, Software 회귀만 PASS이다.

---

# Phase 3H-3 Packaging / Fixture Distribution 검토 — 2026-10-14

**최종 판정: NEEDS_REVIEW.** 사용자는 TEST ONLY DBC가 **미승인**이며 자동 포함을 보류하도록 확인했다.
원 요청의 배포 승인 Gate를 적용하여 Package Data·Fixture 복사·importlib.resources 구현은 보류했다.
현재 Wheel은 기존 설정의 누락 원인을 확인하기 위한 **로컬 진단 산출물**이며 승인된 팀 배포본이 아니다.

기준 Branch PC-Diagnostic-Test / HEAD e5621aa9f156a0bcbc97190a64a1b0450eb237a8.
시작 상태 clean·Stage 비어 있음. 이번 변경은 README.md / VERIFICATION.md만이며
pyproject·Source·Fixture·Tests·공통 Interface·의존성은 변경하지 않았다.

## Gate 및 Inventory

- 사용자 확인: “아직 미승인 — 자동 포함을 보류하세요”.
- tests/fixtures/test_only.dbc: 프로젝트 합성 TEST ONLY 표기, cde2ebf/DHK, tracked,
  823bytes, SHA 9ff1750df33163d0b9591912f202be56dda2a61af9dd97fa398f5a2c2c13a93b.
- gui/demo.py: 기존 Fixture 예제의 payload 상수, 69f904c/DHK, tracked,
  675bytes, SHA db7899aa9545b8676f92322e493cf65756133c89ec1f43353e4507f434d8ef3b.
- gui/automation.py: Catalog11/Expected/입력 조합, e5621aa/DHK, tracked,
  9236bytes, SHA b222bafff19c299e839b8d0c30d9ef1fa02d09be488539ad57ff70b424707bc9.
- 별도 Scenario/Expected 파일·외부 DBC·새 합성 Fixture 없음.
- TEST ONLY 주석·Git author는 출처 근거이며 사용권/팀 재배포 승인 근거를 대체하지 않는다.
  명시적 PC Tool LICENSE/SECURITY 또는 조직 배포 승인 Evidence는 확인되지 않았다.
- 실제 소유·재배포 범위/담당자/날짜/Evidence 확보 전 자동 resource 포함 금지.
  A/B/C 비교·승인 후 설계·Jira 초안은 README Phase3H-3에 기록했다.

## 이번 실제 검증

| 항목 | 실제 결과와 범위 |
|---|---|
| 기존 설정 Wheel Build | PASS, 기존 backend를 새 src/pyproject/README 복사본에서 실행 |
| Wheel Inventory | **43파일 = Python38 + dist-info5**, DBC0. tests/가상환경/로그/screenshot/pyc 미포함 |
| 명백한 개인 경로·인증정보 패턴 | Wheel 전체 텍스트 검사에서 발견 없음; 정식 보안/라이선스 승인과 구분 |
| 승인된 Fixture 포함 | **보류 / 미구현**. 미승인 DBC를 복사/자동 포함하지 않음 |
| 표준 package resource locator | **미구현**. 현행 fixture_path 계약 유지 |
| 최종 외부 Clean Venv 기본 설치 | **PASS**, Python3.12.14, Wheel만 --no-index --no-deps로 설치, editable 아님 |
| 외부 Clean CLI/GUI 모듈 --help | PASS, exit0. GUI 창 실행 의미 아님 |
| 외부 Clean CLI/GUI 설치 entry --help | PASS, exit0. GUI 창 실행 의미 아님 |
| 외부 Clean pip check | No broken requirements found. 기본 의존성 없는 설치만 확인 |
| Worktree/CWD 독립 기본 import | PASS, -I 실행, site-packages에서 import; sys.path/module/CWD/resource 경로에 원 Worktree 없음 |
| 설치본 Catalog | **11개 로드 확인**, 실제 실행은 미검증 |
| 설치본 Fixture 누락 | **FileNotFoundError 재현**, 설치 환경의 Lib/tests/fixtures/test_only.dbc가 없음 |
| 설치본 GUI 창/11개 Scenario | **NOT VERIFIED / 보류**, PySide6/cantools/python-can extras 미설치·Fixture 미포함 |
| 팀원 PC 배포·사용자 수동 확인 | **NOT VERIFIED** |
| 기존 개발 전체 pytest | **517 passed in 49.34s**, 기존517 유지, 실패/skip 없음 |
| 기존 개발 CLI 별도 회귀 | **140 passed in 0.48s** |
| 기존 개발 Windows Native | **9종 모두 PASS**, 실제 windows/노출 창, Mock/Fake. 독립 Wheel 검증 아님 |
| 개발 .venv pip check | No broken requirements found. |
| 신규 pytest/Resource 구현 시험 | 추가하지 않음. Gate 보류로 제품 구현도 미수행; 진단 probe 결과와 구분 |
| Hardware·담당자 리뷰·팀 고정 버전·라이선스 승인 | **NOT VERIFIED / NOT VERIFIED / 미확정 / 미확정** |

### Build / Clean Install 환경

개발 .venv는 Python3.14.6/PySide6 6.10.3/python-can4.6.1/cantools44.2.1/pytest9.1.1을 유지한다.
해당 환경에는 setuptools/wheel/build가 없음을 확인했으며 재설치하지 않았다.
기존 Codex 작업 도구 환경의 Python3.12.14/setuptools84.0.0/wheel0.48.0을 사용해
setuptools.build_meta.build_wheel을 실행했다. 새 backend/build 패키지 도입·다운로드 없음.
Python 최소 버전 >=3.10, 기존 optional extras·entry point 및 package discovery를 유지했다.
3.10/3.11/다른 Python의 실제 실행을 검증했다고 주장하지 않는다.

먼저 프로젝트 제외 Temp의 새 Build 입력에서 Wheel을 생성하고 내부 기본 clean 설치를 진단했다.
이후 Worktree 밖 별도 쓰기 경로의 완전히 새 venv/CWD에서도 재검증했다.
sys.path에 원 Worktree/개발 src가 없고 설치된 site-packages의 pc_diagnostic임을 -I probe로 확인했다.
빌드된 Wheel SHA:
`efdcb2781601888d82c789460319dd63e2df0ae7f30ad6f994f5df500d8d5822`.
기본 설치에는 PySide6/cantools/python-can/pytest extras를 넣지 않았으며
GUI --help가 먼저 처리되는 것을 실제 확인했다. GUI runtime/Decode/Automation 실행 검증이 아니다.

초기 외부 설치는 exit0였으나 sandbox 기본 Temp를 정리하지 못하는 pip 경고가 있었다.
기존/타인의 Temp를 삭제하거나 설치된 개발 가상환경을 수정하지 않았다.
완전히 새 clean-venv-verified와 쓰기 가능한 전용 TEMP/TMP/TMPDIR로 재실행:
설치/진입점/pip check/isolated probe exit0, 경고 없음, 전용 Temp 비어 있음.
이 경고를 Fixture 재배포 승인이나 제품 CAN/GUI 결함으로 해석하지 않았다.

증적 식별:
- 기존 설정 Build 및 개발 회귀: .test-tmp/phase3h3-review-50e40f7c/.
- 개발 Native9종: 위 경로의 final-native/.
- Worktree 밖 최종 clean 진단: 작업용 외부 경로의 phase3h3-review-3f1286b4/
  clean-venv-verified 및 independent-cwd-verified.
- 진단 Wheel/venv/로그/screenshot은 승인된 배포본 또는 Git 업로드 후보가 아니다.
  문서·패키지에 개인 PC 절대 경로를 하드코딩하지 않았다.

### 현행 Wheel 전체 파일 Inventory

```text
pc_diagnostic/__init__.py
pc_diagnostic/__main__.py
pc_diagnostic/cli.py
pc_diagnostic/dbc_codec.py
pc_diagnostic/dbc_loader.py
pc_diagnostic/decode_service.py
pc_diagnostic/decoded_message.py
pc_diagnostic/frame.py
pc_diagnostic/interfaces.py
pc_diagnostic/logger.py
pc_diagnostic/monitor.py
pc_diagnostic/sender.py
pc_diagnostic/state_cache.py
pc_diagnostic/gui/__init__.py
pc_diagnostic/gui/__main__.py
pc_diagnostic/gui/app.py
pc_diagnostic/gui/automation.py
pc_diagnostic/gui/automation_view.py
pc_diagnostic/gui/buffer.py
pc_diagnostic/gui/connection.py
pc_diagnostic/gui/connection_view.py
pc_diagnostic/gui/decode_session.py
pc_diagnostic/gui/demo.py
pc_diagnostic/gui/ecu_observation.py
pc_diagnostic/gui/fault_history.py
pc_diagnostic/gui/fault_monitor_view.py
pc_diagnostic/gui/graph_canvas.py
pc_diagnostic/gui/graph_view.py
pc_diagnostic/gui/logging_session.py
pc_diagnostic/gui/logging_view.py
pc_diagnostic/gui/message_statistics.py
pc_diagnostic/gui/observation_view.py
pc_diagnostic/gui/receiver.py
pc_diagnostic/gui/scenario_runner.py
pc_diagnostic/gui/signal_graph.py
pc_diagnostic/gui/vehicle_status.py
pc_diagnostic/gui/vehicle_view.py
pc_diagnostic/gui/window.py
gateway_pc_diagnostic-0.1.0.dist-info/METADATA
gateway_pc_diagnostic-0.1.0.dist-info/WHEEL
gateway_pc_diagnostic-0.1.0.dist-info/entry_points.txt
gateway_pc_diagnostic-0.1.0.dist-info/top_level.txt
gateway_pc_diagnostic-0.1.0.dist-info/RECORD
```

Wheel에는 Production DBC/Matrix/Routing/Firmware·외부 자료·Capture·실제 ECU Secrets를 넣지 않았다.
기존 demo/automation.py의 Python 상수는 기존 모듈 내용으로만 포함됐다.
Metadata에는 별도 PC Tool License 승인 정보를 넣지 않았다. 라이선스 승인 완료를 주장하지 않는다.

### 개발 Native9종 이번 실행

| Native | 실제 결과 |
|---|---|
| Raw | PASS, 실제 windows/3회 반복/Clear/active close, Mock4 해제 |
| Decode | PASS, 명시 TEST ONLY/Raw/Cache/invalid/반복/close, Mock5 해제 |
| Vehicle | PASS, -10.0/test_unit/Valid/Age/오류/Reload/close, Mock4 해제 |
| ECU | PASS, 7카드/STD-EXT/Fault 관측/반복/Reload/close, Mock4 해제 |
| Logging | PASS, JSONL4/CSV4, 각각 기존 CLI bytes equal, 파일 보호/error restart/close |
| Fake Live | PASS, JSONL6/CSV8, CLI bytes equal, transport4 해제·application send0 |
| Graph | PASS, Pause/Resume/Clear·Logging 동시, JSONL10, transport3 해제·send0 |
| Fault | PASS, 필터/상세/기존 DBC Fake metadata/Source/Reload/close, JSONL9, transport3 해제·send0 |
| Automation | PASS, 기존 Fixture로 11개 PASSED; expected mismatch FAILED, cancel/close CANCELLED, Live BLOCKED, 사용자 receiver/logger 유지, send0 |

위 결과는 **기존 개발 Worktree + 기존 .venv**의 회귀이다.
설치본 11개 Scenario PASS·물리 CAN 수신·HIL/Fault 상태 승인 근거로 사용하지 않는다.
Mock/Live/Logger/Cache/Graph/Fault/Vehicle/ECU/Adapter·기존 Assertion 의미 변경은 없다.

## 보존·Open 및 재개 조건

변경 파일은 README.md / VERIFICATION.md 두 문서뿐이다.
모든 기존 Source/Test/Fixture·pyproject·DBC/Matrix/Routing/Requirements/Firmware,
D: 원본25개 및 다른 Worktree/리뷰 문서를 SHA 기준으로 보존한다.
Stage 비어 있음, Branch/HEAD/기존 이력 유지.
Git add/Commit/Push/PR/Merge/Reset/Rebase/Fetch/Jira 등록·Done 미실행.

Open:
1. TEST ONLY DBC 실제 사용권·팀 재배포 승인 Evidence — 사용자 미승인 확인, **NEEDS_REVIEW**.
2. 승인 후 package data/표준 locator/context 수명/read-only/missing 안내 구현.
3. 선택 extras 포함 clean GUI/11개 Scenario/PASS·FAIL·ERROR/Live 보호/종료 검증.
4. 신규 resource/Archive/installed package/CWD 테스트 및 기존517/CLI140/Native9 회귀.
5. 팀 고정 라이브러리·라이선스·팀원 PC·담당자 코드 리뷰·Production/HIL: 미확정/NOT VERIFIED.

승인 전까지 Fixture 자동 포함을 하지 않는다.
필요 시 B/C 방식도 별도 범위로 검토하지만 현재 제품이 지원한다고 주장하지 않는다.
README의 Jira 후보만 작성했으며 외부 등록·상태 변경 없음.
CAN/LIN Interface 변경은 없고 필요 시 상대 담당자 리뷰 필요 상태로 분리한다.
Packaging 구현 완료·배포 완료는 **아니다**.

---

# Phase 3H-2 Test Automation GUI 검증 — 2026-10-14

기준 Branch **PC-Diagnostic-Test**, HEAD **8f2b629c08f4754753d75c12cbd53647f12f0353**.
아래는 이번 실제 실행이며 이전 Phase3H-1의 466개 결과와 구분한다.
최종 판정은 **PASS (Mock/Fake software MVP)**이다. Hardware/담당자 리뷰 완료 의미가 아니다.

| 검증 | 이번 실제 결과 |
|---|---|
| 전체 pytest | **517 passed in 62.31s** — 기존466 + 신규51, 실패/skip 없음 |
| 신규 Automation 별도 | **51 passed in 15.37s** — 모델13 / Runner29 / GUI9 |
| 기존 CLI 별도 | **140 passed in 1.12s**, 기존 Phase1/2 7개 테스트 모듈 |
| CLI/GUI 모듈 --help | 두 모듈 exit0 |
| 설치 can-diag.exe / can-diag-gui.exe --help | 두 진입점 exit0 |
| pip check | **No broken requirements found.** |
| 실제 Windows Automation Native | **PASS**, windows QApplication/노출 창; 고정11개 시나리오 Assertion 전부 PASSED |
| Automation 음성/격리 검증 | 기대값 불일치 FAILED, 취소/Close CANCELLED, Live Source BLOCKED, 사용자 Mock Receiver/Logger 유지 |
| Automation 자원/TX | 모든 시험 transport shutdown1회·해제, Receiver/Writer/Timer 정리, application send 호출0 |
| 기존 Windows Raw Native | PASS, 3회 반복/Clear/active close, Mock4 해제 |
| 기존 Windows Decode Native | PASS, 명시 TEST ONLY/Raw/Decode/Cache/오류·반복/active close, Mock5 해제 |
| 기존 Windows Vehicle Native | PASS, -10.0/test_unit/3회 반복/Age/오류/Reload/active close, Mock4 해제 |
| 기존 Windows ECU Native | PASS, 7카드/STD-EXT/Fault 관측/반복/Clear/Reload/active close, Mock4 해제 |
| 기존 Windows Logging Native | PASS, JSONL5/CSV5, 각각 기존 CLI bytes equal, 파일 보호/error restart/active close |
| 기존 Windows Fake Live Native | PASS, JSONL5/CSV4, 기존 CLI bytes equal, transport4 해제·send0 |
| 기존 Windows Graph Native | PASS, Pause/Resume/Clear·Logging 동시, JSONL12, transport3 해제·send0 |
| 기존 Windows Fault Native | PASS, 필터/상세/TEST ONLY·기존 DBC Fake metadata, Source/Reload/Graph·Logging/close, JSONL12, transport3 해제·send0 |
| Native 전체 | **9종 PASS (신규 Automation1 + 기존8)**, 모두 실제 Windows 자동화 |
| git diff --check / 신규 Python 구문 | PASS; 신규 untracked Python 공백 검사 포함 |
| Credential 패턴 / Stage | 명백한 토큰·개인키 패턴 발견 없음, Stage 비어 있음 |
| 사용자 수동 Automation GUI / Hardware | **NOT VERIFIED / NOT VERIFIED** |
| 팀 고정 버전 / 담당자 리뷰 / 배포 라이선스 | **미확정 / NOT VERIFIED / 미확정** |

실행 환경은 기존 Worktree .venv의 Python3.14.6 / PySide6 6.10.3 /
python-can4.6.1 / cantools44.2.1 / pytest9.1.1이다.
패키지 설치·재설치·버전 변경·pyproject 변경·신규 의존성은 없다.
팀이 승인한 고정 버전으로 기록하지 않는다.

## 시험 경로와 관측 근거

시험은 git 제외된 **.test-tmp/phase3h2-19423d3b/**의 새 basetemp에서
`-p no:cacheprovider`로 실행했다. 기존 테스트 Temp/기존 사용자 로그를 덮어쓰지 않았다.
최종 Native9종은 위 경로의 **final-native/**에 시험 증적을 생성했다.
Automation 임시 Raw capture용 새 `hint48-mock-*` 하위 경로는 시험 종료 후 제거됐으며
증적 screenshot/기존 Native capture는 Git 추적/Commit 후보가 아니다.

새 시험 입력은 변경 없는 기존 tests/fixtures/test_only.dbc와 gui/demo.py의 payload이다.
Fixture SHA-256:
`9ff1750df33163d0b9591912f202be56dda2a61af9dd97fa398f5a2c2c13a93b`.
Frame은 ScenarioInput(MockCanInterface FIFO 조합) → 기존 ReceiveWorker → Buffer/
FrameObservation → MainWindow Raw/DecodeSession/Cache/View/Logger 경로를 통과했다.
별도 Signal Decode 알고리즘 또는 직접 service 호출로 GUI PASS를 만들지 않았다.

고정 기대값은 Raw 입력/Fixture 정의 및 기존 GUI 계약으로 선언했다.
actual은 처리된 Raw table, Cache, Vehicle 셀·ECU 관측·Fault History·Graph samples,
종료된 CSV/JSONL 파일에서 수집했다.
Expected와 Actual, Assertion result/reason, Scenario ID/start/end/state/error/cancelled,
cleanup_complete/hardware를 분리한다. 미관측 항목은 FAIL/NOT EVALUATED이며 주입 성공이 PASS 근거가 아니다.
Raw/Decode 실패 시 잘못된 프레임은 Raw에 남고 invalid Signal을 정상값으로 대체하지 않는다.

Automation Native는 실제 Run/Cancel/Clear 버튼과 결과 셀을 검사했다.
11개 Catalog 전부 PASSED, 기대값만 바꾼 Raw는 FAILED와 실제값/이유를 표시했다.
사용자의 Mock 수신과 Logger를 실행한 채 Graph 시험을 수행해 기존 Worker/Writer 계속 동작을 확인했다.
Live Source에서 버튼 비활성/direct 실행 ERROR, 실행 중 GUI Close에서 취소 후 정상 해제를 확인했다.
Native screenshot에서 TEST ONLY/Hardware NOT VERIFIED·Scenario 입력/기대값·PASSED/FAILED 화면을 확인했다.
사용자가 직접 확인한 결과는 이번에 없으며 **수동 Automation GUI는 NOT VERIFIED**다.

기존 Fault Native만 기존 저장소 DBC를 시험자가 명시적으로 로드해 Fake metadata 시험에 사용한다.
이번 Automation Catalog에는 Production FaultCode/ACTIVE/CLEARED lifecycle Assertion이 없으며
Fault History는 **Status Unknown**을 기대한다. 실제 ECU Fault 전파 검증이 아니다.

## 유한 실행·격리·정리 정책

- 사용자 Live Source에서는 모든 Automation 실행을 차단한다. 실제 Bus 생성/Bus.send·Replay 없음.
- 별도 hidden MainWindow(Automation 재귀 비활성), 유한 Mock/Fake input, 원래 Worker/Writer를 사용한다.
  사용자 Source/Worker/Cache/Logger를 시험 세션으로 교체하지 않는다.
- 사용자 Source/DBC 편집은 시험 중 잠기며 기존 Mock Receiver/Logger의 자동 중지/전환 없음.
- PC 내부 tick25ms / 실행5s / 정리3s, 입력8·Assertion16 이하, 최신 결과10개 메모리 상한.
  ECU Period/Timeout/Fault Threshold·CAN latency/jitter 측정값이 아니다.
- IDLE/RUNNING 및 PREPARING/OPENING/WRITER_OPENING/RECEIVING/STOPPING/CLEANING/FINISHED를 구분한다.
  최종 PASSED/FAILED/ERROR/CANCELLED; 취소된 Assertion은 NOT EVALUATED.
- 정리 제한 초과는 ERROR/cleanup_complete=False로 session 참조를 유지하고 Timer polling을 중지한다.
  Run/Clear 차단, Cancel/Close로 재시도; 이미 발생한 ERROR를 CANCELLED로 숨기지 않는다.
- Queue drain/flush/close는 기존 Logger 계약. 두 Raw Logging 시나리오는 각 2개 기록,
  closed/received/written/drop/unconfirmed=(True,2,2,0,0), 입력 Raw record와 파일 읽기 결과 일치.
- 일반 CAN CSV/JSONL schema/exclusive create/Append 미지원/Count/Queue/Drop 계약은 수정하지 않았다.
  시험 결과 Report 자동 저장·새 export schema 없음. 시험 임시 파일은 소유 폴더 경계를 검증해 정리한다.
- 사용자 Close는 격리 session cancel/cleanup 완료 후 기존 사용자 종료 경로를 다시 실행한다.
  UI 변경은 Qt main thread; blocking recv/write/Thread wait는 신규 GUI 처리에 추가하지 않았다.

## 실행 중 발견·수정한 문제

1. 초기 파이프라인 시험에서 Vehicle actual은 Ambiguous/No Data로 **FAILED**였다.
   신규 Runner가 기존 Vehicle Signal combo의 문자열 계약에 findData를 사용한 것이 원인이었다.
   Runner의 exact findText 선택만 수정하고 같은 기대값으로 11개 시나리오를 다시 통과했다.
2. 첫 신규 모델/Runner pytest는 30 PASS/11 FAIL이었다.
   11개 시나리오의 실제 Assertion/해제는 이미 PASS였으나 테스트가 deleteLater 후 삭제된
   QTimer를 조회해 RuntimeError가 발생했다. 새 테스트에 QObject validity/Timer 해제 검사를 적용했다.
   제품의 deleteLater 정리는 유지하며 기존 테스트를 변경/약화하지 않았다.
3. 신규 UI 미리보기 시험 1개는 정수 기대값515에 "515.0" 표시를 요구해 실패했다.
   실제 Catalog의 정수 표현을 확인하도록 새 시험만 보정했다. 값/관측 Assertion은 유지했다.
4. PREPARING signal에서 CSV 시험을 취소하는 경계 시험이 새 임시 폴더 잔류를 재현했다.
   CANCELLED 완료 전 cleanup_files를 수행하도록 신규 Runner 최소 수정.
   동일 회귀와 GUI9개 **10 PASS**, 이후 전체517/신규51/Native9종을 재실행해 통과했다.

기존 466개 테스트·Fixture/Common Interface가 실패했거나 이를 삭제/약화하여 해결한 것이 아니다.
CPU/CAN delay/jitter/frame loss 또는 실제 디스크 고갈/ACL 오류를 측정했다고 주장하지 않는다.

## 보존·Git·미완료 범위

이번 변경은 tools/diagnostic_GUI 아래 **신규7 / 수정3 / 삭제0**뿐이다.

신규:
- src/pc_diagnostic/gui/automation.py
- src/pc_diagnostic/gui/scenario_runner.py
- src/pc_diagnostic/gui/automation_view.py
- tests/test_automation.py
- tests/test_scenario_runner.py
- tests/test_automation_view.py
- tests/gui_automation_native_smoke.py

수정:
- src/pc_diagnostic/gui/window.py
- README.md
- VERIFICATION.md

작업 전후 SHA-256 비교로 D: 원본25개, 다른 Worktree의 tracked 파일·HEAD/status 및
기존 리뷰 문서 보존을 확인했다. 리뷰 문서 SHA:
`751ecd803fc1866cc12a51ba2df4a93a64bd41f2cc441456eb9ea49b3178b975`.
기존466 테스트·Fixture·CLI/Adapter/Codec/Cache/Logger·공통 DBC/Matrix/Requirements/
Routing/ECU 추적 파일 해시는 변경 없다. main/develop/다른 담당자 branch와 origin 참조도 변경 없다.
현재 HEAD/branch 유지, Stage 비어 있음. Git add/Commit/Push/PR/Merge/Reset/Rebase/Fetch 및
Jira 등록/Done은 이번 구현 단계에서 수행하지 않았다.

미지원/Open:
- Production Fault 상태 판정/Active Fault 재구성·Fault Clear·ECU 제어·실제 CAN Replay/HIL Assertion.
- 외부 Script/사용자 파일 코드 실행/새 Report 포맷·Export·과거 결과 선택 화면.
- Fixture 없는 독립 wheel/배포 설치: ERROR; resource 포함/버전·라이선스 정책 검토 필요.
- 팀 고정 버전·배포 라이선스·Production Fault 의미 승인: 미확정/검토 필요.
- 담당자 코드 리뷰·사용자 수동 Automation GUI·CANable/ECU·고부하/장시간·디스크/ACL 실측:
  **NOT VERIFIED**. 테스트 통과를 팀 리뷰/Integration Merge/Jira Done으로 해석하지 않는다.

README에 Catalog v1/기대값·Source 계약, 사용법, 상태/정리 정책과 후속 Jira 후보를 기록했다.
CAN/LIN Interface 변경은 없으며 필요 시 별도 Jira와 **상대 담당자 리뷰 필요**로 분리한다.
Commit·Push는 미실행이며 별도 사용자 승인 후 진행해야 한다.

---

# Phase 3H-1 Fault Monitor 검증 — 2026-10-14

기준 Branch PC-Diagnostic-Test, HEAD 96d2cbc4f2a1dee605bfa43173e3e8db46c2084f.
아래는 이번 실제 실행이며 이전 Phase 기록과 구분한다.

| 검증 | 실제 결과 |
|---|---|
| 최종 전체 pytest | **466 passed in 32.60s** — 기존410 + 신규56, skip 없음 |
| 신규 Fault 모델·GUI 별도 | **56 passed in 3.72s** — 모델40 / UI16 |
| 최종 CLI 별도 회귀 | **140 passed in 0.51s** |
| Windows Fault Native Smoke | actual windows QApplication/창 노출, Mock/기존 DBC Fake TEST ONLY, 필터·상세·반복 Start/Stop·Source/DBC 격리 PASS |
| Fault Timestamp/Decode | Missing/Reversed 이력 유지, Status Unknown, Decode Error Raw/DLC/Payload 보존 PASS |
| Fault 동시 실행 | Graph/Logging 동시 진행, Clear History 후 Raw/Cache/Graph/Logging 유지 PASS |
| Fault Native 해제 | Active Close Receiver/Writer 종료, Fake3 해제·application send0, GUI/Graph timer 정지 PASS |
| Fault Native Raw Logging | 최종 Fake JSONL8개, 읽은 수=written, closed 확인 |
| 기존 Windows Native7종 | Graph/Raw/Decode/Vehicle/ECU/Logging/Fake Live 전부 PASS |
| Graph Native | Mock/변화하는 Fake Graph, Pause/Resume/Clear, JSONL9개, Fake3 해제·TX0 |
| 기존 Logging Native | JSONL5/CSV4, CLI bytes equal, 파일 보호·error restart·active close PASS |
| 기존 Fake Live Native | JSONL6/CSV11, CLI bytes equal, transport4 해제·TX0 |
| CLI/GUI 모듈·설치 entry point | help4종 정상 |
| pip check | No broken requirements found. |
| git diff --check / 신규 Python 구문 | PASS (최종 점검) |
| 사용자 수동 Fault GUI | **NOT VERIFIED** |
| CANable Pro / Cluster / ECU, 고부하·장시간 | **NOT VERIFIED** |
| 팀 고정 버전 / 담당자 리뷰 / 배포 라이선스 승인 | **미확정 / NOT VERIFIED / 미확정** |

pytest는 기존 Worktree 가상환경, cacheprovider 비활성화와 Git 제외 대상
.test-tmp/phase3h1-*의 새 쓰기 가능 basetemp에서 실행했다.
기존410개 테스트·TEST ONLY DBC·공통 DBC/Matrix/Requirements/Route/ECU 및
CLI/Codec/Cache/Adapter/Logger는 수정하지 않았다.
새 Native는 기존 TEST ONLY Fixture를 사용하며 FaultCode 시험에서만 기존 저장소 DBC를 명시적으로 읽는다.
Payload는 기존 Encoder로 만든 Fake TEST ONLY 값이며 실제 ECU Fault/CAN 검증이 아니다.
Native screenshot에서 명시적 Fault_Status/0x310 STD, TEST ONLY Source, Order/RX Run,
Timestamp unknown/역전, Decode Error, Status Unknown 및 상세 Raw/Decode 분리 화면을 확인했다.

## 검증 범위

- FrameObservation 결과 재사용 및 codec 호출 수=처리 프레임 수; refresh 재Decode 없음.
- 명시적 typed 채널/Message/ID/STD·EXT/source 확인, 중복 metadata Ambiguous, 자동 연결 없음.
- TX/error-mask/비선택 Message 제외; RTR/길이/processing 오류 Raw 유지, Cache backfill 없음.
- 숫자·Unit·Choice·Payload·Timestamp/출처 immutable history, 반복 Frame 독립 순서 보존.
- FaultCode0/Recovery1/INVALID255도 Status Unknown; No Data와 No Fault 구분.
- FaultCode/Channel(0/'0'/None)/Message/Decode Error 필터, 상세 조회·eviction/필터 후 상세 정리.
- History500/Source32, oldest eviction count, removed-source timestamp 정리, UI Buffer drop 별도.
- Clear History는 모델만 초기화; Cache/Raw/Graph/파일·Writer 유지. 매핑·순서 번호 유지.
- DBC Reload(실패 포함), Mock/Live/Backend/Channel 변경 시 이력/매핑/상세/필터 격리.
- 같은 Source Start/Stop run 구분 및 이력 유지; prior backlog는 RX Run Unknown.
- Fake transport 오류/재접속, 반복 Start 새 관측, 중복 Start 방지, active close cleanup.
- RX 중 Source·immutable 상세 유지, 추가 Fault Thread/Timer 없음; Qt UI main-thread 사용.
- 기존 Signal Graph·Raw/Signal/Cache·Vehicle/ECU·Logging·Mock/Live·CLI 전체 회귀.

## 조사·미확정 범위

근거 파일/행/참조 Commit과 확정/초기값-수정 가능/측정 후 확정/검토 필요/TBD/Open 분류는 README Phase3H-1에 기록했다.
Fault_Status ID/STD/DLC/Signal은 DBC와 메시지 정의서 수치가 일치한다.
D07-9 이전 미확정, Routing OPEN Fault Signal, DBC proposal/Workbook 리뷰 gate,
후속 사용자 Gateway 설계의 확정 정책/Open transport 계약을 서로 다른 결정 상태로 구분했다.
ACTIVE/CLEARED Choice는 metadata로만 표시; 현재 Fault 상태 머신/Severity/발생·해제 매칭/Replay 미구현.
ECUOffline은 node enum이며 임의 bitmask로 해석하지 않는다.
실제 최신 remote HEAD/실장/Flash/E2E는 이번에 검증하지 않았다.
Cluster/Gateway는 README에 명시한 기존 로컬 origin 참조를 읽었으며 fetch/switch/checkout하지 않았다.

## 실행 중 문제와 처리

- 초기 모델/UI51개(3.90s), 전체461개(28.39s), CLI140개(1.00s), Fault Native PASS.
- 화면/코드 검토 후 RX 시 source/상세 초기화 가능성을 보완하고 경계4개를 추가해55개로 확장.
  bounded view/evicted detail/None Channel/backend 변경/선택 유지를 검증했다.
  기존 테스트 실패·삭제·완화로 해결하지 않았으며 중간465개와 Native8종을 다시 실행했다.
- 신규 모델의 중복 metadata 첫 후보 선택과 removed-source timestamp 누적 가능성도 방어/회귀에 포함.
- 보완 명령1건은 Codex 자동 승인 검토 deadline timeout으로 실행되지 않았다.
  안전 여부 거절이 아니며 승인된 내부 최소 수정으로 1회 재시도해 정상 실행됐다.
  해당 지연을 테스트 통과 또는 제품 Hardware 결함으로 기록하지 않았다.

- 최종 UI 리뷰에서 mapping 오류 안내가 다음 refresh에 사라지는 가능성을 보완하고 1개 회귀를 추가했다.
  정상 재시도/새 session까지 오류 안내를 보존한다. 전체466/신규56/CLI140을 실제 재실행해 PASS.
- 이후 Fault Native 1회가 Mock→Live 전환 직후 history isolation assertion에서 실패했다.
  재현4회 중1회는 Receiver/Writer 종료 flag 확인 후에도 UI controls가 다음 Qt event까지 locked였다.
  disabled control의 직접 변경을 기존 ConnectionView가 정상 거부한 시험 동기화 문제로 구분했다.
  제품 Source 잠금 정책은 변경하지 않았고 신규 Native만 실제 can_change_source + Mode enabled를
  wait_until 이벤트 조건으로 기다리도록 수정했다. 기존 isolation assertion/결과 검증은 유지했다.
  동일 Fault 및 기존7종을 새 폴더에서 재실행해 최종8종 PASS. 실패 로그/중간 증적도 제외 Temp에 보존했다.

환경: Python3.14.6 / PySide6 6.10.3 / python-can4.6.1 / cantools44.2.1 / pytest9.1.1.
설치/버전/pyproject 변경 없음; 팀 승인 고정 버전으로 주장하지 않는다.
CAN/LIN Interface 변경 시 상대 담당자 리뷰 필요. Jira 후보만 문서화하고 외부 등록/Done 미실행.
Git add/Commit/Push/PR/Merge/Reset/Rebase 미실행; 기존 이력 유지.

---

# Phase 3G 검증 — 2026-10-13

기준 Branch `PC-Diagnostic-Test`, HEAD `c8d20b6f33660b81575f6dd0adacd29308cb3fbd`.
이번 절은 실제 Phase 3G 실행 결과이며 아래 이전 Phase 실행 기록과 구분한다.

| 검증 | 실제 결과 |
|---|---|
| 전체 pytest | **410 passed in 31.35s** — 기존367 + 신규43, skip 없음 |
| 신규 Graph 테스트 별도 실행 | **43 passed in 4.01s** (Qt 독립 모델30 + Graph UI13) |
| 기존 CLI 별도 회귀 | **140 passed in 1.12s** |
| Windows Graph Native Smoke | 실제 windows 창, Mock/변화하는 Fake Live TEST ONLY Graph, Pause/Resume/Clear, active close PASS |
| Graph Native Logging | JSONL7 프레임, 저장 수=written, Graph Pause/Clear 중 기록 지속 |
| Graph Native 해제 | Fake transport3개 정확히 해제, application send 호출0, Graph timer 정지 |
| 기존 Windows Native Smoke | Raw/Decode/Vehicle/ECU/Logging/Fake Live **6종 모두 PASS** |
| 기존 Mock Logging Native | JSONL5 / CSV5, 기존 CLI Logger byte 일치 |
| 기존 Fake Live Native | JSONL6 / CSV5, 기존 CLI Logger byte 일치, transport4 해제·TX0 |
| CLI/GUI 모듈·설치 진입점 | 도움말 실행 정상 |
| pip check | No broken requirements found. |
| 사람 수동 GUI / 실제 CANable·Cluster | **NOT VERIFIED / NOT VERIFIED** |
| 팀 고정 버전 / 담당자 코드 리뷰 | **미확정 / NOT VERIFIED** |

pytest는 cacheprovider 비활성화 및 Worktree의 제외 대상 `.test-tmp/phase3g-*` 신규 쓰기 가능 경로에서 실행했다.
Windows screenshot은 Qt widget 렌더링이며 native windows QApplication와 창 노출을 확인했다.
Fake Live Graph screenshot에서 TEST ONLY Source, 선택 Channel/0x651 STD/Measurement,
test_unit, 숫자 값·원래 Timestamp·Sample 계수·경과 시간축과 변화 곡선을 실제로 확인했다.
이는 Hardware 수신·실제 차속/RPM·손실률·성능 KPI의 증거가 아니다.

## 구현 계약 검증

- MainWindow는 기존 DecodeSession.process 반환 FrameObservation만 Graph에 전달한다.
  자동 테스트에서 codec 호출 수가 기존 처리 프레임 수와 같고 Graph refresh로 Sample이 늘지 않는 것을 확인.
- 명시적 Channel/Message ID/STD·EXT/Signal 선택; 같은 Signal 이름의 TEST ONLY metadata 중복에도 자동 연결 없음.
- typed Channel 0/'0'/None, 동일 숫자 ID의 STD/EXT, 다른 Message, TX/error-mask 분리.
- 원래 숫자 값/단위/Timestamp와 Source/session 식별자 보존.
- sample 상한1000, oldest-history 제외, 수신 Buffer drop와 Graph history/time/value 제외 계수 분리.
- Pause는 곡선 snapshot만 정지하고 수집/Decode/Logging 유지. Resume은 최신 유한 Buffer 표시.
- Clear Graph는 Graph만 초기화; Raw/Cache/Statistics/Logging 유지. 선택 Unit과 No DBC 상태도 보존.
- DBC Reload/Source 변경 시 선택·곡선·Pause snapshot 초기화. 같은 Source 반복 Start/Stop에는 새 sample 증가.
- Decode 실패, mux Signal 부재, 비숫자/NaN/Infinity/큰 수 경계 모의, timestamp 누락/역전 처리 확인.
  기존 DecodedMessage가 거부하는 값은 경계 모의로 Graph 방어를 시험하며 upstream 계약을 변경하지 않음.
- 오류/누락 뒤 segment를 끊고 Cache의 이전 정상값을 새 점으로 생성하지 않음.
- renderer의 큰 유한 수 좌표 정규화, Qt main-thread 호출 및 종료 후 timer 정리 확인.
- 기존367개 테스트·TEST ONLY DBC·Transport/Codec/Cache/Logger/CLI 소스는 수정하지 않음.

## 환경·라이선스·미검증

기존 Python3.14.6 / PySide6 6.10.3 / python-can4.6.1 / cantools44.2.1 / pytest9.1.1을 사용.
새 외부 라이브러리 추가/설치, pyproject 의존성 변경, USB driver/firmware 변경은 하지 않았다.
QPainter는 기존 PySide6 QtGui에 포함된다. 로컬 PySide6 metadata:
LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only. 팀 배포 라이선스 검토 완료는 NOT VERIFIED.

실제 backend Clock 정확도·실제 CANable/Cluster·사용자 수동 Graph 확인·고부하/장시간/손실률·KPI는 NOT VERIFIED.
Numeric enum/Invalid/Reserved 값의 표시와 ECU Healthy/Fault/물리 유효성 판단은 구분한다.
CAN/LIN Interface/DBC/Matrix/Requirements/ECU 수정은 없으며 변경 필요 시 상대 담당자 리뷰가 필요하다.
다중 Signal·Graph Export·영구 설정은 구현하지 않았다. Git add/Commit/Push/PR/Merge는 실행하지 않았다.

---

# Phase 3F 검증 — 2026-10-13

기준 HEAD `8390c6f9c21a5e5343db7892d4c978e07fe448fb`, Branch `PC-Diagnostic-Test`.
이번 절은 실제 재실행 결과이며 아래 이전 Phase 기록과 구분한다.
실제 CAN 장치를 열거나 송신하지 않았고 Python 패키지/USB driver/firmware 설치도 하지 않았다.

| 검증 | 이번 결과 |
|---|---|
| 전체 pytest | **367 passed in 22.13s** — 기존321 + 신규46, skip 없음 |
| 기존 CLI 별도 회귀 | **140 passed in 0.58s** |
| CLI/GUI 모듈 도움말 | 기존 명령과 새로운 Mock/Live GUI 설명 정상 |
| 설치 진입점 | can-diag.exe / can-diag-gui.exe --help 정상 |
| pip check | No broken requirements found. |
| Windows Fake Live Native Smoke | windows platform, 실제 창 노출, Decode/Cache/Vehicle/ECU/Fault, STD/EXT 통계, active close 통과 |
| Fake Live 파일 | JSONL4 / CSV6 프레임; 동일 Raw의 기존 CLI Logger bytes 일치 |
| Fake Live 해제·TX | transport4개 정확히 해제, application send 호출0 |
| 기존 Windows Raw/Decode/Vehicle/ECU/Logging Native Smoke | 5종 모두 PASS, Mock TEST ONLY |
| 기존 Mock Logging Native | JSONL5 / CSV4 프레임, CLI bytes 일치, 기존 파일 보호 및 active close 통과 |
| 사람 수동 GUI / 실제 CANable·Cluster | **NOT VERIFIED / NOT VERIFIED** |
| 팀 고정 버전 / 담당자 코드 리뷰 | **미확정 / NOT VERIFIED** |

자동 테스트는 cacheprovider 비활성화와 Worktree의 제외 대상 `.test-tmp/phase3f-*` 신규 경로를 사용했다.
Native screenshot은 Qt widget 렌더링 결과이며 실제 windows QApplication과 window exposure를 확인했다.
Fake Native Screenshot에서 Live/Injected backend/TEST ONLY 출처, -10.0/test_unit/Valid와 timestamp/age 표시를 확인했다.

## 검증한 계약과 범위

- 신규46개: Qt 독립 연결 설정/의존성19개 + Fake Live GUI27개.
- 기존321개 Source/Test 회귀를 유지하며 기존 테스트 파일과 TEST ONLY DBC는 수정하지 않았다.
- Live에서 Mock generator 호출을 실패로 주입하고 Fake send는 호출 즉시 실패하도록 하여 미생성·미송신을 검증했다.
- 기존 Raw 객체의 identity와 필드, typed Channel 0/'0', STD/EXT 및 timestamp 보존 확인.
- Decode 실패 시 Raw 보존, 마지막 성공 Cache 유지, Vehicle Decode Error 표시 확인.
- 같은 Source Stop/Start/Clear의 기존 정책 보존. Source 변경은 Cache·매핑·통계를 초기화하고 명시적 DBC 정의만 유지.
- Source/DBC 잠금, open 도중 Stop/Close timeout, 반복 실행마다 새 수신과 새 transport 해제 확인.
- Receiver 종료 후 writer drain 중에도 Source 잠금을 유지하고 실제 writer 완료 후 UI가 자동 해제함을 검증.
- 장치 분리·없는 port·ImportError는 Fake 모의. 오류 표시·Logging drain·재시도·Mock fallback 없음 확인.
- shutdown 실패는 재연결을 차단하며 Close 내부 오류도 첫 Close에서 창을 유지하고 다음 Close로 종료.
- Live CSV/JSONL은 기존 RawCanLogger 계약을 재사용하며 생성/쓰기/flush/close는 Writer 소유.
  Queue512, drop-newest, written/unconfirmed, GUI Buffer drop 분리 정책은 변경하지 않음.
- 테스트 중 발견한 Mock DBC 안내 호환성 실패는 기존 테스트를 변경하지 않고 원래 안내를 보존하여 수정.
  Fake provenance 안내도 보완. 최종 전체 테스트에서 모두 통과.

## 환경과 미완료 항목

Python3.14.6 / PySide6 6.10.3 / python-can4.6.1 / cantools44.2.1 / pytest9.1.1 기존 환경 사용.
이는 팀 승인 고정 버전이 아니다. 실제 pyserial(serial), gs_usb, pyusb(usb)는 미설치 상태이며 설치하지 않았다.
선택적 slcan/gs-usb extra 및 backend 설치 안내를 추가했으나 새 extras 실제 설치는 NOT VERIFIED.
CANable firmware/backend/COM port/USB driver는 미확정. 500000은 분석한 Cluster 소스의 시험 기준이다.

application CAN TX 미호출과 hardware listen-only를 구분한다. 실제 ACK/error signaling,
CANable 분리/driver blocking/clock 정확도/처리량/무손실 기록, 실제 디스크·ACL 장애는 NOT VERIFIED.
Fault/Healthy/Offline 정책, 신규 Signal/Layout, Production 기본 매핑은 구현하지 않았다.
CAN/LIN Interface 변경은 상대 담당자 리뷰 필요이며 이번 작업에 포함하지 않았다.

담당자 코드 리뷰, 사용자 수동 확인, 실기 CANable/ECU 시험, Integration Merge, Jira Done은 완료로 주장하지 않는다.
Git add/Commit/Push/PR/Merge/Reset/Rebase는 수행하지 않았다.

---

# HINT-48 Phase 3E — 현재 파일 재확인 (2026-10-13, Asia/Seoul)

동일 재개 요청에 따라 현재 Git diff와 파일을 다시 조사하고 전체 검증을 새로 실행했다.
직전 완료한 9개 파일과 SHA-256이 일치했으며 이미 적용된 종료 오류 수정을 유지했다.
이번 실행에서 Source/Test의 추가 수정·재작성·삭제·초기화는 하지 않았다.
README의 Logging 사용/기존 Logger 계약/상한/오류/미검증 상태 설명은 현재 구현과 일치하여 유지했다.

| 이번 실제 재실행 | 결과 |
| --- | --- |
| 최우선 close-drain 회귀 단독 | **1 passed in 0.23s** |
| Logging Session/View | **35 passed in 5.79s** — Session21 / GUI14 |
| 전체 pytest | **321 passed in 11.28s** — 기존286 + 신규35 |
| 기존 CLI 별도 회귀 | **140 passed in 0.52s** |
| CLI/GUI 모듈·설치 진입점 | PASS |
| pip check | **No broken requirements found.** |
| Windows Logging Native Smoke | JSONL5 / CSV4프레임, CLI bytes 일치, 기존 파일 보호, 오류 후 재시작, Clear 중 기록 유지, active close, writer close/Receiver1개 해제 |
| Windows Raw/Decode/Vehicle/ECU Native Smoke | **4종 모두 PASS**, Mock4/5/4/4개 해제·미송신 |
| 이번 사람 수동 확인 / Hardware | **NOT VERIFIED / NOT VERIFIED** |
| 팀 고정 버전 / 담당자 코드 리뷰 | **미확정 / NOT VERIFIED** |
| Git add/Commit/Push/PR/Merge | **미실행** |

기준 Branch/HEAD: PC-Diagnostic-Test / `10f18cc5517890600f9d7282feb34cc9dd317a8d`.
종료 오류 테스트의 Condition/wait_for/snapshot 동기화는 Stop 이벤트 기반이다.
첫 Close의 오류 표시/창 유지/Receiver·Writer 종료와 재차 Close를 현재 코드 그대로 확인했다.
직전 실패 재현·수정 원인과 Jira 초안은 아래 과거 검증 절에 보존한다. 새 결함은 재현되지 않았다.
전용 evidence: `.test-tmp/phase3e-recheck-89e78ef12d5f4798b33c52d79672224d`.
캐시 비활성화 및 매회 새 basetemp 사용. 자동 Windows 실행을 사용자 수동 확인으로 기록하지 않는다.
D: 원본25개, 리뷰 Worktree/문서, 공통 Interface와 기존286개 테스트 보존을 재확인했다.
이 절만 추가했으며 앞선 검증 기록은 변경하지 않았다.

---

# HINT-48 Phase 3E — Logging GUI 재개·최종 검증 (2026-10-13, Asia/Seoul)

아래 기존 Phase 3D-2 및 이전 기록은 보존한다. 이번 절은 실제 실행 결과이다.
테스트 통과와 팀 고정 버전 승인/담당자 리뷰/Production 검증/Hardware PASS를 구분한다.

### 중단 지점 복원 및 관련 계약

- Branch PC-Diagnostic-Test / HEAD `10f18cc5517890600f9d7282feb34cc9dd317a8d`.
- 최초 Phase 3E 시작 clean. 재개 시 기존 변경은 수정2개(receiver/window), 신규5개
  (logging_session/view, test_logging_session/view, gui_logging_native_smoke).
  README/VERIFICATION의 Phase 3E 절은 당시 아직 작성하지 않은 상태였다.
- Git diff/실제 7개 파일과 마지막 회귀 테스트를 조사하고 삭제/초기화/재구현 없이 재개.
- D: AGENTS.md, 기존 Logger/README/테스트/RawCanFrame 및 GUI/Buffer/Decode/ECU 계약 확인.
- 핸드북의 PC Tool Logging 관련 p29–30은 archive/initial 문서이다.
  thin GUI/책임 분리와 CSV/JSON 저장을 참고했다. p30의 decoded schema는
  기존 Raw Logger schema와 다른 범위이므로 이번 사용자 요구대로 Raw 계약을 우선한다.
  공통 문서/Interface를 수정하거나 decoded schema를 Raw 공식 필드로 확정하지 않았다.
- RawCanLogger는 독점 x 생성, 매 write 후 flush, 기존 JSONL/CSV 9필드 및 close 계약 유지.
  원래 Logger/CAN Interface/DBC/Cache 소스 변경 없음.

### 마지막 종료 오류 — 테스트와 제품 원인 구분

- 변경 전 재개 재현: 마지막 테스트 **1 failed in 0.30s**.
  이전 세션에서도 **1 failed in 0.35s**로 동일 종료 동작을 확인했다.
- Condition 기본 RLock에서 snapshot의 재진입이 가능하다.
  wait_for는 Stop 상태 전이로 깨어나며 3초 무한 대기가 아니다.
  이번 재현은 timeout/deadlock/Qt 이벤트 부재가 아니라 window.close()가 True를 반환한 assertion 실패다.
- 제품 원인: MainWindow가 writer.wait() 종료 완료만 확인하고 LoggingSession Error를 검사하지 않아
  drain 중 write 오류를 사용자에게 보여주기 전에 창을 닫았다.
- 최소 수정: 종료 wait 후 Session Error 확인, Session generation별 첫 Close에서 창 유지·오류 표시.
  두 번째 Close에서는 종료 허용. 새 Session 오류는 새로운 알림으로 처리.
  generation은 내부 GUI 상태이며 Raw Logger 파일 schema에는 추가하지 않음.
- 회귀 test 강화: 첫 Close 뒤 Writer inactive/file close 확인/Receiver non-running,
  창/오류 표시 유지, 재차 Close 종료 검증.
- 수정 후 같은 마지막 테스트를 포함한 Logging 검증 **31 passed in 4.88s**.
  원래 실패 조건을 삭제하거나 완화하지 않았다. 신규 Phase 3E 오류-close 테스트를 더 엄격한 정책으로 보완했다.

### 실제 최종 실행 결과

| 검증 | 결과 |
| --- | --- |
| Phase 3E 시작 baseline | **286 passed in 11.32s** |
| 초기 Session 통합 | **305 passed in 10.90s** — 기존286 + 신규19 |
| 중단 전 최초 Logging 모델/GUI | **30 passed in 4.95s**, Windows Logging Smoke 통과 |
| 재개 후 오류/경합 추가 검증 | **35 passed in 5.35s** — Session21 / GUI14 |
| 최종 전체 pytest | **321 passed in 15.26s** — 기존286 + 신규35 |
| 기존 CLI 별도 회귀 | **140 passed in 0.61s** |
| CLI/GUI 모듈 및 설치 entry --help | 모두 PASS |
| pip check | **No broken requirements found.** |
| CSV/JSONL 계약 | 기존 CLI Logger와 byte 일치; 필드/순서/원래 Timestamp/null/Channel/RX-TX/RTR/Error 보존 |
| Open/Stop 경합 | Condition 이벤트 기반 모의 Open 실패, 접수2/미확인2/기록0으로 분리 |
| Write/flush 오류 | 성공 Count 미증가; bytes가 파일에 남아도 unconfirmed로 표시; 정상 handle 정리 |
| 기존 파일/권한/잠금 | 기존 파일 bytes 보존 실제 검증, PermissionError/공유 위반은 모의; 실제 ACL/디스크 고갈 시험 아님 |
| Queue/표시 Drop | 독립 저장/표시 경로, 상한과 새 입력 제외, 측정 계수 관계/INCOMPLETE 표시 확인 |
| Receiver 오류/Stop | Queue seal/drain, 파일 close, 종료/재시작 guard 확인 |
| 종료/반복 | 3회 새 Session, 중복 Start-Stop, active close, timeout 창 유지/재시도, drain 실패 알림 후 두 번째 Close |
| GUI main thread | UI snapshot 갱신만 main thread; 생성/write/close는 단일 별도 writer thread |
| Windows Logging Native | JSONL **5프레임**, CSV **4프레임**, 각각 CLI byte 일치; 기존 파일 보호/Error 후 재시작/Clear 중 계속 기록/active close, Receiver1개 해제·미송신 |
| Windows Raw Native | 실제 창/3회 반복/Clear/active close, Mock4개 해제 |
| Windows Decode Native | TEST ONLY 명시 load/Decode/Cache/오류 보존/active close, Mock5개 해제 |
| Windows Vehicle Native | TEST ONLY -10.0/test_unit/3회 반복/Cache/오류/Reload/종료, Mock4개 해제 |
| Windows ECU Native | 7카드/STD-EXT/Fault 읽기/3회 반복/Clear/Reload/오류/종료, Mock4개 해제 |
| 이번 Logging 사람 수동 확인 | **NOT VERIFIED** — 요청하지 않았으며 이전 Phase 수동 결과로 대신하지 않음 |
| 실제 CANable/ECU/Bus 및 Hardware 성능·KPI | **NOT VERIFIED** |
| 팀 고정 버전 / 담당자 코드 리뷰 | **미확정 / NOT VERIFIED** |
| Git add/Commit/Push/PR/Merge/Jira Done | **미실행** |

실제 설치는 Python 3.14.6, PySide6 6.10.3, python-can 4.6.1, cantools 44.2.1,
pytest 9.1.1로 이전 환경과 같음. pyproject/패키지 설치 변경 없음.
매회 새 GUID 테스트 Temp와 `-p no:cacheprovider` 사용; Temp 접근 오류 없음.
최종 evidence: `.test-tmp/phase3e-final-6503166321dc4ab0a0392960cf6591f3`.
테스트 파일은 이 경로/pytest 관리 Temp에만 생성, 정상 handle 정리 및 Git 제외 확인.
오류/부분 파일을 자동 삭제하지 않으며 증적은 Temp에 보존했다.
Mock 자동 Windows 창 실행과 사람의 수동 파일 선택/내용 확인을 구분한다.

### Logging 정책 / 제한

- GUI 시작/CAN Start만으로 자동 기록하지 않음. Receiver 실행 중 별도 Start Logging 필요.
- Receiver sink는 Raw 객체를 독립 Logging Queue와 기존 표시 Buffer에 전달.
  파일 I/O는 GUI/Receiver thread에서 하지 않음.
- 512 pending + 1 in-flight; 초과 시 새 프레임만 제외하고 queue_dropped로 표시.
  Buffer Drop은 다른 계수이며 파일 손실과 자동으로 동일시하지 않음.
- Received는 Recording admission 구간 입력, Logged는 write+flush 반환 건수,
  unconfirmed는 실패한 in-flight 및 잔여 queue. 파일에 부분/전체 bytes가 있을 수도 있음.
  Stop 완료 후 Received = Logged + Queue dropped + unconfirmed.
- Stop Logging/CAN Stop/Receiver 실패/Close는 admission을 닫고 기존 Queue를 drain.
  오류면 Error/원인/부분 파일 가능성 표시. Active writer는 참조 유지, 유한 wait 후 재시도.
- Clear/DBC Reload는 기존 화면/Cache 계약을 유지하고 Logging 파일/계수를 바꾸지 않음.
- 기존 파일은 empty라도 거부, Append/overwrite/상위 폴더 생성/자동 삭제 없음.
- fsync/전원 차단 내구성/rotation/실제 고속 무손실/디스크 용량/GUI Hardware backend는 후속 범위.
- Logger close 실패 시 Error/close confirmed=False로 표시하며 정상 종료를 주장하지 않음.
  OS 파일 I/O 자체를 강제 취소하지 않음.

### Jira 등록용 초안 — 외부 등록 미실행

**HINT-48 / Bug / 종료 drain 중 Logging 오류 안내 누락 (이번 수정 완료, 담당자 리뷰 필요)**
- 재현: Recording 상태에서 Close → Queue drain의 write 실패를 모의.
- 수정 전: Writer Error는 존재하지만 MainWindow.close() True, 창이 사라져 오류 확인 불가.
- 원인: Thread 종료와 Logger 성공을 동일하게 취급한 종료 경로.
- 수정 후: Session Error를 검사하고 첫 Close를 무시하여 원인/부분 파일 안내 표시,
  동일 Session에 재차 Close하면 종료. 실제 Receiver/Writer/파일 정리도 회귀에서 확인.
- 검증: 실패 재현0.30s, 수정 후 동일 회귀 포함 Logging35/전체321 PASS.
- 리뷰 대상: HINT-48 PC Tool 담당자. CAN/LIN 변경 없음.
- Jira 등록/상태 변경/메시지 전송은 하지 않음.

**HINT-48 / Open / 후속 검토**
- 핸드북 decoded export schema는 Raw Logger와 별개: 후속 Signal/quality Export에 대한 범위/승인 필요.
- 팀 고정 버전 및 내부 Receiver frame_sink/Logging Session API 코드 리뷰 필요.
- 실제 ACL/공유 잠금/디스크 고갈/고속 capture/네트워크 파일시스템 종료 지연은 실환경 후속 검증.
- blocking OS I/O의 강제 취소/무손실/파일 rotation을 이번 PASS로 확대하지 않음.
- 공통 Interface 변경이 필요하면 별도 Jira Issue 및 상대 담당자 리뷰 필요.

### 변경 / 보존

수정4개: README.md, VERIFICATION.md, src/pc_diagnostic/gui/receiver.py, window.py.
신규5개: src/pc_diagnostic/gui/logging_session.py, logging_view.py,
tests/test_logging_session.py, test_logging_view.py, gui_logging_native_smoke.py.
삭제0개. 기존286 테스트/Fixture 보존; 기존 Logger/CAN/DBC/Cache/ECU/Vehicle 소스 변경 없음.
D: 원본25개 및 다른 리뷰 Worktree/문서는 SHA-256 기준으로 보존 점검.
Common DBC/Matrix/Requirements/ECU·Interface 수치/Signal/Timeout/Fault 정책 변경 없음.
기준 HEAD와 PC-Diagnostic-Test 유지, Stage 비어 있음.
Commit 후보만 제시: `[feat][YYYYMMDD][권도형] add CAN logging GUI` (이번 실행하지 않음).

---

# HINT-48 Phase 3D-2 — Commit 사전 재검증 (2026-10-13, Asia/Seoul)

이번 절은 사용자 Commit·일반 Push 승인 후 **새로 실행한 Commit 전 검증**이다.
아래 구현 단계 기록의 Git 미실행 표기는 해당 단계의 과거 상태이며 보존한다.
Commit/Push의 실제 실행 결과와 Hash는 작업 완료 보고에서 별도 확인한다.

- 기준 Branch: PC-Diagnostic-Test / HEAD `979251af694a7f87e7553d023b2c6c81a5cf7482`.
- 실제 Worktree/origin/원격 HEAD 일치 확인. 다른 브랜치/공통 Interface 변경 없음.
- 실제 Git Status와 수정 diff 및 미추적 6개 내용 검토: 수정 3개/신규 6개/삭제 0개.
  모두 tools/diagnostic_GUI의 Phase 3D-2 GUI/관측/통계/Test/문서 범위.
- 기존 Worker, RawCanFrame, DecodeService/Codec/Cache와 책임 분리 유지.
  새 모델은 FrameObservation을 사용하며 CAN ID/Signal/Timeout/Fault Threshold를 정의하지 않음.
- Observed는 처리된 RX 관측 사실. 임의 Healthy/Online/Fault 판정 없음.
  명시적 typed Channel/STD-EXT 매핑과 LIN 개별 Signal 확인, Count/Drop 구분,
  Clear/Reload/유한 저장 및 Mock/TEST ONLY 표시 검토.
- 문서의 이전 사용자 확인(Start/Stop/Clear, VCU Observed, STD/EXT)은 기존 수동 증거.
  이번 자동 테스트 결과로 수동 확인을 대체하거나 다시 요청하지 않음.

| 이번 실제 재실행 | 결과 |
| --- | --- |
| 전체 pytest | **286 passed in 9.06s** — 기존 239 + Phase 3D-2 신규 47, 감소/skip 없음 |
| 기존 CLI 7개 테스트 모듈 별도 실행 | **140 passed in 0.49s** |
| CLI module/installed entry --help | PASS |
| GUI module/installed entry --help | PASS |
| CLI monitor --backend mock | 기존 TEST ONLY vector STD/EXT **2 frame(s)** 수신 |
| pip check | **No broken requirements found.** |
| Windows Raw Native Smoke | 실제 창/3회 Start-Stop/Clear/active close, Mock4개 해제·미송신 |
| Windows ECU/Statistics Native Smoke | 실제 창/7카드/명시적 TEST ONLY/STD-EXT/Fault 읽기/오류·Clear·Reload/3회 Start-Stop/active close, Mock4개 해제·미송신 |
| 사용자 수동 확인 | 기존 Start/Stop/Clear, VCU Observed, STD/EXT 확인 기록 유지 |
| Fault 값 사용자 수동 확인 | **NOT VERIFIED** |
| Hardware 및 실제 Fault 전파 | **NOT VERIFIED** |
| 팀 고정 버전 / 담당자 코드 리뷰 | **미확정 / NOT VERIFIED** |
| Production Signal/Fault 의미·출처 | **검토 필요 — 상대 담당자 리뷰 필요** |

전용 쓰기 가능 Temp: `.test-tmp/phase3d2-commit-56f12f1282a147ed8a86d247742acbbc`.
매회 새 basetemp와 `-p no:cacheprovider` 사용. Temp/스크린샷/JSONL/가상환경/캐시는 Commit 제외.
신규 Source/Test 수정 없이 검증 결과만 이 문서에 추가했다.
PR/Merge/Jira Done은 이번 승인 범위에 포함되지 않으며 미실행이다.

---

# HINT-48 Phase 3D-2 — ECU Health Observation 검증 (2026-10-13, Asia/Seoul)

이번 절은 실제 수행한 Phase 3D-2 결과입니다. 아래 과거 검증 기록을 보존합니다.
테스트 통과는 팀 리뷰/Interface 승인/Hardware PASS 또는 Jira Done을 뜻하지 않습니다.

### 기준 / Source of Truth

- Branch PC-Diagnostic-Test / 시작 HEAD `979251af694a7f87e7553d023b2c6c81a5cf7482`.
  시작 Working Tree clean, Stage 비어 있음.
- D: AGENTS.md, 팀 README/CONTRIBUTING, RawCanFrame/Worker/유한 Buffer,
  DecodeSession/SignalStateCache와 Vehicle Status 명시적 매핑 계약 확인.
- 메시지 정의서 v1.2: CAN_Message_Definition 6–11,
  CAN_Signal_Definition 24–29, LIN_Frame_Definition 6–11 읽기 전용 확인.
- 실제 DBC VERSION `0.4 - review-ready interface proposal`; 승인된 Production 기본값 아님.
  Gateway_Status에 GatewayAlive/QueueUsage, Fault_Status에 FaultCode/ECUOffline/
  RecoveryState/SystemState가 존재함. 구현의 기본값/임계값으로 사용하지 않음.
- Door/Light/Window는 LIN slave→Gateway 상태 경로이며 PC는 Gateway CAN 보고만 관찰 가능.
  Cluster의 독립 송신 Health Message를 현재 CAN DBC에서 확인하지 못함: 자동 생성/연결 없음.
- 기존 리뷰 IFC-REV-006 GatewayAlive Invalid=0xF와 정상 0..15 중복,
  IFC-REV-008 All/PC Receiver 범위 및 IFC-REV-007 PC/PC_TOOL 표기 질문 보존.
  이 리뷰 문서와 원본/팀 Interface 파일은 수정하지 않음.
- Fault layout/Choice의 일치는 승인/실제 전파 완료를 뜻하지 않음.
  상대 담당자 리뷰 필요 상태 유지.

### 구현 / Lifecycle

- Qt 독립 MessageStatisticsStore(512키 상한), EcuObservationModel,
  Qt EcuObservationView와 MainWindow 연결만 추가.
- Worker/RawCanFrame/DecodeService/Codec/Cache/Vehicle Public 계약 변경 없음.
  GUI는 기존 DecodeSession의 FrameObservation을 받아 decode를 반복하지 않음.
- 7개 프로젝트 ECU 카드: 직접 CAN 4개, Gateway 경유 CAN 3개.
  기본 연결 없음, 사용자 exact Message/Channel/ID/STD-EXT/출처 확인 필요.
  개별 LIN Signal 없으면 Not Available. 중복 출처는 Ambiguous.
- Count/시각은 처리된 RX 부분집합. ERROR/RTR와 STD/EXT/channel 구분, TX 제외.
- 통계가 꽉 차면 새로운 키 프레임만 제외하며 기존 count 유지.
  Buffer Drop과 capacity exclusion을 분리하여 No Data를 무수신/고장으로 해석하지 않도록 표시.
- Fault target의 기존 Decode 결과/Unit/DBC Choice만 표시.
  최근 실패 프레임 시각과 마지막 정상값 시각 구분, 별도 FaultCode/Recovery 의미 생성 없음.
- Clear: 새 화면의 통계/관측 및 Fault 값 표 초기화; 사용자 매핑과 기존 Cache/Vehicle 값 유지.
  다음 처리 RX부터 새 구간. Start/Stop는 기존 통계/매핑 유지하며 Age는 Stop 후 증가.
- DBC Reload 성공/실패: 새 화면의 매핑/통계/Decode 관측 초기화. 과거 Raw 재처리 없음.
- GUI timer는 bounded 처리 뒤 UI를 main thread에서 갱신. Qt per-frame signal 추가 없음.
  종료는 기존 Worker 정리 후 화면 입력/갱신 차단.

### 실제 실행 결과

| 검증 | 결과 |
| --- | --- |
| 수정 전 baseline | **239 passed in 8.36s** |
| 첫 통합(기존 239 + 모델 34) | **273 passed in 11.68s** |
| 신규 모델/GUI | **47 passed in 2.11s** — 모델 34, Qt Mock/offscreen 13 |
| 최종 전체 pytest | **286 passed in 10.92s** — 기존 239 + 신규 47 |
| 기존 테스트/fixture | 삭제·수정·약화 없음; 전체 실행에 포함 |
| ECU 상태 | 7카드/Not Configured/No Data/Observed/Not Available/Ambiguous/Not Defined/Decode Error 확인 |
| Raw 통계 | DBC 없음/Unknown/RTR/Error, channel None/int/string, STD/EXT, Count/DLC/원래 시각 확인 |
| Fault | 명시적 TEST ONLY 선택 후 -10.0/test_unit 및 DBC Choice ONE, 실패 시 마지막 정상값 시각 보존 |
| Drop/저장 상한 | 1000입력→488 Buffer drop/512처리; 테스트 상한2키에서 capacity 제외510 구분 |
| Lifecycle | Clear Cache 보존/새 통계 초기화, Reload 성공/실패 매핑 reset, 과거 세션 입력 거부 |
| Qt/Worker | main-thread UI, 매회 새 Mock/신규 RX, Start 중복 차단, 3회 Start/Stop와 active close |
| CLI | 모듈/설치 entry --help, 기존 CLI 140개 포함 전체 통과 |
| GUI | 모듈/설치 entry --help 성공, 실제 Windows 창 실행 |
| pip check | **No broken requirements found.** |
| ECU Windows Native Smoke | 7카드/명시적 TEST ONLY/STD-EXT 통계/Fault 읽기/3회 반복/Age/Clear/오류/Reload/종료, Mock4개 해제·미송신 |
| 기존 Vehicle Native Smoke | -10.0/test_unit/3회 반복/Cache/오류/Reload/active close, Mock4개 해제·미송신 |
| 사용자 Phase 3D-2 수동 확인 | **확인 완료(해당 항목)** — 사용자 Start/Stop/Clear 정상 확인 및 안내 후 VCU State=Observed와 CAN Message Statistics의 Format=STD/EXT 두 행 모두 확인. 자동 검증과 별도 기록. Fault 값 표시의 사용자 수동 확인은 **NOT VERIFIED** |
| Production ECU/Signal 의미·출처 / 실제 Fault 전파 | **검토 필요 / NOT VERIFIED** |
| CANable/ECU/실제 CAN 또는 LIN Bus | **NOT VERIFIED** |
| 팀 고정 라이브러리 버전 / 담당자 코드 리뷰 | **미확정 / NOT VERIFIED** |
| Git add/Commit/Push/PR/Merge/Jira Done | **미실행** |

실제 설치 버전: Python 3.14.6 / PySide6 6.10.3 / python-can 4.6.1 / cantools 44.2.1 /
pytest 9.1.1. 기존 pyproject 범위/설치 변경 없음. 다른 환경은 NOT VERIFIED.
매회 새 GUID basetemp와 `-p no:cacheprovider` 사용. 기존 Windows Temp 권한 오류 없음.
최종 native evidence:
`.test-tmp/phase3d2-final-4a22b49cc9c54ee998a46f2bfc075971`.
ECU dashboard/statistics/fault의 Qt widget 렌더를 시각 확인함. 실제 Bus Capture가 아님.
GUI 테스트는 기존 TEST ONLY fixture/vector만 사용하며 Production DBC/fixture 확장 없음.

### 협업 / Jira 질문용 초안 (외부 등록 없음)

새 구현에서 재현된 소스 결함은 없음. 다음은 미확정 Interface/검증 후속 질문이다.

**HINT-48 — ECU 관측 매핑 및 Fault 전파 근거 승인**
- 대상: HINT-41 Gateway, HINT-42 VCU, Motor/Cluster 담당자,
  HINT-45 Door, HINT-46 Light, HINT-47 Window, HINT-48 PC/Test.
- 질문: 각 ECU 표시의 승인 Source Message/Channel/STD-EXT/개별 Signal과 의미/보고 경로는 무엇인가?
  Cluster 독립 송신 정의나 관측 Evidence가 없다면 Not Configured 유지가 맞는가?
- LIN 개별 상태 수신의 freshness/validity가 CAN Signal에 전달되는지 확인 필요.
  Body_Status 수신만으로 세 ECU의 정상/실제 LIN RX를 주장할 수 없음.
- IFC-REV-006/008의 GatewayAlive Invalid/Receiver 문제를 기존 리뷰 절차에서 결정해야 함.
  PC GUI에는 sequence/timeout/invalid 판정 또는 임의 임계값을 추가하지 않음.
- Fault_Status 수신과 Cluster/PC 전파 완료, ECU 고장, Recovery 성공을 구분할 승인 capture/evidence 필요.
  이번 Generic Fault view는 DBC 값만 읽음. Fault Injection/ECU 제어는 후속 Task.
- Source 선택의 송신자 metadata와 물리 ECU identity를 동등한 증거로 취급하지 않아야 함.
- GUI 표시 정책(512 stats, 128 channel, 64 fault rows, Clear/Reload 구간)의 팀 코드 리뷰와
  Python/PySide6/python-can/cantools/pytest 고정 버전 확인 필요.
- Fault/Alive/Timeout Interface를 변경하려면 별도 Jira Issue 및 상대 담당자 리뷰 필요.
- 외부 Jira 등록/상태 변경/팀 질문 전송 미실행.

**HINT-48 — 내부 탭 발견성 검토 (사용성 질문, 결함 확정 아님)**
- 최초 사용자 응답: Start/Stop/Clear는 정상, VCU Observed/STD-EXT 행 위치는 찾지 못함.
- 안내 후 사용자 응답: "Observed와 STD/EXT 모두 확인". 해당 표시의 수동 검증 완료로 기록.
- 안내: ECU Health Observation → ECU Dashboard의 VCU State,
  같은 화면의 CAN Message Statistics → Format 열. Clear 후 Start 필요.
- 질문: 내부 탭의 발견성을 향후 UI 리뷰에서 확인할 필요가 있는가?
  자동 표시 검증과 이후 사용자의 수동 확인을 구분하여 기록함. 위치 안내 후 확인됐으며 UI 결함으로 확정하지 않음.
- 외부 Jira/팀 질문 등록은 승인되지 않아 초안만 작성.

### 변경 / 보존

수정 3개: README.md, VERIFICATION.md, src/pc_diagnostic/gui/window.py.
신규 6개: src/pc_diagnostic/gui/message_statistics.py, ecu_observation.py, observation_view.py,
tests/test_ecu_observation.py, test_ecu_observation_view.py, gui_ecu_native_smoke.py.
삭제 0개. 기존 239개 테스트와 TEST ONLY DBC는 변경하지 않음.
D: 원본 25개 및 다른 Worktree tracked 파일/리뷰 문서 SHA-256 보존 점검.
공통 DBC/Matrix/Requirements/ECU·타 담당자 Public Interface 변경 없음.
Commit 후보만 제시: `[feat][YYYYMMDD][권도형] add ECU observation and CAN statistics GUI`.
이번 작업에서 Stage/Commit/Push 또는 기존 이력 변경 없음.

---

# HINT-48 Phase 3D-1 — Vehicle Status 검증 (2026-10-13, Asia/Seoul)

이번 절은 현재 구현의 실제 검증 결과이며 아래 Phase 3C/3B/1~2 기록은 보존합니다.
테스트 통과는 팀 고정 버전 승인, 담당자 리뷰, Production 매핑 승인 또는 Hardware PASS가 아닙니다.

### 기준 및 관련 Source of Truth

- Branch `PC-Diagnostic-Test`, HEAD `6139ea401fbbe6da6ccdb1a3fbfc3ffbc583bf79`.
  시작 Working Tree clean / Stage 비어 있음.
- D: AGENTS.md, 팀 README/CONTRIBUTING, 기존 GUI/Worker/Buffer/DecodeSession 및
  SignalStateCache의 Channel/Message 키·원래 Timestamp·동일 clock Age 계약 확인.
- `docs/requirements/02__메시지_정의서_ver1.2.xlsx`의
  CAN_Message_Definition / CAN_Signal_Definition에서 차량 상태 관련 행을 읽기 전용으로 확인.
  CAN_Signal_Definition 6–8, 10–11, 14–17은 역할/출처와 상대 담당자 리뷰 필요를 기록합니다.
- `network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc`는 VERSION
  `0.4 - review-ready interface proposal`. 실제 Speed/RPM/Gear/Brake/Torque 이름/Unit/comment
  확인에만 사용했고 승인된 기본 매핑으로 등록하지 않았습니다.
- Speed는 Gateway 가상값, RPM/Gear/Brake는 복수 Message 출처,
  TorqueRequest와 TorqueApplied는 요청/적용값으로 구분됩니다. 역할을 추정해 합치지 않습니다.
- 기존 TEST ONLY fixture는 합성 Measurement/Mode/Counter/Reading/mux 정의입니다.
  Speed/RPM 의미의 Fixture를 생성하지 않았으며 모든 파일을 보존했습니다.

### 구현 및 정책

- 기존 Monitor/Signals 옆 Vehicle Status 탭 추가.
- `VehicleStatusModel`은 Qt 독립이며 값은 SignalStateCache 조회 결과만 사용.
  Unit은 사용자가 로드한 DBC, 상세 오류는 기존 DecodeSession 최신 처리 metadata에서 조회.
- `VehicleStatusView`는 Qt 메인 스레드에서 고정 6개 행을 갱신.
  Worker/Buffer/DecodeService/Codec/Cache의 기존 처리 계약은 유지.
- 기본 연결 없음. 사용자가 Channel(타입 포함), exact Message, exact Signal을 선택하고
  의미/출처 확인 후 Apply mapping. Source 변경 시 확인을 해제함.
- 미매핑/미확인/Message 불명확은 Ambiguous, exact 정의 없음은 Not Defined.
  정의된 완전한 연결의 미수신은 No Data. No DBC/Valid/Decode Error도 구분.
- Decode Error와 마지막 정상 RX 값/시각을 동시에 표시.
  Valid는 Decode 성공 Cache 존재만 뜻하며 timeout/min-max/ECU Health 판정이 아님.
- 기존 Clear/Start/Stop은 동일 DBC session의 매핑/Cache를 보존.
  성공/실패한 DBC 교체는 새 Cache와 함께 매핑/편집기 선택을 초기화.
- PC 소유 `DbcLoader.get_messages()` 읽기 전용 tuple 조회만 추가.
  기존 lookup/Decode/CAN Interface를 변경하거나 타 ECU Public Interface를 수정하지 않음.
  이 PC API 추가에 대한 실제 담당자 코드 리뷰는 NOT VERIFIED.

### 실제 실행 결과

| 검증 | 결과 |
| --- | --- |
| 수정 전 baseline | **201 passed in 5.28s** |
| GUI 최초 통합 후 기존 회귀 | **201 passed in 4.99s** |
| 최종 전체 pytest | **239 passed in 5.94s** — 기존 201 + 신규 38 |
| 신규 모델 | **26개**, Qt 독립, 기존 TEST ONLY DBC 사용 |
| 신규 화면 | **12개**, Mock/Qt offscreen, Channel None/int/string 포함 |
| 기존 201개 | 기존 Test/fixture 삭제·수정·약화 없음; 최종 전체 실행에 포함 |
| 상태/정의 | No DBC/Not Defined/No Data/Valid/Decode Error/Ambiguous 및 exact 이름/중복 확인 |
| 값·Unit·시각 | 기존 Measurement=-10.0, test_unit, 원래 RX Timestamp/반복 Cache 갱신 확인 |
| 출처 격리 | Message/Channel 및 channel 타입 분리; TX는 RX 값 생성 안 함 |
| 실패/복구 | length/codec/application 실패 후 정상 Cache 보존; 정상 RX 후 표시 복구 |
| Age | 미제공/역행 unknown, 정지 중 타이머 갱신, 큰 Age에도 값 삭제/Health 판정 없음 |
| Clear/Reload | Clear/Remove mapping/DBC 재로드 효과 구분, 실패한 교체도 이전 매핑 제거 |
| Qt/Worker | 메인 스레드 갱신, 매회 새 Mock/새 수신, 반복 Start/Stop, active close 정상 해제 |
| 유한 자원 | Vehicle 6행, 기존 512 buffer/500 Raw/100 batch 유지; 2000 입력 중 1488 제외·512 처리 구분 |
| CLI 진입점 | 모듈 및 can-diag.exe --help 정상; 기존 CLI 140개 전체 실행에서 PASS |
| GUI 진입점 | 모듈 및 can-diag-gui.exe --help 정상; 실제 정상 프로그램 창 실행 |
| pip check | **No broken requirements found.** |
| Raw native smoke | Windows 창, 3회 반복/Clear/active close, Mock 4개 해제·송신 없음 |
| Decode native smoke | Windows 창, TEST ONLY 명시적 load/Decode/Cache/오류 보존, Mock 5개 해제·송신 없음 |
| Vehicle native smoke | Windows 창/탭, TEST ONLY 직접 매핑, -10.0/test_unit, 3회 반복/Age/Clear/오류/Reload/active close, Mock 4개 해제·송신 없음 |
| 사용자 Vehicle 수동 확인 | **정상 확인** — 사용자가 DBC Observation의 -10.0/test_unit/Valid 표시 확인. Start/Stop/Clear 후 Age 증가를 관찰했고, 마지막 Cache 값/시각 보존에 따른 정상 동작임을 설명 |
| 실제 Speed/RPM/Gear/Brake/Torque 의미/수신 정확도 | **NOT VERIFIED** — 합성값을 실제 차량 값으로 표시/주장하지 않음 |
| 실제 CANable/ECU 및 Bus | **NOT VERIFIED** |
| 팀 고정 버전 / 담당자 리뷰 | **미확정 / NOT VERIFIED** |
| Git add/Commit/Push/PR/Merge | **미실행**; 기준 HEAD/브랜치 유지 |

실제 설치: Python 3.14.6 / PySide6 6.10.3 / python-can 4.6.1 / cantools 44.2.1 /
pytest 9.1.1. 설치/버전 범위/pyproject 변경 없음. 다른 Python/OS/라이브러리 조합은 NOT VERIFIED.
기존 Phase 3C 사용자 수동 확인을 이번 Vehicle 수동 확인으로 재사용하지 않습니다.

pytest는 매 실행 새 GUID 테스트 전용 basetemp와 `-p no:cacheprovider`를 사용했습니다.
최종 evidence 폴더:
`.test-tmp/phase3d-final-8b28108c29ba420dbf4a527450ef9ecc`.
Qt widget 렌더를 시각 확인했습니다. OS 전체/HW 캡처가 아닙니다.
Temp/렌더/캐시/venv/egg-info는 기존 Git 제외 규칙을 유지합니다.

### Trouble Shooting / Jira 질문 초안 — 외부 등록 미실행

이번 구현·테스트에서 재현된 소스 결함은 없습니다.
다음은 실제 관련 산출물과 미검증 상태에서 확인한 후속 질문입니다.

**HINT-48 / Vehicle 표시 의미·출처 검토**
- Signal 이름이 같은 RPM/Gear/Brake의 Source Message를 용도별로 확정할 담당자 리뷰 필요.
- Vehicle_Status.Speed는 Gateway 가상값이며 실제 속도 센서 측정으로 표시하면 안 됨.
- TorqueRequest(요청)와 TorqueApplied(적용)를 같은 기본 토크 값으로 혼합하면 안 됨.
- 메시지 정의서의 Gear 범위와 현재 review-ready DBC의 정상 범위 표기가 다름.
  기존 Interface Review 절차에 따라 의미/DBC/Matrix 정합성 검토 필요.
- 현재 모든 Production 기본 매핑을 비웠으며 GUI 사용자의 연결은 내부 표시 설정뿐.
- 팀 고정 Python/PySide6/python-can/cantools/pytest 기준 및 PC API 추가 리뷰 필요.
- 실제 신호/승인된 캡처 기반 표시 검증은 후속 Task. 이번에는 TEST ONLY 관찰 행으로만 검증.
- Fixture 확장/Production 산출물 수정/외부 Jira 등록/Jira Done 처리 미실행.

### 변경 및 보존

- 수정: README.md, VERIFICATION.md, src/pc_diagnostic/dbc_loader.py,
  src/pc_diagnostic/gui/window.py.
- 신규: src/pc_diagnostic/gui/vehicle_status.py, src/pc_diagnostic/gui/vehicle_view.py,
  tests/test_vehicle_status.py, tests/test_vehicle_view.py, tests/gui_vehicle_native_smoke.py.
- 기존 D: 원본 25개·다른 worktree tracked 파일·미추적 리뷰 문서를 SHA-256 기준으로 보존 검증.
- 팀 공통 DBC/Matrix/Requirements/ECU 코드 수정 없음. 기존 201개 테스트와 Fixture 보존.
- 실제 CAN 송신 기능이나 Interface 수치/Enum/Timeout/Fault 정책 추가 없음.
- 매핑 저장/자동 복구, 실제 GUI backend, 실제 Vehicle 캡처 시험은 후속 범위.
- 추후 Commit 후보: `[feat][YYYYMMDD][권도형] add vehicle status GUI` (이번 미실행).

---

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


## Phase 3K-1 — UI/UX Workspace (2026-10-17)

### Scope and environment

기준: PC-Diagnostic-Test / 5c3e95db4ff53117afb575f5b7337f6265bcd327.
기존 Interface 리뷰 Markdown 2개를 보존한 상태에서 UI 코드/신규 UI 테스트/문서만 변경했다.
기능/계획 대조 및 미구현 범위는 [UI Gap Analysis](docs/ui_ux_redesign.md)에 기록했다.
Python 3.14.6 / PySide6 6.10.3 / python-can 4.6.1 / cantools 44.2.1 / pytest 9.1.1을 실제 조회했다.
이 값은 설치 환경이며 팀 승인 고정 버전이 아니다. 패키지 설치/재설치/pyproject 변경 없음.

### Actual execution results

| 검증 | 이번 실제 결과 |
|---|---|
| 기존 테스트 유지 | 기존 테스트 파일 SHA-256 동일, Assertion 삭제/완화 없음 |
| UI 초기 변경 후 기존 suite | 569 passed / 69.89s |
| 중간 UI 전체 suite | 593 passed / 60.26s; 최종 스크롤/ID 보완 전 기록 |
| 최종 전체 pytest | **595 passed / 252.19s** — 기존569 + 신규 UI26, skip/fail 없음 |
| CLI 별도 회귀 | **140 passed / 1.07s** — 기존 7개 test 모듈 |
| CLI 모듈 / 설치 진입점 | python -m pc_diagnostic --help / can-diag.exe --help 종료0 |
| GUI 모듈 / 설치 진입점 | python -m pc_diagnostic.gui --help / can-diag-gui.exe --help 종료0 |
| pip check | 종료0, No broken requirements found |
| Windows Native 기존 10종 | **Raw / Decode / Vehicle / ECU / Logging / Fake Live / Graph / Fault / Automation / Driver PASS** |
| 신규 Windows UI Native | **PASS**, windows platform / 실제 창 노출 / 9개 Navigation / Mock 데이터 / Driver Mock·Live 차단 / 3회 Start·Stop / 활성 Worker Close |
| 작은 창 | Windows Native 및 offscreen 800×600 / 1024×768 접근 확인, 1280×920 offscreen/기본 Native 실행 확인 |
| Dashboard | No Data·Disconnected / 명시 TEST ONLY 매핑의 -10.0 test_unit·Observed / 오류 표시 / Source 전환·Clear·Reload 회귀 |
| Raw 표시 필터 | 검색·STD/EXT·Decode Error 필터 후 원래 행/Received/Cache 보존, 필터 중 파일 byte 계약 유지 |
| Graph/Logging/Automation 보호 | Native Graph Pause/Resume/Clear + Logging 동시 실행, CSV/JSONL CLI byte 동일, 11 Scenario PASSED 및 기대 불일치 FAILED·취소 CANCELLED 검증 |
| 종료 | 기존 Close 오류/Worker/Writer/Timer 회귀 포함, 신규 Dashboard/필터는 추가 Timer 없음 |
| 사용자 수동 UI 확인 | **NOT VERIFIED** — 이전 Phase 사용자 확인을 이번 UI 확인으로 재사용하지 않음 |
| 실제 CANable/ECU/Hardware | **NOT VERIFIED / NOT RUN**, Mock/Fake Native는 실기 PASS 근거 아님 |

전체 pytest는 cacheprovider를 끄고 매번 새 쓰기 가능한 .test-tmp/phase3k1-*/ 전용 basetemp로 실행했다.
Windows Native는 QT_QPA_PLATFORM을 제거한 별도 프로세스에서 실행했고 실제 app.platformName()=="windows"를 검사했다.
각 native 결과/캡처는 호출자가 지정한 외부 증적 폴더 native-final/results.json 및 하위 PNG/TXT에 저장했다.
전체 pytest의 실행 시간은 이번 실행 기록이며 UI 성능 KPI/고부하 기준으로 해석하지 않는다.

### Initial failures and retest

- 새 작은 창 테스트는 Offscreen 글꼴의 Header 최소 폭990 때문에 800px 조건을 검출했다.
  Header/배지 줄바꿈을 적용했으며 창 폭/실제 버튼 접근 Assertion을 유지했다.
- show_error 직후 Dashboard 요약이 다음 갱신까지 이전 상태인 문제는 동일 오류 이벤트에서 UI 요약을 갱신했다.
- 800×600 실제 캡처에서 탭 전체 외부 Scroll이 다른 페이지의 최소 폭/스크롤 위치를 Dashboard에 전달했다.
  페이지별 Scroll로 바꾸고 1열/수평 overflow 없음/독립 스크롤 회귀를 추가했다.
- EXT ID 표시 잘림은 실제 문자열·글꼴 폭 계산 및 tooltip으로 보완했다. ID/Format은 변경하지 않았다.
- 신규 Native 시험의 첫 실행은 숨겨진 매핑 페이지에 Apply 클릭을 보내 Observed를 기다리다 실패했다.
  시험에서 실제 페이지/버튼을 노출한 후 클릭하도록 수정했다. 기존 제품 통신 결함으로 분류하지 않았다.
- 위 보완 후 최종 전체595 및 Native 기존10+신규1을 재실행해 통과했다.
  초기 실패 기록은 초기 증적과 구분하며 최종 성공 기록으로 덮어 해석하지 않는다.

### Visual evidence

변경 직전: before-monitor.png / before-driver.png.
최종: native-final/workspace/의 dashboard-no-data.png, dashboard-mock.png,
driver-mock.png, driver-live-blocked.png, monitor-filter.png, monitor-decode.png,
page-1.png~page-9.png, driver-800x600.png, dashboard-800x600.png,
driver-1024x768.png, dashboard-1024x768.png.
실제 Windows QWidget.grab() 캡처를 직접 확인했다. 최초 디자인 시안/사람 수동 검증/실제 차량 측정이 아니다.
자동 생성된 화면·로그·테스트 파일은 소스 Commit 후보에 포함하지 않는다.

### Preserved boundaries and remaining work

기존 Driver model/Adapter/Validation/Live 차단, CAN Interface/CLI Sender/Codec/Cache/Logger,
Graph sample1000·render200ms 및 Automation 11 Scenario는 변경하지 않았다.
공통 DBC/Matrix/LDF/Routing/Requirements/ECU Firmware와 임시 Excel도 변경하지 않았다.
기존 두 리뷰 문서·D: 원본25개·다른 Worktree 파일/HEAD/Status·Git refs의 SHA-256/상태 대조를 수행했다.
Git Stage는 비어 있으며 Git add/Commit/Push/PR/Merge/Jira 등록·Done은 미실행이다.

Network/KPI 및 실제 Fault Injection은 미구현이다. Raw Pause·Decoded/Event export schema는 후속 검토다.
팀 고정 버전·배포/Fixture 승인·Production Signal/Health/Fault/Driver TX 계약은 미확정/검토 필요다.
담당자 코드 리뷰·OS Screen Reader·전체 DPI/테마·사용자 수동 사용성·실제 Hardware는 NOT VERIFIED다.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**이며 이번 UI 테스트 통과로 승인하지 않는다.

## Phase 3K-2 — UI Visual Polish / Layout (2026-10-17)

### Scope / actual environment

기준: PC-Diagnostic-Test / 5c3e95db4ff53117afb575f5b7337f6265bcd327.
3K-1 미커밋11개와 기존 Interface 리뷰2개를 보존하면서 UI만 변경했다.
아래는 이번 실제 실행 결과이며 3K-1의595 PASS 기록을 재사용한 결과가 아니다.

실제 조회: Windows / Python 3.14.6 / PySide6 6.10.3 / python-can 4.6.1 / cantools 44.2.1 / pytest 9.1.1.
새 라이브러리 설치·재설치·의존성/pyproject 변경 없음. 팀 고정 버전은 미확정이다.

### Final actual results

| 검증 | 이번 실행 결과 |
|---|---|
| 기존 suite 중간 확인 | 595 passed / 204.86s — 4열 Dashboard 최종 보완 전 기록 |
| 최종 전체 pytest | **616 passed / 212.36s** — 기존595 + 신규 레이아웃21, fail/skip 없음 |
| 신규 레이아웃 단독 | 21 passed / 6.54s — Header·9페이지 액션·접기·선택 버튼·소수 입력·Live 차단·Timestamp·긴 이름 |
| Dashboard 보완 후 UI 회귀 | 47 passed / 21.08s — 기존 Workspace26 + 신규21, 기존 Assertion 그대로 |
| CLI 별도 회귀 | **140 passed / 0.84s**, 기존 7개 모듈 |
| CLI/GUI 모듈 진입점 | python -m pc_diagnostic --help / python -m pc_diagnostic.gui --help 종료0 |
| CLI/GUI 설치 진입점 | can-diag / can-diag-gui --help 종료0 |
| pip check | 종료0, No broken requirements found |
| Windows Native 기존11종 | **11 PASS** — Raw / Decode / Vehicle / ECU / Logging / Fake Live / Graph / Fault / Automation / Workspace / Driver |
| 신규 Windows Layout Native | **PASS** — windows platform, 9페이지×3크기, 액션 전체 rect48건 접근, Alt+1~9, 방향키, 접기/펼치기, 38 PNG |
| 반복/종료 | Mock 3회 Start/Stop마다 새로운 수신, Clear, 활성 Worker Close 및 기존 Timer 종료 PASS |
| Driver | 기존 Combo/Validation/Adapter 사용, 37.5 소수값 유지, Brake/Gear/Window/Light 버튼, Mock Accepted/ECU Response 분리, Live TX 차단 PASS |
| Monitor/Decode | 기존 fixture STD/EXT·Channel·full Timestamp·선택 프레임·정상 Cache 유지, Raw 필터 기존 회귀 PASS |
| Graph/Logging | Pause/Resume/Clear, Logging 동시 실행, CSV/JSONL 기존 CLI byte 계약 및 기존 파일 보호 Native PASS |
| Automation | 기존 고정11 Scenario PASSED, 기대 불일치 FAILED·취소 CANCELLED 경로 Native PASS. 실제 HIL 결과 아님 |
| Git / whitespace | git diff --check 종료0, Stage 비어 있음. 신규 UI 파일 별도 Syntax/whitespace 검사 |
| 사용자 수동 UI 확인 | **NOT VERIFIED** — 이번 UI에 대한 사람의 확인을 받지 않았음 |
| CANable / ECU / Hardware | **NOT VERIFIED / NOT RUN** — Mock/Fake 시험을 실기 성공으로 해석하지 않음 |

pytest는 프로젝트의 쓰기 확인된 새 .test-tmp/phase3k2-*/ 하위 basetemp와 -p no:cacheprovider를 사용했다.
Native는 QT_QPA_PLATFORM 없는 별도 Windows 프로세스에서 실행했다.
설치 버전 조회에는 프로젝트 .venv를 사용했으며 패키지를 변경하지 않았다.

### Actual layout / visual evidence

| Qt 논리 창 크기 | 변경 전 본문 시작 | 변경 후 본문 시작 | 변경 전 viewport 높이 | 변경 후 viewport 높이 |
|---|---|---|---|---|
| 1280×920 | 260 | 173 | 548 | 701 |
| 1024×768 | 260 | 173 | 396 | 549 |
| 800×600 | 260 | 173 | 228 | 381 |

Header 본체는 93 logical px다. 본문 시작은 페이지 제목/상단 상세 버튼을 포함한 위치다.
viewport 증가는 빈 Activity 축소·여백 변화도 포함한다.
실제 Windows 배율은 devicePixelRatio=1.5이며 800×600 logical 창 캡처는 1200×900 physical px다.
모든 DPI/해상도 조합을 검증했다는 뜻이 아니다.

최종 외부 증적 폴더의 verified-native/results.json, verified-native/polish/results.json 및 PNG를 사용한다.
9페이지 각각 1280×920 / 1024×768 / 800×600의 실제 QWidget.grab() 캡처를 생성했다.
페이지 바깥 수평 overflow는 이 27개 기본 화면에서0이었다. 표 자체의 가로/세로 스크롤은 유지한다.

필수 캡처 파일(verified-native/polish/):

- dashboard-1280x920.png
- dashboard-800x600.png
- driver-mock-1280x920.png
- driver-mock-800x600.png
- can-monitor-mock-decode-1280x920.png

추가: dashboard-1024x768.png, 9페이지 기본 캡처, Vehicle/ECU/Fault mapping 접기,
Automation description 펼치기, 긴 Message/Signal 표시, Live TX blocked, Activity error 표시.
긴 이름 검증은 기존 TEST ONLY 항목의 표시 문자열 모의이며 DBC 파일/Signal 정의를 수정하지 않았다.
전체 이름은 선택 문자열/tooltip에 보존한다. 실제 긴 Production DBC 이름 전수 검증은 NOT VERIFIED다.
자동 캡처는 소스 Git 후보 밖의 증적 디렉터리에 보관하며 Commit 후보에 포함하지 않는다.

### Reproduced issues / final retest

- 초기 Header 재배치 후 offscreen에서 상태/카운터가 버튼과 같은 줄의 최소 폭을999px로 키웠다.
  상태/카운터를 DBC 요약 줄로 옮겨 800px 기존 Assertion을 유지했다.
- Dashboard 4열 도입 후 중간 전체 실행은 **615 passed / 1 failed**였다.
  실패는 기존 test_dashboard_small_width_and_scroll_are_independent_from_other_pages이며 단독으로 재현했다.
  실제 viewport623px, 카드 폭952px, 수평 scroll329px였다. 단순 대기 시간을 늘리지 않았다.
  실제 viewport 기준700px 전환과 최소 너비 고정 해제로 수정했다.
  중간 국소 재검증 실패도 최종 PASS와 구분한다.
- 위 수정 후 기존 Workspace26+신규21=47 PASS, 최종 전체616 PASS,
  기존 Native11종+신규 Layout Native1종을 다시 실행해 모두 통과했다.
  기존 테스트 삭제/조건 완화는 없다.

### Preservation / boundaries / remaining review

작업 전후 SHA-256 대조로 D: 원본25개, 기존 리뷰2개, 다른 Worktree의 파일/HEAD/Status,
임시 Excel, Git refs 및 기존 tracked tests의 보존을 확인했다.
3K-1 MainWindow·MonitorFilter·Workspace pytest/Native 파일도 그대로다.
Driver 기존 메서드는 UI refresh hook 추가를 제외하고 AST 비교상 동일하다.
기존 README/검증/설계 기록을 유지하고 이번 절을 추가했다.

통신/DBC/Signal Cache/ECU/Fault/Graph/Logging/Automation/Driver Model·Adapter는 변경하지 않았다.
공통 DBC/Matrix/LDF/Routing/Requirements/ECU Firmware와 CLI Sender도 변경하지 않았다.
0x600 미승인, VCU_Command(0x100) PC 송신 금지, TorqueRequest VCU 책임,
Driver Live TX Blocked / Interface Pending을 유지한다. CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**다.

미완료: 사용자 수동 사용성, 전체 DPI/OS 테마/Screen Reader, 실제 긴 Production DBC,
실제 CANable/ECU/고부하·장시간 환경은 NOT VERIFIED다.
팀 고정 버전/배포 라이선스/Fixture 재배포 승인·Production 의미/Interface Freeze는 미확정 또는 검토 필요다.
담당자 코드 리뷰 NOT VERIFIED, Integration Merge 미실행이다.
Network/KPI/실제 Fault Injection·Raw Pause·Decoded/Event export 등 기존 미구현 범위는 이번에 구현하지 않았다.
Git add/Commit/Push/PR/Merge/Jira 등록·Done은 미실행이다.

### Interrupted session resume verification (2026-10-17)

사용 한도 중단 후 현재 디스크를 짧은 읽기 전용 명령으로 조사했다.
Branch/HEAD는 위 기준과 동일하며 예상 밖 파일은 없었다. Source/Test 재구현·수정은 하지 않았다.

- 새 Temp와 cacheprovider 비활성화로 재실행: **616 passed / 252.94s**.
- CLI 별도 재실행: **140 passed / 1.25s**.
- CLI/GUI 모듈 및 설치 진입점 --help, pip check 재실행: 모두 종료0.
- 기존 Windows Native11종과 신규 Layout Native1종은 이번 재개에서 재실행하지 않았다.
  verified-native의12개 종료0 로그가 최종 코드 저장(01:54:38) 이후인01:55:48~01:56:47에 생성됨을 확인했다.
  9페이지×3크기, 주요 액션48건, Alt+1~9, 긴 이름, Mock/Live 차단 및 캡처38개 증적을 재검사했다.
- 소스/테스트/설정/Fixture94개 해시를 기록했고 재개 중 코드 변화가 없음을 확인했다.
- D: 원본25개, 리뷰2개, 다른 Worktree 추적 파일446개·HEAD·Status 및 Git refs가 작업 전 기준과 일치했다.
  기존 tracked 테스트 및 3K-1의 MainWindow/MonitorFilter/Workspace pytest·Native 파일도 보존됐다.
- README/VERIFICATION의 기존 기록은 바이트 단위로 보존했다.
  ui_ux_redesign.md의 기존 절은 LF 정규화 후 원래 SHA-256과 일치한다. 중단 전 CRLF 정규화가 있었으며 내용 손실은 없다.
- Git은 수정4개/미추적13개(리뷰2개 포함), Stage는 비어 있다. git diff --check 종료0.
  Git의 LF→CRLF 정책 경고는 확인했으며 Git 설정·Stage·이력은 변경하지 않았다.
- 재개 증적은 외부 UI 증적 폴더의 resume-fcaf5cb2/full.log, cli.log, pytest-results.json,
  entry-pip-results.json, code-sha256.json을 사용한다. 소스 Commit 후보에 포함하지 않는다.

사용자 수동 UI 확인·실제 CANable/ECU Hardware·담당자 코드 리뷰는 NOT VERIFIED다.
PC 입력 CAN Interface는 승인 대기, GUI Driver 실제 CAN TX는 BLOCKED다.
CAN/LIN Interface 변경은 상대 담당자 리뷰 필요이며 이번 UI 자동 검증은 승인 증거가 아니다.
Git add/Commit/Push/PR/Merge/Jira Done은 실행하지 않았다.


## Phase 3L-1 — Raw Pause / Observation Export (2026-10-17)

### Scope and current decisions

기준 PC-Diagnostic-Test / db11a9fdb0a0a5f7c208ec9f8aeb54cad98a8ce5.
이번 작업은 Raw GUI 표시 Pause/Resume, Decoded 및 실제 Fault 관측 snapshot CSV/JSONL Export다.
이전 Phase 기록은 그대로 보존했다. Source/Test 변경을 포함하는 이번 실행 결과이며 이전 PASS 재사용이 아니다.

사용자가 Resume을 **최신 최대500행 snapshot으로 한 번 교체**하도록 결정했다.
기존 수신 버퍼512/drop-oldest, drain100, 표500행은 유지한다.
추가 처리 이력은 immutable 참조500개로 제한하며 전체 History Replay/제외된 과거 프레임 복원은 없다.
Clear는 Pause 유지/Raw 이력 초기화/기존 정상 Cache 보존, Stop·다음 Start는 Pause 유지,
Source 전환은 기존 Gate에서 이력과 Pause 초기화, DBC reload는 기존 Raw 역사/Cache session 정책 유지다.

Decoded는 현재 DBC session의 보관 RX만 Signal별 행으로 저장한다. 실패는 값/Signal null,
이전 Cache backfill 없음. Channel 타입·STD/EXT·Source·Raw timestamp와 실제 Decode 상태 보존.
Fault는 기존 보관 관측 이력/Signal/unit/DBC choice/Status Unknown을 그대로 저장한다.
ECUOffline은 기존 Node Enum이며 FaultCode0을 Clear로, DBC Choice ACTIVE/CLEARED를 Event로 해석하지 않는다.
**기존 Event 저장소 부재로 Event Export는 Open / Not Implemented**다. 가상 Event를 합성하지 않았다.
범위/schema/파일 정책은 docs/observation_export.md에 기록했다.

### Actual environment / final execution

프로젝트 기존 .venv: Python3.14.6, PySide6 6.10.3, python-can4.6.1, cantools44.2.1, pytest9.1.1.
새 패키지 설치·재설치·pyproject 변경 없음. 위 설치 버전은 팀 승인 고정 버전이 아니며 미확정 상태다.

| 검증 | 실제 이번 실행 결과 |
|---|---|
| 기존 GUI/Decode/Logging/Workspace/Layout 국소 회귀 | 100 passed / 23.18s |
| 신규 pytest 단독 최종 | 43 passed / 33.96s |
| 전체 pytest 최종 | **659 passed / 231.70s**, 기존616 + 신규43, fail/skip 없음 |
| 기존 Phase1/2 CLI 별도 회귀 | **140 passed / 0.78s**, 초기 Commit tree의 기존 테스트 목록 사용 |
| CLI/GUI 모듈 --help | 각각 종료0 |
| 설치 can-diag / can-diag-gui --help | 각각 종료0 |
| pip check | 종료0, No broken requirements found |
| Windows Native 기존12종 | **12 PASS** — Raw/Decode/Vehicle/ECU/Logging/Fake Live/Graph/Fault/Automation/Workspace/Driver/Polish |
| 신규 Pause/Export Windows Native | **PASS** — windows platform, Mock 수신·Pause 독립성·Resume snapshot·CSV/JSONL·Fault enum·3크기·Source/Close |
| 사용자 수동 UI | **NOT VERIFIED** |
| CANable / ECU Hardware | **NOT VERIFIED / NOT RUN** |

pytest는 쓰기 확인된 새 .test-tmp/phase3l1-*/ 하위 basetemp와 -p no:cacheprovider,
QT_QPA_PLATFORM=offscreen을 사용했다. Native는 QT_QPA_PLATFORM 없는 별도 Windows 프로세스에서 실행했다.
실제 CAN backend는 신규 Native에서 차단했고 호출0회다. Mock/Fake를 실기 검증으로 해석하지 않는다.

### Tested contracts / actual files

- Pause 표/선택 고정 중 Rx·processed·Decode/Cache·Vehicle·Graph·Fault 정상 갱신.
  Raw Logger CSV/JSONL 파일은 실제 admission 프레임으로 만든 기존 Logger 참조와 byte 일치.
- 755개 관측 중 Resume 최신500개의 순서/중복 없음/제외된 선택 제거,
  다음 신규 행 반영, 누락·역전 Timestamp 원문 유지. Timestamp 정렬/재Decode 없음.
- 반복 Pause/Resume, Clear/DBC reload/Source 전환, 실제 Mock 반복 Start/Stop 및 활성 Close 자원 정리.
- Source는 per-record 고정. 모달 파일 선택 중 새 수신/Source 전환이 이전 snapshot을 바꾸지 않음.
- STD/EXT, int0/str"0"/null Channel, 실패·unknown·processing error·Timestamp 누락/역전 보존.
- TEST ONLY Measurement=-10.0/test_unit, 기존 DBC FaultCode0/ECUOffline1(VCU)/RecoveryState0(ACTIVE) 보존.
  Status Unknown 유지. 기존 DBC는 명시적 시험용 읽기 전용 사용이며 실제 ECU 응답이 아님.
- CSV UTF-8/CRLF 및 JSONL 행별 JSON 확인. Fault map/choice는 JSON object(CSV에서는 JSON 문자열).
- No DBC/No Data/Cancel은 새 파일 없음. 기존 파일 exclusive-create로 보호, overwrite/Append 미지원.
- 느린 Writer 중 GUI 처리 계속, 중복 Export 거부, Open/Write/Close 오류/부분 파일/Unconfirmed 검증.
  첫 Error Close에서 창 유지·원인 표시, 다음 Close 정상 종료. 미종료 I/O는 강제 취소하지 않음.
- Export Error는 Receiver/Raw Logger Error와 독립. 성공/실패는 Activity & Errors에서 확인 가능.
- 기존 LoggingSession writer 구현과 GUI timer를 재사용. 별도 Thread 구현/Timer 추가 없음.
  Export 작업 계수0/1과 Signal 행 수를 구분해 closed/no error일 때만 행 수 완료 메시지 표시.
- 기존 Automation11 Scenario, Driver Validation/Live TX 차단, CAN/CLI 계약은 기존 테스트와 Native 회귀 PASS.

### Initial findings and retests

신규 pytest 첫 실행은42 PASS/1 FAIL이었다.
Raw Logger written>=3만 기다린 시점에 GUI processed=2일 수 있었다. Writer/GUI는 독립 경로이므로
제품 오류가 아니라 신규 테스트의 동기화 오류였다. 실제 GUI processed>=3도 기다리도록 보완했다.
기존 Assertion 삭제/완화는 없고 신규43개 재실행 및 최종659개 전체 PASS다.

새 Native 첫 실행은 Source를 Mock / TEST ONLY라는 잘못된 문자열로 고정 비교해 실패했다.
실제 기존 Source는 Mock / DEMO ONLY다. 저장 값은 실제 Source와 일치했다.
새 Native를 관측 당시 실제 Source와 비교하도록 수정 후 새 출력 폴더에서 재실행해 PASS했다.
제품 Source 값/계약을 변경하지 않았다. 기존 Native12종은 모두 첫 실행 PASS였다.

신규 Native에서 저장한 예: Decoded CSV/JSONL 각15행, Fault CSV/JSONL 각4행.
수신 snapshot 시점에 따라 행 수는 달라질 수 있다. 실제 기록행과 snapshot.row_count 일치를 검사했다.
추가 fault-contract.jsonl은 기존 DBC의 실제 Node Enum/Status Unknown 보존 시험이다.
기존 Logger Native에서도 CSV/JSONL byte 호환성, 파일 보호/오류 후 재시작/활성 Close PASS다.

### Evidence / visual verification

외부 증적 폴더: hint48-phase3l1-20261017.
pytest-all.txt, cli140.txt, pytest-results.json, entry-pip-results.json,
native-final의 기존12개 로그 및 native-pause-export-recheck/result.txt를 사용한다.
native-final/results.json에는 신규 Native의 최초 실패도 남아 있다.
최종 통합 결과는 final-results.json에서 기존12개 PASS + 신규 재실행 PASS를 구분한다.

신규 Native 실제 QWidget.grab() 캡처:
- native-pause-export-recheck/paused-monitor-800x600.png
- native-pause-export-recheck/paused-monitor-1024x768.png
- native-pause-export-recheck/paused-monitor-1280x920.png
- native-pause-export-recheck/fault-export-800x600.png
- native-pause-export-recheck/fault-export-1024x768.png
- native-pause-export-recheck/fault-export-1280x920.png
- native-pause-export-recheck/live-not-connected-tx-blocked.png

800×600 Monitor 및 일반 크기 Fault 캡처를 시각 점검했다.
새 Pause/Export 버튼을3크기에서 스크롤하여 전체 rect 접근 가능함을 Native에서 확인했다.
기존 Polish Native는9페이지×3크기/주요 액션48건/Alt+1~9/긴 이름/Live TX Blocked도 다시 통과했다.
사용자 수동 사용성 확인이나 전체 DPI 검증으로 주장하지 않는다.

### Preservation / pending review

SHA-256 대조: D: 원본25개, 다른 Worktree 추적446개·HEAD·Status, 리뷰2개,
임시 Excel 및 Git refs가 작업 전과 동일하다. 기존 tracked pytest/Native 소스도 그대로다.
기존 README/VERIFICATION은 append로 보존한다. 공통 CAN/DBC/LDF/Matrix/Routing/Requirements,
Firmware, CLI Sender/Adapter/Codec/Cache/Logger 계약과 의존성은 변경하지 않았다.

팀 고정 버전/배포 라이선스/Fixture 재배포·Production Interface 의미/Freeze는 미확정 또는 검토 필요.
담당자 코드 리뷰, 사용자 수동 UI, 실제 ACL/디스크 고갈, 고부하·장시간 무손실은 NOT VERIFIED다.
0x600 미승인 후보, Driver Live TX BLOCKED, VCU_Command(0x100) PC 송신 금지 유지.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**다.
Event 저장소·Event schema/원천/시각/상태 계약은 후속 팀 결정 필요이며 이번에 새로 구현하지 않았다.
Git add/Commit/Push/PR/Merge/Jira 등록·Done은 실행하지 않았다.


## Phase 3L-2 — CAN Network / KPI Observation (2026-10-17)

### Scope / source evidence

기준 PC-Diagnostic-Test / cdc3598dd1a896b9927373cab11708f5b0baf94b, 시작 Working Tree clean.
기존 Raw Pause/Decode/Fault Export를 보존하고 NetworkStatisticsModel, Dashboard 내부 패널,
identity 집계 CSV/JSONL Export를 추가했다. 기존9개 Navigation/Alt+1~9/탭 index는 그대로다.
상세 정의/근거/전체 schema/Open은 docs/network_kpi_observation.md에 기록했다.

조사 근거는 코드와 문서로 구분했다:
- 코드: Worker frame_sink→GUI buffer512/drop-oldest→drain100→Decode/Cache/Graph/Fault/Raw500;
  Network는 동일 drain의 Raw 객체를 한 번 계수한다. Raw Logger는 GUI Drop 이전 경로로 독립 기록한다.
- 코드: demo.make_demo_frame=time.time() 초, PythonCanInterface는 message.timestamp passthrough.
  설치 python-can4.6.1 slcan.py:328은 host time.time(), gs_usb.py:150~151은 하위 frame.timestamp 전달이다.
  실제 장치 clock/epoch/정확도는 NOT VERIFIED. FakeLive fixture의 반복 Timestamp도 실기값이 아니다.
- 문서: 메시지 정의서 CAN_Message_Definition B6:G11과 현재 DBC BO_/SourceTxType/GenMsgCycleTime의
  VCU0x100/10ms, Motor0x110/10ms, Vehicle0x120/20ms, Body0x200/100ms,
  Gateway0x300/100ms, Fault0x310/Event가 이 비교 범위에서 일치한다. 모두 STD/DLC8이다.
- 문서: 핸드북11.2/12.4(p29/32)는 Jitter 권장 예시 목표와 기록 항목을 제시하지만
  공식 산식/표본 창/clock/판정 기준은 확정하지 않는다. 요구사항 SYS_REQ_036은 목표/실제 결과 구분을 요구한다.
- Routing v0.4의 Interface_Ref/CAN_to_LIN은 참고 비교했다. LIN slot/명령 주기를 CAN 관측 KPI로 바꾸지 않았다.

Expected Period는 프로그램에 프로젝트 ID/수치를 하드코딩하지 않고 **사용자가 로드한 실제 DBC**
Cyclic+양수 GenMsgCycleTime에서만 읽는다. TEST ONLY fixture에는 주기가 없어 Definition Pending이다.
Fault_Status는 Event라서 Expected/편차 null이다. Interface 승인/Freeze 완료를 뜻하지 않는다.

### Implemented behavior and limits

Network는 Source·Channel 타입·ID·STD/EXT·RTR/Error를 구분하고 Processed RX/보관 ID/identity Count,
첫/마지막 시각과 양수 연속 간격의 평균/최소/최대/마지막, 관측 span, interval 기반 Rate를 제공한다.
최대512 identity/키당 상수 공간이며 Raw500행 이후에도 집계를 유지한다.

Stop/Start Count는 유지하고 run 경계에서 간격 연결만 끊어 미관측 정지시간을 포함하지 않는다.
span=sum(valid within-run deltas), Rate=interval_count/span이다. 전역 mixed-channel span/Rate는 계산하지 않는다.
Clear/Source/DBC reload는 기존 ECU 통계처럼 새 구간이다. Raw Pause 중 집계/Decode/Cache/Graph/Logging은 계속된다.
Timestamp 누락/중복/역전/overflow, GUI Drop/키 상한 제외/분리 못한 이전 run backlog에는 timing N/A다.
Count/원본 Timestamp와 이상 계수는 남긴다. GUI Drop을 실제 Bus packet loss로 계산하지 않는다.

Jitter Definition Pending, Bus Load N/A/null, Controller state/Bus-Off/Error Passive Unsupported.
Error Frame은 Backend 제공 flag의 처리 RX 수만 센다. Error0/Observed를 Healthy로 해석하지 않는다.
관측 평균-Expected는 산술 차이이며 Jitter/Threshold PASS가 아니다.
Hardware 및 clock accuracy는 항상 NOT VERIFIED다.

기존 ObservationExport/LoggingSession Writer의 exclusive-create, UTF-8 CSV/JSONL, null,
불변 snapshot, 부분 파일/오류, 첫 Error Close 창 유지·재시도 계약을 재사용했다.
Raw Logger/CLI CSV·JSONL 계약과 Thread/Timer 정책은 변경하지 않았다.
Decoded/Fault/Network Export는 공통 단일 작업 잠금을 사용한다. Event Export는 계속 Open이다.

### Actual environment and final runs

기존 .venv 조회: Python3.14.6 / PySide6 6.10.3 / python-can4.6.1 / cantools44.2.1 / pytest9.1.1.
패키지 설치/재설치·pyproject 변경 없음. 팀 고정 승인 버전은 미확정이다.

| 검증 | 이번 실제 결과 |
|---|---|
| 신규 모델/GUI 단독 중간 | 39 passed /14.72s — Raw500 이후 집계 시험1개 추가 전 |
| 최종 전체 pytest | **699 passed /85.79s**, 기존659 + 신규40, fail/skip 없음 |
| 기존 Phase1/2 CLI 별도 | **140 passed /0.69s**, 초기 Commit tree의 기존 테스트 파일 사용 |
| CLI/GUI 모듈 --help | 각각 종료0 |
| can-diag / can-diag-gui 설치 진입점 --help | 각각 종료0 |
| pip check | 종료0, No broken requirements found |
| Windows Native 기존13종 | **13 PASS** — Raw/Decode/Vehicle/ECU/Logging/Fake Live/Graph/Fault/Automation/Workspace/Driver/Polish/Pause Export |
| 신규 Network Windows Native 최종 | **PASS** — Mock/Fake TEST ONLY,3크기/주기·Event/Export/Drop/종료 |
| 기존9페이지 UI | 3크기·주요 액션48건·Alt+1~9·긴 이름·Live TX Blocked 재검증 PASS |
| Hardware / 사용자 수동 UI | **NOT VERIFIED / NOT RUN** |

pytest는 쓰기 확인한 .test-tmp/phase3l2-final/ 아래 별도 basetemp와 -p no:cacheprovider,
QT_QPA_PLATFORM=offscreen을 사용했다. Native는 QT_QPA_PLATFORM 없는 실제 windows platform 프로세스다.
신규40개는 모델/GUI2개 pytest 모듈이다. 신규 Native script는 별도1종이며 pytest 수에 포함하지 않는다.

핵심 검증:
- 첫 Frame N/A, 반복/서로 다른 간격의 독립 계산값, Channel int0/str"0"/null 분리,
  동일 숫자ID STD/EXT·RTR·Error 분리, TX 제외/실제 Error flag Count.
- Timestamp 누락/중복/역전/누적 overflow, 매우 작은 양수 간격 reciprocal의 Infinity 방지.
  원래 시각/Count 보존, 부적합 시간 통계 null, JSON NaN/Infinity 없음.
- 512 buffer에서520개를 주입해 실제8개 drop 재현, 처리512와 Received520 구분,
  timing N/A 및 Raw500 유지. Drop 없는600개 처리에서도 Count600/interval599/Raw500 유지.
- Stop/Start gap 제외, 이전 run pending N/A, Clear/Source/DBC reload, immutable snapshot 격리.
- 현재 Repository DBC6개 Message의 실제 cycle/Event 비교, TEST ONLY metadata 부재 및 No DBC.
- Raw Pause 중 Network/Cache/Graph/기존 Logger 독립, 기존 Automation11 Scenario 및 Driver Validation/TX 차단 회귀.
- Network CSV/JSONL 값/행 수, Empty/명시적 경로/모달 Source 변경, 기존 파일 보호,
  Write 부분 실패/Close 오류 첫 창 유지 및 재시도.
- 기존 Native의 Raw Logging CSV/JSONL CLI byte 호환성 및 Fake Live 송신 호출0/해제 검증.
- 새 Native: CSV/JSONL 각2 identity 행, Fake/Mock 분리, 실제 CAN backend 호출0,
  active Close에서 Receiver/기존 Timer/Writer 종료. 실제 Hardware KPI 결과가 아니다.

### Initial failures and correction

새 단위 시험의 overflow 입력에 음수 Timestamp를 사용해 기존 RawCanFrame이 먼저 거부했다.
기존 Frame 계약을 바꾸지 않고 유효한 비음수 Timestamp의 누적 overflow 시퀀스로 신규 시험만 수정했다.
새 GUI Fake 시험도 기존 window_factory가 지원하지 않는 keyword를 사용했다.
기존 select_live(window,factory) 도우미를 사용하도록 신규 시험만 보완했다. 기존 테스트는 수정하지 않았다.

최초 전체 실행은 **586 passed /113 setup errors /77.94s**였다.
실행 명령이 basetemp 상위 .test-tmp/phase3l2-final을 만들지 않아 WinError3가 발생했다.
제품/테스트 결함으로 단정하지 않았다. 새 상위 폴더를 생성하고 exclusive write-probe로 쓰기를 확인한 뒤
코드/Assertion 변경 없이 전체를 재실행해699 PASS, CLI140 PASS를 얻었다.
실패 로그는 증적 루트에 남기고 최종 재실행은 verified-tests에 분리했다.

### Evidence / Windows visual check

외부 증적 폴더 hint48-phase3l2-20261017:
- verified-tests/pytest-all.txt, cli140.txt, pytest-results.json — 최종 성공 결과
- entry-pip-results.json — 진입점/의존성/설치 버전 조회
- native-final/results.json 및14개 로그 — 기존13 + 신규1 모두 종료0
- native-final/network/ — 최종 Network9개 PNG 및 CSV/JSONL
- network-native/ — 초기 독립 Network Native 성공 증적
- source-test-sha256.json, preservation.json, git-final.json — 최종 보존/변경 검사

실제 Windows 캡처 native-final/network/:
network-mock-800x600.png, network-table-800x600.png,
network-mock-1024x768.png, network-table-1024x768.png,
network-mock-1280x920.png, network-table-1280x920.png,
network-explicit-dbc-period-event.png, network-expected-status-columns.png,
network-fake-live-test-only.png.
800×600 표 및 일반 크기 Network 화면을 시각 점검했고3크기 버튼/표 rect 접근을 자동 검증했다.
표 전체 열은 가로 스크롤, 정확한 값/출처는 선택 상세에서 읽는다.
사용자 수동 UI/전체 DPI·Screen Reader 검증과 구분한다.

### Preservation / collaboration status

작업 전후 SHA-256 비교로 D: 원본25개, 다른 Worktree 추적446개·HEAD·Status,
Interface 리뷰2개, 임시 Excel 및 Git refs를 보존했다.
기존 pytest/Native/Fixture를 수정하지 않았고 README/VERIFICATION은 기존 바이트를 append로 보존했다.
공통 Matrix/DBC/LDF/Routing/Requirements/Firmware, 기존 Interface/Adapter/Codec/Cache/CLI Sender/Logger,
의존성과 기존500행/Queue 정책은 변경하지 않았다.
git diff --check, 신규 Python AST/공백 검사 및 정확한 변경 파일 범위를 확인했다. Stage는 비어 있다.

팀 고정 버전·배포/Fixture 재배포 승인·Production Interface Freeze는 미확정 또는 검토 필요다.
담당자 코드 리뷰·사용자 수동 UI·CANable/ECU Hardware·실제 timestamp 정확도·고속/장시간·실제 파일 I/O 장애는 NOT VERIFIED.
0x600 미승인 후보, VCU_Command(0x100) PC 송신 금지, Driver Live TX BLOCKED 유지.
Jitter 공식/threshold, Bus Load/packet loss 모델은 후속 팀 리뷰 필요.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**, 핸드북4.2/5.5 Interface Change 절차 적용.
Git add/Commit/Push/PR/Merge/Jira 등록·Done 미실행.


## Phase 3M-2 — Fault Injection / Mock TEST ONLY (2026-10-17)

### Scope / actual source review

기준 PC-Diagnostic-Test / 14e31ca40a3196222087fdf3184ab8b26088e77d, 시작 Working Tree clean.
기존 Fault Monitor 아래 TEST ONLY 패널, Qt 독립 FaultInjectionModel facade,
Assertion/시험 History 표시와 방어 검증을 추가했다.
기존9페이지/Alt+1~9/탭 index 및 Automation11개 정의를 유지한다.

실제 조사 근거:
- gui/automation.py catalog/ScenarioInput와 gui/scenario_runner.py의 격리 MainWindow/Worker/cleanup 경로.
- FaultHistoryEntry/Model 및 기존 Fault tests, decode/cache/Raw/Source/Logging 경계.
- 명시적 tests/fixtures/test_only.dbc의 기존 Signal과 SHA-256 계약.
- 현재 Repository DBC Fault_Status(0x310)/Gateway 송신/4개 Signal 및 Node Enum/choice.
- Handbook10.1~10.5(p27~28)의 감지·전파·복구/주입 범위와 기존 Interface 리뷰 J2-016/018.
자료의 감지 Threshold/Recovery 예시를 새로운 PC Fault 정책으로 구현하지 않았다.

상세 Scenario/입력/상태/차단/관측과 실제 Fault의 차이/Open은 docs/fault_mock_injection.md에 기록했다.
이번 구현은 **기존 관측 시험**이다. 실제 Fault_Status 주입/ECU Fault 발생·Recovery/Hardware 완료가 아니다.

### Reuse / source boundary / retained meanings

기존 HINT48-MOCK-FAULT-v1, HINT48-MOCK-DECODE-ERROR-v1, HINT48-MOCK-SOURCE-v1의
같은 Scenario 객체/입력/expected를 참조한다. 새 ID/Scenario 복제/Runner/Thread/Timer는 없다.
같은 Automation Runner를 공유하므로 다른 Automation 실행을 교체하거나 취소하지 않는다.
hidden child에는 새 패널을 만들지 않아 재귀 Runner 생성이 없다.

사용자 Source=Mock와 명시적 unchanged fixture를 Model/기존 Runner에서 각각 검사한다.
실제 user Live(주입 backend 포함)는 버튼/Slot/Model/Runner 직접 호출에서도 차단한다.
기존 Source 편집 lock/programmatic 원복을 유지한다.
이를 우회한 실제 raw settings 변경은 기존 changed/tick에서 감지해 자기 trial만 cancel한다.
기존 Close→request_close→cleanup→Close 재시도 계약을 그대로 사용한다.

사용자 Receiver/Logger/Graph/Cache/Raw/Fault/Network는 격리 trial과 별개다.
시험 중 실제 사용자 Mock Rx/Logging/Graph가 계속됨과 멈춘 사용자 snapshot 불변을 검증했다.
기존 FaultHistoryEntry를 최대8개 참조하고 시험 RunResult를 최대10개 보관한다.
새 FaultTestRecord는 PC 시험 결과이며 ECU Fault Event 저장소가 아니다.
Reset은 자기 결과만 지우고 기존 Automation 결과/사용자 Fault History를 지우지 않는다.

Fixture에는 FaultCode/ECUOffline/RecoveryState/SystemState가 없다.
Production DBC를 자동 입력으로 채택하거나 Fixture를 확장하지 않았다.
별도 읽기 전용 회귀에서 기존 실제 DBC FaultCode0/ECUOffline1=VCU/RecoveryState0 choice ACTIVE와
Status Unknown 보존을 확인했다. 이 Label을 실제 Fault 해제/상태 전이 승인으로 쓰지 않는다.
Gateway 송신 주체/ECUOffline Node Enum/FaultCode0 자동 Clear 금지/Status Unknown을 유지한다.
ACTIVE/CLEARED 승인, 실제 Fault_Status 시험, Event 저장소/Replay/Resync는 계속 Open이다.

### Actual final verification

기존 .venv: Python3.14.6 / PySide6 6.10.3 / python-can4.6.1 / cantools44.2.1 / pytest9.1.1.
추가 패키지 설치/재설치/pyproject 변경 없음. 팀 고정 승인 버전은 미확정이다.

| 검증 | 이번 실제 결과 |
|---|---|
| 새 모델 + 기존 Automation/Runner 국소 회귀 | 54 passed /12.01s |
| 신규 Model/GUI 중간 | 35 passed /6.81s — Header 회귀1개 추가 전 |
| 신규 Model/GUI 최종 단독 | **36 passed /8.85s** |
| Header 보완 전 전체 | 734 passed /100.46s — 최종735와 구분 |
| 최종 전체 pytest | **735 passed /116.41s**, 기존699 + 신규36, fail/skip 없음 |
| 최종 CLI 별도 회귀 | **140 passed /1.30s**, 초기 Phase1/2 테스트 목록 |
| 최종 Windows Native 기존14종 | **14 PASS** — Raw/Decode/Vehicle/ECU/Logging/Fake Live/Graph/Fault/Automation/Workspace/Driver/Polish/Pause Export/Network |
| 최종 신규 Fault TEST Native | **PASS** — 기존3개 실행, PASS/FAIL/ERROR/CANCEL, Live 차단,3크기, 종료 |
| 모듈/설치 CLI·GUI --help | 4개 모두 종료0 |
| pip check | 종료0, No broken requirements found |
| 실제 Hardware / 사용자 수동 UI | **NOT VERIFIED / NOT RUN** |

pytest는 쓰기를 확인한 .test-tmp/phase3m2-verified 아래 새 basetemp와 -p no:cacheprovider,
QT_QPA_PLATFORM=offscreen을 사용했다. Native는 QT_QPA_PLATFORM 없는 실제 windows platform에서 실행했다.
최종 code 이후 전체735, CLI140 및 Native15종을 새 증적 경로로 재실행했다.
새 Assertion/Header 검증을 추가했으며 기존 테스트/Assertion은 수정하지 않았다.

신규36개 검증:
- 기존11개/3개 참조의 객체 identity, 유효/unsupported 선택, 입력 없음/잘못된 Raw/TX,
  No DBC/Fixture 누락/Production DBC 불일치, closing/DBC dialog/shared busy.
- 기존 실제 파이프라인에서3개 Scenario PASS. expected만 다르게 한 TEST ONLY 시험은 FAILED로 검출.
  누락/취소를 PASS로 표시하지 않으며 준비 ERROR가 이전 PASS 표로 표시되지 않음.
- 중복 Run/Reset 차단, 자신의 Cancel, 타 Automation Run cancel 금지, 유한 이력/Reset,
  실제 receive 오류/정상 자원 해제와 active Close.
- Primary Live/주입 Live의 Slot/Model 및 기존 Runner guard.
  can.Bus, PythonCanInterface.send, MockCanInterface.send 공개 경계 spy는 호출되면 실패하도록 설정.
  신규 Native 실제 결과 open0/send0, ScenarioInput send_calls0,7개 stream 정상해제.
  새 코드에는 ECU 제어 API 호출이 없다. 실제 물리 측정으로 해석하지 않는다.
- 기존 잠금 중 Source 변경 시도는 원복, 신호 차단으로 강제한 실제 Source 변경은 CANCELLED.
- TEST ONLY Fault History의 Status Unknown/실제 신호와 시험 이력 구분,
  사용자 Fault/Cache/Graph/Network/Raw snapshot 보존 및 사용자 활성 Mock Rx/Logger 유지.
- 기존 실제 DBC의 Node Enum/choice/FaultCode0/Status Unknown 읽기 전용 계약 회귀.
- 800×600/1024×768/1280×920 액션/Navigation, 새 Header 실제 글꼴 폭/tooltip,
  기존 Raw Pause/Export/Network/Automation11/Driver/Logging/Graph 기존 suite·Native 회귀.

### Initial findings / visual correction

신규 GUI 첫 실행은17 PASS/1 FAIL이었다.
테스트가 잠긴 mode_combo를 바꿔 실제 Source가 변경됐다고 가정했으나,
기존 ConnectionView.settings_changed가 즉시 Mock으로 원복했다.
제품 결함으로 단정하지 않았다. 기존 원복 동작은 별도 새 시험으로 유지하고,
원래 취소 검증에는 QSignalBlocker로 시험자가 실제 값 변경을 만든 뒤 CANCELLED를 확인했다.
기존 Source 방어 코드를 수정하거나 기존 Assertion을 약화하지 않았다.

초기 실제 캡처에서 새 결과 표의 Actual observation/Actual signals 제목이 잘렸다.
새 readonly_table의 styled Header 글꼴 폭/여백과 tooltip만 보완하고 새 회귀1개를 추가했다.
최종 캡처에서 제목 가독성을 확인했다. 전체735/CLI140/Native15종은 이 보완 이후 결과다.

### Evidence / actual Windows captures

외부 증적 hint48-phase3m2-20261017:
- verified-tests-final/pytest-all.txt, cli140.txt, pytest-results.json — 최종735/140
- entry-pip-results.json — 모듈·설치 진입점/의존성/설치 버전
- native-verified/results.json,15개 로그 — 최종 기존14 + 신규1 모두 종료0
- native-verified/fault-injection/ — 최종11개 PNG 및 사용자 Mock Raw Logging 시험 파일
- source-test-sha256.json, preservation.json, git-final.json — 보존/변경 근거
- fault-injection-first/, native-final/, verified-tests/ — Header 보완 전 기록, 최종과 구분

최종 캡처(native-verified/fault-injection/):
fault-test-actions-800x600.png, fault-test-assertions-800x600.png, fault-test-history-800x600.png,
fault-test-actions-1024x768.png, fault-test-assertions-1024x768.png, fault-test-history-1024x768.png,
fault-test-actions-1280x920.png, fault-test-assertions-1280x920.png, fault-test-history-1280x920.png,
fault-test-assertion-failed.png, fault-test-live-blocked.png.
실제 QWidget.grab() 결과를 시각 점검했고 작은 창의 주요 버튼·표 rect 접근을 자동 확인했다.
사용자 수동 확인/전체 DPI·Screen Reader 검증은 NOT VERIFIED다.

### Preservation / open work

SHA-256 대조로 D: 원본25개, 다른 Worktree 추적446개·HEAD·Status, 리뷰2개,
임시 Excel 및 Git refs를 보존했다. README/VERIFICATION은 기존 바이트를 보존해 append했다.
기존 Automation catalog/Runner/Fixture, 모든 기존 테스트, 공통 Matrix/DBC/LDF/Routing/Requirements/
Firmware와 기존 Adapter/Codec/Cache/CLI Sender/Logger/Network/Driver 계약을 변경하지 않았다.
새 소스/테스트 Syntax/공백/Markdown 링크와 git diff --check를 확인했다. Stage는 비어 있다.

팀 고정 버전·배포/Fixture 재배포 승인·Production Fault/Recovery/Interface Freeze는 미확정 또는 검토 필요.
담당자 코드 리뷰·사용자 수동 UI·실제 CANable/ECU Hardware는 NOT VERIFIED.
0x600 미승인 후보, Driver Live TX BLOCKED, VCU_Command(0x100) PC 송신 금지를 유지한다.
실제 Fault_Status fixture/Scenario와 Event/Replay/Resync 계약은 후속 Jira 검토 초안으로 남겼다.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**, 핸드북4.2/5.5 Interface Change 절차 적용.
Git add/Commit/Push/PR/Merge/Jira 등록·Done 미실행.


## Phase 3N-1 — Ignition / Driver Control UI (2026-10-17)

### Phase 3M-2 finalization / inherited evidence

이번 시작 시 Branch PC-Diagnostic-Test/HEAD14e31ca40a3196222087fdf3184ab8b26088e77d,
수정3개+신규6개/Stage 비어 있음을 확인했다.
기존3M-2 최종735 PASS/CLI140 PASS/Windows Native15종 PASS 로그·캡처·final-results.json을 재확인했다.
기존109개 Python Syntax,README/VERIFICATION 기존 바이트 prefix와 원본/다른 Worktree SHA를 확인했다.
동일3M-2 기록을 다시 추가하거나 기존 Fault UI/Runner/테스트를 재작성하지 않았다.
3M-2 실제 Fault_Status fixture/Scenario 및 Event/Replay/Resync는 계속 Open이다.

### Implementation / observed fixes

Ignition: DriverInputs 마지막 필드 str|None,OFF/ON/RUN만 허용,초기/Reset None.
기존5개 위치 인자와 기존 Adapter 재사용. ECU 상태/Enum/Frame/Interlock/Torque 계산 없음.
Driver UI는 기존 ChoiceStrip,Apply/Reset/Source/Close 경계를 재사용한다.
0x600 사용자 전달 팀 합의(PC→VCU/Driver Input)와 Payload TBD/승인 산출물 미확보를 구분했다.
기존 리뷰2개 및 임시 Excel은 수정하지 않았다. 실제 Live TX BLOCKED,0x601/자동ACK/재명령 없음.

첫 기존 Driver/레이아웃 시험에서 새 Label의 owner.source_label AttributeError가 발생했다.
존재하는 Driver model.source로 수정한 뒤 기존 Assertion을 그대로 재실행했다.
신규 단축키 시험의3개 실패는 창 활성화 전 key event 조건이었다.
기존 Native와 같은 activateWindow/raise/qWaitForWindowActive 선행 조건을 추가하고
Alt+1..9 Assertion을 유지했다. 새26개 모두 통과했다.
실제 캡처의 긴 History 입력은 Ignition 우선 요약/전체 원본 tooltip으로 보완했다.
이후 전체/Native 결과를 아래 최종값으로 기록한다.

### Final actual software verification

최종 소스 변경 후 재실행:
- 전체 pytest: **761 PASS /140.28s** = 기존735개 + 신규26개. 실패/Skip0.
- 기존 CLI 별도 회귀: **140 PASS /1.24s**. 초기 Phase1/2 Git tree의8개 테스트 파일을 그대로 실행.
- 신규 Ignition: Model18개 + GUI8개. OFF/ON/RUN,invalid,기존 위치 인자,
  Apply/Reset/Adapter/History,동시 입력 보존,Source,Live Slot/Model 직접 차단,
  세 해상도 주요 액션/9개Navigation,Mock RX와 요청 독립성/종료·새 창 초기화 확인.
- Windows Native: **기존15종+신규Ignition1종=16종 PASS**,각 프로세스 exit0.
  Raw/Decode/Vehicle/ECU/Logging/Fake Live/Graph/Fault/Automation11/Workspace/
  Driver/Polish/Raw Pause Export/Network/Fault Injection/Ignition.
- Logging CSV/JSONL 기존 CLI byte 호환,Graph/Export/Network/Fault TEST ONLY,
  Fault Injection 기존3Scenario/동일 Runner/격리 History와 사용자 RX·Logging 보존 회귀 확인.
- Ignition Native: OFF/ON/RUN,37.5%/Brake ON/Gear R/Window CLOSE/Light ON,
  Apply/History,Live Slot·Model 차단,3회Start/Stop,활성Close와새 창초기화 확인.
  관측한 물리 CAN Open 경계 **0회**,CAN TX 경계 **0회**.
  can.Bus/BusABC.send/MockCanInterface.send/PythonCanInterface.send/RawCanSender.send를 trap으로 감시했다.
  실제 Hardware Bus에 접속했다는 뜻이 아니다.
- CLI/GUI 모듈 --help 및 설치 can-diag/can-diag-gui --help 모두 exit0.
- pip check: exit0,No broken requirements found. 패키지 설치/재설치 없음.
- Qt offscreen pytest/캐시 비활성화,전용 writable basetemp .test-tmp/phase3n1-final.
  Native는 Windows platform 실제 창으로 별도 실행했다.
- Python3.14.6/PySide66.10.3/python-can4.6.1/cantools44.2.1/pytest9.1.1 기존 환경 유지.
  위 설치 버전은 팀 승인 고정 버전이 아니다.

### Actual Windows captures / evidence

외부 증적 hint48-phase3n1-20261017:
- before/: **소스 수정 전**800×600/1024×768/1280×920 Driver Control3장.
- native-verified/ignition/:최종OFF/ON/RUN/전체 입력/Mock Accepted/History/Live Blocked
  7상태×3개 해상도=21장,result.json.
- before_after.md:동일 해상도 Before/After 비교.
- verified-tests-final/pytest-all.txt,cli140.txt,pytest-results.json:최종761/140.
- native-verified/results.json 및16개 로그:최종Native16종.
- entry-pip-results.json:모듈/설치 진입점/의존성 검사.
- interface-source-rows.json,source-doc-sha256.json:읽기 전용 메시지 표/Routing 근거.
- source-test-sha256.json,preservation.json,git-final.json:최종 코드/보존/Git 증적.
- after-first/:History 표시 보완 전 중간캡처,최종과구분.

Before/After actual QWidget.grab()를 시각 점검했다.
800×600에서Apply/Reset/Ignition/Brake/Gear 접근 가능,Body/관측결과/History는기존스크롤 사용.
큰 창에서는Driving/Body 분리 카드,새0x600안내/요청·수락·미송신·관측 경계 표시를 확인했다.
History 전체 원본은 tooltip에 보존한다. 표가좁으면 scroll이 필요하며 모든행·필드가동시에보인다는주장없음.
실제 logical size와PNG픽셀은Windows DPI배율에따라다르다.

### Interface / review / preservation status

현재 로컬 핸드북/02메시지 정의/DBC/Routing의0x120 송신자 Gateway 일치.
Gateway_Status 설명의GatewayHealth/SystemState와실제DBC GatewayAlive/QueueUsage차이는검토필요.
0x100 수신/0x110 RPM관측을0x600수락/성공으로상관시키지않는다.
자세한Receiver/Signal/근거와Jira등록초안은 docs/driver_ignition_ui.md.
원격 최신 Firmware/실제 Flash/버스 실측은 이번에검증하지않았다.
팀 고정버전/배포승인/Production Payload/VCU초기값·Interlock·수락계약/Freeze 미확정.
사용자 수동UI·담당자코드리뷰·실제CANable/ECU Hardware **NOT VERIFIED**.
실제CAN TX **BLOCKED**. 새0x601미구현. 실제Fault_Status시험/Event Export/Replay/Resync Open유지.
공통Matrix/DBC/LDF/Routing/Requirements/Firmware·기존테스트·기존Adapter/Codec/Cache/Sender/Logger미변경.
기존리뷰2개·임시Excel·D:원본25개·다른Worktree446개/HEAD/Status/refs보존은최종SHA대조증적으로확인.
README/VERIFICATION 기존바이트이력은보존해append했다.
Git diff --check/Syntax/Markdown상대링크/변경목록/빈Stage최종점검.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**,핸드북4.2/5.5 및CONTRIBUTING§5절차 적용.
Git add/Commit/Push/PR/Merge/Jira등록·Done 미실행.



## Phase 3N-4 — UART transition preparation (actual verification)

- 현재 변경 범위: `DriverTransport` protocol 계약, 비활성 UART 상태 패널, Driver Control의 UART 상태/Mock 경계 문구, 관련 자동화 및 native smoke.
- UART 상태: `NOT CONFIGURED` / `PENDING APPROVAL` / `UART TX DISABLED` / `UART RX NOT VERIFIED`. Connect/Disconnect 비활성. VCU Response `NOT IMPLEMENTED / NOT VERIFIED`; 자동 ACK·재전송 없음.
- Driver Mock 입력의 모델/검증/Adapter/History 및 Apply/Reset 동작은 유지. Window/Light는 별도 Mock Body intent이며 UART payload에 연결되지 않음. Mock Accepted와 VCU 응답은 구분.
- CAN Monitor는 기존 독립 CAN Interface/Worker를 사용. 새 UART 상태 패널은 CAN 상태를 공유하지 않으며 CAN RX를 UART 응답으로 표시하지 않는다. Phase 3N-4 native smoke에서 CAN Open/TX 호출은 각각 0회.
- 새 UART 모듈에는 실제 Serial open/read/write 구현이 없다. GUI는 DriverTransport를 생성하거나 호출하지 않는다. Serial port 탐색, Baudrate, protocol/framing, payload, ACK, timeout, fail-safe 및 VCU firmware 지원은 미정.
- 최종 전체 pytest: **767 passed / 374.05 s**. 기존 Phase 1/2 CLI 회귀: **140 passed / 1.46 s**. UART/상단 상태 회귀 집중 실행: **27 passed / 15.45 s**.
- Windows Native: **기존 16종 PASS + Phase 3N-4 UART panel smoke PASS**. 확인 범위에는 800×600/1024×768/1280×920 창, 9페이지/Alt+1..9, Mock Apply/Reset, CAN Mock RX와 UART 상태 독립성, Connect/Disconnect 비활성, CAN Open/TX 0회가 포함된다. 새 UART smoke에서 `platform=windows`.
- CLI 및 GUI 설치 진입점 `--help`: PASS. `pip check`: `No broken requirements found`. Python 3.14.6, PySide6 6.10.3, python-can 4.6.1, cantools 44.2.1, pytest 9.1.1 확인. 패키지 설치/재설치와 `pyproject.toml` 변경 없음. 위 버전은 팀 승인 고정 버전이 아니다.
- Before는 Phase 3N-1 작업 전 Windows 화면, After는 3N-4 최종 Windows native 캡처이며 같은 Driver Control 창 크기를 사용했다. 가로 스크롤을 유발하던 비활성 사유의 한 줄 배치를 분리한 뒤 최종 캡처를 다시 생성했다.
- 사용자 수동 GUI 확인, 실제 USB-UART/VCU 연결, UART RX/TX, CANable/ECU Hardware, 담당자 코드 리뷰는 **NOT VERIFIED**. UART protocol 및 physical mapping은 **상대 담당자 리뷰 필요**. 실제 CAN TX와 실제 UART TX는 구현하지 않았고 BLOCKED 상태다.
- 0x600 후보는 UART Packet ID로 재사용하지 않았다. CAN Matrix/DBC/LDF/Routing/Requirements/Firmware 및 기존 UART/CAN 설계 문서는 변경하지 않았다. Git Stage/Commit/Push/PR/Merge/Jira Done은 미실행.

### Windows screenshot evidence

- Before 800×600: `hint48-phase3n1-20261017/before/driver-before-800x600.png`
- Before 1024×768: `hint48-phase3n1-20261017/before/driver-before-1024x768.png`
- Before 1280×920: `hint48-phase3n1-20261017/before/driver-before-1280x920.png`
- After 800×600: `hint48-phase3n4-20261017/native-final/driver-uart-800x600.png`
- After 1024×768: `hint48-phase3n4-20261017/native-final/driver-uart-1024x768.png`
- After 1280×920: `hint48-phase3n4-20261017/native-final/driver-uart-1280x920.png`

Evidence is stored outside the Repository. It is native Windows Qt capture and does not demonstrate physical UART/CAN hardware operation.