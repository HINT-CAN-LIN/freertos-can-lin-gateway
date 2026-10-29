#ifndef TEST_FREERTOS_H
#define TEST_FREERTOS_H
#include <assert.h>
#include <stdint.h>
typedef uint32_t TickType_t;
#define configTICK_RATE_HZ 1000U
#define pdMS_TO_TICKS(ms) ((TickType_t)(ms))
#define configASSERT(x) assert(x)
#endif
