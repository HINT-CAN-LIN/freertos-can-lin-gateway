# USB LED 시험

현재 light_config.h의 LIGHT_USB_BENCH=1이다. USART1 LIN 수신은 비활성화하고
USART2 PA2/PA3 (115200, 8N1)를 Nucleo의 ST-LINK Virtual COM Port로 사용한다.
기본 NUCLEO-F446RE의 ST-LINK VCP 연결 상태를 전제로 한다.
CANgaroo/CANable/LIN 트랜시버/12V 전원은 이 시험에 필요하지 않다.
PA2/PA3에 다른 외부 UART 장치를 연결하지 않는다.

1. CubeIDE의 기존 디버그를 종료한다.
2. light_ECU를 F5로 새로고침하고 Build, Debug, F8로 실행한다.
3. usb_test/open_control.cmd를 더블클릭한다.
4. 장치 관리자의 STMicroelectronics STLink Virtual COM Port 번호를 선택하고 Connect.
5. 연결 시 모든 명령은 OFF. 원하는 LED 체크박스를 선택한다.
6. 상태가 LIGHT1 cmd=... lamps=... out=... diag=... alive=... err=...로 갱신되는지 확인한다.
7. Send every 50 ms를 해제하면 250ms 뒤 소등, diag=1. 다시 체크하면 명령 재개.
8. ALL OFF는 전체 선택을 해제하고 OFF를 전송한다. 창 종료 시 OFF 전송 후 연결 해제.

Head=D4/PB5, Left=D5/PB4, Right=D6/PB10, Reverse=D7/PA8, Brake=D9/PC7.
각 출력 -> 470ohm -> LED 애노드, 캐소드 -> GND. Hazard는 좌우 동시 점멸.
cmd는 명령값, lamps는 논리 상태, out은 점멸 반영 출력, diag는 진단 상태다.
USB 상태 갱신은100ms이며 실제 LED 전류 피드백은 없다.
PC에서 1초간 유효한 응답을 못 받으면 송신을 해제하며 자동 재개하지 않는다.

수동 시리얼 터미널을 사용하는 경우 명령은 Sxx + LF (xx는 00..3F hex).
S01=head, S02=left, S04=right, S08=hazard, S10=reverse, S20=brake, S00=off.
250ms 타임아웃이 있으므로 유지하려면50ms마다 전송한다.
이는 USB 시험용 프로토콜이며 실제 CAN/LIN 프레임은 아니다.

LIN 복귀: Core/Inc/light_config.h의 LIGHT_USB_BENCH를0으로 변경하고 다시 빌드/다운로드.
조명 로직은 USB와 LIN이 공유하지만 두 입력은 동시에 활성화하지 않는다.

검증: ARM 빌드/링크 경고 없음, 프로토콜/IRQ/USB 파서 호스트 테스트 통과,
Windows 제어창 생성 및 PowerShell 구문 검사 통과.
보드 다운로드, COM 포트 송수신, 실제 LED 점등은 사용자가 수행할 하드웨어 검증이다.

## Hardware validation recorded 2026-10-29

User confirmed USB command/status exchange, all five LEDs, direction/hazard
blinking, 250ms timeout OFF and recovery. Initial left/right LED failure was
resolved by correcting GND wiring. Actual LIN bus validation remains pending.
