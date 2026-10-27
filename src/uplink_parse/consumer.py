# TODO: Сделать отдельной библиотекой

from collections.abc import Mapping
from typing import Any, ClassVar

from uplink import (
    Body,
    FieldMap,
    HeaderMap,
    PartMap,
    QueryMap,
    Url,
    form_url_encoded,
    multipart,
)
from uplink import (
    Consumer as _Consumer,
)
from uplink import json as json_request
from uplink.commands import HttpMethodFactory

__all__ = ["Consumer"]

_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}


def _template(self: Any, url: Url, params: QueryMap, headers: HeaderMap) -> None: ...


def _template_json(
    self: Any, url: Url, params: QueryMap, headers: HeaderMap, body: Body
) -> None: ...


def _template_form(
    self: Any, url: Url, params: QueryMap, headers: HeaderMap, body: FieldMap
) -> None: ...


def _template_multipart(
    self: Any, url: Url, params: QueryMap, headers: HeaderMap, body: PartMap
) -> None: ...


_KINDS = {
    None: (_template, None),
    "json": (_template_json, json_request),
    "form": (_template_form, form_url_encoded),
    "multipart": (_template_multipart, multipart),
}


class Consumer(_Consumer):  # type: ignore[misc]
    """Uplink consumer that can send requests without declaring an endpoint."""

    _definitions: ClassVar[dict[tuple[str, str | None], Any]] = {}

    @classmethod
    def _definition(cls, method: str, kind: str | None) -> Any:
        key = (method, kind)
        if key not in cls._definitions:
            template, decorator = _KINDS[kind]
            builder = HttpMethodFactory(method)()(template)
            if decorator is not None:
                builder = decorator(builder)
            cls._definitions[key] = builder.build()
        return cls._definitions[key]

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Any:
        method = method.upper()
        if method not in _METHODS:
            raise ValueError(f"Unsupported HTTP method: {method}")

        payloads = [
            (kind, body)
            for kind, body in (("json", json), ("form", data), ("multipart", files))
            if body is not None
        ]
        if len(payloads) > 1:
            raise ValueError("Pass only one of json, data or files")
        kind, body = payloads[0] if payloads else (None, None)

        call = self.session.create(self, self._definition(method, kind))
        args = (url, params or {}, headers or {})
        return call(*args, body) if kind is not None else call(*args)
