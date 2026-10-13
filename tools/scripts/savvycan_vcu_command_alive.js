// SavvyCAN Scripting Interface test sender
//
// Sends the DBC VCU_Command message (CAN ID 0x100) every 10 ms.
// Payload:
//   D0-D1: TorqueRequest = 100.0 Nm (raw 0x03E8, little-endian)
//   D2[1:0]: Gear = D (2)
//   D2[2]:   Brake = OFF (0)
//   D2[7:4]: AliveCounter = 0..15, wrapping around

var aliveCounter = 0;

function setup()
{
    host.log("VCU_Command sender started");
    host.setTickInterval(10);
}

function tick()
{
    var data = [
        0xE8, // TorqueRequest low byte
        0x03, // TorqueRequest high byte
        ((aliveCounter << 4) | 0x02) & 0xFF, // AliveCounter + Gear D
        0x00,
        0x00,
        0x00,
        0x00,
        0x00
    ];

    can.sendFrame(0, 0x100, 8, data);

    aliveCounter = (aliveCounter + 1) & 0x0F;
}
