#!/usr/bin/env python

# Standard Library
import asyncio

# Library
from apps.sit_gateway import bootstrap
from apps.sit_gateway.entrypoint import websocket
from apps.sit_gateway.gateway import SITGateway
from apps.sit_gateway.service_layer import uow
from apps.sit_gateway.service_layer.utils import cancel_task


gateway = SITGateway()
ws = websocket.Websocket()
bus = bootstrap.bootstrap(uow.UnitOfWork(), ws, gateway)


async def main():
    async with asyncio.TaskGroup() as tg:
        gateway.set_dependencies(tg, bus)
        try:
            task = tg.create_task(ws.connect(bus), name="Websocket Main Task")
            await task
        except KeyboardInterrupt:
            print()
            print("User stopped program.")
        finally:
            print("Disconnecting...")
            cancel_task("Notify Task")
            cancel_task("Websocket Main Task")
            await gateway.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
