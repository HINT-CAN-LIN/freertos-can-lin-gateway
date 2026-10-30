#include "motor_app.h"
#include <math.h>
#include <stddef.h>

uint16_t motor_servo_pulse_us(int16_t raw, uint16_t center_us, bool invert)
{
    int32_t angle = raw;
    if (angle < -450) angle = -450;
    if (angle > 450) angle = 450;
    if (invert) angle = -angle;
    /* Nominal RC calibration: +/-90 degrees = +/-500 us. The requested
     * +/-45 degree bench range therefore uses 1250..1750 us at center 1500.
     * This is an initial calibration, not a measured linkage/shaft angle. */
    int32_t pulse = (int32_t)center_us + angle * 500 / 900;
    if (pulse < 1000) pulse = 1000;
    if (pulse > 2000) pulse = 2000;
    return (uint16_t)pulse;
}

bool motor_command_policy(const MotorVcuCommand *c, uint16_t *allowed)
{
    if (c == NULL || allowed == NULL || c->torque_raw > 40000u || c->gear > 3u ||
        c->steering_raw < -450 || c->steering_raw > 450)
        return false;
    *allowed = (!c->brake && (c->gear == 2u || c->gear == 3u)) ? c->torque_raw : 0;
    return true;
}

void motor_drive_init(MotorDrive *d, uint32_t now)
{
    if (d != NULL) *d = (MotorDrive){ .stopped_ms = now, .stopped = true };
}

void motor_drive_step(MotorDrive *d, const MotorApp *a, uint32_t now)
{
    int8_t requested = 0;
    uint16_t duty = 0;
    if (d == NULL) return;
    if (a != NULL && a->configured && !a->watchdog.inhibit &&
        !a->command.brake && a->status.torque_raw > 0 && a->config.rpm_max > 0) {
        requested = a->command.gear == 2u ? 1 : a->command.gear == 3u ? -1 : 0;
        float scaled = a->target_rpm * (float)MOTOR_PWM_COUNTS / a->config.rpm_max;
        if (scaled > MOTOR_PWM_COUNTS) scaled = MOTOR_PWM_COUNTS;
        if (scaled > 0) duty = (uint16_t)scaled;
    }
    /* A reversal must include a continuous zero-output interval. Keep the
     * previous direction across P/N/brake/timeout, so they cannot bypass it. */
    if (requested != 0 && duty > 0 && requested != d->last_direction &&
        d->last_direction != 0 &&
        (!d->stopped || (uint32_t)(now - d->stopped_ms) < MOTOR_REVERSE_STOP_MS)) {
        duty = 0;
    }
    if (requested == 0 || duty == 0) {
        if (!d->stopped) d->stopped_ms = now;
        d->stopped = true;
        d->direction = 0;
        d->duty = 0;
    } else {
        d->stopped = false;
        d->last_direction = d->direction = requested;
        d->duty = duty;
    }
}

bool motor_app_init(MotorApp *a, const MotorConfig *c, uint32_t now)
{
    if (a == NULL) return false;
    *a = (MotorApp){0};
    motor_watchdog_init(&a->watchdog, now);
    a->model_ms = a->tx_ms = now;
    a->status.state = MOTOR_OFF;
    a->status.firmware_revision = MOTOR_FIRMWARE_REVISION;
    if (c == NULL || c->policy == NULL || !isfinite(c->torque_to_rpm) ||
        c->torque_to_rpm <= 0.0f || !isfinite(c->alpha) || c->alpha <= 0.0f ||
        c->alpha > 1.0f || !isfinite(c->decay_alpha) || c->decay_alpha <= 0.0f ||
        c->decay_alpha > 1.0f || c->rpm_max == 0 || c->rpm_max > 12000u ||
        c->model_period_ms == 0) return false;
    a->config = *c;
    a->watchdog.bench_allow_repeated_alive = c->bench_allow_repeated_alive;
    a->configured = true;
    return true;
}

bool motor_app_receive(MotorApp *a, const MotorCanFrame *f, uint32_t now)
{
    MotorVcuCommand command;
    MotorGatewayStatus gateway;
    uint16_t allowed = 0;
    bool valid;
    if (a == NULL || f == NULL) return false;
    if (motor_can_decode_gateway(f, &gateway)) {
        a->gateway = gateway;
        a->gateway_seen = true;
        a->gateway_rx_ms = now;
        return true; /* Raw observation only: Gateway timeout is unspecified. */
    }
    if (!motor_can_decode_vcu(f, &command)) {
        a->rejected_frames++;
        return false;
    }
    valid = a->configured && command.torque_raw <= 40000u && command.gear <= 3u;
    if (valid) valid = a->config.policy(&command, &allowed);
    valid = valid && allowed <= command.torque_raw;
    a->command = command;
    a->allowed_torque_raw = valid ? allowed : 0;
    motor_watchdog_receive(&a->watchdog, now, &command, valid);
    /* Set safe torque immediately; do not wait for a model update. */
    if (a->watchdog.inhibit) {
        a->status.torque_raw = 0;
        a->target_rpm = 0;
        a->steering_target_raw = 0;
    }
    return true;
}

void motor_app_step(MotorApp *a, uint32_t now, MotorTransmit tx, void *ctx)
{
    MotorCanFrame frame;
    uint32_t elapsed;
    bool inhibited;
    float coefficient, periods;
    if (a == NULL) return;
    motor_watchdog_poll(&a->watchdog, now);
    inhibited = !a->configured || a->watchdog.inhibit;
    if (!inhibited) a->rx_loss = false;
    a->steering_target_raw = inhibited ? 0 : a->command.steering_raw;
    a->status.steering_raw = a->steering_target_raw;
    a->status.fault_flags = (a->watchdog.timeout ? MOTOR_FAULT_TIMEOUT : 0u) |
                           (a->watchdog.alive_error ? MOTOR_FAULT_ALIVE : 0u) |
                           (a->watchdog.invalid_input ? MOTOR_FAULT_INVALID : 0u) |
                           (a->rx_loss ? MOTOR_FAULT_RX_LOSS : 0u);
    a->status.torque_raw = inhibited ? 0 : a->allowed_torque_raw;
    a->target_rpm = 0;
    if (!inhibited) {
        a->target_rpm = (float)a->status.torque_raw * 0.1f * a->config.torque_to_rpm;
        if (a->target_rpm > a->config.rpm_max) a->target_rpm = a->config.rpm_max;
    }
    elapsed = now - a->model_ms;
    if (a->configured && elapsed > 0) {
        coefficient = inhibited ? a->config.decay_alpha : a->config.alpha;
        periods = (float)elapsed / (float)a->config.model_period_ms;
        coefficient = 1.0f - powf(1.0f - coefficient, periods);
        a->rpm += coefficient * (a->target_rpm - a->rpm);
    }
    a->model_ms = now;
    a->status.rpm = (uint16_t)(a->rpm + 0.5f);
    /* Proposed local state mapping; no VCU ignition/state machine here. */
    if (!a->configured) a->status.state = MOTOR_OFF;
    else if (a->watchdog.timeout || a->watchdog.alive_error || a->watchdog.invalid_input || a->rx_loss)
        a->status.state = MOTOR_FAIL_SAFE;
    else if (a->watchdog.inhibit) a->status.state = MOTOR_OFF;
    else a->status.state = (a->status.torque_raw > 0 || a->status.rpm > 0) ? MOTOR_RUN : MOTOR_READY;

    if ((uint32_t)(now - a->tx_ms) >= MOTOR_STATUS_PERIOD_MS) {
        /* No burst replay of obsolete status after a scheduling delay. */
        a->tx_ms = now;
        if (tx != NULL && motor_can_encode_status(&a->status, &frame) && tx(&frame, ctx)) {
            a->tx_accepted++;
            a->status.alive = (uint8_t)((a->status.alive + 1u) & 15u);
        } else a->tx_failures++;
    }
}
