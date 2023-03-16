# Standard Library
import asyncio
import logging
import logging.config
import struct

# Third Party
from bleak import BleakClient, BleakScanner, BLEDevice
from bleak.exc import BleakError


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("ble_gateway")


class BleGateway:
    def __init__(self) -> None:
        self._client: BleakClient = None
        self._isConnected: bool = False
        self._connected_device: set = set()

    async def scan(self, timeout: float = 10.0) -> list[BLEDevice]:
        _scanner = BleakScanner()
        print("Test2")
        return await _scanner.discover(timeout=timeout)

    def _set_client(self, device: BLEDevice):
        self._client = BleakClient(device.address, self._on_disconnect)
        self._connected_device.add(device)

    async def connect_device(self, device: BLEDevice):
        if self._isConnected:
            return
        self._set_client(device=device)
        logger.info("Im Connector {}: {}".format(device.name, device.address))
        try:
            await self._client.connect()
            self._isConnected = self._client.is_connected
            if self._isConnected:
                logger.info(f"Connected to {device.name}")
                for service in self._client.services:
                    logger.info("Services: {}".format(service))
                    for char in service.characteristics:
                        logger.info("Char: {}".format(char))
                while True:
                    if not self._isConnected:
                        break
                    await asyncio.sleep(5.0)
        except Exception as e:
            logger.error("Exeption: {}".format(e))
            self._connected_device.clear()
            self._client = None

    async def disconnect_device(self):
        await self._client.disconnect()
        self._isConnected = False

    async def cleanup(self):
        if self._client is not None:
            await self.disconnect_device()

    async def _on_disconnect(self, client: BleakClient):
        logger.info(f"Disconnected from {list(self._connected_device)[0]}!")
        self._connected_device.clear()
        self._isConnected = False

    async def write_command(self, byte_data):
        try:
            await self._client.write_gatt_char(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720002", byte_data
            )
            logger.info(f"Send {byte_data} to Periphal")
        except Exception as e:
            logger.error("Exeption: {}".format(e))

    async def getNotification(self, socket):
        self._socket = socket
        await self._client.start_notify(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720001", self.on_notification
        )

    async def on_notification(self, sender: int, data: bytearray):
        distance = struct.unpack("f", data)
        print("From Handle {} Distance: {}".format(sender, distance[0]))
        await self._socket.got_distance(distance[0])

    def isConnected(self):
        return self._isConnected
