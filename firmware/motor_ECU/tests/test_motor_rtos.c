/* Execute production task bodies against a deterministic CMSIS2 mock.
 * This checks queue/mutex/error paths, not real kernel preemption or timing. */
#include "motor_rtos.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { unsigned cap, size, count, head; uint8_t data[16][64]; } Queue;
typedef struct { bool locked; } Mutex;
static Queue queues[2];
static Mutex mutexes[2];
static unsigned queue_count, mutex_count, thread_count;
static uint32_t now_ms, scheduled_tick;
static bool in_isr, fail_lock;
static unsigned applied, safe_stops, hw_sent, rx_enables;
static MotorDrive drive;
static int16_t servo_request;
static jmp_buf yield_point;
volatile uint32_t g_canRxDropCount;
extern volatile uint32_t g_rtosMutexTimeouts, g_rtosTxQueueDrops, g_rtosTxStaleDrops;

osKernelState_t osKernelGetState(void) { return osKernelReady; }
uint32_t osKernelGetTickFreq(void) { return 1000; }
uint32_t osKernelGetTickCount(void) { return now_ms; }
osStatus_t osDelayUntil(uint32_t ticks)
{
    assert(!in_isr);
    assert((int32_t)(ticks - now_ms) > 0);
    scheduled_tick = ticks;
    longjmp(yield_point, 1);
}
osMutexId_t osMutexNew(const osMutexAttr_t *attr)
{
    assert(!in_isr && (attr->attr_bits & osMutexPrioInherit));
    assert(mutex_count < 2);
    return &mutexes[mutex_count++];
}
osStatus_t osMutexAcquire(osMutexId_t id, uint32_t timeout)
{
    assert(!in_isr && timeout == 2);
    if (fail_lock) { fail_lock = false; return osErrorTimeout; }
    Mutex *m = id;
    assert(!m->locked);
    m->locked = true;
    return osOK;
}
osStatus_t osMutexRelease(osMutexId_t id)
{
    assert(!in_isr && ((Mutex *)id)->locked);
    ((Mutex *)id)->locked = false;
    return osOK;
}
osMessageQueueId_t osMessageQueueNew(uint32_t count, uint32_t size,
                                    const osMessageQueueAttr_t *attr)
{
    (void)attr;
    assert(queue_count < 2 && count <= 16 && size <= 64);
    Queue *q = &queues[queue_count++];
    q->cap = count; q->size = size;
    return q;
}
osStatus_t osMessageQueuePut(osMessageQueueId_t id, const void *msg,
                            uint8_t priority, uint32_t timeout)
{
    (void)priority;
    assert(timeout == 0); /* Especially important in ISR and under state lock. */
    Queue *q = id;
    if (q->count == q->cap) return osErrorResource;
    memcpy(q->data[(q->head + q->count) % q->cap], msg, q->size);
    ++q->count;
    return osOK;
}
osStatus_t osMessageQueueGet(osMessageQueueId_t id, void *msg,
                            uint8_t *priority, uint32_t timeout)
{
    (void)priority;
    assert(!in_isr && timeout == osWaitForever);
    assert(!mutexes[0].locked && !mutexes[1].locked);
    Queue *q = id;
    if (!q->count) longjmp(yield_point, 1);
    memcpy(msg, q->data[q->head], q->size);
    q->head = (q->head + 1) % q->cap;
    --q->count;
    return osOK;
}
osStatus_t osMessageQueueReset(osMessageQueueId_t id)
{
    assert(!in_isr);
    Queue *q = id;
    q->count = q->head = 0;
    return osOK;
}
osThreadId_t osThreadNew(osThreadFunc_t func, void *arg, const osThreadAttr_t *attr)
{
    (void)func; (void)arg;
    assert(attr->stack_size >= 1024 && attr->stack_size % 8 == 0);
    ++thread_count;
    return (void *)(uintptr_t)thread_count;
}
uint32_t osThreadGetStackSpace(osThreadId_t id) { (void)id; return 512; }
uint32_t MotorBoard_NowMs(void) { return now_ms; }
void MotorBoard_EnableRx(void) { ++rx_enables; }
void MotorBoard_Heartbeat(void) {}
void MotorBoard_SafeStop(void) { ++safe_stops; drive.duty = 0; servo_request = 0; }
void Error_Handler(void) { assert(!"Unexpected fatal error"); abort(); }
const MotorConfig *MotorBoard_Config(void)
{
    static const MotorConfig c = { .torque_to_rpm = 3, .alpha = .1f,
        .decay_alpha = .2f, .rpm_max = 12000, .model_period_ms = 10,
        .policy = motor_command_policy };
    return &c;
}
bool MotorBoard_TransmitHardware(const MotorCanFrame *frame)
{
    assert(!in_isr && mutexes[1].locked && !mutexes[0].locked);
    assert(frame->id == 0x110);
    ++hw_sent;
    return true;
}
void MotorBoard_Apply(const MotorApp *state, uint32_t now)
{
    assert(!in_isr && mutexes[0].locked);
    ++applied;
    motor_drive_step(&drive, state, now);
    servo_request = state->steering_target_raw;
}
static void run_task(osThreadFunc_t task)
{
    if (setjmp(yield_point) == 0) task(NULL);
    assert(!mutexes[0].locked && !mutexes[1].locked);
}
static void capture(uint32_t timestamp, uint8_t alive)
{
    MotorCanFrame f = { .id = 0x100, .dlc = 8,
        .data = { 0xA0, 0x0F, 2, 0xA5, 0x38, 0xFF, 0, 0 } };
    f.data[2] |= alive << 4;
    in_isr = true;
    MotorRTOS_CaptureISR(&f, timestamp);
    in_isr = false;
}
int main(void)
{
    MX_FREERTOS_Init();
    assert(thread_count == 5 && mutex_count == 2 && queue_count == 2);
    motor_drive_init(&drive, 0);
    for (unsigned i = 0; i < 4; ++i) capture(i * 10, i);
    now_ms = 30;
    run_task(CanRxTask);
    assert(rx_enables == 1 && MotorRuntime_State()->watchdog.last_rx_ms == 30);
    run_task(MotorControlTask);
    assert(scheduled_tick == 31);
    run_task(ActuatorTask);
    assert(drive.duty == 420 && servo_request == 0 && applied == 1);
    run_task(CanTxTask);
    assert(hw_sent == 1); /* Queue transport, outside the model state lock. */

    fail_lock = true;
    run_task(ActuatorTask);
    assert(safe_stops == 1 && drive.duty == 0 && g_rtosMutexTimeouts == 1);
    now_ms = 61;
    run_task(ActuatorTask); /* Control task not run; output task still cuts stale command. */
    assert(drive.duty == 0 && servo_request == 0);

    for (unsigned i = 0; i < 17; ++i) capture(70 + i, i & 15);
    assert(g_canRxDropCount == 1);
    run_task(CanRxTask); /* Captures from before loss must not refresh the command. */
    assert(MotorRuntime_State()->watchdog.last_rx_ms == 30);
    now_ms = 100;
    run_task(MotorControlTask);
    assert(queues[0].count == 0 && MotorRuntime_State()->rx_loss);
    assert(MotorRuntime_State()->status.fault_flags & MOTOR_FAULT_RX_LOSS);
    for (unsigned i = 0; i < 4; ++i) capture(110 + i * 10, i);
    now_ms = 140;
    run_task(CanRxTask);
    run_task(MotorControlTask);
    assert(!MotorRuntime_State()->rx_loss && !MotorRuntime_State()->watchdog.inhibit);
    capture(150, 4);
    fail_lock = true;
    run_task(CanRxTask);
    now_ms = 150;
    run_task(MotorControlTask);
    assert(MotorRuntime_State()->rx_loss && MotorRuntime_State()->watchdog.inhibit);

    /* A transmit backlog is dropped after 20 ms, rather than reporting old RUN. */
    now_ms = 200;
    run_task(CanTxTask);
    assert(g_rtosTxStaleDrops > 0);
    MotorCanFrame tx = { .id = 0x110, .dlc = 8 };
    for (unsigned i = 0; i < 4; ++i) assert(MotorBoard_Transmit(&tx));
    assert(!MotorBoard_Transmit(&tx) && g_rtosTxQueueDrops == 1);
    puts("PASS: CMSIS2 task creation, ISR queues, mutex ownership/timeouts, independent output timeout, queue-loss recovery, stale-TX drops");
    return 0;
}
