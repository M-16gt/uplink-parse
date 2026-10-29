from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_MISSING: Any = object()


# TODO: Добавить поддержку ("method", ("request", "method"))
# TODO: или ("method", "request.method")
class ResponseAccessor:
    @staticmethod
    def _get(
        response: Any, attr: str, call_params: Mapping[str, Any] | None = None
    ) -> Any:
        value = getattr(response, attr)
        return value(**(call_params or {})) if callable(value) else value

    @staticmethod
    def get_any(
        response: Any,
        *attrs: str,
        call_params: Mapping[str, Any] | None = None,
        default: Any = _MISSING,
    ) -> Any:
        """Значение первого существующего атрибута ``attrs``.

        Если атрибут вызываемый (``response.json``), он вызывается с
        ``call_params``; если нет (``response.status_code``) — отдаётся как
        есть, ``call_params`` в этом случае не используются. Если нет ни
        одного атрибута — ``default``, а без него ``AttributeError``.
        """
        for attr in attrs:
            if hasattr(response, attr):
                return ResponseAccessor._get(response, attr, call_params)

        if default is not _MISSING:
            return default
        raise AttributeError(
            f"Response {type(response).__qualname__} has none of "
            f"the attributes: {attrs}"
        )
