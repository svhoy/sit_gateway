# Standard Library
import abc
import asyncio


class AbstractHandler(abc.ABC):
    def __init__(self, gateway) -> None:
        self.gateway = gateway

        self.test_id: int | None = None
        self.distance_notify_task: asyncio.Task | None = None
        self.setup_dict: dict = {
            "initiator_device": "",
            "responder_device": [],
        }

    async def msg_handler(self, data, setup):
        raise NotImplementedError

    async def send_setup(self):
        command = {
            "type": "setup_msg",
            "initiator_device": self.setup_dict["initiator_device"],
            "initiator": 1,
            "responder_device": self.setup_dict["responder_device"],
            "responder": len(self.setup_dict["responder_device"]),
        }
        await self.gateway.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
            command,
            self.setup_dict["initiator_device"],
        )
        for device in self.setup_dict["responder_device"]:
            await self.gateway.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720004",
                command,
                device,
            )

    async def start_measurement(self, test_id: int | None):
        raise NotImplementedError

    async def stop_measurement(self):
        raise NotImplementedError

    async def distance_notify(self):
        raise NotImplementedError
