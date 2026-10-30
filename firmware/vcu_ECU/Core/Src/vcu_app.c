#include "vcu_app.h"
#include "vcu_command.h"
#include <stddef.h>

volatile vcu_vehicle_state_t vcu_vehicle_state = VCU_STATE_OFF;

static bool vcu_gear_is_valid(vcu_gear_t gear)
{
    return (unsigned)gear <= (unsigned)VCU_GEAR_R;
}

vcu_app_command_t vcu_app_process_inputs(const vcu_driver_inputs_t *inputs,
                                         vcu_vehicle_state_t *state)
{
    vcu_app_command_t command = {
        .torque_request_nm = 0.0f,
        .gear = VCU_GEAR_P,
        .brake = false,
        .door_lock_request = VCU_DOOR_NO_ACTION,
        .window_command = VCU_WINDOW_STOP
    };
    vcu_vehicle_state_t next_state = VCU_STATE_INPUT_FAULT;

    if (inputs == NULL) {
        if (state != NULL) {
            *state = next_state;
        }
        return command;
    }

    command.brake = inputs->brake;
    if ((unsigned)inputs->door_lock_request <= (unsigned)VCU_DOOR_UNLOCK) {
        command.door_lock_request = inputs->door_lock_request;
    }
    if ((unsigned)inputs->window_command <= (unsigned)VCU_WINDOW_DOWN) {
        command.window_command = inputs->window_command;
    }

    if (!vcu_gear_is_valid(inputs->gear) || inputs->accelerator_percent > 100U ||
        (unsigned)inputs->ignition_state > (unsigned)VCU_IGNITION_RUN) {
        if (state != NULL) {
            *state = next_state;
        }
        return command;
    }

    command.gear = inputs->gear;
    if (inputs->ignition_state == VCU_IGNITION_OFF) {
        next_state = VCU_STATE_OFF;
    } else if (inputs->ignition_state == VCU_IGNITION_ON) {
        /* ON powers the vehicle electronics, but does not enable propulsion. */
        next_state = VCU_STATE_IGNITION_ON;
    } else if (inputs->brake) {
        next_state = VCU_STATE_BRAKING;
    } else {
        switch (inputs->gear) {
        case VCU_GEAR_P:
            next_state = VCU_STATE_PARKED;
            break;
        case VCU_GEAR_N:
            next_state = VCU_STATE_NEUTRAL;
            break;
        case VCU_GEAR_D:
            next_state = VCU_STATE_DRIVE;
            break;
        case VCU_GEAR_R:
            next_state = VCU_STATE_REVERSE;
            break;
        default:
            next_state = VCU_STATE_INPUT_FAULT;
            command.gear = VCU_GEAR_P;
            break;
        }
    }

    /* Simulation policy assumption: pedal percentage scales across the DBC
     * torque range. Only RUN enables propulsion; ON, brake, P and N inhibit it.
     */
    if (inputs->ignition_state == VCU_IGNITION_RUN && !inputs->brake &&
        (inputs->gear == VCU_GEAR_D || inputs->gear == VCU_GEAR_R)) {
        command.torque_request_nm =
            VCU_COMMAND_TORQUE_MAX_NM * (float)inputs->accelerator_percent / 100.0f;
    }

    if (state != NULL) {
        *state = next_state;
    }
    return command;
}

vcu_app_command_t vcu_app_get_command(void)
{
    const vcu_driver_inputs_t inputs = vcu_driver_input_read();
    vcu_vehicle_state_t state;
    const vcu_app_command_t command = vcu_app_process_inputs(&inputs, &state);
    vcu_vehicle_state = state;
    return command;
}
