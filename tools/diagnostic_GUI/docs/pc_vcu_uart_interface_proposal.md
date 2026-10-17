# HINT-48 Phase 3N-3 — PC ↔ VCU UART Interface Proposal

- 작성일: 2026-10-17 (Asia/Seoul)
- 상태: **NEEDS_REVIEW / 상세 UART 계약 미승인 / 실제 Serial TX 미구현**
- 범위: 문서 검토만 수행. PC GUI/Python, Firmware, CAN/LIN 산출물은 변경하지 않는다.
- 관련: [이전 CAN 0x600 제안](pc_vcu_can_0x600_interface_proposal.md), [Review Checklist](pc_vcu_uart_review_checklist.md), [Implementation Tasks](pc_vcu_uart_implementation_tasks.md)

## 1. 구조 결정과 변경 영향

Phase 3N-3 지시에 전달된 팀 결정 방향: PC와 VCU 직접 연결, Driver Input과 VCU 응답은 양방향 UART. VCU↔Motor/Gateway/Cluster의 CAN, Gateway↔Body ECU의 LIN 및 PC CANable Pro CAN Monitor는 유지한다.

| 상태 | 기록 |
|---|---|
| 상위 구조 | PC↔VCU direct UART, bidirectional |
| 기존 CAN 0x600 | 대체 대상. 0x600은 과거 CAN ID 후보이며 UART Packet ID로 재사용하지 않는다. |
| CAN/LIN 경로 | 기존 CAN/DBC/Routing/LDF 계약 유지. UART 입력을 Gateway/LIN으로 임의 전달하지 않는다. |
| 상세 계약 | Port, pins, voltage, baud, framing, payload, response, timing, timeout, fail-safe는 TBD/Open |
| 결정 evidence | 방향은 이번 사용자 전달 결정으로 반영. 결정자/date/회의록 등 별도 승인 근거는 제공되지 않았으므로 세부 Interface 승인으로 보지 않는다. |

기존 CAN 0x600 문서 3개는 과거 제안 이력으로 보존한다. 이 문서만으로 공식 기준 산출물이 자동 개정되지는 않는다. Interface owner가 기존 문서의 controlled supersession과 기준 문서를 결정해야 한다.

운전자 입력은 향후 UART, CAN 모니터는 CANable Pro의 별도 경로다. 기존 PC Driver Control은 in-process Mock이며 실제 송신이 없다.

## 2. Source of Truth 조사

| 자료 | 확인 결과 및 적용 |
|---|---|
| [Driver Input Model](../src/pc_diagnostic/gui/driver_input.py) | accelerator=float 또는 None, brake=bool 또는 None, gear/window/light/ignition=str 또는 None. Ignition OFF/ON/RUN, Gear P/N/D/R, Accelerator Mock 범위 0..100%. 이는 Mock 모델이지 UART wire contract가 아니다. |
| [Driver Control View](../src/pc_diagnostic/gui/driver_control_view.py) | 현재 0x600 안내, Live TX Blocked, ECU Applied NOT VERIFIED, Mock Accepted 문구가 있다. 후속 UI 변경 대상이며 이번 단계에서는 수정하지 않는다. |
| [README/VERIFICATION](../README.md) / [VERIFICATION](../VERIFICATION.md) | 기존 python-can SLCAN serial backend는 CANable CAN 연결용이다. 이전 검증 기록에서 pyserial/serial 미설치 상태가 보고됐으며, 이번 작업에서 설치하지 않았다. 이는 PC↔VCU UART 지원 증거가 아니다. |
| [CAN DBC](../../../network/can/CAN__DB_펌웨어%20전%20최종본_v0.1.dbc) | 조사한 DBC에 0x600/0x601은 없다. 기존 CAN 정의는 UART와 별도 유지한다. |
| [Gateway Routing](../../../network/routing/Gateway_Routing_Table_v0.4_CAN_to_LIN_Decision_Baseline.xlsx) | 기존 CAN→LIN 경로이며 PC↔VCU UART route는 확인되지 않는다. |
| [Message Definition](../../../docs/requirements/02__메시지_정의서_ver1.2.xlsx), [System Requirements](../../../docs/requirements/05__요구사항_명세서_ver1.2.xlsx) | 조사 범위에서 PC UART packet/port/timeout 계약 없음. 기존 CAN 수치를 UART에 복사하지 않는다. |
| [HARDWARE_SETUP](../../../docs/HARDWARE_SETUP.md) | 담당자 작성 placeholder. 실제 보드, pin map, voltage, connector 없음. |
| 현재 PC Branch firmware tree | VCU/Gateway 경로는 .gitkeep만 보유, application source 및 CubeMX .ioc 없음. |
| VCU source snapshot (이전 Phase 읽기 전용 조사) | Commit 7abe70f9a013d8cbdd2bb30cdde8cf3102af2973 application source에서 UART application RX/TX/parser/DMA/ISR 경로 미확인. 물리 port capability/Flash 상태는 미확인. [VCU CAN source](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/7abe70f9a013d8cbdd2bb30cdde8cf3102af2973/firmware/vcu_ECU/Core/Src/can.c), [VCU main](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/7abe70f9a013d8cbdd2bb30cdde8cf3102af2973/firmware/vcu_ECU/Core/Src/main.c). |
| Gateway source snapshot (이전 Phase 조사) | Commit 6215ce46e5fcfa1b74f94f39194cd829392755d5의 Gateway USART2/115200은 debug log로 기록됐다. VCU UART 또는 PC link 설정 근거가 아니다. [Gateway main](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/6215ce46e5fcfa1b74f94f39194cd829392755d5/firmware/gateway_ECU/Core/Src/main.c). |
| [CAN Matrix placeholder](../../../docs/CAN_COMMUNICATION_MATRIX.md) | 담당자 작성 placeholder. 전체 ID registry나 UART contract가 아니다. |

따라서 VCU 보드 모델, 정확한 MCU, UART/USART, TX/RX pins, logic level은 확정할 수 없다. STM32 HAL 또는 다른 ECU의 USART 설정을 VCU 하드웨어 근거로 확대하지 않는다.

## 3. UART Hardware Interface

| 항목 | 현 상태 | 결정/증거 필요 |
|---|---|---|
| VCU board/MCU/revision | TBD | board label, MCU part, schematic/BOM |
| UART peripheral/AF/TX/RX pins | TBD; current branch source/.ioc 없음 | VCU owner가 peripheral, clock, AF, pin ownership 확인 |
| PC link | USB-UART TTL 또는 native USB CDC 후보 | connector, PC driver, VCU USB hardware/firmware 지원 |
| Logic voltage | TBD | MCU IO와 adapter level을 문서로 대조. 확인 전 물리 연결 금지. TTL UART와 RS-232 구분 |
| GND/isolation/power | TBD | 기준 GND/절연, USB-UART VCC pin 사용 여부 및 역전원 방지 |
| Debug/bootloader/LIN 충돌 | TBD | UART 공유 여부, boot log 및 protocol stream 분리, peripheral owner |
| FreeRTOS RX/TX | 구현 미확인 | IRQ/DMA byte capture→bounded buffer/queue→parser task 후보; ISR에서 parsing/printf/blocking 금지 |
| 실제 hardware | NOT VERIFIED / NOT RUN | 보드/배선/전원/Flash 없음 또는 미확인 |

USB-UART TTL은 COM 연결 후보지만 실제 전압/TX-RX-GND/adapter 확인이 필요하다. Native USB CDC는 VCU 지원이 확인되지 않았다. Gateway Debug UART를 VCU PC link로 간주하거나 공유하지 않는다.

## 4. Serial 설정 후보 (모두 Proposal)

| 설정 | 후보와 tradeoff |
|---|---|
| Baudrate | 115200 또는 230400 bps. 호환성/처리량을 비교한다. Gateway log 115200은 적용 근거가 아니다. |
| Data/Parity/Stop | 8 data, no parity, 1 stop (8N1) 후보. 양단 설정 및 VCU HAL 확인 필요. |
| Flow control | none은 배선 단순; RTS/CTS는 backpressure 후보지만 pin/adapter/firmware 지원 필요. |
| RX buffer | 2 × maximum frame bytes or 4 × maximum frame bytes | 2-frame option uses less RAM; 4-frame option tolerates larger bursts. This is a relative sizing candidate, not a selected byte count. |
| TX buffer | one outstanding frame or a bounded queue of 2 or 4 frames | single-frame option applies backpressure sooner; queue option absorbs bursts but can retain stale commands. Queue depth and stale-entry policy TBD. |
| PC read wait | bounded cancellation-friendly wait 또는 event-driven read. GUI 종료용 poll은 protocol/safety timeout이 아님. |
| Packet deadline | inter-byte gap deadline or whole-frame deadline derived from baud, max packet length, and scheduler latency | Both are protocol parser candidates; choose and measure after length/baud decisions. Numerical value TBD. |
| Driver input timeout | VCU의 마지막 유효 입력 freshness. 값과 fail-safe는 VCU/Safety 결정. CAN 0x100 10/30 ms나 Gateway 50 ms를 상속하지 않는다. |

현재 max frame이 없으므로 buffer byte 수나 timeout 숫자를 넣지 않는다. 검토 산식 후보는 buffer capacity ≥ 2 × 최대 frame bytes이며, 실측/승인 후 정한다.

## 5. Application Frame

### 5.1 ASCII vs Binary

| 기준 | ASCII line | Binary framed |
|---|---|---|
| 수동 디버깅 | Terminal에서 읽기 쉬움 | decoder/hex view 필요 |
| 크기 | text/field name으로 커질 수 있음 | compact하게 구성 가능 |
| 경계 | newline 간단, escaping/긴 line 처리가 필요 | SOF+length 명시, 손상 후 resync 필요 |
| 검증 | grammar/locale/partial line | version/type/length/CRC/range |
| 제안 | bench bring-up에는 편리 | 장기 양방향 protocol 후보. 어느 쪽도 미승인 |

Binary 우선 검토 의견은 제안일 뿐이다.

### 5.2 Binary frame shape 후보

SOF | Version | Message Type | Payload Length | Payload | CRC

| 요소 | 검토 목적 | TBD |
|---|---|---|
| SOF | stream frame 시작 찾기 | 폭, pattern, escaping, resync |
| Version | schema 변경 식별 | 폭, initial version, compatibility |
| Message Type | Driver Input/VCU response 구분 | registry와 값. 0x600과 무관 |
| Payload Length | 경계 검증 | 폭, maximum packet |
| Payload | message data | field order/encoding |
| CRC | 손상 검출 | CRC-16/32 후보, polynomial/init/reflection/xor/coverage/test vectors |

Endianness는 little/big 중 승인한다. CAN DBC byte order를 자동 승계하지 않는다. Sequence/Alive/Heartbeat는 넣지 않았으며 필요성, 위치, width, wrap/reset/duplicate 규칙을 별도 승인한다.

### 5.3 Parser 오류 처리 후보

- UART read chunk가 frame 경계라고 가정하지 않고 partial 및 concatenated packet을 처리한다.
- bounded buffer와 승인 maximum을 적용하며 untrusted length로 무제한 할당하지 않는다.
- version/type/length/CRC/field validation 실패 시 전체 input snapshot을 적용하지 않는다.
- 오류 후 resync 후보는 한 byte씩 이동하여 SOF 재탐색 또는 delimiter까지 폐기다. owner 선택 필요.
- Overflow는 원인/count를 남기고 조용한 overwrite를 정상 수신으로 보지 않는다.
- 반복 setpoint와 event/edge를 구분한다. RUN 재수신 의미는 VCU 결정.
- Sequence가 없으면 response와 Apply를 자동 연관하지 않는다.
- Parser error를 ECU/CAN Fault로 변환하지 않는다. 자동 ACK/retry/recommand는 하지 않는다.

## 6. PC→VCU payload 후보

None은 미설정이며 OFF/0/Brake OFF/P와 다르다. Byte length와 wire encoding은 Frame Format 결정 뒤 승인해야 한다.

| Field | PC type / choices | Wire byte length 후보 | Encoding 후보 | Valid range | Invalid | Initial | Reset / Update |
|---|---|---|---|---|---|---|---|
| Ignition | str 또는 None; OFF/ON/RUN | TBD | enum code 또는 ASCII token; 수치 미정 | OFF/ON/RUN 중 명시 값 | invalid code/token 정책 TBD | None/unset, 자동 OFF 금지 | Reset은 local only. Apply snapshot 후보 |
| Accelerator | finite float 또는 None; Mock 0..100% | TBD | scaled integer 또는 decimal text; scale/precision TBD | finite 0..100% (현재 Mock 범위만 확인) | NaN/Infinity/range 밖 거부 후보; wire invalid TBD | None/unset | Reset local only; 양자화/rounding은 승인 필요 |
| Brake | bool 또는 None | TBD | enum code 또는 ASCII token | explicit False/True만 입력 | invalid code/token TBD; None은 미설정 | None/unset, 자동 OFF 금지 | Apply에서 명시값만 snapshot에 포함 후보 |
| Gear | str 또는 None; P/N/D/R | TBD | enum code 또는 ASCII token; numeric mapping 미정 | 명시 P/N/D/R | invalid code/token TBD; None은 미설정 | None/unset, P 자동 지정 금지 | Reset local only; update rule 승인 필요 |
| Window / Light | str 또는 None; 현 UI/Mock | 적용 제외 후보 | 정의하지 않음 | 이번 driving payload 범위 아님 | 해당 없음 | Mock model 현행 유지 | 별도 Body/Gateway route 승인 전 UART에 포함하지 않음 |

| Update 방식 후보 | 설명 | 영향 |
|---|---|---|
| Full snapshot (우선 검토) | Apply 전에 네 driving field를 명시하고 immutable snapshot 전송 | atomicity가 단순해질 수 있으나 현재 Mock partial-input 동작과 달라 migration 승인 필요 |
| Validity mask | partial field와 valid bit 동봉 | mask, stale field, invalid 조합 정책 추가 |
| Per-field/TLV | 설정 field만 전송 | parser 복잡도와 과거 값 결합/freshness 정책 증가 |

현재 model의 initial 상태는 None이며 자동 packet 없음이 후보 정책이다. Reset은 UI/model만 초기화하고 OFF/0/P 또는 safe command를 보내지 않는다. Apply는 확정 snapshot을 보내는 후보이며 편집 중 draft는 보내지 않는다. VCU boot 시 input-valid와 실제 control state는 VCU owner 결정이다. 이 정책들은 승인 전 계약이 아니다.
## 7. VCU→PC response 후보

| 방식 | 내용/영향 |
|---|---|
| A. 응답 없음 | CAN observation은 가능하나 UART request 수신/검증 증거가 없고 양방향 결정과 다를 수 있어 별도 exception 승인 필요 |
| B. 최소 처리 결과 (우선 검토) | CommandReceived, CommandAccepted/Rejected, RejectReason 후보. Accepted가 validation인지 적용인지 정의 필요 |
| C. 결과+상태 | B와 AppliedIgnition/VCUOperatingState 후보. CAN 0x120/0x300/0x310 중복과 authority/freshness 충돌 검토 |

후보 field 이름은 CommandReceived, CommandAccepted, RejectReason, AppliedIgnition, VCUOperatingState, RequestSequence다. 모두 Proposal이며 enum/field/value는 미정. RequestSequence 필요성부터 승인한다. PC는 response 뒤 자동 ACK, retry, re-command, stale input replay를 하지 않는다. Port write completion은 VCU 수신이 아니고 Accepted는 Applied가 아니다.

## 8. PC TX 정책 비교

| 방식 | tradeoff |
|---|---|
| Apply 시 1회 | 명확하고 전송량 낮음. VCU hold/expiry/freshness 필요 |
| 주기 반복 | freshness에 유리할 수 있음. stale snapshot, duplicate, RTOS load를 검증 |
| 변경+주기 유지 | 반응성/freshness 후보. 두 경로 중복 및 순서 관리 필요 |

cadence, jitter, retry, heartbeat, input timeout은 TBD. 기존 CAN 주기/timeout이나 GUI refresh를 전용하지 않는다. VCU/Safety 승인 전 Live UART TX는 BLOCKED다.

## 9. VCU RX/TX 처리 계약 후보

1. ISR/DMA는 byte capture/bounded buffer 전달만 하고 blocking parse/printf/control 판단을 하지 않는다.
2. Parser task에서 SOF/version/type/length/max/CRC/payload/range 검증.
3. packet 전체 검증 전 기존 input 일부도 갱신하지 않는다.
4. Valid snapshot만 승인된 queue/mailbox/critical section으로 control task에 원자 전달.
5. Received/Accepted/Applied 의미 및 증거 owner를 분리.
6. malformed/version/CRC/range/duplicate/overflow/stale 처리를 분리.
7. disconnect/boot/reset/reconnect/freshness/fail-safe/recovery는 VCU Safety 담당자가 결정.
8. response TX는 bounded queue/task에서 처리하고 ISR/control task blocking 금지.
9. UART input과 기존 CAN VCU_Command(0x100)/Motor coordination을 혼합하지 않는다. PC는 0x100을 송신하지 않는다.
10. Debug text와 protocol bytes를 같은 stream에 임의 혼합하지 않는다.

Timeout, interlock, safe state, torque policy, Fault code는 확정하지 않는다.

## 10. CAN Monitor와 상태 표시

기존 DBC 관측 경로를 유지한다.

| ID | 조사된 DBC message/sender | PC 의미 |
|---|---|---|
| 0x100 | VCU_Command / VCU | CAN output observation. UART ACK가 아님 |
| 0x110 | Motor_Status / MOTOR | Motor CAN observation |
| 0x120 | Vehicle_Status / GATEWAY | 기존 vehicle status |
| 0x200 | Body_Status / GATEWAY | LIN 유래 Body status |
| 0x300 | Gateway_Status / GATEWAY | Gateway observation |
| 0x310 | Fault_Status / GATEWAY | CAN fault/state; UART reject와 별도 |

| 상태 후보 | 의미 |
|---|---|
| UART TX Requested | UI 송신 요청 |
| UART Port Write Completed | OS/adapter write 완료 반환; VCU RX 증거 아님 |
| UART Response Received | parser 검증된 응답 |
| UART Command Accepted | 승인된 response meaning일 때만 |
| CAN Message Observed | CANable Pro 수신 |
| ECU Applied | 별도 증거 전까지 NOT VERIFIED |
| Fault Observed | UART transport/parser와 CAN 0x310 source 분리 |

CAN 0x100은 UART command ACK가 아니다. CAN/UART observation이 다르면 자동으로 덮어쓰지 않는다.

## 11. UI/UX 영향과 승인 gate

이번 단계는 GUI를 수정하지 않는다. 기존 Driver Control 0x600 안내는 신규 구조와 충돌한다. 확인한 GUI Source에서는 정확한 문구 CAN TX Not sent는 발견되지 않았다. 후속 UI task에서 승인된 spec에 맞춰 UART Interface Pending/Not Connected로 갱신한다. 지금 UART Connected/Write Success/Accepted를 표시하면 안 된다.

- Driver Input Source(Mock/UART)와 CAN Monitor Source(CANable)를 분리.
- Mock Accepted를 UART Accepted로 재해석하지 않음.
- Live TX Blocked의 transport를 명확히 표시.
- Requested/Port Write/Response/Accepted/Applied를 분리.
- ECU Applied NOT VERIFIED 유지.
- Window/Light는 Mock 유지; 승인 route 전 UART payload에서 제외.
- Raw/Decode/Cache/Logging/Graph/Fault CAN Monitor를 유지.

[CONTRIBUTING §5](../../../CONTRIBUTING.md) 및 핸드북 §§4.2/5.5 절차: decision/Jira → UART controlled spec 및 owner 지정 → VCU/PC/Hardware/CAN 상대 review → 상세 승인 → Python/VCU 구현 승인 → tests → Hardware loopback/ECU integration evidence → 기존 CAN regression → PR/Jira 후속처리.

실제 UART TX 전 board/MCU/port/pins/level/connector/GND/isolation, Debug/LIN 충돌, serial settings/buffers/frame max, frame/payload/CRC vectors, None/initial/reset, response/correlation/retry, timeout/fail-safe/recovery, 동일 protocol revision 및 승인 evidence가 필요하다.

**현재: UART TX BLOCKED / Hardware NOT VERIFIED.**
