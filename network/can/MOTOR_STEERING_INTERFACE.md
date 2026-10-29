# Motor steering interface v0.7

2026-10-17: 사용자 요청에 따라 SteeringAngle을 VCU_Command Byte3..4에서 **Byte4..5**로 이동했다. 저장소 DBC와 Motor ECU 시험용 DBC는 동일 내용이다. 파일명은 기존 경로 참조를 위해 유지하며 내부 VERSION은 0.7이다. Downloads 원본은 수정하지 않았다.

| 0x100 VCU_Command, DLC8, Standard, 10ms | 비트 | 형식 |
|---|---|---|
| TorqueRequest | 0..15 | unsigned, 0.1Nm, 기존 유지 |
| Gear / Brake / AliveCounter | 16..23 | 기존 유지 |
| Byte3 | 24..31 | Body 명령 후보용으로 확보, 현재 스크립트는 0 송신; Motor는 해석하지 않음 |
| SteeringAngle | 32..47 | signed Intel16, 0.1도, -45..45도; 0=중앙, 음수=좌, 양수=우 |
| Byte6..7 | 48..63 | Reserved, 현재 스크립트는 0 송신 |

SteeringAngle raw 정상 범위 -450..450, invalid32767. 범위 밖 요청은 Motor local inhibit 대상이다. Byte3에 제안된 Head/Turn/Hazard/Door/Window 신호는 이 변경에서 활성화하지 않았다. 해당 후보의 Matrix/DBC/VCU/Gateway 검토는 별도다. 방향지시등과 조향은 다른 신호다.

0x110 Motor_Status 기존 RPM/TorqueApplied/MotorState/AliveCounter는 그대로다. 기존 시험 확장인 Byte5..6 SteeringTargetEcho, Byte7 low-nibble LocalFaultFlags 및 high-nibble FirmwareRevision도 저장소 DBC에 함께 반영했다. Echo는 실측 각도가 아니다. LocalFaultFlags bit0 timeout, bit1 Alive, bit2 invalid, bit3 RX queue/mutex loss.

**FirmwareRevision=4**, CANgaroo script **1.4**가 이번 Byte4..5 규격이다. revision3은 Byte3..4였으므로 새 script는 revision3의 구동/조향을 거부한다. 구버전 Raw TX, 구버전 workspace/script 및 별도 VCU 송신기도 동시에 사용하지 않는다. CAN 프레임 자체에는 송신기 버전 협상 필드가 없으므로 모든 VCU 송신기는 이 배치를 직접 따라야 한다.

예시: 전진25%, 좌20도, Alive0 → `10 27 02 00 38 FF 00 00`.

변경 적용 순서: IDE Refresh/Clean/Build → revision4 firmware 다운로드 → CANgaroo에서 script1.4와 변경 DBC 다시 Load → Measurement 시작 → interface 선택 → `status`에서 revision4/READY 확인 → `drive d 25 -20 5`.

핀 배치, PWM 보정, timeout, 복구 계수, CPU fault 처리, CAN bus-off 정책은 이 인터페이스 이동으로 변경되지 않았다. 이전 검토의 CPU fault 출력 차단/bus-off 복구 및 복구 계수 정의 문제는 남아 있다. 부팅 및 안전 정지 시 조향은 중앙이다. SG90 두 개는 현재 같은 논리 target으로 구동한다.

관련 정의서 정렬: 메시지 정의 Excel의 CAN_Byte_Layout에서 VCU_Command Byte4/5를 SteeringAngle LSB/MSB로, CAN_Signal_Definition에 start32/length16/Intel/signed/factor0.1/range±45를 반영해야 한다. Gateway Routing DEC-02의 Byte3 후보는 보존한다. 이 변경은 기존 PDF/Excel 원본을 재작성하지 않고 본 문서로 변경 사항을 추적한다. 팀 공유/검토나 원격 push는 수행하지 않았다.
