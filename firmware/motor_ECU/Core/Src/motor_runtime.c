#include "motor_runtime.h"
#include <stddef.h>

static MotorApp motor;

/* Default board hooks intentionally do not invent model constants or claim TX. */
__attribute__((weak)) const MotorConfig *MotorBoard_Config(void) { return NULL; }
__attribute__((weak)) bool MotorBoard_Transmit(const MotorCanFrame *frame)
{
    (void)frame;
    return false;
}
__attribute__((weak)) void MotorBoard_Apply(const MotorApp *state, uint32_t now_ms)
{
    (void)state;
    (void)now_ms;
}
static bool transmit(const MotorCanFrame *frame, void *ctx)
{
    (void)ctx;
    return MotorBoard_Transmit(frame);
}
void MotorRuntime_Init(uint32_t now_ms)
{
    (void)motor_app_init(&motor, MotorBoard_Config(), now_ms);
}
void MotorRuntime_Process(uint32_t now_ms)
{
    motor_app_step(&motor, now_ms, transmit, NULL);
}
void MotorRuntime_Apply(uint32_t now_ms)
{
    /* Output task checks freshness independently of the model task cadence. */
    motor_watchdog_poll(&motor.watchdog, now_ms);
    if (motor.watchdog.inhibit) {
        motor.status.torque_raw = 0;
        motor.target_rpm = 0;
        motor.steering_target_raw = 0;
    }
    MotorBoard_Apply(&motor, now_ms);
}
void MotorRuntime_ReportRxLoss(uint32_t now_ms)
{
    MotorRuntime_Init(now_ms);
    motor.rx_loss = true;
}
bool MotorRuntime_Receive(const MotorCanFrame *frame, uint32_t rx_ms)
{
    return motor_app_receive(&motor, frame, rx_ms);
}
const MotorApp *MotorRuntime_State(void) { return &motor; }
