#ifndef MOTOR_WATCHDOG_H
#define MOTOR_WATCHDOG_H
#include <stdbool.h>
#include <stdint.h>
#include "motor_can.h"

typedef struct {
    uint32_t last_rx_ms;
    uint8_t previous_alive, recovery_count;
    bool seen, have_alive;
    bool timeout, alive_error, invalid_input, inhibit;
    bool bench_allow_repeated_alive;
} MotorWatchdog;

/* Single owner task only. now_ms is a monotonic millisecond timestamp. */
void motor_watchdog_init(MotorWatchdog *w, uint32_t now_ms);
void motor_watchdog_poll(MotorWatchdog *w, uint32_t now_ms);
/* Call only after accepted CAN envelope; valid is supplied by reviewed policy.
 * The module deliberately does not choose Brake/Alive Invalid precedence.
 */
void motor_watchdog_receive(MotorWatchdog *w, uint32_t rx_ms,
                            const MotorVcuCommand *command, bool valid);
#endif
