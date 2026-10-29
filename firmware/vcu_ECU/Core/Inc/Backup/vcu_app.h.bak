#ifndef VCU_APP_H
#define VCU_APP_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    VCU_GEAR_P = 0,
    VCU_GEAR_N = 1,
    VCU_GEAR_D = 2,
    VCU_GEAR_R = 3
} vcu_gear_t;

typedef enum {
    VCU_IGNITION_OFF = 0,
    VCU_IGNITION_ON = 1,
    VCU_IGNITION_RUN = 2,
    VCU_IGNITION_INVALID = 3
} vcu_ignition_state_t;

typedef enum {
    VCU_DOOR_NO_ACTION = 0,
    VCU_DOOR_LOCK = 1,
    VCU_DOOR_UNLOCK = 2,
    VCU_DOOR_INVALID = 3
} vcu_door_lock_request_t;

typedef enum {
    VCU_WINDOW_STOP = 0,
    VCU_WINDOW_UP = 1,
    VCU_WINDOW_DOWN = 2,
    VCU_WINDOW_INVALID = 3
} vcu_window_command_t;

/* USB-UART driver input only; the production CAN DBC has no steering signal. */
typedef enum {
    VCU_STEERING_CENTER = 0,
    VCU_STEERING_LEFT = 1,
    VCU_STEERING_RIGHT = 2,
    VCU_STEERING_INVALID = 3
} vcu_steering_direction_t;

typedef struct {
    vcu_ignition_state_t ignition_state;
    uint8_t accelerator_percent;
    bool brake;
    vcu_gear_t gear;
    vcu_door_lock_request_t door_lock_request;
    vcu_window_command_t window_command;
    vcu_steering_direction_t steering_direction;
} vcu_driver_inputs_t;

/* Presence bits let serial commands update only explicitly configured inputs. */
#define VCU_DRIVER_INPUT_IGNITION       (1U << 0)
#define VCU_DRIVER_INPUT_ACCELERATOR    (1U << 1)
#define VCU_DRIVER_INPUT_BRAKE          (1U << 2)
#define VCU_DRIVER_INPUT_GEAR           (1U << 3)
#define VCU_DRIVER_INPUT_DOOR           (1U << 4)
#define VCU_DRIVER_INPUT_WINDOW         (1U << 5)
#define VCU_DRIVER_INPUT_STEERING       (1U << 6)

void vcu_driver_input_update(const vcu_driver_inputs_t *inputs, uint8_t valid_mask);
void vcu_driver_input_reset(void);

typedef enum {
    VCU_STATE_OFF = 0,
    VCU_STATE_IGNITION_ON,
    VCU_STATE_PARKED,
    VCU_STATE_NEUTRAL,
    VCU_STATE_BRAKING,
    VCU_STATE_DRIVE,
    VCU_STATE_REVERSE,
    VCU_STATE_INPUT_FAULT
} vcu_vehicle_state_t;

typedef struct {
    float torque_request_nm;
    vcu_gear_t gear;
    bool brake;
    vcu_door_lock_request_t door_lock_request;
    vcu_window_command_t window_command;
} vcu_app_command_t;

/* Single writer is the 10 ms transmit task; useful for debugger inspection. */
extern volatile vcu_vehicle_state_t vcu_vehicle_state;

/* Deterministic mock input provider; replace only after board I/O is approved. */
vcu_driver_inputs_t vcu_driver_input_read(void);

/* Pure application policy, exposed for host verification. */
vcu_app_command_t vcu_app_process_inputs(const vcu_driver_inputs_t *inputs,
                                         vcu_vehicle_state_t *state);

/* Reads mock inputs and applies the VCU policy for the next CAN command. */
vcu_app_command_t vcu_app_get_command(void);

#endif
