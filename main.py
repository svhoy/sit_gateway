#!/usr/bin/env python

# Standard Library
import asyncio

# Library
from apps.sit_gateway.sit_gateway import SITGateway


async def main():
    async with asyncio.TaskGroup() as tg:
        gateway = SITGateway(tg)
        try:
            task = tg.create_task(
                gateway.start_gateway(), name="Gateway Main Task"
            )
            await task
        except KeyboardInterrupt:
            print()
            print("User stopped program.")
        finally:
            print("Disconnecting...")
            await gateway.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
