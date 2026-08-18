from __future__ import annotations
import contextvars
from typing import Optional

from uplink_parse.core._dataclasses import ScraperCtxData
from uplink_parse.core.exceptions import NoActiveContextError

_cv_builder: contextvars.ContextVar = contextvars.ContextVar(
    __package__ + ".builder", default=None
)

_cv_ctx: contextvars.ContextVar[Optional[ScraperCtxData]] = contextvars.ContextVar(
    __package__ + ".ctx", default=None
)


class CtxProxy:
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

    def __getattr__(self, item):
        return getattr(self._get_data(), item)


ctx = CtxProxy()


class ScraperCtx:
    def __init__(self, **kwargs):
        builder = _cv_builder.get()
        if builder is not None:
            _cv_builder.reset(builder.token_ctx)
        self.data = ScraperCtxData(**kwargs | {"builder": builder})
        self.token: Optional[contextvars.Token] = None

    def __enter__(self) -> ScraperCtxData:
        self.token = _cv_ctx.set(self.data)
        return self.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            _cv_ctx.reset(self.token)
        return False