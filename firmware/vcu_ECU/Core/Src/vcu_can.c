#include "vcu_can.h"
#include <stddef.h>
HAL_StatusTypeDef vcu_can_send(const uint8_t data[VCU_COMMAND_DLC])
{
    CAN_TxHeaderTypeDef header = {0};
    uint32_t mailbox;
    if (data == NULL) {
        return HAL_ERROR;
    }

    /* The existing filter receives our own frames in loopback. Drain FIFO0
     * by polling so Phase 1 does not accumulate RX overrun. No routing.
     * Bound work to bxCAN's three-entry FIFO; normal-mode RX is untouched.
     */
    if (hcan1.Init.Mode == CAN_MODE_LOOPBACK) {
        for (unsigned i = 0; i < 3U; ++i) {
            CAN_RxHeaderTypeDef rx_header;
            uint8_t rx_data[8];
            if (HAL_CAN_GetRxFifoFillLevel(&hcan1, CAN_RX_FIFO0) == 0U) {
                break;
            }
            if (HAL_CAN_GetRxMessage(&hcan1, CAN_RX_FIFO0,
                                    &rx_header, rx_data) != HAL_OK) {
                return HAL_ERROR;
            }
        }
    }

    if (HAL_CAN_GetTxMailboxesFreeLevel(&hcan1) == 0U) {
        return HAL_BUSY;
    }
    header.StdId = VCU_COMMAND_CAN_ID;
    header.IDE = CAN_ID_STD;
    header.RTR = CAN_RTR_DATA;
    header.DLC = VCU_COMMAND_DLC;
    header.TransmitGlobalTime = DISABLE;
    return HAL_CAN_AddTxMessage(&hcan1, &header, data, &mailbox);
}
