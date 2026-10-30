#ifndef VCU_UART_H
#define VCU_UART_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define VCU_UART2_BAUDRATE          115200U
#define VCU_UART2_RX_RING_SIZE      128U
#define VCU_UART2_TX_TIMEOUT_MS     20U

void MX_USART2_UART_Init(void);
void vcu_uart2_start_rx(void);
void vcu_uart2_irq_handler(void);
bool vcu_uart2_read_byte(uint8_t *byte);
bool vcu_uart2_write(const uint8_t *data, size_t length);
uint32_t vcu_uart2_rx_overrun_count(void);
uint32_t vcu_uart2_error_count(void);

#endif
