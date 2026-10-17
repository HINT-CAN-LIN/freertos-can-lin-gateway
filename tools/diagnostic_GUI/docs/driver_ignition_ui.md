# HINT-48 Phase 3N-1 — Ignition / Driver Control Mock UI

작성일: 2026-10-17. 기준 Branch PC-Diagnostic-Test, HEAD14e31ca40a3196222087fdf3184ab8b26088e77d.
판정: **NEEDS_REVIEW — Mock 소프트웨어 검증 PASS, Production Payload/수락 계약/Hardware는 미완료**.
기존 Phase 3M-2 파일과 Interface Review19개/승인 기록을 수정하거나 승인으로 전환하지 않았다.

## 1. 범위와 입력 모델

핸드북9.1 표9-1(p25)의 OFF/ON/RUN 입력 모델을 PC 메모리 Mock으로 확장했다.
이는 IGN_OFF → READY → DRIVE → FAULT VCU 상태 머신 구현이 아니다.
새 상태 전이, Gear/Brake Interlock, TorqueRequest 계산을 추가하지 않았다.

- [DriverInputs / Validation / Model](../src/pc_diagnostic/gui/driver_input.py):
  frozen dataclass에 마지막 필드 `ignition: str | None = None` 추가.
  기존5개 위치 인자 accelerator/brake/gear/window/light를 보존한다.
- `IGNITION_CHOICES = ("OFF", "ON", "RUN")`: 기존 Gear/Window/Light와 같은 명시적 문자열 선택.
  Python 내부 자료형이며 숫자 CAN Enum Encoding/Start Bit/Length가 아니다.
  None은 미설정이며 OFF와 다르다. 빈 문자열/소문자/숫자/bool/READY/DRIVE/IGN_OFF 등은 거부한다.
- Accelerator0..100%, Brake bool, Gear P/N/D/R, Window OPEN/CLOSE, Light ON/OFF의 기존 Mock 정책 유지.
  동시 Accelerator+Brake, OFF+Gear R 같은 요청도 그대로 기록하며 ECU interlock으로 해석하지 않는다.
- 초기/Reset: 기존 Model의 draft=None, last_accepted=None, 빈 History/미설정 선택을 유지한다.
  None을 자동 OFF로 바꾸지 않는다. 승인된 VCU ignition startup/reset 규칙은 확보하지 못했다.
- [MockDriverAdapter](../src/pc_diagnostic/gui/driver_adapter.py)는 변경하지 않았다.
  DriverCommand(sequence, timestamp, inputs, source)를 validated() 후 MockReceipt로 반환한다.
  Adapter가 field를 재인코딩하거나 Frame을 만들지 않으므로 Ignition이 같은 immutable inputs 안에 전달된다.
- Apply는 edit→request→Mock result를 최대128개 PC 내부 History에 기록한다.
  sequence는 PC 이력 번호이며 CAN Alive가 아니다. Mock Accepted는 ECU Applied가 아니다.
- Reset/Source 변경/Close는 기존 Adapter.shutdown/폐기 정책을 사용한다.
  Reset은 모든 입력과 과거 Mock 결과를 비우며 차량 OFF/정지/안전 제어 명령을 보내지 않는다.
  기존 Raw Clear는 Driver 요청을 지우지 않는다. Source 변경은 이전 미적용 입력/결과를 새 Source와 섞지 않는다.

## 2. 0x600 결정 이력과 승인 경계

| 시점/근거 | 실제 확인 범위 | 미확정 / 구현 제한 |
|---|---|---|
| 보존된 Phase3J-2/3J-2B 리뷰와 임시 Excel v0.1 | 0x600 미승인 후보, Issue19개 Pending/기존 상태 | 과거 기록을 소급 변경하지 않음 |
| 이번 사용자 지시 Phase3N-1 §5 | 사용자 전달 팀 합의: CAN ID0x600, PC→VCU, Driver Input 목적 | 승인자·팀 리뷰 증적·Matrix/DBC 반영·Freeze는 별도 확인 필요 |
| 현재 로컬 DBC/메시지 정의서/Route | 기존6개 CAN Message만 확인; 0x600 Payload는 미정의 | CAN ID 합의를 DLC/Signal/송신 허가 승인으로 확대하지 않음 |
| 이번 코드 | Ignition/Accelerator/Brake/Gear의 PC 내부 Mock 처리 | Live TX BLOCKED, Production Frame/Encoder/송신 없음 |

다음은 모두 **TBD**: Frame Format, DLC, Start Bit, Length, Endianness, Signed/Unsigned,
Factor/Offset, Enum Encoding, 주기, Timeout, Alive Counter, Fail-safe, 실제 수락/응답 계약.
특히 기존 후보와 과거 '0x600 미승인' 문구를 이번 기록과 구분한다.
UI는0x600 PC→VCU 방향을 안내하지만 Payload Pending/Live TX BLOCKED를 함께 표시한다.
VCU_Command0x100 PC 대체 송신, 새0x601 응답, 자동 ACK/자동 재명령은 구현하지 않았다.

## 3. 기존 메시지와 관측 경계

읽기 전용 비교 기준(현재 Branch 디스크):
- 핸드북5.2 표5-1 p14,9.1 표9-1 p25,4.2 p12–13 및5.5 p16.
- [메시지 정의서](../../../docs/requirements/02__메시지_정의서_ver1.2.xlsx):
  CAN_Message_Definition rows6–11 및15–20, Message_Summary rows25–30.
- [DBC](../../../network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc):
  BO_256/272/288/512/768/784 및 SG_.
  VERSION0.4 review-ready proposal이며 파일명과 내부 제안 버전을 혼동하지 않는다.
- [Routing v0.4](../../../network/routing/Gateway_Routing_Table_v0.4_CAN_to_LIN_Decision_Baseline.xlsx):
  Interface_Ref rows6–33, Vehicle_Status rows15–19. 다수 필드 OPEN/검토 상태.
- [보존 원본 리뷰](pc_driver_input_interface_review.md), [팀 체크리스트](pc_driver_input_team_review_checklist.md).

| ID / Message | DBC 송신자 → Receiver | 현재 DBC 신호 | 관측 해석 한계 |
|---|---|---|---|
|0x100 VCU_Command|VCU→MOTOR/GATEWAY/CLUSTER|TorqueRequest, Gear, Brake, AliveCounter|PC는 버스 Raw 수신/명시 DBC 해석 가능하나 DBC Receiver에 PC 없음. 수신은0x600 수락 ACK가 아님|
|0x110 Motor_Status|MOTOR→VCU/GATEWAY/CLUSTER|RPM, TorqueApplied, MotorState, AliveCounter|Raw/Decode/명시 매핑 가능. RPM 변화만으로 특정 요청 적용 성공 확정 금지|
|0x120 Vehicle_Status|GATEWAY→CLUSTER/PC_TOOL|Speed, RPM, Gear, Brake, NetworkState|현재 비교한 핸드북/메시지 정의/DBC/Routing 모두 Gateway. 비교 범위 내 Sender 충돌 미발견|
|0x200 Body_Status|GATEWAY→CLUSTER/PC_TOOL|DoorStatus, LightStatus, WindowStatus, ReverseLamp, DoorOpen|LIN 유래 상태 관측과 Driver Mock 결과는 별개|
|0x300 Gateway_Status|GATEWAY→VCU/MOTOR/CLUSTER/PC_TOOL|GatewayAlive, QueueUsage|메시지 정의서의 GatewayHealth/SystemState 설명, Routing Interface_Ref25/27의 이름과 DBC의 실제 두 신호는 차이/검토 필요|
|0x310 Fault_Status|GATEWAY→CLUSTER/PC_TOOL|FaultCode, ECUOffline, RecoveryState, SystemState|Event/lifecycle 제안 승인 경계 유지. 관측을 Actual Active Fault/ECU recovery PASS로 확정하지 않음|

현재6개는 DBC/메시지 표에서 STD/DLC8로 일치한다. Encoding은 기존 파일을 그대로 조회할 뿐
이 문서/코드에서 재정의하지 않는다. Frame/Signal 유효성 및 기존 메타데이터 차이는 원본 리뷰로 추적한다.
0x120 다른 브랜치/실제 Flash의 Sender는 새로 검증하지 않았다. 다른 정의가 발견되면 충돌로 기록하고
담당자 리뷰 전 임의 동기화하지 않는다. 원격 최신성/실제 노드 실측을 확인했다고 주장하지 않는다.

| 사용자 질문 | 현재 확인 가능 범위 |
|---|---|
|PC가 명령 송신을 요청했나?|PC 메모리 request 이력/Mock only. CAN TX Sent는 항상 Not sent|
|PC가 기존 CAN 상태를 받았나?|기존 Raw 수신 Source/Count, 명시 DBC Decode/Cache/각 관측 화면. 이번 실기 NOT VERIFIED|
|VCU가 입력을 수락했나?|명시 ACK/상관관계 계약 없음. NOT VERIFIED|
|VCU 출력이 관측됐나?|사용자가 DBC를 로드한0x100 실제 수신 시 해당 값만 관측. 명령 수락 증거로 자동 변환 안 함|
|Motor 상태 변화가 관측됐나?|0x110의 수신값/Graph로 관측 가능; 요청 인과·적용 보장은 NOT VERIFIED|
|Fault가 관측됐나?|기존 명시 매핑/Fault History를 사용. Status Unknown, FaultCode0 자동 Clear 금지, ECUOffline Node Enum 유지|

Driver 화면의 CAN RX Count는 기존 Buffer의 관측 사실/Source만 읽는다.
Driver 입력을 DBC/Cache/Fault/Logger에 가짜 ECU 데이터로 넣지 않는다.
'VCU/Motor/Fault: 명시 매핑 관측 화면에서 확인'과 ECU Applied NOT VERIFIED를 함께 표시한다.
사용자가 결과를 확인하고 다음 조작을 선택한다. ECU 내부 안전/Timeout은 사용자 다음 조작에 의존할 수 없으며
정책·구현 책임은 VCU/각 ECU에 있다.

## 4. UI와 실제 Before / After

기존9개 페이지/Alt+1..9, QSS, ChoiceStrip/ComboBox validation을 유지했다.10번째 페이지는 없다.
Driving: Ignition→Accelerator→Brake→Gear. Body: 기존 Window/Light.
상단 Apply/Reset/Live TX Blocked와0x600/Payload Pending을 유지한다.
Request result는 User Requested/Mock Accepted/CAN TX Not sent/CAN RX Source/ECU Applied NOT VERIFIED를 분리한다.
History는 Ignition부터 읽을 수 있는 입력 요약/원본 dataclass tooltip/기존128개 상한을 사용한다.

외부 증적 폴더 `hint48-phase3n1-20261017`:
- `before/`: **수정 전 실제 Windows 창**3장. 소스 수정 전에 생성했다.
- `native-verified/ignition/`: 최종 Windows 캡처21장(7상태×3해상도)과 result.json.
- `before_after.md`: 동일 해상도 Before/After를 나란히 링크/표시한 비교 자료.
- `after-first/`: History 요약 표시 보완 전 중간 증적. 최종과 구분한다.

| 평가 항목 | Before | After / 제한 |
|---|---|---|
|정보 구조|Driving3항목,Body2항목|Ignition을 Driving 첫 행에 추가,Body 분리 유지|
|조작|기존Slider/Brake/Gear/Apply/Reset|동일 widget 유지,OFF/ON/RUN ChoiceStrip 추가,미선택 허용|
|통신/결과|Interface Pending,Mock Accepted/ECU 응답 분리|0x600 방향·Payload Pending·User Requested·CAN TX Not sent·RX·ECU Applied NV 추가|
|History|긴 dataclass가 앞에서 잘림|Ignition 우선 요약과 전체 tooltip,정보 삭제 없음. 폭 부족 시 표 scroll/tooltip 필요|
|800×600|기존 page scroll|Apply·Ignition·Brake·Gear가 접근 가능,Body/결과/History는 scroll. 전부 한 화면에 보인다는 주장 없음|
|1024×768/1280×920|기존 반응형|기존 카드 배치 유지,세 해상도 실제 Native rect 접근/선택/결과 캡처|
|Mock/Live|Mock/Hardware badge,Live TX Blocked|동일 badge 유지,Live 선택 시 Ignition도 disabled/Slot/Model 차단|
|기능 보존|기존 CAN/Decode/Cache/Graph/Logging/Automation|기존735개 테스트·CLI140·Native15를 그대로 포함해 회귀 검증|

실제 캡처는 logical size800×600/1024×768/1280×920, Windows DPI 배율에 따라 PNG 픽셀은 다를 수 있다.
작은 창의 숨은 표 정보는 scroll/tooltip으로 접근한다. 사용자 수동 확인 및 전체DPI/Screen Reader는 NOT VERIFIED.

## 5. 검증과 Open

신규 시험: tests/test_driver_ignition.py(18), tests/test_driver_ignition_view.py(8).
Native: tests/gui_ignition_native_smoke.py --output-dir <새 증적 경로>.
전체/CLI/Native의 실제 결과와 기간은 VERIFICATION 최신 절에 기록한다.
기존 테스트/Assertion을 삭제하거나 약화하지 않았다.

확인된 초기 수정: 새 관측 Label의 존재하지 않는 owner.source_label 참조를 model.source로 수정.
신규 단축키 시험은 창 활성화 전 이벤트를 보내 실패했으며 기존 Native와 동일한 activation 조건을 추가했다.
제품 단축키나 기존 Assertion은 변경하지 않았다. History 문자열 잘림은 표시 요약/tooltip으로 보완했다.

담당자 결정/후속 Jira 초안(등록 미실행):
1. CAN/VCU/PC:0x600 사용자 전달 합의의 승인자·날짜·범위·ID registry·Matrix/DBC 증적 연결.
   DLC/Encoding/주기/Timeout/Alive/Fail-safe/수락 계약 확정은 상대 담당자 리뷰 필요.
2. VCU+Motor+PC: Ignition 초기/Reset/state transition 및 Gear/Brake 우선순위 계약 승인.
   Input OFF/ON/RUN과 ECU IGN_OFF/READY/DRIVE/FAULT를 구분하고 성공 검증 기준 결정.
3. Gateway+CAN+PC: Gateway_Status 두 실제 신호와 설명/Interface_Ref 차이 동기화 검토.
   0x120 Sender는 현재 자료 범위에서 Gateway로 일치; 다른 버전 발견 시 별도 충돌 추적.
4. Fault 담당+PC: Phase3M-2 실제 Fault_Status fixture/Scenario 및 Event/Replay/Resync Open 유지.
5. 실제 Hardware 준비 후 RX/Decode/출력 관측 검증. 이 Phase의 Mock 결과를 실기 증거로 사용하지 않음.

승인 후 절차: Interface Decision/Jira→기준 Matrix/메시지 정의→상대 담당자 리뷰→DBC/LDF/Routing→
Firmware/PC Encoder/Sender/Tests→Mock 통합→Hardware CAN→공통/기능 DoD.
핸드북4.2/5.5, CONTRIBUTING§5 적용. **CAN/LIN Interface 변경은 상대 담당자 리뷰 필요**.

팀 고정 라이브러리 버전·배포/Fixture 재배포 승인 미확정.
담당자 코드 리뷰/사용자 수동 UI/실제 CANable·ECU Hardware NOT VERIFIED.
실제 TX BLOCKED,0x601 미구현,Event Export Open,Integration Merge 미실행.
Git add/Commit/Push/PR/Merge/Jira 등록·Done 미실행.
