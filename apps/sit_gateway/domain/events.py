# pylint: disable=R0801
# Standard Library
from dataclasses import asdict, dataclass
from json import dumps
from turtle import distance


@dataclass
class Event:  # pylint: disable=R0801
    @property
    def __dict__(self):
        buf_dict = {}
        buf_dict["type"] = self.__class__.__name__
        buf_dict["data"] = asdict(self)
        return buf_dict

    @property
    def json(self):
        return dumps(self.__dict__)


@dataclass
class BleDeviceConnected(Event):
    device_id: str


@dataclass
class BleDeviceConnectFailed(Event):
    device_id: str
    reason: str = ""


@dataclass
class BleDeviceConnectError(Event):
    device_id: str
    reason: str = ""


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
    time_round_1: float
    time_round_2: float
    time_reply_1: float
    time_reply_2: float
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
    measurement: int  # pylint: disable=R0801
    distance: float
    time_round_1: float
    time_round_2: float
    time_reply_1: float
    time_reply_2: float
    nlos: int
    rssi: float
    fpi: float


@dataclass
class CalibrationMeasurement(Event):
    calibration_id: int
    initiator: str
    responder: str
    measurement_type: str
    sequence: int
    measurement: int  # pylint: disable=R0801
    distance: float
    time_round_1: float
    time_round_2: float
    time_reply_1: float
    time_reply_2: float
    nlos: int
    rssi: float
    fpi: float


@dataclass
class SimpleCalibrationMeasurement(Event):
    calibration_id: int
    sequence: int
    measurement: int
    devices: list[str]
    time_m21: float = 0.0
    time_m31: float = 0.0
    time_a21: float = 0.0
    time_a31: float = 0.0
    time_b21: float = 0.0
    time_b31: float = 0.0
    time_tc_i: float = 0.0
    time_tc_ii: float = 0.0
    time_tb_i: float = 0.0
    time_tb_ii: float = 0.0
    time_round_1: float = 0.0
    time_round_2: float = 0.0
    time_reply_1: float = 0.0
    time_reply_2: float = 0.0
    distance: float = 0.0


@dataclass
class CalibrationMeasurementFinished(Event):
    calibration_id: int


@dataclass
class CalibrationSimpleMeasurementFinished(Event):
    calibration_id: int


@dataclass
class CalibrationCalFinished(Event):
    pass


@dataclass
class PositionMeasurement(Event):
    pass


@dataclass
class TestMeasurementFinished(Event):
    test_id: int
