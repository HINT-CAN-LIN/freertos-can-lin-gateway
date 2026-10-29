# Light ECU firmware

Current build: USB bench mode via ST-LINK VCP, USART2 115200 baud. See usb_test/README.md. Set LIGHT_USB_BENCH=0 in light_config.h to restore USART1 LIN slave (19200 baud, PA9 TX / PA10 RX).
Application interface follows network/lin/LIN__vehicle_body_final_ver1.0.ldf.
No RTOS is needed: interrupt-driven LIN transport and nonblocking foreground outputs.

## Build and run

Refresh light_ECU in STM32CubeIDE (F5), Build Project, then download/debug
Debug/light_ECU.elf using ST-LINK. main.c and stm32f4xx_it.c hooks are inside
CubeMX USER CODE sections. Keep User Code is enabled. Custom implementation
headers are included by main.c only, so CubeIDE need not rediscover new C files.
Do not call HAL UART receive/transmit functions on USART1: the custom ISR owns it.

## Default hardware profile

External indicator LED outputs are enabled (active HIGH):

| Function | Nucleo label | MCU pin |
|---|---|---|
| Head | D4 | PB5 |
| Left | D5 | PB4 |
| Right | D6 | PB10 |
| Reverse | D7 | PA8 |
| Brake | D9 | PC7 |

Each pin drives a 470-ohm series resistor and LED anode; LED cathodes connect
to common GND. PA5 still mirrors any active output. All outputs start LOW.
Mapping is in light_board.h and initialized by application code; these pins are
not represented as GPIO outputs in the .ioc. Reserve them when editing CubeMX.
SLP is held HIGH externally; LIGHT_SLP_CONTROL=0 means no MCU SLP output.
No physical lamp feedback exists: status reports logical commanded state.

User confirmed wiring on 2026-10-29. The manufacturer's module PDF contains
contradictory TX/RX descriptions versus its wiring diagram; use verified actual
signal direction, not label-based assumptions. Module VIN uses external 12V,
Nucleo uses USB, grounds are common. Slave INH remains open.

## Application protocol

Master sends BREAK, 0x55, protected ID. This node never generates a master header.

| Frame | ID | PID on wire | Response data |
|---|---|---|---|
| Light_Command | 0x12 | 0x92 | 1 data byte + enhanced checksum from master |
| Light_Status | 0x13 | 0xD3 | 2 data bytes + enhanced checksum from this slave |

Command byte: bit0 head; bits1..2 turn (0 off, 1 left, 2 right, 3 invalid);
bit3 hazard; bit4 reverse; bit5 brake. Reserved bits6..7 ignored.
Invalid turn command immediately turns all outputs off and sets diagnostic FAULT;
it does not refresh the valid-command timeout. A valid command recovers.
Hazard overrides left/right selection; invalid turn=3 is still rejected.

Status byte0: bit0 head, bit1 left, bit2 right, bit3 hazard, bit4 reverse, bit5 brake.
Hazard sets both left/right plus hazard (0x0E). Status represents logical lamp
activation independent of blinking phase. Byte1: bits0..3 alive; bits4..5 diagnostic
(0 normal, 1 startup/timeout warning, 2 invalid-command fault); bit6 response_error.
Reserved status bits are zero. Alive increments modulo16 after a complete response
with matching bus echo. Response errors latch until a successful status response.
No status is sent spontaneously. Unknown IDs and bad PID parity are ignored.

Project defaults (not yet system-approved safety requirements), light_protocol.h:
- No valid command for 250ms: all lamps off, diagnostic WARNING.
- Startup: all lamps off, WARNING until first valid command.
- Turn/hazard: 500ms ON / 500ms OFF, starting ON when selection changes.
- Partial header/response: 10ms frame deadline; recover on next BREAK.

Known on-wire examples (after BREAK):
- Head+reverse+brake ON: 55 92 31 3C.
- All OFF: 55 92 00 6D.
- Left ON: 55 92 02 6B.
- Hazard ON: 55 92 08 65.
- Status header: 55 D3 (master must release bus for slave response).
Send valid commands periodically, e.g. every 50ms as in the operational schedule.

## Scope and validation

Implemented: application frames, PID validation, enhanced checksum, BREAK sync,
UART error recovery, echo verification, nonblocking blink, timeout and status.
Not implemented: LIN diagnostic transport/NAD/product-ID/configurable-frame
services, sleep/wakeup management, autobaud, physical bulb diagnostics, watchdog.
This is an application-level bench firmware, not a LIN-conformance-certified stack.
HSI-derived 84MHz is retained; verify baud tolerance on actual hardware.

Verified 2026-10-29: ARM GCC 14.3 build/link without warnings; portable host tests
cover all 64 PIDs and single-bit corruptions, checksum carry, invalid commands,
blink/hazard, timeout/tick wrap, status, ISR parser, echo collision and recovery.
Register mocks test state transitions, not real USART flag timing or LIN wiring.
Run tests/run_tests.ps1 with GCC on PATH or -Compiler <gcc.exe>.

Hardware acceptance still required:
1. Download and confirm PA5 off at startup.
2. Send valid command every50ms; check steady and flashing outputs.
3. Poll 0xD3 and capture two data bytes/checksum and alive counter.
4. Stop valid commands: outputs off at250ms; bad checksum must not extend deadline.
5. Resume valid traffic and verify recovery; inject truncated frames/bad PID.
6. Confirm BREAK/RX/TC/echo timing with logic analyzer under full gateway schedule.
