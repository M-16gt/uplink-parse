import asyncio
import copy, timeit, attrs

from uplink_parse.core.parse.bs4 import BS4Parse
from uplink_parse.core.parse.obj import Storage, ParseConfig
from uplink_parse.decorators import SKIP, field, prehook, fields
from uplink_parse.decorators.meta import FuncMeta


class P(BS4Parse):
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


t = P(is_decorator=False)
cfg = ParseConfig()
print(timeit.timeit(lambda: Storage.build(t, cfg), number=100_000) * 10, "µs")
