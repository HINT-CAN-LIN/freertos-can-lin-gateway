#include "vcu_command_codec.h"
#include "motor_app.h"
#include "cluster_state.h"
#include <assert.h>
#include <stdio.h>

static ClusterState cluster;
static uint32_t clock_ms;
static bool receive_status(const MotorCanFrame *f, void *context)
{
    (void)context;
    return cluster_receive_frame(&cluster, f->id, f->data, f->dlc,
                                 f->extended, f->remote, clock_ms);
}

int main(void)
{
    assert(cluster_state_self_test());
    MotorConfig config = {.torque_to_rpm=3, .alpha=0.1f, .decay_alpha=0.2f,
        .rpm_max=12000, .model_period_ms=10, .policy=motor_command_policy};
    MotorApp motor;
    assert(motor_app_init(&motor, &config, 0));
    vcu_app_command_t command = {.torque_request_nm=100, .gear=VCU_GEAR_D};
    MotorCanFrame f = {.id=VCU_COMMAND_CAN_ID, .dlc=VCU_COMMAND_DLC};
    for (unsigned i=0; i<40; ++i) {
        clock_ms=i*10;
        assert(vcu_command_encode(&command, i%16, f.data));
        assert(motor_app_receive(&motor, &f, clock_ms));
        assert(cluster_receive_frame(&cluster, f.id, f.data, f.dlc, false, false, clock_ms));
        motor_app_step(&motor, clock_ms, receive_status, NULL);
    }
    assert(!motor.watchdog.inhibit && motor.allowed_torque_raw==1000);
    assert(motor.command.steering_raw==0);
    assert(cluster.vcu.sequence_ok && cluster.motor.sequence_ok);
    ClusterDriveDisplay d=cluster_drive_display(&cluster, clock_ms);
    assert(d.rpm_valid && d.rpm>0 && d.rpm==motor.status.rpm);
    assert(d.gear_valid && d.gear==VCU_GEAR_D && !d.speed_valid);
    assert(!cluster.vehicle.time.valid && !cluster.gateway.time.valid);

    /* Brake, timeout and the status path remain active without a Gateway. */
    command.brake=true;
    clock_ms=400;
    assert(vcu_command_encode(&command, 8, f.data));
    assert(motor_app_receive(&motor, &f, clock_ms));
    motor_app_step(&motor, clock_ms, receive_status, NULL);
    assert(motor.allowed_torque_raw==0);
    clock_ms=431;
    motor_app_step(&motor, clock_ms, receive_status, NULL);
    assert(motor.watchdog.inhibit && motor.watchdog.timeout);
    assert(cluster.motor.mode==MOTOR_FAIL_SAFE);
    d=cluster_drive_display(&cluster, 1500);
    assert(!d.rpm_valid && !d.gear_valid && !d.speed_valid);

    /* A fresh Gateway summary has priority; stale summary falls back. */
    uint8_t vehicle[8]={100,0,200,0,1,0,0,0};
    assert(cluster_receive_frame(&cluster,0x120,vehicle,8,false,false,500));
    d=cluster_drive_display(&cluster,500);
    assert(d.speed_valid && d.speed_dkmh==100 && d.rpm==200 && d.gear==1);
    f.data[2]=2;
    assert(cluster_receive_frame(&cluster,0x100,f.data,8,false,false,1500));
    d=cluster_drive_display(&cluster,1500);
    assert(!d.speed_valid && d.gear_valid && d.gear==2 && !d.rpm_valid);
    f.data[2]=7;
    assert(cluster_receive_frame(&cluster,0x100,f.data,8,false,false,1510));
    assert(!cluster_drive_display(&cluster,1510).gear_valid);
    assert(!cluster_receive_frame(&cluster,0x100,f.data,7,false,false,1520));
    assert(!cluster_receive_frame(&cluster,0x100,f.data,8,true,false,1520));
    assert(!cluster_receive_frame(&cluster,0x100,f.data,8,false,true,1520));
    puts("Three-ECU CAN integration: PASS");
    return 0;
}
