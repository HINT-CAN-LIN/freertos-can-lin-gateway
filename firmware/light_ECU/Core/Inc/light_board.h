#ifndef LIGHT_BOARD_H
#define LIGHT_BOARD_H
/* Breadboard: each output -> 470 ohm -> LED anode; cathode -> common GND.
 * Active-high indicator LEDs only; PA5 continues to mirror active outputs. */
#define LIGHT_EXTERNAL_OUTPUTS 1
#define LIGHT_HEAD_PORT GPIOB
#define LIGHT_HEAD_PIN GPIO_PIN_5
#define LIGHT_LEFT_PORT GPIOB
#define LIGHT_LEFT_PIN GPIO_PIN_4
#define LIGHT_RIGHT_PORT GPIOB
#define LIGHT_RIGHT_PIN GPIO_PIN_10
#define LIGHT_REVERSE_PORT GPIOA
#define LIGHT_REVERSE_PIN GPIO_PIN_8
#define LIGHT_BRAKE_PORT GPIOC
#define LIGHT_BRAKE_PIN GPIO_PIN_7
#define LIGHT_SLP_CONTROL 0
/* For SLP control define LIGHT_SLP_PORT, LIGHT_SLP_PIN,
 * LIGHT_SLP_ACTIVE (GPIO_PIN_SET or GPIO_PIN_RESET) and enable above.
 * Enable the matching GPIO port clock in Light_BoardInit if not A/B/C. */
static inline void Light_BoardInit(void) {
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  GPIO_InitTypeDef gpio = {0};
  gpio.Mode = GPIO_MODE_OUTPUT_PP; gpio.Pull = GPIO_NOPULL;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
#if LIGHT_EXTERNAL_OUTPUTS
#define LIGHT_INIT_OUTPUT(name) HAL_GPIO_WritePin(LIGHT_##name##_PORT, LIGHT_##name##_PIN, GPIO_PIN_RESET); gpio.Pin = LIGHT_##name##_PIN; HAL_GPIO_Init(LIGHT_##name##_PORT, &gpio)
  LIGHT_INIT_OUTPUT(HEAD); LIGHT_INIT_OUTPUT(LEFT); LIGHT_INIT_OUTPUT(RIGHT);
  LIGHT_INIT_OUTPUT(REVERSE); LIGHT_INIT_OUTPUT(BRAKE);
#undef LIGHT_INIT_OUTPUT
#endif
#if LIGHT_SLP_CONTROL
  HAL_GPIO_WritePin(LIGHT_SLP_PORT, LIGHT_SLP_PIN, LIGHT_SLP_ACTIVE);
  gpio.Pin = LIGHT_SLP_PIN; HAL_GPIO_Init(LIGHT_SLP_PORT, &gpio);
#endif
  (void)gpio;
}
static inline void Light_BoardWrite(uint8_t lamps) {
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, lamps ? GPIO_PIN_SET : GPIO_PIN_RESET);
#if LIGHT_EXTERNAL_OUTPUTS
#define LIGHT_WRITE(name, bit) HAL_GPIO_WritePin(LIGHT_##name##_PORT, LIGHT_##name##_PIN, (lamps & (bit)) ? GPIO_PIN_SET : GPIO_PIN_RESET)
  LIGHT_WRITE(HEAD, 1u); LIGHT_WRITE(LEFT, 2u); LIGHT_WRITE(RIGHT, 4u);
  LIGHT_WRITE(REVERSE, 16u); LIGHT_WRITE(BRAKE, 32u);
#undef LIGHT_WRITE
#endif
}
#endif
