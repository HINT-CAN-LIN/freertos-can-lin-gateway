/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2026 STMicroelectronics.
 * All rights reserved.
 *
 * This software is licensed under terms that can be found in the LICENSE file
 * in the root directory of this software component.
 * If no LICENSE file comes with this software, it is provided AS-IS.
 *
 ******************************************************************************
 */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os2.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "motor_runtime.h"
#include "motor_can.h"
#include "motor_rtos.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* Demonstrator calibration, NOT physical motor torque/RPM measurements. */
#define MOTOR_DEMO_RPM_MAX 12000u
#define MOTOR_DEMO_RPM_PER_NM 3.0f
/* Bit 0..3 reverses the corresponding motor for mirrored mounting. */
#define MOTOR_DIRECTION_INVERT_MASK 0x00u
/* The bundled CANgaroo script increments Alive at 10 ms; use strict checking.
 * Set 1 ONLY for a deliberate fixed-payload Raw TX bench experiment. */
#define MOTOR_CANGAROO_FIXED_ALIVE 0
#define SERVO1_CENTER_US 1500u
#define SERVO2_CENTER_US 1500u
/* bit0=servo1, bit1=servo2. Set e.g. 0x02 for mirrored servo2 mounting. */
#define SERVO_DIRECTION_INVERT_MASK 0x00u
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

CAN_HandleTypeDef hcan1;
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */

/* CAN TX Debug variables */
volatile HAL_StatusTypeDef g_canTxResult = HAL_ERROR;
volatile uint32_t g_canTxSuccessCount = 0;
volatile uint32_t g_canTxErrorCount = 0;
volatile uint32_t g_canTxMailbox = 0;
volatile uint32_t g_canRxDropCount = 0;
volatile uint32_t g_motorDuty = 0;
volatile int32_t g_motorDirection = 0;
volatile uint32_t g_servo1PulseUs = 1500;
volatile uint32_t g_servo2PulseUs = 1500;
volatile int32_t g_steeringTargetRaw = 0;
volatile uint32_t g_motorFaultFlags = 0;
volatile uint32_t g_motorFirmwareRevision = MOTOR_FIRMWARE_REVISION;
static MotorDrive physicalDrive;
static bool motorPwmReady = false;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_CAN1_Init(void);
static void MX_USART2_UART_Init(void);

/* Task prototypes and RTOS2 object IDs are declared in motor_rtos.h. */

/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
const MotorConfig *MotorBoard_Config(void)
{
  static const MotorConfig config = {
    .torque_to_rpm = MOTOR_DEMO_RPM_PER_NM,
    .alpha = 0.10f, .decay_alpha = 0.20f,
    .rpm_max = MOTOR_DEMO_RPM_MAX, .model_period_ms = 10,
    .policy = motor_command_policy,
    .bench_allow_repeated_alive = MOTOR_CANGAROO_FIXED_ALIVE != 0
  };
  return &config;
}

bool MotorBoard_TransmitHardware(const MotorCanFrame *frame)
{
  CAN_TxHeaderTypeDef header = {0};
  if (frame == NULL || frame->extended || frame->remote || frame->dlc != 8u)
    return false;
  header.StdId = frame->id;
  header.IDE = CAN_ID_STD;
  header.RTR = CAN_RTR_DATA;
  header.DLC = frame->dlc;
  if (HAL_CAN_GetTxMailboxesFreeLevel(&hcan1) == 0u) {
    g_canTxErrorCount++;
    return false;
  }
  g_canTxResult = HAL_CAN_AddTxMessage(&hcan1, &header,
                                     (uint8_t *)frame->data, (uint32_t *)&g_canTxMailbox);
  if (g_canTxResult == HAL_OK) g_canTxSuccessCount++;
  else g_canTxErrorCount++;
  return g_canTxResult == HAL_OK;
}

static void motor_pwm_stop(void)
{
  if (!motorPwmReady) return;
  TIM1->CCR1 = TIM1->CCR2 = 0;
  TIM3->CCR1 = TIM3->CCR2 = TIM3->CCR3 = TIM3->CCR4 = 0;
  TIM4->CCR1 = TIM4->CCR2 = 0;
  /* Transfer zero immediately rather than waiting for the next PWM period. */
  TIM1->EGR = TIM3->EGR = TIM4->EGR = TIM_EGR_UG;
}

static void motor_timer_init(TIM_TypeDef *timer, bool four_channels)
{
  timer->CR1 = 0;
  timer->PSC = 0;
  timer->ARR = MOTOR_PWM_COUNTS - 1u;
  timer->CCR1 = timer->CCR2 = timer->CCR3 = timer->CCR4 = 0;
  /* PWM mode 1, active high, compare preload. */
  timer->CCMR1 = (6u << 4) | TIM_CCMR1_OC1PE | (6u << 12) | TIM_CCMR1_OC2PE;
  timer->CCMR2 = four_channels ?
      (6u << 4) | TIM_CCMR2_OC3PE | (6u << 12) | TIM_CCMR2_OC4PE : 0;
  timer->CCER = TIM_CCER_CC1E | TIM_CCER_CC2E |
      (four_channels ? TIM_CCER_CC3E | TIM_CCER_CC4E : 0);
  if (timer == TIM1) timer->BDTR = TIM_BDTR_MOE;
  timer->EGR = TIM_EGR_UG;
  timer->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;
}

static void motor_pwm_init(void)
{
  GPIO_InitTypeDef gpio = {0};
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_TIM1_CLK_ENABLE();
  __HAL_RCC_TIM3_CLK_ENABLE();
  __HAL_RCC_TIM4_CLK_ENABLE();
  motor_timer_init(TIM1, false);
  motor_timer_init(TIM3, true);
  motor_timer_init(TIM4, false);
  gpio.Mode = GPIO_MODE_AF_PP;
  gpio.Pull = GPIO_PULLDOWN;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Pin = GPIO_PIN_8 | GPIO_PIN_9;
  gpio.Alternate = GPIO_AF1_TIM1;
  HAL_GPIO_Init(GPIOA, &gpio);
  gpio.Pin = GPIO_PIN_0 | GPIO_PIN_1 | GPIO_PIN_4 | GPIO_PIN_5;
  gpio.Alternate = GPIO_AF2_TIM3;
  HAL_GPIO_Init(GPIOB, &gpio);
  gpio.Pin = GPIO_PIN_6 | GPIO_PIN_7;
  gpio.Alternate = GPIO_AF2_TIM4;
  HAL_GPIO_Init(GPIOB, &gpio);
  motor_drive_init(&physicalDrive, HAL_GetTick());
  motorPwmReady = true;
  motor_pwm_stop();
  /* TIM2 is independent of the 20 kHz DC motor timers: 84MHz/84/20000=50Hz. */
  __HAL_RCC_TIM2_CLK_ENABLE();
  TIM2->CR1 = 0;
  TIM2->PSC = 83;
  TIM2->ARR = 19999;
  TIM2->CCR1 = SERVO1_CENTER_US;
  TIM2->CCR2 = SERVO2_CENTER_US;
  TIM2->CCMR1 = (6u << 4) | TIM_CCMR1_OC1PE | (6u << 12) | TIM_CCMR1_OC2PE;
  TIM2->CCER = TIM_CCER_CC1E | TIM_CCER_CC2E;
  TIM2->EGR = TIM_EGR_UG;
  gpio.Pin = GPIO_PIN_0 | GPIO_PIN_1;
  gpio.Alternate = GPIO_AF1_TIM2;
  HAL_GPIO_Init(GPIOA, &gpio);
  TIM2->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;
}

void MotorBoard_Apply(const MotorApp *state, uint32_t now_ms)
{
  volatile uint32_t *const a[4] = { &TIM1->CCR1, &TIM3->CCR1, &TIM3->CCR3, &TIM4->CCR1 };
  volatile uint32_t *const b[4] = { &TIM1->CCR2, &TIM3->CCR2, &TIM3->CCR4, &TIM4->CCR2 };
  motor_drive_step(&physicalDrive, state, now_ms);
  g_motorDuty = physicalDrive.duty;
  g_motorDirection = physicalDrive.direction;
  if (!motorPwmReady) return;
  g_steeringTargetRaw = state->steering_target_raw;
  g_motorFaultFlags = state->status.fault_flags;
  g_servo1PulseUs = motor_servo_pulse_us(state->steering_target_raw,
      SERVO1_CENTER_US, (SERVO_DIRECTION_INVERT_MASK & 1u) != 0);
  g_servo2PulseUs = motor_servo_pulse_us(state->steering_target_raw,
      SERVO2_CENTER_US, (SERVO_DIRECTION_INVERT_MASK & 2u) != 0);
  TIM2->CCR1 = g_servo1PulseUs;
  TIM2->CCR2 = g_servo2PulseUs;
  if (physicalDrive.duty == 0) { motor_pwm_stop(); return; }
  for (unsigned i = 0; i < 4; ++i) {
    bool forward = physicalDrive.direction > 0;
    if (MOTOR_DIRECTION_INVERT_MASK & (1u << i)) forward = !forward;
    *a[i] = forward ? physicalDrive.duty : 0;
    *b[i] = forward ? 0 : physicalDrive.duty;
  }
}
uint32_t MotorBoard_NowMs(void) { return HAL_GetTick(); }
void MotorBoard_EnableRx(void)
{
  if (HAL_CAN_ActivateNotification(&hcan1, CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK)
    Error_Handler();
}
void MotorBoard_Heartbeat(void) { BSP_LED_Toggle(LED2); }
void MotorBoard_SafeStop(void)
{
  motor_pwm_stop();
  if (motorPwmReady && (RCC->APB1ENR & RCC_APB1ENR_TIM2EN)) {
    TIM2->CCR1 = SERVO1_CENTER_US;
    TIM2->CCR2 = SERVO2_CENTER_US;
    TIM2->EGR = TIM_EGR_UG;
    g_motorDuty = 0;
    g_motorDirection = 0;
    g_steeringTargetRaw = 0;
    g_servo1PulseUs = SERVO1_CENTER_US;
    g_servo2PulseUs = SERVO2_CENTER_US;
  }
}
/* USER CODE END 0 */

/**
 * @brief  The application entry point.
 * @retval int
 */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_CAN1_Init();
  MX_USART2_UART_Init();

  /* USER CODE BEGIN 2 */

  motor_pwm_init();

  /*
   * CAN Bring-up Filter
   * Accept only DBC VCU_Command/Gateway_Status standard data frames.
   */
  CAN_FilterTypeDef canFilter = {0};

  canFilter.FilterBank = 0;
  canFilter.FilterMode = CAN_FILTERMODE_IDMASK;
  canFilter.FilterScale = CAN_FILTERSCALE_32BIT;

  canFilter.FilterIdHigh = MOTOR_CAN_VCU_ID << 5;
  canFilter.FilterIdLow = 0x0000;

  canFilter.FilterMaskIdHigh = 0xFFE0;
  canFilter.FilterMaskIdLow = 0x0006; /* Standard data frames only. */

  canFilter.FilterFIFOAssignment = CAN_RX_FIFO0;
  canFilter.FilterActivation = ENABLE;
  canFilter.SlaveStartFilterBank = 14;

  if (HAL_CAN_ConfigFilter(&hcan1, &canFilter) != HAL_OK)
  {
    Error_Handler();
  }

  canFilter.FilterBank = 1;
  canFilter.FilterIdHigh = MOTOR_CAN_GATEWAY_ID << 5;
  if (HAL_CAN_ConfigFilter(&hcan1, &canFilter) != HAL_OK) Error_Handler();

  /*
   * CAN Peripheral Start
   */
  if (HAL_CAN_Start(&hcan1) != HAL_OK)
  {
    Error_Handler();
  }

  /* USER CODE END 2 */

  /* Initialize CMSIS-RTOS2 before creating queues, mutexes and threads. */
  if (osKernelInitialize() != osOK) Error_Handler();
  MX_FREERTOS_Init();

  /* Initialize leds */
  BSP_LED_Init(LED2);

  /*
   * Initialize USER push-button
   */
  BSP_PB_Init(BUTTON_USER, BUTTON_MODE_EXTI);

  /* Start scheduler */
  if (osKernelStart() != osOK) Error_Handler();

  /*
   * 정상이라면 여기까지 내려오지 않음
   */
  while (1)
  {
  }
}

/**
 * @brief System Clock Configuration
 * @retval None
 */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  __HAL_RCC_PWR_CLK_ENABLE();

  __HAL_PWR_VOLTAGESCALING_CONFIG(
      PWR_REGULATOR_VOLTAGE_SCALE3);

  /*
   * HSI + PLL
   */
  RCC_OscInitStruct.OscillatorType =
      RCC_OSCILLATORTYPE_HSI;

  RCC_OscInitStruct.HSIState =
      RCC_HSI_ON;

  RCC_OscInitStruct.HSICalibrationValue =
      RCC_HSICALIBRATION_DEFAULT;

  RCC_OscInitStruct.PLL.PLLState =
      RCC_PLL_ON;

  RCC_OscInitStruct.PLL.PLLSource =
      RCC_PLLSOURCE_HSI;

  RCC_OscInitStruct.PLL.PLLM = 16;
  RCC_OscInitStruct.PLL.PLLN = 336;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV4;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;

  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /*
   * CPU / AHB / APB clocks
   */
  RCC_ClkInitStruct.ClockType =
      RCC_CLOCKTYPE_HCLK |
      RCC_CLOCKTYPE_SYSCLK |
      RCC_CLOCKTYPE_PCLK1 |
      RCC_CLOCKTYPE_PCLK2;

  RCC_ClkInitStruct.SYSCLKSource =
      RCC_SYSCLKSOURCE_PLLCLK;

  RCC_ClkInitStruct.AHBCLKDivider =
      RCC_SYSCLK_DIV1;

  RCC_ClkInitStruct.APB1CLKDivider =
      RCC_HCLK_DIV2;

  RCC_ClkInitStruct.APB2CLKDivider =
      RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(
          &RCC_ClkInitStruct,
          FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
 * @brief CAN1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_CAN1_Init(void)
{
  /* USER CODE BEGIN CAN1_Init 0 */

  /* USER CODE END CAN1_Init 0 */

  /* USER CODE BEGIN CAN1_Init 1 */

  /* USER CODE END CAN1_Init 1 */

  hcan1.Instance = CAN1;

  /*
   * CAN = 500 kbps
   *
   * CAN Clock = 42 MHz
   * Prescaler = 6
   * BS1 = 11 TQ
   * BS2 = 2 TQ
   *
   * 42 MHz / 6 / (1 + 11 + 2)
   * = 500 kbps
   */
  hcan1.Init.Prescaler = 6;

  hcan1.Init.Mode =
      CAN_MODE_NORMAL;

  hcan1.Init.SyncJumpWidth =
      CAN_SJW_1TQ;

  hcan1.Init.TimeSeg1 =
      CAN_BS1_11TQ;

  hcan1.Init.TimeSeg2 =
      CAN_BS2_2TQ;

  hcan1.Init.TimeTriggeredMode =
      DISABLE;

  hcan1.Init.AutoBusOff =
      ENABLE;

  hcan1.Init.AutoWakeUp =
      DISABLE;

  hcan1.Init.AutoRetransmission =
      ENABLE;

  hcan1.Init.ReceiveFifoLocked =
      DISABLE;

  hcan1.Init.TransmitFifoPriority =
      DISABLE;

  if (HAL_CAN_Init(&hcan1) != HAL_OK)
  {
    Error_Handler();
  }

  /* USER CODE BEGIN CAN1_Init 2 */

  /* USER CODE END CAN1_Init 2 */
}

/**
 * @brief USART2 Initialization Function
 * @param None
 * @retval None
 */
static void MX_USART2_UART_Init(void)
{
  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */

  huart2.Instance = USART2;

  huart2.Init.BaudRate =
      115200;

  huart2.Init.WordLength =
      UART_WORDLENGTH_8B;

  huart2.Init.StopBits =
      UART_STOPBITS_1;

  huart2.Init.Parity =
      UART_PARITY_NONE;

  huart2.Init.Mode =
      UART_MODE_TX_RX;

  huart2.Init.HwFlowCtl =
      UART_HWCONTROL_NONE;

  huart2.Init.OverSampling =
      UART_OVERSAMPLING_16;

  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }

  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */
}

/**
 * @brief GPIO Initialization Function
 * @param None
 * @retval None
 */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /*
   * GPIO Ports Clock Enable
   */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/**
 * @brief CAN RX FIFO0 message pending callback
 */
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
  if (hcan->Instance != CAN1) return;
  while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO0) != 0u) {
    CAN_RxHeaderTypeDef header;
    MotorCanFrame frame = {0};
    uint32_t rx_ms = HAL_GetTick();
    if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &header, frame.data) != HAL_OK) break;
    if (header.IDE != CAN_ID_STD || header.RTR != CAN_RTR_DATA ||
        (header.StdId != MOTOR_CAN_VCU_ID && header.StdId != MOTOR_CAN_GATEWAY_ID))
      continue;
    frame.id = header.StdId;
    frame.dlc = header.DLC;
    MotorRTOS_CaptureISR(&frame, rx_ms);
  }
}

/* USER CODE END 4 */

/**
 * @brief This function is executed in case of error occurrence.
 * @retval None
 */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  __disable_irq();
  MotorBoard_SafeStop();

  while (1)
  {
  }

  /* USER CODE END Error_Handler_Debug */
}

#ifdef USE_FULL_ASSERT

/**
 * @brief Reports the name of the source file and the source line number
 *        where the assert_param error has occurred.
 * @param file: pointer to the source file name
 * @param line: assert_param error line source number
 * @retval None
 */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */

  /* USER CODE END 6 */
}

#endif /* USE_FULL_ASSERT */
