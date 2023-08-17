# Standard Library
import json

# Library
from apps.sit_gateway.entrypoint import websocket

from ...domain import events


async def register_ble_connection(
    event: events.BleDeviceConnected,
    ws: websocket.Websocket,
):
    message = {
        "type": "RegisterBleConnection",
        "data": {"device_id": event.device_id},
    }
    await ws.send(json.dumps(message))


async def unregister_ble_connection(
    event: events.BleDeviceDisconnected,
    ws: websocket.Websocket,
):
    message = {
        "type": "UnregisterBleConnection",
        "data": {"device_id": event.device_id},
    }
    await ws.send(json.dumps(message))


async def send_distance_measurement(
    event: events.DistanceMeasurement, ws: websocket.Websocket
):
    message = {
        "type": "SaveMesurement",
        "data": {
            "initiator": event.initiator,
            "sequence": event.sequence,
            "distance": event.distance,
            "nlos": event.nlos,
            "rssi": event.rssi,
            "fpi": event.fpi,
        },
    }
    await ws.send(json.dumps(message))


async def redirect_event(
    event: events.BleDeviceConnectFailed | events.BleDeviceConnectError,
    ws: websocket.Websocket,
):
    message = event.json
    await ws.send(message)


EVENT_HANDLER = {
    events.BleDeviceConnected: [register_ble_connection],
    events.BleDeviceConnectError: [redirect_event],
    events.BleDeviceConnectFailed: [redirect_event],
    events.BleDeviceDisconnected: [unregister_ble_connection],
    events.DistanceMeasurement: [send_distance_measurement],
}
