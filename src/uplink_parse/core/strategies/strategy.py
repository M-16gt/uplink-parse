from __future__ import annotations

from typing import Any, cast, get_args

from uplink_parse.core._generics import (
    StrategyGeneric,
    attr_name,
    output_data_from_func,
)
from uplink_parse.core.exceptions import ResponseParsingError
from uplink_parse.core.strategies.accessor import ResponseAccessor
from uplink_parse.core.tasks.compat import await_or_return


class Strategy(StrategyGeneric[output_data_from_func, attr_name]):
    __slots__ = ()

    async def __call__(self, response: Any, **params: Any) -> output_data_from_func:
        attrs = get_args(self.config_types["attr_name"])
        try:
            return self.transform(
                await await_or_return(ResponseAccessor.get_any(response, *attrs)),
                **params,
            )
        except Exception as exc:
            raise ResponseParsingError(
                f"Failed to parse response: {exc}",
                details={"strategy": self.__class__.__name__},
                source=self.__class__.__name__,
            ) from exc

    def transform(self, raw: Any, **params: Any) -> output_data_from_func:
        return cast(output_data_from_func, raw)
