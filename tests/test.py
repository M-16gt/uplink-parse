import asyncio
import re
import time

import aiohttp
import uplink

start = time.time()
from uplink_parse.core.parse import BS4Parse
from uplink_parse.decorators.field import field
from uplink_parse.decorators.fields import fields
from uplink_parse.future import add_builder_to_ctx


class PypiStatsProjectParse(BS4Parse):
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
        result = match.group(1).strip() if match else None
        return result

    @field
    def package_name(self):
        return self.response.select("section > h1")[0].get_text(strip=True)

    @field
    def pypi_link(self):
        return self.response.find("a", string="PyPI page")["href"]

    @field
    def homepage(self):
        return self.response.find("a", string="Home page")["href"]

    @fields
    def _(self):
        return {name: self.extract_text(pattern) for name, pattern in self._patterns}


@add_builder_to_ctx
class PypiStats(uplink.Consumer):
    @PypiStatsProjectParse(is_async=True)
    @uplink.get("/packages/{name}")
    def project_data(self, name: uplink.Path):
        pass


async def main():
    # Создаем сессию явно, чтобы управлять её жизненным циклом
    async with aiohttp.ClientSession() as session:
        client = PypiStats(
            base_url="https://pypistats.org",
            client=uplink.clients.AiohttpClient(session=session),
        )

        result = await client.project_data(name="requests")
        # result = await client.project_data(name="requests")
        # print(f"✅ Финальный результат в коде: {result}")
        print(f"📦 Тип результата: {type(result)}")
        print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

# client = PypiStats(
#     base_url="https://pypistats.org",
#
# )
# result =client.project_data(name="requests")
# print(result)
# print(PypiStatsProjectParse().handle_response)
