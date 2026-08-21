import types
from typing import Any

class GenericBase:
    config_types: types.MappingProxyType[str, Any]
    def __init_subclass__(cls, **kwargs: Any) -> None: ...

def make_generic(name: str, *type_vars: Any) -> type[GenericBase]: ...
