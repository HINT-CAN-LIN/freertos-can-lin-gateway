# HINT-48 Phase 3N-3 — PC ↔ VCU UART Review Checklist

- 작성일: 2026-10-17
- 상태: **NEEDS_REVIEW / 24개 세부 결정 Pending / UART TX BLOCKED**
- 관련: [Interface Proposal](pc_vcu_uart_interface_proposal.md), [Implementation Tasks](pc_vcu_uart_implementation_tasks.md)

## 1. 기록 정책

Phase 지시에서 전달된 PC↔VCU 직접 양방향 UART 구조를 반영한다. 이는 packet, payload, timing, hardware, Firmware 또는 Live TX 승인이 아니다. 별도 승인 증거가 없어 모든 세부 결정은 Pending이다. 상태는 Reviewed / Approved / Rejected / Needs Change / Pending 중 하나로 기록한다. Reviewed는 Approved가 아니다. Jira는 미등록이다.

| ID | Priority | Primary Owner | Reviewers | 결정 질문 | 근거 / 완료 조건 | Status |
|---|---|---|---|---|---|---|
| N3-R01 | P0 | VCU | Hardware, PC | VCU board/MCU/revision은? | HARDWARE_SETUP; schematic/BOM 확인 | Pending |
| N3-R02 | P0 | VCU | Hardware, PC | 사용할 UART/USART, clock, AF, TX/RX pin은? | 현재 PC branch에 VCU source/.ioc 없음; owner 승인 | Pending |
| N3-R03 | P0 | Hardware | VCU, PC | USB-UART TTL 또는 native USB CDC? connector/pinout은? | board 지원 및 wiring diagram | Pending |
| N3-R04 | P0 | Hardware | VCU | logic voltage, GND/isolation, adapter VCC 정책은? | 실제 전기 사양 호환 증거 | Pending |
| N3-R05 | P0 | VCU | Hardware, System | Debug/bootloader/programming/LIN UART 충돌/공유는? | port owner 및 log/protocol 분리 승인 | Pending |
| N3-R06 | P1 | VCU | PC, Hardware | baud 후보 115200/230400, 8N1, flow none/RTS-CTS 중 선택은? | Gateway log값 미상속; 양단 및 bench 기준 | Pending |
| N3-R07 | P1 | VCU | PC | bounded buffer, max frame, overflow/backpressure는? | rate/latency/frame 기반 산정 | Pending |
| N3-R08 | P0 | PC | VCU | ASCII line 또는 Binary frame? | debug/size/parser/compatibility tradeoff | Pending |
| N3-R09 | P0 | PC | VCU | SOF/version/type/length/endianness/escaping/width? | versioned layout과 golden vector | Pending |
| N3-R10 | P0 | PC | VCU | Checksum/CRC algorithm, parameters, coverage? | 양단 golden test vectors | Pending |
| N3-R11 | P0 | PC | VCU | max length, partial deadline, resync, overflow recovery? | bounded parser와 negative test 계약 | Pending |
| N3-R12 | P0 | VCU | PC, Safety | Full snapshot, validity mask, per-field/TLV? | None/stale/atomicity 승인 | Pending |
| N3-R13 | P0 | VCU | PC | Ignition, Accelerator scale/precision, Brake, Gear encoding/invalid? | 모든 enum/range/boundary vectors 승인 | Pending |
| N3-R14 | P0 | PC | VCU, Safety | None/initial/reset 의미? OFF/0/P 자동 대체 금지 여부? | driver_input.py; unset/explicit 구분 | Pending |
| N3-R15 | P0 | VCU | PC, System | no response/minimal result/state response? A안과 양방향 결정 관계? | response schema 또는 architecture exception 승인 | Pending |
| N3-R16 | P0 | VCU | PC, Safety | Received/Accepted/Rejected/Applied 각각의 의미와 evidence? | authority/source/freshness 기준 | Pending |
| N3-R17 | P1 | PC | VCU | request-response sequence/correlation 필요? | wrap/restart/duplicate 또는 미지원 결정 | Pending |
| N3-R18 | P0 | VCU | PC, Safety | Apply once/periodic/change+periodic 및 duplicate/RUN 의미? | cadence/idempotency/freshness review | Pending |
| N3-R19 | P0 | VCU | Safety, PC | disconnect/stale/malformed/boot/reconnect fail-safe/timeout/recovery? | VCU safety owner와 시험 기준 승인 | Pending |
| N3-R20 | P1 | VCU | PC | ISR/DMA→bounded buffer→parser task→atomic handoff? | task/queue/atomicity/overflow review | Pending |
| N3-R21 | P1 | VCU | PC | response TX와 CAN/control task의 resource/blocking 충돌? | priority, queue bound, failure path 검토 | Pending |
| N3-R22 | P1 | PC | VCU, CAN/Gateway | Window/Light는 Mock 유지·payload 제외? 별도 route owner는? | Body path 별도 결정, no accidental forward | Pending |
| N3-R23 | P1 | PC | VCU, CAN/Gateway | CANable Monitor와 UART source, 0x100/0x310 해석 분리? | ACK/Fault 오인 방지와 timestamp/source | Pending |
| N3-R24 | P0 | System/Interface | VCU, PC, Hardware, CAN | 기존 0x600 문서/UI controlled supersession과 TX gate는? | evidence, baseline, owner approvals 기록 | Pending |

## 2. 담당자 기록

| Issue ID | Status (하나 선택) | Decision | Owner role/name | Reviewers | Date | Jira | 변경 산출물 | 승인 증거 | 후속 작업 |
|---|---|---|---|---|---|---|---|---|---|
| N3-R__ | Pending | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

개인 이름은 실제 확인 후 기입한다. Reviewed/Approved/Code Merge/Hardware Validation/Jira Done은 각각 별도 상태다.

## 3. 승인 전 차단 항목

- Port/pin/voltage/connector/실물 wiring
- Protocol/payload/CRC/response/freshness/fail-safe 승인
- PC Serial 코드 및 VCU Firmware 구현
- 실제 UART TX, Accepted 또는 Applied 주장
- CAN DBC/Matrix/Routing/LDF/Firmware 변경
- 기존 0x600 이력의 공식 supersession
- Hardware loopback 및 ECU integration evidence

## 4. 최종 승인 Gate

### Interface 결정
- [ ] 결정자/date/Jira 또는 회의 evidence 기록
- [ ] 0x600 제안 대체 상태 승인 및 과거 문서 추적성 유지
- [ ] UART source-of-truth, revision, owner 지정
- [ ] N3-R01–R24 결정 또는 명시된 reject/scope-out evidence
- [ ] TBD를 default로 추정하지 않음

### Hardware/Safety
- [ ] board/MCU/UART/pin/connector/level/GND/isolation 검증
- [ ] Debug/bootloader/LIN conflict 해소
- [ ] ISR/DMA/buffer/parser/atomic handoff 검토
- [ ] disconnect/stale/timeout/fail-safe/interlock/recovery VCU Safety 승인
- [ ] 실제 loopback plan 승인

### Protocol/PC
- [ ] frame/version/type/length/max/CRC/error vectors 승인
- [ ] payload/None/initial/reset/scale/enum/update 승인
- [ ] response와 Accepted/Applied/Reject 의미 승인
- [ ] cadence/retry/duplicate/correlation/timeout 승인
- [ ] PC auto-ACK/auto-recommand/stale replay 없음
- [ ] Mock, UART response, CAN observation 분리

### Implementation
- [ ] PC/VCU가 같은 승인 protocol revision 사용
- [ ] malformed/partial/overflow/disconnect/duplicate tests 통과
- [ ] 실제 loopback 및 ECU integration evidence 기록
- [ ] Live UART TX 별도 gate 통과
- [ ] PR/Merge/Jira state는 팀 절차로 별도 처리

## 5. Interface 변경 절차

UART 세부값은 미승인이다. CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**이며 CONTRIBUTING §5, 핸드북 §§4.2/5.5 절차를 따른다.
