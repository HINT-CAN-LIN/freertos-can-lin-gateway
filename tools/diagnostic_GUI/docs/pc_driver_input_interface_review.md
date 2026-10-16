# HINT-48 — PC Driver Input CAN Interface Review (Phase 3J-2)

- 작성일: 2026-10-16 (Asia/Seoul)
- 조사 원문은 위 고정 Commit 기준이며 최종 정리 시 원격5개 HEAD를 재조회해 동일함을 확인했다.
- 판정: **NEEDS_REVIEW — 조사/리뷰 문서 작성 완료, Production Interface 승인/Freeze 미완료**
- PC 기준: PC-Diagnostic-Test / 5c3e95db4ff53117afb575f5b7337f6265bcd327
- 실제 CAN 송신 / Hardware 검증: **NOT RUN / NOT VERIFIED**
- 담당자 승인 및 코드 리뷰: **NOT VERIFIED**

## 1. 문서 목적

PC를 운전자 입력 장치로 사용하는 계약의 충돌·누락을 식별한다.
이 문서는 CAN ID, Payload, Signal, 주기, Timeout, Fail-safe를 확정하는 산출물이 아니다.
Phase 3J-1의 메모리 Mock 모델을 Production 송신 Interface로 승격하지 않는다.

상태 분류:
- **확정**: 이번 읽기 전용 조사로 확인한 존재/코드 동작 사실, 또는 기존 산출물의 명시된 책임 범위.
  기존 파일에 값이 있다는 사실과 담당자가 Production Interface를 승인했다는 사실은 별개다.
- **초기값-수정 가능**: 임시안의 미승인 후보. 실제 송신에 사용 금지.
- **측정 후 확정**: 목표/설계값과 실제 Bus timing·PID·출력 동작의 대조가 필요한 항목. 현재 실측 없음.
- **검토 필요**: 서로 다른 정의/기준 우선순위/승인 증적 확인 필요.
- **TBD**: 값 또는 Encoding 정의가 없다.
- **Open**: 책임·경로·정책·수신 확인 방법의 팀 결정이 남아 있다.

비교 우선순위는 사용자 지시의 승인된 Matrix/DBC/메시지 정의서 → 승인된 ECU 계약 → Handbook → 임시안이다.
단, 독립 Matrix가 없고 현재 문서의 FIX/DECIDED/APPROVED 표기가 서로 다른 승인 범위를 가리키므로
어느 파일도 자동으로 전체 Interface Freeze 완료로 취급하지 않는다.
02 메시지 정의서 시트 row2/22와 01 통신 규칙 row13은 02/05 FIX 우선·Matrix 참고를 주장한다.
이 기준 권한의 최종 승인자는 J2-001에서 확인한다. 문서 충돌을 여기서 임의 해결하지 않는다.

## 2. 참조 산출물 및 버전

아래 상대 경로는 본 문서에서 Repository 파일로 연결한다.
외부 임시 Excel은 Repository Root 기준 ../HINT48_PC_Driver_Input_Interface_임시설계_v0.1.xlsx에 있으며
Git 관리/배포 산출물이 아니다. 개인 PC 절대경로는 본문에 넣지 않는다.

| Ref | 실제 경로 / 산출물 | 버전·근거·이번 확인 범위 | 승인 구분 |
|---|---|---|---|
| S00 | Repository 외부 HINT48_PC_Driver_Input_Interface_임시설계_v0.1.xlsx | 5 sheets; 요약, 메시지_제안, 신호_제안, 결정_이슈, 개발_순서 | 미승인 임시 초안 |
| S01 | [CAN DBC](../../../network/can/CAN__DB_펌웨어%20전%20최종본_v0.1.dbc) | 파일명 v0.1, 내부 VERSION 0.4 - review-ready interface proposal; BO_/SG_/VAL_/BA_/CM_ 대조 | review-ready proposal, 담당자 승인 별도 |
| S02 | [메시지 정의서](../../../docs/requirements/02__메시지_정의서_ver1.2.xlsx) | CAN_Message_Definition, CAN_Signal_Definition, Value_Table, LIN_Frame_Definition, LIN_Signal_Definition, Fault_Timeout_Policy | FIX 선언과 상대 담당자 리뷰 필요 공존 |
| S03 | [통신사양서](../../../docs/requirements/01__통신사양서_ver1.2.xlsx) | 메시지 정의, Signal 상세, 통신 규칙, 검토 항목; 내부 v5/동기화2026-09-30 | 02/05 기반 설명, 단독 승인 증적 아님 |
| S04 | [Routing v0.4](../../../network/routing/Gateway_Routing_Table_v0.4_CAN_to_LIN_Decision_Baseline.xlsx) | Decision_Baseline, Required_Interface_Changes, CAN_to_LIN, LIN_to_CAN, Interface_Ref, Review_Summary | DECIDED와 PENDING REVIEW/PENDING LDF를 구분 |
| S05 | [LIN LDF](../../../network/lin/LIN__vehicle_body_final_ver1.0.ldf) | 2.2, 6 frames, BODY_10ms/BASE_20ms; 전체 application signal/schedule | header의 APPROVED2026-09-29는 pre-firmware diagnostic baseline; Matrix sync/Freeze 리뷰는 남음 |
| S06 | [요구사항](../../../docs/requirements/05__요구사항_명세서_ver1.2.xlsx) | Requirements SYS_REQ_003, 020, 044, 045, 053, 055, 059 및 Overview/Open_Decisions | Requirements-level Frozen은 CAN/LIN 변경 승인과 별개 |
| S07 | [Handbook v1.0](../../../docs/archive/initial/FreeRTOS_CAN_LIN_Project_핸드북_kr_초기버전.pdf) | §4.2 p12–13, §5.5 p16, §9.1 p25 | 책임/변경 절차/입력 모델 예시 |
| S08 | [CONTRIBUTING](../../../CONTRIBUTING.md) | lines127–154 Interface Change / lines231–249 DoD | 상대 담당자 리뷰 필요 |
| S09 | [DriverInputModel](../src/pc_diagnostic/gui/driver_input.py) | lines8–18,37–52,135–209,211–243 | PC 내부 Mock 계약만 구현 |
| S10 | [MockDriverAdapter](../src/pc_diagnostic/gui/driver_adapter.py) | accept lines17–26, shutdown28–31 | 메모리 처리, Frame/Bus 없음 |
| S11 | [DriverControlView](../src/pc_diagnostic/gui/driver_control_view.py) | policy19–26, _can_edit110–114, apply152–160, source179–186, Live button195 | 승인 전 송신 차단 |
| S12 | [기존 CLI Sender](../src/pc_diagnostic/sender.py) | RawCanSender.send13–16 | Raw 송신 API는 존재하나 Driver 모델과 연결되지 않음 |
| S13 | [CAN Matrix 설명](../../../docs/CAN_COMMUNICATION_MATRIX.md) / [LIN 설명](../../../docs/LIN_SPECIFICATION.md) | placeholder lines2–6 /3–7 | 실제 Matrix/계약 표 아님 |

S00 SHA-256: 871e172dcd591c3b12a4dae796ef4b5f2c4e1f54e0f27ef3134a9e180f423476.
기존 임시 Excel은 읽기만 하고 수정·복사·배포하지 않았다.

### 2.1 없는 파일 / 실제 존재하는 대체 표

network 아래 CAN_Matrix.xlsx, LIN_Matrix.xlsx, LIN_Schedule.xlsx, vehicle.dbc, vehicle.ldf라는
정확한 이름은 **없음**. 최신5개 ECU 브랜치의 파일 Inventory에도 독립 Matrix는 발견되지 않았다.
그렇다고 실제 CAN/LIN 정의가 전혀 없다는 뜻은 아니다.
S03의 메시지 정의/Signal 상세/통신 규칙과 S02의 CAN/LIN 정의·Schedule, S01/S05의 실제 DB 파일이 있다.
독립 Matrix 대조는 **확인 불가**이며, 위 존재하는 표/DB끼리의 대조 결과를 아래에 기록한다.
과거 Routing 문서가 참조하는 Matrix 내용은 현재 파일이 아니라 그 문서의 과거 주장으로만 인용한다.

### 2.2 최신 ECU 원문과 조회 방식

현재 PC 브랜치의 firmware/vcu_ECU, gateway_ECU, door_ECU, light_ECU, window_ECU에는 .gitkeep만 있다.
다른 브랜치의 로컬 보관 참조도 먼저 git ls-tree/show로 확인했다.
git ls-remote의 실제 HEAD와 캐시가 달랐으므로 오래된 scaffold만 보고 결론 내리지 않았다.
GitHub 공식 GET API의 tree 및 고정 Commit raw 원문을 메모리로 읽었다.
Fetch/Checkout/Switch/참조 갱신/소스 다운로드 파일 생성은 하지 않았다.

| Ref | Branch / 조사 Commit | 실제 파일 / 확인 내용 |
|---|---|---|
| RVCU | VCU_ECU / b49e48611a3ba0013077202f63e97a8603d21bb9 | firmware/vcu_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; HAL_Init/SystemClock_Config와 빈 main loop |
| RGW | Gateway_ECU / 6215ce46e5fcfa1b74f94f39194cd829392755d5 | firmware/gateway_ECU/Core/Src/main.c, Core/Inc/main.h, freertos.c, IRQ/MSP; CAN RX/Decode/Monitor/Status/Fault TX 구현 |
| RDOOR | Door_ECU / 1c287d35d7c15488cf04cb2b9025ea1b3d084d22 | firmware/door_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; GPIO/LED/button 초기화, 빈 main loop |
| RLIGHT | Light_ECU / 7abc743403bc0842a3a97fe1a68d0442e5681826 | firmware/light_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; HAL/clock 초기화, 빈 main loop |
| RWIN | Window_ECU / 1704faec999f79ceae1a56d1d603f4d73127f512 | firmware/window_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; GPIO/LED/button 초기화, 빈 main loop |

RVCU/RDOOR/RLIGHT/RWIN 소스에서 운전자 CAN 입력 처리, LIN command RX/response,
로컬 제어/limit-stop의 실행 구현은 확인하지 못했다. 요구사항상의 책임이 없다는 뜻은 아니다.
루트 main.c 및 루트 헤더도 누락 없이 확인했다. 루트 main.c는 출력 테스트이며 해당 계약이 없다.
실제 빌드·Flash·동작 여부는 **NOT VERIFIED**.

최신5개 브랜치의 Interface blob 65개를 현재 HEAD와 비교했다.
64개는 동일하고 Gateway의 S06만 다른 blob이었다.
Gateway S06 SHA-256은 68a9fdfa352b3b0ffe1ee20c68a10ec4f4cb391b0189efbc0bcb962a00838bbc.
data_only=True에서 Overview/Traceability 캐시 값이 달랐으나
data_only=False로 모든5개 sheet의 실제 수식·리터럴을 대조한 결과 행 차이0개였다.
Requirements/Open_Decisions 내용은 동일하다. 이를 새로운 Timeout 승인이나 정책 변경으로 해석하지 않는다.

고정 원문 링크:
- [VCU_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/b49e48611a3ba0013077202f63e97a8603d21bb9/firmware/vcu_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/b49e48611a3ba0013077202f63e97a8603d21bb9/firmware/vcu_ECU/Core/Inc/main.h)
- [Gateway_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/6215ce46e5fcfa1b74f94f39194cd829392755d5/firmware/gateway_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/6215ce46e5fcfa1b74f94f39194cd829392755d5/firmware/gateway_ECU/Core/Inc/main.h)
- [Door_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1c287d35d7c15488cf04cb2b9025ea1b3d084d22/firmware/door_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1c287d35d7c15488cf04cb2b9025ea1b3d084d22/firmware/door_ECU/Core/Inc/main.h)
- [Light_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/7abc743403bc0842a3a97fe1a68d0442e5681826/firmware/light_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/7abc743403bc0842a3a97fe1a68d0442e5681826/firmware/light_ECU/Core/Inc/main.h)
- [Window_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1704faec999f79ceae1a56d1d603f4d73127f512/firmware/window_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1704faec999f79ceae1a56d1d603f4d73127f512/firmware/window_ECU/Core/Inc/main.h)

## 3. PC 입력 메시지 조사 결과

| 검토 항목 | 실제 확인 결과 | 상태 |
|---|---|---|
| PC_Driver_Input / PC_Body_Input 기존 정의 | S01의6개 Message, S02 CAN_Message_Definition6–11, S03 메시지 정의 CAN행8/12/19/23/27/31에 없음 | 확정(부재 사실); 신설 계약은 Open |
| PC→VCU 수신 주체 | S00 메시지_제안 row2의 VCU 후보; RVCU main.c63–100에 수신 처리 없음 | Open |
| PC Body 수신 주체 | S00 row4의 VCU 또는 Gateway 후보; 공식 수신 Message/handler 없음 | Open |
| STD/EXT | S00 row2는 STD 후보; 기존6개 CAN Message는 S01/S02에서 Standard | 초기값-수정 가능(PC 후보) |
| DLC / Payload | S00 row2 E/G=TBD; 기존 VCU_Command DLC8을 복사하지 않음 | TBD |
| Start/Length / Byte Order / Signed / Factor / Offset / Unit | PC 입력 SG_ 정의 없음. 기존 VCU 출력 Signal 배치를 PC 입력으로 재사용하지 않음 | TBD |
| 송신 주기 / Event 또는 cyclic | PC 항목 없음. Mock Apply는 PC 메모리의 단발 수락이며 CAN 주기가 아님 | Open/TBD |
| 수신 Timeout / Fail-safe / 연결 해제 | PC 연결 종료 계약 없음. VCU_Command30ms와 Gateway50ms는 별도 기존 출력 감시값 | Open/TBD |
| AliveCounter / Payload Checksum | PC 적용 여부·검사·초기값·wrap·오류/복구 정책 미정 | Open; 채택 시 Encoding TBD |
| CAN 자체 CRC / LIN checksum과 관계 | PC Payload Checksum 필요 여부를 기존 LIN Enhanced 정책으로 대체하지 않음 | 검토 필요 |
| PC 입력 수락/실행 확인 응답 | MockReceipt만 존재. 실제 ECU ack/상태 연계 없음 | Open |

**이상 없음**: S09/S10/S11은 현재 메모리 Mock만 처리하고 VCU_Command(0x100)를 대신 송신하지 않는다.
기존 CLI Sender S12는 다른 Raw 기능이며 이번 Driver 입력 계약으로 연결하지 않는다.

## 4. 0x600 후보 충돌 검토

실제 cantools parse와 원문 BO_ 목록을 함께 확인했다.
중복 키는 (Frame Format, CAN ID)로 조사했으며 아래6개 Message의 중복은 **없음 — 이상 없음**.
S02/S03의 CAN Message header와 ID/STD/DLC/주기도 대조했다.

| 기존 Message | ID / Frame | DLC | 기존 송신 주체 | 주기 / 유형 |
|---|---|---|---|---|
| VCU_Command | 0x100 / STD | 8 | VCU | 10ms cyclic |
| Motor_Status | 0x110 / STD | 8 | MOTOR | 10ms cyclic |
| Vehicle_Status | 0x120 / STD | 8 | GATEWAY | 20ms cyclic |
| Body_Status | 0x200 / STD | 8 | GATEWAY | 100ms cyclic |
| Gateway_Status | 0x300 / STD | 8 | GATEWAY | 100ms cyclic |
| Fault_Status | 0x310 / STD | 8 | GATEWAY | Event |

S01에 ID0x600인 STD/EXT Message는 없다.
RGW의 unknown ID는 ProcessCanMessage default에서 UART Raw 표시 대상으로만 처리된다. 이것은 PC 명령 수락/ECU 실행/ack 구현이 아니다.
RGW main.h127–132의6개 CAN ID 상수도 위 목록과 동일하다.
조사한5개 ECU의 application .c/.h에도 PC 후보0x600/1536을 사용하는 CAN 계약은 발견되지 않았다.
**정적 조사 범위에서 기존 정의와의 직접 ID 충돌은 미발견**이다.

그러나 독립 CAN Matrix/예약대장, 다른 노드의 실제 Flash/사용 ID, 전체 버스 실측은 없다.
따라서 **0x600 사용 가능/예약 완료/정식 승인으로 판정하지 않는다**.
상태는 초기값-수정 가능 + 검토 필요, J2-002 담당자 결정 대기다.
과거 임시안 요약row7의 미수행 표기는 변경하지 않았다. 이번 제한된 정적 조사 결과를 이 문서에 별도로 기록한다.
TEST ONLY DBC/Mock Frame은 Production ID 예약 근거에서 제외했고 Fixture를 수정하지 않았다.

## 5. Accelerator / Brake / Gear 계약

| 항목 | Handbook / 임시안 | 실제 기존 CAN / PC 모델 | PC Production 계약 |
|---|---|---|---|
| Accelerator | S07§9.1 p25, S00 신호_제안2: 0..100% 입력 모델 | S09 모델0..100, finite 검증. S01에는 Accelerator Signal 없음 | Unit/범위/Encoding/유효성 TBD |
| Brake | S07 bool 또는 pressure mock; S00 row3 ON/OFF 우선 | S09 bool; 기존 VCU_Command.Brake는 start19/len1/Intel/0·1 | bool/pressure 선택과 단위/Invalid/동시 입력 정책 Open |
| Gear | S00 row4 P/N/D/R | S01 Value Table0=P,1=N,2=D,3=R; S09는 이름만 저장, 숫자 인코딩 없음 | PC Gear enum/상태 전이/금지 전이 Open |
| 동시 입력 | S07 VCU가 Brake 시 Torque 제한/0 예시 | S09는 Accelerator+Brake를 둘 다 보관하고 제어 판단하지 않음 | VCU 담당 승인 필요 |

S02의24개 CAN Signal에서 start/length/order/signed/factor/offset/min/max/unit/invalid를 실제 DBC와 비교했다.
차이6개는 VCU/Vehicle Gear의Max2개, VCU/Vehicle Brake의Invalid2개, VCU Alive/GatewayAlive의Invalid2개다.
독립 Matrix가 없어 Matrix 원본과의 비교로 부르지 않는다.

기존 출력 비교:
- TorqueRequest: S02 CAN_Signal_Definition6와 S01은 start0/len16, Intel unsigned, factor0.1/offset0, Nm, 0..4000.
  RGW DecodeVcuCommand828–869의 ReadLe16 및 /10 출력과 배치·표시 배율은 **이상 없음**.
  Gateway의 Decode/표시를 VCU의 Accelerator→Torque 계산 구현으로 오인하지 않는다.
- Gear: S02 row7 Max5 및 S03 Signal 상세8/17은 S01의 정상 Max3, Value_Table6–11의 Reserved4..6,
  RGW main.c684–699/845–847의 정상0..3과 다르다. J2-013.
- Brake: S02 row8/S03 Signal 상세9의 Invalid1은 정상TRUE1과 충돌한다.
  S01 CM_의 Invalid N/A 및 Routing Required_Interface_Changes6(DEC-03)와 다르다. J2-014.
- AliveCounter: S02 row9/S03 Signal 상세10의 Invalid0xF는 정상 wrap0..15와 겹친다.
  S01 CM_에는 Invalid N/A, RGW MonitorAliveCounter544 및 Gateway TX445는 15→0 wrap이다.
  GatewayAlive에도 같은 Invalid0xF/정상15 문제를 대조했다. J2-015.
- PC 모델의 입력 정책을 위 출력 Signal의 최종 수정 결정으로 사용하지 않는다.

## 6. Window / Door / Light 경로 비교

PC 수신 경로 후보는 두 가지로 **Open**이다.
A: PC 입력 → VCU 수신/권한·명령 생성 → Gateway → 각 LIN ECU.
B: PC Body 입력 → Gateway 직수신/권한·명령 생성 → 각 LIN ECU.
S00 메시지_제안4가 두 후보를 남겨두고 있으며 S04의 VCU 출력 기준안만으로 PC 진입점을 승인할 수 없다.
어느 경로도 이번에 구현/선택/송신하지 않았다.

다음 값은 기존 산출물에 적힌 정의를 인용한 것이며 새 PC 요청 배치가 아니다.
LIN Frame ID와 Protected PID를 동일한 숫자라고 확정하지 않는다.

| 기능 | 기존 정의와 Routing 후보 | 지속·초기값·Timeout / 실제 코드 | 상태 |
|---|---|---|---|
| Window Open/Close | S00 신호_제안7은 Gateway→LIN Door ECU. S02 LIN_Frame_Definition10/S05 lines94–104는 Window ECU. LIN WindowCommand는 start0/len2; STOP0/UP1/DOWN2/INVALID3 (S02 LIN_Signal_Definition19/Value Table, S05 222–227). C2L-007은 VCU_Command.WindowCommand Byte3 후보 → Window_Command | S02:1B/100ms/slot10ms/초기STOP. S06 SYS_REQ_045/059는 Window local limit-stop/command freshness 책임. 수치 Local Timeout은 하위 SW에 위임, 실제 코드 없음. OPEN/CLOSE의 UP/DOWN 방향·지속/원샷·재개·로컬 우선순위 미정 | 검토 필요 + Open/TBD |
| Door Lock/Unlock | S02 LIN_Frame_Definition7/S05 77–80: Door_Command→Door ECU. LockCommand start0/len2: NO_ACTION0/LOCK1/UNLOCK2/INVALID3. RequestState start2/len1은 별도 상태 요청. C2L-006의 VCU_Command.DoorLockRequest는 Byte3 후보 | S02:1B/100ms/slot60ms/초기NO_ACTION. Routing DEC-07은 RequestState0 유지 후보. 반복 command가 actuator를 지속 구동하는지, 원샷/중복 억제/완료응답 계약 없음. RDOOR는 command 처리 없음. PC Phase3J-1에도 Door 입력 없음 | Open |
| Light ON/OFF | S02 LIN_Frame_Definition8/S05 81–87: Light ECU. HeadLamp(bit0), TurnLamp(bits1–2), Hazard(bit3), Reverse(bit4), Brake(bit5)로 각각 구분. C2L-003~005의 Head/Turn/Hazard 요청은 Byte3 후보. Gear/Brake 연동 C2L-001/002는 별도 경로 | S02:1B/50ms/slot20·70ms, 기존 lamp 초기0. Mock Light ON을 HeadLamp/전체Lamp/bitmask 중 어느 것으로 해석할지 미정. DEC-08 Hazard 우선은 설계 후보, RLIGHT 실행 코드 없음 | Open + 검토 필요 |

Window와 Door는 별도 기능/ECU다. Light도 하나의 Generic bool로 승인된 것처럼 묶지 않는다.
Door/Window/Lamp invalid/stale fallback은 S04 DEC-04의 **PENDING REVIEW 기준안 인용**이다.
현재 코드의 안전 동작 또는 PC 연결 해제 시 동작으로 주장하지 않는다.

## 7. TorqueRequest 송신 책임

운전자 Accelerator/Brake/Gear → VCU 해석·상태 전이·토크 계산/제한 →
VCU_Command(VCU 송신) → Motor_Status(실제 Motor 또는 Virtual Motor 관측 결과)라는 책임 구분을 유지한다.
S02 CAN_Message_Definition6–7 및 S06 SYS_REQ_003/004가 근거다.

**이상 없음**: S01의 VCU_Command sender=VCU이며 PC S09/S10은 송신 프레임을 생성하지 않는다.
S11의 TorqueRequest는 읽기 전용 관측 안내이고 사용자 직접 제어 항목이 아니다.
RVCU main.c63–100/143–145는 빈 application loop/user section이라 실제 토크 계산/제한은 **확인되지 않음**.
RGW DecodeVcuCommand는 토크 raw 값을 해석·UART 표시할 뿐 입력→토크 계산·Motor 제어를 구현하지 않는다.
PC가 기존 VCU_Command0x100을 직접 송신하는 방식은 기본안에서 제외한다.

## 8. Gateway·LIN Routing 정합성

### 8.1 최신 Gateway에서 확인한 구현

- main.c128–144: CAN RX all-mask filter; 165 queue 생성; 173–183 CAN start/notification.
- main.h127–134 및 main.c1107–1140: 기존6개 ID의 CAN 분류와 Decode, unknown은 UART Raw 표시.
  ID/DLC/기존 VCU payload 배치는 **이상 없음**(Format 구분 문제는 J2-017).
- main.c828–869: Torque/Gear/Brake/Alive만 읽으며 Byte3의 신규 Body request를 읽지 않는다.
- main.c434–464: Gateway_Status0x300, Fault_Status0x310의 Standard 송신 구현.
  Gateway/Body 상태 CAN 송신이 모두 완료된 것으로 확대하지 않는다.
- main.c1193–1243: CAN queue 처리/timeout 검사/status TX의 defaultTask.
  main.c311–329의 USART2는 UART 로그115200 설정이다. 이 코드에서 LIN master command/schedule 실행은 확인되지 않는다.
  UART가 존재한다는 사실을 LIN Master 구현으로 대체하지 않는다.
- Source parser 없음과 실제 Hardware 미검증은 구분한다. 본 단계는 Firmware 빌드/동작 시험이 아니다.

### 8.2 Byte3 변경 후보와 현행 DBC

S04 Decision_Baseline DEC-01/02 및 Required_Interface_Changes7–11은
기존 VCU_Command Reserved Byte3에 HeadLampRequest, TurnLampRequest, HazardLampRequest,
DoorLockRequest, WindowCommand를 추가하는 **PENDING REVIEW** 제안이다.
S02 CAN_Message_Definition15는 Byte3 Reserved, S01 VCU_Command의4개 SG_에는 이5개 필드가 없고
RGW main.h48–54 및 DecodeVcuCommand840–843에도 없다.
따라서 후보 Routing을 현재 Encode/Decode 가능한 기능으로 표시할 수 없다. J2-010.
PC는 이 Byte3를 대신 송신하지 않는다.

### 8.3 Schedule·checksum·PID

S02 LIN_Frame_Definition15–24/S03 통신 규칙19–29와 S05 BODY_10ms162–170은 다음 설계 시점에서 일치한다:
0 Door_Status, 10 Window_Command, 20 Light_Command, 30 Window_Status,
40 Light_Status, 60 Door_Command, 70 Light_Command, 100ms 반복.
LDF의20/30ms delay가 Idle 구간을 흡수하므로 설계상7개 Frame entry와 표의10 slot은 **이상 없음**.
위 숫자는 기존 Schedule 인용이며 실측 PASS가 아니다.

S05 BASE_20ms175–180은 reference-only이고 Window가 없으며 Light_Command가100ms마다1회다.
S04 Interface_Ref51/57–62는 Window TBD/BASE-20ms를 여전히 표기한다.
현재 BODY_10ms 기준과 과거 Reference 행의 우선순위를 명시해 동기화해야 한다. J2-011.
S05의 pre-firmware APPROVED 표기와 S04의 공식Freeze Pending은 승인 범위가 다르므로 자동 해소하지 않는다.

S02의 Identifier 열은 PID라는 제목이고 S05는 frame_id로 해석하여 보존한다.
Protected PID는 S04 DEC-06/S05 주석69–70 및 설명서의 Capture 대상이며 **측정 후 확정**이다.
기존 Enhanced checksum 정책은 S02의 선언/S05 주석183–185에 있으나 실기 검증은 **NOT VERIFIED**다.
독립 LIN Matrix/Schedule 파일 부재와 LIN Firmware 미구현 때문에 전체 Frame/Slave 호환성 승인은 남아 있다.

### 8.4 기존 Fault/Format 불일치

이는 PC 입력용 새로운 정책을 정한 것이 아니라 기존 코드와 문서의 차이를 기록한 것이다.
- S02 POL-0016/POL-00712: VCU age>30ms, FAIL_SAFE, 정상 확인3회.
  RGW main.h135/146과 main.c644/648–651/524–538/567–601:
  monitor>=50ms, DEGRADED, 첫 정상/연속 Alive 회복에서 CLEARED 호출. J2-016.
  이50ms를 PC 입력 Timeout으로 복사하지 않는다.
- RGW main.h41–46의 CanRxMessage_t에 IDE/RTR이 없다.
  RX callback1158–1167은 StdId/ExtId를 같은 id에 넣고 IDE/RTR을 버리며,
  all-mask filter와 ProcessCanMessage의 숫자 ID switch가 같은 수치의 EXT/RTR을 구분할 근거를 잃는다.
  현재 DBC STD 계약과의 불일치다. J2-017. 실기 재현은 NOT RUN이다.


## 9. Interface Open Items

심각도는 이번 Interface 리뷰의 우선순위다. High의 부재/미결정 항목은 현재 Mock 소프트웨어 결함이라는 뜻이 아니라 Production Freeze/구현의 차단 조건이다.
담당자는 역할 기준이며 실제 승인자 이름·승인 증적은 추정하지 않았다. Jira 후보 키는 본 문서 내부 식별자이며 외부 등록하지 않았다.

| Issue | 심각도 | Interface | 현재 상태 | Jira 후보 |
|---|---|---|---|---|
| [J2-001](#j2-001) | High（Freeze blocker） | 기준 산출물 / 승인 범위 | 검토 필요 | J2-T01 |
| [J2-002](#j2-002) | High（Freeze blocker） | PC_Driver_Input 후보 ID0x600 | 초기값-수정 가능 | J2-T01 |
| [J2-003](#j2-003) | High（Freeze blocker） | Accelerator/Brake/Gear Payload | TBD | J2-T02 |
| [J2-004](#j2-004) | High（Freeze blocker） | PC 주기/Timeout/Alive/Checksum/연결 종료 | Open | J2-T03 |
| [J2-005](#j2-005) | High（구현/계약 누락） | VCU 입력 해석·TorqueRequest 계산 | Open | J2-T02 / J2-T03 |
| [J2-006](#j2-006) | High（Freeze blocker） | PC Body 수신 주체 / 경로 | Open | J2-T04 |
| [J2-007](#j2-007) | High（문서 충돌） | Window 대상 / OPEN·CLOSE 의미 / 로컬 제어 | 검토 필요 | J2-T04 / J2-T06-WINDOW |
| [J2-008](#j2-008) | High（계약 누락） | Door Lock/Unlock 실행 | Open | J2-T04 / J2-T06-DOOR |
| [J2-009](#j2-009) | High（의미 미결정） | Light ON/OFF 범위 | Open | J2-T04 / J2-T06-LIGHT |
| [J2-010](#j2-010) | High（실제 정의 부재） | VCU_Command Byte3 Body request 후보 | 검토 필요 | J2-T04 |
| [J2-011](#j2-011) | Medium（기준/표기 정합성） | LIN Schedule / Frame ID·PID / 승인 범위 | 검토 필요 | J2-T09 |
| [J2-012](#j2-012) | High（구현 누락） | Gateway LIN Master / Body Slave 처리 | Open | J2-T06-MASTER / DOOR / WINDOW / LIGHT |
| [J2-013](#j2-013) | Medium（기존 CAN 정의 충돌） | VCU/Vehicle Gear 정상 범위 | 검토 필요 | J2-T05 |
| [J2-014](#j2-014) | High（기존 CAN 정의 충돌） | Brake TRUE / Invalid | 검토 필요 | J2-T05 |
| [J2-015](#j2-015) | Medium（기존 CAN 정의 충돌） | VCU AliveCounter / GatewayAlive Invalid | 검토 필요 | J2-T05 |
| [J2-016](#j2-016) | High（코드·기존 정책 충돌） | Gateway VCU Timeout / State / Recovery | 검토 필요 | J2-T07 |
| [J2-017](#j2-017) | High（Source Format 계약 불일치） | Gateway STD/EXT/RTR 수신 식별 | 검토 필요 | J2-T08 |
| [J2-018](#j2-018) | High（Production 정책 누락） | 입력 권한 / 충돌 / ECU 응답 확인 | Open | J2-T03 / J2-T04 |
| [J2-019](#j2-019) | Low（기존 설명 표기 차이） | LIN Door RequestState bit length | 검토 필요 | J2-T09 |

### J2-001

| 항목 | 내용 |
|---|---|
| 심각도 | High（Freeze blocker） |
| 관련 Interface | 기준 산출물 / 승인 범위 |
| 문서 A의 정의 | S08 §5, S07 §5.5: 승인·동기화된 Matrix/DBC 관리 요구. |
| 문서 B의 정의 | 독립 Matrix 없음. S02 row2/22와 S03 통신 규칙13은 02/05 FIX 우선; S04는 공식Freeze Pending, S05는 pre-firmware 승인 표기. |
| 실제 코드 동작 | PC는 Mock만 처리. 최신5개 ECU Inventory/Interface blob 대조로 별도 Matrix 미발견. |
| 충돌 또는 누락 | 기준 문서의 우선순위와 승인 범위/버전 증적이 하나로 연결되지 않음. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | CAN/LIN 정의, ECU, PC/Test 전원 |
| 결정이 필요한 항목 | 사용할 Baseline 버전/기준 권한, 독립 Matrix 존재·제공 또는 대체 표의 공식 승인 범위. |
| 담당자 | 시스템 / CAN·LIN 기준 산출물 담당 |
| 리뷰 필요 담당자 | VCU, Gateway, Motor, Cluster, Door, Light, Window, PC/Test |
| Jira Task 제안 | J2-T01 |
| 완료 기준 | 기준 파일/Commit·승인 담당자/날짜/범위/Evidence를 기록하고 불일치 처리 절차 합의. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-002

| 항목 | 내용 |
|---|---|
| 심각도 | High（Freeze blocker） |
| 관련 Interface | PC_Driver_Input 후보 ID0x600 |
| 문서 A의 정의 | S00 요약6–7/메시지_제안2: 초기값-수정 가능, 충돌 검사·리뷰 전 TX 금지. |
| 문서 B의 정의 | S01/S02/S03 기존6개 STD ID에0x600 없음. 예약대장/독립CAN Matrix 없음. |
| 실제 코드 동작 | RGW main.h127–132도 같은6개 ID. 조사된5개 ECU source에는 PC0x600 handler 없음. PC Frame 생성 없음. |
| 충돌 또는 누락 | 정적 중복은 미발견이나 사용/예약 및 전체 실제 노드 충돌 없음이 보장되지 않음. |
| 현재 상태 | 초기값-수정 가능 |
| 영향 범위 | PC, VCU, Gateway 및 CAN 전체 노드 |
| 결정이 필요한 항목 | 정식 PC ID/Frame Format 사용·예약 승인, 전체 ID registry 범위. |
| 담당자 | CAN Interface / VCU / PC |
| 리뷰 필요 담당자 | Gateway, Motor, Cluster, 시스템 |
| Jira Task 제안 | J2-T01 |
| 완료 기준 | 전체 ID/예약 대장과 STD·EXT 키 조사 증거, 담당자 승인. 후보 ID를 확정값으로 사용하지 않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-003

| 항목 | 내용 |
|---|---|
| 심각도 | High（Freeze blocker） |
| 관련 Interface | Accelerator/Brake/Gear Payload |
| 문서 A의 정의 | S00 신호_제안2–4: 이름 후보와 입력 모델만 제안, bit/length/factor TBD. |
| 문서 B의 정의 | S01에는 해당 PC 입력 Message/SG_ 없음. S02의 Torque/Gear/Brake는 VCU 출력이며 PC 입력이 아님. |
| 실제 코드 동작 | S09 DriverInputs/validated37–52는 PC 메모리 정책; RVCU main63–100 수신/입력처리 없음. |
| 충돌 또는 누락 | PC Message DLC 및 신호의 위치·길이·byte order·signed·scale·offset·unit·initial/invalid 계약 부재. |
| 현재 상태 | TBD |
| 영향 범위 | PC, VCU, CAN, Motor/Gateway 영향 |
| 결정이 필요한 항목 | Accelerator 모델/단위·Brake bool 또는 pressure·Gear 의미/전이, Encoding/validation 항목 전부. |
| 담당자 | VCU / CAN / PC |
| 리뷰 필요 담당자 | Motor, Gateway, 시스템 |
| Jira Task 제안 | J2-T02 |
| 완료 기준 | 승인된 계약 표와 동기화된 DBC/기준 산출물, 정상/잘못된 입력 비교 기준. 여기서 임의 배치하지 않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-004

| 항목 | 내용 |
|---|---|
| 심각도 | High（Freeze blocker） |
| 관련 Interface | PC 주기/Timeout/Alive/Checksum/연결 종료 |
| 문서 A의 정의 | S00 메시지_제안2 F열 TBD, 결정_이슈IF-03 Open. |
| 문서 B의 정의 | S02 POL-001의30ms는 기존 VCU 출력 감시, POL-009의Window Local Timeout 수치는 하위SW 위임. PC 계약 없음. |
| 실제 코드 동작 | S09 Apply는 수동 메모리 처리; sequence57은 PC 이력 번호. S09 close는 메모리 reset일 뿐. VCU handler 없음. |
| 충돌 또는 누락 | PC 입력 lost/stale/중복/순서/신뢰성/재연결과 안전 처리 정의 없음. |
| 현재 상태 | Open |
| 영향 범위 | PC, VCU, Gateway, Motor 및 Body |
| 결정이 필요한 항목 | Cyclic/Event 여부, Timeout·연결 끊김 동작, Alive/Payload Checksum 필요성, 오류/복구/재입력 정책. |
| 담당자 | VCU / 시스템 안전 정책 / PC |
| 리뷰 필요 담당자 | Gateway, CAN, Motor, affected Body ECU |
| Jira Task 제안 | J2-T03 |
| 완료 기준 | 합의된 정책/검증 시나리오와 담당자 승인. 기존30/50ms·LIN checksum을 PC 정책으로 복사하지 않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-005

| 항목 | 내용 |
|---|---|
| 심각도 | High（구현/계약 누락） |
| 관련 Interface | VCU 입력 해석·TorqueRequest 계산 |
| 문서 A의 정의 | S07§9.1, S06 Requirements8 SYS_REQ_003: VCU 운전자 입력 기반 제어/토크 요청. |
| 문서 B의 정의 | S02 CAN_Message_Definition6 및 S01 sender=VCU, TorqueRequest는 출력. |
| 실제 코드 동작 | RVCU main.c63–100/143–145 HAL/clock 및 빈loop. main.h/IRQ/MSP에서도 입력처리 없음. RGW828–869는 Decode/UART 표시. |
| 충돌 또는 누락 | 현재 확인한 VCU 원문에 입력 RX, state/torque 계산·제한 또는 출력 TX가 구현되지 않음. |
| 현재 상태 | Open |
| 영향 범위 | VCU, Motor, PC, Gateway |
| 결정이 필요한 항목 | 실제 VCU 구현 위치/대상 버전, 입력 처리 계약과 계산/제한/상태 전이 책임. |
| 담당자 | VCU |
| 리뷰 필요 담당자 | Motor, Gateway, PC/Test |
| Jira Task 제안 | J2-T02 / J2-T03 |
| 완료 기준 | 승인 계약과 실제 구현 경로·Commit·SW 테스트 증거. PC가 VCU 출력 송신을 대신하지 않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-006

| 항목 | 내용 |
|---|---|
| 심각도 | High（Freeze blocker） |
| 관련 Interface | PC Body 수신 주체 / 경로 |
| 문서 A의 정의 | S00 메시지_제안4: PC→Gateway 또는 VCU, 미정. |
| 문서 B의 정의 | S04 DEC-01: VCU가Body command 생성 후보, PC 수신 Message/경로 정의는 없음. |
| 실제 코드 동작 | RGW ProcessCanMessage1107–1140는 기존6개ID Decode만 수행, PC Body handler 없음. RVCU 수신 없음. |
| 충돌 또는 누락 | VCU 경유와 Gateway 직접 수신 중 소유권·권한·명령 생성 책임 미선택. |
| 현재 상태 | Open |
| 영향 범위 | PC, VCU, Gateway, Door/Light/Window |
| 결정이 필요한 항목 | A/B 경로와 명령 해석/우선순위/권한·응답 책임; 필요 PC Body 계약. |
| 담당자 | 시스템 / VCU / Gateway |
| 리뷰 필요 담당자 | CAN·LIN, Door, Light, Window, PC |
| Jira Task 제안 | J2-T04 |
| 완료 기준 | 3개 Body 기능별 수신 주체와 책임 경로 승인, 관련 Message/Routing 변경 계획. VCU0x100 PC 대체 송신 제외. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-007

| 항목 | 내용 |
|---|---|
| 심각도 | High（문서 충돌） |
| 관련 Interface | Window 대상 / OPEN·CLOSE 의미 / 로컬 제어 |
| 문서 A의 정의 | S00 신호_제안7: Window 처리 목적지 Gateway→LIN Door ECU, OPEN/CLOSE/STOP 후보. |
| 문서 B의 정의 | S02 LIN_Frame_Definition10/LIN_Signal_Definition19, S05 frames94–104/encoding222–227, S06 SYS_REQ_044/045/059: 별도 Window ECU, STOP/UP/DOWN 및 local safety. |
| 실제 코드 동작 | RWIN main.c65–110 및user section은 빈loop, command/limit-stop 처리 없음. PC는 OPEN/CLOSE 문자열만 Mock에 보관. |
| 충돌 또는 누락 | 대상 ECU 충돌. OPEN/CLOSE→UP/DOWN 방향과 원격/물리 스위치/limit 우선순위·Local Timeout 파라미터 미정. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | Window, Gateway, VCU, PC, Door 문서 |
| 결정이 필요한 항목 | 목적지 정정 승인, 명령 의미/지속·STOP·로컬 우선순위/정량Local Timeout의 하위 요구사항. |
| 담당자 | Window / Gateway / 임시안 작성 담당 |
| 리뷰 필요 담당자 | VCU, Door, LIN Common, PC/Test |
| Jira Task 제안 | J2-T04 / J2-T06-WINDOW |
| 완료 기준 | Window 경로/의미·local safety 승인, 관련 문서 동기화 및 독립 SW/추후실기 증거. Door 기능으로 합치지 않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-008

| 항목 | 내용 |
|---|---|
| 심각도 | High（계약 누락） |
| 관련 Interface | Door Lock/Unlock 실행 |
| 문서 A의 정의 | S02 LIN_Signal_Definition9–10, S05 LockCommand/RequestState: 잠금 요청과 상태 요청 별개. |
| 문서 B의 정의 | S04 DEC-07/C2L-006: LockCommand만 후보 매핑, RequestState0 유지; 지속/원샷 정의 없음. |
| 실제 코드 동작 | RDOOR main.c65–110 초기화/빈loop, LIN handler 없음. PC Phase3J-1 DriverInputs31–35에 Door 없음. |
| 충돌 또는 누락 | CAN 발생원·실제 command 처리·중복 요청/구동 종료/완료응답 정책 부재. |
| 현재 상태 | Open |
| 영향 범위 | Door, Gateway, VCU, PC |
| 결정이 필요한 항목 | 잠금 요청 유지/원샷·중복 억제·액추에이터 완료/상태·초기화/timeout 의미. |
| 담당자 | Door / Gateway |
| 리뷰 필요 담당자 | VCU, LIN Common, PC/Test |
| Jira Task 제안 | J2-T04 / J2-T06-DOOR |
| 완료 기준 | Door 전용 실행/응답 계약과 검증 시나리오 승인. Window/Light와 기능 혼합 금지. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-009

| 항목 | 내용 |
|---|---|
| 심각도 | High（의미 미결정） |
| 관련 Interface | Light ON/OFF 범위 |
| 문서 A의 정의 | S00 신호_제안8/S09 LIGHT_CHOICES13: Generic ON/OFF 후보. |
| 문서 B의 정의 | S02 LIN_Frame_Definition8/LIN_Signal_Definition11–15, S05 81–87: Head/Turn/Hazard/Reverse/Brake 독립; S04 DEC-08 priority후보. |
| 실제 코드 동작 | RLIGHT main63–100 빈loop; S09는단순Mock 의도, bitmask/개별Lamp mapping 없음. |
| 충돌 또는 누락 | ON/OFF가 가리키는 lamp 집합·기존Gear/Brake 연동·Hazard/Turn 우선순위의 승인/실행 없음. |
| 현재 상태 | Open |
| 영향 범위 | Light, Gateway, VCU, PC |
| 결정이 필요한 항목 | Generic ON/OFF의 지원 범위, 각Lamp request, 자동연동과사용자입력충돌/출력우선순위. |
| 담당자 | Light / Gateway / VCU |
| 리뷰 필요 담당자 | LIN Common, PC/Test, 시스템 |
| Jira Task 제안 | J2-T04 / J2-T06-LIGHT |
| 완료 기준 | Light 기능별 의미/권한/priority/초기·stale 정책 승인. Genericbool을전체Lamp 또는HeadLamp로 임의 대응하지 않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-010

| 항목 | 내용 |
|---|---|
| 심각도 | High（실제 정의 부재） |
| 관련 Interface | VCU_Command Byte3 Body request 후보 |
| 문서 A의 정의 | S04 DEC-01/02, Required_Interface_Changes7–11: 신규5개Byte3 필드, PENDING REVIEW. |
| 문서 B의 정의 | S02 CAN_Message_Definition15: Reserved; S01 VCU_Command SG_4개뿐. |
| 실제 코드 동작 | RGW main.h48–54/DecodeVcuCommand840–843도Torque/Gear/Brake/Alive만해석. 신규Body필드없음. |
| 충돌 또는 누락 | Routing Source 후보가 실제 CAN Message/Encoder/Decoder에 없음. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | VCU, Gateway, CAN, Door/Light/Window, PC/Test |
| 결정이 필요한 항목 | 후보채택/대안, 필요한 정식Interface Change와모든산출물 동기화. |
| 담당자 | VCU / Gateway / CAN |
| 리뷰 필요 담당자 | Door, Light, Window, PC/Test |
| Jira Task 제안 | J2-T04 |
| 완료 기준 | 승인된Source필드와일치하는표/DBC/Routing/코드·Evidence. Reserved를임의사용하지않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-011

| 항목 | 내용 |
|---|---|
| 심각도 | Medium（기준/표기 정합성） |
| 관련 Interface | LIN Schedule / Frame ID·PID / 승인 범위 |
| 문서 A의 정의 | S02 LIN_Frame_Definition15–24, S03 통신 규칙19–29, S05 BODY_10ms162–170은 일치. |
| 문서 B의 정의 | S04 Interface_Ref51/57–62는WindowTBD/BASE-20ms; DEC-05/06은Pending; S05는pre-firmware승인이라고표기. |
| 실제 코드 동작 | RGW defaultTask1193–1243에LINschedule없음. Frame/Protected PID실측없음. |
| 충돌 또는 누락 | 낡은Reference/현재운용설계/검증대상 구분 및최종동기화·승인 증적이남음. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | Gateway, LIN Common, Door/Light/Window, PC/Test |
| 결정이 필요한 항목 | 운용vs참고의문서범위, 독립Matrix 제공/동기화, Protected PID/Checksum확인방법. |
| 담당자 | Gateway / LIN Common / 기준 산출물 담당 |
| 리뷰 필요 담당자 | Door, Light, Window, PC/Test |
| Jira Task 제안 | J2-T09 |
| 완료 기준 | Schedule대조·Reference표기정리/동기화및담당자승인. timing/PID/Checksum은HW별도측정, 현재PASS주장금지. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-012

| 항목 | 내용 |
|---|---|
| 심각도 | High（구현 누락） |
| 관련 Interface | Gateway LIN Master / Body Slave 처리 |
| 문서 A의 정의 | S02 LIN정의/S05 Nodes22–28·Frames68–105·Schedule/S04routes가Master-Slave경로요구. |
| 문서 B의 정의 | S06 SYS_REQ_002/005/006/044/045/059가Routing·Body/local출력책임정의. |
| 실제 코드 동작 | RGW CANDecode와UART로그만 확인; LINbreak/header/command/schedule/response처리없음. RDOOR/RWIN/RLIGHT도초기화/빈loop. |
| 충돌 또는 누락 | 문서의LIN제어/피드백/안전경로를현재검토소스로실행가능하다고판정할근거가없음. |
| 현재 상태 | Open |
| 영향 범위 | Gateway, Door/Light/Window, VCU, PC/Test |
| 결정이 필요한 항목 | 실제구현계획·정식소스위치/버전·Master/각Slave범위/검증책임. |
| 담당자 | Gateway / 각 Body ECU |
| 리뷰 필요 담당자 | LIN Common, VCU, PC/Test |
| Jira Task 제안 | J2-T06-MASTER / DOOR / WINDOW / LIGHT |
| 완료 기준 | Interface승인후각소스구현·SW테스트·추후Bus/출력증거. 현재통합/HW완료로판정하지않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-013

| 항목 | 내용 |
|---|---|
| 심각도 | Medium（기존 CAN 정의 충돌） |
| 관련 Interface | VCU/Vehicle Gear 정상 범위 |
| 문서 A의 정의 | S02 CAN_Signal_Definition7/16 및 S03 Signal 상세8/17: Max5. |
| 문서 B의 정의 | S01 GearMax3/VAL_0..3정상,4..6RESERVED,7INVALID; S02 Value_Table6–11도같은enum. |
| 실제 코드 동작 | RGW DbcGearName684–699 및DecodeVcuCommand845–847/DecodeVehicleStatus934–939:0..3정상. |
| 충돌 또는 누락 | 표의physicalMax와enum/DBC/코드정상범위불일치. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | VCU, Gateway, Motor, Cluster, PC/Test |
| 결정이 필요한 항목 | 정상범위/Reserved/Invalid표현및관련산출물권한; PC입력enum으로복제금지. |
| 담당자 | CAN / VCU |
| 리뷰 필요 담당자 | Gateway, Motor, Cluster, PC/Test |
| Jira Task 제안 | J2-T05 |
| 완료 기준 | 승인된범위및표·DBC·모든consumer검증기준일치. 여기서Max수정하지않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-014

| 항목 | 내용 |
|---|---|
| 심각도 | High（기존 CAN 정의 충돌） |
| 관련 Interface | Brake TRUE / Invalid |
| 문서 A의 정의 | S02 CAN_Signal_Definition8/17 및 S03 Signal 상세9/18: Brake 정상1이면서 Invalid1. |
| 문서 B의 정의 | S01 CM_ SG_256Brake는Invalid N/A; S04 Required_Interface_Changes6/DEC-03도N/A후보. |
| 실제 코드 동작 | RGW DecodeVcuCommand842/864는bit1을ON으로표시하며signalInvalid1판정없음. |
| 충돌 또는 누락 | 같은1bit값에정상ON과Invalid를동시에정의. PCBrakeInput계약은또별도미정. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | VCU, Motor, Gateway, Cluster, PC/Test |
| 결정이 필요한 항목 | 기존BrakeInvalid정책승인·동기화와PCBrake계약의독립범위. |
| 담당자 | CAN / VCU / Gateway |
| 리뷰 필요 담당자 | Motor, Cluster, PC/Test |
| Jira Task 제안 | J2-T05 |
| 완료 기준 | 정상TRUE/메시지validity/invalid구분과표·DBC·테스트일치. 기존정상ON거부로해결하지않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-015

| 항목 | 내용 |
|---|---|
| 심각도 | Medium（기존 CAN 정의 충돌） |
| 관련 Interface | VCU AliveCounter / GatewayAlive Invalid |
| 문서 A의 정의 | S02 CAN_Signal_Definition9/24 및 S03 Signal 상세10/25: Invalid0xF. |
| 문서 B의 정의 | S01의CM_는정상0..15wrap과Invalid미지정. S03 통신 규칙15도0..15. |
| 실제 코드 동작 | RGW main.c544 기대counter modulo16,445gatewayAlivewrap;15를정상순환값으로사용. |
| 충돌 또는 누락 | 정상counter15와Invalid0xF가겹침. PC내부sequence는CANAlive와무관. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | VCU, Gateway, CAN consumer, PC/Test |
| 결정이 필요한 항목 | counter범위·Invalid유무·age/continuity분리및승인; PCcounter필요성은별도. |
| 담당자 | CAN / Gateway / VCU |
| 리뷰 필요 담당자 | Motor, Cluster, PC/Test |
| Jira Task 제안 | J2-T05 |
| 완료 기준 | 15→0정상회귀와invalid정책이일관된기준/DBC/consumer증거. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-016

| 항목 | 내용 |
|---|---|
| 심각도 | High（코드·기존 정책 충돌） |
| 관련 Interface | Gateway VCU Timeout / State / Recovery |
| 문서 A의 정의 | S02 POL-0016/POL-00712/POL-0038:age>30ms,VCUCriticalFAIL_SAFE,정상3회;S06 SYS_REQ_020/053/055. |
| 문서 B의 정의 | S01 VCU_CommandCM_도age>30ms. 최신Gatewayheader135/146는50ms/DEGRADED. |
| 실제 코드 동작 | RGW CheckCanSourceTimeout644–651는>=50ms/DEGRADED; MonitorAliveCounter524–538/567–601는첫회복에서CLEARED. |
| 충돌 또는 누락 | 현재Firmware의Threshold·대표State·Recovery확인횟수가기존문서와다름. Runtime/HW재현은미수행. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | Gateway, VCU, Motor, Cluster/PCFault표시 |
| 결정이 필요한 항목 | 적용할승인Fault정책/예외버전과같은기준의기존출력감시. PC입력Timeout으로사용금지. |
| 담당자 | Gateway / Fault 정책 담당 |
| 리뷰 필요 담당자 | VCU, Motor, Cluster, PC/Test |
| Jira Task 제안 | J2-T07 |
| 완료 기준 | 기준정책합의및코드/문서일치,경계·criticalstate·연속recovery테스트와전파증거. 승인전수치수정금지. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-017

| 항목 | 내용 |
|---|---|
| 심각도 | High（Source Format 계약 불일치） |
| 관련 Interface | Gateway STD/EXT/RTR 수신 식별 |
| 문서 A의 정의 | S01/S02기존6개Message는STD. CAN ID는Format과같이식별해야함. |
| 문서 B의 정의 | RGW main.hCanRxMessage_t41–46에는숫자id/dlc/data만있음. |
| 실제 코드 동작 | RGWfilter128–144all-mask;RXcallback1158–1167는STD/EXT를같은id로축약하고RTR도버림;ProcessCanMessage1116–1138는숫자switch. |
| 충돌 또는 누락 | 같은숫자EXT/RTR의기존STD데이터메시지분류를막는metadata/guard가해당경로에없음. 정적확인,실기재현NOT RUN. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | Gateway, CAN consumer정합성, PC/VCU통합시험 |
| 결정이 필요한 항목 | 허용Format/FrameType검증위치·보존방식·테스트기준. 일반CanRxMessagepublic변경은담당자승인대상. |
| 담당자 | Gateway / CAN |
| 리뷰 필요 담당자 | VCU, PC/Test 및영향받는publicinterface담당 |
| Jira Task 제안 | J2-T08 |
| 완료 기준 | STD/EXT동일수치·RTR사례의분류/거부회귀증거,공개계약리뷰. 이번에는코드변경없음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-018

| 항목 | 내용 |
|---|---|
| 심각도 | High（Production 정책 누락） |
| 관련 Interface | 입력 권한 / 충돌 / ECU 응답 확인 |
| 문서 A의 정의 | S00 결정_이슈IF-08·IF-04는Open. PC/로컬/테스트입력권한과ECUack미정. |
| 문서 B의 정의 | S07§9.1은VCU책임;S06 SYS_REQ_045/059는Windowlocal책임;원격PC와의전체중재계약없음. |
| 실제 코드 동작 | S09 MockReceipt및ECU_RESPONSE_STATUS18/111–113은별도. Source변경229–238은PC메모리정리일뿐. |
| 충돌 또는 누락 | Mock수락을실제실행으로판정할계약이없고PC종료/reset을안전정지로볼수없음. |
| 현재 상태 | Open |
| 영향 범위 | PC, VCU, Gateway, Body, 통합Test |
| 결정이 필요한 항목 | 권한/모드전환/중복·재연결·동시제어중재,수락vs실행·실제상태응답/로그correlation방법. |
| 담당자 | 시스템 / VCU / Gateway / PC |
| 리뷰 필요 담당자 | Door, Light, Window, CAN·LIN, Motor/Test |
| Jira Task 제안 | J2-T03 / J2-T04 |
| 완료 기준 | 승인된시나리오/상태·수락/실행구분·팀별책임,추후송신승인Gate. Mock Accepted는ECU응답아님유지. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-019

| 항목 | 내용 |
|---|---|
| 심각도 | Low（기존 설명 표기 차이） |
| 관련 Interface | LIN Door RequestState bit length |
| 문서 A의 정의 | S03 검토 항목row8의A1설명은RequestState2bit라고서술. |
| 문서 B의 정의 | S03 Signal 상세35, S02 LIN_Signal_Definition10, S05 RequestState40/79는1bit. |
| 실제 코드 동작 | 현재Door/GatewayLINhandler없음. 이불일치를수신코드가해결했다고볼수없음. |
| 충돌 또는 누락 | 보조검토문구와실제필드표/DB간길이표기불일치. |
| 현재 상태 | 검토 필요 |
| 영향 범위 | Door, Gateway, LIN문서/Test |
| 결정이 필요한 항목 | 보조설명동기화와정식필드표의승인범위. |
| 담당자 | 통신문서 / Door / LIN Common |
| 리뷰 필요 담당자 | Gateway, PC/Test |
| Jira Task 제안 | J2-T09 |
| 완료 기준 | 문구·Signal표·LDF비교와담당자검토증거. 여기서1/2bit를새로확정/수정하지않음. |
| Decision / Reviewer / Date / Evidence | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

## 10. 담당자별 결정 요청

Handbook§4.2/§5.5 및 S08 기준의 역할 요청이며 실명/실제 리뷰 완료를 추정하지 않는다.
모든 CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**다.

| 담당 역할 | 현재 경계 / 요청 | 관련 Issue |
|---|---|---|
| 시스템 / CAN·LIN 기준 산출물 | 승인된 기준 버전/ID registry/Matrix 대체 표의 권한과 변경 절차 | 001–004,010–011,013–015 |
| VCU (HINT-42) | PC 입력 수신 계약, 상태 전이, Torque 계산/Brake 제한, Gear 및 Body 명령 생성/우선순위 | 002–010,013–018 |
| Gateway (HINT-41) | CAN RX·중재와 LIN Master/Routing 구현 범위, Source Format, 현재 Fault 정책 차이 | 004,006–019 |
| Motor | VCU 출력의 consumer/Virtual Motor 관측 및 Local fail-safe. PC 운전자 입력을 VCU 출력으로 대체하지 않는 경계 검토 | 003–005,013–016,018 |
| Cluster | 기존 상태/Fault consumer와 상태·Event 의미 일치, 명령 수락을 실행 완료로 표시하지 않는 경계 | 013–018 |
| Door (HINT-45) | Lock/Unlock 및 RequestState, 원샷/유지/중복/완료응답·구동 종료 계약 | 006,008,010–012,019 |
| Light (HINT-46) | Generic ON/OFF 의미, 개별 lamp와 Gear/Brake 자동연동·Hazard priority | 006,009–012,018 |
| Window (HINT-47) | 목적지/OPEN·CLOSE 의미, 로컬 스위치/limit-stop, 명령 지속/STOP/Local Timeout·재개 책임 | 006–007,010–012,018 |
| PC/Test (HINT-48) | Mock/live 차단 유지, 승인 후에만 Encoder·권한·응답 상관/로그·통합시험 계획 | 전체 |

결정 기록 양식은 각 Issue의 Decision / Reviewer / Date / Evidence를 사용한다.
상태값은 단순 문서 갱신이나 pytest PASS로 Approved/Frozen으로 바꾸지 않는다.

## 11. 변경 영향 분석

| 영역 | 이번 실제 변경 | 승인 후 필요한 작업 후보 |
|---|---|---|
| 신규 리뷰 문서 | 본 Markdown1개만 작성 | 팀 결정/Evidence 추적 |
| 기존 README/VERIFICATION | 변경 없음, Phase3H-3/3I-1 포함 전체 바이트 보존 | 추후 승인된 Interface 정보만 반영 |
| PC 모델/GUI/CLI/Codec/Cache/Logger/Test/Fixture/의존성 | 변경 없음 | 별도 승인 후 송신 Adapter/Encoding/수락·응답 구분. 현재 Mock 계약 보존 |
| CAN DBC / Message Definition / Matrix | 변경 없음 | PC 입력과 기존6개 Signal 불일치의 승인된 동기화 |
| LIN LDF / Schedule / Matrix / Routing | 변경 없음 | Body 수신 경로, field/schedule/reference/PID 정합성 검토·동기화 |
| VCU / Gateway / Body Firmware | 변경 없음 | 담당자 소유 구현 및 별도 코드 리뷰·시험 |
| 다른 Worktree / D: 원본 / 임시 Excel | 변경 없음 | 승인 없는 복사/이동/초기화 금지 |

새 PC 입력의 영향은 Source Message/Signal 정의만이 아니다.
VCU/로컬 입력 중재, Gateway 전달, Window local safety, Fault/상태 consumer 및 시험 증적이 함께 연결돼야 한다.
현재 Mock의 Apply/Reset/Source 전환은 PC 메모리 동작이며 차량 안전 동작의 증거로 재사용하지 않는다.

## 12. Jira Issue 초안

아래 식별자는 실제 Jira Key가 아닌 **등록 전 초안**이다. 외부 등록/상태 변경은 수행하지 않았다.
기간은 팀 검토용1–3일 크기 제안이며 승인·Hardware 준비에 따른 일정 확정은 아니다.
전제 승인 없이 Firmware/DB/송신 코드를 구현하는 작업 지시가 아니다.

| 후보 | 크기 | 제목 / 범위 | 담당 / 완료 기준 |
|---|---|---|---|
| J2-T01 | 1일 | PC 운전자 입력 Baseline/ID registry 승인 준비 (J2-001/002) | 시스템+CAN/VCU/PC; 전체ID·예약범위/0x600 후보·기준권한과 승인 증적 확보 |
| J2-T02 | 2일 | PC→VCU Accelerator/Brake/Gear 계약 및 VCU 책임 검토 (003/005) | VCU+CAN+PC, Motor/Gateway 리뷰; 각 필드·유효성·소유권·수신/계산 구현 계획 승인 |
| J2-T03 | 2–3일 | PC 입력 freshness/연결 종료/권한·응답 정책 (004/018) | VCU+시스템+PC+Gateway/Body; timing/Alive/checksum 필요성·동시제어·수락vs실행 검증 시나리오 승인 |
| J2-T04 | 2–3일 | Body 입력 경로·Window/Door/Light 의미 및 Byte3 후보 결정 (006–010) | VCU+Gateway+각Body+PC; 목적지 불일치/지원 기능/VCU 경유·직수신/변경 산출물 승인 |
| J2-T05 | 1–2일 | 기존 CAN Gear/Brake/Alive6개 Signal 메타데이터 차이 정합화 검토 (013–015) | CAN+VCU/Gateway+consumer; 정상/Reserved/Invalid 및 표·DBC·회귀 기준 합의 |
| J2-T06-MASTER | 1–3일 | 승인 후 Gateway LIN Master 구현 범위 분리 (012) | Gateway+LIN/Body; header/schedule/command/response/cache/오류 책임·SW/추후Bus 시험 계획 |
| J2-T06-DOOR | 1–3일 | 승인 후 Door command/response 및 원샷/구동 종료 검토 (008/012) | Door+Gateway/LIN; 입력→실제 상태 경로·중복 처리 시험 계획 |
| J2-T06-WINDOW | 1–3일 | 승인 후 Window local/remote/limit-stop 상세 SW 계약 (007/012) | Window+Gateway/LIN; Local Timeout의 하위 parameter·재개/limit 우선순위 및 시험 계획 |
| J2-T06-LIGHT | 1–3일 | 승인 후 Light 입력·출력 priority 상세 SW 계약 (009/012) | Light+Gateway/LIN; 개별lamp/자동연동·Hazard priority 및 상태 검증 계획 |
| J2-T07 | 1–2일 | Gateway 기존 VCU Fault 감시의 문서/코드 차이 검토 (016) | Gateway+VCU/Motor/Cluster/PC;30ms/50ms 차이·State·회복 횟수·반영 대상 승인과 경계/전파 시험 |
| J2-T08 | 1일 | Gateway CAN Source Format metadata 검토 (017) | Gateway+CAN/VCU/PC; STD/EXT 같은숫자·RTR의 구분/거부 회귀 기준과 public contract 리뷰 |
| J2-T09 | 1–2일 | LIN Schedule/PID/RequestState 설명 동기화 검토 (011/019) | LIN/Gateway+각Body+PC; reference/운용·bit설명·Matrix/LDF 비교, 별도실기 Capture 계획 |

각 후보는 문제/근거/영향/담당자/결정/완료 기준을 §9의 Issue에 연결한다.
요구사항이나 DB 값 변경이 필요하면 핸드북4.2/5.5, S08 및 SYS_REQ_058의 Interface Change 절차로
승인된 기준 산출물 → 상대 담당자 리뷰 → DBC/LDF/Schedule → Firmware/Tool/Test → Evidence를 추적한다.

## 13. 승인 전 개발 금지 항목 및 검증 기록

### 13.1 승인 전 금지 / Gate

- 후보0x600 또는 다른 CAN ID, DLC, Payload/bit, Unit/Scale/Enum, 주기/Timeout을 확정하거나 임의 구현하지 않는다.
- PC가 기존 VCU_Command0x100을 대신 송신하거나 Reserved Byte3에 미승인 요청을 넣지 않는다.
- Live Driver TX를 활성화하지 않는다. 기존 CLI Sender를 우회 운전자 송신 경로로 연결하지 않는다.
- 임시 Excel, 공통 Matrix/DBC/LDF/Routing/Requirements, ECU Firmware, 기존 PC Source/Test/Fixture를 수정하지 않는다.
- Window→Door 차이를 문서만으로 임의 정정/승인하지 않고 상대 담당자 결정을 받는다.
- HW가 준비되지 않은 상태에서 CAN 연결·송신·수신/ECU 동작을 시도하거나 PASS로 보고하지 않는다.
- 팀 고정 버전·배포/Fixture 승인·담당자 리뷰는 미확정/NOT VERIFIED 유지.
- Git add/Commit/Push/PR/Merge/Reset/Rebase 및 Jira 등록/Done을 수행하지 않는다.

Interface 구현 재개 전 확인:
1. §9 High/Open/TBD 항목의 담당자 결정/범위·승인 증적 확보.
2. 기준 표/DB/Routing의 버전 일치와 동기화 diff.
3. VCU/Gateway/각Body 책임 및 실제 수신·실행·응답 계약 승인.
4. 별도 구현 요청 및 코드 리뷰·Mock/Fake 통합 검증 계획.
5. 실제 CANable/ECU 실기 Gate는 연결/배선/전원/노드·Firmware 확인 이후 별도로 수행.

### 13.2 이번 정적 검증 결과

| 검사 | 실제 결과 / 제한 |
|---|---|
| Branch/HEAD/시작 상태 | PC-Diagnostic-Test / 5c3e95db4ff53117afb575f5b7337f6265bcd327 / clean |
| Inventory | 실제 관련 파일·Sheet와 부재한 canonical Matrix 이름 구분 |
| CAN ID 중복 | DBC6개 및 메시지 정의6개 header에서 (STD/EXT,ID) 중복 없음 — 이상 없음 |
| 후보0x600 | 조사 범위의 정의/코드 충돌 미발견; 예약·전체노드 실기·정식승인은 검토 필요 |
| DBC/표 Signal 비교 | S02의24개 CAN Signal을 대조. start/length/order/signed/factor/offset/min/max/unit/invalid에서6개 메타데이터 차이(§5) |
| LIN Routing 비교 | 실제 LDF/표의 Frame/Signal/Schedule 및 후보Source 부재/과거Reference 혼재 확인 |
| ECU 최신성 | ls-remote HEAD와 GitHub 고정 Commit 원문 조사. 로컬 참조는 갱신하지 않음 |
| Requirements blob 차이 |5개sheet 수식·리터럴 행차이0, 캐시값 차이. 새로운 정책 승인으로 해석하지 않음 |
| PC 경계 | 읽기 전용 source 확인: 메모리Mock / Live 차단 / Sender 미연결 — 이상 없음 |
| Markdown 링크/경로·구성 | 13절·19개Issue 각13개필수필드, 로컬파일링크14개/Issue앵커19개 PASS. 고정Commit 원격링크10개는 실제 읽은 원문 파일과 대조. 부재 파일은 링크하지 않음 |
| git diff --check | PASS. 신규 미추적 문서도 별도 전체 whitespace 검사 PASS |
| 공통 산출물·기존 Source/Test·README/VERIFICATION·원본·다른Worktree | 최종 SHA-256 동일. D:원본25개·다른Worktree 파일/HEAD/Status·기존리뷰·모든Git refs 보존. 변경은 본 미추적Markdown1개뿐, Stage 비어 있음 |
| 전체 pytest / Driver / CLI / Native | 이번 문서 작업에서는 **NOT RUN**. Source/Test 변경 없음 |
| 직전 SW 결과 | 이전 Commit 준비 실행의569/52/140 PASS, Native10 PASS 기록. 이번 재실행 결과가 아님 |
| Firmware build / runtime / Flash / CANable·ECU 실측 | **NOT RUN / NOT VERIFIED** |
| 승인 / 팀 코드 리뷰 | **NOT VERIFIED**, 문서 작성 완료와 구분 |

최종 Git 변화는 본 미추적 Markdown1개만 허용한다. 실제 변경·보존 검사는 작업 후 보고와 함께 확인한다.
**이 리뷰는 Production Interface Freeze, Live 구현 READY, 팀 Integration 완료를 선언하지 않는다.**
