// SavvyCAN Scripting Interface test sender
//
// Sends the DBC Motor_Status message (CAN ID 0x110) every 10 ms.
// Payload:
//   D0-D1: RPM = 3000 (raw 0x0BB8, little-endian)
//   D2-D3: TorqueApplied = 100.0 Nm (raw 0x03E8, little-endian)
//   D4[1:0]: MotorState = RUN (2)
//   D4[5:2]: AliveCounter = 0..15, wrapping around

var aliveCounter = 0;

function setup()
{
    host.log("Motor_Status sender started");
    host.setTickInterval(10);
}

function tick()
{
    var data = [
        0xB8, // RPM low byte: 3000 = 0x0BB8
        0x0B, // RPM high byte
        0xE8, // TorqueApplied low byte: 100.0 Nm = 0x03E8
        0x03, // TorqueApplied high byte
        ((aliveCounter << 2) | 0x02) & 0xFF, // AliveCounter + RUN state
        0x00,
        0x00,
        0x00
    ];

    can.sendFrame(0, 0x110, 8, data);

    aliveCounter = (aliveCounter + 1) & 0x0F;
}
