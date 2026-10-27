from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast
from urllib.parse import urljoin

from uplink_parse.core.tasks.compat import await_or_return
from uplink_parse.core.utils.ctx import ctx


class FollowMixin:
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
