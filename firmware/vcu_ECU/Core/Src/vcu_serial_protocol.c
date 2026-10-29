#include "vcu_serial_protocol.h"
#include <stddef.h>
#include <string.h>

enum {
    SYNC_0_OFFSET = 0,
    SYNC_1_OFFSET = 1,
    VERSION_OFFSET = 2,
    TYPE_OFFSET = 3,
    SEQUENCE_LOW_OFFSET = 4,
    SEQUENCE_HIGH_OFFSET = 5,
    INPUT_MASK_OFFSET = 6,
    IGNITION_OFFSET = 7,
    ACCELERATOR_OFFSET = 8,
    BRAKE_OFFSET = 9,
    GEAR_OFFSET = 10,
    DOOR_OFFSET = 11,
    WINDOW_OFFSET = 12,
    STEERING_OFFSET = 13,
    INPUT_CRC_OFFSET = 14,
    ACK_STATUS_OFFSET = 6,
    ACK_CRC_OFFSET = 7,
    CRC_START_OFFSET = VERSION_OFFSET
};

uint8_t vcu_serial_crc8(const uint8_t *data, uint32_t length)
{
    uint8_t crc = 0U;
    if (data == NULL) {
        return 0U;
    }

    for (uint32_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8U; ++bit) {
            crc = (crc & 0x80U) != 0U
                    ? (uint8_t)((crc << 1U) ^ 0x07U)
                    : (uint8_t)(crc << 1U);
        }
    }
    return crc;
}

static bool input_fields_valid(const vcu_serial_input_frame_t *input)
{
    const uint8_t mask = input->valid_mask;
    if (mask == 0U || (mask & (uint8_t)~VCU_SERIAL_INPUT_MASK) != 0U) {
        return false;
    }
    if ((mask & VCU_SERIAL_INPUT_IGNITION) != 0U &&
        (unsigned)input->inputs.ignition_state > (unsigned)VCU_IGNITION_RUN) {
        return false;
    }
    if ((mask & VCU_SERIAL_INPUT_ACCELERATOR) != 0U &&
        input->inputs.accelerator_percent > 100U) {
        return false;
    }
    if ((mask & VCU_SERIAL_INPUT_GEAR) != 0U &&
        (unsigned)input->inputs.gear > (unsigned)VCU_GEAR_R) {
        return false;
    }
    if ((mask & VCU_SERIAL_INPUT_DOOR) != 0U &&
        (unsigned)input->inputs.door_lock_request > (unsigned)VCU_DOOR_UNLOCK) {
        return false;
    }
    if ((mask & VCU_SERIAL_INPUT_WINDOW) != 0U &&
        (unsigned)input->inputs.window_command > (unsigned)VCU_WINDOW_DOWN) {
        return false;
    }
    if ((mask & VCU_SERIAL_INPUT_STEERING) != 0U &&
        (unsigned)input->inputs.steering_direction > (unsigned)VCU_STEERING_RIGHT) {
        return false;
    }
    return true;
}

vcu_serial_status_t vcu_serial_decode_input(
    const uint8_t *frame, uint32_t length, vcu_serial_input_frame_t *decoded)
{
    if (frame == NULL || decoded == NULL || length != VCU_SERIAL_INPUT_FRAME_SIZE) {
        return VCU_SERIAL_STATUS_BAD_LENGTH;
    }
    if (frame[SYNC_0_OFFSET] != VCU_SERIAL_SYNC_0 ||
        frame[SYNC_1_OFFSET] != VCU_SERIAL_SYNC_1) {
        return VCU_SERIAL_STATUS_BAD_SYNC;
    }
    if (vcu_serial_crc8(&frame[CRC_START_OFFSET],
                        INPUT_CRC_OFFSET - CRC_START_OFFSET) != frame[INPUT_CRC_OFFSET]) {
        return VCU_SERIAL_STATUS_BAD_CRC;
    }
    if (frame[VERSION_OFFSET] != VCU_SERIAL_PROTOCOL_VERSION) {
        return VCU_SERIAL_STATUS_BAD_VERSION;
    }
    if (frame[TYPE_OFFSET] != VCU_SERIAL_TYPE_DRIVER_INPUT) {
        return VCU_SERIAL_STATUS_BAD_TYPE;
    }

    vcu_serial_input_frame_t candidate = {
        .sequence = (uint16_t)frame[SEQUENCE_LOW_OFFSET] |
                    ((uint16_t)frame[SEQUENCE_HIGH_OFFSET] << 8U),
        .valid_mask = frame[INPUT_MASK_OFFSET],
        .inputs = {
            .ignition_state = (vcu_ignition_state_t)frame[IGNITION_OFFSET],
            .accelerator_percent = frame[ACCELERATOR_OFFSET],
            .brake = frame[BRAKE_OFFSET] != 0U,
            .gear = (vcu_gear_t)frame[GEAR_OFFSET],
            .door_lock_request = (vcu_door_lock_request_t)frame[DOOR_OFFSET],
            .window_command = (vcu_window_command_t)frame[WINDOW_OFFSET],
            .steering_direction = (vcu_steering_direction_t)frame[STEERING_OFFSET]
        }
    };

    if (candidate.valid_mask == 0U ||
        (candidate.valid_mask & (uint8_t)~VCU_SERIAL_INPUT_MASK) != 0U) {
        return VCU_SERIAL_STATUS_BAD_MASK;
    }
    if (((candidate.valid_mask & VCU_SERIAL_INPUT_IGNITION) != 0U &&
         frame[IGNITION_OFFSET] > (uint8_t)VCU_IGNITION_RUN) ||
        ((candidate.valid_mask & VCU_SERIAL_INPUT_ACCELERATOR) != 0U &&
         frame[ACCELERATOR_OFFSET] > 100U) ||
        ((candidate.valid_mask & VCU_SERIAL_INPUT_BRAKE) != 0U &&
         frame[BRAKE_OFFSET] > 1U) ||
        ((candidate.valid_mask & VCU_SERIAL_INPUT_GEAR) != 0U &&
         frame[GEAR_OFFSET] > (uint8_t)VCU_GEAR_R) ||
        ((candidate.valid_mask & VCU_SERIAL_INPUT_DOOR) != 0U &&
         frame[DOOR_OFFSET] > (uint8_t)VCU_DOOR_UNLOCK) ||
        ((candidate.valid_mask & VCU_SERIAL_INPUT_WINDOW) != 0U &&
         frame[WINDOW_OFFSET] > (uint8_t)VCU_WINDOW_DOWN) ||
        ((candidate.valid_mask & VCU_SERIAL_INPUT_STEERING) != 0U &&
         frame[STEERING_OFFSET] > (uint8_t)VCU_STEERING_RIGHT)) {
        return VCU_SERIAL_STATUS_BAD_VALUE;
    }
    *decoded = candidate;
    return VCU_SERIAL_STATUS_ACCEPTED;
}

bool vcu_serial_encode_input(const vcu_serial_input_frame_t *input,
                             uint8_t frame[VCU_SERIAL_INPUT_FRAME_SIZE])
{
    if (input == NULL || frame == NULL || !input_fields_valid(input)) {
        return false;
    }

    memset(frame, 0, VCU_SERIAL_INPUT_FRAME_SIZE);
    frame[SYNC_0_OFFSET] = VCU_SERIAL_SYNC_0;
    frame[SYNC_1_OFFSET] = VCU_SERIAL_SYNC_1;
    frame[VERSION_OFFSET] = VCU_SERIAL_PROTOCOL_VERSION;
    frame[TYPE_OFFSET] = VCU_SERIAL_TYPE_DRIVER_INPUT;
    frame[SEQUENCE_LOW_OFFSET] = (uint8_t)input->sequence;
    frame[SEQUENCE_HIGH_OFFSET] = (uint8_t)(input->sequence >> 8U);
    frame[INPUT_MASK_OFFSET] = input->valid_mask;
    frame[IGNITION_OFFSET] = (uint8_t)input->inputs.ignition_state;
    frame[ACCELERATOR_OFFSET] = input->inputs.accelerator_percent;
    frame[BRAKE_OFFSET] = input->inputs.brake ? 1U : 0U;
    frame[GEAR_OFFSET] = (uint8_t)input->inputs.gear;
    frame[DOOR_OFFSET] = (uint8_t)input->inputs.door_lock_request;
    frame[WINDOW_OFFSET] = (uint8_t)input->inputs.window_command;
    frame[STEERING_OFFSET] = (uint8_t)input->inputs.steering_direction;
    frame[INPUT_CRC_OFFSET] = vcu_serial_crc8(
        &frame[CRC_START_OFFSET], INPUT_CRC_OFFSET - CRC_START_OFFSET);
    return true;
}

void vcu_serial_encode_ack(uint16_t sequence, vcu_serial_status_t status,
                           uint8_t frame[VCU_SERIAL_ACK_FRAME_SIZE])
{
    if (frame == NULL) {
        return;
    }
    frame[SYNC_0_OFFSET] = VCU_SERIAL_SYNC_0;
    frame[SYNC_1_OFFSET] = VCU_SERIAL_SYNC_1;
    frame[VERSION_OFFSET] = VCU_SERIAL_PROTOCOL_VERSION;
    frame[TYPE_OFFSET] = VCU_SERIAL_TYPE_ACK;
    frame[SEQUENCE_LOW_OFFSET] = (uint8_t)sequence;
    frame[SEQUENCE_HIGH_OFFSET] = (uint8_t)(sequence >> 8U);
    frame[ACK_STATUS_OFFSET] = (uint8_t)status;
    frame[ACK_CRC_OFFSET] = vcu_serial_crc8(
        &frame[CRC_START_OFFSET], ACK_CRC_OFFSET - CRC_START_OFFSET);
}
