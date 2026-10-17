# Phase 3L-2 — CAN Network / KPI Observation

## Scope / responsibility

기준: PC-Diagnostic-Test / cdc3598dd1a896b9927373cab11708f5b0baf94b, 2026-10-17.
NetworkStatisticsModel은 GUI와 독립된 기존 RawCanFrame RX 집계다.
Worker/Adapter/Codec/Signal Cache/기존 ECU 통계의 Public Interface는 바꾸지 않는다.
새 Thread/Timer/패키지는 없다. 기존 GUI drain 지점에서 각 프레임을 한 번만 계수한다.
**계산된 수치는 관측 Timestamp의 산술 결과이며 실제 Hardware 성능 PASS가 아니다.**

Dashboard에서 **Network / KPI — observed RX**를 펼친다.
기존9개 Navigation/Alt+1~9/탭 index를 보존하기 위해 Dashboard 내부 패널로 배치했다.
Source, 처리된 RX, 보관 CAN ID/identity 수, GUI Buffer Drop, 키 상한 제외, 제공된 Error Frame 수,
ID별 표와 정의/정밀값 상세, CSV/JSONL Export를 제공한다.
좁은 화면은 기존 페이지 스크롤과 표 자체 가로 스크롤을 사용한다.
숫자는 표에서9 유효자리로 표시하고 선택 상세/Export에서 원래 정밀도를 보존한다.

## Source / Timestamp investigation

| 근거 | 실제 의미 / 한계 |
|---|---|
| gui/demo.py make_demo_frame | 기존 TEST ONLY Frame, time.time() 초 단위 wall clock. 단조/정확도 보장 없음 |
| interfaces.py PythonCanInterface.recv | python-can Message.timestamp를 RawCanFrame에 그대로 전달. Clock 변환/교정 없음 |
| 설치 python-can4.6.1 can/interfaces/slcan.py:328 | time.time()으로 host 수신 시각 생성. ECU 송신 시각/물리 Bus timestamp 아님 |
| 설치 python-can4.6.1 can/interfaces/gs_usb.py:150~151 | GsUsbFrame.timestamp 전달. 하위 gs_usb clock/epoch/정확도는 미검증 |
| tests/fake_live.py | TEST ONLY Frame Timestamp를 재사용할 수 있어 반복·역전 발생 가능. 실기 Source 아님 |
| Network Native TimedFake | 기존 fixture Timestamp를 시험용 결정적 값으로 주입. 실제 도착 주기 측정 아님 |

GUI/Export는 Mock, 주입 Live TEST ONLY, 일반 Live RX를 구분한다.
일반 Live 선택도 Hardware Verified를 의미하지 않는다. 모든 결과의 Hardware/clock accuracy는 NOT VERIFIED다.
Raw Timestamp 단위는 초이며 millisecond epoch/monotonic timestamp로 재해석하지 않는다.
서로 다른 Channel/ID의 clock을 합친 전역 관측 Duration/Frame Rate는 계산하지 않는다.

값의 유효성을 확인한 동일 identity 연속 Timestamp 차이만 **descriptive observed interval**로 계산한다.
이 산술값은 clock 정확도 보증·송신 Task 실행 Jitter·Bus 전송 지연·HIL PASS를 뜻하지 않는다.
누락/중복/역전/누적 수치 overflow가 있으면 해당 identity의 시간 통계는 구간 전체에서 N/A다.
한 프레임뿐이거나 유효 연속 간격이 없을 때도 N/A다. Timestamp는 삭제/정렬/PC 시각 대체하지 않는다.
Raw/Decode/Cache 경로의 원본 값은 그대로다.

## Statistics and bounded storage

- 기존 MessageKey의 Channel/숫자ID/STD·EXT/RTR/Error flag를 재사용한다.
  Channel int0/str"0"/null과 동일 숫자ID의 STD/EXT를 섞지 않는다.
- Processed RX는 GUI drain으로 실제 처리한 RX 부분집합이다. TX는 따로 ignored_tx로 세고 분석에서 제외한다.
  Worker ingress Received, Raw Logger written, 화면500행 수와 다르다.
- Tracked CAN IDs는 Channel+ID+STD/EXT의 보관된 수다. RTR은 같은ID로 묶고 Error mask는 제외한다.
  표 identity는 RTR/Error까지 구분하므로 그 수와 다를 수 있다.
- 기존 MAX_STATISTICS_ENTRIES=512를 PC 저장 상한으로 재사용한다.
  기존 키 집계는 계속하고 상한 이후의 새 키 프레임만 capacity_excluded로 센다.
  ID 수는 상한 제외가 있으면 전체 Bus ID 수가 아니다.
- 키당 Count, 첫/마지막 Timestamp, 간격 수/합/최소/최대/마지막, 이상 계수만 보관한다.
  무제한 Frame/간격 배열을 저장하지 않는다. Raw500행 제외와 독립적으로 Count를 유지한다.
- FrameBuffer512/drop-oldest, drain100, Raw500행 및 Logging Queue 정책은 바꾸지 않는다.
  GUI 처리 전 Drop은 누락 ID/개수를 추정해 배분하지 않는다.
  해당 구간의 GUI Drop/키 상한 제외/분리 못한 이전 run backlog가 있으면 모든 시간 KPI를 N/A로 한다.
- 누락/상한 때문에 Raw Logger와 Network Count가 다를 수 있다.
  Adapter/OS/물리 Bus 누락은 측정할 수 없고, GUI Drop0도 무손실 Bus 수신의 증거가 아니다.

## Observed interval / duration / rate

각 identity의 한 receiver-run 내에서 도착 순서로 인접한 정상 Timestamp의 양수 차이를 d_i로 둔다.
이 공식은 **PC 관측 통계 정의**이며 프로젝트 공식 Jitter 정의가 아니다.

- Mean = sum(d_i) / interval_count
- Min / Max = 유효 간격의 최소/최대
- Observed span = sum(d_i), receiver-run별 관측 span의 합
- Observed rate = interval_count / observed span = 1 / Mean
- 연속된 n개 샘플 한 run의 간격 수는 n-1이다. Count/span으로 첫 샘플을 중복 계산하지 않는다.
- Stop/Start 사이 미관측 시간을 span이나 Message 간격으로 포함하지 않는다.
  여러 run은 interval_segments/receiver_runs로 표시하고 각 run 내부 간격만 합친다.
  따라서 first_timestamp~last_timestamp의 단순 차이와 observed span은 다를 수 있다.
- N/A 조건에서는 위 시간 통계를 null로 내보낸다. 이미 센 Frame/원본 Timestamp/이상 계수는 유지한다.
  interval_count는 판정 근거인 수집된 양수 간격 수이며 완전한 Bus 간격 수가 아니다.

## Expected Period and source reconciliation

조사한 실제 기준:
- docs/requirements/02__메시지_정의서_ver1.2.xlsx, CAN_Message_Definition rows6~11.
- network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc, VERSION0.4 review-ready proposal,
  BO_, SourceTxType, GenMsgCycleTime.
- docs/requirements/05__요구사항_명세서_ver1.2.xlsx, Requirements row41 SYS_REQ_036:
  실제 KPI 결과와 목표값을 구분한다. 내용 Overview는 V0.5다.
- network/routing/Gateway_Routing_Table_v0.4_CAN_to_LIN_Decision_Baseline.xlsx,
  Interface_Ref rows7~10/24~33 및 CAN_to_LIN 경로. LIN slot/명령 주기를 CAN 관측 주기로 바꾸지 않는다.

| Message | 실제 CAN ID | Format / DLC | 정의서 주기 | 현재 DBC |
|---|---|---|---|---|
| VCU_Command | 0x100 | STD /8 | 10ms | Cyclic /10ms |
| Motor_Status | 0x110 | STD /8 | 10ms | Cyclic /10ms |
| Vehicle_Status | 0x120 | STD /8 | 20ms | Cyclic /20ms |
| Body_Status | 0x200 | STD /8 | 100ms | Cyclic /100ms |
| Gateway_Status | 0x300 | STD /8 | 100ms | Cyclic /100ms |
| Fault_Status | 0x310 | STD /8 | Event | Event /주기 없음 |

위6개는 이번 비교 범위에서 이름/ID/Format/DLC/주기 일치다.
Signal metadata/전체 Interface 승인 또는 Freeze 완료를 의미하지 않는다.
특히 Gateway/Fault 정의서 Review는 상대 담당자 리뷰 필요 상태다.

프로그램에는 이 표의 ID/주기 기본 매핑을 하드코딩하지 않았다.
**사용자가 로드한 DBC**에서 정확한 ID+STD/EXT Message를 찾고 SourceTxType=Cyclic와
양수 GenMsgCycleTime이 모두 있을 때만 Expected Period를 읽는다.
Event에는 임의 Expected를 적용하지 않는다. TEST ONLY fixture에는 주기 metadata가 없어 Definition Pending이다.
미로드/정의 없음/주기 없음/Error/RTR는 해당 이유와 null을 보인다.
Mean - Expected는 관측 평균(초→ms)과 metadata의 단순 차이이며 Jitter/허용오차 PASS/FAIL이 아니다.
DBC 로드 성공도 Interface 승인이 아니다. Workbook/DBC가 충돌하면 산출물 변경 전 상대 담당자 리뷰 필요다.

## Jitter / unavailable KPI

핸드북11.2 표11-1, 12.4 표12-3(p29/32)을 확인했다.
CAN cycle/jitter의10ms 메시지·±1ms는 권장 예시 목표이고 평균/최소/최대/표준편차 기록을 제안한다.
Peak-to-peak, 최대 절대 편차, 표준편차 등 중 어떤 산식이 공식 Jitter인지, 표본 창/clock/판정 기준은 명확하지 않다.
요구사항 SYS_REQ_036은 목표와 실측 구분을 요구하며 별도 공식 Jitter 산식을 확정하지 않는다.

따라서 **Jitter Definition Pending**, jitter=null이다. 임의 Threshold/표준편차 KPI를 채택하지 않았다.
후보 검토: 수신 간격 표준편차, expected 대비 최대 절대 편차, max-min.
어느 것도 송신 Task 내부 실행 Jitter와 동일하다고 주장하지 않는다.

Bus Load는 N/A/null이다. 실제 bitrate 검증·bit stuffing/overhead·수신 범위/누락 모델이 없다.
Packet Loss%, CAN→LIN latency, 실제 ECU Healthy/Offline, Controller error counter는 계산하지 않는다.
is_error_frame으로 Backend가 실제 제공한 처리 RX Error Frame 수만 센다.
Controller state/Bus-Off/Error Passive는 현재 CanInterface 계약에서 제공하지 않아 Unsupported다.
Error Frame0으로 Bus Health를 정상 판정하지 않는다.

## Lifecycle

| 동작 | 통계 정책 / 기존 근거 |
|---|---|
| Mock / Fake Live / 일반 Live 선택 | 각 Source 고정. Source 전환 Gate 뒤 Clear로 이전 통계 격리 |
| Raw Pause / Resume | Network 집계 계속. Resume 재표시에 다시 계수하지 않음 |
| Clear | 기존 ECU 통계 Clear와 같이 새 통계 구간. Raw Cache 보존 등 기존 정책 유지 |
| DBC load/reload/실패 | 기존 ECU sync_session과 같이 집계 초기화. 이전 Message metadata 혼합 방지 |
| Stop/다음 Start | 기존 Count 유지, 새 receiver-run 시작 시 간격 연결만 끊음 |
| 이전 run pending 상태 Start | Frame별 run 표식이 없어 timing N/A. 새 정책으로 과거 출처를 생성하지 않음 |
| Close | 자체 Worker/Timer가 없다. 공통 Export/Receiver/Logger 종료 계약 사용 |

Export snapshot은 Capture 시점의 Source/metadata/Count를 고정하므로 이후 수신/Clear/Source/DBC 변경과 격리된다.
표는 기존 UI 주기에서 갱신하며 No Data/미확정 상태를 정상 KPI 값으로 바꾸지 않는다.

## Export schema

schema_version=`pc-network-observation-v1`, record_type=`network_observation`.
한 CSV/JSONL 행은 **보관 identity 한 개의 구간 집계**다. Raw frame/ECU Event 한 개가 아니다.
필드는 NetworkStatisticsModel.snapshot_records의 flat primitive metadata로 고정한다.

| 필드 그룹 | 실제 필드 |
|---|---|
| 출처/식별 | source, source_kind, channel, channel_type, arbitration_id, is_extended_id, is_remote_frame, is_error_frame, message_name |
| 관측 계수/시각 | frame_count, first_timestamp, last_timestamp, interval_count, interval_segments |
| 시간 통계 | observed_duration_s, last_interval_s, mean_period_s, min_period_s, max_period_s, observed_frame_rate_hz |
| 비교 근거 | tx_type, expected_period_ms, expected_source, comparison_status, mean_minus_expected_ms |
| 상태/한계 | timing_status, jitter_status, jitter=null, timestamp_source, timestamp_unit, clock_accuracy, hardware_verification |
| 미지원 | bus_load_percent=null, controller_state=Unsupported |
| 불완전 관측 | timestamp_missing, timestamp_duplicate, timestamp_reversed, timestamp_overflow, buffer_dropped, capacity_excluded, receiver_runs, pending_run_boundary |
| 처리 범위 | processed_rx, error_frame_count |

기존 ObservationExport/LoggingSession Writer를 재사용한다. Decoded/Fault/Network 중 한 Export만 진행 가능하며
기존 Raw Logger와는 독립이다. 기존 CSV/JSONL 파일 계약을 변경하지 않는다.
UTF-8, CSV CRLF/JSONL LF, CSV 누락은 null 문자열/JSONL JSON null, NaN/Infinity 금지.
사용자가 명시적으로 선택한 새 경로만 exclusive create한다. Overwrite/Append 미지원.
No Data/Cancel은 파일 없음. Open/Write/Close 오류는 Activity에 표시하고 부분 파일이 남을 수 있다.
파일 오류는 CAN 수신 오류로 바꾸지 않는다. 미종료 Writer/첫 Close 오류는 창 유지 후 재시도한다.
Event 저장소/Export는 이번에도 Open이며 Fault 관측을 Event로 재구성하지 않는다.

## Open / Jira task drafts

외부 Jira 등록·Done 처리 미실행. 다음은1~3일 작업 단위의 등록 초안이다.

1. **KPI/Jitter 측정 계약 승인 (PC/시스템/Gateway/VCU/Motor/테스트)**:
   공식 산식·표본 창·clock 품질·허용오차·목표와 실제 결과 표시를 결정한다.
   완료 조건: 담당자 승인 증거와 재현 가능한 Timestamp/송신/수신 증적. ±1ms 예시를 자동 승인하지 않는다.
2. **Timestamp/수신 범위 Hardware 확인 (PC/Hardware/테스트)**:
   SLCAN host 수신시각과 gs_usb device timestamp의 epoch/분해능/정확도·adapter 누락/동기화를 확인한다.
   실제 CANable/ECU 및 송신 기준 capture가 필요하다. 현재 Mock 결과를 Hardware PASS로 쓰지 않는다.
3. **Bus Load/packet loss 측정 모델 검토 (시스템/PC/테스트)**:
   bitrate·CAN overhead/stuffing·관측 범위·송신 기대 수·누락 계측을 합의한다. 근거 확보 전 N/A 유지.

팀 고정 버전 미확정, 배포/Fixture 재배포 승인 미확정, 담당자 코드 리뷰 NOT VERIFIED.
사용자 수동 UI·실제 Hardware·고부하/장시간·실제 ACL/디스크 고갈 NOT VERIFIED.
0x600 미승인 후보, VCU_Command(0x100) PC 송신 금지, Driver Live TX BLOCKED 유지.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**, 핸드북4.2/5.5 Interface Change 절차를 따른다.
