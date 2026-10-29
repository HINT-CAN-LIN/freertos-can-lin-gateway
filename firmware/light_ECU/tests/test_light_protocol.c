#include <assert.h>
#include <stdio.h>
#include "light_protocol.h"
int main(void) {
  LightState s = {0}; uint8_t d[2];
  assert(Light_PID(0x12) == 0x92); assert(Light_PID(0x13) == 0xd3);
  for (unsigned id=0; id<64; ++id) {
    uint8_t pid=Light_PID(id);
    for (unsigned bit=0; bit<8; ++bit) {
      uint8_t bad=pid^(1u<<bit);
      assert(bad != Light_PID(bad & 63u));
    }
  }
  d[0]=0x31; assert(Light_Checksum(0x92,d,1)==0x3c);
  d[0]=0xff; d[1]=0xff; assert(Light_Checksum(0xd3,d,2)==0x2c);
  assert(Light_Diagnostic(&s,0)==1); assert(Light_Outputs(&s,0)==0);
  Light_Command(&s,0x31,10); assert(Light_Outputs(&s,259)==0x31);
  assert(Light_Outputs(&s,260)==0); assert(Light_Diagnostic(&s,260)==1);
  Light_Command(&s,2,1000); assert(Light_Outputs(&s,1000)==2);
  Light_Command(&s,2,1200); Light_Command(&s,2,1400);
  assert(Light_Outputs(&s,1499)==2); assert(Light_Outputs(&s,1500)==0);
  assert(Light_Lamps(&s,1500)==2);
  Light_Command(&s,4,1500); assert(Light_Outputs(&s,1500)==4);
  Light_Command(&s,8,1510); assert(Light_Lamps(&s,1510)==14);
  Light_Command(&s,6,1520); assert(Light_Diagnostic(&s,1520)==2);
  assert(Light_Outputs(&s,1520)==0); assert(s.last_command==1510);
  Light_Command(&s,0x31,1530); s.alive=15; s.response_error=1;
  Light_Status(&s,1530,d); assert(d[0]==0x31 && d[1]==0x4f);
  Light_Status(&s,1780,d); assert(d[0]==0 && d[1]==0x5f);
  Light_Command(&s,1,0xfffffff0u); assert(Light_Outputs(&s,20)==1);
  assert(Light_Outputs(&s,234)==0);
  for (unsigned c=0; c<256; ++c) {
    Light_Command(&s,c,2000);
    assert((Light_Lamps(&s,2000) & 0xc0u)==0);
    if (((c>>1)&3)==3) assert(Light_Outputs(&s,2000)==0);
  }
  puts("PASS: PID parity, checksum carry, timeout/wrap, invalid commands, blink, hazard, status");
}
