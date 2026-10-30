#include "cluster_can.h"
#include "cluster_ui.h"
#include "can.h"
#include "cmsis_os.h"
#include "cluster_state.h"

#define RX_QUEUE_LENGTH 64U
typedef struct {
  uint32_t id, received_ms;
  uint8_t data[8], dlc;
  bool extended, remote;
} ClusterRxFrame;
static osMessageQueueId_t rx_queue;
volatile uint32_t cluster_can_rx_count, cluster_can_rx_drops, cluster_can_error;
volatile bool cluster_can_queue_test_passed;
volatile uint32_t cluster_can_current_errors, cluster_can_rx_queue_max;
static bool initialized, live_mode;
volatile HAL_StatusTypeDef cluster_can_status;
static uint32_t reported_drops, reported_error;

static HAL_StatusTypeDef initialize_can(bool live)
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
  /* Never send synthetic frames with an accidentally regenerated Normal IOC. */
  if (CLUSTER_CAN_LOOPBACK && hcan1.Init.Mode!=CAN_MODE_SILENT_LOOPBACK) return HAL_ERROR;
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

HAL_StatusTypeDef cluster_can_init(bool live)
{
  live_mode=live;
  cluster_can_status=initialize_can(live);
  initialized=true;
  return cluster_can_status;
}

void cluster_can_get_diagnostics(ClusterCanDiagnostics *out)
{
  if (out==NULL) return;
  taskENTER_CRITICAL();
  out->initialized=initialized; out->live=live_mode;
  out->init_status=cluster_can_status;
  uint32_t esr=initialized && live_mode && cluster_can_status==HAL_OK ? hcan1.Instance->ESR : 0;
  cluster_can_current_errors=((esr & CAN_ESR_BOFF) ? HAL_CAN_ERROR_BOF : 0) |
    ((esr & CAN_ESR_EPVF) ? HAL_CAN_ERROR_EPV : 0) |
    ((esr & CAN_ESR_EWGF) ? HAL_CAN_ERROR_EWG : 0);
  out->current_errors=cluster_can_current_errors;
  out->error_history=cluster_can_error; out->rx_drops=cluster_can_rx_drops;
  out->queue_count=rx_queue ? osMessageQueueGetCount(rx_queue) : 0;
  out->queue_max=cluster_can_rx_queue_max;
  taskEXIT_CRITICAL();
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
    uint32_t count=osMessageQueueGetCount(rx_queue);
    if (count>cluster_can_rx_queue_max) cluster_can_rx_queue_max=count;
  }
}
void HAL_CAN_ErrorCallback(CAN_HandleTypeDef *hcan)
{
  if (hcan!=&hcan1) return;
  uint32_t error=HAL_CAN_GetError(hcan);
  cluster_can_error |= error;
  if (error & HAL_CAN_ERROR_RX_FOV0) cluster_can_rx_drops++;
  /* Keep history above, then clear the HAL latch so an old FIFO overrun is
   * not counted again by a later, unrelated error callback. */
  HAL_CAN_ResetError(hcan);
}
#if CLUSTER_CAN_LOOPBACK
volatile uint32_t cluster_can_tx_count, cluster_can_tx_errors;
static ClusterState loopback_source;
static uint32_t loopback_start, loopback_last;
static bool loopback_started;
static bool loopback_emit(uint32_t id, const uint8_t *data)
{
  uint32_t begin=HAL_GetTick(), mailbox;
  while (!HAL_CAN_GetTxMailboxesFreeLevel(&hcan1)) {
    if (HAL_GetTick()-begin>=20U) {
      cluster_can_tx_errors++; cluster_ui_mark_rx_gap(); return false;
    }
    osDelay(1);
  }
  CAN_TxHeaderTypeDef h={0};
  h.StdId=id; h.IDE=CAN_ID_STD; h.RTR=CAN_RTR_DATA; h.DLC=8;
  if (HAL_CAN_AddTxMessage(&hcan1,&h,(uint8_t *)data,&mailbox)!=HAL_OK) {
    cluster_can_tx_errors++; cluster_ui_mark_rx_gap(); return false;
  }
  cluster_can_tx_count++;
  return true;
}
#endif
void cluster_can_process(void)
{
  if (!rx_queue) return;
#if CLUSTER_CAN_LOOPBACK
  if (live_mode && cluster_can_status==HAL_OK) {
    uint32_t now=HAL_GetTick();
    if (!loopback_started) { loopback_start=now; loopback_started=true; }
    if (now-loopback_last>=100U) {
      loopback_last=now;
      /* 100 ms demo cadence, not the production DBC transmission schedule. */
      cluster_demo_generate(&loopback_source,now,now-loopback_start,loopback_emit);
    }
  }
#endif
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
