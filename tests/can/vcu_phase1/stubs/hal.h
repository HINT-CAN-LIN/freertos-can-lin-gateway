/* Force-include to substitute only the hardware HAL boundary in host tests. */
#define __CAN_H__
#include <stdint.h>
typedef enum { HAL_OK, HAL_ERROR, HAL_BUSY, HAL_TIMEOUT } HAL_StatusTypeDef;
typedef struct { struct { uint32_t Mode; } Init; } CAN_HandleTypeDef;
typedef struct {
    uint32_t StdId, ExtId, IDE, RTR, DLC, TransmitGlobalTime;
} CAN_TxHeaderTypeDef;
typedef struct { uint32_t unused; } CAN_RxHeaderTypeDef;
#define CAN_MODE_LOOPBACK 1U
#define CAN_RX_FIFO0 0U
#define CAN_ID_STD 0U
#define CAN_RTR_DATA 0U
#define DISABLE 0U
extern CAN_HandleTypeDef hcan1;
uint32_t HAL_CAN_GetRxFifoFillLevel(CAN_HandleTypeDef *, uint32_t);
HAL_StatusTypeDef HAL_CAN_GetRxMessage(CAN_HandleTypeDef *, uint32_t,
                                     CAN_RxHeaderTypeDef *, uint8_t *);
uint32_t HAL_CAN_GetTxMailboxesFreeLevel(CAN_HandleTypeDef *);
HAL_StatusTypeDef HAL_CAN_AddTxMessage(CAN_HandleTypeDef *,
                                     const CAN_TxHeaderTypeDef *,
                                     const uint8_t *, uint32_t *);
