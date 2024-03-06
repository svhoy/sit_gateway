
class BleDataException(Exception):
    def __init__(self, message: str = "Ble data not confirm expected data format") -> None:
        super().__init__(message)
