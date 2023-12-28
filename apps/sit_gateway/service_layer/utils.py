# Standard Library
import asyncio


def cancel_task(task_name: str) -> None:
    for task in asyncio.all_tasks():
        if task.get_name() == task_name:
            task.cancel()
            return None
