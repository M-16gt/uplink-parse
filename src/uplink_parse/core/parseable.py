from typing import Any

from uplink_parse.core._dataclasses import FuncMeta
from uplink_parse.core.utils.markers import Markers


def _field_meta(value: Any) -> FuncMeta | None:
    meta = getattr(value, Markers.META, None)
    if isinstance(meta, FuncMeta) and meta.populate is not None:
        return meta
    return None


class Parseable:
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        names: set[str] = {
            meta.name
            for base in cls.__bases__
            for meta in getattr(base, Markers.PARSE_FIELDS, ())
        }
        for name, value in cls.__dict__.items():
            if (meta := _field_meta(value)) is not None:
                meta.name = name
                names.add(name)

        # Какая именно функция стоит за именем, решает MRO, а не порядок баз:
        # так работают и переопределение, и ромб, и замена поля обычным атрибутом.
        setattr(
            cls,
            Markers.PARSE_FIELDS,
            {meta for n in names if (meta := _field_meta(getattr(cls, n, None)))},
        )

    @property
    def parse_fields(self) -> set[FuncMeta]:
        return getattr(self, Markers.PARSE_FIELDS, set())
