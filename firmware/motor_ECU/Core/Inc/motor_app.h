#ifndef MOTOR_APP_H
#define MOTOR_APP_H
#include "motor_watchdog.h"

/* Review callback: checks disputed Invalid codes and applies ONLY Motor-side
 * command constraints. It must never increase the VCU torque request. */
typedef bool (*MotorCommandPolicy)(const MotorVcuCommand *, uint16_t *allowed_raw);
/* Nonblocking; true means this frame was accepted by the transport. */
typedef bool (*MotorTransmit)(const MotorCanFrame *, void *context);
typedef struct {
    float torque_to_rpm; /* rpm/Nm */
    float alpha;        /* response coefficient at model_period_ms */
    float decay_alpha;  /* fail-safe decay coefficient at model_period_ms */
    uint16_t rpm_max;
    uint32_t model_period_ms;
    MotorCommandPolicy policy;
    bool bench_allow_repeated_alive; /* PC fixed-frame bench only; false for VCU. */
} MotorConfig;
typedef struct {
    MotorConfig config;
    MotorWatchdog watchdog;
    MotorVcuCommand command;
    MotorGatewayStatus gateway;
    MotorStatus status;
    float rpm, target_rpm;
    uint16_t allowed_torque_raw;
    int16_t steering_target_raw; /* Validated 0.1 degree request, zero on inhibit. */
    uint32_t model_ms, tx_ms, gateway_rx_ms;
    uint32_t rejected_frames, tx_failures, tx_accepted;
    bool configured, gateway_seen, rx_loss;
} MotorApp;

/* NULL/unapproved configuration keeps the application inhibited. */
bool motor_app_init(MotorApp *, const MotorConfig *, uint32_t now_ms);
/* Caller serializes receive and step with the state mutex. Deliver frames in timestamp order.
 * rx_ms must be capture time, not queue dequeue time. */
bool motor_app_receive(MotorApp *, const MotorCanFrame *, uint32_t rx_ms);
void motor_app_step(MotorApp *, uint32_t now_ms, MotorTransmit, void *context);
bool motor_command_policy(const MotorVcuCommand *, uint16_t *allowed_raw);
uint16_t motor_servo_pulse_us(int16_t steering_raw, uint16_t center_us, bool invert);

/* Physical demonstration policy, separate from the virtual RPM model.
 * Duty is in timer counts (0..4200); direction is -1/R, 0/stop, +1/D. */
#define MOTOR_PWM_COUNTS 4200u
#define MOTOR_REVERSE_STOP_MS 200u
typedef struct {
    uint32_t stopped_ms;
    int8_t last_direction, direction;
    uint16_t duty;
    bool stopped;
} MotorDrive;
void motor_drive_init(MotorDrive *, uint32_t now_ms);
void motor_drive_step(MotorDrive *, const MotorApp *, uint32_t now_ms);
#endif
