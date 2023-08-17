# Standard Library
from dataclasses import asdict, dataclass
from json import dumps


@dataclass
class Command:
    @property
    def __dict__(self):
        dict = {}
        dict["type"] = self.__class__.__name__
        dict["data"] = asdict(self)
        return dict

    @property
    def json(self):
        return dumps(self.__dict__)


@dataclass
class StartWebsocket:
    pass


@dataclass
class RegisterWsClient(Command):
    client_id: str


@dataclass
class PingWsConnection(Command):
    pass


@dataclass
class ConnectBleDevice(Command):
    device_id: str


@dataclass
class DisconnectBleDevice(Command):
    device_id: str


@dataclass
class StartDistanceMeasurement(Command):
    initiator: str
    responder: list[str]
    test_id: str | None = None
    min_measurements: int | None = None
    max_measurements: int | None = None


@dataclass
class StopDistanceMeasurement(Command):
    pass
