// SavvyCAN Scripting Interface test sender
//
// Sends the DBC Body_Status message (CAN ID 0x200) every 100 ms.
// Payload:
//   D0[0]: ReverseLamp = ON
//   D0[1]: DoorOpen = YES
//   D1:    DoorStatus = OPEN_LOCKED (3)
//   D2:    LightStatus = HAZARD (0x08)
//   D3:    WindowStatus = MOVING_UP (1)

function setup()
{
    host.log("Body_Status sender started");
    host.setTickInterval(100);
}

function tick()
{
    var data = [
        0x03, // ReverseLamp ON + DoorOpen YES
        0x03, // DoorStatus OPEN_LOCKED
        0x08, // LightStatus HAZARD
        0x01, // WindowStatus MOVING_UP
        0x00,
        0x00,
        0x00,
        0x00
    ];

    can.sendFrame(0, 0x200, 8, data);
}
