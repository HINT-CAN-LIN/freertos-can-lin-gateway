#include "cluster_state.h"
#include <stddef.h>

static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static ClusterSampleTime received(uint32_t now) { ClusterSampleTime t = {now, true}; return t; }
ClusterFreshness cluster_sample_freshness(ClusterSampleTime t, uint32_t now)
{
  if (!t.valid || (uint32_t)(now - t.received_ms) >= CLUSTER_OFFLINE_MS) return CLUSTER_OFFLINE;
  return (uint32_t)(now - t.received_ms) >= CLUSTER_STALE_MS ? CLUSTER_STALE : CLUSTER_FRESH;
}
const char *cluster_system_name(uint8_t v)
{
  static const char *names[] = {"NORMAL", "DEGRADED", "OFFLINE", "FAIL_SAFE"};
  return v < 4 ? names[v] : "INVALID";
}
const char *cluster_fault_name(uint8_t v)
{
  static const char *names[] = {"NO OBSERVED FAULT", "VCU_TIMEOUT", "DOOR OFFLINE", "ALIVE_ERROR",
                               "ECU_OFFLINE", "QUEUE_DROP", "WINDOW OFFLINE"};
  return v < 7 ? names[v] : "INVALID";
}
const char *cluster_node_name(uint8_t v)
{
  static const char *names[] = {"NONE", "VCU", "MOTOR", "GATEWAY", "CLUSTER", "DOOR", "LIGHT", "WINDOW"};
  return v < 8 ? names[v] : "INVALID";
}
bool cluster_receive_frame(ClusterState *s, uint32_t id, const uint8_t *d,
                           uint8_t dlc, bool extended, bool remote, uint32_t now)
{
  if (!s) return false;
  if (id != 0x100 && id != 0x110 && id != 0x120 && id != 0x200 && id != 0x300 && id != 0x310) return false;
  if (!d || dlc != 8 || extended || remote) { s->rejected_frames++; return false; }
  switch (id) {
  case 0x100: {
    uint8_t alive = (d[2] >> 4) & 15;
    s->vcu.sequence_ok = !s->vcu.time.valid ||
      cluster_sample_freshness(s->vcu.time, now) != CLUSTER_FRESH ||
      alive == ((s->vcu.alive + 1) & 15);
    s->vcu.torque_request_dnm = le16(d);
    s->vcu.torque_valid = s->vcu.torque_request_dnm <= 40000;
    s->vcu.gear = d[2] & 7; s->vcu.brake = (d[2] >> 3) & 1;
    s->vcu.alive = alive; s->vcu.time = received(now); break;
  }
  case 0x110: {
    uint8_t alive = (d[4] >> 2) & 15;
    s->motor.sequence_ok = !s->motor.time.valid ||
      cluster_sample_freshness(s->motor.time, now) != CLUSTER_FRESH ||
      alive == ((s->motor.alive + 1) & 15);
    s->motor.rpm = le16(d); s->motor.torque_dnm = le16(d+2);
    s->motor.rpm_valid = s->motor.rpm <= 12000;
    s->motor.torque_valid = s->motor.torque_dnm <= 40000;
    s->motor.mode = d[4] & 3; s->motor.alive = alive; s->motor.time = received(now);
    break;
  }
  case 0x120:
    s->vehicle.speed_dkmh = le16(d); s->vehicle.rpm = le16(d+2);
    s->vehicle.gear = d[4] & 7; s->vehicle.brake = (d[4] >> 3) & 1;
    s->vehicle.network = (d[4] >> 4) & 3; s->vehicle.time = received(now);
    break;
  case 0x200:
    s->body.door = d[1]; s->body.lights = d[2]; s->body.window = d[3];
    s->body.reverse_lamp = d[0] & 1; s->body.door_open = (d[0] >> 1) & 1;
    s->body.door_consistent = d[1] <= 3 && s->body.door_open == (d[1] >= 2);
    s->body.lights_consistent = d[2] <= 63 && s->body.reverse_lamp == ((d[2] >> 4) & 1);
    s->body.time = received(now); break;
  case 0x300: {
    uint8_t alive = d[0] & 15;
    s->gateway.sequence_ok = !s->gateway.time.valid ||
      cluster_sample_freshness(s->gateway.time, now) != CLUSTER_FRESH ||
      alive == ((s->gateway.alive + 1) & 15);
    s->gateway.alive = alive; s->gateway.queue_usage = d[1];
    s->gateway.time = received(now); break;
  }
  case 0x310: {
    uint8_t code = d[0], node = d[1] & 15, cleared = (d[1] >> 4) & 1;
    if (code > 6 || node > 7) {
      s->fault.gap_seen=true; s->rejected_frames++; return false;
    }
    /* NONE is not a snapshot/reset-all instruction. CLEARED affects one key. */
    if (code) {
      if (cleared) s->fault.active_nodes[code] &= (uint8_t)~(1U << node);
      else s->fault.active_nodes[code] |= (uint8_t)(1U << node);
    }
    s->fault.last_code = code; s->fault.last_node = node; s->fault.cleared = cleared;
    s->fault.system = (d[1] >> 5) & 3; s->fault.events_seen = true;
    s->fault.time = received(now); break;
  }
  }
  return true;
}
uint8_t cluster_active_fault_count(const ClusterState *s)
{
  uint8_t count = 0;
  for (unsigned c=1; c<=6; ++c)
    for (unsigned n=0; n<8; ++n) if (s->fault.active_nodes[c] & (1U<<n)) ++count;
  return count;
}
uint8_t cluster_major_fault(const ClusterState *s, uint8_t *node)
{
  /* Display selection only: critical VCU/Alive first, then offline, then Queue.
   * Representative SystemState is always received from Gateway, not inferred. */
  static const uint8_t order[] = {1,3,4,2,6,5};
  for (unsigned i=0; i<sizeof(order); ++i)
    for (unsigned n=0; n<8; ++n) if (s->fault.active_nodes[order[i]] & (1U<<n)) {
      if (node) *node = n;
      return order[i];
    }
  if (node) *node = 0;
  return 0;
}

const char *cluster_window_name(uint8_t v)
{
  static const char *names[] = {"STOPPED", "MOVING UP", "MOVING DOWN", "UPPER LIMIT",
                               "LOWER LIMIT", "FAULT", "RESERVED"};
  return v <= 6 ? names[v] : v == 255 ? "INVALID" : "UNDEFINED";
}

bool cluster_demo_update(ClusterState *s, uint32_t now, uint32_t elapsed)
{
  if (!s) return false;
  uint32_t phase = elapsed % CLUSTER_DEMO_CYCLE_MS;
  uint8_t d[8] = {0};
  if (phase >= 18000) return false; /* No cyclic updates; events remain latched. */
  uint16_t speed = phase < 4000 ? 0 : (uint16_t)((phase / 100) % 650);
  uint16_t rpm = (uint16_t)(speed * 8);
  uint8_t system = phase >= 16000 ? 0 : phase >= 15000 ? 2 : phase >= 12000 ? 3 : phase >= 9000 ? 2 : 0;
  uint16_t torque = phase < 4000 ? 0 : 1234;
  d[0]=torque; d[1]=torque>>8;
  d[2]=(phase<4000 ? 0 : 2) | (((s->vcu.alive+1)&15)<<4);
  cluster_receive_frame(s,0x100,d,8,false,false,now);
  d[0]=speed; d[1]=speed>>8; d[2]=rpm; d[3]=rpm>>8;
  d[4]=(phase<4000 ? 0 : 2) | (system<<4);
  cluster_receive_frame(s,0x120,d,8,false,false,now);
  d[0]=0; d[1]=phase >= 9000 && phase < 16000 ? 255 : phase >= 4000 ? 3 : 1;
  d[2]=phase >= 6000 ? 0x09 : 0; d[3]=phase >= 17000 ? 255 : phase >= 16000 ? 6 : (phase/2000)%6;
  if (d[1]<=3 && d[1]>=2) d[0]|=2;
  cluster_receive_frame(s,0x200,d,8,false,false,now);
  d[0]=rpm; d[1]=rpm>>8; d[2]=0; d[3]=0;
  d[4]=(system==3 ? 3 : phase<4000 ? 1 : 2) | (((s->motor.alive+1)&15)<<2);
  cluster_receive_frame(s,0x110,d,8,false,false,now);
  d[0]=(s->gateway.alive+1)&15; d[1]=phase>=12000 ? 85 : 12;
  cluster_receive_frame(s,0x300,d,8,false,false,now);
  /* Edge transitions are keyed to current active table, not periodic Fault frames. */
  bool door = phase>=9000 && phase<16000, vcu = phase>=12000 && phase<15000;
  if (!!(s->fault.active_nodes[2] & (1U<<5)) != door) {
    d[0]=2; d[1]=5 | ((!door)<<4) | (system<<5);
    cluster_receive_frame(s,0x310,d,8,false,false,now);
  }
  if (!!(s->fault.active_nodes[1] & (1U<<1)) != vcu) {
    d[0]=1; d[1]=1 | ((!vcu)<<4) | (system<<5);
    cluster_receive_frame(s,0x310,d,8,false,false,now);
  }
  return true;
}
