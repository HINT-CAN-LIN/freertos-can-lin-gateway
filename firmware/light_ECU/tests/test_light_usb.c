#include <assert.h>
#include <stdio.h>
#include "light_usb_protocol.h"
int main(void) {
 uint8_t v=0;
 assert(Light_USBDecode("S31",3,&v) && v==0x31);
 assert(Light_USBDecode("S0a",3,&v) && v==10);
 assert(!Light_USBDecode("SFF",3,&v));
 assert(!Light_USBDecode("S3G",3,&v));
 assert(!Light_USBDecode("S1",2,&v));
 assert(!Light_USBDecode("S310",4,&v));
 assert(!Light_USBDecode("X00",3,&v));
 for(unsigned i=0;i<64;i++) { char s[4];snprintf(s,sizeof s,"S%02X",i);assert(Light_USBDecode(s,3,&v)&&v==i); }
 puts("PASS: USB command decoding and malformed input");
}
