# Standard Library
import json

# Library
from apps.sit_gateway.domain import events
from apps.sit_gateway.entrypoint import websocket


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
            "responder": event.responder,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "distance": event.distance,
            "nlos": event.nlos,
            "rssi": event.rssi,
            "fpi": event.fpi,
        },
    }
    await ws.send(json.dumps(message))


async def send_test_measurement(
    event: events.TestMeasurement, ws: websocket.Websocket
):
    message = {
        "type": "SaveTestMeasurement",
        "data": {
            "test_id": event.test_id,
            "initiator": event.initiator,
            "responder": event.responder,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "distance": event.distance,
            "nlos": event.nlos,
            "rssi": event.rssi,
            "fpi": event.fpi,
        },
    }
    await ws.send(json.dumps(message))


async def send_calibration_measurement(
    event: events.CalibrationMeasurement, ws: websocket.Websocket
):
    message = {
        "type": "SaveCalibrationMeasurement",
        "data": {
            "calibration_id": event.claibration_id,
            "initiator": event.initiator,
            "responder": event.responder,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "distance": event.distance,
            "nlos": event.nlos,
            "rssi": event.rssi,
            "fpi": event.fpi,
        },
    }
    await ws.send(json.dumps(message))


async def redirect_event(
    event: events.BleDeviceConnectFailed
    | events.BleDeviceConnectError
    | events.CalibrationMeasurementFinished,
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
    events.CalibrationMeasurement: [send_calibration_measurement],
    events.CalibrationMeasurementFinished: [redirect_event],
    events.TestMeasurement: [send_test_measurement],
}
