#ifndef CLUSTER_UI_H
#define CLUSTER_UI_H
#include "stm32f4xx_hal.h"
#include "cluster_state.h"
/* Only the UI task calls initialization/process and LVGL. */
extern volatile HAL_StatusTypeDef cluster_ui_status; /* LED/debugger fallback if LCD fails. */
HAL_StatusTypeDef cluster_ui_init(void);
HAL_StatusTypeDef cluster_ui_process(void);
/* Task-context input API. Internal priority-inheritance mutex protects snapshots.
 * Call only after UI initialization succeeds; never from ISR. */
void cluster_ui_update_input(void);
void cluster_ui_set_state(const ClusterState *state);
bool cluster_ui_receive_frame(uint32_t id, const uint8_t *data, uint8_t dlc,
                              bool extended, bool remote, uint32_t received_ms);
void cluster_ui_mark_rx_gap(void);
#endif
