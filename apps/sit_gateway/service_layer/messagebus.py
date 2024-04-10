import logging
import logging.config
from apps.sit_gateway.domain import commands, events



LOG_CONFIG_PATH = "settings/logging.conf"

logging.config.fileConfig(LOG_CONFIG_PATH)
# create logger
logger = logging.getLogger("messagebus")


class MessageBus:
    def __init__(self, uow, event_handlers, command_handlers):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue = []

    async def handle(self, message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                await self.handle_event(message)
            elif isinstance(message, commands.Command):
                logger.debug(message)
                await self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command") #pylint: disable=broad-exception-raised

    async def handle_event(self, event):
        handlers = self.event_handlers[type(event)]
        for handler in handlers:
            await handler(event)
            # self.queue.extend(self.uow.collect_new_events())

    async def handle_command(self, command):
        handler = self.command_handlers[type(command)]
        # for handler in handlers:
        await handler(command)
        # self.queue.extend(self.uow.collect_new_events())
