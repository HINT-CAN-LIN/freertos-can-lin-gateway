#include "cluster_ui.h"
#include "cluster_can.h"
#include "st7796.h"
#include "lvgl/lvgl.h"
#include "cmsis_os.h"
#include <string.h>

/* 19,200 bytes, rather than a 307,200-byte full framebuffer. */
static uint32_t draw_buffer[480 * 20 * 2 / sizeof(uint32_t)];
static volatile HAL_StatusTypeDef display_status = HAL_OK;
static lv_obj_t *speed_label, *mode_label, *rpm_label;
static lv_obj_t *body_icons[3];
typedef struct {
  lv_obj_t *arc, *needle;
  lv_point_precise_t points[2];
  int32_t value, target;
} ClusterGauge;
static ClusterGauge rpm_gauge, speed_gauge;
static lv_obj_t *warning_badge, *fault_detail_label, *active_fault_label;
static ClusterState state; /* UI-owned rendering snapshot. */
static ClusterState input_state; /* Producer-owned, mutex-protected. */
static osMutexId_t state_mutex;
volatile bool cluster_snapshot_test_passed;
static bool copy_input(ClusterState *snapshot)
{
  if (osMutexAcquire(state_mutex, osWaitForever) != osOK) return false;
  *snapshot=input_state;
  osMutexRelease(state_mutex);
  return true;
}
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

static int32_t gauge_angle(int32_t value)
{
  return 135 + value * 270 / 1000;
}

static lv_point_precise_t dial_point(int32_t angle, int radius)
{
  lv_point_precise_t p = {
    104 + lv_trigo_cos(angle % 360) * radius / LV_TRIGO_SIN_MAX,
    104 + lv_trigo_sin(angle % 360) * radius / LV_TRIGO_SIN_MAX
  };
  return p;
}

static void gauge_position(void *var, int32_t value)
{
  ClusterGauge *g = var;
  g->value = value;
  g->points[0] = dial_point(gauge_angle(value), 64);
  g->points[1] = dial_point(gauge_angle(value), 96);
  lv_line_set_points(g->needle, g->points, 2);
  lv_obj_invalidate(g->needle);
  lv_arc_set_value(g->arc, value);
}

static int32_t gauge_value(uint16_t raw, uint16_t maximum, bool valid)
{
  if (!valid) return 0;
  return raw>=maximum ? 1000 : (int32_t)raw * 1000 / maximum;
}

static void gauge_target(ClusterGauge *g, uint16_t raw, uint16_t maximum, bool valid)
{
  int32_t target = gauge_value(raw, maximum, valid);
  lv_obj_set_style_line_color(g->needle, lv_color_hex(valid ? 0xF4FAFF : 0x45515E), 0);
  lv_obj_set_style_arc_color(g->arc, lv_color_hex(valid ? 0x43CFFF : 0x45515E), LV_PART_INDICATOR);
  if (!valid) {
    lv_anim_delete(g, gauge_position);
    g->target = 0;
    gauge_position(g, 0);
    return;
  }
  if (target == g->target) return;
  lv_anim_delete(g, gauge_position);
  g->target = target;
  lv_anim_t animation;
  lv_anim_init(&animation);
  lv_anim_set_var(&animation, g);
  lv_anim_set_exec_cb(&animation, gauge_position);
  lv_anim_set_values(&animation, g->value, target);
  lv_anim_set_duration(&animation, 100);
  lv_anim_set_path_cb(&animation, lv_anim_path_linear);
  lv_anim_start(&animation);
}

static lv_obj_t *make_gauge(lv_obj_t *screen, ClusterGauge *g, int x,
                            unsigned maximum, const char *unit)
{
  lv_obj_t *dial = lv_obj_create(screen);
  lv_obj_remove_style_all(dial);
  lv_obj_set_pos(dial, x, 50);
  lv_obj_set_size(dial, 208, 208);
  lv_obj_set_scrollable(dial, false);
  lv_obj_set_style_bg_color(dial, lv_color_hex(0x080D14), 0);
  lv_obj_set_style_bg_opa(dial, LV_OPA_COVER, 0);
  lv_obj_set_style_radius(dial, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_border_color(dial, lv_color_hex(0x647381), 0);
  lv_obj_set_style_border_width(dial, 2, 0);
  g->arc = lv_arc_create(dial);
  lv_obj_remove_style_all(g->arc);
  lv_obj_set_size(g->arc, 198, 198);
  lv_obj_set_pos(g->arc, 5, 5);
  lv_arc_set_bg_angles(g->arc, 135, 45);
  lv_arc_set_range(g->arc, 0, 1000);
  lv_obj_set_style_arc_width(g->arc, 4, LV_PART_MAIN);
  lv_obj_set_style_arc_color(g->arc, lv_color_hex(0x283340), LV_PART_MAIN);
  lv_obj_set_style_arc_width(g->arc, 4, LV_PART_INDICATOR);
  lv_obj_set_clickable(g->arc, false);
  unsigned divisions = maximum==250 ? 5 : 6;
  for (unsigned i = 0; i <= divisions; ++i) {
    lv_point_precise_t point = dial_point(gauge_angle(i * 1000 / divisions), 82);
    lv_obj_t *tick = label(dial, "", (int)point.x - 18, (int)point.y - 7,
                          &lv_font_montserrat_14, 0xBAC6D3);
    lv_obj_set_width(tick, 36);
    lv_obj_set_style_text_align(tick, LV_TEXT_ALIGN_CENTER, 0);
    lv_label_set_text_fmt(tick, "%u", maximum * i / divisions);
  }
  if (maximum==12) label(dial, "x1000", 78, 51, &lv_font_montserrat_14, 0x8B9CAB);
  g->needle = lv_line_create(dial);
  lv_obj_set_pos(g->needle, 0, 0);
  lv_obj_set_style_line_width(g->needle, 3, 0);
  lv_obj_set_style_line_rounded(g->needle, true, 0);
  gauge_position(g, 0);
  lv_obj_t *value = label(dial, "--", 32, 86, &lv_font_montserrat_32, 0xFFFFFF);
  lv_obj_set_width(value, 144);
  lv_obj_set_style_text_align(value, LV_TEXT_ALIGN_CENTER, 0);
  lv_obj_t *units = label(dial, unit, 58, 127, &lv_font_montserrat_14, 0x8B9CAB);
  lv_obj_set_width(units, 92);
  lv_obj_set_style_text_align(units, LV_TEXT_ALIGN_CENTER, 0);
  return value;
}

static void make_body_icon(lv_obj_t *screen, unsigned index, int x,
                           const lv_point_precise_t *points, unsigned count)
{
  body_icons[index] = lv_obj_create(screen);
  lv_obj_remove_style_all(body_icons[index]);
  lv_obj_set_pos(body_icons[index], x, 16);
  lv_obj_set_size(body_icons[index], 48, 26);
  lv_obj_set_scrollable(body_icons[index], false);
  lv_obj_t *line = lv_line_create(body_icons[index]);
  lv_obj_set_pos(line, 7, 0);
  lv_line_set_points(line, points, count);
  lv_obj_set_style_line_width(line, 2, 0);
  if (index==2) {
    static const lv_point_precise_t rays[3][2] = {
      {{22,3},{32,3}}, {{22,12},{32,12}}, {{22,22},{32,22}}
    };
    for (unsigned i=0; i<3; ++i) {
      lv_obj_t *ray = lv_line_create(body_icons[index]);
      lv_obj_set_pos(ray, 7, 0);
      lv_line_set_points(ray, rays[i], 2);
      lv_obj_set_style_line_width(ray, 2, 0);
    }
  }
}

static void body_icon_color(unsigned index, uint32_t color)
{
  for (unsigned i=0; i<lv_obj_get_child_count(body_icons[index]); ++i)
    lv_obj_set_style_line_color(lv_obj_get_child(body_icons[index], i), lv_color_hex(color), 0);
}

static void indicator_colors(const ClusterState *s, ClusterFreshness freshness, uint32_t colors[3])
{
  bool body_live = freshness==CLUSTER_FRESH;
  bool body_lost = s->body.time.valid && !body_live;
  bool door_error = body_lost || (body_live && (s->body.door>3 || !s->body.door_consistent)) ||
    ((s->fault.active_nodes[2] | s->fault.active_nodes[4]) & (1U<<5));
  bool window_error = body_lost || (body_live && s->body.window>4) ||
    ((s->fault.active_nodes[6] | s->fault.active_nodes[4]) & (1U<<7));
  bool lamp_error = body_lost || (body_live && (s->body.lights>63 || !s->body.lights_consistent)) ||
    (s->fault.active_nodes[4] & (1U<<6));
  colors[0] = door_error ? 0xFF6666 : body_live && s->body.door_open ? 0xFFCC66 : 0x34414E;
  colors[1] = window_error ? 0xFF6666 : body_live && (s->body.window==1 || s->body.window==2) ? 0x43CFFF : 0x34414E;
  colors[2] = lamp_error ? 0xFF6666 : body_live && s->body.lights ? 0x55E599 : 0x34414E;
}

static const char *dashboard_warning(const ClusterState *s, uint32_t now,
                                     const ClusterCanDiagnostics *d)
{
  if (d->initialized && d->init_status!=HAL_OK) return "CAN INIT\nERROR";
  if (d->current_errors & HAL_CAN_ERROR_BOF) return "CAN\nBUS OFF";
  if (d->current_errors & (HAL_CAN_ERROR_EPV | HAL_CAN_ERROR_EWG)) return "CAN\nERROR";
  uint8_t code = cluster_major_fault(s, NULL);
  if (code) return cluster_fault_name(code);
  if (s->fault.gap_seen || d->rx_drops) return "RX GAP";
  if (d->error_history) return "CAN ERROR\nHISTORY";
  const ClusterSampleTime times[] = {s->vehicle.time,s->vcu.time,s->motor.time,s->gateway.time,s->body.time};
  static const char *offline[] = {"VEHICLE\nOFFLINE","VCU\nOFFLINE","MOTOR\nOFFLINE","GATEWAY\nOFFLINE","BODY\nOFFLINE"};
  for (unsigned i=0; i<5; ++i)
    if (times[i].valid && cluster_sample_freshness(times[i],now)!=CLUSTER_FRESH) return offline[i];
  if (s->vehicle.time.valid && (s->vehicle.speed_dkmh>2500 || s->vehicle.rpm>12000 || s->vehicle.gear>3))
    return "VEHICLE\nDATA ERROR";
  uint8_t system = cluster_display_system(s, now);
  if (system>0 && system<4) return cluster_system_name(system);
  if (s->vcu.time.valid && !s->vcu.sequence_ok) return "VCU\nALIVE GAP";
  if (s->motor.time.valid && !s->motor.sequence_ok) return "MOTOR\nALIVE GAP";
  if (s->gateway.time.valid && !s->gateway.sequence_ok) return "GATEWAY\nALIVE GAP";
  if (s->motor.time.valid && s->motor.mode==3) return "MOTOR\nFAIL_SAFE";
  if (s->gateway.time.valid && s->gateway.queue_usage>100) return "GATEWAY\nDATA ERROR";
  if (s->body.time.valid && (s->body.door>3 || !s->body.door_consistent)) return "DOOR\nDATA ERROR";
  if (s->body.time.valid && (s->body.lights>63 || !s->body.lights_consistent)) return "LAMP\nDATA ERROR";
  if (s->body.time.valid && s->body.window>4) return "WINDOW\nERROR";
  return NULL;
}

static void warning_text(char text[64], const char *warning)
{
  const char *source = warning ? warning : "NO ACTIVE FAULT";
  unsigned i=0;
  for (; source[i] && i<63; ++i)
    text[i] = source[i]=='_' || source[i]=='\n' ? ' ' : source[i];
  text[i]='\0';
}

HAL_StatusTypeDef cluster_ui_init(void)
{
  const osMutexAttr_t attr = {.name="clusterState", .attr_bits=osMutexPrioInherit};
  state_mutex = osMutexNew(&attr);
  if (state_mutex == NULL) return HAL_ERROR;
  /* Exercise snapshot isolation before releasing the producer task. */
  ClusterState probe={0}, copied={0};
  probe.vehicle.speed_dkmh=1234;
  cluster_ui_set_state(&probe);
  probe.vehicle.speed_dkmh=0;
  cluster_snapshot_test_passed=copy_input(&copied) && copied.vehicle.speed_dkmh==1234;
  copied.vehicle.speed_dkmh=0;
  cluster_snapshot_test_passed=cluster_snapshot_test_passed &&
    copy_input(&copied) && copied.vehicle.speed_dkmh==1234;
  cluster_ui_set_state(&probe);
  if (!cluster_snapshot_test_passed) return HAL_ERROR;
  cluster_model_test_passed = cluster_state_self_test();
  if (!cluster_model_test_passed) return HAL_ERROR;
  ClusterState icon_probe = {0};
  icon_probe.body.time.valid = true;
  icon_probe.body.door_consistent = icon_probe.body.lights_consistent = true;
  uint32_t colors[3];
  indicator_colors(&icon_probe, CLUSTER_FRESH, colors);
  if (colors[0]!=0x34414E || colors[1]!=0x34414E || colors[2]!=0x34414E) return HAL_ERROR;
  icon_probe.body.door_open = 1;
  icon_probe.body.window = icon_probe.body.lights = 1;
  indicator_colors(&icon_probe, CLUSTER_FRESH, colors);
  if (colors[0]!=0xFFCC66 || colors[1]!=0x43CFFF || colors[2]!=0x55E599) return HAL_ERROR;
  indicator_colors(&icon_probe, CLUSTER_STALE, colors);
  if (colors[0]!=0xFF6666 || colors[1]!=0xFF6666 || colors[2]!=0xFF6666) return HAL_ERROR;
  char text_probe[64];
  warning_text(text_probe, "CAN\nBUS_OFF");
  if (strcmp(text_probe, "CAN BUS OFF")) return HAL_ERROR;
  ClusterState warning_probe = {0};
  ClusterCanDiagnostics warning_diagnostics = {.initialized=true, .live=true, .init_status=HAL_OK};
  if (dashboard_warning(&warning_probe, 0, &warning_diagnostics)!=NULL) return HAL_ERROR;
  warning_probe.fault.gap_seen=true;
  if (strcmp(dashboard_warning(&warning_probe, 0, &warning_diagnostics), "RX GAP")) return HAL_ERROR;
  warning_probe.fault.active_nodes[1]=1U<<1;
  if (strcmp(dashboard_warning(&warning_probe, 0, &warning_diagnostics), "VCU_TIMEOUT")) return HAL_ERROR;
  warning_diagnostics.current_errors=HAL_CAN_ERROR_BOF;
  if (strcmp(dashboard_warning(&warning_probe, 0, &warning_diagnostics), "CAN\nBUS OFF")) return HAL_ERROR;
  display_status = st7796_init();
  if (display_status != HAL_OK) return display_status;
  lv_init();
  lv_tick_set_cb(HAL_GetTick);
  lv_display_t *display = lv_display_create(480, 320);
  if (display == NULL) return HAL_ERROR;
  lv_display_set_color_format(display, LV_COLOR_FORMAT_RGB565);
  lv_display_set_buffers(display, draw_buffer, NULL, sizeof(draw_buffer), LV_DISPLAY_RENDER_MODE_PARTIAL);
  lv_display_set_flush_cb(display, flush);
  /* Check the linear dial endpoints before creating the screen. */
  if (gauge_angle(0) != 135 || gauge_angle(500) != 270 || gauge_angle(1000) != 405)
    return HAL_ERROR;
  if (gauge_value(6000,12000,true)!=500 || gauge_value(12000,12000,true)!=1000 ||
      gauge_value(65535,12000,true)!=1000 || gauge_value(6000,12000,false)!=0)
    return HAL_ERROR;
  lv_obj_t *screen = lv_screen_active();
  lv_obj_set_style_bg_color(screen, lv_color_hex(0x080D14), 0);
  lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, 0);
  lv_obj_set_scrollable(screen, false);
  static const lv_point_precise_t door[] = {{7,24},{7,5},{22,1},{27,24},{7,24},{22,20},{22,1}};
  static const lv_point_precise_t window[] = {{2,22},{2,3},{30,3},{30,22},{2,22},{2,13},{30,13}};
  static const lv_point_precise_t lamp[] = {{14,3},{3,6},{3,19},{14,22},{14,3}};
  make_body_icon(screen, 0, 160, door, sizeof(door)/sizeof(door[0]));
  make_body_icon(screen, 1, 216, window, sizeof(window)/sizeof(window[0]));
  make_body_icon(screen, 2, 272, lamp, sizeof(lamp)/sizeof(lamp[0]));
  for (unsigned i=0; i<3; ++i) body_icon_color(i, 0x34414E);
  rpm_label = make_gauge(screen, &rpm_gauge, 8, 12, "rpm");
  speed_label = make_gauge(screen, &speed_gauge, 264, 250, "km/h");
  warning_badge = lv_obj_create(screen);
  lv_obj_remove_style_all(warning_badge);
  lv_obj_set_pos(warning_badge, 220, 54);
  lv_obj_set_size(warning_badge, 40, 40);
  lv_obj_set_scrollable(warning_badge, false);
  lv_obj_set_style_bg_color(warning_badge, lv_color_hex(0x301C24), 0);
  lv_obj_set_style_bg_opa(warning_badge, LV_OPA_50, 0);
  lv_obj_set_style_radius(warning_badge, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_border_width(warning_badge, 2, 0);
  lv_obj_set_style_border_color(warning_badge, lv_color_hex(0xD97575), 0);
  lv_obj_t *mark = label(warning_badge, "!", 0, 0, &lv_font_montserrat_32, 0xF0A0A0);
  lv_obj_align(mark, LV_ALIGN_CENTER, 0, 0);
  lv_obj_set_hidden(warning_badge, true);
  fault_detail_label = label(screen, "", 252, 282, &lv_font_montserrat_14, 0x8B9CAB);
  lv_obj_set_width(fault_detail_label, 216);
  lv_label_set_long_mode(fault_detail_label, LV_LABEL_LONG_WRAP);
  lv_obj_set_style_text_align(fault_detail_label, LV_TEXT_ALIGN_RIGHT, 0);
  lv_obj_t *gear_box = lv_obj_create(screen);
  lv_obj_remove_style_all(gear_box);
  lv_obj_set_pos(gear_box, 202, 230);
  lv_obj_set_size(gear_box, 76, 48);
  lv_obj_set_scrollable(gear_box, false);
  lv_obj_set_style_bg_color(gear_box, lv_color_hex(0x172330), 0);
  lv_obj_set_style_bg_opa(gear_box, LV_OPA_50, 0);
  lv_obj_set_style_border_color(gear_box, lv_color_hex(0x506477), 0);
  lv_obj_set_style_border_opa(gear_box, LV_OPA_40, 0);
  lv_obj_set_style_border_width(gear_box, 1, 0);
  lv_obj_set_style_radius(gear_box, 8, 0);
  mode_label = label(gear_box, "--", 2, 4, &lv_font_montserrat_32, 0x64D9FF);
  lv_obj_set_width(mode_label, 72);
  lv_obj_set_style_text_align(mode_label, LV_TEXT_ALIGN_CENTER, 0);
  active_fault_label = label(screen, "Active: 0", 12, 294, &lv_font_montserrat_14, 0x8B9CAB);
  /* Finish the expensive first full-screen paint before live CAN starts. */
  lv_refr_now(display);
  start_ms = HAL_GetTick();
  last_demo_ms = start_ms - 200U;
  return display_status; /* The first LVGL flush can also fail. */
}

void cluster_ui_set_state(const ClusterState *next)
{
  if (next != NULL && osMutexAcquire(state_mutex, osWaitForever) == osOK) {
    input_state = *next;
    osMutexRelease(state_mutex);
  }
}

static void refresh_state(uint32_t now)
{
  ClusterFreshness c=cluster_sample_freshness(state.vcu.time,now);
  ClusterFreshness v=cluster_sample_freshness(state.vehicle.time,now);
  ClusterFreshness b=cluster_sample_freshness(state.body.time,now);
  ClusterFreshness m=cluster_sample_freshness(state.motor.time,now);
  ClusterFreshness g=cluster_sample_freshness(state.gateway.time,now);
  if (state.gateway.time.valid && g!=CLUSTER_FRESH) state.fault.gap_seen=true;
  uint8_t system_value=cluster_display_system(&state,now);
  bool changed=c!=shown_vcu || system_value!=shown_system || !shown_valid || v!=shown_vehicle || b!=shown_body || m!=shown_motor || g!=shown_gateway;
  /* Compare values, not receive timestamps, to avoid redrawing unchanged labels. */
  changed=changed || state.vehicle.speed_dkmh!=shown.vehicle.speed_dkmh ||
    state.vehicle.rpm!=shown.vehicle.rpm || state.vehicle.gear!=shown.vehicle.gear ||
    state.vehicle.brake!=shown.vehicle.brake || state.vehicle.network!=shown.vehicle.network ||
    state.body.door!=shown.body.door || state.body.lights!=shown.body.lights ||
    state.body.window!=shown.body.window || state.body.door_consistent!=shown.body.door_consistent ||
    state.body.lights_consistent!=shown.body.lights_consistent ||
    state.vcu.sequence_ok!=shown.vcu.sequence_ok || state.vcu.gear!=shown.vcu.gear ||
    state.motor.rpm!=shown.motor.rpm || state.motor.rpm_valid!=shown.motor.rpm_valid ||
    state.motor.mode!=shown.motor.mode || state.motor.sequence_ok!=shown.motor.sequence_ok ||
    state.gateway.queue_usage!=shown.gateway.queue_usage || state.gateway.sequence_ok!=shown.gateway.sequence_ok ||
    state.fault.time.received_ms!=shown.fault.time.received_ms ||
    cluster_fault_display_changed(&state.fault,&shown.fault);
  if (!changed) return;
  ClusterDriveDisplay drive = cluster_drive_display(&state, now);
  gauge_target(&speed_gauge, drive.speed_dkmh, 2500, drive.speed_valid);
  gauge_target(&rpm_gauge, drive.rpm, 12000, drive.rpm_valid);
  if (drive.speed_valid)
    lv_label_set_text_fmt(speed_label,"%u.%u",drive.speed_dkmh/10,drive.speed_dkmh%10);
  else lv_label_set_text(speed_label,"--");
  if (drive.rpm_valid) lv_label_set_text_fmt(rpm_label,"%u",drive.rpm);
  else lv_label_set_text(rpm_label,"--");
  static const char *gears[]={"P","N","D","R","RES","RES","RES","INV"};
  lv_label_set_text(mode_label, drive.gear_valid ? gears[drive.gear] : "--");
  uint32_t colors[3];
  indicator_colors(&state, b, colors);
  for (unsigned i=0; i<3; ++i) body_icon_color(i, colors[i]);
  cluster_demo_active_faults=cluster_active_fault_count(&state);
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
  if (osMutexAcquire(state_mutex, osWaitForever) != osOK) return false;
  bool accepted = cluster_receive_frame(&input_state,id,data,dlc,extended,remote,received_ms);
  osMutexRelease(state_mutex);
  return accepted;
}
void cluster_ui_mark_rx_gap(void)
{
  if (osMutexAcquire(state_mutex, osWaitForever) == osOK) {
    input_state.fault.gap_seen=true;
    osMutexRelease(state_mutex);
  }
}

/* CAN task owns test input and freshness bookkeeping, never LVGL. */
void cluster_ui_update_input(void)
{
  if (osMutexAcquire(state_mutex, osWaitForever) != osOK) return;
  uint32_t now=HAL_GetTick();
  if (CLUSTER_TEST_INPUT && !CLUSTER_CAN_LOOPBACK && now-last_demo_ms >= 100U) {
    last_demo_ms=now;
    cluster_demo_update(&input_state,now,now-start_ms);
  }
  if (input_state.gateway.time.valid &&
      cluster_sample_freshness(input_state.gateway.time,now)!=CLUSTER_FRESH)
    input_state.fault.gap_seen=true;
  osMutexRelease(state_mutex);
}

HAL_StatusTypeDef cluster_ui_process(void)
{
  if (display_status != HAL_OK) return display_status;
  if (!copy_input(&state)) return HAL_ERROR;
  /* A producer may preempt us during copy_input: acquire now AFTER snapshot. */
  uint32_t now = HAL_GetTick();
  uint32_t elapsed = now - start_ms;
  cluster_demo_phase_ms = elapsed % CLUSTER_DEMO_CYCLE_MS;
  /* No state lock is held during LVGL rendering or blocking SPI. */
  refresh_state(now);
  ClusterCanDiagnostics diagnostics;
  cluster_can_get_diagnostics(&diagnostics);
  const char *warning = dashboard_warning(&state, now, &diagnostics);
  static uint32_t last_diagnostic_second = UINT32_MAX;
  static const char *shown_warning;
  static uint8_t shown_active, shown_node;
  static bool shown_uncertain;
  uint8_t node, code = cluster_major_fault(&state, &node);
  uint8_t active = cluster_active_fault_count(&state);
  bool uncertain = state.fault.gap_seen || diagnostics.rx_drops!=0;
  uint32_t second = elapsed / 1000U;
  if (warning!=shown_warning || uncertain!=shown_uncertain || active!=shown_active ||
      node!=shown_node || second!=last_diagnostic_second) {
    char text[64];
    warning_text(text, warning);
    lv_obj_set_hidden(warning_badge, warning==NULL);
    lv_label_set_text_fmt(active_fault_label, "Active: %u%s", active, uncertain ? " ?" : "");
    lv_obj_set_style_text_color(active_fault_label, lv_color_hex(active ? 0xFFCC66 : 0x8B9CAB), 0);
    if (code)
      lv_label_set_text_fmt(fault_detail_label,"%s%s\n%s",
        text, uncertain ? " / RX GAP" : "", cluster_node_name(node));
    else lv_label_set_text(fault_detail_label, warning ? text : "");
    shown_warning=warning; shown_uncertain=uncertain; shown_active=active; shown_node=node;
    last_diagnostic_second=second;
  }
  lv_timer_handler();
  return display_status;
}
