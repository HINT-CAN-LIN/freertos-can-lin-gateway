#ifndef MOTOR_RTOS_H
#define MOTOR_RTOS_H
#include "cmsis_os2.h"
#include "motor_runtime.h"

typedef struct {
    MotorCanFrame frame;
    uint32_t rx_ms;
    uint32_t loss_epoch; /* Reject commands captured before an ISR queue loss. */
} CapturedCanFrame;
typedef struct {
    MotorCanFrame frame;
    uint32_t generated_ms;
} MotorTxFrame;

extern osThreadId_t defaultTaskHandle, canRxTaskHandle, canTxTaskHandle;
extern osThreadId_t motorControlTaskHandle, actuatorTaskHandle;
extern osMutexId_t motorStateMutexHandle, canTxMutexHandle;
extern osMessageQueueId_t canRxQueueHandle, canTxQueueHandle;

void MX_FREERTOS_Init(void);
void StartDefaultTask(void *argument);
void CanRxTask(void *argument);
void CanTxTask(void *argument);
void MotorControlTask(void *argument);
void ActuatorTask(void *argument);
/* ISR-only entry: no mutex, no blocking, no model or physical output mutation. */
void MotorRTOS_CaptureISR(const MotorCanFrame *frame, uint32_t rx_ms);

/* Board operations supplied by main.c; RTOS ownership is in freertos.c. */
uint32_t MotorBoard_NowMs(void);
void MotorBoard_EnableRx(void);
void MotorBoard_Heartbeat(void);
void MotorBoard_SafeStop(void);
bool MotorBoard_TransmitHardware(const MotorCanFrame *frame);
void Error_Handler(void);
#endif
