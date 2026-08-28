from typing import Any

from uplink_parse.core.utils.markers import Markers


class Parseable:
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _fields: dict[type[Any], set[str]] = {}
        for base in cls.__bases__:
            if hasattr(base, Markers.PARSE_FIELDS):
                for proc_cls, names in getattr(base, Markers.PARSE_FIELDS).items():
                    _fields[proc_cls] = names.copy()
        for name, value in cls.__dict__.items():
            if name.startswith("__") and name.endswith("__"):
                continue
            proc_cls = getattr(value, Markers.PROCESSOR_CLASS, None)
            if proc_cls is not None:
                _fields.setdefault(proc_cls, set()).add(name)
        setattr(cls, Markers.PARSE_FIELDS, _fields)

    @property
    def parse_fields(self) -> dict[type[Any], set[str]]:
        return getattr(self, Markers.PARSE_FIELDS, {})
