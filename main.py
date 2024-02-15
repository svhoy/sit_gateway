#!/usr/bin/env python

# Standard Library
import asyncio
import logging
import logging.config

# Library
from apps.sit_gateway import bootstrap
from apps.sit_gateway.entrypoint import websocket
from apps.sit_gateway.gateway import SITGateway
from apps.sit_gateway.service_layer import uow
from apps.sit_gateway.service_layer.utils import cancel_task

LOG_CONFIG_PATH = "settings/logging.conf"

# Load logging configuration
logging.config.fileConfig(LOG_CONFIG_PATH)
logger = logging.getLogger("main")

gateway = SITGateway()
ws = websocket.Websocket()
bus = bootstrap.bootstrap(uow.UnitOfWork(), ws, gateway)


async def main():
    """
    Main function of the application. 
    It creates a TaskGroup to run multiple asynchronous tasks concurrently.
    It sets the dependencies for the gateway and creates the main Websocket task.
    It also handles exceptions and performs cleanup when the application is stopped.
    """
    async with asyncio.TaskGroup() as tg:
        gateway.set_dependencies(tg, bus)
        try:
            task = tg.create_task(ws.connect(bus), name="Websocket Main Task")
            await task
        except KeyboardInterrupt:
            logger.info("User stopped program.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            logger.info("Disconnecting...")
            cancel_task("Notify Task")
            cancel_task("Websocket Main Task")
            await gateway.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
