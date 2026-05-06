import re

import uplink

import time
start = time.time()
from uplink_parse.core.parse import HTMLParse
from uplink_parse.decorators.field import field, _Field
from uplink_parse.decorators.fields import fields

from uplink_parse.decorators.transform import transform
from uplink_parse.core.ctx import ctx
print(time.time()-start)

class PypiStatsProjectParse(HTMLParse):
    # consumer: "PypiStats"
    _patterns = [(name.lower(), r"{}:\s*\n\s*([^\n<]+)".format(name)) for name in
                 ["Author", "License", "Latest version", "Downloads last day", "Downloads last week",
                  "Downloads last month"]]

    def extract_text(self, pattern):
        match = re.search(pattern, self.r.get_text(), re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None


    def package_name(self, name) -> tuple:

        return self.r.select("section > h1")[0].get_text(strip=True), name

    @field
    def pypi_link(self):
        return self.r.find("a", string="PyPI page")["href"]

    @transform(lambda d: ctx.c)
    @field
    def homepage(self):
        return self.r.find("a", string="Home page")["href"]

    @fields
    def _(self):
        return {name: self.extract_text(pattern) for name, pattern in self._patterns}

class PypiStats(uplink.Consumer):
    @PypiStatsProjectParse()
    @uplink.get("/packages/{name}")
    def project_data(self, name: uplink.Path): pass

a = PypiStatsProjectParse(
)
b = PypiStatsProjectParse()
print(a is b)
print(_Field() is _Field())
api = PypiStats(base_url="https://pypistats.org")
user = api.project_data("requests")

# import time
print(user)


