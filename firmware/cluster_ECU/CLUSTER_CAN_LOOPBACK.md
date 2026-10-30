# CAN internal loopback test

CAN1 is configured as `CAN_MODE_SILENT_LOOPBACK` in both `Cluster_ECU.ioc` and `Core/Src/can.c`. This exercises bxCAN internally without sending synthetic traffic to the external bus.

`CLUSTER_CAN_LOOPBACK=1` enables the test producer. Frames pass through HAL CAN TX mailboxes, hardware loopback, the RX FIFO0 interrupt, the 64-frame RTOS queue, the decoder, and the protected UI model. Direct demo injection into the UI is disabled in this mode. A mode mismatch fails initialization before test transmission.

The existing 24-second demo drives IDs 0x100, 0x110, 0x120, 0x200, 0x300 and edge-triggered 0x310 Fault events. Cyclic frames are generated every 100 ms, with a 6-second intentional pause to test stale/offline display. This cadence is a display regression test, not validation of the production DBC transmission periods. Fault events remain latched until a clear event.

The screen shows `CAN LOOP` and `CAN:LOOP`; current errors and error/loss history take precedence in the footer. Debug counters: `cluster_can_tx_count`, `cluster_can_rx_count`, `cluster_can_tx_errors`, `cluster_can_rx_drops`, `cluster_can_error`, `cluster_can_rx_queue_max`.

## Return to external CAN RX

1. Set BOTH `CLUSTER_CAN_LOOPBACK` and `CLUSTER_TEST_INPUT` to 0 in `cluster_state.h`.
2. Change CAN1 Mode to Normal in the IOC and regenerate; verify `can.c` uses `CAN_MODE_NORMAL`.
3. Rebuild and download. The Cluster then receives external frames and does not send application frames.

Internal loopback does not validate transceiver wiring, termination, external bus timing, or CANable interoperability. SPI remains blocking; no DMA change is included.

## Board validation (2026-10-11)

Build and flash verification passed. A 29-second run sampled TX/RX=1319/1319, zero TX errors, zero RX drops/error history, maximum RX queue occupancy 3/64, Fresh/Stale/Offline transitions, active Fault counts 0/1/2, and startup self-tests. Minimum free stack: UI 3536 bytes, CAN 1712 bytes; free RTOS heap 3280 bytes. CAN pins use pull-up to allow initial synchronization without an attached transceiver.
