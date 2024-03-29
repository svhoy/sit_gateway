#pylint: disable=unused-argument
# Standard Library
import asyncio
import json

# Library
from apps.sit_gateway import gateway
from apps.sit_gateway.domain import commands
from apps.sit_gateway.entrypoint import websocket


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
        "min_measurement": 0,
        "max_measurement": 0,
        "measurement_type": command.measurement_type,
        "rx_ant_dly": command.rx_ant_dly,
        "tx_ant_dly": command.tx_ant_dly,
    }
    await gateway.ble_send_json(
        "6ba1de6b-3ab6-4d77-9ea1-cb6422720004", setup, command.initiator
    )
    for responder in command.responder:
        await gateway.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720004", setup, responder
        )
    await asyncio.sleep(3)
    await gateway.set_measurement_type(command.measurement_type)
    await gateway.start_measurement(
        initiator_device=command.initiator,
        responder_devices=command.responder,
    )


async def stop_measurement(
    command: commands.StopDistanceMeasurement, gateway: gateway.SITGateway
):
    await gateway.stop_measurement()


async def start_test_measurement(
    command: commands.StartTestMeasurement, gateway: gateway.SITGateway
):
    setup = {
        "type": "setup_msg",
        "initiator_device": command.initiator,
        "initiator": 1,
        "responder_device": command.responder,
        "responder": len(command.responder),
        "min_measurement": command.min_measurement,
        "max_measurement": command.max_measurement,
        "rx_ant_dly": command.rx_ant_dly,
        "tx_ant_dly": command.tx_ant_dly,
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
        test_id=command.test_id,
    )


async def start_calibration(
    command: commands.StartCalibrationMeasurement, gateway: gateway.SITGateway
):
    await gateway.setup_calibration(command)


async def start_single_cali_measurement(
    command: commands.StartCalibrationMeasurement, gateway: gateway.SITGateway
):
    await gateway.start_calibration()


COMMAND_HANDLER = {
    commands.RegisterWsClient: register_ws_client,
    commands.PingWsConnection: ping_ws_connection,
    commands.ConnectBleDevice: connect_ble_device,
    commands.DisconnectBleDevice: disconnect_ble_device,
    commands.StartDistanceMeasurement: start_measurement,
    commands.StopDistanceMeasurement: stop_measurement,
    commands.StartTestMeasurement: start_test_measurement,
    commands.StartCalibrationMeasurement: start_calibration,
    commands.StartSingleCalibrationMeasurement: start_single_cali_measurement,
}
