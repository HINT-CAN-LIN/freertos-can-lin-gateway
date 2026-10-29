#include "vcu_command_codec.h"
#include <stddef.h>
#include <string.h>

/* DBC: TorqueRequest 0|16, Gear 16|3, Brake 19|1, AliveCounter 20|4,
 * DoorLockRequest 28|2, WindowCommand 30|2.
 * TorqueRequest factor 0.1 Nm/raw, normal physical range 0..4000 Nm;
 * 0xFFFF is invalid. Gear 4..6 reserved, 7 invalid: never transmit them.
 */
enum {
    TORQUE_START_BIT = 0, TORQUE_LENGTH = 16,
    GEAR_START_BIT = 16, GEAR_LENGTH = 3,
    BRAKE_START_BIT = 19, BRAKE_LENGTH = 1,
    ALIVE_START_BIT = 20, ALIVE_LENGTH = 4,
    DOOR_LOCK_START_BIT = 28, DOOR_LOCK_LENGTH = 2,
    WINDOW_COMMAND_START_BIT = 30, WINDOW_COMMAND_LENGTH = 2
};

static void pack_unsigned(uint8_t *data, uint32_t raw,
                          unsigned start, unsigned length)
{
    for (unsigned bit = 0; bit < length; ++bit) {
        unsigned position = start + bit;
        data[position / 8U] |= (uint8_t)(((raw >> bit) & 1U)
                                        << (position % 8U));
    }
}

bool vcu_command_encode(const vcu_app_command_t *command, uint8_t alive,
                        uint8_t data[VCU_COMMAND_DLC])
{
    if (command == NULL || data == NULL ||
        !(command->torque_request_nm >= VCU_COMMAND_TORQUE_MIN_NM &&
          command->torque_request_nm <= VCU_COMMAND_TORQUE_MAX_NM) ||
        (unsigned)command->gear > (unsigned)VCU_GEAR_R ||
        (unsigned)command->door_lock_request > VCU_COMMAND_DOOR_REQUEST_MAX ||
        (unsigned)command->window_command > VCU_COMMAND_WINDOW_REQUEST_MAX ||
        alive >= VCU_COMMAND_ALIVE_MODULO) {
        return false;
    }

    uint32_t torque_raw = (uint32_t)(command->torque_request_nm /
                                    VCU_COMMAND_TORQUE_FACTOR_NM + 0.5f);
    memset(data, 0, VCU_COMMAND_DLC);
    pack_unsigned(data, torque_raw, TORQUE_START_BIT, TORQUE_LENGTH);
    pack_unsigned(data, (uint32_t)command->gear, GEAR_START_BIT, GEAR_LENGTH);
    pack_unsigned(data, command->brake ? 1U : 0U, BRAKE_START_BIT, BRAKE_LENGTH);
    pack_unsigned(data, alive, ALIVE_START_BIT, ALIVE_LENGTH);
    pack_unsigned(data, (uint32_t)command->door_lock_request,
                  DOOR_LOCK_START_BIT, DOOR_LOCK_LENGTH);
    pack_unsigned(data, (uint32_t)command->window_command,
                  WINDOW_COMMAND_START_BIT, WINDOW_COMMAND_LENGTH);
    return true;
}
