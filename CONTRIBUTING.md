# Repository Contribution and Upload Guide

FreeRTOS CAN-LIN Gateway 프로젝트의 Repository 폴더, 파일 업로드, Interface 변경, Git 협업 규칙을 정의합니다.

본 문서는 현재 Repository 구조를 기준으로 작성합니다. 폴더 구조를 변경하는 경우에는 먼저 Jira Task를 생성하고, 변경 목적과 영향 범위를 PR에 기록합니다.

## 1. 프로젝트 기본 기준

- CAN Network: 500 kbps
- LIN Network: 19.2 kbps
- CAN Node: VCU, Motor, Gateway, Cluster
- LIN Node: Gateway Master, Door/Light/Window Slave
- Gateway: FreeRTOS 기반 CAN-LIN Routing, LIN Schedule, Health/Fault 관리
- Motor: Virtual Motor 기본안
- PC Tool: CANable, python-can, cantools, pytest 기반
- Window ECU: 최신 시스템 아키텍처 기준 In-Scope LIN Slave

MVP 경로와 Window 상세 Interface는 구분하여 관리합니다. Window PID, Signal, Schedule, Fault 기준은 확정 전까지 TBD/OPEN으로 표시하며 임의로 구현하지 않습니다.

## 2. Repository 폴더 기준

현재 Scaffold 기준의 주요 경로는 다음과 같습니다.

```text
firmware/
├─ cluster_ECU/
├─ common_ECU/
├─ door_ECU/
├─ gateway_ECU/
├─ light_ECU/
├─ motor_ECU/
├─ vcu_ECU/
└─ window_ECU/

network/
├─ can/
├─ lin/
└─ routing/

tools/
├─ dbc_validation/
├─ diagnostic_GUI/
├─ fault_injection/
├─ lin_validation/
└─ scripts/

tests/
├─ can/
├─ fault/
├─ fixtures/
├─ gateway/
├─ integration/
└─ lin/

integration/
├─ configs/
├─ evidence/
└─ scenarios/

docs/
├─ architecture/
├─ decisions/
├─ design/
├─ guides/
├─ hardware/
├─ requirements/
└─ test/
```

### 폴더별 업로드 기준

| 경로 | 업로드 대상 |
|---|---|
| `firmware/*` | ECU별 Firmware, CubeMX/CubeIDE 설정, 공통 Header 및 Source |
| `network/can` | CAN Matrix, `vehicle.dbc`, CAN Interface 검증 자료 |
| `network/lin` | LIN Matrix, LIN Schedule, LDF 및 LIN 검증 자료 |
| `network/routing` | Routing 규칙 또는 Routing Interface 정의 자료 |
| `tools/dbc_validation` | DBC Parse, Encode/Decode, Matrix 비교 도구 |
| `tools/diagnostic_GUI` | PC Diagnostic Tool 화면 및 실행 코드 |
| `tools/fault_injection` | CAN/LIN Fault Injection 코드와 설정 |
| `tests` | Unit, Interface, Fault, Gateway, Integration Test |
| `integration/configs` | 테스트 환경 및 Bus 설정 |
| `integration/scenarios` | MVP, 정상, Fault, Recovery 시나리오 |
| `integration/evidence` | Capture, Log, Test 결과, 측정 증적 |
| `docs` | 요구사항, Architecture, Design, Hardware, Test, Decision 문서 |

## 3. 파일 업로드 규칙

### 업로드 대상

- 실제 Firmware Source, Header, 설정 파일
- `CAN_Matrix.xlsx`, `LIN_Matrix.xlsx`, `LIN_Schedule.xlsx`
- Interface Freeze 후 승인된 `vehicle.dbc`, `vehicle.ldf`
- Python Tool, pytest Test, Fixture, 설정 파일
- Architecture, Requirements, Test Plan, Test Result 문서
- 재현에 필요한 Capture, Log, 사진 및 측정 결과

### 업로드 금지 또는 Git 제외 대상

- `*.exe`, `*.elf`, `*.bin`, `*.hex`, `*.map` 등 생성된 Build 결과물
- 개인 PC 경로가 포함된 설정 파일
- 개인 이름만으로 만든 임시 Header 또는 실험 파일
- IDE 임시 파일, Cache, 자동 생성 Backup 파일
- 검증되지 않은 Matrix, DBC, LDF를 최종본으로 표시한 파일
- 실제 측정하지 않은 KPI 숫자 또는 임의로 작성한 PASS 결과

빈 폴더는 Git이 추적하지 않으므로 구조 보존이 필요할 때만 해당 폴더에 빈 `.gitkeep` 파일을 추가합니다. 실제 Source나 문서가 추가되면 `.gitkeep`은 제거합니다.

## 4. 파일명 규칙

- 폴더명은 영문 소문자와 `_`를 기본으로 사용합니다.
- 동일한 산출물에 버전, 날짜, 담당자 이름을 반복해서 붙이지 않습니다.
- Interface 기준 파일은 다음 이름을 우선 사용합니다.

```text
network/can/CAN_Matrix.xlsx
network/can/vehicle.dbc
network/lin/LIN_Matrix.xlsx
network/lin/LIN_Schedule.xlsx
network/lin/vehicle.ldf
```

- 검토 중인 파일은 파일명에 `candidate` 또는 `review`를 표시하고, 승인 전에는 `final`로 표시하지 않습니다.
- 문서 파일은 내용의 소유 영역에 맞는 `docs` 하위 폴더에 배치합니다.
- 실제 구현 파일인 `routing_table.c/.h`는 Gateway Firmware 소유 영역에 배치합니다.

## 5. CAN/LIN Interface 변경 규칙

CAN/LIN Interface 변경에는 상대 담당자 리뷰 필요합니다.

다음 순서를 반드시 유지합니다.

```text
Jira Issue 생성
→ Matrix 또는 Schedule 수정
→ 상대 담당자 리뷰
→ CANdb++/DBC 또는 LDF 수정
→ Firmware/PC Tool/Test 반영
→ PR Review
→ HW 또는 자동화 Test Evidence
→ Jira Done
```

변경 시 PR에 다음 항목을 기록합니다.

- 변경 사유
- 기존 값과 변경 값
- 영향받는 ECU, Tool, Test
- 관련 CAN ID/DLC/Signal 또는 LIN PID/Frame/Schedule
- 상대 담당자 및 리뷰 결과
- Encode/Decode 또는 Bus Capture 결과
- Migration 및 Known Limitation

Matrix와 DBC/LDF의 의미가 서로 다르면 DBC/LDF만 수정하지 않습니다. Interface 기준을 먼저 정하고 관련 산출물을 함께 갱신합니다.

## 6. Branch 규칙

핸드북 15.7 기준을 적용합니다.

```text
main       Release 전용. 직접 Push 금지
develop    팀 통합 Branch
feature/*  새 기능
fix/*      Bug 수정
test/*     Test, Fixture, 측정, Evidence 보강
```

Branch 이름에는 Jira Key를 포함합니다.

```text
feature/GW-23-reverse-lamp-routing
fix/GW-31-lin-timeout
test/TEST-12-can-timeout
```

기존 ECU별 Branch는 현재 작업 이력으로 보존할 수 있으나, 신규 작업은 Jira Key 포함 Branch를 사용합니다.

## 7. Commit 및 Pull Request 규칙

### Commit

Commit은 하나의 목적만 포함하고 Jira Key와 동사를 사용합니다.

```text
GW-23 add CAN gear signal decoder
GW-23 implement reverse lamp routing
CAN-08 update vehicle.dbc for Gear enum
TEST-12 add CAN timeout fixture
```

다음과 같은 메시지는 사용하지 않습니다.

```text
수정
최종
진짜최종
fix
수정 2
```

### Pull Request

PR 제목은 다음 형식을 사용합니다.

```text
[GW-23] Implement Reverse Lamp Routing
```

PR 본문에 다음 내용을 포함합니다.

- Jira Issue
- 변경 목적과 변경 파일
- 테스트 환경 및 Bus 설정
- Build 결과
- Unit/Integration/Fault Test 결과
- CAN raw/DBC decode 또는 LIN waveform Evidence
- 상대 담당자 Review 결과
- Known Limitation

## 8. 업로드 전 체크리스트

- [ ] 올바른 Repository 폴더에 파일을 배치했는지 확인
- [ ] 파일명이 산출물 의미와 일치하는지 확인
- [ ] 개인 경로, 임시 파일, 생성물이 포함되지 않았는지 확인
- [ ] 관련 Matrix/DBC/LDF와 내용이 일치하는지 확인
- [ ] CAN/LIN Interface 변경 시 상대 담당자 리뷰를 요청했는지 확인
- [ ] 정상·경계·Fault Test를 수행했는지 확인
- [ ] 실제 측정값과 Evidence를 연결했는지 확인
- [ ] Jira Issue, Branch, Commit, PR 링크를 기록했는지 확인

## 9. Definition of Done

Merge만으로 Done 처리하지 않습니다. 다음 조건을 모두 확인합니다.

- Clean Build 통과
- 대상 MCU Flash/Boot 및 Heartbeat 확인
- CANable/DBC Decode 또는 PulseView Waveform 확인
- 정상·경계·Fault Test 결과 기록
- 최소 1명 Review 승인
- Matrix, DBC, Schedule, Setup/Test 문서 갱신
- Jira 상태, PR 링크, Evidence 링크, Known Limitation 갱신

기능별 추가 기준입니다.

- CAN Message: Matrix와 DBC의 ID/DLC/Signal 및 Encode/Decode 일치
- LIN Frame: Matrix/Schedule와 PID/Data/Checksum 및 Timing 일치
- Routing: 양방향 Source/Destination, Conversion, Output 상태 확인
- Fault: Detection, State, Action, External Propagation, Recovery, Log 확인
- PC Tool: 실제 CAN Interface Monitor/Decode/Logging 및 최소 1개 Fault Injection 수행

Fault 감지 후 Cluster 또는 PC Tool로 외부 전파되지 않는 구현은 완료로 판단하지 않습니다.

## 10. 기준 문서

- `CAN-LIN Gateway Handbook v1.0`
- `시스템 아키텍처 사양서 v1.0`
- `D-07 Fault Handling & Fail-safe 설계보고서`
- 승인된 CAN Matrix, LIN Matrix/Schedule, DBC/LDF
- 관련 Jira Issue 및 PR

기준 문서와 실제 산출물이 충돌하면 충돌 사실을 먼저 기록하고, Interface 변경 절차와 상대 담당자 리뷰를 거쳐 확정합니다.
