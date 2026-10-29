#ifndef VCU_SERIAL_PROTOCOL_H
#define VCU_SERIAL_PROTOCOL_H

#include "vcu_app.h"

#define VCU_SERIAL_SYNC_0               0xA5U
#define VCU_SERIAL_SYNC_1               0x5AU
#define VCU_SERIAL_PROTOCOL_VERSION    2U
#define VCU_SERIAL_TYPE_DRIVER_INPUT    0x01U
#define VCU_SERIAL_TYPE_ACK             0x81U
#define VCU_SERIAL_INPUT_FRAME_SIZE     15U
#define VCU_SERIAL_ACK_FRAME_SIZE       8U

#define VCU_SERIAL_INPUT_IGNITION       (1U << 0)
#define VCU_SERIAL_INPUT_ACCELERATOR    (1U << 1)
#define VCU_SERIAL_INPUT_BRAKE          (1U << 2)
#define VCU_SERIAL_INPUT_GEAR           (1U << 3)
#define VCU_SERIAL_INPUT_DOOR           (1U << 4)
#define VCU_SERIAL_INPUT_WINDOW         (1U << 5)
#define VCU_SERIAL_INPUT_STEERING       (1U << 6)
#define VCU_SERIAL_INPUT_MASK           0x7FU

typedef enum {
    VCU_SERIAL_STATUS_ACCEPTED = 0,
    VCU_SERIAL_STATUS_BAD_VERSION = 1,
    VCU_SERIAL_STATUS_BAD_TYPE = 2,
    VCU_SERIAL_STATUS_BAD_CRC = 3,
    VCU_SERIAL_STATUS_BAD_MASK = 4,
    VCU_SERIAL_STATUS_BAD_VALUE = 5,
    VCU_SERIAL_STATUS_BAD_LENGTH = 6,
    VCU_SERIAL_STATUS_BAD_SYNC = 7
} vcu_serial_status_t;

typedef struct {
    uint16_t sequence;
    uint8_t valid_mask;
    vcu_driver_inputs_t inputs;
} vcu_serial_input_frame_t;

/* V2: A5 5A, version, type, sequence LE, mask, seven values, CRC-8. */
uint8_t vcu_serial_crc8(const uint8_t *data, uint32_t length);
vcu_serial_status_t vcu_serial_decode_input(
    const uint8_t *frame, uint32_t length, vcu_serial_input_frame_t *decoded);
bool vcu_serial_encode_input(const vcu_serial_input_frame_t *input,
                             uint8_t frame[VCU_SERIAL_INPUT_FRAME_SIZE]);
void vcu_serial_encode_ack(uint16_t sequence, vcu_serial_status_t status,
                           uint8_t frame[VCU_SERIAL_ACK_FRAME_SIZE]);

#endif
