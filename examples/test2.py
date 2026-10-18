import asyncio

import aiohttp
import uplink

from uplink_parse.core.parse.parsel import ParselParse
from uplink_parse.decorators import field
from uplink_parse.consumer import DynamicConsumer


class MyParse(ParselParse):
    @field
    async def data(self):
        for quote in self.response.css("div.quote"):
            yield {
                "author": quote.xpath("span/small/text()").get(),
                "text": quote.css("span.text::text").get(),
            }
        href = self.response.css('li.next a::attr("href")').get()
        if href is not None:
            yield await self.follow(href)


@MyParse()
class Quotes(DynamicConsumer):
    @uplink.get("/tag/humor/{name}")
    def base(self, name: uplink.Path = ""):
        pass


async def main():

    async with aiohttp.ClientSession() as session:
        client = Quotes(
            base_url="https://quotes.toscrape.com",
            client=uplink.clients.AiohttpClient(session=session),
        )
        tasks = [client.base() for _ in range(25)]
        import time

        start = time.time()
        for data in await asyncio.gather(*tasks):
            print(time.time() - start)
            print(data)


asyncio.run(main())
