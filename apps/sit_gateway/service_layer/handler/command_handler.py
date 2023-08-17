# Standard Library
import asyncio
import json

from ... import gateway
from ...domain import commands
from ...entrypoint import websocket


# Send a register msg to webserver for connection when connection is acepted
async def register_ws_client(
    command: commands.RegisterWsClient,
    ws: websocket.Websocket,
):
    message = command.json
    await ws.send(message)


async def ping_ws_connection(
    command: commands.PingWsConnection, ws: websocket.Websocket
):
    message = {
        "type": "RegisterWsClient",
        "data": {
            "client_id": "PI_Home",
        },
    }
    await ws.send(json.dumps(message))


async def connect_ble_device(
    command: commands.ConnectBleDevice, gateway: gateway.SITGateway
):
    await gateway.start_ble_gateway(command.device_id)


async def disconnect_ble_device(
    command: commands.DisconnectBleDevice, gateway: gateway.SITGateway
):
    await gateway.stop_ble_gateway(command.device_id)


async def start_measurement(
    command: commands.StartDistanceMeasurement, gateway: gateway.SITGateway
):
    setup = {
        "type": "setup_msg",
        "initiator_device": command.initiator,
        "initiator": 1,
        "responder_device": command.responder,
        "responder": len(command.responder),
    }
    await gateway.ble_send_json(
        "6ba1de6b-3ab6-4d77-9ea1-cb6422720004", setup, command.initiator
    )
    for responder in command.responder:
        await gateway.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720004", setup, responder
        )
    await asyncio.sleep(3)
    await gateway.start_measurement(
        initiator_device=command.initiator,
        responder_devices=command.responder,
        test_id=None,
    )


async def stop_measurement(
    command: commands.StopDistanceMeasurement, gateway: gateway.SITGateway
):
    await gateway.stop_measurement()


COMMAND_HANDLER = {
    commands.RegisterWsClient: register_ws_client,
    commands.PingWsConnection: ping_ws_connection,
    commands.ConnectBleDevice: connect_ble_device,
    commands.DisconnectBleDevice: disconnect_ble_device,
    commands.StartDistanceMeasurement: start_measurement,
    commands.StopDistanceMeasurement: start_measurement,
}
