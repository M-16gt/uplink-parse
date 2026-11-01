"""
Уровень 2: объект ответа — ResponseInfo и превращение сырого ответа в ctx.response
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

import attrs

from uplink_parse.core._generics import strategy, strategy_rt
from uplink_parse.core.parse.obj import _ParseObj
from uplink_parse.core.strategies.accessor import AttrPath, ResponseAccessor
from uplink_parse.core.utils.ctx import ctx
from uplink_parse.core.utils.singleton import get_instance


def _auto_field(
    sources: tuple[AttrPath, ...], normalize: Callable[[Any], Any], **kwargs: Any
) -> Any:
    def factory() -> Any:
        return normalize(
            ResponseAccessor.get_any(ctx.response_raw, *sources, default=None)
        )

    return attrs.field(
        default=attrs.Factory(factory),
        metadata={"sources": sources, "normalize": normalize},
        **kwargs,
    )


def _url(value: Any) -> str | None:
    result = str(value)
    try:
        parsed = urlsplit(result)
    except ValueError:
        return None
    return result if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _status_code(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _method(value: Any) -> str | None:
    return value.upper() if isinstance(value, str) else None


@attrs.define(frozen=True, slots=True, kw_only=True)
class ResponseInfo:
    url: str | None = _auto_field(("url", "geturl"), _url)
    status_code: int | None = _auto_field(
        ("status_code", "status", "code", "getcode"), _status_code
    )
    method: str | None = _auto_field(
        ("method", "request.method", "request_info.method"), _method
    )


class _ResponseObj(_ParseObj[strategy, strategy_rt]):
    async def parse_response(
        self,
        *,
        strategy_params: Mapping[str, Any] | None = None,
        read_params: Mapping[str, Any] | None = None,
    ) -> Any:
        """Превратить ``ctx.response_raw`` в ``ctx.response``.

        Параметры из ``storage.config``; переданные здесь дополняют их
        только для этого вызова.
        """
        config = self.storage.config.merged(
            strategy_params=strategy_params, read_params=read_params
        )
        return await get_instance(self.config_types["strategy"])(
            ctx.response_raw,
            read_params=config.read_params,
            transform_params=config.strategy_params,
        )

    @staticmethod
    def use_parse_response() -> bool:
        return bool(getattr(ctx.response_raw, "status_code", None))
