from typing import Any

from src.uplink_parse.core.tasks.compat import to_runnable
from src.uplink_parse.core.tasks.task_strategy import BaseTaskStrategy


def _extract_name(
    owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
) -> dict[str, Any]:
    return {"name": list(base.get_registered(owner.__class__, **kwargs))}


def _extract_url(
    owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
) -> dict[str, Any]:
    return {"url": [getattr(owner, n) for n in acc["name"]]}


def _extract_coroutine_or_func(
    owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
) -> dict[str, Any]:
    return {"coroutine_or_func": to_runnable(*acc["url"])}


def _extract_strategy(
    owner: Any, base: Any, acc: dict[str, Any], kwargs: dict[str, Any]
) -> dict[str, Any]:
    return {
        "strategy": [BaseTaskStrategy.get_strategy(c) for c in acc["coroutine_or_func"]]
    }
