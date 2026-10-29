# Phase 3L-1 — Raw Pause / Observation Export

## Scope and decisions (2026-10-17)

PC GUI 내부 표시·파일 기능이다. CAN/LIN Interface 결정이나 ECU Event 계약이 아니다.
기준 HEAD: db11a9fdb0a0a5f7c208ec9f8aeb54cad98a8ce5, PC-Diagnostic-Test.
핸드북 11.1~11.4의 Raw Pause/계층 분리 요구와 기존 RawCanFrame, DecodeSession,
SignalStateCache, FaultHistoryModel, RawCanLogger, LoggingSession 계약을 확인했다.
핸드북 예시 timestamp_ms/quality를 생성하지 않는다. 실제 frame.timestamp(초 또는 null)와
기존 Decode 상태/관측 상태만 저장한다.

### Raw Pause / Resume

사용자 결정: **Resume은 최신 최대 500행 snapshot으로 한 번 교체**한다.
Pause는 표의 행·선택을 고정한다. 수신 Worker, Decode/Cache, Vehicle/ECU/Fault,
Graph 수집, Raw Logging 및 카운터는 계속 기존 경로로 동작한다.
필터는 표시만 바꾼다. Resume은 Timestamp 정렬이나 재Decode 없이 처리 도착 순서를 사용한다.
보관 중인 선택은 유지하고 상한으로 제외된 선택/과거 프레임은 복원하지 않는다.

- 기존 수신 버퍼512 / drop-oldest, 한 drain 최대100, Raw 표500행 정책 유지.
- 별도 ObservationHistory는 불변 처리 결과 참조500개로 제한한다.
  Pause 표가 보유한 최대500개와 최신 이력500개는 서로 다를 수 있으며 모두 유한하다.
- Export 한 건만 진행 가능하며 추가로 고정한 최대500개 참조를 완료/다음 Export까지 보유한다.
  Signal별 CSV/JSON 행은 파일 Writer에서 한 행씩 생성한다. 무제한 History Replay는 없다.
- Clear: 기존 수신 버퍼/Raw 표/표시 카운터와 새 표시 이력을 비운다. **Pause는 유지**한다.
  기존 정상 Signal Cache 유지, ECU 관측 Clear 등 기존 동작도 유지한다.
- Stop/다음 Start: Pause 유지, Stop drain 및 기존 Receiver/Logger 수명주기 유지.
- Source 변경: 기존 허용 조건을 유지하고 Raw 이력/표를 비우며 Pause 해제. 과거 Source 재생 없음.
- DBC reload: 기존 Raw 역사 행은 보존하고 Pause 유지. 기존 Cache/관측 session 정책 유지.
  Decoded Export는 새 session RX만 포함하므로 이전 DBC 값을 새 정의의 값으로 내보내지 않는다.
- Close: Export Writer도 기존 파일 Session 종료 계약으로 정리한다.

## Export selection and safety

CAN Monitor의 Export Decoded / Fault Monitor의 Export Fault History에서 JSONL 또는 CSV를 고른다.
사용자가 파일 경로를 선택한 경우에만 저장한다. **기존 파일 덮어쓰기·Append는 미지원**이며
exclusive create(`x`)로 실패시킨다. 파일 확인/생성의 경합도 기존 파일을 truncate하지 않는다.
No DBC/No Data는 파일 생성 전에 안내한다. Cancel은 파일을 만들지 않는다.

파일 dialog를 열기 전에 immutable snapshot을 고정한다. 모달 이벤트 루프의 추가 수신이나
Source/DBC 변경이 snapshot의 Source/값을 바꾸지 않는다. 표시 필터는 Export 범위를 줄이지 않는다.
Source는 Decoded 처리 당시 envelope / 기존 FaultHistoryEntry에서 가져온다.
현재 전역 Source나 Channel 문자열에서 과거 Source를 추정하지 않는다.

기존 LoggingSession + 전용 SnapshotFileWriter를 재사용한다. Raw Logger와 독립된 한 건의
snapshot queue(capacity1)이며 새 Thread 구현/Timer는 없다. 직렬화·open/write/flush/close는
기존 Writer thread에서 실행하고 상태 조회는 기존 GUI timer를 사용한다.
Writer의 written은 snapshot 작업 완료 수(0/1)다. GUI의 rows는 snapshot에서 계산한 행 수이며,
**closed + no error + written=1**일 때만 완료라고 알린다.

Export Error는 Activity & Errors로 전달한다. CAN Error로 바꾸거나 Raw Logging을 중지하지 않는다.
권한/open/write/flush/close 실패에는 부분 파일이 남을 수 있다. 자동 삭제·이어쓰기하지 않는다.
실패 시 완전한 행 수나 파일 성공을 주장하지 않는다. 기존 파일은 보존한다.
Close는 기존1초 wait 후 Writer 미종료면 창을 유지한다. 첫 Error Close도 원인을 표시하고 창을 유지하며
다음 Close에서 안전하게 종료한다. I/O 강제 중단은 하지 않는다.

UTF-8, newline=""를 기존 Logger와 같이 사용한다.
CSV는 표준 csv.DictWriter의 CRLF, JSONL은 한 JSON 객체와 LF이며 NaN/Infinity는 허용하지 않는다.
숫자는 원래 decoded 값이다. Raw Logger 파일 계약은 바꾸지 않는다.
Export는 **유한 관측 snapshot**이다. 전체 CAN 수신/연속 녹화나 무손실 기록을 뜻하지 않는다.

## Local file schema: pc-observation-v1

공통 필드:

| 필드 | 의미 |
|---|---|
| schema_version | PC 로컬 파일 schema `pc-observation-v1` |
| record_type | `decoded_observation` 또는 `fault_observation`; 실제 ECU Event를 의미하지 않음 |
| source | 해당 관측 시점의 기존 Mock/Live/TEST ONLY Source 문자열 |
| session_id | 기존 DBC/Source observation session 식별자. 전역 영구 ID가 아님 |
| observation_sequence | 해당 PC 보관 이력의 도착 순서. CAN Alive Counter가 아님 |
| timestamp | 원래 Raw timestamp(초), 누락은 null. PC 시각으로 대체하지 않음 |
| arbitration_id | 원래 숫자 CAN ID |
| is_extended_id / is_remote_frame / is_error_frame | 원래 STD·EXT / RTR / Error flag |
| dlc / data | 원래 DLC / 기존 RawCanFrame.to_record()의 hex payload |
| channel / channel_type | 원래 Channel과 타입; int0 / str"0" / null 구분 |
| is_rx | 원래 수신 방향 |
| message_name | 실제 per-frame Message, 확인 못하면 null |
| decode_status / error | 아래 record_type별 기존 상태 및 실제 오류 |

### Decoded fields and scope

현재 DBC session의 **보관된 최신 최대500 RX frame**. Raw 표시가 Pause여도 최신 처리 결과다.
TX는 제외한다. 같은 이름 Signal도 Channel/ID/STD·EXT/Message/session이 다른 Record로 구분한다.
기존 Codec 결과를 재사용하고 Cache의 마지막 정상값을 실패 Record에 붙이지 않는다.

| 추가 필드 | 의미 |
|---|---|
| source_mode | 관측 당시 Mock / Live 선택값; Live 실기 성공을 뜻하지 않음 |
| signal_name | 실제 Signal 이름 |
| decoded_value / unit | 실제 decoded 숫자 / DBC unit. 없는 값은 null |
| decode_status | 실제 Codec decoded / unknown / invalid 또는 결과 부재 null |
| error | Codec 오류 또는 application processing_error |

정상 Signal 한 개당 한 행이다. 실패/unknown/처리 오류/Signal 없는 관측은 값·Signal null 한 행으로
남긴다. Codec 상태와 application 오류를 별도 보존하므로 processing_error가 있는 경우에도
decode_status는 실제 Codec 상태일 수 있다. No Data는 Cache 유무와 별개다.

### Fault fields and scope

기존 FaultHistoryModel의 실제 보관 이력 최대500개 전체다. 화면 필터는 무시한다.

| 추가 필드 | 의미 |
|---|---|
| receiver_run | 기존 관측 Receiver 실행 구분 |
| signals / units | 실제 보관된 Signal 숫자 / DBC unit map |
| dbc_choices | 기존 DBC choice 설명 map; Fault 상태 판정이 아님 |
| timestamp_note | 기존 Provided/Missing/Reversed 등 timestamp 관측 메모 |
| fault_status | 기존 `Status Unknown` 그대로 |
| decode_status | 기존 Fault entry의 Observed / Decode Error 관측 상태 |

FaultCode/ECUOffline/RecoveryState/SystemState는 **실제 map에 있을 때만** 저장한다.
TEST ONLY DBC에 없으면 필드를 만들어 채우지 않는다. ECUOffline은 기존 Node Enum을 유지한다.
FaultCode0을 Clear로, DBC Choice ACTIVE/CLEARED를 새 lifecycle Event로 판정하지 않는다.

**Event 저장소는 기존 구현에 없다. Event Export는 Open / Not Implemented**다.
Fault 반복 관측을 실제 발생/복구 Event로 재구성하거나 현재 ECU Active Fault로 해석하지 않는다.

CSV의 map은 JSON 문자열, 누락 값은 `null` 문자열로 저장한다.
JSONL은 map을 객체, 누락 값은 JSON null로 보존한다.
실제 Signal/unit/enum/ID 정의를 이 파일 schema로 변경하지 않는다.

## Validation and follow-up

실제 실행 수치/로그는 VERIFICATION의 Phase 3L-1 절을 참조한다.
새 tests/test_observation_export.py, test_raw_pause.py, test_export_controls.py 및
gui_pause_export_native_smoke.py는 Mock/주입 TEST ONLY이며 Hardware 검증이 아니다.
기존 fixture와 Repository DBC는 명시적 읽기 전용 시험에서만 사용하고 기본 Production 매핑을 추가하지 않았다.

Jira 등록용 초안(외부 등록 미실행):

1. **1~2일 / Event 저장소·Export 계약 결정**: PC/시스템/Fault 담당.
   실제 Event 원천·식별자·시각·관측과 lifecycle 구분·승인 증적을 결정한다.
   완료 조건은 문서화된 계약과 담당자 리뷰이며 현재 Fault 관측을 Event로 전환하지 않는다.
2. **1~2일 / 파일 schema 및 수동 사용성 리뷰**: PC/데이터 소비자/테스트 담당.
   유한 범위·CSV null/map·Source/Channel 타입·부분 파일 처리를 리뷰하고 Windows 수동 확인한다.
3. **1~3일 / 실기·파일 I/O 장애 검증**: Hardware 준비 후 PC/테스트 담당.
   실제 ACL/디스크 고갈/고속 장시간 성능은 별도 검증한다. 현재 Mock 주입 결과로 대체하지 않는다.

팀 고정 버전 미확정, 담당자 코드 리뷰·사용자 수동 UI·CANable/ECU Hardware NOT VERIFIED.
PC 입력0x600 후보 미승인, Driver 실제 CAN TX BLOCKED, VCU_Command(0x100) PC 송신 금지 유지.
CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**이며 이번 기능으로 승인/Freeze하지 않는다.
