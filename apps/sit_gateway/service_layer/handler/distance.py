# Standard Library
import asyncio

from .handler import AbstractHandler


class DistanceHandler(AbstractHandler):
    async def msg_handler(self, data, setup):
        match data:
            case {"state": "start", "test_id": test_id, **rest}: #pylint: disable=unused-variable
                self.setup_dict = setup
                await self.send_setup()
                await asyncio.sleep(5.0)
                await self.start_measurement(test_id)
            case {"state": "stop", **rest}: #pylint: disable=unused-variable
                await self.stop_measurement()
                await asyncio.sleep(5.0)
                await self.send_setup()
                self.setup_dict = {
                    "initiator_device": "",
                    "responder_device": [],
                }

    async def start_measurement(self, test_id: int | None):
        self.test_id = test_id
        command = {"type": "measurement_msg", "command": "start"}
        for device in self.setup_dict["responder_device"]:
            await self.gateway.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
                command,
                device,
            )
        await self.gateway.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
            command,
            self.setup_dict["initiator_device"],
        )
        self.distance_notify_task = self.gateway.taskGroup.create_task(
            self.gateway.enable_notify(
                self.setup_dict["initiator_device"], self.distance_notify
            ),
            name="Notify Task",
        )

    async def stop_measurement(self):
        self.test_id = None
        command = {"type": "measurement_msg", "command": "stop"}
        for device in self.setup_dict["responder_device"]:
            await self.gateway.ble_send_json(
                "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
                command,
                device,
            )
        await self.gateway.ble_send_json(
            "6ba1de6b-3ab6-4d77-9ea1-cb6422720003",
            command,
            self.setup_dict["initiator_device"],
        )
        if self.distance_notify_task is not None:
            self.distance_notify_task.cancel()
