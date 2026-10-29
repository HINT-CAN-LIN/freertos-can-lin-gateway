#include "FreeRTOS.h"
TickType_t xTaskGetTickCount(void);
void vTaskDelayUntil(TickType_t *last, TickType_t period);
#define taskENTER_CRITICAL() ((void)0)
#define taskEXIT_CRITICAL() ((void)0)
