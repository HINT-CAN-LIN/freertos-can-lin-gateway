# VCU ECU Implementation Rules

## Current scope
Implement VCU ECU firmware only.

Current production CAN interface is the actual current DBC.

VCU_Command:
- CAN ID: 0x100
- Period: 10 ms
- Current implemented signals:
  - TorqueRequest
  - Gear
  - Brake
  - AliveCounter
  - DoorLockRequest
  - WindowCommand

## Important interface rule
The following signals are design decisions for a future DBC revision and
MUST NOT be implemented unless the DBC has been updated and explicitly approved:
- HeadLampRequest
- TurnLampRequest
- HazardLampRequest

Do not modify the DBC without explicit user approval.

## Architecture boundary
VCU:
- reads/mock driver inputs
- manages vehicle state
- calculates TorqueRequest
- generates VCU_Command
- transmits CAN

VCU MUST NOT:
- implement LIN
- implement CAN-to-LIN conversion
- generate Light_Command, Door_Command, or Window_Command
- implement Gateway routing logic

Gateway owns CAN-LIN routing.

## CAN rules
- Classical CAN
- Use actual DBC as source of truth for ID, DLC, bit position, scaling and enums.
- Do not duplicate DBC bit positions as unexplained magic numbers.
- Gear reserved/invalid values must not be treated as valid drive states.
- AliveCounter is modulo 16: 0..15..0.
- VCU_Command shall be transmitted every 10 ms.

## Development policy
Before modifying code:
1. inspect the repository
2. identify MCU and CAN peripheral (CAN vs FDCAN)
3. identify generated CubeMX/HAL code
4. identify build system
5. report assumptions and missing information

Do not invent missing hardware configuration.

Prefer small, reviewable changes.
Run available build/tests after each implementation step.
