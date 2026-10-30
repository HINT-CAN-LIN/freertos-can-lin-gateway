/* CMSIS-RTOS2 application integration, FreeRTOS kernel V10.3.1.
 * STM32Cube FW_F4 V1.28.3 supplies the unmodified CMSIS_RTOS_V2 adapter.
 */
#include "motor_rtos.h"
#include "FreeRTOS.h"
#include "task.h"

osThreadId_t defaultTaskHandle, canRxTaskHandle, canTxTaskHandle;
osThreadId_t motorControlTaskHandle, actuatorTaskHandle;
osMutexId_t motorStateMutexHandle, canTxMutexHandle;
osMessageQueueId_t canRxQueueHandle, canTxQueueHandle;

extern volatile uint32_t g_canRxDropCount;
volatile uint32_t g_rtosApiVersion = 2;
volatile uint32_t g_rtosMutexTimeouts = 0;
volatile uint32_t g_rtosRxLockDrops = 0;
volatile uint32_t g_rtosTxQueueDrops = 0;
volatile uint32_t g_rtosTxStaleDrops = 0;
volatile uint32_t g_rtosRxStackFree = 0, g_rtosControlStackFree = 0;
volatile uint32_t g_rtosActuatorStackFree = 0, g_rtosTxStackFree = 0;
/* Only CAN ISR increments this aligned word. Tasks never clear it. */
static volatile uint32_t rxLossEpoch = 0;

static const osMutexAttr_t motorStateMutex_attributes = {
    .name = "motorStateMutex", .attr_bits = osMutexPrioInherit
};
static const osMutexAttr_t canTxMutex_attributes = {
    .name = "canTxMutex", .attr_bits = osMutexPrioInherit
};
static const osMessageQueueAttr_t canRxQueue_attributes = { .name = "canRxQueue" };
static const osMessageQueueAttr_t canTxQueue_attributes = { .name = "canTxQueue" };
static const osThreadAttr_t defaultTask_attributes = {
    .name = "healthTask", .stack_size = 1024, .priority = osPriorityBelowNormal
};
static const osThreadAttr_t canRxTask_attributes = {
    .name = "canRxTask", .stack_size = 1024, .priority = osPriorityAboveNormal
};
static const osThreadAttr_t motorControlTask_attributes = {
    .name = "motorControlTask", .stack_size = 2048, .priority = osPriorityHigh
};
static const osThreadAttr_t actuatorTask_attributes = {
    .name = "actuatorTask", .stack_size = 1024, .priority = osPriorityHigh1
};
static const osThreadAttr_t canTxTask_attributes = {
    .name = "canTxTask", .stack_size = 1024, .priority = osPriorityNormal
};

/* Fixed-rate tasks skip missed releases; they never spin on an expired deadline.
 * This project requires a 1 kHz OS tick, checked at initialization. */
static void wait_next(uint32_t *deadline, uint32_t period)
{
    uint32_t now = osKernelGetTickCount();
    *deadline += period;
    if ((int32_t)(*deadline - now) <= 0) *deadline = now + period;
    if (osDelayUntil(*deadline) != osOK) Error_Handler();
}
static bool state_lock(void)
{
    if (osMutexAcquire(motorStateMutexHandle, 2) == osOK) return true;
    /* Multiple tasks may report this debug count: preserve increments. */
    __atomic_fetch_add(&g_rtosMutexTimeouts, 1, __ATOMIC_RELAXED);
    return false;
}
static void state_unlock(void)
{
    if (osMutexRelease(motorStateMutexHandle) != osOK) Error_Handler();
}

void MX_FREERTOS_Init(void)
{
    if (osKernelGetState() != osKernelReady || osKernelGetTickFreq() != 1000)
        Error_Handler();
    motorStateMutexHandle = osMutexNew(&motorStateMutex_attributes);
    canTxMutexHandle = osMutexNew(&canTxMutex_attributes);
    canRxQueueHandle = osMessageQueueNew(16, sizeof(CapturedCanFrame), &canRxQueue_attributes);
    canTxQueueHandle = osMessageQueueNew(4, sizeof(MotorTxFrame), &canTxQueue_attributes);
    if (!motorStateMutexHandle || !canTxMutexHandle || !canRxQueueHandle || !canTxQueueHandle)
        Error_Handler();
    MotorRuntime_Init(MotorBoard_NowMs());
    defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);
    canRxTaskHandle = osThreadNew(CanRxTask, NULL, &canRxTask_attributes);
    motorControlTaskHandle = osThreadNew(MotorControlTask, NULL, &motorControlTask_attributes);
    actuatorTaskHandle = osThreadNew(ActuatorTask, NULL, &actuatorTask_attributes);
    canTxTaskHandle = osThreadNew(CanTxTask, NULL, &canTxTask_attributes);
    if (!defaultTaskHandle || !canRxTaskHandle || !motorControlTaskHandle ||
        !actuatorTaskHandle || !canTxTaskHandle) Error_Handler();
}

void MotorRTOS_CaptureISR(const MotorCanFrame *frame, uint32_t rx_ms)
{
    CapturedCanFrame item = { .frame = *frame, .rx_ms = rx_ms, .loss_epoch = rxLossEpoch };
    /* timeout MUST be zero in ISR. The CMSIS2 adapter performs FromISR/yield. */
    if (osMessageQueuePut(canRxQueueHandle, &item, 0, 0) != osOK) {
        ++g_canRxDropCount;
        ++rxLossEpoch;
    }
}

/* Runtime's nonblocking TX hook: called under motorStateMutex by control task.
 * The model counts queue acceptance, not a confirmed physical CAN transmission. */
bool MotorBoard_Transmit(const MotorCanFrame *frame)
{
    MotorTxFrame item = { .frame = *frame, .generated_ms = MotorBoard_NowMs() };
    if (osMessageQueuePut(canTxQueueHandle, &item, 0, 0) == osOK) return true;
    ++g_rtosTxQueueDrops;
    return false;
}

void CanRxTask(void *argument)
{
    (void)argument;
    MotorBoard_EnableRx(); /* Kernel is running and the receive queue exists. */
    for (;;) {
        CapturedCanFrame item;
        if (osMessageQueueGet(canRxQueueHandle, &item, NULL, osWaitForever) != osOK)
            Error_Handler();
        /* Never use queue dequeue time as command freshness. */
        if (state_lock()) {
            if (item.loss_epoch == rxLossEpoch)
                MotorRuntime_Receive(&item.frame, item.rx_ms);
            state_unlock();
        } else {
            /* The control task observes this task-owned loss counter too. */
            ++g_rtosRxLockDrops;
        }
    }
}

void MotorControlTask(void *argument)
{
    (void)argument;
    uint32_t deadline = osKernelGetTickCount();
    static uint32_t handledIsrLoss = 0, handledLockLoss = 0;
    for (;;) {
        if (state_lock()) {
            uint32_t epoch = rxLossEpoch;
            uint32_t lockLoss = g_rtosRxLockDrops;
            if (epoch != handledIsrLoss || lockLoss != handledLockLoss) {
                /* Discard queued old commands before restarting Alive sync. */
                if (osMessageQueueReset(canRxQueueHandle) != osOK) Error_Handler();
                MotorRuntime_ReportRxLoss(MotorBoard_NowMs());
                handledIsrLoss = epoch;
                handledLockLoss = lockLoss;
            }
            MotorRuntime_Process(MotorBoard_NowMs());
            state_unlock();
        }
        wait_next(&deadline, 1);
    }
}

void ActuatorTask(void *argument)
{
    (void)argument;
    uint32_t deadline = osKernelGetTickCount();
    for (;;) {
        if (state_lock()) {
            MotorRuntime_Apply(MotorBoard_NowMs());
            state_unlock();
        } else {
            /* Actuator task is the sole normal PWM writer. Never hold stale
             * torque/steering while waiting indefinitely for a shared state. */
            MotorBoard_SafeStop();
        }
        wait_next(&deadline, 1);
    }
}

void CanTxTask(void *argument)
{
    (void)argument;
    for (;;) {
        MotorTxFrame item;
        if (osMessageQueueGet(canTxQueueHandle, &item, NULL, osWaitForever) != osOK)
            Error_Handler();
        if ((uint32_t)(MotorBoard_NowMs() - item.generated_ms) > 20) {
            ++g_rtosTxStaleDrops;
            continue;
        }
        if (osMutexAcquire(canTxMutexHandle, 2) == osOK) {
            (void)MotorBoard_TransmitHardware(&item.frame);
            if (osMutexRelease(canTxMutexHandle) != osOK) Error_Handler();
        } else {
            __atomic_fetch_add(&g_rtosMutexTimeouts, 1, __ATOMIC_RELAXED);
        }
    }
}

void StartDefaultTask(void *argument)
{
    (void)argument;
    uint32_t deadline = osKernelGetTickCount();
    for (;;) {
        MotorBoard_Heartbeat();
        g_rtosRxStackFree = osThreadGetStackSpace(canRxTaskHandle);
        g_rtosControlStackFree = osThreadGetStackSpace(motorControlTaskHandle);
        g_rtosActuatorStackFree = osThreadGetStackSpace(actuatorTaskHandle);
        g_rtosTxStackFree = osThreadGetStackSpace(canTxTaskHandle);
        wait_next(&deadline, 500);
    }
}

/* Fatal allocation/stack failures stop physical output without using RTOS locks. */
void vApplicationMallocFailedHook(void) { Error_Handler(); }
void vApplicationStackOverflowHook(TaskHandle_t task, char *name)
{
    (void)task; (void)name; Error_Handler();
}
static StaticTask_t idleTcb;
static StackType_t idleStack[configMINIMAL_STACK_SIZE];
void vApplicationGetIdleTaskMemory(StaticTask_t **tcb, StackType_t **stack, uint32_t *size)
{
    *tcb = &idleTcb; *stack = idleStack; *size = configMINIMAL_STACK_SIZE;
}
