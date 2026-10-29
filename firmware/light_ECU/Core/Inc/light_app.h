#ifndef LIGHT_APP_H
#define LIGHT_APP_H
#include "light_protocol.h"
#include "light_config.h"
#include "light_board.h"
/* Sole owner of USART1 interrupts. Do not mix HAL UART receive/transmit APIs.
 * ISR and poll serialize state; no blocking delays or allocation. */
static LightState light;
static enum { LIGHT_IDLE, LIGHT_SYNC, LIGHT_PID_STATE, LIGHT_DATA, LIGHT_CHECK,
              LIGHT_TX } light_rx;
static uint8_t light_data, light_tx[3], light_sent, light_echo;
static uint32_t light_frame_start;
static void Light_StopTx(void) {
  USART1->CR1 &= ~(USART_CR1_TXEIE | USART_CR1_TCIE);
}
static void Light_Abort(void) {
  if (light_rx == LIGHT_DATA || light_rx == LIGHT_CHECK || light_rx == LIGHT_TX)
    light.response_error = 1;
  Light_StopTx(); light_rx = LIGHT_IDLE;
}
static void Light_AppInit(void) {
  Light_BoardInit();
  /* PA5 is initialized by BSP immediately afterwards; output defaults OFF. */
  (void)USART1->SR; (void)USART1->DR;
  __HAL_UART_CLEAR_FLAG(&huart1, UART_FLAG_LBD);
#if !LIGHT_USB_BENCH
  USART1->CR2 |= USART_CR2_LBDIE;
  USART1->CR3 |= USART_CR3_EIE;
  USART1->CR1 |= USART_CR1_RXNEIE;
#endif
}
void Light_UART_IRQHandler(void) {
  uint32_t sr = USART1->SR;
  uint32_t now = HAL_GetTick();
  if (sr & USART_SR_LBD) {
    (void)USART1->DR;
    __HAL_UART_CLEAR_FLAG(&huart1, UART_FLAG_LBD);
    Light_Abort(); light_rx = LIGHT_SYNC; light_frame_start = now;
    return;
  }
  if (sr & (USART_SR_ORE | USART_SR_NE | USART_SR_FE | USART_SR_PE)) {
    (void)USART1->DR; Light_Abort(); return;
  }
  if (light_rx != LIGHT_IDLE && (uint32_t)(now-light_frame_start) >= LIGHT_FRAME_TIMEOUT_MS)
    Light_Abort();
  if (sr & USART_SR_RXNE) {
    uint8_t byte = (uint8_t)USART1->DR;
    switch (light_rx) {
    case LIGHT_SYNC: light_rx = byte == 0x55u ? LIGHT_PID_STATE : LIGHT_IDLE; break;
    case LIGHT_PID_STATE:
      if (byte != Light_PID(byte & 0x3fu)) { light_rx = LIGHT_IDLE; break; }
      if (byte == Light_PID(LIGHT_COMMAND_ID)) light_rx = LIGHT_DATA;
      else if (byte == Light_PID(LIGHT_STATUS_ID)) {
        Light_Status(&light, now, light_tx);
        light_tx[2] = Light_Checksum(byte, light_tx, 2);
        light_sent = 0; light_echo = 0; light_rx = LIGHT_TX;
        USART1->CR1 |= USART_CR1_TXEIE;
      } else light_rx = LIGHT_IDLE;
      break;
    case LIGHT_DATA: light_data = byte; light_rx = LIGHT_CHECK; break;
    case LIGHT_CHECK:
      if (byte == Light_Checksum(Light_PID(LIGHT_COMMAND_ID), &light_data, 1))
        Light_Command(&light, light_data, now);
      else light.response_error = 1;
      light_rx = LIGHT_IDLE; break;
    case LIGHT_TX:
      if (light_echo >= light_sent || byte != light_tx[light_echo]) Light_Abort();
      else ++light_echo;
      break;
    default: break;
    }
  }
  if ((USART1->CR1 & USART_CR1_TXEIE) && (USART1->SR & USART_SR_TXE)) {
    USART1->DR = light_tx[light_sent++];
    if (light_sent == 3u) {
      USART1->CR1 &= ~USART_CR1_TXEIE;
      USART1->CR1 |= USART_CR1_TCIE;
    }
    return; /* never use a stale TC flag after writing DR */
  }
  if ((USART1->CR1 & USART_CR1_TCIE) && (USART1->SR & USART_SR_TC)) {
    Light_StopTx();
    /* A LIN transceiver must echo the transmitted response on RXD. */
    if (light_echo == 3u) {
      light.alive = (light.alive + 1u) & 15u;
      light.response_error = 0;
    } else light.response_error = 1;
    light_rx = LIGHT_IDLE;
  }
}
static void Light_AppPoll(void) {
  uint32_t mask = __get_PRIMASK(); __disable_irq();
  uint32_t now = HAL_GetTick();
  if (light_rx != LIGHT_IDLE && (uint32_t)(now-light_frame_start) >= LIGHT_FRAME_TIMEOUT_MS)
    Light_Abort();
  Light_BoardWrite(Light_Outputs(&light, now));
  __set_PRIMASK(mask);
}
#endif
