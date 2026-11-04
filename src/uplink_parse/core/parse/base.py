"""Уровень 3: сам парсинг — запуск полей и подзапросы."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any, cast
from urllib.parse import urljoin

from uplink_parse.core._generics import strategy, strategy_rt
from uplink_parse.core.parse.response import ResponseInfo, _ResponseObj
from uplink_parse.core.utils import await_or_return
from uplink_parse.core.utils.ctx import ScraperCtx, ctx


class BaseParse(_ResponseObj[strategy, strategy_rt], check_typevars=("strategy",)):
    async def _call_async(self, *args: Any, **kwargs: Any) -> Any:
        with ScraperCtx(
            response=args[-1],
            consumer=args[0] if len(args) > 1 else None,
            scraper=self,
            response_raw=args[-1],
            response_info_factory=ResponseInfo,
        ):
            if self.use_parse_response():
                ctx.response = await self.parse_response()
            return await self.storage.task_runner(self.storage.parse_funcs_meta)

    @functools.wraps(_call_async)
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        coro = self._call_async(*args, **kwargs)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        return coro

    async def follow(
        self,
        href: str | None = None,
        *,
        url: str | None = None,
        callback: Callable[[Any, Any], Any] | None = None,
        method: str = "GET",
        **options: Any,
    ) -> Any:
        """Request a URL and parse its response with callback or this parser."""
        if href is None:
            if url is None:
                raise ValueError("Pass href or url to follow")
            target_url = str(url)
        else:
            base_url = ctx.response_info.url if url is None else url
            target_url = urljoin(str(base_url), href)

        consumer = ctx.consumer
        if consumer is None:
            raise RuntimeError("follow requires a consumer")
        response = await await_or_return(
            consumer.request(method, target_url, **options)
        )
        parser = cast(Callable[[Any, Any], Any], self) if callback is None else callback
        return await await_or_return(parser(consumer, response))
