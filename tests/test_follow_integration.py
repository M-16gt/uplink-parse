import asyncio

import pytest

uplink = pytest.importorskip("uplink")
aiohttp = pytest.importorskip("aiohttp")
pytest.importorskip("parsel")
from aiohttp import web  # noqa: E402

from uplink_parse.consumer import DynamicConsumer  # noqa: E402
from uplink_parse.core.parse.parsel import ParselParse  # noqa: E402
from uplink_parse.decorators import field  # noqa: E402


class Page(ParselParse):
    @field
    def titles(self):
        for title in self.response.css("h1::text"):
            yield title.get()
        link = self.response.css("a.next::attr(href)").get()
        if link:
            yield self.follow(link)


@Page()
class Site(DynamicConsumer):
    @uplink.get("/start")
    def start(self):
        pass


async def _exercise_follow() -> None:
    async def next_page(request):
        return web.Response(text="<h1>second</h1>", content_type="text/html")

    next_app = web.Application()
    next_app.router.add_get("/next", next_page)
    next_runner = web.AppRunner(next_app)
    await next_runner.setup()
    next_site = web.TCPSite(next_runner, "127.0.0.1", 0)
    await next_site.start()
    next_port = next_site._server.sockets[0].getsockname()[1]

    async def start_page(request):
        html = (
            '<h1>first</h1><a class="next" '
            f'href="http://127.0.0.1:{next_port}/next">next</a>'
        )
        return web.Response(text=html, content_type="text/html")

    start_app = web.Application()
    start_app.router.add_get("/start", start_page)
    start_runner = web.AppRunner(start_app)
    await start_runner.setup()
    start_site = web.TCPSite(start_runner, "127.0.0.1", 0)
    await start_site.start()
    start_port = start_site._server.sockets[0].getsockname()[1]

    try:
        async with aiohttp.ClientSession() as session:
            consumer = Site(
                base_url=f"http://127.0.0.1:{start_port}",
                client=uplink.clients.AiohttpClient(session=session),
            )
            assert await consumer.start() == {"titles": ["first", {"titles": "second"}]}
    finally:
        await start_runner.cleanup()
        await next_runner.cleanup()


def test_sync_field_follows_absolute_url_with_aiohttp() -> None:
    asyncio.run(_exercise_follow())
