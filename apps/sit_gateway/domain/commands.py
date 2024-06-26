# Standard Library
from dataclasses import asdict, dataclass
from json import dumps


@dataclass
class Command:  # pylint: disable=R0801
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
    measurement_type: str = "ds_3_twr"
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
    measurement_type: str = "ds_3_twr"
    init_rx_ant_dly: float = 0
    init_tx_ant_dly: float = 0
    resp_rx_ant_dly: float = 0
    resp_tx_ant_dly: float = 0


@dataclass
class StartCalibrationMeasurement(Command):
    calibration_id: int
    devices: list[str]
    max_measurement: int
    measurement_type: str = "ds_3_twr"
    rx_ant_dly: int = 0
    tx_ant_dly: int = 0


@dataclass
class StartSimpleCalibrationMeasurement(Command):
    calibration_id: int
    devices: list[str]
    max_measurement: int
    measurement_type: str = "two_device"
    rx_ant_dly: int = 0
    tx_ant_dly: int = 0


@dataclass
class StartSingleCalibrationMeasurement(Command):
    pass


@dataclass
class StartDebugCalibration(Command):
    calibration_id: int
    devices: list[str]
    measurement_type: str = "simple"
    max_measurement: int = 0
    rx_ant_dly: int = 0
    tx_ant_dly: int = 0
