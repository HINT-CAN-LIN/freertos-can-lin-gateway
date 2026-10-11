/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
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
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "cluster_ui.h"
#include "cluster_can.h"

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
/* USER CODE BEGIN Variables */
volatile HAL_StatusTypeDef cluster_ui_status = HAL_OK;
volatile uint32_t ui_stack_free_words;
volatile uint32_t can_stack_free_words;

volatile uint32_t cluster_heap_free_bytes;
volatile TaskHandle_t stack_overflow_task;

/* USER CODE END Variables */
/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 2048 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};

osThreadId_t canTaskHandle;
const osThreadAttr_t canTask_attributes = {
  .name="canTask", .stack_size=512 * 4, .priority=osPriorityAboveNormal
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

void StartDefaultTask(void *argument);
void StartCanTask(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of defaultTask */
  defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);

  /* creation of canTask */
  canTaskHandle = osThreadNew(StartCanTask, NULL, &canTask_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  if (defaultTaskHandle == NULL || canTaskHandle == NULL) Error_Handler();
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartDefaultTask */
/**
  * @brief  Function implementing the defaultTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartDefaultTask */
void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN StartDefaultTask */

  (void)argument;
  cluster_ui_status = cluster_ui_init();
  extern volatile HAL_StatusTypeDef cluster_can_status;
  if (cluster_ui_status == HAL_OK && (osThreadFlagsSet(canTaskHandle, 1U) & osFlagsError))
    cluster_ui_status = HAL_ERROR;
  uint32_t last_led = HAL_GetTick();
  for (;;) {
    if (cluster_ui_status == HAL_OK) {
      cluster_ui_status = cluster_ui_process();
    }
    cluster_heap_free_bytes = xPortGetFreeHeapSize();
    ui_stack_free_words = uxTaskGetStackHighWaterMark(NULL);
    uint32_t now = HAL_GetTick();
    if (now - last_led >= (cluster_ui_status == HAL_OK && cluster_can_status == HAL_OK && cluster_can_current_errors==0 ? 500U : 100U)) {
      last_led = now;
      HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
    }
    osDelay(5);
  }
  /* USER CODE END StartDefaultTask */
}

/* Private application code --------------------------------------------------*/
void StartCanTask(void *argument)
{
  /* USER CODE BEGIN StartCanTask */
  (void)argument;
  /* Avoid CAN startup before the first full-screen paint completes. */
  if (osThreadFlagsWait(1U, osFlagsWaitAny, osWaitForever) & osFlagsError)
    Error_Handler();
  extern volatile HAL_StatusTypeDef cluster_can_status;
  cluster_can_status=cluster_can_init(CLUSTER_CAN_LOOPBACK || !CLUSTER_TEST_INPUT);
  uint32_t wake=osKernelGetTickCount();
  for (;;) {
    if (cluster_can_status == HAL_OK) {
      cluster_can_process();
      cluster_ui_update_input();
    }
    can_stack_free_words=uxTaskGetStackHighWaterMark(NULL);
    wake += 5U; /* FreeRTOS tick is 1 ms. */
    if ((int32_t)(wake-osKernelGetTickCount()) <= 0)
      wake=osKernelGetTickCount()+5U;
    osDelayUntil(wake);
  }
  /* USER CODE END StartCanTask */
}

/* USER CODE BEGIN Application */

void vApplicationStackOverflowHook(TaskHandle_t task, char *name)
{
  (void)name;
  stack_overflow_task = task;
  taskDISABLE_INTERRUPTS();
  for (;;) { }
}

/* USER CODE END Application */



