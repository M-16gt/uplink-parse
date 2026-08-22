from __future__ import annotations

from typing import Any, cast, get_args

from src.uplink_parse.core._generics import (
    StrategyGeneric,
    attr_name,
    output_data_from_func,
)
from src.uplink_parse.core.accessor import ResponseAccessor
from src.uplink_parse.core.cached import Cached
from src.uplink_parse.core.compat import await_or_return
from src.uplink_parse.core.exceptions import ResponseParsingError, StrategyError


class Strategy(StrategyGeneric[output_data_from_func, attr_name], Cached):
    async def __call__(self, response: Any) -> output_data_from_func:
        try:
            attrs = get_args(self.config_types["attr_name"])
            if not attrs:
                raise StrategyError(
                    f"{self.__class__.__name__}: attr_name must be a Literal "
                    f"with at least one string argument"
                )

            return self.transform(
                await await_or_return(ResponseAccessor.get_any(response, *attrs))
            )

        except KeyError:
            raise StrategyError from None
        except Exception as exc:
            raise ResponseParsingError(
                f"Failed to parse response: {exc}",
                details={"strategy": self.__class__.__name__},
                source=self.__class__.__name__,
            ) from exc

    def transform(self, raw: Any) -> output_data_from_func:
        return cast(output_data_from_func, raw)
