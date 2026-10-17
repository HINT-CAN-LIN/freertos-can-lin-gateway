> 최신 RTOS 구성: [RTOS2_ARCHITECTURE.md](RTOS2_ARCHITECTURE.md). CAN RX/TX, 제어, 출력, 상태 감시를 5개 task로 분리하고 공유 상태는 mutex로 보호한다.

> 현재 통합 상태: CANable/cangaroo DC 모터 4개 시험용 코드가 연결되었습니다.
> 제공 스크립트: [cangaroo/motor_control.py](cangaroo/motor_control.py), [사용법](cangaroo/README.md).
> 실행 절차와 현행 정책은 [CANGAROO_DC_MOTOR.md](CANGAROO_DC_MOTOR.md)를 참조하세요.
> 아래 내용은 CAN/PWM 연결 전의 초기 설계 기록입니다.

# Motor application 연결 기록

## 작성 범위

motor_app: CAN decode → 명령 검증 callback → local watchdog → Virtual Motor → Motor_Status.
motor_runtime: 단일 main loop/task에서 호출하는 board entry 및 weak hook.
기존 CAN codec와 watchdog 유지. VCU 명령 생성 및 Gateway Fault_Status 생성은 없음.

현재 Cube main loop에서 HAL_GetTick()으로 Init/Process 호출. RTOS task/ISR 연결 아님.
Receive는 실제 CAN 수신 어댑터에서 호출해야 한다. ISR에서 직접 호출하지 말고,
동일 소유 task에서 캡처 timestamp 순서대로 처리 후 현재 시각으로 Process 호출한다.

## 기본 설정

MotorBoard_Config()는 NULL, MotorBoard_Transmit()는 false를 반환한다.
따라서 기본 상태는 OFF, TorqueApplied=0, RPM=0이며 실제 CAN 송신은 없다.
MotorRuntime_State()로 configured, watchdog, rpm, tx_failures 등을 디버거에서 확인 가능.
tx_failures는 현재 미연결 transport 시도도 포함하며 실제 CAN bus error count가 아니다.

승인 후 별도 board C 파일에서 두 weak hook을 재정의한다. Config에는
torque_to_rpm(rpm/Nm), alpha, decay_alpha, rpm_max, model_period_ms, policy가 필요하다.
임의 기본 모델 계수는 제공하지 않음. tests/test_app.c 수치는 합성 테스트 전용.
policy는 Brake/Alive Invalid 충돌과 Motor 측 Gear/Brake 제약을 해결해야 한다.
모듈은 토크 범위와 Gear 0~3을 검사하고 요청 토크를 초과하는 policy 결과를 거부한다.

## 구현 제안 — 상대 담당자 리뷰 필요

- 모델: 핸드북 9.2 1차 응답. elapsed dt에 대해 유효 alpha = 1-(1-alpha)^(dt/period).
  입력은 마지막 명령을 유지하는 이산 모델. 명령 경계에 걸친 dt 적용 방식도 리뷰 대상.
- timeout: age > 30 ms. 출력 토크/target 즉시 0, 모델 RPM은 decay_alpha로 감쇠.
- 상태: 설정 없음/초기 동기화 OFF, 유효 출력 또는 잔여 RPM이면 RUN, 정지 READY,
  timeout/invalid/Alive 오류 FAIL_SAFE. VCU ignition/state machine을 구현하지 않음.
- TX: 10 ms 시도, 실패 시 Alive 유지, transport 수락 시 증가. 실제 버스 송신 완료
  보장이 아니므로 HAL mailbox 취소/bus-off/재전송 처리와 함께 확정할 것.
- Gateway_Status는 관측만 수행. timeout/health 제어 임계값 미정.
- FreeRTOS task/queue/IRQ 우선순위, CAN loopback/HAL 초기화는 후속 통합 대상.

## 검증

호스트 C11 경고 오류 빌드 및 test_app PASS: 응답 계산, timeout/감쇠/복구,
테스트용 Brake 정책, TX 실패 시 Alive 유지, 토크 증폭 거부, 설정 차단.
기존 test_motor도 유지. 보드 timing/jitter 실측 없음.

Jira 1~3일 Task: 모델/정책 리뷰; CAN loopback 어댑터; FreeRTOS 통합/외부 Fault 전파 검증.
현재 전체 DoD 완료 아님. 핸드북 표 15-6/15-7, 표 2-3/15-11 검토 필요.
