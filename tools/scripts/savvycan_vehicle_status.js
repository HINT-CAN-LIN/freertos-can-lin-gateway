// SavvyCAN Scripting Interface test sender
//
// Sends the DBC Vehicle_Status message (CAN ID 0x120) every 20 ms.
// Payload:
//   D0-D1: Speed = 50.0 km/h (raw 500 = 0x01F4, little-endian)
//   D2-D3: RPM = 3000 (raw 0x0BB8, little-endian)
//   D4[2:0]: Gear = D (2)
//   D4[3]:   Brake = OFF (0)
//   D4[5:4]: NetworkState = NORMAL (0)

function setup()
{
    host.log("Vehicle_Status sender started");
    host.setTickInterval(20);
}

function tick()
{
    var data = [
        0xF4, // Speed low byte: 50.0 km/h = 500 = 0x01F4
        0x01, // Speed high byte
        0xB8, // RPM low byte: 3000 = 0x0BB8
        0x0B, // RPM high byte
        0x02, // Gear D, Brake OFF, Network NORMAL
        0x00,
        0x00,
        0x00
    ];

    can.sendFrame(0, 0x120, 8, data);
}
