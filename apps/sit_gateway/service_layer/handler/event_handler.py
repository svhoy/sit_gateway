# Standard Library
import json
import logging
import logging.config

from email import message

# Library
from apps.sit_gateway.domain import events
from apps.sit_gateway.entrypoint import websocket


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("event_handler")


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
            "measurement_type": event.measurement_type,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "distance": event.distance,
            "time_round_1": event.time_round_1,
            "time_round_2": event.time_round_2,
            "time_reply_1": event.time_reply_1,
            "time_reply_2": event.time_reply_2,
            "nlos_final": event.nlos,
            "rssi_final": event.rssi,
            "fpi_final": event.fpi,
        },
    }
    logger.debug(f"Sending distance measurement: {message}")
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
            "measurement_type": event.measurement_type,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "distance": event.distance,
            "time_round_1": event.time_round_1,
            "time_round_2": event.time_round_2,
            "time_reply_1": event.time_reply_1,
            "time_reply_2": event.time_reply_2,
            "nlos_final": event.nlos,
            "rssi_final": event.rssi,
            "fpi_final": event.fpi,
        },
    }
    await ws.send(json.dumps(message))


async def send_calibration_measurement(
    event: events.CalibrationMeasurement, ws: websocket.Websocket
):
    message = {
        "type": "SaveCalibrationMeasurement",
        "data": {
            "calibration_id": event.calibration_id,
            "initiator": event.initiator,
            "responder": event.responder,
            "measurement_type": event.measurement_type,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "distance": event.distance,
            "time_round_1": event.time_round_1,
            "time_round_2": event.time_round_2,
            "time_reply_1": event.time_reply_1,
            "time_reply_2": event.time_reply_2,
            "nlos_final": event.nlos,
            "rssi_final": event.rssi,
            "fpi_final": event.fpi,
        },
    }
    logger.debug(
        f"Sending calibration measurement: {message['data']['measurement_type']}"
    )
    await ws.send(json.dumps(message))


async def send_simple_calibration_measurement(
    event: events.SimpleCalibrationMeasurement, ws: websocket.Websocket
):
    message = {
        "type": "SaveSimpleCalibrationMeasurement",
        "data": {
            "calibration_id": event.calibration_id,
            "sequence": event.sequence,
            "measurement": event.measurement,
            "devices": event.devices,
            "time_m21": event.time_m21,
            "time_m31": event.time_m31,
            "time_a21": event.time_a21,
            "time_a31": event.time_a31,
            "time_b21": event.time_b21,
            "time_b31": event.time_b31,
            "time_tc_i": event.time_tc_i,
            "time_tc_ii": event.time_tc_ii,
            "time_tb_i": event.time_tb_i,
            "time_tb_ii": event.time_tb_ii,
            "time_round_1": event.time_round_1,
            "time_round_2": event.time_round_2,
            "time_reply_1": event.time_reply_1,
            "time_reply_2": event.time_reply_2,
            "distance": event.distance,
        },
    }
    logger.debug(f"Sending calibration measurement: {message['data']}")
    await ws.send(json.dumps(message))


async def send_test_finished(
    event: events.TestMeasurementFinished, ws: websocket.Websocket
):
    message = {
        "type": "TestFinished",
        "data": {
            "test_id": event.test_id,
        },
    }
    await ws.send(json.dumps(message))


async def redirect_event(
    event: (
        events.BleDeviceConnectFailed
        | events.BleDeviceConnectError
        | events.CalibrationMeasurementFinished
    ),
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
    events.SimpleCalibrationMeasurement: [send_simple_calibration_measurement],
    events.CalibrationSimpleMeasurementFinished: [redirect_event],
    events.TestMeasurementFinished: [send_test_finished],
}
