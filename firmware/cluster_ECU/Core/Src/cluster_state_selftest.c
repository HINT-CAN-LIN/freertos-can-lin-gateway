#include "cluster_state.h"
#include <string.h>

#define CHECK(x) do { if (!(x)) return false; } while (0)
bool cluster_state_self_test(void)
{
  ClusterState s = {0};
  uint8_t vcu[8]={0xD2,0x04,0xFA,0,0,0,0,0};
  CHECK(cluster_receive_frame(&s,0x100,vcu,8,false,false,1));
  CHECK(s.vcu.torque_request_dnm==1234 && s.vcu.torque_valid &&
    s.vcu.gear==2 && s.vcu.brake==1 && s.vcu.alive==15 && s.vcu.sequence_ok);
  vcu[2]=0x02;
  CHECK(cluster_receive_frame(&s,0x100,vcu,8,false,false,11) && s.vcu.sequence_ok);
  vcu[0]=0x40; vcu[1]=0x9C;
  CHECK(cluster_receive_frame(&s,0x100,vcu,8,false,false,21) && s.vcu.torque_valid);
  vcu[0]=0x41;
  CHECK(cluster_receive_frame(&s,0x100,vcu,8,false,false,31) && !s.vcu.torque_valid);
  vcu[0]=255; vcu[1]=255;
  CHECK(cluster_receive_frame(&s,0x100,vcu,8,false,false,41) && !s.vcu.torque_valid);
  CHECK(!cluster_receive_frame(&s,0x100,vcu,7,false,false,51) && s.vcu.time.received_ms==41);
  s.rejected_frames=0;
  CHECK(strcmp(cluster_window_name(5),"FAULT")==0);
  CHECK(strcmp(cluster_window_name(6),"RESERVED")==0);
  CHECK(strcmp(cluster_window_name(7),"UNDEFINED")==0);
  CHECK(strcmp(cluster_window_name(255),"INVALID")==0);
  uint8_t d[8] = {0x7B,0,0xD2,4,0x2A,0,0,0}; /* 12.3 km/h,1234 rpm,D,brake,OFFLINE */
  CHECK(cluster_receive_frame(&s,0x120,d,8,false,false,10));
  CHECK(s.vehicle.speed_dkmh==123 && s.vehicle.rpm==1234 && s.vehicle.gear==2 &&
        s.vehicle.brake==1 && s.vehicle.network==2);
  CHECK(!cluster_receive_frame(&s,0x120,d,7,false,false,20));
  CHECK(!cluster_receive_frame(&s,0x120,d,8,true,false,20));
  CHECK(!cluster_receive_frame(&s,0x120,d,8,false,true,20));
  CHECK(s.vehicle.time.received_ms==10 && s.rejected_frames==3);
  d[0]=3; d[1]=3; d[2]=0x30; d[3]=4;
  CHECK(cluster_receive_frame(&s,0x200,d,8,false,false,20));
  CHECK(s.body.door_consistent && s.body.lights_consistent && s.body.window==4);
  d[0]=0;
  CHECK(cluster_receive_frame(&s,0x200,d,8,false,false,21));
  CHECK(!s.body.door_consistent && !s.body.lights_consistent);
  d[0]=255; d[1]=255; d[2]=255; d[3]=255;
  CHECK(cluster_receive_frame(&s,0x120,d,8,false,false,22));
  CHECK(s.vehicle.speed_dkmh==65535 && s.vehicle.rpm==65535);
  d[0]=15; d[1]=100;
  CHECK(cluster_receive_frame(&s,0x300,d,8,false,false,30) && s.gateway.sequence_ok);
  d[0]=0;
  CHECK(cluster_receive_frame(&s,0x300,d,8,false,false,130) && s.gateway.sequence_ok);
  d[0]=2;
  CHECK(cluster_receive_frame(&s,0x300,d,8,false,false,230) && !s.gateway.sequence_ok);
  d[0]=1; d[1]=0x61; /* VCU ACTIVE / FAIL_SAFE */
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,40));
  d[0]=2; d[1]=0x65; /* Door ACTIVE / simultaneous */
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,50));
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,51)); /* idempotent */
  CHECK(cluster_active_fault_count(&s)==2);
  uint8_t node;
  CHECK(cluster_major_fault(&s,&node)==1 && node==1);
  d[0]=1; d[1]=0x51; /* VCU CLEARED; Door remains; OFFLINE */
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,60));
  CHECK(cluster_active_fault_count(&s)==1 && cluster_major_fault(&s,&node)==2 && node==5);
  d[0]=0; d[1]=0x10; /* NONE cannot erase active Door fault */
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,70));
  CHECK(cluster_active_fault_count(&s)==1);
  d[0]=255;
  CHECK(!cluster_receive_frame(&s,0x310,d,8,false,false,80));
  CHECK(s.fault.time.received_ms==70 && cluster_active_fault_count(&s)==1);
  d[0]=2; d[1]=0x15;
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,90));
  CHECK(cluster_active_fault_count(&s)==0);
  d[0]=0; d[1]=0x61; /* NONE is accepted metadata, not a global reset. */
  CHECK(cluster_receive_frame(&s,0x310,d,8,false,false,100));
  CHECK(cluster_active_fault_count(&s)==0);
  d[0]=0xE0;d[1]=0x2E;d[2]=0x40;d[3]=0x9C;d[4]=3;
  CHECK(cluster_receive_frame(&s,0x110,d,8,false,false,101));
  CHECK(s.motor.rpm_valid && s.motor.torque_valid);
  d[0]=0xE1;d[2]=0x41;
  CHECK(cluster_receive_frame(&s,0x110,d,8,false,false,102));
  CHECK(!s.motor.rpm_valid && !s.motor.torque_valid);
  ClusterSampleTime t={UINT32_MAX-20,true};
  CHECK(cluster_sample_freshness(t,21)==CLUSTER_FRESH);
  CHECK(cluster_sample_freshness(t,979)==CLUSTER_STALE);
  CHECK(cluster_sample_freshness(t,2979)==CLUSTER_OFFLINE);
  t.valid=false; CHECK(cluster_sample_freshness(t,0)==CLUSTER_OFFLINE);
  memset(&s,0,sizeof(s));
  CHECK(cluster_demo_update(&s,100,13000) && cluster_active_fault_count(&s)==2);
  CHECK(cluster_demo_update(&s,200,15500) && cluster_active_fault_count(&s)==1);
  CHECK(cluster_demo_update(&s,300,16500) && cluster_active_fault_count(&s)==0);
  CHECK(!cluster_demo_update(&s,400,20000));
  return true;
}
