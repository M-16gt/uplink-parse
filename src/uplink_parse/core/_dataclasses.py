from dataclasses import dataclass, field
from typing import Callable, Awaitable, Any


@dataclass
class _ParseMeta:
    names: list[str] = field(default_factory=list)
    urls: list[Callable] = field(default_factory=list)
    coroutines_or_funcs: list[Callable | Awaitable] = field(default_factory=list)
    strategies: list[Callable] = field(default_factory=list)

    def is_nan_obj(self):
        return not len(self.names)

@dataclass
class ScraperCtxData:
    response: Any | None = None
    request: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None
    builder: Any | None = None

@dataclass
class Storage:
    _data: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __getattr__(self, item: str) -> Any:
        if item in self._data:
            return self._data[item]
        raise AttributeError(f"'Storage' object has no attribute '{item}'")

    def __setattr__(self, item: str, value: Any) -> None:
        if item == "_data" or item in self.__dict__:
            object.__setattr__(self, item, value)
        else:
            self._data[item] = value

    def __delattr__(self, item: str) -> None:
        if item == "_data":
            raise AttributeError("Cannot delete '_data'")
        if item in self._data:
            del self._data[item]
        else:
            raise AttributeError(f"'Storage' object has no attribute '{item}'")