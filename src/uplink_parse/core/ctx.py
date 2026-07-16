from __future__ import annotations
import contextvars
from typing import Optional
from uplink_parse.core._dataclasses import ScraperCtxData
from uplink_parse.core.exceptions import NoActiveContextError

_cv_builder: contextvars.ContextVar = contextvars.ContextVar("uplink_parse.core.builder", default=None)

_cv_ctx: contextvars.ContextVar[Optional[ScraperCtxData]] = contextvars.ContextVar(
    "uplink_parse.core.ctx", default=None
)


class CtxProxy:
    @staticmethod
    def _get_data() -> ScraperCtxData:
        data = _cv_ctx.get()
        if data is None:
            raise NoActiveContextError("No active scraper context.", source="CtxProxy", context=None)
        return data

    def __getattr__(self, item):
        return getattr(self._get_data(), item)


ctx = CtxProxy()


class ScraperCtx:
    def __init__(self, **kwargs):
        builder = _cv_builder.get()
        if not builder is None:
            _cv_builder.reset(builder._token)  # noqa
        self.data = ScraperCtxData(**kwargs | {"builder": builder})
        self.token: Optional[contextvars.Token] = None

    def __enter__(self) -> ScraperCtxData:
        self.token = _cv_ctx.set(self.data)
        return self.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            _cv_ctx.reset(self.token)
        return False