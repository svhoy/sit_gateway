# Standard Library
import dataclasses
import time


@dataclasses.dataclass
class MsgData:
    msg_type: str
    state: str
    responder: int
    sequence: int
    measurement: int
    distance: float
    time_round_1: float
    time_round_2: float
    time_reply_1: float
    time_reply_2: float
    nlos: int = 0
    rssi: float = 0.0
    fpi: float = 0.0


@dataclasses.dataclass
class SimpleMsgData:
    msg_type: str
    sequence: int
    measurement: int
    time_m21: float
    time_m31: float
    time_a21: float
    time_a31: float
    time_b21: float
    time_b31: float
    time_tc_i: float
    time_tc_ii: float
    time_tb_i: float
    time_tb_ii: float
    time_round_1: float
    time_round_2: float
    time_reply_1: float
    time_reply_2: float
    distance: float
