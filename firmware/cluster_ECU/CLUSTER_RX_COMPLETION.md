# Cluster RX 누락 및 Value Table 수정 완료

2026-10-02. 대상 프로젝트: `C:\Users\sunma\OneDrive\Dokumen\GitHub\freertos-can-lin-gateway\firmware\cluster_ECU`.
첨부 DBC SHA-256 `d982916f61245e96518e422bc84fc59e0c9a121ea25cb19f227e901700e4fff4` 기준.

## 변경 내용

- `cluster_state.h/c`: VCU_Command 0x100 수신 모델·디코더 추가. TorqueRequest bit0/16, Gear bit16/3, Brake bit19/1, Alive bit20/4. Torque는 0.1 Nm 정수로 보관하며 raw0~40000 유효, 40001~65535는 유효하지 않음. Gear raw4~6 reserved,7 invalid를 그대로 보관합니다. VCU Command 데이터는 Gateway Vehicle_Status를 덮어쓰지 않습니다.
- Motor_Status RPM/Torque 개별 유효성 플래그 추가: RPM<=12000, Torque raw<=40000. FFFF를 정상값으로 사용하지 않음.
- WindowStatus: 0~5 정상 enum,6 RESERVED,FF INVALID,7~254 UNDEFINED로 구분. 화면에서 직접 확인 가능합니다.
- FaultCode NONE 프레임에 있던 node0+CLEARED 제한 제거. DBC가 허용하는 code0 조합은 metadata로 수신하지만, 어떤 조합도 전체 ACTIVE 표를 초기화하지 않습니다. code1~6의 해당 node CLEARED만 개별 해제합니다.
- `cluster_can.c/h`: 표준 data frame용 16-bit ID-list 필터 2개 bank로 100/110/120/200/300/310 정확히 수신. 다른 ID 및 IDE/RTR 필터 불일치는 제외합니다. DLC8 유효성은 Task 디코더에서 검사합니다.
- RX FIFO0 ISR에서 프레임·HAL 수신 시각을 CMSIS-RTOS2 queue에 복사합니다. queue64 entries이며 callback priority5에 맞게 timeout0 ISR API를 사용합니다. Task에서 최대64개를 drain하고 디코딩한 뒤 LVGL을 호출합니다.
- 큐 drop/FIFO overrun/CAN error는 진단 counter와 Fault-table uncertainty로 반영합니다. Gateway Fault를 Cluster가 임의 생성하지 않습니다. CAN error ISR도 LVGL을 호출하지 않습니다.
- 초기 전체 LCD 그림을 CAN 시작 전에 완료합니다. 이후 SPI는 blocking이며 과부하 상황에서 큐 유실 가능성을 drop counter로 확인해야 합니다. CANable 통합에서 실제 worst-case latency를 측정하세요.
- `.ioc` 핀맵은 유지합니다. CAN1 PA11 RX / PA12 TX, 500 kbps 설정. 새 코드는 독립 파일과 freertos USER CODE 블록에 있습니다.
- Cluster application TX 메시지는 추가하지 않았습니다. 이 DBC에는 Cluster 송신 메시지가 없습니다.

## 현재 모드와 CANable 단계

`Core/Inc/cluster_state.h`:

```c
#define CLUSTER_TEST_INPUT 1
```

**현재 다운로드된 값은1입니다.** 데모 유지, 실제 CAN 시작 안 함. CAN용 queue를 생성하고 copy self-test는 실행합니다. RX 하단의 C는 VCU Command, V는 Vehicle_Status, B Body, M Motor, G Gateway입니다. C 데이터는 현재 디코더/진단 상태로 보관하며 별도 TorqueRequest 숫자 UI는 없습니다.

CANable을 준비하면:

1. CAN 트랜시버·CANH/L·GND·양 끝 종단저항을 연결합니다.
2. `CLUSTER_TEST_INPUT`을0으로 바꿉니다.
3. CubeIDE Build 후 보드에 다운로드합니다. 화면 상단은 CAN RX로 바뀌고 데모 입력을 중단합니다.
4. CANable에서 standard11-bit,500 kbps,data,DLC8로 송신합니다.
5. 100/110은10 ms,120은20 ms,200/300은100 ms로 송신합니다. 310은 ACTIVE/CLEARED 전이 이벤트로 송신합니다.
6. RX C/V/B/M/G와 Queue/Fault 표시를 확인하고 특정 ID만 중단해 개별 freshness가 바뀌는지 검증합니다. 실제 CAN RX count/drop/error와 stack/heap도 함께 확인합니다.

stale1초/offline3초는 여전히 임시 화면 정책입니다. VCU timeout30 ms 및 Gateway의3회 복구 정책과 별개입니다. Cluster는 Motor의 안전 출력을 제어하지 않습니다. CAN 초기화 실패 시 `cluster_can_status`가 HAL_ERROR를 유지하고 LED가 빠르게 깜박입니다.

## 확인용 추가 payload

| ID | DLC8 hex payload | 기대 값 |
|---|---|---|
| 100 | D2 04 FA 00 00 00 00 00 | TorqueRequest123.4 Nm,GearD,BrakeON,Alive15 |
| 100 | D2 04 0A 00 00 00 00 00 | 같은 값,Alive0:15→0 정상 |
| 100 | 40 9C 1A 00 00 00 00 00 | Torque4000.0 Nm,Alive1,상한 유효 |
| 100 | FF FF 2A 00 00 00 00 00 | Torque invalid,Alive2 |
| 200 | 00 00 00 06 00 00 00 00 | Window RESERVED |
| 200 | 00 00 00 FF 00 00 00 00 | Window INVALID |
| 200 | 00 00 00 07 00 00 00 00 | Window UNDEFINED |

## 검증 범위

- DBC 정적 교차검증: 누락 RX0개,6개 메시지24개 신호의 bit position/length/byte order/factor 일치.
- 모델 startup self-test에 VCU decode,Alive15→0,40000 상한/40001 범위 초과/FFFF,DLC 오류,Window reserved/undefined/invalid,Motor validity,NONE metadata 처리를 추가했습니다.
- 최종 Debug build: 오류0/경고0. 보드 Flash verify/reset 완료.
- 최종 보드 RAM 관찰41회/약29초: 모델 및 CAN queue copy self-test PASS,uptime25→54초,RX 정상/stale/offline 및 Fault0/1/2개 변화 확인. SPI HAL_OK,stack overflow 없음,Task 스택 최소 여유3768 bytes,FreeRTOS heap 여유5608 bytes.
- 실제 CAN 버스, ISR→queue 전체 수신, 송신 주기, Gateway 상대 Fault E2E는 **CANable 연결 후 확인 필요**. 테스트 모드의 queue copy 검사로 실제 CAN 통신 성공을 주장하지 않습니다.

이 문서는 이전 `cluster_dbc_crosscheck.md`의 미구현 항목 및 이전 `cluster_spec_alignment.md`의 CAN 미연결 설명을 갱신합니다. 이전 문서는 당시 검토 기록입니다.
