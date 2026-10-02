#ifndef CLUSTER_CAN_H
#define CLUSTER_CAN_H
#include "stm32f4xx_hal.h"
#include <stdbool.h>
/* Called from UI owner task, after the scheduler starts. */
HAL_StatusTypeDef cluster_can_init(bool enable_live);
void cluster_can_process(void);
#endif
