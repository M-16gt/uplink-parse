from abc import ABCMeta
from typing import Any

class PropertyCollectorMeta(type):

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        props = set()

        for base in cls.__mro__[:-4]:
            for attr_name, attr_value in base.__dict__.items():
                if isinstance(attr_value, property):
                    props.add(attr_name)

        cls._cached_property_names = frozenset(props)

        def get_properties(self) -> dict[str, Any]:
            return {_: getattr(self, _) for _ in self._cached_property_names}

        cls.get_properties = get_properties

        return cls


class PropertyCollector(metaclass=PropertyCollectorMeta):
    pass

class CombinedMeta(PropertyCollectorMeta, ABCMeta):
    pass
