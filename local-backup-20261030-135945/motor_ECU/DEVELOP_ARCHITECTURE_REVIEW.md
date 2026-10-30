# Motor ECU / develop 대조 검토

> 검토 후 조치(2026-10-17): F1의 로컬 Byte3 충돌은 SteeringAngle을 Byte4..5로 이동해 수정했다. DBC0.7 / script1.4 / firmware revision4가 현재 규격이다. 아래 본문은 수정 전 커밋 대조 기록이며, F2/F3/F4는 해결되지 않았다. 최신 배치는 `network/can/MOTOR_STEERING_INTERFACE.md`를 따른다.

검토일: 2026-10-17. 원격 `origin/develop`를 fetch한 커밋 **226e88e076171037d9e115e9722ec3cbdc18e268**을 기준으로 현재 작업 디렉터리의 Motor ECU를 검토했다. 원격 파일을 현재 소스에 덮어쓰지 않았다. 이 작업에서는 펌웨어와 공식 DBC를 변경하지 않았다.

판정: **기본 CAN/Virtual Motor/Local Fail-safe 구조는 부합하지만, 통합 완료 또는 문제 없음으로 판정할 수 없다.** 특히 로컬 조향 신호와 Gateway의 Body Command 후보가 같은 비트를 사용한다.

## 1. 우선 해결할 발견 사항

### F1 [P1, 통합 차단] 조향각과 Gateway Body Command 후보의 Byte3 중복

- 현재 `Core/Src/motor_can.c:22`, `cangaroo/motor_ecu.dbc:20` 인근: SteeringAngle은 0x100 bit24부터 signed 16bit, 즉 Byte3~4이다. 송신 스크립트도 같은 형식이다.
- 최신 `docs/design/gateway/01__Gateway_Routing_Table_v1.0_최종.xlsx`의 DEC-01/02, IFC-02~06은 **같은 Byte3**에 HeadLampRequest(bit24), TurnLampRequest(25~26), HazardLampRequest(27), DoorLockRequest(28~29), WindowCommand(30~31)를 제안한다.
- Gateway SW Architecture PDF는 이 다섯 신호가 **DBC/Matrix 반영과 상대 검토 전에는 공식 인터페이스가 아니며 disable 또는 diagnostic-only**라고 명시한다. 현재 공식 DBC에는 Body Command도 SteeringAngle도 없다. 이미 확정된 Body 인터페이스를 위반했다고 단정하는 것이 아니라, 통합할 수 없는 두 확장이 공존하는 상태다.
- 재현: 조향 -20도는 raw -200, Byte3~4=`38 FF`. Body 후보로 읽으면 Hazard=1, DoorLock=3(INVALID)가 된다. 반대로 Window UP을 Byte3=0x40으로 보내면 현재 Motor ECU는 조향 +6.4도로 해석한다. Byte4가 0이라는 예시 조건이다.
- 조치: 공식 인터페이스에서 비트 배치를 하나로 합의하고 DBC, Message Definition, VCU, Motor, Gateway, PC 스크립트를 함께 변경한다. 예를 들어 **Byte3는 Body 후보로 남기고, 다른 미할당 16bit 위치를 조향 후보로 검토**할 수 있으나 다른 확장과의 중복 확인/리뷰 전에는 확정하지 않는다. 임의로 새 배치를 적용하지 않았다.

### F2 [P1, 물리 출력 견고성] CPU fault 시 마지막 PWM 출력이 남을 수 있음

- `Core/Src/stm32f4xx_it.c:88` 이후 HardFault/MemManage/BusFault/UsageFault 핸들러는 출력 정리 없이 무한 루프에 진입한다.
- TIM1/3/4와 TIM2는 하드웨어 PWM이므로 task 실행이 멈춰도 마지막 CCR 출력이 계속될 수 있다. 1ms task 기반 watchdog은 이때 실행되지 않는다.
- `Error_Handler()`와 malloc/stack overflow hook에는 SafeStop 경로가 있으나 위 예외들은 그 경로를 호출하지 않는다. IWDG/WWDG도 활성화되어 있지 않다.
- 조치: fault 핸들러에서도 RTOS mutex에 의존하지 않는 최소 출력 차단 경로를 마련하고, CPU 정지/스케줄러 정지까지 다루려면 독립 watchdog 및 하드웨어 출력 차단을 별도 설계한다. 이는 기존 문서에 수치가 정해진 요구사항 위반 판정이 아니라, 실제 모터를 연결한 구현의 코드상 결함/검증 공백이다.
- 실물 fault injection으로 PWM 차단과 reset 후 기본 출력까지 검증해야 한다. 이번 검토에서는 fault를 실제 보드에 주입하지 않았다.

### F3 [P2] CAN bus-off 뒤 자동/소프트웨어 복구 경로 없음

- `Core/Src/main.c:455`: AutoBusOff=DISABLE. 수신 notification은 RX_FIFO0_MSG_PENDING만 활성화한다.
- 애플리케이션에 bus-off 감시/오류 callback/복구 상태 머신 또는 재초기화 경로가 없다.
- bus-off 후 새 VCU 프레임을 받지 못하면 기존 30ms timeout으로 출력은 정지한다. 그러나 배선을 복구해도 정상 프레임을 다시 수신할 경로가 보장되지 않아, 전원/리셋 없이 통신 복귀를 검증할 수 없다.
- 조치: CAN 상태 관측, 복구 방식(ABOM 또는 관리된 재시작), 큐/Alive 재동기화 정책을 정하고 테스트한다. 복구 동안 출력 inhibit를 유지해야 한다. 하위 Motor SW에서 구체 정책을 정의할 항목이며, Gateway 전용 task/정책을 그대로 복사할 사안은 아니다.

### F4 [P2, 정책 정렬 필요] “정상 3회 확인”과 seed 제외 계수의 차이

- D07 보고서 PDF 실제 7쪽 §5.1, 통신사양서 POL-001/OPN-06은 정상 VCU_Command + Valid + Alive **3회 연속 확인**을 요구한다.
- `Core/Src/motor_watchdog.c:39`의 최초 프레임은 Alive seed만 설정한다. 다음 세 번의 연속 증가를 세므로 timeout 후 실제 **4프레임**에서 inhibit가 해제된다.
- 모듈 실행 재현: frame1 inhibit=1/count0, frame2=1/1, frame3=1/2, frame4=0/0. 10ms 주기의 정상 프레임이면 첫 복구 프레임 기준 30ms 뒤 해제한다.
- 이는 한 프레임으로 성급하게 복귀하는 오류는 아니다. 첫 Alive를 seed로 보는 것이 필요한 상황이 있으므로 단순히 임계값만 2로 바꾸면 안 된다. 문서의 3회가 프레임 세 개인지, seed 이후 Alive 일치 세 번인지 명시하고 Gateway의 관측 기준 및 시험 기대값과 맞춰야 한다.

## 2. 공식 인터페이스와 로컬 확장

공식 `network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc`는 VERSION 0.4이고 SHA256은 `12fb32d996a468e9bdc9dc8fdab295e124e2ffcb51a971530b289b540f15a727`이다. 이전 사용자 Downloads 파일의 해시와 구분해야 한다.

6개 메시지, 기존 **24개 신호의 정의 줄**을 로컬 DBC와 기계적으로 비교했으며 start/length/byte order/sign/factor/offset/range/unit/receiver 차이는 없었다. 이는 펌웨어가 여섯 메시지를 모두 구현한다는 뜻은 아니다. Motor ECU는 0x100/0x300을 수신하고 0x110을 송신한다.

| 로컬 추가 신호 | 위치 | 공식 develop 상태 |
|---|---|---|
| SteeringAngle | 0x100 bit24, signed16, 0.1도 | 없음, Gateway Byte3 후보와 중복 |
| SteeringTargetEcho | 0x110 bit40, signed16 | 없음, 기존 Reserved 사용 |
| LocalFaultFlags | 0x110 bit56, 4bit | 없음 |
| FirmwareRevision | 0x110 bit60, 4bit | 없음 |

추가 신호는 사용자 요청에 따른 시험용 확장이다. 기존 기본 신호는 읽히지만, **공식 DBC를 쓰는 다른 ECU/PC가 조향·echo·상세 진단을 알 수는 없다.** 공식 Message Definition의 Byte3~7 및 상태 Byte5~7은 Reserved이다. 이 확장을 공식 표준으로 취급하려면 관련 산출물 동기화가 필요하다. `left/right` 조향 명령과 LightStatus의 LEFT_TURN/RIGHT_TURN 램프 상태는 다른 기능이다.

## 3. 요구사항 대조 결과

| 기준 | 현재 구현 | 판정 |
|---|---|---|
| SYS_REQ_009 CAN 500kbps | APB1 42MHz / prescaler6 / (1+11+2) TQ | 정적 설정 일치 |
| 0x100 VCU_Command, Standard/DLC8/10ms | exact ID 필터, envelope 검사, 스크립트 10ms | 일치, 버스 실제 jitter는 미측정 |
| Torque 0.1Nm, Gear 0=P/1=N/2=D/3=R, Brake bit19, Alive bit20~23 | 디코더/정책 및 script 일치 | 일치 |
| Torque invalid0xFFFF, Gear4~6 reserved/7invalid | torque>40000 / gear>3 inhibit | 일치 |
| SYS_REQ_004/037 Virtual Motor 유지 | target RPM, 1차 응답 모델, 상태 생성; 실측 RPM 아님 | 일치 |
| SYS_REQ_046 보조 DC 출력 | 별도 actuator task가 모델 target을 PWM으로 매핑 | 구조 일치, 전류/실회전 feedback 없음 |
| SYS_REQ_020 age>30ms | 캡처 시각, 1ms control 및 actuator 검사 | 논리 일치, 실물 최대 차단 지연 미측정 |
| SYS_REQ_024/051 Local Fail-safe | torque=0 / targetRPM=0 / RPM decay; Gateway clear 불필요 | 정상 task 실행 범위에서 일치 |
| Alive modulo16 / critical VCU invalid | strict next counter, discontinuity inhibit | 일치 |
| D07 / POL-001 복구 3회 | seed + 연속 증가3회 | F4 계수 정의 정렬 필요 |
| Motor_Status0x110/DLC8/10ms | 기존 4신호 encode, TX queue, stale20ms 폐기 | 기본 형식 일치; 실물 전송 성공/주기는 별도 검증 |
| Gateway의 Fault_Status0x310 전파 | Motor가 송신하지 않음 | 책임 분리에 부합; Gateway E2E는 별도 검증 |
| Motor_Status timeout / speed 환산 | Motor에서 임의 Gateway timeout/VehicleSpeed 생성 안 함 | 적절, 하위 담당 정책과 구분 |
| CANable PC 진단 | CANgaroo script/API mock | 도구 경로 일치, 이번 실물 통합 미수행 |

TorqueApplied와 RPM은 demonstrator 모델 값이며 실측 토크·실측 축 RPM으로 주장하면 안 된다. D/R 전환은 물리 출력에 200ms zero interval을 둔다. SYS_REQ_046이 실제 12000RPM/4000Nm 하드웨어 성능을 요구한다는 뜻도 아니다.

## 4. RTOS와 핀 배치

- CMSIS-RTOS2 / FreeRTOS V10.3.1, 5 tasks, 2 queues, 2 priority-inheritance mutexes로 분리되어 있다. Gateway 문서에 나오는 RoutingTask/LINSchedulerTask/Signal Cache는 Gateway 소유이므로 Motor ECU에 동일하게 구현할 요구는 없다.
- RX ISR은 timeout0 queue put만 수행하며 mutex를 잡지 않는다. CAN RX IRQ priority5, max syscall priority5, SysTick15 설정이다.
- runtime 상태 접근은 mutex로 직렬화하며, PWM은 actuator task, HAL TX는 TX task가 담당한다. 큐 포화, mutex 실패, stale TX 처리 회귀는 통과했다.
- 현재 `.ioc`와 수동 PWM 초기화에서 확인한 채널은 다음과 같고, 이 범위에서 중복은 발견하지 못했다.

| 기능 | MCU 핀 |
|---|---|
| CAN RX/TX | PA11 / PA12 |
| Motor1 A/B | PA8 / PA9 (TIM1 CH1/2) |
| Motor2 A/B | PB4 / PB5 (TIM3 CH1/2) |
| Motor3 A/B | PB0 / PB1 (TIM3 CH3/4) |
| Motor4 A/B | PB6 / PB7 (TIM4 CH1/2) |
| Servo1/2 | PA0 / PA1 (TIM2 CH1/2) |
| UART2 / LED / SWD | PA2/PA3 / PA5 / PA13/PA14 |

핀 중복 검사는 소스/설정 기준이다. 보드 헤더 위치, 트랜시버 배선, 외부 전원 및 실제 연결 확인을 대신하지 않는다. BOM에는 MDD3A 두 개가 포함되어 있으나 SG90 조향은 공식 아키텍처에 정의되지 않은 사용자 확장이다. 서보 50Hz, center1500us, 현재 최대명령±45도→1250..1750us이며 **직전 답변의 2배 변환 예시는 아직 코드에 적용되지 않았다.** 실제 각도는 미보정이다.

재생성 주의: `freertos.c` task 본문은 CubeMX USER CODE 보존 구획 밖에 직접 관리되고, main의 커널 초기화 경로도 생성 코드와 차이가 있다. `.ioc` Generate Code 뒤 무검토 빌드/다운로드는 피하고 diff와 전체 빌드를 확인해야 한다. 현재 기존 빌드 통과가 재생성 보존성을 검증한 것은 아니다.

## 5. 문서 내부 불일치와 기준 우선순위

- 최신 Gateway 아키텍처 PDF도 Freeze 전 통합 초안임을 밝힌다. 문서명에 '최종'이 있어도 표의 Pending Review/TBD는 그대로 남아 있다.
- 공식 DBC/Value_Table은 Gear0..3, Brake Invalid=N/A, Alive15 유효값이다. 메시지 정의 Excel의 CAN_Signal_Definition에는 Gear 최대5, Brake Invalid=1, Alive Invalid=0xF 같은 오래된 셀이 남아 있다. 해당 파일의 Review/Value_Table 및 DBC 보고서가 교정 방향을 설명한다. 현재 코드가 Gear4/5를 거부하고 Brake1을 정상 제동으로 해석하며 Alive15를 허용하는 것은 DBC와 일치한다.
- `docs/CAN_COMMUNICATION_MATRIX.md`, `FAULT_AND_FAILSAFE_SPEC.md`, `GATEWAY_SW_ARCHITECTURE.md`, `HARDWARE_SETUP.md`, `LIN_SPECIFICATION.md`, `TEST_PLAN_AND_RESULTS.md`는 실제 명세/결과 대신 작성 안내가 있는 placeholder다. 이 문서만 보고 적합성을 선언할 수 없다.
- 과거 archive, 라우팅 v0.1~0.4, Gateway 초기 RTOS workbook은 배경 자료로 비교했으며 최신 Aligned/하위 결정의 대체 기준으로 쓰지 않았다. LIN 스케줄·Door/Light/Window 로직은 Motor 직접 구현 범위 밖이다.

## 6. 검증 및 범위

- 이번 실행: C 제어 회귀 PASS, 실제 task 함수에 CMSIS2 mock을 연결한 RTOS 회귀 PASS, CANgaroo mock 10 tests PASS.
- 별도 재현으로 F1 바이트 중복, F4의 네 프레임 복구, 서보 현재 펄스 범위를 확인했다. 기계적 DBC 비교 산출물은 `tmp/motor_audit_develop/dbc-comparison.json`에 보관했다.
- 전체 ARM Debug 빌드는 직전 RTOS 변경 작업에서 통과했다. 이번 검토에서는 펌웨어를 변경하지 않아 ARM 빌드를 반복하지 않았다.
- 원격 docs/network/README 스냅샷과 추출 문서 목록: `tmp/motor_audit_develop/reviewed-document-inventory.md`. PDF 텍스트/Excel 행/Word 단락을 추출해 Motor 요구사항과 인터페이스 관련 내용을 대조했고, 선택한 PDF의 복구/적용 범위 페이지는 시각 확인했다. 모든 PDF 도표의 전 페이지 시각 검수나 모든 타 ECU 펌웨어 전수 검증을 의미하지 않는다. 조달 PDF의 일부 인코딩 한계는 BOM Excel로 보완했다.
- 실물 CAN bus-off/복구, 타 ECU와 공동 버스, 30ms 차단 latency/jitter, RTOS 선점·최대 mutex 보유 시간·stack 여유, CPU fault 출력, 전원/전류, 모터/서보 기구 및 PWM 측정은 미수행이다. 이 증거가 없으므로 시스템 통합 시험 완료를 주장할 수 없다.

## 7. 권장 처리 순서

1. F1 조향/Body 비트 충돌부터 인터페이스를 확정하고 관련 문서와 송수신 코드를 함께 반영한다.
2. F2 CPU fault 출력 차단, F3 bus-off 복구를 구현하고 주입 시험을 추가한다.
3. F4 복구 계수 기준을 명문화하고 Motor/Gateway의 동일 로그를 비교한다.
4. 공식 DBC로 기본 신호를, 합의된 확장 DBC로 조향·진단을 확인한 뒤 실물 E2E 증거를 기록한다.

기준 저장소: https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/tree/226e88e076171037d9e115e9722ec3cbdc18e268
