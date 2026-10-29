from typing import Any, Callable
from urllib.parse import urlsplit

import attrs

from uplink_parse.core.strategies.accessor import ResponseAccessor
from uplink_parse.core.utils.ctx import ctx


def _auto_field(
    sources: tuple[str, ...], normalize: Callable[[Any], Any], **kwargs: Any
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


# TODO: Добавить поля по типу headers, method, proxies, ...
@attrs.define(frozen=True, slots=True, kw_only=True)
class ResponseInfo:
    url: str | None = _auto_field(("url", "geturl"), _url)
    status_code: int | None = _auto_field(
        ("status_code", "status", "code", "getcode"), _status_code
    )
