#include "motor_watchdog.h"
#include <stddef.h>

void motor_watchdog_init(MotorWatchdog *w, uint32_t now_ms)
{
    if (w == NULL) return;
    *w = (MotorWatchdog){0};
    w->last_rx_ms = now_ms;
    w->inhibit = true;
}

void motor_watchdog_poll(MotorWatchdog *w, uint32_t now_ms)
{
    if (w == NULL) return;
    if ((uint32_t)(now_ms - w->last_rx_ms) > MOTOR_VCU_TIMEOUT_MS) {
        w->timeout = true;
        w->inhibit = true;
        w->recovery_count = 0;
        w->have_alive = false;
    }
}

void motor_watchdog_receive(MotorWatchdog *w, uint32_t rx_ms,
                            const MotorVcuCommand *c, bool valid)
{
    bool continuous;
    if (w == NULL || c == NULL) return;
    /* Detect a gap even if no poll ran between two arrivals. */
    motor_watchdog_poll(w, rx_ms);
    w->last_rx_ms = rx_ms;
    w->seen = true;
    if (!valid || c->alive > 15u) {
        w->invalid_input = true;
        w->inhibit = true;
        w->recovery_count = 0;
        w->have_alive = false;
        return;
    }
    if (!w->have_alive) {
        /* Proposal: seed only; a first sample cannot prove continuity. */
        w->previous_alive = c->alive;
        w->have_alive = true;
        w->recovery_count = 0;
        return;
    }
    continuous = c->alive == (uint8_t)((w->previous_alive + 1u) & 15u);
    if (w->bench_allow_repeated_alive && c->alive == w->previous_alive)
        continuous = true;
    /* Proposal: rebase on the received valid sample after a discontinuity. */
    w->previous_alive = c->alive;
    if (!continuous) {
        w->alive_error = true;
        w->inhibit = true;
        w->recovery_count = 0;
        return;
    }
    if (w->inhibit && ++w->recovery_count >= 3u) {
        w->timeout = false;
        w->alive_error = false;
        w->invalid_input = false;
        w->inhibit = false;
        w->recovery_count = 0;
    }
}
