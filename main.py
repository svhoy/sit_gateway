#!/usr/bin/env python

# Standard Library
import asyncio

from contextlib import suppress

# Library
from apps.sit_api.socket import BleWebsocket
from apps.sit_ble.ble import BleGateway


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ble_gateway = BleGateway()
    socket = BleWebsocket(ble_gateway)

    loop.run_until_complete(socket.connect())


if __name__ == "__main__":
    main()
