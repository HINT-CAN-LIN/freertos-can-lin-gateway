> Updated 2026-10-02: see [CLUSTER_RX_COMPLETION.md](CLUSTER_RX_COMPLETION.md) for completed RX decoder, CAN queue/filter integration and mode switching. Earlier CAN-not-implemented statements below describe the previous version.

# Cluster ECU 규약 반영

검토 기준: develop commit `d131a136c3c84ddd47ebf4863ed4e3f806d401f7`.
원본: [requirements](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/tree/d131a136c3c84ddd47ebf4863ed4e3f806d401f7/docs/requirements), [architecture](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/tree/d131a136c3c84ddd47ebf4863ed4e3f806d401f7/docs/architecture/system), [CAN DBC](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/tree/d131a136c3c84ddd47ebf4863ed4e3f806d401f7/network/can).

## 구현 범위와 책임

SYS_REQ_007 / SYS_REQ_049 및 SF_06에 따라 ST7796S에 Vehicle, Motor, Body, Fault, Health를 표시합니다. SYS_REQ_025/026/050/051/052/058과 Message Definition POL-006/008을 기준으로 Fault 이벤트를 보관합니다. Gateway의 Fault 감지/복구 정책, Motor의 안전 출력, Window Local Command Timeout은 Cluster가 실행하지 않습니다. 터치 입력은 이 표시 기능에 필요하지 않습니다.

| ID | 메시지 / 송신 방식 | 반영 내용 |
|---|---|---|
| 0x110 | Motor_Status / 10 ms cyclic | MotorState, Alive 연속성 진단, RPM/Torque 원시 값 디코딩 |
| 0x120 | Vehicle_Status / 20 ms cyclic | Speed 0.1 km/h, RPM, Gear P/N/D/R, Brake, NetworkState |
| 0x200 | Body_Status / 100 ms cyclic | Door 닫힘/열림·잠금, Light 6개 비트, Window 0~5 상태 |
| 0x300 | Gateway_Status / 100 ms cyclic | QueueUsage 0~100%, GatewayAlive 0~15 및 wrap |
| 0x310 | Fault_Status / event | FaultCode + source node 별 ACTIVE/CLEARED 표, SystemState |

표준 11-bit data frame, DLC=8, Intel little endian을 사용합니다. 다른 ID는 무시하고, 대상 ID의 잘못된 DLC/extended/RTR은 거부하며 수신 시간을 갱신하지 않습니다. CAN 실제 수신은 아직 연결하지 않았습니다. VCU_Command 0x100은 제어 입력이므로 현재 Cluster 표시 경로는 Gateway의 0x120을 사용합니다.

## Fault 및 유효성

- Fault 코드: 1 VCU_TIMEOUT, 2 DOOR_ECU_OFFLINE, 3 ALIVE_ERROR, 4 ECU_OFFLINE, 5 QUEUE_DROP, 6 WINDOW_ECU_OFFLINE.
- 노드: 0 NONE, 1 VCU, 2 MOTOR, 3 GATEWAY, 4 CLUSTER, 5 DOOR, 6 LIGHT, 7 WINDOW.
- RecoveryState: **0 ACTIVE, 1 CLEARED**. 한 프레임은 한 Fault 전이입니다. 같은 코드라도 노드가 다르면 별개로 보관합니다. 중복 이벤트는 결과가 변하지 않습니다.
- Fault_Status에는 주기 timeout을 적용하지 않습니다. 특정 Fault의 CLEARED만 그 항목을 해제합니다. NONE을 전체 초기화 명령으로 해석하지 않습니다.
- 부팅 이전 이벤트나 유실 이벤트를 복구하는 snapshot/retry 규칙은 아직 정의가 부족합니다. `NO OBSERVED FAULT`는 전체 시스템에 Fault가 없다는 보장이 아닙니다. Gateway 수신 gap/잘못된 Fault 이벤트 후에는 표가 불완전할 수 있다고 표시하고, 기존 ACTIVE는 유지합니다. 유실 후 재동기화는 다음 통합 작업에서 Gateway와 합의해야 합니다.
- 대표 SystemState는 Gateway가 보내는 값입니다. 이벤트의 SystemState를 우선 반영하고 다음 Vehicle_Status의 NetworkState로 갱신합니다. Fault 표로 대표 상태를 임의 계산하지 않습니다.
- 주요 Fault 화면 선택 순서는 표시용 로컬 정책입니다: VCU_TIMEOUT → ALIVE_ERROR → ECU_OFFLINE → DOOR_OFFLINE → WINDOW_OFFLINE → QUEUE_DROP. 전체 ACTIVE 개수를 함께 표시합니다. Critical/Noncritical 판정 로직을 대체하지 않습니다.
- Speed raw 0xFFFF/2500 초과, RPM raw 0xFFFF/12000 초과는 `--`; Gear 4~6 RESERVED, 7 INVALID; Door/Light/Window invalid는 INVALID로 표시합니다. Light 여러 비트는 함께 표시합니다. H=headlamp, L/R=turn, HZ=hazard, REV=reverse, BRK=brake.
- DoorOpen과 DoorStatus, ReverseLamp와 LightStatus bit4가 불일치하면 MISMATCH를 표시합니다.

## 아직 확정하면 안 되는 항목

시스템 문서는 Cluster의 stale/offline 표시를 요구하지만 화면 판정 시간의 정량값은 고정하지 않습니다. `CLUSTER_STALE_MS=1000`, `CLUSTER_OFFLINE_MS=3000`은 **임시 로컬 표시 정책**입니다. 각 cyclic 메시지 수신 시간을 독립적으로 검사합니다. Gateway VCU timeout 30 ms, Door 3 cycles, Window 2 cycles와 혼동하지 마세요. 실차/통합 완료 전 메시지별 표시 threshold를 팀에서 합의해야 합니다.

Excel Signal Definition 일부 행의 Brake invalid=1, Alive invalid=0xF, Gear 최대 5 표기는 Value_Table 및 DBC와 충돌합니다. 구현은 BOOL=0/1 모두 유효, Alive=0~15 모두 유효 및 15→0 wrap, Gear 정상=0~3 / 4~6 reserved / 7 invalid를 사용합니다. 이 충돌과 DBC의 review-ready 표시는 상대 담당자 검토 대상으로 남깁니다. 통신 문서 원본을 임의 수정하지 않았습니다.

## 현재 테스트 모드

`CLUSTER_TEST_INPUT=1`: 24초 반복으로 정상 → 주행/램프/창문 → Door OFFLINE → VCU_TIMEOUT+Door 동시 ACTIVE → VCU만 CLEARED → Door CLEARED → 수신 중단 → 재수신을 재현합니다. UI 값을 직접 바꾸지 않고 동일한 `cluster_receive_frame()`에 raw CAN payload를 넣습니다.

테스트 프레임 생성은 UI Task의 약 100 ms 간격입니다. 위 표의 실제 버스 송신 주기 검증이나 E2E CAN 증거를 대신하지 않습니다. SPI blocking 출력은 유지하며, UI의 모든 LVGL 호출은 한 Task에서 수행합니다.

다음 통합은 CAN RX ISR → FreeRTOS queue → Task에서 decoder → UI snapshot 순서입니다. ISR에서 LVGL을 호출하지 마세요. TEST_INPUT를 끄는 것만으로 실제 CAN 수신이 연결되지는 않습니다. CANable 연결 후 필터/시작/notification/queue 경로를 구현하고 이 문서의 payload를 주기 송신해 검증해야 합니다.

## CANable 수동 검증 payload

모두 DLC8, standard data frame, hex byte 순서입니다. Fault 이벤트는 한 번 전송해도 보관되어야 합니다.

| ID | Payload | 기대 결과 |
|---|---|---|
| 120 | 7B 00 D2 04 2A 00 00 00 | 12.3 km/h,1234 rpm,D,brake ON,System OFFLINE |
| 200 | 03 03 30 04 00 00 00 00 | OPEN/LOCK, reverse+brake lamps, Window LOWER LIMIT |
| 200 | 00 FF FF FF 00 00 00 00 | Door/Light/Window INVALID |
| 200 | 00 03 10 00 00 00 00 00 | Door/Reverse duplicate signals MISMATCH |
| 310 | 01 61 00 00 00 00 00 00 | VCU_TIMEOUT ACTIVE,source VCU,System FAIL_SAFE |
| 310 | 02 65 00 00 00 00 00 00 | Door OFFLINE ACTIVE,active count2 |
| 310 | 01 51 00 00 00 00 00 00 | VCU CLEARED,Door는 ACTIVE 유지,count1,System OFFLINE |
| 310 | 02 15 00 00 00 00 00 00 | Door CLEARED,count0,System NORMAL |
| 310 | FF 0F 00 00 00 00 00 00 | Invalid event 거부,active table 유지,uncertain 표시 |

Gateway_Status는 payload 첫 byte alive를 0..15 순환시키고 두 번째 byte에 QueueUsage를 넣습니다. Motor_Status는 byte4 bits2..5에 Alive, bits0..1에 MotorState를 넣습니다. 각 cyclic ID를 별도로 중단해 RX V/B/M/G가 독립적으로 바뀌는지 확인하세요.

## 수행한 검증

2026-10-02: 최종 Debug 빌드 오류 0 / 경고 0. 연결된 NUCLEO-F446RE에 ELF 다운로드, Flash verify 및 reset 완료. 약 29초 동안 41회 RAM 상태를 읽어 시작 시 모델 self-test PASS, uptime 34→63초, ACTIVE 개수 0/1/2, RX 정상/stale/offline을 확인했습니다. SPI 상태 HAL_OK, stack overflow hook 미발생, Task 스택 최소 여유 3,672 bytes였습니다.

검증 한계: LCD 글자의 배치/가독성은 사용자 실물 확인이 필요합니다. 실제 CAN 배선·수신·송신 주기 및 Gateway와의 Fault E2E 전파는 CANable/상대 ECU 연결 후 검증해야 합니다. 테스트 모드 결과로 시스템 전체 요구사항 완료를 선언하지 않습니다.
