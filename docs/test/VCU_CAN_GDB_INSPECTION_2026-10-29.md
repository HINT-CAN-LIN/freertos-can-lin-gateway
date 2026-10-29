# VCU CAN debugger inspection — 2026-10-29

Inspected NUCLEO-F446RE through ST-LINK GDB server 7.14.0 in attach mode.
No flash download or deliberate MCU reset was performed. Symbols: firmware/vcu_ECU/Debug/vcu_ECU.elf.

## Hardware breakpoint

A temporary hardware breakpoint at vcu_can_send was reached from:

- vcu_can_send
- vcu_task_run (vcu_task.c:23)
- StartVCUTxTask (freertos.c:219)

Current RTOS task: VCUTxTask. Encode errors, HAL submission errors, and deadline misses were zero.
CAN state was HAL_CAN_STATE_LISTENING; HAL ErrorCode was zero.
The project does not enable CAN error notifications, so HAL ErrorCode=0 does not establish bus health.
CAN ESR=0x00800033: last error ACK, TEC=128, error-passive, not bus-off.
All three CAN TX mailboxes had TIR=0x20000001 (standard ID 0x100, TXRQ pending).

## Reversible internal comparison

CAN BTR was temporarily changed in RAM/registers from 0x001E0004 to
0xC01E0004 (Silent Loopback: internal test, no external data transmission).
No firmware source change was needed.

| State | tx_accepted | tx_busy | ESR |
| --- | ---: | ---: | --- |
| Before test, Normal | 3 | 41045 | 0x00800033 |
| Silent Loopback | 906 | 41045 | 0x00000000 |
| Restored Normal | 909 | 44499 | 0x00800033 |

BTR was restored to 0x001E0004; test RX FIFO entries were released.
The GDB client detached and MCU execution resumed.

Conclusion: scheduling, encoding, mailbox submission, and internal CAN transmission work.
Normal-mode external transmission remains blocked by missing CAN ACK.
This result does not identify a particular wire, transceiver, or adapter as faulty.
CANable firmware/configuration and the external signal path remain candidates.

## IDE limitation

CubeIDE Debug Configurations repeatedly crashed in macOS AX attribute serialization
(CFStringGetLength / AXSerializeCFType). The inspection was therefore performed with
the same bundled ST-LINK GDB server and arm-none-eabi-gdb through the command line.
No successful IDE GUI debug session was established.

CubeIDE workspace was reopened after the inspection. No unverified attach profile was retained.

## CANable direct serial follow-up

CANViewer was not running at the follow-up. Direct pyserial access to
`/dev/cu.usbmodem205F387C38461` succeeded. Commands C, S6, M0, O were sent
sequentially. V returned `16e7497-dirty github.com/normaldotcom/canable2.git`.
Five seconds of direct USB reception yielded zero CAN frames. E returned
`CANable Error Register: 0`; upstream error.c shows this is a software error
bitmap, not the FDCAN protocol status or TEC/REC.

The source at commit 16e7497 maps S6 to 500 kbit/s. Its can_enable() sets Normal
mode, so a persistent listen-only selection does not explain this direct test.
Runtime has a dirty suffix; matching source does not prove the binary is identical.

With adapter retransmission disabled (A0), one DLC0 remote request r1000 was
submitted. No actuator data frame was injected. VCU register reads before/after:

- RF0R: 0x00000010 -> 0x00000010 (FIFO pending count zero both times).
- ESR: 0x00980033 -> 0x01A00033 (no valid reception; ACK error persists).
- BTR: 0x001E0004 both times.

This does not prove successful adapter transmission or identify a faulty component.
Adapter channel was closed and A1 restored afterward. No flash/source modification.
Further discrimination requires observing the VCU TX pin, transceiver bus output,
and adapter bus input with an oscilloscope/logic analyzer, or an independently
verified CAN node. Existing USB commands do not expose adapter FDCAN registers.

## Bidirectional isolation and timing comparison

User explicitly confirmed actuators disconnected and approved ID0x100 zero-data
DLC0/1/2/8 test transmissions.

- VCU Silent mode, adapter closed: PA12 and PA11 low in 0/500 samples.
- VCU Silent mode, CANable remote requests: PA12 low 0/500; PA11 low 5/500.
- A single CANable r1000 request was decoded by VCU: RF0R=0x11
  (one pending), RX RIR=0x20000002 (standard ID0x100, RTR), RDTR=0.
- VCU-generated remote request received directly over CANable USB as r1000.
  Mailbox TXOK was set. Thus neither direction is completely disconnected.
- VCU zero-data frames: DLC0 and DLC1 were observed; DLC2 and DLC8 were not
  observed in the initial bounded tests. This alone was not a repeatability test.

A separate timing comparison used existing application periodic frames, discarded
USB buffered data after 300 ms settling, and collected for one second per case.
CANable remained configured S6 (500 kbit/s):

| VCU BTR | Calculated rate at PCLK1=45 MHz | Result |
| --- | --- | --- |
| 0x001E0004 (original) | 500000 | 0 frames |
| 0x034B0004 (earlier sample, SJW4) | 500000 | 0 frames |
| 0x032D0004 (middle sample, SJW4) | 500000 | 0 frames |
| 0x035F0003 | 489130.43 | 104 ID0x100 DLC8 frames |
| 0x034B0004 (repeat) | 500000 | 0 frames |
| 0x001E0004 (repeat) | 500000 | 0 frames |

This is concrete evidence of effective bitrate/timing incompatibility at the
nominal 500k settings. Sampling-point changes alone did not resolve it. It does
not independently measure either oscillator or establish which node's clock is
inaccurate. VCU uses HSI-derived PLL; adapter upstream source also uses HSI.
489130 is an experiment, not a production 500k interface change.
Original BTR=0x001E0004 was restored; no firmware/DBC edits or flashing performed.

## VCU clock cross-check against host time

TIM2 is configured PSC89, ARR0xFFFFFFFF and was stopped (CR1=0). It was
briefly started without enabling any output channel. DBGMCU_APB1_FZ=0, so TIM2
continued while CPU halted. Host timestamps bracketed two CNT reads inside
one GDB session, avoiding separate attach timing variation:

- Host first: 1793241940.309210; TIM2 CNT first: 49970095
- Host second: 1793241950.498751; TIM2 CNT second: 60298385
- Delta host: 10.189541 seconds; delta timer: 10328290 counts.
- Approximate timer rate: 1,013,617 counts/sec versus nominal 1,000,000.

This is an approximate software cross-check (timestamp/read latency remains),
not a calibrated frequency-counter measurement. It supports about +1.4% VCU
clock error. At the original divider, actual CAN rate is approximately 507k
rather than exactly 500k. This is sufficient evidence to investigate HSI clock
accuracy and establish a verified external reference for production CAN.
It does not calibrate the CANable oscillator independently.
TIM2 CR1 was restored to 0; CPU detached/resumed. CAN BTR remains original.
CANViewer reconnected at nominal 500k. No source/DBC modifications or flash writes.

## HSE clock correction and live CAN verification

ST-LINK MCO HSE availability was tested without reset/flash by setting RCC_CR.HSEON
while SYSCLK remained on the original PLL, polling HSERDY, then restoring RCC_CR.
HSERDY was already set on the first read. The NUCLEO-F446RE therefore has a live
HSE clock input with the ST-LINK connected.

Updated `main.c`, HAL `HSE_VALUE`, and CubeMX IOC to use HSE bypass at 8 MHz.
PLL M=8, N=360, P=2 produces 180 MHz SYSCLK exactly from nominal MCO; APB1 /4
is 45 MHz. bxCAN Prescaler=5, BS1=15TQ, BS2=2TQ produces
45 MHz / (5 * (1+15+2)) = 500000 bit/s. CubeMX IOC retains CAN1 500000.

Built Debug firmware with bundled STM32CubeIDE toolchain; build succeeded.
Flashed NUCLEO-F446RE by ST-LINK and programmer verified download successfully.
After reset, live RCC registers showed HSEON+HSERDY, PLLSRC=HSE, M=8, N=360,
P=2, SYSCLK SWS=PLL, APB1 prescaler=/4. CAN BTR=0x001E0004, TSR showed TXOK,
ESR=0. CANViewer connected at 500k showed recurring standard ID0x100 DLC8
frames at about 10 ms intervals.

This validates 500 kbit/s operation on this Nucleo + ST-LINK MCO + CANable setup.
It assumes the 8 MHz MCO clock nominal accuracy; the previous TIM2 measurement
was a software cross-check, not calibrated metrology. If the target is later run
without ST-LINK MCO present, its HSE source must be retained/provided.
