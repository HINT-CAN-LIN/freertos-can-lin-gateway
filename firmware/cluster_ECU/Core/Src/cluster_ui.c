#include "cluster_ui.h"
#include "st7796.h"
#include "lvgl/lvgl.h"

/* 19,200 bytes, rather than a 307,200-byte full framebuffer. */
static uint32_t draw_buffer[480 * 20 * 2 / sizeof(uint32_t)];
static volatile HAL_StatusTypeDef display_status = HAL_OK;
static lv_obj_t *uptime_label;
static lv_obj_t *speed_label, *mode_label, *lights_label, *door_label, *window_label;
static lv_obj_t *rpm_label, *motor_label, *link_label;
static lv_obj_t *fault_label, *fault_detail_label, *health_label;
static ClusterState state;
static ClusterState shown;
static ClusterFreshness shown_vehicle, shown_body, shown_motor, shown_gateway;
volatile uint32_t cluster_demo_active_faults;
static bool shown_valid;
static uint8_t shown_system = 255;
static ClusterFreshness shown_vcu;
static uint32_t last_demo_ms;
volatile bool cluster_model_test_passed;
/* These globals allow diagnostics without calling LVGL from another task. */
volatile uint32_t cluster_demo_phase_ms;
volatile ClusterFreshness cluster_demo_health;
static uint32_t last_second = UINT32_MAX;
static uint32_t start_ms;

static void flush(lv_display_t *display, const lv_area_t *area, uint8_t *pixels)
{
  /* ponytail: blocking transfer; switch to DMA when measured UI latency requires it. */
  if (display_status == HAL_OK)
    display_status = st7796_blit(area->x1, area->y1, area->x2, area->y2, pixels);
  /* The SPI transfer has finished; LVGL may reuse the buffer now. */
  lv_display_flush_ready(display);
}

static lv_obj_t *label(lv_obj_t *parent, const char *text, int x, int y,
                       const lv_font_t *font, uint32_t color)
{
  lv_obj_t *obj = lv_label_create(parent);
  lv_label_set_text(obj, text);
  lv_obj_set_style_text_font(obj, font, 0);
  lv_obj_set_style_text_color(obj, lv_color_hex(color), 0);
  lv_obj_set_pos(obj, x, y);
  return obj;
}

static lv_obj_t *panel(lv_obj_t *parent, int x, int y, int w, int h)
{
  lv_obj_t *obj = lv_obj_create(parent);
  lv_obj_remove_style_all(obj);
  lv_obj_set_pos(obj, x, y);
  lv_obj_set_size(obj, w, h);
  lv_obj_set_style_bg_color(obj, lv_color_hex(0x172334), 0);
  lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
  lv_obj_set_style_radius(obj, 10, 0);
  lv_obj_set_scrollable(obj, false);
  return obj;
}

HAL_StatusTypeDef cluster_ui_init(void)
{
  cluster_model_test_passed = cluster_state_self_test();
  if (!cluster_model_test_passed) return HAL_ERROR;
  display_status = st7796_init();
  if (display_status != HAL_OK) return display_status;
  lv_init();
  lv_tick_set_cb(HAL_GetTick);
  lv_display_t *display = lv_display_create(480, 320);
  if (display == NULL) return HAL_ERROR;
  lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB565);
  lv_display_set_buffers(display, draw_buffer, NULL, sizeof(draw_buffer), LV_DISPLAY_RENDER_MODE_PARTIAL);
  lv_display_set_flush_cb(display, flush);
  lv_obj_t *screen = lv_screen_active();
  lv_obj_set_style_bg_color(screen, lv_color_hex(0x0B1220), 0);
  lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, 0);
  lv_obj_set_scrollable(screen, false);
  label(screen, "CLUSTER ECU", 16, 12, &lv_font_montserrat_20, 0xFFFFFF);
  label(screen, CLUSTER_TEST_INPUT ? "TEST MODE" : "CAN RX", 365, 17, &lv_font_montserrat_14, 0xFFCC66);
  lv_obj_t *vehicle = panel(screen, 12, 48, 224, 196);
  label(vehicle, "VEHICLE / MOTOR", 12, 10, &lv_font_montserrat_14, 0x9BAAC0);
  speed_label = label(vehicle, "--", 12, 32, &lv_font_montserrat_48, 0xFFFFFF);
  lv_obj_set_width(speed_label, 200);
  lv_obj_set_style_text_align(speed_label, LV_TEXT_ALIGN_CENTER, 0);
  label(vehicle, "km/h", 89, 87, &lv_font_montserrat_14, 0x9BAAC0);
  rpm_label = label(vehicle, "RPM: --", 12, 112, &lv_font_montserrat_14, 0xFFFFFF);
  mode_label = label(vehicle, "GEAR: -- BRAKE: --", 12, 139, &lv_font_montserrat_14, 0x64D9FF);
  motor_label = label(vehicle, "MOTOR: --", 12, 167, &lv_font_montserrat_14, 0x9BAAC0);
  lv_obj_t *body = panel(screen, 244, 48, 224, 116);
  label(body, "BODY STATUS", 10, 8, &lv_font_montserrat_14, 0x9BAAC0);
  door_label = label(body, "DOOR: --", 10, 31, &lv_font_montserrat_14, 0xFFFFFF);
  window_label = label(body, "WINDOW: --", 10, 54, &lv_font_montserrat_14, 0xFFFFFF);
  lights_label = label(body, "LAMPS: --", 10, 77, &lv_font_montserrat_14, 0x64D9FF);
  lv_obj_set_width(lights_label, 204);
  lv_label_set_long_mode(lights_label, LV_LABEL_LONG_WRAP);
  lv_obj_t *fault = panel(screen, 244, 172, 224, 72);
  label(fault, "FAULT / EVENT", 10, 7, &lv_font_montserrat_14, 0x9BAAC0);
  fault_label = label(fault, "WAITING FOR EVENTS", 10, 28, &lv_font_montserrat_14, 0xFFCC66);
  fault_detail_label = label(fault, "Active table incomplete", 10, 50, &lv_font_montserrat_14, 0x9BAAC0);
  health_label = label(screen, "SYSTEM: UNKNOWN", 16, 254, &lv_font_montserrat_14, 0xFFCC66);
  link_label = label(screen, "RX V/B/M/G: OFFLINE", 16, 275, &lv_font_montserrat_14, 0x9BAAC0);
  uptime_label = label(screen, "UI UPTIME: 0 s", 16, 298, &lv_font_montserrat_14, 0x9BAAC0);
  /* Finish the expensive first full-screen paint before live CAN starts. */
  lv_refr_now(display);
  start_ms = HAL_GetTick();
  last_demo_ms = start_ms - 200U;
  return HAL_OK;
}

void cluster_ui_set_state(const ClusterState *next)
{
  if (next != NULL) state = *next;
}

static const char *fresh_name(ClusterFreshness f)
{
  return f==CLUSTER_FRESH ? "OK" : f==CLUSTER_STALE ? "STALE" : "OFF";
}
static void refresh_state(uint32_t now)
{
  ClusterFreshness c=cluster_sample_freshness(state.vcu.time,now);
  ClusterFreshness v=cluster_sample_freshness(state.vehicle.time,now);
  ClusterFreshness b=cluster_sample_freshness(state.body.time,now);
  ClusterFreshness m=cluster_sample_freshness(state.motor.time,now);
  ClusterFreshness g=cluster_sample_freshness(state.gateway.time,now);
  if (state.gateway.time.valid && g!=CLUSTER_FRESH) state.fault.gap_seen=true;
  bool event_newer=state.fault.time.valid && (uint32_t)(now-state.fault.time.received_ms)<=
    (uint32_t)(now-state.vehicle.time.received_ms);
  uint8_t system_value=v!=CLUSTER_FRESH?255:event_newer?state.fault.system:state.vehicle.network;
  bool changed=c!=shown_vcu || system_value!=shown_system || !shown_valid || v!=shown_vehicle || b!=shown_body || m!=shown_motor || g!=shown_gateway;
  /* Compare values, not receive timestamps, to avoid redrawing unchanged labels. */
  changed=changed || state.vehicle.speed_dkmh!=shown.vehicle.speed_dkmh ||
    state.vehicle.rpm!=shown.vehicle.rpm || state.vehicle.gear!=shown.vehicle.gear ||
    state.vehicle.brake!=shown.vehicle.brake || state.vehicle.network!=shown.vehicle.network ||
    state.body.door!=shown.body.door || state.body.lights!=shown.body.lights ||
    state.body.window!=shown.body.window || state.body.door_consistent!=shown.body.door_consistent ||
    state.body.lights_consistent!=shown.body.lights_consistent ||
    state.motor.mode!=shown.motor.mode || state.motor.sequence_ok!=shown.motor.sequence_ok ||
    state.gateway.queue_usage!=shown.gateway.queue_usage || state.gateway.sequence_ok!=shown.gateway.sequence_ok ||
    state.fault.time.received_ms!=shown.fault.time.received_ms || state.fault.gap_seen!=shown.fault.gap_seen;
  if (!changed) return;
  if (v==CLUSTER_FRESH && state.vehicle.speed_dkmh<=2500)
    lv_label_set_text_fmt(speed_label,"%u.%u",state.vehicle.speed_dkmh/10,state.vehicle.speed_dkmh%10);
  else lv_label_set_text(speed_label,"--");
  if (v==CLUSTER_FRESH && state.vehicle.rpm<=12000)
    lv_label_set_text_fmt(rpm_label,"RPM: %u",state.vehicle.rpm);
  else lv_label_set_text(rpm_label,"RPM: --");
  static const char *gears[]={"P","N","D","R","RES","RES","RES","INV"};
  if (v==CLUSTER_FRESH)
    lv_label_set_text_fmt(mode_label,"GEAR: %s BRAKE: %s",gears[state.vehicle.gear],state.vehicle.brake?"ON":"OFF");
  else lv_label_set_text(mode_label,"GEAR: -- BRAKE: --");
  static const char *motors[]={"OFF","READY","RUN","FAIL_SAFE"};
  lv_label_set_text_fmt(motor_label,"MOTOR: %s",m!=CLUSTER_FRESH?fresh_name(m):
    !state.motor.sequence_ok?"ALIVE GAP":motors[state.motor.mode]);
  static const char *doors[]={"CLOSED / UNLOCK","CLOSED / LOCK","OPEN / UNLOCK","OPEN / LOCK"};
  lv_label_set_text_fmt(door_label,"DOOR: %s",b!=CLUSTER_FRESH?fresh_name(b):
    (state.fault.active_nodes[2] | state.fault.active_nodes[4]) & (1U<<5)?"OFFLINE":
    state.body.door>3?"INVALID":!state.body.door_consistent?"MISMATCH":doors[state.body.door]);
  lv_label_set_text_fmt(window_label,"WINDOW: %s",b!=CLUSTER_FRESH?fresh_name(b):
    (state.fault.active_nodes[6] | state.fault.active_nodes[4]) & (1U<<7)?"OFFLINE":
    cluster_window_name(state.body.window));
  uint8_t lights=state.body.lights;
  if (b!=CLUSTER_FRESH) lv_label_set_text_fmt(lights_label,"LAMPS: %s",fresh_name(b));
  else if (lights>63) lv_label_set_text(lights_label,"LAMPS: INVALID");
  else if (!state.body.lights_consistent) lv_label_set_text(lights_label,"LAMPS: MISMATCH");
  else if (!lights) lv_label_set_text(lights_label,"LAMPS: ALL OFF");
  else lv_label_set_text_fmt(lights_label,"LAMPS:%s%s%s%s%s%s",lights&1?" H":"",lights&2?" L":"",
    lights&4?" R":"",lights&8?" HZ":"",lights&16?" REV":"",lights&32?" BRK":"");
  uint8_t node, code=cluster_major_fault(&state,&node);
  cluster_demo_active_faults=cluster_active_fault_count(&state);
  lv_label_set_text(fault_label,code?cluster_fault_name(code):
    state.fault.events_seen?"NO OBSERVED FAULT":"WAITING FOR EVENTS");
  if (code) lv_label_set_text_fmt(fault_detail_label,"%s / ACTIVE:%lu%s",cluster_node_name(node),
    (unsigned long)cluster_demo_active_faults,state.fault.gap_seen?" ?":"");
  else if (state.fault.gap_seen) lv_label_set_text(fault_detail_label,"RX GAP: TABLE UNCERTAIN");
  else if (state.fault.events_seen) lv_label_set_text_fmt(fault_detail_label,"LAST:%s %s",cluster_node_name(state.fault.last_node),
    state.fault.cleared?"CLEARED":"ACTIVE");
  else lv_label_set_text(fault_detail_label,"No startup snapshot");
  lv_obj_set_style_text_color(fault_label,lv_color_hex(code?0xFF6666:0xFFCC66),0);
  const char *system=system_value==255?"UNKNOWN":cluster_system_name(system_value);
  if (g==CLUSTER_FRESH && state.gateway.queue_usage<=100)
    lv_label_set_text_fmt(health_label,"SYSTEM: %s   QUEUE: %u%%%s",system,state.gateway.queue_usage,
      state.gateway.sequence_ok?"":" ALIVE GAP");
  else lv_label_set_text_fmt(health_label,"SYSTEM: %s   GATEWAY: %s",system,
    g==CLUSTER_FRESH?"QUEUE INVALID":fresh_name(g));
  lv_label_set_text_fmt(link_label,"RX C:%s V:%s B:%s M:%s G:%s",fresh_name(c),fresh_name(v),fresh_name(b),fresh_name(m),fresh_name(g));
  cluster_demo_health=v>b?v:b;
  if (c>cluster_demo_health) cluster_demo_health=c;
  if (m>cluster_demo_health) cluster_demo_health=m;
  if (g>cluster_demo_health) cluster_demo_health=g;
  shown=state; shown_vehicle=v; shown_body=b; shown_motor=m; shown_gateway=g;
  shown_valid=true; shown_system=system_value; shown_vcu=c;
}

bool cluster_ui_receive_frame(uint32_t id, const uint8_t *data, uint8_t dlc,
                              bool extended, bool remote, uint32_t received_ms)
{
  return cluster_receive_frame(&state,id,data,dlc,extended,remote,received_ms);
}
void cluster_ui_mark_rx_gap(void) { state.fault.gap_seen=true; }

HAL_StatusTypeDef cluster_ui_process(void)
{
  if (display_status != HAL_OK) return display_status;
  uint32_t now = HAL_GetTick();
  uint32_t elapsed = now - start_ms;
  cluster_demo_phase_ms = elapsed % CLUSTER_DEMO_CYCLE_MS;
  /* Only the data producer is simulated. Real reception can replace this block. */
  if (CLUSTER_TEST_INPUT && now - last_demo_ms >= 100U) {
    last_demo_ms = now;
    ClusterState next = state;
    if (cluster_demo_update(&next, now, elapsed)) cluster_ui_set_state(&next);
  }
  refresh_state(now);
  uint32_t second = elapsed / 1000U;
  if (second != last_second) {
    last_second = second;
    lv_label_set_text_fmt(uptime_label, "UI UPTIME: %lu s", (unsigned long)second);
  }
  lv_timer_handler();
  return display_status;
}
