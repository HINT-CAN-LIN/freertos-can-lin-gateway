# Phase 3M-2 — Fault Injection / Mock TEST ONLY

## Scope and implementation boundary (2026-10-17)

기준 PC-Diagnostic-Test / 14e31ca40a3196222087fdf3184ab8b26088e77d.
기존 Fault Monitor 아래 **Fault Injection / Mock TEST ONLY** 패널을 추가한다.
이 기능은 **기존 TEST ONLY 관측 시험의 실행/결과 화면**이다.
실제 CAN Bus에 주입하거나 ECU Fault/Recovery를 발생시키는 기능이 아니다.

기존 ScenarioRunner 하나와 기존11개 Scenario 정의를 그대로 공유한다.
새 Runner/Thread/Timer, CAN ID/Signal/Fault Code/Threshold를 만들지 않는다.
새 FaultInjectionModel은 Qt를 import하지 않는 facade이며 기존 Scenario 객체를 참조한다.
View만 Qt Widget을 갱신하고, 실제 시험은 기존 hidden MainWindow + ScenarioInput + Mock FIFO RX 경로를 사용한다.
기존9페이지/Alt+1~9/탭 index와 Test Automation의11개 선택 목록은 유지한다.

## Usage

1. 사용자 Source를 Mock으로 둔다. 사용자 수신/Raw Logging은 실행 중이어도 된다.
2. Select DBC에서 기존 tests/fixtures/test_only.dbc를 **명시적으로** 선택한다.
3. Fault Monitor(Alt+6) 아래 패널을 펼치고 기존 Scenario를 선택한다.
4. Run Fault TEST ONLY를 누른다. Cancel/Retry cleanup, Reset test results를 제공한다.
5. Expected/Actual/Assertion 결과와 **격리된 시험 Fault History**를 확인한다.
6. Test run history에서 과거 시험을 선택한다. 이는 ECU Fault Event/현재 Fault 상태가 아니다.

실제 user Live Source에서는 실행을 막는다. 주입 Fake Live도 user Source가 Live이면 차단한다.
Mock user Source 아래 별도 **격리 Fake child**만 실행한다. 실제 Live 장치를 시험용으로 전환하지 않는다.
Fixture가 없거나 달라졌거나 Production DBC이면 실행하지 않는다.
Fixture SHA-256 계약은 기존 TEST_DBC_SHA256을 재사용하며 재배포/Wheel 포함 승인 상태는 바꾸지 않는다.

## Referenced Scenario Catalog

새 Scenario/ID/입력/expected를 정의하지 않았다. 아래는 기존11개 중3개의 **같은 객체**를 가리킨다.

| 기존 Scenario ID | 이름/대상 | 데이터 출처/DBC | 실제 예상 Assertion / 성공 조건 |
|---|---|---|---|
| HINT48-MOCK-FAULT-v1 | Fault History infrastructure | 기존 TEST ONLY TestOnlySample 두 RX, 명시적 unchanged test_only.dbc | raw_frames 일치; 기존 fault 두 관측이 Observed/Status Unknown/Measurement=-10; application_tx0, resources_released, parent_source_unchanged |
| HINT48-MOCK-DECODE-ERROR-v1 | DBC Decode failure | 기존 정상+길이 오류 TEST ONLY RX | decoded/invalid 상태, 실패 Signal empty, Raw 보존; TX0/해제/parent source 유지 |
| HINT48-MOCK-SOURCE-v1 | Isolated Source transition | 기존 TEST ONLY RX, hidden Source A→B | 기존 source_reset=(0,0,0,0,True,True), cache=(-10,11), 최종 Raw, TX0/해제/parent source 유지 |

입력과 기대값의 정확한 tuple은 기존 gui/automation.py catalog에서 읽는다.
표의 -10/11은 기존 합성 fixture의 Measurement/Timestamp이며 실제 차량 값/주기/ECU 시각이 아니다.
UI는 Scenario ID/대상/출처/실행 제한/기존 입력 및 expected 목록을 보여 준다.

공통 상태:
- PASSED: 기존 모든 실제 관측 Assertion 일치 및 자원 해제. **Mock software assertions만 PASS**.
- FAILED: actual 누락/불일치. 입력 자체를 actual로 대신 사용하지 않는다.
- ERROR: 준비/DBC/입력/Receiver/cleanup 오류. 준비 오류에는 과거 PASS를 대신 표시하지 않는다.
- CANCELLED: 미완료 Assertion은 NOT EVALUATED. Recovery PASS가 아니다.
- 실행 불가: unknown/non-supported ID, 입력 없음/잘못된 Raw/TX, Fixture 누락/불일치,
  No DBC/다른 DBC, user Live Source, closing/DBC dialog, 공유 Runner busy.
- Reset: 자신의 시험 결과/관측 snapshot만 지운다. 기존 Runner result/history와 사용자 Fault History를 지우지 않는다.

단순 VCU timeout/Alive/ECU offline/Queue drop/복구 시나리오를 추가하지 않았다.
현재 fixture의 Counter0..255를 VCU Alive0..15로 해석하지 않는다.
실제 Fault_Status4개 Signal을 포함하는 시험 입력/approved Fixture가 없으므로 해당 주입 범위는 Open이다.

## Fault contract / actual source review

읽기 전용으로 다음을 확인했다:
- Handbook10.1~10.5(p27~28): timeout/Alive/LIN no-response/fail-safe/외부 전파와 복구는 별도 ECU·통합 검증이다.
  이 문서의30ms/3cycle/modulo16과 복구 정의를 PC Mock 정책으로 복사·변경하지 않았다.
- network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc:
  Fault_Status(기존0x310, STD,8byte, Gateway 송신), lines45~49/57/78~81/99/152~155.
  현재 파일은 review-ready proposal이며 로드/관측으로 팀 승인/Freeze를 확정하지 않는다.
- tests/fixtures/test_only.dbc:
  TestOnlySample.Measurement/Mode/Counter, TestOnlyExtended.Reading, TestOnlyMux.
  **FaultCode/ECUOffline/RecoveryState/SystemState는 없다.**
- gui/fault_history.py 및 기존 tests/test_fault_history.py:
  불변 실제 관측 Entry, Status Unknown, Node Enum/DBC choice와 현재 Fault 판정 구분.
- 기존 Interface 리뷰 J2-016/018 및 체크리스트: Fault Event/대표 상태/회복/입력 응답 의미는 별도 리뷰 대상이다.

현재 DBC의 실제 Raw metadata:
- FaultCode0=NONE,1=VCU_TIMEOUT,2=DOOR_ECU_OFFLINE,3=ALIVE_ERROR,
  4=ECU_OFFLINE,5=QUEUE_DROP,6=WINDOW_ECU_OFFLINE,255=INVALID.
- ECUOffline은 Node Enum:0NONE/1VCU/2MOTOR/3GATEWAY/4CLUSTER/5DOOR/6LIGHT/7WINDOW/15INVALID.
- RecoveryState의 choice0ACTIVE/1CLEARED는 현 DBC에 있는 제안 metadata다.
  실제 Interface 승인/ECU lifecycle을 확정하지 않는다.
- SystemState는 현 DBC의0NORMAL/1DEGRADED/2OFFLINE/3FAIL_SAFE metadata다.

위 값은 **조사/읽기 전용 회귀 근거**다. 이번 UI에 Production 입력이나 가상 ECU 현재 상태로 넣지 않았다.
Gateway 송신 주체, ECUOffline Enum, FaultCode0 자동 Clear 금지, Status Unknown을 유지한다.
ACTIVE/CLEARED 의미·전파·검출/Recovery 구현을 완료했다고 주장하지 않는다.
Fault Event 저장소/Replay/Resync/새 lifecycle은 미구현·Open이다.
Clear History와 Reset test results는 ECU Fault 해제 명령이 아니다.

## Isolation and safety

1. FaultInjectionModel은 실제 owner Source/closing/선택 상태와 입력/DBC를 검사한다.
   UI Slot 직접 호출이나 Model.run 직접 호출도 같은 guard를 통과한다.
2. 기존 ScenarioRunner.start의 별도 user Live guard도 그대로다.
3. Runner는 사용자 live factory를 호출하지 않고 hidden MainWindow(automation_enabled=False)에서
   기존 ScenarioInput(CanInterface + MockCanInterface FIFO)을 사용한다.
   hidden child에는 이 패널을 만들지 않으므로 새 Runner 재귀 생성이 없다.
4. 실제 can.Bus/Adapter send/Mock send/ScenarioInput send 경로는 실행하지 않는다.
   ScenarioInput.send는 기존 코드대로 거부하며 시험에서 send_calls0을 확인한다.
   새 코드에는 ECU 제어 API가 없다.
5. 사용자의 Receiver/Logger/Graph/Cache/Fault/Network 세션을 중단하거나 Fake 데이터로 교체하지 않는다.
   기존 Source/DBC 편집 잠금을 유지한다. 보통 programmatic 변경도 ConnectionView가 원복한다.
6. 실제 owner raw settings가 달라지는 강제 변경은 기존 Runner.changed/tick에서 감지해 자신의 trial만 cancel한다.
   같은 cancel을 재진입 반복하지 않는다. Source 변경을 임의로 승인/복구하거나 user Receiver를 중지하지 않는다.
7. Close는 기존 automation_active→request_close→비동기 cleanup→parent close 재시도 경로를 사용한다.
   cleanup 미완료 Error는 session 참조/취소 재시도를 유지하고 강제 Thread 종료를 하지 않는다.

Bus Open0/TX0은 Mock 자동 시험의 계측 결과다.
실제 장치 listen-only/ACK 무송신 검증 또는 물리 Fault 검증을 뜻하지 않는다.

## Observation and test history

Runner.changed에서 hidden child의 **기존 FaultHistoryEntry**를 불변 참조 tuple로 읽는다.
다시 Decode하거나 Payload/Enum을 재정의하지 않는다.
최대 입력8개, 시험 결과10개는 기존 MAX_SCENARIO_FRAMES/MAX_RESULTS 상한을 재사용한다.
새 FaultTestRecord는 기존 RunResult와 이 snapshot을 함께 보관하는 **PC test result**이며 ECU Event 저장소가 아니다.
기존 Test Automation result/history와 사용자 Fault Monitor history는 별개다.

Source reset 시험은 hidden Source 변경 뒤의 실제 이력을 보관한다. 과거 Source를 재생/복구하지 않는다.
Assertion FAIL/Cancel/ERROR도 실제 관측과 상태를 구분한다.
Fault History의 정상 관측과 실제 ECU Fault/Recovery 판정은 끝까지 다르다.

## Verification / remaining review

실제 실행 결과와 Windows 캡처/회귀 결과는 VERIFICATION의 Phase3M-2 절을 참조한다.
신규 test_fault_injection.py는 Qt 독립 guard/소유권/유한 이력 시험,
test_fault_injection_view.py는 기존 Runner/실제 Qt 파이프라인 시험,
gui_fault_injection_native_smoke.py는 실제 Windows 창의 Mock/Fake 자동 시험이다.
기존699개 테스트/11개 Scenario/Assertion/Fixture/Runner 구현을 보존한다.

후속 Jira 등록용 초안(외부 등록 미실행,1~3일 작업):
- **Fault_Status TEST ONLY Fixture/Scenario 범위 리뷰** — PC/Gateway/시스템/테스트 담당.
  현재 fixture 부재와 배포 미승인을 해소할 승인 근거/허용 범위/expected를 합의한다.
  완료 조건은 담당자 리뷰와 fixture/관측/actual assertion 계약이다. 지금 새 값/ID를 확정하지 않는다.
- **Fault Event/Recovery·Replay/Resync 계약 리뷰** — Gateway/Cluster/PC/시스템 담당.
  J2-016/018과 연계해 의미/전파/재동기화 증거를 정리한다. Open을 코드로 대신 닫지 않는다.
- **실제 Fault 통합 시험 Gate** — Hardware/각 ECU/PC/테스트 담당.
  승인 Interface·Firmware·배선/종단·전원·송신 노드·측정 증거 준비 후 별도 승인 작업으로 진행한다.
  현재 software PASS를 ECU fail-safe/Recovery PASS로 쓰지 않는다.

팀 고정 버전·배포/Fixture 재배포 승인은 미확정, 담당자 코드 리뷰·사용자 수동 UI·Hardware NOT VERIFIED.
Driver Live TX BLOCKED, PC 입력0x600 후보 미승인, VCU_Command(0x100) PC 송신 금지 유지.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**, 핸드북4.2/5.5 Interface Change 절차를 따른다.
Git add/Commit/Push/PR/Merge/Jira 등록·Done 미실행.
