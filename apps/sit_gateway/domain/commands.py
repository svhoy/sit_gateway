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
    rx_ant_dly: int = 16385
    tx_ant_dly: int = 16385


@dataclass
class StopDistanceMeasurement(Command):
    pass


@dataclass
class StartTestMeasurement(Command):
    test_id: int
    initiator: str
    responder: list[str]
    min_measurement: int
    max_measurement: int
    rx_ant_dly: int = 0
    tx_ant_dly: int = 0


@dataclass
class StartCalibrationMeasurement(Command):
    calibration_id: int
    devices: list[str]
    max_measurement: int
    rx_ant_dly: int = 0
    tx_ant_dly: int = 0


@dataclass
class StartSingleCalibrationMeasurement(Command):
    pass
