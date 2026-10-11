#ifndef CLUSTER_CAN_H
#define CLUSTER_CAN_H
#include "stm32f4xx_hal.h"
#include <stdbool.h>
/* CAN task only, after UI initialization has released its startup flag. */
HAL_StatusTypeDef cluster_can_init(bool enable_live);
void cluster_can_process(void);
typedef struct {
  HAL_StatusTypeDef init_status;
  bool initialized, live;
  uint32_t current_errors, error_history, rx_drops;
  uint32_t queue_count, queue_max;
} ClusterCanDiagnostics;
/* Task context only; independent of the Gateway's published health metrics. */
void cluster_can_get_diagnostics(ClusterCanDiagnostics *out);
extern volatile HAL_StatusTypeDef cluster_can_status;
extern volatile uint32_t cluster_can_current_errors;
extern volatile uint32_t cluster_can_error; /* Cumulative history, not current. */
extern volatile uint32_t cluster_can_rx_count, cluster_can_rx_drops;
extern volatile uint32_t cluster_can_rx_queue_max;
#endif
