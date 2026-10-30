#include "vcu_app.h"
#include "FreeRTOS.h"
#include "task.h"
#include <stddef.h>

static vcu_driver_inputs_t current_inputs = {
    .ignition_state = VCU_IGNITION_OFF,
    .accelerator_percent = 0U,
    .brake = false,
    .gear = VCU_GEAR_P,
    .door_lock_request = VCU_DOOR_NO_ACTION,
    .window_command = VCU_WINDOW_STOP,
    .steering_direction = VCU_STEERING_CENTER
};

vcu_driver_inputs_t vcu_driver_input_read(void)
{
    vcu_driver_inputs_t inputs;
    taskENTER_CRITICAL();
    inputs = current_inputs;
    taskEXIT_CRITICAL();
    return inputs;
}

void vcu_driver_input_update(const vcu_driver_inputs_t *inputs, uint8_t valid_mask)
{
    if (inputs == NULL) {
        return;
    }

    taskENTER_CRITICAL();
    if ((valid_mask & VCU_DRIVER_INPUT_IGNITION) != 0U) {
        current_inputs.ignition_state = inputs->ignition_state;
    }
    if ((valid_mask & VCU_DRIVER_INPUT_ACCELERATOR) != 0U) {
        current_inputs.accelerator_percent = inputs->accelerator_percent;
    }
    if ((valid_mask & VCU_DRIVER_INPUT_BRAKE) != 0U) {
        current_inputs.brake = inputs->brake;
    }
    if ((valid_mask & VCU_DRIVER_INPUT_GEAR) != 0U) {
        current_inputs.gear = inputs->gear;
    }
    if ((valid_mask & VCU_DRIVER_INPUT_DOOR) != 0U) {
        current_inputs.door_lock_request = inputs->door_lock_request;
    }
    if ((valid_mask & VCU_DRIVER_INPUT_WINDOW) != 0U) {
        current_inputs.window_command = inputs->window_command;
    }
    if ((valid_mask & VCU_DRIVER_INPUT_STEERING) != 0U) {
        current_inputs.steering_direction = inputs->steering_direction;
    }
    taskEXIT_CRITICAL();
}

void vcu_driver_input_reset(void)
{
    const vcu_driver_inputs_t safe_inputs = {
        .ignition_state = VCU_IGNITION_OFF,
        .accelerator_percent = 0U,
        .brake = false,
        .gear = VCU_GEAR_P,
        .door_lock_request = VCU_DOOR_NO_ACTION,
        .window_command = VCU_WINDOW_STOP,
        .steering_direction = VCU_STEERING_CENTER
    };
    taskENTER_CRITICAL();
    current_inputs = safe_inputs;
    taskEXIT_CRITICAL();
}
