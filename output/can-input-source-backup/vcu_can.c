#include "vcu_can.h"
#include <stddef.h>
#include "vcu_pc_can.h"

/* One task owns CAN input and its timeout. UART input is rejected in this build. */
void vcu_pc_can_poll(void)
{
    static bool active;
    static uint16_t sequence;
    static uint32_t last;
    uint32_t now=HAL_GetTick();
    if (active && (uint32_t)(now-last)>=PC_INPUT_TIMEOUT_MS) {
        vcu_driver_input_reset();
        active=false;
    }
    for (unsigned i=0;i<3;i++) {
        CAN_RxHeaderTypeDef h;
        uint8_t d[8];
        if (!HAL_CAN_GetRxFifoFillLevel(&hcan1,CAN_RX_FIFO0)) break;
        if (HAL_CAN_GetRxMessage(&hcan1,CAN_RX_FIFO0,&h,d)!=HAL_OK) break;
        if (h.IDE!=CAN_ID_STD || h.RTR!=CAN_RTR_DATA || h.StdId!=PC_INPUT_CAN_ID || h.DLC!=8 || !pc_valid(d)) continue;
        uint16_t seq=(uint16_t)d[1] | ((uint16_t)d[2]<<8);
        uint16_t delta=(uint16_t)(seq-sequence);
        uint8_t status=0;
        if (!pc_safe(d) && (!active || delta==0 || delta>=32768U)) status=2;
        if (!status) {
            vcu_driver_inputs_t inputs={0};
            inputs.ignition_state=(vcu_ignition_state_t)d[3];
            inputs.accelerator_percent=d[4];
            inputs.brake=d[5]!=0;
            inputs.gear=(vcu_gear_t)d[6];
            vcu_driver_input_update(&inputs,15);
            sequence=seq; last=now; active=true;
        }
        uint8_t ack[8]={1,d[1],d[2],status,d[3],d[4],d[6],0};
        ack[7]=pc_crc(ack);
        CAN_TxHeaderTypeDef tx={0}; uint32_t mailbox;
        tx.StdId=PC_ACK_CAN_ID; tx.IDE=CAN_ID_STD; tx.RTR=CAN_RTR_DATA; tx.DLC=8;
        if (HAL_CAN_GetTxMailboxesFreeLevel(&hcan1)) (void)HAL_CAN_AddTxMessage(&hcan1,&tx,ack,&mailbox);
    }
}

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
