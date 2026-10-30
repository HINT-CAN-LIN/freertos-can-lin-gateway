#ifndef VCU_COMMAND_CODEC_H
#define VCU_COMMAND_CODEC_H

#include <stdint.h>
#include "vcu_app.h"
#include "vcu_command.h"

/* Source: network/can/CAN__DB_펌웨어 전 최종본_v0.1.dbc,
 * VERSION "0.4 - review-ready interface proposal", BO_ 256 and its attributes.
 * All encoded signals: unsigned Intel (@1+), offset 0. Door/window fields
 * are CAN requests consumed by Gateway; LIN command generation is out of scope.
 */
/* Reject invalid application inputs; leave output untouched on failure.
 * Torque is rounded to the nearest 0.1 Nm. Reserved bits/bytes are zero.
 */
bool vcu_command_encode(const vcu_app_command_t *command, uint8_t alive,
                        uint8_t data[VCU_COMMAND_DLC]);

#endif
