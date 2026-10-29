from __future__ import annotations

from typing import TYPE_CHECKING, Any

from uplink_parse.core._dataclasses import ParseConfig, Storage, build_parse_meta
from uplink_parse.core.hooks import class_hooks_of
from uplink_parse.core.tasks.task_runner import TaskRunner

if TYPE_CHECKING:
    from uplink_parse.core.parse.base import BaseParse


def configure_parse(instance: BaseParse[Any, Any], config: ParseConfig) -> None:
    instance.storage = Storage(
        parse_funcs_meta=build_parse_meta(instance),
        task_runner=TaskRunner(
            batch_size=config.batch_size,
            use_thread_for_sync=config.use_thread_for_sync,
            class_hooks=class_hooks_of(instance),
        ),
        config=config,
    )
