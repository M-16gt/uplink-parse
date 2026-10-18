from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

from uplink_parse.core._dataclasses import Storage, build_parse_meta
from uplink_parse.core.hooks import class_hooks_of
from uplink_parse.core.tasks.task_runner import TaskRunner
from uplink_parse.core.utils import to_dict

if TYPE_CHECKING:
    from uplink_parse.core.parse.base import BaseParse


def configure_parse(
    instance: BaseParse[Any, Any], strategy_params: dict[str, Any] | None
) -> None:
    instance.storage = Storage(
        parse_funcs_meta=build_parse_meta(instance),
        task_runner=TaskRunner(class_hooks=class_hooks_of(instance)),
    )
    instance.parse_response = functools.partial(  # type: ignore[method-assign]
        instance.parse_response, **to_dict(strategy_params)
    )
