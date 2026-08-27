from __future__ import annotations

import contextvars
from typing import Any, Literal

from src.uplink_parse.core._dataclasses import ScraperCtxData
from src.uplink_parse.core.exceptions import NoActiveContextError

_cv_builder: contextvars.ContextVar[Any] = contextvars.ContextVar(
    __package__ + ".builder", default=None
)

_cv_ctx: contextvars.ContextVar[ScraperCtxData | None] = contextvars.ContextVar(
    __package__ + ".ctx", default=None
)


class CtxProxy:
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


ctx = CtxProxy()


class ScraperCtx:
    def __init__(self, **kwargs: Any) -> None:
        builder = _cv_builder.get()
        if builder is not None:
            _cv_builder.reset(builder.token_ctx)
        self.data = ScraperCtxData(**kwargs | {"builder": builder})
        self.token: contextvars.Token[Any] | None = None

    def __enter__(self) -> ScraperCtxData:
        self.token = _cv_ctx.set(self.data)
        return self.data

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        if self.token is not None:
            _cv_ctx.reset(self.token)
        return False
