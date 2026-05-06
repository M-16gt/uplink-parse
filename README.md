uplink-parse - расширение для библиотеки uplink, расширяющее возможности uplink в сторону парсинга нацелен на удобный парсинг через базовые классы 
__all__ = ("HTMLParse", "XMLParse", "TextParse", "JSONParse", "BytesParse", "AutoParse") наследуемые от BaseParse, есть возможность создавать свои базовые классы на основе его требуется только реализация parse_response для того чтобы расспарсить приходящий запрос
Пример использования расширения:
import re
import uplink

from uplink_parse.parse import HTMLParse
from uplink_parse import auto_parse


class PypiStatsProjectParse(HTMLParse):
    _pattern = r"{}:\s*\n\s*([^\n<]+)"

    def extract_text(self, name):
        match = re.search(self._pattern.format(name), self.r.get_text(), re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    @property
    def package_name(self):
        return self.r.select("section > h1")[0].get_text(strip=True)
    @property
    def pypi_link(self):
        return self.r.find("a", string="PyPI page")["href"]
    @property
    def homepage(self):
        return self.r.find("a", string="Home page")["href"]
    @property
    def author(self):
        return self.extract_text("Author")
    @property
    def license(self):
        return self.extract_text("License")
    @property
    def last_version(self):
        return self.extract_text("Latest version")
    @property
    def download_last_day(self):
        return self.extract_text("Downloads last day")
    @property
    def download_last_week(self):
        return self.extract_text("Downloads last week")
    @property
    def download_last_month(self):
        return self.extract_text("Downloads last month")

class PypiStats(uplink.Consumer):
    @auto_parse(PypiStatsProjectParse)
    @uplink.get("/packages/{name}")
    def project_data(self, name: uplink.Path): pass


api = PypiStats(base_url="https://pypistats.org")
project = api.project_data("requests")


