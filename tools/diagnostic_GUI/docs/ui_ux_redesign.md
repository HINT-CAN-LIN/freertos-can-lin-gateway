# HINT-48 Phase 3K-1 UI/UX Inventory and Gap Analysis

작성일: 2026-10-17 (Asia/Seoul). 기준 Branch: PC-Diagnostic-Test.
기준 HEAD: 5c3e95db4ff53117afb575f5b7337f6265bcd327.
범위는 화면 배치·스타일·탐색·관측 요약·표시 필터다. CAN Interface/Decode/Cache/ECU 제어/송신/DBC/Routing 정책은 변경하지 않는다.

## 1. 확인한 기준 및 원본 시안

- [핸드북](../../../docs/archive/initial/FreeRTOS_CAN_LIN_Project_핸드북_kr_초기버전.pdf): §11.1~11.4 p29–30의 계층 분리 및 화면 계획. §4.2/§5.5/15장의 소유권·Interface 변경·Review/Done 경계.
- [기능 정의서](../../../docs/requirements/03__기능_정의서_ver1.2.xlsx): Function definition 행113~132의 PC 입력/출력·Raw/Decode/Vehicle/Health/Network/Fault/Graph/Logging.
- [기능 분석](../../../docs/requirements/04__시스템_기능_분석_ver1.2.xlsx): System function analysis 행29~32, SF_15~18.
- [요구사항](../../../docs/requirements/05__요구사항_명세서_ver1.2.xlsx): Requirements 행32~41, SYS_REQ_027~036. 승인되지 않은 Signal/Health/Fault 의미를 이 UI 단계에서 확정하지 않는다.
- [README](../README.md), [VERIFICATION](../VERIFICATION.md), 실제 MainWindow와 기존 View/테스트.
- 기존 [Interface 리뷰](pc_driver_input_interface_review.md)와 [팀 체크리스트](pc_driver_input_team_review_checklist.md)는 보존 대상이다.

추적 파일에서 최초 UI 시안(.ui/.fig/.png/.jpg/.svg/.html)은 발견하지 못했다.
Worktree .test-tmp의 과거 PNG는 자동 Smoke 증적이며 최초 디자인 시안으로 취급하지 않는다.
따라서 원본 그림과 1:1 일치한다고 주장하지 않는다. 아래 비교 대상은 핸드북/기능 정의의 화면 계획과 실제 코드다.
새 before-* 캡처는 변경 직전 Windows 창이며 원본 시안이 아니다.

## 2. 계획과 구현의 1:1 비교

상태는 중복될 수 있다. '구현 완료'는 명시한 소프트웨어 범위만 뜻하며 Production/Hardware 완료가 아니다.

| 계획 / 근거 | 변경 전 실제 화면 | 이번 UI 개선 | 현재 상태 / 남은 Gap |
|---|---|---|---|
| 통합 Dashboard / 이번 요청 | 통합 요약 없음; 각 탭에서 확인 | 기존 상태·계수·ECU 관측·Fault 이력·Logging·Vehicle 표시를 6개 카드/Source 배지로 요약 | 구현 완료(관측 요약), Live 미검증 |
| Driver Control / Phase 3J-1 | 한 세로 form, 긴 정책/결과, Mock 입력 | Driving/Body/Request result 그룹; Accelerator 표시, 기존 Brake/Gear 선택 유지; Mock Accepted와 ECU Response 분리 | Mock 전용, Interface 승인 대기, Live TX Blocked |
| Raw CAN / HB11.2·기능123 | Timestamp/Channel/ID/DLC/DATA 500행, 선택 상세 | 검색·STD/EXT·Decode Error 표시 필터, ID 전체 폭/tooltip, 공통 표/숫자 정렬 | 구현 완료(Raw 관측/표시 필터); Raw Pause 미구현. Stop은 Pause로 재정의하지 않음 |
| DBC Decode / HB11.2·기능124 | 명시 DBC 선택, 선택 프레임/정상 Cache 별도 | 기존 표/상세를 동일 Monitor 페이지에 유지, 단위·값 정렬/오류 보조 색상 | 구현 완료(지원 Classic CAN 범위), Production 의미/Live 미검증 |
| Vehicle / HB11.2·기능125 | 명시적 Message/Signal/Channel 매핑과 마지막 정상값 | 동일 View+표 스타일, Dashboard는 이 표시값 그대로 요약 | 부분 구현, Live 미검증, Production 매핑 승인 대기. Ignition 임의 추가 없음 |
| ECU Health / HB11.2·기능126 | 7개 ECU 사용자 매핑, Observed·Count·Age | ECU Observation 명칭의 Navigation, 기존 카드/통계/탭 그대로, Dashboard 관측 이름만 요약 | 부분 구현. Observed는 Healthy/Online 판정 아님; 실제 Health 계약/Live 미검증 |
| Network / KPI / HB11.2·기능127 | 처리된 RX 통계는 ECU 화면에 있음; 종합 KPI 화면 없음 | 실제 Statistics 유지, Dashboard에 Not Implemented 안내 | 미구현(종합 Network/KPI). frames/s·threshold·CAN/LIN timeout 실측치를 생성하지 않음 |
| Fault / 기능128·131 | 명시 출처의 유한 이력·필터·상세, Status Unknown | 기존 이력/필터/상세를 공통 스타일로 표시, 관측 건수 요약 | 부분 구현, Interface 승인 대기. Active/Cleared/Severity 또는 Fault-free 추론 없음 |
| Graph / HB11.2·기능129 | 단일 명시 Signal, 유한 sample, Pause/Resume/Clear | 기존 Canvas/버튼/모델 유지, 주변 스타일·탐색·표 가독성 통일 | 구현 완료(단일 Signal 관측); Live·고부하/장시간 미검증 |
| Logging / HB11.2·기능130~132 | Raw CSV/JSONL, 독립 Writer, 오류/계수/Queue | 기존 Recording/Stopping/Error·계수·오류 영역 유지, Dashboard immutable snapshot 요약 | 구현 완료(Raw 파일 계약); Decoded/Event Export schema 후속 검토 |
| Automation / SF_18 | 고정 11개 Mock/Fake Scenario, assertion 결과/취소·오류 | 동일 Runner/View/Scenario·PASS/FAIL 문자 유지, 공통 표/탐색/오류 접근 | Mock 전용. 실제 HIL/ECU PASS 및 결과 Report export 미구현 |
| Fault Injection / HB11.2·기능116~122 | GUI 실제 주입 없음; CLI Raw Sender 및 Mock 시험은 별개 | Not Implemented 안내만 제공 | 미구현, Interface/송신 승인 대기. 주입·송신 로직 신규 구현 없음 |

## 3. 디자인 시스템

| 요소 | 적용 원칙 |
|---|---|
| 배경/표면/본문 | #f2f5f9 / #ffffff / #182b42, 경계 #d7e0eb |
| Navigation / 강조 | #14283f / #087f8c. 강조색은 주 동작/선택 표시이며 ECU 정상 판정이 아님 |
| 경고/미검증 / 오류 | #875600 / #b32636. No Data/Unknown/NOT VERIFIED/Error/PASS/FAIL 문자를 함께 유지 |
| 폰트 | Segoe UI 기본, 표는 Consolas 요청 및 플랫폼 fallback. 전역 QApplication/CLI 설정은 변경하지 않음 |
| 여백/구조 | 창 여백14, 카드 내부16/14, 카드 간격12. 모두 GUI 표시 설정 |
| 버튼 | 공통 border/hover/focus/disabled. Start/Apply만 주요 동작 강조. disabled Live TX 유지 |
| 표 | 교대 행/헤더/readonly 유지. Value/Timestamp/Age/Count/DLC 오른쪽 정렬, Unit 문자열 그대로. ID 폭은 실제 텍스트와 글꼴 측정값으로 확보 |
| 긴 내용 | 원문 값/오류/출처 보존, tooltip·기존 상세 영역·페이지별 스크롤로 접근 |
| 접근성 | Navigation 방향키/Home/End, Alt+1~9, 기존 Tab 이동, focus border, Source/상태/오류 문자와 accessibleName |
| 작은 창 | 800×600/1024×768 자동 검증. 페이지마다 독립 QScrollArea, Dashboard 좁은 폭 1열, Driver 창 폭1200 미만 세로 배치 |

고정 1200/620/표 행 높이/색상은 레이아웃 설정이며 CAN/LIN 주기·Timeout·Health 정책이 아니다.
OS Screen Reader, 모든 DPI/테마 및 사용자 수동 사용성은 NOT VERIFIED다.

## 4. Navigation과 데이터 흐름

Navigation 순서: Dashboard → Driver Control → CAN Monitor / Decode → Vehicle Status → ECU Observation → Fault Monitor → Signal Graph → Logging → Test Automation.
초기 페이지는 기존 CAN Monitor를 유지한다. Dashboard는 첫 Navigation 항목/Alt+1로 접근한다.
기존 tabs의 View 객체/이름/번호(0~7), setCurrentWidget/indexOf/currentWidget 접근은 보존하며 Dashboard를 마지막 index에 추가했다.
Automation 비활성 창에서는 해당 항목이 없다.

상단: 제목/Mock·Live 출처/Hardware 상태 → Start·Stop·Clear·Select DBC·Connection settings → DBC/정책/계수.
연결 설정 펼치기는 편집기를 보이게 할 뿐 Source 변경·장치 연결을 수행하지 않는다.
하단 Activity & Errors는 페이지와 독립적으로 유지해 종료/수신/Writer 오류를 확인할 수 있다.
페이지별 스크롤로 다른 화면의 최소 크기나 스크롤 위치가 Dashboard에 섞이지 않도록 했다.

CAN/Mock → 기존 Worker → 유한 Buffer → 기존 DecodeSession/Cache/각 모델·View.
Dashboard는 기존 View의 표시와 Logging immutable snapshot만 읽는다. 새 Decode·ECU 추론·Worker·Timer가 없다.
Raw 필터는 기존 최대500행의 hide/show만 수행한다. Raw 객체·선택 결과·Received/Processed·Cache·파일 Logging을 삭제/재해석하지 않는다.
GUI Buffer Drop, Logging Queue Drop, Fault 이력 상한 제외의 의미를 합치지 않는다.

## 5. 기능 보호와 표시 경계

- Mock/Live Source 전환·DBC Reload·Clear 계약을 유지한다. Cache의 마지막 정상값을 Age만으로 삭제/고장 판정하지 않는다.
- Driver 모델/Validation/Adapter/Apply·Reset은 기존 메모리 동작이다. Body 목적지/Enum/제어 우선순위를 정하지 않는다.
- Mock Accepted와 ECU Response Not Verified를 분리하고 Live TX 버튼/직접 호출 차단을 유지한다.
- Graph sample1000/렌더200ms·Timestamp/NaN·segment 정책, CSV/JSONL byte 계약, Automation 11개 Scenario는 변경하지 않는다.
- Receiver/Writer/Timer 종료와 종료 오류 시 첫 Close 유지 계약을 변경하지 않는다.
- 기존 CLI Sender/Interface/Codec/Cache/Logger, 공통 DB/Matrix/Routing/Requirements 및 ECU Firmware는 변경하지 않는다.
- Production CAN/LIN Interface 변경은 별도 Jira와 상대 담당자 리뷰 필요. 이번 UI 준비/테스트 PASS는 해당 승인 증거가 아니다.

## 6. 1~3일 Task 분할 및 후속 제안

아래는 계획/후속 등록용 초안이다. 실제 Jira Issue 생성·담당 배정·Done 처리는 하지 않는다.
기간은 작업 묶음 제안이며 실제 투입 일수/승인 일정의 확정이 아니다.

| 후보 | 크기 | 범위 / 독립 검증 | 이번 범위 |
|---|---|---|---|
| UI-K1 Inventory | 1일 | 핸드북/기능 정의와 실제 화면 비교·원본 시안 유무·상태 분류 | 본 문서 |
| UI-K2 Design system | 1일 | QSS·표/숫자·focus·disabled·상태 문자 | 공통 스타일 |
| UI-K3 Shell | 1~2일 | Navigation/Header/오류 영역·Tab 계약·페이지별 스크롤 | 구현/회귀 대상 |
| UI-K4 Dashboard/Driver | 1~2일 | No Data·기존 관측 요약·Mock/ECU 응답 분리·Live 차단 | 구현/회귀 대상 |
| UI-K5 Observation pages | 1~2일 | Monitor 표시 필터·Decode/Vehicle/ECU/Fault 공통 스타일 | 구현/회귀 대상 |
| UI-K6 Graph/Logging/Automation | 1일 | 기존 View/정책 유지·상태/표/오류 가독성 | 공통 스타일/기존 Smoke |
| UI-K7 Regression/visual | 1~2일 | 전체/CLI/Native·800/1024/1280 크기·캡처·보존 SHA | VERIFICATION 참조 |
| 후속 UX 확인 | 1~2일 | 사용자 수동 확인·DPI/Screen Reader·긴 실제 DBC 이름·표 열 너비 사용성 | NOT VERIFIED, 별도 일정/승인 |
| 후속 Network/KPI | 1~3일 설계 검토 | 실제 관측 가능 항목·산식·시간 기준·근거와 표시 정책 결정 | 미구현, 이번 범위 제외 |
| 후속 승인 Interface 연계 | 1~3일 리뷰 | 기존 J2 19개 Issue·공식 매핑/Health/Fault/Driver TX 승인 | 기존 리뷰 활용, 구현 승인 아님 |

## 7. 확인된 Troubleshooting 등록용 초안

| 후보 | 재현/기대·실제 | 원인·이번 대응 / 검증 |
|---|---|---|
| UI 최소 폭 | Offscreen 글꼴에서 800px 요청이 990px로 제한됨 | Header의 긴 제목/배지 최소 폭. 줄바꿈 적용, 동일 800px assertion 유지 |
| 페이지 간 스크롤 | 실제 800×600 캡처에서 Driver의 폭/스크롤이 Dashboard를 가림 | 탭 전체 외부 Scroll 대신 페이지별 Scroll 사용, 1열·수평 overflow 없음·독립 위치 회귀 추가 |
| EXT ID 가독성 | Raw EXT 표시가 축약돼 Format을 읽기 어려움 | 실제 글꼴/표시 문자열 폭과 tooltip 확보. ID/STD·EXT 데이터는 그대로 |
| Dashboard 오류 요약 | show_error 직후 기존 오류는 보이나 요약은 다음 갱신까지 이전 상태 | 동일 오류 이벤트에서 UI 요약 갱신, 통신 상태/복구 정책 변경 없음 |
| Native 시험 전제 | 숨겨진 매핑 페이지의 Apply 클릭 후 Observed 대기 실패 | 신규 시험이 실제 페이지/버튼 노출 후 클릭하도록 보완. 제품 결함으로 분류하지 않음 |

위 항목은 외부 Jira 등록용 재현/원인/검증 초안이며 외부 등록은 미실행이다.
최종 실제 테스트·Windows 캡처 결과와 초기 실패/재검증 구분은 [VERIFICATION](../VERIFICATION.md)의 Phase 3K-1 절에 기록한다.

## 8. Phase 3K-2 — Windows 캡처 기반 보완 (2026-10-17)

앞 절은 Phase 3K-1 기록으로 보존한다. 이번에는 기존 Windows 창을 직접 캡처해 비교했다.
사용자가 첨부한 최초 원본 UI 시안과 동일하다고 주장하지 않는다.
디자인 원칙·Source of Truth·기능별 구현/미구현 상태는 앞 절을 따르며 승인 상태를 변경하지 않는다.

| 화면 | 3K-1의 표시 Gap | 3K-2 변경 | 유지한 경계 |
|---|---|---|---|
| 공통 Header | 긴 제목/정책/계수·빈 오류 영역이 본문 공간 차지 | 3줄 compact Header, 상세/빈 Activity 접기, 새 오류 자동 펼침 | Source·Hardware·Driver TX 차단 상시, 원래 전체 문구 보존 |
| Dashboard | 6개 동등 카드·공백·작은 폭 세로 길이 | 상단 4개 핵심 요약, 넓은 폭 4열/작은 폭 2×2, Logging/Vehicle 아래 | 기존 표시/snapshot만 읽음, No Data/Unknown 구분 |
| Driver | Combo/버튼 중복·입력 결과까지 긴 정책 | Brake/Gear 버튼, 기존 Window/Light 버튼 재배치, Apply/Reset 상단, 요청/응답 분리 | 기존 Model/Adapter/Validation/History128/Source/Live 차단 |
| CAN Monitor/Decode | Timestamp 폭과 데이터 영역 구분 | raw full Timestamp 고정폭/표시 폭, 필터 범위 캡션, 기존 선택/Signal/Cache 유지 | Raw 값·STD/EXT·필터/선택 의미 불변 |
| Vehicle | 설정과 관측이 한 영역 | 접이식 Mapping, 좁은 폼 두 열, Value/Unit/State/Age 앞쪽 시각 열 | logical column 불변, 자동 매핑 없음, 확인/Apply 필수 |
| ECU | 설정/긴 설명과 관측 혼재 | 접이식 Mapping/Details, 관측/통계/읽기 전용 Fault 탭 구분 | 기존 7개 카드/통계, Observed ≠ Healthy/Online |
| Fault | Source/필터/긴 정책 혼재 | Unknown 요약 상단, 접이식 Source, 필터/History/상세 캡션 | Active Fault 추론 없음, Clear History ≠ ECU 해제 |
| Graph | 긴 설명/통계로 Canvas 공간 제한 | latest/state 사본+Canvas, 전체 문자열/통계 Details | Sample1000/render200ms/Pause/수신·Logging 불변 |
| Logging | 긴 기술 설명/빈 오류 영역 | 상태/파일/Format/Start·Stop 우선, 오류 표시, 통계/정책 Details | 파일 보호/Queue/Flush/Writer 정책 불변 |
| Automation | 설명/실행/상세 결과 계층 약함 | Scenario/실행, 접이식 설명, Summary/Assertion 구분 | 11개 Mock/Fake Scenario, 실제 HIL PASS 아님 |

### 8.1 표시용 설정과 접근성

창 여백8, 페이지 여백4, 카드 내부10/7, 카드 간격6, Navigation 폭156을 적용한다.
Header 본체는 이번 Windows 환경에서 93 logical px다.
상단 상세/제목까지 포함한 본문 시작 위치는 260→173 logical px로 줄었다.
빈 오류 영역 축소를 포함하여 800×600 본문 viewport는 228→381px다.
이는 실행 환경의 레이아웃 측정이며 차량 KPI 또는 모든 DPI 환경에 대한 보장은 아니다.

Dashboard 상세 카드 전환 기준은 실제 viewport 폭700px다. 상단 요약은 작은 화면에서 2×2다.
출처 폼은 페이지 폭760px 미만에서 두 열로 바뀐다. Driver 기존 창 폭1200 전환은 유지한다.
이 수치는 GUI 배치 설정이며 CAN 주기/Timeout/Fault Threshold가 아니다.

긴 DBC 이름은 ComboBox의 전체 선택 문자열·tooltip에 보존하고 Header는 가운데만 생략한다.
테스트에서는 기존 TEST ONLY 항목의 **표시 문자열**만 길게 바꾸고 원래 식별 data를 보존했다.
Production DBC/Signal/이름/의미를 생성하거나 긴 실제 팀 DBC 전수 검증을 수행한 것이 아니다.
Qt UI 표의 자체 가로 스크롤/기존 상세를 통해 원본 문자열에 접근한다.
모든 긴 텍스트를 작은 화면에 동시에 전부 표시했다고 주장하지 않는다.

기본 설정 패널은 기존 자동화 클릭/Widget 계약을 위해 펼침이다.
사용자가 설정을 접으면 Vehicle/ECU/Fault 관측 공간이 늘어난다.
접기는 값·enabled·확인·선택·승인 상태를 변경하지 않는다.
오류 원문·부분 파일 경고·Status Unknown·ECU Response Not Verified는 관측 의미와 구분한다.

### 8.2 확인된 Troubleshooting / Jira 등록 초안

| 후보 | 재현/원인 | 수정/완료 근거 |
|---|---|---|
| HINT-48 UI Header 최소 폭 | Offscreen에서 toolbar의 상태/카운터가 버튼과 같은 행을 차지해 800px 창이 999px로 제한됨 | 상태/카운터를 DBC 요약 행에 재배치. 기존 800px Assertion 그대로 재실행 |
| HINT-48 Dashboard 축소 전환 | 4열 요약 도입 후 작은 창 테스트에서 623px viewport인데 620px 기준이 유지되어 카드 최소 폭952/수평 overflow329 발생 | 최소 너비 고정을 해제하고 실제 viewport 폭과 700px 표시 breakpoint 사용. 기존 독립 스크롤/1열 상세 Assertion 유지 |
| 후속 UI 수동/DPI 사용성 | 현재 Windows 배율150% 자동 검증 외의 사용자 수동·모든 DPI·Screen Reader 미확인 | 1~2일, PC/테스트 담당: 사용자 검토·100/125/200% 환경·실제 긴 DBC 이름·키보드/Screen Reader 확인. 승인 증적/실제 캡처로 완료 |

외부 Jira 등록/담당자 지정/Done 처리는 미실행이다.
Production CAN/LIN Interface 변경은 기존 리뷰 19개 Issue 및 팀 체크리스트를 따라 **상대 담당자 리뷰 필요**다.
0x600 미승인, VCU_Command(0x100) PC 대체 송신 금지, TorqueRequest VCU 책임을 유지한다.
Network/KPI/실제 Fault Injection·Production 의미/매핑은 이번 UI 작업으로 구현/승인하지 않는다.

### 8.3 검증 경계

기존 595개 테스트 파일/Assertion과 3K-1의 MainWindow·필터·기존 Native 시험은 보존한다.
새 레이아웃 pytest와 Windows 9페이지×3크기 캡처/액션/접기/Alt+1~9 시험을 추가한다.
실제 실행 결과와 재검증 기록은 [VERIFICATION](../VERIFICATION.md)의 Phase 3K-2 절을 따른다.
팀 고정 라이브러리 버전·배포/Fixture 재배포 승인 미확정, 담당자 리뷰/Hardware/사용자 수동은 NOT VERIFIED다.
