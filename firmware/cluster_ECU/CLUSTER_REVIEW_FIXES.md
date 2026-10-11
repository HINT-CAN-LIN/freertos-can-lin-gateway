# Cluster ECU review fixes — 2026-10-11

## Implemented
- R1: `cluster_display_system` chooses the newest fresh Vehicle/Fault state; a fresh Fault is no longer hidden by missing/stale Vehicle data. Equal timestamps favor the event. Uses existing display freshness constants only; never clears active faults.
- R2: UI copies input before reading HAL_GetTick; producer reads time after acquiring state mutex. This prevents a newer snapshot being evaluated against an older clock sample.
- R4: Fault redraw compares active-node bitmap and explicit last-code/node/clear/system/observed/gap fields, not just receive timestamp or struct padding.
- R3: footer now shows `UP`, local `CAN` status and actual local `RXQ:n/64`. The existing `QUEUE:%` remains the Gateway's transmitted/demo metric. Local queue high-water is `cluster_can_rx_queue_max`.
- Local CAN states: WAIT, TEST, INIT ERROR, BUS OFF, PASSIVE, WARNING, OK, OK/LOSS HIST, OK/ERR HIST. Current BOFF/EPVF/EWGF are read from the controller separately from cumulative `cluster_can_error` history. A recovered bus can show OK with retained history.
- HAL error latch is cleared after copying error history so a past FIFO overrun is not counted again on an unrelated later error callback.
- The first LVGL paint's SPI failure is returned from UI init. `cluster_ui_status` is exposed for debugger/LED fallback when LCD rendering cannot continue. Current CAN error state also enables fast LED diagnostics.

## Verification
- ARM Debug build: no warnings/errors. Flash text+data=503700 B; static RAM data+bss=74808 B.
- Expected NUCLEO-F446RE serial 066EFF485775495067212557: download verified and reset.
- Startup actual C model tests PASS, including missing/stale Vehicle + fresh Fault, newer cyclic state, equal stamp, cleared state, stale sources, tick wrap and same-stamp Fault content changes. Snapshot and CAN queue copy selftests PASS.
- Clock/snapshot call-order and first-flush error propagation static checks PASS.
- Runtime 15 samples, uptime8→37s (~29s), freshness states0/1/2 and active fault counts0/1/2 observed; SPI HAL_OK, UI status HAL_OK, no stack overflow.
- Minimum observed free UI stack3552 B; CAN stack1712 B; FreeRTOS heap3280 B. These are demo observations, not worst-case live-CAN guarantees.

## Next board checks
Current firmware remains TEST_INPUT=1. The board is already running this tested image. CubeIDE F5 refresh/reload disk edits before further work. Debug watches: `cluster_ui_status`, `cluster_can_current_errors`, `cluster_can_error`, `cluster_can_rx_drops`, `cluster_can_rx_queue_max`, `ui_stack_free_words`, `can_stack_free_words`, `cluster_heap_free_bytes`. Stack free values are words, multiply by4.

Actual CAN init failure/bus-off/recovery/burst/drop injection, long-run measurement and IOC regeneration remain unverified. The current footer queue count is sampled when the second or health text changes; use queue_max for burst occupancy.

## Deliberately unchanged team design items
Fault event boot/replay/order/loss/resynchronization; final channel freshness thresholds; node-health UI policy; CAN interface/DBC; SPI DMA; touch/SD. No synthetic Gateway Fault_Status TX was added.
