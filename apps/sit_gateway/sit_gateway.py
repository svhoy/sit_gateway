# Standard Library
import asyncio
import json
import logging
import logging.config

# Third Party
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from .ble import Ble
from .websocket import Websocket


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_socket")


class SITGateway:
    def __init__(self, taskGroup) -> None:
        self.taskGroup = taskGroup
        self._ble_list: list[Ble] = []
        self._socket: Websocket = Websocket(self)

        self._test_id: int | None = None
        self._ble_connection_task: list[asyncio.Task] = []
        self._websocket_task: asyncio.Task | None = None
        self._distance_notify_task: asyncio.Task | None = None

    async def start_gateway(self):
        await self.start_websocket()

    async def cleanup(self):
        for device in self._ble_list:
            await device.cleanup()
        self._ble_list.clear()
        if self._distance_notify_task is not None:
            self._distance_notify_task.cancel()
        if self._websocket_task is not None:
            self._websocket_task.cancel()
        for task in asyncio.all_tasks():
            if "Ble Task " in task.get_name():
                task.cancel()
                return None

    # Websocket Manager
    async def start_websocket(self) -> None:
        self._websocket_task = asyncio.create_task(self._socket.connect())
        await self._websocket_task

    # Message Handler
    # Handle Connection Messanges
    async def handle_ping_msg(self):
        await self._socket.send_websocket_ping()

    # Handle Scanning MSG Connection
    async def handle_scanning_msg(self, msg):
        match msg:
            case {"state": True, "device_name": device_name}:
                await self.start_ble_gateway(device_name)
            case {
                "state": False,
                "connection": "disconnect",
                "device_name": device_name,
            }:
                await self.stop_ble_gateway(device_name)

    # Handle Distance message
    async def handle_distance_msg(self, data):
        match data:
            case {"state": "start", "test_id": test_id, **rest}:
                await self.start_measurement(test_id)
            case {"state": "stop", **rest}:
                await self.stop_measurement()

    # Bluetooth Connection Manager
    async def start_ble_gateway(self, device_name) -> None:
        ble = await self.connect_ble(device_name=device_name)
        await asyncio.sleep(5.0)
        if ble is not None:
            await asyncio.sleep(5.0)
            # TODO
            if ble.isConnected():
                self._ble_list.append(ble)
                connection = "complete"
            else:
                if len(self._ble_connection_task) >= 1:
                    connection_task = self._ble_connection_task.pop()
                    connection_task.cancel()
                connection = "error"
            await self._socket.send_ble_connection_msg(
                connection,
                device_name,
            )
        else:
            await self._socket.send_ble_connection_msg("notFound", device_name)

    async def stop_ble_gateway(self, device_name) -> None:
        index = self.get_device_index(device_name)
        if index is not None:
            ble = self._ble_list.pop(index)
            await ble.cleanup()
            if self._distance_notify_task:
                self._distance_notify_task.cancel()
            self.cancel_task("Ble Task " + device_name)

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
                task_name = "Ble Task " + device_name
                self.taskGroup.create_task(
                    ble.connect_device(device),
                    name=task_name,
                )
                await asyncio.sleep(2.0)
                return ble
        return None

    async def enable_notify(self):
        enable_notify = False
        while 1:
            if self._ble.isConnected() and not enable_notify:
                await self._ble.getNotification(
                    "6ba1de6b-3ab6-4d77-9ea1-cb6422720001"
                )
                enable_notify = True
            await asyncio.sleep(2)

    async def ble_send_json(self, ble, uuid, command):
        json_msg = json.dumps(command).encode("utf-8")
        await ble.write_command(uuid, json_msg)

    async def ble_send_int(self, uuid: str, intger: int) -> None:
        await ble.write_command(uuid, intger.to_bytes(1, byteorder="big"))

    async def start_measurement(self, test_id: int | None):
        self._test_id = test_id
        command = {"type": "measurement_msg", "command": "start"}
        await self.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command
        )
        # await self.ble_send_int("6ba1de6b-3ab6-4d77-9ea1-cb6422720002", 5)
        self._distance_notify_task = asyncio.create_task(self.enable_notify())

    async def stop_measurement(self):
        self._test_id = None
        command = {"type": "measurement_msg", "command": "stop"}
        await self.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003", command
        )
        if self._distance_notify_task is not None:
            self._distance_notify_task.cancel()

    async def distance_notify(self, id, sequence, distance, nlos, rssi, fpi):
        await self._socket.send_distance_msg(
            self._test_id, sequence, distance, nlos, rssi, fpi
        )

    def get_device_index(self, device_name) -> int | None:
        index = 0
        for device in self._ble_list:
            if device_name in device.getDeviceName():
                return index
            else:
                index += 1
        return None

    def get_device(self, device_name) -> Ble | None:
        for device in self._ble_list:
            if device_name in device.getDeviceName():
                return device
        return None

    def cancel_task(self, task_name) -> asyncio.Task | None:
        for task in asyncio.all_tasks():
            if task.get_name() == task_name:
                task.cancel()
                return None
