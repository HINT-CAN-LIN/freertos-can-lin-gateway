# LVGL LCD bring-up

LVGL 9.6.0 is vendored in Middlewares/Third_Party/lvgl (src/include, upstream licenses retained).

- Core/Inc/lv_conf.h: 32 KiB LVGL built-in allocation pool, software rendering, fonts 14/20/48.
- Core/Src/cluster_ui.c: 480x320 RGB565 partial display, one 19,200-byte buffer, HAL_GetTick tick source.
- Core/Src/st7796.c: blocking area transfer; converts native little-endian RGB565 to SPI high-byte-first without modifying the LVGL buffer.
- defaultTask owns every LVGL call. LV_USE_OS is NONE intentionally; other tasks must not call LVGL.
- defaultTask stack is 8 KiB, also saved in cluster_ECU.ioc.
- CAN is not started; all values marked TEST are placeholders. CAN OFFLINE is expected.
- No touch driver is registered.

## Hardware verification

Refresh the project, reload changed files, build Debug, download, and resume (F8).
Expected: dark landscape screen with CLUSTER ECU / TEST MODE, speed 0 km/h, BODY, FAULT,
HEALTH: CAN OFFLINE, and UI UPTIME increasing each second. Green LED toggles every 500 ms.
Red/green/blue colors must be recognizable; shifted blocks or wrong colors suggest area/byte-order issues.
On SPI failure the green LED toggles every 100 ms; inspect ui_status / display_status in the debugger.
A stopped screen or stopped uptime requires checking the task stack and any LVGL assertion.

## Regeneration

Custom task code is inside USER CODE blocks. Preserve the LVGL include path
../Middlewares/Third_Party/lvgl/include and compile the Middlewares source tree.
The existing .cproject source entries already include Middlewares for Debug and Release.
Do not allocate a full framebuffer (307,200 bytes); the MCU has only 128 KiB RAM.

## Next

After verifying this screen, bring up CAN reception independently, then pass decoded state
to the UI owner through a queue. Introduce DMA only after validating blocking transfers.

Local upstream adaptation: public header includes use <lvgl/...> rather than nested relative paths, to prevent GCC/Windows long-path dependency errors in this repository location. Software color support is limited to RGB565 and A8 for this screen.

Stack overflow checking (mode 2) is enabled; ui_stack_free_words records the UI stack high-water mark in words. Initial O0 rendering exceeded the original 4 KiB stack and corrupted scheduler globals; the UI stack is now 8 KiB.
