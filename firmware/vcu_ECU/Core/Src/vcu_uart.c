#include "vcu_uart.h"
#include "main.h"
#include "FreeRTOS.h"
#include "task.h"

_Static_assert((VCU_UART2_RX_RING_SIZE & (VCU_UART2_RX_RING_SIZE - 1U)) == 0U,
               "UART RX ring size must be a power of two");

static uint8_t rx_ring[VCU_UART2_RX_RING_SIZE];
static volatile uint16_t rx_head;
static volatile uint16_t rx_tail;
static volatile uint32_t rx_overruns;
static volatile uint32_t uart_errors;

void vcu_uart2_start_rx(void)
{
    /* Called once before the scheduler, before RXNE interrupts are enabled. */
    rx_head = 0U;
    rx_tail = 0U;
    rx_overruns = 0U;
    uart_errors = 0U;

    /* Clear any stale RX/error flags using the STM32F4 SR-then-DR sequence. */
    const volatile uint32_t status = USART2->SR;
    const volatile uint32_t data = USART2->DR;
    (void)status;
    (void)data;
    USART2->CR1 |= USART_CR1_RXNEIE;
    HAL_NVIC_EnableIRQ(USART2_IRQn);
}

void vcu_uart2_irq_handler(void)
{
    const uint32_t status = USART2->SR;
    const uint32_t error_mask = USART_SR_ORE | USART_SR_NE |
                                USART_SR_FE | USART_SR_PE;

    if ((status & error_mask) != 0U) {
        ++uart_errors;
    }

    if ((status & USART_SR_RXNE) != 0U) {
        const uint8_t byte = (uint8_t)USART2->DR;
        const uint16_t next = (uint16_t)((rx_head + 1U) &
                                         (VCU_UART2_RX_RING_SIZE - 1U));
        if (next == rx_tail) {
            ++rx_overruns;
        } else {
            rx_ring[rx_head] = byte;
            rx_head = next;
        }
    } else if ((status & error_mask) != 0U) {
        (void)USART2->DR;
    }
}

bool vcu_uart2_read_byte(uint8_t *byte)
{
    bool available = false;
    if (byte == NULL) {
        return false;
    }

    taskENTER_CRITICAL();
    if (rx_tail != rx_head) {
        *byte = rx_ring[rx_tail];
        rx_tail = (uint16_t)((rx_tail + 1U) &
                             (VCU_UART2_RX_RING_SIZE - 1U));
        available = true;
    }
    taskEXIT_CRITICAL();
    return available;
}

bool vcu_uart2_write(const uint8_t *data, size_t length)
{
    if (data == NULL && length != 0U) {
        return false;
    }

    const uint32_t start_tick = HAL_GetTick();
    for (size_t i = 0; i < length; ++i) {
        while ((USART2->SR & USART_SR_TXE) == 0U) {
            if ((uint32_t)(HAL_GetTick() - start_tick) >=
                VCU_UART2_TX_TIMEOUT_MS) {
                return false;
            }
        }
        USART2->DR = data[i];
    }

    while ((USART2->SR & USART_SR_TC) == 0U) {
        if ((uint32_t)(HAL_GetTick() - start_tick) >=
            VCU_UART2_TX_TIMEOUT_MS) {
            return false;
        }
    }
    return true;
}

uint32_t vcu_uart2_rx_overrun_count(void)
{
    uint32_t count;
    taskENTER_CRITICAL();
    count = rx_overruns;
    taskEXIT_CRITICAL();
    return count;
}

uint32_t vcu_uart2_error_count(void)
{
    uint32_t count;
    taskENTER_CRITICAL();
    count = uart_errors;
    taskEXIT_CRITICAL();
    return count;
}
