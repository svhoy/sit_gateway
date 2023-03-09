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
logger = logging.getLogger("device_socket")

HOST = "ws://192.168.0.101:8000/"


class BleWebsocket:
    def __init__(self, ble_gateway) -> None:
        # self._auth = Authenticator()
        # self._auth.login()
        self.ble_gateway = ble_gateway
        self._distance_notify_task = None

    async def connect(self):
        uri = HOST + "ws/ble-devices/"
        async for websocket in websockets.connect(uri):
            self.websocket = websocket
            await self.send_websocket_connection()
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
                                if self.ble_gateway.isConnected():
                                    connection = "complete"
                                    device_name = scan["device_name"]
                                else:
                                    connection = "error"
                                    device_name = ""

                                await self.send_ble_connection_msg(
                                    websocket,
                                    connection,
                                    device_name,
                                )
                                await asyncio.sleep(5.0)
                                command = 5
                                await self.ble_gateway.write_command(
                                    command.to_bytes(1, byteorder="big")
                                )
                                self._distance_notify_task = (
                                    asyncio.create_task(self.enable_notify())
                                )
                                await self._distance_notify_task
                            else:
                                await self.send_ble_connection_msg(
                                    websocket,
                                    "notFound",
                                    "",
                                )
                        case {"type": "connection_ping"}:
                            await self.send_websocket_ping()

            except websockets.ConnectionClosedError as e:
                logger.error(e)
                logger.error("Connection is closed, try reconnect")
                continue

    async def send_websocket_connection(self):
        await self.websocket.send(
            json.dumps(
                {
                    "type": "connection_register",
                    "device_id": "PI_Home",
                }
            )
        )

    async def send_websocket_ping(self):
        await self.websocket.send(
            json.dumps(
                {
                    "type": "connection_ping",
                    "device_id": "PI_Home",
                }
            )
        )

    async def send_ble_connection_msg(self, websocket, connection, device_name):
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
            if device.name == device_name:
                logger.info("{}: {}".format(device.name, device.address))
                logger.info("UUIDs: {}".format(device.metadata["uuids"]))
                asyncio.create_task(self.ble_gateway.connect_device(device))
                await asyncio.sleep(5.0)
                return True
        return False

    async def scan(self) -> list[BLEDevice]:
        return await self.ble_gateway.scan(20)

    async def enable_notify(self):
        enable_notify = False
        while 1:
            if self.ble_gateway.isConnected() and not enable_notify:
                await self.ble_gateway.getNotification(self)
                enable_notify = True
            await asyncio.sleep(1)

    async def got_distance(self, distance):
        print(distance)
        await self.send_distance_msg(distance)

    async def send_distance_msg(self, distance):
        await self.websocket.send(
            json.dumps({"type": "distance_msg", "distance": distance})
        )
