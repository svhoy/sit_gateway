#!/usr/bin/env python

# Standard Library
import asyncio

# Library
from apps.sit_api.socket import BleWebsocket
from apps.sit_ble.ble import BleGateway


async def main():
    ble_gateway = BleGateway()
    socket = BleWebsocket(ble_gateway)
    try:
        task = asyncio.create_task(socket.connect())
        await task
    except KeyboardInterrupt:
        print()
        print("User stopped program.")
    finally:
        print("Disconnecting...")
        await ble_gateway.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
