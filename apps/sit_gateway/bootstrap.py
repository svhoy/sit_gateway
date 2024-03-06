# Standard Library
import inspect

from apps.sit_gateway.service_layer import messagebus, uow
from apps.sit_gateway.service_layer.handler import command_handler, event_handler


def bootstrap(uow: uow.UnitOfWork, ws, gateway):
    dependencies = {"uow": uow, "ws": ws, "gateway": gateway}

    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in event_handler.EVENT_HANDLER.items()
    }

    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in command_handler.COMMAND_HANDLER.items()
    }

    return messagebus.MessageBus(
        uow, injected_event_handlers, injected_command_handlers
    )


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)
