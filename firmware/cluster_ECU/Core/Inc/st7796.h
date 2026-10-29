#ifndef ST7796_H
#define ST7796_H
#include "stm32f4xx_hal.h"
/* SPI2: PB13 SCK, PB15 MOSI; PB12 CS, PC6 DC, PC7 RESET.
 * Blocking bring-up driver. Call only from one task. */
HAL_StatusTypeDef st7796_init(void);
HAL_StatusTypeDef st7796_fill(uint16_t rgb565);
/* Pixels are packed RGB565 in native STM32 little-endian order. */
HAL_StatusTypeDef st7796_blit(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2,
                            const uint8_t *pixels);
#endif
