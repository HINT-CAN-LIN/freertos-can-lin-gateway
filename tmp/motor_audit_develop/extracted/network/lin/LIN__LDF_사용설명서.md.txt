# `vehicle_body.ldf` 사용설명서

## 1. 문서 목적

본 문서는 LIN과 LDF를 처음 접하는 사용자가 `vehicle_body.ldf`의 구조와 사용 방법을 이해하기 위한 설명서입니다.

대상 파일: `vehicle_body.ldf`

주요 도구: Vector LDF Explorer 1.7.42

현재 문서 상태: 펌웨어 개발 전 진단 Interface Baseline 확정본. 실제 Slave/NCF 및 Bus 검증은 후속 단계.

## 2. LDF란 무엇인가

LDF는 **LIN Description File**의 약어입니다. LIN Bus에서 어떤 ECU가 참여하고, 어떤 Frame과 Signal이 오가며, Master가 어느 순서로 통신하는지 기록한 네트워크 설명 파일입니다.

LDF는 다음 정보를 설명합니다.

| 정보 | 의미 |
|---|---|
| Node | LIN Bus에 참여하는 ECU |
| Signal | 실제 데이터 의미와 bit 길이 |
| Frame | 여러 Signal을 담는 LIN 데이터 단위 |
| Schedule Table | Master가 Frame을 요청하는 순서와 시간 |
| Signal Encoding | 숫자 값을 사람이 읽는 상태명으로 해석하는 방법 |

LDF는 Firmware 자체가 아니며, LIN 통신을 자동으로 보장하는 파일도 아닙니다. Gateway Firmware, Matrix, Test와 함께 사용해야 합니다.

## 3. 이 프로젝트의 LIN 구성

| 항목 | 현재 설정 |
|---|---|
| LIN Protocol | 2.2 |
| LIN bitrate | 19.2 kbps |
| Master | Gateway ECU |
| Slave | Door ECU, Light ECU, Window ECU |
| 운용 Schedule | `BODY_10ms` |
| 참고 Schedule | `BASE_20ms` |
| 운용 주기 | 100 ms supercycle |
| 진단 속성 | Node_attributes 적용. Pre-Firmware 설계 기준 |

### 3.1 통신 방향

```text
Gateway ECU (LIN Master)
        |
        +-- Door ECU   (LIN Slave)
        +-- Light ECU  (LIN Slave)
        +-- Window ECU (LIN Slave)
```

LIN에서는 Master가 Schedule에 따라 Header를 시작합니다. 해당 Header의 Frame을 Publisher가 응답 또는 Data로 제공합니다.

예시:

- Gateway가 `Door_Status` Header를 요청합니다.
- Door ECU가 `DoorOpen`, `DoorLocked`, `DoorAlive`를 응답합니다.
- Gateway가 수신한 값을 CAN Body Status 또는 Fault 판단에 사용합니다.

## 4. LDF 파일을 위에서부터 읽는 방법

### 4.1 Global 설정

```ldf
LIN_description_file;
LIN_protocol_version = "2.2";
LIN_language_version = "2.2";
LIN_speed = 19.2 kbps;
```

의미:

- `LIN_protocol_version`: Bus가 사용하는 LIN Protocol 버전.
- `LIN_language_version`: LDF 문법 버전.
- `LIN_speed`: LIN 통신 속도.

### 4.2 Nodes

```ldf
Nodes {
  Master: Gateway_ECU, 10 ms, 1 ms ;
  Slaves: Door_ECU, Light_ECU, Window_ECU ;
}
```

`Gateway_ECU`가 Master이고 나머지 세 ECU가 Slave입니다.

- `10 ms`: Master Schedule time base.
- `1 ms`: jitter 목표값. 하드웨어 실측값이 아님.
- time base는 모든 Frame의 주기가 10 ms라는 의미가 아님. Schedule delay를 표현하는 기본 단위입니다.

### 4.3 Signals

Signal 선언 형식은 다음과 같습니다.

```ldf
SignalName: bit_length, initial_value, publisher, subscriber ;
```

예시:

```ldf
DoorOpen: 1, 0, Door_ECU, Gateway_ECU ;
```

해석:

| 항목 | 값 | 의미 |
|---|---|---|
| Signal 이름 | `DoorOpen` | Door가 열렸는지 나타내는 값 |
| bit length | `1` | 1 bit 사용 |
| initial value | `0` | 초기값 0 |
| publisher | `Door_ECU` | 값을 생성하는 ECU |
| subscriber | `Gateway_ECU` | 값을 받는 ECU |

현재 LDF의 주요 Signal은 다음과 같습니다.

| Frame | Signal | Bit 위치 | 길이 |
|---|---|---:|---:|
| Door_Status | DoorOpen | 0 | 1 |
| Door_Status | DoorLocked | 1 | 1 |
| Door_Status | DoorAlive | 2 | 4 |
| Door_Command | LockCommand | 0 | 2 |
| Door_Command | RequestState | 2 | 1 |
| Light_Command | HeadLamp | 0 | 1 |
| Light_Command | TurnLamp | 1 | 2 |
| Light_Command | HazardLamp | 3 | 1 |
| Light_Command | ReverseLamp | 4 | 1 |
| Light_Command | BrakeLamp | 5 | 1 |
| Light_Status | LampState | 0 | 6 |
| Light_Status | LightAlive | 8 | 4 |
| Light_Status | DiagnosticState | 12 | 2 |
| Window_Command | WindowCommand | 0 | 2 |
| Window_Status | WindowState | 0 | 3 |
| Window_Status | UpperLimit | 3 | 1 |
| Window_Status | LowerLimit | 4 | 1 |
| Window_Status | MotorState | 5 | 2 |
| Window_Status | WindowAlive | 8 | 4 |
| Door_Status | DoorResponseError | 7 | 1 |
| Light_Status | LightResponseError | 14 | 1 |
| Window_Status | WindowResponseError | 14 | 1 |

### 4.4 Frames

Frame 선언 형식은 다음과 같습니다.

```ldf
FrameName: frame_id, publisher, frame_size {
  SignalName, start_bit ;
}
```

예시:

```ldf
Door_Status: 0x10, Door_ECU, 1 {
  DoorOpen, 0 ;
  DoorLocked, 1 ;
  DoorAlive, 2 ;
}
```

해석:

- Frame 이름: `Door_Status`.
- LDF frame identifier: `0x10`.
- Publisher: `Door_ECU`.
- Data 영역: 1 byte.
- `DoorOpen`은 bit 0부터 저장.
- `DoorLocked`는 bit 1부터 저장.
- `DoorAlive`는 bit 2부터 4 bit 저장.

현재 Frame 목록입니다.

| Frame | LDF ID | Publisher | 길이 | 운용 주기 |
|---|---:|---|---:|---:|
| Door_Status | `0x10` | Door_ECU | 1 byte | 100 ms |
| Door_Command | `0x11` | Gateway_ECU | 1 byte | 100 ms |
| Light_Command | `0x12` | Gateway_ECU | 1 byte | 50 ms |
| Light_Status | `0x13` | Light_ECU | 2 byte | 100 ms |
| Window_Command | `0x14` | Gateway_ECU | 1 byte | 100 ms |
| Window_Status | `0x15` | Window_ECU | 2 byte | 100 ms |

## 5. 승인된 운용 Schedule: `BODY_10ms`

현재 운용 후보는 `BODY_10ms`입니다. 총 100 ms가 지나면 다시 처음부터 반복됩니다.

```text
0 ms   Door_Status
10 ms  Window_Command
20 ms  Light_Command
30 ms  Window_Status
40 ms  Light_Status
50 ms  Reserved/Idle 구간
60 ms  Door_Command
70 ms  Light_Command
80 ms  Reserved/Idle 구간
90 ms  Reserved/Idle 구간
100 ms 다시 Door_Status
```

LDF Schedule에서는 Idle을 별도 Frame으로 만들지 않습니다. 따라서 Idle 구간은 앞의 Frame delay를 늘려 표현합니다.

예를 들어 다음 부분은 다음과 같이 해석합니다.

```ldf
Light_Status delay 20 ms ;
```

`Light_Status`가 40 ms에 시작하고 다음 `Door_Command`가 60 ms에 시작하므로, 40~60 ms 구간 전체가 해당 Schedule slot입니다.

`Light_Command`는 20 ms와 70 ms에 두 번 등장합니다. 따라서 100 ms supercycle 기준으로 50 ms 주기를 만족합니다.

## 6. `BASE_20ms`는 무엇인가

`BASE_20ms`는 실제 `LIN_Matrix.xlsx`의 기존 Schedule을 참고용으로 보존한 Table입니다.

```text
0 ms   Door_Status
20 ms  Light_Command
40 ms  Light_Status
60 ms  Door_Command
100 ms 반복
```

이 Table은 다음 이유로 현재 운용 Schedule이 아닙니다.

- Window Frame이 없음.
- `Light_Command`가 100 ms에 한 번만 송신되어 50 ms 주기와 불일치.

Gateway Firmware와 Test는 승인된 운용 기준인 `BODY_10ms`를 사용해야 합니다. Matrix 동기화 및 **상대 담당자 리뷰 필요**입니다.

## 7. Signal Encoding

`Signal_encoding_types`는 숫자를 사람이 읽는 상태명으로 해석하기 위한 정보입니다.

예시:

```ldf
WindowCommand_Encoding {
  logical_value, 0, "STOP" ;
  logical_value, 1, "UP" ;
  logical_value, 2, "DOWN" ;
  logical_value, 3, "INVALID" ;
}
```

따라서 `WindowCommand=1`을 수신하면 PC Tool이나 분석 도구에서 `UP`으로 표시할 수 있습니다.

Encoding은 ECU의 안전 동작을 자동으로 구현하지 않습니다. 실제 Motor Stop, Limit 보호, Fault 처리는 Window ECU와 Gateway Firmware가 구현해야 합니다.

## 8. PID와 Frame ID의 주의사항

현재 LDF는 Matrix의 `0x10`~`0x15` 숫자를 LDF `frame_id`로 유지합니다.

LDF의 Frame ID와 실제 Bus에서 전송되는 protected PID는 parity 계산 관계가 있을 수 있습니다. 따라서 다음 항목은 실제 LIN Capture로 확인해야 합니다.

- Header의 protected PID.
- Frame ID와 parity bit 관계.
- Bus Analyzer가 표시하는 ID 형식.

문서 숫자만으로 실제 Bus Header 값을 확정하지 않습니다. **상대 담당자 리뷰 필요**입니다.

## 9. Checksum 정책

프로젝트 결정은 Application Frame에 **Enhanced checksum**을 사용하는 것입니다.

Canonical LDF 문법에는 Frame별 checksum type을 별도 field로 기록하지 않으므로, 다음 산출물이 같은 정책을 사용해야 합니다.

- LIN Matrix.
- Gateway Firmware.
- Door/Light/Window Firmware.
- PC Tool.
- Bus Test 및 Capture 분석.

실제 19.2 kbps Bus에서 checksum 정상/오류 Frame을 확인해야 합니다. **상대 담당자 리뷰 필요**입니다.

## 10. Node_attributes와 Diagnostic 속성

현재 LDF에는 펌웨어 개발을 위한 진단 속성 기준이 포함되어 있습니다.

| Node | NAD | Product ID | response_error |
|---|---:|---|---|
| Door_ECU | `0x05` | `0x0000, 0x0005, 255` | Door_Status bit 7 |
| Light_ECU | `0x06` | `0x0000, 0x0006, 255` | Light_Status bit 14 |
| Window_ECU | `0x07` | `0x0000, 0x0007, 255` | Window_Status bit 14 |

진단 timing 기준은 다음과 같습니다.

```text
P2_min       = 50 ms
ST_min       = 0 ms
N_As_timeout = 1000 ms
N_Cr_timeout = 1000 ms
```

이 값은 **Pre-Firmware 설계 기준**입니다. 실제 Slave Firmware 또는 NCF가 제공되면 NAD, Product ID, response_error bit와 일치하는지 확인해야 합니다.

`Diagnostic_signals`와 `Diagnostic_frames`는 별도 진단 범위로 관리하며, 현재 운용 Schedule에는 추가하지 않았습니다.

## 11. 실제 사용 순서

1. Vector LDF Explorer 1.7.42에서 `vehicle_body.ldf` Open.
2. Nodes에서 Gateway/ Door/ Light/ Window 역할 확인.
3. Frames에서 ID, Publisher, Data length 확인.
4. Signals에서 bit 위치와 길이 확인.
5. Schedule Tables에서 `BODY_10ms` 선택.
6. Gateway Firmware의 Header 송신 순서를 `BODY_10ms`와 일치.
7. 각 Slave가 자신의 Publisher Frame에 응답하도록 구현.
8. 19.2 kbps LIN Capture로 timing, protected PID, checksum, response를 확인.
9. Matrix, Firmware, PC Tool, Test 결과를 동일 Jira/PR에 기록.

## 12. 검증 상태

| 검증 항목 | 결과 |
|---|---|
| LDF 2.2 parser | Parser error 없음 |
| Static structure | PASS |
| Signals | 22개 |
| Frames | 6개 |
| Schedule | 2개, 각각 100 ms |
| Vector LDFReader | `HasErrors=False` |
| Vector consistency | `RunChecks=True`, Error 0건 |
| Node_attributes | Pre-Firmware 기준 적용 |
| 실제 Bus timing/PID/checksum | 하드웨어 Capture 필요 |

## 13. 관련 문서

- `vehicle_body.ldf`
- `LDF_검토보고.md`
- `LIN_Matrix.xlsx`
- `메시지 정의서_v0.3_점검완료.xlsx`
- `시스템 아키텍처 사양서.pdf`
- `freertos_can_lin_gateway_handbook_ko.pdf`

Interface 변경, Window 값, Schedule, PID, Checksum 변경은 모두 **상대 담당자 리뷰 필요**입니다.
