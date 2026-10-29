#ifndef VCU_CAN_H
#define VCU_CAN_H

#include "can.h"
#include "vcu_command_codec.h"

/* HAL_OK means accepted by a TX mailbox, not confirmed bus delivery. */
HAL_StatusTypeDef vcu_can_send(const uint8_t data[VCU_COMMAND_DLC]);

#endif
