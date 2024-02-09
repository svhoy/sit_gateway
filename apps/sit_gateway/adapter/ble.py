# Standard Library
import asyncio
import logging
import logging.config
import struct

from typing import Callable

# Third Party
from bleak import BleakClient
from bleak.backends.device import BLEDevice



LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_ble")


class Ble:
    def __init__(self, gateway) -> None:
        self._gateway = gateway

        self._client: BleakClient
        self._isConnected: bool = False
        self._connected_device: BLEDevice

    def _set_client(self, device: BLEDevice):
        self._client = BleakClient(device.address, self._on_disconnect)
        self._connected_device = device

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
            self._connected_device = None
            self._client = None

    async def disconnect_device(self):
        await self._client.disconnect()
        self._isConnected = False

    async def cleanup(self):
        if self._client is not None:
            await self.disconnect_device()

    async def _on_disconnect(self, client: BleakClient):
        logger.info(f"Disconnected from {self._connected_device.name}!")
        self._connected_device = None
        self._isConnected = False

    async def write_command(self, uuid: str, byte_data):
        try:
            await self._client.write_gatt_char(uuid, byte_data)
            logger.info(f"Send {byte_data} to Periphal")
        except Exception as e:
            logger.error("Exeption: {}".format(e))

    async def getNotification(self, uuid: str, callback: Callable) -> None:
        self._callback = callback
        await self._client.start_notify(uuid, self.on_distance_notification)

    async def on_distance_notification(self, sender: int, data: bytearray):
        logger.info(f"Daten in Notfiy Function: {data}")
        
        try:
            logger.info(struct.calcsize("15s 15s H I I f H f f"))
            logger.info(len(data))
            (
                msg_type_b,
                state_b,
                responder,
                sequence,
                measurements,
                distance,
                nlos,
                rssi,
                fpi,
            ) = struct.unpack(
                "15s 15s H I I f H f f", data
            )  # Datatype 15 char[] (c string) and f->float and I->uint32_t and H->uint8_t
            logger.info("Test")
        except Exception as e:
            logger.error(f"Execption: {e}")
        msg_type = msg_type_b.decode("utf-8")
        state = state_b.decode("utf-8")
        # logger.info("From Handle {} Msg_Type: {}".format(sender, msg_type))
        # logger.info("From Handle {} Sequence: {}".format(sender, sequence))
        # logger.info(
        #     "From Handle {} Measurements: {}".format(sender, measurements)
        # )
        # logger.debug("From Handle {} Distance: {}".format(sender, distance))
        # logger.debug("From Handle {} NLOS: {}".format(sender, nlos))
        # logger.debug("From Handle {} RSSI: {}".format(sender, rssi))
        # logger.debug("From Handle {} FPI: {}".format(sender, fpi))
        await self._callback(
            responder, sequence, measurements, distance, nlos, rssi, fpi
        )

    def isConnected(self):
        return self._isConnected

    def getDeviceName(self) -> str:
        if self._connected_device is not None:
            return self._connected_device.name
