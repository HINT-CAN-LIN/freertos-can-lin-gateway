#include "cluster_can.h"
#include "cluster_ui.h"
#include "can.h"
#include "cmsis_os.h"

#define RX_QUEUE_LENGTH 64U
typedef struct {
  uint32_t id, received_ms;
  uint8_t data[8], dlc;
  bool extended, remote;
} ClusterRxFrame;
static osMessageQueueId_t rx_queue;
volatile uint32_t cluster_can_rx_count, cluster_can_rx_drops, cluster_can_error;
volatile bool cluster_can_queue_test_passed;
volatile HAL_StatusTypeDef cluster_can_status;
static uint32_t reported_drops, reported_error;

HAL_StatusTypeDef cluster_can_init(bool live)
{
  if (rx_queue) return HAL_ERROR;
  rx_queue=osMessageQueueNew(RX_QUEUE_LENGTH,sizeof(ClusterRxFrame),NULL);
  if (!rx_queue) return HAL_ERROR;
  /* Verify the same queue's frame/timestamp copy before enabling interrupts. */
  ClusterRxFrame sent={.id=0x100,.received_ms=123,.data={0xD2,0x04,0xFA},.dlc=8}, got;
  cluster_can_queue_test_passed=osMessageQueuePut(rx_queue,&sent,0,0)==osOK &&
    osMessageQueueGet(rx_queue,&got,NULL,0)==osOK && got.id==sent.id &&
    got.received_ms==123 && got.dlc==8 && got.data[2]==0xFA && !got.extended && !got.remote;
  if (!cluster_can_queue_test_passed) return HAL_ERROR;
  if (!live) return HAL_OK;
  /* 16-bit list encoding: STDID<<5, RTR bit4=0, IDE bit3=0.
   * Two banks cover six exact standard data IDs; repeat unused list entries. */
  static const uint16_t ids[2][4]={{0x100,0x110,0x120,0x200},{0x300,0x310,0x300,0x310}};
  for (uint32_t bank=0;bank<2;bank++) {
    CAN_FilterTypeDef f={0};
    f.FilterBank=bank; f.FilterMode=CAN_FILTERMODE_IDLIST;
    f.FilterScale=CAN_FILTERSCALE_16BIT; f.FilterFIFOAssignment=CAN_FILTER_FIFO0;
    f.FilterActivation=ENABLE; f.SlaveStartFilterBank=14;
    f.FilterIdHigh=ids[bank][0]<<5; f.FilterIdLow=ids[bank][1]<<5;
    f.FilterMaskIdHigh=ids[bank][2]<<5; f.FilterMaskIdLow=ids[bank][3]<<5;
    if (HAL_CAN_ConfigFilter(&hcan1,&f)!=HAL_OK) return HAL_ERROR;
  }
  /* Arm notifications before Start so the first event cannot be stranded. */
  if (HAL_CAN_ActivateNotification(&hcan1,CAN_IT_RX_FIFO0_MSG_PENDING |
      CAN_IT_RX_FIFO0_OVERRUN | CAN_IT_BUSOFF | CAN_IT_ERROR)!=HAL_OK) return HAL_ERROR;
  return HAL_CAN_Start(&hcan1);
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
  if (hcan!=&hcan1 || !rx_queue) return;
  while (HAL_CAN_GetRxFifoFillLevel(hcan,CAN_RX_FIFO0)) {
    CAN_RxHeaderTypeDef header; ClusterRxFrame frame={0};
    if (HAL_CAN_GetRxMessage(hcan,CAN_RX_FIFO0,&header,frame.data)!=HAL_OK) {
      cluster_can_rx_drops++; break;
    }
    frame.extended=header.IDE==CAN_ID_EXT; frame.remote=header.RTR==CAN_RTR_REMOTE;
    frame.id=frame.extended?header.ExtId:header.StdId;
    frame.dlc=header.DLC; frame.received_ms=HAL_GetTick();
    cluster_can_rx_count++;
    if (osMessageQueuePut(rx_queue,&frame,0,0)!=osOK) cluster_can_rx_drops++;
  }
}
void HAL_CAN_ErrorCallback(CAN_HandleTypeDef *hcan)
{
  if (hcan!=&hcan1) return;
  cluster_can_error=HAL_CAN_GetError(hcan);
  if (cluster_can_error & HAL_CAN_ERROR_RX_FOV0) cluster_can_rx_drops++;
}
void cluster_can_process(void)
{
  if (!rx_queue) return;
  if (cluster_can_rx_drops!=reported_drops || cluster_can_error!=reported_error) {
    cluster_ui_mark_rx_gap(); reported_drops=cluster_can_rx_drops;
    reported_error=cluster_can_error;
  }
  ClusterRxFrame frame;
  /* Bounded drain prevents an overloaded bus from starving LVGL/other tasks. */
  for (uint32_t n=0;n<RX_QUEUE_LENGTH;n++) {
    if (osMessageQueueGet(rx_queue,&frame,NULL,0)!=osOK) break;
    cluster_ui_receive_frame(frame.id,frame.data,frame.dlc,frame.extended,frame.remote,frame.received_ms);
  }
}
