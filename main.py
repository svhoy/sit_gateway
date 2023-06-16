#!/usr/bin/env python

# Standard Library
import asyncio

# Library
from apps.sit_gateway.sit_gateway import SITGateway


async def main():
    gateway = SITGateway()
    try:
        task = asyncio.create_task(gateway.start_gateway())
        await task
    except KeyboardInterrupt:
        print()
        print("User stopped program.")
    finally:
        print("Disconnecting...")
        await gateway.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
