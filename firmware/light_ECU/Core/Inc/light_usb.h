#ifndef LIGHT_USB_H
#define LIGHT_USB_H
#include <stdio.h>
#include "light_usb_protocol.h"
static UART_HandleTypeDef light_usb_uart;
static char usb_line[4], usb_tx[80];
static unsigned usb_used, usb_drop, usb_tx_pos, usb_tx_len;
static uint32_t usb_last_byte, usb_last_status, usb_errors;
static void Light_USBInit(void) {
  __HAL_RCC_USART2_CLK_ENABLE();
  light_usb_uart.Instance=USART2;
  light_usb_uart.Init.BaudRate=115200;
  light_usb_uart.Init.WordLength=UART_WORDLENGTH_8B;
  light_usb_uart.Init.StopBits=UART_STOPBITS_1;
  light_usb_uart.Init.Parity=UART_PARITY_NONE;
  light_usb_uart.Init.Mode=UART_MODE_TX_RX;
  light_usb_uart.Init.HwFlowCtl=UART_HWCONTROL_NONE;
  light_usb_uart.Init.OverSampling=UART_OVERSAMPLING_16;
  if(HAL_UART_Init(&light_usb_uart)!=HAL_OK) Error_Handler();
}
static void Light_USBPoll(void) {
  uint32_t now=HAL_GetTick(), sr=USART2->SR;
  if((usb_used || usb_drop) && (uint32_t)(now-usb_last_byte)>=100u) {
    usb_used=0; usb_drop=0;
  }
  if(sr & (USART_SR_ORE|USART_SR_NE|USART_SR_FE|USART_SR_PE)) {
    (void)USART2->DR; usb_used=0; usb_drop=1; usb_last_byte=now; ++usb_errors;
  } else if(sr & USART_SR_RXNE) {
    char ch=(char)USART2->DR; usb_last_byte=now;
    if(ch=='\n') {
      uint8_t value;
      if(!usb_drop && Light_USBDecode(usb_line,usb_used,&value)) Light_Command(&light,value,now);
      else ++usb_errors;
      usb_used=0; usb_drop=0;
    } else if(ch!='\r') {
      if(usb_used<sizeof usb_line && !usb_drop) usb_line[usb_used++]=ch;
      else usb_drop=1;
    }
  }
  if(usb_tx_pos==usb_tx_len && (uint32_t)(now-usb_last_status)>=100u) {
    usb_last_status=now;
    int n=snprintf(usb_tx,sizeof usb_tx,"LIGHT1 cmd=%02X lamps=%02X out=%02X diag=%u alive=%u err=%lu\n",
      light.command,Light_Lamps(&light,now),Light_Outputs(&light,now),Light_Diagnostic(&light,now),
      light.alive,(unsigned long)usb_errors);
    if(n>0 && (unsigned)n<sizeof usb_tx) { usb_tx_pos=0; usb_tx_len=(unsigned)n; }
    light.alive=(light.alive+1u)&15u;
  }
  if(usb_tx_pos<usb_tx_len && (USART2->SR & USART_SR_TXE)) USART2->DR=(uint8_t)usb_tx[usb_tx_pos++];
}
#endif
