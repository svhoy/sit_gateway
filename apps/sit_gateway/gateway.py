# Standard Library
import asyncio
import json
import logging
import logging.config

# Third Party
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

# Library
from apps.sit_gateway.domain import events
from apps.sit_gateway.service_layer.utils import cancel_task

from .adapter.ble import Ble


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_socket")


class SITGateway:
    def __init__(self) -> None:
        self.ble_list: list[Ble] = []

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
        await self.bus.handle(events.BleDeviceDisconnected(device_id=device_id))

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
        test_id: int | None,
    ):
        self._test_id = test_id
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
        self._test_id = None
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
        self.initiator_device = None
        self.responder_devices = []
        if self._distance_notify_task is not None:
            self._distance_notify_task.cancel()

    async def enable_notify(self, initiator_device):
        enable_notify = False
        device = self.get_device(initiator_device)
        while 1:
            if device.isConnected() and not enable_notify:
                await device.getNotification(
                    "6ba1de6b-3ab6-4d77-9ea1-cb6422720001", self.bus
                )
                enable_notify = True
            await asyncio.sleep(2)

    async def ble_send_json(self, uuid, command, device_name):
        try:
            device = self.get_device(device_name)
            json_msg = json.dumps(command).encode("utf-8")
            await device.write_command(uuid, json_msg)
        except:
            logger.error("Counldn't Write Json Command")

    async def ble_send_int(
        self, uuid: str, intger: int, device_name: str
    ) -> None:
        try:
            device = self.get_device(device_name)
            await device.write_command(
                uuid, intger.to_bytes(1, byteorder="big")
            )
        except:
            logger.error("Cound't write Int Command")

    # Utils Gateway Functions
    def get_device_index(self, device_name) -> int | None:
        index = 0
        for device in self.ble_list:
            if device_name in device.getDeviceName():
                return index
            else:
                index += 1
        return None

    def get_device(self, device_name) -> Ble | None:
        for device in self.ble_list:
            if device_name in device.getDeviceName():
                return device
        return None
