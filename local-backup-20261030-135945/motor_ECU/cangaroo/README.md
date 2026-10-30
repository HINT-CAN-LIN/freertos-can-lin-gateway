실물 연결: [하드웨어 구성 및 Pin In / Pin Out](../../../docs/hardware/MOTOR_ECU_PINOUT.md).

# Motor ECU / CANgaroo 0.7.0

스크립트 v1.5와 펌웨어 revision 4는 DC 모터 4개와 SG90 두 개를 함께 구동한다.
기존 d/r 단축 명령도 유지한다. CANgaroo에 예전 Desktop 복사본을 열었다면
이 폴더의 `motor_control.py`를 Load로 다시 선택해야 한다.

## DBC의 방향 명령

자동 반복 시험: Measurement 시작 후 이 폴더의 script1.5를 Load/Run하고 인터페이스를 선택한다. `status`에서 revision4/READY를 확인한 뒤 **`auto`**를 입력한다. Run만 누르면 P/zero를 유지하고 자동으로 움직이지 않는다.

`auto`는 30초 시퀀스를 중단할 때까지 반복한다. 전진 PWM20%/중앙 → 25%/좌20도 → 35%/좌40도 → 20%/중앙 → 25%/우20도 → 35%/우40도(각3초), P/중앙1초, 후진20%/좌20도 → 25%/중앙 → 20%/우20도(각3초), P/중앙2초 순서다. 실제 속도가 아닌 PWM 요청값이며 실제 조향각도 보정값에 따라 다르다.

**`s`로 즉시 시퀀스를 해제하고 다음 송신에서 DC0/P/서보 중앙을 요청한다.** `quit`는 정지 후 종료한다. 수동 구동/조향/정지 명령도 자동 모드를 해제하며, 자동 모드에서 수동 조향만 입력하면 DC는 0으로 전환한다. `status/help/dbc`는 자동 모드를 유지한다. 상태 수신 끊김, ECU OFF/FAIL_SAFE, 펌웨어 버전 불일치 시 자동 모드를 해제하고 정상 통신이 돌아와도 재시작하지 않는다. 다시 `auto`를 입력해야 한다. 정지 구간 중에도 같은 검사를 수행한다.

자동 반복에는 후진이 포함되므로 바퀴를 띄우고 링크의 가동 범위를 확인한 상태에서 시험한다. `AUTO_STEPS`에서 시간/PWM/Gear/조향을 변경할 수 있다. DC/서보 핀, DBC 배치와 펌웨어는 v1.4 시점 규격을 유지하므로 revision4가 이미 올라가 있다면 펌웨어 재다운로드는 필요 없다.

방향 명령은 `VCU_Command` 표준 ID **0x100**, DLC 8, 10 ms 주기로 들어온다.
Byte2의 bit0..2가 Gear이며 0=P, 1=N, 2=D(전진), 3=R(후진)이다.
Byte2 bit3=Brake, bit4..7=AliveCounter이다. Byte0..1은 TorqueRequest(raw*0.1 Nm)이다.
Byte2는 `(AliveCounter << 4) | (Brake << 3) | Gear`로 조합한다.
예를 들어 400 Nm, R, Brake=0, Alive=0이면 `A0 0F 03 00 00 00 00 00`이다.

`Vehicle_Status` 0x120의 Gear는 Gateway가 전달하는 차량 상태이며 Motor ECU 제어 입력이 아니다.
추가 신호 `SteeringAngle`: 0x100의 Byte4..5, `32|16@1- (0.1,0) [-45|45] "deg"`.
Signed little-endian이며 0=중앙, 음수=좌, 양수=우로 정의했다. raw 32767은 INVALID이다.
범위와 부호는 이번 로컬 확장의 인터페이스 정의이며 실제 SG90 축 각도와 같다는 의미는 아니다.
Byte3와 Byte6..7은 0으로 유지한다. Byte3의 Body 명령 후보는 이 스크립트에서 생성하지 않는다. 기존 Byte4..5가 0인 송신은 중앙 요청으로 해석한다.

예: 토크 0/P/Alive0/좌20도는 `00 00 00 00 38 FF 00 00`이다.
Motor ECU는 `MotorRuntime_State()->command.steering_raw`로 원시 요청을 보존하고,
유효한 요청은 `steering_target_raw`에 반영한다. 단위는 0.1도이다.
잘못된 각도는 전체 명령을 invalid로 차단하며, timeout 시 target은 0으로 만든다.
timeout/invalid/Alive 오류에서는 DC PWM을 차단하고 두 서보에 중앙 펄스를 출력한다. 실제 복귀 여부는 전원/기구에 달려 있다.

SG90 두 개는 PA0/PA1(TIM2 CH1/CH2)에서 50Hz로 구동한다. 부팅 시 중앙 1500us를 출력한다.
기본 매핑은 두 서보 같은 방향이며 `SERVO_DIRECTION_INVERT_MASK`의 bit0/bit1로 각 서보를 반전한다.
`SERVO1_CENTER_US`, `SERVO2_CENTER_US`로 중립을 보정한다.
명목 변환은 90도당 500us이며 -45..45도 요청이 1250..1750us에 대응한다.
예: -20도=1389us, 0도=1500us, +20도=1611us. 실제 축/차륜 각도는 기구와 제품별 보정이 필요하다.
P/N 및 DC 출력 0 상태에서도 서보 단독 시험이 가능하다. 최초 연결 시험은 링크를 분리한 상태로 확인한다.
서보 전력은 제품 정격에 맞는 외부 안정화 전원에서 공급하고 ECU와 GND를 공통 연결한다.
서보별 각도 명령이나 실제 각도 피드백은 정의하지 않았다.
LightStatus의 LEFT_TURN/RIGHT_TURN은 방향지시등 상태이며 조향 명령과 별개다.

이 폴더의 `motor_control.py`를 CANgaroo Script View에서 Load한다.
일반 Python이나 터미널에서 실행하는 스크립트가 아니다.
`motor_ecu.dbc`는 사용자가 제공한 DBC에 SteeringAngle을 추가한 v0.7 확장본이며 network/can의 공식 저장소 DBC와 동일하다. Downloads 원본은 수정하지 않았다.

## 시작 순서

1. STM32CubeIDE에서 상위 `motor_ECU` 프로젝트를 빌드하고 ST-LINK로 보드에 다운로드/실행한다.
   준비된 바이너리는 `../Debug/motor_ECU.elf`, `../Debug/motor_ECU.bin`이다.
   BIN을 직접 다운로드할 때 Flash 시작 주소는 `0x08000000`이다.
2. CANable과 Motor ECU의 CAN 트랜시버를 CANH/CANL/GND로 연결한다.
3. CANgaroo Measurement Setup에서 실제 CANable을 선택하고 500 kbit/s,
   Classic CAN, 일반 송수신 모드로 설정한다. Listen-only는 해제한다.
   인터페이스에 이 폴더의 `motor_ecu.dbc`를 연결한다.
4. Measurement를 시작한다. Motor ECU가 0x110을 10 ms 주기로 보내는지 확인한다.
5. `Window -> New -> Script View`에서 `motor_control.py`를 Load한다.
   AutoRun은 끈 상태로 두고 Run을 누른다.
6. CAN 인터페이스가 둘 이상이면 콘솔에 표시된 실제 CANable의 interface id를
   하단 `Script input` 입력란에 입력하고 Enter를 누른다. CAN ID 0x100과 다른 값이다.
7. 시작 시 P/토크 0 명령만 전송된다. 약 0.1초 후 입력란에 `status`를 입력해
   `State=READY`, fresh 0x110, `ECU firmware revision=4`, `faults=0x0`을 확인한다.
   revision=0이면 구형 펌웨어이므로 새 소스를 빌드/다운로드하고 F8로 실행한다.
8. 입력란에 `d 10 5`를 입력하면 네 DC 모터가 전진 PWM 10%로 5초 구동한 뒤 정지한다.
   `r 10 5`는 후진이다. 실제 모터가 낮은 듀티에서 기동하지 않으면 부하/전원을 확인한다.

Raw TX 또는 TX Generator에서 0x100을 동시에 반복 송신하지 않는다.
스크립트는 초당 100프레임을 보내며 AliveCounter를 0..15로 증가시킨다.
현재 펌웨어의 `MOTOR_CANGAROO_FIXED_ALIVE=0`과 맞는다.

## 입력 명령

| 입력 | 동작 |
|---|---|
| `d 10 5` | D, PWM 10%, 5초 |
| `forward 25 3` | 전진, PWM 25%, 3초 (`d 25 3`과 동일) |
| `reverse 10 5` | 후진, PWM 10%, 5초 (`r 10 5`와 동일) |
| `gear D` / `gear R` | 토크 0으로 기어만 선택, 자동 구동하지 않음 |
| `gear P` / `gear N` | 토크 0으로 P/N 선택 |
| `torque D 400 5` | 전진, TorqueRequest 400 Nm, 5초 (데모 PWM 10%) |
| `torque R 1000 3` | 후진, TorqueRequest 1000 Nm, 3초 (데모 PWM 25%) |
| `left 20 5` | 좌20도 요청, 5초 후 요청 0 |
| `right 20 5` | 우20도 요청, 5초 후 요청 0 |
| `steer -15 5` | 부호 있는 좌15도 요청, 5초 |
| `center` | 두 서보 중앙 명령 |
| `drive d 25 -20 5` | DC 전진25% + 좌20도, 동시에 5초 |
| `drive r 25 20 5` | DC 후진25% + 우20도, 동시에 5초 |
| `dbc` | 신호 위치와 방향 명령 해석 표시 |
| `d 25 3` | D, PWM 25%, 3초 |
| `r 10 5` | R, PWM 10%, 5초 |
| `d 10` | D, PWM 10%, 기본 5초 |
| `s` 또는 `p` | 즉시 토크 0/P 명령으로 변경 |
| `n` | 토크 0/N |
| `b` | 토크 0/Brake |
| `status` | 마지막 가상 RPM/토크/State/Alive와 수신 age 표시 |
| `help` | 명령 안내 |
| `quit` | 토크 0/P 프레임 전송 후 스크립트 종료 |

허용 범위는 PWM 0..100%, 구동 시간 0초 초과~60초 이하이다.
잘못된 명령을 입력하면 현재 구동 명령도 토크 0으로 바뀐다.
지정 시간 종료, 0x110 응답 150 ms 초과 중단 또는 ECU FAIL_SAFE 감지 시
토크 0/P로 바뀌며 명시적인 새 d/r 명령 전에는 재가동하지 않는다.

조향 명령은 DC 모터 출력 크기/기어를 변경하지 않는다. DC 구동 명령은 현재 조향 요청을 유지한다.
정지 명령(s/p/n/b/gear)·잘못된 입력·응답 손실은 조향 요청도 0으로 만든다.
조향 유지 시간이 끝나면 조향 요청만 0으로 바뀐다. 주행 시간 종료 시에는 주행과 조향 요청을 모두 0으로 만든다.

서보 PWM은 활성화된다. DBC에는 네 모터별 명령이 없어 네 모터가 같은 출력 크기로 움직인다.
좌우 장착 반전은 `../Core/Src/main.c`의 `MOTOR_DIRECTION_INVERT_MASK`로 설정한다.
물리 출력은 목표 가상 RPM 비율이다. 10%=TorqueRequest 400 Nm=Target 1200 RPM이며
실제 토크나 실제 RPM 측정값이 아니다. `status`의 RPM은 가상 모델의 현재 RPM이다.

스크립트 Stop 버튼, Measurement 중지, 앱 종료 등으로 Python 정리 코드가 중단되어도
ECU의 마지막 명령 수신 후 30 ms 초과 timeout이 물리 PWM을 차단한다.
호스트 OS 지연이 30 ms를 넘으면 ECU가 FAIL_SAFE로 전환될 수 있다.
방향 전환은 펌웨어에서 200 ms 출력 차단 후 수행한다. 이는 축 정지 확인 기능이 아니다.

## FAIL_SAFE 진단

Motor_Status 0x110 Byte5..6은 signed 0.1도 `SteeringTargetEcho`이며 측정 각도가 아니다.
Byte7의 하위 4비트는 `LocalFaultFlags`, 상위 4비트는 `FirmwareRevision`이다.
revision=4이 새 펌웨어이다. 0은 이 필드가 없던 구버전일 수 있다.
스크립트는 구형 펌웨어로 운전/조향 명령을 보내지 않는다.

| 플래그 | 의미 | 확인할 내용 |
|---|---|---|
| 0x1 | TIMEOUT | 0x100 수신 간격이 30ms를 초과했는지 |
| 0x2 | ALIVE_SEQUENCE | 다른 Script/Raw TX가 같은 0x100을 보내는지, 프레임 누락 여부 |
| 0x4 | INVALID_INPUT | 토크/Gear/각도 범위와 펌웨어·DBC 버전 일치 여부 |
| 0x8 | RX_QUEUE_LOSS | 수신 큐 포화 또는 상태 mutex 대기로 수신 명령 누락 |

여러 원인이 함께 있으면 비트가 합쳐진다. 예를 들어 0x3은 TIMEOUT+ALIVE이다.
`status`는 최대 TX API 호출 간격도 표시한다. 버스 실제 전달 간격을 측정한 값은 아니다.
로그의 FAIL_SAFE만으로 원인을 확정하지 말고 이 플래그를 확인한다.
안전 조건을 강제로 해제하지 않는다. 정상 프레임으로 복구한 후 새 명령을 입력한다.

## 파일과 검증

- `motor_control.py`: CANgaroo 0.7.0 내장 `cangaroo` API만 사용한다. pip 설치 불필요.
- `motor_ecu.dbc`: 로컬 SteeringAngle 확장본. 기반 원본의 SHA256 `D982916F61245E96518E422BC84FC59E0C9A121EA25CB19F227E901700E4FFF4`.
- `../tests/test_cangaroo_script.py`: 하드웨어에 송신하지 않는 모의 API 회귀 테스트.
- `../tests/test_motor_control.c`: 펌웨어 CAN 해석/정지/복구/방향 전환 테스트.

API 기준은 설치 버전과 같은 V0.7.0의 `examples/periodic_send.py`,
`examples/measurement_control.py`, `src/core/PythonEngine.cpp` 및
`src/window/ScriptWindow/ScriptWindow.cpp`이다.
https://github.com/Schildkroet/CANgaroo/tree/V0.7.0

호스트 로직 및 모의 API 테스트와 ARM 빌드는 검증한다.
실제 CANable/모터 연결 시험은 아직 수행하지 않았다.

CMSIS-RTOS2 task·mutex·queue 구성과 빌드 절차: [RTOS2_ARCHITECTURE.md](../RTOS2_ARCHITECTURE.md).
