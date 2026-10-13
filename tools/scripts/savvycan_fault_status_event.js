// SavvyCAN Scripting Interface test sender
//
// Sends two DBC Fault_Status event frames on CAN ID 0x310:
//   1) ACTIVE  : VCU_TIMEOUT, VCU offline, system DEGRADED
//   2) CLEARED : the same fault cleared, after 1 second
//
// Payload byte 0: FaultCode = VCU_TIMEOUT (1)
// Payload byte 1:
//   bits 0..3: ECUOffline = VCU (1)
//   bit  4:    RecoveryState = ACTIVE (0) / CLEARED (1)
//   bits 5..6: SystemState = DEGRADED (1)

var tickCount = 0;

function setup()
{
    host.log("Fault_Status event test started");
    host.setTickInterval(100);
}

function tick()
{
    if (tickCount == 0)
    {
        can.sendFrame(0, 0x310, 8, [
            0x01, // FaultCode: VCU_TIMEOUT
            0x21, // ECUOffline=VCU, Recovery=ACTIVE, System=DEGRADED
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00
        ]);

        host.log("FAULT_STATUS ACTIVE sent");
    }
    else if (tickCount == 10)
    {
        can.sendFrame(0, 0x310, 8, [
            0x01, // FaultCode: VCU_TIMEOUT
            0x31, // ECUOffline=VCU, Recovery=CLEARED, System=DEGRADED
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00
        ]);

        host.log("FAULT_STATUS CLEARED sent");
        host.setTickInterval(0);
    }

    tickCount = tickCount + 1;
}
