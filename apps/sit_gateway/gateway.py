# Standard Library
import asyncio
import json
import logging
import logging.config

# Third Party
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

# Library
from apps.sit_gateway.domain import commands, events
from apps.sit_gateway.service_layer.utils import cancel_task

from .adapter.ble import Ble


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_socket")


class SITGateway:
    def __init__(self) -> None:
        self.ble_list: list[Ble] = []

        self.test_id = None
        self.calibration_id: int = 0

    def set_dependencies(self, tg, bus):
        self.taskGroup = tg
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
            if ble.isConnected():
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
        logger.info(devices)
        for device in devices:
            if device_name in device.name:
                ble = Ble(self)
                logger.info("{}: {}".format(device.name, device.address))
                logger.info("UUIDs: {}".format(device.metadata["uuids"]))
                task_name = (
                    "Ble Task " + device_name
                )  # BLE TASK with Device Name to identify the Task
                self.taskGroup.create_task(
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
        self._distance_notify_task = self.taskGroup.create_task(
            self.enable_notify(initiator_device)
        )

    async def stop_measurement(self):
        command = {"type": "measurement_msg", "command": "stop"}
        for responder in self.responder_devices:
            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command, responder
            )
        await self.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
            command,
            self.initiator_device,
        )
        if self._distance_notify_task is not None:
            self._distance_notify_task.cancel()
        self.test_id = None

    async def enable_notify(self, initiator_device):
        enable_notify = False
        device = self.get_device(initiator_device)
        while 1:
            if device.isConnected() and not enable_notify:
                await device.getNotification(
                    "6ba1de6b-3ab6-4d77-9ea1-cb6422720001",
                    self.distance_notifcation,
                )
                enable_notify = True
            await asyncio.sleep(2)

    async def distance_notifcation(
        self, responder, sequence, measurement, distance, nlos, rssi, fpi
    ):
        if self.test_id is not None:
            await self.bus.handle(
                events.TestMeasurement(
                    test_id=self.test_id,
                    initiator=self.initiator_device,
                    responder=self.get_responder(responder),
                    sequence=sequence,
                    measurement=measurement,
                    distance=distance,
                    nlos=nlos,
                    rssi=rssi,
                    fpi=fpi,
                )
            )
        elif self.calibration_id != 0:
            await self.bus.handle(
                events.CalibrationMeasurement(
                    claibration_id=self.calibration_id,
                    initiator=self.initiator_device,
                    responder=self.get_responder(responder),
                    sequence=sequence,
                    measurement=measurement,
                    distance=distance,
                    nlos=nlos,
                    rssi=rssi,
                    fpi=fpi,
                )
            )
            if self.cali_setup["max_measurement"] == measurement:
                await self.stop_measurement()
                await self.bus.handle(
                    commands.StartSingleCalibrationMeasurement()
                )
        else:
            await self.bus.handle(
                events.DistanceMeasurement(
                    initiator=self.initiator_device,
                    responder=self.get_responder(responder),
                    sequence=sequence,
                    measurement=measurement,
                    distance=distance,
                    nlos=nlos,
                    rssi=rssi,
                    fpi=fpi,
                )
            )

    async def setup_calibration(
        self, calibration_setup: commands.StartCalibrationMeasurement
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
            "initiator_device": "",
            "initiator": 1,
            "responder_device": [],
            "responder": 1,
            "min_measurement": 0,
            "max_measurement": calibration_setup.max_measurement,
            "rx_ant_dly": calibration_setup.rx_ant_dly,
            "tx_ant_dly": calibration_setup.tx_ant_dly,
        }
        await self.bus.handle(commands.StartSingleCalibrationMeasurement())

    async def start_calibration(self):
        print("Test")
        print(f"Cali Round: {self.cali_rounds}")
        print(f"Cali Liste: {self.cali_device_list}")
        print(f"Cali Finished Len: {len(self.cali_finished_list)}")
        if self.cali_rounds > len(self.cali_finished_list):
            cali_devices = self.cali_device_list.pop(0)
            self.cali_setup["initiator_device"] = cali_devices[0]

            self.cali_setup["responder_device"] = [cali_devices[1]]

            await self.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
                self.cali_setup,
                self.cali_setup["initiator_device"],
            )

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
        except Exception:
            logger.error("Counldn't Write Json Command")

    async def ble_send_int(
        self, uuid: str, intger: int, device_name: str
    ) -> None:
        try:
            device = self.get_device(device_name)
            await device.write_command(
                uuid, intger.to_bytes(1, byteorder="big")
            )
        except Exception:
            logger.error("Cound't write Int Command")

    # Utils Gateway Functions
    def get_device_index(self, device_name: str) -> int | None:
        index = 0
        for device in self.ble_list:
            if device_name in device.getDeviceName():
                return index
            else:
                index += 1
        return None

    def get_device(self, device_name: str) -> Ble | None:
        for device in self.ble_list:
            if device_name in device.getDeviceName():
                return device
        return None

    def get_responder(self, responder_index: int) -> str:
        # modolu 100 because the id
        # from responders on ble devices starts with 100
        # so to get index in device list will be:
        index = responder_index % 100
        return self.responder_devices[index]
