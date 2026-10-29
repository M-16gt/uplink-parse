from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast, get_args

from uplink_parse.core._generics import (
    StrategyGeneric,
    attr_name,
    output_data_from_func,
)
from uplink_parse.core.exceptions import ResponseParsingError
from uplink_parse.core.strategies.accessor import ResponseAccessor
from uplink_parse.core.tasks.compat import await_or_return


# TODO: Переделать Strategy.read_response, чтобы было более удобно пользоваться
# TODO: исключениями из правил.
class Strategy(
    StrategyGeneric[output_data_from_func, attr_name], check_typevars=("attr_name",)
):
    __slots__ = ()

    async def __call__(
        self,
        response: Any,
        *,
        read_params: Mapping[str, Any] | None = None,
        transform_params: Mapping[str, Any] | None = None,
    ) -> output_data_from_func:
        """``read_params`` уходят в ``read_response`` (вызов ``response.json()``
        и т.п.), ``transform_params`` — в ``transform``. Это разные этапы и
        разные аргументы: смешивать их нельзя."""
        try:
            raw = await self.read_response(response, **(read_params or {}))
            return self.transform(raw, **(transform_params or {}))
        except Exception as exc:
            raise ResponseParsingError(
                f"Failed to parse response: {exc}",
                details={"strategy": self.__class__.__name__},
                source=self.__class__.__name__,
            ) from exc

    async def read_response(self, response: Any, **params: Any) -> Any:
        attrs = get_args(self.config_types["attr_name"])
        return await await_or_return(
            ResponseAccessor.get_any(response, *attrs, call_params=params)
        )

    def transform(self, raw: Any, **params: Any) -> output_data_from_func:
        return cast(output_data_from_func, raw)
