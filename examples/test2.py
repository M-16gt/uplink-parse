# src/uplink_parse/core/_strategies.py
import asyncio

import aiohttp
import uplink

from uplink_parse.core.strategies.parsel import ParselResult, ParselStrategy

# ... существующие импорты ...
from uplink_parse.core.parse import BaseParse
from uplink_parse.decorators.field import field


class ParselParse(BaseParse[ParselStrategy, ParselResult]):
    @field
    async def data(self):
        for quote in self.response.css("div.quote"):
            yield {
                "author": quote.xpath("span/small/text()").get(),
                "text": quote.css("span.text::text").get(),
            }
        link = self.response.css('li.next a::attr("href")').get()
        if link is not None:
            yield await self.consumer.base2(link)


@ParselParse()
class Quotes(uplink.Consumer):
    @uplink.get("/tag/humor/{name}")
    def base(self, name: uplink.Path = ""):
        pass

    @uplink.get("/{data}")
    def base2(self, data: uplink.Path):
        pass


# client = Quotes(
#             base_url="https://quotes.toscrape.com"
#         )
# print(client.base())
async def main():
    import cProfile

    # Создаем сессию явно, чтобы управлять её жизненным циклом
    async with aiohttp.ClientSession() as session:
        client = Quotes(
            base_url="https://quotes.toscrape.com",
            client=uplink.clients.AiohttpClient(session=session),
        )
        tasks = [client.base() for i in range(100)]
        import time

        start = time.time()
        for data in await asyncio.gather(*tasks):
            print(time.time() - start)
            print(data)


asyncio.run(main())
