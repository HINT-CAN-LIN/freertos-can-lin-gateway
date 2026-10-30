# CANgaroo에서 실제 VCU / Motor 조작

기존 Python PC Tool에서 **정지** 후 창을 닫아 COM4/COM6을 해제한다.
루트의 `Start_CANgaroo.cmd`로 CANgaroo를 실행한다. 워크스페이스가 자동으로 열리지 않으면
File → Open Workspace에서 `tools/cangaroo/VCU_Motor.cangaroo`를 연다.

1. Measurement를 시작한다. CANable은 SLCAN / COM4 / 500 kbit/s이다.
2. 표에서 0x100과 0x110 수신을 확인한다.
3. Script View의 `vcu_motor_control.py`에서 Run을 누른다.
   Script View가 없으면 Window → New → Script View를 열고 이 파일을 Load한다.
4. `VCU USB ACK`/정상 연결을 확인하고 아래 **Script input**에 명령을 입력하고 Enter를 누른다.

| 입력 | 동작 |
| --- | --- |
| `status` | 실제 수신한 VCU 명령과 Motor 상태, 수신 age, USB ACK 표시 |
| `d 10 2` | 전진 10%, 2초 후 정지 |
| `r 10 2` | 후진 10%, 2초 후 정지 |
| `s` 또는 `b` | P / 토크 0 / 브레이크 요청 |
| `quit` | 정지 요청 후 스크립트 종료 |

가속 범위는 0–20%, 실행 시간은 1–10초이다. 기동은 항상 정지 상태이며
Run만 누르면 움직이지 않는다. UART 입력은 COM6로 전달하고 **실제 VCU가 CAN 0x100을 송신**한다.
CANgaroo는 CAN 수신만 담당한다. 기존 `motor_control.py`는 VCU를 대체하는 CAN 직접 송신용이므로
실제 VCU가 연결된 이번 구성에서 함께 실행하지 않는다. TX Generator도 사용하지 않는다.

0x100/0x110 수신, Motor READY/RUN, VCU UART ACK가 있어야 구동된다.
CAN 수신 끊김/실행시간 종료 시 정지로 전환되며 자동 재시작하지 않는다.
Script Stop 강제 중단보다 `s` → `quit`를 우선 사용한다. USB 연결이 끊겨 정지 명령을
못 보내면 VCU의 500 ms 입력 타임아웃이 적용된다. RPM은 기존 가상 모터 모델 값이다.

포트가 바뀌면 Measurement Setup의 COM4와 스크립트의 VCU_PORT=COM6을 각각 수정한다.
스크립트의 CAN 인터페이스 선택 조건에 있는 COM4도 새 CANable 포트로 수정한다.
이 스크립트는 로컬 `tools/can_monitor` 모듈과 전용 Python 환경의 pyserial을 사용한다.
PC Tool 창을 실행할 필요는 없다. 런처가 저장소 위치를 VCU_PROJECT_ROOT로 전달한다. 스크립트가 자동으로 열리지 않으면 Load로 선택한다.

검증: CANgaroo 0.7.0 내에서 스크립트 실행, 실제 COM6 VCU ACK,
COM4의 0x100(P/브레이크/토크0) 및 0x110(READY/RPM0/토크0) 수신을 확인했다.
이후 `d 10 10` 실행과 자동 정지를 CAN 상태로 확인했고, 사용자가 실제 모터 회전·정지를 확인했다.
이 결과는 모터/드라이버의 전기적 한계 또는 내구성 검증을 의미하지 않는다.
내장 Python의 ctypes에 필요한 DLL은 설치된 `C:/msys64/ucrt64/bin` 경로에서 로드한다.


## 통신 구조 및 요구 펌웨어

```text
PC CANgaroo --USB COM6 / ST-LINK UART 115200--> VCU
VCU --CAN 0x100 / 500 kbps--> Motor ECU --PWM--> MDD3A --전력--> 모터
VCU/Motor CAN 버스 --CANable / USB COM4--> PC CANgaroo 모니터
Motor ECU --CAN 0x110--> 같은 CAN 버스
```

이 스크립트는 UART v2 입력과 ACK를 지원하는 VCU 펌웨어용이다.
CAN 입력 전용 펌웨어(`vcu-can-input`)는 UART 입력을 거부하므로 호환되지 않는다.
이번 도구 변경에는 MCU 펌웨어나 보드 자동 다운로드를 포함하지 않는다.
`RUN requested`는 PC 요청 로그이며 개별 수신 완료 로그가 아니다.
UART 스레드가 명령마다 ACK를 검증하고, 초기 성공 및 오류를 출력한다.
모니터의 0x100은 VCU 명령, 0x110은 Motor 응답이며 RPM은 모델 계산값이다.

## 의존성 및 테스트

CANgaroo 0.7.0의 Script View 및 Python 환경이 필요하다.
pyserial 3.5, python-can 4.6.1을 CANgaroo Python에 설치하거나
`tools/can_monitor/.venv` 환경에 설치한다(임베디드 Python과 호환되는 버전 사용).
이 PC의 MSYS Python 3.14 환경에서는 다음으로 준비/검증한다.

```powershell
C:/msys64/ucrt64/bin/python.exe -m venv tools/can_monitor/.venv
tools/can_monitor/.venv/bin/python.exe -m pip install pyserial==3.5 python-can==4.6.1
tools/can_monitor/.venv/bin/python.exe -m unittest discover -s tools/can_monitor -p test_vcu_input.py -v
```

다른 PC의 CANgaroo 설치 위치가 다르면 Start_CANgaroo.cmd를 수정한다.
libffi 등 런타임 경로는 CANGAROO_RUNTIME_DIR 환경변수로 지정할 수 있다.
