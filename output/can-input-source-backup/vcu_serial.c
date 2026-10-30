#include "vcu_serial.h"
#include "vcu_app.h"
#include "vcu_serial_protocol.h"
#include "vcu_uart.h"
#include "FreeRTOS.h"
#include "task.h"
#include <string.h>

volatile vcu_serial_stats_t vcu_serial_stats;

static uint8_t rx_frame[VCU_SERIAL_INPUT_FRAME_SIZE];
static uint32_t rx_frame_length;
static TickType_t last_valid_input_tick;
static bool input_link_active;

void vcu_serial_start(void)
{
    memset((void *)&vcu_serial_stats, 0, sizeof(vcu_serial_stats));
    memset(rx_frame, 0, sizeof(rx_frame));
    rx_frame_length = 0U;
    last_valid_input_tick = 0U;
    input_link_active = false;
    vcu_uart2_start_rx();
}

static vcu_serial_status_t process_frame(void)
{
    vcu_serial_input_frame_t input;
    vcu_serial_status_t status = vcu_serial_decode_input(
        rx_frame, sizeof(rx_frame), &input);
    /* CAN-only control: never let another transport overwrite drive inputs. */
    if (status == VCU_SERIAL_STATUS_ACCEPTED) status = VCU_SERIAL_STATUS_BAD_TYPE;
    const uint16_t sequence = (uint16_t)rx_frame[4] |
                              ((uint16_t)rx_frame[5] << 8U);
    uint8_t ack[VCU_SERIAL_ACK_FRAME_SIZE];

    if (status == VCU_SERIAL_STATUS_ACCEPTED) {
        vcu_driver_input_update(&input.inputs, input.valid_mask);
        last_valid_input_tick = xTaskGetTickCount();
        input_link_active = true;
        ++vcu_serial_stats.accepted_frames;
    } else {
        ++vcu_serial_stats.rejected_frames;
    }

    vcu_serial_encode_ack(sequence, status, ack);
    if (!vcu_uart2_write(ack, sizeof(ack))) {
        ++vcu_serial_stats.ack_tx_errors;
    }
    return status;
}

static bool is_frame_header_valid(void)
{
    return rx_frame[0] == VCU_SERIAL_SYNC_0 &&
           rx_frame[1] == VCU_SERIAL_SYNC_1;
}

static void parser_resync(void)
{
    const uint32_t last = VCU_SERIAL_INPUT_FRAME_SIZE - 1U;
    if (rx_frame[last - 1U] == VCU_SERIAL_SYNC_0 &&
        rx_frame[last] == VCU_SERIAL_SYNC_1) {
        rx_frame[0] = VCU_SERIAL_SYNC_0;
        rx_frame[1] = VCU_SERIAL_SYNC_1;
        rx_frame_length = 2U;
    } else if (rx_frame[VCU_SERIAL_INPUT_FRAME_SIZE - 1U] ==
               VCU_SERIAL_SYNC_0) {
        rx_frame[0] = VCU_SERIAL_SYNC_0;
        rx_frame_length = 1U;
    } else {
        rx_frame_length = 0U;
    }
    ++vcu_serial_stats.parser_resyncs;
}

static void parser_feed(uint8_t byte)
{
    if (rx_frame_length == 0U) {
        if (byte == VCU_SERIAL_SYNC_0) {
            rx_frame[0] = byte;
            rx_frame_length = 1U;
        }
        return;
    }

    if (rx_frame_length == 1U) {
        if (byte == VCU_SERIAL_SYNC_1) {
            rx_frame[1] = byte;
            rx_frame_length = 2U;
        } else {
            rx_frame_length = (byte == VCU_SERIAL_SYNC_0) ? 1U : 0U;
            if (rx_frame_length == 1U) {
                rx_frame[0] = byte;
            }
        }
        return;
    }

    rx_frame[rx_frame_length++] = byte;
    if (rx_frame_length == VCU_SERIAL_INPUT_FRAME_SIZE) {
        if (!is_frame_header_valid()) {
            parser_resync();
            return;
        }
        if (process_frame() == VCU_SERIAL_STATUS_BAD_CRC) {
            parser_resync();
        } else {
            rx_frame_length = 0U;
        }
    }
}

void vcu_serial_task_run(void)
{
    const TickType_t timeout = pdMS_TO_TICKS(VCU_SERIAL_INPUT_TIMEOUT_MS);
    configASSERT(timeout > 0U);

    for (;;) {
        uint8_t byte;
        while (vcu_uart2_read_byte(&byte)) {
            parser_feed(byte);
        }

        if (input_link_active &&
            (TickType_t)(xTaskGetTickCount() - last_valid_input_tick) >= timeout) {
            vcu_driver_input_reset();
            input_link_active = false;
            ++vcu_serial_stats.input_timeouts;
        }

        vTaskDelay(1U);
    }
}
