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
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/

/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

CAN_HandleTypeDef hcan1;

UART_HandleTypeDef huart2;

/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 256 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for canRxQueue */
osMessageQueueId_t canRxQueueHandle;
const osMessageQueueAttr_t canRxQueue_attributes = {
  .name = "canRxQueue"
};
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART2_UART_Init(void);
static void MX_CAN1_Init(void);
void StartDefaultTask(void *argument);

/* USER CODE BEGIN PFP */
static void ProcessCanMessage(const CanRxMessage_t *message);
static void CanMonitorInit(void);
static void MonitorCanMessage(const CanRxMessage_t *message);
static void CheckCanTimeouts(void);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

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

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_CAN1_Init();
  /* USER CODE BEGIN 2 */
  CAN_FilterTypeDef canFilter = {0};

  canFilter.FilterBank = 0;
  canFilter.FilterMode = CAN_FILTERMODE_IDMASK;
  canFilter.FilterScale = CAN_FILTERSCALE_32BIT;
  canFilter.FilterIdHigh = 0x0000;
  canFilter.FilterIdLow = 0x0000;
  canFilter.FilterMaskIdHigh = 0x0000;
  canFilter.FilterMaskIdLow = 0x0000;
  canFilter.FilterFIFOAssignment = CAN_RX_FIFO0;
  canFilter.FilterActivation = ENABLE;
  canFilter.SlaveStartFilterBank = 14;

  if (HAL_CAN_ConfigFilter(&hcan1, &canFilter) != HAL_OK)
  {
    Error_Handler();
  }

  /* USER CODE END 2 */

  /* Init scheduler */
  osKernelInitialize();

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* creation of canRxQueue */
  canRxQueueHandle = osMessageQueueNew (16, sizeof(CanRxMessage_t), &canRxQueue_attributes);

  /* USER CODE BEGIN RTOS_QUEUES */
  if (canRxQueueHandle == NULL)
  {
    Error_Handler();
  }

  if (HAL_CAN_Start(&hcan1) != HAL_OK)
  {
    Error_Handler();
  }

  if (HAL_CAN_ActivateNotification(
          &hcan1,
          CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK)
  {
    Error_Handler();
  }

  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

  /* Initialize leds */
  BSP_LED_Init(LED2);

  /* Initialize USER push-button, will be used to trigger an interrupt each time it's pressed.*/
  BSP_PB_Init(BUTTON_USER, BUTTON_MODE_EXTI);

  /* Start scheduler */
  osKernelStart();

  /* We should never get here as control is now taken by the scheduler */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 16;
  RCC_OscInitStruct.PLL.PLLN = 336;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV4;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
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
  hcan1.Init.Prescaler = 6;
  hcan1.Init.Mode = CAN_MODE_NORMAL;
  hcan1.Init.SyncJumpWidth = CAN_SJW_1TQ;
  hcan1.Init.TimeSeg1 = CAN_BS1_11TQ;
  hcan1.Init.TimeSeg2 = CAN_BS2_2TQ;
  hcan1.Init.TimeTriggeredMode = DISABLE;
  hcan1.Init.AutoBusOff = DISABLE;
  hcan1.Init.AutoWakeUp = DISABLE;
  hcan1.Init.AutoRetransmission = ENABLE;
  hcan1.Init.ReceiveFifoLocked = DISABLE;
  hcan1.Init.TransmitFifoPriority = DISABLE;
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
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
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

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
static uint16_t ReadLe16(const uint8_t *data, uint8_t offset)
{
  return (uint16_t)data[offset]
       | ((uint16_t)data[offset + 1U] << 8U);
}

static void SendUartText(char *text, uint16_t textSize, int textLength)
{
  if ((text == NULL) || (textSize == 0U) || (textLength <= 0))
  {
    return;
  }

  if (textLength >= (int)textSize)
  {
    textLength = (int)textSize - 1;
  }

  HAL_UART_Transmit(&huart2,
                    (uint8_t *)text,
                    (uint16_t)textLength,
                    100U);
}

typedef struct
{
  uint8_t have_frame;
  uint8_t last_alive;
  uint8_t alive_error;
  uint8_t timeout_reported;
  uint32_t last_rx_tick;
} CanMonitorState_t;

static CanMonitorState_t vcuMonitorState;
static CanMonitorState_t motorMonitorState;
static uint32_t canMonitorStartTick;

static void CanMonitorInit(void)
{
  vcuMonitorState.have_frame = 0U;
  vcuMonitorState.last_alive = 0U;
  vcuMonitorState.alive_error = 0U;
  vcuMonitorState.timeout_reported = 0U;
  vcuMonitorState.last_rx_tick = 0U;

  motorMonitorState.have_frame = 0U;
  motorMonitorState.last_alive = 0U;
  motorMonitorState.alive_error = 0U;
  motorMonitorState.timeout_reported = 0U;
  motorMonitorState.last_rx_tick = 0U;

  canMonitorStartTick = HAL_GetTick();
}

static void MonitorAliveCounter(const char *sourceName,
                                CanMonitorState_t *state,
                                uint8_t aliveCounter,
                                uint32_t now)
{
  char text[112];
  int textLength;

  if (!state->have_frame)
  {
    state->have_frame = 1U;
    state->last_alive = aliveCounter;
    state->last_rx_tick = now;
    state->alive_error = 0U;

    textLength = snprintf(text,
                          sizeof(text),
                          "CAN_MONITOR %s ONLINE Alive=%u\r\n",
                          sourceName,
                          (unsigned int)aliveCounter);
    SendUartText(text, (uint16_t)sizeof(text), textLength);

    if (state->timeout_reported != 0U)
    {
      textLength = snprintf(text,
                            sizeof(text),
                            "CAN_MONITOR %s TIMEOUT_RECOVERED Alive=%u\r\n",
                            sourceName,
                            (unsigned int)aliveCounter);
      SendUartText(text, (uint16_t)sizeof(text), textLength);
      state->timeout_reported = 0U;
    }

    return;
  }

  {
    uint8_t expectedAlive = (uint8_t)((state->last_alive + 1U) & 0x0FU);

    if (aliveCounter != expectedAlive)
    {
      if (state->alive_error == 0U)
      {
        textLength = snprintf(
            text,
            sizeof(text),
            "CAN_MONITOR %s ALIVE_ERROR Expected=%u Actual=%u\r\n",
            sourceName,
            (unsigned int)expectedAlive,
            (unsigned int)aliveCounter);
        SendUartText(text, (uint16_t)sizeof(text), textLength);
      }

      state->alive_error = 1U;
    }
    else if (state->alive_error != 0U)
    {
      textLength = snprintf(text,
                            sizeof(text),
                            "CAN_MONITOR %s ALIVE_RECOVERED Alive=%u\r\n",
                            sourceName,
                            (unsigned int)aliveCounter);
      SendUartText(text, (uint16_t)sizeof(text), textLength);
      state->alive_error = 0U;
    }
  }

  state->last_alive = aliveCounter;
  state->last_rx_tick = now;

  if (state->timeout_reported != 0U)
  {
    textLength = snprintf(text,
                          sizeof(text),
                          "CAN_MONITOR %s TIMEOUT_RECOVERED Alive=%u\r\n",
                          sourceName,
                          (unsigned int)aliveCounter);
    SendUartText(text, (uint16_t)sizeof(text), textLength);
    state->timeout_reported = 0U;
  }
}

static void MonitorCanMessage(const CanRxMessage_t *message)
{
  uint32_t now;

  if ((message == NULL) || (message->dlc != DBC_CAN_FRAME_DLC))
  {
    return;
  }

  now = HAL_GetTick();

  switch (message->id)
  {
    case DBC_CAN_ID_VCU_COMMAND:
      MonitorAliveCounter("VCU",
                          &vcuMonitorState,
                          (uint8_t)((message->data[2] >> 4U) & 0x0FU),
                          now);
      break;

    case DBC_CAN_ID_MOTOR_STATUS:
      MonitorAliveCounter("MOTOR",
                          &motorMonitorState,
                          (uint8_t)((message->data[4] >> 2U) & 0x0FU),
                          now);
      break;

    default:
      break;
  }
}

static void CheckCanSourceTimeout(const char *sourceName,
                                  CanMonitorState_t *state,
                                  uint32_t now)
{
  uint32_t referenceTick = state->have_frame
                         ? state->last_rx_tick
                         : canMonitorStartTick;

  if ((uint32_t)(now - referenceTick) >= DBC_CAN_MONITOR_TIMEOUT_MS)
  {
    if (state->timeout_reported == 0U)
    {
      char text[80];
      int textLength = snprintf(text,
                                sizeof(text),
                                "CAN_MONITOR %s TIMEOUT\r\n",
                                sourceName);
      SendUartText(text, (uint16_t)sizeof(text), textLength);
      state->timeout_reported = 1U;
    }
  }
}

static void CheckCanTimeouts(void)
{
  uint32_t now = HAL_GetTick();

  CheckCanSourceTimeout("VCU", &vcuMonitorState, now);
  CheckCanSourceTimeout("MOTOR", &motorMonitorState, now);
}

static void PrintInvalidDlc(const char *messageName, uint8_t dlc)
{
  char text[80];
  int textLength = snprintf(text,
                            sizeof(text),
                            "%s INVALID DLC=%u EXPECTED=8\r\n",
                            messageName,
                            (unsigned int)dlc);

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static const char *DbcGearName(uint8_t gear)
{
  switch (gear)
  {
    case 0U:
      return "P";
    case 1U:
      return "N";
    case 2U:
      return "D";
    case 3U:
      return "R";
    default:
      return "INVALID";
  }
}

static const char *DbcMotorStateName(uint8_t state)
{
  switch (state)
  {
    case 0U:
      return "OFF";
    case 1U:
      return "READY";
    case 2U:
      return "RUN";
    case 3U:
      return "FAIL_SAFE";
    default:
      return "INVALID";
  }
}

static const char *DbcNetworkStateName(uint8_t state)
{
  switch (state)
  {
    case 0U:
      return "NORMAL";
    case 1U:
      return "DEGRADED";
    case 2U:
      return "OFFLINE";
    case 3U:
      return "FAIL_SAFE";
    default:
      return "INVALID";
  }
}

static const char *DbcDoorStatusName(uint8_t state)
{
  switch (state)
  {
    case 0U:
      return "CLOSED_UNLOCKED";
    case 1U:
      return "CLOSED_LOCKED";
    case 2U:
      return "OPEN_UNLOCKED";
    case 3U:
      return "OPEN_LOCKED";
    default:
      return "INVALID";
  }
}

static const char *DbcWindowStatusName(uint8_t state)
{
  switch (state)
  {
    case 0U:
      return "STOPPED";
    case 1U:
      return "MOVING_UP";
    case 2U:
      return "MOVING_DOWN";
    case 3U:
      return "UPPER_LIMIT";
    case 4U:
      return "LOWER_LIMIT";
    case 5U:
      return "FAULT";
    case 6U:
      return "RESERVED";
    default:
      return "INVALID";
  }
}

static const char *DbcFaultCodeName(uint8_t faultCode)
{
  switch (faultCode)
  {
    case 0U:
      return "NONE";
    case 1U:
      return "VCU_TIMEOUT";
    case 2U:
      return "DOOR_ECU_OFFLINE";
    case 3U:
      return "ALIVE_ERROR";
    case 4U:
      return "ECU_OFFLINE";
    case 5U:
      return "QUEUE_DROP";
    case 6U:
      return "WINDOW_ECU_OFFLINE";
    default:
      return "INVALID_OR_RESERVED";
  }
}

static const char *DbcEcuName(uint8_t ecu)
{
  switch (ecu)
  {
    case 0U:
      return "NONE";
    case 1U:
      return "VCU";
    case 2U:
      return "MOTOR";
    case 3U:
      return "GATEWAY";
    case 4U:
      return "CLUSTER";
    case 5U:
      return "DOOR";
    case 6U:
      return "LIGHT";
    case 7U:
      return "WINDOW";
    default:
      return "INVALID_OR_RESERVED";
  }
}

static const char *DbcRecoveryStateName(uint8_t state)
{
  return (state == 0U) ? "ACTIVE" : "CLEARED";
}

static void DecodeVcuCommand(const CanRxMessage_t *message)
{
  VcuCommand_t command = {0};
  char text[128];
  int textLength;

  if (message->dlc != DBC_VCU_COMMAND_DLC)
  {
    PrintInvalidDlc("VCU_CMD", message->dlc);
    return;
  }

  command.torque_request_raw = ReadLe16(message->data, 0U);
  command.gear = message->data[2] & 0x07U;
  command.brake = (message->data[2] >> 3U) & 0x01U;
  command.alive_counter = (message->data[2] >> 4U) & 0x0FU;

  if ((command.torque_request_raw == 0xFFFFU)
      || (command.torque_request_raw > 40000U)
      || (command.gear > 3U))
  {
    textLength = snprintf(text,
                          sizeof(text),
                          "VCU_CMD INVALID TorqueRaw=%u GearRaw=%u\r\n",
                          (unsigned int)command.torque_request_raw,
                          (unsigned int)command.gear);
  }
  else
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "VCU_CMD Torque=%u.%uNm Gear=%s Brake=%s Alive=%u\r\n",
        (unsigned int)(command.torque_request_raw / 10U),
        (unsigned int)(command.torque_request_raw % 10U),
        DbcGearName(command.gear),
        (command.brake != 0U) ? "ON" : "OFF",
        (unsigned int)command.alive_counter);
  }

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void DecodeMotorStatus(const CanRxMessage_t *message)
{
  MotorStatus_t status = {0};
  char text[128];
  int textLength;

  if (message->dlc != DBC_CAN_FRAME_DLC)
  {
    PrintInvalidDlc("MOTOR_STATUS", message->dlc);
    return;
  }

  status.rpm = ReadLe16(message->data, 0U);
  status.torque_applied_raw = ReadLe16(message->data, 2U);
  status.motor_state = message->data[4] & 0x03U;
  status.alive_counter = (message->data[4] >> 2U) & 0x0FU;

  if ((status.rpm == 0xFFFFU)
      || (status.rpm > 12000U)
      || (status.torque_applied_raw == 0xFFFFU)
      || (status.torque_applied_raw > 40000U))
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "MOTOR_STATUS INVALID RPM_RAW=%u TorqueRaw=%u\r\n",
        (unsigned int)status.rpm,
        (unsigned int)status.torque_applied_raw);
  }
  else
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "MOTOR_STATUS RPM=%u Torque=%u.%uNm State=%s Alive=%u\r\n",
        (unsigned int)status.rpm,
        (unsigned int)(status.torque_applied_raw / 10U),
        (unsigned int)(status.torque_applied_raw % 10U),
        DbcMotorStateName(status.motor_state),
        (unsigned int)status.alive_counter);
  }

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void DecodeVehicleStatus(const CanRxMessage_t *message)
{
  VehicleStatus_t status = {0};
  char text[144];
  int textLength;

  if (message->dlc != DBC_CAN_FRAME_DLC)
  {
    PrintInvalidDlc("VEHICLE_STATUS", message->dlc);
    return;
  }

  status.speed_raw = ReadLe16(message->data, 0U);
  status.rpm = ReadLe16(message->data, 2U);
  status.gear = message->data[4] & 0x07U;
  status.brake = (message->data[4] >> 3U) & 0x01U;
  status.network_state = (message->data[4] >> 4U) & 0x03U;

  if ((status.speed_raw == 0xFFFFU)
      || (status.speed_raw > 2500U)
      || (status.rpm == 0xFFFFU)
      || (status.rpm > 12000U)
      || (status.gear > 3U))
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "VEHICLE_STATUS INVALID SpeedRaw=%u RPMRaw=%u GearRaw=%u\r\n",
        (unsigned int)status.speed_raw,
        (unsigned int)status.rpm,
        (unsigned int)status.gear);
  }
  else
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "VEHICLE_STATUS Speed=%u.%ukm/h RPM=%u Gear=%s Brake=%s Network=%s\r\n",
        (unsigned int)(status.speed_raw / 10U),
        (unsigned int)(status.speed_raw % 10U),
        (unsigned int)status.rpm,
        DbcGearName(status.gear),
        (status.brake != 0U) ? "ON" : "OFF",
        DbcNetworkStateName(status.network_state));
  }

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void DecodeBodyStatus(const CanRxMessage_t *message)
{
  BodyStatus_t status = {0};
  char text[160];
  int textLength;

  if (message->dlc != DBC_CAN_FRAME_DLC)
  {
    PrintInvalidDlc("BODY_STATUS", message->dlc);
    return;
  }

  status.reverse_lamp = message->data[0] & 0x01U;
  status.door_open = (message->data[0] >> 1U) & 0x01U;
  status.door_status = message->data[1];
  status.light_status = message->data[2];
  status.window_status = message->data[3];

  if ((status.door_status > 3U)
      || (status.light_status > 63U)
      || (status.window_status > 5U))
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "BODY_STATUS INVALID Door=%u Light=0x%02X Window=%u\r\n",
        (unsigned int)status.door_status,
        status.light_status,
        (unsigned int)status.window_status);
  }
  else
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "BODY_STATUS ReverseLamp=%s DoorOpen=%s Door=%s Light=0x%02X Window=%s\r\n",
        (status.reverse_lamp != 0U) ? "ON" : "OFF",
        (status.door_open != 0U) ? "YES" : "NO",
        DbcDoorStatusName(status.door_status),
        status.light_status,
        DbcWindowStatusName(status.window_status));
  }

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void DecodeGatewayStatus(const CanRxMessage_t *message)
{
  GatewayStatus_t status = {0};
  char text[96];
  int textLength;

  if (message->dlc != DBC_CAN_FRAME_DLC)
  {
    PrintInvalidDlc("GATEWAY_STATUS", message->dlc);
    return;
  }

  status.gateway_alive = message->data[0] & 0x0FU;
  status.queue_usage = message->data[1];

  if (status.queue_usage > 100U)
  {
    textLength = snprintf(text,
                          sizeof(text),
                          "GATEWAY_STATUS INVALID QueueUsage=%u\r\n",
                          (unsigned int)status.queue_usage);
  }
  else
  {
    textLength = snprintf(text,
                          sizeof(text),
                          "GATEWAY_STATUS Alive=%u QueueUsage=%u%%\r\n",
                          (unsigned int)status.gateway_alive,
                          (unsigned int)status.queue_usage);
  }

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void DecodeFaultStatus(const CanRxMessage_t *message)
{
  FaultStatus_t status = {0};
  char text[144];
  int textLength;

  if (message->dlc != DBC_CAN_FRAME_DLC)
  {
    PrintInvalidDlc("FAULT_STATUS", message->dlc);
    return;
  }

  status.fault_code = message->data[0];
  status.ecu_offline = message->data[1] & 0x0FU;
  status.recovery_state = (message->data[1] >> 4U) & 0x01U;
  status.system_state = (message->data[1] >> 5U) & 0x03U;

  if ((status.fault_code > 6U) || (status.ecu_offline > 7U))
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "FAULT_STATUS INVALID FaultCode=%u ECU=%u\r\n",
        (unsigned int)status.fault_code,
        (unsigned int)status.ecu_offline);
  }
  else
  {
    textLength = snprintf(
        text,
        sizeof(text),
        "FAULT_STATUS Code=%s ECU=%s Recovery=%s System=%s\r\n",
        DbcFaultCodeName(status.fault_code),
        DbcEcuName(status.ecu_offline),
        DbcRecoveryStateName(status.recovery_state),
        DbcNetworkStateName(status.system_state));
  }

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void PrintRawCanMessage(const CanRxMessage_t *message)
{
  char text[96];
  int textLength = snprintf(
      text,
      sizeof(text),
      "CAN RX ID=0x%03lX DLC=%u DATA=%02X %02X %02X %02X %02X %02X %02X %02X\r\n",
      (unsigned long)message->id,
      (unsigned int)message->dlc,
      message->data[0],
      message->data[1],
      message->data[2],
      message->data[3],
      message->data[4],
      message->data[5],
      message->data[6],
      message->data[7]);

  SendUartText(text, (uint16_t)sizeof(text), textLength);
}

static void ProcessCanMessage(const CanRxMessage_t *message)
{
  if (message == NULL)
  {
    return;
  }

  MonitorCanMessage(message);

  switch (message->id)
  {
    case DBC_CAN_ID_VCU_COMMAND:
      DecodeVcuCommand(message);
      break;
    case DBC_CAN_ID_MOTOR_STATUS:
      DecodeMotorStatus(message);
      break;
    case DBC_CAN_ID_VEHICLE_STATUS:
      DecodeVehicleStatus(message);
      break;
    case DBC_CAN_ID_BODY_STATUS:
      DecodeBodyStatus(message);
      break;
    case DBC_CAN_ID_GATEWAY_STATUS:
      DecodeGatewayStatus(message);
      break;
    case DBC_CAN_ID_FAULT_STATUS:
      DecodeFaultStatus(message);
      break;
    default:
      PrintRawCanMessage(message);
      break;
  }
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
  CAN_RxHeaderTypeDef rxHeader;
  uint8_t rxData[8];
  CanRxMessage_t rxMessage = {0};

  if (hcan->Instance != CAN1)
  {
    return;
  }

  if (HAL_CAN_GetRxMessage(hcan,
                           CAN_RX_FIFO0,
                           &rxHeader,
                           rxData) == HAL_OK)
  {
    if (rxHeader.IDE == CAN_ID_STD)
    {
      rxMessage.id = rxHeader.StdId;
    }
    else
    {
      rxMessage.id = rxHeader.ExtId;
    }

    rxMessage.dlc = (uint8_t)rxHeader.DLC;

    for (uint8_t i = 0U; i < 8U; i++)
    {
      rxMessage.data[i] = rxData[i];
    }

    if (canRxQueueHandle != NULL)
    {
      (void)osMessageQueuePut(canRxQueueHandle,
                              &rxMessage,
                              0U,
                              0U);
    }
  }
}

/* USER CODE END 4 */

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN 5 */

  static const uint8_t boot_message[] =
      "Gateway ECU boot\r\n";

  CanRxMessage_t rxMessage = {0};
  uint32_t lastLedToggleTick;

  (void)argument;

  CanMonitorInit();
  lastLedToggleTick = HAL_GetTick();

  HAL_UART_Transmit(&huart2,
                    (uint8_t *)boot_message,
                    sizeof(boot_message) - 1U,
                    100U);

  for (;;)
  {
    uint32_t now = HAL_GetTick();

    if ((uint32_t)(now - lastLedToggleTick) >= DBC_LED_TOGGLE_PERIOD_MS)
    {
      BSP_LED_Toggle(LED2);
      lastLedToggleTick = now;
    }

    while (osMessageQueueGet(canRxQueueHandle,
                             &rxMessage,
                             NULL,
                             0U) == osOK)
    {
      ProcessCanMessage(&rxMessage);
    }

    CheckCanTimeouts();
    osDelay(DBC_CAN_MONITOR_SERVICE_PERIOD_MS);
  }

  /* USER CODE END 5 */
}

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM6 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM6)
  {
    HAL_IncTick();
  }
  /* USER CODE BEGIN Callback 1 */

  /* USER CODE END Callback 1 */
}

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
