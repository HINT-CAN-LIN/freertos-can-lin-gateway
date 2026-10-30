/* Exercise the actual firmware poller with a mocked HAL (no motor hardware). */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "vcu_app.h"
#include "vcu_command.h"
#define VCU_CAN_H
typedef int HAL_StatusTypeDef;
#define HAL_OK 0
#define HAL_ERROR 1
#define HAL_BUSY 2
#define CAN_RX_FIFO0 0
#define CAN_ID_STD 0
#define CAN_RTR_DATA 0
#define CAN_MODE_LOOPBACK 1
#define DISABLE 0
typedef struct { unsigned StdId,IDE,RTR,DLC,TransmitGlobalTime; } CAN_TxHeaderTypeDef;
typedef CAN_TxHeaderTypeDef CAN_RxHeaderTypeDef;
static struct {struct {int Mode;} Init;} hcan1;
static unsigned tick, available, updates, resets;
static CAN_RxHeaderTypeDef rx;
static unsigned char payload[8], response[8];
static vcu_driver_inputs_t input;
unsigned HAL_GetTick(void) {return tick;}
unsigned HAL_CAN_GetRxFifoFillLevel(void *h,unsigned f) {(void)h;(void)f;return available;}
int HAL_CAN_GetRxMessage(void *h,unsigned f,CAN_RxHeaderTypeDef *r,unsigned char *d) {
    (void)h;(void)f;*r=rx;memcpy(d,payload,8);available=0;return HAL_OK;
}
unsigned HAL_CAN_GetTxMailboxesFreeLevel(void *h) {(void)h;return 3;}
int HAL_CAN_AddTxMessage(void *h,CAN_TxHeaderTypeDef *r,const unsigned char *d,unsigned *m) {
    (void)h;(void)m;if(r->StdId==0x201) memcpy(response,d,8);return HAL_OK;
}
void vcu_driver_input_update(const vcu_driver_inputs_t *d,uint8_t mask) {assert(mask==15);input=*d;updates++;}
void vcu_driver_input_reset(void) {memset(&input,0,sizeof(input));resets++;}
#include "../firmware/vcu_ECU/Core/Src/vcu_can.c"
static void packet(unsigned seq,int run) {
    rx=(CAN_RxHeaderTypeDef){.StdId=0x200,.DLC=8};
    unsigned char d[8]={1,seq&255,seq>>8,run?2:0,run?10:0,run?0:1,run?2:0,0};
    d[7]=pc_crc(d);memcpy(payload,d,8);available=1;
}
int main(void) {
    packet(1,1);vcu_pc_can_poll();assert(updates==0 && response[3]==2);
    packet(1,0);vcu_pc_can_poll();assert(updates==1 && response[3]==0);
    packet(2,1);vcu_pc_can_poll();assert(updates==2 && input.accelerator_percent==10);
    packet(2,1);vcu_pc_can_poll();assert(updates==2 && response[3]==2);
    packet(1,1);vcu_pc_can_poll();assert(updates==2);
    packet(3,1);payload[7]^=1;vcu_pc_can_poll();assert(updates==2);
    packet(3,1);payload[4]=21;payload[7]=pc_crc(payload);vcu_pc_can_poll();assert(updates==2);
    packet(3,1);rx.IDE=4;vcu_pc_can_poll();assert(updates==2);
    packet(3,1);rx.RTR=2;vcu_pc_can_poll();assert(updates==2);
    packet(3,1);rx.DLC=7;vcu_pc_can_poll();assert(updates==2);
    tick=299;vcu_pc_can_poll();assert(resets==0);
    tick=300;vcu_pc_can_poll();assert(resets==1 && input.accelerator_percent==0);
    packet(3,1);vcu_pc_can_poll();assert(updates==2 && response[3]==2);
    packet(65535,0);vcu_pc_can_poll();assert(updates==3);
    packet(0,1);vcu_pc_can_poll();assert(updates==4 && response[3]==0);
    assert(response[7]==pc_crc(response));
    puts("PC CAN firmware: validation, replay, timeout, safe handshake, wrap PASS");
}
