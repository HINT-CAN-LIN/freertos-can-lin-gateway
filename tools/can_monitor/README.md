# VCU · Motor PC Tool

프로젝트 루트의 `Start_CAN_Monitor.cmd`를 더블클릭한다.
이 PC에는 전용 Python 환경과 CAN 수신 라이브러리를 설치했다.
앱은 연결하지 않은 상태로 시작하며 **데모 시작**은 합성 신호만 표시한다.

## CAN으로 VCU 입력하기

경로: PC → USB CANable(COM4) → CAN 0x200 → VCU → CAN 0x100 → Motor.
VCU가 입력을 수락하면 0x201 ACK를 돌려준다. COM6 USB-UART 입력은 사용하지 않는다.
이번 CAN 입력 전용 VCU 펌웨어는 UART 구동 입력을 거부하여 두 입력원의 충돌을 방지한다.

1. VCU에 `output/can-integration/vcu-can-input.elf`를 다운로드한다. Motor 펌웨어는 기존 것을 사용한다.
2. CANable / VCU / Motor를 CAN_H, CAN_L, 공통 GND에 연결하고 버스 양 끝을 120 Ω 종단한다.
3. CANgaroo 등 CANable을 사용하는 다른 프로그램의 연결을 닫는다.
4. PC Tool에서 **slcan / COM4 → 전체 연결**을 누른다. 속도는 500 kbps다.
5. **CAN ACK 0x201 OK**, VCU 0x100, Motor 0x110 수신을 확인한다.
6. **D / 10% / 2초 → ▶ 실행**을 누른다. **정지 / 브레이크**로 즉시 정지를 요청할 수 있다.

가속은 0–20%, 시간은 1–10초이며 P/N은 가속 0으로 제한한다. 값 편집만으로는
움직이지 않는다. 실행 시간이 끝나거나 CAN/화면 갱신이 끊기면 정지를 요청하고
자동으로 재시작하지 않는다. 데모에서는 송신하지 않는다.

PC는 50 ms마다 0x200을 보내고 해당 sequence의 ACK를 기다린다. ACK가 200 ms 내
오지 않으면 구동을 취소한다. UI 갱신 lease는 300 ms다. VCU는 유효한 입력이
300 ms 끊기면 OFF/P/가속 0으로 복귀한다. 연결 종료 시 정지 프레임 3개를
최선 노력으로 전송하며 종료 ACK 확인을 보장하지 않는다.

기존 UART 전용 펌웨어에서는 0x201 응답이 없으므로 실행 버튼이 활성화되지 않는다.
CANable은 PC와 USB로 연결하지만 VCU에는 CAN으로 전달된다. PC가 0x100을 직접
송신하지 않으며 Motor는 VCU의 0x100만 처리한다.

## PC 입력 CAN 규격 (벤치 전용 확장)

표준 11-bit DATA, DLC 8, 500 kbps. 기존 DBC의 구동 신호와 별도 확장이다.

| ID | 방향 | byte 0..7 |
| --- | --- | --- |
| 0x200 | PC → VCU | version=1, sequence LSB, MSB, ignition(0..2), pedal(0..20), brake(0/1), gear(P0/N1/D2/R3), CRC |
| 0x201 | VCU → PC | version=1, sequence LSB, MSB, status(0 accepted/2 sequence 또는 handshake 거부), ignition echo, pedal echo, gear echo, CRC |

CRC-8 polynomial 0x07, initial 0, bytes 0..6, no reflection/xor-out.
잘못된 CRC/버전/값/길이/확장/RTR 프레임은 입력을 갱신하지 않고 ACK도 보내지 않는다.
시작 및 타임아웃 후에는 OFF/P/가속0/브레이크1 프레임으로 먼저 연결해야 한다.
구동 프레임은 modulo 65536 sequence가 1..32767만큼 전진해야 하며 중복/과거 값은 거부한다.
정지 프레임은 sequence와 관계없이 수락한다. 이는 인증 프로토콜이 아니며 격리된 벤치용이다.

## 표시 및 기록

- 0x200: PC 송신 입력 (TX 표시와 카운트).
- 0x201: VCU 수락 ACK (RX 표시와 카운트).
- 0x100: TorqueRequest, Gear, Brake, AliveCounter.
- 0x110: RPM, TorqueApplied(디코더), MotorState, AliveCounter.
- Raw 표: ID/타입별 최신 payload, 처리 수, 마지막 수신 간격, 경과 시간, Alive 누락 횟수.
- 기본 신호 배치는 `network/can`의 현재 DBC와 MCU 인코더에 맞췄다. 임의 DBC 로더는 아니다.
- 30 ms 초과는 LATE 표시, 100 ms 초과는 카드/그래프 값을 비운다. PC 스케줄링 및
  USB 버퍼링 영향을 포함하므로 이 수치는 펌웨어의 타이밍 합격 판정이 아니다.
- Alive는 연속 수신에서 modulo 16 증가를 검사한다. 30 ms 초과 간격 뒤에는 재동기화한다.
- 표 캐시는 512개 ID/타입으로 제한한다. UI 큐 손실은 UI DROPS로 별도 표시한다.
- 실제 수신은 `captures/YYYYMMDD-HHMMSS-ffffff.csv`에 자동 저장된다. 데모는 저장하지 않는다.
  TX/RX는 direction 열로 구분한다. 원시 수신을 UI 큐에 넣기 전에 기록하며, 250 ms마다 flush한다. 저장 오류는 수신을 중단한다.
- Cluster에는 송신 heartbeat가 없으므로 PC에서 Cluster 생존/수신을 확인할 수 없다.
  Cluster 보드의 RPM·기어 표시를 함께 확인한다.
- 현재 Motor RPM은 모델 값이다. 속도는 Gateway의 0x120이 없으면 제공되지 않는다.
- 연결 실패 시 오류를 표시하며 데모로 자동 전환하지 않는다. 앱이 USB 드라이버나 펌웨어를 바꾸지 않는다.

## 실행 환경과 테스트

다른 PC에서는 Python 3.10 이상(Tk 포함)으로 다음을 실행한다.

```powershell
python -m venv tools/can_monitor/.venv
tools/can_monitor/.venv/Scripts/python.exe -m pip install -r tools/can_monitor/requirements.txt
```

현재 PC의 MSYS Python 환경에서는 다음 테스트 명령을 사용한다.

```powershell
tools/can_monitor/.venv/bin/python.exe -m unittest discover -s tools/can_monitor -p 'test_*.py' -v
```

실제 Python CAN VirtualBus → 수신 스레드 → 디코더 → CSV,
UI 값 갱신/만료, Alive wrap/누락, 잘못된 프레임, 연결 실패와 중지를 검사한다.
기존 UART→VCU→CAN 저속 시험 이력은 output/can-integration/hardware-captures에 있다.
이번 CAN 입력 확장의 실제 보드 시험 여부는 별도 확인해야 한다.
`tests/test_pc_can_input.c`는 실제 VCU 수신 함수로 입력 검증·재전송·300 ms 만료·재연결을 검사한다.

`usb/libusb-1.0.dll`은 PyPI libusb-package 1.0.30.0 Windows x64 wheel에서 가져왔다.
동봉 LICENSE와 LGPL-2.1 조건을 참고한다. libusb 소스는 https://github.com/libusb/libusb 에서 제공된다.
사용자 CANable의 Windows 드라이버가 호환되어야 한다.
Backend API 참고: https://python-can.readthedocs.io/en/stable/interfaces/gs_usb.html 및
https://python-can.readthedocs.io/en/stable/interfaces/slcan.html .


## 이번 CAN 입력 버전 검증 상태 (2026-10-30)

- VCU ARM 전체 컴파일/링크 및 ELF/BIN 생성 완료.
- PC Tool 자동 테스트 19개 통과 (VirtualBus, ACK 검증/손실, 정지 포함).
- 실제 VCU CAN 수신 함수를 사용하는 호스트 테스트 통과 (값/CRC/ID 형식,
  중복 sequence, 300 ms 만료, 정지 handshake, sequence wrap).
- USB 장치 목록에서 CANable/ST-LINK가 검출되지 않아 새 펌웨어의 보드 다운로드와
  실제 CAN 입력 시험은 아직 수행하지 못했다. 이전 UART 시험 결과와 구분한다.
- 다운로드: 보드를 연결한 뒤 `powershell -ExecutionPolicy Bypass -File tools/flash_vcu_can_input.ps1`.
  기본 대상은 확인된 VCU ST-LINK serial 066EFF505487525067173344이며 Motor는 선택하지 않는다.
- 테스트 재실행: `powershell -ExecutionPolicy Bypass -File tools/test_pc_can_input.ps1`.
