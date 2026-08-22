from __future__ import annotations

import uplink

from uplink_parse.core.utils.ctx import _cv_builder
from uplink_parse.decorators.hooks import posthooks, prehooks


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
    uplink.hooks.RequestAuditor, uplink.decorators._BaseHandlerAnnotation
):
    pass


@request_auditor
def add_builder_to_ctx(request):
    request.token_ctx = _cv_builder.set(request)
    return request
