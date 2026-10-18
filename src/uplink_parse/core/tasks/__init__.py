from uplink_parse.core.tasks.compat import (
    await_or_return,
)
from uplink_parse.core.tasks.task_runner import TaskRunner
from uplink_parse.core.tasks.task_strategy import BaseTaskStrategy

__all__ = [
    "TaskRunner",
    "BaseTaskStrategy",
    "await_or_return",
]
