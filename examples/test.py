import asyncio
import re
import time
from collections.abc import Callable, Coroutine

import aiohttp
import uplink

start = time.time()
from uplink_parse.core.parse import BaseParse
from uplink_parse.core.strategies.bs4 import BS4Strategy, BS4Result

from uplink_parse.decorators.field import field
from uplink_parse.decorators.fields import fields
from uplink_parse.future import add_builder_to_ctx
from uplink_parse.core.hooks import prehook, SKIP


class PypiStatsProjectParse(BaseParse[BS4Strategy, BS4Result]):
    # consumer: "PypiStats"
    _patterns = [
        (name.lower(), rf"{name}:\s*\n\s*([^\n<]+)")
        for name in [
            "Author",
            "License",
            "Latest version",
            "Downloads last day",
            "Downloads last week",
            "Downloads last month",
        ]
    ]

    def extract_text(self, pattern):
        match = re.search(pattern, self.response.get_text(), re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    @field
    def package_name(self):
        return self.response.select("section > h1")[0].get_text(strip=True)

    @field
    def pypi_link(self):
        return self.response.find("a", string="PyPI page")["href"]

    @field
    @prehook(lambda func_meta: SKIP)
    def homepage(self):
        return self.response.find("a", string="Home page")["href"]

    @fields
    def _(self):
        return {name: self.extract_text(pattern) for name, pattern in self._patterns}


@add_builder_to_ctx
class PypiStats(uplink.Consumer):
    @PypiStatsProjectParse(strategy_params={"features": "lxml"})
    @uplink.get("/packages/{name}")
    def project_data(self, name: uplink.Path) -> Callable | Coroutine:
        pass


async def main():
    # Создаем сессию явно, чтобы управлять её жизненным циклом
    async with aiohttp.ClientSession() as session:
        client = PypiStats(
            base_url="https://pypistats.org",
            client=uplink.clients.AiohttpClient(session=session),
        )

        result = await client.project_data(name="requests")
        print(f"📦 Тип результата: {type(result)}")
        print(result)


import asyncio

asyncio.run(main())
