#ifndef CLUSTER_STATE_H
#define CLUSTER_STATE_H
#include <stdint.h>
#include <stdbool.h>

/* Local display policy, NOT Gateway fault deadlines. Numeric limits are
 * not frozen by the system documents; keep them explicit pending team review. */
#define CLUSTER_STALE_MS 1000U
#define CLUSTER_OFFLINE_MS 3000U
#define CLUSTER_DEMO_CYCLE_MS 24000U
/* 1: LCD demo, CAN disabled. 0: actual CAN RX, no application TX. */
#define CLUSTER_TEST_INPUT 1

typedef enum { CLUSTER_FRESH, CLUSTER_STALE, CLUSTER_OFFLINE } ClusterFreshness;
typedef struct { uint32_t received_ms; bool valid; } ClusterSampleTime;
typedef struct {
  uint16_t torque_request_dnm;
  uint8_t gear, brake, alive;
  bool torque_valid, sequence_ok;
  ClusterSampleTime time;
} ClusterVcuState;
typedef struct {
  uint16_t speed_dkmh, rpm;
  uint8_t gear, brake, network;
  ClusterSampleTime time;
} ClusterVehicleState;
typedef struct {
  uint8_t door, lights, window, reverse_lamp, door_open;
  bool door_consistent, lights_consistent;
  ClusterSampleTime time;
} ClusterBodyState;
typedef struct {
  uint16_t rpm, torque_dnm;
  uint8_t mode, alive;
  bool sequence_ok, rpm_valid, torque_valid;
  ClusterSampleTime time;
} ClusterMotorState;
typedef struct {
  uint8_t alive, queue_usage;
  bool sequence_ok;
  ClusterSampleTime time;
} ClusterGatewayState;
typedef struct {
  /* Fault code 1..6 x source node 0..7; no fixed-slot overflow. */
  uint8_t active_nodes[7];
  uint8_t last_code, last_node, cleared, system;
  bool events_seen, gap_seen;
  ClusterSampleTime time;
} ClusterFaultState;
typedef struct {
  ClusterVcuState vcu;
  ClusterVehicleState vehicle;
  ClusterBodyState body;
  ClusterMotorState motor;
  ClusterGatewayState gateway;
  ClusterFaultState fault;
  uint32_t rejected_frames;
} ClusterState;

ClusterFreshness cluster_sample_freshness(ClusterSampleTime sample, uint32_t now_ms);
/* Task-context only. Standard 11-bit DATA, DLC=8; ISR must queue first. */
bool cluster_receive_frame(ClusterState *state, uint32_t id, const uint8_t *data,
                           uint8_t dlc, bool extended, bool remote, uint32_t now_ms);
uint8_t cluster_active_fault_count(const ClusterState *state);
uint8_t cluster_major_fault(const ClusterState *state, uint8_t *node);
const char *cluster_system_name(uint8_t value);
const char *cluster_fault_name(uint8_t code);
const char *cluster_node_name(uint8_t node);
bool cluster_demo_update(ClusterState *state, uint32_t now_ms, uint32_t elapsed_ms);
const char *cluster_window_name(uint8_t value);
bool cluster_state_self_test(void);
#endif
