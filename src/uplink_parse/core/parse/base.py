from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

from uplink_parse.core.response_info import ResponseInfo

if TYPE_CHECKING:
    from typing_extensions import Self
else:
    try:
        from typing import Self
    except ImportError:  # Python 3.10
        from typing_extensions import Self

from uplink_parse.core.parseable import Parseable
from uplink_parse.core.utils.singleton import get_instance

try:
    from uplink import response_handler
except ImportError:

    def response_handler(handler: Any, requires_consumer: bool = False) -> Any:
        return handler


from uplink_parse.core._dataclasses import Storage
from uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from uplink_parse.core.parse.factory import configure_parse
from uplink_parse.core.parse.follow import FollowMixin
from uplink_parse.core.parse.runner import execute_parse, run_parse
from uplink_parse.core.utils.ctx import ctx


class _ParseObj(ParseGeneric[strategy, strategy_rt]):
    scraper: Self
    response: strategy_rt
    response_raw: Any
    response_info: ResponseInfo
    consumer: Any
    request: Any

    def __getattr__(self, item: str) -> Any:
        return getattr(ctx, item)


class BaseParse(
    Parseable,
    FollowMixin,
    _ParseObj[strategy, strategy_rt],
    check_typevars=("strategy",),
):
    storage: Storage

    def __new__(
        cls,
        *,
        is_decorator: bool = True,
        strategy_params: dict[str, Any] | None = None,
    ) -> Any:
        instance = super().__new__(cls)
        configure_parse(instance, strategy_params)
        return instance if not is_decorator else parse(instance)

    async def _call_async(self, *args: Any, **kwargs: Any) -> Any:
        return await execute_parse(self, *args)

    @functools.wraps(_call_async)
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return run_parse(self._call_async(*args, **kwargs))

    async def parse_response(self, **strategy_params: Any) -> Any:
        return await get_instance(self.config_types["strategy"])(
            ctx.response_raw, **strategy_params
        )

    @staticmethod
    def use_parse_response() -> bool:
        return bool(getattr(ctx.response_raw, "status_code", None))


def parse(cls: BaseParse[Any, Any]) -> Any:
    return response_handler(cls.__call__, requires_consumer=True)
