#ifndef MOTOR_RUNTIME_H
#define MOTOR_RUNTIME_H
#include "motor_app.h"
/* Cube main loop entry points. No HAL/CAN/RTOS dependencies in this layer. */
void MotorRuntime_Init(uint32_t now_ms);
void MotorRuntime_Process(uint32_t now_ms);
/* Caller holds the state mutex in the RTOS2 integration. */
void MotorRuntime_Apply(uint32_t now_ms);
void MotorRuntime_ReportRxLoss(uint32_t now_ms);
bool MotorRuntime_Receive(const MotorCanFrame *frame, uint32_t rx_ms);
const MotorApp *MotorRuntime_State(void);
/* Board hooks are implemented in main.c USER CODE for the DC demonstration. */
const MotorConfig *MotorBoard_Config(void);
bool MotorBoard_Transmit(const MotorCanFrame *frame);
void MotorBoard_Apply(const MotorApp *state, uint32_t now_ms);
#endif
