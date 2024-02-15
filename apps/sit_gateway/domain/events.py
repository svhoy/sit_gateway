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
    responder: str
    sequence: int
    measurement_type: str
    measurement: int
    distance: float
    nlos: int
    rssi: float
    fpi: float


@dataclass
class TestMeasurement(Event):
    test_id: int
    initiator: str
    responder: str
    measurement_type: str
    sequence: int
    measurement: int
    distance: float
    nlos: int
    rssi: float
    fpi: float


@dataclass
class CalibrationMeasurement(Event):
    claibration_id: int
    initiator: str
    responder: str
    measurement_type: str
    sequence: int
    measurement: int
    distance: float
    nlos: int
    rssi: float
    fpi: float


@dataclass
class CalibrationMeasurementFinished(Event):
    calibration_id: int


@dataclass
class CalibrationCalFinished(Event):
    pass


@dataclass
class PositionMeasurement(Event):
    pass
