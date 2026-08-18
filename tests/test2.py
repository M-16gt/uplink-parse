# src/uplink_parse/core/_strategies.py
import asyncio

import aiohttp
import uplink

from uplink_parse.core.ctx import ctx
# ... существующие импорты ...
from uplink_parse.core.parse import BaseParse
from uplink_parse.core.strategy import Strategy
from uplink_parse.core._strategies import TextStrategy
from uplink_parse.decorators.field import field
from uplink_parse.decorators.fields import fields

try:
    from parsel import Selector as ParselSelector
except ImportError:
    ParselSelector = None

ParselResult = "ParselSelector"


def _sync_parsel(response) -> ParselSelector:
    if ParselSelector is None:
        raise ImportError("parsel is not installed. Run: pip install parsel")
    # Parsel умеет сам определять тип (html/xml), но можно форсировать
    return ParselSelector(text=TextStrategy()(response))


async def _async_parsel(response) -> ParselSelector:
    if ParselSelector is None:
        raise ImportError("parsel is not installed. Run: pip install parsel")
    text = await TextStrategy()(response)
    return ParselSelector(text=text)


class ParselStrategy(Strategy[ParselResult]):
    funcs_dict = {
        "RequestsClient": _sync_parsel,
        "AiohttpClient": _async_parsel
    }


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



@ParselParse(is_async=True)
class Quotes(uplink.Consumer):
    @uplink.get("/tag/humor/{name}")
    def base(self, name: uplink.Path = ""): pass

    @uplink.get("/{data}")
    def base2(self, data: uplink.Path):
        pass


# client = Quotes(
#             base_url="https://quotes.toscrape.com"
#         )
# print(client.base())
async def main():
    # Создаем сессию явно, чтобы управлять её жизненным циклом
    async with aiohttp.ClientSession() as session:
        client = Quotes(
            base_url="https://quotes.toscrape.com",
            client=uplink.clients.AiohttpClient(session=session)
        )

        result = await client.base()
        print(result)


asyncio.run(main())
