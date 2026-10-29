# PC Diagnostic GUI ↔ VCU UART quick start

The Driver Control panel can send its current driver-input snapshot to the VCU
over the NUCLEO-F446RE ST-LINK Virtual COM Port. It opens a connection log when
Connect is pressed and records each transmitted frame, VCU ACK, timeout, and
transport error. The panel sends immediately, then repeats every 100 ms, while
it reads the VCU acknowledgement on the same full-duplex UART connection.

## Setup

From this directory, install the GUI and serial extras into the Python
environment used to run the tool:

```sh
pip install -e ".[gui,uart]"
```

Connect the board's ST-LINK USB connector to the PC. On macOS, list serial
ports with `ls /dev/cu.usb*`; choose the board's `/dev/cu.usbmodem…` entry in
the Driver Control panel. The UART settings are fixed to 115200 baud, 8 data
bits, no parity, 1 stop bit. Press **Connect VCU UART** to start or **Disconnect
UART** to stop.

Choose the inputs before connecting. The version 2 UART frame carries ignition,
integer accelerator percent, brake, gear, door lock request, window command,
and steering direction (`CENTER=0`, `LEFT=1`, `RIGHT=2`). Accelerator values
with a fractional part are rejected for UART. Light remains a Mock-only
control and is not sent. The VCU ACK label reports whether the VCU received and
validated the packet; it does not confirm Gateway or actuator behavior.

Arrow-key controls are explicitly armed in Driver Control. Holding Up ramps
accelerator by 5 percentage points every 100 ms and releasing it returns the
accelerator to zero. Holding Down applies brake and releasing it clears brake.
Holding Left or Right sends that steering direction; releasing both sends
center. The GUI highlights each held key. Steering is stored/validated by the
VCU, but the current production CAN DBC has no steering signal, so steering is
not forwarded in `VCU_Command`.

The GUI assumes the paired VCU firmware applies a safe-input fallback after its
receive timeout (currently intended to be 500 ms). Verify that timeout and the
neutral values against the firmware actually flashed to the board before relying
on this behavior; this repository checkout does not include the VCU application
source.

## CAN boundary

The UART sender works with the CAN Monitor set to Mock or Live. Changing the
CAN input source while UART is active stops the sender and clears its input
snapshot. The existing CAN command remains Classical CAN ID `0x100`, DLC 8, 10 ms, as
defined by the production DBC. CAN mode and physical bus delivery are independent of UART ACK. Confirm the
firmware CAN mode and observe the physical bus separately; this PC-side UART
path does not enable or verify CAN transmission. External
CAN requires CAN1 Normal mode plus a separate CAN transceiver and a correctly
terminated bus; the GUI UART ACK does not change or bypass that hardware path.
