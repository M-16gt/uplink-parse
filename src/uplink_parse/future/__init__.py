from __future__ import annotations
from typing import Any

import repath
import uplink

from uplink_parse.core.ctx import ctx, _cv_builder
from uplink_parse.decorators.hooks import prehooks, posthooks
from uplink_parse.core._enums import FieldActions


# Класс для поддержки lambda функций в BaseParse
class LambdaChecker:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr_name, value in vars(cls).items():
            if callable(value) and getattr(value, "__name__", None) == "<lambda>":
                value.__name__ = attr_name
                value.__qualname__ = f"{cls.__name__}.{attr_name}"


_prehooks = prehooks()
_posthooks = posthooks()


class request_auditor(
    uplink.hooks.RequestAuditor, uplink.decorators._BaseHandlerAnnotation):
    pass


@request_auditor
def add_builder_to_ctx(request):
    request.token_ctx = _cv_builder.set(request)
    return request


class Router:
    __slots__ = ("_compiled", "_cache")

    def __init__(self):
        self._compiled: dict[str, Any] = {}
        self._cache: dict[str, bool] = {}

    def add_pattern(self, pattern: str) -> None:
        if pattern in self._compiled:
            return

        self._compiled[pattern] = repath.compile(pattern)
        self._cache.clear()

    def match(self, template: str) -> bool:
        if template in self._cache:
            return self._cache[template]

        for compiled in self._compiled.values():
            if compiled.match(template) is not None:
                self._cache[template] = True
                return True

        self._cache[template] = False
        return False

def route(pattern: str, reverse: bool = False):
    def wrapper(args, kwargs, func):
        print(33)
        scraper = ctx.scraper or args[0]

        storage = scraper.storage

        if not hasattr(storage, "router"):
            storage.router = Router()
        print(1)
        url = str(ctx.builder.url)

        storage.router.add_pattern(pattern)
        is_match = storage.router.match(url)
        print(is_match)

        final_result = not is_match if reverse else is_match
        return final_result if final_result else FieldActions.SKIP

    return _prehooks(hooks=wrapper)


def _(kwargs):
    for key in list(kwargs):
        if kwargs[key] is FieldActions.SKIP:
            del kwargs[key]
    return kwargs


_ = _posthooks(hooks=_)
