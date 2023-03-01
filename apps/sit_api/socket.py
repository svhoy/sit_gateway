# Standard Library
import asyncio
import json
import logging
import logging.config

# Third Party
import websockets

from bleak import BLEDevice


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("ble_gateway")

HOST = "ws://192.168.0.101:8000/"


class BleWebsocket:
    def __init__(self, ble_gateway) -> None:
        # self._auth = Authenticator()
        # self._auth.login()
        self.ble_gateway = ble_gateway

    async def connect(self):
        uri = HOST + "ws/ble-devices/"
        async for websocket in websockets.connect(uri):
            try:
                # Process messages received on the connection.
                async for text_data in websocket:
                    data = json.loads(text_data)
                    match data:
                        case {"type": "scanning_state", "scan": scan} if scan[
                            "state"
                        ] is True:
                            conn_state = await self.connect_ble_device(
                                scan["device_name"]
                            )
                            if conn_state is True:
                                await self.send_connection_msg(
                                    websocket,
                                    "complete",
                                    scan["device_name"],
                                )
                            else:
                                await self.send_connection_msg(
                                    websocket,
                                    "error",
                                    "",
                                )

            except websockets.ConnectionClosedError as e:
                logger.error(e)
                logger.error("Connection is closed, try reconnect")
                continue

    async def send_connection_msg(self, websocket, connection, device_name):
        await websocket.send(
            json.dumps(
                {
                    "type": "scanning_state",
                    "scan": {
                        "state": False,
                        "connection": connection,
                        "device_name": device_name,
                    },
                }
            )
        )

    async def connect_ble_device(self, device_name):
        devices = await self.scan()
        print(devices)
        for device in devices:
            print(f"Test: {device.name}")
            if device.name == device_name:
                logger.info("{}: {}".format(device.name, device.address))
                logger.info("UUIDs: {}".format(device.metadata["uuids"]))
                self.ble_gateway.connect_device()
                return True
        return False

    async def scan(self) -> list[BLEDevice]:
        return await self.ble_gateway.scan(20)
