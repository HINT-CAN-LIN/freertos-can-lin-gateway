# Cluster ECU FreeRTOS task split (2026-10-11)

- defaultTask: UI owner, Normal, 8192-byte stack. Initializes LCD/LVGL, renders a copied state, handles diagnostic LED and UI stack/heap metrics. LVGL and SPI are called only here.
- canTask: AboveNormal, 2048-byte stack, 5-ms periodic service. Waits for UI startup flag before initializing CAN queue and live CAN. Drains RX queue, updates model/test input and freshness bookkeeping.
- ISR: queues CAN frames only; never takes state mutex or calls LVGL.
- Input state uses a priority-inheritance CMSIS mutex. UI takes a short snapshot, releases the mutex before rendering/blocking SPI. Test producer runs in canTask.
- IOC contains both tasks. Custom task bodies remain in USER CODE blocks.
- CLUSTER_TEST_INPUT remains 1 (demo). Live bus is enabled by setting it to 0.

## Verification
ARM build completed with no compiler warnings/errors. Task ownership/startup barrier/IOC static checks passed. Startup now tests snapshot copy isolation (`cluster_snapshot_test_passed`), in addition to existing model and queue tests. These firmware startup tests still need execution on the board after this change.

## Board check
Refresh project (F5), build, download, resume (F8) or reset. Verify uptime and the 24-second demo cycle. Watch `can_stack_free_words`, `ui_stack_free_words`, `cluster_heap_free_bytes`, `cluster_snapshot_test_passed`, `cluster_model_test_passed`, `cluster_can_queue_test_passed` and `stack_overflow_task`. Stack free values are words, multiply by 4 for bytes. Record margins under load before accepting stack sizes. Actual CAN receive/overload/Gateway integration remains unverified.

SPI is still blocking, but CAN task can preempt UI during transfers. Task separation does not establish final timeout/fault resynchronization policy or fix the previously documented SystemState display priority issue.

## 2026-10-11 follow-up validation
Task-split demo runtime is now verified after review fixes. See CLUSTER_REVIEW_FIXES.md for regression cases and measured stack/heap margins. Live CAN and IOC regeneration remain pending.
