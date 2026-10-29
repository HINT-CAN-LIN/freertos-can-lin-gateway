#ifndef LIGHT_USB_PROTOCOL_H
#define LIGHT_USB_PROTOCOL_H
#include <stdint.h>
static inline int Light_Hex(char c) {
  if(c>='0' && c<='9') return c-'0';
  if(c>='A' && c<='F') return c-'A'+10;
  if(c>='a' && c<='f') return c-'a'+10;
  return -1;
}
/* Exact command: Sxx newline. Same command byte as the LIN application. */
static inline int Light_USBDecode(const char *s, unsigned n, uint8_t *value) {
  if(n!=3 || s[0]!='S') return 0;
  int a=Light_Hex(s[1]), b=Light_Hex(s[2]);
  if(a<0 || b<0 || a>3) return 0;
  *value=(uint8_t)((a<<4)|b); return 1;
}
#endif
