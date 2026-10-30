#ifndef VCU_PC_CAN_H
#define VCU_PC_CAN_H
#include <stdint.h>
#include <stdbool.h>
#define PC_INPUT_CAN_ID 0x200U
#define PC_ACK_CAN_ID 0x201U
#define PC_INPUT_TIMEOUT_MS 300U
static inline uint8_t pc_crc(const uint8_t *d) {
    uint8_t crc=0;
    for (unsigned i=0;i<7;i++) {
        crc ^= d[i];
        for (unsigned b=0;b<8;b++) crc=(uint8_t)((crc<<1)^((crc&128)?7:0));
    }
    return crc;
}
static inline bool pc_valid(const uint8_t *d) {
    return d[0]==1 && d[3]<=2 && d[4]<=20 && d[5]<=1 && d[6]<=3 && d[7]==pc_crc(d);
}
static inline bool pc_safe(const uint8_t *d) {
    return d[3]==0 && d[4]==0 && d[5]==1 && d[6]==0;
}
void vcu_pc_can_poll(void);
#endif
