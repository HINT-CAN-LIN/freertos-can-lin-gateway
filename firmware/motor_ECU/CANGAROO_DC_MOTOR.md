> 최신 RTOS 구성: [RTOS2_ARCHITECTURE.md](RTOS2_ARCHITECTURE.md). CAN RX/TX, 제어, 출력, 상태 감시를 5개 task로 분리하고 공유 상태는 mutex로 보호한다.

> 조향각 추가 업데이트: `cangaroo/motor_ecu.dbc` 로컬 v0.7와
> `cangaroo/motor_control.py` v1.4를 사용한다.
> Byte4..5에 단일 SteeringAngle(0.1도, signed, -45..45)을 추가했다.
> 펌웨어 revision 4에서 PA0/PA1의 SG90 PWM을 활성화했다. 최신 진단/동시명령은 README를 따른다.
> 최신 명령과 인터페이스 설명은 [cangaroo/README.md](cangaroo/README.md)를 참조한다.
> 아래 원본 해시는 확장 전 사용자 DBC의 해시이다.

# CANable / cangaroo DC 모터 시험

## 구현 범위

NUCLEO-F446RE 한 대, MDD3A 두 대, DC 모터 네 개를 사용한다.
SG90의 TIM2/PA0/PA1 출력은 50Hz로 구동한다. 부팅/실패 시 중앙 펄스 1500us가 적용된다.
네 모터에는 같은 크기의 출력이 적용된다. DBC에는 모터별 명령이 없다.

기준: 사용자가 제공한 `CAN_DB_펌웨어 전 최종본_v0.1.dbc`.
파일 내부 VERSION은 `0.4 - review-ready interface proposal`이다.
제공 파일 SHA256: `D982916F61245E96518E422BC84FC59E0C9A121EA25CB19F227E901700E4FFF4`.
저장소 network/can의 유사한 이름 파일과 해시가 다르므로 시험에는 사용자가 제공한 DBC를 불러온다.

| 메시지 | 표준 CAN ID | DLC | 주기 | 동작 |
|---|---|---|---|---|
| VCU_Command | 0x100 (십진수 256) | 8 | 10 ms | PC가 VCU 대신 송신 |
| Motor_Status | 0x110 (십진수 272) | 8 | 10 ms | Motor ECU 송신 |
| Gateway_Status | 0x300 | 8 | 100 ms | 수신 관측만 수행, 단독 시험에 불필요 |

CAN bitrate는 500 kbit/s, Classic CAN, 11-bit Standard, Data frame이다.
PC에서 0x110을 송신하지 않는다. 모터의 응답 ID이다.

## 배선

| ECU 핀 | Nucleo 커넥터 | MDD3A 입력 |
|---|---|---|
| PA8 | CN10-23 | 드라이버 #1 M1A |
| PA9 | CN10-21 | 드라이버 #1 M1B |
| PB4 | CN10-27 | 드라이버 #1 M2A |
| PB5 | CN10-29 | 드라이버 #1 M2B |
| PB0 | CN7-34 | 드라이버 #2 M1A |
| PB1 | CN10-24 | 드라이버 #2 M1B |
| PB6 | CN10-17 | 드라이버 #2 M2A |
| PB7 | CN7-21 | 드라이버 #2 M2B |

각 모터의 두 전선은 해당 MDD3A 모터 출력 두 단자에 연결한다.
모터 정격 전압을 외부 전원에서 MDD3A 두 대에 병렬 공급한다.
모터 기동/스톨 전류와 네 개 동시 운전 전류를 전원/드라이버 정격과 대조한다.
ECU GND, 드라이버 GND, 모터 전원 음극을 공통 연결한다.
MDD3A 5V 출력은 USB로 구동 중인 Nucleo에 연결하지 않는다.

CAN은 PA12 -> SN65HVD230 TXD(D), PA11 <- RXD(R), 트랜시버 VCC=3.3V이다.
CANable CANH/CANL을 트랜시버 CANH/CANL과 연결하고 GND 기준도 연결한다.
CAN 버스 양 끝에만 120옴 종단을 둔다. 모듈 내장 종단도 포함해 확인한다.

## 권장: CANgaroo Python 스크립트

현재 펌웨어 기본은 Alive 순번 검사 활성화(`MOTOR_CANGAROO_FIXED_ALIVE=0`)이다.
`cangaroo/motor_control.py`를 Script View에서 Load하고 Run한다.
자세한 실행 순서는 [스크립트 사용법](cangaroo/README.md)을 따른다.
스크립트는 P/토크 0으로 시작하며 `d 10 5`, `r 10 5`, `s`를 입력해 제어한다.
사용자 제공 DBC 복사본도 `cangaroo/motor_ecu.dbc`에 포함했다.

## 선택: 고정 Raw TX 설정과 송신 데이터

아래 고정 payload 예제는 명시적으로 `MOTOR_CANGAROO_FIXED_ALIVE=1`로 바꾸고
재빌드한 벤치 시험에서만 운전에 사용할 수 있다. 현재 기본 빌드는 증가하는 Alive가 필요하다.

1. 현재 빌드한 `Debug/motor_ECU.elf`를 ST-LINK로 다운로드하고 실행한다.
   이미 소스에 PWM 초기화가 있으므로 시험을 위해 CubeMX 재생성을 먼저 할 필요는 없다.
2. CANable 펌웨어에 맞는 SLCAN 또는 Candlelight 인터페이스를 선택한다.
   500 kbit/s의 일반 통신 모드를 사용한다. Listen-only 모드는 사용하지 않는다.
3. DBC를 불러오고 측정을 시작한다. 0x110 상태가 10 ms 간격으로 보이는지 확인한다.
4. Raw TX에서 ID `100`(HEX), DLC `8`, Extended/RTR/FD/BRS 해제,
   반복 간격 `10 ms`를 설정한다. 단발 Send만으로는 운전 상태가 유지되지 않는다.
5. 아래 중 한 행만 반복 송신한다. 명령을 바꿀 때 기존 반복 송신을 중지한 뒤
   데이터를 수정하고 다시 시작한다. 서로 다른 명령 두 개를 동시에 반복하지 않는다.

| 동작 | DATA (HEX, 8 bytes) | TorqueRequest | 데모 출력 |
|---|---|---|---|
| D, 0% | `00 00 02 00 00 00 00 00` | 0 Nm | 정지 |
| D, 10% | `A0 0F 02 00 00 00 00 00` | 400 Nm | PWM 10% |
| D, 25% | `10 27 02 00 00 00 00 00` | 1000 Nm | PWM 25% |
| D, 50% | `20 4E 02 00 00 00 00 00` | 2000 Nm | PWM 50% |
| R, 10% | `A0 0F 03 00 00 00 00 00` | 400 Nm | 반대 방향 PWM 10% |
| D + Brake | `A0 0F 0A 00 00 00 00 00` | 400 Nm | 출력 0 |
| P | `00 00 00 00 00 00 00 00` | 0 Nm | 출력 0 |
| N | `00 00 01 00 00 00 00 00` | 0 Nm | 출력 0 |

낮은 듀티에서 실제 모터가 움직이지 않을 수 있다. 부하와 모터 기동 특성에 따라 달라진다.
기계적으로 고정한 상태에서 처음에는 10% 명령부터 확인한다.

`TorqueRequest_raw = TorqueRequest_Nm * 10`이며 Byte0=하위, Byte1=상위 바이트이다.
Byte2는 `(AliveCounter << 4) | (Brake << 3) | Gear`이다.
Gear는 0=P, 1=N, 2=D, 3=R이다. Byte4..5는 확장 SteeringAngle 요청, Byte3와 Byte6..7은 0으로 송신한다.

## Alive 벤치 옵션

`main.c`의 `MOTOR_CANGAROO_FIXED_ALIVE=0`이 현재 기본이다.
Python 스크립트가 Alive를 증가시키므로 실제 VCU와 같은 순번 검사를 사용한다.
고정 Raw TX 벤치만 시험할 때 명시적으로 1로 바꾸면 다음 예외가 적용된다.
cangaroo의 기본 Raw TX가 동일 payload를 반복하므로 같은 Alive 값도 정상 수신으로 허용한다.
이는 PC 구동 시험 전용 정책이며, Alive 고착 검출을 완화한다.
잘못된 토크/Gear 차단과 30 ms timeout은 이 옵션에서도 동작한다.
Alive를 변경한다면 정상 증가는 +1 modulo 16을 사용한다.

실제 VCU/Alive 고장 시험과 제공 Python 스크립트에서는 이 값을 **0**으로 유지한다.
이 경우 고정 payload 반복으로 운전할 수 없다. Byte2의 상위 니블을
`0,1,...,F,0,...`으로 10 ms마다 증가시켜야 한다.
예: D 10%는 `A0 0F 02 ...`, `A0 0F 12 ...`, `A0 0F 22 ...` 순서다.

시작/timeout 이후에는 첫 프레임으로 Alive 기준을 잡고, 이후 정상 관계를 세 번 확인한다.
10 ms 반복이면 네 프레임이 필요하다. 정상 운전 중 순번 오류도 세 번 정상 관계 확인 후 복구한다.

## 제어 정책과 상태 확인

- 입력 범위: TorqueRequest raw 0..40000, Gear 0..3. raw 0xFFFF/범위 초과/Gear 4..7은 차단한다.
- P/N/Brake/토크 0에서는 물리 출력 0. 명령 수신 age > 30 ms에서도 출력 0.
  timeout 검사는 제어 및 출력 task에서 약 1 ms마다 수행하며 실물 정지 지연은 아직 측정하지 않았다.
- D/R 전환은 출력 0을 200 ms 연속 유지한 뒤 반대 방향을 인가한다.
  이 시간은 데모 정책이며 실제 축 정지를 확인하는 피드백은 없다.
- 20 kHz PWM. D는 A=PWM/B=0, R은 A=0/B=PWM. 정지는 A=B=0.
  출력 0은 축이 즉시 정지한다는 의미가 아니다.
- 가상 모델: TargetRPM = min(TorqueRequest_Nm * 3, 12000).
  물리 듀티는 TargetRPM / 12000이다. 따라서 400 Nm -> Target 1200 RPM -> 10%.
  이 계수는 DBC에 없는 데모 보정값이며 `main.c`에 명시했다.
- Motor_Status.RPM은 가상 모델의 현재 RPM이다. 엔코더가 없으므로 실제 RPM/토크 측정값이 아니다.
  가상 RPM은 10 ms 기준 정상 응답 계수 0.10, fail-safe 감쇠 계수 0.20으로 갱신한다.
- Mirror 장착 때문에 특정 모터만 반대로 돌면 `MOTOR_DIRECTION_INVERT_MASK`의
  해당 비트를 1로 설정한다. bit0..3은 모터1..4이다. 예: 2/4번 반전은 0x0A.
- Queue overflow는 출력 차단 및 runtime 재동기화로 처리한다.
  Gateway 생존 여부는 이 단독 시험의 운전 조건이 아니다.

0x110 Byte0..1=가상 RPM, Byte2..3=TorqueApplied raw, Byte4 bits0..1=MotorState,
bits2..5=AliveCounter이다. Byte5..6=검증된 조향 목표 echo, Byte7 하위니블=고장 flags, 상위니블=firmware revision이다. State 0=OFF, 1=READY, 2=RUN, 3=FAIL_SAFE.
400 Nm 명령의 정상 응답에서 TorqueApplied는 `A0 0F`, RPM은 점차 1200으로 접근한다.

디버거에서 `g_motorDuty`(0..4200), `g_motorDirection`(-1/0/+1),
`g_canTxSuccessCount`, `g_canTxErrorCount`, `g_canRxDropCount`,
`MotorRuntime_State()`를 확인할 수 있다. TX success는 mailbox 접수 횟수이며 버스 전달 보장은 아니다.

## 검증과 빌드

STM32CubeIDE의 기존 Debug 설정으로 빌드한다. PWM은 `main.c` USER CODE 구간에서
GPIO 대체 기능과 TIM1/3/4 레지스터를 초기화한다. HAL TIM 파일 추가 없이 현재 프로젝트로 빌드 가능하다.
수신 ISR은 프레임과 캡처 시각을 큐에 넣고, CanRxTask 하나가 decode/model/PWM/status TX를 소유한다.
CanTxTask의 고정 1000 RPM 테스트 송신은 제거했다.

호스트 회귀 테스트(저장소 루트, GCC 필요):

```powershell
gcc -std=c11 -Wall -Wextra -Werror -Ifirmware/motor_ECU/Core/Inc firmware/motor_ECU/tests/test_motor_control.c firmware/motor_ECU/Core/Src/motor_app.c firmware/motor_ECU/Core/Src/motor_can.c firmware/motor_ECU/Core/Src/motor_watchdog.c -lm -o firmware/motor_ECU/tests/test_motor_control.exe
./firmware/motor_ECU/tests/test_motor_control.exe
```

검증 완료: 호스트 테스트 및 ARM Debug 빌드. 보드 다운로드, CANable 실통신,
오실로스코프 PWM 측정, 네 모터 실제 회전은 아직 수행하지 않았다.

참고: cangaroo Raw TX 반복 동작은 프로젝트 소스
https://github.com/normaldotcom/cangaroo/blob/master/src/window/RawTxWindow/RawTxWindow.cpp
의 sendRepeatMessage/changeRepeatRate/sendRawMessage에서 확인했다.
