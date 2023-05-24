# Standard Library
import asyncio
import json
import logging
import logging.config

# Third Party
import websockets.client


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_socket")


class Websocket:
    def __init__(
        self,
        gateway,
        host: str = "ws://192.168.0.101:8000/",
        path: str = "ws/ble-devices/",
    ) -> None:
        # self._auth = Authenticator()
        # self._auth.login()
        self._gateway = gateway
        self._uri = host + path

    async def connect(self):
        async for _websocket in websockets.client.connect(self._uri):
            self._websocket = _websocket
            await self.send_websocket_connection_register()
            try:
                # Process messages received on the connection.
                async for text_data in self._websocket:
                    await self.recive(text_data)
            except websockets.ConnectionClosedError as e:
                logger.error(e)
                logger.error("Connection is closed, try reconnect")
                continue
            except websockets.ConnectionClosed as e:
                logger.error(e)
                logger.error("Connection is closed, try reconnect")
                continue

    async def recive(self, data_msg):
        data = json.loads(data_msg)
        logger.info(data)
        match data:
            case {"type": "connection_ping"}:
                await self._gateway.handle_ping_msg()
            case {"type": "scanning_state", "scan": msg}:
                await self._gateway.handle_scanning_msg(msg)
            case {
                "type": "distance_msg",
                "data": data,
            }:
                await self._gateway.handle_distance_msg(data)

    async def send(self, data_msg):
        await self._websocket.send(data_msg)

    # Different Messanges send functions
    async def send_websocket_connection_register(self):
        await self.send(
            json.dumps(
                {
                    "type": "connection_register",
                    "device_id": "PI_Home",
                }
            )
        )

    async def send_websocket_ping(self):
        await self.send(
            json.dumps(
                {
                    "type": "connection_ping",
                    "device_id": "PI_Home",
                }
            )
        )

    async def send_ble_connection_msg(
        self, connection: str, device_name: str = ""
    ):
        await self.send(
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

    async def send_distance_msg(self, test_id, distance):
        await self.send(
            json.dumps(
                {
                    "type": "distance_msg",
                    "data": {
                        "state": "scanning",
                        "distance": distance,
                        "test_id": test_id,
                    },
                }
            )
        )
