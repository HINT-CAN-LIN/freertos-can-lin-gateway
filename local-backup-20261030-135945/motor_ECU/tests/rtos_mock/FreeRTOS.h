#ifndef TEST_FREERTOS_H
#define TEST_FREERTOS_H
#include <stdint.h>
typedef uint32_t StackType_t;
typedef struct { uint32_t unused; } StaticTask_t;
#define configMINIMAL_STACK_SIZE 128
#endif
