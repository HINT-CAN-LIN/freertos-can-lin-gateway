#include "vcu_task.h"
#include "vcu_app.h"
#include "vcu_can.h"
#include "FreeRTOS.h"
#include "task.h"
#include "vcu_pc_can.h"

volatile vcu_task_stats_t vcu_task_stats;

void vcu_task_run(void)
{
    const TickType_t period = pdMS_TO_TICKS(VCU_COMMAND_PERIOD_MS);
    TickType_t last_release = xTaskGetTickCount();
    uint8_t alive = 0;
    configASSERT(period > 0);
    configASSERT((configTICK_RATE_HZ * VCU_COMMAND_PERIOD_MS) % 1000U == 0U);

    for (;;) {
        vcu_pc_can_poll();
        vcu_app_command_t command = vcu_app_get_command();
        uint8_t data[VCU_COMMAND_DLC];
        if (!vcu_command_encode(&command, alive, data)) {
            ++vcu_task_stats.encode_errors;
        } else {
            HAL_StatusTypeDef status = vcu_can_send(data);
            if (status == HAL_OK) {
                ++vcu_task_stats.tx_accepted;
                alive = (uint8_t)((alive + 1U) % VCU_COMMAND_ALIVE_MODULO);
                vcu_task_stats.next_alive = alive;
            } else if (status == HAL_BUSY) {
                ++vcu_task_stats.tx_busy;
            } else {
                ++vcu_task_stats.tx_errors;
            }
        }

        /* Absolute releases avoid accumulating execution-time drift.
         * On overrun, report and rebase instead of bursting stale commands.
         */
        if ((TickType_t)(xTaskGetTickCount() - last_release) >= period) {
            ++vcu_task_stats.deadline_misses;
            last_release = xTaskGetTickCount();
        }
        vTaskDelayUntil(&last_release, period);
    }
}
