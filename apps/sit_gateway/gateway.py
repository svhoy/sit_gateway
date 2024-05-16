# Standard Library
import asyncio
import json
import logging
import logging.config

from cgi import test
from itertools import permutations
from turtle import distance

# Third Party
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

# Library
from apps.sit_gateway.domain import commands, events
from apps.sit_gateway.domain.data import MsgData, SimpleMsgData
from apps.sit_gateway.service_layer.utils import cancel_task

from .adapter.ble import Ble


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("sit_gateway")


class SITGateway:
    def __init__(self) -> None:
        self.ble_list: list[Ble] = []

        self.test_id: int = 0
        self.calibration_id: int = 0
        self._distance_notify_tasks = set()
        self.measurement_type = "ss_twr"
        self.initiator_device: str
        self.responder_devices: list[str]
        self.cali_device_list: list[str]
        self.is_running = False

    def set_dependencies(self, tg, bus):
        self.task_group = tg
        self.bus = bus

    async def cleanup(self):
        for device in self.ble_list:
            await device.cleanup()
        self.ble_list.clear()
        for task in asyncio.all_tasks():
            if "Ble Task " in task.get_name():
                task.cancel()
                return None

    # Bluetooth Connection Manager
    async def start_ble_gateway(self, device_id: str) -> None:
        ble = await self.connect_ble(device_name=device_id)
        await asyncio.sleep(5.0)
        if ble is not None:
            await asyncio.sleep(5.0)
            # TODO
            if ble.is_connected():
                self.ble_list.append(ble)
                await self.bus.handle(
                    events.BleDeviceConnected(device_id=device_id)
                )
            else:
                cancel_task("Ble Task " + device_id)
                await self.bus.handle(
                    events.BleDeviceConnectError(
                        device_id=device_id, reason="Error"
                    )
                )
        else:
            await self.bus.handle(
                events.BleDeviceConnectFailed(
                    device_id=device_id, reason="Not Found"
                )
            )

    async def stop_ble_gateway(self, device_id) -> None:
        index = self.get_device_index(device_id)
        if index is not None:
            ble = self.ble_list.pop(index)
            await ble.cleanup()
            cancel_task("Ble Task " + device_id)
        await self.bus.handle(
            events.BleDeviceDisconnected(device_id=device_id)
        )

    async def scan(self, timeout: float = 10.0) -> list[BLEDevice]:
        _scanner = BleakScanner()
        return await _scanner.discover(timeout=timeout)

    async def connect_ble(self, device_name) -> Ble | None:
        devices = await self.scan(20)
        for device in devices:
            if device_name in device.name:
                ble = Ble(self)
                logger.info(f"{device.name}: {device.address}")
                logger.info(f"UUIDs: {device.metadata['uuids']}")
                task_name = (
                    "Ble Task " + device_name
                )  # BLE TASK with Device Name to identify the Task
                self.task_group.create_task(
                    ble.connect_device(device),
                    name=task_name,
                )
                await asyncio.sleep(2.0)
                return ble
        return None

    async def start_measurement(
        self,
        initiator_device: str,
        responder_devices: list[str],
        test_id=None,
    ):
        self.test_id = test_id
        self.initiator_device = initiator_device
        self.responder_devices = responder_devices

        command = {"type": "measurement_msg", "command": "start"}
        for responder in self.responder_devices:
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command, responder
            )
        await self.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command, initiator_device
        )

        self.task_group.create_task(
            self.enable_notify(initiator_device),
            name="BLE Notify" + initiator_device,
        )
        for responder in responder_devices:
            self.task_group.create_task(
                self.enable_notify(responder), name="BLE Notify" + responder
            )
        self.is_running = True

    async def stop_measurement(self):
        command = {"type": "measurement_msg", "command": "stop"}
        for responder in self.responder_devices:
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command, responder
            )
            cancel_task("BLE Notify" + responder)
        await self.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
            command,
            self.initiator_device,
        )
        cancel_task("BLE Notify" + self.initiator_device)

        self.is_running = False

    async def start_cali_measurement(self, devices):
        command = {"type": "measurement_msg", "command": "start"}
        for device in devices:
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
                command,
                device,
            )
            self.task_group.create_task(
                self.enable_notify(device),
                name="BLE Notify" + device,
            )
            await asyncio.sleep(0.5)

    async def stop_cali_measurement(self):
        command = {"type": "measurement_msg", "command": "stop"}
        for device in reversed(self.actuale_cali_devices):
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command, device
            )
            cancel_task("BLE Notify" + device)
        self.is_running = False

    async def enable_notify(self, initiator_device):
        enable_notify = False
        device = self.get_device(initiator_device)
        while 1:
            if device.is_connected() and not enable_notify:
                await device.get_notification(
                    "6ba1de6b-3ab6-4d77-9ea1-cb6422720001",
                    self.distance_notifcation,
                )
                enable_notify = True
            await asyncio.sleep(2)

    async def distance_notifcation(
        self, data: MsgData | SimpleMsgData, device: str
    ):
        if isinstance(data, MsgData):
            # Not a good option but when get full data msg
            # the response
            # from device the id is always 8292
            # so find an option to change this

            if self.measurement_type == "ss_twr":
                responder = self.responder_devices[0]
            else:
                responder = device

            if self.test_id != 0:
                await self.bus.handle(
                    events.TestMeasurement(
                        test_id=self.test_id,
                        initiator=self.initiator_device,
                        responder=responder,
                        measurement_type=self.measurement_type,
                        sequence=data.sequence,
                        measurement=data.measurement,
                        distance=data.distance,
                        time_round_1=data.time_round_1,
                        time_round_2=data.time_round_2,
                        time_reply_1=data.time_reply_1,
                        time_reply_2=data.time_reply_2,
                        nlos=data.nlos,
                        rssi=data.rssi,
                        fpi=data.fpi,
                    )
                )
                if self.test_setup["max_measurement"] - 1 == data.measurement:
                    await self.stop_measurement()
                    await self.bus.handle(
                        events.TestMeasurementFinished(self.test_id)
                    )
                    self.test_id = None

            elif self.calibration_id != 0:
                await self.bus.handle(
                    events.SimpleCalibrationMeasurement(
                        calibration_id=self.calibration_id,
                        sequence=data.sequence,
                        measurement=data.measurement,
                        devices=self.actuale_cali_devices,
                        time_reply_1=data.time_reply_1,
                        time_reply_2=data.time_reply_2,
                        time_round_1=data.time_round_1,
                        time_round_2=data.time_round_2,
                        distance=data.distance,
                    )
                )
                if self.cali_setup["max_measurement"] - 1 == data.measurement:
                    await self.stop_cali_measurement()
                    await self.bus.handle(
                        commands.StartSingleCalibrationMeasurement()
                    )
            else:
                logger.debug(f"Data: {data}")
                await self.bus.handle(
                    events.DistanceMeasurement(
                        initiator=self.initiator_device,
                        responder=responder,
                        measurement_type=self.measurement_type,
                        sequence=data.sequence,
                        measurement=data.measurement,
                        distance=data.distance,
                        time_round_1=data.time_round_1,
                        time_round_2=data.time_round_2,
                        time_reply_1=data.time_reply_1,
                        time_reply_2=data.time_reply_2,
                        nlos=data.nlos,
                        rssi=data.rssi,
                        fpi=data.fpi,
                    )
                )
        else:
            await self.bus.handle(
                events.SimpleCalibrationMeasurement(
                    calibration_id=self.calibration_id,
                    sequence=data.sequence,
                    measurement=data.measurement,
                    devices=self.actuale_cali_devices,
                    time_m21=data.time_m21,
                    time_m31=data.time_m31,
                    time_a21=data.time_a21,
                    time_a31=data.time_a31,
                    time_b21=data.time_b21,
                    time_b31=data.time_b31,
                    time_tc_i=data.time_tc_i,
                    time_tc_ii=data.time_tc_ii,
                    time_tb_i=data.time_tb_i,
                    time_tb_ii=data.time_tb_ii,
                    time_reply_1=data.time_reply_1,
                    time_reply_2=data.time_reply_2,
                    time_round_1=data.time_round_1,
                    time_round_2=data.time_round_2,
                    distance=data.distance,
                )
            )
            if self.cali_setup["max_measurement"] - 1 == data.measurement:
                await self.stop_cali_measurement()
                await self.bus.handle(
                    commands.StartSingleCalibrationMeasurement()
                )

    async def setup_calibration(
        self,
        calibration_setup: commands.StartCalibrationMeasurement,
    ):
        self.calibration_id = calibration_setup.calibration_id
        self.cali_device_list = []
        for initiator_device in calibration_setup.devices:
            for responder_device in calibration_setup.devices:
                if initiator_device != responder_device:
                    self.cali_device_list.append(
                        [initiator_device, responder_device]
                    )

        self.cali_finished_list = []
        self.cali_rounds = len(self.cali_device_list)

        self.cali_setup = {
            "type": "setup_msg",
            "device_type": "",
            "initiator_device": "",
            "initiator": 1,
            "responder_device": [],
            "responder": 1,
            "min_measurement": 0,
            "max_measurement": calibration_setup.max_measurement,
            "measurement_type": calibration_setup.measurement_type,
            "rx_ant_dly": calibration_setup.rx_ant_dly,
            "tx_ant_dly": calibration_setup.tx_ant_dly,
        }
        await self.bus.handle(commands.StartSingleCalibrationMeasurement())

    async def setup_test(
        self,
        test_setup: commands.StartTestMeasurement,
    ):
        self.test_id = test_setup.test_id
        self.test_setup = {
            "type": "setup_msg",
            "device_type": "",
            "initiator_device": test_setup.initiator,
            "initiator": 1,
            "responder_device": test_setup.responder,
            "responder": 1,
            "min_measurement": 0,
            "max_measurement": test_setup.max_measurement,
            "measurement_type": test_setup.measurement_type,
        }
        await self.set_measurement_type(test_setup.measurement_type)
        self.test_setup["device_type"] = "initiator"
        self.test_setup["rx_ant_dly"] = int(
            (test_setup.init_rx_ant_dly / 1.026e-6) * 63898
        )
        self.test_setup["tx_ant_dly"] = int(
            (test_setup.init_tx_ant_dly / 1.026e-6) * 63898
        )
        await self.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
            self.test_setup,
            test_setup.initiator,
        )
        self.test_setup["device_type"] = "responder"

        for responder in test_setup.responder:
            self.test_setup["rx_ant_dly"] = int(
                (test_setup.resp_rx_ant_dly / 1.026e-6) * 63898
            )
            self.test_setup["tx_ant_dly"] = int(
                (test_setup.resp_tx_ant_dly / 1.026e-6) * 63898
            )
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
                self.test_setup,
                responder,
            )
        await asyncio.sleep(3)
        await self.start_measurement(
            initiator_device=test_setup.initiator,
            responder_devices=test_setup.responder,
            test_id=test_setup.test_id,
        )

    async def setup_simple_calibration(
        self,
        calibration_setup: commands.StartSimpleCalibrationMeasurement,
    ):
        self.is_running = True
        self.cali_finished_list = []
        self.calibration_id = calibration_setup.calibration_id

        self.measurement_type = calibration_setup.measurement_type

        self.cali_device_list = list(
            map(list, permutations(calibration_setup.devices, 3))
        )
        self.cali_rounds = len(self.cali_device_list)
        self.cali_setup = {
            "type": "setup_msg",
            "device_type": "",
            "initiator_device": "",
            "initiator": 1,
            "responder_device": [],
            "responder": 1,
            "min_measurement": 0,
            "max_measurement": calibration_setup.max_measurement,
            "measurement_type": calibration_setup.measurement_type,
            "rx_ant_dly": calibration_setup.rx_ant_dly,
            "tx_ant_dly": calibration_setup.tx_ant_dly,
        }

        await asyncio.sleep(2)
        await self.bus.handle(commands.StartSingleCalibrationMeasurement())

    async def start_simple_calibration(self):
        self.is_running = True
        if self.cali_rounds > len(self.cali_finished_list):
            self.actuale_cali_devices = self.cali_device_list.pop(0)
            for idx, device in enumerate(self.actuale_cali_devices):
                if idx == 0:
                    if self.measurement_type == "two_device":
                        self.cali_setup["device_type"] = "A"
                    else:
                        self.cali_setup["device_type"] = "initiator"
                        self.cali_setup["initiator_device"] = device
                elif idx == 1:
                    if self.measurement_type == "two_device":
                        self.cali_setup["device_type"] = "B"
                    else:
                        self.cali_setup["device_type"] = "responder"
                        self.cali_setup["responder_device"] = [device]
                elif idx == 2:
                    self.cali_setup["device_type"] = "C"

                await self.ble_send_json(
                    "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
                    self.cali_setup,
                    device,
                )
                await asyncio.sleep(0.1)
            self.cali_finished_list.append(self.actuale_cali_devices)
            await self.start_cali_measurement(self.actuale_cali_devices)
        else:
            logger.debug("Calibration Finished")
            self.is_running = False
            await self.bus.handle(
                events.CalibrationSimpleMeasurementFinished(
                    calibration_id=self.calibration_id
                )
            )

    async def start_calibration(self):
        logger.info(f"Cali Round: {self.cali_rounds}")
        logger.info(f"Cali Liste: {self.cali_device_list}")
        logger.info(f"Cali Finished Len: {len(self.cali_finished_list)}")
        if self.cali_rounds > len(self.cali_finished_list):
            cali_devices = self.cali_device_list.pop(0)
            self.cali_setup["initiator_device"] = cali_devices[0]
            self.cali_setup["responder_device"] = [cali_devices[1]]

            self.cali_setup["device_type"] = "initiator"
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
                self.cali_setup,
                self.cali_setup["initiator_device"],
            )

            self.cali_setup["device_type"] = "responder"
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
                self.cali_setup,
                self.cali_setup["responder_device"][0],
            )
            await asyncio.sleep(3)
            self.cali_finished_list.append(cali_devices)
            await self.start_measurement(
                self.cali_setup["initiator_device"],
                self.cali_setup["responder_device"],
            )

        else:
            logger.debug("Calibration Finished")
            self.is_running = False
            await self.bus.handle(
                events.CalibrationMeasurementFinished(
                    calibration_id=self.calibration_id
                )
            )

    async def ble_send_json(self, uuid, command, device_name):
        try:
            device = self.get_device(device_name)
            json_msg = json.dumps(command).encode("utf-8")
            await device.write_command(uuid, json_msg)
            logger.debug(f"JSON Command Sent: {device_name}")
        except BleakError as e:
            logger.error(f"Can't write JSON Command: {e}")

    async def ble_send_int(
        self, uuid: str, intger: int, device_name: str
    ) -> None:
        try:
            device = self.get_device(device_name)
            await device.write_command(
                uuid, intger.to_bytes(1, byteorder="big")
            )
        except BleakError as e:
            logger.error(f"Can't write Int Command: {e}")

    # Utils Gateway Functions
    async def set_measurement_type(self, measurement_type: str) -> None:
        self.measurement_type = measurement_type

    def get_device_index(self, device_name: str) -> int | None:
        index = 0
        for device in self.ble_list:
            if device_name in device.get_device_name():
                return index
            index += 1
        return None

    def get_device(self, device_name: str) -> Ble | None:
        for device in self.ble_list:
            if device_name in device.get_device_name():
                return device
        return None

    def get_responder(self, responder_index: int) -> str:
        # modolu 100 because the id
        # from responders on ble devices starts with 100
        # so to get index in device list will be:
        index = responder_index % 100
        return self.responder_devices[index]
