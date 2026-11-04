from __future__ import annotations

import contextvars
import functools
from collections.abc import Callable
from typing import Any, Literal

import attrs

from uplink_parse.core.exceptions import NoActiveContextError


@attrs.define(slots=False)
class ScraperCtxData:
    response: Any | None = None
    response_raw: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None
    request: Any | None = None
    response_info_factory: Callable[[], Any] | None = None

    @functools.cached_property
    def response_info(self) -> Any:
        """Строится при первом обращении: читают его редко, а стоит заметно."""
        factory = self.response_info_factory
        return factory() if factory is not None else None


#: Запрос, который ``request_auditor`` оставляет для ближайшего ``ScraperCtx``.
#: Лежит в списке-«коробке», а не напрямую: ``ScraperCtx`` забирает его через
#: ``pop()``. ``asyncio.run`` и дочерние задачи работают в копии контекста, но
#: список в копии тот же, поэтому запрос находится и не остаётся лежать в
#: родительском контексте. ``ContextVar.reset(token)`` в таких случаях падает
#: с ``ValueError: ... was created in a different Context``.
_cv_request: contextvars.ContextVar[list[Any] | None] = contextvars.ContextVar(
    __package__ + ".request", default=None
)

_cv_ctx: contextvars.ContextVar[ScraperCtxData | None] = contextvars.ContextVar(
    __package__ + ".ctx", default=None
)


class CtxProxy:
    __slots__ = ()

    response: Any

    @staticmethod
    def _get_data() -> ScraperCtxData:
        data = _cv_ctx.get()
        if data is None:
            raise NoActiveContextError(
                "No active scraper context. "
                "Ensure the call is inside a ScraperCtx manager.",
                source="CtxProxy",
            )
        return data

    def __getattr__(self, item: str) -> Any:
        return getattr(self._get_data(), item)

    def __setattr__(self, item: str, value: Any) -> None:
        setattr(self._get_data(), item, value)


ctx = CtxProxy()


class ScraperCtx:
    def __init__(self, **kwargs: Any) -> None:
        box = _cv_request.get()
        request = box.pop() if box else None
        self.data = ScraperCtxData(**kwargs | {"request": request})
        self.token: contextvars.Token[Any] | None = None

    def __enter__(self) -> ScraperCtxData:
        self.token = _cv_ctx.set(self.data)
        return self.data

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        if self.token is not None:
            _cv_ctx.reset(self.token)
        return False
