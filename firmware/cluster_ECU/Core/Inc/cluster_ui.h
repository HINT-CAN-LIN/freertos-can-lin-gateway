#ifndef CLUSTER_UI_H
#define CLUSTER_UI_H
#include "stm32f4xx_hal.h"
#include "cluster_state.h"
/* Call both functions exclusively from defaultTask (the UI owner). */
HAL_StatusTypeDef cluster_ui_init(void);
HAL_StatusTypeDef cluster_ui_process(void);
/* UI-owner task only. Future CAN task must send snapshots via a queue. */
void cluster_ui_set_state(const ClusterState *state);
bool cluster_ui_receive_frame(uint32_t id, const uint8_t *data, uint8_t dlc,
                              bool extended, bool remote, uint32_t received_ms);
void cluster_ui_mark_rx_gap(void);
#endif
