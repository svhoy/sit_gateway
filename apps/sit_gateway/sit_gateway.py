# Standard Library
import asyncio
import json
import logging
import logging.config

from .ble import Ble
from .websocket import Websocket


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_socket")


class SITGateway:
    def __init__(self) -> None:
        self._ble: Ble = Ble(self)
        self._socket: Websocket = Websocket(self)

        self._test_id: int | None = None
        self._ble_connection_task: asyncio.Task | None = None
        self._websocket_task: asyncio.Task | None = None
        self._distance_notify_task: asyncio.Task | None = None

    async def start_gateway(self):
        await self.start_websocket()

    async def cleanup(self):
        await self._ble.cleanup()
        if self._distance_notify_task is not None:
            self._distance_notify_task.cancel()
        if self._websocket_task is not None:
            self._websocket_task.cancel()
        if self._ble_connection_task is not None:
            self._ble_connection_task.cancel()

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
            case {"state": False, "connection": "disconnect"}:
                await self.stop_ble_gateway()

    # Handle Distance message
    async def handle_distance_msg(self, data):
        match data:
            case {"state": "start", "test_id": test_id, **rest}:
                await self.start_measurement(test_id)
            case {"state": "stop", **rest}:
                await self.stop_measurement()

    # Bluetooth Connection Manager
    async def start_ble_gateway(self, device_name) -> None:
        conn_state = await self.connect_ble(device_name=device_name)
        await asyncio.sleep(5.0)
        if conn_state is True:
            if self._ble.isConnected():
                connection = "complete"
            else:
                if self._ble_connection_task:
                    self._ble_connection_task.cancel()
                connection = "error"
                device_name = ""
            await self._socket.send_ble_connection_msg(
                connection,
                device_name,
            )
        else:
            await self._socket.send_ble_connection_msg("notFound")

    async def stop_ble_gateway(self) -> None:
        await self._ble.cleanup()
        if self._distance_notify_task:
            self._distance_notify_task.cancel()
        if self._ble_connection_task:
            self._ble_connection_task.cancel()

    async def connect_ble(self, device_name) -> bool:
        devices = await self._ble.scan(20)
        logger.info(devices)
        for device in devices:
            if device.name == device_name:
                logger.info("{}: {}".format(device.name, device.address))
                logger.info("UUIDs: {}".format(device.metadata["uuids"]))
                self.ble_connection_task = asyncio.create_task(
                    self._ble.connect_device(device)
                )
                await asyncio.sleep(5.0)
                return True
        return False

    async def enable_notify(self):
        enable_notify = False
        while 1:
            if self._ble.isConnected() and not enable_notify:
                await self._ble.getNotification(
                    "6ba1de6b-3ab6-4d77-9ea1-cb6422720001"
                )
                enable_notify = True
            await asyncio.sleep(2)

    async def ble_send_json(self, uuid, command):
        json_msg = json.dumps(command).encode("utf-8")
        await self._ble.write_command(uuid, json_msg)

    async def ble_send_int(self, uuid: str, intger: int) -> None:
        await self._ble.write_command(uuid, intger.to_bytes(1, byteorder="big"))

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

    async def distance_notify(self, distance):
        await self._socket.send_distance_msg(self._test_id, distance)
