#ifndef VCU_SERIAL_H
#define VCU_SERIAL_H

#include <stdint.h>

#define VCU_SERIAL_INPUT_PERIOD_MS   100U
#define VCU_SERIAL_INPUT_TIMEOUT_MS  500U

typedef struct {
    uint32_t accepted_frames;
    uint32_t rejected_frames;
    uint32_t ack_tx_errors;
    uint32_t input_timeouts;
    uint32_t parser_resyncs;
} vcu_serial_stats_t;

extern volatile vcu_serial_stats_t vcu_serial_stats;

void vcu_serial_start(void);
void vcu_serial_task_run(void);

#endif
