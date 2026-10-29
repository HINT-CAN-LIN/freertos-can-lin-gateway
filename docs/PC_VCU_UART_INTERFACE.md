# PC GUI ↔ VCU UART interface

This is the VCU-side serial contract for the NUCLEO-F446RE board. The PC uses
the board's ST-LINK virtual COM port over the USB cable. The target MCU uses
USART2 at 115200 baud, 8 data bits, no parity, 1 stop bit (8N1). The default
Nucleo routing is PA2/USART2_TX to the ST-LINK VCP RX and PA3/USART2_RX from
the ST-LINK VCP TX.

## Driver input frame

All multibyte integers are little-endian. Version 2 input frames are fixed at
15 bytes; version 2 adds steering direction for the keyboard controls:

| Offset | Size | Meaning | Valid values |
| ---: | ---: | --- | --- |
| 0 | 1 | Sync byte 0 | `0xA5` |
| 1 | 1 | Sync byte 1 | `0x5A` |
| 2 | 1 | Protocol version | `2` |
| 3 | 1 | Message type | `0x01` (driver input) |
| 4 | 2 | PC sequence number | `0..65535`, wraps modulo 65536 |
| 6 | 1 | Valid-field mask | bit 0 ignition, 1 accelerator, 2 brake, 3 gear, 4 door, 5 window, 6 steering; at least one bit set |
| 7 | 1 | Ignition | `0` OFF, `1` ON, `2` RUN |
| 8 | 1 | Accelerator | integer percent `0..100` |
| 9 | 1 | Brake | `0` off, `1` on |
| 10 | 1 | Gear | `0` P, `1` N, `2` D, `3` R |
| 11 | 1 | Door lock request | `0` no action, `1` lock, `2` unlock |
| 12 | 1 | Window command | `0` stop, `1` up/close, `2` down/open |
| 13 | 1 | Steering direction | `0` center, `1` left, `2` right; bit 6 must be set |
| 14 | 1 | CRC-8 | CRC over offsets 2 through 13 |

CRC is CRC-8/ATM: polynomial `0x07`, initial value `0`, no reflection, final
XOR `0`. The mask lets a PC command update only fields explicitly configured;
other VCU inputs retain their previous values. The VCU starts with ignition OFF,
accelerator zero, brake off, gear P, door no-action, window stop, and steering
center. Steering is stored in VCU input state for receipt/validation only; the
current production DBC has no steering CAN signal, so this field does not enter
`VCU_Command` or Gateway traffic.

## VCU acknowledgement

The VCU responds to each complete input frame with an 8-byte version 2 frame:

`A5 5A 02 81 seq_low seq_high status crc`

The sequence is copied from the input. Status values are `0` accepted, `1` bad
version, `2` bad message type, `3` bad CRC, `4` invalid field mask, `5` invalid
signal value, `6` bad length, and `7` bad sync. The ACK means the VCU received and validated
the PC input packet; it does not prove that Gateway or downstream ECUs acted on
the requested command.

## Freshness and PC GUI operation

While the serial link is active, the PC sends the current input snapshot every
100 ms. If no valid input packet arrives for 500 ms, the VCU resets its driver
inputs to safe startup values. The PC Diagnostic GUI's Driver Control panel now
opens the ST-LINK Virtual COM Port, repeats the snapshot every 100 ms, and
shows the VCU ACK. Install the GUI's optional `uart` dependency (`pyserial`)
to use this path. Ignition starts OFF. ON indicates powered electronics but
keeps propulsion torque at zero; RUN enables torque calculation when gear is D
or R and brake is off. This is a conservative project assumption: the reviewed
handbooks do not define different behavior for the three ignition states.
Window `OPEN` maps to `WindowCommand=DOWN`;
`CLOSE` maps to `UP`. Light remains Mock-only and is not sent.

The current DBC `VCU_Command` includes `DoorLockRequest` and `WindowCommand` in
the final two bits of byte 3 (bits 4..5 and 6..7). After a valid UART update,
the VCU includes these requests in its standard CAN ID `0x100`, DLC 8 frame,
transmitted every 10 ms. The UART ACK confirms only packet receipt and
validation; it does not confirm Gateway reception or downstream actuation.

CAN1 is configured for Normal mode so frames can leave the MCU. The
NUCLEO-F446RE does not provide a CAN physical-layer transceiver: connect PA12
(CAN1_TX) and PA11 (CAN1_RX) to a compatible external transceiver, share GND,
and connect its CANH/CANL to the Gateway bus. The transceiver supply, bus
termination, and 500 kbps bitrate must match the actual Gateway hardware. Until
that hardware is connected, UART ACK proves only PC-to-VCU reception; it cannot
prove CAN delivery.
