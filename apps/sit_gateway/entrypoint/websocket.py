# Standard Library
import importlib.util
import json
import logging
import logging.config
import pkgutil

# Third Party
import websockets.client

# Library
from apps.sit_gateway.domain import commands, events


LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("pi_socket")


class Websocket:
    def __init__(
        self,
        host: str = "ws://192.168.0.101:8000/",
        # host: str = "ws://192.168.137.1:8000/",
        path: str = "ws/sit/1",
    ) -> None:
        # self._auth = Authenticator()
        # self._auth.login()
        self._uri = host + path
        self.dataclasses = self.find_dataclasses_in_directory()

    async def connect(self, bus):
        async for _websocket in websockets.client.connect(self._uri):
            self._websocket = _websocket
            await bus.handle(commands.RegisterWsClient("PI_Home"))
            try:
                # Process messages received on the connection.
                async for text_data in self._websocket:
                    await self.recive(text_data, bus)
            except websockets.ConnectionClosedError as e:
                logger.error(e)
                logger.error("Connection is closed, try reconnect")
                continue
            except websockets.ConnectionClosed as e:
                logger.error(e)
                logger.error("Connection is closed, try reconnect")
                continue

    async def recive(self, data_msg, bus):
        data = json.loads(data_msg)
        logger.info(data)
        try:
            message = self.create_dataclass_instance(
                data["type"], data["data"]
            )
            if not (
                isinstance(message, events.BleDeviceConnected)
                or isinstance(message, events.BleDeviceConnectFailed)
                or isinstance(message, events.BleDeviceConnectError)
            ):
                await bus.handle(message)
        except ValueError as e:
            logger.error(f"Can not create Dataclass: {e}")

    async def send(self, data_msg):
        await self._websocket.send(data_msg)

    def create_dataclass_instance(self, event_type, data):
        data_class = self.dataclasses.get(event_type)
        if data_class:
            instance = data_class(**data)
            return instance
        else:
            raise ValueError("Invalid event type")

    def find_dataclasses_in_directory(self):
        dataclasses = {}
        directory = (
            "apps.sit_gateway.domain"  # Vollständiger Pfad zu den Klassen
        )
        try:
            package = importlib.import_module(directory)
        except ModuleNotFoundError:
            return dataclasses  # Module not found, return empty dict
        print(package)

        for importer, modname, ispkg in pkgutil.walk_packages(
            path=package.__path__, prefix=package.__name__ + "."
        ):
            module = importlib.import_module(modname)
            for name, obj in module.__dict__.items():
                if (
                    isinstance(obj, type)
                    and hasattr(obj, "__annotations__")
                    and hasattr(obj, "__dataclass_fields__")
                ):
                    dataclasses[name] = obj

        return dataclasses

    # Different Messanges send functions

    async def send_distance_msg(
        self, test_id, sequence, distance, nlos, rssi, fpi
    ):
        await self.send(
            json.dumps(
                {
                    "type": "distance_msg",
                    "data": {
                        "state": "scanning",
                        "distance": distance,
                        "test_id": test_id,
                        "sequence": sequence,
                        "nlos": nlos,
                        "rssi": rssi,
                        "fpi": fpi,
                    },
                    "setup": None,
                }
            )
        )