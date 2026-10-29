# VCU Phase 1/2 Bring-up

## Scope and baseline

STM32F446RET6 / HAL CAN1 (bxCAN), Classical CAN 500 kbps, USART2, FreeRTOS
V10.3.1 with CMSIS-RTOS2. The board is the NUCLEO-F446RE shown in the
bring-up setup; its ST-LINK USB connector provides the PC virtual COM port
through USART2 PA2/PA3. Serial settings are 115200 8N1. Follow root AGENTS.md.
Interface source:
`network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc`, internal version
`0.4 - review-ready interface proposal`, with the explicitly requested VCU
`DoorLockRequest` and `WindowCommand` signals added to the DBC on 2026-10-17.

VCU_Command 0x100 / DLC 8 / 10 ms includes TorqueRequest, Gear, Brake,
AliveCounter, DoorLockRequest and WindowCommand. These two body fields are CAN
requests consumed by Gateway; LIN command generation and Gateway routing remain
excluded. CAN1 runs in **Normal mode** to put VCU_Command on the physical bus.
The NUCLEO-F446RE requires an external CAN transceiver between PA11/PA12 and
CANH/CANL; its supply, termination, and 500 kbps bitrate must match the Gateway.

## Runtime path

`main -> MX_CAN1_Init + MX_USART2_UART_Init -> VCU_CAN_Start + vcu_serial_start -> RTOS`
`PC USB/VCP -> USART2 RX ISR/ring -> StartVCUCtrlTask/vcu_serial_task_run`
`-> decode + CRC/range check -> input store -> ACK on USART2 TX -> VCU input`
`-> StartVCUTxTask`
`-> vcu_task_run -> vcu_app_get_command -> vcu_driver_input_read`
`-> vcu_app_process_inputs -> vcu_command_encode`
`-> vcu_can_send -> HAL_CAN_AddTxMessage(hcan1)`.

- `vcu_driver_input_mock.c`: safe deterministic startup values: ignition off,
  accelerator 0%, P, brake false, door NO_ACTION, window STOP. No MCU input
  pins or physical door/window controls are assumed. Valid UART input fields
  replace only the explicitly present values; the 500 ms receive timeout resets
  all fields to these safe values.
- `usart.c`: CubeMX-generated HAL UART initialization for USART2 at 115200
  8N1 on PA2/PA3. `vcu_uart.*` retains the register-level byte RX/TX path and
  bounded RX ring buffer; no HAL receive operation is armed. The USART2 IRQ
  USER CODE block dispatches to `vcu_uart2_irq_handler()` and returns before
  the generated HAL handler so the ring buffer exclusively owns received bytes.
  Keep this dispatch and the `vcu_serial.h` include in `main.c` inside USER CODE
  regions when regenerating.
- `vcu_serial.*` and `vcu_serial_protocol.*`: fixed 15-byte PC input frame (protocol v2),
  CRC-8/ATM, signal validation, valid-field updates, 8-byte matching sequence
  ACK, parser recovery and input freshness timeout. Full byte layout and PC
  sender requirements are in `docs/PC_VCU_UART_INTERFACE.md`.
- `vcu_app.*`: validates gear and accelerator range, updates a debugger-visible
  vehicle state, and inhibits torque when ignition is off, the brake is on, or
  gear is P/N. For this simulation only, accelerator percentage maps linearly
  to the DBC TorqueRequest range 0..4000 Nm. The project requirements do not
  specify a calibrated pedal-to-torque map; replace this assumption when the
  VCU control policy is approved.
- `vcu_command.h`: shared CAN ID, DLC, cycle, alive modulo, DBC torque range
  and body-request range constants.
- `vcu_command_codec.*`: DBC ID/DLC/period, field positions, scaling,
  validation and encoding. Torque rounds to nearest 0.1 Nm. Gear 4..7,
  invalid door/window enum values, out-of-range/nonfinite torque and alive >15
  are rejected. Invalid body mock inputs are sanitized to NO_ACTION/STOP before
  encoding. Reserved bits/bytes are zero.
- `vcu_can.*`: standard CAN data header, nonblocking mailbox submission,
  bounded polling drain of self-received FIFO0 frames in loopback only.
- `vcu_task.*`: one owner of AliveCounter and diagnostics; immediate first
  transmission with alive 0, subsequent releases every 10 ticks at 1 kHz.
  Absolute `vTaskDelayUntil` releases avoid cumulative execution-time drift.
  Overruns are counted and the schedule rebased, without catch-up bursts.
- `freertos.c`: VCUCtrlTask runs the UART parser/ack worker. VCUTxTask evaluates
  the latest input snapshot every 10 ms. The input store uses a short critical
  section so the two tasks see consistent values.

HAL_OK means mailbox acceptance, not confirmed delivery. Alive increments
modulo 16 only after acceptance, so failed/busy submissions retain the next
counter. No blocking retries or out-of-period retransmit submissions occur.
Inspect `vcu_task_stats` in the debugger for accepted/busy/error/encode-error
counts, deadline misses and the next counter. Hardware CAN retransmission
remains configured by the existing CAN initialization.

## Build and automated verification

The checked-in CubeIDE Debug makefiles do not enumerate new source files.
`firmware/vcu_ECU/makefile.defs` adds missing objects using the existing
compile rule, and filters out objects already discovered after IDE regeneration.
Generated makefiles and objects.list are not edited.

Build with the CubeIDE ARM toolchain bin directory on PATH:

```sh
make -C firmware/vcu_ECU/Debug -B -j4 all
python3 tests/can/vcu_phase1/run_tests.py
```

Validation on 2026-10-17:

- Full forced rebuild, GNU Tools for STM32 14.3.rel1: PASS.
- ELF size after USART2 support: text 29120, data 96, bss 21224 bytes.
- Host tests compile actual VCU modules against HAL/RTOS boundary stubs
  using address/undefined-behavior sanitizers and warnings as errors.
- Coverage: known DBC payload, body request encoding and invalid enum handling,
  all normal torque raw values, invalid Gear,
  invalid/nonfinite torque, null arguments, reserved bytes, standard ID/DLC,
  input-to-state and torque gating (ignition, brake, P/N, D/R), invalid driver
  inputs, UART input/ACK layouts, CRC, sequence, masks, range rejection and
  safe partial input updates, loopback FIFO drain, safe startup defaults,
  35 cyclic submissions with
  alive wrap, RTOS tick wrap, busy/error submissions and execution overrun.
- Test runner also checks actual DBC signal layout, period and Gear/body request enums
  baseline to detect interface drift. No third-party Python packages needed.

## Hardware verification still required

No flash, real RTOS execution, physical TX-complete, or timing measurement
was performed. The host scheduler test checks requested releases, not real
interrupt latency or CAN arbitration. A busy mailbox, HAL failure or deadline
miss is visible in diagnostics and prevents a claim of uninterrupted delivery.

1. Connect a compatible CAN transceiver to PA12 (CAN1_TX), PA11 (CAN1_RX),
   common GND, and the Gateway's CANH/CANL bus. Confirm transceiver voltage,
   bus termination, and bitrate before running the 100 Hz command stream.
2. Connect the board's ST-LINK USB port to the PC. In the PC Diagnostic GUI's
   Driver Control panel, select the VCP serial port, configure at least one
   supported field, and connect at 115200 8N1. Verify the 100 ms input frames
   and matching 8-byte VCU ACK. Disconnect and confirm safe defaults after the
   500 ms receive timeout.
3. Ensure the Gateway (or another CAN node) is powered and ACKs frames.
4. Flash the firmware and inspect `vcu_task_stats`; confirm no sustained
   mailbox busy/error counts or deadline misses.
5. Capture standard 0x100, DLC 8, nominal 10 ms spacing with CANable and the
   current DBC. With torque 0, DoorLockRequest=NO_ACTION and WindowCommand=STOP,
   the first payload is `00 00 00 00 00 00 00 00`; byte 2 then cycles `10`,
   `20`, ..., `F0`, `00`. With Door LOCK and Window DOWN selected, byte 3 must
   be `90`. Bytes 4..7 remain zero.
6. Record measured timing/jitter, counters and capture evidence before marking
   hardware bring-up complete. Door/window requests arrive only over the PC
   serial protocol; no extra GPIO/ADC input configuration is assumed. Serial
   ACK confirms PC input acceptance by VCU only, not Gateway/ECU execution.
