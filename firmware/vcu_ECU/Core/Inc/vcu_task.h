#ifndef VCU_TASK_H
#define VCU_TASK_H

#include <stdint.h>

typedef struct {
    uint32_t tx_accepted;
    uint32_t tx_busy;
    uint32_t tx_errors;
    uint32_t encode_errors;
    uint32_t deadline_misses;
    uint8_t next_alive;
} vcu_task_stats_t;

/* Single writer: VCUTxTask. Inspect in debugger; no ISR writes. */
extern volatile vcu_task_stats_t vcu_task_stats;
void vcu_task_run(void);

#endif
