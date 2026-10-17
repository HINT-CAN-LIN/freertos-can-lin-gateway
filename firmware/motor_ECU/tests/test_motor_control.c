#include "motor_app.h"
#include <assert.h>
#include <stdio.h>

static MotorCanFrame sent;
static unsigned sent_count;
static bool accept_tx = true;
static bool capture(const MotorCanFrame *f, void *ctx)
{
    (void)ctx;
    sent = *f;
    ++sent_count;
    return accept_tx;
}
static MotorConfig config(bool bench)
{
    return (MotorConfig){ .torque_to_rpm = 3, .alpha = 0.1f,
        .decay_alpha = 0.2f, .rpm_max = 12000, .model_period_ms = 10,
        .policy = motor_command_policy, .bench_allow_repeated_alive = bench };
}
static MotorCanFrame command(uint16_t raw, uint8_t gear, bool brake, uint8_t alive)
{
    MotorCanFrame f = { .id = 0x100, .dlc = 8 };
    f.data[0] = raw & 255;
    f.data[1] = raw >> 8;
    f.data[2] = gear | (brake ? 8 : 0) | (alive << 4);
    return f;
}
static void receive(MotorApp *a, uint32_t now, uint16_t raw,
                    uint8_t gear, bool brake, uint8_t alive)
{
    MotorCanFrame f = command(raw, gear, brake, alive);
    assert(motor_app_receive(a, &f, now));
    motor_app_step(a, now, capture, NULL);
}
static void ready(MotorApp *a, bool bench, uint32_t start, uint16_t raw)
{
    MotorConfig c = config(bench);
    assert(motor_app_init(a, &c, start));
    for (unsigned i = 0; i < 4; ++i)
        receive(a, start + i * 10, raw, 2, false, bench ? 0 : (14 + i) & 15);
    assert(!a->watchdog.inhibit);
}
static void test_dbc(void)
{
    /* DBC Intel 0.1 Nm; Gear 16|3, Brake 19|1, Alive 20|4. */
    MotorCanFrame f = { .id = 0x100, .dlc = 8,
        .data = { 0xA0, 0x0F, 0xAB, 0, 0, 0, 0, 0 } };
    MotorVcuCommand c;
    assert(motor_can_decode_vcu(&f, &c));
    assert(c.torque_raw == 4000 && c.gear == 3 && c.brake == 1 && c.alive == 10);
    f.id = 0x101; assert(!motor_can_decode_vcu(&f, &c));
    f.id = 0x100; f.dlc = 3; assert(!motor_can_decode_vcu(&f, &c));
    f.dlc = 8; f.extended = true; assert(!motor_can_decode_vcu(&f, &c));
    f.extended = false; f.remote = true; assert(!motor_can_decode_vcu(&f, &c));
    MotorStatus status = { .rpm = 1200, .torque_raw = 4000,
        .state = MOTOR_RUN, .alive = 15 };
    assert(motor_can_encode_status(&status, &f));
    assert(f.id == 0x110 && f.dlc == 8 && !f.extended && !f.remote);
    assert(f.data[0] == 0xB0 && f.data[1] == 4 &&
           f.data[2] == 0xA0 && f.data[3] == 0x0F && f.data[4] == 0x3E);
    assert(f.data[5] == 0 && f.data[6] == 0 && f.data[7] == 0);
}
static void test_steering_request(void)
{
    MotorApp a;
    MotorVcuCommand c;
    MotorCanFrame f = command(4000, 2, false, 0);
    f.data[4] = 0x38; f.data[5] = 0xFF; /* -20 degrees */
    assert(motor_can_decode_vcu(&f, &c) && c.steering_raw == -200);
    /* Every Body Byte3 pattern must leave steering and drive bits unchanged. */
    for (unsigned body = 0; body < 256; ++body) {
        f.data[3] = (uint8_t)body;
        assert(motor_can_decode_vcu(&f, &c) && c.steering_raw == -200);
        assert(c.torque_raw == 4000 && c.gear == 2 && c.brake == 0);
    }
    f.data[3] = 0;
    ready(&a, true, 0, 4000);
    assert(motor_app_receive(&a, &f, 40));
    motor_app_step(&a, 40, capture, NULL);
    assert(a.steering_target_raw == -200 && a.status.torque_raw == 4000);
    assert(a.status.steering_raw == -200 && a.status.firmware_revision == 4);
    assert(a.status.fault_flags == 0);
    MotorCanFrame echo;
    assert(motor_can_encode_status(&a.status, &echo));
    assert(echo.data[5] == 0x38 && echo.data[6] == 0xFF && echo.data[7] == 0x40);
    f.data[4] = 0xC2; f.data[5] = 1; /* +45 degrees */
    assert(motor_app_receive(&a, &f, 50));
    motor_app_step(&a, 50, capture, NULL);
    assert(a.steering_target_raw == 450);
    motor_app_step(&a, 81, capture, NULL);
    assert(a.steering_target_raw == 0 && a.watchdog.inhibit);
    assert(a.status.fault_flags & MOTOR_FAULT_TIMEOUT);
    ready(&a, true, 100, 4000);
    f.data[4] = 0xFF; f.data[5] = 0x7F; /* INVALID */
    assert(motor_app_receive(&a, &f, 140));
    motor_app_step(&a, 140, capture, NULL);
    assert(a.watchdog.invalid_input && a.status.torque_raw == 0 && a.steering_target_raw == 0);
    assert(a.status.fault_flags & MOTOR_FAULT_INVALID);
}
static void test_servo_mapping(void)
{
    assert(motor_servo_pulse_us(0, 1500, false) == 1500);
    assert(motor_servo_pulse_us(-450, 1500, false) == 1250);
    assert(motor_servo_pulse_us(450, 1500, false) == 1750);
    assert(motor_servo_pulse_us(-200, 1500, false) == 1389);
    assert(motor_servo_pulse_us(200, 1500, false) == 1611);
    assert(motor_servo_pulse_us(-200, 1500, true) == 1611);
    assert(motor_servo_pulse_us(INT16_MIN, 1500, false) == 1250);
    assert(motor_servo_pulse_us(INT16_MAX, 1500, false) == 1750);
    MotorApp a;
    MotorDrive d;
    ready(&a, true, 0, 0);
    MotorCanFrame f = command(0, 0, false, 0);
    f.data[4] = 200;
    motor_app_receive(&a, &f, 40);
    motor_app_step(&a, 40, capture, NULL);
    motor_drive_init(&d, 0);
    motor_drive_step(&d, &a, 40);
    assert(d.duty == 0 && a.steering_target_raw == 200); /* P does not block bench steering */
    motor_app_step(&a, 71, capture, NULL);
    assert(a.steering_target_raw == 0);
    assert(motor_servo_pulse_us(a.steering_target_raw, 1500, false) == 1500);
}
static void test_bench_and_stops(void)
{
    MotorApp a;
    MotorDrive d;
    ready(&a, true, 0, 4000);
    motor_drive_init(&d, 0);
    motor_drive_step(&d, &a, 30);
    assert(a.target_rpm == 1200 && a.status.torque_raw == 4000);
    assert(d.direction == 1 && d.duty == 420);
    receive(&a, 40, 40000, 2, false, 0);
    motor_drive_step(&d, &a, 40);
    assert(d.duty == 4200);
    receive(&a, 50, 4000, 2, true, 0);
    motor_drive_step(&d, &a, 50);
    assert(d.duty == 0 && a.status.torque_raw == 0);
    receive(&a, 60, 4000, 0, false, 0);
    motor_drive_step(&d, &a, 60); assert(d.duty == 0);
    receive(&a, 70, 4000, 1, false, 0);
    motor_drive_step(&d, &a, 70); assert(d.duty == 0);
    receive(&a, 80, 4000, 2, false, 0);
    motor_drive_step(&d, &a, 80); assert(d.duty == 420);
    motor_app_step(&a, 110, capture, NULL);
    motor_drive_step(&d, &a, 110); assert(d.duty == 420); /* age == 30 */
    float before = a.rpm;
    motor_app_step(&a, 111, capture, NULL);
    motor_drive_step(&d, &a, 111);
    assert(d.duty == 0 && a.target_rpm == 0 && a.status.torque_raw == 0);
    assert(a.status.state == MOTOR_FAIL_SAFE && a.rpm < before);
    /* A queued old frame cannot make the present-day command fresh. */
    MotorCanFrame old = command(4000, 2, false, 0);
    assert(motor_app_receive(&a, &old, 90));
    motor_app_step(&a, 150, capture, NULL);
    motor_drive_step(&d, &a, 150); assert(d.duty == 0);
}
static void test_invalid_and_strict_alive(void)
{
    MotorApp a;
    MotorDrive d;
    ready(&a, false, 0, 4000); /* includes 15 -> 0 wrap */
    receive(&a, 40, 4000, 2, false, 1); /* duplicate */
    assert(a.watchdog.alive_error && a.watchdog.inhibit);
    receive(&a, 50, 4000, 2, false, 2);
    receive(&a, 60, 4000, 2, false, 3);
    assert(a.watchdog.inhibit);
    receive(&a, 70, 4000, 2, false, 4);
    assert(!a.watchdog.inhibit);
    receive(&a, 80, 0xFFFF, 2, false, 5);
    assert(a.watchdog.invalid_input && a.status.torque_raw == 0);
    motor_drive_init(&d, 0); motor_drive_step(&d, &a, 80); assert(d.duty == 0);
    ready(&a, true, 100, 4000);
    receive(&a, 140, 40001, 2, false, 0); assert(a.watchdog.inhibit);
    for (uint8_t gear = 4; gear <= 7; ++gear) {
        ready(&a, true, 200, 4000);
        receive(&a, 240, 4000, gear, false, 0);
        assert(a.watchdog.invalid_input && a.target_rpm == 0);
    }
}
static void test_reversal_and_rollover(void)
{
    MotorApp a;
    MotorDrive d;
    ready(&a, true, 0, 4000); motor_drive_init(&d, 0);
    motor_drive_step(&d, &a, 30); assert(d.direction == 1);
    receive(&a, 40, 4000, 3, false, 0);
    motor_drive_step(&d, &a, 40); assert(d.duty == 0);
    for (uint32_t t = 50; t <= 230; t += 10) {
        receive(&a, t, 4000, 3, false, 0);
        motor_drive_step(&d, &a, t); assert(d.duty == 0);
    }
    receive(&a, 240, 4000, 3, false, 0);
    motor_drive_step(&d, &a, 240); assert(d.direction == -1 && d.duty == 420);
    receive(&a, 250, 4000, 1, false, 0);
    motor_drive_step(&d, &a, 250); assert(d.duty == 0);
    receive(&a, 260, 4000, 2, false, 0);
    motor_drive_step(&d, &a, 260); assert(d.duty == 0); /* N cannot bypass guard */
    ready(&a, true, UINT32_MAX - 40, 4000);
    motor_app_step(&a, 20, capture, NULL); /* 31 ms across wrap */
    assert(a.watchdog.timeout);
}
static void test_tx_timing(void)
{
    MotorApp a;
    MotorConfig c = config(true);
    motor_app_init(&a, &c, 0);
    sent_count = 0;
    motor_app_step(&a, 9, capture, NULL); assert(sent_count == 0);
    motor_app_step(&a, 10, capture, NULL); assert(sent_count == 1 && sent.data[4] == 0);
    motor_app_step(&a, 20, capture, NULL); assert(sent_count == 2 && sent.data[4] == 4);
    accept_tx = false;
    motor_app_step(&a, 30, capture, NULL); assert(a.status.alive == 2);
    accept_tx = true;
    motor_app_step(&a, 100, capture, NULL); assert(sent_count == 4 && a.status.alive == 3);
}
int main(void)
{
    test_steering_request();
    test_servo_mapping();
    test_dbc(); test_bench_and_stops(); test_invalid_and_strict_alive();
    test_reversal_and_rollover(); test_tx_timing();
    puts("PASS: DBC encoding, drive/brake/P/N, timeout, invalid inputs, strict/bench Alive, reversal guard, tick wrap and TX cadence");
    return 0;
}
