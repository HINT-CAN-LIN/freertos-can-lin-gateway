#ifndef LIGHT_PROTOCOL_H
#define LIGHT_PROTOCOL_H
#include <stdint.h>
#define LIGHT_COMMAND_ID 0x12u
#define LIGHT_STATUS_ID 0x13u
#define LIGHT_TIMEOUT_MS 250u
#define LIGHT_BLINK_MS 500u
#define LIGHT_FRAME_TIMEOUT_MS 10u
typedef struct {
  uint32_t last_command, blink_start;
  uint8_t command, seen, invalid, response_error, alive;
} LightState;
static inline uint8_t Light_PID(uint8_t id) {
  id &= 0x3fu;
  uint8_t p0 = ((id >> 0) ^ (id >> 1) ^ (id >> 2) ^ (id >> 4)) & 1u;
  uint8_t p1 = (~((id >> 1) ^ (id >> 3) ^ (id >> 4) ^ (id >> 5))) & 1u;
  return (uint8_t)(id | (p0 << 6) | (p1 << 7));
}
static inline uint8_t Light_Checksum(uint8_t pid, const uint8_t *data, uint8_t n) {
  uint16_t sum = pid;
  while (n--) { sum += *data++; if (sum > 255u) sum -= 255u; }
  return (uint8_t)~sum;
}
static inline void Light_Command(LightState *s, uint8_t command, uint32_t now) {
  if (((command >> 1) & 3u) == 3u) { s->invalid = 1; s->command = 0; return; }
  if (!s->seen || s->invalid || (uint32_t)(now-s->last_command) >= LIGHT_TIMEOUT_MS ||
      ((s->command ^ command) & 0x0eu)) s->blink_start = now;
  s->command = command & 0x3fu; s->last_command = now; s->seen = 1; s->invalid = 0;
}
static inline uint8_t Light_Diagnostic(const LightState *s, uint32_t now) {
  if (s->invalid) return 2;
  return (!s->seen || (uint32_t)(now-s->last_command) >= LIGHT_TIMEOUT_MS) ? 1u : 0u;
}
/* Logical lamp state, independent of the flashing phase; no physical feedback. */
static inline uint8_t Light_Lamps(const LightState *s, uint32_t now) {
  if (Light_Diagnostic(s, now)) return 0;
  uint8_t lamps = s->command & 0x31u;
  if (s->command & 8u) lamps |= 0x0eu;
  else if ((s->command & 6u) == 2u) lamps |= 2u;
  else if ((s->command & 6u) == 4u) lamps |= 4u;
  return lamps;
}
static inline uint8_t Light_Outputs(const LightState *s, uint32_t now) {
  uint8_t lamps = Light_Lamps(s, now);
  if (((uint32_t)(now-s->blink_start) / LIGHT_BLINK_MS) & 1u) lamps &= (uint8_t)~0x0eu;
  return lamps;
}
static inline void Light_Status(const LightState *s, uint32_t now, uint8_t data[2]) {
  data[0] = Light_Lamps(s, now);
  data[1] = (uint8_t)((s->alive & 15u) | (Light_Diagnostic(s, now) << 4) |
                       ((s->response_error != 0) << 6));
}
#endif
