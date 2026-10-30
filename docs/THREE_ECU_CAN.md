# VCU–Motor–Cluster CAN 연결

세 프로젝트는 STM32F446RE의 CAN1(bxCAN), Normal 모드, 500 kbit/s,
표준 11비트 ID, 데이터 프레임, DLC 8을 사용한다.

| ECU | APB1 CAN 클럭 | Prescaler | BS1 / BS2 | RX / TX |
| --- | --- | --- | --- | --- |
| VCU | 45 MHz | 5 | 15 / 2 TQ | PA11 / PA12 |
| Motor | 42 MHz | 6 | 11 / 2 TQ | PA11 / PA12 |
| Cluster | 42 MHz | 6 | 11 / 2 TQ | PA11 / PA12 |

비트레이트 = CAN 클럭 / Prescaler / (1 + BS1 + BS2).
VCU는 기존 설정대로 8 MHz HSE bypass(ST-LINK MCO)를 사용한다.
Motor와 Cluster는 HSI 기반 PLL을 사용한다. 보드 클럭 배선은 기존 설정과 같아야 한다.
세 ECU의 자동 bus-off 복구와 자동 재전송을 활성화했다.

## 배선과 다운로드

1. 각 보드의 PA12(TX)를 CAN 트랜시버 TXD, PA11(RX)을 RXD에 연결한다.
2. 트랜시버의 CAN_H끼리, CAN_L끼리 연결하고 보드 GND를 공통으로 연결한다.
3. 버스 양 끝에만 CAN_H–CAN_L 사이 120 Ω 종단저항을 둔다.
4. 트랜시버의 전압 및 EN/STB 설정은 사용 중인 모듈에 맞춰 활성화한다.
5. CubeIDE에 세 프로젝트를 각각 import하고 각 보드에 해당 프로젝트를 빌드/다운로드한다.
   저장소의 Debug makefile에는 업로더 PC 경로가 있으므로 CubeIDE에서 재생성한다.

## 메시지 흐름

| 송신 | ID | 주기 | 수신 및 용도 |
| --- | --- | --- | --- |
| VCU | 0x100 | 10 ms | Motor 구동 명령, Cluster 기어 표시 |
| Motor | 0x110 | 10 ms | Cluster RPM 및 모터 상태 표시 |

TorqueRequest는 byte 0–1의 little-endian unsigned 16비트(0.1 Nm),
Gear는 byte 2 bit 0–2(P=0, N=1, D=2, R=3), Brake는 bit 3,
AliveCounter는 bit 4–7이며 0–15 순환이다.
Motor_Status는 byte 0–1 RPM, byte 2–3 TorqueApplied(0.1 Nm),
byte 4 bit 0–1 MotorState, bit 2–5 AliveCounter이다.
기본 필드는 network/can의 DBC와 세 코드에서 일치한다.

VCU는 기동 시 OFF/P/토크 0이다. 기존 USB-UART 입력 경로로 RUN, D 또는 R,
가속 입력을 보내야 구동되며 입력 갱신이 끊기면 기존 입력 타임아웃 정책이 적용된다.
Motor는 첫 Alive 표본과 이후 3회 연속 증가를 확인한 뒤 구동을 허용한다.
VCU 명령이 30 ms를 초과해 끊기면 fail-safe가 적용된다.
벤치용 고정 Alive 허용 옵션은 꺼져 있다.

## Gateway 없이 표시되는 항목

Cluster는 신선한 0x120 Vehicle_Status가 있으면 기존 Gateway 요약 표시를 유지한다.
없거나 오래되면 RPM은 Motor 0x110, 기어는 VCU 0x100에서 직접 가져온다.
직접 받은 RPM/기어 변경에도 화면을 갱신하고, 유효하지 않거나 오래된 값은 `--`로 표시한다.
표시 freshness 기준은 기존 정책인 stale 1000 ms / offline 3000 ms이다.
이는 Motor의 30 ms 제어 타임아웃과 별개다.

속도, 차체 상태, Gateway 종합 상태는 세 ECU만으로 생성되지 않는다.
속도를 임의로 RPM에서 계산하거나 Gateway 메시지를 대신 송신하지 않는다.
Motor RPM은 기존 가상 모터 모델 값이며 실제 회전 센서 측정값이 아니다.

Motor의 로컬 DBC에는 조향/진단 확장이 있지만 현재 VCU는 CAN 조향을 전송하지 않는다.
VCU byte 4–5는 0이므로 Motor 조향은 중앙값이다. VCU byte 3의 도어/창문 요청과
Motor의 추가 진단 바이트는 기존대로 유지하며, 이 작업에서는 공통 DBC를 변경하지 않았다.

## 검증

2026-10-30: 세 ECU ARM 전체 빌드, 통합 테스트, 기존 Motor 제어 테스트 통과.
Cluster의 LVGL 내부 `transform_safe_range` 미사용 함수 경고 1건이 있으며 빌드는 성공했다.
빌드 결과 ELF/BIN은 `output/can-integration/`에 모았다. BIN의 플래시 시작 주소는
각 프로젝트 링커 스크립트 기준 `0x08000000`이다. 실제 보드 플래시는 수행하지 않았다.

`powershell -ExecutionPolicy Bypass -File tools/test_three_ecu_can.ps1`

호스트 GCC로 실제 VCU 인코더 → Motor 수신/상태 생성 → Cluster 디코더를 연결해
Alive 순환, 브레이크, 통신 타임아웃, 직접 표시, Gateway 우선순위,
stale 데이터, 잘못된 기어/DLC/확장·원격 프레임을 검사한다.
기존 Cluster 상태 self-test도 실행한다.
호스트 테스트와 ARM 빌드는 실제 배선, 트랜시버, ACK, 버스 오류 복구 검증을 대신하지 않는다.

보드에서 VCU `vcu_task_stats.tx_accepted`, Motor `g_canTxSuccessCount`,
Cluster `cluster_can_rx_count` 증가를 확인하고, VCU 송신 중단 시 모터 정지와
Cluster 상태/표시 만료를 확인한다.
