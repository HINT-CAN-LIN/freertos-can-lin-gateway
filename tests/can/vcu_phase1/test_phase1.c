#include <assert.h>
#include <math.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "vcu_can.h"
#include "vcu_serial_protocol.h"
#include "vcu_task.h"
#include "task.h"

CAN_HandleTypeDef hcan1;
static uint32_t free_mailboxes = 3, rx_fill, sends, releases, stop_after;
static uint32_t fail_on = UINT32_MAX, overrun_on = UINT32_MAX;
static uint8_t expected_alive;
static uint8_t expected_body_requests;
static TickType_t tick;
static jmp_buf done;

uint32_t HAL_CAN_GetRxFifoFillLevel(CAN_HandleTypeDef *h, uint32_t fifo)
{
    assert(h == &hcan1 && fifo == CAN_RX_FIFO0);
    return rx_fill;
}
HAL_StatusTypeDef HAL_CAN_GetRxMessage(CAN_HandleTypeDef *h, uint32_t fifo,
                                     CAN_RxHeaderTypeDef *header, uint8_t *data)
{
    (void)header; (void)data;
    assert(h == &hcan1 && fifo == CAN_RX_FIFO0 && rx_fill > 0);
    --rx_fill;
    return HAL_OK;
}
uint32_t HAL_CAN_GetTxMailboxesFreeLevel(CAN_HandleTypeDef *h)
{
    assert(h == &hcan1);
    return free_mailboxes;
}
HAL_StatusTypeDef HAL_CAN_AddTxMessage(CAN_HandleTypeDef *h,
                                     const CAN_TxHeaderTypeDef *header,
                                     const uint8_t *data, uint32_t *mailbox)
{
    assert(h == &hcan1 && header->StdId == 0x100 && header->DLC == 8);
    assert(header->IDE == CAN_ID_STD && header->RTR == CAN_RTR_DATA);
    assert(header->TransmitGlobalTime == DISABLE);
    assert(data[0] == 0 && data[1] == 0 && data[2] == expected_alive * 16U);
    assert(data[3] == expected_body_requests);
    for (unsigned i = 4; i < 8; ++i) assert(data[i] == 0);
    *mailbox = 0;
    if (releases == overrun_on) tick += 12;
    ++sends;
    if (releases == fail_on) return HAL_ERROR;
    expected_alive = (uint8_t)((expected_alive + 1) % 16);
    return HAL_OK;
}
TickType_t xTaskGetTickCount(void) { return tick; }
void vTaskDelayUntil(TickType_t *last, TickType_t period)
{
    assert(period == 10);
    assert((TickType_t)(tick - *last) < period);
    *last += period;
    tick = *last;
    if (++releases == stop_after) longjmp(done, 1);
}

static void test_codec(void)
{
    uint8_t data[8];
    vcu_app_command_t c = {
        .torque_request_nm = 123.4f,
        .gear = VCU_GEAR_R,
        .brake = true,
        .door_lock_request = VCU_DOOR_NO_ACTION,
        .window_command = VCU_WINDOW_STOP
    };
    assert(vcu_command_encode(&c, 15, data));
    const uint8_t expected[8] = {0xD2, 0x04, 0xFB, 0, 0, 0, 0, 0};
    assert(memcmp(data, expected, 8) == 0);
    c.door_lock_request = VCU_DOOR_UNLOCK;
    c.window_command = VCU_WINDOW_DOWN;
    assert(vcu_command_encode(&c, 15, data) && data[3] == 0xA0);
    for (unsigned request = 0; request <= 2; ++request) {
        c.door_lock_request = (vcu_door_lock_request_t)request;
        c.window_command = (vcu_window_command_t)request;
        assert(vcu_command_encode(&c, 0, data));
        assert(data[3] == (uint8_t)((request << 4U) | (request << 6U)));
    }
    c.door_lock_request = VCU_DOOR_INVALID;
    assert(!vcu_command_encode(&c, 0, data));
    c.door_lock_request = VCU_DOOR_NO_ACTION;
    c.window_command = VCU_WINDOW_INVALID;
    assert(!vcu_command_encode(&c, 0, data));
    c.window_command = VCU_WINDOW_STOP;
    for (int gear = 0; gear < 8; ++gear) {
        c.gear = (vcu_gear_t)gear;
        assert(vcu_command_encode(&c, 0, data) == (gear < 4));
    }
    c.gear = (vcu_gear_t)-1;
    assert(!vcu_command_encode(&c, 0, data));
    c.gear = VCU_GEAR_P;
    for (unsigned raw = 0; raw <= 40000; ++raw) {
        c.torque_request_nm = (float)raw / 10.0f;
        assert(vcu_command_encode(&c, 0, data));
        assert(data[0] == (raw & 0xFFU) && data[1] == (raw >> 8));
    }
    c.torque_request_nm = 4000;
    assert(vcu_command_encode(&c, 0, data));
    assert(data[0] == 0x40 && data[1] == 0x9C);
    float invalid[] = {-0.1f, 4000.1f, NAN, INFINITY};
    for (unsigned i = 0; i < sizeof(invalid)/sizeof(invalid[0]); ++i) {
        c.torque_request_nm = invalid[i];
        memset(data, 0xAA, 8);
        assert(!vcu_command_encode(&c, 0, data));
        for (unsigned j = 0; j < 8; ++j) assert(data[j] == 0xAA);
    }
    c.torque_request_nm = 0.1f;
    assert(vcu_command_encode(&c, 0, data) && data[0] == 1);
    assert(!vcu_command_encode(&c, 16, data));
    assert(!vcu_command_encode(NULL, 0, data));
    assert(!vcu_command_encode(&c, 0, NULL));
}

static void test_vcu_application_policy(void)
{
    vcu_driver_inputs_t inputs = {
        .ignition_state = VCU_IGNITION_RUN,
        .accelerator_percent = 50U,
        .brake = false,
        .gear = VCU_GEAR_D,
        .door_lock_request = VCU_DOOR_UNLOCK,
        .window_command = VCU_WINDOW_UP
    };
    vcu_vehicle_state_t state;
    vcu_app_command_t command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_DRIVE && command.gear == VCU_GEAR_D);
    assert(command.torque_request_nm == 2000.0f && !command.brake);
    assert(command.door_lock_request == VCU_DOOR_UNLOCK);
    assert(command.window_command == VCU_WINDOW_UP);

    inputs.door_lock_request = VCU_DOOR_INVALID;
    inputs.window_command = VCU_WINDOW_INVALID;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_DRIVE && command.torque_request_nm == 2000.0f);
    assert(command.door_lock_request == VCU_DOOR_NO_ACTION);
    assert(command.window_command == VCU_WINDOW_STOP);
    inputs.door_lock_request = VCU_DOOR_UNLOCK;
    inputs.window_command = VCU_WINDOW_UP;

    inputs.gear = VCU_GEAR_R;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_REVERSE && command.torque_request_nm == 2000.0f);

    inputs.brake = true;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_BRAKING && command.torque_request_nm == 0.0f);

    inputs.brake = false;
    inputs.gear = VCU_GEAR_P;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_PARKED && command.torque_request_nm == 0.0f);

    inputs.gear = VCU_GEAR_N;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_NEUTRAL && command.torque_request_nm == 0.0f);

    inputs.ignition_state = VCU_IGNITION_OFF;
    inputs.gear = VCU_GEAR_D;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_OFF && command.torque_request_nm == 0.0f);

    inputs.ignition_state = VCU_IGNITION_ON;
    inputs.accelerator_percent = 50U;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_IGNITION_ON && command.torque_request_nm == 0.0f);

    inputs.ignition_state = VCU_IGNITION_RUN;
    inputs.accelerator_percent = 101U;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_INPUT_FAULT && command.gear == VCU_GEAR_P);
    assert(command.torque_request_nm == 0.0f);

    inputs.accelerator_percent = 0U;
    inputs.gear = (vcu_gear_t)7;
    command = vcu_app_process_inputs(&inputs, &state);
    assert(state == VCU_STATE_INPUT_FAULT && command.gear == VCU_GEAR_P);
    assert(command.torque_request_nm == 0.0f);

    command = vcu_app_process_inputs(NULL, &state);
    assert(state == VCU_STATE_INPUT_FAULT && command.gear == VCU_GEAR_P);
    assert(command.torque_request_nm == 0.0f);

    command = vcu_app_get_command();
    assert(vcu_vehicle_state == VCU_STATE_OFF);
    assert(command.gear == VCU_GEAR_P && command.torque_request_nm == 0.0f);
    assert(command.door_lock_request == VCU_DOOR_NO_ACTION);
    assert(command.window_command == VCU_WINDOW_STOP);
}

static void test_serial_protocol(void)
{
    static const uint8_t crc_check[] = "123456789";
    assert(vcu_serial_crc8(crc_check, 9U) == 0xF4U);

    vcu_serial_input_frame_t sent = {
        .sequence = 0xA55AU,
        .valid_mask = VCU_SERIAL_INPUT_MASK,
        .inputs = {
            .ignition_state = VCU_IGNITION_RUN,
            .accelerator_percent = 73U,
            .brake = true,
            .gear = VCU_GEAR_R,
            .door_lock_request = VCU_DOOR_UNLOCK,
            .window_command = VCU_WINDOW_DOWN,
            .steering_direction = VCU_STEERING_RIGHT
        }
    };
    uint8_t frame[VCU_SERIAL_INPUT_FRAME_SIZE];
    vcu_serial_input_frame_t received;
    assert(vcu_serial_encode_input(&sent, frame));
    assert(frame[0] == VCU_SERIAL_SYNC_0 && frame[1] == VCU_SERIAL_SYNC_1);
    assert(frame[4] == 0x5AU && frame[5] == 0xA5U);
    assert(frame[13] == VCU_STEERING_RIGHT);
    assert(frame[14] == vcu_serial_crc8(&frame[2], 12U));
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_ACCEPTED);
    assert(received.sequence == sent.sequence && received.valid_mask == sent.valid_mask);
    assert(received.inputs.ignition_state == VCU_IGNITION_RUN &&
           received.inputs.accelerator_percent == 73U);
    assert(received.inputs.brake && received.inputs.gear == VCU_GEAR_R);
    assert(received.inputs.door_lock_request == VCU_DOOR_UNLOCK);
    assert(received.inputs.window_command == VCU_WINDOW_DOWN);
    assert(received.inputs.steering_direction == VCU_STEERING_RIGHT);

    uint8_t ack[VCU_SERIAL_ACK_FRAME_SIZE];
    vcu_serial_encode_ack(sent.sequence, VCU_SERIAL_STATUS_ACCEPTED, ack);
    assert(ack[0] == VCU_SERIAL_SYNC_0 && ack[1] == VCU_SERIAL_SYNC_1);
    assert(ack[3] == VCU_SERIAL_TYPE_ACK && ack[4] == 0x5AU && ack[5] == 0xA5U);
    assert(ack[6] == VCU_SERIAL_STATUS_ACCEPTED);
    assert(ack[7] == vcu_serial_crc8(&ack[2], 5U));

    assert(vcu_serial_decode_input(frame, sizeof(frame) - 1U, &received) ==
           VCU_SERIAL_STATUS_BAD_LENGTH);
    frame[14] ^= 0x01U;
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_BAD_CRC);
    frame[14] ^= 0x01U;

    frame[2] = (uint8_t)(VCU_SERIAL_PROTOCOL_VERSION + 1U);
    frame[14] = vcu_serial_crc8(&frame[2], 12U);
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_BAD_VERSION);
    frame[2] = VCU_SERIAL_PROTOCOL_VERSION;
    frame[3] = 0x7FU;
    frame[14] = vcu_serial_crc8(&frame[2], 12U);
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_BAD_TYPE);
    frame[3] = VCU_SERIAL_TYPE_DRIVER_INPUT;
    frame[6] = 0x80U;
    frame[14] = vcu_serial_crc8(&frame[2], 12U);
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_BAD_MASK);
    frame[6] = VCU_SERIAL_INPUT_ACCELERATOR;
    frame[8] = 101U;
    frame[14] = vcu_serial_crc8(&frame[2], 12U);
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_BAD_VALUE);

    frame[6] = VCU_SERIAL_INPUT_IGNITION;
    frame[7] = (uint8_t)VCU_IGNITION_INVALID;
    frame[14] = vcu_serial_crc8(&frame[2], 12U);
    assert(vcu_serial_decode_input(frame, sizeof(frame), &received) ==
           VCU_SERIAL_STATUS_BAD_VALUE);

    sent.valid_mask = 0U;
    assert(!vcu_serial_encode_input(&sent, frame));
    sent.valid_mask = VCU_SERIAL_INPUT_GEAR;
    sent.inputs.gear = (vcu_gear_t)7;
    assert(!vcu_serial_encode_input(&sent, frame));
    sent.valid_mask = VCU_SERIAL_INPUT_IGNITION;
    sent.inputs.ignition_state = VCU_IGNITION_INVALID;
    assert(!vcu_serial_encode_input(&sent, frame));
    sent.valid_mask = VCU_SERIAL_INPUT_STEERING;
    sent.inputs.steering_direction = VCU_STEERING_INVALID;
    assert(!vcu_serial_encode_input(&sent, frame));
}

static void test_driver_input_store(void)
{
    const vcu_driver_inputs_t update = {
        .ignition_state = VCU_IGNITION_RUN,
        .accelerator_percent = 67U,
        .brake = true,
        .gear = VCU_GEAR_D,
        .door_lock_request = VCU_DOOR_LOCK,
        .window_command = VCU_WINDOW_UP,
        .steering_direction = VCU_STEERING_LEFT
    };
    vcu_driver_input_reset();
    vcu_driver_input_update(&update,
        VCU_DRIVER_INPUT_IGNITION | VCU_DRIVER_INPUT_ACCELERATOR |
        VCU_DRIVER_INPUT_GEAR | VCU_DRIVER_INPUT_STEERING);
    vcu_driver_inputs_t current = vcu_driver_input_read();
    assert(current.ignition_state == VCU_IGNITION_RUN && current.accelerator_percent == 67U);
    assert(current.gear == VCU_GEAR_D && !current.brake);
    assert(current.door_lock_request == VCU_DOOR_NO_ACTION);
    assert(current.window_command == VCU_WINDOW_STOP);
    assert(current.steering_direction == VCU_STEERING_LEFT);

    vcu_driver_input_update(&update, VCU_DRIVER_INPUT_BRAKE);
    current = vcu_driver_input_read();
    assert(current.ignition_state == VCU_IGNITION_RUN && current.accelerator_percent == 67U);
    assert(current.gear == VCU_GEAR_D && current.brake);
    assert(current.steering_direction == VCU_STEERING_LEFT);

    vcu_driver_input_reset();
    current = vcu_driver_input_read();
    assert(current.ignition_state == VCU_IGNITION_OFF && current.accelerator_percent == 0U);
    assert(!current.brake && current.gear == VCU_GEAR_P);
    assert(current.door_lock_request == VCU_DOOR_NO_ACTION);
    assert(current.window_command == VCU_WINDOW_STOP);
    assert(current.steering_direction == VCU_STEERING_CENTER);
}

static void run_task(uint32_t count)
{
    releases = sends = expected_alive = 0;
    vcu_task_stats = (vcu_task_stats_t){0};
    stop_after = count;
    if (setjmp(done) == 0) vcu_task_run();
}

static void test_body_requests_reach_can_tx_payload(void)
{
    const vcu_serial_input_frame_t request = {
        .sequence = 1U,
        .valid_mask = VCU_SERIAL_INPUT_DOOR | VCU_SERIAL_INPUT_WINDOW,
        .inputs = {
            .door_lock_request = VCU_DOOR_LOCK,
            .window_command = VCU_WINDOW_DOWN
        }
    };
    uint8_t uart_frame[VCU_SERIAL_INPUT_FRAME_SIZE];
    vcu_serial_input_frame_t received;
    assert(vcu_serial_encode_input(&request, uart_frame));
    assert(vcu_serial_decode_input(uart_frame, sizeof(uart_frame), &received) ==
           VCU_SERIAL_STATUS_ACCEPTED);

    vcu_driver_input_reset();
    vcu_driver_input_update(&received.inputs, received.valid_mask);
    expected_body_requests = 0x90U; /* DBC: lock=01 at bit 28, down=10 at bit 30. */
    run_task(1);
    expected_body_requests = 0U;
    vcu_driver_input_reset();
}

int main(void)
{
    test_codec();
    test_vcu_application_policy();
    test_serial_protocol();
    test_driver_input_store();
    hcan1.Init.Mode = CAN_MODE_LOOPBACK;
    test_body_requests_reach_can_tx_payload();
    rx_fill = 3;
    tick = UINT32_MAX - 15U;
    run_task(35);
    assert(rx_fill == 0 && sends == 35);
    assert(vcu_task_stats.tx_accepted == 35 && vcu_task_stats.next_alive == 3);
    assert(vcu_task_stats.deadline_misses == 0);
    fail_on = 3;
    run_task(20);
    assert(vcu_task_stats.tx_errors == 1 && vcu_task_stats.next_alive == 3);
    fail_on = UINT32_MAX;
    free_mailboxes = 0;
    run_task(4);
    assert(sends == 0 && vcu_task_stats.tx_busy == 4);
    assert(vcu_task_stats.next_alive == 0);
    free_mailboxes = 3;
    overrun_on = 2;
    run_task(4);
    assert(vcu_task_stats.deadline_misses == 1);
    assert(vcu_can_send(NULL) == HAL_ERROR);
    puts("PASS: VCU app policy, UART serial protocol/ACK/CRC/ranges, input state, CAN codec/FIFO, 10 ms releases, alive wrap, TX failure/busy, overrun");
    return 0;
}
