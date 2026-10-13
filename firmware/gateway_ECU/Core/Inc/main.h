/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f4xx_hal.h"

#include "stm32f4xx_nucleo.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */
typedef struct
{
  uint32_t id;
  uint8_t dlc;
  uint8_t data[8];
} CanRxMessage_t;

typedef struct
{
  uint16_t torque_request_raw;
  uint8_t gear;
  uint8_t brake;
  uint8_t alive_counter;
} VcuCommand_t;

typedef struct
{
  uint16_t rpm;
  uint16_t torque_applied_raw;
  uint8_t motor_state;
  uint8_t alive_counter;
} MotorStatus_t;

typedef struct
{
  uint16_t speed_raw;
  uint16_t rpm;
  uint8_t gear;
  uint8_t brake;
  uint8_t network_state;
} VehicleStatus_t;

typedef struct
{
  uint8_t reverse_lamp;
  uint8_t door_open;
  uint8_t door_status;
  uint8_t light_status;
  uint8_t window_status;
} BodyStatus_t;

typedef struct
{
  uint8_t gateway_alive;
  uint8_t queue_usage;
} GatewayStatus_t;

typedef struct
{
  uint8_t fault_code;
  uint8_t ecu_offline;
  uint8_t recovery_state;
  uint8_t system_state;
} FaultStatus_t;
/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define USART_TX_Pin GPIO_PIN_2
#define USART_TX_GPIO_Port GPIOA
#define USART_RX_Pin GPIO_PIN_3
#define USART_RX_GPIO_Port GPIOA
#define TMS_Pin GPIO_PIN_13
#define TMS_GPIO_Port GPIOA
#define TCK_Pin GPIO_PIN_14
#define TCK_GPIO_Port GPIOA
#define SWO_Pin GPIO_PIN_3
#define SWO_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */
#define DBC_CAN_ID_VCU_COMMAND  (0x100U)
#define DBC_CAN_ID_MOTOR_STATUS (0x110U)
#define DBC_CAN_ID_VEHICLE_STATUS (0x120U)
#define DBC_CAN_ID_BODY_STATUS  (0x200U)
#define DBC_CAN_ID_GATEWAY_STATUS (0x300U)
#define DBC_CAN_ID_FAULT_STATUS (0x310U)
#define DBC_VCU_COMMAND_DLC    (8U)
#define DBC_CAN_FRAME_DLC      (8U)
#define DBC_CAN_MONITOR_TIMEOUT_MS (50U)
#define DBC_CAN_MONITOR_SERVICE_PERIOD_MS (10U)
#define DBC_LED_TOGGLE_PERIOD_MS (500U)

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
