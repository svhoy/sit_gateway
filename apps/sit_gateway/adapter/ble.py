# Standard Library
import asyncio
import logging
import logging.config
import struct

from typing import Callable

# Third Party
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from apps.sit_gateway.adapter.exceptions import BleDataException

from apps.sit_gateway.domain.data import MsgData


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_ble")


class Ble:
    def __init__(self, gateway) -> None:
        self._gateway = gateway

        self._client: BleakClient | None
        self._is_connected: bool = False
        self._connected_device: BLEDevice | None
        self._callback: Callable

    def _set_client(self, device: BLEDevice):
        self._client = BleakClient(device.address, self._on_disconnect)
        self._connected_device = device

    async def connect_device(self, device: BLEDevice):
        if self._is_connected:
            return
        self._set_client(device=device)
        logger.info(f"Im Connector {device.name}: {device.address}")
        try:
            await self._client.connect()
            self._is_connected = self._client.is_connected
            if self._is_connected:
                logger.info(f"Connected to {device.name}")
                for service in self._client.services:
                    logger.info(f"Services: {service}")
                    for char in service.characteristics:
                        logger.info(f"Char: {char}")
                while True:
                    if not self._is_connected:
                        break
                    await asyncio.sleep(5.0)
        except Exception as e:
            logger.error(f"Exeption: {e}")
            self._connected_device = None
            self._client = None

    async def disconnect_device(self):
        await self._client.disconnect()
        self._is_connected = False

    async def cleanup(self):
        if self._client is not None:
            await self.disconnect_device()

    async def _on_disconnect(self, client: BleakClient):
        logger.info(f"Disconnected from {self._connected_device.name}!")
        self._connected_device = None
        self._is_connected = False

    async def write_command(self, uuid: str, byte_data):
        try:
            await self._client.write_gatt_char(uuid, byte_data)
            logger.info(f"Send {byte_data} to Periphal")
        except Exception as e:
            logger.error(f"Exeption: {e}")

    async def get_notification(self, uuid: str, callback: Callable) -> None:
        self._callback = callback
        await self._client.start_notify(uuid, self.on_distance_notification)

    async def on_distance_notification(self, sender: BleakGATTCharacteristic, data: bytearray):
        # Datatype 15 char[] (c string) and f->float and I->uint32_t and H->uint8_t
        msg_structure = "15s 15s H I I f f f f f"
        msg_structure_all = "15s 15s H I I f f f f f f f I H"
        logger.debug(f"MSG Structure: {struct.calcsize(msg_structure)}")
        logger.debug(f"All MSG Structure: {struct.calcsize(msg_structure_all)}")
        logger.debug(f"Data Lenght: {len(data)}")
        try:
            if (struct.calcsize(msg_structure)) == len(data):
                msg_data_buf = struct.unpack(
                    msg_structure, data
                )
                msg_data = MsgData(
                    msg_type=msg_data_buf[0].decode("utf-8"),
                    state=msg_data_buf[1].decode("utf-8"),
                    responder=msg_data_buf[2],
                    sequence=msg_data_buf[3],
                    measurement=msg_data_buf[4],
                    distance=msg_data_buf[5],
                    time_round_1=msg_data_buf[6],
                    time_round_2=msg_data_buf[7],
                    time_reply_1=msg_data_buf[8],
                    time_reply_2=msg_data_buf[9],
                )
            elif (struct.calcsize(msg_structure_all)) == len(data):
                msg_data_buf = struct.unpack(
                    msg_structure_all, data
                )
                msg_data = MsgData(
                    msg_type=msg_data_buf[0].decode("utf-8"),
                    state=msg_data_buf[1].decode("utf-8"),
                    responder=msg_data_buf[2],
                    sequence=msg_data_buf[3],
                    measurement=msg_data_buf[4],
                    distance=msg_data_buf[5],
                    time_round_1=msg_data_buf[6],
                    time_round_2=msg_data_buf[7],
                    time_reply_1=msg_data_buf[8],
                    time_reply_2=msg_data_buf[9],
                    nlos=msg_data_buf[13],
                    rssi=msg_data_buf[10],
                    fpi=msg_data_buf[11],
                )
            else: 
                raise BleDataException(f"Data length not correct: {len(data)}")
        except struct.error as e:
            logger.error(f"Execption - {e}")
        # msg_type = msg_type_b.decode("utf-8")
        # state = state_b.decode("utf-8")
        # logger.debug("From Handle {} Msg_Type: {}".format(sender, msg_type))
        # logger.debug("From Handle {} Sequence: {}".format(sender, sequence))
        # logger.debug(
        #     "From Handle {} Measurements: {}".format(sender, measurements)
        # )
        # logger.debug("From Handle {} Distance: {}".format(sender, distance))
        # logger.debug("From Handle {} NLOS: {}".format(sender, nlos))
        # logger.debug("From Handle {} RSSI: {}".format(sender, rssi))
        # logger.debug("From Handle {} FPI: {}".format(sender, fpi))
        await self._callback(
            msg_data
        )

    def is_connected(self):
        return self._is_connected

    def get_device_name(self) -> str:
        if self._connected_device is not None:
            return self._connected_device.name
        logger.info("No Device connected")
        return ""
