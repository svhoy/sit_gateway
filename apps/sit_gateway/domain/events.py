# Standard Library
from dataclasses import asdict, dataclass
from json import dumps


@dataclass
class Event:
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
class BleDeviceConnected(Event):
    device_id: str


@dataclass
class BleDeviceConnectFailed(Event):
    device_id: str
    reason: str = None


@dataclass
class BleDeviceConnectError(Event):
    device_id: str
    reason: str = None


@dataclass
class BleDeviceDisconnected(Event):
    device_id: str


@dataclass
class MeasurementRunning(Event):
    pass


@dataclass
class DistanceMeasurement(Event):
    initiator: str
    sequence: int
    distance: float
    nlos: int
    rssi: float
    fpi: float


@dataclass
class PositionMeasurement(Event):
    pass
