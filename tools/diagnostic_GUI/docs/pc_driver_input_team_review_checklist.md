# HINT-48 PC Driver Input Interface Team Review Checklist

## 1. 문서 목적 및 범위

Phase 3J-2의 원본 19개 Issue를 팀 의사결정에 사용할 수 있도록 분류한 리뷰 패키지다.
작성 기준일: 2026-10-16 (Asia/Seoul). 실제 팀 리뷰·승인·Interface Freeze는 아직 확인되지 않았다.
원본 리뷰 문서는 보존하며, 이 문서의 검토 순서·Primary Owner 제안은 원본 심각도/상태나 ECU 구현 책임을 변경하지 않는다.

이번 범위는 질문·선택지·영향·승인 양식·Jira 초안 작성이다. CAN/LIN Interface 변경은 **상대 담당자 리뷰 필요**다.
코드/Matrix/DBC/LDF/Routing/Requirements/임시 Excel/README/VERIFICATION은 변경하지 않는다.
PC 운전자 입력의 실제 CAN 송신은 **BLOCKED**이며, 기존 CLI Sender를 우회 경로로 연결하지 않는다.
CANable/ECU Hardware는 **NOT VERIFIED**다.

P0는 이 문서의 **우선 의사결정 안건**이며 원본 Issue의 High/Medium/Low 심각도를 재분류한 값이 아니다.
Reviewed, Approved, 코드 Merge, Jira Done 및 실제 Hardware 검증은 각각 별도의 증거가 필요하다.
이 문서 작성과 정적 대조만으로 팀 Reviewed/Approved를 체크하지 않는다.

## 2. 기준 문서·버전

| 항목 | 기준 |
|---|---|
| Repository | [HINT-CAN-LIN/freertos-can-lin-gateway](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway) |
| Branch / HEAD | PC-Diagnostic-Test / 5c3e95db4ff53117afb575f5b7337f6265bcd327 |
| 원본 | [pc_driver_input_interface_review.md](pc_driver_input_interface_review.md), Phase 3J-2, §9의 J2-001~019 |
| 원본 SHA-256 | 7f01a042327d15c1b8d5fbe762a94c111e54637bbf065d5a50c6f1873cca90a8 |
| 시작 Git 상태 | 원본 리뷰 Markdown 1개만 미추적, Stage 비어 있음 |
| 임시 Excel | Repository 외부 HINT48_PC_Driver_Input_Interface_임시설계_v0.1.xlsx, 미승인 초안 |
| 임시 Excel SHA-256 | 871e172dcd591c3b12a4dae796ef4b5f2c4e1f54e0f27ef3134a9e180f423476 |
| 변경 절차 | 핸드북 §4.2 p12–13, §5.5 p16, 15장 p43–50; CONTRIBUTING §5/§9 |

아래 S00~S13 및 R* 식별자는 원본의 근거 ID를 그대로 사용한다.
표의 버전/승인 구분은 산출물에 적힌 범위를 인용한 것으로 전체 Interface 승인 선언이 아니다.
특히 LDF의 pre-firmware 승인 문구, Requirements-level Frozen, Routing의 DECIDED와 PENDING REVIEW는 구분한다.

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


S07은 이번에 15장 전체(p43–50)를 추가 확인했다. §15.3/§15.6/§15.9는 Merge와 Done을 분리하고,
§15.14는 CAN·LIN·Fault·Routing 변경의 상대 담당자 리뷰와 검증 근거를 요구한다.
핸드북의 Window 소유권 세부사항은 S06 SYS_REQ_044/045/059 및 원본 J2-007/012/018과 함께 본다.

원본 ECU 근거는 아래 **고정 Commit** 범위다. 이번 패키지는 브랜치 최신성 재조사나 실제 Firmware 빌드/Flash 결과를 추가하지 않는다.
고정 원문의 VCU/Gateway/Body main 및 Gateway header를 읽기 전용으로 재대조했다.
원본의 전체 브랜치 Inventory/65개 blob 대조 기록은 이전 분석 기록으로 구분하며 이번 재실행 결과로 간주하지 않는다.

| Ref | Branch / 조사 Commit | 실제 파일 / 확인 내용 |
|---|---|---|
| RVCU | VCU_ECU / b49e48611a3ba0013077202f63e97a8603d21bb9 | firmware/vcu_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; HAL_Init/SystemClock_Config와 빈 main loop |
| RGW | Gateway_ECU / 6215ce46e5fcfa1b74f94f39194cd829392755d5 | firmware/gateway_ECU/Core/Src/main.c, Core/Inc/main.h, freertos.c, IRQ/MSP; CAN RX/Decode/Monitor/Status/Fault TX 구현 |
| RDOOR | Door_ECU / 1c287d35d7c15488cf04cb2b9025ea1b3d084d22 | firmware/door_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; GPIO/LED/button 초기화, 빈 main loop |
| RLIGHT | Light_ECU / 7abc743403bc0842a3a97fe1a68d0442e5681826 | firmware/light_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; HAL/clock 초기화, 빈 main loop |
| RWIN | Window_ECU / 1704faec999f79ceae1a56d1d603f4d73127f512 | firmware/window_ECU/Core/Src/main.c, Core/Inc/main.h, IRQ/MSP; GPIO/LED/button 초기화, 빈 main loop |


고정 원문 링크:
- [VCU_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/b49e48611a3ba0013077202f63e97a8603d21bb9/firmware/vcu_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/b49e48611a3ba0013077202f63e97a8603d21bb9/firmware/vcu_ECU/Core/Inc/main.h)
- [Gateway_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/6215ce46e5fcfa1b74f94f39194cd829392755d5/firmware/gateway_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/6215ce46e5fcfa1b74f94f39194cd829392755d5/firmware/gateway_ECU/Core/Inc/main.h)
- [Door_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1c287d35d7c15488cf04cb2b9025ea1b3d084d22/firmware/door_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1c287d35d7c15488cf04cb2b9025ea1b3d084d22/firmware/door_ECU/Core/Inc/main.h)
- [Light_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/7abc743403bc0842a3a97fe1a68d0442e5681826/firmware/light_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/7abc743403bc0842a3a97fe1a68d0442e5681826/firmware/light_ECU/Core/Inc/main.h)
- [Window_ECU main.c](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1704faec999f79ceae1a56d1d603f4d73127f512/firmware/window_ECU/Core/Src/main.c), [main.h](https://github.com/HINT-CAN-LIN/freertos-can-lin-gateway/blob/1704faec999f79ceae1a56d1d603f4d73127f512/firmware/window_ECU/Core/Inc/main.h)


원본 §2의 정확한 경로와 §9의 Sheet/행/함수/라인을 각 Issue에 보존한다.
CAN_Matrix.xlsx, LIN_Matrix.xlsx, LIN_Schedule.xlsx, vehicle.dbc, vehicle.ldf라는 canonical 이름은 현 기준 network 아래에 없다.
실제 존재하는 S01/S02/S03/S05와 비교하며, 독립 Matrix/예약 대장과 그 승인 범위는 J2-001/002에서 확인할 대상이다.
팀 고정 라이브러리 버전, Fixture 재배포 승인, 담당자 코드 리뷰는 미확정 / NOT VERIFIED를 유지한다.

## 3. 원본 19개 Issue 분류

주 분류는 Issue당 하나만 부여한다. 다른 그룹과의 관련성은 Reviewers 및 P0 안건에서 추적한다.
원본 담당자 목록은 §6에 그대로 남기며, Primary Owner는 회의 조정 역할 제안으로서 팀 배정 승인이 아니다.

| 그룹 | 범위 | 개수 |
|---|---|---|
| A | PC·VCU 입력 Interface | 5 |
| B | Gateway·LIN·Body Control | 8 |
| C | 공통 CAN/Fault 정합성 | 6 |
| 합계 | 원본 ID 19개, 추가 Issue 없음 | 19 |

| Issue ID | 원본 심각도 | 그룹 | 현재 상태(원문) | 관련 Interface | Primary Owner 제안 |
|---|---|---|---|---|---|
| [J2-001](#j2-001) | High（Freeze blocker） | C | 검토 필요 | 기준 산출물 / 승인 범위 | 시스템 / CAN·LIN 기준 산출물 |
| [J2-002](#j2-002) | High（Freeze blocker） | A | 초기값-수정 가능 | PC_Driver_Input 후보 ID0x600 | CAN Interface |
| [J2-003](#j2-003) | High（Freeze blocker） | A | TBD | Accelerator/Brake/Gear Payload | VCU |
| [J2-004](#j2-004) | High（Freeze blocker） | A | Open | PC 주기/Timeout/Alive/Checksum/연결 종료 | VCU / 시스템 안전 정책 |
| [J2-005](#j2-005) | High（구현/계약 누락） | A | Open | VCU 입력 해석·TorqueRequest 계산 | VCU |
| [J2-006](#j2-006) | High（Freeze blocker） | B | Open | PC Body 수신 주체 / 경로 | 시스템 |
| [J2-007](#j2-007) | High（문서 충돌） | B | 검토 필요 | Window 대상 / OPEN·CLOSE 의미 / 로컬 제어 | Window |
| [J2-008](#j2-008) | High（계약 누락） | B | Open | Door Lock/Unlock 실행 | Door |
| [J2-009](#j2-009) | High（의미 미결정） | B | Open | Light ON/OFF 범위 | Light |
| [J2-010](#j2-010) | High（실제 정의 부재） | B | 검토 필요 | VCU_Command Byte3 Body request 후보 | VCU / Gateway / CAN |
| [J2-011](#j2-011) | Medium（기준/표기 정합성） | B | 검토 필요 | LIN Schedule / Frame ID·PID / 승인 범위 | Gateway / LIN Common |
| [J2-012](#j2-012) | High（구현 누락） | B | Open | Gateway LIN Master / Body Slave 처리 | Gateway (Master) / 각 Body ECU (Slave) |
| [J2-013](#j2-013) | Medium（기존 CAN 정의 충돌） | C | 검토 필요 | VCU/Vehicle Gear 정상 범위 | CAN |
| [J2-014](#j2-014) | High（기존 CAN 정의 충돌） | C | 검토 필요 | Brake TRUE / Invalid | CAN |
| [J2-015](#j2-015) | Medium（기존 CAN 정의 충돌） | C | 검토 필요 | VCU AliveCounter / GatewayAlive Invalid | CAN |
| [J2-016](#j2-016) | High（코드·기존 정책 충돌） | C | 검토 필요 | Gateway VCU Timeout / State / Recovery | Gateway / Fault 정책 |
| [J2-017](#j2-017) | High（Source Format 계약 불일치） | C | 검토 필요 | Gateway STD/EXT/RTR 수신 식별 | Gateway |
| [J2-018](#j2-018) | High（Production 정책 누락） | A | Open | 입력 권한 / 충돌 / ECU 응답 확인 | 시스템 |
| [J2-019](#j2-019) | Low（기존 설명 표기 차이） | B | 검토 필요 | LIN Door RequestState bit length | 통신문서 / LIN Common |

원본 심각도: High 15개 / Medium 3개 / Low 1개.
원본 상태: 검토 필요 10개 / 초기값-수정 가능 1개 / TBD 1개 / Open 7개.
§7의 Pending은 팀 결정 양식의 초기 상태이며 이 원본 상태를 대체하지 않는다.

## 4. P0 결정 항목

아래 8개는 사용자가 요청한 우선 회의 안건이다. 안건 번호는 새 Issue ID가 아니다.
연결된 Medium/Low Issue는 관련 근거로 함께 검토하며 원본 심각도를 상향하지 않는다.

| P0 안건 | 먼저 결정할 질문 | 연결 Issue | 결정 담당 역할 제안 | 승인 전 영향 |
|---|---|---|---|---|
| 1. PC→VCU 입력 메시지 | 새 입력 Message가 필요한가? 기준 버전/ID registry와 수신 주체는 무엇인가? | J2-001/002/003/005 | 시스템·CAN·VCU | 현재 DBC/코드에 입력 계약 없음. 송신 구현 차단 |
| 2. 0x600 후보 | 전체 사용/예약 대장과 Format을 대조해 후보를 검토할 수 있는가? | J2-001/002 | CAN Interface·VCU | 정적 중복 미발견을 사용 승인으로 볼 수 없음 |
| 3. Accelerator/Brake/Gear | 입력 의미·DLC·encoding·정상/invalid·validation 계약은 무엇인가? | J2-003, 관련 J2-013/014/015 | VCU·CAN | VCU 출력 layout/Enum을 PC 입력에 복사 금지 |
| 4. 주기·Timeout·Fail-safe | Cyclic/Event, 단절·stale·재연결·중복/순서·복구를 누가 처리하는가? | J2-004/018 | VCU·시스템 안전·PC | 기존 VCU 출력 감시/Window local timeout과 별개 |
| 5. VCU 책임 | 입력 RX/해석·Gear 전이·Torque 계산/제한·출력 생성의 실제 구현과 버전은? | J2-005/018 | VCU, Motor 검토 | TorqueRequest는 VCU 계산 결과. PC 대체 송신 제외 |
| 6. Window/Door/Light 경로 | VCU 경유/직접 Gateway 경로 및 각 기능 의미·권한·실제 응답은? | J2-006/007/008/009/018 | 시스템·VCU·Gateway·각 Body | Window local/limit 책임과 Light/Door 실행 계약 미확정 |
| 7. Gateway→LIN | 명령 Source, Routing, Master/Slave, Frame/Signal/Schedule 및 검증 책임은? | J2-010/011/012, 관련 J2-019 | Gateway·LIN Common·각 Body | Byte3 후보/낡은 Reference를 실제 구현으로 사용 금지 |
| 8. 기존 CAN 메타데이터 | Gear 정상/Reserved, Brake Invalid, Alive Invalid의 승인 기준은? | J2-013/014/015 | CAN·VCU·Gateway, consumer 검토 | 기존 6개 Signal 차이의 정합화 필요 |

J2-001의 기준/Freeze, J2-016의 Fault Event·대표 상태·회복 정합성,
J2-017의 STD/EXT/RTR 보존, J2-018의 권한·실제 응답은 위 안건의 공통 승인 의존성이다.
기존 Fault 정책과 PC 입력 정책을 혼합하거나 Fault Event를 명령 Ack로 간주하지 않는다.
새 Fault Event Issue/Code/Threshold를 추가하지 않고 원본 J2-016/018의 범위로 검토한다.

| 기존 메타데이터 차이 | S02 근거 | S01/기존 해석과의 차이 | 원본 Issue |
|---|---|---|---|
| VCU_Command.Gear / Vehicle_Status.Gear | CAN_Signal_Definition7/16, Max5 | DBC Max3 및 0..3 정상 / 4..6 Reserved / 7 Invalid | J2-013 |
| VCU_Command.Brake / Vehicle_Status.Brake | CAN_Signal_Definition8/17, Invalid1 | 정상 TRUE=1과 중복. DBC는 Invalid N/A | J2-014 |
| VCU_Command.AliveCounter / Gateway_Status.GatewayAlive | CAN_Signal_Definition9/24, Invalid0xF | DBC/코드는 0..15 순환, 15도 정상 | J2-015 |

이 표의 값은 충돌 근거 인용이며 승인된 변경안이 아니다. 3종 × 2필드 = 원본의 6개 차이를 보존한다.

## 5. 담당자별 질문

개인 이름은 지정하지 않는다. 표의 역할은 핸드북 §4.2/§15.14, 원본 §10 및 S06 책임에 근거한다.
Primary Owner는 의사결정을 조정하고, 실제 변경 소유자는 해당 산출물/ECU 담당자로 유지한다.
교차 영향이 있으면 Primary 단독 결정으로 상대 담당자 승인을 대체할 수 없다.

| 담당 역할 | 회의에서 답할 질문 / 제출할 증거 | 관련 Issue |
|---|---|---|
| 시스템 / CAN·LIN 기준 산출물 | 공식 기준·승인 범위·독립 Matrix 또는 대체 표 권한·예약 대장은? Freeze 승인 증적과 변경 승인자는? | J2-001/002/003/004/006/010/011/013/014/015/018 |
| VCU (HINT-42) | PC 입력 RX 버전과 실제 구현 위치는? Accelerator/Brake/Gear 해석·상태 전이·Torque 계산/제한은? Body 명령 생성·입력 권한/응답 책임은? | J2-002/003/004/005/006/007/008/009/010/013/014/015/016/017/018 |
| Gateway (HINT-41) | Body 수신 경로·Routing Source는? LIN Master와 응답 수집은 어디에 구현되는가? 30/50ms·상태/회복 차이와 Source Format 손실을 어떻게 승인 기준에 맞출 것인가? | J2-004/006/007/008/009/010/011/012/013/014/015/016/017/018/019 |
| Motor | VCU Torque 출력 consumer/독립 local fail-safe 기준은? Gear/Brake/Alive 정합화와 VCU 입력 변경의 Motor 영향 검증은? | J2-003/004/005/013/014/015/016/018 |
| Cluster | 상태와 Fault Event의 기존 의미/대표 상태/회복 표시를 어떻게 검증하는가? 수락·실행·Fault 해제를 혼동하지 않는가? | J2-013/014/015/016/018 |
| Door (HINT-45) | Lock/Unlock 유지·원샷·중복·구동 종료·완료/상태 응답은? RequestState는 LockCommand와 어떻게 분리하는가? | J2-006/008/010/011/012/018/019 |
| Light (HINT-46) | Generic ON/OFF는 어느 기능인가? 개별 Lamp·Gear/Brake 자동 연동·Hazard/Turn 출력 우선순위의 승인 근거는? | J2-006/009/010/011/012/018 |
| Window (HINT-47) | 별도 Window 목적지와 OPEN/CLOSE 의미는? 로컬 Tact/Limit/motor-stop·원격 명령 중재 및 하위 Local Timeout 검증 책임은? | J2-006/007/010/011/012/018 |
| LIN Common / 통신문서 | 운용/참고 Schedule, Frame ID/Protected PID, checksum, RequestState 설명 및 Matrix/LDF 승인 범위는? | J2-007/008/009/010/011/012/019 |
| PC/Test (HINT-48) | Mock 수락과 실제 응답을 어떻게 구분·상관 기록할 것인가? 승인 후 Encoder/Sender·권한 Gate·통합 테스트를 어떤 기준/증적으로 검증할 것인가? | J2-001~019 |
| 임시안 작성 담당 | Window 목적지·미정 Payload/경로와 문서 우선순위를 실제 기준에 맞춰 어떤 변경 절차로 결정할 것인가? | J2-002/003/004/006/007/009/018 |

## 6. Issue별 결정 테이블·선택지 및 영향도

심각도·상태·문서 A/B·실제 코드·충돌·원본 담당/Reviewer·완료 기준은 원문을 그대로 인용한다.
원문 S*/R*는 §2의 파일/버전에 연결된다. 코드 위치는 해당 고정 Commit 기준이며 실행/Hardware 증거가 아니다.
선택지는 원문/S00에 실제로 제시된 후보만 사용한다. 상충한 현행 값은 승인 가능한 동등 대안으로 취급하지 않는다.
대안 근거가 없으면 **담당자 결정 필요**로 남긴다.
승인 필요는 앞으로 해당 계약/변경에 필요한 승인 절차이며 현재 승인 여부가 아니다.
역할 분리는 원본 담당자 범위를 보존하는 조정안이다. 결정·승인 입력은 §7에서 수행한다.

### J2-001

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-001 원문](pc_driver_input_interface_review.md#j2-001) |
| 기존 심각도 | High（Freeze blocker） |
| 그룹 | C |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | 기준 산출물 / 승인 범위 |
| 근거 파일·위치 / 문서 A(원문) | S08 §5, S07 §5.5: 승인·동기화된 Matrix/DBC 관리 요구. |
| 근거 파일·위치 / 문서 B(원문) | 독립 Matrix 없음. S02 row2/22와 S03 통신 규칙13은 02/05 FIX 우선; S04는 공식Freeze Pending, S05는 pre-firmware 승인 표기. |
| 실제 코드 동작·위치(원문) | PC는 Mock만 처리. 최신5개 ECU Inventory/Interface blob 대조로 별도 Matrix 미발견. |
| 충돌 또는 누락(원문) | 기준 문서의 우선순위와 승인 범위/버전 증적이 하나로 연결되지 않음. |
| 결정 질문(원문) | 사용할 Baseline 버전/기준 권한, 독립 Matrix 존재·제공 또는 대체 표의 공식 승인 범위. |
| 가능한 대안 / 결정 대상 | 원문 질문에 제시된 기준 관리 방식: 독립 Matrix 제공 또는 실제 존재하는 대체 표의 공식 승인 범위 명시. 어느 쪽도 현재 승인되지 않음. |
| 대안별 영향 / 영향 범위 | 독립 Matrix 제공: 현행 표·DB와 대조 및 버전 연결 필요. 대체 표 사용: 기준 권한·승인 범위·변경 추적을 명시해야 하며 파일명/FIX 선언만으로 대체 승인 불가. |
| 영향받는 ECU·Tool(원문) | CAN/LIN 정의, ECU, PC/Test 전원 |
| 원본 담당자 | 시스템 / CAN·LIN 기준 산출물 담당 |
| Primary Owner 제안 | 시스템 / CAN·LIN 기준 산출물 |
| Reviewers(원문) | VCU, Gateway, Motor, Cluster, Door, Light, Window, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T01 |
| 완료 조건(원문) | 기준 파일/Commit·승인 담당자/날짜/범위/Evidence를 기록하고 불일치 처리 절차 합의. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-002

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-002 원문](pc_driver_input_interface_review.md#j2-002) |
| 기존 심각도 | High（Freeze blocker） |
| 그룹 | A |
| 현재 상태(원문) | 초기값-수정 가능 |
| 관련 Interface(원문) | PC_Driver_Input 후보 ID0x600 |
| 근거 파일·위치 / 문서 A(원문) | S00 요약6–7/메시지_제안2: 초기값-수정 가능, 충돌 검사·리뷰 전 TX 금지. |
| 근거 파일·위치 / 문서 B(원문) | S01/S02/S03 기존6개 STD ID에0x600 없음. 예약대장/독립CAN Matrix 없음. |
| 실제 코드 동작·위치(원문) | RGW main.h127–132도 같은6개 ID. 조사된5개 ECU source에는 PC0x600 handler 없음. PC Frame 생성 없음. |
| 충돌 또는 누락(원문) | 정적 중복은 미발견이나 사용/예약 및 전체 실제 노드 충돌 없음이 보장되지 않음. |
| 결정 질문(원문) | 정식 PC ID/Frame Format 사용·예약 승인, 전체 ID registry 범위. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 0x600은 검토할 단일 임시 후보이며 대체 ID/Format을 이 문서에서 생성하지 않음. |
| 대안별 영향 / 영향 범위 | ID registry·예약·전체 노드 조사 및 CAN 송신/수신 담당자 검토가 필요. 현재 6개 정의에서 중복 미발견은 사용 승인이나 실제 버스 충돌 부재 증거가 아님. |
| 영향받는 ECU·Tool(원문) | PC, VCU, Gateway 및 CAN 전체 노드 |
| 원본 담당자 | CAN Interface / VCU / PC |
| Primary Owner 제안 | CAN Interface |
| Reviewers(원문) | Gateway, Motor, Cluster, 시스템 |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T01 |
| 완료 조건(원문) | 전체 ID/예약 대장과 STD·EXT 키 조사 증거, 담당자 승인. 후보 ID를 확정값으로 사용하지 않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-003

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-003 원문](pc_driver_input_interface_review.md#j2-003) |
| 기존 심각도 | High（Freeze blocker） |
| 그룹 | A |
| 현재 상태(원문) | TBD |
| 관련 Interface(원문) | Accelerator/Brake/Gear Payload |
| 근거 파일·위치 / 문서 A(원문) | S00 신호_제안2–4: 이름 후보와 입력 모델만 제안, bit/length/factor TBD. |
| 근거 파일·위치 / 문서 B(원문) | S01에는 해당 PC 입력 Message/SG_ 없음. S02의 Torque/Gear/Brake는 VCU 출력이며 PC 입력이 아님. |
| 실제 코드 동작·위치(원문) | S09 DriverInputs/validated37–52는 PC 메모리 정책; RVCU main63–100 수신/입력처리 없음. |
| 충돌 또는 누락(원문) | PC Message DLC 및 신호의 위치·길이·byte order·signed·scale·offset·unit·initial/invalid 계약 부재. |
| 결정 질문(원문) | Accelerator 모델/단위·Brake bool 또는 pressure·Gear 의미/전이, Encoding/validation 항목 전부. |
| 가능한 대안 / 결정 대상 | S00 신호_제안3 및 원문 질문의 Brake bool 또는 pressure 모델을 비교 검토. Accelerator/Gear의 상세 encoding과 DLC는 담당자 결정 필요. |
| 대안별 영향 / 영향 범위 | bool: 제동 의도 입력의 의미·유효성·VCU 제한 처리를 정의해야 함. pressure: 물리 의미·단위·범위·변환·검증 계약을 추가로 정의해야 함. 두 모델 모두 기존 VCU 출력 Brake/Torque bit layout을 PC 입력에 복사할 근거가 아님. |
| 영향받는 ECU·Tool(원문) | PC, VCU, CAN, Motor/Gateway 영향 |
| 원본 담당자 | VCU / CAN / PC |
| Primary Owner 제안 | VCU |
| Reviewers(원문) | Motor, Gateway, 시스템 |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T02 |
| 완료 조건(원문) | 승인된 계약 표와 동기화된 DBC/기준 산출물, 정상/잘못된 입력 비교 기준. 여기서 임의 배치하지 않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-004

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-004 원문](pc_driver_input_interface_review.md#j2-004) |
| 기존 심각도 | High（Freeze blocker） |
| 그룹 | A |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | PC 주기/Timeout/Alive/Checksum/연결 종료 |
| 근거 파일·위치 / 문서 A(원문) | S00 메시지_제안2 F열 TBD, 결정_이슈IF-03 Open. |
| 근거 파일·위치 / 문서 B(원문) | S02 POL-001의30ms는 기존 VCU 출력 감시, POL-009의Window Local Timeout 수치는 하위SW 위임. PC 계약 없음. |
| 실제 코드 동작·위치(원문) | S09 Apply는 수동 메모리 처리; sequence57은 PC 이력 번호. S09 close는 메모리 reset일 뿐. VCU handler 없음. |
| 충돌 또는 누락(원문) | PC 입력 lost/stale/중복/순서/신뢰성/재연결과 안전 처리 정의 없음. |
| 결정 질문(원문) | Cyclic/Event 여부, Timeout·연결 끊김 동작, Alive/Payload Checksum 필요성, 오류/복구/재입력 정책. |
| 가능한 대안 / 결정 대상 | 원문 질문의 Cyclic 또는 Event 송신 방식 검토. Timeout·Alive·Payload Checksum·단절/복구 동작은 담당자 결정 필요. |
| 대안별 영향 / 영향 범위 | Cyclic: 갱신·age·전송부하 검증이 필요. Event: 갱신이 없는 상태와 단절을 구분할 검증 계약이 필요. 어느 쪽도 주기·Timeout·Fail-safe 수치/기법을 확정하지 않으며 기존 30/50ms를 PC 입력에 전용하지 않음. |
| 영향받는 ECU·Tool(원문) | PC, VCU, Gateway, Motor 및 Body |
| 원본 담당자 | VCU / 시스템 안전 정책 / PC |
| Primary Owner 제안 | VCU / 시스템 안전 정책 |
| Reviewers(원문) | Gateway, CAN, Motor, affected Body ECU |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T03 |
| 완료 조건(원문) | 합의된 정책/검증 시나리오와 담당자 승인. 기존30/50ms·LIN checksum을 PC 정책으로 복사하지 않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-005

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-005 원문](pc_driver_input_interface_review.md#j2-005) |
| 기존 심각도 | High（구현/계약 누락） |
| 그룹 | A |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | VCU 입력 해석·TorqueRequest 계산 |
| 근거 파일·위치 / 문서 A(원문) | S07§9.1, S06 Requirements8 SYS_REQ_003: VCU 운전자 입력 기반 제어/토크 요청. |
| 근거 파일·위치 / 문서 B(원문) | S02 CAN_Message_Definition6 및 S01 sender=VCU, TorqueRequest는 출력. |
| 실제 코드 동작·위치(원문) | RVCU main.c63–100/143–145 HAL/clock 및 빈loop. main.h/IRQ/MSP에서도 입력처리 없음. RGW828–869는 Decode/UART 표시. |
| 충돌 또는 누락(원문) | 현재 확인한 VCU 원문에 입력 RX, state/torque 계산·제한 또는 출력 TX가 구현되지 않음. |
| 결정 질문(원문) | 실제 VCU 구현 위치/대상 버전, 입력 처리 계약과 계산/제한/상태 전이 책임. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 실제 구현 위치·버전·입력 해석/계산/제한 책임의 증거를 요청. PC의 VCU 출력 대체 송신은 대안에서 제외. |
| 대안별 영향 / 영향 범위 | VCU가 입력을 해석하고 TorqueRequest를 계산하는 경계를 유지. Motor는 VCU 출력 consumer, Gateway는 전달/관측 책임. 현재 빈 loop를 구현 완료로 판단할 수 없음. |
| 영향받는 ECU·Tool(원문) | VCU, Motor, PC, Gateway |
| 원본 담당자 | VCU |
| Primary Owner 제안 | VCU |
| Reviewers(원문) | Motor, Gateway, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T02 / J2-T03 |
| 완료 조건(원문) | 승인 계약과 실제 구현 경로·Commit·SW 테스트 증거. PC가 VCU 출력 송신을 대신하지 않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-006

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-006 원문](pc_driver_input_interface_review.md#j2-006) |
| 기존 심각도 | High（Freeze blocker） |
| 그룹 | B |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | PC Body 수신 주체 / 경로 |
| 근거 파일·위치 / 문서 A(원문) | S00 메시지_제안4: PC→Gateway 또는 VCU, 미정. |
| 근거 파일·위치 / 문서 B(원문) | S04 DEC-01: VCU가Body command 생성 후보, PC 수신 Message/경로 정의는 없음. |
| 실제 코드 동작·위치(원문) | RGW ProcessCanMessage1107–1140는 기존6개ID Decode만 수행, PC Body handler 없음. RVCU 수신 없음. |
| 충돌 또는 누락(원문) | VCU 경유와 Gateway 직접 수신 중 소유권·권한·명령 생성 책임 미선택. |
| 결정 질문(원문) | A/B 경로와 명령 해석/우선순위/권한·응답 책임; 필요 PC Body 계약. |
| 가능한 대안 / 결정 대상 | S00 메시지_제안4와 원문 A/B 경로: PC→VCU→Gateway→LIN Body 또는 PC→Gateway→LIN Body. 현재 어느 경로도 승인되지 않음. |
| 대안별 영향 / 영향 범위 | VCU 경유: 입력 해석·권한·Body 명령 생성과 기존 VCU 출력 변경 영향 검토. Gateway 직접: Gateway 수신/중재 책임 변경 및 VCU와의 제어 권한 충돌 검토. 공통으로 Door/Light/Window별 실제 응답·Routing 계약 필요. VCU_Command(0x100)의 송신자는 VCU 유지. |
| 영향받는 ECU·Tool(원문) | PC, VCU, Gateway, Door/Light/Window |
| 원본 담당자 | 시스템 / VCU / Gateway |
| Primary Owner 제안 | 시스템 |
| Reviewers(원문) | CAN·LIN, Door, Light, Window, PC |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T04 |
| 완료 조건(원문) | 3개 Body 기능별 수신 주체와 책임 경로 승인, 관련 Message/Routing 변경 계획. VCU0x100 PC 대체 송신 제외. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-007

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-007 원문](pc_driver_input_interface_review.md#j2-007) |
| 기존 심각도 | High（문서 충돌） |
| 그룹 | B |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | Window 대상 / OPEN·CLOSE 의미 / 로컬 제어 |
| 근거 파일·위치 / 문서 A(원문) | S00 신호_제안7: Window 처리 목적지 Gateway→LIN Door ECU, OPEN/CLOSE/STOP 후보. |
| 근거 파일·위치 / 문서 B(원문) | S02 LIN_Frame_Definition10/LIN_Signal_Definition19, S05 frames94–104/encoding222–227, S06 SYS_REQ_044/045/059: 별도 Window ECU, STOP/UP/DOWN 및 local safety. |
| 실제 코드 동작·위치(원문) | RWIN main.c65–110 및user section은 빈loop, command/limit-stop 처리 없음. PC는 OPEN/CLOSE 문자열만 Mock에 보관. |
| 충돌 또는 누락(원문) | 대상 ECU 충돌. OPEN/CLOSE→UP/DOWN 방향과 원격/물리 스위치/limit 우선순위·Local Timeout 파라미터 미정. |
| 결정 질문(원문) | 목적지 정정 승인, 명령 의미/지속·STOP·로컬 우선순위/정량Local Timeout의 하위 요구사항. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 임시 Excel의 Door 목적지와 기존 Window ECU 정의는 충돌 근거이며 동등하게 승인된 경로 대안이 아님. OPEN/CLOSE의 UP/DOWN 대응을 추정하지 않음. |
| 대안별 영향 / 영향 범위 | Window 수신 경로·로컬 Tact/Limit·모터 정지·원격 입력 중재와 하위 Local Timeout 요구사항에 영향. 임시안 작성 담당, Window/Gateway 및 Door의 문서 검토 필요. |
| 영향받는 ECU·Tool(원문) | Window, Gateway, VCU, PC, Door 문서 |
| 원본 담당자 | Window / Gateway / 임시안 작성 담당 |
| Primary Owner 제안 | Window |
| Reviewers(원문) | VCU, Door, LIN Common, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T04 / J2-T06-WINDOW |
| 완료 조건(원문) | Window 경로/의미·local safety 승인, 관련 문서 동기화 및 독립 SW/추후실기 증거. Door 기능으로 합치지 않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-008

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-008 원문](pc_driver_input_interface_review.md#j2-008) |
| 기존 심각도 | High（계약 누락） |
| 그룹 | B |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | Door Lock/Unlock 실행 |
| 근거 파일·위치 / 문서 A(원문) | S02 LIN_Signal_Definition9–10, S05 LockCommand/RequestState: 잠금 요청과 상태 요청 별개. |
| 근거 파일·위치 / 문서 B(원문) | S04 DEC-07/C2L-006: LockCommand만 후보 매핑, RequestState0 유지; 지속/원샷 정의 없음. |
| 실제 코드 동작·위치(원문) | RDOOR main.c65–110 초기화/빈loop, LIN handler 없음. PC Phase3J-1 DriverInputs31–35에 Door 없음. |
| 충돌 또는 누락(원문) | CAN 발생원·실제 command 처리·중복 요청/구동 종료/완료응답 정책 부재. |
| 결정 질문(원문) | 잠금 요청 유지/원샷·중복 억제·액추에이터 완료/상태·초기화/timeout 의미. |
| 가능한 대안 / 결정 대상 | 원문 질문의 요청 유지 또는 원샷 실행 방식 검토. 중복 억제·완료·실제 상태 응답 세부 계약은 담당자 결정 필요. |
| 대안별 영향 / 영향 범위 | 유지 방식: 반복 수신과 실제 액추에이터 동작 지속을 구분해야 함. 원샷 방식: 요청 중복·재연결 시 재실행·완료 관측 기준을 정해야 함. LockCommand와 RequestState는 별개이며 새 응답 Signal/Timeout을 임의 추가하지 않음. |
| 영향받는 ECU·Tool(원문) | Door, Gateway, VCU, PC |
| 원본 담당자 | Door / Gateway |
| Primary Owner 제안 | Door |
| Reviewers(원문) | VCU, LIN Common, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T04 / J2-T06-DOOR |
| 완료 조건(원문) | Door 전용 실행/응답 계약과 검증 시나리오 승인. Window/Light와 기능 혼합 금지. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-009

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-009 원문](pc_driver_input_interface_review.md#j2-009) |
| 기존 심각도 | High（의미 미결정） |
| 그룹 | B |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | Light ON/OFF 범위 |
| 근거 파일·위치 / 문서 A(원문) | S00 신호_제안8/S09 LIGHT_CHOICES13: Generic ON/OFF 후보. |
| 근거 파일·위치 / 문서 B(원문) | S02 LIN_Frame_Definition8/LIN_Signal_Definition11–15, S05 81–87: Head/Turn/Hazard/Reverse/Brake 독립; S04 DEC-08 priority후보. |
| 실제 코드 동작·위치(원문) | RLIGHT main63–100 빈loop; S09는단순Mock 의도, bitmask/개별Lamp mapping 없음. |
| 충돌 또는 누락(원문) | ON/OFF가 가리키는 lamp 집합·기존Gear/Brake 연동·Hazard/Turn 우선순위의 승인/실행 없음. |
| 결정 질문(원문) | Generic ON/OFF의 지원 범위, 각Lamp request, 자동연동과사용자입력충돌/출력우선순위. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. Generic ON/OFF를 전체 Lamp나 HeadLamp로 자동 대응하지 않음. S04 DEC-08은 검토 중인 Hazard 우선 후보로만 제시. |
| 대안별 영향 / 영향 범위 | Head/Turn/Hazard/Reverse/Brake 각 기능과 자동 Gear/Brake 연동, 최종 Light 출력 책임 및 우선순위에 영향. 사용 범위/초기·stale 정책과 피드백 계약이 결정돼야 함. |
| 영향받는 ECU·Tool(원문) | Light, Gateway, VCU, PC |
| 원본 담당자 | Light / Gateway / VCU |
| Primary Owner 제안 | Light |
| Reviewers(원문) | LIN Common, PC/Test, 시스템 |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T04 / J2-T06-LIGHT |
| 완료 조건(원문) | Light 기능별 의미/권한/priority/초기·stale 정책 승인. Genericbool을전체Lamp 또는HeadLamp로 임의 대응하지 않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-010

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-010 원문](pc_driver_input_interface_review.md#j2-010) |
| 기존 심각도 | High（실제 정의 부재） |
| 그룹 | B |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | VCU_Command Byte3 Body request 후보 |
| 근거 파일·위치 / 문서 A(원문) | S04 DEC-01/02, Required_Interface_Changes7–11: 신규5개Byte3 필드, PENDING REVIEW. |
| 근거 파일·위치 / 문서 B(원문) | S02 CAN_Message_Definition15: Reserved; S01 VCU_Command SG_4개뿐. |
| 실제 코드 동작·위치(원문) | RGW main.h48–54/DecodeVcuCommand840–843도Torque/Gear/Brake/Alive만해석. 신규Body필드없음. |
| 충돌 또는 누락(원문) | Routing Source 후보가 실제 CAN Message/Encoder/Decoder에 없음. |
| 결정 질문(원문) | 후보채택/대안, 필요한 정식Interface Change와모든산출물 동기화. |
| 가능한 대안 / 결정 대상 | 원문 질문의 Byte3 후보 채택 여부 결정 필요. 채택하지 않을 경우 대안 경로/계약은 담당자가 제시해야 하며 여기서 새 Message/필드를 제안하지 않음. |
| 대안별 영향 / 영향 범위 | 후보 채택: Reserved의 정식 Interface Change 및 표·DBC·VCU encoder·Gateway decoder·Routing·consumer/Test 동기화 필요. 미채택: 해당 Routing Source를 현재 존재하는 필드처럼 사용할 수 없음. S04 PENDING REVIEW를 승인으로 승격하지 않음. |
| 영향받는 ECU·Tool(원문) | VCU, Gateway, CAN, Door/Light/Window, PC/Test |
| 원본 담당자 | VCU / Gateway / CAN |
| Primary Owner 제안 | VCU / Gateway / CAN |
| Reviewers(원문) | Door, Light, Window, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T04 |
| 완료 조건(원문) | 승인된Source필드와일치하는표/DBC/Routing/코드·Evidence. Reserved를임의사용하지않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-011

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-011 원문](pc_driver_input_interface_review.md#j2-011) |
| 기존 심각도 | Medium（기준/표기 정합성） |
| 그룹 | B |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | LIN Schedule / Frame ID·PID / 승인 범위 |
| 근거 파일·위치 / 문서 A(원문) | S02 LIN_Frame_Definition15–24, S03 통신 규칙19–29, S05 BODY_10ms162–170은 일치. |
| 근거 파일·위치 / 문서 B(원문) | S04 Interface_Ref51/57–62는WindowTBD/BASE-20ms; DEC-05/06은Pending; S05는pre-firmware승인이라고표기. |
| 실제 코드 동작·위치(원문) | RGW defaultTask1193–1243에LINschedule없음. Frame/Protected PID실측없음. |
| 충돌 또는 누락(원문) | 낡은Reference/현재운용설계/검증대상 구분 및최종동기화·승인 증적이남음. |
| 결정 질문(원문) | 운용vs참고의문서범위, 독립Matrix 제공/동기화, Protected PID/Checksum확인방법. |
| 가능한 대안 / 결정 대상 | 원문에 존재하는 운용 후보 BODY_10ms와 참고 BASE_20ms의 역할/승인 범위를 분리해 검토. 단순히 둘 중 하나의 이름을 선택해 Freeze하는 대안은 아님. |
| 대안별 영향 / 영향 범위 | BODY_10ms는 현재 S02/S03/S05와 대응, BASE_20ms는 LDF 참고 표이며 Light 주기 요구와 차이. S04 과거 Interface_Ref의 위치/승인 범위를 정리하고 Frame ID와 Protected PID를 구분해야 함. timing/checksum 실측은 별도. |
| 영향받는 ECU·Tool(원문) | Gateway, LIN Common, Door/Light/Window, PC/Test |
| 원본 담당자 | Gateway / LIN Common / 기준 산출물 담당 |
| Primary Owner 제안 | Gateway / LIN Common |
| Reviewers(원문) | Door, Light, Window, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T09 |
| 완료 조건(원문) | Schedule대조·Reference표기정리/동기화및담당자승인. timing/PID/Checksum은HW별도측정, 현재PASS주장금지. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-012

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-012 원문](pc_driver_input_interface_review.md#j2-012) |
| 기존 심각도 | High（구현 누락） |
| 그룹 | B |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | Gateway LIN Master / Body Slave 처리 |
| 근거 파일·위치 / 문서 A(원문) | S02 LIN정의/S05 Nodes22–28·Frames68–105·Schedule/S04routes가Master-Slave경로요구. |
| 근거 파일·위치 / 문서 B(원문) | S06 SYS_REQ_002/005/006/044/045/059가Routing·Body/local출력책임정의. |
| 실제 코드 동작·위치(원문) | RGW CANDecode와UART로그만 확인; LINbreak/header/command/schedule/response처리없음. RDOOR/RWIN/RLIGHT도초기화/빈loop. |
| 충돌 또는 누락(원문) | 문서의LIN제어/피드백/안전경로를현재검토소스로실행가능하다고판정할근거가없음. |
| 결정 질문(원문) | 실제구현계획·정식소스위치/버전·Master/각Slave범위/검증책임. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 검토한 고정 Commit 밖에 실제 구현이 있다면 정확한 소스/Commit과 계약 증거를 먼저 제공. 구현 계획은 Master/각 Slave로 분리. |
| 대안별 영향 / 영향 범위 | Gateway는 LIN header/schedule/command/response와 Routing, 각 Body ECU는 자체 명령·출력·상태·로컬 안전 책임. 현재 소스의 부재 확인을 팀 전체의 구현 부재나 실제 보드 동작으로 확대하지 않음. |
| 영향받는 ECU·Tool(원문) | Gateway, Door/Light/Window, VCU, PC/Test |
| 원본 담당자 | Gateway / 각 Body ECU |
| Primary Owner 제안 | Gateway (Master) / 각 Body ECU (Slave) |
| Reviewers(원문) | LIN Common, VCU, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T06-MASTER / DOOR / WINDOW / LIGHT |
| 완료 조건(원문) | Interface승인후각소스구현·SW테스트·추후Bus/출력증거. 현재통합/HW완료로판정하지않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-013

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-013 원문](pc_driver_input_interface_review.md#j2-013) |
| 기존 심각도 | Medium（기존 CAN 정의 충돌） |
| 그룹 | C |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | VCU/Vehicle Gear 정상 범위 |
| 근거 파일·위치 / 문서 A(원문) | S02 CAN_Signal_Definition7/16 및 S03 Signal 상세8/17: Max5. |
| 근거 파일·위치 / 문서 B(원문) | S01 GearMax3/VAL_0..3정상,4..6RESERVED,7INVALID; S02 Value_Table6–11도같은enum. |
| 실제 코드 동작·위치(원문) | RGW DbcGearName684–699 및DecodeVcuCommand845–847/DecodeVehicleStatus934–939:0..3정상. |
| 충돌 또는 누락(원문) | 표의physicalMax와enum/DBC/코드정상범위불일치. |
| 결정 질문(원문) | 정상범위/Reserved/Invalid표현및관련산출물권한; PC입력enum으로복제금지. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 문서 Max5와 DBC/enum의 정상 0..3은 충돌하는 현행 정의로 비교하며 새로운 정상 범위/Enum 대안을 만들지 않음. |
| 대안별 영향 / 영향 범위 | VCU/Vehicle Gear 두 필드와 Gateway·Motor·Cluster·PC consumer, Reserved/Invalid 검증에 영향. 두 정의 중 권위/승인 증거를 확인하고 산출물을 함께 정합화해야 함. |
| 영향받는 ECU·Tool(원문) | VCU, Gateway, Motor, Cluster, PC/Test |
| 원본 담당자 | CAN / VCU |
| Primary Owner 제안 | CAN |
| Reviewers(원문) | Gateway, Motor, Cluster, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T05 |
| 완료 조건(원문) | 승인된범위및표·DBC·모든consumer검증기준일치. 여기서Max수정하지않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-014

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-014 원문](pc_driver_input_interface_review.md#j2-014) |
| 기존 심각도 | High（기존 CAN 정의 충돌） |
| 그룹 | C |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | Brake TRUE / Invalid |
| 근거 파일·위치 / 문서 A(원문) | S02 CAN_Signal_Definition8/17 및 S03 Signal 상세9/18: Brake 정상1이면서 Invalid1. |
| 근거 파일·위치 / 문서 B(원문) | S01 CM_ SG_256Brake는Invalid N/A; S04 Required_Interface_Changes6/DEC-03도N/A후보. |
| 실제 코드 동작·위치(원문) | RGW DecodeVcuCommand842/864는bit1을ON으로표시하며signalInvalid1판정없음. |
| 충돌 또는 누락(원문) | 같은1bit값에정상ON과Invalid를동시에정의. PCBrakeInput계약은또별도미정. |
| 결정 질문(원문) | 기존BrakeInvalid정책승인·동기화와PCBrake계약의독립범위. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 표의 정상 TRUE=1/Invalid=1 충돌과 DBC의 Invalid N/A 및 S04 후보를 비교. 정상 ON 거부를 해결안으로 제시하지 않음. |
| 대안별 영향 / 영향 범위 | VCU/Vehicle Brake 두 필드의 실제 값과 메시지 validity 구분, VCU·Motor·Gateway·Cluster·PC 해석/회귀에 영향. PC BrakeInput 계약은 별도 J2-003에서 결정. |
| 영향받는 ECU·Tool(원문) | VCU, Motor, Gateway, Cluster, PC/Test |
| 원본 담당자 | CAN / VCU / Gateway |
| Primary Owner 제안 | CAN |
| Reviewers(원문) | Motor, Cluster, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T05 |
| 완료 조건(원문) | 정상TRUE/메시지validity/invalid구분과표·DBC·테스트일치. 기존정상ON거부로해결하지않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-015

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-015 원문](pc_driver_input_interface_review.md#j2-015) |
| 기존 심각도 | Medium（기존 CAN 정의 충돌） |
| 그룹 | C |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | VCU AliveCounter / GatewayAlive Invalid |
| 근거 파일·위치 / 문서 A(원문) | S02 CAN_Signal_Definition9/24 및 S03 Signal 상세10/25: Invalid0xF. |
| 근거 파일·위치 / 문서 B(원문) | S01의CM_는정상0..15wrap과Invalid미지정. S03 통신 규칙15도0..15. |
| 실제 코드 동작·위치(원문) | RGW main.c544 기대counter modulo16,445gatewayAlivewrap;15를정상순환값으로사용. |
| 충돌 또는 누락(원문) | 정상counter15와Invalid0xF가겹침. PC내부sequence는CANAlive와무관. |
| 결정 질문(원문) | counter범위·Invalid유무·age/continuity분리및승인; PCcounter필요성은별도. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 표 Invalid0xF와 DBC/코드의 정상 0..15 순환은 현행 충돌이며 임의의 새 counter 범위나 Invalid code를 제안하지 않음. |
| 대안별 영향 / 영향 범위 | VCU AliveCounter/GatewayAlive 두 필드 및 consumer의 연속성·복구·15→0 검증에 영향. PC 이력 sequence와 CAN Alive를 분리해야 함. |
| 영향받는 ECU·Tool(원문) | VCU, Gateway, CAN consumer, PC/Test |
| 원본 담당자 | CAN / Gateway / VCU |
| Primary Owner 제안 | CAN |
| Reviewers(원문) | Motor, Cluster, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T05 |
| 완료 조건(원문) | 15→0정상회귀와invalid정책이일관된기준/DBC/consumer증거. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-016

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-016 원문](pc_driver_input_interface_review.md#j2-016) |
| 기존 심각도 | High（코드·기존 정책 충돌） |
| 그룹 | C |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | Gateway VCU Timeout / State / Recovery |
| 근거 파일·위치 / 문서 A(원문) | S02 POL-0016/POL-00712/POL-0038:age>30ms,VCUCriticalFAIL_SAFE,정상3회;S06 SYS_REQ_020/053/055. |
| 근거 파일·위치 / 문서 B(원문) | S01 VCU_CommandCM_도age>30ms. 최신Gatewayheader135/146는50ms/DEGRADED. |
| 실제 코드 동작·위치(원문) | RGW CheckCanSourceTimeout644–651는>=50ms/DEGRADED; MonitorAliveCounter524–538/567–601는첫회복에서CLEARED. |
| 충돌 또는 누락(원문) | 현재Firmware의Threshold·대표State·Recovery확인횟수가기존문서와다름. Runtime/HW재현은미수행. |
| 결정 질문(원문) | 적용할승인Fault정책/예외버전과같은기준의기존출력감시. PC입력Timeout으로사용금지. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. 문서의 age>30ms/FAIL_SAFE/정상3회와 고정 Gateway 코드의 >=50ms/DEGRADED/첫 회복 차이를 승인 근거와 적용 범위로 해소. 수치 선택을 이 문서에서 권고하지 않음. |
| 대안별 영향 / 영향 범위 | Gateway·VCU·Motor 안전 처리 및 Cluster/PC Fault_Status의 ACTIVE/CLEARED·대표 상태·회복 관측에 영향. 기존 Fault Event 의미/전파·회복 근거를 정리하되 새 Fault Code, threshold, retry 계약을 생성하지 않음. |
| 영향받는 ECU·Tool(원문) | Gateway, VCU, Motor, Cluster/PCFault표시 |
| 원본 담당자 | Gateway / Fault 정책 담당 |
| Primary Owner 제안 | Gateway / Fault 정책 |
| Reviewers(원문) | VCU, Motor, Cluster, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T07 |
| 완료 조건(원문) | 기준정책합의및코드/문서일치,경계·criticalstate·연속recovery테스트와전파증거. 승인전수치수정금지. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-017

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-017 원문](pc_driver_input_interface_review.md#j2-017) |
| 기존 심각도 | High（Source Format 계약 불일치） |
| 그룹 | C |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | Gateway STD/EXT/RTR 수신 식별 |
| 근거 파일·위치 / 문서 A(원문) | S01/S02기존6개Message는STD. CAN ID는Format과같이식별해야함. |
| 근거 파일·위치 / 문서 B(원문) | RGW main.hCanRxMessage_t41–46에는숫자id/dlc/data만있음. |
| 실제 코드 동작·위치(원문) | RGWfilter128–144all-mask;RXcallback1158–1167는STD/EXT를같은id로축약하고RTR도버림;ProcessCanMessage1116–1138는숫자switch. |
| 충돌 또는 누락(원문) | 같은숫자EXT/RTR의기존STD데이터메시지분류를막는metadata/guard가해당경로에없음. 정적확인,실기재현NOT RUN. |
| 결정 질문(원문) | 허용Format/FrameType검증위치·보존방식·테스트기준. 일반CanRxMessagepublic변경은담당자승인대상. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. Format/FrameType 검증 위치와 metadata 보존 방식을 Gateway/CAN 및 public interface 담당자가 정하도록 요청. 새 STD/EXT/RTR 허용 규칙을 정의하지 않음. |
| 대안별 영향 / 영향 범위 | RX filter→Callback→queue public 구조체→숫자 ID 분류 경로 전체와 동일 수치 STD/EXT·RTR 회귀에 영향. 단순 숫자 ID 대조로 동일 Message라 판단할 수 없음. |
| 영향받는 ECU·Tool(원문) | Gateway, CAN consumer정합성, PC/VCU통합시험 |
| 원본 담당자 | Gateway / CAN |
| Primary Owner 제안 | Gateway |
| Reviewers(원문) | VCU, PC/Test 및영향받는publicinterface담당 |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T08 |
| 완료 조건(원문) | STD/EXT동일수치·RTR사례의분류/거부회귀증거,공개계약리뷰. 이번에는코드변경없음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-018

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-018 원문](pc_driver_input_interface_review.md#j2-018) |
| 기존 심각도 | High（Production 정책 누락） |
| 그룹 | A |
| 현재 상태(원문) | Open |
| 관련 Interface(원문) | 입력 권한 / 충돌 / ECU 응답 확인 |
| 근거 파일·위치 / 문서 A(원문) | S00 결정_이슈IF-08·IF-04는Open. PC/로컬/테스트입력권한과ECUack미정. |
| 근거 파일·위치 / 문서 B(원문) | S07§9.1은VCU책임;S06 SYS_REQ_045/059는Windowlocal책임;원격PC와의전체중재계약없음. |
| 실제 코드 동작·위치(원문) | S09 MockReceipt및ECU_RESPONSE_STATUS18/111–113은별도. Source변경229–238은PC메모리정리일뿐. |
| 충돌 또는 누락(원문) | Mock수락을실제실행으로판정할계약이없고PC종료/reset을안전정지로볼수없음. |
| 결정 질문(원문) | 권한/모드전환/중복·재연결·동시제어중재,수락vs실행·실제상태응답/로그correlation방법. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. PC/로컬/다른 테스트 입력 권한, 재연결·중복·동시 제어, 수락/실행/상태 응답의 계약을 역할별로 합의. |
| 대안별 영향 / 영향 범위 | PC Apply/Reset/Source 변경은 메모리 동작. Mock Accepted는 실제 ECU 수락/실행/Fault 해제 증거가 아님. VCU·Gateway·Body 중재와 PC 로그 상관, 테스트 모드/송신 권한 Gate에 영향. |
| 영향받는 ECU·Tool(원문) | PC, VCU, Gateway, Body, 통합Test |
| 원본 담당자 | 시스템 / VCU / Gateway / PC |
| Primary Owner 제안 | 시스템 |
| Reviewers(원문) | Door, Light, Window, CAN·LIN, Motor/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T03 / J2-T04 |
| 완료 조건(원문) | 승인된시나리오/상태·수락/실행구분·팀별책임,추후송신승인Gate. Mock Accepted는ECU응답아님유지. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

### J2-019

| 항목 | 내용 |
|---|---|
| Issue ID | [J2-019 원문](pc_driver_input_interface_review.md#j2-019) |
| 기존 심각도 | Low（기존 설명 표기 차이） |
| 그룹 | B |
| 현재 상태(원문) | 검토 필요 |
| 관련 Interface(원문) | LIN Door RequestState bit length |
| 근거 파일·위치 / 문서 A(원문) | S03 검토 항목row8의A1설명은RequestState2bit라고서술. |
| 근거 파일·위치 / 문서 B(원문) | S03 Signal 상세35, S02 LIN_Signal_Definition10, S05 RequestState40/79는1bit. |
| 실제 코드 동작·위치(원문) | 현재Door/GatewayLINhandler없음. 이불일치를수신코드가해결했다고볼수없음. |
| 충돌 또는 누락(원문) | 보조검토문구와실제필드표/DB간길이표기불일치. |
| 결정 질문(원문) | 보조설명동기화와정식필드표의승인범위. |
| 가능한 대안 / 결정 대상 | 담당자 결정 필요. S03 검토 문구 2bit와 실제 Signal 표/LDF 1bit를 승인 범위에 맞게 설명 정합화. 새 bit length 대안을 만들지 않음. |
| 대안별 영향 / 영향 범위 | Door/Gateway/LIN 문서·Test 기준에 영향. 원문 Low를 유지하며 현행 Signal 필드를 임의 변경하는 구현 이슈로 확대하지 않음. |
| 영향받는 ECU·Tool(원문) | Door, Gateway, LIN문서/Test |
| 원본 담당자 | 통신문서 / Door / LIN Common |
| Primary Owner 제안 | 통신문서 / LIN Common |
| Reviewers(원문) | Gateway, PC/Test |
| 승인 필요 여부 | 필요 — 해당 기준/계약 또는 변경 범위의 담당자 및 상대 담당자 리뷰·승인 증적 필요. 현재 미승인 / 결정 Pending. |
| Jira Task 후보(원문) | J2-T09 |
| 완료 조건(원문) | 문구·Signal표·LDF비교와담당자검토증거. 여기서1/2bit를새로확정/수정하지않음. |
| Decision / Reviewer / Date / Evidence(원문) | 미입력 / 미입력 / 미입력 / 승인 증적 미확보 |

## 7. 리뷰 승인 체크리스트

각 Issue의 검토 진행과 결정 결과를 별도로 기록한다.

| 상태 | 기록 기준 |
|---|---|
| Reviewed | 담당자가 실제 근거와 영향 범위를 검토하고 참여자·날짜·검토 증거를 남김. 승인 의미 아님 |
| Approved | 정해진 범위의 결정 담당 역할과 필요한 상대 담당자가 승인하고 결정·날짜·증거를 남김 |
| Rejected | 제안 거부 및 사유·영향·후속 작업을 기록. 다른 후보의 자동 승인 아님 |
| Needs Change | 수정 요구와 재검토 조건/담당을 기록. 수정 완료 전 승인 아님 |
| Pending | 아직 결정 또는 필요한 증거가 없음. 초기 19개 모두 이 상태 |

Reviewed는 별도의 체크박스다. 결정 결과는 Approved / Rejected / Needs Change / Pending 중 하나를 표시한다.
검토 후 결정 대기 중이면 Reviewed와 Pending이 동시에 표시될 수 있다.
Approved는 리뷰 참여·증적 없이 체크하지 않으며, 적용 범위·버전이 바뀌면 해당 결정의 재검토 여부를 남긴다.
아래 결정 담당 역할의 제안값은 §6에서 참고하고, 실제 담당 역할·참여자는 회의 시 확인해 입력한다.
기존 S05 일부 승인 문구나 SW 테스트 결과를 이 양식의 승인 증거로 대체하지 않는다.

공통 검토 절차:

- [ ] 원본 ID·심각도·상태 및 고정 버전 근거를 확인했다.
- [ ] 충돌/누락과 해당 기능의 영향·대안을 검토했다.
- [ ] Primary 조정 역할과 실제 산출물 Owner·상대 담당자를 확인했다.
- [ ] 미정 입력/Protocol 값과 실제 변경 제안을 구분했다.
- [ ] 결정·Jira·수정 산출물·증거·후속 검증을 아래 해당 Issue에 연결했다.
- [ ] Review/승인/구현/Mock 테스트/Hardware/Integration Merge/Jira Done을 별도로 기록했다.

### 7.1 Issue별 회의 기록

초기값의 '미입력'은 실제 결정 기록이 없다는 의미다. 승인 날짜/실명/실제 Jira Key는 추정하지 않는다.

#### Review J2-001

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: 시스템 / CAN·LIN 기준 산출물) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T01 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-002

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: CAN Interface) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T01 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-003

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: VCU) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T02 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-004

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: VCU / 시스템 안전 정책) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T03 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-005

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: VCU) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T02 / J2-T03 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-006

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: 시스템) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T04 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-007

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Window) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T04 / J2-T06-WINDOW 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-008

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Door) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T04 / J2-T06-DOOR 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-009

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Light) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T04 / J2-T06-LIGHT 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-010

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: VCU / Gateway / CAN) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T04 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-011

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Gateway / LIN Common) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T09 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-012

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Gateway (Master) / 각 Body ECU (Slave)) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T06-MASTER / DOOR / WINDOW / LIGHT 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-013

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: CAN) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T05 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-014

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: CAN) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T05 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-015

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: CAN) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T05 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-016

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Gateway / Fault 정책) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T07 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-017

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: Gateway) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T08 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-018

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: 시스템) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T03 / J2-T04 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

#### Review J2-019

| 기록 항목 | 팀 입력 |
|---|---|
| 검토 진행 | [ ] Reviewed |
| 결정 결과 | [ ] Approved / [ ] Rejected / [ ] Needs Change / [x] Pending |
| 결정 내용·사유·적용 범위/버전 | 미입력 |
| 결정 담당 역할 | 미입력 (제안: 통신문서 / LIN Common) |
| 리뷰 참여자·역할 | 미입력 |
| 결정 날짜 | 미입력 |
| 관련 Jira Issue | 미등록 — 초안 J2-T09 참조 |
| 수정 대상 산출물·영향 ECU | 미입력 — §6의 근거·영향을 검토 후 확정 |
| 승인 증적 | 미확보 |
| 후속 작업·담당 역할·재검토 조건 | 미입력 |

## 8. Jira Task 초안

아래는 원본 §12의 **12개 등록 전 후보**다. 실제 Jira Key가 아니며 외부 등록·담당 배정·상태 변경을 수행하지 않았다.
원본 J2-001~019를 추적하는 작업 묶음이며 새로운 리뷰 Issue를 추가하지 않는다.
크기는 기존 1~3일 제안으로 유지한다. 승인·실기 준비 대기 시간이나 전체 Firmware 개발 기간을 확정한 값이 아니다.
각 Task의 실제 담당자 1명과 일정은 팀이 배정한다. 범위가 커지면 별도 승인 후 구현/검증 Task를 분리한다.

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


### 8.1 등록 시 포함할 의존성·산출물·증거

| 후보 | 연결 Issue / 선행 조건 | Input / Output·완료 증거 |
|---|---|---|
| J2-T01 | J2-001/002; 시스템/CAN의 공식 기준·registry 제공 | 입력: S00/S01/S02/S03 및 실제 전체 예약 대장. 출력: 기준 버전/권한·후보 검토·승인 범위와 참가자/날짜/Evidence |
| J2-T02 | J2-003/005; T01 기준과 T03 안전·권한 정책 연계 | 입력: 미정 PC 입력 의미와 VCU 책임. 출력: 입력/유효성/encoding 계약 표, VCU 구현 소스·버전·검증 계획 및 상대 담당자 승인 |
| J2-T03 | J2-004/018, 관련 J2-005; T01/T02/T04와 상호 검토 | 입력: freshness/연결·충돌/응답 질문. 출력: 주기·Timeout·신뢰성 필요성·권한·수락/실행/실제 응답 시나리오와 승인 증거 |
| J2-T04 | J2-006~010/018; T01, T02/T03와 경로 합의 | 입력: S00 경로 후보, S04 Pending 및 Body 정의. 출력: 기능별 Source/해석/중재/Destination/상태 경로·수정 대상·상대 담당자 승인 |
| J2-T05 | J2-013/014/015; T01 기준 권한 | 입력: S02/S03 ↔ S01 및 consumer 해석. 출력: 6개 차이의 결정/근거·정상/Reserved/Invalid/15→0 기준 및 후속 동기화/회귀 계획 |
| J2-T06-MASTER | J2-012; T04/T09 및 승인된 CAN/LIN 정의 선행 | 입력: 확정될 Source/Frame/Signal/Schedule. 출력: Gateway Master 구현 범위·위치·응답/오류/캐시 책임과 SW/Bus evidence 계획 |
| J2-T06-DOOR | J2-008/012; T04/T09 및 Master 계약 연계 | 입력: 승인된 LockCommand/RequestState 의미. 출력: 유지/원샷·중복·구동 종료·실제 상태 계약과 Door 검증 계획 |
| J2-T06-WINDOW | J2-007/012; T04/T09 및 S06 local safety 선행 | 입력: Window 경로/로컬·원격/limit 정책. 출력: 하위 Local Timeout parameter 추적·STOP/재개/limit 검증 계획 |
| J2-T06-LIGHT | J2-009/012; T04/T09 및 Master 계약 연계 | 입력: 개별 Lamp/자동 연동/priority 결정. 출력: Light 최종 출력 책임과 실제 상태 비교 계획 |
| J2-T07 | J2-016; T01 기준 및 기존 Fault 정책·consumer 리뷰 | 입력: S02/S06 ↔ RGW threshold/state/recovery 차이. 출력: 적용 정책·버전/예외·ACTIVE/CLEARED 전파·경계/회복 검증 계획. PC 입력 Timeout과 분리 |
| J2-T08 | J2-017; T01 기준, Gateway/CAN/public contract 리뷰 | 입력: RGW 수신 metadata/분류 경로. 출력: Format 보존/검증 위치 결정과 동일 수치 STD/EXT·RTR 구분/거부 회귀 기준 |
| J2-T09 | J2-011/019; T01 기준, T04 및 LIN/각 Body 리뷰 | 입력: S02/S03/S04/S05. 출력: 운용/참고·Frame ID/PID·RequestState 설명의 결정/수정 대상과 후속 timing/checksum Capture 계획 |

각 후보의 Purpose/Actual vs Expected/근거/영향/담당·Reviewer/Acceptance Criteria는 §6의 원본 Issue와 연결한다.
Approval 산출물과 SW/Hardware 테스트 결과는 별도로 첨부한다. 제안값이 정해지기 전에 숫자 입력 Frame이나 기대 Payload를 작성하지 않는다.
확인된 문서/코드 차이는 정적 분석 근거로 등록하며 Runtime/HW 재현을 했다고 쓰지 않는다.

## 9. 승인 후 산출물 변경 순서

현재 단계에서는 아래 절차를 실행하지 않는다. 문서 작성은 구현/송신/Git 업로드의 추가 승인이 아니다.
핸드북 §4.2/§5.5/15장과 CONTRIBUTING §5의 **Jira → Matrix/Schedule → 상대 담당자 리뷰 → DBC/LDF → 코드 → PR → 검증 증거 → Done** 순서를 따른다.
요청한 1단계의 Interface Decision 기록은 결정 질문·회의 결과와 범위를 남기는 단계이며,
관련 Jira/기준 표 리뷰를 생략하고 신규 Interface를 먼저 확정하는 단계가 아니다.

| 순서 | 승인 후 수행할 일 | 담당·통과 증거 |
|---|---|---|
| 1 | Interface Decision 기록 | §7에 근거 버전·결정 범위·참여자·날짜·Evidence 기록. 미승인 초안과 승인된 범위를 명시 |
| 2 | Jira Issue 등록 및 상대 담당자 리뷰 계획/요청 | 별도 등록 승인 후 실제 Key 연결, Owner/Reviewer/완료 조건/의존성 지정. 새 값 변경 전 변경 통제 시작 |
| 3 | CAN Matrix / 메시지 정의서 갱신 및 상대 담당자 리뷰 | 승인된 변경 요청에 대한 표의 변경안 작성·구/신 값·영향/전환 계획 대조. 독립 Matrix 부재 시 먼저 기준 권한 해결. CAN/LIN 계약 승인 증거 확보 후 DB 반영 |
| 4 | DBC 갱신; 해당되는 LIN Matrix/Schedule/LDF 동기화 | CAN 담당·송수신 ECU·Gateway 및 LIN Common/Body 리뷰. 표 ↔ DB의 ID/DLC/encoding/enum/유효성·주기 정합성 검증. LDF 기존 승인 범위를 전체 Freeze로 확대 금지 |
| 5 | Gateway / VCU / LIN Routing 및 Firmware 반영 | 각 소유자가 승인 Source/Destination·VCU 계산/권한·Master/Slave·local 안전·Fault를 반영. Routing 후보와 실제 구현을 동기화 |
| 6 | PC DBC Encoder / CAN Sender 반영 | 별도 소스 변경 승인 후 승인된 DB·입력 권한·응답/로그 계약만 사용. PC가 VCU_Command 또는 TorqueRequest를 대체 송신하지 않음 |
| 7 | Mock 통합 테스트 | 정상/invalid·중복/단절/재연결·충돌/실제 상태 구분·STD/EXT/RTR·Fault 전파/회복 검증. Mock PASS는 Hardware PASS 아님 |
| 8 | Hardware CAN 통합 검증 | 별도 송신 승인과 물리 Gate 충족 후 CANable/ECU·CAN/LIN Capture·실제 출력·고장/회복 검증. 미실행 항목 NOT RUN / NOT VERIFIED |
| 9 | 공통 DoD 및 기능별 DoD 점검 | 핸드북 §15.6, CONTRIBUTING §9의 Build/Flash/Boot/Bus/정상·경계·Fault/Review/문서/Evidence 확인. PR Review/Integration Merge/Jira Done은 각각 별도 승인·절차 |

실제 작업 Branch/PR/Commit 정책은 향후 작업 승인 시 팀 규칙에 맞춰 확인한다.
이번 문서 작업에서는 기존 PC-Diagnostic-Test를 유지하고 신규 Branch나 Git 작업을 만들지 않는다.
모든 구현 변경은 관련 Jira/기준 산출물/상대 담당자 승인 증적에 연결한다.

## 10. Open 및 Blocked 항목

| 항목 | 현재 상태 | 해소에 필요한 근거 |
|---|---|---|
| 원본 19개 Issue의 팀 결정 | Pending, 원본 심각도·상태 유지 | 각 Issue의 §7 결정 담당·Reviewers·날짜·Jira·승인 증적 |
| 공식 Baseline / Interface Freeze | 검토 필요, Freeze 승인 미확보 | J2-001의 기준 권한·승인 범위·버전 연결. 파일명/FIX/일부 Frozen만으로 전체 승인 불가 |
| PC_Driver_Input / 0x600 / STD 후보 | 초기값-수정 가능 / 미승인 | 전체 registry/예약·노드 및 Format 검토, 신규 정의 필요 여부/승인 |
| PC DLC / Payload / Signal | TBD | Accelerator/Brake/Gear 이름·단위·layout·length·order·signed·scale·offset·initial/invalid·validation의 정식 계약 |
| PC 주기 / Timeout / Fail-safe / Alive / Payload Checksum | Open | VCU/시스템 안전 정책·관련 ECU 결정. 기존 VCU 30/50ms나 LIN checksum 전용 금지 |
| VCU 구현·Body 경로·Local 안전·실제 응답 | Open / 검토 필요 | 고정 근거 밖 구현이 있으면 소스/Commit·계약 제공, 기능별 소유권/중재/상태·응답 승인 |
| Routing Byte3 후보 / LIN Schedule·PID | 검토 필요 / Pending Review | S04 후보와 실제 DB/표/코드의 동기화 및 승인, Frame ID와 PID 구분/후속 Capture |
| 기존 6개 CAN 메타데이터 차이 | 검토 필요 | J2-013/014/015 결정·consumer 영향/회귀 기준 |
| Gateway Fault / Source Format | 검토 필요 | J2-016/017의 정책·metadata/public contract·전파/회복 검토 |
| 실제 PC Driver CAN 송신 | BLOCKED | §11 조건과 별도 구현/송신 승인. 기존 Sender API 존재만으로 해제 불가 |
| 실제 CANable/ECU·배선/전원/Flash 버전 | NOT VERIFIED | 사용자가 Hardware 미연결로 보고한 상태 유지. 실제 연결/Frame 수신/Decode/제어 시험 NOT RUN |
| 팀 고정 라이브러리·배포/Fixture 재배포 승인 | 미확정 | 해당 승인 담당자/범위/날짜/Evidence; 이 패키지에서 자동 승인하지 않음 |
| 담당자 코드 리뷰·Integration Merge·Jira Done | NOT VERIFIED / 미실행 | 실제 상대 담당자 승인·통합 및 DoD evidence와 별도 상태 전환 |

이번 재대조에서는 원본의 19개 ID/근거와 다른 새로운 리뷰 Issue를 추가하지 않았다.
임시 Excel의 Window→Door, Routing Source 부재, 메타데이터/Fault 차이는 원본에 이미 기록된 충돌이다.
원본의 Low J2-019를 새 CAN bit layout 정의나 구현 결함으로 확대하지 않는다.
승인된 범위가 좁다면 미해결 항목과 적용 제외/후속 결정을 역할·근거로 명시해야 하며,
해당 송신에 필요한 ID/Payload/권한/안전 계약을 미정 상태로 둔 채 승인할 수 없다.

## 11. 실제 CAN 송신 허용 조건

현재는 어떤 항목도 완료 체크하지 않는다. 이 체크리스트는 송신 허가 자체가 아니다.

- [ ] J2-001/002의 기준 권한·전체 ID/예약 대장·Source Format 및 PC 메시지 필요성에 승인 증적이 있다.
- [ ] J2-003의 DLC/Payload/encoding/enum/normal/initial/invalid/validation이 실제 표·DBC와 일치한다.
- [ ] J2-004/005/018의 VCU 입력 해석·Torque 계산/제한·상태 전이·권한·중복·단절/재연결·Timeout/Fail-safe·실제 응답 계약이 승인됐다.
- [ ] Body를 제어할 경우 J2-006~012/019의 Source/Destination·명령 의미·local 안전·Frame/Signal/Schedule/Routing과 실제 Firmware가 승인 버전으로 연결된다.
- [ ] 기존 CAN 메타데이터 J2-013~015, Gateway Fault J2-016 및 STD/EXT/RTR J2-017의 관련 영향과 승인 범위를 해결했다.
- [ ] VCU_Command(0x100)는 VCU 출력으로 유지하고 PC가 TorqueRequest/기존 출력 메시지를 대체 송신하지 않는다.
- [ ] PC 송신 구현을 별도로 승인받고 코드 리뷰·입력 검증·Mock 통합 회귀 증거를 확보했다.
- [ ] 실제 CANable/ECU, 트랜시버·배선·전원·종단/GND/절연·노드/Bitrate·Flash 버전을 확인하고 해당 실기 시험 계획·권한을 승인받았다.
- [ ] Mock Accepted와 실제 ECU 수락/실행/상태/Fault를 구분해 관측·로그할 승인 계약이 있다.
- [ ] 시험 범위/안전 정지·실패/복구 책임 및 사용자 명시적 실제 CAN 송신 승인이 있다.

송신 Gate를 통과하더라도 실제 Hardware PASS나 Integration Merge/Jira Done을 미리 선언하지 않는다.
PC Apply/Reset/Close를 차량 정지나 Fault 해제 증거로 사용하지 않는다.

### 11.1 이 문서 작업의 검증 범위

기존 Source/Test 및 Interface 파일은 변경 대상이 아니다.
원본 19개 ID·심각도·상태·A/B/코드 근거·기존 담당·완료 기준의 보존,
그룹 분류·P0 연결·승인 양식·Markdown 링크/표/whitespace 및 Git 범위는 정적으로 검사한다.
작업 전후 SHA-256으로 원본 리뷰/임시 Excel/추적 파일·D: 원본 25개·기존 Worktree 자료를 대조한다.
세부 실행 결과는 작업 후 보고에 남긴다.

pytest / CLI / Native Smoke는 이번 문서 단계에서 **NOT RUN**이다.
원본에 적힌 과거 테스트 결과는 이전 기록이며 이번 검증 결과로 사용하지 않는다.
Firmware Build/Flash/Runtime/실제 CAN 송수신/Hardware 검증 역시 **NOT RUN / NOT VERIFIED**다.
팀 Reviewed/Approved·담당자 코드 리뷰·Interface Freeze 승인은 미확인 상태를 유지한다.
Git add/Commit/Push/PR/Merge 및 Jira 외부 등록/Done을 수행하지 않는다.

### 11.2 Phase 3J-2B 정적 검증 결과 (2026-10-16)

| 검사 | 실제 결과 / 제한 |
|---|---|
| 원본 Issue / 필드 | J2-001~019 중복·누락 없음, 원본 14필드 × 19개 = 266개 값 동일 |
| 분류 / 우선 결정 | A 5개 / B 8개 / C 6개, P0 안건 8개. 원본 심각도·상태 유지 |
| 팀 승인 양식 | Issue별 19개, 모두 Pending. Reviewed/Approved 체크 없음 |
| Markdown | 표 열 수·로컬 파일/Issue 앵커 링크 53개·문서 전체 whitespace 검사 통과 |
| 원격 근거 링크 | 고정 Commit 원문 10개 HEAD 조회 HTTP 200. 브랜치 최신성/Runtime 검증과 별개 |
| git diff --check | 종료 코드 0. 미추적 문서는 별도 전체 whitespace 검사로 보완 |
| 보호 대상 | Worktree 추적 431개 / 기존 Repository 추적 446개 / D: 원본 25개 SHA-256 동일 |
| 원본·상태 보존 | 원본 리뷰·임시 Excel·기존 리뷰 SHA-256 동일. 다른 Worktree HEAD/Status·Git refs 동일 |
| 최종 변경 범위 | 새 체크리스트 1개만 추가, 기존 미추적 원본 리뷰 유지. Stage 비어 있음 |
| pytest / CLI / Native / Hardware | 이번 단계 NOT RUN. Hardware·담당자 코드 리뷰 NOT VERIFIED |

문서 준비 검증은 **PASS_REVIEW_PREP**다. 실제 팀 의사결정·Interface 승인·Live 송신 준비 완료를 의미하지 않는다.
