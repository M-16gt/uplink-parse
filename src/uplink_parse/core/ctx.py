from __future__ import annotations
import contextvars
from typing import Any, Optional, Self
from dataclasses import dataclass

import uplink


@dataclass
class ScraperCtxData:
    response: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None


_cv_ctx: contextvars.ContextVar[Optional[ScraperCtxData]] = contextvars.ContextVar(
    "uplink_parse.core.ctx", default=None
)


class CtxProxy:
    @staticmethod
    def _get_data() -> ScraperCtxData:
        data = _cv_ctx.get()
        if data is None:
            raise RuntimeError("No active scraper context.")
        return data

    @property
    def s(self) -> Any: return self._get_data().scraper

    @s.setter
    def s(self, value: Any) -> None: self._get_data().scraper = value

    @property
    def r(self) -> Any: return self._get_data().response

    @r.setter
    def r(self, value: Any) -> None: self._get_data().response = value

    @property
    def c(self) -> Self: return self._get_data().consumer

    @c.setter
    def c(self, value: Any) -> None: self._get_data().consumer = value


    scraper = s
    response = r
    consumer = c


ctx = CtxProxy()


class ScraperCtx:
    def __init__(self, response: Any | None = None, consumer: Any | None = None, scraper: Any | None = None):
        self.data = ScraperCtxData(response=response, consumer=consumer, scraper=scraper)
        self.token: Optional[contextvars.Token] = None

    def __enter__(self) -> ScraperCtxData:
        self.token = _cv_ctx.set(self.data)
        return self.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            _cv_ctx.reset(self.token)
        return False