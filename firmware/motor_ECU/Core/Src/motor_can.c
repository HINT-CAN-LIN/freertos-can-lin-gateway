#include "motor_can.h"
#include <stddef.h>

static bool matches(const MotorCanFrame *f, uint32_t id)
{
    return f != NULL && f->id == id && f->dlc == MOTOR_CAN_DLC &&
           !f->extended && !f->remote;
}

static uint16_t read_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

bool motor_can_decode_vcu(const MotorCanFrame *frame, MotorVcuCommand *out)
{
    if (out == NULL || !matches(frame, MOTOR_CAN_VCU_ID)) return false;
    out->torque_raw = read_u16(frame->data);
    out->gear = frame->data[2] & 7u;
    out->brake = (frame->data[2] >> 3) & 1u;
    out->alive = (frame->data[2] >> 4) & 15u;
    /* Byte 3 carries DoorLockRequest/WindowCommand in the current DBC;
     * bytes 4..7 are reserved here. Never interpret them as steering. */
    out->steering_raw = 0;
    return true;
}

bool motor_can_decode_gateway(const MotorCanFrame *frame, MotorGatewayStatus *out)
{
    if (out == NULL || !matches(frame, MOTOR_CAN_GATEWAY_ID)) return false;
    out->alive = frame->data[0] & 15u;
    out->queue_usage = frame->data[1];
    return true;
}

bool motor_can_encode_status(const MotorStatus *s, MotorCanFrame *out)
{
    MotorCanFrame f = {0};
    if (s == NULL || out == NULL || s->alive > 15u ||
        (unsigned)s->state > (unsigned)MOTOR_FAIL_SAFE ||
        (s->rpm > 12000u && s->rpm != UINT16_MAX) ||
        (s->torque_raw > 40000u && s->torque_raw != UINT16_MAX)) return false;
    f.id = MOTOR_CAN_STATUS_ID;
    f.dlc = MOTOR_CAN_DLC;
    f.data[0] = (uint8_t)s->rpm;
    f.data[1] = (uint8_t)(s->rpm >> 8);
    f.data[2] = (uint8_t)s->torque_raw;
    f.data[3] = (uint8_t)(s->torque_raw >> 8);
    f.data[4] = (uint8_t)((uint8_t)s->state | (s->alive << 2));
    /* Current Motor_Status DBC defines bytes 5..7 as reserved. */
    *out = f;
    return true;
}
