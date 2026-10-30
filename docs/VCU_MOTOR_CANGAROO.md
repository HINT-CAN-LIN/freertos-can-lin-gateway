# VCU + Motor + CANgaroo 통합 구성

이 브랜치의 VCU는 USB-UART 입력용이며 캥거루 스크립트와 함께 사용한다.

PC CANgaroo → USB COM6 / ST-LINK UART 115200 → VCU → CAN 0x100 → Motor ECU → PWM → 드라이버 → 모터.
CANable(COM4)은 같은 500 kbps CAN 버스에서 0x100/0x110을 수신해 PC에 표시한다.
PC 스크립트는 CAN 구동 명령을 직접 송신하지 않는다.

## 빌드

STM32CubeIDE에서 firmware/vcu_ECU와 firmware/motor_ECU를 Existing Projects로 가져온다.
각 프로젝트를 Clean/Build하여 Debug makefile을 재생성한다. STM32F446RE 대상이다.
Core, Drivers, FreeRTOS 및 링커 스크립트를 함께 포함했다. 생성된 Debug/Release,
바이너리, 로컬 IDE 설정 및 백업 파일은 버전 관리에서 제외한다.
보드에 다운로드할 때 VCU와 Motor 대상을 구분한다. 이 업로드 작업에서는 보드 플래시를 하지 않았다.

## 동작 조건

- 양쪽 CAN1 PA11(RX)/PA12(TX), Normal mode, 500 kbps. 외부 CAN 트랜시버가 필요하다.
- VCU: HSE bypass 8 MHz, CAN 클럭 45 MHz / prescaler 5 / 18 TQ.
- Motor: CAN 클럭 42 MHz / prescaler 6 / 14 TQ.
- VCU UART 입력 만료 500 ms, Motor CAN 명령 만료 30 ms.
- 캥거루 실행 및 명령은 tools/cangaroo/README.md 참조.
- 0x110 RPM 및 Nm는 모델 값이다. 실측 토크/RPM이 아니다.
- 해당 Motor 구성에서 가속 10%는 정상 구동 시 PWM 듀티 약 10%로 변환된다.
- 2026-10-30: d 10 10 명령, CAN 응답 및 자동 정지를 확인했고 사용자가 실제 회전·정지를 확인했다.
  드라이버 소손 이력도 있어 이 결과는 전기적 안전성/내구성 검증을 의미하지 않는다.

PC→CANable→VCU의 CAN 입력 전용 실험 소스는 이 구성에 포함하지 않는다.
