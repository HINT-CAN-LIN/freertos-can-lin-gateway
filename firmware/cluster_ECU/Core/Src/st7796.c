/* ST7796S initialization adapted from LCDWiki MSP4020/MSP4021 V1.0,
 * Demo_STM32F407ZGT6_Hardware_SPI/HARDWARE/LCD/lcd.c.
 * Source: https://www.lcdwiki.com/4.0inch_SPI_Module_ST7796
 * HAL SPI2 port for NUCLEO-F446RE; RGB565, landscape 480x320.
 */
#include "st7796.h"
#include "spi.h"
#include "cmsis_os2.h"

static uint8_t fill_buffer[256];

static HAL_StatusTypeDef write_bytes(uint8_t *data, uint16_t size)
{
  return HAL_SPI_Transmit(&hspi2, data, size, 1000);
}

static HAL_StatusTypeDef write_byte(uint8_t value, GPIO_PinState dc)
{
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_6, dc);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET);
  HAL_StatusTypeDef result = write_bytes(&value, 1);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
  return result;
}

static void delay_ms(uint32_t ms)
{
  if (osKernelGetState() == osKernelRunning) {
    uint32_t ticks = (ms * osKernelGetTickFreq() + 999U) / 1000U;
    osDelay(ticks);
  } else {
    HAL_Delay(ms);
  }
}

HAL_StatusTypeDef st7796_init(void)
{
  /* LCD GPIO and SPI2 must already be initialized by CubeMX. */
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_7, GPIO_PIN_RESET);
  delay_ms(100);
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_7, GPIO_PIN_SET);
  delay_ms(120);
  static const uint8_t init[][2] = {
    {0, 0xF0},
    {1, 0xC3},
    {0, 0xF0},
    {1, 0x96},
    {0, 0x36},
    {1, 0x68},
    {0, 0x3A},
    {1, 0x05},
    {0, 0xB0},
    {1, 0x80},
    {0, 0xB6},
    {1, 0x00},
    {1, 0x02},
    {0, 0xB5},
    {1, 0x02},
    {1, 0x03},
    {1, 0x00},
    {1, 0x04},
    {0, 0xB1},
    {1, 0x80},
    {1, 0x10},
    {0, 0xB4},
    {1, 0x00},
    {0, 0xB7},
    {1, 0xC6},
    {0, 0xC5},
    {1, 0x24},
    {0, 0xE4},
    {1, 0x31},
    {0, 0xE8},
    {1, 0x40},
    {1, 0x8A},
    {1, 0x00},
    {1, 0x00},
    {1, 0x29},
    {1, 0x19},
    {1, 0xA5},
    {1, 0x33},
    {0, 0xC2},
    {1, 0xA7},
    {0, 0xE0},
    {1, 0xF0},
    {1, 0x09},
    {1, 0x13},
    {1, 0x12},
    {1, 0x12},
    {1, 0x2B},
    {1, 0x3C},
    {1, 0x44},
    {1, 0x4B},
    {1, 0x1B},
    {1, 0x18},
    {1, 0x17},
    {1, 0x1D},
    {1, 0x21},
    {0, 0xE1},
    {1, 0xF0},
    {1, 0x09},
    {1, 0x13},
    {1, 0x0C},
    {1, 0x0D},
    {1, 0x27},
    {1, 0x3B},
    {1, 0x44},
    {1, 0x4D},
    {1, 0x0B},
    {1, 0x17},
    {1, 0x17},
    {1, 0x1D},
    {1, 0x21},
    {0, 0x36},
    {1, 0xEC},
    {0, 0xF0},
    {1, 0xC3},
    {0, 0xF0},
    {1, 0x69},
    {0, 0x13},
    {0, 0x11},
    {0, 0x29},
  };
  for (uint32_t i = 0; i < sizeof(init) / sizeof(init[0]); ++i) {
    HAL_StatusTypeDef result = write_byte(init[i][1], init[i][0] ? GPIO_PIN_SET : GPIO_PIN_RESET);
    if (result != HAL_OK) return result;
    if (!init[i][0] && init[i][1] == 0x11) delay_ms(120);
    if (!init[i][0] && init[i][1] == 0x29) delay_ms(20);
  }
  /* Explicit RGB565 and LCDWiki landscape direction 1 (BGR + MV). */
  if (write_byte(0x3A, GPIO_PIN_RESET) != HAL_OK) return HAL_ERROR;
  if (write_byte(0x55, GPIO_PIN_SET) != HAL_OK) return HAL_ERROR;
  if (write_byte(0x36, GPIO_PIN_RESET) != HAL_OK) return HAL_ERROR;
  return write_byte(0x28, GPIO_PIN_SET);
}

HAL_StatusTypeDef st7796_fill(uint16_t rgb565)
{
  static const uint8_t window[][2] = {
    {0,0x2A}, {1,0x00}, {1,0x00}, {1,0x01}, {1,0xDF},
    {0,0x2B}, {1,0x00}, {1,0x00}, {1,0x01}, {1,0x3F}, {0,0x2C}
  };
  for (uint32_t i = 0; i < sizeof(window) / sizeof(window[0]); ++i) {
    HAL_StatusTypeDef result = write_byte(window[i][1], window[i][0] ? GPIO_PIN_SET : GPIO_PIN_RESET);
    if (result != HAL_OK) return result;
  }
  for (uint32_t i = 0; i < sizeof(fill_buffer); i += 2) {
    fill_buffer[i] = (uint8_t)(rgb565 >> 8);
    fill_buffer[i + 1] = (uint8_t)rgb565;
  }
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_6, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET);
  HAL_StatusTypeDef result = HAL_OK;
  for (uint32_t remaining = 480U * 320U * 2U; remaining; remaining -= sizeof(fill_buffer)) {
    result = write_bytes(fill_buffer, sizeof(fill_buffer));
    if (result != HAL_OK) break;
  }
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
  return result;
}

HAL_StatusTypeDef st7796_blit(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2,
                            const uint8_t *pixels)
{
  if (pixels == NULL || x1 > x2 || y1 > y2 || x2 >= 480 || y2 >= 320)
    return HAL_ERROR;
  const uint8_t window[][2] = {
    {0,0x2A}, {1,x1 >> 8}, {1,x1}, {1,x2 >> 8}, {1,x2},
    {0,0x2B}, {1,y1 >> 8}, {1,y1}, {1,y2 >> 8}, {1,y2}, {0,0x2C}
  };
  for (uint32_t i = 0; i < sizeof(window) / sizeof(window[0]); ++i) {
    HAL_StatusTypeDef result = write_byte(window[i][1], window[i][0] ? GPIO_PIN_SET : GPIO_PIN_RESET);
    if (result != HAL_OK) return result;
  }
  HAL_GPIO_WritePin(LCD_DC_GPIO_Port, LCD_DC_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_RESET);
  uint32_t remaining = (uint32_t)(x2 - x1 + 1) * (y2 - y1 + 1) * 2;
  HAL_StatusTypeDef result = HAL_OK;
  while (remaining) {
    uint16_t count = remaining > sizeof(fill_buffer) ? sizeof(fill_buffer) : remaining;
    /* SPI expects the high byte first; leave LVGL's source buffer unchanged. */
    for (uint16_t i = 0; i < count; i += 2) {
      fill_buffer[i] = pixels[i + 1];
      fill_buffer[i + 1] = pixels[i];
    }
    result = write_bytes(fill_buffer, count);
    if (result != HAL_OK) break;
    remaining -= count;
    pixels += count;
  }
  HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_SET);
  return result;
}
