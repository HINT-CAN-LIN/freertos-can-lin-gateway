#include "motor_watchdog.h"
#include "motor_app.h"
#include <stdio.h>
int main(void) {
 MotorWatchdog w; MotorVcuCommand c={0}; motor_watchdog_init(&w,0);
 motor_watchdog_poll(&w,31);
 for(unsigned i=0;i<4;i++){ c.alive=i; motor_watchdog_receive(&w,40+i*10,&c,true); printf("recovery frame %u inhibit=%u count=%u\n",i+1,w.inhibit,w.recovery_count); }
 printf("steer -20 raw bytes: %02X %02X; proposed Head=%u Turn=%u Hazard=%u Door=%u Window=%u\n",0x38,0xFF,0x38&1,(0x38>>1)&3,(0x38>>3)&1,(0x38>>4)&3,(0x38>>6)&3);
 printf("pulse left45=%u center=%u right45=%u\n",motor_servo_pulse_us(-450,1500,0),motor_servo_pulse_us(0,1500,0),motor_servo_pulse_us(450,1500,0));
}
