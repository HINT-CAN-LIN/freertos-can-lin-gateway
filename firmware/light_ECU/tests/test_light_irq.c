#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#define LIGHT_BOARD_H
static uint8_t output;
static void Light_BoardInit(void) {}
static void Light_BoardWrite(uint8_t v) { output=v; }
typedef struct { uint32_t SR,DR,CR1,CR2,CR3; } Registers;
static Registers regs;
#define USART1 (&regs)
#define USART_SR_PE (1u<<0)
#define USART_SR_FE (1u<<1)
#define USART_SR_NE (1u<<2)
#define USART_SR_ORE (1u<<3)
#define USART_SR_RXNE (1u<<5)
#define USART_SR_TC (1u<<6)
#define USART_SR_TXE (1u<<7)
#define USART_SR_LBD (1u<<8)
#define USART_CR1_RXNEIE (1u<<5)
#define USART_CR1_TCIE (1u<<6)
#define USART_CR1_TXEIE (1u<<7)
#define USART_CR2_LBDIE (1u<<6)
#define USART_CR3_EIE 1u
#define UART_FLAG_LBD USART_SR_LBD
#define __HAL_UART_CLEAR_FLAG(h,f) (regs.SR &= ~(f))
static uint32_t tick;
static uint32_t HAL_GetTick(void) { return tick; }
static uint32_t __get_PRIMASK(void) { return 0; }
static void __disable_irq(void) {}
static void __set_PRIMASK(uint32_t v) { (void)v; }
#include "light_app.h"
static void event(uint32_t flags, uint8_t byte) {
  regs.SR=flags; regs.DR=byte; Light_UART_IRQHandler();
}
static void header(uint8_t pid) {
  event(USART_SR_LBD,0); event(USART_SR_RXNE,0x55); event(USART_SR_RXNE,pid);
}
static void command(uint8_t data, uint8_t check) {
  header(0x92); event(USART_SR_RXNE,data); event(USART_SR_RXNE,check);
}
int main(void) {
  Light_AppInit(); Light_AppPoll(); assert(output==0);
  command(0x31,0x3c); Light_AppPoll(); assert(output==0x31);
  tick=10; command(0,0); assert(light.response_error && light.last_command==0);
  header(0x93); assert(light_rx==LIGHT_IDLE);
  header(0xd3); assert(light_rx==LIGHT_TX);
  uint8_t expected[3]={0x31,0x40,0xba};
  for (unsigned i=0;i<3;i++) {
    event(USART_SR_TXE,0); assert(regs.DR==expected[i]);
    event(USART_SR_RXNE,expected[i]);
  }
  event(USART_SR_TC,0); assert(light.alive==1 && !light.response_error);
  header(0xd3); event(USART_SR_TXE,0); event(USART_SR_RXNE,0xff);
  assert(light_rx==LIGHT_IDLE && light.response_error);
  header(0x92); tick+=10; Light_AppPoll(); assert(light_rx==LIGHT_IDLE);
  command(1,0x6c); Light_AppPoll(); assert(output==1);
  tick+=250; Light_AppPoll(); assert(output==0);
  header(0x92); event(USART_SR_ORE,0); assert(light_rx==LIGHT_IDLE);
  command(0,0x6d); assert(light.command==0 && !light.invalid);
  puts("PASS: IRQ frame parser, bad PID/checksum, TX echo/collision, partial timeout, recovery");
}
