#!/usr/bin/env python

# Standard Library
import asyncio

from contextlib import suppress

# Library
from apps.sit_api.socket import BleWebsocket
from apps.sit_ble.ble import BleGateway


async def main():
    ble_gateway = BleGateway()
    socket = BleWebsocket(ble_gateway)
    try:
        task = asyncio.create_task(socket.connect())
        await task
        # # TODO ensure_future is deprecated find other solution
        # asyncio.ensure_future(device.manager(test_id))
        # asyncio.ensure_future(main())
        # loop.run_forever()
    except KeyboardInterrupt:
        print()
        print("User stopped program.")
    finally:
        print("Disconnecting...")
        await ble_gateway.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
