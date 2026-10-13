// SavvyCAN Scripting Interface test sender
//
// Sends the DBC Gateway_Status message (CAN ID 0x300) every 100 ms.
// Payload:
//   D0[3:0]: GatewayAlive = 0..15, wrapping around
//   D1:      QueueUsage = 37 percent

var gatewayAlive = 0;

function setup()
{
    host.log("Gateway_Status sender started");
    host.setTickInterval(100);
}

function tick()
{
    var data = [
        gatewayAlive & 0x0F, // GatewayAlive
        0x25,                // QueueUsage = 37%
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00
    ];

    can.sendFrame(0, 0x300, 8, data);

    gatewayAlive = (gatewayAlive + 1) & 0x0F;
}
