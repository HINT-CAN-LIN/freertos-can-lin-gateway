#ifndef MOTOR_CAN_H
#define MOTOR_CAN_H
#include <stdbool.h>
#include <stdint.h>

/* motor_ecu.dbc: base 0.4 + local SteeringAngle/diagnostics extension 0.6. */
#define MOTOR_CAN_VCU_ID 0x100u
#define MOTOR_CAN_STATUS_ID 0x110u
#define MOTOR_CAN_GATEWAY_ID 0x300u
#define MOTOR_CAN_DLC 8u
#define MOTOR_STATUS_PERIOD_MS 10u
#define MOTOR_VCU_TIMEOUT_MS 30u
#define MOTOR_FIRMWARE_REVISION 4u
#define MOTOR_FAULT_TIMEOUT 1u
#define MOTOR_FAULT_ALIVE 2u
#define MOTOR_FAULT_INVALID 4u
#define MOTOR_FAULT_RX_LOSS 8u

typedef struct {
    uint32_t id;
    uint8_t dlc;
    bool extended, remote;
    uint8_t data[8];
} MotorCanFrame;

/* Torque stays in raw 0.1 Nm units; VCU owns command generation. */
typedef struct {
    uint16_t torque_raw;
    uint8_t gear, brake, alive;
    int16_t steering_raw; /* VCU Byte4..5; Byte3 is not steering. Signed 0.1 degree; -450=left45, +450=right45. */
} MotorVcuCommand;

typedef struct { uint8_t alive, queue_usage; } MotorGatewayStatus;
typedef enum {
    MOTOR_OFF = 0, MOTOR_READY = 1, MOTOR_RUN = 2, MOTOR_FAIL_SAFE = 3
} MotorState;
typedef struct {
    uint16_t rpm, torque_raw;
    MotorState state;
    uint8_t alive;
    int16_t steering_raw; /* Validated target echo; not measured shaft angle. */
    uint8_t fault_flags, firmware_revision;
} MotorStatus;

/* Decode extracts raw fields; motor_app validates ranges/invalid values. */
bool motor_can_decode_vcu(const MotorCanFrame *frame, MotorVcuCommand *out);
bool motor_can_decode_gateway(const MotorCanFrame *frame, MotorGatewayStatus *out);
/* Unused TX bytes/bits are zero. */
bool motor_can_encode_status(const MotorStatus *status, MotorCanFrame *out);
#endif
