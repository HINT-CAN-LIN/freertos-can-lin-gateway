# HINT-48 Phase 3N-3 — PC ↔ VCU UART Implementation Task Draft

- 작성일: 2026-10-17
- 상태: **Jira 미등록 / 구현 미시작 / 실제 UART TX BLOCKED**
- 기준: [Interface Proposal](pc_vcu_uart_interface_proposal.md), [Review Checklist](pc_vcu_uart_review_checklist.md)

아래는 승인 후 등록할 수 있는 1–3일 Jira task 초안이다. 등록, 담당자 배정, Interface 승인 또는 구현 권한을 의미하지 않는다.

| Task | 크기 | Owner 역할 | 선행 | 범위 / 완료 조건 |
|---|---:|---|---|---|
| N3-T01 | 1일 | System/Interface | 구조 결정 | PC↔VCU UART 결정, 0x600 대체 이력, protocol source/revision owner 기록; 결정자/date/Jira evidence |
| N3-T02 | 1–2일 | VCU + Hardware | board 자료 | board/MCU/revision, UART/AF/pins, connector/level/GND/isolation, Debug/bootloader/LIN 충돌; schematic 기반 wiring 승인 |
| N3-T03 | 1일 | Hardware + PC + VCU | T02 | USB-UART TTL vs native USB CDC 및 driver/COM 선정; 전기 호환과 VCC 정책 확인 |
| N3-T04 | 1일 | VCU + PC | T02 | baud/framing/flow/read wait/buffer sizing 결정; 양단 설정과 bench plan, Gateway log 값 미상속 |
| N3-T05 | 2–3일 | PC + VCU | T01/T04 | ASCII/Binary, SOF/version/type/length/max/endian/CRC/resync/duplicate 결정; spec/golden/malformed vectors 승인 |
| N3-T06 | 1–2일 | VCU + PC + Safety | T05 | Input fields, enum/scale/None/initial/reset/full-or-partial/invalid 결정; boundary/atomicity vectors 승인, Window/Light 범위 분리 |
| N3-T07 | 1–2일 | VCU + PC | T05 | response, Received/Accepted/Rejected/Applied, RejectReason, correlation 결정; schema와 no-auto-ACK 승인 |
| N3-T08 | 2–3일 | VCU + Safety | T06/T07 | cadence/retry/duplicate/disconnect/stale timeout/fail-safe/recovery 결정; Safety approval/evidence |
| N3-T09 | 1일 | CAN/Gateway + System | T01 | CAN observation 경계 및 old 0x600 docs/UI 이력 관리; CAN/DBC/Route 불변 확인 |
| N3-T10 | 2일 | PC | T05–T07 approved | Python transport-independent packet model/codec/bounded parser/CRC; partial/concat/resync/length/range tests |
| N3-T11 | 2일 | PC | T02/T04/T10 | Serial Adapter/COM/bounded read-write/cancel/disconnect/close; Mock Serial lifecycle/resource cleanup tests |
| N3-T12 | 1–2일 | PC | T07/T11 | PySide6 UART Connection/Driver UI; CANable source 분리 및 write/response/accepted/applied status tests |
| N3-T13 | 2–3일 | VCU | T02/T04–T08 approved | RX ISR/DMA, bounded buffer, parser task, validation, atomic handoff; malformed/partial/overflow/stale tests |
| N3-T14 | 1–2일 | VCU | T07/T13 | response TX queue/task/error path; bounded resources, no blocking in ISR/control task |
| N3-T15 | 2일 | PC + VCU | T10–T14 | Mock Serial/cross-language vectors/error injection; noise/CRC/version/duplicate/disconnect/correlation tests |
| N3-T16 | 1–2일 | Hardware + PC + VCU | T02–T15, bench approval | physical UART loopback direction/voltage/baud/reconnect; setup and measured evidence |
| N3-T17 | 2–3일 | VCU + PC + CAN/Gateway | T16, build/flash identified | UART input/response plus independent CANable observation; source/timestamp/safety outcome evidence |
| N3-T18 | 1일 | PC + QA/Integration | T17 | Raw/Decode/Cache/Vehicle/ECU/Fault/Graph/Logging/Automation/CLI regression; logs and hardware status separated |

## 1. 순서

1. T01–T09 Interface/Hardware/Safety 결정 및 승인
2. T10 Python protocol/codec, T13 VCU RX
3. T11 PC Serial Adapter, T14 VCU response TX
4. T12 PC GUI
5. T15 Mock/cross-language tests
6. T16 Hardware loopback
7. T17 PC↔VCU 통합 및 CAN 관측
8. T18 GUI/CLI 회귀

## 2. 후속 구현 DoD

- PC와 VCU가 동일 승인 protocol revision 및 test vectors를 사용한다.
- 0x600을 UART Message Type으로 재사용하지 않는다.
- CAN DBC/Matrix/Routing/LDF/기존 CAN contract는 별도 승인 없이 변경하지 않는다.
- CANable Monitor/CLI를 유지하고 UART와 CAN Source를 구분한다.
- Requested, Port Write, Response, Accepted, Applied, CAN Observed를 분리한다.
- None과 OFF/0/P를 구분하며 Mock Accepted를 ECU Accepted로 표시하지 않는다.
- partial/overflow/malformed/duplicate/timeout/disconnect/reconnect/cancel을 검증한다.
- GUI close 시 Serial resource와 worker를 정리한다.
- 미실행 Hardware 검증은 NOT VERIFIED로 보고한다.
- CAN/LIN 변경은 상대 담당자 review 및 CONTRIBUTING §5/핸드북 §§4.2/5.5 절차를 통과한다.

## 3. Jira 등록용 초안 (미등록)

- Summary: [HINT-48] Define and review direct PC-VCU UART driver input interface
- Description: Agree on VCU UART hardware/electrical connection, framing, Driver Input payload, VCU response, freshness/fail-safe and approval evidence before Python/Firmware implementation. Preserve CANable observation and existing CAN/LIN contracts.
- Components: PC Diagnostic Tool, VCU Firmware, Hardware, CAN/Gateway Interface
- Acceptance: N3-R01–R24 decisions/evidence recorded; UART protocol revision approved; unresolved items resolved or formally scoped out; draft alone does not enable implementation or Live TX.
- Status: 초안 / Jira 미등록
- Assignee/reviewer/date/priority: 실제 담당자 및 팀 기준 확인 후 입력

이 작업은 Jira에 등록되지 않았고 담당자를 지정하지 않았다.
