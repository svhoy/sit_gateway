import dataclasses

@dataclasses.dataclass
class MsgData:
    msg_type: str
    state: str
    responder: int
    sequence: int
    measurement: float
    distance: float
    time_round_1: float
    time_round_2: float
    time_reply_1: float
    time_reply_2: float
    nlos: int = 0
    rssi: float = 0.0
    fpi: float = 0.0
