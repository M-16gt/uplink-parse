from typing import Any


class Markers:
    PROCESSOR_CLASS: str = "__parse_processor__"
    PARSE_FIELDS: str = "__parse_fields__"
    HOOKS: str = "__parse_hooks__"
    META: str = "__parse_meta__"


def check_meta_in_func(func: Any) -> None:
    if not hasattr(func, Markers.META):
        setattr(func, Markers.META, {})
