from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: Путь к атрибуту: ``"request.method"`` и ``("request", "method")`` равнозначны.
AttrPath = str | tuple[str, ...]

_MISSING: Any = object()


def _resolve(obj: Any, path: AttrPath) -> Any:
    for name in path.split(".") if isinstance(path, str) else path:
        obj = getattr(obj, name, _MISSING)
        if obj is _MISSING:
            break
    return obj


class ResponseAccessor:
    @staticmethod
    def get_any(
        response: Any,
        *paths: AttrPath,
        call_params: Mapping[str, Any] | None = None,
        default: Any = _MISSING,
    ) -> Any:
        """Значение первого существующего пути из ``paths``.

        Путь — имя атрибута, цепочка через точку или кортеж имён. Если
        найденное значение вызываемое (``response.json``), оно вызывается с
        ``call_params``; если нет — отдаётся как есть (параметры не нужны).
        Если нет ни одного пути — ``default``, а без него ``AttributeError``.
        """
        for path in paths:
            value = _resolve(response, path)
            if value is not _MISSING:
                return value(**(call_params or {})) if callable(value) else value

        if default is not _MISSING:
            return default
        raise AttributeError(
            f"Response {type(response).__qualname__} has none of "
            f"the attributes: {paths}"
        )
